#include "CommandDispatcher.h"

#include <string.h>

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
}  // namespace

void CommandDispatcher::reset() {
  pwm_.reset();
  oled_.reset();
  neoPixel_.reset();
  mp3_.reset();
  pn532_.reset();
  softwareSerial_.reset();
  for (uint8_t index = 0; index < sizeof(board::DIGITAL_PINS); ++index) {
    pinMode(board::DIGITAL_PINS[index], INPUT);
  }
}

void CommandDispatcher::dispatch(protocol::Frame& frame) {
  uint16_t dataLength = 0;
  protocol::Status status;
  if (frame.version != protocol::VERSION) {
    status = protocol::Status::BadVersion;
  } else if (frame.kind != protocol::Kind::Request) {
    status = protocol::Status::BadFrame;
  } else {
    status = execute(frame, frame.payload + 1, dataLength);
  }
  frame.version = protocol::VERSION;
  frame.kind = protocol::Kind::Response;
  frame.payload[0] = static_cast<uint8_t>(status);
  frame.length = dataLength + 1;
}

protocol::Status CommandDispatcher::execute(
    const protocol::Frame& request, uint8_t* output, uint16_t& outputLength) {
  using protocol::Command;
  using protocol::Status;
  outputLength = 0;

  switch (static_cast<Command>(request.command)) {
    case Command::Ping:
      if (request.length > protocol::MAX_PAYLOAD - 1) return Status::BadLength;
      memmove(output, request.payload, request.length);
      outputLength = request.length;
      return Status::Ok;

    case Command::GetInfo:
      if (request.length != 0) return Status::BadLength;
      output[0] = protocol::VERSION;
      output[1] = 4;
      output[2] = 3;
      output[3] = 1;
      output[4] = board::BOARD_ID_STARDUST;
      writeU32(output + 5, 0x000006FFUL);
      outputLength = 9;
      return Status::Ok;

    case Command::ResetState:
      if (request.length != 0) return Status::BadLength;
      reset();
      return Status::Ok;

    case Command::PinMode: {
      if (request.length != 2) return Status::BadLength;
      const uint8_t pin = request.payload[0];
      const uint8_t mode = request.payload[1];
      if (!board::canUseDigital(pin) || mode > 3) return Status::BadArgument;
      if (mode == 3) return Status::Unsupported;
      const uint8_t modes[] = {INPUT, OUTPUT, INPUT_PULLUP};
      pinMode(pin, modes[mode]);
      return Status::Ok;
    }

    case Command::DigitalWrite:
      if (request.length != 2) return Status::BadLength;
      if (!board::canUseDigital(request.payload[0]) || request.payload[1] > 1)
        return Status::BadArgument;
      digitalWrite(request.payload[0], request.payload[1] ? HIGH : LOW);
      return Status::Ok;

    case Command::DigitalRead:
      if (request.length != 1) return Status::BadLength;
      if (!board::canUseDigital(request.payload[0])) return Status::BadArgument;
      output[0] = digitalRead(request.payload[0]) == HIGH ? 1 : 0;
      outputLength = 1;
      return Status::Ok;

    case Command::AnalogRead: {
      if (request.length != 2) return Status::BadLength;
      if (!board::canReadAnalog(request.payload[0]) || request.payload[1] > 1)
        return Status::BadArgument;
      const uint16_t raw = analogRead(request.payload[0]);
      const uint32_t value = request.payload[1]
                                 ? (static_cast<uint32_t>(raw) * 5000UL + 511UL) / 1023UL
                                 : raw;
      writeU32(output, value);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::AnalogWrite:
      return Status::Unsupported;

    case Command::PwmConfigure:
      if (request.length != 6) return Status::BadLength;
      return pwm_.configure(request.payload[0], readU32(request.payload + 1),
                            request.payload[5])
                 ? Status::Ok
                 : Status::BadArgument;

    case Command::PwmWrite:
      if (request.length != 5) return Status::BadLength;
      return pwm_.write(request.payload[0], readU32(request.payload + 1))
                 ? Status::Ok
                 : Status::BadArgument;

    case Command::PwmStop:
      if (request.length != 2) return Status::BadLength;
      if (request.payload[1] > 1) return Status::BadArgument;
      return pwm_.stop(request.payload[0], request.payload[1] != 0)
                 ? Status::Ok
                 : Status::BadArgument;

    case Command::OledInit:
      if (request.length != 2) return Status::BadLength;
      if (request.payload[1] > 1) return Status::BadArgument;
      return oled_.begin(request.payload[0], request.payload[1] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledClear:
      if (request.length != 1) return Status::BadLength;
      if (request.payload[0] > 1) return Status::BadArgument;
      return oled_.clear(request.payload[0] != 0)
                 ? Status::Ok : Status::BadArgument;

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
      return oled_.pixel(request.payload[0], request.payload[1],
                         request.payload[2] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledLine:
      if (request.length != 5) return Status::BadLength;
      if (request.payload[4] > 1) return Status::BadArgument;
      return oled_.line(request.payload[0], request.payload[1], request.payload[2],
                        request.payload[3], request.payload[4] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledRect:
      if (request.length != 6) return Status::BadLength;
      if (request.payload[4] > 1 || request.payload[5] > 1)
        return Status::BadArgument;
      return oled_.rect(request.payload[0], request.payload[1], request.payload[2],
                        request.payload[3], request.payload[4] != 0,
                        request.payload[5] != 0)
                 ? Status::Ok : Status::BadArgument;

    case Command::OledBitmap:
      return Status::Unsupported;

    case Command::Dht11Read: {
      if (request.length != 1) return Status::BadLength;
      int16_t temperature = 0;
      uint16_t humidity = 0;
      if (!dht11_.read(request.payload[0], temperature, humidity))
        return Status::BadArgument;
      writeU16(output, static_cast<uint16_t>(temperature));
      writeU16(output + 2, humidity);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::NeoPixelInit:
      if (request.length != 4) return Status::BadLength;
      return neoPixel_.begin(request.payload[0], readU16(request.payload + 1),
                             request.payload[3])
                 ? Status::Ok : Status::BadArgument;

    case Command::NeoPixelSet:
      if (request.length != 6) return Status::BadLength;
      return neoPixel_.set(readU16(request.payload), request.payload[2],
                           request.payload[3], request.payload[4], request.payload[5])
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

    case Command::Mp3Init: {
      if (request.length != 3) return Status::BadLength;
      const int8_t busyPin = request.payload[2] == 0xFF
                                 ? -1 : static_cast<int8_t>(request.payload[2]);
      softwareSerial_.reset();
      return mp3_.begin(request.payload[0], request.payload[1], busyPin)
                 ? Status::Ok : Status::BadArgument;
    }

    case Command::Mp3PlayTrack:
      if (request.length != 2) return Status::BadLength;
      return mp3_.playTrack(readU16(request.payload))
                 ? Status::Ok : Status::BadArgument;
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
      return mp3_.setVolume(request.payload[0])
                 ? Status::Ok : Status::BadArgument;

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
      outputLength = uidLength + 1;
      return Status::Ok;
    }

    case Command::Pn532ClassicRead:
      if (request.length != 8) return Status::BadLength;
      if (request.payload[1] > 1) return Status::BadArgument;
      if (!pn532_.readClassic(request.payload[0], request.payload[1] != 0,
                              request.payload + 2, output)) return Status::Busy;
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
      mp3_.reset();
      return softwareSerial_.begin(request.payload[0], request.payload[1],
                                   readU32(request.payload + 2))
                 ? Status::Ok : Status::BadArgument;

    case Command::SoftwareSerialWrite:
      if (request.length == 0 || request.length > 96) return Status::BadLength;
      return softwareSerial_.write(request.payload,
                                   static_cast<uint8_t>(request.length))
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

    case Command::UltrasonicRead: {
      if (request.length != 6) return Status::BadLength;
      const uint8_t triggerPin = request.payload[0];
      const uint8_t echoPin = request.payload[1];
      const uint32_t timeoutUs = readU32(request.payload + 2);
      if (!board::canUseDigital(triggerPin) ||
          !board::canUseDigital(echoPin) || triggerPin == echoPin ||
          timeoutUs < 1000 || timeoutUs > 100000) return Status::BadArgument;
      pinMode(triggerPin, OUTPUT);
      pinMode(echoPin, INPUT);
      digitalWrite(triggerPin, LOW);
      delayMicroseconds(2);
      digitalWrite(triggerPin, HIGH);
      delayMicroseconds(10);
      digitalWrite(triggerPin, LOW);
      uint32_t started = micros();
      while (digitalRead(echoPin) == LOW) {
        if (micros() - started >= timeoutUs) return Status::BadArgument;
      }
      started = micros();
      while (digitalRead(echoPin) == HIGH) {
        if (micros() - started >= timeoutUs) return Status::BadArgument;
      }
      const uint32_t duration = micros() - started;
      writeU32(output, (duration * 343UL) / 2000UL);
      outputLength = 4;
      return Status::Ok;
    }

    case Command::WiFiConnect:
    case Command::WiFiDisconnect:
    case Command::WiFiStatus:
    case Command::ESPNowInit:
    case Command::ESPNowAddPeer:
    case Command::ESPNowRemovePeer:
    case Command::ESPNowSend:
    case Command::ESPNowReceive:
    case Command::ESPNowLocalMac:
    case Command::TimeSync:
    case Command::TimeNow:
      return Status::Unsupported;
  }
  return Status::BadCommand;
}
