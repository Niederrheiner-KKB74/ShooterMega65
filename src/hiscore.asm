// ----------------------------------------------------------------------------
// High-score table on disk (Stage 16).
//
// 10 entries: name (10 characters, ASCII A-Z 0-9 space . - !), score (3 BCD bytes), level reached (1-4, 5 =
// mission accomplished). File SH65HI.DAT (SEQ, HI_BYTES bytes):
//   +0  "SH65HI", version 1, entry count 10     +8  CRC-16/CCITT (lo, hi) over all bytes except +8/+9
//   +10 six zero bytes                           +16 10 records of 16 bytes: name 10, score 3, level 1, 0, 0
//
// The disk transaction is Vyper's, confirmed on hardware (Vyper Stage 10a6, src/tests/stage10a6_disk.asm, copied
// unchanged apart from the size HI_BYTES and the file names): write SH65HI.TMP, read it back and verify; if a valid
// SH65HI.DAT exists, check that it still equals the list read at start, scratch SH65HI.BAK, rename DAT -> BAK; then
// rename TMP -> DAT and verify it again. A damaged file is never overwritten (hi_blocked; Vyper's rule).
//
// Reading happens at start while the KERNAL still owns the machine (hi_boot, from the loader). Saving needs the
// KERNAL again: kernal_enter gives BASIC's zero page, VIC registers and CIA direction back (Vyper's hi_suspend:
// native video state, then CLI), the screen stays black (palette 0 black); kernal_leave returns to the game.
// ----------------------------------------------------------------------------
.const HI_ENTRIES = 10
.const HI_NAME    = 10
.const HI_REC     = 16
.const HI_HEAD    = 16
.const HI_BYTES   = HI_HEAD + HI_ENTRIES * HI_REC          // 176
.label hi_backup  = $0a00                                  // in BASIC's saved screen area (work RAM, SAVED_SCR)
.errorif (HI_BYTES > 255), "high-score file must stay below 256 bytes (X-indexed loops)"
.errorif (hi_backup + HI_BYTES > $1000), "hi_backup beyond $0FFF"

hi_table: .fill HI_BYTES, 0          // the list in use
hi_io:    .fill HI_BYTES, 0          // file image for reading, writing and checking

hi_device:  .byte 8
hi_blocked: .byte 0                  // 1: file damaged or recovered from the backup, or a save failed: never save
hi_present: .byte 0                  // 1: a valid SH65HI.DAT was read
hi_error:   .byte 0                  // 0 ok, 1 open, 2 DOS/channel, 3 read, 4 write, 5 verify
hi_dos:     .byte 0                  // DOS status number (62 = file not found)
hi_stage:   .byte 0
hi_note:    .byte 0                  // shown under the list: 0 none, 1 saved, 2 disk error, 3 file damaged
hi_rank:    .byte 0                  // place of the new entry 0-9, 10 = not qualified
hi_level:   .byte 0                  // level reached by the last game (1-4, 5 = all)
hi_name:    .fill HI_NAME, $20       // name being entered
hi_crc:     .word 0
hi_left:    .word 0
hi_file_ptr: .word 0
hi_file_len: .byte 0
hi_lfn:     .byte 2
hi_secondary: .byte 2
hi_io_byte: .byte 0
hi_io_status: .byte 0
hi_cmd_budget: .byte 0
hi_cmd_code: .byte 0
hi_i:       .byte 0
hi_j:       .byte 0

hi_magic: .byte $53, $48, $36, $35, $48, $49, 1, HI_ENTRIES      // "SH65HI", version, entries
// file names in PETSCII (upper case letters = ASCII codes)
hi_filename:    .text "0:SH65HI.DAT,S,R"
                .byte 0
hi_tmp_read:    .text "0:SH65HI.TMP,S,R"
                .byte 0
hi_tmp_write:   .text "0:SH65HI.TMP,S,W"
                .byte 0
hi_bak_read:    .text "0:SH65HI.BAK,S,R"
                .byte 0
hi_scratch_bak: .text "S0:SH65HI.BAK"
                .byte 0
hi_rename_bak:  .text "R0:SH65HI.BAK=SH65HI.DAT"
                .byte 0
hi_rename_dat:  .text "R0:SH65HI.DAT=SH65HI.TMP"
                .byte 0

// default list (no file yet): invented pilots
hi_def_names: .text "VIPER     FALCON    HAWK      EAGLE     RAVEN     COBRA     TALON     STORM     BLADE     NOVA      "
hi_def_score: .byte $05,$00,$00, $04,$00,$00, $03,$00,$00, $02,$50,$00, $02,$00,$00
              .byte $01,$50,$00, $01,$00,$00, $00,$75,$00, $00,$50,$00, $00,$25,$00
hi_def_level: .byte 4, 4, 3, 3, 3, 2, 2, 2, 1, 1

// ============================================================== start (KERNAL active, from the loader)
hi_boot:
    lda ld_device
    sta hi_device
    lda #0
    sta hi_blocked
    sta hi_present
    sta hi_note
    lda #<hi_filename
    ldy #>hi_filename
    jsr hi_read_named
    lda hi_error
    bne hb_fallback
    jsr hi_validate
    bcs hb_bad
    jsr hi_io_to_table
    lda #1
    sta hi_present
    jmp hi_best
hb_bad:
    lda #1
    sta hi_blocked
hb_fallback:
    lda hi_dos                  // 62 = no file yet: fine; anything else: do not write
    cmp #62
    beq !+
    lda #1
    sta hi_blocked
!:  lda #<hi_bak_read           // a valid backup is shown, but never written over (Vyper)
    ldy #>hi_bak_read
    jsr hi_read_named
    lda hi_error
    bne hb_empty
    jsr hi_validate
    bcs hb_empty
    jsr hi_io_to_table
    lda #1
    sta hi_blocked
    lda #3
    sta hi_note
    jmp hi_best
hb_empty:
    jsr hi_empty
    lda hi_blocked
    beq hi_best
    lda #3
    sta hi_note
// the best score of the list -> the title's high score
hi_best:
    ldx #2
!:  lda hi_table+HI_HEAD+HI_NAME,x
    sta hiscore_bcd,x
    dex
    bpl !-
    rts

// default list, sealed
hi_empty:
    ldx #HI_BYTES - 1
    lda #0
!:  sta hi_table,x
    dex
    bne !-
    sta hi_table
    ldx #7
!:  lda hi_magic,x
    sta hi_table,x
    dex
    bpl !-
    lda #0
    sta hi_i
!rec:
    ldx hi_i                    // record offset in Y, name offset (i * 10) in hi_j
    jsr hi_rec_y
    txa
    asl
    sta hi_j
    asl
    asl
    adc hi_j
    sta hi_j
    ldx #0
!:  stx hi_crc
    ldx hi_j
    lda hi_def_names,x
    sta hi_table,y
    inc hi_j
    iny
    ldx hi_crc
    inx
    cpx #HI_NAME
    bne !-
    lda hi_i                    // score: i * 3
    asl
    adc hi_i
    tax
    lda hi_def_score,x
    sta hi_table,y
    lda hi_def_score+1,x
    sta hi_table+1,y
    lda hi_def_score+2,x
    sta hi_table+2,y
    ldx hi_i
    lda hi_def_level,x
    sta hi_table+3,y
    inc hi_i
    lda hi_i
    cmp #HI_ENTRIES
    bne !rec-
    jmp hi_seal

// Y = offset of record X (16 + X * 16)
hi_rec_y:
    txa
    asl
    asl
    asl
    asl
    clc
    adc #HI_HEAD
    tay
    rts

// ============================================================== qualify / insert
// hi_rank = place of score_bcd (first entry with a lower score), 10 = not in the list (or score 0)
hi_qualify:
    lda #HI_ENTRIES
    sta hi_rank
    lda score_bcd
    ora score_bcd+1
    ora score_bcd+2
    beq !done+
    ldx #0
!rec:
    jsr hi_rec_y
    lda score_bcd               // score > entry?  (BCD compares like binary)
    cmp hi_table+HI_NAME,y
    bne !cmp+
    lda score_bcd+1
    cmp hi_table+HI_NAME+1,y
    bne !cmp+
    lda score_bcd+2
    cmp hi_table+HI_NAME+2,y
    beq !next+                  // equal: the older entry stays ahead
!cmp:
    bcs !found+
!next:
    inx
    cpx #HI_ENTRIES
    bne !rec-
!done:
    rts
!found:
    stx hi_rank
    rts

// insert hi_name / score_bcd / hi_level at hi_rank, the last entry drops out
hi_insert:
    ldy #HI_BYTES - 1           // move records rank..8 down by one record (from the end)
    ldx hi_rank
    jsr hi_rec_y
    sty hi_j                    // first byte of the new record
    ldy #HI_BYTES - 1 - HI_REC
!:  cpy hi_j
    bcc !put+
    lda hi_table,y
    sta hi_table+HI_REC,y
    cpy hi_j
    beq !put+
    dey
    jmp !-
!put:
    ldy hi_j
    ldx #0
!:  lda hi_name,x
    sta hi_table,y
    iny
    inx
    cpx #HI_NAME
    bne !-
    lda score_bcd
    sta hi_table,y
    lda score_bcd+1
    sta hi_table+1,y
    lda score_bcd+2
    sta hi_table+2,y
    lda hi_level
    sta hi_table+3,y
    lda #0
    sta hi_table+4,y
    sta hi_table+5,y
    rts

// ============================================================== save (needs the KERNAL)
// the list (with the new entry; hi_backup = the list before it) to disk; hi_note tells the result
hi_save:
    jsr hi_seal
    lda hi_blocked
    beq !+
    lda #3                      // damaged file: the entry stays for this session, nothing is written
    sta hi_note
    rts
!:  jsr kernal_enter
    jsr hi_disk_save
    lda hi_error
    pha
    jsr kernal_leave
    pla
    beq !ok+
    lda #1                      // keep the entry for this session, no further writes
    sta hi_blocked
    lda #2
    sta hi_note
    rts
!ok:
    lda #1
    sta hi_note
    rts

// BASIC's machine state for KERNAL disk calls; the screen stays black (Vyper's hi_suspend)
kernal_enter:
    sei
    jsr sound_off
    lda #0
    sta VIC_SPREN
    jsr wait_vblank
    lda #0                      // palette 0 black: BASIC's screen stays invisible
    sta VIC_PALSEL
    tax
!:  sta PAL_RED,x
    sta PAL_GREEN,x
    sta PAL_BLUE,x
    inx
    bne !-
    jsr vic_to_basic            // VIC registers (HOTREG last) and CIA port A direction as BASIC had them
    RunDma(job_gzp_save)        // our zero page aside, BASIC's back
    RunDma(job_zp_rest)
    lda saved_b
    tab
    ldz #0
    cli
    rts

kernal_leave:
    sei
    cld
    lda #0
    tab
    RunDma(job_zp_save)         // the KERNAL's zero page as it is now (for the final exit)
    RunDma(job_gzp_rest)
    lda #$47                    // VIC-IV I/O personality (as at start)
    sta VIC_KEY
    lda #$53
    sta VIC_KEY
    lda #0
    sta CIA1_DDRA
    jsr video_init
    jsr palette_init
    jmp key_drain

job_gzp_save: DmaJob(DMA_CMD_COPY, $0002, SAVED_GZP + 2, 254)
job_gzp_rest: DmaJob(DMA_CMD_COPY, SAVED_GZP + 2, $0002, 254)

// ============================================================== checks
hi_seal:
    jsr hi_table_to_io
    jsr hi_crc16
    lda hi_crc
    sta hi_io+8
    sta hi_table+8
    lda hi_crc+1
    sta hi_io+9
    sta hi_table+9
    rts

// CRC-16/CCITT ($FFFF, polynomial $1021) of hi_io without bytes 8/9 (Vyper's hi_crc16, X-indexed)
hi_crc16:
    lda #$ff
    sta hi_crc
    sta hi_crc+1
    ldx #0
!byte:
    cpx #8
    beq !next+
    cpx #9
    beq !next+
    lda hi_io,x
    eor hi_crc+1
    sta hi_crc+1
    ldy #8
!bit:
    asl hi_crc
    rol hi_crc+1
    bcc !+
    lda hi_crc
    eor #$21
    sta hi_crc
    lda hi_crc+1
    eor #$10
    sta hi_crc+1
!:  dey
    bne !bit-
!next:
    inx
    cpx #HI_BYTES
    bne !byte-
    rts

// carry clear: hi_io is a valid list (magic, reserved bytes, CRC, names, BCD scores, levels, order)
hv_bad:
    sec
    rts
hi_validate:
    ldx #7
!:  lda hi_io,x
    cmp hi_magic,x
    bne hv_bad
    dex
    bpl !-
    ldx #10
!:  lda hi_io,x
    bne hv_bad
    inx
    cpx #HI_HEAD
    bne !-
    jsr hi_crc16
    lda hi_crc
    cmp hi_io+8
    bne hv_bad
    lda hi_crc+1
    cmp hi_io+9
    bne hv_bad
    ldx #0
!rec:
    stx hi_i
    jsr hi_rec_y
    ldx #HI_NAME
!:  lda hi_io,y
    jsr hi_allowed
    bcs hv_bad2
    iny
    dex
    bne !-
    ldx #3                      // BCD digits
!:  lda hi_io,y
    and #$0f
    cmp #10
    bcs hv_bad2
    lda hi_io,y
    cmp #$a0
    bcs hv_bad2
    iny
    dex
    bne !-
    lda hi_io,y                 // level 1-5
    beq hv_bad2
    cmp #6
    bcs hv_bad2
    lda hi_io+1,y
    ora hi_io+2,y
    bne hv_bad2
    ldx hi_i                    // order: this score <= the previous one
    beq !next+
    tya
    sec
    sbc #3                      // score of this record
    tay
    lda hi_io-HI_REC,y
    cmp hi_io,y
    bne !o+
    lda hi_io-HI_REC+1,y
    cmp hi_io+1,y
    bne !o+
    lda hi_io-HI_REC+2,y
    cmp hi_io+2,y
!o: bcc hv_bad2
!next:
    ldx hi_i
    inx
    cpx #HI_ENTRIES
    bne !rec-
    clc
    rts
hv_bad2:
    sec
    rts

// carry clear if A may appear in a name
hi_allowed:
    cmp #$20
    beq !ok+
    cmp #$21                    // !
    beq !ok+
    cmp #$2d                    // - .
    beq !ok+
    cmp #$2e
    beq !ok+
    cmp #$30
    bcc !no+
    cmp #$3a
    bcc !ok+
    cmp #$41
    bcc !no+
    cmp #$5b
    bcc !ok+
!no:
    sec
    rts
!ok:
    clc
    rts

hi_table_to_io:
    ldx #HI_BYTES - 1
!:  lda hi_table,x
    sta hi_io,x
    dex
    cpx #$ff
    bne !-
    rts
hi_io_to_table:
    ldx #HI_BYTES - 1
!:  lda hi_io,x
    sta hi_table,x
    dex
    cpx #$ff
    bne !-
    rts
hi_table_to_backup:
    ldx #HI_BYTES - 1
!:  lda hi_table,x
    sta hi_backup,x
    dex
    cpx #$ff
    bne !-
    rts
// carry set if hi_io differs from hi_table / from hi_backup
hi_compare_table:
    ldx #HI_BYTES - 1
!:  lda hi_io,x
    cmp hi_table,x
    bne !diff+
    dex
    cpx #$ff
    bne !-
    clc
    rts
!diff:
    sec
    rts
hi_compare_backup:
    ldx #HI_BYTES - 1
!:  lda hi_io,x
    cmp hi_backup,x
    bne !diff+
    dex
    cpx #$ff
    bne !-
    clc
    rts
!diff:
    sec
    rts

// ============================================================== disk transaction (Vyper Stage 10a6, unchanged)
#import "hiscore_disk.asm"
