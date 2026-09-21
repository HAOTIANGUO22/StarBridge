import struct
import unittest

from fake_transport import FakeTransport
from starbridge import Board, Pin, PinMode
from starbridge.constants import Command, Status


def handler(request):
    if request.command == Command.PING:
        return Status.OK, request.payload
    if request.command == Command.GET_INFO:
        return Status.OK, struct.pack("<BBBBBI", 2, 2, 0, 0, 1, 0x0F)
    if request.command == Command.DIGITAL_READ:
        return Status.OK, b"\x01"
    if request.command == Command.ANALOG_READ:
        return Status.OK, struct.pack("<I", 2048)
    return Status.OK, b""


class BoardTests(unittest.TestCase):
    def test_high_level_api(self) -> None:
        transport = FakeTransport(handler)
        with Board.from_transport(transport, timeout=0.1) as board:
            self.assertEqual(board.ping(b"ready"), b"ready")
            self.assertEqual(board.info().firmware_major, 2)
            board.pin_mode(Pin.P0, PinMode.OUTPUT)
            board.digital_write(Pin.P0, True)
            self.assertTrue(board.digital_read(Pin.P0))
            self.assertEqual(board.analog_read(Pin.P0), 2048)
            board.analog_write(Pin.P9, 128)
            board.pwm_configure(Pin.P0, 1000, 8)
            board.pwm_write(Pin.P0, 127)
            board.pwm_stop(Pin.P0)
        self.assertFalse(transport.is_open)
