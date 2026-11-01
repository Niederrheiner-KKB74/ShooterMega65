// ----------------------------------------------------------------------------
// Object system (structure of arrays). All moving objects except the player are
// RRB pixies. Slot ranges also define the draw order (later = on top):
//   0-9 ground objects, 10-29 air objects (+ explosions, bonus items), 30-47 shots.
// Every object has a kind; per-kind tables below define frames, hit points,
// damage to the player, points, explosion size, weapon and bonus drops.
// ----------------------------------------------------------------------------
.const MAXOBJ       = 48
.const GROUND_FIRST = 0
.const GROUND_END   = 10
.const AIR_FIRST    = 10
.const AIR_END      = 30
.const SHOT_FIRST   = 30
.const SHOT_END     = 48

.const T_NONE  = 0
.const T_PSHOT = 1
.const T_AIR   = 2
.const T_TANK  = 3
.const T_ESHOT = 4
.const T_EXPL  = 5
.const T_BONUS = 6

.const K_FIGHTER  = 0
.const K_BOMBER   = 1
.const K_HELI     = 2
.const K_ARMOURED = 3
.const K_TANK     = 4
.const K_SHOT_RED = 5
.const K_SHOT_FIRE = 6
.const K_ROCKET   = 7
.const K_BONUS    = 8

.const BONUS_SHIELD = 16          // shield points per bonus item

//                    fighter      bomber        heli       armoured       tank       red  fire  rocket bonus
kind_frame: .byte FR_FIGHTER0, FR_BOMBER0, FR_HELI0, FR_ARMOURED0, FR_TANK, FR_ESHOT_RED, FR_ESHOT_FIRE, FR_ROCKET, FR_BONUS
kind_hp:    .byte 1,  5,  2,  8,  2
kind_dmg:   .byte 12, 20, 12, 24, 0,  6, 10, 14, 0    // shield points lost on contact
kind_pts_lo:.byte $00,$00,$50,$00,$00                 // BCD points
kind_pts_hi:.byte $01,$03,$01,$05,$02                 // fighter 100, bomber 300, heli 150, armoured 500, tank 200
kind_big:   .byte 0,  1,  0,  1,  0                   // 32x32 explosion
kind_drop:  .byte 0,  0,  0,  1,  0                   // always leaves a bonus item
kind_shot:  .byte K_SHOT_RED, K_SHOT_FIRE, K_SHOT_RED, K_SHOT_FIRE, K_ROCKET
kind_fire:  .byte 3,  5,  3,  6,  2                   // firing chance per frame (n/256)
shot_speed: .byte 2,  3,  3                           // red, fire, rocket (px/frame)
wave_size:  .byte 6,  3,  6,  3                       // planes per formation
wave_gap:   .byte 24, 40, 24, 40                      // vertical spacing in a formation

.label ob_i     = $40                // current object
.label ob_end   = $41
.label wave_timer = $42
.label tank_timer = $43
.label ko_flags = $44                // kill_obj: bit 0 = award points
.label ko_drop  = $45
.label sp_x     = $46                // 16 bit spawn position
.label sp_y     = $48                // 16 bit
.label wave_n   = $4a
.label wave_x   = $4b
.label cs_s     = $4c
.label cs_e     = $4d
.label oc_x     = $4e                // 16 bit object centre (collisions)
.label oc_y     = $6a                // 16 bit
.label pc_x     = $6c                // 16 bit player centre
.label pc_y     = $6e                // 16 bit

obj_type: .fill MAXOBJ, 0
obj_kind: .fill MAXOBJ, 0
obj_xl:   .fill MAXOBJ, 0
obj_xh:   .fill MAXOBJ, 0
obj_yl:   .fill MAXOBJ, 0
obj_yh:   .fill MAXOBJ, 0
obj_fr:   .fill MAXOBJ, 0
obj_t:    .fill MAXOBJ, 0
obj_a:    .fill MAXOBJ, 0
obj_b:    .fill MAXOBJ, 0
obj_hp:   .fill MAXOBJ, 0
obj_wave: .fill MAXOBJ, 0
obj_base: .fill MAXOBJ, 0            // first animation frame
wave_kind:  .byte 0                  // fighter, bomber, helicopter, armoured plane
wave_seq:   .byte 0                  // formation id 0..3
wave_kills: .fill 4, 0
wave_count: .fill 4, 0

objects_init:
    ldx #MAXOBJ-1
    lda #0
!:  sta obj_type,x
    dex
    bpl !-
    sta wave_kind
    sta wave_seq
    lda #40
    sta wave_timer
    lda #20
    sta tank_timer
    rts

game_restart:
    jsr objects_init
    jsr hud_reset
    jmp player_reset

// Find a free slot in [X, ob_end). Returns carry clear + X = slot, or carry set.
alloc_slot:
!:  lda obj_type,x
    beq !found+
    inx
    cpx ob_end
    bne !-
    sec
    rts
!found:
    clc
    rts

// Initialise slot X: type A, position sp_x/sp_y, everything else 0.
init_slot:
    sta obj_type,x
    lda sp_x
    sta obj_xl,x
    lda sp_x+1
    sta obj_xh,x
    lda sp_y
    sta obj_yl,x
    lda sp_y+1
    sta obj_yh,x
    lda #0
    sta obj_t,x
    sta obj_a,x
    sta obj_b,x
    sta obj_hp,x
    sta obj_kind,x
    rts

// Slot X gets kind Y: frame, animation base and hit points from the tables.
set_kind:
    tya
    sta obj_kind,x
    lda kind_frame,y
    sta obj_fr,x
    sta obj_base,x
    cpy #K_TANK+1
    bcs !+
    lda kind_hp,y
    sta obj_hp,x
!:  rts

// ---------------------------------------------------------------- spawning
spawn_update:
    dec wave_timer
    beq !+
    jmp !no_wave+
!:  lda #170
    sta wave_timer
    // a formation snaking down the screen
    jsr random
    and #127
    clc
    adc #48
    sta wave_x
    ldy wave_kind
    ldx wave_seq
    lda #0
    sta wave_kills,x
    lda wave_size,y
    sta wave_count,x
    lda #0
    sta wave_n
    lda #<-32
    sta sp_y
    lda #>-32
    sta sp_y+1
!w: lda #0
    sta sp_x
    sta sp_x+1
    ldx #AIR_FIRST
    lda #AIR_END
    sta ob_end
    jsr alloc_slot
    bcs !full+
    lda #T_AIR
    jsr init_slot
    ldy wave_kind
    jsr set_kind
    lda wave_x
    sta obj_a,x
    lda wave_n
    asl
    asl
    asl
    asl
    sta obj_b,x                 // phase
    lda wave_seq
    sta obj_wave,x
    sec                         // next plane further up
    lda sp_y
    ldy wave_kind
    sbc wave_gap,y
    sta sp_y
    lda sp_y+1
    sbc #0
    sta sp_y+1
    inc wave_n
    lda wave_n
    ldy wave_kind
    cmp wave_size,y
    bne !w-
    jmp !next+
!full:                          // not all planes fitted: the formation cannot be completed
    ldx wave_seq
    lda #$ff
    sta wave_count,x
!next:
    lda wave_kind
    clc
    adc #1
    and #3
    sta wave_kind
    lda wave_seq
    clc
    adc #1
    and #3
    sta wave_seq
!no_wave:
    dec tank_timer
    bne !no_tank+
    lda #90
    sta tank_timer
    jsr random
    sta sp_x                    // x = 16 + random (0..255)
    lda #0
    sta sp_x+1
    clc
    lda sp_x
    adc #16
    sta sp_x
    bcc !+
    inc sp_x+1
!:  lda #<-16
    sta sp_y
    lda #>-16
    sta sp_y+1
    ldx #GROUND_FIRST
    lda #GROUND_END
    sta ob_end
    jsr alloc_slot
    bcs !no_tank+
    lda #T_TANK
    jsr init_slot
    ldy #K_TANK
    jsr set_kind
    jsr random
    and #2
    sec
    sbc #1                      // +1 or -1
    sta obj_b,x
!no_tank:
    rts

// object X fires its weapon: shot appears at its centre, aimed horizontally at the player
spawn_eshot:
    ldy obj_fr,x
    clc
    lda obj_xl,x
    adc frame_hit_cx,y
    sta sp_x
    lda obj_xh,x
    adc #0
    sta sp_x+1
    sec                         // shot frames are 16 wide: centre - 8
    lda sp_x
    sbc #8
    sta sp_x
    lda sp_x+1
    sbc #0
    sta sp_x+1
    clc
    lda obj_yl,x
    adc frame_hit_cy,y
    sta sp_y
    lda obj_yh,x
    adc #0
    sta sp_y+1
    ldy obj_kind,x
    lda kind_shot,y
    sta es_kind
    stx ob_i
    ldx #SHOT_FIRST
    lda #SHOT_END
    sta ob_end
    jsr alloc_slot
    bcs !full+
    lda #T_ESHOT
    jsr init_slot
    ldy es_kind
    jsr set_kind
    lda shot_speed-K_SHOT_RED,y
    sta obj_b,x
    // dx = sign(player centre - shot centre)
    clc
    lda pl_x
    adc #8
    sta tmp
    lda pl_x+1
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc sp_x
    sta tmp
    lda tmp+1
    sbc sp_x+1
    bmi !left+
    ora tmp
    beq !st+                    // dx = 0
    lda #1
    bne !st+
!left:
    lda #$ff
!st:
    sta obj_a,x
!full:
    ldx ob_i
    rts
es_kind: .byte 0

// explosion with first frame A at sp_x/sp_y (air range, does not scroll)
spawn_explosion:
    sta se_frame
    ldx #AIR_FIRST
    lda #AIR_END
    sta ob_end
    jsr alloc_slot
    bcs !+
    lda #T_EXPL
    jsr init_slot
    lda se_frame
    sta obj_fr,x
    sta obj_base,x
!:  rts
se_frame: .byte 0

// ---------------------------------------------------------------- destroying objects
// Object X is destroyed: points (if ko_flags bit 0), formation bonus, explosion.
// X is preserved.
kill_obj:
    stx ko_i
    lda #0
    sta ko_drop
    ldy obj_kind,x
    lda kind_drop,y
    sta ko_drop
    lda ko_flags
    and #1
    beq !nopts+
    lda kind_pts_hi,y
    tax
    lda kind_pts_lo,y
    jsr score_add
    ldx ko_i
    // formation complete?
    lda obj_type,x
    cmp #T_AIR
    bne !nopts+
    ldy obj_wave,x
    lda wave_kills,y
    clc
    adc #1
    sta wave_kills,y
    cmp wave_count,y
    bne !nopts+
    lda #1
    sta ko_drop
!nopts:
    // centre of the object
    ldy obj_fr,x
    clc
    lda obj_xl,x
    adc frame_hit_cx,y
    sta oc_x
    lda obj_xh,x
    adc #0
    sta oc_x+1
    clc
    lda obj_yl,x
    adc frame_hit_cy,y
    sta oc_y
    lda obj_yh,x
    adc #0
    sta oc_y+1
    // explosion: 32x32 for big kinds, else 16x16, centred
    ldy obj_kind,x
    lda kind_big,y
    beq !small+
    lda #16
    ldy #FR_EX32_0
    bne !ex+
!small:
    lda #8
    ldy #FR_EX16_0
!ex:
    sta tmp
    tya
    sta obj_fr,x
    sta obj_base,x
    sec
    lda oc_x
    sbc tmp
    sta obj_xl,x
    lda oc_x+1
    sbc #0
    sta obj_xh,x
    sec
    lda oc_y
    sbc tmp
    sta obj_yl,x
    lda oc_y+1
    sbc #0
    sta obj_yh,x
    lda obj_type,x
    cmp #T_TANK                 // ground explosions keep moving with the landscape
    lda #0
    rol
    sta obj_a,x
    lda #T_EXPL
    sta obj_type,x
    lda #0
    sta obj_t,x
    // bonus item at the centre
    lda ko_drop
    beq !done+
    sec
    lda oc_x
    sbc #8
    sta sp_x
    lda oc_x+1
    sbc #0
    sta sp_x+1
    sec
    lda oc_y
    sbc #8
    sta sp_y
    lda oc_y+1
    sbc #0
    sta sp_y+1
    ldx #AIR_FIRST
    lda #AIR_END
    sta ob_end
    jsr alloc_slot
    bcs !done+
    lda #T_BONUS
    jsr init_slot
    ldy #K_BONUS
    jsr set_kind
!done:
    ldx ko_i
    rts
ko_i: .byte 0

// ---------------------------------------------------------------- update
objects_update:
    ldx #0
!:  lda obj_type,x
    beq !next+
    stx ob_i
    asl
    tay
    lda upd_tab-2,y
    sta upd_call+1
    lda upd_tab-1,y
    sta upd_call+2
upd_call:
    jsr $ffff
    ldx ob_i
!next:
    inx
    cpx #MAXOBJ
    bne !-
    rts

upd_tab:
    .word upd_pshot, upd_air, upd_tank, upd_eshot, upd_expl, upd_bonus

free_x:
    lda #T_NONE
    sta obj_type,x
    rts

upd_pshot:
    sec
    lda obj_yl,x
    sbc #6
    sta obj_yl,x
    lda obj_yh,x
    sbc #0
    sta obj_yh,x
    bpl !+
    lda obj_yl,x
    cmp #<-16
    bcs !+
    jmp free_x
!:  rts

// generic "y += n" (n = 0..127) and remove when below the screen
move_down:
    clc
    adc obj_yl,x
    sta obj_yl,x
    lda obj_yh,x
    adc #0
    sta obj_yh,x
    bmi !+
    beq !+
    jmp free_x                  // y >= 256
!:  rts

upd_air:
    inc obj_t,x
    lda obj_t,x
    and #7
    bne !anim_done+
    inc obj_fr,x
    lda obj_base,x
    clc
    adc #AIR_ANIM_FRAMES
    cmp obj_fr,x
    bne !anim_done+
    lda obj_base,x
    sta obj_fr,x
!anim_done:
    lda #1
    jsr move_down
    lda obj_type,x
    beq !gone+
    // x = a + 16 + sin[(2t + b) & 255]
    lda obj_t,x
    asl
    clc
    adc obj_b,x
    tay
    lda sin_tab,y
    sta tmp
    ldy #0
    bit tmp
    bpl !+
    dey
!:  sty tmp+1
    clc
    lda obj_a,x
    adc #16
    sta obj_xl,x
    lda #0
    adc #0
    sta obj_xh,x
    clc
    lda obj_xl,x
    adc tmp
    sta obj_xl,x
    lda obj_xh,x
    adc tmp+1
    sta obj_xh,x
    jmp maybe_fire
!gone:
    rts

// fire with the kind's probability while on screen (y 8..150)
maybe_fire:
    lda pl_state                // no shots at a destroyed player
    bne !no+
    lda obj_yh,x
    bne !no+
    lda obj_yl,x
    cmp #8
    bcc !no+
    cmp #150
    bcs !no+
    jsr random
    ldy obj_kind,x
    cmp kind_fire,y
    bcs !no+
    jmp spawn_eshot
!no:
    rts

upd_tank:
    lda scroll_delta
    jsr move_down
    lda obj_type,x
    beq !gone+
    inc obj_t,x
    lda obj_t,x
    and #3
    bne !fire+
    // x += b, bounce between 8 and 290
    lda obj_b,x
    bmi !l+
    inc obj_xl,x
    bne !+
    inc obj_xh,x
!:  lda obj_xh,x
    beq !fire+
    lda obj_xl,x
    cmp #<290
    bcc !fire+
    lda #$ff
    sta obj_b,x
    bne !fire+
!l: lda obj_xl,x
    bne !+
    dec obj_xh,x
!:  dec obj_xl,x
    lda obj_xh,x
    bne !fire+
    lda obj_xl,x
    cmp #8
    bcs !fire+
    lda #1
    sta obj_b,x
!fire:
    jmp maybe_fire
!gone:
    rts

upd_eshot:
    lda obj_b,x                 // speed
    jsr move_down
    lda obj_type,x
    beq !gone+
    lda obj_a,x                 // x += dx (-1/0/+1)
    beq !gone+
    bmi !l+
    inc obj_xl,x
    bne !chk+
    inc obj_xh,x
    jmp !chk+
!l: lda obj_xl,x
    bne !+
    dec obj_xh,x
!:  dec obj_xl,x
!chk:
    lda obj_xh,x
    bmi !free+
    cmp #2
    bcs !free+
!gone:
    rts
!free:
    jmp free_x

upd_expl:
    lda obj_a,x                 // ground explosions move with the landscape
    beq !+
    lda scroll_delta
    jsr move_down
    lda obj_type,x
    beq !gone+
!:  inc obj_t,x
    lda obj_t,x
    cmp #18                     // 6 frames x 3
    bcs !free+
    ldy #0
!div:
    cmp #3
    bcc !+
    sbc #3
    iny
    bne !div-
!:  tya
    clc
    adc obj_base,x
    sta obj_fr,x
!gone:
    rts
!free:
    jmp free_x

upd_bonus:                      // drifts down slowly
    inc obj_t,x
    lda obj_t,x
    and #1
    jmp move_down

// ---------------------------------------------------------------- collisions
// Player shots against air enemies and tanks.
collide_shots:
    ldx #SHOT_FIRST
!shot:
    stx cs_s
    lda obj_type,x
    cmp #T_PSHOT
    beq !+
    jmp !nexts+
!:  ldy #GROUND_FIRST
!en:
    lda obj_type,y
    cmp #T_AIR
    beq !test+
    cmp #T_TANK
    beq !test+
    jmp !nexte+
!test:
    // compare the shot centre (x+8, y+4) with the target's visible rectangle
    sty cs_e
    lda obj_fr,y
    tay
    lda frame_hit_cx,y
    sta hit_centre
    lda frame_hit_halfw,y
    clc
    adc #2
    sta hit_limit
    ldy cs_e
    clc
    lda obj_xl,x
    adc #8
    sta tmp
    lda obj_xh,x
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc obj_xl,y
    sta tmp
    lda tmp+1
    sbc obj_xh,y
    sta tmp+1
    jsr hit_axis
    bcc !+
    jmp !nexte+
!:  lda obj_fr,y
    tay
    lda frame_hit_cy,y
    sta hit_centre
    lda frame_hit_halfh,y
    clc
    adc #2
    sta hit_limit
    ldy cs_e
    clc
    lda obj_yl,x
    adc #4
    sta tmp
    lda obj_yh,x
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc obj_yl,y
    sta tmp
    lda tmp+1
    sbc obj_yh,y
    sta tmp+1
    jsr hit_axis
    bcc !+
    jmp !nexte+
!:  // hit: the shot disappears, the target loses one hit point
    lda #T_NONE
    sta obj_type,x
    lda obj_hp,y
    sec
    sbc #1
    sta obj_hp,y
    bne !nexts+
    tya
    tax
    lda #1                      // destroyed by the player: points
    sta ko_flags
    jsr kill_obj
    jmp !nexts+
!nexte:
    iny
    cpy #AIR_END
    beq !nexts+
    jmp !en-
!nexts:
    ldx cs_s
    inx
    cpx #SHOT_END
    beq !done+
    jmp !shot-
!done:
    rts

// tmp = position - target origin. Carry clear if |tmp - hit_centre| < hit_limit.
// X/Y survive this helper.
hit_axis:
    sec
    lda tmp
    sbc hit_centre
    sta tmp
    lda tmp+1
    sbc #0
    sta tmp+1
    bpl !positive+
    sec
    lda #0
    sbc tmp
    sta tmp
    lda #0
    sbc tmp+1
    sta tmp+1
!positive:
    lda tmp+1
    bne !no+
    lda tmp
    cmp hit_limit
    rts
!no:
    sec
    rts

hit_centre: .byte 0
hit_limit:  .byte 0

// Player against enemy planes, enemy shots and bonus items.
collide_player:
    lda pl_state
    beq !+
    rts
!:  clc
    lda pl_x
    adc #PL_HIT_CX
    sta pc_x
    lda pl_x+1
    adc #0
    sta pc_x+1
    lda pl_y
    clc
    adc #PL_HIT_CY
    sta pc_y
    lda #0
    adc #0
    sta pc_y+1
    ldx #AIR_FIRST
!obj:
    lda obj_type,x
    cmp #T_AIR
    beq !test+
    cmp #T_ESHOT
    beq !test+
    cmp #T_BONUS
    beq !test+
    jmp !next+
!test:
    ldy obj_fr,x
    // |object centre x - player centre x| < halfw + PL_HIT_HW
    lda frame_hit_cx,y
    sta hit_centre
    lda frame_hit_halfw,y
    clc
    adc #PL_HIT_HW
    sta hit_limit
    sec
    lda pc_x
    sbc obj_xl,x
    sta tmp
    lda pc_x+1
    sbc obj_xh,x
    sta tmp+1
    jsr hit_axis
    bcs !next+
    ldy obj_fr,x
    lda frame_hit_cy,y
    sta hit_centre
    lda frame_hit_halfh,y
    clc
    adc #PL_HIT_HH
    sta hit_limit
    sec
    lda pc_y
    sbc obj_yl,x
    sta tmp
    lda pc_y+1
    sbc obj_yh,x
    sta tmp+1
    jsr hit_axis
    bcs !next+
    // contact
    lda obj_type,x
    cmp #T_BONUS
    bne !harm+
    jsr free_x
    stx cs_s
    ldx #$02                    // 250 points
    lda #$50
    jsr score_add
    lda #BONUS_SHIELD
    jsr player_heal
    ldx cs_s
    jmp !next+
!harm:
    ldy pl_inv                  // invulnerable: no damage, nothing destroyed
    bne !next+
    ldy obj_kind,x
    lda kind_dmg,y
    pha
    lda obj_type,x
    cmp #T_ESHOT
    bne !plane+
    jsr free_x
    jmp !dmg+
!plane:
    lda #0                      // collision: the plane is destroyed, no points
    sta ko_flags
    jsr kill_obj
!dmg:
    stx cs_s
    pla
    jsr player_damage
    ldx cs_s
    lda pl_state
    beq !next+
    rts                         // destroyed: stop testing
!next:
    inx
    cpx #SHOT_END
    beq !+
    jmp !obj-
!:  rts

// ---------------------------------------------------------------- drawing
objects_draw:
    ldx #0
!:  lda obj_type,x
    beq !next+
    stx ob_i
    lda obj_xl,x
    sta px_x
    lda obj_xh,x
    sta px_x+1
    lda obj_yl,x
    sta px_y
    lda obj_yh,x
    sta px_y+1
    ldy obj_fr,x
    lda frame_pal,y
    sta px_pal
    lda obj_fr,x
    jsr pixie_draw
    ldx ob_i
!next:
    inx
    cpx #MAXOBJ
    bne !-
    jmp hud_draw
