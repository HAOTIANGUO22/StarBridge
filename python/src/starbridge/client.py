from __future__ import annotations

from collections import deque
import threading
import time

from .constants import Command, FrameKind, PROTOCOL_VERSION, Status
from .errors import (
    BoardCommandError,
    ConnectionClosedError,
    ProtocolError,
    RequestTimeoutError,
    command_name,
)
from .protocol import Frame, StreamDecoder
from .transport import Transport


class ProtocolClient:
    """Thread-safe synchronous request client with event preservation."""

    def __init__(self, transport: Transport, timeout: float = 1.0) -> None:
        self.transport = transport
        self.timeout = timeout
        self._sequence = 0
        self._lock = threading.Lock()
        self._decoder = StreamDecoder()
        self._events: deque[Frame] = deque()
        self._pending: deque[Frame] = deque()

    def _next_sequence(self) -> int:
        self._sequence = (self._sequence % 0xFFFF) + 1
        return self._sequence

    def request(
        self, command: Command | int, payload: bytes = b"", *, timeout: float | None = None
    ) -> bytes:
        with self._lock:
            if not self.transport.is_open:
                raise ConnectionClosedError("transport is closed")
            sequence = self._next_sequence()
            request = Frame(FrameKind.REQUEST, sequence, int(command), payload)
            self.transport.write(request.encode())
            request_timeout = self.timeout if timeout is None else timeout
            if request_timeout <= 0:
                raise ValueError("timeout must be positive")
            deadline = time.monotonic() + request_timeout
            while True:
                response = self._take_response(sequence, int(command))
                if response is not None:
                    return self._validate_response(response)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RequestTimeoutError(
                        f"{command_name(int(command))}超时：开发板在 {request_timeout:.1f} 秒内没有响应。"
                        "请检查 USB 连接、串口是否被其他程序占用，然后重新插拔开发板。"
                    )
                chunk = self.transport.read(64, min(remaining, 0.05))
                for frame in self._decoder.feed(chunk):
                    if frame.version != PROTOCOL_VERSION:
                        raise ProtocolError(
                            f"board protocol {frame.version} is incompatible with {PROTOCOL_VERSION}"
                        )
                    if frame.kind == FrameKind.EVENT:
                        self._events.append(frame)
                    else:
                        self._pending.append(frame)

    def _take_response(self, sequence: int, command: int) -> Frame | None:
        for frame in tuple(self._pending):
            if frame.kind == FrameKind.RESPONSE and frame.sequence == sequence and frame.command == command:
                self._pending.remove(frame)
                return frame
        return None

    @staticmethod
    def _validate_response(frame: Frame) -> bytes:
        if not frame.payload:
            raise ProtocolError("response is missing status byte")
        status = frame.payload[0]
        if status != Status.OK:
            raise BoardCommandError(status, frame.command)
        return frame.payload[1:]

    def pop_event(self) -> Frame | None:
        return self._events.popleft() if self._events else None

    def close(self) -> None:
        self.transport.close()
