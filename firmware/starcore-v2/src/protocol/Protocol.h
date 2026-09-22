#pragma once

#include <Arduino.h>

namespace protocol {

constexpr uint8_t SOF_0 = 0xA5;
constexpr uint8_t SOF_1 = 0x5A;
constexpr uint8_t VERSION = 2;
constexpr size_t HEADER_SIZE = 7;
constexpr size_t MAX_PAYLOAD = 256;
constexpr size_t MAX_BODY_SIZE = HEADER_SIZE + MAX_PAYLOAD + 2;
constexpr uint32_t FRAME_TIMEOUT_MS = 100;

enum class Kind : uint8_t {
  Request = 1,
  Response = 2,
  Event = 3,
};

enum class Command : uint8_t {
  Ping = 0x01,
  GetInfo = 0x02,
  ResetState = 0x03,
  PinMode = 0x10,
  DigitalWrite = 0x11,
  DigitalRead = 0x12,
  AnalogRead = 0x13,
  AnalogWrite = 0x14,
  PwmConfigure = 0x20,
  PwmWrite = 0x21,
  PwmStop = 0x22,
  OledInit = 0x30,
  OledClear = 0x31,
  OledShow = 0x32,
  OledText = 0x33,
  OledPixel = 0x34,
  OledLine = 0x35,
  OledRect = 0x36,
  OledBitmap = 0x37,
  Dht11Read = 0x40,
  NeoPixelInit = 0x50,
  NeoPixelSet = 0x51,
  NeoPixelFill = 0x52,
  NeoPixelShow = 0x53,
  NeoPixelClear = 0x54,
  UltrasonicRead = 0x60,
  Mp3Init = 0x70,
  Mp3PlayTrack = 0x71,
  Mp3Play = 0x72,
  Mp3Pause = 0x73,
  Mp3Stop = 0x74,
  Mp3Next = 0x75,
  Mp3Previous = 0x76,
  Mp3SetVolume = 0x77,
  Mp3Status = 0x78,
  Mp3Busy = 0x79,
  Pn532Init = 0x80,
  Pn532FirmwareVersion = 0x81,
  Pn532Scan = 0x82,
  Pn532ClassicRead = 0x83,
  Pn532ClassicWrite = 0x84,
  Pn532PageRead = 0x85,
  Pn532PageWrite = 0x86,
  SoftwareSerialInit = 0x90,
  SoftwareSerialWrite = 0x91,
  SoftwareSerialRead = 0x92,
  SoftwareSerialAvailable = 0x93,
  SoftwareSerialEnd = 0x94,
  WiFiConnect = 0xA0,
  WiFiDisconnect = 0xA1,
  WiFiStatus = 0xA2,
  ESPNowInit = 0xB0,
  ESPNowAddPeer = 0xB1,
  ESPNowRemovePeer = 0xB2,
  ESPNowSend = 0xB3,
  ESPNowReceive = 0xB4,
  ESPNowLocalMac = 0xB5,
  TimeSync = 0xC0,
  TimeNow = 0xC1,
};

enum class Status : uint8_t {
  Ok = 0,
  BadFrame = 1,
  BadVersion = 2,
  BadCommand = 3,
  BadLength = 4,
  BadArgument = 5,
  Unsupported = 6,
  Busy = 7,
  InternalError = 8,
};

struct Frame {
  uint8_t version = VERSION;
  Kind kind = Kind::Request;
  uint16_t sequence = 0;
  uint8_t command = 0;
  uint16_t length = 0;
  uint8_t payload[MAX_PAYLOAD]{};
};

uint16_t crc16Ccitt(const uint8_t* data, size_t length, uint16_t initial = 0xFFFF);

class Decoder {
 public:
  bool feed(uint8_t byte, uint32_t nowMs, Frame& output);
  void tick(uint32_t nowMs);
  void reset();
  uint32_t crcErrors() const { return crcErrors_; }
  uint32_t lengthErrors() const { return lengthErrors_; }

 private:
  enum class State : uint8_t { SeekFirst, SeekSecond, Body };
  State state_ = State::SeekFirst;
  uint8_t body_[MAX_BODY_SIZE]{};
  size_t received_ = 0;
  size_t expected_ = 0;
  uint32_t lastByteMs_ = 0;
  uint32_t crcErrors_ = 0;
  uint32_t lengthErrors_ = 0;
};

size_t encode(const Frame& frame, uint8_t* output, size_t capacity);

}  // namespace protocol
