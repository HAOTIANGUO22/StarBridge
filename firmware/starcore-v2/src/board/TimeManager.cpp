#include "TimeManager.h"

#include <time.h>

bool TimeManager::synchronize(
    int32_t utcOffsetSeconds, int32_t daylightOffsetSeconds,
    const char* server, uint16_t timeoutMs, uint64_t& epoch) {
  if (server == nullptr || server[0] == '\0' || timeoutMs < 100 ||
      timeoutMs > 30000 || utcOffsetSeconds < -50400 || utcOffsetSeconds > 50400 ||
      daylightOffsetSeconds < -7200 || daylightOffsetSeconds > 7200)
    return false;
  configTime(utcOffsetSeconds, daylightOffsetSeconds, server);
  const uint32_t started = millis();
  do {
    const time_t current = time(nullptr);
    if (current > 1609459200) {
      epoch = static_cast<uint64_t>(current);
      return true;
    }
    delay(20);
  } while (static_cast<uint32_t>(millis() - started) < timeoutMs);
  return false;
}

bool TimeManager::now(uint64_t& epoch) const {
  const time_t current = time(nullptr);
  if (current <= 1609459200) return false;
  epoch = static_cast<uint64_t>(current);
  return true;
}
