// ----------------------------------------------------------------------------
// Level files and level runtime (format: docs/level_json.md, tools/build_level.py)
//
//   LnGFX  'SG', glyph count, 4 landscape palettes (192 bytes), landscape glyphs
//   LnDAT  'SL' header, metatiles, row dictionary, row list, events, formations, paths
//
// Both are SEQ files on the disk. They are loaded with the KERNAL before the game
// takes over the machine (Vyper rules: SETBNK before SETNAM, CHRIN/READST loop,
// CLRCHN/CLOSE), through a 256-byte bank-0 buffer and DMA to LEVEL_BUF ($50000).
// The GFX file is unpacked at once (glyphs to TILE_ADDR, palettes to lev_pal),
// then the DAT file is loaded to LEVEL_BUF and stays there for the whole level.
// ----------------------------------------------------------------------------
.const LEVEL_BUF   = $050000
.const LEVEL_MAX   = $4000
.const LEVEL_DAT_MAX = $2800    // LnDAT stays at $50000-$527FF (build_level.py MAX_DAT)
.const SETLFS = $ffba
.const SETNAM = $ffbd
.const SETBNK = $ff6b
.const OPEN   = $ffc0
.const CLOSE  = $ffc3
.const CHKIN  = $ffc6
.const CLRCHN = $ffcc
.const CHRIN  = $ffcf
.const READST = $ffb7
.const CHROUT = $ffd2

.const EV_FORMATION = 1
.const EV_GROUND    = 2
.const EV_SPEED     = 3
.const EV_SHOP      = 4
.const EV_BOSS      = 5
.const EV_END       = 6
.const OP_END = $80
.const OP_LOOP = $81
.const OP_ENDLOOP = $82
.const OP_AIM = $83
.const OP_FIRE = $84
.const OP_WAIT = $85

.label lev_ptr = $72        // 32-bit pointer into LEVEL_BUF
.encoding "petscii_upper"

// ============================================================== loading (KERNAL)
// Called before anything else, in BASIC's environment. Carry set = failed
// (a message has been printed).
load_device:
    lda $ba                     // device of the last LOAD (Vyper: capture_device)
    cmp #8
    bcs !+
    lda #8
!:  sta ld_device
    rts

level_load:
    lda #<name_gfx
    ldx #>name_gfx
    ldy #name_gfx_end - name_gfx
    jsr load_seq
    bcc !+
    jmp !fail+
!:
    RunDma(job_gfxhdr)          // header + palettes to bank 0
    lda lev_gfxhdr
    cmp #$53                    // 'S'
    bne !bad+
    lda lev_gfxhdr+1
    cmp #$47                    // 'G'
    bne !bad+
    lda lev_gfxhdr+2            // glyph count * 64 = glyph bytes
    sta job_glyphs+DMA_COUNT+1  // * 256 / 4: shift the count left by 6
    lda #0
    sta job_glyphs+DMA_COUNT
    lsr job_glyphs+DMA_COUNT+1
    ror job_glyphs+DMA_COUNT
    lsr job_glyphs+DMA_COUNT+1
    ror job_glyphs+DMA_COUNT
    RunDma(job_glyphs)
    jsr dest_load               // destroyed tiles (ground.asm), through the load buffer
    bcc !+
    jmp !fail+
!:
    lda #<name_dat
    ldx #>name_dat
    ldy #name_dat_end - name_dat
    jsr load_seq
    bcs !fail+
    RunDma(job_dathdr)
    lda lev_hdr
    cmp #$53                    // 'S'
    bne !bad+
    lda lev_hdr+1
    cmp #$4c                    // 'L'
    bne !bad+
    clc
    rts
!bad:
    lda #<msg_bad
    ldx #>msg_bad
    jsr print
!fail:
    sec
    rts

// A/X = file name, Y = length. Loads to LEVEL_BUF (max. LEVEL_MAX bytes). Carry set on error (message printed).
load_seq:
    pha
    lda #<(LEVEL_BUF & $ffff)
    sta ld_dst
    lda #>(LEVEL_BUF & $ffff)
    sta ld_dst+1
    lda #(LEVEL_BUF >> 16)
    sta ld_dst+2
    lda #0
    sta ld_dst+3
    lda #>LEVEL_MAX
    sta ld_maxhi
    pla
// same, destination ld_dst (low 16 bits, bank 0-15, megabyte: 0 chip RAM / $80 attic RAM; must not
// cross a 64 KB boundary), at most ld_maxhi * 256 bytes
load_seq_to:
    sta ld_name
    stx ld_name+1
    sty ld_len
    lda #0
    sta ld_x
    sta ld_total
    sta ld_total+1
    lda ld_dst                  // DMA destination of the first block
    sta job_ldflush+DMA_DST
    lda ld_dst+1
    sta job_ldflush+DMA_DST+1
    lda ld_dst+2
    sta job_ldflush+DMA_DST+2
    lda ld_dst+3
    sta job_ldflush+DMA_DSTMB
    lda #2
    ldx ld_device
    ldy #2
    jsr SETLFS
    lda #0
    ldx #0
    jsr SETBNK                  // file name in bank 0 (Vyper rule)
    lda ld_len
    ldx ld_name
    ldy ld_name+1
    jsr SETNAM
    jsr OPEN
    bcs !err+
    ldx #2
    jsr CHKIN
    bcs !err+
!byte:
    jsr CHRIN
    ldx ld_x
    sta ld_buf,x
    inc ld_x
    jsr READST
    sta ld_st
    and #$bf                    // anything but EOF is an error
    bne !err+
    lda ld_x
    bne !+
    jsr ld_flush                // 256 bytes collected
    bcs !err+
!:  lda ld_st
    and #$40
    beq !byte-
    lda ld_x                    // EOF: write the rest
    beq !+
    jsr ld_flush
    bcs !err+
!:  jsr CLRCHN
    lda #2
    jsr CLOSE
    lda ld_total
    ora ld_total+1
    beq !err2+
    clc
    rts
!err:
    jsr CLRCHN
    lda #2
    jsr CLOSE
!err2:
    lda #<msg_load
    ldx #>msg_load
    jsr print
    lda ld_name                 // file name
    sta ld_char+1
    lda ld_name+1
    sta ld_char+2
    lda #0
    sta ld_x
ld_char:
    lda $ffff
    jsr CHROUT
    inc ld_char+1
    bne !+
    inc ld_char+2
!:  inc ld_x
    lda ld_x
    cmp ld_len
    bne ld_char
    lda #13
    jsr CHROUT
    sec
    rts

// copy ld_x bytes (0 = 256) from ld_buf to the next destination
ld_flush:
    lda ld_x
    sta job_ldflush+DMA_COUNT
    lda #0
    sta job_ldflush+DMA_COUNT+1
    lda ld_x
    bne !+
    inc job_ldflush+DMA_COUNT+1
!:  RunDma(job_ldflush)
    clc
    lda job_ldflush+DMA_DST
    adc job_ldflush+DMA_COUNT
    sta job_ldflush+DMA_DST
    lda job_ldflush+DMA_DST+1
    adc job_ldflush+DMA_COUNT+1
    sta job_ldflush+DMA_DST+1
    clc
    lda ld_total
    adc job_ldflush+DMA_COUNT
    sta ld_total
    lda ld_total+1
    adc job_ldflush+DMA_COUNT+1
    sta ld_total+1
    cmp ld_maxhi                // file too big for the destination
    bcs !+
    lda #0
    sta ld_x
    clc
    rts
!:  sec
    rts

print:                          // A/X = zero-terminated text
    sta pr_char+1
    stx pr_char+2
pr_char:
    lda $ffff
    beq !+
    jsr CHROUT
    inc pr_char+1
    bne pr_char
    inc pr_char+2
    bne pr_char
!:  rts

ld_device: .byte 8
ld_name:   .word 0
ld_len:    .byte 0
ld_x:      .byte 0
ld_st:     .byte 0
ld_total:  .word 0
ld_dst:    .fill 4, 0
ld_maxhi:  .byte 0
name_gfx:  .text "L1GFX,S,R"
name_gfx_end:
name_dat:  .text "L1DAT,S,R"
name_dat_end:
msg_load:  .text "SHOOTER65: CANNOT LOAD "
           .byte 0
msg_bad:   .text "SHOOTER65: LEVEL FILE DAMAGED"
           .byte 13, 0

job_ldflush: DmaJob(DMA_CMD_COPY, ld_buf, LEVEL_BUF, 256)
job_gfxhdr:  DmaJob(DMA_CMD_COPY, LEVEL_BUF, lev_gfxhdr, 4 + 192)
job_glyphs:  DmaJob(DMA_CMD_COPY, LEVEL_BUF + 4 + 192, TILE_ADDR, 0)
job_dathdr:  DmaJob(DMA_CMD_COPY, LEVEL_BUF, lev_hdr, 40)

// ============================================================== runtime
// read the byte at offset tmp2 (16 bit) of the level data
lev_read:
    lda tmp2
    sta lev_ptr
    lda tmp2+1
    clc
    adc #>(LEVEL_BUF & $ffff)
    sta lev_ptr+1
    lda #(LEVEL_BUF >> 16)
    sta lev_ptr+2
    lda #0
    sta lev_ptr+3
    ldz #0
    lda ((lev_ptr)),z
    rts

// header fields (copied from lev_hdr)
.label lev_nmeta  = lev_hdr+3
.label lev_nrows  = lev_hdr+4
.label lev_offmeta = lev_hdr+6
.label lev_offdict = lev_hdr+8
.label lev_offrows = lev_hdr+10
.label lev_offev  = lev_hdr+12
.label lev_offform = lev_hdr+14
.label lev_offptab = lev_hdr+16
.label lev_speed  = lev_hdr+18
.label lev_offgt  = lev_hdr+21       // Stage 8: ground-target tables (format 2)
.label lev_ndest  = lev_hdr+23

level_init:
    // metatile table -> meta_top / meta_bot / meta_col
    lda lev_offmeta
    sta tmp2
    lda lev_offmeta+1
    sta tmp2+1
    ldx #0
!:  jsr lev_read
    sta meta_top,x
    jsr lev_inc
    jsr lev_read
    sta meta_bot,x
    jsr lev_inc
    jsr lev_read
    sta meta_col,x
    jsr lev_inc
    inx
    cpx lev_nmeta
    bne !-
    jsr gd_tables               // destroyable tiles (ground.asm)
level_restart:
    jsr gd_reset
    lda lev_speed
    sta scroll_spd
    lda lev_speed+1
    sta scroll_spd+1
    lda lev_offev
    sta lev_evp
    lda lev_offev+1
    sta lev_evp+1
    lda #0
    sta lev_base
    sta lev_base+1
    sta shop_req
    rts

lev_inc:
    inc tmp2
    bne !+
    inc tmp2+1
!:  rts

// Fill dr_glyph / dr_col for glyph row tmp (16 bit). Uses tmp2, lev_t.
level_row:
    lda tmp
    and #1
    sta lev_half                // 0 = lower half of the metatile row (rows count upwards)
    lda tmp+1                   // metarow = glyph row / 2
    lsr
    sta lev_t+1
    lda tmp
    ror
    sta lev_t
!wrap:                          // metarow modulo number of rows (the level repeats after its end)
    lda lev_t
    sec
    sbc lev_nrows
    tay
    lda lev_t+1
    sbc lev_nrows+1
    bcc !ok+
    sta lev_t+1
    sty lev_t
    jmp !wrap-
!ok:
    clc                         // dictionary index = rows[metarow]
    lda lev_offrows
    adc lev_t
    sta tmp2
    lda lev_offrows+1
    adc lev_t+1
    sta tmp2+1
    jsr lev_read
    sta lev_t                   // index * 21 = index * 16 + index * 4 + index
    lda #0
    sta lev_t+1
    lda lev_t
    sta lev_m
    lda #0
    sta lev_m+1
    ldy #2
!:  asl lev_m
    rol lev_m+1
    dey
    bne !-
    clc                         // lev_t += index*4
    lda lev_t
    adc lev_m
    sta lev_t
    lda lev_t+1
    adc lev_m+1
    sta lev_t+1
    asl lev_m
    rol lev_m+1
    asl lev_m
    rol lev_m+1
    clc                         // + index*16
    lda lev_t
    adc lev_m
    sta lev_t
    lda lev_t+1
    adc lev_m+1
    sta lev_t+1
    clc
    lda lev_offdict
    adc lev_t
    sta tmp2
    lda lev_offdict+1
    adc lev_t+1
    sta tmp2+1
    ldx #0
!col:
    jsr lev_read
    tay
    lda lev_half
    bne !top+
    lda meta_bot,y
    jmp !st+
!top:
    lda meta_top,y
!st:
    sta dr_glyph,x
    lda meta_col,y
    sta dr_col,x
    lda #>TILE_CHAR
    sta dr_hi,x
    jsr lev_inc
    inx
    cpx #BG_TOKENS
    bne !col-
    jmp gd_apply                // destroyed buildings (ground.asm)

// ---------------------------------------------------------------- events
// Called once per frame: run every event whose row has been reached by the top of the screen.
level_events:
    // top metarow = ((scroll_px >> 3) + 25) >> 1, relative to the start of the current pass
    lda scroll_px+1
    sta lev_t+1
    lda scroll_px
    lsr lev_t+1
    ror
    lsr lev_t+1
    ror
    lsr lev_t+1
    ror
    clc
    adc #25
    sta lev_t
    bcc !+
    inc lev_t+1
!:  lsr lev_t+1
    ror lev_t
    sec
    lda lev_t
    sbc lev_base
    sta lev_t
    lda lev_t+1
    sbc lev_base+1
    sta lev_t+1
!next:
    lda lev_evp
    sta tmp2
    lda lev_evp+1
    sta tmp2+1
    jsr lev_read                // event row
    sta lev_m
    jsr lev_inc
    jsr lev_read
    sta lev_m+1
    and lev_m                   // $ffff = no more events
    cmp #$ff
    beq !done+
    lda lev_t                   // row > top metarow: not yet
    cmp lev_m
    lda lev_t+1
    sbc lev_m+1
    bcc !done+
    ldx #0                      // type + 5 parameters
!:  jsr lev_inc
    jsr lev_read
    sta ev_type,x
    inx
    cpx #6
    bne !-
    clc
    lda lev_evp
    adc #8
    sta lev_evp
    bcc !+
    inc lev_evp+1
!:  jsr ev_run
    lda ev_type                 // after the level end the event list starts again: the
    cmp #EV_END                 // position must be recomputed against the new base first
    beq !done+                  // (otherwise every event runs again at once, endlessly)
    jmp !next-
!done:
    rts

ev_run:
    lda ev_type
    cmp #EV_FORMATION
    bne !+
    jmp ev_formation
!:  cmp #EV_GROUND
    bne !+
    jmp ev_ground
!:  cmp #EV_SPEED
    bne !+
    lda ev_p
    sta scroll_spd
    lda ev_p+1
    sta scroll_spd+1
    rts
!:  cmp #EV_SHOP
    bne !+
#if SKIP_SHOP
    lda ev_p                    // test build (build.py --define SKIP_SHOP): no shops, the checkpoint stays
    bne ev_noshop               // (named: an anonymous label would capture "bne !+" above)
    jmp cp_save
ev_noshop:
    rts
#endif
    lda ev_p                    // 0 mid, 1 end -> shop_req 1 / 2
    clc
    adc #1
    sta shop_req
    rts
!:  cmp #EV_END
    bne !+
    lda #MUS_LEVEL_CLEAR        // level end: fanfare, then the level music again
    jsr music_play
    lda #MUS_LEVEL1
    jsr music_queue
    lda attic_ok                // Stage 9: with attic RAM the next level follows (levels.asm, main loop)
    beq !repeat+                // (named: an anonymous label here would capture "bne !+" above)
    lda #1
    sta level_next_req
    rts
!repeat:
    clc                         // level end: the map repeats, events start again
    lda lev_base
    adc lev_nrows
    sta lev_base
    lda lev_base+1
    adc lev_nrows+1
    sta lev_base+1
    lda lev_offev
    sta lev_evp
    lda lev_offev+1
    sta lev_evp+1
    rts
!:  cmp #EV_BOSS
    bne !+
    lda #1                      // boss.asm takes over when the sky is clear
    sta boss_req
!:  rts

ev_ground:
    lda ev_p                    // 4 tank/speedboat, 5 patrol boat, 6 frigate, 8 light gun, 9 heavy gun (GROUND)
    cmp #8
    bcc !tank+
    sbc #8
    jmp gun_spawn               // ground.asm
!tank:
    lda ev_p+1
    sta sp_x
    lda ev_p+2
    sta sp_x+1
    ldy ev_p                    // just above the top edge: 16 / 32 / 64 high (Stage 13b: ships glide in)
    lda gr_y-4,y
    sta sp_y
    lda #$ff
    sta sp_y+1
    ldx #GROUND_FIRST
    lda #GROUND_END
    sta ob_end
    jsr alloc_slot
    bcs !+
    lda #T_TANK
    jsr init_slot
    ldy ev_p
    lda gr_kind-4,y
    tay
    jsr set_kind
    lda ev_p+3
    sta obj_b,x                 // direction
    lda #0
    sta obj_wave,x
    jsr tank_frame
    jmp ship_guns               // ships (Stage 13): hit points, guns
!:  rts
gr_kind: .byte K_TANK, K_BOMBER, K_ARMOURED     // level 3: speedboat, patrol boat, frigate (enemy set slots)
gr_y:    .byte <-16, <-32, <-64

ev_formation:
    // formation record: kind, count, path, delay, x (16), y (16)
    lda ev_p                    // * 8
    sta tmp2
    lda #0
    sta tmp2+1
    ldy #3
!:  asl tmp2
    rol tmp2+1
    dey
    bne !-
    clc
    lda tmp2
    adc lev_offform
    sta tmp2
    lda tmp2+1
    adc lev_offform+1
    sta tmp2+1
    ldx #0
!:  jsr lev_read
    sta fm_rec,x
    jsr lev_inc
    inx
    cpx #8
    bne !-
    lda ev_p+3                  // x given in the event?
    and #2
    beq !+
    lda ev_p+1
    sta fm_x
    lda ev_p+2
    sta fm_x+1
!:  lda ev_p+3
    and #1
    sta fm_mirror
    beq !+
    ldy fm_kind                 // mirrored: x = 320 - width - x
    ldx kind_frame,y
    lda frame_w,x
    asl
    asl
    asl
    asl
    sta tmp
    sec
    lda #<320
    sbc tmp
    sta tmp
    lda #>320
    sbc #0
    sta tmp+1
    sec
    lda tmp
    sbc fm_x
    sta fm_x
    lda tmp+1
    sbc fm_x+1
    sta fm_x+1
!:  // path start offset
    lda fm_path
    asl
    clc
    adc lev_offptab
    sta tmp2
    lda lev_offptab+1
    adc #0
    sta tmp2+1
    jsr lev_read
    sta fm_pc
    jsr lev_inc
    jsr lev_read
    sta fm_pc+1
    // formation bookkeeping (capsule when all are shot down)
    ldx wave_seq
    lda #0
    sta wave_kills,x
    lda fm_count
    sta wave_count,x
    lda #0
    sta fm_i
    sta fm_dly
!member:
    lda fm_x
    sta sp_x
    lda fm_x+1
    sta sp_x+1
    lda fm_y
    sta sp_y
    lda fm_y+1
    sta sp_y+1
    ldx #AIR_FIRST
    lda #AIR_END
    sta ob_end
    jsr alloc_slot
    bcs !full+
    lda #T_AIR
    jsr init_slot
    ldy fm_kind
    jsr set_kind
    lda wave_seq
    sta obj_wave,x
    lda fm_pc
    sta obj_pcl,x
    lda fm_pc+1
    sta obj_pch,x
    lda fm_dly
    sta obj_dly,x
    lda fm_mirror
    sta obj_mir,x
    lda #0
    sta obj_cnt,x
    sta obj_xf,x
    sta obj_yf,x
    sta obj_lpn,x
    sta obj_aim,x
    clc
    lda fm_dly
    adc fm_delay
    sta fm_dly
    inc fm_i
    lda fm_i
    cmp fm_count
    bne !member-
    jmp !next+
!full:
    ldx wave_seq                // not all members fitted: no formation capsule
    lda #$ff
    sta wave_count,x
!next:
    lda wave_seq
    clc
    adc #1
    and #3
    sta wave_seq
    rts

// ---------------------------------------------------------------- path interpreter
// Air object X: next path command(s) until a timed command is found.
path_fetch:
    lda #12                     // safety: at most 12 commands per call
    sta pf_guard
!cmd:
    lda obj_pcl,x
    sta tmp2
    lda obj_pch,x
    sta tmp2+1
    jsr lev_read
    cmp #$80
    bcs !op+
    // move: frames, dx, dy (1/4 px per frame)
    sta obj_cnt,x
    jsr lev_inc
    jsr lev_read
    ldy obj_mir,x
    beq !+
    eor #$ff
    clc
    adc #1
!:  sta obj_a,x
    jsr lev_inc
    jsr lev_read
    sta obj_b,x
    lda #0
    sta obj_aim,x
    lda #3
    jmp pf_advance
!op:
    cmp #OP_END                 // keep the current velocity forever
    bne !+
    lda #255
    sta obj_cnt,x
    rts
!:  cmp #OP_LOOP
    bne !+
    jsr lev_inc
    jsr lev_read
    bne !n+
    lda #1
!n: sta obj_lpn,x
    clc                         // loop start = after this command
    lda obj_pcl,x
    adc #2
    sta obj_lpl,x
    lda obj_pch,x
    adc #0
    sta obj_lph,x
    lda #2
    jsr pf_skip
    jmp !again+
!:  cmp #OP_ENDLOOP
    bne !+
    dec obj_lpn,x
    beq !out+
    lda obj_lpl,x
    sta obj_pcl,x
    lda obj_lph,x
    sta obj_pch,x
    jmp !again+
!out:
    lda #1
    jsr pf_skip
    jmp !again+
!:  cmp #OP_AIM
    bne !+
    jsr lev_inc
    jsr lev_read
    sta obj_cnt,x
    jsr lev_inc
    jsr lev_read
    sta obj_aim,x
    lda #3
    jmp pf_advance
!:  cmp #OP_FIRE
    bne !+
    lda #1
    jsr pf_skip
    lda pl_state
    bne !again+
    jsr spawn_eshot             // keeps X
    jmp !again+
!:  cmp #OP_WAIT
    bne !bad+
    jsr lev_inc
    jsr lev_read
    sta obj_cnt,x
    lda #0
    sta obj_a,x
    sta obj_b,x
    sta obj_aim,x
    lda #2
    jmp pf_advance
!bad:
    lda #255                    // unknown command: just keep flying
    sta obj_cnt,x
    rts
!again:
    dec pf_guard
    beq !+
    jmp !cmd-
!:  rts

pf_advance:                     // pc += A, done
    jsr pf_skip
    lda obj_cnt,x
    bne !+
    lda #1
    sta obj_cnt,x
!:  rts
pf_skip:                        // pc += A
    clc
    adc obj_pcl,x
    sta obj_pcl,x
    bcc !+
    inc obj_pch,x
!:  rts

// ---------------------------------------------------------------- data
lev_gfxhdr: .fill 4, 0
lev_pal:    .fill 192, 0         // banks 1-4: R[16] G[16] B[16] each, nibble-swapped
lev_hdr:    .fill 40, 0                 // Stage 17c: 40 bytes (whitecaps at +32)
lev_evp:    .word 0
lev_base:   .word 0
lev_t:      .word 0
lev_m:      .word 0
lev_half:   .byte 0
shop_req:   .byte 0              // 1 = mid-level shop, 2 = end-of-level shop reached (overlay: later stage)
scroll_spd: .word $0080
ev_type:    .byte 0
ev_p:       .fill 5, 0
fm_rec:
fm_kind:    .byte 0
fm_count:   .byte 0
fm_path:    .byte 0
fm_delay:   .byte 0
fm_x:       .word 0
fm_y:       .word 0
fm_pc:      .word 0
fm_mirror:  .byte 0
fm_i:       .byte 0
fm_dly:     .byte 0
pf_guard:   .byte 0
dr_glyph:   .fill BG_TOKENS, 0
dr_col:     .fill BG_TOKENS, 0
dr_hi:      .fill BG_TOKENS, 0
.align $100
ld_buf:     .fill 256, 0
meta_top:   .fill 256, 0
meta_bot:   .fill 256, 0
meta_col:   .fill 256, 0
