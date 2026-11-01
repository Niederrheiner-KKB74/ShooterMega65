# Stage 7 – Boss, title screen, game over

Branch `stage7`, based on `stage6-stable` plus PR #14 (artwork). Release files are in `releases/stage7/`.
Design details: `docs/design.md` §18 (boss) and §19 (title, game over).

## What is new
- **Title screen** "Shooter65" (PR #14) with title music, blinking "PRESS FIRE" and the high score. Fire starts a game.
- **Level-1 boss**: a quadrotor gunship at the end of the level (after the last wave, before the end shop). The
  landscape stops, boss music plays. Four turrets aim at the player and must be destroyed first (1,000 points
  each); then the core opens and fires faster (5,000 points). Missile and bomb work on the boss (the bomb takes
  20 hit points from every part instead of destroying it). Touching the boss costs shield.
- **Game over**: banner (PR #14) over the stopped game with the score; fire (after 1 s) or 5 s → title screen,
  where the high score is updated. Then a new game from the start of the level.
- **Music**: two new pieces by Claude: "Shooter65 Theme" (title, D major) and "Quadrotor" (boss, E minor, 150 BPM).
  `MUSICTEST`: keys 1–6 = level, shop, game over, level clear, boss, title; T = 440 Hz.
- New files on the D81: `TITLE`, `GOVER`, `L1BOSS`. Title and banner are kept in attic RAM (MEGA65 R3 and
  later). Without attic RAM the title appears only at the start and game over is a small box.
- Test builds: `build.py --define BOSS_TEST` (weak boss), `--define ONE_LIFE`, `--define NO_ATTIC`,
  `--test-credits`.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 10 files read back; `L1DAT` + `L1BOSS` = 16,273 of 16,384 bytes | ✔ |
| XEMU: title screen at start, "PRESS FIRE" blinks, fire starts the game | ✔ |
| XEMU boss test level: boss enters, scrolling stops, turrets lose hit points and show their destroyed view, core opens (memory dumps), RRB overflow 0 | ✔ |
| XEMU weak boss: explosions, 9,000 points, scrolling resumes | ✔ |
| XEMU one life: game-over banner with score 700, title shows HIGH SCORE 000700, fire starts a new game from the level start | ✔ |
| XEMU without attic RAM (`NO_ATTIC`): title at start, "GAME OVER" box, new game directly | ✔ |
| XEMU full level with the (weak) boss at row 358, both shops, into the second pass (frame 16,831), RRB overflow 0; afterwards the fighter/bomber glyph area is byte-identical to `PIXIES` | ✔ |
| XEMU audio: boss and title music recorded (`docs/audio/`) | ✔ |
| Real MEGA65 | ✔ all checklist items confirmed by the owner (01.11.2026), `stage7-stable` |

## Hardware test checklist
1. `RUN`: after loading the title screen appears with the title music; "PRESS FIRE" blinks; HIGH SCORE 000000.
   Fire starts the game.
2. At the end of the level (after about 3:50) the sky clears, the landscape stops and the boss flies in with its
   own music. Rotors turn, turrets turn towards the player (south, south-east, south-west) and fire with a flash.
3. Destroyed turrets show their wreck; after the fourth one the core opens (blue) and fires orange shots.
   Missile and bomb hurt the boss. Flying into the boss costs shield.
4. Core destroyed: explosions, the boss disappears, the landscape moves on, level music, then the end shop and the
   level-clear fanfare. In the next round the fighters and bombers look normal again (no boss pieces).
5. Lose all planes: the game-over banner shows your score; fire (or 5 s) → title with the new high score →
   fire → a new game from the start.
6. Losing the last plane during the boss fight: game over, title and the new game look right.
7. `MUSICTEST`: keys 5 and 6 play the boss and the title music.
8. X returns to BASIC (also on the title and game-over screens).
