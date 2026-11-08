// ----------------------------------------------------------------------------
// Level-4 final boss, phase 3 (Stage 17, owner's design): when the mech's core falls, the mech breaks apart
// (the usual death explosions) and an armoured sphere rolls out of the wreck (file L4BALL, attic $8100000: its
// glyphs replace the mech's in the boss area, its palette banks 5/6).
//
// The sphere (boss_x/boss_y, 48x48, drawn by boss_draw) rolls through the upper half of the screen, bounces
// off the edges, changes direction now and then and fires fans of red shots. Every few seconds it stops:
//   BL_OPEN  the iris hatch opens            BL_WARN  the core pulses (warning beeps)
//   BL_BEAM  a stream of fire shots, aimed at the player when it starts
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

.const BL_ROLL = 0
.const BL_OPEN = 1
.const BL_WARN = 2
.const BL_BEAM = 3
.const BL_VULN = 4
.const BL_SHUT = 5

ball_on:   .byte 0                  // 1: the sphere replaced the mech
ball_next: .byte 0                  // 1: the mech is exploding, the sphere follows
bl_mode:   .byte 0
bl_t:      .byte 0                  // frames left in this mode
bl_vx:     .byte 0                  // px per frame, signed
bl_vy:     .byte 0
bl_turn:   .byte 0
bl_fire:   .byte 0
bl_roll:   .byte 0
bl_fr:     .byte FR_BALL_ROLL0
bl_core:   .byte $ff                // slot of the core object
bl_dx:     .byte 0                  // fire stream: sideways speed of every shot
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

// the mech's explosions are over (boss_dying): the sphere appears in the middle of the wreck
ball_start:
    lda #0
    sta ball_next
    lda #1
    sta ball_on
    RunDma(job_ball_in)
    RunDma(job_ball_pal)
    RunDma(job_ball_fl)
    jsr boss_palette
    lda fx_bx                   // centre of the mech body: + (width - 48) / 2, + (height - 48) / 2
    sec
    sbc #40
    lsr
    clc
    adc boss_x
    sta boss_x
    lda boss_x+1
    adc #0
    sta boss_x+1
    lda boss_y+1                // still flying in (above the screen): start at the top
    beq !+
    lda #BALL_YMIN
    sta boss_y
    lda #0
    sta boss_y+1
    beq !y+
!:  lda fx_by
    sec
    sbc #44
    bcs !+
    lda #0
!:  lsr
    clc
    adc boss_y
    sta boss_y
!y: lda boss_y                  // inside BALL_YMIN..BALL_YMAX
    cmp #BALL_YMIN
    bcs !+
    lda #BALL_YMIN
!:  cmp #BALL_YMAX
    bcc !+
    lda #BALL_YMAX
!:  sta boss_y
    lda #40                     // touch box of the sphere
    sta fx_bx
    lda #44
    sta fx_by
    clc                         // a big explosion where it breaks out
    lda boss_x
    adc #8
    sta sp_x
    lda boss_x+1
    adc #0
    sta sp_x+1
    clc
    lda boss_y
    adc #8
    sta sp_y
    lda #0
    sta sp_y+1
    lda #FR_EX32_0
    jsr spawn_explosion
    lda #SFX_EXPLODE_BIG
    jsr sfx_play
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
    lda #BL_ROLL
    sta bl_mode
    lda #120
    sta bl_t
    lda #1
    sta bl_vx
    sta bl_vy
    lda #50
    sta bl_turn
    sta bl_fire
    lda #0
    sta boss_t
    lda #BS_BALL
    sta boss_state
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
    jmp boss_touch
bf_lo: .byte <bl_rolling, <bl_opening, <bl_warning, <bl_beam, <bl_open, <bl_closing
bf_hi: .byte >bl_rolling, >bl_opening, >bl_warning, >bl_beam, >bl_open, >bl_closing

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
    lda #$80                    // $80: aim with the first shot
    sta bl_dx
    lda #BL_BEAM
    ldx #36
    jmp bl_mode_set
!:  rts

bl_beam:                        // a fire shot every second frame
    lda bl_t
    and #1
    bne !+
    jsr bl_stream
!:  dec bl_t
    bne !+
    ldx bl_core                 // now it can be hit
    bmi !m+
    lda #1
    sta obj_b,x
!m: lda #BL_VULN
    ldx #110
    jmp bl_mode_set
!:  rts

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

// one fire shot of the stream from the hatch; the first is aimed at the player, the rest fly the same way
bl_stream:
    clc
    lda boss_x
    adc #16
    sta sp_x
    lda boss_x+1
    adc #0
    sta sp_x+1
    clc
    lda boss_y
    adc #20
    sta sp_y
    lda #0
    sta sp_y+1
    lda #K_SHOT_FIRE
    sta es_kind
    lda #$ff
    sta es_slot
    jsr spawn_eshot_at
    ldy es_slot
    bmi !rts+
    lda #2                      // 2 px per frame (aim_shot's speed)
    sta obj_b,y
    lda bl_dx
    cmp #$80
    bne !+
    jsr aim_shot
    ldy es_slot
    lda obj_a,y
    sta bl_dx
    rts
!:  sta obj_a,y
    lda #SFX_SHOT
    jsr sfx_play
!rts:
    rts

// rolling: move, bounce, turn now and then, fans of red shots
bl_rolling:
    inc bl_roll
    lda bl_roll
    lsr
    lsr
    and #3
    clc
    adc #FR_BALL_ROLL0
    sta bl_fr
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

// core frame (part_frame, obj_kind 5): hidden while shut, pulsing while warning, bright while firing
ball_core_frame:
    lda bl_mode
    cmp #BL_WARN
    bcc !none+
    cmp #BL_SHUT
    beq !none+
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
!c0:
    lda #FR_BALL_CORE0
    sta obj_fr,x
    rts
!none:
    lda #FR_BALL_NONE
    sta obj_fr,x
    rts

job_ball_in:  DmaJob(DMA_CMD_COPY, ATTIC_BALL, BOSS_SWAP_ADDR, BALL_GLYPHS * 64)
job_ball_pal: DmaJob(DMA_CMD_COPY, ATTIC_BALL + BALL_GLYPHS * 64, boss_pal_buf, 48)
job_ball_fl:  DmaJob(DMA_CMD_COPY, ATTIC_BALL + BALL_GLYPHS * 64 + 48, ball_flash, 48)
.errorif (BALL_GLYPHS > 324), "sphere glyphs larger than the boss area"
.errorif (BALL_FILE_BYTES > $10000), "L4BALL larger than its attic area"
