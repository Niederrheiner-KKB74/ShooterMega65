# Stage 14c – fixes: scrolling after dying at the boss, calmer drone

Branch `stage14`, release files in `releases/stage14c/`.

## Fixes
- **Dying at the boss after the mid shop**: the level restarted after the shop, but the landscape stood still (the
  boss had stopped the scrolling and the restart did not switch it back on), so no enemies came. Now the restart
  first resets the boss (glyphs, palette, scrolling) and sets the level's scroll speed again.
- **Heavy drone** (level 4): the red eye no longer blinks; the rotors no longer flicker (only two blade glints
  orbit each hub); banking no longer changes the rotor sizes, the lowered side is only a little darker.
- Test aid: builds with `SKIP_SHOP` keep the mid-level checkpoint.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 read back | ✔ |
| XEMU (test level: mid shop, then the boss): plane lost at the boss → restart after the shop, scrolling at 0.5 px/frame again, the boss comes again; lost again → same | ✔ |
| Drone animation: 32 pixels change per phase (was about 107), no red pixel changes | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 4: lose a plane at the boss → the game continues after the mid shop, scrolls, enemies come, the boss
   comes again.
2. The same before the mid shop → the level starts from the beginning.
3. Heavy drone: no blinking, rotors turn calmly.
4. The rest of the Stage 14/14b checklists.
