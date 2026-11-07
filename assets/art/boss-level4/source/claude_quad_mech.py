#!/usr/bin/env python3
"""Final boss of level 4: a heavy four-legged mech (Stage 14g, drawn by Claude at the owner's request).

Seen from above, symmetric, so it can walk in all four directions without turning: an armoured hull with four
gun turrets, a reactor hatch in the middle (`core_exposed`), four thighs to the corners and four feet (the
`rotors`: they step in diagonal pairs only while it walks), a flame thrower at the front, a missile rack on the
back (the `catapult`: missiles start from it and fly at the player), dust under the feet. Same colours as the
level-4 enemies (steel, red, orange lights).

    python3 assets/art/boss-level4/source/claude_quad_mech.py

writes ../generated/indexed-source.json, palette.rgb, placement.json and boss-preview.png.
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
PAL = [(0, 0, 0), (14, 14, 20), (44, 52, 64), (78, 90, 106), (116, 130, 148), (164, 178, 194),
       (218, 226, 236), (118, 22, 20), (190, 40, 32), (238, 84, 62), (248, 150, 40), (255, 222, 96),
       (120, 104, 80), (184, 168, 134), (90, 220, 255), (255, 255, 240)]
STEEL, DARK, LIGHT, RED = (3, 4, 5), (2, 3, 4), (4, 5, 6), (7, 8, 9)
BW, BH = 96, 64


def body():
    c = Canvas(BW, BH)
    for sx in (-1, 1):                                     # thighs to the corners (feet are separate frames)
        for sy in (-1, 1):
            c.capsule(sx * 16, sy * 10, sx * 33, sy * 17, 4.2, DARK)
            c.capsule(sx * 16, sy * 10, sx * 33, sy * 17, 2.2, STEEL)
            c.ellipse(sx * 17, sy * 11, 4.5, 4.5, LIGHT)  # hip joints
            c.dot(sx * 17, sy * 11, 7)
    c.poly([(-20, -22), (20, -22), (28, -12), (28, 14), (18, 24), (-18, 24), (-28, 14), (-28, -12)], STEEL)
    c.poly([(-15, -17), (15, -17), (21, -9), (21, 10), (14, 18), (-14, 18), (-21, 10), (-21, -9)], DARK)
    for sx in (-1, 1):
        c.capsule(sx * 25, -8, sx * 25, 10, 1.2, RED)      # red side armour stripes
        c.dot(sx * 9, 21.5, 11)                             # headlights
        c.dot(sx * 12, 21.5, 10)
    c.line(-6, 21.5, 6, 21.5, 14)                           # sensor slit
    c.ellipse(0, 0, 14.5, 14.5, (2, 2, 3), shade=False)     # hatch ring around the reactor (core 32x32)
    c.ellipse(0, 0, 12.5, 12.5, LIGHT)                      # closed hatch
    c.line(-12, 0, 12, 0, 2)
    c.line(0, -12, 0, 12, 2)
    c.capsule(-6, -25, 6, -25, 2.6, DARK)                   # missile rack on the back
    for k in range(-2, 3):
        c.dot(k * 2.4, -25, 8)
    return c.render(0)


def foot(phase):
    """foot pad with ankle; phase 0 planted, 1 lifting (larger, lighter), 2 coming down"""
    c = Canvas(32, 32)
    k = (1.0, 1.25, 1.1)[phase]
    ramp = (STEEL, LIGHT, STEEL)[phase]
    c.ellipse(0, 0, 9 * k, 9 * k, DARK)
    c.ellipse(0, 0, 7 * k, 7 * k, ramp)
    for a in (0, 90, 180, 270):                             # claws
        b = math.radians(a + 45)
        c.capsule(math.cos(b) * 6 * k, math.sin(b) * 6 * k, math.cos(b) * 11 * k, math.sin(b) * 11 * k,
                  1.6, DARK)
    c.ellipse(0, 0, 3.2, 3.2, RED)
    c.dot(0, 0, 10)
    img = c.render(0)
    if phase == 0:                                          # planted: a dark contact ring
        h, w = img.shape
        for y in range(h):
            for x in range(w):
                if img[y, x] == 0 and 10.5 < math.hypot(x - 15.5, y - 15.5) < 11.5 and (x + y) % 2:
                    img[y, x] = 12
    return img


def turret(angle, destroyed=False):
    c = Canvas(16, 16)
    if destroyed:
        c.ellipse(0, 0, 6, 6, DARK)
        c.capsule(-3, -2, 2, 3, 1.0, (1, 2, 2))
        c.dot(-1, 1, 10)
        c.dot(2, -2, 9)
        return c.render(0)
    c.ellipse(0, 0, 6.2, 6.2, STEEL)
    c.capsule(-1.5, 1, -1.5, 7.2, 0.9, DARK)                # twin barrels
    c.capsule(1.5, 1, 1.5, 7.2, 0.9, DARK)
    c.ellipse(0, -0.5, 3.4, 3.4, LIGHT)
    c.dot(0, -0.5, 8)
    return c.render(angle)


def core():
    c = Canvas(32, 32)
    c.ellipse(0, 0, 14.5, 14.5, (2, 2, 3), shade=False)
    c.ellipse(0, 0, 12.5, 12.5, (1, 2, 2))                  # open hatch: dark shaft
    c.ellipse(0, 0, 9, 9, (8, 9, 10), shade=True)           # glowing reactor
    c.ellipse(0, 0, 5.5, 5.5, (10, 11, 15))
    c.ellipse(0, 0, 2.5, 2.5, (15, 15, 15), shade=False)
    for a in range(0, 360, 45):
        b = math.radians(a)
        c.line(math.cos(b) * 10.5, math.sin(b) * 10.5, math.cos(b) * 12.5, math.sin(b) * 12.5, 4)
    return c.render(0)


def muzzle(n):
    c = Canvas(16, 16)
    r = (4.5, 3.2)[n]
    c.ellipse(0, 2, r, r + 1.5, (8, 10, 11), outline=False)
    c.ellipse(0, 1.5, r * 0.5, r * 0.7, (11, 15, 15), shade=False, outline=False)
    return c.render(0)


def flame(n):
    img = np.zeros((32, 16), np.uint8)
    length = (12, 31, 22)[n]
    rng = np.random.default_rng(40 + n)
    for y in range(length):
        w = 1.5 + y * (0.18 if n != 2 else 0.12)
        for x in range(16):
            d = abs(x - 7.5)
            if d <= w + rng.random() * 0.8:
                t = d / (w + 0.01)
                img[y, x] = 15 if t < 0.3 and y < length - 4 else (11 if t < 0.6 else (10 if t < 0.85 else 9))
    return img


def spray(n):
    img = np.zeros((16, 32), np.uint8)
    rng = np.random.default_rng(70 + n)
    for k in range(60 + 15 * n):
        a = rng.random() * math.pi
        r = rng.random() * (8 + 3 * n)
        x, y = int(15.5 + math.cos(a) * r * 1.6), int(12 - math.sin(a) * r * 0.7)
        if 0 <= x < 32 and 0 <= y < 16:
            img[y, x] = 13 if rng.random() < 0.55 else 12
    return img


def missile(n):
    c = Canvas(16, 16)
    c.capsule(0, -4.5, 0, 4.5, 1.6, STEEL)
    c.poly([(0, 6.8), (1.7, 3.8), (-1.7, 3.8)], RED)
    for s in (-1, 1):
        c.capsule(s * 1.2, -4.5, s * 3.0, -6, 0.6, DARK)
    if n >= 1:
        c.ellipse(0, -7.0, 1.4, 1.8 + n, (10, 11, 15), outline=False)
    return c.render(0)


def main():
    frames = [('body', body()), ('core_exposed', core())]
    frames += [(f'rotor_{n}', foot(n)) for n in range(3)]
    for t in ('nw', 'ne', 'sw', 'se'):
        frames += [(f'turret_{t}_south', turret(DIRS8['south'])),
                   (f'turret_{t}_southeast', turret(DIRS8['southeast'])),
                   (f'turret_{t}_destroyed', turret(0, True))]
    frames += [(f'muzzle_{n}', muzzle(n)) for n in range(2)]
    frames += [(f'flame_{n}', flame(n)) for n in range(3)]
    frames += [(f'spray_{n}', spray(n)) for n in range(3)]
    frames += [(f'deck_jet_{n}', missile(n)) for n in range(3)]
    src = [{'id': i, 'width': a.shape[1], 'height': a.shape[0], 'rows': rows(a)} for i, a in frames]
    (GEN / 'indexed-source.json').write_text(json.dumps(src, indent=1) + '\n')
    (GEN / 'palette.rgb').write_bytes(bytes(v for c in PAL for v in c))
    tpos = {'nw': [22, 10], 'ne': [58, 10], 'sw': [22, 38], 'se': [58, 38]}
    pl = {
        'body': 'body', 'body_size': [BW, BH], 'palette': 'boss',
        'turrets': [{'id': f'turret_{t}', 'offset': tpos[t], 'size': [16, 16], 'south': f'turret_{t}_south',
                     'southeast': f'turret_{t}_southeast', 'destroyed': f'turret_{t}_destroyed'} for t in tpos],
        'core': {'offset': [32, 16], 'size': [32, 32], 'exposed_overlay': 'core_exposed'},
        'rotors': [{'id': 'foot_nw', 'offset': [0, 0], 'phase_offset': 0},
                   {'id': 'foot_ne', 'offset': [64, 0], 'phase_offset': 1},
                   {'id': 'foot_sw', 'offset': [0, 40], 'phase_offset': 1},
                   {'id': 'foot_se', 'offset': [64, 40], 'phase_offset': 0}],
        'rotor_frames': ['rotor_0', 'rotor_1', 'rotor_2'],
        'muzzle': {'frames': ['muzzle_0', 'muzzle_1'], 'south_offset_from_turret': [0, 15]},
        'flame': {'frames': ['flame_0', 'flame_1', 'flame_2'], 'offset': [40, 56]},
        'spray': {'frames': ['spray_0', 'spray_1', 'spray_2'], 'offsets': [[0, 60], [64, 60], [0, 8], [64, 8]]},
        'catapult': {'frames': ['deck_jet_0', 'deck_jet_1', 'deck_jet_2'], 'offset': [40, 0]},
    }
    (GEN / 'placement.json').write_text(json.dumps(pl, indent=1) + '\n')
    # composed preview: body, feet (phase per foot), turrets, then core open + flame
    z = 4
    big = np.zeros((96, 128), np.uint8)

    def blit(a, x, y):
        h, w = a.shape
        for yy in range(h):
            for xx in range(w):
                if a[yy, xx] and 0 <= y + yy < big.shape[0] and 0 <= x + xx < big.shape[1]:
                    big[y + yy, x + xx] = a[yy, xx]
    fr = dict(frames)
    for side, open_core in ((0, False), (1, True)):
        big[:] = 0
        blit(fr['body'], 16, 4)
        for r, ph in zip(pl['rotors'], (0, 1, 1, 0)):
            blit(fr[f'rotor_{ph}'], 16 + r['offset'][0], 4 + r['offset'][1])
        for t in pl['turrets']:
            blit(fr[t['destroyed'] if open_core else t['south']], 16 + t['offset'][0], 4 + t['offset'][1])
        if open_core:
            blit(fr['core_exposed'], 16 + 32, 4 + 16)
            blit(fr['flame_1'], 16 + 40, 4 + 56)
        img = Image.new('RGB', (128 * z, 96 * z), (52, 54, 60))
        for y in range(96):
            for x in range(128):
                if big[y, x]:
                    img.paste(PAL[big[y, x]], (x * z, y * z, x * z + z, y * z + z))
        img.save(GEN / ('boss-preview.png' if side == 0 else 'boss-preview-core.png'))
    print(f'{len(frames)} boss frames written')


if __name__ == '__main__':
    main()
