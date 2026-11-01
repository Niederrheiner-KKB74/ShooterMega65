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
  be hit. At 0 it explodes.
- **Three lives** (HUD: plane icon + number next to the score). After 3 s the next plane starts with a full shield;
  after the last one a new game starts.
- **Tanks** from PR #6: four driving directions with animated tracks; they turn at the edges and at random.
- **Animations** (PR #7): exhaust flames for the player and the planes, rotor for the helicopter. The first
  artwork frames were different drawings and made the objects jump (`docs/img/stage2_frame_variants.png`);
  the new loops change only the flame/rotor pixels.
- **Capsules** (PR #7): "S" = +16 shield (whole formation shot down), "$" in three sizes = 10 / 25 / 50 credits
  (tank / bomber / armoured plane). Credits are shown in the middle of the HUD.
- **Enemies** have hit points: bombers and armoured planes need several hits. Points per kind.
- Formations alternate: 6 fighters, 3 bombers, 6 helicopters, 3 armoured planes.
- **Raster time display** is now off by default; **D** switches it on and off (red border band).

Still missing: a use for the credits, title/game-over screens, the special weapon (space bar is read but does nothing yet), destructible
bunkers and flak (they are part of the landscape for now).

## Build and start
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
`LOAD "SHOOTER",8` and `RUN`. Joystick port 2, fire = shoot, D = raster display, X or RUN/STOP = back to BASIC.

## Verification so far
| Check | Result |
|---|---|
| Importer: map reproduces `level-example.png`, palettes without colour reduction, 259 of 512 pixie glyphs, no frame-variant warnings | ✔ |
| Assembly, PRG < `$C000`, D81 read-back | ✔ |
| XEMU (ROM 920395): new graphics, HUD, scoring, shield loss, bonus capsule, player explosion, restart after 3 s, RRB overflow 0 | ✔ |
| XEMU after the hardware feedback: steady sprites, lives (3 → 2, full shield, score kept), tanks in all directions | ✔ |
| XEMU with PR #7: player flame animation, credits box, "$" capsule collected (+50), RRB overflow 0 | ✔ |
| XEMU: RUN → X → `READY.` → RUN → X → `READY.` | ✔ |
| **Real MEGA65** | ✔ all checklist items confirmed by the owner (01.11.2026), `stage2-stable` |

## Hardware test checklist
1. The HUD stays still at the top while the landscape scrolls; no jitter and no garbage next to the boxes.
2. Colours of all object types look like `assets/art/spec-v2/generated/preview-all.png`.
3. Flying straight, only the exhaust flame of the player flickers (the plane itself must not jump); it banks
   left/right with the joystick. Enemy planes: only flames move, helicopter: only the rotor.
   Tanks: the tracks move, the barrel points in the driving direction.
4. Bombers and armoured planes (32×32) are drawn completely, including at the screen edges.
5. Being hit: the shield bar shrinks and changes colour, the plane blinks; at 0 it explodes, the lives number
   drops, and after 3 s the next plane starts with a full shield. After the third plane a new game starts.
6. Shoot down a whole formation: an "S" capsule appears; collecting it refills the shield.
   Tanks, bombers and armoured planes leave "$" capsules (small/medium/large); the credits counter in the
   middle of the HUD goes up by 10/25/50.
7. D shows the red raster band; note how big it gets with many objects on screen.
8. Exit with X / RUN/STOP and `RUN` again work as in Stage 1.
