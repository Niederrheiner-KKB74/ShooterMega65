// ----------------------------------------------------------------------------
// Several levels (Stage 9)
//
// With attic RAM all level files are loaded at start into one 64 KB pack per level and copied into place by
// DMA when the level begins (level_enter). Pack n (level n+1) at ATTIC_LEVELS + n * $10000:
//   +$0000 LnGFX (<= 16 KB)   +$4000 LnDAT (<= 10 KB)   +$7000 LnDEST (<= 6 KB)   +$9000 level music piece
// The boss of level n+1 (LnBOSS) is at $8020000 + n * $40000 (level 1 $8020000, level 2 $8060000).
// Without attic RAM only level 1 exists: it is loaded straight into place as before and repeats.
// At the end of a level (event `end`) the next level starts with the next map; score, lives, credits and
// everything bought are kept. After the last level comes level 1 again.
// ----------------------------------------------------------------------------
.const ATTIC_LEVELS = $8040000
.const LEVELS       = 2
.const LV_GFX  = $0000
.const LV_DAT  = $4000
.const LV_DEST = $7000
.const LV_MUS  = $9000

.errorif (LEVEL_DAT_MAX > LV_DEST - LV_DAT), "LnDAT overlaps LnDEST in the attic pack"
.errorif (MUS_SLOT_MAX > $10000 - LV_MUS), "level music overlaps the next attic pack"
.errorif (ATTIC_LEVELS + LEVELS * $10000 > $8060000), "level packs overlap the level-2 boss"

cur_level:      .byte 0
level_next_req: .byte 0
mus_hdr_lo:     .byte <MUS_HDR1, <MUS_HDR2
mus_hdr_hi:     .byte >MUS_HDR1, >MUS_HDR2

// ============================================================== loading (KERNAL, at start)
// all levels into attic RAM (attic_ok must be set). Carry set = failed (message printed).
levels_load:
    lda #0
    sta lv_n
!lv:
    lda lv_n                    // file names L<n+1>GFX, L<n+1>DAT, L<n+1>DEST, L<n+1>BOSS
    clc
    adc #'1'
    sta name_gfx+1
    sta name_dat+1
    sta name_dest+1
    sta name_boss+1
    lda lv_n
    clc
    adc #((ATTIC_LEVELS >> 16) & $0f)
    sta lv_bank
    lda #<LV_GFX
    ldx #>LV_GFX
    ldy #(>$4000) + 1
    jsr lv_dst
    lda #<name_gfx
    ldx #>name_gfx
    ldy #name_gfx_end - name_gfx
    jsr load_seq_to
    bcs !fail+
    lda #<LV_DAT
    ldx #>LV_DAT
    ldy #(>LEVEL_DAT_MAX) + 1
    jsr lv_dst
    lda #<name_dat
    ldx #>name_dat
    ldy #name_dat_end - name_dat
    jsr load_seq_to
    bcs !fail+
    lda #<LV_DEST
    ldx #>LV_DEST
    ldy #(>(48 * 128)) + 1
    jsr lv_dst
    lda #<name_dest
    ldx #>name_dest
    ldy #name_dest_end - name_dest
    jsr load_seq_to
    bcs !fail+
    lda lv_n                    // boss: bank 2 + 4n of the attic RAM
    asl
    asl
    clc
    adc #((ATTIC_BOSS >> 16) & $0f)
    sta bl_bank
    jsr boss_load
    bcs !fail+
    inc lv_n
    lda lv_n
    cmp #LEVELS
    bne !lv-
    // music: the level-1 piece is in MUSIC already (copied to pack 0), the others are files MUS2 ...
    RunDma(job_mus1_save)
    lda #((ATTIC_LEVELS >> 16) & $0f) + 1
    sta lv_bank
    lda #<LV_MUS
    ldx #>LV_MUS
    ldy #(>MUS_SLOT_MAX) + 1
    jsr lv_dst
    lda #<name_mus2
    ldx #>name_mus2
    ldy #name_mus2_end - name_mus2
    jsr load_seq_to
    bcs !fail+
    lda #'1'                    // names back for messages
    sta name_gfx+1
    sta name_dat+1
    clc
!fail:
    rts
lv_n:    .byte 0
lv_bank: .byte 0
name_mus2: .text "MUS2"
name_mus2_end:
job_mus1_save: DmaJob(DMA_CMD_COPY, MUS_SLOT, ATTIC_LEVELS + LV_MUS, MUS1_BYTES)

// load destination: attic RAM, bank lv_bank, offset A/X; Y = size limit (high byte + 1)
lv_dst:
    sta ld_dst
    stx ld_dst+1
    sty ld_maxhi
    lda lv_bank
    sta ld_dst+2
    lda #(ATTIC_LEVELS >> 20)
    sta ld_dst+3
    rts

// ============================================================== runtime
// level A (0 = level 1) from its attic pack into place: landscape glyphs and palettes, destroyed tiles,
// level data, level music, boss glyph source, palette and part positions
level_enter:
    sta cur_level
    clc
    adc #((ATTIC_LEVELS >> 16) & $0f)
    sta job_a_hdr+DMA_SRC+2
    sta job_a_glyphs+DMA_SRC+2
    sta job_a_dest1+DMA_SRC+2
    sta job_a_dest2+DMA_SRC+2
    sta job_a_dat+DMA_SRC+2
    sta job_a_mus+DMA_SRC+2
    RunDma(job_a_hdr)           // 'SG', glyph count, palettes -> bank 0
    lda lev_gfxhdr+2            // glyph count * 64
    sta job_a_glyphs+DMA_COUNT+1
    lda #0
    sta job_a_glyphs+DMA_COUNT
    lsr job_a_glyphs+DMA_COUNT+1
    ror job_a_glyphs+DMA_COUNT
    lsr job_a_glyphs+DMA_COUNT+1
    ror job_a_glyphs+DMA_COUNT
    RunDma(job_a_glyphs)
    RunDma(job_a_dest1)
    RunDma(job_a_dest2)
    RunDma(job_a_dat)
    RunDma(job_dathdr)          // header of LnDAT -> lev_hdr
    jsr level_init              // metatiles, ground-target tables, events from the start
    RunDma(job_a_mus)           // level music into the slot, header table entry 0 -> its piece
    ldx cur_level
    lda mus_hdr_lo,x
    sta MUSIC_ADDR + 4
    lda mus_hdr_hi,x
    sta MUSIC_ADDR + 5
    txa                         // boss of this level: attic bank 2 + 4n
    asl
    asl
    clc
    adc #((ATTIC_BOSS >> 16) & $0f)
    sta job_boss_in+DMA_SRC+2
    sta job_boss_pal+DMA_SRC+2
    RunDma(job_boss_pal)
    ldx cur_level               // part positions (part_dx, part_dy, rotor_dx, rotor_dy, rotor_ph: 22 bytes per view)
    ldy #0
    lda le_place_lo,x
    sta le_src+1
    lda le_place_hi,x
    sta le_src+2
!:
le_src:
    lda $ffff,y
    sta boss_place_cur,y
    iny
    cpy #44
    bne !-
    lda #0
    jsr boss_orient
    jmp palette_init            // landscape banks 1-4 (and the boss bank back to normal)
le_place_lo: .byte <boss_place1, <boss_place2
le_place_hi: .byte >boss_place1, >boss_place2

job_a_hdr:    DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_GFX, lev_gfxhdr, 4 + 192)
job_a_glyphs: DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_GFX + 4 + 192, TILE_ADDR, 0)
job_a_dest1:  DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_DEST, DEST1_ADDR, 32 * 128)
job_a_dest2:  DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_DEST + 32 * 128, DEST2_ADDR, 16 * 128)
job_a_dat:    DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_DAT, LEVEL_BUF, LEVEL_DAT_MAX)
job_a_mus:    DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_MUS, MUS_SLOT, MUS_SLOT_MAX)

// end of a level (main loop, after the event `end`): the next level, the player keeps everything
level_next:
    lda #0
    sta level_next_req
    lda cur_level
    clc
    adc #1
    cmp #LEVELS
    bcc !+
    lda #0
!:  jsr level_enter
    jsr buffers_init
    jsr scroll_init
    jsr objects_init
    lda #0
    sta boss_state
    sta boss_req
    lda #INV_FRAMES             // a moment to get oriented
    sta pl_inv
    jmp build_frame
