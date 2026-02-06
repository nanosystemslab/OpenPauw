#include "vdp_sequences.h"

// Van der Pauw configurations for sample orientation:
//   A/1------------------------------C/3
//   |                                 |
//   |                                 |
//   B/2------------------------------D/4
//
// RouterState order: {ip, im, vp, vm} = {I+, I-, V+, V-}
//
// Config 1: I: B->C, V: A-D  (I+=C, I-=B, V+=A, V-=D)
// Config 2: I: C->B, V: D-A  (reverse polarity of 1)
// Config 3: I: A->D, V: B-C  (perpendicular)
// Config 4: I: D->A, V: C-B  (reverse polarity of 3)
static const VdpConfig kConfigs[] = {
    {1, {Pad::C, Pad::B, Pad::A, Pad::D}},  // I: B->C, V: A-D
    {2, {Pad::B, Pad::C, Pad::D, Pad::A}},  // I: C->B, V: D-A
    {3, {Pad::D, Pad::A, Pad::B, Pad::C}},  // I: A->D, V: B-C
    {4, {Pad::A, Pad::D, Pad::C, Pad::B}},  // I: D->A, V: C-B
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
