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

# Stage 7b – boss feedback and difficulty, title fix

Branch `stage7`, on top of the confirmed Stage 7 (`stage7-release`). Release files are in `releases/stage7b/`.

## What changed
- **Title**: the shadow of "PRESS FIRE" now stays inside the blinking row, so no blue fragments remain.
- **Hit flash**: a turret or the core that is hit but not destroyed lights up for 4 frames (shots, missile and bomb).
- **Wrecks**: halfway through the death explosions the turret wrecks disappear with the body, each with an explosion.
- **Harder boss**: turrets 70 hit points (was 40), core 200 (was 120). The boss moves twice as fast sideways
  (1 px/frame, 2 px in the core phase) and also bobs up and down. Turrets fire more often, and the fewer are left, the
  faster they fire. The open core fires a fan of three shots (left, down, right).
- Fixed during the work: a label mix-up in the new drawing code froze the game at the start (found in XEMU before
  the release).

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 10 files read back | ✔ |
| XEMU title: row 23 has no non-background pixels in both blink phases | ✔ |
| XEMU boss test level (fire held, player not moving): the hit turret is drawn lightened (screenshot), `obj_a` counts down on turrets and core | ✔ |
| XEMU: boss x moves 1 px/frame and bounces, y bobs 20–44; core phase 2 px/frame; core fan: three shots with direction −1 / 0 / +1 | ✔ |
| XEMU weak boss (`BOSS_TEST`): at the halfway point of the explosions no boss parts are left; 9,000 points, scrolling resumes | ✔ |
| XEMU weak boss: turrets destroyed while it is still flying in → the core keeps descending to its fighting height | ✔ |
| XEMU full-strength boss, player standing still: after 65 s three turrets are left (one at 10 HP), the player loses all three planes → game-over banner, boss removed | ✔ |
| XEMU default level for 58 s after the start, RRB overflow 0 (also in all boss runs) | ✔ |
| Real MEGA65 | ✔ all checklist items confirmed by the owner (02.11.2026), `stage7b-stable`; balancing "clearly better" |

## Hardware test checklist
1. Title: "PRESS FIRE" blinks without any blue remains under the letters.
2. Boss: every hit on a turret or on the open core makes it light up briefly; also with missile and bomb.
3. The boss moves noticeably faster sideways and bobs up and down; turrets fire more often, faster when only one or
   two are left; the open core fires fans of three shots.
4. The fight takes clearly longer than in Stage 7 (turrets 70, core 200 hit points). Is the difficulty right?
5. After the core is destroyed: halfway through the explosions the body **and** the turret wrecks disappear.
6. Everything else as in the Stage 7 checklist (end shop, next round, game over during the boss fight, title).

# Stage 7c – boss aims, tanks on land, new waves, boss data in attic RAM

Branch `stage7`, on top of the confirmed Stage 7b (`stage7b-release`). Release files are in `releases/stage7c/`.

## What changed
- **Boss core phase**: besides the fans of three, the core fires a red shot every 0.4–1 s. Half of them are
  aimed exactly at the player, the others go off at a random angle. Hiding at the far left or right no longer works.
  Enemy shots can now fly at any angle (sideways speed in 1/16 px per frame).
- **Tanks** never drive into water (or onto the coast); they turn round in front of it.
- **New waves for level 1** (`tools/design_waves_l1.py`): 14 flight paths and 16 formations instead of 5. Loops,
  U-turns, fighters entering from the side, pincers (a formation and its mirror image together), V groups,
  helicopters that hover and shoot, bombers crossing diagonally, armoured planes that stop and fire. Up to 8 planes
  per formation, 57 formation events, 23 tanks at varied places. Map, shops and boss are unchanged.
- **Attic RAM**: the boss data (`L1BOSS`) are now kept in attic RAM and copied in by DMA when the boss arrives; the
  fighter and bomber glyphs are saved there and copied back afterwards. The 16 KB level buffer is free for level data
  (the new waves needed it). Without attic RAM there is no boss.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 10 files read back; `L1DAT` 7,143 bytes | ✔ |
| XEMU boss test level, player at the far left: core shots with many angles (sideways −64 … +52 in 1/16 px), aimed ones towards the player, the shield drops | ✔ |
| XEMU: boss graphics and palette from attic RAM correct (screenshot); after the boss the fighter/bomber glyphs are byte-identical to `PIXIES` | ✔ |
| XEMU without attic RAM (`NO_ATTIC`): the boss event is skipped, the game goes on | ✔ |
| XEMU: the land mask matches the screenshot water areas; tanks seen in the dumps all on land | ✔ |
| XEMU default level 78 s after the start with the new waves, RRB overflow 0 | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Boss core phase: besides the fans, single red shots at different angles, some aimed at you. Staying at the far
   left or right edge is no longer safe.
2. Tanks: none drives into the sea or onto the beach; they turn round in front of the water.
3. New waves: loops, U-turns, planes from the side, pincers from both sides, V groups, hovering helicopters, diagonal
   bombers, armoured planes that stop to shoot. Is it fun, too hard, too easy? Any flicker or missing planes?
4. Boss fight looks as before (graphics and colours), and after it the fighters and bombers look normal again.
5. Everything else as in the Stage 7 checklist.
