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

# Stage 13b: own paths and formations in addition to level 1's (more variety), denser waves (harder)
PATHS3 = {
    'dive_aim':   [['move', 30, 0, 2.5], ['aim', 40, 1.75], ['fire'], ['move', 127, 0, 3], ['end']],
    'scissor':    [['move', 60, 1.75, 1.5], ['fire'], ['move', 127, 1.75, 1.5], ['end']],
    'spiral':     [['move', 30, 0, 2]] + w1.arc(2.25, 0, 540, 120) + [['fire'], ['move', 127, 0, 2.5], ['end']],
    'swirl_side': [['move', 40, 2, 0.25]] + w1.arc(2, 90, -270, 90) + [['fire'], ['move', 127, 0, 2.25], ['end']],
    'heli_pop':   [['move', 35, 0, 2], ['wait', 20], ['aim', 30, 0.5], ['fire'], ['wait', 15], ['fire'],
                   ['move', 127, 0, -1.25], ['end']],
    'heli_side':  [['move', 50, 1.5, 0.5], ['wait', 25], ['fire'], ['aim', 40, 0.75], ['fire'],
                   ['move', 127, 1.5, -0.5], ['end']],
}
FORMATIONS3 = {
    'dive6':      ('fighter', 6, 'dive_aim', 12, 48, -24),
    'scissor5':   ('fighter', 5, 'scissor', 14, -24, -24),
    'spiral5':    ('fighter', 5, 'spiral', 18, 110, -24),
    'swirl6':     ('fighter', 6, 'swirl_side', 14, -32, 40),
    'hpop3':      ('helicopter', 3, 'heli_pop', 24, 60, -24),
    'hside3':     ('helicopter', 3, 'heli_side', 26, -32, 30),
}

# (row, [(formation, mirror, x or None), ...]); quiet before the shops (188, 368) and the boss (352)
WAVES = [
    (10, [('dive6', False, None)]),
    (16, [('hpop3', False, None), ('hpop3', True, None)]),
    (22, [('scissor5', False, None), ('scissor5', True, None)]),
    (29, [('spiral5', False, None)]),
    (35, [('hside3', False, None), ('side6', True, None)]),
    (41, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120)]),
    (47, [('swirl6', False, None), ('swirl6', True, None)]),
    (54, [('ring5', False, None), ('dive6', True, None)]),
    (61, [('snake8', False, None), ('hpop3', True, None)]),
    (68, [('scissor5', True, None), ('strafe5', False, None)]),
    (75, [('loop6', False, None), ('loop6', True, None)]),
    (82, [('hside3', False, None), ('hside3', True, None)]),
    (88, [('spiral5', True, None), ('zigzag6', False, None)]),
    # oil field (96-183)
    (95, [('dive6', False, None), ('dive6', True, None)]),
    (102, [('hover4', False, None), ('swirl6', True, None)]),
    (109, [('swoop8', False, None), ('hpop3', True, None)]),
    (116, [('scissor5', False, None), ('scissor5', True, None)]),
    (123, [('ring5', True, None), ('side6', False, None)]),
    (130, [('v_lead', False, 60), ('v_wing', False, 28), ('v_lead', True, 60), ('v_wing', True, 28)]),
    (137, [('spiral5', False, None), ('hside3', True, None)]),
    (144, [('uturn6', False, None), ('uturn6', True, None)]),
    (151, [('hpop3', False, None), ('dive6', True, None)]),
    (158, [('swirl6', False, None), ('snake8', True, None)]),
    (165, [('hover4', False, None), ('hover4', True, None)]),
    (172, [('strafe5', False, None), ('strafe5', True, None), ('dive6', False, None)]),
    # mid shop at row 188; research platforms and wind farm (184-279)
    (196, [('scissor5', False, None), ('scissor5', True, None)]),
    (203, [('hside3', False, None), ('ring5', True, None)]),
    (210, [('spiral5', False, None), ('spiral5', True, None)]),
    (217, [('dive6', False, None), ('hpop3', True, None)]),
    (224, [('swirl6', False, None), ('swirl6', True, None)]),
    (231, [('zigzag6', False, None), ('hside3', True, None)]),
    (238, [('v_lead', False, None), ('v_wing', False, 120), ('v_wing', True, 120), ('hpop3', False, None)]),
    (245, [('loop6', False, None), ('dive6', True, None)]),
    (252, [('hover4', False, None), ('hover4', True, None), ('strafe5', False, None)]),
    (259, [('scissor5', True, None), ('spiral5', False, None)]),
    (266, [('swoop8', False, None), ('hside3', True, None)]),
    (273, [('dive6', False, None), ('dive6', True, None)]),
    # naval base (280-374)
    (280, [('swirl6', False, None), ('hpop3', True, None)]),
    (287, [('ring5', False, None), ('ring5', True, None)]),
    (294, [('scissor5', False, None), ('scissor5', True, None), ('hside3', False, None)]),
    (301, [('spiral5', False, None), ('dive6', True, None)]),
    (308, [('uturn6', False, None), ('uturn6', True, None)]),
    (315, [('hpop3', False, None), ('hpop3', True, None), ('strafe5', False, None)]),
    (322, [('swirl6', True, None), ('snake8', False, None)]),
    (329, [('dive6', False, None), ('dive6', True, None)]),
    (336, [('hside3', False, None), ('hside3', True, None), ('zigzag6', False, None)]),
    # boss at row 352
]

# (row, kind, size in px (w, h), directions)
SHIPS = [(r, 'speedboat', (16, 16), ['east', 'west', 'south']) for r in
         (14, 26, 38, 50, 62, 74, 86, 100, 112, 124, 136, 148, 160, 172, 198, 210, 222, 234, 246, 258, 270,
          286, 298, 310, 322, 334, 344)] + \
        [(r, 'patrol_boat', (32, 32), ['south', 'east', 'west']) for r in
         (32, 58, 80, 104, 128, 152, 176, 206, 230, 254, 278, 302, 326)] + \
        [(r, 'frigate', (32, 64), ['south']) for r in (70, 118, 166, 216, 262, 296, 332)]

GUN_ROWS = [(r, k) for r in range(18, 350, 9) for k in (('heavy_flak' if r % 4 == 0 else 'flak'),)]


def main():
    w1.PATHS.update(PATHS3)
    w1.FORMATIONS.update(FORMATIONS3)
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
