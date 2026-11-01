#!/usr/bin/env python3
"""Convert a level description (JSON, see docs/level_json.md) into the engine's level files.

  python3 tools/build_level.py levels/level01.json --out build/levels --name L1

Writes:
  <NAME>GFX   landscape glyphs + 4 landscape palettes (SEQ file on the D81)
  <NAME>DAT   map (metatiles, row dictionary, row list), events, formations, paths
  <name>_preview.png   level picture (start at the bottom) with event markers
  <name>_report.txt    sizes and budgets
Both files are loaded to $50000 by the engine (max. 16 KB each).
"""
import argparse
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
COLS = 21
MAX_FILE = 0x4000
LAND_BANKS = {'water': 1, 'nature': 2, 'structures': 3, 'fixed_targets': 4}
ENEMIES = {'fighter': 0, 'bomber': 1, 'helicopter': 2, 'armoured': 3}
GROUND = {'tank': 4}
DIRS = {'north': 0, 'east': 1, 'south': 2, 'west': 3}
EV_FORMATION, EV_GROUND, EV_SPEED, EV_SHOP, EV_BOSS, EV_END = 1, 2, 3, 4, 5, 6
OP_END, OP_LOOP, OP_ENDLOOP, OP_AIM, OP_FIRE, OP_WAIT = 0x80, 0x81, 0x82, 0x83, 0x84, 0x85
SHOPS = {'mid': 0, 'end': 1}


class LevelError(Exception):
    pass


def swap(v):
    return ((v & 0x0F) << 4) | (v >> 4)


def quarter(v, what):
    q = round(v * 4)
    if abs(v * 4 - q) > 1e-6 or not -127 <= q <= 127:
        raise LevelError(f'{what}: {v} px/frame must be a multiple of 0.25 between -31.75 and 31.75')
    return q & 0xFF


def expand_map(entries, where='map'):
    rows = []
    for i, e in enumerate(entries):
        if isinstance(e, dict):
            n = e.get('repeat', 1)
            rows += expand_map(e['rows'], f'{where}[{i}]') * n
        else:
            if len(e) != COLS:
                raise LevelError(f'{where}[{i}]: a row needs {COLS} tile ids, got {len(e)}')
            rows.append(list(e))
    return rows


def compile_path(name, cmds):
    out = bytearray()
    loop_open = False
    for i, c in enumerate(cmds):
        op, args = c[0], c[1:]
        w = f'path {name}[{i}] {op}'
        if op == 'move':
            frames, dx, dy = args
            while frames > 0:
                f = min(frames, 127)
                out += bytes((f, quarter(dx, w), quarter(dy, w)))
                frames -= f
        elif op == 'sine':                 # amplitude px, period frames, cycles, dy px/frame
            amp, period, cycles, dy = args
            steps = 16
            seg = max(1, round(period / steps))
            for k in range(round(cycles * steps)):
                # velocity = derivative of amp*sin(2*pi*t/period)
                t = (k + 0.5) * seg
                v = amp * 2 * math.pi / period * math.cos(2 * math.pi * t / period)
                out += bytes((seg, quarter(round(v * 4) / 4, w), quarter(dy, w)))
        elif op == 'aim':
            frames, speed = args
            out += bytes((OP_AIM, frames, quarter(speed, w)))
        elif op == 'wait':
            out += bytes((OP_WAIT, args[0]))
        elif op == 'fire':
            out += bytes((OP_FIRE,))
        elif op == 'loop':
            if loop_open:
                raise LevelError(f'{w}: loops cannot be nested')
            loop_open = True
            out += bytes((OP_LOOP, args[0]))
        elif op == 'endloop':
            if not loop_open:
                raise LevelError(f'{w}: endloop without loop')
            loop_open = False
            out += bytes((OP_ENDLOOP,))
        elif op == 'end':
            out += bytes((OP_END,))
        else:
            raise LevelError(f'{w}: unknown command')
    if loop_open:
        raise LevelError(f'path {name}: loop not closed')
    if not out or out[-1] != OP_END:
        out += bytes((OP_END,))
    return bytes(out)


def build(src, outdir, name):
    lv = json.loads(Path(src).read_text())
    tileset = ROOT / lv.get('tileset', 'assets/art/spec-v2/generated')
    tiles_meta = json.loads((tileset / 'level-example.json').read_text())['tiles']
    terrain = (tileset / 'terrain.ncm.bin').read_bytes()
    manifest = json.loads((tileset / 'manifest.json').read_text())
    ntiles = len(terrain) // 128
    tile_bank = {t['id']: LAND_BANKS[t['palette']] for t in tiles_meta}

    # ---------------- GFX file: palettes of banks 1-4 + all landscape glyphs
    pal = bytearray()
    for pname in LAND_BANKS:
        cols = manifest['palettes'][pname]
        for ch in range(3):
            pal += bytes(swap(c[ch]) for c in cols)
    gfx = b'SG' + struct.pack('<H', ntiles * 2) + bytes(pal) + terrain

    # ---------------- map
    rows = expand_map(lv['map'])
    for r, row in enumerate(rows):
        for t in row:
            if not 0 <= t < ntiles:
                raise LevelError(f'map row {r}: tile id {t} does not exist (0..{ntiles - 1})')
    used = sorted({t for row in rows for t in row})
    meta_id = {t: i for i, t in enumerate(used)}
    meta = b''.join(bytes((2 * t, 2 * t + 1, (tile_bank[t] << 4) | 0x0F)) for t in used)
    dict_rows, row_index = [], {}
    rowlist = bytearray()
    for row in rows:
        key = tuple(meta_id[t] for t in row)
        if key not in row_index:
            row_index[key] = len(dict_rows)
            dict_rows.append(key)
        rowlist.append(row_index[key])
    if len(dict_rows) > 256:
        raise LevelError(f'{len(dict_rows)} different map rows, maximum 256')

    # ---------------- paths and formations
    path_names = list(lv.get('paths', {}))
    paths = [compile_path(p, lv['paths'][p]) for p in path_names]
    form_names = list(lv.get('formations', {}))
    forms = bytearray()
    for fn in form_names:
        f = lv['formations'][fn]
        if f['enemy'] not in ENEMIES:
            raise LevelError(f'formation {fn}: enemy must be one of {list(ENEMIES)}')
        if f['path'] not in path_names:
            raise LevelError(f'formation {fn}: unknown path {f["path"]}')
        if not 1 <= f.get('count', 1) <= 8:
            raise LevelError(f'formation {fn}: count 1..8')
        forms += struct.pack('<BBBBhh', ENEMIES[f['enemy']], f.get('count', 1), path_names.index(f['path']),
                             f.get('delay', 16), f.get('x', 144), f.get('y', -32))

    # ---------------- events
    events = bytearray()
    last = -1
    nrows = len(rows)
    has_end = False
    for i, e in enumerate(lv['events']):
        row, typ = e['row'], e['type']
        w = f'event {i} (row {row}, {typ})'
        if row < last:
            raise LevelError(f'{w}: events must be sorted by row')
        if not 0 <= row <= nrows:
            raise LevelError(f'{w}: row outside the map (0..{nrows})')
        last = row
        if typ == 'formation':
            if e['formation'] not in form_names:
                raise LevelError(f'{w}: unknown formation')
            x = e.get('x', -1)
            flags = (1 if e.get('mirror') else 0) | (2 if 'x' in e else 0)
            rec = (EV_FORMATION, form_names.index(e['formation']), x & 0xFF, (x >> 8) & 0xFF, flags, 0)
        elif typ == 'ground':
            if e['enemy'] not in GROUND:
                raise LevelError(f'{w}: ground enemy must be one of {list(GROUND)}')
            x = e['x']
            if not 0 <= x <= 304:
                raise LevelError(f'{w}: x 0..304')
            rec = (EV_GROUND, GROUND[e['enemy']], x & 0xFF, x >> 8, DIRS[e.get('dir', 'south')], 0)
        elif typ == 'speed':
            v = round(e['value'] * 256)
            if not 0 <= v <= 0x400:
                raise LevelError(f'{w}: speed 0..4 px/frame')
            rec = (EV_SPEED, v & 0xFF, v >> 8, 0, 0, 0)
        elif typ == 'shop':
            rec = (EV_SHOP, SHOPS[e.get('id', 'mid')], 0, 0, 0, 0)
        elif typ == 'boss':
            rec = (EV_BOSS, e.get('id', 0), 0, 0, 0, 0)
        elif typ == 'end':
            rec = (EV_END, 0, 0, 0, 0, 0)
            has_end = True
        else:
            raise LevelError(f'{w}: unknown event type')
        events += struct.pack('<H', row) + bytes(rec)
    if not has_end:
        events += struct.pack('<H', nrows) + bytes((EV_END, 0, 0, 0, 0, 0))
    events += b'\xff\xff' + bytes(6)

    # ---------------- DAT file
    speed = round(lv.get('scroll_speed', 0.5) * 256)
    hdr_len = 32
    off_meta = hdr_len
    off_dict = off_meta + len(meta)
    off_rows = off_dict + COLS * len(dict_rows)
    off_events = off_rows + len(rowlist)
    off_forms = off_events + len(events)
    off_ptab = off_forms + len(forms)
    off_code = off_ptab + 2 * len(paths)
    ptab, code = bytearray(), bytearray()
    for p in paths:
        ptab += struct.pack('<H', off_code + len(code))
        code += p
    header = struct.pack('<2sBBHHHHHHHHB', b'SL', 1, len(used), nrows, off_meta, off_dict, off_rows,
                         off_events, off_forms, off_ptab, speed, len(dict_rows) & 0xFF)
    header = header.ljust(hdr_len, b'\0')
    dat = header + meta + b''.join(bytes(r) for r in dict_rows) + bytes(rowlist) + bytes(events) + bytes(forms) + bytes(ptab) + bytes(code)
    for fname, data in (('GFX', gfx), ('DAT', dat)):
        if len(data) > MAX_FILE:
            raise LevelError(f'{name}{fname} is {len(data)} bytes, maximum {MAX_FILE}')

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f'{name}GFX').write_bytes(gfx)
    (outdir / f'{name}DAT').write_bytes(dat)

    # ---------------- preview: rebuild the picture from the binary data, mark events
    palette = {}
    for bank in LAND_BANKS.values():
        palette[bank] = manifest['palettes'][list(LAND_BANKS)[bank - 1]]
    img = np.zeros((nrows * 16, COLS * 16, 3), np.uint8)
    for r in range(nrows):
        y0 = (nrows - 1 - r) * 16
        drow = dat[off_dict + COLS * rowlist[r]:][:COLS]
        for c in range(COLS):
            top, bot, col = meta[3 * drow[c]:3 * drow[c] + 3]
            for half, g in ((0, top), (1, bot)):
                gl = terrain[g * 64:g * 64 + 64]
                for yy in range(8):
                    for xx in range(16):
                        v = (gl[yy * 8 + xx // 2] >> (4 * (xx & 1))) & 15
                        img[y0 + half * 8 + yy, c * 16 + xx] = palette[col >> 4][v]
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    colours = {'formation': (255, 60, 60), 'ground': (255, 200, 0), 'speed': (0, 200, 255),
               'shop': (0, 255, 120), 'boss': (255, 0, 255), 'end': (255, 255, 255)}
    for e in lv['events']:
        y = (nrows - e['row']) * 16
        d.line((0, y, 15, y), fill=colours[e['type']], width=2)
        x = e.get('x', 160 if e['type'] != 'formation' else lv['formations'][e['formation']].get('x', 144))
        d.rectangle((x + 16, y - 3, x + 22, y + 3), outline=colours[e['type']])
    im.save(outdir / f'{name.lower()}_preview.png')
    report = [f'level {lv.get("name", name)}: {nrows} map rows ({nrows * 16} px, '
              f'{nrows * 16 / (speed / 256 * 50):.0f} s at {speed / 256} px/frame)',
              f'metatiles {len(used)}, different rows {len(dict_rows)}/256, glyphs {ntiles * 2}',
              f'events {len(lv["events"])}, formations {len(form_names)}, paths {len(paths)} ({len(code)} bytes)',
              f'{name}GFX {len(gfx)} bytes, {name}DAT {len(dat)} bytes (max. {MAX_FILE} each)']
    (outdir / f'{name.lower()}_report.txt').write_text('\n'.join(report) + '\n')
    return gfx, dat, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('level')
    ap.add_argument('--out', default=str(ROOT / 'build/levels'))
    ap.add_argument('--name', default='L1')
    a = ap.parse_args()
    try:
        _, _, report = build(a.level, a.out, a.name)
    except LevelError as e:
        sys.exit(f'level error: {e}')
    print('\n'.join(report))


if __name__ == '__main__':
    main()
