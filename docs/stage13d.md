# Stage 13d – Level 3: moving sea and tall wind turbines (PR #24)

Branch `stage13b` (PR #24 merged), release files in `releases/stage13d/`. Includes Stages 13b and 13c.

## What is new
- **Colour cycling of the sea**: the water palette has a wave band (indices 9–12) that rotates every 9 frames
  (`cycle_frame` in `anim.asm`, data in `animations.json` → `LnDAT` header +26..29). Wave lines run over all open
  water and the surf. The glitter tile animation is gone (replaced by the cycling).
- **Wind turbines twice as high** (32×64) on pylons in the water, drawn in the water palette with water around them
  (no grey square); only the rotor is animated.
- Ship positions recomputed for the new wind farm map (`design_waves_l3.py`: 27 speedboats, 13 patrol boats,
  7 frigates, 10 guns).

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level3_art.py` | OK, no errors (124 tiles, cycling 9–12 every 9 frames) |
| Assembly; D81 read back | ✔ |
| XEMU: wave pattern on the water, wind farm with tall turbines, rotor phases change, enemies and ships | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 3: the waves move over the sea smoothly, not too hectic; the surf moves; reefs, oil films, buoys stay calm.
2. Wind turbines look tall, stand in the water without a grey square, the rotors turn.
3. Ships still find their way through the wind farm.
4. Everything else as in Stage 13c.
