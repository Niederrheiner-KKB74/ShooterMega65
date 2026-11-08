# Stage 17 – third phase of the final boss, boss colours after a bomb

Branch `stage17` (from `stage16`, after the owner confirmed Stage 16b), release files in `releases/stage17/`.

## What is new
- **Boss colours after a bomb** (owner's finding): the end of the bomb flash restored all palettes from the level,
  including the two banks that hold the boss palette during the fight, so parts of the boss turned red. Now the
  boss palette is set again after the flash (all bosses).
- **Level-4 final boss, phase 3** (owner's design): when the mech's core is destroyed, the mech explodes and an
  armoured **sphere** rolls out of the wreck.
  - It rolls through the upper half of the screen, bounces off the edges, changes direction every 1–2 s and fires
    fans of five red shots.
  - Every 3–4 s it stops, its iris hatch opens, the core pulses with warning beeps (1 s), then it fires a **stream
    of fire** in the direction of the player (aimed when the stream starts, about 0.7 s).
  - Afterwards the hatch stays open for about 2 s: **only now** the glowing core can be hit (also by bombs). Then
    it closes and rolls on.
  - 180 hit points; when the core is destroyed the sphere explodes and the level is clear (MISSION ACCOMPLISHED).
  - Losing the plane restarts at the checkpoint before the boss, with the mech again.
- Test define `BALL_TEST`: the boss comes at once (with `START_LEVEL4`, and `BOSS_TEST` for weak parts).

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$A808`; overlay area still large enough); D81 read back | ✔ |
| XEMU `BALL_TEST` + `BOSS_TEST` + level 4: mech destroyed → sphere appears, rolls, opens, core pulses, fire stream aimed at the plane, core hit while open, sphere explodes → LEVEL CLEAR | ✔ |
| Bomb colours | not tested in XEMU (no bombs in the test run); hardware test |
| Real MEGA65 | open |

## Hardware test checklist
1. Any boss: drop a bomb: after the flash the boss keeps its colours.
2. Level 4 (key 4 on the title, F for full equipment): destroy the mech: explosions, then the sphere rolls out.
3. Sphere: rolling animation, bouncing, fans of shots; stop, hatch opens, warning beeps, stream of fire towards
   the plane; can it be hit only while open? Does a bomb hurt it only while open?
4. Difficulty with full equipment: too easy / too hard? (Hit points, open time and shot rates are easy to change.)
5. Sphere destroyed: explosions, LEVEL CLEAR, MISSION ACCOMPLISHED.
6. Bomb during the sphere: colours stay right.
