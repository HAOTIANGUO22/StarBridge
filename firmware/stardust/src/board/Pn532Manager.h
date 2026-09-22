#pragma once

#include <Arduino.h>

#include "../drivers/Pn532I2c.h"

class Pn532Manager {
 public:
  bool begin(uint8_t irqPin, uint8_t resetPin, uint32_t& firmwareVersion);
  bool firmwareVersion(uint32_t& firmwareVersion);
  bool scan(uint16_t timeoutMs, uint8_t* uid, uint8_t& uidLength);
  bool readClassic(uint8_t block, bool keyB, const uint8_t* key, uint8_t* data);
  bool writeClassic(uint8_t block, bool keyB, const uint8_t* key,
                    const uint8_t* data);
  bool readPage(uint8_t page, uint8_t* data);
  bool writePage(uint8_t page, const uint8_t* data);
  void reset();

 private:
  bool selectTag(uint16_t timeoutMs = 250);
  Pn532I2c device_;
  uint8_t irqPin_ = 0xFF;
  uint8_t resetPin_ = 0xFF;
  uint8_t uid_[7]{};
  uint8_t uidLength_ = 0;
  bool initialized_ = false;
};
