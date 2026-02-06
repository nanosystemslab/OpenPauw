#pragma once

#include <Arduino.h>

enum class LedState {
  OFF,
  READY,      // Green - idle/ready
  BUSY,       // Blue - processing
  ERROR,      // Red - error
  SUCCESS,    // Green bright - operation succeeded
  WARNING,    // Yellow - partial success
  SWTEST_PASS,  // Green - all connections valid
  SWTEST_FAIL,  // Red - no connections or unexpected
  SWTEST_PARTIAL // Yellow - some connections
};

class StatusLed {
 public:
  static constexpr uint8_t kNeoPixelPin = 16;
  static constexpr uint8_t kNeoPixelPower = 17;
  static constexpr uint8_t kBrightness = 30;  // 0-255, keep low to avoid glare

  StatusLed();
  void begin();
  void set_state(LedState state);
  void set_color(uint8_t r, uint8_t g, uint8_t b);
  void off();
  void pulse();  // Call in loop for pulsing effect when busy
  void update(); // Call in loop for animations

 private:
  LedState current_state_;
  uint32_t last_update_;
  uint8_t pulse_value_;
  bool pulse_rising_;
};

extern StatusLed status_led;
