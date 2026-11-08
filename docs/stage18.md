# Stage 18 – enemies also fire upwards

Branch `stage18` (from `stage17-stable`), release files in `releases/stage18/`.

## What is new
- Planes, tanks and boats: when the plane is above them, they fire upwards - at half the rate of their downward
  fire and always with red bolts (2-3 px per frame, slight drift towards the plane, like the downward shots).
- Ground guns: they already turned towards the plane above them, but their shots flew downwards; now they fire
  upwards, aimed, also at half the rate.
- Bosses unchanged.

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$AC3E`), D81 read back | ✔ |
| XEMU level 1, plane held at the top edge (`GOD_MODE`): red bolts fly up at 2 px per frame towards the plane | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Levels 1-4: above the middle of the screen the plane is no longer safe; is the upward fire fair (half rate)?
2. Ground guns in all levels: shots towards a plane above them fly up and are aimed.
3. Upward bolts look right (slanted views mirrored), disappear above the screen, are cleared by a bomb.
4. Bosses fire as before.
