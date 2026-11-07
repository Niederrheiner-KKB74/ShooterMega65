// ----------------------------------------------------------------------------
// Text pages (Stage 16): Hall of Fame, name entry, MISSION ACCOMPLISHED.
//
// The upper title rows (the "Shooter65" logo, title rows 0..TP_LOGO_ROWS-1) stay on screen; below them text is
// drawn pixel by pixel with a 6-px font (5x7 from the shop, file TRANS -> tp_font) into a block of 16 x 15
// glyphs (256 x 120 px) in the landscape glyph area ($40000, char $1000; free on the title screen, every game start
// copies the level's glyphs back from attic RAM). Text line L (0-14) = glyphs L*16 .. L*16+15, shown in screen row
// tp_rowmap; glyph 255 stays empty (blank tokens). Palette bank 2 (PAL_TEXT). Attic RAM only.
// ----------------------------------------------------------------------------
.const TP_ADDR      = TILE_ADDR
.const TP_CHAR      = TILE_CHAR
.const TP_LINES     = 15
.const TP_COLS      = 16
.const TP_COL0      = 2                       // first text token of the 20 visible ones (centred)
.const TP_BLANK     = 255
.const TP_LOGO_ROWS = 5
.const PAL_TEXT     = (2 << 4) | $0f
.label tp_ptr       = $80                     // 32-bit pointer into the glyph block (zero page $80-$83)
.label tp_font      = $0800                   // 64 characters x 8 bytes (BASIC's saved screen area)
.errorif (TP_LINES * TP_COLS > TP_BLANK), "text block reaches the blank glyph"
.errorif (TP_ADDR + 256 * 64 > SHOP_ADDR), "text block beyond the landscape glyphs"

// text colours (bank 2)
.const TC_WHITE = 1
.const TC_SHADE = 2
.const TC_GOLD  = 3
.const TC_BLUE  = 4
.const TC_GREY  = 5
.const TC_ORANGE = 6
.const TC_GREEN = 7
.const TC_RED   = 8
tp_rgb:  // r, g, b of colours 0-15 (written with swapped nibbles)
    .byte 4, 240, 10, 255, 120, 150, 255, 90, 210, 0, 0, 0, 0, 0, 0, 0
    .byte 8, 244, 10, 206, 200, 160, 120, 220, 60, 0, 0, 0, 0, 0, 0, 0
    .byte 22, 250, 20, 64, 255, 180, 60, 120, 50, 0, 0, 0, 0, 0, 0, 0

// screen rows 0-24 -> text line ($ff: blank, $fe: title row)
tp_rowmap: .byte $fe, $fe, $fe, $fe, $fe, $ff, 0, 1, $ff, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, $ff, 13, $ff, 14, $ff

tp_x:     .byte 0                       // pen position (pixels in the block)
tp_y:     .byte 0                       // pixel row in the block (line * 8)
tp_c:     .byte TC_WHITE                // ink
tp_sh:    .byte TC_SHADE                // shadow (0 = none)
tp_scale: .byte 1
tp_px:    .byte 0
tp_py:    .byte 0
tp_pc:    .byte 0
tp_t:     .byte 0
tp_m:     .byte 0
tp_r:     .byte 0
tp_k:     .byte 0
tp_ch:    .byte 0
tp_chh:   .byte 0
tp_rowbuf: .fill 40, 0

// font into place, text block empty, bank-2 palette, the page tokens in screen A (logo rows from the title)
tp_open:
    RunDma(job_tp_font)
    RunDma(job_tp_clear)
    lda #0
    sta tp_ptr+3
    lda #(TP_ADDR >> 16)
    sta tp_ptr+2
    lda #0
    sta VIC_PALSEL
    ldx #15
!:  lda tp_rgb,x
    jsr tp_swap
    sta PAL_RED+$20,x
    lda tp_rgb+16,x
    jsr tp_swap
    sta PAL_GREEN+$20,x
    lda tp_rgb+32,x
    jsr tp_swap
    sta PAL_BLUE+$20,x
    dex
    bpl !-
    lda #$10                    // background/border: title colour 0 (the logo's background)
    sta VIC_BGCOL
    sta VIC_BORDER
    lda #0
    sta tt_row
!row:
    ldx tt_row
    lda tp_rowmap,x
    cmp #$fe
    bne !+
    jsr title_row               // logo row of the title picture
    jmp !next+
!:  jsr tp_tokens
!next:
    inc tt_row
    lda tt_row
    cmp #25
    bne !row-
    rts

tp_swap:                        // nibble swap (palette registers)
    asl
    adc #$80
    rol
    asl
    adc #$80
    rol
    rts

// screen row tt_row: 20 tokens of text line tp_rowmap (or blanks)
tp_tokens:
    ldx tt_row
    lda tp_rowmap,x
    sta tp_t
    ldx #0
!:  lda #TP_BLANK
    sta tp_rowbuf,x
    lda #0
    sta tp_rowbuf+1,x
    inx
    inx
    cpx #40
    bne !-
    lda tp_t
    cmp #TP_LINES
    bcs !blit+
    asl                         // first glyph of the line: line * 16
    asl
    asl
    asl
    ldx #TP_COL0 * 2
!:  sta tp_rowbuf,x
    clc
    adc #1
    inx
    inx
    cpx #(TP_COL0 + TP_COLS) * 2
    bne !-
!blit:
    lda #<tp_rowbuf
    sta bw_sp
    lda #>tp_rowbuf
    sta bw_sp+1
    lda #0
    sta bw_sp+2
    sta bw_sp+3
    lda #1
    sta bw_rows
    lda #20
    sta bw_cols
    ldx tt_row
    inx
    stx bw_row0
    lda #2
    sta bw_col2
    lda #<TP_CHAR
    sta bw_chr
    lda #>TP_CHAR
    sta bw_chr+1
    lda #PAL_TEXT
    sta bw_pal
    lda #1
    sta bw_bufs
    jmp blit_words

// clear text line A
tp_clear_line:
    asl                         // line * 1024 = (line * 4) << 8
    asl
    clc
    adc #>(TP_ADDR & $ffff)
    sta job_tp_line+DMA_DST+1
    RunDma(job_tp_line)
    rts

// text at A/X (0-terminated ASCII), pen tp_x / tp_y, colours tp_c / tp_sh, tp_scale 1 or 2
tp_text:
    sta tp_src+1
    stx tp_src+2
!:
tp_src:
    lda $ffff
    beq !done+
    jsr tp_char
    inc tp_src+1
    bne !-
    inc tp_src+2
    bne !-
!done:
    rts

// one character A at the pen, pen advances 6 * scale
tp_char:
    sec
    sbc #$20
    cmp #64
    bcc !+
    lda #0
!:  ldx #0                      // characters 32-63 in the second half of the font
    cmp #32
    bcc !+
    inx
!:  stx tp_chh
    asl
    asl
    asl
    sta tp_ch
    lda tp_sh                   // shadow first, one pixel down right
    beq !ink+
    sta tp_pc
    lda #1
    jsr tp_glyph
!ink:
    lda tp_c
    sta tp_pc
    lda #0
    jsr tp_glyph
    lda tp_scale
    asl
    adc tp_scale
    asl                         // 6 * scale
    clc
    adc tp_x
    sta tp_x
    rts

// draw font character tp_ch in colour tp_pc at the pen + A (shadow offset)
tp_glyph:
    sta tp_k
    lda #0
    sta tp_r
!row:
    lda tp_ch
    clc
    adc tp_r
    tax
    lda tp_chh
    bne !hi+
    lda tp_font,x
    jmp !+
!hi:
    lda tp_font+256,x
!:  sta tp_m
    ldx #0                      // column 0-4
!col:
    lda tp_m
    and tp_bit,x
    beq !next+
    stx tp_t                    // pixel block scale x scale at pen + col * scale, y + row * scale
    lda tp_scale
    cmp #2
    beq !big+
    txa
    clc
    adc tp_x
    adc tp_k
    sta tp_px
    lda tp_r
    clc
    adc tp_y
    adc tp_k
    sta tp_py
    jsr tp_plot
    jmp !nx+
!big:
    txa
    asl
    clc
    adc tp_x
    adc tp_k
    sta tp_px
    lda tp_r
    asl
    clc
    adc tp_y
    adc tp_k
    sta tp_py
    jsr tp_plot
    inc tp_px
    jsr tp_plot
    inc tp_py
    jsr tp_plot
    dec tp_px
    jsr tp_plot
!nx:
    ldx tp_t
!next:
    inx
    cpx #5
    bne !col-
    inc tp_r
    lda tp_r
    cmp #7
    beq !+
    jmp !row-
!:  rts
tp_bit: .byte $10, $08, $04, $02, $01

// pixel tp_px / tp_py (0-119) := tp_pc
tp_plot:
    lda tp_py
    cmp #TP_LINES * 8
    bcs !out+
    lsr                         // (line * 1024 + (x >> 4) * 64) >> 8 = line * 4 + (x >> 6)
    lsr
    lsr
    asl
    asl
    sta tp_ptr+1
    lda tp_px
    lsr
    lsr
    lsr
    lsr
    lsr
    lsr
    clc
    adc tp_ptr+1
    adc #>(TP_ADDR & $ffff)
    sta tp_ptr+1
    lda tp_px                   // low byte: ((x >> 4) & 3) * 64 + row * 8 + (x & 15) / 2
    and #$30
    asl
    asl
    sta tp_ptr
    lda tp_py
    and #7
    asl
    asl
    asl
    ora tp_ptr
    sta tp_ptr
    lda tp_px
    and #$0e
    lsr
    ora tp_ptr
    sta tp_ptr
    ldz #0
    lda tp_px
    and #1
    bne !hi+
    lda ((tp_ptr)),z
    and #$f0
    ora tp_pc
    sta ((tp_ptr)),z
!out:
    rts
!hi:
    lda tp_pc
    asl
    asl
    asl
    asl
    sta tp_hn
    lda ((tp_ptr)),z
    and #$0f
    ora tp_hn
    sta ((tp_ptr)),z
    rts
tp_hn: .byte 0

// pen to (A = x, X = line), scale 1, white with shadow
tp_at:
    sta tp_x
    txa
    asl
    asl
    asl
    sta tp_y
    lda #1
    sta tp_scale
    rts

// 6 BCD digits at A/X (3 bytes); leading zeros as spaces (the last digit always)
tp_score:
    sta tp_bcd+1
    stx tp_bcd+2
    lda tp_zi                   // 1: leading zeros are shown
    sta tp_z
    lda #0
    sta tp_i
!:  lda tp_i
    lsr
    tay
tp_bcd:
    lda $ffff,y
    ldx tp_i
    cpx #5
    beq !d+
    pha
    txa
    and #1
    tax
    pla
    cpx #0
    bne !lo+
    lsr
    lsr
    lsr
    lsr
!lo:
    and #$0f
    bne !nz+
    ldx tp_z
    bne !nz+
    lda #$20
    bne !put+
!d: and #$0f
!nz:
    ldx #1
    stx tp_z
    ora #$30
!put:
    jsr tp_char
    inc tp_i
    lda tp_i
    cmp #6
    bne !-
    rts
tp_z: .byte 0
tp_zi: .byte 0
tp_i: .byte 0

job_tp_font:  DmaJob(DMA_CMD_COPY, ATTIC_TRANS + TR_FONT_OFS, tp_font, 64 * 8)
job_tp_clear: DmaJob(DMA_CMD_FILL, 0, TP_ADDR, 256 * 64)
job_tp_line:  DmaJob(DMA_CMD_FILL, 0, TP_ADDR, TP_COLS * 64)
