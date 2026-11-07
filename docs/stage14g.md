# Stage 14g – level 4: new enemies and new final boss, drawn by Claude

Branch `stage14`, release files in `releases/stage14g/`. Includes Stages 14c–14f (restart after dying at the boss,
cheat F).

## What is new
All level-4 enemies except the jets are new, drawn by Claude as one set in the style of the level-1 enemies
(steel grey, red accents, orange/yellow lights), with a small vector renderer (`tools/pixel_vector.py`) so the
diagonal views stay clean. Scripts: `assets/art/enemies-level4/source/claude_l4_enemies.py`,
`assets/art/boss-level4/source/claude_quad_mech.py`.
- **Jets**: the level-1 fighters (unchanged).
- **Attack helicopter** (small, 16×16, 8 directions): fuselage with canopy, stub wings with red rocket pods, tail
  boom; the rotor is one blurred blade pair turning by 60° per phase.
- **Gunship** (large, 32×32, replaces the drone; an original design, not a copy of any film or TV helicopter):
  charcoal fuselage with pointed nose, tandem canopy, twin engines with exhaust glow, stub wings with rocket pods,
  chin cannon, blurred four-blade rotor; banking views. 5 hits.
- **Small mech**: four-legged, twin cannons, walks only on the streets (4 directions, 4 steps).
- **Heavy walker**: four-legged, armoured hull with turret ring for its gun, 4 steps, burning wreck. 24 hits.
- **Final boss: four-legged heavy mech**. Symmetric seen from above, it walks in all four directions without
  turning; four feet step in diagonal pairs only while it walks, dust under the feet; four twin-barrel turrets;
  the reactor hatch in the middle opens in the core phase; flame thrower at the front; missiles start from the
  rack on its back and fly at the player.
- Level 4 a little easier: enemies fire less often (jets 4, gunships 6, helicopters 4, walkers 8, mechs 3 per 256
  frames), 16 guns instead of 24.

## Verification so far
| Check | Result |
|---|---|
| `tools/check_level4_art.py` | OK, no errors (aircraft area 285/324, mechs 48/48, boss 225/324) |
| Assembly; D81 read back | ✔ |
| XEMU level 4: helicopters, gunship formations, mechs, walkers | ✔ |
| XEMU boss: walks with stepping feet and dust, missiles, turrets, hatch opens, destroyed; glyphs afterwards equal `ENEM4` | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 4: do the enemies fit together and to the level-1 jets? Helicopters and gunships readable in all views?
2. Mechs and walkers walk smoothly, nothing blinks.
3. Boss: walks in all directions, feet step only while it walks, turrets, hatch, flame, missiles.
4. Difficulty of level 4 (with cheat F and without).
