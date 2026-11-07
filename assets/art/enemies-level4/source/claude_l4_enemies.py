#!/usr/bin/env python3
"""Level-4 enemies drawn by Claude (Stage 14g, owner's wish: one consistent set in the style of level 1).

Grey steel with red accents and orange/yellow lights like the level-1 fighters (which level 4 keeps):
  attack_heli  16x16, 8 directions x 3 rotor phases     (helicopter slots, palette `heli`)
  gunship      32x32, straight/left/right x 3 phases     (bomber slots, palette `gunship`; an original sleek
                                                          attack helicopter with tandem cockpit and stub wings)
  mech         16x16, 4 directions x 4 walk phases        (tank slots, palette `mechs`; a small four-legged mech)
  walker       32x32, south x 4 walk phases + wreck      (armoured-plane slots, palette `mechs`)
Drawn as vector shapes (tools/pixel_vector.py) and rasterised per direction, so diagonal views stay clean.

    python3 assets/art/enemies-level4/source/claude_l4_enemies.py

rewrites ../generated/indexed-source.json, palettes.json, placement.json and writes ../generated/l4-enemies.png.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
from pixel_vector import Canvas, DIRS8, rows  # noqa: E402

GEN = Path(__file__).resolve().parents[1] / 'generated'
BASE = [(0, 0, 0), (14, 14, 20), (46, 50, 60), (84, 90, 102), (124, 130, 142), (172, 178, 188),
        (224, 228, 234), (118, 22, 20), (190, 40, 32), (238, 84, 62), (248, 150, 40), (255, 222, 96),
        (28, 58, 90), (66, 134, 196), (170, 220, 255), (150, 156, 166)]
PALS = {
    'heli': BASE,
    # the gunship a little darker (charcoal), red brighter
    'gunship': BASE[:2] + [(36, 38, 46), (62, 66, 78), (98, 104, 118), (150, 156, 170), (208, 212, 222)] +
    [(126, 18, 18), (206, 36, 28), (250, 90, 60)] + BASE[10:],
    # the mechs: steel blue-grey with red and orange
    'mechs': BASE[:2] + [(44, 52, 64), (78, 90, 106), (116, 130, 148), (164, 178, 194), (218, 226, 236)] +
    BASE[7:],
}
STEEL, DARK, LIGHT, RED, GLASS = (3, 4, 5), (2, 3, 4), (4, 5, 6), (7, 8, 9), (12, 13, 14)
BLUR, OUT = 15, 1


def heli(angle, phase):
    c = Canvas(16, 16)
    c.capsule(-4.6, 0.6, 4.6, 0.6, 0.9, DARK)              # stub wings
    c.capsule(-4.6, -0.2, -4.6, 1.8, 0.8, RED)             # rocket pods
    c.capsule(4.6, -0.2, 4.6, 1.8, 0.8, RED)
    c.capsule(0, -1, 0, -6.6, 0.9, STEEL)                  # tail boom
    c.capsule(-1.8, -6.4, 1.8, -6.4, 0.6, DARK)            # tail plane
    c.ellipse(0, 1.4, 2.8, 4.5, STEEL)                     # fuselage
    c.line(-1.9, -1.1, 1.9, -1.1, 8)                       # red band
    c.ellipse(0, 3.6, 1.6, 1.9, GLASS)                     # canopy
    c.dot(0, 6.2, 1)                                       # chin gun
    a = phase * 60 + 20                                    # rotor: one blade pair, 60 deg per phase, blurred
    b = math.radians(a)
    c.line(-math.cos(b) * 7.4, -math.sin(b) * 7.4, math.cos(b) * 7.4, math.sin(b) * 7.4, BLUR, dash=1.5)
    c.dot(0, 0, 6)
    return c.render(angle)


def gunship(roll, phase):
    c = Canvas(32, 32)
    c.capsule(-9.5, 0.5, 9.5, 0.5, 1.4, STEEL)                    # stub wings
    for s in (-1, 1):
        c.capsule(s * 8.5, -1.6, s * 8.5, 3.2, 1.3, RED)          # rocket pods
        c.dot(s * 8.5, 4.3, 11)
        c.dot(s * 10.8, 0.5, 9 if s < 0 else 13)                  # wing tip lights
    c.capsule(0, -3, 0, -14, 1.5, DARK)                           # tail boom
    c.capsule(-4.5, -13.2, 4.5, -13.2, 1.0, DARK)                 # tail plane
    c.line(4.6, -15.5, 4.6, -11, BLUR)                            # tail rotor (edge on)
    for s in (-1, 1):
        c.capsule(s * 3.3, -0.5, s * 3.3, -5.5, 1.5, STEEL)       # engine nacelles
        c.dot(s * 3.3, -7.0, 10)                                  # exhaust glow
    c.poly([(0, 10.5), (3.1, 6.5), (3.5, 0.5), (2.8, -4.5), (1.6, -6.5), (-1.6, -6.5), (-2.8, -4.5),
            (-3.5, 0.5), (-3.1, 6.5)], DARK)                     # fuselage, pointed nose
    c.line(-3.0, -2.6, 3.0, -2.6, 8)                              # red band
    c.line(-2.6, -3.4, 2.6, -3.4, 7)
    c.ellipse(0, 5.4, 1.8, 2.5, GLASS)                            # tandem canopy
    c.ellipse(0, 1.8, 1.6, 1.8, GLASS)
    c.capsule(0, 10, 0, 12.6, 0.6, DARK)                          # chin cannon
    c.dot(0, 13.3, 1)
    a = phase * 30 + 10                                           # main rotor: 4 blades
    for k in (0, 90):
        b = math.radians(a + k)
        c.line(-math.cos(b) * 14.5, -math.sin(b) * 14.5 + 0.5, math.cos(b) * 14.5,
               math.sin(b) * 14.5 + 0.5, BLUR, dash=2)
    c.dot(0, 0.5, 6)
    light = {0: (-1, -1), -1: (-1.6, -0.6), 1: (-0.4, -1.2)}[roll]
    return c.render(0, light=light, roll=roll)


def quad_legs(c, step, hip, foot, rleg, rfoot):
    """four legs, diagonal pairs move together; step 0-3"""
    off = [-1, 0, 1, 0][step]
    for sx, sy, pair in ((-1, -1, 0), (1, 1, 0), (1, -1, 1), (-1, 1, 1)):
        dy = off if pair == 0 else -off
        hx, hy = sx * hip[0], sy * hip[1]
        fx, fy = sx * foot[0], sy * foot[1] + dy * foot[2]
        kx, ky = (hx + fx) / 2 + sx * foot[3], (hy + fy) / 2
        c.capsule(hx, hy, kx, ky, rleg, DARK)
        c.capsule(kx, ky, fx, fy, rleg * 0.85, STEEL)
        lifted = (pair == 0 and step == 1) or (pair == 1 and step == 3)
        c.ellipse(fx, fy, rfoot * (1.15 if lifted else 1), rfoot * (1.15 if lifted else 1),
                  LIGHT if lifted else STEEL)


def mech(angle, step):
    c = Canvas(16, 16)
    quad_legs(c, step, (2.2, 2.2), (5.3, 5.2, 0.9, 0.6), 0.75, 1.15)
    c.ellipse(0, 0, 3.4, 3.8, STEEL)                       # hull
    c.capsule(-1.0, 1.0, -1.0, 6.4, 0.55, DARK)            # twin cannons forward
    c.capsule(1.0, 1.0, 1.0, 6.4, 0.55, DARK)
    c.ellipse(0, -0.4, 2.0, 2.0, LIGHT)                    # turret
    c.dot(0, 1.4, 9)                                       # red sensor
    c.dot(-2.4, -2.6, 10)                                  # lights
    c.dot(2.4, -2.6, 10)
    return c.render(angle)


def walker(step, wreck=False):
    c = Canvas(32, 32)
    if wreck:
        quad_legs(c, 0, (5.5, 5.0), (11.5, 10.5, 1.5, 1.6), 1.6, 2.2)
    else:
        quad_legs(c, step, (5.5, 5.0), (11.5, 10.5, 1.5, 1.6), 1.6, 2.2)
    hull = STEEL if not wreck else DARK
    c.poly([(-6.5, -6), (6.5, -6), (8, -2), (8, 5), (5, 8.5), (-5, 8.5), (-8, 5), (-8, -2)], hull)
    for s in (-1, 1):
        c.capsule(s * 7.2, -3.5, s * 7.2, 4.5, 0.8, RED if not wreck else DARK)   # side armour stripes
        c.dot(s * 4.2, 8.0, 11 if not wreck else 2)                             # headlights
    c.line(-3.5, 6.6, 3.5, 6.6, 13 if not wreck else 2)                          # sensor slit
    c.ellipse(0.5, -1.5, 5.4, 5.4, (2, 2, 3), shade=False)                       # turret ring (gun on top)
    c.ellipse(0.5, -1.5, 4.3, 4.3, DARK)
    img = c.render(0)
    if wreck:
        rng = np.random.default_rng(14)
        for x, y in ((12, 11), (19, 17), (14, 20), (21, 9)):
            for k in range(9):
                yy, xx = y + rng.integers(-2, 2), x + rng.integers(-2, 3)
                if img[yy, xx]:
                    img[yy, xx] = (10, 11, 9, 8)[k % 4]
    return img


def main():
    frames = []
    for d, ang in DIRS8.items():
        for n in range(3):
            frames.append(('attack_heli', d, n, 'heli', heli(ang, n)))
    for pose, roll in (('straight', 0), ('left', -1), ('right', 1)):
        for n in range(3):
            frames.append(('gunship', pose, n, 'gunship', gunship(roll, n)))
    for d in ('north', 'east', 'south', 'west'):
        for n in range(4):
            frames.append(('mech', d, n, 'mechs', mech(DIRS8[d], n)))
    for n in range(4):
        frames.append(('walker', 'south', n, 'mechs', walker(n)))
    frames.append(('walker', 'destroyed', 0, 'mechs', walker(0, True)))
    src = [{'group': g, 'pose': p, 'phase': n, 'width': a.shape[1], 'height': a.shape[0], 'palette': pal,
            'rows': rows(a)} for g, p, n, pal, a in frames]
    (GEN / 'indexed-source.json').write_text(json.dumps(src, indent=1) + '\n')
    (GEN / 'palettes.json').write_text(json.dumps({k: [list(c) for c in v] for k, v in PALS.items()}, indent=1) + '\n')
    (GEN / 'placement.json').write_text(json.dumps({'walker': {'guns': [[8, 6]]}}, indent=1) + '\n')
    # preview: 4x on dark and light ground
    z = 4
    W = 640
    img = Image.new('RGB', (W * z // 2 + 40, 20 * 40 * z // 4), (40, 44, 48))
    x = y = 0
    rowh = 0
    for g, p, n, pal, a in frames:
        h, w = a.shape
        if x + w + 4 > W // 2:
            x, y = 0, y + rowh + 4
            rowh = 0
        for yy in range(h):
            for xx in range(w):
                if a[yy, xx]:
                    img.paste(PALS[pal][a[yy, xx]], ((x + xx) * z, (y + yy) * z, (x + xx + 1) * z, (y + yy + 1) * z))
        x += w + 4
        rowh = max(rowh, h)
    img = img.crop((0, 0, img.width, (y + rowh + 4) * z))
    img.save(GEN / 'l4-enemies.png')
    print(f'{len(frames)} frames written')


if __name__ == '__main__':
    main()
