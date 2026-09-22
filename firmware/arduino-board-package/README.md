# StarBridge Arduino board package

This development package adds `StarCore V2 (星核板 V2)` and `StarDust (星尘板)` to Arduino IDE and Arduino CLI. It reuses the official `esp32:esp32` and `arduino:avr` cores.

## Requirements

- Arduino CLI 1.0.4 or newer, or a current Arduino IDE 2.x.
- Espressif `esp32:esp32` core 3.3.11.
- Arduino `arduino:avr` core 1.8.8.

## Manual installation

Copy the `hardware` directory into the Arduino sketchbook directory. The resulting layout must be:

```text
<sketchbook>/hardware/starbridge/esp32/boards.txt
<sketchbook>/hardware/starbridge/esp32/platform.txt
<sketchbook>/hardware/starbridge/esp32/variants/starcore_v2/pins_arduino.h
<sketchbook>/hardware/starbridge/avr/boards.txt
<sketchbook>/hardware/starbridge/avr/platform.txt
<sketchbook>/hardware/starbridge/avr/variants/stardust/pins_arduino.h
```

Restart Arduino IDE, then select the required StarBridge board. The FQBNs are:

```text
starbridge:esp32:starcore_v2
starbridge:avr:stardust
```

The package references the vendor cores instead of copying them. StarDust uses the Uno-compatible ATmega328P/16 MHz/Optiboot parameters, but its general-purpose variant pins are D2, D3, D5, D6, D9, D10, and A0-A3. D0/D1 are reserved for the CH340 protocol serial port; the dedicated I2C connector uses SDA=A4 and SCL=A5.
