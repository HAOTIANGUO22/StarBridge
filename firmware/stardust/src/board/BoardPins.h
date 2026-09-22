#pragma once

#include <Arduino.h>

namespace board {

constexpr uint8_t BOARD_ID_STARDUST = 3;
constexpr uint8_t PIN_I2C_SDA = 18;  // Dedicated A4/SDA connector.
constexpr uint8_t PIN_I2C_SCL = 19;  // Dedicated A5/SCL connector.

constexpr uint8_t DIGITAL_PINS[] = {2, 3, 5, 6, 9, 10, A0, A1, A2, A3};
constexpr uint8_t ANALOG_INPUT_PINS[] = {A0, A1, A2, A3};
constexpr uint8_t PWM_PINS[] = {3, 5, 6, 9, 10};

inline bool contains(const uint8_t* values, size_t length, uint8_t pin) {
  for (size_t index = 0; index < length; ++index) {
    if (values[index] == pin) return true;
  }
  return false;
}

inline bool canUseDigital(uint8_t pin) {
  return contains(DIGITAL_PINS, sizeof(DIGITAL_PINS), pin);
}

inline bool canReadAnalog(uint8_t pin) {
  return contains(ANALOG_INPUT_PINS, sizeof(ANALOG_INPUT_PINS), pin);
}

inline bool canPwm(uint8_t pin) {
  return contains(PWM_PINS, sizeof(PWM_PINS), pin);
}

inline uint16_t pwmFrequency(uint8_t pin) {
  return pin == 5 || pin == 6 ? 980 : 490;
}

}  // namespace board
