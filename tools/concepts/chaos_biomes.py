"""Concept art for Crawl Chaos's floors: six biomes, three rooms each, built the way the game builds its rooms.

    python3 tools/concepts/chaos_biomes.py <outdir>

What a Crawl room is (read from the game's atlases, e.g. AtlasEnvironmentCrypt crypt_large1_floor / _wall and the
prop atlases):
  - the floor is one painted image the size of the room. Its tones are close together (the crypt floor's main
    colours are all within about 15 of each other), mottled in small soft clusters, with the stone pattern only
    one tone darker and a lighter area in the middle. Rooms are not always rectangles: corners are cut, alcoves
    stick out, corridors bend;
  - the back wall is one strip about 30 px tall: a cap line, a darker brick face, pillars and arches in the lighter
    stone, slit windows, a dark skirting. No side or bottom walls, only black;
  - props are small and muted, outlined in a dark shade of their own colour (not black), shaded in three or four
    tones, standing on a soft shadow. Debris, bones and bits are scattered as tiny clusters;
  - the life in a room comes from what is in it: rugs and inlays, scattered debris, lit braziers and their pools.

Each room here follows that: narrow tone ranges, clustered mottling (no checker dither on floors), patterns one
tone off, prop outlines in their own hue, decals scattered, and one of our monsters at its real size.

Concepts only: nothing here ships with the mod.
"""
import colorsys
import json
import math
import os
import random
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCALE = 3
VOIDC = (9, 8, 11)



def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hx(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def ramp(base, n=8, lo=0.42, hi=1.28, hue_dark=0.03, sat_dark=0.18):
    """Tones of one material, dark to light. Darker tones lean cooler and a little more saturated, lighter ones warmer
    and paler, the way the game's art shades."""
    h, s, v = colorsys.rgb_to_hsv(*[c / 255.0 for c in base])
    out = []
    for i in range(n):
        t = i / (n - 1)
        k = lo + (hi - lo) * t
        hh = (h + hue_dark * (0.5 - t)) % 1.0
        ss = clamp(s * (1 + sat_dark * (0.5 - t) * 2) * (1.0 if t < 0.8 else 0.85))
        vv = clamp(v * k)
        out.append(tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(hh, ss, vv)))
    return out


# ------------------------------------------------------------------ noise
class Noise:
    def __init__(self, seed):
        self.seed = seed
        self.g = {}

    def v(self, ix, iy, s):
        k = (ix, iy, s)
        if k not in self.g:
            self.g[k] = random.Random(hash((ix, iy, s, self.seed))).random()
        return self.g[k]

    def value(self, x, y, s):
        fx, fy = x / s, y / s
        ix, iy = int(math.floor(fx)), int(math.floor(fy))
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a, b = self.v(ix, iy, s), self.v(ix + 1, iy, s)
        c, d = self.v(ix, iy + 1, s), self.v(ix + 1, iy + 1, s)
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty

    def cluster(self, x, y):
        """The game's floor mottle: soft blobs a few pixels across, stepped."""
        return 0.55 * self.value(x, y, 3.2) + 0.3 * self.value(x, y, 7) + 0.15 * self.value(x, y, 16)


# ------------------------------------------------------------------ sprites
class Spr:
    def __init__(self, w, h):
        self.w, self.h = int(w), int(h)
        self.im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.px = self.im.load()

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = tuple(c[:3]) + (255,)

    def get(self, x, y):
        x, y = int(x), int(y)
        return self.px[x, y] if 0 <= x < self.w and 0 <= y < self.h else (0, 0, 0, 0)

    def fill(self, tones, inside, tone):
        """Paint tones[tone(x, y)] where inside(x, y); tone returns a float index (rounded)."""
        for y in range(self.h):
            for x in range(self.w):
                if inside(x, y):
                    t = tone(x, y)
                    self.put(x, y, tones[int(clamp(round(t), 0, len(tones) - 1))])

    def outline(self, c):
        src = self.im.copy(); sp = src.load()
        for y in range(self.h):
            for x in range(self.w):
                if sp[x, y][3]: continue
                if any(0 <= x + dx < self.w and 0 <= y + dy < self.h and sp[x + dx, y + dy][3]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.px[x, y] = tuple(c) + (255,)
        return self

    def mirror(self):
        self.im = self.im.transpose(Image.FLIP_LEFT_RIGHT); self.px = self.im.load()
        return self


def ell(cx, cy, rx, ry):
    return lambda x, y: ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def box(x0, y0, x1, y1):
    return lambda x, y: x0 <= x < x1 and y0 <= y < y1


def roundlit(cx, cy, rx, ry, n=6, hi=0.9):
    """Tone for a rounded form lit from the upper left, as an index into an n-tone ramp."""
    def f(x, y):
        dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        t = 0.5 - 0.32 * dx - 0.38 * dy + 0.15 * (1 - min(1.0, dx * dx + dy * dy))
        return clamp(t, 0, hi) * (n - 1)
    return f


def boxlit(x0, y0, x1, y1, n=6, top=2):
    """A box seen from the front and a little above: lit top face, mid front, darker right edge."""
    def f(x, y):
        if y < y0 + top: return n - 2
        t = 0.55 - 0.25 * (x - x0) / max(1, x1 - x0) - 0.15 * (y - y0) / max(1, y1 - y0)
        if x == x0: t += 0.12
        if x == x1 - 1: t -= 0.15
        return clamp(t) * (n - 1)
    return f


# ------------------------------------------------------------------ a room
class Room:
    """A room canvas: the floor shape (a set of rects, minus cut-outs), a back wall strip above the top edge of each
    rect that faces the void, props, decals and lights."""

    def __init__(self, w, h, seed, wall=30, margin=10):
        self.w, self.h, self.wh, self.m = w, h, wall, margin
        self.W, self.H = w + margin * 2, h + wall + margin * 2
        self.cv = Spr(self.W, self.H)
        for y in range(self.H):
            for x in range(self.W):
                self.cv.px[x, y] = VOIDC + (255,)
        self.ox, self.oy = margin, margin + wall      # floor origin on the canvas
        self.n = Noise(seed)
        self.r = random.Random(seed)
        self.lights = []
        self.inside = lambda u, v: True
        self.props = []

    def at(self, u, v):
        return self.ox + u, self.oy + v

    def on(self, u, v):
        return 0 <= u < self.w and 0 <= v < self.h and self.inside(u, v)

    # floors
    def floor(self, tones, pattern=None, inside=None, mid=0.9, spread=1.6, centre=0.8, overlay=None):
        """Paint the floor. tones is a ramp; the floor uses a narrow band round index mid*len (spread tones wide),
        mottled in clusters; pattern(u, v) returns -1 (seam: one tone darker), +1 (a lit edge) or 0; overlay(u, v)
        may return a colour to paint instead."""
        if inside: self.inside = inside
        n = len(tones)
        base = mid * (n - 1)
        for v in range(self.h):
            for u in range(self.w):
                if not self.inside(u, v): continue
                x, y = self.at(u, v)
                if overlay:
                    c = overlay(u, v)
                    if c is not None:
                        self.cv.put(x, y, c); continue
                t = base + (self.n.cluster(x, y) - 0.5) * spread * 2
                d = ((u - self.w / 2) / (self.w * 0.52)) ** 2 + ((v - self.h / 2) / (self.h * 0.6)) ** 2
                t += centre * (1 - min(1.0, d)) - 0.5
                # darker toward the room's edges
                edge = min(u, self.w - 1 - u, self.h - 1 - v)
                if not self.inside(u - 1, v) or not self.inside(u + 1, v) or not self.inside(u, v + 1): edge = 0
                if edge < 2: t -= 0.8
                if pattern:
                    p = pattern(u, v)
                    t += 1.0 * p
                self.cv.put(x, y, tones[int(clamp(round(t), 0, n - 1))])
        # contact shadow under the back wall
        for u in range(self.w):
            for k in range(3):
                if self.on(u, k) and not self.on(u, k - 1 - 0):
                    pass
            if self.on(u, 0):
                for k in range(2):
                    x, y = self.at(u, k)
                    self.cv.put(x, y, mix(self.cv.get(x, y)[:3], VOIDC, 0.5 - k * 0.25))

    def wall(self, face, tones, features=(), cap=None):
        """The back wall strip over every floor column whose top edge meets the void. face(u, v) gives a tone index
        (-1 seam) for the wall's material; features draw on top (pillars, arches, windows...)."""
        n = len(tones)
        top_of = {}
        for u in range(-1, self.w + 1):
            for v in range(self.h):
                if self.on(u, v) or self.on(u - 1, v) or self.on(u + 1, v):
                    top_of[u] = v; break
        self.top_of = top_of
        for u, v0 in top_of.items():
            for k in range(self.wh):
                x, y = self.at(u, v0 - self.wh + k)
                t = face(u, k)
                if t is None: continue
                t += (self.n.cluster(x * 1.5, y * 1.5) - 0.5) * 1.2
                t -= 1.4 * max(0, (k - (self.wh - 7)) / 7.0)     # darker toward the skirting
                self.cv.put(x, y, tones[int(clamp(round(t), 0, n - 1))])
            x, y = self.at(u, v0 - self.wh)
            self.cv.put(x, y, cap or tones[-2]); self.cv.put(x, y + 1, tones[-3])
            x, y = self.at(u, v0 - 1)
            self.cv.put(x, y, tones[0])
        for f in features:
            f(self)

    def wx(self, u, k):
        """Canvas position of wall column u, k pixels down from the cap."""
        if u not in self.top_of: return (-99, -99)
        return self.at(u, self.top_of[u] - self.wh + k)

    # things in the room
    def stamp(self, s, u, v, shadow=0.45, ax=0.5, ay=1.0):
        x, y = self.at(u, v)
        if shadow:
            rx = max(3.0, s.w * 0.45)
            for yy in range(-2, 3):
                for xx in range(-int(rx) - 1, int(rx) + 2):
                    if (xx / rx) ** 2 + (yy / 2.3) ** 2 <= 1:
                        c = self.cv.get(x + xx, y + yy)
                        if c[3]: self.cv.put(x + xx, y + yy, mix(c[:3], VOIDC, shadow))
        self.cv.im.alpha_composite(s.im, (int(x - s.w * ax), int(y - s.h * ay)))
        self.cv.px = self.cv.im.load()

    def scatter(self, maker, count, area=None, avoid=0, shadow=0):
        """Place count small things at random floor spots (inside area (u0, v0, u1, v1) if given)."""
        u0, v0, u1, v1 = area or (3, 4, self.w - 3, self.h - 3)
        placed = 0
        tries = 0
        while placed < count and tries < count * 30:
            tries += 1
            u, v = self.r.uniform(u0, u1), self.r.uniform(v0, v1)
            if not self.on(int(u), int(v)): continue
            self.stamp(maker(self.r), u, v, shadow=shadow)
            placed += 1

    def light(self, u, v, r, c, k=0.6):
        x, y = self.at(u, v)
        self.lights.append((x, y, r, c, k))

    def finish(self, ambient=0.86):
        out = self.cv.im.copy(); px = out.load()
        for y in range(self.H):
            for x in range(self.W):
                c = px[x, y]
                if c[:3] == VOIDC: continue
                f = ambient
                add = [0.0, 0.0, 0.0]
                for (lx, ly, r, col, k) in self.lights:
                    d = math.hypot(x - lx, (y - ly) * 1.45) / r
                    if d < 1:
                        t = (1 - d) ** 1.7 * k
                        # stepped falloff, as the game's light pools look in pixels
                        t = math.floor(t * 6 + self.n.cluster(x * 1.3, y * 1.3)) / 6.0
                        f += t * 0.45
                        for i in range(3): add[i] += col[i] * t * 0.28
                px[x, y] = tuple(int(clamp(c[i] * f + add[i], 0, 255)) for i in range(3)) + (255,)
        return out.resize((self.W * SCALE, self.H * SCALE), Image.NEAREST)


# ------------------------------------------------------------------ floor patterns
def flags(cw=14, ch=9, seed=1, tone_var=0.6):
    rows = {}
    def cuts(row):
        if row not in rows:
            r = random.Random(row * 977 + seed); x, c = -r.randint(0, cw), []
            while x < 900: c.append(x); x += r.randint(int(cw * 0.6), int(cw * 1.45))
            rows[row] = c
        return rows[row]
    def f(u, v):
        row = v // ch; c = cuts(row)
        i = max(k for k in range(len(c)) if c[k] <= u)
        su, sv = u - c[i], v % ch
        if su == 0 or sv == 0: return -1
        t = random.Random(hash((row, i, seed))).uniform(-tone_var, tone_var) * 0.6
        return t + (0.6 if sv == 1 else 0)
    return f


def bricks(bw=9, bh=4, seed=2):
    def f(u, v):
        row = v // bh; off = (row % 2) * (bw // 2)
        if (u + off) % bw == 0 or v % bh == 0: return -1
        return 0.6 if v % bh == 1 else random.Random(hash(((u + off) // bw, row, seed))).uniform(-0.4, 0.4)
    return f


def boards(bh=5, seed=3):
    def f(u, v):
        row = v // bh
        r = random.Random(row * 7919 + seed)
        seams = set(r.sample(range(4, 900), 40))
        if v % bh == 0 or u in seams: return -1
        return (0.5 if v % bh == 1 else 0) + 0.35 * math.sin(u * 0.4 + row * 1.7) * (1 if (u // 3 + row) % 4 else 0)
    return f


def plates(pw=22, ph=14, seed=4):
    def f(u, v):
        su, sv = u % pw, v % ph
        if su == 0 or sv == 0: return -1
        if su in (2, pw - 2) and sv in (2, ph - 2): return 1.2
        return 0.5 if sv == 1 else -0.2 * sv / ph
    return f


def plain():
    return lambda u, v: 0


# ------------------------------------------------------------------ wall faces and features
def face_bricks(bw=8, bh=4, base=3.0, seed=5):
    def f(u, k):
        row = k // bh; off = (row % 2) * (bw // 2)
        if (u + off) % bw == 0 or k % bh == 0: return base - 1.2
        return base + (0.7 if k % bh == 1 else 0) + random.Random(hash(((u + off) // bw, row, seed))).uniform(-0.6, 0.6)
    return f


def face_rough(base=3.0, seed=6):
    def f(u, k):
        return base + math.sin(u * 0.21 + k * 0.5) * 0.6 + math.sin(u * 0.07) * 0.5
    return f


def pillars(every, tones, width=5, arch=True):
    """Stone pillars on the wall every `every` px, with arches springing between them (the crypt wall's look)."""
    def draw(R):
        us = sorted(R.top_of)
        for u in range(us[0] + every // 2, us[-1] - 2, every):
            for k in range(2, R.wh - 1):
                for i in range(width):
                    x, y = R.wx(u + i, k)
                    t = 5 if i == 0 else 4 if i < width - 1 else 2
                    if k > R.wh - 4: t -= 1
                    R.cv.put(x, y, tones[t])
            if arch:
                # arch from this pillar to the next
                for i in range(every - width):
                    a = i / (every - width)
                    kk = 3 + int(7 * (1 - math.sin(a * math.pi)))
                    x, y = R.wx(u + width + i, kk)
                    R.cv.put(x, y, tones[5]); R.cv.put(x, y + 1, tones[2])
    return draw


def slits(every, tones, glass=None, h=12, w=3, top=8):
    def draw(R):
        us = sorted(R.top_of)
        for j, u in enumerate(range(us[0] + every, us[-1] - 4, every)):
            g = glass[j % len(glass)] if glass else None
            for k in range(top, top + h):
                for i in range(-1, w + 1):
                    x, y = R.wx(u + i, k)
                    if i in (-1, w): R.cv.put(x, y, tones[5] if i == -1 else tones[2])
                    else:
                        if g: R.cv.put(x, y, g[(k + i) % len(g)] if (k - top) % 4 else tones[0])
                        else: R.cv.put(x, y, tones[0] if k > top else tones[1])
            for i in range(-1, w + 1):
                x, y = R.wx(u + i, top + h); R.cv.put(x, y, tones[5])
            if top > 2:
                x, y = R.wx(u + w // 2, top - 1); R.cv.put(x, y, tones[5])
    return draw


def hang(every, maker, k=2, start=None):
    """Hang a sprite on the wall (banners, shelves, skulls...)."""
    def draw(R):
        us = sorted(R.top_of)
        for j, u in enumerate(range((start if start is not None else us[0] + every // 2), us[-1] - 4, every)):
            s = maker(j)
            x, y = R.wx(u, k)
            R.cv.im.alpha_composite(s.im, (int(x - s.w / 2), int(y)))
            R.cv.px = R.cv.im.load()
    return draw


# ------------------------------------------------------------------ props (library)
def outline_of(tones):
    return mix(tones[0], VOIDC, 0.35)


def brazier(metal, size=1.0):
    s = Spr(12, 20)
    s.fill(metal, lambda x, y: (8 <= y < 11 and 1 <= x < 11) or (11 <= y < 16 and 4 <= x < 8) or (16 <= y < 19 and 2 <= x < 10),
           lambda x, y: 6 if y == 8 else 4 - (x - 2) * 0.3 if y < 11 else 3 - (x - 4) * 0.4)
    fl = [hx("#5a1f0c"), hx("#b23e10"), hx("#e8701c"), hx("#f7a837"), hx("#fde39a")]
    s.fill(fl, lambda x, y: 1 < y < 8 and abs(x - 5.5) < (8 - y) * 0.42 + 0.6, lambda x, y: 4 - abs(x - 5.5) * 0.9 - (7 - y) * 0.25)
    return s.outline(outline_of(metal))


def candles(wax, metal, n=3):
    s = Spr(2 * n + 3, 16)
    s.fill(metal, lambda x, y: (x == s.w // 2 and 5 <= y < 15) or (y == 15 and 1 <= x < s.w - 1) or (y == 5 and 1 <= x < s.w - 1), lambda x, y: 4)
    for i in range(n):
        cx = 1 + i * 2
        s.fill(wax, lambda x, y, cx=cx: x == cx and 2 <= y < 5, lambda x, y: 5 - (y - 2))
        s.put(cx, 1, hx("#f7b244")); s.put(cx, 0, hx("#fff0c0"))
    return s.outline(outline_of(metal))


def pile(tones, n=7, w=14, h=7, seed=0, r0=2.4):
    s = Spr(w, h)
    rnd = random.Random(seed)
    for i in range(n):
        cx, cy = rnd.uniform(r0, w - r0), rnd.uniform(h * 0.4, h - 1.5)
        s.fill(tones, ell(cx, cy, r0 * rnd.uniform(0.7, 1.1), r0 * 0.55), roundlit(cx, cy, r0, r0 * 0.55, len(tones)))
    return s.outline(outline_of(tones))


def debris(tones):
    """Tiny loose bits, like the game's prc_deb sprites (no outline, no shadow)."""
    def make(r):
        s = Spr(7, 4)
        for _ in range(r.randint(2, 5)):
            x, y = r.randint(0, 6), r.randint(1, 3)
            s.put(x, y, tones[r.randint(1, 3)])
            if r.random() < 0.4: s.put(x + 1, y, tones[r.randint(2, 4)])
        return s
    return make


def chest(wood, metal):
    s = Spr(14, 10)
    s.fill(wood, box(0, 2, 14, 10), boxlit(0, 2, 14, 10, len(wood), top=2))
    s.fill(wood, box(1, 0, 13, 2), lambda x, y: 6)
    for x in range(14): s.put(x, 4, metal[3])
    s.put(6, 5, metal[6]); s.put(7, 5, metal[5]); s.put(6, 6, metal[3]); s.put(7, 6, metal[2])
    return s.outline(outline_of(wood))


def barrel(wood, metal):
    s = Spr(10, 13)
    s.fill(wood, lambda x, y: 1 <= y < 13 and abs(x - 4.5) <= 4 - (1 if y in (1, 12) else 0), roundlit(4.5, 6, 4.5, 6, len(wood)))
    s.fill(wood, ell(4.5, 1.5, 4, 1.4), lambda x, y: 6)
    for y in (3, 9):
        for x in range(10):
            if s.get(x, y)[3]: s.put(x, y, metal[2 if x > 5 else 4])
    return s.outline(outline_of(wood))


def statue(stone, pose=0):
    """A small robed figure on a plinth."""
    s = Spr(12, 24)
    s.fill(stone, box(1, 19, 11, 24), boxlit(1, 19, 11, 24, len(stone), top=1))
    s.fill(stone, lambda x, y: 6 <= y < 19 and abs(x + 0.5 - 6) <= 2 + (y - 6) * 0.2, lambda x, y: 4.5 - (x - 3) * 0.45)
    s.fill(stone, ell(6, 4, 2.4, 2.6), roundlit(6, 4, 2.4, 2.6, len(stone)))
    if pose == 1:
        for i in range(5): s.put(3 - i * 0.4, 9 + i, stone[5]); s.put(9 + i * 0.3, 8 - i, stone[3])
    return s.outline(outline_of(stone))


def pillar_prop(stone, h=30, broken=False):
    s = Spr(10, h)
    hh = h if not broken else h * 0.55
    s.fill(stone, lambda x, y: y >= h - hh and 2 <= x < 8, lambda x, y: 5 if x == 2 else 4 if x < 5 else 2)
    s.fill(stone, box(1, h - 3, 9, h), boxlit(1, h - 3, 9, h, len(stone), top=1))
    if not broken: s.fill(stone, box(1, 0, 9, 3), boxlit(1, 0, 9, 3, len(stone), top=1))
    else:
        top = int(h - hh)
        for x in range(2, 8):
            if (x * 7) % 3 == 0: s.put(x, top, (0, 0, 0, 0)) if False else None
    return s.outline(outline_of(stone))


def hero():
    rows = ["....oo.......", "...oSSo......", "..oSssso.....", "..oSkkso...w.", "..osssso..ow.", "...oSso...ow.",
            "..oRRRRo..ow.", ".oRrrrrRo.ow.", "oBoRrrrRo.ow.", "oBBoRrrRohgho", "oBBoRrrRo.o..", ".oBoRRRRo....",
            "..ooDDDDo....", "...oDooDo....", "...oDo.Do....", "...oLo.Lo....", "...ooo.oo...."]
    col = {"o": (20, 14, 16), "S": (196, 204, 214), "s": (128, 138, 152), "k": (30, 28, 36), "R": (170, 70, 56),
           "r": (124, 46, 40), "B": (118, 90, 58), "D": (62, 48, 44), "L": (40, 30, 28), "w": (220, 226, 236),
           "h": (150, 112, 60), "g": (210, 170, 90)}
    s = Spr(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in col: s.put(x, y, col[ch])
    return s


def sprite(sheet, frame=0, flip=False):
    for d in sorted(os.listdir(os.path.join(ROOT, "art"))):
        p = os.path.join(ROOT, "art", d, sheet + ".json")
        if os.path.exists(p):
            m = json.load(open(p))
            im = Image.open(p[:-5] + ".png").convert("RGBA")
            c, r = frame % m["cols"], frame // m["cols"]
            cell = im.crop((c * m["cellW"], r * m["cellH"], (c + 1) * m["cellW"], (r + 1) * m["cellH"]))
            bb = cell.getbbox()
            cell = cell.crop(bb) if bb else cell
            if flip: cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
            s = Spr(cell.size[0], cell.size[1]); s.im = cell; s.px = cell.load()
            return s
    return None


def cast(R, monster, mu, mv, hu, hv, flip=False):
    m = sprite(monster, flip=flip)
    if m: R.stamp(m, mu, mv, shadow=0.5)
    R.stamp(hero(), hu, hv, shadow=0.5)


def cut_corners(w, h, c=12, alcoves=()):
    """A floor shape: the rect with its bottom corners cut and optional alcoves (u0, v0, u1, v1) added."""
    def f(u, v):
        for (a, b, cc, d) in alcoves:
            if a <= u < cc and b <= v < d: return True
        if not (0 <= u < w and 0 <= v < h): return False
        if v > h - c and (u < c - (h - v) or u > w - 1 - c + (h - v)): return False
        return True
    return f


# ------------------------------------------------------------------ materials
STONE_G = ramp(hx("#7d887f"))
BRINE = [hx("#0a1c22"), hx("#0f2c35"), hx("#163d47"), hx("#1f525b"), hx("#2c6a70"), hx("#4a8a86"), hx("#86b8ab"), hx("#c5e0d3")]
WOOD = ramp(hx("#6e4a33"))
BRASS = ramp(hx("#a5853f"))
MOSS = ramp(hx("#3e5a35"))
GLASS = [[hx("#4c1b1d"), hx("#7f3330"), hx("#a54f3d")], [hx("#162c43"), hx("#2a547a"), hx("#4c82a2")],
         [hx("#40330f"), hx("#7a6424"), hx("#ad9443")]]

ASH = ramp(hx("#6f685f"))
BONE = ramp(hx("#c4bb9f"), lo=0.35, hi=1.18)
EARTH = ramp(hx("#5e4a3c"))
LANTERN = [hx("#5a2a0c"), hx("#b5651d"), hx("#f0a442"), hx("#ffe08a")]

IRON = ramp(hx("#5b524e"), lo=0.3, hi=1.35)
BRICK = ramp(hx("#7a4a3c"))
MOLTEN = [hx("#4a1006"), hx("#8f290a"), hx("#d0561a"), hx("#f08a2e"), hx("#fbb85a"), hx("#ffe39a"), hx("#fff6d6")]
COAL = ramp(hx("#333033"), lo=0.4, hi=1.5)

SOIL = ramp(hx("#5e4b57"))
CAVE = ramp(hx("#544650"))
CAP_T = [hx("#0d2a2e"), hx("#134a51"), hx("#1c6f75"), hx("#2f9a96"), hx("#5cc4b5"), hx("#a8ead9")]
CAP_G = [hx("#22300d"), hx("#3b5414"), hx("#5f841e"), hx("#88b032"), hx("#bfdc6a"), hx("#ecf8b0")]
STEM = ramp(hx("#bdb2a2"), lo=0.4, hi=1.15)

BOARD = ramp(hx("#6b4c32"))
SHELF = ramp(hx("#5a3c28"))
PAPER = ramp(hx("#d8ccaa"), lo=0.5, hi=1.12)
RUG_R = ramp(hx("#7a2c2c"))
INK = [hx("#07080d"), hx("#0e111a"), hx("#171c2a"), hx("#232b40"), hx("#323d58")]
BOOKS = [ramp(hx("#7a2a26"))[2:5], ramp(hx("#2a4f6a"))[2:5], ramp(hx("#7a6428"))[2:5], ramp(hx("#3a5a2c"))[2:5]]

VOID = [hx("#07040b"), hx("#120a1c"), hx("#1e1131"), hx("#311b51"), hx("#53308a"), hx("#8a5cc8"), hx("#c7a6f2"), hx("#f1e6ff")]
CRYPT = ramp(hx("#857b5c"))


# ------------------------------------------------------------------ the biomes and their rooms
BIOMES = []


def biome(**info):
    def deco(fn):
        BIOMES.append((fn, info))
        return fn
    return deco


# ======== Drowned Nave
def pew(w, broken=False):
    s = Spr(w, 10)
    s.fill(WOOD, lambda x, y: (y < 4 and (not broken or x < w * 0.55)) or (4 <= y < 10 and x in (1, 2, w - 3, w - 2)) or (6 <= y < 8 and 1 <= x < w - 1),
           lambda x, y: 6 if y == 0 else 4 if y < 4 else 2)
    if broken:
        for i in range(4): s.put(w * 0.55 + i, 3 - i % 2, WOOD[3])
    return s.outline(outline_of(WOOD))


def kelp(j):
    s = Spr(4, 6 + j % 4 * 2)
    for k in range(s.h): s.put(1 + int(math.sin(k * 0.9 + j) * 1.2), k, MOSS[3 if k % 3 else 5])
    return s


@biome(name="Drowned Nave", tag="A cathedral the sea took back",
       palette=[STONE_G[4], BRINE[4], BRINE[6], GLASS[0][2], GLASS[1][2], WOOD[4]],
       look="Grey-green nave stone and dim stained glass, pews swept into heaps, kelp hanging from the cornices. Brine "
            "stands in the low side of every room and the windows lay coloured light across the floor.",
       hazard="The tide floods across the room and drains back on a slow cycle. Standing in it slows the hero, and Bel'Mora's "
              "monsters heal in it. In the font room the water is the floor and the stone ring is the only dry ground.",
       props="Pews to smash through, fallen columns, bell frames, candle stands, reliquaries that hold gold, kelp.",
       fits="Bel'Mora, the Drowned Bell, big swimmers.")
def drowned_nave():
    rooms = []

    # 1. The flooded nave: long, tide on the left, a mosaic aisle down the middle
    R = Room(236, 96, 11)
    tide = lambda u, v: u < 62 + 16 * math.sin(v * 0.09) + 5 * math.sin(v * 0.33)
    def nave_overlay(u, v):
        edge = 62 + 16 * math.sin(v * 0.09) + 5 * math.sin(v * 0.33)
        x, y = R.at(u, v)
        if u < edge:
            t = 3 + (R.n.value(x * 2, y * 5, 7) - 0.5) * 3 + (1.5 if (y + x // 4) % 11 == 0 else 0)
            if edge - u < 1.5: t = 7
            elif edge - u < 3: t = 5
            return BRINE[int(clamp(round(t), 0, 7))]
        # the aisle: a strip of small diamond mosaic down the middle
        if 140 <= u < 156:
            a = (u - 140) % 6; b = v % 6
            if abs(a - 3) + abs(b - 3) == 3: return STONE_G[2]
            if abs(a - 3) + abs(b - 3) <= 1: return GLASS[(v // 6) % 3][1]
        return None
    def nave_pat(u, v):
        p = flags(13, 8, seed=4)(u, v)
        edge = 62 + 16 * math.sin(v * 0.09) + 5 * math.sin(v * 0.33)
        if u - edge < 5: p -= 0.8          # wet stone at the tide line
        return p
    R.floor(STONE_G, nave_pat, overlay=nave_overlay, mid=0.62, spread=0.9)
    R.wall(face_bricks(10, 5, 3.0, 7), STONE_G, [pillars(34, STONE_G), slits(34, STONE_G, glass=GLASS, h=14, w=5, top=6),
                                                hang(23, kelp, k=1)])
    for (u, v, w, b) in [(108, 30, 28, False), (180, 30, 28, True), (108, 56, 28, True), (180, 56, 28, False), (108, 82, 28, False), (182, 84, 24, True)]:
        R.stamp(pew(w, b), u, v)
    col = Spr(36, 12)
    col.fill(STONE_G, lambda x, y: 2 <= y < 10 and 1 <= x < 34, lambda x, y: 6 - (y - 2) * 0.5 + (0.6 if x % 7 == 0 else 0))
    col.fill(STONE_G, ell(33, 6, 3, 5), lambda x, y: 3)
    col.outline(outline_of(STONE_G)); R.stamp(col, 74, 70)
    R.scatter(debris(STONE_G), 22)
    R.scatter(lambda r: pile(STONE_G, 4, 9, 5, r.randint(0, 99), 1.6), 5, shadow=0.3)
    for (u, v) in [(92, 14), (226, 14), (226, 88)]:
        R.stamp(candles(PAPER, BRASS), u, v); R.light(u, v - 15, 24, (255, 200, 120), 0.7)
    for j, u in enumerate(range(45, 236, 34)):
        R.light(u + 2, 22, 30, GLASS[j % 3][2], 0.45)
    cast(R, "BelDrownedBell", 40, 64, 160, 70)
    rooms.append(("The Flooded Nave", "A long nave, half under the tide, pews in rows and a glass-mosaic aisle down the middle.", R.finish()))

    # 2. The font: a round pool with a ring of stone round it, four pillars
    R = Room(200, 112, 12)
    cx, cy = 100, 58
    def font_overlay(u, v):
        d = math.hypot((u - cx) / 1.0, (v - cy) * 1.55)
        x, y = R.at(u, v)
        if d < 34:
            t = 2.5 + (R.n.value(x * 2, y * 4, 6) - 0.5) * 2.5 + (2 if int(d) % 9 == 0 else 0)
            return BRINE[int(clamp(round(t), 0, 7))]
        if d < 36: return BRINE[7] if (u + v) % 3 else BRINE[6]
        if d < 46:
            a = math.atan2((v - cy) * 1.55, u - cx)
            seg = int((a + math.pi) / (math.pi / 10))
            if int(d) in (36, 45) or abs(((a + math.pi) % (math.pi / 10)) - 0.01) < 0.03: return STONE_G[2]
            return STONE_G[5] if seg % 2 else GLASS[seg // 2 % 3][1]
        if d < 48: return STONE_G[2]
        return None
    R.floor(STONE_G, flags(12, 8, seed=9), overlay=font_overlay, inside=cut_corners(200, 112, 16), mid=0.6, spread=0.9)
    R.wall(face_bricks(10, 5, 3.0, 8), STONE_G, [pillars(40, STONE_G), slits(40, STONE_G, glass=GLASS, h=14, w=5, top=6)])
    for (u, v) in [(46, 30), (154, 30), (46, 100), (154, 100)]:
        R.stamp(pillar_prop(STONE_G, 30), u, v)
        R.stamp(candles(PAPER, BRASS, 2), u + 9, v + 2, shadow=0.3); R.light(u + 9, v - 12, 22, (255, 200, 120), 0.6)
    R.scatter(debris(STONE_G), 16)
    R.light(cx, cy, 60, (120, 200, 190), 0.35)
    cast(R, "BelKraken", cx, cy + 8, 160, 76)
    rooms.append(("The Font", "A round room built round a sunken font: the water is most of the floor, a mosaic ring the dry ground.", R.finish()))

    # 3. The bell chapel: small, the floor broken through to water, a bell frame and organ pipes on the wall
    R = Room(170, 92, 13)
    def chapel_overlay(u, v):
        x, y = R.at(u, v)
        hole = ((u - 112) / 26.0) ** 2 + ((v - 54) / 15.0) ** 2 + 0.25 * math.sin(u * 0.7) * math.sin(v * 0.9)
        if hole < 1:
            return BRINE[int(clamp(round(2 + (R.n.value(x * 2, y * 4, 5) - 0.5) * 3), 0, 7))]
        if hole < 1.25: return STONE_G[1] if (u + v) % 2 else STONE_G[2]
        if 20 <= u < 70 and 30 <= v < 70:     # a red runner carpet to the altar
            if u in (20, 69) or v in (30, 69): return RUG_R[5]
            return RUG_R[3] if ((u // 3 + v // 3) % 4) else RUG_R[2]
        return None
    R.floor(STONE_G, flags(12, 8, seed=13), overlay=chapel_overlay, inside=cut_corners(170, 92, 10, alcoves=[(60, -8, 110, 0)]), mid=0.6, spread=0.9)
    def organ(R):
        us = sorted(R.top_of)
        mid = (us[0] + us[-1]) // 2
        for i in range(-7, 8):
            ph = 22 - abs(i) * 2
            for k in range(R.wh - 2 - ph, R.wh - 3):
                x, y = R.wx(mid + i * 3, k)
                for j in range(2): R.cv.put(x + j, y, BRASS[5 - j * 2] if k > R.wh - 2 - ph + 1 else BRASS[6])
    R.wall(face_bricks(10, 5, 3.0, 9), STONE_G, [pillars(42, STONE_G, arch=False), organ])
    frame = Spr(30, 30)
    frame.fill(WOOD, lambda x, y: (x in (2, 3, 26, 27) and y >= 4) or (y in (3, 4) and 1 <= x < 29), lambda x, y: 5 if y == 3 else 3)
    frame.fill(BRASS, lambda x, y: 8 <= y < 24 and abs(x - 14.5) <= 3 + (y - 8) * 0.45, roundlit(13, 14, 8, 10, len(BRASS)))
    frame.fill(BRASS, box(13, 24, 17, 26), lambda x, y: 3)
    frame.outline(outline_of(WOOD)); R.stamp(frame, 46, 24)
    R.stamp(chest(WOOD, BRASS), 140, 22)
    R.scatter(debris(STONE_G), 14); R.scatter(lambda r: pile(STONE_G, 4, 9, 5, r.randint(0, 99), 1.6), 3, area=(84, 34, 150, 76), shadow=0.3)
    R.stamp(candles(PAPER, BRASS), 16, 26); R.light(16, 12, 26, (255, 200, 120), 0.7)
    R.light(112, 54, 34, (110, 190, 180), 0.35)
    cast(R, "BelSlimeHag", 112, 62, 44, 60)
    rooms.append(("The Bell Chapel", "A small chapel whose floor has given way to the sea, with a bell frame, organ pipes and a red runner to the altar.", R.finish()))
    return rooms


# ======== Bone Orchard
def bone_tree(s=1.0, lanterns=3, seed=0):
    sp = Spr(44 * s, 50 * s)
    cx = sp.w / 2
    rnd = random.Random(seed)
    def limb(x0, y0, x1, y1, w):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.4) + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t + math.sin(t * 6 + seed) * 0.6, y0 + (y1 - y0) * t
            ww = max(0.5, w * (1 - 0.65 * t))
            for d in range(-int(ww), int(ww) + 1):
                sp.put(x + d, y, BONE[6 if d < 0 else 4 if d == 0 else 2])
            if i % 5 == 2 and w > 1:      # knuckle
                sp.put(x - ww - 1, y, BONE[5]); sp.put(x + ww + 1, y, BONE[3])
    limb(cx, sp.h - 1, cx, sp.h * 0.42, 2.4 * s)
    tips = []
    for (dx, dy, w) in [(-15, -44, 1.4), (13, -46, 1.4), (-5, -48, 1.2), (17, -32, 1.1), (-18, -28, 1.1), (6, -38, 1.0)]:
        x1, y1 = cx + dx * s, sp.h + dy * s
        limb(cx, sp.h * 0.55, x1, y1, w * s); tips.append((x1, y1))
    # root flare and a skull at the foot
    for d in range(-5, 6):
        sp.put(cx + d, sp.h - 1, BONE[4 if d < 0 else 2])
    sp.fill(BONE, ell(cx + 4, sp.h - 4, 2.6, 2.2), roundlit(cx + 4, sp.h - 4, 2.6, 2.2, len(BONE)))
    sp.put(cx + 3, sp.h - 4, BONE[0]); sp.put(cx + 5, sp.h - 4, BONE[0])
    lights = []
    for (x, y) in [(int(a), int(b)) for (a, b) in rnd.sample(tips, min(lanterns, len(tips)))]:
        for k in range(3): sp.put(x, y + k, EARTH[1])
        for yy in range(y + 3, y + 7):
            for xx in (x - 1, x, x + 1): sp.put(xx, yy, LANTERN[3 if xx == x and yy in (y + 4, y + 5) else 1])
        lights.append((x, y + 5))
    sp.outline(outline_of(BONE))
    return sp, lights


def bone_bit(r):
    """A loose bone, rib or skull lying on the floor."""
    k = r.randint(0, 3)
    if k == 3:
        s = Spr(6, 5)
        s.fill(BONE, ell(3, 2.5, 2.6, 2.2), roundlit(3, 2.3, 2.6, 2.2, len(BONE)))
        s.put(2, 2, BONE[0]); s.put(4, 2, BONE[0])
    else:
        n = r.randint(4, 7)
        s = Spr(n + 2, 3)
        for i in range(n): s.put(i + 1, 1, BONE[5 if i % 2 else 4])
        for e in (0, n + 1): s.put(e, 0, BONE[5]); s.put(e, 2, BONE[3])
        if r.random() < 0.5: s.mirror()
    return s.outline(outline_of(BONE))


def grave():
    s = Spr(16, 12)
    s.fill(EARTH, ell(8, 8, 7.5, 3.6), roundlit(8, 8, 7.5, 3.6, len(EARTH)))
    s.fill(BONE, box(10, 0, 13, 7), lambda x, y: 5 if x == 10 else 3)
    s.fill(BONE, box(9, 2, 14, 3), lambda x, y: 5)
    return s.outline(outline_of(EARTH))


def skull_lamp():
    s = Spr(8, 22)
    s.fill(EARTH, lambda x, y: x in (3, 4) and y >= 6, lambda x, y: 4 if x == 3 else 2)
    s.fill(BONE, ell(4, 3.5, 3.4, 3.2), roundlit(4, 3.5, 3.4, 3.2, len(BONE)))
    s.put(3, 3, LANTERN[3]); s.put(5, 3, LANTERN[3]); s.put(4, 5, LANTERN[2])
    return s.outline(outline_of(BONE))


@biome(name="Bone Orchard", tag="A grove grown from the dead",
       palette=[ASH[4], BONE[5], BONE[2], LANTERN[2], EARTH[3]],
       look="Ash-grey soil veined with pale roots, trees of fused bone hung with lanterns, ribs and skulls set in the earth "
            "bank of the back wall. Outside the lantern light the rooms fall dark.",
       hazard="The rooms are dark outside the lantern pools. A tree hit hard drops its lanterns and the room goes darker. "
              "Grave mounds cough up a minion when walked over, and bone piles mean Ossivar's monsters start every fight armed.",
       props="Bone trees (solid, break into piles), grave mounds, skull lamps, a bone fence along the gate, the shrine's ring of stones.",
       fits="Ossivar, the Carrion Saint, anything that eats bones.")
def bone_orchard():
    rooms = []

    def soil_pat(R, roots_n=10):
        pts = set()
        rr = random.Random(R.r.random())
        for _ in range(roots_n):
            x, y = rr.uniform(0, R.w), rr.uniform(0, R.h)
            for i in range(44):
                pts.add((int(x), int(y))); x += rr.choice((-1, 1, 1, 0)); y += rr.choice((0, 0, 1, -1))
        return lambda u, v: 2.2 if (u, v) in pts else -1.2 if (u, v - 1) in pts else 0

    def bank(R):
        us = sorted(R.top_of)
        for u in range(us[0] + 5, us[-1] - 5, 14):
            for k in range(4, R.wh - 4):
                uu = u + int(4.5 * math.sin((k - 4) / (R.wh - 8) * math.pi))
                x, y = R.wx(uu, k); R.cv.put(x, y, BONE[5]); R.cv.put(x + 1, y, BONE[3]); R.cv.put(x + 2, y, BONE[1])
        for j, u in enumerate(range(us[0] + 18, us[-1] - 10, 42)):
            sk = Spr(9, 8)
            sk.fill(BONE, ell(4.5, 3.5, 4.2, 3.6), roundlit(4, 3, 4, 4, len(BONE)))
            for p in ((3, 4), (6, 4)): sk.put(*p, BONE[0])
            sk.put(4, 6, BONE[1]); sk.put(5, 6, BONE[1]); sk.outline(outline_of(BONE))
            x, y = R.wx(u, 10); R.cv.im.alpha_composite(sk.im, (x, y)); R.cv.px = R.cv.im.load()

    # 1. The grove
    R = Room(210, 100, 21)
    R.floor(ASH, soil_pat(R), inside=cut_corners(210, 100, 14), mid=0.55, spread=1.1)
    R.wall(face_rough(2.6, 1), EARTH, [bank])
    for (u, v, s, seed) in [(48, 52, 1.0, 1), (170, 46, 1.1, 2), (110, 96, 0.9, 3)]:
        t, ls = bone_tree(s, 3, seed)
        R.stamp(t, u, v)
        for (lx, ly) in ls: R.light(u - t.w / 2 + lx, v - t.h + ly, 30, (255, 185, 95), 0.75)
    R.stamp(grave(), 150, 86); R.stamp(grave(), 30, 88)
    R.scatter(lambda r: pile(BONE, 6, 13, 6, r.randint(0, 99), 2.2), 5, shadow=0.3)
    R.scatter(debris(BONE), 26)
    R.scatter(bone_bit, 14, shadow=0.2)
    cast(R, "OssTombwright", 120, 52, 80, 70)
    rooms.append(("The Grove", "Bone trees as pillars to fight round, lanterns in their branches, graves between them.", R.finish(0.66)))

    # 2. The ossuary gate: a corridor between two bone fences, skull lamps
    R = Room(240, 54, 22)
    R.floor(ASH, flags(16, 9, seed=3), mid=0.55, spread=1.0)
    R.wall(face_rough(2.4, 2), EARTH, [bank, pillars(48, BONE, width=4)])
    fence = Spr(12, 12)
    fence.fill(BONE, lambda x, y: (x % 4 == 1 and y >= 1) or y in (4, 9), lambda x, y: 5 if x % 4 == 1 else 3)
    fence.outline(outline_of(BONE))
    for u in range(4, 236, 12):
        if 100 <= u < 140: continue
        R.stamp(fence, u + 6, 14, shadow=0.2); R.stamp(fence, u + 6, 52, shadow=0.2)
    for u in (96, 144):
        R.stamp(skull_lamp(), u, 30); R.light(u, 12, 32, (255, 170, 80), 0.75)
    R.scatter(debris(BONE), 16, area=(4, 16, 236, 46))
    R.scatter(bone_bit, 6, area=(4, 18, 236, 44), shadow=0.2)
    cast(R, "OssCoffinBearer", 190, 42, 56, 38, flip=True)
    rooms.append(("The Ossuary Gate", "A corridor between bone fences, skull lamps at its gate, the way into the deep grove.", R.finish(0.62)))

    # 3. The root shrine: one huge bone tree in a ring of standing stones
    R = Room(180, 112, 23)
    ccx, ccy = 90, 66
    def shrine_overlay(u, v):
        d = math.hypot(u - ccx, (v - ccy) * 1.6)
        if 30 <= d < 32: return ASH[6]
        if 32 <= d < 34: return ASH[2]
        if d < 30 and int(d) % 7 == 0 and (u + v) % 3: return ASH[5]
        return None
    R.floor(ASH, soil_pat(R, 14), overlay=shrine_overlay, inside=cut_corners(180, 112, 18), mid=0.5, spread=1.1)
    R.wall(face_rough(2.5, 3), EARTH, [bank])
    for i in range(8):
        a = i / 8 * math.tau
        u, v = ccx + 40 * math.cos(a), ccy + 26 * math.sin(a)
        st = Spr(7, 12)
        st.fill(ASH, lambda x, y: y >= 1 and 1 <= x < 6, lambda x, y: 6 if y < 2 else 5 - x * 0.6)
        st.outline(outline_of(ASH)); R.stamp(st, u, v)
    big, ls = bone_tree(1.6, 5, 9)
    R.stamp(big, ccx, ccy + 8)
    for (lx, ly) in ls: R.light(ccx - big.w / 2 + lx, ccy + 8 - big.h + ly, 34, (255, 185, 95), 0.8)
    R.scatter(debris(BONE), 20)
    R.scatter(bone_bit, 10, shadow=0.2)
    cast(R, "OssOssuary", 40, 96, 140, 92)
    rooms.append(("The Root Shrine", "One great bone tree in a ring of standing stones, the orchard's heart and its brightest room.", R.finish(0.62)))
    return rooms


# ======== Ember Works
def anvil():
    s = Spr(16, 10)
    s.fill(IRON, lambda x, y: (y < 3 and not (y == 0 and x > 12)) or (3 <= y < 7 and 5 <= x < 11) or (7 <= y < 10 and 3 <= x < 13),
           lambda x, y: 7 if y == 0 else 5 if y < 3 else 3)
    return s.outline(outline_of(IRON))


def crucible():
    s = Spr(16, 24)
    for y in range(0, 11):
        s.put(7, y, IRON[5]); s.put(8, y, IRON[3])
    s.fill(IRON, ell(8, 17, 7, 6.5), roundlit(7, 15, 7, 6.5, len(IRON)))
    s.fill(MOLTEN, ell(8, 12.5, 5, 1.6), lambda x, y: 5)
    return s.outline(outline_of(IRON))


def cart():
    s = Spr(18, 13)
    s.fill(WOOD, box(1, 2, 17, 9), boxlit(1, 2, 17, 9, len(WOOD)))
    s.fill(COAL, lambda x, y: y < 3 and 2 <= x < 16 and (y > 0 or x % 3), lambda x, y: (x * 5 + y * 3) % 6)
    s.fill(IRON, lambda x, y: y >= 9 and (abs(x - 4.5) <= 2 or abs(x - 13.5) <= 2), lambda x, y: 4)
    return s.outline(outline_of(WOOD))


def gear(r=9):
    s = Spr(r * 2 + 3, r * 2 + 3)
    c = r + 1
    def inside(x, y):
        d = math.hypot(x - c, y - c); a = math.atan2(y - c, x - c)
        return (d <= r - 2) or (d <= r and math.cos(a * 8) > 0.3)
    s.fill(IRON, lambda x, y: inside(x, y) and math.hypot(x - c, y - c) > 2, roundlit(c, c, r, r, len(IRON)))
    return s.outline(outline_of(IRON))


def bellows():
    s = Spr(32, 20)
    leather = ramp(hx("#6a4530"))
    top = lambda x: 2 + x * 0.32                      # the upper board slopes down to the nozzle
    s.fill(leather, lambda x, y: 1 <= x < 24 and top(x) + 2 <= y < 15, lambda x, y: (5 if x % 4 == 0 else 3 if x % 4 in (1, 3) else 1.5) - y * 0.05)
    s.fill(WOOD, lambda x, y: 0 <= x < 26 and top(x) <= y < top(x) + 2.2, lambda x, y: 6 if y < top(x) + 1 else 4)
    s.fill(WOOD, box(0, 15, 28, 18), boxlit(0, 15, 28, 18, len(WOOD), top=1))
    s.fill(IRON, lambda x, y: 24 <= x < 32 and 11 <= y < 15 - (x - 24) * 0.25, lambda x, y: 6 if y == 11 else 3)
    s.fill(WOOD, box(0, 0, 3, 3), lambda x, y: 5)       # handle
    for x in (5, 13, 21): s.put(x, 16, BRASS[6])
    return s.outline(outline_of(WOOD))


@biome(name="Ember Works", tag="The foundry below the mines",
       palette=[IRON[4], BRICK[4], MOLTEN[3], MOLTEN[1], COAL[3]],
       look="Soot-black riveted iron plate split by channels of molten metal, furnace mouths glowing along a brick back "
            "wall, gears and bellows the size of a room. Most of the light is the metal itself.",
       hazard="The pour: every few seconds a pulse of heat runs down the channels (a bright tell first), burning anything "
              "on a grate. Crucibles hang on chains and tip when hit. In the slag pit the bridges are the only floor.",
       props="Anvils for cover, coal carts that roll when struck, crucibles, bellows, gears, slag heaps.",
       fits="Vhorrul's fire monsters, anything heavy and armoured.")
def ember_works():
    rooms = []

    def furnaces(every, start=12):
        def draw(R):
            us = sorted(R.top_of)
            for u in range(us[0] + start, us[-1] - 30, every):
                for k in range(3, R.wh - 1):
                    for i in range(28):
                        x, y = R.wx(u + i, k)
                        R.cv.put(x, y, IRON[5 if k == 3 else 4 - (1 if i > 22 else 0) - (1 if i < 2 else 0)])
                mx = u + 14
                for k in range(12, R.wh - 2):
                    half = 8 if k > 15 else 8 - (15 - k) * 2
                    for i in range(-half, half + 1):
                        x, y = R.wx(mx + i, k)
                        t = 5 - abs(i) * 0.45 - (R.wh - 2 - k) * 0.18
                        R.cv.put(x, y, MOLTEN[int(clamp(round(t), 0, 6))])
                for i in range(-9, 10):
                    x, y = R.wx(mx + i, 11 if abs(i) < 6 else 12 + abs(i) - 6); R.cv.put(x, y, IRON[6])
                for k in range(-8, 3):
                    for i in range(21, 26):
                        x, y = R.wx(u + i, k); R.cv.put(x, y, IRON[6 - (i - 21)])
                R.light(mx - R.ox + R.ox, 2, 40, (255, 140, 50), 0.9)
        return draw

    def channel_overlay(R, hs, vs, width=2):
        def f(u, v):
            x, y = R.at(u, v)
            for cy in hs:
                if abs(v - cy) <= width:
                    if u % 8 == 0: return IRON[1]
                    t = 5.5 - abs(v - cy) * 1.4 + math.sin(u * 0.5 + v) * 0.7
                    return MOLTEN[int(clamp(round(t), 0, 6))]
            for cx in vs:
                if abs(u - cx) <= width:
                    if v % 8 == 0: return IRON[1]
                    t = 5.5 - abs(u - cx) * 1.4 + math.sin(v * 0.5 + u) * 0.7
                    return MOLTEN[int(clamp(round(t), 0, 6))]
            for cy in hs:
                if abs(v - cy) == width + 1: return IRON[1]
            for cx in vs:
                if abs(u - cx) == width + 1: return IRON[1]
            return None
        return f

    # 1. The casting hall
    R = Room(240, 96, 31)
    hs, vs = (30, 70), (70, 160)
    R.floor(IRON, plates(22, 14), overlay=channel_overlay(R, hs, vs), mid=0.45, spread=0.9, centre=0.5)
    R.wall(face_bricks(8, 4, 3.0, 11), BRICK, [furnaces(54)])
    for cy in hs:
        for u in range(0, 240, 8): R.light(u, cy, 11, (255, 120, 40), 0.35)
    for cx in vs:
        for v in range(0, 96, 8): R.light(cx, v, 11, (255, 120, 40), 0.35)
    R.stamp(anvil(), 110, 52); R.stamp(anvil(), 200, 92); R.stamp(cart(), 30, 92); R.stamp(cart(), 220, 50)
    R.stamp(crucible(), 120, 92, shadow=0); R.light(120, 80, 18, (255, 150, 60), 0.6)
    R.scatter(lambda r: pile(COAL, 5, 10, 5, r.randint(0, 99), 1.8), 6, shadow=0.3)
    R.scatter(debris(COAL), 22)
    cast(R, "VhPyreWarden", 196, 50, 40, 52)
    rooms.append(("The Casting Hall", "Iron plate cut into islands by channels of molten metal, furnaces along the back wall.", R.finish(0.7)))

    # 2. The bellows room: great bellows feeding a central furnace column, gears on the wall
    R = Room(176, 96, 32)
    def bellows_overlay(u, v):
        d = math.hypot(u - 88, (v - 52) * 1.5)
        if d < 14: return MOLTEN[int(clamp(round(6 - d * 0.35 + math.sin(u + v) * 0.6), 0, 6))]
        if d < 17: return IRON[6] if d < 15 else IRON[1]
        return None
    R.floor(IRON, plates(18, 12, seed=7), overlay=bellows_overlay, inside=cut_corners(176, 96, 12), mid=0.45, spread=0.9, centre=0.5)
    def gears_on(R):
        us = sorted(R.top_of)
        for j, u in enumerate(range(us[0] + 16, us[-1] - 10, 36)):
            g = gear(8 + (j % 2) * 3)
            x, y = R.wx(u, 4 + (j % 2) * 2); R.cv.im.alpha_composite(g.im, (int(x - g.w / 2), y)); R.cv.px = R.cv.im.load()
    R.wall(face_bricks(8, 4, 3.0, 12), BRICK, [gears_on])
    R.light(88, 52, 50, (255, 140, 50), 0.9)
    for (u, v, f) in [(48, 56, False), (128, 56, True)]:
        b = bellows(); b = b.mirror() if f else b
        R.stamp(b, u, v)
    R.stamp(anvil(), 40, 88); R.stamp(cart(), 150, 90)
    R.scatter(debris(COAL), 18)
    cast(R, "VhRenderer", 88, 92, 150, 40)
    rooms.append(("The Bellows Room", "Two great bellows feeding a pool of molten metal in the floor, gears turning on the wall.", R.finish(0.68)))

    # 3. The slag pit: most of the room is a molten pool, crossed by iron bridges
    R = Room(210, 108, 33)
    def pit_overlay(u, v):
        x, y = R.at(u, v)
        wob = int(3 * R.n.value(x, y, 5))
        on_bridge = (50 <= v < 62) or (96 <= u < 112) or (v >= 92 - wob) or (v < 10 + wob) or u < 4 + wob or u >= 206 - wob
        if on_bridge:
            if v in (50, 61) and not (96 <= u < 112): return IRON[1]
            if u in (96, 111) and not (50 <= v < 62) and 10 <= v < 92: return IRON[1]
            return None
        crust = 0.7 * R.n.value(x, y, 11) + 0.3 * R.n.value(x, y, 4)
        if crust > 0.6:
            return COAL[int(clamp(round(1.2 + (crust - 0.6) * 9 + (R.n.cluster(x, y) - 0.5) * 1.5), 0, 4))]
        if crust > 0.56: return MOLTEN[5]
        t = 2.6 + (R.n.value(x, y, 7) - 0.5) * 2.4 + (crust - 0.3) * 3
        return MOLTEN[int(clamp(round(t), 1, 6))]
    R.floor(IRON, plates(16, 12, seed=8), overlay=pit_overlay, mid=0.45, spread=0.9, centre=0.4)
    R.wall(face_bricks(8, 4, 3.0, 13), BRICK, [furnaces(70, 30)])
    for u in range(0, 210, 14):
        for v in range(10, 92, 14):
            if not (50 <= v < 62 or 96 <= u < 112): R.light(u, v, 18, (255, 120, 40), 0.4)
    R.stamp(crucible(), 60, 52, shadow=0); R.stamp(crucible(), 150, 52, shadow=0)
    R.scatter(debris(COAL), 14, area=(2, 92, 208, 106))
    cast(R, "VhAshSeraph", 104, 58, 40, 104)
    rooms.append(("The Slag Pit", "A room of molten slag with an iron cross of bridges over it. The bridges are the floor.", R.finish(0.66)))
    return rooms


# ======== Rot Gardens
def cap(s, pal, seed=0):
    sp = Spr(24 * s + 2, 28 * s + 2)
    cx = sp.w / 2
    sp.fill(STEM, lambda x, y: abs(x + 0.5 - cx) <= 2.3 * s and y >= sp.h * 0.35, lambda x, y: 5 - (x - cx + 2) * 0.9)
    sp.fill(pal, ell(cx, sp.h * 0.33, 11 * s, 6.2 * s), roundlit(cx - 2, sp.h * 0.3, 11 * s, 6.2 * s, len(pal)))
    rnd = random.Random(seed)
    for _ in range(int(6 * s)):
        dx, dy = rnd.uniform(-8, 8) * s, rnd.uniform(-4, 1) * s
        sp.put(cx + dx, sp.h * 0.33 + dy, pal[-1])
    for x in range(int(cx - 10 * s), int(cx + 10 * s)):
        if x % 2: sp.put(x, sp.h * 0.33 + 5.5 * s, pal[0])
    return sp.outline(outline_of(pal))


def puffball(r=4):
    s = Spr(r * 2 + 2, r * 2 + 1)
    s.fill(STEM, ell(r + 1, r, r, r * 0.85), roundlit(r + 1, r, r, r * 0.85, len(STEM)))
    return s.outline(outline_of(STEM))


@biome(name="Rot Gardens", tag="Caves gone soft with fungus",
       palette=[SOIL[4], CAP_T[3], CAP_G[3], STEM[5], CAVE[2]],
       look="Spongy plum-brown floor patched with moss and threads of mycelium, shelf fungus up the cave walls, giant caps "
            "glowing teal and acid green. The caps are the rooms' lights, so a room's colour tells you what grows there.",
       hazard="Spore drifts hang in the air and slowly move. Walking through dazes the hero briefly. A cap that is hit bursts "
              "into a fresh cloud, so a careless swing can blind your own escape.",
       props="Caps (light and burst), puffballs that roll, mycelium mats that slow everything on them, fallen logs.",
       fits="Spore and slime monsters, and the Tallow Grub's kin.")
def rot_gardens():
    rooms = []

    def moss_overlay(R, thresh=0.66):
        def f(u, v):
            x, y = R.at(u, v)
            m = R.n.value(x, y, 9)
            if m > thresh:
                return MOSS[int(clamp(round(2 + (m - thresh) * 12 + (R.n.cluster(x, y) - 0.5) * 2), 1, 5))]
            if R.n.value(x, y, 2.5) > 0.9 and R.n.value(x, y, 13) > 0.6: return STEM[4]
            return None
        return f

    def cave_wall(R):
        us = sorted(R.top_of)
        rnd = random.Random(7)
        for u in range(us[0] + 2, us[-1] - 2, 6):
            for k in range(rnd.randint(3, 14)):
                x, y = R.wx(u + int(math.sin(k * 0.7 + u) * 1.2), 2 + k); R.cv.put(x, y, SOIL[5 if k % 3 else 4])
        for u in range(us[0] + 4, us[-1] - 14, 18):
            for j in range(rnd.randint(1, 3)):
                sh = Spr(12 - j * 2, 4)
                sh.fill(STEM, ell(sh.w / 2, 1.6, sh.w / 2, 2.2), lambda x, y: 6 - y * 1.4)
                sh.outline(outline_of(STEM))
                x, y = R.wx(u + rnd.randint(0, 8), 6 + rnd.randint(0, 14))
                R.cv.im.alpha_composite(sh.im, (x, y)); R.cv.px = R.cv.im.load()

    # 1. The cap cavern
    R = Room(206, 100, 41)
    R.floor(SOIL, plain(), overlay=moss_overlay(R), inside=cut_corners(206, 100, 18, alcoves=[(-10, 30, 0, 70)]), mid=0.5, spread=1.1)
    R.wall(face_rough(2.4, 4), CAVE, [cave_wall])
    for (u, v, s, pal) in [(40, 46, 1.3, CAP_T), (176, 52, 1.5, CAP_T), (100, 96, 0.9, CAP_G), (150, 96, 0.7, CAP_T), (80, 30, 0.6, CAP_G)]:
        c = cap(s, pal, int(u)); R.stamp(c, u, v); R.light(u, v - c.h * 0.65, 34 * s, pal[3], 0.85)
    R.scatter(lambda r: puffball(r.randint(2, 4)), 6, shadow=0.35)
    R.scatter(debris(SOIL), 18)
    for _ in range(80):
        u, v = int(R.r.gauss(120, 24)), int(R.r.gauss(56, 12))
        if R.on(u, v):
            x, y = R.at(u, v); R.cv.put(x, y, mix(R.cv.get(x, y)[:3], (210, 240, 170), 0.5))
    cast(R, "TallowColossus", 70, 78, 136, 70)
    rooms.append(("The Cap Cavern", "A round cavern lit by giant caps, moss underfoot and a spore drift across the middle.", R.finish(0.64)))

    # 2. The mycelium tunnel: a low bending tunnel with a slowing mat
    R = Room(240, 60, 42)
    def tunnel(u, v):
        top = 6 + 8 * math.sin(u / 240 * math.pi * 2)
        return top <= v < top + 44
    def mat(u, v):
        x, y = R.at(u, v)
        if 90 <= u < 170:
            edge = min(u - 90, 170 - u) / 12.0
            w = R.n.value(x, y, 9) + 0.25 * min(1.0, edge) - 0.2
            if w > 0.35:
                thread = abs(R.n.value(x, y, 6) - 0.5) < 0.035 or abs(R.n.value(x + 50, y, 4) - 0.5) < 0.03
                return STEM[6] if thread else STEM[int(clamp(round(3 + (R.n.cluster(x, y) - 0.5) * 2 + (w - 0.35) * 3), 2, 5))]
        return moss_overlay(R, 0.72)(u, v)
    R.floor(SOIL, plain(), overlay=mat, inside=tunnel, mid=0.45, spread=1.0)
    R.wall(face_rough(2.2, 5), CAVE, [cave_wall])
    log = Spr(40, 12)
    log.fill(WOOD, lambda x, y: 2 <= y < 11 and 1 <= x < 39, lambda x, y: 5 - (y - 2) * 0.5 + (0.8 if (x + y) % 7 == 0 else 0))
    log.fill(WOOD, ell(38, 6.5, 2.5, 4.5), lambda x, y: 3 if (x + y) % 2 else 5)
    log.outline(outline_of(WOOD)); R.stamp(log, 60, 40)
    for (u, v, s, pal) in [(200, 30, 0.8, CAP_G), (24, 34, 0.7, CAP_T)]:
        c = cap(s, pal); R.stamp(c, u, v); R.light(u, v - c.h * 0.65, 30, pal[3], 0.85)
    R.scatter(debris(SOIL), 14)
    cast(R, "SylCarrionLily", 130, 46, 210, 50)
    rooms.append(("The Mycelium Tunnel", "A low winding tunnel with a mat of mycelium across the middle that slows everything on it.", R.finish(0.6)))

    # 3. The hollow trunk: inside a dead giant mushroom stem, growth rings on the floor
    R = Room(176, 112, 43)
    ccx, ccy = 88, 60
    def rings(u, v):
        d = math.hypot(u - ccx, (v - ccy) * 1.5)
        if d > 82: return None
        if int(d) % 9 == 0: return STEM[2]
        return STEM[int(clamp(round(3.5 + (R.n.cluster(*R.at(u, v)) - 0.5) * 2 + (1 if int(d / 9) % 2 else 0)), 2, 6))]
    R.floor(SOIL, plain(), overlay=rings, inside=lambda u, v: math.hypot(u - ccx, (v - ccy) * 1.5) < 86, mid=0.45, spread=1.0)
    R.wall(face_rough(3.0, 6), STEM, [cave_wall])
    for i in range(6):
        a = i / 6 * math.tau + 0.3
        u, v = ccx + 64 * math.cos(a), ccy + 40 * math.sin(a)
        if R.on(int(u), int(v)):
            c = cap(0.6, CAP_T if i % 2 else CAP_G, i); R.stamp(c, u, v); R.light(u, v - 10, 26, (CAP_T if i % 2 else CAP_G)[3], 0.8)
    R.scatter(lambda r: puffball(r.randint(2, 3)), 5, shadow=0.35)
    cast(R, "SylBriarChampion", ccx, ccy + 10, 128, 96)
    rooms.append(("The Hollow Trunk", "A fight inside the stem of a dead giant mushroom, its growth rings on the floor, caps round the edge.", R.finish(0.62)))
    return rooms


# ======== Ledger Vaults
def bookcase(w, h, seed=0):
    s = Spr(w, h)
    s.fill(SHELF, lambda x, y: True, lambda x, y: (6 if y == 0 else 2 if x in (0, w - 1) else 3))
    rnd = random.Random(seed)
    for sy in range(3, h - 2, 6):
        x = 2
        while x < w - 2:
            bw, bh, pal = rnd.randint(1, 2), rnd.randint(3, 5), rnd.choice(BOOKS)
            for xx in range(x, min(w - 2, x + bw)):
                for yy in range(sy + 5 - bh, sy + 5):
                    s.put(xx, yy, pal[2] if yy == sy + 5 - bh else pal[1] if xx == x else pal[0])
            x += bw + (1 if rnd.random() < 0.15 else 0)
        for xx in range(1, w - 1): s.put(xx, sy + 5, SHELF[5])
    return s.outline(outline_of(SHELF))


def desk():
    s = Spr(22, 12)
    s.fill(BOARD, lambda x, y: y < 4 or ((x < 3 or x > 18) and y < 12), lambda x, y: 6 if y == 0 else 4 if y < 4 else 2)
    s.fill(PAPER, box(5, 0, 13, 2), lambda x, y: 5)
    s.put(15, 0, INK[2]); s.put(15, 1, INK[3]); s.put(16, -0, BRASS[6])
    return s.outline(outline_of(BOARD))


def globe():
    s = Spr(12, 18)
    s.fill(BOARD, lambda x, y: (y >= 12 and abs(x - 5.5) <= 1) or (y == 17 and 2 <= x < 10), lambda x, y: 4)
    s.fill(ramp(hx("#5b7a6a")), ell(5.5, 6, 5, 5), roundlit(5.5, 6, 5, 5, 8))
    for y in range(1, 12): s.put(10 - abs(y - 6) * 0.3, y, BRASS[5])
    return s.outline(outline_of(BOARD))


def catalogue():
    s = Spr(16, 22)
    s.fill(SHELF, box(0, 0, 16, 22), boxlit(0, 0, 16, 22, len(SHELF), top=2))
    for y in range(3, 20, 4):
        for x in range(2, 14, 4):
            s.fill(SHELF, box(x, y, x + 3, y + 3), lambda xx, yy: 5 if yy == y else 3)
            s.put(x + 1, y + 1, BRASS[6])
    return s.outline(outline_of(SHELF))


def candle_float():
    s = Spr(3, 7)
    s.fill(PAPER, lambda x, y: y >= 2, lambda x, y: 6 - x)
    s.put(1, 1, hx("#f7b244")); s.put(1, 0, hx("#fff0c0"))
    return s


@biome(name="Ledger Vaults", tag="An archive that never ends",
       palette=[BOARD[4], BOOKS[0][1], BOOKS[1][2], RUG_R[4], hx("#f7b244"), INK[2]],
       look="Walnut boards, bookcases for walls, free-standing shelves that make a maze of the room, floating candles and "
            "loose pages. Dusty and warm, with ink-black pools and worn red rugs as the accents.",
       hazard="Shelves fall: a big monster that charges into a shelf topples it, crushing whatever is behind and opening "
              "a new path. Ink pools hide anything standing in them (a monster's tell disappears).",
       props="Shelves (walls that fall), reading desks, the card catalogue, a globe, page drifts, ink pools.",
       fits="Jinx's tricksters and gamblers, the Steward, anything that hides.")
def ledger_vaults():
    rooms = []

    def cases(R):
        us = sorted(R.top_of)
        for j, u in enumerate(range(us[0], us[-1] - 19, 20)):
            bc = bookcase(20, R.wh - 3, j)
            x, y = R.wx(u, 2); R.cv.im.alpha_composite(bc.im, (x, y)); R.cv.px = R.cv.im.load()

    def pages(n):
        def place(R):
            for _ in range(n):
                u, v = R.r.uniform(3, R.w - 3), R.r.uniform(3, R.h - 3)
                if R.on(int(u), int(v)):
                    x, y = R.at(u, v)
                    for k in range(3): R.cv.put(x + k, y, PAPER[6]); R.cv.put(x + k, y + 1, PAPER[3])
        return place

    def ink(u0, v0, rx, ry):
        def f(u, v):
            d = ((u - u0) / rx) ** 2 + ((v - v0) / ry) ** 2 + 0.2 * math.sin(u * 0.8) * math.sin(v)
            if d < 1: return INK[int(clamp(round(1 + (1 - d) * 3), 0, 4))]
            return None
        return f

    # 1. The stacks: a shelf maze
    R = Room(206, 100, 51)
    inkp = ink(36, 82, 16, 6)
    def stacks_overlay(u, v):
        c = inkp(u, v)
        if c: return c
        if 74 <= u < 136 and 36 <= v < 66:
            if u in (74, 75, 134, 135) or v in (36, 37, 64, 65): return RUG_R[5]
            return RUG_R[3] if ((u - 74) // 3 + (v - 36) // 3) % 3 else RUG_R[2]
        return None
    R.floor(BOARD, boards(5), overlay=stacks_overlay, mid=0.5, spread=0.8)
    R.wall(lambda u, k: 3, SHELF, [cases])
    for (u, v, w) in [(50, 40, 40), (160, 40, 44), (104, 92, 44), (190, 92, 26)]:
        R.stamp(bookcase(w, 24, int(u)), u, v)
    R.stamp(desk(), 30, 66); R.stamp(globe(), 150, 70)
    pages(18)(R)
    for (u, v) in [(26, 18), (96, 20), (182, 20), (124, 60), (20, 92), (186, 70)]:
        R.stamp(candle_float(), u, v - 10, shadow=0); R.light(u, v - 14, 24, (255, 200, 110), 0.7)
    cast(R, "JinxCardKing", 104, 60, 60, 74)
    rooms.append(("The Stacks", "A maze of free-standing shelves on walnut boards, a worn rug in the middle, ink spilt by the desk.", R.finish(0.7)))

    # 2. The reading room: a round rug like a dome's shadow, desks in a ring
    R = Room(206, 112, 52)
    ccx, ccy = 103, 60
    def reading_overlay(u, v):
        d = math.hypot(u - ccx, (v - ccy) * 1.6)
        a = math.atan2((v - ccy) * 1.6, u - ccx)
        if d < 50:
            if int(d) in (49, 48, 30, 29): return RUG_R[6]
            if d < 12: return BRASS[int(clamp(round(5 - d * 0.25), 2, 6))] if int(d) % 4 else BRASS[2]
            seg = int((a + math.pi) / (math.pi / 8))
            if d > 30: return RUG_R[3] if seg % 2 else RUG_R[2]
            return RUG_R[4] if (int(d) // 4 + seg) % 2 else RUG_R[3]
        return None
    R.floor(BOARD, boards(5, 9), overlay=reading_overlay, inside=cut_corners(206, 112, 16), mid=0.5, spread=0.8)
    R.wall(lambda u, k: 3, SHELF, [cases])
    for i in range(6):
        a = i / 6 * math.tau
        u, v = ccx + 66 * math.cos(a), ccy + 40 * math.sin(a)
        if R.on(int(u), int(v)):
            R.stamp(desk(), u, v); R.stamp(candle_float(), u + 6, v - 13, shadow=0); R.light(u + 6, v - 16, 22, (255, 200, 110), 0.7)
    R.stamp(globe(), ccx, ccy + 4)
    pages(14)(R)
    cast(R, "JinxHouseOfCards", 160, 100, 46, 100)
    rooms.append(("The Reading Room", "A round red rug with a brass compass at its heart, reading desks in a ring, a globe in the middle.", R.finish(0.7)))

    # 3. The index hall: a corridor of card catalogues
    R = Room(240, 56, 53)
    R.floor(BOARD, boards(4, 11), mid=0.5, spread=0.8, overlay=lambda u, v: (RUG_R[3] if (u // 4 + v // 4) % 2 else RUG_R[2]) if 20 <= v < 36 and 6 <= u < 234 else None)
    R.wall(lambda u, k: 3, SHELF, [cases])
    for u in range(20, 230, 26):
        R.stamp(catalogue(), u, 16, shadow=0.3); R.stamp(catalogue(), u + 12, 54, shadow=0.3)
    pages(10)(R)
    for u in (60, 120, 180):
        R.stamp(candle_float(), u, 16, shadow=0); R.light(u, 12, 26, (255, 200, 110), 0.7)
    cast(R, "JinxRingmaster", 200, 36, 40, 34)
    rooms.append(("The Index Hall", "A corridor between card catalogues, a runner rug down the middle.", R.finish(0.66)))
    return rooms


# ======== The Seam
@biome(name="The Seam", tag="Chaos's own floor: the other floors, torn and stitched",
       palette=[VOID[2], VOID[4], VOID[6], CRYPT[4], STONE_G[4], IRON[4]],
       look="Islands of the other floors (crypt flags next to iron plate next to old boards) stitched over a violet void lit "
            "from below. The back wall changes material every few steps. The violet seams are the only bright colour.",
       hazard="Shifts: when a room is cleared its islands drift into a new layout before the next wave. Rifts open between "
              "islands, and anything knocked into one comes out of another.",
       props="Fragments of every biome's props, rift shards that teleport whoever strikes them, the gate's standing rift.",
       fits="Everything. The late chaos floors, where tier 4 and 5 monsters live.")
def the_seam():
    rooms = []

    def void_overlay(R, islands, cracks=()):
        def f(u, v):
            x, y = R.at(u, v)
            for (a, b, c, d, tones, pat) in islands:
                rough = int(3 * R.n.value(x * 2, y * 2, 3))
                a2, b2, c2, d2 = a + rough, b + rough // 2, c - rough, d - rough // 2
                if a2 <= u < c2 and b2 <= v < d2:
                    t = 0.55 * (len(tones) - 1) + (R.n.cluster(x, y) - 0.5) * 2 + pat(u, v)
                    if v == b2: t += 2
                    for (cx0, cy0, cx1, cy1) in cracks:
                        if abs((u - cx0) * (cy1 - cy0) - (v - cy0) * (cx1 - cx0)) / math.hypot(cx1 - cx0, cy1 - cy0) < 1 and min(cx0, cx1) <= u <= max(cx0, cx1):
                            return VOID[7]
                    return tones[int(clamp(round(t), 0, len(tones) - 1))]
                if a2 <= u < c2 and d2 <= v < d2 + 4: return tones[1] if (u + v) % 3 else tones[0]
            t = 1.5 + R.n.value(x, y, 7) * 2.5 + (2.5 if R.n.value(x * 4, y * 4, 1.3) > 0.95 else 0)
            return VOID[int(clamp(round(t), 0, 7))]
        return f

    def torn_wall(R):
        segs = [(CRYPT, face_bricks(9, 4, 3.0, 1)), (STONE_G, face_bricks(10, 5, 3.0, 2)), (BRICK, face_bricks(8, 4, 3.0, 3)), (BOARD, face_bricks(14, 5, 3.0, 4))]
        us = sorted(R.top_of)
        for j, u0 in enumerate(range(us[0], us[-1] + 1, 48)):
            tones, face = segs[j % len(segs)]
            for u in range(u0, min(u0 + 48, us[-1] + 1)):
                for k in range(2, R.wh - 1):
                    x, y = R.wx(u, k)
                    t = face(u, k) + (R.n.cluster(x, y) - 0.5) - 1.4 * max(0, (k - (R.wh - 7)) / 7.0)
                    R.cv.put(x, y, tones[int(clamp(round(t), 0, len(tones) - 1))])
            for k in range(0, R.wh):
                x, y = R.wx(u0 + int(2 * math.sin(k * 0.9)), k)
                R.cv.put(x, y, VOID[7]); R.cv.put(x + 1, y, VOID[5])
            R.light(u0, 0, 14, (180, 120, 255), 0.4)

    def shard(h=14):
        s = Spr(9, h)
        s.fill(VOID[2:], lambda x, y: abs(x - 4) <= 4 - abs(y - h * 0.45) * (8.0 / h), lambda x, y: 5 - x * 0.5)
        return s.outline(VOID[0])

    # 1. The island arena
    R = Room(240, 110, 61)
    isl = [(0, 0, 80, 46, CRYPT, flags(12, 8, 1)), (88, 0, 240, 42, STONE_G, flags(14, 8, 2)),
           (0, 54, 104, 110, BOARD, boards(5, 4)), (114, 50, 240, 110, IRON, plates(22, 14, 5))]
    R.floor(CRYPT, plain(), overlay=void_overlay(R, isl, cracks=[(140, 60, 200, 96)]), mid=0.5)
    R.wall(lambda u, k: 3, CRYPT, [torn_wall], cap=VOID[6])
    for (u, v) in [(84, 50), (110, 46), (60, 50)]:
        R.stamp(shard(), u, v, shadow=0); R.light(u, v - 7, 26, (190, 130, 255), 0.75)
    R.stamp(brazier(IRON), 30, 40); R.light(30, 26, 26, (255, 160, 70), 0.7)
    R.stamp(pew(26), 180, 30); R.stamp(anvil(), 200, 100); R.stamp(bookcase(30, 22, 3), 50, 100)
    for i in range(0, 40):
        u, v = 140 + i * 1.5, 60 + i * 0.9
        R.light(u, v, 6, (190, 130, 255), 0.25)
    cast(R, "UmbHollowKing", 176, 90, 40, 36)
    rooms.append(("The Island Arena", "Four floors torn from other places, side by side over the void, a rift across the iron.", R.finish(0.7)))

    # 2. The rift bridge: a narrow walk of mismatched slabs over the void
    R = Room(240, 60, 62)
    walk = []
    x, mats = 0, [(CRYPT, flags(10, 7, 3)), (STONE_G, flags(12, 8, 4)), (BOARD, boards(4, 5)), (IRON, plates(16, 12, 6))]
    j = 0
    while x < 240:
        w = R.r.randint(26, 44); y0 = 18 + int(6 * math.sin(x * 0.03))
        tones, pat = mats[j % 4]; walk.append((x, y0, x + w - 3, y0 + 22, tones, pat)); x += w; j += 1
    R.floor(CRYPT, plain(), overlay=void_overlay(R, walk), mid=0.5)
    R.wall(lambda u, k: 3, CRYPT, [torn_wall], cap=VOID[6])
    for (a, b, c, d, t, p) in walk[1::2]:
        R.stamp(shard(10), c + 1, b + 4, shadow=0); R.light(c + 1, b - 2, 18, (190, 130, 255), 0.7)
    cast(R, "UmbGlitterswarm", 180, 40, 40, 38)
    rooms.append(("The Rift Bridge", "A narrow way of mismatched slabs over the void, each from a different floor.", R.finish(0.66)))

    # 3. The shard gate: a standing rift in a ring of shards
    R = Room(176, 112, 63)
    ccx, ccy = 88, 60
    isl = [(10, 6, 166, 108, CRYPT, flags(12, 8, 9))]
    def gate(u, v):
        d = math.hypot(u - ccx, (v - ccy) * 1.5)
        if d < 18: return VOID[int(clamp(round(7 - d * 0.3 + math.sin(d * 1.3) * 1.5), 2, 7))]
        if d < 20: return VOID[7]
        if 30 <= d < 32: return VOID[5] if (u + v) % 4 else VOID[7]
        return void_overlay(R, isl)(u, v)
    R.floor(CRYPT, plain(), overlay=gate, mid=0.5)
    R.wall(lambda u, k: 3, CRYPT, [torn_wall], cap=VOID[6])
    for i in range(7):
        a = i / 7 * math.tau
        u, v = ccx + 52 * math.cos(a), ccy + 32 * math.sin(a)
        R.stamp(shard(16), u, v, shadow=0); R.light(u, v - 8, 20, (190, 130, 255), 0.7)
    R.light(ccx, ccy, 50, (190, 130, 255), 0.8)
    cast(R, "UmbHollowKing", 140, 102, 40, 100)
    rooms.append(("The Shard Gate", "A standing rift in the floor ringed by shards: the way down to the next chaos floor.", R.finish(0.62)))
    return rooms


# ------------------------------------------------------------------ output
def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    out = []
    for fn, info in BIOMES:
        rooms = fn()
        slug = info["name"].lower().replace(" ", "_")
        files = []
        for i, (title, blurb, im) in enumerate(rooms):
            f = "%s_%d.png" % (slug, i + 1)
            im.convert("RGB").save(os.path.join(outdir, f))
            files.append((title, blurb, f))
        out.append((info, files))
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/concepts/chaos")
