// ----------------------------------------------------------------------------
// Vertical scrolling
//
// The level map is a list of 21-glyph rows, row 0 at the start (bottom).
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

scroll_advance:
    lda scroll_px
    sta tmp2
    clc
    lda scroll_frac
    adc #<SCROLL_SPEED
    sta scroll_frac
    lda scroll_px
    adc #>SCROLL_SPEED
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

// Decode map row tmp (16 bit) into ring slots k and k+32.
decode_row:
    lda #31
    sec
    sbc tmp
    and #31
    sta dr_slot
    // source offset = (m & 511) * 21 = m*16 + m*4 + m
    lda tmp
    and #<(MAP_ROWS-1)
    sta tmp2
    lda tmp+1
    and #>(MAP_ROWS-1)
    sta tmp2+1
    lda tmp2
    sta dr_acc
    lda tmp2+1
    sta dr_acc+1
    asl tmp2                    // *4
    rol tmp2+1
    asl tmp2
    rol tmp2+1
    clc
    lda dr_acc
    adc tmp2
    sta dr_acc
    lda dr_acc+1
    adc tmp2+1
    sta dr_acc+1
    asl tmp2                    // *16
    rol tmp2+1
    asl tmp2
    rol tmp2+1
    clc
    lda dr_acc
    adc tmp2
    sta dr_acc
    lda dr_acc+1
    adc tmp2+1
    sta dr_acc+1
    clc
    lda dr_acc
    adc #<map_data
    sta dr_src
    lda dr_acc+1
    adc #>map_data
    sta dr_src+1
    clc
    lda dr_acc
    adc #<mapcol_data
    sta dr_csrc
    lda dr_acc+1
    adc #>mapcol_data
    sta dr_csrc+1

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
    lda dr_src
    sta dr_rd+1
    lda dr_src+1
    sta dr_rd+2
    lda dr_csrc
    sta dr_crd+1
    lda dr_csrc+1
    sta dr_crd+2
    ldy #0
    ldz #0
!:  lda #$08                    // colour byte 0: NCM
    sta ((col_ptr)),z
dr_rd:
    lda $ffff,y                 // glyph offset within the tile set
    sta ((scr_ptr)),z
    inz
    lda #>TILE_CHAR
    sta ((scr_ptr)),z
dr_crd:
    lda $ffff,y                 // colour byte 1: palette bank << 4 | $0f
    sta ((col_ptr)),z
    inz
    iny
    cpy #BG_TOKENS
    bne !-
    rts

dr_slot: .byte 0
dr_acc:  .word 0
dr_src:  .word 0
dr_csrc: .word 0

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
