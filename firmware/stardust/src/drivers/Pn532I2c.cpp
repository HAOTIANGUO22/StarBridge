#include "Pn532I2c.h"

#include <string.h>

namespace {
constexpr uint8_t CMD_GET_FIRMWARE_VERSION = 0x02;
constexpr uint8_t CMD_SAM_CONFIGURATION = 0x14;
constexpr uint8_t CMD_RF_CONFIGURATION = 0x32;
constexpr uint8_t CMD_IN_DATA_EXCHANGE = 0x40;
constexpr uint8_t CMD_IN_LIST_PASSIVE_TARGET = 0x4A;
constexpr uint8_t MIFARE_AUTH_A = 0x60;
constexpr uint8_t MIFARE_AUTH_B = 0x61;
constexpr uint8_t MIFARE_READ = 0x30;
constexpr uint8_t MIFARE_WRITE = 0xA0;
constexpr uint8_t NTAG_WRITE = 0xA2;
constexpr uint8_t ACK[] = {0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00};
}  // namespace

bool Pn532I2c::begin(TwoWire& wire, uint8_t irqPin, uint8_t resetPin) {
  wire_ = &wire;
  irqPin_ = irqPin;
  resetPin_ = resetPin;
  if (irqPin_ != NO_PIN) pinMode(irqPin_, INPUT_PULLUP);
  if (resetPin_ != NO_PIN) {
    pinMode(resetPin_, OUTPUT);
    digitalWrite(resetPin_, LOW);
    delay(1);
    digitalWrite(resetPin_, HIGH);
    delay(10);
  }
  return true;
}

bool Pn532I2c::firmwareVersion(uint32_t& version) {
  uint8_t response[4]{};
  uint8_t length = 0;
  if (!command(CMD_GET_FIRMWARE_VERSION, nullptr, 0, response, length,
               sizeof(response)) || length != sizeof(response)) return false;
  version = (static_cast<uint32_t>(response[0]) << 24) |
            (static_cast<uint32_t>(response[1]) << 16) |
            (static_cast<uint32_t>(response[2]) << 8) | response[3];
  return true;
}

bool Pn532I2c::configureSam() {
  const uint8_t arguments[] = {0x01, 0x14, 0x01};
  uint8_t length = 0;
  return command(CMD_SAM_CONFIGURATION, arguments, sizeof(arguments), nullptr,
                 length, 0) && length == 0;
}

bool Pn532I2c::setPassiveActivationRetries(uint8_t retries) {
  const uint8_t arguments[] = {0x05, 0xFF, 0x01, retries};
  uint8_t length = 0;
  return command(CMD_RF_CONFIGURATION, arguments, sizeof(arguments), nullptr,
                 length, 0) && length == 0;
}

bool Pn532I2c::scan(uint16_t timeoutMs, uint8_t* uid, uint8_t& uidLength) {
  const uint8_t arguments[] = {0x01, 0x00};
  uint8_t response[13]{};
  uint8_t length = 0;
  uidLength = 0;
  if (!command(CMD_IN_LIST_PASSIVE_TARGET, arguments, sizeof(arguments),
               response, length, sizeof(response), timeoutMs)) return false;
  if (length == 0 || response[0] == 0) return true;
  if (length < 6 || response[0] != 1) return false;
  const uint8_t reportedLength = response[5];
  if ((reportedLength != 4 && reportedLength != 7) ||
      static_cast<uint8_t>(6 + reportedLength) > length) return false;
  memcpy(uid, response + 6, reportedLength);
  uidLength = reportedLength;
  return true;
}

bool Pn532I2c::authenticate(const uint8_t* uid, uint8_t uidLength,
                            uint8_t block, bool keyB, const uint8_t* key) {
  if (uidLength != 4 && uidLength != 7) return false;
  uint8_t arguments[13]{};
  arguments[0] = 1;
  arguments[1] = keyB ? MIFARE_AUTH_B : MIFARE_AUTH_A;
  arguments[2] = block;
  memcpy(arguments + 3, key, 6);
  memcpy(arguments + 9, uid + uidLength - 4, 4);
  uint8_t response[1]{};
  uint8_t length = 0;
  return command(CMD_IN_DATA_EXCHANGE, arguments, sizeof(arguments), response,
                 length, sizeof(response)) && length == 1 && response[0] == 0;
}

bool Pn532I2c::readBlock(uint8_t block, uint8_t* data) {
  const uint8_t arguments[] = {1, MIFARE_READ, block};
  uint8_t response[17]{};
  uint8_t length = 0;
  if (!command(CMD_IN_DATA_EXCHANGE, arguments, sizeof(arguments), response,
               length, sizeof(response)) || length != sizeof(response) ||
      response[0] != 0) return false;
  memcpy(data, response + 1, 16);
  return true;
}

bool Pn532I2c::writeBlock(uint8_t block, const uint8_t* data) {
  uint8_t arguments[19] = {1, MIFARE_WRITE, block};
  memcpy(arguments + 3, data, 16);
  uint8_t response[1]{};
  uint8_t length = 0;
  return command(CMD_IN_DATA_EXCHANGE, arguments, sizeof(arguments), response,
                 length, sizeof(response)) && length == 1 && response[0] == 0;
}

bool Pn532I2c::readPage(uint8_t page, uint8_t* data) {
  uint8_t block[16]{};
  if (!readBlock(page, block)) return false;
  memcpy(data, block, 4);
  return true;
}

bool Pn532I2c::writePage(uint8_t page, const uint8_t* data) {
  uint8_t arguments[7] = {1, NTAG_WRITE, page};
  memcpy(arguments + 3, data, 4);
  uint8_t response[1]{};
  uint8_t length = 0;
  return command(CMD_IN_DATA_EXCHANGE, arguments, sizeof(arguments), response,
                 length, sizeof(response)) && length == 1 && response[0] == 0;
}

void Pn532I2c::reset() {
  if (resetPin_ != NO_PIN) {
    digitalWrite(resetPin_, LOW);
    delay(1);
    digitalWrite(resetPin_, HIGH);
    delay(10);
  }
}

bool Pn532I2c::command(
    uint8_t commandByte, const uint8_t* arguments, uint8_t argumentLength,
    uint8_t* response, uint8_t& responseLength, uint8_t responseCapacity,
    uint16_t timeoutMs) {
  responseLength = 0;
  if (!writeFrame(commandByte, arguments, argumentLength)) return false;
  delay(1);
  if (!waitReady(timeoutMs) || !readAck()) return false;
  delay(1);
  if (!waitReady(timeoutMs)) return false;
  return readResponse(commandByte, response, responseLength, responseCapacity);
}

bool Pn532I2c::writeFrame(
    uint8_t commandByte, const uint8_t* arguments, uint8_t argumentLength) {
  if (wire_ == nullptr || argumentLength > 23) return false;
  const uint8_t frameLength = static_cast<uint8_t>(argumentLength + 2);
  uint8_t checksum = static_cast<uint8_t>(HOST_TO_PN532 + commandByte);
  wire_->beginTransmission(ADDRESS);
  wire_->write(static_cast<uint8_t>(0x00));
  wire_->write(static_cast<uint8_t>(0x00));
  wire_->write(static_cast<uint8_t>(0xFF));
  wire_->write(frameLength);
  wire_->write(static_cast<uint8_t>(~frameLength + 1));
  wire_->write(HOST_TO_PN532);
  wire_->write(commandByte);
  for (uint8_t index = 0; index < argumentLength; ++index) {
    wire_->write(arguments[index]);
    checksum = static_cast<uint8_t>(checksum + arguments[index]);
  }
  wire_->write(static_cast<uint8_t>(~checksum + 1));
  wire_->write(static_cast<uint8_t>(0x00));
  return wire_->endTransmission() == 0;
}

bool Pn532I2c::waitReady(uint16_t timeoutMs) {
  const uint32_t started = millis();
  do {
    const uint8_t received = wire_->requestFrom(ADDRESS, static_cast<uint8_t>(1));
    if (received == 1 && wire_->read() == READY) return true;
    delay(5);
  } while (static_cast<uint32_t>(millis() - started) <= timeoutMs);
  return false;
}

bool Pn532I2c::readAck() {
  uint8_t frame[sizeof(ACK)]{};
  return readI2c(frame, sizeof(frame)) && memcmp(frame, ACK, sizeof(ACK)) == 0;
}

bool Pn532I2c::readResponse(
    uint8_t commandByte, uint8_t* response, uint8_t& responseLength,
    uint8_t responseCapacity) {
  uint8_t frame[31]{};
  const uint8_t bytesToRead = static_cast<uint8_t>(responseCapacity + 9);
  if (!readI2c(frame, bytesToRead)) return false;
  if (frame[0] != 0x00 || frame[1] != 0x00 || frame[2] != 0xFF) return false;
  const uint8_t frameLength = frame[3];
  if (frameLength < 2 || frameLength > 23 ||
      static_cast<uint8_t>(frameLength + frame[4]) != 0) return false;
  const uint8_t payloadLength = static_cast<uint8_t>(frameLength - 2);
  if (payloadLength > responseCapacity || frame[5] != PN532_TO_HOST ||
      frame[6] != static_cast<uint8_t>(commandByte + 1)) return false;
  uint8_t checksum = 0;
  for (uint8_t index = 5; index < static_cast<uint8_t>(5 + frameLength); ++index)
    checksum = static_cast<uint8_t>(checksum + frame[index]);
  if (static_cast<uint8_t>(checksum + frame[5 + frameLength]) != 0) return false;
  if (payloadLength > 0) memcpy(response, frame + 7, payloadLength);
  responseLength = payloadLength;
  return true;
}

bool Pn532I2c::readI2c(uint8_t* data, uint8_t length) {
  if (wire_ == nullptr || length > 31) return false;
  const uint8_t requested = static_cast<uint8_t>(length + 1);
  const uint8_t received = wire_->requestFrom(ADDRESS, requested);
  if (received != requested || wire_->read() != READY) return false;
  for (uint8_t index = 0; index < length; ++index) {
    const int value = wire_->read();
    if (value < 0) return false;
    data[index] = static_cast<uint8_t>(value);
  }
  return true;
}
