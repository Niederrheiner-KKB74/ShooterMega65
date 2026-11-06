// ----------------------------------------------------------------------------
// Level-1 boss (Stage 7): quadrotor gunship, artwork PR #14 (assets/art/boss-level1).
//
// A `boss` event sets boss_req. When no aircraft are left on screen (at most 5 s
// later) the boss arrives: scrolling stops, its glyphs are swapped in over the
// fighter + bomber frames (file L1BOSS, kept at the end of the level buffer),
// its palette replaces bank 5, the boss music starts.
//   body + 4 rotors   drawn here (boss_draw, before all objects)
//   4 turrets, core   objects of type T_BOSS (air slots): shot, missile and bomb
//                     targets; obj_kind 0-3 turrets, 4 core; obj_b = 1 while it can be hit;
//                     obj_t = fire timer, obj_wave = muzzle flash timer
// Turrets first; when all four are destroyed the core is exposed. Core destroyed:
// explosions, bonus, glyphs and palette restored, scrolling goes on.
// ----------------------------------------------------------------------------
#if BOSS_CORE_TEST
.const BOSS_HP_TURRET = 4          // test build: turrets fall quickly, full-strength core
.const BOSS_HP_CORE  = 200
#elif BOSS_TEST
.const BOSS_HP_TURRET = 4          // test build (build.py --define BOSS_TEST): quick boss
.const BOSS_HP_CORE  = 8
#else
.const BOSS_HP_TURRET = 70         // Stage 7b (owner: boss too easy); Stage 7: 40 / 120
.const BOSS_HP_CORE  = 200
#endif
.const BOSS_BOMB_DMG = 20
.const BOSS_Y        = 20          // fighting height (top of the bob)
.const BOSS_BOB      = 24          // vertical bob range in pixels
.const BOSS_X0       = 112         // entry x (96 px wide, screen centre)
.const BOSS_XMIN     = 24
.const BOSS_XMAX     = 320 - 96 - 24
.const BOSS_WAIT     = 250         // at most 5 s waiting for the sky to clear
.const BOSS_DIE      = 150         // 3 s of explosions
// Stage 7c: L1BOSS is kept in attic RAM (the level buffer is needed for larger levels). The glyphs are
// copied by DMA over the fighter and bomber glyphs when the boss arrives, and the saved originals are copied
// back afterwards. Without attic RAM there is no boss (the level simply goes on).
.const ATTIC_BOSS    = $8020000    // L1BOSS: glyphs + palette
.const BOSS_SWAP_ADDR = PIXIE_ADDR + BOSS_SWAP_GLYPH * 64

// FLASH_BANK, PAL_BOSS_FLASH, FLASH_FRAMES_HIT: layout.asm (used by objects.asm before this file)
.const BS_OFF = 0
.const BS_WAIT = 1
.const BS_ENTER = 2
.const BS_FIGHT = 3
.const BS_CORE = 4
.const BS_DIE = 5

boss_req:   .byte 0
boss_state: .byte 0
boss_x:     .word 0
boss_y:     .word 0
boss_vx:    .byte 0
boss_vy:    .byte 0
boss_t2:    .byte 0                // open core: frames until the next aimed / random shot
boss_t:     .byte 0
boss_left:  .byte 0                // turrets still standing
boss_spd:   .word 0                // scroll speed before the boss

// part offsets relative to the boss (turrets nw, ne, sw, se, core)
part_dx:   .byte 30, 50, 30, 50, 32
part_dy:   .byte 8, 8, 40, 40, 16
rotor_dx:  .byte 0, 64, 0, 64
rotor_dy:  .byte 0, 0, 32, 32
rotor_ph:  .byte 0, 1, 2, 0

// ============================================================== loading (KERNAL)
// called by levels_load (levels.asm) for every level, only with attic RAM: LnBOSS to attic bank bl_bank
boss_load:
    lda #<(ATTIC_BOSS & $ffff)
    sta ld_dst
    lda #>(ATTIC_BOSS & $ffff)
    sta ld_dst+1
    lda bl_bank
    sta ld_dst+2
    lda #(ATTIC_BOSS >> 20)
    sta ld_dst+3
    lda #(>BOSS_FILE_BYTES) + 1
    sta ld_maxhi
    lda #<name_boss
    ldx #>name_boss
    ldy #name_boss_end - name_boss
    jsr load_seq_to
    rts                         // (palette: level_enter; the glyphs come back from the level's enemy set)
bl_bank: .byte (ATTIC_BOSS >> 16) & $0f
name_boss: .text "L1BOSS"
name_boss_end:

// new game while the boss was there: glyphs, palette and scrolling back
boss_reset:
    lda boss_state
    beq !+
    cmp #BS_WAIT
    beq !+
    jsr boss_restore
    lda boss_spd
    sta scroll_spd
    lda boss_spd+1
    sta scroll_spd+1
!:  lda #0
    sta boss_state
    sta boss_req
    rts

// ============================================================== per frame
boss_update:
    lda boss_state
    bne !+
    lda boss_req                // the event arrived
    beq !done+
    lda #0
    sta boss_req
    sta boss_t
    lda attic_ok                // no attic RAM: no boss data
    beq !done+
    lda #BS_WAIT
    sta boss_state
!done:
    rts
!:  inc boss_t
    cmp #BS_WAIT
    bne !+
    jmp boss_wait
!:  cmp #BS_ENTER
    bne !+
    jmp boss_enter
!:  cmp #BS_DIE
    bne !+
    jmp boss_dying
!:  jmp boss_fight

// wait until no aircraft are left (or the time is up), then the boss arrives
boss_wait:
    lda boss_t
    cmp #BOSS_WAIT
    bcs !go+
    ldx #AIR_FIRST
!:  lda obj_type,x
    cmp #T_AIR
    bne !+
    rts                         // still aircraft about
!:  inx
    cpx #AIR_END
    bne !--
!go:
    ldx #AIR_FIRST              // remaining aircraft and their shots leave (their glyphs are swapped out)
!:  lda obj_type,x
    cmp #T_AIR
    bne !+
    lda #T_NONE
    sta obj_type,x
!:  inx
    cpx #SHOT_END
    bne !--
    ldx #SHOT_FIRST
!:  lda obj_type,x
    cmp #T_ESHOT
    bne !+
    lda #T_NONE
    sta obj_type,x
!:  inx
    cpx #SHOT_END
    bne !--
    lda scroll_spd              // the landscape stops
    sta boss_spd
    lda scroll_spd+1
    sta boss_spd+1
    lda #0
    sta scroll_spd
    sta scroll_spd+1
    RunDma(job_boss_in)         // boss glyphs in (attic RAM)
    jsr boss_palette
    lda #MUS_BOSS
    jsr music_play
    lda #0                      // hover tank: flame idle, first target straight below (Stage 11)
    sta hv_fp
    lda #120
    sta hv_ft
    lda #BOSS_X0
    sta hv_tx
    lda #BOSS_Y
    sta hv_ty
    lda #<BOSS_X0
    sta boss_x
    lda #>BOSS_X0
    sta boss_x+1
    lda #<-80                   // above the screen (bodies up to 80 high)
    sta boss_y
    lda #>-80
    sta boss_y+1
    lda #1
    sta boss_vx
    sta boss_vy
    lda #4
    sta boss_left
    ldy #0                      // the four turrets
!:  sty bp_k
    jsr boss_new_part
    ldy bp_k
    iny
    cpy #4
    bne !-
    lda #0
    sta boss_t
    lda #BS_ENTER
    sta boss_state
!rts:
    rts

// part Y (0-3 turret, 4 core) as a T_BOSS object
boss_new_part:
    sty bp_k
    ldx #AIR_FIRST
    lda #AIR_END
    sta ob_end
    jsr alloc_slot
    bcs !+
    lda #T_BOSS
    jsr init_slot
    lda bp_k
    sta obj_kind,x
    lda #1
    sta obj_b,x                 // can be hit
    lda #0
    sta obj_wave,x
    jsr random
    and #63
    clc
    adc #60
    sta obj_t,x                 // first shot after 1-2 s
    ldy bp_k
    lda #BOSS_HP_TURRET
    cpy #4
    bne !hp+
    lda #BOSS_HP_CORE
!hp:
    sta obj_hp,x
    jsr part_pos
    jsr part_frame
!:  rts
bp_k: .byte 0

// slide down to the fighting height (0.5 px per frame)
boss_enter:
    lda boss_t
    and #1
    beq !+
    inc boss_y
    bne !+
    inc boss_y+1
!:  lda boss_y+1
    bne !rts+
    lda boss_y
    cmp #BOSS_Y
    bcc !rts+
    lda #BS_FIGHT
    sta boss_state
!rts:
    jmp boss_touch

// move sideways (1 px per frame, 2 in the core phase) and bob up and down (0.5 px per frame);
// the parts fire in their own update
boss_fight:
    lda cur_level               // level 2: the hover tank glides in every direction (Stage 11)
    beq !+
    jmp hover_fight
!:  jsr boss_step_x
    lda boss_state
    cmp #BS_CORE
    bne !+
    lda boss_t                  // core phase: 1.5 px/frame (Stage 8c; Stage 7b: 2), extra step every 2nd frame
    and #1
    bne !+
    jsr boss_step_x
!:  lda boss_t                  // vertical bob between BOSS_Y and BOSS_Y + BOSS_BOB
    and #1
    bne boss_touch
    lda boss_y+1                // core opened while still flying in: keep descending first
    bne !down+
    lda boss_y
    cmp #BOSS_Y
    bcs !bob+
!down:
    inc boss_y
    bne !+
    inc boss_y+1
!:  jmp boss_touch
!bob:
    lda boss_y
    clc
    adc boss_vy
    sta boss_y
    cmp #BOSS_Y
    beq !turn+
    cmp #BOSS_Y + BOSS_BOB
    bne boss_touch
!turn:
    lda boss_vy
    eor #$ff
    clc
    adc #1
    sta boss_vy
    jmp boss_touch

// one pixel sideways, turn at BOSS_XMIN / BOSS_XMAX
boss_step_x:
    lda boss_vx
    bmi !left+
    clc
    adc boss_x
    sta boss_x
    lda boss_x+1
    adc #0
    sta boss_x+1
    bne !turn+
    lda boss_x
    cmp fx_xmax
    bcc !ok+
!turn:
    lda boss_vx
    eor #$ff
    clc
    adc #1
    sta boss_vx
!ok:
    rts
!left:
    clc
    adc boss_x
    sta boss_x
    lda boss_x+1
    adc #$ff
    sta boss_x+1
    bne !turn-
    lda boss_x
    cmp #BOSS_XMIN
    bcc !turn-
    rts

// the player flying into the boss body: damage (the hit invulnerability limits it)
boss_touch:
    lda pl_state
    bne !no+
    lda boss_y+1                // only when the boss is fully on screen
    bne !no+
    clc                         // player centre x - boss x in 8..88
    lda pl_x
    adc #PL_HIT_CX
    sta tmp
    lda pl_x+1
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc boss_x
    sta tmp
    lda tmp+1
    sbc boss_x+1
    bne !no+
    lda tmp
    cmp #8
    bcc !no+
    cmp fx_bx                   // body width - 8 (boss_fx of the level)
    bcs !no+
    lda pl_y                    // player centre y - boss y in 4..60 (sideways 4..88)
    clc
    adc #PL_HIT_CY
    sec
    sbc boss_y
    bcc !no+
    cmp #4
    bcc !no+
    cmp fx_by
    bcs !no+
    lda #16
    jmp player_damage
!no:
    rts

// ---------------------------------------------------------------- hover tank (level 2, Stage 11, PR #21)
// Glides to a target point (both axes 1 px/frame, in the core phase 1.5), then picks a new one near the
// player's x. In the core phase it fires its flame thrower: warning (small flame, harmless, it stops),
// full jet (damage on contact), fading. Dust at the skirt while it moves (boss_draw).
.const HV_YMIN = 16
.const HV_WARN = 30                // flame phases (frames)
.const HV_BURN = 80                // Stage 12: longer; the jet grows down to HV_SEGS segments of 32 px
.const HV_FADE = 15
.const HV_SEGS = 5                 // segments 24 px apart (they overlap, the flame frames taper)
.const HV_GROW = 4                 // frames per new segment (the tip shoots down at 6 px/frame)
hover_fight:
    jsr hv_jets                 // carrier (level 3): deck jets
    lsr hv_mov                  // dust/wake: still shown one frame after a step (the carrier steps every 2nd)
    lda boss_y+1                // core opened while still gliding in: keep descending first
    bne !in+
    lda boss_y
    cmp #HV_YMIN                // the targets reach up to HV_YMIN
    bcs !+
!in:
    inc boss_y
    bne !t+
    inc boss_y+1
!t: jmp hv_flame
!:  lda hv_fp                   // no gliding while the flame thrower is busy
    bne !t-
    lda fx_cat                  // the carrier glides at half speed
    beq !+
    lda boss_t
    and #1
    bne !t-
!:  jsr hv_step
    lda boss_state
    cmp #BS_CORE
    bne !t-
    lda boss_t
    and #1
    bne !t-
    jsr hv_step
    jmp hv_flame

// one pixel towards (hv_tx, hv_ty) on each axis; there: a new target
hv_step:
    lda boss_x
    cmp hv_tx
    beq !y+
    lda #3
    sta hv_mov
    bcc !r+
    dec boss_x
    jmp !y+
!r: inc boss_x
!y: lda boss_y
    cmp hv_ty
    beq !chk+
    lda #3
    sta hv_mov
    bcc !d+
    dec boss_y
    rts
!d: inc boss_y
    rts
!chk:
    lda boss_x
    cmp hv_tx
    beq !new+
    rts
!new:
    // x: centre over the player +- up to 32 px
    jsr random
    and #63
    sec
    sbc #32
    sta hv_rnd
    jsr hv_aimx
    jmp !st+
!st:
    sta hv_tx
    jsr random                  // y: 16..47 (bodies over 100 high: 16..31)
    and #31
    ldy fx_by
    cpy #100
    bcc !+
    and #15
!:  clc
    adc #HV_YMIN
    sta hv_ty
    rts

// A = boss x that puts the flame over the player (+ hv_rnd), limited to 24..fx_xmax (16-bit, player x up to 320)
hv_aimx:
    lda fx_flx                  // tmp2 = flame x + 8 - PL_HIT_CX + 32
    clc
    adc #40 - PL_HIT_CX
    sta tmp2
    lda hv_rnd
    clc
    adc #32
    clc
    adc pl_x
    sta tmp
    lda pl_x+1
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc tmp2
    sta tmp
    lda tmp+1
    sbc #0
    bmi !lo+                    // left of 0
    bne !hi+                    // 256 and more
    lda tmp
    cmp #24
    bcc !lo+
    cmp fx_xmax
    bcc !rts+
!hi:
    lda fx_xmax
    rts
!lo:
    lda #24
!rts:
    rts
hv_rnd: .byte 0

// flame thrower (core phase, bosses with a flame): phase hv_fp 0 idle, 1 warning, 2 jet, 3 fading
hv_flame:
    lda fx_flame
    beq hv_touch
    lda boss_state
    cmp #BS_CORE
    beq !+
hv_touch:
    jmp boss_touch
!:  dec hv_ft
    bne !hit+
    ldx hv_fp                   // next phase
    inx
    cpx #4
    bcc !+
    ldx #0
!:  stx hv_fp
    lda #0
    sta hv_seg
    sta hv_sc
    cpx #2
    bne !+
    inc hv_seg                  // jet: starts with one segment
!:  cpx #3
    bne !+
    lda #HV_SEGS                // fading: the jet shrinks from the tip
    sta hv_seg
!:  lda hv_len,x
    bne !+
    jsr random                  // idle: 1.6-3.6 s
    ora #80
!:  sta hv_ft
    cpx #2
    bne !hit+
    lda #SFX_BOMB               // the jet ignites
    jsr sfx_play
!hit:
    jsr hv_grow
    lda hv_seg                  // jet (growing or fading): the player in the flame takes damage
    beq !touch+
    lda pl_state
    bne !touch+
    clc                         // player centre x - (boss x + flame x) in 0..15
    lda pl_x
    adc #PL_HIT_CX
    sta tmp
    lda pl_x+1
    adc #0
    sta tmp+1
    clc
    lda boss_x
    adc fx_flx
    sta tmp2
    lda boss_x+1
    adc #0
    sta tmp2+1
    sec
    lda tmp
    sbc tmp2
    sta tmp
    lda tmp+1
    sbc tmp2+1
    bne !touch+
    lda tmp
    cmp #16
    bcs !touch+
    lda hv_seg                  // length of the jet: segments * 24 + 8
    asl
    asl
    asl
    sta tmp2
    asl
    clc
    adc tmp2
    adc #8
    sta tmp2
    clc                         // player centre y - (boss y + flame y) in 0..length-1
    lda boss_y
    adc fx_fly
    sta tmp
    lda pl_y
    clc
    adc #PL_HIT_CY
    sec
    sbc tmp
    bcc !touch+
    cmp tmp2
    bcs !touch+
    lda #12
    jsr player_damage
!touch:
    jmp boss_touch
hv_len: .byte 0, HV_WARN, HV_BURN, HV_FADE

// carrier (Stage 13): every 2-5 s a jet takes off from the catapult (hv_jt < 24: launch views in hv_draw) and
// flies at the player like a fire shot (it cannot be shot down)
hv_jets:
    lda fx_cat
    beq !rts+
    dec hv_jt
    bne !rts+
    jsr random
    ora #96
    sta hv_jt
    clc
    lda boss_x
    adc fx_catx
    sta sp_x
    lda boss_x+1
    adc #0
    sta sp_x+1
    clc
    lda boss_y
    adc fx_caty
    sta sp_y
    lda boss_y+1
    adc #0
    sta sp_y+1
    lda #K_SHOT_FIRE
    sta es_kind
    lda #$ff
    sta es_slot
    jsr spawn_eshot_at
    ldy es_slot
    bmi !rts+
    lda #FR_BOSS_JET2
    sta obj_fr,y
    sta obj_base,y
    lda #SFX_SELECT
    jmp sfx_play
!rts:
    rts
hv_jt:  .byte 120
hv_walk: .byte 0
bd_clk: .byte 0

// jet: one more segment every HV_GROW frames, the boss sweeps slowly towards the player (0.5 px/frame);
// fading: one segment less every HV_FADE / HV_SEGS frames
hv_grow:
    lda hv_fp
    cmp #2
    bne !fade+
    inc hv_sc
    lda hv_sc
    cmp #HV_GROW
    bcc !sw+
    lda #0
    sta hv_sc
    lda hv_seg
    cmp #HV_SEGS
    bcs !sw+
    inc hv_seg
!sw:
    lda boss_t                  // sweep
    and #1
    bne !rts+
    jsr hv_aimx
    cmp boss_x
    beq !rts+
    bcc !l+
    inc boss_x
    rts
!l: dec boss_x
    rts
!fade:
    cmp #3
    bne !rts+
    inc hv_sc
    lda hv_sc
    cmp #HV_FADE / HV_SEGS
    bcc !rts+
    lda #0
    sta hv_sc
    lda hv_seg
    beq !rts+
    dec hv_seg
!rts:
    rts
hv_seg: .byte 0
hv_sc:  .byte 0
hv_k:   .byte 0
hv_tx:  .byte BOSS_X0
hv_ty:  .byte BOSS_Y
hv_mov: .byte 0
hv_fp:  .byte 0
hv_ft:  .byte 120

// effects and sizes of this level's boss (level_enter, from boss_fx1/2 of tools/import_art.py)
.const BOSS_FX_LEN = 19
boss_fx_cur: .byte 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 88, 60, BOSS_XMAX, 0, 0, 0, 0
.label fx_flx   = boss_fx_cur + 0     // flame position on the body
.label fx_fly   = boss_fx_cur + 1
.label fx_sx    = boss_fx_cur + 2     // dust positions x0-3, y0-3 (signed)
.label fx_sy    = boss_fx_cur + 6
.label fx_spn   = boss_fx_cur + 10    // number of dust positions
.label fx_rotn  = boss_fx_cur + 11    // number of rotors
.label fx_bx    = boss_fx_cur + 12    // body box for boss_touch: width - 8, height - 4
.label fx_by    = boss_fx_cur + 13
.label fx_xmax  = boss_fx_cur + 14    // right limit of x
.label fx_flame = boss_fx_cur + 15    // 1 = flame thrower
.label fx_catx  = boss_fx_cur + 16    // Stage 13: catapult (deck jets) position, flag
.label fx_caty  = boss_fx_cur + 17
.label fx_cat   = boss_fx_cur + 18
.errorif (boss_place2 - boss_fx1 != BOSS_FX_LEN), "boss_fx tables of import_art.py and BOSS_FX_LEN differ"

// dust at the skirt while gliding, flame jet in its phases (boss_draw)
hv_draw:
    lda hv_mov
    beq !fl+
    lda fx_spn
    beq !fl+
    sta bd_i
    dec bd_i
!sp:
    ldx bd_i
    ldy #0                      // x = boss x + signed offset
    lda fx_sx,x
    bpl !+
    dey
!:  clc
    adc boss_x
    sta px_x
    tya
    adc boss_x+1
    sta px_x+1
    ldy #0
    lda fx_sy,x
    bpl !+
    dey
!:  clc
    adc boss_y
    sta px_y
    tya
    adc boss_y+1
    sta px_y+1
    ldy #FR_BOSS_SPRAY0
    lda frame_pal,y
    sta px_pal
    lda boss_t                  // three phases, shifted per cloud
    lsr
    lsr
    clc
    adc bd_i
!:  cmp #3
    bcc !+
    sbc #3
    bcs !-
!:  clc
    adc #FR_BOSS_SPRAY0
    jsr pixie_draw
    dec bd_i
    bpl !sp-
!fl:
    lda fx_cat                  // carrier: jet on the catapult before take-off
    beq !nc+
    lda hv_jt
    cmp #24
    bcs !nc+
    cmp #12                     // first on the catapult (steam), then lifting off
    lda #FR_BOSS_JET0
    bcs !+
    lda #FR_BOSS_JET1
!:  pha
    clc
    lda boss_x
    adc fx_catx
    sta px_x
    lda boss_x+1
    adc #0
    sta px_x+1
    clc
    lda boss_y
    adc fx_caty
    sta px_y
    lda boss_y+1
    adc #0
    sta px_y+1
    ldy #FR_BOSS_JET0
    lda frame_pal,y
    sta px_pal
    pla
    jsr pixie_draw
!nc:
    lda hv_fp
    bne !+
    rts
!:  clc
    lda boss_x
    adc fx_flx
    sta px_x
    lda boss_x+1
    adc #0
    sta px_x+1
    clc
    lda boss_y
    adc fx_fly
    sta px_y
    lda boss_y+1
    adc #0
    sta px_y+1
    ldy #FR_BOSS_FLAME0
    lda frame_pal,y
    sta px_pal
    lda hv_fp
    cmp #1
    bne !jet+
    lda boss_t                  // warning: the small flame flickers
    and #4
    beq !rts+
    lda #FR_BOSS_FLAME0
    jmp pixie_draw
!jet:
    lda hv_seg                  // jet: hv_seg segments below each other
    beq !rts+
    sta hv_k
!seg:
    lda hv_fp
    cmp #3
    beq !f2+
    lda boss_t                  // full: flickers between full and fading view, shifted per segment
    lsr
    clc
    adc hv_k
    and #1
    clc
    adc #FR_BOSS_FLAME1
    ldx hv_k                    // the tip (lowest segment) of a growing jet: the short flame
    cpx #1
    bne !+
    ldx hv_seg
    cpx #HV_SEGS
    beq !+
    lda #FR_BOSS_FLAME0
    jmp !+
!f2:
    lda #FR_BOSS_FLAME2
!:  ldx px_y                    // pixie_draw may change px_y: keep it
    phx
    ldx px_y+1
    phx
    jsr pixie_draw
    plx
    stx px_y+1
    plx
    clc
    txa
    adc #24
    sta px_y
    bcc !+
    inc px_y+1
!:  dec hv_k
    bne !seg-
!rts:
    rts

// core destroyed: explosions over the body, then everything back to normal
boss_dying:
    lda boss_t
    and #7
    bne !+
    jsr random                  // explosion at a random place on the body
    and #63
    clc
    adc #8
    adc boss_x
    sta sp_x
    lda boss_x+1
    adc #0
    sta sp_x+1
    jsr random
    and #31
    clc
    adc #8
    adc boss_y
    sta sp_y
    lda boss_y+1
    adc #0
    sta sp_y+1
    lda boss_t
    and #8
    beq !small+
    lda #FR_EX32_0
    jsr spawn_explosion
    lda #SFX_EXPLODE_BIG
    jsr sfx_play
    jmp !+
!small:
    lda #FR_EX16_0
    jsr spawn_explosion
!:  lda boss_t
    cmp #BOSS_DIE / 2           // the wreck disappears (boss_draw): the turret wrecks go with it
    bne !+
    jsr boss_parts_away
!:  lda boss_t
    cmp #BOSS_DIE
    bcc !rts+
    // gone: parts away, glyphs and palette back, the landscape moves again
    ldx #AIR_FIRST
!:  lda obj_type,x
    cmp #T_BOSS
    bne !+
    lda #T_NONE
    sta obj_type,x
!:  inx
    cpx #AIR_END
    bne !--
    jsr boss_restore
    lda boss_spd
    sta scroll_spd
    lda boss_spd+1
    sta scroll_spd+1
    lda #MUS_LEVEL1
    jsr music_play
    lda #BS_OFF
    sta boss_state
!rts:
    rts

// all T_BOSS objects disappear, each with an explosion
boss_parts_away:
    ldx #AIR_FIRST
!:  lda obj_type,x
    cmp #T_BOSS
    bne !next+
    lda #T_NONE
    sta obj_type,x
    stx bpa_x
    lda obj_xl,x
    sta sp_x
    lda obj_xh,x
    sta sp_x+1
    lda obj_yl,x
    sta sp_y
    lda obj_yh,x
    sta sp_y+1
    lda #FR_EX16_0
    jsr spawn_explosion
    ldx bpa_x
!next:
    inx
    cpx #AIR_END
    bne !-
    rts
bpa_x: .byte 0

boss_restore:
    ldx cur_level               // the level's aircraft glyphs back (Stage 13: from its enemy set)
    jsr set_in
    jmp palette_init

// ============================================================== parts (T_BOSS objects)
upd_boss:
    lda boss_state              // parts stand still while the boss is dying
    cmp #BS_DIE
    bne !+
    rts
!:  jsr part_pos
    lda obj_a,x                 // hit flash timer
    beq !+
    dec obj_a,x
!:  lda obj_wave,x              // muzzle flash timer
    beq !+
    dec obj_wave,x
!:  lda obj_b,x
    bne !+
    jmp part_frame              // destroyed: only the frame
!:  lda boss_state
    cmp #BS_FIGHT
    bcs !+
    jmp part_frame              // no shots while entering
!:
    lda obj_kind,x
    cmp #4
    bne !+
    jsr core_extra              // open core: aimed and random-angle shots between the fans
!:  dec obj_t,x
    beq !+
    jmp part_frame
!:
    jsr random                  // next shot: turrets 0.5-1.7 s, faster with fewer left; core 0.7-1.3 s
    and #31
    ldy obj_kind,x
    cpy #4
    beq !core+
    clc
    adc #24
    adc boss_left               // + 8 per turret still standing
    adc boss_left
    adc boss_left
    adc boss_left
    adc boss_left
    adc boss_left
    adc boss_left
    adc boss_left
    sta obj_t,x
    lda #6
    sta obj_wave,x
    lda #K_SHOT_RED
    jsr spawn_eshot_a
    jmp part_frame
!core:
    clc
    adc #36
    sta obj_t,x
    ldy #2                      // fan of three shots: left, straight down, right
!fan:
    sty cf_i
    lda #K_SHOT_FIRE
    jsr spawn_eshot_a
    ldy es_slot
    bmi !+
    sty tmp
    ldy cf_i
    lda fan_dx,y
    ldy tmp
    sta obj_a,y
!:  ldy cf_i
    dey
    bpl !fan-
    jmp part_frame
cf_i:   .byte 0
fan_dx: .byte $ec, 0, 20         // -1.25, 0, +1.25 px per frame

// Open core, between the fans (Stage 7c): every 0.4-1 s a red shot, half of them aimed exactly at the
// player, the others at a random angle (up to 4 px/frame sideways). The player cannot hide at the edges.
core_extra:
    dec boss_t2
    bne !rts+
    jsr random
    and #31
    clc
    adc #20
    sta boss_t2
    lda #K_SHOT_RED
    jsr spawn_eshot_a           // keeps X
    ldy es_slot
    bmi !rts+
    jsr random
    bmi !aim+
    jsr random                  // random angle: -64..+63 (1/16 px)
    and #$7f
    sec
    sbc #64
    sta obj_a,y
!rts:
    rts
!aim:
    jmp aim_shot

// shot Y (red, 2 px/frame down): dx so that it flies at the player's centre.
// dx(1/16 px) = (player x - shot x) * 2 * 16 / (player y - shot y), at most 4 px/frame. Keeps X and Y.
aim_shot:
    sty as_y
    lda obj_yh,y                // only from the visible area
    bne !rts+
    clc                         // dy = player centre y - shot centre y (shot 16x16: +8)
    lda pl_y
    adc #PL_HIT_CY - 8
    sec
    sbc obj_yl,y
    bcc !rts+                   // player above the shot: keep the default
    cmp #16
    bcs !+
    lda #16
!:  sta as_dv
    clc                         // dxpix = player centre x - 8 - shot x (16 bit, signed)
    lda pl_x
    adc #PL_HIT_CX - 8
    sta tmp
    lda pl_x+1
    adc #0
    sta tmp+1
    sec
    lda tmp
    sbc obj_xl,y
    sta tmp
    lda tmp+1
    sbc obj_xh,y
    sta tmp+1
    sta as_sg                   // sign
    bpl !+
    lda #0                      // |dxpix|
    sec
    sbc tmp
    sta tmp
    lda #0
    sbc tmp+1
    sta tmp+1
!:  ldy #5                      // * 32
!:  asl tmp
    rol tmp+1
    dey
    bne !-
    lda #0                      // tmp = tmp / as_dv (16 / 8 bit)
    ldy #16
!:  asl tmp
    rol tmp+1
    rol
    bcs !sub+
    cmp as_dv
    bcc !nx+
!sub:
    sbc as_dv
    inc tmp
!nx:
    dey
    bne !-
    lda tmp+1                   // at most 64 (4 px per frame)
    bne !max+
    lda tmp
    cmp #65
    bcc !+
!max:
    lda #64
!:  bit as_sg
    bpl !+
    eor #$ff
    clc
    adc #1
!:  ldy as_y
    sta obj_a,y
!rts:
    ldy as_y
    rts
as_y:  .byte 0
as_dv: .byte 0
as_sg: .byte 0
// frame of part X: turrets aim south / south-east / south-west, destroyed view; core overlay
part_frame:
    lda obj_kind,x
    cmp #4
    bne !+
    lda #FR_BOSS_CORE
    sta obj_fr,x
    rts
!:  asl
    asl
    clc
    adc #FR_BOSS_T0_S
    sta tmp
    lda obj_b,x
    bne !+
    lda tmp                     // destroyed
    clc
    adc #3
    sta obj_fr,x
    rts
!:  sec                         // player centre - turret centre (x + 8)
    lda pl_x
    adc #PL_HIT_CX - 8 - 1
    sta tmp2
    lda pl_x+1
    adc #0
    sta tmp2+1
    sec
    lda tmp2
    sbc obj_xl,x
    sta tmp2
    lda tmp2+1
    sbc obj_xh,x
    bmi !neg+
    bne !se+
    lda tmp2
    cmp #24
    bcs !se+
!s: lda tmp
    sta obj_fr,x
    rts
!se:
    lda tmp
    clc
    adc #1
    sta obj_fr,x
    rts
!neg:
    cmp #$ff
    bne !sw+
    lda tmp2
    cmp #<-24
    bcs !s-
!sw:
    lda tmp
    clc
    adc #2
    sta obj_fr,x
    rts

// part X at boss position + its offset
part_pos:
    ldy obj_kind,x
    clc
    lda boss_x
    adc part_dx,y
    sta obj_xl,x
    lda boss_x+1
    adc #0
    sta obj_xh,x
    clc
    lda boss_y
    adc part_dy,y
    sta obj_yl,x
    lda boss_y+1
    adc #0
    sta obj_yh,x
    rts

// part X lost its last hit point (from collide_shots or the bomb)
boss_part_down:
    lda #0
    sta obj_b,x
    sta obj_wave,x
    stx bpd_x
    clc                         // explosion on the part
    lda obj_xl,x
    sta sp_x
    lda obj_xh,x
    sta sp_x+1
    lda obj_yl,x
    sta sp_y
    lda obj_yh,x
    sta sp_y+1
    lda obj_kind,x
    cmp #4
    beq !core+
    lda #FR_EX16_0
    jsr spawn_explosion
    lda #SFX_EXPLODE
    jsr sfx_play
    ldx #$10                    // 1000 points per turret
    lda #$00
    jsr score_add
    ldx bpd_x
    jsr part_frame
    dec boss_left
    bne !+
    lda #BS_CORE                // all turrets down: the core opens
    sta boss_state
    lda #40
    sta boss_t2
    ldy #4
    jsr boss_new_part
    lda #SFX_EXPLODE_BIG
    jsr sfx_play
!:  ldx bpd_x
    rts
!core:
    ldx bpd_x                   // the core is gone: the boss explodes
    lda #T_NONE
    sta obj_type,x
    ldx #$50                    // 5000 points
    lda #$00
    jsr score_add
    lda #SFX_BOMB
    jsr sfx_play
    lda #0
    sta boss_t
    lda #BS_DIE
    sta boss_state
    ldx bpd_x
    rts
bpd_x: .byte 0

// bomb: every part that can be hit loses BOSS_BOMB_DMG (called for each T_BOSS object X)
boss_bomb_part:
    lda obj_b,x
    beq !+
    lda obj_hp,x
    sec
    sbc #BOSS_BOMB_DMG
    sta obj_hp,x
    beq !down+
    bcc !down+
    lda #FLASH_FRAMES_HIT       // still standing: hit flash
    sta obj_a,x
    rts
!down:
    jmp boss_part_down
!:  rts

// ============================================================== drawing
// body and rotors, before all objects (turrets, core and explosions are drawn on top)
boss_draw:
    lda boss_state
    cmp #BS_ENTER
    bcs !+
    rts
!:  cmp #BS_DIE                 // the wreck disappears halfway through the explosions
    bne !+
    lda boss_t
    cmp #BOSS_DIE / 2
    bcc !+
    rts
!:  lda boss_x
    sta px_x
    lda boss_x+1
    sta px_x+1
    lda boss_y
    sta px_y
    lda boss_y+1
    sta px_y+1
    ldy #FR_BOSS_BODY
    lda frame_pal,y
    sta px_pal
    tya
    jsr pixie_draw
    lda fx_flame                // the mech (flame and drones, level 4): legs step only while it walks
    and fx_cat
    beq !+
    lda hv_mov
    beq !w+
    inc hv_walk
!w: lda hv_walk
    jmp !c+
!:  lda boss_t
!c: sta bd_clk
    ldx fx_rotn                 // rotors / fans / legs of this boss
    dex
    stx bd_i
!rot:
    ldx bd_i
    clc
    lda boss_x
    adc rotor_dx,x
    sta px_x
    lda boss_x+1
    adc #0
    sta px_x+1
    clc
    lda boss_y
    adc rotor_dy,x
    sta px_y
    lda boss_y+1
    adc #0
    sta px_y+1
    lda bd_clk                  // rotor phase: every 4 frames, offset per rotor
    lsr
    lsr
    clc
    adc rotor_ph,x
!:  cmp #3
    bcc !+
    sbc #3
    bcs !-
!:  clc
    adc #FR_BOSS_ROTOR0
    jsr pixie_draw
    dec bd_i
    bpl !rot-
    jsr hv_draw                 // dust and flame of the hover tank (Stage 11)
    // muzzle flashes under firing turrets
    ldx #AIR_FIRST
!mz:
    lda obj_type,x
    cmp #T_BOSS
    bne !next+
    lda obj_wave,x
    beq !next+
    stx bd_x
    lda obj_xl,x
    sta px_x
    lda obj_xh,x
    sta px_x+1
    clc
    lda obj_yl,x
    adc #15
    sta px_y
    lda obj_yh,x
    adc #0
    sta px_y+1
    lda obj_wave,x
    and #2
    lsr
    clc
    adc #FR_BOSS_MUZZLE0
    jsr pixie_draw
    ldx bd_x
!next:
    inx
    cpx #AIR_END
    bne !mz-
    rts
bd_i: .byte 0
bd_x: .byte 0

// ============================================================== glyphs and palette
job_boss_pal: DmaJob(DMA_CMD_COPY, ATTIC_BOSS + BOSS_GLYPHS * 64, boss_pal_buf, 48)
job_boss_in:  DmaJob(DMA_CMD_COPY, ATTIC_BOSS, BOSS_SWAP_ADDR, BOSS_GLYPHS * 64)
boss_pal_buf: .fill 48, 0

// bank 5 <- boss palette (R, G, B planes of 16), bank 6 <- lightened copy
boss_palette:
    ldx #15
!:  lda boss_pal_buf,x
    sta PAL_RED + BOSS_BANK * 16,x
    lda boss_pal_buf+16,x
    sta PAL_GREEN + BOSS_BANK * 16,x
    lda boss_pal_buf+32,x
    sta PAL_BLUE + BOSS_BANK * 16,x
    dex
    bpl !-
    ldz #0
    ldx #15                     // lightened copy for the hit flash
!:  lda boss_flash_pal,x
    sta PAL_RED + FLASH_BANK * 16,x
    lda boss_flash_pal+16,x
    sta PAL_GREEN + FLASH_BANK * 16,x
    lda boss_flash_pal+32,x
    sta PAL_BLUE + FLASH_BANK * 16,x
    dex
    bpl !-
    rts

.errorif (BOSS_FILE_BYTES > $10000), "L1BOSS larger than its 64 KB attic area"
.errorif (BOSS_GLYPHS * 64 > $10000), "boss glyph save larger than its 64 KB attic area"
.errorif ((PIXIE_ADDR + BOSS_SWAP_GLYPH * 64) >> 16 != (PIXIE_ADDR + (BOSS_SWAP_GLYPH + BOSS_GLYPHS) * 64 - 1) >> 16), "boss swap area crosses a bank"
