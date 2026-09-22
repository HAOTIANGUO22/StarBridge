#include "PwmManager.h"

#include "BoardPins.h"

uint8_t PwmManager::pinMask(uint8_t pin) {
  switch (pin) {
    case 3: return 1 << 0;
    case 5: return 1 << 1;
    case 6: return 1 << 2;
    case 9: return 1 << 3;
    case 10: return 1 << 4;
    default: return 0;
  }
}

bool PwmManager::configure(uint8_t pin, uint32_t frequency, uint8_t resolution) {
  const uint8_t mask = pinMask(pin);
  if (mask == 0 || resolution != 8 || frequency != board::pwmFrequency(pin)) return false;
  pinMode(pin, OUTPUT);
  analogWrite(pin, 0);
  activePins_ |= mask;
  return true;
}

bool PwmManager::write(uint8_t pin, uint32_t duty) {
  const uint8_t mask = pinMask(pin);
  if (mask == 0 || (activePins_ & mask) == 0 || duty > 255) return false;
  analogWrite(pin, static_cast<uint8_t>(duty));
  return true;
}

bool PwmManager::stop(uint8_t pin, bool idleHigh) {
  const uint8_t mask = pinMask(pin);
  if (mask == 0 || (activePins_ & mask) == 0) return false;
  analogWrite(pin, 0);
  pinMode(pin, OUTPUT);
  digitalWrite(pin, idleHigh ? HIGH : LOW);
  activePins_ &= static_cast<uint8_t>(~mask);
  return true;
}

void PwmManager::reset() {
  const uint8_t pins[] = {3, 5, 6, 9, 10};
  for (uint8_t index = 0; index < sizeof(pins); ++index) {
    const uint8_t mask = pinMask(pins[index]);
    if (activePins_ & mask) stop(pins[index], false);
  }
  activePins_ = 0;
}
