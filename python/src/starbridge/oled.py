from __future__ import annotations

from .client import ProtocolClient
from .constants import Command, MAX_PAYLOAD, OledFont


class OLED:
    """Buffered SSD1306 128x64 display controlled by DFRobot U8g2 firmware."""

    WIDTH = 128
    HEIGHT = 64

    def __init__(self, client: ProtocolClient) -> None:
        self._client = client

    def begin(self, address: int = 0x3C, *, rotate180: bool = False) -> "OLED":
        if not 0x08 <= address <= 0x77:
            raise ValueError("I2C address must be between 0x08 and 0x77")
        self._client.request(Command.OLED_INIT, bytes((address, int(rotate180))))
        return self

    def clear(self, *, white: bool = False) -> None:
        self._client.request(Command.OLED_CLEAR, bytes((int(white),)))

    def show(self) -> None:
        self._client.request(Command.OLED_SHOW)

    def text(
        self,
        x: int,
        baseline: int,
        text: str,
        *,
        font: OledFont = OledFont.CHINESE_GB2312_12,
    ) -> None:
        self._point(x, baseline)
        encoded = str(text).encode("utf-8")
        if not encoded or len(encoded) > 250:
            raise ValueError("UTF-8 text must contain 1 to 250 bytes")
        self._client.request(Command.OLED_TEXT, bytes((x, baseline, int(font))) + encoded)

    def pixel(self, x: int, y: int, *, white: bool = True) -> None:
        self._point(x, y)
        self._client.request(Command.OLED_PIXEL, bytes((x, y, int(white))))

    def line(self, x0: int, y0: int, x1: int, y1: int, *, white: bool = True) -> None:
        self._point(x0, y0)
        self._point(x1, y1)
        self._client.request(Command.OLED_LINE, bytes((x0, y0, x1, y1, int(white))))

    def rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        filled: bool = False,
        white: bool = True,
    ) -> None:
        self._region(x, y, width, height)
        self._client.request(
            Command.OLED_RECT,
            bytes((x, y, width, height, int(filled), int(white))),
        )

    def bitmap(self, x: int, y: int, width: int, height: int, data: bytes) -> None:
        """Draw XBM/LSB-first data, splitting it into protocol-safe horizontal strips."""
        self._region(x, y, width, height)
        row_bytes = (width + 7) // 8
        expected = row_bytes * height
        if len(data) != expected:
            raise ValueError(f"bitmap requires {expected} bytes, got {len(data)}")
        rows_per_chunk = (MAX_PAYLOAD - 4) // row_bytes
        if rows_per_chunk == 0:
            raise ValueError("bitmap row is wider than the protocol payload")
        row = 0
        while row < height:
            rows = min(rows_per_chunk, height - row)
            start = row * row_bytes
            end = start + rows * row_bytes
            payload = bytes((x, y + row, width, rows)) + data[start:end]
            self._client.request(Command.OLED_BITMAP, payload)
            row += rows

    @classmethod
    def _point(cls, x: int, y: int) -> None:
        if not 0 <= x < cls.WIDTH or not 0 <= y < cls.HEIGHT:
            raise ValueError("OLED coordinate is outside 128x64")

    @classmethod
    def _region(cls, x: int, y: int, width: int, height: int) -> None:
        cls._point(x, y)
        if width <= 0 or height <= 0 or x + width > cls.WIDTH or y + height > cls.HEIGHT:
            raise ValueError("OLED region is outside 128x64")

