# Stage 2 – Artwork v2, HUD, shield and bonus items

Branch `stage2`, based on PR #2–#4 (reference board, aircraft integration, artwork v2) on top of
`stage1-stable`. Release files are in `releases/stage2/`.

## What is new
- **Artwork v2** from `assets/art/spec-v2` is imported at build time by `tools/import_art.py`:
  example level (62 tiles, 4 landscape palettes, 512 px long, repeats), player (6 frames: exhaust
  animation, banking left/right), fighter, helicopter, bomber, armoured plane (3 animation frames each),
  player and enemy shots, rocket, small and big explosions (6 frames). Every object type has its own palette bank.
  The importer checks that the converted map reproduces `level-example.png` pixel for pixel.
- **HUD** at the top: 6-digit score on the left, shield bar on the right (green → yellow → red).
- **Shield** instead of instant death: contact with enemy planes or enemy shots costs shield points
  depending on the enemy kind (table in `docs/design.md` §6). After a hit the plane blinks for 1 s and cannot
  be hit. At 0 it explodes and a new game starts after 3 s.
- **Enemies** have hit points: bombers and armoured planes need several hits. Points per kind.
- **Bonus items** (green capsule, placeholder art) refill 16 shield points: dropped when a whole formation was
  shot down, and always by an armoured plane.
- Formations alternate: 6 fighters, 3 bombers, 6 helicopters, 3 armoured planes.
- **Raster time display** is now off by default; **D** switches it on and off (red border band).

Still placeholder or missing: the tank (old placeholder art; no tank in artwork v2), the bonus capsule,
lives, title/game-over screens, the special weapon (space bar is read but does nothing yet), destructible
bunkers and flak (they are part of the landscape for now).

## Build and start
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
`LOAD "SHOOTER",8` and `RUN`. Joystick port 2, fire = shoot, D = raster display, X or RUN/STOP = back to BASIC.

## Verification so far
| Check | Result |
|---|---|
| Importer: map reproduces `level-example.png`, palettes without colour reduction, 189 of 256 pixie glyphs | ✔ |
| Assembly, PRG < `$C000`, D81 read-back | ✔ |
| XEMU (ROM 920395): new graphics, HUD, scoring, shield loss, bonus capsule, player explosion, restart after 3 s, RRB overflow 0 | ✔ |
| XEMU: RUN → X → `READY.` → RUN → X → `READY.` | ✔ |
| **Real MEGA65** | **open – please test** |

## Hardware test checklist
1. The HUD stays still at the top while the landscape scrolls; no jitter and no garbage next to the boxes.
2. Colours of all object types look like `assets/art/spec-v2/generated/preview-all.png`.
3. The player shows the exhaust animation and banks left/right with the joystick.
4. Bombers and armoured planes (32×32) are drawn completely, including at the screen edges.
5. Being hit: the shield bar shrinks and changes colour, the plane blinks; at 0 it explodes, after 3 s a new game starts
   with score 0 and a full shield.
6. Shoot down a whole formation: a green capsule appears; collecting it refills the shield.
7. D shows the red raster band; note how big it gets with many objects on screen.
8. Exit with X / RUN/STOP and `RUN` again work as in Stage 1.
