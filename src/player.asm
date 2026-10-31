// ----------------------------------------------------------------------------
// Player: two 16-colour hardware sprites (32x24), joystick port 2.
// ----------------------------------------------------------------------------
.label pl_x    = $50      // 16 bit, 0..PL_MAX_X (playfield coordinates, left edge of the plane)
.label pl_y    = $52      // 0..PL_MAX_Y
.label pl_cd   = $53      // fire cooldown

.const PL_W     = 32
.const PL_H     = 24
.const PL_MAX_X = 320 - PL_W
.const PL_MAX_Y = 200 - PL_H
.const PL_SPEED = 2
.const FIRE_RATE = 6
.const SPR_XOFS = 24      // VIC-II sprite coordinates of the playfield's top left pixel
.const SPR_YOFS = 50

player_init:
    lda #<SPRPTR_TABLE
    sta VIC_SPRPTR
    lda #>SPRPTR_TABLE
    sta VIC_SPRPTR+1
    lda #$80                    // table in bank 0, 16-bit pointers
    sta VIC_SPRPTR+2
    lda #<SPRITE_PTR0
    sta SPRPTR_TABLE
    lda #>SPRITE_PTR0
    sta SPRPTR_TABLE+1
    lda #<SPRITE_PTR1
    sta SPRPTR_TABLE+2
    lda #>SPRITE_PTR1
    sta SPRPTR_TABLE+3
    lda #%00000011
    sta VIC_SPR16EN             // 16 colours (16 px wide, 8 bytes per row)
    sta VIC_SPRHGTEN
    lda #PL_H
    sta VIC_SPRHGHT
    lda #0
    sta VIC_SPRX64EN
    sta VIC_SPRXEXP
    sta VIC_SPRYEXP
    sta VIC_SPRPRIO
    sta VIC_SPRMCM
    sta VIC_SPR0COL             // in 16-colour mode: transparent colour index
    sta VIC_SPR1COL
    sta pl_cd
    sta pl_frame
    sta pl_drawn_frame
    lda #<(160 - PL_W/2)
    sta pl_x
    lda #>(160 - PL_W/2)
    sta pl_x+1
    lda #150
    sta pl_y
    jsr player_update_sprites
    lda #%00000011
    sta VIC_SPREN
    rts

player_move:
    lda #0
    sta pl_frame
    lda joy
    and #(JOY_LEFT | JOY_RIGHT)
    cmp #JOY_LEFT
    bne !right_art+
    inc pl_frame
    bne !art_done+
!right_art:
    cmp #JOY_RIGHT
    bne !art_done+
    lda #2
    sta pl_frame
!art_done:
    lda joy
    and #JOY_UP
    beq !+
    lda pl_y
    sec
    sbc #PL_SPEED
    bcs !st+
    lda #0
!st:sta pl_y
!:  lda joy
    and #JOY_DOWN
    beq !+
    lda pl_y
    clc
    adc #PL_SPEED
    cmp #PL_MAX_Y+1
    bcc !st+
    lda #PL_MAX_Y
!st:sta pl_y
!:  lda joy
    and #JOY_LEFT
    beq !+
    sec
    lda pl_x
    sbc #PL_SPEED
    sta pl_x
    lda pl_x+1
    sbc #0
    sta pl_x+1
    bpl !+
    lda #0
    sta pl_x
    sta pl_x+1
!:  lda joy
    and #JOY_RIGHT
    beq !+
    clc
    lda pl_x
    adc #PL_SPEED
    sta pl_x
    lda pl_x+1
    adc #0
    sta pl_x+1
    beq !+
    lda pl_x
    cmp #<PL_MAX_X
    bcc !+
    lda #<PL_MAX_X
    sta pl_x
!:
    // fire: two shots every FIRE_RATE frames while the button is held
    lda pl_cd
    beq !+
    dec pl_cd
!:  lda joy
    and #JOY_FIRE
    beq !done+
    lda pl_cd
    bne !done+
    lda #FIRE_RATE
    sta pl_cd
    lda #2                      // left gun: x + 2
    jsr fire_shot
    lda #14                     // right gun: x + 14
    jsr fire_shot
!done:
    rts

// spawn a player shot at pl_x + A, pl_y - 4
fire_shot:
    clc
    adc pl_x
    sta sp_x
    lda pl_x+1
    adc #0
    sta sp_x+1
    sec
    lda pl_y
    sbc #4
    sta sp_y
    lda #0
    sbc #0
    sta sp_y+1
    ldx #SHOT_FIRST
    lda #SHOT_END
    sta ob_end
    jsr alloc_slot
    bcs !+
    lda #T_PSHOT
    jsr init_slot
    lda #FR_PBULLET
    sta obj_fr,x
!:  rts

player_update_sprites:
    clc
    lda pl_x
    adc #SPR_XOFS
    sta VIC_SPR0X
    lda pl_x+1
    adc #0
    sta tmp                     // bit 0 = sprite 0 x msb
    clc
    lda pl_x
    adc #SPR_XOFS + 16
    sta VIC_SPR1X
    lda pl_x+1
    adc #0
    asl
    ora tmp                     // bit 1 = sprite 1 x msb
    sta VIC_SPRXMSB
    clc
    lda pl_y
    adc #SPR_YOFS
    sta VIC_SPR0Y
    sta VIC_SPR1Y
    .if (PLAYER_FRAMES > 1) {
        // Only called in vblank, or with sprites disabled during init.
        lda pl_frame
        cmp pl_drawn_frame
        beq !art_done+
        sta pl_drawn_frame
        asl                       // 512 bytes per pair, bank-0 source
        clc
        adc #>sprite_data
        sta job_player_frame+DMA_SRC+1
        RunDma(job_player_frame)
    !art_done:
    }
    rts

pl_frame:       .byte 0            // 0 normal, 1 left, 2 right
pl_drawn_frame: .byte 0
job_player_frame: DmaJob(DMA_CMD_COPY, sprite_data, SPRITE_ADDR, $200)

.align 16
SPRPTR_TABLE: .fill 16, 0       // 16-bit sprite pointer table (inside the program, not in BASIC's RAM)

