#include "switch_validator.h"

constexpr uint8_t SwitchValidator::kOutputPins[];
constexpr uint8_t SwitchValidator::kInputPins[];

SwitchValidator::SwitchValidator() {}

void SwitchValidator::begin() {
  // Configure output pins
  for (uint8_t i = 0; i < kNumOutputs; i++) {
    pinMode(kOutputPins[i], OUTPUT);
    digitalWrite(kOutputPins[i], LOW);
  }

  // Configure input pins with pull-down resistors
  // When output drives HIGH through a closed switch, input reads HIGH
  for (uint8_t i = 0; i < kNumInputs; i++) {
    pinMode(kInputPins[i], INPUT_PULLDOWN);
  }
}

void SwitchValidator::set_all_outputs_low() {
  for (uint8_t i = 0; i < kNumOutputs; i++) {
    digitalWrite(kOutputPins[i], LOW);
  }
}

SwitchValidator::ScanResult SwitchValidator::scan() {
  ScanResult result;
  result.connection_count = 0;

  // Clear the result matrix
  for (uint8_t out = 0; out < kNumOutputs; out++) {
    for (uint8_t in = 0; in < kNumInputs; in++) {
      result.connections[out][in] = false;
    }
  }

  // For each output, drive it HIGH and read all inputs
  for (uint8_t out = 0; out < kNumOutputs; out++) {
    // Start with all outputs LOW
    set_all_outputs_low();

    // Drive this output HIGH
    digitalWrite(kOutputPins[out], HIGH);

    // Small delay for signal to settle
    delayMicroseconds(100);

    // Read all inputs
    for (uint8_t in = 0; in < kNumInputs; in++) {
      if (digitalRead(kInputPins[in]) == HIGH) {
        result.connections[out][in] = true;
        result.connection_count++;
      }
    }
  }

  // Return outputs to LOW state
  set_all_outputs_low();

  return result;
}

void SwitchValidator::print_result(const ScanResult& result) {
  Serial.println("SWTEST RESULT:");
  Serial.println("        IN0   IN1   IN2   IN3");
  Serial.print("       (GP26)(GP27)(GP28)(GP29)");
  Serial.println();

  for (uint8_t out = 0; out < kNumOutputs; out++) {
    Serial.print("OUT");
    Serial.print(out);
    Serial.print(" (GP");
    Serial.print(kOutputPins[out]);
    Serial.print(")");
    if (kOutputPins[out] < 10) Serial.print(" ");

    for (uint8_t in = 0; in < kNumInputs; in++) {
      Serial.print("  ");
      Serial.print(result.connections[out][in] ? "X" : ".");
      Serial.print("   ");
    }
    Serial.println();
  }

  Serial.print("CONNECTIONS: ");
  Serial.println(result.connection_count);
}
