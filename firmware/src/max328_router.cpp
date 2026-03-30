#include "max328_router.h"

#include <ctype.h>

char pad_to_char(Pad pad) {
  switch (pad) {
    case Pad::A:
      return 'A';
    case Pad::B:
      return 'B';
    case Pad::C:
      return 'C';
    case Pad::D:
      return 'D';
    default:
      return '?';
  }
}

bool parse_pad_char(char c, Pad &pad) {
  switch (toupper(static_cast<unsigned char>(c))) {
    case 'A':
      pad = Pad::A;
      return true;
    case 'B':
      pad = Pad::B;
      return true;
    case 'C':
      pad = Pad::C;
      return true;
    case 'D':
      pad = Pad::D;
      return true;
    default:
      return false;
  }
}

Max328Router::Max328Router()
    : state_{Pad::A, Pad::A, Pad::A, Pad::A},
      cfg_id_(0),
      enable_mask_(kEnableAll) {}

void Max328Router::begin() {
  if (!mcp_.begin_I2C(kMcpAddress)) {
    Serial.println("ERROR: MCP23017 not found at 0x20");
    return;
  }

  // Set all 16 pins as OUTPUT and LOW
  for (uint8_t i = 0; i < 16; i++) {
    mcp_.pinMode(i, OUTPUT);
  }
  mcp_.writeGPIOAB(0x0000);

  apply_enable_mask();
}

void Max328Router::apply_state(const RouterState &state, uint8_t cfg_id) {
  state_ = state;
  cfg_id_ = cfg_id;

  // Disable all chips, set addresses, then re-enable
  uint8_t prev_mask = enable_mask_;
  enable_mask_ = 0;
  write_all();
  delay(1);
  enable_mask_ = prev_mask;

  write_all();
  delay(kSettleDelayMs);
}

const RouterState &Max328Router::state() const { return state_; }

uint8_t Max328Router::cfg_id() const { return cfg_id_; }

void Max328Router::set_chip(const ChipPins &pins, Pad pad) {
  uint8_t value = static_cast<uint8_t>(pad);
  mcp_.digitalWrite(pins.a0, (value & 0x01) ? HIGH : LOW);
  mcp_.digitalWrite(pins.a1, (value & 0x02) ? HIGH : LOW);
  mcp_.digitalWrite(pins.a2, (value & 0x04) ? HIGH : LOW);
}

void Max328Router::set_enable_mask(uint8_t mask) {
  enable_mask_ = mask & kEnableAll;
  apply_enable_mask();
}

uint8_t Max328Router::enable_mask() const { return enable_mask_; }

void Max328Router::apply_enable_mask() {
  mcp_.digitalWrite(kU1Pins.en, (enable_mask_ & kEnableIp) ? HIGH : LOW);
  mcp_.digitalWrite(kU2Pins.en, (enable_mask_ & kEnableIm) ? HIGH : LOW);
  mcp_.digitalWrite(kU3Pins.en, (enable_mask_ & kEnableVp) ? HIGH : LOW);
  mcp_.digitalWrite(kU4Pins.en, (enable_mask_ & kEnableVm) ? HIGH : LOW);
}

void Max328Router::write_all() {
  // Build the full 16-bit port value and write in one I2C transaction
  uint16_t port_value = 0;

  auto set_bits = [&](const ChipPins &pins, Pad pad, bool enabled) {
    uint8_t value = static_cast<uint8_t>(pad);
    if (enabled) port_value |= (1 << pins.en);
    if (value & 0x01) port_value |= (1 << pins.a0);
    if (value & 0x02) port_value |= (1 << pins.a1);
    if (value & 0x04) port_value |= (1 << pins.a2);
  };

  set_bits(kU1Pins, state_.ip, enable_mask_ & kEnableIp);
  set_bits(kU2Pins, state_.im, enable_mask_ & kEnableIm);
  set_bits(kU3Pins, state_.vp, enable_mask_ & kEnableVp);
  set_bits(kU4Pins, state_.vm, enable_mask_ & kEnableVm);

  mcp_.writeGPIOAB(port_value);
}

Adafruit_MCP23X17 &Max328Router::mcp() { return mcp_; }
