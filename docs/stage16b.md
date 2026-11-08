# Stage 16b – fixes after the hardware test of Stage 16

Branch `stage16`, release files in `releases/stage16b/`. Everything else as in `docs/stage16.md`.

## Owner's findings and fixes
- **MISSION ACCOMPLISHED: random pixels blinking in the bottom line.** Cause: the fade-in uses `$0800–$0BFF` as work
  RAM (`fade_tab`, `pal_snap`), where the menu pages keep their font. The page text is drawn before the fade, the
  blinking PRESS FIRE TO CONTINUE after it, with the overwritten font. Fix: the font is copied back after the fade.
- **No chance to enter a name: fire saves at once.** Fire meant "done" (letters with up/down). Now arcade style:
  - up/down chooses the letter (a new position starts with A; down from A gives `>` at once),
  - **fire accepts the letter and moves to the next position**,
  - fire on `>` ends the entry, fire on `<` goes back one position; after the 10th letter the entry ends by itself,
  - left/right move the cursor; the keyboard works as before (letters, DEL, RETURN).
  Help line: `UP/DOWN: LETTER  FIRE: NEXT  >: END`. `<`/`>` are never saved (replaced by spaces).

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 read back | ✔ |
| XEMU `HI_TEST`: up (B), fire, down twice (`<`), fire = back; fire, down (`>`), fire = done → "B" saved | ✔ |
| XEMU `TRANS_TEST` + level 4: MISSION ACCOMPLISHED, PRESS FIRE TO CONTINUE blinks cleanly, score with six digits | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Game over with a new high score: enter a name with the joystick (up/down, fire for each letter, `>` + fire to
   finish). Saved, and still there after switching off?
2. Name with the keyboard (RETURN to finish).
3. End of level 4: MISSION ACCOMPLISHED without stray pixels; the line PRESS FIRE TO CONTINUE blinks cleanly.
4. The rest of the Stage 16 checklist (`docs/stage16.md`), if not done yet.
