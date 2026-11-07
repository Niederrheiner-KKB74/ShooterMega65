#!/usr/bin/env python3
"""Heavy four-legged walker for level 4 (Stage 14d, drawn by Claude at the owner's request).

Replaces the walker of PR #26 (coarse, two jumpy phases). 32x32, front down (it walks towards the player), palette
`mechs` (shared with the small mech). An armoured hull with a turret ring in the middle (the game puts its light gun
at placement offset [8, 6]), sensor slit and headlights at the front, and four legs whose feet step in a smooth
four-phase cycle (diagonal pairs move together). Plus a burning wreck.

    python3 assets/art/enemies-level4/source/claude_walker.py

rewrites the `walker` frames in ../generated/indexed-source.json and writes ../generated/walker-big-preview.png.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

GEN = Path(__file__).resolve().parents[1] / 'generated'
# palette `mechs` indices: 1 outline, 2 dark, 3 mid, 4 steel, 5 light, 6 pale, 7 cream, 8 dark teal, 9 teal,
# 10 cyan, 11 dark rust, 12 rust, 13 orange, 14 yellow, 15 pale yellow


def put(img, x, y, c):
    if 0 <= x < 32 and 0 <= y < 32:
        img[y, x] = c


def seg(img, x0, y0, x1, y1, c, w=1):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for dx in range(w):
            put(img, round(x) + dx, round(y), c)


def leg(img, hx, hy, fx, fy, side, lift):
    """hip (hx, hy) -> knee (bent outwards) -> foot (fx, fy): armoured segments 3 px wide with outline; a lifted
    foot is lighter and casts a small shadow."""
    kx, ky = (hx + fx) / 2 + side * 2.0, (hy + fy) / 2
    for (ax, ay, bx, by) in ((hx, hy, kx, ky), (kx, ky, fx, fy)):
        for o in (-2, 2):
            seg(img, ax - 1, ay + o, bx - 1, by + o, 1, 3)
        for o in (-1, 0, 1):
            seg(img, ax - 1, ay + o, bx - 1, by + o, 3, 3)
        seg(img, ax - 1, ay - 1, bx - 1, by - 1, 5, 3)          # lit upper edge
        seg(img, ax - 1, ay + 1, bx - 1, by + 1, 2, 3)          # shadow lower edge
    for y in (-1, 0, 1):                                       # knee joint
        for x in (-1, 0, 1):
            put(img, round(kx) + x, round(ky) + y, 1 if abs(x) + abs(y) == 2 else 9)
    put(img, round(kx) - 1 + (side < 0), round(ky) - 1, 10)
    if lift:
        for x in (-1, 0, 1, 2):
            put(img, round(fx) + x, round(fy) + 3, 2)          # shadow on the ground
    for y in (-2, -1, 0, 1, 2):                                # foot pad
        for x in (-2, -1, 0, 1, 2):
            if abs(x) + abs(y) <= 3:
                edge = abs(x) + abs(y) == 3 or abs(x) == 2 and abs(y) == 1 or abs(y) == 2
                c = 1 if edge else ((6 if y < 0 else 5) if lift else (4 if y < 0 else 3))
                put(img, round(fx) + x, round(fy) + y, c)


def hull(img, wreck=False):
    x0, x1, y0, y1 = 9, 22, 7, 23
    for y in range(y0, y1 + 1):
        cut = max(0, 2 - (y - y0), 2 - (y1 - y))
        for x in range(x0 + cut, x1 - cut + 1):
            if x in (x0 + cut, x1 - cut) or y in (y0, y1):
                c = 1
            elif x - x0 + y - y0 < 8:
                c = 6 if not wreck else 3
            elif (x1 - x) + (y1 - y) < 7:
                c = 2
            else:
                c = 4 if not wreck else 2
            img[y, x] = c
    # side armour with rust warning stripes
    for y in range(10, 20):
        img[y, x0 + 1] = 12 if (y // 2) % 2 and not wreck else 3
        img[y, x1 - 1] = 12 if (y // 2) % 2 and not wreck else 2
    # turret ring where the game mounts the gun (gun at [8, 6]: centre near 16, 14)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - 15.5, y - 13.5)
            if 4.6 < d <= 5.6:
                img[y, x] = 1
            elif 3.6 < d <= 4.6:
                img[y, x] = 8 if (x - 15.5) + (y - 13.5) > 0 else 9
            elif d <= 3.6:
                img[y, x] = 2
    if wreck:
        return
    # front: sensor slit and headlights
    for x in range(13, 19):
        img[20, x] = 10
    img[20, 15] = 7
    img[21, 12] = 14
    img[21, 19] = 14
    img[22, 13] = 1
    img[22, 18] = 1


def walker(phase):
    img = np.zeros((32, 32), np.uint8)
    a = [-2, 0, 2, 0][phase]                           # pair A: front left + back right; pair B opposite
    lift_a, lift_b = phase == 1, phase == 3            # the pair that swings forward is lifted
    legs = [(11, 10, 4, 5 - a, -1, lift_a), (20, 20, 27, 26 - a, 1, lift_a),     # back left, front right (A)
            (20, 10, 27, 5 + a, 1, lift_b), (11, 20, 4, 26 + a, -1, lift_b)]     # back right, front left (B)
    for hx, hy, fx, fy, side, lift in legs:
        if not lift:
            leg(img, hx, hy, fx, fy, side, lift)
    hull(img)
    for hx, hy, fx, fy, side, lift in legs:            # lifted legs above the hull edge (closer to the camera)
        if lift:
            leg(img, hx, hy, fx, fy, side, lift)
    return img


def wreck():
    img = np.zeros((32, 32), np.uint8)
    leg(img, 11, 20, 4, 26, -1, False)                 # two legs left, two broken stumps
    leg(img, 20, 10, 27, 5, 1, False)
    seg(img, 10, 9, 7, 7, 1, 2)
    seg(img, 21, 20, 24, 23, 1, 2)
    hull(img, wreck=True)
    rng = np.random.default_rng(14)
    for x, y in ((14, 11), (18, 16), (12, 18)):        # fires
        for k in range(10):
            dx, dy = rng.integers(-2, 3), rng.integers(-3, 2)
            put(img, x + dx, y + dy, (13, 14, 15, 12)[k % 4])
    for x, y in ((9, 5), (22, 25), (25, 12)):          # smoke
        for k in range(6):
            put(img, x + rng.integers(-2, 3), y + rng.integers(-2, 3), (2, 3)[k % 2])
    return img


def main():
    src = json.loads((GEN / 'indexed-source.json').read_text())
    src = [f for f in src if f['group'] != 'walker']
    frames = [(f'south', n, walker(n)) for n in range(4)] + [('destroyed', 0, wreck())]
    out = []
    for pose, n, a in frames:
        out.append({'group': 'walker', 'pose': pose, 'phase': n, 'width': 32, 'height': 32, 'palette': 'mechs',
                    'rows': [''.join(f'{v:02x}' for v in row) for row in a]})
    (GEN / 'indexed-source.json').write_text(json.dumps(src + out, indent=1) + '\n')
    pal = json.loads((GEN / 'palettes.json').read_text())['mechs']
    z = 6
    img = Image.new('RGB', (5 * 36 * z, 36 * z), (52, 54, 60))
    for k, (_, _, a) in enumerate(frames):
        for y in range(32):
            for x in range(32):
                if a[y, x]:
                    ox, oy = k * 36 + 2 + x, 2 + y
                    img.paste(tuple(pal[a[y, x]]), (ox * z, oy * z, ox * z + z, oy * z + z))
    img.save(GEN / 'walker-big-preview.png')
    print('walker: 4 phases + wreck written')


if __name__ == '__main__':
    main()
