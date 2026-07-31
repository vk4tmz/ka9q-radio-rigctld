import unittest

from status import parsePacket


class ParsePacketTests(unittest.TestCase):
    def test_unknown_status_type_is_preserved(self):
        packet = bytes([117, 0, 0])

        result = parsePacket(packet)

        self.assertEqual(result[117], b"")


if __name__ == "__main__":
    unittest.main()
