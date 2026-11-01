// ----------------------------------------------------------------------------
// HUD: score (6 BCD digits) and shield bar at the top of the screen.
//
// Both boxes are pixie objects with fixed screen positions (fine scrolling moves
// the text rows, the pixie y offset compensates). Their 7 glyphs live in the pixie
// glyph area (HUD_GLYPH + 2*k, k = 0..6, each followed by a blank guard) and are
// rebuilt in a bank-0 buffer and copied only when the score or the shield changes.
// ----------------------------------------------------------------------------
.label hud_dirty = $59      // bit 0 score, bit 1 shield
.label hp_src    = $5a      // 16 bit
.label hp_dst    = $5c      // 16 bit
.label hud_ptr   = $60      // 32 bit
.label score_bcd = $64      // 3 bytes, most significant first (6 digits)

.const HUD_Y       = 2
.const HUD_SCORE_X = 4
.const HUD_SHIELD_X = 320 - 64 - 4

hud_reset:
    lda #0
    sta score_bcd
    sta score_bcd+1
    sta score_bcd+2
    lda #3
    sta hud_dirty
    rts

hud_shield_changed:
    lda hud_dirty
    ora #2
    sta hud_dirty
    rts

// add A (low BCD byte) + X (high BCD byte) points
score_add:
    sed
    clc
    adc score_bcd+2
    sta score_bcd+2
    txa
    adc score_bcd+1
    sta score_bcd+1
    lda #0
    adc score_bcd
    sta score_bcd
    cld
    lda hud_dirty
    ora #1
    sta hud_dirty
    rts

// rebuild changed boxes and copy them to the glyph area
hud_update:
    lda hud_dirty
    bne !+
    rts
!:  lsr
    bcc !+
    jsr hud_render_score
!:  lda hud_dirty
    and #2
    beq !+
    jsr hud_render_shield
!:  lda #0
    sta hud_dirty
    // copy 7 glyphs to bank 5
    lda #(PIXIE_ADDR >> 16)
    sta hud_ptr+2
    lda #0
    sta hud_ptr+3
    ldx #0
!col:
    lda hud_dst_lo,x
    sta hud_ptr
    lda hud_dst_hi,x
    sta hud_ptr+1
    lda hud_src_lo,x
    sta hp_src
    lda hud_src_hi,x
    sta hp_src+1
    ldy #0
    ldz #0
!:  lda (hp_src),y
    sta ((hud_ptr)),z
    iny
    inz
    cpy #64
    bne !-
    inx
    cpx #7
    bne !col-
    ldz #0
    rts

hud_render_score:
    ldx #0
!digit:
    txa
    lsr
    tay
    lda score_bcd,y
    bcs !low+                   // odd digit index: low nibble
    lsr
    lsr
    lsr
    lsr
    bpl !got+
!low:
    and #$0f
!got:
    tay
    lda digit_src_lo,y
    sta hp_src
    lda digit_src_hi,y
    sta hp_src+1
    lda digit_dst_lo,x
    sta hp_dst
    lda digit_dst_hi,x
    sta hp_dst+1
    ldy #0                      // source: 4 bytes per row, destination: 8 bytes per row
    ldz #0
!row:
    lda (hp_src),y
    sta (hp_dst),z
    iny
    inz
    lda (hp_src),y
    sta (hp_dst),z
    iny
    inz
    lda (hp_src),y
    sta (hp_dst),z
    iny
    inz
    lda (hp_src),y
    sta (hp_dst),z
    iny
    inz
    inz
    inz
    inz
    inz
    cpy #32
    bne !row-
    inx
    cpx #6
    bne !digit-
    ldz #0
    rts

hud_render_shield:
    ldx #0
!:  lda hud_template,x
    sta hud_buf+192,x
    inx
    bne !-
    // colour by level: high / medium / low
    lda pl_shield
    ldy #6
    cmp #SHIELD_MAX/2+1
    bcs !+
    ldy #7
    cmp #SHIELD_MAX/4+1
    bcs !+
    ldy #8
!:  sty hs_lo
    tya
    asl
    asl
    asl
    asl
    sta hs_hi
    lda #BAR_X0
    sta hs_px
    lda pl_shield
    beq !done+
    sta hs_n
!px:
    // X = column*64 + byte within the row
    lda hs_px
    and #$f0
    asl
    asl
    sta tmp                     // column * 64
    lda hs_px
    and #$0f
    lsr
    ora tmp
    tax
    lda hs_px
    and #1
    bne !odd+
    .for (var r = 2; r < 6; r++) {
        lda hud_buf+192+r*8,x
        and #$f0
        ora hs_lo
        sta hud_buf+192+r*8,x
    }
    jmp !next+
!odd:
    .for (var r = 2; r < 6; r++) {
        lda hud_buf+192+r*8,x
        and #$0f
        ora hs_hi
        sta hud_buf+192+r*8,x
    }
!next:
    inc hs_px
    dec hs_n
    bne !px-
!done:
    rts

// draw both boxes (call last, so they are on top)
hud_draw:
    lda #PAL_HUD
    sta px_pal
    lda #0
    sta px_y+1
    sta px_x+1
    lda #HUD_Y
    sta px_y
    lda #HUD_SCORE_X
    sta px_x
    lda #FR_HUD_SCORE
    jsr pixie_draw
    lda #HUD_Y
    sta px_y
    lda #0
    sta px_y+1
    lda #<HUD_SHIELD_X
    sta px_x
    lda #>HUD_SHIELD_X
    sta px_x+1
    lda #FR_HUD_SHIELD
    jmp pixie_draw

hs_lo: .byte 0
hs_hi: .byte 0
hs_px: .byte 0
hs_n:  .byte 0

.align $100
hud_buf:      .fill 7*64, 0          // 3 score glyphs, 4 shield glyphs
hud_digits:   .import binary "../build/gen/hud.bin", 0, 320
hud_template: .import binary "../build/gen/hud.bin", 320, 256
digit_src_lo: .fill 10, <(hud_digits + i*32)
digit_src_hi: .fill 10, >(hud_digits + i*32)
digit_dst_lo: .fill 6, <(hud_buf + (i>>1)*64 + (i&1)*4)
digit_dst_hi: .fill 6, >(hud_buf + (i>>1)*64 + (i&1)*4)
hud_src_lo:   .fill 7, <(hud_buf + i*64)
hud_src_hi:   .fill 7, >(hud_buf + i*64)
hud_dst_lo:   .fill 7, <(((PIXIE_ADDR & $ffff) + (HUD_GLYPH + 2*i)*64))
hud_dst_hi:   .fill 7, >(((PIXIE_ADDR & $ffff) + (HUD_GLYPH + 2*i)*64))
.errorif ((HUD_GLYPH + 14) * 64 > $4000), "HUD glyphs outside the pixie area"
