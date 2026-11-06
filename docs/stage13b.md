# Stage 13b – Level 3: balancing, formations, ships glide in

Branch `stage13b`, based on `stage13-stable`. Release files are in `releases/stage13b/`. The new artwork (wind
turbines, enemies, lying carrier) is ordered from ChatGPT (`docs/chatgpt_level3c.md`) and comes in a later stage.

## What is new
- **Ships glide into the picture** from above the top edge (speedboat 16, patrol boat 32, frigate 64 pixels above)
  instead of appearing whole.
- **More varied formations** in level 3: six new flight patterns (diving and aiming, scissors from both sides,
  spirals, swirling in from the side, helicopters that pop up, fire and retreat, helicopters that come in from the
  side), mixed with the level-1 patterns; 100 formation events instead of 61.
- **Harder level 3**: denser waves, 27 speedboats, 13 patrol boats, 7 frigates (before 18/8/5), 10 guns on islands
  and platforms (before 5). Per level now: hit points and firing chance of the enemy kinds. Level 3: seaplane 2 hits,
  navy helicopter 3, they fire more often (seaplane 5/256 per frame instead of 3, helicopter 6, patrol boat 8,
  frigate 10, speedboat 4). Levels 1 and 2 unchanged.
- The checker for the level-3 art now expects a fourth palette `frigate` and a lying carrier (≤ 128×64).

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 read back | ✔ |
| XEMU: new formations fly, patrol boat glides in from the top edge | ✔ |
| XEMU difficulty with a simple bot (fires, sways left/right, no dodging): level 3 old: 1 life left at frame 5,700; level 3 new: game over at frame 3,400; level 2: game over at frame 3,775 | level 3 now slightly harder than level 2 |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 3 (key 3): ships come into the picture from the top instead of appearing.
2. Formations varied enough? Do the new patterns look good (dives, scissors, spirals, side entries, helicopters)?
3. Difficulty: without upgrades level 3 should be hard; with upgrades from levels 1 and 2 doable.
4. Levels 1 and 2 unchanged.
