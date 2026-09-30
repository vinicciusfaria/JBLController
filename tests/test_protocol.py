import unittest
from jbl_controller.protocol import (
    build_command, build_field, build_set_light_info, parse_notification,
    CMD_SET_LIGHT_INFO, FIELD_BRIGHTNESS, FIELD_COLOR, FIELD_PATTERN,
    HEADER_IDENTIFIER, PAYLOAD_START_BYTE
)
from jbl_controller.exceptions import ProtocolError

class TestProtocol(unittest.TestCase):

    def test_build_field(self):
        f = build_field(FIELD_BRIGHTNESS, bytes([100]))
        self.assertEqual(f, bytes([0x45, 0x01, 100]))

    def test_build_command(self):
        # build_command(cmd, fields) -> [AA] [CMD] [LEN] [00] [fields]
        cmd = build_command(CMD_SET_LIGHT_INFO, bytes([0x45, 0x01, 100]))
        # fields len = 3, payload len = 1 (for 00) + 3 = 4
        self.assertEqual(cmd, bytes([0xAA, 0x33, 0x04, 0x00, 0x45, 0x01, 100]))

    def test_build_set_light_info_single(self):
        cmd = build_set_light_info([(FIELD_BRIGHTNESS, bytes([0x64]))])
        self.assertEqual(cmd, bytes([0xAA, 0x33, 0x04, 0x00, 0x45, 0x01, 0x64]))

    def test_build_set_light_info_multiple(self):
        fields = [
            (FIELD_PATTERN, bytes([0x15])),
            (FIELD_COLOR, bytes([0xFF, 0x00, 0x00]))
        ]
        cmd = build_set_light_info(fields)
        # Payload len: 1 (00) + 3 (Pattern) + 5 (Color) = 9
        self.assertEqual(cmd, bytes([0xAA, 0x33, 0x09, 0x00, 0x31, 0x01, 0x15, 0x32, 0x03, 0xFF, 0x00, 0x00]))

    def test_parse_notification_valid(self):
        # [AA] [32] [09] [00] [45 01 64] [49 01 01]
        data = bytes([0xAA, 0x32, 0x07, 0x00, 0x45, 0x01, 0x64, 0x49, 0x01, 0x01])
        cmd_id, fields = parse_notification(data)
        self.assertEqual(cmd_id, 0x32)
        self.assertIn(0x45, fields)
        self.assertEqual(fields[0x45], bytes([0x64]))
        self.assertIn(0x49, fields)
        self.assertEqual(fields[0x49], bytes([0x01]))

    def test_parse_notification_invalid_header(self):
        data = bytes([0xBB, 0x32, 0x04, 0x00, 0x45, 0x01, 0x64])
        with self.assertRaises(ProtocolError):
            parse_notification(data)

    def test_parse_notification_too_short(self):
        data = bytes([0xAA, 0x32, 0x04])
        with self.assertRaises(ProtocolError):
            parse_notification(data)

if __name__ == "__main__":
    unittest.main()

