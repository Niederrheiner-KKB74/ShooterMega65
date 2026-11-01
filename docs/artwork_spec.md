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

## Shop (Stage 3b, placeholders until the artwork exists)
- **Item icons: 16×16 pixels**, one per item: SHOT II, SHOT III, SHOT IV, MISSILE, SHIELD (invulnerability),
  BOMB, EXTRA LIFE, EXIT. They sit in the middle of a 64×40 cell, the name above, the price below.
- All shop graphics share **one 16-colour palette** (index 0 is not usable). Fixed roles: 1 panel background,
  2 outline/text shadow, 3 thick frame, 4 thin cell frame (blinks for the cursor), 5 text, 6 price, 7 frame light
  edge, 8 cell interior. **Icons may use indices 9–15 plus 2, 5, 8** (currently red, orange, yellow, green, cyan,
  grey, dark grey). A new icon set may bring new colours for 9–15. A dimmed copy of the palette is made
  automatically.
- Deliver the icons as indexed PNG or JSON pixel rows (like `assets/art/bonus-capsules`), in
  `assets/art/shop/`. The frame, font and texts are drawn by `tools/make_shop.py`.
- **HUD icons 8×8** (7 px wide plus one free column) in the HUD palette (bank 12): bomb and invulnerability
  (shield with a glow). Placeholders are in `tools/import_art.py` (`HUD_BOMB`, `HUD_INVULN`).

## Working with ChatGPT
- Ask for *"pixel art, top-down view, flat colours, no anti-aliasing, limited palette of 15 colours, on a
  transparent background, each sprite exactly 16×16 pixels (shown enlarged 8×)"*.
- Image generators rarely hit the exact pixel grid. Expect to scale the result down to the exact size
  (nearest neighbour), reduce the colours and clean it up in a pixel editor (Aseprite, LibreSprite, GIMP).
  I can build a helper that scales down and reduces colours as a first step if that helps.
- Save the finished PNGs in `assets/art/<theme>/` in the repository.
