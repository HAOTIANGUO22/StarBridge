#include "NeoPixelManager.h"

#include "BoardPins.h"

NeoPixelManager::~NeoPixelManager() { reset(); }

bool NeoPixelManager::begin(uint8_t pin, uint16_t count, uint8_t brightness) {
  if (!board::canUseDigital(pin) || count == 0 || count > MAX_PIXELS) return false;
  reset();
  strip_ = new Adafruit_NeoPixel(count, pin, NEO_GRB + NEO_KHZ800);
  if (strip_ == nullptr) return false;
  strip_->begin();
  strip_->setBrightness(brightness);
  strip_->clear();
  strip_->show();
  return true;
}

bool NeoPixelManager::set(uint16_t index, uint8_t red, uint8_t green,
                          uint8_t blue, uint8_t white) {
  if (strip_ == nullptr || index >= strip_->numPixels()) return false;
  strip_->setPixelColor(index, strip_->Color(red, green, blue, white));
  return true;
}

bool NeoPixelManager::fill(uint16_t first, uint16_t count, uint8_t red,
                           uint8_t green, uint8_t blue, uint8_t white) {
  if (strip_ == nullptr || first >= strip_->numPixels() || count == 0 ||
      static_cast<uint32_t>(first) + count > strip_->numPixels()) return false;
  strip_->fill(strip_->Color(red, green, blue, white), first, count);
  return true;
}

bool NeoPixelManager::show() {
  if (strip_ == nullptr) return false;
  strip_->show();
  return true;
}

bool NeoPixelManager::clear() {
  if (strip_ == nullptr) return false;
  strip_->clear();
  return true;
}

void NeoPixelManager::reset() {
  if (strip_ != nullptr) {
    strip_->clear();
    strip_->show();
    delete strip_;
    strip_ = nullptr;
  }
}
