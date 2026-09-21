from __future__ import annotations

from enum import IntEnum, StrEnum


PROTOCOL_VERSION = 2
MAX_PAYLOAD = 256


class BoardType(StrEnum):
    STARCORE_V2 = "starcore-v2"
    ARDUINO_UNO = "arduino-uno"


class FrameKind(IntEnum):
    REQUEST = 1
    RESPONSE = 2
    EVENT = 3


class Command(IntEnum):
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
    OLED_INIT = 0x30
    OLED_CLEAR = 0x31
    OLED_SHOW = 0x32
    OLED_TEXT = 0x33
    OLED_PIXEL = 0x34
    OLED_LINE = 0x35
    OLED_RECT = 0x36
    OLED_BITMAP = 0x37
    DHT11_READ = 0x40
    NEOPIXEL_INIT = 0x50
    NEOPIXEL_SET = 0x51
    NEOPIXEL_FILL = 0x52
    NEOPIXEL_SHOW = 0x53
    NEOPIXEL_CLEAR = 0x54
    ULTRASONIC_READ = 0x60
    MP3_INIT = 0x70
    MP3_PLAY_TRACK = 0x71
    MP3_PLAY = 0x72
    MP3_PAUSE = 0x73
    MP3_STOP = 0x74
    MP3_NEXT = 0x75
    MP3_PREVIOUS = 0x76
    MP3_SET_VOLUME = 0x77
    MP3_STATUS = 0x78
    MP3_BUSY = 0x79


class Status(IntEnum):
    OK = 0
    BAD_FRAME = 1
    BAD_VERSION = 2
    BAD_COMMAND = 3
    BAD_LENGTH = 4
    BAD_ARGUMENT = 5
    UNSUPPORTED = 6
    BUSY = 7
    INTERNAL_ERROR = 8


class PinMode(IntEnum):
    INPUT = 0
    OUTPUT = 1
    INPUT_PULLUP = 2
    INPUT_PULLDOWN = 3


class OledFont(IntEnum):
    ASCII_6X12 = 0
    CHINESE_GB2312_12 = 1


class Pin(IntEnum):
    """星核板 V2 connector and onboard-resource pin map."""
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
    P_P = 27
    P_Y = 14
    P_T = 12
    P_H = 13
    P_O = 15
    P_N = 4
    MICROPHONE = 38
    LIGHT = 39
    BUTTON_A = 0
    BUTTON_B = 2
    BUZZER = 16
    ONBOARD_PIXELS = 17
    I2C_SCL = 22
    I2C_SDA = 23
