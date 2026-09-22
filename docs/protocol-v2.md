# StarBridge Protocol V2

All multi-byte integers use little-endian byte order. The PC is the requester; the board returns exactly one response for each valid request frame.

## Frame

| Offset | Size | Field | Description |
|---:|---:|---|---|
| 0 | 2 | SOF | `A5 5A` |
| 2 | 1 | version | `02` |
| 3 | 1 | kind | request `01`, response `02`, event `03` |
| 4 | 2 | sequence | Request identifier, 1–65535 |
| 6 | 1 | command | Command identifier |
| 7 | 2 | length | Payload size, maximum 256 |
| 9 | N | payload | Command-specific data |
| 9+N | 2 | CRC | CRC16-CCITT over version through payload, initial `FFFF` |

Response payload byte zero is always a status code. Remaining bytes are response data.

## Capability bits

`GET_INFO` 的 capability `u32` 按位表示功能组：bit 0 GPIO、bit 1 ADC/DAC、bit 2 PWM、bit 3 OLED、bit 4 DHT11、bit 5 NeoPixel、bit 6 超声波、bit 7 MP3、bit 8 板级服务（保留）、bit 9 PN532、bit 10 软件串口、bit 11 Wi-Fi、bit 12 ESP-NOW、bit 13 网络时间。星核板 V2 返回 `0x00003FFF`；星尘板 4.3.1 返回 `0x000006FF`。具体命令不受某块板支持时必须返回 `UNSUPPORTED`。

## Status codes

| Value | Name | Meaning |
|---:|---|---|
| 0 | OK | Command completed |
| 1 | BAD_FRAME | Invalid kind or frame semantics |
| 2 | BAD_VERSION | Unsupported protocol version |
| 3 | BAD_COMMAND | Unknown command |
| 4 | BAD_LENGTH | Payload length does not match command |
| 5 | BAD_ARGUMENT | Pin, mode, value or range is invalid |
| 6 | UNSUPPORTED | Valid feature unavailable on this board |
| 7 | BUSY | Resource is temporarily busy |
| 8 | INTERNAL_ERROR | Unexpected firmware failure |

## Commands

| ID | Command | Request payload | Response data |
|---:|---|---|---|
| `01` | PING | arbitrary bytes, max 255 | same bytes |
| `02` | GET_INFO | empty | protocol, firmware `major.minor.patch`, board id, capability `u32` |
| `03` | RESET_STATE | empty | empty |
| `10` | PIN_MODE | pin `u8`, mode `u8` | empty |
| `11` | DIGITAL_WRITE | pin `u8`, value `u8` | empty |
| `12` | DIGITAL_READ | pin `u8` | value `u8` |
| `13` | ANALOG_READ | pin `u8`, millivolts `u8` | value `u32` |
| `14` | ANALOG_WRITE | pin `u8`, DAC value `u8` | empty |
| `20` | PWM_CONFIGURE | pin `u8`, frequency `u32`, resolution `u8` | empty |
| `21` | PWM_WRITE | pin `u8`, duty `u32` | empty |
| `22` | PWM_STOP | pin `u8`, idle-high `u8` | empty |
| `30` | OLED_INIT | I²C address `u8`, rotate-180 `u8` | empty |
| `31` | OLED_CLEAR | white `u8` | empty |
| `32` | OLED_SHOW | empty | empty |
| `33` | OLED_TEXT | x, baseline, font, UTF-8 bytes | empty |
| `34` | OLED_PIXEL | x, y, white | empty |
| `35` | OLED_LINE | x0, y0, x1, y1, white | empty |
| `36` | OLED_RECT | x, y, width, height, filled, white | empty |
| `37` | OLED_BITMAP | x, y, width, height, XBM bytes | empty |
| `40` | DHT11_READ | pin `u8` | temperature ×10 `i16`, humidity ×10 `u16` |
| `50` | NEOPIXEL_INIT | pin `u8`, count `u16`, brightness `u8` | empty |
| `51` | NEOPIXEL_SET | index `u16`, R, G, B, W (`u8` each) | empty |
| `52` | NEOPIXEL_FILL | first `u16`, count `u16`, R, G, B, W | empty |
| `53` | NEOPIXEL_SHOW | empty | empty |
| `54` | NEOPIXEL_CLEAR | empty | empty |
| `60` | ULTRASONIC_READ | trigger pin, echo pin, timeout µs `u32` | distance mm `u32` |
| `70` | MP3_INIT | software RX pin, software TX pin, BUSY pin or `FF` | empty |
| `71` | MP3_PLAY_TRACK | track `u16` | empty |
| `72`–`76` | MP3 play, pause, stop, next, previous | empty | empty |
| `77` | MP3_SET_VOLUME | volume `u8` (0–30) | empty |
| `78` | MP3_STATUS | empty | module status `u8` |
| `79` | MP3_BUSY | empty | busy `u8` |
| `80` | PN532_INIT | IRQ pin or `FF`, RSTPD_N pin or `FF` | chip, firmware major, minor, support (`u32`) |
| `81` | PN532_FIRMWARE_VERSION | empty | chip, firmware major, minor, support (`u32`) |
| `82` | PN532_SCAN | timeout ms `u16` (1–800) | UID length `u8`, UID bytes; zero length means no tag |
| `83` | PN532_CLASSIC_READ | block, key B flag, 6-byte key | 16-byte block |
| `84` | PN532_CLASSIC_WRITE | block, key B flag, 6-byte key, 16-byte block | empty |
| `85` | PN532_PAGE_READ | page `u8` | 4-byte NTAG/Ultralight page |
| `86` | PN532_PAGE_WRITE | page `u8`, 4-byte data | empty |
| `90` | SOFTWARE_SERIAL_INIT | RX pin, TX pin, baud `u32` | empty |
| `91` | SOFTWARE_SERIAL_WRITE | 1–255 data bytes | empty |
| `92` | SOFTWARE_SERIAL_READ | maximum `u8`, timeout ms `u16` | received bytes |
| `93` | SOFTWARE_SERIAL_AVAILABLE | empty | buffered byte count `u16` |
| `94` | SOFTWARE_SERIAL_END | empty | empty |
| `A0` | WIFI_CONNECT | timeout ms `u16`, SSID length, password length, UTF-8 strings | status, IPv4, RSSI `i32`, MAC, channel |
| `A1` | WIFI_DISCONNECT | erase credentials flag | empty |
| `A2` | WIFI_STATUS | empty | status, IPv4, RSSI `i32`, MAC, channel |
| `B0` | ESPNOW_INIT | channel (0 keeps current) | empty |
| `B1` | ESPNOW_ADD_PEER | MAC, channel, encrypt flag, 16-byte LMK | empty |
| `B2` | ESPNOW_REMOVE_PEER | MAC | empty |
| `B3` | ESPNOW_SEND | MAC, 1–240 data bytes | empty |
| `B4` | ESPNOW_RECEIVE | empty | MAC, RSSI, channel, length, data; `BUSY` if empty |
| `B5` | ESPNOW_LOCAL_MAC | empty | 6-byte STA MAC |
| `C0` | TIME_SYNC | UTC offset `i32`, DST offset `i32`, timeout `u16`, server length and ASCII server | Unix time `u64` |
| `C1` | TIME_NOW | empty | Unix time `u64` |

Pin mode values are input `0`, output `1`, input-pullup `2`, and input-pulldown `3`.

星尘板只接受 D2、D3、D5、D6、D9、D10 和 A0-A3（数值 14-17）。其 AVR PWM 分辨率固定为 8 位：D3/D9/D10 的 `PWM_CONFIGURE` 频率必须为 490 Hz，D5/D6 必须为 980 Hz。
星尘板的专用 I²C 接口是 SDA=A4、SCL=A5，不列入通用 GPIO 白名单。其 OLED 使用 411 字常用中文子集与分页命令队列，不支持 `OLED_BITMAP`；WS2812 上限 16 颗；MP3 串口和通用软件串口互斥。

OLED font `0` is ASCII 6×12. Font `1` is the DFRobot U8g2 WenQuanYi 12px GB2312 font. Drawing commands update the in-memory framebuffer; `OLED_SHOW` flushes it to the SSD1306 display. Large bitmaps are divided into horizontal strips by the Python SDK.

The NeoPixel driver controls one active WS2812 strip at a time and uses GRB/800 kHz ordering; its reserved white byte is ignored by the RGB driver. `MP3_INIT` creates a real ESP32 software UART at 9600 baud. Pin names are from the ESP32 viewpoint: RX connects to DFR0534 `T`, TX connects to DFR0534 `R`. The optional BUSY input is high while audio is playing.

The PN532 driver uses the chip's standard I²C address `0x24` on P20/SDA and P19/SCL. Readiness is polled through the PN532 I²C status byte, so IRQ is optional. `PN532_INIT` verifies chip ID `0x32`, configures SAM normal mode, and limits passive-target retries so a missing tag does not block the serial protocol indefinitely. The Python SDK blocks sector-trailer and manufacturer/configuration-page writes by default.

Wi-Fi and ESP-NOW use the ESP32 Arduino core's native radio stack. When Wi-Fi is connected, ESP-NOW must use the access point's channel. SNTP uses `configTime`; cloud HTTP APIs are deliberately implemented in the Python SDK so credentials are not embedded in firmware.

## Recovery rules

- Noise before `A5 5A` is discarded.
- CRC failures discard the current frame and restart SOF search.
- Lengths over 256 discard the current frame.
- A partial frame is discarded after 100 ms without another byte.
- A response is accepted by the SDK only when sequence and command both match.
- Protocol V1 fallback is intentionally not automatic.

## Golden vector

PING request, sequence `0x1234`, payload `abc`:

```text
A5 5A 02 01 34 12 01 03 00 61 62 63 1D FC
```
