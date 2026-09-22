#pragma once

#include <Arduino.h>
#include <Wire.h>

// Minimal PN532 I2C driver for StarCore V2. Only protocol-v2 operations are
// implemented, so the firmware does not need a full third-party library tree.
class Pn532I2c {
 public:
  bool begin(TwoWire& wire, uint8_t irqPin, uint8_t resetPin);
  bool firmwareVersion(uint32_t& version);
  bool configureSam();
  bool setPassiveActivationRetries(uint8_t retries);
  bool scan(uint16_t timeoutMs, uint8_t* uid, uint8_t& uidLength);
  bool authenticate(const uint8_t* uid, uint8_t uidLength, uint8_t block,
                    bool keyB, const uint8_t* key);
  bool readBlock(uint8_t block, uint8_t* data);
  bool writeBlock(uint8_t block, const uint8_t* data);
  bool readPage(uint8_t page, uint8_t* data);
  bool writePage(uint8_t page, const uint8_t* data);
  void reset();

 private:
  static constexpr uint8_t ADDRESS = 0x24;
  static constexpr uint8_t NO_PIN = 0xFF;
  static constexpr uint8_t HOST_TO_PN532 = 0xD4;
  static constexpr uint8_t PN532_TO_HOST = 0xD5;
  static constexpr uint8_t READY = 0x01;

  bool command(uint8_t command, const uint8_t* arguments, uint8_t argumentLength,
               uint8_t* response, uint8_t& responseLength, uint8_t responseCapacity,
               uint16_t timeoutMs = 1000);
  bool writeFrame(uint8_t command, const uint8_t* arguments, uint8_t argumentLength);
  bool waitReady(uint16_t timeoutMs);
  bool readAck();
  bool readResponse(uint8_t command, uint8_t* response, uint8_t& responseLength,
                    uint8_t responseCapacity);
  bool readI2c(uint8_t* data, uint8_t length);

  TwoWire* wire_ = nullptr;
  uint8_t irqPin_ = NO_PIN;
  uint8_t resetPin_ = NO_PIN;
};
