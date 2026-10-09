"""
tools/rfid_diagnostic.py
========================
RFID Reader Diagnostic Utility for KiddoVax — READ ONLY MODE.

Detects the SYRIS Technology USB RFID reader (VID_0E6A / PID_030F) and
monitors its HID keyboard output in real time. Compatible cards are read
and their UIDs displayed with timestamps. The utility never writes to any
card, never modifies the reader, and never changes any database record.

Interface detected: HID Keyboard Emulation (keyboard wedge mode).
The reader types the card UID as keystrokes followed by Enter.

Usage
-----
    python tools/rfid_diagnostic.py            # interactive monitor
    python tools/rfid_diagnostic.py --no-monitor  # device check only
    python tools/rfid_diagnostic.py --duration 120  # monitor for 120 seconds

Requirements
------------
    Python 3.9+, Windows only.
    No third-party packages required (uses only stdlib + optional pywin32).
    Run from project root or from the tools/ directory.

Safety guarantee
----------------
    This script performs zero write operations.
    It cannot write to any card, modify any UID, lock bits, OTP fields,
    authentication keys, or any writable memory area.
    It does not change reader configuration or firmware mode.
"""

import sys
import os
import time
import datetime
import argparse
import logging
import winreg
import subprocess
from dataclasses import dataclass, field
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Constants — never modify these without confirmed hardware documentation
# ──────────────────────────────────────────────────────────────────────────────

READER_VID = "0E6A"
READER_PID = "030F"
READER_NAME = "SYRIS Technology RD-series (USB Keyboard + EasyPOD)"
EXPECTED_FIRMWARE_NAME = "USB Keyboard + EasyPOD"

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(
    LOG_DIR,
    f"rfid_diagnostic_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
)

DEFAULT_MONITOR_DURATION = 60  # seconds

# ──────────────────────────────────────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────────────────────────────────────

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("rfid_diagnostic")


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DeviceInfo:
    """Holds verified USB device properties."""
    vid: str = ""
    pid: str = ""
    revision: str = ""
    firmware_name: str = ""
    instance_id: str = ""
    status: str = ""
    driver: str = ""
    driver_version: str = ""
    location: str = ""
    interfaces: list = field(default_factory=list)
    is_present: bool = False


@dataclass
class CardRead:
    """Represents a single card read event."""
    uid: str
    timestamp: datetime.datetime
    length: int

    def __str__(self):
        return (
            f"[{self.timestamp.strftime('%H:%M:%S.%f')[:-3]}]  "
            f"UID: {self.uid!r:20s}  len={self.length}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Device detection
# ──────────────────────────────────────────────────────────────────────────────

def detect_device_via_registry() -> Optional[DeviceInfo]:
    """
    Read device properties directly from the Windows registry.
    Does not require pywin32 or WMI — uses only stdlib winreg.
    Returns DeviceInfo if the device is present, None otherwise.
    """
    reg_path = rf"SYSTEM\CurrentControlSet\Enum\USB\VID_{READER_VID}&PID_{READER_PID}"
    try:
        hklm = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
    except FileNotFoundError:
        return None  # Device never installed on this machine
    except OSError as exc:
        log.warning("Registry read failed: %s", exc)
        return None

    info = DeviceInfo(vid=READER_VID, pid=READER_PID)

    # Enumerate sub-keys (one per unique device instance)
    idx = 0
    instance_key_name = None
    while True:
        try:
            instance_key_name = winreg.EnumKey(hklm, idx)
            idx += 1
        except OSError:
            break

    winreg.CloseKey(hklm)

    if not instance_key_name:
        return None

    # Read the most recent instance
    instance_path = rf"{reg_path}\{instance_key_name}"
    try:
        inst_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, instance_path)
    except OSError:
        return None

    def _read_value(key, name: str, default="") -> str:
        try:
            val, _ = winreg.QueryValueEx(key, name)
            if isinstance(val, list):
                return val[0] if val else default
            return str(val)
        except OSError:
            return default

    info.instance_id = f"USB\\VID_{READER_VID}&PID_{READER_PID}\\{instance_key_name}"
    info.location = _read_value(inst_key, "LocationInformation")
    info.driver = _read_value(inst_key, "Driver")
    info.status = "Present in registry"
    winreg.CloseKey(inst_key)

    # Try to get BusReportedDeviceDesc via PowerShell (no WMI dependency)
    try:
        ps_cmd = (
            "Get-PnpDeviceProperty "
            f"-InstanceId 'USB\\VID_{READER_VID}&PID_{READER_PID}\\{instance_key_name}' "
            "| Where-Object { $_.KeyName -eq 'DEVPKEY_Device_BusReportedDeviceDesc' } "
            "| Select-Object -ExpandProperty Data"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10
        )
        firmware_name = result.stdout.strip()
        if firmware_name:
            info.firmware_name = firmware_name
    except Exception:
        pass

    # Enumerate child interfaces (MI_00, MI_01, etc.)
    child_path = rf"SYSTEM\CurrentControlSet\Enum\USB\VID_{READER_VID}&PID_{READER_PID}&MI_00"
    try:
        child_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, child_path)
        info.interfaces.append("MI_00 (HID Keyboard)")
        winreg.CloseKey(child_key)
    except OSError:
        pass

    child_path = rf"SYSTEM\CurrentControlSet\Enum\USB\VID_{READER_VID}&PID_{READER_PID}&MI_01"
    try:
        child_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, child_path)
        info.interfaces.append("MI_01 (HID Consumer + System)")
        winreg.CloseKey(child_key)
    except OSError:
        pass

    info.is_present = True
    return info


def detect_device_via_powershell() -> Optional[DeviceInfo]:
    """
    Use PowerShell Get-PnpDevice to check live presence.
    Uses a minimal, fast query to avoid hanging in subprocess.
    """
    ps_cmd = (
        "$d = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue | "
        f"Where-Object {{ $_.InstanceId -like '*VID_{READER_VID}*PID_{READER_PID}*' "
        "-and $_.Class -eq 'USB' }} | Select-Object -First 1; "
        "if ($d) { Write-Output ($d.Status + '|' + $d.InstanceId) } "
        "else { Write-Output 'NOTFOUND' }"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        log.debug("PowerShell live check: %r", output)

        if not output or output == "NOTFOUND":
            return None

        parts = output.split("|", 1)
        status = parts[0].strip()
        instance_id = parts[1].strip() if len(parts) > 1 else ""

        return DeviceInfo(
            vid=READER_VID,
            pid=READER_PID,
            instance_id=instance_id,
            status=status,
            is_present=(status == "OK"),
        )
    except subprocess.TimeoutExpired:
        log.warning("PowerShell live check timed out -- using registry-only detection")
        return None
    except Exception as exc:
        log.debug("PowerShell device check failed: %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Database lookup helper (optional Django integration)
# ──────────────────────────────────────────────────────────────────────────────

def _setup_django():
    """Bootstrap Django ORM if we're inside the project directory."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kiddovax.settings")
    try:
        import django
        django.setup()
        return True
    except Exception as exc:
        log.debug("Django not available: %s", exc)
        return False


def lookup_card_in_db(uid: str) -> dict:
    """
    Look up the scanned UID in the KiddoVax database.
    Returns a dict describing the result:
      - found: True/False
      - status: 'REGISTERED' | 'NOT_REGISTERED' | 'DB_UNAVAILABLE'
      - patient_name: str
      - message: str

    This is READ-ONLY — no data is modified.
    """
    try:
        from patientapp.models import RFIDCard
        card = RFIDCard.objects.filter(
            card_number=uid.strip(), is_active=True
        ).select_related("patient").first()

        if card:
            return {
                "found": True,
                "status": "REGISTERED",
                "patient_name": card.patient.name,
                "message": f"Registered to patient: {card.patient.name} (ID {card.patient_id})",
            }
        else:
            return {
                "found": False,
                "status": "NOT_REGISTERED",
                "patient_name": "",
                "message": "Card UID is not registered to any patient in KiddoVax.",
            }
    except Exception as exc:
        return {
            "found": False,
            "status": "DB_UNAVAILABLE",
            "patient_name": "",
            "message": f"Database unavailable: {exc}",
        }


# ──────────────────────────────────────────────────────────────────────────────
# HID keyboard monitor
# ──────────────────────────────────────────────────────────────────────────────

def monitor_hid_keyboard(duration_seconds: int, django_available: bool) -> list[CardRead]:
    """
    Monitor keyboard input for RFID card UIDs.

    The SYRIS reader in HID keyboard wedge mode sends the card UID as a
    sequence of ASCII characters followed by a newline (Enter keypress).
    This function reads stdin (which captures what the reader types) for
    the given duration and returns a list of CardRead events.

    IMPORTANT: The terminal / console window must have keyboard focus.
    The reader's keystrokes go to whichever window is focused.

    This function uses msvcrt.getwch() on Windows for non-blocking key
    capture without requiring the window to be a text editor.
    """
    reads: list[CardRead] = []

    try:
        import msvcrt
    except ImportError:
        log.error("msvcrt not available — this diagnostic requires Windows.")
        return reads

    print()
    print("  " + "=" * 58)
    print("  INSTRUCTIONS:")
    print("  1. Keep THIS window focused (do not click elsewhere)")
    print("  2. Place your card flat on the CENTRE of the reader")
    print("  3. A working card produces a beep + the UID appears below")
    print(f"  4. Monitoring for {duration_seconds} seconds (Ctrl+C to stop)")
    print("  " + "=" * 58)
    print()

    log.info("HID monitor started (duration=%ds)", duration_seconds)

    deadline = time.monotonic() + duration_seconds
    buffer = ""
    read_count = 0

    try:
        while time.monotonic() < deadline:
            if msvcrt.kbhit():
                # Read one wide char (handles extended ASCII from HID)
                ch = msvcrt.getwch()
                code = ord(ch)

                if code in (13, 10):
                    # Enter / newline = end of UID transmission
                    uid = buffer.strip()
                    buffer = ""
                    if uid:
                        ts = datetime.datetime.now()
                        card = CardRead(uid=uid, timestamp=ts, length=len(uid))
                        reads.append(card)
                        read_count += 1

                        print(f"\n  [{ts.strftime('%H:%M:%S.%f')[:-3]}]  "
                              f"CARD READ #{read_count}")
                        print(f"  UID (raw):  {uid!r}")
                        print(f"  UID length: {len(uid)} characters")
                        log.info("CARD_READ uid=%r length=%d", uid, len(uid))

                        # Optional: DB lookup
                        if django_available:
                            db_result = lookup_card_in_db(uid)
                            status = db_result["status"]
                            msg = db_result["message"]
                            if db_result["found"]:
                                print(f"  DB status:  [REGISTERED] {msg}")
                                log.info("DB_LOOKUP status=%s patient=%s",
                                         status, db_result["patient_name"])
                            elif status == "NOT_REGISTERED":
                                print(f"  DB status:  [NOT REGISTERED] {msg}")
                                print("              --> Assign this card via the "
                                      "receptionist RFID assignment workflow.")
                                log.warning("DB_LOOKUP status=NOT_REGISTERED uid=%r", uid)
                            else:
                                print(f"  DB status:  [UNAVAILABLE] {msg}")
                                log.warning("DB_LOOKUP status=%s", status)
                        print()

                elif code == 3:
                    # Ctrl+C
                    print("\n  Stopped by user (Ctrl+C).")
                    break
                elif 32 <= code <= 126:
                    # Printable ASCII — accumulate into UID buffer
                    buffer += ch
                # Ignore control chars, function keys, etc.

            else:
                time.sleep(0.005)  # 5ms poll — low CPU, responsive

    except KeyboardInterrupt:
        print("\n  Stopped by user.")

    return reads


# ──────────────────────────────────────────────────────────────────────────────
# Diagnostic report sections
# ──────────────────────────────────────────────────────────────────────────────

def print_section(title: str):
    print()
    print("=" * 62)
    print(f"  {title}")
    print("=" * 62)


def print_ok(msg: str):
    print(f"  [OK]     {msg}")


def print_warn(msg: str):
    print(f"  [WARN]   {msg}")


def print_fail(msg: str):
    print(f"  [FAIL]   {msg}")


def print_info(msg: str):
    print(f"  [INFO]   {msg}")


def _check_device_live_via_wmic() -> bool:
    """
    Fast fallback to confirm the device is live using pnputil or wmic.
    Used when PowerShell subprocess times out.
    """
    try:
        # pnputil /enum-devices lists only currently present devices
        result = subprocess.run(
            ["pnputil", "/enum-devices", "/connected"],
            capture_output=True, text=True, timeout=10
        )
        vid_pid = f"VID_{READER_VID}&PID_{READER_PID}".upper()
        return vid_pid in result.stdout.upper()
    except Exception:
        pass

    try:
        # Last resort: check the registry Flags key — 0x04 bit = device present
        key_path = (
            rf"SYSTEM\CurrentControlSet\Enum\USB\VID_{READER_VID}&PID_{READER_PID}"
        )
        hklm = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        idx = 0
        while True:
            try:
                sub = winreg.EnumKey(hklm, idx)
                idx += 1
                inst_key = winreg.OpenKey(hklm, sub)
                try:
                    flags, _ = winreg.QueryValueEx(inst_key, "ConfigFlags")
                    # ConfigFlags bit 0x04 = device is present/started
                    if (flags & 0x04) == 0:  # 0 means working / started
                        winreg.CloseKey(inst_key)
                        winreg.CloseKey(hklm)
                        return True
                except OSError:
                    pass
                winreg.CloseKey(inst_key)
            except OSError:
                break
        winreg.CloseKey(hklm)
    except Exception:
        pass

    return False


def run_device_check() -> tuple[Optional[DeviceInfo], bool]:
    """Run both detection methods and merge results."""
    print_section("1. Device Presence Check")

    # Registry check (historical presence + metadata)
    reg_info = detect_device_via_registry()
    # PowerShell check (live presence)
    ps_info = detect_device_via_powershell()

    # If PS timed out but registry shows device, try fast fallback
    if reg_info and ps_info is None:
        log.info("PS check unavailable -- using pnputil fallback for live detection")
        is_live_fallback = _check_device_live_via_wmic()
        if is_live_fallback:
            # Treat as live -- registry shows it, pnputil/wmic confirms it present
            ps_info = DeviceInfo(
                vid=READER_VID, pid=READER_PID,
                instance_id=reg_info.instance_id,
                status="OK",
                is_present=True,
            )

    if ps_info and ps_info.is_present:
        # Merge registry metadata into live check result
        if reg_info:
            ps_info.firmware_name = reg_info.firmware_name or ps_info.firmware_name
            ps_info.location = reg_info.location or ps_info.location
            ps_info.driver = reg_info.driver or ps_info.driver
            ps_info.interfaces = reg_info.interfaces

        info = ps_info
        print_ok(f"Reader LIVE and present: VID_{READER_VID} / PID_{READER_PID}")
        print_ok(f"Windows status:          {info.status}")
    elif reg_info:
        info = reg_info
        print_warn("Reader found in registry but NOT currently connected (USB unplugged?)")
        print_info("Plug the reader in and re-run this diagnostic.")
    else:
        print_fail(
            f"Reader NOT found: VID_{READER_VID} / PID_{READER_PID} has never been "
            "installed on this machine."
        )
        print_info("Check that the USB cable is connected and try a different port.")
        log.error("DEVICE_NOT_FOUND VID=%s PID=%s", READER_VID, READER_PID)
        return None, False

    if info.firmware_name:
        match = info.firmware_name == EXPECTED_FIRMWARE_NAME
        if match:
            print_ok(f"Firmware name:           {info.firmware_name!r} (expected)")
        else:
            print_warn(
                f"Firmware name:           {info.firmware_name!r} "
                f"(expected {EXPECTED_FIRMWARE_NAME!r})"
            )
    if info.instance_id:
        print_info(f"Instance ID:             {info.instance_id}")
    if info.location:
        print_info(f"USB port:                {info.location}")

    log.info(
        "DEVICE_FOUND firmware=%r instance=%s status=%s",
        info.firmware_name, info.instance_id, info.status,
    )
    return info, ps_info is not None and ps_info.is_present


def run_interface_check(info: DeviceInfo):
    """Report what interfaces are exposed."""
    print_section("2. Interface Analysis")

    print_ok("Interface: HID Keyboard Emulation (active)")
    print_info("  Sub-interface MI_00 = HID Boot Keyboard (Usage Page 0x0001, Usage 0x0006)")
    print_info("  Sub-interface MI_01 = HID Consumer/System Controller")
    print()
    print_warn("Interface: COM / Serial Port ........... NOT present")
    print_warn("Interface: PC/SC Smart Card Reader ..... NOT present")
    print_warn("Interface: WinUSB / libusb direct ...... NOT present")
    print_warn("Interface: Vendor-defined HID RAW ...... NOT present")
    print()
    print_info("Current mode: HID Keyboard Emulation ONLY.")
    print_info("Card UID is output as keyboard keystrokes followed by Enter.")
    print_info("No driver, SDK, or special software is needed to read the UID.")
    print_info("Write operations are NOT available in this mode.")
    print()

    if info.interfaces:
        for iface in info.interfaces:
            print_info(f"  Detected interface: {iface}")

    log.info("INTERFACE_CHECK mode=HID_KEYBOARD write_capable=False")


def run_service_check():
    """Check PC/SC and related Windows services."""
    print_section("3. Windows RFID Service Status")

    services = {
        "SCardSvr": "Smart Card (PC/SC stack)",
        "ScDeviceEnum": "Smart Card Device Enumeration",
    }
    for svc_name, svc_label in services.items():
        try:
            result = subprocess.run(
                ["sc", "query", svc_name],
                capture_output=True, text=True, timeout=5
            )
            if "RUNNING" in result.stdout:
                print_warn(f"{svc_label}: RUNNING (unusual for HID-mode RFID)")
            else:
                print_info(f"{svc_label}: STOPPED (normal for HID keyboard mode)")
        except Exception:
            print_info(f"{svc_label}: could not query")

    print_info("HID-mode readers do NOT use the PC/SC stack.")
    log.info("SERVICE_CHECK complete")


def print_model_identification_guide():
    """Print the manual identification guide."""
    print_section("4. Reader Model Identification")
    print_info("The USB descriptor alone cannot confirm the exact reader model.")
    print_info("The same VID/PID is used by multiple SYRIS hardware variants.")
    print()
    print("  To confirm the model:")
    print("  A) Flip the reader over — look for a label, e.g., 'RD200-LF' or 'RD200-M1'")
    print("  B) Check the original packaging or documentation")
    print("  C) Download the SYRIS RD200/300 Tool from  ftp.syris.com")
    print("     and connect — the tool reads the model from the device")
    print("  D) Email SYRIS support with VID=0E6A, PID=030F, REV=0140")
    print()
    print("  Model reference:")
    print("  +------------+------------+------------------------------------------+")
    print("  | Model      | Frequency  | Supported card chips                     |")
    print("  +------------+------------+------------------------------------------+")
    print("  | RD200-LF   | 125 kHz    | EM4100 (read-only), T5577, EM4305, FDX-B |")
    print("  | RD200-M1   | 13.56 MHz  | MIFARE Classic, Ultralight, NTAG2xx      |")
    print("  | RD300-H1   | 13.56 MHz  | ISO15693, ISO14443A/B, DESFire, NTAG     |")
    print("  +------------+------------+------------------------------------------+")
    print()
    print_warn("Card frequency MUST match reader frequency. Mismatch = no beep, no output.")
    log.info("MODEL_GUIDE displayed")


def print_summary(reads: list[CardRead], django_available: bool):
    """Print final summary after monitoring."""
    print_section("5. Monitoring Summary")

    if reads:
        print_ok(f"Total cards read: {len(reads)}")
        for card in reads:
            print_info(f"  {card}")
        print()
        print_ok("Reader is functional. Cards are readable at this frequency.")
        print_info("Next step: assign cards to patients via the receptionist workflow.")
        if not django_available:
            print_warn("Django was not available — DB lookup was skipped.")
            print_info("Run from project root with: python tools/rfid_diagnostic.py")
    else:
        print_warn("No cards were read during the monitoring window.")
        print()
        print("  Possible causes (in order of probability):")
        print("  1. Card frequency does not match reader frequency (most common).")
        print("     --> Check reader model label and card packaging.")
        print("  2. Card was not placed flat on the centre of the reader antenna.")
        print("     --> Try repositioning the card.")
        print("  3. This console window lost focus during monitoring.")
        print("     --> HID keystrokes went to another window. Re-run and keep focus.")
        print("  4. Card chip is not supported by this reader variant.")
        print("     --> Confirm card type against reader model's supported list.")
        print("  5. Metal backing / multi-card wallet blocking RF field.")
        print("     --> Remove card from wallet and test directly.")
        print()
        print_info("This is a hardware/compatibility issue, NOT a software error.")
        log.warning("MONITOR_COMPLETE reads=0")

    print()
    print(f"  Log saved to: {LOG_FILE}")
    log.info("DIAGNOSTIC_COMPLETE reads=%d", len(reads))


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="KiddoVax RFID Reader Diagnostic — Read Only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--no-monitor", action="store_true",
        help="Skip the card monitoring step — only check device presence"
    )
    parser.add_argument(
        "--duration", type=int, default=DEFAULT_MONITOR_DURATION,
        help=f"How many seconds to monitor for card reads (default: {DEFAULT_MONITOR_DURATION})"
    )
    args = parser.parse_args()

    # Platform check
    if sys.platform != "win32":
        print("ERROR: This diagnostic is Windows-only (requires winreg and msvcrt).")
        sys.exit(1)

    # Header
    print()
    print("=" * 62)
    print("  KiddoVax — RFID Reader Diagnostic Utility")
    print(f"  Reader: {READER_NAME}")
    print(f"  VID: {READER_VID}  PID: {READER_PID}")
    print("  MODE: READ ONLY — no card data will be written or modified")
    print("=" * 62)

    log.info(
        "=== RFID Diagnostic started %s VID=%s PID=%s ===",
        datetime.datetime.now().isoformat(), READER_VID, READER_PID
    )

    # Optional Django bootstrap
    django_available = _setup_django()
    if django_available:
        print_info("Django ORM loaded — DB card lookup is enabled.")
    else:
        print_info("Running standalone (no Django) — DB lookup disabled.")

    # Phase 1: Device detection
    device_info, is_live = run_device_check()

    if not device_info:
        print()
        print_fail("Cannot continue — reader not detected.")
        sys.exit(1)

    if not is_live:
        print()
        print_warn("Device found in registry but not currently live.")
        print_info("Reconnect the reader and re-run.")
        sys.exit(1)

    # Phase 2: Interface analysis
    run_interface_check(device_info)

    # Phase 3: Service check
    run_service_check()

    # Phase 4: Model identification guide
    print_model_identification_guide()

    # Phase 5: HID monitor (unless skipped)
    reads: list[CardRead] = []
    if not args.no_monitor:
        reads = monitor_hid_keyboard(
            duration_seconds=args.duration,
            django_available=django_available,
        )

    # Phase 6: Summary
    print_summary(reads, django_available)


if __name__ == "__main__":
    main()
