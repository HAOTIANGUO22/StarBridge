# Third-party notices

The MIT license at the repository root applies only to original StarBridge v4 code. Third-party components retain their own licenses.

## DFRobot U8g2 Arduino

- Location: `firmware/shared-libraries/U8g2`
- Source: https://github.com/DFRobot/U8g2_Arduino
- Pinned source commit: `42351d05350b5013012a02653f0588f680cd3610`
- Upstream U8g2 code license: BSD-2-Clause
- Full bundled license: `firmware/shared-libraries/U8g2/LICENSE`

The bundled U8g2 source contains fonts and other assets with licenses that differ from the library code. Their copyright and license comments are retained in the upstream source. U8g2's font-license index is available at https://github.com/olikraus/u8g2/wiki/fntgrp.

StarBridge uses `u8g2_font_wqy12_t_gb2312`. Its source identifies it as GPL-2.0-or-later with the GNU Font Embedding Exception. The original notice remains in `firmware/shared-libraries/U8g2/src/clib/u8g2_fonts.c`.

## DFRobot DHT11

- Location: `firmware/shared-libraries/DFRobot_DHT11`
- Source: https://github.com/DFRobot/DFRobot_DHT11
- Version/commit: `V1.0.0` / `d6de7bd51683eb45c4e7d951e8a7b1ffd254c1b5`
- License: MIT; bundled as `firmware/shared-libraries/DFRobot_DHT11/LICENSE`

## Adafruit NeoPixel

- Location: `firmware/shared-libraries/Adafruit_NeoPixel`
- Source: https://github.com/adafruit/Adafruit_NeoPixel
- Version/commit: `1.15.5` / `d514fc3beae85dd4c2b19781b93faa47bd6e996f`
- License: LGPL-3.0; bundled as `firmware/shared-libraries/Adafruit_NeoPixel/COPYING`

## EspSoftwareSerial

- Location: `firmware/platforms/esp32/libraries/EspSoftwareSerial`
- Source: https://github.com/plerup/espsoftwareserial
- Version/commit: `8.1.0` / `9e61fa07c3a81b90fa1c2b333f963c0b70b74fe3`
- License: LGPL-2.1-or-later; bundled as `firmware/platforms/esp32/libraries/EspSoftwareSerial/LICENSE`

The DFR0534 command framing code under `firmware/starcore-v2/src/board` is original StarBridge code written from DFRobot's published serial protocol and is covered by the repository MIT license.

## Espressif esptool

- Bundled in Windows release wheels as `starbridge/_offline/windows-x86_64/esptool.exe`
- Source: https://github.com/espressif/esptool
- Version: 5.3.1
- License: GPL-2.0-or-later
- The upstream license is bundled beside the executable as `ESPTOOL_LICENSE.txt`.

The executable is distributed as an independent program and is invoked through a subprocess. StarBridge does not link against or import esptool code.

## pySerial

- Location: `python/src/starbridge/_vendor/serial`
- Source: https://github.com/pyserial/pyserial
- Version: 3.5
- License: BSD-3-Clause
- Full bundled license: `python/src/starbridge/_vendor/serial/LICENSE.txt`

pySerial is stored under StarBridge's private vendor namespace so an offline wheel has no external Python package dependency.
