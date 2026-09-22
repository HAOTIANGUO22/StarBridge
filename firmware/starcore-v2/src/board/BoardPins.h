#pragma once

#include <Arduino.h>

namespace board {

// 星核板 V2 connector map from the company schematic.
constexpr uint8_t BOARD_ID_STARCORE_V2 = 1;
constexpr uint8_t PIN_MICROPHONE = 38;
constexpr uint8_t PIN_LIGHT = 39;
constexpr uint8_t PIN_BUTTON_A = 0;
constexpr uint8_t PIN_BUTTON_B = 2;
constexpr uint8_t PIN_BUZZER = 16;
constexpr uint8_t PIN_ONBOARD_PIXELS = 17;
constexpr uint8_t PIN_I2C_SCL = 22;
constexpr uint8_t PIN_I2C_SDA = 23;

inline bool contains(const uint8_t* values, size_t length, uint8_t pin) {
  for (size_t index = 0; index < length; ++index) {
    if (values[index] == pin) return true;
  }
  return false;
}

constexpr uint8_t DIGITAL_INPUT_PINS[] = {
    33, 32, 35, 34, 39, 0, 16, 17, 26, 25, 36, 2,
    18, 19, 21, 5, 22, 23, 27, 14, 12, 13, 15, 4};
constexpr uint8_t DIGITAL_OUTPUT_PINS[] = {
    33, 32, 0, 16, 17, 26, 25, 2, 18, 19,
    21, 5, 22, 23, 27, 14, 12, 13, 15, 4};
constexpr uint8_t ANALOG_INPUT_PINS[] = {
    36, 38, 33, 39, 34, 35, 32, 25, 26, 27, 14, 12, 13, 15, 2, 4};
constexpr uint8_t DAC_PINS[] = {25, 26};
constexpr uint8_t PWM_PINS[] = {
    33, 32, 0, 16, 17, 26, 25, 2, 18, 19,
    21, 5, 22, 23, 27, 14, 12, 13, 15, 4};

inline bool canReadDigital(uint8_t pin) {
  return contains(DIGITAL_INPUT_PINS, sizeof(DIGITAL_INPUT_PINS), pin);
}
inline bool canWriteDigital(uint8_t pin) {
  return contains(DIGITAL_OUTPUT_PINS, sizeof(DIGITAL_OUTPUT_PINS), pin);
}
inline bool canReadAnalog(uint8_t pin) {
  return contains(ANALOG_INPUT_PINS, sizeof(ANALOG_INPUT_PINS), pin);
}
inline bool canPwm(uint8_t pin) {
  return contains(PWM_PINS, sizeof(PWM_PINS), pin);
}
inline bool canWriteAnalog(uint8_t pin) {
  return contains(DAC_PINS, sizeof(DAC_PINS), pin);
}

}  // namespace board
