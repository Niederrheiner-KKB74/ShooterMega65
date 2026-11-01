# ShooterMega65

A vertically scrolling shooter for the MEGA65, written in 45GS02 assembly.

- 320×200 with 16-colour (NCM) tiles and several 16-colour palettes
- smooth vertical scrolling of a themed landscape at a fixed speed
- RRB "pixies" for all enemies, ground units, shots and explosions; hardware sprites for the player
- formations, ground targets, collectibles and a boss at the end of every level

## Status
- **Stage 1** (engine prototype) and **Stage 1-aircraft**: confirmed on real hardware (01.11.2026),
  `stage1-stable` / `stage1-aircraft-stable`.
- **Stage 2** (branch `stage2`): artwork v2 and animated tanks, HUD with score, lives, credits and shield bar,
  shield/damage, three lives, capsules. Confirmed on real hardware (01.11.2026), `stage2-stable`.
- **Stage 3a** (branch `stage3`): capsule and weapon rules; levels as JSON files, converted into level files
  on the D81 (map, formations, flight paths, ground units). Confirmed on real hardware (01.11.2026), `stage3a-stable`.
  See [docs/stage3.md](docs/stage3.md), level format for ChatGPT: [docs/level_json.md](docs/level_json.md).
- **Stage 3b** (branch `stage3`): shop overlay (weapon levels, missile, shield, bomb, extra life), HUD counters
  for bombs and invulnerability, coastal-base level (PR #8) as the default, shop icons (PR #9).
  Confirmed on real hardware (01.11.2026), `stage3b-stable`.
- **Stage 4** (branch `stage4`): special weapons from the shop: bomb (space), 10 s invulnerability with a
  shimmering ring (S), homing missile; extra life / exit icons and denser coastal level (PR #10).
  Confirmed on real hardware (01.11.2026), `stage4-stable`. See [docs/stage4.md](docs/stage4.md).
- **Stage 4b** (branch `stage4`): missile drawn in 8 flight directions, revised coastal level (PR #11).
  Confirmed on real hardware (01.11.2026), `stage4b-stable`.
- **Stage 5** (branch `stage5`): music (four pieces composed by Claude) and 14 sound effects on separate SIDs;
  MUSICTEST program with a 440 Hz tuning tone. Confirmed on real hardware (01.11.2026), `stage5-stable`. See [docs/stage5.md](docs/stage5.md).

## Build
Requirements: Python 3 with Pillow and NumPy, Java, and `KickAss65CE02-5.25.jar`.
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
The output is `build/SHOOTER.PRG` and `build/SHOOTER65.D81` (`LOAD "SHOOTER",8` / `RUN`).

Controls: joystick in port 2 (fire = shoot), space = bomb, S = invulnerability (both bought in the shop). D toggles the raster time display. Press X or RUN/STOP to go back to BASIC.

## Documentation
- [Technical design and roadmap](docs/design.md)
- [Memory map](docs/memory_map.md)
- [Artwork specification](docs/artwork_spec.md)
- [Stage 2 notes and hardware checklist](docs/stage2.md)
- [Level data: research and format proposal](docs/level_format.md)
- [Level JSON format (for level design)](docs/level_json.md)
- [Music JSON format (for music with ChatGPT)](docs/music_json.md)
- [Working rules](CLAUDE.md)

## Layout
```
src/       engine sources (main, video, scroll, pixie, objects, player, hud, shop, level, system, hw, layout)
tools/     build.py, import_art.py (artwork importer), build_level.py (JSON → level files), make_shop.py,
           build_music.py (JSON → MUSIC), compose_music.py (score of the four pieces), d81.py
levels/    level descriptions (JSON)
music/     music pieces and sound effects (JSON)
docs/      design, memory map, stage notes
releases/  tested stage builds (PRG + D81)
```

