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
- **Stage 3** (branch `stage3`, in progress): capsule and weapon rules, level files.
  Level storage research and format proposal: [docs/level_format.md](docs/level_format.md).

## Build
Requirements: Python 3 with Pillow and NumPy, Java, and `KickAss65CE02-5.25.jar`.
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
The output is `build/SHOOTER.PRG` and `build/SHOOTER65.D81` (`LOAD "SHOOTER",8` / `RUN`).

Controls: joystick in port 2 (fire = shoot). D toggles the raster time display. Press X or RUN/STOP to go back to BASIC.

## Documentation
- [Technical design and roadmap](docs/design.md)
- [Memory map](docs/memory_map.md)
- [Artwork specification](docs/artwork_spec.md)
- [Stage 2 notes and hardware checklist](docs/stage2.md)
- [Level data: research and format proposal](docs/level_format.md)
- [Working rules](CLAUDE.md)

## Layout
```
src/       engine sources (main, video, scroll, pixie, objects, player, hud, system, hw, layout)
tools/     build.py, import_art.py (artwork v2 importer), make_assets.py (placeholders), d81.py
docs/      design, memory map, stage notes
releases/  tested stage builds (PRG + D81)
```

