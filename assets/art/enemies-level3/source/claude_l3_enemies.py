#!/usr/bin/env python3
"""Level-3 enemies redrawn by Claude (Stage 15, owner: "the level-3 enemies do not look good stylistically; make
them coherent with the other levels").

Same style as the level-1 aircraft and Claude's level-4 set: grey steel, red markings, orange/yellow lights, 1 px dark
outline, shading with light from the top left (tools/pixel_vector.py). Same frames, sizes and palette names as before:
  seaplane     16x16, 8 directions x 3 propeller phases   (fighter slots, palette `air`)
  navy_heli    16x16, 8 directions x 3 rotor phases       (helicopter slots, palette `heli`)
  speedboat    16x16, 4 directions x 4 wake phases        (tank slots, palette `ships`)
  patrol_boat  32x32, 4 directions x 2 wake phases        (bomber slots, palette `ships`; gun object at 8,10)
  frigate      32x64, south x 2 wake phases + wreck       (armoured-plane slots, palette `frigate`; guns at 8,8 / 8,36)

    python3 assets/art/enemies-level3/source/claude_l3_enemies.py

rewrites ../generated/indexed-source.json, palettes.json, placement.json and ../generated/l3-enemies.png.
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
# 1 outline, 2-6 hull ramp (dark -> light), 7-9 red, 10 orange, 11 yellow, 12-14 glass, 15 foam / blur
BASE = [(0, 0, 0), (12, 14, 22), (44, 52, 64), (78, 90, 104), (118, 132, 146), (166, 178, 190),
        (220, 228, 236), (118, 22, 20), (190, 40, 32), (238, 84, 62), (248, 150, 40), (255, 222, 96),
        (28, 58, 90), (66, 134, 196), (170, 220, 255), (236, 246, 250)]
PALS = {
    'air': BASE,
    # the naval helicopter: darker blue-grey with yellow markings (rescue/navy look), so it differs from the plane
    'heli': BASE[:2] + [(30, 40, 58), (52, 66, 90), (80, 98, 124), (122, 140, 164), (180, 194, 212)] + BASE[7:],
    'ships': BASE,
    'frigate': BASE[:2] + [(40, 46, 56), (70, 80, 92), (108, 118, 130), (152, 162, 172), (204, 212, 220)] + BASE[7:],
}
STEEL, DARK, LIGHT, RED, GLASS = (3, 4, 5), (2, 3, 4), (4, 5, 6), (7, 8, 9), (12, 13, 14)
DECK = (4, 5, 6)
FOAM, SPRAY = 15, 14


def seaplane(angle, phase):
    c = Canvas(16, 16)
    c.capsule(-3.2, -6.4, 3.2, -6.4, 0.7, DARK)                    # tail plane
    c.capsule(-7.3, 1.4, 7.3, 1.4, 1.0, LIGHT)                     # straight wing, light grey
    for s in (-1, 1):
        c.dot(s * 6.8, 1.4, 8)                                     # red wing tips
        c.capsule(s * 3.6, -2.4, s * 3.6, 5.4, 0.95, DARK)         # long floats, seen on top of the wing
        c.dot(s * 3.6, 5.6, 4)
    c.capsule(0, -6.8, 0, 4.4, 1.35, STEEL)                        # fuselage
    c.dot(0, -6.6, 8)                                              # red fin
    c.ellipse(0, 1.0, 0.9, 1.5, GLASS)                             # canopy
    c.capsule(0, 4.2, 0, 5.4, 1.0, RED)                            # red cowling
    a = math.radians(phase * 60 + 15)                              # propeller blur
    c.line(-math.cos(a) * 3.4, 6.6 + math.sin(a) * 0.6, math.cos(a) * 3.4, 6.6 - math.sin(a) * 0.6, FOAM, dash=1.2)
    c.dot(0, 6.6, 10)
    return c.render(angle)


def navy_heli(angle, phase):
    c = Canvas(16, 16)
    c.capsule(0, -1, 0, -7.0, 0.7, STEEL)                          # tail boom
    c.capsule(-1.6, -6.6, 1.6, -6.6, 0.5, DARK)                    # tail plane
    c.line(1.4, -7.4, 1.4, -5.4, FOAM)                             # tail rotor
    for s in (-1, 1):
        c.capsule(s * 3.3, -0.2, s * 3.3, 2.6, 0.9, DARK)          # sponsons with floats
    c.ellipse(0, 1.2, 2.9, 4.6, STEEL)                             # fuselage
    c.line(-2.4, -1.4, 2.4, -1.4, 11)                              # yellow band
    c.ellipse(0, 3.8, 1.8, 1.6, GLASS)                             # cockpit
    c.dot(0, -2.6, 10)                                             # anti-collision light
    a = phase * 30 + 10                                            # 4-blade rotor, blurred
    for k in (0, 90):
        b = math.radians(a + k)
        c.line(-math.cos(b) * 7.3, -math.sin(b) * 7.3 + 0.8, math.cos(b) * 7.3, math.sin(b) * 7.3 + 0.8, FOAM, dash=1.6)
    c.dot(0, 0.8, 6)
    return c.render(angle)


def wake(c, length, width, phase, back, step=1.6):
    """foam trail behind the stern (y = back), dashes moving with the phase, plus two spreading wash lines"""
    for s in (-1, 1):
        c.line(s * width * 0.5, back, s * width, back - length, FOAM, dash=step, outline=False)
    off = (phase % 2) * step
    c.line(0, back - off, 0, back - length, SPRAY, dash=step, outline=False)


def speedboat(angle, phase):
    c = Canvas(16, 16)
    off = phase * 0.8
    for s in (-1, 1):                                              # V wake, moving
        c.line(s * 1.6, -4.0 - off % 1.6, s * 4.2, -7.6, FOAM, dash=1.6, outline=False)
    c.line(0, -4.6 - (phase % 2), 0, -7.6, SPRAY, dash=1.4, outline=False)
    c.poly([(0, 6.8), (2.2, 3.2), (2.4, -3.6), (-2.4, -3.6), (-2.2, 3.2)], STEEL)   # hull, pointed bow
    c.poly([(0, 6.0), (1.4, 3.4), (-1.4, 3.4)], LIGHT)             # foredeck
    c.ellipse(0, 1.2, 1.5, 1.1, GLASS)                             # windshield
    c.line(-1.8, -1.0, 1.8, -1.0, 8)                               # red stripe
    c.capsule(0, -2.0, 0, -3.2, 0.6, DARK)                         # outboard engine
    c.dot(0, -1.8, 1)                                              # gunner
    if phase % 2:
        c.line(-2.0, 6.4, -3.0, 7.3, SPRAY, outline=False)         # bow spray
        c.line(2.0, 6.4, 3.0, 7.3, SPRAY, outline=False)
    return c.render(angle)


def patrol_boat(angle, phase):
    c = Canvas(32, 32)
    off = phase * 1.2
    for s in (-1, 1):                                              # wake behind the stern, bow wave
        c.line(s * 3.2, -12.5 - off, s * 6.5, -15.5, FOAM, dash=1.5, outline=False)
        c.line(s * 1.4, 13.0, s * 3.8, 10.0 + off * 0.5, FOAM, outline=False)
    c.line(0, -12.4 - off, 0, -15.6, SPRAY, dash=1.2, outline=False)
    hull = [(0, 14.0), (3.2, 10.5), (4.6, 5.0), (4.8, -9.0), (4.2, -12.2), (-4.2, -12.2), (-4.8, -9.0),
            (-4.6, 5.0), (-3.2, 10.5)]
    c.poly(hull, DARK)                                             # hull
    c.poly([(0, 12.6), (2.6, 9.6), (3.6, 5.0), (3.7, -10.8), (-3.7, -10.8), (-3.6, 5.0), (-2.6, 9.6)], DECK)  # deck
    c.line(-3.4, 7.0, 3.4, 7.0, 8)                                 # red bow marking
    c.ellipse(0, 2.5, 2.8, 2.8, (2, 2, 3), shade=False)            # gun ring (gun object on top)
    c.poly([(-2.8, -5.0), (2.8, -5.0), (2.6, -9.6), (-2.6, -9.6)], STEEL)   # bridge, aft
    c.line(-2.2, -5.4, 2.2, -5.4, 13)                              # bridge windows
    c.line(0, -6.8, 0, -9.0, 1)                                    # mast
    c.dot(0, -9.4, 10)
    c.dot(-3.8, -11.2, 9)                                          # navigation lights
    c.dot(3.8, -11.2, 13)
    return c.render(angle)


def frigate(phase, wreck=False):
    c = Canvas(32, 64)
    if not wreck:
        off = phase * 1.4
        for s in (-1, 1):                                          # foam along the sides, wake at the stern, bow wave
            c.line(s * 7.0, -28.0 - off, s * 10.5, -31.5, FOAM, dash=1.5, outline=False)
            c.line(s * 6.8, 6.0 + off, s * 6.8, -24.0, FOAM, dash=2.5, outline=False)
            c.line(s * 1.2, 30.8, s * 5.2, 25.5 - off * 0.5, FOAM, outline=False)
        c.line(0, -28.5 - off, 0, -31.5, SPRAY, dash=1.2, outline=False)
    hull = [(0, 31.0), (3.6, 26.0), (6.0, 18.0), (6.4, 6.0), (6.4, -22.0), (5.6, -27.6), (-5.6, -27.6),
            (-6.4, -22.0), (-6.4, 6.0), (-6.0, 18.0), (-3.6, 26.0)]
    c.poly(hull, DARK)
    c.poly([(0, 29.4), (3.0, 25.2), (5.0, 18.0), (5.2, 6.0), (5.2, -26.2), (-5.2, -26.2), (-5.2, 6.0),
            (-5.0, 18.0), (-3.0, 25.2)], DECK)                     # deck
    c.line(-4.0, 22.5, 4.0, 22.5, 8)                               # red bow marking
    c.line(-4.6, 21.6, 4.6, 21.6, 7)
    c.ellipse(0.5, 12.5, 3.2, 3.2, (2, 2, 3), shade=False)          # forward gun ring (gun object at 8,36)
    c.ellipse(0.5, -15.5, 3.2, 3.2, (2, 2, 3), shade=False)         # aft gun ring (gun object at 8,8)
    c.poly([(-4.4, 8.0), (4.4, 8.0), (4.6, -2.0), (-4.6, -2.0)], STEEL)     # bridge block
    c.line(-3.6, 7.4, 3.6, 7.4, 13)                                # bridge windows
    c.line(-3.6, 6.6, 3.6, 6.6, 12)
    c.ellipse(0, 2.2, 1.8, 1.8, LIGHT)                             # radar dome
    c.capsule(-3.4, -4.0, 3.4, -4.0, 0.6, DARK)                    # mast yard
    c.capsule(0, -2.2, 0, -5.4, 0.7, DARK)                         # mast
    c.dot(0, -5.8, 10)
    c.poly([(-2.6, -6.6), (2.6, -6.6), (2.2, -10.8), (-2.2, -10.8)], STEEL)  # funnel
    c.ellipse(0, -9.4, 1.4, 1.0, (1, 1, 1), shade=False)           # funnel top
    c.poly([(-4.6, -20.0), (4.6, -20.0), (4.6, -26.0), (-4.6, -26.0)], LIGHT)   # helicopter deck
    c.line(-1.2, -21.4, -1.2, -24.6, 11)                           # H
    c.line(1.2, -21.4, 1.2, -24.6, 11)
    c.line(-1.2, -23.0, 1.2, -23.0, 11)
    c.dot(-5.6, -26.8, 9)                                          # navigation lights
    c.dot(5.6, -26.8, 13)
    img = c.render(0)
    if wreck:
        rng = np.random.default_rng(31)
        dark = {6: 4, 5: 3, 4: 2, 3: 2, 13: 2, 12: 1, 11: 10, 15: 2, 14: 2}
        img = np.vectorize(lambda v: dark.get(int(v), int(v)))(img).astype(np.uint8)
        for x, y in ((14, 18), (19, 30), (13, 41), (18, 50), (16, 10)):     # fires and holes
            for k in range(14):
                yy, xx = y + rng.integers(-3, 3), x + rng.integers(-2, 3)
                if img[yy, xx] > 1:
                    img[yy, xx] = (10, 11, 9, 1, 8)[k % 5]
        for y in range(62, 30, -1):                                # bow sinking: the front half fades into the sea
            for x in range(32):
                if img[y, x] and rng.random() < (y - 40) / 40:
                    img[y, x] = 0 if rng.random() < 0.5 else 14
        img[img == 14] = 0
    return img


def main():
    frames = []
    for d, ang in DIRS8.items():
        for n in range(3):
            frames.append(('seaplane', d, n, 'air', seaplane(ang, n)))
    for d, ang in DIRS8.items():
        for n in range(3):
            frames.append(('navy_heli', d, n, 'heli', navy_heli(ang, n)))
    for d in ('north', 'east', 'south', 'west'):
        for n in range(4):
            frames.append(('speedboat', d, n, 'ships', speedboat(DIRS8[d], n)))
    for d in ('north', 'east', 'south', 'west'):
        for n in range(2):
            frames.append(('patrol_boat', d, n, 'ships', patrol_boat(DIRS8[d], n)))
    for n in range(2):
        frames.append(('frigate', 'south', n, 'frigate', frigate(n)))
    frames.append(('frigate', 'destroyed', 0, 'frigate', frigate(0, True)))
    src = [{'group': g, 'pose': p, 'phase': n, 'width': a.shape[1], 'height': a.shape[0], 'palette': pal,
            'rows': rows(a)} for g, p, n, pal, a in frames]
    (GEN / 'indexed-source.json').write_text(json.dumps(src, indent=1) + '\n')
    (GEN / 'palettes.json').write_text(json.dumps({k: [list(c) for c in v] for k, v in PALS.items()}, indent=1) + '\n')
    (GEN / 'placement.json').write_text(json.dumps({'patrol_boat': {'guns': [[8, 10]]},
                                                    'frigate': {'guns': [[8, 8], [8, 36]]}}) + '\n')
    z, W = 4, 340
    pos, x, y, rh = [], 0, 0, 0
    for g, p, n, pal, a in frames:
        h, w = a.shape
        if x + w > W:
            x, y, rh = 0, y + rh + 4, 0
        pos.append((x, y))
        x, rh = x + w + 4, max(rh, h)
    img = Image.new('RGB', (W * z, (y + rh + 4) * z), (38, 92, 112))       # on level-3 water
    for (g, p, n, pal, a), (x, y) in zip(frames, pos):
        for yy in range(a.shape[0]):
            for xx in range(a.shape[1]):
                if a[yy, xx]:
                    img.paste(PALS[pal][a[yy, xx]], ((x + xx) * z, (y + yy) * z, (x + xx + 1) * z, (y + yy + 1) * z))
    img.save(GEN / 'l3-enemies.png')
    print(f'{len(frames)} frames written')


if __name__ == '__main__':
    main()
