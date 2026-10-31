# Working rules for ShooterMega65

1. **Toolchain.** Use KickAssembler 65CE02 5.25 (`KickAss65CE02-5.25.jar`, SHA-256
   `5d8544280dae2d018c79151d8c7b877eca1fb994096e54ca380b26d0cd79f847`) with `.cpu _45gs02`.
   Build only through `python3 tools/build.py`. The jar and the MEGA65 ROM are never committed
   (`tools/bin/` is git-ignored).
2. **Hardware before XEMU.** XEMU is not authoritative for RRB/GOTOX scaling, RRB timing or audio
   DMA. Graphics and sound changes count as confirmed only after the owner has tested them on real MEGA65
   hardware. Rules inherited from Vyper (confirmed there on hardware):
   - H320 with `CHRXSCL $D05A = 120`, GOTOX in logical 320-px coordinates.
   - RRB double buffering: `$D051` bit 7 = 0.
   - GOTOX token: screen `X lo, (X hi & 3) | $10 | yoffset<<5`, colour `$90,$00`; glyph colour `$08, pal`.
   - Audio DMA: write `$D72A/$D72B` before `$D72C`; test `$D711` bit 7 only.
   - KERNAL I/O: `SETBNK ($FF6B)` before `SETNAM`.
   - `$20000–$3FFFF` is ROM, never a data target.
3. **Memory.** Check `docs/memory_map.md` before using any address and update it in the same change.
   Guard regions with assembler checks (`.errorif` / `.if … .error`).
4. **Stages.** Every test stage ships PRG, D81, sources and reproducible build instructions in
   `releases/stageN/` and a `docs/stageN.md` with a hardware checklist. When the owner confirms a stage
   on hardware, it is tagged `stageN-stable` and its release folder is not changed again.
5. **Reports.** Keep these separate: assembled, emulator smoke test, owner-confirmed on hardware.
   Never claim hardware success without the owner's confirmation.
6. **Diagnosis first.** Find the cause before making large changes; prefer small, traceable commits.
7. **Vyper reuse.** Port proven modules from `Niederrheiner-KKB74/Vyper_for_Mega65` (loader, ZX0 unpacker,
   audio DMA, D81/highscore) into clean modules here, noting the Vyper source stage in a comment.
8. **Docs.** Keep `docs/design.md` (architecture and decisions) and `docs/memory_map.md` current.
