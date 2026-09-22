# 星尘板引脚与板卡参数

星尘板的芯片和引导程序与 Arduino Uno 兼容：ATmega328P、16 MHz、5 V 逻辑、32 KB Flash（引导程序后可用 32256 字节）、2 KB SRAM，上传协议为 Optiboot `arduino` 115200 baud。USB 串口芯片为 CH340。

- 板型标识：`stardust`
- Python 板型：`BoardType.STARDUST`
- Protocol V2 `board_id`：`3`
- FQBN：`starbridge:avr:stardust`
- Arduino 核心：`arduino:avr@1.8.8`

## 可用引脚

| 板上标识 | Arduino 数值 | 数字 I/O | ADC | PWM |
|---|---:|:---:|:---:|:---:|
| D2 | 2 | 是 | 否 | 否 |
| D3 | 3 | 是 | 否 | 是，490 Hz |
| D5 | 5 | 是 | 否 | 是，980 Hz |
| D6 | 6 | 是 | 否 | 是，980 Hz |
| D9 | 9 | 是 | 否 | 是，490 Hz |
| D10 | 10 | 是 | 否 | 是，490 Hz |
| A0 | 14 | 是 | 是 | 否 |
| A1 | 15 | 是 | 是 | 否 |
| A2 | 16 | 是 | 是 | 否 |
| A3 | 17 | 是 | 是 | 否 |

D0/RX 和 D1/TX 连接 CH340，专用于 115200 baud 的 StarBridge Protocol V2，不得作为用户 GPIO。其他 Uno 数字引脚在星尘板 variant 中标记为不可用，固件也会拒绝这些引脚参数。板上独立 I²C 接口使用 SDA=A4、SCL=A5，专用于 SSD1306、PN532 等 I²C 外设，不作为通用 GPIO 开放。

## 固件能力

固件 4.3.1 支持 Protocol V2 的板卡信息、Ping、状态复位、数字 I/O、A0-A3 的 10 位 ADC 与毫伏换算（按 5 V 参考电压）、五个固定频率的 8 位 PWM 引脚、DHT11、WS2812、超声波测距、SSD1306 OLED、PN532 I²C、DFR0534 MP3 和通用软件串口。由于 ATmega328P 没有 DAC，`ANALOG_WRITE` 返回 `UNSUPPORTED`。`INPUT_PULLDOWN` 也不受 AVR 硬件支持。

AVR 资源限制：

- WS2812 最多 16 颗。
- OLED 使用 U8g2 文泉驿 12px 的 411 字常用中文子集；完整 GB2312 字库约 208 KB，无法装入 32 KB Flash。ASCII 与子集中的中文可使用同一 `text()` API。
- OLED 采用 128 字节分页显示和 256 字节绘图队列；支持文字、像素、直线、矩形，但 `OLED_BITMAP` 在星尘板上返回 `UNSUPPORTED`。`clear()` 可清空队列后继续绘制。
- 通用软件串口与 MP3 软件串口互斥；后初始化的功能会关闭前一路。通用软件串口支持 300–115200 baud，单次读写最多 96 字节。
- OLED 和 PN532 共用一组 I²C 总线；SSD1306 通常为 `0x3C`，PN532 为 `0x24`。

Python 使用示例：

```python
from starbridge import Board, BoardType, PinMode, StardustPin

with Board.begin(BoardType.STARDUST) as board:
    board.pin_mode(StardustPin.D2, PinMode.OUTPUT)
    board.digital_write(StardustPin.D2, True)
    print(board.analog_read(StardustPin.A0))

    board.pwm_configure(StardustPin.D9, 490, resolution=8)
    board.pwm_write(StardustPin.D9, 128)

    sonar = board.ultrasonic(StardustPin.D2, StardustPin.D3)
    print(sonar.read_cm())
```

超声波模块以第一个引脚连接 Trig、第二个引脚连接 Echo；两者必须是不同的可用 GPIO。常见 HC-SR04 可直接使用星尘板的 5 V 逻辑，默认等待回波的超时时间为 30 ms。
