# Stage 18c – fixes: tanks in the forest, sea in an island, sound effects after Game Over

`SHOOTER65.D81` contains `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `SPRITES`, `PIXIES2`, `PIXIES3`, `TITLE`,
`GOVER`, `HIMENU`, `L4BALL`, `L1GFX`–`L4BOSS` (level packs and bosses), `ENEM0`, `ENEM3`, `ENEM4`, `MUS2`, `MUS3`, `MUS4`, `TRANS`.
The game writes `SH65HI.DAT` (and later `SH65HI.BAK`) to this disk; keep the disk writable.
`LOAD "SHOOTER",8` then `RUN`. On the title: fire = level 1, keys 2/3/4 = levels 2/3/4; during play F = full
equipment (test aid). `MUSICTEST`: keys 1–6 play the pieces, T = 440 Hz, X = BASIC.

Rebuild from the sources of the commit that added this folder (branch `stage18`):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
The level-3 sea is made by `assets/art/level3/source/claude_sea.py` (already applied to the committed art and map),
the sphere, wreck and flame frames by `assets/art/boss-level4/source/claude_ball.py`.
Test builds: `--define BALL_TEST` (the boss at once; with `--define START_LEVEL4 --define BOSS_TEST` the sphere
quickly), `--define START_LEVEL3 --define SKIP_SHOP` (level 3 at once).

Notes and hardware checklist: `docs/stage18c.md`. Status: assembled and tested in XEMU; hardware test by the owner
open. Needs attic RAM.

The new level-1 and level-2 art is made by `assets/art/coastal-base/source/claude_terrain.py` and
`assets/art/level2/source/claude_desert.py` (already applied to the committed art and maps).
