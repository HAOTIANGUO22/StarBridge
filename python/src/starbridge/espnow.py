from __future__ import annotations

from dataclasses import dataclass

from .client import ProtocolClient
from .constants import Command, Status
from .errors import BoardCommandError, ProtocolError


def normalize_mac(mac: str | bytes | bytearray) -> bytes:
    if isinstance(mac, str):
        try:
            raw = bytes.fromhex(mac.replace(":", "").replace("-", ""))
        except ValueError as error:
            raise ValueError("MAC address must contain six hexadecimal bytes") from error
    else:
        raw = bytes(mac)
    if len(raw) != 6:
        raise ValueError("MAC address must contain six bytes")
    return raw


@dataclass(frozen=True, slots=True)
class ESPNowMessage:
    mac: str
    data: bytes
    rssi: int
    channel: int


class ESPNow:
    def __init__(self, client: ProtocolClient, channel: int = 0) -> None:
        if not 0 <= channel <= 14:
            raise ValueError("channel must be 0 or between 1 and 14")
        self._client = client
        client.request(Command.ESPNOW_INIT, bytes((channel,)))

    def add_peer(self, mac: str | bytes, *, channel: int = 0,
                 key: bytes | None = None) -> None:
        if not 0 <= channel <= 14:
            raise ValueError("channel must be 0 or between 1 and 14")
        if key is not None and len(key) != 16:
            raise ValueError("ESP-NOW LMK must contain exactly 16 bytes")
        self._client.request(Command.ESPNOW_ADD_PEER,
                             normalize_mac(mac) + bytes((channel, key is not None)) +
                             (key if key is not None else bytes(16)))

    def remove_peer(self, mac: str | bytes) -> None:
        self._client.request(Command.ESPNOW_REMOVE_PEER, normalize_mac(mac))

    def send(self, mac: str | bytes, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        if not 1 <= len(raw) <= 240:
            raise ValueError("ESP-NOW data must contain 1 to 240 bytes")
        self._client.request(Command.ESPNOW_SEND, normalize_mac(mac) + raw)

    def receive(self) -> ESPNowMessage | None:
        try:
            data = self._client.request(Command.ESPNOW_RECEIVE)
        except BoardCommandError as error:
            if error.status == Status.BUSY:
                return None
            raise
        if len(data) < 9 or len(data) != 9 + data[8]:
            raise ProtocolError("ESPNOW_RECEIVE returned an invalid payload")
        mac = ":".join(f"{byte:02X}" for byte in data[:6])
        rssi = data[6] - 256 if data[6] >= 128 else data[6]
        return ESPNowMessage(mac, data[9:], rssi, data[7])

    def local_mac(self) -> str:
        data = self._client.request(Command.ESPNOW_LOCAL_MAC)
        if len(data) != 6:
            raise ProtocolError("ESPNOW_LOCAL_MAC returned an invalid payload")
        return ":".join(f"{byte:02X}" for byte in data)
