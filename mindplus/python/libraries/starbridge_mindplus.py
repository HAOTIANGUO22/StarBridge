"""Python 3.5-compatible StarBridge Protocol V2 client for Mind+ V1.

This module intentionally implements only the public surface needed by the
Mind+ blocks. The full StarBridge SDK remains the source of truth for firmware
installation, offline flashing and advanced diagnostics.
"""

from __future__ import print_function

import struct
import threading
import time
import hashlib
import json
import os
import subprocess

import serial
from serial.tools import list_ports


PROTOCOL_VERSION = 2
MAX_PAYLOAD = 256
SOF = b"\xA5\x5A"
HEADER = struct.Struct("<BBHBH")
CRC = struct.Struct("<H")
MIN_FRAME_SIZE = len(SOF) + HEADER.size + CRC.size


class BoardType(object):
    STARCORE_V2 = "starcore-v2"


class PinMode(object):
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2
    INPUT_PULLDOWN = 3


class Pin(object):
    P0 = 33
    P1 = 32
    P2 = 35
    P3 = 34
    P4 = 39
    P5 = 0
    P6 = 16
    P7 = 17
    P8 = 26
    P9 = 25
    P10 = 36
    P11 = 2
    P13 = 18
    P14 = 19
    P15 = 21
    P16 = 5
    P19 = 22
    P20 = 23
    BUTTON_A = 0
    BUTTON_B = 2
    BUZZER = 16
    ONBOARD_PIXELS = 17
    I2C_SCL = 22
    I2C_SDA = 23


class Command(object):
    PING = 0x01
    GET_INFO = 0x02
    RESET_STATE = 0x03
    PIN_MODE = 0x10
    DIGITAL_WRITE = 0x11
    DIGITAL_READ = 0x12
    ANALOG_READ = 0x13
    ANALOG_WRITE = 0x14
    PWM_CONFIGURE = 0x20
    PWM_WRITE = 0x21
    PWM_STOP = 0x22
    DHT11_READ = 0x40
    ULTRASONIC_READ = 0x60


class StarBridgeError(Exception):
    pass


class BoardNotFoundError(StarBridgeError):
    pass


class FirmwareRequiredError(StarBridgeError):
    pass


class BoardCommandError(StarBridgeError):
    def __init__(self, command, status):
        self.command = command
        self.status = status
        if command == 0x40 and status == 5:
            message = (
                "DHT11 温湿度读取失败：传感器没有返回有效数据。"
                "请确认 DATA 接在支持双向输入输出的引脚上（不要使用 P2、P3、P4、P10），"
                "检查 VCC、GND 和上拉电阻，并确保连续读取间隔至少 1 秒。"
                "[命令 0x40，状态 5]"
            )
        elif command == 0x60 and status == 5:
            message = (
                "超声波测距失败：请确认 TRIG/ECHO 顺序、供电和共地；"
                "物体过近、超出量程或角度过斜时也可能没有回波。"
                "[命令 0x60，状态 5]"
            )
        else:
            message = "StarBridge command 0x{0:02X} failed with status {1}".format(
                command, status
            )
        StarBridgeError.__init__(self, message)


def crc16_ccitt(data, initial=0xFFFF):
    crc = initial
    for value in bytearray(data):
        crc ^= value << 8
        for unused in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def _encode_frame(kind, sequence, command, payload=b""):
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload exceeds 256 bytes")
    body = HEADER.pack(
        PROTOCOL_VERSION, kind, sequence, command, len(payload)
    ) + payload
    return SOF + body + CRC.pack(crc16_ccitt(body))


class _StreamDecoder(object):
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        self.buffer.extend(data)
        frames = []
        while True:
            start = self.buffer.find(SOF)
            if start < 0:
                if self.buffer[-1:] == SOF[:1]:
                    del self.buffer[:-1]
                else:
                    del self.buffer[:]
                break
            if start:
                del self.buffer[:start]
            if len(self.buffer) < MIN_FRAME_SIZE:
                break
            version, kind, sequence, command, length = HEADER.unpack_from(
                self.buffer, len(SOF)
            )
            if length > MAX_PAYLOAD:
                del self.buffer[0]
                continue
            frame_size = MIN_FRAME_SIZE + length
            if len(self.buffer) < frame_size:
                break
            body_end = len(SOF) + HEADER.size + length
            body = bytes(self.buffer[len(SOF):body_end])
            expected_crc = CRC.unpack_from(self.buffer, body_end)[0]
            if crc16_ccitt(body) != expected_crc:
                del self.buffer[0]
                continue
            payload = body[HEADER.size:]
            frames.append((version, kind, sequence, command, payload))
            del self.buffer[:frame_size]
        return frames


def _discover_port(explicit_port=None):
    if explicit_port:
        return explicit_port
    candidates = []
    for port in list_ports.comports():
        vid_pid = (getattr(port, "vid", None), getattr(port, "pid", None))
        description = "{0} {1} {2}".format(
            getattr(port, "description", "") or "",
            getattr(port, "manufacturer", "") or "",
            getattr(port, "hwid", "") or "",
        ).lower()
        if vid_pid in ((0x10C4, 0xEA60), (0x1A86, 0x55D4)):
            candidates.append(port.device)
        elif any(hint in description for hint in ("cp210", "ch910", "wch.cn", "starcore")):
            candidates.append(port.device)
    candidates = sorted(set(candidates))
    if not candidates:
        raise BoardNotFoundError(
            "No StarCore V2 serial port was found. Check USB and the CP210x/CH9102 driver."
        )
    if len(candidates) > 1:
        raise BoardNotFoundError(
            "Multiple StarCore V2 ports were found: {0}. Specify the port explicitly.".format(
                ", ".join(candidates)
            )
        )
    return candidates[0]


def _offline_root():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "starbridge_offline")


def _flash_precompiled(port):
    root = _offline_root()
    bundle = os.path.join(root, "firmware", "starcore-v2")
    manifest_path = os.path.join(bundle, "manifest.json")
    esptool = os.path.join(root, "windows-x86_64", "esptool.exe")
    if not os.path.isfile(manifest_path) or not os.path.isfile(esptool):
        raise FirmwareRequiredError(
            "The Mind+ extension is missing its offline firmware resources. "
            "Reinstall the complete .mpext package."
        )
    with open(manifest_path, "r") as manifest_file:
        manifest = json.load(manifest_file)
    if manifest.get("format") != 1 or manifest.get("board") != "starcore-v2":
        raise FirmwareRequiredError("The bundled firmware manifest is invalid")

    images = []
    declared_images = manifest.get("images", [])
    if len(declared_images) != 4:
        raise FirmwareRequiredError("The bundled firmware must contain four images")
    for image in declared_images:
        filename = image.get("file")
        offset = image.get("offset")
        image_path = os.path.join(bundle, filename or "")
        if not offset or not os.path.isfile(image_path):
            raise FirmwareRequiredError("A bundled firmware image is missing")
        digest = hashlib.sha256()
        with open(image_path, "rb") as image_file:
            while True:
                chunk = image_file.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        if digest.hexdigest() != str(image.get("sha256", "")).lower():
            raise FirmwareRequiredError(
                "Firmware checksum failed for {0}".format(filename)
            )
        images.extend((offset, image_path))

    command = [
        esptool,
        "--chip", str(manifest.get("chip", "esp32")),
        "--port", port,
        "--baud", str(manifest.get("baud", 921600)),
        "--before", "default-reset",
        "--after", "hard-reset",
        "write-flash", "-z",
        "--flash-mode", "keep",
        "--flash-freq", "keep",
        "--flash-size", "keep",
    ] + images
    print("StarBridge Mind+：未检测到兼容固件，开始自动烧录，请勿拔出 USB。")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    output, unused = process.communicate()
    if process.returncode != 0:
        details = "\n".join((output or "").splitlines()[-8:])
        raise FirmwareRequiredError(
            "Automatic firmware installation failed. Check USB and serial port usage.\n{0}".format(
                details
            )
        )
    print("StarBridge Mind+：固件烧录完成，正在等待开发板重启。")


class _ProtocolClient(object):
    def __init__(self, port, timeout=1.0):
        self.serial = serial.Serial(port=port, baudrate=115200, timeout=0)
        self.timeout = timeout
        self.sequence = 0
        self.lock = threading.Lock()
        self.decoder = _StreamDecoder()

    def request(self, command, payload=b""):
        with self.lock:
            self.sequence = (self.sequence % 0xFFFF) + 1
            sequence = self.sequence
            self.serial.write(_encode_frame(1, sequence, command, payload))
            self.serial.flush()
            deadline = time.time() + self.timeout
            while time.time() < deadline:
                previous_timeout = self.serial.timeout
                self.serial.timeout = min(max(deadline - time.time(), 0.0), 0.05)
                try:
                    chunk = self.serial.read(64)
                finally:
                    self.serial.timeout = previous_timeout
                for frame in self.decoder.feed(chunk):
                    version, kind, response_sequence, response_command, response_payload = frame
                    if version != PROTOCOL_VERSION:
                        raise StarBridgeError(
                            "Board protocol {0} is incompatible with protocol 2".format(version)
                        )
                    if kind != 2 or response_sequence != sequence or response_command != command:
                        continue
                    if not response_payload:
                        raise StarBridgeError("Response is missing its status byte")
                    status = bytearray(response_payload)[0]
                    if status != 0:
                        raise BoardCommandError(command, status)
                    return response_payload[1:]
            raise StarBridgeError(
                "The board did not respond within {0:.1f} seconds".format(self.timeout)
            )

    def close(self):
        if self.serial.is_open:
            self.serial.close()


class BoardInfo(object):
    def __init__(self, values):
        self.protocol_version = values[0]
        self.firmware_major = values[1]
        self.firmware_minor = values[2]
        self.firmware_patch = values[3]
        self.board_id = values[4]
        self.capabilities = values[5]

    def __repr__(self):
        return "BoardInfo(protocol={0}, firmware={1}.{2}.{3}, board_id={4})".format(
            self.protocol_version,
            self.firmware_major,
            self.firmware_minor,
            self.firmware_patch,
            self.board_id,
        )


class Board(object):
    def __init__(self, client):
        self.client = client

    @classmethod
    def begin(
        cls,
        board_type=BoardType.STARCORE_V2,
        port=None,
        timeout=1.0,
        force_flash=False,
    ):
        if board_type != BoardType.STARCORE_V2:
            raise ValueError("Mind+ V1 currently supports StarCore V2 only")
        selected_port = _discover_port(port)
        if not force_flash:
            try:
                return cls._connect_compatible(selected_port, timeout)
            except Exception:
                pass

        _flash_precompiled(selected_port)
        deadline = time.time() + 12.0
        last_error = None
        while time.time() < deadline:
            try:
                return cls._connect_compatible(selected_port, timeout)
            except Exception as error:
                last_error = error
                time.sleep(0.4)
        raise FirmwareRequiredError(
            "Firmware was installed, but StarCore V2 did not reconnect: {0}".format(
                last_error
            )
        )

    @classmethod
    def _connect_compatible(cls, port, timeout):
        client = _ProtocolClient(port, timeout)
        board = cls(client)
        try:
            board.ping()
            info = board.info()
            if info.board_id != 1 or info.firmware_major < 4:
                raise FirmwareRequiredError(
                    "StarCore V2 requires StarBridge firmware 4.x or newer"
                )
            return board
        except Exception:
            board.close()
            raise

    def ping(self, data=b"starbridge"):
        return self.client.request(Command.PING, data)

    def info(self):
        data = self.client.request(Command.GET_INFO)
        if len(data) != 9:
            raise StarBridgeError("GET_INFO returned an invalid payload")
        return BoardInfo(struct.unpack("<BBBBBI", data))

    def reset_state(self):
        self.client.request(Command.RESET_STATE)

    def pin_mode(self, pin, mode):
        self.client.request(Command.PIN_MODE, bytes(bytearray((int(pin), int(mode)))))

    def digital_write(self, pin, value):
        self.client.request(
            Command.DIGITAL_WRITE, bytes(bytearray((int(pin), int(bool(value)))))
        )

    def digital_read(self, pin):
        data = self.client.request(Command.DIGITAL_READ, bytes(bytearray((int(pin),))))
        return bool(bytearray(data)[0])

    def analog_read(self, pin, millivolts=False):
        payload = bytes(bytearray((int(pin), int(bool(millivolts)))))
        data = self.client.request(Command.ANALOG_READ, payload)
        return struct.unpack("<I", data)[0]

    def analog_write(self, pin, value):
        if value < 0 or value > 255:
            raise ValueError("DAC value must be between 0 and 255")
        self.client.request(
            Command.ANALOG_WRITE, bytes(bytearray((int(pin), int(value))))
        )

    def pwm_configure(self, pin, frequency, resolution=8):
        self.client.request(
            Command.PWM_CONFIGURE,
            struct.pack("<BIB", int(pin), int(frequency), int(resolution)),
        )

    def pwm_write(self, pin, duty):
        self.client.request(Command.PWM_WRITE, struct.pack("<BI", int(pin), int(duty)))

    def pwm_stop(self, pin, idle_high=False):
        self.client.request(
            Command.PWM_STOP, bytes(bytearray((int(pin), int(bool(idle_high)))))
        )

    def dht11(self, pin):
        return DHT11(self.client, pin)

    def ultrasonic(self, trigger_pin, echo_pin, timeout_us=30000):
        return Ultrasonic(self.client, trigger_pin, echo_pin, timeout_us)

    def close(self):
        self.client.close()


class DHT11Reading(object):
    def __init__(self, temperature_c, humidity_percent):
        self.temperature_c = temperature_c
        self.humidity_percent = humidity_percent


_DHT_CACHE = {}


class DHT11(object):
    def __init__(self, client, pin):
        self.client = client
        self.pin = int(pin)

    def read(self):
        now = time.time()
        cached = _DHT_CACHE.get(self.pin)
        if cached is not None and now - cached[0] < 1.0:
            return cached[1]

        last_error = None
        for attempt in range(3):
            if attempt:
                time.sleep(1.1)
            try:
                data = self.client.request(
                    Command.DHT11_READ, bytes(bytearray((self.pin,)))
                )
            except BoardCommandError as error:
                if error.status != 5:
                    raise
                last_error = error
                continue
            if len(data) != 4:
                raise StarBridgeError("DHT11 returned an invalid payload")
            temperature, humidity = struct.unpack("<hH", data)
            reading = DHT11Reading(temperature / 10.0, humidity / 10.0)
            _DHT_CACHE[self.pin] = (time.time(), reading)
            return reading
        raise last_error


class Ultrasonic(object):
    def __init__(self, client, trigger_pin, echo_pin, timeout_us=30000):
        self.client = client
        self.trigger_pin = int(trigger_pin)
        self.echo_pin = int(echo_pin)
        self.timeout_us = int(timeout_us)

    def read_mm(self):
        payload = struct.pack(
            "<BBI", self.trigger_pin, self.echo_pin, self.timeout_us
        )
        data = self.client.request(Command.ULTRASONIC_READ, payload)
        return struct.unpack("<I", data)[0]

    def read_cm(self):
        return self.read_mm() / 10.0
