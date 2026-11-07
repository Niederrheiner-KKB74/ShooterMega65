#!/usr/bin/env python3
"""Heavy combat drone for level 4 (Stage 14b, drawn by Claude at the owner's request).

Replaces the small 16x16 drone of PR #26 with a 32x32 heavy quadrocopter in the size of the level-1 bomber:
four ducted rotors on armoured arms, an armoured hull with hazard stripes, a red sensor eye and two gun barrels
pointing down (to the player). Views `straight`, `left`, `right` (banking: the lowered side's rotors look smaller
and darker), phases 0-2 turn the rotor blades by 60 degrees. Palette `drone`.

    python3 assets/art/enemies-level4/source/claude_drone.py

rewrites the `drone` frames in ../generated/indexed-source.json, the palette `drone` in ../generated/palettes.json
and writes ../generated/drone-big-preview.png.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

GEN = Path(__file__).resolve().parents[1] / 'generated'
PAL = [
    (0, 0, 0),          # 0 transparent
    (12, 12, 18),       # 1 outline
    (38, 42, 54),       # 2 dark gunmetal
    (66, 72, 88),       # 3 gunmetal
    (104, 112, 130),    # 4 steel
    (160, 168, 186),    # 5 light steel
    (210, 216, 228),    # 6 highlight
    (54, 60, 74),       # 7 duct inside (rotor blur)
    (196, 206, 220),    # 8 rotor blade
    (255, 64, 40),      # 9 red eye
    (140, 16, 16),      # 10 dark red
    (255, 160, 48),     # 11 orange glow
    (236, 196, 40),     # 12 hazard yellow
    (88, 66, 16),       # 13 hazard dark
    (70, 220, 255),     # 14 cyan light
    (255, 255, 236),    # 15 white
]


def disc(img, cx, cy, r, c):
    for y in range(32):
        for x in range(32):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                img[y, x] = c


def ring(img, cx, cy, r, c, w=1.0):
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - cx, y - cy)
            if r - w < d <= r:
                img[y, x] = c


def line(img, x0, y0, x1, y1, c):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        x, y = round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t)
        if 0 <= x < 32 and 0 <= y < 32:
            img[y, x] = c


def rotor(img, cx, cy, r, phase, low):
    """Ducted fan (Stage 14c: calm): dark duct, static blur ring, hub; only two blade glints orbit the hub
    (60 degrees per phase), so the rotor turns smoothly instead of flickering."""
    disc(img, cx, cy, r, 7)
    ring(img, cx, cy, r, 1)
    ring(img, cx, cy, r - 1, 2 if low else 3)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - cx, y - cy)
            if r - 1.0 < d <= r and (x - cx) + (y - cy) < -r * 0.6:
                img[y, x] = 4 if low else 5            # rim lit from top left
            elif r - 3.2 < d <= r - 2.4:
                img[y, x] = 2                          # faint inner ring (static)
    for k in (0, 180):
        for back, c in ((0, 8 if not low else 5), (28, 4)):
            b = math.radians(phase * 60 + k - back + 20)
            x, y = round(cx + math.cos(b) * (r - 2.6)), round(cy + math.sin(b) * (r - 2.6))
            img[y, x] = c
    img[round(cy), round(cx)] = 4
    img[round(cy) - 1, round(cx) - 1] = 6
    img[round(cy), round(cx) - 1] = 3


def drone(pose, phase):
    img = np.zeros((32, 32), np.uint8)
    lean = {'straight': 0, 'left': -1, 'right': 1}[pose]
    cx = 15.5 + lean * 1.6
    # rotor hubs; banking: the side the drone leans to sinks (smaller, darker)
    hubs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            low = (lean != 0 and sx == lean)
            high = (lean != 0 and sx == -lean)
            # Stage 14e: stronger banking (owner's wish): the lowered side's rotors are small, dark and pulled in,
            # the raised side's rotors larger and further out
            r = 4.4 if low else (6.9 if high else 6.2)
            hx = 15.5 + sx * (7.2 if low else (9.8 if high else 9.0))
            hy = 15.5 + sy * 9.0
            hubs.append((hx, hy, r, low))
    # arms (drawn first, rotors and hull on top)
    for hx, hy, r, low in hubs:
        for o in (-1, 0, 1):
            line(img, cx + o * 0.7, 15.5, hx + o * 0.7, hy, 1)
        line(img, cx, 15.5, hx, hy, 3 if low else 4)
        line(img, cx - 0.7, 15.0, hx - 0.7, hy - 0.5, 5)
    for hx, hy, r, low in hubs:
        rotor(img, hx, hy, r, phase, low)
    # armoured hull: octagon 12 x 16
    x0, x1, y0, y1 = int(cx - 5.5), int(cx + 5.5), 8, 24
    for y in range(y0, y1 + 1):
        cut = max(0, 2 - (y - y0), (y - 19) if y > 19 else 0)     # pointed towards the front (down)
        for x in range(x0 + cut, x1 - cut + 1):
            edge = x in (x0 + cut, x1 - cut) or y in (y0, y1)
            if edge:
                img[y, x] = 1
            elif x - x0 + y - y0 < 9:
                img[y, x] = 5          # lit top-left
            elif (x1 - x) + (y1 - y) < 7:
                img[y, x] = 2          # shadow bottom-right
            else:
                img[y, x] = 3
    # dorsal plate with panel line and cyan status lights
    for y in range(11, 16):
        for x in range(int(cx - 3), int(cx + 4)):
            img[y, x] = 4
    line(img, cx - 3, 11, cx + 3, 11, 6)
    line(img, cx - 3, 16, cx + 3, 16, 2)
    for x in range(int(cx - 2), int(cx + 3)):                    # red warning stripe, antenna
        img[13, x] = 10
    img[13, int(cx)] = 9
    img[9, int(cx) + 2] = 6
    img[8, int(cx) + 2] = 1
    # hazard stripes across the front
    for x in range(int(cx - 4), int(cx + 5)):
        img[17, x] = 12 if (x + 17) % 3 else 13
        img[18, x] = 13 if (x + 18) % 3 else 12
    for x in (x0, x1):                                           # side missile pods
        for y in range(14, 20):
            img[y, x] = 1
            img[y, x + (-1 if x == x0 else 1)] = 10 if y == 14 else 3
    # red sensor eye with glow (flickers with the phase)
    ey = 20
    for x in range(int(cx - 2), int(cx + 3)):
        img[ey, x] = 10
    img[ey, int(cx)] = 9                                         # steady eye (no blinking)
    img[ey, int(cx) - 1] = 11
    img[ey, int(cx) + 1] = 9
    # gun barrels pointing down, muzzle glow
    for gx in (int(cx - 4), int(cx + 4)):
        for y in range(22, 28):
            img[y, gx] = 1
            img[y, gx + (1 if gx < cx else -1)] = 4 if y < 26 else 2
        img[28, gx] = 1
    # lights at the arm ends (navigation: red left, cyan right)
    for (hx, hy, r, low), c in zip(hubs, (9, 9, 14, 14)):
        if hy > 15.5:
            img[min(31, round(hy + r)), round(hx)] = c
    return img


def main():
    src = json.loads((GEN / 'indexed-source.json').read_text())
    src = [f for f in src if f['group'] != 'drone']
    frames = []
    for pose in ('straight', 'left', 'right'):
        for n in range(3):
            a = drone(pose, n)
            frames.append({'group': 'drone', 'pose': pose, 'phase': n, 'width': 32, 'height': 32,
                           'palette': 'drone', 'rows': [''.join(f'{v:02x}' for v in row) for row in a]})
    (GEN / 'indexed-source.json').write_text(json.dumps(src + frames, indent=1) + '\n')
    pals = json.loads((GEN / 'palettes.json').read_text())
    pals['drone'] = [list(c) for c in PAL]
    (GEN / 'palettes.json').write_text(json.dumps(pals, indent=1) + '\n')
    z = 6
    out = Image.new('RGB', (3 * 36 * z, 3 * 36 * z), (52, 54, 60))
    for k, f in enumerate(frames):
        a = np.array([[int(r[2 * x:2 * x + 2], 16) for x in range(32)] for r in f['rows']])
        for y in range(32):
            for x in range(32):
                if a[y, x]:
                    ox, oy = (k % 3) * 36 + 2 + x, (k // 3) * 36 + 2 + y
                    out.paste(PAL[a[y, x]], (ox * z, oy * z, ox * z + z, oy * z + z))
    out.save(GEN / 'drone-big-preview.png')
    print('drone: 9 frames 32x32 written')


if __name__ == '__main__':
    main()
