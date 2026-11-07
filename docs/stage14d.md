# Stage 14d – new heavy walker (level 4)

Branch `stage14`, release files in `releases/stage14d/`. Includes the Stage 14c fixes (restart after dying at the
boss scrolls again, calmer drone).

## What is new
- The **heavy walker** of level 4 is redrawn by Claude (`assets/art/enemies-level4/source/claude_walker.py`): an
  armoured hull with side stripes, sensor slit and headlights, a turret ring under the gun, and four armoured legs
  with knee joints. The feet step in a smooth **four-phase cycle** (diagonal pairs move together, the lifted feet
  lighter with a shadow) instead of two jumpy phases; nothing blinks any more. New burning wreck frame.
- The frigate/walker slots now hold 4 phases (the frigate repeats its 2 phases).

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level4_art.py` | OK, no errors |
| Assembly; D81 read back | ✔ |
| XEMU level 4: walkers walk down the streets with their gun on top | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 4: the walkers look like heavy four-legged machines and walk smoothly, nothing blinks.
2. The gun sits on the turret ring and turns, fires; the walker dies after 30 hits.
3. Level 3: frigates unchanged.
4. Stage 14c points: restart after dying at the boss; drone.
