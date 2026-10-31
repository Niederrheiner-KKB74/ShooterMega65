#!/usr/bin/env python3
"""Generate the Stage-1 placeholder assets (tiles, map, pixies, player sprite, palettes).

All graphics here are procedural placeholders so the engine can be tested before
real artwork exists. The output formats are the ones the engine expects, so real
artwork only has to be converted into the same layout later (see docs/design.md).

Outputs (into the given directory):
  tiles.bin      NCM glyphs for the landscape, 64 bytes each (glyph TILE_CHAR_BASE+n)
  map.bin        MAP_ROWS rows x 21 bytes: tile glyph offset per column, row 0 = level start (bottom)
  mapcol.bin     MAP_ROWS rows x 21 bytes: colour-RAM byte 1 (palette bank << 4 | $0F)
  pixies.bin     NCM glyphs for pixie frames (glyph PIXIE_CHAR_BASE+n), column stacks with blank guards
  sprite.bin     two 16-colour sprites (left/right half of the player plane), 192 bytes each, 256-byte aligned
  palette.bin    256 x (R,G,B) nibble-swapped MEGA65 palette register values for the text palette
  sprpal.bin     32 x (R,G,B) for the sprite palette (sprite 0 and 1)
  assets.inc     KickAssembler constants (sizes, frame numbers)
  frames.inc     frame table (glyph base, width, height)
  preview_*.png  previews for humans
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

MAP_COLS = 21          # 21 x 16 px = 336 px (16 px hidden under the left border)
META_ROWS = 256        # 16x16 metatiles; map rows = 2 * META_ROWS glyph rows
MAP_ROWS = META_ROWS * 2

# ---------------------------------------------------------------- palettes
# Palette bank 1 ($10-$1F): landscape. Index 0 of every bank is transparent/background.
PAL_TILES = [
    (0, 0, 0),        # 0  (background colour / transparent)
    (24, 64, 24),     # 1  dark green
    (40, 100, 36),    # 2  green
    (72, 140, 52),    # 3  light green
    (20, 44, 110),    # 4  deep water
    (36, 80, 160),    # 5  water
    (110, 170, 230),  # 6  wave highlight
    (150, 120, 70),   # 7  dark sand
    (210, 180, 110),  # 8  sand
    (90, 60, 30),     # 9  soil / trunk
    (14, 48, 20),     # 10 forest dark
    (60, 120, 40),    # 11 forest highlight
    (110, 80, 44),    # 12 field brown
    (140, 110, 60),   # 13 field light
    (230, 210, 80),   # 14 flowers / crop
    (8, 20, 10),      # 15 shadow
]
# Palette bank 2 ($20-$2F): objects (enemies, tanks, bullets, explosions)
PAL_OBJ = [
    (0, 0, 0),        # 0 transparent
    (16, 16, 24),     # 1 k outline
    (120, 120, 130),  # 2 g grey
    (190, 190, 200),  # 3 G light grey
    (200, 40, 40),    # 4 R red
    (80, 220, 240),   # 5 c glass
    (60, 70, 30),     # 6 o olive dark
    (100, 110, 50),   # 7 O olive
    (150, 160, 80),   # 8 P olive light
    (255, 230, 60),   # 9 y yellow
    (255, 140, 30),   # 10 a orange
    (255, 255, 255),  # 11 w white
    (230, 60, 20),    # 12 e bullet red/orange
    (120, 20, 20),    # 13 r dark red
    (70, 60, 60),     # 14 s smoke
    (40, 36, 36),     # 15 S dark smoke
]
OBJ_KEY = {'.': 0, 'k': 1, 'g': 2, 'G': 3, 'R': 4, 'c': 5, 'o': 6, 'O': 7, 'P': 8,
           'y': 9, 'a': 10, 'w': 11, 'e': 12, 'r': 13, 's': 14, 'S': 15}
# Sprite palette (palette set 1, entries 0-15 for sprite 0 and 16-31 for sprite 1)
PAL_SPR = [
    (0, 0, 0),        # 0 . transparent
    (10, 14, 30),     # 1 k outline
    (30, 50, 110),    # 2 b dark blue
    (60, 100, 190),   # 3 B blue
    (140, 180, 240),  # 4 L light blue
    (250, 250, 250),  # 5 w white
    (190, 30, 30),    # 6 r red
    (250, 90, 80),    # 7 R light red
    (40, 170, 200),   # 8 c canopy
    (170, 240, 255),  # 9 C canopy highlight
    (255, 230, 60),   # 10 y yellow
    (120, 120, 130),  # 11 g grey
    (190, 190, 200),  # 12 G light grey
    (255, 140, 30),   # 13 o flame
    (60, 60, 70),     # 14 d dark grey
    (255, 255, 255),  # 15
]
SPR_KEY = {'.': 0, 'k': 1, 'b': 2, 'B': 3, 'L': 4, 'w': 5, 'r': 6, 'R': 7, 'c': 8,
           'C': 9, 'y': 10, 'g': 11, 'G': 12, 'o': 13, 'd': 14}


def swap(v):
    """MEGA65 palette registers hold the colour value with swapped nibbles."""
    return ((v & 0x0F) << 4) | (v >> 4)


# ---------------------------------------------------------------- glyph helpers
def ncm_glyph(pix):
    """16x8 array of colour indices -> 64 bytes NCM (left pixel in the LOW nibble)."""
    assert pix.shape == (8, 16)
    out = bytearray()
    for y in range(8):
        for x in range(0, 16, 2):
            out.append((int(pix[y, x]) & 15) | ((int(pix[y, x + 1]) & 15) << 4))
    return bytes(out)


def art(lines, key, mirror=False):
    rows = []
    for line in lines:
        row = [key[c] for c in line]
        if mirror:
            row = row + row[::-1]
        rows.append(row)
    return np.array(rows, dtype=np.uint8)


# ---------------------------------------------------------------- landscape metatiles
rng = random.Random(6502)


def noise_tile(colours, weights):
    t = np.zeros((16, 16), np.uint8)
    for y in range(16):
        for x in range(16):
            t[y, x] = rng.choices(colours, weights)[0]
    return t


def grass(variant):
    t = noise_tile([1, 2, 3], [2, 6, 2])
    if variant == 1:     # flowers
        for _ in range(4):
            x, y = rng.randrange(1, 15), rng.randrange(1, 15)
            t[y, x] = 14
    if variant == 2:     # darker patch
        for y in range(16):
            for x in range(16):
                if (x - 8) ** 2 + (y - 8) ** 2 < 30 and rng.random() < .7:
                    t[y, x] = 1
    return t


def forest(variant):
    t = noise_tile([10, 1], [7, 3])
    centres = [(4, 4), (12, 5), (7, 11), (14, 13), (1, 12)] if variant == 0 else [(5, 6), (12, 2), (11, 11), (2, 14)]
    for cx, cy in centres:
        for y in range(16):
            for x in range(16):
                d = (x - cx) ** 2 + (y - cy) ** 2
                if d < 12:
                    t[y, x] = 11 if (x - cx + 1) ** 2 + (y - cy + 1) ** 2 < 4 else 2
                elif d < 16:
                    t[y, x] = 15
    return t


def water(mask, phase):
    """mask bits: 1=land above, 2=land below, 4=land left, 8=land right -> sand rim."""
    t = noise_tile([4, 5], [3, 7])
    for y in range(16):
        for x in range(16):
            if (x * 3 + y * 5 + phase) % 23 == 0:
                t[y, x] = 6
                if x + 1 < 16:
                    t[y, x + 1] = 6
    for y in range(16):
        for x in range(16):
            rim = 3 + ((x * 7 + y * 3 + phase) % 3 == 0)
            if (mask & 1 and y < rim) or (mask & 2 and y >= 16 - rim) or (mask & 4 and x < rim) or (mask & 8 and x >= 16 - rim):
                t[y, x] = 8 if rng.random() < .8 else 7
            elif (mask & 1 and y == rim) or (mask & 2 and y == 15 - rim) or (mask & 4 and x == rim) or (mask & 8 and x == 15 - rim):
                t[y, x] = 6
    return t


def field(variant):
    t = np.zeros((16, 16), np.uint8)
    for y in range(16):
        for x in range(16):
            stripe = (x // 2) % 2 if variant == 0 else (y // 2) % 2
            t[y, x] = (13 if stripe else 12) if rng.random() < .9 else 9
    return t


METATILES = {}
order = []


def add(name, pix):
    METATILES[name] = pix
    order.append(name)


for v in range(3):
    add(f'grass{v}', grass(v))
for v in range(2):
    add(f'forest{v}', forest(v))
for m in range(16):
    add(f'water{m}', water(m, m))
for v in range(2):
    add(f'field{v}', field(v))


def build_map():
    grid = [['grass0'] * MAP_COLS for _ in range(META_ROWS)]
    kinds = [[0] * MAP_COLS for _ in range(META_ROWS)]     # 0 land 1 water 2 forest 3 field
    for r in range(META_ROWS):
        centre = 10 + 5.5 * math.sin(r / 19.0) + 2.0 * math.sin(r / 6.3)
        width = 2.2 + 1.2 * math.sin(r / 11.0)
        if 40 <= r < 70 or 150 <= r < 175:      # stretches without river
            width = -1
        for c in range(MAP_COLS):
            if abs(c - centre) <= width:
                kinds[r][c] = 1
    for _ in range(26):     # forests
        r0, c0 = rng.randrange(META_ROWS), rng.randrange(MAP_COLS)
        rad = rng.uniform(1.5, 3.5)
        for r in range(META_ROWS):
            for c in range(MAP_COLS):
                if kinds[r][c] == 0 and (r - r0) ** 2 + ((c - c0) * 1.3) ** 2 < rad * rad:
                    kinds[r][c] = 2
    for _ in range(14):     # fields
        r0, c0 = rng.randrange(META_ROWS), rng.randrange(MAP_COLS - 4)
        h, w, v = rng.randrange(2, 5), rng.randrange(2, 5), rng.randrange(2)
        for r in range(r0, min(META_ROWS, r0 + h)):
            for c in range(c0, min(MAP_COLS, c0 + w)):
                if kinds[r][c] == 0:
                    kinds[r][c] = 3 + v
    for r in range(META_ROWS):
        for c in range(MAP_COLS):
            k = kinds[r][c]
            if k == 1:
                def land(rr, cc):
                    if cc < 0 or cc >= MAP_COLS:
                        return False
                    return kinds[rr % META_ROWS][cc] != 1
                # map row r+1 is further "up" on screen (later in the level)
                mask = (1 if land(r + 1, c) else 0) | (2 if land(r - 1, c) else 0) | \
                       (4 if land(r, c - 1) else 0) | (8 if land(r, c + 1) else 0)
                grid[r][c] = f'water{mask}'
            elif k == 2:
                grid[r][c] = f'forest{(r * 7 + c * 3) % 2}'
            elif k >= 3:
                grid[r][c] = f'field{k - 3}'
            else:
                h = (r * 131 + c * 71) % 11
                grid[r][c] = 'grass1' if h == 0 else 'grass2' if h == 1 else 'grass0'
    return grid


# ---------------------------------------------------------------- pixie frames
ENEMY = [
    "........",
    "....kkkk",
    "....kRRR",
    ".....kgg",
    "......kg",
    "k.....kg",
    "kk...kgg",
    "kRkkkggg",
    "kRRRRggg",
    "kgggggGG",
    ".kkkkkgG",
    "......kg",
    "......kc",
    "......kc",
    ".......k",
    "........",
]
TANK = [
    "........",
    ".kkkk...",
    ".koOk...",
    ".kOOkkkk",
    ".koOkOOO",
    ".kOOkOPP",
    ".koOkOPk",
    ".kOOkOPk",
    ".koOkOPk",
    ".kOOkOPP",
    ".koOkOOO",
    ".kOOkkkk",
    ".koOk..k",
    ".kOOk..k",
    ".kkkk..k",
    "........",
]
PBULLET = [
    "........",
    "......yy",
    "......yw",
    "......yw",
    "......yw",
    "......yw",
    "......yy",
    "........",
]
EBULLET = [
    "........",
    "........",
    "......ae",
    ".....aye",
    ".....aye",
    "......ae",
    "........",
    "........",
]


def explosion(step):
    t = np.zeros((16, 16), np.uint8)
    r_out = [3.5, 5.5, 7.0, 7.5][step]
    r_in = [0, 1.5, 3.5, 5.5][step]
    cols = [[11, 9, 10], [9, 10, 12], [10, 12, 13], [14, 15, 14]][step]
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5) + rng.uniform(-1, 1)
            if r_in <= d <= r_out:
                f = (d - r_in) / max(.1, r_out - r_in)
                t[y, x] = cols[min(2, int(f * 3))]
    return t


# frames: name -> (pixel array, palette bank)
FRAMES = [
    ('ENEMY', art(ENEMY, OBJ_KEY, True)),
    ('TANK', art(TANK, OBJ_KEY, True)),
    ('PBULLET', art(PBULLET, OBJ_KEY, True)),
    ('EBULLET', art(EBULLET, OBJ_KEY, True)),
    ('EXPL0', explosion(0)),
    ('EXPL1', explosion(1)),
    ('EXPL2', explosion(2)),
    ('EXPL3', explosion(3)),
]

PLAYER_HALF = [
    "...............k",
    "..............kG",
    "..............kw",
    ".............kGw",
    ".............kcC",
    ".............kcc",
    "............kBcc",
    "............kBBc",
    "...........kBBBB",
    "..........kbBBLB",
    "........kkbBBBLB",
    "......kkbBBBBBLB",
    "....kkbbBBBrBBLB",
    "..kkbbBBBBrRBBLB",
    ".kbBBBBBBBBBBBLB",
    "kbbbbbbbBBBBBBLB",
    "kkkkkkkkbBBBBBLB",
    "........kbBBBBLB",
    ".........kBBBBLB",
    "........kbBBBBBB",
    ".......kbBBbBBBd",
    "......kbBBBbkdyo",
    "......kkkkkk.kyo",
    ".............oo.",
]


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    # ---- landscape glyphs: each metatile -> top & bottom glyph, deduplicated
    glyphs, glyph_index = [], {}

    def glyph_id(pix):
        g = ncm_glyph(pix)
        if g not in glyph_index:
            glyph_index[g] = len(glyphs)
            glyphs.append(g)
        return glyph_index[g]

    meta = {name: (glyph_id(METATILES[name][:8]), glyph_id(METATILES[name][8:])) for name in order}
    grid = build_map()
    map_bytes, col_bytes = bytearray(), bytearray()
    for r in range(META_ROWS):
        # glyph row 2r is the LOWER half (rows count upwards), 2r+1 the upper half
        for half in (1, 0):
            for c in range(MAP_COLS):
                map_bytes.append(meta[grid[r][c]][half])
                col_bytes.append(0x1F)   # palette bank 1, colour 15 = bank colour 15
    assert len(glyphs) <= 256
    (out / 'tiles.bin').write_bytes(b''.join(glyphs))
    (out / 'map.bin').write_bytes(map_bytes)
    (out / 'mapcol.bin').write_bytes(col_bytes)

    # ---- pixie glyph area: glyph 0 is blank; each frame column = h glyphs + trailing blank
    blank = bytes(64)
    pix_glyphs = [blank]
    frame_info = []
    for name, pix in FRAMES:
        h_px, w_px = pix.shape
        assert h_px % 8 == 0 and w_px % 16 == 0
        h, w = h_px // 8, w_px // 16
        base = len(pix_glyphs)
        for c in range(w):
            for i in range(h):
                pix_glyphs.append(ncm_glyph(pix[i * 8:(i + 1) * 8, c * 16:(c + 1) * 16]))
            pix_glyphs.append(blank)
        frame_info.append((name, base, w, h))
    (out / 'pixies.bin').write_bytes(b''.join(pix_glyphs))

    # ---- player sprite: 32x24 -> two 16x24 16-colour sprites, left pixel in the HIGH nibble
    player = art(PLAYER_HALF, SPR_KEY, True)
    spr = bytearray()
    for half in range(2):
        part = player[:, half * 16:(half + 1) * 16]
        data = bytearray()
        for y in range(24):
            for x in range(0, 16, 2):
                data.append((int(part[y, x]) << 4) | int(part[y, x + 1]))
        spr += data + bytes(256 - len(data))
    (out / 'sprite.bin').write_bytes(spr)

    # ---- palettes
    pal = [(0, 0, 0)] * 256
    # keep the 16 C64 colours in bank 0 so the border debug colours stay recognisable
    c64 = [(0, 0, 0), (255, 255, 255), (136, 0, 0), (170, 255, 238), (204, 68, 204), (0, 204, 85),
           (0, 0, 170), (238, 238, 119), (221, 136, 85), (102, 68, 0), (255, 119, 119), (51, 51, 51),
           (119, 119, 119), (170, 255, 102), (0, 136, 255), (187, 187, 187)]
    for i, c in enumerate(c64):
        pal[i] = c
    for i, c in enumerate(PAL_TILES):
        pal[0x10 + i] = c
    for i, c in enumerate(PAL_OBJ):
        pal[0x20 + i] = c
    (out / 'palette.bin').write_bytes(bytes(swap(c[ch]) for ch in range(3) for c in pal))
    sprpal = PAL_SPR + PAL_SPR
    (out / 'sprpal.bin').write_bytes(bytes(swap(c[ch]) for ch in range(3) for c in sprpal))

    # ---- constants
    lines = ['// generated by tools/make_assets.py - do not edit',
             f'.const MAP_ROWS={MAP_ROWS}', f'.const MAP_COLS={MAP_COLS}',
             f'.const TILE_GLYPHS={len(glyphs)}', f'.const PIXIE_GLYPHS={len(pix_glyphs)}']
    for i, (name, base, w, h) in enumerate(frame_info):
        lines.append(f'.const FR_{name}={i}   // glyph +{base}, {w}x{h} chars')
    (out / 'assets.inc').write_text('\n'.join(lines) + '\n')
    tables = ['// generated by tools/make_assets.py - do not edit',
              'frame_base: .byte ' + ','.join(str(b) for _, b, _, _ in frame_info),
              'frame_w: .byte ' + ','.join(str(w) for _, _, w, _ in frame_info),
              'frame_h: .byte ' + ','.join(str(h) for _, _, _, h in frame_info)]
    (out / 'frames.inc').write_text('\n'.join(tables) + '\n')

    # ---- previews
    def rgb(pix, palette):
        return np.array([[palette[v] for v in row] for row in pix], np.uint8)
    strip = np.vstack([np.hstack([METATILES[grid[r][c]] for c in range(MAP_COLS)]) for r in range(63, -1, -1)])
    Image.fromarray(rgb(strip, PAL_TILES)).resize((MAP_COLS * 16 * 2, 64 * 16 * 2), Image.NEAREST).save(out / 'preview_map.png')
    sheet = np.hstack([np.pad(p, ((0, 16 - p.shape[0]), (0, 2))) for _, p in FRAMES])
    Image.fromarray(rgb(sheet, PAL_OBJ)).resize((sheet.shape[1] * 4, 64), Image.NEAREST).save(out / 'preview_pixies.png')
    Image.fromarray(rgb(player, PAL_SPR)).resize((128, 96), Image.NEAREST).save(out / 'preview_player.png')
    print(f'assets: {len(glyphs)} tile glyphs, {len(pix_glyphs)} pixie glyphs, map {MAP_ROWS} rows')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'build/gen')
