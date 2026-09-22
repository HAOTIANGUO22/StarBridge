# StarBridge

StarBridge 是一个通过 Python 控制微控制器开发板及其外设的软硬件开发平台。项目在电脑端提供统一的 Python API，在开发板端运行对应固件，并通过带校验、序号和错误码的串口协议连接两端。

使用 StarBridge，可以在 Python 程序中直接控制 GPIO、PWM、传感器、显示屏、灯带和串口设备，而不需要为每个实验重复编写底层串口通信代码。

## 项目组成

```text
Python 程序
    │
    │ StarBridge Protocol V2 / USB 串口
    ▼
开发板固件
    │
    ├── GPIO / ADC / DAC / PWM
    ├── OLED
    ├── DHT11
    ├── WS2812
    ├── 超声波传感器
    ├── DFR0534 MP3
    └── PN532 NFC（I²C）
```

项目包含以下部分：

- `starbridge` Python SDK：向应用程序提供统一的开发板控制接口。
- StarBridge Protocol V2：负责请求、响应、CRC 校验、命令序号和错误处理。
- 预编译开发板固件：随官方 wheel 分发，用于首次自动烧录。
- 自动测试与构建脚本：检查 Python SDK 并生成可安装 wheel。

本仓库统一维护 Python API、通信协议、星核板 V2 下位机生产源码、板级依赖和预编译发布固件。wheel 只携带编译后的离线烧录资源，不携带 C/C++ 源码。

## 支持的开发板

当前正式支持：

| 开发板 | MCU | 支持状态 |
|---|---|---|
| 星核板 V2 | ESP32 | 正式支持 |
| 星尘板 StarDust | ATmega328P / CH340 | 固件与离线烧录支持，实机待测 |

项目采用多板型结构。不同开发板拥有独立固件和引脚定义，共享同一套通信协议与 Python SDK。Arduino Uno、其他 ESP32 型号和更多架构可以作为新的目标板加入。

## 硬件能力

星核板 V2 固件提供：

- 数字输入与输出
- ADC 模拟输入和毫伏读取
- DAC 模拟输出
- PWM 频率、分辨率和占空比控制
- SSD1306 128×64 OLED 绘图与中文显示
- DHT11 温湿度读取
- WS2812 RGB 灯带及板载三颗 RGB 灯控制
- 超声波距离测量
- DFR0534 MP3 播放模块控制
- 软件串口 MP3 通信
- 通用 PN532 NFC 寻卡、UID、MIFARE Classic 和 NTAG/Ultralight 读写
- ESP32 原生 Wi-Fi、ESP-NOW、SNTP 网络时间与通用软串口
- Python 主机侧天气、时区时间、语音识别和 OpenAI 兼容大模型 API
- 固件版本、板型和能力查询
- 外设状态统一复位

完整命令定义见 [StarBridge Protocol V2](docs/protocol-v2.md)。引脚对应关系见 [星核板 V2 引脚定义](docs/starcore-v2-pinout.md) 和 [星尘板引脚与板卡参数](docs/stardust-pinout.md)。

全部元器件示例见 [HTML 示例手册](docs/examples.html)，实机测试发现与待办见 [测试问题记录](docs/test-findings.md)。

## 快速开始

### 1. 安装 Python SDK

项目要求 Python 3.10 或更高版本：

```powershell
# 从 PyPI 安装（发行名为 starbridge-hardware，导入名仍为 starbridge）
python -m pip install starbridge-hardware

# 也可以从 GitHub Release 安装
python -m pip install https://github.com/HAOTIANGUO22/StarBridge/releases/download/v4.5.0/starbridge_hardware-4.5.0-py3-none-any.whl

# 开发仓库中使用可编辑安装
python -m pip install -e .\python
```

Windows wheel 已包含 StarCore V2 和 StarDust 的预编译固件，以及 esptool 与 avrdude 离线烧录器。用户安装这一个 wheel 后，`Board.begin()` 可在无 Arduino IDE、Arduino CLI 或板卡 Core 的电脑上自动烧录。

如需从源码重新编译固件并构建 wheel，先安装 `build`，再执行：

```powershell
python -m pip install build
.\tools\build-wheel.ps1
```

构建脚本会准备固定版本的 Arduino CLI、ESP32 Core 与 Arduino AVR Core，编译 `firmware/starcore-v2` 和 `firmware/stardust`，刷新 Python 包内的离线固件和 manifest 哈希，然后将预编译镜像与烧录器装入 wheel。

### 2. 无需准备额外烧录环境

安装官方 Windows wheel 后，不需要 Arduino IDE、Arduino CLI、ESP32/AVR Core 或固件源码。首次连接时 SDK 会使用 wheel 内置的校验清单、固件镜像和烧录器完成部署。

### 3. 声明板型并开始使用

`Board.begin()` 会执行以下流程：

1. 根据声明的板型识别 USB 串口。
2. 尝试读取板型 ID 和固件版本。
3. 已有兼容固件时直接连接，不重复烧录。
4. 没有兼容固件时，Windows wheel 直接使用内置镜像烧录。
5. 等待开发板重启并返回可用的 `Board` 对象。

```python
from starbridge import Board, BoardType, Pin

with Board.begin(BoardType.STARCORE_V2) as board:
    print(board.info())

    climate = board.dht11(Pin.P0).read()
    print(climate.temperature_c, climate.humidity_percent)

    distance_cm = board.ultrasonic(Pin.P6, Pin.P7).read_cm()
    print(distance_cm)

    pixels = board.neopixel(Pin.ONBOARD_PIXELS, 3, brightness=64)
    pixels.set_pixel(0, 255, 0, 0)
    pixels.show()
```

存在多个相同串口设备时，可以明确指定串口；需要重新烧录时可以使用 `force_flash=True`：

```python
board = Board.begin(
    BoardType.STARCORE_V2,
    port="COM7",
    force_flash=True,
)
```

星尘板使用 `BoardType.STARDUST` 和 `StardustPin`，支持 D2、D3、D5、D6、D9、D10、A0-A3 的 GPIO，A0-A3 ADC、固定频率 8 位 PWM、DHT11、超声波测距、最多 16 颗 WS2812、SSD1306 OLED 常用中文、PN532 I²C、DFR0534 MP3 和通用软件串口。专用 I²C 口为 SDA=A4、SCL=A5。Arduino Uno 仍作为未实现的通用板型占位，不会被错误烧录。

## OLED 中文显示

星核板 OLED 使用 `P20/SDA = GPIO23`、`P19/SCL = GPIO22`，默认地址为 `0x3C`。

```python
from starbridge import Board, BoardType

with Board.begin(BoardType.STARCORE_V2) as board:
    oled = board.oled().begin()
    oled.clear()
    oled.text(0, 14, "你好，StarBridge")
    oled.rect(0, 18, 128, 30)
    oled.show()
```

## MP3 播放模块

DFR0534 使用 9600 baud 软件串口。引脚名称从开发板角度描述：开发板 RX 连接模块 `T`，开发板 TX 连接模块 `R`，BUSY 引脚可以省略。

```python
from starbridge import Board, BoardType, Pin

with Board.begin(BoardType.STARCORE_V2) as board:
    # 开发板 P15=RX 接模块 TX；P16=TX 接模块 RX
    mp3 = board.mp3(Pin.P15, Pin.P16)
    mp3.set_volume(20)
    mp3.play_track(1)
```

## PN532 NFC（I²C）

将 PN532 模块切换到 I²C 模式，SDA 接 P20、SCL 接 P19。IRQ 和 RSTPD_N 可不接；若模块上电后无法唤醒，可把 RSTPD_N 接到一个可输出引脚并传给 `reset_pin`。

```python
from starbridge import Board, BoardType, Pin

with Board.begin(BoardType.STARCORE_V2) as board:
    nfc = board.pn532(reset_pin=Pin.P0).begin()
    uid = nfc.scan()
    print(None if uid is None else uid.hex("-").upper())

    # NTAG / MIFARE Ultralight：每页 4 字节
    if uid is not None:
        print(nfc.read_page(4))
```

## Wi-Fi、ESP-NOW、软串口与云 API

```python
from starbridge import Board, BoardType, CloudClient, Pin

with Board.begin(BoardType.STARCORE_V2) as board:
    wifi = board.wifi()
    print(wifi.connect("你的 2.4G Wi-Fi", "密码"))
    print(board.network_time().synchronize(utc_offset=8 * 3600))

    radio = board.espnow()  # Wi-Fi 已连接时沿用同一信道
    radio.add_peer("AA:BB:CC:DD:EE:FF")
    radio.send("AA:BB:CC:DD:EE:FF", b"hello")

    uart = board.software_serial(Pin.P6, Pin.P7, 9600)
    uart.write(b"AT\r\n")

cloud = CloudClient()
print(cloud.weather(31.2304, 121.4737))
print(cloud.time("Asia/Shanghai"))
print(cloud.chat("用一句话介绍上海"))  # 从 OPENAI_API_KEY 读取密钥
print(cloud.transcribe("recording.wav"))
```

云 API 运行在电脑端；不要把 API 密钥写进固件或提交到 Git。`CloudClient` 只使用 Python 标准库，不新增运行时依赖。

## 目录结构

```text
firmware/
  arduino-board-package/           StarBridge Arduino 板卡定义
  starcore-v2/                     星核板 V2 固件源码、驱动和专用库
  stardust/                        星尘板 AVR 固件源码
python/
  src/starbridge/                  Python SDK 与构建生成的离线资源
  tests/                           SDK 与协议自动测试
docs/                              协议、引脚、示例、测试和发布文档
tools/                             工具链、验证、构建与清理脚本
artifacts/                         可删除、可重建的构建产物
MAINTENANCE.md                     后续人类与 AI 的维护规则
```

## 验证工程

```powershell
.\tools\verify.ps1
```

该脚本会运行 Python 自动测试、字节码检查，并完整编译星核板 V2 与星尘板固件。

新增星核板功能或 Arduino Uno 等新板型前，必须先阅读 [工程维护指南](MAINTENANCE.md)。简要开发入口见 [开发指南](docs/development.md)，后续功能规划见 [路线图](docs/roadmap.md)。

## 许可证

StarBridge 自有代码采用 MIT License。U8g2、DFRobot_DHT11、Adafruit_NeoPixel 和 EspSoftwareSerial 保留各自许可证，详见 [第三方声明](THIRD_PARTY_NOTICES.md)。
