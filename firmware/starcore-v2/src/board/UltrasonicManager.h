#pragma once

#include <Arduino.h>

class UltrasonicManager {
 public:
  bool readMillimeters(uint8_t triggerPin, uint8_t echoPin, uint32_t timeoutUs,
                       uint32_t& distanceMm);
};
