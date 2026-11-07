#!/usr/bin/env python3
"""Level-2 ground targets redrawn by Claude (Stage 15, owner: "the tent does not look like a tent seen from
obliquely above").

All nine 2x2-tile targets (32x32) are drawn to one convention, the same as the level-4 buildings: seen from above
and slightly from the south (south walls visible below the roof), light from the top left, shadow to the lower
right on the sand. Each has a designed wreck (collapsed, burnt, debris) for the destroyed tiles.

The script patches the generated tile set in place (the original generate.py also rewrites the boss and the
level, which were changed later, so it is not run again):
  terrain.ncm.bin       tiles <name>_<col>_<row>
  ground-targets.json   destroyed tiles <name>_destroyed_<col>_<row>
  targets-preview.png   intact and destroyed, 4x

    python3 assets/art/level2/source/claude_targets.py
"""
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

GEN = Path(__file__).resolve().parents[1] / 'generated'
NAMES = ['tent', 'mast', 'command', 'crates', 'oiltank', 'pump', 'workshop', 'loading', 'chimney']

# palette `structures`: 1 near black, 2-7 grey ramp (dark -> light), 8 teal, 9 sand, 10 rust, 11 orange,
# 12 yellow, 13 brown (shadow on sand), 14 dark brown, 15 tan
SAND, SHADOW, SCORCH, OUT = 9, 13, 14, 1


def canvas():
    im = Image.new('L', (32, 32), SAND)
    return im, ImageDraw.Draw(im)


def speckle(im, seed):
    """the sand of the tiles around has light grains; same on the target tiles (only where it is plain sand)"""
    a = np.array(im)
    rng = np.random.default_rng(seed)
    m = (a == SAND) & (rng.random(a.shape) < 0.07)
    a[m] = 12
    return Image.fromarray(a)


def shadow(d, pts, dx=4, dy=3):
    d.polygon([(x + dx, y + dy) for x, y in pts], fill=SHADOW)


# ------------------------------------------------------------------ intact
def tent():
    im, d = canvas()
    sil = [(5, 9), (15, 3), (16, 3), (26, 9), (26, 26), (5, 26)]
    shadow(d, sil)
    for x0, y0, x1, y1 in ((5, 11, 1, 6), (5, 22, 1, 25), (26, 11, 30, 7), (26, 22, 30, 24)):   # guy ropes
        d.line((x0, y0, x1, y1), fill=15)
        d.point((x1, y1), fill=OUT)
    d.polygon([(5, 9), (15, 3), (15, 18), (5, 26)], fill=6)              # west slope, lit
    d.polygon([(16, 3), (26, 9), (26, 26), (16, 18)], fill=4)            # east slope, shaded
    d.line((6, 15, 14, 9), fill=5)                                       # canvas seams
    d.line((6, 21, 14, 15), fill=5)
    d.line((17, 9, 25, 15), fill=3)
    d.line((17, 15, 25, 21), fill=3)
    d.line((15, 3, 15, 17), fill=7)                                      # ridge
    d.line((16, 3, 16, 17), fill=5)
    d.polygon([(5, 26), (15, 18), (16, 18), (26, 26)], fill=5)          # south gable
    d.polygon([(12, 26), (15, 21), (16, 21), (19, 26)], fill=OUT)        # entrance
    d.line((12, 26, 14, 22), fill=3)                                     # flaps tied back
    d.line((19, 26, 17, 22), fill=3)
    d.line((5, 9, 15, 3), fill=7)                                        # outline: light top edge, dark rest
    d.line((16, 3, 26, 9), fill=3)
    d.line((26, 9, 26, 26), fill=2)
    d.line((5, 9, 5, 26), fill=3)
    d.line((5, 26, 26, 26), fill=2)
    d.point((15, 2), fill=OUT)                                           # pole tip
    return im


def mast():
    im, d = canvas()
    d.polygon([(23, 23), (26, 22), (31, 30), (27, 31)], fill=SHADOW)    # pad and tower shadow
    d.rectangle((8, 22, 23, 29), fill=3)                                 # concrete pad
    d.rectangle((8, 22, 23, 26), fill=5)
    d.line((8, 22, 23, 22), fill=6)
    d.rectangle((8, 27, 23, 29), fill=2)
    for y in range(9, 26, 4):                                            # lattice tower
        w = 2 + (y - 9) // 5
        d.line((16 - w, y, 16 + w, y + 4), fill=4)
        d.line((16 + w, y, 16 - w, y + 4), fill=4)
    d.line((13, 26, 15, 9), fill=2)
    d.line((19, 26, 17, 9), fill=OUT)
    d.line((14, 26, 15, 10), fill=6)
    d.ellipse((7, 2, 25, 11), fill=OUT)                                  # dish, tilted towards the sky
    d.ellipse((8, 3, 24, 10), fill=6)
    d.ellipse((10, 4, 22, 9), fill=7)
    d.arc((8, 3, 24, 10), 20, 160, fill=4)
    d.line((16, 6, 16, 1), fill=2)                                       # feed horn
    d.point((16, 1), fill=11)
    d.point((15, 0), fill=12)
    return im


def command():
    im, d = canvas()
    shadow(d, [(5, 8), (26, 8), (27, 24), (4, 24)])
    d.polygon([(6, 6), (25, 6), (27, 9), (27, 18), (4, 18), (4, 9)], fill=5)    # flat roof with chamfered edges
    d.polygon([(6, 6), (25, 6), (24, 8), (7, 8)], fill=6)
    d.line((6, 6, 25, 6), fill=7)
    d.line((4, 9, 6, 6), fill=6)
    d.line((27, 9, 25, 6), fill=3)
    d.line((27, 9, 27, 18), fill=3)
    d.rectangle((9, 10, 14, 13), fill=4)                                 # roof hatch
    d.line((9, 10, 14, 10), fill=6)
    d.rectangle((18, 10, 22, 14), fill=3)                                # air vent
    d.line((18, 12, 22, 12), fill=2)
    d.line((23, 4, 23, 11), fill=2)                                      # antenna
    d.point((23, 3), fill=11)
    d.rectangle((4, 19, 27, 24), fill=3)                                 # south wall
    d.line((4, 19, 27, 19), fill=2)
    d.rectangle((7, 20, 15, 21), fill=OUT)                               # firing slit
    d.rectangle((19, 20, 23, 24), fill=2)                                # steel door
    d.line((19, 20, 23, 20), fill=4)
    d.point((22, 22), fill=12)
    for x in range(3, 29, 4):                                            # sandbags in front
        d.ellipse((x, 25, x + 4, 28), fill=15)
        d.line((x + 1, 25, x + 3, 25), fill=12)
        d.line((x + 1, 28, x + 3, 28), fill=SHADOW)
    return im


def crate(d, x, y, w=8, h=6, f=3, wood=True):
    top, mid, front, edge = (12, 11, 10, 14) if wood else (6, 5, 3, 2)
    d.rectangle((x, y, x + w, y + h), fill=top)
    d.line((x, y, x + w, y), fill=top if not wood else 12)
    d.line((x + 1, y + h // 2, x + w - 1, y + h // 2), fill=mid)
    d.rectangle((x, y + h + 1, x + w, y + h + f), fill=front)
    d.line((x, y + h + 1, x + w, y + h + 1), fill=edge)
    d.line((x + w, y, x + w, y + h + f), fill=edge)
    d.line((x + 2, y + h + 2, x + w - 2, y + h + 2), fill=edge if wood else 4)


def crates():
    im, d = canvas()
    for x, y, w, h, f in ((4, 7, 12, 8, 4), (17, 9, 10, 7, 3), (6, 21, 9, 5, 3), (17, 20, 10, 6, 4)):
        d.rectangle((x + 3, y + 3, x + w + 3, y + h + f + 3), fill=SHADOW)
    crate(d, 4, 7, 12, 8, 4)
    crate(d, 17, 9, 10, 7, 3, wood=False)                               # metal ammo box
    d.rectangle((19, 11, 21, 12), fill=12)                               # stencil
    crate(d, 6, 21, 9, 5, 3)
    crate(d, 17, 20, 10, 6, 4)
    crate(d, 7, 2, 7, 5, 3)                                             # stacked on top of the big one
    d.rectangle((8, 9, 13, 10), fill=SHADOW)
    return im


def oiltank():
    im, d = canvas()
    d.ellipse((9, 18, 31, 31), fill=SHADOW)
    d.rectangle((4, 9, 27, 24), fill=5)                                  # wall, shaded left to right
    for x0, x1, c in ((4, 7, 6), (8, 13, 7), (14, 17, 6), (18, 21, 5), (22, 24, 4), (25, 27, 3)):
        d.rectangle((x0, 9, x1, 24), fill=c)
    d.chord((4, 20, 27, 29), 0, 180, fill=3)                             # bottom of the wall
    for x0, x1, c in ((4, 7, 6), (8, 13, 7), (14, 17, 6), (18, 21, 5), (22, 24, 4), (25, 27, 3)):
        for x in range(x0, x1 + 1):
            for y in range(20, 30):
                if im.getpixel((x, y)) == 3:
                    im.putpixel((x, y), c)
    d.arc((4, 20, 27, 29), 0, 180, fill=2)
    d.line((4, 15, 4, 24), fill=3)
    d.line((27, 14, 27, 24), fill=2)
    for y0 in (14, 19):                                                  # bands
        d.arc((4, y0, 27, y0 + 9), 0, 180, fill=10)
    d.ellipse((4, 3, 27, 15), fill=OUT)                                  # roof
    d.ellipse((5, 4, 26, 14), fill=6)
    d.ellipse((8, 5, 21, 11), fill=7)
    d.ellipse((13, 7, 18, 10), fill=5)                                   # hatch
    d.point((15, 8), fill=3)
    d.line((24, 10, 24, 26), fill=OUT)                                   # ladder
    d.line((26, 11, 26, 26), fill=OUT)
    for y in range(12, 26, 3):
        d.line((24, y, 26, y), fill=4)
    return im


def pump():
    im, d = canvas()
    shadow(d, [(4, 18), (28, 18), (28, 28), (4, 28)], 3, 2)
    d.line((8, 12, 28, 20), fill=SHADOW, width=2)                       # shadow of the beam
    d.rectangle((3, 19, 28, 27), fill=4)                                 # concrete pad
    d.rectangle((3, 19, 28, 24), fill=5)
    d.line((3, 19, 28, 19), fill=6)
    d.rectangle((3, 25, 28, 27), fill=3)
    d.rectangle((20, 15, 27, 22), fill=3)                                # motor housing
    d.rectangle((20, 15, 27, 18), fill=5)
    d.line((20, 15, 27, 15), fill=6)
    d.polygon([(13, 23), (15, 9), (17, 9), (19, 23)], fill=2)           # A-frame (samson post)
    d.line((14, 22, 15, 10), fill=4)
    d.line((15, 15, 18, 15), fill=3)
    d.rectangle((22, 8, 26, 16), fill=OUT)                               # counterweight on the crank
    d.rectangle((22, 8, 25, 14), fill=2)
    d.line((22, 8, 25, 8), fill=4)
    d.line((4, 9, 26, 10), fill=OUT, width=3)                           # walking beam
    d.line((4, 8, 26, 9), fill=11)
    d.line((5, 8, 20, 8), fill=12)
    d.polygon([(2, 7), (6, 6), (7, 13), (3, 14)], fill=10)              # horse head
    d.line((2, 7, 6, 6), fill=11)
    d.line((3, 14, 3, 23), fill=OUT)                                     # rod into the well
    d.rectangle((2, 22, 5, 24), fill=2)                                  # well head
    d.point((3, 22), fill=6)
    return im


def workshop():
    im, d = canvas()
    shadow(d, [(4, 6), (28, 6), (28, 27), (4, 27)])
    for x in range(3, 29):                                               # corrugated roof, gentle slope south
        c = 6 if x % 3 == 0 else 5
        d.line((x, 5, x, 17), fill=c)
    d.line((3, 4, 28, 4), fill=7)                                        # ridge cap
    d.line((3, 5, 28, 5), fill=6)
    d.line((3, 11, 28, 11), fill=4)                                      # roof panel joint
    d.rectangle((8, 7, 12, 9), fill=8)                                   # skylights
    d.rectangle((19, 7, 23, 9), fill=8)
    d.line((8, 7, 12, 7), fill=7)
    d.line((19, 7, 23, 7), fill=7)
    d.line((28, 4, 28, 17), fill=3)
    d.line((3, 18, 28, 18), fill=2)                                      # eaves
    d.rectangle((3, 19, 28, 27), fill=3)                                 # south wall
    d.rectangle((6, 20, 17, 27), fill=2)                                 # roller door
    for y in range(21, 27, 2):
        d.line((6, y, 17, y), fill=OUT)
    d.line((6, 20, 17, 20), fill=4)
    d.rectangle((21, 21, 25, 23), fill=8)                                # window
    d.line((21, 21, 25, 21), fill=7)
    d.line((3, 19, 3, 27), fill=4)
    d.rectangle((24, 1, 25, 4), fill=2)                                  # vent pipe
    d.point((24, 0), fill=4)
    return im


def loading():
    im, d = canvas()
    shadow(d, [(3, 5), (28, 5), (28, 25), (3, 25)])
    d.rectangle((3, 4, 28, 12), fill=6)                                  # canopy roof
    for x in range(5, 28, 4):
        d.line((x, 4, x, 12), fill=5)
    d.line((3, 4, 28, 4), fill=7)
    d.line((3, 12, 28, 12), fill=3)
    d.line((28, 4, 28, 12), fill=4)
    d.rectangle((3, 13, 28, 19), fill=OUT)                               # open loading bay, dark
    for x in (3, 15, 28):                                                # posts
        d.line((x, 13, x, 20), fill=4)
    for x in (6, 10, 19, 23):                                            # barrels inside
        d.ellipse((x, 15, x + 3, 18), fill=10)
        d.line((x + 1, 15, x + 2, 15), fill=11)
    d.rectangle((3, 20, 28, 23), fill=4)                                 # dock edge with warning stripes
    for x in range(3, 29, 4):
        d.polygon([(x, 23), (x + 2, 20), (x + 3, 20), (x + 1, 23)], fill=12)
    d.line((3, 20, 28, 20), fill=5)
    d.line((3, 24, 28, 24), fill=2)
    crate(d, 20, 25, 6, 2, 2)                                            # pallet in front
    d.ellipse((7, 25, 10, 28), fill=10)                                  # barrel in front
    d.line((8, 25, 9, 25), fill=11)
    d.line((11, 27, 12, 29), fill=SHADOW)
    return im


def chimney():
    im, d = canvas()
    d.polygon([(17, 27), (21, 26), (31, 31), (25, 31)], fill=SHADOW)    # long shadow
    d.rectangle((6, 21, 25, 28), fill=3)                                 # boiler house at the foot
    d.rectangle((6, 21, 25, 24), fill=5)
    d.line((6, 21, 25, 21), fill=6)
    d.rectangle((8, 25, 11, 28), fill=2)
    d.rectangle((20, 25, 23, 26), fill=8)
    for y in range(4, 25):                                               # stack: tapered cylinder, shaded
        w = 3 + (y - 4) // 7
        for x in range(16 - w, 16 + w + 1):
            t = (x - (16 - w)) / (2 * w)
            c = 6 if t < 0.25 else 7 if t < 0.45 else 5 if t < 0.7 else 4 if t < 0.85 else 3
            im.putpixel((x, y), c)
    for y in (7, 8, 12, 13):                                             # warning bands
        w = 3 + (y - 4) // 7
        for x in range(16 - w, 16 + w + 1):
            im.putpixel((x, y), 10 if im.getpixel((x, y)) in (5, 6, 7) else 14)
    d.ellipse((12, 1, 20, 5), fill=4)                                    # opening at the top
    d.ellipse((13, 2, 19, 4), fill=OUT)
    d.point((14, 2), fill=2)
    return im


INTACT = {'tent': tent, 'mast': mast, 'command': command, 'crates': crates, 'oiltank': oiltank, 'pump': pump,
          'workshop': workshop, 'loading': loading, 'chimney': chimney}


# ------------------------------------------------------------------ wrecks
def scorch(d, rng, box, n=22):
    """burnt ground: brown halo, dark core, a few loose grains at the edge"""
    x0, y0, x1, y1 = box
    d.ellipse(box, fill=SHADOW)
    w, h = x1 - x0, y1 - y0
    d.ellipse((x0 + w // 5, y0 + h // 5, x1 - w // 5, y1 - h // 5), fill=SCORCH)
    for _ in range(n):
        x, y = rng.randrange(x0 - 2, x1 + 3), rng.randrange(y0 - 2, y1 + 3)
        d.point((x, y), fill=SHADOW)


def debris(d, rng, box, n=9, cols=(3, 4, 5, 15, 2)):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rng.randrange(x0, x1), rng.randrange(y0, y1)
        d.line((x, y, x + rng.randrange(0, 3), y + rng.randrange(-1, 2)), fill=rng.choice(cols))


def embers(d, rng, box, n=4):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rng.randrange(x0, x1), rng.randrange(y0, y1)
        d.point((x, y), fill=rng.choice((11, 11, 12, 10)))


def wreck(name):
    rng = random.Random(NAMES.index(name) * 31 + 7)
    im, d = canvas()
    if name == 'tent':
        scorch(d, rng, (4, 8, 27, 28))
        d.polygon([(6, 14), (14, 10), (24, 15), (25, 25), (12, 27), (5, 23)], fill=3)   # canvas lying flat
        d.polygon([(7, 15), (14, 12), (15, 22), (8, 23)], fill=4)
        d.line((15, 6, 18, 26), fill=OUT, width=2)                       # fallen pole
        d.line((15, 6, 18, 26), fill=15)
        d.line((6, 18, 23, 21), fill=2)
        debris(d, rng, (5, 10, 27, 28), 14, (2, 5, 15))
        embers(d, rng, (8, 12, 24, 25))
    elif name == 'mast':
        scorch(d, rng, (6, 18, 26, 30))
        d.rectangle((8, 22, 23, 29), fill=2)                             # cracked pad
        d.line((9, 25, 22, 24), fill=OUT)
        d.line((12, 23, 4, 4), fill=OUT, width=3)                        # tower toppled to the north-west
        for k in range(0, 18, 3):
            x, y = 12 - k * 8 // 18, 23 - k
            d.line((x - 1, y, x + 1, y - 2), fill=4)
        d.line((12, 23, 4, 4), fill=4)
        d.ellipse((1, 1, 11, 7), fill=3)                                 # crushed dish
        d.chord((1, 1, 11, 7), 200, 360, fill=5)
        d.line((2, 6, 9, 2), fill=OUT)
        debris(d, rng, (6, 16, 28, 30))
        embers(d, rng, (9, 22, 23, 29), 4)
    elif name == 'command':
        scorch(d, rng, (3, 5, 28, 28))
        d.polygon([(6, 6), (25, 6), (27, 9), (27, 18), (4, 18), (4, 9)], fill=3)       # roof broken in
        d.polygon([(9, 8), (20, 7), (23, 14), (14, 17), (8, 14)], fill=OUT)
        d.polygon([(12, 9), (18, 9), (15, 14)], fill=2)                  # slab hanging in
        d.line((9, 8, 23, 15), fill=4)                                   # rebar
        d.line((10, 14, 20, 7), fill=4)
        d.rectangle((4, 19, 27, 24), fill=2)
        d.line((4, 19, 27, 19), fill=OUT)
        d.line((19, 20, 24, 24), fill=SCORCH, width=2)                   # door blown out
        for x in range(3, 29, 4):                                         # scattered sandbags
            if rng.random() < 0.6:
                xx = x + rng.randrange(-1, 2)
                d.ellipse((xx, 25 + rng.randrange(0, 2), xx + 3, 28), fill=15)
        debris(d, rng, (3, 4, 29, 30))
        embers(d, rng, (9, 8, 22, 16))
    elif name == 'crates':
        scorch(d, rng, (3, 5, 29, 30))
        for _ in range(14):                                              # splintered planks
            x, y = rng.randrange(3, 26), rng.randrange(4, 28)
            dx, dy = rng.choice(((4, 1), (3, -2), (1, 4), (-3, 2)))
            d.line((x, y, x + dx, y + dy), fill=rng.choice((10, 14, 11)))
        d.rectangle((17, 11, 26, 18), fill=2)                             # ammo box torn open
        d.rectangle((19, 13, 24, 16), fill=OUT)
        debris(d, rng, (3, 3, 29, 29), 10, (2, 3, 12))
        embers(d, rng, (4, 6, 26, 26), 8)
    elif name in ('oiltank', 'chimney'):
        scorch(d, rng, (2, 6, 30, 31), 90)
        if name == 'oiltank':
            d.ellipse((4, 6, 27, 27), fill=OUT)                          # burst tank, open, burnt inside
            d.ellipse((6, 8, 25, 22), fill=SCORCH)
            d.arc((4, 6, 27, 27), 120, 330, fill=3, width=2)             # remaining wall
            d.arc((4, 6, 27, 27), 330, 60, fill=2)
            d.polygon([(23, 18), (30, 20), (27, 26), (21, 24)], fill=3)  # torn sheet
            d.line((23, 18, 29, 21), fill=5)
            d.ellipse((8, 23, 18, 30), fill=OUT)                         # burning oil
            embers(d, rng, (8, 9, 24, 20), 10)
            embers(d, rng, (9, 24, 18, 30), 6)
        else:
            d.rectangle((6, 21, 25, 28), fill=2)                         # boiler house burnt
            d.rectangle((8, 22, 23, 26), fill=OUT)
            d.ellipse((12, 18, 20, 23), fill=3)                          # stump of the stack
            d.ellipse((13, 19, 19, 22), fill=OUT)
            for k in range(6):                                           # fallen stack as broken rings
                x, y = 15 - k * 2, 16 - k * 3
                d.ellipse((x - 3, y - 2, x + 3, y + 1), fill=4 if k % 2 else 5)
                d.point((x, y - 1), fill=10)
            embers(d, rng, (8, 22, 24, 27), 8)
        debris(d, rng, (2, 4, 30, 30))
    elif name == 'pump':
        scorch(d, rng, (2, 10, 29, 30))
        d.rectangle((3, 19, 28, 27), fill=3)                              # cracked pad
        d.line((5, 23, 26, 21), fill=2)
        d.line((5, 20, 25, 27), fill=OUT, width=3)                       # beam down across the pad
        d.line((5, 19, 25, 26), fill=10)
        d.polygon([(2, 16), (6, 15), (7, 21), (3, 22)], fill=14)         # horse head on the ground
        d.polygon([(14, 25), (16, 16), (19, 17), (20, 25)], fill=2)      # bent A-frame
        d.rectangle((21, 14, 27, 20), fill=2)                             # burnt motor
        d.line((21, 14, 27, 14), fill=3)
        debris(d, rng, (2, 12, 30, 30))
        embers(d, rng, (5, 18, 26, 27))
    elif name == 'workshop':
        scorch(d, rng, (2, 3, 29, 29))
        d.rectangle((3, 4, 28, 18), fill=OUT)                             # roof gone: dark hall, trusses
        for x in range(5, 28, 5):
            d.line((x, 4, x + 1, 18), fill=4)
        d.line((3, 11, 28, 11), fill=3)
        d.polygon([(3, 4), (12, 4), (8, 10), (3, 9)], fill=5)            # a piece of roof still hanging
        d.line((3, 4, 12, 4), fill=6)
        d.polygon([(20, 13), (28, 12), (28, 18), (22, 18)], fill=4)
        d.rectangle((3, 19, 28, 27), fill=2)                              # wall, burnt
        d.line((3, 19, 28, 19), fill=OUT)
        d.polygon([(6, 20), (17, 20), (15, 27), (8, 27)], fill=OUT)      # door blown in
        d.line((21, 21, 25, 23), fill=SCORCH, width=2)
        debris(d, rng, (3, 4, 29, 29))
        embers(d, rng, (5, 6, 26, 17), 8)
    elif name == 'loading':
        scorch(d, rng, (2, 3, 29, 30))
        d.polygon([(3, 6), (28, 4), (28, 10), (16, 20), (3, 13)], fill=4)    # canopy collapsed into the bay
        d.line((3, 6, 28, 4), fill=5)
        for x in range(6, 28, 5):
            d.line((x, 5, x - 2, 15), fill=3)
        d.line((16, 8, 16, 20), fill=OUT)
        d.rectangle((3, 20, 28, 23), fill=3)                              # dock edge, stripes burnt
        for x in range(3, 29, 6):
            d.polygon([(x, 23), (x + 2, 20), (x + 3, 20), (x + 1, 23)], fill=11)
        for x, y in ((6, 17), (20, 15), (9, 25), (23, 26)):              # burst barrels
            d.ellipse((x, y, x + 3, y + 3), fill=OUT)
            d.point((x + 1, y + 1), fill=11)
        debris(d, rng, (2, 3, 29, 30))
        embers(d, rng, (5, 12, 26, 20), 8)
    a = np.array(speckle(im, 300 + NAMES.index(name)))
    a[:2, :] = SAND                                                      # rim stays sand like the tiles around
    a[-1:, :] = np.where(a[-1:, :] == SHADOW, SHADOW, SAND)
    a[:, :1] = SAND
    return a


# ------------------------------------------------------------------ tile set
def ncm(a):
    return bytes(int(a[y, x]) | (int(a[y, x + 1]) << 4) for y in range(8) for x in range(0, 16, 2))


def main():
    tiles = {t['name']: t for t in json.loads((GEN / 'level-example.json').read_text())['tiles']}
    terr = bytearray((GEN / 'terrain.ncm.bin').read_bytes())
    gtp = GEN / 'ground-targets.json'
    gt = json.loads(gtp.read_text())
    dest = {d['name']: d for d in gt['destroyed_tiles']}
    pal = json.loads((GEN / 'manifest.json').read_text())['palettes']['structures']
    prev = Image.new('RGB', (len(NAMES) * 36, 72), (30, 30, 30))
    for k, name in enumerate(NAMES):
        whole = np.array(speckle(INTACT[name](), 200 + k))
        broken = wreck(name)
        assert whole.min() > 0 and broken.min() > 0, name
        for c in range(2):
            for r in range(2):
                t = tiles[f'{name}_{c}_{r}']
                assert t['palette'] == 'structures'
                cell = whole[r * 16:r * 16 + 16, c * 16:c * 16 + 16]
                terr[t['id'] * 128:t['id'] * 128 + 64] = ncm(cell[:8])
                terr[t['id'] * 128 + 64:t['id'] * 128 + 128] = ncm(cell[8:])
                dc = broken[r * 16:r * 16 + 16, c * 16:c * 16 + 16]
                dest[f'{name}_destroyed_{c}_{r}']['pixels'] = [''.join(f'{v:x}' for v in row) for row in dc]
        for row, a in enumerate((whole, broken)):
            for y in range(32):
                for x in range(32):
                    prev.putpixel((k * 36 + x, row * 36 + y), tuple(pal[a[y, x]]))
    (GEN / 'terrain.ncm.bin').write_bytes(bytes(terr))
    gtp.write_text(json.dumps(gt, indent=2) + '\n', encoding='ascii', newline='\n')
    prev.resize((prev.width * 4, prev.height * 4), Image.NEAREST).save(GEN / 'targets-preview.png')
    print(f'{len(NAMES)} targets redrawn')


if __name__ == '__main__':
    main()
