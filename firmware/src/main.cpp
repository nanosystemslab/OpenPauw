#include <Arduino.h>

#include "max328_router.h"
#include "protocol.h"
#include "switch_validator.h"
#include "test_mode.h"
#include "vdp_sequences.h"

Max328Router router;
TestMode test_mode(router);
SwitchValidator switch_validator;
Protocol protocol(router, &test_mode, &switch_validator);

void setup() {
  Serial.begin(115200);

  router.begin();
  test_mode.begin();
  switch_validator.begin();

  RouterState default_state;
  if (get_vdp_config(1, default_state)) {
    router.apply_state(default_state, 1);
  }

  Serial.println("READY");

  protocol.begin();
}

void loop() {
  protocol.update();
  test_mode.update();
}

// Python (pyserial) example:
//
// import serial
// ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
// ser.write(b"CFG 2\n")
// print(ser.readline().decode().strip())
