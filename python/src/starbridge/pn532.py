from __future__ import annotations

from dataclasses import dataclass
import struct

from .client import ProtocolClient
from .constants import Command, Pin
from .errors import ProtocolError


@dataclass(frozen=True, slots=True)
class PN532FirmwareInfo:
    ic: int
    major: int
    minor: int
    support: int


class PN532:
    """Generic PN532 NFC reader connected through the board's I2C bus."""

    I2C_ADDRESS = 0x24
    DEFAULT_KEY = b"\xff" * 6

    def __init__(
        self,
        client: ProtocolClient,
        irq_pin: Pin | int | None = None,
        reset_pin: Pin | int | None = None,
    ) -> None:
        self._client = client
        self._irq_pin = self._optional_pin(irq_pin)
        self._reset_pin = self._optional_pin(reset_pin)
        self._firmware: PN532FirmwareInfo | None = None

    def begin(self) -> "PN532":
        data = self._client.request(
            Command.PN532_INIT,
            bytes((self._irq_pin, self._reset_pin)),
        )
        self._firmware = self._decode_firmware(data)
        return self

    def firmware_info(self) -> PN532FirmwareInfo:
        data = self._client.request(Command.PN532_FIRMWARE_VERSION)
        self._firmware = self._decode_firmware(data)
        return self._firmware

    def scan(self, timeout: float = 0.25) -> bytes | None:
        """Return the first ISO14443A tag UID, or ``None`` when no tag is present."""
        timeout_ms = round(timeout * 1000)
        if not 1 <= timeout_ms <= 800:
            raise ValueError("timeout must be between 0.001 and 0.8 seconds")
        data = self._client.request(Command.PN532_SCAN, struct.pack("<H", timeout_ms))
        if not data:
            raise ProtocolError("PN532_SCAN returned an empty payload")
        uid_length = data[0]
        if uid_length == 0:
            if len(data) != 1:
                raise ProtocolError("PN532_SCAN returned invalid no-tag data")
            return None
        if uid_length not in (4, 7) or len(data) != uid_length + 1:
            raise ProtocolError("PN532_SCAN returned an invalid UID")
        return bytes(data[1:])

    def read_mifare_classic(
        self,
        block: int,
        *,
        key: bytes = DEFAULT_KEY,
        key_b: bool = False,
    ) -> bytes:
        self._block(block)
        key = self._key(key)
        data = self._client.request(
            Command.PN532_CLASSIC_READ,
            bytes((block, int(key_b))) + key,
        )
        if len(data) != 16:
            raise ProtocolError("PN532_CLASSIC_READ returned an invalid payload")
        return data

    def write_mifare_classic(
        self,
        block: int,
        data: bytes,
        *,
        key: bytes = DEFAULT_KEY,
        key_b: bool = False,
        allow_trailer: bool = False,
    ) -> None:
        self._block(block)
        if self._is_trailer_block(block) and not allow_trailer:
            raise ValueError(
                "refusing to overwrite a MIFARE sector trailer; "
                "pass allow_trailer=True only when changing keys or access bits intentionally"
            )
        if len(data) != 16:
            raise ValueError("MIFARE Classic block data must contain exactly 16 bytes")
        key = self._key(key)
        self._client.request(
            Command.PN532_CLASSIC_WRITE,
            bytes((block, int(key_b))) + key + data,
        )

    def read_page(self, page: int) -> bytes:
        self._page(page)
        data = self._client.request(Command.PN532_PAGE_READ, bytes((page,)))
        if len(data) != 4:
            raise ProtocolError("PN532_PAGE_READ returned an invalid payload")
        return data

    def write_page(self, page: int, data: bytes, *, unsafe: bool = False) -> None:
        self._page(page)
        # Pages 4..39 are the common user-memory range shared by NTAG213,
        # NTAG215/216 and the usual Ultralight layouts. Larger tags expose
        # more user pages, but their lock/configuration boundary varies.
        if not unsafe and not 4 <= page <= 39:
            raise ValueError(
                "page is outside the universally safe 4..39 user range; "
                "pass unsafe=True only after checking the exact tag memory map"
            )
        if len(data) != 4:
            raise ValueError("NTAG/Ultralight page data must contain exactly 4 bytes")
        self._client.request(Command.PN532_PAGE_WRITE, bytes((page,)) + data)

    @staticmethod
    def _decode_firmware(data: bytes) -> PN532FirmwareInfo:
        if len(data) != 4:
            raise ProtocolError("PN532 firmware query returned an invalid payload")
        raw = struct.unpack("<I", data)[0]
        info = PN532FirmwareInfo(
            ic=(raw >> 24) & 0xFF,
            major=(raw >> 16) & 0xFF,
            minor=(raw >> 8) & 0xFF,
            support=raw & 0xFF,
        )
        if info.ic != 0x32:
            raise ProtocolError(f"I2C device is not a PN532 (chip id 0x{info.ic:02X})")
        return info

    @staticmethod
    def _optional_pin(pin: Pin | int | None) -> int:
        if pin is None:
            return 0xFF
        value = int(pin)
        if not 0 <= value < 0xFF:
            raise ValueError("optional PN532 pin must be between 0 and 254")
        return value

    @staticmethod
    def _block(block: int) -> None:
        if not 0 <= block <= 255:
            raise ValueError("MIFARE Classic block must be between 0 and 255")

    @staticmethod
    def _page(page: int) -> None:
        if not 0 <= page <= 230:
            raise ValueError("NTAG/Ultralight page must be between 0 and 230")

    @staticmethod
    def _key(key: bytes) -> bytes:
        key = bytes(key)
        if len(key) != 6:
            raise ValueError("MIFARE Classic key must contain exactly 6 bytes")
        return key

    @staticmethod
    def _is_trailer_block(block: int) -> bool:
        return (block + 1) % (4 if block < 128 else 16) == 0
