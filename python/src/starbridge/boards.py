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
        description_hints=("cp210", "silicon labs", "ch910", "wch.cn", "starcore"),
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
