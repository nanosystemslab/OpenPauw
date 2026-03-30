#pragma once

#include <Adafruit_MCP23X17.h>
#include <Arduino.h>

#include "max328_router.h"

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

  // MCP23017 pin assignments per chip (same as Max328Router)
  static constexpr Max328Router::ChipPins kChipPins[kNumChips] = {
      Max328Router::kU1Pins,
      Max328Router::kU2Pins,
      Max328Router::kU3Pins,
      Max328Router::kU4Pins,
  };

  // Result matrix: connections[chip][pad] = true if U(chip+1) connects to PAD(pad)
  struct ScanResult {
    bool connections[kNumChips][kNumOutputs];
    uint8_t connection_count;
  };

  explicit SwitchValidator(Adafruit_MCP23X17 &mcp);
  void begin();

  // Run a full matrix scan and return results
  ScanResult scan();

  // Print scan results to Serial
  void print_result(const ScanResult& result);

  // Verify a specific configuration is routed correctly
  // Returns true if all 4 channels route to expected pads
  bool verify_config(uint8_t ip_pad, uint8_t im_pad, uint8_t vp_pad, uint8_t vm_pad);

  // Print verification result
  void print_verify_result(uint8_t ip_pad, uint8_t im_pad, uint8_t vp_pad, uint8_t vm_pad,
                           bool ip_ok, bool im_ok, bool vp_ok, bool vm_ok);

 private:
  Adafruit_MCP23X17 &mcp_;

  void set_all_outputs_low();
  void set_all_enables(bool enabled);
  void set_chip_address(const Max328Router::ChipPins &pins, uint8_t addr);
  void set_chip_enable(const Max328Router::ChipPins &pins, bool enabled);
};
