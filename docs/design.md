# ShooterMega65 – Technical Design

Status: Stage 2 confirmed on real hardware by the owner on 01.11.2026 (`stage2-stable`). Stage 3 (branch `stage3`)
in progress: capsule/weapon rules, level files (research: `docs/level_format.md`, JSON format for level design:
`docs/level_json.md`).
Items marked **(decision)** need the
project owner's confirmation. Items marked **(HW)** have to be checked on real
MEGA65 hardware, because XEMU is not authoritative for them (see Vyper rule 19).

## 1. Game summary

Vertically scrolling shooter for the MEGA65, 45GS02 assembly (KickAssembler 65CE02 5.25).

- The player flies an armed aircraft that moves freely over the whole screen.
- The landscape scrolls from top to bottom at a fixed speed, with a different theme in each level.
- There are fixed and moving ground targets. Air enemies fly in formations and shoot.
- Ground objects also attack the player.
- Items and persons on the ground are collected by flying over them.
- A large boss ends every level.

## 2. Display

| Property | Choice |
|---|---|
| Mode | H320 / V200 (`$D031 = $40`), PAL, 40.5 MHz CPU |
| Background | 16-colour (NCM) characters, 16×8 pixels, 64 bytes per glyph |
| Colours | 16-colour sub-palettes (palette banks). Each tile and each pixie selects its bank through colour-RAM byte 1 (`bank<<4 \| $0F`). Nibble 0 is transparent in overlays and shows the background colour in tiles. Nibble 15 shows colour-RAM byte 1's colour, which is set to the bank's colour 15, so every bank offers 15 colours plus transparency. |
| Moving objects | RRB "pixies" (GOTOX overlays in the same NCM format) |
| Player | 2 hardware sprites in 16-colour mode (32×24) |
| Glyph addressing | `CHR16` + `FCLRHI` (`$D054 = $45`); all game glyphs are ≥ `$1000` |

The screen uses 320×200 logical pixels. With NCM, the levels can use several
16-colour palettes at the same time, for example one each for land, water, buildings and enemies.

### 2.1 The hidden left column
Text starts 16 logical pixels left of the side border (`TEXTXPOS = 48` native, border
width 80). Every row therefore has **21** background chars (336 px), and the first 16 px
are hidden under the border. A pixie at screen x uses GOTOX `x + 16`. Objects can therefore
enter from the left edge without the software cropping that Vyper needed
(`offscreen.asm`). The right edge needs no special handling, because pixels past x = 336
fall under the right border.

### 2.2 Hardware rules inherited from Vyper (confirmed on real hardware)
1. H320 with `CHRXSCL $D05A = 120`; GOTOX values are logical 320-px coordinates.
2. RRB double buffering: `$D051` bit 7 (NORRDEL) = 0. It is written on every flip.
3. GOTOX token format: screen byte 0 = X low, byte 1 = `X bits 8-9 | $10 | (yoffset<<5)`.
   Colour bytes are `$90,$00` (GOTOX, no background paint). Glyph tokens use colour
   `$08` (NCM) followed by the palette byte.
4. Audio DMA: write `$D72A/$D72B` before `$D72C`, and check `$D711` bit 7 only. This applies when sound is added.
5. KERNAL file I/O: call `SETBNK ($FF6B)` before `SETNAM`. This applies when loading levels.

## 3. Vertical scrolling

```
 map (bottom→top)        ring buffer (32 slots, stored twice)        back buffer (27 rows)
 row m  ──decode──▶  slot (31-m)&31  and  slot+32   ──1 DMA/frame──▶  rows 0..25   + null row 26
```

- **Map rows** contain 21 glyph indices plus 21 colour bytes (palette per tile). The engine
  decodes one row into the ring every 8 pixels of scrolling, writing both copies.
- **Ring order** is chosen so that display rows 0..25 are 26 consecutive slots. Storing the ring
  twice removes the wrap-around, so a single DMA copies the visible screen part (4,420
  bytes) and a second one copies the colour part into the back buffer every frame. The copy also
  removes the previous frame's pixies, so no per-row clearing is needed.
- **Fine scroll** moves `TEXTYPOS` (`$D04E`): `88 + 2·(scroll_px & 7)` physical
  raster lines. Row 0 starts up to 8 px above the top border (104). `DISPROWS = 26` fetches 27 rows. The 27th row is a
  static "null" row under the bottom border.
- **Double buffering**: screen A/B (bank 5) and colour A/B (colour RAM). The flip during the
  vertical blank writes `$D060-62`, `$D064-65`, `$D04E` and `$D051`.
- **Speed**: `SCROLL_SPEED` is 8.8 fixed point: 0.5 px/frame (25 px/s), confirmed by the owner on 31.10.2026.
- Ground objects store screen coordinates and add `scroll_delta` (the whole pixels scrolled
  this frame), so they stay locked to the landscape.

Cost per frame: two DMA jobs of 4,420 bytes, plus one 21-column decode every 16 frames at the current speed.

## 4. RRB pixies

### 4.1 Row layout (85 tokens = 170 bytes, `LINESTEP`)
| Tokens | Content |
|---|---|
| 0–20 | background tiles (from the ring) |
| 21–83 | overlay area: pixie fragments, initially "null" GOTOX(320) tokens |
| 84 | transparent blank glyph. Each row ends at x = 336, exactly at the right border |

Each fragment needs `1 + w` tokens (GOTOX plus w glyphs). A row holds **63 overlay tokens**,
for example 31 one-char fragments. If a fragment does not fit, it is dropped and
counted in `overflow` ($0D). Objects are never corrupted. Whether 85 tokens per row are fast enough at full load
is a **(HW)** test item. Vyper ran 96-token rows.

### 4.2 Glyph layout for vertical positioning
A frame is `w` chars wide and `h` glyph rows high. Column `c`, row `i` is glyph
`PIXIE_CHAR + base + c·(h+1) + i`, and the glyph before each column is blank:

```
[blank] [c0 r0] [c0 r1] … [c0 r(h-1)] [blank] [c1 r0] … [blank]
```

An object at grid y = 8·r0 + k touches rows r0 … r0+h (h+1 rows when k ≠ 0). Each row i
uses glyph i with Y offset k, so the VIC fetches it k lines early and shows the tail of
glyph i-1 on top. Clipping at the top and bottom only skips rows outside 0..25.

### 4.3 Draw order and palettes
Slot ranges define the draw order: ground objects 0–9, air objects 10–29, shots 30–47.
Later fragments are drawn on top. Each object passes its own palette byte, so the same glyphs
can be recoloured, for example to make an enemy flash white when hit.

The current emitter obtains the palette from `frame_pal[obj_fr]`: bank 2 for
the original tank/shots/explosions, banks 3–6 for the four air-enemy types.
Waves cycle fighter → bomber → helicopter → armoured plane. Air enemies keep
their animation base in `obj_airbase` and advance one of three frames every
eight ticks. The original sine paths, firing and wave size remain unchanged.
Frames are contiguous within a type. `--placeholder-art` emits one-frame
animations and four aliases for the original enemy, using the same code path.

Air hitboxes use visible 16×16 or 24×24 bounds, centred in their 16px/32px NCM
canvases, with the existing two-pixel shot allowance. The 16px explosion graphic
is positioned at the target centre. Explosion artwork and its four-frame timing
are unchanged. See `docs/stage1-aircraft.md` for validation and remaining tests.

## 5. Hardware sprites
- Sprites 0+1: the player, 16-colour, 16×24 each, 16-bit sprite pointers (16-byte-aligned table in bank 0,
  data at `$5F000`), sprite palette = palette set 1 (`$D070 = $04`). In 16-colour mode the
  sprite colour register holds the *transparent* index (0). **(HW)**
- Since Stage 2 all six frame pairs of the artwork v2 player (3 exhaust frames, left, normal, right)
  are copied once to `$5F000–$5FBFF`. Changing the frame only rewrites the two 16-bit sprite
  pointers in the vertical blank, so no DMA is needed during play.
- While invulnerable after a hit the sprites blink (enable register toggled every 4 frames).
- Sprites 2–7 are free. Candidates **(decision)**: the player's shadow, option drones, a HUD part, or boss turrets
  that must sit above everything.

## 6. Objects, collisions, gameplay

- Structure-of-arrays tables (`obj_type, kind, x, y (16-bit signed), frame, t, a, b, hp, wave`). Updates go
  through a jump table per type: player shot, air enemy, tank, enemy shot, explosion, bonus item.
- **Kinds** (Stage 2) carry the gameplay values in tables in `objects.asm`: frame, hit points, damage
  to the player's shield, points, explosion size, weapon, firing rate and guaranteed bonus drop.

  | Kind | HP | Shield damage on contact | Points | Weapon (damage) |
  |---|---|---|---|---|
  | fighter (16×16, formation of 6) | 1 | 12 | 100 | red shot (6) |
  | helicopter (16×16, formation of 6) | 2 | 12 | 150 | red shot (6) |
  | bomber (32×32, formation of 3) | 5 | 20 | 300 | fire shot (10) |
  | armoured plane (32×32, formation of 3) | 8 | 24 | 500 | fire shot (10), always drops a bonus |
  | tank (16×16, 4 directions, animated tracks) | 3 | – (ground) | 200 | rocket (14) |

- **Shield** (decided 01.11.2026): the player has `SHIELD_MAX = 48` shield points instead of dying on the first
  contact. Contact with an enemy plane or an enemy shot costs the kind's damage; the plane is destroyed (no points).
  After a hit the player is invulnerable for 1 s. At 0 the plane explodes. **Three lives** (decided 01.11.2026):
  after 3 s the next plane starts with a full shield; after the last one a new game starts.
- **Tanks** (artwork PR #6) drive on the ground in four directions at 0.5 px/frame relative to the landscape,
  turn at the playfield edges and at random, and advance their track phase every 5 frames. Stage 7c: they never
  drive into water. `decode_row` keeps a 21-bit land mask per decoded glyph row (`land_ring`: palette bank ≠ 1;
  coast tiles use the water bank and count as water); `is_water` maps a playfield point to map row
  `(scroll_px + 199 − y) >> 3` and column `(x + 16) >> 4`. A tank turns round when the point just ahead is water
  and never picks a new direction towards water
  (frame = `FR_TANK_N0 + direction·4 + phase`, palette bank 4 shared with the fixed targets).
- **Animation frames**: the first artwork v2 frames per aircraft were different drawings, not phases, which made
  the objects jump. PR #7 replaced them with real effect loops (exhaust flames, helicopter rotor; everything else
  pixel-identical). The player cycles frames 0-2 every 4 frames when flying straight (3/5 when banking), enemies
  cycle their 3 phases every 4 frames. The importer warns if a frame set turns into unrelated drawings again.
- **Bonus capsules** (artwork PR #7, palette bank 12; rules decided 01.11.2026):
  - "S" capsule (16×16): refills **20 % of the shield** (+250 points). Appears **at random** (15 %) when an enemy is shot down.
  - "$" capsules, three sizes, add **credits** (HUD centre, 4 digits, max. 9999): small 10, medium 25, large 50.
    Dropped by **every tank** (small) and by the **last plane of a completed formation**: fighters/helicopters
    small, bombers medium, armoured planes large.
  - Credits are spent in **shops in the middle and at the end of every level**: extra lives and weapon upgrades.
- **Enemy hit points vs. weapon level**: every player shot does `pl_power` damage (1 at the start, raised by
  weapon upgrades in the shops). Hit points: fighter 1, helicopter 2, tank 3, bomber 6, armoured plane 10.
  Capsules drift down slowly and are collected by flying over them.
- Collisions use bounding boxes from the visible pixels of every frame (`frame_hit_*` tables made by the
  importer) with 16-bit signed differences: player shots against air enemies and tanks, and the player
  against enemy planes, enemy shots and bonus items.
- Planned types:
  - formation flyers driven by path tables. The path format follows Vyper's curve interpreter (segments of dx/dy/frames).
  - turret and tank ground units that aim at the player.
  - fixed ground targets: part of the tile map. A target table per level (row, column, hit points, rubble tiles)
    patches the ring rows when the target is destroyed.
  - collectibles (persons, power-ups), and the boss.
- Player weapons (decided 31.10.2026): **one fire button** for an upgradable main gun that hits air and
  ground targets, plus a **special weapon on the space bar** (implemented in a later stage; the key
  is already read from the hardware keyboard queue `$D610` and sets `special_req`).

## 7. Boss
- The boss is a multi-char pixie object, for example 96×64 px = 6 chars × 8 rows, which is 7 tokens per row
  (plus 1 row when it is not aligned). Turrets and weak points are separate objects at fixed offsets, so they can
  be destroyed one by one. Big frames may need DMA-based glyph streaming for animation.
- Scrolling stops (`SCROLL_SPEED = 0`) or loops a short boss-arena section of the map while the boss is alive.

## 8. HUD
**Implemented in Stage 2** (`hud.asm`): two pixie boxes at the top, the 6-digit BCD score on the left
(48×8 px) and the shield box on the right (64×8 px: shield icon and a 48 px bar, green → yellow → red).
Since the lives and credits were added there are three boxes: score + lives (64 px, left), credits (48 px, centre),
shield (64 px, right). Their 11 glyphs sit in the pixie glyph area; they are rebuilt in bank 0 and copied only
when a value changes. Cost: 2 rows × (5 + 4 + 5) tokens.

**Decided (31.10.2026): option 1, a score strip at the top of the screen.** Fine scrolling moves the whole text area, so a HUD made of plain text chars would scroll too. The options were:
1. **A pixie strip at a fixed screen y** (recommended). It is 1–2 rows of 20 glyphs drawn from a small dynamic
   glyph buffer, re-rendered only when the score changes. Its cost is about 42 tokens in 2 rows.
2. Hardware sprites for the score and lives (sprites 2–7, 16-colour, 16 px wide each).
3. A raster split with a second text area. This is the most complex option and risky on hardware.

## 9. Level data and loading
**Stage 3a (implemented):** levels are JSON files (`levels/*.json`, format for ChatGPT: `docs/level_json.md`),
converted by `tools/build_level.py` into two SEQ files per level on the D81: `LnGFX` (landscape glyphs + 4 palettes)
and `LnDAT` (metatile table, row dictionary, row list, event list sorted by map row, formations, path bytecode).
`level.asm` loads both with the KERNAL before the game takes over (Vyper loader rules), unpacks the graphics
and keeps the data at `$50000`. The map, the spawning (formations, tanks, scroll speed) and the enemy movement
(path interpreter: move/sine/aim/wait/fire/loop/end, mirrored formations) all come from the level data.
At the `end` event the level currently repeats. Shop events open the shop (§15, Stage 3b); boss events have no effect yet.

Original plan:
- Per level: a tile set (NCM glyphs and up to n palette banks), a map (21 glyph bytes and 21 colour bytes
  per row, or metatiles to save memory), a spawn script (events keyed by map row) and boss data.
- Loading uses KERNAL SEQ files between levels, following Vyper's loader rules. Files are ZX0-packed, using Vyper Stage 10a2's
  streaming unpacker.
- Memory: chip RAM `$40000–$5FFFF` holds the run-time data, and level data goes to attic RAM if needed
  (see `memory_map.md`).

## 10. Sound
- Music: SID tunes. The MEGA65 has 4 SIDs, so music and sound effects can use separate chips.
- **Implemented in Stage 5 (`sound.asm`, `tools/build_music.py`, score `tools/compose_music.py`):** music on SID 1
  mirrored to SID 3, effects on SID 2 mirrored to SID 4, so both sound from the middle. All pieces and effects are
  in the file `MUSIC` (≤ 8 KB) at `$A000` in bank 0 (Stage 7; before: 4 KB at `$5E000`). Player per frame (called in the vertical blank, also inside the shop):
  row every `tempo` frames, the next row decoded two frames earlier with a hard restart (gate off, ADSR 0) for new
  notes; wave tables, arpeggios, vibrato (step = semitone × depth / 8 / speed, computed at note start), pulse sweep.
  Effects: fixed voice and priority per effect. Pieces: level music (loops), shop music while the shop is open,
  game-over jingle, level-clear fanfare at the `end` event, each followed by the level music. SID clock
  1 MHz (`SID_CLOCK` in `build_music.py`), confirmed on hardware (440 Hz test tone).
- **Decided 01.11.2026:** music on one SID (3 voices), sound effects on another. Music is written as JSON text
  (`docs/music_json.md`, tracker-like: instruments, patterns, one order list per voice), converted at build
  time and played by our own 50 Hz player. By default SIDs 1/2 are panned slightly right and 3/4 slightly left.
- Sample effects: Vyper's audio-DMA driver (`stage10a6_audio_core.asm`), with the register order from §2.2.

## 11. Reuse from Vyper
| Reused | How |
|---|---|
| RRB GOTOX format, H320/CHRXSCL, double buffering | rules in §2.2, new implementation |
| F018A enhanced DMA job format | `hw.asm` `DmaJob` macro |
| D81 writer | `tools/d81.py` (adapted) |
| Later: SEQ loader, ZX0 unpacker, audio DMA, highscore D81 handling | port the modules when needed |

Vyper's stage files are not copied wholesale, because they carry their full history of fixed addresses.

## 12. Roadmap

| Stage | Content | Acceptance |
|---|---|---|
| **1** | Engine prototype: mode, scrolling ring, double-buffered RRB, pixies, sprite player, demo enemies | XEMU smoke test ✔, **real hardware test by owner** |
| **2** | Artwork v2 import, HUD (score + shield bar), shield/damage, bonus items, restart | XEMU ✔, HW open |
| 2b | Lives, game states (title → play → game over), special weapon on space | HW |
| 3 | Level format and tool (PNG/Tiled → tiles/map/script), first real tile set, spawn script | HW |
| 4 | Enemy paths and formations, ground turrets, fixed targets (tile patching) | HW |
| 5 | Collectibles, weapon power-ups, bombs | HW |
| 6 | Boss framework and first boss | HW |
| 7 | Sound (SID music + DMA SFX) | HW |
| 8 | Loader, packed level files, several themed levels, polish | HW |

## 13. Leaving the game
**X** or **RUN/STOP** returns to BASIC (`system.asm`), following Vyper's exit strategy: the VIC-IV
registers and palettes are saved at start and written back with HOTREG off, and HOTREG is restored last.
To make this possible, the game leaves the memory map, the stack, the interrupt sources (only `SEI`),
BASIC's screen RAM and colour RAM `$0000–$0FFF` untouched. On exit it restores zero page, the base page and the stack
pointer and returns with `RTS` to the SYS caller. Every routine with self-modifying DMA lists resets them,
so `RUN` works again after an exit.

## 14. Decisions log
| Date | Decision |
|---|---|
| 31.10.2026 | Scroll speed 0.5 px/frame |
| 31.10.2026 | One fire button; special weapon on the space bar (later stage) |
| 31.10.2026 | Score display at the top of the screen (pixie strip, §8) |
| 31.10.2026 | Artwork made by the owner (with ChatGPT), following `docs/artwork_spec.md` |
| 31.10.2026 | Exit to BASIC with X or RUN/STOP, as in Vyper |
| 01.11.2026 | HUD also shows a shield bar; the player has shield hit points, damage depends on the enemy kind |
| 01.11.2026 | Shield refills come from bonus items left by certain enemies or completed formations |
| 01.11.2026 | Artwork v2 (PR #4) adopted; Stage 1 and Stage 1-aircraft confirmed on hardware |
| 01.11.2026 | Three lives, every new life starts with a full shield |
| 01.11.2026 | Animated four-direction tank (PR #6) adopted |
| 01.11.2026 | Real flame/rotor animations and bonus capsules S / $ in three sizes (PR #7) adopted; credits counter in the HUD |
| 01.11.2026 | Stage 2 confirmed on hardware |
| 01.11.2026 | Shops in the middle and at the end of every level (extra lives, weapon upgrades); enemies have hit points, weapon upgrades raise the damage |
| 01.11.2026 | S capsule: 20 % shield, random drop; $ capsule: completed formation or single ground enemy |
| 01.11.2026 | Levels are stored in separate files, not in the program (format proposal: `docs/level_format.md`) |
| 01.11.2026 | Levels written as JSON text so ChatGPT can create them; shops are an overlay over the game screen; a level lasts about 4 minutes |
| 01.11.2026 | Coastal-base level and new shield/coin capsules (PR #8) adopted; coastal level is the default |
| 01.11.2026 | Shop icons (PR #9) adopted for SHOT II–IV, MISSILE, SHIELD, BOMB; tags `stage1-stable`, `stage1-aircraft-stable`, `stage2-stable`, `stage3a-stable` set by the owner |
| 01.11.2026 | Stage 3b (shop) confirmed on hardware |
| 01.11.2026 | Space = bomb, S = invulnerability; extra life / exit icons and denser coastal level (PR #10) adopted |
| 01.11.2026 | Capsules fall at their own speed (1.5 px/frame), not with the landscape |
| 01.11.2026 | Stage 4 (special weapons) confirmed on hardware |
| 01.11.2026 | Missile in 8 flight directions (45° view from PR #11); revised coastal level (PR #11) |
| 01.11.2026 | Stage 4b confirmed on hardware; music composed by Claude instead of PR #12 (owner's choice) |
| 01.11.2026 | Stage 5 (music, effects) confirmed on hardware; the SID tuning (1 MHz) is right |
| 01.11.2026 | Aircraft views (PR #13); music volume 11 (effects 15); shop fire needs 8 frames release; S capsule 5 % |
| 01.11.2026 | Curved paths for helicopters, bombers, armoured planes; Stage 6 confirmed on hardware |
| 01.11.2026 | Game name "Shooter65" (repository keeps its name); PR #14 adopted: title, game-over banner, level-1 boss; boss and title music by Claude |
| 01.11.2026 | Stage 7 confirmed on hardware |
| 01.11.2026 | Stage 7b: boss parts flash when hit, wrecks vanish with the body, "PRESS FIRE" shadow kept inside the blinking row; boss harder (70 / 200 hit points, 1–2 px/frame plus bob, faster turret fire, core fires fans of three) |
| 02.11.2026 | Stage 7b confirmed on hardware |
| 02.11.2026 | Stage 7c: core fires aimed and random-angle shots; tanks avoid water; new level-1 waves (14 paths, 16 formations: loops, U-turns, side entries, pincers, V groups, hovering helicopters; tanks at varied places, `tools/design_waves_l1.py`); `L1BOSS` moved to attic RAM (no boss without attic RAM) |
| 02.11.2026 | Stage 7c confirmed on hardware; tag `stage7b-stable` set by the owner; ChatGPT asked for the Stage 8 ground-target artwork (`docs/chatgpt_ground_targets.md`) |
| 02.11.2026 | PR #15 (destroyed buildings and halls, light and heavy flak) merged; Stage 8: destroyable buildings and ground guns, music to `$AC00`, `LnDAT` ≤ 10 KB |
| 03.11.2026 | Stage 8 confirmed on hardware (no freeze) |
| 03.11.2026 | Stage 8b: shot level visible (1 / 2 / 3 bolts, bar), $ capsules 5 / 15 / 30, heavy flak 60 hit points; boss unchanged |
| 03.11.2026 | Stage 8b confirmed on hardware |
| 03.11.2026 | Stage 8c: boss core phase 1.5 px/frame (was 2), heavy flak 50 hit points; test cheat C = +5000 credits |
| 03.11.2026 | Stage 8c confirmed on hardware; balancing accepted by the owner |
| 03.11.2026 | PR #17 and #18 (level 2 tileset, map, ruins, land cruiser) merged; Stage 9: level 2 with level change, own waves, music "Desert Heat", key 2 on the title starts level 2 |
| 04.11.2026 | PR #20 merged; Stage 10: land cruiser turns through a diagonal view with dust |
| 04.11.2026 | Stage 10 rejected (the diagonal view looks smaller); PR #21 merged; Stage 11: hover tank with dust and flame thrower replaces the land cruiser, Stage 10 is not tested on hardware |
| 05.11.2026 | Stage 11 confirmed on hardware; Stage 12: longer flame jet that shoots down and sweeps towards the player |
| 06.11.2026 | Stage 12 confirmed; PR #22 (level 3) revised and merged; Stage 13: level 3 with enemy sets, ships, tile animation and carrier |
| 06.11.2026 | Stage 13 confirmed; Stage 13b: level 3 harder, more formations, ships glide in; art revision 2 ordered |
| 06.11.2026 | PR #23 merged (top-down wind turbines, new enemies, lying carrier 128×56); Stage 13c |
| 06.11.2026 | Stage 13c confirmed; colour cycling of the water (`cycle_frame`, header +26..29 from `animations.json` "cycle") built; brief `chatgpt_level3d.md`: wave band 9–12 in the water palette, tall wind turbines 32×64 on pylons |
| 06.11.2026 | PR #24 merged (wave band and colour cycling, tall wind turbines); ships placed anew; Stage 13d |
| 06.11.2026 | Stage 13d confirmed. Level 4 "Iron City" (final) planned: city, mechs (tank slots, walk only on the `streets` palette = bank 1), walker (armoured slots, like the frigate), jets/attack helicopters/drones (fighter/heli/bomber slots), mech boss (legs as `rotors`, flame arm, drones via the catapult); palette aliases streets/ruins/buildings in `build_level.py`; brief `chatgpt_level4.md`, checker `check_level4_art.py` |
| 06.11.2026 | PR #25 merged; Stage 14: level 4 (`ENEM4`, attic banks A/B/C, walker 30 hits one gun, mech boss legs step only while walking, music "Iron City"), checkpoint restart after a lost plane (start of level or after the mid shop, shot level −1), sprite frames as file `SPRITES` (PRG −3 KB) |
| 07.11.2026 | PR #26 merged (city and enemies redrawn); Stage 14b: level-4 jets are the level-1 fighters (enemy set copies their glyphs and table entries, palette bank 5 from level 1), heavy 32×32 drone drawn by Claude in the bomber slots (6 hits) |
| 07.11.2026 | Stage 14c: `level_retry` calls `boss_reset` and restores `lev_speed` (dying at the boss left the scrolling stopped); drone: steady eye, rotor glints instead of flickering sectors, banking without size change |
| 07.11.2026 | Stage 14d: walker redrawn by Claude (4 smooth walk phases + wreck); frigate/walker slots hold 4 phases, `tank_frame` uses phase & 3 for them |
| 07.11.2026 | Stage 14e: test cheat F (Shot IV, missile, 9 shields, full energy); drone banking stronger (lowered rotors 4.4 px radius pulled in, raised 6.9 px out) |
| 07.11.2026 | Stage 14f: the drone's hull rolls with the banking (narrower deck towards the lowered side, side wall on the raised side, deck lighting, hidden pod and shorter barrel on the lowered side) |
| 07.11.2026 | Stage 14g: all level-4 enemies except the jets and the final boss redrawn by Claude (`tools/pixel_vector.py`, scripts in the asset `source/` folders): attack helicopter, gunship (bomber slots, palette `gunship`), small four-legged mech, walker (24 hits), four-legged boss mech (feet as `rotors`, missiles via the catapult, flame); level 4 fires less, 16 guns |
| 07.11.2026 | Stage 14g confirmed for difficulty. Stage 14h: boss legs as 32×48 leg frames beside the hull, drawn before the body for legged bosses (`bd_rotors`, `bd_legs`); flame as a straight column |
| 08.11.2026 | Stage 17 confirmed (bomb colours, sphere). Stage 17b: level-3 sea variant C (owner chose it from a preview video: 64×32 swell block, 6-colour cycle over two index ranges, calm water at coasts and features); final boss: wreck field where the mech falls, sphere hidden in explosions, flame column instead of the fire-shot stream |
| 08.11.2026 | Stage 17b: final boss accepted ("sehr gut"); sea still looked like a blinking area on the big screen. Stage 17c: narrower crests, softer 5-colour cycle every 12 frames, whitecaps with two flash rhythms |
| 08.11.2026 | Stage 17c: music confirmed after the move, sea much better. Second sea preview; owner chose variant C (7.5 px) with the fine crest line of D: Stage 17d |
| 08.11.2026 | Stage 17d confirmed, tagged `stage17-stable` by the owner. Stage 18: enemies also fire upwards (half the rate); ground guns' upward shots fixed. Next: a look at the backgrounds of levels 1 and 2 (monotone) |
| 08.11.2026 | Previews for levels 1 and 2 accepted ("großartig"); owner chose option 1 (raise the row limit) and irregular forest outlines: Stage 18b, level format 3 (512 rows) |
| 10.11.2026 | Stage 18b: new level designs "sehr gut". Fixes (Stage 18c): tanks on tree tops, animated sea in a level-3 island, no sound effects after Game Over / the last level |
| 04.11.2026 | Owner: the turn still looks wrong (diagonal view had to be 85 % size). Decision: replace the land cruiser by a hover tank that glides in every direction, with flame thrower and dust effects (`docs/chatgpt_level2d.md`) |
| 04.11.2026 | Stage 9 confirmed on hardware; land cruiser turns look abrupt: intermediate diagonal view and dust requested from ChatGPT (`docs/chatgpt_level2c.md`) |
| 01.11.2026 | Shop: "ENTERING SHOP" 3 s (fire skips), 4×4 grid with thick outer and thin cell frames, 16×16 icon, name above, price below; blinking cursor only on cells that can be bought; "PURCHASE ITEM?" Y/N; unaffordable items dimmed; shot levels in order; items SHOT II–IV, MISSILE, SHIELD (10 s invulnerability), BOMB; HUD shows bombs and invulnerability counts |

## 15. Shop (Stage 3b, `shop.asm`, `tools/make_shop.py`)
- A `shop` event sets `shop_req`; the main loop calls `shop_run`, which **pauses** the game. All objects are
  removed (their pixies would draw over the panel), both screen buffers are rebuilt without them, the player
  sprites are switched off.
- The pictures replace **background tokens** of both screen buffers (opaque 16×8 NCM glyphs, no RRB cost).
  Leaving the shop rebuilds the frame from the ring buffer, which removes them again. Positions (screen rows /
  background tokens): "ENTERING SHOP" box rows 12–14, tokens 7–14; panel rows 3–24, tokens 2–19 (288×176 px,
  16 px landscape left and right); "PURCHASE ITEM?" dialog rows 10–15, tokens 6–15.
- Glyphs: file `SHOP` on the D81 (148 glyphs now), loaded at start to `$44000` (char `$1100`). Token maps,
  items, prices and palettes are generated into `build/gen/shop_*.inc`; **items and prices are defined only in
  `tools/make_shop.py` (`ITEMS`)**, because the prices are drawn into the glyphs.
- Palettes: while the shop is open, banks 13–15 (rocket and explosions; no objects exist) hold the shop palette
  in three versions: normal, dimmed (cannot be bought), highlight (cursor / selected button). The cursor frame
  blinks by changing one palette entry (bank 15, colour 4) every 8 frames. On leaving, banks 13–15 are restored
  from the game palette.
- Flow: "ENTERING SHOP" 3 s (fire skips) → 4×4 grid. The joystick moves the cursor only between cells that can be
  bought now and EXIT (nearest cell in the pressed direction, auto repeat), fire on an item opens
  "PURCHASE ITEM?" with YES / NO (left/right, **NO preselected**), fire confirms. Fire on EXIT resumes the game
  (1 s invulnerable). Only new fire presses count, so holding fire from the game does not skip anything.
- A cell can be bought if: credits ≥ price; shot level n needs level n−1 (bought ones stay dimmed); missile once;
  shield (invulnerability), bomb and extra life up to 9 each (one HUD digit).

| Cell | Item | Price | Effect now |
|---|---|---|---|
| 0–2 | SHOT II / III / IV | 100 / 200 / 400 | weapon level 2–4 = damage per shot |
| 3 | MISSILE | 250 | flag `has_missile` (homing missile: later stage) |
| 4 | SHIELD | 150 | `inv_count` + 1, HUD (activation, 10 s invulnerability with shimmering frame: later stage) |
| 5 | BOMB | 200 | `bomb_count` + 1, HUD (activation, destroys all enemies on screen: later stage) |
| 6 | EXTRA LIFE | 300 | one more life |
| 7–14 | – | | empty, kept for later items |
| 15 | EXIT | | leave the shop |

The HUD has a fourth box (48 px, x = 168) with a bomb icon + count and an invulnerability icon + count;
the credits box moved to x = 96. Bought items stay for the whole game; a new game (after the last life) resets them.

## 16. Special weapons (Stage 4, `special.asm`)
Keys (hardware keyboard queue, `system.asm`): **space = bomb**, **S = invulnerability** (decided 01.11.2026).
Requests while the plane is destroyed or inside the shop are dropped.
- **Bomb** (`bomb_count`): every enemy that is at least partly on the screen (y −24…199, formation members
  still waiting above the screen excluded) is destroyed through `kill_obj` with points and capsules, as if shot
  down. Enemy shots disappear. Flash: landscape banks 1–4 light for 4 frames, then `palette_init`.
- **Invulnerability** (`inv_count`): 500 frames (10 s) without damage (`player_vulnerable` = hit
  invulnerability or bought invulnerability; used by `player_damage` and `collide_player`). Cannot be started
  while running. Shown by a shimmering ring: hardware sprites 2–4 (16-colour, 48×24 ellipse outline behind the
  plane, glyph data `ring.bin` from `import_art.py` at `$5FC00`). The ring pixels use colour indices 1–6 by angle;
  `special_vblank` rotates six blue/white colours through sprite palette entries `$21–$26`, `$31–$36`, `$41–$46`
  every 4 frames. The ring blinks during the last 2 seconds.
- **Homing missile** (`has_missile`): object type `T_MISSILE` in the shot slots. It starts with the guns when
  no missile is under way and a visible enemy exists, and picks a random visible enemy (air or tank). Each frame
  it moves up to 3 px per axis towards the target centre; if the target is gone it picks another one, without
  any it flies straight up. After 200 frames it disappears. `collide_shots` treats it like a player shot, so it
  does `pl_power` damage to whatever enemy it touches. Graphic (Stage 4b): 8 frames in the flight direction,
  made at build time from the upward rocket and a 45° view by 90° rotations (no hardware flipping, see `docs/stage4.md`).

## 17. Aircraft views (Stage 6)
- Artwork PR #13: fighter and helicopter in 8 directions (N, NE … NW), bomber and armoured plane straight / left /
  right bank, 3 effect phases each (66 frames), plus repaired transparent holes in the hulls.
- `air_pose` (objects.asm) picks the view every frame from the path velocity (`obj_a`, `obj_b`): small aircraft
  with `vec_dir` (the missile's 45° sectors), large ones bank when |vx| ≥ 0.75 px/frame. The effect phase is kept;
  no movement keeps the view.
- Glyph budget: 535 of 608. To make room the pixie area starts at `$46800` (behind the 160 glyphs reserved for the
  shop) and frame bases are absolute character numbers. The glyph image left the PRG: file `PIXIES` (34 KB) is
  loaded straight into the pixie area. The PRG shrank from `$B460` to `$8460`.
- Column stacks must stay contiguous in memory (the hardware Y offset reads into the glyph above), so identical
  glyphs of different frames cannot be shared.

## 18. Boss (Stage 7, `boss.asm`)
- Level event `boss` (coastal level: row 358, before the end shop) sets `boss_req`. The boss arrives when no
  aircraft are left on screen (at most 5 s later; the rest are removed): scrolling stops, the boss music starts.
- Graphics (PR #14, quadrotor 96×64): file `L1BOSS` (149 glyphs + palette, 9,584 bytes), loaded at start into attic RAM
  (`$8020000`, Stage 7c; before: end of the level buffer). At start the fighter and bomber glyphs are also copied to
  attic RAM (`$8030000`). At the start of the fight a DMA copies the boss glyphs over the fighter and bomber glyphs (no fighters or bombers then), the boss palette replaces bank 5;
  afterwards both are swapped back and `palette_init` restores the bank. The frame table entries of the boss
  (`FR_BOSS_*`) point to the swapped place already. South-west turret views are mirrored south-east views.
- Body and the four rotors are drawn by `boss_draw` before all objects; the four turrets and the core are objects of
  type `T_BOSS` (air slots), so shots, the missile and the bomb (20 damage) work on them. Turrets (Stage 7b): 70 hit points,
  aim south / south-east / south-west at the player, red shots every 0.5–1.7 s (interval 24 + 8 per standing
  turret + 0–31 frames, so the last turrets fire faster), muzzle flash; 1,000 points each.
  When all four are destroyed the core opens (200 hit points, a fan of three fire shots left / down / right every
  0.7–1.3 s, faster movement); core destroyed: 5,000 points, 3 s of explosions, glyphs/palette back, scrolling and
  level music resume. Stage 7: 40 / 120 hit points, slower fire; the owner found the boss too easy.
- Stage 7c (owner: in the core phase the player could hide at the far left or right and win with missiles): the open
  core also fires a red shot every 0.4–1 s, half of them aimed exactly at the player (dx = Δx·32/Δy, up to
  4 px/frame sideways), the others at a random angle. Enemy shots now move sideways in 1/16 px per frame
  (`obj_a`, fraction in `obj_xf`); the fan is −1.25 / 0 / +1.25 px per frame.
- Hit feedback (Stage 7b): a part that is hit but survives is drawn for 4 frames (`FLASH_FRAMES_HIT`, `obj_a`) with
  palette bank 6, a copy of the boss palette lightened 65 % toward white (`boss_flash_pal`, made by
  `import_art.py`; bank 6 belongs to the bomber, which cannot appear during the fight).
- The boss moves sideways (x 24–200, 1 px/frame; core phase 1.5 px/frame since Stage 8c, before 2) and bobs up and down (y 20–44,
  0.5 px/frame); touching its body costs 16 shield. If the core opens while the boss is still flying in, it first
  descends to its fighting height.
- Halfway through the death explosions the body disappears, together with the turret wrecks (`boss_parts_away`,
  each with an explosion).

## 19. Title, game over, high score (Stage 7, `screens.asm`, `tools/make_screens.py`)
- Flow: start → title → game → last plane lost → game-over banner (fire after 1 s, or 5 s) → title → new game.
- Title (PR #14, 320×200, 399 glyphs incl. texts and 3 digit glyphs, file `TITLE` 26 KB) is shown as background
  tokens of screen buffer A, its glyphs at `$56000` (screen B and ring are free then). Its palette goes to bank 1,
  the background colour register to entry `$10`. "PRESS FIRE" blinks by swapping row 22 with a copy without text.
- Game-over banner (256×64 with "GAME OVER", "SCORE" and "PRESS FIRE" in the PR #14 font, 85 glyphs, file `GOVER`)
  is laid over the paused game like the shop, its glyphs at `$58000` (ring), palette in bank 13.
- Score digits are three reserved glyphs per screen, filled at run time from 8×8 digit cells (shop font).
- Both files are kept in attic RAM (`$8000000`, `$8010000`, all MEGA65 from R3 on) and copied in when needed.
  Without attic RAM (detected at start) the title is loaded straight to `$56000` and shown once; game over is then
  a small "GAME OVER" box in the shop style and a new game starts directly.
- High score: kept in memory while the program runs (not saved to disk yet).
- New game (`game_new`): all RRB rows, scroll, level events, objects, boss, shop items, HUD, player, level music.

## 20. Ground targets (Stage 8, `ground.asm`, artwork PR #15)
- **Buildings** are landscape tiles. `build_level.py` writes per tile whether it has a destroyed variant
  (`gt_dest`) and which target it belongs to (`gt_info`: kind, row and column inside a 2×2 group) into `LnDAT`
  (format 2, header offset 21), and the destroyed glyphs into `LnDEST` (48 tiles: 0–31 at `$5E000`, 32–47 in the
  last 32 pixie glyphs at `$4F800`). Landscape characters are now 16 bit per cell (`dr_hi`).
- Player shots fly **over** buildings (they still hit aircraft behind them) and damage each tile cell they cross
  once (cell remembered in the shot's `obj_cnt` / `obj_dly`). Hit points / points: hangar 16 / 500, depot 12 / 400
  (+ $ capsule), checkpoint 8 / 200, bunker 24 / 800 (+ large $), radar 12 / 600, fuel 10 / 500 (+ small $),
  crates 4 / 150 (+ S capsule); each hall tile 4 / 50 (halls are destroyed tile by tile). Damage of up to 8
  buildings is remembered.
- Destroyed cells in the ring are patched at once (both copies, screen and colour part); cells of rows not decoded
  yet go to an override list (48 entries, absolute metarow) that `level_row` applies. The next pass of the level
  shows everything intact again. The bomb destroys every building on the screen.
- **Guns** (`T_GUN`, ground slots): light flak 16×16 (6 hit points, 300 points) and heavy flak 32×32 (50, 1,000;
  Stage 8b: 60, Stage 8: 24). Both use the light gun's muzzle flash (Stage 8b).
  They move with the landscape, turn one 45° step every 8 frames towards the player and fire aimed red shots
  only when they point at him (light every 1.2–2.5 s, heavy two shots every 1–2.3 s), with a muzzle flash at the
  barrel tip. Shot, missile and bomb hit them; destroyed guns stay as wrecks. Level events `ground` with
  `enemy`: `flak` / `heavy_flak`.
- Memory: music moved to `$AC00` (5 KB) to give the program room; `LnDAT` is limited to 10 KB
  (`$50000–$527FF`), the heavy-gun glyphs (`PIXIES2`) follow at `$52800`.
- Test defines: `GOD_MODE` (no damage), `SKIP_SHOP` (shop events ignored), `BOSS_CORE_TEST`; `--test-credits`
  also gives 9 bombs.

## 21. Shot levels and economy (Stage 8b)
- One player shot object per volley (every `FIRE_RATE` = 6 frames), centred on the plane. Its view shows the shot
  level: one bolt (level 1), two (II), three (III), a bar 5×14 (IV; Stage 8b: 8×14) (frames `PSHOT1`–`PSHOT4`, built by
  `import_art.py` from the bolt of PR #4). The shot carries its damage in `obj_hp`: 2 × level, the same as the two
  shot objects of Stage 8 together, so the boss fight is unchanged. The missile does `level` damage as before.
- $ capsules are worth 5 / 15 / 30 credits (Stage 8: 10 / 25 / 50); the S capsule is unchanged. A player standing
  still collects about 65 credits until the mid shop and 210 in the whole level (XEMU).
- Test defines `SHOT2` / `SHOT3` / `SHOT4`: start with that shot level.
- Test cheat (Stage 8c, owner's request, in every build): key **C** during the flight adds 5,000 credits (at most
  9,999), so every shop item can be tried.

## 22. Several levels (Stage 9, `levels.asm`)
- Level 2 "Canyon und Raffinerie" (artwork PR #17/#18): desert, canyon with river and bridges, oasis, refinery;
  land cruiser boss. Waves: `tools/design_waves_l2.py` (paths and formations of level 1, new order, denser).
- With attic RAM all level files are loaded at start into a 64 KB pack per level (`$8040000 + n·$10000`: GFX, DAT,
  DEST, music piece); bosses at `$8020000 + n·$40000`. `level_enter` copies a level into place by DMA (landscape
  glyphs and palettes, destroyed tiles, `LnDAT`, music piece into the slot, boss source, palette and part
  positions). Without attic RAM only level 1 exists (loaded as before, repeats).
- The event `end` starts the next level (after the last: level 1). Score, lives, credits, shot level, missile,
  bombs and shields are kept; scroll, objects, buildings and the boss start fresh.
- Both bosses share one frame layout (`import_art.py` pads smaller frames to the level-1 sizes); part positions
  per level come from `placement.json` (`boss_place1/2`).
- Music: the level piece (`MUS_LEVEL1`) lives in a slot behind the shared pieces; level 2 "Desert Heat"
  (E Phrygian dominant). The level-clear fanfare queues "the level music", so the new piece follows it.
- Palms next to water: `tools/decorate_level2.py` (run after every new level-2 map; fills the 256-row limit).
- Boss area (Stage 9b, PR #19): 324 glyphs over the fighter, bomber, helicopter and armoured-plane frames (no
  aircraft during the fight); both bosses 229 glyphs incl. a second view (`BOSS_BODY_SIDE`, `BOSS_CORE_SIDE`,
  `BOSS_RSIDE0-2`; empty for the quadrotor). `boss_orient` switches frames, part positions (44 bytes per level:
  normal + side), body box and x limit.
- Land cruiser (`cruiser_fight`): drives y to 20 / 56, stops and turns (centre kept), drives x to the player's
  position (40..216), stops, turns back. Stage 10 (PR #20): a turn takes 36 frames: 12 in the old view, then 24 in
  the diagonal view (`BOSS_BODY_DIAG`, 96×96, front down-left) with dust clouds (`BOSS_DUST0/1`) at the track ends
  and a rumble, then the new view. Boss area 323 of 324 glyphs; part positions 66 bytes per level (3 views). The quadrotor of level 1 keeps flying sideways with the bob.
- **Stage 11 (PR #21): the hover tank replaces the land cruiser** (no turns any more, so no shrinking view).
  `hover_fight` glides one pixel per frame on both axes (1.5 in the core phase) to a target point: x near the
  player (± 32 px, limited to 24..`fx_xmax`), y 16..47; on arrival a new target. While it moves, dust (`BOSS_SPRAY0-2`,
  32×16) is drawn at the skirt positions. In the core phase the flame thrower runs a cycle: idle 1.6–3.6 s, warning
  30 frames (small flame `BOSS_FLAME0` flickers, harmless, the tank stops), jet 50 frames (`BOSS_FLAME1/2`, damage 12
  when the player's centre is in the 16×32 box), fading 12 frames. Rotors: `fx_rotn` of them (quadrotor 4, hover
  tank 2 fans).
- Stage 12: the jet grows by one 24-px segment every 4 frames to 5 segments (about 128 px; damage length
  segments·24 + 8), lasts 80 frames, the tank sweeps towards the player at 0.5 px/frame while it burns (`hv_aimx`),
  and the jet shrinks back from the tip in 15 frames.
- Per-level boss tables from `import_art.py`: `boss_place1/2` (22 bytes: part and rotor positions) and `boss_fx1/2`
  (16 bytes: flame position, 4 signed dust positions, dust count, rotor count, body box width − 8 / height − 4,
  x limit, flame flag). `level_enter` copies them to `part_dx` and `boss_fx_cur`. Both bosses 205 of 324 glyphs.
  The orientation code (`boss_orient`, `cruiser_fight`, the side and diagonal frames) is gone.
- Title: key **2** starts directly in level 2 (test aid, also in release builds). Test define `START_LEVEL2`,
  `build.py --level2 FILE` builds another JSON as level 2.

## 22a. Level 3 "Operation Offshore" (Stage 13, PR #22)
- Sea level by ChatGPT: open sea with islands, oil field, research platforms with wind farm, naval base; 126 tiles,
  35 ruined tiles, 4 tile animations. Waves: `tools/design_waves_l3.py` (only fighter and helicopter formations,
  ships as ground events on open water, guns on islands and platforms).
- **Attic layout per level** (tables in `levels.asm`): pack banks 4, 5, 7; boss banks 2, 6, 8; enemy-set banks 3, 3, 9.
  Key 3 on the title starts level 3 (test aid, like key 2); `--define START_LEVEL3`, `build.py --level3`.
- **Per-level enemy set** (`import_art.py enemy_sets`, files `ENEM0` for levels 1/2 and `ENEM3`): the aircraft area
  (324 glyphs, frames 0–65), the tank area (49 glyphs, `FR_TANK_N0`+0–15), the palettes of banks 5–8 (into
  `palette_data`) and these frames' table entries. `set_in` copies it with one DMA job per part (23 parts) at
  `level_enter` and after the boss (replaces the Stage 7c `PXSAVE` copy). Level 3: seaplane in the fighter slots,
  patrol boat (4 directions × 2) in the bomber slots, navy helicopter in the helicopter slots, frigate (2 phases +
  wreck) in the armoured-plane slots, speedboat in the tank slots. Bomber and armoured formations must not be used
  in level 3.
- **Ships** are `T_TANK` objects: speedboat = `K_TANK` (in level 3 `tank_boat` = 1: land ahead blocks, off-screen is
  open water, it moves every frame), patrol boat = `K_BOMBER` (32×32, every 2nd frame, 16 hits, one light gun),
  frigate = `K_ARMOURED` (south only, every 4th frame, 40 hits, two light guns). Guns on ships are `T_GUN` objects
  in a slot after the ship's (drawn on top) with the ship's slot + 1 in `obj_mir` and their offset in
  `obj_pcl/obj_pch`; they ride with the ship and vanish with it. The frigate wreck frame is not used yet.
- **Carrier boss** uses the hover code (`hover_fight`): no flame, half glide speed, y 16–31, wake (`spray`) while it
  moves, 1 radar (`rotors`). Every 2–5 s a deck jet: 24 frames on the catapult (`BOSS_JET0/1`), then it flies at
  the player as a fire shot with frame `BOSS_JET2` (cannot be shot down). `boss_fx` has 19 bytes (catapult x, y,
  flag added).
- **Tile animation** (`anim.asm`): `animations.json` → table in `LnDAT` (header word +24); every `period` frames the
  phase's tile glyphs are copied by DMA from the level pack (untouched `LnGFX`) over the phase-0 tiles. ≤ 8
  animations, ≤ 24 animated map tiles; animated tiles are not destroyable.
- Music "Open Waters" (A Dorian, `MUS3`); `build.py --music-level N` makes a listening disk.
- Stage 13b: ships spawn above the top edge by their height (`gr_y`); `kind_hp`/`kind_fire` are set per level
  by `level_enter` (`lv_kind_hp`, `lv_kind_fire`); level 3 has six own paths/formations (`design_waves_l3.py`
  PATHS3/FORMATIONS3) and denser waves. Art revision 2 ordered (`docs/chatgpt_level3c.md`): top-down wind
  turbines, slimmer and more colourful enemies (fourth palette `frigate` in bank 8), lying carrier ≤ 128×64.
- Bank-0 space: BASIC's palette 0 and zero page are saved in chip RAM (`$5DB00`, `$5DE00`) instead of bank 0.

## 22b. Level transition, diagonal shots, art review (Stage 15)
- **Transition** (`transition.asm`, pictures from `tools/make_overlays.py`): when the boss is gone the victory
  fanfare (`MUS_LEVEL_CLEAR`) plays and `level_clear_req` counts down 60 frames (the plane is invulnerable meanwhile);
  then the main loop calls `level_transition`, which pauses the game: LEVEL CLEAR! with a burnt picture of the
  boss (composed from the boss artwork: body, legs/rotors, destroyed turrets, open core; darkened, scorched, on fire)
  and a blinking PRESS FIRE TO CONTINUE → fire → the end shop (as before, after the boss) → fade to black →
  `level_next` behind the black screen → PREPARE FOR LEVEL n → fire → fade in, level music. The end-shop and
  `end` events of the level are no longer reached (the transition replaces the level); without attic RAM there is no
  boss, so the old end of level remains. A plane lost during the 60 frames cancels the transition (the level is
  retried). Test define `TRANS_TEST`: transition 5 s into the game.
- **Pictures** are drawn like the shop pictures: opaque 14-column rectangles of shop-palette glyphs, copied from
  attic bank `$0D` over the shop glyphs, maps into `ov_map`, drawn by `blit_msg` (pictures 3 and 4); bank 15 is a copy
  of bank 13 in which colours 4 and 8 (text, shadow of the blinking line, attribute 18) switch every 16 frames.
  The shop glyphs come back from attic bank `$0E`.
- **Fading through palette 2**: the screen shows palette 2 during the fades and the PREPARE picture. `fade_set` writes
  palette 2 = palette-0 snapshot × k/16 (k = 0–16, register nibbles swapped: a 256-byte table per step), 2 frames per
  step. Palette 0 is never darkened, so the next level's `palette_init` can run while the screen is black. Every
  `$D070` write in the game ORs in `pal_show` so it cannot switch back to palette 0 too early.
- **Diagonal enemy shots**: red bolts and fireballs flying with |dx| ≥ 7/16 of their fall speed (about 24° and more)
  show a 45° view (down-left / down-right; the bolt sheared, the fireball rotated). Frames in a third pixie area
  (`PIXIES3`, `$55200`, behind screen buffer A); `eshot_view` in `upd_eshot`. Rockets and the carrier's deck jets keep
  their frames.
- **Art review**: the level-2 and level-3 ground targets (`assets/art/level2|3/source/claude_targets.py`, patching
  the generated tile sets) and the level-3 enemies (`assets/art/enemies-level3/source/claude_l3_enemies.py`) are
  redrawn in the convention of the level-4 buildings and Claude's level-4 enemies.

## 22c. High scores, title cycle, end of the mission, second missile (Stage 16)
- **High-score list** (`hiscore.asm`): 10 entries, name 10 characters (A–Z, 0–9, space . - !), 6-digit BCD score,
  level reached (1–4, 5 = mission accomplished). File `SH65HI.DAT` (SEQ, 176 bytes, magic `SH65HI`, CRC-16/CCITT).
  Read at start while the KERNAL still owns the machine (`hi_boot`); without a file the default list (invented
  pilots VIPER … NOVA). Saving uses **Vyper's disk transaction unchanged** (Stage 10a6, confirmed on hardware;
  `hiscore_disk.asm`): write `SH65HI.TMP`, read back and verify, check the old `DAT` against the list read at start,
  scratch `BAK`, rename `DAT`→`BAK`, `TMP`→`DAT`, verify again. A damaged file is never written over (`hi_blocked`);
  the list then stays in memory for the session only.
- **KERNAL session** for the save (`kernal_enter`/`kernal_leave`, like Vyper's `hi_suspend`/`hi_resume`): sound off,
  palette 0 black, VIC registers and CIA direction as BASIC had them (`vic_to_basic`, shared with the exit), the
  game's zero page to `SAVED_GZP` and BASIC's back, `CLI`; afterwards everything back and `video_init`/`palette_init`.
  The screen is black for one or two seconds.
- **Text pages** (`textpage.asm`): the engine only knows 16-px tokens, so text is drawn pixel by pixel with a 6-px
  font (the shop's 5×7 letters) into a 16×15 glyph block in the landscape glyph area; the logo rows of the title
  stay above it. Pages: Hall of Fame (the title shows the picture for 10 s, then the list for 10 s, and so on; fire
  or keys 2–4 start at any time), name entry (keyboard, or joystick up/down = letter, left/right = position, fire =
  OK; an empty name becomes PILOT), MISSION ACCOMPLISHED (after the level-4 boss: LEVEL CLEAR, fade out, the page with
  the final score fades in; no end shop), then the name entry if the score enters the list.
- **Menu overlay** (`menu.asm`): the 5 KB of menu code would not fit in bank 0 below the music (`$AC00`). It is
  assembled for `swap_start` into the file `HIMENU`, loaded to attic RAM and swapped by DMA over `boss.asm` +
  `ground.asm` while no game runs (both directions, so the list and the game code's state are kept).
- **BASIC's screen** `$0800–$0FFF` is saved at start and restored at the exit, so the game may use it as work RAM
  (transition buffers, font, backup copy of the list). Stage 15 had put the transition buffers there without this
  save; corrected here.
- **Second missile**: shop cell 7, $400, two-missile icon, after the first missile; then two homing missiles can be
  in flight, alternately from the wings. Its label is "MISSILE" like the first: "MISSILE II" would need 6 more
  shop glyphs than the 160 reserved.
- Bank 0 freed: the ring sprites come with the file `SPRITES`; PRG ends at `$A333` (Stage 15: `$A939`).

## 22d. Level-4 boss, third phase (Stage 17)
- Owner: the final boss is too easy with full equipment. When the mech's core falls, its death explosions run as
  before, then (`ball_next`) an armoured sphere rolls out of the wreck (`ball.asm`, artwork
  `assets/art/boss-level4/source/claude_ball.py`). Its glyphs (file `L4BALL`, attic `$8100000`) replace the mech's
  in the boss area, its palette and lightened hit-flash palette go to banks 5/6 (`boss_palette` knows `ball_on`).
- The sphere (48×48, `boss_x/boss_y`, drawn by `boss_draw`) rolls in the upper half (y 16–92), bounces, picks a new
  direction every 1–2 s and fires fans of five red shots. After 3–4 s it stops: hatch opens (24 frames), core pulses
  with warning beeps (50), stream of fire shots every 2nd frame for 36 frames, all with the direction aimed at the
  player when the stream starts; then open for 110 frames: only now the core (`T_BOSS`, `obj_kind` 5, 180 hp,
  `BOSS_TEST`: 8) can be hit, also by bombs; hatch closes (24), rolls again. The core's last hit point → `BS_DIE`
  with the sphere, then LEVEL CLEAR as before. A lost plane restarts at the checkpoint with the mech again.
- Bomb flash fix: `palette_init` after the flash also overwrote banks 5/6 during a boss fight (boss partly red).

## 22e. Wreck field, hidden appearance, flame column; the new sea (Stage 17b)
- Owner: the mech vanished without a trace, the sphere came out of nothing, its fire stream looked worse than the
  flame of the earlier bosses. Now, halfway through the mech's death explosions (`BOSS_DIE/2`): four big
  explosions cover the body and the mech is no longer drawn (`ball_cover`); three frames later, when no RRB display
  list shows it any more (double buffering: swapping at once flashed sphere glyphs for a frame in XEMU), `L4BALL`
  is copied into the boss area (`ball_wreck_in`) and the **wreck** (`FR_BALL_WRECK`, 128×80: the mech's legs, body
  and destroyed turrets, burnt, torn, blown-out core crater, small fires, debris around it) lies where the mech
  fell (`wk_x/wk_y`) until the level is clear. It smoulders: a small explosion on it every 0.5–1 s.
- At the end of the explosions four big explosions fill the crater and the sphere is in it (`ball_start`); it rolls
  down out of the wreck (`BL_EMERGE`, 44 frames), then rolls as before.
- Flame column: instead of the stream of fire shots the sphere rolls over the player (`BL_AIM`, also to y 56,
  at most 3 s), opens, warns (small flickering flame in the hatch) and fires the hover bosses' flame thrower straight
  down: `hv_burn` (grow, sweep after the player at 0.5 px/frame, damage) and `hv_draw`, with `fx_flx/fx_fly` set to
  the hatch (16, 26), `fx_xmax` 240, no dust, no deck jets. The jet's damage test moved from `hv_flame` into the
  subroutine `hv_burn` (unchanged for the hover tank and the carrier).
- `L4BALL` is an image of the whole boss room (298 of 324 glyphs): the mech's flame frames stay at the glyph places
  of `FR_BOSS_FLAME0-2` (colours mapped to the sphere palette), the sphere and wreck frames fill the gaps
  (`tools/import_art.py`). The room beyond the mech's 237 glyphs holds aircraft glyphs, which `set_in` brings back.
- Level 3, sea (`assets/art/level3/source/claude_sea.py`, owner chose variant C of a preview video): the open sea is
  one 64×32 px swell block (8 tiles, map cell → block tile by column % 4 and row % 2); moving pixels carry the
  6 colours 9, 10, 11, 12, 1, 2 of a wave profile, so the crests travel when `cycle_frame` rotates them. The
  colour list now has a second range (level header +30/+31 `first2/count2`, `animations.json` "cycle"). The swell
  only joins itself, so coast transitions and features (oil, wakes, buoy, pipe, turbines) get calm water with swell
  pixels dithered in towards their border; coasts get a smoothed coastline with a 1-px rim. A first attempt that
  gave them the swell of their most frequent block position showed seams; a 16-px swell (joins everywhere)
  looked like stripes. Tile budget: 124 of 126; unused now `free_blue`, `shelf1`, `edge6`, `edge9`, `edge15`,
  `island6`, `island9`.

## 22f. Sea: narrower crests, slower, whitecaps (Stage 17c)
- Owner: on the screen the wide colour bands and the fast cycling looked like a blinking area. Now the crests are
  about 11 px apart (phase `4u + 2v`, was `2u + v`), the cycle has 5 softer colours (9, 10, 11, 1, 2: crest, crest
  edge, base, shadow, base) and steps every 12 frames (was 6 colours every 9). Calm patches are one colour (4).
- Whitecaps: the freed palette indices 12 and 3 are cap registers. `cycle_frame` gives them the colour of their list
  place every frame (place 0, where index 9 starts with the crest colour), so their pixels are invisible on the
  crest pixels; when the crest colour reaches that place for the n-th time (12: every 2nd, 3: every 3rd pass) the
  register flashes white and fades for 24 frames. Their flecks (4-6 crest pixels) are only in 8 extra tiles
  `cap_bXY` (same swell as `sea_bXY`; the 7 unused tiles and one new tile, 125 tiles now). They replace about 10 %
  of the open-sea cells. The level format allows 256 different rows, so every different row has a few fixed
  variants (the frequent pure-sea rows 8, within the budget: 249 rows) and each map row takes one at random.
- Level header 40 bytes (was 32): +32 cap count, +33.. index / list place / every per cap (`animations.json`
  "cycle" "caps", checked by `build_level.py`). `cycle_reset` (in `video.asm`, called by `palette_init`) starts
  the crest at place 0 again whenever the level colours are reloaded (level start, after a bomb flash).
- Program room: `anim.asm` moved into the overlay area (it runs only in the game), `ATTIC_LEVELS` to `layout.asm`,
  the music data from `$AC00` to `$AE00` (4,519 of 4,608 bytes).

## 22g. Sea: finer still (Stage 17d)
- Owner: much better, the colour zones could be narrower still; a second preview video showed four variants (A as
  17c, B 8 px, C 7.5 px at 45°, D = B with a fine crest line). Owner's choice: C with the fine line of D. Now the
  phase is `6u + 3v` (crests about 7.5 px apart, zones about 1.5 px) and the 5 cycle colours are crest, crest edge,
  base, base, shadow: a bright line with a shadow behind it on almost even water. Narrower would break the zones
  into single pixels. Whitecaps, period and everything else as in Stage 17c.

## 22h. Enemies also fire upwards (Stage 18)
- Owner: almost all enemies fire only downwards, so the player is safe above the middle of the screen. Now
  `enemy_fire` (planes and tanks via `maybe_fire`, scripted `OP_FIRE`): if the player's centre is more than 8 px
  above the enemy's centre (`pl_above`), the shot flies up - at half the rate (a random bit) and always as a red
  bolt (fireballs and rockets have a direction in their pictures). Otherwise everything as before.
- Upward shots have a negative speed in `obj_b` (`es_up` before `spawn_eshot_a`); `upd_eshot` moves them up and
  removes them 32 px above the screen; `eshot_view` mirrors the slanted bolt views.
- Ground guns turned towards a player above them but their shots still flew down (a bug): now they fire up, aimed
  (`aim_shot` handles upward shots), also at half the rate. Bosses unchanged.

## 22i. Levels 1 and 2: big seamless patterns, irregular forests (Stage 18b)
- Owner: levels 1 and 2 looked monotone (one grass tile, six forest tiles with trees at the same places, regular
  rows of rock tiles). After a preview (single sections, then both complete levels) the owner chose the proposal:
  big seamless patterns instead of single repeated tiles, irregular forest outlines, and - because the patterns
  multiply the number of different map rows (a row exists once per position in the pattern) - a larger row limit.
- Level format 3: the map's row list holds 16-bit indices into the row dictionary, so a level may have 512
  different rows (was 256; `level_row` in `level.asm`, `MAX_ROWS` in `build_level.py`). Cost: 2 instead of 1 byte
  per map row and 21 bytes per extra different row. `LnDAT` stays at most 10 KB: L1DAT 9,632, L2DAT 9,760 bytes.
  Levels 3 and 4 unchanged (only +375 bytes each); level 1 in XEMU pixel-identical before the art change.
- Level 1 (`assets/art/coastal-base/source/claude_terrain.py`): meadow 64x32 (8 tiles), forest canopy 64x32
  (overlapping crowns, 8 tiles) inside the forest, forest edge (whole crowns on the meadow of the same block
  position, 8 tiles), still sea 32x16 (2 tiles). Room: the 15 pixel-identical road/bridge tile pairs merged, the
  old grass/forest/sea tiles, `rocks` and the dotted `meadow` patch: 26 tiles for 26. Forest outlines redrawn
  within 3 cells of the old outline from the signed distance plus smooth noise (only meadow/forest cells; forest
  area 2,791 -> 2,718 cells); 316 different rows. The map is written without `repeat` blocks.
- Level 2 (`assets/art/level2/source/claude_desert.py`): dunes 64x64 (16 tiles; ripples, flat irregular crests
  with lee shadow), three rock formations (2x2, 3x2, 3x1 tiles) that each sit only on one dune block position
  (their tiles carry that dune background, so the dunes run on seamlessly) - 42 formations at random among the
  anchor positions, boss yard as concrete plates 64x16 (4 tiles, palette structures). Room: 20 unused tiles, the 12
  sand/scree/salt/boulder tiles and `yard`: 33 for 33; 316 different rows. `tools/decorate_level2.py` (palms, from
  the ChatGPT phase) expects the old sand tiles and must not be run again.
- Sea in level 1 stays still: an animation like level 3's would need free palette colours, and the water palette
  of level 1 is full.

## 22j. Fixes after Stage 18b (Stage 18c)
- Owner: in level 1 a tank drove over the tree tops. Tanks only knew water (`land_store`: palette bank 1 is
  water). Now tiles from the level header's +39 on (0 = none) count as not land too; `build_level.py` writes the
  first id of the tiles marked `"blocks_tanks"` in level-example.json (they must be the last ids). Level 1: the 16
  forest tiles (canopy, wood) are ids 110-125 (`claude_terrain.py` renumbers them), and every tank starts in a 5x5
  cell clearing (forest 2,718 -> 2,488 cells, 314 rows). Tanks turn in front of forest as in front of water.
- Owner: in level 3 animated open sea showed in an island (rows 247/248, columns 14/15: a 2x2 of former deep
  water inside the reef ring, now the cycling swell). Replaced by the shallow tiles shelf2/shelf3/shelf0.
- Owner: after Game Over and after the last level the sound effects were silent in the next game, the music played.
  Cause: the highscore disk session (`kernal_enter`) calls `sound_off`, which also clears the volume of the effects
  SIDs; music sets its volume with every piece, the effects only once at program start (`sound_init`). Now
  `kernal_leave` calls `sfx_volume` (Stage 16 bug, since the highscore table).

## 23. Open questions for the owner
1. Should the scroll speed change per level or section, for example a faster section before the boss?
3. How many levels, with which themes (for example countryside, desert, coast/sea, city, fortress)?
4. Should the high score be saved on the disk (with initials)?
5. Are the damage values and points in §6 a good starting point?

## Coastal-base level ("Operation Küstenwald", PR #8)

`levels/coastal_base.json` is a coastal → forest → military road/bridge → base scenario.
**Since Stage 3b it is the default level L1**; `tools/build.py --level levels/level01.json` still builds the
old test level. Native transition tiles and the four
palette budget are documented in `docs/COASTAL_BASE_LEVEL.md`. Bonus graphics now
show a medieval shield and three gold coin sizes, retaining their IDs and bank 12.
Level/data checks and assembly passed; no new emulator or hardware acceptance is
claimed for this candidate.

## Shop icons and denser coastal-base revision

Extra-Life and Exit now load from `assets/art/shop/generated/indexed-source.json`
through the existing HUD-to-shop colour map. Prices, item codes, palette roles and
runtime logic are unchanged. Extra-Life derives from the actual player sprite;
Exit uses a green running-person/door/arrow motif.

The coastal-base source now schedules 44 formations (240 aircraft) and 16 tanks,
with 7–8 rows between waves and quiet shop approaches. New scenery includes
islands, woodland ponds, rocks, supply areas, radar and a runway. All fixed
structures remain decoration. See `docs/COASTAL_BASE_LEVEL.md` for budgets and
validation; the denser schedule still requires a full gameplay/hardware pass.

## Natural terrain and large base complexes

The next coastal-base artwork pass uses a smooth multi-frequency coastline,
compact islands, nine broad clearings and less noisy grass. Ten building wings
use reusable steel/brick roof modules, including an L-shaped workshop and halls
up to 128 pixels wide. Used tiles are pruned and locally renumbered; import the
tileset and level together. The denser wave schedule and runtime logic are unchanged.
The actual 16KB GFX budget allows 126 tiles including the header/palettes.

`assets/art/rocket-directions/` supplies original and clockwise-45-degree static
views of the game projectile with exactly the existing rocket palette. These
are optional standalone assets, not animation frames or a new homing mechanic.

## Enemy opacity fixes and additional poses

Explicit indexed hull repairs fill 1/10/21 previously transparent pixels per
fighter/bomber/armoured phase. Existing opaque pixels, palettes, player, helicopter
and tanks stay unchanged. Canonical three-phase animation remains the runtime path.
`assets/art/enemy-views/` additionally supplies eight fighter/helicopter headings
and straight/left/right bank poses for large aircraft, each with three effect phases.
These views are standalone assets: full replacement would require 535 of the
available 512 glyphs, so direction selection and packing optimisation remain future work.
The large bonus coin is reduced from 26 to 18 visible pixels, giving 10/14/18 sizes.
See `docs/ENEMY_VIEWS_AND_OPACITY.md` for source provenance, packing and validation.

## Title / game-over artwork and Level-1 boss art

`assets/art/screens/` provides a 320x200 Shooter65 title with a clear 320x24
engine-text band, a spec-sized 256x64 game-over decoration banner and the requested
320x200 full-screen game-over alternative. Native screen files are indexed,
16-colour assets with one local palette, deduplicated NCM tiles and maps.
The city scenes are generated source art; prompts and deterministic conversion
are archived. Runtime overlay texts remain separate from banner decoration.

`assets/art/boss-level1/` provides a 96x64 native quadrotor body, four distinct
independently destructible turret instances (south/SE/destroyed), visual-only
rotor animation and an exposed-core overlay. Artwork metadata specifies body
invulnerability until all four turrets are destroyed, then a final body phase;
HP, movement and implementation are left to the game. All graphics use one
15-colour palette plus transparency, 137 guarded glyphs / 8768 bytes. No screen
or boss gameplay integration is claimed. See `docs/SCREENS_AND_LEVEL1_BOSS.md`.
