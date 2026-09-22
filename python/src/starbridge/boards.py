from __future__ import annotations

from dataclasses import dataclass

from .constants import BoardType


@dataclass(frozen=True, slots=True)
class BoardProfile:
    type: BoardType
    display_name: str
    board_id: int
    fqbn: str
    firmware_directory: str | None
    architecture: str
    vid_pid: frozenset[tuple[int, int]]
    description_hints: tuple[str, ...]
    baudrate: int = 115200
    minimum_firmware_major: int = 4
    minimum_firmware_minor: int = 0
    minimum_firmware_patch: int = 0

    @property
    def minimum_firmware_version(self) -> tuple[int, int, int]:
        return (
            self.minimum_firmware_major,
            self.minimum_firmware_minor,
            self.minimum_firmware_patch,
        )

    @property
    def has_firmware(self) -> bool:
        return self.firmware_directory is not None


BOARD_PROFILES: dict[BoardType, BoardProfile] = {
    BoardType.STARCORE_V2: BoardProfile(
        type=BoardType.STARCORE_V2,
        display_name="StarCore V2",
        board_id=1,
        fqbn="starbridge:esp32:starcore_v2",
        firmware_directory="starcore-v2",
        architecture="esp32",
        vid_pid=frozenset({
            (0x10C4, 0xEA60),  # Silicon Labs CP210x
            (0x1A86, 0x55D4),  # WCH CH9102
        }),
        description_hints=("cp210", "silicon labs", "ch910", "starcore"),
        minimum_firmware_minor=2,
    ),
    BoardType.STARDUST: BoardProfile(
        type=BoardType.STARDUST,
        display_name="StarDust (星尘板)",
        board_id=3,
        fqbn="starbridge:avr:stardust",
        firmware_directory="stardust",
        architecture="avr",
        vid_pid=frozenset({
            (0x1A86, 0x7523),  # WCH CH340/CH341
            (0x1A86, 0x5523),  # Older WCH CH340 identity
        }),
        description_hints=("ch340", "usb-serial ch34", "stardust"),
        minimum_firmware_minor=3,
        minimum_firmware_patch=1,
    ),
    BoardType.ARDUINO_UNO: BoardProfile(
        type=BoardType.ARDUINO_UNO,
        display_name="Arduino Uno",
        board_id=2,
        fqbn="arduino:avr:uno",
        firmware_directory=None,
        architecture="avr",
        vid_pid=frozenset({
            (0x2341, 0x0043), (0x2341, 0x0001),
            (0x2A03, 0x0043), (0x2A03, 0x0001),
        }),
        description_hints=("arduino uno",),
    ),
}


def get_board_profile(board: BoardType | str) -> BoardProfile:
    board_type = board if isinstance(board, BoardType) else BoardType(board.lower())
    return BOARD_PROFILES[board_type]
