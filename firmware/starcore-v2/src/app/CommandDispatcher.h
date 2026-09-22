#pragma once

#include "../board/PwmManager.h"
#include "../board/OledManager.h"
#include "../board/Dht11Manager.h"
#include "../board/NeoPixelManager.h"
#include "../board/UltrasonicManager.h"
#include "../board/Dfr0534Manager.h"
#include "../board/Pn532Manager.h"
#include "../board/SoftwareSerialManager.h"
#include "../board/WiFiManager.h"
#include "../board/ESPNowManager.h"
#include "../board/TimeManager.h"
#include "../protocol/Protocol.h"

class CommandDispatcher {
 public:
  void dispatch(const protocol::Frame& request, protocol::Frame& response);
  void reset();

 private:
  PwmManager pwm_;
  OledManager oled_;
  Dht11Manager dht11_;
  NeoPixelManager neoPixel_;
  UltrasonicManager ultrasonic_;
  Dfr0534Manager mp3_;
  Pn532Manager pn532_;
  SoftwareSerialManager softwareSerial_;
  WiFiManager wifi_;
  ESPNowManager espNow_;
  TimeManager time_;
  protocol::Status execute(const protocol::Frame& request, uint8_t* output, uint16_t& outputLength);
};
