#include "PwmManager.h"

#include "BoardPins.h"
#include <esp_arduino_version.h>

PwmManager::Slot* PwmManager::find(uint8_t pin) {
  for (auto& slot : slots_) {
    if (slot.active && slot.pin == pin) return &slot;
  }
  return nullptr;
}

PwmManager::Slot* PwmManager::allocate(uint8_t pin) {
  if (auto* existing = find(pin)) return existing;
  for (size_t index = 0; index < SLOT_COUNT; ++index) {
    if (!slots_[index].active) {
      slots_[index].pin = pin;
      slots_[index].channel = static_cast<uint8_t>(index);
      return &slots_[index];
    }
  }
  return nullptr;
}

bool PwmManager::configure(uint8_t pin, uint32_t frequency, uint8_t resolution) {
  if (!board::canPwm(pin) || frequency == 0 || frequency > 40000000 ||
      resolution == 0 || resolution > 20) return false;
  Slot* slot = allocate(pin);
  if (!slot) return false;
  if (slot->active) stop(pin, false);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  if (!ledcAttachChannel(pin, frequency, resolution, slot->channel)) return false;
#else
  if (ledcSetup(slot->channel, frequency, resolution) == 0) return false;
  ledcAttachPin(pin, slot->channel);
#endif
  slot->active = true;
  slot->frequency = frequency;
  slot->resolution = resolution;
  return true;
}

bool PwmManager::write(uint8_t pin, uint32_t duty) {
  Slot* slot = find(pin);
  if (!slot) return false;
  const uint32_t maximum = slot->resolution == 32 ? 0xFFFFFFFFUL : ((1UL << slot->resolution) - 1UL);
  if (duty > maximum) return false;
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  return ledcWrite(pin, duty);
#else
  ledcWrite(slot->channel, duty);
  return true;
#endif
}

bool PwmManager::stop(uint8_t pin, bool idleHigh) {
  Slot* slot = find(pin);
  if (!slot) return false;
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcDetach(pin);
#else
  ledcDetachPin(pin);
#endif
  pinMode(pin, OUTPUT);
  digitalWrite(pin, idleHigh ? HIGH : LOW);
  // Keep the slot/channel identity stable so a subsequent configure call
  // cannot accidentally reuse channel zero and collide with another pin.
  slot->active = false;
  slot->frequency = 0;
  slot->resolution = 0;
  return true;
}

void PwmManager::reset() {
  for (auto& slot : slots_) {
    if (slot.active) stop(slot.pin, false);
  }
}
