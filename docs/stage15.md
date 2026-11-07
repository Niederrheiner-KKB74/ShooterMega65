# Stage 15 – level transition, diagonal enemy shots, art review

Branch `stage15` (from `stage14`, after `stage14-stable`), release files in `releases/stage15/`.

## What is new
- **Level transition** (`src/transition.asm`, pictures from `tools/make_overlays.py`):
  1. Boss destroyed → victory fanfare; about 1 s later (the plane cannot be hit meanwhile) the game pauses.
  2. **LEVEL CLEAR!** in the middle of the screen with a burnt picture of the destroyed boss (built from the boss
     artwork, darkened, scorched, with fires and smoke) and a blinking **PRESS FIRE TO CONTINUE**.
  3. Fire → the end shop as before (it used to follow the boss after a few rows of scrolling).
  4. Leaving the shop → the screen fades to black (about 0.6 s); the next level is set up behind the black screen.
  5. **PREPARE FOR LEVEL n** with a blinking PRESS FIRE TO CONTINUE on the black screen.
  6. Fire → the level fades in and starts with its music.
  After level 4, "PREPARE FOR LEVEL 1" follows for now (the end screen comes with Stage 16).
- **Diagonal enemy shots**: red bolts and fireballs that fly at an angle of about 24° or more are shown turned by
  45° (down-left or down-right) instead of upright. New file `PIXIES3` (11 glyphs at `$55200`).
- **Level-2 ground targets redrawn** (tent, radar mast, command post, crates, oil tank, pump jack, workshop, loading
  bay, chimney): all seen from above and slightly from the south, with the south wall visible, light from the top
  left and a shadow to the lower right, like the level-4 buildings. The tent is a ridge tent with two roof slopes,
  the entrance on the south gable and guy ropes. Each target has a designed wreck.
- **Level-3 ground targets redrawn** the same way (drilling derrick, crane, radar mast, tank, lighthouse,
  containers, control building, quarters) on the platform deck plating.
- **Level-3 enemies redrawn** in the grey-steel/red style of levels 1 and 4: seaplane with floats and red
  cowling, naval helicopter (dark blue-grey with yellow band, 4-blade rotor), speedboat with V wake, patrol boat and
  frigate (bridge, funnel, radar, helicopter deck, gun rings under the gun objects, wake animation).

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$A939`, guard `$AC00`); D81 read back | ✔ |
| `tools/check_level2_art.py`, `tools/check_level3_art.py` | OK, no errors |
| XEMU `TRANS_TEST`: LEVEL CLEAR (level-1 boss picture) → shop → fade out → PREPARE FOR LEVEL 2 → fade in → level 2 plays | ✔ |
| XEMU level 4 (`GOD_MODE`, weak boss): mech destroyed → LEVEL CLEAR with the mech picture | ✔ |
| XEMU level 4: aimed red bolts shown diagonally, fireballs at small angles upright | ✔ |
| XEMU levels 2 and 3: new targets and level-3 enemies on screen, frigate guns on their rings | ✔ |
| Real MEGA65 | open |

The palette fade uses MEGA65 palette 2 (`$D070`), which was not used before: please watch the fades closely.

## Hardware test checklist
1. Beat a boss (key F helps): fanfare, then LEVEL CLEAR with the boss picture; does PRESS FIRE TO CONTINUE blink?
2. Fire → shop as usual, buying works, EXIT.
3. Fade to black: smooth, no flash of the old or new level, no wrong colours?
4. PREPARE FOR LEVEL n with the right number, text blinks; fire → the level fades in smoothly, music starts, HUD and
   player normal, colour cycling of the sea (level 3) runs.
5. Try it from all four bosses (keys 2/3/4 on the title); after level 4 comes PREPARE FOR LEVEL 1.
6. Enemy shots fired at an angle are drawn diagonally.
7. Level 2: does the tent look like a tent seen obliquely from above? Do the other targets and their wrecks look
   right? Level 3: the targets on the platforms, and the new seaplanes, helicopters and ships.
