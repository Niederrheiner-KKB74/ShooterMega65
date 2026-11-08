#!/usr/bin/env python3
"""Check the level-2 delivery (tileset, destroyed tiles, level map, boss) before a pull request:
docs/chatgpt_level2.md.

    python3 tools/check_level2_art.py

Errors must be fixed; notes should be looked at. Exit code 1 if there are errors.
Needs Python 3 with numpy and Pillow (as the rest of tools/).
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_level  # noqa: E402

TILES = ROOT / 'assets/art/level2/generated'
BOSS = ROOT / 'assets/art/boss-level2/generated'
LEVEL = ROOT / 'levels/level2.json'
L1_FIXED = ROOT / 'assets/art/ground-targets/generated/ground-targets.json'
PALETTES = ('water', 'nature', 'structures', 'fixed_targets')
MAX_TILES = 128
MAX_DEST = 48
BOSS_ROOM = 324                 # glyphs of the fighter, bomber, helicopter and armoured-plane area (Stage 9b)
MAX_ROWS_DELIVERED = 512        # Stage 18b: level format 3 (16-bit row indices); was 240
TURRETS = ['nw', 'ne', 'sw', 'se']

errors, notes = [], []


def err(m):
    errors.append(m)


def note(m):
    notes.append(m)


def load(path, what):
    if not path.exists():
        err(f'{what}: {path.relative_to(ROOT)} missing')
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        err(f'{what}: {path.relative_to(ROOT)} is not valid JSON ({e})')
        return None


def hexrows(where, rows, w, h, digits):
    """digits = 1: one hex digit per pixel (tiles); 2: two hex digits per pixel (boss, as PR #14)."""
    if not isinstance(rows, list) or len(rows) != h:
        err(f'{where}: needs {h} rows')
        return None
    out = []
    for y, r in enumerate(rows):
        if not isinstance(r, str) or len(r) != w * digits:
            err(f'{where} row {y}: needs {w * digits} hex digits')
            return None
        try:
            vals = [int(r[i:i + digits], 16) for i in range(0, len(r), digits)]
        except ValueError:
            err(f'{where} row {y}: only 0-9 and a-f allowed')
            return None
        if any(v > 15 for v in vals):
            err(f'{where} row {y}: palette index above 15')
            return None
        out.append(vals)
    return out


def check_tiles():
    man = load(TILES / 'manifest.json', 'tileset')
    lst = load(TILES / 'level-example.json', 'tileset')
    ncm = TILES / 'terrain.ncm.bin'
    if not ncm.exists():
        err('tileset: terrain.ncm.bin missing')
        return None
    data = ncm.read_bytes()
    if man is None or lst is None:
        return None
    if len(data) % 128:
        err(f'terrain.ncm.bin: {len(data)} bytes, must be a multiple of 128 (two 16x8 glyphs per tile)')
    n = len(data) // 128
    if n > MAX_TILES:
        err(f'{n} tiles, at most {MAX_TILES}')
    tiles = lst.get('tiles', [])
    ids = [t.get('id') for t in tiles]
    if ids != list(range(len(tiles))):
        err('level-example.json: tile ids must be 0, 1, 2 ... in order')
    if len(tiles) != n:
        err(f'level-example.json lists {len(tiles)} tiles, terrain.ncm.bin holds {n}')
    names = [t.get('name') for t in tiles]
    if len(set(names)) != len(names):
        err('level-example.json: tile names must be unique')
    for t in tiles:
        if t.get('palette') not in PALETTES:
            err(f'tile {t.get("id")} {t.get("name")}: palette must be one of {PALETTES}')
    pals = man.get('palettes', {})
    for p in PALETTES:
        if p not in pals or len(pals[p]) != 16:
            err(f'manifest.json: palette {p} with exactly 16 entries [R,G,B] missing')
    fixed = json.loads(L1_FIXED.read_text())['palettes']['fixed_targets']
    if pals.get('fixed_targets') and [list(c) for c in pals['fixed_targets']] != fixed:
        err('manifest.json: fixed_targets must be exactly the level-1 palette incl. entries 12-15 '
            '(tanks, guns and their wrecks use it)')
    zero = [t for t in range(min(n, len(tiles))) if any((b & 15) == 0 or (b >> 4) == 0
                                                         for b in data[t * 128:t * 128 + 128])]
    if zero:
        err(f'tiles {zero[:10]}{" ..." if len(zero) > 10 else ""} use index 0 (shows the background colour)')
    water = [t['name'] for t in tiles if t.get('palette') == 'water']
    note(f'tileset: {n} tiles; palette water (tanks avoid these tiles): {len(water)} tiles')
    return {t['name']: t for t in tiles}, pals


def check_destroyed(by_name, pals):
    gt = load(TILES / 'ground-targets.json', 'destroyed tiles')
    if gt is None:
        return
    if 'palettes' in gt:
        err('ground-targets.json: no "palettes" here (fixed_targets is in manifest.json)')
    dts = gt.get('destroyed_tiles', [])
    if not dts:
        err('ground-targets.json: no destroyed tiles')
    if len(dts) > MAX_DEST:
        err(f'{len(dts)} destroyed tiles, at most {MAX_DEST}')
    seen = set()
    groups = {}
    for i, d in enumerate(dts):
        w = f'destroyed_tiles[{i}] {d.get("name", "?")}'
        of = d.get('of')
        if of not in by_name:
            err(f'{w}: "of" must name a tile of level-example.json')
            continue
        if of in seen:
            err(f'{w}: {of} has two destroyed variants')
        seen.add(of)
        if d.get('kind') not in build_level.TARGET_KINDS:
            err(f'{w}: kind must be one of {build_level.TARGET_KINDS}')
            continue
        c, r = d.get('col', 0), d.get('row', 0)
        if d['kind'] == 'hall':
            if (c, r) != (0, 0):
                err(f'{w}: hall tiles are single cells (col 0, row 0)')
        elif c not in (0, 1) or r not in (0, 1):
            err(f'{w}: col and row must be 0 or 1 (cell inside the 32x32 building)')
        else:
            groups.setdefault(d.get('group', '?'), set()).add((c, r))
        if d.get('palette') not in (by_name[of]['palette'], 'fixed_targets'):
            err(f'{w}: palette must be the intact tile\'s ({by_name[of]["palette"]}) or fixed_targets')
        px = hexrows(w, d.get('pixels'), 16, 16, 1)
        if px and any(v == 0 for row in px for v in row):
            err(f'{w}: index 0 is not allowed in landscape tiles')
    for g, cells in groups.items():
        if g == '?':
            err('2x2 destroyed tiles need a "group" name (the building they belong to)')
        elif cells != {(0, 0), (1, 0), (0, 1), (1, 1)}:
            err(f'group {g}: needs all four cells, has {sorted(cells)}')
    total = len(by_name) + len(dts)
    note(f'destroyed tiles: {len(dts)} (max {MAX_DEST}); buildings: {len(groups)}')
    if len(by_name) > MAX_TILES:
        err(f'intact tiles {len(by_name)} > {MAX_TILES}')
    return total


def check_level():
    lv = load(LEVEL, 'level')
    if lv is None:
        return
    if lv.get('tileset') != 'assets/art/level2/generated':
        err('levels/level2.json: "tileset" must be "assets/art/level2/generated"')
    if lv.get('ground_targets') != 'assets/art/level2/generated':
        err('levels/level2.json: "ground_targets" must be "assets/art/level2/generated"')
    rows = []
    for e in lv.get('map', []):
        rows += [tuple(x) for x in e['rows']] * e['repeat'] if isinstance(e, dict) else [tuple(e)]
    palms = {t['id'] for t in json.loads((TILES / 'level-example.json').read_text())['tiles']
             if t['name'] in ('palm0', 'palm1', 'palm2', 'palm3')}
    if palms and any(t in palms for r in rows for t in r):
        note(f'levels/level2.json: {len(set(rows))} different map rows incl. the automatic palms '
             f'(a new map from ChatGPT: at most {MAX_ROWS_DELIVERED} without them)')
    elif len(set(rows)) > MAX_ROWS_DELIVERED:
        err(f'levels/level2.json: {len(set(rows))} different map rows, at most {MAX_ROWS_DELIVERED} '
            f'(room for the automatic palms)')
    types = [e.get('type') for e in lv.get('events', [])]
    for t, n in (('shop', 2), ('boss', 1), ('end', 1)):
        if types.count(t) != n:
            err(f'levels/level2.json: needs {n} "{t}" event(s), has {types.count(t)}')
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _, _, report = build_level.build(LEVEL, tmp, 'L2')
            for line in report:
                print('level:', line)
        except build_level.LevelError as e:
            err(f'levels/level2.json: {e}')
        except Exception as e:                  # noqa: BLE001 - report anything the converter trips over
            err(f'levels/level2.json: converter failed: {type(e).__name__}: {e}')


def glyphs(w, h):
    return (w // 16) * (h // 8 + 1)


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
        [f'turret_{t}_{v}' for t in TURRETS for v in ('south', 'southeast', 'destroyed')]
    for n in need:
        if n not in frames:
            err(f'boss: frame {n} missing')
    # as tools/import_art.py: frames of both bosses get the larger of the two sizes (level-1 quadrotor)
    l1 = {f['id']: (f['width'], f['height'])
          for f in json.loads((ROOT / 'assets/art/boss-level1/generated/indexed-source.json').read_text())}
    total = 1
    for fid, f in frames.items():
        w, h = f.get('width', 0), f.get('height', 0)
        if w % 16 or h % 8 or not w or not h:
            err(f'boss {fid}: {w}x{h}, width must be a multiple of 16 and height of 8')
            continue
        hexrows(f'boss {fid}', f.get('rows'), w, h, 2)
        lw, lh = l1.get(fid, (w, h))
        n = glyphs(max(w, lw), max(h, lh))
        total += n * (2 if fid.endswith('_southeast') else 1)   # south-west = mirrored south-east, stored too
    bw, bh = frames.get('body', {}).get('width', 0), frames.get('body', {}).get('height', 0)
    if bw > 128 or bh > 80:
        err(f'boss body {bw}x{bh}: at most 128x80')
    if total > BOSS_ROOM:
        err(f'boss needs {total} glyphs, room for {BOSS_ROOM} (formula: per frame width/16 x (height/8 + 1), '
            f'plus one; south-east views count twice)')
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
    rot = pl.get('rotors', [])
    if len(rot) > 4:
        err('placement.json: at most 4 "rotors" (animated overlays)')
    # Stage 11: hover tank (docs/chatgpt_level2d.md): no turning views, flame and dust effects
    for old in ('side', 'diag'):
        if old in pl:
            err(f'placement.json: "{old}" belongs to the land cruiser, please remove it')
    for old in ('body_side', 'core_exposed_side', 'rotor_side_0', 'rotor_side_1', 'rotor_side_2',
                'body_diag', 'core_exposed_diag', 'dust_0', 'dust_1'):
        if old in frames:
            err(f'boss: frame {old} belongs to the land cruiser, please remove it')
    for n, (w, h) in (('flame_0', (16, 32)), ('flame_1', (16, 32)), ('flame_2', (16, 32)),
                      ('spray_0', (32, 16)), ('spray_1', (32, 16)), ('spray_2', (32, 16))):
        if n not in frames:
            err(f'boss: frame {n} missing')
        elif (frames[n].get('width'), frames[n].get('height')) != (w, h):
            err(f'boss {n}: must be {w}x{h}')
    fl = pl.get('flame', {})
    if 'offset' not in fl:
        err('placement.json: "flame" with "offset" missing')
    else:
        fx, fy = fl['offset']
        if not (0 <= fx <= bw - 16 and 0 <= fy <= bh + 16):
            err(f'placement.json: flame offset {fl["offset"]} not at the body')
    sp = pl.get('spray', {}).get('offsets', [])
    if not 2 <= len(sp) <= 4:
        err('placement.json: "spray" needs 2 to 4 "offsets"')
    for o in sp:
        if not (-32 <= o[0] <= bw and -16 <= o[1] <= bh + 8):
            err(f'placement.json: spray offset {o} too far from the body')


def main():
    t = check_tiles()
    if t:
        by_name, pals = t
        check_destroyed(by_name, pals)
    check_level()
    check_boss()
    for n in notes:
        print('NOTE:', n)
    for e in errors:
        print('ERROR:', e)
    print('OK, no errors' if not errors else f'{len(errors)} error(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
