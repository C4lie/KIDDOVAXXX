"""
tools/test_rfid_writer.py
=========================
Unit tests for RFIDHardwareService (dry-run, read, write, verify, hardware checks).
"""

import unittest
from tools.rfid_writer_app import RFIDHardwareService, HardwareStatus, CardState


class TestRFIDHardwareService(unittest.TestCase):
    def setUp(self):
        self.service = RFIDHardwareService(dry_run=True)

    def test_connect_dry_run(self):
        status = self.service.connect_reader()
        self.assertTrue(status.is_connected)
        self.assertTrue(status.is_writable)
        self.assertIn("Dry-Run", status.interface_type)

    def test_read_card_dry_run(self):
        self.service.connect_reader()
        success, card, msg = self.service.read_card()
        self.assertTrue(success)
        self.assertTrue(card.detected)
        self.assertIsNotNone(card.uid)

    def test_write_and_verify_card_dry_run(self):
        self.service.connect_reader()
        target_number = "100001"
        
        # Write
        write_success, write_msg = self.service.write_card(target_number, card_uid="TEST_CARD_99")
        self.assertTrue(write_success)
        self.assertIn("DRY-RUN SUCCESS", write_msg)

        # Verify matching
        verify_success, verify_msg = self.service.verify_card(target_number)
        self.assertTrue(verify_success)
        self.assertIn("VERIFIED MATCH", verify_msg)

        # Verify mismatch
        mismatch_success, mismatch_msg = self.service.verify_card("999999")
        self.assertFalse(mismatch_success)
        self.assertIn("VERIFICATION FAILED", mismatch_msg)

    def test_hid_wedge_card_read(self):
        self.service.dry_run = False
        self.service.hardware_status = HardwareStatus(
            is_connected=True,
            device_name="SYRIS EasyPOD",
            interface_type="USB HID Keyboard Wedge (Read-Only Transponder)",
            is_writable=False
        )
        success, card, msg = self.service.read_card(wedge_input="10384721")
        self.assertTrue(success)
        self.assertEqual(card.uid, "10384721")

    def test_empty_target_number_validation(self):
        success, msg = self.service.write_card("")
        self.assertFalse(success)
        self.assertIn("cannot be empty", msg)


if __name__ == "__main__":
    unittest.main()
