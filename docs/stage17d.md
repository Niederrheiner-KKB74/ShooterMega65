# Stage 17d – level-3 sea: finer crest lines

Branch `stage17` (after Stage 17c: music confirmed by the owner, sea much better, colour zones still a bit wide),
release files in `releases/stage17d/`.

## What is new
- The owner chose variant C of the second preview video with the fine crest line of variant D: crests about
  7.5 px apart (was 11), colour zones about 1.5 px (was 2.3); each wave is a bright line with a thin shadow behind
  it on almost even water. Whitecaps, speed (a step every 12 frames) and everything else as in Stage 17c.

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$AC00`); D81 read back; `check_level3_art.py` (249 of 256 map rows); tiles identical to preview variant C | ✔ |
| XEMU level 3: fine crest lines, cycling, whitecaps flashing | ✔ (screenshots) |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 3: does the sea look like the preview (variant C with fine lines) on the big screen? No flicker or moiré?
2. Whitecaps still visible on the narrower crests?
3. Coasts, wakes, buoys, wind turbines as before.
