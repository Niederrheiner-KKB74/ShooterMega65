#!/usr/bin/env python3
"""Level transition overlays (Stage 15): 'LEVEL CLEAR!' with a picture of the destroyed boss, and
'PREPARE FOR LEVEL n', each with a blinking 'PRESS FIRE TO CONTINUE'.

Like the shop pictures (tools/make_shop.py) every picture is an opaque rectangle of 16x8 NCM glyphs in the shop
palette; the game DMAs one picture at a time from attic RAM into the shop glyph area ($44000) and replaces
background tokens with it (blit_msg). Writes into build/gen/:

  TRANS            pictures 0-3 'LEVEL CLEAR' (boss of level 1-4), 4-7 'PREPARE FOR LEVEL 1-4';
                   per picture: glyphs (64 bytes each), then the glyph map and the attribute map (rows x cols)
  trans_const.inc  sizes and screen positions
  trans_data.inc   offsets, glyph counts and rows of the pictures
  preview_trans.png

The boss picture is composed from the boss artwork (body, legs/rotors, destroyed turrets, open core), darkened,
torn and set on fire, then mapped to the shop palette. Attribute 16 = normal palette, 18 = the blinking line.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import make_assets as ph  # noqa: E402
import make_shop as ms  # noqa: E402

FONT = dict(ms.FONT)
FONT['!'] = ['#', '#', '#', '#', '#', '.', '#']
COLS, CLEAR_ROWS, PREP_ROWS = 14, 14, 7
COL0, CLEAR_ROW0, PREP_ROW0 = 3, 5, 9
MAX_GLYPHS = 160                 # shop glyph area
BLINK, BLINK_SHADOW = 4, 8       # the blinking line: the game copies bank 13 into bank 15 and switches entries 4 and 8


def text(img, s, cx, y, colour, scale=1, shadow=2):
    w = (sum(len(FONT[c][0]) + 1 for c in s) - 1) * scale
    x = cx - w // 2
    for c in s:
        g = FONT[c]
        for layer, col, off in ((0, shadow, scale), (1, colour, 0)):
            if col is None:
                continue
            for gy, row in enumerate(g):
                for gx, ch in enumerate(row):
                    if ch == '#':
                        y0, x0 = y + gy * scale + off, x + gx * scale + off
                        img[y0:y0 + scale, x0:x0 + scale] = col
        x += (len(g[0]) + 1) * scale


def boss_rgb(level):
    d = ROOT / f'assets/art/boss-level{level}/generated'
    frames = {f['id']: f for f in json.loads((d / 'indexed-source.json').read_text())}
    pl = json.loads((d / 'placement.json').read_text())
    pal = list((d / 'palette.rgb').read_bytes())
    pal = [tuple(pal[i * 3:i * 3 + 3]) for i in range(16)]

    def arr(fid):
        f = frames[fid]
        return np.frombuffer(bytes.fromhex(''.join(f['rows'])), np.uint8).reshape(f['height'], f['width'])
    body = arr(pl['body'])
    parts = []
    for r in pl.get('rotors', []):
        parts.append((arr(pl['rotor_frames'][0]), r['offset']))
    legs_first = 'flame' in pl and 'catapult' in pl            # the mech: legs under the body
    canvas = np.zeros((body.shape[0] + 60, body.shape[1] + 40), np.uint8)
    ox, oy = 20, 10

    def put(a, x, y):
        h, w = a.shape
        sub = canvas[oy + y:oy + y + h, ox + x:ox + x + w]
        m = a[:sub.shape[0], :sub.shape[1]] != 0
        sub[m] = a[:sub.shape[0], :sub.shape[1]][m]
    if legs_first:
        for a, (x, y) in parts:
            put(a, x, y)
    put(body, 0, 0)
    if not legs_first:
        for a, (x, y) in parts:
            put(a, x, y)
    for t in pl['turrets']:
        put(arr(t['destroyed']), *t['offset'])
    put(arr(pl['core']['exposed_overlay']), *pl['core']['offset'])
    ys, xs = np.nonzero(canvas)
    canvas = canvas[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgb = np.zeros(canvas.shape + (3,), float)
    for i in range(1, 16):
        rgb[canvas == i] = pal[i]
    return rgb, canvas != 0


SHOP = [np.array(c, float) for c in ms.PAL]
WRECK_COLOURS = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14]      # no 6 (price yellow), 12, 15 (greens)


def wreck_picture(level, maxw, maxh):
    rgb, mask = boss_rgb(level)
    h, w = mask.shape
    s = min(1.0, maxw / w, maxh / h)
    if s < 1.0:                                                 # nearest-neighbour scaling down
        nh, nw = int(h * s), int(w * s)
        yi = (np.arange(nh) / s).astype(int)
        xi = (np.arange(nw) / s).astype(int)
        rgb, mask = rgb[yi][:, xi], mask[yi][:, xi]
        h, w = nh, nw
    rng = np.random.default_rng(100 + level)
    grey = rgb.mean(axis=2, keepdims=True)
    rgb = (rgb * 0.45 + grey * 0.55) * 0.62                     # burnt: less colour, darker
    for _ in range(int(w * h / 90)):                            # scorch marks and tears
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        for k in range(rng.integers(3, 9)):
            x, y = cx + k * rng.integers(-1, 2), cy + k * rng.integers(-1, 2)
            if 0 <= x < w and 0 <= y < h and mask[y, x]:
                rgb[y, x] = (10, 10, 14)
    out = np.zeros((h, w), np.uint8)
    for y in range(h):
        for x in range(w):
            if mask[y, x]:
                out[y, x] = min(WRECK_COLOURS, key=lambda i: ((SHOP[i] - rgb[y, x]) ** 2).sum())
    for _ in range(5 + level):                                  # fires
        cx, cy = rng.integers(w // 6, w - w // 6), rng.integers(h // 5, h - h // 4)
        for k in range(40):
            dx, dy = rng.normal(0, 2.2), -abs(rng.normal(0, 3.5))
            x, y = int(cx + dx), int(cy + dy)
            if 0 <= x < w and 0 <= y < h:
                r = abs(dx) + abs(dy) * 0.5
                out[y, x] = 5 if r < 1 else (11 if r < 2.2 else (10 if r < 3.6 else 9))
    return out


def smoke(img, x0, y0, w, h, rng):
    for _ in range(w * h // 18):
        x, y = x0 + rng.integers(0, w), y0 + rng.integers(0, h)
        if img[y, x] == 1:
            img[y, x] = 3 if rng.random() < 0.6 else 4


def clear_picture(level):
    img = np.zeros((CLEAR_ROWS * 8, COLS * 16), np.uint8)
    ms.frame(img, thick=2)
    text(img, 'LEVEL CLEAR!', img.shape[1] // 2, 7, 11, scale=2)
    wr = wreck_picture(level, img.shape[1] - 24, 64)
    h, w = wr.shape
    x0, y0 = (img.shape[1] - w) // 2, 26 + (64 - h) // 2
    rng = np.random.default_rng(level)
    smoke(img, x0 - 4, y0 - 6, w + 8, 14, rng)
    m = wr != 0
    img[y0:y0 + h, x0:x0 + w][m] = wr[m]
    return img, blink_line(img, CLEAR_ROWS)


def blink_line(img, rows):
    """'PRESS FIRE TO CONTINUE' fills token row rows-2 exactly (7 px + 1 px shadow); that row gets attribute 18"""
    r = rows - 2
    band = img[r * 8:r * 8 + 8]
    assert not np.isin(band[:, 4:-4], (BLINK, BLINK_SHADOW)).any()
    text(img, 'PRESS FIRE TO CONTINUE', img.shape[1] // 2, r * 8, BLINK, shadow=BLINK_SHADOW)
    attr = np.full((rows, COLS), 16, np.uint8)
    attr[r, :] = 18
    return attr


def prepare_picture(level):
    img = np.zeros((PREP_ROWS * 8, COLS * 16), np.uint8)
    ms.frame(img, thick=2)
    text(img, 'PREPARE FOR', img.shape[1] // 2, 7, 5)
    text(img, f'LEVEL {level}', img.shape[1] // 2, 18, 11, scale=2)
    return img, blink_line(img, PREP_ROWS)


def main(out):
    out = Path(out)
    pics = [clear_picture(n) for n in (1, 2, 3, 4)] + [prepare_picture(n) for n in (1, 2, 3, 4)]
    data, consts, report = b'', [], []
    offs, counts, rows = [], [], []
    for k, (img, attr) in enumerate(pics):
        assert not (img == 0).any(), f'picture {k}: colour 0'
        glyphs, index = [], {}
        r, c = img.shape[0] // 8, img.shape[1] // 16
        m = np.zeros((r, c), np.uint8)
        for y in range(r):
            for x in range(c):
                g = ph.ncm_glyph(img[y * 8:y * 8 + 8, x * 16:x * 16 + 16])
                if g not in index:
                    index[g] = len(glyphs)
                    glyphs.append(g)
                m[y, x] = index[g]
        if len(glyphs) > MAX_GLYPHS:
            sys.exit(f'transition picture {k}: {len(glyphs)} glyphs, room for {MAX_GLYPHS}')
        offs.append(len(data))
        counts.append(len(glyphs))
        rows.append(r)
        data += b''.join(glyphs) + bytes(m.reshape(-1)) + bytes(attr.reshape(-1))
        report.append(len(glyphs))
    if len(data) > 0xffff:
        sys.exit(f'TRANS: {len(data)} bytes, at most 64 KB')
    (out / 'TRANS').write_bytes(data)
    consts = ['// generated by tools/make_overlays.py - do not edit',
              f'.const TRANS_BYTES={len(data)}', f'.const TR_COLS={COLS}', f'.const TR_COL0={COL0}',
              f'.const TR_CLEAR_ROWS={CLEAR_ROWS}', f'.const TR_CLEAR_ROW0={CLEAR_ROW0}',
              f'.const TR_PREP_ROWS={PREP_ROWS}', f'.const TR_PREP_ROW0={PREP_ROW0}',
              f'.const TR_MAP_MAX={COLS * CLEAR_ROWS}']
    (out / 'trans_const.inc').write_text('\n'.join(consts) + '\n')
    tables = ['// generated by tools/make_overlays.py - do not edit',
              'tr_ofs_lo: .byte ' + ','.join(str(o & 255) for o in offs),
              'tr_ofs_hi: .byte ' + ','.join(str(o >> 8) for o in offs),
              'tr_glyphs: .byte ' + ','.join(str(n) for n in counts),
              'tr_rows: .byte ' + ','.join(str(n) for n in rows)]
    (out / 'trans_data.inc').write_text('\n'.join(tables) + '\n')
    prev = []
    for img, attr in pics:
        o = np.zeros(img.shape + (3,), np.uint8)
        for y in range(img.shape[0]):
            for x in range(img.shape[1]):
                v = img[y, x]
                o[y, x] = ms.PAL[v]
                if attr[y // 8, x // 16] == 18 and v in (BLINK, BLINK_SHADOW):
                    o[y, x] = ms.PAL[11] if v == BLINK else ms.PAL[2]
        prev.append(o)
    w = max(p.shape[1] for p in prev)
    canvas = np.full((sum(p.shape[0] + 4 for p in prev[:4]), 2 * w + 8, 3), 60, np.uint8)
    y = 0
    for p in prev[:4]:
        canvas[y:y + p.shape[0], :p.shape[1]] = p
        y += p.shape[0] + 4
    y = 0
    for p in prev[4:]:
        canvas[y:y + p.shape[0], w + 8:w + 8 + p.shape[1]] = p
        y += p.shape[0] + 4
    Image.fromarray(canvas).resize((canvas.shape[1] * 2, canvas.shape[0] * 2), Image.NEAREST).save(out / 'preview_trans.png')
    return [f'transitions: {len(pics)} pictures, glyphs {report}, {len(data)} bytes']


if __name__ == '__main__':
    print('\n'.join(main(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'build/gen')))
