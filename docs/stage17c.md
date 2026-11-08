# Stage 17c – level-3 sea: narrower crests, slower, whitecaps

Branch `stage17` (after the owner's verdict on Stage 17b: final boss very good, sea still looked like a blinking
area on the big screen), release files in `releases/stage17c/`.

## What is new
- **Narrower crests:** about 11 px apart instead of 22, still diagonal.
- **Calmer animation:** 5 softer colours (bright crest, crest edge, base, shadow, base) instead of 6 with strong
  contrast; one step every 12 frames instead of 9. Less of the surface changes its colour per step.
- **Whitecaps:** small white flecks on the crests flash up and fade when a crest passes them, in two different
  rhythms (every 2nd and every 3rd crest), scattered over about one sea cell in ten at random, so they form no grid.
- Technical: level header 40 bytes; the music data moved from `$AC00` to `$AE00` (room for the program).

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$AC00`, music from `$AE00`); `MUSICTEST`; D81 read back; `check_level3_art.py` (249 of 256 map rows) | ✔ |
| XEMU level 3: narrower crests, cycling, whitecaps invisible when off and flashing scattered on the crests | ✔ (screenshots) |
| Music after the move (all levels, shop, title) | not listened to in XEMU (XEMU is not authoritative for audio); hardware test |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 3: does the sea now look like water moving, not like a blinking area? Speed right? (Step every 12 frames:
   `period` in `animations.json`; crest spacing and colours in `claude_sea.py`.)
2. Whitecaps: visible, not too many / too few, no regular pattern? (Share `CAP_SHARE` 0.13, size 4–6 px.)
3. Coasts, wakes, buoys, wind turbines as in Stage 17b.
4. After a bomb in level 3: the sea cycles on normally.
5. Music: title, shop, all four levels, boss, LEVEL CLEAR, game over play as before (music data moved).
6. Levels 1, 2 and 4 unchanged (they have no colour cycling or only level 3's).
