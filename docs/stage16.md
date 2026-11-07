# Stage 16 – high-score list, title cycle, MISSION ACCOMPLISHED, second missile

Branch `stage16` (from `stage15`, after `stage15-stable`), release files in `releases/stage16/`.

## What is new
- **High-score list** with 10 entries (name up to 10 characters, score, level reached), saved on the game disk as
  `SH65HI.DAT`. The previous list is kept as `SH65HI.BAK`. The save uses Vyper's disk transaction from Vyper
  Stage 10a6 unchanged (temporary file, read back and checked, then renamed). A damaged file is never written over.
  Without a file the game starts with a default list (VIPER 50,000 … NOVA 2,500).
- **Name entry** after game over or after the end of the mission when the score enters the list: NEW HIGH SCORE!
  with the list and the new place in gold. Keyboard (letters, digits, space . - !, DEL, RETURN) or joystick
  (up/down letter, left/right position, fire = OK). Then the screen is black for a moment while the list is saved,
  and the list appears with "SAVED ON DISK" (or a red message if that was not possible).
- **Title**: the title picture (with title music) and, every 10 seconds, the **Hall of Fame** under the Shooter65
  logo. Fire or keys 2/3/4 start the game from both.
- **End of the mission**: after the level-4 boss, LEVEL CLEAR as before, then (no end shop) a fade to black and
  **MISSION ACCOMPLISHED** with the final score; fire → name entry if the score qualifies → title.
- **Second missile** in the shop (cell 7, $400, two missiles in the icon). It can be bought after the first missile.
  Then two homing missiles can be in flight at once, alternately from the left and right wing. Key F now gives
  both missiles. (The label is "MISSILE" again: "MISSILE II" would need more shop glyphs than there is room for.)
- **Memory**: the menu code (high scores, pages, name entry, disk access; 5 KB) is an overlay that is swapped in
  from attic RAM only while no game runs. BASIC's text screen is saved at start and restored on exit, which corrects a
  Stage 15 oversight: the transition used that area without saving it. Bank 0 now ends at `$A333` (2.2 KB free).

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$A333`, guard `$AC00`; overlay 5,057 of 5,630 bytes); D81 read back | ✔ |
| XEMU: title → Hall of Fame after 10 s (default list) | ✔ |
| XEMU `HI_TEST`: game over with 31,250 → NEW HIGH SCORE, name typed on the keyboard → SAVED ON DISK; `SH65HI.DAT` on the image is valid | ✔ |
| XEMU: second run with that disk: list loaded, another entry, `SH65HI.BAK` = previous list | ✔ |
| XEMU: name entered with the joystick ("BA") | ✔ |
| XEMU `TRANS_TEST` + level 4: LEVEL CLEAR → MISSION ACCOMPLISHED (fade in) → title | ✔ |
| XEMU: two missiles in flight with key F | ✔ |
| XEMU: X after the Hall of Fame → BASIC screen intact | ✔ |
| Real MEGA65 (above all the disk save and the KERNAL session) | open |

XEMU is not authoritative for disk access; the save is the main point of this hardware test.

## Hardware test checklist
1. Start: title with music; after about 10 s the Hall of Fame (default list), then the picture again.
2. Lose a game with more than 2,500 points: name entry. Try the keyboard and the joystick. RETURN or fire.
3. Short black screen, then the list with your name in gold and "SAVED ON DISK".
4. Switch off, start again: is your entry in the Hall of Fame? (The disk now holds `SH65HI.DAT`; after a second
   entry also `SH65HI.BAK`.)
5. Play through level 4 (keys 4 and F help): after LEVEL CLEAR comes MISSION ACCOMPLISHED with the final score,
   then the name entry (level shown as ALL).
6. Shop: the second missile (cell 7) is dimmed until the first one is bought; afterwards two missiles fly.
7. X on the title: back to BASIC with an intact screen.
8. A write-protected or full disk should give a red "DISK ERROR - NOT SAVED" message and nothing else.
