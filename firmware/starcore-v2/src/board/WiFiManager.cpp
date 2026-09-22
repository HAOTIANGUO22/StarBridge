#include "WiFiManager.h"

#include <WiFi.h>

bool WiFiManager::connect(
    const char* ssid, const char* password, uint16_t timeoutMs) {
  if (ssid == nullptr || ssid[0] == '\0' || timeoutMs < 100 || timeoutMs > 30000)
    return false;
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  const uint32_t started = millis();
  while (WiFi.status() != WL_CONNECTED &&
         static_cast<uint32_t>(millis() - started) < timeoutMs) {
    delay(20);
  }
  return WiFi.status() == WL_CONNECTED;
}

bool WiFiManager::state(WiFiState& result) const {
  result.status = static_cast<uint8_t>(WiFi.status());
  WiFi.macAddress(result.mac);
  result.channel = static_cast<uint8_t>(WiFi.channel());
  if (WiFi.status() != WL_CONNECTED) return true;
  const IPAddress ip = WiFi.localIP();
  for (uint8_t index = 0; index < 4; ++index) result.ip[index] = ip[index];
  result.rssi = WiFi.RSSI();
  return true;
}

void WiFiManager::disconnect(bool eraseCredentials) {
  WiFi.disconnect(false, eraseCredentials);
}

void WiFiManager::reset() { disconnect(false); }
