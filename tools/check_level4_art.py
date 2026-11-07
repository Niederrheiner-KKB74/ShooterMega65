#!/usr/bin/env python3
"""Check the level-4 delivery (city tileset with animations, destroyed buildings, level map, enemy set, mech boss)
before a pull request: docs/chatgpt_level4.md.

    python3 tools/check_level4_art.py

Errors must be fixed; notes should be looked at. Exit code 1 if there are errors.
Needs Python 3 with numpy and Pillow (as the rest of tools/).
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_level         # noqa: E402
import check_level2_art as c2   # noqa: E402  (shared helpers: load, hexrows, tiles, destroyed tiles)

TILES = ROOT / 'assets/art/level4/generated'
ENEMIES = ROOT / 'assets/art/enemies-level4/generated'
BOSS = ROOT / 'assets/art/boss-level4/generated'
LEVEL = ROOT / 'levels/level4.json'
MAX_ROWS = 256                  # different map rows
BOSS_ROOM = 324                 # glyphs of the aircraft area (the boss is swapped in there)
ENEMY_ROOM = 324                # level enemy set: the same aircraft area ...
BOAT_ROOM = 48                  # ... plus the tank area for the speedboat
MAX_ANIMS = 8
MAX_ANIM_SLOTS = 24             # map tiles that are animated (phase 0), all animations together
DIR8 = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']
DIR4 = ['north', 'east', 'south', 'west']
TURRETS = ['nw', 'ne', 'sw', 'se']

c2.TILES = TILES
c2.PALETTES = ('streets', 'ruins', 'buildings', 'fixed_targets')   # Stage 14: names of the city palettes
c2.MAX_TILES = 126              # 4 + 192 + 126 * 128 bytes fit the 16 KB of L3GFX
err, note, load, hexrows, glyphs = c2.err, c2.note, c2.load, c2.hexrows, c2.glyphs


def rel(p):
    return p.relative_to(ROOT)


def check_animations(by_name):
    an = load(TILES / 'animations.json', 'tile animations')
    if an is None:
        return None
    anims = an.get('animations', [])
    if not 1 <= len(anims) <= MAX_ANIMS:
        err(f'animations.json: 1 to {MAX_ANIMS} animations')
    slots, used = 0, set()
    for i, a in enumerate(anims):
        w = f'animation {a.get("name", i)}'
        ph = a.get('phases', [])
        if not 2 <= len(ph) <= 4:
            err(f'{w}: 2 to 4 phases')
            continue
        if len({len(p) for p in ph}) != 1 or not ph[0]:
            err(f'{w}: every phase lists the same number of tiles')
            continue
        if not 4 <= a.get('period', 0) <= 32:
            err(f'{w}: "period" (frames per phase) 4 to 32')
        for p in ph:
            for t in p:
                if t not in by_name:
                    err(f'{w}: tile {t} is not in level-example.json')
                elif t in used:
                    err(f'{w}: tile {t} is used by two animations or twice')
                used.add(t)
        for k in range(len(ph[0])):
            pals = {by_name[p[k]]['palette'] for p in ph if p[k] in by_name}
            if len(pals) > 1:
                err(f'{w}: tile {k} changes its palette between phases ({sorted(pals)})')
        slots += len(ph[0])
    cy = an.get('cycle')            # optional colour cycling (fire glow, lights)
    if cy is None:
        note('animations.json: no "cycle" (colour cycling, optional)')
    elif cy.get('palette') not in ('streets', 'ruins', 'buildings') or not (1 <= cy.get('first', 0) and cy.get('first', 0) + cy.get('count', 0) <= 16
                                              and 3 <= cy.get('count', 0) <= 6 and 2 <= cy.get('period', 0) <= 32):
        err(f'animations.json "cycle" {cy}: palette streets/ruins/buildings, first >= 1, 3-6 colours, period 2-32')
    else:
        note(f'colour cycling: {cy["palette"]} indices {cy["first"]}-{cy["first"] + cy["count"] - 1}, every {cy["period"]} frames')
    if slots > MAX_ANIM_SLOTS:
        err(f'animations: {slots} animated map tiles, at most {MAX_ANIM_SLOTS}')
    note(f'animations: {len(anims)}, {slots} animated map tiles (max {MAX_ANIM_SLOTS})')
    return {t for a in anims for p in a.get('phases', [])[1:] for t in p}, \
        {t for a in anims for p in a.get('phases', []) for t in p}


def check_level(later_phases, animated):
    lv = load(LEVEL, 'level')
    if lv is None:
        return
    for key in ('tileset', 'ground_targets'):
        if lv.get(key) != 'assets/art/level4/generated':
            err(f'levels/level4.json: "{key}" must be "assets/art/level4/generated"')
    names = [t['name'] for t in json.loads((TILES / 'level-example.json').read_text())['tiles']]
    rows = []
    for e in lv.get('map', []):
        rows += [tuple(x) for x in e['rows']] * e['repeat'] if isinstance(e, dict) else [tuple(e)]
    if len(set(rows)) > MAX_ROWS:
        err(f'levels/level4.json: {len(set(rows))} different map rows, at most {MAX_ROWS}')
    late = {names.index(n) for n in later_phases if n in names}
    if any(t in late for r in rows for t in r):
        err('levels/level4.json: the map uses tiles of animation phases 2-4; use the phase-1 tile only')
    gt = load(TILES / 'ground-targets.json', 'destroyed tiles') or {}
    dest = {d.get('of') for d in gt.get('destroyed_tiles', [])}
    if dest & animated:
        err(f'animated tiles cannot be destroyable: {sorted(dest & animated)}')
    types = [e.get('type') for e in lv.get('events', [])]
    for t, n in (('shop', 2), ('boss', 1), ('end', 1)):
        if types.count(t) != n:
            err(f'levels/level4.json: needs {n} "{t}" event(s), has {types.count(t)}')
    for e in lv.get('events', []):
        if e.get('type') == 'ground' and e.get('enemy') == 'tank':
            err(f'levels/level4.json row {e.get("row")}: no tanks in level 4 (mechs are placed by Claude)')
    if lv.get('formations') or lv.get('paths'):
        note('levels/level4.json: formations and paths are made by Claude; they will be replaced')
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _, _, report = build_level.build(LEVEL, tmp, 'L4')
            for line in report:
                print('level:', line)
        except build_level.LevelError as e:
            err(f'levels/level4.json: {e}')
        except Exception as e:                  # noqa: BLE001 - report anything the converter trips over
            err(f'levels/level4.json: converter failed: {type(e).__name__}: {e}')


ENEMY_SET = (
    # group, poses, phases, size, palette, area
    # fighter slots: the level-1 fighters (Stage 14b, 72 glyphs, counted below)
    ('drone', ['straight', 'left', 'right'], 3, (32, 32), 'drone', 'aircraft'),   # bomber slots, 32x32 (Stage 14b)
    ('attack_heli', DIR8, 3, (16, 16), 'heli', 'aircraft'),         # helicopter slots
    ('walker', ['south'], 4, (32, 32), 'mechs', 'aircraft'),      # Stage 14d: 4 steps (Claude)        # armoured-plane slots
    ('walker', ['destroyed'], 1, (32, 32), 'mechs', 'aircraft'),
    ('mech', DIR4, 4, (16, 16), 'mechs', 'boat'),                   # tank slots
)


def check_enemies():
    src = load(ENEMIES / 'indexed-source.json', 'enemy set')
    pal = load(ENEMIES / 'palettes.json', 'enemy set')
    pl = load(ENEMIES / 'placement.json', 'enemy set')
    if pal is not None:
        for p in ('drone', 'heli', 'mechs'):
            if p not in pal or len(pal[p]) != 16:
                err(f'enemies palettes.json: palette "{p}" with exactly 16 entries [R,G,B] missing')
    if src is None:
        return
    have = {(f.get('group'), f.get('pose'), f.get('phase')): f for f in src}
    room = {'aircraft': 0, 'boat': 0}
    want = set()
    for group, poses, phases, (w, h), p, area in ENEMY_SET:
        for pose in poses:
            for n in range(phases):
                key = (group, pose, n)
                want.add(key)
                f = have.get(key)
                where = f'enemy {group} {pose} phase {n}'
                if f is None:
                    err(f'{where}: missing')
                    continue
                if (f.get('width'), f.get('height')) != (w, h):
                    err(f'{where}: must be {w}x{h}')
                    continue
                if f.get('palette') != p:
                    err(f'{where}: palette must be "{p}"')
                hexrows(where, f.get('rows'), w, h, 2)
                room[area] += glyphs(w, h)
    for key in set(have) - want:
        err(f'enemy set: unexpected frame {key} (group, pose, phase)')
    room['aircraft'] += 1 + 72          # + the level-1 fighters in the fighter slots
    if room['aircraft'] > ENEMY_ROOM:
        err(f'enemy set: {room["aircraft"]} glyphs in the aircraft area, room for {ENEMY_ROOM}')
    if room['boat'] > BOAT_ROOM:
        err(f'enemy set: mechs {room["boat"]} glyphs, room for {BOAT_ROOM}')
    note(f'enemy set: aircraft area {room["aircraft"]} of {ENEMY_ROOM} glyphs, mechs {room["boat"]} of '
         f'{BOAT_ROOM}')
    if pl is None:
        return
    for ship, n, (w, h) in (('walker', 1, (32, 32)),):
        g = pl.get(ship, {}).get('guns', [])
        if len(g) != n:
            err(f'enemies placement.json: "{ship}" needs "guns" with {n} offset [x, y]')
        for o in g:
            if not (0 <= o[0] <= w - 16 and 0 <= o[1] <= h - 16):
                err(f'enemies placement.json: {ship} gun {o} outside the ship')


def check_boss():
    src = load(BOSS / 'indexed-source.json', 'boss')
    pl = load(BOSS / 'placement.json', 'boss')
    pal = BOSS / 'palette.rgb'
    if not pal.exists() or len(pal.read_bytes()) != 48:
        err('boss: palette.rgb missing or not 48 bytes (16 x R,G,B)')
    if src is None or pl is None:
        return
    frames = {f.get('id'): f for f in src}
    need = ['body', 'core_exposed', 'rotor_0', 'rotor_1', 'rotor_2', 'muzzle_0', 'muzzle_1'] + \
        [f'flame_{n}' for n in range(3)] + \
        [f'turret_{t}_{v}' for t in TURRETS for v in ('south', 'southeast', 'destroyed')]
    sized = {**{f'spray_{n}': (32, 16) for n in range(3)}, **{f'deck_jet_{n}': (16, 16) for n in range(3)}}
    for n in need + list(sized):
        if n not in frames:
            err(f'boss: frame {n} missing')
    for n, s in sized.items():
        if n in frames and (frames[n].get('width'), frames[n].get('height')) != s:
            err(f'boss {n}: must be {s[0]}x{s[1]}')
    sized.update({f'flame_{n}': (16, 32) for n in range(3)})
    for n in ('rotor_0', 'rotor_1', 'rotor_2'):
        if n in frames and (frames[n].get('width', 99) > 32 or frames[n].get('height', 99) > 48):
            err(f'boss {n} (leg): at most 32x48')
    # as tools/import_art.py: frames of all bosses get the largest size of each frame id
    others = {}
    for d in ('boss-level1', 'boss-level2', 'boss-level3'):
        for f in json.loads((ROOT / f'assets/art/{d}/generated/indexed-source.json').read_text()):
            w, h = others.get(f['id'], (0, 0))
            others[f['id']] = (max(w, f['width']), max(h, f['height']))
    total = 1
    for fid, f in frames.items():
        w, h = f.get('width', 0), f.get('height', 0)
        if w % 16 or h % 8 or not w or not h:
            err(f'boss {fid}: {w}x{h}, width must be a multiple of 16 and height of 8')
            continue
        hexrows(f'boss {fid}', f.get('rows'), w, h, 2)
        ow, oh = others.get(fid, (w, h))
        total += glyphs(max(w, ow), max(h, oh)) * (2 if fid.endswith('_southeast') else 1)
    for fid, (w, h) in others.items():          # frames only the other bosses have (e.g. the flame): room too
        if fid not in frames:
            total += glyphs(w, h) * (2 if fid.endswith('_southeast') else 1)
    bw, bh = frames.get('body', {}).get('width', 0), frames.get('body', {}).get('height', 0)
    if bw > 112 or bh > 64:
        err(f'boss body {bw}x{bh}: at most 112x64 (the legs are separate frames below it)')
    if total > BOSS_ROOM:
        err(f'boss needs {total} glyphs, room for {BOSS_ROOM} (per frame width/16 x (height/8 + 1), plus one; '
            f'south-east views count twice; each frame as large as the largest of all bosses)')
    note(f'boss: {total} of {BOSS_ROOM} glyphs, body {bw}x{bh}')
    tur = pl.get('turrets', [])
    if len(tur) != 4:
        err('placement.json: exactly 4 "turrets"')
    for t in tur:
        ox, oy = t.get('offset', [999, 999])
        if not (0 <= ox <= bw - 16 and 0 <= oy <= bh - 16):
            err(f'placement.json: turret {t.get("id")} offset {t.get("offset")} outside the body')
    if 'core' not in pl or 'offset' not in pl['core']:
        err('placement.json: "core" with "offset" missing')
    legs = pl.get('rotors', [])
    if not 2 <= len(legs) <= 4:
        err('placement.json: 2 to 4 "rotors" (the legs)')
    for o in legs:
        ox, oy = o.get('offset', [999, 999])
        if not (-16 <= ox <= bw and 0 <= oy <= bh + 8):
            err(f'placement.json: leg {o} too far from the body')
    fl = pl.get('flame', {}).get('offset')
    if not fl or not (0 <= fl[0] <= bw - 16 and 0 <= fl[1] <= bh + 8):
        err('placement.json: "flame" with "offset" (the flame thrower arm) missing or off the body')
    sp = pl.get('spray', {}).get('offsets', [])
    if not 2 <= len(sp) <= 4:
        err('placement.json: "spray" needs 2 to 4 "offsets" (dust and sparks at the feet)')
    for o in sp:
        if not (-32 <= o[0] <= bw and -16 <= o[1] <= bh + 56):
            err(f'placement.json: spray offset {o} too far from the body')
    cat = pl.get('catapult', {}).get('offset')
    if not cat or not (0 <= cat[0] <= bw - 16 and 0 <= cat[1] <= bh - 16):
        err('placement.json: "catapult" with "offset" (where the drones start on the body) missing')


def main():
    t = c2.check_tiles()
    later, animated = set(), set()
    if t:
        by_name, pals = t
        c2.check_destroyed(by_name, pals)
        r = check_animations(by_name)
        if r:
            later, animated = r
    check_level(later, animated)
    check_enemies()
    check_boss()
    for n in c2.notes:
        print('NOTE:', n)
    for e in c2.errors:
        print('ERROR:', e.replace('levels/level2.json', 'levels/level4.json'))
    print('OK, no errors' if not c2.errors else f'{len(c2.errors)} error(s)')
    return 1 if c2.errors else 0


if __name__ == '__main__':
    sys.exit(main())
