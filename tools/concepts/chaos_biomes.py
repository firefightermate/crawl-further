"""Concept art for Crawl Chaos's floors: one room per new biome, built the way the game builds its rooms.

    python3 tools/concepts/chaos_biomes.py <outdir>

How a Crawl room is made (read from the game's atlases, e.g. AtlasEnvironmentCrypt crypt_large1_floor / _wall):
  - the floor is one painted image the size of the room (200 x 96 for a large room), mottled stone in four or five
    tones with a lighter oval in the middle and darker edges;
  - the back wall is one strip about 30 px tall across the top: a light cap line, a brick or stone face with pillars,
    arches and slit windows, a dark skirting where it meets the floor;
  - there are no side or bottom walls, only black;
  - props are small (a brazier is about 12 x 20), outlined in their darkest tone, shaded in three or four tones,
    with a soft shadow, and the lit ones throw a warm pool.
Everything here follows those rules: limited palettes per material, ordered dithering instead of smooth gradients,
1 px dark outlines on props, and the room laid out at the game's scale. The monster in each room is one of our own
sheets (frame 0), at its in-game size.

Concepts only: nothing here ships with the mod.
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H = 256, 144                 # one screen
RX0, RY0, RW, RH = 28, 36, 200, 96   # floor rect (the wall strip sits above it)
WALL = 30
SCALE = 4

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hexs(*cs):
    return [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in cs]


# ------------------------------------------------------------------ noise and quantising
class Noise:
    def __init__(self, seed):
        self.r = random.Random(seed)
        self.g = {}

    def v(self, ix, iy, s):
        k = (ix, iy, s)
        if k not in self.g:
            self.g[k] = self.r.random()
        return self.g[k]

    def value(self, x, y, s):
        fx, fy = x / s, y / s
        ix, iy = int(math.floor(fx)), int(math.floor(fy))
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = self.v(ix, iy, s); b = self.v(ix + 1, iy, s); c = self.v(ix, iy + 1, s); d = self.v(ix + 1, iy + 1, s)
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty

    def fbm(self, x, y, octaves=((14, 0.5), (7, 0.28), (3, 0.14), (1.5, 0.08))):
        return sum(self.value(x, y, s) * w for s, w in octaves) / sum(w for _, w in octaves)


def quant(pal, lum, x, y, dither=0.45):
    n = len(pal)
    t = lum * (n - 1) + (BAYER[y % 4][x % 4] / 16.0 - 0.47) * dither
    return pal[int(clamp(round(t), 0, n - 1))]


# ------------------------------------------------------------------ canvases
class Layer:
    """RGBA buffer with helpers. Props are drawn into their own Layer, outlined, then stamped."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.im.load()

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c if len(c) == 4 else c + (255,)

    def get(self, x, y):
        x, y = int(x), int(y)
        return self.px[x, y] if 0 <= x < self.w and 0 <= y < self.h else (0, 0, 0, 0)

    def outline(self, c):
        src = self.im.copy(); sp = src.load()
        for y in range(self.h):
            for x in range(self.w):
                if sp[x, y][3]: continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < self.w and 0 <= yy < self.h and sp[xx, yy][3] > 0:
                        self.px[x, y] = c + (255,); break


def shape(layer, pal, inside, lum, seed=0, dither=0.5):
    """Fill every pixel where inside(x, y) with the palette tone lum(x, y) (0..1), dithered."""
    for y in range(layer.h):
        for x in range(layer.w):
            if inside(x, y):
                layer.put(x, y, quant(pal, clamp(lum(x, y)), x, y, dither))


def ellipse_in(cx, cy, rx, ry):
    return lambda x, y: ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def rect_in(x0, y0, x1, y1):
    return lambda x, y: x0 <= x < x1 and y0 <= y < y1


def lit(cx, cy, rx, ry, top=0.85, bottom=0.25, side=0.15):
    """Lighting for a rounded form lit from the upper left."""
    def f(x, y):
        dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        return clamp(0.55 - 0.45 * dy * 0.9 - side * dx + 0.2 * (1 - min(1, dx * dx + dy * dy)))
    return f


# ------------------------------------------------------------------ the room
class Room:
    def __init__(self, seed):
        self.cv = Layer(W, H)
        for y in range(H):
            for x in range(W):
                self.cv.px[x, y] = (8, 7, 10, 255)
        self.n = Noise(seed)
        self.r = random.Random(seed)
        self.lights = []
        self.mask = [[0] * W for _ in range(H)]     # 1 on the floor

    # floors
    def floor(self, pal, pattern, extra=None, centre=0.16, grain=0.26, mortar=0.2, dither=0.28):
        """Paint the floor: a pattern (luminance and mortar) with grain, a light oval in the middle, darker edges."""
        n = self.n
        for y in range(RY0, RY0 + RH):
            for x in range(RX0, RX0 + RW):
                u, v = x - RX0, y - RY0
                lum, line = pattern(u, v)
                g = n.fbm(x, y) - 0.5
                d = ((u - RW / 2) / (RW * 0.5)) ** 2 + ((v - RH / 2) / (RH * 0.55)) ** 2
                lum = lum + g * grain + centre * (1 - min(1, d)) - 0.1 * max(0, d - 0.85)
                if u < 2 or u > RW - 3 or v > RH - 3: lum -= 0.12
                if line: lum -= mortar
                if extra: lum = extra(u, v, lum)
                if lum is None: continue
                self.cv.put(x, y, quant(pal, clamp(lum), x, y, dither))
                self.mask[y][x] = 1

    # the back wall strip
    def wall(self, pal, face, motif=None, cap=None):
        y0 = RY0 - WALL
        for y in range(y0, RY0):
            for x in range(RX0 - 1, RX0 + RW + 1):
                u, v = x - RX0, y - y0
                lum, line = face(u, v)
                lum += (self.n.fbm(x * 1.3, y * 1.3) - 0.5) * 0.25
                lum -= 0.2 * max(0, (v - (WALL - 8)) / 8.0)     # darker toward the skirting
                if line: lum -= 0.3
                self.cv.put(x, y, quant(pal, clamp(lum), x, y))
        capc = cap or pal[-1]
        for x in range(RX0 - 2, RX0 + RW + 2):
            self.cv.put(x, y0, capc); self.cv.put(x, y0 + 1, mix(capc, pal[2], 0.5))
            self.cv.put(x, RY0 - 1, pal[0]); self.cv.put(x, RY0, pal[0])
            if self.mask[RY0 + 1][x] if 0 <= x < W else 0:
                self.cv.put(x, RY0 + 1, mix(self.cv.get(x, RY0 + 1)[:3], pal[0], 0.6))   # shadow line on the floor
        if motif: motif(self, y0)

    def stamp(self, layer, x, y, shadow=True, anchor=(0.5, 1.0)):
        """Place a prop with its feet at (x, y), with a soft dark shadow under it."""
        lx, ly = int(x - layer.w * anchor[0]), int(y - layer.h * anchor[1])
        if shadow:
            rx = max(3, layer.w * 0.42)
            for yy in range(-2, 3):
                for xx in range(int(-rx), int(rx) + 1):
                    if (xx / rx) ** 2 + (yy / 2.2) ** 2 <= 1:
                        c = self.cv.get(x + xx, y + yy)
                        if c[3]: self.cv.put(x + xx, y + yy, mix(c[:3], (8, 6, 10), 0.45))
        self.cv.im.alpha_composite(layer.im, (lx, ly))
        self.cv.px = self.cv.im.load()

    def light(self, x, y, r, c, k=0.5):
        self.lights.append((x, y, r, c, k))

    def finish(self, ambient=0.84):
        """Lighting: the room a little dimmer away from lights, warm pools around them (dithered, so it stays pixel)."""
        out = self.cv.im.copy(); px = out.load()
        for y in range(H):
            for x in range(W):
                c = px[x, y]
                if c[:3] == (8, 7, 10): continue
                f = ambient
                add = [0.0, 0.0, 0.0]
                for (lx, ly, r, col, k) in self.lights:
                    d = math.hypot(x - lx, (y - ly) * 1.5) / r
                    if d < 1:
                        t = (1 - d) ** 2 * k
                        b = BAYER[y % 4][x % 4] / 16.0
                        if t > 0.06 + b * 0.08:
                            f += t * 0.5
                            for i in range(3): add[i] += col[i] * t * 0.35
                px[x, y] = tuple(int(clamp(c[i] * f + add[i], 0, 255)) for i in range(3)) + (255,)
        return out


# ------------------------------------------------------------------ floor and wall patterns
def flagstones(cell=(13, 9), jitter=0.4, seed=1):
    """Stone flags in rows, each row's stones of varied length, each stone its own tone, lit edge on top."""
    rows = {}
    def cuts(row):
        if row not in rows:
            r = random.Random(row * 977 + seed)
            x, c = -r.randint(0, cell[0]), []
            while x < RW + cell[0]:
                c.append(x); x += r.randint(int(cell[0] * 0.6), int(cell[0] * 1.5))
            rows[row] = c
        return rows[row]
    def f(u, v):
        row = int(v // cell[1]); c = cuts(row)
        i = max(k for k in range(len(c)) if c[k] <= u)
        su, sv = u - c[i], v % cell[1]
        tone = random.Random((row, i, seed).__hash__()).uniform(-0.1, 0.1)
        line = su == 0 or sv == 0
        lum = 0.55 + tone + (0.07 if sv == 1 else 0) - (0.05 if sv == cell[1] - 1 else 0) + (0.04 if su == 1 else 0)
        return lum, line
    return f


def bricks(bw=9, bh=4, base=0.55, var=0.1, seed=2):
    def f(u, v):
        row = int(v // bh); off = (row % 2) * (bw // 2)
        su, sv = (u + off) % bw, v % bh
        key = ((u + off) // bw, row)
        t = random.Random(hash(key) ^ seed).uniform(-var, var)
        return base + t + (0.1 if sv == 1 else 0), (su == 0 or sv == 0)
    return f


def planks(ph=5, seed=3):
    def f(u, v):
        row = int(v // ph)
        r = random.Random(row * 7919 + seed)
        seams = sorted(r.sample(range(8, RW - 8), 3))
        line = v % ph == 0 or u in seams
        grain = 0.06 * math.sin(u * 0.35 + row * 2.1)
        return 0.52 + r.uniform(-0.1, 0.1) + grain, line
    return f


def plates(pw=24, ph=16, seed=4):
    def f(u, v):
        su, sv = u % pw, v % ph
        line = su == 0 or sv == 0
        rivet = (su in (2, pw - 2)) and (sv in (2, ph - 2))
        return (0.75 if rivet else 0.5 + random.Random((u // pw) * 31 + (v // ph) * 17 + seed).uniform(-0.08, 0.08)
                - 0.06 * (sv / ph)), line
    return f


def earth(seed=5):
    def f(u, v):
        return 0.5, False
    return f


# ------------------------------------------------------------------ props
def P(w, h):
    return Layer(w, h)


def brazier(pal_metal, flame=True):
    L = P(12, 20)
    shape(L, pal_metal, lambda x, y: (8 <= y < 12 and 1 <= x < 11) or (12 <= y < 17 and 4 <= x < 8) or (17 <= y < 19 and 2 <= x < 10),
          lambda x, y: 0.75 - x / 14 + (0.15 if y in (8, 17) else 0))
    if flame:
        fl = hexs("#6b1d0e", "#c2410c", "#f97316", "#fbbf24", "#fff1b8")
        shape(L, fl, lambda x, y: y < 8 and abs(x - 5.5) < (8 - y) * 0.45 + 0.6 and y > 1,
              lambda x, y: 0.95 - abs(x - 5.5) * 0.18 - (7 - y) * 0.06)
    L.outline((16, 12, 14))
    return L


def candle_stand(metal):
    L = P(7, 18)
    shape(L, metal, lambda x, y: x == 3 and 3 <= y < 17 or (y == 17 and 1 <= x < 6) or (y == 5 and 1 <= x < 6), lambda x, y: 0.6)
    wax = hexs("#7a6a4f", "#c9b98f", "#efe2bc")
    for cx in (1, 3, 5):
        shape(L, wax, lambda x, y, cx=cx: x == cx and 2 <= y < 5, lambda x, y: 0.7)
        L.put(cx, 1, (255, 214, 120)); L.put(cx, 0, (255, 245, 200))
    L.outline((16, 12, 14))
    return L


# ------------------------------------------------------------------ the biomes
BIOMES = []


def biome(fn):
    BIOMES.append(fn)
    return fn


STONE_GREEN = hexs("#1d2421", "#323d38", "#4a5650", "#66716a", "#858e84", "#a3a993")
BRINE = hexs("#0b1f26", "#123440", "#1b4b57", "#2b6a72", "#4f8e8e", "#9cc7bd")
WOOD = hexs("#1e140f", "#3a261b", "#5a3b27", "#7a5234", "#9b6c43")
BRASS = hexs("#2a2015", "#4f3d23", "#7d6233", "#a8884a", "#d1b46e")
GLASS = [hexs("#3b1618", "#6e2a2c", "#9d4a3e"), hexs("#14283b", "#24496a", "#3f7393"), hexs("#3a2f12", "#6e5a22", "#a08a3e")]


def sprite(sheet, frame=0, folder=None):
    for d in ([folder] if folder else []) + sorted(os.listdir(os.path.join(ROOT, "art"))):
        p = os.path.join(ROOT, "art", d, sheet + ".json")
        if os.path.exists(p):
            m = json.load(open(p))
            im = Image.open(p[:-5] + ".png").convert("RGBA")
            c, r = frame % m["cols"], frame // m["cols"]
            cell = im.crop((c * m["cellW"], r * m["cellH"], (c + 1) * m["cellW"], (r + 1) * m["cellH"]))
            bb = cell.getbbox()
            cell = cell.crop(bb) if bb else cell
            L = Layer(cell.size[0], cell.size[1]); L.im = cell; L.px = cell.load()
            return L
    return None


HERO_MAP = [
    "....oo.......",
    "...oSSo......",
    "..oSssso.....",
    "..oSkkso...w.",
    "..osssso..ow.",
    "...oSso...ow.",
    "..oRRRRo..ow.",
    ".oRrrrrRo.ow.",
    "oBoRrrrRo.ow.",
    "oBBoRrrRohgho",
    "oBBoRrrRo.o..",
    ".oBoRRRRo....",
    "..ooDDDDo....",
    "...oDooDo....",
    "...oDo.Do....",
    "...oLo.Lo....",
    "...ooo.oo....",
]
HERO_COL = {"o": (18, 12, 14), "S": (196, 204, 214), "s": (128, 138, 152), "k": (30, 28, 36), "R": (176, 72, 58),
            "r": (128, 46, 40), "B": (120, 92, 58), "D": (62, 48, 44), "L": (40, 30, 28), "w": (220, 226, 236),
            "h": (150, 112, 60), "g": (210, 170, 90)}


def hero():
    """A hero-sized knight (our own drawing, a pixel map) for scale: helm, tunic, shield and sword."""
    L = P(len(HERO_MAP[0]), len(HERO_MAP))
    for y, row in enumerate(HERO_MAP):
        for x, ch in enumerate(row):
            if ch in HERO_COL: L.put(x, y, HERO_COL[ch])
    return L


@biome
def drowned_nave():
    R = Room(11)
    tide = lambda u, v: u < 64 + 18 * math.sin(v * 0.09) + 6 * math.sin(v * 0.33)

    def water(u, v, lum):
        edge = 64 + 18 * math.sin(v * 0.09) + 6 * math.sin(v * 0.33)
        if u < edge:
            x, y = u + RX0, v + RY0
            w = 0.35 + 0.25 * (R.n.value(x * 2, y * 4, 6) - 0.5) + (0.18 if (y + int(x * 0.3)) % 9 == 0 else 0)
            if edge - u < 2: w = 0.95
            R.cv.put(x, y, quant(BRINE, clamp(w + 0.1 * (lum - 0.5)), x, y))
            R.mask[y][x] = 1
            return None
        if edge - u > -3: lum -= 0.12   # wet stone at the tide line
        return lum
    R.floor(STONE_GREEN, flagstones((14, 8), seed=3), extra=water)

    def nave(r, y0):
        for i, wx in enumerate(range(RX0 + 14, RX0 + RW - 10, 36)):
            # pillar between windows
            px0 = wx - 9
            for y in range(y0 + 2, RY0 - 1):
                for x in range(px0, px0 + 5):
                    r.cv.put(x, y, quant(STONE_GREEN, 0.75 - (x - px0) * 0.12, x, y))
            # tall pointed window with stained glass
            g = GLASS[i % 3]
            for y in range(y0 + 5, RY0 - 4):
                half = 4 if y > y0 + 9 else max(0, 4 - (y0 + 9 - y))
                for x in range(wx + 4 - half, wx + 4 + half + 1):
                    lead = (x - wx) % 3 == 0 or (y - y0) % 4 == 0
                    r.cv.put(x, y, STONE_GREEN[0] if lead else quant(g, 0.6 + 0.3 * math.sin(x + y), x, y))
            for y in range(y0 + 5, RY0 - 4):
                r.cv.put(wx - 1, y, STONE_GREEN[4]); r.cv.put(wx + 9, y, STONE_GREEN[1])
            r.light(wx + 4, RY0 + 18, 26, g[2], 0.35)
        # kelp hanging from the cap
        for x in range(RX0 + 4, RX0 + RW - 4, 23):
            ln = r.r.randint(5, 12)
            for k in range(ln):
                r.cv.put(x + int(math.sin(k * 0.8)), y0 + 2 + k, hexs("#1f3b2a", "#2f5a3c")[k % 2])
    R.wall(STONE_GREEN, bricks(10, 5, 0.5, seed=7), nave)

    # pews, broken and whole
    def pew(w, broken=False):
        L = P(w, 9)
        shape(L, WOOD, lambda x, y: (y < 3 and (not broken or x < w * 0.6)) or (3 <= y < 9 and x in (1, w - 2)) or (5 <= y < 7),
              lambda x, y: 0.75 if y == 0 else 0.5 if y < 3 else 0.35)
        L.outline((14, 10, 8))
        return L
    for (x, y, w, b) in [(150, 70, 30, False), (190, 72, 26, True), (140, 96, 30, True), (186, 100, 30, False), (150, 124, 22, True)]:
        R.stamp(pew(w, b), x, y)
    # a fallen column across the tide line, and rubble
    col = P(34, 11)
    shape(col, STONE_GREEN, lambda x, y: 2 <= y < 10 and 1 <= x < 33, lambda x, y: 0.85 - (y - 2) * 0.08 + (0.08 if x % 6 == 0 else 0))
    shape(col, STONE_GREEN, ellipse_in(31, 6, 3, 4.5), lambda x, y: 0.45)
    col.outline((12, 16, 14))
    R.stamp(col, 96, 104)
    for (x, y) in [(96, 70), (140, 128), (226, 92)]:
        rb = P(9, 5)
        for k in range(5):
            cx, cy = 1.5 + k * 1.6, 2.5 + (k % 2)
            shape(rb, STONE_GREEN, ellipse_in(cx, cy, 1.8, 1.4), lit(cx, cy, 1.8, 1.4))
        rb.outline((12, 16, 14))
        R.stamp(rb, x, y, shadow=False)
    for (x, y) in [(118, 64), (214, 120)]:
        R.stamp(candle_stand(BRASS), x, y); R.light(x, y - 16, 22, (255, 200, 120), 0.6)
    m = sprite("BelDrownedBell"); R.stamp(m, 60, 116) if m else None
    R.stamp(hero(), 170, 90)
    return R.finish(), dict(
        name="Drowned Nave", tag="A cathedral the sea took back",
        palette=[STONE_GREEN[3], BRINE[3], BRINE[5], GLASS[0][2], GLASS[1][2], WOOD[3]],
        look="Grey-green nave stone, tall arched windows of dim stained glass, broken pews. Brine stands in the low side "
             "of every room and the coloured light from the windows lies across the floor in slanted shafts.",
        hazard="The tide: brine floods across the room and drains back on a slow cycle. Standing in it slows the hero, and "
               "water monsters (Bel'Mora's) heal in it, as in their brine pools. Some rooms flood fully, then the floor is "
               "an island fight.",
        props="Pews to break (cover that monsters smash through), fallen bells, reliquaries that hold gold.",
        rooms="Long naves (two screens wide) with side chapels, and a font room that is all water but a ring of stone.",
        fits="Bel'Mora, the Drowned Bell, big swimmers.")


ASH = hexs("#1b1816", "#2f2a26", "#47403a", "#625a51", "#81786c", "#a39a8a")
BONE = hexs("#3a3428", "#6e6551", "#a39a82", "#cfc7ad", "#eee8d2")
LANTERN = hexs("#5a2a0c", "#b5651d", "#f0a442", "#ffe08a")


@biome
def bone_orchard():
    R = Room(21)
    roots = []
    rr = random.Random(4)
    for _ in range(9):
        x, y = rr.uniform(0, RW), rr.uniform(0, RH)
        pts = []
        for i in range(40):
            pts.append((int(x), int(y))); x += rr.choice((-1, 1, 1, 0)); y += rr.choice((0, 0, 1, -1))
        roots.extend(pts)
    rootset = set(roots)

    def soil(u, v, lum):
        if (u, v) in rootset: return lum + 0.28
        if (u, v - 1) in rootset: return lum - 0.12
        return lum
    R.floor(ASH, lambda u, v: (0.5 + 0.08 * math.sin(u * 0.2) * math.sin(v * 0.31), False), extra=soil, grain=0.5)

    def bank(r, y0):
        for x in range(RX0 + 6, RX0 + RW - 6, 15):
            # ribs set in the earth bank
            for t in range(WALL - 8):
                xx = x + int(5 * math.sin(t / (WALL - 8) * math.pi))
                r.cv.put(xx, y0 + 4 + t, quant(BONE, 0.75, xx, y0 + t))
                r.cv.put(xx + 1, y0 + 4 + t, BONE[1])
        for x in range(RX0 + 20, RX0 + RW - 10, 47):
            sk = P(9, 8)
            shape(sk, BONE, ellipse_in(4.5, 3.5, 4.2, 3.6), lit(4, 3, 4, 4))
            sk.put(3, 4, (20, 16, 14)); sk.put(6, 4, (20, 16, 14)); sk.put(4, 6, (40, 34, 28)); sk.put(5, 6, (40, 34, 28))
            sk.outline((20, 16, 14))
            r.cv.im.alpha_composite(sk.im, (x, y0 + 11)); r.cv.px = r.cv.im.load()
    R.wall(ASH, lambda u, v: (0.42 + 0.1 * math.sin(u * 0.15 + v * 0.4), False), bank)

    def tree(s):
        L = P(int(40 * s), int(46 * s))
        cx = L.w / 2
        def limb(x0, y0, x1, y1, w):
            n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 1
            for i in range(n + 1):
                t = i / n
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                ww = w * (1 - 0.6 * t)
                for dx in range(-int(ww), int(ww) + 1):
                    L.put(x + dx, y, quant(BONE, 0.8 - (dx + ww) / (2 * ww + 1) * 0.6, int(x + dx), int(y)))
        limb(cx, L.h - 1, cx, L.h * 0.45, 2.2 * s)
        for (dx, dy, w) in [(-14, -40, 1.4), (12, -42, 1.4), (-5, -44, 1.2), (16, -30, 1.1), (-17, -26, 1.1)]:
            limb(cx, L.h * 0.55, cx + dx * s, L.h + dy * s, w * s)
        for (dx, dy) in [(-14, -40), (16, -30), (-17, -26)]:
            lx, ly = cx + dx * s, L.h + dy * s + 2
            for k in range(3): L.put(lx, ly + k, BONE[0])
            shape(L, LANTERN, lambda x, y, lx=lx, ly=ly: abs(x - lx) <= 1 and ly + 3 <= y < ly + 7, lambda x, y: 0.9)
        L.outline((18, 14, 12))
        return L, [(cx + dx * s, L.h + dy * s + 6) for dx, dy in [(-14, -40), (16, -30), (-17, -26)]]
    for (x, y, s) in [(70, 86, 1.0), (196, 80, 1.1), (130, 126, 0.85)]:
        t, ls = tree(s)
        R.stamp(t, x, y)
        for (lx, ly) in ls:
            R.light(x - t.w / 2 + lx, y - t.h + ly, 30, (255, 190, 100), 0.7)
    def pile():
        L = P(14, 7)
        rnd = random.Random(len(R.lights))
        for i in range(7):
            cx, cy = rnd.uniform(3, 11), rnd.uniform(2, 5)
            shape(L, BONE, ellipse_in(cx, cy, 2.6, 1.3), lit(cx, cy, 2.6, 1.3))
        L.outline((20, 16, 14))
        return L
    for (x, y) in [(112, 66), (160, 116), (52, 120), (220, 108)]:
        R.stamp(pile(), x, y)
    m = sprite("OssTombwright"); R.stamp(m, 160, 92) if m else None
    R.stamp(hero(), 110, 100)
    return R.finish(0.7), dict(
        name="Bone Orchard", tag="A grove grown from the dead",
        palette=[ASH[3], BONE[3], BONE[1], LANTERN[2], ASH[1]],
        look="Ash-grey soil veined with pale roots, trees of fused bone hung with lanterns that throw warm pools of light, "
             "ribs and skulls set in the earth bank of the back wall. Outside the lantern light the room is dark.",
        hazard="Lanterns: rooms are dark outside the lantern pools. A tree hit hard enough drops its lanterns and the room "
               "goes darker. Bone piles litter the floor, so Ossivar monsters start every fight armed.",
        props="Bone trees (solid, break into piles), grave mounds that cough up a minion when walked over, ossuary shrines.",
        rooms="Wide groves with the trees as pillars to fight around, and narrow root tunnels between them.",
        fits="Ossivar, the Carrion Saint, anything that eats bones.")


IRON = hexs("#141214", "#241f1f", "#363030", "#4b4342", "#655a55", "#857770")
MOLTEN = hexs("#5a1407", "#a3300b", "#e0631a", "#f9a03f", "#ffd77a", "#fff4c9")
BRICK = hexs("#1c1110", "#36201b", "#53302a", "#704338", "#8f5a49")


@biome
def ember_works():
    R = Room(31)
    chan_y = (30, 70); chan_x = (60, 140)

    def channels(u, v, lum):
        x, y = u + RX0, v + RY0
        for cy in chan_y:
            if abs(v - cy) <= 2:
                grate = u % 8 == 0
                t = 1.0 - abs(v - cy) * 0.3 + 0.15 * math.sin(u * 0.4 + v)
                R.cv.put(x, y, IRON[1] if grate else quant(MOLTEN, clamp(t), x, y)); R.mask[y][x] = 1
                return None
            if abs(v - cy) == 3: return lum - 0.2
        for cx in chan_x:
            if abs(u - cx) <= 2:
                grate = v % 8 == 0
                t = 1.0 - abs(u - cx) * 0.3 + 0.15 * math.sin(v * 0.4 + u)
                R.cv.put(x, y, IRON[1] if grate else quant(MOLTEN, clamp(t), x, y)); R.mask[y][x] = 1
                return None
            if abs(u - cx) == 3: return lum - 0.2
        return lum
    R.floor(IRON, plates(24, 16), extra=channels, centre=0.08)
    for cy in chan_y:
        for x in range(RX0, RX0 + RW, 6): R.light(x, RY0 + cy, 10, (255, 120, 40), 0.25)
    for cx in chan_x:
        for y in range(RY0, RY0 + RH, 6): R.light(RX0 + cx, y, 10, (255, 120, 40), 0.25)

    def furnaces(r, y0):
        for x in range(RX0 + 8, RX0 + RW - 30, 50):
            for y in range(y0 + 3, RY0 - 1):
                for xx in range(x, x + 28):
                    r.cv.put(xx, y, quant(IRON, 0.55 - (xx - x) * 0.012 + (0.15 if y == y0 + 3 else 0), xx, y))
            mx = x + 14
            for y in range(y0 + 13, RY0 - 3):
                half = 7 if y > y0 + 16 else 7 - (y0 + 16 - y) * 2
                for xx in range(mx - half, mx + half + 1):
                    t = 1 - abs(xx - mx) / 8 - (RY0 - 3 - y) * 0.05
                    r.cv.put(xx, y, quant(MOLTEN, clamp(t), xx, y))
            r.light(mx, RY0 + 2, 36, (255, 140, 50), 0.8)
            # a pipe up into the dark
            for y in range(y0 - 6, y0 + 3):
                for xx in range(x + 20, x + 25):
                    r.cv.put(xx, y, quant(IRON, 0.7 - (xx - x - 20) * 0.12, xx, y))
    R.wall(BRICK, bricks(8, 4, 0.5, seed=11), furnaces, cap=BRICK[4])

    def anvil():
        L = P(16, 10)
        shape(L, IRON, lambda x, y: (y < 3 and 0 <= x < 16 and not (y == 0 and x > 12)) or (3 <= y < 7 and 5 <= x < 11) or (7 <= y < 10 and 3 <= x < 13),
              lambda x, y: 0.85 if y == 0 else 0.6 - x * 0.02)
        L.outline((8, 6, 6))
        return L

    def crucible():
        L = P(14, 22)
        for y in range(0, 10): L.put(6, y, IRON[4]); L.put(7, y, IRON[2])
        shape(L, IRON, ellipse_in(7, 15, 6.5, 6), lit(6, 14, 6, 6))
        shape(L, MOLTEN, ellipse_in(7, 11, 4.5, 1.6), lambda x, y: 0.9)
        L.outline((8, 6, 6))
        return L
    R.stamp(anvil(), 110, 56); R.stamp(anvil(), 186, 116)
    R.stamp(crucible(), 100, 104, shadow=False); R.light(100, 94, 18, (255, 150, 60), 0.6)
    def cart():
        L = P(18, 12)
        shape(L, WOOD, lambda x, y: y < 8 and 1 <= x < 17, lambda x, y: 0.6 - y * 0.04)
        shape(L, IRON, lambda x, y: (y >= 8 and (abs(x - 4) <= 2 or abs(x - 13) <= 2)), lambda x, y: 0.5)
        shape(L, hexs("#0c0b0c", "#232022", "#3a3537"), lambda x, y: y < 3 and 2 <= x < 16, lambda x, y: (x * 7 % 5) / 5)
        L.outline((8, 6, 6))
        return L
    R.stamp(cart(), 216, 74)
    m = sprite("VhPyreWarden"); R.stamp(m, 180, 92) if m else None
    R.stamp(hero(), 80, 92)
    return R.finish(0.72), dict(
        name="Ember Works", tag="The foundry below the mines",
        palette=[IRON[3], BRICK[3], MOLTEN[3], MOLTEN[1], IRON[1]],
        look="Soot-black riveted iron plate split by channels of molten metal under grates, furnace mouths glowing along a "
             "brick back wall. Most of the light in the room is the metal itself.",
        hazard="The pour: every few seconds a pulse of heat runs down the channels (a bright tell first), burning anything "
               "standing on a grate. Crucibles hang on chains. Hit one and it tips, pouring a short-lived pool.",
        props="Anvils (cover), coal carts that roll when struck, slag heaps.",
        rooms="Grid rooms cut into islands by the channels, and long casting halls with a pour that sweeps end to end.",
        fits="Vhorrul's fire monsters, anything heavy and armoured.")


SOIL = hexs("#191318", "#2b2129", "#3f313b", "#56434f", "#6f5866", "#8b7180")
CAP_T = hexs("#0f2f33", "#16525a", "#1f7f86", "#3fb3ac", "#9be3d3")
CAP_G = hexs("#24320f", "#3f5a16", "#68901f", "#9ec43a", "#dff58f")
STEM = hexs("#4d4440", "#857a70", "#b9ad9d", "#e1d8c6")


@biome
def rot_gardens():
    R = Room(41)

    def moss(u, v, lum):
        x, y = u + RX0, v + RY0
        m = R.n.value(x, y, 9)
        if m > 0.68:
            R.cv.put(x, y, quant(CAP_G[:3], clamp((m - 0.68) * 3 + 0.2), x, y)); R.mask[y][x] = 1
            return None
        if R.n.value(x * 3, y * 3, 2) > 0.93: return lum + 0.35   # mycelium specks
        return lum
    R.floor(SOIL, lambda u, v: (0.5, False), extra=moss, grain=0.55)

    def shelves(r, y0):
        rnd = random.Random(17)
        # hanging roots
        for x in range(RX0 + 3, RX0 + RW - 3, 7):
            ln = rnd.randint(3, 14)
            for k in range(ln): r.cv.put(x + int(math.sin(k * 0.7 + x)), y0 + 2 + k, SOIL[4 if k % 3 else 3])
        for x in range(RX0 + 4, RX0 + RW - 12, 26):
            for k in range(rnd.randint(1, 3)):
                sx, sy = x + rnd.randint(0, 12), y0 + 5 + rnd.randint(0, 16)
                sh = P(12 - k * 2, 4)
                shape(sh, STEM, ellipse_in(sh.w / 2, 1.5, sh.w / 2, 2.2), lambda xx, yy: 0.8 - yy * 0.2)
                sh.outline((20, 14, 18))
                r.cv.im.alpha_composite(sh.im, (sx, sy)); r.cv.px = r.cv.im.load()
    R.wall(SOIL, lambda u, v: (0.4 + 0.15 * R.n.value(u, v, 5), False), shelves)

    def cap(s, pal):
        L = P(int(22 * s) + 2, int(26 * s) + 2)
        cx = L.w / 2
        shape(L, STEM, lambda x, y: abs(x + 0.5 - cx) <= 2.2 * s and y >= L.h * 0.35, lambda x, y: 0.8 - (x - cx + 2) * 0.12)
        shape(L, pal, ellipse_in(cx, L.h * 0.33, 10.5 * s, 6 * s), lit(cx - 2, L.h * 0.3, 10 * s, 6 * s))
        for (dx, dy) in [(-4, -2), (3, -3), (0, 0), (6, 0), (-7, 1)]:
            L.put(cx + dx * s, L.h * 0.33 + dy * s, pal[-1])
        # gills
        for x in range(int(cx - 9 * s), int(cx + 9 * s)):
            if x % 2: L.put(x, L.h * 0.33 + 5 * s, pal[0])
        L.outline((14, 10, 14))
        return L
    for (x, y, s, pal) in [(64, 74, 1.3, CAP_T), (210, 82, 1.5, CAP_T), (128, 128, 0.9, CAP_G), (172, 124, 0.7, CAP_T), (100, 64, 0.6, CAP_G)]:
        c = cap(s, pal); R.stamp(c, x, y)
        R.light(x, y - c.h * 0.65, 34 * s, pal[3], 0.75)
    # spore drift
    rnd = random.Random(7)
    for _ in range(90):
        x, y = int(rnd.gauss(150, 26)), int(rnd.gauss(86, 12))
        if R.cv.get(x, y)[3]: R.cv.put(x, y, mix(R.cv.get(x, y)[:3], (210, 240, 170), 0.55))
    m = sprite("TallowColossus"); R.stamp(m, 90, 112) if m else None
    R.stamp(hero(), 160, 98)
    return R.finish(0.66), dict(
        name="Rot Gardens", tag="Caves gone soft with fungus",
        palette=[SOIL[3], CAP_T[3], CAP_G[3], STEM[2], SOIL[1]],
        look="Spongy plum-brown floor patched with moss and threads of mycelium, shelf fungus stacked up the cave wall, giant "
             "caps glowing teal and acid green. The caps are the room's lights, so a room's colour tells you what grows there.",
        hazard="Spore drifts: clouds that hang in the air and slowly drift. Walking through dazes the hero briefly. A cap "
               "that is hit bursts into a fresh cloud, so a careless swing can blind your own escape.",
        props="Caps (light and burst), puffballs that roll, mycelium mats that slow everything on them.",
        rooms="Round caverns joined by low tunnels, and a hollow trunk room you fight inside.",
        fits="Spore and slime monsters, and the Tallow Grub's kin.")


BOARD = hexs("#1f1610", "#3a2a1d", "#56402b", "#735637", "#8f6c44")
BOOKS = [hexs("#3a1414", "#6a2424", "#8f3a33"), hexs("#11222e", "#1f3d52", "#335f78"), hexs("#2f2810", "#5a4a1c", "#86702d"),
         hexs("#1b2a14", "#2f4a22", "#476b33")]
RUG = hexs("#2a0f12", "#4a1a1f", "#6d2a2d", "#8f4436", "#b37a4a")
INK = hexs("#07080d", "#10131d", "#1c2233", "#2d3550")


def bookcase(w, h):
    L = P(w, h)
    shape(L, BOARD, lambda x, y: True, lambda x, y: 0.55 - (0.15 if x in (0, w - 1) else 0) + (0.2 if y == 0 else 0))
    for sy in range(3, h - 2, 6):
        x = 2
        rnd = random.Random(sy * 13 + w)
        while x < w - 2:
            bw = rnd.randint(1, 2); bh = rnd.randint(3, 5); pal = rnd.choice(BOOKS)
            for xx in range(x, min(w - 2, x + bw)):
                for yy in range(sy + 5 - bh, sy + 5):
                    L.put(xx, yy, pal[2] if yy == sy + 5 - bh else pal[1] if xx == x else pal[0])
            x += bw + (1 if rnd.random() < 0.2 else 0)
        for xx in range(1, w - 1): L.put(xx, sy + 5, BOARD[4])
    L.outline((10, 7, 5))
    return L


@biome
def ledger_vaults():
    R = Room(51)

    def rug(u, v, lum):
        x, y = u + RX0, v + RY0
        if 70 <= u < 150 and 34 <= v < 66:
            border = u in (70, 71, 148, 149) or v in (34, 35, 64, 65)
            pat = ((u - 70) // 4 + (v - 34) // 4) % 3 == 0
            R.cv.put(x, y, RUG[4] if border else quant(RUG, 0.6 if pat else 0.35, x, y)); R.mask[y][x] = 1
            return None
        dx, dy = (u - 30) / 16.0, (v - 80) / 6.0
        if dx * dx + dy * dy < 1:
            R.cv.put(x, y, quant(INK, 0.4 + 0.3 * (1 - dx * dx - dy * dy), x, y)); R.mask[y][x] = 1
            return None
        return lum
    R.floor(BOARD, planks(5), extra=rug, grain=0.25)

    def cases(r, y0):
        for x in range(RX0, RX0 + RW, 20):
            bc = bookcase(20, WALL - 2)
            r.cv.im.alpha_composite(bc.im, (x, y0 + 2)); r.cv.px = r.cv.im.load()
    R.wall(BOARD, lambda u, v: (0.4, False), cases)
    for (x, y) in [(66, 64), (178, 62), (122, 100)]:
        R.stamp(bookcase(36, 24), x, y)
    desk = P(20, 11)
    shape(desk, BOARD, lambda x, y: y < 4 or ((x < 3 or x > 16) and y < 11), lambda x, y: 0.8 if y == 0 else 0.5)
    shape(desk, hexs("#8d8366", "#d8cfae", "#f3ecd3"), lambda x, y: y < 2 and 5 <= x < 13, lambda x, y: 0.8)
    desk.outline((10, 7, 5))
    R.stamp(desk, 198, 106)
    for (x, y) in [(40, 54), (110, 56), (216, 58), (150, 86), (30, 112), (200, 98)]:
        c = P(3, 7)
        shape(c, hexs("#7a6a4f", "#c9b98f", "#efe2bc"), lambda xx, yy: yy >= 2, lambda xx, yy: 0.7 - xx * 0.2)
        c.put(1, 1, (255, 214, 120)); c.put(1, 0, (255, 245, 200))
        R.stamp(c, x, y - 8, shadow=False)
        R.light(x, y - 12, 24, (255, 200, 110), 0.65)
    rnd = random.Random(3)
    for _ in range(14):
        x, y = rnd.randrange(RX0 + 8, RX0 + RW - 8), rnd.randrange(RY0 + 6, RY0 + RH - 6)
        for k in range(3): R.cv.put(x + k, y, (214, 204, 176)); R.cv.put(x + k, y + 1, (168, 156, 128))
    m = sprite("JinxCardKing"); R.stamp(m, 196, 90) if m else None
    R.stamp(hero(), 110, 84)
    return R.finish(0.72), dict(
        name="Ledger Vaults", tag="An archive that never ends",
        palette=[BOARD[3], BOOKS[0][1], BOOKS[1][2], RUG[3], (255, 214, 120), INK[1]],
        look="Walnut boards, bookcases for walls, free-standing shelves that make a maze of the room, floating candles and "
             "loose pages. Dusty and warm, with ink-black pools and a worn red rug as the accents.",
        hazard="Shelves fall: a big monster that charges into a shelf topples it, crushing whatever is behind and opening "
               "a new path. Ink pools hide anything standing in them (a monster's tell disappears).",
        props="Shelves (walls that fall), reading desks (cover), page drifts that rustle when walked through.",
        rooms="Shelf mazes that open up as the fight goes on, and a reading-room arena with a domed ceiling.",
        fits="Jinx's tricksters and gamblers, the Steward, anything that hides.")


VOID = hexs("#08050c", "#140b1f", "#22123a", "#3a1e5c", "#6b3fa0", "#b48ae6", "#efe0ff")
CRYPT = hexs("#24211a", "#3c372b", "#575040", "#736b55", "#8f866b", "#aaa184")


@biome
def the_seam():
    R = Room(61)
    islands = [((0, 0, 70, 44), CRYPT, flagstones((12, 8), seed=1)), ((76, 0, 200, 40), STONE_GREEN, flagstones((14, 8), seed=2)),
               ((0, 50, 96, 96), BOARD, planks(5, seed=4)), ((104, 46, 200, 96), IRON, plates(24, 16, seed=5))]

    def seam(u, v, lum):
        x, y = u + RX0, v + RY0
        for (a, b, c, d), pal, pat in islands:
            rough = int(3 * R.n.value(x * 2, y * 2, 3))
            a, b, c, d = a + rough, b + rough // 2, c - rough, d - rough // 2
            if a + 2 <= u < c - 2 and b + 2 <= v < d - 2:
                l, line = pat(u, v)
                l += (R.n.fbm(x, y) - 0.5) * 0.35 - (0.32 if line else 0)
                if v == b + 2: l += 0.25
                R.cv.put(x, y, quant(pal, clamp(l), x, y)); R.mask[y][x] = 1
                return None
            if a + 2 <= u < c - 2 and d - 2 <= v < d + 3:
                R.cv.put(x, y, quant(pal, 0.12, x, y)); R.mask[y][x] = 1    # the island's broken underside
                return None
        # the void between
        t = 0.25 + 0.35 * R.n.value(x, y, 7) + (0.45 if R.n.value(x * 4, y * 4, 1.3) > 0.95 else 0)
        R.cv.put(x, y, quant(VOID[:6], clamp(t), x, y)); R.mask[y][x] = 1
        return None
    R.floor(CRYPT, lambda u, v: (0.5, False), extra=seam)
    segs = [(CRYPT, flagstones((10, 6), seed=9)), (STONE_GREEN, bricks(10, 5, seed=3)), (BRICK, bricks(8, 4, seed=4)), (BOARD, planks(5, seed=8))]

    def torn(r, y0):
        for i, x0 in enumerate(range(RX0, RX0 + RW, 50)):
            pal, pat = segs[i % len(segs)]
            for y in range(y0 + 2, RY0 - 1):
                for x in range(x0, min(RX0 + RW, x0 + 50)):
                    l, line = pat(x - RX0, y - y0)
                    r.cv.put(x, y, quant(pal, clamp(l - (0.3 if line else 0) - 0.15 * (y - y0) / WALL), x, y))
            for y in range(y0, RY0):
                xx = x0 + int(2 * math.sin(y * 0.9))
                r.cv.put(xx, y, VOID[6]); r.cv.put(xx + 1, y, VOID[4]); r.light(xx, y, 6, (180, 120, 255), 0.25)
    R.wall(CRYPT, lambda u, v: (0.5, False), torn, cap=VOID[5])
    # rift crack across an island and a hanging shard
    x, y = 140, 60
    rnd = random.Random(2)
    for i in range(60):
        R.cv.put(x, y, VOID[6]); R.cv.put(x - 1, y, VOID[4]); R.cv.put(x + 1, y, VOID[4])
        if i % 4 == 0: R.light(x, y, 12, (190, 130, 255), 0.4)
        x += rnd.choice((1, 1, 0)); y += rnd.choice((1, 0, 1, -1))
    shard = P(9, 14)
    shape(shard, VOID[2:], lambda xx, yy: abs(xx - 4) <= 4 - abs(yy - 6) * 0.6, lambda xx, yy: 0.9 - xx * 0.1)
    shard.outline((8, 4, 12))
    R.stamp(shard, 92, 70, shadow=False); R.light(92, 64, 26, (190, 130, 255), 0.7)
    m = sprite("UmbHollowKing"); R.stamp(m, 176, 88) if m else None
    R.stamp(hero(), 60, 76)
    return R.finish(0.7), dict(
        name="The Seam", tag="Chaos's own floor: the other floors, torn and stitched",
        palette=[VOID[2], VOID[4], VOID[6], CRYPT[3], STONE_GREEN[3], IRON[3]],
        look="Islands of the other floors (crypt flags next to iron plate next to old boards) stitched over a violet void lit from below. The "
             "back wall changes material every few steps. The violet seams are the only bright colour.",
        hazard="Shifts: when a room is cleared its islands drift into a new layout before the next wave. Rifts open "
               "between islands, and anything knocked into one comes out of another.",
        props="Fragments of every biome's props, and rift shards that teleport whoever strikes them.",
        rooms="Chaos-only. Arenas of several islands, the floor where tier 4 and 5 monsters live.",
        fits="Everything. The late chaos floors.")


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    out = []
    for fn in BIOMES:
        im, info = fn()
        slug = info["name"].lower().replace(" ", "_")
        im.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST).save(os.path.join(outdir, "biome_%s.png" % slug))
        out.append(info)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/concepts/chaos")
