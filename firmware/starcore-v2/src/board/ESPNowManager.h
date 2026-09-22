#pragma once

#include <Arduino.h>
#include <esp_now.h>

struct ESPNowMessage {
  uint8_t mac[6]{};
  int8_t rssi = 0;
  uint8_t channel = 0;
  uint8_t length = 0;
  uint8_t data[240]{};
};

class ESPNowManager {
 public:
  bool begin(uint8_t channel);
  bool addPeer(const uint8_t* mac, uint8_t channel, bool encrypt, const uint8_t* lmk);
  bool removePeer(const uint8_t* mac);
  bool send(const uint8_t* mac, const uint8_t* data, uint8_t length);
  bool receive(ESPNowMessage& message);
  void localMac(uint8_t* mac) const;
  void reset();

 private:
  static constexpr uint8_t QUEUE_SIZE = 4;
  static ESPNowManager* instance_;
  static void onReceive(const esp_now_recv_info_t* info, const uint8_t* data, int length);

  bool initialized_ = false;
  ESPNowMessage queue_[QUEUE_SIZE]{};
  volatile uint8_t head_ = 0;
  volatile uint8_t tail_ = 0;
  volatile uint8_t count_ = 0;
  portMUX_TYPE mutex_ = portMUX_INITIALIZER_UNLOCKED;
};
