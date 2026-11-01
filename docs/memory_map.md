# Memory map (Stage 7)

All addresses are 28-bit physical addresses. The program keeps BASIC's SYS memory map (RAM below `$C000`,
I/O at `$D000`, KERNAL above) and returns to BASIC with X or RUN/STOP (see `docs/design.md` §13).
BASIC's screen RAM, colour RAM `$0000–$0FFF` and RAM below `$2000` are never written.
Exact addresses of the bank-0 areas come from `build/main.sym`; the values below are from the Stage 2 build.

## Zero page (`$02–$FF` saved at start, restored on exit)

| Address | Use |
|---|---|
| `$02–$0D` | frame counter, buffer select, scroll state, joystick, random seed, RRB overflow counter |
| `$10–$1B` | 32-bit screen/colour pointers, temporaries |
| `$1C–$2F` | pixie emitter |
| `$34–$38` | back buffer addresses, pending TEXTYPOS |
| `$40–$4F` | object system (current object, timers, spawn position, kill flags, collision temporaries) |
| `$50–$58` | player (position, fire cooldown, shield, invulnerability, state, timer, sprite frame) |
| `$59–$66` | HUD (dirty flags, pointers, 32-bit glyph pointer, score BCD `$64–$66`) |
| `$67` | lives |
| `$68–$69` | credits (BCD, 4 digits) |
| `$70` | player exhaust animation counter |
| `$6A–$6F` | collision centres |
| `$71` | player weapon damage (`pl_power`) |
| `$72–$75` | 32-bit pointer into the level data |
| `$76–$79` | 32-bit pointer into the music data (`sound.asm`) |
| `$7A–$7D` | 32-bit source pointer of the title / banner routines (`screens.asm`) |

Shop state (`bomb_count`, `inv_count`, `has_missile`, cursor and dialog variables) lives in bank 0 in `shop.asm`,
not in the zero page.

## Bank 0

| Address | Use |
|---|---|
| `$2001–$2010` | BASIC stub `BANK 0:SYS 8224` |
| `$2020–…` | code and tables: sprite pointer table, HUD work buffer (14×64), HUD digits/templates, exit save area, sine table, frame tables, shop code, token maps and palettes |
| `…` | level loader buffer (256 bytes), metatile tables (3×256 bytes) |
| `…` | pixie glyph staging: only the non-blank glyphs (174) plus a run table; exact addresses in `build/main.sym` |
| `$9E00–$A9FF` | player sprites, 6 pairs × 512 bytes |
| `$AA00–$AD5F` | text palette (768 bytes) and sprite palette (96 bytes) |
| `$A000–$BFFF` | music and sound effects from the file `MUSIC` (Stage 7: 4,519 of 8,192 bytes); the PRG must end below `$A000` (guard in `sound.asm`) |

## Banks 4/5 (chip RAM)

| Address | Size | Use |
|---|---|---|
| `$40000–$43FFF` | 16 KB | landscape NCM glyphs, char `$1000`+ (max. 256 per level: tile offsets in the map are bytes; `build_level.py` allows 128 tiles; the coastal level uses 208 glyphs) |
| `$44000–$467FF` | 10 KB | shop glyphs from the file `SHOP`, char `$1100`+ (160 reserved, 148 used). Guarded in `shop.asm` |
| `$46800–$4FFFF` | 38 KB | pixie NCM glyphs, char `$11A0`+ (max. 608, Stage 6 uses 535): loaded at start from the file `PIXIES` (complete image incl. blank guards) straight into this area. Frame bases in `frames.inc` are absolute character numbers. HUD glyphs at `HUD_GLYPH + 2k`, rebuilt at run time |
| `$50000–$53FFF` | 16 KB | load buffer (at the end: `L1BOSS`, 9,584 bytes, swapped with the fighter/bomber glyphs during the boss fight): first `SHOP` (glyphs → `$44000`), `MUSIC` (→ `$5E000`) (`PIXIES` goes straight to `$46800`), then `LnGFX` (glyphs → `$40000`, palettes → bank 0), then `LnDAT` (map, events, formations, paths), which stays here for the whole level |
| `$54000–$551ED` | 27×170 | RRB screen buffer A |
| `$56000–$571ED` | 27×170 | RRB screen buffer B |
| `$58000–$5AA7F` | 64×170 | ring buffer, screen part (32 slots stored twice) |
| `$5B000–$5DA7F` | 64×170 | ring buffer, colour part |
| `$56000–$5C7FF` | 26 KB | **while the title is shown**: title glyphs, map, palette (`TITLE`); overlaps screen B and the ring, which are rebuilt for every game |
| `$58000–$5966F` | 5.6 KB | **while the game-over banner is shown**: banner glyphs, map, palette (`GOVER`), in the ring (the game is paused) |
| `$5E000–$5EFFF` | 4 KB | free (music moved to bank 0 in Stage 7) |
| `$5F000–$5FBFF` | | player sprites, 6 frame pairs (left/right half 256 bytes each) |
| `$5FC00–$5FEFF` | | invulnerability ring, sprites 2–4 (256 bytes each, `special.asm`) |
| `$5FF00–$5FFFF` | | free |

`$20000–$3FFFF` is ROM and is never used for data (Vyper rule 4).

## Colour RAM (`$FF80000`)

| Offset | Use |
|---|---|
| `$0000–$0FFF` | BASIC's colour RAM (80×50 needs 4000 bytes), never written |
| `$1000–$21ED` | colour buffer A (27×170) |
| `$2400–$35ED` | colour buffer B (27×170) |

## VIC-IV configuration

| Register | Value | Meaning |
|---|---|---|
| `$D031` | `$40` | FAST, H320, V200 |
| `$D054` | `$45` (+ PALEMU kept) | CHR16, FCLRHI, VFAST |
| `$D058/9` | 170 | LINESTEP |
| `$D05E`/`$D063` | 85 | CHRCOUNT |
| `$D05A` | 120 | CHRXSCL |
| `$D04C/D` | 48 | TEXTXPOS (16 logical px under the left border) |
| `$D04E/F` | 88–102 | TEXTYPOS (fine scroll) |
| `$D048/9`, `$D04A/B` | 104, 504 | top and bottom border |
| `$D05C` | 80 | side border width |
| `$D07B` | 26 | display rows (27 rows fetched, last one under the border) |
| `$D051` | `$00` | RRB double buffering |
| `$D070` | `$04` | text palette 0, sprite palette 1 |
| `$D030` | BASIC value, bit 0 cleared, bit 2 set | RAM palette, CRAM2K off |

All registers above (plus the sprite colour registers `$D029–$D02B`), palette 0 and palette 1 entries 0–79 are saved at start and restored on exit.

## Palette banks (text palette 0, 16 entries each; made by `tools/import_art.py`)

| Bank | Use | Bank | Use |
|---|---|---|---|
| 0 | C64 colours (border, debug) | 8 | armoured plane |
| 1 | landscape: water | 9 | player shot |
| 2 | landscape: nature | 10 | red enemy shot |
| 3 | landscape: structures | 11 | fire shot |
| 4 | landscape: fixed targets; tanks | 12 | HUD, bonus capsules |
| 5 | fighter | 13 | rocket |
| 6 | bomber; during the boss fight: boss hit flash (Stage 7b) | 14 | small explosion |
| 7 | helicopter | 15 | big explosion |

While the shop is open (Stage 3b), banks 13–15 hold the shop palettes (normal, dimmed, highlight); no objects
exist then. They are restored from the game palette when the shop closes.

All 16 banks are in use. Further object types must share a bank; the importer merges and, if needed,
reduces colours (`merge_bank`). Sprite palette (set 1) entries `$00–$1F`: player (sprites 0 and 1); `$20–$4F`: invulnerability ring (sprites 2–4), indices 1–6 rotated at run time.

## Coastal-base level (default since Stage 3b)

`levels/coastal_base.json` is the default 375-row level. The denser scenery
revision has 126 tiles using 252 glyphs (16128 bytes) at `$40000–$43EFF`.
The 16324-byte GFX payload and 6566-byte DAT payload each fit
the existing 16KB level buffer; DAT occupies `$50000–$519A5`. The GFX header/palettes
leave room for at most 126 tiles, not 128; only 60 bytes remain in the file budget. Fixed-target palette
bank 4 stays RGB-identical because moving tanks share it. Shield/coin artwork
reuses HUD/bonus bank 12. No memory regions or zero-page variables are added.
The verified Stage-3b candidate PRG ends at `$9D60` (exclusive); pixie allocation
is 265 of 512 glyphs. The shop uses 148 glyphs / 9476 bytes including its header,
within its existing 255-glyph/load-buffer limit. See `docs/COASTAL_BASE_LEVEL.md` for build evidence and
remaining emulator/hardware tests.

The clockwise-45-degree rocket source in `assets/art/rocket-directions/` is now
used by Stage 4/5 to derive eight runtime missile directions through the existing
bank-13 remap. These are included in the current glyph count below.

## Enemy artwork revision (Stage 5)

The repaired canonical enemy hulls and 18px large coin retain the current
289/512 runtime glyph allocation and existing 61 frame IDs. No address or region
is added; the verified candidate PRG ends at `$B460` (exclusive).
`assets/art/enemy-views/` is an offline 325-glyph pose bundle, not runtime data.
Replacing all 12 canonical air frames (78 glyphs) with its 66 frames (324 glyphs
plus the shared existing blank) would need 535 runtime glyphs, exceeding the
512-glyph area by 23. Do not append/import the whole bundle without deduplication
or selecting fewer poses. Local bases and source palette indices require relocation
and the existing per-type palette remap. See `docs/ENEMY_VIEWS_AND_OPACITY.md`.

## Sound chips

| SID | Address | Use |
|---|---|---|
| 1 | `$D400` | music (3 voices) |
| 2 | `$D420` | sound effects (3 voices) |
| 3 | `$D440` | copy of SID 1 (SIDs 1/2 are panned slightly right, 3/4 slightly left) |
| 4 | `$D460` | copy of SID 2 |

All four are silenced on the way back to BASIC.

## Offline title / game-over and Level-1 boss assets

The new assets are not loaded by this stage and add no runtime address or
allocation. Title: 384 unique 16x8 glyphs / 24576 bytes, plus separate local map
and palette data; bottom three glyph rows are reserved for dynamic text.
Game-over banner: 55 glyphs / 3520 bytes at 256x64. The 320x200 full-screen
alternative has 500 glyphs / 32000 bytes and must not be loaded into a banner-sized
region. Each screen uses one local 16-entry palette; choose/restore the hardware
bank and background colour during later screen integration.

Boss: 96x64 body plus component art, 137 guarded glyphs / 8768 bytes; one 48-byte
palette gives 8816 bytes of glyph/palette data, below the 9KB artwork budget.
Local bases must be relocated and source palette indices mapped during later
import. Four turret IDs are damage parts; four rotor instances are visual-only
and reuse three frames. No new fixed palette bank is assumed. Future engine
integration must add its own address/region guards. See `docs/SCREENS_AND_LEVEL1_BOSS.md`.

## Attic RAM (`$8000000`, MEGA65 R3 and later)

| Address | Use |
|---|---|
| `$8000000` | title screen data (`TITLE`, 26 KB), copied to `$56000` for the title |
| `$8010000` | game-over banner data (`GOVER`, 5.6 KB), copied to `$58000` for the banner |

Detected at start (two patterns written by DMA and read back). Without attic RAM the title is loaded straight to
`$56000` and shown only once.

## Files on the D81 (Stage 7)

`SHOOTER`, `MUSICTEST` (PRG), `SHOP`, `MUSIC`, `PIXIES`, `TITLE`, `GOVER`, `L1GFX`, `L1DAT`, `L1BOSS` (SEQ).
