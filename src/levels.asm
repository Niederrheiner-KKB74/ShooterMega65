// ----------------------------------------------------------------------------
// Several levels (Stage 9; three since Stage 13)
//
// With attic RAM all level files are loaded at start into one 64 KB pack per level and copied into place by
// DMA when the level begins (level_enter). Each level has a 64 KB pack (bank lv_pack_bank of the attic RAM):
//   +$0000 LnGFX (<= 16 KB)   +$4000 LnDAT (<= 10 KB)   +$7000 LnDEST (<= 6 KB)   +$9000 level music piece
// and its boss LnBOSS in bank lv_boss_bank. Attic banks ($80n0000): 0 TITLE, 1 GOVER, 2 L1BOSS, 3 PXSAVE,
// 4 pack 1, 5 pack 2, 6 L2BOSS, 7 pack 3, 8 L3BOSS (docs/memory_map.md).
// Without attic RAM only level 1 exists: it is loaded straight into place as before and repeats.
// At the end of a level (event `end`) the next level starts with the next map; score, lives, credits and
// everything bought are kept. After the last level comes level 1 again.
// ----------------------------------------------------------------------------
.const ATTIC_LEVELS = $8040000
.const LEVELS       = 4
.const LV_GFX  = $0000
.const LV_DAT  = $4000
.const LV_DEST = $7000
.const LV_MUS  = $9000

.errorif (LEVEL_DAT_MAX > LV_DEST - LV_DAT), "LnDAT overlaps LnDEST in the attic pack"
.errorif (MUS_SLOT_MAX > $10000 - LV_MUS), "level music overlaps the next attic pack"
lv_pack_bank: .byte $04, $05, $07, $0a  // attic bank of each level's pack and boss (Stage 13: tables)
lv_boss_bank: .byte $02, $06, $08, $0b
lv_set_bank:  .byte $03, $03, $09, $0c
lv_sea:       .byte 0, 0, 1, 1          // tanks keep to bank-1 tiles: level 3 speedboats (water), level 4 mechs (streets)
lv_tankmask:  .byte 1, 1, 0, 1          // tanks move every 2nd frame, speedboats every frame
lv_kind_ofs:  .byte 0, 0, 5, 10         // per level: kind_hp / kind_fire of fighter, bomber, heli, armoured, tank
lv_kind_hp:   .byte 1, 6, 2, 10, 3,   2, 6, 3, 10, 3,   2, 6, 3, 30, 4   // L3 seaplane 2, heli 3; L4 jet 2, heavy drone 6
lv_kind_fire: .byte 3, 5, 3, 6, 2,    5, 8, 6, 10, 4,   6, 6, 7, 10, 5       // enemy set (Stage 13): ENEM0 for levels 1 and 2, ENEM3
.errorif (lv_boss_bank - lv_pack_bank != LEVELS), "one pack and one boss bank per level"

cur_level:      .byte 0
level_next_req: .byte 0
mus_hdr_lo:     .byte <MUS_HDR1, <MUS_HDR2, <MUS_HDR3, <MUS_HDR4
mus_hdr_hi:     .byte >MUS_HDR1, >MUS_HDR2, >MUS_HDR3, >MUS_HDR4

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
    ldx lv_n
    lda lv_pack_bank,x
    sta lv_bank
    lda #<LV_GFX
    ldx #>LV_GFX
    ldy #(>$4000) + 1
    jsr lv_dst
    lda #<name_gfx
    ldx #>name_gfx
    ldy #name_gfx_end - name_gfx
    jsr load_seq_to
    bcc !+
    jmp lv_fail
!:
    lda #<LV_DAT
    ldx #>LV_DAT
    ldy #(>LEVEL_DAT_MAX) + 1
    jsr lv_dst
    lda #<name_dat
    ldx #>name_dat
    ldy #name_dat_end - name_dat
    jsr load_seq_to
    bcc !+
    jmp lv_fail
!:
    lda #<LV_DEST
    ldx #>LV_DEST
    ldy #(>(48 * 128)) + 1
    jsr lv_dst
    lda #<name_dest
    ldx #>name_dest
    ldy #name_dest_end - name_dest
    jsr load_seq_to
    bcc !+
    jmp lv_fail
!:
    ldx lv_n                    // boss: its own bank of the attic RAM
    lda lv_boss_bank,x
    sta bl_bank
    jsr boss_load
    bcc !+
    jmp lv_fail
!:
    inc lv_n
    lda lv_n
    cmp #LEVELS
    bne !lv-
    // music: the level-1 piece is in MUSIC already (copied to pack 1), the others are files MUS2, MUS3
    RunDma(job_mus1_save)
    ldx #1
!mu:
    stx lv_n
    lda lv_pack_bank,x
    sta lv_bank
    txa
    clc
    adc #'1'
    sta name_mus2+3
    lda #<LV_MUS
    ldx #>LV_MUS
    ldy #(>MUS_SLOT_MAX) + 1
    jsr lv_dst
    lda #<name_mus2
    ldx #>name_mus2
    ldy #name_mus2_end - name_mus2
    jsr load_seq_to
    bcc !+
    jmp lv_fail
!:
    ldx lv_n
    inx
    cpx #LEVELS
    bne !mu-
    lda #'0'                    // enemy sets (Stage 13): ENEM0 -> bank 3, ENEM3 -> bank 9
    ldx #$03
    jsr lv_set_load
    bcc !+
    jmp lv_fail
!:  lda #'3'
    ldx #$09
    jsr lv_set_load
    bcc !+
    jmp lv_fail
!:  lda #'4'                    // Stage 14: ENEM4 -> bank 12
    ldx #$0c
    jsr lv_set_load
    bcc !+
    jmp lv_fail
!:
    lda #'1'                    // names back for messages
    sta name_gfx+1
    sta name_dat+1
    clc
lv_fail:
    rts
lv_n:    .byte 0
lv_bank: .byte 0
name_mus2: .text "MUS2"
name_mus2_end:
job_mus1_save: DmaJob(DMA_CMD_COPY, MUS_SLOT, ATTIC_LEVELS + LV_MUS, MUS1_BYTES)

// enemy set file ENEM<A> into attic bank X
lv_set_load:
    sta name_enem+4
    stx lv_bank
    lda #0
    tax
    ldy #(>SET_BYTES) + 1
    jsr lv_dst
    lda #<name_enem
    ldx #>name_enem
    ldy #5
    jmp load_seq_to
name_enem: .text "ENEM0"

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
    tax
    lda lv_pack_bank,x
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
    ldx cur_level
    jsr anim_init               // tile animations of the level (Stage 13)
    RunDma(job_a_mus)           // level music into the slot, header table entry 0 -> its piece
    ldx cur_level
    lda mus_hdr_lo,x
    sta MUSIC_ADDR + 4
    lda mus_hdr_hi,x
    sta MUSIC_ADDR + 5
    lda lv_boss_bank,x          // boss of this level
    sta job_boss_in+DMA_SRC+2
    sta job_boss_pal+DMA_SRC+2
    RunDma(job_boss_pal)
    ldx cur_level               // part positions (22 bytes) and effects/sizes (BOSS_FX_LEN bytes) of this boss
    ldy #0
    lda le_place_lo,x
    sta le_src+1
    lda le_place_hi,x
    sta le_src+2
!:
le_src:
    lda $ffff,y
    sta part_dx,y
    iny
    cpy #22
    bne !-
    lda le_fx_lo,x
    sta le_fx+1
    lda le_fx_hi,x
    sta le_fx+2
    ldy #BOSS_FX_LEN - 1
!:
le_fx:
    lda $ffff,y
    sta boss_fx_cur,y
    dey
    bpl !-
    ldx cur_level               // the level's enemy set (Stage 13)
    lda lv_sea,x                // level 3: tanks are speedboats (water only, fast)
    sta tank_boat
    lda lv_tankmask,x
    sta mvmask+K_TANK
    ldy lv_kind_ofs,x           // hit points and firing chances of the enemy kinds (Stage 13b)
    ldx #0
!:  lda lv_kind_hp,y
    sta kind_hp,x
    lda lv_kind_fire,y
    sta kind_fire,x
    iny
    inx
    cpx #5
    bne !-
    ldx cur_level
    jsr set_in
    jmp palette_init            // landscape banks 1-4 (and the boss bank back to normal)
le_fx_lo:    .byte <boss_fx1, <boss_fx2, <boss_fx3, <boss_fx4
le_fx_hi:    .byte >boss_fx1, >boss_fx2, >boss_fx3, >boss_fx4
le_place_lo: .byte <boss_place1, <boss_place2, <boss_place3, <boss_place4
le_place_hi: .byte >boss_place1, >boss_place2, >boss_place3, >boss_place4

job_a_hdr:    DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_GFX, lev_gfxhdr, 4 + 192)
job_a_glyphs: DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_GFX + 4 + 192, TILE_ADDR, 0)
job_a_dest1:  DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_DEST, DEST1_ADDR, 32 * 128)
job_a_dest2:  DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_DEST + 32 * 128, DEST2_ADDR, 16 * 128)
job_a_dat:    DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_DAT, LEVEL_BUF, LEVEL_DAT_MAX)
job_a_mus:    DmaJob(DMA_CMD_COPY, ATTIC_LEVELS + LV_MUS, MUS_SLOT, MUS_SLOT_MAX)

// enemy set of level X into place (Stage 13; ENEMn from tools/import_art.py enemy_sets): aircraft and tank
// glyphs, palettes of banks 5-8 (into palette_data; palette_init sets them), the frame-table entries
set_in:
    lda lv_set_bank,x
    sta job_set+DMA_SRC+2
    lda #0
    sta job_set+DMA_SRC
    sta job_set+DMA_SRC+1
    tax
!:  lda set_dlo,x
    sta job_set+DMA_DST
    lda set_dhi,x
    sta job_set+DMA_DST+1
    lda set_dbk,x
    sta job_set+DMA_DST+2
    lda set_llo,x
    sta job_set+DMA_COUNT
    lda set_lhi,x
    sta job_set+DMA_COUNT+1
    RunDma(job_set)
    clc
    lda job_set+DMA_SRC
    adc set_llo,x
    sta job_set+DMA_SRC
    lda job_set+DMA_SRC+1
    adc set_lhi,x
    sta job_set+DMA_SRC+1
    inx
    cpx #set_dhi - set_dlo
    bne !-
    rts
// destinations and sizes of the parts of a set, in file order
set_dlo: .byte <(PIXIE_ADDR + SET_AIR_GLYPH * 64), <(PIXIE_ADDR + SET_TANK_GLYPH * 64), <(palette_data + $50), <(palette_data + $150), <(palette_data + $250), <(frame_base), <(frame_base + FR_TANK_N0), <(frame_base_hi), <(frame_base_hi + FR_TANK_N0), <(frame_w), <(frame_w + FR_TANK_N0), <(frame_h), <(frame_h + FR_TANK_N0), <(frame_pal), <(frame_pal + FR_TANK_N0), <(frame_hit_cx), <(frame_hit_cx + FR_TANK_N0), <(frame_hit_cy), <(frame_hit_cy + FR_TANK_N0), <(frame_hit_halfw), <(frame_hit_halfw + FR_TANK_N0), <(frame_hit_halfh), <(frame_hit_halfh + FR_TANK_N0)
set_dhi: .byte >(PIXIE_ADDR + SET_AIR_GLYPH * 64), >(PIXIE_ADDR + SET_TANK_GLYPH * 64), >(palette_data + $50), >(palette_data + $150), >(palette_data + $250), >(frame_base), >(frame_base + FR_TANK_N0), >(frame_base_hi), >(frame_base_hi + FR_TANK_N0), >(frame_w), >(frame_w + FR_TANK_N0), >(frame_h), >(frame_h + FR_TANK_N0), >(frame_pal), >(frame_pal + FR_TANK_N0), >(frame_hit_cx), >(frame_hit_cx + FR_TANK_N0), >(frame_hit_cy), >(frame_hit_cy + FR_TANK_N0), >(frame_hit_halfw), >(frame_hit_halfw + FR_TANK_N0), >(frame_hit_halfh), >(frame_hit_halfh + FR_TANK_N0)
set_dbk: .byte [(PIXIE_ADDR + SET_AIR_GLYPH * 64) >> 16] & $0f, [(PIXIE_ADDR + SET_TANK_GLYPH * 64) >> 16] & $0f, [(palette_data + $50) >> 16] & $0f, [(palette_data + $150) >> 16] & $0f, [(palette_data + $250) >> 16] & $0f, [(frame_base) >> 16] & $0f, [(frame_base + FR_TANK_N0) >> 16] & $0f, [(frame_base_hi) >> 16] & $0f, [(frame_base_hi + FR_TANK_N0) >> 16] & $0f, [(frame_w) >> 16] & $0f, [(frame_w + FR_TANK_N0) >> 16] & $0f, [(frame_h) >> 16] & $0f, [(frame_h + FR_TANK_N0) >> 16] & $0f, [(frame_pal) >> 16] & $0f, [(frame_pal + FR_TANK_N0) >> 16] & $0f, [(frame_hit_cx) >> 16] & $0f, [(frame_hit_cx + FR_TANK_N0) >> 16] & $0f, [(frame_hit_cy) >> 16] & $0f, [(frame_hit_cy + FR_TANK_N0) >> 16] & $0f, [(frame_hit_halfw) >> 16] & $0f, [(frame_hit_halfw + FR_TANK_N0) >> 16] & $0f, [(frame_hit_halfh) >> 16] & $0f, [(frame_hit_halfh + FR_TANK_N0) >> 16] & $0f
set_llo: .byte <(SET_AIR_GLYPHS * 64), <(SET_TANK_GLYPHS * 64), <(64), <(64), <(64), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16), <(SET_AIR_FRAMES), <(16)
set_lhi: .byte >(SET_AIR_GLYPHS * 64), >(SET_TANK_GLYPHS * 64), >(64), >(64), >(64), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16), >(SET_AIR_FRAMES), >(16)
job_set: DmaJob(DMA_CMD_COPY, $8030000, PIXIE_ADDR, 0)
.errorif (FR_PSHOT1 != SET_AIR_FRAMES), "the enemy set covers frames 0 to FR_PSHOT1 - 1"

// ============================================================== checkpoint (Stage 14)
// A lost plane restarts the level: from its start, or after the mid-level shop once that was reached. The shot
// level drops by one; everything else bought stays. Destroyed buildings stay destroyed after the checkpoint.
level_retry_req: .byte 0
cp_valid:  .byte 0
cp_scroll: .word 0
cp_evp:    .word 0
cp_base:   .word 0

// mid-level shop reached (main loop, before the shop): remember where the level goes on
cp_save:
    lda #1
    sta cp_valid
    lda scroll_px
    sta cp_scroll
    lda scroll_px+1
    sta cp_scroll+1
    lda lev_evp
    sta cp_evp
    lda lev_evp+1
    sta cp_evp+1
    lda lev_base
    sta cp_base
    lda lev_base+1
    sta cp_base+1
    rts

level_retry:
    lda #0
    sta level_retry_req
    sta boss_state
    sta boss_req
    lda pl_power                // the shot level drops by one
    cmp #2
    bcc !+
    dec pl_power
!:  lda cp_valid
    bne !cp+
    lda attic_ok                // from the start: the level fresh from attic RAM
    beq !na+
    lda cur_level
    jsr level_enter
    jmp !go+
!na:
    jsr level_restart           // (without attic RAM: level 1 is in place)
!go:
    jsr buffers_init
    jsr scroll_init
    jmp !obj+
!cp:
    lda cp_scroll
    sta scroll_px
    lda cp_scroll+1
    sta scroll_px+1
    lda cp_evp
    sta lev_evp
    lda cp_evp+1
    sta lev_evp+1
    lda cp_base
    sta lev_base
    lda cp_base+1
    sta lev_base+1
    ldx cur_level               // the boss may have replaced the aircraft glyphs
    jsr set_in
    jsr palette_init
    jsr buffers_init
    jsr scroll_restore
!obj:
    jsr objects_init
    lda #MUS_LEVEL1
    jsr music_play
    jsr player_spawn
    jmp build_frame

// end of a level (main loop, after the event `end`): the next level, the player keeps everything
level_next:
    lda #0
    sta level_next_req
    sta cp_valid                // the new level starts without a checkpoint
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
