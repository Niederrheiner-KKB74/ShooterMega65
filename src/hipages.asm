// ----------------------------------------------------------------------------
// Pages built with textpage.asm (Stage 16): Hall of Fame (title cycle), name entry, MISSION ACCOMPLISHED.
// Attic RAM only (the logo rows come from the title data, the text uses the landscape glyph area).
// ----------------------------------------------------------------------------
.const HX = 16                          // left edge of the list in the 256-px text block
.const ENTRY_FRAMES = 0                 // name entry: no time limit

pg_hl:    .byte $ff                     // highlighted entry (new entry), $ff none
pg_t:     .word 0
pg_blink: .byte 0
pg_cur:   .byte 0                       // name entry: cursor 0-9
pg_rep:   .byte 0                       // joystick repeat delay
pg_prev:  .byte 0
pg_key:   .byte 0
pg_e:     .byte 0                       // entry being drawn

s_hof:    .text "HALL OF FAME"
          .byte 0
s_new:    .text "NEW HIGH SCORE!"
          .byte 0
s_head:   .text "NO  NAME          SCORE  LEVEL"
          .byte 0
s_fire:   .text "PRESS FIRE TO START"
          .byte 0
s_cont:   .text "PRESS FIRE TO CONTINUE"
          .byte 0
s_enter:  .text "ENTER YOUR NAME"
          .byte 0
s_help:   .text "UP/DOWN: LETTER  FIRE: NEXT  >: END"
          .byte 0
s_saved:  .text "SAVED ON DISK"
          .byte 0
s_err:    .text "DISK ERROR - NOT SAVED"
          .byte 0
s_bad:    .text "SCORE FILE DAMAGED - NOT SAVED"
          .byte 0
s_all:    .text "ALL"
          .byte 0
s_ten:    .text "10."
          .byte 0
s_mis:    .text "MISSION ACCOMPLISHED"
          .byte 0
s_mis2:   .text "ALL FOUR OPERATIONS COMPLETED."
          .byte 0
s_mis3:   .text "THE ENEMY FORCES ARE DEFEATED."
          .byte 0
s_final:  .text "FINAL SCORE"
          .byte 0
s_pilot:  .text "PILOT     "
pg_alpha: .text "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-! "
          .byte $3c, $3e              // < delete, > end (joystick only, never stored)
pg_alpha_end:

// screen A with the logo rows, palettes, empty text block
page_begin:
    lda #0
    sta VIC_SPREN
    RunDma(job_title_in)
    jsr buffer_a_init
    lda #TEXTYPOS_BASE
    sta VIC_TEXTYPOS
    jsr show_buffer_a
    lda #<((TITLE_ADDR + TITLE_PAL) & $ffff)
    ldx #>((TITLE_ADDR + TITLE_PAL) & $ffff)
    ldy #$10
    jsr load_palette16
    jmp tp_open

// big centred text A/X on line Y (length in pg_key), colour tp_c
pg_big:
    sta pg_t
    stx pg_t+1
    tya
    tax
    lda pg_key                  // x = (256 - len * 12) / 2 = 128 - len * 6
    asl
    adc pg_key
    asl
    eor #$ff
    sec
    adc #128
    jsr tp_at
    lda #2
    sta tp_scale
    lda pg_t
    ldx pg_t+1
    jmp tp_text

// centred small text A/X on line Y, length pg_key, colour tp_c
pg_small:
    sta pg_t
    stx pg_t+1
    tya
    tax
    lda pg_key                  // x = 128 - len * 3
    asl
    adc pg_key
    eor #$ff
    sec
    adc #128
    jsr tp_at
    lda pg_t
    ldx pg_t+1
    jmp tp_text

// the whole list (title line A/X, length pg_key)
hof_draw:
    ldy #0
    jsr pg_big
    lda #TC_GREY
    sta tp_c
    lda #HX
    ldx #2
    jsr tp_at
    lda #<s_head
    ldx #>s_head
    jsr tp_text
    lda #0
    sta pg_t
!:  ldx pg_t
    jsr hof_entry
    inc pg_t
    lda pg_t
    cmp #HI_ENTRIES
    bne !-
    rts

// entry X on line 3 + X
hof_entry:
    stx pg_e
    txa
    clc
    adc #3
    pha
    jsr tp_clear_line
    pla
    tax
    lda #HX + 6
    jsr tp_at
    ldx pg_e
    lda #TC_WHITE
    cpx pg_hl
    bne !+
    lda #TC_GOLD
!:  cpx #3                      // the top three in light blue
    bcs !+
    cpx pg_hl
    beq !+
    lda #TC_BLUE
!:  sta tp_c
    cpx #9
    bne !+
    lda #HX
    sta tp_x
    lda #<s_ten
    ldx #>s_ten
    jsr tp_text
    jmp !name+
!:  txa
    clc
    adc #$31
    jsr tp_char
    lda #$2e
    jsr tp_char
!name:
    lda #HX + 24
    sta tp_x
    ldx pg_e
    jsr hi_rec_y
    sty pg_prev
    ldx #0
!:  stx pg_key
    ldy pg_prev
    lda hi_table,y
    jsr tp_char
    inc pg_prev
    ldx pg_key
    inx
    cpx #HI_NAME
    bne !-
    lda #HX + 108               // score, right edge HX + 144
    sta tp_x
    ldy pg_prev                 // = record + 10
    tya
    clc
    adc #<hi_table
    pha
    lda #>hi_table
    adc #0
    tax
    pla
    jsr tp_score
    ldy pg_prev
    lda hi_table+3,y            // level 1-4, 5 = all
    cmp #5
    bne !+
    lda #HX + 162
    sta tp_x
    lda #<s_all
    ldx #>s_all
    jmp tp_text
!:  pha
    lda #HX + 168
    sta tp_x
    pla
    ora #$30
    jmp tp_char

// line 13: result of the last save
pg_note:
    lda #13
    jsr tp_clear_line
    lda hi_note
    beq !done+
    ldx #TC_GREEN
    cmp #1
    beq !+
    ldx #TC_RED
!:  stx tp_c
    tax
    lda pg_note_lo-1,x
    pha
    lda pg_note_len-1,x
    sta pg_key
    lda pg_note_hi-1,x
    tax
    pla
    ldy #13
    jmp pg_small
!done:
    rts
pg_note_lo:  .byte <s_saved, <s_err, <s_bad
pg_note_hi:  .byte >s_saved, >s_err, >s_bad
pg_note_len: .byte 13, 22, 30

// line 14 blinking (A/X text, length pg_key); returns after every frame, carry set when fire was pressed
pg_line14:
    sta pg_t
    stx pg_t+1
    lda #14
    jsr tp_clear_line
    lda pg_blink
    and #16
    beq !+
    lda #TC_GOLD
    sta tp_c
    lda pg_t
    ldx pg_t+1
    ldy #14
    jsr pg_small
!:  rts

// ============================================================== Hall of Fame (title cycle and after an entry)
// shows the list; returns after about 9 s or when fire was pressed (carry set) / a level key (key_2)
hof_page:
    jsr page_begin
    lda #TC_GOLD
    sta tp_c
    lda #12
    sta pg_key
    lda #<s_hof
    ldx #>s_hof
    jsr hof_draw
    jsr pg_note
    lda #0
    sta pg_t
    sta pg_t+1
    sta pg_blink
!:  jsr shop_frame
    inc pg_blink
    lda pg_blink
    and #15
    bne !nb+
    lda #19
    sta pg_key
    lda #<s_fire
    ldx #>s_fire
    jsr pg_line14
!nb:
    lda key_2
    bne !key+
    lda sh_press
    and #$10
    bne !fire+
    inc pg_t
    bne !-
    inc pg_t+1
    lda pg_t+1
    cmp #2                      // 512 frames
    bne !-
    clc
    rts
!fire:
!key:
    sec
    rts

// ============================================================== after a game (game over or mission accomplished)
// A = level reached (1-4, 5 = all). Name entry and save when the score enters the list.
hi_after_game:
    sta hi_level
    lda attic_ok
    bne !+
    rts
!:  jsr hi_qualify
    lda hi_rank
    cmp #HI_ENTRIES
    bcc !+
    rts
!:  sta pg_hl
    jsr hi_table_to_backup      // the list as it is on disk (hi_save checks the disk against it)
    ldx #HI_NAME - 1
    lda #$20
!:  sta hi_name,x
    dex
    bpl !-
    jsr hi_insert
    lda #MUS_TITLE
    jsr music_play
    jsr page_begin
    lda #TC_GOLD
    sta tp_c
    lda #15
    sta pg_key
    lda #<s_new
    ldx #>s_new
    jsr hof_draw
    lda #TC_WHITE
    sta tp_c
    lda #15
    sta pg_key
    lda #<s_enter
    ldx #>s_enter
    ldy #13
    jsr pg_small
    lda #TC_GREY
    sta tp_c
    lda #35
    sta pg_key
    lda #<s_help
    ldx #>s_help
    ldy #14
    jsr pg_small
    jsr name_entry
    jsr hi_save                 // KERNAL session: the screen is black for a moment
    lda #MUS_TITLE
    jsr music_play
    jsr page_begin              // the list again with the result
    lda #TC_GOLD
    sta tp_c
    lda #12
    sta pg_key
    lda #<s_hof
    ldx #>s_hof
    jsr hof_draw
    jsr pg_note
    jsr fire_reset
    lda #0
    sta pg_t
    sta pg_t+1
    sta pg_blink
!:  jsr shop_frame
    inc pg_blink
    lda pg_blink
    and #15
    bne !+
    lda #22
    sta pg_key
    lda #<s_cont
    ldx #>s_cont
    jsr pg_line14
!:  lda sh_press
    and #$10
    bne !done+
    inc pg_t
    bne !--
    inc pg_t+1
    lda pg_t+1
    cmp #3
    bne !--
!done:
    lda #$ff
    sta pg_hl
    rts

// ============================================================== name entry
// keyboard: letters, digits, space . - !, DEL, RETURN; joystick (arcade style, Stage 16b): up/down letter,
// fire = accept and next position, '<' = back one position, '>' or fire on the 10th character = done;
// left/right move the cursor
name_entry:
    lda #$41                    // the first position shows A
    sta hi_name
    lda #0
    sta pg_cur
    sta pg_rep
    sta pg_blink
    jsr key_drain
    jsr read_joystick
    lda joy
    sta pg_prev
    jmp !frame+
ne_ret:
    jmp !done+                  // (branch trampoline)
ne_fire:
    jsr ne_accept
    bcs ne_ret
    lda #SFX_SELECT
    jsr sfx_play
    lda #8
    sta pg_blink
    jsr ne_draw
    jmp !next+
!frame:
    jsr wait_vblank
    jsr sound_frame
    inc pg_blink
    lda pg_blink
    and #7
    bne !+
    jsr ne_draw
!:  lda KEYQUEUE                // raw keys (no game keys here)
    beq !joy+
    sta KEYQUEUE
    cmp #$0d
    beq ne_ret
    cmp #$14                    // DEL
    beq !del+
    cmp #$61                    // lower case -> upper case
    bcc !+
    cmp #$7b
    bcs !joy+
    and #$df
!:  jsr hi_allowed
    bcs !joy+
    jsr ne_put
    lda pg_cur
    cmp #HI_NAME - 1
    bcs !redraw+
    inc pg_cur
    jmp !redraw+
!del:
    lda pg_cur
    beq !+
    dec pg_cur
!:  lda #$20
    jsr ne_put
    jmp !redraw+
!joy:
    jsr read_joystick
    lda joy
    and #$10                    // fire: new press only
    beq !+
    lda pg_prev
    and #$10
    beq ne_fire
!:  lda joy
    and #$0f
    bne !dir+
    sta pg_rep
    jmp !next+
!dir:
    ldx pg_rep                  // first move at once, then every 8 frames after a 20-frame pause
    beq !go+
    dec pg_rep
    jmp !next+
!go:
    ldx #8
    cmp pg_prev
    beq !+
    ldx #20
!:  stx pg_rep
    lsr                         // bit 0 up
    bcc !+
    jsr ne_step_up
    jmp !redraw+
!:  lsr                         // bit 1 down
    bcc !+
    jsr ne_step_down
    jmp !redraw+
!:  lsr                         // bit 2 left
    bcc !+
    lda pg_cur
    beq !redraw+
    dec pg_cur
    jmp !redraw+
!:  lsr                         // bit 3 right
    bcc !next+
    lda pg_cur
    cmp #HI_NAME - 1
    bcs !redraw+
    inc pg_cur
!redraw:
    lda #8                      // show the cursor at once
    sta pg_blink
    jsr ne_draw
!next:
    lda joy
    sta pg_prev
    jmp !frame-
!done:
    ldx #HI_NAME - 1            // characters a file may not hold (< > left behind) -> space
!:  lda hi_name,x
    jsr hi_allowed
    bcc !ok+
    lda #$20
    sta hi_name,x
!ok:
    dex
    bpl !-
    ldx #HI_NAME - 1            // empty name: PILOT
!:  lda hi_name,x
    cmp #$20
    bne !named+
    dex
    bpl !-
    ldx #HI_NAME - 1
!:  lda s_pilot,x
    sta hi_name,x
    dex
    bpl !-
!named:
    jsr ne_copy
    lda #SFX_SELECT
    jmp sfx_play

// fire: carry set = name complete
ne_accept:
    ldx pg_cur
    lda hi_name,x
    cmp #$3e                    // > end
    bne !+
    lda #$20
    sta hi_name,x
    sec
    rts
!:  cmp #$3c                    // < back
    bne !+
    lda #$20
    sta hi_name,x
    cpx #0
    beq !keep+
    dec pg_cur
!keep:
    clc
    rts
!:  cpx #HI_NAME - 1            // 10th character accepted: done
    bcc !+
    sec
    rts
!:  inc pg_cur
    ldx pg_cur
    lda hi_name,x
    cmp #$20
    bne !keep-
    lda #$41                    // a new position starts with A
    sta hi_name,x
    clc
    rts

// character A at the cursor
ne_put:
    ldx pg_cur
    sta hi_name,x
    rts
ne_step_up:
    jsr ne_index
    inx
    cpx #pg_alpha_end - pg_alpha
    bcc !+
    ldx #0
!:  lda pg_alpha,x
    jmp ne_put
ne_step_down:
    jsr ne_index
    dex
    bpl !+
    ldx #pg_alpha_end - pg_alpha - 1
!:  lda pg_alpha,x
    jmp ne_put
// X = position of the character at the cursor in pg_alpha (0 if not found)
ne_index:
    ldx pg_cur
    lda hi_name,x
    ldx #pg_alpha_end - pg_alpha - 1
!:  cmp pg_alpha,x
    beq !+
    dex
    bpl !-
    ldx #0
!:  rts

// hi_name into the new entry of the table
ne_copy:
    ldx hi_rank
    jsr hi_rec_y
    ldx #0
!:  lda hi_name,x
    sta hi_table,y
    iny
    inx
    cpx #HI_NAME
    bne !-
    rts

// the new entry with the cursor (blinking underline)
ne_draw:
    jsr ne_copy
    ldx hi_rank
    jsr hof_entry
    lda pg_blink
    and #8
    beq !+
    lda hi_rank                 // underline under the cursor character
    clc
    adc #3
    tax
    lda pg_cur
    asl
    adc pg_cur
    asl
    adc #HX + 24
    jsr tp_at
    inc tp_y
    lda #0
    sta tp_sh
    lda #TC_ORANGE
    sta tp_c
    lda #$5f
    jsr tp_char
    lda #TC_SHADE
    sta tp_sh
!:  rts

// ============================================================== MISSION ACCOMPLISHED
// screen black (palette 2 shown); the page, fade in, wait for fire
mission_page:
    jsr page_begin              // built in palette 0 while palette 2 (black) is shown
    lda #TC_GOLD
    sta tp_c
    lda #20
    sta pg_key
    lda #<s_mis
    ldx #>s_mis
    ldy #0
    jsr pg_big
    lda #TC_WHITE
    sta tp_c
    lda #30
    sta pg_key
    lda #<s_mis2
    ldx #>s_mis2
    ldy #3
    jsr pg_small
    lda #30
    sta pg_key
    lda #<s_mis3
    ldx #>s_mis3
    ldy #4
    jsr pg_small
    lda #TC_BLUE
    sta tp_c
    lda #11
    sta pg_key
    lda #<s_final
    ldx #>s_final
    ldy #7
    jsr pg_small
    lda #TC_GOLD                // score, big: 6 digits * 12 px
    sta tp_c
    lda #128 - 36
    ldx #9
    jsr tp_at
    lda #2
    sta tp_scale
    lda #1                      // all six digits, like the HUD
    sta tp_zi
    lda #<score_bcd
    ldx #>score_bcd
    jsr tp_score
    lda #0
    sta tp_zi
    lda #MUS_TITLE
    jsr music_play
    jsr pal_snapshot            // fade in from black (transition.asm)
    lda #1
    sta fd_step
!:  jsr fade_wait
    lda fd_step
    jsr fade_set
    inc fd_step
    lda fd_step
    cmp #17
    bne !-
    RunDma(job_tp_font)         // the fade used $0800-$0BFF (fade_tab, pal_snap): font back for line 14
    lda #0
    sta pal_show
    lda #PALSEL_GAME
    sta VIC_PALSEL
    jsr fire_reset
    lda #0
    sta pg_blink
!:  jsr shop_frame
    inc pg_blink
    lda pg_blink
    and #15
    bne !+
    lda #22
    sta pg_key
    lda #<s_cont
    ldx #>s_cont
    jsr pg_line14
!:  lda sh_press
    and #$10
    beq !--
    rts
