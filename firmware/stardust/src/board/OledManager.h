#pragma once

#include <Arduino.h>
#include <U8g2lib.h>

class OledManager {
 public:
  bool begin(uint8_t address, bool rotate180);
  bool clear(bool white);
  bool show();
  bool text(uint8_t x, uint8_t baseline, uint8_t font,
            const uint8_t* utf8, uint16_t length);
  bool pixel(uint8_t x, uint8_t y, bool white);
  bool line(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1, bool white);
  bool rect(uint8_t x, uint8_t y, uint8_t width, uint8_t height,
            bool filled, bool white);
  void reset();

 private:
  enum Operation : uint8_t { Text = 1, Pixel = 2, Line = 3, Rect = 4 };
  static constexpr uint16_t QUEUE_CAPACITY = 256;

  U8G2_SSD1306_128X64_NONAME_1_HW_I2C display_{U8G2_R0, U8X8_PIN_NONE};
  uint8_t queue_[QUEUE_CAPACITY]{};
  uint16_t used_ = 0;
  bool initialized_ = false;

  bool append(const uint8_t* data, uint16_t length);
  void replay();
};
