from __future__ import annotations

from collections.abc import Sequence
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from ._vendor.serial.tools import list_ports

from .boards import BoardProfile
from .errors import BoardNotFoundError, FirmwareInstallError, UnsupportedBoardError
from ._version import __version__


def discover_port(profile: BoardProfile, requested_port: str | None = None) -> str:
    ports = list(list_ports.comports())
    if requested_port is not None:
        requested = requested_port.casefold()
        for port in ports:
            if port.device.casefold() == requested:
                return port.device
        raise BoardNotFoundError(
            f"串口 {requested_port!r} 不存在。请重新插拔开发板，"
            "并在 Windows 设备管理器中确认实际 COM 口。"
        )

    matches = []
    for port in ports:
        identity = (port.vid, port.pid)
        description = f"{port.description} {port.manufacturer}".casefold()
        if identity in profile.vid_pid or any(hint in description for hint in profile.description_hints):
            matches.append(port.device)

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise BoardNotFoundError(
            f"找到多个 {profile.display_name} 串口：{', '.join(matches)}。"
            f"请使用 Board.begin(..., port={matches[0]!r}) 明确指定。"
        )
    available = ", ".join(
        f"{port.device} ({port.description or '未知设备'})" for port in ports
    ) or "无"
    raise BoardNotFoundError(
        f"无法自动识别 {profile.display_name}。当前串口：{available}。"
        "请确认 USB 数据线和驱动；如果已知道端口，"
        "可使用 Board.begin(..., port='COMx') 指定。"
    )


class _FlashProgress:
    _PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%")

    def __init__(self, profile: BoardProfile, port: str, firmware_version: str) -> None:
        self.profile = profile
        self.port = port
        self.firmware_version = firmware_version
        self.segment = 0
        self.last_raw = 0.0
        self.last_overall = -1

    def start(self) -> None:
        print()
        print(f"StarBridge {__version__}")
        print(f"{self.profile.display_name} | 固件 {self.firmware_version} | {self.port}")
        print("正在烧录，请不要拔出 USB 数据线…")
        self.update(0)

    def consume(self, line: str) -> None:
        match = self._PERCENT.search(line)
        if match is None:
            if "Connecting" in line:
                self.update(5)
            elif "Erasing" in line:
                self.update(8)
            return
        raw = min(100.0, float(match.group(1)))
        if raw + 10 < self.last_raw and self.segment < 3:
            self.segment += 1
        elif raw >= 99 and self.last_raw >= 99 and self.segment < 3:
            self.segment += 1
        self.last_raw = raw
        overall = 10 + int(((self.segment + raw / 100.0) / 4.0) * 85)
        self.update(min(overall, 95))

    def update(self, percent: int) -> None:
        percent = max(self.last_overall, percent)
        if percent == self.last_overall:
            return
        self.last_overall = percent
        width = 30
        filled = round(width * percent / 100)
        bar = "#" * filled + "-" * (width - filled)
        sys.stdout.write(f"\r[{bar}] {percent:3d}%")
        sys.stdout.flush()

    def finish(self) -> None:
        self.update(100)
        print("\n烧录完成，正在等待开发板重启…")

    @staticmethod
    def fail() -> None:
        print("\n烧录失败。")


class FirmwareProgrammer:
    def __init__(self, project_root: str | Path | None = None,
                 arduino_cli: str | Path | None = None) -> None:
        self._explicit_arduino_cli = arduino_cli is not None
        self.firmware_root = self._find_firmware_root(project_root)
        self.project_root = (
            self.firmware_root.parent
            if self.firmware_root is not None and self.firmware_root.name == "firmware"
            else self.firmware_root or Path(__file__).resolve().parent
        )
        self.arduino_cli = self._find_arduino_cli(arduino_cli, self.project_root)

    @staticmethod
    def _find_firmware_root(explicit: str | Path | None) -> Path | None:
        candidates: list[Path] = []
        if explicit is not None:
            supplied = Path(explicit)
            candidates.extend((supplied / "firmware", supplied))
        elif os.environ.get("STARBRIDGE_HOME"):
            supplied = Path(os.environ["STARBRIDGE_HOME"])
            candidates.extend((supplied / "firmware", supplied))
        else:
            package_root = Path(__file__).resolve().parent
            candidates.append(package_root / "_firmware")
            candidates.extend(parent / "firmware" for parent in package_root.parents)
        for candidate in candidates:
            if (candidate / "arduino-board-package").is_dir():
                return candidate.resolve()
        return None

    @staticmethod
    def _cache_root() -> Path:
        if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
            return Path(os.environ["LOCALAPPDATA"]) / "StarBridge" / "cache"
        return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "starbridge"

    @staticmethod
    def _find_arduino_cli(
        explicit: str | Path | None,
        project_root: Path,
    ) -> Path | None:
        candidates = [
            str(explicit) if explicit is not None else None,
            os.environ.get("STARBRIDGE_ARDUINO_CLI"),
            str(project_root / "tools" / "arduino-cli" / "arduino-cli.exe")
            if os.name == "nt" else None,
            shutil.which("arduino-cli"),
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return Path(candidate).resolve()
        return None

    @staticmethod
    def _offline_root() -> Path:
        return Path(__file__).resolve().parent / "_offline"

    def _find_offline_bundle(self, profile: BoardProfile) -> Path | None:
        if os.name != "nt" or self._explicit_arduino_cli:
            return None
        bundle = self._offline_root() / "firmware" / profile.type.value
        if (bundle / "manifest.json").is_file():
            return bundle
        return None

    def flash(self, profile: BoardProfile, port: str) -> None:
        if not profile.has_firmware:
            raise UnsupportedBoardError(
                f"{profile.display_name} is registered, but its StarBridge firmware is not implemented yet"
            )
        offline_bundle = self._find_offline_bundle(profile)
        if offline_bundle is not None:
            self._flash_precompiled(profile, port, offline_bundle)
            return
        if self.arduino_cli is None:
            raise FirmwareInstallError(
                "neither bundled offline firmware nor arduino-cli was found; "
                "reinstall the official StarBridge wheel or set STARBRIDGE_ARDUINO_CLI"
            )
        if self.firmware_root is None:
            raise FirmwareInstallError(
                "firmware source was not found; reinstall the official wheel to use its "
                "bundled binary firmware or run from the complete source repository"
            )
        firmware_root = self.firmware_root
        sketch = firmware_root / profile.firmware_directory
        board_libraries = sketch / "libraries"
        shared_libraries = firmware_root / "shared-libraries"
        board_package = firmware_root / "arduino-board-package"
        artifacts = self._cache_root() / "auto-flash"
        config = artifacts / "arduino-cli.yaml"
        build_path = artifacts / profile.type.value
        artifacts.mkdir(parents=True, exist_ok=True)

        if not config.exists():
            self._run(("config", "init", "--dest-file", str(config)))
        self._run(("config", "set", "directories.user", str(board_package),
                   "--config-file", str(config)))
        self._run((
            "compile", "--upload", "--port", port,
            "--config-file", str(config),
            "--fqbn", profile.fqbn,
            "--warnings", "all",
            "--libraries", str(board_libraries),
            "--libraries", str(shared_libraries),
            "--build-path", str(build_path),
            str(sketch),
        ))

    def _flash_precompiled(
        self,
        profile: BoardProfile,
        port: str,
        bundle: Path,
    ) -> None:
        try:
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise FirmwareInstallError(f"invalid bundled firmware manifest: {error}") from error
        if manifest.get("format") != 1 or manifest.get("board") != profile.type.value:
            raise FirmwareInstallError("bundled firmware manifest does not match the selected board")

        if profile.architecture == "avr":
            self._flash_precompiled_avr(profile, port, bundle, manifest)
            return
        if profile.architecture != "esp32":
            raise FirmwareInstallError(
                f"unsupported bundled firmware architecture: {profile.architecture}"
            )

        esptool = self._offline_root() / "windows-x86_64" / "esptool.exe"
        if not esptool.is_file():
            raise FirmwareInstallError("the bundled Windows esptool executable is missing")

        declared_images = manifest.get("images", [])
        if not isinstance(declared_images, list) or len(declared_images) != 4:
            raise FirmwareInstallError("bundled firmware manifest must contain four images")
        images: list[str] = []
        for image in declared_images:
            filename = image.get("file")
            offset = image.get("offset")
            path = bundle / filename if isinstance(filename, str) else bundle / ""
            if not isinstance(offset, str) or not path.is_file():
                raise FirmwareInstallError("a bundled firmware image is missing or invalid")
            expected_hash = image.get("sha256")
            if not isinstance(expected_hash, str):
                raise FirmwareInstallError("a bundled firmware checksum is missing")
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_hash != expected_hash.casefold():
                raise FirmwareInstallError(f"bundled firmware checksum failed for {filename}")
            images.extend((offset, str(path)))

        command = (
            str(esptool),
            "--chip", str(manifest.get("chip", "esp32")),
            "--port", port,
            "--baud", str(manifest.get("baud", 921600)),
            "--before", "default-reset",
            "--after", "hard-reset",
            "write-flash", "-z",
            "--flash-mode", "keep",
            "--flash-freq", "keep",
            "--flash-size", "keep",
            *images,
        )
        self._run_flash_process(
            command,
            profile,
            port,
            str(manifest.get("firmware_version", "4.x")),
        )

    def _flash_precompiled_avr(
        self,
        profile: BoardProfile,
        port: str,
        bundle: Path,
        manifest: dict[str, object],
    ) -> None:
        runtime = self._offline_root() / "windows-x86_64"
        avrdude = runtime / "avrdude.exe"
        config = runtime / "avrdude.conf"
        if not avrdude.is_file() or not config.is_file():
            raise FirmwareInstallError("the bundled Windows avrdude runtime is missing")

        image = manifest.get("image")
        if not isinstance(image, dict):
            raise FirmwareInstallError("bundled AVR firmware image is missing")
        filename = image.get("file")
        expected_hash = image.get("sha256")
        path = bundle / filename if isinstance(filename, str) else bundle / ""
        if not path.is_file() or not isinstance(expected_hash, str):
            raise FirmwareInstallError("bundled AVR firmware image is invalid")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != expected_hash.casefold():
            raise FirmwareInstallError(f"bundled firmware checksum failed for {filename}")

        command = (
            str(avrdude),
            "-C", str(config),
            "-p", str(manifest.get("mcu", "atmega328p")),
            "-c", str(manifest.get("programmer", "arduino")),
            "-P", port,
            "-b", str(manifest.get("baud", 115200)),
            "-D",
            "-U", f"flash:w:{path}:i",
        )
        self._run_flash_process(
            command,
            profile,
            port,
            str(manifest.get("firmware_version", "4.x")),
        )

    @staticmethod
    def _run_flash_process(
        command: Sequence[str],
        profile: BoardProfile,
        port: str,
        firmware_version: str,
    ) -> None:
        progress = _FlashProgress(profile, port, firmware_version)
        progress.start()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        captured: list[str] = []
        current: list[str] = []
        while True:
            character = process.stdout.read(1)
            if character == "":
                break
            if character in "\r\n":
                if current:
                    line = "".join(current)
                    captured.append(line)
                    captured = captured[-20:]
                    progress.consume(line)
                    current.clear()
            elif len(current) < 4096:
                current.append(character)
        if current:
            line = "".join(current)
            captured.append(line)
            progress.consume(line)
        returncode = process.wait()
        if returncode != 0:
            progress.fail()
            details = "\n".join(captured[-8:]).strip() or "烧录器未返回详细信息"
            raise FirmwareInstallError(
                f"固件烧录失败。请检查 USB 连接和串口占用，"
                f"重新插拔开发板后重试。\n烧录器输出：{details}"
            )
        progress.finish()

    def _run(self, arguments: Sequence[str]) -> None:
        if self.arduino_cli is None:
            raise FirmwareInstallError("arduino-cli is not available")
        command = (str(self.arduino_cli), *arguments)
        self._run_process(command, "arduino-cli")

    @staticmethod
    def _run_process(command: Sequence[str], tool_name: str) -> None:
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            raise FirmwareInstallError(
                f"{tool_name} failed ({result.returncode}): {details}"
            )
