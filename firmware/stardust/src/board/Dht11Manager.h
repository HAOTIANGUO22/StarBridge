#pragma once

#include <Arduino.h>
#include <DFRobot_DHT11.h>

class Dht11Manager {
 public:
  bool read(uint8_t pin, int16_t& temperatureTenths, uint16_t& humidityTenths);

 private:
  DFRobot_DHT11 sensor_;
};
