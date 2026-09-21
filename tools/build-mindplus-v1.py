from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
EXTENSION_ROOT = ROOT / "mindplus"
DIST_DIR = ROOT / "artifacts" / "dist"


def validate_extension() -> dict[str, object]:
    config_path = EXTENSION_ROOT / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["id"] == "starbridge"
    assert config["isBoard"] is False
    assert config["platform"] == ["win"]
    python_asset = config["asset"]["python"]
    assert python_asset["dir"] == "python/"
    assert python_asset["main"] == "main.ts"
    assert python_asset["dependencies"] == {}
    declared_files = set(python_asset["files"])
    expected_files = {
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
    }
    assert declared_files == expected_files, "asset.python.files is incomplete"
    for relative in declared_files:
        assert (EXTENSION_ROOT / "python" / relative).is_file(), (
            "declared Python asset is missing: {0}".format(relative)
        )

    required = (
        "LICENSE.TXT",
        "README.md",
        "python/main.ts",
        "python/libraries/starbridge_mindplus.py",
        "python/_images/icon.svg",
        "python/_images/featured.png",
        "python/_locales/zh-cn.json",
        "python/_locales/en.json",
        "python/_menus/index.json",
    )
    for relative in required:
        assert (EXTENSION_ROOT / relative).is_file(), f"missing {relative}"

    main_ts = (EXTENSION_ROOT / "python" / "main.ts").read_text(encoding="utf-8")
    menus = json.loads(
        (EXTENSION_ROOT / "python" / "_menus" / "index.json").read_text(encoding="utf-8")
    )
    locale_zh = json.loads(
        (EXTENSION_ROOT / "python" / "_locales" / "zh-cn.json").read_text(encoding="utf-8")
    )
    locale_en = json.loads(
        (EXTENSION_ROOT / "python" / "_locales" / "en.json").read_text(encoding="utf-8")
    )

    referenced_menus = set(re.findall(r'\.options="([A-Z_]+)"', main_ts))
    assert referenced_menus <= menus.keys(), (
        f"undefined menus: {sorted(referenced_menus - menus.keys())}"
    )
    for name, definition in menus.items():
        entries = definition.get("menu")
        assert entries and all(len(entry) == 2 for entry in entries), f"invalid menu {name}"

    block_functions = set(
        re.findall(
            r'//% block="[^\n]+" blockType="(?:command|reporter|boolean|hat)"\s+'
            r'(?:[^\n]*\n)*?\s*export function ([A-Za-z0-9_]+)',
            main_ts,
        )
    )
    expected_locale_keys = {f"starbridge.{name}|block" for name in block_functions}
    assert expected_locale_keys <= locale_zh.keys(), "Chinese block translations are incomplete"
    assert expected_locale_keys <= locale_en.keys(), "English block translations are incomplete"

    expected_snippets = (
        "Board.begin(BoardType.STARCORE_V2)",
        "board.digital_write",
        "board.digital_read",
        "board.analog_read",
        "board.analog_write",
        "board.pwm_configure",
        "board.dht11",
        "board.ultrasonic",
        "board.close",
    )
    for snippet in expected_snippets:
        assert snippet in main_ts, f"missing generated API call: {snippet}"
    assert "from starbridge_mindplus import" in main_ts

    offline_manifest = json.loads(
        (
            EXTENSION_ROOT
            / "python"
            / "libraries"
            / "starbridge_offline"
            / "firmware"
            / "starcore-v2"
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert offline_manifest["sdk_version"] == "4.3.0"
    assert offline_manifest["firmware_version"] == "4.0.0"

    png = (EXTENSION_ROOT / "python" / "_images" / "featured.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n", "featured.png is not a PNG"
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (600, 374), "featured.png must be 600x374"

    return config


def build_package(config: dict[str, object]) -> Path:
    version = str(config["version"])
    output = DIST_DIR / f"starbridge-starbridge-thirdex-V{version}.mpext"
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(
        path for path in EXTENSION_ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(EXTENSION_ROOT).as_posix()
            info = ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and package the Mind+ V1 extension")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    config = validate_extension()
    print(f"Mind+ V1 extension {config['version']} validation passed")
    if not args.validate_only:
        output = build_package(config)
        print(output)


if __name__ == "__main__":
    main()
