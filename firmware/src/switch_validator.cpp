#include "switch_validator.h"

constexpr uint8_t SwitchValidator::kOutputPins[];
constexpr uint8_t SwitchValidator::kInputPins[];
constexpr uint8_t SwitchValidator::kEnablePins[];
constexpr uint8_t SwitchValidator::kAddrPins[];

SwitchValidator::SwitchValidator() {}

void SwitchValidator::begin() {
  // Configure output pins (directly drive J5 pads)
  for (uint8_t i = 0; i < kNumOutputs; i++) {
    pinMode(kOutputPins[i], OUTPUT);
    digitalWrite(kOutputPins[i], LOW);
  }

  // Configure input pins with pull-down resistors (read J1-J4)
  for (uint8_t i = 0; i < kNumInputs; i++) {
    pinMode(kInputPins[i], INPUT_PULLDOWN);
  }

  // Configure enable pins (active HIGH)
  for (uint8_t i = 0; i < kNumChips; i++) {
    pinMode(kEnablePins[i], OUTPUT);
    digitalWrite(kEnablePins[i], LOW);  // Start disabled
  }

  // Configure address pins
  for (uint8_t i = 0; i < 3; i++) {
    pinMode(kAddrPins[i], OUTPUT);
    digitalWrite(kAddrPins[i], LOW);
  }
}

void SwitchValidator::set_all_outputs_low() {
  for (uint8_t i = 0; i < kNumOutputs; i++) {
    digitalWrite(kOutputPins[i], LOW);
  }
}

void SwitchValidator::set_all_enables(bool enabled) {
  for (uint8_t i = 0; i < kNumChips; i++) {
    digitalWrite(kEnablePins[i], enabled ? HIGH : LOW);
  }
}

void SwitchValidator::set_address(uint8_t addr) {
  // MAX328 address: A0, A1, A2 select S1-S8
  // addr 0 = S1, addr 1 = S2, addr 2 = S3, addr 3 = S4
  digitalWrite(kAddrPins[0], (addr & 0x01) ? HIGH : LOW);
  digitalWrite(kAddrPins[1], (addr & 0x02) ? HIGH : LOW);
  digitalWrite(kAddrPins[2], (addr & 0x04) ? HIGH : LOW);
}

SwitchValidator::ScanResult SwitchValidator::scan() {
  ScanResult result;
  result.connection_count = 0;

  // Clear the result matrix
  for (uint8_t chip = 0; chip < kNumChips; chip++) {
    for (uint8_t pad = 0; pad < kNumOutputs; pad++) {
      result.connections[chip][pad] = false;
    }
  }

  // Test each chip one at a time (they share address lines)
  for (uint8_t chip = 0; chip < kNumChips; chip++) {
    // Disable all chips first
    set_all_enables(false);
    delayMicroseconds(100);

    // Enable only this chip
    digitalWrite(kEnablePins[chip], HIGH);
    delayMicroseconds(100);

    // For each pad (S1-S4), set address and test
    for (uint8_t pad = 0; pad < kNumOutputs; pad++) {
      // Start with all outputs LOW
      set_all_outputs_low();

      // Set address to select this pad (S1=addr0, S2=addr1, etc.)
      set_address(pad);
      delayMicroseconds(100);

      // Drive this pad HIGH via output pin
      digitalWrite(kOutputPins[pad], HIGH);
      delayMicroseconds(100);

      // Read the input for this chip
      if (digitalRead(kInputPins[chip]) == HIGH) {
        result.connections[chip][pad] = true;
        result.connection_count++;
      }
    }

    // Disable this chip before moving to next
    digitalWrite(kEnablePins[chip], LOW);
  }

  // Return outputs to LOW state and disable all chips
  set_all_outputs_low();
  set_all_enables(false);

  return result;
}

void SwitchValidator::print_result(const ScanResult& result) {
  Serial.println("SWTEST RESULT (MAX328 Switch Matrix):");
  Serial.println("        PAD_A PAD_B PAD_C PAD_D");
  Serial.println("        (S1)  (S2)  (S3)  (S4)");

  const char* chip_names[] = {"U1/J1", "U2/J2", "U3/J3", "U4/J4"};

  for (uint8_t chip = 0; chip < kNumChips; chip++) {
    Serial.print(chip_names[chip]);
    Serial.print(" ");

    for (uint8_t pad = 0; pad < kNumOutputs; pad++) {
      Serial.print("  ");
      Serial.print(result.connections[chip][pad] ? "X" : ".");
      Serial.print("   ");
    }
    Serial.println();
  }

  Serial.print("CONNECTIONS: ");
  Serial.println(result.connection_count);
}

bool SwitchValidator::verify_config(uint8_t ip_pad, uint8_t im_pad, uint8_t vp_pad, uint8_t vm_pad) {
  // Test each channel individually with the router's current enable state
  // Chip order: U1=IP, U2=IM, U3=VP, U4=VM
  uint8_t expected_pads[4] = {ip_pad, im_pad, vp_pad, vm_pad};
  bool results[4] = {false, false, false, false};

  for (uint8_t chip = 0; chip < kNumChips; chip++) {
    // Disable all chips
    set_all_enables(false);
    delayMicroseconds(100);

    // Enable only this chip
    digitalWrite(kEnablePins[chip], HIGH);
    delayMicroseconds(100);

    // Set address to the expected pad for this chip
    uint8_t pad = expected_pads[chip];
    set_address(pad);
    delayMicroseconds(100);

    // Drive the expected pad HIGH
    set_all_outputs_low();
    digitalWrite(kOutputPins[pad], HIGH);
    delayMicroseconds(100);

    // Read this chip's input
    results[chip] = (digitalRead(kInputPins[chip]) == HIGH);

    // Disable this chip
    digitalWrite(kEnablePins[chip], LOW);
  }

  set_all_outputs_low();
  set_all_enables(false);

  print_verify_result(ip_pad, im_pad, vp_pad, vm_pad,
                      results[0], results[1], results[2], results[3]);

  return results[0] && results[1] && results[2] && results[3];
}

void SwitchValidator::print_verify_result(uint8_t ip_pad, uint8_t im_pad,
                                          uint8_t vp_pad, uint8_t vm_pad,
                                          bool ip_ok, bool im_ok,
                                          bool vp_ok, bool vm_ok) {
  const char pad_chars[] = "ABCD";

  Serial.println("CFGTEST RESULT:");
  Serial.print("  IP (U1/J1) -> PAD_");
  Serial.print(pad_chars[ip_pad]);
  Serial.println(ip_ok ? " : PASS" : " : FAIL");

  Serial.print("  IM (U2/J2) -> PAD_");
  Serial.print(pad_chars[im_pad]);
  Serial.println(im_ok ? " : PASS" : " : FAIL");

  Serial.print("  VP (U3/J3) -> PAD_");
  Serial.print(pad_chars[vp_pad]);
  Serial.println(vp_ok ? " : PASS" : " : FAIL");

  Serial.print("  VM (U4/J4) -> PAD_");
  Serial.print(pad_chars[vm_pad]);
  Serial.println(vm_ok ? " : PASS" : " : FAIL");
}
