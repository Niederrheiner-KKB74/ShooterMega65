// ----------------------------------------------------------------------------
// Memory layout (see docs/memory_map.md). All addresses are 28-bit physical.
// ----------------------------------------------------------------------------

// Screen geometry
.const BG_TOKENS    = 21                 // 21 NCM background chars = 336 px (x 0..15 hidden by border)
.const ROW_TOKENS   = 85                 // tokens per RRB row (CHRCOUNT)
.const ROW_BYTES    = ROW_TOKENS * 2     // 170 bytes per row (LINESTEP)
.const OVL_START    = BG_TOKENS * 2      // first overlay byte in a row (42)
.const OVL_END      = (ROW_TOKENS - 1) * 2   // last token (168) stays a blank char: overlay must end before it
.const VIS_ROWS     = 26                 // rows 0..25 visible (row 0 partly hidden above the top border)
.const BUF_ROWS     = 27                 // + one null row under the bottom border
.const RING_SLOTS   = 32                 // ring buffer of decoded map rows, stored twice (64 slots)
.const GOTOX_BIAS   = 16                 // logical x 0 of the playfield = GOTOX 16

// Chip RAM
.const TILE_ADDR    = $040000            // landscape NCM glyphs  -> char $1000+ (max. 512 glyphs, $40000-$47FFF)
.const PIXIE_ADDR   = $046800            // pixie NCM glyphs      -> char $11A0+ (max. 608 glyphs, $46800-$4FFFF)
                                         // (directly behind the 160 glyphs reserved for the shop at $44000)
.const SCREEN_A     = $054000            // RRB screen buffer A (27 x 170 bytes)
.const SCREEN_B     = $056000            // RRB screen buffer B
.const PIXIE3_ADDR  = $055200            // Stage 15: diagonal enemy shots (file PIXIES3, 24 glyphs max., char $1548+)
.const RING_SCR     = $058000            // 64 x 170 bytes decoded map rows (screen part)
.const RING_COL     = $05b000            // 64 x 170 bytes decoded map rows (colour part)
.const SAVED_PAL0   = $05db00            // Stage 13: BASIC's palette 0 (768 bytes) until exit
.const SAVED_ZP     = $05de00            // Stage 13: BASIC's zero page (256 bytes) until exit
.const SAVED_GZP    = $05df00            // Stage 16: the game's zero page during a KERNAL session (hiscore.asm)
.const SAVED_SCR    = $055800            // Stage 16: BASIC's text screen $0800-$0FFF (2 KB) until exit
.errorif (RING_COL + 64 * 170 > SAVED_PAL0 || SAVED_PAL0 + 768 > SAVED_ZP || SAVED_ZP + 256 > $05e000), "SAVED_PAL0/SAVED_ZP overlap the ring or the destroyed tiles"
.const SPRITE_ADDR  = $05f000            // player sprites (256 bytes each)
.const RING_ADDR    = $05fc00            // invulnerability ring, sprites 2-4 (256 bytes each)
.const RING_PTR     = RING_ADDR / 64

// Special weapons (special.asm)
.const INV_LONG     = 500                // bought invulnerability: 10 s
.const INV_WARN     = 100                // ring blinks during the last 2 s
.const MS_SPEED     = 3                  // homing missile: px per frame on each axis
.const MS_LIFE      = 200                // frames until a missile gives up
.const FLASH_FRAMES = 4                  // bomb flash

// Boss hit flash (boss.asm): hit parts are drawn with a lightened copy of the boss palette in bank 6
// (the bomber palette; no bombers during the boss fight)
.const FLASH_BANK       = 6
.const PAL_BOSS_FLASH   = (FLASH_BANK << 4) | $0f
.const FLASH_FRAMES_HIT = 4

// Colour RAM (offsets; CPU/DMA see it at $ff80000)
.const COLRAM       = $ff80000
.const COLOUR_A     = $1000            // $0000-$0FFF stays BASIC's (80x50 uses 4000 bytes)
.const COLOUR_B     = $2400

.const TILE_CHAR    = TILE_ADDR / 64     // $1000
.const PIXIE_CHAR   = PIXIE_ADDR / 64    // $11A0 (frame bases in frames.inc are absolute character numbers)
.const PIXIE_MAX    = ($04F800 - PIXIE_ADDR) / 64   // 576 (Stage 8: $4F800-$4FFFF holds destroyed landscape tiles)
.const SPRITE_PTR0  = SPRITE_ADDR / 64
.const SPRITE_PTR1  = (SPRITE_ADDR + $100) / 64


.if (ROW_BYTES * 2 * RING_SLOTS > $3000) .error "ring buffer too large"
.if (SCREEN_A + ROW_BYTES * BUF_ROWS > SCREEN_B) .error "screen buffer A overlaps B"
.if (SCREEN_A + ROW_BYTES * BUF_ROWS > PIXIE3_ADDR) .error "screen buffer A overlaps the diagonal shots"
.if (SCREEN_B + ROW_BYTES * BUF_ROWS > RING_SCR) .error "screen buffer B overlaps ring"
.if (COLOUR_A + ROW_BYTES * BUF_ROWS > COLOUR_B) .error "colour buffer A overlaps B"
.const CLEAR_DELAY  = 60                // Stage 15: frames between the end of the boss and LEVEL CLEAR (transition.asm)
.errorif (PIXIE3_ADDR + 24 * 64 > SAVED_SCR || SAVED_SCR + $800 > SCREEN_B), "PIXIES3 / SAVED_SCR overlap"
