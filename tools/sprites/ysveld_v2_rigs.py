"""YSVELD v2: every Ysveld monster and effect sheet, drawn the Jinx v2 way (a material buffer lit
from the top left, 3 tones per material, a selective outline, posed frames). This file holds the renderer, the Ysveld
ramps, the shared body builders (spider, moth, robe, plate, rime) and the build entry point; the monsters are in
ysveld_v2_t1.py, ysveld_v2_t2.py, ysveld_v2_t3a.py and ysveld_v2_t3b.py, the effects in ysveld_v2_fx.py and the
portraits in ysveld_v2_idol.py.

    python3 ysveld_v2_rigs.py [outdir] [--only Name,Name]

Writes to <repo>/art/out_ysveld/ by default (the repo found from this file's own path). Same manifest format as every
other sheet: <id>.png + <id>.json (cellW, cellH, cols, anims[{name, frames, durations}]) + <id>_preview.png, feet at
(cellW // 2, cellH - 2), facing right.
"""
import math, os, sys, random
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from anim import SprRGB, pack, preview  # noqa: E402
from PIL import Image  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = str(REPO / "art" / "out_ysveld")


# ================================================================== palette: material ramps (ink, shadow, base, light, hi)
def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


RAMPS = {
    # frost and ice (shadows go violet-blue, lights go cyan-white)
    "ice":   ["0e1a46", "244a8a", "4a80c4", "8cc4f0", "e4f8ff"],   # glacier ice
    "frost": ["1c2250", "3a4c8e", "7890c6", "b4cbea", "f2f8ff"],   # packed snow / hoarfrost
    "glass": ["14284e", "2e5a88", "5e98c0", "a8daf0", "ffffff"],   # clear ice glass
    "crys":  ["26164a", "48307e", "7454b0", "a486da", "dcc8ff"],   # crystal violet
    "silk":  ["1a1838", "3c3a6a", "6c6aa0", "a4a2cc", "e0def2"],   # silk grey
    "web":   ["262e60", "56689e", "9cb2dc", "d6e4f6", "ffffff"],   # fresh silk white
    # bodies
    "chit":  ["10122e", "222a56", "3a4a80", "6a80b4", "b4c8e8"],   # frost spider chitin (blue-grey, readable mid)
    "fur":   ["1a2048", "36457e", "60739e", "93a8cc", "dce8f8"],   # shaggy hoarfrost fur
    "shell": ["0e1634", "1e3462", "36588e", "6a90c4", "c0d8ec"],   # ice crab shell
    "skin":  ["3a2a48", "7a6a92", "b4a8cc", "dcd2ec", "f8f2fa"],   # pale frost skin
    "robe":  ["10122c", "262e58", "424e82", "6e80b0", "a8b8d8"],   # grey-blue robe
    "veil":  ["2a3060", "5a6aa4", "9cb0dc", "d4e2f6", "ffffff"],   # bridal lace
    "black": ["0c0a12", "1c1826", "322c42", "4c4462", "6c6484"],   # widowed veil
    "steel": ["0e1230", "22305e", "3e5690", "6a8cc4", "b8d0f0"],   # rime-crusted plate
    "rock":  ["16122a", "2e2846", "4e4668", "786e90", "a89cbc"],   # geode rind
    "wood":  ["1e1612", "4a3424", "705038", "967050", "b89068"],   # hermit's staff, loom frame
    "red":   ["3a0a16", "7a1628", "b42636", "e04a4a", "ff8c7c"],   # widow red (the one warm note)
    "silver": ["2a2c3a", "5c6072", "9298aa", "c6ccda", "f4f6ff"],  # spool silver
    "gold":  ["2e1a10", "6e4618", "a8782a", "dcb04a", "fbe796"],   # the idol
    "goldh": ["3a2c3c", "6a6a84", "9aa6c0", "c8d6ea", "f0f8ff"],   # silver-blue hollows of the idol
    # emissive (not shaded, no sel-out)
    "eye":   ["1a3a6a", "2e6ab0", "5aa8ff", "a8dcff", "ffffff"],   # ice-blue eye glow
    "rglow": ["4a0a14", "a01828", "ff3a3a", "ff8a7a", "ffd8d0"],   # hourglass red glow
    "vglow": ["2a1a5a", "5a3aa8", "9a6ae0", "c8a8f4", "f0e4ff"],   # crystal violet glow
    "aurg":  ["0a3a2a", "1a7a52", "3ad08a", "8af0b8", "e0fff0"],   # aurora green
    "aurp":  ["4a1a3a", "9a2a72", "e05aa8", "f8a0d0", "fff0f8"],   # aurora pink
    "cyan":  ["0a3a4a", "1a7a94", "3ac8e0", "9af0ff", "ffffff"],   # glass scythe edges
    "snow":  ["6a7894", "a0b0c8", "d0dcec", "eef4fa", "ffffff"],   # flying snow, frost breath
    "white": ["8a8a90", "c8c8cc", "e8e8ea", "f6f6f6", "ffffff"],
    "shade": ["0e1018", "161a26", "1e2434", "262e40", "2e384c"],   # contact shadows on the floor
}
RAMPS = {k: [_h(c) for c in v] for k, v in RAMPS.items()}
EMISSIVE = {"eye", "rglow", "vglow", "aurg", "aurp", "cyan", "snow", "white", "shade"}
SHINY = {"ice", "glass", "crys", "steel", "red", "silver", "gold"}
STONE = [_h(c) for c in ("2a2a30", "4c4c54", "6e6e76", "92929a", "b6b6bc")]
LIGHT_MATS = ("frost", "web", "veil", "skin", "fur", "white", "snow", "glass", "silk")

LIGHT = (-0.55, -0.68, 0.48)
_ln = math.sqrt(sum(v * v for v in LIGHT)); LIGHT = tuple(v / _ln for v in LIGHT)
T_SHADOW, T_LIGHT, T_HI = 0.2, 0.66, 0.88
OUTLINE = (14, 14, 40)      # the 1 px navy line round every body's outside silhouette


def lam(nx, ny, nz):
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


# ================================================================== the material buffer
class Rig:
    """Pixel buffer: (x, y) -> [z, mat, light, part, fixed_tone]. Origin = feet, y up is negative.
    SCALE: a per-sheet fit factor the build sets before each job (multiplies k)."""
    SCALE = 1.0

    def __init__(self, k=1.0):
        self.b = {}
        self.k = k * Rig.SCALE           # drawing scale: every coordinate and radius is multiplied by it (stamps keep their pixels)
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
        k = self.k; cx, cy, rx, ry = cx * k, cy * k, rx * k, ry * k
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
        k = self.k; pts = [(x * k, y * k) for x, y in pts]; radii = [v * k for v in radii]
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
        xs = [q[0] for q in pts]
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
        k = self.k
        for (x, y) in line_px(int(round(x0 * k)), int(round(y0 * k)), int(round(x1 * k)), int(round(y1 * k))):
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
        self.put(x * self.k, y * self.k, z, mat, 0.5, p, tone)
        return p

    def dots(self, pts, mat, tone, z):
        p = self.part(True, z)
        for (x, y) in pts: self.put(x * self.k, y * self.k, z, mat, 0.5, p, tone)
        return p

    def stamp(self, grid, x, y, z, legend, pivot=(0, 0), flip=False, part=None, lit=False):
        """Hand-pixelled part: grid rows of chars, legend char -> (mat, tone). (x, y) = where pivot lands."""
        p = part or self.part(False, z)
        if not lit: self.hand.add(p)
        x, y = x * self.k, y * self.k
        rows = [r for r in grid.strip("\n").split("\n")]
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in ". " or ch not in legend: continue
                m, t = legend[ch]
                dx = i - pivot[0]
                self.put(x + (-dx if flip else dx), y + j - pivot[1], z, m, 0.5, p, None if lit else t)
        return p

    # ---------------------------------------------------------------- resolve to pixels
    def resolve(self, selout=True, cast=True, contour=True, clean=True, floor=True, outline=True):
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
                    # bottom edges take the ink tone (they sit the shape on the floor); right edges only drop to the
                    # shadow tone, like the vanilla art; only where the part is at least 2 px thick across that edge
                    thick = ((x - 1, y) in tone) if open_r else ((x, y - 1) in tone)
                    if thick: out[k] = 0 if open_d else min(out[k], 1)
                elif (x + 1, y + 1) not in tone and (x + 1, y) in tone and (x, y + 1) in tone:
                    out[k] = min(out[k], 1)
        px = {}
        for k, t in out.items():
            px[k] = RAMPS[mat[k]][max(0, min(4, t))]
        tones = {k: (mat[k], out[k]) for k in out}
        if outline:
            # the navy line round the outside: every empty pixel touching a solid (non-glowing) one
            for (x, y) in list(out):
                if mat[(x, y)] in EMISSIVE: continue
                for dx, dy in N4:
                    q = (x + dx, y + dy)
                    if q in px or (floor and q[1] > 0): continue
                    px[q] = OUTLINE; tones[q] = ("line", 0)
        s = SprRGB(px)
        s.tones = tones
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


# ================================================================== small helpers
def stone(s):
    """Statue: tones map onto the stone ramp (clusters survive); light materials sit one step up."""
    px = {}
    for k, (m, t) in s.tones.items():
        lift = 1 if m in LIGHT_MATS else 0
        if m in EMISSIVE: t = 2
        if m == "line": t, lift = 0, 0
        px[k] = STONE[max(0, min(4, t + lift if t > 0 else 0))]
    out = SprRGB(px); out.tones = {k: ("stone", 0) for k in px}
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


def knee_up(sx, sy, tx, ty, l1, l2):
    """The IK solution whose joint sits higher (spider and crab legs)."""
    a = ik(sx, sy, tx, ty, l1, l2, 1); b = ik(sx, sy, tx, ty, l1, l2, -1)
    return a if a[1] < b[1] else b


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pt(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


def sparkle(r, x, y, k=1, mat="white", z=9.0):
    """A frost glint: k=1 a 4-point star, k=2 a smaller one, k=3 a single pixel."""
    r.dot(x, y, mat, 4, z)
    if k <= 2:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r.dot(x + dx, y + dy, "snow" if mat == "white" else mat, 3 if k == 1 else 2, z - 0.01)
    if k == 1:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            r.dot(x + dx, y + dy, "snow" if mat == "white" else mat, 1, z - 0.02)


def arc_smear(r, cx, cy, R, a0, a1, mat="snow", width=2, z=4.8):
    """Motion smear along an arc (deg a0 -> a1, the leading end at a1): brightest at the lead, thinning behind it."""
    n = max(3, int(abs(a1 - a0) / 6))
    for i in range(n + 1):
        t = i / n
        a = math.radians(lerp(a0, a1, t))
        tone = 1 if t < 0.35 else 2 if t < 0.75 else 3
        for w in range(width if t > 0.3 else 1):
            rr = R - w
            r.dot(cx + rr * math.cos(a), cy + rr * math.sin(a), mat, max(1, tone - w), z)


def snow_puff(r, x, y, k, w=1.0, z=5.0):
    """Kicked-up snow at the feet: k = 0 (burst) .. 2 (thinning)."""
    for side in (-1, 1):
        for i in range(3 - k):
            px = x + side * (2 + i * 2 + k * 1.5) * w
            py = y - (i % 2) - (1 if k else 0)
            r.ell(px, py, 1.3 - 0.3 * k, 0.9, "snow", 5.0 + i * 0.01, flat=3 if i == 0 and k == 0 else 2)


def flakes(r, pts, z=8.0):
    """Loose snow flakes: (x, y, tone)."""
    for (x, y, t) in pts: r.dot(x, y, "snow", t, z)


def rime_fringe(r, pts, z, mat="frost", step=2, seed=1, length=1.6):
    """Hoarfrost: little downward icicle teeth along a list of edge points."""
    rnd = random.Random(seed)
    for i, (x, y) in enumerate(pts[::step]):
        L = 1 + int(rnd.random() * length + 0.5)
        for j in range(L):
            r.dot(x, y + j, mat, 4 if j == 0 else 3 if j < L - 1 else 2, z)


def crystal(r, x, y, h, w, mat="crys", z=2.0, ang=0.0, bias=0.15):
    """A crystal prism standing on (x, y): a pointed hexagonal shaft lit as two faces (left lit, right shaded)."""
    T = Xf(ang, (x, y))
    hw = w / 2.0
    tip = T(x, y - h)
    left = [T(x - hw, y), T(x - hw, y - h * 0.72), tip, T(x, y - h * 0.68), T(x, y)]
    right = [T(x, y), T(x, y - h * 0.68), tip, T(x + hw, y - h * 0.72), T(x + hw, y)]
    r.poly(left, mat, z, bias=bias, normal=(-0.7, -0.4, 0.6))
    r.poly(right, mat, z - 0.001, bias=bias, normal=(0.8, -0.1, 0.5))
    return tip


# ================================================================== shared bodies
def leg(r, hip, foot, l1, l2, mat, z, rad=(1.0, 0.8, 0.5), bias=0.0, tip_mat=None, knee=None, thin=False):
    """A jointed leg, knee up (arachnid). Returns the knee. tip_mat: a lit claw pixel at the foot."""
    k = knee or knee_up(hip[0], hip[1], foot[0], foot[1], l1, l2)
    r.tube([hip, k, foot], list(rad), mat, z, bias=bias, thin=thin)
    if tip_mat: r.dot(foot[0], foot[1], tip_mat, 3, z + 0.01)
    return k


def spider(r, cx=0.0, cy=-4.0, s=1.0, phase=0.0, stride=1.0, lean=0.0, abd=(5.0, 4.0), abd_at=(-5.5, -1.5),
           ceph=(3.2, 2.4), legs=(5.0, 5.5), spread=(7.0, 3.0, -3.5, -7.5), mats=("chit", "chit", "chit"),
           eyes=((2.6, -1.0),), eye_mat="eye", fang=0.0, fang_mat="frost", front=None, z=0.0, abd_mat=None,
           hairs=None, lift=None, leg_rad=(0.9, 0.7, 0.45), knee_lift=0.0, knee_h=(4.2, 3.6, 3.4, 4.0), near_z=0.5):
    """A frost spider seen from the side, facing right. (cx, cy) = the cephalothorax centre; everything scales by s.
    phase 0..1 walks the tetrapod gait (legs 0+2 near and 1+3 far step together). front: an override for the two front
    legs, ((foot_near), (foot_far)) relative to the hips (rearing, impaling). lift: per-leg extra foot lift."""
    body, legm, abdm = mats
    abdm = abd_mat or abdm
    T = Xf(lean, (cx, cy + 2 * s))
    hips = [T(cx + (1.6 - i * 1.1) * s, cy + 0.6 * s) for i in range(4)]
    L1, L2 = legs[0] * s, legs[1] * s
    for side, zz, bias in ((1, z - 3.0, -0.35), (0, z + near_z, 0.0)):         # far side first, darker
        for i in range(4):
            grp = (i + side) % 2
            ph = (phase + 0.5 * grp) % 1.0
            sw = math.sin(ph * math.tau) * stride * 2.0 * s
            up = max(0.0, math.sin(ph * math.tau)) * stride * 1.5 * s
            fx = cx + spread[i] * s + sw + (1.0 if side else 0.0) * s * (0.6 if i < 2 else -0.6)
            fy = 0.0 - up - (lift[i] if lift else 0.0)
            hx, hy = hips[i]
            if front and i == 0:
                fx, fy = hx + front[side][0] * s, hy + front[side][1] * s
            if front and i == 1 and len(front) > 2:
                fx, fy = hx + front[2 + side][0] * s, hy + front[2 + side][1] * s
            if knee_h:
                # an explicit knee: partway out toward the foot and well above the hip, so the legs arch like a spider's
                kh = knee_h[i] * s * (1.0 if side == 0 else 0.85) + knee_lift * s
                kn = (lerp(hx, fx, 0.42), min(hy, fy) - kh)
            else:
                kn = knee_up(hx, hy, fx, fy, L1, L2)
                kn = (kn[0], kn[1] - knee_lift * s)
            leg(r, (hx, hy), (fx, fy), L1, L2, legm, zz + i * 0.01, rad=tuple(v * max(0.8, s) for v in leg_rad), bias=bias, knee=kn)
            # the knee joint catches the frost
            r.dot(kn[0], kn[1] - 0.5, "frost" if side == 0 else "ice", 4 if side == 0 else 2, zz + i * 0.01 + 0.02)
            if hairs:
                hairs(r, (hx, hy), kn, (fx, fy), zz + i * 0.01 + 0.005, side)
    ax, ay = T(cx + abd_at[0] * s, cy + abd_at[1] * s)
    r.ell(ax, ay, abd[0] * s, abd[1] * s, abdm, z, bias=0.05)
    hx, hy = T(cx, cy)
    r.ell(hx, hy, ceph[0] * s, ceph[1] * s, body, z + 1.0, bias=0.1)
    for n, (ex, ey) in enumerate(eyes):
        x, y = T(cx + ex * s, cy + ey * s)
        r.dot(x, y, eye_mat, 4 if n == 0 else 3, z + 1.2)
        if n == 0 and s >= 1.0: r.dot(x - 0.6 * s, y, eye_mat, 2, z + 1.19)
    # chelicerae and fangs, curling down (fang > 0 opens them)
    fx0, fy0 = T(cx + ceph[0] * s * 0.8, cy + ceph[1] * s * 0.4)
    r.tube([(fx0, fy0), (fx0 + 1.2 * s + fang * 0.6, fy0 + 1.3 * s - fang * 0.6)], [0.9 * s, 0.6 * s], body, z + 1.1)
    r.line(fx0 + 1.2 * s + fang * 0.6, fy0 + 1.3 * s - fang * 0.6, fx0 + 1.2 * s + fang * 1.1, fy0 + 2.3 * s,
           fang_mat, z + 1.15, tone=4)
    return (ax, ay), (hx, hy)


def wing(r, root, ang, length, width, mat, z, bias=0.0, spots=None, vein=None, scallop=0.0, n=9, rim=None):
    """A moth wing from root, pointing ang deg, a rounded leaf length x width; spots: [(t, s, mat, tone)] along it."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    pts = []
    for i in range(n + 1):
        t = i / n
        w = width * math.sin(t * math.pi) ** 0.8 * (1.0 + 0.25 * t)
        pts.append((root[0] + ux * length * t + vx * w * 0.55, root[1] + uy * length * t + vy * w * 0.55))
    for i in range(n, -1, -1):
        t = i / n
        w = width * math.sin(t * math.pi) ** 0.9
        sc = scallop * (0.5 + 0.5 * math.cos(t * math.pi * 6)) if t > 0.3 else 0.0
        pts.append((root[0] + ux * length * t - vx * (w * 0.45 + sc), root[1] + uy * length * t - vy * (w * 0.45 + sc)))
    p = r.poly(pts, mat, z, bias=bias, normal=(-0.25, -0.45, 1.0))
    if rim:
        # a coloured border: the same leaf a little larger, just behind
        big = [(root[0] + (x - root[0]) * 1.1, root[1] + (y - root[1]) * 1.1) for (x, y) in pts]
        r.poly(big, rim, z - 0.005, bias=bias - 0.1, normal=(-0.25, -0.45, 1.0))
    if vein:
        r.line(root[0], root[1], root[0] + ux * length * 0.85, root[1] + uy * length * 0.85, vein[0], z + 0.01, tone=vein[1])
    for (t, sv, sm, st) in spots or ():
        r.ell(root[0] + ux * length * t + vx * sv, root[1] + uy * length * t + vy * sv, 1.2, 1.2, sm, z + 0.02, flat=st)
    return p


def antenna(r, x, y, ang, ln, mat, z, feather=True, tone=3):
    """A feathery moth antenna: a stalk with short side barbs."""
    pts = chain(x, y, [(ln * 0.5, ang), (ln * 0.5, ang + 25)])
    r.polyline(pts, mat, z, tone=tone)
    if feather:
        for i in range(1, 4):
            t = i / 4.0
            px, py = lerp_pt(pts[0], pts[-1], t)
            r.dot(px - 1, py - 0.5, mat, tone - 1, z - 0.01)
            r.dot(px + 1, py - 0.5, mat, tone - 1, z - 0.01)


def moth(r, cx, cy, span=9.0, chord=6.5, flap=0.0, fore="frost", hind="silk", body="fur", z=0.0, lean=0.0,
         spots=(), hspots=(), eye="eye", ant=0.0, ant_mat="frost", hind_span=0.62, fold=1.0, abd=4.0, scallop=0.4,
         head_r=1.6, far=0.8, rise=0.0, rim=None):
    """A moth seen from the front-left, wings spread wide (the far, left wing foreshortened by `far`).
    flap: degrees the wings beat down (+) or up (-). Returns the head point."""
    T = Xf(lean, (cx, cy))
    L = span * fold
    # far (left) wings first, darker
    wing(r, T(cx - 0.6, cy - 0.6), -158 + flap + rise, L * far, chord * 0.9, fore, z - 2.0, bias=-0.28, rim=rim,
         spots=[(t, -v, m, max(1, tn - 1)) for (t, v, m, tn) in spots])
    wing(r, T(cx - 0.6, cy + 0.8), 165 - flap * 0.5, L * hind_span * far, chord * 0.75, hind, z - 2.1, bias=-0.3,
         spots=[(t, -v, m, max(1, tn - 1)) for (t, v, m, tn) in hspots])
    # body: furry thorax, segmented abdomen hanging below
    r.tube([T(cx + 0.4, cy - 1.0), T(cx, cy + 1.5), T(cx - 0.4, cy + abd)], [1.8, 1.4, 0.8], body, z, bias=0.1)
    for k in range(1, 3):
        x, y = T(cx - 0.1 * k, cy + 1.0 + k * 1.1)
        r.dot(x - 1, y, body, 1, z + 0.01); r.dot(x + 1, y, body, 1, z + 0.01)
    hx, hy = T(cx + 1.0, cy - 2.4)
    r.ell(hx, hy, head_r, head_r * 0.9, body, z + 0.3, bias=0.2)
    r.dot(hx + 0.8, hy, eye, 3, z + 0.5); r.dot(hx - 0.6, hy - 0.2, eye, 2, z + 0.5)
    antenna(r, hx + 0.6, hy - 1.2, -62 + ant, 4.2, ant_mat, z + 0.2)
    antenna(r, hx - 0.6, hy - 1.2, -112 + ant, 3.6, ant_mat, z - 0.5, tone=2)
    # near (right) wings over the body
    wing(r, T(cx + 0.6, cy + 0.8), 15 + flap * 0.5, L * hind_span, chord * 0.78, hind, z + 1.0, bias=-0.05, spots=hspots, rim=rim)
    wing(r, T(cx + 0.6, cy - 0.6), -22 - flap - rise, L, chord, fore, z + 1.1, bias=0.05, spots=spots, scallop=scallop, rim=rim)
    return (hx, hy)


def robe(r, top, hem_y, hem_w, sway=0.0, mat="robe", z=0.0, top_w=3.0, flare=1.0, bias=0.0, hem_teeth=0, teeth_mat=None):
    """A bell-shaped robe from shoulders at top (x, y) to a hem at hem_y, hem_w wide; sway leans the hem."""
    tx, ty = top
    pts = [(tx - top_w, ty), (tx + top_w, ty)]
    for i in range(1, 5):
        t = i / 4.0
        w = lerp(top_w, hem_w / 2.0, t ** flare)
        pts.append((tx + w + sway * t, lerp(ty, hem_y, t)))
    left = []
    for i in range(4, 0, -1):
        t = i / 4.0
        w = lerp(top_w, hem_w / 2.0, t ** flare)
        left.append((tx - w + sway * t * 0.7, lerp(ty, hem_y, t)))
    pts += left
    p = r.poly(pts, mat, z, bias=bias, curve=0.8)
    if hem_teeth:
        for i in range(hem_teeth):
            x = tx - hem_w / 2.0 + sway + (i + 0.5) * hem_w / hem_teeth
            r.dot(x, hem_y + 1, teeth_mat or mat, 3, z + 0.01)
    return p


def shadow(r, x, y, rx, z=-20.0):
    """A soft contact shadow under a hovering body (two tones of the floor shade)."""
    r.ell(x, y, rx, max(1.0, rx * 0.28), "shade", z, flat=1)


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


def fx(name, cell, origin, anims, outdir, scale=8):
    """An effect sheet with a fixed cell and origin (the code's offsets depend on them)."""
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-20s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def tail_anims(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [stone(idle0)], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


# ================================================================== TIMING.md
SYNC = {}
NOTES = {}


def write_timing(outdir):
    L = ["# Ysveld: sprite timing", "",
         "Generated by `tools/sprites/ysveld_v2_rigs.py` (and the ysveld_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet, x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). Every sheet is at final size (no ArtScale).", "",
         "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in BUILT.items():
        if n.startswith("Fx") or n.startswith("Deity"): continue
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox()
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], bb[2] - bb[0], bb[3] - bb[1],
                                                               ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Effect sheets", "", "| Sheet | Cell | Origin | Anims |", "|---|---|---|---|"]
    for n, b in BUILT.items():
        if not n.startswith("Fx"): continue
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, b["cell"][0], b["cell"][1], b["feet"][0], b["feet"][1],
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
# per-sheet fit: the outline adds a pixel all round, so sheets drawn near their tier's size limit are drawn a little smaller
FIT = {"YsvRimeling": 0.93, "YsvHoarmoth": 0.86, "YsvWeaver": 0.92, "YsvLurker": 0.92, "YsvSilkmoth": 0.92,
       "YsvVeilWitch": 0.91, "YsvRimeKnight": 0.94, "YsvHermit": 0.94, "YsvMatron": 0.94, "YsvHoarclaw": 0.97, "YsvEmpress": 0.96}

MODULES = ("ysveld_v2_t1", "ysveld_v2_t2", "ysveld_v2_t3a", "ysveld_v2_t3b", "ysveld_v2_fx", "ysveld_v2_idol")


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
        Rig.SCALE = FIT.get(name, 1.0)
        fn(outdir)
        Rig.SCALE = 1.0
    if not only:
        write_timing(outdir)


if __name__ == "__main__":
    sys.modules["ysveld_v2_rigs"] = sys.modules[__name__]   # the tier modules import this one by name: share its state
    main()
