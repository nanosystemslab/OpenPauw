#pragma once

#include <Arduino.h>

class SwitchValidator {
 public:
  static constexpr uint8_t kNumOutputs = 4;
  static constexpr uint8_t kNumInputs = 4;

  // Output pins (directly drive switches)
  static constexpr uint8_t kOutputPins[kNumOutputs] = {0, 1, 2, 3};

  // Input pins (read switch state) - A0-A3 on Feather RP2040
  static constexpr uint8_t kInputPins[kNumInputs] = {26, 27, 28, 29};

  // Result matrix: connections_[out][in] = true if output connects to input
  struct ScanResult {
    bool connections[kNumOutputs][kNumInputs];
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
};
