# Memory map (Stage 1)

All addresses are 28-bit physical addresses. The program keeps BASIC's SYS memory map (RAM below `$C000`,
I/O at `$D000`, KERNAL above) and returns to BASIC with X or RUN/STOP (see `docs/design.md` §13).
BASIC's screen RAM, colour RAM `$0000–$0FFF` and RAM below `$2000` are never written.

## Bank 0

| Address | Use |
|---|---|
| `$0002–$0053` | zero page variables (see `main.asm`, `pixie.asm`, `objects.asm`, `player.asm`); `$02–$FF` saved at start and restored on exit |
| `$2001–$2010` | BASIC stub `BANK 0:SYS 8224` |
| `$2020–…` | code and tables, incl. the 16-bit sprite pointer table `SPRPTR_TABLE` and the exit save area (zero page, VIC registers, palettes, about 1.2 KB) |
| `…–$A45F` | map (21 bytes/row × 512), map colours, tile/pixie glyph staging, sprites, palettes |
| `< $C000` | assembler guard: the PRG must end below `$C000` |

## Banks 4/5 (chip RAM)

| Address | Size | Use |
|---|---|---|
| `$40000–$4FFFF` | 64 KB | landscape NCM glyphs, char `$1000`+ (1024 glyphs) |
| `$50000–$53FFF` | 16 KB | pixie NCM glyphs, char `$1400`+ (256 glyphs); glyph `$1400` = blank |
| `$54000–$551ED` | 27×170 | RRB screen buffer A |
| `$56000–$571ED` | 27×170 | RRB screen buffer B |
| `$58000–$5AA7F` | 64×170 | ring buffer, screen part (32 slots stored twice) |
| `$5B000–$5DA7F` | 64×170 | ring buffer, colour part |
| `$5E000–$5EFFF` | | free (planned: HUD glyphs) |
| `$5F000–$5F1FF` | | player sprites (2 × 192 bytes, 256-byte aligned) |

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

## Palettes

| Entries | Use |
|---|---|
| text `$00–$0F` | C64 colours (debug border colours) |
| text `$10–$1F` | landscape (bank 1) |
| text `$20–$2F` | objects (bank 2) |
| sprite set 1 `$00–$1F` | player sprites 0 and 1 |
