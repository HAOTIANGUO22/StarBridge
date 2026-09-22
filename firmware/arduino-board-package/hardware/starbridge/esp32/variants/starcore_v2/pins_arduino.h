#ifndef Pins_Arduino_h
#define Pins_Arduino_h

#include <stdint.h>

// USB-to-UART bridge.
static const uint8_t TX = 1;
static const uint8_t RX = 3;

// StarCore V2 I2C bus: P20/SDA and P19/SCL.
static const uint8_t SDA = 23;
static const uint8_t SCL = 22;

// VSPI-compatible aliases on exposed StarCore pins.
static const uint8_t SS = 5;
static const uint8_t MOSI = 23;
static const uint8_t MISO = 19;
static const uint8_t SCK = 18;

// P connectors. P12, P17 and P18 are not exposed by the board.
static const uint8_t P0 = 33;
static const uint8_t P1 = 32;
static const uint8_t P2 = 35;
static const uint8_t P3 = 34;
static const uint8_t P4 = 39;
static const uint8_t P5 = 0;
static const uint8_t P6 = 16;
static const uint8_t P7 = 17;
static const uint8_t P8 = 26;
static const uint8_t P9 = 25;
static const uint8_t P10 = 36;
static const uint8_t P11 = 2;
static const uint8_t P13 = 18;
static const uint8_t P14 = 19;
static const uint8_t P15 = 21;
static const uint8_t P16 = 5;
static const uint8_t P19 = 22;
static const uint8_t P20 = 23;

// Lettered connectors (each has a 510-ohm series resistor on StarCore V2).
static const uint8_t PIN_P = 27;
static const uint8_t PIN_Y = 14;
static const uint8_t PIN_T = 12;
static const uint8_t PIN_H = 13;
static const uint8_t PIN_O = 15;
static const uint8_t PIN_N = 4;

// Onboard resources.
static const uint8_t MICROPHONE = 38;
static const uint8_t LIGHT_SENSOR = P4;
static const uint8_t BUTTON_A = P5;
static const uint8_t BUTTON_B = P11;
static const uint8_t BUZZER = P6;
static const uint8_t ONBOARD_PIXELS = P7;
static const uint8_t ONBOARD_PIXEL_COUNT = 3;

// Arduino-compatible analog, touch and DAC aliases.
static const uint8_t A0 = 36;
static const uint8_t A3 = 39;
static const uint8_t A4 = 32;
static const uint8_t A5 = 33;
static const uint8_t A6 = 34;
static const uint8_t A7 = 35;
static const uint8_t A10 = 4;
static const uint8_t A11 = 0;
static const uint8_t A12 = 2;
static const uint8_t A13 = 15;
static const uint8_t A14 = 13;
static const uint8_t A15 = 12;
static const uint8_t A16 = 14;
static const uint8_t A17 = 27;
static const uint8_t A18 = 25;
static const uint8_t A19 = 26;

static const uint8_t T0 = 4;
static const uint8_t T1 = 0;
static const uint8_t T2 = 2;
static const uint8_t T3 = 15;
static const uint8_t T4 = 13;
static const uint8_t T5 = 12;
static const uint8_t T6 = 14;
static const uint8_t T7 = 27;
static const uint8_t T8 = 33;
static const uint8_t T9 = 32;

static const uint8_t DAC1 = 25;
static const uint8_t DAC2 = 26;

#define RGB_BUILTIN ONBOARD_PIXELS
#define RGB_BRIGHTNESS 64

#endif  // Pins_Arduino_h
