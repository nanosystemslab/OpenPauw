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
  static constexpr uint8_t kEnableIp = 1 << 0;
  static constexpr uint8_t kEnableIm = 1 << 1;
  static constexpr uint8_t kEnableVp = 1 << 2;
  static constexpr uint8_t kEnableVm = 1 << 3;
  static constexpr uint8_t kEnableAll = kEnableIp | kEnableIm | kEnableVp | kEnableVm;

  Max328Router();
  void begin();
  void apply_state(const RouterState &state, uint8_t cfg_id);
  const RouterState &state() const;
  uint8_t cfg_id() const;
  void set_enable_mask(uint8_t mask);
  uint8_t enable_mask() const;

 private:
  struct ChipPins {
    uint8_t a0;
    uint8_t a1;
    uint8_t a2;
  };

  struct EnablePins {
    uint8_t ip;
    uint8_t im;
    uint8_t vp;
    uint8_t vm;
  };

  static const ChipPins kChipLPlus;
  static const ChipPins kChipLMinus;
  static const ChipPins kChipVPlus;
  static const ChipPins kChipVMinus;
  static const EnablePins kEnablePins;

  static constexpr bool kUseEnablePins = true;
  static constexpr bool kEnableActiveHigh = true;

  RouterState state_;
  uint8_t cfg_id_;
  uint8_t enable_mask_;

  void set_chip(const ChipPins &pins, Pad pad);
  void apply_enable_mask();
};
