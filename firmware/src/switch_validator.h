#pragma once

#include <Arduino.h>

class SwitchValidator {
 public:
  static constexpr uint8_t kNumOutputs = 4;  // J5 pads (S1-S4)
  static constexpr uint8_t kNumInputs = 4;   // J1-J4 probes (D pins of U1-U4)
  static constexpr uint8_t kNumChips = 4;    // U1, U2, U3, U4

  // Output pins - directly drive J5 pads (S1-S4 on all MAX328s)
  // J5 pin 1 (PAD_A) = MOSI (GP19), pin 2 (PAD_B) = MISO (GP20)
  // J5 pin 3 (PAD_C) = RX (GP1), pin 4 (PAD_D) = TX (GP0)
  static constexpr uint8_t kOutputPins[kNumOutputs] = {19, 20, 1, 0};

  // Input pins - read J1-J4 probes (D outputs of MAX328s)
  // A0-A3 on Feather RP2040 = GP26-29
  static constexpr uint8_t kInputPins[kNumInputs] = {26, 27, 28, 29};

  // MAX328 Enable pins: U1=D9(GP9), U2=D6(GP8), U3=D5(GP7), U4=D4(GP6)
  static constexpr uint8_t kEnablePins[kNumChips] = {9, 8, 7, 6};

  // MAX328 Address pins (shared): A0=D10(GP10), A1=D11(GP11), A2=D12(GP12)
  static constexpr uint8_t kAddrPins[3] = {10, 11, 12};

  // Result matrix: connections[chip][pad] = true if U(chip+1) connects to PAD(pad)
  struct ScanResult {
    bool connections[kNumChips][kNumOutputs];
    uint8_t connection_count;
  };

  SwitchValidator();
  void begin();

  // Run a full matrix scan and return results
  ScanResult scan();

  // Print scan results to Serial
  void print_result(const ScanResult& result);

 private:
  void set_all_outputs_low();
  void set_all_enables(bool enabled);
  void set_address(uint8_t addr);
};
