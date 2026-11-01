# Stage 4 – Special weapons

Branch `stage4`, based on `stage3b-stable` plus PR #10. Release files are in `releases/stage4/`.
Design details: `docs/design.md` §16.

## What is new
- **Bomb** (space): uses one bomb from the HUD counter. Every enemy on the screen explodes (with points and
  capsules), enemy shots disappear, the landscape flashes briefly.
- **Invulnerability** (S): uses one from the HUD counter, 10 seconds without damage. A shimmering blue/white
  ring around the plane shows it; it blinks during the last 2 seconds. Pressing S again while it runs does
  nothing (nothing is used up).
- **Homing missile** (bought once): while fire is held, a missile starts whenever none is under way and an
  enemy is visible. It flies towards a randomly chosen enemy and hits for the current shot level.
- **Capsules** fall at 1.5 px per frame (before: 0.5, as fast as the landscape), so they are harder to collect
  (`BONUS_VY` in `objects.asm`).
- **Shop**: icons for EXTRA LIFE and EXIT (PR #10). **Level**: denser coastal level with 44 formations and
  16 tanks, new scenery (PR #10).

## Verification so far
| Check | Result |
|---|---|
| Assembly, D81 with `SHOOTER`, `SHOP`, `L1GFX`, `L1DAT` read back | ✔ |
| XEMU, shop test build (999 credits): buy missile, invulnerability, bomb; S shows the ring, counter goes down, ring gone after 10 s; missile hits an enemy away from the gun line; space destroys all enemies on screen with flash, counter goes down | ✔ |
| XEMU, release build with fire held: dense level, no RRB overflow at 40 s and 75 s | ✔ |
| XEMU, full level with fire held and scripted EXIT in both shops: past the level end into the second pass (frame 16,805, scroll 8,402 px), RRB overflow 0 | ✔ |
| XEMU, capsule speed measured: 75 px in 50 frames (landscape: 25 px) | ✔ |
| Real MEGA65 | ✔ all checklist items confirmed by the owner (01.11.2026), `stage4-stable` |

## Hardware test checklist
1. Buy SHIELD, BOMB and MISSILE in the mid-level shop (about 2 minutes in).
2. Press **S**: the ring appears behind the plane and shimmers (colours run around it), the counter goes down.
   No damage from enemies or shots for 10 seconds; the ring blinks at the end and disappears. S while the ring
   is active does not use up another one.
3. Press **space** with enemies on the screen: all of them explode, enemy shots vanish, short flash, points
   and capsules appear, the counter goes down. Without bombs nothing happens.
4. Hold fire: a missile starts, flies to an enemy (also off the gun line) and destroys it or damages it. Only
   one missile at a time.
5. The ring sprites and the plane look right at the left and right screen edges.
6. Capsules fall clearly faster than the landscape and can still be caught.
7. Shop: EXTRA LIFE and EXIT show their new icons. The denser level runs without slowdown or flicker.
8. X returns to BASIC; sprites and colours in BASIC look normal afterwards.
