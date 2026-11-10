# Stage 19 – Shot IV as four bolts, the drone

Branch `stage19` (from Stage 18c, confirmed on hardware), release files in `releases/stage19/`.

## What is new
- **Shot IV:** four thin bolts like Shot I-III, the middle two a little further forward (was a thick bar). Damage
  as before.
- **Drone (shop, $300, cell 8 "DRONE"):** a small satellite circles the plane (about 1.3 s per turn). Enemy shots
  that touch it vanish; enemy planes it touches are damaged and destroyed after a few contacts (with points).
  Bosses, guns and tanks are not affected. It stays until the plane is destroyed; then it can be bought again.
- **Shop:** "EXTRA LIFE" is now called "LIFE" (the panel had no glyphs left for the new item).
- Technical: the pixie glyphs moved up by 2 glyphs, the music data by 64 bytes (room for the shop and the code).

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$AE2D`, music from `$AE40`); shop 162 glyphs; D81 read back | ✔ |
| XEMU level 1 with `SHOT4`: four bolts, middle two in front | ✔ |
| XEMU level 1 with `DRONE_TEST`: the drone circles the plane, an enemy plane is destroyed by it (points) | ✔ |
| XEMU level 4 with `BALL_TEST`: mech, wreck, sphere, flame column unchanged after the pixie move | ✔ |
| Shop panel (preview image): DRONE in cell 8, LIFE | ✔ |
| Buying the drone, losing it with a life, shots caught | not played through in XEMU; hardware test |
| Music after the move | not listened to (XEMU not authoritative); hardware test |
| Real MEGA65 | open |

## Hardware test checklist
1. Shop: DRONE in the third row, $300; bought once, then greyed out until the plane is lost.
2. The drone circles the plane smoothly, also at the screen edges; its colours are right.
3. Enemy shots that touch the drone vanish; enemy planes that touch it are damaged / destroyed (points).
4. A life lost: the drone is gone, it can be bought again in the next shop.
5. Shot IV: four thin bolts, middle two in front; hits as before.
6. All enemies, explosions, the HUD and all four bosses look as before (pixie glyphs moved).
7. Music and sound effects as before (music data moved).
