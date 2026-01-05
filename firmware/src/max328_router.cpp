#include "max328_router.h"

#include <ctype.h>

const Max328Router::ChipPins Max328Router::kChipLPlus = {26, 27, 28};
const Max328Router::ChipPins Max328Router::kChipLMinus = {29, 24, 25};
const Max328Router::ChipPins Max328Router::kChipVPlus = {18, 19, 20};
const Max328Router::ChipPins Max328Router::kChipVMinus = {1, 0, 6};

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

Max328Router::Max328Router() : state_{Pad::A, Pad::A, Pad::A, Pad::A}, cfg_id_(0) {}

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
}

void Max328Router::apply_state(const RouterState &state, uint8_t cfg_id) {
  state_ = state;
  cfg_id_ = cfg_id;

  set_chip(kChipLPlus, state.ip);
  set_chip(kChipLMinus, state.im);
  set_chip(kChipVPlus, state.vp);
  set_chip(kChipVMinus, state.vm);

  delay(kSettleDelayMs);
}

const RouterState &Max328Router::state() const { return state_; }

uint8_t Max328Router::cfg_id() const { return cfg_id_; }

void Max328Router::set_chip(const ChipPins &pins, Pad pad) {
  uint8_t value = static_cast<uint8_t>(pad);
  digitalWrite(pins.a0, (value & 0x01) ? HIGH : LOW);
  digitalWrite(pins.a1, (value & 0x02) ? HIGH : LOW);
  digitalWrite(pins.a2, LOW);
}
