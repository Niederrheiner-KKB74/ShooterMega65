# ShooterMega65 – Technical Design

Status: Stage 1 with reference-aircraft integration (31.10.2026); aircraft build
assembled and data-tested, emulator/hardware confirmation still open.
Items marked **(decision)** need the
project owner's confirmation. Items marked **(HW)** have to be checked on real
MEGA65 hardware, because XEMU is not authoritative for them (see Vyper rule 19).

## 1. Game summary

Vertically scrolling shooter for the MEGA65, 45GS02 assembly (KickAssembler 65CE02 5.25).

- The player flies an armed aircraft that moves freely over the whole screen.
- The landscape scrolls from top to bottom at a fixed speed, with a different theme in each level.
- There are fixed and moving ground targets. Air enemies fly in formations and shoot.
- Ground objects also attack the player.
- Items and persons on the ground are collected by flying over them.
- A large boss ends every level.

## 2. Display

| Property | Choice |
|---|---|
| Mode | H320 / V200 (`$D031 = $40`), PAL, 40.5 MHz CPU |
| Background | 16-colour (NCM) characters, 16×8 pixels, 64 bytes per glyph |
| Colours | 16-colour sub-palettes (palette banks). Each tile and each pixie selects its bank through colour-RAM byte 1 (`bank<<4 \| $0F`). Nibble 0 is transparent in overlays and shows the background colour in tiles. Nibble 15 shows colour-RAM byte 1's colour, which is set to the bank's colour 15, so every bank offers 15 colours plus transparency. |
| Moving objects | RRB "pixies" (GOTOX overlays in the same NCM format) |
| Player | 2 hardware sprites in 16-colour mode (32×24) |
| Glyph addressing | `CHR16` + `FCLRHI` (`$D054 = $45`); all game glyphs are ≥ `$1000` |

The screen uses 320×200 logical pixels. With NCM, the levels can use several
16-colour palettes at the same time, for example one each for land, water, buildings and enemies.

### 2.1 The hidden left column
Text starts 16 logical pixels left of the side border (`TEXTXPOS = 48` native, border
width 80). Every row therefore has **21** background chars (336 px), and the first 16 px
are hidden under the border. A pixie at screen x uses GOTOX `x + 16`. Objects can therefore
enter from the left edge without the software cropping that Vyper needed
(`offscreen.asm`). The right edge needs no special handling, because pixels past x = 336
fall under the right border.

### 2.2 Hardware rules inherited from Vyper (confirmed on real hardware)
1. H320 with `CHRXSCL $D05A = 120`; GOTOX values are logical 320-px coordinates.
2. RRB double buffering: `$D051` bit 7 (NORRDEL) = 0. It is written on every flip.
3. GOTOX token format: screen byte 0 = X low, byte 1 = `X bits 8-9 | $10 | (yoffset<<5)`.
   Colour bytes are `$90,$00` (GOTOX, no background paint). Glyph tokens use colour
   `$08` (NCM) followed by the palette byte.
4. Audio DMA: write `$D72A/$D72B` before `$D72C`, and check `$D711` bit 7 only. This applies when sound is added.
5. KERNAL file I/O: call `SETBNK ($FF6B)` before `SETNAM`. This applies when loading levels.

## 3. Vertical scrolling

```
 map (bottom→top)        ring buffer (32 slots, stored twice)        back buffer (27 rows)
 row m  ──decode──▶  slot (31-m)&31  and  slot+32   ──1 DMA/frame──▶  rows 0..25   + null row 26
```

- **Map rows** contain 21 glyph indices plus 21 colour bytes (palette per tile). The engine
  decodes one row into the ring every 8 pixels of scrolling, writing both copies.
- **Ring order** is chosen so that display rows 0..25 are 26 consecutive slots. Storing the ring
  twice removes the wrap-around, so a single DMA copies the visible screen part (4,420
  bytes) and a second one copies the colour part into the back buffer every frame. The copy also
  removes the previous frame's pixies, so no per-row clearing is needed.
- **Fine scroll** moves `TEXTYPOS` (`$D04E`): `88 + 2·(scroll_px & 7)` physical
  raster lines. Row 0 starts up to 8 px above the top border (104). `DISPROWS = 26` fetches 27 rows. The 27th row is a
  static "null" row under the bottom border.
- **Double buffering**: screen A/B (bank 5) and colour A/B (colour RAM). The flip during the
  vertical blank writes `$D060-62`, `$D064-65`, `$D04E` and `$D051`.
- **Speed**: `SCROLL_SPEED` is 8.8 fixed point: 0.5 px/frame (25 px/s), confirmed by the owner on 31.10.2026.
- Ground objects store screen coordinates and add `scroll_delta` (the whole pixels scrolled
  this frame), so they stay locked to the landscape.

Cost per frame: two DMA jobs of 4,420 bytes, plus one 21-column decode every 16 frames at the current speed.

## 4. RRB pixies

### 4.1 Row layout (85 tokens = 170 bytes, `LINESTEP`)
| Tokens | Content |
|---|---|
| 0–20 | background tiles (from the ring) |
| 21–83 | overlay area: pixie fragments, initially "null" GOTOX(320) tokens |
| 84 | transparent blank glyph. Each row ends at x = 336, exactly at the right border |

Each fragment needs `1 + w` tokens (GOTOX plus w glyphs). A row holds **63 overlay tokens**,
for example 31 one-char fragments. If a fragment does not fit, it is dropped and
counted in `overflow` ($0D). Objects are never corrupted. Whether 85 tokens per row are fast enough at full load
is a **(HW)** test item. Vyper ran 96-token rows.

### 4.2 Glyph layout for vertical positioning
A frame is `w` chars wide and `h` glyph rows high. Column `c`, row `i` is glyph
`PIXIE_CHAR + base + c·(h+1) + i`, and the glyph before each column is blank:

```
[blank] [c0 r0] [c0 r1] … [c0 r(h-1)] [blank] [c1 r0] … [blank]
```

An object at grid y = 8·r0 + k touches rows r0 … r0+h (h+1 rows when k ≠ 0). Each row i
uses glyph i with Y offset k, so the VIC fetches it k lines early and shows the tail of
glyph i-1 on top. Clipping at the top and bottom only skips rows outside 0..25.

### 4.3 Draw order and palettes
Slot ranges define the draw order: ground objects 0–9, air objects 10–29, shots 30–47.
Later fragments are drawn on top. Each object passes its own palette byte, so the same glyphs
can be recoloured, for example to make an enemy flash white when hit.

The current emitter obtains the palette from `frame_pal[obj_fr]`: bank 2 for
the original tank/shots/explosions, banks 3–6 for the four air-enemy types.
Waves cycle fighter → bomber → helicopter → armoured plane. Air enemies keep
their animation base in `obj_airbase` and advance one of three frames every
eight ticks. The original sine paths, firing and wave size remain unchanged.
Frames are contiguous within a type. `--placeholder-art` emits one-frame
animations and four aliases for the original enemy, using the same code path.

Air hitboxes use visible 16×16 or 24×24 bounds, centred in their 16px/32px NCM
canvases, with the existing two-pixel shot allowance. The 16px explosion graphic
is positioned at the target centre. Explosion artwork and its four-frame timing
are unchanged. See `docs/stage1-aircraft.md` for validation and remaining tests.

## 5. Hardware sprites
- Sprites 0+1: the player, 16-colour, 16×24 each, 16-bit sprite pointers (16-byte-aligned table in bank 0,
  data at `$5F000`), sprite palette = palette set 1 (`$D070 = $04`). In 16-colour mode the
  sprite colour register holds the *transparent* index (0). **(HW)**
- The 24×24 reference-board player is centred in its existing 32×24 canvas.
  Three 512-byte pairs (normal/left/right) are staged in bank 0; a change of
  horizontal input copies one pair to the unchanged `$5F000` region in vblank.
  Initial asset DMA and `player_init` reset the normal frame on every RUN.
- Sprites 2–7 are free. Candidates **(decision)**: the player's shadow, option drones, a HUD part, or boss turrets
  that must sit above everything.

## 6. Objects, collisions, gameplay

- Structure-of-arrays tables (`obj_type, x, y (16-bit signed), frame, t, a, b`). Updates go
  through a jump table per type. Stage 1 types: player shot, air enemy, tank, enemy shot, explosion.
- Collisions use bounding boxes with 16-bit signed differences, and only shots against targets
  (O(shots × targets) ≤ 18 × 30 checks).
- Planned types:
  - formation flyers driven by path tables. The path format follows Vyper's curve interpreter (segments of dx/dy/frames).
  - turret and tank ground units that aim at the player.
  - fixed ground targets: part of the tile map. A target table per level (row, column, hit points, rubble tiles)
    patches the ring rows when the target is destroyed.
  - collectibles (persons, power-ups), and the boss.
- Player weapons (decided 31.10.2026): **one fire button** for an upgradable main gun that hits air and
  ground targets, plus a **special weapon on the space bar** (implemented in a later stage; the key
  is already read from the hardware keyboard queue `$D610` and sets `special_req`).

## 7. Boss
- The boss is a multi-char pixie object, for example 96×64 px = 6 chars × 8 rows, which is 7 tokens per row
  (plus 1 row when it is not aligned). Turrets and weak points are separate objects at fixed offsets, so they can
  be destroyed one by one. Big frames may need DMA-based glyph streaming for animation.
- Scrolling stops (`SCROLL_SPEED = 0`) or loops a short boss-arena section of the map while the boss is alive.

## 8. HUD
**Decided (31.10.2026): option 1, a score strip at the top of the screen.** Fine scrolling moves the whole text area, so a HUD made of plain text chars would scroll too. The options were:
1. **A pixie strip at a fixed screen y** (recommended). It is 1–2 rows of 20 glyphs drawn from a small dynamic
   glyph buffer, re-rendered only when the score changes. Its cost is about 42 tokens in 2 rows.
2. Hardware sprites for the score and lives (sprites 2–7, 16-colour, 16 px wide each).
3. A raster split with a second text area. This is the most complex option and risky on hardware.

## 9. Level data and loading
- Per level: a tile set (NCM glyphs and up to n palette banks), a map (21 glyph bytes and 21 colour bytes
  per row, or metatiles to save memory), a spawn script (events keyed by map row) and boss data.
- Loading uses KERNAL SEQ files between levels, following Vyper's loader rules. Files are ZX0-packed, using Vyper Stage 10a2's
  streaming unpacker.
- Memory: chip RAM `$40000–$5FFFF` holds the run-time data, and level data goes to attic RAM if needed
  (see `memory_map.md`).

## 10. Sound
- Music: SID tunes. The MEGA65 has 4 SIDs, so music and sound effects can use separate chips.
- Sample effects: Vyper's audio-DMA driver (`stage10a6_audio_core.asm`), with the register order from §2.2.

## 11. Reuse from Vyper
| Reused | How |
|---|---|
| RRB GOTOX format, H320/CHRXSCL, double buffering | rules in §2.2, new implementation |
| F018A enhanced DMA job format | `hw.asm` `DmaJob` macro |
| D81 writer | `tools/d81.py` (adapted) |
| Later: SEQ loader, ZX0 unpacker, audio DMA, highscore D81 handling | port the modules when needed |

Vyper's stage files are not copied wholesale, because they carry their full history of fixed addresses.

## 12. Roadmap

| Stage | Content | Acceptance |
|---|---|---|
| **1** | Engine prototype: mode, scrolling ring, double-buffered RRB, pixies, sprite player, demo enemies | XEMU smoke test ✔, **real hardware test by owner** |
| 2 | HUD, player hit/lives, game states (title → play → game over) | HW |
| 3 | Level format and tool (PNG/Tiled → tiles/map/script), first real tile set, spawn script | HW |
| 4 | Enemy paths and formations, ground turrets, fixed targets (tile patching) | HW |
| 5 | Collectibles, weapon power-ups, bombs | HW |
| 6 | Boss framework and first boss | HW |
| 7 | Sound (SID music + DMA SFX) | HW |
| 8 | Loader, packed level files, several themed levels, polish | HW |

## 13. Leaving the game
**X** or **RUN/STOP** returns to BASIC (`system.asm`), following Vyper's exit strategy: the VIC-IV
registers and palettes are saved at start and written back with HOTREG off, and HOTREG is restored last.
To make this possible, the game leaves the memory map, the stack, the interrupt sources (only `SEI`),
BASIC's screen RAM and colour RAM `$0000–$0FFF` untouched. On exit it restores zero page, the base page and the stack
pointer and returns with `RTS` to the SYS caller. Every routine with self-modifying DMA lists resets them,
so `RUN` works again after an exit.

## 14. Decisions log
| Date | Decision |
|---|---|
| 31.10.2026 | Scroll speed 0.5 px/frame |
| 31.10.2026 | One fire button; special weapon on the space bar (later stage) |
| 31.10.2026 | Score display at the top of the screen (pixie strip, §8) |
| 31.10.2026 | Artwork made by the owner (with ChatGPT), following `docs/artwork_spec.md` |
| 31.10.2026 | Exit to BASIC with X or RUN/STOP, as in Vyper |

## 15. Open questions for the owner
1. Should the scroll speed change per level or section, for example a faster section before the boss?
2. What should the special weapon be (screen bomb, laser, shield …), and how many uses should there be per life or level?
3. How many levels, with which themes (for example countryside, desert, coast/sea, city, fortress)?

