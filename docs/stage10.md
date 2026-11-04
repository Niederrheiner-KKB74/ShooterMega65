# Stage 10 – smoother turns of the land cruiser

Branch `stage10`, based on `stage9-stable` plus PR #20 (artwork). Release files are in `releases/stage10/`.
Design details: `docs/design.md` §22.

## What is new
- The land cruiser (boss of level 2) no longer jumps between its two views. A turn now takes 36 frames:
  12 frames standing in the old view, then 24 frames in a new **diagonal view** (front down-left) with **dust
  clouds** at the ends of the tracks and a short rumble, then the new view. The centre of the boss stays in place.
- The turrets sit on their places of the diagonal view and keep firing during the turn; in the end phase the open
  engine room is shown in the diagonal view, too.
- Inside: the boss graphics now use 323 of the 324 glyphs of the aircraft area.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 17 files read back; PRG ends at `$A860` (music at `$AC00`) | ✔ |
| XEMU level-2 boss: sideways → diagonal (x − 16, dust on screen) → driving down (y + 16), RRB overflow 0 | ✔ |
| XEMU weak level-2 boss destroyed (moving test pilot); afterwards all 323 aircraft glyphs identical to `PIXIES` | ✔ |
| XEMU level-1 boss unchanged; default game runs, RRB overflow 0 | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Key 2 on the title, fly to the boss (or play level 2 to the end).
2. The land cruiser stops, then turns through the diagonal view with dust clouds and drives on in the other
   direction. The turn should look like a movement, not a jump.
3. Turrets and engine room are in the right places in all three views; shots still hit them.
4. After the boss all aircraft look normal; level 1 boss unchanged.
5. Everything else as in Stage 9.
