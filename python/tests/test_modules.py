import struct
import unittest

from fake_transport import FakeTransport
from starbridge import Board, Pin
from starbridge.constants import Command, Status


def handler(request):
    if request.command == Command.DHT11_READ:
        return Status.OK, struct.pack("<hH", 235, 618)
    if request.command == Command.ULTRASONIC_READ:
        return Status.OK, struct.pack("<I", 1234)
    if request.command == Command.MP3_STATUS:
        return Status.OK, b"\x02"
    if request.command == Command.MP3_BUSY:
        return Status.OK, b"\x01"
    return Status.OK, b""


class ModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = FakeTransport(handler)
        self.board = Board.from_transport(self.transport, timeout=0.1)

    def tearDown(self) -> None:
        self.board.close()

    def test_dht11_and_ultrasonic(self) -> None:
        reading = self.board.dht11(Pin.P0).read()
        self.assertEqual(reading.temperature_c, 23.5)
        self.assertEqual(reading.humidity_percent, 61.8)
        sonar = self.board.ultrasonic(Pin.P0, Pin.P1)
        self.assertEqual(sonar.read_mm(), 1234)
        self.assertEqual(sonar.read_cm(), 123.4)

    def test_neopixel_commands(self) -> None:
        pixels = self.board.neopixel(Pin.P0, 8, brightness=64)
        pixels.set_pixel(2, 10, 20, 30)
        pixels.fill(1, 2, 3, first=1, count=3)
        pixels.show()
        pixels.clear()
        commands = [frame[6] for frame in self.transport.writes]
        self.assertEqual(commands, [Command.NEOPIXEL_INIT, Command.NEOPIXEL_SET,
                                    Command.NEOPIXEL_FILL, Command.NEOPIXEL_SHOW,
                                    Command.NEOPIXEL_CLEAR, Command.NEOPIXEL_SHOW])

    def test_mp3_commands(self) -> None:
        mp3 = self.board.mp3(Pin.P6, Pin.P7, Pin.P8)
        mp3.play_track(258)
        mp3.set_volume(20)
        mp3.pause()
        mp3.play()
        mp3.stop()
        mp3.next()
        mp3.previous()
        self.assertEqual(mp3.status(), 2)
        self.assertTrue(mp3.is_busy())

    def test_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.board.neopixel(Pin.P0, 0)
        mp3 = self.board.mp3(Pin.P6, Pin.P7)
        with self.assertRaises(ValueError):
            mp3.set_volume(31)
        with self.assertRaises(ValueError):
            self.board.ultrasonic(Pin.P0, Pin.P1, timeout_us=999)


if __name__ == "__main__":
    unittest.main()
