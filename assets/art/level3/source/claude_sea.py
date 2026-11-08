#!/usr/bin/env python3
"""Level-3 sea redrawn by Claude (Stage 17b, owner chose variant C of the preview; Stage 17c: narrower crests,
softer colours, slower, whitecaps - owner: on the big screen the wide colour bands looked like a blinking area;
Stage 17d: owner chose variant C of a second preview with the fine crest line of variant D).

The open water is a 64x32 px swell block (4x2 tiles): diagonal crests about 7.5 px apart, calm patches. Every moving
pixel carries a colour of the 5-colour cycle list 9, 10, 11, 1, 2 (a fine wave line: crest, crest edge, base, base,
shadow), so when the colours rotate (anim.asm, one step every 12 frames) the crests travel.

Whitecaps: palette indices 12 and 3 are not in the cycle. anim.asm gives them the current colour of the crest
register 9 (invisible), and lets them flash white and fade when the crest passes them - index 12 every 2nd pass,
index 3 every 3rd. Small flecks of them lie on the crest pixels of 8 extra sea tiles (cap_bXY, the same swell as
sea_bXY), which replace about one open-sea cell in eight at random, never two side by side, so they form no grid.

The swell block only joins itself, so the other water tiles (coast transitions, oil, wakes, buoy, pipe, wind
turbines) - used at changing block positions - get calm water (the still colours of the swell at their most frequent
block position): a calm band in the lee of the reefs, calm water along wakes and oil. Towards the tile border more and
more swell pixels are mixed in, so the calm areas have no hard edge. The coast transitions get a clean coastline:
the dithered border is smoothed and a 1-px rim of colour 5 separates the deep water from the shallow water.
Shallow water (shelf, reef, sandbank) and the islands keep their art; their old sparkle pixels (9-12, now swell
colours) become colour 7. No foam flecks: in a 64x32 block they form a visible grid.

  sea_bXY    open sea, block position X (0-3), Y (0-1) (were deep0-3 and sea0-3)
  cap_bXY    the same with whitecap flecks (were the unused tiles blue, shelf1, edge6, edge9, edge15, island6,
             island9 and one new tile)
The map is renumbered: an open-water cell gets the block tile of its position (column % 4, row % 2).

Patches assets/art/level3/generated (terrain.ncm.bin, level-example.json, manifest.json, animations.json) and
levels/level3.json (map), writes sea-preview.png.

    python3 assets/art/level3/source/claude_sea.py
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
G = ROOT / 'assets/art/level3/generated'
LEVEL = ROOT / 'levels/level3.json'
CYCLE = [9, 10, 11, 1, 2]
PROFILE = [(84, 146, 168), (54, 104, 132), (42, 86, 112), (42, 86, 112), (30, 64, 94)]
CALM = (4, 4)                                  # still colour of the calm patches (index 3 is a whitecap now)
CAPS = [{'index': 12, 'pos': 0, 'every': 2}, {'index': 3, 'pos': 0, 'every': 3}]
CAP_TILES = ['blue', 'shelf1', 'edge6', 'edge9', 'edge15', 'island6', 'island9']     # + one new tile
CAP_SHARE = 0.13
ROW_LIMIT = 252                                # the level format: at most 256 different rows (4 spare)
MAX_VAR = 8
SPARKLE = {9, 10, 11, 12}
SHALLOW = {6, 7, 8, 15}


def field(x, y):
    """swell phase (radians) and roughness, periodic in 64 x 32 px (y downwards) - variant C of the preview"""
    u, v = 2 * math.pi * x / 64, 2 * math.pi * y / 32
    th = 6 * u + 3 * v + 0.8 * math.sin(u - v + 0.7) + 0.45 * math.sin(3 * u + 2 * v + 2.1)
    rough = 0.55 + 0.3 * math.sin(u + 0.4) * math.cos(v + 1.0) + 0.15 * math.sin(3 * u - v + 1.7)
    return th, rough


def block(calm=False):
    rng = np.random.default_rng(7)
    a = np.zeros((32, 64), np.uint8)
    for y in range(32):
        for x in range(64):
            th, rough = field(x, y)
            f = (th / (2 * math.pi)) % 1.0
            if not calm and rough + rng.normal(0, 0.06) > 0.36:
                a[y, x] = CYCLE[int(f * len(CYCLE)) % len(CYCLE)]
            else:
                a[y, x] = CALM[0] if f < 0.5 else CALM[1]
    return a


def flecks(tile, rng):
    """whitecap flecks on the crest pixels (index 9) of a 16x16 swell tile: 1-2 small clusters, one per cap index"""
    a = tile.copy()
    crest = list(zip(*np.nonzero(a[1:15, 1:15] == CYCLE[0])))
    rng.shuffle(crest)
    caps = [c['index'] for c in CAPS]
    rng.shuffle(caps)
    used = []
    for y, x in crest:
        y, x = y + 1, x + 1
        if len(used) == 2 or any(abs(y - yy) + abs(x - xx) < 7 for yy, xx in used):
            continue
        cap = caps[len(used)]
        todo, n = [(y, x)], 0                           # 4-6 crest pixels around the seed
        size = int(rng.integers(4, 7))
        while todo and n < size:
            yy, xx = todo.pop(0)
            if not (1 <= yy < 15 and 1 <= xx < 15) or a[yy, xx] != CYCLE[0]:
                continue
            a[yy, xx] = cap
            n += 1
            todo += [(yy + dy, xx + dx) for dy, dx in ((0, 1), (0, -1), (-1, 1), (1, -1), (1, 0), (-1, 0))]
        used.append((y, x))
    assert used, 'no crest pixel for a whitecap'
    return a


def calm_tex(blk, still, bx, by, seed):
    """calm water for coast and feature tiles; towards the tile border more and more swell pixels (a soft edge)"""
    sw, ca = cell(blk, bx, by), cell(still, bx, by)
    rng = np.random.default_rng(100 + seed)
    out = ca.copy()
    for y in range(16):
        for x in range(16):
            d = min(x, y, 15 - x, 15 - y)
            if d < 3 and rng.random() < (0.55, 0.3, 0.12)[d]:
                out[y, x] = sw[y, x]
    return out


def neighbours(m, y, x):
    return [m[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < 16 and 0 <= xx < 16]


def coast(a, tex):
    """coast transition tile: smooth shallow area, rim 5, swell outside"""
    s = np.isin(a, list(SHALLOW))
    for y in range(16):                                  # sparkles follow their surroundings
        for x in range(16):
            if a[y, x] in SPARKLE:
                s[y, x] = sum(neighbours(np.isin(a, list(SHALLOW)), y, x)) >= 2
    t = s.copy()
    for y in range(1, 15):                               # 3x3 majority, borders kept for the neighbours
        for x in range(1, 15):
            t[y, x] = s[y - 1:y + 2, x - 1:x + 2].sum() >= 5
    out = np.where(t, np.where(np.isin(a, list(SHALLOW)), a, 6), tex).astype(np.uint8)
    for y in range(16):
        for x in range(16):
            if not t[y, x] and any(neighbours(t, y, x)):
                out[y, x] = 5
    return out


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


def cell(block_img, bx, by):
    return block_img[by * 16:by * 16 + 16, bx * 16:bx * 16 + 16]


def by_of(row):
    """map row r (rows go upwards): even rows show the lower half of the block, odd rows the upper half"""
    return 1 - (row & 1)


def main():
    ex = json.loads((G / 'level-example.json').read_text())
    man = json.loads((G / 'manifest.json').read_text())
    anims = json.loads((G / 'animations.json').read_text())
    lv = json.loads(LEVEL.read_text())
    terr = bytearray((G / 'terrain.ncm.bin').read_bytes())
    tiles = ex['tiles']
    byname = {t['name']: t for t in tiles}
    if 'sea_b00' in byname:
        raise SystemExit('the sea is already converted (sea_b00 exists)')

    wp = man['palettes']['water']
    for idx, c in zip(CYCLE, PROFILE):
        wp[idx] = list(c)
    for c in CAPS:                                      # off: the crest colour (anim.asm copies it every frame)
        wp[c['index']] = list(PROFILE[0])
    blk = block()
    still = block(calm=True)

    # open sea: 8 block tiles
    sea_old = [f'deep{i}' for i in range(4)] + [f'sea{i}' for i in range(4)]
    is_sea = {byname[n]['id'] for n in sea_old + ['blue']}
    new_id = {}
    for k, n in enumerate(sea_old):
        bx, by = k % 4, k // 4
        t = byname[n]
        t['name'] = f'sea_b{bx}{by}'
        put(terr, t['id'], cell(blk, bx, by))
        new_id[(bx, by)] = t['id']
    # whitecap variants: 7 unused tiles and one new one
    nid = max(t['id'] for t in tiles) + 1
    tiles.append({**{k: v for k, v in byname['blue'].items() if k not in ('id', 'name')}, 'id': nid, 'name': 'cap_new'})
    terr += bytes(128)
    cap_id = {}
    rng = np.random.default_rng(23)
    for k, n in enumerate(CAP_TILES + ['cap_new']):
        bx, by = k % 4, k // 4
        t = next(t for t in tiles if t['name'] == n)
        t['name'] = f'cap_b{bx}{by}'
        t['palette'] = 'water'
        put(terr, t['id'], flecks(cell(blk, bx, by), rng))
        cap_id[(bx, by)] = t['id']

    # where are the other water tiles used (block position)?
    pos = {}
    for r, row in enumerate(lv['map']):
        for c, tid in enumerate(row):
            pos.setdefault(tid, Counter())[(c % 4, by_of(r))] += 1
    group = {}                                          # animation phases follow their first phase
    for a in anims['animations']:
        first = a['phases'][0]
        for ph in a['phases']:
            for k, n in enumerate(ph):
                group[n] = first[k]
    changed = []
    for t in tiles:
        name = t['name']
        if t['palette'] != 'water' or t['id'] in new_id.values() or t['id'] in cap_id.values():
            continue
        ref = byname[group.get(name, name)]['id']
        bx, by = pos[ref].most_common(1)[0][0] if ref in pos else (0, 0)
        a = untile(terr, t['id'])
        tex = calm_tex(blk, still, bx, by, t['id'])
        if name.startswith('edge'):
            b = coast(a, tex)
        elif name.startswith(('shelf', 'reef', 'bank')):
            b = np.where(np.isin(a, list(SPARKLE)), 7, a).astype(np.uint8)
        else:                                           # features in open water: background 1-5 and sparkles
            b = np.where(np.isin(a, [1, 2, 3, 4, 5] + list(SPARKLE)), tex, a).astype(np.uint8)
        if (b != a).any():
            put(terr, t['id'], b)
            changed.append(name)

    n = 0
    for r, row in enumerate(lv['map']):
        for c, tid in enumerate(row):
            if tid in is_sea:
                row[c] = new_id[(c % 4, by_of(r))]
                n += 1
    # whitecap cells. The level format allows 256 different map rows, so every different row gets a few fixed
    # whitecap variants (the frequent pure-sea rows up to MAX_VAR, the others one) within the free row budget, and
    # each map row takes one of its row's variants at random - preferably one without a whitecap next to the row
    # below.
    caps = set(cap_id.values())
    sea_ids = set(new_id.values())
    rng = np.random.default_rng(29)
    m = lv['map']
    freq = Counter(tuple(row) for row in m)
    budget = ROW_LIMIT - len(freq)
    variants = {}
    for key, cnt in freq.most_common():
        if not any(t in sea_ids for t in key):
            continue
        nv = min(MAX_VAR, 1 + budget) if cnt >= 6 else 1
        budget -= nv - 1
        vs = []
        for _ in range(nv):
            cols = []
            for c, t in enumerate(key):
                if t in sea_ids and rng.random() < CAP_SHARE and (not cols or cols[-1] < c - 1):
                    cols.append(c)
            vs.append(cols)
        variants[key] = vs
    ncap = 0
    prev = []
    for r, row in enumerate(m):
        key = tuple(row)
        if key not in variants:
            prev = []
            continue
        vs = list(variants[key])
        rng.shuffle(vs)
        cols = min(vs, key=lambda v: sum(1 for c in v for p in prev if abs(c - p) <= 1))
        for c in cols:
            row[c] = cap_id[(c % 4, by_of(r))]
        ncap += len(cols)
        prev = cols
    for t in tiles:                                     # only the whitecap tiles carry the cap indices
        if t['palette'] == 'water' and t['id'] not in caps:
            assert not np.isin(untile(terr, t['id']), [c['index'] for c in CAPS]).any(), t['name']

    anims['cycle'] = {'palette': 'water', 'first': 9, 'count': 3, 'first2': 1, 'count2': 2, 'period': 12,
                      'caps': CAPS}
    (G / 'terrain.ncm.bin').write_bytes(bytes(terr))
    (G / 'level-example.json').write_text(json.dumps(ex, indent=2) + '\n')
    (G / 'manifest.json').write_text(json.dumps(man, indent=2) + '\n')
    (G / 'animations.json').write_text(json.dumps(anims, indent=2) + '\n')
    txt = json.dumps(lv, indent=2, ensure_ascii=False)       # innermost lists on one line, as in the file
    txt = re.sub(r'\[([^\[\]{}]*)\]', lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']'
                 if m.group(1).strip() else '[]', txt)
    LEVEL.write_text(txt + '\n')
    prev = np.zeros((32, 136, 3), np.uint8)
    for y in range(32):
        for x in range(64):
            prev[y, x] = prev[y, 72 + x] = wp[blk[y, x]]
    Image.fromarray(prev).resize((136 * 4, 32 * 4), Image.NEAREST).save(G / 'sea-preview.png')
    print(f'{n} map cells renumbered ({ncap} whitecap cells); tiles redrawn: {", ".join(changed)}')


if __name__ == '__main__':
    main()
