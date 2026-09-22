#include "OledManager.h"

#include <Wire.h>

#include "BoardPins.h"

bool OledManager::begin(uint8_t address, bool rotate180) {
  if (address < 0x08 || address > 0x77) return false;
  Wire.begin(board::PIN_I2C_SDA, board::PIN_I2C_SCL);
  Wire.beginTransmission(address);
  if (Wire.endTransmission() != 0) return false;
  display_.setI2CAddress(static_cast<uint8_t>(address << 1));
  display_.setDisplayRotation(rotate180 ? U8G2_R2 : U8G2_R0);
  display_.begin();
  display_.setFontMode(1);
  display_.setDrawColor(1);
  display_.clearBuffer();
  display_.sendBuffer();
  initialized_ = true;
  return true;
}

bool OledManager::clear(bool white) {
  if (!initialized_) return false;
  if (white) {
    display_.setDrawColor(1);
    display_.drawBox(0, 0, 128, 64);
  } else {
    display_.clearBuffer();
  }
  return true;
}

bool OledManager::show() {
  if (!initialized_) return false;
  display_.sendBuffer();
  return true;
}

bool OledManager::text(
    uint8_t x, uint8_t baseline, uint8_t font, const uint8_t* utf8, uint16_t length) {
  if (!initialized_ || x >= 128 || baseline >= 64 || length == 0 || length > 250) return false;
  char textBuffer[251];
  memcpy(textBuffer, utf8, length);
  textBuffer[length] = '\0';
  switch (font) {
    case 0:
      display_.setFont(u8g2_font_6x12_tf);
      break;
    case 1:
      // Full Simplified Chinese GB2312 font provided by DFRobot's U8g2 fork.
      display_.setFont(u8g2_font_wqy12_t_gb2312);
      break;
    default:
      return false;
  }
  display_.setDrawColor(1);
  display_.drawUTF8(x, baseline, textBuffer);
  return true;
}

bool OledManager::pixel(uint8_t x, uint8_t y, bool white) {
  if (!initialized_ || x >= 128 || y >= 64) return false;
  display_.setDrawColor(white ? 1 : 0);
  display_.drawPixel(x, y);
  return true;
}

bool OledManager::line(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1, bool white) {
  if (!initialized_ || x0 >= 128 || x1 >= 128 || y0 >= 64 || y1 >= 64) return false;
  display_.setDrawColor(white ? 1 : 0);
  display_.drawLine(x0, y0, x1, y1);
  return true;
}

bool OledManager::rect(
    uint8_t x, uint8_t y, uint8_t width, uint8_t height, bool filled, bool white) {
  if (!initialized_ || x >= 128 || y >= 64 || width == 0 || height == 0 ||
      static_cast<uint16_t>(x) + width > 128 || static_cast<uint16_t>(y) + height > 64)
    return false;
  display_.setDrawColor(white ? 1 : 0);
  if (filled) display_.drawBox(x, y, width, height);
  else display_.drawFrame(x, y, width, height);
  return true;
}

bool OledManager::bitmap(
    uint8_t x, uint8_t y, uint8_t width, uint8_t height,
    const uint8_t* data, uint16_t length) {
  const uint16_t expected = static_cast<uint16_t>((width + 7) / 8) * height;
  if (!initialized_ || x >= 128 || y >= 64 || width == 0 || height == 0 ||
      static_cast<uint16_t>(x) + width > 128 || static_cast<uint16_t>(y) + height > 64 ||
      length != expected) return false;
  display_.setDrawColor(1);
  display_.drawXBM(x, y, width, height, data);
  return true;
}

void OledManager::reset() {
  if (!initialized_) return;
  display_.clearBuffer();
  display_.sendBuffer();
}
