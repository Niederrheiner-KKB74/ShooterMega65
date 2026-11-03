#!/usr/bin/env python3
"""Stage 7c: enemy waves of level 1 (levels/coastal_base.json).

Rewrites only "paths", "formations" and the formation / ground events. The map, the shops, the boss and the
level end stay as they are. Run again after changing this file:

    python3 tools/design_waves_l1.py            # rewrites levels/coastal_base.json

Ideas: loops and U-turns, enemies entering from the sides, pincers (a formation and its mirror image in the
same row), V groups, helicopters that hover and shoot, bombers crossing diagonally, armoured planes that stop
and fire. Tanks start on land at varied places (the converter checks it) and avoid water while driving.
"""
import json
import math
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVEL = ROOT / 'levels/coastal_base.json'


def q(v):
    """Speeds are multiples of 0.25 px/frame."""
    return round(v * 4) / 4


def arc(speed, start_deg, sweep_deg, frames, seg=6):
    """Moves along a circular arc: the velocity turns from start_deg by sweep_deg (0 = down, 90 = right,
    -90 = left, 180 = up; positive sweep turns counter-clockwise on screen, i.e. down -> right -> up)."""
    out = []
    n = max(1, round(frames / seg))
    for k in range(n):
        a = math.radians(start_deg + sweep_deg * (k + 0.5) / n)
        out.append(['move', seg, q(speed * math.sin(a)), q(speed * math.cos(a))])
    return out


PATHS = {
    # fighters
    'swoop':      [['move', 40, 0, 2], ['move', 40, 1, 1.5], ['fire'], ['move', 80, 0.5, 2.5], ['end']],
    'snake':      [['sine', 40, 96, 2, 1.25], ['fire'], ['sine', 40, 96, 1, 1.75], ['end']],
    'loop':       [['move', 48, 0, 2]] + arc(2, 0, 360, 96) + [['fire'], ['move', 127, 0, 2.5], ['end']],
    'u_turn':     [['move', 50, 0, 2.5], ['fire']] + arc(2.5, 0, 180, 48) + [['move', 127, 0, -2.5], ['end']],
    'side_in':    [['move', 30, 2, 0.5]] + arc(2, 90, -90, 30) + [['fire'], ['move', 127, 0, 2], ['end']],
    'zigzag':     [['move', 30, 1.5, 1.5], ['move', 30, -1.5, 1.5], ['fire'], ['move', 30, 1.5, 1.5],
                   ['move', 30, -1.5, 1.5], ['move', 127, 0, 2], ['end']],
    'strafe':     [['move', 127, 2.25, 0.25], ['end']],
    'v_dive':     [['move', 36, 0, 1.5], ['aim', 50, 1], ['fire'], ['move', 127, 0, 3], ['end']],
    # helicopters
    'hover':      [['move', 50, 0, 1.5], ['wait', 30], ['fire'], ['aim', 60, 0.75], ['fire'], ['wait', 20],
                   ['move', 127, -1.5, 0.5], ['end']],
    'heli_ring':  [['move', 40, 0, 1.5]] + arc(1.5, 0, 270, 120) + [['fire'], ['wait', 20],
                   ['move', 127, 0, 1.5], ['end']],
    # bombers
    'cross':      [['move', 127, 1.25, 1], ['fire'], ['move', 127, 1.25, 1], ['end']],
    'weave':      [['move', 60, 0, 1], ['move', 50, 1, 0.75], ['fire'], ['move', 60, -1, 0.75],
                   ['move', 127, 0, 1.25], ['end']],
    # armoured planes
    'stop_fire':  [['move', 70, 0, 1], ['wait', 30], ['fire'], ['wait', 40], ['fire'], ['move', 60, 0.75, 0.5],
                   ['fire'], ['move', 127, 0, 1.5], ['end']],
    'sweep':      [['move', 80, 0, 0.75], ['fire'], ['move', 64, 1.25, 0.5], ['fire'], ['move', 96, -1.25, 0.5],
                   ['move', 127, 0, 1.5], ['end']],
}

# name: enemy, count, path, delay, x, y
FORMATIONS = {
    'swoop8':     ('fighter', 8, 'swoop', 14, 40, -24),
    'swoop6':     ('fighter', 6, 'swoop', 14, 40, -24),
    'snake8':     ('fighter', 8, 'snake', 14, 136, -24),
    'loop6':      ('fighter', 6, 'loop', 16, 70, -24),
    'uturn6':     ('fighter', 6, 'u_turn', 12, 100, -24),
    'side6':      ('fighter', 6, 'side_in', 14, -32, 24),
    'zigzag6':    ('fighter', 6, 'zigzag', 16, 60, -24),
    'strafe5':    ('fighter', 5, 'strafe', 18, -32, 8),
    'v_lead':     ('fighter', 1, 'v_dive', 0, 152, -24),
    'v_wing':     ('fighter', 2, 'v_dive', 16, 0, -40),
    'hover4':     ('helicopter', 4, 'hover', 28, 60, -24),
    'ring5':      ('helicopter', 5, 'heli_ring', 22, 120, -24),
    'cross4':     ('bomber', 4, 'cross', 32, -24, -40),
    'weave4':     ('bomber', 4, 'weave', 30, 140, -40),
    'stop3':      ('armoured', 3, 'stop_fire', 40, 80, -40),
    'sweep3':     ('armoured', 3, 'sweep', 36, 144, -40),
}

# rows of the waves: (row, [(formation, mirror, x or None), ...]); quiet before the shops and the boss
WAVES = [
    (16, [('swoop8', False, None)]),
    (24, [('swoop8', True, None)]),
    (32, [('snake8', False, None)]),
    (40, [('side6', False, None)]),
    (47, [('cross4', False, None)]),
    (55, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120)]),
    (62, [('loop6', False, None)]),
    (70, [('hover4', False, None), ('hover4', True, None)]),
    (79, [('uturn6', False, None)]),
    (86, [('side6', True, None)]),
    (93, [('weave4', True, None)]),
    (100, [('zigzag6', False, None), ('zigzag6', True, None)]),
    (109, [('ring5', False, None)]),
    (117, [('strafe5', False, None)]),
    (122, [('loop6', True, None)]),
    (130, [('stop3', False, None)]),
    (138, [('swoop6', False, None), ('swoop6', True, None)]),
    (147, [('cross4', True, None)]),
    (154, [('v_lead', False, 60), ('v_wing', False, 28), ('v_lead', True, 60), ('v_wing', True, 28)]),
    (162, [('uturn6', True, None)]),
    (170, [('hover4', False, None)]),
    # mid shop at row 188
    (198, [('snake8', True, None)]),
    (205, [('sweep3', False, None)]),
    (212, [('side6', False, None), ('side6', True, None)]),
    (221, [('loop6', False, None)]),
    (228, [('ring5', True, None)]),
    (236, [('cross4', False, None), ('cross4', True, None)]),
    (245, [('zigzag6', False, None)]),
    (251, [('strafe5', True, None)]),
    (257, [('stop3', True, None)]),
    (265, [('uturn6', False, None), ('uturn6', True, None)]),
    (274, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120)]),
    (281, [('hover4', False, None), ('hover4', True, None)]),
    (290, [('loop6', True, None)]),
    (297, [('weave4', False, None)]),
    (304, [('swoop6', False, None), ('swoop6', True, None)]),
    (313, [('sweep3', True, None)]),
    (320, [('side6', True, None)]),
    (327, [('ring5', False, None)]),
    (335, [('snake8', False, None)]),
    (342, [('stop3', False, None), ('strafe5', False, None)]),
    # boss at row 358
]

# tank rows; x is picked on land (seeded, reproducible)
TANK_ROWS = [28, 44, 58, 66, 84, 97, 112, 126, 134, 150, 158, 166, 202, 216, 232, 248, 260, 270, 286, 300,
             316, 330, 344]

# ground guns (Stage 8): (row, kind); x on land, not on a destroyable building (seeded, reproducible)
GUN_ROWS = [(36, 'flak'), (74, 'flak'), (104, 'flak'), (118, 'flak'), (142, 'flak'), (162, 'heavy_flak'),
            (200, 'flak'), (210, 'flak'), (226, 'heavy_flak'), (240, 'flak'), (254, 'flak'), (266, 'heavy_flak'),
            (282, 'flak'), (292, 'heavy_flak'), (306, 'flak'), (318, 'flak'), (326, 'heavy_flak'), (338, 'flak'),
            (348, 'heavy_flak')]


def main():
    design(LEVEL, WAVES, TANK_ROWS, GUN_ROWS)


def design(level, waves, tank_rows, gun_rows):
    """Rewrite paths, formations and the formation / ground events of the level JSON `level` (Path)."""
    lv = json.loads(level.read_text())
    tiles = json.loads((ROOT / lv['tileset'] / 'level-example.json').read_text())['tiles']
    water = {t['id'] for t in tiles if t['palette'] == 'water'}
    rows = []
    for e in lv['map']:
        rows += e['rows'] * e['repeat'] if isinstance(e, dict) else [e]

    rnd = random.Random(7)
    events = [e for e in lv['events'] if e['type'] not in ('formation', 'ground')]
    for row, group in waves:
        for name, mirror, x in group:
            ev = {'row': row, 'type': 'formation', 'formation': name, 'mirror': mirror}
            if x is not None:
                ev['x'] = x
            events.append(ev)
    dirs = ['north', 'east', 'south', 'west']
    for row in tank_rows:
        # land columns in this row and the next two (the tank appears at the top edge)
        cand = [x for x in range(16, 289, 8)
                if all(rows[r][c] not in water
                       for r in range(row, min(row + 3, len(rows)))
                       for c in {(x + 16) >> 4, (x + 31) >> 4})]
        if not cand:
            continue
        events.append({'row': row, 'type': 'ground', 'enemy': 'tank', 'x': rnd.choice(cand),
                       'dir': rnd.choice(dirs)})
    gt = json.loads((ROOT / lv['ground_targets'] / 'ground-targets.json').read_text())
    by_name = {t['name']: t['id'] for t in tiles}
    buildings = {by_name[d['of']] for d in gt['destroyed_tiles']}
    grnd = random.Random(11)
    for row, kind in gun_rows:
        w = 32 if kind == 'heavy_flak' else 16
        cand = [x for x in range(16, 305 - w, 8)
                if all(rows[r][c] not in water and rows[r][c] not in buildings
                       for r in range(row, min(row + 4, len(rows)))
                       for c in {(x + 16) >> 4, (x + 15 + w) >> 4})]
        if cand:
            events.append({'row': row, 'type': 'ground', 'enemy': kind, 'x': grnd.choice(cand)})
    order = {'speed': 0, 'formation': 1, 'ground': 2, 'boss': 3, 'shop': 4, 'end': 5}
    events.sort(key=lambda e: (e['row'], order[e['type']]))
    lv['paths'] = PATHS
    lv['formations'] = {n: {'enemy': f[0], 'count': f[1], 'path': f[2], 'delay': f[3], 'x': f[4], 'y': f[5]}
                        for n, f in FORMATIONS.items()}
    lv['events'] = events
    text = json.dumps(lv, indent=2)          # innermost lists (map rows, path commands) on one line
    text = re.sub(r'\[([^\[\]{}]*)\]', lambda m: '[' + ', '.join(t.strip() for t in m[1].split(',')) + ']'
                  if m[1].strip() else '[]', text)
    level.write_text(text + '\n')
    n_form = sum(e['type'] == 'formation' for e in events)
    n_tank = sum(e['type'] == 'ground' and e['enemy'] == 'tank' for e in events)
    n_gun = sum(e['type'] == 'ground' and e['enemy'] != 'tank' for e in events)
    print(f'{level.name}: {len(PATHS)} paths, {len(FORMATIONS)} formations, {n_form} formation events, '
          f'{n_tank} tanks, {n_gun} guns')


if __name__ == '__main__':
    sys.exit(main())
