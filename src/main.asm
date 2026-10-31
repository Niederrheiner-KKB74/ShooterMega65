// ============================================================================
// ShooterMega65 - Stage 1 engine prototype
//   H320/V200, 16-colour (NCM) tiles, vertically scrolling landscape,
//   RRB pixies for all moving objects, hardware sprites for the player.
// Build: python3 tools/build.py   (KickAssembler 65CE02 5.25, see README)
// ============================================================================
.cpu _45gs02

#import "hw.asm"
#import "layout.asm"
#import "../build/gen/assets.inc"

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

.const SCROLL_SPEED = $0080    // 8.8 pixels per frame (0.5 px = 25 px/s)
.const DEBUG_RASTER = 1        // border shows CPU time used per frame

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
    sei
    lda #$35
    sta $01
    lda #0                             // unmap everything: plain bank 0 RAM + I/O
    tax
    tay
    taz
    map
    eom
    tab                                // base page = $00xx
    lda #$47                           // VIC-IV I/O personality
    sta VIC_KEY
    lda #$53
    sta VIC_KEY
    lda #65                            // 40.5 MHz
    sta $00
    lda #$7f                           // no CIA / VIC interrupts, we poll the raster
    sta CIA1_ICR
    sta CIA2_ICR
    lda CIA1_ICR
    lda CIA2_ICR
    lda #0
    sta VIC_IRQMASK
    lda #$ff
    sta VIC_IRQ
    lda #0
    sta CIA1_DDRA                      // port A as input: joystick 2 only
    cld
    ldx #$ff
    txs

    lda #0
    sta frame_lo
    sta frame_hi
    jsr video_init
    jsr assets_init
    jsr scroll_init
    jsr objects_init
    jsr player_init
    lda #$a7
    sta seed

    // build the first frame into buffer A, show it, then run the loop
    lda #0
    sta back
    jsr build_frame

main_loop:
    jsr wait_vblank
    jsr flip                           // show the buffer just built
    jsr player_update_sprites          // sprite registers during vblank
    .if (DEBUG_RASTER == 1) {
        lda #2
        sta VIC_BORDER
    }
    inc frame_lo
    bne !+
    inc frame_hi
!:
    jsr read_joystick
    jsr player_move
    jsr scroll_advance
    jsr build_frame
    .if (DEBUG_RASTER == 1) {
        lda #0
        sta VIC_BORDER
    }
    jmp main_loop

// ---------------------------------------------------------------- frame
// Build the complete next frame into the back buffer.
build_frame:
    jsr scroll_copy_rows               // background rows (DMA) + reset row fill levels
    jsr spawn_update
    jsr objects_update
    jsr collide_shots
    jsr objects_draw
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

// ---------------------------------------------------------------- data
.align $100
sin_tab:   .fill 256, round(48 * sin(toRadians(i * 360 / 256)))   // signed
#import "../build/gen/frames.inc"

code_end:
.align $100
map_data:     .import binary "../build/gen/map.bin"
mapcol_data:  .import binary "../build/gen/mapcol.bin"
tile_data:    .import binary "../build/gen/tiles.bin"
tile_end:
pixie_data:   .import binary "../build/gen/pixies.bin"
pixie_end:
.align $100
sprite_data:  .import binary "../build/gen/sprite.bin"
palette_data: .import binary "../build/gen/palette.bin"
sprpal_data:  .import binary "../build/gen/sprpal.bin"
prg_end:
.errorif (prg_end > $c000), "PRG too large for bank 0 below $c000"
.print "code ends at $" + toHexString(code_end) + ", PRG ends at $" + toHexString(prg_end)
