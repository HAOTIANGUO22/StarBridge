from __future__ import annotations

import struct

from .client import ProtocolClient
from .constants import Command, Pin
from .errors import ProtocolError


class MP3:
    def __init__(self, client: ProtocolClient, rx_pin: Pin | int,
                 tx_pin: Pin | int, busy_pin: Pin | int | None = None) -> None:
        busy = 0xFF if busy_pin is None else int(busy_pin)
        self._client = client
        self._client.request(Command.MP3_INIT, bytes((int(rx_pin), int(tx_pin), busy)))

    def play_track(self, track: int) -> None:
        if not 1 <= track <= 65535:
            raise ValueError("track must be between 1 and 65535")
        self._client.request(Command.MP3_PLAY_TRACK, struct.pack("<H", track))

    def play(self) -> None:
        self._client.request(Command.MP3_PLAY)

    def pause(self) -> None:
        self._client.request(Command.MP3_PAUSE)

    def stop(self) -> None:
        self._client.request(Command.MP3_STOP)

    def next(self) -> None:
        self._client.request(Command.MP3_NEXT)

    def previous(self) -> None:
        self._client.request(Command.MP3_PREVIOUS)

    def set_volume(self, volume: int) -> None:
        if not 0 <= volume <= 30:
            raise ValueError("volume must be between 0 and 30")
        self._client.request(Command.MP3_SET_VOLUME, bytes((volume,)))

    def status(self) -> int:
        data = self._client.request(Command.MP3_STATUS)
        if len(data) != 1:
            raise ProtocolError("MP3_STATUS returned an invalid payload")
        return data[0]

    def is_busy(self) -> bool:
        data = self._client.request(Command.MP3_BUSY)
        if len(data) != 1:
            raise ProtocolError("MP3_BUSY returned an invalid payload")
        return bool(data[0])
