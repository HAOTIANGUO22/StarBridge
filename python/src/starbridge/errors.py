from __future__ import annotations

from .constants import Command, Status


class StarBridgeError(Exception):
    """Base SDK exception."""


class ProtocolError(StarBridgeError):
    """A malformed or incompatible protocol frame was received."""


class ConnectionClosedError(StarBridgeError):
    """The serial connection is closed."""


class RequestTimeoutError(StarBridgeError):
    """The board did not answer before the request deadline."""


class BoardCommandError(StarBridgeError):
    def __init__(self, status: int, command: int) -> None:
        self.status = status
        self.command = command
        super().__init__(_friendly_command_error(status, command))


class BoardNotFoundError(StarBridgeError):
    """No unambiguous serial port was found for the selected board."""


class FirmwareInstallError(StarBridgeError):
    """Firmware compilation or upload failed."""


class UnsupportedBoardError(StarBridgeError):
    """The board is known, but no usable firmware target exists yet."""


_COMMAND_NAMES = {
    Command.PIN_MODE: "设置引脚模式",
    Command.DIGITAL_WRITE: "数字输出",
    Command.DIGITAL_READ: "数字输入",
    Command.ANALOG_READ: "模拟量读取",
    Command.ANALOG_WRITE: "模拟量输出",
    Command.PWM_CONFIGURE: "PWM 配置",
    Command.PWM_WRITE: "PWM 输出",
    Command.PWM_STOP: "PWM 停止",
    Command.OLED_INIT: "OLED 初始化",
    Command.OLED_CLEAR: "OLED 清屏",
    Command.OLED_SHOW: "OLED 刷新",
    Command.OLED_TEXT: "OLED 文字显示",
    Command.OLED_PIXEL: "OLED 像素绘制",
    Command.OLED_LINE: "OLED 线条绘制",
    Command.OLED_RECT: "OLED 矩形绘制",
    Command.OLED_BITMAP: "OLED 位图绘制",
    Command.DHT11_READ: "DHT11 温湿度读取",
    Command.NEOPIXEL_INIT: "WS2812 初始化",
    Command.NEOPIXEL_SET: "WS2812 像素设置",
    Command.NEOPIXEL_FILL: "WS2812 填充",
    Command.NEOPIXEL_SHOW: "WS2812 刷新",
    Command.NEOPIXEL_CLEAR: "WS2812 清除",
    Command.ULTRASONIC_READ: "超声波测距",
    Command.MP3_INIT: "MP3 模块初始化",
    Command.MP3_PLAY_TRACK: "MP3 曲目播放",
    Command.MP3_PLAY: "MP3 播放",
    Command.MP3_PAUSE: "MP3 暂停",
    Command.MP3_STOP: "MP3 停止",
    Command.MP3_NEXT: "MP3 下一曲",
    Command.MP3_PREVIOUS: "MP3 上一曲",
    Command.MP3_SET_VOLUME: "MP3 音量设置",
    Command.MP3_STATUS: "MP3 状态读取",
    Command.MP3_BUSY: "MP3 BUSY 读取",
    Command.PN532_INIT: "PN532 初始化",
    Command.PN532_FIRMWARE_VERSION: "PN532 固件版本读取",
    Command.PN532_SCAN: "PN532 NFC 寻卡",
    Command.PN532_CLASSIC_READ: "MIFARE Classic 块读取",
    Command.PN532_CLASSIC_WRITE: "MIFARE Classic 块写入",
    Command.PN532_PAGE_READ: "NTAG/Ultralight 页读取",
    Command.PN532_PAGE_WRITE: "NTAG/Ultralight 页写入",
    Command.SOFTWARE_SERIAL_INIT: "软串口初始化",
    Command.SOFTWARE_SERIAL_WRITE: "软串口发送",
    Command.SOFTWARE_SERIAL_READ: "软串口接收",
    Command.WIFI_CONNECT: "Wi-Fi 连接",
    Command.WIFI_STATUS: "Wi-Fi 状态读取",
    Command.ESPNOW_INIT: "ESP-NOW 初始化",
    Command.ESPNOW_ADD_PEER: "ESP-NOW 添加节点",
    Command.ESPNOW_SEND: "ESP-NOW 发送",
    Command.ESPNOW_RECEIVE: "ESP-NOW 接收",
    Command.TIME_SYNC: "网络时间同步",
    Command.TIME_NOW: "网络时间读取",
}

_STATUS_NAMES = {
    Status.BAD_FRAME: "通信帧格式错误",
    Status.BAD_VERSION: "协议版本不兼容",
    Status.BAD_COMMAND: "当前固件不支持这个功能",
    Status.BAD_LENGTH: "发送的数据长度不正确",
    Status.BAD_ARGUMENT: "参数、接线或传感器返回值无效",
    Status.UNSUPPORTED: "当前硬件配置不支持这个功能",
    Status.BUSY: "设备正忙或暂时没有响应",
    Status.INTERNAL_ERROR: "开发板内部执行失败",
}

_COMMAND_GUIDANCE = {
    Command.DHT11_READ: (
        "确认 DATA 接在支持双向输入输出的引脚上（不要使用仅输入的 P2、P3、P4、P10），"
        "检查 VCC/GND 和上拉电阻，并将连续读取间隔设为至少 1 秒。"
    ),
    Command.ULTRASONIC_READ: (
        "确认 TRIG/ECHO 顺序、供电和共地；HC-SR04 的 ECHO 需降压到 3.3V。"
        "物体紧贴探头、超出量程或角度过斜时不会产生有效回波，请捕获此异常后继续测量。"
    ),
    Command.OLED_INIT: (
        "确认 OLED 使用 0x3C 地址，SDA 接 P20、SCL 接 P19，并检查供电和共地。"
    ),
    Command.NEOPIXEL_INIT: (
        "确认灯带数据脚、灯珠数量、供电和共地正确；外接灯带建议使用独立电源并共地。"
    ),
    Command.MP3_INIT: (
        "确认开发板 RX 连接模块 T、开发板 TX 连接模块 R，模块波特率为 9600，并检查供电和共地。"
    ),
    Command.PN532_INIT: (
        "确认 PN532 已切换到 I²C 模式，SDA 接 P20、SCL 接 P19，并检查 3.3V 逻辑电平和共地；"
        "模块无法从休眠唤醒时再连接 RSTPD_N 并传入 reset_pin。"
    ),
    Command.PN532_SCAN: (
        "确认卡片支持 ISO14443A，并贴近天线；没有卡片时 scan() 会正常返回 None。"
    ),
    Command.PN532_CLASSIC_READ: (
        "确认卡片为 MIFARE Classic，块号和 A/B 密钥正确，并保持卡片贴近天线。"
    ),
    Command.PN532_CLASSIC_WRITE: (
        "确认卡片未锁定、块号和 A/B 密钥正确；写入期间不要移动卡片。"
    ),
    Command.PN532_PAGE_READ: (
        "确认卡片为 NTAG 或 MIFARE Ultralight，页号有效，并保持卡片贴近天线。"
    ),
    Command.PN532_PAGE_WRITE: (
        "确认标签页未锁定且页号位于可写区域；写入期间不要移动卡片。"
    ),
    Command.WIFI_CONNECT: (
        "确认 SSID、密码和 2.4 GHz 网络可用；ESP32 不支持仅 5 GHz 的接入点。"
    ),
    Command.ESPNOW_INIT: (
        "确认信道为 1–14；若 Wi-Fi 已连接，ESP-NOW 必须使用相同信道。"
    ),
    Command.TIME_SYNC: (
        "先连接 Wi-Fi，并确认网络允许访问所选 NTP 服务器。"
    ),
}


def command_name(command: int) -> str:
    try:
        typed = Command(command)
    except ValueError:
        return f"命令 0x{command:02X}"
    return _COMMAND_NAMES.get(typed, typed.name)


def _friendly_command_error(status: int, command: int) -> str:
    try:
        typed_status = Status(status)
    except ValueError:
        typed_status = None
    try:
        typed_command = Command(command)
    except ValueError:
        typed_command = None

    status_name = _STATUS_NAMES.get(typed_status, "开发板返回未知错误")
    guidance = (
        _COMMAND_GUIDANCE.get(typed_command)
        if typed_status in (Status.BAD_ARGUMENT, Status.BUSY)
        else None
    )
    if guidance is None:
        guidance = {
            Status.BAD_ARGUMENT: "检查所选引脚是否支持该功能，以及参数是否处于允许范围。",
            Status.BUSY: "稍等片刻后重试，并检查外设是否正确连接和供电。",
            Status.BAD_VERSION: "升级 StarBridge Python 包并重新烧录匹配的固件。",
            Status.BAD_COMMAND: "升级开发板固件后重试。",
        }.get(typed_status, "检查接线和参数；若问题持续，请重新连接开发板后再试。")
    return (
        f"{command_name(command)}失败：{status_name}。解决建议：{guidance} "
        f"[技术信息：命令 0x{command:02X}，状态 {status}]"
    )
