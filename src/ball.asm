// ----------------------------------------------------------------------------
// Level-4 final boss, phase 3 (Stage 17, owner's design; Stage 17b: wreck, hidden appearance, flame column):
// halfway through the mech's death explosions its glyphs and palette are replaced by file L4BALL (attic $8100000:
// the sphere, the mech's wreck and the flame frames in the sphere's colours, palette banks 5/6) - from then on the
// burning wreck lies where the mech fell. At the end of the explosions four big explosions cover the crater and
// the sphere is there: it rolls down out of the wreck (BL_EMERGE).
//
// The sphere (boss_x/boss_y, 48x48, ball_draw) rolls through the upper half of the screen, bounces off the edges,
// changes direction now and then and fires fans of red shots. Every few seconds:
//   BL_AIM   it rolls over the player and stops       BL_OPEN  the iris hatch opens
//   BL_WARN  the core pulses, a small flame flickers (warning beeps)
//   BL_BEAM  a flame column straight down (the hover bosses' flame thrower: hv_burn / hv_draw), sweeping slowly
//   BL_VULN  the hatch stays open: only now the core (T_BOSS object, obj_kind 5) can be hit (also by bombs)
//   BL_SHUT  the hatch closes, it rolls again
// The core's last hit point: the sphere explodes (BS_DIE), the level is cleared.
// ----------------------------------------------------------------------------
.const ATTIC_BALL = $8100000
#if BOSS_TEST
.const BALL_HP   = 8
#else
.const BALL_HP   = 180
#endif
.const BALL_XMIN = 8
.const BALL_XMAX = 320 - 48 - 8
.const BALL_YMIN = 16
.const BALL_YMAX = 92

.const BALL_AIMY = 56                // y while aiming (the flame column then reaches the bottom of the screen)

.const BL_ROLL = 0
.const BL_OPEN = 1
.const BL_WARN = 2
.const BL_BEAM = 3
.const BL_VULN = 4
.const BL_SHUT = 5
.const BL_AIM  = 6
.const BL_EMERGE = 7

ball_on:   .byte 0                  // 1: the sphere replaced the mech
ball_next: .byte 0                  // 1: the mech is exploding, the sphere follows
ball_wreck: .byte 0                 // 1: the mech's wreck lies at wk_x / wk_y
bl_vis:    .byte 0                  // 1: the sphere is drawn
wk_x:      .word 0
wk_y:      .word 0
bl_smoke:  .byte 0
bl_mode:   .byte 0
bl_t:      .byte 0                  // frames left in this mode
bl_vx:     .byte 0                  // px per frame, signed
bl_vy:     .byte 0
bl_turn:   .byte 0
bl_fire:   .byte 0
bl_roll:   .byte 0
bl_fr:     .byte FR_BALL_ROLL0
bl_core:   .byte $ff                // slot of the core object
bl_k:      .byte 0
ball_flash: .fill 48, 0
bl_fan:    .byte <-40, <-20, 0, 20, 40

// KERNAL, levels_load (attic only)
ball_load:
    lda #0
    sta ld_dst
    sta ld_dst+1
    lda #(ATTIC_BALL >> 16) & $0f
    sta ld_dst+2
    lda #(ATTIC_BALL >> 20)
    sta ld_dst+3
    lda #(>BALL_FILE_BYTES) + 1
    sta ld_maxhi
    lda #<name_ball
    ldx #>name_ball
    ldy #name_ball_end - name_ball
    jmp load_seq_to
name_ball: .text "L4BALL"
name_ball_end:

// halfway through the mech's explosions (boss_dying): big explosions all over the body, the mech disappears
ball_cover:
    lda #24
    ldx #8
    jsr bl_boom
    lda #72
    ldx #8
    jsr bl_boom
    lda #24
    ldx #36
    jsr bl_boom
    lda #72
    ldx #36
    jsr bl_boom
    lda #SFX_EXPLODE_BIG
    jmp sfx_play

// three frames later (RRB double buffering: the mech is in no display list any more): its glyphs become the
// sphere's and the wreck's, the wreck lies where the mech fell
ball_wreck_in:
    RunDma(job_ball_in)
    RunDma(job_ball_pal)
    RunDma(job_ball_fl)
    lda #1
    sta ball_on
    sta ball_wreck
    lda #0
    sta bl_vis
    jsr boss_palette
    sec                         // the wreck picture has the mech at (8, 4)
    lda boss_x
    sbc #8
    sta wk_x
    lda boss_x+1
    sbc #0
    sta wk_x+1
    sec
    lda boss_y
    sbc #4
    sta wk_y
    lda boss_y+1
    sbc #0
    sta wk_y+1
    rts

// big explosion at boss position + (A, X)
bl_boom:
    clc
    adc boss_x
    sta sp_x
    lda boss_x+1
    adc #0
    sta sp_x+1
    txa
    clc
    adc boss_y
    sta sp_y
    lda boss_y+1
    adc #0
    sta sp_y+1
    lda #FR_EX32_0
    jmp spawn_explosion

// the mech's explosions are over (boss_dying): in four big explosions the sphere is in the crater of the wreck
ball_start:
    lda #0
    sta ball_next
    clc                         // the crater: mech + (32, 10) for the sphere's top left corner
    lda boss_x
    adc #32
    sta boss_x
    lda boss_x+1
    adc #0
    sta boss_x+1
    clc
    lda boss_y
    adc #10
    sta boss_y
    lda boss_y+1
    adc #0
    sta boss_y+1
    beq !+
    lda #0                      // the mech died still above the screen: start at the top
    sta boss_y
    sta boss_y+1
!:  lda boss_y
    cmp #BALL_YMAX
    bcc !+
    lda #BALL_YMAX
    sta boss_y
!:  lda #0
    ldx #0
    jsr bl_boom
    lda #16
    ldx #0
    jsr bl_boom
    lda #0
    ldx #16
    jsr bl_boom
    lda #16
    ldx #16
    jsr bl_boom
    lda #SFX_EXPLODE_BIG
    jsr sfx_play
    lda #1
    sta bl_vis
    lda #40                     // touch box of the sphere; flame from the hatch; no dust, no deck jets
    sta fx_bx
    lda #44
    sta fx_by
    lda #16
    sta fx_flx
    lda #26
    sta fx_fly
    lda #240
    sta fx_xmax
    lda #0
    sta fx_cat
    sta fx_spn
    sta hv_fp
    sta hv_seg
    sta hv_mov
    sta hv_rnd
    lda #$ff
    sta bl_core
    ldy #5                      // the core: a T_BOSS object, closed at first (the only T_BOSS now)
    jsr boss_new_part
    ldx #AIR_FIRST
!:  lda obj_type,x
    cmp #T_BOSS
    beq !found+
    inx
    cpx #AIR_END
    bne !-
    beq !none+
!found:
    stx bl_core
    lda #0
    sta obj_b,x
    lda #BALL_HP
    sta obj_hp,x
!none:
    lda #BL_EMERGE
    sta bl_mode
    lda #44
    sta bl_t
    lda #50
    sta bl_turn
    sta bl_fire
    lda #0
    sta boss_t
    lda #BS_BALL
    sta boss_state
    rts

// the sphere rolls down out of the wreck
bl_emerge:
    jsr bl_rollfr
    lda boss_y
    cmp #BALL_YMAX
    bcs !+
    inc boss_y
!:  dec bl_t
    bne !rts+
    jsr random
    and #2
    sec
    sbc #1
    sta bl_vx
    lda #1
    sta bl_vy
    lda #BL_ROLL
    ldx #120
    jmp bl_mode_set
!rts:
    rts

// roll animation: 4 frames, one every 4 frames
bl_rollfr:
    inc bl_roll
    lda bl_roll
    lsr
    lsr
    and #3
    clc
    adc #FR_BALL_ROLL0
    sta bl_fr
    rts

// every frame in BS_BALL: the routine of the current mode, then the touch check
ball_fight:
    ldx bl_mode
    lda bf_lo,x
    sta bf_j+1
    lda bf_hi,x
    sta bf_j+2
bf_j:
    jsr $ffff
    dec bl_smoke                // the wreck smoulders: a small explosion now and then
    bne !+
    jsr random
    and #31
    ora #24
    sta bl_smoke
    jsr random
    and #63
    clc
    adc #24
    adc wk_x
    sta sp_x
    lda wk_x+1
    adc #0
    sta sp_x+1
    jsr random
    and #31
    clc
    adc #16
    adc wk_y
    sta sp_y
    lda wk_y+1
    adc #0
    sta sp_y+1
    lda #FR_EX16_0
    jsr spawn_explosion
!:  jmp boss_touch
bf_lo: .byte <bl_rolling, <bl_opening, <bl_warning, <bl_beam, <bl_open, <bl_closing, <bl_aim, <bl_emerge
bf_hi: .byte >bl_rolling, >bl_opening, >bl_warning, >bl_beam, >bl_open, >bl_closing, >bl_aim, >bl_emerge

// next mode A for X frames
bl_mode_set:
    sta bl_mode
    stx bl_t
    rts

bl_opening:                     // hatch opening: OPEN1, OPEN2, OPEN3
    lda bl_t
    jsr bl_hatch
    dec bl_t
    bne !+
    lda #1                      // hv_draw: the small flame flickers in the hatch
    sta hv_fp
    lda #BL_WARN
    ldx #50
    jmp bl_mode_set
!:  rts

bl_warning:                     // core pulsing, warning beeps
    lda #FR_BALL_OPEN3
    sta bl_fr
    lda bl_t
    and #7
    bne !+
    lda #SFX_CURSOR
    jsr sfx_play
!:  dec bl_t
    bne !+
    lda #2                      // the flame column ignites (hv_burn grows it, sweeps after the player)
    sta hv_fp
    lda #1
    sta hv_seg
    lda #0
    sta hv_sc
    lda #HV_BURN
    sta hv_ft
    lda #SFX_BOMB
    jsr sfx_play
    lda #BL_BEAM
    ldx #1
    jmp bl_mode_set
!:  rts

bl_beam:                        // flame column: burning, then fading; then the hatch stays open
    jsr hv_burn
    dec hv_ft
    bne !rts+
    lda hv_fp
    cmp #2
    bne !end+
    lda #3                      // fading: the column shrinks from the tip
    sta hv_fp
    lda #HV_SEGS
    sta hv_seg
    lda #0
    sta hv_sc
    lda #HV_FADE
    sta hv_ft
    rts
!end:
    lda #0
    sta hv_fp
    sta hv_seg
    ldx bl_core                 // now it can be hit
    bmi !m+
    lda #1
    sta obj_b,x
!m: lda #BL_VULN
    ldx #110
    jmp bl_mode_set
!rts:
    rts

// rolling over the player (flame x over his centre) and up/down to BALL_AIMY; there (or after bl_t): open
bl_aim:
    jsr bl_rollfr
    jsr hv_aimx                 // A = target x (8 bit, <= fx_xmax)
    sta tmp
    lda boss_x+1
    bne !l+                     // right of 255: left
    lda boss_x
    cmp tmp
    beq !y+
    bcc !r+
!l: lda boss_x                  // 2 px left (1 if only 1 to go)
    sec
    sbc #1
    sta boss_x
    lda boss_x+1
    sbc #0
    sta boss_x+1
    bne !l2+
    lda boss_x
    cmp tmp
    beq !y+
!l2:
    lda boss_x
    sec
    sbc #1
    sta boss_x
    lda boss_x+1
    sbc #0
    sta boss_x+1
    jmp !y+
!r: inc boss_x
    lda boss_x
    cmp tmp
    beq !y+
    inc boss_x
!y: lda boss_y
    cmp #BALL_AIMY
    beq !chk+
    bcc !d+
    dec boss_y
    jmp !t+
!d: inc boss_y
    jmp !t+
!chk:
    lda boss_x+1
    bne !t+
    lda boss_x
    cmp tmp
    beq !go+
!t: dec bl_t
    bne !rts+
    lda boss_x+1                // time is up: open where it is (x < 256 for the flame sweep)
    bne !rts+
!go:
    lda #BL_OPEN
    ldx #24
    jmp bl_mode_set
!rts:
    rts

bl_open:                        // open and vulnerable
    dec bl_t
    bne !+
    ldx bl_core
    bmi !m+
    lda #0
    sta obj_b,x
!m: lda #BL_SHUT
    ldx #24
    jmp bl_mode_set
!:  rts

bl_closing:                     // OPEN3, OPEN2, OPEN1 backwards
    lda #25
    sec
    sbc bl_t
    jsr bl_hatch
    dec bl_t
    bne !+
    jsr random
    and #63
    clc
    adc #150
    tax
    lda #BL_ROLL
    jmp bl_mode_set
!:  rts

// hatch frame for a counter 24..1 (opening)
bl_hatch:
    ldx #FR_BALL_OPEN1
    cmp #17
    bcs !+
    inx
    cmp #9
    bcs !+
    inx
!:  stx bl_fr
    rts

// rolling: move, bounce, turn now and then, fans of red shots
bl_rolling:
    jsr bl_rollfr
    lda bl_vx                   // x (16 bit), bounce at BALL_XMIN / BALL_XMAX
    bmi !l+
    clc
    adc boss_x
    sta boss_x
    lda boss_x+1
    adc #0
    sta boss_x+1
    beq !+
    lda boss_x
    cmp #<BALL_XMAX
    bcc !y+
    jmp !flipx+
!:  jmp !y+
!l: clc
    adc boss_x
    sta boss_x
    lda boss_x+1
    adc #$ff
    sta boss_x+1
    bmi !flipx+
    bne !y+
    lda boss_x
    cmp #BALL_XMIN
    bcs !y+
!flipx:
    lda bl_vx
    eor #$ff
    clc
    adc #1
    sta bl_vx
!y: lda boss_y                  // y: down again above BALL_YMIN, up again below BALL_YMAX
    clc
    adc bl_vy
    sta boss_y
    cmp #BALL_YMIN
    bcs !+
    lda #1
    sta bl_vy
    bne !t+
!:  cmp #BALL_YMAX
    bcc !t+
    lda #$ff
    sta bl_vy
!t: dec bl_turn                 // a new direction now and then: vx +-1/2, vy -1..1
    bne !+
    jsr random
    and #63
    adc #40
    sta bl_turn
    jsr random
    and #3
    tax
    lda bl_vxs,x
    sta bl_vx
    jsr random
    and #3
    tax
    lda bl_vys,x
    sta bl_vy
!:  dec bl_fire                 // a fan of five red shots
    bne !+
    jsr random
    and #31
    adc #45
    sta bl_fire
    jsr bl_fan5
!:  dec bl_t
    bne !+
    lda #BL_OPEN                // stop and open
    ldx #24
    jmp bl_mode_set
!:  rts
bl_vxs: .byte 1, 2, <-1, <-2
bl_vys: .byte 1, 0, <-1, 1

bl_fan5:
    ldy #4
!:  sty bl_k
    clc
    lda boss_x
    adc #16
    sta sp_x
    lda boss_x+1
    adc #0
    sta sp_x+1
    clc
    lda boss_y
    adc #36
    sta sp_y
    lda #0
    sta sp_y+1
    lda #K_SHOT_RED
    sta es_kind
    lda #$ff
    sta es_slot
    jsr spawn_eshot_at
    ldy es_slot
    bmi !+
    ldx bl_k
    lda bl_fan,x
    sta obj_a,y
!:  ldy bl_k
    dey
    bpl !--
    lda #SFX_SHOT
    jmp sfx_play

// core frame (part_frame, obj_kind 5): hidden while shut, pulsing while warning, bright while firing, steady open
ball_core_frame:
    lda bl_mode
    cmp #BL_WARN
    bne !+
    lda boss_t
    and #4
    beq !c0+
!c1:
    lda #FR_BALL_CORE1
    sta obj_fr,x
    rts
!:  cmp #BL_BEAM
    beq !c1-
    cmp #BL_VULN
    bne !none+
!c0:
    lda #FR_BALL_CORE0
    sta obj_fr,x
    rts
!none:
    lda #FR_BALL_NONE
    sta obj_fr,x
    rts

// boss_draw while ball_on: the wreck, the sphere (gone halfway through its own explosions), the flame column
ball_draw:
    lda ball_wreck
    beq !+
    lda wk_x
    sta px_x
    lda wk_x+1
    sta px_x+1
    lda wk_y
    sta px_y
    lda wk_y+1
    sta px_y+1
    ldy #FR_BALL_WRECK
    lda frame_pal,y
    sta px_pal
    lda #FR_BALL_WRECK
    jsr pixie_draw
!:  lda bl_vis
    beq !rts+
    lda boss_state
    cmp #BS_DIE
    bne !+
    lda boss_t
    cmp #BOSS_DIE / 2
    bcs !rts+
!:  lda boss_x
    sta px_x
    lda boss_x+1
    sta px_x+1
    lda boss_y
    sta px_y
    lda boss_y+1
    sta px_y+1
    ldy #FR_BALL_ROLL0
    lda frame_pal,y
    sta px_pal
    lda bl_fr
    jsr pixie_draw
    jmp hv_draw
!rts:
    rts

job_ball_in:  DmaJob(DMA_CMD_COPY, ATTIC_BALL, BOSS_SWAP_ADDR, BALL_GLYPHS * 64)
job_ball_pal: DmaJob(DMA_CMD_COPY, ATTIC_BALL + BALL_GLYPHS * 64, boss_pal_buf, 48)
job_ball_fl:  DmaJob(DMA_CMD_COPY, ATTIC_BALL + BALL_GLYPHS * 64 + 48, ball_flash, 48)
.errorif (BALL_GLYPHS > 324), "sphere glyphs larger than the boss area"
.errorif (BALL_FILE_BYTES > $10000), "L4BALL larger than its attic area"
