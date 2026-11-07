// ----------------------------------------------------------------------------
// Special weapons (Stage 4): the items bought in the shop (shop.asm).
//
//   Bomb (space):            destroys every enemy on the screen (points and capsules as
//                            if shot down), removes enemy shots, short light flash.
//   Invulnerability (S):     INV_LONG frames (10 s) without damage; a shimmering ring
//                            (hardware sprites 2-4, 48x24, behind the plane) shows it and
//                            blinks during the last 2 seconds.
//   Homing missile:          starts with the guns (fire) when no missile is under way and an
//                            enemy is visible; steers towards a random visible enemy and does
//                            pl_power damage (collide_shots treats it like a player shot).
//                            8 frames FR_MS0..7 (up, then clockwise) follow the flight direction.
// ----------------------------------------------------------------------------
// constants: layout.asm (RING_ADDR, INV_*, MS_*, FLASH_FRAMES), objects.asm (T_MISSILE)

.errorif (RING_ADDR < SPRITE_ADDR + PLAYER_FRAMES * $200), "ring sprites overlap the player sprites"
.errorif (RING_ADDR + 3 * $100 > $060000), "ring sprites outside bank 5"

.function nswap(v) { .return ((v & 15) << 4) | (v >> 4) }   // palette registers hold swapped nibbles
.const FLASH_RGB = nswap(230)

inv_timer:  .word 0
inv_req:    .byte 0
bomb_flash: .byte 0
ring_phase: .byte 0
ring_tick:  .byte 0
ms_slot:    .byte 0                 // slot of the last missile

// new game / new plane: nothing active
special_reset:
    lda #0
    sta inv_timer
    sta inv_timer+1
    sta inv_req
    sta special_req
    rts

// once per frame in the main loop, after read_keys
special_update:
    lda inv_timer               // count the invulnerability down
    ora inv_timer+1
    beq !+
    lda inv_timer
    bne !dec+
    dec inv_timer+1
!dec:
    dec inv_timer
!:  lda pl_state                // destroyed: requests are dropped
    beq !+
    jmp special_reset_reqs
!:  lda special_req             // space: bomb
    beq !inv+
    lda #0
    sta special_req
    lda bomb_count
    beq !inv+
    dec bomb_count
    jsr hud_score_changed
    jsr bomb_fire
!inv:
    lda inv_req                 // S: invulnerability (not while it is running)
    beq !done+
    lda #0
    sta inv_req
    lda inv_count
    beq !done+
    lda inv_timer
    ora inv_timer+1
    bne !done+
    dec inv_count
    lda #SFX_INVULNERABLE
    jsr sfx_play
    jsr hud_score_changed
    lda #<INV_LONG
    sta inv_timer
    lda #>INV_LONG
    sta inv_timer+1
!done:
    rts

special_reset_reqs:
    lda #0
    sta special_req
    sta inv_req
    rts

// A = 0 if the player can be hurt (no hit invulnerability, no bought invulnerability)
player_vulnerable:
    lda pl_inv
    ora inv_timer
    ora inv_timer+1
    rts

// ---------------------------------------------------------------- bomb
bomb_fire:
    ldx #GROUND_FIRST
!obj:
    lda obj_type,x
    cmp #T_BOSS
    bne !+
    jsr boss_bomb_part          // boss parts lose hit points instead
    jmp !next+
!:  cmp #T_GUN                 // ground guns become wrecks
    bne !+
    jsr enemy_visible
    bcs !next+
    jsr gun_down                // keeps X
    jmp !next+
!:  cmp #T_AIR
    beq !enemy+
    cmp #T_TANK
    bne !next+
!enemy:
    jsr enemy_visible
    bcs !next+
    lda #1                      // points and capsules as if shot down
    sta ko_flags
    jsr kill_obj                // keeps X
!next:
    inx
    cpx #AIR_END
    bne !obj-
    ldx #SHOT_FIRST             // enemy shots disappear
!:  lda obj_type,x
    cmp #T_ESHOT
    bne !+
    lda #T_NONE
    sta obj_type,x
!:  inx
    cpx #SHOT_END
    bne !--
    jsr gd_bomb                 // buildings on the screen (ground.asm)
    lda #FLASH_FRAMES
    sta bomb_flash
    lda #SFX_BOMB
    jmp sfx_play

// object X: carry clear if it is an enemy that is (at least partly) on the screen
enemy_visible:
    lda obj_type,x
    cmp #T_BOSS
    bne !nb+
    lda obj_b,x                 // boss part: only while it can be hit
    beq !no+
    clc
    rts
!nb:
    cmp #T_GUN                  // gun: not as a wreck
    bne !+
    lda obj_b,x
    beq !no+
!:
    cmp #T_AIR
    bne !+
    lda obj_dly,x               // formation member still waiting above the screen
    bne !no+
!:  lda obj_yh,x
    beq !low+
    cmp #$ff
    bne !no+
    lda obj_yl,x                // y = -24 .. -1
    cmp #<-24
    bcc !no+
    clc
    rts
!low:
    lda obj_yl,x
    cmp #200
    rts                         // carry clear if y < 200
!no:
    sec
    rts

// ---------------------------------------------------------------- missile
// called by player_move when the guns fire
missile_try:
    lda has_missile
    beq !no+
    ldx ms_slot
    lda obj_type,x
    cmp #T_MISSILE
    beq !no+                    // one missile at a time
    jsr pick_target
    bcs !no+
    sty ms_target
    clc
    lda pl_x
    adc #8
    sta sp_x
    lda pl_x+1
    adc #0
    sta sp_x+1
    sec
    lda pl_y
    sbc #12
    sta sp_y
    lda #0
    sbc #0
    sta sp_y+1
    ldx #SHOT_FIRST
    lda #SHOT_END
    sta ob_end
    jsr alloc_slot
    bcs !no+
    lda #T_MISSILE
    jsr init_slot
    lda #FR_MS0
    sta obj_fr,x
    lda pl_power                // damage (collide_shots)
    sta obj_hp,x
    lda ms_target
    sta obj_a,x
    lda #MS_LIFE
    sta obj_t,x
    stx ms_slot
    lda #SFX_MISSILE
    jsr sfx_play
!no:
    rts
ms_target: .byte 0

// Y = a random visible enemy (carry clear), carry set if there is none
pick_target:
    jsr random
    and #31
    cmp #AIR_END
    bcc !+
    sbc #AIR_END
!:  tax
    lda #AIR_END
    sta pt_n
!:  lda obj_type,x
    cmp #T_AIR
    beq !test+
    cmp #T_BOSS
    beq !test+
    cmp #T_GUN
    beq !test+
    cmp #T_TANK
    bne !next+
!test:
    jsr enemy_visible
    bcc !found+
!next:
    inx
    cpx #AIR_END
    bne !+
    ldx #0
!:  dec pt_n
    bne !--
    sec
    rts
!found:
    txa
    tay
    clc
    rts
pt_n: .byte 0

// object update for T_MISSILE (X = slot)
upd_missile:
    dec obj_t,x
    bne !+
    jmp free_x
!:  ldy obj_a,x                 // target still there?
    lda obj_type,y
    cmp #T_AIR
    beq !chk+
    cmp #T_BOSS
    beq !chk+
    cmp #T_GUN
    beq !chk+
    cmp #T_TANK
    bne !new+
!chk:
    stx ms_self
    tya
    tax
    jsr enemy_visible
    ldx ms_self
    bcc !steer+
!new:
    stx ms_self
    jsr pick_target
    ldx ms_self
    bcc !+
    sec                         // nothing left: straight up, gone above the screen
    lda obj_yl,x
    sbc #4
    sta obj_yl,x
    lda obj_yh,x
    sbc #0
    sta obj_yh,x
    bpl !ok+
    lda obj_yl,x
    cmp #<-16
    bcs !ok+
    jmp free_x
!ok:
    lda #FR_MS0                 // pointing up
    sta obj_fr,x
    rts
!:  tya
    sta obj_a,x
!steer:
    // dx = target centre - missile centre (x + 8, y + 8), each axis at most MS_SPEED
    ldy obj_a,x
    lda obj_fr,y
    sta ms_fr
    sty ms_tgt
    ldy ms_fr
    lda frame_hit_cx,y
    ldy ms_tgt
    clc
    adc obj_xl,y
    sta tmp
    lda obj_xh,y
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc #8
    sta tmp
    lda tmp+1
    sbc #0
    sta tmp+1
    sec
    lda tmp
    sbc obj_xl,x
    sta tmp
    lda tmp+1
    sbc obj_xh,x
    sta tmp+1
    jsr ms_clamp                // A = step (signed)
    sta tmp
    sta ms_sx
    clc
    adc obj_xl,x
    sta obj_xl,x
    lda tmp
    and #$80
    beq !+
    lda #$ff
!:  adc obj_xh,x
    sta obj_xh,x
    ldy ms_fr                   // y axis
    lda frame_hit_cy,y
    ldy ms_tgt
    clc
    adc obj_yl,y
    sta tmp
    lda obj_yh,y
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc #8
    sta tmp
    lda tmp+1
    sbc #0
    sta tmp+1
    sec
    lda tmp
    sbc obj_yl,x
    sta tmp
    lda tmp+1
    sbc obj_yh,x
    sta tmp+1
    jsr ms_clamp
    sta tmp
    sta ms_sy
    clc
    adc obj_yl,x
    sta obj_yl,x
    lda tmp
    and #$80
    beq !+
    lda #$ff
!:  adc obj_yh,x
    sta obj_yh,x
    // fall through: frame for the flight direction

// Missile frame from the step (ms_sx, ms_sy): one of 8 directions (45 degree sectors,
// a component counts when it is at least half the other one). No movement: frame kept.
ms_dir:
    jsr vec_dir
    bmi !keep+
    clc
    adc #FR_MS0
    sta obj_fr,x
!keep:
    rts

// direction of the vector (ms_sx, ms_sy): A = 0 up, 1 up-right … 7 up-left (45 degree sectors,
// a component counts when it is at least half the other one), $ff = no movement. Keeps X.
vec_dir:
    lda ms_sx
    jsr ms_abs
    sta ms_ax
    lda ms_sy
    jsr ms_abs
    sta ms_ay
    ldy #1                      // horizontal: 0 left, 1 none, 2 right
    lda ms_ay
    lsr                         // ignore x if 2*|x| < |y|  <=> |x| < |y|/2 (rounded down)
    cmp ms_ax
    bcs !hz+                    // |y|/2 >= |x|: x is too small... unless both are 0
    lda ms_sx
    bmi !l+
    iny
    bne !hz+
!l: dey
!hz:
    sty ms_h
    ldy #1                      // vertical: 0 up, 1 none, 2 down
    lda ms_ax
    lsr
    cmp ms_ay
    bcs !vt+
    lda ms_sy
    bmi !u+
    iny
    bne !vt+
!u: dey
!vt:
    lda ms_h                    // table index = h * 3 + v
    asl
    adc ms_h
    sty ms_h
    adc ms_h
    tay
    lda ms_dir_tab,y
    rts

ms_abs:
    bpl !+
    eor #$ff
    clc
    adc #1
!:  rts

ms_sx: .byte 0
ms_sy: .byte 0
ms_ax: .byte 0
ms_ay: .byte 0
ms_h:  .byte 0
// h (left/none/right) * 3 + v (up/none/down) -> direction 0 up, 1 up-right ... 7 up-left
ms_dir_tab: .byte 7, 6, 5,   0, $ff, 4,   1, 2, 3
ms_self: .byte 0
ms_tgt:  .byte 0
ms_fr:   .byte 0

// tmp (signed 16 bit) -> A = clamp(tmp, -MS_SPEED, MS_SPEED)
ms_clamp:
    lda tmp+1
    bmi !neg+
    bne !max+
    lda tmp
    cmp #MS_SPEED+1
    bcs !max+
    rts
!max:
    lda #MS_SPEED
    rts
!neg:
    cmp #$ff
    bne !min+
    lda tmp
    cmp #<-MS_SPEED
    bcc !min+
    rts
!min:
    lda #<-MS_SPEED
    rts

// ---------------------------------------------------------------- vertical blank
// after player_update_sprites: ring colours and the bomb flash
special_vblank:
    inc ring_tick
    lda ring_tick
    and #3
    bne !flash+
    ldx ring_phase              // ring: colours move one step every 4 frames
    inx
    cpx #6
    bne !+
    ldx #0
!:  stx ring_phase
    lda #$44                    // edit palette 1 (sprites)
    ora pal_show
    sta VIC_PALSEL
    ldy #1                      // colour index 1-6
!col:
    lda ring_r,x
    sta PAL_RED+$20,y
    sta PAL_RED+$30,y
    sta PAL_RED+$40,y
    lda ring_g,x
    sta PAL_GREEN+$20,y
    sta PAL_GREEN+$30,y
    sta PAL_GREEN+$40,y
    lda ring_b,x
    sta PAL_BLUE+$20,y
    sta PAL_BLUE+$30,y
    sta PAL_BLUE+$40,y
    inx
    cpx #6
    bne !+
    ldx #0
!:  iny
    cpy #7
    bne !col-
    lda #$04
    ora pal_show
    sta VIC_PALSEL
!flash:
    lda bomb_flash
    beq !done+
    dec bomb_flash
    beq !restore+
    cmp #FLASH_FRAMES           // first frame: landscape banks 1-4 light
    bne !done+
    ldx #$3f
    lda #FLASH_RGB
!:  sta PAL_RED+$10,x
    sta PAL_GREEN+$10,x
    sta PAL_BLUE+$10,x
    dex
    bpl !-
!done:
    rts
!restore:
    jmp palette_init

// shimmer: white -> light cyan -> blue -> light cyan (nibble-swapped palette values)
ring_r: .byte nswap(255), nswap(190), nswap(110), nswap(60), nswap(110), nswap(190)
ring_g: .byte nswap(255), nswap(240), nswap(200), nswap(140), nswap(200), nswap(240)
ring_b: .byte nswap(255), nswap(255), nswap(255), nswap(240), nswap(255), nswap(255)
