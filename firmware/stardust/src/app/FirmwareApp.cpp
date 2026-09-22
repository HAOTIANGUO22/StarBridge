#include "FirmwareApp.h"

void FirmwareApp::begin(uint32_t baud) {
  if (&stream_ == &Serial) Serial.begin(baud);
  dispatcher_.reset();
}

void FirmwareApp::poll() {
  const uint32_t now = millis();
  decoder_.tick(now);
  while (stream_.available() > 0) {
    const int value = stream_.read();
    if (value < 0) break;
    if (decoder_.feed(static_cast<uint8_t>(value), now, frame_)) {
      dispatcher_.dispatch(frame_);
      protocol::write(stream_, frame_);
    }
  }
}
