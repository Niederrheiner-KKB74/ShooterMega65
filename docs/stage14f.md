# Stage 14f – the drone's hull rolls with the banking

Branch `stage14`, release files in `releases/stage14f/`. Includes Stages 14c–14e.

## What is new
- **Heavy drone**: when it banks, the hull now rolls with the rotors: the top deck gets narrower and slides towards
  the lowered side, the raised side shows its ribbed side wall, the deck turns towards the light when it rolls left
  (brighter) and away from it when it rolls right (darker); plate, stripes, eye and guns sit on the deck; on the
  lowered side the missile pod disappears under the hull and the gun barrel is foreshortened.

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level4_art.py`; assembly; D81 read back | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 4: in curves the whole drone (rotors and hull) looks tilted.
2. Stage 14e points (cheat F) and 14c/14d.
