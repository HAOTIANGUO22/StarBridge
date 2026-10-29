import json
import unittest
from dataclasses import FrozenInstanceError

from starbridge import BoardInfo, BoardType
from starbridge.boards import get_board_profile


class CompatibilityTests(unittest.TestCase):
    def test_board_type_keeps_string_behavior(self):
        for board_type in BoardType:
            with self.subTest(board=board_type.value):
                self.assertEqual(str(board_type), board_type.value)
                self.assertEqual("{}".format(board_type), board_type.value)
                self.assertEqual(json.loads(json.dumps(board_type)), board_type.value)
                self.assertEqual(BoardType(board_type.value), board_type)
                self.assertEqual(get_board_profile(board_type.value).type, board_type)

    def test_board_info_remains_immutable(self):
        info = BoardInfo(2, 4, 2, 0, 1, 0)
        self.assertEqual(info, BoardInfo(2, 4, 2, 0, 1, 0))
        with self.assertRaises(FrozenInstanceError):
            info.board_id = 3
