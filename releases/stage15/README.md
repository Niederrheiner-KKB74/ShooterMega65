# Stage 15 – level transition, diagonal shots, art review

`SHOOTER65.D81` contains `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `PIXIES2`, `PIXIES3`, `TITLE`, `GOVER`,
`L1GFX`, `L1DAT`, `L1DEST`, `L1BOSS`, `L2GFX`, `L2DAT`, `L2DEST`, `L2BOSS`, `L3GFX`, `L3DAT`, `L3DEST`, `L3BOSS`,
`L4GFX`, `L4DAT`, `L4DEST`, `L4BOSS`, `ENEM0`, `ENEM3`, `ENEM4`, `SPRITES`, `MUS2`, `MUS3`, `MUS4`, `TRANS`.
`LOAD "SHOOTER",8` then `RUN`.
On the title screen: fire = level 1, keys 2/3/4 = levels 2/3/4, F during play = full equipment (test aid).
`MUSICTEST`: keys 1–6 play the pieces, T = 440 Hz, X = BASIC.

Rebuild from the sources of the commit that added this folder (branch `stage15`):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Test build with the transition 5 s into the game: `python3 tools/build.py --define TRANS_TEST`.

Notes and hardware checklist: `docs/stage15.md`. Status: assembled and tested in XEMU; hardware test by the owner
open. Needs attic RAM for the bosses, the further levels and the transition.
