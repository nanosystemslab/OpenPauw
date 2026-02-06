#include "protocol.h"

#include <ctype.h>
#include <stdlib.h>

#include "status_led.h"
#include "switch_validator.h"
#include "test_mode.h"
#include "vdp_sequences.h"

Protocol::Protocol(Max328Router &router, TestMode *test_mode,
                   SwitchValidator *switch_validator)
    : router_(router),
      test_mode_(test_mode),
      switch_validator_(switch_validator) {}

void Protocol::begin() { line_.reserve(80); }

void Protocol::update() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == '\r') {
      continue;
    }
    if (c == '\n') {
      String line = line_;
      line_ = "";
      line.trim();
      if (line.length() > 0) {
        handle_line(line);
      }
      continue;
    }
    if (line_.length() < 120) {
      line_ += c;
    }
  }
}

void Protocol::handle_line(const String &line) {
  String upper = line;
  upper.toUpperCase();

  if (upper == "PING") {
    Serial.println("PONG");
    return;
  }

  if (upper == "VERSION" || upper == "VER") {
    Serial.print("OpenPauw Firmware v");
    Serial.println(FIRMWARE_VERSION);
    return;
  }

  if (upper == "HELP") {
    print_help();
    return;
  }

  if (upper == "STATE?") {
    print_state();
    return;
  }

  if (upper == "TEST?") {
    if (!test_mode_) {
      Serial.println("ERR");
      return;
    }
    print_test_status();
    return;
  }

  if (upper == "CFGTEST") {
    if (!switch_validator_) {
      Serial.println("ERR NO_VALIDATOR");
      status_led.set_state(LedState::ERROR);
      return;
    }
    status_led.set_state(LedState::BUSY);

    // Get current router state and verify the routing
    const RouterState& state = router_.state();
    bool pass = switch_validator_->verify_config(
        static_cast<uint8_t>(state.ip),
        static_cast<uint8_t>(state.im),
        static_cast<uint8_t>(state.vp),
        static_cast<uint8_t>(state.vm));

    if (pass) {
      Serial.println("OK CFGTEST PASS");
      status_led.set_state(LedState::SWTEST_PASS);
    } else {
      Serial.println("ERR CFGTEST FAIL");
      status_led.set_state(LedState::SWTEST_FAIL);
    }
    return;
  }

  if (upper.startsWith("CFG")) {
    String tokens[2];
    int count = split_tokens(upper, tokens, 2);
    if (count == 2) {
      int cfg_id = tokens[1].toInt();
      RouterState state;
      if (cfg_id >= 1 && cfg_id <= 4 && get_vdp_config(cfg_id, state)) {
        router_.apply_state(state, static_cast<uint8_t>(cfg_id));
        Serial.print("OK CFG ");
        Serial.println(cfg_id);
        return;
      }
    }
    Serial.println("ERR");
    return;
  }

  if (upper.startsWith("ENMASK")) {
    String tokens[2];
    int count = split_tokens(upper, tokens, 2);
    uint32_t mask_value = 0;
    if (count == 2 && parse_uint32(tokens[1], mask_value) && mask_value <= 15) {
      router_.set_enable_mask(static_cast<uint8_t>(mask_value));
      Serial.print("OK ENMASK ");
      Serial.println(mask_value);
      return;
    }
    Serial.println("ERR");
    return;
  }

  if (upper.startsWith("SET")) {
    String tokens[5];
    int count = split_tokens(upper, tokens, 5);
    if (count == 5) {
      RouterState state;
      if (parse_pad_token(tokens[1], state.ip) &&
          parse_pad_token(tokens[2], state.im) &&
          parse_pad_token(tokens[3], state.vp) &&
          parse_pad_token(tokens[4], state.vm)) {
        router_.apply_state(state, 0);
        print_ok_set(state);
        return;
      }
    }
    Serial.println("ERR");
    return;
  }

  if (upper.startsWith("TEST")) {
    if (!test_mode_) {
      Serial.println("ERR");
      return;
    }
    String tokens[3];
    int count = split_tokens(upper, tokens, 3);
    if (count == 1 || (count >= 2 && tokens[1] == "ON")) {
      uint32_t interval_ms = test_mode_->interval_ms();
      if (count == 3) {
        uint32_t parsed = 0;
        if (!parse_uint32(tokens[2], parsed)) {
          Serial.println("ERR");
          return;
        }
        interval_ms = parsed;
      }
      test_mode_->start(interval_ms);
      Serial.println("OK TEST ON");
      print_test_status();
      return;
    }
    if (count == 2 && tokens[1] == "OFF") {
      test_mode_->stop();
      Serial.println("OK TEST OFF");
      return;
    }
    if (count == 2 && tokens[1] == "STEP") {
      test_mode_->step_once();
      Serial.println("OK TEST STEP");
      print_test_status();
      return;
    }
    Serial.println("ERR");
    return;
  }

  if (upper == "SWTEST") {
    if (!switch_validator_) {
      Serial.println("ERR NO_VALIDATOR");
      status_led.set_state(LedState::ERROR);
      return;
    }
    status_led.set_state(LedState::BUSY);
    SwitchValidator::ScanResult result = switch_validator_->scan();
    switch_validator_->print_result(result);
    Serial.println("OK SWTEST");

    // Set LED based on connection count
    if (result.connection_count == 0) {
      status_led.set_state(LedState::SWTEST_FAIL);  // Red - no connections
    } else if (result.connection_count == 16) {
      status_led.set_state(LedState::SWTEST_PASS);  // Green - expected full matrix
    } else {
      status_led.set_state(LedState::SWTEST_PARTIAL);  // Yellow - partial
    }
    return;
  }

  Serial.println("ERR");
}

int Protocol::split_tokens(const String &line, String *tokens, int max_tokens) {
  int count = 0;
  int i = 0;
  int len = line.length();

  while (i < len && count < max_tokens) {
    while (i < len && isspace(static_cast<unsigned char>(line[i]))) {
      i++;
    }
    if (i >= len) {
      break;
    }
    int start = i;
    while (i < len && !isspace(static_cast<unsigned char>(line[i]))) {
      i++;
    }
    tokens[count++] = line.substring(start, i);
  }
  return count;
}

bool Protocol::parse_pad_token(const String &token, Pad &pad) {
  if (token.length() != 1) {
    return false;
  }
  return parse_pad_char(token[0], pad);
}

bool Protocol::parse_uint32(const String &token, uint32_t &value) {
  char buf[16];
  size_t len = token.length();
  if (len == 0 || len >= sizeof(buf)) {
    return false;
  }
  token.toCharArray(buf, sizeof(buf));
  char *end = nullptr;
  value = static_cast<uint32_t>(strtoul(buf, &end, 10));
  return end && *end == '\0';
}

void Protocol::print_state() {
  const RouterState &state = router_.state();
  Serial.print("STATE CFG=");
  Serial.print(router_.cfg_id());
  Serial.print(" IP=");
  Serial.print(pad_to_char(state.ip));
  Serial.print(" IM=");
  Serial.print(pad_to_char(state.im));
  Serial.print(" VP=");
  Serial.print(pad_to_char(state.vp));
  Serial.print(" VM=");
  Serial.println(pad_to_char(state.vm));
}

void Protocol::print_ok_set(const RouterState &state) {
  Serial.print("OK SET IP=");
  Serial.print(pad_to_char(state.ip));
  Serial.print(" IM=");
  Serial.print(pad_to_char(state.im));
  Serial.print(" VP=");
  Serial.print(pad_to_char(state.vp));
  Serial.print(" VM=");
  Serial.println(pad_to_char(state.vm));
}

void Protocol::print_help() {
  Serial.println("PING -> PONG");
  Serial.println("VERSION -> firmware version");
  Serial.println("CFG n (1-4) -> apply VDP preset");
  Serial.println("CFGTEST -> verify current config routing");
  Serial.println("ENMASK m (0-15) -> enable mask for IP/IM/VP/VM");
  Serial.println("SET ip im vp vm (A-D) -> apply routing");
  Serial.println("STATE? -> report current state");
  Serial.println("TEST ON [ms] -> start test mode");
  Serial.println("TEST STEP -> advance one step");
  Serial.println("TEST OFF -> stop test mode");
  Serial.println("TEST? -> report test status");
  Serial.println("SWTEST -> scan full MAX328 matrix");
  Serial.println("HELP -> this message");
}

void Protocol::print_test_status() {
  if (!test_mode_) {
    Serial.println("TEST ACTIVE=0");
    return;
  }
  uint8_t mask = test_mode_->current_enable_mask();
  const char *line = "MULTI";
  if (mask == Max328Router::kEnableIp) {
    line = "IP";
  } else if (mask == Max328Router::kEnableIm) {
    line = "IM";
  } else if (mask == Max328Router::kEnableVp) {
    line = "VP";
  } else if (mask == Max328Router::kEnableVm) {
    line = "VM";
  } else if (mask == 0) {
    line = "NONE";
  }
  Serial.print("TEST ACTIVE=");
  Serial.print(test_mode_->active() ? 1 : 0);
  Serial.print(" AUTO=");
  Serial.print(test_mode_->auto_run() ? 1 : 0);
  Serial.print(" INTERVAL_MS=");
  Serial.print(test_mode_->interval_ms());
  Serial.print(" PAD=");
  Serial.print(pad_to_char(test_mode_->current_pad()));
  Serial.print(" EN=");
  Serial.println(line);
}
