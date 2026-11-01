# Stage 7b – boss feedback and difficulty, title fix

`SHOOTER65.D81` contains `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `TITLE`, `GOVER`, `L1GFX`, `L1DAT`,
`L1BOSS`. `LOAD "SHOOTER",8` then `RUN`. `MUSICTEST`: keys 1–6 play the pieces, T = 440 Hz test tone, X = BASIC.

Rebuild from the sources of the commit that added this folder (branch `stage7`):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Notes and hardware checklist: `docs/stage7.md` (section Stage 7b). Status: assembled and tested in XEMU; hardware test by the owner open.
