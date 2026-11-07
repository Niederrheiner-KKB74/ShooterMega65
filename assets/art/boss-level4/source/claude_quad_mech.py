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
BW, BH = 112, 64
LEG_X = (0, 80)          # left / right leg frames (32 wide): beside the hull
LEG_Y = (0, 24)          # rear / front legs
HIP = (16, 7)            # hip joint inside a leg frame


def body():
    """hull 64 wide in the middle of the 112-px frame; struts and hip housings out to the legs, which are
    drawn before the body (boss.asm) so the housings cover the leg tops"""
    c = Canvas(BW, BH)
    for lx in LEG_X:
        for ly in LEG_Y:
            hx, hy = lx + HIP[0] - (BW - 1) / 2, ly + HIP[1] - (BH - 1) / 2
            sx = -1 if lx == 0 else 1
            c.capsule(hx, hy, hx - sx * 14, hy, 3.4, DARK)          # strut to the hull
            c.ellipse(hx, hy, 6.0, 5.2, STEEL)                      # hip housing
            c.ellipse(hx, hy, 2.6, 2.4, RED)
            c.dot(hx, hy, 10)
    c.poly([(-22, -30), (22, -30), (31, -20), (31, 18), (21, 29), (-21, 29), (-31, 18), (-31, -20)], STEEL)
    c.poly([(-17, -25), (17, -25), (25, -16), (25, 14), (16, 23), (-16, 23), (-25, 14), (-25, -16)], DARK)
    for sx in (-1, 1):
        c.capsule(sx * 28, -14, sx * 28, 12, 1.2, RED)       # red side armour stripes
        c.dot(sx * 9, 27, 11)                                 # headlights
        c.dot(sx * 12, 27, 10)
    c.line(-6, 27, 6, 27, 14)                                 # sensor slit
    c.ellipse(0, 0, 14.5, 14.5, (2, 2, 3), shade=False)      # hatch ring around the reactor (core 32x32)
    c.ellipse(0, 0, 12.5, 12.5, LIGHT)                       # closed hatch
    c.line(-12, 0, 12, 0, 2)
    c.line(0, -12, 0, 12, 2)
    c.capsule(-6, -28, 6, -28, 2.4, DARK)                    # missile rack on the back
    for k in range(-2, 3):
        c.dot(k * 2.4, -28, 8)
    return c.render(0)


def foot(phase):
    """one leg seen from above, slightly from the front: knee, shin straight down, wide foot pad.
    phase 0 planted (contact shadow), 1 lifted (foot higher, lighter, shadow below it), 2 coming down"""
    c = Canvas(32, 48, ox=15.5, oy=0)
    lift = (0, 7, 3)[phase]
    fy = 40 - lift
    if lift:                                                   # shadow on the ground under a lifted foot
        c.ellipse(0, 41.5, 7.5, 2.4, (2, 2, 2), shade=False, outline=False)
    c.capsule(0, HIP[1], 0, 15 - lift * 0.3, 3.6, DARK)       # thigh (hidden under the hip housing at the top)
    c.ellipse(0, 16 - lift * 0.3, 4.2, 3.6, LIGHT)            # knee
    c.dot(0, 16 - lift * 0.3, 8)
    c.capsule(0, 18 - lift * 0.3, 0, fy - 3, 2.6, STEEL)      # shin
    c.capsule(-2.8, 22, -2.8, fy - 5, 0.8, DARK)              # piston
    c.ellipse(0, fy, 8.5, 4.4, LIGHT if lift >= 5 else STEEL) # foot pad
    for x in (-6, 0, 6):
        c.capsule(x, fy + 1.5, x, fy + 4.6, 1.0, DARK)        # claws to the front
    img = c.render(0)
    if lift == 0:                                              # planted: dust ring at the pad
        for x in range(4, 28, 2):
            if img[45, x] == 0:
                img[45, x] = 12
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
    """a straight column of fire (Stage 14h): the segments of the jet join seamlessly (no cones); flame_0 is the
    short tip of a growing jet, flame_1 the full column, flame_2 the thinner fading one"""
    img = np.zeros((32, 16), np.uint8)
    rng = np.random.default_rng(40 + n)
    half = (3.0, 4.2, 2.6)[n]
    end = (20, 32, 32)[n]
    for y in range(32):
        if y >= end:
            break
        w = half + math.sin(y * 0.9 + n) * 0.6 + (rng.random() - 0.5) * 0.8
        if n == 0 and y > 12:
            w *= max(0.0, (end - y) / (end - 12))                  # tip: rounded end
        for x in range(16):
            d = abs(x - 7.5)
            if d <= w:
                t = d / max(w, 0.1)
                img[y, x] = 15 if t < 0.25 else (11 if t < 0.55 else (10 if t < 0.8 else 9))
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
    tpos = {'nw': [30, 6], 'ne': [66, 6], 'sw': [30, 40], 'se': [66, 40]}
    pl = {
        'body': 'body', 'body_size': [BW, BH], 'palette': 'boss',
        'turrets': [{'id': f'turret_{t}', 'offset': tpos[t], 'size': [16, 16], 'south': f'turret_{t}_south',
                     'southeast': f'turret_{t}_southeast', 'destroyed': f'turret_{t}_destroyed'} for t in tpos],
        'core': {'offset': [40, 16], 'size': [32, 32], 'exposed_overlay': 'core_exposed'},
        # front legs first: the game draws the list backwards, so they end up in front of the rear legs
        'rotors': [{'id': 'leg_sw', 'offset': [LEG_X[0], LEG_Y[1]], 'phase_offset': 1},
                   {'id': 'leg_se', 'offset': [LEG_X[1], LEG_Y[1]], 'phase_offset': 0},
                   {'id': 'leg_nw', 'offset': [LEG_X[0], LEG_Y[0]], 'phase_offset': 0},
                   {'id': 'leg_ne', 'offset': [LEG_X[1], LEG_Y[0]], 'phase_offset': 1}],
        'rotor_frames': ['rotor_0', 'rotor_1', 'rotor_2'],
        'muzzle': {'frames': ['muzzle_0', 'muzzle_1'], 'south_offset_from_turret': [0, 15]},
        'flame': {'frames': ['flame_0', 'flame_1', 'flame_2'], 'offset': [48, 60]},
        'spray': {'frames': ['spray_0', 'spray_1', 'spray_2'], 'offsets': [[0, 60], [80, 60], [0, 36], [80, 36]]},
        'catapult': {'frames': ['deck_jet_0', 'deck_jet_1', 'deck_jet_2'], 'offset': [48, 0]},
    }
    (GEN / 'placement.json').write_text(json.dumps(pl, indent=1) + '\n')
    # composed preview: body, feet (phase per foot), turrets, then core open + flame
    z = 4
    big = np.zeros((140, 128), np.uint8)

    def blit(a, x, y):
        h, w = a.shape
        for yy in range(h):
            for xx in range(w):
                if a[yy, xx] and 0 <= y + yy < big.shape[0] and 0 <= x + xx < big.shape[1]:
                    big[y + yy, x + xx] = a[yy, xx]
    fr = dict(frames)
    for side, open_core in ((0, False), (1, True)):
        big[:] = 0
        for r in reversed(pl['rotors']):
            blit(fr[f'rotor_{r["phase_offset"]}'], 8 + r['offset'][0], 4 + r['offset'][1])
        blit(fr['body'], 8, 4)
        for t in pl['turrets']:
            blit(fr[t['destroyed'] if open_core else t['south']], 8 + t['offset'][0], 4 + t['offset'][1])
        if open_core:
            blit(fr['core_exposed'], 8 + pl['core']['offset'][0], 4 + pl['core']['offset'][1])
            for k in range(3):
                blit(fr['flame_1'], 8 + pl['flame']['offset'][0], 4 + pl['flame']['offset'][1] + k * 24)
        img = Image.new('RGB', (128 * z, 140 * z), (52, 54, 60))
        for y in range(140):
            for x in range(128):
                if big[y, x]:
                    img.paste(PAL[big[y, x]], (x * z, y * z, x * z + z, y * z + z))
        img.save(GEN / ('boss-preview.png' if side == 0 else 'boss-preview-core.png'))
    print(f'{len(frames)} boss frames written')


if __name__ == '__main__':
    main()
