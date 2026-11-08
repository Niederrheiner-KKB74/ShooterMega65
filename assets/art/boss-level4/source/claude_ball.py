#!/usr/bin/env python3
"""Level-4 final boss, phase 3 (Stage 17, owner's idea): an armoured sphere that rolls out of the wrecked mech,
opens an iris hatch, warns with its glowing core and fires a stream of fire at the player.

Frames (palette `ball`, light from the top left, 1 px dark outline):
  roll_0..3   48x48  the sphere rolling: a tread band with seams and lights turns (period 90 deg, 22.5 deg per frame)
  open_1..3   48x48  the iris hatch opening (slits, small hole, wide hole with a glowing rim)
  core_0, 1   16x16  the core (a separate target object in the hole): steady / bright warning pulse
  none        16x16  empty (the core while the hatch is shut)

    python3 assets/art/boss-level4/source/claude_ball.py

writes ../generated/ball.json (frames + palette + flash palette) and ../generated/ball-preview.png.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

GEN = Path(__file__).resolve().parents[1] / 'generated'
PAL = [(0, 0, 0), (12, 14, 22), (40, 48, 60), (70, 82, 98), (108, 122, 140), (156, 170, 188), (212, 222, 234),
       (110, 20, 18), (180, 36, 30), (236, 80, 56), (248, 150, 40), (255, 220, 90), (255, 250, 220),
       (26, 12, 12), (74, 26, 18), (90, 160, 220)]
STEEL = [2, 3, 4, 5, 6]
R = 21.5
C = 23.5
LIGHT = np.array([-0.5, -0.62, 0.6])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def sphere(theta, hole=0.0, slits=0.0):
    img = np.zeros((48, 48), np.uint8)
    for y in range(48):
        for x in range(48):
            dx, dy = (x - C) / R, (y - C) / R
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            n = np.array([dx, dy, math.sqrt(1 - d2)])
            lum = float(n @ LIGHT)
            k = 0 if lum < -0.15 else 1 if lum < 0.2 else 2 if lum < 0.5 else 3 if lum < 0.78 else 4
            col = STEEL[k]
            # rolling about the x axis: q = Rx(theta) n
            ct, st = math.cos(theta), math.sin(theta)
            qx, qy, qz = n[0], ct * n[1] - st * n[2], st * n[1] + ct * n[2]
            phi = math.degrees(math.atan2(qy, qz)) % 360
            band = abs(qx) < 0.2
            if band:                                            # tread band, red, with lights every 90 deg
                col = [7, 7, 8, 8, 9][k]
                if abs(qx) > 0.15:
                    col = 1
                if (phi % 90) < 9 and abs(qx) < 0.1 and n[2] > 0.2:
                    col = 11 if k >= 2 else 10
            elif (phi % 45) < 3.5:                              # seams between the armour plates
                col = max(1, col - 2)
            elif (phi % 45) < 6 and k >= 2:                     # bright edge after each seam
                col = min(6, col + 1)
            r = math.hypot(x - C, y - C)
            if slits and r < 11 * slits:                        # iris: four slits opening, hot glow inside
                a = math.degrees(math.atan2(y - C, x - C)) % 90
                w = 10 * slits * (1.4 - r / (11 * slits))
                if a < w or a > 90 - w:
                    col = 14 if r < 4 else 13
                if r < 2.5:
                    col = 10
            if hole and r < hole:                               # iris open: dark hollow with a hot rim
                col = 13 if r < hole - 3 else (14 if r < hole - 1.5 else 10)
                if r < hole - 3 and (x + y) % 5 == 0:
                    col = 14
            img[y, x] = col
    out = img.copy()                                            # outline
    for y in range(48):
        for x in range(48):
            if img[y, x] == 0 and any(0 <= y + dy < 48 and 0 <= x + dx < 48 and img[y + dy, x + dx]
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y, x] = 1
    return out


def core(bright):
    img = np.zeros((16, 16), np.uint8)
    rr = 6.6 if bright else 5.8
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5)
            if r > rr:
                continue
            t = r / rr
            img[y, x] = (12 if t < 0.35 else 11 if t < 0.6 else 10 if t < 0.85 else 9) if bright else \
                        (11 if t < 0.3 else 10 if t < 0.55 else 9 if t < 0.8 else 8)
    if bright:                                                  # rays
        for k in range(8):
            a = math.radians(k * 45 + 22.5)
            for s in (6.8, 7.4):
                x, y = int(round(7.5 + math.cos(a) * s)), int(round(7.5 + math.sin(a) * s))
                if 0 <= x < 16 and 0 <= y < 16:
                    img[y, x] = 11
    return img


def lighten(c, f=0.55):
    return tuple(int(v + (255 - v) * f) for v in c)


def main():
    frames = {}
    for p in range(4):
        frames[f'roll_{p}'] = sphere(math.radians(p * 22.5))
    frames['open_1'] = sphere(0, slits=1.0)
    frames['open_2'] = sphere(0, hole=8)
    frames['open_3'] = sphere(0, hole=12.5)
    frames['core_0'] = core(False)
    frames['core_1'] = core(True)
    frames['none'] = np.zeros((16, 16), np.uint8)
    data = {'palette': [list(c) for c in PAL],
            'flash_palette': [list(lighten(c)) for c in PAL],
            'frames': [{'id': k, 'width': a.shape[1], 'height': a.shape[0],
                        'rows': [''.join(f'{v:x}' for v in r) for r in a]} for k, a in frames.items()]}
    (GEN / 'ball.json').write_text(json.dumps(data, indent=1) + '\n')
    z = 5
    keys = ['roll_0', 'roll_1', 'roll_2', 'roll_3', 'open_1', 'open_2', 'open_3']
    img = Image.new('RGB', ((52 * len(keys) + 2 * 20) * z, 52 * z), (44, 48, 54))
    x = 0
    for k in keys + ['core_0', 'core_1']:
        a = frames[k]
        for yy in range(a.shape[0]):
            for xx in range(a.shape[1]):
                if a[yy, xx]:
                    img.paste(PAL[a[yy, xx]], ((x + xx) * z, (yy + 2) * z, (x + xx + 1) * z, (yy + 3) * z))
        x += a.shape[1] + 4
    img.save(GEN / 'ball-preview.png')
    print(f'{len(frames)} frames')


if __name__ == '__main__':
    main()
