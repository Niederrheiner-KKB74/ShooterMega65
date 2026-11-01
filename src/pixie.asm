// ----------------------------------------------------------------------------
// RRB pixie emitter
//
// A pixie frame is w NCM chars wide (16 px each) and h glyph rows high.
// Glyph layout (made by tools/import_art.py): column c, row i is character
// base + c*(h+1) + i (base = absolute character number), and the glyph directly before every column
// and the glyph after it are blank. Vertical sub-row positioning uses the
// GOTOX Y offset (screen byte 1: bit 4 set + offset in bits 5-7 = glyph rows are
// fetched "offset" lines earlier), so an object at sub-row k touches h+1 rows:
// row i shows the bottom k lines of glyph i-1 and the top 8-k lines of glyph i.
// This is the hardware-verified Vyper format ($10 + k<<5, colour $90/$00).
//
// One fragment per touched row: GOTOX token + w glyph tokens, appended to the
// row's overlay area in the back buffer.
// ----------------------------------------------------------------------------

.label px_x    = $1c      // 16 bit signed screen x (0 = left edge of the playfield)
.label px_y    = $1e      // 16 bit signed screen y
.label px_pal  = $20      // colour RAM byte 1 for the glyphs: palette bank << 4 | $0f
.label px_gx   = $21      // 16 bit GOTOX value
.label px_gy   = $23      // 16 bit y in row-grid coordinates
.label px_r0   = $25      // first row (signed)
.label px_yb   = $26      // GOTOX screen byte 1 bits (Y offset)
.label px_n    = $27      // rows to emit
.label px_i    = $28
.label px_base = $29
.label px_w    = $2a
.label px_h    = $2b
.label px_need = $2c
.label px_row  = $2d
.label px_gl   = $2e      // 16 bit glyph number
.label px_bhi  = $30      // frame base, high byte

// in: px_x, px_y, px_pal, A = frame number
pixie_draw:
    tax
    lda frame_base,x
    sta px_base
    lda frame_base_hi,x
    sta px_bhi
    lda frame_w,x
    sta px_w
    asl
    clc
    adc #2
    sta px_need
    lda frame_h,x
    sta px_h
    // GOTOX = x + 16; visible if 0 <= GOTOX < 336
    clc
    lda px_x
    adc #GOTOX_BIAS
    sta px_gx
    lda px_x+1
    adc #0
    sta px_gx+1
    bmi !skip+
    beq !xok+
    cmp #1
    bne !skip+
    lda px_gx
    cmp #<336
    bcs !skip+
!xok:
    // gy = y + 8 - fine
    clc
    lda px_y
    adc #8
    sta px_gy
    lda px_y+1
    adc #0
    sta px_gy+1
    sec
    lda px_gy
    sbc fine
    sta px_gy
    lda px_gy+1
    sbc #0
    sta px_gy+1
    bmi !neg+
    bne !skip+                  // >= 256: below the screen
    lda px_gy
    cmp #VIS_ROWS*8
    bcs !skip+
    bcc !rows+
!neg:
    cmp #$ff                    // more than 256 px above: skip
    bne !skip+
!rows:
    lda px_gy
    and #7
    tax
    lda ybits_tab,x
    sta px_yb
    cpx #1                      // carry = (k != 0)
    lda px_h
    adc #0
    sta px_n
    // r0 = gy >> 3 (arithmetic, result fits a signed byte)
    lda px_gy+1
    sta px_row
    lda px_gy
    lsr px_row
    ror
    lsr px_row
    ror
    lsr px_row
    ror
    sta px_r0
    lda #0
    sta px_i
!loop:
    lda px_r0
    clc
    adc px_i
    bmi !next+                  // row above the screen
    cmp #VIS_ROWS
    bcs !done+                  // further rows are below as well
    sta px_row
    jsr emit_fragment
!next:
    inc px_i
    lda px_i
    cmp px_n
    bne !loop-
!done:
!skip:
    rts

// emit row px_i of the current frame into display row px_row
emit_fragment:
    ldx px_row
    lda rowfill,x
    clc
    adc px_need
    cmp #OVL_END+1
    bcc !fits+
    inc overflow
    rts
!fits:
    pha                         // new fill level
    lda rowfill,x               // offset = row_ofs[row] + rowfill[row]
    clc
    adc row_ofs_lo,x
    sta tmp
    lda row_ofs_hi,x
    adc #0
    sta tmp+1
    clc
    lda tmp
    adc backscr
    sta scr_ptr
    lda tmp+1
    adc backscr+1
    sta scr_ptr+1
    lda #(SCREEN_A >> 16)
    sta scr_ptr+2
    lda #0
    sta scr_ptr+3
    clc
    lda tmp
    adc backcol
    sta col_ptr
    lda tmp+1
    adc backcol+1
    sta col_ptr+1
    lda #(COLRAM >> 16) & $ff
    sta col_ptr+2
    lda #(COLRAM >> 24)
    sta col_ptr+3
    pla
    sta rowfill,x

    // glyph = base + i (absolute character number)
    clc
    lda px_base
    adc px_i
    sta px_gl
    lda px_bhi
    adc #0
    sta px_gl+1

    ldz #0
    lda px_gx                   // GOTOX token
    sta ((scr_ptr)),z
    lda #$90                    // GOTOX, no background paint (transparent)
    sta ((col_ptr)),z
    inz
    lda px_gx+1
    and #3
    ora px_yb
    sta ((scr_ptr)),z
    lda #$00
    sta ((col_ptr)),z
    inz
    ldx px_w
!col:
    lda px_gl
    sta ((scr_ptr)),z
    lda #$08                    // NCM glyph
    sta ((col_ptr)),z
    inz
    lda px_gl+1
    sta ((scr_ptr)),z
    lda px_pal
    sta ((col_ptr)),z
    inz
    dex
    beq !end+
    clc                         // next column: + h + 1 glyphs
    lda px_gl
    adc px_h
    sta px_gl
    bcc !+
    inc px_gl+1
!:  inc px_gl
    bne !col-
    inc px_gl+1
    bne !col-
!end:
    rts

ybits_tab:  .fill 8, $10 + (i << 5)
row_ofs_lo: .fill VIS_ROWS, <(i * ROW_BYTES)
row_ofs_hi: .fill VIS_ROWS, >(i * ROW_BYTES)
rowfill:    .fill VIS_ROWS, 0
