import hashlib
import io
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from starbridge import Board, BoardType
from starbridge.boards import get_board_profile
from starbridge.errors import (
    BoardNotFoundError,
    FirmwareInstallError,
    UnsupportedBoardError,
)
from starbridge.programmer import FirmwareProgrammer, discover_port


class ProgrammerTests(unittest.TestCase):
    def test_profiles_distinguish_board_architectures(self) -> None:
        starcore = get_board_profile(BoardType.STARCORE_V2)
        uno = get_board_profile(BoardType.ARDUINO_UNO)
        self.assertEqual(starcore.fqbn, "starbridge:esp32:starcore_v2")
        self.assertEqual(starcore.architecture, "esp32")
        self.assertTrue(starcore.has_firmware)
        self.assertEqual(uno.fqbn, "arduino:avr:uno")
        self.assertFalse(uno.has_firmware)

    @patch("starbridge.programmer.list_ports.comports")
    def test_port_discovery_uses_usb_identity(self, comports) -> None:
        comports.return_value = [
            SimpleNamespace(device="COM3", vid=0x2341, pid=0x0043,
                            description="Arduino Uno", manufacturer="Arduino"),
            SimpleNamespace(device="COM7", vid=0x10C4, pid=0xEA60,
                            description="CP210x", manufacturer="Silicon Labs"),
        ]
        self.assertEqual(discover_port(get_board_profile("starcore-v2")), "COM7")
        self.assertEqual(discover_port(get_board_profile("arduino-uno")), "COM3")

    @patch("starbridge.programmer.list_ports.comports")
    def test_starcore_discovery_supports_ch9102(self, comports) -> None:
        comports.return_value = [
            SimpleNamespace(
                device="COM4",
                vid=0x1A86,
                pid=0x55D4,
                description="USB-Enhanced-SERIAL CH9102",
                manufacturer="wch.cn",
            ),
            SimpleNamespace(
                device="COM5",
                vid=0x2BDF,
                pid=0x0289,
                description="USB Serial Device",
                manufacturer="Microsoft",
            ),
        ]
        self.assertEqual(discover_port(get_board_profile("starcore-v2")), "COM4")

    @patch("starbridge.programmer.list_ports.comports")
    def test_ambiguous_ports_require_explicit_selection(self, comports) -> None:
        comports.return_value = [
            SimpleNamespace(device="COM7", vid=0x10C4, pid=0xEA60,
                            description="CP210x", manufacturer="Silicon Labs"),
            SimpleNamespace(device="COM8", vid=0x10C4, pid=0xEA60,
                            description="CP210x", manufacturer="Silicon Labs"),
        ]
        with self.assertRaises(BoardNotFoundError):
            discover_port(get_board_profile("starcore-v2"))

    @patch("starbridge.programmer.list_ports.comports")
    def test_unknown_single_port_is_not_flashed_by_guess(self, comports) -> None:
        comports.return_value = [
            SimpleNamespace(device="COM9", vid=0xFFFF, pid=0xFFFF,
                            description="Unknown device", manufacturer="Unknown"),
        ]
        with self.assertRaises(BoardNotFoundError):
            discover_port(get_board_profile("starcore-v2"))

    def test_flash_command_uses_target_specific_libraries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "firmware" / "arduino-board-package").mkdir(parents=True)
            (root / "firmware" / "starcore-v2").mkdir()
            (root / "firmware" / "shared-libraries").mkdir()
            (root / "firmware" / "platforms" / "esp32" / "libraries").mkdir(parents=True)
            cli = root / "arduino-cli.exe"
            cli.touch()
            programmer = FirmwareProgrammer(root, cli)
            programmer._run = Mock()
            programmer.flash(get_board_profile("starcore-v2"), "COM7")
            compile_call = programmer._run.call_args_list[-1].args[0]
            self.assertIn("--upload", compile_call)
            self.assertIn("COM7", compile_call)
            resolved = programmer.firmware_root
            self.assertIn(str(resolved / "shared-libraries"), compile_call)
            self.assertIn(str(resolved / "platforms" / "esp32" / "libraries"),
                          compile_call)

    def test_direct_packaged_firmware_directory_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            firmware = Path(directory) / "starbridge" / "_firmware"
            (firmware / "arduino-board-package").mkdir(parents=True)
            cli = Path(directory) / "arduino-cli.exe"
            cli.touch()
            programmer = FirmwareProgrammer(firmware, cli)
            self.assertEqual(programmer.firmware_root, firmware.resolve())

    @patch("starbridge.programmer.os.name", "nt")
    def test_project_local_arduino_cli_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "firmware" / "arduino-board-package").mkdir(parents=True)
            cli = root / "tools" / "arduino-cli" / "arduino-cli.exe"
            cli.parent.mkdir(parents=True)
            cli.touch()

            programmer = FirmwareProgrammer(root)

            self.assertEqual(programmer.arduino_cli, cli.resolve())

    @patch("starbridge.programmer.os.name", "nt")
    def test_bundled_firmware_flashes_without_arduino_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            offline = root / "offline"
            bundle = offline / "firmware" / "starcore-v2"
            runtime = offline / "windows-x86_64"
            bundle.mkdir(parents=True)
            runtime.mkdir(parents=True)
            (runtime / "esptool.exe").touch()
            images = [
                ("0x1000", "bootloader.bin"),
                ("0x8000", "partitions.bin"),
                ("0xe000", "boot_app0.bin"),
                ("0x10000", "firmware.bin"),
            ]
            for _, filename in images:
                (bundle / filename).touch()
            (bundle / "manifest.json").write_text(json.dumps({
                "format": 1,
                "board": "starcore-v2",
                "chip": "esp32",
                "baud": 921600,
                "images": [
                    {
                        "offset": offset,
                        "file": filename,
                        "sha256": hashlib.sha256(b"").hexdigest(),
                    }
                    for offset, filename in images
                ],
            }), encoding="utf-8")

            with patch.object(FirmwareProgrammer, "_offline_root", return_value=offline):
                programmer = FirmwareProgrammer(root)
                programmer._run_flash_process = Mock()
                programmer.flash(get_board_profile("starcore-v2"), "COM7")

            command, profile, port, firmware_version = programmer._run_flash_process.call_args.args
            self.assertEqual(command[0], str(runtime / "esptool.exe"))
            self.assertIn("COM7", command)
            self.assertIn("0x10000", command)
            self.assertEqual(profile.type, BoardType.STARCORE_V2)
            self.assertEqual(port, "COM7")
            self.assertEqual(firmware_version, "4.x")

    @patch("starbridge.programmer.subprocess.Popen")
    def test_flash_progress_displays_brand_version_and_completion(self, popen) -> None:
        process = Mock()
        process.stdout = io.StringIO(
            "Connecting...\rWriting at 0x1000 [...] 50.0% 50/100 bytes\r"
            "Writing at 0x1000 [...] 100.0% 100/100 bytes\r"
        )
        process.wait.return_value = 0
        popen.return_value = process
        output = io.StringIO()

        with patch("starbridge.programmer.sys.stdout", output):
            FirmwareProgrammer._run_flash_process(
                ("esptool.exe", "--chip", "esp32", "--port", "COM4"),
                get_board_profile("starcore-v2"),
                "COM4",
                "4.0.0",
            )

        text = output.getvalue()
        self.assertIn("StarBridge 4.4.0", text)
        self.assertIn("固件 4.0.0", text)
        self.assertIn("100%", text)
        self.assertIn("烧录完成", text)

    @patch("starbridge.programmer.shutil.which", return_value=None)
    @patch.dict("starbridge.programmer.os.environ", {}, clear=True)
    def test_missing_cli_and_offline_bundle_reports_install_error(self, which) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(
                FirmwareProgrammer,
                "_offline_root",
                return_value=root / "missing-offline-runtime",
            ):
                programmer = FirmwareProgrammer(root)
                self.assertIsNone(programmer.firmware_root)
                with self.assertRaises(FirmwareInstallError):
                    programmer.flash(get_board_profile("starcore-v2"), "COM7")

    @patch("starbridge.board.discover_port", return_value="COM7")
    @patch("starbridge.board.Board._connect_if_compatible")
    @patch("starbridge.board.FirmwareProgrammer")
    def test_begin_reuses_compatible_firmware(self, programmer, compatible, discover) -> None:
        expected = object()
        compatible.return_value = expected
        result = Board.begin(BoardType.STARCORE_V2)
        self.assertIs(result, expected)
        programmer.assert_not_called()
        discover.assert_called_once()

    @patch("starbridge.board.discover_port", return_value="COM3")
    @patch("starbridge.board.Board._connect_if_compatible", return_value=None)
    def test_uno_does_not_receive_esp32_firmware(self, compatible, discover) -> None:
        with self.assertRaises(UnsupportedBoardError):
            Board.begin(BoardType.ARDUINO_UNO)


if __name__ == "__main__":
    unittest.main()
