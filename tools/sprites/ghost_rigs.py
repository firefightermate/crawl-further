"""GHOST FORMS + BLOB FODDER: every sprite sheet for ghosts_v1.

The blobs themselves are drawn by ghosts_v2_blobs.py (material renderer); this file runs them, and draws the goo
effects with its metaball engine (soft balls thresholded, height-mapped and lit from the top-left, the underside in the
gel's ink tone), plus the ghost portraits and auras with the shaded primitives from shaded_prims.

    python3 ghost_rigs.py [outdir] [--only Name,Name]

Sheets: BlobMote BlobSpitter BlobGel BlobBrute BlobTitan BlobKing (via ghosts_v2_blobs.py),
FX: FxGooGlob FxGooPuddle FxMergeBurst FxWisp FxHexBolt FxHexPuff FxBlobQuake FxBlobSpawn FxGooDrop FxGleanerAura
FxBinderAura FxPoltergeistAura, portraits: GhostWisp GhostGleaner GhostBinder GhostPoltergeist.
A full run (no --only) also runs ghost_forms.py: FormGleaner FormBinder FormPoltergeist, ModVioletPip, ModBadgeGem.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, SprRGB, PALETTE, pack, preview  # noqa: E402
from ghosts_v2_kit import selout_anims  # noqa: E402
from shaded_prims import ell, tube, line, chain, poly, P, dissolve  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_ghosts")


def hexc(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# runtime palette additions (this script only)
PALETTE.update({k: hexc(v) for k, v in {
    # ectoplasm gel, dark -> light (neutral grey-green so the per-player tint reads)
    '1': '262f30', '2': '394746', '3': '4c5e5a', '4': '637970', '5': '7f988a', '6': 'a6bea8', '7': 'd8eacf',
    # bone suspended in gel
    'l': '5c5844', 'j': '9a9372', 'J': 'cbc49c',
    # eyes + mouth
    'E': 'f0fde0', 'Z': 'a8e4b4', 'M': '161c1c',
    # vanilla hag ghost
    '8': '42464a', 'H': '565b56', 'I': '6a6e66', 'L': '868a7e', 'D': '546664', 'C': '657a76',
    '9': '6a6c46', 'f': '8e9160', 'd': 'aaac76', '0': 'c8c892', 'x': 'a17a6a', 'z': 'e0886a',
    # binder chains
    'Q': '2c625a', '+': '70ccb8', '=': 'c8fff0',
    # hex fire
    '~': 'd8ffa0', '^': '2a4426',
    # portrait background
    '#': '1c1c24', '%': '24242e', '&': '2d2d38',
}.items()})

GEL = "23456"
TH = 0.3
KR = math.sqrt(1 - math.sqrt(TH))


def norm3(x, y, z):
    m = math.sqrt(x * x + y * y + z * z) or 1.0
    return x / m, y / m, z / m


LIGHT = norm3(-0.9, -1.25, 1.35)
HALF = norm3(LIGHT[0], LIGHT[1], LIGHT[2] + 1.0)


def pick(ramp, l):
    n = len(ramp)
    i = int((l + 1.0) * 0.5 * n)
    return ramp[max(0, min(n - 1, i))]


LIGHTER = {'1': '2', '2': '3', '3': '4', '4': '5', '5': '6', '6': '6'}
DARKER = {'7': '6', '6': '5', '5': '4', '4': '3', '3': '2', '2': '2', '1': '1'}


# ================================================================== the gel engine
class Frame:
    """A rendered gel: pixels plus the interior mask so inner bones / eyes clip to the jelly."""

    def __init__(self, px, mask, inner, ndir):
        self.px = px; self.mask = mask; self.inner = inner; self.ndir = ndir

    def put(self, x, y, ch):
        self.px[P(x, y)] = ch

    def put_in(self, x, y, ch):
        k = P(x, y)
        if k in self.inner:
            self.px[k] = ch

    def glow(self, x, y, r=1.5):
        """Brighten the gel around a glowing point (ectoplasm glow)."""
        cx, cy = P(x, y)
        R = int(math.ceil(r))
        for yy in range(cy - R, cy + R + 1):
            for xx in range(cx - R, cx + R + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r and (xx, yy) in self.inner:
                    c = self.px.get((xx, yy))
                    if c in LIGHTER: self.px[(xx, yy)] = LIGHTER[c]

    def bone(self, x0, y0, x1, y1, lit=True):
        pts = line_px(*P(x0, y0), *P(x1, y1))
        for i, (x, y) in enumerate(pts):
            self.put_in(x, y, 'j' if (i % 3 or not lit) else 'J')
        for (x, y) in (pts[0], pts[-1]):
            self.put_in(x, y, 'J' if lit else 'j')
        # knobs: one extra pixel at each end, perpendicular
        (ax, ay), (bx, by) = pts[0], pts[-1]
        dx, dy = bx - ax, by - ay
        if abs(dx) >= abs(dy):
            self.put_in(ax, ay - 1, 'j'); self.put_in(bx, by + 1, 'l')
        else:
            self.put_in(ax - 1, ay, 'j'); self.put_in(bx + 1, by, 'l')

    def sprite(self, grid, x, y, inside=True):
        rows = grid.strip("\n").split("\n")
        h, w = len(rows), max(len(r) for r in rows)
        x, y = P(math.floor(x + 0.5), math.floor(y + 0.5))
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch in ". ": continue
                X, Y = P(x - w // 2 + i, y - h // 2 + j)
                if inside: self.put_in(X, Y, ch)
                else: self.put(X, Y, ch)

    def eye(self, x, y, size=1, state="open", look=1):
        x, y = P(x, y)
        if state == "none": return
        if size == 1:  # a tall pale slit: bright top, glow below, dark socket behind
            if state in ("open", "wide"):
                self.put(x, y, 'E'); self.put(x, y + 1, 'Z')
                self.put(x - 1, y, '2'); self.put(x - 1, y + 1, '2')
                if state == "wide": self.put(x, y - 1, 'Z')
            elif state == "blink":
                self.put(x, y + 1, '1'); self.put(x - 1, y + 1, '2')
            elif state == "squint":
                self.put(x, y + 1, 'Z'); self.put(x - 1, y + 1, '2'); self.put(x, y, '2')
            elif state == "dead":
                self.put(x, y, '1'); self.put(x, y + 1, '2')
        elif size == 2:
            if state in ("open", "wide"):
                self.glow(x + 0.5, y + 0.5, 2.2)
                self.put(x, y, 'E'); self.put(x + 1, y, 'E'); self.put(x, y + 1, 'Z'); self.put(x + 1, y + 1, 'E')
                self.put(x, y + 2, '2'); self.put(x + 1, y + 2, '2')
                if state == "wide": self.put(x, y - 1, 'Z'); self.put(x + 1, y - 1, 'Z')
            elif state == "blink":
                self.put(x, y + 1, '1'); self.put(x + 1, y + 1, '1')
            elif state == "squint":
                self.put(x, y + 1, 'Z'); self.put(x + 1, y + 1, 'E'); self.put(x, y, '2'); self.put(x + 1, y, '2')
            elif state == "dead":
                self.put(x, y, '1'); self.put(x + 1, y + 1, '1'); self.put(x + 1, y, '2'); self.put(x, y + 1, '2')
        else:  # 3: the Mote's one big eye: a round white with a pupil looking forward, in a dark socket
            sq = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
            if state in ("open", "wide", "squint"):
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if (dx, dy) not in sq and abs(dx) + abs(dy) < 4 and (x + dx, y + dy) in self.inner:
                            self.px[(x + dx, y + dy)] = DARKER.get(self.px.get((x + dx, y + dy), '3'), '2')
            if state in ("open", "wide"):
                for dx, dy in sq:
                    corner = abs(dx) + abs(dy) == 2
                    self.put(x + dx, y + dy, 'Z' if corner and state != "wide" else 'E')
                self.put(x + look, y, 'M')
                if state == "open": self.put(x + look, y + 1, '1')
            elif state == "blink":
                for dx in (-1, 0, 1): self.put(x + dx, y + 1, '1')
            elif state == "squint":
                for dx in (-1, 0, 1): self.put(x + dx, y, 'E')
                self.put(x + look, y, 'M'); self.put(x, y - 1, '2')
            elif state == "dead":
                for d in (-1, 0, 1):
                    self.put(x + d, y + d, '1'); self.put(x + d, y - d, '1')

    def glint(self, x, y, big=False):
        """Wet specular glint on the lit side of a lobe."""
        x, y = P(x, y)
        self.put_in(x, y, '7')
        if big:
            self.put_in(x + 1, y, '6'); self.put_in(x, y + 1, '6')

    def bubbles(self, pts):
        for (x, y) in pts:
            k = P(x, y)
            if k in self.inner and self.px.get(k) in '2345':
                self.px[k] = LIGHTER[self.px[k]]
                self.put_in(k[0] + 1, k[1] + 1, DARKER.get(self.px.get((k[0] + 1, k[1] + 1), '3'), '2'))

    def spr(self):
        return Spr({k: v for k, v in self.px.items() if k[1] <= 0})


class Goo:
    def __init__(self):
        self.balls = []

    def ball(self, x, y, rx, ry=None):
        ry = rx if ry is None else ry
        rx, ry = max(0.55, rx), max(0.55, ry)
        self.balls.append((x, y, rx / KR, ry / KR, min(rx, ry)))

    def strand(self, pts, radii, step=0.9):
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            r0, r1 = radii[i], radii[i + 1]
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
            last = i == len(pts) - 2
            for k in range(n + (1 if last else 0)):
                t = k / n
                self.ball(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r0 + (r1 - r0) * t)

    def field(self, x, y):
        F = 0.0; R = 0.0
        for (cx, cy, fx, fy, r) in self.balls:
            dx = (x - cx) / fx; dy = (y - cy) / fy
            d2 = dx * dx + dy * dy
            if d2 < 1.0:
                f = (1.0 - d2) ** 2
                F += f; R += f * r
        return F, (R / F if F > 0 else 1.0)

    def render(self, cut=True, edge='1', ramp=GEL, bias=0.0, rim=1.0, spec=False, zr=None):
        if not self.balls:
            return Frame({}, set(), set(), {})
        x0 = int(math.floor(min(b[0] - b[2] for b in self.balls))) - 1
        x1 = int(math.ceil(max(b[0] + b[2] for b in self.balls))) + 1
        y0 = int(math.floor(min(b[1] - b[3] for b in self.balls))) - 1
        y1 = int(math.ceil(max(b[1] + b[3] for b in self.balls))) + 1
        Z = {}
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                F, R = self.field(x, y)
                if F > TH:
                    Z[(x, y)] = (zr if zr else R * 1.15) * math.sqrt(min(1.0, (F - TH) / (1.0 - TH)))
        mask = {k for k in Z if not cut or k[1] <= 0}
        px = {}; ndir = {}
        for (x, y) in mask:
            gx = (Z.get((x + 1, y), 0.0) - Z.get((x - 1, y), 0.0)) * 0.5
            gy = (Z.get((x, y + 1), 0.0) - Z.get((x, y - 1), 0.0)) * 0.5
            nx, ny, nz = norm3(-gx, -gy, 1.0)
            ndir[(x, y)] = (nx, ny, nz)
            lam = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
            fres = 1.0 - nz
            # translucent jelly: a darker deep core, a lit skin toward the light, and a backlit rim lower-right
            l = -0.42 + 1.1 * (lam - LIGHT[2]) + bias
            l += 0.55 * fres * max(0.0, -(0.6 * nx + 0.8 * ny))
            l += rim * 1.5 * fres * max(0.0, 0.45 * nx + 0.9 * ny) ** 2
            ch = pick(ramp, l)
            if spec:
                sp = (nx * HALF[0] + ny * HALF[1] + nz * HALF[2]) ** 24
                if sp > 0.72: ch = '7'
                elif sp > 0.5 and ch in '456': ch = LIGHTER[ch]
            px[(x, y)] = ch
        inner = set()
        shade = {'1': '2', '2': '2', '3': '3'}.get(edge, edge)
        for (x, y) in mask:
            if all(n in mask for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                inner.add((x, y))
            elif edge:
                # selective outline: the underside sits in the gel's ink tone, the right side in its shadow tone, and
                # the lit top / left skin keeps its own tone (no dark ring)
                if (x, y + 1) not in mask:
                    px[(x, y)] = edge
                elif (x + 1, y) not in mask:
                    px[(x, y)] = min(px[(x, y)], shade)
        return Frame(px, mask, inner, ndir)


def drops(fr, pts, ch='5'):
    """Loose single-pixel droplets with a dark underside."""
    for (x, y) in pts:
        x, y = P(x, y)
        fr.px[(x, y)] = ch
        fr.px.setdefault((x, y + 1), '1')


# ================================================================== per-tier colour + identity (v0.6)
# (v0.6 gave each tier its own hue; v0.8 made them one ectoplasm, see GOO7 below.)
# Poses are drawn with the generic gel chars ('1'-'7', bones, eyes) and recoloured per tier at the end.
_TK = [0x0410]


def _reg(hexs):
    ch = chr(_TK[0]); _TK[0] += 1
    PALETTE[ch] = hexc(hexs)
    return ch


def _tier(gel7, eyes, bones=None):
    m = {str(i + 1): _reg(h) for i, h in enumerate(gel7)}
    m['E'], m['Z'], m['M'] = _reg(eyes[0]), _reg(eyes[1]), _reg(eyes[2])
    if bones:
        m['J'], m['j'], m['l'] = _reg(bones[0]), _reg(bones[1]), _reg(bones[2])
    return m


# v0.8 final review: every ghost blob is the SAME ectoplasm (Gels fuse into Brutes, Titans, Kings; Motes and Spitters are
# the other forms' blobs), so all six share one gel ramp and one eye set. Tiers read apart by size, silhouette and
# ornament, which grows with each fusion: Gel = nucleus; Brute = rocks + bones swallowed, fists; Titan = a crust of bone
# plates with the gel glowing through the seams; King = gold crown with rubies and a velvet cape.
GOO7 = ['1c2a28', '2e4440', '4a6a5e', '6a8f78', '9ab89a', 'b8d0b4', 'e0ece0']   # Crawl's muted teal-green (ghosts_v2_blobs.py)
GOO_EYES = ['ffffff', 'b8f0d0', '0a2420']
T_GOO = _tier(GOO7, GOO_EYES)


def tint(spr, tier):
    return type(spr)({k: tier.get(v, v) for k, v in spr.px.items()})


def tint_anims(anims, tier):
    return [(a, [f if isinstance(f, SprRGB) else tint(f, tier) for f in fr], d) for a, fr, d in anims]


# ================================================================== shared sheet helpers
BUILT = {}
GOO_DROP_DURS = (0.3, 0.22, 0.18, 0.1, 0.08, 0.12, 0.15)   # SPLAT (hit) on frame 4, t = 0.80 s


def floor_ok(spr):
    return Spr({k: v for k, v in spr.px.items() if k[1] <= 0})


# ================================================================== FX
def fx_sheet(name, anims, outdir, scale=8):
    """fx.py pattern: symmetric width around the centre, (0,0) = ground/centre point."""
    anims = selout_anims(anims)
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf); y1 = max(f.bbox()[3] for f in allf)
    hw = max(-x0, x1 + 1) + 2
    h = -y0 + 2
    cw, ch = 2 * hw, h + max(0, y1) + 2
    img, man = pack(name, anims, cw, ch, (hw, h), outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": (hw, h), "anims": [(a, len(f), list(d)) for a, f, d in anims],
                   "img": img, "man": man}
    print("built %-18s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def goo_glob_frames():
    out = []
    for i in range(4):
        g = Goo()
        sx = [1.2, 1.08, 0.94, 1.06][i]; sy = [0.86, 0.96, 1.08, 0.98][i]
        g.ball(0.6, -4.0, 2.9 * sx, 2.7 * sy)
        g.ball(-2.4, -4.0 + [0.0, 0.5, 0.0, -0.5][i], 1.5, 1.3)
        fr = g.render(cut=False, zr=2.6, bias=0.15)
        fr.glint(-0.6, -5.4, big=True)
        drops(fr, [(-5 - i % 2, -4 + (1 if i % 2 else 0)), (-7 + (i % 2), -3 - (i // 2))])
        out.append(fr.spr())
    return out


def goo_puddle_frames():
    def pud(w, h, ph, seed, bias=0.3, bub=(), glint=True, dry=0.0):
        g = Goo()
        g.ball(0, -0.6, w, h)
        r = random.Random(seed)
        for k in range(3):
            g.ball(r.uniform(-w * 0.6, w * 0.6), -0.8, r.uniform(1.8, 3.0) * (1 - dry * 0.5), h * 1.1 + 0.3 * math.sin(ph + k))
        g.ball(-w * 0.9 + 0.5 * math.sin(ph), -0.4, 1.8 * (1 - dry), h * 0.7)
        g.ball(w * 0.9 - 0.5 * math.sin(ph + 1), -0.4, 1.6 * (1 - dry), h * 0.6)
        fr = g.render(bias=bias, zr=2.4)
        for (x, y, big) in bub:
            k = P(x, y)
            if big:
                for d in ((0, 0), (1, 0)):
                    if (k[0] + d[0], k[1]) in fr.inner: fr.px[(k[0] + d[0], k[1])] = '6'
                fr.put(k[0], k[1] - 1, '5'); fr.put(k[0] + 1, k[1] - 1, '5')
                fr.put(k[0] - 1, k[1] - 1, '1'); fr.put(k[0] + 2, k[1] - 1, '1'); fr.put(k[0], k[1] - 2, '1')
                fr.put(k[0] + 1, k[1] - 2, '1')
            else:
                fr.put_in(x, y, '6')
        if glint: fr.glint(-w * 0.45, -2, big=True)
        sp = fr.spr()
        if dry:
            sp = dissolve(sp, 1 - dry * 0.45, seed=seed)
            sp = Spr({k: DARKER.get(v, v) for k, v in sp.px.items()})
        return sp
    splat = []
    g = Goo(); g.ball(0, -3.0, 3.6, 3.2); g.ball(0, -0.6, 5.5, 1.5)
    fr = g.render(zr=2.6, bias=0.2); fr.glint(-1.2, -4.5, big=True)
    drops(fr, [(-5, -6), (5, -7), (-3, -8), (3, -9)])
    splat.append(fr.spr())
    g = Goo(); g.ball(0, -1.2, 8.0, 2.4); g.ball(0, -2.6, 3.0, 2.0)
    fr = g.render(zr=2.4, bias=0.25)
    drops(fr, [(-9, -4), (9, -5), (-6, -6), (7, -7), (0, -6)])
    splat.append(fr.spr())
    big = pud(11.5, 3.2, 0.0, 7, bias=0.4)
    big = Spr(dict(big.px, **{}))
    for (x, y) in ((-13, -2), (13, -2), (-10, -3), (11, -4)):
        big.px[P(x, y)] = '5'
    splat.append(big)
    idle = []
    r = random.Random(11)
    for i in range(16):
        bx = r.uniform(-7, 7)
        bub = [(bx, -2.6, i % 4 == 1)] + ([(r.uniform(-8, 8), -2.0, False)] if i % 3 == 0 else [])
        idle.append(pud(11.0, 3.0, i * 0.71 + 0.2, 7, bias=0.3, bub=bub, glint=(i % 2 == 0)))
    dry = [pud(10.5, 2.8, 1.0, 7, bias=0.1, dry=0.3), pud(9.5, 2.3, 1.5, 7, bias=-0.1, dry=0.6, glint=False),
           pud(8.0, 1.8, 2.0, 7, bias=-0.3, dry=0.85, glint=False)]
    return splat, idle, dry


def merge_burst_frames():
    out = []
    def two(rr, th, r, bridge=0.0, bias=0.2):
        g = Goo()
        a = math.radians(th)
        for sgn in (1, -1):
            x, y = sgn * rr * math.cos(a), -11 + sgn * rr * math.sin(a) * 0.6
            g.ball(x, y, r, r * 0.9)
        if bridge:
            g.ball(0, -11, bridge, bridge * 0.8)
        fr = g.render(cut=False, zr=3.0, bias=bias)
        for sgn in (1, -1):
            x, y = sgn * rr * math.cos(a), -11 + sgn * rr * math.sin(a) * 0.6
            fr.glint(x - r * 0.4, y - r * 0.45)
        return fr
    # 0: two blobs drifting in
    fr = two(9.5, 0, 4.0); fr.eye(-8, -13, 1); fr.eye(11, -13, 1)
    drops(fr, [(-3, -19), (3, -4), (0, -12)]); out.append(fr.spr())
    # 1: they stretch toward each other, a bridge forms
    fr = two(7.0, 25, 4.2, bridge=2.0); drops(fr, [(-11, -18), (11, -5), (-12, -8)]); out.append(fr.spr())
    # 2: swirling into one
    fr = two(3.6, 80, 4.6, bridge=3.0, bias=0.35)
    for k in range(10):
        t = k / 10.0 * 2 * math.pi
        rr = 9 + 1.5 * math.sin(3 * t)
        fr.put(rr * math.cos(t), -11 + rr * 0.7 * math.sin(t), '5' if k % 2 else '4')
    out.append(fr.spr())
    # 3: compressed, glowing hot
    g = Goo(); g.ball(0, -11, 6.4, 5.0); fr = g.render(cut=False, zr=3.4, bias=0.8)
    fr.glint(-2.5, -14, big=True)
    for k in range(12):
        t = k / 12.0 * 2 * math.pi + 0.3
        fr.put(11 * math.cos(t), -11 + 8 * math.sin(t), 'Z' if k % 3 == 0 else '4')
    out.append(fr.spr())
    # 4: POP
    c = cv()
    for k in range(14):
        t = k / 14.0 * 2 * math.pi
        x, y = 9 * math.cos(t), -11 + 7.5 * math.sin(t)
        ell(c, x, y, 1.6, 1.3, "456")
        c.put(*P(x - 0.5, y - 0.5), '7')
    for k in range(8):
        t = k / 8.0 * 2 * math.pi + 0.2
        line(c, 2.5 * math.cos(t), -11 + 2.5 * math.sin(t), 5.5 * math.cos(t), -11 + 4.5 * math.sin(t), 'Z')
    ell(c, 0, -11, 2.2, 2.0, "6EE")
    out.append(c.spr())
    # 5: droplets fly out
    c = cv()
    for k in range(14):
        t = k / 14.0 * 2 * math.pi + 0.1
        x, y = 13 * math.cos(t), -11 + 10 * math.sin(t) + 1
        c.put(*P(x, y), '5'); c.put(*P(x + 1, y), '4'); c.put(*P(x, y + 1), '2')
    for k in range(5):
        t = k / 5.0 * 2 * math.pi
        c.put(*P(4 * math.cos(t), -11 + 3 * math.sin(t)), 'Z')
    c.put(0, -11, 'E')
    out.append(c.spr())
    # 6: last drops, fading
    c = cv()
    for k in range(9):
        t = k / 9.0 * 2 * math.pi + 0.4
        x, y = 14.5 * math.cos(t), -11 + 11.5 * math.sin(t) + 3
        c.put(*P(x, y), '4'); c.put(*P(x, y + 1), '2')
    c.put(-2, -12, '4'); c.put(2, -9, 'Z')
    out.append(c.spr())
    return [floor_ok(s) for s in out]


def _wisp(bob, sw, eye="open", sx=1.0, sy=1.0, bias=0.55, tail=1.0):
    g = Goo()
    g.ball(0, -3.6 + bob, 2.6 * sx, 2.4 * sy)
    if tail > 0:
        g.strand([(0, -4.5 + bob), (-0.5 + sw * 0.5, -4.5 - 2.5 * tail + bob), (-1 + sw, -4.5 - 4.5 * tail + bob),
                  (0 + sw, -4.5 - 6 * tail + bob)], [1.6, 1.1, 0.7, 0.55], step=0.6)
    fr = g.render(cut=False, zr=2.2, bias=bias, edge='2')
    if eye == "open":
        fr.put(0, -4 + bob, 'E'); fr.put(1, -4 + bob, 'E'); fr.put(0, -3 + bob, 'Z')
    elif eye == "blink":
        fr.put(0, -4 + bob, 'Z'); fr.put(1, -4 + bob, 'Z')
    elif eye == "glee":
        fr.put(0, -4 + bob, 'E'); fr.put(1, -5 + bob, 'E'); fr.put(1, -3 + bob, 'Z')
    fr.put(-1, -5 + bob, '7')
    return fr


def wisp_frames():
    """Idle 10 (seamless loop: bob, tail sway, a blink), Collect 8, Fade 6 (the vanilla ectoplasm's 10 / 8 / 6)."""
    idle = []
    for i in range(10):
        t = i / 10.0 * 2 * math.pi
        bob = int(round(-0.6 - 0.9 * math.sin(t)))
        sw = round(1.2 * math.sin(t + 1.2))
        fr = _wisp(bob, sw, eye="blink" if i == 6 else "open", sx=1.0 + 0.06 * math.cos(2 * t), tail=1.0 + 0.12 * math.sin(t))
        if i in (2, 3, 7):   # a glint drifting off the tail
            fr.put(1 + (i % 2), -11 + bob - (i % 3), '7' if i != 7 else '6')
        idle.append(fr.spr())
    # Collect: pulled down into a squash, flashes white, pops into a ring and motes that fly up (to the ghost)
    col = []
    f0 = _wisp(-1, 0, eye="glee", sx=1.2, sy=0.8, tail=0.6); col.append(f0.spr())
    f1 = _wisp(-1, 0, eye="none", sx=1.35, sy=0.7, tail=0.3, bias=1.2); col.append(f1.spr())
    for k, (r, n, rise) in enumerate(((3.0, 10, 0), (4.6, 12, 1), (5.8, 12, 2), (6.4, 8, 3), (6.8, 5, 4), (7.0, 3, 6))):
        c = Canvas()
        if k == 0:
            g = Goo(); g.ball(0, -4, 1.6, 1.6); fr = g.render(cut=False, zr=1.8, bias=1.4, edge=None)
            for kk, v in fr.px.items(): c.put(kk[0], kk[1], 'E' if v in '67' else '7')
        for j in range(n):
            a = j / n * 2 * math.pi + k * 0.3
            x, y = r * math.cos(a), -4 + r * 0.8 * math.sin(a) - rise
            if k >= 3 and j % 2: continue
            c.put(*P(x, y), '7' if k < 2 else '6' if k < 4 else '5')
        for j in range(3):   # motes streaking upward
            x = [-2, 1, 3][j]; y = -6 - rise * 1.5 - j * 2
            if k < 5 or j == 0:
                c.put(x, y, 'E' if k < 3 else 'Z'); c.put(x, y + 1, '5')
        col.append(c.spr())
    # Fade: unattended wisp thins out and dissolves into dim specks
    fade = []
    for k in range(6):
        fr = _wisp(-1 - k // 2, round(math.sin(k)), eye="blink" if k > 1 else "open", sx=1.0 - 0.1 * k,
                   sy=1.0 - 0.08 * k, tail=1.0 + 0.2 * k, bias=0.55 - 0.25 * k).spr()
        if k >= 2:
            fr = dissolve(fr, 1.0 - 0.2 * (k - 1), seed=k * 7)
            fr = Spr({kk: DARKER.get(v, v) for kk, v in fr.px.items()})
        if k == 5:
            fr = Spr({kk: v for kk, v in fr.px.items() if (kk[0] + kk[1]) % 2 == 0})
        fade.append(fr)
    return idle, col, fade


def goo_ring_frames(radii, thick, ry_k=0.4, back=False, crest=0.6, drop_frames=(1, 2), seed=3, keep=(1, 1, 0.7, 0.4),
                    yoff=0, hop=1.0):
    """A ring of goo spreading over the floor, centred on (0, -yoff) (sprites keep y <= 0, so the ring's centre sits
    yoff px above the sheet's centre point). Front = the near (lower) half, back = the far half."""
    out = []
    r = random.Random(seed + (100 if back else 0))
    for i, (rx, th) in enumerate(zip(radii, thick)):
        ry = rx * ry_k
        g = Goo()
        n = max(6, int(rx * 1.4))
        for j in range(n + 1):
            t = (math.pi * j / n) + (math.pi if back else 0.0)
            x, y = rx * math.cos(t), ry * math.sin(t) - yoff
            g.ball(x, y - th * crest, th * (0.75 if back else 1.0) * (0.85 + 0.3 * r.random()), th * 0.8)
        fr = g.render(cut=False, zr=2.0, bias=0.85 if not back else 0.45, edge='3')
        if i in drop_frames:   # droplets flung up off the crest
            for j in range(5):
                t = (math.pi * (j + 0.5) / 5) + (math.pi if back else 0.0)
                x = rx * 0.9 * math.cos(t)
                y = ry * 0.9 * math.sin(t) - yoff - th - 2 - hop * r.random() * 3 * (2 - abs(i - 1.5))
                fr.put(*P(x, y), '7' if j % 2 else '6'); fr.put(*P(x, y + 1), '4')
        sp = fr.spr()
        if keep[i] < 1: sp = dissolve(sp, keep[i], seed=seed + i)
        out.append(sp)
    return out


QUAKE_YOFF = 11      # FxBlobQuake ring centre: 11 px above the sheet's centre point (see GhostPack.ArtCentre)
SPAWN_YOFF = 6       # FxBlobSpawn ring centre


def blob_quake_frames():
    """FxBlobQuake: the Brute's bounce landing / the King's slam. Ring 4 (front) + Back 4, like the troll's
    BigShockwave pair, ~46 x 18 at its widest (collider 42 x 18)."""
    radii = [9.0, 16.0, 21.0, 23.0]; thick = [2.4, 2.2, 1.6, 1.0]
    return (goo_ring_frames(radii, thick, yoff=QUAKE_YOFF),
            goo_ring_frames(radii, [t * 0.8 for t in thick], back=True, yoff=QUAKE_YOFF))


def blob_spawn_frames():
    """FxBlobSpawn: the little splash crown a blob forms in (replaces the vanilla slime's spawn shockwave, 43 x 9).
    A thin rim of goo with drops leaping off it. Ring 4 + Back 4, ~28 x 12."""
    radii = [5.0, 9.5, 12.5, 14.0]; thick = [1.3, 1.1, 0.8, 0.55]
    kw = dict(ry_k=0.33, crest=0.3, drop_frames=(0, 1, 2), seed=9, keep=(1, 1, 0.75, 0.45), yoff=SPAWN_YOFF, hop=1.6)
    return goo_ring_frames(radii, thick, **kw), goo_ring_frames(radii, [t * 0.8 for t in thick], back=True, **kw)


def goo_drop_frames():
    """FxGooDrop Fall 7: shadow + a goo drop falling from ~34 px up, SPLAT on frame 4, splash settles, fades.
    (0, 0) = the splat point on the floor (the hitbox centre)."""
    out = []
    for i, (dy, shw) in enumerate(((-34, 2.0), (-24, 3.0), (-13, 4.0), (-4, 5.0))):
        c = Canvas()
        for x in range(-int(shw), int(shw) + 1):   # shadow grows as the drop nears
            c.put(x, 0, '2' if abs(x) < shw - 1 else '1')
            if abs(x) < shw - 1: c.put(x, -1, '1')
        g = Goo()
        st = 1.0 + 0.12 * i
        g.ball(0, dy - 1.5, 2.6 / math.sqrt(st), 2.5 * st)
        g.ball(0, dy - 3.6 * st, 1.1, 1.5 * st)   # trailing tip
        fr = g.render(cut=False, zr=2.6, bias=0.6, edge='2')
        fr.glint(-0.8, dy - 2.4, big=True)
        for k, v in fr.px.items(): c.put(k[0], k[1], v)
        if i >= 1:
            for k in range(i):   # speed streak above
                c.put(0, int(dy - 3.2 * st - 2 - 2 * k), '3' if k else '4')
        out.append(c.spr())
    # 4 SPLAT
    g = Goo(); g.ball(0, -1.2, 7.5, 2.0); g.ball(0, -2.6, 3.4, 2.2)
    fr = g.render(zr=2.4, bias=0.7, edge='2')
    drops(fr, [(-8, -5), (8, -6), (-5, -7), (5, -8), (0, -8), (-10, -3), (10, -3)])
    out.append(fr.spr())
    # 5 the splash falls back, a crown of drops
    g = Goo(); g.ball(0, -0.8, 9.0, 1.8); g.ball(-3, -1.6, 2.4, 1.6); g.ball(3.5, -1.4, 2.2, 1.4)
    fr = g.render(zr=2.2, bias=0.5, edge='2')
    drops(fr, [(-10, -2), (10, -2), (-7, -4), (7, -4)])
    out.append(fr.spr())
    # 6 a thin smear soaking away
    g = Goo(); g.ball(0, -0.6, 8.0, 1.4); g.ball(-4, -0.8, 2.0, 1.2)
    sp = g.render(zr=2.0, bias=0.0, edge='2').spr()
    out.append(Spr({k: DARKER.get(v, v) for k, v in dissolve(sp, 0.7, seed=5).px.items()}))
    return out


def hex_bolt_frames():
    out = []
    for i in range(4):
        c = cv()
        fl = [0, 1, 0, -1][i]
        cy = -3.5
        # three flickering flame tongues trailing to the left (middle one longest)
        for k, (ln, yo, w0) in enumerate(((6 + (i % 2), -1.4, 0.9), (9 - (i % 2), 0.0, 1.3), (5 + ((i + 1) % 2), 1.4, 0.9))):
            wob = fl * (0.7 if k != 1 else -0.5)
            pts = [(0.5, cy + yo * 0.5), (-ln * 0.5, cy + yo + wob), (-ln, cy + yo * 1.5 - wob)]
            tube(c, pts, [w0, w0 * 0.6, 0.3], "^vV", bias=0.0 if k != 1 else 0.3)
        # head: a hot round core
        ell(c, 2.0, cy, 2.4, 2.0, "vVGG", bias=0.25)
        c.put(2, -4, '~'); c.put(3, -4, '~'); c.put(3, -3, '~' if i % 2 else 'G'); c.put(4, -4, 'G')
        c.put(1, -2, '^'); c.put(2, -2, 'v')
        # loose embers
        r = random.Random(i + 3)
        for k in range(3):
            c.put(*P(-r.uniform(4, 10), cy + r.uniform(-3, 3)), 'GVv'[k])
        out.append(c.spr())
    return out


def hex_puff_frames():
    """FxHexPuff: the hex bolt bursting. Wall 5 (on walls), Hit 4 (on a monster/hero). (0, 0) = impact point."""
    wall = []
    for i, r in enumerate((1.5, 3.0, 4.5, 5.5, 6.0)):
        c = cv()
        if i < 3:
            ell(c, 0, -3, max(1.0, 2.6 - i * 0.6), max(1.0, 2.4 - i * 0.6), "vVGG" if i else "VG~~", bias=0.3)
        for k in range(8):
            a = k / 8.0 * 2 * math.pi + i * 0.35
            x, y = r * math.cos(a), -3 + r * 0.8 * math.sin(a)
            if i >= 3 and k % 2: continue
            c.put(*P(x, y), '~' if i < 2 else 'G' if i < 4 else 'V')
            if i in (1, 2): c.put(*P(x * 0.7, y * 0.7 - 0.9), 'v')
        if i >= 2:   # smoke rising
            c.put(-1, -6 - i, '^'); c.put(1, -7 - i, '^')
        wall.append(c.spr())
    hit = []
    for i in range(4):
        c = cv()
        L = [3, 5, 6, 6][i]
        for k in range(6):
            a = k / 6.0 * 2 * math.pi + 0.5
            for t in range(L if i < 3 else 1):
                if i >= 2 and t < L - 3: continue
                x, y = (t + 1) * math.cos(a), -3 + (t + 1) * 0.8 * math.sin(a)
                c.put(*P(x, y), '~' if t < 2 and i < 2 else 'G' if t < 4 else 'V')
        if i < 2: ell(c, 0, -3, 1.6, 1.6, "G~~", bias=0.5)
        hit.append(c.spr())
    return wall, hit


def gleaner_aura_frames():
    """Two counter-rotating rings of ectoplasm motes (outer wide and low, inner small and high)."""
    out = []
    for f in range(6):
        c = cv()
        motes = []
        for ring, N, rx, ry, cy, dirn, bob in ((0, 10, 14.0, 4.6, -8.0, 1, 2.0), (1, 6, 8.0, 2.6, -16.5, -1, 1.2)):
            for i in range(N):
                th = 2 * math.pi * (i + dirn * f / 6.0) / N
                x = rx * math.cos(th)
                y = cy + ry * math.sin(th) + bob * math.sin(2 * th * (1 if ring else 1) + i * 1.3 + 0.0)
                motes.append((math.sin(th) > 0, x, y, th, dirn, ring))
        for front, x, y, th, dirn, ring in sorted(motes, key=lambda m: m[0]):
            tx = x + dirn * 1.6 * math.sin(th); ty = y - dirn * 0.5 * math.cos(th)
            tx2 = x + dirn * 3.0 * math.sin(th); ty2 = y - dirn * 0.9 * math.cos(th)
            if front:
                c.put(*P(tx2, ty2), '3'); c.put(*P(tx, ty), '4')
                c.put(*P(x, y), 'E'); c.put(*P(x + 1, y), 'Z'); c.put(*P(x, y + 1), '5')
            else:
                c.put(*P(tx, ty), '2'); c.put(*P(x, y), '4' if ring else '5')
        out.append(c.spr())
    return out


def binder_aura_frames():
    """Two tilted, counter-rotating rings of faint chain with three glowing rune links each."""
    out = []
    step = 6.0
    for f in range(6):
        c = cv()
        back, front = {}, {}
        for ring, tilt, dirn in ((0, 3.5, 1), (1, -3.5, -1)):
            phi = dirn * f * 20.0
            for td in range(0, 360):
                t = math.radians(td)
                x = 14.0 * math.cos(t)
                y = -10.5 + 4.0 * math.sin(t) + tilt * math.cos(t)
                k = P(x, y)
                link = int(math.floor((td - phi) / step)) % 2
                fr_ = math.sin(t) > 0
                mid = (td - phi) % step < 1.0
                if fr_:
                    if link: front[k] = 'Q'
                    elif mid: front[k] = '+'
                else:
                    if link and td % 2 == 0: back[k] = 'Q'
            for j in range(3):
                td = (j * 120 + phi + 3) % 360
                t = math.radians(td)
                x = 14.0 * math.cos(t); y = -10.5 + 4.0 * math.sin(t) + tilt * math.cos(t)
                X, Y = P(x, y)
                tgt = front if math.sin(t) > 0 else back
                hi, lo = ('=', '+') if math.sin(t) > 0 else ('+', 'Q')
                glyph = [((0, -1), lo), ((0, 1), lo), ((-1, 0), lo), ((1, 0), lo), ((0, 0), hi)] if (j + ring) % 2 \
                    else [((-1, -1), lo), ((1, 1), lo), ((1, -1), lo), ((-1, 1), lo), ((0, 0), hi)]
                for (dx, dy), ch in glyph:
                    tgt[(X + dx, Y + dy)] = ch
        for k, v in back.items(): c.put(k[0], k[1], v)
        for k, v in front.items(): c.put(k[0], k[1], v)
        out.append(c.spr())
    return out


CUP = """
.uuuu..
Ukkkkuu
UuuuU.u
UUuuuuu
.UUUU..
"""
CANDLE = """
..Y..
..O..
..W..
..w..
.eAe.
..A..
.eAAe
"""
BONE = """
JJ...JJ
.jjjjj.
jj...jj
"""


def grid_px(grid):
    rows = grid.strip("\n").split("\n")
    h, w = len(rows), max(len(r) for r in rows)
    return {(i - w // 2, j - h // 2): ch for j, r in enumerate(rows) for i, ch in enumerate(r) if ch not in ". "}


def rot_px(px, deg):
    a = math.radians(deg); ca, sa = math.cos(a), math.sin(a)
    R = max(max(abs(x), abs(y)) for x, y in px) + 2
    out = {}
    for y in range(-R, R + 1):
        for x in range(-R, R + 1):
            sx_ = int(round(x * ca + y * sa)); sy_ = int(round(-x * sa + y * ca))
            if (sx_, sy_) in px: out[(x, y)] = px[(sx_, sy_)]
    return out


DIMOBJ = {'u': 'U', 'U': 'S', 'k': 'K', 'Y': 'O', 'O': 'o', 'W': 'w', 'w': 'h', 'e': 'A', 'A': 'k', 'J': 'j', 'j': 'l'}


def polter_aura_frames():
    out = []
    objs = [(grid_px(CUP), 0), (grid_px(CANDLE), 120), (grid_px(BONE), 240)]
    for f in range(6):
        c = cv()
        items = []
        for i, (px, off) in enumerate(objs):
            th = math.radians(off + f * 60.0)
            x = 13.5 * math.cos(th); y = -12 + 4.5 * math.sin(th) - 2.5 * math.sin(2 * th + i)
            q = (f + i) % 4
            if i == 0:   # the cup flips end over end (always readable as a cup)
                rp = [px, {(-x_, y_): v for (x_, y_), v in px.items()}, rot_px(px, 180),
                      {(-x_, y_): v for (x_, y_), v in rot_px(px, 180).items()}][q]
            else:
                rp = rot_px(px, 90 * (q if i == 2 else -q))
            items.append((math.sin(th) > 0, x, y, th, rp))
        for front, x, y, th, px in sorted(items, key=lambda it: it[0]):
            # smear trail behind the object (it travels with +theta)
            for k in (1, 2):
                tx = x + 3.2 * k * math.sin(th); ty = y - 1.2 * k * math.cos(th)
                c.put(*P(tx, ty), 'H' if k == 1 else '8')
            X, Y = P(x, y)
            for (dx, dy), ch in px.items():
                c.put(X + dx, Y + dy, ch if front else DIMOBJ.get(ch, ch))
        out.append(c.spr())
    return out


def cv():
    return Canvas()


def goo_fx(anims):
    """Goo FX share the blobs' one ectoplasm ramp (T_GOO)."""
    return tint_anims(anims, T_GOO)


def build_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxGooGlob"): fx_sheet("FxGooGlob", goo_fx([("Fly", goo_glob_frames(), [0.08] * 4)]), outdir, scale=10)
    if want("FxGooPuddle"):
        splat, idle, dry = goo_puddle_frames()
        fx_sheet("FxGooPuddle", goo_fx([("Life", splat + idle + dry, [0.06, 0.08, 0.1] + [0.27] * 16 + [0.15, 0.15, 0.2])]),
                 outdir, scale=6)
    if want("FxMergeBurst"):
        fx_sheet("FxMergeBurst", goo_fx([("Play", merge_burst_frames(), [0.1, 0.1, 0.08, 0.08, 0.06, 0.1, 0.12])]), outdir, scale=6)
    if want("FxWisp"):
        idle, col, fade = wisp_frames()
        fx_sheet("FxWisp", goo_fx([("Idle", idle, [0.15] * 10), ("Collect", col, [0.1] * 8), ("Fade", fade, [0.1] * 6)]), outdir,
                 scale=10)
    if want("FxBlobQuake"):
        ring, back = blob_quake_frames()
        fx_sheet("FxBlobQuake", goo_fx([("Ring", ring, [0.067] * 4), ("Back", back, [0.067] * 4)]), outdir, scale=6)
    if want("FxBlobSpawn"):
        ring, back = blob_spawn_frames()
        fx_sheet("FxBlobSpawn", goo_fx([("Ring", ring, [0.067] * 4), ("Back", back, [0.067] * 4)]), outdir, scale=8)
    if want("FxGooDrop"):
        fx_sheet("FxGooDrop", goo_fx([("Fall", goo_drop_frames(), list(GOO_DROP_DURS))]), outdir, scale=6)
    if want("FxHexPuff"):
        wall, hit = hex_puff_frames()
        fx_sheet("FxHexPuff", [("Wall", wall, [0.05, 0.05, 0.06, 0.07, 0.08]), ("Hit", hit, [0.05, 0.05, 0.06, 0.08])],
                 outdir, scale=10)
    if want("FxHexBolt"): fx_sheet("FxHexBolt", [("Fly", hex_bolt_frames(), [0.07] * 4)], outdir, scale=10)
    if want("FxGleanerAura"): fx_sheet("FxGleanerAura", [("Play", gleaner_aura_frames(), [0.1] * 6)], outdir, scale=6)
    if want("FxBinderAura"): fx_sheet("FxBinderAura", [("Play", binder_aura_frames(), [0.12] * 6)], outdir, scale=6)
    if want("FxPoltergeistAura"):
        fx_sheet("FxPoltergeistAura", [("Play", polter_aura_frames(), [0.12] * 6)], outdir, scale=6)


# ================================================================== GHOST FORM PORTRAITS (29x24, opaque)
def portrait_bg(c, glow='&'):
    for y in range(-23, 1):
        for x in range(-14, 15):
            d = math.hypot(x / 13.0, (y + 12) / 11.5)
            dd = d + (0.06 if (x + y) % 2 else -0.06)   # dithered band edges
            c.put(x, y, glow if dd < 0.58 else '%' if dd < 1.0 else '#')


def ghost_body(c, ph, bob, sw):
    """The vanilla hag ghost's shroud: a tapering grey sheet sweeping down-left into a wisp tail."""
    tube(c, [(2.5, -9 + bob), (3.0, -5.5 + bob), (0.5, -2 + bob), (-5, 0 + bob), (-11, -1.5 + sw), (-14, -3 + sw)],
         [5.0, 5.4, 4.6, 3.0, 1.4, 0.6], "8HIL", bias=-0.05)
    line(c, 1, -7 + bob, -1, -2 + bob, 'H'); line(c, 5, -7 + bob, 6, -2 + bob, '8')
    for x in (-3, 0, 4, 7):  # ragged hem
        c.put(x, 0, '8' if (x + ph) % 2 else 'H')


def ghost_hair(c, bob, sw):
    ell(c, 1.6, -14.4 + bob, 6.0, 6.4, "DCC", bias=0.1)
    for (x0, y0, x1, y1) in ((-3, -12, -5.5, -6), (-1.5, -10, -3, -5), (6.5, -12, 8.5, -7)):
        tube(c, [(x0, y0 + bob), ((x0 + x1) / 2 - sw * 0.6, (y0 + y1) / 2 + bob), (x1 + sw, y1 + bob)], [1.0, 0.8, 0.5], "DC")


def ghost_arm(c, sh, el, hand, fingers=True, up=True, ramp="9f"):
    tube(c, [sh, el, hand], [1.1, 0.9, 0.8], ramp)
    if fingers:
        hx, hy = hand
        if up:
            for dx, ln in ((-1, 2), (0, 2.5), (1, 2)):
                line(c, hx + dx * 0.6, hy, hx + dx * 1.4, hy - ln, 'f')
                c.put(*P(hx + dx * 1.4, hy - ln), 'd')
        else:
            for dy in (-1, 0, 1):
                line(c, hx, hy + dy * 0.6, hx + 2, hy + dy * 1.2, 'f')


def ghost_face(c, bob, eyes="normal", mouth="wail", ph=0):
    ell(c, 3.2, -14.2 + bob, 3.6, 4.2, "9fd", bias=0.15)
    ell(c, 3.4, -11.4 + bob, 2.6, 1.8, "9f", bias=0.0)
    c.put(4, -13 + bob, '9')                    # nose shadow
    for ex in (1.4, 5.0):
        ell(c, ex, -14.6 + bob, 1.3, 1.1, "88")
        c.put(*P(ex, -14.6 + bob), 'z' if (eyes == "angry" or ph % 2) else 'x')
    if eyes == "angry":
        line(c, 0, -17 + bob, 2.5, -16 + bob, 'H'); line(c, 6.5, -17 + bob, 4, -16 + bob, 'H')
        c.put(1, -15 + bob, 'z'); c.put(5, -15 + bob, 'z')
    if mouth == "wail":
        for (x, y) in ((3, -11), (4, -11), (3, -10), (4, -10), (3, -9)):
            c.put(x, y + bob, 'M')
    elif mouth == "grit":
        line(c, 2, -10 + bob, 5, -10 + bob, 'M'); c.put(3, -10 + bob, 'd'); c.put(5, -10 + bob, 'd')
        c.put(2, -9 + bob, '9'); c.put(5, -11 + bob, 'M')
    elif mouth == "hum":
        c.put(3, -10 + bob, 'M'); c.put(4, -10 + bob, 'M')


def crop_portrait(c):
    return Spr({k: v for k, v in c.px.items() if -14 <= k[0] <= 14 and -23 <= k[1] <= 0})


def ghost_wisp(ph):
    c = cv(); portrait_bg(c)
    bob = [0, -1, -1, 0][ph]; sw = [0, 1, 0, -1][ph]
    ghost_body(c, ph, bob, sw)
    ghost_hair(c, bob, sw)
    ghost_arm(c, (-1.5, -9 + bob), (-6, -12.5 + bob), (-8, -18.5 + bob + sw * 0.5))
    ghost_arm(c, (6.5, -9 + bob), (10, -12 + bob), (11, -18.5 + bob - sw * 0.5))
    ghost_face(c, bob, ph=ph)
    return crop_portrait(c)


def tiny_gel(c, cx, cy, ph, glow=False):
    g = Goo()
    g.ball(cx, cy, 4.6, 3.0 + 0.3 * math.sin(ph * 1.6)); g.ball(cx, cy + 1.6, 5.2, 1.6)
    fr = g.render(cut=False, zr=2.4, bias=0.35 if glow else 0.1)
    fr.eye(cx + 0.5, cy - 1, 1); fr.eye(cx + 2.6, cy - 1, 1)
    fr.glint(cx - 2, cy - 1.6)
    for k, v in tint(Spr(fr.px), T_GOO).px.items(): c.put(k[0], k[1], v)   # the blobs' shared ectoplasm ramp


def ghost_gleaner(ph):
    c = cv(); portrait_bg(c)
    bob = [0, -1, -1, 0][ph]; sw = [0, 1, 0, -1][ph]
    ghost_body(c, ph, bob, sw)
    ghost_hair(c, bob, sw)
    ghost_arm(c, (-1.5, -9 + bob), (-6, -12.5 + bob), (-8, -18.5 + bob + sw * 0.5))   # beckoning
    # the sack, slung down at her side, mouth held open
    ell(c, 9.5, -3.6, 4.6, 4.0, "ktTh", bias=0.1)
    ell(c, 9.0, -8.0, 2.6, 1.6, "tT")
    line(c, 6.5, -6.6, 11.5, -6.6, 'k')                      # drawstring
    c.put(8, -9, 'K'); c.put(9, -9, 'K'); c.put(10, -9, 'K'); c.put(9, -10, 'k')
    c.put(7, -2, 'k'); c.put(11, -4, 'k'); c.put(12, -1, 't')     # patches / folds
    ghost_arm(c, (6.5, -9 + bob), (8.5, -10 + bob), (10, -8.6), fingers=False)
    c.put(10, -8, 'f'); c.put(11, -8, 'f')
    ghost_face(c, bob, mouth="hum", ph=ph)
    # motes spiralling into the sack mouth
    for i in range(5):
        u = ((i + ph / 4.0) / 5.0) % 1.0
        a = 2.6 * (1 - u) * 2 * math.pi + 1.0
        r = 11.0 * (1 - u)
        x, y = 9 + r * math.cos(a), -9.5 + r * 0.6 * math.sin(a) - 4.0 * (1 - u)
        tx, ty = x - 1.4 * math.sin(a) * (1 - u), y + 0.9 * math.cos(a) * (1 - u)
        c.put(*P(tx, ty), '4')
        c.put(*P(x, y), 'E' if u < 0.75 else 'Z')
        if u < 0.5: c.put(*P(x + 1, y), 'Z')
    return crop_portrait(c)


def chain_line(c, pts, phase, bright=True):
    """Glowing chain: alternating oval / edge-on links, a glint travelling along it."""
    k = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in line_px(*P(x0, y0), *P(x1, y1)):
            ch = '+' if k % 2 == 0 else 'Q'
            if bright and (k + phase) % 6 == 0: ch = '='
            c.put(x, y, ch)
            k += 1


def ghost_binder(ph):
    c = cv(); portrait_bg(c)
    bob = [0, -1, -1, 0][ph]; sw = [0, 1, 0, -1][ph]
    ghost_body(c, ph, bob, sw)
    ghost_hair(c, bob, sw)
    # arms brought forward, hands joined over the gel
    ghost_arm(c, (-1, -8.5 + bob), (0, -5 + bob), (4, -6.5 + bob), fingers=False)
    ghost_arm(c, (7, -8.5 + bob), (9, -5.5 + bob), (6, -6.5 + bob), fingers=False)
    c.put(5, -7 + bob, 'd'); c.put(4, -7 + bob, 'f'); c.put(6, -7 + bob, 'f')
    ghost_face(c, bob, mouth="hum", ph=ph)
    # chains wrapped around her: one across the chest and arms, one around the tail
    chain_line(c, [(-7, -13 + bob), (-1, -9 + bob), (6, -9 + bob), (11, -12 + bob)], ph * 2)
    chain_line(c, [(-13, -5 + sw), (-8, -2 + bob), (-3, -3 + bob)], ph * 2 + 3)
    # the gel she binds, glowing under her joined hands
    tiny_gel(c, 5, -2.4, ph, glow=True)
    for i in range(4):
        t = (i / 4.0 + ph / 16.0) * 2 * math.pi
        c.put(*P(5 + 7 * math.cos(t), -3 + 2.2 * math.sin(t)), '+' if i % 2 else '=')
    return crop_portrait(c)


def ghost_poltergeist(ph):
    c = cv(); portrait_bg(c)
    bob = [0, -1, -1, 0][ph]; sw = [0, 1, 0, -1][ph]
    ghost_body(c, ph, bob, sw)
    ghost_hair(c, bob, sw)
    # back arm cocked behind her head with a plate
    hx, hy = -9, -19 + bob + sw * 0.5
    ghost_arm(c, (-1.5, -9 + bob), (-6, -14 + bob), (hx, hy), fingers=False)
    ell(c, hx - 1, hy - 1.5, 2.6, 1.4, "Uuc", ang=-30)
    c.put(hx - 1, hy - 1, 'S')
    # front arm flung forward: the throw
    ghost_arm(c, (6.5, -9 + bob), (10, -11 + bob), (12.5, -12.5 + bob), up=False)
    ghost_face(c, bob, eyes="angry", mouth="grit", ph=ph)
    # crockery flying out to the right, tumbling (cycles through the 4 frames)
    cup = grid_px(CUP)
    cup = [cup, {(-x, y): v for (x, y), v in cup.items()}, rot_px(cup, 180), cup][ph]
    cx, cy = 10 + ph * 0.5, -19 - (ph % 2)
    X, Y = P(cx, cy)
    for (dx, dy), v in cup.items(): c.put(X + dx, Y + dy, v)
    for k in (1, 2, 3): c.put(*P(cx - 3 - k * 1.5, cy + 0.5 * k), 'H' if k < 3 else '8')
    # plate shards and a fork
    for (x, y, ch) in ((12 - ph % 2, -6, 'u'), (13, -5 + ph % 2, 'U'), (11 + ph % 2, -4, 'c')):
        c.put(x, y, ch)
    fx_, fy_ = -11 + ph % 2, -6 - (ph // 2)
    line(c, fx_, fy_, fx_ + 3, fy_ - 2, 'U'); c.put(fx_ + 3, fy_ - 3, 'u'); c.put(fx_ + 4, fy_ - 2, 'u')
    return crop_portrait(c)


def build_portraits(outdir, only=None):
    # GhostGleaner / GhostBinder / GhostPoltergeist are composed by ghost_v11.py (tinted frame + their fodder),
    # from the drawings below; only the vanilla Wisp is written here
    for name, fn in (("GhostWisp", ghost_wisp),):
        if only is not None and name not in only: continue
        frames = [fn(i) for i in range(4)]
        durs = [0.25, 0.2, 0.25, 0.2]
        img, man = pack(name, [("Idle", frames, durs)], 29, 24, (14, 23), outdir)
        preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=10)
        crop = img.crop((0, 0, 29 * 4, 24)).load()
        assert all(crop[x, y][3] == 255 for x in range(29 * 4) for y in range(24)), name + " must be opaque"
        BUILT[name] = {"cell": (29, 24), "feet": (14, 23), "anims": [("Idle", 4, durs)], "img": img, "man": man}
        print("built %-18s cell 29x24  Idle:4 (opaque)" % name)


# ================================================================== TIMING.md + contact sheet
EVENTS = {
    "BlobMote": {"Bite": [("hit", 3)]},
    "BlobSpitter": {"Spit": [("release (spawn FxGooGlob at the tube tip)", 3)]},
    "BlobGel": {"Slam": [("hit", 3)]},
    "BlobBrute": {"Slam": [("hit", 4)], "Bounce": [("crouch", 0), ("airborne (leave ground)", 2), ("land (impact)", 5)]},
    "BlobTitan": {"Slam": [("hit", 4)], "Engulf": [("lunge start", 2), ("lunge end", 4), ("mouth closes (bite/grab)", 5)]},
    "BlobKing": {"Slam": [("hit", 4)], "Rain": [("rear up", 0), ("spew (launch the glob rain)", 4), ("settle", 5)]},
}
FX_NOTES = {
    "FxGooGlob": "Fly loop, faces right (Spitter / King Rain projectile).",
    "FxGooPuddle": "Life: splat 0-2 (0.24 s), idle 3-18 (0.27 s each, 4.32 s), dry 19-21 (0.5 s); 5.06 s total.",
    "FxMergeBurst": "Play once; blobs touch on 1, merged on 3, POP on frame 4 (spawn the fused blob here).",
    "FxWisp": "Gleaner pickups. Idle: seamless 10-frame loop (bob, tail sway, blink on 6), floats 2-12 px above the centre. "
              "Collect: once, squash 0-1, white flash 2, ring + motes rising 3-7 (replaces vanilla EctoplasmCollect). "
              "Fade: once, thins and dissolves (replaces vanilla EctoplasmDisappear).",
    "FxHexPuff": "Hex bolt impact. Wall: once, burst + smoke (wall/floor hits). Hit: once, star of green sparks on a body.",
    "FxBlobQuake": "Brute Bounce landing / King slam ring. Ring = near half, Back = far half (child sprite, like the troll's "
                   "BigShockwaveFront/Back); damage on 0.05-0.18 s. Widest 46 x 18; collider 42 x 18 on the centre.",
    "FxBlobSpawn": "Splash crown under a forming blob (blob Spawn clip's AnimAttack 3 at 0.15 s). Ring = near half, Back = "
                   "far half. Visual only.",
    "FxGooDrop": "King Rain drop. Fall: shadow + drop falling from ~34 px (0-3), SPLAT = hit on frame 4 (t = 0.80 s), "
                 "splash settles 5, soaks away 6. Centre = the splat point.",
    "FxHexBolt": "Fly loop, faces right (Poltergeist bolt).",
    "FxGleanerAura": "Play as a seamless loop around the ghost (frame 5 flows into frame 0).",
    "FxBinderAura": "Play as a seamless loop around the ghost (frame 5 flows into frame 0).",
    "FxPoltergeistAura": "Play as a seamless loop around the ghost; each object makes one full orbit per loop.",
}
MONSTERS = ["BlobMote", "BlobSpitter", "BlobGel", "BlobBrute", "BlobTitan", "BlobKing"]
FXS = ["FxGooGlob", "FxGooPuddle", "FxMergeBurst", "FxWisp", "FxHexBolt", "FxHexPuff", "FxBlobQuake", "FxBlobSpawn",
       "FxGooDrop", "FxGleanerAura", "FxBinderAura",
       "FxPoltergeistAura"]
PORTRAITS = ["GhostWisp", "GhostGleaner", "GhostBinder", "GhostPoltergeist"]


def idle_height(n):
    b = BUILT[n]; img, man = b["img"], b["man"]
    cw, ch = man["cellW"], man["cellH"]
    fi = man["anims"][0]["frames"][0]
    bb = img.crop(((fi % man["cols"]) * cw, (fi // man["cols"]) * ch, (fi % man["cols"] + 1) * cw,
                   (fi // man["cols"] + 1) * ch)).getbbox()
    return bb[3] - bb[1], bb[2] - bb[0]


def write_timing(outdir):
    L = ["# Ghost forms + blob fodder: sprite timing", "",
         "Generated by `tools/sprites/ghost_rigs.py`. Frame indices are 0-based within the anim.",
         "Monster sheets use feet = (cellW/2, cellH-2) and face right; FX use the fx.py centre point listed below.",
         "Times are seconds from the start of the anim to the start of that frame.",
         "All six blobs are ONE ectoplasm (drawn by ghosts_v2_blobs.py): a lit gel skin over a darker core, a backlit rim,",
         "glowing hearts, bubbles and what each has swallowed. Mote one big eye; Spitter a goo sac and a nozzle; Gel one",
         "heart; Brute two hearts, rocks and a bone, fists; Titan three hearts under a crust of bone plates; King a gold",
         "crown, an ermine-collared cape and the skulls of its subjects.", "",
         "Design scale: the kits' offsets are authored in design units that ArtScale.cs multiplies by the sheet's factor",
         "(SCALE below); the art is drawn at its final size. Blob cells are locked (code depends on them).",
         "Brute, Titan and King grow with each fusion: GhostPack multiplies their kit offsets, hitboxes and node by GROW",
         "on top of the design scale.", "",
         "## Monster sheets", "",
         "| Sheet | Cell (w x h) | Feet | Idle size (h x w) | Design scale | Grow | Anims (frames) |", "|---|---|---|---|---|---|---|"]
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]; ih, iw = idle_height(n)
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %.2f | %.2f | %s |" % (n, cw, ch, cw // 2, ch - 2, ih, iw,
                 SCALE.get(n, 1.0), GROW.get(n, 1.0), ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Gameplay sync frames", "", "| Sheet | Anim | Frames | Event | Frame index | Time (s) | Anim length (s) |",
          "|---|---|---|---|---|---|---|"]
    for n in MONSTERS:
        if n not in BUILT: continue
        anims = {a: (k, d) for a, k, d in BUILT[n]["anims"]}
        for an, evs in EVENTS[n].items():
            k, d = anims[an]
            for ev, fi in evs:
                assert fi < k
                L.append("| %s | %s | %d | %s | %d | %.2f | %.2f |" % (n, an, k, ev, fi, sum(d[:fi]), sum(d)))
    L += ["", "Every attack has at least two wind-up frames before its first strike frame; strike frames last 0.06-0.07 s",
          "and are followed by longer recovery holds. Death plays once and ends on the puddle corpse; Dead is that frame.",
          "Run is a squash-and-stretch hop (crouch 0, launch 1, airborne 2-4, land 5).", "",
          "## FX sheets", "", "| Sheet | Cell (w x h) | Centre | Anims (frames, total s) | Notes |", "|---|---|---|---|---|"]
    for n in FXS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"]), FX_NOTES[n]))
    L += ["", "Blob Spawn (all six sheets, 5 frames, the vanilla slime spawn's durations 0.067/0.083/0.2/0.2/0.25 so its "
          "events keep their times: sound 0 s, spawn splash (FxBlobSpawn, effect 3) 0.15 s, sound 0.35 s): pool gathers 0, "
          "mound 1, surges up 2, lands squashed 3, settles 4."]
    L += ["", "## Ghost form portraits (opaque)", "", "| Sheet | Cell | Feet | Anims |", "|---|---|---|---|"]
    for n in PORTRAITS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s loop" % (a, k, sum(d)) for a, k, d in b["anims"])))
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(outdir, "TIMING.md"))


def contact_sheet(outdir):
    from PIL import Image, ImageDraw
    cells = []
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; img, man = b["img"], b["man"]
        cw, chh = man["cellW"], man["cellH"]
        fi = man["anims"][0]["frames"][0]
        x0, y0 = (fi % man["cols"]) * cw, (fi // man["cols"]) * chh
        cell = img.crop((x0, y0, x0 + cw, y0 + chh))
        bb = cell.getbbox()
        cells.append((n, cell.crop((bb[0], 0, bb[2], chh - 2))))   # trim sides, keep the ground line aligned
    if not cells: return
    S = 6
    H = max(c.size[1] for _, c in cells)
    W = sum(c.size[0] for _, c in cells) + 5 * (len(cells) + 1)
    bg = Image.new("RGBA", (W * S, (H + 3) * S), (28, 26, 32, 255))
    x = 5
    for n, c in cells:
        bg.alpha_composite(c.resize((c.size[0] * S, c.size[1] * S), Image.NEAREST), (x * S, (H - c.size[1]) * S))
        x += c.size[0] + 5
    d = ImageDraw.Draw(bg)
    d.line([(0, H * S + S // 2), (W * S, H * S + S // 2)], fill=(60, 56, 64, 255))
    bg.convert("RGB").save(os.path.join(outdir, "contact_idle.png"))
    print("contact sheet", os.path.join(outdir, "contact_idle.png"))


# ------------------------------------------------------------------ main
# the factor each blob kit's design units are scaled by (src/CrawlFurther/SheetScales.cs)
SCALE = {"BlobMote": 0.92, "BlobSpitter": 0.8, "BlobGel": 0.8, "BlobBrute": 0.57, "BlobTitan": 0.58, "BlobKing": 0.5}
# v0.8 fusion growth on top of SCALE (ArtScale.cs keeps SCALE): each fusion step is clearly bigger than the last.
# GhostPack multiplies these kits' design-space offsets / hitboxes / node by the same factor (GhostPack.Grow*).
GROW = {"BlobBrute": 1.3, "BlobTitan": 1.2, "BlobKing": 1.3}


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    outdir = args[0] if args else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    import ghosts_v2_blobs as BLOBS
    import ghosts_v2_kit as KIT
    for n, fn in BLOBS.JOBS:
        if only is None or n in only:
            fn(outdir)
            BUILT[n] = KIT.BUILT[n]
    if only is None or only & set(FXS):
        build_fx(outdir, None if only is None else only & set(FXS))
    if only is None or only & set(PORTRAITS):
        build_portraits(outdir, None if only is None else only & set(PORTRAITS))
    if only is None:
        contact_sheet(outdir)
        write_timing(outdir)
        # the in-game ghost form bodies + menu marks (ghost_forms.py) append their own TIMING.md section
        import ghost_forms
        sys.argv = [sys.argv[0], outdir]
        ghost_forms.main()


if __name__ == "__main__":
    main()
