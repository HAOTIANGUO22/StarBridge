import hashlib
import json
from pathlib import Path
import unittest

import starbridge


class DistributionTests(unittest.TestCase):
    def test_bundled_firmware_matches_integrity_manifests(self):
        offline = Path(starbridge.__file__).parent / "_offline"
        for board in ("starcore-v2", "stardust"):
            with self.subTest(board=board):
                bundle = offline / "firmware" / board
                manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["sdk_version"], starbridge.__version__)
                self.assertEqual(manifest["board"], board)
                images = manifest.get("images") or [manifest["image"]]
                for image in images:
                    digest = hashlib.sha256((bundle / image["file"]).read_bytes()).hexdigest()
                    self.assertEqual(digest, image["sha256"])

    def test_bundled_windows_flash_tools_and_licenses_are_present(self):
        runtime = Path(starbridge.__file__).parent / "_offline" / "windows-x86_64"
        for filename in ("esptool.exe", "avrdude.exe", "avrdude.conf",
                         "ESPTOOL_LICENSE.txt", "AVRDUDE_LICENSE.txt"):
            with self.subTest(file=filename):
                self.assertGreater((runtime / filename).stat().st_size, 0)
