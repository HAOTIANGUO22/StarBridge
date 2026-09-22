from __future__ import annotations

import struct

from .client import ProtocolClient
from .constants import Command, Pin
from .errors import ProtocolError


class SoftwareSerial:
    def __init__(self, client: ProtocolClient, rx_pin: Pin | int, tx_pin: Pin | int,
                 baudrate: int = 9600) -> None:
        if not 300 <= baudrate <= 230_400:
            raise ValueError("baudrate must be between 300 and 230400")
        self._client = client
        client.request(Command.SOFTWARE_SERIAL_INIT,
                       struct.pack("<BBI", int(rx_pin), int(tx_pin), baudrate))

    def write(self, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        if not 1 <= len(raw) <= 255:
            raise ValueError("data must contain 1 to 255 bytes")
        self._client.request(Command.SOFTWARE_SERIAL_WRITE, raw)

    def read(self, maximum: int = 250, timeout: float = 0.0) -> bytes:
        if not 1 <= maximum <= 250:
            raise ValueError("maximum must be between 1 and 250")
        if not 0 <= timeout <= 5:
            raise ValueError("timeout must be between 0 and 5 seconds")
        timeout_ms = round(timeout * 1000)
        data = self._client.request(
            Command.SOFTWARE_SERIAL_READ,
            struct.pack("<BH", maximum, timeout_ms),
            timeout=max(self._client.timeout, timeout + 0.5),
        )
        if len(data) > maximum:
            raise ProtocolError("SOFTWARE_SERIAL_READ returned too much data")
        return data

    def available(self) -> int:
        data = self._client.request(Command.SOFTWARE_SERIAL_AVAILABLE)
        if len(data) != 2:
            raise ProtocolError("SOFTWARE_SERIAL_AVAILABLE returned an invalid payload")
        return struct.unpack("<H", data)[0]

    def close(self) -> None:
        self._client.request(Command.SOFTWARE_SERIAL_END)
