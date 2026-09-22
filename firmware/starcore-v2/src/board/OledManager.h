#pragma once

#include <Arduino.h>
#include <U8g2lib.h>

class OledManager {
 public:
  bool begin(uint8_t address, bool rotate180);
  bool clear(bool white);
  bool show();
  bool text(uint8_t x, uint8_t baseline, uint8_t font, const uint8_t* utf8, uint16_t length);
  bool pixel(uint8_t x, uint8_t y, bool white);
  bool line(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1, bool white);
  bool rect(uint8_t x, uint8_t y, uint8_t width, uint8_t height, bool filled, bool white);
  bool bitmap(uint8_t x, uint8_t y, uint8_t width, uint8_t height,
              const uint8_t* data, uint16_t length);
  void reset();
  bool initialized() const { return initialized_; }

 private:
  U8G2_SSD1306_128X64_NONAME_F_HW_I2C display_{U8G2_R0, U8X8_PIN_NONE};
  bool initialized_ = false;
};

