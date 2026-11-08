// ----------------------------------------------------------------------------
// Tile animation (Stage 13)
//
// LnDAT carries a table from animations.json of the tile set (tools/build_level.py, header word at +24):
//   count, then per animation: period (frames per phase), phases, tiles, tile ids phase by phase.
// Phase 0 lists the tiles that the map uses. Every `period` frames the next phase is shown by copying the
// glyphs (2 x 64 bytes per tile) of that phase's tiles from the level pack in attic RAM (the untouched LnGFX)
// over the glyphs of the phase-0 tiles in chip RAM. Phase 0 comes from the pack as well, so nothing is lost.
// ----------------------------------------------------------------------------
.const ANIM_MAX    = 8
.const ANIM_BUF    = 128
.const LV_GFX_GLYPHS = 4 + 192          // offset of the glyphs in LnGFX ('SG', count, 4 palettes)

// after level_init (lev_hdr valid), X = level index: load the table
anim_init:
    lda #0
    sta anim_n
    lda lv_pack_bank,x
    sta job_anim+DMA_SRC+2
    lda lev_hdr+24
    sta job_anim_buf+DMA_SRC
    ora lev_hdr+25
    beq !rts+
    lda lev_hdr+25
    sta job_anim_buf+DMA_SRC+1
    RunDma(job_anim_buf)
    ldx #0
    ldy #1
!a:
    cpx anim_buf
    beq !done+
    tya
    sta an_off,x
    lda #1                      // first step in the next frame
    sta an_t,x
    lda #0
    sta an_ph,x
    lda anim_buf+1,y            // record length 3 + phases * tiles
    sta an_cnt
    tya
    clc
    adc #3
!m: clc
    adc anim_buf+2,y
    dec an_cnt
    bne !m-
    tay
    inx
    cpx #ANIM_MAX
    bne !a-
!done:
    stx anim_n
!rts:
    rts

// colour cycling (Stage 13d, header +26..29: bank, first index, count, frames per step; bank 0 = none;
// Stage 17b: +30/+31 a second range first2/count2, 0 = none): the colours of the list first .. first+count-1,
// first2 .. first2+count2-1 rotate by one place each step (the last one moves to the front)
cycle_frame:
    lda lev_hdr+26
    beq !rts+
    dec cy_t
    bne !rts+
    lda lev_hdr+29
    sta cy_t
    lda lev_hdr+26              // palette registers of the list
    asl
    asl
    asl
    asl
    sta cy_b
    ldy #0
    ldx lev_hdr+27
    lda lev_hdr+28
    jsr cy_range
    ldx lev_hdr+30
    lda lev_hdr+31
    beq !+
    jsr cy_range
!:  dey                         // y = last entry
    ldx cy_list,y               // its colour moves to the front
    lda PAL_RED,x
    pha
    lda PAL_GREEN,x
    pha
    lda PAL_BLUE,x
    pha
!r: cpy #0
    beq !put+
    ldx cy_list-1,y             // entry k <- entry k-1
    lda PAL_RED,x
    sta cy_r
    lda PAL_GREEN,x
    sta cy_g
    lda PAL_BLUE,x
    sta cy_bl
    ldx cy_list,y
    lda cy_r
    sta PAL_RED,x
    lda cy_g
    sta PAL_GREEN,x
    lda cy_bl
    sta PAL_BLUE,x
    dey
    jmp !r-
!put:
    ldx cy_list
    pla
    sta PAL_BLUE,x
    pla
    sta PAL_GREEN,x
    pla
    sta PAL_RED,x
!rts:
    rts

// append A registers from index X to cy_list (at Y)
cy_range:
    sta cy_n
!:  txa
    ora cy_b
    sta cy_list,y
    iny
    inx
    dec cy_n
    bne !-
    rts
cy_b:    .byte 0
cy_n:    .byte 0
cy_r:    .byte 0
cy_g:    .byte 0
cy_bl:   .byte 0
cy_list: .fill 16, 0
cy_t: .byte 1

// once per frame (build_frame)
anim_frame:
    jsr cycle_frame
    ldx anim_n
    bne !+
    rts
!:  dex
!a:
    dec an_t,x
    beq !+
    jmp !next+
!:  ldy an_off,x
    lda anim_buf,y              // period
    sta an_t,x
    inc an_ph,x                 // next phase
    lda an_ph,x
    cmp anim_buf+1,y
    bcc !+
    lda #0
    sta an_ph,x
!:  lda anim_buf+2,y            // tiles
    sta an_cnt
    tya
    clc
    adc #3
    sta an_dst                  // phase-0 ids
    ldz an_ph,x                 // + phase * tiles
    beq !s+
!m: clc
    adc anim_buf+2,y
    dez
    bne !m-
!s: sta an_src
!t:
    ldy an_src                  // source: the tile in the pack, LV_GFX_GLYPHS + id * 128
    lda anim_buf,y
    lsr
    sta job_anim+DMA_SRC+1
    lda #0
    ror
    clc
    adc #<LV_GFX_GLYPHS
    sta job_anim+DMA_SRC
    lda job_anim+DMA_SRC+1
    adc #>LV_GFX_GLYPHS
    sta job_anim+DMA_SRC+1
    ldy an_dst                  // destination: the phase-0 tile's glyphs, TILE_ADDR + id * 128
    lda anim_buf,y
    lsr
    sta job_anim+DMA_DST+1
    lda #0
    ror
    sta job_anim+DMA_DST
    RunDma(job_anim)
    inc an_src
    inc an_dst
    dec an_cnt
    bne !t-
!next:
    dex
    bmi !+
    jmp !a-
!:  ldz #0
    rts

anim_n:   .byte 0
an_cnt:   .byte 0
an_src:   .byte 0
an_dst:   .byte 0
an_off:   .fill ANIM_MAX, 0
an_t:     .fill ANIM_MAX, 0
an_ph:    .fill ANIM_MAX, 0
anim_buf: .fill ANIM_BUF, 0
job_anim_buf: DmaJob(DMA_CMD_COPY, LEVEL_BUF, anim_buf, ANIM_BUF)
job_anim:     DmaJob(DMA_CMD_COPY, ATTIC_LEVELS, TILE_ADDR, 128)
.errorif ((TILE_ADDR & $ff) != 0), "anim_frame assumes TILE_ADDR on a page boundary"
