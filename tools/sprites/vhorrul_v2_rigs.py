"""VHORRUL v2: every Vhorrul monster and effect sheet. This file holds the material renderer
(the same approach as jinx_v2_rigs.py), the shared wax-and-fire parts (candles, flames, drips, smoke, floor pools) and
the build entry point; the monsters are in vhorrul_v2_t1.py, vhorrul_v2_t2.py, vhorrul_v2_t3a.py and vhorrul_v2_t3b.py,
the effects in vhorrul_v2_fx.py.

    python3 vhorrul_v2_rigs.py [outdir] [--only Name,Name]

Writes to art/out/ by default (where every Vhorrul sheet lives). Same manifest format as every other sheet: <id>.png +
<id>.json (cellW, cellH, cols, anims[{name, frames, durations}]) + <id>_preview.png, feet at (cellW // 2, cellH - 2),
facing right. Every sheet is drawn at its final size (no ArtScale entry).

Rules carried over from the Jinx v2 rigs: a material buffer lit by one top-left light and quantised to 3 tones per
material (a 4th on shiny ones), no black ring (bottom edges in the material's darkest tone, right edges in its shadow
tone), stray pixels folded, a front part casts a one-tone shadow, every frame a fresh pose. Flames are emissive: they
keep their drawn tones and never take an outline, so they read as light on the dark crypt floor.
"""
import math, os, sys, json, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from anim import Spr, SprRGB, pack, preview  # noqa: E402
from PIL import Image  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out")


# ================================================================== palette: material ramps (ink, shadow, base, light, hi)
def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


RAMPS = {
    # wax and tallow
    "tallow": ["2e2018", "6c563c", "ac946a", "d6c49a", "f2e6c6"],   # cream tallow (shadows go umber)
    "oldtal": ["1c2018", "464e38", "767e5c", "a0a682", "c8ccaa"],   # grey-green old tallow (the Colossus)
    "bees":   ["2a1408", "683610", "a6601c", "d69838", "f4ca6c"],   # beeswax amber
    "pink":   ["2c1820", "6a4450", "a67882", "d2a6a8", "eed0cc"],   # pale rendered fat (Sow, Grub Mother)
    "grease": ["2a2420", "6a6058", "a89e90", "d8d0c2", "fcf8ee"],   # a greased hide's pale shine
    # cloth, skin, hide
    "soot":   ["100c0c", "241a18", "3a2e28", "56463c", "766456"],   # soot umber
    "ash":    ["181616", "363232", "5c5654", "86807c", "b2aca6"],   # ash grey
    "ashw":   ["34302e", "726c6a", "a8a29e", "d6d0ca", "f6f2ec"],   # ash white (the Seraph)
    "moth":   ["1a1816", "3a3632", "625c54", "8a8278", "b0a89c"],   # moth wing dust
    "robe":   ["0c0e12", "1a2026", "2a343c", "3e4c58", "5c6c7a"],   # the Wraith's dusk robe
    "lthr":   ["160e0c", "33201a", "4e3226", "6c4a34", "8a6646"],   # apron, straps
    "ghoul":  ["181a14", "3a4032", "626c54", "8a9676", "b2bc9a"],   # the Renderer's grave skin
    "flesh":  ["3a1e24", "7a4a44", "b07c62", "d6a882", "eccaa0"],   # the crone's skin
    "rat":    ["1a1210", "3c2a22", "62463a", "8a6650", "aa866a"],   # mangy rat fur
    "cloth":  ["2c2420", "6c5e56", "a89c90", "d4cabe", "f0e8de"],   # the Warden's scorched surcoat
    "violet": ["140a1c", "2c1838", "482c58", "684878", "8c6c9c"],   # the Hag's shawl
    "chitin": ["141212", "322e2c", "585250", "807874", "a8a098"],   # the scorpion's ash plates
    "tick":   ["1c0a08", "461812", "742a1c", "9e4428", "c26a3a"],   # the tick's swollen shell
    "dwood":  ["140c0a", "2a1a14", "42281c", "5e3c28", "7c5638"],   # the reliquary's dark wood
    "wick":   ["0a0808", "1a1412", "2c2420", "3e342e", "524640"],   # wick black
    # metal, glass, bone
    "iron":   ["121216", "2a2a32", "46464e", "6a6a74", "9c9ca6"],
    "steel":  ["22242c", "4e525e", "7e828e", "aeb2bc", "dcdee4"],   # the Warden's burnished plate
    "rust":   ["1e100c", "4a2416", "7a3e22", "a45e34", "c4844c"],
    "gold":   ["2e1a10", "6e4618", "a8782a", "dcb04a", "fbe796"],
    "bronze": ["1e140a", "4a3214", "7a5a26", "a8843c", "d0b060"],
    "votive": ["2a0810", "6a1020", "a8202e", "d84a44", "f48a70"],   # red votive glass
    "glass":  ["1a2a30", "3a5a62", "6a949c", "a8ccd0", "e6f8fa"],
    "bone":   ["3a2e28", "7c6c5c", "b8a68c", "ded0b4", "f8f0dc"],
    # emissive (not shaded, no sel-out)
    "fire":   ["5a1a0a", "b8401a", "f07a24", "ffc04a", "fff0b0"],
    "ember":  ["4a0c0a", "a0200e", "e8501a", "ffa040", "fff0a0"],
    "blue":   ["0c1a4a", "1c3a9a", "3a6ae0", "8ab4ff", "e0f0ff"],   # blue flame cores (the Wyrm)
    "hex":    ["2a0c3a", "5a1a7a", "9a3ac8", "d07af0", "f6d8ff"],   # hex violet flames (the Hag)
    "soul":   ["082a2a", "0e5a5a", "1a9a92", "5ad8c8", "c8fff4"],   # soul teal (the Wraith)
    "spark":  ["6a5a3a", "c8b47a", "fff0b8", "fffae0", "ffffff"],   # spark white (the Scorpion)
    "sigil":  ["5a3a0a", "a86e14", "f0b42a", "ffe070", "fffad0"],   # sigil gold flame
    "magma":  ["4a0806", "96140c", "e0301a", "ff7a3a", "ffd090"],   # magma cracks (the Tick)
    "eye":    ["5a0c0c", "b01a1a", "ff3a2a", "ff8a5a", "ffd0a0"],
    "smoke":  ["2a2630", "4a4652", "6e6a76", "948f9a", "b8b4bc"],
    "white":  ["8a8a90", "c8c8cc", "e8e8ea", "f6f6f6", "ffffff"],
    "heat":   ["3a0c10", "7a1a1e", "c03a30", "f07a5a", "ffc0a0"],   # fever flush
}
RAMPS = {k: [_h(c) for c in v] for k, v in RAMPS.items()}
EMISSIVE = {"fire", "ember", "blue", "hex", "soul", "spark", "sigil", "magma", "eye", "smoke", "white", "heat"}
SHINY = {"gold", "bronze", "iron", "steel", "votive", "glass", "grease", "bone"}
STONE = [_h(c) for c in ("2a2a30", "4c4c54", "6e6e76", "92929a", "b6b6bc")]
LIGHTMATS = ("tallow", "bees", "pink", "grease", "ashw", "cloth", "bone", "flesh", "gold", "white")

LIGHT = (-0.55, -0.68, 0.48)
_ln = math.sqrt(sum(v * v for v in LIGHT)); LIGHT = tuple(v / _ln for v in LIGHT)
T_SHADOW, T_LIGHT, T_HI = 0.12, 0.62, 0.9


def lam(nx, ny, nz):
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


# ================================================================== the material buffer
class Rig:
    """Pixel buffer: (x, y) -> [z, mat, light, part, fixed_tone]. Origin = feet, y up is negative.
    k scales every primitive's coordinates and sizes (a sheet sets Rig.default_k to draw a pose bigger)."""
    default_k = 1.0

    def __init__(self):
        self.k = Rig.default_k
        self.b = {}
        self._part = 0
        self.thin = set()     # parts that never take a sel-out (1-2 px wide things)
        self.zof = {}
        self.hand = set()     # hand-pixelled parts: keep their drawn tones and edges

    def part(self, thin=False, z=0.0):
        self._part += 1
        if thin: self.thin.add(self._part)
        self.zof[self._part] = z
        return self._part

    def put(self, x, y, z, mat, l, part, tone=None):
        x, y = int(math.floor(x + 0.5)), int(math.floor(y + 0.5))
        if callable(mat): mat = mat(x, y)
        if mat is None: return
        cur = self.b.get((x, y))
        if cur is None or z >= cur[0]:
            self.b[(x, y)] = [z, mat, l, part, tone]

    # ---------------------------------------------------------------- lit primitives
    def ell(self, cx, cy, rx, ry, mat, z, bias=0.0, ang=0.0, flat=None, thin=False, clip=None, part=None):
        """Ellipsoid (lit as a sphere). flat=tone fixes the tone. clip(x, y) -> False skips a pixel."""
        p = part or self.part(thin, z)
        k = self.k
        cx, cy, rx, ry = cx * k, cy * k, rx * k, ry * k
        if clip and k != 1.0:
            c0 = clip; clip = lambda x, y: c0(x / k, y / k)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        R = int(max(rx, ry)) + 2
        for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)) + 1):
            for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R)) + 1):
                dx, dy = x - cx, y - cy
                u = dx * ca + dy * sa; v = -dx * sa + dy * ca
                nu, nv = u / max(rx, 0.5), v / max(ry, 0.5)
                d = nu * nu + nv * nv
                if d > 1.0: continue
                if clip and not clip(x, y): continue
                wx, wy = nu * ca - nv * sa, nu * sa + nv * ca
                nz = math.sqrt(max(0.0, 1 - min(1.0, wx * wx + wy * wy)))
                self.put(x, y, z, mat, lam(wx, wy, nz) + bias, p, flat)
        return p

    def tube(self, pts, radii, mat, z, bias=0.0, flat=None, thin=False, part=None, zs=None):
        """Capsule chain lit as a cylinder. zs: optional per-point depth (for limbs that reach forward)."""
        p = part or self.part(thin, z)
        pts = [(x * self.k, y * self.k) for x, y in pts]; radii = [q * self.k for q in radii]
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            r0, r1 = radii[min(i, len(radii) - 1)], radii[min(i + 1, len(radii) - 1)]
            R = max(r0, r1) + 1
            L2 = (x1 - x0) ** 2 + (y1 - y0) ** 2
            for y in range(int(math.floor(min(y0, y1) - R)), int(math.ceil(max(y0, y1) + R)) + 1):
                for x in range(int(math.floor(min(x0, x1) - R)), int(math.ceil(max(x0, x1) + R)) + 1):
                    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / L2))
                    qx, qy = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                    r = r0 + (r1 - r0) * t
                    ox, oy = x - qx, y - qy
                    d = math.hypot(ox, oy)
                    if d > r + 0.2: continue
                    if r < 0.8:
                        l = 0.45
                    else:
                        nx, ny = ox / (r + 0.2), oy / (r + 0.2)
                        l = lam(nx, ny, math.sqrt(max(0.0, 1 - nx * nx - ny * ny)))
                    zz = z if zs is None else zs[i] + (zs[i + 1] - zs[i]) * t
                    self.put(x, y, zz, mat, l + bias, p, flat)
        return p

    def poly(self, pts, mat, z, bias=0.0, normal=(0.0, 0.0, 1.0), curve=0.0, flat=None, thin=False, part=None):
        """Filled polygon. normal: its facing (lit flat); curve: >0 bends it like a cylinder across x."""
        p = part or self.part(thin, z)
        pts = [(x * self.k, y * self.k) for x, y in pts]
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
        x0, x1 = min(xs), max(xs)
        mid, half = (x0 + x1) / 2.0, max(0.5, (x1 - x0) / 2.0)
        for (x, y) in poly_px(pts):
            nx, ny, nz = normal
            if curve:
                u = max(-1.0, min(1.0, (x - mid) / half)) * curve
                nx, nz = nx + u, nz * math.sqrt(max(0.05, 1 - u * u))
            n = math.sqrt(nx * nx + ny * ny + nz * nz)
            self.put(x, y, z, mat, lam(nx / n, ny / n, nz / n) + bias, p, flat)
        return p

    def line(self, x0, y0, x1, y1, mat, z, tone=2, part=None):
        p = part or self.part(True, z)
        k = self.k; x0, y0, x1, y1 = x0 * k, y0 * k, x1 * k, y1 * k
        for (x, y) in line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
            self.put(x, y, z, mat, 0.5, p, tone)
        return p

    def polyline(self, pts, mat, z, tone=2, tones=None, part=None):
        p = part or self.part(True, z)
        pts = [(x * self.k, y * self.k) for x, y in pts]
        for i in range(len(pts) - 1):
            t = tones[i] if tones else tone
            for (x, y) in line_px(int(round(pts[i][0])), int(round(pts[i][1])), int(round(pts[i + 1][0])), int(round(pts[i + 1][1]))):
                self.put(x, y, z, mat, 0.5, p, t)
        return p

    def dot(self, x, y, mat, tone, z, part=None):
        p = part or self.part(True, z)
        x, y = x * self.k, y * self.k
        self.put(x, y, z, mat, 0.5, p, tone)
        return p

    def dots(self, pts, mat, tone, z):
        p = self.part(True, z)
        pts = [(x * self.k, y * self.k) for x, y in pts]
        for (x, y) in pts: self.put(x, y, z, mat, 0.5, p, tone)
        return p

    def stamp(self, grid, x, y, z, legend, pivot=(0, 0), flip=False, part=None, lit=False):
        """Hand-pixelled part: grid rows of chars, legend char -> (mat, tone). (x, y) = where pivot lands.
        lit=True lets the tone be re-derived by the resolver (normally stamps keep their drawn tones)."""
        p = part or self.part(False, z)
        if not lit: self.hand.add(p)
        rows = [r for r in grid.strip("\n").split("\n")]
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in ". " or ch not in legend: continue
                m, t = legend[ch]
                dx = i - pivot[0]
                self.put(x + (-dx if flip else dx), y + j - pivot[1], z, m, 0.5, p, None if lit else t)
        return p

    def merge(self, other, dx=0, dy=0, dz=0.0):
        base = self._part
        for k, v in other.b.items():
            x, y = k[0] + dx, k[1] + dy
            self.put(x, y, v[0] + dz, v[1], v[2], v[3] + base, v[4])
        for p in other.thin: self.thin.add(p + base)
        self._part += other._part + 1

    # ---------------------------------------------------------------- resolve to pixels
    def resolve(self, selout=True, cast=True, contour=True, clean=True, floor=True):
        tone, mat, part, z = {}, {}, {}, {}
        for k, (zz, m, l, p, t) in self.b.items():
            if floor and k[1] > 0: continue
            mat[k] = m; part[k] = p; z[k] = zz
            if t is not None:
                tone[k] = t
            elif m in EMISSIVE:
                tone[k] = 2 if l < 0.7 else 3
            else:
                tone[k] = 1 if l < T_SHADOW else 2 if l < T_LIGHT else (4 if (m in SHINY and l > T_HI) else 3)
        fixed = {k for k, v in self.b.items() if v[4] is not None}
        N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
        if clean:
            for _ in range(2):
                ch = {}
                for k, t in tone.items():
                    if k in fixed: continue
                    same = [tone[(k[0] + dx, k[1] + dy)] for dx, dy in N4
                            if (k[0] + dx, k[1] + dy) in tone and mat.get((k[0] + dx, k[1] + dy)) == mat[k]]
                    if len(same) >= 3 and t not in same:
                        ch[k] = max(set(same), key=same.count)
                    elif len(same) == 4 and same.count(t) == 1:
                        # a 2-px sliver poking into a flat area
                        o = [s for s in same if s != t]
                        if len(set(o)) == 1: ch[k] = o[0]
                tone.update(ch)
        out = dict(tone)
        if cast:
            for k in tone:
                if mat[k] in EMISSIVE or k in fixed or part[k] in self.hand: continue
                for dx, dy in ((-1, 0), (0, -1), (-1, -1)):
                    q = (k[0] + dx, k[1] + dy)
                    if q in part and part[q] != part[k] and z[q] > z[k] + 0.01 and mat[q] not in EMISSIVE \
                            and part[q] not in self.thin:
                        out[k] = max(1, min(out[k], tone[k] - 1)); break
        if contour:
            for k in tone:
                if mat[k] in EMISSIVE or part[k] in self.hand: continue
                for dx, dy in N4:
                    q = (k[0] + dx, k[1] + dy)
                    if q in part and part[q] != part[k] and z[q] > z[k] + 0.01 and mat[q] == mat[k] \
                            and part[q] not in self.thin:
                        out[k] = min(out[k], 1 if tone[k] > 1 else 0); break
        if selout:
            for k in tone:
                m = mat[k]
                if m in EMISSIVE or part[k] in self.thin or part[k] in self.hand: continue
                x, y = k
                open_r = (x + 1, y) not in tone
                open_d = (x, y + 1) not in tone and not (floor and y == 0)
                if open_r or open_d:
                    # only where the part is at least 2 px thick across that edge. Bottom edges take the ink tone (they
                    # sit the shape on the floor); right edges only drop to the shadow tone, like the vanilla art.
                    thick = ((x - 1, y) in tone) if open_r else ((x, y - 1) in tone)
                    if thick: out[k] = 0 if open_d else min(out[k], 1)
                elif (x + 1, y + 1) not in tone and (x + 1, y) in tone and (x, y + 1) in tone:
                    out[k] = min(out[k], 1)
        px = {}
        for k, t in out.items():
            px[k] = RAMPS[mat[k]][max(0, min(4, t))]
        s = SprRGB(px)
        s.tones = {k: (mat[k], out[k]) for k in out}
        return s


def poly_px(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    out = []
    for y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        for x in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]; xj, yj = pts[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                    inside = not inside
                j = i
            if inside: out.append((x, y))
    return out


def line_px(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts


# ================================================================== sprite helpers
def stone(s):
    """Statue: tones map onto the stone ramp (clusters survive); light materials sit one step up."""
    px = {}
    for k, (m, t) in s.tones.items():
        lift = 1 if m in LIGHTMATS else 0
        if m in EMISSIVE: t = 2
        px[k] = STONE[max(0, min(4, t + lift if t > 0 else 0))]
    out = SprRGB(px); out.tones = {k: ("stone", 0) for k in px}
    return out


def flip_x(s):
    out = SprRGB({(-x, y): c for (x, y), c in s.px.items()})
    out.tones = {(-x, y): v for (x, y), v in getattr(s, "tones", {}).items()}
    return out


def Xf(ang, pivot):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)

    def f(x, y):
        dx, dy = x - pivot[0], y - pivot[1]
        return pivot[0] + dx * ca - dy * sa, pivot[1] + dx * sa + dy * ca
    return f


def chain(x, y, segs):
    pts = [(x, y)]
    for ln, ang in segs:
        a = math.radians(ang); x += ln * math.cos(a); y += ln * math.sin(a); pts.append((x, y))
    return pts


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    """2-bone IK: returns the elbow/knee point. bend=+1 bends one way, -1 the other."""
    dx, dy = tx - sx, ty - sy
    d = max(0.01, min(l1 + l2 - 0.01, math.hypot(dx, dy)))
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1.0, min(1.0, c)))
    return sx + l1 * math.cos(a - bend * b), sy + l1 * math.sin(a - bend * b)


def lerp(a, b, t):
    return a + (b - a) * t



# ================================================================== wax and fire parts
FLICK = (0.0, 0.7, -0.4, 0.4, -0.7, 0.2)


def flame(r, x, y, h=4.0, ph=0, mat="fire", z=5.0, lean=0.0, wide=1.0, core=True):
    """A candle flame whose root sits on (x, y), h px tall: a white-hot core near the root (tone 4), a bright body
    (tone 3) and a darker skin (tone 2). ph (0-5) bends the tip for flicker; lean tilts the whole tongue."""
    p = r.part(True, z)
    x, y, h, lean = x * r.k, y * r.k, h * r.k, lean * r.k
    n = max(1, int(round(h)))
    fl = FLICK[ph % len(FLICK)] * min(1.5, h / 4.0)
    for j in range(n):
        t = (j + 0.5) / n
        half = wide * 1.3 * math.sin(math.pi * min(1.0, 0.25 + t)) ** 0.8 * (1.05 - 0.8 * t) * max(0.6, (h / 4.0) ** 0.6)
        cx = x + lean * t + fl * t * t
        for xx in range(int(math.floor(cx - half + 0.5)), int(math.floor(cx + half + 0.5)) + 1):
            d = abs(xx - cx) / max(0.6, half + 0.4)
            tone = 4 if (core and t < 0.5 and d < 0.45) else (3 if d < 0.7 and t < 0.8 else 2)
            r.put(xx, y - j, z, mat, 0.5, p, tone)
    r.put(x + lean + fl, y - n, z, mat, 0.5, p, 2 if h < 5 else 3)
    if h >= 6:
        r.put(x + lean + fl * 1.3, y - n - 1, z, mat, 0.5, p, 2)
    return p


def candle(r, x, y, h=4.0, w=2.0, z=0.0, lit=True, ph=0, mat="tallow", fl="fire", flh=None, drip=1, lean=0.0, out=False):
    """A candle stub standing on (x, y): a lit cylinder w px wide and h tall, a dark wick, wax drips down its lit side
    and (lit) a flame. out=True shows a guttered wick with a curl of smoke instead."""
    x0, x1 = x - w / 2.0, x + w / 2.0
    top = y - h
    r.poly([(x0, y), (x1, y), (x1 + lean, top), (x0 + lean, top)], mat, z, curve=0.8, normal=(-0.1, -0.1, 1.0))
    r.line(x0 + lean, top, x1 + lean - 1, top, mat, z + 0.01, tone=4 if mat in ("tallow", "bees") else 3)
    for k in range(drip):
        dx = x0 + lean * 0.8 + (0.0 if k == 0 else w - 1.0)
        r.line(dx, top + 1, dx, top + 1 + min(h - 1, 1.5 + k), mat, z + 0.02, tone=3 if k == 0 else 2)
    wx = x + lean - 0.5 + (0.5 if w >= 3 else 0.0)
    r.dot(wx, top - 1, "wick", 1, z + 0.03)
    if lit and not out:
        flame(r, wx, top - 1.5, flh if flh is not None else max(2.0, min(5.0, h * 0.9)), ph, fl, z + 0.05)
    elif out:
        smoke_curl(r, wx, top - 2, ph, z + 0.05, k=0.6)


def smoke_curl(r, x, y, ph=0, z=6.0, k=1.0):
    """A thin curl of smoke rising from (x, y); ph (0-5) drifts it."""
    p = r.part(True, z)
    x, y = x * r.k, y * r.k
    for i in range(int(3 + 3 * k)):
        a = (ph * 0.9 + i * 1.1)
        r.put(x + math.sin(a) * (0.6 + 0.35 * i), y - i * 1.1, z, "smoke", 0.5, p, 3 if i < 2 else 2 if i < 4 else 1)


def drip(r, x, y, ln, mat="tallow", z=0.0, bulb=True):
    """A run of wax hanging from (x, y), ln px long, with a bead at the end."""
    p = r.part(True, z)
    x, y, ln = x * r.k, y * r.k, ln * r.k
    for j in range(int(ln)):
        r.put(x, y + j, z, mat, 0.5, p, 3 if j == 0 else 2)
    if bulb:
        r.put(x, y + ln, z, mat, 0.5, p, 2)
        r.put(x + 1, y + ln - 1, z, mat, 0.5, p, 1)
    return p


def floor_pool(r, cx, cy, rx, ry, mat="tallow", z=-5.0, rim=True, tone=2, edge=1):
    """A flat pool on the floor centred (cx, cy): body tone `tone`, a lit rim up-left and a dark lip down-right."""
    p = r.part(False, z)
    cx, cy, rx, ry = cx * r.k, cy * r.k, rx * r.k, ry * r.k
    for y in range(int(math.floor(cy - ry - 1)), int(math.ceil(cy + ry + 1)) + 1):
        for x in range(int(math.floor(cx - rx - 1)), int(math.ceil(cx + rx + 1)) + 1):
            u, v = (x - cx) / max(rx, 0.5), (y - cy) / max(ry, 0.5)
            d = u * u + v * v
            if d > 1.0: continue
            t = tone
            if rim and d > 0.55:
                t = min(4, tone + 1) if (u + v * 1.6) < -0.3 else (edge if (u + v * 1.6) > 0.5 else tone)
            r.put(x, y, z, mat, 0.5, p, t)
    return p


def ember_dots(r, pts, z=7.0, mat="ember"):
    p = r.part(True, z)
    for (x, y, t) in pts:
        r.put(x * r.k, y * r.k, z, mat, 0.5, p, t)


def glow_ring(r, cx, cy, R, mat, z, tone=3, ry=None, step=4.0):
    """A thin ring of emissive pixels (rx R, ry ry), for halos and auras."""
    ry = R * 0.45 if ry is None else ry
    cx, cy, R, ry = cx * r.k, cy * r.k, R * r.k, ry * r.k
    p = r.part(True, z)
    n = max(8, int(2 * math.pi * R / 1.2))
    for i in range(n):
        a = 2 * math.pi * i / n
        r.put(cx + R * math.cos(a), cy + ry * math.sin(a), z, mat, 0.5, p, tone)
    return p


def scaled(k):
    """Decorator for a sheet function: draw every frame of the sheet k times bigger."""
    def wrap(fn):
        def run(outdir):
            old = Rig.default_k
            Rig.default_k = k
            try:
                return fn(outdir)
            finally:
                Rig.default_k = old
        run.__name__ = fn.__name__
        return run
    return wrap


# ================================================================== sheet assembly
BUILT = {}


def sheet(name, anims, outdir, scale=6, pad=2, min_w=0, min_h=0):
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf)
    hw = max(-x0, x1 + 1) + pad
    cw = max(min_w, 2 * hw)
    ch = max(min_h, -y0 + 1 + pad + 2)
    feet = (cw // 2, ch - 2)
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-20s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return img, man


def fx_sheet(name, anims, outdir, cell, origin, scale=6):
    """An effect sheet with a fixed cell and origin (the spawn point, listed in TIMING.md)."""
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-20s cell %dx%d origin %s  %s" % (name, cell[0], cell[1], origin, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return img, man


def tail_anims(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [stone(idle0)], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


# ================================================================== TIMING.md
SYNC, NOTES = {}, {}


def write_timing(outdir):
    L = ["# Vhorrul: sprite timing", "",
         "Generated by `tools/sprites/vhorrul_v2_rigs.py` (and the vhorrul_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet, x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). Effect sheets: origin = the spawn point.",
         "Every sheet is at final size (no ArtScale).", "",
         "| Sheet | Cell (w x h) | Feet / origin | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in BUILT.items():
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox() or (0, 0, 0, 0)
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], bb[2] - bb[0], bb[3] - bb[1],
                                                               ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Sync frames", "", "| Sheet | Anim | Frames | Event | Frame | Time (s) | Length (s) |", "|---|---|---|---|---|---|---|"]
    for n, anims in SYNC.items():
        if n not in BUILT: continue
        dd = {a: d for a, k, d in BUILT[n]["anims"]}
        for a, evs in anims.items():
            d = dd[a]
            for ev, fi in evs:
                L.append("| %s | %s | %d | %s | %d | %.2f | %.2f |" % (n, a, len(d), ev, fi, sum(d[:fi]), sum(d)))
    L += ["", "## Durations", ""]
    for n, b in BUILT.items():
        for a, k, d in b["anims"]:
            L.append("- %s %s: %s" % (n, a, ", ".join("%.2f" % x for x in d)))
    L += ["", "## Notes", ""] + ["- **%s**: %s" % kv for kv in NOTES.items()]
    L += ["- Death plays once and ends on the corpse; Dead is that corpse frame. Statue = the Idle frame mapped tone-for-tone",
          "  onto the stone ramp. Every attack has at least two wind-up frames before its first event."]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


# ================================================================== build
MODULES = ("vhorrul_v2_t1", "vhorrul_v2_t2", "vhorrul_v2_t3a", "vhorrul_v2_t3b", "vhorrul_v2_fx")


def all_jobs():
    import importlib
    jobs = []
    for mod in MODULES:
        try:
            m = importlib.import_module(mod)
        except ImportError as e:
            if mod not in str(e): raise
            continue
        jobs += m.JOBS
        SYNC.update(getattr(m, "SYNC", {}))
        NOTES.update(getattr(m, "NOTES", {}))
    return jobs


def main():
    argv = sys.argv[1:]
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = set(argv[i + 1].split(","))
        argv = argv[:i] + argv[i + 2:]
    outdir = argv[0] if argv else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    for name, fn in all_jobs():
        if only and name not in only: continue
        fn(outdir)
    if not only:
        write_timing(outdir)


if __name__ == "__main__":
    sys.modules["vhorrul_v2_rigs"] = sys.modules[__name__]   # the tier modules import this one by name: share its state
    main()
