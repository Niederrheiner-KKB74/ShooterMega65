#!/usr/bin/env python3
"""Import the artwork v2 package (assets/art/spec-v2, PR #4) into the engine's data formats.

Reads the indexed pixel data (indexed-source.json), the palettes (manifest.json) and the
example level (level-example.json + terrain.ncm.bin). Writes into build/gen/:

  tiles.bin      landscape NCM glyphs (tile t: glyph 2t = upper half, 2t+1 = lower half)
  map.bin        MAP_ROWS x 21 glyph offsets, glyph row 0 = level start (bottom)
  mapcol.bin     MAP_ROWS x 21 colour-RAM byte 1 (palette bank << 4 | $0f)
  PIXIES         all pixie frames, column stacks with blank guards (+ HUD glyph area): file for the D81
  sprite.bin     6 player frame pairs, 512 bytes each (2 x 192 + padding)
  ring.bin       invulnerability ring, 3 sprites x 256 bytes (48x24, colour indices 1-6)
  palette.bin    text palette 0 (R/G/B planes, nibble-swapped), sprpal.bin sprite palette
  hud.bin        HUD source data: 10 digit half-glyphs (32 bytes), lives glyph template (64 bytes),
                 credits box (192 bytes), shield box template (256 bytes), bombs/invulnerability box (192 bytes)
  assets.inc     constants, frames.inc frame tables, previews

Palette banks (text palette 0): 0 C64 colours, 1-4 landscape, 5-8 air enemies,
9 player shot, 10 red enemy shot, 11 fire shot, 12 HUD + bonus + placeholder tank,
13 rocket, 14 small explosion, 15 big explosion. The tank (assets/art/ground-vehicles, PR #6)
uses the fixed_targets landscape palette (bank 4), as delivered. All 15 banks are in use; groups that
have to share a bank later (e.g. the orange/green weapon shots) are merged by
merge_bank(): above 15 colours it reduces them (median cut) and remaps every pixel.
"""
import json
import math
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
# placeholder HUD icons (HUD palette indices), 8x8: bomb and invulnerability (shop items, Stage 3b)
HUD_BOMB = ['....3.3.', '.....3..', '...55...', '..5555..', '.555555.', '.525555.', '.555555.', '..5555..']
HUD_INVULN = ['7777777.', '7222227.', '7222227.', '7222227.', '.72227..', '.72227..', '..727...', '...7....']
ROCKET_VIEWS = ROOT / 'assets/art/rocket-directions/generated'
BOSS = ROOT / 'assets/art/boss-level1/generated'
BOSS2 = ROOT / 'assets/art/boss-level2/generated'   # PR #17 (Stage 9)
BOSS_BANK = 5                # boss palette replaces the fighter palette while the boss is on screen
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
VIEWS = ROOT / 'assets/art/enemy-views/generated'
VIEW_DIRS = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']
VIEW_BANK = ['straight', 'left', 'right']
PIXIE_MAX = 576              # pixie glyph area $46800-$4F7FF (src/layout.asm); the last 32 glyphs ($4F800-$4FFFF)
                             # hold destroyed landscape tiles (Stage 8, build_level.py)
PLAYER_STRAIGHT = 0          # straight flight cycles frames 0-2; 3 = left, 5 = right
ANIM_MIN_SHARED = 0.6        # report frame sets whose consecutive frames share less than this
CAPSULES = ROOT / 'assets/art/bonus-capsules/generated'
GROUND_TARGETS = ROOT / 'assets/art/ground-targets/generated'   # PR #15: guns (destroyed tiles: build_level.py)
GUN_DIRS = ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']          # engine direction 0-7 (as vec_dir)
PIXIE2_ADDR = 0x52800        # second pixie area (Stage 8): heavy gun, file PIXIES2 (src/layout.asm)
PIXIE2_MAX = 96
PIXIE_ADDR = 0x46800
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

    # aircraft (PR #13): fighter/helicopter 8 directions N, NE … NW, bomber/armoured plane straight/left/right,
    # 3 effect phases each, in the source palette of spec-v2 -> through the bank remap of that group
    views = json.loads((VIEWS / 'indexed-source.json').read_text())
    air_extra = []
    for const, group in AIR:
        bank, m = remap[group]
        poses = []
        for v in views:
            if v['group'] != group:
                continue
            if v['pose'] not in poses:
                poses.append(v['pose'])
            a = np.frombuffer(bytes.fromhex(''.join(v['rows'])), np.uint8).reshape(v['height'], v['width'])
            add(f'{const}_{poses.index(v["pose"])}_{v["phase"]}', m[a], bank)
        assert poses in (VIEW_DIRS, VIEW_BANK), f'{group}: unexpected poses {poses}'
        default = poses.index('south' if poses == VIEW_DIRS else 'straight')
        air_extra += [(f'{const}0', f'{const}_{default}_0'), (f'{const}_DIR0', f'{const}_0_0')]
    # player shots (Stage 8b): one object per volley, the number of bolts shows the shot level:
    # PSHOT1 one bolt, PSHOT2 two, PSHOT3 three, PSHOT4 a thick bar (16x16). Built from the bolt of PR #4.
    shot, sbank = grp('player_shot_blue', 0)
    bolt = shot[:7, 6:9]                                    # 3 x 7 pixels
    for n, xs in ((1, [6]), (2, [2, 10]), (3, [1, 6, 11])):
        a = np.zeros((8, 16), np.uint8)
        for x0 in xs:
            a[:7, x0:x0 + 3] = bolt
        add(f'PSHOT{n}', a, sbank)
    bar = np.zeros((16, 16), np.uint8)
    for y in range(14):                                     # 5 px wide (bolt: 3), 14 high (Stage 9: was 8 wide)
        row = bolt[min(6, y // 2)]
        bar[y, 5] = row[0]
        bar[y, 6:9] = row[1]
        bar[y, 9] = row[2]
    bar[2:12, 7] = bolt[3, 1] if bolt[3, 1] else bolt[2, 1]     # bright core
    add('PSHOT4', bar, sbank)
    add('ESHOT_RED', *grp('enemy_shot_red', 0))
    add('ESHOT_FIRE', *grp('enemy_shot_fire', 0))
    add('ROCKET', *grp('rocket', 0))
    # homing missile, 8 directions (up, then clockwise in 45 degree steps): the upward rocket and the
    # 45 degree view of PR #11, the others by lossless 90 degree rotations; colours through the rocket remap
    rbank, rmap = remap['rocket']
    views = {v['id']: np.frombuffer(bytes.fromhex(''.join(v['rows'])), np.uint8).reshape(16, 16)
             for v in json.loads((ROCKET_VIEWS / 'indexed-source.json').read_text())}
    assert (views['rocket_up'] == pix['rocket', 0]).all(), 'rocket views: upward view differs from the game rocket'
    up, d45 = views['rocket_up'], views['rocket_right45']
    for n, a in enumerate((up, d45, np.rot90(up, -1), np.rot90(d45, -1), np.rot90(up, 2), np.rot90(d45, 2),
                           np.rot90(up, 1), np.rot90(d45, 1))):
        add(f'MS{n}', rmap[np.ascontiguousarray(a)], rbank)
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
    # ground guns (PR #15), palette fixed_targets (bank 4): light gun 16x16 here; heavy gun 32x32 in PIXIES2
    gt = json.loads((GROUND_TARGETS / 'ground-targets.json').read_text())

    def gt_frame(rows):
        return np.array([[int(ch, 16) for ch in r] for r in rows], np.uint8)
    lg, hg = gt['ground_gun'], gt['heavy_gun']
    for n, d in enumerate(GUN_DIRS):
        add(f'GUN{n}', gt_frame(lg['frames'][d]), LAND['fixed_targets'])
    add('GUN_WRECK', gt_frame(lg['frames']['wreck']), LAND['fixed_targets'])
    for n in range(2):                                      # muzzle flash, used by both guns (Stage 8b: room for
        add(f'GUN_FLASH{n}', gt_frame(lg['frames'][f'flash{n}']), LAND['fixed_targets'])   # the shot views)

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
    for name, w in (('HUD_SCORE', 4), ('HUD_CREDITS', 3), ('HUD_SHIELD', 4), ('HUD_SPECIAL', 3)):
        base = len(glyphs)
        glyphs += [bytes(64)] * (2 * w)
        table.append(dict(name=name, base=base, w=w, h=1, pal=(HUD_BANK << 4) | 15, hit=(8, 4, 1, 1)))
    # ------------------------------------------------------------ level-1 boss (PR #14), file L1BOSS
    # The boss glyphs are swapped in over the fighter + bomber frames while the boss is on screen (no
    # fighters or bombers then). Their frame table entries point to that place already.
    names_now = {t['name']: t for t in table}
    swap0 = names_now['FIGHTER_0_0']['base'] - 1             # the blank guard before the first fighter column
    boss_frames = [('BOSS_BODY', 'body'), ('BOSS_CORE', 'core_exposed')] + \
        [(f'BOSS_ROTOR{n}', f'rotor_{n}') for n in range(3)] + \
        [(f'BOSS_T{k}_{v}', f'turret_{t}_{src}') for k, t in enumerate(('nw', 'ne', 'sw', 'se'))
         for v, src in (('S', 'south'), ('SE', 'southeast'), ('SW', 'southeast'), ('X', 'destroyed'))] + \
        [('BOSS_MUZZLE0', 'muzzle_0'), ('BOSS_MUZZLE1', 'muzzle_1')] + \
        [('BOSS_BODY_SIDE', 'body_side'), ('BOSS_CORE_SIDE', 'core_exposed_side')] + \
        [(f'BOSS_RSIDE{n}', f'rotor_side_{n}') for n in range(3)]
    # Stage 9b: a second view for bosses that drive (level 2: tracks horizontal); bosses without it get empty
    # frames of the same size. The boss area covers the fighter, bomber, helicopter and armoured-plane frames.
    side_ids = ('body_side', 'core_exposed_side', 'rotor_side_0', 'rotor_side_1', 'rotor_side_2')
    side_ref = {f['id']: (f['height'], f['width']) for f in json.loads((BOSS2 / 'indexed-source.json').read_text())
                if f['id'] in side_ids}
    swap_end = names_now['PSHOT1']['base'] - 1               # first glyph after the armoured-plane frames
    # Stage 9: one frame layout for every level's boss (the frame table is fixed); each level has its own glyphs,
    # palette and part positions. Smaller frames are padded (top left) to the size of the level-1 frame.
    boss_files, boss_place = {}, {}
    for lvl, bdir in enumerate((BOSS, BOSS2), 1):
        src = {f['id']: np.frombuffer(bytes.fromhex(''.join(f['rows'])), np.uint8).reshape(f['height'], f['width'])
               for f in json.loads((bdir / 'indexed-source.json').read_text())}
        if lvl == 1:
            ref = {sid: a.shape for sid, a in src.items()}
            ref.update(side_ref)
        for sid in side_ids:
            src.setdefault(sid, np.zeros(ref[sid], np.uint8))
        bglyphs = [bytes(64)]
        for name, sid in boss_frames:
            a = src[sid]
            if a.shape != ref[sid]:
                assert a.shape[0] <= ref[sid][0] and a.shape[1] <= ref[sid][1], f'boss {lvl} {sid} larger than level 1'
                b = np.zeros(ref[sid], np.uint8)
                b[:a.shape[0], :a.shape[1]] = a
                a = b
            if name.endswith('_SW'):
                a = a[:, ::-1]                                # south-west = mirrored south-east
            h, w = a.shape[0] // 8, a.shape[1] // 16
            base = swap0 + len(bglyphs)
            for c in range(w):
                for i in range(h):
                    bglyphs.append(ph.ncm_glyph(a[i * 8:i * 8 + 8, c * 16:c * 16 + 16]))
                bglyphs.append(bytes(64))
            if lvl == 1:
                table.append(dict(name=name, base=base, w=w, h=h, pal=(BOSS_BANK << 4) | 15, hit=hitbox(a)))
        assert swap0 + len(bglyphs) <= swap_end, f'boss {lvl} glyphs ({len(bglyphs)}) exceed the fighter/bomber area'
        bpal_raw = (bdir / 'palette.rgb').read_bytes()
        bp = [tuple(bpal_raw[i:i + 3]) for i in range(0, 48, 3)]
        if lvl == 1:
            bpal = bp
        boss_files[lvl] = b''.join(bglyphs) + bytes(ph.swap(c[ch]) for ch in range(3) for c in bp)
        (out / f'L{lvl}BOSS').write_bytes(boss_files[lvl])
        pl = json.loads((bdir / 'placement.json').read_text())
        tur = pl['turrets']
        rot = pl['rotors']
        def place(pl):
            tur, rot = pl['turrets'], pl['rotors']
            return ([t['offset'][0] for t in tur] + [pl['core']['offset'][0]] +
                    [t['offset'][1] for t in tur] + [pl['core']['offset'][1]] +
                    [r['offset'][0] for r in rot] + [r['offset'][1] for r in rot] +
                    [r.get('phase_offset', 0) for r in rot])
        boss_place[lvl] = place(pl) + place(pl.get('side', pl))    # driving down / sideways
        assert len(boss_place[lvl]) == 44, f'boss {lvl}: 4 turrets, core and 4 rotors expected'
        report.append(f'boss {lvl}: {len(bglyphs)} glyphs swapped in at glyph {swap0} (room {swap_end - swap0})')
    assert len(boss_files[1]) == len(boss_files[2])
    boss_consts = [f'.const BOSS_SWAP_GLYPH={swap0}', f'.const BOSS_GLYPHS={len(bglyphs)}',
                   f'.const BOSS_FILE_BYTES={len(bglyphs) * 64 + 48}', f'.const BOSS_BANK={BOSS_BANK}']
    # ------------------------------------------------------------ heavy gun (PR #15), file PIXIES2 at PIXIE2_ADDR
    p2base = (PIXIE2_ADDR - PIXIE_ADDR) // 64
    g2 = [bytes(64)]
    for name, rows in [(f'HGUN{n}', hg['frames'][d]) for n, d in enumerate(GUN_DIRS)] + [('HGUN_WRECK', hg['frames']['wreck'])]:
        a = gt_frame(rows)
        h, w = a.shape[0] // 8, a.shape[1] // 16
        base = p2base + len(g2)
        for c in range(w):
            for i in range(h):
                g2.append(ph.ncm_glyph(a[i * 8:i * 8 + 8, c * 16:c * 16 + 16]))
            g2.append(bytes(64))
        table.append(dict(name=name, base=base, w=w, h=h, pal=(LAND['fixed_targets'] << 4) | 15, hit=hitbox(a)))
    assert len(g2) <= PIXIE2_MAX, f'second pixie area ({PIXIE2_MAX} glyphs) exceeded: {len(g2)}'
    (out / 'PIXIES2').write_bytes(b''.join(g2))
    report.append(f'pixies2: heavy gun {len(g2)} glyphs of {PIXIE2_MAX}')
    gun_consts = [f'.const PIXIES2_BYTES={len(g2) * 64}']
    for key, pre in (('ground_gun', 'gun'), ('heavy_gun', 'hgun')):
        mz = gt[key]['muzzle']
        half = gt[key]['size'][0] // 2
        # muzzle flash (16x16) centred on the barrel tip: offset of its top left corner from the gun's
        gun_consts.append(f'{pre}_mz_x: .byte ' + ','.join(str((mz[d][0] - 8) & 0xff) for d in GUN_DIRS))
        gun_consts.append(f'{pre}_mz_y: .byte ' + ','.join(str((mz[d][1] - 8) & 0xff) for d in GUN_DIRS))
    assert len(table) <= 256, f'{len(table)} frames: frame numbers are bytes'
    assert len(glyphs) <= PIXIE_MAX, f'pixie glyph area ({PIXIE_MAX} glyphs) exceeded: {len(glyphs)}'
    # The complete glyph image (blank guards included) is a file on the disk (PIXIES), loaded to PIXIE_ADDR.
    (out / 'PIXIES').write_bytes(b''.join(glyphs))
    report.append(f'pixies: {len(table)} frames, {len(glyphs)} glyphs of {PIXIE_MAX}')

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
    special = np.full((8, 48), 4, np.uint8)    # bombs + invulnerability: icon at x 0 / 24, digit at x 8 / 32
    for x0, icon in ((0, HUD_BOMB), (24, HUD_INVULN)):
        for y, row in enumerate(icon):
            for x, c in enumerate(row):
                if c != '.':
                    special[y, x0 + x] = int(c)
    spec = b''.join(ph.ncm_glyph(special[:, c * 16:c * 16 + 16]) for c in range(3))
    (out / 'hud.bin').write_bytes(bytes(digits) + ph.ncm_glyph(lives) + cred + template + spec)

    # ------------------------------------------------------------ player sprites
    spr = bytearray()
    for n in range(6):
        a = pix['player', n]
        for half in range(2):
            part = a[:, half * 16:half * 16 + 16].reshape(-1)
            spr += bytes((int(part[i]) << 4) | int(part[i + 1]) for i in range(0, len(part), 2)) + bytes(64)
    (out / 'sprite.bin').write_bytes(spr)
    # invulnerability ring (Stage 4): 48x24 ellipse outline for sprites 2-4, colour indices 1-6 by angle,
    # cycled at run time (palette 1 entries $21-$26, $31-$36, $41-$46). Left pixel in the high nibble.
    ring = np.zeros((24, 48), np.uint8)
    for y in range(24):
        for x in range(48):
            dx, dy = (x - 23.5) / 23.5, (y - 11.5) / 11.5
            r = math.hypot(dx, dy)
            if 0.84 <= r <= 1.0:
                ang = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                ring[y, x] = int(ang * 12) % 6 + 1
    rb = bytearray()
    for k in range(3):
        part = ring[:, k * 16:k * 16 + 16].reshape(-1)
        rb += bytes((int(part[i]) << 4) | int(part[i + 1]) for i in range(0, len(part), 2)) + bytes(64)
    (out / 'ring.bin').write_bytes(rb)

    # ------------------------------------------------------------ constants
    names = {t['name']: i for i, t in enumerate(table)}
    lines = ['// generated by tools/import_art.py - do not edit',
             f'.const MAP_ROWS={map_rows}', f'.const MAP_COLS={BG_COLS}',
             f'.const TILE_GLYPHS={ntiles * 2}', f'.const PIXIE_GLYPHS={len(glyphs)}',
             '.const PLAYER_FRAMES=6   // 3 left, 4 normal, 5 right (0-2 are unused alternative drawings)',
             f'.const PLAYER_STRAIGHT={PLAYER_STRAIGHT}', f'.const AIR_ANIM_FRAMES={AIR_FRAMES}',
             f'.const TANK_PHASES={TANK_PHASES}', f'.const SHIELD_MAX={SHIELD_MAX}', f'.const BAR_X0={BAR_X0}',
             f'.const HUD_GLYPH={table[names["HUD_SCORE"]]["base"]}',
             f'.const PAL_HUD=${(HUD_BANK << 4) | 15:02x}']
    lines += boss_consts + gun_consts[:1]
    for name, i in names.items():
        lines.append(f'.const FR_{name}={i}')
    for alias, name in air_extra:
        lines.append(f'.const FR_{alias}={names[name]}')
    (out / 'assets.inc').write_text('\n'.join(lines) + '\n')
    tl = ['// generated by tools/import_art.py - do not edit']
    # absolute character numbers (PIXIE_CHAR + glyph index): the pixie area need not start on a 256-char boundary
    for label, f in [('frame_base', lambda t: f'<(PIXIE_CHAR+{t["base"]})'),
                     ('frame_base_hi', lambda t: f'>(PIXIE_CHAR+{t["base"]})'),
                     ('frame_w', lambda t: t['w']), ('frame_h', lambda t: t['h']),
                     ('frame_pal', lambda t: t['pal']), ('frame_hit_cx', lambda t: t['hit'][0]),
                     ('frame_hit_cy', lambda t: t['hit'][1]), ('frame_hit_halfw', lambda t: t['hit'][2]),
                     ('frame_hit_halfh', lambda t: t['hit'][3])]:
        tl.append(f'{label}: .byte ' + ','.join(str(f(t)) for t in table))
    # boss hit flash (Stage 7b): the boss palette lightened towards white, loaded into bank 6 during the fight
    flash = [tuple(min(255, int(v + (255 - v) * 0.65)) for v in c) for c in bpal]
    tl += gun_consts[1:]
    # boss part positions per level (Stage 9): part_dx[5], part_dy[5], rotor_dx[4], rotor_dy[4], rotor_ph[4]
    for lvl in (1, 2):
        tl.append(f'boss_place{lvl}: .byte ' + ','.join(str(v) for v in boss_place[lvl]))
    tl.append('boss_flash_pal: .byte ' + ','.join(str(ph.swap(c[ch])) for ch in range(3) for c in flash))
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
