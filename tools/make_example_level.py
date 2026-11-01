#!/usr/bin/env python3
"""Write levels/level01.json: a 4-minute test level in the JSON level format.

The map repeats the example landscape of artwork v2 (PR #4); the events recreate and extend the
Stage 2 test waves with paths, formations, tanks, the two shops and the level end. A real level is
expected to be written by hand or by ChatGPT following docs/level_json.md.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows_top_down = json.loads((ROOT / 'assets/art/spec-v2/generated/level-example.json').read_text())['rows']
rng = random.Random(65)

paths = {
    'snake':      [['sine', 48, 128, 3, 1], ['end']],
    'snake_fast': [['sine', 32, 64, 4, 1.5], ['end']],
    'dive':       [['move', 48, 0, 1.5], ['aim', 40, 1], ['fire'], ['move', 127, 0, 2.5], ['end']],
    'swoop':      [['move', 40, 0, 2], ['move', 24, 1, 1.5], ['move', 24, 2, 0.5], ['fire'],
                   ['move', 60, 2, -0.25], ['end']],
    'zigzag':     [['loop', 4], ['move', 24, 1.5, 1], ['move', 24, -1.5, 1], ['endloop'], ['end']],
    'bomber':     [['loop', 3], ['move', 60, 0, 0.75], ['fire'], ['endloop'], ['move', 127, 0, 1], ['end']],
    'hover':      [['move', 50, 0, 1.5], ['wait', 40], ['fire'], ['wait', 30], ['aim', 60, 1.5], ['move', 127, 0, 2], ['end']],
}
formations = {
    'fighters_snake':  {'enemy': 'fighter', 'count': 6, 'path': 'snake', 'delay': 20, 'x': 120},
    'fighters_swoop':  {'enemy': 'fighter', 'count': 5, 'path': 'swoop', 'delay': 14, 'x': 24},
    'fighters_dive':   {'enemy': 'fighter', 'count': 4, 'path': 'dive', 'delay': 24, 'x': 150},
    'helis_zigzag':    {'enemy': 'helicopter', 'count': 6, 'path': 'zigzag', 'delay': 18, 'x': 100},
    'helis_hover':     {'enemy': 'helicopter', 'count': 3, 'path': 'hover', 'delay': 30, 'x': 200},
    'bombers':         {'enemy': 'bomber', 'count': 3, 'path': 'bomber', 'delay': 40, 'x': 140},
    'armoured':        {'enemy': 'armoured', 'count': 3, 'path': 'snake_fast', 'delay': 36, 'x': 140},
}
order = ['fighters_snake', 'helis_zigzag', 'fighters_swoop', 'bombers', 'fighters_dive',
         'helis_hover', 'armoured', 'fighters_swoop']
events = []
repeats = 12                      # 12 x 32 rows = 384 rows = 6144 px = about 4 minutes
nrows = repeats * len(rows_top_down)
row, k = 6, 0
while row < nrows - 12:
    f = order[k % len(order)]
    ev = {'row': row, 'type': 'formation', 'formation': f}
    if f == 'fighters_swoop' and (k // len(order)) % 2:
        ev['mirror'] = True
    if f in ('fighters_snake', 'bombers', 'armoured'):
        ev['x'] = rng.randrange(60, 200)
    events.append(ev)
    if k % 2 == 0:
        events.append({'row': row + 3, 'type': 'ground', 'enemy': 'tank', 'x': rng.randrange(120, 290, 2),
                       'dir': rng.choice(['south', 'west', 'east'])})
    row += 9 if f in ('bombers', 'armoured') else 7
    k += 1
mid = nrows // 2
events.append({'row': mid, 'type': 'shop', 'id': 'mid'})
events.append({'row': nrows - 8, 'type': 'shop', 'id': 'end'})
events.append({'row': nrows, 'type': 'end'})
events.sort(key=lambda e: e['row'])

level = {
    'format': 'shootermega65-level-1',
    'name': 'Level 1 (test)',
    'tileset': 'assets/art/spec-v2/generated',
    'scroll_speed': 0.5,
    'map': [{'repeat': repeats, 'rows': list(reversed(rows_top_down))}],
    'paths': paths,
    'formations': formations,
    'events': events,
}
out = ROOT / 'levels/level01.json'
out.parent.mkdir(exist_ok=True)
text = json.dumps(level, indent=1)
out.write_text(text + '\n')
print(f'{out}: {nrows} rows, {len(events)} events')
