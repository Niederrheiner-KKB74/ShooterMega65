#!/usr/bin/env python3
"""Stage 9: palms along the river and around the oasis of level 2 (levels/level2.json, owner's request).

Puts the palm tiles of the level-2 tileset (palm0-palm3) on plain sand and dunes next to water (any of the 8
neighbours in the palette `water`, fewer two steps away). Rows whose pattern occurs only once in the map are decorated first (no new row
patterns); rows that share their pattern only while the limit of 256 different rows allows. Deterministic, can
be run again (palms are not plain sand, so nothing is placed twice). Run it after every new map from ChatGPT:

    python3 tools/decorate_level2.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVEL = ROOT / 'levels/level2.json'
PLAIN_SAND = ('sand0', 'sand1', 'sand2', 'sand3', 'sand4', 'sand5', 'sand9', 'sand10', 'sand11')   # plain sand and dunes
PALMS = ('palm0', 'palm1', 'palm2', 'palm3')
DENSITY = 9          # out of 16 cells next to water get a palm
DENSITY2 = 4         # out of 16 cells two steps from the water
MAX_ROWS = 256


def h(r, c):
    return (r * 7919 + c * 104729 + 12345) * 2654435761 % 2 ** 32


def main():
    lv = json.loads(LEVEL.read_text())
    tiles = json.loads((ROOT / lv['tileset'] / 'level-example.json').read_text())['tiles']
    tid = {t['name']: t['id'] for t in tiles}
    water = {t['id'] for t in tiles if t['palette'] == 'water'}
    sand = {tid[n] for n in PLAIN_SAND}
    palms = [tid[n] for n in PALMS]
    rows = []
    for e in lv['map']:
        rows += [list(x) for x in e['rows']] * e['repeat'] if isinstance(e, dict) else [list(e)]
    before = len({tuple(r) for r in rows})

    def decorated(r):
        new = list(rows[r])
        for c in range(1, 21):
            if new[c] not in sand:
                continue
            def near(d):
                return any(rows[rr][cc] in water for rr in range(r - d, r + d + 1)
                           for cc in range(c - d, c + d + 1) if 0 <= rr < len(rows) and 0 <= cc < 21)
            if (near(1) and h(r, c) % 16 < DENSITY) or (near(2) and h(r, c) % 16 < DENSITY2):
                new[c] = palms[h(c, r) % 4]
        return new

    count = Counter(tuple(r) for r in rows)
    changed = 0
    for unique_first in (True, False):
        for r in range(len(rows)):
            if (count[tuple(rows[r])] == 1) != unique_first:
                continue
            new = decorated(r)
            if new == rows[r]:
                continue
            old = tuple(rows[r])
            trial = count.copy()
            trial[old] -= 1
            if trial[old] == 0:
                del trial[old]
            trial[tuple(new)] += 1
            if len(trial) > MAX_ROWS:
                continue
            count = trial
            rows[r] = new
            changed += 1
    lv['map'] = rows
    text = json.dumps(lv, indent=2)
    text = re.sub(r'\[([^\[\]{}]*)\]', lambda m: '[' + ', '.join(t.strip() for t in m[1].split(',')) + ']'
                  if m[1].strip() else '[]', text)
    LEVEL.write_text(text + '\n')
    palms_n = sum(t in palms for r in rows for t in r)
    print(f'{LEVEL.name}: {changed} rows with new palms, {palms_n} palms in total, '
          f'different rows {before} -> {len(count)} (max {MAX_ROWS})')


if __name__ == '__main__':
    sys.exit(main())
