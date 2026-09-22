#pragma once

#include <Arduino.h>

class PwmManager {
 public:
  bool configure(uint8_t pin, uint32_t frequency, uint8_t resolution);
  bool write(uint8_t pin, uint32_t duty);
  bool stop(uint8_t pin, bool idleHigh);
  void reset();

 private:
  uint8_t activePins_ = 0;
  static uint8_t pinMask(uint8_t pin);
};
