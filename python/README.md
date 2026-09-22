# StarBridge Python SDK 4.5.0

Install the public distribution from PyPI:

```bash
python -m pip install starbridge-hardware
```

The PyPI distribution is named `starbridge-hardware`; the Python import package remains `starbridge`.

```python
from starbridge import Board, BoardType, Pin, PinMode

with Board.begin(BoardType.STARCORE_V2) as board:
    print(board.info())
    board.pin_mode(Pin.P0, PinMode.OUTPUT)
    board.digital_write(Pin.P0, True)

    print(board.dht11(Pin.P1).read())
    print(board.ultrasonic(Pin.P6, Pin.P7).read_cm())

    nfc = board.pn532().begin()
    print("PN532 UID:", nfc.scan())
```

The SDK communicates with protocol-v2 firmware. It does not silently fall back to the legacy protocol.

`Board.begin()` detects the serial port and reuses compatible firmware. On Windows, the official wheel contains precompiled StarCore V2 and StarDust firmware plus esptool and avrdude, so first-time provisioning works without Arduino IDE, Arduino CLI, installed board cores, or firmware source. Pass `port="COM7"` to override discovery or `force_flash=True` to request a new upload.

The wheel includes only the public Python SDK, precompiled flash images, their integrity manifests, and the Windows x86-64 flashing runtimes. Firmware production source remains in the repository's `firmware/` tree and is not copied into the wheel.

StarDust users select `BoardType.STARDUST` and use `StardustPin` for D2, D3, D5, D6, D9, D10, and A0-A3. See `docs/stardust-pinout.md` for its fixed AVR PWM frequencies and limitations.

Version 4.5.0 adds native ESP32 Wi-Fi, ESP-NOW, software serial and SNTP support, plus dependency-free host-side clients for time, weather, speech transcription and OpenAI-compatible chat APIs. Version 4.4.1 introduced generic PN532 NFC over I2C.
