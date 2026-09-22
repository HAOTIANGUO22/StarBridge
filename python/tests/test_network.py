from __future__ import annotations

from contextlib import contextmanager
from datetime import timezone
import json
from pathlib import Path
import struct
import tempfile
import unittest

from fake_transport import FakeTransport
from starbridge import Board, CloudClient, Pin, WiFiStatus
from starbridge.constants import Command, Status


MAC = bytes.fromhex("AABBCCDDEEFF")


def handler(request):
    if request.command in (Command.WIFI_CONNECT, Command.WIFI_STATUS):
        return Status.OK, struct.pack("<BBBBBi6sB", 3, 192, 168, 1, 8, -55, MAC, 6)
    if request.command == Command.SOFTWARE_SERIAL_READ:
        return Status.OK, b"hello"
    if request.command == Command.SOFTWARE_SERIAL_AVAILABLE:
        return Status.OK, struct.pack("<H", 5)
    if request.command == Command.ESPNOW_LOCAL_MAC:
        return Status.OK, MAC
    if request.command == Command.ESPNOW_RECEIVE:
        return Status.OK, MAC + bytes((206, 6, 4)) + b"pong"
    if request.command in (Command.TIME_SYNC, Command.TIME_NOW):
        return Status.OK, struct.pack("<Q", 1_700_000_000)
    return Status.OK, b""


class NetworkModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = FakeTransport(handler)
        self.board = Board.from_transport(self.transport, timeout=0.1)

    def tearDown(self) -> None:
        self.board.close()

    def test_software_serial(self) -> None:
        serial = self.board.software_serial(Pin.P6, Pin.P7, 9600)
        serial.write(b"test")
        self.assertEqual(serial.available(), 5)
        self.assertEqual(serial.read(timeout=0.01), b"hello")
        serial.close()

    def test_wifi(self) -> None:
        info = self.board.wifi().connect("school", "password", timeout=0.1)
        self.assertEqual(info.status, WiFiStatus.CONNECTED)
        self.assertEqual(info.ip, "192.168.1.8")
        self.assertEqual(info.mac, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(info.rssi, -55)

    def test_espnow(self) -> None:
        radio = self.board.espnow(channel=6)
        radio.add_peer("11:22:33:44:55:66")
        radio.send("11:22:33:44:55:66", b"ping")
        message = radio.receive()
        self.assertIsNotNone(message)
        assert message is not None
        self.assertEqual(message.data, b"pong")
        self.assertEqual(message.rssi, -50)
        self.assertEqual(radio.local_mac(), "AA:BB:CC:DD:EE:FF")

    def test_network_time(self) -> None:
        clock = self.board.network_time()
        value = clock.synchronize(timeout=0.1)
        self.assertEqual(value.tzinfo, timezone.utc)
        self.assertEqual(clock.now().timestamp(), 1_700_000_000)


class FakeResponse:
    def __init__(self, value: dict) -> None:
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.value).encode()


class FakeOpener:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        return FakeResponse(self.responses.pop(0))


class CloudTests(unittest.TestCase):
    def test_time_weather_and_chat(self) -> None:
        opener = FakeOpener([
            {"datetime": "2026-09-22T10:00:00+08:00", "timezone": "Asia/Shanghai",
             "unixtime": 1_790_043_600},
            {"timezone": "Asia/Shanghai", "current": {
                "time": "2026-09-22T10:00", "temperature_2m": 25.5,
                "relative_humidity_2m": 60, "apparent_temperature": 26,
                "precipitation": 0, "weather_code": 1, "wind_speed_10m": 8,
            }},
            {"choices": [{"message": {"content": "你好"}}]},
        ])
        cloud = CloudClient(opener=opener)
        self.assertEqual(cloud.time().timezone, "Asia/Shanghai")
        self.assertEqual(cloud.weather(31.23, 121.47).temperature_c, 25.5)
        self.assertEqual(cloud.chat("你好", api_key="test-key"), "你好")
        self.assertTrue(opener.requests[-1][0].full_url.endswith("/chat/completions"))

    def test_transcription_multipart(self) -> None:
        opener = FakeOpener([{"text": "测试语音"}])
        cloud = CloudClient(opener=opener)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.wav"
            path.write_bytes(b"RIFFtest")
            self.assertEqual(cloud.transcribe(path, api_key="test-key"), "测试语音")
        request = opener.requests[0][0]
        self.assertIn(b'name="file"', request.data)
        self.assertIn(b'gpt-4o-mini-transcribe', request.data)


if __name__ == "__main__":
    unittest.main()
