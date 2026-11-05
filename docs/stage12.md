# Stage 12 – a dangerous flame thrower

Branch `stage12`, based on `stage11-stable`. Release files are in `releases/stage12/`. Design: `docs/design.md` §22.

## What is new
- The flame jet of the hover tank (level 2, core phase) now **shoots down like a shot**: after the warning it grows
  by one segment every 4 frames (6 px per frame) to five overlapping segments, about 128 px long, so it reaches the
  bottom of the screen.
- The jet lasts 80 frames (before: 50) and the tank **sweeps slowly towards the player** while it burns
  (0.5 px per frame; the player is faster and can dodge sideways).
- When it ends, the jet shrinks back from the tip (15 frames). Damage 12 per hit as before, along the whole length.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 read back | ✔ |
| XEMU: jet grows to five segments down to the player and sweeps towards him | ✔ |
| XEMU without `GOD_MODE`: a player standing still under the boss loses lives to the jet | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Key 2 on the title, play level 2 to the boss and destroy the four turrets.
2. After the flickering warning the jet shoots down quickly and reaches the bottom of the screen.
3. While it burns, the tank follows the player slowly; dodging sideways works.
4. The jet shrinks back from the tip; no flame remains after the boss is destroyed.
5. Difficulty: threatening, but fair?
