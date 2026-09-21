from __future__ import annotations

from dataclasses import dataclass
import struct

from .client import ProtocolClient
from .constants import Command, Pin
from .errors import ProtocolError


@dataclass(frozen=True, slots=True)
class DHT11Reading:
    temperature_c: float
    humidity_percent: float


class DHT11:
    def __init__(self, client: ProtocolClient, pin: Pin | int) -> None:
        self._client = client
        self._pin = int(pin)

    def read(self) -> DHT11Reading:
        data = self._client.request(Command.DHT11_READ, bytes((self._pin,)))
        if len(data) != 4:
            raise ProtocolError("DHT11_READ returned an invalid payload")
        temperature, humidity = struct.unpack("<hH", data)
        return DHT11Reading(temperature / 10.0, humidity / 10.0)


class Ultrasonic:
    def __init__(self, client: ProtocolClient, trigger_pin: Pin | int,
                 echo_pin: Pin | int, timeout_us: int = 30_000) -> None:
        if not 1_000 <= timeout_us <= 100_000:
            raise ValueError("timeout_us must be between 1,000 and 100,000")
        self._client = client
        self._trigger = int(trigger_pin)
        self._echo = int(echo_pin)
        self._timeout_us = timeout_us

    def read_mm(self) -> int:
        payload = struct.pack("<BBI", self._trigger, self._echo, self._timeout_us)
        data = self._client.request(Command.ULTRASONIC_READ, payload)
        if len(data) != 4:
            raise ProtocolError("ULTRASONIC_READ returned an invalid payload")
        return struct.unpack("<I", data)[0]

    def read_cm(self) -> float:
        return self.read_mm() / 10.0
