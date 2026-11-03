# Artwork specification

This describes how graphics have to look so the engine can use them directly. Converters
(PNG → MEGA65 data) will be written in Stage 3, and they follow this specification. Until then the game uses
generated placeholders (`docs/img/preview_*.png`).

## General rules (all graphics)
- **PNG at the exact final pixel size**: 1 image pixel = 1 game pixel (320×200 screen). It must be sharp,
  with no anti-aliasing, blur, gradients or JPEG artefacts.
- **Colours**: each tile or object uses **at most 15 colours plus transparency**, which is one 16-colour sub-palette.
  Colours can be any 24-bit RGB value. The MEGA65 palette has 8 bits per channel.
- **Transparency**: a real alpha channel, or pure magenta `#FF00FF`.
- View: **top-down**, light from the top left, the player flies **up** the screen.
- Keep shared colours identical: if several objects should share a palette, use exactly the same RGB values.

## Landscape (one set per level / theme)
| Item | Specification |
|---|---|
| Tile size | **16×16** pixels (the engine stores them as two 16×8 characters) |
| Palettes | Each 16×16 tile uses one palette of up to 15 colours. A level can use **2–4 landscape palettes**, for example grass/forest, water/coast, buildings |
| Level image | **336 px wide** (the leftmost 16 px are hidden under the border, so visible content belongs in x = 16..335), height a multiple of 16. The **bottom of the image is the level start** |
| Repetition | The converter cuts the image into 16×16 tiles and removes duplicates. Up to **512 different tiles per level**. Re-using tiles, like real tile-based art, keeps you well inside the limit |
| Fixed targets | Bunkers, flak guns and similar targets are drawn into the landscape at 16×16 or 32×32. Please supply a **destroyed (rubble) version** of each as well |

The easiest workflow is to design a tile sheet (a grid of 16×16 tiles), then assemble the level from it in an
editor such as Tiled. An AI-generated full landscape picture can also work, but it usually produces far too
many unique tiles and needs cleaning up.

## Moving objects (RRB pixies)
| Item | Specification |
|---|---|
| Width | **multiple of 16 px** (16, 32, 48 …) |
| Height | **multiple of 8 px** |
| Typical sizes | small enemy plane 16×16, tank/turret 16×16, bigger enemy 32×32, items/persons 16×16, shots 16×8 (the shot itself is just a few pixels inside it) |
| Boss | up to about 96×64 to 128×96, delivered as one image. Turrets and weak points should also be supplied as **separate small images**, so they can be destroyed one by one |
| Animation | frames side by side in **one horizontal strip**, all the same size |
| Explosions | 16×16 and 32×32, 4–8 frames |
| Palette | one 15-colour palette per object type. Several types can share one palette, for example "all enemies" |

Budget: several dozen pixies can be on screen, but each 16 px of object width costs raster
time in every 8-pixel row it touches. Many small objects are therefore cheaper than a few very wide ones.

## Player plane (hardware sprites)
- **32×24** pixels, 15 colours + transparency, facing up.
- Optional extra frames (tilting left/right, flashing when hit) as a strip of 32×24 frames.

## HUD (score strip at the top)
- A font of **8×8 or 8×16 digits 0–9** plus a few icons (lives, special weapon) in up to 15 colours.

## Shop (Stage 3b)
- **Item icons: 16×16 pixels**, one per item: SHOT II, SHOT III, SHOT IV, MISSILE, SHIELD (invulnerability),
  BOMB, EXTRA LIFE, EXIT. **Delivered (PR #9, `assets/art/shop-upgrades`):** SHOT II–IV, BOMB, MISSILE,
  SHIELD, drawn in the HUD palette; `tools/make_shop.py` maps their colours to the shop palette (`ICON_HUD_MAP`).
  **EXTRA LIFE and EXIT:** `assets/art/shop/generated/`, imported by `tools/make_shop.py`.
  Extra-Life is a nearest-neighbour miniature of the current straight-flight player;
  Exit is a green running-person/door/arrow pictogram. Both use only HUD colours 1–8 and 10.
  They sit in the middle of a 64×40 cell, the name above, the price below.
- All shop graphics share **one 16-colour palette** (index 0 is not usable). Fixed roles: 1 panel background,
  2 outline/text shadow, 3 thick frame, 4 thin cell frame (blinks for the cursor), 5 text, 6 price, 7 frame light
  edge, 8 cell interior. **Icons may use indices 9–15 plus 2, 5, 8** (currently red, orange, yellow, green, cyan,
  grey, dark grey). A new icon set may bring new colours for 9–15. A dimmed copy of the palette is made
  automatically.
- Deliver the icons as indexed PNG or JSON pixel rows (like `assets/art/bonus-capsules`), in
  `assets/art/shop/`. The frame, font and texts are drawn by `tools/make_shop.py`.
- **HUD icons 8×8** (7 px wide plus one free column) in the HUD palette (bank 12): bomb and invulnerability
  (shield with a glow). Placeholders are in `tools/import_art.py` (`HUD_BOMB`, `HUD_INVULN`).

## Boss (next stage)
The boss is a pixie object like the enemies, only bigger, and consists of parts that are destroyed one by one.
- **Main body**: at most **128×80 pixels** (multiples of 16 wide, 8 high), top-down view, flying or driving
  downwards (nose/front at the bottom). One frame plus, if wanted, a second "damaged" frame of the same size.
- **Parts**: 2–4 turrets or engines, each **16×16 or 32×32**, placed on the body. For every part: an intact and a
  destroyed view. Turrets that aim at the player: one view pointing down (south) and one diagonal (south-east);
  the other directions are made by rotation and mirroring, as for the aircraft.
- Optional effects: muzzle flash 16×16, 2–3 frames.
- **Colours**: at most **two 15-colour palettes** for the whole boss (body and parts), plus transparency
  (index 0). Index 0 inside the hull is see-through, so the hull must be closed.
- **Size budget**: all boss graphics together at most **9 KB** (about 140 glyphs of 16×8 pixels): for example a
  128×80 body in two frames is 2 × 8 columns × 11 = 176 glyphs, which is too much; 112×64 in two frames
  (2 × 7 × 9 = 126) or 128×80 in one frame plus parts fits. Empty columns cost nothing extra; empty rows inside a
  column do.
- In the same form as the other aircraft: indexed pixel rows (JSON) + palette, PNG previews, a placement list
  (offset of each part relative to the body's top left corner).

## Title screen and game-over screen (next stage)
- **Title screen**: full screen **320×200**, drawn in tiles of **16×8 pixels**. Each tile uses one of at most
  **four 15-colour palettes** (index 0 = background colour), so the picture can have up to 60 colours, but
  neighbouring areas with different palettes must meet on the 16×8 grid. Identical tiles are stored once, so
  calm areas (sky, plain background) are cheap: at most about **500 different tiles** (32 KB).
  Leave room for text that the game writes itself: a **320×24 band at the bottom** for "PRESS FIRE" and the high
  score, drawn with the shop font. The game title may be part of the picture.
- **Game-over screen**: an overlay like the shop: a **banner of 256×64 pixels** (16 tiles × 8 rows of 16×8) in the
  middle of the paused game screen, one 15-colour palette, at most **100 different tiles**. "GAME OVER", the score
  and "PRESS FIRE" are drawn by the game with the shop font; the banner provides frame and decoration.
- Delivery as for the landscape: indexed PNG plus JSON with palette(s) and, for the title, the palette number of
  every 16×8 tile.

## Destroyable buildings and ground guns (Stage 8)
Full brief for ChatGPT (German, ready to hand over): `docs/chatgpt_ground_targets.md`; checker:
`python3 tools/check_ground_targets.py`. In short:
- **A (required)**: destroyed variants of the 2×2 building groups of the coastal tileset (hangar, depot, checkpoint,
  bunker, radar, fuel, crates: 28 tiles), same footprint, outer 2 px close to the original, in the intact tile's
  palette or `fixed_targets`. `structures` is full; `fixed_targets` entries 1–11 stay (tanks), 12–15 may be new.
  Index 0 is not allowed in landscape tiles.
- **B (required)**: light ground gun 16×16 in `fixed_targets`: 8 directions drawn one by one (fixed base), 2 muzzle
  flash frames, wreck, barrel tip per direction.
- **C/D (optional)**: heavy gun 32×32; destroyed variants of the modular halls. At most 64 new tiles in total.
- Delivery: `assets/art/ground-targets/generated/ground-targets.json` (hex pixel rows) plus previews; no other files.

## Level 2 (next stage)
Brief for ChatGPT (German, ready to hand over): `docs/chatgpt_level2.md`; checker: `python3 tools/check_level2_art.py`.
Theme desert, canyon with river, oasis, oil refinery. Tileset ≤ 128 tiles in four palettes (`water` only for water:
tanks avoid it; `fixed_targets` exactly the level-1 palette), ≤ 48 destroyed tiles with explicit `kind`, `group`,
`col`, `row`; map `levels/level2.json` with shops, boss and end; boss in the PR #14 format, ≤ 162 glyphs.

## Working with ChatGPT
- Ask for *"pixel art, top-down view, flat colours, no anti-aliasing, limited palette of 15 colours, on a
  transparent background, each sprite exactly 16×16 pixels (shown enlarged 8×)"*.
- Image generators rarely hit the exact pixel grid. Expect to scale the result down to the exact size
  (nearest neighbour), reduce the colours and clean it up in a pixel editor (Aseprite, LibreSprite, GIMP).
  I can build a helper that scales down and reduces colours as a first step if that helps.
- Save the finished PNGs in `assets/art/<theme>/` in the repository.
