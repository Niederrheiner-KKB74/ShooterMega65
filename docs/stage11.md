# Stage 11 – the hover tank (boss of level 2)

Branch `stage11`, based on `stage10` plus PR #21 (artwork). Release files are in `releases/stage11/`.
Design details: `docs/design.md` §22. Stage 10 (diagonal turn of the land cruiser) was not tested on hardware and is
replaced by this stage.

## What is new
- The land cruiser is replaced by a **heavy hover tank**. It never turns: it glides freely in every direction over the
  place in front of the refinery, often towards the player's x position.
- **Dust** swirls up at the skirt while it glides (three phases, four places).
- Four turrets as before; then the reactor hatch opens. In this **core phase** it glides a little faster and uses its
  **flame thrower**: first a small flickering flame as a warning (harmless, the tank stops), then a jet downwards for
  about 1 second that damages the player on contact (12), then it fades out. Between two jets 1.6–3.6 seconds.
- The two big lift fans turn (the level-1 quadrotor keeps its four rotors).
- Inside: the boss graphics use 205 of the 324 glyphs; the turn code of the land cruiser is gone.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 17 files read back; PRG ends at `$A860` (music at `$AC00`) | ✔ |
| XEMU level-2 boss: enters, glides to changing targets with dust; turrets destroyed, hatch open, flame jet under the nozzle; boss destroyed, level continues | ✔ |
| XEMU after the level-2 boss: aircraft glyphs identical to `PIXIES` (only the HUD glyphs differ, as always) | ✔ |
| XEMU level-1 boss unchanged (four rotors, sideways flight, destruction, glyphs restored) | ✔ |
| Flame damage (XEMU tests ran with `GOD_MODE`) | open, hardware test |
| Real MEGA65 | open |

## Hardware test checklist
1. Key 2 on the title, play level 2 to the boss.
2. The hover tank flies in from the top and glides smoothly sideways and up/down; dust at the skirt while it moves,
   none while it stands; the two fans turn.
3. Turrets fire, flash when hit and are destroyed in place; then the hatch opens.
4. Core phase: before every jet a small flickering flame as a warning; the jet hurts when the player flies into it,
   not before and not beside it. Fair enough to dodge?
5. Destroying the boss: explosions, no remains; afterwards all aircraft look normal.
6. Level-1 boss unchanged; everything else as in Stage 9.
