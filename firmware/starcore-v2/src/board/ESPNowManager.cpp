#include "ESPNowManager.h"

#include <WiFi.h>
#include <esp_wifi.h>

ESPNowManager* ESPNowManager::instance_ = nullptr;

bool ESPNowManager::begin(uint8_t channel) {
  if (channel > 14) return false;
  if (initialized_) reset();
  WiFi.mode(WIFI_STA);
  if (channel != 0) {
    if (WiFi.status() == WL_CONNECTED && WiFi.channel() != channel) return false;
    if (esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE) != ESP_OK) return false;
  }
  if (esp_now_init() != ESP_OK) return false;
  instance_ = this;
  if (esp_now_register_recv_cb(onReceive) != ESP_OK) {
    esp_now_deinit();
    instance_ = nullptr;
    return false;
  }
  initialized_ = true;
  return true;
}

bool ESPNowManager::addPeer(
    const uint8_t* mac, uint8_t channel, bool encrypt, const uint8_t* lmk) {
  if (!initialized_ || mac == nullptr || channel > 14 || (encrypt && lmk == nullptr))
    return false;
  if (esp_now_is_peer_exist(mac)) esp_now_del_peer(mac);
  esp_now_peer_info_t peer{};
  memcpy(peer.peer_addr, mac, 6);
  peer.channel = channel;
  peer.ifidx = WIFI_IF_STA;
  peer.encrypt = encrypt;
  if (encrypt) memcpy(peer.lmk, lmk, ESP_NOW_KEY_LEN);
  return esp_now_add_peer(&peer) == ESP_OK;
}

bool ESPNowManager::removePeer(const uint8_t* mac) {
  return initialized_ && mac != nullptr && esp_now_del_peer(mac) == ESP_OK;
}

bool ESPNowManager::send(const uint8_t* mac, const uint8_t* data, uint8_t length) {
  return initialized_ && mac != nullptr && data != nullptr && length > 0 &&
         length <= 240 && esp_now_send(mac, data, length) == ESP_OK;
}

bool ESPNowManager::receive(ESPNowMessage& message) {
  portENTER_CRITICAL(&mutex_);
  if (count_ == 0) {
    portEXIT_CRITICAL(&mutex_);
    return false;
  }
  message = queue_[tail_];
  tail_ = static_cast<uint8_t>((tail_ + 1) % QUEUE_SIZE);
  count_ = static_cast<uint8_t>(count_ - 1);
  portEXIT_CRITICAL(&mutex_);
  return true;
}

void ESPNowManager::localMac(uint8_t* mac) const { WiFi.macAddress(mac); }

void ESPNowManager::reset() {
  if (initialized_) {
    esp_now_unregister_recv_cb();
    esp_now_deinit();
  }
  initialized_ = false;
  if (instance_ == this) instance_ = nullptr;
  portENTER_CRITICAL(&mutex_);
  head_ = 0;
  tail_ = 0;
  count_ = 0;
  portEXIT_CRITICAL(&mutex_);
}

void ESPNowManager::onReceive(
    const esp_now_recv_info_t* info, const uint8_t* data, int length) {
  ESPNowManager* self = instance_;
  if (self == nullptr || info == nullptr || data == nullptr || length <= 0) return;
  const uint8_t size = static_cast<uint8_t>(min(length, 240));
  portENTER_CRITICAL(&self->mutex_);
  if (self->count_ == QUEUE_SIZE) {
    self->tail_ = static_cast<uint8_t>((self->tail_ + 1) % QUEUE_SIZE);
    self->count_ = static_cast<uint8_t>(self->count_ - 1);
  }
  ESPNowMessage& message = self->queue_[self->head_];
  memcpy(message.mac, info->src_addr, 6);
  message.rssi = info->rx_ctrl == nullptr ? 0 : static_cast<int8_t>(info->rx_ctrl->rssi);
  message.channel = info->rx_ctrl == nullptr ? 0 : info->rx_ctrl->channel;
  message.length = size;
  memcpy(message.data, data, size);
  self->head_ = static_cast<uint8_t>((self->head_ + 1) % QUEUE_SIZE);
  self->count_ = static_cast<uint8_t>(self->count_ + 1);
  portEXIT_CRITICAL(&self->mutex_);
}
