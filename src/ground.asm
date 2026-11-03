// ----------------------------------------------------------------------------
// Ground targets (Stage 8, artwork PR #15, assets/art/ground-targets)
//
// Destroyable buildings are landscape tiles. The level data (LnDAT, build_level.py) say for every tile
// whether it has a destroyed variant (gt_dest) and which target it belongs to (gt_info: kind << 2 |
// row << 1 | column inside a 2x2 group). The destroyed glyphs (file LnDEST) live in two places:
// variants 0-31 at DEST1_ADDR (char $1780), 32-47 in the last 32 glyphs of the pixie area (char $13E0).
//
// Player shots pass over buildings and damage every tile cell they cross once. A building that has lost
// its hit points is destroyed.
// Cells already in the ring are changed there at once; cells of rows not decoded yet go into the override list
// (absolute metarow + column), which level_row applies when the row is decoded.
// The list is keyed by the absolute row, so the next pass of the level shows the buildings intact again.
//
// Ground guns are objects of type T_GUN in the ground slots (like tanks). They move with the landscape,
// turn towards the player one step (45 degrees) every 8 frames and fire aimed shots when they point at
// him. obj_kind 0 light (16x16) / 1 heavy (32x32), obj_a direction 0-7 (N, NE ... NW), obj_b 1 = alive,
// obj_t fire timer, obj_wave muzzle flash timer. Destroyed guns stay as wrecks.
// ----------------------------------------------------------------------------
.const DEST1_ADDR  = $05E000        // destroyed tiles 0-31 (4 KB, char $1780)
.const DEST2_ADDR  = $04F800        // destroyed tiles 32-47 (2 KB, char $13E0, end of the pixie area)
.const PIXIE2_ADDR = $052800        // heavy gun glyphs (file PIXIES2, 91 of 96 glyphs)
.const GD_OV_N     = 48             // destroyed cells remembered
.const GD_DM_N     = 8              // damaged buildings remembered
.const GK_HALL     = 7
.const GUN_HP_LIGHT = 6
.const GUN_HP_HEAVY = 60           // Stage 8b (owner: too easy); Stage 8: 24

.errorif (DEST1_ADDR + 32 * 128 > $05F000), "destroyed tiles overlap the player sprites at $5F000"
.errorif (DEST2_ADDR != PIXIE_ADDR + PIXIE_MAX * 64), "destroyed tiles must follow the pixie area"
.errorif (DEST2_ADDR + 16 * 128 > $050000), "destroyed tiles 32-47 overlap the level buffer"
.errorif (PIXIE2_ADDR + PIXIES2_BYTES > $054000), "heavy gun glyphs overlap screen buffer A"
.errorif (PIXIE2_ADDR < LEVEL_BUF + $2800), "heavy gun glyphs overlap the 10 KB of LnDAT"

// target kinds (build_level.py TARGET_KINDS): hangar, depot, checkpoint, bunker, radar, fuel, crates, hall tile
gk_hp:     .byte 16, 12,  8, 24, 12, 10,  4,  4
gk_size:   .byte  2,  2,  2,  2,  2,  2,  2,  1
gk_pts_lo: .byte $00,$00,$00,$00,$00,$00,$50,$50   // BCD: 500 400 200 800 600 500 150 50
gk_pts_hi: .byte $05,$04,$02,$08,$06,$05,$01,$00
gk_drop:   .byte 0, K_CASH2, 0, K_CASH3, 0, K_CASH1, K_BONUS, 0

gt_dest: .fill 128, $ff             // tile -> destroyed variant (or $ff)
gt_info: .fill 128, 0
dk_lo:   .fill 48, 0                // destroyed variant: char of the upper half (low byte), high byte, colour
dk_hi:   .fill 48, 0
dk_col:  .fill 48, 0
ov_rlo:  .fill GD_OV_N, $ff         // destroyed cells: absolute metarow, column
ov_rhi:  .fill GD_OV_N, $ff
ov_col:  .fill GD_OV_N, 0
ov_next: .byte 0
dm_rlo:  .fill GD_DM_N, $ff         // damaged buildings: anchor (upper left cell), hit points left
dm_rhi:  .fill GD_DM_N, $ff
dm_col:  .fill GD_DM_N, 0
dm_hp:   .fill GD_DM_N, 0
dm_next: .byte 0

// ============================================================== loading (KERNAL, at start)
// LnDEST through the load buffer to its two places (called by level_load before LnDAT)
dest_load:
    lda #<name_dest
    ldx #>name_dest
    ldy #name_dest_end - name_dest
    jsr load_seq
    bcs !+
    RunDma(job_dest1)
    RunDma(job_dest2)
    clc
!:  rts
name_dest: .text "L1DEST"
name_dest_end:
job_dest1: DmaJob(DMA_CMD_COPY, LEVEL_BUF, DEST1_ADDR, 32 * 128)
job_dest2: DmaJob(DMA_CMD_COPY, LEVEL_BUF + 32 * 128, DEST2_ADDR, 16 * 128)

pixies2_load:
    lda #<(PIXIE2_ADDR & $ffff)
    sta ld_dst
    lda #>(PIXIE2_ADDR & $ffff)
    sta ld_dst+1
    lda #(PIXIE2_ADDR >> 16)
    sta ld_dst+2
    lda #0
    sta ld_dst+3
    lda #(>PIXIES2_BYTES) + 1
    sta ld_maxhi
    lda #<name_pixies2
    ldx #>name_pixies2
    ldy #name_pixies2_end - name_pixies2
    jmp load_seq_to
name_pixies2: .text "PIXIES2"
name_pixies2_end:

// tables behind the path code of LnDAT (level_init)
gd_tables:
    lda lev_offgt
    sta tmp2
    lda lev_offgt+1
    sta tmp2+1
    ldx #0
!:  jsr lev_read
    sta gt_dest,x
    jsr lev_inc
    inx
    bpl !-
    ldx #0
!:  jsr lev_read
    sta gt_info,x
    jsr lev_inc
    inx
    bpl !-
    ldx #0
!:  cpx lev_ndest
    beq gd_reset
    jsr lev_read
    sta dk_lo,x
    jsr lev_inc
    jsr lev_read
    sta dk_hi,x
    jsr lev_inc
    jsr lev_read
    sta dk_col,x
    jsr lev_inc
    inx
    bne !-
    // fall through
// new game / level start: everything intact
gd_reset:
    ldx #GD_OV_N - 1
    lda #$ff
!:  sta ov_rhi,x
    dex
    bpl !-
    ldx #GD_DM_N - 1
!:  sta dm_rhi,x
    dex
    bpl !-
    rts

// ============================================================== decoding (level_row)
// dr_glyph / dr_hi / dr_col of glyph row tmp (absolute): destroyed cells of that metarow
gd_apply:
    lda tmp+1
    lsr
    sta ga_m+1
    lda tmp
    ror
    sta ga_m
    ldy #GD_OV_N - 1
!ov:
    lda ov_rlo,y
    cmp ga_m
    bne !next+
    lda ov_rhi,y
    cmp ga_m+1
    bne !next+
    ldx ov_col,y
    lda dr_hi,x
    cmp #>TILE_CHAR
    bne !next+                  // already destroyed
    sty ga_y
    lda dr_glyph,x
    lsr
    tay
    lda gt_dest,y
    ldy ga_y
    cmp #$ff
    beq !next+
    tay                         // destroyed variant k
    lda lev_half                // 1 = upper half (char k), 0 = lower half (char k + 1)
    eor #1
    clc
    adc dk_lo,y
    sta dr_glyph,x
    lda dk_hi,y
    sta dr_hi,x
    lda dk_col,y
    sta dr_col,x
    ldy ga_y
!next:
    dey
    bpl !ov-
    rts
ga_m: .word 0
ga_y: .byte 0

// ============================================================== player shots over buildings
// called by upd_pshot (X = shot). The shot's tip (x+8, y) is tested once per tile cell.
gs_out:
    rts
gd_shot:
    lda obj_yh,x
    bne gs_out
    lda obj_yl,x
    cmp #200
    bcs gs_out
    clc                         // glyph row m = (scroll_px + 199 - y) >> 3
    lda scroll_px
    adc #199
    sta gs_m
    lda scroll_px+1
    adc #0
    sta gs_m+1
    sec
    lda gs_m
    sbc obj_yl,x
    sta gs_m
    lda gs_m+1
    sbc #0
    sta gs_m+1
    ldy #3
!:  lsr gs_m+1
    ror gs_m
    dey
    bne !-
    clc                         // column = (x + 8 + 16) >> 4
    lda obj_xl,x
    adc #24
    sta gs_c
    lda obj_xh,x
    adc #0
    ldy #4
!:  lsr
    ror gs_c
    dey
    bne !-
    lda gs_c
    beq gs_out                   // hidden column
    cmp #BG_TOKENS
    bcs gs_out
    lda gs_m+1                  // new cell? (metarow low byte in obj_cnt, column + 1 in obj_dly)
    lsr
    lda gs_m
    ror
    sta gs_ml
    ldy gs_c
    iny
    tya
    cmp obj_dly,x
    bne !new+
    lda gs_ml
    cmp obj_cnt,x
    beq gs_out
!new:
    tya
    sta obj_dly,x
    lda gs_ml
    sta obj_cnt,x
    stx gs_x
    jsr gd_target               // a destroyable tile here?
    bcs !done+
    lda #0
    sta gs_bomb
    jsr gd_hit
!done:
    ldx gs_x
    rts
gs_m:    .word 0
gs_c:    .byte 0
gs_ml:   .byte 0
gs_x:    .byte 0
gs_info: .byte 0
gs_bomb: .byte 0

// glyph row gs_m, column gs_c: carry clear if the tile there can be destroyed (gs_info set)
gd_target:
    lda gs_m                    // ring slot (31 - m) & 31
    eor #$ff
    and #31
    tay
    lda slot_ofs_lo,y
    sta scr_ptr
    lda slot_ofs_hi,y
    clc
    adc #>(RING_SCR & $ffff)
    sta scr_ptr+1
    lda #(RING_SCR >> 16)
    sta scr_ptr+2
    lda #0
    sta scr_ptr+3
    lda gs_c
    asl
    taz
    lda ((scr_ptr)),z
    tay
    inz
    lda ((scr_ptr)),z
    ldz #0
    cmp #>TILE_CHAR
    bne !no+                    // destroyed already (or not a landscape tile)
    tya
    lsr
    tay
    lda gt_dest,y
    cmp #$ff
    beq !no+
    lda gt_info,y
    sta gs_info
    clc
    rts
!no:
    sec
    rts

// hit on the target in cell (gs_m >> 1, gs_c) with info gs_info; gs_bomb = 1: destroyed at once
gd_hit:
    lda gs_m+1                  // anchor = upper left cell: metarow + row, column - column
    lsr
    sta gd_ma+1
    lda gs_m
    ror
    sta gd_ma
    lda gs_info
    and #2
    lsr
    clc
    adc gd_ma
    sta gd_ma
    bcc !+
    inc gd_ma+1
!:  lda gs_info
    and #1
    sta tmp
    sec
    lda gs_c
    sbc tmp
    sta gd_ca
    lda gs_info
    lsr
    lsr
    sta gd_kind
    lda gs_bomb
    bne gd_destroy
    ldy #GD_DM_N - 1            // damaged before?
!:  lda dm_rlo,y
    cmp gd_ma
    bne !nx+
    lda dm_rhi,y
    cmp gd_ma+1
    bne !nx+
    lda dm_col,y
    cmp gd_ca
    beq !found+
!nx:
    dey
    bpl !-
    ldy dm_next                 // new entry (the oldest is forgotten)
    lda dm_next
    clc
    adc #1
    and #GD_DM_N - 1
    sta dm_next
    lda gd_ma
    sta dm_rlo,y
    lda gd_ma+1
    sta dm_rhi,y
    lda gd_ca
    sta dm_col,y
    ldx gd_kind
    lda gk_hp,x
    sta dm_hp,y
!found:
    ldx gs_x                    // damage carried by the shot
    lda dm_hp,y
    sec
    sbc obj_hp,x
    sta dm_hp,y
    beq !kill+
    bcc !kill+
    lda gd_kind                 // still standing: hit sound (not for every hall tile)
    cmp #GK_HALL
    beq !+
    lda #SFX_HIT
    jsr sfx_play
!:  rts
!kill:
    lda #$ff
    sta dm_rhi,y
    // fall through
// destroy the target with anchor (gd_ma, gd_ca), kind gd_kind
gd_destroy:
    ldx gd_kind
    lda gk_size,x
    sta gd_n
    ldy #0                      // cells (ma - rr, ca + cc)
!rr:
    sty gd_rr
    ldx #0
!cc:
    stx gd_cc
    sec                         // glyph rows 2M (lower half) and 2M + 1 (upper half) of metarow M = ma - rr
    lda gd_ma
    sbc gd_rr
    sta gp_m
    lda gd_ma+1
    sbc #0
    sta gp_m+1
    clc
    lda gd_ca
    adc gd_cc
    sta gp_c
    lda gp_m
    asl
    sta tmp
    lda gp_m+1
    rol
    sta tmp+1
    jsr gd_patch                // in the ring: changed at once
    ror gp_late                 // carry set: not decoded yet
    inc tmp
    jsr gd_patch
    ror gp_late
    lda gp_late
    beq !+
    ldy ov_next                 // remembered for level_row
    lda gp_m
    sta ov_rlo,y
    lda gp_m+1
    sta ov_rhi,y
    lda gp_c
    sta ov_col,y
    iny
    cpy #GD_OV_N
    bcc !ok+
    ldy #0
!ok:
    sty ov_next
!:  lda #0
    sta gp_late
    ldx gd_cc
    inx
    cpx gd_n
    bne !cc-
    ldy gd_rr
    iny
    cpy gd_n
    bne !rr-
    // points, sound, explosion, capsule
    ldy gd_kind
    ldx gk_pts_hi,y
    lda gk_pts_lo,y
    jsr score_add
    lda gd_n
    cmp #2
    bne !small+
    lda #SFX_EXPLODE_BIG
    jsr sfx_play
    lda #FR_EX32_0
    bne !ex+
!small:
    lda #SFX_EXPLODE
    jsr sfx_play
    lda #FR_EX16_0
!ex:
    sta gd_fr
    // upper left corner: x = 16 * ca - 16, y = scroll_px + 184 - 16 * ma
    lda gd_ca
    sec
    sbc #1
    sta sp_x
    lda #0
    sta sp_x+1
    ldy #4
!:  asl sp_x
    rol sp_x+1
    dey
    bne !-
    lda gd_ma
    sta tmp
    lda gd_ma+1
    sta tmp+1
    ldy #4
!:  asl tmp
    rol tmp+1
    dey
    bne !-
    clc
    lda scroll_px
    adc #184
    sta sp_y
    lda scroll_px+1
    adc #0
    sta sp_y+1
    sec
    lda sp_y
    sbc tmp
    sta sp_y
    lda sp_y+1
    sbc tmp+1
    sta sp_y+1
    lda gd_fr
    jsr spawn_explosion
    bcs !+
    lda #1                      // moves with the landscape
    sta obj_a,x
!:  ldx gd_kind
    lda gk_drop,x
    beq !rts+
    sta ko_drop
    lda gd_n                    // centre of the target
    asl
    asl
    asl
    sta tmp
    clc
    lda sp_x
    adc tmp
    sta oc_x
    lda sp_x+1
    adc #0
    sta oc_x+1
    clc
    lda sp_y
    adc tmp
    sta oc_y
    lda sp_y+1
    adc #0
    sta oc_y+1
    lda gs_x
    sta ko_i
    jmp drop_at_oc              // keeps nothing; X = ko_i afterwards
!rts:
    rts
gd_ma:   .word 0
gd_ca:   .byte 0
gd_kind: .byte 0
gd_n:    .byte 0
gd_rr:   .byte 0
gd_cc:   .byte 0
gd_fr:   .byte 0

// cell (glyph row tmp, column gp_c) in the ring: destroyed variant written into both copies of the slot.
// Carry set if the row is not decoded yet (above the ring window (scroll_px >> 3) + 26).
gd_patch:
    lda scroll_px+1
    sta gr_top+1
    lda scroll_px
    ldy #3
!:  lsr gr_top+1
    ror
    dey
    bne !-
    clc
    adc #26
    sta gr_top
    bcc !+
    inc gr_top+1
!:  sec                         // d = top - tmp
    lda gr_top
    sbc tmp
    sta gr_d
    lda gr_top+1
    sbc tmp+1
    bpl !+
    sec                         // negative: not decoded yet
    rts
!:  bne !gone+
    lda gr_d
    cmp #32
    bcs !gone+
    lda tmp                     // slot (31 - row) & 31
    eor #$ff
    and #31
    sta gp_slot
    lda gp_c
    asl
    sta gp_z
    ldx gp_slot
    jsr gp_ptrs
    ldz gp_z
    inz
    lda ((scr_ptr)),z
    cmp #>TILE_CHAR
    bne !done+                  // destroyed already
    dez
    lda ((scr_ptr)),z
    lsr
    tay
    lda gt_dest,y
    cmp #$ff
    beq !done+
    tay                         // variant k: upper half char dk_lo, lower half dk_lo + 1
    lda tmp
    and #1
    eor #1
    clc
    adc dk_lo,y
    sta gp_lo
    lda dk_hi,y
    sta gp_hi
    lda dk_col,y
    sta gp_col
    jsr gp_write
    lda gp_slot
    clc
    adc #RING_SLOTS
    tax
    jsr gp_ptrs
    jsr gp_write
!done:
    ldz #0
!gone:
    clc
    rts

gp_ptrs:                        // scr_ptr / col_ptr -> ring slot X
    lda slot_ofs_lo,x
    sta scr_ptr
    sta col_ptr
    lda slot_ofs_hi,x
    clc
    adc #>(RING_SCR & $ffff)
    sta scr_ptr+1
    lda slot_ofs_hi,x
    clc
    adc #>(RING_COL & $ffff)
    sta col_ptr+1
    lda #(RING_SCR >> 16)
    sta scr_ptr+2
    sta col_ptr+2
    lda #0
    sta scr_ptr+3
    sta col_ptr+3
    rts

gp_write:
    ldz gp_z
    lda gp_lo
    sta ((scr_ptr)),z
    inz
    lda gp_hi
    sta ((scr_ptr)),z
    lda gp_col
    sta ((col_ptr)),z
    ldz #0
    rts
gr_top:  .word 0
gr_d:    .byte 0
gp_m:    .word 0
gp_c:    .byte 0
gp_late: .byte 0
gp_slot: .byte 0
gp_z:    .byte 0
gp_lo:   .byte 0
gp_hi:   .byte 0
gp_col:  .byte 0

// bomb: every destroyable target on the screen goes (glyph rows scroll_px >> 3 .. + 25)
gd_bomb:
    lda scroll_px+1
    sta gs_m+1
    lda scroll_px
    ldy #3
!:  lsr gs_m+1
    ror
    dey
    bne !-
    sta gs_m
    lda #26
    sta gb_n
!row:
    lda #1
    sta gs_c
!col:
    jsr gd_target
    bcs !+
    lda #1
    sta gs_bomb
    lda #0
    sta gs_x
    jsr gd_hit
!:  inc gs_c
    lda gs_c
    cmp #BG_TOKENS
    bne !col-
    inc gs_m
    bne !+
    inc gs_m+1
!:  dec gb_n
    bne !row-
    rts
gb_n: .byte 0

// ============================================================== ground guns
// level event: gun of kind A (0 light, 1 heavy) at x = ev_p+1/+2, above the screen
gun_spawn:
    sta gu_k
    lda ev_p+1
    sta sp_x
    lda ev_p+2
    sta sp_x+1
    lda #<-32
    sta sp_y
    lda #>-32
    sta sp_y+1
    ldx #GROUND_FIRST
    lda #GROUND_END
    sta ob_end
    jsr alloc_slot
    bcs !+
    lda #T_GUN
    jsr init_slot
    lda gu_k
    sta obj_kind,x
    lda #1
    sta obj_b,x                 // alive
    lda #4
    sta obj_a,x                 // pointing south
    lda #0
    sta obj_wave,x
    lda #60
    sta obj_t,x
    ldy #GUN_HP_LIGHT
    lda gu_k
    beq !l+
    ldy #GUN_HP_HEAVY
!l: tya
    sta obj_hp,x
    jsr gun_frame
!:  rts
gu_k: .byte 0

gun_frame:
    lda obj_b,x
    bne !+
    lda #FR_GUN_WRECK
    ldy obj_kind,x
    beq !st+
    lda #FR_HGUN_WRECK
    bne !st+
!:  lda obj_a,x
    ldy obj_kind,x
    beq !l+
    clc
    adc #FR_HGUN0
    bne !st+
!l: clc
    adc #FR_GUN0
!st:
    sta obj_fr,x
    rts

upd_gun:
    lda scroll_delta            // moves with the landscape
    jsr move_down
    lda obj_type,x
    bne !+
    rts
!:  lda obj_wave,x
    beq !+
    dec obj_wave,x
!:  lda obj_b,x
    bne !+
    rts                         // wreck
!:  lda pl_state                // no aiming at a destroyed player
    ora obj_yh,x                // only on the screen (y 0..170)
    beq !+
    jmp gun_frame
!:  lda obj_yl,x
    cmp #170
    bcc !+
    jmp gun_frame
!:
    // direction to the player: (player centre - gun centre) / 4 -> vec_dir
    ldy obj_fr,x
    clc
    lda obj_xl,x
    adc frame_hit_cx,y
    sta tmp
    lda obj_xh,x
    adc #0
    sta tmp+1
    clc
    lda pl_x
    adc #PL_HIT_CX
    sta tmp2
    lda pl_x+1
    adc #0
    sta tmp2+1
    sec
    lda tmp2
    sbc tmp
    sta tmp
    lda tmp2+1
    sbc tmp+1
    cmp #$80                    // / 4, signed
    ror
    ror tmp
    cmp #$80
    ror
    ror tmp
    lda tmp
    sta ms_sx
    clc
    lda obj_yl,x
    adc frame_hit_cy,y
    sta tmp
    lda pl_y
    clc
    adc #PL_HIT_CY
    sec
    sbc tmp
    sta tmp                     // both 0..255: difference as 9 bit (carry = no borrow)
    lda #0
    sbc #0
    cmp #$80
    ror
    ror tmp
    cmp #$80
    ror
    ror tmp
    lda tmp
    sta ms_sy
    jsr vec_dir                 // keeps X; A = 0..7 or $ff
    bpl !+
    jmp gun_frame
!:
    sta gu_t
    lda obj_t,x                 // fire timer
    beq !+
    dec obj_t,x
!:
    lda gu_t
    sec
    sbc obj_a,x
    and #7
    beq !fire+                  // pointing at the player
    tay
    lda frame_lo                // turn one step every 8 frames
    and #7
    bne !frame+
    cpy #4
    bcc !right+
    dec obj_a,x
    jmp !wrap+
!right:
    inc obj_a,x
!wrap:
    lda obj_a,x
    and #7
    sta obj_a,x
    jmp !frame+
!fire:
    lda obj_t,x
    bne !frame+
    jsr random                  // next shot: light 1.2-2.5 s, heavy 1-2.3 s
    and #63
    clc
    adc #60
    ldy obj_kind,x
    beq !+
    sbc #10
!:  sta obj_t,x
    lda #6
    sta obj_wave,x
    jsr gun_frame               // the shot leaves from the current view
    lda #K_SHOT_RED
    jsr spawn_eshot_a           // keeps X
    ldy es_slot
    bmi !frame+
    jsr aim_shot
    lda obj_kind,x
    beq !frame+
    lda #K_SHOT_RED             // heavy: a second shot, slightly to the side
    jsr spawn_eshot_a
    ldy es_slot
    bmi !frame+
    jsr aim_shot
    lda obj_a,y
    clc
    adc #12
    sta obj_a,y
!frame:
    jmp gun_frame
gu_t: .byte 0

// gun X destroyed (shot, missile, bomb): wreck, explosion, points
gun_down:
    lda #0
    sta obj_b,x
    sta obj_wave,x
    stx gd_x
    jsr gun_frame
    lda obj_xl,x
    sta sp_x
    lda obj_xh,x
    sta sp_x+1
    lda obj_yl,x
    sta sp_y
    lda obj_yh,x
    sta sp_y+1
    lda obj_kind,x
    bne !heavy+
    lda #SFX_EXPLODE
    jsr sfx_play
    ldx #$03                    // 300 points
    lda #$00
    jsr score_add
    lda #FR_EX16_0
    bne !ex+
!heavy:
    lda #SFX_EXPLODE_BIG
    jsr sfx_play
    ldx #$10                    // 1000 points
    lda #$00
    jsr score_add
    lda #FR_EX32_0
!ex:
    jsr spawn_explosion
    bcs !+
    lda #1                      // moves with the landscape
    sta obj_a,x
!:  ldx gd_x
    rts
gd_x: .byte 0

// objects_draw, after object X: muzzle flash of a gun (16x16, centred on the barrel tip)
gun_flash_draw:
    lda obj_type,x
    cmp #T_GUN
    bne !rts+
    lda obj_wave,x
    beq !rts+
    ldy obj_a,x
    lda obj_kind,x
    bne !h+
    lda gun_mz_x,y
    sta tmp
    lda gun_mz_y,y
    sta tmp+1
    lda #FR_GUN_FLASH0
    bne !go+
!h: lda hgun_mz_x,y
    sta tmp
    lda hgun_mz_y,y
    sta tmp+1
    lda #FR_GUN_FLASH0          // the light gun's flash (Stage 8b: pixie room for the shot views)
!go:
    sta gf_fr
    lda obj_wave,x              // two phases
    and #2
    lsr
    clc
    adc gf_fr
    sta gf_fr
    ldy #0
    lda tmp
    bpl !+
    dey
!:  clc
    adc obj_xl,x
    sta px_x
    tya
    adc obj_xh,x
    sta px_x+1
    ldy #0
    lda tmp+1
    bpl !+
    dey
!:  clc
    adc obj_yl,x
    sta px_y
    tya
    adc obj_yh,x
    sta px_y+1
    ldy gf_fr
    lda frame_pal,y
    sta px_pal
    tya
    jsr pixie_draw
    ldx ob_i
!rts:
    rts
gf_fr: .byte 0
