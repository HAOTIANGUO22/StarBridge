#include "Protocol.h"

#include <cstring>

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
  expected_ = 0;
}

void Decoder::tick(uint32_t nowMs) {
  if (state_ != State::SeekFirst && static_cast<uint32_t>(nowMs - lastByteMs_) > FRAME_TIMEOUT_MS) {
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
      expected_ = 0;
    } else {
      state_ = byte == SOF_0 ? State::SeekSecond : State::SeekFirst;
    }
    return false;
  }

  body_[received_++] = byte;
  if (received_ == HEADER_SIZE) {
    const uint16_t payloadLength = static_cast<uint16_t>(body_[5]) |
                                   (static_cast<uint16_t>(body_[6]) << 8);
    if (payloadLength > MAX_PAYLOAD) {
      ++lengthErrors_;
      reset();
      return false;
    }
    expected_ = HEADER_SIZE + payloadLength + 2;
  }
  if (expected_ == 0 || received_ < expected_) return false;

  const uint16_t receivedCrc = static_cast<uint16_t>(body_[expected_ - 2]) |
                               (static_cast<uint16_t>(body_[expected_ - 1]) << 8);
  const uint16_t calculatedCrc = crc16Ccitt(body_, expected_ - 2);
  if (receivedCrc != calculatedCrc) {
    ++crcErrors_;
    reset();
    return false;
  }

  output.version = body_[0];
  output.kind = static_cast<Kind>(body_[1]);
  output.sequence = static_cast<uint16_t>(body_[2]) |
                    (static_cast<uint16_t>(body_[3]) << 8);
  output.command = body_[4];
  output.length = static_cast<uint16_t>(body_[5]) |
                  (static_cast<uint16_t>(body_[6]) << 8);
  if (output.length) std::memcpy(output.payload, body_ + HEADER_SIZE, output.length);
  reset();
  return true;
}

size_t encode(const Frame& frame, uint8_t* output, size_t capacity) {
  const size_t required = 2 + HEADER_SIZE + frame.length + 2;
  if (frame.length > MAX_PAYLOAD || capacity < required) return 0;
  output[0] = SOF_0;
  output[1] = SOF_1;
  output[2] = frame.version;
  output[3] = static_cast<uint8_t>(frame.kind);
  output[4] = static_cast<uint8_t>(frame.sequence & 0xFF);
  output[5] = static_cast<uint8_t>(frame.sequence >> 8);
  output[6] = frame.command;
  output[7] = static_cast<uint8_t>(frame.length & 0xFF);
  output[8] = static_cast<uint8_t>(frame.length >> 8);
  if (frame.length) std::memcpy(output + 9, frame.payload, frame.length);
  const uint16_t crc = crc16Ccitt(output + 2, HEADER_SIZE + frame.length);
  output[9 + frame.length] = static_cast<uint8_t>(crc & 0xFF);
  output[10 + frame.length] = static_cast<uint8_t>(crc >> 8);
  return required;
}

}  // namespace protocol

