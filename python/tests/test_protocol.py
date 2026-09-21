import unittest

from starbridge.constants import Command, FrameKind
from starbridge.errors import ProtocolError
from starbridge.protocol import Frame, StreamDecoder, crc16_ccitt, decode_frame


class ProtocolTests(unittest.TestCase):
    def test_crc_standard_vector(self) -> None:
        self.assertEqual(crc16_ccitt(b"123456789"), 0x29B1)

    def test_golden_ping_frame(self) -> None:
        frame = Frame(FrameKind.REQUEST, 0x1234, Command.PING, b"abc")
        self.assertEqual(frame.encode().hex(), "a55a020134120103006162631dfc")
        self.assertEqual(decode_frame(frame.encode()), frame)

    def test_decoder_handles_chunking_and_noise(self) -> None:
        first = Frame(FrameKind.REQUEST, 1, Command.PING, b"one")
        second = Frame(FrameKind.RESPONSE, 1, Command.PING, b"\x00one")
        decoder = StreamDecoder()
        self.assertEqual(decoder.feed(b"noise" + first.encode()[:5]), [])
        self.assertEqual(decoder.feed(first.encode()[5:] + second.encode()), [first, second])

    def test_decoder_recovers_after_bad_crc(self) -> None:
        bad = bytearray(Frame(FrameKind.REQUEST, 1, Command.PING, b"bad").encode())
        bad[-1] ^= 0xFF
        good = Frame(FrameKind.REQUEST, 2, Command.PING, b"good")
        decoder = StreamDecoder()
        self.assertEqual(decoder.feed(bytes(bad) + good.encode()), [good])
        self.assertEqual(decoder.bad_crc_count, 1)

    def test_decode_requires_exactly_one_frame(self) -> None:
        with self.assertRaises(ProtocolError):
            decode_frame(b"garbage")
