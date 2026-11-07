// ============================================================================
// ShooterMega65 - Stage 1 engine prototype
//   H320/V200, 16-colour (NCM) tiles, vertically scrolling landscape,
//   RRB pixies for all moving objects, hardware sprites for the player.
// Build: python3 tools/build.py   (KickAssembler 65CE02 5.25, see README)
// Keys:  joystick port 2, X or RUN/STOP = back to BASIC
// ============================================================================
.cpu _45gs02

#import "hw.asm"
#import "layout.asm"
#import "../build/gen/assets.inc"
#import "../build/gen/shop_const.inc"
#import "../build/gen/music_const.inc"
#import "../build/gen/screens_const.inc"
#import "../build/gen/trans_const.inc"

// ---------------------------------------------------------------- zero page
.const ZP = $02
.label frame_lo     = $02
.label frame_hi     = $03
.label back         = $04      // 0 = build into A, 1 = build into B
.label fine         = $05      // scroll_px & 7 of the frame being built
.label scroll_frac  = $06
.label scroll_px    = $07      // 16 bit
.label scroll_delta = $09      // whole pixels scrolled this frame
.label joy          = $0a      // joystick bits, active HIGH after read_joystick
.label seed         = $0b
.label k0           = $0c      // ring slot of display row 0
.label overflow     = $0d      // RRB fragments dropped this frame (debug)
.label scr_ptr      = $10      // 32-bit pointer into the screen buffer
.label col_ptr      = $14      // 32-bit pointer into colour RAM
.label tmp          = $18      // 16 bit
.label tmp2         = $1a      // 16 bit
.label backscr      = $34      // low 16 bits of the back screen buffer (bank 5)
.label backcol      = $36      // colour RAM offset of the back buffer
.label pend_typos   = $38      // TEXTYPOS for the frame being built


// ---------------------------------------------------------------- BASIC stub
*=$2001
    .word basic_end, 10
    .byte $fe, $02, $30, $3a           // BANK 0:
    .byte $9e                          // SYS
    .text "8224"                       // $2020
    .byte 0
basic_end:
    .word 0

*=$2020

// ---------------------------------------------------------------- entry
start:
    jsr load_device                    // drive of the last LOAD
    jsr shop_load                      // shop glyphs from disk (shop.asm)
    bcs !fail+
    jsr music_load                     // music and sound effects (sound.asm)
    bcs !fail+
    jsr pixies_load                    // all pixie glyphs, straight into the pixie area
    bcs !fail+
    jsr sprites_load                   // Stage 14: player sprite frames straight to SPRITE_ADDR (were in the PRG)
    bcs !fail+
    jsr attic_detect                   // attic RAM? (screens.asm)
    lda attic_ok
    beq !direct+
    jsr levels_load                    // Stage 9: all levels and bosses into attic RAM (levels.asm)
    jmp !loaded+
!direct:
    jsr level_load                     // without attic RAM: level 1 straight into place (level.asm)
!loaded:
    bcs !fail+
    jsr pixies2_load                   // heavy gun glyphs behind LnDAT (ground.asm)
    bcs !fail+
    jsr pixies3_load                   // Stage 15: diagonal enemy shots behind screen buffer A (ground.asm)
    bcs !fail+
    jsr screens_load                   // title and game-over banner: attic RAM or title directly (screens.asm)
    bcs !fail+
    lda attic_ok                       // Stage 16: menu overlay to attic RAM, high-score list from disk
    beq !+
    jsr menu_load
    bcs !fail+
    jsr menu_in
    jsr hi_boot                        // (the default list if there is no file; never fails)
    jsr menu_out
    clc
    bcc !+
!fail:
    rts                                // failed: message printed, back to BASIC
!:  sei
    lda #$47                           // VIC-IV I/O personality
    sta VIC_KEY
    lda #$53
    sta VIC_KEY
    jsr system_save                    // everything needed to return to BASIC (also sets B = 0)
    // The memory map, the stack and the interrupt sources stay as BASIC left them;
    // SEI keeps the KERNAL interrupt handler from running while the game owns the machine.
    // Code and data stay below $C000, which is RAM under the SYS memory map (as in Vyper).
    lda #0
    sta CIA1_DDRA                      // port A as input: joystick 2 only (restored on exit)
    cld

    lda #0
    sta special_req
    sta debug_raster
    sta frame_lo
    sta frame_hi
    jsr video_init
    jsr assets_init
    jsr level_init
    lda #0                             // no boss (the files were just loaded: nothing to swap back)
    sta boss_state
    sta boss_req
    sta game_over_req
    sta title_seen
    jsr sound_init
    lda #$a7
    sta seed

#if MUSIC_TEST
    jsr buffers_init
    lda #MUS_LEVEL1
    jsr music_play
    jmp music_test                     // test build: keys 1-6 play the pieces, T = 440 Hz, X = BASIC
#endif
    jsr title_run                      // title screen (screens.asm), then a new game
    jsr game_new

main_loop:
    jsr wait_vblank
    jsr flip                           // show the buffer just built
    jsr player_update_sprites          // sprite registers during vblank
    jsr special_vblank                 // invulnerability ring colours, bomb flash
    jsr sound_frame                    // music and sound effects, 50 times per second
    lda debug_raster                   // D key: border shows the CPU time per frame
    beq !+
    lda #2
    sta VIC_BORDER
!:
    inc frame_lo
    bne !+
    inc frame_hi
!:
#if HI_TEST
    lda frame_hi                       // test build (--define HI_TEST): game over after 256 frames
    cmp #1
    bne !+
    lda frame_lo
    bne !+
    lda #1
    sta game_over_req
!:
#endif
    jsr read_keys                      // X or RUN/STOP: exit to BASIC; space: bomb; S: invulnerability
    jsr special_update
    jsr read_joystick
    jsr player_move
    jsr scroll_advance
    jsr build_frame
    lda #0
    sta VIC_BORDER
    lda level_clear_req                // Stage 15: boss gone -> after CLEAR_DELAY frames LEVEL CLEAR, end shop,
    beq ml_shop                        // fade, next level (transition.asm); the end shop waits for it
    dec level_clear_req
    bne ml_retry
    jsr level_transition
    jmp main_loop
ml_shop:
    lda shop_req                       // shop event reached: paused shop overlay
    beq ml_retry
    cmp #1                             // mid-level shop: the checkpoint after a lost plane (Stage 14)
    bne !sh+
    jsr cp_save
!sh:
    jsr shop_run
ml_retry:
    lda level_retry_req                // plane lost: the level again from its start or checkpoint
    beq !+
    jsr level_retry
!:  lda level_next_req                 // level end with attic RAM: the next level (levels.asm)
    beq !+
    jsr level_next
!:  lda game_over_req                  // last plane lost: game over, title, new game
    beq !+
    jsr game_over_run
    jsr title_run
    jsr game_new
!:  jmp main_loop

#if MUSIC_TEST
music_test:
    jsr wait_vblank
    jsr sound_frame
    lda $d610                          // KEYQUEUE
    beq music_test
    sta $d610
    cmp #$31
    bcc !+
    cmp #$31 + MUSIC_PIECES
    bcs !+
    sec
    sbc #$31
    jsr music_play
    jmp music_test
!:  and #$df
    cmp #$54                           // T: test tone A-4 = 440 Hz (tuning check), triangle, SID 1 + 3
    bne !+
    jsr music_stop
    lda freq_lo+57
    sta $d400
    sta $d440
    lda freq_hi+57
    sta $d401
    sta $d441
    lda #$00
    sta $d405
    sta $d445
    lda #$f0
    sta $d406
    sta $d446
    lda #$0f
    sta $d418
    sta $d458
    lda #$11
    sta $d404
    sta $d444
    jmp music_test
!:  cmp #$58
    bne music_test
    jmp exit_to_basic
#endif

// ---------------------------------------------------------------- frame
// Build the complete next frame into the back buffer.
build_frame:
    jsr anim_frame                     // tile animations (Stage 13)
    jsr scroll_copy_rows               // background rows (DMA) + reset row fill levels
    jsr spawn_update
    jsr boss_update
    jsr objects_update
    jsr collide_shots
    jsr collide_player
    jsr hud_update
    jsr objects_draw                   // objects, then the HUD on top
    rts

// Wait until the raster is in the bottom border area (VIC-II line >= 256),
// and only after having been outside it, so we never flip twice per frame.
wait_vblank:
!:  bit VIC_CTRL1
    bmi !-
!:  bit VIC_CTRL1
    bpl !-
    rts

read_joystick:
    lda CIA1_PRA
    eor #$ff
    and #$1f
    sta joy
    rts

// 8-bit Galois LFSR, returns A
random:
    lda seed
    asl
    bcc !+
    eor #$1d
!:  sta seed
    rts

#import "video.asm"
#import "scroll.asm"
#import "pixie.asm"
#import "objects.asm"
#import "player.asm"
#import "hud.asm"
#import "system.asm"
#import "level.asm"
#import "shop.asm"
#import "special.asm"
#import "sound.asm"
swap_start:                            // Stage 16: overlay area for the menu code (menu.asm)
#import "boss.asm"
#import "ground.asm"
swap_end:
#import "levels.asm"
#import "anim.asm"
#import "screens.asm"
#import "transition.asm"
#import "menu.asm"

// file PIXIES: the complete pixie glyph area image (tools/import_art.py), loaded to PIXIE_ADDR
pixies_load:
    lda #<(PIXIE_ADDR & $ffff)
    sta ld_dst
    lda #>(PIXIE_ADDR & $ffff)
    sta ld_dst+1
    lda #(PIXIE_ADDR >> 16)
    sta ld_dst+2
    lda #>(PIXIE_MAX * 64)
    sta ld_maxhi
    lda #<name_pixies
    ldx #>name_pixies
    ldy #name_pixies_end - name_pixies
    jmp load_seq_to
name_pixies: .text "PIXIES"
name_pixies_end:
sprites_load:
    lda #<(SPRITE_ADDR & $ffff)
    sta ld_dst
    lda #>(SPRITE_ADDR & $ffff)
    sta ld_dst+1
    lda #(SPRITE_ADDR >> 16)
    sta ld_dst+2
    lda #(>(PLAYER_FRAMES * $200 + 3 * 256)) + 1     // Stage 16: the ring sprites follow (RING_ADDR)
    sta ld_maxhi
    lda #<name_sprites
    ldx #>name_sprites
    ldy #7
    jmp load_seq_to
name_sprites: .text "SPRITES"

.errorif (SPRITE_ADDR + PLAYER_FRAMES * $200 != RING_ADDR), "file SPRITES: the ring must follow the player frames"
.errorif (((PIXIE_ADDR & $ffff) + PIXIE_MAX * 64) > $10000), "pixie area crosses a 64 KB boundary"

// ---------------------------------------------------------------- data
#import "../build/gen/frames.inc"

code_end:
pixie_end:
palette_data: .import binary "../build/gen/palette.bin"
sprpal_data:  .import binary "../build/gen/sprpal.bin"
prg_end:
.errorif (prg_end > $c000), "PRG too large for bank 0 below $c000"
.errorif (PIXIE_GLYPHS > PIXIE_MAX), "pixie glyph area ($46800-$4FFFF) exceeded"
.print "code ends at $" + toHexString(code_end) + ", PRG ends at $" + toHexString(prg_end)

// ---------------------------------------------------------------- Stage 16: menu overlay (file HIMENU)
// High scores, text pages, name entry, end screen: assembled for swap_start, written to HIMENU.bin, kept in
// attic RAM and swapped in over boss.asm/ground.asm while no game runs (menu.asm).
.segmentdef Menu [start=$0000]
.file [name="HIMENU.bin", type="bin", segments="Menu"]
.segment Menu
.pseudopc swap_start {
menu_start:
#import "hiscore.asm"
#import "textpage.asm"
#import "hipages.asm"
menu_end:
}
.segment Default
