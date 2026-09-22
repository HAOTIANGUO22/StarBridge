#pragma once

#include <Adafruit_NeoPixel.h>

class NeoPixelManager {
 public:
  ~NeoPixelManager();
  bool begin(uint8_t pin, uint16_t count, uint8_t brightness);
  bool set(uint16_t index, uint8_t red, uint8_t green, uint8_t blue, uint8_t white);
  bool fill(uint16_t first, uint16_t count, uint8_t red, uint8_t green, uint8_t blue,
            uint8_t white);
  bool show();
  bool clear();
  void reset();

 private:
  Adafruit_NeoPixel* strip_ = nullptr;
};
