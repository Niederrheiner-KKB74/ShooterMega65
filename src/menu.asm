// ----------------------------------------------------------------------------
// Menu overlay (Stage 16). The high-score list, the text pages, the name entry and the end screen (hiscore.asm,
// textpage.asm, hipages.asm) only run while no game runs. They are assembled for swap_start (the start of
// boss.asm/ground.asm), written to the file HIMENU, loaded to attic RAM at start and swapped in by DMA:
//   menu_in:  bank-0 area -> ATTIC_MSAVE (game code as it is), ATTIC_MENU -> bank-0 area
//   menu_out: bank-0 area -> ATTIC_MENU (keeps the list and the other menu variables), ATTIC_MSAVE -> area
// Nothing in boss.asm/ground.asm may be used between menu_in and menu_out. Attic RAM only.
// ----------------------------------------------------------------------------
.const ATTIC_MENU  = $80F0000
.const ATTIC_MSAVE = $80F8000
.const MENU_BYTES  = menu_end - menu_start
.errorif (menu_end > swap_end), "menu overlay larger than boss.asm + ground.asm"
.errorif (MENU_BYTES > $8000), "menu overlay larger than 32 KB"

menu_on: .byte 0

// file HIMENU -> attic (KERNAL load at start); carry set = failed
menu_load:
    lda #(ATTIC_MENU >> 16) & $0f
    sta lv_bank
    lda #0
    tax
    ldy #(>MENU_BYTES) + 1
    jsr lv_dst
    lda #<name_menu
    ldx #>name_menu
    ldy #name_menu_end - name_menu
    jmp load_seq_to
name_menu: .text "HIMENU"
name_menu_end:

menu_in:
    lda menu_on
    bne !+
    RunDma(job_menu_save)
    RunDma(job_menu_in)
    lda #1
    sta menu_on
!:  rts

menu_out:
    lda menu_on
    beq !+
    RunDma(job_menu_keep)
    RunDma(job_menu_back)
    lda #0
    sta menu_on
!:  rts

job_menu_save: DmaJob(DMA_CMD_COPY, swap_start, ATTIC_MSAVE, MENU_BYTES)
job_menu_in:   DmaJob(DMA_CMD_COPY, ATTIC_MENU, swap_start, MENU_BYTES)
job_menu_keep: DmaJob(DMA_CMD_COPY, swap_start, ATTIC_MENU, MENU_BYTES)
job_menu_back: DmaJob(DMA_CMD_COPY, ATTIC_MSAVE, swap_start, MENU_BYTES)
