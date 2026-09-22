#include "Pn532Manager.h"

#include <Wire.h>

#include "BoardPins.h"

namespace {
constexpr uint8_t NO_PIN = 0xFF;
constexpr uint8_t PN532_CHIP_ID = 0x32;
}  // namespace

bool Pn532Manager::begin(
    uint8_t irqPin, uint8_t resetPin, uint32_t& firmwareVersionValue) {
  if (irqPin != NO_PIN && !board::canReadDigital(irqPin)) return false;
  if (resetPin != NO_PIN && !board::canWriteDigital(resetPin)) return false;
  if (initialized_ && (irqPin != irqPin_ || resetPin != resetPin_)) return false;

  irqPin_ = irqPin;
  resetPin_ = resetPin;
  Wire.begin(board::PIN_I2C_SDA, board::PIN_I2C_SCL);
  if (!device_.begin(Wire, irqPin_, resetPin_)) return false;
  // SAMConfiguration is also the documented I2C wake-up command.
  if (!device_.configureSam()) return false;
  if (!device_.firmwareVersion(firmwareVersionValue)) return false;
  if (static_cast<uint8_t>(firmwareVersionValue >> 24) != PN532_CHIP_ID)
    return false;
  if (!device_.setPassiveActivationRetries(0x01)) return false;
  initialized_ = true;
  uidLength_ = 0;
  return true;
}

bool Pn532Manager::scan(uint16_t timeoutMs, uint8_t* uid, uint8_t& uidLength) {
  uidLength = 0;
  if (!initialized_ || timeoutMs == 0 || timeoutMs > 800) return false;
  if (!device_.scan(timeoutMs, uid_, uidLength_)) {
    uidLength_ = 0;
    return false;
  }
  if (uidLength_ == 0) return true;
  memcpy(uid, uid_, uidLength_);
  uidLength = uidLength_;
  return true;
}

bool Pn532Manager::firmwareVersion(uint32_t& firmwareVersionValue) {
  if (!initialized_ || !device_.firmwareVersion(firmwareVersionValue)) return false;
  return static_cast<uint8_t>(firmwareVersionValue >> 24) == PN532_CHIP_ID;
}

bool Pn532Manager::selectTag(uint16_t timeoutMs) {
  uint8_t ignored[7]{};
  uint8_t length = 0;
  return scan(timeoutMs, ignored, length) && length > 0;
}

bool Pn532Manager::readClassic(
    uint8_t block, bool keyB, const uint8_t* key, uint8_t* data) {
  return selectTag() && device_.authenticate(uid_, uidLength_, block, keyB, key) &&
         device_.readBlock(block, data);
}

bool Pn532Manager::writeClassic(
    uint8_t block, bool keyB, const uint8_t* key, const uint8_t* data) {
  return selectTag() && device_.authenticate(uid_, uidLength_, block, keyB, key) &&
         device_.writeBlock(block, data);
}

bool Pn532Manager::readPage(uint8_t page, uint8_t* data) {
  return selectTag() && device_.readPage(page, data);
}

bool Pn532Manager::writePage(uint8_t page, const uint8_t* data) {
  return selectTag() && device_.writePage(page, data);
}

void Pn532Manager::reset() {
  if (initialized_) device_.reset();
  initialized_ = false;
  uidLength_ = 0;
}
