from __future__ import annotations

import struct

from .client import ProtocolClient
from .constants import Command, Pin


def _color(red: int, green: int, blue: int, white: int) -> bytes:
    values = (red, green, blue, white)
    if any(value < 0 or value > 255 for value in values):
        raise ValueError("color channels must be between 0 and 255")
    return bytes(values)


class NeoPixel:
    def __init__(self, client: ProtocolClient, pin: Pin | int, count: int,
                 brightness: int = 255) -> None:
        if not 1 <= count <= 1024:
            raise ValueError("count must be between 1 and 1024")
        if not 0 <= brightness <= 255:
            raise ValueError("brightness must be between 0 and 255")
        self._client = client
        self.count = count
        self._client.request(Command.NEOPIXEL_INIT,
                             struct.pack("<BHB", int(pin), count, brightness))

    def set_pixel(self, index: int, red: int, green: int, blue: int,
                  white: int = 0) -> None:
        if not 0 <= index < self.count:
            raise IndexError("pixel index is out of range")
        self._client.request(Command.NEOPIXEL_SET,
                             struct.pack("<H", index) + _color(red, green, blue, white))

    def fill(self, red: int, green: int, blue: int, white: int = 0,
             *, first: int = 0, count: int | None = None) -> None:
        length = self.count - first if count is None else count
        if first < 0 or length <= 0 or first + length > self.count:
            raise ValueError("fill range is outside the strip")
        payload = struct.pack("<HH", first, length) + _color(red, green, blue, white)
        self._client.request(Command.NEOPIXEL_FILL, payload)

    def show(self) -> None:
        self._client.request(Command.NEOPIXEL_SHOW)

    def clear(self, *, show: bool = True) -> None:
        self._client.request(Command.NEOPIXEL_CLEAR)
        if show:
            self.show()
