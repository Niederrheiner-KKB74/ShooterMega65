#!/usr/bin/env python3
"""Level 2 (desert): sand, rocks and the boss yard redrawn by Claude (Stage 18b; the owner chose the proposal from a
preview: big seamless patterns instead of regular rows of single tiles).

  dune_bXY    64x64 px dunes (16 tiles): fine wind ripples, flat irregular crests with a lit edge and a lee
              shadow                                                                          (palette nature)
  rocksA_XY   rock formations 2x2, 3x2 and 3x1 tiles (A, B, C): rounded boulders lit from the top left, shadow
  rocksB_XY   on the sand; each lies only on its own dune block position (anchor), so the dunes run on
  rocksC_XY   seamlessly around it; scattered, never touching anything but dunes            (nature)
  yard_bX     64x16 px concrete plates for the boss yard: joints, light mottling, a crack      (structures)
The desert cells (sand0-8, red_scree, salt_flat, shaded_boulders) become dunes of their block position.

Tile budget: 20 unused tiles + the 12 desert tiles + yard = 33 places for 33 new tiles.

Patches assets/art/level2/generated (terrain.ncm.bin, level-example.json) and levels/level2.json (map), writes
generated/desert-preview.png.

    python3 assets/art/level2/source/claude_desert.py
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
G = ROOT / 'assets/art/level2/generated'
LEVEL = ROOT / 'levels/level2.json'
DESERT = [f'sand{i}' for i in range(9)] + ['red_scree', 'salt_flat', 'shaded_boulders']
FORM_SHARE = 0.2                 # per anchor position (every 4th column and row)
FORMS = [('rocksA', 2, 2, 11, (0, 0)), ('rocksB', 3, 2, 12, (1, 2)), ('rocksC', 3, 1, 15, (0, 1))]   # kind, w, h, seed, anchor


def ncm(a):
    return bytes(int(a[y, x]) | (int(a[y, x + 1]) << 4) for y in range(8) for x in range(0, 16, 2))


def put(terr, i, a):
    terr[i * 128:i * 128 + 64] = ncm(a[:8])
    terr[i * 128 + 64:i * 128 + 128] = ncm(a[8:])


def dunes():
    y, x = np.mgrid[0:64, 0:64]
    u, v = 2 * math.pi * x / 64, 2 * math.pi * y / 64
    crest = (v + 0.55 * np.sin(u + 0.5) + 0.4 * np.sin(3 * u - v + 1.3) + 0.25 * np.sin(2 * u + 2 * v + 0.4)) \
        / (2 * math.pi) % 1
    a = np.full((64, 64), 7, np.uint8)
    rip = (2 * math.pi * (5 * x / 64 + 11 * y / 64) + 1.4 * np.sin(u * 2 + v) + 0.8 * np.sin(3 * v - u)) % (2 * math.pi)
    a[rip < 0.9] = 8
    a[(rip > 3.2) & (rip < 3.9)] = 6
    a[(crest > 0.0) & (crest < 0.04)] = 8              # sunlit crest edge
    a[(crest >= 0.04) & (crest < 0.09)] = 5            # lee slope shadow
    a[(crest >= 0.09) & (crest < 0.2) & (a != 8)] = 6
    return a


def boulders(w, h, seed):
    """rock formation w x h tiles; 255 = transparent (the dunes show through)"""
    rng = np.random.default_rng(seed)
    W, H = w * 16, h * 16
    a = np.full((H, W), 255, np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    rocks = []
    for _ in range(60):
        r = rng.uniform(3.0, min(7.5, (H - 5) / 2))
        cx, cy = rng.uniform(r + 2, W - r - 3), rng.uniform(r + 2, H - r - 3)
        e = ((cx - W / 2) / (W / 2)) ** 2 + ((cy - H / 2) / (H / 2)) ** 2
        if e < 0.75 and all(math.hypot(cx - px, cy - py) > 0.8 * (r + pr) for px, py, pr in rocks):
            rocks.append((cx, cy, r))
    shadow = np.zeros((H, W), bool)
    for cx, cy, r in rocks:
        shadow |= np.hypot(xx - cx - 2.5, (yy - cy - 2.5) * 1.2) < r
    a[shadow] = 15
    for cx, cy, r in sorted(rocks, key=lambda t: t[1]):
        dx, dy = xx - cx, yy - cy
        m = np.hypot(dx, dy * 1.15) < r + 0.5 * np.sin(np.arctan2(dy, dx) * 5 + cx)
        lit = (-dx - dy) / r
        col = np.where(lit > 0.7, 8, np.where(lit > 0.25, 5, np.where(lit > -0.3, 4, np.where(lit > -0.75, 3, 2))))
        a[m] = col[m]
    return a


def plates():
    """concrete plates 32x16 (palette structures): joints 4 with a light edge 6, mottling, one crack"""
    rng = np.random.default_rng(9)
    y, x = np.mgrid[0:16, 0:64]
    n = sum(rng.uniform(0.5, 1) * np.sin(2 * math.pi * (int(rng.integers(1, 5)) * x / 64
                                                       + int(rng.integers(-1, 2)) * y / 16) + rng.uniform(0, 6.3))
            for _ in range(4)) / 4 + rng.normal(0, 0.25, (16, 64))
    a = np.full((16, 64), 5, np.uint8)
    a[n > 0.55] = 6
    a[n < -0.6] = 4
    a[:, 0] = 4
    a[:, 32] = 4
    a[0, :] = 4
    a[:, 1] = 6
    a[:, 33] = 6
    a[1, :] = 6
    xx, yy = 8, 9
    for _ in range(14):
        a[yy % 16, xx % 64] = 3
        xx += 1
        yy += int(rng.integers(-1, 2))
        yy = min(max(yy, 3), 14)
    return a


def main():
    ex = json.loads((G / 'level-example.json').read_text())
    lv = json.loads(LEVEL.read_text())
    terr = bytearray((G / 'terrain.ncm.bin').read_bytes())
    tiles = ex['tiles']
    byname = {t['name']: t for t in tiles}
    if 'dune_b00' in byname:
        raise SystemExit('level 2 is already converted (dune_b00 exists)')
    M = [list(r) for r in lv['map']]
    R, C = len(M), len(M[0])
    used = Counter(t for row in M for t in row)
    desert = {byname[n]['id'] for n in DESERT}
    yard = byname['yard']['id']
    free = sorted([t['id'] for t in tiles if used[t['id']] == 0] + list(desert) + [yard])

    db, pb = dunes(), plates()
    forms = {k: boulders(w, h, sd) for k, w, h, sd, _ in FORMS}
    new = [('dune', db, 'nature')] + [(k, forms[k], 'nature') for k, *_ in FORMS] + [('yard', pb, 'structures')]
    tid = {}
    k = 0
    for kind, blk, pn in new:
        for by in range(blk.shape[0] // 16):
            for bx in range(blk.shape[1] // 16):
                t = next(t for t in tiles if t['id'] == free[k])
                k += 1
                t['name'] = f'{kind}_b{bx}{by}' if kind in ('dune', 'yard') else f'{kind}_{bx}{by}'
                t['palette'] = pn
                img = blk[by * 16:by * 16 + 16, bx * 16:bx * 16 + 16]
                if kind in forms:
                    tid[(kind, bx, by, 'img')] = img
                else:
                    put(terr, t['id'], img)
                tid[(kind, bx, by)] = t['id']
    print(f'{k} of {len(free)} free tiles used')

    def dune_of(r, c):
        return db[(3 - r % 4) * 16:(3 - r % 4) * 16 + 16, (c % 4) * 16:(c % 4) * 16 + 16]

    # rock formations: their tiles are drawn over the dunes of one fixed block position each
    # each formation sits only on its anchor block position (its tiles carry that dune background), so the dunes
    # run on seamlessly around it
    rng = np.random.default_rng(1)
    place = {}
    fpos = {k: a for k, _, _, _, a in FORMS}
    nform = 0
    for r in range(R - 2):
        for c in range(C - 3):
            for kind, w, h, _, anchor in FORMS:
                if (c % 4, r % 4) != anchor or rng.random() >= FORM_SHARE:
                    continue
                cells = [(r + i, c + j) for i in range(-1, h + 1) for j in range(-1, w + 1)]
                if all(0 <= rr < R and 0 <= cc < C and M[rr][cc] in desert and (rr, cc) not in place
                       for rr, cc in cells):
                    nform += 1
                    for i in range(h):
                        for j in range(w):
                            place[(r + i, c + j)] = (kind, j, h - 1 - i)
    for kind, w, h, _, (c0, r0) in FORMS:          # picture row by (0 = top) lies on map row r0 + h - 1 - by
        for j in range(w):
            for by in range(h):
                img = tid[(kind, j, by, 'img')]
                bg = dune_of(r0 + h - 1 - by, c0 + j).copy()
                bg[img != 255] = img[img != 255]
                put(terr, tid[(kind, j, by)], bg)

    for r in range(R):
        for c in range(C):
            t = M[r][c]
            if (r, c) in place:
                kind, j, by = place[(r, c)]
                M[r][c] = tid[(kind, j, by)]
            elif t in desert:
                M[r][c] = tid[('dune', c % 4, 3 - r % 4)]
            elif t == yard:
                M[r][c] = tid[('yard', c % 4, 0)]
    lv['map'] = M
    (G / 'terrain.ncm.bin').write_bytes(bytes(terr))
    (G / 'level-example.json').write_text(json.dumps(ex, indent=2) + '\n')
    txt = json.dumps(lv, indent=2, ensure_ascii=False)
    txt = re.sub(r'\[([^\[\]{}]*)\]', lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']'
                 if m.group(1).strip() else '[]', txt)
    LEVEL.write_text(txt + '\n')
    nat = np.array(json.loads((G / 'manifest.json').read_text())['palettes']['nature'], np.uint8)
    Image.fromarray(nat[db]).resize((256, 256), Image.NEAREST).save(G / 'desert-preview.png')
    print(f'{nform} rock formations, different rows {len(set(map(tuple, M)))}')


if __name__ == '__main__':
    main()
