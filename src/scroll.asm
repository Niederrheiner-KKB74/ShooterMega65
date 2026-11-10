// ----------------------------------------------------------------------------
// Vertical scrolling
//
// The level map comes from the level file (level.asm), glyph row 0 at the start (bottom).
// Decoded rows live in a ring of 32 RRB rows that is stored twice (slot k and
// k+32), so the 26 visible rows are always one contiguous block: each frame
// a single DMA copies them (screen + colour part) into the back buffer, which
// also wipes the previous frame's pixies. Fine scrolling moves TEXTYPOS.
//
//   scroll_px  pixels scrolled since level start
//   display row r shows map row m = (scroll_px >> 3) + 25 - r
//   ring slot of map row m = (31 - m) & 31
// ----------------------------------------------------------------------------

scroll_init:
    lda #0
    sta scroll_px
    sta scroll_px+1
    sta scroll_frac
    sta scroll_delta
    sta tmp+1
    lda #26                     // decode map rows 0..26
    sta tmp
!:  jsr decode_row
    dec tmp
    bpl !-
    rts

// Stage 14: the 27 map rows from (scroll_px >> 3) on into the ring (restart at a checkpoint)
scroll_restore:
    lda #0
    sta scroll_frac
    sta scroll_delta
    lda scroll_px+1
    sta tmp+1
    lda scroll_px
    lsr tmp+1
    ror
    lsr tmp+1
    ror
    lsr tmp+1
    ror
    sta tmp
    lda #27
    sta sr_n
!:  jsr decode_row
    inc tmp
    bne !n+
    inc tmp+1
!n: dec sr_n
    bne !-
    rts
sr_n: .byte 0

scroll_advance:
    lda scroll_px
    sta tmp2
    clc
    lda scroll_frac
    adc scroll_spd
    sta scroll_frac
    lda scroll_px
    adc scroll_spd+1
    sta scroll_px
    lda scroll_px+1
    adc #0
    sta scroll_px+1
    lda scroll_px
    sec
    sbc tmp2
    sta scroll_delta
    lda scroll_px               // crossed an 8 pixel boundary?
    eor tmp2
    and #$f8
    beq !done+
    // decode map row (scroll_px >> 3) + 26 (one row ahead of the top display row)
    lda scroll_px+1
    sta tmp+1
    lda scroll_px
    lsr tmp+1
    ror
    lsr tmp+1
    ror
    lsr tmp+1
    ror
    clc
    adc #26
    sta tmp
    lda tmp+1
    adc #0
    sta tmp+1
    jsr decode_row
!done:
    rts

// Decode map row tmp (16 bit) into ring slots k and k+32 (contents from the level data).
decode_row:
    lda #31
    sec
    sbc tmp
    and #31
    sta dr_slot
    jsr level_row               // -> dr_glyph / dr_col
    jsr land_store              // land mask of this row (tanks avoid water)
    ldx dr_slot
    jsr dr_write
    lda dr_slot
    clc
    adc #RING_SLOTS
    tax
    // fall through
dr_write:
    lda slot_ofs_lo,x
    sta scr_ptr
    sta col_ptr
    lda slot_ofs_hi,x
    clc
    adc #>(RING_SCR & $ffff)
    sta scr_ptr+1
    lda slot_ofs_hi,x
    clc
    adc #>(RING_COL & $ffff)
    sta col_ptr+1
    lda #(RING_SCR >> 16)
    sta scr_ptr+2
    sta col_ptr+2
    lda #0
    sta scr_ptr+3
    sta col_ptr+3
    ldy #0
    ldz #0
!:  lda #$08                    // colour byte 0: NCM
    sta ((col_ptr)),z
    lda dr_glyph,y              // glyph offset within the tile set
    sta ((scr_ptr)),z
    inz
    lda dr_hi,y                 // character high byte (destroyed tiles live elsewhere, ground.asm)
    sta ((scr_ptr)),z
    lda dr_col,y                // colour byte 1: palette bank << 4 | $0f
    sta ((col_ptr)),z
    inz
    iny
    cpy #BG_TOKENS
    bne !-
    rts

dr_slot: .byte 0

// Copy the 26 visible rows into the back buffer and prepare the pixie pass.
scroll_copy_rows:
    lda scroll_px
    and #7
    sta fine
    asl
    clc
    adc #TEXTYPOS_BASE
    sta pend_typos
    lda scroll_px               // ((scroll_px >> 3) & 31)
    lsr
    lsr
    lsr
    sta tmp
    lda #6
    sec
    sbc tmp
    and #31
    sta k0
    tax
    // patch sources
    lda slot_ofs_lo,x
    sta job_frame_scr+DMA_SRC
    sta job_frame_col+DMA_SRC
    lda slot_ofs_hi,x
    clc
    adc #>(RING_SCR & $ffff)
    sta job_frame_scr+DMA_SRC+1
    lda slot_ofs_hi,x
    clc
    adc #>(RING_COL & $ffff)
    sta job_frame_col+DMA_SRC+1
    // patch destinations
    lda back
    bne !b+
    lda #<SCREEN_A
    sta backscr
    lda #>SCREEN_A
    sta backscr+1
    lda #<COLOUR_A
    sta backcol
    lda #>COLOUR_A
    sta backcol+1
    jmp !set+
!b: lda #<SCREEN_B
    sta backscr
    lda #>SCREEN_B
    sta backscr+1
    lda #<COLOUR_B
    sta backcol
    lda #>COLOUR_B
    sta backcol+1
!set:
    lda backscr
    sta job_frame_scr+DMA_DST
    lda backscr+1
    sta job_frame_scr+DMA_DST+1
    lda backcol
    sta job_frame_col+DMA_DST
    lda backcol+1
    sta job_frame_col+DMA_DST+1
    RunDma(job_frame_scr)
    RunDma(job_frame_col)
    // empty overlay in every visible row
    ldx #VIS_ROWS-1
    lda #OVL_START
!:  sta rowfill,x
    dex
    bpl !-
    lda #0
    sta overflow
    rts

job_frame_scr: DmaJob(DMA_CMD_COPY, RING_SCR, SCREEN_A, ROW_BYTES * VIS_ROWS)
job_frame_col: DmaJob(DMA_CMD_COPY, RING_COL, COLRAM + COLOUR_A, ROW_BYTES * VIS_ROWS)

slot_ofs_lo: .fill RING_SLOTS*2, <(i * ROW_BYTES)
slot_ofs_hi: .fill RING_SLOTS*2, >(i * ROW_BYTES)

// ---------------------------------------------------------------- terrain (Stage 7c)
// land_ring: per ring slot 3 bytes, bit c = map column c is land (its palette bank is not the water bank 1;
// coast tiles use the water bank and count as water). Stage 18c: tiles from the level header's +39 on (forest in
// level 1; 0 = none) are not land either - tanks do not drive over the tree tops.
land_store:
    lda dr_slot
    sta ls_i
    asl
    adc ls_i                    // slot * 3 (slot < 32: no carry)
    sta ls_i
    tax
    lda #0
    sta land_ring,x
    sta land_ring+1,x
    sta land_ring+2,x
    ldy #0
!:  lda dr_col,y
    and #$f0
    cmp #$10
    beq !next+
    lda lev_hdr+39              // Stage 18c: forest tiles (glyph >= 2 * first tile)
    beq !land+
    asl
    sta ls_b
    lda dr_glyph,y
    cmp ls_b
    bcs !next+
!land:
    tya
    and #7
    tax
    lda bit_tab,x
    sta ls_b
    tya
    lsr
    lsr
    lsr
    clc
    adc ls_i
    tax
    lda land_ring,x
    ora ls_b
    sta land_ring,x
!next:
    iny
    cpy #BG_TOKENS
    bne !-
    rts
ls_i: .byte 0
ls_b: .byte 0
bit_tab: .byte 1, 2, 4, 8, 16, 32, 64, 128
land_ring: .fill 32 * 3, $ff

// Carry set if the playfield point (ln_x, ln_y; 16 bit) lies on water. Outside the playfield: land.
// Display row r (top at y = 8r - 8 + fine) shows map row m = (scroll_px >> 3) + 25 - r, so the point lies in
// map row m = (scroll_px + 199 - y) >> 3, ring slot (31 - m) & 31; map column (x + 16) >> 4.
// Keeps X.
is_water:
    lda ln_y+1
    bne !land+                  // above the top or far below
    lda ln_y
    cmp #200
    bcs !land+
    lda ln_x+1
    cmp #>320
    bcc !+
    bne !land+
    lda ln_x
    cmp #<320
    bcs !land+
!:  clc                         // m low byte = scroll_px + 199 - y (only bits 3-7 are needed)
    lda scroll_px
    adc #199
    sec
    sbc ln_y
    lsr
    lsr
    lsr
    eor #31                     // (31 - m) & 31
    and #31
    sta ls_i
    asl
    adc ls_i
    sta ls_i                    // slot * 3
    clc                         // column = (x + 16) >> 4  (0..20)
    lda ln_x
    adc #16
    sta ls_b
    lda ln_x+1
    adc #0
    lsr
    ror ls_b
    lsr
    ror ls_b
    lsr
    ror ls_b
    lsr
    ror ls_b                    // ls_b = column
    stx ls_x
    lda ls_b
    lsr
    lsr
    lsr
    clc
    adc ls_i
    tax
    lda ls_b
    and #7
    tay
    lda land_ring,x
    and bit_tab,y
    ldx ls_x
    cmp #1                      // A = 0 (water) -> carry clear ... invert below
    bcs !land+
    sec
    rts
!land:
    clc
    rts
ls_x: .byte 0
ln_x: .word 0
ln_y: .word 0
