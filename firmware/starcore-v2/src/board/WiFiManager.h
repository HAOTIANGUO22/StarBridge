#pragma once

#include <Arduino.h>

struct WiFiState {
  uint8_t status = 0;
  uint8_t ip[4]{};
  int32_t rssi = 0;
  uint8_t mac[6]{};
  uint8_t channel = 0;
};

class WiFiManager {
 public:
  bool connect(const char* ssid, const char* password, uint16_t timeoutMs);
  bool state(WiFiState& state) const;
  void disconnect(bool eraseCredentials);
  void reset();
};
