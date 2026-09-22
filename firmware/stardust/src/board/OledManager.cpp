#include "OledManager.h"

#include <Wire.h>
#include <string.h>

bool OledManager::append(const uint8_t* data, uint16_t length) {
  if (length > QUEUE_CAPACITY - used_) return false;
  memcpy(queue_ + used_, data, length);
  used_ += length;
  return true;
}

bool OledManager::begin(uint8_t address, bool rotate180) {
  if (address < 0x08 || address > 0x77) return false;
  Wire.begin();
  Wire.beginTransmission(address);
  if (Wire.endTransmission() != 0) return false;
  display_.setI2CAddress(static_cast<uint8_t>(address << 1));
  display_.setDisplayRotation(rotate180 ? U8G2_R2 : U8G2_R0);
  display_.begin();
  display_.setFontMode(1);
  used_ = 0;
  initialized_ = true;
  return show();
}

bool OledManager::clear(bool white) {
  if (!initialized_) return false;
  used_ = 0;
  if (!white) return true;
  return rect(0, 0, 128, 64, true, true);
}

void OledManager::replay() {
  uint16_t cursor = 0;
  while (cursor < used_) {
    const uint8_t operation = queue_[cursor++];
    if (operation == Text) {
      const uint8_t x = queue_[cursor++];
      const uint8_t baseline = queue_[cursor++];
      const uint8_t font = queue_[cursor++];
      const uint8_t length = queue_[cursor++];
      (void)font;
      display_.setFont(u8g2_font_wqy12_t_chinese1);
      display_.setDrawColor(1);
      display_.drawUTF8(x, baseline,
                        reinterpret_cast<const char*>(queue_ + cursor));
      cursor += static_cast<uint16_t>(length) + 1;
    } else if (operation == Pixel) {
      const uint8_t x = queue_[cursor++];
      const uint8_t y = queue_[cursor++];
      display_.setDrawColor(queue_[cursor++] ? 1 : 0);
      display_.drawPixel(x, y);
    } else if (operation == Line) {
      const uint8_t x0 = queue_[cursor++];
      const uint8_t y0 = queue_[cursor++];
      const uint8_t x1 = queue_[cursor++];
      const uint8_t y1 = queue_[cursor++];
      display_.setDrawColor(queue_[cursor++] ? 1 : 0);
      display_.drawLine(x0, y0, x1, y1);
    } else if (operation == Rect) {
      const uint8_t x = queue_[cursor++];
      const uint8_t y = queue_[cursor++];
      const uint8_t width = queue_[cursor++];
      const uint8_t height = queue_[cursor++];
      const bool filled = queue_[cursor++] != 0;
      display_.setDrawColor(queue_[cursor++] ? 1 : 0);
      if (filled) display_.drawBox(x, y, width, height);
      else display_.drawFrame(x, y, width, height);
    } else {
      return;
    }
  }
}

bool OledManager::show() {
  if (!initialized_) return false;
  display_.firstPage();
  do {
    replay();
  } while (display_.nextPage());
  return true;
}

bool OledManager::text(
    uint8_t x, uint8_t baseline, uint8_t font,
    const uint8_t* utf8, uint16_t length) {
  if (!initialized_ || x >= 128 || baseline >= 64 || font > 1 ||
      length == 0 || length > 96 || length + 6 > QUEUE_CAPACITY - used_)
    return false;
  const uint8_t header[] = {
      Text, x, baseline, font, static_cast<uint8_t>(length)};
  if (!append(header, sizeof(header)) || !append(utf8, length)) return false;
  const uint8_t terminator = 0;
  return append(&terminator, 1);
}

bool OledManager::pixel(uint8_t x, uint8_t y, bool white) {
  if (!initialized_ || x >= 128 || y >= 64) return false;
  const uint8_t operation[] = {Pixel, x, y, static_cast<uint8_t>(white)};
  return append(operation, sizeof(operation));
}

bool OledManager::line(
    uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1, bool white) {
  if (!initialized_ || x0 >= 128 || x1 >= 128 || y0 >= 64 || y1 >= 64)
    return false;
  const uint8_t operation[] = {
      Line, x0, y0, x1, y1, static_cast<uint8_t>(white)};
  return append(operation, sizeof(operation));
}

bool OledManager::rect(
    uint8_t x, uint8_t y, uint8_t width, uint8_t height,
    bool filled, bool white) {
  if (!initialized_ || x >= 128 || y >= 64 || width == 0 || height == 0 ||
      static_cast<uint16_t>(x) + width > 128 ||
      static_cast<uint16_t>(y) + height > 64) return false;
  const uint8_t operation[] = {
      Rect, x, y, width, height,
      static_cast<uint8_t>(filled), static_cast<uint8_t>(white)};
  return append(operation, sizeof(operation));
}

void OledManager::reset() {
  if (!initialized_) return;
  used_ = 0;
  show();
  initialized_ = false;
}
