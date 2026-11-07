# Stage 14h – final boss: real legs, straight flame

Branch `stage14`, release files in `releases/stage14h/`. Includes Stage 14g.

## What is new
- **Legs of the boss mech**: four real legs beside the hull instead of growing and shrinking circles. Each leg
  (32×48): hip housing on a strut from the hull, knee, shin with piston, a wide foot pad with claws. Stepping: planted
  (dust at the pad) → lifted (foot higher and lighter, shadow on the ground) → coming down; diagonal pairs alternate,
  only while it walks. The legs are drawn before the body (`bd_rotors`, legged bosses only), so the hip housings
  cover their tops; the front legs are in front of the rear legs.
- **Flame**: a straight column of fire with flickering edges instead of stacked cones; the segments of the jet join
  seamlessly, the short tip is rounded.
- The hull is 64 px wide in a 112-px body frame (turrets, reactor hatch, missile rack as before).

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level4_art.py` | OK, no errors (boss 237/324) |
| Assembly; D81 read back | ✔ |
| XEMU boss: legs step while it walks, dust at the feet, straight flame column, missiles, turrets, hatch | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Is the boss clearly a four-legged mech? Do the legs step only while it walks?
2. Does the flame look like a straight column?
3. The other bosses (levels 1–3) unchanged.
