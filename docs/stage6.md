# Stage 6 – Aircraft views, balance

Branch `stage6`, based on `stage5-stable` plus PR #13. Release files are in `releases/stage6/`.

## What is new
- **Aircraft views** (ChatGPT, PR #13): fighters and helicopters turn into their flight direction (8 views),
  bombers and armoured planes bank left/right while moving sideways; flames and rotors keep animating.
  Transparent holes inside the hulls are repaired; the large coin is smaller (18 px instead of 26).
- **Pixie glyphs from disk**: new file `PIXIES` (34 KB) with all object graphics, loaded at start into the
  enlarged pixie area (608 glyphs instead of 512). The program got 15 KB smaller (ends at `$8460`).
- **Music volume** 11 instead of 15 (shop 9, jingles 12); effects stay at full volume.
- **Shop**: fire counts only after it was released for 8 frames (160 ms), so a bouncing button no longer gives
  double actions.
- **Shield capsules**: 5 % chance per enemy shot down (was 15 %).
- D81 writer: more than 8 files possible.
- **Curved flight paths** (owner request after the first test): helicopters (`heli_hunt`: turn aside, hover and
  fire, cross the screen, snake down), bombers (`bomber_weave`: right, left, right, then dive) and armoured planes
  (`armour_sweep`: wide sweeps right and left) now fly curves, so all views are used. Edited in
  `levels/coastal_base.json` and in `tools/design_coastal_base.py`. Note: that generator script no longer
  reproduces the committed landscape (it makes a different map), so the level JSON is the source now.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 with `SHOOTER`, `MUSICTEST`, `SHOP`, `MUSIC`, `PIXIES`, `L1GFX`, `L1DAT` read back; pixies 535 of 608 | ✔ |
| XEMU: game starts after about 4 s (loading `PIXIES`); fighters turn into their flight direction (diagonal views in curves) | ✔ |
| XEMU shop (999 credits): purchases work; a second press 2 frames after releasing fire is ignored | ✔ |
| XEMU curve test level (helicopters, bombers, armoured planes early), memory dumps: helicopters W/SW/SE/S, bombers and armoured planes left/right/straight, each matching the velocity | ✔ |
| XEMU full level with scripted shop exits: past the level end into the second pass (frame 16,791), RRB overflow 0 | ✔ |
| **Real MEGA65** | **open – please test** |

## Hardware test checklist
1. Loading: how long until the game starts? (The new `PIXIES` file adds 34 KB.)
2. Fighters and helicopters point where they fly (also sideways and diagonally in curves), bombers and armoured
   planes bank when they move sideways (helicopters from about 1 minute, bombers from about 20 s, armoured planes
   after the mid-level shop). Flames/rotors still animate, no flicker when the view changes.
3. No see-through holes in the bomber and the armoured plane; the large coin is smaller.
4. Music is quieter compared with the effects.
5. Shop: no more double actions with fire (message, purchase dialog, YES/NO, EXIT).
6. Fewer shield capsules (about one in twenty enemies).
7. MUSICTEST and X back to BASIC still work.
