// ----------------------------------------------------------------------------
// Sound (Stage 5): music player and sound effects, data from the file MUSIC
// (tools/build_music.py, format: docs/music_json.md), loaded to MUSIC_ADDR (bank 0, $A000).
//
// Music: SID 1 ($D400), mirrored to SID 3 ($D440) so it sounds from the middle
// (by default SIDs 1/2 are panned slightly right, 3/4 slightly left).
// Effects: SID 2 ($D420), mirrored to SID 4 ($D460). Three voices each.
//
// Music timing: every `tempo` frames a pattern row starts (tick 0). Two frames
// earlier (tick tempo-2) the next row is decoded; a voice that will start a new
// note (not legato) gets a hard restart then: gate off, ADSR 0, so the envelope
// starts cleanly. Per frame: wave table or arpeggio, vibrato, pulse sweep.
// ----------------------------------------------------------------------------
.label mu_ptr = $76             // 32-bit pointer into the music data (bank 5)

.const SID_M  = $d400           // music
.const SID_M2 = $d440
.const SID_S  = $d420           // effects
.const SID_S2 = $d460

.errorif ((MUSIC_ADDR >> 16) != 0 || MUSIC_ADDR + MUSIC_BYTES > $c000), "music data must be in bank 0 below $C000"
.errorif (prg_end > MUSIC_ADDR), "the program has grown into the music data at MUSIC_ADDR"

// ---------------------------------------------------------------- loading (KERNAL)
// file MUSIC: copied as a whole to MUSIC_ADDR. Carry set = failed (message printed).
music_load:
    lda #<name_music
    ldx #>name_music
    ldy #name_music_end - name_music
    jsr load_seq
    bcs !fail+
    RunDma(job_music)
    lda #<MUSIC_ADDR            // check the 'SM' signature in bank 5
    sta mu_ptr
    lda #>MUSIC_ADDR
    sta mu_ptr+1
    lda #(MUSIC_ADDR >> 16)
    sta mu_ptr+2
    lda #0
    sta mu_ptr+3
    ldz #0
    lda ((mu_ptr)),z
    cmp #$53
    bne !bad+
    inz
    lda ((mu_ptr)),z
    ldz #0
    cmp #$4d
    bne !bad+
    clc
    rts
!bad:
    ldz #0
    lda #<msg_bad
    ldx #>msg_bad
    jsr print
!fail:
    sec
    rts

// ---------------------------------------------------------------- init / off
sound_init:
    jsr sound_off
    lda #(MUSIC_ADDR >> 16)
    sta mu_ptr+2
    lda #0
    sta mu_ptr+3
    sta mu_playing
    sta s_active
    sta s_active+1
    sta s_active+2
    lda #$ff
    sta mu_next
// effects SIDs: full volume, no filter (Stage 18c: also after kernal_leave - sound_off clears it)
sfx_volume:
    lda #$0f
    sta SID_S+$18
    sta SID_S2+$18
    rts

// all four SIDs silent (also used on the way back to BASIC)
sound_off:
    lda #0
    ldx #$7f
!:  sta $d400,x
    dex
    bpl !-
    rts

// ---------------------------------------------------------------- music control
// A = piece (MUS_*): start it from the beginning (X and Y are kept)
music_play:
    phx
    phy
    asl
    clc
    adc #<(MUSIC_ADDR + 4)
    sta mu_ptr
    lda #>(MUSIC_ADDR + 4)
    adc #0
    sta mu_ptr+1
    jsr mu_read16               // piece header address
    sta mu_ptr
    stx mu_ptr+1
    ldz #0
    ldy #0
!:  lda ((mu_ptr)),z            // copy the 20-byte header
    sta mu_hdr,y
    inz
    iny
    cpy #20
    bne !-
    ldz #0
    lda #0
    sta mu_playing
    sta mu_routing
    sta mu_ended
    ldx #2
!v: lda #0
    sta v_gate,x
    sta v_wait,x
    sta v_pend,x
    sta v_inst,x
    sta v_wtlen,x
    sta v_arplen,x
    sta v_vdepth,x
    sta v_swlo,x
    sta v_swhi,x
    lda #$ff                    // order position -1: the first decode loads entry 0
    sta v_ord,x
    jsr mu_hardrestart
    jsr mu_next_pattern
    dex
    bpl !v-
    // filter and volume
    lda mu_hdr+2
    sta SID_M+$15
    sta SID_M2+$15
    lda mu_hdr+3
    sta SID_M+$16
    sta SID_M2+$16
    lda mu_hdr+4
    sta SID_M+$17
    sta SID_M2+$17
    lda mu_hdr+5
    ora mu_hdr+1
    sta SID_M+$18
    sta SID_M2+$18
    lda mu_hdr                  // hard restart two frames before each row
    sec
    sbc #2
    sta mu_hrtick
    ldx #2                      // first row now, applied in the next frame
!:  jsr mu_decode
    dex
    bpl !-
    lda mu_hdr
    sec
    sbc #1
    sta mu_tick
    lda #1
    sta mu_playing
    ply
    plx
    rts

// A = piece to start when the current (non-looping) piece has ended; $ff = none
music_queue:
    sta mu_next
    rts

music_stop:
    lda #0
    sta mu_playing
    ldx #2
!:  ldy v_sidofs,x
    lda #0
    sta v_gate,x
    lda v_wave,x
    sta SID_M+4,y
    sta SID_M2+4,y
    dex
    bpl !-
    rts

// ---------------------------------------------------------------- per frame
sound_frame:
    jsr music_frame
    jmp sfx_frame

music_frame:
    lda mu_playing
    bne !+
    rts
!:  inc mu_tick
    lda mu_tick
    cmp mu_hdr                  // tempo
    bcc !+
    lda #0
    sta mu_tick
!:  lda mu_tick
    bne !+
    ldx #2                      // tick 0: the decoded row starts
!a: jsr mu_apply
    dex
    bpl !a-
!:  lda mu_tick
    cmp mu_hrtick
    bne !+
    lda #0
    sta mu_ended
    ldx #2                      // decode the next row (hard restart for new notes)
!d: jsr mu_decode
    dex
    bpl !d-
    lda mu_ended
    beq !+
    jmp mu_finished
!:  ldx #2
!e: jsr mu_effects
    dex
    bpl !e-
    rts

// the piece reached its end (no loop): release, then the queued piece
mu_finished:
    jsr music_stop
    lda mu_next
    bmi !+
    ldx #$ff
    stx mu_next
    jmp music_play
!:  rts

// ---------------------------------------------------------------- decoding
// voice X: read the next row into v_pend (0 nothing, 1 note, 2 off)
mu_decode:
    lda #0
    sta v_pend,x
    sta v_plegato,x
    lda v_wait,x
    beq !read+
    dec v_wait,x
    rts
!read:
    jsr v_byte
    cmp #$60
    bcc !note+
    cmp #$80
    bcc !inst+
    beq !legato+
    cmp #$81
    beq !off+
    cmp #$82
    beq !end+
    and #$3f                    // $c0+n: this row and n more without events
    sta v_wait,x
    rts
!inst:
    and #$1f
    sta v_inst,x
    jmp !read-
!legato:
    lda #1
    sta v_plegato,x
    jmp !read-
!off:
    lda #2
    sta v_pend,x
    rts
!end:
    jsr mu_next_pattern
    lda mu_ended
    beq !read-
    rts
!note:
    sta v_pnote,x
    lda #1
    sta v_pend,x
    lda v_plegato,x
    bne !+
    jmp mu_hardrestart
!:  rts

// voice X: gate off, ADSR 0 (written to the SID at once)
mu_hardrestart:
    ldy v_sidofs,x
    lda #0
    sta v_gate,x
    sta SID_M+5,y
    sta SID_M2+5,y
    sta SID_M+6,y
    sta SID_M2+6,y
    lda v_wave,x
    sta SID_M+4,y
    sta SID_M2+4,y
    rts

// voice X: next entry of its order list (loop or end of the piece)
mu_next_pattern:
    inc v_ord,x
    lda v_ord,x
    cmp mu_hdr+7,x              // order length
    bcc !load+
    lda mu_hdr+6                // loop index
    cmp #$ff
    bne !+
    lda #1                      // no loop: the piece has ended
    sta mu_ended
    rts
!:  sta v_ord,x
!load:
    txa                         // order list address: header 10 + 2 * voice
    asl
    tay
    clc
    lda mu_hdr+10,y
    adc v_ord,x
    sta mu_ptr
    lda mu_hdr+11,y
    adc #0
    sta mu_ptr+1
    ldz #0
    lda ((mu_ptr)),z            // pattern number
    asl
    clc
    adc mu_hdr+16
    sta mu_ptr
    lda mu_hdr+17
    adc #0
    sta mu_ptr+1
    jsr mu_read16               // A = low, X = high byte; the voice is in mu_tmpx
    ldy mu_tmpx
    sta v_patlo,y
    txa
    sta v_pathi,y
    ldx mu_tmpx
    rts

// A/X = 16-bit word at mu_ptr (keeps the voice in mu_tmpx)
mu_read16:
    stx mu_tmpx
    ldz #0
    lda ((mu_ptr)),z
    pha
    inz
    lda ((mu_ptr)),z
    tax
    ldz #0
    pla
    rts

// next byte of voice X's pattern
v_byte:
    lda v_patlo,x
    sta mu_ptr
    lda v_pathi,x
    sta mu_ptr+1
    ldz #0
    lda ((mu_ptr)),z
    inc v_patlo,x
    bne !+
    inc v_pathi,x
!:  rts

// ---------------------------------------------------------------- tick 0
mu_apply:
    lda v_pend,x
    bne !+
    rts
!:  cmp #2
    bne !note+
    lda #0                      // off: release
    sta v_gate,x
    rts
!note:
    lda v_pnote,x
    sta v_note,x
    lda v_plegato,x
    beq !new+
    lda v_gate,x
    beq !new+
    jmp mu_vibstep              // legato: new pitch only
!new:
    // instrument record: table + 16 * instrument
    lda v_inst,x
    asl
    asl
    asl
    asl
    clc
    adc mu_hdr+18
    sta mu_ptr
    lda mu_hdr+19
    adc #0
    sta mu_ptr+1
    ldz #0
    ldy #0
!:  lda ((mu_ptr)),z
    sta mu_rec,y
    inz
    iny
    cpy #16
    bne !-
    ldz #0
    ldy v_sidofs,x
    lda mu_rec
    sta SID_M+5,y
    sta SID_M2+5,y
    lda mu_rec+1
    sta SID_M+6,y
    sta SID_M2+6,y
    lda mu_rec+2
    sta v_wave,x
    lda mu_rec+3
    sta v_pwlo,x
    lda mu_rec+4
    sta v_pwhi,x
    lda mu_rec+5
    sta v_swlo,x
    lda mu_rec+6
    sta v_swhi,x
    lda mu_rec+7
    sta v_vdelay,x
    lda mu_rec+8
    sta v_vspeed,x
    lda mu_rec+9
    sta v_vdepth,x
    lda mu_rec+10
    sta v_arplo,x
    lda mu_rec+11
    sta v_arphi,x
    lda mu_rec+12
    and #$1f
    sta v_arplen,x
    lda mu_rec+13
    sta v_wtlo,x
    lda mu_rec+14
    sta v_wthi,x
    lda mu_rec+15
    sta v_wtlen,x
    lda #0
    sta v_arppos,x
    sta v_wtpos,x
    sta v_vcnt,x
    sta v_vph,x
    sta v_voflo,x
    sta v_vofhi,x
    lda #1
    sta v_gate,x
    lda v_bit,x                 // filter routing
    eor #$ff
    and mu_routing
    sta mu_routing
    lda mu_rec+12
    bpl !+
    lda v_bit,x
    ora mu_routing
    sta mu_routing
!:  lda mu_hdr+4
    ora mu_routing
    sta SID_M+$17
    sta SID_M2+$17
    // fall through
// vibrato step for the current note: semitone * depth / 8 / speed (1/8 semitone units)
mu_vibstep:
    lda v_vdepth,x
    bne !+
    rts
!:  ldy v_note,x
    lda semi_lo,y
    sta mu_m
    lda semi_hi,y
    sta mu_m+1
    lda #0
    sta mu_p
    sta mu_p+1
    sta mu_p+2
    ldy v_vdepth,x              // product = semitone * depth
!:  clc
    lda mu_p
    adc mu_m
    sta mu_p
    lda mu_p+1
    adc mu_m+1
    sta mu_p+1
    lda mu_p+2
    adc #0
    sta mu_p+2
    dey
    bne !-
    ldy #3                      // / 8
!:  lsr mu_p+2
    ror mu_p+1
    ror mu_p
    dey
    bne !-
    lda #0                      // / speed (16-bit by 8-bit)
    sta mu_q
    sta mu_q+1
    ldy #16
!:  asl mu_p
    rol mu_p+1
    rol
    cmp v_vspeed,x
    bcc !skip+
    sbc v_vspeed,x
    inc mu_p
!skip:
    dey
    bne !-
    lda mu_p
    sta v_vstlo,x
    lda mu_p+1
    sta v_vsthi,x
    rts

// ---------------------------------------------------------------- effects
mu_effects:
    lda v_wtlen,x
    beq !arp+
    lda v_wtpos,x               // wave table entry
    asl
    clc
    adc v_wtlo,x
    sta mu_ptr
    lda v_wthi,x
    adc #0
    sta mu_ptr+1
    ldz #0
    lda ((mu_ptr)),z
    sta mu_w
    inz
    lda ((mu_ptr)),z
    ldz #0
    sta mu_n
    lda v_wtpos,x
    clc
    adc #1
    cmp v_wtlen,x
    bcs !+
    sta v_wtpos,x
!:  lda mu_w
    and #1
    beq !rel+
    lda mu_n                    // absolute note
    jmp !gotn+
!rel:
    lda v_note,x
    clc
    adc mu_n
    jmp !gotn+
!arp:
    lda v_wave,x
    sta mu_w
    lda v_arplen,x
    beq !plain+
    lda v_arppos,x
    clc
    adc v_arplo,x
    sta mu_ptr
    lda v_arphi,x
    adc #0
    sta mu_ptr+1
    ldz #0
    lda ((mu_ptr)),z
    clc
    adc v_note,x
    sta mu_n
    inc v_arppos,x
    lda v_arppos,x
    cmp v_arplen,x
    bcc !+
    lda #0
    sta v_arppos,x
!:  lda mu_n
    jmp !gotn+
!plain:
    lda v_note,x
!gotn:
    bpl !+                      // clamp to 0..95
    lda #0
!:  cmp #96
    bcc !+
    lda #95
!:  tay
    lda freq_lo,y
    sta mu_f
    lda freq_hi,y
    sta mu_f+1
    // vibrato (not with wave tables): triangle around the note after the delay
    lda v_wtlen,x
    bne !novib+
    lda v_vdepth,x
    beq !novib+
    lda v_vcnt,x
    cmp v_vdelay,x
    bcs !vib+
    inc v_vcnt,x
    jmp !novib+
!vib:
    lda v_vph,x                 // phase 0..4*speed-1: up, down, down, up
    ldy #0
!:  cmp v_vspeed,x
    bcc !dir+
    sbc v_vspeed,x
    iny
    bne !-
!dir:
    tya                         // quarter 0 or 3: up, 1 or 2: down
    beq !up+
    cmp #3
    beq !up+
    sec
    lda v_voflo,x
    sbc v_vstlo,x
    sta v_voflo,x
    lda v_vofhi,x
    sbc v_vsthi,x
    sta v_vofhi,x
    jmp !ph+
!up:
    clc
    lda v_voflo,x
    adc v_vstlo,x
    sta v_voflo,x
    lda v_vofhi,x
    adc v_vsthi,x
    sta v_vofhi,x
!ph:
    inc v_vph,x
    lda v_vspeed,x
    asl
    asl
    cmp v_vph,x
    bne !+
    lda #0
    sta v_vph,x
!:  clc
    lda mu_f
    adc v_voflo,x
    sta mu_f
    lda mu_f+1
    adc v_vofhi,x
    sta mu_f+1
!novib:
    // pulse sweep, bouncing between 256 and 3840
    lda v_swlo,x
    ora v_swhi,x
    beq !pw+
    clc
    lda v_pwlo,x
    adc v_swlo,x
    sta v_pwlo,x
    lda v_pwhi,x
    adc v_swhi,x
    sta v_pwhi,x
    bmi !turn+
    cmp #1
    bcc !turn+
    cmp #15
    bcc !pw+
!turn:
    lda v_pwhi,x                // back inside, sweep reversed
    bmi !low+
    cmp #1
    bcs !high+
!low:
    lda #1
    sta v_pwhi,x
    lda #0
    sta v_pwlo,x
    beq !neg+
!high:
    lda #15
    sta v_pwhi,x
    lda #0
    sta v_pwlo,x
!neg:
    sec
    lda #0
    sbc v_swlo,x
    sta v_swlo,x
    lda #0
    sbc v_swhi,x
    sta v_swhi,x
!pw:
    ldy v_sidofs,x
    lda mu_f
    sta SID_M,y
    sta SID_M2,y
    lda mu_f+1
    sta SID_M+1,y
    sta SID_M2+1,y
    lda v_pwlo,x
    sta SID_M+2,y
    sta SID_M2+2,y
    lda v_pwhi,x
    sta SID_M+3,y
    sta SID_M2+3,y
    lda mu_w
    and #$f0
    ora v_gate,x
    sta SID_M+4,y
    sta SID_M2+4,y
    rts

// ---------------------------------------------------------------- sound effects
// A = effect (SFX_*). Plays on the effect's voice unless a higher-priority effect is still sounding there.
sfx_play:
    stx s_savex
    sty s_savey
    asl
    clc
    adc #<(MUSIC_ADDR + 4 + 2 * MUSIC_PIECES)
    sta mu_ptr
    lda #>(MUSIC_ADDR + 4 + 2 * MUSIC_PIECES)
    adc #0
    sta mu_ptr+1
    jsr mu_read16
    sta mu_ptr
    stx mu_ptr+1
    ldz #0
    ldy #0
!:  lda ((mu_ptr)),z
    sta s_rec,y
    inz
    iny
    cpy #12
    bne !-
    ldz #0
    ldx s_rec+5                 // voice
    lda s_rec+6                 // priority: lower ones do not interrupt
    cmp s_prio,x
    bcc !done+
    sta s_prio,x
    ldy v_sidofs,x
    lda #$08                    // test bit: oscillator and envelope start cleanly
    sta SID_S+4,y
    sta SID_S2+4,y
    lda s_rec
    sta SID_S+5,y
    sta SID_S2+5,y
    lda s_rec+1
    sta SID_S+6,y
    sta SID_S2+6,y
    lda s_rec+2
    sta SID_S+2,y
    sta SID_S2+2,y
    lda s_rec+3
    sta SID_S+3,y
    sta SID_S2+3,y
    lda s_rec+4
    sta s_note,x
    lda s_rec+7
    sta s_frames,x
    lda s_rec+8
    sta s_wtlo,x
    lda s_rec+9
    sta s_wthi,x
    lda s_rec+10
    sta s_wtlen,x
    lda #0
    sta s_pos,x
    lda #1
    sta s_active,x
!done:
    ldx s_savex
    ldy s_savey
    rts

sfx_frame:
    ldx #2
!v: lda s_active,x
    bne !+
    jmp !next+
!:
    lda s_pos,x
    asl
    clc
    adc s_wtlo,x
    sta mu_ptr
    lda s_wthi,x
    adc #0
    sta mu_ptr+1
    ldz #0
    lda ((mu_ptr)),z
    sta mu_w
    inz
    lda ((mu_ptr)),z
    ldz #0
    sta mu_n
    lda s_pos,x
    clc
    adc #1
    cmp s_wtlen,x
    bcs !+
    sta s_pos,x
!:  lda mu_w
    and #1
    bne !abs+
    lda s_note,x
    clc
    adc mu_n
    jmp !got+
!abs:
    lda mu_n
!got:
    bpl !+
    lda #0
!:  cmp #96
    bcc !+
    lda #95
!:  tay
    lda freq_lo,y
    pha
    lda freq_hi,y
    ldy v_sidofs,x
    sta SID_S+1,y
    sta SID_S2+1,y
    pla
    sta SID_S,y
    sta SID_S2,y
    lda mu_w
    and #$f0
    sta mu_w
    lda s_frames,x              // gate open while frames are left, then release
    beq !rel+
    dec s_frames,x
    lda mu_w
    ora #1
    bne !ctl+
!rel:
    lda #0                      // released: any effect may take the voice
    sta s_prio,x
    lda mu_w
!ctl:
    sta SID_S+4,y
    sta SID_S2+4,y
!next:
    dex
    bmi !+
    jmp !v-
!:  rts

// ---------------------------------------------------------------- data
v_sidofs: .byte 0, 7, 14
v_bit:    .byte 1, 2, 4
mu_hdr:   .fill 20, 0
mu_rec:   .fill 16, 0
mu_playing: .byte 0
mu_tick:  .byte 0
mu_hrtick:.byte 0
mu_ended: .byte 0
mu_next:  .byte $ff
mu_routing: .byte 0
mu_tmpx:  .byte 0
mu_w:     .byte 0
mu_n:     .byte 0
mu_f:     .word 0
mu_m:     .word 0
mu_p:     .fill 3, 0
mu_q:     .word 0
v_ord:    .fill 3, 0
v_patlo:  .fill 3, 0
v_pathi:  .fill 3, 0
v_wait:   .fill 3, 0
v_inst:   .fill 3, 0
v_note:   .fill 3, 0
v_gate:   .fill 3, 0
v_wave:   .fill 3, 0
v_pend:   .fill 3, 0
v_pnote:  .fill 3, 0
v_plegato:.fill 3, 0
v_pwlo:   .fill 3, 0
v_pwhi:   .fill 3, 0
v_swlo:   .fill 3, 0
v_swhi:   .fill 3, 0
v_vdelay: .fill 3, 0
v_vspeed: .fill 3, 0
v_vdepth: .fill 3, 0
v_vcnt:   .fill 3, 0
v_vph:    .fill 3, 0
v_vstlo:  .fill 3, 0
v_vsthi:  .fill 3, 0
v_voflo:  .fill 3, 0
v_vofhi:  .fill 3, 0
v_arplo:  .fill 3, 0
v_arphi:  .fill 3, 0
v_arplen: .fill 3, 0
v_arppos: .fill 3, 0
v_wtlo:   .fill 3, 0
v_wthi:   .fill 3, 0
v_wtlen:  .fill 3, 0
v_wtpos:  .fill 3, 0
s_active: .fill 3, 0
s_prio:   .fill 3, 0
s_note:   .fill 3, 0
s_frames: .fill 3, 0
s_pos:    .fill 3, 0
s_wtlo:   .fill 3, 0
s_wthi:   .fill 3, 0
s_wtlen:  .fill 3, 0
s_rec:    .fill 12, 0
s_savex:  .byte 0
s_savey:  .byte 0

name_music: .text "MUSIC"
name_music_end:
job_music: DmaJob(DMA_CMD_COPY, LEVEL_BUF, MUSIC_ADDR, MUSIC_BYTES)

#import "../build/gen/music_tables.inc"
