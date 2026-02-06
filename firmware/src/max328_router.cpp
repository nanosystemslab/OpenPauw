#include "max328_router.h"

#include <ctype.h>

// Address pins: A0=D10(GP10), A1=D11(GP11), A2=D12(GP12) (shared across all chips)
const Max328Router::ChipPins Max328Router::kChipLPlus = {10, 11, 12};
const Max328Router::ChipPins Max328Router::kChipLMinus = {10, 11, 12};
const Max328Router::ChipPins Max328Router::kChipVPlus = {10, 11, 12};
const Max328Router::ChipPins Max328Router::kChipVMinus = {10, 11, 12};
// Enable pins: U1=D9(GP9), U2=D6(GP8), U3=D5(GP7), U4=D4(GP6)
// Order is {IP, IM, VP, VM} which maps to {U1, U2, U3, U4}
const Max328Router::EnablePins Max328Router::kEnablePins = {9, 8, 7, 6};

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
  pinMode(kChipLPlus.a0, OUTPUT);
  pinMode(kChipLPlus.a1, OUTPUT);
  pinMode(kChipLPlus.a2, OUTPUT);

  pinMode(kChipLMinus.a0, OUTPUT);
  pinMode(kChipLMinus.a1, OUTPUT);
  pinMode(kChipLMinus.a2, OUTPUT);

  pinMode(kChipVPlus.a0, OUTPUT);
  pinMode(kChipVPlus.a1, OUTPUT);
  pinMode(kChipVPlus.a2, OUTPUT);

  pinMode(kChipVMinus.a0, OUTPUT);
  pinMode(kChipVMinus.a1, OUTPUT);
  pinMode(kChipVMinus.a2, OUTPUT);

  if (kUseEnablePins) {
    pinMode(kEnablePins.ip, OUTPUT);
    pinMode(kEnablePins.im, OUTPUT);
    pinMode(kEnablePins.vp, OUTPUT);
    pinMode(kEnablePins.vm, OUTPUT);
  }

  apply_enable_mask();
}

void Max328Router::apply_state(const RouterState &state, uint8_t cfg_id) {
  state_ = state;
  cfg_id_ = cfg_id;

  if (kUseEnablePins) {
    uint8_t prev_mask = enable_mask_;
    enable_mask_ = 0;
    apply_enable_mask();
    delay(1);
    enable_mask_ = prev_mask;
  }

  set_chip(kChipLPlus, state.ip);
  set_chip(kChipLMinus, state.im);
  set_chip(kChipVPlus, state.vp);
  set_chip(kChipVMinus, state.vm);

  apply_enable_mask();
  delay(kSettleDelayMs);
}

const RouterState &Max328Router::state() const { return state_; }

uint8_t Max328Router::cfg_id() const { return cfg_id_; }

void Max328Router::set_chip(const ChipPins &pins, Pad pad) {
  uint8_t value = static_cast<uint8_t>(pad);
  digitalWrite(pins.a0, (value & 0x01) ? HIGH : LOW);
  digitalWrite(pins.a1, (value & 0x02) ? HIGH : LOW);
  digitalWrite(pins.a2, (value & 0x04) ? HIGH : LOW);
}

void Max328Router::set_enable_mask(uint8_t mask) {
  enable_mask_ = mask & kEnableAll;
  apply_enable_mask();
}

uint8_t Max328Router::enable_mask() const { return enable_mask_; }

void Max328Router::apply_enable_mask() {
  if (!kUseEnablePins) {
    return;
  }

  auto to_level = [](bool enabled) -> uint8_t {
    if (kEnableActiveHigh) {
      return enabled ? HIGH : LOW;
    }
    return enabled ? LOW : HIGH;
  };

  digitalWrite(kEnablePins.ip, to_level(enable_mask_ & kEnableIp));
  digitalWrite(kEnablePins.im, to_level(enable_mask_ & kEnableIm));
  digitalWrite(kEnablePins.vp, to_level(enable_mask_ & kEnableVp));
  digitalWrite(kEnablePins.vm, to_level(enable_mask_ & kEnableVm));
}
