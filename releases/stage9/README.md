# Stage 9 – Level 2 "Canyon und Raffinerie"

`SHOOTER65.D81` contains `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `PIXIES2`, `TITLE`, `GOVER`, `L1GFX`, `L1DAT`,
`L1DEST`, `L1BOSS`, `L2GFX`, `L2DAT`, `L2DEST`, `L2BOSS`, `MUS2`. `LOAD "SHOOTER",8` then `RUN`.
On the title screen: fire = level 1, key 2 = level 2. `MUSICTEST`: keys 1–6 play the pieces, T = 440 Hz, X = BASIC.

Rebuild from the sources of the commit that added this folder (branch `stage9`):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Notes and hardware checklist: `docs/stage9.md`. Status: assembled and tested in XEMU; hardware test by the owner open. Needs attic RAM for the boss and level 2.
