# Stage 16b – fixes: name entry (arcade style), MISSION ACCOMPLISHED line

`SHOOTER65.D81` contains `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `SPRITES`, `PIXIES2`, `PIXIES3`, `TITLE`,
`GOVER`, `HIMENU`, `L1GFX`–`L4BOSS` (level packs and bosses), `ENEM0`, `ENEM3`, `ENEM4`, `MUS2`, `MUS3`, `MUS4`, `TRANS`.
The game writes `SH65HI.DAT` (and later `SH65HI.BAK`) to this disk; keep the disk writable.
`LOAD "SHOOTER",8` then `RUN`. On the title: fire = level 1, keys 2/3/4 = levels 2/3/4; during play F = full
equipment (test aid). `MUSICTEST`: keys 1–6 play the pieces, T = 440 Hz, X = BASIC.

Rebuild from the sources of the commit that added this folder (branch `stage16`, Stage 16b):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Test builds: `--define HI_TEST` (game over after 5 s with 31,250 points), `--define TRANS_TEST` (level transition
after 5 s; with `--define START_LEVEL4` the end of the mission).

Notes and hardware checklist: `docs/stage16b.md` (and `docs/stage16.md`). Status: assembled and tested in XEMU; hardware test by the owner
open. Needs attic RAM.
