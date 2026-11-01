# Stage 3a – Level files, flight paths, capsule and weapon rules

Branch `stage3`, based on `stage2-stable`. Release files are in `releases/stage3a/`.

## What is new
- **Levels from disk**: `SHOOTER` loads `L1GFX` and `L1DAT` from the same drive (SEQ files) before the game
  starts. If a file is missing, a message is printed and the program returns to BASIC.
- **Level description as JSON** (`levels/level01.json`, format: `docs/level_json.md`). The test level is
  4 minutes long. It reuses the artwork-v2 example landscape and has 7 flight paths, 7 formations, 77 events,
  two shop markers and an end marker, after which the level starts again.
- **Flight paths**: snake lines, dives that aim at the player, swoops, zigzags, hovering helicopters, and bombers
  that fire at intervals. Formations fly one path with a delay between members; some come mirrored from the
  other side.
- **Capsules**: an S capsule refills 20 % of the shield and appears at random (15 %) when an enemy is shot down. $ capsules
  come from every tank and from the last plane of a completed formation.
- **Weapon damage vs. enemy hit points**: fighter 1, helicopter 2, tank 3, bomber 6, armoured plane 10 hits at
  weapon level 1. Upgrades come with the shops (Stage 3b).

## Build and start
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
The D81 contains `SHOOTER`, `L1GFX` and `L1DAT`. `LOAD "SHOOTER",8` then `RUN`.

## Verification so far
| Check | Result |
|---|---|
| `build_level.py`: 384 rows, 15 different rows, 35 metatiles; `L1GFX` 8132 bytes, `L1DAT` 1929 bytes; preview picture | ✔ |
| Assembly, D81 with three files read back | ✔ |
| XEMU: files loaded from drive 8, landscape from the level file, formations fly their paths, tanks from events, capsules, RRB overflow 0 | ✔ |
| XEMU: 16,000 frames (5 min 20 s), across the level end and into the second pass | ✔ |
| Real MEGA65 (first build) | runs without errors, but froze after about 4 minutes, see below |
| Real MEGA65 (fixed build) | ✔ confirmed by the owner (01.11.2026): the level can be played repeatedly |

## Fixed: freeze at the level end
The first Stage 3a build froze when the level end was reached (map row 384, about 4 minutes). The `end` event
moves the event list back to its start, but the event loop kept comparing against the old position, so it ran
every event of the level at once, including the `end` event again, endlessly. The loop now stops after the
`end` event and continues with the new position in the next frame. Reproduced and verified in XEMU (frame counter
stopped at 11,888 before the fix; runs past 16,000 frames after it).

## Hardware test checklist
1. Start from the D81: the game starts after a short load. Without the D81 (or with a missing `L1DAT`),
   a "CANNOT LOAD" message appears and BASIC is still usable.
2. The landscape looks as in Stage 2; after about 4 minutes the level starts again without a visible jump and
   **without freezing** (play for at least 5 minutes).
3. Formations: snakes, dives towards the player, swoops from the left and the right (mirrored), zigzag helicopters,
   hovering helicopters, bombers with bursts of fire. Movement is smooth (no jerks).
4. Tanks appear on the ground in different directions.
5. Fighters die with one hit, bombers and armoured planes need many. Capsules appear as described.
6. Exit with X and `RUN` again (the level is loaded again) work.

---

# Stage 3b – Shop overlay, coastal-base level

Release files are in `releases/stage3b/`. Design details: `docs/design.md` §15.

## What is new
- **Coastal-base level** "Operation Küstenwald" (ChatGPT, PR #8) is now the default level: coast → forest →
  military road with bridge → base, 375 rows, shops at rows 188 and 368. New shield and coin capsules (PR #8).
- **Shop**: at a shop event the game pauses and "ENTERING SHOP" appears for 3 seconds (fire skips it).
  Then a 4×4 grid with a thick outer frame and thin cell frames. Each cell shows the name, a 16×16 icon
  (placeholders) and the price. A blinking frame marks the selected cell; the joystick moves it only between
  cells that can be bought now and EXIT. Fire opens "PURCHASE ITEM?" with YES / NO (left/right, NO is
  preselected), fire confirms. Items that cannot be bought (too expensive, previous shot level missing, already
  owned, maximum reached) are shown darker. EXIT (bottom right) continues the game.
- Items and prices: SHOT II 100, SHOT III 200, SHOT IV 400, MISSILE 250, SHIELD 150, BOMB 200, EXTRA LIFE 300.
  Weapon levels raise the damage per shot (1 → 4) right away. Missile, shield (invulnerability) and bomb are
  only stored and counted for now; using them comes in a later stage.
- **HUD**: new box with a bomb icon + count and an invulnerability icon + count; the credits box moved left.
- Disk: new file `SHOP` (shop graphics).
- Test build with 999 credits at the start: `python3 tools/build.py --test-credits` (not for releases).

## Verification so far
| Check | Result |
|---|---|
| Assembly, D81 with `SHOOTER`, `SHOP`, `L1GFX`, `L1DAT` read back | ✔ |
| XEMU, test level with a shop at row 20 and 999 credits: message, skip with fire, grid, dimming, cursor moves, YES/NO dialog, buying all items, HUD counters, credits, EXIT back into the game | ✔ |
| XEMU, release build: the mid-level shop of the coastal level opens after about 2 minutes (no credits: everything dimmed, cursor on EXIT) | ✔ |
| **Real MEGA65** | **open – please test** |

## Hardware test checklist
1. Start from the D81. The coastal level appears (water on the left, then forest).
2. After about 2 minutes "ENTERING SHOP" appears in the middle for 3 seconds; the game stands still, enemies
   disappear. Pressing fire skips the message (holding fire from the game must not skip it).
3. The grid: thick outer frame, thin frames, names, icons, prices. Too expensive items are darker. The selected
   cell has a blinking frame; the joystick moves it only to bright cells and EXIT.
4. Fire on an item: "PURCHASE ITEM?" YES / NO; left/right changes the blinking button; NO closes the dialog
   without buying; YES buys: credits go down in the HUD, the item turns dark if it can no longer be bought.
5. SHOT III can only be bought after SHOT II, SHOT IV only after SHOT III. After buying, bombers and armoured
   planes need fewer hits.
6. SHIELD and BOMB raise the counters in the new HUD box, EXTRA LIFE the lives counter.
7. EXIT: the game continues where it stopped, the plane blinks for a moment. The end shop (shortly before the
   level end) works the same; afterwards the level starts again.
8. No flicker or broken tokens around the panel; the HUD stays visible above it. X still returns to BASIC,
   also inside the shop.
