from __future__ import annotations

from datetime import datetime, timezone
import struct

from .client import ProtocolClient
from .constants import Command
from .errors import ProtocolError


class NetworkTime:
    def __init__(self, client: ProtocolClient) -> None:
        self._client = client

    @staticmethod
    def _datetime(data: bytes) -> datetime:
        if len(data) != 8:
            raise ProtocolError("time command returned an invalid payload")
        return datetime.fromtimestamp(struct.unpack("<Q", data)[0], tz=timezone.utc)

    def synchronize(self, server: str = "pool.ntp.org", *, utc_offset: int = 0,
                    daylight_offset: int = 0, timeout: float = 10.0) -> datetime:
        server_bytes = server.encode("ascii")
        if not 1 <= len(server_bytes) <= 63:
            raise ValueError("server must contain 1 to 63 ASCII bytes")
        if not -50_400 <= utc_offset <= 50_400:
            raise ValueError("utc_offset must be between -50400 and 50400 seconds")
        if not -7_200 <= daylight_offset <= 7_200:
            raise ValueError("daylight_offset must be between -7200 and 7200 seconds")
        if not 0.1 <= timeout <= 30:
            raise ValueError("timeout must be between 0.1 and 30 seconds")
        payload = struct.pack("<iiHB", utc_offset, daylight_offset,
                              round(timeout * 1000), len(server_bytes)) + server_bytes
        return self._datetime(self._client.request(
            Command.TIME_SYNC, payload,
            timeout=max(self._client.timeout, timeout + 1.0),
        ))

    def now(self) -> datetime:
        return self._datetime(self._client.request(Command.TIME_NOW))
