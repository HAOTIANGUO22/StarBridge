#include "src/app/FirmwareApp.h"

FirmwareApp app(Serial);

void setup() {
  app.begin(115200);
}

void loop() {
  app.poll();
}
