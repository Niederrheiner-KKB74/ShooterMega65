#!/usr/bin/env python3
"""Level 1 (coastal base): meadow, forest and sea redrawn by Claude (Stage 18b; the owner chose the proposal from a
preview: big seamless patterns instead of single repeated tiles, irregular forest outlines).

  meadow_bXY  64x32 px meadow (8 tiles): lighter and darker patches, tufts, a few flowers   (palette nature)
  canopy_bXY  64x32 px dense forest: overlapping crowns of different sizes, shadows          (nature)
  wood_bXY    forest edge (8 tiles): whole crowns on the meadow of the same block position, their shadows
  sea_bX      32x16 px sea (2 tiles): diagonal swell, still                                  (water)
A forest cell whose 8 neighbours are all forest is canopy, any other forest cell an edge tile. Stage 18c: the 16
forest tiles are the last tile ids and carry "blocks_tanks" (tanks turn in front of them like in front of water),
and every tank starts in a 5x5-cell clearing.

Tile budget (126 tiles, all used before): the 15 pixel-identical road/bridge tile pairs are merged, grass0,
forest0-5, sea0, sea1, rocks and meadow (the dotted flower patch) go: 26 places for the 26 new tiles.
Forest outlines: within 2 cells of the old outline, meadow and forest cells are redrawn from the distance to the
outline plus a smooth noise field; only meadow and forest cells change.

Patches assets/art/coastal-base/generated (terrain.ncm.bin, level-example.json) and levels/coastal_base.json
(map, written without repeat blocks), writes generated/terrain-preview.png.

    python3 assets/art/coastal-base/source/claude_terrain.py
"""
import json
import math
import re
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
G = ROOT / 'assets/art/coastal-base/generated'
LEVEL = ROOT / 'levels/coastal_base.json'
OLD_GREEN = ['grass0', 'meadow', 'rocks']
OLD_FOREST = [f'forest{i}' for i in range(6)]
OLD_SEA = ['sea0', 'sea1']


def untile(terr, i):
    a = np.zeros((16, 16), np.uint8)
    for h in range(2):
        g = terr[(2 * i + h) * 64:(2 * i + h) * 64 + 64]
        for y in range(8):
            for x in range(16):
                a[h * 8 + y, x] = (g[y * 8 + x // 2] >> (4 * (x & 1))) & 15
    return a


def ncm(a):
    return bytes(int(a[y, x]) | (int(a[y, x + 1]) << 4) for y in range(8) for x in range(0, 16, 2))


def put(terr, i, a):
    terr[i * 128:i * 128 + 64] = ncm(a[:8])
    terr[i * 128 + 64:i * 128 + 128] = ncm(a[8:])


def noise(seed, fx, fy, n, h=32, w=64):
    """smooth periodic noise on a w x h block"""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]
    v = np.zeros((h, w))
    for _ in range(n):
        a, b = int(rng.integers(1, fx + 1)), int(rng.integers(-fy, fy + 1))
        v += rng.uniform(0.5, 1) * np.sin(2 * math.pi * (a * x / w + b * y / h) + rng.uniform(0, 6.3))
    return v / n


def meadow():
    """base 9; soft lighter (13) / darker (12) patches, tufts 10 and 8, a few flowers 7 and 4"""
    rng = np.random.default_rng(3)
    v = noise(1, 3, 2, 4) + 0.45 * noise(2, 6, 4, 4) + rng.normal(0, 0.18, (32, 64))
    a = np.full((32, 64), 9, np.uint8)
    a[v > 0.42] = 13
    a[v < -0.45] = 12
    for _ in range(70):
        x, y = int(rng.integers(0, 64)), int(rng.integers(0, 32))
        a[y, x] = 10 if a[y, x] != 12 else 9
        if rng.random() < 0.5:
            a[(y + 1) % 32, x] = 8 if a[y, x] == 10 else 12
    for _ in range(9):
        x, y = int(rng.integers(0, 64)), int(rng.integers(0, 32))
        if v[y, x] > 0:
            a[y, x] = 7 if rng.random() < 0.6 else 4
    return a


def crown_colours(dx, dy, r):
    lit = (-dx - dy) / (r + 0.01)                  # light from the top left
    return np.where(lit > 0.55, 10, np.where(lit > 0.05, 13, np.where(lit > -0.5, 9, np.where(lit > -0.85, 12, 8))))


def canopy():
    """dense forest: overlapping crowns of different sizes, wrapping around the 64x32 block"""
    rng = np.random.default_rng(5)
    a = np.full((32, 64), 11, np.uint8)
    crowns = []
    for _ in range(400):
        x, y, r = rng.uniform(0, 64), rng.uniform(0, 32), rng.choice([3.2, 4.2, 5.2, 6.5], p=[.25, .35, .25, .15])
        if all(min(abs(x - cx), 64 - abs(x - cx)) ** 2 + min(abs(y - cy), 32 - abs(y - cy)) ** 2
               > (0.72 * (r + cr)) ** 2 for cx, cy, cr in crowns):
            crowns.append((x, y, r))
    yy, xx = np.mgrid[0:32, 0:64]
    for cx, cy, r in sorted(crowns, key=lambda t: t[1]):
        dx = (xx - cx + 32) % 64 - 32
        dy = (yy - cy + 16) % 32 - 16
        m = np.hypot(dx, dy * 1.05) < r + 0.36 * np.sin(np.arctan2(dy, dx) * 7 + cx)
        sh = (np.hypot(dx - 1.5, dy - 1.5) < r + 0.6) & ~m & (a != 11)
        a[sh] = np.minimum(a[sh], 8)
        a[m] = crown_colours(dx, dy, r)[m]
    return a


def wood(mb):
    """forest edge: per block tile whole crowns (none crosses the tile border) on the meadow, with shadows"""
    out = np.zeros((32, 64), np.uint8)
    yy, xx = np.mgrid[0:16, 0:16]
    for k in range(8):
        bx, by = k % 4, k // 4
        rng = np.random.default_rng(40 + k)
        cr = []
        for _ in range(300):
            r = rng.choice([2.6, 3.2, 3.9, 4.6, 5.4], p=[.15, .25, .25, .2, .15])
            x, y = rng.uniform(r + 0.6, 15.4 - r - 0.6), rng.uniform(r + 0.6, 15.4 - r - 0.6)
            if all(math.hypot(x - p, y - q) > 0.78 * (r + s) for p, q, s in cr):
                cr.append((x, y, r))
        g = mb[by * 16:by * 16 + 16, bx * 16:bx * 16 + 16]
        a = g.copy()
        crown = np.zeros((16, 16), bool)
        for cx, cy, r in cr:
            crown |= np.hypot(xx - cx, yy - cy) < r
        for cx, cy, r in cr:                        # shadows on the meadow first
            sh = (np.hypot(xx - cx - 1.3, yy - cy - 1.3) < r) & ~crown
            a[sh] = np.where(g[sh] == 13, 12, 8)
        for cx, cy, r in sorted(cr, key=lambda t: t[1]):
            dx, dy = xx - cx, yy - cy
            m = np.hypot(dx, dy) < r + 0.45 * np.sin(np.arctan2(dy, dx) * 6 + cx * 3)
            a[m] = crown_colours(dx, dy, r)[m]
        out[by * 16:by * 16 + 16, bx * 16:bx * 16 + 16] = a
    return out


def sea():
    """32x16 still swell: crest 3, trough 1 on 2, diagonal, gentle bends"""
    y, x = np.mgrid[0:16, 0:32]
    u, v = 2 * math.pi * x / 32, 2 * math.pi * y / 16
    th = 2 * u + v + 0.5 * np.sin(u - v + 0.7) + 0.3 * np.sin(u + 2 * v + 2.1)
    f = (th / (2 * math.pi)) % 1
    a = np.full((16, 32), 2, np.uint8)
    a[f < 0.1] = 3
    a[(f > 0.6) & (f < 0.72)] = 1
    return a


def cell(blk, r, c):
    rows = blk.shape[0] // 16
    cols = blk.shape[1] // 16
    by, bx = rows - 1 - (r % rows), c % cols          # map rows count upwards
    return by, bx


def expand(m):
    out = []
    for e in m:
        if isinstance(e, dict):
            out += [list(r) for _ in range(e.get('repeat', 1)) for r in e['rows']]
        else:
            out.append(list(e))
    return out


def main():
    ex = json.loads((G / 'level-example.json').read_text())
    lv = json.loads(LEVEL.read_text())
    terr = bytearray((G / 'terrain.ncm.bin').read_bytes())
    tiles = ex['tiles']
    byname = {t['name']: t for t in tiles}
    if 'meadow_b00' in byname:
        raise SystemExit('level 1 is already converted (meadow_b00 exists)')
    M = expand(lv['map'])

    # 1. merge pixel-identical tiles (same palette): the map uses the first one
    raw = {t['id']: bytes(terr[t['id'] * 128:t['id'] * 128 + 128]) for t in tiles}
    pal = {t['id']: t['palette'] for t in tiles}
    alias = {}
    for t in tiles:
        for u in tiles:
            if u['id'] < t['id'] and raw[u['id']] == raw[t['id']] and pal[u['id']] == pal[t['id']]:
                alias[t['id']] = alias.get(u['id'], u['id'])
                break
    M = [[alias.get(t, t) for t in row] for row in M]
    free = sorted(alias)

    # 2. classify cells
    ids = {n: byname[n]['id'] for n in OLD_GREEN + OLD_FOREST + OLD_SEA}
    green = {ids[n] for n in OLD_GREEN}
    forest = {ids[n] for n in OLD_FOREST}
    seaid = {ids[n] for n in OLD_SEA}
    free += [ids[n] for n in OLD_GREEN + OLD_FOREST + OLD_SEA]
    R, C = len(M), len(M[0])
    land = np.array([[t in green or t in forest for t in row] for row in M])
    fmask = np.array([[t in forest for t in row] for row in M])

    # 3. irregular forest outlines: signed distance to the outline + smooth noise (only meadow/forest cells)
    def dist(mask):
        d = np.full((R, C), 99)
        q = deque()
        for r in range(R):
            for c in range(C):
                if not mask[r, c]:
                    d[r, c] = 0
                    q.append((r, c))
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < R and 0 <= cc < C and d[rr, cc] > d[r, c] + 1:
                    d[rr, cc] = d[r, c] + 1
                    q.append((rr, cc))
        return d
    sd = dist(fmask) - dist(~fmask)                    # > 0 inside the forest (1 = edge cell), <= 0 outside
    rng = np.random.default_rng(12)
    rr, cc = np.mgrid[0:R, 0:C]
    nz = sum(rng.uniform(0.6, 1.0) * np.sin(2 * math.pi * (rr / rng.uniform(5, 13) + cc / rng.uniform(4, 11))
                                             + rng.uniform(0, 6.3)) for _ in range(4)) / 2.2
    nz += rng.normal(0, 0.35, (R, C))
    newf = np.where(np.abs(sd) <= 3, (sd + 1.6 * nz) > 0, fmask) & land
    # no lone meadow holes of one cell inside the forest, no single trees far out: tidy once
    for r in range(R):
        for c in range(C):
            if not land[r, c]:
                continue
            n = sum(newf[r + dr, c + dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                    if (dr or dc) and 0 <= r + dr < R and 0 <= c + dc < C)
            if newf[r, c] and n <= 1:
                newf[r, c] = False
            elif not newf[r, c] and n >= 7:
                newf[r, c] = True

    # Stage 18c: tanks only drive in the open - a clearing of 5x5 cells around every tank's starting point (it
    # appears just above the top edge in map column (x + 24) // 16); the forest tiles stop them (blocks_tanks)
    for e in lv['events']:
        if e.get('type') == 'ground' and e.get('enemy') == 'tank':
            r0, c0 = e['row'] + 1, (e['x'] + 24) // 16
            for r in range(r0 - 2, r0 + 3):
                for c in range(c0 - 2, c0 + 3):
                    if 0 <= r < R and 0 <= c < C:
                        newf[r, c] = False

    # 4. new tiles into the free places
    mb, cb = meadow(), canopy()
    wb, sb = wood(mb), sea()
    new = [('meadow', mb, 'nature'), ('canopy', cb, 'nature'), ('wood', wb, 'nature'), ('sea', sb, 'water')]
    tid = {}
    k = 0
    for kind, blk, pn in new:
        for by in range(blk.shape[0] // 16):
            for bx in range(blk.shape[1] // 16):
                i = free[k]
                k += 1
                t = next(t for t in tiles if t['id'] == i)
                t['name'] = f'{kind}_b{bx}{by}' if kind != 'sea' else f'sea_b{bx}'
                t['palette'] = pn
                put(terr, i, blk[by * 16:by * 16 + 16, bx * 16:bx * 16 + 16])
                tid[(kind, bx, by)] = i
    assert k == len(free), (k, len(free))

    # 5. the map
    def isf(r, c):
        return not (0 <= r < R and 0 <= c < C) or newf[r, c] or not land[r, c] and M[r][c] in forest
    for r in range(R):
        for c in range(C):
            t = M[r][c]
            if land[r, c]:
                by, bx = cell(mb, r, c)
                if newf[r, c]:
                    inner = all(isf(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))
                    M[r][c] = tid[('canopy' if inner else 'wood', bx, by)]
                else:
                    M[r][c] = tid[('meadow', bx, by)]
            elif t in seaid:
                by, bx = cell(sb, r, c)
                M[r][c] = tid[('sea', bx, by)]

    # 6. Stage 18c: the 16 forest tiles become the last tile ids and stop tanks (level header +39, land_store)
    n = len(tiles)
    forest_ids = [tid[(k, bx, by)] for k in ('canopy', 'wood') for by in range(2) for bx in range(4)]
    tail = list(range(n - len(forest_ids), n))
    swap = dict(zip([i for i in forest_ids if i not in tail], [i for i in tail if i not in forest_ids]))
    swap.update({b: a for a, b in list(swap.items())})
    byid = {t['id']: t for t in tiles}
    old_terr = bytes(terr)
    for a, b in swap.items():
        terr[b * 128:b * 128 + 128] = old_terr[a * 128:a * 128 + 128]
    for t in byid.values():
        t['id'] = swap.get(t['id'], t['id'])
        if t['id'] >= n - len(forest_ids):
            t['blocks_tanks'] = True
    tiles.sort(key=lambda t: t['id'])
    M = [[swap.get(t, t) for t in row] for row in M]

    lv['map'] = M
    (G / 'terrain.ncm.bin').write_bytes(bytes(terr))
    (G / 'level-example.json').write_text(json.dumps(ex, indent=2) + '\n')
    txt = json.dumps(lv, indent=2, ensure_ascii=False)
    txt = re.sub(r'\[([^\[\]{}]*)\]', lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']'
                 if m.group(1).strip() else '[]', txt)
    LEVEL.write_text(txt + '\n')
    prev = np.zeros((32, 64 * 3 + 16, 3), np.uint8)
    nat = np.array(json.loads((G / 'manifest.json').read_text())['palettes']['nature'], np.uint8)
    for k2, blk in enumerate((mb, cb, wb)):
        prev[:, k2 * 72:k2 * 72 + 64] = nat[blk]
    Image.fromarray(prev).resize((prev.shape[1] * 4, 128), Image.NEAREST).save(G / 'terrain-preview.png')
    print(f'{len(alias)} identical tiles merged, {len(free)} tiles redrawn; forest cells {int(fmask.sum())} -> '
          f'{int(newf.sum())}; different rows {len(set(map(tuple, M)))}')


if __name__ == '__main__':
    main()
