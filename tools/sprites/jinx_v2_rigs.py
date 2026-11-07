"""JINX v2: every Jinx monster and effect sheet. This file holds the material renderer, the five
sheets that set the style (Dice Imp, Ringmaster, Roulette Ouroboros, Grand Jester, High Roller) and the build entry point; the other
monsters are in jinx_v2_t1.py, jinx_v2_t2.py and jinx_v2_t3.py, the effects in jinx_v2_fx.py.

    python3 jinx_v2_rigs.py [outdir] [--only Name,Name]

Writes to art/out_jinx/ by default. Same manifest format as every other sheet: <id>.png + <id>.json (cellW, cellH,
cols, anims[{name, frames, durations}]) + <id>_preview.png, feet at (cellW // 2, cellH - 2), facing right.

What changed from jinx_rigs.py (the v1 rig), after measuring the vanilla tier 3s:
  * MATERIAL BUFFER, not a char canvas. Every pixel keeps (depth, material, light, part). Shapes are lit by a real
    normal against one top-left light and quantised to 3 tones per material (+ a highlight tone only on shiny
    materials: gold, ivory, glass). Tones come from hue-shifted ramps (shadows cooler, lights warmer).
  * SELECTIVE OUTLINE. Vanilla T3s have no black ring: 0-38 % of their silhouette edge is near-black (the v1 Jinx
    sheets: 87-100 %). Here the bottom/right silhouette edge takes the material's own darkest tone (sel-out) and the
    top/left edge stays lit, so the shape reads against the dark crypt floor by value, the way the vanilla art does.
  * CLUSTERS. After quantising, single stray tone pixels are folded into their neighbours (no noise, no banding);
    a front part casts a one-tone shadow down-right onto what is behind it; two touching parts of the same
    material get a contour line on the back one, so an arm over a coat still reads.
  * POSES, NOT TRANSFORMS. Every frame (death and knockback too) is a posed redraw; motion frames add
    anticipation, smears and follow-through where the motion is fast.
"""
import math, os, sys, json, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from anim import Spr, SprRGB, pack, preview  # noqa: E402
from PIL import Image  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_jinx")


# ================================================================== palette: material ramps (ink, shadow, base, light, hi)
def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


RAMPS = {
    # cloth / skin
    "crim":  ["2a0a1a", "5e1426", "962230", "c4423a", "e07a52"],   # harlequin crimson (shadows go plum)
    "blk":   ["120e1a", "241c2e", "3a3046", "564a62", "766a80"],   # harlequin black (violet-grey lights)
    "coat":  ["1a0c1c", "3c1428", "5e1e32", "86303c", "a8524a"],   # ringmaster's dark wine tailcoat
    "imp":   ["2c0c1c", "6a1c2a", "a43430", "d0603e", "ec9a62"],   # imp skin: hot coral-red
    "dskin": ["2a1020", "5a2030", "8c3a3a", "b65e48", "d68a62"],   # demon skin (high roller, darker)
    "flesh": ["3a1e24", "7a4a44", "b07c62", "d6a882", "eccaa0"],   # human skin
    "ivory": ["3a2a30", "8a7468", "c4b294", "e6dab8", "fbf4dc"],   # masks, dice, teeth, ruffs
    "gold":  ["2e1a10", "6e4618", "a8782a", "dcb04a", "fbe796"],   # tarnished brass / gold leaf
    "felt":  ["0c1c1a", "163a30", "245a42", "3a7e54", "64a670"],   # card-table green
    "chipb": ["0e1430", "1e3266", "3456a0", "5a86cc", "9cc0ec"],   # blue chip
    "wood":  ["1e120e", "4a2a1a", "70442a", "96643c", "b88a58"],
    "lthr":  ["160e0e", "33201a", "4e3226", "6c4a34", "8a6646"],   # whip leather, boots
    "steel": ["1a1a24", "3e4250", "686e7e", "9aa0ae", "d4d8e0"],
    "wing":  ["1e0a1a", "45142e", "6e2242", "96384e", "b85a5e"],   # bat-wing membrane
    "horn":  ["14101a", "2c2430", "4a3e46", "6e5e5e", "9a8a7a"],
    "plum":  ["160a1c", "36163e", "5a2a5e", "804878", "a46c94"],   # high roller's demon hide
    "rdie":  ["2a0814", "6e1020", "a81c2a", "dc3a3a", "ff8a7a"],   # translucent casino-red die
    "tear":  ["101c3a", "203a6e", "3a62a8", "6a94d0", "a8ccf0"],   # tragedy-mask blue
    "scale": ["1e0a14", "4a1022", "7c1a2a", "a83030", "cc5a44"],   # serpent red scales
    "sblk":  ["0e0c14", "1e1a26", "322a3a", "4a4052", "665a6c"],   # serpent black scales
    "belly": ["2a2018", "6a5440", "a08a62", "c8b482", "e6d6a8"],   # serpent belly plates
    "gob":   ["1a2014", "3e4a24", "6a7434", "9a9c4a", "c4c070"],   # card sharp's sallow goblin skin
    "porc":  ["3a3040", "8a7e8a", "c8bec2", "e8e0dc", "fffaf2"],   # marionette porcelain (cool shadows)
    "card":  ["3a3438", "8e8684", "cfc8bc", "efeadc", "fffcf0"],   # playing-card stock
    "viol":  ["160c26", "321a4e", "54307a", "7a4ea0", "a07ac2"],   # seer's violet velvet
    "jade":  ["0c2018", "164234", "26664a", "3e8e62", "70b886"],   # gorgon jade
    "mane":  ["2a1408", "6a3612", "a4601e", "d08e34", "f0c060"],   # chimera ochre mane / lion hide
    "glass": ["1a2a34", "3a5a6a", "6a94a4", "a8ccd4", "e6f8fa"],   # slot-machine glass
    "d20":   ["1c0c30", "3e1a64", "6430a0", "8e58c8", "c09cec"],   # natural twenty's violet facets
    # emissive (not shaded, no sel-out)
    "eye":   ["5a0c0c", "b01a1a", "ff3a2a", "ff8a5a", "ffd0a0"],
    "glow":  ["3a1a5a", "7a3aa8", "b46ae0", "d8a8f4", "f4e0ff"],   # Jinx violet luck-magic
    "fire":  ["5a1a0a", "b8401a", "f07a24", "ffc04a", "fff0b0"],
    "ember": ["4a0c0a", "a0200e", "e8501a", "ffa040", "fff0a0"],
    "smoke": ["2a2630", "4a4652", "6e6a76", "948f9a", "b8b4bc"],
    "white": ["8a8a90", "c8c8cc", "e8e8ea", "f6f6f6", "ffffff"],
}
RAMPS = {k: [_h(c) for c in v] for k, v in RAMPS.items()}
EMISSIVE = {"eye", "glow", "fire", "ember", "smoke", "white"}
SHINY = {"gold", "ivory", "steel", "chipb", "glass", "rdie", "porc", "d20", "jade"}
STONE = [_h(c) for c in ("2a2a30", "4c4c54", "6e6e76", "92929a", "b6b6bc")]

LIGHT = (-0.55, -0.68, 0.48)
_ln = math.sqrt(sum(v * v for v in LIGHT)); LIGHT = tuple(v / _ln for v in LIGHT)
T_SHADOW, T_LIGHT, T_HI = 0.12, 0.62, 0.9


def lam(nx, ny, nz):
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


# ================================================================== the material buffer
class Rig:
    """Pixel buffer: (x, y) -> [z, mat, light, part, fixed_tone]. Origin = feet, y up is negative."""

    def __init__(self):
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
        for (x, y) in line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
            self.put(x, y, z, mat, 0.5, p, tone)
        return p

    def polyline(self, pts, mat, z, tone=2, tones=None, part=None):
        p = part or self.part(True, z)
        for i in range(len(pts) - 1):
            t = tones[i] if tones else tone
            for (x, y) in line_px(int(round(pts[i][0])), int(round(pts[i][1])), int(round(pts[i + 1][0])), int(round(pts[i + 1][1]))):
                self.put(x, y, z, mat, 0.5, p, t)
        return p

    def dot(self, x, y, mat, tone, z, part=None):
        p = part or self.part(True, z)
        self.put(x, y, z, mat, 0.5, p, tone)
        return p

    def dots(self, pts, mat, tone, z):
        p = self.part(True, z)
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
        lift = 1 if m in ("ivory", "gold", "white", "flesh", "belly", "porc", "card") else 0
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


# ------------------------------------------------------------------ the die (shared by the imp and others)
CUBE = [((1, 0, 0), 3), ((-1, 0, 0), 4), ((0, -1, 0), 1), ((0, 1, 0), 6), ((0, 0, 1), 2), ((0, 0, -1), 5)]
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)]}


def rot3(v, rx, ry, rz):
    x, y, z = v
    for ax, a in (("y", ry), ("x", rx), ("z", rz)):
        a = math.radians(a); ca, sa = math.cos(a), math.sin(a)
        if ax == "x": y, z = y * ca - z * sa, y * sa + z * ca
        elif ax == "y": x, z = x * ca + z * sa, -x * sa + z * ca
        else: x, y = x * ca - y * sa, x * sa + y * ca
    return x, y, z


def die3(r, cx, cy, size, rx=0.0, ry=35.0, rz=0.0, z=0.0, mat="ivory", pip="blk", one="crim", tilt=26.0,
         pip_min=2.4, pips=True, pip_faces=6, part_z_step=0.001, pip_skip=0):
    """A die of edge `size` centred (cx, cy): flat-lit faces, pips (the 1 in red), crisp edges.
    The camera looks down `tilt` degrees, so the top face shows. Faces nearer the viewer draw over the others."""
    h = size / 2.0
    xf = lambda v: rot3(rot3(v, rx, ry, rz), -tilt, 0, 0)
    faces = []
    for n, val in CUBE:
        nn = xf(n)
        # screen: x right, y down, viewer at -z -> facing if nn z < 0
        if nn[2] >= -0.02: continue
        if n[0]: e1, e2 = (0, 0, 1), (0, 1, 0)
        elif n[1]: e1, e2 = (1, 0, 0), (0, 0, 1)
        else: e1, e2 = (1, 0, 0), (0, 1, 0)
        pts = []
        for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            w = xf(tuple(h * (n[k] + su * e1[k] + sv * e2[k]) for k in range(3)))
            pts.append((cx + w[0], cy + w[1]))
        faces.append((-nn[2], pts, val, n, e1, e2, nn))
    faces.sort(key=lambda f: f[0])
    pip_ok = set(id(f) for f in sorted(faces, key=lambda f: -abs(f[6][2]) * (1.25 if f[6][1] > 0.3 else 1.0))[pip_skip:pip_skip + pip_faces])
    part = r.part(False, z)
    for i, (facing, pts, val, n, e1, e2, nn) in enumerate(faces):
        l = lam(nn[0], nn[1], -nn[2])
        t = 1 if l < 0.05 else 2 if l < 0.5 else 3
        if t == 3 and l > 0.8 and mat == "ivory": t = 4 if size >= 8 else 3
        pp = r.part(False, z + 0.001 * i)
        for (x, y) in poly_px(pts):
            r.put(x, y, z + 0.001 * i, mat, 0.5, pp, t)
        if size >= 9:
            # bevel: the face's upper/left edges catch the light, its lower/right edges sit in shadow
            cxp = sum(q[0] for q in pts) / 4.0; cyp = sum(q[1] for q in pts) / 4.0
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                mx_, my_ = (a_[0] + b_[0]) / 2 - cxp, (a_[1] + b_[1]) / 2 - cyp
                tt = min(4, t + 1) if (mx_ + my_) < -0.5 else max(0, t - 1) if (mx_ + my_) > 0.5 else t
                for (x, y) in line_px(int(math.floor(a_[0] + 0.5)), int(math.floor(a_[1] + 0.5)), int(math.floor(b_[0] + 0.5)), int(math.floor(b_[1] + 0.5))):
                    if (x, y) in r.b and r.b[(x, y)][3] == pp:
                        r.put(x, y, z + 0.001 * i, mat, 0.5, pp, tt)
        if pips and abs(nn[2]) * size >= pip_min and id(faces[i]) in pip_ok:
            k = 0.52
            for (pu, pv) in PIPS[val]:
                w = xf(tuple(h * (n[j] + k * (pu * e1[j] + pv * e2[j])) for j in range(3)))
                pm = one if val == 1 else pip
                r.put(cx + w[0], cy + w[1], z + 0.01 + 0.001 * i, pm, 0.5, pp, 3 if pm == "ivory" else (1 if val != 1 else 2))
    return part


# ------------------------------------------------------------------ bat wing
def bat_wing(r, sx, sy, ang, spread, ln, z, mat="wing", near=True, fingers=3):
    """Wing from shoulder (sx, sy): arm bone along ang, `fingers` struts fanning `spread` deg, scalloped membrane."""
    ex, ey = sx + ln * 0.42 * math.cos(math.radians(ang)), sy + ln * 0.42 * math.sin(math.radians(ang))
    tips = []
    for k in range(fingers):
        a = ang + 20 + k * spread / max(1, fingers - 1)
        L = ln * (1.0 - 0.16 * k)
        tips.append((ex + L * math.cos(math.radians(a)), ey + L * math.sin(math.radians(a))))
    pts = [(sx, sy), (ex, ey), tips[0]]
    for a_, b_ in zip(tips, tips[1:]):
        mx, my = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
        cx, cy = (ex + mx) / 2, (ey + my) / 2
        pts += [(lerp(mx, cx, 0.35), lerp(my, cy, 0.35)), b_]
    pts += [(sx + 1.2, sy + 2.2)]
    bias = 0.12 if near else -0.3
    r.poly(pts, mat, z, bias=bias, normal=(-0.2, -0.3, 1.0))
    bone = r.part(True, z + 0.01)
    for (x, y) in line_px(*map(int, map(round, (sx, sy, ex, ey)))):
        r.put(x, y, z + 0.01, "horn", 0.5, bone, 2 if near else 1)
    for t in tips:
        for (x, y) in line_px(int(round(ex)), int(round(ey)), int(round(t[0])), int(round(t[1]))):
            r.put(x, y, z + 0.01, "horn", 0.5, bone, 1 if near else 0)
    r.put(ex, ey - 1, z + 0.02, "ivory", 0.5, bone, 2 if near else 1)    # thumb claw
    return tips


# ------------------------------------------------------------------ flat-faced boxes and playing cards
def box3(r, x0, y0, w, h, d, mat, z, top=None, side=None, front=None, ang=0.0, pivot=None):
    """A box seen from the front and a little above: front face w x h with its bottom-left at (x0, y0) (y0 = bottom),
    a top face d px deep and a right side face, each flat-lit. top/side/front: material overrides (or callables).
    ang tilts the whole box about pivot (default: the bottom centre). Returns the four front corners (bl, br, tr, tl)."""
    pv = pivot or (x0 + w / 2.0, y0)
    T = Xf(ang, pv)
    sk = d * 0.6                                    # the depth recedes up and to the right
    bl, br, tr, tl = T(x0, y0), T(x0 + w, y0), T(x0 + w, y0 - h), T(x0, y0 - h)
    btr, btl = T(x0 + w + sk, y0 - h - d * 0.7), T(x0 + sk, y0 - h - d * 0.7)
    bbr = T(x0 + w + sk, y0 - d * 0.7)
    r.poly([br, bbr, btr, tr], side or mat, z - 0.02, normal=(0.9, -0.2, 0.45))
    r.poly([tl, tr, btr, btl], top or mat, z - 0.01, normal=(-0.1, -1.0, 0.5))
    r.poly([bl, br, tr, tl], front or mat, z, normal=(-0.15, -0.1, 1.0))
    return bl, br, tr, tl


def card(r, cx, cy, w, h, mat_face="card", back=None, pip=None, pip_mat="crim", z=0.0, ang=0.0, edge=False, lit=0.0):
    """A playing card centred (cx, cy), w x h, turned ang degrees. back: a material (or callable) for the patterned
    back (else the face shows, with an optional pip stamp of 1-3 px in pip_mat). edge=True draws it edge-on."""
    if edge:
        a = math.radians(ang + 90)
        return r.line(cx - h / 2 * math.cos(a), cy - h / 2 * math.sin(a), cx + h / 2 * math.cos(a), cy + h / 2 * math.sin(a),
                      mat_face, z, tone=3)
    T = Xf(ang, (cx, cy))
    pts = [T(cx - w / 2, cy - h / 2), T(cx + w / 2, cy - h / 2), T(cx + w / 2, cy + h / 2), T(cx - w / 2, cy + h / 2)]
    p = r.poly(pts, back or mat_face, z, bias=lit, normal=(-0.2, -0.3, 1.0))
    if back is None and pip:
        for (dx, dy) in pip:
            r.dot(*T(cx + dx, cy + dy), pip_mat, 2, z + 0.01)
    return p


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


def tail_anims(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [stone(idle0)], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]




# ================================================================== DICE IMP (T1): a big-headed imp hugging its die
IMP_LEG = {"k": ("imp", 0), "d": ("imp", 1), "r": ("imp", 2), "R": ("imp", 3), "L": ("imp", 4),
           "Y": ("fire", 4), "y": ("fire", 3), "W": ("ivory", 4), "w": ("ivory", 3), "a": ("ivory", 1),
           "m": ("blk", 0), "n": ("crim", 1), "h": ("horn", 1)}
IMP_HEAD = {
    # pivot (3, 6): the chin. Curled ivory horns, two yellow eyes with pupils, a fanged grin.
    "grin": """
.w....w.
.aRRRRa.
rRLRRRRd
RYmRRYmk
RRRRRRRk
dRWnWnRk
.ddkkdd.
""",
    "glee": """
.w....w.
.aRRRRa.
rRLRRRRd
RmmRRmmk
RRRRRRRk
dRnWWWnk
.ddkkdd.
""",
    "hurt": """
w......w
.aRRRRa.
rRLRRRRd
RwmRRwmk
RRRRRRRk
dRmnnmRk
.ddkkdd.
""",
    "dead": """
........
waRRRRaw
rRLRRRRd
RmRmmRmk
RRmRRmRk
dRRmmRRk
.ddkkdd.
""",
}


def imp_body(r, cx, cy, z, flap, tail, near_hand, far_hand, face, lean=0.0, wing_len=7.0, claws=True, arm=2.2):
    """The imp around a point (cx, cy) = its chin. Wings fan from behind the head, arms reach to the hands."""
    T = Xf(lean, (cx, cy + 3))
    sx, sy = T(cx - 1.5, cy + 1.0)
    bat_wing(r, sx + 0.5, sy - 1.0, -112 + flap * 0.6, 60, wing_len * 0.75, -3.0, near=False)
    bat_wing(r, sx, sy - 0.5, -140 + flap, 66, wing_len, -1.0, near=True)
    # tail: from the rump, curls out behind and down, gold spade tip
    tp = chain(*T(cx - 2.0, cy + 3.5), [(2.0, 175 + tail), (2.2, 210 + tail), (2.0, 250 + tail * 1.2), (1.6, 300 + tail * 1.4)])
    r.tube(tp, [0.8, 0.7, 0.6, 0.5, 0.4], "imp", -2.0, bias=-0.15)
    ex, ey = tp[-1]
    r.stamp("""
.g.
gGg
.g.
""", ex, ey, -1.9, {"g": ("gold", 2), "G": ("gold", 4)}, pivot=(1, 0))
    # torso (mostly hidden by whatever it hugs)
    bx, by = T(cx - 0.4, cy + 3.0)
    r.ell(bx, by, 2.6, 2.4, "imp", 0.0, bias=0.0)
    # arms: shoulders -> hands, claws ivory
    for k, (hx, hy) in enumerate((far_hand, near_hand)):
        sx_, sy_ = T(cx + (-1.6 if k == 0 else 1.4), cy + 2.0)
        el = ik(sx_, sy_, hx, hy, arm, arm, bend=1 if k else -1)
        z_ = (0.5 if k == 0 else 4.0)
        r.tube([(sx_, sy_), el, (hx, hy)], [0.9, 0.8, 0.7], "imp", z_, bias=-0.3 if k == 0 else 0.0)
        if claws:
            r.dot(hx + 1, hy, "ivory", 3 if k else 2, z_ + 0.01)
    # head (hand-pixelled), centred on the chin point
    r.stamp(IMP_HEAD[face], *T(cx, cy), 3.0, IMP_LEG, pivot=(4, 6))


def dice_imp(alt=1.0, die_rot=(0.0, 34.0, 0.0), die_at=None, die_size=7.0, lean=0.0, flap=0.0, tail=0.0,
             face="grin", head_dy=0.0, head_dx=0.0, near_hand=None, far_hand=None, small=None, smear=None,
             extra=None, dust=None, die_z=2.0, hold=True, arm=2.2, die_mat="ivory", glint=None, small2=None):
    """The die floats `alt` px off the floor; the imp's chin rests on its top edge (head_dx/dy move the imp)."""
    r = Rig()
    dcx, dcy = 0.5, -alt - die_size * 0.62
    top = dcy - die_size * 0.55
    cx, cy = -1.0 + head_dx, top + 0.2 + head_dy
    if die_at is None:
        die3(r, dcx, dcy, die_size, *die_rot, z=die_z, pip_faces=1, pip_min=3.0, mat=die_mat)
    else:
        die3(r, die_at[0], die_at[1], die_size, *die_rot, z=die_z, pip_faces=1, pip_min=3.0, mat=die_mat)
    nh = near_hand or (dcx + 3.4, top + 1.4)
    fh = far_hand or (dcx - 3.4, top + 1.0)
    imp_body(r, cx, cy, 1.0, flap, tail, nh, fh, face, lean=lean, arm=arm)
    if small is not None:
        die3(r, small[0], small[1], 2.6, small[2], small[2] * 1.3, 0, z=4.5, pips=False)
    if small2 is not None:
        die3(r, small2[0], small2[1], 2.6, small2[2], small2[2] * 1.3, 0, z=4.4, pips=False)
    if glint:
        for (x, y, k) in glint: star(r, x, y, k)
    if smear:
        for (a, b, m, tn) in smear:
            r.line(*a, *b, m, 3.5, tone=tn)
    if dust:
        dust_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def dust_puff(r, x, y, k, w=1.0):
    """Floor dust: k = 0 (burst) .. 2 (thinning)."""
    for side in (-1, 1):
        for i in range(3 - k):
            px = x + side * (2 + i * 2 + k * 1.5) * w
            py = y - (i % 2) - (1 if k else 0)
            r.ell(px, py, 1.2 - 0.3 * k, 0.9, "smoke", 5.0 + i * 0.01, flat=2 if i else 3)


def imp_sheet(outdir):
    I = dice_imp
    idle = [I(alt=[0.0, 0.3, 0.6, 0.3][i], flap=[-12, -20, -30, -20][i], tail=[0, 8, 14, 6][i], head_dy=[0, 0, 0.5, 0][i])
            for i in range(4)]
    # Run: the die tumbles forward under it (the imp rides the roll, leaning in), wings beating
    run = [I(alt=0.4 + 0.8 * abs(math.sin(i / 6 * math.pi * 2)), lean=10, flap=[-35, -5, 25, 35, 10, -20][i],
             die_rot=(0.0, 34.0, i * 15.0), tail=[-10, -4, 4, 10, 4, -4][i], head_dx=0.5) for i in range(6)]
    # Toss (6): reach behind for a little die (0), cock it over the head (1), fling (2, smear), release (3), follow, settle
    toss = [I(lean=-6, flap=-10, near_hand=(-1.0, -11.5), small=(-1.0, -13.0, 20), face="glee"),
            I(lean=-12, flap=-30, near_hand=(-2.0, -15.5), small=(-2.0, -17.0, 50), face="glee", head_dy=-0.5),
            I(lean=8, flap=20, near_hand=(4.5, -14.0), small=(5.5, -15.5, 80), face="glee",
              smear=[((-1, -17), (4, -17), "ivory", 1)]),
            I(lean=16, flap=35, near_hand=(7.0, -9.5), face="glee", head_dx=1.0,
              smear=[((5, -13), (10, -12), "ivory", 2), ((4, -12), (9, -11), "ivory", 1)],
              extra=lambda r: die3(r, 12.0, -11.0, 2.6, 30, 60, 0, z=5, pips=False)),
            I(lean=10, flap=10, near_hand=(5.5, -6.5), head_dx=0.5),
            I(lean=2, flap=-10)]
    # TossTwin (6): after a lucky six: two little dice in both claws, flung in a V (3)
    twin = [I(lean=-6, flap=-10, near_hand=(-1.0, -11.5), far_hand=(-3.0, -11.0), small=(-1.0, -13.0, 20),
              small2=(-3.0, -12.5, 60), face="glee", die_mat="gold"),
            I(lean=-12, flap=-30, near_hand=(-2.0, -15.5), far_hand=(-4.0, -14.5), small=(-2.0, -17.0, 50),
              small2=(-4.5, -16.0, 10), face="glee", head_dy=-0.5, die_mat="gold", glint=[(0.0, -19.0, 2)]),
            I(lean=8, flap=20, near_hand=(4.5, -14.0), far_hand=(3.0, -15.0), small=(5.5, -15.5, 80), small2=(4.0, -17.5, 30),
              face="glee", smear=[((-1, -17), (4, -17), "ivory", 1), ((-2, -19), (3, -19), "ivory", 1)], die_mat="gold"),
            I(lean=16, flap=35, near_hand=(7.0, -9.5), far_hand=(6.0, -11.0), face="glee", head_dx=1.0, die_mat="gold",
              smear=[((5, -13), (10, -12), "ivory", 2), ((5, -15), (10, -16), "ivory", 2)],
              extra=lambda r: [die3(r, 12.0, -10.0, 2.6, 30, 60, 0, z=5, pips=False), die3(r, 12.0, -15.0, 2.6, 0, 40, 20, z=5, pips=False)]),
            I(lean=10, flap=10, near_hand=(5.5, -6.5), head_dx=0.5),
            I(lean=2, flap=-10)]
    # Lucky (4 + 6): the idle and run while a six is banked: the big die burns gold and glints
    lucky = [I(alt=[0.0, 0.3, 0.6, 0.3][i], flap=[-12, -20, -30, -20][i], tail=[0, 8, 14, 6][i], head_dy=[0, 0, 0.5, 0][i],
               die_mat="gold", face="glee" if i == 2 else "grin", glint=[[(4.0, -9.0, 2)], [(5.0, -6.0, 1)], [], [(-2.0, -6.0, 2)]][i])
             for i in range(4)]
    lucky_run = [I(alt=0.4 + 0.8 * abs(math.sin(i / 6 * math.pi * 2)), lean=10, flap=[-35, -5, 25, 35, 10, -20][i],
                   die_rot=(0.0, 34.0, i * 15.0), tail=[-10, -4, 4, 10, 4, -4][i], head_dx=0.5, die_mat="gold",
                   glint=[(4.0, -8.0, 2)] if i % 3 == 0 else None) for i in range(6)]
    # Roll (8): grip (0), heave it up (1), spin it overhead (2-5, smeared), SLAM it down in front (6), new die poofs in (7)
    roll = [I(lean=6, flap=-20, head_dy=1.0, face="glee")]
    roll.append(I(alt=2.0, lean=-4, flap=30, die_at=(1.0, -20.0), die_rot=(0, 34, 20), face="glee", head_dy=-2.5,
                  near_hand=(3.4, -16.5), far_hand=(-1.6, -16.5), die_z=2.5, arm=3.2))
    for k in range(4):
        roll.append(I(alt=2.5, lean=[-8, -2, -8, -2][k], flap=[-40, 30, -40, 30][k], head_dy=-4.5,
                      die_at=(1.0 + [0, 0.5, 0, -0.5][k], -21.5), die_rot=(0, 34 + 25 * k, 40 + 50 * k), face="glee",
                      near_hand=(3.4 + [0, 0.5, 0, -0.5][k], -18.0), far_hand=(-1.6, -18.0), die_z=2.5, arm=3.4,
                      smear=[((-4, -23 + k % 2), (-3, -25 + k % 2), "ivory", 2), ((6, -25 + k % 2), (7, -23 + k % 2), "ivory", 2)]))
    roll.append(I(alt=2.0, lean=22, flap=40, head_dy=1.5, head_dx=2.0, die_at=(8.5, -3.3), die_rot=(0, 20, 0),
                  die_z=4.0, face="glee", near_hand=(7.0, -7.0), far_hand=(5.0, -7.5), dust=(8.5, 0, 0, 1.0),
                  smear=[((7, -10), (7, -16), "ivory", 1), ((10, -10), (10, -16), "ivory", 1)]))
    roll.append(I(alt=1.6, lean=4, flap=-15, face="grin", dust=(8.5, 0, 1, 1.2),
                  extra=lambda r: r.dots([(-5, -9), (5, -10), (-4, -3), (6, -4)], "glow", 3, 6)))
    # death (4): struck (0), let go and tips (1), crashes (2), corpse beside the die, which shows a red 1 (3)
    d0 = I(lean=-18, flap=-50, face="hurt", head_dy=-1.0, head_dx=-1.0)
    d1 = I(alt=0.5, lean=-50, flap=60, face="dead", head_dx=-3.0, head_dy=1.0, die_rot=(0, 50, 30),
           near_hand=(1.0, -13.0), far_hand=(-6.0, -12.0))
    d2 = imp_corpse(stage=0)
    corpse = imp_corpse(stage=1)
    knock = I(lean=-22, flap=-45, face="hurt", alt=1.6, head_dx=-1.0, die_rot=(0, 30, -14))
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.07] * 6),
             ("Toss", toss, [0.14, 0.12, 0.05, 0.08, 0.1, 0.14]),
             ("Roll", roll, [0.14, 0.07, 0.07, 0.07, 0.07, 0.07, 0.06, 0.25]),
             ("TossTwin", twin, [0.14, 0.12, 0.05, 0.08, 0.1, 0.14]),
             ("IdleLucky", lucky, [0.12, 0.1, 0.12, 0.1]), ("RunLucky", lucky_run, [0.07] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("JinxDiceImp", anims, outdir, scale=6)


def imp_corpse(stage=1):
    r = Rig()
    die3(r, 5.0, -3.4, 6.2, 0 if stage else 20, 0 if stage else 60, 0 if stage else 25, z=0.0, pip_faces=2, pip_min=2.0)
    bat_wing(r, -2.0, -2.0, -40 if stage else -70, 55, 6.0, -1.0, near=True)
    r.ell(-1.5, -1.8, 2.6, 1.7, "imp", 1.0)
    r.tube([(0.2, -1.4), (1.6, -3.6), (2.4, -3.2)], [0.9, 0.7, 0.5], "imp", 1.2)
    r.stamp("""
.kd.
dRrd
RYRk
rmWk
dmmk
.dk.
""", -5.0, -1.0, 2.0, IMP_LEG, pivot=(2, 5)) if stage == 0 else r.stamp("""
..ddd.
wdRRrk
aRmRmk
.RRRRk
.dmmmk
""", -5.5, 0.0, 2.0, IMP_LEG, pivot=(3, 4))
    if stage == 0:
        dust_puff(r, -2.0, 0, 1, 1.2)
    return r.resolve()


# ================================================================== RINGMASTER (T2): masked ringleader, crimson tailcoat, whip
RING_LEG = {"k": ("blk", 0), "K": ("blk", 1), "b": ("blk", 2), "B": ("blk", 3), "V": ("blk", 4),
            "a": ("ivory", 1), "w": ("ivory", 2), "W": ("ivory", 3), "X": ("ivory", 4),
            "m": ("blk", 0), "n": ("crim", 1), "c": ("crim", 2), "C": ("crim", 3), "e": ("eye", 3),
            "g": ("gold", 2), "G": ("gold", 4)}
RING_HEAD = {
    # masked face: white-painted mask, black eyes, handlebar moustache with upturned tips, small red painted grin
    "grin": """
...aWWWw..
..aWXWWWw.
..wWmWWmW.
m.wWWWWWWwm
.mmmmmmmmm.
..awnCnwa..
...aawwa...
""",
    "shout": """
...aWWWw..
..aWXWWWw.
..wWmWWmW.
m.wWWWWWWwm
.mmmmmmmmm.
..awmnmwa..
...anmna...
""",
    "hurt": """
...aWWWw..
..aWXWWWw.
..wWWmWWm.
..wWmWWmWw.
.mmmmmmmmm.
m.awnnnwa.m
...aawwa...
""",
    "dead": """
...aWWWw..
..aWXWWWw.
..wmWmWmW.
..wWmWmWWw.
.mmmmmmmmm.
m.awnCnwa.m
...aawwa...
""",
}
TOPHAT = """
...BBBbk...
...BbWbK...
...CccnK...
...BbbbK...
.kBbbbbbKk.
"""


def whip_path(hx, hy, angs, seg=3.0):
    return chain(hx, hy, [(seg * (1.0 - 0.04 * i), a) for i, a in enumerate(angs)])


def ringmaster(lean=0.0, bob=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), hand=(5.0, -12.0), hand2=(-4.0, -11.0),
               whip=None, crack=None, face="grin", hat=None, tails=0.0, hoop=None, extra=None, knee_bend=1,
               hips=None, head_dx=0.0, smear=None, body_only=False, akimbo=False):
    """Feet at y=0. hand / hand2: near / far hand. whip: list of segment angles from the near hand (None = coiled
    on the hip). hat: (dx, dy, spin) when the hat flies off (else worn). tails: coat-tail flare (0..1)."""
    r = Rig()
    hip = hips or (0.0, -9.0 + bob)
    T = Xf(lean, hip)
    chest = T(hip[0] + 0.6, hip[1] - 5.0)
    neck = T(hip[0] + 1.0, hip[1] - 7.4)
    sh_n, sh_f = T(hip[0] + 2.4, hip[1] - 6.6), T(hip[0] - 1.8, hip[1] - 6.8)
    # far leg, far arm (behind)
    for k, f in enumerate(feet):
        hp = (hip[0] + (-0.6 if k == 0 else 0.8), hip[1] + 0.4)
        kn = ik(hp[0], hp[1], f[0], f[1] - 1.2, 4.6, 4.2, bend=-knee_bend)
        z = -1.0 if k == 0 else 1.5
        bias = -0.3 if k == 0 else 0.0
        r.tube([hp, kn], [1.3, 1.1], "ivory", z, bias=bias - 0.15)                      # jodhpurs
        r.tube([kn, (f[0], f[1] - 1.2)], [1.1, 1.0], "blk", z + 0.01, bias=bias + 0.2)   # tall boots
        r.poly([(f[0] - 1.4, f[1] - 2.2), (f[0] + 2.4, f[1] - 1.0), (f[0] + 2.4, f[1]), (f[0] - 1.4, f[1])], "blk", z + 0.02,
               bias=bias + 0.25)
        r.dot(kn[0] + 0.6, kn[1] + 1.0, "gold", 3, z + 0.03)                            # boot buckle
    # coat tails: two flaps flaring back from the waist
    wb = T(hip[0] - 1.6, hip[1] - 1.5)
    for k in range(2):
        fl = (0.3 + tails) * (1.0 + 0.6 * k)
        tip = (wb[0] - 3.4 - 3.2 * fl - k * 0.9, hip[1] + 6.0 - 2.4 * fl - k * 0.4)
        r.poly([wb, (wb[0] + 1.6, wb[1] + 1.2), (tip[0] + 1.8, tip[1]), tip], "crim", -1.5 + 0.2 * k,
               bias=-0.25 + 0.15 * k, normal=(-0.3, -0.2, 1.0))
    # far arm
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 3.4, 3.2, bend=-1)
    r.tube([sh_f, e2, hand2], [1.2, 1.0, 0.9], "coat", -0.5, bias=-0.3)
    r.ell(hand2[0], hand2[1], 1.0, 1.0, "ivory", -0.45, bias=-0.1)
    # torso: crimson tailcoat over a black waistcoat, gold buttons
    # a broad-shouldered tailcoat: crimson with gold-piped lapels, a harlequin waistcoat, white shirt-front and bow tie
    tw = [T(hip[0] - 2.8, hip[1] - 0.5), T(hip[0] + 2.8, hip[1] - 0.5), T(hip[0] + 3.8, hip[1] - 6.4),
          T(hip[0] + 2.4, hip[1] - 7.8), T(hip[0] - 2.2, hip[1] - 7.8), T(hip[0] - 3.4, hip[1] - 6.2)]
    r.poly(tw, "crim", 0.0, curve=0.8)
    r.poly([T(hip[0] + 0.2, hip[1] - 0.6), T(hip[0] + 2.6, hip[1] - 0.6), T(hip[0] + 3.0, hip[1] - 5.0),
            T(hip[0] + 1.4, hip[1] - 5.4)], harl(hip[0], hip[1], 2.0, "blk", "crim"), 0.1, curve=0.4, normal=(0.2, 0, 1))
    r.poly([T(hip[0] + 0.8, hip[1] - 5.2), T(hip[0] + 2.8, hip[1] - 5.0), T(hip[0] + 2.4, hip[1] - 7.6),
            T(hip[0] + 1.0, hip[1] - 7.6)], "ivory", 0.15, bias=0.15)
    r.dots([T(hip[0] + 1.2, hip[1] - 7.2), T(hip[0] + 2.4, hip[1] - 7.2)], "blk", 0, 0.2)     # bow tie
    r.dot(*T(hip[0] + 1.8, hip[1] - 7.0), "crim", 1, 0.21)
    r.polyline([T(hip[0] + 0.2, hip[1] - 0.8), T(hip[0] + 0.8, hip[1] - 5.4), T(hip[0] + 0.6, hip[1] - 7.6)], "gold", 0.18,
               tones=[2, 3])
    for j in range(2):
        r.dot(*T(hip[0] + 1.6, hip[1] - 1.8 - 1.8 * j), "gold", 4 if j else 3, 0.2)
    # belt
    r.line(*T(hip[0] - 2.6, hip[1] - 0.6), *T(hip[0] + 2.6, hip[1] - 0.6), "blk", 0.15, tone=1)
    r.dot(*T(hip[0] + 0.2, hip[1] - 0.6), "gold", 4, 0.16)
    # epaulettes, with gold fringe
    r.ell(sh_f[0] - 0.4, sh_f[1] - 0.2, 1.5, 0.9, "gold", -0.4, bias=-0.2)
    r.ell(sh_n[0] - 0.2, sh_n[1] - 0.2, 1.8, 1.0, "gold", 2.2)
    r.dots([(sh_n[0] - 1.4 + i, sh_n[1] + 1.0) for i in range(4)], "gold", 1, 2.21)
    # head + hat (hand-pixelled)
    hx, hy = neck[0] + head_dx, neck[1]
    r.stamp(RING_HEAD[face], hx + 0.5, hy, 3.0, RING_LEG, pivot=(5, 6))
    if hat is None:
        r.stamp(TOPHAT, hx + 0.5, hy - 6.0, 3.5, RING_LEG, pivot=(5, 4))
    elif hat is not False:
        dx, dy, spin = hat
        hp = r.part(False, 3.5); r.hand.add(hp)
        rows = TOPHAT.strip("\n").split("\n")
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in "." or ch not in RING_LEG: continue
                u, v = i - 5, j - 4
                ca, sa = math.cos(math.radians(spin)), math.sin(math.radians(spin))
                m, t = RING_LEG[ch]
                r.put(hx + dx + u * ca - v * sa, hy - 6 + dy + u * sa + v * ca, 3.5, m, 0.5, hp, t)
    # near arm (+ whip)
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 3.4, 3.2, bend=1 if akimbo else -1)
    r.tube([sh_n, e1, hand], [1.3, 1.1, 1.0], "coat", 4.0, bias=0.15)
    r.dot(*lerp_pt(e1, hand, 0.8), "gold", 3, 4.05)   # gold cuff
    r.ell(hand[0], hand[1], 1.1, 1.1, "ivory", 4.1)
    if whip is None:
        # coiled on the hip
        cx, cy = T(hip[0] - 0.5, hip[1] + 1.0)
        r.ell(cx, cy, 2.0, 1.6, "lthr", 1.8, flat=None)
        r.ell(cx, cy, 0.9, 0.6, "lthr", 1.85, flat=1)
        r.polyline([hand, (hand[0] - 0.5, hand[1] + 2.0), (cx + 1.5, cy - 0.5)], "lthr", 4.2, tone=2)
    else:
        pts = whip_path(hand[0] + 0.5, hand[1] - 0.5, whip)
        r.tube(pts[:2], [0.8, 0.6], "lthr", 4.3)                          # handle
        r.polyline(pts[1:], "lthr", 4.2, tones=[3, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        if crack:
            x, y = pts[-1]
            star(r, x, y, crack)
    if hoop is not None:
        flaming_hoop(r, *hoop)
    if smear:
        for pts, tone in smear:
            r.polyline(pts, "ivory", 3.9, tone=tone)
    if extra: extra(r)
    return r.resolve()


def star(r, x, y, k=1):
    """Crack spark: k=1 big (gold/white star), 2 fading."""
    if k == 1:
        r.dot(x, y, "white", 4, 9)
        for d in (1, 2):
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                r.dot(x + dx, y + dy, "fire", 4 if d == 1 else 3, 9)
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            r.dot(x + dx, y + dy, "fire", 2, 8.9)
    else:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            r.dot(x + dx, y + dy, "fire", 2, 9)
        r.dot(x, y, "fire", 3, 9)


def arc_smear(r, cx, cy, R, a0, a1, mat="white", width=2, z=4.8):
    """Motion smear along an arc (deg a0 -> a1, the leading end at a1): brightest at the lead, thinning behind it."""
    n = max(3, int(abs(a1 - a0) / 6))
    for i in range(n + 1):
        t = i / n
        a = math.radians(lerp(a0, a1, t))
        tone = 1 if t < 0.35 else 2 if t < 0.75 else 3
        for w in range(width if t > 0.3 else 1):
            rr = R - w
            r.dot(cx + rr * math.cos(a), cy + rr * math.sin(a), mat, max(1, tone - w), z)


def flaming_hoop(r, cx, cy, rx, ry, phase=0, fire=1.0, z=5.0):
    """A gold hoop (ellipse ring) wreathed in flame tongues that lick upward."""
    n = 28
    for i in range(n):
        a = i / n * math.tau
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
        front = math.sin(a) > -0.1 or rx < 2.0
        r.dot(x, y, "gold", 3 if (math.cos(a) < 0 and math.sin(a) < 0) else 2, z + (0.5 if front else -6))
    if fire > 0:
        rnd = random.Random(phase * 31 + int(rx * 7))
        for i in range(0, n, 2):
            a = i / n * math.tau
            x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
            h = (1 + rnd.random() * 2.2) * fire
            front = math.sin(a) > -0.1
            zz = z + (0.6 if front else -6)
            r.dot(x, y - 1, "fire", 3, zz)
            if h > 1.4: r.dot(x + (1 if (i + phase) % 4 == 0 else 0), y - 2, "fire", 2, zz)
            if h > 2.4: r.dot(x, y - 3, "ember", 2, zz)


def ring_sheet(outdir):
    R = ringmaster
    idle = []
    for i in range(4):
        b = [0, 0.3, 0.6, 0.3][i]
        idle.append(R(bob=b, tails=[0.0, 0.1, 0.2, 0.1][i], hand=(2.6, -9.2 + b), hand2=(-3.6, -10.6 + b),
                      face="grin", akimbo=True))
    # Run: a swaggering strut, coat tails flying, whip coiled
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (2.8 * math.cos(ph), -max(0.0, 1.8 * math.sin(ph)))
        f2 = (-2.8 * math.cos(ph), -max(0.0, -1.8 * math.sin(ph)))
        run.append(R(lean=8, bob=-0.6 * abs(math.sin(ph)), feet=(f2, f1), tails=0.7 + 0.25 * math.sin(ph * 2),
                     hand=(4.2 + 1.5 * math.cos(ph), -11.0), hand2=(-2.5 - 1.5 * math.cos(ph), -11.5)))
    # Whip (7): raise the arm, whip loops back overhead (0-1), crack forward (2 smear, 3 = HIT, full reach), recoil,
    # whip falls slack (5), coil back (6)
    whip = [
        R(lean=-6, hand=(1.0, -16.5), hand2=(-4.0, -10.0), whip=[-120, -150, -175, 160, 140, 120, 110, 100], face="grin", tails=0.1),
        R(lean=-10, hand=(-1.0, -18.0), hand2=(-4.5, -9.5), whip=[-140, -170, 170, 150, 130, 110, 95, 85, 80], face="shout",
          tails=0.15),
        R(lean=4, hand=(4.0, -15.0), hand2=(-4.0, -10.0), whip=[-60, -30, -10, 10, 30, 60, 90, 110, 120, 125], face="shout",
          smear=[([(-3, -26), (3, -28), (9, -26)], 2)]),
        R(lean=10, hand=(6.5, -12.0), hand2=(-3.5, -11.0), whip=[-5, -3, -1, 0, 1, 2, 3, 4, 4, 5, 5], crack=1,
          face="shout", tails=0.4, feet=((-3.5, 0.0), (4.0, 0.0))),
        R(lean=8, hand=(6.0, -11.0), hand2=(-3.5, -11.0), whip=[10, 15, 20, 25, 32, 40, 50, 60, 70, 80, 90], crack=2,
          face="grin", tails=0.3, feet=((-3.5, 0.0), (4.0, 0.0))),
        R(lean=4, hand=(5.0, -10.0), hand2=(-3.5, -11.0), whip=[40, 60, 75, 90, 100, 170, 180, 185], face="grin",
          tails=0.15),
        R(lean=0, hand=(4.6, -11.0), hand2=(-3.6, -10.8), face="grin")]
    # Hoop (8): reach back (0), the hoop catches fire overhead (1-2), spin it on a finger (3), THROW (4), follow (5-7)
    hoop = [
        R(lean=-4, hand=(-4.0, -14.0), hand2=(-5.0, -10.0), hoop=(-5.5, -15.0, 1.2, 4.0, 0, 0.0), face="grin"),
        R(lean=-8, hand=(-0.5, -22.0), hand2=(-4.0, -10.0), hoop=(-1.0, -27.5, 4.0, 2.2, 1, 0.6), face="shout"),
        R(lean=-8, hand=(-0.5, -22.0), hand2=(-4.0, -10.0), hoop=(-1.0, -27.5, 3.0, 2.8, 2, 1.0), face="shout"),
        R(lean=-12, hand=(-3.0, -18.0), hand2=(-4.5, -9.5), hoop=(-5.5, -19.0, 1.5, 4.6, 3, 1.0), face="shout", tails=0.2),
        R(lean=12, hand=(7.0, -14.0), hand2=(-3.5, -11.0), hoop=(11.0, -15.5, 1.2, 4.6, 4, 1.0), face="shout", tails=0.5,
          feet=((-4.0, 0.0), (4.5, 0.0)), smear=[([(-3, -20), (2, -21), (7, -19)], 2)]),
        R(lean=10, hand=(6.0, -11.0), hand2=(-3.5, -11.0), face="grin", tails=0.4, feet=((-4.0, 0.0), (4.5, 0.0))),
        R(lean=4, hand=(5.0, -11.0), hand2=(-3.6, -10.8), face="grin", tails=0.2),
        R(lean=0, hand=(4.6, -11.4), hand2=(-3.6, -10.8), face="grin")]
    # Encore (5): the hoop came back clean: he doffs his hat to the crowd (lift 1, bow 2, back on 3) and grins
    encore = [R(hand=(3.5, -19.0), hand2=(-3.6, -10.8), face="grin"),
              R(hand=(4.0, -25.0), hand2=(-4.5, -10.0), face="grin", hat=(1.0, -3.0, 15), lean=-4),
              R(hand=(6.0, -21.0), hand2=(-5.0, -9.0), face="shout", hat=(4.0, 1.0, 40), lean=12, tails=0.4),
              R(hand=(3.5, -19.5), hand2=(-4.0, -10.0), face="grin", hat=(0.5, -1.0, 5), lean=2),
              R(hand=(4.6, -11.6), hand2=(-3.6, -10.6), face="grin")]
    # Death (4): whipped back (0), knees go, hat flies (1), falls (2), corpse with the hat rolled away (3)
    d0 = R(lean=-16, hand=(1.0, -16.0), hand2=(-6.0, -13.0), face="hurt", tails=0.3, hat=(-1.0, -2.0, -20))
    d1 = R(lean=-30, hips=(-1.0, -6.5), feet=((-3.0, 0.0), (2.5, 0.0)), hand=(1.0, -13.0), hand2=(-6.5, -9.0), face="dead",
           hat=(-4.0, -6.0, -60), knee_bend=-1)
    d2 = ring_corpse(0)
    corpse = ring_corpse(1)
    knock = R(lean=-18, hand=(1.5, -15.5), hand2=(-6.0, -12.5), face="hurt", tails=0.4, feet=((-4.0, 0.0), (2.0, 0.0)))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Whip", whip, [0.14, 0.12, 0.06, 0.08, 0.12, 0.12, 0.14]),
             ("Hoop", hoop, [0.12, 0.1, 0.1, 0.12, 0.06, 0.12, 0.14, 0.2]),
             ("Encore", encore, [0.06, 0.08, 0.12, 0.08, 0.08])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxRingmaster", anims, outdir, scale=6)


def ring_corpse(stage):
    r = Rig()
    # lying on his back, head left, legs right; the hat rolled off to the left
    y0 = -2.0
    r.tube([(3.0, y0), (7.5, y0 - (2.5 if stage == 0 else 1.0)), (10.5, y0 + 0.5)], [1.3, 1.1, 1.0], "ivory", 0.5)
    r.tube([(9.0, y0 + 0.3), (11.5, y0 + 0.6)], [1.2, 1.1], "blk", 0.6)
    r.tube([(3.0, y0 + 0.5), (8.0, y0 + 1.0)], [1.3, 1.1], "ivory", 0.2, bias=-0.3)
    r.poly([(-4.0, y0 - 2.4), (3.5, y0 - 2.6), (3.8, y0 + 1.6), (-4.0, y0 + 1.6)], "crim", 1.0, curve=0.3)
    r.poly([(-2.0, y0 - 2.6), (3.2, y0 - 2.6), (3.0, y0 - 1.2), (-2.0, y0 - 1.2)], "blk", 1.1)
    r.tube([(-2.0, y0 - 1.0), (1.0, y0 - 4.5 if stage == 0 else y0 - 3.0), (3.0, y0 - 5.0 if stage == 0 else y0 - 3.5)],
           [1.2, 1.0, 0.9], "crim", 1.5)
    r.stamp("""
.aww.
awWWm
wWmWm
wWCWm
wWCmm
.awm.
""", -6.5, 0.0, 2.0, RING_LEG, pivot=(2, 5))
    r.stamp("""
.kBbB.
kBbbbk
kCccnk
kBbbbK
""" if stage else """
..kk..
.kBbk.
kBbbbk
kCccnk
""", -12.0, 0.0, 2.0, RING_LEG, pivot=(3, 3))
    # the whip, slack across the floor
    r.polyline([(1.0, y0 - 3.5), (4.0, -0.4), (8.0, 0.0), (13.0, -0.6), (16.0, 0.0)], "lthr", 0.1, tone=1)
    return r.resolve()


# ================================================================== THE ROULETTE OUROBOROS (T3, replaces the Dice Rattler)
# A serpent that has swallowed its own tail round the brass turret of a roulette wheel. Its scales are the pockets:
# crimson / black, one green zero, gold frets between them. The body crawls endlessly through its own mouth (idle,
# run), so the head stays on top and readable. It lets go of its tail to bite, and spins itself as the wheel.
SNAKE_LEG = {"K": ("sblk", 0), "k": ("sblk", 1), "b": ("sblk", 2), "B": ("sblk", 3), "V": ("sblk", 4),
             "e": ("eye", 2), "E": ("eye", 4), "z": ("gold", 1), "g": ("gold", 2), "G": ("gold", 3), "H": ("gold", 4),
             "a": ("ivory", 1), "w": ("ivory", 3), "W": ("ivory", 4), "r": ("crim", 1), "R": ("crim", 2),
             "t": ("crim", 3), "x": ("scale", 0)}
SNAKE_HEAD = {
    # pivot = the back of the skull where the neck joins (col 1, row 6). The eye is a die's one: snake eyes.
    "bite": """
....g.gHg.....
...gGkgGkg....
..kBBVBBBBk...
.kBwWWBbbbbk..
kbBWeWbbbbbbk.
kbbwWabbbbbbbk
.kbbbbbkkkkkKK
..kwakwakwakK.
...kKKKKKKKK..
""",
    "open": """
....g.gHg.......
...gGkgGkg......
..kBBVBBBBk.....
.kBwWWBbbbbk....
kbBWeWbbbbbbk...
kbbwWabbbbkkKKw.
.kbbbbbkrrRRRta.
..kbbbkrrRtt....
...kbbbkkwkkw...
....kKKKKKK.....
""",
    "hiss": """
....g.gHg.....
...gGkgGkg....
..kBBVBBBBk...
.kBwWWBbbbbk..
kbBWEWbbbbbbk.
kbbwWabbbbkKKw
.kbbbbbkrRRtt.
..kbbbkkwkkw..
...kKKKKKKK...
""",
    "dead": """
..............
...gzkgzk.....
..kBbbbbBk....
.kBbbbbbbbk...
kbbaKabbbbbk..
kbbbabbbbbbbk.
.kbbbbbkkkkkKK
..kakkakkakK..
...kKKKKKKKK..
""",
}
POCKET = 30.0   # degrees of arc per pocket (12 round the ring)


def ring_mat(cx, cy, Rc, flow, r_body, zero_at=7, blur=False):
    """Material of the ring at (x, y): pockets alternating scale / sblk, green zero, gold frets, belly on the inside."""
    def f(x, y):
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        th = math.degrees(math.atan2(dy, dx))
        a = (th - flow) % 360.0
        k = int(a // POCKET)
        off = a - k * POCKET
        arc = math.radians(min(off, POCKET - off)) * d
        if d < Rc - r_body * 0.45:
            return "belly" if not blur else ("belly" if k % 2 else "ivory")
        if blur:
            return "scale" if d > Rc + 0.4 else ("gold" if d > Rc - 0.6 else "sblk")
        if arc < 0.55:
            return "gold"
        if k == zero_at: m = "felt"
        else: m = "scale" if k % 2 == 0 else "sblk"
        # the pocket number: an ivory tick on the outer scales, mid-pocket
        if abs(off - POCKET / 2) * math.pi / 180.0 * d < 0.6 and Rc + 0.8 < d < Rc + 2.0:
            return "ivory"
        return m
    return f


def ouroboros(flow=0.0, cx=0.0, cy=-16.0, Rc=13.0, sx=1.0, sy=1.0, head="bite", head_at=None, neck_from=-112.0,
              tail_to=-56.0, open_gap=False, hub=0.0, ball=None, blur=False, extra=None, lean=0.0, spark=None,
              ball_trail=None, dust=None, tongue=False, head_dy=0.0):
    """flow: how far the scales have crawled (deg). sx/sy squash the ring (rolling bumps, rearing).
    head_at: (x, y) of the head pivot (default: on top of the ring, biting the tail). neck_from / tail_to: the angles
    where the neck leaves the ring and where the tail ends (tail_to is inside the mouth when biting)."""
    r = Rig()
    rb = 3.3
    # the arc: from the neck (neck_from) going round anticlockwise (screen) to the tail tip (tail_to)
    span = (neck_from - tail_to) % 360.0
    pts, rad = [], []
    n = 72
    for i in range(n + 1):
        s = i / n
        th = math.radians(neck_from - s * span)
        pts.append((cx + Rc * sx * math.cos(th), cy + Rc * sy * math.sin(th)))
        taper = max(0.0, min(1.0, (1.0 - s) / 0.24))
        rad.append(max(0.7, rb * (0.82 + 0.18 * math.sin(math.pi * min(1.0, s * 1.3))) * (0.25 + 0.75 * taper)))
    mat = ring_mat(cx, cy, Rc * (sx + sy) / 2, flow, rb, blur=blur)
    r.tube(pts, rad, mat, 1.0, bias=0.05)
    # the brass turret: hub, four spokes to the inner track, spindle knob
    inner = Rc - rb - 0.4
    for k in range(4):
        a = math.radians(hub + 45 + 90 * k)
        r.tube([(cx, cy), (cx + inner * sx * math.cos(a), cy + inner * sy * math.sin(a))], [1.0, 0.6], "gold", -1.0, bias=-0.15)
    r.ell(cx, cy, 3.0 * sx, 3.0 * sy, "gold", -0.5, bias=0.1)
    r.ell(cx - 0.3, cy - 0.6, 1.2, 1.2, "ivory", -0.4, bias=0.2)
    # the ball on the inner track
    if ball is not None:
        a = math.radians(ball)
        bx, by = cx + (inner - 0.6) * sx * math.cos(a), cy + (inner - 0.6) * sy * math.sin(a)
        if ball_trail:
            for j in range(1, ball_trail + 1):
                aa = math.radians(ball - j * 14)
                r.dot(cx + (inner - 0.4) * sx * math.cos(aa), cy + (inner - 0.4) * sy * math.sin(aa), "white", 2 if j == 1 else 1, 3.0)
        r.ell(bx, by, 1.5, 1.5, "white", 3.1, flat=3)
        r.dot(bx - 0.5, by - 0.5, "white", 4, 3.2); r.dot(bx + 1, by + 1, "smoke", 1, 3.2)
    # neck + head
    th0 = math.radians(neck_from)
    nx, ny = cx + Rc * sx * math.cos(th0), cy + Rc * sy * math.sin(th0)
    hx, hy = head_at if head_at else (nx + 1.0, ny - 2.5 + head_dy)
    tang = (math.sin(th0), -math.cos(th0))          # direction the body leaves the ring (anticlockwise tangent, reversed)
    mid = (lerp(nx, hx, 0.5) - tang[0] * 2.0, lerp(ny, hy, 0.5) - tang[1] * 2.0)
    r.tube([(nx, ny), mid, (hx, hy)], [rb * 0.8, rb * 0.82, rb * 0.75], "sblk", 1.5)
    r.dots([(lerp(nx, hx, t) + 0.5, lerp(ny, hy, t) - 1.0) for t in (0.3, 0.6)], "gold", 3, 1.6)   # dorsal studs
    if head == "bite" and head_at is None:
        # the tail tip curls up into the closed jaws
        th1 = math.radians(tail_to)
        tx, ty = cx + Rc * sx * math.cos(th1), cy + Rc * sy * math.sin(th1)
        r.tube([(tx, ty), (tx - 0.2, ty - 1.6), (hx + 8.0, hy + 1.0)], [1.0, 0.9, 0.8], "sblk", 1.2)
    r.stamp(SNAKE_HEAD[head], hx, hy, 4.0, SNAKE_LEG, pivot=(1, 6))
    if tongue:
        r.polyline([(hx + 13, hy + 0), (hx + 15, hy - 0.5), (hx + 16, hy + 0.5)], "crim", 4.1, tone=3)
    if spark:
        for (x, y, k) in spark: star(r, x, y, k)
    if dust:
        dust_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def ouro_sheet(outdir):
    O = ouroboros
    idle = [O(flow=7.5 * i, ball=95 - 6 * math.sin(i / 4 * math.tau), head_dy=[0, -0.5, -1, -0.5][i]) for i in range(4)]
    # Run: the hoop rolls; the scales crawl two pockets per cycle, little bumps, dust kicked back
    run = []
    for i in range(6):
        bump = abs(math.sin(i / 6 * math.tau))
        run.append(O(flow=-10.0 * i, cx=0.0, cy=-16.0 - 1.0 * bump, sy=1.0 - 0.04 * (1 - bump), sx=1.0 + 0.03 * (1 - bump),
                     ball=70 + 18 * i, hub=-15 * i, dust=(-11.0, 0.0, i % 3, 0.8) if i % 3 == 0 else None))
    # Bite (7): lets go of its tail (0), rears the head back (1), STRIKE to full reach (2-3: the hit), worries (4),
    # pulls back (5), bites its tail again (6)
    bite = [
        O(head="open", head_dy=-1.5),
        O(head="open", neck_from=-125, tail_to=-40, head_at=(-6.0, -34.0)),
        O(head="open", neck_from=-100, tail_to=-35, head_at=(10.0, -26.0)),
        O(head="bite", neck_from=-80, tail_to=-30, head_at=(16.0, -20.0), spark=[(29.0, -19.0, 2)]),
        O(head="hiss", neck_from=-85, tail_to=-32, head_at=(14.0, -21.0), tongue=True),
        O(head="open", neck_from=-110, tail_to=-40, head_at=(2.0, -31.0)),
        O(head="bite", head_dy=-0.5)]
    # Spin (10): rears up (0), sets the turret turning and flicks the ball in (1), spins (2-6, the scales blur),
    # slows (7), the ball DROPS into a pocket at the top: the colour is called (8), holds (9)
    spin = [O(sy=0.92, sx=1.06, cy=-15.0, head="hiss", tongue=True, ball=95),
            O(flow=20, hub=40, ball=10, head="open", ball_trail=2)]
    for k in range(5):
        spin.append(O(flow=60 + 70 * k, hub=80 + 70 * k, ball=-60 - 100 * k, ball_trail=4, blur=k in (1, 2, 3),
                      head="open" if k % 2 else "hiss", sy=1.0 + 0.02 * (k % 2)))
    spin.append(O(flow=420, hub=420, ball=-160, ball_trail=2, head="hiss"))
    spin.append(O(flow=440, hub=440, ball=-90, head="hiss", tongue=True,
                  extra=lambda r: [r.dots([(-1, -31), (1, -31), (0, -32), (0, -30)], "white", 4, 9),
                                   r.dots([(-3, -31), (3, -31), (0, -34), (0, -28)], "fire", 3, 9)]))
    spin.append(O(flow=440, hub=440, ball=-90, head="bite"))
    # Death (4): struck (0), the tail slips out of its mouth (1), the hoop topples (2), a slack coil, the ball rolled out (3)
    d0 = O(head="hiss", sx=1.06, sy=0.94, cy=-15.0, head_dy=-1)
    d1 = O(head="open", neck_from=-120, tail_to=-20, head_at=(-9.0, -31.0), sy=0.85, cy=-14.0)
    d2 = ouro_corpse(0)
    corpse = ouro_corpse(1)
    knock = O(head="hiss", sx=0.9, sy=1.05, cx=-1.0, head_dy=-1.5, flow=10)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.07] * 6),
             ("Bite", bite, [0.12, 0.12, 0.05, 0.1, 0.12, 0.1, 0.12]),
             ("Spin", spin, [0.14, 0.1, 0.07, 0.06, 0.06, 0.06, 0.07, 0.1, 0.2, 0.2])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxRoulette", anims, outdir, scale=5)


def ouro_corpse(stage):
    r = Rig()
    # the body lies in a loose S on the floor
    pts = [(-16, -2), (-11, -4.5), (-5, -2.5), (0, -1.5), (5, -3.5), (10, -4.5), (14, -2.5)] if stage else \
          [(-14, -6), (-10, -10), (-4, -6), (0, -3), (5, -5), (10, -6), (14, -3)]
    rad = [0.9, 2.6, 3.0, 3.1, 3.0, 2.8, 2.6]
    seq = lambda x, y: ("gold" if (int(x) % 5 == 0) else ("scale" if (int(x) // 5) % 2 else "sblk"))
    r.tube(pts, rad, seq, 1.0)
    r.stamp(SNAKE_HEAD["dead"], 14.0, -1.0 if stage else -2.0, 3.0, SNAKE_LEG, pivot=(1, 5))
    r.ell(-4.0, -6.5 if not stage else -6.0, 2.6, 2.6, "gold", 2.0)
    r.ell(-20.0 if stage else -18.0, -1.4, 1.4, 1.4, "ivory", 2.0, bias=0.2)
    return r.resolve()


# ================================================================== GRAND JESTER (T3): the masque of two faces
# A lanky court fool with a split-motley costume and a marotte (a fool's sceptre with a little carved head). He wears
# one of two masks, COMEDY (white and gold, grinning) or TRAGEDY (blue, weeping); the marotte's head wears the other.
# Turning the mask swaps them: the face he wears tells the hero how he will fight.
def harl(ox, oy, size=3.0, a="crim", b="blk", ang=0.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def f(x, y):
        dx, dy = x - ox, y - oy
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        return a if (math.floor((u + v) / size) + math.floor((u - v) / size)) % 2 == 0 else b
    return f


JEST_LEG = {"F": ("crim", 3), "a": ("ivory", 1), "w": ("ivory", 2), "W": ("ivory", 3), "X": ("ivory", 4), "m": ("blk", 0),
            "n": ("crim", 1), "C": ("crim", 3), "g": ("gold", 2), "G": ("gold", 4), "z": ("gold", 1),
            "t": ("tear", 1), "T": ("tear", 2), "U": ("tear", 3), "u": ("tear", 4), "k": ("tear", 0),
            "s": ("smoke", 2), "S": ("smoke", 3)}
MASK = {
    "comedy": """
..aWWw..
.aWXWWw.
aWmWWmWw
aFWWWWFg
gWnWWnWw
.aWnnWWa
..awwwa.
""",
    "tragedy": """
..tTTt..
.tTuTTt.
tTkTTkTt
tTTUTTTg
gTTkkkTt
.tkTTTkt
..ttTtt.
""",
    "blur": """
..aSSs..
.aSWSSs.
aSSSSSSs
aSWSSSSg
gSSSSSSs
.aSsSsSa
..asssa.
""",
    "side": """
..aw....
.aWw....
aWWwg...
aWWWg...
gWWwg...
.aWwa...
..aw....
""",
    "dead": """
..aWWw..
.aWXWWw.
aWmWmWWw
aWWmWmWg
gWWWWWWw
.aWmmmWa
..awwwa.
""",
}
MINI = {"comedy": """
gWg
WWW
anW
""", "tragedy": """
gTg
TkT
tkt
"""}


def jester_hat(r, x, y, sway=0.0, lift=0.0, z=3.6, spin=0.0):
    """Three floppy points, each ending in a gold bell. (x, y) = the forehead band centre. sway: lag of the points
    (+ = they trail to the left, as when he moves right)."""
    band = r.part(False, z)
    r.tube([(x - 3.6, y), (x + 3.4, y + 0.4)], [1.0, 1.0], "gold", z + 0.2)
    # cap dome
    r.ell(x - 0.2, y - 1.8, 3.6, 2.2, "blk", z, bias=0.05)
    pts = [  # (base, mid, tip, mat, depth)
        ((x - 2.2, y - 2.2), (x - 6.0 - sway, y - 4.5 + lift), (x - 8.5 - sway * 1.5, y - 1.0 + lift * 1.5), "crim", z - 0.4),
        ((x - 0.4, y - 3.2), (x - 1.4 - sway * 0.8, y - 6.2 - lift * 0.3), (x - 4.4 - sway * 1.2, y - 6.8 - lift * 0.2), "blk", z - 0.2),
        ((x + 1.8, y - 2.4), (x + 5.5 - sway * 0.6, y - 5.0 + lift), (x + 7.5 - sway, y - 1.8 + lift * 1.5), "crim", z + 0.1),
    ]
    for base, mid, tip, mat, zz in pts:
        r.tube([base, mid, tip], [1.8, 1.2, 0.6], mat, zz, bias=0.05)
        r.ell(tip[0], tip[1] + 1.2, 1.3, 1.3, "gold", zz + 0.05, bias=0.1)
        r.dot(tip[0], tip[1] + 2.4, "gold", 0, zz + 0.06)


def marotte(r, hx, hy, ang, face, z, ln=11.0):
    """The fool's sceptre held at (hx, hy) pointing along ang: gold-banded stick, little carved head with the other mask."""
    a = math.radians(ang)
    tx, ty = hx + ln * math.cos(a), hy + ln * math.sin(a)
    bx, by = hx - 2.0 * math.cos(a), hy - 2.0 * math.sin(a)
    r.tube([(bx, by), (tx, ty)], [0.8, 0.8], "wood", z)
    r.dot(lerp(bx, tx, 0.45), lerp(by, ty, 0.45), "gold", 3, z + 0.01)
    # mini hat points + head
    r.tube([(tx - 1.5, ty - 1.5), (tx - 3.4, ty - 2.6)], [0.9, 0.5], "crim", z + 0.02)
    r.tube([(tx + 1.5, ty - 1.5), (tx + 3.4, ty - 2.4)], [0.9, 0.5], "blk", z + 0.02)
    r.dot(tx - 3.5, ty - 1.6, "gold", 3, z + 0.03); r.dot(tx + 3.5, ty - 1.4, "gold", 3, z + 0.03)
    r.stamp(MINI[face], tx, ty, z + 0.05, JEST_LEG, pivot=(1, 1))
    return tx, ty


def grand_jester(lean=0.0, bob=0.0, feet=((-3.5, 0.0), (3.5, 0.0)), hand=(6.0, -19.0), hand2=(-5.0, -18.0),
                 mask="comedy", rod=-60.0, rod_hand="near", sway=0.0, lift=0.0, balls=(), smear=None, extra=None,
                 hips=None, knee=1, head_dx=0.0, head_dy=0.0, hat=True, spark=None, ruff_tilt=0.0):
    r = Rig()
    hip = hips or (0.0, -14.0 + bob)
    T = Xf(lean, hip)
    other = "tragedy" if mask in ("comedy", "dead") else "comedy"
    # legs: far (black) and near (crimson) pantaloons, thin tights, curled shoes with bells
    for k, f in enumerate(feet):
        hp = (hip[0] + (-0.8 if k == 0 else 0.9), hip[1])
        kn = ik(hp[0], hp[1], f[0], f[1] - 1.0, 7.2, 6.6, bend=-knee)
        z = -1.0 if k == 0 else 1.5
        mat = "blk" if k == 0 else "crim"
        r.ell(*lerp_pt(hp, kn, 0.35), 2.4, 3.2, mat, z, bias=-0.15 if k == 0 else 0.05, ang=math.degrees(math.atan2(kn[1] - hp[1], kn[0] - hp[0])) + 90)
        r.tube([kn, (f[0], f[1] - 1.0)], [0.9, 0.8], "crim" if k == 0 else "blk", z - 0.01, bias=-0.2 if k == 0 else 0.1)
        # shoe: a curled point
        sh = [(f[0] - 1.5, f[1] - 1.8), (f[0] + 2.0, f[1] - 1.2), (f[0] + 4.0, f[1] - 2.8), (f[0] + 3.4, f[1] - 0.1), (f[0] - 1.5, f[1])]
        r.poly(sh, "blk" if k == 1 else "crim", z + 0.02, bias=0.1 if k else -0.2)
        r.dot(f[0] + 3.8, f[1] - 2.9, "gold", 3 if k else 2, z + 0.03)
    # torso: harlequin doublet, a gold belt with a bell, the points of the jerkin hem
    sh_n, sh_f = T(hip[0] + 2.0, hip[1] - 9.6), T(hip[0] - 1.6, hip[1] - 9.6)
    neck = T(hip[0] + 0.6, hip[1] - 11.0)
    tor = [T(hip[0] - 3.2, hip[1] + 1.0), T(hip[0] + 3.6, hip[1] + 1.0), T(hip[0] + 3.6, hip[1] - 8.5),
           T(hip[0] + 2.0, hip[1] - 10.4), T(hip[0] - 2.0, hip[1] - 10.4), T(hip[0] - 3.4, hip[1] - 8.0)]
    # far arm first (behind)
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 5.0, 4.6, bend=-1)
    r.ell(*lerp_pt(sh_f, e2, 0.4), 1.9, 2.4, "blk", -0.6, bias=-0.2)
    r.tube([e2, hand2], [0.9, 0.8], "crim", -0.6, bias=-0.3)
    r.ell(hand2[0], hand2[1], 1.1, 1.1, "ivory", -0.55, bias=-0.15)
    if rod_hand == "far":
        marotte(r, hand2[0], hand2[1], rod, other, -0.7)
    r.poly(tor, harl(hip[0], hip[1], 3.0, "crim", "blk", ang=lean), 0.0, curve=0.9)
    for j in range(5):   # jerkin hem points
        bx = hip[0] - 3.0 + j * 1.6
        r.poly([T(bx, hip[1] + 0.6), T(bx + 1.6, hip[1] + 0.6), T(bx + 0.8, hip[1] + 2.6)], "crim" if j % 2 else "blk", 0.05,
               bias=-0.1)
    r.line(*T(hip[0] - 3.2, hip[1] - 1.2), *T(hip[0] + 3.6, hip[1] - 1.2), "gold", 0.2, tone=2)
    r.dot(*T(hip[0] + 1.0, hip[1] - 1.2), "gold", 4, 0.21)
    # ruff collar
    rx, ry = neck
    for i in range(9):
        a = math.radians(-180 + i * 22.5)
        r.ell(rx + 3.6 * math.cos(a) * 1.05, ry + 0.4 + 1.5 * math.sin(a), 1.4, 1.2, "ivory", 2.0 + 0.01 * i,
              bias=0.15 - 0.05 * (i % 2))
    # head: mask + hat
    hx, hy = rx + 1.0 + head_dx, ry - 1.0 + head_dy
    r.stamp(MASK[mask], hx, hy, 3.0, JEST_LEG, pivot=(4, 6))
    if hat:
        jester_hat(r, hx - 0.5, hy - 6.0, sway=sway, lift=lift)
    # near arm (puffy sleeve, glove) + marotte
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 5.0, 4.6, bend=-1)
    r.ell(*lerp_pt(sh_n, e1, 0.4), 2.0, 2.5, "crim", 4.0, bias=0.05)
    r.tube([e1, hand], [1.0, 0.9], "blk", 4.0, bias=0.1)
    r.ell(hand[0], hand[1], 1.2, 1.2, "ivory", 4.1, bias=0.1)
    if rod_hand == "near":
        marotte(r, hand[0], hand[1], rod, other, 4.2)
    for (bx, by, m) in balls:
        r.ell(bx, by, 1.6, 1.6, m, 5.0, bias=0.15)
    if smear:
        for sm in smear:
            if sm[0] == "arc":
                arc_smear(r, *sm[1:])
            else:
                pts, m, tn = sm
                r.polyline(pts, m, 4.9, tone=tn)
    if spark:
        for (x, y, k) in spark: star(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def lerp_pt(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))


BALLS = ("crim", "gold", "chipb")


def jest_sheet(outdir):
    G = grand_jester
    out = {}
    for mood in ("comedy", "tragedy"):
        idle = []
        for i in range(4):
            b = [0, -0.4, -0.8, -0.4][i]
            if mood == "comedy":
                # idle-juggles two balls in the off hand while the marotte rests on the shoulder
                bl = [((-5.0 + [0, 1, 2, 1][i], -24.0 - [0, 3, 5, 3][i], "crim")), ((-4.0 - [0, 1, 2, 1][i], -20.0 - [3, 1, 0, 1][i], "gold"))]
                idle.append(G(bob=b, mask=mood, sway=[0, 0.5, 1, 0.5][i], lift=[0, 0.4, 0.8, 0.4][i], hand=(5.5, -19.0 + b),
                              hand2=(-4.5, -18.5 + b - [0, 1, 1.5, 1][i]), rod=-65, balls=bl))
            else:
                # tragedy: hunched, marotte held two-handed like a club
                idle.append(G(bob=b + 1.0, lean=6, mask=mood, sway=[0, 0.3, 0.6, 0.3][i], lift=[1.2, 1.4, 1.6, 1.4][i],
                              hand=(4.0, -17.0 + b), hand2=(2.0, -16.5 + b), rod=-100, knee=1,
                              feet=((-4.0, 0.0), (4.0, 0.0))))
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            f1 = (3.5 * math.cos(ph), -max(0.0, 2.6 * math.sin(ph)))
            f2 = (-3.5 * math.cos(ph), -max(0.0, -2.6 * math.sin(ph)))
            kw = dict(lean=10, bob=-0.8 * abs(math.sin(ph)), feet=(f2, f1), mask=mood, sway=2.0 + 0.6 * math.sin(ph * 2),
                      lift=0.6 * math.cos(ph * 2))
            if mood == "comedy":
                run.append(G(hand=(5.0 + 1.5 * math.cos(ph), -18.0), hand2=(-3.5 - 1.5 * math.cos(ph), -17.0), rod=-55, **kw))
            else:
                run.append(G(hand=(4.5, -16.5), hand2=(2.5, -16.0), rod=-115, **kw))
        out[mood] = (idle, run)
    # Juggle (8, comedy): balls up (0-2), three lobs on 3, 4, 5 (each leaves the near hand), bow (6), recover (7)
    J = []
    J.append(G(mask="comedy", hand=(4.0, -17.0), hand2=(-3.0, -17.0), rod_hand="far", rod=120,
               balls=[(3.5, -19.0, "crim"), (-2.5, -19.0, "gold"), (0.5, -23.0, "chipb")]))
    J.append(G(mask="comedy", bob=0.6, hand=(4.0, -19.0), hand2=(-2.5, -21.0), rod_hand="far", rod=120, sway=0.5,
               balls=[(3.0, -26.0, "crim"), (-2.0, -31.0, "gold"), (1.5, -36.0, "chipb")]))
    J.append(G(mask="comedy", lean=-4, hand=(3.0, -22.0), hand2=(-3.0, -20.0), rod_hand="far", rod=120, sway=-0.5,
               balls=[(2.5, -24.0, "crim"), (-1.5, -33.0, "gold"), (5.0, -38.0, "chipb")]))
    for k in range(3):
        bl = [(4.0, -36.0, "chipb"), (-1.0, -30.0, "gold"), (2.0, -24.0, "crim")][k + 1:] if k < 2 else []
        J.append(G(mask="comedy", lean=8 + 3 * k, hand=(9.0, -20.0 + k), hand2=(-3.0, -19.0), rod_hand="far", rod=120,
                   sway=1.0 + k * 0.5, balls=[(12.5, -20.0 + k, BALLS[k])] + bl,
                   smear=[("arc", 5.0, -15.0 + k, 8.0, -150, -60, "white", 1)]))
    J.append(G(mask="comedy", lean=22, hand=(8.0, -12.0), hand2=(-5.0, -22.0), rod_hand="far", rod=-120, sway=3.0, lift=1.5,
               head_dx=1.0, head_dy=0.5))
    J.append(G(mask="comedy", lean=6, hand=(5.5, -18.0), hand2=(-4.5, -18.0), rod=-65, sway=1.0))
    # Bash (8, tragedy): raise the marotte two-handed (0-1), overhead (2), SMASH (3: the hit, x 14..22 at the floor),
    # shudder (4), drag it back (5-6), hunch (7)
    B = [G(mask="tragedy", lean=0, hand=(3.0, -20.0), hand2=(1.0, -20.0), rod=-110, sway=0.5, lift=1.0),
         G(mask="tragedy", lean=-10, hand=(0.5, -26.0), hand2=(-1.0, -25.5), rod=-115, sway=-1.0, lift=0.0),
         G(mask="tragedy", lean=-14, hand=(-1.0, -27.5), hand2=(-2.0, -26.5), rod=-150, sway=-2.0, lift=-0.5,
           smear=[("arc", 0.0, -24.0, 13.0, -30, -150, "smoke", 1)]),
         G(mask="tragedy", lean=18, hand=(8.0, -14.0), hand2=(6.0, -14.5), rod=20, sway=3.0, lift=2.0, head_dx=1,
           feet=((-5.0, 0.0), (6.0, 0.0)), smear=[("arc", 2.0, -21.0, 16.0, -150, 15, "white", 2)],
           spark=[(20.0, -4.0, 1)]),
         G(mask="tragedy", lean=20, hand=(8.0, -13.0), hand2=(6.0, -13.5), rod=30, sway=2.5, lift=2.5, head_dx=1,
           feet=((-5.0, 0.0), (6.0, 0.0)), spark=[(20.0, -3.0, 2)]),
         G(mask="tragedy", lean=12, hand=(6.0, -14.0), hand2=(4.0, -14.5), rod=10, sway=1.5, lift=2.0,
           feet=((-4.5, 0.0), (5.0, 0.0))),
         G(mask="tragedy", lean=8, hand=(5.0, -16.0), hand2=(3.0, -16.0), rod=-40, sway=1.0, lift=1.5),
         G(mask="tragedy", lean=6, bob=1.0, hand=(4.0, -17.0), hand2=(2.0, -16.5), rod=-100, sway=0.5, lift=1.2)]
    # Flip (10): turn the mask. Hands to the face (0), the head whips round (1-4: side, blur, side), the other mask snaps
    # on (5), the marotte spins to the other side (6), TA-DA arms wide (7-8: the turn resolves), settle (9)
    def flip(src, dst):
        F = [G(mask=src, hand=(5.0, -25.0), hand2=(3.5, -24.5), rod=-80, sway=0.5),
             G(mask="side", hand=(4.0, -26.0), hand2=(2.0, -25.5), rod=-60, sway=-2.0, lift=-1.0, head_dx=-1),
             G(mask="blur", hand=(4.0, -26.0), hand2=(2.0, -25.5), rod=-30, sway=-3.5, lift=-2.0,
               smear=[("arc", 1.0, -30.0, 7.0, 150, 250, "white", 1)]),
             G(mask="blur", hand=(4.0, -26.0), hand2=(2.0, -25.5), rod=0, sway=3.5, lift=-2.0,
               smear=[("arc", 1.0, -30.0, 7.0, 30, -70, "white", 1)]),
             G(mask="side", hand=(4.5, -25.0), hand2=(2.5, -25.0), rod=30, sway=2.0, lift=-1.0, head_dx=-1),
             G(mask=dst, hand=(5.0, -24.0), hand2=(3.5, -23.5), rod=60, sway=1.0, lift=0.5),
             G(mask=dst, hand=(6.0, -20.0), hand2=(-4.0, -20.0), rod=150, sway=0.5, lift=0.5,
               smear=[("arc", 6.0, -20.0, 10.0, 80, -20, "white", 1)]),
             G(mask=dst, lean=-6, bob=-1.0, hand=(9.0, -27.0), hand2=(-8.0, -27.0), rod=-70, sway=-1.0, lift=-1.5,
               feet=((-4.5, 0.0), (4.5, 0.0)), spark=[(-10.0, -31.0, 1), (11.0, -31.0, 1)]),
             G(mask=dst, lean=-4, bob=-0.5, hand=(9.0, -26.0), hand2=(-8.0, -26.0), rod=-70, sway=-0.5, lift=-1.0,
               feet=((-4.5, 0.0), (4.5, 0.0)), spark=[(-10.0, -30.0, 2), (11.0, -30.0, 2)]),
             out[dst][0][0] if False else G(mask=dst, hand=(5.5, -19.0), hand2=(-4.5, -18.5), rod=-65)]
        return F
    flip_ct = flip("comedy", "tragedy")
    flip_tc = flip("tragedy", "comedy")
    # Death (4): the masks crack (0), staggers (1), falls (2), corpse with both masks on the floor (3)
    d0 = G(mask="dead", lean=-14, hand=(2.0, -26.0), hand2=(-7.0, -24.0), rod=-140, sway=-2.0, lift=-1.0)
    d1 = G(mask="dead", lean=-28, hips=(-1.5, -10.0), feet=((-3.0, 0.0), (3.0, 0.0)), knee=-1, hand=(-3.0, -22.0),
           hand2=(-9.0, -16.0), rod_hand="none", sway=-3.0, lift=2.0)
    d2 = jest_corpse(0)
    corpse = jest_corpse(1)
    knock = G(mask="comedy", lean=-18, hand=(3.0, -24.0), hand2=(-7.0, -22.0), rod=-130, sway=-2.5, lift=-1.0,
              feet=((-5.0, 0.0), (2.5, 0.0)))
    ci, cr = out["comedy"]; ti, tr = out["tragedy"]
    anims = [("Idle", ci, [0.14, 0.12, 0.14, 0.12]), ("Run", cr, [0.075] * 6),
             ("IdleSad", ti, [0.16, 0.14, 0.16, 0.14]), ("RunSad", tr, [0.08] * 6),
             ("Juggle", J, [0.14, 0.12, 0.12, 0.06, 0.06, 0.06, 0.16, 0.14]),
             ("Bash", B, [0.14, 0.14, 0.1, 0.06, 0.1, 0.12, 0.12, 0.14]),
             ("Flip", flip_ct, [0.1, 0.06, 0.05, 0.05, 0.06, 0.08, 0.1, 0.16, 0.14, 0.2]),
             ("FlipBack", flip_tc, [0.1, 0.06, 0.05, 0.05, 0.06, 0.08, 0.1, 0.16, 0.14, 0.2])]
    anims += tail_anims(ci[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxGrandJester", anims, outdir, scale=4)


def jest_corpse(stage):
    r = Rig()
    y0 = -2.2
    # sprawled on his back: legs to the right, head left, hat points splayed
    r.ell(-1.0, y0, 5.5, 2.4, harl(0, 0, 3.0), 1.0)
    r.ell(5.5, y0 + 0.4, 2.6, 1.8, "crim", 0.8)
    r.tube([(7.0, y0 + 0.5), (12.5, y0 - (3.0 if stage == 0 else 1.0)), (15.0, y0 - (1.0 if stage == 0 else 0.0))], [0.9, 0.8, 0.8], "blk", 0.9)
    r.ell(5.0, y0 - 1.0, 2.4, 1.8, "blk", 0.7, bias=-0.2)
    r.tube([(6.0, y0 - 1.0), (11.0, y0 + 1.5)], [0.9, 0.8], "crim", 0.6, bias=-0.2)
    for i in range(5):
        r.ell(-7.0, y0 - 2.5 + i * 1.2, 1.2, 1.0, "ivory", 1.5 + i * 0.01)
    r.stamp(MASK["dead"], -10.5, 0.0, 2.0, JEST_LEG, pivot=(4, 6))
    r.tube([(-12.0, -3.0), (-17.0, -5.0 if stage == 0 else -1.5), (-19.0, -1.5 if stage == 0 else -0.5)], [1.6, 1.0, 0.6], "crim", 1.8)
    r.ell(-19.0, -0.8, 1.2, 1.2, "gold", 1.9)
    # the marotte fallen beside him, its tragedy face up
    r.tube([(2.0, -0.6), (12.0, -0.8)], [0.7, 0.7], "wood", 0.2)
    r.stamp(MINI["tragedy"], 13.5, -1.5, 0.3, JEST_LEG, pivot=(1, 1))
    if stage == 0:
        dust_puff(r, 0.0, 0.0, 1, 1.4)
    return r.resolve()


# ================================================================== HIGH ROLLER (T3): the die-bellied demon gambler
# A squat, heavy demon whose whole torso is a loaded die in an open pinstripe waistcoat: fedora with the horns through
# the brim, a cigar, a tower of chips in one fist. The belly's front face carries six empty gold-rimmed pip sockets:
# FxJinxStake lights them (1-6) to show what he has riding on the pot.
ROLL_LEG = {"k": ("plum", 0), "d": ("plum", 1), "r": ("plum", 2), "R": ("plum", 3), "L": ("plum", 4),
            "Y": ("fire", 4), "y": ("fire", 3), "m": ("blk", 0), "W": ("ivory", 3), "w": ("ivory", 2),
            "K": ("blk", 0), "b": ("blk", 1), "B": ("blk", 2), "V": ("blk", 3), "n": ("gold", 1), "C": ("gold", 3),
            "c": ("lthr", 2), "e": ("ember", 3), "g": ("gold", 2), "G": ("gold", 4)}
ROLL_HEAD = {
    "grin": """
.krRRrk..
krRLRRRr.
rRYmRYmrk
rRRRRRRRk
drWmWmWck
.kddrrdk.
""",
    "chomp": """
.krRRrk..
krRLRRRr.
rRmmRmmrk
rRRRRRRRk
drWWWWWck
.kddrrdk.
""",
    "shout": """
.krRRrk..
krRLRRRr.
rRYmRYmrk
rRRmmmRRk
drmCCCmrk
.kdWWWdk.
""",
    "dazed": """
.krRRrk..
krRLRRRr.
rRwmRwmrk
rRRRRRRRk
drRmmmRrk
.kddrrdk.
""",
}
FEDORA = """
...KBVVBK...
..KBVBBBBK..
..KnCCCCnK..
KKBVVBBBBBKK
"""


def chip_stack(r, x, y, n, z, lean=0.0):
    """A tower of n poker chips (alternating colours) standing on (x, y)."""
    cols = ["crim", "chipb", "gold", "ivory", "crim", "chipb", "gold"]
    for i in range(n):
        cx = x + lean * i
        cy = y - i * 1.6
        r.ell(cx, cy, 2.2, 1.0, cols[i % len(cols)], z + 0.01 * i, bias=0.15)
        r.dot(cx - 1, cy, "ivory", 3, z + 0.01 * i + 0.005)


def high_roller(lean=0.0, bob=0.0, die_rot=(0.0, 30.0, 0.0), feet=((-4.0, 0.0), (4.0, 0.0)), hand=(10.0, -18.0),
                hand2=(-9.0, -14.0), stack=5, stack_at="hand", face="grin", smoke=0, hat=None, extra=None,
                chips=(), smear=None, legs_bend=1, body_dy=0.0, ember=True, spark=None, dice=1):
    r = Rig()
    by = -7.5 + bob + body_dy
    bc = (0.0, by - 6.5)                     # centre of the belly die
    # goat legs + hooves (behind the die)
    for k, f in enumerate(feet):
        hp = (f[0] * 0.6 + (-0.5 if k == 0 else 0.5), by)
        kn = (lerp(hp[0], f[0], 0.5) - 1.6 * legs_bend, lerp(hp[1], f[1], 0.5))
        z = -1.0 if k == 0 else 0.5
        r.tube([hp, kn, (f[0], f[1] - 1.5)], [2.3, 1.7, 1.3], lambda x, y: "blk" if (x + 200) % 3 else "coat", z,
               bias=-0.3 if k == 0 else -0.05)
        r.poly([(f[0] - 1.6, f[1] - 2.0), (f[0] + 1.8, f[1] - 2.0), (f[0] + 2.2, f[1]), (f[0] - 1.6, f[1])], "horn", z + 0.01,
               bias=-0.1 if k == 0 else 0.15)
    # tail with a little pip tip
    r.tube([(-6.0, by - 2.0), (-10.0, by - 1.0), (-12.0, by - 4.0), (-11.0, by - 6.5)], [1.0, 0.8, 0.6, 0.5], "plum", -2.0, bias=-0.2)
    r.ell(-11.0, by - 7.5, 1.2, 1.2, "ivory", -1.9, bias=0.1)
    # far arm
    sh_f = (bc[0] - 5.0, bc[1] - 4.5)
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 5.0, 5.0, bend=1)
    r.tube([sh_f, e2, hand2], [2.2, 1.8, 1.6], "plum", -0.8, bias=-0.35)
    r.ell(hand2[0], hand2[1], 1.8, 1.7, "plum", -0.75, bias=-0.25)
    r.dot(hand2[0] + 1, hand2[1], "gold", 3, -0.7)   # a ring
    if dice:
        die3(r, hand2[0] - 0.5, hand2[1] - 2.2, 2.6, 0, 30 + dice * 40, dice * 25, z=-0.65, pips=False)
        die3(r, hand2[0] + 1.6, hand2[1] - 2.6, 2.6, 0, 60 - dice * 30, -dice * 20, z=-0.64, pips=False)
    # the belly: a fat-cat paunch in a crimson brocade waistcoat under a black pinstripe jacket, gold watch chain
    T = Xf(lean, (0.0, by))
    r.ell(*T(bc[0] - 0.6, bc[1] - 0.5), 7.4, 7.6, lambda x, y: "blk" if (x + 200) % 3 else "coat", -0.2, bias=-0.05)
    r.ell(*T(bc[0] + 1.0, bc[1] + 0.4), 5.8, 6.6, lambda x, y: "crim" if (x + y + 200) % 4 else "scale", 0.0, bias=0.05)
    r.poly([T(bc[0] - 1.6, bc[1] - 7.0), T(bc[0] + 3.6, bc[1] - 7.0), T(bc[0] + 1.2, bc[1] - 2.0)], "ivory", 0.3, bias=0.1)
    for side, xx in ((-1, -2.6), (1, 4.6)):
        r.poly([T(bc[0] + xx - 1.2, bc[1] - 7.2), T(bc[0] + xx + 1.2, bc[1] - 7.2), T(bc[0] + 1.0 + side * 0.4, bc[1] - 1.6)],
               "blk", 0.35, bias=0.1 if side < 0 else -0.1)
    for j in range(3):
        r.dot(*T(bc[0] + 1.6, bc[1] - 0.8 + 2.4 * j), "gold", 4 if j == 0 else 3, 0.4)
    # head, hat, horns, cigar
    hx, hy = T(bc[0] + 1.2, bc[1] - 6.6)
    r.stamp(ROLL_HEAD[face], hx, hy, 2.0, ROLL_LEG, pivot=(4, 5))
    hat_at = (hx - 0.5, hy - 6.4)
    for side in (-1, 1):
        base = (hat_at[0] + side * 3.6, hat_at[1] + 2.4)
        r.tube([base, (base[0] + side * 2.4, base[1] - 2.0), (base[0] + side * 2.0, base[1] - 4.6)], [1.1, 0.8, 0.4], "ivory",
               2.6 if side > 0 else 1.6, bias=-0.1 if side < 0 else 0.1)
    if hat is None:
        r.stamp(FEDORA, *hat_at, 2.5, ROLL_LEG, pivot=(6, 2))
    elif hat:
        r.stamp(FEDORA, hat_at[0] + hat[0], hat_at[1] + hat[1], 2.5, ROLL_LEG, pivot=(6, 2))
    cg = (hx + 4.0, hy - 1.0)
    r.tube([cg, (cg[0] + 3.4, cg[1] - 1.0)], [0.7, 0.7], "lthr", 2.6)
    if ember:
        r.dot(cg[0] + 4.2, cg[1] - 1.2, "ember", 3, 2.7)
    for j in range(smoke):
        r.dot(cg[0] + 4.0 + [0, 1, 0, -1, 0][j % 5], cg[1] - 3.0 - 1.6 * j, "smoke", 3 - j // 2, 2.8)
    # near arm + chip stack
    sh_n = T(bc[0] + 5.0, bc[1] - 4.0)
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 5.2, 5.0, bend=1)
    r.tube([sh_n, e1, hand], [2.4, 2.0, 1.8], "plum", 3.0, bias=0.05)
    r.ell(hand[0], hand[1], 2.0, 1.8, "plum", 3.05, bias=0.1)
    r.dot(hand[0] - 0.5, hand[1] + 1, "gold", 4, 3.1)
    if stack and stack_at == "hand":
        chip_stack(r, hand[0] + 0.5, hand[1] - 2.2, stack, 3.2)
    for (x, y, m, edge) in chips:
        if edge:
            r.ell(x, y, 0.8, 1.8, m, 5.0, bias=0.2)
        else:
            r.ell(x, y, 1.9, 1.0, m, 5.0, bias=0.2); r.dot(x - 1, y, "ivory", 3, 5.01)
    if smear:
        for sm in smear:
            arc_smear(r, *sm)
    if spark:
        for (x, y, k) in spark: star(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def roller_sheet(outdir):
    H = high_roller
    idle = [H(bob=[0, 0.3, 0.6, 0.3][i], hand=(10.0, -18.0 + [0, 0.3, 0.6, 0.3][i]), smoke=[1, 2, 3, 2][i], dice=i + 1,
              face="grin" if i != 2 else "chomp", hand2=(-9.0, -14.0 + [0, 1.0, 2.0, 1.0][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(H(lean=6 * math.sin(ph), bob=-1.0 * abs(math.sin(ph)), die_rot=(0.0, 30.0, 4 * math.sin(ph)),
                     feet=((-4.0 + 2.5 * math.cos(ph), -max(0, 1.6 * math.sin(ph))), (4.0 - 2.5 * math.cos(ph), -max(0, -1.6 * math.sin(ph)))),
                     hand=(10.0, -17.0 - 0.8 * math.sin(ph)), hand2=(-9.0, -13.5 + 0.8 * math.sin(ph)), smoke=1 + i % 3))
    # Flick (6): thumb cocked on a chip (0-1), FLICK: the chip leaves the thumb (2), it spins away (3), settle (4-5)
    flick = [H(hand=(9.0, -19.0), face="chomp", smoke=1, chips=[(11.0, -23.0, "crim", False)]),
             H(hand=(8.0, -21.0), face="chomp", smoke=2, lean=-3, chips=[(10.0, -25.5, "crim", True)]),
             H(hand=(11.5, -19.0), face="grin", smoke=2, lean=3, chips=[(17.0, -20.0, "crim", True)],
               smear=[(10.0, -15.0, 6.0, -140, -60, "white", 1)]),
             H(hand=(11.0, -18.0), face="grin", smoke=3, lean=2, chips=[(23.0, -21.0, "crim", False)]),
             H(hand=(10.5, -18.0), face="grin", smoke=3),
             H(hand=(10.0, -18.0), face="grin", smoke=2)]
    # AllIn (9): gathers the stack in both arms (0-2), heaves (3-4), SHOVES it onto the floor in front (5: the pot is
    # set), leans on it grinning (6-8)
    allin = [H(hand=(9.0, -17.0), hand2=(-4.0, -18.0), face="grin", smoke=2),
             H(hand=(7.0, -21.0), hand2=(-2.0, -21.0), face="chomp", smoke=2, lean=-4, stack=7),
             H(hand=(5.0, -23.0), hand2=(-3.0, -23.0), face="chomp", smoke=1, lean=-8, stack=7, body_dy=0.5),
             H(hand=(12.0, -15.0), hand2=(9.0, -15.5), face="shout", lean=8, stack=7, body_dy=-0.5),
             H(hand=(14.0, -9.0), hand2=(11.5, -9.5), face="shout", lean=14, stack=0, ember=True,
               chips=[(16.0, -12.0 + j * 1.8, ["crim", "chipb", "gold"][j % 3], j % 2 == 0) for j in range(5)],
               smear=[(6.0, -9.0, 10.0, -100, -10, "white", 2)]),
             H(hand=(14.5, -6.0), hand2=(12.0, -6.5), face="shout", lean=16, stack=0,
               chips=[(17.0 + (j % 3) * 2.2 - 2, -1.0 - (j // 3) * 1.6, ["crim", "chipb", "gold"][j % 3], False) for j in range(7)],
               spark=[(18.0, -6.0, 1)]),
             H(hand=(13.0, -7.0), hand2=(11.0, -8.0), face="grin", lean=12, stack=0, smoke=1,
               chips=[(17.0 + (j % 3) * 2.2 - 2, -1.0 - (j // 3) * 1.6, ["crim", "chipb", "gold"][j % 3], False) for j in range(7)]),
             H(hand=(11.0, -12.0), hand2=(-6.0, -15.0), face="grin", lean=6, stack=0, smoke=2),
             H(hand=(10.0, -16.0), hand2=(-9.0, -14.0), face="grin", stack=0, smoke=3)]
    # Bust (6, new): the hero hit him mid-pot: he reels (0-1), the hat pops (2), dazed wobble (3-4), recovers (5)
    bust = [H(face="dazed", lean=-10, hand=(6.0, -22.0), hand2=(-10.0, -20.0), stack=0, ember=False),
            H(face="dazed", lean=-14, hand=(4.0, -24.0), hand2=(-11.0, -21.0), stack=0, hat=(-1.0, -3.0), ember=False),
            H(face="dazed", lean=-8, hand=(6.0, -20.0), hand2=(-10.0, -17.0), stack=0, hat=(-3.0, -6.0), ember=False),
            H(face="dazed", lean=6, hand=(9.0, -16.0), hand2=(-8.0, -13.0), stack=0, hat=(-4.0, -1.0), ember=False,
              extra=lambda r: r.dots([(-3, -36), (2, -37), (6, -35)], "fire", 3, 9)),
            H(face="dazed", lean=-6, hand=(9.0, -16.0), hand2=(-8.0, -13.0), stack=0, hat=(-2.0, 0.0), ember=False,
              extra=lambda r: r.dots([(-4, -35), (1, -38), (6, -36)], "fire", 3, 9)),
            H(face="chomp", hand=(10.0, -17.0), hand2=(-9.0, -14.0), stack=1)]
    d0 = H(face="dazed", lean=-12, hand=(5.0, -23.0), hand2=(-10.0, -20.0), stack=0, ember=False,
           chips=[(14.0, -24.0, "crim", True), (7.0, -30.0, "gold", False)])
    d1 = H(face="dazed", lean=-24, hand=(2.0, -21.0), hand2=(-12.0, -15.0), stack=0, hat=(-6.0, -4.0), ember=False, body_dy=2.0,
           die_rot=(0.0, 26.0, -18.0), chips=[(15.0, -2.0, "crim", False), (11.0, -14.0, "gold", True)])
    d2 = roller_corpse(0)
    corpse = roller_corpse(1)
    knock = H(face="dazed", lean=-14, hand=(6.0, -21.0), hand2=(-11.0, -18.0), stack=3, die_rot=(0.0, 22.0, -8.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Flick", flick, [0.12, 0.1, 0.05, 0.1, 0.12, 0.13]),
             ("AllIn", allin, [0.12, 0.1, 0.1, 0.08, 0.05, 0.12, 0.12, 0.12, 0.13]),
             ("Bust", bust, [0.08, 0.1, 0.12, 0.14, 0.14, 0.16])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxHighRoller", anims, outdir, scale=4)


def roller_corpse(stage):
    r = Rig()
    # flat on his back, the paunch in the air, hooves up; his two dice rolled out showing snake eyes
    r.ell(0.5, -4.0, 7.6, 4.2, lambda x, y: "blk" if (x + 200) % 3 else "coat", 0.0, bias=-0.1)
    r.ell(1.0, -5.5 if stage == 0 else -5.0, 6.0, 4.4, lambda x, y: "crim" if (x + y + 200) % 4 else "scale", 0.5)
    for j in range(3):
        r.dot(-1.5 + 2.6 * j, -9.4 if stage == 0 else -8.9, "gold", 3, 0.6)
    for k, (kx, up) in enumerate(((6.0, 7.0), (8.0, 5.0))):
        r.tube([(kx, -3.0), (kx + 3.0, -3.0 - up * (1.0 if stage == 0 else 0.7)), (kx + 4.0, -3.5 - up * (1.0 if stage == 0 else 0.6))],
               [2.0, 1.5, 1.2], lambda x, y: "blk" if (x + 200) % 3 else "coat", 0.2 + k * 0.6, bias=-0.2 if k == 0 else 0.0)
        r.ell(kx + 4.4, -4.0 - up * (1.0 if stage == 0 else 0.6), 1.4, 1.2, "horn", 0.3 + k * 0.6)
    r.tube([(-4.0, -6.0), (-6.0, -9.0), (-4.0, -11.0 if stage == 0 else -9.0)], [1.8, 1.6, 1.4], "plum", 1.0)
    r.stamp(ROLL_HEAD["dazed"], -10.5, 0.0, 1.0, ROLL_LEG, pivot=(4, 5))
    r.stamp(FEDORA, -18.0, 0.0, 1.2, ROLL_LEG, pivot=(6, 3))
    for j in range(5 if stage else 3):
        x = 12.0 + j * 3.0
        r.ell(x, -1.0, 1.9, 1.0, ["crim", "chipb", "gold"][j % 3], 2.0 + j * 0.01, bias=0.2)
    for k, x in enumerate((-24.0, -28.5)):
        die3(r, x, -1.8, 3.4, 0, 0, 0, z=2.0, tilt=0.0, pip_faces=1, pip_min=1.0)
    return r.resolve()


def fx_stake(outdir):
    """FxJinxStake P0..P6: the High Roller's stake: a casino-red die face that floats over his hat showing 0-6 lit
    pips (2-frame loop, the pips pulse). Origin = the bottom centre of the die face (place it ~38 px over the feet)."""
    anims = []
    for n in range(7):
        frs = []
        for ph in range(2):
            r = Rig()
            die3(r, 0.0, -4.5, 7.0, 0, 0, 0, z=0.0, mat="rdie", pips=False, tilt=0.0)
            for (pu, pv) in PIPS[n] if n else []:
                r.dot(pu * 2.0, -4.5 + pv * 2.0, "white" if ph else "ivory", 4 if ph else 3, 1.0)
            frs.append(r.resolve())
        anims.append(("P%d" % n, frs, [0.4, 0.4]))
    img, man = pack("FxJinxStake", anims, 12, 12, (6, 10), outdir)
    preview(img, man, os.path.join(outdir, "FxJinxStake_preview.png"), scale=8)
    BUILT["FxJinxStake"] = {"cell": (12, 12), "feet": (6, 10), "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built FxJinxStake  cell 12x12")


# ================================================================== TIMING.md
SYNC = {
    "JinxDiceImp": {"Toss": [("little die leaves the hand at (12, -11); launch FxDie on the floor at (12, 0)", 3)],
                    "Roll": [("heave: the big die goes overhead", 1), ("spin (smears)", 2),
                             ("SLAM: the die lands at (8, -3); spawn FxDieFace at (8, 0)", 6), ("new die pops in under it", 7)]},
    "JinxRingmaster": {"Whip": [("crack: whip at full reach, tip + spark at (33, -12); hit box x 8..34, y -16..-8", 3)],
                       "Hoop": [("hoop catches fire overhead", 1), ("THROW: hoop leaves the hand at (11, -15)", 4)]},
    "JinxRoulette": {"Bite": [("lets go of its tail (the ring opens)", 0), ("STRIKE: jaws at x 24..30, y -23..-16 (box 16 x 10 at (22, -19))", 3),
                              ("bites its tail again", 6)],
                     "Spin": [("the turret starts turning, the ball is flicked in", 1), ("ball circling (blur 3-5)", 2),
                              ("the ball DROPS into the top pocket: resolve red / black / green zero (flash at (0, -31))", 8)]},
    "JinxGrandJester": {"Juggle": [("ball 1 leaves the hand at (12, -20)", 3), ("ball 2 at (12, -19)", 4), ("ball 3 at (12, -18)", 5)],
                        "Bash": [("SMASH: the marotte head lands at (18, -10), floor spark (20, -4); box 14 x 14 at (18, -7)", 3)],
                        "Flip": [("hands to the mask", 0), ("head whips round (1-4)", 1), ("the other mask is on", 5),
                                 ("TA-DA: the stance swap resolves (comedy -> tragedy)", 7)],
                        "FlipBack": [("TA-DA: the stance swap resolves (tragedy -> comedy)", 7)]},
    "JinxHighRoller": {"Flick": [("chip leaves the thumb at (17, -20)", 2)],
                       "AllIn": [("heave the stack", 3), ("SHOVE: the pot lands on the floor at (18, 0); FxJinxStake shows the stake 38 px up", 5)],
                       "Bust": [("hat pops off (the pot is busted)", 1), ("dazed (2-4)", 2)]},
}
NOTES = {
    "JinxDiceImp": "Flies: the die hovers 0.4-1 px over the feet point (T1 limit 16 px including the hover).",
    "JinxRoulette": "New T3 (replaces JinxRattler). The body crawls through its own mouth: Idle moves the scales 7.5 deg a "
                    "frame (one pocket per loop), Run 10 deg a frame (two pockets per loop), so both loops repeat without a jump.",
    "JinxGrandJester": "Idle/Run wear COMEDY, IdleSad/RunSad wear TRAGEDY; Juggle is the comedy basic, Bash the tragedy basic; "
                       "Flip goes comedy -> tragedy, FlipBack tragedy -> comedy.",
    "JinxHighRoller": "FxJinxStake P0..P6 (12 x 12, origin (6, 10)) floats over the fedora and shows the stake.",
}


def write_timing(outdir):
    L = ["# Jinx: sprite timing", "",
         "Generated by `tools/sprites/jinx_v2_rigs.py` (and the jinx_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet, x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). Every sheet is at final size (no ArtScale).", "",
         "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in BUILT.items():
        if n.startswith("Fx"): continue
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox()
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
          "  onto the stone ramp. Every attack has at least two wind-up frames before its first event; strike frames 0.05-0.06 s."]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


# ================================================================== build
JOBS = [("JinxDiceImp", imp_sheet), ("JinxRingmaster", ring_sheet), ("JinxRoulette", ouro_sheet),
        ("JinxGrandJester", jest_sheet), ("JinxHighRoller", roller_sheet), ("FxJinxStake", fx_stake)]


def all_jobs():
    """The jobs in this file plus those of the per-tier and effect modules (imported here: they import this module)."""
    import importlib
    jobs = list(JOBS)
    for mod in ("jinx_v2_t1", "jinx_v2_t2", "jinx_v2_t3", "jinx_v2_fx"):
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
    sys.modules["jinx_v2_rigs"] = sys.modules[__name__]   # the tier modules import this one by name: share its state
    main()
