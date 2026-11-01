// ----------------------------------------------------------------------------
// HUD: score (6 BCD digits), lives and shield bar at the top of the screen.
//
// Both boxes are pixie objects with fixed screen positions (fine scrolling moves
// the text rows, the pixie y offset compensates). Their 8 glyphs live in the pixie
// glyph area (HUD_GLYPH + 2*k, k = 0..7, each followed by a blank guard) and are
// rebuilt in a bank-0 buffer and copied only when score, lives or shield change.
// Score box: columns 0-2 = 6 digits, column 3 = plane icon + lives digit.
// Credits box: columns 4-6 = '$' icon + 4 digits. Shield box: columns 7-10.
// Special box: columns 11-13 = bomb icon + count, invulnerability icon + count (shop items).
// ----------------------------------------------------------------------------
.label hud_dirty = $59      // bit 0 score + lives, bit 1 shield
.label hp_src    = $5a      // 16 bit
.label hp_dst    = $5c      // 16 bit
.label hud_ptr   = $60      // 32 bit
.label score_bcd = $64      // 3 bytes, most significant first (6 digits)
.label credit_bcd = $68     // 2 bytes, most significant first (4 digits, max. 9999)

.const HUD_Y       = 2
.const HUD_SCORE_X = 4
.const HUD_SHIELD_X = 320 - 64 - 4
.const HUD_CREDITS_X = 96
.const HUD_SPECIAL_X = 168
.const HUD_COLS     = 14
.const CREDITS_BUF  = 4*64      // credits box in hud_buf
.const SHIELD_BUF   = 7*64      // shield box in hud_buf
.const SPECIAL_BUF  = 11*64     // bombs / invulnerability box in hud_buf

hud_reset:
    lda #0
    sta credit_bcd
    sta credit_bcd+1
#if TEST_CREDITS
    lda #$09                    // test build (build.py --test-credits): 999 credits
    sta credit_bcd
    lda #$99
    sta credit_bcd+1
    lda #0
#endif
    sta score_bcd
    sta score_bcd+1
    sta score_bcd+2
    lda #3
    sta hud_dirty
    rts

hud_score_changed:
    lda hud_dirty
    ora #1
    sta hud_dirty
    rts

hud_shield_changed:
    lda hud_dirty
    ora #2
    sta hud_dirty
    rts

// add A (BCD, 0-99) credits, saturating at 9999
credits_add:
    sed
    clc
    adc credit_bcd+1
    sta credit_bcd+1
    lda credit_bcd
    adc #0
    sta credit_bcd
    cld
    bcc !+
    lda #$99
    sta credit_bcd
    sta credit_bcd+1
!:  jmp hud_score_changed

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
    // copy the glyphs to bank 5
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
    cpx #HUD_COLS
    bne !col-
    ldz #0
    rts

hud_render_score:
    ldx #63                     // column 3: plane icon, lives digit drawn below
!:  lda hud_lives_tpl,x
    sta hud_buf+3*64,x
    dex
    bpl !-
    ldx #191                    // credits box template
!:  lda hud_credits_tpl,x
    sta hud_buf+CREDITS_BUF,x
    dex
    cpx #$ff
    bne !-
    ldx #191                    // bombs / invulnerability box template
!:  lda hud_special_tpl,x
    sta hud_buf+SPECIAL_BUF,x
    dex
    cpx #$ff
    bne !-
    ldx #0
!digit:
    cpx #11                     // digits 11-12 = bombs, invulnerability (0-9)
    bcc !+
    lda bomb_count-11,x
    jmp !got+
!:  cpx #7                      // digits 7-10 = credits
    bcc !+
    txa
    sec
    sbc #7
    lsr
    tay
    lda credit_bcd,y
    bcs !low+
    lsr
    lsr
    lsr
    lsr
    bpl !got+
!:  cpx #6                      // digit 6 = lives (0-9)
    bne !+
    lda pl_lives
    cmp #10
    bcc !got+
    lda #9
    bne !got+
!:  txa
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
    cpx #13
    bne !digit-
    ldz #0
    rts

hud_render_shield:
    ldx #0
!:  lda hud_template,x
    sta hud_buf+SHIELD_BUF,x
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
        lda hud_buf+SHIELD_BUF+r*8,x
        and #$f0
        ora hs_lo
        sta hud_buf+SHIELD_BUF+r*8,x
    }
    jmp !next+
!odd:
    .for (var r = 2; r < 6; r++) {
        lda hud_buf+SHIELD_BUF+r*8,x
        and #$0f
        ora hs_hi
        sta hud_buf+SHIELD_BUF+r*8,x
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
    lda #<HUD_CREDITS_X
    sta px_x
    lda #>HUD_CREDITS_X
    sta px_x+1
    lda #FR_HUD_CREDITS
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
    jsr pixie_draw
    lda #HUD_Y
    sta px_y
    lda #0
    sta px_y+1
    lda #<HUD_SPECIAL_X
    sta px_x
    lda #>HUD_SPECIAL_X
    sta px_x+1
    lda #FR_HUD_SPECIAL
    jmp pixie_draw

hs_lo: .byte 0
hs_hi: .byte 0
hs_px: .byte 0
hs_n:  .byte 0

.align $100
hud_buf:      .fill HUD_COLS*64, 0   // 4 score/lives glyphs, 4 shield glyphs
hud_digits:   .import binary "../build/gen/hud.bin", 0, 320
hud_lives_tpl:.import binary "../build/gen/hud.bin", 320, 64
hud_credits_tpl: .import binary "../build/gen/hud.bin", 384, 192
hud_template: .import binary "../build/gen/hud.bin", 576, 256
hud_special_tpl: .import binary "../build/gen/hud.bin", 832, 192
digit_src_lo: .fill 10, <(hud_digits + i*32)
digit_src_hi: .fill 10, >(hud_digits + i*32)
// digits 0-5 score, 6 lives (column 3, right half), 7-10 credits (box pixels 8, 16, 24, 32),
// 11 bombs (special box pixel 8), 12 invulnerability (pixel 32)
.function digit_dst(i) {
    .if (i < 6) .return hud_buf + (i>>1)*64 + (i&1)*4
    .if (i == 6) .return hud_buf + 3*64 + 4
    .if (i == 11) .return hud_buf + SPECIAL_BUF + 4
    .if (i == 12) .return hud_buf + SPECIAL_BUF + 2*64
    .eval var px = 8 + (i-7)*8
    .return hud_buf + CREDITS_BUF + (px>>4)*64 + ((px>>3)&1)*4
}
digit_dst_lo: .fill 13, <digit_dst(i)
digit_dst_hi: .fill 13, >digit_dst(i)
hud_src_lo:   .fill HUD_COLS, <(hud_buf + i*64)
hud_src_hi:   .fill HUD_COLS, >(hud_buf + i*64)
hud_dst_lo:   .fill HUD_COLS, <(((PIXIE_ADDR & $ffff) + (HUD_GLYPH + 2*i)*64))
hud_dst_hi:   .fill HUD_COLS, >(((PIXIE_ADDR & $ffff) + (HUD_GLYPH + 2*i)*64))
.errorif (HUD_GLYPH + 2*HUD_COLS > PIXIE_MAX), "HUD glyphs outside the pixie area"
