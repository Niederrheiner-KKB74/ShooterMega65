# Stage 13 – Level 3 „Operation Offshore“

Branch `stage13`, based on `stage12-stable` plus PR #22 (artwork and map by ChatGPT). Release files are in
`releases/stage13/`. Design details: `docs/design.md` §22a, addresses: `docs/memory_map.md`.

## What is new
- **Level 3** after level 2: open sea with palm islands and reefs, oil field with drilling rigs, research platforms
  and wind farm, naval base. Music „Open Waters“. Key **3** on the title starts level 3 directly (test aid).
- **Animated tiles**: glittering water, turning wind turbines, flare stacks, blinking antenna lights.
- **Own enemies**: seaplanes and navy helicopters (in place of fighters and helicopters), speedboats (fast, only on
  water), patrol boats with a gun, frigates (slow, 40 hits, two guns). Guns on ships turn towards the player and
  ride with the ship.
- **Boss: aircraft carrier**. It glides slowly with a bow wave; four turrets, then the deck lift opens over the
  reactor. Every few seconds a jet takes off from the catapult and flies at the player (it cannot be shot down,
  dodge it).
- Inside: attic addresses per level from tables, enemy sets per level (`ENEM0`, `ENEM3`), palette and zero page of
  BASIC saved in chip RAM to make room in bank 0.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with 25 files read back; PRG ends at `$AA60` (music at `$AC00`) | ✔ |
| `tools/check_level3_art.py` (artwork PR #22) | OK, no errors |
| XEMU level 3: map scrolls, music `MUS3` in the slot, tile animations switch the right glyphs (checked in RAM) | ✔ |
| XEMU level 3: seaplanes, helicopters, patrol boat with gun, guns on islands; the enemy set in RAM equals `ENEM3` | ✔ |
| XEMU carrier: enters, glides, jets take off, turrets, deck lift, destroyed; afterwards the aircraft glyphs equal `ENEM3` | ✔ |
| XEMU regression: bosses of level 1 and 2 destroyed, glyphs restored (`ENEM0`); level 1 enemy set equals `PIXIES` | ✔ |
| XEMU: exit with X to BASIC, palette and screen correct | ✔ |
| Speedboats and frigates seen in XEMU | partly (patrol boat seen; speedboat/frigate only by code path) |
| Real MEGA65 | open |

## Hardware test checklist
1. Title: key 3 starts level 3. Levels 1 and 2 unchanged (aircraft, tanks, bosses).
2. Level 3: water glitters, wind turbines turn, flare stacks flicker, antenna lights blink. No wrong tiles elsewhere.
3. Seaplanes and navy helicopters look right in all directions.
4. Speedboats stay on the water and turn at islands and platforms; patrol boats carry a gun that aims and fires;
   frigates come down slowly with two guns; guns disappear with their ship.
5. Shops at the middle and the end of level 3 work.
6. Carrier: enters from the top, glides slowly with bow wave, radar turns; jets start from the catapult and fly at
   the player; four turrets, then the lift opens; destruction; afterwards all enemies look normal again.
7. After level 3 the game continues with level 1. X / RUN-STOP returns to BASIC with correct colours.
8. Difficulty of level 3 (with upgrades from levels 1 and 2)?
