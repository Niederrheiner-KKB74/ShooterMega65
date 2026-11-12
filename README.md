# Shooter65 (repository ShooterMega65)

A vertically scrolling shooter for the MEGA65, written in 45GS02 assembly (KickAssembler 65CE02 5.25).
**Finished** (12.11.2026): Stage 19 is the final version, confirmed on real MEGA65 hardware.

## The game
- Four levels, each with its own landscape, enemies, music and boss:
  1. **Coast and forest**, ending in a military base. Boss: a quadrotor with four turrets.
  2. **Desert, canyon and refinery**. Boss: a hover tank with a flame thrower.
  3. **Open sea** with islands, oil field, wind farm and naval base, ships and an animated sea. Boss: an aircraft
     carrier that launches jets.
  4. **Iron City**. Boss: a four-legged mech, then its wreck releases an armoured sphere with a flame column.
- A shop in the middle and at the end of every level: shot levels II–IV, two homing missiles, shield
  (invulnerability), bombs, lives and a drone that orbits the plane and catches enemy shots.
- Shield bar, three lives with checkpoints, credits from capsules, destroyable buildings and ground guns.
- Title screen and Hall of Fame (10 names, saved on the disk), name entry, MISSION ACCOMPLISHED page.
- Music and 14 sound effects composed by Claude, on separate SIDs.

## Playing
`LOAD "SHOOTER",8` and `RUN` from `releases/stage19/SHOOTER65.D81` (needs attic RAM, every MEGA65 from R3 on;
keep the disk writable for the high scores).

- Joystick in port 2: move, fire = shoot. Space = bomb, S = invulnerability (both bought in the shop).
- On the title: fire starts level 1, keys 2/3/4 start levels 2/3/4.
- X or RUN/STOP returns to BASIC; D shows the raster time.
- Test aids, also in the release: C = +5,000 credits, F = full equipment.

## Build
Requirements: Python 3 with Pillow and NumPy, Java, and `KickAss65CE02-5.25.jar` (not part of the repository).
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
The output is `build/SHOOTER.PRG`, `build/MUSICTEST.PRG` and `build/SHOOTER65.D81`. Test builds:
`--define GOD_MODE`, `SKIP_SHOP`, `START_LEVEL2/3/4`, `BOSS_TEST`, `BALL_TEST`, `DRONE_TEST`, `SHOT2/3/4`
(see the `docs/stageN.md` files).

## Stages
Every stage has a release folder `releases/stageN/` (PRG, D81, README, checksums) and notes with a hardware
checklist in `docs/stageN.md`; confirmed stages are tagged `stageN-stable`.

| Stages | Content |
|---|---|
| 1–2 | engine (NCM scrolling, RRB pixies, sprite player), artwork v2, HUD, shield, lives, capsules |
| 3–4 | levels as JSON files, shop, bomb, invulnerability, homing missile |
| 5–7 | music and effects, aircraft views, title, game over, level-1 boss |
| 8–9 | destroyable buildings, ground guns, level 2 |
| 10–12 | level-2 boss (hover tank with flame jet) |
| 13 | level 3 (sea, ships, tile animation and colour cycling, carrier) |
| 14 | level 4 (Iron City, mech boss), checkpoints, enemies redrawn by Claude |
| 15 | level transitions, diagonal enemy shots, art review |
| 16 | Hall of Fame on disk, title cycle, mission end, second missile |
| 17 | third phase of the final boss (sphere, wreck field, flame column), new animated sea in level 3 |
| 18 | enemies fire upwards, new backgrounds for levels 1 and 2, tanks stay out of the forest |
| 19 | Shot IV as four bolts, the drone |

## Documentation
- [Technical design and decisions](docs/design.md)
- [Memory map](docs/memory_map.md)
- [Level JSON format](docs/level_json.md) and [level data research](docs/level_format.md)
- [Music JSON format](docs/music_json.md)
- [Artwork specification](docs/artwork_spec.md)
- [Working rules](CLAUDE.md)

## Layout
```
src/       engine and game: main, video, scroll, pixie, objects, player, hud, shop, special, sound, level, levels,
           anim, boss, ball, ground, screens, transition, textpage, menu, hiscore, hiscore_disk, hipages, system,
           hw, layout
tools/     build.py, build_level.py (JSON → level files), build_music.py, compose_music.py, import_art.py,
           make_shop.py, make_screens.py, make_overlays.py, design_waves_l1..l4.py, pixel_vector.py, d81.py,
           check_*.py (artwork checks)
assets/    artwork; source/ folders hold the scripts with which Claude drew or redrew art
levels/    level descriptions (JSON)
music/     music pieces and sound effects (JSON)
docs/      design, memory map, stage notes, formats
releases/  tested stage builds (PRG, D81, README, checksums)
```
