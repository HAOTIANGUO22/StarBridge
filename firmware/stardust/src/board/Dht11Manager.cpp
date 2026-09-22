#include "Dht11Manager.h"

#include "BoardPins.h"

bool Dht11Manager::read(uint8_t pin, int16_t& temperatureTenths,
                        uint16_t& humidityTenths) {
  if (!board::canUseDigital(pin)) return false;
  sensor_.read(pin);
  if (sensor_.humidity < 0 || sensor_.humidity > 100 ||
      sensor_.temperature < -40 || sensor_.temperature > 80) return false;
  temperatureTenths = static_cast<int16_t>(sensor_.temperature * 10);
  humidityTenths = static_cast<uint16_t>(sensor_.humidity * 10);
  return true;
}
