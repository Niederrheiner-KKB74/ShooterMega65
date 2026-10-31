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
.const TILE_ADDR    = $040000            // landscape NCM glyphs  -> char $1000+
.const PIXIE_ADDR   = $050000            // pixie NCM glyphs      -> char $1400+
.const SCREEN_A     = $054000            // RRB screen buffer A (27 x 170 bytes)
.const SCREEN_B     = $056000            // RRB screen buffer B
.const RING_SCR     = $058000            // 64 x 170 bytes decoded map rows (screen part)
.const RING_COL     = $05b000            // 64 x 170 bytes decoded map rows (colour part)
.const SPRITE_ADDR  = $05f000            // player sprites (256 bytes each)

// Colour RAM (offsets; CPU/DMA see it at $ff80000)
.const COLRAM       = $ff80000
.const COLOUR_A     = $0800
.const COLOUR_B     = $2000

.const TILE_CHAR    = TILE_ADDR / 64     // $1000
.const PIXIE_CHAR   = PIXIE_ADDR / 64    // $1400
.const SPRITE_PTR0  = SPRITE_ADDR / 64
.const SPRITE_PTR1  = (SPRITE_ADDR + $100) / 64

// Bank 0
.const SPRPTR_TABLE = $1f00              // 16-bit sprite pointer table (8 x 2 bytes)

.if (ROW_BYTES * 2 * RING_SLOTS > $3000) .error "ring buffer too large"
.if (SCREEN_A + ROW_BYTES * BUF_ROWS > SCREEN_B) .error "screen buffer A overlaps B"
.if (SCREEN_B + ROW_BYTES * BUF_ROWS > RING_SCR) .error "screen buffer B overlaps ring"
.if (COLOUR_A + ROW_BYTES * BUF_ROWS > COLOUR_B) .error "colour buffer A overlaps B"
