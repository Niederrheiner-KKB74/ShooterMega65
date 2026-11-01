#!/usr/bin/env python3
"""Shop graphics (Stage 3b): panel with 4x4 item cells, 'ENTERING SHOP' box, 'PURCHASE ITEM?' dialog.

The shop is drawn by replacing background tokens of the (paused) game screen, so every picture
is an opaque rectangle of 16x8 NCM glyphs. Writes into build/gen/:

  SHOP          SEQ file for the D81: 'SH', glyph count (16 bit), glyphs (64 bytes each).
                The game loads it to $44000 (char $1100), behind the landscape glyphs.
  shop_const.inc / shop_data.inc  placement constants; token maps (glyph index + attribute per token), item table, prices (BCD),
                the three shop palettes (normal, dimmed, highlight)
  preview_shop.png

Attribute of a token: 0-15 = item cell (palette chosen at run time: normal, dimmed or
highlighted), 16 = frame (always normal), 17/18 = YES/NO button of the dialog.

The items and prices are defined here only (ITEMS); the engine gets them from shop.inc.
Icons are placeholders until the artwork exists (docs/artwork_spec.md, shop icons).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import make_assets as ph  # noqa: E402

# ------------------------------------------------------------------ items (single source)
# code: 1-3 shot level 2-4, 4 missile, 5 shield (invulnerability), 6 bomb, 7 extra life, 8 exit
ITEMS = {                        # cell: (name, price, code, icon)
    0: ('SHOT II', 100, 1, 'shot2'),
    1: ('SHOT III', 200, 2, 'shot3'),
    2: ('SHOT IV', 400, 3, 'shot4'),
    3: ('MISSILE', 250, 4, 'missile'),
    4: ('SHIELD', 150, 5, 'shield'),
    5: ('BOMB', 200, 6, 'bomb'),
    6: ('EXTRA LIFE', 300, 7, 'life'),
    15: ('EXIT', 0, 8, 'exit'),
}

# ------------------------------------------------------------------ palette (16 colours)
PAL = [(0, 0, 0),            # 0 unused (index 0 is not drawn on opaque tokens)
       (18, 22, 40),         # 1 panel background
       (6, 6, 10),           # 2 outline / text shadow
       (96, 116, 160),       # 3 thick frame
       (78, 92, 128),        # 4 thin cell border (blinks in the highlight palette)
       (235, 240, 250),      # 5 text
       (255, 200, 60),       # 6 price
       (176, 194, 230),      # 7 thick frame light edge
       (30, 36, 64),         # 8 cell interior
       (220, 60, 50),        # 9 red
       (255, 140, 40),       # 10 orange
       (250, 230, 90),       # 11 yellow
       (80, 200, 100),       # 12 green
       (90, 200, 240),       # 13 cyan
       (150, 152, 165),      # 14 grey
       (72, 74, 88)]         # 15 dark grey
DIM = [tuple(int(c * 0.42) for c in rgb) for rgb in PAL]
HILITE = list(PAL)
HILITE[4] = (255, 230, 80)   # blinks between this and BLINK_B at run time
HILITE[8] = (44, 52, 92)     # the selected cell is a little lighter
BLINK_B = (255, 255, 255)

PANEL_ROW0, PANEL_COL0, PANEL_ROWS, PANEL_COLS = 3, 2, 22, 18     # screen rows / background tokens
MSG_ROW0, MSG_COL0, MSG_ROWS, MSG_COLS = 12, 7, 3, 8
DLG_ROW0, DLG_COL0, DLG_ROWS, DLG_COLS = 10, 6, 6, 10
CELL_W, CELL_H = 64, 40

FONT = {
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.####'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'],
    'J': ['..###', '...#.', '...#.', '...#.', '#..#.', '#..#.', '.##..'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'Q': ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['####.', '....#', '....#', '.###.', '....#', '....#', '####.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['.###.', '#....', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '....#', '.###.'],
    '$': ['..#..', '.####', '#.#..', '.###.', '..#.#', '####.', '..#..'],
    '?': ['.###.', '#...#', '....#', '...#.', '..#..', '.....', '..#..'],
    ' ': ['..', '..', '..', '..', '..', '..', '..'],
}


def text_width(s):
    return sum(len(FONT[c][0]) + 1 for c in s) - 1


def draw_text(img, s, cx, y, colour, shadow=2):
    """Centred at cx, top row y; 1-pixel shadow down right."""
    x = cx - text_width(s) // 2
    for c in s:
        g = FONT[c]
        for gy, row in enumerate(g):
            for gx, ch in enumerate(row):
                if ch == '#':
                    if shadow is not None and img[y + gy + 1, x + gx + 1] != colour:
                        img[y + gy + 1, x + gx + 1] = shadow
        for gy, row in enumerate(g):
            for gx, ch in enumerate(row):
                if ch == '#':
                    img[y + gy, x + gx] = colour
        x += len(g[0]) + 1


def rect(img, x0, y0, x1, y1, colour):        # outline, inclusive
    img[y0, x0:x1 + 1] = colour
    img[y1, x0:x1 + 1] = colour
    img[y0:y1 + 1, x0] = colour
    img[y0:y1 + 1, x1] = colour


def frame(img, thick=4, margin_x=0):
    """Outline, thick frame with a light inner-top edge, background inside."""
    h, w = img.shape
    img[:, :] = 1
    rect(img, 0, 0, w - 1, h - 1, 2)
    for t in range(1, thick + 1):
        rect(img, t, t, w - 1 - t, h - 1 - t, 3)
    rect(img, 1, 1, w - 2, h - 2, 7)
    img[h - 2, 1:w - 1] = 3
    img[1:h - 1, w - 2] = 3


def shape(rows, mapping):
    a = np.zeros((len(rows), len(rows[0])), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            a[y, x] = mapping.get(ch, 0)
    return a


ICONS = {
    'bullet': ['.c.', 'cdc', 'cdc', 'cdc', '.c.', '.y.'],
    'missile': ['.......r........', '......rrr.......', '......ggg.......', '......gWg.......',
                '......ggg.......', '......ggg.......', '......ggg.......', '.....dgggd......',
                '....ddgggdd.....', '...dd.ggg.dd....', '......ggg.......', '.....d.o.d......',
                '.......o........', '......yoy.......', '.......y........', '................'],
    'shield': ['................', '..ccccccccccc...', '.cyyyyyyyyyyyc..', '.cyWWWyyyyyyyc..',
               '.cyWyyyyyyyyyc..', '.cyyyyyyyyyyyc..', '.cyyyyyyyyyyyc..', '.cyyyyyyyyyyyc..',
               '..cyyyyyyyyyc...', '..cyyyyyyyyyc...', '...cyyyyyyyc....', '....cyyyyyc.....',
               '.....cyyyc......', '......cyc.......', '.......c........', '................'],
    'bomb': ['..........yo....', '.........o.y....', '........d.......', '.......dd.......',
             '.....ddddd......', '...dddddddddd...', '..dddddddddddd..', '..ddWWdddddddd..',
             '.dddWdddddddddd.', '.ddddddddddddd..', '.dddddddddddddd.', '..dddddddddddd..',
             '..dddddddddddd..', '...dddddddddd...', '.....dddddd.....', '................'],
    'life': ['.......c........', '......cWc.......', '......cWc.......', '......ccc.......',
             '.....cccccc.....', '...ccccccccc....', '.ccccccccccccc..', 'cccccc.c.cccccc.',
             '.......c........', '......ccc.......', '.....ccccc......', '.......r........',
             '......ror.......', '.......y........', '................', '................'],
    'exit': ['.......g........', '......ggg.......', '.....ggggg......', '....ggggggg.....',
             '...ggggggggg....', '..ggggggggggg...', '.....ggggg......', '.....ggggg......',
             '.....ggggg......', '.....ggggg......', '.....ggggg......', '................',
             '...WWWWWWWWWW...', '................', '................', '................'],
}
ICON_MAP = {'c': 13, 'd': 15, 'y': 11, 'r': 9, 'g': 14, 'W': 5, 'o': 10, 'G': 12}
ICON_MAP_EXIT = dict(ICON_MAP, g=12)


def icon(name):
    a = np.full((16, 16), 8, np.uint8)
    if name.startswith('shot'):
        n = int(name[4])
        b = shape(ICONS['bullet'], ICON_MAP)
        w = n * 4 - 1
        x0 = (16 - w) // 2
        for k in range(n):
            y0 = 5 if k in (0, n - 1) and n > 2 else 3
            sub = a[y0:y0 + 6, x0 + 4 * k:x0 + 4 * k + 3]
            sub[b > 0] = b[b > 0]
        return a
    s = shape(ICONS[name], ICON_MAP_EXIT if name == 'exit' else ICON_MAP)
    a[s > 0] = s[s > 0]
    return a


def cell_image(cell):
    img = np.ones((CELL_H, CELL_W), np.uint8)
    img[2:CELL_H - 2, 3:CELL_W - 3] = 8
    rect(img, 2, 1, CELL_W - 3, CELL_H - 2, 4)
    if cell in ITEMS:
        name, price, _, ic = ITEMS[cell]
        draw_text(img, name, CELL_W // 2, 4, 5)
        img[12:28, 24:40] = icon(ic)
        if price:
            draw_text(img, f'${price}', CELL_W // 2, 30, 6)
    return img


def panel_image():
    w, h = PANEL_COLS * 16, PANEL_ROWS * 8
    img = np.zeros((h, w), np.uint8)
    frame(img, thick=4)
    attr = np.full((PANEL_ROWS, PANEL_COLS), 16, np.uint8)
    for c in range(16):
        x, y = 16 + (c % 4) * CELL_W, 8 + (c // 4) * CELL_H
        img[y:y + CELL_H, x:x + CELL_W] = cell_image(c)
        attr[y // 8:(y + CELL_H) // 8, x // 16:(x + CELL_W) // 16] = c
    return img, attr


def message_image():
    img = np.zeros((MSG_ROWS * 8, MSG_COLS * 16), np.uint8)
    frame(img, thick=2)
    draw_text(img, 'ENTERING SHOP', img.shape[1] // 2, 8, 5)
    return img, np.full((MSG_ROWS, MSG_COLS), 16, np.uint8)


def dialog_image():
    img = np.zeros((DLG_ROWS * 8, DLG_COLS * 16), np.uint8)
    frame(img, thick=2)
    draw_text(img, 'PURCHASE ITEM?', img.shape[1] // 2, 9, 5)
    attr = np.full((DLG_ROWS, DLG_COLS), 16, np.uint8)
    for k, (word, col) in enumerate((('YES', 2), ('NO', 6))):
        x0, y0 = col * 16, 24
        img[y0 + 1:y0 + 15, x0 + 1:x0 + 31] = 8
        rect(img, x0 + 1, y0 + 1, x0 + 30, y0 + 14, 4)
        draw_text(img, word, x0 + 16, y0 + 4, 5)
        attr[3:5, col:col + 2] = 17 + k
    return img, attr


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    glyphs, index = [], {}

    def tokens(img):
        rows, cols = img.shape[0] // 8, img.shape[1] // 16
        m = np.zeros((rows, cols), np.int32)
        for r in range(rows):
            for c in range(cols):
                g = ph.ncm_glyph(img[r * 8:r * 8 + 8, c * 16:c * 16 + 16])
                if g not in index:
                    index[g] = len(glyphs)
                    glyphs.append(g)
                m[r, c] = index[g]
        return m

    pics = {'panel': panel_image(), 'msg': message_image(), 'dlg': dialog_image()}
    maps = {k: tokens(img) for k, (img, _) in pics.items()}
    assert all(not (img == 0).any() for img, _ in pics.values()), 'colour 0 in an opaque shop picture'
    if len(glyphs) > 255:
        sys.exit(f'shop: {len(glyphs)} glyphs, maximum 255 (16 KB load buffer)')
    (out / 'SHOP').write_bytes(b'SH' + len(glyphs).to_bytes(2, 'little') + b''.join(glyphs))

    def bcd(v):
        return int(str(v), 16)
    consts = ['// generated by tools/make_shop.py - do not edit',
             f'.const SHOP_GLYPHS={len(glyphs)}',
             f'.const PANEL_ROW0={PANEL_ROW0}', f'.const PANEL_COL0={PANEL_COL0}',
             f'.const PANEL_ROWS={PANEL_ROWS}', f'.const PANEL_COLS={PANEL_COLS}',
             f'.const MSG_ROW0={MSG_ROW0}', f'.const MSG_COL0={MSG_COL0}',
             f'.const MSG_ROWS={MSG_ROWS}', f'.const MSG_COLS={MSG_COLS}',
             f'.const DLG_ROW0={DLG_ROW0}', f'.const DLG_COL0={DLG_COL0}',
             f'.const DLG_ROWS={DLG_ROWS}', f'.const DLG_COLS={DLG_COLS}']
    (out / 'shop_const.inc').write_text('\n'.join(consts) + '\n')
    lines = ['// generated by tools/make_shop.py - do not edit']
    for k, (_, attr) in pics.items():
        lines.append(f'shop_{k}_glyph: .byte ' + ','.join(str(v) for v in maps[k].reshape(-1)))
        lines.append(f'shop_{k}_attr: .byte ' + ','.join(f'${v:02x}' for v in attr.reshape(-1)))
    lines.append('item_code: .byte ' + ','.join(str(ITEMS[c][2] if c in ITEMS else 0) for c in range(16)))
    lines.append('item_price_hi: .byte ' + ','.join(f'${bcd(ITEMS[c][1]) >> 8:02x}' if c in ITEMS else '0' for c in range(16)))
    lines.append('item_price_lo: .byte ' + ','.join(f'${bcd(ITEMS[c][1]) & 255:02x}' if c in ITEMS else '0' for c in range(16)))
    for name, pal in (('shop_pal', PAL), ('shop_pal_dim', DIM), ('shop_pal_hi', HILITE)):
        lines.append(f'{name}: .byte ' + ','.join(str(ph.swap(c[ch])) for ch in range(3) for c in pal))
    lines.append('shop_blink: .byte ' + ','.join(str(ph.swap(c)) for c in HILITE[4] + BLINK_B))
    (out / 'shop_data.inc').write_text('\n'.join(lines) + '\n')

    # preview: panel with cell 0 highlighted, cells 2/6 dimmed, dialog on top; message box separately
    def rgb(img, attr, state):
        o = np.zeros(img.shape + (3,), np.uint8)
        for r in range(img.shape[0]):
            for c in range(img.shape[1]):
                a = attr[r // 8, c // 16]
                p = state.get(a, PAL)
                o[r, c] = p[img[r, c]]
        return o
    pimg, pattr = pics['panel']
    st = {0: HILITE, 2: DIM, 3: DIM, 6: DIM}
    st.update({c: DIM for c in range(16) if c not in ITEMS})
    prev = rgb(pimg, pattr, st)
    dimg, dattr = pics['dlg']
    d = rgb(dimg, dattr, {18: HILITE})
    y0, x0 = (DLG_ROW0 - PANEL_ROW0) * 8, (DLG_COL0 - PANEL_COL0) * 16
    both = prev.copy()
    both[y0:y0 + d.shape[0], x0:x0 + d.shape[1]] = d
    mimg, mattr = pics['msg']
    m = rgb(mimg, mattr, {})
    canvas = np.full((prev.shape[0], prev.shape[1] * 2 + m.shape[1] + 16, 3), 60, np.uint8)
    canvas[:, :prev.shape[1]] = prev
    canvas[:, prev.shape[1] + 8:2 * prev.shape[1] + 8] = both
    canvas[:m.shape[0], 2 * prev.shape[1] + 16:] = m
    Image.fromarray(canvas).resize((canvas.shape[1] * 2, canvas.shape[0] * 2), Image.NEAREST).save(out / 'preview_shop.png')
    return [f'shop: {len(glyphs)} glyphs of 255, {len(ITEMS) - 1} items']


if __name__ == '__main__':
    print('\n'.join(main(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'build/gen')))
