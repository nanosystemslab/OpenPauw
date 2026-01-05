#pragma once

#include <Arduino.h>

#include "max328_router.h"

class Protocol {
 public:
  explicit Protocol(Max328Router &router);
  void begin();
  void update();

 private:
  Max328Router &router_;
  String line_;

  void handle_line(const String &line);
  int split_tokens(const String &line, String *tokens, int max_tokens);
  bool parse_pad_token(const String &token, Pad &pad);
  void print_state();
  void print_ok_set(const RouterState &state);
  void print_help();
};
