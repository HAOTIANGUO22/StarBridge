# 星核板 V2 引脚定义

StarBridge v4 的首个目标硬件是星核板 V2。固件和 Python SDK 使用板载丝印名称，不要求使用者记忆底层 ESP32 GPIO。

板载 SPI Flash 型号为 GD25Q64（64 Mbit，即 8 MB）。Arduino 板型默认采用 `default_8MB` 分区和 3,342,336 字节最大应用空间。

## P 口

| 星核板口 | ESP32 GPIO | 主要能力 |
|---|---:|---|
| P0 | 33 | 数字、ADC、PWM |
| P1 | 32 | 数字、ADC、PWM |
| P2 | 35 | 数字输入、ADC，仅输入 |
| P3 | 34 | 数字输入、ADC，仅输入；板载扩展按键 |
| P4 | 39 | 数字输入、ADC，仅输入；板载光线传感器 |
| P5 | 0 | 数字、PWM；板载按键 A、启动配置脚 |
| P6 | 16 | 数字、PWM；板载蜂鸣器 |
| P7 | 17 | 数字、PWM；板载 3 颗 WS2812B |
| P8 | 26 | 数字、ADC、DAC、PWM |
| P9 | 25 | 数字、ADC、DAC、PWM |
| P10 | 36 | 数字输入、ADC，仅输入 |
| P11 | 2 | 数字、ADC、PWM；板载按键 B、启动配置脚 |
| P13 | 18 | 数字、PWM |
| P14 | 19 | 数字、PWM |
| P15 | 21 | 数字、PWM |
| P16 | 5 | 数字、PWM；启动配置脚 |
| P19 / SCL | 22 | 数字、PWM、I²C SCL |
| P20 / SDA | 23 | 数字、PWM、I²C SDA |

原理图没有引出 P12、P17 和 P18。代码因此不为它们定义可用引脚。

## 字母 IO 口

| 丝印 | ESP32 GPIO |
|---|---:|
| P | 27 |
| Y | 14 |
| T | 12 |
| H | 13 |
| O | 15 |
| N | 4 |

这六路信号在原理图中各经过 510 Ω 串联电阻。GPIO12、GPIO15 等属于 ESP32 启动配置相关引脚，外设上电时不应强行拉到影响启动的电平。

## 板载资源别名

Python SDK 同时提供以下可读名称：

```python
Pin.MICROPHONE       # GPIO38
Pin.LIGHT            # P4 / GPIO39
Pin.BUTTON_A         # P5 / GPIO0
Pin.BUTTON_B         # P11 / GPIO2
Pin.BUZZER           # P6 / GPIO16
Pin.ONBOARD_PIXELS   # P7 / GPIO17，3 颗 WS2812B
Pin.I2C_SCL          # P19 / GPIO22
Pin.I2C_SDA          # P20 / GPIO23
```

板载 OLED 与其他 I²C 器件统一使用 SDA GPIO23、SCL GPIO22。麦克风 GPIO38 只加入 ADC 输入集合，不作为普通数字输出使用。
