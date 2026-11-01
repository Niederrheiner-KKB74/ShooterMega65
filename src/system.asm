// ----------------------------------------------------------------------------
// Entry state save / exit to BASIC, and keyboard via the hardware ASCII queue.
//
// Exit strategy follows Vyper (stage10a6.asm exit_to_basic, confirmed on
// hardware): HOTREG off, restore the saved VIC-IV registers directly, HOTREG
// last. In addition the game never changes the memory map, the stack pointer,
// BASIC's screen RAM or the first 4 KB of colour RAM, so BASIC can continue
// with an intact screen after the final RTS.
// ----------------------------------------------------------------------------

.const KEYQUEUE = $d610          // MEGA65 hardware keyboard: ASCII of the oldest key, write = pop

// VIC registers saved at start and written back on exit (HOTREG $D05D last).
.var vic_restore = List().add(
    $d010, $d015, $d017, $d01b, $d01c, $d01d, $d020, $d021, $d027, $d028,
    $d030, $d031, $d048, $d049, $d04a, $d04b, $d04c, $d04d, $d04e, $d04f,
    $d051, $d054, $d055, $d056, $d057, $d058, $d059, $d05a, $d05c, $d05e,
    $d060, $d061, $d062, $d063, $d064, $d065, $d06b, $d06c, $d06d, $d06e,
    $d070, $d07b, $d029, $d02a, $d02b).lock()

// called right after SEI, before anything is changed
system_save:
    tsx                          // SP as it will be after returning to the caller
    inx
    inx
    stx saved_sp
    tsy
    sty saved_sph
    tba
    sta saved_b
    lda #0
    tab                          // our zero page is $00xx
    ldx #2                       // zero page $02-$ff (absolute addressing, independent of B)
!:  lda $0000,x
    sta saved_zp,x
    inx
    bne !-
    lda CIA1_DDRA
    sta saved_ddra
    .for (var i = 0; i < vic_restore.size(); i++) {
        lda vic_restore.get(i)
        sta saved_vic + i
    }
    lda VIC_D05D
    sta saved_d05d
    // palette 0 (all 256 entries) and palette 1 entries 0-79 (sprite palette: player, ring)
    lda VIC_PALSEL
    and #%00111111               // MAPEDPAL = 0
    sta VIC_PALSEL
    ldx #0
!:  lda PAL_RED,x
    sta saved_pal0,x
    lda PAL_GREEN,x
    sta saved_pal0+$100,x
    lda PAL_BLUE,x
    sta saved_pal0+$200,x
    inx
    bne !-
    lda VIC_PALSEL
    ora #%01000000               // MAPEDPAL = 1
    sta VIC_PALSEL
    ldx #79
!:  lda PAL_RED,x
    sta saved_pal1,x
    lda PAL_GREEN,x
    sta saved_pal1+80,x
    lda PAL_BLUE,x
    sta saved_pal1+160,x
    dex
    bpl !-
    lda saved_vic + vic_restore.size() - 5   // $d070
    sta VIC_PALSEL
    jmp key_drain

exit_to_basic:
    sei
    lda #0
    sta VIC_SPREN
    jsr wait_vblank              // switch modes while the raster is in the border
    // palettes (VIC-IV I/O personality is still active)
    lda #$00                     // MAPEDPAL = 0
    sta VIC_PALSEL
    ldx #0
!:  lda saved_pal0,x
    sta PAL_RED,x
    lda saved_pal0+$100,x
    sta PAL_GREEN,x
    lda saved_pal0+$200,x
    sta PAL_BLUE,x
    inx
    bne !-
    lda #$40                     // MAPEDPAL = 1
    sta VIC_PALSEL
    ldx #79
!:  lda saved_pal1,x
    sta PAL_RED,x
    lda saved_pal1+80,x
    sta PAL_GREEN,x
    lda saved_pal1+160,x
    sta PAL_BLUE,x
    dex
    bpl !-
    // VIC-IV registers: HOTREG off first, saved values, HOTREG last
    lda VIC_D05D
    and #$7f
    sta VIC_D05D
    sta VIC_D05D
    .for (var i = 0; i < vic_restore.size(); i++) {
        lda saved_vic + i
        sta vic_restore.get(i)
    }
    lda saved_d05d
    sta VIC_D05D
    lda saved_ddra
    sta CIA1_DDRA
    jsr key_drain                // do not hand the exit key to BASIC
    // zero page, base page and stack as BASIC left them
    ldx #2
!:  lda saved_zp,x
    sta $0000,x
    inx
    bne !-
    lda saved_b
    tab
    ldx saved_sp
    ldy saved_sph
    tys
    txs
    ldz #0                       // C65 ROM code expects Z = 0
    lda #0
    tax
    tay
    cli
    rts                          // back to the SYS caller -> READY.

// Read one key from the hardware queue (0 = none). Handles the global keys.
read_keys:
    lda KEYQUEUE
    beq !none+
    sta KEYQUEUE                 // pop
    cmp #$03                     // RUN/STOP
    beq !exit+
    cmp #$20                     // space
    beq !space+
    and #$df                     // fold lower case
    cmp #$58                     // X
    beq !exit+
    cmp #$53                     // S: invulnerability (special.asm)
    bne !+
    lda #1
    sta inv_req
    rts
!:  cmp #$44                     // D: toggle the raster time display
    bne !none+
    lda debug_raster
    eor #1
    sta debug_raster
    rts
!space:
    lda #1                       // space: bomb (special.asm)
    sta special_req
!none:
    rts
!exit:
    jmp exit_to_basic

key_drain:
!:  lda KEYQUEUE
    beq !+
    sta KEYQUEUE
    bne !-
!:  rts

special_req: .byte 0
debug_raster: .byte 0
saved_sp:   .byte 0
saved_sph:  .byte 0
saved_b:    .byte 0
saved_ddra: .byte 0
saved_d05d: .byte 0
saved_vic:  .fill vic_restore.size(), 0
saved_zp:   .fill 256, 0
saved_pal0: .fill 768, 0
saved_pal1: .fill 240, 0
