# Stage 8c – boss core phase slower, heavy flak 50, credit cheat

`SHOOTER65.D81` contains `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `PIXIES2`, `TITLE`, `GOVER`, `L1GFX`, `L1DAT`, `L1DEST`,
`L1BOSS`. `LOAD "SHOOTER",8` then `RUN`. `MUSICTEST`: keys 1–6 play the pieces, T = 440 Hz test tone, X = BASIC.

Rebuild from the sources of the commit that added this folder (branch `stage8`):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Notes and hardware checklist: `docs/stage8.md` (section Stage 8c). Status: assembled and tested in XEMU; hardware test by the owner open. Needs attic RAM for the boss.
