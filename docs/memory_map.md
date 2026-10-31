# Memory map (Stage 1)

All addresses are 28-bit physical addresses. The program keeps BASIC's SYS memory map (RAM below `$C000`,
I/O at `$D000`, KERNAL above) and returns to BASIC with X or RUN/STOP (see `docs/design.md` §13).
BASIC's screen RAM, colour RAM `$0000–$0FFF` and RAM below `$2000` are never written.

## Bank 0

| Address | Use |
|---|---|
| `$0002–$0053` | zero page variables (see `main.asm`, `pixie.asm`, `objects.asm`, `player.asm`); `$02–$FF` saved at start and restored on exit |
| `$2001–$2010` | BASIC stub `BANK 0:SYS 8224` |
| `$2020–$3A9B` | code/tables, 16-bit sprite pointer table, exit save area, 48-byte air-animation base table and wave-kind byte |
| `$3B00–$9A7F` | unchanged map, map colours and landscape glyph staging |
| `$9A80–$AFFF` | 86 guarded pixie glyphs (5504 bytes) |
| `$B000–$B5FF` | three 512-byte player pairs in bank-0 staging (normal, left, right) |
| `$B600–$B95F` | text palette (768 bytes) and sprite palette (96 bytes) |
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
| `$5F000–$5F1FF` | 512 bytes | one resident player pair (2 × 192 bytes, 256-byte aligned); 512-byte DMA only when tilt changes, during vblank |

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
| text `$20–$2F` | unchanged ground tank, shots and explosions (bank 2) |
| text `$30–$3F` | reference-board fighter (bank 3) |
| text `$40–$4F` | reference-board bomber (bank 4) |
| text `$50–$5F` | reference-board helicopter (bank 5) |
| text `$60–$6F` | reference-board armoured plane (bank 6) |
| sprite set 1 `$00–$1F` | player sprites 0 and 1 |

Addresses above describe the default aircraft build (PRG end exclusive `$B960`,
1696 bytes free before `$C000`). Chip-RAM regions and zero-page allocation are
unchanged. All text palette entries were already saved/restored by `system.asm`.
`--placeholder-art` uses fewer staging bytes; always check the assembler's actual
memory report. Guards cover PRG size, 16KB pixie region, byte-sized glyph bases,
player frame length and page alignment.

