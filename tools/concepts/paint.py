"""Pixel-art painter for the concept props the game does not have (giant caps, logs, anvils, lanterns...).

The game's own props have no black outline: they are shaded in muted, hue-shifted ramps (shadows cooler, lights
warmer), lit from the upper left, with surface texture in every tone and a darker edge only where the form turns
away from the light. To match that, each prop is modelled as a few small 3D shapes (ellipsoids, lathed stems,
boxes, flat discs) z-buffered into a sprite, shaded per pixel from its normal, then quantised to a ramp with a
little ordered dither. Parts can glow (an emissive copy is returned beside the sprite).

Concept tool only.
"""
import colorsys
import math
import random

from PIL import Image

LIGHT = (-0.52, 0.62, 0.59)
_l = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _l for v in LIGHT)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def ramp(rgb, n=6, dark=0.28, light=1.22, hue_dark=0.70, hue_light=0.12, shift=0.05, sat_dark=0.12, sat_light=-0.18):
    """A shading ramp from dark to light round a base colour. Shadows lean cool, lights lean warm (as the game's
    props do), and the darkest tone keeps some saturation so it never reads as black."""
    h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in rgb])
    out = []
    for i in range(n):
        t = i / (n - 1)
        k = dark + (light - dark) * t
        hh = h
        tgt, amt = (hue_dark, (1 - t) * shift) if t < 0.5 else (hue_light, (t - 0.5) * 2 * shift)
        d = ((tgt - hh + 0.5) % 1.0) - 0.5
        hh = (hh + d * amt * 2) % 1.0
        ss = clamp(s + (sat_dark * (1 - t) * 2 if t < 0.5 else sat_light * (t - 0.5) * 2))
        vv = clamp(v * k)
        out.append(tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(hh, ss, vv)))
    return out


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


class Noise:
    def __init__(self, seed):
        self.seed, self.g = seed, {}

    def v(self, x, y, s):
        fx, fy = x / s, y / s
        ix, iy = math.floor(fx), math.floor(fy)
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        def r(a, b):
            k = (a, b, s)
            if k not in self.g:
                self.g[k] = random.Random(hash((a, b, round(s, 3), self.seed))).random()
            return self.g[k]
        return (r(ix, iy) * (1 - tx) + r(ix + 1, iy) * tx) * (1 - ty) + (r(ix, iy + 1) * (1 - tx) + r(ix + 1, iy + 1) * tx) * ty

    def fbm(self, x, y, s, oct=3):
        t, a, tot = 0.0, 1.0, 0.0
        for i in range(oct):
            t += a * self.v(x + i * 17.3, y - i * 9.1, s / (2 ** i))
            tot += a
            a *= 0.5
        return t / tot


class Mat:
    """A surface: ramp (dark to light), texture fn(x, y) -> -1..1 and its strength, an optional glow."""

    def __init__(self, rgb=None, tones=None, tex=None, tex_amp=0.18, emit=None, ambient=0.32, diffuse=0.78, spec=0.0,
                 dither=0.5, edge=True, flat=None, **ramp_kw):
        self.tones = tones or ramp(rgb, **ramp_kw)
        self.tex, self.tex_amp = tex, tex_amp
        self.emit = emit                 # fn(x, y, t) -> alpha 0..1 of glow at this pixel, or None
        self.ambient, self.diffuse, self.spec = ambient, diffuse, spec
        self.dither, self.edge, self.flat = dither, edge, flat


class Sculpt:
    """Shapes z-buffered into a sprite. Coordinates: x right, y up from the sprite's bottom row, z toward the viewer."""

    def __init__(self, w, h, seed=0):
        self.w, self.h = int(w), int(h)
        self.z = [[-1e9] * self.w for _ in range(self.h)]
        self.hit = [[None] * self.w for _ in range(self.h)]
        self.rnd = random.Random(seed)
        self.n = Noise(seed)

    def _put(self, x, y, z, nrm, mat, extra=None):
        if 0 <= x < self.w and 0 <= y < self.h and z > self.z[y][x]:
            self.z[y][x] = z
            self.hit[y][x] = (nrm, mat, extra)

    # ---- primitives (each loops over its own bounding box)
    def ellipsoid(self, cx, cy, cz, rx, ry, rz, mat, clip=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                px, py = x + 0.5, y + 0.5
                dx, dy = (px - cx) / rx, (py - cy) / ry
                q = 1 - dx * dx - dy * dy
                if q < 0 or (clip and not clip(px, py)):
                    continue
                dz = math.sqrt(q)
                nrm = (dx / rx, dy / ry, dz / rz)
                self._put(x, y, cz + dz * rz, nrm, mat, (px, py))

    def lathe(self, cx_of, y0, y1, r_of, cz, mat, depth=1.0):
        """A surface of revolution round a vertical axis that may bend: centre x cx_of(y), radius r_of(y)."""
        for y in range(int(y0), int(math.ceil(y1))):
            py = y + 0.5
            r = r_of(py)
            if r <= 0.15:
                continue
            cx = cx_of(py)
            dr = (r_of(py + 0.5) - r_of(py - 0.5))
            dc = (cx_of(py + 0.5) - cx_of(py - 0.5))
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                px = x + 0.5
                u = (px - cx) / r
                if abs(u) > 1:
                    continue
                w = math.sqrt(1 - u * u)
                nrm = (u, -dr - dc * u * 0.5, w)
                self._put(x, y, cz + w * r * depth, nrm, mat, (px, py))

    def hcyl(self, x0, x1, cy, r, cz, mat, end=None):
        """A cylinder lying along x (a log, a pipe)."""
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            py = y + 0.5
            v = (py - cy) / r
            if abs(v) > 1:
                continue
            w = math.sqrt(1 - v * v)
            for x in range(int(x0), int(math.ceil(x1))):
                self._put(x, y, cz + w * r, (0, v, w), mat, (x + 0.5, py))
        if end:
            # the cut end, facing the viewer's right
            self.ellipsoid(x1, cy, cz, max(1.2, r * 0.42), r, r * 0.2, end)

    def box(self, x0, y0, x1, y1, top, cz, mat_front, mat_top=None, mat_side=None, bevel=0.6):
        """A block seen from a little above: front face, then a top face `top` px tall above it."""
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                ex = min(x + 0.5 - x0, x1 - x - 0.5)
                b = clamp(ex / max(0.01, bevel), 0, 1)
                nrm = ((-1 if x + 0.5 - x0 < x1 - x - 0.5 else 1) * (1 - b) * 0.9, -0.15, 1)
                self._put(x, y, cz + 1, nrm, mat_front, (x + 0.5, y + 0.5))
        for y in range(int(y1), int(y1 + top)):
            for x in range(int(x0), int(x1)):
                self._put(x, y, cz + 0.5, (0, 1, 0.55), mat_top or mat_front, (x + 0.5, y + 0.5))

    def disc(self, cx, cy, rx, ry, cz, mat, nrm=(0, 1, 0.6), clip=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                px, py = x + 0.5, y + 0.5
                if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 > 1:
                    continue
                if clip and not clip(px, py):
                    continue
                self._put(x, y, cz, nrm, mat, (px, py))

    def line(self, pts, width, cz, mat, taper=True):
        """A tapering stroke (a root, a tendril, a chain): a run of small spheres along points."""
        segs = []
        for (a, b) in zip(pts, pts[1:]):
            L = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) * 2))
            for i in range(L):
                t = i / L
                segs.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        segs.append(pts[-1])
        N = len(segs)
        for i, (x, y) in enumerate(segs):
            r = width * (1 - 0.7 * i / N if taper else 1)
            r = max(0.5, r)
            self.ellipsoid(x, y, cz + (pts[0][2] if len(pts[0]) > 2 else 0), r, r, r, mat)

    def pixel(self, x, y, cz, mat, nrm=(0, 0, 1)):
        self._put(int(x), int(y), cz, nrm, mat, (x, y))

    # ---- shading
    def render(self, light=LIGHT):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        em = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px, ep = im.load(), em.load()
        idx = [[None] * self.w for _ in range(self.h)]
        for y in range(self.h):
            for x in range(self.w):
                hit = self.hit[y][x]
                if not hit:
                    continue
                (nx, ny, nz), mat, ex = hit
                l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
                nx, ny, nz = nx / l, ny / l, nz / l
                d = max(0.0, nx * light[0] + ny * light[1] + nz * light[2])
                t = mat.ambient + mat.diffuse * d
                if mat.spec:
                    hx, hy, hz = light[0], light[1], light[2] + 1
                    hl = math.sqrt(hx * hx + hy * hy + hz * hz)
                    t += mat.spec * max(0, (nx * hx + ny * hy + nz * hz) / hl) ** 18
                if mat.tex:
                    t += mat.tex(ex[0], ex[1]) * mat.tex_amp
                if mat.flat is not None:
                    t = mat.flat
                n = len(mat.tones)
                f = clamp(t) * (n - 1) + (BAYER[y % 4][x % 4] / 16 - 0.5) * mat.dither
                k = int(round(clamp(f, 0, n - 1)))
                idx[y][x] = (k, mat)
                if mat.emit:
                    a = mat.emit(ex[0], ex[1], t)
                    if a and a > 0:
                        c = mat.tones[k]
                        ep[x, self.h - 1 - y] = c + (int(255 * clamp(a)),)
        # the form's edge: one tone darker where it meets nothing below or to the right (turning from the light)
        for y in range(self.h):
            for x in range(self.w):
                v = idx[y][x]
                if not v:
                    continue
                k, mat = v
                if mat.edge:
                    below = y == 0 or idx[y - 1][x] is None
                    right = x == self.w - 1 or idx[y][x + 1] is None
                    left = x == 0 or idx[y][x - 1] is None
                    above = y == self.h - 1 or idx[y + 1][x] is None
                    if below or right:
                        k = max(0, k - 2 if below and right else k - 1)
                    elif (left or above) and k < len(mat.tones) - 2:
                        k = k + 1 if self.rnd.random() < 0.5 else k
                px[x, self.h - 1 - y] = mat.tones[k] + (255,)
        return im, (em if em.getbbox() else None)


def shadow(w, h=None, alpha=110, colour=(10, 6, 14)):
    """A ground shadow like the game's: a soft-edged dark ellipse, two steps of alpha."""
    h = h or max(3, int(w * 0.32))
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    px = im.load()
    cx, cy = w / 2, h / 2
    for y in range(int(h)):
        for x in range(int(w)):
            d = ((x + 0.5 - cx) / (w / 2)) ** 2 + ((y + 0.5 - cy) / (h / 2)) ** 2
            if d <= 1:
                px[x, y] = colour + (alpha if d < 0.55 else int(alpha * 0.6),)
    return im


def trim(im, em=None):
    bb = im.getbbox()
    if not bb:
        return im, em
    return im.crop(bb), (em.crop(bb) if em is not None else None)
