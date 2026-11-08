# Stage 17b – new sea in level 3, wreck field and flame column for the final boss

Branch `stage17` (after the owner confirmed Stage 17), release files in `releases/stage17b/`.

## What is new
- **Level 3, sea (variant C of the preview video, owner's choice).** The open sea is one 64×32 px swell block:
  long diagonal crests in six colours of a wave profile; the colour cycling now rotates 6 colours over two index
  ranges, so the crests travel over the water. Calm patches in between.
- **Coasts and wakes** (owner: they looked like foreign bodies): the reef/sandbank transitions now have a clean
  coastline with a thin light rim and calm water in front of it; wakes, oil, buoys, pipe and wind turbines lie in
  calm water whose edge fades into the swell. Shallow water and islands as before.
- **Final boss, wreck field:** halfway through the mech's death explosions big explosions cover it and from then on
  its burnt **wreck** lies where it fell (buckled legs, shot-up turrets, blown-out crater, small fires, debris
  around it). It smoulders until the level is clear.
- **The sphere's appearance is hidden:** at the end of the explosions four big explosions fill the crater; the sphere
  is in it and rolls down out of the wreck.
- **Flame column instead of the fire-shot stream:** the sphere rolls over the plane, stops, opens, a small flame
  flickers in the hatch (warning), then the same flame thrower as the earlier bosses burns straight down and follows
  the plane slowly; then the hatch stays open (core can be hit) as before.

## Verification so far
| Check | Result |
|---|---|
| Assembly (PRG ends at `$AA51`); D81 read back; `check_level3_art.py` | ✔ |
| XEMU level 3: swell, colour cycling, coasts, wakes, platforms | ✔ (screenshots) |
| XEMU `BALL_TEST` + `BOSS_TEST` + level 4: mech explodes → wreck (no glyph flash after the delayed swap) → sphere in four explosions, rolls out → rolls, aims, opens, flame column → hit while open → explodes → LEVEL CLEAR | ✔ |
| Hover tank (level 2) and carrier (level 3) flame thrower after moving its damage test into `hv_burn` | not reached in the automatic XEMU run (code only moved); hardware test |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 3 (key 3 on the title): does the sea look like moving water? Speed of the waves right? (`period` 9 in
   `animations.json`.)
2. Level 3: reef edges, island coasts, wakes, oil, buoys, wind turbines: do they still look like foreign bodies?
3. Level 2 and 3 bosses: flame thrower still burns and hurts as before.
4. Level 4 (key 4, F for full equipment): destroy the mech: explosions, the wreck stays, no flash of strange pixels
   when the wreck appears.
5. The sphere appears inside explosions in the crater and rolls out of the wreck.
6. The sphere rolls over the plane, opens, the warning flame flickers, the flame column burns down and follows the
   plane; it hurts only inside the column; afterwards the core can be hit.
7. Bomb during the sphere and during the wreck: colours stay right.
8. Sphere destroyed: explosions, LEVEL CLEAR, MISSION ACCOMPLISHED.
