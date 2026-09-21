from __future__ import annotations

from collections.abc import Callable

from starbridge.constants import FrameKind, Status
from starbridge.protocol import Frame, decode_frame


Handler = Callable[[Frame], tuple[int, bytes]]


class FakeTransport:
    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self._open = True
        self._incoming = bytearray()
        self.writes: list[bytes] = []

    @property
    def is_open(self) -> bool:
        return self._open

    def write(self, data: bytes) -> None:
        self.writes.append(data)
        request = decode_frame(data)
        status, payload = self.handler(request)
        response = Frame(
            FrameKind.RESPONSE,
            request.sequence,
            request.command,
            bytes((status,)) + payload,
        )
        self._incoming.extend(response.encode())

    def read(self, size: int, timeout: float) -> bytes:
        del timeout
        data = bytes(self._incoming[:size])
        del self._incoming[:size]
        return data

    def reset_input_buffer(self) -> None:
        self._incoming.clear()

    def close(self) -> None:
        self._open = False


def echo_handler(request: Frame) -> tuple[int, bytes]:
    return Status.OK, request.payload
