# Aircraft integration candidate

Built from this branch with the pinned KickAss65CE02 5.25 and `python3 tools/build.py`.
Sources are in `src/`, asset sources in `assets/art/reference-board/`, and the
build/integration tools in `tools/`. Full build instructions, validation and
hardware checklist: [docs/stage1-aircraft.md](../../docs/stage1-aircraft.md).

Player normal/left/right and all four animated air-enemy types are integrated.
Other graphics remain the Stage-1 placeholders. PRG: 39265 bytes, exclusive end
`$B960`. Assembled, asset-regression and collision-boundary checks passed; D81
read-back passed. Repeated build produced identical PRG bytes.

Emulator startup did not reach a confirmed game run in this session. **No
emulator or hardware success is claimed.** These are test candidates, not a
stable or hardware-accepted stage. The existing `releases/stage1/` is untouched.

Mount `SHOOTER65.D81`, `LOAD "SHOOTER",8`, then `RUN`. Joystick port 2;
X or RUN/STOP exits. See SHA256SUMS.txt for file checksums.
