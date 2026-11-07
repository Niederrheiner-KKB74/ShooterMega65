// ----------------------------------------------------------------------------
// Level transition (Stage 15), see docs/stage15.md and docs/design.md.
//
// When the boss is gone (boss.asm) the victory fanfare plays and level_clear_req counts down CLEAR_DELAY frames;
// then the main loop calls level_transition, which pauses the game:
//   1. "LEVEL CLEAR!" with a picture of the destroyed boss, "PRESS FIRE TO CONTINUE" blinking;
//   2. fire: the end shop (shop_run, as before after the boss);
//   3. the screen fades to black, the next level is set up behind the black screen;
//   4. "PREPARE FOR LEVEL n" on the black screen; fire: the level fades in and starts.
//
// Pictures: file TRANS (tools/make_overlays.py) in attic bank $0D; one picture at a time is copied over the
// shop glyphs ($44000) and its maps into ov_map, then drawn with blit_msg (shop.asm, pictures 3 and 4). The
// shop glyphs come back from a copy in attic bank $0E.
//
// Fading: the screen is shown through palette 2 while the transition runs (pal_show = $20). Palette 0 keeps the
// real colours (and receives the next level's colours from palette_init), palette 2 gets them scaled by k/16.
// So the next level can be set up while the screen stays black. Only fade_set and the PREPARE picture write
// palette 2 (VIC_PALSEL edit bits); everything else keeps writing palette 0.
// ----------------------------------------------------------------------------
#import "../build/gen/trans_data.inc"

.const ATTIC_TRANS  = $80D0000
.const ATTIC_SHOPG  = $80E0000
.const FADE_FRAMES  = 2                      // frames per fade step (16 steps)
.const PALSEL_GAME  = $04                    // edit 0, text 0, sprites 1 (video.asm)
.const PALSEL_SHOW2 = $24                    // edit 0, text palette 2 shown
.const PALSEL_EDIT2 = $a4                    // edit 2, text palette 2 shown

.errorif (TRANS_BYTES > $10000), "TRANS must fit one attic bank"
.errorif (TR_COL0 + TR_COLS > BG_TOKENS), "transition picture wider than the background"
.errorif (TR_CLEAR_ROW0 + TR_CLEAR_ROWS > VIS_ROWS - 1), "LEVEL CLEAR picture below the visible rows"
.errorif (TR_PREP_ROW0 + TR_PREP_ROWS > VIS_ROWS - 1), "PREPARE picture below the visible rows"

level_clear_req: .byte 0                    // > 0: frames until LEVEL CLEAR
pal_show:        .byte 0                    // $20 while palette 2 is shown (ORed into VIC_PALSEL writes)

// ============================================================== loading (KERNAL, levels_load, attic only)
// TRANS -> attic bank $0D; a copy of the shop glyphs -> attic bank $0E. Carry set = failed.
trans_load:
    lda #(ATTIC_TRANS >> 16) & $0f
    sta lv_bank
    lda #0
    tax
    ldy #(>TRANS_BYTES) + 1
    jsr lv_dst
    lda #<name_trans
    ldx #>name_trans
    ldy #name_trans_end - name_trans
    jsr load_seq_to
    bcs !+
    RunDma(job_shopg_save)
    clc
!:  rts
name_trans: .text "TRANS"
name_trans_end:

// ============================================================== the transition (main loop)
level_transition:
    lda #0
    sta level_clear_req
    lda level_retry_req         // plane lost meanwhile: no transition, the level is retried
    ora game_over_req
    beq !+
    rts
!:  sta shop_req                // (the end-shop event may have been reached during the delay)
    sta level_next_req
    lda #$ff
    jsr music_queue
    jsr ov_clean
    jsr ov_palettes
    lda cur_level               // LEVEL CLEAR + destroyed boss
    jsr ov_show
    jsr ov_wait
    jsr shop_glyphs_back
    lda cur_level               // Stage 16: after the last level the end of the mission
    cmp #LEVELS - 1
    bne !+
    jmp mission_end
!:  jsr shop_run                // the end shop
    jsr wait_vblank
    jsr flip                    // shop_run built the back buffer without its panel
    lda #$ff
    jsr music_queue
    jsr music_stop
    jsr fade_out
    // next level behind the black screen (palette_init writes palette 0)
    jsr level_next
    jsr ov_clean
    lda #PALSEL_EDIT2           // PREPARE FOR LEVEL n in palette 2 (banks 13-15), the rest stays black
    sta VIC_PALSEL
    jsr ov_palettes
    lda cur_level
    clc
    adc #4
    jsr ov_show
    jsr ov_wait
    lda #PALSEL_SHOW2
    sta VIC_PALSEL
    jsr shop_glyphs_back
    jsr ov_clean                // both buffers without the picture
    // fade in: palette 2 from black to palette 0, then show palette 0 again
    jsr pal_snapshot
    lda #1
    sta fd_step
!:  jsr fade_wait
    lda fd_step
    jsr fade_set
    inc fd_step
    lda fd_step
    cmp #17
    bne !-
    lda #0
    sta pal_show
    lda #PALSEL_GAME
    sta VIC_PALSEL
    lda #MUS_LEVEL1
    jsr music_play
    lda #INV_FRAMES
    sta pl_inv
    rts

// fade out: palette 2 = palette 0, show palette 2, darken it to black
fade_out:
    jsr pal_snapshot
    lda #16
    jsr fade_set
    lda #$20
    sta pal_show
    lda #PALSEL_SHOW2
    sta VIC_PALSEL
    lda #15
    sta fd_step
!:  jsr fade_wait
    lda fd_step
    jsr fade_set
    dec fd_step
    bpl !-
    rts

// Stage 16: level 4 cleared -> fade out, MISSION ACCOMPLISHED, high-score entry, title, new game
mission_end:
    lda #$ff
    jsr music_queue
    jsr music_stop
    jsr fade_out
    jsr hiscore_update
    jsr menu_in
    jsr mission_page            // (hipages.asm; ends with palette 0 shown)
    lda #5
    jsr hi_after_game
    jsr menu_out
    jsr palette_init
    jsr title_run
    jmp game_new

// objects away, both buffers rebuilt (without objects and pictures), player hidden
ov_clean:
    jsr objects_init
    jsr build_frame
    jsr wait_vblank
    jsr flip
    jsr build_frame
    jsr wait_vblank
    jsr flip
    lda #0
    sta VIC_SPREN
    rts

// shop palettes into banks 13-15 of the palette being edited; bank 15 = bank 13 with the blinking colours 4 and 8
ov_palettes:
    jsr shop_palettes
    ldx #15
!:  lda shop_pal,x
    sta PAL_RED+$f0,x
    lda shop_pal+16,x
    sta PAL_GREEN+$f0,x
    lda shop_pal+32,x
    sta PAL_BLUE+$f0,x
    dex
    bpl !-
    lda #PAL_SHOP_H
    sta tok_pal+18
    rts

// picture A (0-3 LEVEL CLEAR of level A+1, 4-7 PREPARE FOR LEVEL A-3): glyphs, maps, into both buffers
ov_show:
    sta ov_pic
    tax
    lda tr_ofs_lo,x
    sta job_trg+DMA_SRC
    lda tr_ofs_hi,x
    sta job_trg+DMA_SRC+1
    lda tr_glyphs,x             // count * 64
    lsr
    lsr
    sta job_trg+DMA_COUNT+1
    lda tr_glyphs,x
    asl
    asl
    asl
    asl
    asl
    asl
    sta job_trg+DMA_COUNT
    RunDma(job_trg)
    clc                         // the maps follow the glyphs
    lda job_trg+DMA_SRC
    adc job_trg+DMA_COUNT
    sta job_trm+DMA_SRC
    lda job_trg+DMA_SRC+1
    adc job_trg+DMA_COUNT+1
    sta job_trm+DMA_SRC+1
    ldx ov_pic
    lda tr_rows,x               // glyph map + attribute map: rows * cols * 2
    ldx #TR_COLS * 2
    jsr mul8
    lda sh_size
    sta job_trm+DMA_COUNT
    lda sh_size+1
    sta job_trm+DMA_COUNT+1
    RunDma(job_trm)
    ldy #3                      // blit_msg picture 3 (LEVEL CLEAR) or 4 (PREPARE)
    lda ov_pic
    cmp #4
    bcc !+
    iny
!:  lda #<ov_map
    ldx #>ov_map
    jmp blit_msg

// paused frames until fire; the line with attribute 18 blinks (bank 15 colours 4 and 8)
ov_wait:
    lda joy
    sta sh_prev
    lda #0                      // fire must be released first
    sta sh_rel
!:  jsr shop_frame
    ldx #11                     // on: yellow text, dark shadow; off: both panel background
    ldy #2
    lda sh_blink
    and #16
    bne !on+
    ldx #1
    ldy #1
!on:
    lda shop_pal,x
    sta PAL_RED+$f4
    lda shop_pal+16,x
    sta PAL_GREEN+$f4
    lda shop_pal+32,x
    sta PAL_BLUE+$f4
    lda shop_pal,y
    sta PAL_RED+$f8
    lda shop_pal+16,y
    sta PAL_GREEN+$f8
    lda shop_pal+32,y
    sta PAL_BLUE+$f8
    lda sh_press
    and #$10
    beq !-
    lda #SFX_SELECT
    jmp sfx_play

shop_glyphs_back:
    RunDma(job_shopg_back)
    rts

fade_wait:
    lda #FADE_FRAMES
    sta fd_w
!:  jsr wait_vblank
    jsr sound_frame
    dec fd_w
    bne !-
    rts

// ============================================================== palette fade
// palette 0 (all 256 entries) -> pal_snap
pal_snapshot:
    ldx #0
!:  lda PAL_RED,x
    sta pal_snap,x
    lda PAL_GREEN,x
    sta pal_snap+256,x
    lda PAL_BLUE,x
    sta pal_snap+512,x
    inx
    bne !-
    rts

// palette 2 <- pal_snap * A / 16 (A = 0-16). Register values hold the colour with swapped nibbles, so
// fade_tab[swap(r)] = swap(r * A / 16) is built first (r * A summed up in fd_acc), then looked up.
fade_set:
    sta fd_k
    lda #0
    sta fd_acc
    sta fd_acc+1
    tax
!t: txa                         // y = swap(x)
    asl
    adc #$80
    rol
    asl
    adc #$80
    rol
    tay
    lda fd_acc+1                // swap(fd_acc >> 4) = (fd_acc & $f0) | (fd_acc >> 8)
    and #$0f
    sta fd_t
    lda fd_acc
    and #$f0
    ora fd_t
    sta fade_tab,y
    clc
    lda fd_acc
    adc fd_k
    sta fd_acc
    bcc !+
    inc fd_acc+1
!:  inx
    bne !t-
    lda #PALSEL_EDIT2
    sta VIC_PALSEL
!a: ldy pal_snap,x
    lda fade_tab,y
    sta PAL_RED,x
    ldy pal_snap+256,x
    lda fade_tab,y
    sta PAL_GREEN,x
    ldy pal_snap+512,x
    lda fade_tab,y
    sta PAL_BLUE,x
    inx
    bne !a-
    lda #PALSEL_GAME
    ora pal_show
    sta VIC_PALSEL
    rts

ov_pic:  .byte 0
fd_step: .byte 0
fd_w:    .byte 0
fd_k:    .byte 0
fd_t:    .byte 0
fd_acc:  .word 0

job_trg:        DmaJob(DMA_CMD_COPY, ATTIC_TRANS, SHOP_ADDR, 0)
job_trm:        DmaJob(DMA_CMD_COPY, ATTIC_TRANS, ov_map, 0)
job_shopg_save: DmaJob(DMA_CMD_COPY, SHOP_ADDR, ATTIC_SHOPG, SHOP_GLYPHS * 64)
job_shopg_back: DmaJob(DMA_CMD_COPY, ATTIC_SHOPG, SHOP_ADDR, SHOP_GLYPHS * 64)
.errorif (SHOP_ADDR + 160 * 64 > PIXIE_ADDR), "transition glyphs overlap the pixie glyphs"

// work buffers in BASIC's text screen area $0800-$0FFF (saved to SAVED_SCR at start, restored on exit)
.label fade_tab = $0800                     // 256, page aligned
.label pal_snap = $0900                     // 768
.label ov_map   = $0c00                     // TR_MAP_MAX * 2
.errorif (ov_map + TR_MAP_MAX * 2 > $1000), "transition buffers beyond $0FFF"
