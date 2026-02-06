#include "status_led.h"
#include <Adafruit_NeoPixel.h>

static Adafruit_NeoPixel pixel(1, StatusLed::kNeoPixelPin, NEO_GRB + NEO_KHZ800);

StatusLed status_led;

StatusLed::StatusLed()
    : current_state_(LedState::OFF),
      last_update_(0),
      pulse_value_(0),
      pulse_rising_(true) {}

void StatusLed::begin() {
  pinMode(kNeoPixelPower, OUTPUT);
  digitalWrite(kNeoPixelPower, HIGH);  // Enable NeoPixel power

  pixel.begin();
  pixel.setBrightness(kBrightness);
  pixel.clear();
  pixel.show();

  set_state(LedState::READY);
}

void StatusLed::set_state(LedState state) {
  current_state_ = state;

  switch (state) {
    case LedState::OFF:
      pixel.setPixelColor(0, 0, 0, 0);
      break;
    case LedState::READY:
      pixel.setPixelColor(0, 0, 50, 0);  // Dim green
      break;
    case LedState::BUSY:
      pixel.setPixelColor(0, 0, 0, 50);  // Blue
      break;
    case LedState::ERROR:
    case LedState::SWTEST_FAIL:
      pixel.setPixelColor(0, 100, 0, 0);  // Red
      break;
    case LedState::SUCCESS:
    case LedState::SWTEST_PASS:
      pixel.setPixelColor(0, 0, 100, 0);  // Bright green
      break;
    case LedState::WARNING:
    case LedState::SWTEST_PARTIAL:
      pixel.setPixelColor(0, 100, 50, 0);  // Yellow/orange
      break;
  }
  pixel.show();
}

void StatusLed::set_color(uint8_t r, uint8_t g, uint8_t b) {
  pixel.setPixelColor(0, r, g, b);
  pixel.show();
}

void StatusLed::off() {
  set_state(LedState::OFF);
}

void StatusLed::update() {
  if (current_state_ != LedState::BUSY) {
    return;
  }

  uint32_t now = millis();
  if (now - last_update_ < 20) {
    return;
  }
  last_update_ = now;

  if (pulse_rising_) {
    pulse_value_ += 5;
    if (pulse_value_ >= 100) {
      pulse_rising_ = false;
    }
  } else {
    pulse_value_ -= 5;
    if (pulse_value_ <= 10) {
      pulse_rising_ = true;
    }
  }

  pixel.setPixelColor(0, 0, 0, pulse_value_);
  pixel.show();
}
