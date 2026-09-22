#pragma once

#include <Arduino.h>

#include "CommandDispatcher.h"

class FirmwareApp {
 public:
  explicit FirmwareApp(Stream& stream) : stream_(stream) {}
  void begin(uint32_t baud);
  void poll();

 private:
  Stream& stream_;
  protocol::Decoder decoder_;
  CommandDispatcher dispatcher_;
  uint8_t output_[2 + protocol::MAX_BODY_SIZE]{};
};

