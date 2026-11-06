#!/usr/bin/env python3
"""Stage 13: enemy waves of level 3 "Operation Offshore" (levels/level3.json, map by ChatGPT, PR #22).

Air: the fighter and helicopter formations of level 1 (tools/design_waves_l1.py), shown as seaplanes and navy
helicopters by the level-3 enemy set. Bomber and armoured-plane formations are not used: their slots hold the
patrol boat and the frigate. Sea: speedboats, patrol boats and frigates as ground events on open water; guns on
islands and platforms. The map, the shops, the boss and the level end stay as they are.

    python3 tools/design_waves_l3.py            # rewrites levels/level3.json
"""
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_waves_l1 as w1  # noqa: E402

LEVEL = w1.ROOT / 'levels/level3.json'

# (row, [(formation, mirror, x or None), ...]); quiet before the shops (188, 368) and the boss (352)
WAVES = [
    (12, [('side6', False, None)]),
    (20, [('hover4', False, None)]),
    (28, [('snake8', False, None)]),
    (37, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120)]),
    (46, [('ring5', False, None)]),
    (55, [('loop6', False, None), ('loop6', True, None)]),
    (64, [('hover4', False, None), ('hover4', True, None)]),
    (73, [('strafe5', False, None), ('strafe5', True, None)]),
    (82, [('uturn6', False, None)]),
    # oil field (96-183)
    (94, [('zigzag6', False, None), ('zigzag6', True, None)]),
    (103, [('ring5', True, None)]),
    (112, [('swoop8', False, None)]),
    (121, [('hover4', False, None), ('side6', True, None)]),
    (130, [('v_lead', False, 60), ('v_wing', False, 28), ('v_lead', True, 60), ('v_wing', True, 28)]),
    (140, [('loop6', False, None), ('ring5', False, None)]),
    (150, [('snake8', True, None)]),
    (160, [('hover4', False, None), ('hover4', True, None)]),
    (170, [('strafe5', False, None), ('strafe5', True, None)]),
    # mid shop at row 188; research platforms and wind farm (184-279)
    (198, [('swoop6', False, None), ('swoop6', True, None)]),
    (207, [('ring5', False, None), ('ring5', True, None)]),
    (216, [('uturn6', False, None), ('uturn6', True, None)]),
    (225, [('side6', False, None), ('hover4', True, None)]),
    (234, [('zigzag6', False, None), ('zigzag6', True, None)]),
    (243, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120)]),
    (252, [('loop6', False, None), ('loop6', True, None)]),
    (261, [('hover4', False, None), ('ring5', True, None)]),
    (270, [('snake8', False, None)]),
    # naval base (280-374)
    (282, [('strafe5', False, None), ('strafe5', True, None)]),
    (291, [('ring5', False, None), ('hover4', True, None)]),
    (300, [('swoop8', False, None)]),
    (309, [('side6', False, None), ('side6', True, None)]),
    (318, [('uturn6', False, None), ('uturn6', True, None)]),
    (327, [('hover4', False, None), ('hover4', True, None)]),
    (336, [('zigzag6', False, None)]),
    # boss at row 352
]

# (row, kind, size in px (w, h), directions)
SHIPS = [(r, 'speedboat', (16, 16), ['east', 'west', 'south']) for r in
         (16, 33, 50, 68, 86, 105, 125, 145, 165, 200, 218, 238, 258, 276, 296, 314, 332, 344)] + \
        [(r, 'patrol_boat', (32, 32), ['south', 'east', 'west']) for r in
         (42, 78, 116, 156, 210, 248, 288, 322)] + \
        [(r, 'frigate', (32, 64), ['south']) for r in (100, 174, 230, 306, 338)]

GUN_ROWS = [(24, 'flak'), (60, 'flak'), (98, 'heavy_flak'), (118, 'flak'), (136, 'flak'), (152, 'heavy_flak'),
            (176, 'flak'), (204, 'flak'), (222, 'heavy_flak'), (244, 'flak'), (264, 'flak'), (286, 'heavy_flak'),
            (298, 'flak'), (312, 'heavy_flak'), (326, 'flak'), (340, 'heavy_flak')]


def main():
    w1.design(LEVEL, WAVES, [], GUN_ROWS)
    lv = json.loads(LEVEL.read_text())
    tiles = json.loads((w1.ROOT / lv['tileset'] / 'level-example.json').read_text())['tiles']
    water = {t['id'] for t in tiles if t['palette'] == 'water'}
    rows = []
    for e in lv['map']:
        rows += e['rows'] * e['repeat'] if isinstance(e, dict) else [e]
    rnd = random.Random(13)
    events = lv['events']
    for row, kind, (w, h), dirs in SHIPS:
        # open water under the whole hull for the rows it appears in and a little below (map row = top edge)
        cand = [x for x in range(16, 305 - w, 8)
                if all(rows[r][c] in water
                       for r in range(max(0, row - h // 16 - 3), row + 1)
                       for c in range((x + 16) >> 4, ((x + 15 + w) >> 4) + 1))]
        if cand:
            events.append({'row': row, 'type': 'ground', 'enemy': kind, 'x': rnd.choice(cand),
                           'dir': rnd.choice(dirs)})
        else:
            print(f'row {row}: no open water for a {kind}')
    order = {'speed': 0, 'formation': 1, 'ground': 2, 'boss': 3, 'shop': 4, 'end': 5}
    events.sort(key=lambda e: (e['row'], order[e['type']]))
    text = json.dumps(lv, indent=2)          # as design_waves_l1: innermost lists on one line
    text = re.sub(r'\[([^\[\]{}]*)\]', lambda m: '[' + ', '.join(t.strip() for t in m[1].split(',')) + ']'
                  if m[1].strip() else '[]', text)
    LEVEL.write_text(text + '\n')
    n = {k: sum(e.get('enemy') == k for e in events) for k in ('speedboat', 'patrol_boat', 'frigate')}
    print(f'level3.json: ships {n}')


if __name__ == '__main__':
    sys.exit(main())
