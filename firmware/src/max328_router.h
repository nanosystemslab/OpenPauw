#pragma once

#include <Adafruit_MCP23X17.h>
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

  static constexpr uint8_t kMcpAddress = 0x20;

  // MCP23017 pin assignments per chip (EN, A0, A1, A2)
  // Port A: U1 (I+) and U2 (I-)
  // Port B: U3 (V+) and U4 (V-)
  struct ChipPins {
    uint8_t en;
    uint8_t a0;
    uint8_t a1;
    uint8_t a2;
  };

  static constexpr ChipPins kU1Pins = {0, 1, 2, 3};    // GPA0-3: I+
  static constexpr ChipPins kU2Pins = {4, 5, 6, 7};    // GPA4-7: I-
  static constexpr ChipPins kU3Pins = {8, 9, 10, 11};   // GPB0-3: V+
  static constexpr ChipPins kU4Pins = {12, 13, 14, 15}; // GPB4-7: V-

  Max328Router();
  void begin();
  void apply_state(const RouterState &state, uint8_t cfg_id);
  const RouterState &state() const;
  uint8_t cfg_id() const;
  void set_enable_mask(uint8_t mask);
  uint8_t enable_mask() const;

  Adafruit_MCP23X17 &mcp();

 private:
  Adafruit_MCP23X17 mcp_;
  RouterState state_;
  uint8_t cfg_id_;
  uint8_t enable_mask_;

  void set_chip(const ChipPins &pins, Pad pad);
  void apply_enable_mask();
  void write_all();
};
