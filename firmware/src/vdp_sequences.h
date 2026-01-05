#pragma once

#include "max328_router.h"

struct VdpConfig {
  uint8_t cfg_id;
  RouterState state;
};

const VdpConfig *find_vdp_config(uint8_t cfg_id);
bool get_vdp_config(uint8_t cfg_id, RouterState &out_state);
