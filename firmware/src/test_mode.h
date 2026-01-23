#pragma once

#include <Arduino.h>

#include "max328_router.h"

class TestMode {
 public:
  explicit TestMode(Max328Router &router);

  void begin();
  void start(uint32_t interval_ms = 500);
  void step_once();
  void stop();
  void update();

  bool active() const;
  bool auto_run() const;
  uint32_t interval_ms() const;
  Pad current_pad() const;
  uint8_t current_enable_mask() const;

 private:
  Max328Router &router_;
  bool active_;
  bool auto_run_;
  uint32_t interval_ms_;
  uint32_t last_ms_;
  uint8_t pad_index_;
  uint8_t enable_index_;
  uint8_t last_pad_index_;
  uint8_t last_enable_index_;
  RouterState prev_state_;
  uint8_t prev_cfg_id_;
  uint8_t prev_enable_mask_;

  void begin_if_needed(bool auto_run, uint32_t interval_ms);
  void apply_current();
  void advance();
};
