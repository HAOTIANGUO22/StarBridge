from __future__ import annotations

from dataclasses import dataclass
import struct

from .constants import FrameKind, MAX_PAYLOAD, PROTOCOL_VERSION
from .errors import ProtocolError


SOF = b"\xA5\x5A"
_HEADER = struct.Struct("<BBHBH")
_CRC = struct.Struct("<H")
MIN_FRAME_SIZE = len(SOF) + _HEADER.size + _CRC.size


def crc16_ccitt(data: bytes, initial: int = 0xFFFF) -> int:
    crc = initial
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass(frozen=True, slots=True)
class Frame:
    kind: FrameKind
    sequence: int
    command: int
    payload: bytes = b""
    version: int = PROTOCOL_VERSION

    def encode(self) -> bytes:
        if not 0 <= self.sequence <= 0xFFFF:
            raise ValueError("sequence must fit in uint16")
        if not 0 <= self.command <= 0xFF:
            raise ValueError("command must fit in uint8")
        if len(self.payload) > MAX_PAYLOAD:
            raise ValueError(f"payload exceeds {MAX_PAYLOAD} bytes")
        body = _HEADER.pack(
            self.version,
            int(self.kind),
            self.sequence,
            self.command,
            len(self.payload),
        ) + self.payload
        return SOF + body + _CRC.pack(crc16_ccitt(body))


class StreamDecoder:
    """Incremental decoder that resynchronizes after noise or corrupt frames."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self.bad_crc_count = 0
        self.bad_length_count = 0

    def reset(self) -> None:
        self._buffer.clear()

    def feed(self, data: bytes) -> list[Frame]:
        self._buffer.extend(data)
        frames: list[Frame] = []
        while True:
            start = self._buffer.find(SOF)
            if start < 0:
                if self._buffer[-1:] == SOF[:1]:
                    del self._buffer[:-1]
                else:
                    self._buffer.clear()
                break
            if start:
                del self._buffer[:start]
            if len(self._buffer) < MIN_FRAME_SIZE:
                break
            version, raw_kind, sequence, command, length = _HEADER.unpack_from(self._buffer, len(SOF))
            if length > MAX_PAYLOAD:
                self.bad_length_count += 1
                del self._buffer[0]
                continue
            frame_size = MIN_FRAME_SIZE + length
            if len(self._buffer) < frame_size:
                break
            body_end = len(SOF) + _HEADER.size + length
            body = bytes(self._buffer[len(SOF):body_end])
            expected_crc = _CRC.unpack_from(self._buffer, body_end)[0]
            if crc16_ccitt(body) != expected_crc:
                self.bad_crc_count += 1
                del self._buffer[0]
                continue
            try:
                kind = FrameKind(raw_kind)
            except ValueError:
                del self._buffer[:frame_size]
                continue
            frames.append(Frame(kind, sequence, command, body[_HEADER.size:], version))
            del self._buffer[:frame_size]
        return frames


def decode_frame(data: bytes) -> Frame:
    decoder = StreamDecoder()
    frames = decoder.feed(data)
    if len(frames) != 1 or decoder._buffer:
        raise ProtocolError("expected exactly one complete frame")
    return frames[0]

