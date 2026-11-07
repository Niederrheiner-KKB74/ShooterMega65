"""Small vector-to-pixel renderer for Claude's sprites (Stage 14g).

Shapes are described in the sprite's own coordinates (front = down = +y, centre at the origin) and rasterised
for any of the 8 view directions by rotating the shapes, not the pixels, so diagonal views stay clean. Every
shape has a colour ramp (dark, mid, light): pixels on the side facing the light (top left of the screen) get the
light colour, the opposite side the dark one. A 1-pixel outline is drawn around the silhouette at the end.

    c = Canvas(16, 16)
    c.ellipse(0, 2, 2.5, 4, RAMP_STEEL)
    pixels = c.render(angle_deg)     # 2-D numpy array of palette indices
"""
import math

import numpy as np

OUTLINE = 1
DIRS8 = {'south': 0, 'southwest': 45, 'west': 90, 'northwest': 135, 'north': 180, 'northeast': 225,
         'east': 270, 'southeast': 315}


class Canvas:
    def __init__(self, w, h, ox=None, oy=None):
        self.w, self.h = w, h
        self.ox = (w - 1) / 2 if ox is None else ox
        self.oy = (h - 1) / 2 if oy is None else oy
        self.shapes = []          # (kind, params, ramp, layer flags)

    # ---- shapes (sprite coordinates, front = +y)
    def ellipse(self, x, y, rx, ry, ramp, rot=0.0, shade=True, outline=True):
        self.shapes.append(('ell', (x, y, rx, ry, math.radians(rot)), ramp, shade, outline))

    def capsule(self, x0, y0, x1, y1, r, ramp, shade=True, outline=True):
        self.shapes.append(('cap', (x0, y0, x1, y1, r), ramp, shade, outline))

    def poly(self, pts, ramp, shade=True, outline=True):
        self.shapes.append(('poly', tuple(pts), ramp, shade, outline))

    def dot(self, x, y, colour):
        self.shapes.append(('dot', (x, y), (colour, colour, colour), False, False))

    def line(self, x0, y0, x1, y1, colour, outline=False, dash=0):
        """dash > 0: only every other `dash` px along the line (motion blur of rotor blades)"""
        self.shapes.append(('line', (x0, y0, x1, y1, dash), (colour, colour, colour), False, outline))

    # ---- rendering
    def render(self, angle=0.0, light=(-1.0, -1.0), roll=0.0):
        """angle: view direction in degrees (0 = front down, clockwise on screen); roll: banking -1..1 squeezes
        x on one side (lowered side = sign of roll)."""
        a = math.radians(angle)
        ca, sa = math.cos(a), math.sin(a)
        lx, ly = light
        ln = math.hypot(lx, ly)
        lx, ly = lx / ln, ly / ln
        img = np.zeros((self.h, self.w), np.uint8)
        sil = np.zeros((self.h, self.w), bool)
        ol = np.zeros((self.h, self.w), bool)
        for kind, p, ramp, shade, outline in self.shapes:
            for py in range(self.h):
                for px in range(self.w):
                    # screen -> sprite coordinates (inverse rotation), banking squeezes one side
                    sx, sy = px - self.ox, py - self.oy
                    u, v = ca * sx + sa * sy, -sa * sx + ca * sy
                    if roll:
                        k = 1 + 0.45 * abs(roll) if u * roll > 0 else 1 - 0.12 * abs(roll)
                        u = u * k
                    hit, nx, ny = self._inside(kind, p, u, v)
                    if not hit:
                        continue
                    if shade:
                        # normal back to screen space
                        snx, sny = ca * nx - sa * ny, sa * nx + ca * ny
                        d = snx * lx + sny * ly
                        c = ramp[2] if d > 0.35 else (ramp[0] if d < -0.35 else ramp[1])
                    else:
                        c = ramp[1]
                    img[py, px] = c
                    if outline:
                        sil[py, px] = True
                    elif kind != 'line':
                        sil[py, px] = True
        for py in range(self.h):
            for px in range(self.w):
                if img[py, px] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        qx, qy = px + dx, py + dy
                        if 0 <= qx < self.w and 0 <= qy < self.h and sil[qy, qx]:
                            ol[py, px] = True
                            break
        img[ol] = OUTLINE
        return img

    @staticmethod
    def _inside(kind, p, u, v):
        if kind == 'ell':
            x, y, rx, ry, rot = p
            cu, cv = u - x, v - y
            cr, sr = math.cos(rot), math.sin(rot)
            a, b = cr * cu + sr * cv, -sr * cu + cr * cv
            q = (a / rx) ** 2 + (b / ry) ** 2
            if q <= 1.0:
                n = math.hypot(cu, cv) or 1
                return True, cu / n * math.sqrt(q), cv / n * math.sqrt(q)
            return False, 0, 0
        if kind == 'cap':
            x0, y0, x1, y1, r = p
            dx, dy = x1 - x0, y1 - y0
            ll = dx * dx + dy * dy or 1
            t = max(0, min(1, ((u - x0) * dx + (v - y0) * dy) / ll))
            qx, qy = x0 + t * dx, y0 + t * dy
            d = math.hypot(u - qx, v - qy)
            if d <= r:
                return True, (u - qx) / r, (v - qy) / r
            return False, 0, 0
        if kind == 'poly':
            pts = p
            inside = False
            for i in range(len(pts)):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % len(pts)]
                if (ay > v) != (by > v) and u < (bx - ax) * (v - ay) / (by - ay) + ax:
                    inside = not inside
            if inside:
                cx = sum(q[0] for q in pts) / len(pts)
                cy = sum(q[1] for q in pts) / len(pts)
                n = max(1.0, max(math.hypot(q[0] - cx, q[1] - cy) for q in pts))
                return True, (u - cx) / n, (v - cy) / n
            return False, 0, 0
        if kind == 'dot':
            x, y = p
            return (abs(u - x) <= 0.5 and abs(v - y) <= 0.5), 0, 0
        if kind == 'line':
            x0, y0, x1, y1, dash = p
            dx, dy = x1 - x0, y1 - y0
            ll = dx * dx + dy * dy or 1
            t = max(0, min(1, ((u - x0) * dx + (v - y0) * dy) / ll))
            if dash and int(t * math.sqrt(ll) / dash) % 2:
                return False, 0, 0
            return math.hypot(u - (x0 + t * dx), v - (y0 + t * dy)) <= 0.55, 0, 0
        return False, 0, 0


def rows(img):
    return [''.join(f'{v:02x}' for v in r) for r in img]
