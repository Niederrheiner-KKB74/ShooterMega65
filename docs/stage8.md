# Stage 8 – destroyable buildings and ground guns

Branch `stage8`, based on `stage7c-stable` plus PR #15 (artwork). Release files are in `releases/stage8/`.
Design details: `docs/design.md` §20.

## What is new
- **Destroyable buildings**: hangars, depots, checkpoints, bunkers, radar, tank farms, crate stacks and the big
  halls of the base can be shot to pieces. Shots fly over them (aircraft behind them can still be hit) and damage
  every building they cross. Destroyed buildings show the rubble of PR #15, explode and give points; depots,
  bunkers, tank farms and crates leave a capsule. Halls are destroyed tile by tile. The bomb destroys every
  building on the screen. In the next round of the level everything is intact again.
- **Ground guns**: light flak (16×16) and heavy double flak (32×32). They turn towards you in 45° steps, fire aimed
  shots when they point at you (the heavy one two at a time) with a muzzle flash, and stay as wrecks when
  destroyed (300 / 1,000 points). Shot, missile and bomb work on them. Level 1 has 19 guns, most of them in the
  second half (military road and base).
- New files on the D81: `PIXIES2` (heavy gun), `L1DEST` (destroyed tiles).
- Inside: the music moved to `$AC00` to give the program room; `LnDAT` may be up to 10 KB.
- Test builds: `--define GOD_MODE` (no damage), `--define SKIP_SHOP`, `--define BOSS_CORE_TEST`;
  `--test-credits` also gives 9 bombs.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 12 files read back; PRG ends at `$A260` (music at `$AC00`) | ✔ |
| XEMU audio: title and level music still play from `$AC00` | ✔ |
| XEMU test level (base first): halls and crates under the shots turn into rubble (screenshot), points counted; light and heavy guns turn towards the player and fire; flying under the heavy gun destroys it (wreck) | ✔ |
| XEMU bomb: every building on the screen destroyed at once (screenshot), no cell left in the override list | ✔ |
| XEMU `GOD_MODE` + weak boss: whole level 1 with buildings, guns and boss into the second round (game frame 15,899), RRB overflow 0; 4 more runs with different start times to game frame 9,369 | ✔ |
| XEMU without attic RAM (`NO_ATTIC`): game runs | ✔ |
| **Open**: in 1 of 11 long XEMU runs the game stopped at game frame 7,917 (military road, a light gun and armoured planes on screen) in the vblank wait; program code in memory was intact; not reproducible with the same or other input | ? |
| Real MEGA65 | ✔ all checklist items confirmed by the owner (03.11.2026), no freeze on hardware, `stage8-stable` |

## Hardware test checklist
1. From the middle of the level (after the mid shop) and in the base: shooting buildings turns them into rubble
   with an explosion and points; halls break tile by tile. The neighbouring tiles look unchanged.
2. Shots still hit aircraft that fly over buildings.
3. Depots, bunkers, tank farms and crates leave a capsule when destroyed.
4. The bomb destroys all buildings on the screen. Buildings that are only partly on the screen: half destroyed
   is expected.
5. Guns: they turn towards you, fire aimed shots with a muzzle flash, and stay as wrecks. Missile and bomb destroy
   them too. Is the number of guns and their aim right, too hard or too easy?
6. Music and sound effects as before (the music moved in memory).
7. Please watch for a freeze anywhere in the level (one XEMU run stopped once, see above) and tell me roughly
   where it happened.
8. Everything else as in the Stage 7 checklists (boss, shops, game over, title).

# Stage 8b – visible shot levels, balancing

Branch `stage8`, on top of the confirmed Stage 8 (`stage8-release`). Release files are in `releases/stage8b/`.

## What changed
- **Shots show their level**: one bolt without upgrade, two with SHOT II, three with SHOT III, a thick bar with
  SHOT IV. Every volley is now one object in the middle of the plane, with the damage of the former pair, so the
  boss fight stays as it is.
- **Less money**: $ capsules are worth 5 / 15 / 30 credits instead of 10 / 25 / 50 (S capsules unchanged).
- **Heavy flak** takes 60 hit points instead of 24.
- The heavy flak now uses the muzzle flash of the light flak (memory for the new shot views).

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 12 files read back; pixie area 573 of 576 glyphs | ✔ |
| XEMU test builds `SHOT2`–`SHOT4`: one, two, three bolts and the bar, centred on the plane (screenshot) | ✔ |
| XEMU `GOD_MODE` + weak boss: whole level, boss, into the second round (game frame 12,899), RRB overflow 0 | ✔ |
| XEMU player standing still: 65 credits at the mid shop, 210 for the whole level | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Without upgrade one bolt; after SHOT II two, SHOT III three, SHOT IV a thick bar.
2. With SHOT II fighters still go down with one hit, bombers and armoured planes need several.
3. At the first shop you can no longer afford SHOT II and the missile together (unless you play very well).
4. Heavy flak takes clearly longer to destroy.
5. Boss fight as difficult as in Stage 8.
6. Everything else as in Stage 8.
