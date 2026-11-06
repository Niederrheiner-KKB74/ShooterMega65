// ----------------------------------------------------------------------------
// Title screen, game over, high score, new game (Stage 7). Artwork PR #14, data
// from tools/make_screens.py (files TITLE and GOVER, build/gen/screens_*.inc).
//
// Memory: the title (26 KB) is shown from TITLE_ADDR ($56000: screen buffer B and
// ring, unused while the title is up); the banner from GOVER_ADDR ($58000: ring,
// unused while the game is paused). Both are kept in attic RAM ($8000000) and
// copied in when needed. Without attic RAM the title is loaded straight to
// TITLE_ADDR and can only be shown once; game over is then a small message box.
//
// Flow: start -> title_run -> game_new -> main loop -> last plane lost ->
//       game_over_run -> title_run -> game_new -> …
// ----------------------------------------------------------------------------
.const TITLE_ADDR  = $056000
.const TITLE_CHAR  = TITLE_ADDR / 64
.const GOVER_ADDR  = $058000
.const GOVER_CHAR  = GOVER_ADDR / 64
.const ATTIC_TITLE = $8000000
.const ATTIC_GOVER = $8010000
.const PAL_TITLE   = (1 << 4) | $0f      // title palette in bank 1 (landscape: not on screen then)
.const PAL_GOVER   = (13 << 4) | $0f     // banner palette in bank 13 (no objects then)
.const GOVER_ROW0  = 9
.const GOVER_COL0  = 3
.label bw_sp = $7a                       // 32-bit source pointer

.errorif (TITLE_ADDR + TITLE_BYTES > $05e000), "title data too large"
.errorif (GOVER_ADDR + GOVER_BYTES > RING_COL), "banner data too large"
.errorif (TITLE_ADDR < SCREEN_A + ROW_BYTES * BUF_ROWS), "title data overlaps screen buffer A"

attic_ok:   .byte 0          // 1 = attic RAM found at start
title_seen: .byte 0
game_over_req: .byte 0
hiscore_bcd: .fill 3, 0      // most significant first

// ============================================================== loading (KERNAL)
// attic RAM present? Two patterns written by DMA and read back by the CPU.
attic_detect:
    lda #0
    sta attic_ok
#if NO_ATTIC
    rts                         // test build (build.py --define NO_ATTIC): behave as without attic RAM
#endif
    lda #<ATTIC_TITLE
    sta tmp
    lda #>ATTIC_TITLE
    sta tmp+1
    lda #<(ATTIC_TITLE >> 16)
    sta tmp2
    lda #>(ATTIC_TITLE >> 16)
    sta tmp2+1
    RunDma(job_attic_a5)
    ldz #0
    lda ((tmp)),z
    cmp #$a5
    bne !no+
    RunDma(job_attic_5a)
    lda ((tmp)),z
    cmp #$5a
    bne !no+
    lda #1
    sta attic_ok
!no:
    rts

// TITLE and GOVER: into attic RAM, or (without it) TITLE straight to TITLE_ADDR
screens_load:
    jsr attic_detect
    lda attic_ok
    beq !direct+
    lda #<(ATTIC_TITLE & $ffff)
    sta ld_dst
    lda #>(ATTIC_TITLE & $ffff)
    sta ld_dst+1
    lda #((ATTIC_TITLE >> 16) & $0f)
    sta ld_dst+2
    lda #(ATTIC_TITLE >> 20)
    sta ld_dst+3
    jsr !title+
    bcs !done+
    lda #<(ATTIC_GOVER & $ffff)
    sta ld_dst
    lda #>(ATTIC_GOVER & $ffff)
    sta ld_dst+1
    lda #((ATTIC_GOVER >> 16) & $0f)
    sta ld_dst+2
    lda #(ATTIC_GOVER >> 20)
    sta ld_dst+3
    lda #(>GOVER_BYTES) + 1
    sta ld_maxhi
    lda #<name_gover
    ldx #>name_gover
    ldy #name_gover_end - name_gover
    jsr load_seq_to
!done:
    lda #0                      // later loads go to chip RAM again
    sta ld_dst+3
    rts
!direct:
    lda #<(TITLE_ADDR & $ffff)
    sta ld_dst
    lda #>(TITLE_ADDR & $ffff)
    sta ld_dst+1
    lda #(TITLE_ADDR >> 16)
    sta ld_dst+2
    lda #0
    sta ld_dst+3
!title:
    lda #(>TITLE_BYTES) + 1         // limit: high byte of the size + 1
    sta ld_maxhi
    lda #<name_title
    ldx #>name_title
    ldy #name_title_end - name_title
    jmp load_seq_to

// ============================================================== title
title_run:
    lda attic_ok
    bne !load+
    lda title_seen
    beq !show+
    rts                         // no attic RAM: the title data were overwritten by the first game
!load:
    RunDma(job_title_in)
!show:
    lda #1
    sta title_seen
    lda #0
    sta VIC_SPREN
    jsr buffer_a_init
    lda #TEXTYPOS_BASE          // no fine scroll: rows 1-25 are the 200 visible lines
    sta VIC_TEXTYPOS
    jsr show_buffer_a
    // palette of the title -> bank 1, background and border = its colour 0
    lda #<((TITLE_ADDR + TITLE_PAL) & $ffff)
    ldx #>((TITLE_ADDR + TITLE_PAL) & $ffff)
    ldy #$10
    jsr load_palette16
    lda #$10
    sta VIC_BGCOL
    sta VIC_BORDER
    // high score digits, then all 25 rows
    lda #<hiscore_bcd
    ldx #>hiscore_bcd
    ldy #0
    jsr render_digits
    lda #0
    sta tt_row
!:  jsr title_row
    inc tt_row
    lda tt_row
    cmp #25
    bne !-
    lda #MUS_TITLE
    jsr music_play
    jsr fire_reset
    lda #0
    sta key_2
#if START_LEVEL2
    lda #1                      // test build (build.py --define START_LEVEL2): level 2 first
#endif
#if START_LEVEL3
    lda #2                      // test build: level 3 first
#endif
    sta start_level
!loop:
    jsr shop_frame              // vertical blank, sound, keys, debounced joystick
    lda key_2                   // key 2 / 3: start in level 2 / 3 (with attic RAM)
    beq !+
    lda attic_ok
    beq !+
    lda key_2
    sta start_level
    bne !go+
!:
    inc tt_blink
    lda tt_blink
    and #31                     // "PRESS FIRE" blinks
    bne !+
    lda tt_blink
    and #32
    lsr
    lsr
    lsr
    lsr
    lsr
    sta tt_alt
    lda #22
    sta tt_row
    jsr title_row
    lda #0
    sta tt_alt
!:  lda sh_press
    and #$10
    beq !loop-
!go:
    lda #SFX_SELECT
    jsr sfx_play
    lda #0
    sta VIC_BGCOL
    sta VIC_BORDER
    jmp palette_init
start_level: .byte 0           // level of the next game (0 = level 1; key 2 on the title: 1)
tt_row:   .byte 0
tt_blink: .byte 0
tt_alt:   .byte 0                // 1 = row 22 without "PRESS FIRE"

// title row tt_row -> screen A row tt_row + 1, background tokens 1-20
title_row:
    lda tt_row
    sta tmp                     // source = map + row * 40 (or the alternative row 22)
    lda #0
    sta tmp+1
    ldx #40
    jsr mul_tmp
    clc
    lda tmp
    adc #<((TITLE_ADDR + TITLE_MAP) & $ffff)
    sta bw_sp
    lda tmp+1
    adc #>((TITLE_ADDR + TITLE_MAP) & $ffff)
    sta bw_sp+1
    lda tt_alt
    beq !+
    lda #<((TITLE_ADDR + TITLE_ALT22) & $ffff)
    sta bw_sp
    lda #>((TITLE_ADDR + TITLE_ALT22) & $ffff)
    sta bw_sp+1
!:  lda #(TITLE_ADDR >> 16)
    sta bw_sp+2
    lda #0
    sta bw_sp+3
    lda #1
    sta bw_rows
    lda #20
    sta bw_cols
    ldx tt_row
    inx
    stx bw_row0
    lda #2                      // token 1 (token 0 is the hidden column)
    sta bw_col2
    lda #<TITLE_CHAR
    sta bw_chr
    lda #>TITLE_CHAR
    sta bw_chr+1
    lda #PAL_TITLE
    sta bw_pal
    lda #1                      // screen A only
    sta bw_bufs
    jmp blit_words

// ============================================================== game over
game_over_run:
    lda #0
    sta game_over_req
    lda #$ff                    // no level music after the jingle
    jsr music_queue
    jsr hiscore_update
    jsr boss_reset              // died during the boss: glyphs and palette back
    jsr objects_init
    jsr build_frame             // both buffers without objects (as in the shop)
    jsr wait_vblank
    jsr flip
    jsr build_frame
    jsr wait_vblank
    jsr flip
    lda #0
    sta VIC_SPREN
    lda attic_ok
    beq !box+
    RunDma(job_gover_in)
    lda #<((GOVER_ADDR + GOVER_PAL) & $ffff)
    ldx #>((GOVER_ADDR + GOVER_PAL) & $ffff)
    ldy #$d0
    jsr load_palette16
    lda #<score_bcd
    ldx #>score_bcd
    ldy #1
    jsr render_digits
    lda #<((GOVER_ADDR + GOVER_MAP) & $ffff)
    sta bw_sp
    lda #>((GOVER_ADDR + GOVER_MAP) & $ffff)
    sta bw_sp+1
    lda #(GOVER_ADDR >> 16)
    sta bw_sp+2
    lda #0
    sta bw_sp+3
    lda #8
    sta bw_rows
    lda #16
    sta bw_cols
    lda #GOVER_ROW0
    sta bw_row0
    lda #GOVER_COL0 * 2
    sta bw_col2
    lda #<GOVER_CHAR
    sta bw_chr
    lda #>GOVER_CHAR
    sta bw_chr+1
    lda #PAL_GOVER
    sta bw_pal
    lda #3                      // both buffers
    sta bw_bufs
    jsr blit_words
    jmp !wait+
!box:
    jsr shop_palettes           // fallback: "GAME OVER" box in the shop style
    lda #<shop_gover_glyph
    ldx #>shop_gover_glyph
    ldy #0
    jsr blit_msg
!wait:
    jsr fire_reset
    lda #0
    sta go_t
!:  jsr shop_frame
    inc go_t
    beq !done+                  // about 5 s: continue anyway
    lda go_t
    cmp #50                     // at least 1 s before fire counts
    bcc !-
    lda sh_press
    and #$10
    beq !-
!done:
    jmp palette_init
go_t: .byte 0

// fire must be released first (shop_frame debounce)
fire_reset:
    jsr read_joystick
    lda joy
    sta sh_prev
    lda #0
    sta sh_rel
    sta sh_press
    rts

hiscore_update:
    ldx #0
!:  lda score_bcd,x
    cmp hiscore_bcd,x
    bcc !no+
    bne !new+
    inx
    cpx #3
    bne !-
!no:
    rts
!new:
    ldx #2
!:  lda score_bcd,x
    sta hiscore_bcd,x
    dex
    bpl !-
    rts

// ============================================================== new game
game_new:
    lda #0                      // no checkpoint yet (Stage 14)
    sta cp_valid
    sta level_retry_req
    lda attic_ok                // Stage 9: the level chosen on the title (key 2: level 2) from attic RAM
    beq !+
    lda start_level
    jsr level_enter
!:  jsr buffers_init            // the title used screen B and the ring
    jsr scroll_init
    jsr level_restart
    jsr objects_init
    lda #0
    sta boss_state
    sta boss_req
    sta game_over_req
    jsr shop_reset
    jsr hud_reset
    jsr player_init
    lda #MUS_LEVEL1
    jsr music_play
    lda #1                      // build into B (A still shows the title), the main loop shows it
    sta back
    jmp build_frame

// ============================================================== helpers
// palette 0 entries Y..Y+15 <- 48 bytes (R, G, B planes, 16 each) at A/X (low 16 bits, bank 5)
load_palette16:
    sta bw_sp
    stx bw_sp+1
    sty lp_y
    lda #5
    sta bw_sp+2
    lda #0
    sta bw_sp+3
    ldz #0
    ldx #16
!:  lda ((bw_sp)),z
    sta PAL_RED,y
    iny
    inz
    dex
    bne !-
    ldy lp_y
    ldx #16
!:  lda ((bw_sp)),z
    sta PAL_GREEN,y
    iny
    inz
    dex
    bne !-
    ldy lp_y
    ldx #16
!:  lda ((bw_sp)),z
    sta PAL_BLUE,y
    iny
    inz
    dex
    bne !-
    ldz #0
    rts
lp_y: .byte 0

// six BCD digits at A/X (bank 0) -> three glyphs: Y = 0 title (TITLE_DIGIT), 1 banner (GOVER_DIGIT)
render_digits:
    sta rd_bcd+1
    stx rd_bcd+2
    lda rd_dlo,y
    sta bw_sp
    lda rd_dhi,y
    sta bw_sp+1
    lda #5
    sta bw_sp+2
    lda #0
    sta bw_sp+3
    lda rd_clo,y
    sta rd_cells
    lda rd_chi,y
    sta rd_cells+1
    lda #0
    sta rd_d
!digit:
    lda rd_d                    // value of digit d (even: high nibble)
    lsr
    tay
rd_bcd:
    lda $ffff,y
    bcs !+
    lsr
    lsr
    lsr
    lsr
!:  and #$0f
    tay                         // cell = cells + value * 32
    clc
    lda rd_cells
    adc rd_off_lo,y
    sta rd_src+1
    lda rd_cells+1
    adc rd_off_hi,y
    sta rd_src+2
    lda rd_d                    // destination: glyph (d / 2) * 64 + (d & 1) * 4
    and #1
    asl
    asl
    sta rd_z
    lda rd_d
    lsr
    asl
    asl
    asl
    asl
    asl
    asl
    clc
    adc rd_z
    sta rd_z
    ldx #0
!row:
    ldy #4
    ldz rd_z
!:
rd_src:
    lda $ffff,x
    sta ((bw_sp)),z
    inx
    inz
    dey
    bne !-
    lda rd_z
    clc
    adc #8
    sta rd_z
    cpx #32
    bne !row-
    inc rd_d
    lda rd_d
    cmp #6
    bne !digit-
    ldz #0
    rts
rd_off_lo: .fill 10, <(i * 32)
rd_off_hi: .fill 10, >(i * 32)
rd_d:     .byte 0
rd_z:     .byte 0
rd_cells: .word 0
rd_dlo:   .byte <((TITLE_ADDR + TITLE_DIGIT * 64) & $ffff), <((GOVER_ADDR + GOVER_DIGIT * 64) & $ffff)
rd_dhi:   .byte >((TITLE_ADDR + TITLE_DIGIT * 64) & $ffff), >((GOVER_ADDR + GOVER_DIGIT * 64) & $ffff)
rd_clo:   .byte <title_digits, <gover_digits
rd_chi:   .byte >title_digits, >gover_digits
.errorif ((TITLE_ADDR >> 16) != 5 || (GOVER_ADDR >> 16) != 5), "screens must be in bank 5"

// rows x cols words at bw_sp (character offsets) -> background tokens, screen row bw_row0, byte bw_col2;
// character = bw_chr + word, colour bytes $08 / bw_pal; bw_bufs: bit 0 buffer A, bit 1 buffer B
blit_words:
    lda #0
    sta bw_b
!buf:
    lda bw_bufs
    ldx bw_b
    and v_bit,x                 // 1, 2
    bne !+
    jmp !nextbuf+
!:  lda bw_sp                   // restart the source for each buffer
    sta bw_s0
    lda bw_sp+1
    sta bw_s0+1
    ldx bw_row0
    lda bw_rows
    sta bw_r
!row:
    clc
    lda row_ofs_lo,x
    adc bw_col2
    sta scr_ptr
    sta col_ptr
    lda row_ofs_hi,x
    adc #0
    pha
    ldy bw_b
    clc
    adc buf_scr_hi,y
    sta scr_ptr+1
    pla
    clc
    adc buf_col_hi,y
    sta col_ptr+1
    lda #(SCREEN_A >> 16)
    sta scr_ptr+2
    lda #<(COLRAM >> 16)
    sta col_ptr+2
    lda #0
    sta scr_ptr+3
    lda #>(COLRAM >> 16)
    sta col_ptr+3
    ldy bw_cols
    ldz #0
!tok:
    lda ((bw_sp)),z             // source word at the same offset as the destination token
    clc
    adc bw_chr
    sta bw_w
    inz
    lda ((bw_sp)),z
    adc bw_chr+1
    sta bw_w+1
    dez
    lda bw_w
    sta ((scr_ptr)),z
    lda #$08
    sta ((col_ptr)),z
    inz
    lda bw_w+1
    sta ((scr_ptr)),z
    lda bw_pal
    sta ((col_ptr)),z
    inz
    dey
    bne !tok-
    lda bw_cols                 // next source row
    asl
    clc
    adc bw_sp
    sta bw_sp
    bcc !+
    inc bw_sp+1
!:  inx
    dec bw_r
    bne !row-
    lda bw_s0
    sta bw_sp
    lda bw_s0+1
    sta bw_sp+1
!nextbuf:
    inc bw_b
    lda bw_b
    cmp #2
    beq !+
    jmp !buf-
!:  ldz #0
    rts
bw_rows: .byte 0
bw_cols: .byte 0
bw_row0: .byte 0
bw_col2: .byte 0
bw_chr:  .word 0
bw_pal:  .byte 0
bw_bufs: .byte 0
bw_b:    .byte 0
bw_r:    .byte 0
bw_w:    .word 0
bw_s0:   .word 0

// tmp (16 bit) * X -> tmp
mul_tmp:
    lda tmp
    sta mt_a
    lda tmp+1
    sta mt_a+1
    lda #0
    sta tmp
    sta tmp+1
    cpx #0
    beq !done+
!:  clc
    lda tmp
    adc mt_a
    sta tmp
    lda tmp+1
    adc mt_a+1
    sta tmp+1
    dex
    bne !-
!done:
    rts
mt_a: .word 0

name_title: .text "TITLE"
name_title_end:
name_gover: .text "GOVER"
name_gover_end:
job_title_in: DmaJob(DMA_CMD_COPY, ATTIC_TITLE, TITLE_ADDR, TITLE_BYTES)
job_gover_in: DmaJob(DMA_CMD_COPY, ATTIC_GOVER, GOVER_ADDR, GOVER_BYTES)
job_attic_a5: DmaJob(DMA_CMD_FILL, $a5, ATTIC_TITLE, 16)
job_attic_5a: DmaJob(DMA_CMD_FILL, $5a, ATTIC_TITLE, 16)

#import "../build/gen/screens_data.inc"
