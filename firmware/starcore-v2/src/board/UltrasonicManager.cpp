#include "UltrasonicManager.h"

#include "BoardPins.h"

bool UltrasonicManager::readMillimeters(uint8_t triggerPin, uint8_t echoPin,
                                        uint32_t timeoutUs, uint32_t& distanceMm) {
  if (!board::canWriteDigital(triggerPin) || !board::canReadDigital(echoPin) ||
      triggerPin == echoPin || timeoutUs < 1000 || timeoutUs > 100000) return false;
  pinMode(triggerPin, OUTPUT);
  pinMode(echoPin, INPUT);
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  const uint32_t duration = pulseIn(echoPin, HIGH, timeoutUs);
  if (duration == 0) return false;
  distanceMm = static_cast<uint32_t>((static_cast<uint64_t>(duration) * 343ULL) / 2000ULL);
  return true;
}
