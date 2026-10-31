# Stage 1 – reference-board player and air enemies

This is a separate artwork test build, not a hardware-confirmed stable release.
`releases/stage1/` is untouched; candidate binaries are in `releases/stage1-aircraft/`.
Sources and reproducible build tools are in this branch. The integration PR is
stacked on the reference-board asset delivery (PR #2).

## Visible changes

- Blue/silver 24×24 player centred in the original 32×24 hardware-sprite canvas.
  Horizontal input chooses normal, left or right artwork (poster frames 4, 3, 5).
  Up/down only and simultaneous left+right select normal. Three pairs are staged
  in bank 0; only one 512-byte pair is resident in the existing chip-RAM region.
  The pair changes through DMA during vblank, only when the selected tilt changes.
- Waves cycle through fighter, bomber, helicopter and armoured plane. Each type
  has three frames, eight game ticks per frame (a 24-tick cycle). Enemy artwork is
  rotated 180 degrees from the poster so the noses face down.
- Each enemy type has its own 15-colour palette plus transparency, rather than
  forcing all four into the shared object palette. Existing palette save/restore
  already covers these entries.
- 24×24 enemies occupy centred 32×24 NCM canvases. Hitboxes use visible dimensions;
  the original 16px explosion is centred on the target when it is hit.

Landscape, ground tank, player/enemy projectiles, explosion artwork/timing,
scrolling, input controls, enemy paths, firing and six-enemy wave size are retained.
There are still no player lives/hit detection or HUD; those belong to later stages.

## Build and run

Python with NumPy and Pillow, Java, and the project's pinned
`KickAss65CE02-5.25.jar` are required (see `CLAUDE.md`). The assembler and MEGA65
ROM are not distributed. No PNG conversion is needed for normal builds: the
integration consumes reviewed indexed JSON from the asset delivery.

```sh
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
python3 tools/check_aircraft_integration.py
```

Default outputs: `build/SHOOTER.PRG`, `build/SHOOTER65.D81`. Mount D81, then
`LOAD "SHOOTER",8` and `RUN`. Joystick port 2; fire shoots; X or RUN/STOP exits.
To build the earlier placeholder artwork for comparison:

```sh
python3 tools/build.py --placeholder-art --out build-placeholder --kickass /path/to/KickAss65CE02-5.25.jar
```

Rebuild the default before running its integration check, because `build/gen`
always contains the most recently selected artwork. `--out` now resolves relative
paths before passing them to the assembler, so this documented comparison command
works from the repository root or another working directory. Failed assemblies
remove previous output binaries, so stale executables cannot look like fresh builds.

`tools/make_assets.py` still generates the legacy world/combat assets. The normal
build then calls `tools/integrate_aircraft.py`, replaces only player/aircraft data,
and emits named frame tables, palette indices and collision geometry. The seven
remaining legacy frames retain their names, including contiguous `FR_EXPL0..3`.
Frame IDs are generated and must not be hardcoded. Placeholder mode emits the same
table schema, keeping the runtime comparison path buildable.

## Validation of this candidate

| Check | Result |
|---|---|
| Pinned assembler SHA-256 | Matches the value in `CLAUDE.md` |
| Default build | Assembled, 39265-byte PRG, exclusive end `$B960` |
| Memory budget | 1696 bytes remain below `$C000`; 86 pixie glyphs / 5504 bytes fit the 16KB region |
| D81 | Generated and the stored PRG read back byte-for-byte |
| Comparison mode | `--placeholder-art` assembled; D81 read-back passed |
| Asset regression | Map, map colours and landscape glyphs unchanged; decoded tank, shots and all four explosions unchanged |
| New graphics | All 12 enemy frames independently decoded, orientation/guards/padding checked; three player pairs and palettes checked |
| Collision boundary checks | 2050 cases execute the actual assembled `hit_axis` instructions in a small instruction runner, including signed/negative coordinates |
| Emulator | Attempted in isolated XEMU master `40dfef0` (2026-01-29); no confirmed BASIC/PRG startup before timeout, so **not passed** |
| Real MEGA65 | **Not tested; owner confirmation required** |

The instruction runner checks arithmetic, not VIC-IV behaviour or a complete CPU.
The emulator attempt did not establish a game failure: the startup/injection did
not reach a confirmed running PRG. No emulator screenshot is claimed as evidence.
The previous Stage-1 XEMU screenshots do not validate this candidate.

Memory addresses and palettes are documented in `docs/memory_map.md`. Assembler
guards reject PRG overflow, pixie-region overflow and incorrectly aligned/sized
player frames. The generated layout is `build/gen/aircraft-layout.json`.

## Hardware checklist before acceptance

1. Confirm normal player, left/right tilt, diagonals and transparency. Rapidly
   change direction and return to normal; there must be no torn half or stale frame.
2. Wait through all four wave types (about 12 seconds at 50Hz). Check their colours,
   downward orientation and three-frame animation, with no lines between glyph rows.
3. Shoot large and small targets near their edges. Transparent NCM padding must not
   count as an enlarged target; the old explosion must appear at the target centre.
4. Check both screen edges, simultaneous shots/tanks and overlapping large enemies.
   Observe the debug raster band and RRB overflow byte `$0D` under load. Wider pixies
   consume more row tokens; timing/overflow are not established by the data tests.
5. Exit with X and RUN/STOP. Check BASIC colours, RUN again, and verify the normal
   player frame is restored. Repeat after leaving the player tilted.
6. Compare scrolling, ground tank, shots and explosion timing with the placeholder
   build. Existing game rules should behave the same.

All aircraft remain automatically reduced/quantized reconstructions of the user's
PNG, not recovered original pixel grids or newly hand-drawn art. Original PNG,
crop parameters and the conversion pipeline are retained from PR #2.
