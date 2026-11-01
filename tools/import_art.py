#!/usr/bin/env python3
"""Import the artwork v2 package (assets/art/spec-v2, PR #4) into the engine's data formats.

Reads the indexed pixel data (indexed-source.json), the palettes (manifest.json) and the
example level (level-example.json + terrain.ncm.bin). Writes into build/gen/:

  tiles.bin      landscape NCM glyphs (tile t: glyph 2t = upper half, 2t+1 = lower half)
  map.bin        MAP_ROWS x 21 glyph offsets, glyph row 0 = level start (bottom)
  mapcol.bin     MAP_ROWS x 21 colour-RAM byte 1 (palette bank << 4 | $0f)
  pixies.bin     all pixie frames, column stacks with blank guards (+ HUD glyph area)
  sprite.bin     6 player frame pairs, 512 bytes each (2 x 192 + padding)
  palette.bin    text palette 0 (R/G/B planes, nibble-swapped), sprpal.bin sprite palette
  hud.bin        HUD source data: 10 digit half-glyphs (32 bytes), lives glyph template (64 bytes),
                 shield box template (256 bytes)
  assets.inc     constants, frames.inc frame tables, previews

Palette banks (text palette 0): 0 C64 colours, 1-4 landscape, 5-8 air enemies,
9 player shot, 10 red enemy shot, 11 fire shot, 12 HUD + bonus + placeholder tank,
13 rocket, 14 small explosion, 15 big explosion. The tank (assets/art/ground-vehicles, PR #6)
uses the fixed_targets landscape palette (bank 4), as delivered. All 15 banks are in use; groups that
have to share a bank later (e.g. the orange/green weapon shots) are merged by
merge_bank(): above 15 colours it reduces them (median cut) and remaps every pixel.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/art/spec-v2'
GEN = ART / 'generated'
sys.path.insert(0, str(ROOT / 'tools'))
import make_assets as ph  # noqa: E402  (placeholder tank, C64 colours, NCM packer)

BG_COLS = 21
LAND = {'water': 1, 'nature': 2, 'structures': 3, 'fixed_targets': 4}
BANKS = {
    5: ['fighter'], 6: ['bomber'], 7: ['helicopter'], 8: ['armoured_plane'],
    9: ['player_shot_blue'], 10: ['enemy_shot_red'], 11: ['enemy_shot_fire'], 13: ['rocket'],
    14: ['explosion_16'], 15: ['explosion_32'],
}
HUD_BANK = 12
# HUD bank colours (index: role)
HUD_PAL = [(0, 0, 0), (54, 82, 111), (221, 239, 247), (255, 165, 50),     # 1-3 from hud.json
           (14, 18, 30),        # 4 backdrop
           (150, 160, 178),     # 5 bar frame
           (60, 205, 90),       # 6 shield high
           (245, 215, 40),      # 7 shield medium
           (230, 50, 40),       # 8 shield low
           (36, 42, 58),        # 9 bar empty
           (160, 245, 175),     # 10 bonus light
           (20, 120, 55),       # 11 bonus dark
           (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
TANKS = ROOT / 'assets/art/ground-vehicles/generated'
TANK_DIRS = ('north', 'east', 'south', 'west')       # engine direction 0-3
TANK_PHASES = 4
SHIELD_MAX = 48                 # bar length in pixels
BAR_X0 = 11                     # first bar pixel inside the 64 px shield box

# frames in engine order: (constant name, group, frame)
AIR = [('FIGHTER', 'fighter'), ('BOMBER', 'bomber'), ('HELI', 'helicopter'), ('ARMOURED', 'armoured_plane')]
# Frames used by the engine. Since PR #7 the three frames per aircraft are real effect phases
# (exhaust flames / rotor, everything else pixel-identical). The importer warns if a frame set
# ever turns into unrelated drawings again (that made the objects jump in the first Stage 2 build).
AIR_FRAMES = 3
PLAYER_STRAIGHT = 0          # straight flight cycles frames 0-2; 3 = left, 5 = right
ANIM_MIN_SHARED = 0.6        # report frame sets whose consecutive frames share less than this
CAPSULES = ROOT / 'assets/art/bonus-capsules/generated'
CAPSULE_FRAMES = [('CAP_S', 'capsule_S'), ('CAP_D1', 'capsule_dollar_small'),
                  ('CAP_D2', 'capsule_dollar_medium'), ('CAP_D3', 'capsule_dollar_large')]


def load():
    manifest = json.loads((GEN / 'manifest.json').read_text())
    src = json.loads((GEN / 'indexed-source.json').read_text())
    pix = {}
    for s in src:
        a = np.frombuffer(bytes.fromhex(''.join(s['rows'])), np.uint8).reshape(s['height'], s['width'])
        pix[s['group'], s['frame']] = a.copy()
    return manifest, pix


def merge_bank(groups, manifest, pix):
    """Return (palette[16], {group: remap array}) for groups sharing one bank."""
    colours = {}
    for g in groups:
        pal = manifest['palettes'][g]
        for (gg, _), a in pix.items():
            if gg != g:
                continue
            for idx, n in zip(*np.unique(a, return_counts=True)):
                if idx:
                    c = tuple(pal[idx])
                    colours[c] = colours.get(c, 0) + int(n)
    cols = sorted(colours, key=lambda c: -colours[c])
    if len(cols) > 15:      # median cut on a weighted swatch, then nearest colour
        swatch = []
        for c in cols:
            swatch += [c] * max(1, colours[c] // 4)
        img = Image.fromarray(np.array(swatch, np.uint8).reshape(1, -1, 3))
        q = img.quantize(15, method=Image.Quantize.MEDIANCUT)
        qp = q.getpalette()[:45]
        reduced = [tuple(qp[i:i + 3]) for i in range(0, 45, 3)]
    else:
        reduced = cols
    palette = [(0, 0, 0)] + reduced + [(0, 0, 0)] * (15 - len(reduced))
    remaps = {}
    for g in groups:
        pal = manifest['palettes'][g]
        m = np.zeros(16, np.uint8)
        for i in range(1, 16):
            c = np.array(pal[i])
            m[i] = 1 + int(np.argmin([((c - np.array(r)) ** 2).sum() for r in reduced]))
        remaps[g] = m
    return palette, remaps, len(cols)


def hitbox(a):
    ys, xs = np.nonzero(a)
    if not len(xs):
        return a.shape[1] // 2, a.shape[0] // 2, 1, 1
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return (x0 + x1) // 2, (y0 + y1) // 2, max(1, (x1 - x0) // 2), max(1, (y1 - y0) // 2)


def pad16(a):
    h, w = a.shape
    out = np.zeros((h, (w + 15) // 16 * 16), np.uint8)
    off = (out.shape[1] - w) // 2
    out[:, off:off + w] = a
    return out


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    manifest, pix = load()
    hud = json.loads((ART / 'source/hud.json').read_text())
    report = []

    # ------------------------------------------------------------ palettes
    pal = [(0, 0, 0)] * 256
    pal[:16] = [(0, 0, 0), (255, 255, 255), (136, 0, 0), (170, 255, 238), (204, 68, 204), (0, 204, 85),
                (0, 0, 170), (238, 238, 119), (221, 136, 85), (102, 68, 0), (255, 119, 119), (51, 51, 51),
                (119, 119, 119), (170, 255, 102), (0, 136, 255), (187, 187, 187)]
    for name, bank in LAND.items():
        pal[bank * 16:bank * 16 + 16] = [tuple(c) for c in manifest['palettes'][name]]
    remap = {}
    for bank, groups in BANKS.items():
        p, r, n = merge_bank(groups, manifest, pix)
        pal[bank * 16:bank * 16 + 16] = p
        remap.update({g: (bank, m) for g, m in r.items()})
        report.append(f'bank {bank:2}: {"+".join(groups)} ({n} colours{" -> 15" if n > 15 else ""})')
    pal[HUD_BANK * 16:HUD_BANK * 16 + 16] = HUD_PAL
    (out / 'palette.bin').write_bytes(bytes(ph.swap(c[ch]) for ch in range(3) for c in pal))
    sprpal = [tuple(c) for c in manifest['palettes']['player']] * 2
    (out / 'sprpal.bin').write_bytes(bytes(ph.swap(c[ch]) for ch in range(3) for c in sprpal))

    # ------------------------------------------------------------ landscape
    level = json.loads((GEN / 'level-example.json').read_text())
    terrain = (GEN / 'terrain.ncm.bin').read_bytes()
    ntiles = len(terrain) // 128
    assert ntiles * 2 <= 256, 'tile glyph offsets must fit a byte'
    (out / 'tiles.bin').write_bytes(terrain)
    tile_pal = {t['id']: LAND[t['palette']] for t in level['tiles']}
    rows = level['rows']                         # top to bottom
    assert all(len(r) == BG_COLS for r in rows)
    map_bytes, col_bytes = bytearray(), bytearray()
    for meta in reversed(rows):                  # bottom (level start) first
        for half in (1, 0):                      # lower glyph row first: rows count upwards
            for t in meta:
                map_bytes.append(t * 2 + half)
                col_bytes.append((tile_pal[t] << 4) | 0x0F)
    map_rows = len(rows) * 2
    assert map_rows & (map_rows - 1) == 0, 'map rows must be a power of two (ring index masking)'
    (out / 'map.bin').write_bytes(map_bytes)
    (out / 'mapcol.bin').write_bytes(col_bytes)

    # check: rebuild the level picture from our map + glyphs and compare with level-example.png
    ref = np.array(Image.open(GEN / 'level-example.png').convert('RGB'))
    img = np.zeros((map_rows * 8, BG_COLS * 16, 3), np.uint8)
    for r in range(map_rows):
        y = (map_rows - 1 - r) * 8
        for c in range(BG_COLS):
            g = terrain[map_bytes[r * BG_COLS + c] * 64:][:64]
            bank = col_bytes[r * BG_COLS + c] >> 4
            for yy in range(8):
                for xx in range(16):
                    v = (g[yy * 8 + xx // 2] >> (4 * (xx & 1))) & 15
                    img[y + yy, c * 16 + xx] = pal[bank * 16 + v]
    assert (img == ref).all(), 'map conversion does not reproduce level-example.png'
    report.append(f'landscape: {ntiles} tiles, {map_rows} glyph rows, matches level-example.png')

    # ------------------------------------------------------------ pixie frames
    frames = []          # (name, pixels padded, bank, hitbox from unpadded)

    def add(name, a, bank):
        p = pad16(a)
        off = (p.shape[1] - a.shape[1]) // 2
        cx, cy, hw, hh = hitbox(a)
        frames.append((name, p, bank, (cx + off, cy, hw, hh)))

    def grp(group, n):
        bank, m = remap[group]
        return m[pix[group, n]], bank

    for const, group in AIR:
        for n in range(AIR_FRAMES):
            a, b = grp(group, n)
            add(f'{const}{n}', a, b)
    for n in range(2):
        add(f'PSHOT{n}', *grp('player_shot_blue', n))
    add('ESHOT_RED', *grp('enemy_shot_red', 0))
    add('ESHOT_FIRE', *grp('enemy_shot_fire', 0))
    add('ROCKET', *grp('rocket', 0))
    for n in range(6):
        add(f'EX16_{n}', *grp('explosion_16', n))
    for n in range(6):
        add(f'EX32_{n}', *grp('explosion_32', n))
    tank_rgb = (TANKS / 'palette.rgb').read_bytes()
    assert [list(tank_rgb[i:i + 3]) for i in range(0, 48, 3)] == manifest['palettes']['fixed_targets'], \
        'tank artwork must use the fixed_targets palette (bank 4)'
    tanks = {(t['direction'], t['phase']): np.frombuffer(bytes.fromhex(''.join(t['rows'])), np.uint8).reshape(16, 16)
             for t in json.loads((TANKS / 'indexed-source.json').read_text())}
    for d in TANK_DIRS:
        for n in range(TANK_PHASES):
            frames.append((f'TANK_{d[0].upper()}{n}', tanks[d, n].copy(), LAND['fixed_targets'], (8, 8, 6, 6)))
    cap_pal = json.loads((CAPSULES / 'manifest.json').read_text())['palette']
    assert [tuple(c) for c in cap_pal] == [tuple(c) for c in HUD_PAL[:16]][:len(cap_pal)] or \
        all(tuple(cap_pal[i]) == HUD_PAL[i] for i in range(12)), 'capsules must use the HUD palette (bank 12)'
    caps = {c['id']: np.frombuffer(bytes.fromhex(''.join(c['rows'])), np.uint8).reshape(c['height'], c['width'])
            for c in json.loads((CAPSULES / 'indexed-source.json').read_text())}
    for const, cid in CAPSULE_FRAMES:
        add(const, caps[cid].copy(), HUD_BANK)

    glyphs = [bytes(64)]
    table = []
    for name, p, bank, hb in frames:
        h, w = p.shape[0] // 8, p.shape[1] // 16
        base = len(glyphs)
        for c in range(w):
            for i in range(h):
                glyphs.append(ph.ncm_glyph(p[i * 8:i * 8 + 8, c * 16:c * 16 + 16]))
            glyphs.append(bytes(64))
        table.append(dict(name=name, base=base, w=w, h=h, pal=(bank << 4) | 15, hit=hb))
    # HUD: score box 3 columns, shield box 4 columns (h = 1), contents written at run time
    for name, w in (('HUD_SCORE', 4), ('HUD_CREDITS', 3), ('HUD_SHIELD', 4)):
        base = len(glyphs)
        glyphs += [bytes(64)] * (2 * w)
        table.append(dict(name=name, base=base, w=w, h=1, pal=(HUD_BANK << 4) | 15, hit=(8, 4, 1, 1)))
    assert len(glyphs) <= 512, 'pixie glyph area (512 glyphs, $48000-$4FFFF) exceeded'
    # Only non-blank glyphs are stored; the engine clears the area and copies these runs.
    blank = bytes(64)
    stored, runs, i = bytearray(), [], 0
    while i < len(glyphs):
        if glyphs[i] == blank:
            i += 1
            continue
        j = i
        while j < len(glyphs) and glyphs[j] != blank:
            j += 1
        runs.append((i, len(stored), j - i))
        stored += b''.join(glyphs[i:j])
        i = j
    assert len(runs) <= 255
    (out / 'pixies.bin').write_bytes(stored)
    rl = ['// generated by tools/import_art.py - pixie glyph runs (destination glyph, source offset, glyphs)',
          ]
    for name, f in [('pixrun_src_lo', lambda r: f'<(pixie_data+{r[1]})'), ('pixrun_src_hi', lambda r: f'>(pixie_data+{r[1]})'),
                    ('pixrun_dst_lo', lambda r: f'<((PIXIE_ADDR & $ffff)+{r[0] * 64})'),
                    ('pixrun_dst_hi', lambda r: f'>((PIXIE_ADDR & $ffff)+{r[0] * 64})'),
                    ('pixrun_len_lo', lambda r: f'<{r[2] * 64}'), ('pixrun_len_hi', lambda r: f'>{r[2] * 64}')]:
        rl.append(f'{name}: .byte ' + ','.join(f(r) for r in runs))
    (out / 'pixruns.inc').write_text('\n'.join(rl) + '\n')
    report.append(f'pixies: {len(table)} frames, {len(glyphs)} glyphs of 512')

    # ------------------------------------------------------------ HUD source data
    digits = bytearray()
    for d in hud['digits']:
        for row in d:
            v = [int(c) or 4 for c in row]                 # transparent -> backdrop
            digits += bytes(v[x] | (v[x + 1] << 4) for x in range(0, 8, 2))
    box = np.full((8, 64), 4, np.uint8)
    for y, row in enumerate(hud['icons'][2]):
        for x, c in enumerate(row):
            if int(c):
                box[y, x] = int(c)
    box[1, BAR_X0 - 1:BAR_X0 + SHIELD_MAX + 1] = 5
    box[6, BAR_X0 - 1:BAR_X0 + SHIELD_MAX + 1] = 5
    box[1:7, BAR_X0 - 1] = 5
    box[1:7, BAR_X0 + SHIELD_MAX] = 5
    box[2:6, BAR_X0:BAR_X0 + SHIELD_MAX] = 9
    template = b''.join(ph.ncm_glyph(box[:, c * 16:c * 16 + 16]) for c in range(4))
    lives = np.full((8, 16), 4, np.uint8)      # 4th score column: plane icon + lives digit (digit drawn at run time)
    for y, row in enumerate(hud['icons'][0]):
        for x, c in enumerate(row):
            if int(c):
                lives[y, x] = int(c)
    credits = np.full((8, 48), 4, np.uint8)    # credits box: '$' icon, 4 digits drawn at run time
    dollar = [r for k, r in enumerate(json.loads((ART.parent / 'bonus-capsules/source/capsules.json').read_text())['glyphs']['$'])
              if k != 3]                       # 5x9 label glyph -> 5x8 (drops a repeated row)
    for y, row in enumerate(dollar):
        for x, c in enumerate(row):
            if c == '1':
                credits[y, 1 + x] = 3
    cred = b''.join(ph.ncm_glyph(credits[:, c * 16:c * 16 + 16]) for c in range(3))
    (out / 'hud.bin').write_bytes(bytes(digits) + ph.ncm_glyph(lives) + cred + template)

    # ------------------------------------------------------------ player sprites
    spr = bytearray()
    for n in range(6):
        a = pix['player', n]
        for half in range(2):
            part = a[:, half * 16:half * 16 + 16].reshape(-1)
            spr += bytes((int(part[i]) << 4) | int(part[i + 1]) for i in range(0, len(part), 2)) + bytes(64)
    (out / 'sprite.bin').write_bytes(spr)

    # ------------------------------------------------------------ constants
    names = {t['name']: i for i, t in enumerate(table)}
    lines = ['// generated by tools/import_art.py - do not edit',
             f'.const MAP_ROWS={map_rows}', f'.const MAP_COLS={BG_COLS}',
             f'.const TILE_GLYPHS={ntiles * 2}', f'.const PIXIE_GLYPHS={len(glyphs)}',
             '.const PLAYER_FRAMES=6   // 3 left, 4 normal, 5 right (0-2 are unused alternative drawings)',
             f'.const PLAYER_STRAIGHT={PLAYER_STRAIGHT}', f'.const AIR_ANIM_FRAMES={AIR_FRAMES}',
             f'.const TANK_PHASES={TANK_PHASES}', f'.const SHIELD_MAX={SHIELD_MAX}', f'.const BAR_X0={BAR_X0}',
             f'.const HUD_GLYPH={table[names["HUD_SCORE"]]["base"]}',
             f'.const PIXIE_STORED={len(stored) // 64}', f'.const PIX_RUNS={len(runs)}',
             f'.const PAL_HUD=${(HUD_BANK << 4) | 15:02x}']
    for name, i in names.items():
        lines.append(f'.const FR_{name}={i}')
    (out / 'assets.inc').write_text('\n'.join(lines) + '\n')
    tl = ['// generated by tools/import_art.py - do not edit']
    for label, f in [('frame_base', lambda t: t['base'] & 255), ('frame_base_hi', lambda t: t['base'] >> 8),
                     ('frame_w', lambda t: t['w']), ('frame_h', lambda t: t['h']),
                     ('frame_pal', lambda t: t['pal']), ('frame_hit_cx', lambda t: t['hit'][0]),
                     ('frame_hit_cy', lambda t: t['hit'][1]), ('frame_hit_halfw', lambda t: t['hit'][2]),
                     ('frame_hit_halfh', lambda t: t['hit'][3])]:
        tl.append(f'{label}: .byte ' + ','.join(str(f(t)) for t in table))
    (out / 'frames.inc').write_text('\n'.join(tl) + '\n')

    # ------------------------------------------------------------ preview of what the engine shows
    tiles = []
    for name, p, bank, _ in frames:
        rgb = np.array([[pal[bank * 16 + v] if v else (40, 40, 48) for v in row] for row in p], np.uint8)
        tiles.append(np.pad(rgb, ((0, 32 - rgb.shape[0]), (0, 2), (0, 0)), constant_values=40))
    sheet = np.hstack(tiles)
    Image.fromarray(sheet).resize((sheet.shape[1] * 3, sheet.shape[0] * 3), Image.NEAREST).save(out / 'preview_pixies.png')
    hudimg = np.array([[pal[HUD_BANK * 16 + v] for v in row] for row in box], np.uint8)
    Image.fromarray(hudimg).resize((256, 32), Image.NEAREST).save(out / 'preview_hud.png')
    for g in ('player', 'fighter', 'bomber', 'helicopter', 'armoured_plane', 'explosion_16', 'explosion_32'):
        n = 3 if g == 'player' else 1 + max(f for (gg, f) in pix if gg == g)   # player 3-5 are poses
        shared = []
        for f in range(1, n):
            a, b = pix[g, f - 1], pix[g, f]
            both = (a > 0) | (b > 0)
            shared.append(((a == b) & both).sum() / max(1, both.sum()))
        if min(shared) < ANIM_MIN_SHARED and not g.startswith('explosion'):
            report.append(f'WARNING {g}: consecutive frames share only {min(shared):.0%}-{max(shared):.0%} of their pixels '
                          '- separate drawings, not animation phases')
    (out / 'import_report.txt').write_text('\n'.join(report) + '\n')
    print('artwork v2: ' + '; '.join(report))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'build/gen')
