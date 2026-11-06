# Stage 14 – Level 4 „Operation Iron City“ and checkpoints

Branch `stage14`, based on `stage13d-stable` plus PR #25 (artwork and map by ChatGPT). Release files in
`releases/stage14/`. End screen, high-score table with names and the new title page follow in Stage 15.

## What is new
- **Level 4** after level 3: ruined city with streets, industry, city centre and fortress; music „Iron City“.
  Key **4** on the title starts level 4 directly (test aid).
- **Own enemies**: modern jets, attack helicopters, quadrocopter drones (they fly the bomber formations),
  small mechs that walk only on the streets, heavy walkers (30 hits, one gun) coming down the streets.
- **Final boss: combat mech**. It stomps across the square (legs step only while it walks, dust at the feet),
  four weapons, flame-thrower arm in the core phase (like the hover tank), drones start from its back
  (like the carrier's jets).
- **Lost plane: the level restarts** – from its start, or after the mid-level shop once that was reached. The shot
  level drops by one (Shot IV → III …); everything else bought stays. Buildings destroyed after the checkpoint stay
  destroyed.
- Inside: the player sprite frames are a file (`SPRITES`) instead of part of the program: 3 KB more room for code.

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level4_art.py` (PR #25) | OK, no errors (117 tiles, enemy set 202/324 + 48/48, boss 237/324) |
| Assembly; D81 read back; PRG ends at `$A004` | ✔ |
| XEMU level 4: map, jets, drones, mechs on the streets, walkers with gun, guns | ✔ |
| XEMU mech boss: walking with leg animation and dust, weapons, chest opens, flame jet, destroyed; glyphs afterwards equal `ENEM4` | ✔ |
| XEMU lost plane (3 → 2 lives): level 3 starts again from its beginning, shot level 3 → 2 | ✔ |
| XEMU restart after the mid shop | not tested (code path only) |
| Real MEGA65 | open |

## Hardware test checklist
1. Key 4 starts level 4; levels 1–3 unchanged; after level 3 comes level 4, after level 4 level 1 (end screen in
   Stage 15).
2. Level 4: animations (fires, smoke, lights); jets, helicopters, drones look right; mechs keep to the streets;
   walkers carry a gun that aims and fires.
3. Mech boss: legs move only while it walks; dust at the feet; weapons, chest, flame, drones; destruction.
4. Lose a plane before the mid shop: the level starts from the beginning. Lose one after the mid shop: it goes on
   right after the shop. The shot level drops by one each time; shop, bombs etc. stay.
5. Music of level 4 („Iron City“).
6. Difficulty of level 4.
