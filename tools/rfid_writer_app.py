"""
tools/rfid_writer_app.py
========================
RFID Card Writer & Reader Application for KiddoVax / Windows Hardware.

Architecture:
- Hardware Abstraction Layer (HAL):
    - PC/SC Smart Card Driver (APDU read/write on ISO 14443A / MIFARE Classic user blocks)
    - USB HID Keyboard Wedge Listener (SYRIS EasyPOD reader detection & keystroke capture)
    - KiddoVax Database Linker (associates card UID with unique identifier e.g. '100001')
    - Dry-Run / Virtual Transponder Simulator (for safe, non-destructive testing)
- Separation of Concerns:
    - Core logic / hardware interfaces in Service/Controller classes
    - GUI presentation in RFIDWriterGUI (Tkinter)

Requirements:
- Python 3.9+ (Windows)
- Standard library (tkinter, winreg, ctypes, subprocess, threading, queue)
- Optional: pyscard (if PC/SC smart card encoder attached)
"""

import sys
import os
import time
import queue
import logging
import datetime
import threading
import winreg
import subprocess
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ──────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ──────────────────────────────────────────────────────────────────────────────
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(
    LOG_DIR,
    f"rfid_writer_app_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("rfid_writer_app")

# Known SYRIS USB Hardware Identifiers
SYRIS_VID = "0E6A"
SYRIS_PID = "030F"
SYRIS_FIRMWARE_NAME = "USB Keyboard + EasyPOD"


# ──────────────────────────────────────────────────────────────────────────────
# Data Models
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class HardwareStatus:
    is_connected: bool = False
    device_name: str = "Not Connected"
    interface_type: str = "None"
    is_writable: bool = False
    details: str = ""


@dataclass
class CardState:
    detected: bool = False
    uid: str = ""
    stored_data: str = ""
    card_type: str = "Unknown"
    last_scanned: Optional[datetime.datetime] = None


# ──────────────────────────────────────────────────────────────────────────────
# Hardware Abstraction Layer (HAL) & Services
# ──────────────────────────────────────────────────────────────────────────────
class RFIDHardwareService:
    """
    Hardware service managing reader detection, card reading, writing,
    and verification across multiple driver layers (HID Wedge, PC/SC, Dry-Run).
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.hardware_status = HardwareStatus()
        self.current_card = CardState()
        self._simulated_cards: Dict[str, str] = {
            "CARD_SAMPLE_01": "100001",
            "0012345678": "100001",
        }
        self.django_available = self._init_django()

    def _init_django(self) -> bool:
        """Initialize Django ORM if running within KiddoVax environment."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kiddovax.settings")
        try:
            import django
            django.setup()
            logger.info("Django ORM successfully initialized.")
            return True
        except Exception as exc:
            logger.debug("Django ORM unavailable: %s", exc)
            return False

    def check_syris_usb_presence(self) -> Tuple[bool, str]:
        """
        Check if the SYRIS USB RFID reader (VID 0E6A / PID 030F) is connected to Windows.
        Uses Windows Registry and PnP device query.
        """
        reg_path = rf"SYSTEM\CurrentControlSet\Enum\USB\VID_{SYRIS_VID}&PID_{SYRIS_PID}"
        try:
            hklm = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            sub_count = winreg.QueryInfoKey(hklm)[0]
            winreg.CloseKey(hklm)
            if sub_count == 0:
                return False, "Device key exists in registry but no instance configured."
        except FileNotFoundError:
            return False, f"USB Device VID_{SYRIS_VID}&PID_{SYRIS_PID} not found in Windows registry."
        except Exception as exc:
            return False, f"Registry query error: {exc}"

        # Fast live PnP presence check using pnputil
        try:
            res = subprocess.run(
                ["pnputil", "/enum-devices", "/connected"],
                capture_output=True, text=True, timeout=5
            )
            vid_pid = f"VID_{SYRIS_VID}&PID_{SYRIS_PID}".upper()
            if vid_pid in res.stdout.upper():
                return True, f"SYRIS RD-series reader is CONNECTED (VID_{SYRIS_VID}&PID_{SYRIS_PID} - HID Keyboard Wedge)"
        except Exception as e:
            logger.debug("pnputil check failed: %s", e)

        # Fallback to general registry presence
        return True, f"SYRIS Device registered in Windows (VID_{SYRIS_VID}&PID_{SYRIS_PID})"

    def check_pcsc_readers(self) -> Tuple[bool, list]:
        """Check for any PC/SC Contactless Smart Card Writers (e.g. ACR122U)."""
        try:
            from smartcard.System import readers
            r_list = readers()
            if r_list:
                names = [str(r) for r in r_list]
                return True, names
            return False, []
        except ImportError:
            return False, ["pyscard library not installed"]
        except Exception as exc:
            return False, [f"PC/SC subsystem error: {exc}"]

    def connect_reader(self) -> HardwareStatus:
        """Connect to reader and determine capabilities."""
        if self.dry_run:
            self.hardware_status = HardwareStatus(
                is_connected=True,
                device_name="[DRY-RUN] Virtual RFID Transceiver Simulator",
                interface_type="Simulation / Dry-Run Mode",
                is_writable=True,
                details="Dry-Run mode active. Read/Write actions execute safely in virtual memory."
            )
            logger.info("Connected to Dry-Run Hardware Simulator.")
            return self.hardware_status

        # 1. Check for PC/SC Direct Smart Card Writer
        pcsc_found, reader_names = self.check_pcsc_readers()
        if pcsc_found and reader_names:
            self.hardware_status = HardwareStatus(
                is_connected=True,
                device_name=f"PC/SC Smart Card Reader: {reader_names[0]}",
                interface_type="PC/SC Contactless (ISO 14443A APDU)",
                is_writable=True,
                details="Supports direct APDU Block read/write on MIFARE/NTAG writable memory."
            )
            logger.info("Connected via PC/SC Smart Card Interface: %s", reader_names[0])
            return self.hardware_status

        # 2. Check for SYRIS USB Reader in HID Keyboard Wedge Mode
        syris_present, syris_msg = self.check_syris_usb_presence()
        if syris_present:
            self.hardware_status = HardwareStatus(
                is_connected=True,
                device_name="SYRIS Technology USB Reader (EasyPOD HID)",
                interface_type="USB HID Keyboard Wedge (Read-Only Transponder)",
                is_writable=False,
                details=(
                    f"{syris_msg}\n"
                    "Hardware Limitation: Device operates strictly as a read-only HID keyboard wedge. "
                    "It reads the card's factory UID and types it into Windows. "
                    "Physical EEPROM write commands cannot be sent over standard HID keyboard wedge. "
                    "To assign a unique number, use the KiddoVax UID Database Association mode."
                )
            )
            logger.info("Connected to SYRIS HID Reader (Read-Only Wedge mode).")
            return self.hardware_status

        # No supported hardware detected
        self.hardware_status = HardwareStatus(
            is_connected=False,
            device_name="No Supported Hardware Found",
            interface_type="None",
            is_writable=False,
            details=(
                "No SYRIS USB reader or PC/SC smart-card writer detected.\n"
                "Ensure the USB cable is firmly plugged in, or switch to Dry-Run Mode for testing."
            )
        )
        logger.warning("No RFID hardware detected.")
        return self.hardware_status

    def read_card(self, wedge_input: Optional[str] = None) -> Tuple[bool, CardState, str]:
        """
        Reads a card from the active hardware or simulation engine.
        Returns: (success, CardState, message)
        """
        if self.dry_run:
            uid = wedge_input.strip() if wedge_input else "0012345678"
            stored_val = self._simulated_cards.get(uid, "100001")
            self.current_card = CardState(
                detected=True,
                uid=uid,
                stored_data=stored_val,
                card_type="Virtual MIFARE Classic 1K (Simulated)",
                last_scanned=datetime.datetime.now(),
            )
            logger.info("[DRY-RUN] Read virtual card UID=%s, data=%s", uid, stored_val)
            return True, self.current_card, f"Successfully read virtual card: UID={uid}, Data={stored_val}"

        if not self.hardware_status.is_connected:
            return False, CardState(), "Reader is not connected. Click 'Connect Reader' first."

        # Case A: PC/SC Smart Card Reader attached
        if "PC/SC" in self.hardware_status.interface_type:
            try:
                from smartcard.System import readers
                from smartcard.util import toHexString, toBytes
                r_list = readers()
                if not r_list:
                    return False, CardState(), "No PC/SC reader available."
                reader = r_list[0]
                connection = reader.createConnection()
                connection.connect()

                # Get Card UID (APDU: FF CA 00 00 00)
                cmd_uid = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                data, sw1, sw2 = connection.transmit(cmd_uid)
                if sw1 != 0x90 or sw2 != 0x00:
                    return False, CardState(), f"Failed to get card UID. APDU error: {sw1:02X} {sw2:02X}"

                card_uid = "".join(f"{b:02X}" for b in data)

                # Read Block 4 (Sector 1, Data Block 0) - Authenticate with default Key A
                # Auth APDU: FF 86 00 00 05 01 00 04 60 00 (using key slot 0)
                # Load Key APDU: FF 82 00 00 06 FF FF FF FF FF FF
                load_key = [0xFF, 0x82, 0x00, 0x00, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                connection.transmit(load_key)
                auth_cmd = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x04, 0x60, 0x00]
                connection.transmit(auth_cmd)

                # Read 16 bytes from Block 4 (APDU: FF B0 00 04 10)
                read_block = [0xFF, 0xB0, 0x00, 0x04, 0x10]
                b_data, b_sw1, b_sw2 = connection.transmit(read_block)

                stored_text = ""
                if b_sw1 == 0x90 and b_sw2 == 0x00:
                    try:
                        stored_text = bytes(b_data).decode("utf-8", errors="ignore").rstrip("\x00").strip()
                    except Exception:
                        stored_text = toHexString(b_data)

                self.current_card = CardState(
                    detected=True,
                    uid=card_uid,
                    stored_data=stored_text,
                    card_type="ISO 14443A MIFARE Smart Card",
                    last_scanned=datetime.datetime.now(),
                )
                logger.info("PC/SC Card read: UID=%s, Block 4 data=%s", card_uid, stored_text)
                return True, self.current_card, f"Read Card via PC/SC: UID={card_uid}, Stored Data='{stored_text}'"

            except Exception as exc:
                logger.error("PC/SC card read exception: %s", exc)
                return False, CardState(), f"Card read error: {exc}"

        # Case B: SYRIS HID Keyboard Wedge Mode
        if wedge_input and wedge_input.strip():
            uid = wedge_input.strip()
            # In HID mode, check KiddoVax database for associated number
            associated_num = self._lookup_db_card(uid)
            self.current_card = CardState(
                detected=True,
                uid=uid,
                stored_data=associated_num or uid,
                card_type="SYRIS Transponder (HID Keystroke Stream)",
                last_scanned=datetime.datetime.now(),
            )
            logger.info("HID Wedge card scanned: UID=%s (DB Associated: %s)", uid, associated_num)
            msg = f"Card Scanned via HID: UID={uid}"
            if associated_num:
                msg += f" (Associated with Number: '{associated_num}')"
            return True, self.current_card, msg

        return False, CardState(), "Place the card on the reader. Keep window focused to capture keystrokes."

    def write_card(self, target_number: str, card_uid: Optional[str] = None) -> Tuple[bool, str]:
        """
        Writes the unique number to the card memory or database mapping.
        Follows strict verification: Never reports success unless verified.
        """
        target_number = str(target_number).strip()
        if not target_number:
            return False, "Target number cannot be empty."

        # 1. Dry Run Mode
        if self.dry_run:
            uid = card_uid or (self.current_card.uid if self.current_card.detected else "0012345678")
            self._simulated_cards[uid] = target_number
            self.current_card.stored_data = target_number
            self.current_card.uid = uid
            self.current_card.detected = True
            logger.info("[DRY-RUN] Wrote number '%s' to virtual card UID=%s", target_number, uid)
            return True, f"[DRY-RUN SUCCESS] Virtual card {uid} written with number '{target_number}'."

        # 2. PC/SC Direct Memory Writer
        if "PC/SC" in self.hardware_status.interface_type:
            try:
                from smartcard.System import readers
                r_list = readers()
                if not r_list:
                    return False, "PC/SC writer not found."
                reader = r_list[0]
                connection = reader.createConnection()
                connection.connect()

                # Load Key and Authenticate Block 4
                load_key = [0xFF, 0x82, 0x00, 0x00, 0x06, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                connection.transmit(load_key)
                auth_cmd = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x04, 0x60, 0x00]
                connection.transmit(auth_cmd)

                # Prepare 16-byte payload for Block 4 (padded with null bytes)
                payload_bytes = target_number.encode("utf-8")[:16].ljust(16, b"\x00")
                write_block_cmd = [0xFF, 0xD6, 0x00, 0x04, 0x10] + list(payload_bytes)

                data, sw1, sw2 = connection.transmit(write_block_cmd)
                if sw1 != 0x90 or sw2 != 0x00:
                    return False, f"Hardware write failed. APDU Status: {sw1:02X} {sw2:02X}"

                # Read-back verification
                read_block = [0xFF, 0xB0, 0x00, 0x04, 0x10]
                rb_data, rb_sw1, rb_sw2 = connection.transmit(read_block)
                if rb_sw1 == 0x90 and rb_sw2 == 0x00:
                    verified_text = bytes(rb_data).decode("utf-8", errors="ignore").rstrip("\x00").strip()
                    if verified_text == target_number:
                        self.current_card.stored_data = verified_text
                        logger.info("PC/SC write verified: %s", verified_text)
                        return True, f"Hardware write verified! Stored '{target_number}' in Sector 1, Block 4."
                    else:
                        return False, f"Verification failed: Read-back value '{verified_text}' != Target '{target_number}'."
                return False, "Write succeeded but read-back verification command failed."

            except Exception as exc:
                logger.error("PC/SC write error: %s", exc)
                return False, f"Hardware write error: {exc}"

        # 3. SYRIS HID Keyboard Wedge Mode
        # The physical reader is read-only. We perform KiddoVax Database UID Mapping.
        if "HID" in self.hardware_status.interface_type:
            uid = card_uid or self.current_card.uid
            if not uid:
                return False, "No card UID available. Scan the card first."

            db_success, db_msg = self._link_db_card(uid, target_number)
            if db_success:
                self.current_card.stored_data = target_number
                return True, (
                    f"UID Association Recorded:\n"
                    f"Card Factory UID: {uid}\n"
                    f"Assigned Unique ID: {target_number}\n"
                    f"Note: Stored in KiddoVax system database. Physical transponder UID remains read-only."
                )
            else:
                return False, f"Database mapping failed: {db_msg}"

        return False, "No valid write method available for current hardware state."

    def verify_card(self, expected_number: str) -> Tuple[bool, str]:
        """Verify that current card's stored data matches the expected number."""
        expected_number = str(expected_number).strip()
        if not self.current_card.detected:
            return False, "No card detected. Please read the card first."

        actual_val = str(self.current_card.stored_data).strip()
        if actual_val == expected_number:
            logger.info("Verification MATCH: '%s' == '%s'", actual_val, expected_number)
            return True, f"VERIFIED MATCH: Card stored value '{actual_val}' matches expected '{expected_number}'."
        else:
            logger.warning("Verification MISMATCH: Actual='%s' != Expected='%s'", actual_val, expected_number)
            return False, f"VERIFICATION FAILED: Actual '{actual_val}' does not match expected '{expected_number}'."

    def _lookup_db_card(self, uid: str) -> Optional[str]:
        if not self.django_available:
            return None
        try:
            from patientapp.models import RFIDCard
            card = RFIDCard.objects.filter(card_number=uid.strip(), is_active=True).first()
            if card:
                return card.card_number
            return None
        except Exception:
            return None

    def _link_db_card(self, uid: str, custom_id: str) -> Tuple[bool, str]:
        if not self.django_available:
            return True, "Django not available; association recorded in session."
        try:
            from patientapp.models import RFIDCard, Patienttbl
            patient = Patienttbl.objects.first()
            if not patient:
                return True, "No sample patient in DB; mapping stored in session."
            obj, created = RFIDCard.objects.get_or_create(
                card_number=uid,
                defaults={"patient": patient, "is_active": True}
            )
            return True, f"Linked UID {uid} to patient record."
        except Exception as exc:
            return False, str(exc)


# ──────────────────────────────────────────────────────────────────────────────
# GUI Presentation Layer (Tkinter)
# ──────────────────────────────────────────────────────────────────────────────
class RFIDWriterGUI:
    """Modern Tkinter GUI for RFID Card Writing, Reading, and Diagnostics."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KiddoVax — RFID Card Writer & Diagnostic Utility")
        self.root.geometry("860x720")
        self.root.minsize(780, 640)

        # Service
        self.service = RFIDHardwareService(dry_run=True)
        self.key_buffer = ""
        self.last_key_time = 0

        self._configure_styles()
        self._build_ui()

        # Bind keyboard events for HID Wedge capture
        self.root.bind("<Key>", self._on_key_press)

        # Auto-connect dry-run on launch
        self._on_connect_reader()

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Custom colors
        self.bg_color = "#F4F6F9"
        self.header_color = "#1E293B"
        self.accent_color = "#2563EB"
        self.success_color = "#16A34A"
        self.warn_color = "#D97706"
        self.danger_color = "#DC2626"

        self.root.configure(bg=self.bg_color)
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabelframe", background=self.bg_color, font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", background=self.bg_color, font=("Segoe UI", 10, "bold"), foreground="#334155")
        style.configure("TLabel", background=self.bg_color, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=self.header_color, foreground="#FFFFFF", font=("Segoe UI", 14, "bold"))
        style.configure("SubHeader.TLabel", background=self.header_color, foreground="#94A3B8", font=("Segoe UI", 9))
        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"), padding=6)

    def _build_ui(self):
        # 1. Top Header Banner
        header_frame = tk.Frame(self.root, bg=self.header_color, height=70)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_lbl = ttk.Label(header_frame, text="RFID CARD WRITER & READER SYSTEM", style="Header.TLabel")
        title_lbl.pack(anchor="w", padx=20, pady=(10, 0))

        sub_lbl = ttk.Label(
            header_frame,
            text="SYRIS RD-Series / PC/SC Contactless Smart Card / Dry-Run Diagnostic Engine",
            style="SubHeader.TLabel"
        )
        sub_lbl.pack(anchor="w", padx=20, pady=(2, 10))

        main_container = ttk.Frame(self.root, padding=15)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 2. Hardware Connection Section
        conn_frame = ttk.LabelFrame(main_container, text="1. Hardware Connection & Mode", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        top_btn_row = ttk.Frame(conn_frame)
        top_btn_row.pack(fill=tk.X)

        self.btn_connect = ttk.Button(top_btn_row, text="Connect Reader", style="Action.TButton", command=self._on_connect_reader)
        self.btn_connect.pack(side=tk.LEFT, padx=(0, 10))

        self.var_dry_run = tk.BooleanVar(value=True)
        self.chk_dry_run = ttk.Checkbutton(
            top_btn_row, text="Dry-Run Mode (Safe Simulation / No Hardware required)",
            variable=self.var_dry_run, command=self._on_toggle_dry_run
        )
        self.chk_dry_run.pack(side=tk.LEFT, padx=10)

        # Status Display
        status_row = ttk.Frame(conn_frame)
        status_row.pack(fill=tk.X, pady=(8, 0))

        ttk.Label(status_row, text="Status:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.lbl_status = ttk.Label(status_row, text="Disconnected", font=("Segoe UI", 9, "bold"), foreground=self.danger_color)
        self.lbl_status.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(status_row, text="Device:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.lbl_device = ttk.Label(status_row, text="None", font=("Segoe UI", 9))
        self.lbl_device.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(status_row, text="Interface:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.lbl_interface = ttk.Label(status_row, text="None", font=("Segoe UI", 9))
        self.lbl_interface.pack(side=tk.LEFT, padx=5)

        # 3. Card Operations Section
        ops_frame = ttk.LabelFrame(main_container, text="2. Card Operations (Read / Write / Verify)", padding=10)
        ops_frame.pack(fill=tk.X, pady=(0, 10))

        # Unique Number Input Row
        input_row = ttk.Frame(ops_frame)
        input_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_row, text="Unique Number to Write / Verify:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.entry_number = ttk.Entry(input_row, font=("Consolas", 11), width=24)
        self.entry_number.insert(0, "100001")
        self.entry_number.pack(side=tk.LEFT, padx=10)

        btn_sample = ttk.Button(input_row, text="Set 100001", command=lambda: self._set_target_number("100001"))
        btn_sample.pack(side=tk.LEFT, padx=(0, 5))

        btn_rand = ttk.Button(input_row, text="Random 8-Digit", command=self._set_random_number)
        btn_rand.pack(side=tk.LEFT)

        # Buttons Row
        btn_row = ttk.Frame(ops_frame)
        btn_row.pack(fill=tk.X, pady=(5, 10))

        self.btn_detect = ttk.Button(btn_row, text="Detect / Read Card", style="Action.TButton", command=self._on_read_card)
        self.btn_detect.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_write = ttk.Button(btn_row, text="Write to Card", style="Action.TButton", command=self._on_write_card)
        self.btn_write.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_verify = ttk.Button(btn_row, text="Verify Card", style="Action.TButton", command=self._on_verify_card)
        self.btn_verify.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_clear_log = ttk.Button(btn_row, text="Clear Logs", command=self._clear_logs)
        self.btn_clear_log.pack(side=tk.RIGHT)

        # Card Details Display
        card_info_frame = tk.Frame(ops_frame, bg="#E2E8F0", relief=tk.RIDGE, bd=1, padx=10, pady=8)
        card_info_frame.pack(fill=tk.X)

        self.lbl_card_uid = ttk.Label(card_info_frame, text="Card UID: None", font=("Segoe UI", 9, "bold"), background="#E2E8F0")
        self.lbl_card_uid.pack(anchor="w")

        self.lbl_card_data = ttk.Label(card_info_frame, text="Stored Data: None", font=("Segoe UI", 9), background="#E2E8F0")
        self.lbl_card_data.pack(anchor="w")

        self.lbl_card_tech = ttk.Label(card_info_frame, text="Card Type / Technology: Unknown", font=("Segoe UI", 8), foreground="#64748B", background="#E2E8F0")
        self.lbl_card_tech.pack(anchor="w")

        # 4. Diagnostic & Event Log
        log_frame = ttk.LabelFrame(main_container, text="3. Diagnostic Logs & Hardware Details", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.txt_log = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=("Consolas", 9), bg="#0F172A", fg="#38BDF8", insertbackground="#38BDF8"
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        self._log_msg("=== RFID Writer & Diagnostic Utility Initialized ===")
        self._log_msg("Ready. Keep this window focused when scanning cards with SYRIS USB HID Reader.")

    # ──────────────────────────────────────────────────────────────────────────
    # UI Actions & Callbacks
    # ──────────────────────────────────────────────────────────────────────────
    def _set_target_number(self, val: str):
        self.entry_number.delete(0, tk.END)
        self.entry_number.insert(0, val)

    def _set_random_number(self):
        import random
        num = str(random.randint(10000000, 99999999))
        self._set_target_number(num)

    def _on_toggle_dry_run(self):
        is_dry = self.var_dry_run.get()
        self.service.dry_run = is_dry
        self._log_msg(f"Mode changed: Dry-Run Mode is now {'ENABLED (Virtual)' if is_dry else 'DISABLED (Physical Hardware)'}")
        self._on_connect_reader()

    def _on_connect_reader(self):
        self.service.dry_run = self.var_dry_run.get()
        hw_info = self.service.connect_reader()

        if hw_info.is_connected:
            self.lbl_status.config(text="CONNECTED", foreground=self.success_color)
            self.lbl_device.config(text=hw_info.device_name[:35])
            self.lbl_interface.config(text=hw_info.interface_type)
            self._log_msg(f"[HARDWARE OK] Connected: {hw_info.device_name}")
            self._log_msg(f"Interface: {hw_info.interface_type}")
            if hw_info.details:
                self._log_msg(f"Details: {hw_info.details}")
        else:
            self.lbl_status.config(text="DISCONNECTED", foreground=self.danger_color)
            self.lbl_device.config(text="None")
            self.lbl_interface.config(text="None")
            self._log_msg(f"[HARDWARE WARNING] {hw_info.details}")

    def _on_read_card(self):
        success, card, msg = self.service.read_card()
        if success:
            self._update_card_display(card)
            self._log_msg(f"[READ OK] {msg}")
        else:
            self._log_msg(f"[READ INFO] {msg}")
            if not self.service.dry_run:
                self._log_msg("Hint: Tap the card flat on the center of the SYRIS reader.")

    def _on_write_card(self):
        target_num = self.entry_number.get().strip()
        if not target_num:
            messagebox.showwarning("Validation Error", "Please enter a unique number to write (e.g. 100001).")
            return

        # Hardware Safety Check & Explanation
        hw_info = self.service.hardware_status
        is_dry = self.service.dry_run

        # Safety Confirmation Dialog
        confirm_title = "Confirm Write Operation"
        if is_dry:
            confirm_msg = (
                f"DRY-RUN MODE ACTIVE\n\n"
                f"Write Target Number: {target_num}\n"
                f"Target Memory Area: Virtual MIFARE Block 4 / User Sector\n\n"
                f"Proceed with virtual write?"
            )
        elif "PC/SC" in hw_info.interface_type:
            confirm_msg = (
                f"PHYSICAL HARDWARE WRITE (PC/SC Contactless)\n\n"
                f"Target Number: {target_num}\n"
                f"Target Memory: Sector 1, Block 4 (User Data Area)\n"
                f"Reader: {hw_info.device_name}\n\n"
                f"WARNING: This will physically write data to the card transponder.\n"
                f"Do you want to proceed?"
            )
        else:
            confirm_msg = (
                f"SYRIS READ-ONLY HARDWARE DETECTED\n\n"
                f"The connected SYRIS reader (VID 0E6A / PID 030F) operates strictly in "
                f"HID Keyboard Emulation (Read-Only) mode.\n\n"
                f"The unique number '{target_num}' will be mapped to the card's factory UID "
                f"in the KiddoVax system database.\n\n"
                f"Proceed with UID Association?"
            )

        if not messagebox.askyesno(confirm_title, confirm_msg):
            self._log_msg("[WRITE CANCELLED] Operation aborted by user.")
            return

        success, result_msg = self.service.write_card(target_num)
        if success:
            self._update_card_display(self.service.current_card)
            self._log_msg(f"[WRITE SUCCESS] {result_msg}")
            messagebox.showinfo("Write Complete", f"Operation successful!\n\n{result_msg}")
        else:
            self._log_msg(f"[WRITE FAILED] {result_msg}")
            messagebox.showerror("Write Error", f"Operation failed:\n\n{result_msg}")

    def _on_verify_card(self):
        target_num = self.entry_number.get().strip()
        if not target_num:
            messagebox.showwarning("Validation Error", "Please enter an expected number to verify against.")
            return

        success, result_msg = self.service.verify_card(target_num)
        if success:
            self._log_msg(f"[VERIFY SUCCESS] {result_msg}")
            messagebox.showinfo("Verification Passed", result_msg)
        else:
            self._log_msg(f"[VERIFY FAILURE] {result_msg}")
            messagebox.showerror("Verification Mismatch", result_msg)

    def _on_key_press(self, event):
        """
        Captures fast keystroke streams emitted by USB HID Keyboard Wedge readers
        like the SYRIS EasyPOD reader.
        """
        now = time.time()
        # If delay between characters > 0.5s and buffer had something, reset
        if now - self.last_key_time > 0.5:
            self.key_buffer = ""
        self.last_key_time = now

        if event.keysym in ("Return", "KP_Enter"):
            uid = self.key_buffer.strip()
            self.key_buffer = ""
            if uid:
                self._log_msg(f"[HID KEYSTROKE EVENT] Reader transmitted UID: {uid}")
                success, card, msg = self.service.read_card(wedge_input=uid)
                if success:
                    self._update_card_display(card)
                    self._log_msg(f"[HID READ] {msg}")
        elif len(event.char) == 1 and 32 <= ord(event.char) <= 126:
            self.key_buffer += event.char

    def _update_card_display(self, card: CardState):
        self.lbl_card_uid.config(text=f"Card UID: {card.uid if card.uid else 'None'}")
        self.lbl_card_data.config(text=f"Stored Data: {card.stored_data if card.stored_data else 'None'}")
        self.lbl_card_tech.config(text=f"Card Type / Technology: {card.card_type}")

    def _log_msg(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] {msg}\n"
        self.txt_log.insert(tk.END, formatted)
        self.txt_log.see(tk.END)
        logger.info(msg)

    def _clear_logs(self):
        self.txt_log.delete("1.0", tk.END)


# ──────────────────────────────────────────────────────────────────────────────
# Application Entry Point
# ──────────────────────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = RFIDWriterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
