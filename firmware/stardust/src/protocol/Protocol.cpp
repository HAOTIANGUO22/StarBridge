#include "Protocol.h"

#include <string.h>

namespace protocol {

uint16_t crc16Ccitt(const uint8_t* data, size_t length, uint16_t initial) {
  uint16_t crc = initial;
  for (size_t index = 0; index < length; ++index) {
    crc ^= static_cast<uint16_t>(data[index]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000) ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
                           : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

void Decoder::reset() {
  state_ = State::SeekFirst;
  received_ = 0;
  payloadLength_ = 0;
}

void Decoder::tick(uint32_t nowMs) {
  if (state_ != State::SeekFirst &&
      static_cast<uint32_t>(nowMs - lastByteMs_) > FRAME_TIMEOUT_MS) {
    reset();
  }
}

bool Decoder::feed(uint8_t byte, uint32_t nowMs, Frame& output) {
  lastByteMs_ = nowMs;
  if (state_ == State::SeekFirst) {
    if (byte == SOF_0) state_ = State::SeekSecond;
    return false;
  }
  if (state_ == State::SeekSecond) {
    if (byte == SOF_1) {
      state_ = State::Body;
      received_ = 0;
      payloadLength_ = 0;
    } else {
      state_ = byte == SOF_0 ? State::SeekSecond : State::SeekFirst;
    }
    return false;
  }

  if (received_ < HEADER_SIZE) {
    header_[received_++] = byte;
    if (received_ == HEADER_SIZE) {
      payloadLength_ = static_cast<uint16_t>(header_[5]) |
                       (static_cast<uint16_t>(header_[6]) << 8);
    if (payloadLength_ > MAX_PAYLOAD) {
      reset();
      return false;
    }
    }
    return false;
  }

  const uint16_t payloadReceived = received_ - HEADER_SIZE;
  if (payloadReceived < payloadLength_) {
    output.payload[payloadReceived] = byte;
    ++received_;
    return false;
  }
  if (payloadReceived == payloadLength_) {
    receivedCrcLow_ = byte;
    ++received_;
    return false;
  }

  uint16_t calculatedCrc = crc16Ccitt(header_, HEADER_SIZE);
  calculatedCrc = crc16Ccitt(output.payload, payloadLength_, calculatedCrc);
  const uint16_t receivedCrc = static_cast<uint16_t>(receivedCrcLow_) |
                               (static_cast<uint16_t>(byte) << 8);
  if (receivedCrc != calculatedCrc) {
    reset();
    return false;
  }

  output.version = header_[0];
  output.kind = static_cast<Kind>(header_[1]);
  output.sequence = static_cast<uint16_t>(header_[2]) |
                    (static_cast<uint16_t>(header_[3]) << 8);
  output.command = header_[4];
  output.length = payloadLength_;
  reset();
  return true;
}

size_t write(Stream& stream, const Frame& frame) {
  if (frame.length > MAX_PAYLOAD) return 0;
  const uint8_t sof[] = {SOF_0, SOF_1};
  const uint8_t header[] = {
      frame.version,
      static_cast<uint8_t>(frame.kind),
      static_cast<uint8_t>(frame.sequence),
      static_cast<uint8_t>(frame.sequence >> 8),
      frame.command,
      static_cast<uint8_t>(frame.length),
      static_cast<uint8_t>(frame.length >> 8),
  };
  uint16_t crc = crc16Ccitt(header, sizeof(header));
  crc = crc16Ccitt(frame.payload, frame.length, crc);
  const uint8_t crcBytes[] = {
      static_cast<uint8_t>(crc), static_cast<uint8_t>(crc >> 8)};
  stream.write(sof, sizeof(sof));
  stream.write(header, sizeof(header));
  if (frame.length) stream.write(frame.payload, frame.length);
  stream.write(crcBytes, sizeof(crcBytes));
  return sizeof(sof) + sizeof(header) + frame.length + sizeof(crcBytes);
}

}  // namespace protocol
