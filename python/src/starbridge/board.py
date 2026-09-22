from __future__ import annotations

from dataclasses import dataclass
import struct
import time
from pathlib import Path

from .client import ProtocolClient
from .constants import BoardType, Command, Pin, PinMode
from .boards import BoardProfile, get_board_profile
from .errors import FirmwareInstallError, ProtocolError, StarBridgeError, UnsupportedBoardError
from .programmer import FirmwareProgrammer, discover_port
from .transport import SerialTransport, Transport
from .oled import OLED
from .mp3 import MP3
from .pn532 import PN532
from .neopixel import NeoPixel
from .sensors import DHT11, Ultrasonic
from .software_serial import SoftwareSerial
from .wifi import WiFi
from .espnow import ESPNow
from .network_time import NetworkTime


@dataclass(frozen=True, slots=True)
class BoardInfo:
    protocol_version: int
    firmware_major: int
    firmware_minor: int
    firmware_patch: int
    board_id: int
    capabilities: int


class Board:
    def __init__(self, client: ProtocolClient) -> None:
        self._client = client

    @classmethod
    def connect(cls, port: str, baudrate: int = 115200, timeout: float = 1.0) -> "Board":
        board = cls(ProtocolClient(SerialTransport(port, baudrate), timeout))
        try:
            board.ping()
            return board
        except Exception:
            board.close()
            raise

    @classmethod
    def begin(
        cls,
        board: BoardType | str,
        *,
        port: str | None = None,
        flash_if_needed: bool = True,
        force_flash: bool = False,
        timeout: float = 1.0,
        project_root: str | Path | None = None,
        arduino_cli: str | Path | None = None,
    ) -> "Board":
        """Find a board, provision compatible firmware once, then connect.

        Existing compatible firmware is reused. Set ``force_flash=True`` to
        upload again even when the board already answers correctly.
        """
        profile = get_board_profile(board)
        selected_port = discover_port(profile, port)
        if not force_flash:
            connected = cls._connect_if_compatible(selected_port, profile, timeout)
            if connected is not None:
                return connected
        if not flash_if_needed:
            raise FirmwareInstallError(
                f"{profile.display_name} does not have compatible StarBridge firmware"
            )
        if not profile.has_firmware:
            raise UnsupportedBoardError(
                f"{profile.display_name} is registered, but its StarBridge firmware is not implemented yet"
            )
        FirmwareProgrammer(project_root, arduino_cli).flash(profile, selected_port)

        deadline = time.monotonic() + 12.0
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                refreshed_port = discover_port(profile, selected_port)
                connected = cls._connect_if_compatible(refreshed_port, profile, timeout)
                if connected is not None:
                    return connected
            except (OSError, StarBridgeError) as error:
                last_error = error
            time.sleep(0.4)
        raise FirmwareInstallError(
            f"firmware was uploaded but {profile.display_name} did not reconnect: {last_error}"
        )

    @classmethod
    def _connect_if_compatible(cls, port: str, profile: BoardProfile,
                               timeout: float) -> "Board | None":
        for attempt in range(2):
            candidate: Board | None = None
            try:
                candidate = cls.connect(port, profile.baudrate, timeout)
                info = candidate.info()
                firmware_version = (
                    info.firmware_major,
                    info.firmware_minor,
                    info.firmware_patch,
                )
                if (info.board_id == profile.board_id and
                        firmware_version >= profile.minimum_firmware_version):
                    return candidate
            except (OSError, StarBridgeError):
                pass
            if candidate is not None:
                candidate.close()
            if attempt == 0:
                time.sleep(0.25)
        return None

    @classmethod
    def from_transport(cls, transport: Transport, timeout: float = 1.0) -> "Board":
        return cls(ProtocolClient(transport, timeout))

    def __enter__(self) -> "Board":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def ping(self, data: bytes = b"starbridge") -> bytes:
        return self._client.request(Command.PING, data)

    def info(self) -> BoardInfo:
        data = self._client.request(Command.GET_INFO)
        if len(data) != 9:
            raise ProtocolError(f"GET_INFO returned {len(data)} bytes, expected 9")
        protocol, major, minor, patch, board_id, capabilities = struct.unpack("<BBBBBI", data)
        return BoardInfo(protocol, major, minor, patch, board_id, capabilities)

    def reset_state(self) -> None:
        self._client.request(Command.RESET_STATE)

    def pin_mode(self, pin: Pin | int, mode: PinMode) -> None:
        self._client.request(Command.PIN_MODE, bytes((int(pin), int(mode))))

    def digital_write(self, pin: Pin | int, value: bool) -> None:
        self._client.request(Command.DIGITAL_WRITE, bytes((int(pin), int(bool(value)))))

    def digital_read(self, pin: Pin | int) -> bool:
        data = self._client.request(Command.DIGITAL_READ, bytes((int(pin),)))
        if len(data) != 1:
            raise ProtocolError("DIGITAL_READ returned an invalid payload")
        return bool(data[0])

    def analog_read(self, pin: Pin | int, *, millivolts: bool = False) -> int:
        data = self._client.request(Command.ANALOG_READ, bytes((int(pin), int(millivolts))))
        if len(data) != 4:
            raise ProtocolError("ANALOG_READ returned an invalid payload")
        return struct.unpack("<I", data)[0]

    def analog_write(self, pin: Pin | int, value: int) -> None:
        if not 0 <= value <= 255:
            raise ValueError("DAC value must be between 0 and 255")
        self._client.request(Command.ANALOG_WRITE, bytes((int(pin), value)))

    def pwm_configure(self, pin: Pin | int, frequency: int, resolution: int = 8) -> None:
        if not 1 <= frequency <= 40_000_000:
            raise ValueError("frequency must be between 1 and 40,000,000 Hz")
        if not 1 <= resolution <= 20:
            raise ValueError("resolution must be between 1 and 20 bits")
        self._client.request(Command.PWM_CONFIGURE, struct.pack("<BIB", int(pin), frequency, resolution))

    def pwm_write(self, pin: Pin | int, duty: int) -> None:
        if duty < 0:
            raise ValueError("duty must not be negative")
        self._client.request(Command.PWM_WRITE, struct.pack("<BI", int(pin), duty))

    def pwm_stop(self, pin: Pin | int, idle_high: bool = False) -> None:
        self._client.request(Command.PWM_STOP, bytes((int(pin), int(idle_high))))

    def oled(self) -> OLED:
        return OLED(self._client)

    def dht11(self, pin: Pin | int) -> DHT11:
        return DHT11(self._client, pin)

    def neopixel(self, pin: Pin | int, count: int, brightness: int = 255) -> NeoPixel:
        return NeoPixel(self._client, pin, count, brightness)

    def ultrasonic(self, trigger_pin: Pin | int, echo_pin: Pin | int,
                   timeout_us: int = 30_000) -> Ultrasonic:
        return Ultrasonic(self._client, trigger_pin, echo_pin, timeout_us)

    def mp3(self, rx_pin: Pin | int, tx_pin: Pin | int,
            busy_pin: Pin | int | None = None) -> MP3:
        return MP3(self._client, rx_pin, tx_pin, busy_pin)

    def pn532(
        self,
        *,
        irq_pin: Pin | int | None = None,
        reset_pin: Pin | int | None = None,
    ) -> PN532:
        return PN532(self._client, irq_pin, reset_pin)

    def nfc(
        self,
        *,
        irq_pin: Pin | int | None = None,
        reset_pin: Pin | int | None = None,
    ) -> PN532:
        """Alias for :meth:`pn532`."""
        return self.pn532(irq_pin=irq_pin, reset_pin=reset_pin)

    def software_serial(self, rx_pin: Pin | int, tx_pin: Pin | int,
                        baudrate: int = 9600) -> SoftwareSerial:
        return SoftwareSerial(self._client, rx_pin, tx_pin, baudrate)

    def wifi(self) -> WiFi:
        return WiFi(self._client)

    def espnow(self, channel: int = 0) -> ESPNow:
        return ESPNow(self._client, channel)

    def network_time(self) -> NetworkTime:
        return NetworkTime(self._client)

    def close(self) -> None:
        self._client.close()
