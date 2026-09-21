# StarBridge Python SDK 4.4

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
```

The SDK communicates with protocol-v2 firmware. It does not silently fall back to the legacy protocol.

`Board.begin()` detects the serial port and reuses compatible firmware. On Windows, the official wheel contains precompiled StarCore V2 firmware and esptool, so first-time provisioning works without Arduino IDE, Arduino CLI, an installed ESP32 core, or firmware source. Pass `port="COM7"` to override discovery or `force_flash=True` to request a new upload.

The wheel includes only the public Python SDK, precompiled flash images, their integrity manifest, and the Windows x86-64 esptool runtime. Firmware production source is maintained separately and is not distributed in this repository or wheel.

Version 4.4 recognizes both CP210x and CH9102 USB-to-serial bridges. First-time flashing displays the StarBridge, SDK and firmware versions plus a progress bar. Hardware command failures include Chinese troubleshooting guidance while retaining the numeric command and status for diagnostics.
