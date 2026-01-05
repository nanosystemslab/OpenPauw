#include "protocol.h"

#include <ctype.h>

#include "vdp_sequences.h"

Protocol::Protocol(Max328Router &router) : router_(router) {}

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

  if (upper == "HELP") {
    print_help();
    return;
  }

  if (upper == "STATE?") {
    print_state();
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
  Serial.println("CFG n (1-4) -> apply preset");
  Serial.println("SET ip im vp vm (A-D) -> apply routing");
  Serial.println("STATE? -> report current state");
  Serial.println("HELP -> this message");
}
