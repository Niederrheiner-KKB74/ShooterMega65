// ----------------------------------------------------------------------------
// Video mode, palettes, buffer initialisation and page flipping
// ----------------------------------------------------------------------------

// TEXTYPOS (physical raster lines) for fine scroll 0: row 0 starts 8 px above
// the top border (104), so 88; +2 per pixel of fine scroll (V200 = 2 rasters/pixel).
.const TEXTYPOS_BASE = 104 - 16

video_init:
    lda #0
    sta VIC_SPREN
    lda VIC_D05D                // switch HOTREG off and cancel any pending recalculation;
                                // every register is then set explicitly (legacy $D011/$D016 untouched)
    and #$7f
    sta VIC_D05D
    sta VIC_D05D

    lda #$40                    // FAST, H320, V200, no ATTR, no bitplanes
    sta VIC_D031
    lda VIC_D030                // RAM palette, CRAM2K off (keeps CIA1 visible),
    and #%11111110              // ROM banking bits unchanged (restored on exit anyway)
    ora #%00000100
    sta VIC_D030
    lda VIC_D054                // keep the user's PALEMU setting (bit 5)
    and #%00100000
    ora #$45                    // CHR16 + FCLRHI + VFAST
    sta VIC_D054

    lda #104                    // top border
    sta VIC_TBDRPOS
    lda #0
    sta VIC_TBDRPOS+1
    lda #<504                   // bottom border
    sta VIC_BBDRPOS
    lda #>504
    sta VIC_BBDRPOS+1
    lda #80-32                  // text 16 logical px left of the border edge:
    sta VIC_TEXTXPOS            // logical x 0..15 of every row is hidden under the border
    lda #0
    sta VIC_TEXTXPOS+1
    lda #TEXTYPOS_BASE
    sta VIC_TEXTYPOS
    sta pend_typos
    lda #0
    sta VIC_TEXTYPOS+1
    lda #80                     // side border width (default H320)
    sta VIC_SDBDRWD
    lda #0                      // HOTREG off, border width high bits 0
    sta VIC_D05D
    lda #120                    // CHRXSCL: H320 with logical GOTOX coordinates (Vyper rule 19a)
    sta VIC_CHRXSCL

    lda #<ROW_BYTES
    sta VIC_LINESTEP
    lda #>ROW_BYTES
    sta VIC_LINESTEP+1
    lda #<ROW_TOKENS
    sta VIC_CHRCOUNT
    lda VIC_D063                // keep bits 6-7 (as Vyper does)
    and #%11000000
    ora #((>ROW_TOKENS) << 4)   // CHRCOUNT bits 8-9, screen pointer bits 24-27 = 0
    sta VIC_D063
    lda #VIS_ROWS               // rows 0..26 are fetched; row 26 is the null row
    sta VIC_DISPROWS
    lda #0
    sta VIC_D051                // NORRDEL = 0: RRB double buffering
    sta VIC_BORDER
    sta VIC_BGCOL
    jsr show_buffer_a
    jmp palette_init

palette_init:
    lda #$04                    // edit text palette 0, sprites use palette 1
    sta VIC_PALSEL
    ldx #0
!:  lda palette_data,x
    sta PAL_RED,x
    lda palette_data+$100,x
    sta PAL_GREEN,x
    lda palette_data+$200,x
    sta PAL_BLUE,x
    inx
    bne !-
    ldx #0                      // landscape banks 1-4 from the level file
!:  txa
    and #$0f
    sta tmp
    txa                         // source: bank b = x>>4 (0-3), R/G/B blocks of 16
    and #$30
    sta tmp+1
    asl                         // bank * 48 = bank*32 + bank*16
    clc
    adc tmp+1
    adc tmp
    tay
    lda lev_pal,y
    sta PAL_RED+$10,x
    lda lev_pal+16,y
    sta PAL_GREEN+$10,x
    lda lev_pal+32,y
    sta PAL_BLUE+$10,x
    inx
    cpx #64
    bne !-
    lda #$44                    // map palette 1 for editing
    sta VIC_PALSEL
    ldx #31
!:  lda sprpal_data,x
    sta PAL_RED,x
    lda sprpal_data+32,x
    sta PAL_GREEN,x
    lda sprpal_data+64,x
    sta PAL_BLUE,x
    dex
    bpl !-
    lda #$04                    // text: palette 0, sprites: palette 1
    sta VIC_PALSEL
    rts

// Copy glyphs and sprites to their final place, initialise all RRB rows.
assets_init:
    // pixie glyphs: loaded from the file PIXIES directly into the pixie area (pixies_load)
    RunDma(job_sprites)
    RunDma(job_ring)
    rts

// all RRB rows: ring, screen buffers A and B (game start; the title uses screen B and the ring)
buffers_init:
    ldx #RING_SLOTS*2
    lda #<job_ring_scr
    ldy #>job_ring_scr
    jsr dma_replicate
    ldx #RING_SLOTS*2
    lda #<job_ring_col
    ldy #>job_ring_col
    jsr dma_replicate
    jsr buffer_a_init
    ldx #BUF_ROWS
    lda #<job_scr_b
    ldy #>job_scr_b
    jsr dma_replicate
    ldx #BUF_ROWS
    lda #<job_col_b
    ldy #>job_col_b
    jmp dma_replicate

// screen buffer A and its colour RAM: empty rows (title screen)
buffer_a_init:
    ldx #BUF_ROWS
    lda #<job_scr_a
    ldy #>job_scr_a
    jsr dma_replicate
    ldx #BUF_ROWS
    lda #<job_col_a
    ldy #>job_col_a
    jmp dma_replicate

// Run the DMA job at A/Y (lo/hi) X times, advancing its destination by ROW_BYTES each time.
dma_replicate:
    sta tmp2
    sty tmp2+1
    stx rep_count
    ldy #DMA_DST+2              // remember the destination: the job must be reusable on a second RUN
!:  lda (tmp2),y
    sta rep_dst-DMA_DST,y
    dey
    cpy #DMA_DST-1
    bne !-
!loop:
    lda #0
    sta DMA_ADDRBANK
    sta DMA_ADDRMB
    lda tmp2+1
    sta DMA_ADDRMSB
    lda tmp2
    sta DMA_ADDRLSB_ETRIG
    ldy #DMA_DST
    clc
    lda (tmp2),y
    adc #<ROW_BYTES
    sta (tmp2),y
    iny
    lda (tmp2),y
    adc #>ROW_BYTES
    sta (tmp2),y
    iny
    lda (tmp2),y
    adc #0
    sta (tmp2),y
    dec rep_count
    bne !loop-
    ldy #DMA_DST+2
!:  lda rep_dst-DMA_DST,y
    sta (tmp2),y
    dey
    cpy #DMA_DST-1
    bne !-
    rts
rep_count: .byte 0
rep_dst:   .fill 3, 0

// Show the buffer that was just built (back), then make the other one the back buffer.
flip:
    lda pend_typos
    sta VIC_TEXTYPOS
    lda back
    bne !b+
    jsr show_buffer_a
    lda #1
    sta back
    rts
!b: jsr show_buffer_b
    lda #0
    sta back
    rts

show_buffer_a:
    lda #<SCREEN_A
    sta VIC_SCRNPTR
    lda #>SCREEN_A
    sta VIC_SCRNPTR+1
    lda #(SCREEN_A >> 16)
    sta VIC_SCRNPTR+2
    lda #<COLOUR_A
    sta VIC_COLPTR
    lda #>COLOUR_A
    sta VIC_COLPTR+1
    lda #0
    sta VIC_D051
    rts

show_buffer_b:
    lda #<SCREEN_B
    sta VIC_SCRNPTR
    lda #>SCREEN_B
    sta VIC_SCRNPTR+1
    lda #(SCREEN_B >> 16)
    sta VIC_SCRNPTR+2
    lda #<COLOUR_B
    sta VIC_COLPTR
    lda #>COLOUR_B
    sta VIC_COLPTR+1
    lda #0
    sta VIC_D051
    rts

// ---------------------------------------------------------------- DMA jobs
job_sprites: DmaJob(DMA_CMD_COPY, sprite_data, SPRITE_ADDR, sprite_end - sprite_data)
job_ring:    DmaJob(DMA_CMD_COPY, ring_data, RING_ADDR, ring_end - ring_data)
job_ring_scr: DmaJob(DMA_CMD_COPY, row_tpl_scr, RING_SCR, ROW_BYTES)
job_ring_col: DmaJob(DMA_CMD_COPY, row_tpl_col, RING_COL, ROW_BYTES)
job_scr_a:   DmaJob(DMA_CMD_COPY, row_tpl_scr, SCREEN_A, ROW_BYTES)
job_scr_b:   DmaJob(DMA_CMD_COPY, row_tpl_scr, SCREEN_B, ROW_BYTES)
job_col_a:   DmaJob(DMA_CMD_COPY, row_tpl_col, COLRAM + COLOUR_A, ROW_BYTES)
job_col_b:   DmaJob(DMA_CMD_COPY, row_tpl_col, COLRAM + COLOUR_B, ROW_BYTES)

// Template RRB row: 21 background tokens (blank pixie glyph until a map row is
// decoded into it), 63 "null" GOTOX tokens to X=320 and a final transparent blank
// glyph, which therefore always ends the row exactly at the right border (x 336).
// Pixie fragments overwrite the null tokens from the left.
row_tpl_scr:
    .for (var i = 0; i < BG_TOKENS; i++) .word PIXIE_CHAR
    .for (var i = BG_TOKENS; i < ROW_TOKENS - 1; i++) .word $0140
    .word PIXIE_CHAR
row_tpl_col:
    .for (var i = 0; i < BG_TOKENS; i++) .byte $08, $1f
    .for (var i = BG_TOKENS; i < ROW_TOKENS - 1; i++) .byte $90, $00
    .byte $08, $2f
