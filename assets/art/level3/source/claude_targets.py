#!/usr/bin/env python3
"""Level-3 ground targets redrawn by Claude (Stage 15, owner: review the level-3 artwork, coherent style).

The eight 2x2-tile targets on the platforms (drilling derrick, crane, radar mast, tank, lighthouse, containers,
control building, quarters) are drawn like the level-2 and level-4 buildings: from above and slightly from the
south (south walls visible), light from the top left, shadow to the lower right. They stand on the deck plating of
the tile `deck`, so the edges join the platform around them. Each has a designed wreck.

Patches the generated tile set in place (terrain.ncm.bin, ground-targets.json) and writes targets-preview.png:

    python3 assets/art/level3/source/claude_targets.py
"""
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

GEN = Path(__file__).resolve().parents[1] / 'generated'
NAMES = ['drill', 'crane', 'mast', 'tank', 'lighthouse', 'cargo', 'command', 'quarters']
# palette `structures` (level 3): 1 near black, 2-7 blue-grey ramp (5 = deck), 8 khaki, 9 yellow, 10 cream,
# 11 rust red, 12 red-orange, 13 orange, 14 olive grey, 15 dark teal
OUT, SHADOW, SCORCH = 1, 3, 15
DECK = None          # 32x32 deck plating (filled in main from the tile `deck`)


def canvas():
    im = Image.fromarray(DECK.copy())
    return im, ImageDraw.Draw(im)


def shadow(d, pts, dx=4, dy=3):
    d.polygon([(x + dx, y + dy) for x, y in pts], fill=SHADOW)


def box(d, x0, y0, x1, y1, h, top=6, front=3, edge=7, line=2):
    """a block seen from above-south: roof x0..x1 / y0..y1, south wall h px high below it"""
    d.rectangle((x0, y0, x1, y1), fill=top)
    d.line((x0, y0, x1, y0), fill=edge)
    d.line((x0, y0, x0, y1), fill=edge)
    d.line((x1, y0, x1, y1), fill=line)
    d.rectangle((x0, y1 + 1, x1, y1 + h), fill=front)
    d.line((x0, y1 + 1, x1, y1 + 1), fill=line)


def lattice(d, x0, y0, x1, y1, w0, w1, col, dark):
    """tapered lattice from (x0,y0) (width w0) to (x1,y1) (width w1)"""
    n = 6
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        ax, ay = x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0
        bx, by = x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1
        wa, wb = w0 + (w1 - w0) * t0, w0 + (w1 - w0) * t1
        d.line((ax - wa, ay, bx + wb, by), fill=col)
        d.line((ax + wa, ay, bx - wb, by), fill=col)
    d.line((x0 - w0, y0, x1 - w1, y1), fill=col)
    d.line((x0 + w0, y0, x1 + w1, y1), fill=dark)


# ------------------------------------------------------------------ intact
def drill():
    im, d = canvas()
    d.polygon([(19, 27), (24, 25), (31, 31), (25, 31)], fill=SHADOW)
    box(d, 5, 18, 26, 24, 4, top=4, front=2, edge=6)                 # drill floor
    d.rectangle((7, 20, 11, 23), fill=13)                            # mud pumps, orange
    d.line((7, 20, 11, 20), fill=9)
    for y in (19, 21, 23):                                           # pipe rack
        d.line((19, y, 25, y), fill=7)
    lattice(d, 15.5, 22, 15.5, 4, 6, 2, 9, 13)                       # derrick, yellow
    d.line((9, 22, 13, 4), fill=OUT)
    d.line((22, 22, 18, 4), fill=OUT)
    d.rectangle((12, 1, 19, 4), fill=12)                             # crown block
    d.line((12, 1, 19, 1), fill=13)
    d.line((15, 5, 15, 21), fill=2)                                  # drill string
    d.point((16, 0), fill=13)
    return im


def crane():
    im, d = canvas()
    d.line((14, 26, 31, 14), fill=SHADOW, width=2)                   # boom shadow
    d.ellipse((5, 18, 17, 29), fill=SHADOW)
    d.ellipse((4, 17, 15, 27), fill=OUT)                             # pedestal
    d.ellipse((5, 18, 14, 26), fill=4)
    d.ellipse((5, 18, 13, 23), fill=6)
    box(d, 5, 14, 14, 19, 3, top=9, front=13, edge=10, line=OUT)     # cab
    d.rectangle((6, 20, 9, 21), fill=OUT)                            # cab window
    d.line((12, 15, 29, 3), fill=OUT, width=4)                       # lattice boom
    d.line((12, 15, 29, 3), fill=9, width=2)
    for k in range(13, 29, 3):
        d.line((k, 15 - (k - 12) * 12 // 17, k + 2, 14 - (k - 10) * 12 // 17), fill=13)
    d.line((29, 3, 29, 12), fill=OUT)                                # hook cable
    d.rectangle((27, 12, 31, 15), fill=12)                           # load
    d.line((27, 12, 31, 12), fill=13)
    return im


def mast():
    im, d = canvas()
    d.polygon([(22, 24), (26, 23), (31, 30), (27, 31)], fill=SHADOW)
    box(d, 8, 21, 23, 25, 3, top=6, front=3)                         # equipment shelter
    d.rectangle((10, 26, 13, 28), fill=2)
    for y in range(9, 22, 4):                                        # lattice
        w = 1 + (y - 9) // 5
        d.line((16 - w, y, 16 + w, y + 4), fill=7)
        d.line((16 + w, y, 16 - w, y + 4), fill=7)
    d.line((13, 22, 15, 9), fill=2)
    d.line((19, 22, 17, 9), fill=OUT)
    d.ellipse((6, 1, 26, 10), fill=OUT)                              # radar dish
    d.ellipse((7, 2, 25, 9), fill=6)
    d.ellipse((9, 3, 22, 8), fill=7)
    d.arc((7, 2, 25, 9), 20, 160, fill=4)
    d.line((16, 5, 16, 0), fill=2)
    d.point((16, 0), fill=12)
    return im


def tank():
    im, d = canvas()
    d.ellipse((9, 17, 31, 31), fill=SHADOW)
    for x0, x1, c in ((4, 7, 6), (8, 13, 7), (14, 17, 6), (18, 21, 5), (22, 24, 4), (25, 27, 3)):
        d.rectangle((x0, 9, x1, 24), fill=c)
        d.pieslice((4, 20, 27, 29), 0, 180, fill=0)
    for x0, x1, c in ((4, 7, 6), (8, 13, 7), (14, 17, 6), (18, 21, 5), (22, 24, 4), (25, 27, 3)):
        for x in range(x0, x1 + 1):
            for y in range(9, 30):
                if im.getpixel((x, y)) == 0:
                    im.putpixel((x, y), c)
    d.arc((4, 20, 27, 29), 0, 180, fill=2)
    d.line((27, 14, 27, 24), fill=2)
    for y0 in (13, 18):                                              # red bands
        d.arc((4, y0, 27, y0 + 9), 0, 180, fill=11)
    d.ellipse((4, 3, 27, 15), fill=OUT)                              # roof
    d.ellipse((5, 4, 26, 14), fill=6)
    d.ellipse((8, 5, 21, 11), fill=7)
    d.ellipse((13, 7, 18, 10), fill=4)
    d.line((24, 10, 24, 26), fill=OUT)                               # ladder
    d.line((26, 11, 26, 26), fill=OUT)
    for y in range(12, 26, 3):
        d.line((24, y, 26, y), fill=4)
    return im


def lighthouse():
    im, d = canvas()
    d.polygon([(17, 27), (21, 26), (31, 31), (25, 31)], fill=SHADOW)
    box(d, 6, 22, 25, 25, 3, top=7, front=4, edge=10)                # keeper's house
    d.rectangle((9, 26, 11, 28), fill=2)
    d.rectangle((20, 26, 22, 27), fill=10)
    for y in range(7, 25):                                           # tapered round tower, shaded
        w = 3 + (y - 7) // 6
        for x in range(16 - w, 16 + w + 1):
            t = (x - (16 - w)) / (2 * w)
            c = 6 if t < 0.25 else 7 if t < 0.45 else 6 if t < 0.7 else 5 if t < 0.85 else 4
            im.putpixel((x, y), c)
    for y in list(range(10, 13)) + list(range(16, 19)):              # red bands
        w = 3 + (y - 7) // 6
        for x in range(16 - w, 16 + w + 1):
            v = im.getpixel((x, y))
            im.putpixel((x, y), 12 if v in (6, 7) else 11)
    d.ellipse((10, 5, 21, 9), fill=2)                                # gallery
    d.ellipse((11, 5, 20, 8), fill=4)
    d.rectangle((13, 2, 18, 6), fill=10)                             # lantern, lit
    d.line((13, 2, 18, 2), fill=9)
    d.line((15, 3, 15, 5), fill=7)
    d.ellipse((12, 0, 19, 3), fill=11)                               # roof
    d.point((15, 0), fill=12)
    return im


def container(d, x, y, w, h, top, front, dark):
    d.rectangle((x + 2, y + 2, x + w + 2, y + h + 5), fill=SHADOW)
    d.rectangle((x, y, x + w, y + h), fill=top)
    for k in range(x + 1, x + w, 2):                                 # corrugation
        d.line((k, y + 1, k, y + h - 1), fill=front)
    d.line((x, y, x + w, y), fill=7)
    d.rectangle((x, y + h + 1, x + w, y + h + 3), fill=front)
    d.line((x, y + h + 1, x + w, y + h + 1), fill=dark)
    d.line((x + w, y, x + w, y + h + 3), fill=dark)


def cargo():
    im, d = canvas()
    container(d, 3, 3, 12, 6, 12, 11, OUT)
    container(d, 17, 4, 11, 6, 14, 2, OUT)
    container(d, 3, 14, 11, 6, 4, 2, OUT)
    container(d, 16, 15, 12, 6, 13, 12, OUT)
    container(d, 5, 23, 10, 3, 8, 14, OUT)                          # smaller crate stack
    d.rectangle((20, 25, 26, 28), fill=9)                            # forklift
    d.line((20, 25, 26, 25), fill=10)
    d.line((19, 26, 19, 28), fill=OUT)
    return im


def command():
    im, d = canvas()
    shadow(d, [(4, 6), (27, 6), (27, 26), (4, 26)])
    box(d, 4, 5, 27, 18, 6, top=6, front=3, edge=7)                  # control building
    d.rectangle((8, 8, 14, 12), fill=4)                              # roof units
    d.line((8, 8, 14, 8), fill=7)
    d.rectangle((18, 8, 23, 11), fill=4)
    d.line((18, 8, 23, 8), fill=7)
    d.ellipse((18, 13, 23, 16), fill=7)                              # satellite dome
    d.line((25, 2, 25, 9), fill=2)                                   # antenna
    d.point((25, 1), fill=12)
    for x in range(6, 26, 4):                                        # lit windows, south wall
        d.rectangle((x, 21, x + 2, 22), fill=10)
    d.rectangle((14, 21, 17, 24), fill=2)                            # door
    d.rectangle((4, 25, 27, 25), fill=2)
    return im


def quarters():
    im, d = canvas()
    shadow(d, [(3, 4), (28, 4), (28, 27), (3, 27)])
    box(d, 3, 3, 28, 13, 12, top=7, front=4, edge=10)                # three-storey block, tall south wall
    for x in range(6, 26, 6):                                        # air conditioners
        d.rectangle((x, 5, x + 3, 7), fill=5)
        d.line((x, 5, x + 3, 5), fill=7)
    d.line((3, 10, 28, 10), fill=6)
    for y in (16, 20, 24):                                           # window rows
        for x in range(5, 27, 3):
            d.point((x, y), fill=10 if (x + y) % 7 else 2)
            d.point((x + 1, y), fill=2)
    d.line((3, 26, 28, 26), fill=2)
    d.rectangle((24, 15, 30, 18), fill=13)                           # lifeboat on the side
    d.line((24, 15, 30, 15), fill=9)
    d.line((30, 16, 30, 18), fill=12)
    return im


INTACT = {'drill': drill, 'crane': crane, 'mast': mast, 'tank': tank, 'lighthouse': lighthouse, 'cargo': cargo,
          'command': command, 'quarters': quarters}


# ------------------------------------------------------------------ wrecks
def scorch(d, rng, b, n=20):
    x0, y0, x1, y1 = b
    d.ellipse(b, fill=SHADOW)
    w, h = x1 - x0, y1 - y0
    d.ellipse((x0 + w // 5, y0 + h // 5, x1 - w // 5, y1 - h // 5), fill=SCORCH)
    for _ in range(n):
        d.point((rng.randrange(x0 - 2, x1 + 3), rng.randrange(y0 - 2, y1 + 3)), fill=SHADOW)


def debris(d, rng, b, n=9, cols=(2, 4, 6, 8)):
    x0, y0, x1, y1 = b
    for _ in range(n):
        x, y = rng.randrange(x0, x1), rng.randrange(y0, y1)
        d.line((x, y, x + rng.randrange(0, 3), y + rng.randrange(-1, 2)), fill=rng.choice(cols))


def embers(d, rng, b, n=5):
    x0, y0, x1, y1 = b
    for _ in range(n):
        d.point((rng.randrange(x0, x1), rng.randrange(y0, y1)), fill=rng.choice((13, 13, 9, 12)))


def wreck(name):
    rng = random.Random(NAMES.index(name) * 37 + 3)
    im, d = canvas()
    if name == 'drill':
        scorch(d, rng, (3, 12, 29, 30))
        d.rectangle((5, 18, 26, 27), fill=2)
        d.line((8, 22, 27, 5), fill=OUT, width=3)                    # derrick toppled across the platform
        d.line((8, 22, 27, 5), fill=13)
        for k in range(9, 27, 3):
            d.line((k, 21 - (k - 8), k + 2, 23 - (k - 8)), fill=9)
        d.rectangle((25, 2, 30, 6), fill=11)                         # crown block
        embers(d, rng, (6, 18, 25, 27))
        debris(d, rng, (3, 12, 30, 30))
    elif name == 'crane':
        scorch(d, rng, (3, 14, 22, 30))
        d.ellipse((4, 17, 15, 27), fill=2)                           # pedestal, cab gone
        d.ellipse((6, 19, 13, 24), fill=OUT)
        d.line((12, 24, 30, 28), fill=OUT, width=3)                  # boom fallen onto the deck
        d.line((12, 24, 30, 28), fill=8)
        d.rectangle((24, 20, 30, 24), fill=11)                       # dropped load
        embers(d, rng, (5, 18, 16, 27))
        debris(d, rng, (3, 12, 30, 30))
    elif name == 'mast':
        scorch(d, rng, (5, 16, 27, 30))
        d.rectangle((8, 21, 23, 27), fill=2)
        d.rectangle((10, 22, 21, 25), fill=OUT)
        d.line((13, 21, 4, 3), fill=OUT, width=3)                    # mast toppled north-west
        d.line((13, 21, 4, 3), fill=6)
        d.ellipse((1, 0, 11, 6), fill=4)                             # crushed dish
        d.line((2, 5, 9, 1), fill=OUT)
        embers(d, rng, (9, 21, 22, 26))
        debris(d, rng, (5, 14, 28, 30))
    elif name == 'tank':
        scorch(d, rng, (2, 6, 30, 31), 30)
        d.ellipse((4, 6, 27, 27), fill=OUT)                          # burst tank
        d.ellipse((6, 8, 25, 22), fill=SCORCH)
        d.arc((4, 6, 27, 27), 120, 330, fill=4, width=2)
        d.polygon([(23, 18), (30, 20), (27, 26), (21, 24)], fill=4)
        d.ellipse((8, 23, 18, 30), fill=OUT)                         # burning oil on the deck
        embers(d, rng, (8, 9, 24, 20), 9)
        embers(d, rng, (9, 24, 18, 30), 5)
        debris(d, rng, (2, 4, 30, 30))
    elif name == 'lighthouse':
        scorch(d, rng, (3, 12, 30, 31))
        d.rectangle((6, 22, 25, 28), fill=2)                         # house burnt
        d.rectangle((8, 23, 23, 26), fill=OUT)
        d.ellipse((11, 18, 20, 23), fill=4)                          # stump
        d.ellipse((12, 19, 19, 22), fill=OUT)
        for k in range(6):                                           # tower broken into ring pieces
            x, y = 15 - k * 2, 16 - k * 3
            d.ellipse((x - 3, y - 2, x + 3, y + 1), fill=12 if k % 2 else 6)
            d.point((x, y - 1), fill=2)
        embers(d, rng, (8, 22, 24, 27))
        debris(d, rng, (3, 3, 30, 30))
    elif name == 'cargo':
        scorch(d, rng, (2, 2, 30, 30))
        for x, y, w, c in ((3, 3, 12, 11), (17, 5, 11, 14), (3, 15, 11, 4), (16, 16, 12, 12)):
            d.rectangle((x, y, x + w, y + 7), fill=OUT)              # burnt-out containers, doors blown
            d.rectangle((x + 1, y + 1, x + w - 1, y + 5), fill=SCORCH)
            d.line((x, y, x + w, y), fill=c)
            d.line((x + w, y, x + w - 3, y + 7), fill=c)
        embers(d, rng, (4, 4, 28, 26), 8)
        debris(d, rng, (2, 2, 30, 30), 10, (11, 12, 14, 4))
    elif name in ('command', 'quarters'):
        scorch(d, rng, (2, 2, 30, 30))
        d.rectangle((4, 4, 27, 17), fill=OUT)                        # roof caved in, beams
        for x in range(6, 27, 5):
            d.line((x, 4, x + 1, 17), fill=4)
        d.line((4, 10, 27, 10), fill=3)
        d.polygon([(4, 4), (13, 4), (9, 10), (4, 9)], fill=6 if name == 'command' else 7)
        d.rectangle((4, 18, 27, 26), fill=2)                         # wall, windows blown out
        for x in range(6, 26, 4):
            d.rectangle((x, 20, x + 2, 22), fill=OUT)
        if name == 'quarters':
            d.rectangle((24, 23, 30, 26), fill=13)                   # lifeboat dropped
        embers(d, rng, (5, 5, 26, 16), 8)
        debris(d, rng, (2, 2, 30, 30))
    return np.array(im)


def ncm(a):
    return bytes(int(a[y, x]) | (int(a[y, x + 1]) << 4) for y in range(8) for x in range(0, 16, 2))


def untile(terr, i):
    a = np.zeros((16, 16), np.uint8)
    for half in range(2):
        g = terr[(2 * i + half) * 64:(2 * i + half) * 64 + 64]
        for y in range(8):
            for x in range(16):
                a[half * 8 + y, x] = (g[y * 8 + x // 2] >> (4 * (x & 1))) & 15
    return a


def main():
    global DECK
    tiles = {t['name']: t for t in json.loads((GEN / 'level-example.json').read_text())['tiles']}
    terr = bytearray((GEN / 'terrain.ncm.bin').read_bytes())
    deck = untile(terr, tiles['deck']['id'])
    DECK = np.tile(deck, (2, 2))
    gtp = GEN / 'ground-targets.json'
    gt = json.loads(gtp.read_text())
    dest = {d['of']: d for d in gt['destroyed_tiles']}
    pal = json.loads((GEN / 'manifest.json').read_text())['palettes']['structures']
    prev = Image.new('RGB', (len(NAMES) * 36, 72), (30, 30, 30))
    for k, name in enumerate(NAMES):
        whole, broken = np.array(INTACT[name]()), wreck(name)
        assert whole.min() > 0 and broken.min() > 0, name
        for c in range(2):
            for r in range(2):
                key = f'{name}_{c}_{r}'
                t = tiles[key]
                assert t['palette'] == 'structures' and dest[key]['palette'] == 'structures'
                cell = whole[r * 16:r * 16 + 16, c * 16:c * 16 + 16]
                terr[t['id'] * 128:t['id'] * 128 + 64] = ncm(cell[:8])
                terr[t['id'] * 128 + 64:t['id'] * 128 + 128] = ncm(cell[8:])
                dest[key]['pixels'] = [''.join(f'{v:x}' for v in row)
                                       for row in broken[r * 16:r * 16 + 16, c * 16:c * 16 + 16]]
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
