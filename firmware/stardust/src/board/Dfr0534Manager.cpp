#include "Dfr0534Manager.h"

#include "BoardPins.h"

Dfr0534Manager::~Dfr0534Manager() { reset(); }

bool Dfr0534Manager::begin(uint8_t rxPin, uint8_t txPin, int8_t busyPin) {
  if (!board::canUseDigital(rxPin) || !board::canUseDigital(txPin) ||
      rxPin == txPin ||
      (busyPin >= 0 && !board::canUseDigital(static_cast<uint8_t>(busyPin))))
    return false;
  reset();
  serial_ = new SoftwareSerial(rxPin, txPin);
  if (serial_ == nullptr) return false;
  serial_->begin(9600);
  serial_->listen();
  busyPin_ = busyPin;
  if (busyPin_ >= 0) pinMode(busyPin_, INPUT);
  return true;
}

bool Dfr0534Manager::send(
    uint8_t command, const uint8_t* data, uint8_t length) {
  if (serial_ == nullptr || length > 8) return false;
  serial_->listen();
  uint8_t frame[12] = {0xAA, command, length};
  uint8_t checksum = static_cast<uint8_t>(0xAA + command + length);
  for (uint8_t index = 0; index < length; ++index) {
    frame[3 + index] = data[index];
    checksum = static_cast<uint8_t>(checksum + data[index]);
  }
  frame[3 + length] = checksum;
  return serial_->write(frame, static_cast<size_t>(length + 4)) == length + 4;
}

bool Dfr0534Manager::playTrack(uint16_t track) {
  if (track == 0) return false;
  const uint8_t data[] = {
      static_cast<uint8_t>(track >> 8), static_cast<uint8_t>(track)};
  return send(0x07, data, 2);
}

bool Dfr0534Manager::play() { return send(0x02); }
bool Dfr0534Manager::pause() { return send(0x03); }
bool Dfr0534Manager::stop() { return send(0x04); }
bool Dfr0534Manager::previous() { return send(0x05); }
bool Dfr0534Manager::next() { return send(0x06); }

bool Dfr0534Manager::setVolume(uint8_t volume) {
  return volume <= 30 && send(0x13, &volume, 1);
}

bool Dfr0534Manager::readStatus(uint8_t& status, uint32_t timeoutMs) {
  if (serial_ == nullptr) return false;
  serial_->listen();
  while (serial_->available()) serial_->read();
  if (!send(0x01)) return false;
  const uint32_t started = millis();
  uint8_t frame[5]{};
  uint8_t received = 0;
  while (millis() - started < timeoutMs) {
    while (serial_->available() && received < sizeof(frame)) {
      const uint8_t value = static_cast<uint8_t>(serial_->read());
      if (received == 0 && value != 0xAA) continue;
      frame[received++] = value;
    }
    if (received == sizeof(frame)) {
      const uint8_t checksum =
          static_cast<uint8_t>(frame[0] + frame[1] + frame[2] + frame[3]);
      if (frame[1] == 0x01 && frame[2] == 0x01 && frame[4] == checksum) {
        status = frame[3];
        return true;
      }
      received = 0;
    }
    delay(1);
  }
  return false;
}

bool Dfr0534Manager::isBusy(bool& busy) const {
  if (busyPin_ < 0) return false;
  busy = digitalRead(busyPin_) == HIGH;
  return true;
}

void Dfr0534Manager::reset() {
  if (serial_ != nullptr) {
    serial_->end();
    delete serial_;
    serial_ = nullptr;
  }
  busyPin_ = -1;
}
