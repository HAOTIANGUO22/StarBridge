import unittest

from fake_transport import FakeTransport, echo_handler
from starbridge.client import ProtocolClient
from starbridge.constants import Command, Status
from starbridge.errors import BoardCommandError


class ClientTests(unittest.TestCase):
    def test_request_response_round_trip(self) -> None:
        client = ProtocolClient(FakeTransport(echo_handler), timeout=0.1)
        self.assertEqual(client.request(Command.PING, b"hello"), b"hello")

    def test_sequence_increments(self) -> None:
        transport = FakeTransport(echo_handler)
        client = ProtocolClient(transport, timeout=0.1)
        client.request(Command.PING)
        client.request(Command.PING)
        self.assertEqual(transport.writes[0][4:6], b"\x01\x00")
        self.assertEqual(transport.writes[1][4:6], b"\x02\x00")

    def test_remote_error_is_typed(self) -> None:
        transport = FakeTransport(lambda request: (Status.BAD_ARGUMENT, b""))
        client = ProtocolClient(transport, timeout=0.1)
        with self.assertRaises(BoardCommandError) as caught:
            client.request(Command.DIGITAL_WRITE, b"\xff\x01")
        self.assertEqual(caught.exception.status, Status.BAD_ARGUMENT)
        self.assertIn("数字输出失败", str(caught.exception))
        self.assertIn("解决建议", str(caught.exception))

    def test_sensor_error_explains_likely_fix(self) -> None:
        transport = FakeTransport(lambda request: (Status.BAD_ARGUMENT, b""))
        client = ProtocolClient(transport, timeout=0.1)
        with self.assertRaises(BoardCommandError) as caught:
            client.request(Command.ULTRASONIC_READ, b"\x00" * 6)
        message = str(caught.exception)
        self.assertIn("超声波测距失败", message)
        self.assertIn("TRIG/ECHO", message)
        self.assertIn("物体紧贴探头", message)
