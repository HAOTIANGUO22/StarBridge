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
    └── DFR0534 MP3
```

项目包含以下部分：

- `starbridge` Python SDK：向应用程序提供统一的开发板控制接口。
- StarBridge Protocol V2：负责请求、响应、CRC 校验、命令序号和错误处理。
- 预编译开发板固件：随官方 wheel 分发，用于首次自动烧录。
- 自动测试与构建脚本：检查 Python SDK 并生成可安装 wheel。

本公开仓库提供用户开发所需的 API、协议、文档和预编译固件。下位机固件生产源码在独立私有仓库维护，不包含在源码仓库或 wheel 中。

## 支持的开发板

当前正式支持：

| 开发板 | MCU | 支持状态 |
|---|---|---|
| 星核板 V2 | ESP32 | 正式支持 |

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
- 固件版本、板型和能力查询
- 外设状态统一复位

完整命令定义见 [StarBridge Protocol V2](docs/protocol-v2.md)。引脚对应关系见 [星核板 V2 引脚定义](docs/starcore-v2-pinout.md)。

全部元器件示例见 [HTML 示例手册](docs/examples.html)，实机测试发现与待办见 [测试问题记录](docs/test-findings.md)。

## 快速开始

### 1. 安装 Python SDK

项目要求 Python 3.10 或更高版本：

```powershell
# 从 GitHub Release 安装
python -m pip install https://github.com/HAOTIANGUO22/StarBridge/releases/download/v4.4.0/starbridge-4.4.0-py3-none-any.whl

# 开发仓库中使用可编辑安装
python -m pip install -e .\python
```

Windows wheel 已包含用 ESP32 Core 3.3.11 编译的 StarCore V2 固件和官方 esptool 5.3.1。用户安装这一个 wheel 后，`Board.begin()` 可在无 Arduino IDE、Arduino CLI 或 ESP32 Core 的电脑上自动烧录。

如需从公开仓库重新打包已有的预编译资源，先安装 `build`，再执行：

```powershell
python -m pip install build
.\tools\build-wheel.ps1
```

构建脚本会校验私有构建流程交付的固件包，然后将预编译镜像和烧录器装入 wheel。公开构建过程不会包含或重新编译下位机源码。

### 2. 无需准备额外烧录环境

安装官方 Windows wheel 后，不需要 Arduino IDE、Arduino CLI、ESP32 Core 或固件源码。首次连接时 SDK 会使用 wheel 内置的校验清单、固件镜像和烧录器完成部署。

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

Arduino Uno 已进入板型注册表，可以使用 `BoardType.ARDUINO_UNO` 声明；在 Uno 固件加入项目之前，SDK 会明确报告该目标尚未实现，不会把 ESP32 固件烧入 Uno。

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

## 目录结构

```text
docs/                              协议、引脚和开发文档
python/
  src/starbridge/                  Python SDK 与预编译离线资源
  tests/                           SDK 与协议自动测试
tools/build-wheel.ps1              构建公开安装包
tools/verify.ps1                   验证公开 SDK
```

## 验证工程

```powershell
.\tools\verify.ps1
```

该脚本会运行 Python 自动测试并检查公开 SDK 源码。下位机固件在私有构建流程中单独编译和验证。

开发目录约定见 [开发指南](docs/development.md)，后续功能规划见 [路线图](docs/roadmap.md)。

## 许可证

StarBridge 自有代码采用 MIT License。U8g2、DFRobot_DHT11、Adafruit_NeoPixel 和 EspSoftwareSerial 保留各自许可证，详见 [第三方声明](THIRD_PARTY_NOTICES.md)。
