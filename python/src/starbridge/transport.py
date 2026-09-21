from __future__ import annotations

from typing import Protocol, runtime_checkable

from .errors import ConnectionClosedError


@runtime_checkable
class Transport(Protocol):
    @property
    def is_open(self) -> bool: ...
    def write(self, data: bytes) -> None: ...
    def read(self, size: int, timeout: float) -> bytes: ...
    def reset_input_buffer(self) -> None: ...
    def close(self) -> None: ...


class SerialTransport:
    def __init__(self, port: str, baudrate: int = 115200) -> None:
        from ._vendor import serial

        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=0,
            write_timeout=1.0,
            exclusive=None,
        )

    @property
    def is_open(self) -> bool:
        return bool(self._serial.is_open)

    def write(self, data: bytes) -> None:
        if not self.is_open:
            raise ConnectionClosedError("serial port is closed")
        written = self._serial.write(data)
        if written != len(data):
            raise ConnectionClosedError("short serial write")
        self._serial.flush()

    def read(self, size: int, timeout: float) -> bytes:
        if not self.is_open:
            raise ConnectionClosedError("serial port is closed")
        previous = self._serial.timeout
        self._serial.timeout = timeout
        try:
            return self._serial.read(size)
        finally:
            self._serial.timeout = previous

    def reset_input_buffer(self) -> None:
        self._serial.reset_input_buffer()

    def close(self) -> None:
        if self.is_open:
            self._serial.close()
