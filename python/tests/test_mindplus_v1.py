from __future__ import annotations

import json
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ROOT = ROOT / "mindplus"


class MindPlusV1ExtensionTests(unittest.TestCase):
    def test_manifest_targets_python_mode_with_bundled_compatibility_layer(self) -> None:
        config = json.loads((EXTENSION_ROOT / "config.json").read_text(encoding="utf-8"))

        self.assertEqual(config["id"], "starbridge")
        self.assertFalse(config["isBoard"])
        self.assertEqual(config["platform"], ["win"])
        self.assertEqual(config["asset"]["python"]["dir"], "python/")
        self.assertEqual(config["asset"]["python"]["dependencies"], {})
        self.assertEqual(
            set(config["asset"]["python"]["files"]),
            {
                "_images/featured.png",
                "_images/icon.svg",
                "_locales/zh-cn.json",
                "_locales/en.json",
                "_menus/index.json",
                "libraries/starbridge_mindplus.py",
                "libraries/starbridge_offline/firmware/starcore-v2/boot_app0.bin",
                "libraries/starbridge_offline/firmware/starcore-v2/bootloader.bin",
                "libraries/starbridge_offline/firmware/starcore-v2/firmware.bin",
                "libraries/starbridge_offline/firmware/starcore-v2/manifest.json",
                "libraries/starbridge_offline/firmware/starcore-v2/partitions.bin",
                "libraries/starbridge_offline/windows-x86_64/ESPTOOL_LICENSE.txt",
                "libraries/starbridge_offline/windows-x86_64/esptool.exe",
            },
        )

    def test_all_referenced_menus_exist(self) -> None:
        main_ts = (EXTENSION_ROOT / "python" / "main.ts").read_text(encoding="utf-8")
        menus = json.loads(
            (EXTENSION_ROOT / "python" / "_menus" / "index.json").read_text(
                encoding="utf-8"
            )
        )

        referenced = set(re.findall(r'\.options="([A-Z_]+)"', main_ts))
        self.assertTrue(referenced)
        self.assertEqual(referenced - menus.keys(), set())

    def test_reporters_generate_expressions(self) -> None:
        main_ts = (EXTENSION_ROOT / "python" / "main.ts").read_text(encoding="utf-8")

        self.assertIn(
            "Generator.addCode([`board.digital_read(${pin})`, Generator.ORDER_UNARY_POSTFIX])",
            main_ts,
        )
        self.assertIn("board.dht11(${pin}).read().temperature_c", main_ts)
        self.assertIn("board.ultrasonic(${trigger}, ${echo}).read_cm()", main_ts)

    def test_bundled_client_matches_protocol_golden_vector(self) -> None:
        import importlib.util

        module_path = (
            EXTENSION_ROOT / "python" / "libraries" / "starbridge_mindplus.py"
        )
        spec = importlib.util.spec_from_file_location("starbridge_mindplus", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        frame = module._encode_frame(1, 0x1234, module.Command.PING, b"abc")
        self.assertEqual(frame.hex(), "a55a020134120103006162631dfc")
        self.assertEqual(module.crc16_ccitt(b"123456789"), 0x29B1)

    def test_mindplus_bundle_contains_offline_flasher(self) -> None:
        offline = EXTENSION_ROOT / "python" / "libraries" / "starbridge_offline"
        manifest = json.loads(
            (offline / "firmware" / "starcore-v2" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(manifest["sdk_version"], "4.3.0")
        self.assertEqual(manifest["firmware_version"], "4.0.0")
        self.assertTrue((offline / "windows-x86_64" / "esptool.exe").is_file())

    def test_dht11_retries_status_5_and_caches_reading(self) -> None:
        import importlib.util
        from unittest import mock

        module_path = (
            EXTENSION_ROOT / "python" / "libraries" / "starbridge_mindplus.py"
        )
        spec = importlib.util.spec_from_file_location("starbridge_mindplus_dht", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FakeClient:
            def __init__(self) -> None:
                self.calls = 0

            def request(self, command, payload=b"") -> bytes:
                self.calls += 1
                if self.calls == 1:
                    raise module.BoardCommandError(command, 5)
                return struct.pack("<hH", 260, 615)

        module._DHT_CACHE.clear()
        client = FakeClient()
        sensor = module.DHT11(client, module.Pin.P1)
        with mock.patch.object(module.time, "sleep") as sleep:
            first = sensor.read()
            second = sensor.read()

        self.assertEqual(first.temperature_c, 26.0)
        self.assertEqual(first.humidity_percent, 61.5)
        self.assertIs(first, second)
        self.assertEqual(client.calls, 2)
        sleep.assert_called_once_with(1.1)

    def test_feature_image_has_mindplus_dimensions(self) -> None:
        data = (EXTENSION_ROOT / "python" / "_images" / "featured.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (600, 374))


if __name__ == "__main__":
    unittest.main()
