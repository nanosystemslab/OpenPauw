#include "test_mode.h"

TestMode::TestMode(Max328Router &router)
    : router_(router),
      active_(false),
      auto_run_(false),
      interval_ms_(500),
      last_ms_(0),
      pad_index_(0),
      enable_index_(0),
      last_pad_index_(0),
      last_enable_index_(0),
      prev_state_{Pad::A, Pad::A, Pad::A, Pad::A},
      prev_cfg_id_(0),
      prev_enable_mask_(Max328Router::kEnableAll) {}

void TestMode::begin() { last_ms_ = millis(); }

void TestMode::start(uint32_t interval_ms) { begin_if_needed(true, interval_ms); }

void TestMode::step_once() { begin_if_needed(false, interval_ms_); }

void TestMode::stop() {
  if (!active_) {
    return;
  }
  active_ = false;
  auto_run_ = false;
  router_.set_enable_mask(prev_enable_mask_);
  router_.apply_state(prev_state_, prev_cfg_id_);
}

void TestMode::update() {
  if (!active_ || !auto_run_) {
    return;
  }
  uint32_t now = millis();
  if (now - last_ms_ < interval_ms_) {
    return;
  }
  last_ms_ = now;
  apply_current();
  advance();
}

bool TestMode::active() const { return active_; }

bool TestMode::auto_run() const { return auto_run_; }

uint32_t TestMode::interval_ms() const { return interval_ms_; }

Pad TestMode::current_pad() const {
  return static_cast<Pad>(last_pad_index_);
}

uint8_t TestMode::current_enable_mask() const {
  return static_cast<uint8_t>(1 << last_enable_index_);
}

void TestMode::begin_if_needed(bool auto_run, uint32_t interval_ms) {
  if (!active_) {
    prev_state_ = router_.state();
    prev_cfg_id_ = router_.cfg_id();
    prev_enable_mask_ = router_.enable_mask();
    pad_index_ = 0;
    enable_index_ = 0;
    last_pad_index_ = 0;
    last_enable_index_ = 0;
    last_ms_ = millis();
    active_ = true;
  }
  auto_run_ = auto_run;
  interval_ms_ = interval_ms;
  apply_current();
  advance();
}

void TestMode::apply_current() {
  last_pad_index_ = pad_index_;
  last_enable_index_ = enable_index_;

  Pad pad = static_cast<Pad>(pad_index_);
  RouterState state{pad, pad, pad, pad};

  router_.set_enable_mask(0);
  router_.apply_state(state, 0);
  router_.set_enable_mask(static_cast<uint8_t>(1 << enable_index_));

  const char *en_name = "MULTI";
  if (enable_index_ == 0) {
    en_name = "IP";
  } else if (enable_index_ == 1) {
    en_name = "IM";
  } else if (enable_index_ == 2) {
    en_name = "VP";
  } else if (enable_index_ == 3) {
    en_name = "VM";
  }
  Serial.print("TEST STEP PAD=");
  Serial.print(pad_to_char(pad));
  Serial.print(" EN=");
  Serial.println(en_name);
}

void TestMode::advance() {
  enable_index_++;
  if (enable_index_ >= 4) {
    enable_index_ = 0;
    pad_index_++;
    if (pad_index_ >= 4) {
      pad_index_ = 0;
    }
  }
}
