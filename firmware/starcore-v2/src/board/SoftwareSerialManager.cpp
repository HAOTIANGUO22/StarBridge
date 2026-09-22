#include "SoftwareSerialManager.h"

#include "BoardPins.h"

SoftwareSerialManager::~SoftwareSerialManager() { reset(); }

bool SoftwareSerialManager::begin(
    uint8_t rxPin, uint8_t txPin, uint32_t baudrate) {
  if (!board::canReadDigital(rxPin) || !board::canWriteDigital(txPin) ||
      !EspSoftwareSerial::GpioCapabilities::isValidInputPin(static_cast<int8_t>(rxPin)) ||
      !EspSoftwareSerial::GpioCapabilities::isValidOutputPin(static_cast<int8_t>(txPin)) ||
      rxPin == txPin || baudrate < 300 || baudrate > 230400)
    return false;
  reset();
  serial_ = new SoftwareSerial(static_cast<int8_t>(rxPin), static_cast<int8_t>(txPin));
  if (serial_ == nullptr) return false;
  serial_->begin(baudrate);
  return true;
}

bool SoftwareSerialManager::write(const uint8_t* data, uint8_t length) {
  return serial_ != nullptr && length > 0 &&
         serial_->write(data, length) == length;
}

bool SoftwareSerialManager::read(
    uint8_t* data, uint8_t maximum, uint16_t timeoutMs, uint8_t& length) {
  length = 0;
  if (serial_ == nullptr || maximum == 0 || maximum > 250 || timeoutMs > 5000)
    return false;
  const uint32_t started = millis();
  do {
    while (serial_->available() > 0 && length < maximum) {
      const int value = serial_->read();
      if (value >= 0) data[length++] = static_cast<uint8_t>(value);
    }
    if (length > 0 || timeoutMs == 0) return true;
    delay(1);
  } while (static_cast<uint32_t>(millis() - started) < timeoutMs);
  return true;
}

bool SoftwareSerialManager::available(uint16_t& count) const {
  if (serial_ == nullptr) return false;
  count = static_cast<uint16_t>(serial_->available());
  return true;
}

void SoftwareSerialManager::reset() {
  if (serial_ != nullptr) {
    serial_->end();
    delete serial_;
    serial_ = nullptr;
  }
}
