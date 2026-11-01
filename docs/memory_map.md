# Memory map (Stage 3)

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

## Bank 0

| Address | Use |
|---|---|
| `$2001–$2010` | BASIC stub `BANK 0:SYS 8224` |
| `$2020–$4407` | code and tables: sprite pointer table, HUD work buffer (7×64), HUD digits/template, exit save area, sine table, frame tables |
| `…` | level loader buffer (256 bytes), metatile tables (3×256 bytes) |
| `…` | pixie glyph staging: only the non-blank glyphs (174) plus a run table; exact addresses in `build/main.sym` |
| `$9E00–$A9FF` | player sprites, 6 pairs × 512 bytes |
| `$AA00–$AD5F` | text palette (768 bytes) and sprite palette (96 bytes) |
| `< $C000` | assembler guard: the PRG must end below `$C000` |

## Banks 4/5 (chip RAM)

| Address | Size | Use |
|---|---|---|
| `$40000–$47FFF` | 32 KB | landscape NCM glyphs, char `$1000`+ (max. 512; tile offsets in the map are bytes, so 256 per level; Stage 2 uses 124) |
| `$48000–$4FFFF` | 32 KB | pixie NCM glyphs, char `$1200`+ (max. 512, 16-bit frame bases; Stage 2 uses 259); glyph `$1200` = blank; HUD glyphs at `HUD_GLYPH + 2k`, k = 0..10. The area is cleared by DMA at start and only the non-blank glyph runs are copied from the PRG |
| `$50000–$53FFF` | 16 KB | level buffer: `LnGFX` is loaded here first (glyphs → `$40000`, palettes → bank 0), then `LnDAT` (map, events, formations, paths) stays here for the whole level |
| `$54000–$551ED` | 27×170 | RRB screen buffer A |
| `$56000–$571ED` | 27×170 | RRB screen buffer B |
| `$58000–$5AA7F` | 64×170 | ring buffer, screen part (32 slots stored twice) |
| `$5B000–$5DA7F` | 64×170 | ring buffer, colour part |
| `$5E000–$5EFFF` | | free |
| `$5F000–$5FBFF` | | player sprites, 6 frame pairs (left/right half 256 bytes each) |

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

All registers above, palette 0 and palette 1 entries 0–31 are saved at start and restored on exit.

## Palette banks (text palette 0, 16 entries each; made by `tools/import_art.py`)

| Bank | Use | Bank | Use |
|---|---|---|---|
| 0 | C64 colours (border, debug) | 8 | armoured plane |
| 1 | landscape: water | 9 | player shot |
| 2 | landscape: nature | 10 | red enemy shot |
| 3 | landscape: structures | 11 | fire shot |
| 4 | landscape: fixed targets; tanks | 12 | HUD, bonus capsules |
| 5 | fighter | 13 | rocket |
| 6 | bomber | 14 | small explosion |
| 7 | helicopter | 15 | big explosion |

All 16 banks are in use. Further object types must share a bank; the importer merges and, if needed,
reduces colours (`merge_bank`). Sprite palette (set 1) entries `$00–$1F`: player (sprites 0 and 1).
