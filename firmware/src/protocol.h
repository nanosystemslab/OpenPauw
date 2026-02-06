#pragma once

#include <Arduino.h>

#include "max328_router.h"

#define FIRMWARE_VERSION "1.3.0"

class TestMode;
class SwitchValidator;

class Protocol {
 public:
  explicit Protocol(Max328Router &router, TestMode *test_mode = nullptr,
                    SwitchValidator *switch_validator = nullptr);
  void begin();
  void update();

 private:
  Max328Router &router_;
  TestMode *test_mode_;
  SwitchValidator *switch_validator_;
  String line_;

  void handle_line(const String &line);
  int split_tokens(const String &line, String *tokens, int max_tokens);
  bool parse_pad_token(const String &token, Pad &pad);
  bool parse_uint32(const String &token, uint32_t &value);
  void print_state();
  void print_ok_set(const RouterState &state);
  void print_help();
  void print_test_status();
};
