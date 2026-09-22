#pragma once

#include <Arduino.h>
#include <SoftwareSerial.h>

class Dfr0534Manager {
 public:
  ~Dfr0534Manager();
  bool begin(uint8_t rxPin, uint8_t txPin, int8_t busyPin);
  bool playTrack(uint16_t track);
  bool play();
  bool pause();
  bool stop();
  bool next();
  bool previous();
  bool setVolume(uint8_t volume);
  bool readStatus(uint8_t& status, uint32_t timeoutMs = 150);
  bool isBusy(bool& busy) const;
  void reset();

 private:
  SoftwareSerial* serial_ = nullptr;
  int8_t busyPin_ = -1;
  bool send(uint8_t command, const uint8_t* data = nullptr, uint8_t length = 0);
};
