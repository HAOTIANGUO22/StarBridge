/*
  StarDust pin variant, derived from Arduino's standard ATmega328P variant.
  The inherited variant code remains licensed under LGPL-2.1-or-later.
*/

#ifndef Pins_Arduino_h
#define Pins_Arduino_h

#include <avr/pgmspace.h>

#define NUM_DIGITAL_PINS            20
#define NUM_ANALOG_INPUTS           4
#define analogInputToDigitalPin(p)  ((p) < 4 ? (p) + 14 : -1)
#define digitalPinHasPWM(p)         ((p) == 3 || (p) == 5 || (p) == 6 || (p) == 9 || (p) == 10)

// D0/D1 are wired to CH340 and reserved for the StarBridge protocol.
static const uint8_t RX = 0;
static const uint8_t TX = 1;

// Only SS is physically exposed; the remaining hardware SPI pins are absent.
#define PIN_SPI_SS    (10)
#define PIN_SPI_MOSI  (255)
#define PIN_SPI_MISO  (255)
#define PIN_SPI_SCK   (255)
static const uint8_t SS = PIN_SPI_SS;
static const uint8_t MOSI = PIN_SPI_MOSI;
static const uint8_t MISO = PIN_SPI_MISO;
static const uint8_t SCK = PIN_SPI_SCK;

// Dedicated I2C connector. These pins are not exposed as general protocol GPIO.
#define PIN_WIRE_SDA  (18)
#define PIN_WIRE_SCL  (19)
static const uint8_t SDA = PIN_WIRE_SDA;
static const uint8_t SCL = PIN_WIRE_SCL;

#define PIN_A0 (14)
#define PIN_A1 (15)
#define PIN_A2 (16)
#define PIN_A3 (17)
static const uint8_t A0 = PIN_A0;
static const uint8_t A1 = PIN_A1;
static const uint8_t A2 = PIN_A2;
static const uint8_t A3 = PIN_A3;

#define STARDUST_PIN_VALID(p) \
  ((p) == 2 || (p) == 3 || (p) == 5 || (p) == 6 || (p) == 9 || \
   (p) == 10 || ((p) >= 14 && (p) <= 17))

#define digitalPinToPCICR(p) \
  (STARDUST_PIN_VALID(p) ? (&PCICR) : ((uint8_t*)0))
#define digitalPinToPCICRbit(p) \
  ((p) <= 7 ? 2 : ((p) <= 13 ? 0 : 1))
#define digitalPinToPCMSK(p) \
  (!STARDUST_PIN_VALID(p) ? ((uint8_t*)0) : \
   ((p) <= 7 ? (&PCMSK2) : ((p) <= 13 ? (&PCMSK0) : (&PCMSK1))))
#define digitalPinToPCMSKbit(p) \
  ((p) <= 7 ? (p) : ((p) <= 13 ? (p) - 8 : (p) - 14))

#define digitalPinToInterrupt(p) \
  ((p) == 2 ? 0 : ((p) == 3 ? 1 : NOT_AN_INTERRUPT))

#ifdef ARDUINO_MAIN

const uint16_t PROGMEM port_to_mode_PGM[] = {
  NOT_A_PORT, NOT_A_PORT, (uint16_t)&DDRB, (uint16_t)&DDRC, (uint16_t)&DDRD,
};

const uint16_t PROGMEM port_to_output_PGM[] = {
  NOT_A_PORT, NOT_A_PORT, (uint16_t)&PORTB, (uint16_t)&PORTC, (uint16_t)&PORTD,
};

const uint16_t PROGMEM port_to_input_PGM[] = {
  NOT_A_PORT, NOT_A_PORT, (uint16_t)&PINB, (uint16_t)&PINC, (uint16_t)&PIND,
};

const uint8_t PROGMEM digital_pin_to_port_PGM[] = {
  NOT_A_PORT, NOT_A_PORT, PD, PD, NOT_A_PORT, PD, PD, NOT_A_PORT,
  NOT_A_PORT, PB, PB, NOT_A_PORT, NOT_A_PORT, NOT_A_PORT, PC, PC, PC, PC,
  PC, PC,
};

const uint8_t PROGMEM digital_pin_to_bit_mask_PGM[] = {
  0, 0, _BV(2), _BV(3), 0, _BV(5), _BV(6), 0,
  0, _BV(1), _BV(2), 0, 0, 0, _BV(0), _BV(1), _BV(2), _BV(3),
  _BV(4), _BV(5),
};

const uint8_t PROGMEM digital_pin_to_timer_PGM[] = {
  NOT_ON_TIMER, NOT_ON_TIMER, NOT_ON_TIMER, TIMER2B, NOT_ON_TIMER,
  TIMER0B, TIMER0A, NOT_ON_TIMER, NOT_ON_TIMER, TIMER1A, TIMER1B,
  NOT_ON_TIMER, NOT_ON_TIMER, NOT_ON_TIMER, NOT_ON_TIMER, NOT_ON_TIMER,
  NOT_ON_TIMER, NOT_ON_TIMER, NOT_ON_TIMER, NOT_ON_TIMER,
};

#endif

#define SERIAL_PORT_MONITOR Serial
#define SERIAL_PORT_HARDWARE Serial

#endif  // Pins_Arduino_h
