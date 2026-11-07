# Stage 14b – Level 4: new city graphics, level-1 jets, heavy drone

Branch `stage14` (PR #26 merged), release files in `releases/stage14b/`. Includes everything from Stage 14.

## What is new
- **City background** redrawn by ChatGPT (PR #26): roofs with edges and shadows, streets with pavements and
  crossings, parks, ruins with rubble; mechs, walkers and guns placed anew for the new map.
- **Jets**: the fighters of level 1 (owner's wish), in their level-1 colours.
- **Heavy combat drone** drawn by Claude (`assets/art/enemies-level4/source/claude_drone.py`): 32×32 like the
  level-1 bomber, four ducted rotors with turning blades, armoured hull pointed towards the player, red sensor eye,
  hazard stripes, missile pods, gun barrels; banking views to the left and right. 6 hits (was 2).
- Attack helicopter, mech and walker: the redrawn frames of PR #26.

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level4_art.py` | OK, no errors (aircraft area 265 of 324 glyphs incl. 72 for the level-1 jets) |
| Assembly; D81 read back | ✔ |
| XEMU level 4: city, jets, drone formations, helicopters, mechs, walkers | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 4 (key 4): the city reads as a city; the jets are the level-1 fighters.
2. The heavy drones look big and threatening; rotors turn; they bank in curves.
3. Helicopters, mechs and walkers look better than in Stage 14.
4. The open points of the Stage 14 checklist (restart after a lost plane, mech boss, music).
