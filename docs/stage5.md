# Stage 5 – Music and sound effects

Branch `stage5`, based on `stage4b-stable`. Release files are in `releases/stage5/`.
Design details: `docs/design.md` §10, music format: `docs/music_json.md`.

## What is new
- **Music player** (`sound.asm`): three voices on SID 1, mirrored to SID 3 (centre). Patterns, hard restart,
  wave tables (drums), arpeggios, vibrato, pulse sweep. Data from the new file `MUSIC` on the D81 (2,859 bytes),
  made by `tools/build_music.py` from `music/*.json`.
- **Four pieces composed by Claude** (score: `tools/compose_music.py`, instead of PR #12):

  | Piece | Use | Key, tempo | Length |
  |---|---|---|---|
  | `level1` "Coastal Run" | level, loops (from bar 5) | D minor, 125 BPM | 44 bars, 84.5 s: intro, A, A′, B (saw lead), breakdown, A, turnaround |
  | `shop` "Supply Depot" | while the shop is open, loops | F major, ~107 BPM | 16 bars, 35.8 s: walking bass, maj7/m7 chords, flute-like lead |
  | `game_over` | last plane lost, then level music | D minor | 5.8 s |
  | `level_clear` | level end, then level music | D major | 5.8 s |
- **14 sound effects** on SID 2, mirrored to SID 4 (`music/sfx.json`): shots, missile, hit, explosion, big
  explosion, player hit, player destroyed, bomb, coin, shield capsule, invulnerability, shop cursor, select, buy.
  Fixed voice and priority per effect, so shots never cut off an explosion.
- **MUSICTEST** on the D81: keys 1–4 play the pieces, T plays a 440 Hz test tone (A-4), X returns to BASIC.

## Verification so far
| Check | Result |
|---|---|
| `build_music.py`: all pieces valid, voices equal length, loop rows aligned; `MUSIC` 2,859 of 4,096 bytes | ✔ |
| Assembly, D81 with `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `L1GFX`, `L1DAT` read back | ✔ |
| XEMU audio recording (SDL disk driver) of all pieces: sound in both channels, no clipping, structure visible (breakdown quieter, loop) | ✔ |
| XEMU: game with shop: level music → shop music → level music, effects audible, RRB overflow 0 | ✔ |
| XEMU: full level with sound, both shops, level end with fanfare, into the second pass (frame 16,805), RRB overflow 0 | ✔ |
| XEMU tuning: test tone 435.3 Hz (expected 440 at a 1 MHz SID clock) – XEMU is not authoritative for audio | open on hardware |
| **Real MEGA65** | **open – please test** |

## Hardware test checklist
1. `LOAD "MUSICTEST",8` / `RUN`: the level music starts. Keys 2, 3, 4: shop music, game-over jingle, level-clear
   fanfare; 1: level music again. Music sounds from both sides.
2. Key **T**: a steady test tone. With a tuner app it should show **A, 440 Hz**. If it is clearly off (for example
   433 Hz), please tell me the value: the frequency table is adjusted with one constant.
3. Notes start cleanly (no dropped or "swallowed" notes), drums (kick, snare) are recognisable, no clicks at the
   loop point of the level music (after about 1:24).
4. `LOAD "SHOOTER",8` / `RUN`: level music during the game; shots, hits, explosions, capsules, bomb, missile,
   invulnerability have their own sounds and do not interrupt the music.
5. Shop: shop music while it is open, cursor/select/buy sounds; level music again afterwards.
6. Losing the last plane: game-over jingle, then the level music. Level end (about 4 minutes): fanfare.
7. X (in the game and in MUSICTEST): back to BASIC, silence.
