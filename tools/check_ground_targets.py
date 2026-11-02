#!/usr/bin/env python3
"""Check the ground-target artwork (Stage 8) before a pull request: docs/chatgpt_ground_targets.md.

    python3 tools/check_ground_targets.py [path/to/ground-targets.json]

Errors must be fixed; notes should be looked at. Exit code 1 if there are errors.
Needs only the Python standard library.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TILESET = ROOT / 'assets/art/coastal-base/generated'
DEFAULT = ROOT / 'assets/art/ground-targets/generated/ground-targets.json'

REQUIRED_GROUPS = ['hangar', 'depot', 'checkpoint', 'bunker', 'radar', 'fuel', 'crates']
HALL_TILES = ([f'complex_steel_plain'] + [f'complex_steel_{c}_{r}' for r in range(3) for c in range(3)] +
              [f'complex_brick_plain'] + [f'complex_brick_{c}_{r}' for r in range(3) for c in range(3)])
GUN_FRAMES = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
MAX_NEW_TILES = 64
PALETTES = ('water', 'nature', 'structures', 'fixed_targets')

errors, notes = [], []


def err(msg):
    errors.append(msg)


def note(msg):
    notes.append(msg)


def pixels(where, rows, w, h, transparent):
    """Validate hex pixel rows; returns a list of lists of indices or None."""
    if not isinstance(rows, list) or len(rows) != h:
        err(f'{where}: needs exactly {h} rows, got {len(rows) if isinstance(rows, list) else type(rows).__name__}')
        return None
    out = []
    for y, r in enumerate(rows):
        if not isinstance(r, str) or len(r) != w:
            err(f'{where} row {y}: needs a string of {w} hex digits')
            return None
        try:
            vals = [int(ch, 16) for ch in r]
        except ValueError:
            err(f'{where} row {y}: only 0-9 and a-f allowed')
            return None
        out.append(vals)
    if not transparent and any(v == 0 for row in out for v in row):
        err(f'{where}: index 0 is not allowed in landscape tiles (it shows the background colour)')
    return out


def ncm_tile(data, t):
    a = []
    for half in range(2):
        g = data[(2 * t + half) * 64:(2 * t + half) * 64 + 64]
        for y in range(8):
            a.append([(g[y * 8 + x // 2] >> (4 * (x & 1))) & 15 for x in range(16)])
    return a


def rgb(pal, idx):
    return tuple(pal[idx])


def main(path):
    path = Path(path)
    if not path.exists():
        print(f'ERROR: {path} not found')
        return 1
    try:
        art = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f'ERROR: {path}: not valid JSON ({e})')
        return 1
    manifest = json.loads((TILESET / 'manifest.json').read_text())
    tiles = json.loads((TILESET / 'level-example.json').read_text())['tiles']
    terrain = (TILESET / 'terrain.ncm.bin').read_bytes()
    by_name = {t['name']: t for t in tiles}
    pals = {k: [list(c) for c in v] for k, v in manifest['palettes'].items()}

    if art.get('schema') != 1:
        err('schema must be 1')

    # ---------------- palettes
    new_ft = art.get('palettes', {}).get('fixed_targets')
    if new_ft is not None:
        if len(new_ft) != 16 or not all(isinstance(c, list) and len(c) == 3 and all(0 <= v <= 255 for v in c)
                                        for c in new_ft):
            err('palettes.fixed_targets: exactly 16 entries [R,G,B] with 0..255')
        else:
            for i in range(1, 12):
                if list(new_ft[i]) != pals['fixed_targets'][i]:
                    err(f'palettes.fixed_targets[{i}] changed: entries 1-11 are used by the tanks and must stay')
            pals['fixed_targets'] = [list(c) for c in new_ft]
            note('fixed_targets 12-15: ' + ', '.join(str(tuple(c)) for c in new_ft[12:]))
    for extra in art.get('palettes', {}):
        if extra != 'fixed_targets':
            err(f'palettes.{extra}: only fixed_targets may be changed')

    # ---------------- destroyed tiles
    dts = art.get('destroyed_tiles', [])
    names = set()
    of_map = {}
    for i, d in enumerate(dts):
        where = f'destroyed_tiles[{i}] {d.get("name", "?")}'
        name, of, pal = d.get('name'), d.get('of'), d.get('palette')
        if not name or name in names:
            err(f'{where}: missing or duplicate name')
        names.add(name)
        if of not in by_name:
            err(f'{where}: "of" must name a tile of level-example.json, got {of!r}')
            continue
        if of in of_map:
            err(f'{where}: {of} has two destroyed variants')
        of_map[of] = d
        if pal not in PALETTES:
            err(f'{where}: palette must be one of {PALETTES}')
            continue
        intact_pal = by_name[of]['palette']
        if pal not in (intact_pal, 'fixed_targets'):
            err(f'{where}: palette must be the intact tile\'s ({intact_pal}) or fixed_targets')
        px = pixels(where, d.get('pixels'), 16, 16, transparent=False)
        if px is None:
            continue
        unused = [v for row in px for v in row if v >= 1 and pals[pal][v] == [0, 0, 0] and pal == 'fixed_targets'
                  and v >= 12]
        if unused:
            note(f'{where}: uses fixed_targets entries 12-15 that are still black')
        d['_px'] = px
    if len(dts) > MAX_NEW_TILES:
        err(f'{len(dts)} new tiles, at most {MAX_NEW_TILES}')

    # required groups: completeness, edges, difference (on the 32x32 group)
    for g in REQUIRED_GROUPS:
        parts = [f'{g}_{c}_{r}' for r in range(2) for c in range(2)]
        missing = [p for p in parts if p not in of_map]
        if missing:
            err(f'part A: group {g} incomplete, missing destroyed variants of {missing}')
            continue
        if any('_px' not in of_map[p] for p in parts):
            continue
        intact = [[None] * 32 for _ in range(32)]
        broken = [[None] * 32 for _ in range(32)]
        for p in parts:
            c, r = int(p[-3]), int(p[-1])
            ti = by_name[p]
            ipx = ncm_tile(terrain, ti['id'])
            d = of_map[p]
            for y in range(16):
                for x in range(16):
                    intact[r * 16 + y][c * 16 + x] = rgb(pals[ti['palette']], ipx[y][x])
                    broken[r * 16 + y][c * 16 + x] = rgb(pals[d['palette']], d['_px'][y][x])
            expect = f'{g}_destroyed_{c}_{r}'
            if d['name'] != expect:
                note(f'part A: destroyed variant of {p} should be called {expect} (is {d["name"]})')
        edge = [(x, y) for y in range(32) for x in range(32) if min(x, y, 31 - x, 31 - y) < 2]
        inner = [(x, y) for y in range(32) for x in range(32) if min(x, y, 31 - x, 31 - y) >= 2]
        e_diff = sum(intact[y][x] != broken[y][x] for x, y in edge) / len(edge)
        i_diff = sum(intact[y][x] != broken[y][x] for x, y in inner) / len(inner)
        if i_diff < 0.30:
            err(f'part A: {g}: only {i_diff:.0%} of the inner pixels changed, at least 30% (it must look destroyed)')
        if e_diff > 0.25:
            note(f'part A: {g}: {e_diff:.0%} of the outer 2-pixel border differs from the intact group '
                 f'(should stay close to the original so the neighbours fit)')
        print(f'part A {g:10s}: inner changed {i_diff:4.0%}, border changed {e_diff:4.0%}')

    halls = [t for t in HALL_TILES if t in of_map]
    if halls and len(halls) != len(HALL_TILES):
        note(f'part D: {len(halls)} of {len(HALL_TILES)} hall tiles delivered; missing '
             f'{[t for t in HALL_TILES if t not in of_map]}')
    for t in of_map:
        if t not in HALL_TILES and not any(t.startswith(g + '_') for g in REQUIRED_GROUPS):
            note(f'extra destroyed tile for {t} (not requested, will be considered)')

    # ---------------- guns
    def gun(key, size, required):
        gdef = art.get(key)
        if gdef is None:
            if required:
                err(f'{key} missing (part B is required)')
            return
        if gdef.get('size') != [size, size]:
            err(f'{key}.size must be [{size}, {size}]')
        if gdef.get('palette') != 'fixed_targets':
            err(f'{key}.palette must be fixed_targets')
        frames = gdef.get('frames', {})
        got = {}
        for f in GUN_FRAMES + ['wreck']:
            if f not in frames:
                err(f'{key}: frame {f} missing')
                continue
            got[f] = pixels(f'{key}.{f}', frames[f], size, size, transparent=True)
        for f in ('flash0', 'flash1'):
            if f not in frames:
                err(f'{key}: frame {f} missing')
                continue
            pixels(f'{key}.{f}', frames[f], 16, 16, transparent=True)
        extra = set(frames) - set(GUN_FRAMES) - {'wreck', 'flash0', 'flash1'}
        if extra:
            note(f'{key}: extra frames {sorted(extra)} ignored')
        muzzle = gdef.get('muzzle', {})
        for f in GUN_FRAMES:
            m = muzzle.get(f)
            if not (isinstance(m, list) and len(m) == 2 and all(isinstance(v, int) and 0 <= v < size for v in m)):
                err(f'{key}.muzzle.{f}: needs [x, y] inside the {size}x{size} frame')
            elif got.get(f) and got[f][m[1]][m[0]] == 0:
                note(f'{key}.muzzle.{f}: {m} is a transparent pixel (should be the barrel tip)')
        views = [got[f] for f in GUN_FRAMES if got.get(f)]
        if len(views) == 8:
            if len({json.dumps(v) for v in views}) < 8:
                err(f'{key}: some directions are identical')
            # base: pixels in the outer ring that are the same in every direction
            ring = [(x, y) for y in range(size) for x in range(size) if min(x, y, size - 1 - x, size - 1 - y) < 2]
            same = sum(len({v[y][x] for v in views}) == 1 for x, y in ring) / len(ring)
            if same < 0.6:
                note(f'{key}: only {same:.0%} of the outer ring is the same in all directions '
                     f'(the base should not turn with the gun)')
            for f, v in zip(GUN_FRAMES, views):
                if not any(c for row in v for c in row):
                    err(f'{key}.{f}: frame is empty')
        print(f'{key}: {len([f for f in got if got[f]])} frames checked')

    gun('ground_gun', 16, True)
    gun('heavy_gun', 32, False)

    print(f'destroyed tiles: {len(dts)} (max {MAX_NEW_TILES})')
    for n in notes:
        print('NOTE:', n)
    for e in errors:
        print('ERROR:', e)
    print('OK, no errors' if not errors else f'{len(errors)} error(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
