#pragma once

#include <Arduino.h>

enum Pad : uint8_t { A = 0, B = 1, C = 2, D = 3 };

struct RouterState {
  Pad ip;
  Pad im;
  Pad vp;
  Pad vm;
};

char pad_to_char(Pad pad);
bool parse_pad_char(char c, Pad &pad);

class Max328Router {
 public:
  static constexpr uint32_t kSettleDelayMs = 50;

  Max328Router();
  void begin();
  void apply_state(const RouterState &state, uint8_t cfg_id);
  const RouterState &state() const;
  uint8_t cfg_id() const;

 private:
  struct ChipPins {
    uint8_t a0;
    uint8_t a1;
    uint8_t a2;
  };

  static const ChipPins kChipLPlus;
  static const ChipPins kChipLMinus;
  static const ChipPins kChipVPlus;
  static const ChipPins kChipVMinus;

  RouterState state_;
  uint8_t cfg_id_;

  void set_chip(const ChipPins &pins, Pad pad);
};
