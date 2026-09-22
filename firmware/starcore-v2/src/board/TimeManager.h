#pragma once

#include <Arduino.h>

class TimeManager {
 public:
  bool synchronize(int32_t utcOffsetSeconds, int32_t daylightOffsetSeconds,
                   const char* server, uint16_t timeoutMs, uint64_t& epoch);
  bool now(uint64_t& epoch) const;
};
