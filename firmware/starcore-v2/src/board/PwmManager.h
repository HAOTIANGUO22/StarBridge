#pragma once

#include <Arduino.h>

class PwmManager {
 public:
  bool configure(uint8_t pin, uint32_t frequency, uint8_t resolution);
  bool write(uint8_t pin, uint32_t duty);
  bool stop(uint8_t pin, bool idleHigh);
  void reset();

 private:
  struct Slot {
    bool active = false;
    uint8_t pin = 0;
    uint8_t resolution = 0;
    uint8_t channel = 0;
    uint32_t frequency = 0;
  };

  static constexpr size_t SLOT_COUNT = 16;
  Slot slots_[SLOT_COUNT]{};
  Slot* find(uint8_t pin);
  Slot* allocate(uint8_t pin);
};

