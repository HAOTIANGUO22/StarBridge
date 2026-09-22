from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct

from .client import ProtocolClient
from .constants import Command
from .errors import ProtocolError


class WiFiStatus(IntEnum):
    IDLE = 0
    NO_SSID = 1
    SCAN_COMPLETED = 2
    CONNECTED = 3
    CONNECT_FAILED = 4
    CONNECTION_LOST = 5
    DISCONNECTED = 6


@dataclass(frozen=True, slots=True)
class WiFiInfo:
    status: WiFiStatus | int
    ip: str
    rssi: int
    mac: str
    channel: int

    @property
    def connected(self) -> bool:
        return self.status == WiFiStatus.CONNECTED


class WiFi:
    def __init__(self, client: ProtocolClient) -> None:
        self._client = client

    @staticmethod
    def _decode(data: bytes) -> WiFiInfo:
        if len(data) != 16:
            raise ProtocolError("WIFI_STATUS returned an invalid payload")
        raw_status, a, b, c, d, rssi, mac, channel = struct.unpack("<BBBBBi6sB", data)
        try:
            status: WiFiStatus | int = WiFiStatus(raw_status)
        except ValueError:
            status = raw_status
        return WiFiInfo(status, f"{a}.{b}.{c}.{d}", rssi,
                        ":".join(f"{byte:02X}" for byte in mac), channel)

    def connect(self, ssid: str, password: str = "", timeout: float = 15.0) -> WiFiInfo:
        ssid_bytes = ssid.encode("utf-8")
        password_bytes = password.encode("utf-8")
        if not 1 <= len(ssid_bytes) <= 32:
            raise ValueError("SSID must contain 1 to 32 UTF-8 bytes")
        if len(password_bytes) > 63:
            raise ValueError("password must contain at most 63 UTF-8 bytes")
        if not 0.1 <= timeout <= 30:
            raise ValueError("timeout must be between 0.1 and 30 seconds")
        payload = struct.pack("<HBB", round(timeout * 1000), len(ssid_bytes),
                              len(password_bytes)) + ssid_bytes + password_bytes
        return self._decode(self._client.request(
            Command.WIFI_CONNECT, payload,
            timeout=max(self._client.timeout, timeout + 1.0),
        ))

    def status(self) -> WiFiInfo:
        return self._decode(self._client.request(Command.WIFI_STATUS))

    def disconnect(self, *, erase_credentials: bool = False) -> None:
        self._client.request(Command.WIFI_DISCONNECT, bytes((erase_credentials,)))
