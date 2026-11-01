// ----------------------------------------------------------------------------
// Shop overlay (Stage 3b), see docs/stage3.md and docs/design.md §15.
//
// A shop event of the level (mid / end) sets shop_req. The main loop then calls
// shop_run, which pauses the game:
//   1. all objects are removed and both screen buffers are rebuilt without them,
//      the player sprites are hidden, the shop palettes replace banks 13-15
//      (rocket and explosions: no objects exist while the shop is open);
//   2. "ENTERING SHOP" for 3 seconds (fire skips it);
//   3. the 4x4 item grid; the joystick moves a blinking frame between the cells
//      that can be bought (and EXIT), fire opens "PURCHASE ITEM?" with YES / NO.
// Pictures are drawn by replacing background tokens in both screen buffers
// (the game is paused, so nothing else changes them). Leaving the shop rebuilds
// the frame from the ring buffer, which removes the panel again.
//
// Glyphs: file SHOP (tools/make_shop.py) loaded to SHOP_ADDR ($44000, char $1100),
// behind the landscape glyphs (a level has at most 256 glyphs = $40000-$43FFF).
// Token maps, items, prices and palettes: build/gen/shop.inc.
// ----------------------------------------------------------------------------
.const SHOP_ADDR  = $044000
.const SHOP_CHAR  = SHOP_ADDR / 64           // $1100
.const PAL_SHOP_N = (13 << 4) | $0f          // normal
.const PAL_SHOP_D = (14 << 4) | $0f          // dimmed: cannot be bought
.const PAL_SHOP_H = (15 << 4) | $0f          // highlighted: cursor / selected button
.const MSG_FRAMES = 150                      // 3 s
.const FIRE_RELEASE = 8                      // fire must be released this many frames before a press counts
.const REPEAT_FIRST = 18                     // joystick auto repeat (frames)
.const REPEAT_NEXT  = 8
.const MAX_COUNT    = 9                      // bombs, invulnerability, lives (one HUD digit)
.const IT_EXIT = 8

.errorif (SHOP_GLYPHS > 255), "shop glyphs exceed 255"
.errorif (TILE_ADDR + 256*64 > SHOP_ADDR), "shop glyphs overlap the landscape glyphs"
.errorif (SHOP_ADDR + SHOP_GLYPHS*64 > PIXIE_ADDR), "shop glyphs overlap the pixie glyphs (160 reserved)"
.errorif (PANEL_ROW0 + PANEL_ROWS > VIS_ROWS - 1), "shop panel below the visible rows"
.errorif (PANEL_COL0 + PANEL_COLS > BG_TOKENS), "shop panel wider than the background"

// ---------------------------------------------------------------- items owned
bomb_count:  .byte 0        // order matters: hud.asm reads bomb_count, bomb_count+1
inv_count:   .byte 0
has_missile: .byte 0

// new game: nothing bought yet (pl_power is reset by player_new_game)
shop_reset:
    lda #0
    sta bomb_count
    sta inv_count
    sta has_missile
    jmp special_reset

// ============================================================== loading (KERNAL)
// file SHOP: 'SH', glyph count (16 bit), glyphs. Carry set = failed (message printed).
shop_load:
    lda #<name_shop
    ldx #>name_shop
    ldy #name_shop_end - name_shop
    jsr load_seq
    bcs !fail+
    RunDma(job_shophdr)
    lda shop_hdr
    cmp #$53                    // 'S'
    bne !bad+
    lda shop_hdr+1
    cmp #$48                    // 'H'
    bne !bad+
    lda shop_hdr+2              // count * 64
    sta job_shopglyphs+DMA_COUNT+1
    lda #0
    sta job_shopglyphs+DMA_COUNT
    lsr job_shopglyphs+DMA_COUNT+1
    ror job_shopglyphs+DMA_COUNT
    lsr job_shopglyphs+DMA_COUNT+1
    ror job_shopglyphs+DMA_COUNT
    RunDma(job_shopglyphs)
    clc
    rts
!bad:
    lda #<msg_bad
    ldx #>msg_bad
    jsr print
!fail:
    sec
    rts

// ============================================================== shop
shop_run:
    lda #0
    sta shop_req
    jsr objects_init            // the overlay replaces background tokens: no pixies may cover it
    lda #MUS_SHOP
    jsr music_play
    jsr build_frame             // rebuild both buffers without objects
    jsr wait_vblank
    jsr flip
    jsr build_frame
    jsr wait_vblank
    jsr flip
    lda #0
    sta VIC_SPREN               // player hidden
    jsr shop_palettes
    lda joy
    sta sh_prev
    lda #0                      // fire must be released first
    sta sh_rel

    // ---------------- "ENTERING SHOP"
    lda #<shop_msg_glyph
    ldx #>shop_msg_glyph
    ldy #0
    jsr blit_msg
    lda #MSG_FRAMES
    sta sh_timer
!:  jsr shop_frame
    lda sh_press
    and #$10
    bne !+
    dec sh_timer
    bne !-

    // ---------------- item grid
!:  lda #$ff
    sta sh_cursor
    jsr shop_states             // also puts the cursor on the first cell that can be bought
    jsr draw_panel
!loop:
    jsr shop_frame
    lda sh_press
    and #$10
    bne !fire+
    jsr joy_dir                 // A = direction bits 0-3 (new press or auto repeat)
    beq !loop-
    jsr move_cursor
    lda #SFX_CURSOR
    jsr sfx_play
    jsr draw_panel
    jmp !loop-
!fire:
    ldx sh_cursor
    lda item_code,x
    cmp #IT_EXIT
    beq !leave+
    jsr purchase_dialog
    jsr shop_states
    jsr draw_panel
    jmp !loop-
!leave:
    lda #SFX_SELECT
    jsr sfx_play
    lda #MUS_LEVEL1
    jsr music_play
    jsr shop_restore
    lda #INV_FRAMES             // a moment to get oriented again
    sta pl_inv
    jmp build_frame             // back buffer without the panel; the main loop shows it

// "PURCHASE ITEM?" YES / NO for the cell at the cursor; buys on YES
purchase_dialog:
    lda #SFX_SELECT
    jsr sfx_play
    lda #1                      // NO preselected
    sta sh_choice
!draw:
    jsr dialog_pals
    lda #<shop_dlg_glyph
    ldx #>shop_dlg_glyph
    ldy #1
    jsr blit_msg
!:  jsr shop_frame
    lda sh_press
    and #$10
    bne !fire+
    jsr joy_dir
    and #%1100                  // left / right
    beq !-
    lda sh_choice
    eor #1
    sta sh_choice
    lda #SFX_CURSOR
    jsr sfx_play
    jmp !draw-
!fire:
    lda sh_choice
    bne !done+
    jsr buy
    lda #SFX_BUY
    jsr sfx_play
!done:
    rts

// one paused frame: wait for the vertical blank, blink, read keys and joystick
shop_frame:
    jsr wait_vblank
    jsr sound_frame
    inc sh_blink
    ldx #0                      // highlight colour changes every 8 frames
    lda sh_blink
    and #8
    beq !+
    ldx #3
!:
    lda shop_blink,x            // R, G, B of the two blink colours (offsets 0-2, 3-5)
    sta PAL_RED+$f4
    lda shop_blink+1,x
    sta PAL_GREEN+$f4
    lda shop_blink+2,x
    sta PAL_BLUE+$f4
    jsr read_keys               // X / RUN-STOP still return to BASIC
    lda #0
    sta special_req
    sta inv_req
    jsr read_joystick
    lda sh_prev                 // sh_press = buttons pressed since the last frame
    eor #$ff
    and joy
    sta sh_press
    lda joy
    sta sh_prev
    // fire counts only after it was released for FIRE_RELEASE frames (contact bounce gave double actions)
    lda sh_rel
    cmp #FIRE_RELEASE
    bcs !+
    lda sh_press
    and #%11101111
    sta sh_press
!:  lda joy
    and #$10
    beq !up+
    lda #0                      // held: count again from 0
    sta sh_rel
    rts
!up:
    lda sh_rel
    cmp #$ff
    beq !+
    inc sh_rel
!:  rts

// direction with auto repeat: A = new direction bits (0 = none), Z flag set accordingly
joy_dir:
    lda joy
    and #$0f
    bne !held+
    sta sh_rep
    rts
!held:
    lda sh_press
    and #$0f
    beq !+
    lda #REPEAT_FIRST           // new press
    sta sh_rep
    lda sh_press
    and #$0f
    rts
!:  dec sh_rep
    bne !none+
    lda #REPEAT_NEXT
    sta sh_rep
    lda joy
    and #$0f
    rts
!none:
    lda #0
    rts

// ---------------------------------------------------------------- items
// sh_ok[cell] = 1 if it can be bought now (or is EXIT); tok_pal[cell] = its palette.
// The cursor moves to the first such cell if its own cell is no longer one.
shop_states:
    ldx #15
!cell:
    lda #0
    sta sh_ok,x
    lda item_code,x
    beq !set+
    cmp #IT_EXIT
    beq !ok+
    jsr item_allowed
    bcc !set+
    lda credit_bcd              // affordable: credits >= price (BCD compares like binary)
    cmp item_price_hi,x
    bcc !set+
    bne !ok+
    lda credit_bcd+1
    cmp item_price_lo,x
    bcc !set+
!ok:
    lda #1
    sta sh_ok,x
!set:
    dex
    bpl !cell-
    ldx sh_cursor
    bmi !first+
    lda sh_ok,x
    bne cell_pals
!first:
    ldx #0
!:  lda sh_ok,x
    bne !+
    inx
    bne !-                      // EXIT is always ok
!:  stx sh_cursor
cell_pals:
    ldx #15
!:  lda #PAL_SHOP_D
    ldy sh_ok,x
    beq !set+
    lda #PAL_SHOP_N
    cpx sh_cursor
    bne !set+
    lda #PAL_SHOP_H
!set:
    sta tok_pal,x
    dex
    bpl !-
    lda #PAL_SHOP_N
    sta tok_pal+16
    rts

// item code A (1-7) for cell X: carry set if the item may be bought (apart from the price)
item_allowed:
    cmp #4
    bcs !+
    cmp pl_power                // shot level 2-4: needs exactly the previous level
    beq !yes+
    clc
    rts
!:  bne !+
    lda has_missile             // missile: once
    beq !yes+
    clc
    rts
!:  cmp #5
    bne !+
    lda inv_count
    jmp !max+
!:  cmp #6
    bne !+
    lda bomb_count
    jmp !max+
!:  lda pl_lives               // 7: extra life
!max:
    cmp #MAX_COUNT              // carry clear if below the maximum
    bcc !yes+
    clc
    rts
!yes:
    sec
    rts

dialog_pals:
    jsr cell_pals
    ldx #PAL_SHOP_H
    ldy #PAL_SHOP_N
    lda sh_choice
    beq !+
    ldx #PAL_SHOP_N
    ldy #PAL_SHOP_H
!:  stx tok_pal+17
    sty tok_pal+18
    rts

// buy the item at the cursor: pay, then apply it
buy:
    ldx sh_cursor
    sed
    sec
    lda credit_bcd+1
    sbc item_price_lo,x
    sta credit_bcd+1
    lda credit_bcd
    sbc item_price_hi,x
    sta credit_bcd
    cld
    lda item_code,x
    cmp #4
    bcs !+
    adc #1                      // shot level 2-4
    sta pl_power
    bne !hud+
!:  bne !+
    lda #1
    sta has_missile
    bne !hud+
!:  cmp #5
    bne !+
    inc inv_count
    bne !hud+
!:  cmp #6
    bne !+
    inc bomb_count
    bne !hud+
!:  inc pl_lives
!hud:
    jsr hud_score_changed       // credits, lives and counters are redrawn
    jmp hud_update

// ---------------------------------------------------------------- cursor
// move in the joystick direction A (bits 0 up, 1 down, 2 left, 3 right) to the nearest
// cell that can be bought: score = distance across * 8 + distance along the direction
move_cursor:
    sta sh_dir
    lda #$ff
    sta sh_best
    sta sh_bscore
    lda sh_cursor
    and #3
    sta sh_cc
    lda sh_cursor
    lsr
    lsr
    sta sh_cr
    ldx #15
!cell:
    lda sh_ok,x
    beq !next+
    cpx sh_cursor
    beq !next+
    txa
    and #3
    sec
    sbc sh_cc
    sta sh_dc                   // column difference (signed)
    txa
    lsr
    lsr
    sec
    sbc sh_cr
    sta sh_dr                   // row difference (signed)
    lda sh_dir
    and #%0011
    beq !horiz+
    and #1                      // vertical: along = -dr (up) or dr (down), across = |dc|
    beq !+
    lda #0
    sec
    sbc sh_dr
    jmp !v+
!:  lda sh_dr
!v: sta sh_along
    lda sh_dc
    jmp !score+
!horiz:
    lda sh_dir
    and #%0100
    beq !+
    lda #0                      // left
    sec
    sbc sh_dc
    jmp !h+
!:  lda sh_dc                   // right
!h: sta sh_along
    lda sh_dr
!score:
    bpl !+                      // across = |A|
    eor #$ff
    clc
    adc #1
!:  asl
    asl
    asl
    sta sh_score
    lda sh_along
    beq !next+                  // not in that direction
    bmi !next+
    clc
    adc sh_score
    cmp sh_bscore
    bcs !next+
    sta sh_bscore
    stx sh_best
!next:
    dex
    bpl !cell-
    lda sh_best
    bmi !+
    sta sh_cursor
!:  jmp cell_pals

// ---------------------------------------------------------------- drawing
draw_panel:
    lda #<shop_panel_glyph
    ldx #>shop_panel_glyph
    ldy #2
    // fall through
// A/X = glyph map, Y = picture (0 message, 1 dialog, 2 panel); the attribute map
// follows the glyph map. Writes into both screen buffers.
blit_msg:
    sta tmp
    stx tmp+1
    lda pic_rows,y
    sta sh_rows
    lda pic_cols,y
    sta sh_cols
    lda pic_row0,y
    sta sh_row
    lda pic_col0,y
    asl
    sta sh_col2
    lda pic_rows,y              // attribute map = glyph map + rows * cols
    ldx pic_cols,y
    jsr mul8                    // A * X -> sh_size (16 bit)
    clc
    lda tmp
    adc sh_size
    sta tmp2
    lda tmp+1
    adc sh_size+1
    sta tmp2+1
    lda #0
    sta sh_buf
!buf:
    lda tmp                     // restart the maps for every buffer
    sta sh_g+1
    lda tmp+1
    sta sh_g+2
    lda tmp2
    sta sh_a+1
    lda tmp2+1
    sta sh_a+2
    ldx sh_row
    lda sh_rows
    sta sh_r
!row:
    // screen: SCREEN_A/B + row * 170 + col * 2, colour RAM the same offset in COLOUR_A/B
    clc
    lda row_ofs_lo,x
    adc sh_col2
    sta scr_ptr
    sta col_ptr
    lda row_ofs_hi,x
    adc #0
    sta sh_m
    ldy sh_buf
    clc
    adc buf_scr_hi,y
    sta scr_ptr+1
    lda sh_m
    clc
    adc buf_col_hi,y
    sta col_ptr+1
    lda #(SCREEN_A >> 16)
    sta scr_ptr+2
    lda #<(COLRAM >> 16)
    sta col_ptr+2
    lda #0
    sta scr_ptr+3
    lda #>(COLRAM >> 16)
    sta col_ptr+3
    ldy #0
    ldz #0
!tok:
sh_g:
    lda $ffff,y
    sta ((scr_ptr)),z
    lda #$08                    // colour byte 0: NCM
    sta ((col_ptr)),z
    inz
    lda #>SHOP_CHAR
    sta ((scr_ptr)),z
    phx
sh_a:
    lda $ffff,y
    tax
    lda tok_pal,x
    plx
    sta ((col_ptr)),z
    inz
    iny
    cpy sh_cols
    bne !tok-
    clc                         // next map row (self-modified operands)
    lda sh_g+1
    adc sh_cols
    sta sh_g+1
    bcc !+
    inc sh_g+2
!:  clc
    lda sh_a+1
    adc sh_cols
    sta sh_a+1
    bcc !+
    inc sh_a+2
!:  inx
    dec sh_r
    beq !+
    jmp !row-
!:
    inc sh_buf
    lda sh_buf
    cmp #2
    beq !+
    jmp !buf-
!:  ldz #0
    rts

// A * X -> sh_size (both < 256)
mul8:
    sta sh_m
    lda #0
    sta sh_size
    sta sh_size+1
    cpx #0
    beq !done+
!:  clc
    lda sh_size
    adc sh_m
    sta sh_size
    bcc !+
    inc sh_size+1
!:  dex
    bne !--
!done:
    rts

// ---------------------------------------------------------------- palettes
// banks 13-15 <- normal, dimmed, highlight shop palettes
shop_palettes:
    ldx #15
!:  lda shop_pal,x
    sta PAL_RED+$d0,x
    lda shop_pal+16,x
    sta PAL_GREEN+$d0,x
    lda shop_pal+32,x
    sta PAL_BLUE+$d0,x
    lda shop_pal_dim,x
    sta PAL_RED+$e0,x
    lda shop_pal_dim+16,x
    sta PAL_GREEN+$e0,x
    lda shop_pal_dim+32,x
    sta PAL_BLUE+$e0,x
    lda shop_pal_hi,x
    sta PAL_RED+$f0,x
    lda shop_pal_hi+16,x
    sta PAL_GREEN+$f0,x
    lda shop_pal_hi+32,x
    sta PAL_BLUE+$f0,x
    dex
    bpl !-
    lda #PAL_SHOP_N
    sta tok_pal+16
    sta tok_pal+17
    sta tok_pal+18
    rts

// banks 13-15 back to the game palette
shop_restore:
    ldx #47
!:  lda palette_data+$d0,x
    sta PAL_RED+$d0,x
    lda palette_data+$1d0,x
    sta PAL_GREEN+$d0,x
    lda palette_data+$2d0,x
    sta PAL_BLUE+$d0,x
    dex
    bpl !-
    rts

// ---------------------------------------------------------------- data
pic_rows: .byte MSG_ROWS, DLG_ROWS, PANEL_ROWS
pic_cols: .byte MSG_COLS, DLG_COLS, PANEL_COLS
pic_row0: .byte MSG_ROW0, DLG_ROW0, PANEL_ROW0
pic_col0: .byte MSG_COL0, DLG_COL0, PANEL_COL0
buf_scr_hi: .byte >(SCREEN_A & $ffff), >(SCREEN_B & $ffff)
buf_col_hi: .byte >COLOUR_A, >COLOUR_B
.errorif ((<COLOUR_A) != 0 || (<COLOUR_B) != 0 || (<SCREEN_A) != 0 || (<SCREEN_B) != 0), "buffers must be page aligned"
.errorif ((SCREEN_A >> 16) != (SCREEN_B >> 16)), "screen buffers must share a bank"

sh_prev:   .byte 0
sh_rel:    .byte 0                  // frames since fire was released
sh_press:  .byte 0
sh_rep:    .byte 0
sh_timer:  .byte 0
sh_blink:  .byte 0
sh_cursor: .byte 0
sh_choice: .byte 0
sh_dir:    .byte 0
sh_best:   .byte 0
sh_bscore: .byte 0
sh_score:  .byte 0
sh_along:  .byte 0
sh_cc:     .byte 0
sh_cr:     .byte 0
sh_dc:     .byte 0
sh_dr:     .byte 0
sh_rows:   .byte 0
sh_cols:   .byte 0
sh_row:    .byte 0
sh_col2:   .byte 0
sh_r:      .byte 0
sh_buf:    .byte 0
sh_m:      .byte 0
sh_size:   .word 0
sh_ok:     .fill 16, 0
tok_pal:   .fill 19, PAL_SHOP_N      // 0-15 cells, 16 frame, 17 YES, 18 NO
shop_hdr:  .fill 4, 0

name_shop: .text "SHOP"
name_shop_end:
job_shophdr:    DmaJob(DMA_CMD_COPY, LEVEL_BUF, shop_hdr, 4)
job_shopglyphs: DmaJob(DMA_CMD_COPY, LEVEL_BUF + 4, SHOP_ADDR, 0)

#import "../build/gen/shop_data.inc"
