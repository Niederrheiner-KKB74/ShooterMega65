#!/usr/bin/env python3
"""Title screen and game-over banner (Stage 7) from the PR #14 artwork (assets/art/screens/generated).

Writes into build/gen/:
  TITLE   title glyphs (16x8 NCM, deduplicated) + map (20x25 words, local glyph numbers)
          + alternative row 22 without "PRESS FIRE" (blinking) + palette (48 bytes, R/G/B planes)
  GOVER   game-over banner glyphs + map (16x8 words) + palette
  screens_const.inc / screens_data.inc   layout constants, digit cells (8x8, two per glyph)

Texts drawn here with the PR #14 pixel font (tools/export_screen_art.py): "PRESS FIRE" and "HIGH SCORE" on the
title, "GAME OVER", "SCORE" and "PRESS FIRE" in the banner. The six score digits are reserved glyphs that the
game fills at run time (three glyphs, two 8-pixel digit cells each).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import make_assets as ph            # noqa: E402
import export_screen_art as art     # noqa: E402  (pixel font of PR #14)
import make_shop                    # noqa: E402  (digits 0-9 of the shop font)

SCR = ROOT / 'assets/art/screens/generated'
TITLE_DIGITS = (24, 11)     # tile row, first tile column of the 3 high-score digit glyphs (x 176-223, y 192-199)
BANNER_DIGITS = (4, 7)      # banner tile row, first tile column (x 112-159, y 32-39)


def text(a, s, x, y, colour, shadow=None):
    """PR #14 font, scale 1, left edge x (None = centred)."""
    m = np.array(art.text_mask(s, 1), dtype=bool)
    if x is None:
        x = (a.shape[1] - m.shape[1]) // 2
    if shadow is not None:
        a[y + 1:y + 1 + m.shape[0], x + 1:x + 1 + m.shape[1]][m] = shadow
    a[y:y + m.shape[0], x:x + m.shape[1]][m] = colour
    return x + m.shape[1]


def big_text(a, s, y, colour, shadow):
    m = np.array(art.text_mask(s, 2), dtype=bool)
    x = (a.shape[1] - m.shape[1]) // 2
    a[y + 1:y + 1 + m.shape[0], x + 1:x + 1 + m.shape[1]][m] = shadow
    a[y:y + m.shape[0], x:x + m.shape[1]][m] = colour


def digit_cells(colour, background):
    """10 cells of 8x8 pixels, 4 bytes per row (left pixel in the low nibble), shop-font digits."""
    out = bytearray()
    for d in '0123456789':
        cell = np.full((8, 8), background, np.uint8)
        for y, row in enumerate(make_shop.FONT[d]):
            for x, ch in enumerate(row):
                if ch == '#':
                    cell[y, 1 + x] = colour
        for y in range(8):
            out += bytes(int(cell[y, x]) | (int(cell[y, x + 1]) << 4) for x in range(0, 8, 2))
    return out


def tiles(img, reserved):
    """Deduplicated glyphs + word map; tiles in `reserved` get their own (runtime) glyphs."""
    glyphs, index, rows = [], {}, []
    for r in range(img.shape[0] // 8):
        row = []
        for c in range(img.shape[1] // 16):
            g = ph.ncm_glyph(img[r * 8:r * 8 + 8, c * 16:c * 16 + 16])
            if (r, c) in reserved:
                row.append(len(glyphs))
                glyphs.append(g)
                continue
            if g not in index:
                index[g] = len(glyphs)
                glyphs.append(g)
            row.append(index[g])
        rows.append(row)
    return glyphs, index, rows


def pal_bytes(pal):
    return bytes(ph.swap(c[ch]) for ch in range(3) for c in pal)


def words(rows):
    return b''.join(v.to_bytes(2, 'little') for row in rows for v in row)


def main(out):
    out = Path(out)
    # ---------------------------------------------------------------- title
    t_img = Image.open(SCR / 'title.png')
    title = np.array(t_img).copy()
    tpal = [tuple(t_img.getpalette()[i:i + 3]) for i in range(0, 48, 3)]
    assert title.shape == (200, 320) and not title[176:].any(), 'title: bottom 24 rows must be free'
    blank_title = title.copy()
    text(title, 'PRESS FIRE', None, 176, 15, shadow=8)    # text + shadow stay in tile row 22 (y 176-183), which blinks
    end = text(title, 'HIGH SCORE', None, 192, 7)
    title[192:200, TITLE_DIGITS[1] * 16 - 2:] = 0
    lx = TITLE_DIGITS[1] * 16 - 4 - (len('HIGH SCORE') * 6 - 1)
    title[192:200, :] = 0
    text(title, 'HIGH SCORE', lx, 192, 7)
    reserved = {(TITLE_DIGITS[0], TITLE_DIGITS[1] + k) for k in range(3)}
    glyphs, index, rows = tiles(title, reserved)
    blank = ph.ncm_glyph(np.zeros((8, 16), np.uint8))
    if blank not in index:
        index[blank] = len(glyphs)
        glyphs.append(blank)
    alt22 = [index[ph.ncm_glyph(blank_title[176:184, c * 16:c * 16 + 16])] if ph.ncm_glyph(blank_title[176:184, c * 16:c * 16 + 16]) in index
             else index[blank] for c in range(20)]
    t_digit = rows[TITLE_DIGITS[0]][TITLE_DIGITS[1]]
    t_data = b''.join(glyphs) + words(rows) + words([alt22]) + pal_bytes(tpal)
    (out / 'TITLE').write_bytes(t_data)
    t_n = len(glyphs)

    # ---------------------------------------------------------------- game-over banner
    b_img = Image.open(SCR / 'game-over-banner.png')
    banner = np.array(b_img).copy()
    bpal = [tuple(b_img.getpalette()[i:i + 3]) for i in range(0, 48, 3)]
    assert banner.shape == (64, 256)
    big_text(banner, 'GAME OVER', 8, 7, 2)
    lx = BANNER_DIGITS[1] * 16 - 4 - (len('SCORE') * 6 - 1)
    text(banner, 'SCORE', lx, 32, 6)
    text(banner, 'PRESS FIRE', None, 46, 15, shadow=2)
    reserved = {(BANNER_DIGITS[0], BANNER_DIGITS[1] + k) for k in range(3)}
    bglyphs, _, brows = tiles(banner, reserved)
    b_digit = brows[BANNER_DIGITS[0]][BANNER_DIGITS[1]]
    b_data = b''.join(bglyphs) + words(brows) + pal_bytes(bpal)
    (out / 'GOVER').write_bytes(b_data)

    consts = ['// generated by tools/make_screens.py - do not edit',
              f'.const TITLE_GLYPHS={t_n}', f'.const TITLE_MAP={t_n * 64}', f'.const TITLE_ALT22={t_n * 64 + 1000}',
              f'.const TITLE_PAL={t_n * 64 + 1040}', f'.const TITLE_BYTES={len(t_data)}',
              f'.const TITLE_DIGIT={t_digit}', f'.const TITLE_DIGIT_ROW={TITLE_DIGITS[0]}',
              f'.const GOVER_GLYPHS={len(bglyphs)}', f'.const GOVER_MAP={len(bglyphs) * 64}',
              f'.const GOVER_PAL={len(bglyphs) * 64 + 256}', f'.const GOVER_BYTES={len(b_data)}',
              f'.const GOVER_DIGIT={b_digit}']
    (out / 'screens_const.inc').write_text('\n'.join(consts) + '\n')
    data = ['// generated by tools/make_screens.py - digit cells (10 x 32 bytes)',
            'title_digits: .byte ' + ','.join(str(b) for b in digit_cells(7, 0)),
            'gover_digits: .byte ' + ','.join(str(b) for b in digit_cells(6, 1))]
    (out / 'screens_data.inc').write_text('\n'.join(data) + '\n')
    # previews
    for name, img, pal in (('title', title, tpal), ('gover', banner, bpal)):
        rgb = np.array([[pal[v] for v in row] for row in img], np.uint8)
        Image.fromarray(rgb).resize((img.shape[1] * 3, img.shape[0] * 3), Image.NEAREST).save(out / f'preview_{name}.png')
    return [f'title: {t_n} glyphs, {len(t_data)} bytes; game-over banner: {len(bglyphs)} glyphs, {len(b_data)} bytes']


if __name__ == '__main__':
    print('\n'.join(main(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'build/gen')))
