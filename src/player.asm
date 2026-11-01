// ----------------------------------------------------------------------------
// Player: two 16-colour hardware sprites (32x24), joystick port 2,
// shield (hit points), invulnerability after a hit, death and restart.
// ----------------------------------------------------------------------------
.label pl_x      = $50    // 16 bit, 0..PL_MAX_X (playfield coordinates, left edge of the plane)
.label pl_y      = $52    // 0..PL_MAX_Y
.label pl_cd     = $53    // fire cooldown
.label pl_shield = $54    // 0..SHIELD_MAX
.label pl_inv    = $55    // invulnerability frames left (sprites blink)
.label pl_state  = $56    // 0 = flying, 1 = destroyed (waiting for restart)
.label pl_timer  = $57
.label pl_frame  = $58    // sprite frame pair 0..5
.label pl_lives  = $67    // lives left including the current one
.label pl_anim   = $70    // exhaust animation counter 0-11

.const PL_W     = 32
.const PL_H     = 24
.const PL_MAX_X = 320 - PL_W
.const PL_MAX_Y = 200 - PL_H
.const PL_SPEED = 2
.const FIRE_RATE = 6
.const SPR_XOFS = 24      // VIC-II sprite coordinates of the playfield's top left pixel
.const SPR_YOFS = 50
.const INV_FRAMES = 50    // 1 s invulnerable after a hit
.const RESTART_FRAMES = 150    // 3 s after being destroyed
.const START_LIVES = 3
// player hit box relative to pl_x/pl_y (the plane is narrower than its 32x24 canvas)
.label PL_HIT_CX = 16
.label PL_HIT_CY = 12
.label PL_HIT_HW = 9
.label PL_HIT_HH = 9

player_init:
    lda #<SPRPTR_TABLE
    sta VIC_SPRPTR
    lda #>SPRPTR_TABLE
    sta VIC_SPRPTR+1
    lda #$80                    // table in bank 0, 16-bit pointers
    sta VIC_SPRPTR+2
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
// new game: three lives, then the first plane
player_new_game:
    lda #START_LIVES
    sta pl_lives
    jsr hud_score_changed       // the lives counter is part of the score box
// a new plane: full shield, centre bottom, briefly invulnerable
player_spawn:
    lda #0
    sta pl_cd
    sta pl_state
    lda #PLAYER_STRAIGHT
    sta pl_frame
    lda #INV_FRAMES
    sta pl_inv
    lda #SHIELD_MAX
    sta pl_shield
    jsr hud_shield_changed
    lda #<(160 - PL_W/2)
    sta pl_x
    lda #>(160 - PL_W/2)
    sta pl_x+1
    lda #150
    sta pl_y
    jmp player_update_sprites

player_move:
    lda pl_state
    beq !alive+
    dec pl_timer                // destroyed: wait, then the next plane or a new game
    bne !+
    lda pl_lives
    bne player_spawn
    jmp game_restart
!:  rts
!alive:
    lda pl_inv
    beq !+
    dec pl_inv
!:  // sprite frame: 3 = banking left, 5 = right, otherwise PLAYER_STRAIGHT
    lda joy
    and #(JOY_LEFT | JOY_RIGHT)
    cmp #JOY_LEFT
    bne !+
    lda #3
    bne !set+
!:  cmp #JOY_RIGHT
    bne !+
    lda #5
    bne !set+
!:  inc pl_anim                 // straight: exhaust animation, frames 0-2, 4 frames each
    lda pl_anim
    cmp #12
    bcc !+
    lda #0
    sta pl_anim
!:  lsr
    lsr
!set:
    sta pl_frame
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
    lda #4                      // left gun
    jsr fire_shot
    lda #12                     // right gun
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
    lda #FR_PSHOT0
    sta obj_fr,x
!:  rts

// A = damage. Ignored while invulnerable or destroyed.
player_damage:
    ldy pl_state
    bne !no+
    ldy pl_inv
    bne !no+
    sta tmp
    lda pl_shield
    sec
    sbc tmp
    bcs !+
    lda #0
!:  sta pl_shield
    jsr hud_shield_changed
    lda pl_shield
    beq player_destroyed
    lda #INV_FRAMES
    sta pl_inv
!no:
    rts

player_destroyed:
    dec pl_lives
    jsr hud_score_changed
    lda #1
    sta pl_state
    lda #RESTART_FRAMES
    sta pl_timer
    // big explosion centred on the plane (32x32 frame)
    sec
    lda pl_x
    sbc #0
    sta sp_x
    lda pl_x+1
    sbc #0
    sta sp_x+1
    sec
    lda pl_y
    sbc #4
    sta sp_y
    lda #0
    sbc #0
    sta sp_y+1
    lda #FR_EX32_0
    jmp spawn_explosion

// A = shield points (bonus pickup)
player_heal:
    clc
    adc pl_shield
    cmp #SHIELD_MAX+1
    bcc !+
    lda #SHIELD_MAX
!:  sta pl_shield
    jmp hud_shield_changed

// called during the vertical blank
player_update_sprites:
    lda pl_state                // hidden while destroyed, blinking while invulnerable
    bne !off+
    lda pl_inv
    and #4
    beq !on+
!off:
    lda #0
    sta VIC_SPREN
    rts
!on:
    lda #%00000011
    sta VIC_SPREN
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
    // all six frame pairs are resident at SPRITE_ADDR: only the pointers change
    lda pl_frame
    asl
    asl
    asl                         // 8 pointer units (512 bytes) per pair
    clc
    adc #<SPRITE_PTR0
    sta SPRPTR_TABLE
    adc #4
    sta SPRPTR_TABLE+2
    lda #>SPRITE_PTR0
    sta SPRPTR_TABLE+1
    sta SPRPTR_TABLE+3
    rts

.align 16
SPRPTR_TABLE: .fill 16, 0       // 16-bit sprite pointer table (inside the program, not in BASIC's RAM)
.errorif ((<SPRITE_PTR0) + 6*8 > 256), "player sprite pointers must not cross a 256 boundary"
