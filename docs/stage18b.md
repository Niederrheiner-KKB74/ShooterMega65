# Stage 18b – new backgrounds for levels 1 and 2

Branch `stage18` (on top of Stage 18, which is not yet confirmed on hardware), release files in `releases/stage18b/`.
Includes Stage 18 (enemies also fire upwards).

## What is new
- **Level 1:** a mottled meadow (lighter and darker patches, tufts, a few flowers) instead of one grass tile; inside
  the forests a dense canopy of overlapping crowns of different sizes; at the forest edges whole crowns with
  shadows on the meadow; forest outlines redrawn irregular instead of rectangular; the sea with a still swell.
- **Level 2:** dune fields with fine wind ripples and flat irregular crests instead of the rows of rock and sand
  tiles; 42 rock formations in three shapes scattered over the dunes; concrete plates with joints on the boss yard.
- **Level format 3:** up to 512 different map rows per level (was 256) - the big patterns need more rows.

## Verification so far
| Check | Result |
|---|---|
| Assembly; all four levels built (L1 316, L2 316, L3 249, L4 235 rows; L1DAT 9,632 and L2DAT 9,760 of 10,240 bytes); D81 read back | ✔ |
| XEMU: level 1 pixel-identical to Stage 18 after the format change (before the new art) | ✔ |
| XEMU: levels 1 and 2 with the new art scroll and play (screenshots) | ✔ |
| Levels 3 and 4 with format 3 | built; not looked at in XEMU |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 1 from start to boss: meadow, forest inside and edge, sea, roads, bridge, city - no wrong tiles, no gaps.
2. Level 2 from start to boss: dunes, rock formations, canyon, oasis, refinery, boss yard - no wrong tiles.
3. Levels 3 and 4 look exactly as before (level format 3).
4. Destroyed buildings in levels 1 and 2 still show their ruins.
5. Stage 18 checklist (enemies fire upwards), if not done yet.
