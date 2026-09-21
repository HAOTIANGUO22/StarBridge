import unittest

from fake_transport import FakeTransport
from starbridge import Board, OledFont
from starbridge.constants import Command, Status


class OledTests(unittest.TestCase):
    def setUp(self) -> None:
        self.requests = []

        def handler(request):
            self.requests.append(request)
            return Status.OK, b""

        self.transport = FakeTransport(handler)
        self.board = Board.from_transport(self.transport, timeout=0.1)

    def tearDown(self) -> None:
        self.board.close()

    def test_chinese_text_is_utf8(self) -> None:
        oled = self.board.oled().begin()
        oled.clear()
        oled.text(0, 14, "你好，星环", font=OledFont.CHINESE_GB2312_12)
        oled.show()
        text_request = next(item for item in self.requests if item.command == Command.OLED_TEXT)
        self.assertEqual(text_request.payload[:3], b"\x00\x0e\x01")
        self.assertEqual(text_request.payload[3:].decode("utf-8"), "你好，星环")

    def test_full_screen_bitmap_is_split(self) -> None:
        oled = self.board.oled()
        oled.bitmap(0, 0, 128, 64, bytes(1024))
        chunks = [item for item in self.requests if item.command == Command.OLED_BITMAP]
        self.assertEqual(len(chunks), 5)
        self.assertTrue(all(len(item.payload) <= 256 for item in chunks))

    def test_out_of_range_region_is_rejected_locally(self) -> None:
        with self.assertRaises(ValueError):
            self.board.oled().rect(120, 60, 16, 8)
