// ----------------------------------------------------------------------------
// MEGA65 hardware registers and helper macros
// ----------------------------------------------------------------------------

// VIC-II / VIC-III / VIC-IV
.const VIC_SPR0X     = $d000
.const VIC_SPR0Y     = $d001
.const VIC_SPR1X     = $d002
.const VIC_SPR1Y     = $d003
.const VIC_SPRXMSB   = $d010
.const VIC_CTRL1     = $d011     // bit 7 = raster bit 8
.const VIC_RASTER    = $d012
.const VIC_SPREN     = $d015
.const VIC_CTRL2     = $d016
.const VIC_SPRYEXP   = $d017
.const VIC_IRQ       = $d019
.const VIC_IRQMASK   = $d01a
.const VIC_SPRPRIO   = $d01b
.const VIC_SPRMCM    = $d01c
.const VIC_SPRXEXP   = $d01d
.const VIC_BORDER    = $d020
.const VIC_BGCOL     = $d021
.const VIC_SPR0COL   = $d027
.const VIC_SPR1COL   = $d028
.const VIC_KEY       = $d02f
.const VIC_D030      = $d030     // bit0 CRAM2K, bit2 PAL (RAM palette), bits3-7 ROM banking
.const VIC_D031      = $d031     // bit7 H640, bit6 FAST, bit5 ATTR, bit3 V400
.const VIC_TBDRPOS   = $d048     // top border position (+$d049 low nibble)
.const VIC_BBDRPOS   = $d04a     // bottom border position (+$d04b low nibble)
.const VIC_TEXTXPOS  = $d04c     // (+$d04d low nibble)
.const VIC_TEXTYPOS  = $d04e     // (+$d04f low nibble)
.const VIC_D051      = $d051     // bit7 NORRDEL: 0 = RRB double buffering (keep 0, see CLAUDE.md)
.const VIC_D054      = $d054     // bit0 CHR16, bit2 FCLRHI, bit6 VFAST
.const VIC_SPRHGTEN  = $d055
.const VIC_SPRHGHT   = $d056
.const VIC_SPRX64EN  = $d057
.const VIC_LINESTEP  = $d058     // +$d059
.const VIC_CHRXSCL   = $d05a
.const VIC_SDBDRWD   = $d05c     // side border width low byte
.const VIC_D05D      = $d05d     // bit7 HOTREG, bits0-5 side border width high bits
.const VIC_CHRCOUNT  = $d05e
.const VIC_SCRNPTR   = $d060     // $d060-$d063 (28 bit)
.const VIC_D063      = $d063     // bits 4-5 CHRCOUNT bits 8-9
.const VIC_COLPTR    = $d064     // +$d065
.const VIC_SPR16EN   = $d06b
.const VIC_SPRPTR    = $d06c     // $d06c-$d06e, $d06e bit7 = 16-bit sprite pointers
.const VIC_PALSEL    = $d070     // 7-6 MAPEDPAL, 5-4 BTPALSEL, 3-2 SPRPALSEL, 1-0 ABTPALSEL
.const VIC_DISPROWS  = $d07b
.const PAL_RED       = $d100
.const PAL_GREEN     = $d200
.const PAL_BLUE      = $d300

// CIA
.const CIA1_PRA      = $dc00     // joystick port 2 (active low: 0 up 1 down 2 left 3 right 4 fire)
.const CIA1_DDRA     = $dc02
.const CIA1_ICR      = $dc0d
.const CIA2_ICR      = $dd0d

// DMAgic
.const DMA_ADDRLSB_ETRIG = $d705
.const DMA_ADDRMSB   = $d701
.const DMA_ADDRBANK  = $d702
.const DMA_ADDRMB    = $d704

.const JOY_UP    = %00000001
.const JOY_DOWN  = %00000010
.const JOY_LEFT  = %00000100
.const JOY_RIGHT = %00001000
.const JOY_FIRE  = %00010000

// ----------------------------------------------------------------------------
// F018A DMA job in enhanced (option-list) form, as used and verified in Vyper.
// Field offsets for run-time patching:
.const DMA_CMD   = 6
.const DMA_COUNT = 7
.const DMA_SRC   = 9     // lo16, then bank nibble at +2
.const DMA_DST   = 12    // lo16, then bank nibble at +2
.const DMA_SRCMB = 2
.const DMA_DSTMB = 4
.const DMA_CMD_COPY = $00
.const DMA_CMD_FILL = $03

.macro DmaJob(cmd, src, dst, len) {
    .byte $0a                 // list is F018A format
    .byte $80, (src >> 20) & $ff
    .byte $81, (dst >> 20) & $ff
    .byte $00                 // end of options
    .byte cmd
    .word len
    .word src & $ffff
    .byte (src >> 16) & $0f
    .word dst & $ffff
    .byte (dst >> 16) & $0f
    .word 0                   // modulo (unused)
}

// Run the DMA job at a constant bank-0 address. CPU halts until it is done.
.macro RunDma(list) {
    lda #0
    sta DMA_ADDRBANK
    sta DMA_ADDRMB
    lda #>list
    sta DMA_ADDRMSB
    lda #<list
    sta DMA_ADDRLSB_ETRIG
}
