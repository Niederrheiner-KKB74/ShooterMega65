# Stage 9 – Level 2 "Canyon und Raffinerie"

Branch `stage9`, based on `stage8c-stable` plus PR #17 and #18 (artwork). Release files are in `releases/stage9/`.
Design details: `docs/design.md` §22.

## What is new
- **Level 2**: desert approach, canyon with river and two bridges, oasis with outposts, oil refinery (map and
  graphics by ChatGPT). 40 destroyable buildings with their own ruins plus refinery hall tiles, 24 tanks,
  20 guns, 74 enemy waves (same aircraft as level 1, denser).
- **Boss 2**: the land cruiser, with four turrets, animated tracks and an engine room that opens when the
  turrets are gone. Same hit points as the level-1 boss. It drives only along its tracks: down and up, then it
  stops, turns on the spot (second view with horizontal tracks, PR #19) and drives sideways to the player's
  position, stops, turns back, and so on (1 px/frame, 1.5 in the core phase).
- **More colour in level 2** (PR #19): reeds, bushes, grass and palm groves along the water, salt flats, red scree,
  dark boulders; more green in the palette.
- **Level change**: after the end shop of level 1 the level-clear fanfare plays and level 2 starts. Score, lives,
  credits and everything bought are kept. After level 2, level 1 comes again.
- **Music**: new level-2 piece "Desert Heat" (oriental scale).
- **Palms** along the river and around the oasis (119, placed by `tools/decorate_level2.py`).
- **Shot IV**: the bar is narrower (5 px instead of 8; a normal bolt is 3 px).
- **Title screen: key 2** starts directly in level 2 (to test it without playing level 1).
- New files on the D81: `L2GFX`, `L2DAT`, `L2DEST`, `L2BOSS`, `MUS2`. Loading takes a little longer (everything
  goes into attic RAM at start). Without attic RAM there is only level 1, as before.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 17 files read back; PRG ends at `$A560` (music at `$AC00`) | ✔ |
| XEMU: key 2 on the title starts level 2 | ✔ |
| XEMU short level 1 → level 2 starts (desert, ruins, tank, armoured planes; screenshot), level-2 music piece set, RRB overflow 0 | ✔ |
| XEMU full level 1 (weak boss, no shops) → level 2, score and credits kept (game frame 13,199) | ✔ |
| XEMU level-2 boss: land cruiser with tracks and turrets (screenshot); weak boss destroyed, afterwards the fighter/bomber glyphs identical to `PIXIES` | ✔ |
| XEMU land cruiser: drives down/up, stops, turns (side view on screen), drives sideways to the player, turns back; with a moving test pilot the weak boss is destroyed and all 229 aircraft glyphs (fighters to armoured planes) are identical to `PIXIES` afterwards | ✔ |
| XEMU level-1 boss unchanged; without attic RAM (`NO_ATTIC`) level 1 runs | ✔ |
| Found and fixed in XEMU: a label mix-up made the boss event of level 2 restart the event list endlessly | ✔ |
| Real MEGA65 | ✔ all checklist items confirmed by the owner (04.11.2026), `stage9-stable`; level 2 difficulty OK with upgrades from level 1; the 90° turns of the land cruiser look abrupt (next stage) |

## Hardware test checklist
1. Loading: the title appears (a few seconds later than before).
2. Key 2 on the title: the game starts in the desert with the level-2 music.
3. Level 2: canyon with river and bridges, tanks stay off the water, buildings turn into recognisable ruins, guns,
   oasis, refinery; mid shop and end shop.
4. Boss 2 (land cruiser): drives only along its tracks, stops and turns before it changes between up/down and
   sideways; tracks move, turrets aim and fire, engine room opens, explodes; afterwards all aircraft (also
   helicopters and armoured planes) look normal.
5. Playing level 1 to the end: after the end shop and the fanfare, level 2 starts; score, lives, credits and
   upgrades are kept.
6. Game over in level 2 → title → new game starts in level 1 (with the level-1 music and boss).
7. Is level 2 a bit harder than level 1, but fair?
8. Palms along the river and around the oasis.
9. Shot IV: the bar is narrower than before but clearly wider than a normal bolt.
10. Everything else as in Stage 8c.
