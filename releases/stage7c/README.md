# Stage 7c – boss aims, tanks on land, new waves, boss data in attic RAM

`SHOOTER65.D81` contains `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `TITLE`, `GOVER`, `L1GFX`, `L1DAT`,
`L1BOSS`. `LOAD "SHOOTER",8` then `RUN`. `MUSICTEST`: keys 1–6 play the pieces, T = 440 Hz test tone, X = BASIC.

Rebuild from the sources of the commit that added this folder (branch `stage7`):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Notes and hardware checklist: `docs/stage7.md` (section Stage 7c). Status: confirmed on real hardware by the owner (02.11.2026), tag `stage7c-stable`. Needs attic RAM for the boss.
