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

Pin mode values are input `0`, output `1`, input-pullup `2`, and input-pulldown `3`.

OLED font `0` is ASCII 6×12. Font `1` is the DFRobot U8g2 WenQuanYi 12px GB2312 font. Drawing commands update the in-memory framebuffer; `OLED_SHOW` flushes it to the SSD1306 display. Large bitmaps are divided into horizontal strips by the Python SDK.

The NeoPixel driver controls one active WS2812 strip at a time and uses GRB/800 kHz ordering; its reserved white byte is ignored by the RGB driver. `MP3_INIT` creates a real ESP32 software UART at 9600 baud. Pin names are from the ESP32 viewpoint: RX connects to DFR0534 `T`, TX connects to DFR0534 `R`. The optional BUSY input is high while audio is playing.

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
