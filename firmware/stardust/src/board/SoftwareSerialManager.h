#pragma once

#include <Arduino.h>
#include <SoftwareSerial.h>

class SoftwareSerialManager {
 public:
  ~SoftwareSerialManager();
  bool begin(uint8_t rxPin, uint8_t txPin, uint32_t baudrate);
  bool write(const uint8_t* data, uint8_t length);
  bool read(uint8_t* data, uint8_t maximum, uint16_t timeoutMs, uint8_t& length);
  bool available(uint16_t& count);
  void reset();

 private:
  SoftwareSerial* serial_ = nullptr;
};
