#include "CommandDispatcher.h"

#include "../board/BoardPins.h"

namespace {
uint16_t readU16(const uint8_t* data) {
  return static_cast<uint16_t>(data[0]) |
         (static_cast<uint16_t>(data[1]) << 8);
}

uint32_t readU32(const uint8_t* data) {
  return static_cast<uint32_t>(data[0]) |
         (static_cast<uint32_t>(data[1]) << 8) |
         (static_cast<uint32_t>(data[2]) << 16) |
         (static_cast<uint32_t>(data[3]) << 24);
}

void writeU16(uint8_t* data, uint16_t value) {
  data[0] = static_cast<uint8_t>(value);
  data[1] = static_cast<uint8_t>(value >> 8);
}

void writeU32(uint8_t* data, uint32_t value) {
  data[0] = static_cast<uint8_t>(value);
  data[1] = static_cast<uint8_t>(value >> 8);
  data[2] = static_cast<uint8_t>(value >> 16);
  data[3] = static_cast<uint8_t>(value >> 24);
}

void writeU64(uint8_t* data, uint64_t value) {
  for (uint8_t index = 0; index < 8; ++index)
    data[index] = static_cast<uint8_t>(value >> (index * 8));
}
}  // namespace

void CommandDispatcher::reset() {
  pwm_.reset();
  oled_.reset();
  neoPixel_.reset();
  mp3_.reset();
  pn532_.reset();
  softwareSerial_.reset();
  espNow_.reset();
  wifi_.reset();
}

void CommandDispatcher::dispatch(const protocol::Frame& request, protocol::Frame& response) {
  response.version = protocol::VERSION;
  response.kind = protocol::Kind::Response;
  response.sequence = request.sequence;
  response.command = request.command;
  uint16_t dataLength = 0;
  protocol::Status status;
  if (request.version != protocol::VERSION) {
    status = protocol::Status::BadVersion;
  } else if (request.kind != protocol::Kind::Request) {
    status = protocol::Status::BadFrame;
  } else {
    status = execute(request, response.payload + 1, dataLength);
  }
  response.payload[0] = static_cast<uint8_t>(status);
  response.length = static_cast<uint16_t>(dataLength + 1);
}

protocol::Status CommandDispatcher::execute(
    const protocol::Frame& request, uint8_t* output, uint16_t& outputLength) {
  using protocol::Command;
  using protocol::Status;
  outputLength = 0;
  switch (static_cast<Command>(request.command)) {
    case Command::Ping:
      if (request.length > protocol::MAX_PAYLOAD - 1) return Status::BadLength;
      memcpy(output, request.payload, request.length);
      outputLength = request.length;
      return Status::Ok;

    case Command::GetInfo: {
      if (request.length != 0) return Status::BadLength;
      output[0] = protocol::VERSION;
      output[1] = 4;
      output[2] = 2;
      output[3] = 0;
      output[4] = board::BOARD_ID_STARCORE_V2;
      writeU32(output + 5, 0x00003FFF);
      outputLength = 9;
      return Status::Ok;
    }

    case Command::ResetState:
      if (request.length != 0) return Status::BadLength;
      reset();
      return Status::Ok;

    case Command::PinMode: {
      if (request.length != 2) return Status::BadLength;
      const uint8_t pin = request.payload[0];
      const uint8_t mode = request.payload[1];
      if (!board::canReadDigital(pin) || mode > 3) return Status::BadArgument;
      if (mode == 1 && !board::canWriteDigital(pin)) return Status::BadArgument;
      const uint8_t modes[] = {INPUT, OUTPUT, INPUT_PULLUP, INPUT_PULLDOWN};
      pinMode(pin, modes[mode]);
      return Status::Ok;
    }

    case Command::DigitalWrite:
      if (request.length != 2) return Status::BadLength;
      if (!board::canWriteDigital(request.payload[0]) || request.payload[1] > 1)
        return Status::BadArgument;
      digitalWrite(request.payload[0], request.payload[1] ? HIGH : LOW);
      return Status::Ok;

    case Command::DigitalRead:
      if (request.length != 1) return Status::BadLength;
      if (!board::canReadDigital(request.payload[0])) return Status::BadArgument;
      output[0] = digitalRead(request.payload[0]) == HIGH ? 1 : 0;
      outputLength = 1;
      return Status::Ok;

    case Command::AnalogRead: {
      if (request.length != 2) return Status::BadLength;
      const uint8_t pin = request.payload[0];
      if (!board::canReadAnalog(pin) || request.payload[1] > 1) return Status::BadArgument;
      const uint32_t value = request.payload[1] ? analogReadMilliVolts(pin) : analogRead(pin);
      writeU32(output, value);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::AnalogWrite:
      if (request.length != 2) return Status::BadLength;
      if (!board::canWriteAnalog(request.payload[0])) return Status::BadArgument;
      dacWrite(request.payload[0], request.payload[1]);
      return Status::Ok;

    case Command::PwmConfigure:
      if (request.length != 6) return Status::BadLength;
      return pwm_.configure(request.payload[0], readU32(request.payload + 1), request.payload[5])
                 ? Status::Ok : Status::BadArgument;

    case Command::PwmWrite:
      if (request.length != 5) return Status::BadLength;
      return pwm_.write(request.payload[0], readU32(request.payload + 1))
                 ? Status::Ok : Status::BadArgument;

    case Command::PwmStop:
      if (request.length != 2) return Status::BadLength;
      if (request.payload[1] > 1) return Status::BadArgument;
      return pwm_.stop(request.payload[0], request.payload[1] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledInit:
      if (request.length != 2) return Status::BadLength;
      if (request.payload[1] > 1) return Status::BadArgument;
      return oled_.begin(request.payload[0], request.payload[1] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledClear:
      if (request.length != 1) return Status::BadLength;
      if (request.payload[0] > 1) return Status::BadArgument;
      return oled_.clear(request.payload[0] != 0) ? Status::Ok : Status::BadArgument;

    case Command::OledShow:
      if (request.length != 0) return Status::BadLength;
      return oled_.show() ? Status::Ok : Status::BadArgument;

    case Command::OledText:
      if (request.length < 4) return Status::BadLength;
      return oled_.text(request.payload[0], request.payload[1], request.payload[2],
                        request.payload + 3, request.length - 3)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledPixel:
      if (request.length != 3) return Status::BadLength;
      if (request.payload[2] > 1) return Status::BadArgument;
      return oled_.pixel(request.payload[0], request.payload[1], request.payload[2] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledLine:
      if (request.length != 5) return Status::BadLength;
      if (request.payload[4] > 1) return Status::BadArgument;
      return oled_.line(request.payload[0], request.payload[1], request.payload[2],
                        request.payload[3], request.payload[4] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledRect:
      if (request.length != 6) return Status::BadLength;
      if (request.payload[4] > 1 || request.payload[5] > 1) return Status::BadArgument;
      return oled_.rect(request.payload[0], request.payload[1], request.payload[2],
                        request.payload[3], request.payload[4] != 0,
                        request.payload[5] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledBitmap:
      if (request.length < 5) return Status::BadLength;
      return oled_.bitmap(request.payload[0], request.payload[1], request.payload[2],
                          request.payload[3], request.payload + 4, request.length - 4)
                 ? Status::Ok : Status::BadArgument;

    case Command::Dht11Read: {
      if (request.length != 1) return Status::BadLength;
      int16_t temperature = 0;
      uint16_t humidity = 0;
      if (!dht11_.read(request.payload[0], temperature, humidity)) return Status::BadArgument;
      writeU16(output, static_cast<uint16_t>(temperature));
      writeU16(output + 2, humidity);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::NeoPixelInit:
      if (request.length != 4) return Status::BadLength;
      return neoPixel_.begin(request.payload[0], readU16(request.payload + 1), request.payload[3])
                 ? Status::Ok : Status::BadArgument;

    case Command::NeoPixelSet:
      if (request.length != 6) return Status::BadLength;
      return neoPixel_.set(readU16(request.payload), request.payload[2], request.payload[3],
                           request.payload[4], request.payload[5])
                 ? Status::Ok : Status::BadArgument;

    case Command::NeoPixelFill:
      if (request.length != 8) return Status::BadLength;
      return neoPixel_.fill(readU16(request.payload), readU16(request.payload + 2),
                            request.payload[4], request.payload[5], request.payload[6],
                            request.payload[7])
                 ? Status::Ok : Status::BadArgument;

    case Command::NeoPixelShow:
      if (request.length != 0) return Status::BadLength;
      return neoPixel_.show() ? Status::Ok : Status::BadArgument;

    case Command::NeoPixelClear:
      if (request.length != 0) return Status::BadLength;
      return neoPixel_.clear() ? Status::Ok : Status::BadArgument;

    case Command::UltrasonicRead: {
      if (request.length != 6) return Status::BadLength;
      uint32_t millimeters = 0;
      if (!ultrasonic_.readMillimeters(request.payload[0], request.payload[1],
                                       readU32(request.payload + 2), millimeters))
        return Status::BadArgument;
      writeU32(output, millimeters);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::Mp3Init: {
      if (request.length != 3) return Status::BadLength;
      const int8_t busyPin = request.payload[2] == 0xFF
                                 ? -1 : static_cast<int8_t>(request.payload[2]);
      return mp3_.begin(request.payload[0], request.payload[1], busyPin)
                 ? Status::Ok : Status::BadArgument;
    }

    case Command::Mp3PlayTrack:
      if (request.length != 2) return Status::BadLength;
      return mp3_.playTrack(readU16(request.payload)) ? Status::Ok : Status::BadArgument;

    case Command::Mp3Play:
      if (request.length != 0) return Status::BadLength;
      return mp3_.play() ? Status::Ok : Status::BadArgument;
    case Command::Mp3Pause:
      if (request.length != 0) return Status::BadLength;
      return mp3_.pause() ? Status::Ok : Status::BadArgument;
    case Command::Mp3Stop:
      if (request.length != 0) return Status::BadLength;
      return mp3_.stop() ? Status::Ok : Status::BadArgument;
    case Command::Mp3Next:
      if (request.length != 0) return Status::BadLength;
      return mp3_.next() ? Status::Ok : Status::BadArgument;
    case Command::Mp3Previous:
      if (request.length != 0) return Status::BadLength;
      return mp3_.previous() ? Status::Ok : Status::BadArgument;
    case Command::Mp3SetVolume:
      if (request.length != 1) return Status::BadLength;
      return mp3_.setVolume(request.payload[0]) ? Status::Ok : Status::BadArgument;

    case Command::Mp3Status: {
      if (request.length != 0) return Status::BadLength;
      uint8_t moduleStatus = 0;
      if (!mp3_.readStatus(moduleStatus)) return Status::Busy;
      output[0] = moduleStatus;
      outputLength = 1;
      return Status::Ok;
    }

    case Command::Mp3Busy: {
      if (request.length != 0) return Status::BadLength;
      bool busy = false;
      if (!mp3_.isBusy(busy)) return Status::Unsupported;
      output[0] = busy ? 1 : 0;
      outputLength = 1;
      return Status::Ok;
    }

    case Command::Pn532Init: {
      if (request.length != 2) return Status::BadLength;
      uint32_t version = 0;
      if (!pn532_.begin(request.payload[0], request.payload[1], version))
        return Status::BadArgument;
      writeU32(output, version);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::Pn532FirmwareVersion: {
      if (request.length != 0) return Status::BadLength;
      uint32_t version = 0;
      if (!pn532_.firmwareVersion(version)) return Status::BadArgument;
      writeU32(output, version);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::Pn532Scan: {
      if (request.length != 2) return Status::BadLength;
      uint8_t uidLength = 0;
      if (!pn532_.scan(readU16(request.payload), output + 1, uidLength))
        return Status::BadArgument;
      output[0] = uidLength;
      outputLength = static_cast<uint16_t>(uidLength + 1);
      return Status::Ok;
    }

    case Command::Pn532ClassicRead:
      if (request.length != 8) return Status::BadLength;
      if (request.payload[1] > 1) return Status::BadArgument;
      if (!pn532_.readClassic(request.payload[0], request.payload[1] != 0,
                              request.payload + 2, output))
        return Status::Busy;
      outputLength = 16;
      return Status::Ok;

    case Command::Pn532ClassicWrite:
      if (request.length != 24) return Status::BadLength;
      if (request.payload[1] > 1) return Status::BadArgument;
      return pn532_.writeClassic(request.payload[0], request.payload[1] != 0,
                                 request.payload + 2, request.payload + 8)
                 ? Status::Ok : Status::Busy;

    case Command::Pn532PageRead:
      if (request.length != 1) return Status::BadLength;
      if (!pn532_.readPage(request.payload[0], output)) return Status::Busy;
      outputLength = 4;
      return Status::Ok;

    case Command::Pn532PageWrite:
      if (request.length != 5) return Status::BadLength;
      return pn532_.writePage(request.payload[0], request.payload + 1)
                 ? Status::Ok : Status::Busy;

    case Command::SoftwareSerialInit:
      if (request.length != 6) return Status::BadLength;
      return softwareSerial_.begin(request.payload[0], request.payload[1],
                                   readU32(request.payload + 2))
                 ? Status::Ok : Status::BadArgument;

    case Command::SoftwareSerialWrite:
      if (request.length == 0 || request.length > 255) return Status::BadLength;
      return softwareSerial_.write(request.payload, static_cast<uint8_t>(request.length))
                 ? Status::Ok : Status::BadArgument;

    case Command::SoftwareSerialRead: {
      if (request.length != 3) return Status::BadLength;
      uint8_t length = 0;
      if (!softwareSerial_.read(output, request.payload[0],
                                readU16(request.payload + 1), length))
        return Status::BadArgument;
      outputLength = length;
      return Status::Ok;
    }

    case Command::SoftwareSerialAvailable: {
      if (request.length != 0) return Status::BadLength;
      uint16_t count = 0;
      if (!softwareSerial_.available(count)) return Status::BadArgument;
      writeU16(output, count);
      outputLength = 2;
      return Status::Ok;
    }

    case Command::SoftwareSerialEnd:
      if (request.length != 0) return Status::BadLength;
      softwareSerial_.reset();
      return Status::Ok;

    case Command::WiFiConnect: {
      if (request.length < 5) return Status::BadLength;
      const uint16_t timeout = readU16(request.payload);
      const uint8_t ssidLength = request.payload[2];
      const uint8_t passwordLength = request.payload[3];
      if (ssidLength == 0 || ssidLength > 32 || passwordLength > 63 ||
          request.length != static_cast<uint16_t>(4 + ssidLength + passwordLength))
        return Status::BadArgument;
      char ssid[33]{};
      char password[64]{};
      memcpy(ssid, request.payload + 4, ssidLength);
      memcpy(password, request.payload + 4 + ssidLength, passwordLength);
      if (!wifi_.connect(ssid, password, timeout)) return Status::Busy;
      WiFiState state;
      wifi_.state(state);
      output[0] = state.status;
      memcpy(output + 1, state.ip, 4);
      writeU32(output + 5, static_cast<uint32_t>(state.rssi));
      memcpy(output + 9, state.mac, 6);
      output[15] = state.channel;
      outputLength = 16;
      return Status::Ok;
    }

    case Command::WiFiDisconnect:
      if (request.length != 1) return Status::BadLength;
      if (request.payload[0] > 1) return Status::BadArgument;
      wifi_.disconnect(request.payload[0] != 0);
      return Status::Ok;

    case Command::WiFiStatus: {
      if (request.length != 0) return Status::BadLength;
      WiFiState state;
      if (!wifi_.state(state)) return Status::InternalError;
      output[0] = state.status;
      memcpy(output + 1, state.ip, 4);
      writeU32(output + 5, static_cast<uint32_t>(state.rssi));
      memcpy(output + 9, state.mac, 6);
      output[15] = state.channel;
      outputLength = 16;
      return Status::Ok;
    }

    case Command::ESPNowInit:
      if (request.length != 1) return Status::BadLength;
      return espNow_.begin(request.payload[0]) ? Status::Ok : Status::BadArgument;

    case Command::ESPNowAddPeer:
      if (request.length != 24) return Status::BadLength;
      if (request.payload[7] > 1) return Status::BadArgument;
      return espNow_.addPeer(request.payload, request.payload[6], request.payload[7] != 0,
                             request.payload + 8)
                 ? Status::Ok : Status::BadArgument;

    case Command::ESPNowRemovePeer:
      if (request.length != 6) return Status::BadLength;
      return espNow_.removePeer(request.payload) ? Status::Ok : Status::BadArgument;

    case Command::ESPNowSend:
      if (request.length < 7 || request.length > 246) return Status::BadLength;
      return espNow_.send(request.payload, request.payload + 6,
                          static_cast<uint8_t>(request.length - 6))
                 ? Status::Ok : Status::Busy;

    case Command::ESPNowReceive: {
      if (request.length != 0) return Status::BadLength;
      ESPNowMessage message;
      if (!espNow_.receive(message)) return Status::Busy;
      memcpy(output, message.mac, 6);
      output[6] = static_cast<uint8_t>(message.rssi);
      output[7] = message.channel;
      output[8] = message.length;
      memcpy(output + 9, message.data, message.length);
      outputLength = static_cast<uint16_t>(9 + message.length);
      return Status::Ok;
    }

    case Command::ESPNowLocalMac:
      if (request.length != 0) return Status::BadLength;
      espNow_.localMac(output);
      outputLength = 6;
      return Status::Ok;

    case Command::TimeSync: {
      if (request.length < 12) return Status::BadLength;
      const uint8_t serverLength = request.payload[10];
      if (serverLength == 0 || serverLength > 63 || request.length != 11 + serverLength)
        return Status::BadArgument;
      char server[64]{};
      memcpy(server, request.payload + 11, serverLength);
      uint64_t epoch = 0;
      if (!time_.synchronize(static_cast<int32_t>(readU32(request.payload)),
                             static_cast<int32_t>(readU32(request.payload + 4)),
                             server, readU16(request.payload + 8), epoch))
        return Status::Busy;
      writeU64(output, epoch);
      outputLength = 8;
      return Status::Ok;
    }

    case Command::TimeNow: {
      if (request.length != 0) return Status::BadLength;
      uint64_t epoch = 0;
      if (!time_.now(epoch)) return Status::Busy;
      writeU64(output, epoch);
      outputLength = 8;
      return Status::Ok;
    }
  }
  return Status::BadCommand;
}
