// ----------------------------------------------------------------------------
// Object system (structure of arrays). All moving objects except the player are
// RRB pixies. Slot ranges also define the draw order (later = on top):
//   0-9 ground objects, 10-29 air objects, 30-47 shots.
// ----------------------------------------------------------------------------
.const MAXOBJ      = 48
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

.const PAL_OBJ = $2f                 // palette bank 2

.label ob_i     = $40                // current object
.label ob_end   = $41
.label wave_timer = $42
.label tank_timer = $43
.label score    = $44                // 16 bit (binary, stage 1)
.label sp_x     = $46                // 16 bit spawn position
.label sp_y     = $48                // 16 bit
.label wave_n   = $4a
.label wave_x   = $4b

obj_type: .fill MAXOBJ, 0
obj_xl:   .fill MAXOBJ, 0
obj_xh:   .fill MAXOBJ, 0
obj_yl:   .fill MAXOBJ, 0
obj_yh:   .fill MAXOBJ, 0
obj_fr:   .fill MAXOBJ, 0
obj_t:    .fill MAXOBJ, 0
obj_a:    .fill MAXOBJ, 0
obj_b:    .fill MAXOBJ, 0
obj_airbase: .fill MAXOBJ, 0    // first frame of the current air animation
wave_kind: .byte 0             // fighter, bomber, helicopter, armoured plane

objects_init:
    ldx #MAXOBJ-1
    lda #0
!:  sta obj_type,x
    dex
    bpl !-
    sta score
    sta score+1
    sta wave_kind
    lda #40
    sta wave_timer
    lda #20
    sta tank_timer
    rts

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
    rts

// ---------------------------------------------------------------- spawning
spawn_update:
    dec wave_timer
    bne !no_wave+
    lda #170
    sta wave_timer
    // a formation of 6 planes snaking down the screen
    jsr random
    and #127
    clc
    adc #48
    sta wave_x
    lda #0
    sta wave_n
!w: lda wave_n
    asl                         // y = -16 - n*22
    asl
    asl
    sta tmp
    lda wave_n
    asl
    asl
    asl
    asl
    clc
    adc tmp                     // n*24
    eor #$ff
    sec
    sbc #15                     // -(n*24) - 16
    sta sp_y
    lda #$ff
    sta sp_y+1
    lda #0
    sta sp_x
    sta sp_x+1
    ldx #AIR_FIRST
    lda #AIR_END
    sta ob_end
    jsr alloc_slot
    bcs !no_wave+
    lda #T_AIR
    jsr init_slot
    lda wave_x
    sta obj_a,x
    lda wave_n
    asl
    asl
    asl
    asl
    sta obj_b,x                 // phase
    ldy wave_kind
    lda air_frame_first,y
    sta obj_fr,x
    sta obj_airbase,x
    inc wave_n
    lda wave_n
    cmp #6
    bne !w-
    inc wave_kind
    lda wave_kind
    and #3
    sta wave_kind
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
    lda #FR_TANK
    sta obj_fr,x
    jsr random
    and #2
    sec
    sbc #1                      // +1 or -1
    sta obj_b,x
!no_tank:
    rts

// spawn an enemy shot at (obj x, obj y + A) of object X, aimed horizontally at the player
spawn_eshot:
    clc
    adc obj_yl,x
    sta sp_y
    lda obj_yh,x
    adc #0
    sta sp_y+1
    lda obj_xl,x
    sta sp_x
    lda obj_xh,x
    sta sp_x+1
    stx ob_i
    ldx #SHOT_FIRST
    lda #SHOT_END
    sta ob_end
    jsr alloc_slot
    bcs !full+
    lda #T_ESHOT
    jsr init_slot
    lda #FR_EBULLET
    sta obj_fr,x
    // dx = sign(player_x + 8 - shot_x)  (player sprite is 32 px wide, shot glyph 16)
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
    .word upd_pshot, upd_air, upd_tank, upd_eshot, upd_expl

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
    lda obj_airbase,x
    clc
    adc #AIR_ANIM_FRAMES
    cmp obj_fr,x
    bne !anim_done+
    lda obj_airbase,x
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
    // maybe fire when on screen (y 8..150)
    lda obj_yh,x
    bne !gone+
    lda obj_yl,x
    cmp #8
    bcc !gone+
    cmp #150
    bcs !gone+
    jsr random
    cmp #3
    bcs !gone+
    lda #12
    jmp spawn_eshot
!gone:
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
    lda obj_yh,x
    bne !gone+
    lda obj_yl,x
    cmp #140
    bcs !gone+
    jsr random
    cmp #2
    bcs !gone+
    lda #8
    jmp spawn_eshot
!gone:
    rts

upd_eshot:
    lda #2
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
    cmp #20
    bcs !free+
    lsr
    lsr
    cmp #4
    bcc !+
    lda #3
!:  clc
    adc #FR_EXPL0
    sta obj_fr,x
!gone:
    rts
!free:
    jmp free_x

// ---------------------------------------------------------------- collisions
// Player shots against air enemies and tanks (bounding boxes, 16-bit signed).
.label cs_s = $4c
.label cs_e = $4d
collide_shots:
    ldx #SHOT_FIRST
!shot:
    stx cs_s
    lda obj_type,x
    cmp #T_PSHOT
    beq !+
    jmp !nexts+
!:
    ldy #GROUND_FIRST
!en:
    lda obj_type,y
    cmp #T_AIR
    beq !test+
    cmp #T_TANK
    beq !test+
    jmp !nexte+
!test:
    // Compare shot centre (x+8,y+4) to the visible target rectangle.
    // NCM padding on 24px targets does not enlarge the hitbox.
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
!:
    lda obj_fr,y
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
!:
    // hit: enemy explodes, shot disappears
    // Keep the existing 16px explosion centred on a 24px/32px canvas target.
    ldx obj_fr,y
    lda frame_hit_cx,x
    sec
    sbc #8
    clc
    adc obj_xl,y
    sta obj_xl,y
    lda obj_xh,y
    adc #0
    sta obj_xh,y
    lda frame_hit_cy,x
    sec
    sbc #8
    clc
    adc obj_yl,y
    sta obj_yl,y
    lda obj_yh,y
    adc #0
    sta obj_yh,y
    ldx cs_s
    lda obj_type,y
    cmp #T_TANK
    lda #0
    rol                         // a = 1 for tanks (scrolls with the ground)
    sta obj_a,y
    lda #T_EXPL
    sta obj_type,y
    lda #0
    sta obj_t,y
    lda #FR_EXPL0
    sta obj_fr,y
    lda #T_NONE
    sta obj_type,x
    inc score
    bne !+
    inc score+1
!:  jmp !nexts+
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

// tmp = shot centre - target origin. Carry clear if |tmp-centre| < limit.
// X/Y (the object indices) survive this helper.
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
    rts

