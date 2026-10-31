# ShooterMega65

A vertically scrolling shooter for the MEGA65, written in 45GS02 assembly.

- 320×200 with 16-colour (NCM) tiles and several 16-colour palettes
- smooth vertical scrolling of a themed landscape at a fixed speed
- RRB "pixies" for all enemies, ground units, shots and explosions; hardware sprites for the player
- formations, ground targets, collectibles and a boss at the end of every level

## Status
**Stage 1 – engine prototype** (branch `stage1-engine-prototype`): scrolling, double-buffered
RRB, pixies, player sprite and demo enemies with placeholder graphics.
Smoke-tested in XEMU; **waiting for the real-hardware test**. See [docs/stage1.md](docs/stage1.md).

## Build
Requirements: Python 3 with Pillow and NumPy, Java, and `KickAss65CE02-5.25.jar`.
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
The output is `build/SHOOTER.PRG` and `build/SHOOTER65.D81` (`LOAD "SHOOTER",8` / `RUN`).

Controls: joystick in port 2 (fire = shoot). Press X or RUN/STOP to go back to BASIC.

## Documentation
- [Technical design and roadmap](docs/design.md)
- [Memory map](docs/memory_map.md)
- [Artwork specification](docs/artwork_spec.md)
- [Working rules](CLAUDE.md)

## Layout
```
src/       engine sources (main, video, scroll, pixie, objects, player, system, hw, layout)
tools/     build.py, make_assets.py (placeholder graphics), d81.py
docs/      design, memory map, stage notes
releases/  tested stage builds (PRG + D81)
```
