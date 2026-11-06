# Stage 13c – Level 3: new artwork (PR #23)

Branch `stage13b` (PR #23 merged), release files in `releases/stage13c/`. Includes everything from Stage 13b.

## What is new
- **Wind turbines** seen from above: nacelle on the platform, the rotor as blades in a flat ellipse (3 phases).
- **Enemies redrawn**, slimmer and more detailed: seaplane blue with yellow, navy helicopter olive/sand,
  slimmer speedboat, patrol boat and frigate (own palette).
- **Carrier lying** (128×56, bow to the left): much more room below it. It glides between x 24 and 168, the jets
  start at the bow.

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level3_art.py` | OK, no errors (enemy set 279/324 and 48/48 glyphs, boss 225/324) |
| Assembly; D81 read back | ✔ |
| XEMU: carrier enters, glides with wake, jets start, turrets, lift opens, destroyed; glyphs afterwards equal `ENEM3` | ✔ |
| XEMU: new seaplanes, helicopters, patrol boat in the level | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 3: wind turbines look right from above and turn.
2. Seaplanes, helicopters and ships look good in all directions and stand out from the water.
3. Carrier: enough room below it; wake, radar, jets from the bow; destruction.
4. The Stage 13b points (ships glide in, formations, difficulty).
