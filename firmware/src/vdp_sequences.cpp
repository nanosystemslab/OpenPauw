#include "vdp_sequences.h"

static const VdpConfig kConfigs[] = {
    {1, {Pad::A, Pad::B, Pad::C, Pad::D}},
    {2, {Pad::B, Pad::A, Pad::D, Pad::C}},
    {3, {Pad::B, Pad::C, Pad::D, Pad::A}},
    {4, {Pad::C, Pad::B, Pad::A, Pad::D}},
};

const VdpConfig *find_vdp_config(uint8_t cfg_id) {
  for (const auto &cfg : kConfigs) {
    if (cfg.cfg_id == cfg_id) {
      return &cfg;
    }
  }
  return nullptr;
}

bool get_vdp_config(uint8_t cfg_id, RouterState &out_state) {
  const VdpConfig *cfg = find_vdp_config(cfg_id);
  if (!cfg) {
    return false;
  }
  out_state = cfg->state;
  return true;
}
