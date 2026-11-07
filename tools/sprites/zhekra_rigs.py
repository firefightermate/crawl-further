"""ZHEKRA, THE BROOD QUEEN: "The hive is never finished". The first Zhekra rig. Its monster, effect and portrait
sheets are now drawn by zhekra_v2_rigs.py; running this file builds only what v2 does not draw: the two item icons
(with their shop bubbles and HUD icon).

    python3 zhekra_rigs.py [outdir]

Method (same family as belmora_rigs.py): every frame is a fresh pose drawn from shaded primitives (ellipses,
tapered tubes, polygons) lit from the top-left, then a 1px chitin-black outline, then glow pixels on top
(acid eyes, glands, spiracles) so they stay bright. Materials: dark chitin, sickly amber resin, pale grub
flesh, acid green. No fire, no plants, no water.
"""
import json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, PALETTE, pack, preview  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_zhekra")
ROOT = os.path.dirname(os.path.dirname(HERE))

# ------------------------------------------------------------------ palette (this pack only; never overrides anim.py's)
PALETTE.update({
    '0': (0x14, 0x0f, 0x0b),   # outline: chitin black
    '1': (0x26, 0x1b, 0x14),   # chitin ramp, dark -> sheen
    '2': (0x3c, 0x2b, 0x1e),
    '3': (0x57, 0x40, 0x2b),
    '4': (0x7a, 0x5c, 0x3c),
    '5': (0xa4, 0x8e, 0x70),   # cool chitin sheen
    '6': (0x63, 0x30, 0x0c),   # amber resin ramp
    '7': (0xa4, 0x58, 0x12),
    '8': (0xd6, 0x8e, 0x22),
    '9': (0xf4, 0xc4, 0x52),
    'E': (0xff, 0xec, 0xa4),   # resin highlight
    'f': (0x6b, 0x5a, 0x42),   # grub flesh ramp (sickly, pale)
    'M': (0x9a, 0x88, 0x64),
    'C': (0xc6, 0xb6, 0x8a),
    'H': (0xe8, 0xdc, 0xb2),
    'd': (0x26, 0x44, 0x10),   # acid ramp
    'D': (0x48, 0x84, 0x14),
    'Q': (0x88, 0xd6, 0x22),
    'J': (0xcc, 0xff, 0x66),
    'L': (0xf4, 0xff, 0xcc),
    'z': (0x4a, 0x52, 0x4a),   # wing membrane
    'l': (0x86, 0x92, 0x7c),
    'j': (0x36, 0x2a, 0x1e),   # dirt
    'I': (0x58, 0x45, 0x30),
    'Z': (0x7c, 0x64, 0x46),
    'x': (0x4e, 0x1e, 0x1a),   # maw / wet flesh
    '~': (0xb6, 0xc2, 0xa6),   # wing membrane light
    # v0.8: Hive Hornet's own colours (rust-red hunter chitin, smoky amber wings), status overlays
    '!': (0x4a, 0x18, 0x12),   # hornet chitin: oxblood -> rust
    '@': (0x7c, 0x2a, 0x1a),
    '#': (0xae, 0x46, 0x22),
    '$': (0xe0, 0x76, 0x34),
    '%': (0x7a, 0x5a, 0x30),   # smoky amber wing membrane
    '^': (0xc4, 0x9c, 0x5a),
    '&': (0x2e, 0x20, 0x12),   # wing vein
    ';': (0x34, 0x3a, 0x1a),   # Acid Mantis olive chitin
    ':': (0x56, 0x60, 0x26),
    '+': (0x80, 0x8c, 0x3a),
    '=': (0xb4, 0xbc, 0x64),
})
GLOW = set("QJL")
OUT_C = "0"

CHIT = "1234"
CHIT_L = "2345"
AMB = "6789"
AMB_L = "789E"
GRUB = "fMCH"
GRUB_D = "1fMC"
ACID = "dDQJ"
ACID_L = "DQJL"
WING = "zl"
DIRT = "jIZ"


# ------------------------------------------------------------------ primitives (after belmora_rigs.py)
def pick(ramp, l):
    n = len(ramp)
    i = int((l + 1.0) * 0.5 * n)
    return ramp[max(0, min(n - 1, i))]


def P(x, y):
    return int(round(x)), int(round(y))


def ell(c, cx, cy, rx, ry, ramp, ang=0.0, bias=0.0, vmax=None, vmin=None, over=True, shader=None):
    """Filled ellipse lit from the top-left; ang rotates; vmax/vmin clip in local normalised v."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = int(max(rx, ry)) + 2
    for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)) + 1):
        for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R)) + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            nu, nv = u / max(rx, 0.5), v / max(ry, 0.5)
            d = nu * nu + nv * nv
            if d > 1.0: continue
            if vmax is not None and nv > vmax: continue
            if vmin is not None and nv < vmin: continue
            wx, wy = nu * ca - nv * sa, nu * sa + nv * ca
            l = 0.8 * (-(wx + wy) / 1.414) + 0.35 * (1 - d) - 0.12 + bias
            ch = pick(ramp, l)
            if shader:
                r = shader(nu, nv, d, l, ch, x, y)
                if r is None: continue
                ch = r
            c.put(x, y, ch, over)


def tube(c, pts, radii, ramp, bias=0.0, over=True):
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r0, r1 = radii[i], radii[i + 1]
        R = max(r0, r1) + 1
        L2 = (x1 - x0) ** 2 + (y1 - y0) ** 2
        for y in range(int(math.floor(min(y0, y1) - R)), int(math.ceil(max(y0, y1) + R)) + 1):
            for x in range(int(math.floor(min(x0, x1) - R)), int(math.ceil(max(x0, x1) + R)) + 1):
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / L2))
                qx, qy = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                r = r0 + (r1 - r0) * t
                ox, oy = x - qx, y - qy
                if math.hypot(ox, oy) > r + 0.15: continue
                l = bias if r < 0.75 else -(ox + oy) / (r * 1.414) * 0.9 + 0.15 + bias
                c.put(x, y, pick(ramp, l), over)


def line(c, x0, y0, x1, y1, ch, over=True):
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    for i, (x, y) in enumerate(pts):
        c.put(x, y, ch[i % len(ch)] if len(ch) > 1 else ch, over)
    return pts


def polyline(c, pts, ch, over=True):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        line(c, x0, y0, x1, y1, ch, over)


def chain(x, y, segs):
    pts = [(x, y)]
    for ln, a in segs:
        x += ln * math.cos(math.radians(a)); y += ln * math.sin(math.radians(a))
        pts.append((x, y))
    return pts


def poly(c, pts, ch, over=True, shade=None):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]; xj, yj = pts[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                    inside = not inside
                j = i
            if inside:
                c.put(x, y, shade(x, y) if shade else ch, over)


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    dx, dy = tx - sx, ty - sy
    d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 1e-3))
    a = math.atan2(dy, dx)
    b = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    ea = a - bend * b
    return (sx + l1 * math.cos(ea), sy + l1 * math.sin(ea)), (sx + d * math.cos(a), sy + d * math.sin(a))


def leg(c, hip, foot, l1, l2, bend, cols=("2", "3"), knee_hi="4"):
    """Two-segment insect leg by IK; returns the knee."""
    knee, end = ik(hip[0], hip[1], foot[0], foot[1], l1, l2, bend)
    line(c, hip[0], hip[1], knee[0], knee[1], cols[0])
    line(c, knee[0], knee[1], end[0], end[1], cols[1])
    if knee_hi: c.put(*P(*knee), knee_hi)
    return knee


def rot(p, piv, deg):
    a = math.radians(deg)
    x, y = p[0] - piv[0], p[1] - piv[1]
    return piv[0] + x * math.cos(a) - y * math.sin(a), piv[1] + x * math.sin(a) + y * math.cos(a)


# ------------------------------------------------------------------ frame: body canvas + glow canvas
class Fr:
    def __init__(self):
        self.b = Canvas()   # outlined body
        self.g = Canvas()   # glow / fx pixels drawn over the outline
        self.u = Canvas()   # under-layer: behind the body, outlined with it (back limbs)
        self.n = Canvas()   # far layer: behind everything, no outline (far-side limbs in shadow)
        self.pts = {}       # named points (mouth, tip...) for TIMING.md

    def done(self, outline=True, clip=True):
        base = dict(self.u.px)
        base.update(self.b.px)
        spr = Spr(base)
        if outline: spr = outl(spr)
        px = dict(self.n.px)
        px.update(spr.px)
        px.update(self.g.px)
        if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
        s = Spr(px)
        s.pts = self.pts
        return s


def outl(spr, ch=OUT_C):
    out = dict(spr.px)
    for (x, y) in spr.px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in spr.px: out[k] = ch
    return Spr(out)


def grounded(spr):
    b = spr.bbox()
    return Spr({(x, y - b[3]): v for (x, y), v in spr.px.items()})


def merge(*sprs):
    out = {}
    for s in sprs: out.update(s.px)
    return Spr(out)


def recol(spr, mapping):
    return Spr({k: mapping.get(v, v) for k, v in spr.px.items()})


def dim_glow(spr):
    return recol(spr, {"J": "D", "L": "Q", "Q": "d"})


def shifted(spr, dx, dy):
    return Spr({(x + dx, y + dy): v for (x, y), v in spr.px.items()})


# ------------------------------------------------------------------ sheet helpers
BUILT = {}
SPAWN = {}          # sheet -> {(anim, frame): (x, y)} recorded from pose points


def note(sheet_name, anim, frames, key):
    """Record each frame's named point (e.g. 'mouth') for TIMING.md."""
    for i, f in enumerate(frames):
        p = getattr(f, "pts", {}).get(key)
        if p is not None:
            SPAWN.setdefault(sheet_name, {})[(anim, i, key)] = P(*p)


# v0.8 readability: the darkest Zhekra sheets wear a lighter chitin ramp (audit: idle luminance ~55 vs vanilla ~100)
LIFT = {"1": "2", "2": "3", "3": "4", "4": "5"}
LIFT_OLIVE = {"1": ";", "2": ":", "3": "+", "4": "="}
LIFT_BEETLE = {"1": "2", "2": "3", "3": "4", "4": "5"}     # v0.10: the Resin Beetle's shell a step brighter again
HORNET_LIFT = {"!": "@", "@": "#", "#": "$", "1": "2", "2": "3", "d": "D"}   # v0.10: hornet midtones lifted     # the Acid Mantis: olive-green chitin


def lifted(anims, remap):
    """Recolour every frame with remap (named points kept); the Statue is re-cut from the recoloured Idle frame 0."""
    idle0 = recol(anims[0][1][0], remap)
    out = []
    for an, fr, du in anims:
        if an == "Statue":
            out.append((an, [idle0.stone()], du)); continue
        nf = []
        for f in fr:
            g = recol(f, remap); g.pts = getattr(f, "pts", {}); nf.append(g)
        out.append((an, nf, du))
    return out


def sheet(name, anims, outdir, scale=6, pad=2, remap=None):
    if remap: anims = lifted(anims, remap)
    allf = [f for a in anims for f in a[1]]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
        for i, f in enumerate(fr):
            if f.px and max(p[1] for p in f.px) > 0:
                print("WARNING %s/%s[%d] has pixels below the floor" % (name, an, i))
    x0 = min(f.bbox()[0] for f in allf if f.px); x1 = max(f.bbox()[2] for f in allf if f.px)
    y0 = min(f.bbox()[1] for f in allf if f.px)
    hw = max(-x0, x1 + 1) + pad
    cw = 2 * hw
    ch = -y0 + 1 + pad + 2
    ch += ch % 2          # v0.9: even cell heights (one spare row on top), feet stay 2 rows above the bottom
    feet = (cw // 2, ch - 2)
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man}
    b = anims[0][1][0].bbox()
    print("built %-16s cell %dx%d idle %dx%d  %s" % (name, cw, ch, b[2] - b[0] + 1, b[3] - b[1] + 1,
                                                     ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def fx_sheet(name, anims, outdir, scale=8):
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf); y1 = max(f.bbox()[3] for f in allf)
    hw = max(-x0, x1 + 1) + 1
    h = -y0 + 1
    cw, ch = 2 * hw, h + max(0, y1) + 1
    img, man = pack(name, anims, cw, ch, (hw, h), outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": (hw, h), "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man}
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def std_tail(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


def acid_drip(c, x, y, n, ph=0):
    """A hanging acid drool strand from (x,y) down n px, bright bead at the end."""
    for i in range(n):
        c.put(*P(x + (0.4 if (i + ph) % 3 == 2 else 0), y + i), "D" if i < n - 1 else "Q")
    c.put(*P(x, y + n), "J")


# ================================================================== GRUBS: ACID GRUB (T1) and the LARVA minion
def resin_shell(c, g, x, y, rx, ry, ang=0.0, beads=3):
    """v0.9 lineage motif of the Resin Beetle: a glossy dark elytra dome split by a resin seam, amber beads welling out
    of its pores (Beetle -> Hive Soldier / Nasute -> Chitin Colossus / Amber Hive)."""
    def sh(nu, nv, d, l, ch, X, Y):
        if abs(nu) < 0.09 and nv < 0.6: return "7"
        if l > 0.7 and d < 0.35: return "5"
        return pick("1234", l)
    ell(c, x, y, rx, ry, "1234", ang=ang, bias=0.05, shader=sh, vmax=0.95)
    a = math.radians(ang)
    for k in range(beads):
        t = -0.55 + 1.1 * k / max(1, beads - 1)
        bx, by = x + t * rx * math.cos(a) - 0.35 * ry * math.sin(a), y + t * rx * math.sin(a) - 0.45 * ry
        ell(c, bx, by, 0.9, 0.8, AMB_L, bias=0.4)
        g.put(*P(bx - 0.3, by - 0.4), "E")


def tube2(c, pts, radii, shader, over=True):
    """Tapered tube along a polyline; shader(s, ox, oy, r, l) picks each pixel (s = point index + t)."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    R = max(radii) + 1
    for y in range(int(math.floor(min(ys) - R)), int(math.ceil(max(ys) + R)) + 1):
        for x in range(int(math.floor(min(xs) - R)), int(math.ceil(max(xs) + R)) + 1):
            best = None
            for i in range(len(pts) - 1):
                (x0, y0), (x1, y1) = pts[i], pts[i + 1]
                L2 = (x1 - x0) ** 2 + (y1 - y0) ** 2
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / L2))
                qx, qy = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                r = radii[i] + (radii[i + 1] - radii[i]) * t
                ox, oy = x - qx, y - qy
                dd = math.hypot(ox, oy) - r
                if dd <= 0.15 and (best is None or dd < best[0]):
                    best = (dd, i + t, ox, oy, r)
            if best is None: continue
            _, s, ox, oy, r = best
            l = -(ox + oy) / (max(r, 0.5) * 1.414) * 0.9 + 0.15
            ch = shader(s, ox, oy, r, l) if shader.__code__.co_argcount == 5 else shader(s, ox, oy, r, l, x, y)
            if ch: c.put(x, y, ch, over)


def grub(dx=0.0, dy=0.0, k=1.0, n=5, plates=True, st=1.0, hump=0.0, ph=0.0, lift=0.0, jaw=0.25, legs=0.0,
         swell=0.0, flat=0.0, eye="open", drip=2, extra=None, spir=1, rear=1.0):
    """A segmented grub facing right: a bumpy tapered tube with creases between segments, dark chitin
    plates on the back (plates=True), pale sickly flesh below, acid spiracles, a chitin head with amber
    mandibles. k scales it (1 = Acid Grub, ~0.62 = larva)."""
    f = Fr()
    seg = 1.95 * k * st
    rc = [1.7, 2.5, 3.1, 3.3, 3.0, 2.8][-n:]
    rc = [r * k * (1 - flat * 0.45) for r in rc]
    for i in (n - 2, n - 3):
        rc[i] += swell * 0.8 * k
    x0 = dx - (n * seg) * 0.62
    pts, radii = [], []
    for j in range(2 * n + 1):
        i = j / 2.0
        x = x0 + i * seg
        if j % 2 == 1:
            r = rc[j // 2]
        else:
            a = rc[max(0, j // 2 - 1)] if j > 0 else rc[0] * 0.55
            b = rc[min(n - 1, j // 2)]
            r = min(a, b) * 0.86 if 0 < j < 2 * n else (rc[0] * 0.6 if j == 0 else rc[-1] * 0.9)
        h = hump * max(0.0, math.sin(ph - i * 0.95))
        up = (rear * 0.6 + lift) * max(0.0, i - (n - 2.5)) * 0.7
        pts.append((x, dy - max(rc) * 0.95 - 0.6 - h - up + (max(rc) - r) * 0.55))
        radii.append(r)
    neck = pts[-1]
    # stubby true legs under the three front segments (far side in shadow)
    if flat < 0.5:
        for side, cv_ in ((0, f.n), (1, f.u)):
            for jj, i in enumerate(range(n - 3, n)):
                x, y = pts[2 * i + 1]
                pha = legs + jj * 2.1 + side * math.pi
                fx = x + 0.8 + 0.9 * math.sin(pha) - (0 if side else 0.8)
                fy = -max(0.0, 0.8 * math.cos(pha))
                line(cv_, x + (0.3 if side else -0.5), y + rc[i] * 0.6, fx, fy, "3" if side else "1")
                cv_.put(*P(fx + 0.6, fy), "4" if side else "1")

    def sh(s, ox, oy, r, l):
        segp = s / 2.0
        fr = segp - math.floor(segp)
        crease = (fr < 0.14 or fr > 0.9) and 0.4 < segp < n - 0.1
        if plates and oy < -0.12 * r and segp > 0.7:
            if crease: return "0" if oy < -0.5 * r else "1"
            if oy > -0.3 * r: return "1"                      # plate rim shadow
            if l > 0.8 and fr > 0.4: return "5"
            return "4" if l > 0.55 else ("3" if l > 0.1 else "2")
        if crease: return "f"
        if oy > 0.55 * r: return pick("fM", l + 0.3)
        return pick(GRUB, l + 0.25 - (0.25 if segp < 1 else 0))
    tube2(f.b, pts, radii, sh)
    # spiracles: acid pores along the side; they flare when the glands swell
    for i in range(1, n):
        x, y = pts[2 * i + 1]
        c = "J" if swell > 0.55 else ("Q" if swell > 0.2 or spir else "D")
        f.g.put(*P(x, y + rc[i] * 0.05), c)
    # head capsule
    hr = 2.4 * k
    hx, hy = neck[0] + hr * 0.7, neck[1] - 0.4 - lift * 0.3
    ell(f.b, hx, hy, hr, hr * 0.92, "1234", bias=0.2)
    f.b.put(*P(hx - hr * 0.3, hy - hr * 0.6), "5")
    for yy in range(-1, 2):                                          # collar crease
        f.b.put(*P(hx - hr * 0.95, hy + yy * hr * 0.5), "0")
    # mandibles: amber hooks that open with jaw
    mx = hx + hr * 0.7
    up = [(mx, hy - 0.4), (mx + 1.5 * k, hy - 0.9 - jaw * 1.4 * k), (mx + 2.4 * k, hy - 0.1 - jaw * 0.9 * k)]
    lo = [(mx, hy + 0.8 * k), (mx + 1.4 * k, hy + 1.5 * k + jaw * 1.3 * k), (mx + 2.2 * k, hy + 0.8 * k + jaw * 1.2 * k)]
    polyline(f.b, up, "8"); polyline(f.b, lo, "7")
    f.b.put(*P(*up[-1]), "9"); f.b.put(*P(*lo[-1]), "8")
    if jaw > 0.6:
        f.g.put(*P(mx + 0.6, hy + 0.3), "Q")
    f.pts["mouth"] = (mx + 1.8 * k, hy + 0.3)
    # eyes: acid ocelli
    ex, ey = hx + hr * 0.25, hy - hr * 0.25
    if eye == "open":
        f.g.put(*P(ex, ey), "J")
    elif eye == "wide":
        f.g.put(*P(ex, ey), "L"); f.g.put(*P(ex, ey - 1), "Q")
    elif eye == "squint":
        f.g.put(*P(ex, ey), "D")
    else:
        f.g.put(*P(ex, ey), "1")
    if drip:
        acid_drip(f.g, mx + 0.5, hy + 1.5 * k + 0.6, drip)
    segs = [(pts[2 * i + 1][0], pts[2 * i + 1][1], rc[i], rc[i]) for i in range(n)]
    if extra: extra(f, segs, (hx, hy))
    return f.done()


def grub_corpse(k=1.0, n=5, plates=True):
    """Deflated, split open, sunk in its own acid."""
    f = Fr()
    for x in range(int(-8 * k) - 1, int(9 * k) + 2):
        if x % 3: f.n.put(x, 0, "D" if x % 2 else "d")
    f.n.put(int(-3 * k), -1, "Q"); f.n.put(int(4 * k), 0, "J")
    xs = [-5.0 * k + i * 2.1 * k for i in range(n)]
    for i, x in enumerate(xs):
        ry = (1.2 + 0.4 * (i % 2)) * k
        def sh(nu, nv, d, l, ch, X, Y, i=i):
            if plates and nv < -0.3 and i > 0: return pick("123", l)
            return pick(GRUB_D, l + 0.1)
        ell(f.b, x, -ry - 0.4, 1.9 * k + 0.4, ry, GRUB, shader=sh)
    hx = xs[-1] + 2.2 * k
    ell(f.b, hx, -1.4 * k - 0.4, 1.8 * k, 1.6 * k, CHIT, bias=0.0)
    line(f.b, hx + 1.5 * k, -0.6, hx + 3 * k, 0, "6")
    f.g.put(*P(xs[2], -2.6 * k), "Q"); f.g.put(*P(xs[1], -1.8 * k), "D")
    f.g.put(*P(hx, -1.8 * k), "1")
    return f.done()


def build_grub(outdir):
    G = grub
    idle = [G(hump=0.2, ph=0.0, jaw=0.2, drip=2),
            G(hump=0.5, ph=1.2, jaw=0.35, drip=3, spir=1, st=1.02),
            G(hump=0.6, ph=2.4, jaw=0.45, drip=2, eye="squint", st=1.03),
            G(hump=0.3, ph=3.6, jaw=0.25, drip=1)]
    run = []
    for i in range(6):
        a = i * math.pi / 3
        run.append(G(hump=1.3, ph=a * 1.0 + 1.0, st=0.96 + 0.06 * math.cos(a), legs=a * 2, jaw=0.3, lift=0.3 * max(0, math.sin(a)),
                     dx=0.4 * math.sin(a), drip=1 + (i % 2)))

    def chomp_fx(nfx):
        def fn(f, segs, head):
            hx, hy = head
            for j, (a, b) in enumerate(((6, -2), (7, 0), (6, 2), (8, -1))[:nfx]):
                f.g.put(*P(hx + a, hy + b), "J" if j % 2 == 0 else "Q")
        return fn
    bite = [G(st=0.9, lift=1.4, jaw=0.7, dx=-1.0, eye="wide", drip=1),
            G(st=0.84, lift=2.2, jaw=1.1, dx=-1.6, eye="wide", drip=0, hump=0.4, ph=2),
            G(st=1.1, lift=0.6, jaw=1.2, dx=2.2, eye="wide", drip=0),
            G(st=1.12, lift=0.0, jaw=0.0, dx=3.2, eye="squint", drip=0, extra=chomp_fx(4)),
            G(st=1.08, lift=0.0, jaw=0.1, dx=2.8, eye="squint", drip=2, extra=chomp_fx(2)),
            G(st=1.0, lift=0.3, jaw=0.3, dx=1.4, drip=2),
            G(st=1.0, lift=0.1, jaw=0.25, dx=0.4, drip=2)]

    def spray(nfx, reach):
        def fn(f, segs, head):
            hx, hy = head
            for j in range(nfx):
                t = j / max(1, nfx - 1)
                x = hx + 4 + t * reach
                y = hy - 0.5 - math.sin(t * math.pi) * 2.0 + t * 1.5
                f.g.put(*P(x, y), "J" if j % 2 else "Q")
                if j % 2 == 0: f.g.put(*P(x - 0.5, y + 1), "D", over=False)
        return fn
    spit = [G(lift=1.0, swell=0.3, jaw=0.3, drip=1),
            G(lift=1.8, swell=0.7, jaw=0.4, eye="wide", drip=0, dx=-0.6, st=0.94),
            G(lift=2.3, swell=1.0, jaw=0.5, eye="wide", drip=0, dx=-1.0, st=0.9),
            G(lift=1.4, swell=0.1, jaw=1.3, eye="wide", drip=0, dx=0.6, st=1.05, extra=spray(6, 6)),
            G(lift=1.0, swell=0.0, jaw=0.7, drip=1, dx=0.3, extra=spray(3, 9)),
            G(lift=0.4, swell=0.0, jaw=0.3, drip=2)]
    death = [G(lift=2.2, jaw=1.2, eye="wide", swell=0.8, hump=0.6, ph=1.5, drip=0),
             G(lift=0.8, jaw=0.9, eye="squint", swell=0.4, flat=0.25, dx=-0.5, drip=3),
             grounded(G(lift=0.0, jaw=0.6, eye="dead", flat=0.5, drip=0, st=1.05)),
             grub_corpse()]
    knock = G(lift=1.6, jaw=0.8, eye="squint", st=0.9, dx=-1.0, hump=0.5, ph=2.0, drip=1)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.09] * 6),
             ("Bite", bite, [0.14, 0.12, 0.07, 0.06, 0.12, 0.12, 0.12]),
             ("Spit", spit, [0.14, 0.14, 0.16, 0.06, 0.12, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkGrub", "Bite", bite, "mouth"); note("ZhkGrub", "Spit", spit, "mouth")
    sheet("ZhkGrub", anims, outdir, scale=7)


def maggot(dx=0.0, dy=0.0, curl=0.25, wave=0.0, lift=0.0, hooks=0.3, drip=2, st=1.0, flat=0.0, dead=False, extra=None):
    """v0.10: the larva is its own creature, not a small Acid Grub: a legless, eyeless pale maggot with no chitin at all,
    bent into a C (curl), tapering to a pointed front end with two black mouth hooks and an acid drip, a blunt rear with
    two dark breathing spots. wave runs a peristaltic squeeze down the body; lift raises the front end to bite."""
    f = Fr()
    n = 9
    pts, radii = [], []
    for i in range(n):
        t = i / (n - 1.0)                       # 0 = rear, 1 = front
        x = dx + (t - 0.55) * 9.0 * st * (1 - curl * 0.25)
        # arched like a pale crescent (curl), the front end lifting to bite
        y = dy - 2.4 - curl * 4.2 * math.sin(math.pi * (0.1 + 0.8 * t)) - lift * max(0.0, t - 0.55) * 4.0
        squeeze = 1.0 + 0.16 * math.sin(wave - t * 6.0)
        r = (1.4 + 1.6 * math.sin(math.pi * (0.18 + 0.72 * t)) ** 0.7) * squeeze * (1 - flat * 0.4)
        if t > 0.86: r *= 0.62 + (1 - t) * 1.6        # pointed front
        pts.append((x, y)); radii.append(r)
    def sh(sv, ox, oy, r, l):
        v = oy / max(r, 0.5)                                  # -1 top .. 1 bottom
        fr = sv - math.floor(sv)
        if fr < 0.16 and 0.8 < sv < n - 1.5 and abs(v) < 0.9: return "M" if v > -0.5 else "C"     # ring creases
        if dead: return "M" if v > 0.3 else ("C" if v > -0.4 else "H")
        return "M" if v > 0.55 else ("C" if v > 0.1 else ("H" if v > -0.6 else "X"))
    tube2(f.b, pts, radii, sh)
    rx, ry = pts[0]
    f.b.put(*P(rx - radii[0] * 0.5, ry - 0.2), "f")                                                    # rear spiracle
    hx, hy = pts[-1]
    # mouth hooks: two black hooks parting with hooks, acid between them
    up = [(hx + 0.6, hy - 0.3), (hx + 1.8, hy - 0.6 - hooks * 1.2)]
    lo = [(hx + 0.6, hy + 0.6), (hx + 1.8, hy + 1.0 + hooks * 1.0)]
    polyline(f.b, up, "0"); polyline(f.b, lo, "0")
    f.pts["mouth"] = (hx + 1.6, hy + 0.2)
    if not dead:
        f.g.put(*P(hx + 1.0, hy + 0.2), "Q" if hooks > 0.5 else "D")
        if drip:
            acid_drip(f.g, hx + 1.2, hy + 1.6 + hooks, drip)
    if extra: extra(f, pts, (hx, hy))
    return f.done()


def build_larva(outdir):
    L = maggot
    idle = [L(curl=0.35, wave=0.0), L(curl=0.42, wave=1.6, hooks=0.5), L(curl=0.48, wave=3.1, hooks=0.6, drip=3),
            L(curl=0.4, wave=4.7, hooks=0.4, drip=1)]
    run = [L(curl=0.15 + 0.1 * math.sin(i * math.pi / 3), wave=i * 1.05, st=1.0 + 0.1 * math.sin(i * math.pi / 3),
             dx=0.6 * math.sin(i * math.pi / 3), drip=i % 2 + 1) for i in range(6)]
    bite = [L(curl=0.5, lift=0.4, hooks=0.9, dx=-0.6, drip=0), L(curl=0.6, lift=0.8, hooks=1.2, dx=-1.0, drip=0),
            L(curl=0.1, lift=0.3, hooks=1.2, dx=1.4, st=1.15, drip=0), L(curl=0.0, hooks=0.0, dx=2.0, st=1.18, drip=0),
            L(curl=0.15, hooks=0.2, dx=1.2, st=1.06, drip=1), L(curl=0.3, hooks=0.3, dx=0.4, drip=1)]
    def burst(f, pts, h):
        for k in range(5):
            f.g.put(*P(h[0] - 4 + k * 2, h[1] - 2 - (k % 2)), "Q" if k % 2 else "J")
    death = [L(curl=0.7, lift=0.6, hooks=1.2, drip=0), L(curl=0.9, flat=0.2, hooks=0.6, drip=2, extra=burst),
             grounded(L(curl=0.5, flat=0.5, hooks=0.2, drip=0, dead=True)), grounded(L(curl=0.2, flat=0.7, hooks=0.0, drip=0, dead=True))]
    knock = L(curl=0.8, lift=0.6, hooks=0.8, dx=-0.6, st=0.9, drip=0)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.07] * 6),
             ("Bite", bite, [0.12, 0.1, 0.06, 0.06, 0.1, 0.1])]
    anims += std_tail(idle[0], death, [0.08, 0.1, 0.12, 0.4], knock)
    note("ZhkLarva", "Bite", bite, "mouth")
    sheet("ZhkLarva", anims, outdir, scale=9)


# ================================================================== RESIN BEETLE (T1)
def beetle(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, jaw=0.25, head=0.0, throat=0.0, crack=0.0, eye="open", lift=0.0,
           hunker=0.0, extra=None, beads=1.0):
    f = Fr()
    cx, cy = dx - 1.8, dy - 5.8 - lift + hunker * 1.6
    piv = (cx + 2, cy + 3)
    R = lambda x, y: rot((x, y), piv, tilt)
    # legs: three near (outlined, under-layer), three far (shadow)
    hips = [(-3.2, 2.4), (0.0, 2.9), (3.0, 2.6)]
    feet = [(-7.0, 0), (-1.2, 0), (5.2, 0)]
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, ((hx, hy), (fx, fy)) in enumerate(zip(hips, feet)):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(cx + hx - (0 if side else 0.8), cy + hy)
            ft = (dx + fx + 1.0 * math.sin(pha) - (0 if side else 1.0) + (0.6 if j == 2 else 0) * hunker,
                  -max(0.0, 1.0 * math.cos(pha)) * (1 - hunker))
            leg(cv_, hp, ft, 3.0, 3.0, -1 if fx < cx + hx else 1, cols=("3", "4") if side else ("2", "2"), knee_hi="5" if side else None)
            cv_.put(*P(ft[0] + 0.5, ft[1]), "4" if side else "2")
    # elytra dome: dark glossy chitin, a resin seam down the middle, resin beads welling out of pores
    ex, ey = R(cx, cy)
    def shell(nu, nv, d, l, ch, X, Y):
        if nv > 0.55: return pick("12", l)                                       # v0.10: no outline-black inside the shell
        if 0.28 < d < 0.5 and -0.75 < nu < 0.1 and nv < -0.2: return "5"     # specular arc
        if abs(nu + nv * 0.35 - 0.15) < 0.1 and nv < 0.35: return "6"          # seam
        return pick("12334", l)
    ell(f.b, ex, ey, 5.6, 3.9, CHIT_L, ang=tilt, bias=0.0, shader=shell, vmax=0.95)
    if crack > 0:  # elytra lift a little: amber membrane glow in the crack
        line(f.b, ex - 3, ey - 2.8 - crack, ex + 2, ey - 3.4 - crack, "3")
        line(f.g, ex - 2, ey - 2.2, ex + 1.5, ey - 2.8, "8")
    if beads:
        for (bx, by, r) in ((-2.6, -1.6, 1.0), (0.8, -2.4, 0.9), (-0.6, 0.4, 0.7)):
            p = R(cx + bx, cy + by)
            ell(f.b, p[0], p[1], r * beads + 0.2, r * beads + 0.2, AMB_L, bias=0.3)
    # pronotum + head
    px_, py_ = R(cx + 5.0, cy + 0.2)
    ell(f.b, px_, py_, 2.6, 2.5, "1123", ang=tilt, bias=0.1)
    f.b.put(*P(px_ - 1, py_ - 1.4), "5")
    hx, hy = R(cx + 7.0, cy + 1.2 + head)
    ell(f.b, hx, hy, 1.7, 1.6, CHIT, bias=0.1)
    if throat > 0:
        ell(f.b, hx - 0.6, hy + 1.6, 1.1 + throat * 0.9, 0.9 + throat * 0.8, AMB_L, bias=0.4)
        if throat > 0.6: f.g.put(*P(hx - 1, hy + 1.2), "E")
    # mandibles: thick sickles, amber edged
    a = math.radians(tilt)
    def M(ox, oy):
        return hx + ox * math.cos(a) - oy * math.sin(a), hy + ox * math.sin(a) + oy * math.cos(a)
    up = [M(1.0, -0.6), M(2.6, -1.3 - jaw * 1.6), M(3.9, -0.3 - jaw * 1.0)]
    lo = [M(1.0, 0.7), M(2.6, 1.5 + jaw * 1.5), M(3.7, 0.7 + jaw * 1.0)]
    polyline(f.b, up, "4"); polyline(f.b, lo, "3")
    f.b.put(*P(*up[1]), "5"); f.b.put(*P(*up[-1]), "9"); f.b.put(*P(*lo[-1]), "8")
    f.pts["mouth"] = M(3.4, 0.3)
    if eye == "open": f.g.put(*P(hx + 0.4, hy - 0.7), "J")
    elif eye == "wide": f.g.put(*P(hx + 0.4, hy - 0.7), "L"); f.g.put(*P(hx - 0.4, hy - 0.8), "Q")
    elif eye == "squint": f.g.put(*P(hx + 0.4, hy - 0.5), "D")
    else: f.g.put(*P(hx + 0.4, hy - 0.7), "1")
    if extra: extra(f, (hx, hy), M)
    return f.done()


def beetle_corpse():
    f = Fr()
    # on its back: pale-brown underside up, legs folded in the air, a spilled resin blob
    ell(f.b, -1.5, -2.6, 5.6, 2.6, "2345", bias=0.0)
    ell(f.b, -1.0, -3.6, 4.0, 1.4, "34", bias=0.2)
    for j, x in enumerate((-4.0, -1.5, 1.2)):
        polyline(f.b, [(x, -5), (x - 1 + 2 * (j % 2), -7), (x + (1 if j % 2 else -1), -8)], "23")
    ell(f.b, 5.0, -1.8, 1.6, 1.5, CHIT)
    ell(f.n, -7.0, -0.6, 2.2, 0.9, AMB_L, bias=0.3)
    f.g.put(-7, -1, "E"); f.g.put(5, -2, "1")
    return f.done()


def build_beetle(outdir):
    B = beetle
    idle = [B(jaw=0.25), B(jaw=0.4, dy=0.3, legs=0.3, beads=1.08), B(jaw=0.5, dy=0.3, legs=0.5, eye="squint", beads=1.12),
            B(jaw=0.3, legs=0.2, beads=1.04)]
    # v0.8: the gait is offset half a step (pi/6) and the beetle leans into it, so no Run frame repeats an Idle pose
    run = [B(legs=i * math.pi / 3 + math.pi / 6, dy=-0.5 * abs(math.sin(i * math.pi / 3 + math.pi / 6)),
             tilt=-1.5 - 2 * math.sin(i * math.pi / 3 + math.pi / 6), head=0.15, jaw=0.3 + 0.2 * (i % 2)) for i in range(6)]

    def snap_fx(nfx):
        def fn(f, head, M):
            for j, (a, b) in enumerate(((5.0, -1.5), (5.5, 0.5), (6.0, 2.0), (4.5, -3.0))[:nfx]):
                f.g.put(*P(*M(a, b)), "E" if j % 2 == 0 else "9")
        return fn
    snap = [B(jaw=0.9, tilt=-4, dx=-0.6, eye="wide", legs=0.4),
            B(jaw=1.3, tilt=-8, dx=-1.2, head=-0.6, eye="wide", legs=0.8, lift=0.4),
            B(jaw=1.4, tilt=4, dx=2.0, eye="wide", legs=1.6),
            B(jaw=0.0, tilt=6, dx=3.0, eye="squint", legs=2.0, extra=snap_fx(4)),
            B(jaw=0.1, tilt=4, dx=2.5, eye="squint", legs=2.0, extra=snap_fx(2)),
            B(jaw=0.3, tilt=0, dx=0.8, legs=1.0)]

    def resin_fx(nfx, reach):
        def fn(f, head, M):
            for j in range(nfx):
                t = j / max(1, nfx - 1)
                p = M(3.8 + t * reach, -0.4 - math.sin(t * 3.0) * 2.2)
                f.g.put(*P(*p), "9" if j % 2 else "8")
                f.g.put(*P(p[0], p[1] + 1), "7", over=False)
        return fn
    resin = [B(tilt=-6, throat=0.2, jaw=0.3, beads=1.15, crack=0.5),
             B(tilt=-12, throat=0.6, jaw=0.4, eye="wide", beads=1.25, crack=1.0, dx=-0.6),
             B(tilt=-16, throat=1.0, jaw=0.6, eye="wide", beads=1.3, crack=1.0, dx=-1.0, lift=0.5),
             B(tilt=-4, throat=0.1, jaw=1.4, eye="wide", beads=0.7, dx=0.8, extra=resin_fx(6, 6)),
             B(tilt=-2, throat=0.0, jaw=0.8, beads=0.8, dx=0.4, extra=resin_fx(3, 9)),
             B(tilt=0, jaw=0.3, beads=0.9)]
    death = [B(tilt=-14, jaw=1.2, eye="wide", dx=-0.5, legs=1.0, lift=0.6),
             B(tilt=-34, jaw=0.8, eye="dead", dy=0.5, legs=2.0, hunker=0.3),
             grounded(B(tilt=-150, jaw=0.6, eye="dead", legs=2.5, beads=0.6)),
             beetle_corpse()]
    knock = B(tilt=-12, jaw=0.9, eye="squint", dx=-0.8, legs=0.8, lift=0.5)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.075] * 6),
             ("Snap", snap, [0.14, 0.14, 0.07, 0.06, 0.12, 0.14]),
             ("Resin", resin, [0.14, 0.14, 0.16, 0.06, 0.12, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkBeetle", "Snap", snap, "mouth"); note("ZhkBeetle", "Resin", resin, "mouth")
    sheet("ZhkBeetle", anims, outdir, scale=7, remap=LIFT_BEETLE)


# ================================================================== BROOD DRONE (T1, flier)
def wing(c, root, ang, L, W, ph=0, cols=("l", "~", "z")):
    """A translucent insect wing from root, pointing ang (deg), length L, width W. Veins + membrane.
    cols = (membrane, light membrane, vein)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    pts = []
    for i in range(12):
        t = i / 11.0
        w = W * math.sin(math.pi * min(1.0, t * 1.05)) * (0.6 + 0.4 * (1 - t))
        pts.append((root[0] + ux * L * t + nx * w, root[1] + uy * L * t + ny * w))
    for i in range(11, -1, -1):
        t = i / 11.0
        w = W * 0.35 * math.sin(math.pi * t)
        pts.append((root[0] + ux * L * t - nx * w, root[1] + uy * L * t - ny * w))
    poly(c, pts, cols[0], over=False, shade=lambda x, y: cols[1] if (x + 2 * y + ph) % 4 == 0 else cols[0])
    polyline(c, pts[:12], cols[1])
    line(c, root[0], root[1], root[0] + ux * L * 0.95, root[1] + uy * L * 0.95, cols[2])


def drone(dx=0.0, dy=0.0, tilt=0.0, wph=0, curl=0.0, legs=0.0, eye="open", extra=None, streak=0, fold=False):
    f = Fr()
    cx, cy = dx, dy - 7.2
    piv = (cx, cy)
    R = lambda x, y: rot((x, y), piv, tilt)
    # dangling legs (far set in shadow)
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, hx in enumerate((-0.9, 0.4, 1.5)):
            h = R(cx + hx - (0.5 if not side else 0), cy + 1.6)
            sw = math.sin(legs + j) * 0.8
            k = (h[0] - 0.6 + sw, h[1] + 1.8)
            e = (k[0] + 0.8 - 0.3 * j, k[1] + 1.6)
            line(cv_, h[0], h[1], k[0], k[1], "2" if side else "1")
            line(cv_, k[0], k[1], e[0], e[1], "3" if side else "1")
    # abdomen: banded amber/black, hinged at the waist; curl swings the sting under and forward
    wst = R(cx - 1.9, cy + 0.6)
    aa = 150 - 95 * curl + tilt
    ar = math.radians(aa)
    ac = (wst[0] + 3.4 * math.cos(ar), wst[1] + 3.4 * math.sin(ar))
    def band(nu, nv, d, l, ch, X, Y):
        b = int((nu + 1.0) * 2.6)
        if b % 2 == 1: return pick("123", l)
        return pick(AMB_L, l - 0.1)
    ell(f.b, ac[0], ac[1], 3.6, 2.3, AMB_L, ang=aa + 180, bias=0.1, shader=band)
    tip = (wst[0] + 7.0 * math.cos(ar), wst[1] + 7.0 * math.sin(ar))
    st_end = (wst[0] + 8.8 * math.cos(ar), wst[1] + 8.8 * math.sin(ar))
    line(f.b, tip[0], tip[1], st_end[0], st_end[1], "5")
    f.g.put(*P(*st_end), "J")
    f.pts["sting"] = st_end
    # thorax + head
    ell(f.b, *R(cx, cy), 2.5, 2.2, CHIT_L, ang=tilt, bias=0.1)
    tp = R(cx - 0.3, cy - 1.2)
    line(f.b, tp[0] - 1, tp[1] + 0.3, tp[0] + 1.2, tp[1] - 0.2, "8")          # amber collar
    hx, hy = R(cx + 3.2, cy - 0.4)
    ell(f.b, hx, hy, 1.8, 1.9, CHIT, bias=0.15)
    line(f.b, hx + 1.4, hy + 1.2, hx + 2.4, hy + 1.6, "8")                     # mandible
    # antennae
    line(f.b, hx + 0.4, hy - 1.6, hx + 1.6, hy - 3.6, "2")
    f.b.put(*P(hx + 2.2, hy - 3.8), "3")
    # compound eye: big acid green
    ex, ey = hx + 0.7, hy - 0.3
    if eye != "dead":
        for (a, b, ch) in ((0, 0, "Q"), (0, -1, "J" if eye != "squint" else "Q"), (1, 0, "D"), (1, -1, "Q")):
            f.g.put(*P(ex + a, ey + b), ch)
        if eye == "wide": f.g.put(*P(ex, ey - 1), "L")
    else:
        f.g.put(*P(ex, ey), "1"); f.g.put(*P(ex, ey - 1), "2")
    # wings over the top (no outline: they're thin and see-through)
    root = R(cx - 0.4, cy - 1.8)
    if fold:
        wing(f.g, root, 180 + tilt * 0.5, 7.0, 1.6)
    else:
        angs = [-112, -142, -172, -138][wph % 4]
        wing(f.g, (root[0] - 0.5, root[1] + 0.3), angs + 26 + tilt * 0.3, 5.2, 1.8, wph + 1)
        wing(f.g, root, angs + tilt * 0.3, 6.0, 2.6, wph)
    for s in range(streak):
        y = cy - 2 + s * 2
        line(f.g, cx - 6 - s * 2, y - 3 + s, cx - 10 - s * 2, y - 5 + s, "l" if s % 2 else "z", over=False)
    if extra: extra(f, (hx, hy), st_end)
    return f.done()


def drone_corpse():
    f = Fr()
    ell(f.b, -2.5, -1.8, 3.4, 1.8, AMB_L, bias=0.0,
        shader=lambda nu, nv, d, l, ch, X, Y: pick("123", l) if int((nu + 1) * 2.6) % 2 else pick(AMB, l))
    ell(f.b, 1.6, -2.0, 2.0, 1.7, CHIT_L)
    ell(f.b, 4.2, -1.6, 1.5, 1.4, CHIT)
    wing(f.g, (0.0, -3.0), -160, 6.0, 1.6)
    for x in (0.5, 1.8, 3.0):
        line(f.b, x, -3.5, x + 0.5, -5.5, "2")
    f.g.put(4, -2, "D"); f.g.put(-6, -1, "J")
    return f.done()


def build_drone(outdir):
    D_ = drone
    idle = [D_(wph=i, dy=[0, -0.6, -1, -0.4][i], legs=i * 0.8, curl=0.05 * (i % 2)) for i in range(4)]
    run = [D_(wph=i % 4, dy=-0.5 * math.sin(i * math.pi / 3), tilt=8, legs=i, curl=0.1) for i in range(6)]

    def dart_fx(n):
        def fn(f, head, st):
            for j in range(n):
                f.g.put(*P(st[0] + 1 + j, st[1] - (j % 2)), "J" if j == 0 else "Q")
        return fn
    sting = [D_(wph=0, curl=0.35, tilt=-4, eye="wide", dy=-1.0),
             D_(wph=1, curl=0.75, tilt=-10, dx=-0.8, dy=-2.4, eye="wide"),
             D_(wph=2, curl=1.0, tilt=-6, dx=-1.0, dy=-3.4, eye="wide"),
             D_(wph=3, curl=1.05, tilt=2, dx=0.6, dy=-3.4, eye="squint", extra=dart_fx(3)),
             D_(wph=0, curl=0.6, tilt=0, dx=0.3, dy=-1.6),
             D_(wph=1, curl=0.2)]
    dive = [D_(wph=0, dy=-1.6, tilt=-12, curl=0.3, eye="wide"),
            D_(wph=2, dy=-2.0, dx=-1.5, tilt=-20, curl=0.6, eye="wide"),
            D_(fold=True, dx=1.5, dy=1.5, tilt=38, curl=0.55, streak=2),
            D_(fold=True, dx=2.0, dy=2.4, tilt=42, curl=0.6, streak=3),
            D_(fold=True, dx=2.0, dy=2.4, tilt=40, curl=0.6, streak=3),
            D_(wph=1, dx=1.0, dy=0.5, tilt=4, curl=0.5),
            D_(wph=3, dy=-0.5, curl=0.1)]
    death = [D_(wph=1, tilt=-30, curl=0.6, eye="wide", dy=-1),
             D_(fold=True, tilt=-70, curl=0.2, eye="dead", dy=2.5),
             grounded(D_(fold=True, tilt=-150, curl=0.0, eye="dead")),
             drone_corpse()]
    knock = D_(wph=2, tilt=-22, curl=0.5, dx=-1, eye="squint")
    anims = [("Idle", idle, [0.07, 0.07, 0.07, 0.07]), ("Run", run, [0.06] * 6),
             ("Sting", sting, [0.12, 0.14, 0.14, 0.06, 0.12, 0.12]),
             ("Dive", dive, [0.14, 0.14, 0.08, 0.1, 0.1, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkDrone", "Sting", sting, "sting"); note("ZhkDrone", "Dive", dive, "sting")
    sheet("ZhkDrone", anims, outdir, scale=7)


# ================================================================== ACID SPITTER (T2, Acid Grub line)
def acid_sac(f, cx, cy, rx, ry, ang=0.0, ph=0, glow=1.0, stretch=1.0):
    """The engorged acid gland: dark chitin plates stretched apart over glowing acid membrane, bubbles
    rising inside, a chitin cradle along the bottom. stretch (>1 = swollen) widens the glowing seams."""
    seam = 0.16 + 0.32 * max(0.0, stretch - 0.75)
    def sh(nu, nv, d, l, ch, X, Y):
        if nv > 0.55: return pick("1123", l + 0.2)
        u = (nu * 0.9 + 1.0) * 2.0 + nv * 0.6
        fr = u - math.floor(u)
        if fr < seam or nv > 0.4:
            if l > 0.55 and d < 0.6: return "J" if glow > 0.7 else "Q"
            return pick("dDQ", l + 0.25 * glow)
        if l > 0.62 and d < 0.55 and fr > seam + 0.15: return "5"
        return pick("1234", l)
    ell(f.b, cx, cy, rx, ry, ACID, ang=ang, bias=0.0, shader=sh)
    rnd = random.Random(ph * 7 + 3)
    for _ in range(3):
        bx, by = cx + rnd.uniform(-0.7, 0.5) * rx, cy + rnd.uniform(-0.4, 0.3) * ry - (ph % 3) * 0.6
        if f.b.px.get(P(bx, by)) in ("d", "D", "Q", "J"):
            f.g.put(*P(bx, by), "L" if glow > 0.9 else "J")


def spitter(dx=0.0, dy=0.0, tilt=0.0, sac=1.0, ph=0, legs=0.0, spout=-15.0, head=0.0, rear=0.0, eye="open",
            glow=1.0, jaw=0.0, extra=None, crouch=0.0):
    f = Fr()
    cx, cy = dx, dy - 9.0 + crouch * 2.0
    piv = (cx, cy)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # legs: high-kneed, spidery; near three outlined, far three in shadow
    hips = [(-2.5, 1.8), (0.5, 2.2), (3.2, 1.8)]
    feet = [(-10.0, 0), (-3.0, 0), (8.5, 0)]
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, ((hx, hy), (fx, _)) in enumerate(zip(hips, feet)):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(hx - (0 if side else 1.0), hy)
            ft = (dx + fx * (1 - 0.15 * crouch) + 1.2 * math.sin(pha) - (0 if side else 1.5), -max(0.0, 1.2 * math.cos(pha)))
            bend = 1 if ft[0] > hp[0] else -1
            leg(cv_, hp, ft, 5.4 - crouch, 6.0, bend, cols=("3", "4") if side else ("1", "2"), knee_hi="5" if side else None)
            cv_.put(*P(ft[0], ft[1]), "4" if side else "2")
    # ovipositor at the rear (lowered for Egg)
    rp = R(-7.5, 2.0 + rear * 3.0)
    # v0.10 lineage (Acid Grub, its only parent): the ovipositor is a ringed tail of grub flesh with an acid pore
    tube(f.u, [R(-5.5, 1.0), rp], [1.6, 0.9], GRUB)
    for k in range(3):
        q = (R(-5.5, 1.0)[0] + (rp[0] - R(-5.5, 1.0)[0]) * (0.25 + k * 0.25), R(-5.5, 1.0)[1] + (rp[1] - R(-5.5, 1.0)[1]) * (0.25 + k * 0.25))
        f.u.put(*P(*q), "f"); f.u.put(*P(q[0], q[1] - 1), "f")
    f.u.put(*P(*rp), "Q")
    f.pts["rear"] = rp
    # thorax + head; v0.9 lineage (Acid Grub): the thorax is the grub's pale segmented flesh with acid spiracles
    def gsh(nu, nv, d, l, ch, X, Y):
        if abs(((nu + 1.0) * 2.0) % 1.0) < 0.15: return "f"
        return pick(GRUB, l + 0.1)
    ell(f.b, *R(2.6, 0.6), 4.2, 3.0, "1234", ang=tilt, bias=0.1, shader=gsh)
    for k in range(3):
        f.g.put(*P(*R(0.8 + k * 1.6, 1.4)), "Q" if glow > 0.5 else "D")
    hx, hy = R(7.0, -0.2 + head)
    for yy in (-1.5, -0.5, 0.5, 1.5):
        f.b.put(*P(hx - 2.4, hy + yy), "0")
    ell(f.b, hx, hy, 2.6, 2.3, "2345", bias=0.0)
    # mouth tube (the spout)
    ta = math.radians(spout + tilt)
    t0 = (hx + 1.8 * math.cos(ta), hy + 1.8 * math.sin(ta) + 0.6)
    t1 = (t0[0] + 3.4 * math.cos(ta), t0[1] + 3.4 * math.sin(ta))
    tube(f.b, [t0, t1], [1.2, 0.9 + jaw * 0.5], "2345")
    f.b.put(*P(*t1), "1")
    f.g.put(*P(t1[0] + 0.5 * math.cos(ta), t1[1] + 0.5 * math.sin(ta)), "Q" if glow > 0.5 else "D")
    f.pts["mouth"] = (t1[0] + 1.0 * math.cos(ta), t1[1] + 1.0 * math.sin(ta))
    # eyes: a cluster of three acid ocelli
    if eye != "dead":
        for (a, b, ch) in ((0.6, -1.2, "J"), (1.6, -0.8, "Q"), (-0.4, -1.4, "Q")):
            f.g.put(*P(hx + a, hy + b), "L" if eye == "wide" and ch == "J" else (ch if eye != "squint" else "D"))
    else:
        f.g.put(*P(hx + 0.6, hy - 1.2), "1")
    # the grub's new adult wings (it pupated into the spitter), too small to fly, buzzing behind the sac
    wr = R(0.6, -1.6)
    wing(f.n, (wr[0] - 0.8, wr[1]), -150 + tilt + (ph % 2) * 10, 7.0, 2.2, ph)
    # the great acid sac on its back
    sx, sy = R(-3.6, -4.6)
    acid_sac(f, sx, sy, 6.6 * sac ** 0.5, 6.0 * sac, ang=tilt - 8, ph=ph, glow=glow, stretch=sac)
    wing(f.g, wr, -126 + tilt + (ph % 2) * 14, 7.4, 2.4, ph + 1)
    if extra: extra(f, (hx, hy), f.pts["mouth"])
    return f.done()


def spitter_corpse():
    f = Fr()
    # collapsed on its belly, sac burst and spilled, legs curled
    for x in range(-13, 10):
        if (x * 7) % 5: f.n.put(x, 0, "D" if x % 3 else "Q")
    ell(f.b, -4.0, -2.4, 6.0, 2.4, "dDQ", bias=0.0,
        shader=lambda nu, nv, d, l, ch, X, Y: "d" if (X + 2 * Y) % 4 == 0 else pick("dDQ", l))
    ell(f.b, 3.0, -2.6, 3.8, 2.4, "1234", bias=0.1)
    ell(f.b, 7.0, -2.0, 2.2, 1.9, "1234", bias=0.1)
    for (x0, x1) in ((-8, -11), (-1, -2), (5, 9)):
        polyline(f.b, [(x0, -3), (x0 + (x1 - x0) * 0.5, -6), (x1, -4)], "34")
    f.g.put(-6, -4, "J"); f.g.put(-2, -3, "L"); f.g.put(7, -3, "1")
    return f.done()


def build_spitter(outdir):
    S_ = spitter
    idle = [S_(sac=1.0, ph=0), S_(sac=1.04, ph=1, dy=0.3, legs=0.2), S_(sac=1.07, ph=2, dy=0.4, legs=0.3, glow=1.2),
            S_(sac=1.03, ph=3, dy=0.2, legs=0.1, eye="squint")]
    run = [S_(legs=i * math.pi / 3, dy=-0.6 * abs(math.sin(i * math.pi / 3)), tilt=1.5 * math.sin(i * math.pi / 3),
              sac=1.0 + 0.04 * math.cos(i * math.pi / 3), ph=i) for i in range(6)]

    def spray(n, reach):
        def fn(f, head, m):
            for j in range(n):
                t = j / max(1, n - 1)
                f.g.put(*P(m[0] + 1 + t * reach, m[1] - 1 - t * reach * 0.7 + (j % 2)), "J" if j % 2 == 0 else "Q")
        return fn
    lob = [S_(sac=1.12, ph=0, head=0.8, spout=0, glow=1.1, crouch=0.3),
           S_(sac=1.22, ph=1, head=1.2, spout=10, tilt=4, glow=1.3, crouch=0.6, eye="wide"),
           S_(sac=0.92, ph=2, head=-0.8, spout=-45, tilt=-6, glow=1.4, eye="wide"),
           S_(sac=0.82, ph=3, head=-1.0, spout=-42, tilt=-8, glow=0.8, jaw=1.0, eye="wide", extra=spray(5, 5)),
           S_(sac=0.88, ph=4, head=-0.4, spout=-30, tilt=-4, glow=0.7, extra=spray(2, 7)),
           S_(sac=0.96, ph=5, spout=-18, glow=0.9)]

    def egg_fx(stage):
        def fn(f, head, m):
            r = f.pts["rear"]
            if stage == 1:
                ell(f.b, r[0] - 0.8, r[1] + 0.5, 1.4, 1.2, GRUB, bias=0.3)
            elif stage >= 2:
                ell(f.b, r[0] - 1.5, min(-1.6, r[1] + 1.6), 1.8, 1.6, GRUB, bias=0.3)
                f.g.put(*P(r[0] - 2, min(-2, r[1] + 1)), "Q")
        return fn
    egg = [S_(tilt=-4, rear=0.4, sac=1.05, ph=0),
           S_(tilt=-9, rear=1.0, sac=1.12, ph=1, crouch=0.4, eye="squint"),
           S_(tilt=-11, rear=1.4, sac=1.0, ph=2, crouch=0.6, eye="squint", extra=egg_fx(1)),
           S_(tilt=-12, rear=1.6, sac=0.9, ph=3, crouch=0.7, eye="squint", extra=egg_fx(2)),
           S_(tilt=-6, rear=0.8, sac=0.92, ph=4, crouch=0.3),
           S_(tilt=-2, rear=0.2, sac=0.96, ph=5),
           S_(sac=1.0, ph=0)]
    death = [S_(tilt=-10, sac=1.3, glow=1.5, eye="wide", head=1, crouch=0.3),
             S_(tilt=-6, sac=0.7, glow=0.6, eye="dead", crouch=1.0, dy=0.5),
             grounded(S_(tilt=-4, sac=0.5, glow=0.3, eye="dead", crouch=1.6)),
             spitter_corpse()]
    knock = S_(tilt=-10, sac=1.1, eye="squint", dx=-1, head=1.0)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.09] * 6),
             ("Lob", lob, [0.14, 0.16, 0.1, 0.06, 0.14, 0.16]),
             ("Egg", egg, [0.12, 0.14, 0.16, 0.16, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkSpitter", "Lob", lob, "mouth"); note("ZhkSpitter", "Egg", egg, "rear")
    sheet("ZhkSpitter", anims, outdir, scale=6, remap=LIFT)


# ================================================================== HIVE SOLDIER (T2, Acid Grub line)
def scythe(c, g, sh, a1, a2, L1=4.0, L2=8.0, far=False, smear=None):
    """Raptorial forelimb: upper arm from the shoulder at a1, a long serrated blade at a2. Returns the tip."""
    el = (sh[0] + L1 * math.cos(math.radians(a1)), sh[1] + L1 * math.sin(math.radians(a1)))
    tip = (el[0] + L2 * math.cos(math.radians(a2)), el[1] + L2 * math.sin(math.radians(a2)))
    if far:
        line(c, sh[0], sh[1], el[0], el[1], "1"); line(c, el[0], el[1], tip[0], tip[1], "2")
        return tip
    tube(c, [sh, el], [1.1, 0.9], "2344")
    a = math.radians(a2)
    nx, ny = -math.sin(a), math.cos(a)
    # the blade: chitin spine with an amber cutting edge on the inner side, serrations
    pts = [el, (el[0] + nx * 1.4 + (tip[0] - el[0]) * 0.35, el[1] + ny * 1.4 + (tip[1] - el[1]) * 0.35), tip]
    poly(c, [el, pts[1], tip, (el[0] - nx * 0.6, el[1] - ny * 0.6)], "7",
         shade=lambda x, y: "8" if ((x - el[0]) * nx + (y - el[1]) * ny) > 0.6 else "7")
    line(c, el[0], el[1], tip[0], tip[1], "3")
    for t in (0.3, 0.55, 0.8):
        q = (el[0] + (tip[0] - el[0]) * t + nx * 1.1, el[1] + (tip[1] - el[1]) * t + ny * 1.1)
        c.put(*P(*q), "9")
    c.put(*P(*tip), "9")
    c.put(*P(*el), "5")
    if smear:
        for k, (ang, rad) in enumerate(smear):
            pass
    return tip


def soldier(dx=0.0, dy=0.0, lean=0.0, sink=0.0, near=(-60, -20), farm=(-70, -35), jaw=0.2, legs=0.0, eye="open",
            gaster=0.0, extra=None, smear=None, mound=0.0, crack=0.0, dirt=0, head=0.0, hidden=False):
    f = Fr()
    oy = dy + sink
    # mound of earth (burrow)
    if mound > 0:
        w = 7.0 + 2.0 * mound
        h = 2.0 + 2.5 * mound
        def msh(nu, nv, d, l, ch, X, Y):
            if crack and abs(nu * 3 + nv * 1.5 - 0.3 * math.sin(Y)) < 0.35 * crack: return "1" if crack < 0.8 else "Q"
            return pick("jIZ", l + 0.1)
        ell(f.b, dx, 0.5, w, h, DIRT, vmax=0.0, shader=msh)
        for k in range(int(3 * mound)):
            f.b.put(*P(dx - w * 0.6 + k * 2.6, -h * 0.55 - (k % 2)), "Z")
    if not hidden:
        cx, cy = dx, oy - 9.5
        piv = (cx, cy)
        R = lambda x, y: rot((cx + x, cy + y), piv, lean)
        # legs: four walking legs from the mesosoma (near two outlined, far two shadowed)
        for side, cv_ in ((0, f.n), (1, f.u)):
            for j, (hx, fx) in enumerate(((-1.0, -7.5), (1.0, 3.5))):
                pha = legs + j * 2.6 + side * math.pi
                hp = R(hx - (0 if side else 0.8), 1.2)
                ft = (dx + fx + 1.3 * math.sin(pha) - (0 if side else 1.2), oy - max(0.0, 1.2 * math.cos(pha)))
                leg(cv_, hp, ft, 4.4, 5.6, -1 if ft[0] < hp[0] else 1, cols=("3", "4") if side else ("1", "2"),
                    knee_hi="5" if side else None)
        # far scythe arm
        sh_far = R(3.4, -3.6)
        scythe(f.n, f.g, sh_far, farm[0], farm[1], far=True)
        # gaster (abdomen) with amber bands, petiole
        gx, gy = R(-6.2, 0.4 + gaster)
        # v0.9 lineage (Acid Grub): the gaster is the grub's pale ringed flesh with acid spiracles
        def gsh(nu, nv, d, l, ch, X, Y):
            b = (nu + 1.0) * 2.4 + 0.5
            if (b - math.floor(b)) < 0.18 and d < 0.9: return "f"
            if nv > 0.55: return pick("fM", l + 0.3)
            return pick(GRUB, l + 0.1)
        ell(f.b, gx, gy, 4.6, 3.7, "1234", ang=lean - 15, bias=0.05, shader=gsh)
        for k in range(3):
            f.g.put(*P(gx - 2.4 + k * 2.0, gy + 0.6 - k * 0.3), "Q" if eye != "dead" else "d")
        ell(f.b, *R(-1.6, -0.2), 1.3, 1.2, "234", bias=0.1)
        # mesosoma: angled up toward the head
        tube(f.b, [R(-0.6, 0.0), R(1.8, -2.0), R(3.6, -4.2)], [1.9, 2.1, 1.8], "1234", bias=0.1)
        f.b.put(*P(*R(1.2, -2.6)), "5")
        # v0.10 lineage (Acid Grub, its only parent): the grub's dark back plates over the mesosoma, an acid pore
        ell(f.b, *R(1.4, -3.4), 3.0, 1.9, "1234", ang=lean - 40, bias=0.1, vmax=0.3)
        f.g.put(*P(*R(0.6, -2.6)), "Q" if eye != "dead" else "d")
        # head: big, armoured, sickle mandibles
        hx, hy = R(6.4, -6.2 + head)
        ell(f.b, hx, hy, 3.6, 3.1, "1234", ang=lean, bias=0.1)
        f.b.put(*P(hx - 1.5, hy - 2.0), "5"); f.b.put(*P(hx - 0.5, hy - 2.3), "4")
        a = math.radians(lean)
        M = lambda ox, oy_: (hx + ox * math.cos(a) - oy_ * math.sin(a), hy + ox * math.sin(a) + oy_ * math.cos(a))
        up = [M(2.4, 0.4), M(4.4, -0.4 - jaw * 1.4), M(5.6, 1.0 - jaw * 0.6)]
        lo = [M(2.2, 1.6), M(4.2, 2.6 + jaw * 1.2), M(5.2, 1.6 + jaw * 0.8)]
        polyline(f.b, up, "4"); polyline(f.b, lo, "3")
        f.b.put(*P(*up[-1]), "9"); f.b.put(*P(*lo[-1]), "8"); f.b.put(*P(*up[1]), "7")
        # antennae: elbowed, swept back
        e1 = M(0.4, -2.8); e2 = M(0.0, -5.4); e3 = M(3.2, -6.6)
        polyline(f.b, [e1, e2, e3], "2")
        f.b.put(*P(*e3), "3")
        if eye != "dead":
            f.g.put(*P(*M(1.2, -0.8)), "L" if eye == "wide" else ("J" if eye == "open" else "D"))
            f.g.put(*P(*M(0.2, -1.0)), "Q" if eye != "squint" else "D")
        else:
            f.g.put(*P(*M(1.2, -0.8)), "1")
        f.pts["head"] = (hx, hy)
        # near scythe arm over everything
        sh_near = R(3.2, -3.0)
        tip = scythe(f.b, f.g, sh_near, near[0], near[1])
        f.pts["tip"] = tip
        if smear:
            el = (sh_near[0] + 4.0 * math.cos(math.radians(near[0])), sh_near[1] + 4.0 * math.sin(math.radians(near[0])))
            for k in range(14):
                t = k / 13.0
                ang = math.radians(smear[0] + (smear[1] - smear[0]) * t)
                for rr, ch in ((8.6, "E"), (7.4, "9"), (6.2, "7")):
                    if rr == 6.2 and t < 0.4: continue
                    f.g.put(*P(el[0] + rr * math.cos(ang), el[1] + rr * math.sin(ang)), ch, over=False)
    if dirt:
        rnd = random.Random(dirt * 13)
        for k in range(6 + dirt * 2):
            x = dx + rnd.uniform(-9, 9)
            y = -rnd.uniform(1, 4 + dirt * 3)
            f.g.put(*P(x, y), "IZjZ"[k % 4])
    if extra: extra(f)
    return f.done()


def soldier_corpse():
    f = Fr()
    ell(f.b, -5.5, -2.8, 4.4, 2.8, "1234", bias=0.05)
    ell(f.b, -0.8, -2.0, 1.2, 1.1, "234")
    tube(f.b, [(0.4, -2.0), (3.6, -2.4)], [1.7, 1.6], "1234")
    ell(f.b, 7.2, -2.6, 3.0, 2.4, "1234", bias=0.1)
    line(f.b, 9.5, -1.0, 12.0, -0.0, "4"); f.b.put(12, 0, "9")
    for (x0, x1, y1) in ((-2, -5, -6), (1, 0, -7), (3, 5, -6)):
        polyline(f.b, [(x0, -3), (x0 + (x1 - x0) * 0.5, -5.5), (x1, y1)], "34")
    line(f.b, 4.0, -1.0, 11.0, -0.0, "3"); f.b.put(11, 0, "8")
    f.g.put(8, -3, "1"); f.g.put(-6, -4, "7")
    return f.done()


REST = dict(near=(-50, 55), farm=(-62, 50))


def build_soldier(outdir):
    S_ = soldier
    idle = [S_(**REST), S_(near=(-47, 58), farm=(-59, 53), dy=0.3, legs=0.2, jaw=0.35),
            S_(near=(-45, 61), farm=(-57, 56), dy=0.4, legs=0.3, jaw=0.45, eye="squint"),
            S_(near=(-48, 57), farm=(-60, 52), dy=0.2, legs=0.1, jaw=0.3)]
    run = [S_(legs=i * math.pi / 3, dy=-0.6 * abs(math.sin(i * math.pi / 3)), lean=3, near=(-45 + 6 * math.sin(i * math.pi / 3), 50),
              farm=(-58, 45), jaw=0.3) for i in range(6)]
    # SCYTHE: raise, slash 1 (smear), follow-through, raise again, slash 2, recover
    scy = [S_(near=(-110, -100), farm=(-95, -60), lean=-6, dx=-0.5, eye="wide", jaw=0.6),
           S_(near=(-140, -120), farm=(-80, -40), lean=-10, dx=-1.0, eye="wide", jaw=0.9),
           S_(near=(-20, 40), farm=(-110, -90), lean=8, dx=2.0, eye="wide", jaw=0.2, smear=(-120, 40)),
           S_(near=(10, 70), farm=(-120, -110), lean=10, dx=2.4, eye="squint", jaw=0.1),
           S_(near=(-30, 10), farm=(-140, -120), lean=0, dx=1.0, eye="wide", jaw=0.6),
           S_(near=(10, 70), farm=(-10, 30), lean=10, dx=2.6, eye="wide", jaw=0.2, smear=(-100, 50)),
           S_(**REST, dx=0.6)]
    # BURROW: crouch, dig in, sink, only the mound (teleport), mound rumbles, cracks glowing, ERUPT, rise, recover
    bur = [S_(near=(40, 90), farm=(30, 80), lean=14, sink=1.0, legs=1.0, dirt=1, jaw=0.4),
           S_(near=(60, 110), farm=(50, 100), lean=18, sink=6.0, legs=2.0, dirt=2, mound=0.4),
           S_(near=(60, 110), farm=(50, 100), lean=20, sink=12.0, dirt=3, mound=0.8),
           S_(hidden=True, mound=0.6),
           S_(hidden=True, mound=0.8, dirt=1),
           S_(hidden=True, mound=1.0, crack=1.0, dirt=2),
           S_(near=(-80, -95), farm=(-100, -80), lean=-12, sink=3.0, dy=-1.0, jaw=1.2, eye="wide", dirt=4, mound=0.7),
           S_(near=(-70, -50), farm=(-85, -50), lean=-6, sink=0.0, jaw=0.8, eye="wide", dirt=2, mound=0.3),
           S_(**REST)]
    death = [S_(near=(-140, -160), farm=(-120, -150), lean=-14, eye="wide", jaw=1.2, dx=-0.6),
             S_(near=(60, 120), farm=(80, 130), lean=-30, eye="dead", jaw=0.6, dy=1.5, legs=2.0),
             grounded(S_(near=(80, 160), farm=(90, 170), lean=-80, eye="dead", jaw=0.4, legs=3.0)),
             soldier_corpse()]
    knock = S_(near=(-130, -150), farm=(-110, -130), lean=-12, eye="squint", dx=-0.8, jaw=0.8)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.08] * 6),
             ("Scythe", scy, [0.14, 0.14, 0.06, 0.1, 0.12, 0.06, 0.16]),
             ("Burrow", bur, [0.12, 0.12, 0.12, 0.16, 0.18, 0.18, 0.06, 0.14, 0.16])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkSoldier", "Scythe", scy, "tip")
    sheet("ZhkSoldier", anims, outdir, scale=6, remap=LIFT)


if __name__ == "__main__" and "--t2" in sys.argv:
    o = DEFAULT_OUT; os.makedirs(o, exist_ok=True)
    build_spitter(o); build_soldier(o)


# ================================================================== BROOD MOTHER (T3, Spitter line)
# A termite-queen: a vast egg-swollen abdomen dragged along the floor behind an upright chitin torso with
# four thin arms, a long neck and a crowned head (amber resin spines). Pale, wet, regal. Nothing like the
# Colossus, which is all dark armour and horn.
def mother(dx=0.0, dy=0.0, lean=0.0, neck=0.0, wave=0.0, swell=0.0, arms=((-40, 60), (20, 80)), crown=1.0,
           jaw=0.2, throat=0.0, eye="open", legs=0.0, tail=0.0, extra=None, look=0.0):
    f = Fr()
    # --- the abdomen: a bumpy segmented sac with spaced chitin plates and eggs glowing through
    n = 7
    pts, radii = [], []
    for j in range(2 * n + 1):
        i = j / 2.0
        t = i / n
        x = dx - 23.0 + t * 22.0 + tail * (1 - t) * 1.5
        base_r = 1.8 + 4.9 * math.sin(math.pi * min(1.0, t * 0.62 + 0.12)) ** 0.8
        r = base_r * (1 + swell * 0.08 * math.sin(i * 1.7 + wave)) + 0.35 * math.sin(i * 2.1 + wave * 2)
        if j % 2 == 0 and 0 < j < 2 * n: r *= 0.8
        pts.append((x, dy - base_r - 0.4 + (0 if j > 1 else 0.6)))
        radii.append(r)

    def ash(s, ox, oy, r, l, X, Y):
        segp = (X - 0.35 * abs(oy) * (1 if oy < 0 else -1) - (dx - 23.0 + tail * 0.75)) / 4.6
        fr = segp - math.floor(segp)
        if (fr < 0.13 or fr > 0.9) and segp > 0.3:
            return "2" if oy < -0.45 * r else ("f" if oy < 0.5 * r else "1")
        if oy < -0.42 * r and 0.25 < fr < 0.78 and segp > 0.8:            # tergite plate (an island)
            if oy > -0.55 * r or fr < 0.3 or fr > 0.73: return "1"
            return "5" if l > 0.8 else ("4" if l > 0.5 else "3")
        if oy > 0.6 * r: return pick("fM", l + 0.3)
        return pick(GRUB, l - 0.05)
    tube2(f.b, pts, radii, ash)
    rnd = random.Random(5)
    for k in range(14):                                        # eggs glowing through the membrane
        i = rnd.randint(1, n - 1)
        x, y = pts[2 * i + 1]
        ex, ey = x + rnd.uniform(-1.0, 1.0), y + rnd.uniform(-0.25, 0.45) * radii[2 * i + 1]
        if f.b.px.get(P(ex, ey)) in ("C", "H", "M") and f.b.px.get(P(ex + 1, ey)) in ("C", "H", "M"):
            f.b.put(*P(ex, ey), "8"); f.b.put(*P(ex + 1, ey), "9" if (k + int(wave)) % 3 else "E")
    for i in range(1, n):                                      # acid spiracles
        x, y = pts[2 * i + 1]
        f.g.put(*P(x, y + radii[2 * i + 1] * 0.25), "Q" if swell < 0.5 else "J")
    f.pts["tail"] = (pts[0][0] - 1.0, -1.0)
    # --- legs under the torso
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx) in enumerate(((0.5, -2.0), (2.5, 3.0), (4.0, 7.5))):
            pha = legs + j * 2.1 + side * math.pi
            hp = (dx + hx - (0 if side else 0.8), dy - 8.0)
            ft = (dx + fx + 1.0 * math.sin(pha) - (0 if side else 1.0), dy - max(0.0, 1.0 * math.cos(pha)))
            leg(cv_, hp, ft, 4.0, 4.6, -1 if ft[0] < hp[0] else 1, cols=("3", "4") if side else ("1", "2"),
                knee_hi="5" if side else None)
    # --- the torso: rises from the abdomen, leaning with lean
    base = (dx + 1.0, dy - 9.0)
    piv = base
    R = lambda x, y: rot((dx + x, dy + y), piv, lean)
    th = [R(1.0, -9.0), R(2.4, -14.0), R(3.4, -19.0)]
    # v0.10 lineage (Acid Spitter, her only parent): the spitter's pale wings, grown, behind the torso
    for (ox, oy, a_, L_, W_) in ((1.0, -16.0, -150, 10.0, 3.0), (1.6, -17.0, -122, 11.4, 3.6)):
        wing(f.u, R(ox, oy), a_ + lean + 4 * math.sin(wave), L_, W_, int(wave * 2))
    # v0.9 lineage (Acid Spitter): the spitter's great acid sac bulging out of the abdomen's back
    sp = pts[7]
    acid_sac(f, sp[0] - 1.0, sp[1] - radii[7] * 0.55, 4.4, 3.6 + swell * 0.4, ang=-6, ph=int(wave * 3), glow=1.0 + swell * 0.2)
    tube(f.b, th, [4.0, 3.6, 3.0], "2345", bias=0.1)     # the spitter's chitin
    for k, p in enumerate(th[:2]):
        line(f.b, p[0] - 2.4, p[1] + 1.6, p[0] + 2.0, p[1] + 1.0, "7")                  # amber-rimmed plates
        f.b.put(*P(p[0] - 1.2, p[1] - 0.8), "5")
    # far arms (shadow)
    sh_u = R(3.0, -17.5); sh_l = R(2.4, -13.5)
    for sh, (a1, a2) in ((sh_u, arms[0]), (sh_l, arms[1])):
        el = (sh[0] - 1.2 + 4.0 * math.cos(math.radians(a1 - 10)), sh[1] + 4.0 * math.sin(math.radians(a1 - 10)))
        hd = (el[0] + 4.0 * math.cos(math.radians(a2 - 10)), el[1] + 4.0 * math.sin(math.radians(a2 - 10)))
        line(f.n, sh[0] - 1, sh[1], el[0], el[1], "1"); line(f.n, el[0], el[1], hd[0], hd[1], "2")
    # neck + head
    nk0 = R(3.8, -20.5)
    na = math.radians(-70 + neck * 25 + lean)
    hx, hy = nk0[0] + 4.2 * math.cos(na) + look, nk0[1] + 4.2 * math.sin(na)
    tube(f.b, [nk0, (hx - 0.5, hy + 1.0)], [1.6, 1.4], "2345")
    if throat > 0:
        ell(f.b, (nk0[0] + hx) / 2 + 1.2, (nk0[1] + hy) / 2 + 0.5, 1.2 + throat, 1.0 + throat * 0.8, ACID_L, bias=0.4)
    hang = math.degrees(na) + 70 - neck * 10
    # crown: a fan of amber resin spines growing from the back of the skull
    for k in range(5):
        a = math.radians(-165 + k * 24 + hang * 0.5)
        L_ = (2.4 + (1.4 if k == 2 else 0.8 if k in (1, 3) else 0.0)) * (0.8 + 0.2 * crown)
        b0 = (hx - 1.4 + 2.2 * math.cos(a), hy - 0.4 + 2.2 * math.sin(a))
        b1 = (b0[0] + L_ * math.cos(a), b0[1] + L_ * math.sin(a))
        tube(f.b, [b0, b1], [0.9, 0.35], "6778", bias=0.0)
        f.g.put(*P(*b1), "E" if crown > 1.4 else "9")
    ell(f.b, hx, hy, 3.8, 3.2, "2345", ang=hang * 0.5, bias=0.12)    # the spitter's head
    for k in range(3): f.g.put(*P(hx + 0.6 + k * 0.9, hy + 1.6), "Q")       # its acid spout pores
    f.b.put(*P(hx - 1.4, hy - 2.0), "5")
    # mandibles
    a = math.radians(hang * 0.5)
    M = lambda ox, oy: (hx + ox * math.cos(a) - oy * math.sin(a), hy + ox * math.sin(a) + oy * math.cos(a))
    up = [M(2.4, 0.2), M(4.2, -0.4 - jaw * 1.2), M(5.0, 0.8 - jaw * 0.5)]
    lo = [M(2.2, 1.4), M(3.9, 2.4 + jaw * 1.2), M(4.7, 1.5 + jaw * 0.7)]
    polyline(f.b, up, "4"); polyline(f.b, lo, "3")
    f.b.put(*P(*up[-1]), "9"); f.b.put(*P(*lo[-1]), "8")
    f.pts["mouth"] = M(4.4, 1.0)
    if eye != "dead":
        e = "L" if eye == "wide" else ("J" if eye == "open" else "D")
        f.g.put(*P(*M(1.2, -0.8)), e); f.g.put(*P(*M(2.2, -0.8)), "Q" if eye != "squint" else "D")
        f.g.put(*P(*M(1.2, -1.8)), "Q" if eye == "wide" else "D")
    else:
        f.g.put(*P(*M(1.2, -0.8)), "1")
    f.pts["crown"] = (hx - 1.5, hy - 5)
    # near arms (thin, amber-jointed, three-clawed)
    for sh, (a1, a2) in ((sh_u, arms[0]), (sh_l, arms[1])):
        el = (sh[0] + 4.2 * math.cos(math.radians(a1)), sh[1] + 4.2 * math.sin(math.radians(a1)))
        hd = (el[0] + 4.2 * math.cos(math.radians(a2)), el[1] + 4.2 * math.sin(math.radians(a2)))
        tube(f.b, [sh, el], [0.8, 0.7], "234")
        line(f.b, el[0], el[1], hd[0], hd[1], "3")
        f.b.put(*P(*el), "8")
        for da in (-35, 0, 35):
            aa = math.radians(a2 + da)
            f.b.put(*P(hd[0] + 1.2 * math.cos(aa), hd[1] + 1.2 * math.sin(aa)), "4")
    if extra: extra(f, (hx, hy), f.pts["mouth"])
    return f.done()


def mother_corpse():
    f = Fr()
    for x in range(-22, 8):
        if (x * 5) % 7: f.n.put(x, 0, "D" if x % 2 else "d")
    pts = [(-20, -2.5), (-15, -3.6), (-10, -4.2), (-5, -3.8), (-1, -3.0)]
    tube(f.b, pts, [2.0, 3.2, 3.6, 3.2, 2.4], GRUB, bias=0.1)
    for x in (-16, -11, -6):
        line(f.b, x, -6.5, x + 2, -6.8, "3")
        f.b.put(x + 1, -4, "8")
    tube(f.b, [(0, -2.5), (6, -2.4), (11, -2.0)], [2.6, 2.2, 1.8], "1234")
    ell(f.b, 13.5, -2.6, 2.8, 2.3, "1234")
    for k in range(4):
        line(f.b, 12 + k, -4.5, 10 + k * 2.2, -8 - (k % 2), "7")
        f.g.put(10 + k * 2, -8 - (k % 2), "9")
    f.g.put(14, -3, "1"); f.g.put(-9, -3, "Q"); f.g.put(-14, -2, "J")
    return f.done()


ARM_REST = ((-30, 40), (20, 85))


def build_mother(outdir):
    M_ = mother
    idle = [M_(wave=0.0, arms=ARM_REST),
            M_(wave=0.8, swell=0.4, arms=((-34, 36), (24, 88)), crown=1.1, dy=0.0, look=0.3),
            M_(wave=1.6, swell=0.7, arms=((-36, 34), (26, 90)), crown=1.2, eye="squint", jaw=0.4),
            M_(wave=2.4, swell=0.3, arms=((-32, 38), (22, 86)), crown=1.05)]
    run = [M_(wave=i * 1.05, tail=math.sin(i * math.pi / 3), legs=i * math.pi / 3, lean=4, arms=((-20, 50), (30, 95)),
              dy=-0.4 * abs(math.sin(i * math.pi / 3))) for i in range(6)]

    def spew(n, h):
        def fn(f, head, m):
            for j in range(n):
                t = j / max(1, n - 1)
                x = m[0] + 1 + t * 3 + math.sin(j * 1.3) * 0.8
                y = m[1] - 1 - t * h
                f.g.put(*P(x, y), "J" if j % 2 == 0 else "Q")
                if j % 3 == 0: f.g.put(*P(x + 1, y + 1), "L")
        return fn
    rain = [M_(lean=-4, neck=0.6, throat=0.4, arms=((-60, 10), (10, 70)), jaw=0.3, eye="wide"),
            M_(lean=-10, neck=1.2, throat=0.9, arms=((-80, -20), (-10, 60)), jaw=0.5, eye="wide", swell=0.6),
            M_(lean=-14, neck=1.6, throat=1.3, arms=((-100, -60), (-30, 40)), jaw=0.6, eye="wide", swell=0.9),
            M_(lean=-6, neck=-1.6, throat=0.2, arms=((-120, -90), (-40, 20)), jaw=1.3, eye="wide", extra=spew(10, 12)),
            M_(lean=-4, neck=-1.3, throat=0.0, arms=((-110, -80), (-30, 30)), jaw=1.1, extra=spew(6, 16)),
            M_(lean=-2, neck=-0.4, arms=((-60, 0), (0, 60)), jaw=0.5),
            M_(lean=0, neck=0.0, arms=((-40, 30), (15, 80)), jaw=0.3),
            M_(arms=ARM_REST)]

    def rings(k, egg=0):
        def fn(f, head, m):
            cx_, cy_ = f.pts["crown"]
            for j in range(k):
                r = 2.5 + j * 2.6
                for q in range(int(r * 5)):
                    a = 2 * math.pi * q / int(r * 5)
                    if math.sin(a) < 0.2:
                        f.g.put(*P(cx_ + r * math.cos(a), cy_ + r * 0.6 * math.sin(a) - j), "9" if j < 2 else "7", over=False)
            if egg:
                tx, ty = f.pts["tail"]
                for e in range(egg):
                    ell(f.b, tx - 1.5 - e * 3.2, -1.6, 1.7, 1.5, GRUB, bias=0.3)
                    f.g.put(*P(tx - 2 - e * 3.2, -2), "Q")
        return fn
    brood = [M_(arms=((-80, -40), (-20, 30)), crown=1.3, neck=0.4, eye="wide"),
             M_(arms=((-110, -80), (-60, -20)), crown=1.6, neck=0.8, eye="wide", swell=0.5, extra=rings(1)),
             M_(arms=((-120, -100), (-80, -40)), crown=1.8, neck=1.0, eye="wide", swell=0.9, jaw=0.9, extra=rings(3)),
             M_(arms=((-100, -70), (-50, 0)), crown=1.5, swell=1.4, wave=1.5, tail=1.0, extra=rings(2)),
             M_(arms=((-80, -40), (-20, 40)), crown=1.3, swell=1.0, wave=3.0, tail=-1.0, extra=rings(1, egg=1)),
             M_(arms=((-60, 0), (0, 60)), crown=1.2, swell=0.6, wave=4.5, tail=0.5, extra=rings(0, egg=2)),
             M_(arms=((-40, 30), (15, 80)), crown=1.1),
             M_(arms=ARM_REST)]
    death = [M_(lean=-16, neck=1.8, arms=((-130, -110), (-90, -60)), eye="wide", jaw=1.3, crown=1.6, swell=1.2),
             M_(lean=20, neck=-1.0, arms=((40, 90), (60, 100)), eye="dead", jaw=0.8, crown=0.9, swell=0.4, dy=1.0),
             grounded(M_(lean=55, neck=-1.6, arms=((80, 120), (90, 130)), eye="dead", jaw=0.6, crown=0.8)),
             mother_corpse()]
    knock = M_(lean=-12, neck=1.0, arms=((-110, -80), (-60, -10)), eye="squint", jaw=0.9, dx=-1)
    anims = [("Idle", idle, [0.26, 0.2, 0.26, 0.2]), ("Run", run, [0.1] * 6),
             ("Rain", rain, [0.14, 0.14, 0.16, 0.06, 0.14, 0.14, 0.12, 0.12]),
             ("Brood", brood, [0.14, 0.14, 0.16, 0.14, 0.14, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    note("ZhkMother", "Rain", rain, "mouth"); note("ZhkMother", "Brood", brood, "tail"); note("ZhkMother", "Brood", brood, "crown")
    sheet("ZhkMother", anims, outdir, scale=5)


# ================================================================== CHITIN COLOSSUS (T3, Nasute line)
def horn(c, root, ang0, curve, L, r0, n=7):
    """A tapering curved horn; returns the tip."""
    pts = [root]; rad = [r0]
    a = ang0
    x, y = root
    for i in range(n):
        x += (L / n) * math.cos(math.radians(a)); y += (L / n) * math.sin(math.radians(a))
        a += curve / n
        pts.append((x, y)); rad.append(max(0.4, r0 * (1 - (i + 1) / (n + 0.5))))
    tube(c, pts, rad, "1234", bias=0.15)
    for i in range(1, n - 1, 2):
        c.put(*P(pts[i][0] - 0.4, pts[i][1] - rad[i] * 0.6), "5")
    c.put(*P(*pts[-1]), "9"); c.put(*P(*pts[-2]), "7")
    return pts[-1]


def colossus(dx=0.0, dy=0.0, tilt=0.0, head=0.0, legs=0.0, crack=0.0, glow=1.0, eye="open", lift=0.0, crouch=0.0,
             plate=0.0, extra=None, smear=None, dust=0):
    f = Fr()
    cx, cy = dx - 4.5, dy - 12.5 - lift + crouch * 2.0
    piv = (dx + 2.0, dy - 8.0)
    R = lambda x, y: rot((x, y), piv, tilt)
    # legs: chunky, toothed tibiae
    hips = [(-7.5, 6.0), (-1.5, 7.0), (4.5, 6.0)]
    feet = [(-13.5, 0), (-4.5, 0), (8.0, 0)]
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, ((hx, hy), (fx, _)) in enumerate(zip(hips, feet)):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(cx + hx - (0 if side else 1.4), cy + hy)
            ft = (dx + fx + 1.6 * math.sin(pha) - (0 if side else 2.0), -max(0.0, 1.8 * math.cos(pha)) * (1 - crouch * 0.5))
            bend = -1 if ft[0] < hp[0] else 1
            if side:
                knee, end = ik(hp[0], hp[1], ft[0], ft[1], 5.2, 6.0, bend)
                tube(cv_, [hp, knee], [1.6, 1.3], "2345")
                tube(cv_, [knee, end], [1.3, 0.8], "1234")
                mx_, my_ = (knee[0] + end[0]) / 2, (knee[1] + end[1]) / 2
                cv_.put(*P(mx_ + 1.2 * (1 if bend > 0 else -1), my_), "4")      # tibial tooth
                cv_.put(*P(end[0] + 0.8, end[1]), "3")
            else:
                leg(cv_, hp, ft, 5.2, 6.0, bend, cols=("1", "2"), knee_hi=None)
    # elytra: the great dome. Glossy black chitin, amber resin crusted along the rim, a glowing acid seam
    ex, ey = R(cx, cy)
    def shell(nu, nv, d, l, ch, X, Y):
        if nv > 0.6: return pick("01", l)
        if 0.3 < d < 0.48 and -0.8 < nu < 0.05 and nv < -0.25: return "5"
        if 0.12 < d < 0.2 and -0.4 < nu < -0.1 and nv < -0.3: return "4"
        seam = abs(nu * 0.25 + nv * 0.95 + 0.05)
        if seam < 0.06 + 0.06 * crack and nu > -0.7: return "J" if crack > 0.5 else ("Q" if glow > 0.6 else "D")
        if d > 0.72 and nv > 0.05: return pick("6789", l + 0.4) if (X + Y) % 3 else "7"   # resin crust rim
        return pick("1123", l)
    ell(f.b, ex, ey, 11.0, 9.0, CHIT_L, ang=tilt - 6, shader=shell, vmax=0.9)
    rnd = random.Random(11)
    for k in range(5):                                       # embedded amber chunks
        a = rnd.uniform(200, 330); rr = rnd.uniform(0.45, 0.75)
        bx, by = ex + 11.0 * rr * math.cos(math.radians(a)), ey + 9.2 * rr * math.sin(math.radians(a))
        ell(f.b, bx, by, 1.3, 1.1, AMB_L, bias=0.4)
        f.g.put(*P(bx - 0.4, by - 0.4), "E" if glow > 0.8 else "9")
    if plate > 0:                                            # Harden: resin welling up over the shell
        for k in range(int(10 * plate)):
            a = math.radians(205 + k * 13)
            f.g.put(*P(ex + 11.4 * math.cos(a), ey + 9.4 * math.sin(a)), "9" if k % 2 else "E")
    # v0.10 lineage (Nasute, its only parent): the nasute's swollen amber glue sacs bulging under the shell
    bl = R(dx - 1.0, dy - 5.6 - lift + crouch * 1.6)
    ell(f.b, bl[0], bl[1], 9.0, 2.8, AMB_L, bias=0.1, vmin=-0.2,
        shader=lambda nu, nv, d, l, ch, X, Y: "6" if abs(((nu + 1) * 3.0) % 1.0) < 0.15 else ("E" if (X + Y) % 5 == 0 and abs(nv) < 0.3 else pick("789", l + 0.1)))
    # pronotum with the thoracic horn
    px_, py_ = R(dx + 6.2, dy - 13.0 - lift + crouch * 2.0)
    ell(f.b, px_, py_, 5.6, 6.0, CHIT_L, ang=tilt, bias=0.1,
        shader=lambda nu, nv, d, l, ch, X, Y: "5" if (l > 0.72 and d < 0.35) else pick("1123", l))
    horn(f.b, R(px_ + 0.5, py_ - 5.0), -70 + tilt, 60, 6.0, 1.6, n=5)
    # head + the great cephalic horn
    hx, hy = R(dx + 11.0, dy - 9.0 - lift + crouch * 2.0 + head * 1.5)
    ell(f.b, hx, hy, 3.4, 3.0, "1234", bias=0.1)
    ha = -25 + tilt - head * 40
    tip = horn(f.b, (hx + 2.0, hy - 0.8), ha, -55 + head * 20, 10.0, 2.2, n=8)
    f.pts["horn"] = tip
    # v0.9 lineage (Nasute): the horn ends in the nasute's glue nozzle, a resin bead at its mouth; short mandibles under
    # the head
    f.b.put(*P(tip[0], tip[1]), "7"); f.b.put(*P(tip[0] - 0.8, tip[1] + 0.6), "6")
    f.g.put(*P(tip[0] + 0.6, tip[1] + 1.2), "9" if glow < 1.3 else "E")
    a_ = math.radians(tilt)
    Mx = lambda ox, oy: (hx + ox * math.cos(a_) - oy * math.sin(a_), hy + ox * math.sin(a_) + oy * math.cos(a_))
    polyline(f.b, [Mx(2.4, 1.6), Mx(4.4, 2.8), Mx(5.4, 1.8)], "8"); f.b.put(*P(*Mx(5.4, 1.8)), "9")
    if eye != "dead":
        f.g.put(*P(hx + 0.6, hy - 0.6), "L" if eye == "wide" else ("J" if eye == "open" else "D"))
        f.g.put(*P(hx - 0.4, hy - 0.4), "Q" if eye != "squint" else "D")
    else:
        f.g.put(*P(hx + 0.6, hy - 0.6), "1")
    if smear:
        for k in range(16):
            t = k / 15.0
            a = math.radians(smear[0] + (smear[1] - smear[0]) * t)
            for rr, ch in ((13.0, "E"), (11.8, "9"), (10.6, "7")):
                if rr < 11 and t < 0.5: continue
                f.g.put(*P(hx + rr * math.cos(a), hy + rr * math.sin(a)), ch, over=False)
    if dust:
        for k in range(3 + dust * 2):
            f.g.put(*P(dx - 14 - k * 2.2, -1 - (k % 3)), "Z" if k % 2 else "I")
    if extra: extra(f, (hx, hy), tip)
    return f.done()


def colossus_corpse():
    f = Fr()
    # toppled on its side, legs stiff in the air, the shell split and leaking acid
    for x in range(-18, 12):
        if (x * 3) % 4: f.n.put(x, 0, "D" if x % 3 else "Q")
    ell(f.b, -4.0, -5.5, 12.0, 5.5, CHIT_L, vmax=0.95,
        shader=lambda nu, nv, d, l, ch, X, Y: ("7" if d > 0.75 and nv > 0 else ("5" if l > 0.75 and d < 0.4 else pick("1123", l))))
    line(f.g, -12, -6, 4, -8, "Q"); f.g.put(-4, -7, "J")
    ell(f.b, 9.5, -4.0, 4.4, 3.8, "1234")
    horn(f.b, (12.5, -2.5), 10, -20, 9.0, 1.8, n=6)
    for x in (-9, -3, 3):
        polyline(f.b, [(x, -10), (x - 1.5, -13), (x + 1, -15)], "34")
    f.g.put(11, -5, "1")
    return f.done()


def build_colossus(outdir):
    C_ = colossus
    idle = [C_(), C_(dy=0.3, legs=0.2, glow=1.2), C_(dy=0.5, legs=0.3, glow=1.3, eye="squint", head=0.1), C_(dy=0.2, legs=0.1, glow=1.1)]
    run = [C_(legs=i * math.pi / 3, dy=-0.8 * abs(math.sin(i * math.pi / 3)), tilt=1.5 * math.sin(i * math.pi / 3), head=0.2, dust=i % 2)
           for i in range(6)]
    gore = [C_(head=0.6, crouch=0.3, tilt=3, eye="wide"),
            C_(head=1.2, crouch=0.7, tilt=6, dx=-1.0, eye="wide", dust=1),
            C_(head=1.4, crouch=0.9, tilt=7, dx=-1.5, eye="wide", legs=0.5),
            C_(head=-0.4, crouch=0.0, tilt=-6, dx=2.0, eye="wide", lift=1.0, smear=(40, -60)),
            C_(head=-1.0, crouch=0.0, tilt=-10, dx=2.6, eye="squint", lift=1.5, smear=(-20, -80)),
            C_(head=-0.6, tilt=-6, dx=2.0, lift=0.8),
            C_(head=0.0, tilt=-2, dx=1.0),
            C_()]
    charge = [C_(crack=0.6, plate=0.4, crouch=0.3, eye="wide", glow=1.4),
              C_(crack=1.0, plate=1.0, crouch=0.6, eye="wide", glow=1.6, legs=1.5, dust=1),
              C_(head=1.0, crouch=0.8, tilt=5, eye="wide", plate=0.8, dust=1),
              C_(head=1.0, tilt=6, legs=0.0, dy=-0.6, dust=2, plate=0.6),
              C_(head=1.0, tilt=6, legs=math.pi / 2, dy=-1.2, dust=3, plate=0.6),
              C_(head=1.0, tilt=6, legs=math.pi, dy=-0.6, dust=3, plate=0.6),
              C_(head=1.0, tilt=6, legs=3 * math.pi / 2, dy=-1.2, dust=3, plate=0.6),
              C_(head=0.4, tilt=-6, crouch=0.5, legs=0.3, dust=2, eye="squint"),
              C_()]
    death = [C_(head=-1.0, tilt=-10, lift=1.5, eye="wide", crack=1.0),
             C_(head=0.6, tilt=14, crouch=1.0, eye="dead", crack=0.6, glow=0.4, dy=1.0),
             grounded(C_(head=1.2, tilt=24, crouch=1.4, eye="dead", glow=0.2)),
             colossus_corpse()]
    knock = C_(head=-0.8, tilt=-8, lift=1.0, eye="squint", dx=-1.0)
    anims = [("Idle", idle, [0.28, 0.22, 0.28, 0.22]), ("Run", run, [0.1] * 6),
             ("Gore", gore, [0.16, 0.16, 0.12, 0.06, 0.1, 0.14, 0.14, 0.14]),
             ("Charge", charge, [0.14, 0.18, 0.12, 0.08, 0.08, 0.08, 0.08, 0.16, 0.16])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.4], knock)
    note("ZhkColossus", "Gore", gore, "horn"); note("ZhkColossus", "Charge", charge, "horn")
    sheet("ZhkColossus", anims, outdir, scale=5, remap=LIFT)


if __name__ == "__main__" and "--t3" in sys.argv:
    o = DEFAULT_OUT; os.makedirs(o, exist_ok=True)
    build_mother(o); build_colossus(o)


# ================================================================== HIVE HORNET (T2, Drone line; flier)
# v0.8 redraw (it read as a bigger Drone): an upright hunting hornet. Oxblood-and-rust chitin instead of the Drone's
# amber, a heavy black abdomen that HANGS straight down under the body with acid-green bands and an amber pheromone
# gland at the tip, four raised smoky-amber wings, a big horned head with hooked mandibles, long legs trailing.
# The Drone is a horizontal amber-striped dart; the Hornet is a tall dark-red "T" with a green-banded hook below.
def hornet(dx=0.0, dy=0.0, tilt=0.0, wph=0, curl=0.0, legs=0.0, eye="open", gland=0.0, jaw=0.2, extra=None, streak=0):
    f = Fr()
    cx, cy = dx, dy - 14.0
    piv = (cx, cy)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    RED, RED_L = "!@#$", "@#$"
    # long legs: front pairs reaching forward under the head, the hind pair trailing far down and back
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, kx, ky, ex, ey) in enumerate(((2.0, 4.0, 2.6, 5.6, 5.4), (0.6, 1.2, 3.8, 2.6, 7.0), (-0.8, -3.4, 4.0, -4.6, 10.0))):
            sw = math.sin(legs + j * 1.7 + side) * 0.8
            h = R(hx - (0 if side else 0.6), 1.6)
            k = R(kx + sw * 0.5 - (0 if side else 0.6), ky)
            e = R(ex + sw - (0 if side else 0.8), ey + (0.6 if side else 0))
            line(cv_, h[0], h[1], k[0], k[1], "@" if side else "1")
            line(cv_, k[0], k[1], e[0], e[1], "#" if side else "!")
            if side: cv_.put(*P(*k), "$"); cv_.put(*P(*e), "2")
    # petiole and the hanging abdomen: points straight down (aa ~ 100), curl swings the sting forward
    w0 = R(-1.6, 1.4)
    aa = 104 - 62 * curl + tilt
    ar = math.radians(aa)
    w1 = (w0[0] + 1.2 * math.cos(ar), w0[1] + 1.2 * math.sin(ar))
    line(f.b, w0[0], w0[1], w1[0], w1[1], "@")
    ac = (w1[0] + 3.9 * math.cos(ar), w1[1] + 3.9 * math.sin(ar))
    def band(nu, nv, d, l, ch, X, Y):
        b = int((nu + 1.0) * 3.0)
        if b % 2 == 0: return pick("1223", l)
        return pick("dDQ", l + 0.05)
    ell(f.b, ac[0], ac[1], 4.3, 2.8, "0123", ang=aa + 180, bias=0.1, shader=band)
    st0 = (w1[0] + 7.8 * math.cos(ar), w1[1] + 7.8 * math.sin(ar))
    st1 = (w1[0] + 9.4 * math.cos(ar), w1[1] + 9.4 * math.sin(ar))
    line(f.b, st0[0], st0[1], st1[0], st1[1], "5")
    f.g.put(*P(*st1), "J")
    # pheromone gland at the tip: always a dot of amber, swelling when it marks
    gp = (st0[0] - 0.6 * math.cos(ar), st0[1] - 0.6 * math.sin(ar))
    if gland > 0:
        ell(f.g, gp[0], gp[1], 0.9 + gland, 0.9 + gland * 0.8, "89E", bias=0.4)
    else:
        f.g.put(*P(*gp), "8")
    f.pts["sting"] = st1
    # thorax: rust-red, a bright collar and a pale scutellum dot
    ell(f.b, *R(0.4, -0.2), 3.0, 2.5, RED, ang=tilt, bias=0.15)
    tp = R(0.2, -1.8)
    line(f.b, tp[0] - 1.4, tp[1] + 0.4, tp[0] + 1.2, tp[1] - 0.2, "$")
    f.b.put(*P(*R(-1.4, 0.2)), "E")
    # head: big, rust with a black face plate, a forward-swept horn crest and hooked amber mandibles
    hx, hy = R(4.6, -1.2)
    ell(f.b, hx, hy, 2.6, 2.4, RED, bias=0.15)
    ell(f.b, hx + 1.2, hy + 0.6, 1.4, 1.5, "0112", bias=0.0)
    polyline(f.b, [(hx - 1.2, hy - 1.8), (hx - 0.6, hy - 3.6), (hx + 1.4, hy - 4.8)], "#"); f.b.put(*P(hx + 1.8, hy - 5.0), "$")
    a = math.radians(tilt)
    M = lambda ox, oy: (hx + ox * math.cos(a) - oy * math.sin(a), hy + ox * math.sin(a) + oy * math.cos(a))
    polyline(f.b, [M(2.0, 1.0), M(3.4, 0.6 - jaw), M(4.2, 1.6 - jaw * 0.4)], "9")
    polyline(f.b, [M(1.8, 1.8), M(3.2, 2.8 + jaw), M(3.8, 2.0 + jaw * 0.5)], "8")
    f.b.put(*P(*M(4.2, 1.6 - jaw * 0.4)), "E")
    f.pts["mouth"] = M(3.4, 1.4)
    # antennae: sweeping forward and up
    polyline(f.b, [M(0.8, -1.8), M(2.2, -3.6), M(4.8, -4.4)], "2")
    if eye != "dead":
        e = "L" if eye == "wide" else ("J" if eye == "open" else "D")
        for (ox, oy, ch) in ((0.2, -0.8, e), (1.0, -0.6, "Q"), (0.2, 0.2, "D"), (-0.6, -0.6, "D")):
            f.g.put(*P(*M(ox, oy)), ch)
    else:
        f.g.put(*P(*M(0.2, -0.8)), "1")
    # wings: two raised smoky-amber pairs (the Drone's are pale grey and swept back)
    root = R(-0.4, -2.2)
    angs = [-98, -122, -146, -118][wph % 4]
    wc = ("%", "^", "&")
    wing(f.g, (root[0] - 0.8, root[1] + 0.2), angs - 22 + tilt * 0.3, 6.8, 2.0, wph + 1, cols=wc)
    wing(f.g, root, angs + tilt * 0.3, 8.4, 2.8, wph, cols=wc)
    for s_ in range(streak):
        y = cy - 1 + s_ * 2
        line(f.g, cx - 8 - s_ * 2, y - 2 + s_, cx - 12 - s_ * 2, y - 4 + s_, "^" if s_ % 2 else "%", over=False)
    if extra: extra(f, (hx, hy), st1)
    return f.done()


def hornet_corpse():
    f = Fr()
    ell(f.b, -4.0, -2.0, 4.6, 2.2, "0123",
        shader=lambda nu, nv, d, l, ch, X, Y: pick("0112", l) if int((nu + 1) * 3) % 2 == 0 else pick("dDQ", l))
    line(f.b, 0.6, -2, 1.6, -2, "@")
    ell(f.b, 3.6, -2.0, 2.5, 2.0, "!@#$")
    ell(f.b, 7.4, -2.0, 2.0, 1.8, "!@#$")
    for x in (2.0, 3.4, 4.8):
        polyline(f.b, [(x, -3.5), (x - 0.5, -6), (x + 1, -7.5)], "@#")
    wing(f.g, (2.6, -3.6), -165, 8.0, 1.8, cols=("%", "^", "&"))
    f.g.put(-9, -1, "8"); f.g.put(7, -2, "1")
    return f.done()


def build_hornet(outdir):
    H_ = hornet
    idle = [H_(wph=i, dy=[0, -0.8, -1.2, -0.5][i], legs=i * 0.7, curl=0.08 * (i % 2)) for i in range(4)]
    run = [H_(wph=i % 4, dy=-0.5 * math.sin(i * math.pi / 3), tilt=10, legs=i, curl=0.1) for i in range(6)]

    def darts(n):
        def fn(f, head, st):
            for j in range(n):
                for k in (-1, 0, 1):
                    f.g.put(*P(st[0] + 2 + j, st[1] + k * (1 + j * 0.6)), "J" if j == 0 else "Q")
        return fn
    # VOLLEY: curl the abdomen forward under the body and fire a fan of three stingers
    vol = [H_(wph=0, curl=0.4, tilt=-4, dy=-0.6, eye="wide"),
           H_(wph=1, curl=0.85, tilt=-12, dx=-1.0, dy=-2.0, eye="wide"),
           H_(wph=2, curl=1.1, tilt=-8, dx=-1.2, dy=-2.4, eye="wide"),
           H_(wph=3, curl=1.15, tilt=2, dx=0.6, dy=-2.4, eye="squint", extra=darts(2)),
           H_(wph=0, curl=0.7, dx=0.4, dy=-1.4),
           H_(wph=1, curl=0.2, dy=-0.4)]
    # MARK: the pheromone gland swells, it hovers back, then flicks a glowing amber dart
    def glow_fx(n):
        def fn(f, head, st):
            for j in range(n):
                a = j * 2.1
                f.g.put(*P(st[0] + math.cos(a) * 3, st[1] - 1 + math.sin(a) * 2), "9" if j % 2 else "E", over=False)
        return fn
    mark = [H_(wph=0, curl=0.3, gland=0.3, eye="squint"),
            H_(wph=1, curl=0.6, gland=0.7, dx=-0.8, dy=-1.0, tilt=-6, extra=glow_fx(3)),
            H_(wph=2, curl=0.9, gland=1.1, dx=-1.4, dy=-1.6, tilt=-10, eye="wide", extra=glow_fx(5)),
            H_(wph=3, curl=1.15, gland=1.3, dx=-1.6, dy=-2.0, tilt=-10, eye="wide", extra=glow_fx(6)),
            H_(wph=0, curl=1.2, gland=0.0, dx=0.8, dy=-2.0, tilt=4, eye="wide", streak=1),
            H_(wph=1, curl=0.7, dx=0.4, dy=-1.0),
            H_(wph=2, curl=0.2)]
    death = [H_(wph=1, tilt=-30, curl=0.6, eye="wide", dy=-1),
             H_(wph=3, tilt=-70, curl=0.2, eye="dead", dy=3.0),
             grounded(H_(wph=2, tilt=-150, curl=0.0, eye="dead")),
             hornet_corpse()]
    knock = H_(wph=2, tilt=-22, curl=0.5, dx=-1, eye="squint")
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6),
             ("Volley", vol, [0.12, 0.14, 0.12, 0.06, 0.12, 0.12]),
             ("Mark", mark, [0.12, 0.14, 0.14, 0.14, 0.06, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkHornet", "Volley", vol, "sting"); note("ZhkHornet", "Mark", mark, "sting")
    sheet("ZhkHornet", anims, outdir, scale=6, remap=HORNET_LIFT)


# ================================================================== NASUTE (T2, Resin Beetle line)
# A termite soldier: pale soft body, and a huge dark chitin head drawn out into a nozzle that squirts glue.
def nasute(dx=0.0, dy=0.0, tilt=0.0, nose=-12.0, legs=0.0, eye="open", rear=0.0, glow=0.0, swell=0.0, extra=None, crouch=0.0):
    f = Fr()
    cx, cy = dx, dy - 8.0 + crouch * 1.4
    piv = (cx + 2, cy + 2)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # six short legs from the thorax
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx) in enumerate(((-0.8, -6.0), (1.0, 0.5), (2.8, 6.0))):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(hx - (0 if side else 0.8), 2.0)
            ft = (dx + fx + 1.0 * math.sin(pha) - (0 if side else 1.0), -max(0.0, 1.0 * math.cos(pha)))
            leg(cv_, hp, ft, 3.6, 4.4, -1 if ft[0] < hp[0] else 1, cols=("3", "4") if side else ("1", "2"), knee_hi="5" if side else None)
    # soft pale abdomen behind, segmented, amber gut glowing through
    # v0.10: the abdomen is a cluster of swollen amber glue sacs (its own read next to the Hive Soldier's pale gaster)
    pts = [R(-8.6, 0.2 - rear), R(-6.4, -0.8 - rear * 0.6), R(-3.8, -0.6), R(-1.4, 0.0)]
    rad = [2.6 + swell * 0.4, 4.0 + swell * 0.8, 4.0 + swell * 0.6, 2.6]
    def gsh(s, ox, oy, r, l, X, Y):
        fr = (X - pts[0][0] - 0.4 * oy) / 2.6
        if (fr - math.floor(fr)) < 0.17 and 0.4 < s < 2.8: return "6"
        if l > 0.75 and abs(oy) < 0.5 * r: return "E"
        if oy > 0.55 * r: return pick("67", l + 0.3)
        return pick("789", l + 0.1 + 0.15 * glow)
    tube2(f.b, pts, rad, gsh)
    # thorax: v0.9 lineage (Resin Beetle): the beetle's resin-beaded elytra dome, carried over the thorax
    resin_shell(f.b, f.g, *R(0.0, -0.6), 3.4, 2.6, ang=tilt, beads=2)
    # the head: a big dark bulb drawn out into the nozzle (rostrum)
    hx, hy = R(5.6, -3.6)
    stamp_c = Canvas()
    ell(stamp_c, hx, hy, 5.6, 5.2, "1234", ang=tilt, bias=0.3,
        shader=lambda nu, nv, d, l, ch, X, Y: "5" if (l > 0.7 and d < 0.35) else pick("23345", l))   # v0.10: big dark bulb
    for k_, v_ in outl(Spr(stamp_c.px), "0").px.items(): f.b.put(k_[0], k_[1], v_)          # its own dark rim
    na = math.radians(nose + tilt)
    n0 = (hx + 3.8 * math.cos(na), hy + 3.8 * math.sin(na))
    n1 = (n0[0] + 4.0 * math.cos(na), n0[1] + 4.0 * math.sin(na))
    tube(f.b, [n0, n1], [2.1, 0.9], "1234", bias=0.1)
    for k in (0.3, 0.65):
        q = (n0[0] + (n1[0] - n0[0]) * k, n0[1] + (n1[1] - n0[1]) * k)
        f.b.put(*P(q[0] - math.sin(na) * 1.0, q[1] + math.cos(na) * 1.0 - 0.0), "6")
    f.b.put(*P(n1[0] - 0.3 * math.cos(na), n1[1] - 0.3 * math.sin(na)), "7")
    f.g.put(*P(n1[0] + 0.6 * math.cos(na), n1[1] + 0.6 * math.sin(na)), "9" if glow < 0.5 else "E")
    f.pts["mouth"] = (n1[0] + 1.2 * math.cos(na), n1[1] + 1.2 * math.sin(na))
    if glow < 0.5:   # a resin bead hanging off the nozzle
        f.g.put(*P(n1[0], n1[1] + 1.2), "8")
    # tiny vestigial eyes (termite soldiers are near blind): one acid pore each side of the bulb
    if eye != "dead":
        f.g.put(*P(hx + 0.6, hy - 2.0), "Q" if eye != "wide" else "J")
        f.g.put(*P(hx - 2.0, hy - 0.6), "D" if eye == "squint" else "Q")
        # amber-rimmed suture over the bulb
        polyline(f.b, [(hx - 3.2, hy - 1.6), (hx - 1.0, hy - 3.6), (hx + 1.8, hy - 3.2)], "6")
    if extra: extra(f, (hx, hy), f.pts["mouth"], na)
    return f.done()


def nasute_corpse():
    f = Fr()
    tube(f.b, [(-11, -1.6), (-8, -2.2), (-4.6, -2.2), (-1.6, -1.8)], [1.4, 2.2, 2.3, 1.6], GRUB, bias=0.1)
    ell(f.b, 1.2, -1.8, 2.0, 1.6, "2345")
    ell(f.b, 5.6, -2.8, 3.6, 2.8, "1234", bias=0.1)
    tube(f.b, [(8.6, -1.6), (12.4, -0.4)], [1.3, 0.6], "2345")
    for x in (-1.0, 1.0, 3.0):
        polyline(f.b, [(x, -3.5), (x - 0.5, -6), (x + 1, -7)], "34")
    ell(f.n, 13.6, -0.6, 2.4, 0.9, AMB_L, bias=0.3)
    f.g.put(13, -1, "E"); f.g.put(6, -4, "1")
    return f.done()


def build_nasute(outdir):
    N_ = nasute
    idle = [N_(nose=-12), N_(nose=-10, dy=0.3, legs=0.2, swell=0.2), N_(nose=-8, dy=0.4, legs=0.3, swell=0.35, eye="squint"),
            N_(nose=-11, dy=0.2, legs=0.1, swell=0.15)]
    run = [N_(legs=i * math.pi / 3, dy=-0.5 * abs(math.sin(i * math.pi / 3)), tilt=-1.5 * math.sin(i * math.pi / 3), nose=-6) for i in range(6)]

    def jet(n, reach):
        def fn(f, head, m, na):
            for j in range(n):
                t = j / max(1, n - 1)
                x = m[0] + 1 + t * reach * math.cos(na)
                y = m[1] + t * reach * math.sin(na) + t * t * 2.5
                f.g.put(*P(x, y), "E" if j % 3 == 0 else "9")
                f.g.put(*P(x, y + 1), "7", over=False)
        return fn
    sq = [N_(nose=-20, tilt=-4, swell=0.5, glow=0.3, crouch=0.4),
          N_(nose=-28, tilt=-8, swell=1.0, glow=0.7, crouch=0.8, eye="wide"),
          N_(nose=-6, tilt=2, swell=0.2, glow=1.0, dx=0.8, eye="wide", extra=jet(9, 14)),
          N_(nose=-4, tilt=3, swell=0.0, glow=1.0, dx=1.0, extra=jet(10, 18)),
          N_(nose=-8, tilt=1, glow=0.4, dx=0.6, extra=jet(4, 20)),
          N_(nose=-12)]

    def rain(n, h):
        def fn(f, head, m, na):
            for j in range(n):
                a = -math.pi + (j + 0.5) * math.pi / n
                x = head[0] - 3 + math.cos(a) * (6 + h * 0.6)
                y = m[1] - 2 - math.sin(-a) * h * 0.5 + (h - 6) * 0.3
                f.g.put(*P(x, y), "E" if j % 2 else "9")
                f.g.put(*P(x, y + 1), "8", over=False)
        return fn
    seal = [N_(nose=-30, tilt=-6, swell=0.4, crouch=0.5),
            N_(nose=-55, tilt=-14, swell=0.9, glow=0.6, rear=0.6, eye="squint"),
            N_(nose=-80, tilt=-20, swell=1.2, glow=1.0, rear=1.0, eye="squint", extra=rain(5, 8)),
            N_(nose=-88, tilt=-22, swell=0.8, glow=1.0, rear=1.0, extra=rain(7, 10)),
            N_(nose=-70, tilt=-16, swell=0.4, glow=0.8, rear=0.8, extra=rain(9, 6)),
            N_(nose=-40, tilt=-8, glow=0.4, rear=0.4, extra=rain(9, 2)),
            N_(nose=-20, tilt=-2),
            N_(nose=-12)]
    death = [N_(nose=-60, tilt=-14, eye="wide", swell=1.0, glow=1.0),
             N_(nose=20, tilt=10, eye="dead", crouch=1.6, dy=0.5),
             grounded(N_(nose=30, tilt=14, eye="dead", crouch=2.4, legs=2.0)),
             nasute_corpse()]
    knock = N_(nose=-40, tilt=-12, eye="squint", dx=-0.8, swell=0.6)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.075] * 6),
             ("Squirt", sq, [0.14, 0.16, 0.06, 0.1, 0.12, 0.14]),
             ("Seal", seal, [0.12, 0.14, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkNasute", "Squirt", sq, "mouth"); note("ZhkNasute", "Seal", seal, "mouth")
    sheet("ZhkNasute", anims, outdir, scale=6)


# ================================================================== AMBER HIVE (T3, Hive Hornet line)
# A living hive: a great mound of amber honeycomb carried on six chitin legs, an armoured wasp-queen head
# under its front edge, hornets crawling over the comb. Gold and bright where the Colossus is black.
def comb_shader(cx, cy, ph, pulse=0.0, open_=0.0):
    """Honeycomb: offset rows of hex-ish cells (4 px wide, 3 tall) with resin walls, lit from the top-left."""
    def sh(nu, nv, d, l, ch, X, Y):
        if nv > 0.6: return pick("0112", l)                        # dark chitin skirt underneath
        row = (Y + 40) // 3
        xx = X + (2 if row % 2 else 0) + 40
        ly, lx = (Y + 40) % 3, xx % 4
        if d > 0.88: return pick("1267", l + 0.1)                  # the rim, in shadow
        if ly == 0 or lx == 0: return pick("1167", l)               # cell walls
        cell = ((xx // 4) * 5 + row * 7) % 11
        if cell == 0: return "M" if l < 0.3 else "C"                # a larva asleep in its cell
        if cell in (3, 8) and pulse > 0: return "J" if (row + ph) % 2 else "Q"
        if cell in (5, 9): return "0" if open_ > 0.5 else pick("12", l)   # empty cell
        if lx == 1 and ly == 1 and l > 0.35: return "E"                # wet glint on full cells
        return pick("6789", l + 0.1 + 0.2 * pulse)
    return sh


def tiny_wasp(c, x, y, ph):
    """v0.9: the Hive Hornet's brood: rust-red bodies, a green-banded tail, smoky wings."""
    x, y = P(x, y)
    c.put(x, y, "#"); c.put(x - 1, y, "D"); c.put(x + 1, y, "$")
    c.put(x - (ph % 2), y - 1, "^")


def hive(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, crouch=0.0, ph=0, pulse=0.0, jaw=0.2, eye="open", head=0.0, wasps=3,
         ooze=0.0, extra=None, open_=0.0):
    f = Fr()
    cx, cy = dx - 2.0, dy - 19.0 + crouch * 3.0
    piv = (dx, dy - 8)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # thick legs
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx) in enumerate(((-8.0, -14.0), (-1.0, -3.5), (6.0, 9.0))):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(hx - (0 if side else 1.4), 10.0)
            ft = (dx + fx + 1.4 * math.sin(pha) - (0 if side else 1.6), -max(0.0, 1.6 * math.cos(pha)) * (1 - crouch * 0.6))
            bend = -1 if ft[0] < hp[0] else 1
            if side:
                knee, end = ik(hp[0], hp[1], ft[0], ft[1], 5.0, 5.4 - crouch * 0.6, bend)
                tube(cv_, [hp, knee], [1.5, 1.2], "2345")
                tube(cv_, [knee, end], [1.2, 0.7], "1234")
                cv_.put(*P(end[0] + 0.6, end[1]), "3")
            else:
                leg(cv_, hp, ft, 5.0, 5.4 - crouch * 0.6, bend, cols=("1", "2"), knee_hi=None)
    # the comb mound
    hx0, hy0 = R(0, 0)
    shd = comb_shader(hx0, hy0, ph, pulse, open_)
    for (ox, oy_, rx, ry) in ((0, 0, 14.0, 11.5), (-6.5, -3.5, 8.0, 8.5), (4.5, -5.0, 8.5, 8.0)):
        q = R(ox, oy_)
        ell(f.b, q[0], q[1], rx, ry - crouch * 0.6, AMB_L, ang=tilt, shader=shd, vmax=0.9 if oy_ == 0 else 0.6, over=(oy_ == 0))
    # resin drips hanging off the rim
    for k, x in enumerate((-11, -6, 1, 7)):
        n = 1 + ((k + ph) % 3) + int(ooze * 3)
        bx, by = R(x, 9.6 - abs(x) * 0.12)
        for j in range(n):
            f.b.put(*P(bx, by + j), "8" if j < n - 1 else "9")
    # queen head under the front edge
    qx, qy = R(13.5, 4.5 + head)
    ell(f.b, qx, qy, 4.6, 4.0, "1234", bias=0.12,
        shader=lambda nu, nv, d, l, ch, X, Y: "5" if (l > 0.72 and d < 0.3) else pick("1234", l))
    a = math.radians(tilt)
    M = lambda ox, oy: (qx + ox * math.cos(a) - oy * math.sin(a), qy + ox * math.sin(a) + oy * math.cos(a))
    polyline(f.b, [M(3.0, 0.8), M(5.0, 0.0 - jaw * 1.2), M(5.8, 1.6 - jaw * 0.5)], "8")
    polyline(f.b, [M(2.8, 2.2), M(4.6, 3.2 + jaw * 1.2), M(5.4, 2.4 + jaw * 0.6)], "7")
    f.b.put(*P(*M(5.8, 1.6 - jaw * 0.5)), "9")
    polyline(f.b, [M(0.0, -3.2), M(2.4, -6.0), M(5.0, -6.6)], "2")
    # v0.10 lineage (Hive Hornet, its only parent): the hornet's horn crest on the queen's brow, its smoky-amber
    # wings fanning from under the comb rim, and the hornet brood circling it
    polyline(f.b, [M(0.6, -3.0), M(2.4, -5.4), M(5.0, -6.2)], "#"); f.b.put(*P(*M(5.4, -6.4)), "$")
    f.pts["mouth"] = M(5.0, 1.4)
    if eye != "dead":
        e = "L" if eye == "wide" else ("J" if eye == "open" else "D")
        for (ox, oy, ch) in ((1.2, -1.0, e), (2.2, -0.8, "Q"), (1.2, 0.0, "D")):
            f.g.put(*P(*M(ox, oy)), ch)
    else:
        f.g.put(*P(*M(1.2, -1.0)), "1")
    f.pts["comb"] = R(4.0, -9.0)
    for (ox, oy, a_, L_) in ((-8.0, -10.0, -150, 8.0), (-5.0, -12.0, -124, 9.0)):
        wing(f.n, R(ox, oy), a_ + tilt + (ph % 2) * 8, L_, 2.8, ph, cols=("%", "^", "&"))
    # hornets crawling / circling the comb
    for k in range(wasps):
        a2 = 2 * math.pi * (k / max(1, wasps) + ph / 8.0)
        tiny_wasp(f.g, hx0 + 13.0 * math.cos(a2) * 0.9, hy0 - 4 + 9.0 * math.sin(a2) * 0.7 - 3, ph + k)
    if extra: extra(f, (hx0, hy0), f.pts["comb"])
    return f.done()


def hive_corpse():
    f = Fr()
    for x in range(-18, 14):
        if (x * 5) % 3: f.n.put(x, 0, "7" if x % 2 else "8")
    ell(f.b, -2.0, -6.0, 15.0, 6.5, AMB_L, shader=comb_shader(0, -6, 0, 0.0, 1.0), vmax=0.95)
    for (x0, y0) in ((-9, -10), (-2, -12), (5, -10)):
        polyline(f.b, [(x0, y0), (x0 - 1.5, y0 - 3), (x0 + 1, y0 - 5)], "34")
    ell(f.b, 13.0, -2.6, 3.4, 2.6, "1234")
    f.g.put(14, -3, "1"); f.g.put(-6, -8, "9"); f.g.put(2, -9, "E")
    return f.done()


def build_hive(outdir):
    H_ = hive
    idle = [H_(ph=0), H_(ph=1, dy=0.3, legs=0.2, crouch=0.15), H_(ph=2, dy=0.4, legs=0.3, crouch=0.25, eye="squint", jaw=0.4),
            H_(ph=3, dy=0.2, legs=0.1, crouch=0.1)]
    # v0.8: half-step gait offset + a forward lean, so no Run frame repeats an Idle pose
    run = [H_(legs=i * math.pi / 3 + math.pi / 6, dy=-0.7 * abs(math.sin(i * math.pi / 3 + math.pi / 6)),
              tilt=1.0 + 1.5 * math.sin(i * math.pi / 3 + math.pi / 6), head=0.15, ph=i) for i in range(6)]

    def burst(n, r):
        def fn(f, c, comb):
            for k in range(n):
                a = -math.pi * 0.85 + k * math.pi * 0.7 / max(1, n - 1)
                tiny_wasp(f.g, comb[0] + 4 + r * math.cos(a) * 1.2, comb[1] + r * math.sin(a), k)
        return fn
    swarm = [H_(ph=0, pulse=0.4, crouch=0.2, tilt=-2, eye="wide", wasps=3),
             H_(ph=1, pulse=0.8, crouch=0.4, tilt=-4, eye="wide", wasps=2, jaw=0.6),
             H_(ph=2, pulse=1.0, crouch=0.5, tilt=-5, eye="wide", wasps=1, jaw=0.9),
             H_(ph=3, pulse=0.6, crouch=0.0, tilt=3, eye="wide", wasps=0, jaw=1.2, extra=burst(6, 4)),
             H_(ph=4, pulse=0.3, tilt=2, wasps=0, jaw=0.8, extra=burst(6, 8)),
             H_(ph=5, pulse=0.1, tilt=0, wasps=1, extra=burst(4, 12)),
             H_(ph=6, wasps=2)]
    def drip_ring(stage):
        def fn(f, c, comb):
            for k in range(7):
                x = c[0] - 15 + k * 5
                if stage >= 1: f.g.put(*P(x, -1), "8"); f.g.put(*P(x + 1, -1), "7")
                if stage >= 2: f.g.put(*P(x - 1, 0), "7"); f.g.put(*P(x + 2, 0), "8")
        return fn
    rebuild = [H_(ph=0, crouch=0.4, ooze=0.3, eye="squint"),
               H_(ph=1, crouch=0.9, ooze=0.7, eye="squint", pulse=0.3, open_=1.0),
               H_(ph=2, crouch=1.2, ooze=1.0, eye="squint", pulse=0.5, open_=1.0, extra=drip_ring(1)),
               H_(ph=3, crouch=1.3, ooze=1.0, eye="squint", pulse=0.7, open_=1.0, extra=drip_ring(2)),
               H_(ph=4, crouch=1.2, ooze=0.6, pulse=0.9, extra=drip_ring(2)),
               H_(ph=5, crouch=0.8, ooze=0.3, pulse=0.6, eye="wide"),
               H_(ph=6, crouch=0.3, pulse=0.2),
               H_(ph=7)]
    death = [H_(ph=1, tilt=-6, eye="wide", jaw=1.2, pulse=1.0, wasps=0),
             H_(ph=2, crouch=1.4, tilt=6, eye="dead", wasps=0, open_=1.0, dy=0.5),
             grounded(H_(ph=3, crouch=2.2, tilt=10, eye="dead", wasps=0, open_=1.0)),
             hive_corpse()]
    knock = H_(ph=2, tilt=-8, eye="squint", dx=-1, jaw=0.8)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.1] * 6),
             ("Swarm", swarm, [0.14, 0.14, 0.16, 0.06, 0.12, 0.12, 0.14]),
             ("Rebuild", rebuild, [0.12, 0.14, 0.16, 0.2, 0.16, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.4], knock)
    note("ZhkHive", "Swarm", swarm, "comb"); note("ZhkHive", "Swarm", swarm, "mouth")
    sheet("ZhkHive", anims, outdir, scale=5)


# ================================================================== ACID MANTIS (T3, Hive Soldier line)
# Tall, upright, thin: a mantis on four stilt legs, long prothorax, triangular head with great acid eyes,
# and two raptorial arms whose blades are coated in glowing acid. Vertical where the Mother and Colossus sprawl.
def mantis_arm(c, g, sh, a1, a2, far=False, drip=True):
    """Raptorial foreleg: femur (spined, acid edge) then the folding tibia hook. Returns the hook tip."""
    el = (sh[0] + 6.6 * math.cos(math.radians(a1)), sh[1] + 6.6 * math.sin(math.radians(a1)))
    tip = (el[0] + 7.2 * math.cos(math.radians(a2)), el[1] + 7.2 * math.sin(math.radians(a2)))
    if far:
        line(c, sh[0], sh[1], el[0], el[1], "1"); line(c, el[0], el[1], tip[0], tip[1], "d")
        return tip
    tube(c, [sh, el], [1.3, 1.0], "2345")
    a = math.radians(a1); nx, ny = -math.sin(a), math.cos(a)
    for t in (0.35, 0.6, 0.85):                                   # femur spines
        q = (sh[0] + (el[0] - sh[0]) * t + nx * 1.4, sh[1] + (el[1] - sh[1]) * t + ny * 1.4)
        c.put(*P(*q), "4")
    a = math.radians(a2); nx, ny = -math.sin(a), math.cos(a)
    poly(c, [el, (el[0] + nx * 1.8 + (tip[0] - el[0]) * 0.4, el[1] + ny * 1.8 + (tip[1] - el[1]) * 0.4), tip,
             (el[0] - nx * 0.6, el[1] - ny * 0.6)], "D",
         shade=lambda x, y: "Q" if ((x - el[0]) * nx + (y - el[1]) * ny) > 0.5 else "D")
    line(c, el[0], el[1], tip[0], tip[1], "2")
    c.put(*P(*el), "5")
    g.put(*P(*tip), "J")
    if drip:
        g.put(*P(tip[0], tip[1] + 1.5), "Q"); g.put(*P(tip[0], tip[1] + 2.5), "D")
    return tip


def mantis(dx=0.0, dy=0.0, lean=0.0, crouch=0.0, near=(-80, 100), farm=(-90, 95), legs=0.0, eye="open", head=0.0,
           abd=0.0, wings=0.0, extra=None, smear=None, air=0.0, jaw=0.0):
    f = Fr()
    oy = dy - air
    hip = (dx - 1.0, oy - 13.0 + crouch * 4.0)
    piv = hip
    R = lambda x, y: rot((hip[0] + x, hip[1] + y), piv, lean)
    # four stilt legs (two pairs), folded under when airborne
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx) in enumerate(((-1.5, -9.0), (1.5, 6.5))):
            pha = legs + j * 2.6 + side * math.pi
            hp = R(hx - (0 if side else 1.0), 0.8)
            if air > 0.5:
                ft = (hp[0] + (-4 if j == 0 else 3), hp[1] + 6)
            else:
                ft = (dx + fx * (1 - crouch * 0.2) + 1.4 * math.sin(pha) - (0 if side else 1.4), oy - max(0.0, 1.4 * math.cos(pha)))
            bend = -1 if ft[0] < hp[0] else 1
            leg(cv_, hp, ft, 7.0 - crouch, 7.6 - crouch, bend if j else -bend, cols=("3", "4") if side else ("1", "2"),
                knee_hi="5" if side else None)
    # abdomen: long, angled back and up, tip curling
    ab = [R(-1.0, 0.0), R(-5.0, -1.0 - abd), R(-9.0, -3.0 - abd * 2), R(-11.4, -5.5 - abd * 3)]
    def ash(s, ox, oy_, r, l, X, Y):
        if int(s * 2.0) % 2 == 1 and oy_ < 0: return pick("012", l)
        if oy_ > 0.5 * r: return pick("12", l)
        return pick("1234", l)
    tube2(f.b, ab, [1.8, 2.7, 2.2, 1.0], ash)
    # v0.10 lineage (Hive Soldier, its only parent): the soldier's ringed gaster on the abdomen, its scythe arms below
    def gsh(nu, nv, d, l, ch, X, Y):
        b = (nu + 1.0) * 2.4 + 0.5
        if (b - math.floor(b)) < 0.18 and d < 0.9: return "f"
        if nv > 0.55: return pick("fM", l + 0.3)
        return pick(GRUB, l + 0.1)
    gx_, gy_ = ab[1][0] - 0.6, ab[1][1] - 2.2                       # v0.10: the soldier's pale ringed gaster
    ell(f.b, gx_, gy_, 3.6, 2.8, GRUB, ang=-20 + lean, bias=0.05, shader=gsh)
    for k in range(2): f.g.put(*P(gx_ - 1.2 + k * 2.0, gy_ + 0.6), "Q" if eye != "dead" else "d")
    # folded wings along the abdomen (leathery, amber-veined) - spread with wings
    wa = 200 + lean - 40 * wings
    wing(f.n, R(-0.5, -1.8), wa, 10.0 + 2 * wings, 1.6 + 2.0 * wings)
    # long prothorax (neck), rising forward
    top = R(3.4 - head * 0.4, -12.0 + head)
    tube(f.b, [R(0.2, -0.6), R(1.8, -6.0), top], [2.4, 1.8, 1.6], "1234", bias=0.15)
    f.b.put(*P(*R(1.0, -4.0)), "6"); f.b.put(*P(*R(1.6, -6.8)), "6")
    # far raptorial arm
    sh_far = R(2.2, -9.2)
    mantis_arm(f.n, f.n, sh_far, farm[0], farm[1], far=True)
    # head: a triangle, two great eyes at the corners, mandibles at the point
    hx, hy = top[0] + 1.6, top[1] - 1.6
    a = math.radians(lean * 0.5 + head * 8)
    T = lambda ox, oy_: (hx + ox * math.cos(a) - oy_ * math.sin(a), hy + ox * math.sin(a) + oy_ * math.cos(a))
    poly(f.b, [T(-3.8, -2.0), T(4.0, -2.0), T(1.4, 3.6), T(0.0, 3.8)], "3",
         shade=lambda x, y: "5" if (y < hy - 1.0 and x < hx) else ("4" if y < hy - 0.5 else "2"))
    for sd, ex in ((-1, -3.0), (1, 3.2)):
        ell(f.b, *T(ex * 1.08, -2.0), 1.8, 1.7, "dDQJ", bias=0.4)
    f.b.put(*P(*T(0.4, -2.8)), "5")
    polyline(f.b, [T(-0.6, -2.6), T(-2.6, -6.0), T(-1.0, -9.0)], "2")
    polyline(f.b, [T(0.8, -2.6), T(2.8, -6.2), T(5.2, -8.4)], "2")
    polyline(f.b, [T(0.0, 3.4), T(1.0 + jaw, 4.4)], "8"); f.b.put(*P(*T(1.2 + jaw, 4.6)), "9")
    if eye != "dead":
        f.g.put(*P(*T(3.0, -2.0)), "L" if eye == "wide" else "J")
        f.g.put(*P(*T(-3.2, -2.0)), "J" if eye != "squint" else "Q")
    else:
        f.g.put(*P(*T(3.0, -2.0)), "d"); f.g.put(*P(*T(-3.2, -2.0)), "d")
    # near raptorial arm over everything
    sh_near = R(3.2, -8.0)
    tip = mantis_arm(f.b, f.g, sh_near, near[0], near[1])
    f.pts["tip"] = tip
    if smear:
        el = (sh_near[0] + 6.6 * math.cos(math.radians(near[0])), sh_near[1] + 6.6 * math.sin(math.radians(near[0])))
        for k in range(16):
            t = k / 15.0
            ang = math.radians(smear[0] + (smear[1] - smear[0]) * t)
            for rr, ch in ((8.0, "L"), (6.8, "J"), (5.6, "Q")):
                if rr < 5 and t < 0.45: continue
                f.g.put(*P(el[0] + rr * math.cos(ang), el[1] + rr * math.sin(ang)), ch, over=False)
    if extra: extra(f, (hx, hy), tip)
    return f.done(clip=air <= 0)


def mantis_corpse():
    f = Fr()
    tube(f.b, [(-12, -2), (-6, -2.6), (-1, -2.4)], [1.4, 2.6, 2.0], "2345")
    tube(f.b, [(0, -2.2), (7, -2.0)], [1.6, 1.2], "2345")
    poly(f.b, [(8, -5), (13, -4), (10, -0), (9, 0)], "3")
    ell(f.b, 12, -4, 1.4, 1.3, "dDQ")
    for (x0, x1) in ((-4, -8), (0, 3), (4, 9)):
        polyline(f.b, [(x0, -3), (x0 + (x1 - x0) * 0.5, -8), (x1, -10)], "34")
    line(f.b, 5, -1, 13, 0, "D"); f.g.put(13, 0, "J")
    f.g.put(12, -4, "d")
    return f.done()


M_REST = dict(near=(-18, 108), farm=(-10, 112))


def build_mantis(outdir):
    M_ = mantis
    idle = [M_(**M_REST), M_(near=(-20, 105), farm=(-12, 109), dy=0.3, head=0.2, abd=0.2, legs=0.2),
            M_(near=(-22, 102), farm=(-14, 106), dy=0.5, head=0.4, abd=0.4, legs=0.3, eye="squint"),
            M_(near=(-19, 107), farm=(-11, 111), dy=0.2, head=0.2, abd=0.2, legs=0.1)]
    run = [M_(legs=i * math.pi / 3, dy=-0.6 * abs(math.sin(i * math.pi / 3)), lean=6, near=(-10 + 6 * math.sin(i), 115), farm=(-4, 118),
              abd=0.3 * math.sin(i)) for i in range(6)]
    # REAP: arms up, slash down (smear), cross back, second slash, recover
    reap = [M_(near=(-120, -60), farm=(-110, -70), lean=-6, eye="wide", head=-0.4, jaw=0.6),
            M_(near=(-150, -100), farm=(-130, -90), lean=-10, dx=-1.0, eye="wide", head=-0.6, jaw=1.0),
            M_(near=(-10, 50), farm=(-120, -80), lean=8, dx=2.0, eye="wide", smear=(-140, 30)),
            M_(near=(30, 90), farm=(-140, -110), lean=10, dx=2.4, eye="squint"),
            M_(near=(-60, -10), farm=(-30, 30), lean=2, dx=1.0, eye="wide"),
            M_(near=(20, 80), farm=(10, 70), lean=12, dx=2.8, eye="wide", smear=(-90, 40)),
            M_(**M_REST, dx=0.6)]
    # POUNCE: crouch deep, spring (airborne, wings flared), fall, LAND (acid splash), rise
    def land_fx(n):
        def fn(f, head, tip):
            for k in range(n):
                a = -math.pi + k * math.pi / max(1, n - 1)
                x, y = dx0 + 9 + 8 * math.cos(a), -1 + 3 * math.sin(a)
                f.g.put(*P(x, y), "J" if k % 2 else "Q")
        dx0 = 0
        return fn
    pounce = [M_(near=(-100, -40), farm=(-110, -60), crouch=0.6, lean=10, eye="wide"),
              M_(near=(-120, -70), farm=(-130, -80), crouch=1.2, lean=16, eye="wide", abd=-0.4),
              M_(near=(-30, 20), farm=(-40, 10), air=8.0, lean=18, wings=1.0, eye="wide"),
              M_(near=(-10, 40), farm=(-20, 30), air=9.0, lean=22, wings=1.0, eye="wide"),
              M_(near=(30, 80), farm=(20, 70), air=3.0, lean=26, wings=0.6, eye="wide"),
              M_(near=(40, 95), farm=(30, 90), crouch=1.4, lean=20, eye="squint", extra=land_fx(9)),
              M_(near=(-20, 60), farm=(-30, 55), crouch=0.7, lean=8, extra=land_fx(5)),
              M_(**M_REST)]
    death = [M_(near=(-150, -170), farm=(-130, -150), lean=-14, eye="wide", jaw=1.0, head=-1.0),
             M_(near=(60, 120), farm=(80, 130), lean=-40, eye="dead", crouch=1.2, dy=0.5),
             grounded(M_(near=(80, 160), farm=(90, 170), lean=-80, eye="dead", crouch=2.0)),
             mantis_corpse()]
    knock = M_(near=(-130, -150), farm=(-110, -130), lean=-12, eye="squint", dx=-0.8, head=-0.6)
    # airborne frames must stay above the floor and inside the cell
    pounce = [Spr({k: v for k, v in fr.px.items() if k[1] <= 0}) for fr in pounce]
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.08] * 6),
             ("Reap", reap, [0.14, 0.14, 0.06, 0.1, 0.12, 0.06, 0.16]),
             ("Pounce", pounce, [0.14, 0.14, 0.08, 0.08, 0.06, 0.12, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkMantis", "Reap", reap, "tip")
    sheet("ZhkMantis", anims, outdir, scale=5, remap=LIFT_OLIVE)


# ================================================================== FX
def cv():
    return Canvas()


def blob(c, cx, cy, rx, ry, ramp, wob=0.0, ph=0, bias=0.25):
    """A wobbling liquid blob (a little squash per frame)."""
    ell(c, cx, cy, rx * (1 + wob * math.sin(ph)), ry * (1 - wob * math.sin(ph)), ramp, bias=bias)


def fx_acid_spit():
    """FxZhkAcidSpit: a small acid glob, bright core, spattered trail (faces right)."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(5):
            x = -3 - k * 1.5 - (i % 2) * 0.7
            y = -3 + math.sin(k * 1.4 + i) * 1.2
            c.put(*P(x, y), "Q" if k < 2 else "D" if k < 4 else "d")
        blob(c, 0, -3, 2.6, 2.2, "dDQJ", wob=0.12, ph=i * 1.6)
        c.put(-1, -4, "L"); c.put(0, -4 if i % 2 else -5, "J")
        c.put(*P(2.5, -3 + (i % 3) - 1), "J")
        out.append(outl(Spr(c.px), "d"))
    return out


def fx_stinger():
    """FxZhkStinger: an amber barbed stinger dart with a dripping acid tip (faces right)."""
    out = []
    for i in range(4):
        c = cv()
        for x in range(-4, 4):
            c.put(x, -2, "8" if x > -2 else "7")
            if x < 1: c.put(x, -1, "6")
        c.put(4, -2, "Q"); c.put(5, -2, "J"); c.put(4, -1, "D")
        c.put(-1, -3, "9"); c.put(1, -1, "6")                         # barbs
        for k in range(3):                                            # blur trail
            c.put(-6 - k * 2 - (i % 2), -2 + ((k + i) % 2) - (1 if k == 2 else 0), "~" if k == 0 else "l" if k == 1 else "z")
        c.put(*P(3 - i, -1), "E")                                     # travelling glint
        out.append(outl(Spr(c.px), "0"))
    return out


def fx_resin_glob():
    """FxZhkResinGlob: a lobbed glob of amber resin with sticky strands."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(4):
            c.put(*P(-3.5 - k * 1.3, -3.5 + math.sin(k + i) * 0.8), "7" if k < 2 else "6")
        blob(c, 0, -3.5, 2.8, 2.5, "6789", wob=0.15, ph=i * 1.6, bias=0.3)
        c.put(-1, -5, "E"); c.put(0, -5, "9")
        c.put(*P(1, -2 + (i % 2)), "6")
        out.append(outl(Spr(c.px), "0"))
    return out


def fx_acid_glob():
    """FxZhkAcidGlob: the Spitter's big lobbed acid glob: a membrane bag, bubbles inside, drips."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(6):
            x = -4.5 - k * 1.4 - (i % 2)
            c.put(*P(x, -4 + math.sin(k * 1.3 + i) * 1.6), "Q" if k < 2 else "D" if k < 4 else "d")
        blob(c, 0, -4.5, 3.8, 3.3, "dDQJ", wob=0.1, ph=i * 1.6, bias=0.15)
        c.put(-1, -6, "L"); c.put(-2, -5, "J")
        c.put(*P(1, -3 - (i % 3)), "L"); c.put(*P(-1, -2 - ((i + 1) % 3)), "J")
        c.put(*P(0.5, -1), "D")
        out.append(outl(Spr(c.px), "d"))
    return out


def puddle(ramp_edge, ramp_in, spread=1.0, phase=0, fade=0.0, seed=0, bub="J", glint="L", w=11.0, strands=False):
    """A low, lumpy floor puddle of overlapping flat lobes (resin or acid)."""
    c = cv()
    lobes = [(0, 0, w, 2.8), (-w * 0.55, 0.3, w * 0.5, 2.2), (w * 0.5, -0.2, w * 0.55, 2.4), (-1.5, -0.6, w * 0.62, 3.0)]
    inside = {}
    for (lx, ly, rx, ry) in lobes:
        rx, ry = rx * spread, max(1.0, ry * (0.5 + 0.5 * spread))
        for y in range(int(-ry) - 1, int(ry) + 2):
            for x in range(int(lx * spread - rx) - 1, int(lx * spread + rx) + 2):
                d = ((x - lx * spread) / rx) ** 2 + ((y - ly) / ry) ** 2
                if d <= 1.0:
                    inside[(x, y)] = min(inside.get((x, y), 9), d)
    for (x, y), d in inside.items():
        if fade and d > 1.0 - fade * 0.75: continue          # v0.10: fades by shrinking (no stipple noise)
        edge = any((x + a, y + b) not in inside for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            ch = ramp_edge[2] if (y < 0 and x < 3) else ramp_edge[1] if y <= 0 else ramp_edge[0]
        else:
            ch = ramp_in[0]
            if ((x + 2 * y + phase) % 6) == 0 and d > 0.2: ch = ramp_in[1]
        c.put(x, y - 3, ch)
    if fade < 0.7:
        rnd = random.Random(seed * 5 + 1)
        for k in range(3):
            bx, by = rnd.uniform(-w * 0.7, w * 0.7) * spread, rnd.uniform(-1.5, 1.0)
            if (phase + k) % 3 != 2 and (int(bx), int(by)) in inside:
                c.put(*P(bx, by - 3), bub)
                if (phase + k) % 3 == 1: c.put(*P(bx, by - 4), glint)
        if strands:
            for k in range(3):
                x0 = (-w * 0.5 + k * w * 0.5) * spread
                h = 1 + (phase + k) % 3
                for j in range(h):
                    c.put(*P(x0, -4 - j), "7" if j < h - 1 else "9")
    return c.spr()


def fx_resin():
    E, I = "679", "78"
    sp = [puddle(E, I, 0.35, 0, w=10, bub="9", glint="E"), puddle(E, I, 0.65, 1, w=10, bub="9", glint="E"),
          puddle(E, I, 0.92, 2, w=10, bub="9", glint="E", strands=True)]
    idle = [puddle(E, I, 1.0, 0, seed=1, w=10, bub="9", glint="E", strands=True), puddle(E, I, 1.0, 1, seed=2, w=10, bub="9", glint="E")]
    fd = [puddle(E, I, 0.95, 0, 0.35, w=10, bub="9", glint="E"), puddle(E, I, 0.85, 1, 0.6, w=10, bub="9", glint="E"),
          puddle(E, I, 0.7, 0, 0.85, w=10, bub="9", glint="E")]
    return sp, idle, fd


def fx_acid_pool():
    E, I = "dDQ", "DQ"
    sp = [puddle(E, I, 0.35, 0, w=10), puddle(E, I, 0.7, 1, w=10), puddle(E, I, 0.95, 2, w=10)]
    idle = [puddle(E, I, 1.0, k, seed=k + 1, w=10) for k in range(4)]
    fd = [puddle(E, I, 0.95, 0, 0.35, w=10), puddle(E, I, 0.85, 1, 0.6, w=10), puddle(E, I, 0.7, 2, 0.85, w=10)]
    return sp, idle, fd


def fx_splash():
    """FxZhkSplash: an acid splash crown + droplets, ends in a hiss of vapour."""
    out = []
    for i in range(5):
        c = cv()
        h = [3, 7, 9, 6, 2][i]
        w = [3, 5, 7, 8, 9][i]
        if i < 4:
            for sd in (-1, 1):
                for k in range(3):
                    x0 = sd * (1.5 + k * 1.4) * (w / 7.0)
                    hh = h * (1 - 0.25 * k)
                    lean = sd * (1.5 + i * 1.3 + k * 0.7)
                    line(c, x0, 0, x0 + lean, -hh, "DQ" if k else "QJ")
                    c.put(*P(x0 + lean, -hh - 1), "J" if i < 2 else "Q")
        rnd = random.Random(7)
        for k in range(8):
            a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
            t = (i + 0.5) / 4.0
            x = math.cos(a) * w * 1.1 * (0.4 + t)
            y = min(0, math.sin(a) * 11 * t * (1.4 - t) + t * t * 3)
            if i >= 1: c.put(*P(x, y), "L" if k % 3 == 0 else "Q")
        for x in range(-w, w + 1):
            if i >= 1 and (x + i) % 2 == 0: c.put(x, 0, "D")
        if i >= 3:
            for k in range(3):
                c.put(*P(-3 + k * 3, -3 - i - k % 2), "l" if k % 2 else "~")            # vapour
        out.append(c.spr())
    return out


def egg(c, cx, crack=0, wob=0.0, open_=0.0, glow=1):
    """A pale leathery egg on the floor (6x7), crack lines glowing acid; open_ splits it apart."""
    if open_ <= 0:
        ell(c, cx + wob, -3.6, 2.6, 3.4, GRUB, ang=wob * 8, bias=0.25)
        c.put(*P(cx - 1 + wob, -5.5), "H")
        if crack >= 1:
            polyline(c, [(cx - 1 + wob, -6), (cx + wob, -4.5), (cx - 0.5 + wob, -3), (cx + 1 + wob, -2)], "Q" if glow else "D")
        if crack >= 2:
            polyline(c, [(cx + 1.5 + wob, -5.5), (cx + 0.5 + wob, -4.5)], "J")
            c.put(*P(cx + wob, -4.5), "L")
    else:
        o = open_
        ell(c, cx - 1.6 - o, -2.2, 1.8, 2.2, GRUB, vmin=-0.2, bias=0.15)
        ell(c, cx + 1.6 + o, -2.2, 1.8, 2.2, GRUB, vmin=-0.2, bias=0.15)
        for x in range(int(cx - 3 - o), int(cx + 4 + o)):
            if x % 2: c.put(x, 0, "D")
        c.put(*P(cx, -1), "Q"); c.put(*P(cx - 1, -3 - o), "J"); c.put(*P(cx + 1, -4 - o), "Q")


def fx_egg():
    """FxZhkEgg. Hatch: crack, split, burst (the death perk, ~0.5 s). Life: lands, wobbles twice, then hatches (~1.2 s)."""
    def fr(**k):
        c = cv(); egg(c, 0, **k); return outl(Spr(c.px), "0")
    hatch = [fr(crack=0, wob=0), fr(crack=1, wob=-0.5), fr(crack=2, wob=0.5), fr(open_=0.6), fr(open_=1.4), fr(open_=1.8, glow=0)]
    life = [fr(crack=0), fr(crack=0, wob=-0.6), fr(crack=0, wob=0.6), fr(crack=0), fr(crack=1, wob=-0.6), fr(crack=1, wob=0.6)] + hatch[1:]
    return hatch, life


def fx_acid_rain():
    """FxZhkAcidRain: a target ring blooms on the floor while a drop of acid falls; it splats on frame 4."""
    out = []
    for i in range(7):
        c = cv()
        # target ring (telegraph): grows over frames 0-3, then the splat
        rr = [3, 5, 7, 8, 8, 9, 9][i]
        ry = rr * 0.38
        for k in range(int(rr * 5)):
            a = 2 * math.pi * k / int(rr * 5)
            if i < 4 and (k + i) % 3 == 0: continue
            if i >= 5 and k % 2: continue
            c.put(*P(rr * math.cos(a), ry * math.sin(a) - 1), "D" if i < 3 else "Q")
        if i < 4:
            dy = [-32, -24, -15, -6][i]
            for k in range(4):
                c.put(0, dy - 3 - k * 2, "D" if k > 1 else "Q")            # falling streak
            ell(c, 0, dy, 1.4, 2.2, "DQJ", bias=0.3)
            c.put(0, dy - 1, "L")
        elif i == 4:
            ell(c, 0, -2.0, 6.0, 2.6, "dDQJ", bias=0.3)
            for sd in (-1, 1):
                for k in range(3):
                    line(c, sd * (1 + k * 1.6), -2, sd * (2.5 + k * 2.6), -6 - (2 - k) * 1.5, "QJ")
            c.put(0, -3, "L")
        else:
            for x in range(-7, 8):
                if (x + i) % 2: c.put(x, -1, "D")
            for k in range(5):
                c.put(*P(-6 + k * 3, -3 - (i - 4) * 2 - (k % 2)), "Q" if i == 5 else "D")
        out.append(c.spr())
    return out


def fx_pheromone():
    """FxZhkPheromone: amber rings rippling out across the floor, scent motes rising (Brood Mother)."""
    out = []
    for i in range(6):
        c = cv()
        for j in range(2):
            r = 6 + (i - j * 2.5) * 6
            if r < 3 or r > 36: continue
            ry = r * 0.32
            fade = r / 36.0
            n = int(r * 5)
            for k in range(n):
                if fade > 0.6 and k % 3 == 0: continue
                a = 2 * math.pi * k / n
                c.put(*P(r * math.cos(a), ry * math.sin(a) - 2), "9" if fade < 0.35 else "8" if fade < 0.7 else "7", over=False)
        rnd = random.Random(i)
        for k in range(7):
            x = rnd.uniform(-20, 20); y = -3 - ((i * 4 + k * 5) % 18)
            c.put(*P(x, y), "E" if k % 3 == 0 else "9")
        out.append(c.spr())
    return out


def fx_swarm():
    """FxZhkSwarm: amber motes circling above a monster while the swarm buff is on (loop)."""
    out = []
    for i in range(6):
        c = cv()
        for k in range(4):
            a = 2 * math.pi * (k / 4.0 + i / 6.0)
            x, y = 6.5 * math.cos(a), -3 + 2.0 * math.sin(a)
            c.put(*P(x, y), "9" if math.sin(a) > 0 else "8")
            if k % 2 == 0: c.put(*P(x - math.sin(a), y + 0.5), "7")
        out.append(c.spr())
    return out


def fx_plate():
    """FxZhkPlate: two amber-resin chitin plates orbiting (Colossus Harden), loop."""
    out = []
    for i in range(6):
        c = cv()
        for k in range(2):
            a = 2 * math.pi * (k / 2.0 + i / 6.0)
            x, y = 9 * math.cos(a), -4 + 3 * math.sin(a)
            front = math.sin(a) > 0
            ell(c, x, y, 1.8 if front else 1.3, 2.4 if front else 1.8, "6789" if front else "4567", bias=0.3)
            c.put(*P(x - 0.5, y - 1), "E" if front else "8")
        out.append(outl(Spr(c.px), "0"))
    return out


def fx_resin_burst():
    """FxZhkResinBurst: a ring of resin splashes out of the hero (Hive Amber)."""
    out = []
    for i in range(5):
        c = cv()
        r = [4, 8, 12, 14, 15][i]
        ry = r * 0.4
        n = 14
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = r * math.cos(a), ry * math.sin(a) - 2
            if i < 4:
                ell(c, x, y, 1.4 - i * 0.2, 1.1, "6789", bias=0.3)
                if k % 2 and i < 3: line(c, x * 0.6, y * 0.6 - 1, x, y, "7")
            elif k % 2:
                c.put(*P(x, y), "7")
        if i < 2:
            ell(c, 0, -3, 3 - i, 2.2 - i * 0.5, "789E", bias=0.4)
        out.append(c.spr())
    return out


def fx_dirt():
    """FxZhkDirt: earth and chitin chips thrown up as the Soldier erupts."""
    out = []
    rnd = random.Random(4)
    parts = [(rnd.uniform(-1, 1), rnd.uniform(0.6, 1.0), rnd.choice("jIZ3")) for _ in range(16)]
    for i in range(5):
        c = cv()
        t = (i + 0.6) / 4.2
        for (vx, vy, ch) in parts:
            x = vx * 14 * t
            y = min(0, -vy * 22 * t + 18 * t * t)
            c.put(*P(x, y), ch)
            if i < 2: c.put(*P(x, y + 1), "j", over=False)
        if i < 3:
            ell(c, 0, 0, 7 - i, 2.5 - i * 0.6, "jIZ", vmax=0.0)
        out.append(c.spr())
    return out


def fx_sheet_fixed(name, anims, outdir, cell, origin, scale=8):
    cw, ch = cell
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
        for f in fr:
            for (x, y) in f.px:
                assert -origin[0] <= x < cw - origin[0] and -origin[1] <= y < ch - origin[1], (name, x, y)
    img, man = pack(name, anims, cw, ch, origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man}
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def build_fx(outdir):
    fx_sheet("FxZhkAcidSpit", [("Fly", fx_acid_spit(), [0.07] * 4)], outdir)
    fx_sheet("FxZhkStinger", [("Fly", fx_stinger(), [0.05] * 4)], outdir)
    fx_sheet("FxZhkResinGlob", [("Fly", fx_resin_glob(), [0.08] * 4)], outdir)
    fx_sheet("FxZhkAcidGlob", [("Fly", fx_acid_glob(), [0.08] * 4)], outdir)
    sp, idl, fd = fx_resin()
    life = sp + idl * 8 + fd
    fx_sheet("FxZhkResin", [("Life", life, [0.1] * 3 + [0.22] * 16 + [0.15] * 3),
                            ("Spread", sp, [0.1] * 3), ("Idle", idl, [0.22, 0.22]), ("Fade", fd, [0.15] * 3)], outdir)
    sp, idl, fd = fx_acid_pool()
    life = sp + idl * 3 + fd
    fx_sheet("FxZhkAcidPool", [("Life", life, [0.1] * 3 + [0.2] * 12 + [0.13] * 3),
                               ("Spread", sp, [0.1] * 3), ("Idle", idl, [0.2] * 4), ("Fade", fd, [0.13] * 3)], outdir)
    fx_sheet("FxZhkSplash", [("Play", fx_splash(), [0.05, 0.06, 0.07, 0.09, 0.12])], outdir)
    hatch, life = fx_egg()
    fx_sheet("FxZhkEgg", [("Hatch", hatch, [0.1, 0.1, 0.1, 0.08, 0.08, 0.1]),
                          ("Life", life, [0.12, 0.14, 0.14, 0.12, 0.14, 0.14, 0.1, 0.1, 0.08, 0.08, 0.1])], outdir)
    fx_sheet("FxZhkAcidRain", [("Play", fx_acid_rain(), [0.12, 0.12, 0.12, 0.1, 0.06, 0.1, 0.12])], outdir, scale=6)
    fx_sheet("FxZhkPheromone", [("Play", fx_pheromone(), [0.09] * 6)], outdir, scale=4)
    fx_sheet("FxZhkSwarm", [("Loop", fx_swarm(), [0.08] * 6)], outdir)
    fx_sheet("FxZhkPlate", [("Play", fx_plate(), [0.08] * 6)], outdir)
    fx_sheet("FxZhkResinBurst", [("Play", fx_resin_burst(), [0.05, 0.06, 0.07, 0.09, 0.12])], outdir, scale=5)
    fx_sheet("FxZhkDirt", [("Play", fx_dirt(), [0.06, 0.07, 0.08, 0.09, 0.1])], outdir)


# ================================================================== FX for the v0.7.2 evolutions
def fx_glue_jet():
    """FxZhkGlueJet: a short stream of amber glue specks (Nasute Squirt), faces right."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(7):
            x = 3 - k * 1.6 - (i % 2) * 0.8
            y = -2 + math.sin(k * 1.1 + i * 1.3) * 0.9
            c.put(*P(x, y), "E" if k == 0 else "9" if k < 3 else "8" if k < 5 else "7")
            if k < 3: c.put(*P(x, y + 1), "7", over=False)
        ell(c, 3.5, -2, 1.6, 1.2, "789E", bias=0.4)
        out.append(outl(Spr(c.px), "6"))
    return out


def fx_swarm_cloud():
    """FxZhkSwarmCloud: a buzzing knot of tiny hornets (Amber Hive Swarm), loop."""
    out = []
    rnd = random.Random(9)
    bugs = [(rnd.uniform(0, 6.28), rnd.uniform(2.0, 6.5), rnd.uniform(0.7, 1.3), rnd.choice((1, -1))) for _ in range(9)]
    for i in range(6):
        c = cv()
        for (a0, r, sp, sd) in bugs:
            a = a0 + sd * i * sp * 1.05
            x, y = r * math.cos(a), -7 + r * 0.7 * math.sin(a)
            tiny_wasp(c, x, y, i)
            c.put(*P(x - 2 * sd * math.sin(a), y + 0.0), "z", over=False)
        out.append(c.spr())
    return out


def fx_mark_dart():
    """FxZhkMarkDart: a glowing amber pheromone dart with a scent trail (Hornet Mark), faces right."""
    out = []
    for i in range(4):
        c = cv()
        for x in range(-3, 3):
            c.put(x, -2, "8" if x < 1 else "9")
        c.put(3, -2, "E"); c.put(4, -2, "E")
        c.put(0, -3, "7"); c.put(0, -1, "7")
        for k in range(5):
            c.put(*P(-5 - k * 1.7, -2 + math.sin(k + i * 1.6) * 1.4), "9" if k < 2 else "8" if k < 4 else "7")
        out.append(outl(Spr(c.px), "6"))
    return out


def fx_mark():
    """FxZhkMark: the pheromone mark hovering over a marked hero: an amber chevron + scent motes (loop)."""
    out = []
    for i in range(6):
        c = cv()
        bob = [0, -1, -1, 0, 1, 1][i]
        for k in range(4):
            c.put(-3 + k, -6 + k + bob, "9" if k < 3 else "E")
            c.put(3 - k, -6 + k + bob, "8" if k < 3 else "E")
        c.put(0, -2 + bob, "E")
        for k in range(3):
            a = (i / 6.0 + k / 3.0) * 2 * math.pi
            c.put(*P(5 * math.cos(a), -4 + 2 * math.sin(a) + bob), "9" if math.sin(a) > 0 else "7")
        out.append(outl(Spr(c.px), "6"))
    return out


def fx_seal():
    """FxZhkSeal: a dome of resin flowing over an ally (Nasute Seal), plays once then the plate orbits."""
    out = []
    for i in range(5):
        c = cv()
        h = [3, 8, 12, 13, 13][i]
        w = [5, 7, 8, 8, 8][i]
        for k in range(15):
            a = math.pi + k * math.pi / 14
            x, y = w * math.cos(a), -1 + h * math.sin(a) * 0.95
            c.put(*P(x, y), "E" if (k + i) % 4 == 0 else "9" if k % 2 else "8")
            if i >= 2 and k % 3 == 0: c.put(*P(x, y + 1), "7")
        if i >= 3:
            for k in range(3): c.put(*P(-6 + k * 6, -1 - (i - 3)), "8")
        out.append(c.spr())
    return out


def build_fx2(outdir):
    fx_sheet("FxZhkGlueJet", [("Fly", fx_glue_jet(), [0.05] * 4)], outdir)
    fx_sheet("FxZhkSwarmCloud", [("Loop", fx_swarm_cloud(), [0.07] * 6)], outdir)
    fx_sheet("FxZhkMarkDart", [("Fly", fx_mark_dart(), [0.06] * 4)], outdir)
    fx_sheet("FxZhkMark", [("Loop", fx_mark(), [0.1] * 6)], outdir)
    fx_sheet("FxZhkSeal", [("Play", fx_seal(), [0.06, 0.07, 0.08, 0.1, 0.12])], outdir)


# ================================================================== v0.8 art pass: own sheets for things that borrowed art
def fx_hornet_stinger():
    """FxZhkHornetStinger: the Hive Hornet's needle (faces right). Not the Drone's amber dart: a thin oxblood-and-rust
    shaft with a black hooked barb, a bead of acid at the tip and a smoky-amber wing-beat smear behind it."""
    out = []
    for i in range(4):
        c = cv()
        for x in range(-4, 5):
            c.put(x, -2, "E" if x == 3 else "$" if x > -2 else "#")
        c.put(-4, -1, "!"); c.put(-3, -1, "@")                          # fletch of rust chitin
        c.put(5, -2, "0"); c.put(6, -2, "J"); c.put(5, -1, "D")         # black barb point + acid bead
        c.put(1, -3, "0"); c.put(2, -3, "@")                            # hooked barb on the back
        for k in range(3):                                              # smoky wing-beat smear
            c.put(-6 - k * 2 - (i % 2), -2 + ((k + i) % 2) * (1 if k else 0), "^" if k == 0 else "%")
        if i % 2 == 0: c.put(-7 - (i // 2), -3, "%")
        c.put(*P(3 - i * 1.5, -2), "E")                                 # travelling glint
        out.append(outl(Spr(c.px), "0"))
    return out


def fx_acid_mark():
    """FxZhkAcidMark: Corroded (acid, +20% damage taken), hovering over the victim's head: an acid droplet with a
    corroded hole eaten through it, a bubble lifting off and a drip falling off its tip. Loop 4. Origin = bottom centre.
    Redrawn at head-overlay size (8 x 11 max, was 9 x 15: it stood as tall as the hero over him), in line with the
    other head overlays (Marked 11 x 7, Implant 8 x 8, Rime pips 13 x 6)."""
    out = []
    for i in range(4):
        c = cv()
        bob = [0, -1, -1, 0][i]
        # droplet: round body tapering to a point on top (6 rows)
        for y in range(-7, -1):
            t = (y + 7) / 5.0
            w = 0.5 + 2.1 * math.sin(min(1.0, t * 1.2) * math.pi * 0.6)
            for x in range(-3, 4):
                if abs(x) <= w:
                    l = 0.55 - (x + 0.3) * 0.2 - (y + 4) * 0.09
                    c.put(x, y + bob, pick("dDQJ", l))
        # the corroded hole: a dark pit with a bright rim
        for (x, y) in ((0, -4), (1, -4), (0, -3)):
            c.put(x, y + bob, "x")
        c.put(-1, -4 + bob, "L"); c.put(1, -3 + bob, "Q")
        c.put(-1, -6 + bob, "L")                                        # highlight
        spr = outl(Spr(c.px), "d")
        px = dict(spr.px)
        # one bubble rising off the shoulder, a drip off the bottom
        ph = i % 2
        px[(-3 + (i // 2) * 6, -8 - ph + bob)] = "J" if ph == 0 else "Q"
        if i in (1, 2): px[(0, 0)] = "Q" if i == 1 else "D"
        out.append(Spr(px))
    return out


def fx_frenzy(rx=9.0, ry=3.2, n=14):
    """FxZhkFrenzy: Brood Mother pheromone frenzy on a Zhekra monster. Laid at the feet so it fits any body size:
    a churning ring of amber pheromone motes and short orange speed streaks whirling round the legs. Loop 4.
    Origin = the feet."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(n):
            a = (k / float(n) + i / 22.0) * 2 * math.pi
            x, y = rx * math.cos(a), -1.5 + ry * math.sin(a)
            front = math.sin(a) > 0
            ch = ("E" if k % 3 == 0 else "9") if front else ("8" if k % 2 else "7")
            c.put(*P(x, y), ch)
            if True:                                                    # a short trailing streak behind each mote
                a2 = a - 0.22
                c.put(*P(rx * math.cos(a2), -1.5 + ry * math.sin(a2)), "8" if front else "6")
        # rising heat flecks (frenzy = speed + attack rate)
        for k in range(3 if rx < 12 else 5):
            ph = (i + k) % 4
            x = int(-rx * 0.66) + k * int(rx * 0.66) // (1 if rx < 12 else 2) + (1 if ph % 2 else 0)
            c.put(*P(x, -3 - ph * 1.6), "9" if ph < 2 else "7")
            if ph < 3: c.put(*P(x, -2 - ph * 1.6), "7")
        out.append(c.spr())
    return out


def build_fx3(outdir):
    fx_sheet("FxZhkHornetStinger", [("Fly", fx_hornet_stinger(), [0.04] * 4)], outdir)
    fx_sheet("FxZhkAcidMark", [("Loop", fx_acid_mark(), [0.12, 0.1, 0.12, 0.1])], outdir)
    fx_sheet("FxZhkFrenzy", [("Loop", fx_frenzy(), [0.08] * 4), ("LoopBig", fx_frenzy(15.0, 5.0, 22), [0.08] * 4)], outdir)


# ================================================================== ICONS, SHOP BUBBLES, GOD PORTRAIT
def icon_frame(c):
    sp = Spr({k: v for k, v in c.px.items() if -7 <= k[0] <= 6 and -14 <= k[1] <= -1})
    return outl(sp, "0")


def icon_acid_spit(ph):
    """Acid Spit: a glob of acid arcing up and right, drips trailing, a sizzling pool below."""
    c = cv()
    for x in range(-6, 1):
        c.put(x, -2, "D" if x % 2 else "Q")
    ell(c, -3, -2.2, 3.4, 1.2, "dDQ", bias=0.2)
    c.put(-4, -3, "J")
    for k in range(4):                                    # the arc it flew
        c.put(*P(-4 + k * 1.6, -5 - k * 1.7), "D" if k < 2 else "Q")
    ell(c, 2.4, -10.4, 3.2, 2.9, "dDQJ", bias=0.25)
    c.put(1, -12, "L"); c.put(2, -12, "J")
    c.put(*P(3.5, -9 + ph), "L")
    c.put(5, -7 + ph, "Q"); c.put(4, -6 + ph * 2, "D")      # drip
    out = icon_frame(c)
    if ph:
        out = merge(out, Spr({(-6, -4): "l", (-5, -5): "~", (0, -4): "~"}))
    return out


def icon_hive_amber(ph):
    """Hive Amber: a six-sided lump of amber resin, a curled larva caught inside, honeycomb facets."""
    c = cv()
    hexp = [(-5.5, -7.5), (-3, -12.5), (3, -12.5), (5.8, -7.5), (3, -2.2), (-3, -2.2)]
    poly(c, hexp, "8", shade=lambda x, y: pick("6789E", 0.95 - (x + 6) * 0.07 - (y + 13) * 0.09))
    # facet lines
    line(c, -3, -12, 0, -7.5, "7"); line(c, 0, -7.5, 5, -7.5, "7"); line(c, 0, -7.5, -3, -3, "7")
    # the larva inside, curled
    for (x, y, ch) in ((-1, -9, "f"), (0, -10, "M"), (1, -10, "M"), (2, -9, "f"), (2, -8, "M"), (1, -7, "f"), (0, -7, "x")):
        c.put(x, y, ch)
    c.put(-1, -8, "1")
    c.put(-3, -11, "E"); c.put(-4, -10, "E" if ph == 0 else "9"); c.put(4, -5, "9")
    out = icon_frame(c)
    if ph:
        out = merge(out, Spr({(6, -12): "E", (-6, -3): "9"}))
    return out


def honeycomb(c, x0, y0, x1, y1, ph=0):
    """Dark hive walls: hex cells in chitin brown with a little amber glow in a few cells."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            row = (y + 30) // 4
            xx = x + (2 if row % 2 else 0)
            lx, ly = xx % 4, (y + 30) % 4
            wall = (ly == 0) or (lx == 0)
            cell = ((xx // 4) * 7 + row * 3) % 11
            if wall: ch = "1"
            elif cell == 0: ch = "6" if (ph + row) % 2 else "2"
            elif cell == 5: ch = "d"
            else: ch = "0"
            c.put(x, y, ch)


def deity_portrait(ph):
    bg = cv()
    honeycomb(bg, -14, -23, 14, 0, ph)
    c = cv()
    sway = [0, 1, 0, -1][ph]
    # the queen's crown: amber resin spines fanned behind the head
    for k in range(7):
        a = math.radians(-160 + k * 23.3)
        b0 = (sway * 0.3 + 6.0 * math.cos(a), -12 + 5.0 * math.sin(a))
        b1 = (sway * 0.3 + 10.5 * math.cos(a), -12 + 9.5 * math.sin(a))
        tube(c, [b0, b1], [1.3, 0.5], "6789", bias=0.2)
        c.put(*P(*b1), "E" if (k + ph) % 3 == 0 else "9")
    # head: a wide chitin skull seen from the front
    ell(c, sway * 0.3, -11.5, 7.2, 6.4, "2345", bias=0.15,
        shader=lambda nu, nv, d, l, ch, X, Y: "5" if (l > 0.7 and d < 0.35) else pick("2344", l))
    hx = sway * 0.3
    line(c, hx, -17, hx, -13, "1")                                           # median suture
    # compound eyes: two big acid domes
    for sd in (-1, 1):
        ell(c, hx + sd * 3.6, -12.5, 2.2, 2.4, "dDQJ", bias=0.3)
        c.put(*P(hx + sd * 3.6 - 0.6, -13.6), "L" if ph != 2 else "J")
    # mandibles closing over the mouth, acid drool
    for sd in (-1, 1):
        pts = [(hx + sd * 3.0, -6.5), (hx + sd * 3.8, -4.0), (hx + sd * 1.2, -2.5)]
        polyline(c, pts, "7"); c.put(*P(*pts[1]), "8"); c.put(*P(*pts[-1]), "9")
    ell(c, hx, -6.2, 2.0, 1.4, "x0x", bias=0.0)
    for k, x in enumerate((-1, 1)):
        n = 2 + (ph + k) % 3
        for j in range(n):
            c.put(*P(hx + x, -5 + j), "Q" if j < n - 1 else "J")
    # antennae
    for sd in (-1, 1):
        polyline(c, [(hx + sd * 2.0, -17.5), (hx + sd * 4.5, -21), (hx + sd * 7.5 + sway * 0.5, -22.5)], "3")
    px = dict(bg.px)
    px.update(outl(Spr(c.px), "0").px)
    return Spr({k: v for k, v in px.items() if -14 <= k[0] <= 14 and -23 <= k[1] <= 0})


def item_card_and_bubbles(name, frames, kind, outdir):
    """Shop bubble (34x41) + HUD icon (11x7), the same way tools/sprites/item_icons.py makes them:
    spells sit on vanilla's blank parchment card, artifacts float in the lower middle of the bubble."""
    import item_icons
    card = item_icons.blank_card() if kind == "spell" else None
    tmp = os.path.join(outdir, name + ".png")
    icons = []
    m = json.load(open(os.path.join(outdir, name + ".json")))
    im = Image.open(tmp).convert("RGBA")
    for f in m["anims"][0]["frames"]:
        x, y = (f % m["cols"]) * m["cellW"], (f // m["cols"]) * m["cellH"]
        icons.append(im.crop((x, y, x + m["cellW"], y + m["cellH"])))
    bubbles = []
    for ic in icons:
        b = card.copy() if kind == "spell" else Image.new("RGBA", (34, 41), (0, 0, 0, 0))
        bb = card.getbbox() if kind == "spell" else (0, 0, 34, 41)
        cx = (bb[0] + bb[2]) // 2 - 8
        cy = (bb[1] + bb[3]) // 2 - 8 if kind == "spell" else 41 - 16 - 6
        b.alpha_composite(ic, (cx, cy))
        bubbles.append(b)

    def save(nm, fr, w, h, anim):
        img = Image.new("RGBA", (w * len(fr), h), (0, 0, 0, 0))
        for i, f in enumerate(fr): img.alpha_composite(f, (i * w, 0))
        img.save(os.path.join(outdir, nm + ".png"))
        json.dump({"cellW": w, "cellH": h, "cols": len(fr),
                   "anims": [{"name": anim, "frames": list(range(len(fr))), "durations": [0.5] * len(fr)}]},
                  open(os.path.join(outdir, nm + ".json"), "w"))
        BUILT[nm] = {"cell": (w, h), "feet": (w // 2, h - 1), "anims": [(anim, len(fr), [0.5] * len(fr))], "img": img, "man": None}
    save(name + "Bubble", bubbles, 34, 41, "Bubble")
    bbox = icons[0].getbbox()
    crop = icons[0].crop(bbox)
    s_ = min(11 / crop.width, 7 / crop.height)
    small = crop.resize((max(1, round(crop.width * s_)), max(1, round(crop.height * s_))), Image.NEAREST)
    hud = Image.new("RGBA", (11, 7), (0, 0, 0, 0))
    hud.alpha_composite(small, ((11 - small.width) // 2, (7 - small.height) // 2))
    if kind != "spell":
        save(name + "Hud", [hud], 11, 7, "Hud")
    print("built", name + "Bubble" + ("" if kind == "spell" else " + Hud"))


def build_icons(outdir):
    for name, fn, kind in (("IconZhkAcidSpit", icon_acid_spit, "spell"), ("IconZhkHiveAmber", icon_hive_amber, "artifact")):
        frames = [fn(0), fn(1)]
        img, man = pack(name, [("Idle", frames, [0.5, 0.5])], 16, 16, (8, 15), outdir)
        preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=10)
        BUILT[name] = {"cell": (16, 16), "feet": (8, 15), "anims": [("Idle", 2, [0.5, 0.5])], "img": img, "man": man}
        print("built", name)
        item_card_and_bubbles(name, frames, kind, outdir)


# ================================================================== v0.10 unique-evolution tree: new monsters
# Tree (every evolved monster has one parent):
#   Grub -> Spitter (-> Mother, Bloater), Soldier (-> Mantis, Antlion)
#   Drone -> Hornet (-> Hive, Hunter), Siphon (-> Gorger, Botfly)
#   Beetle -> Nasute (-> Colossus, Mortar), Scarab (-> Stag, SunScarab)
PALETTE.update({
    # blood (Blood Siphon line): engorged abdomens, drained drops
    'α': (0x34, 0x0e, 0x16), 'β': (0x68, 0x16, 0x1e), 'γ': (0xa4, 0x26, 0x26), 'δ': (0xdc, 0x48, 0x34), 'ε': (0xff, 0x9a, 0x74),
    # Hunting Wasp: metallic blue-black (lifted so it reads on a dark floor) and burnt-orange wings
    'θ': (0x1a, 0x1a, 0x2c), 'ι': (0x2c, 0x30, 0x52), 'κ': (0x42, 0x4e, 0x82), 'ο': (0x62, 0x7c, 0xb8), 'π': (0xa8, 0xc4, 0xf0),
    'ρ': (0x8a, 0x34, 0x10), 'ς': (0xd2, 0x62, 0x1a), 'τ': (0xf6, 0x9a, 0x3a),
    # jewel teal (Amber Scarab line)
    'σ': (0x10, 0x2c, 0x30), 'υ': (0x1a, 0x52, 0x52), 'φ': (0x26, 0x7e, 0x72), 'χ': (0x48, 0xb0, 0x94), 'ψ': (0xa0, 0xf0, 0xd0),
    # violet sheen (Stag), dusty sand (Antlion), bristle
    'ω': (0x30, 0x1a, 0x46), 'Ω': (0x56, 0x30, 0x7a), 'Ψ': (0x8a, 0x5c, 0xb8),
    'Σ': (0x4a, 0x3a, 0x2a), 'Φ': (0x76, 0x60, 0x40), 'Χ': (0xa8, 0x8e, 0x5c), 'Λ': (0xd2, 0xbc, 0x86),
    # botfly fur (ash grey-brown) and its pale eggs
    'Γ': (0x3a, 0x34, 0x30), 'Δ': (0x5e, 0x56, 0x4c), 'Θ': (0x8c, 0x82, 0x70), 'Ξ': (0xbc, 0xb2, 0x9a), 'Π': (0xf2, 0xee, 0xdc),
})
BLOOD = "αβγδ"
BLOOD_L = "βγδε"
INDIGO = "θικο"
INDIGO_L = "ικοπ"
ORANGE_W = ("ς", "τ", "ρ")
TEAL = "συφχ"
TEAL_L = "υφχψ"
VIOLET = "ωΩΨχ"
SAND = "ΣΦΧΛ"
FUR = "ΓΔΘΞ"
GLOW |= set("δε")


def banded_leg(c, hip, foot, l1, l2, bend, cols=("h", "2"), joint="i"):
    """A long thin insect leg by IK, its segments banded in two colours (mosquito / stilt legs)."""
    knee, end = ik(hip[0], hip[1], foot[0], foot[1], l1, l2, bend)
    for (a, b) in ((hip, knee), (knee, end)):
        pts = line_px(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1])))
        for i, (x, y) in enumerate(pts):
            c.put(x, y, cols[(i // 2) % 2])
    c.put(*P(*knee), joint)
    return knee


# ------------------------------------------------------------------ BLOOD SIPHON (T2, Drone line; flier)
# The Brood Drone grown into a mosquito: the drone's dark thorax with its amber collar, its pale wings (narrow now),
# its amber-and-black banded abdomen that turns blood-red and swells as it drinks, a long needle proboscis where the
# drone had a mandible, and six long pale banded legs, the hind pair raised up behind. A thin horizontal "needle"
# where its sibling the Hive Hornet is a tall dark-red "T".
def siphon(dx=0.0, dy=0.0, tilt=0.0, wph=0, fill=0.0, legs=0.0, eye="open", nose=28.0, reach=0.0, extra=None,
           streak=0, fold=False, drip=0):
    f = Fr()
    cx, cy = dx, dy - 13.0
    piv = (cx, cy)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # legs: front pair forward-down, middle straight down, hind pair raised up and back (far set in shadow)
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx, fy, bend) in enumerate(((1.2, 3.6, 9.0, -1), (0.0, -1.6, 10.0, 1), (-1.2, -10.5, -2.5, -1))):
            sw = math.sin(legs + j * 1.9 + side * 1.3) * 0.9
            hp = R(hx - (0 if side else 0.7), 1.8)
            ft = R(fx + sw - (0 if side else 1.2), fy + (0.6 if side else 0) - (1.2 if (j == 2 and not side) else 0))
            if side: banded_leg(cv_, hp, ft, 4.8 if j < 2 else 5.6, 5.6 if j < 2 else 6.4, bend, cols=("w", "3"), joint="W")
            else: banded_leg(cv_, hp, ft, 4.8 if j < 2 else 5.6, 5.6 if j < 2 else 6.4, bend, cols=("2", "3"), joint="3")
    # abdomen: long and thin when empty (the drone's amber/black bands), blood-red and swollen when full
    wst = R(-2.0, 0.6)
    aa = 168 + tilt - 10 * fill
    ar = math.radians(aa)
    L = 5.0 + 1.2 * fill
    ac = (wst[0] + L * math.cos(ar), wst[1] + L * math.sin(ar))
    ry = 1.7 + 1.9 * fill
    def band(nu, nv, d, l, ch, X, Y):
        b = int((nu + 1.0) * 3.0)
        if b % 2 == 1:
            return pick("1223", l) if fill < 0.5 else pick("βγ", l)
        if fill > 0.15 and nv > -0.55 + fill * 0.4:
            if l > 0.6 and d < 0.45: return "ε" if fill > 0.6 else "δ"
            return pick(BLOOD_L if fill > 0.5 else BLOOD, l + 0.1)
        return pick(AMB_L, l - 0.05)
    ell(f.b, ac[0], ac[1], L + 0.4, ry, AMB_L, ang=aa + 180, bias=0.1, shader=band)
    tail = (wst[0] + (2 * L + 0.6) * math.cos(ar), wst[1] + (2 * L + 0.6) * math.sin(ar))
    f.b.put(*P(*tail), "2")
    if drip:
        for k in range(drip): f.g.put(*P(tail[0], tail[1] + 1 + k), "δ" if k < drip - 1 else "ε")
    # thorax: a humped dark shield with the drone's amber collar
    ell(f.b, *R(0.2, -0.4), 2.9, 2.5, CHIT_L, ang=tilt, bias=0.15)
    tp = R(-0.2, -2.2)
    line(f.b, tp[0] - 1.4, tp[1] + 0.5, tp[0] + 1.4, tp[1] - 0.2, "8")
    f.b.put(*P(*R(-1.2, -1.0)), "5")
    # head: small and round, a big acid-green compound eye
    hx, hy = R(3.6, -0.2)
    ell(f.b, hx, hy, 1.7, 1.7, CHIT, bias=0.15)
    # proboscis: the needle, angled down by nose, longer with reach; two short palps beside it
    na = math.radians(nose + tilt)
    p0 = (hx + 1.4 * math.cos(na), hy + 1.4 * math.sin(na))
    pl = 7.0 + reach
    p1 = (p0[0] + pl * math.cos(na), p0[1] + pl * math.sin(na))
    line(f.b, p0[0], p0[1] + 1, p0[0] + pl * 0.55 * math.cos(na), p0[1] + 1 + pl * 0.55 * math.sin(na), "2")   # under-shadow
    line(f.b, p0[0], p0[1], p1[0], p1[1], "W")
    line(f.b, p0[0], p0[1], p0[0] + 2.0 * math.cos(na), p0[1] + 2.0 * math.sin(na), "5")
    f.g.put(*P(*p1), "δ" if fill > 0.2 else "9")
    f.pts["tip"] = p1
    # feathery antennae
    polyline(f.b, [(hx + 0.2, hy - 1.4), (hx + 1.2, hy - 3.2), (hx + 2.8, hy - 4.0)], "3")
    f.b.put(*P(hx + 1.0, hy - 2.6), "4")
    if eye != "dead":
        for (a, b, ch) in ((0.5, -0.4, "Q"), (0.5, -1.2, "J" if eye != "squint" else "Q"), (1.3, -0.4, "D")):
            f.g.put(*P(hx + a, hy + b), ch)
        if eye == "wide": f.g.put(*P(hx - 0.3, hy - 1.0), "L")
    else:
        f.g.put(*P(hx + 0.5, hy - 0.8), "1")
    # wings: the drone's pale wings, long and narrow, laid back over the abdomen; a blur when they beat
    root = R(-0.6, -2.0)
    if fold:
        wing(f.g, root, 176 + tilt, 9.0, 1.3)
    else:
        angs = [-150, -168, -186, -164][wph % 4]
        wing(f.g, (root[0] - 0.4, root[1] + 0.4), angs + 16 + tilt * 0.4, 7.4, 1.2, wph + 1)
        wing(f.g, root, angs + tilt * 0.4, 9.0, 1.5, wph)
    for s in range(streak):
        y = cy - 1 + s * 2
        line(f.g, cx - 9 - s * 2, y - 2 + s, cx - 13 - s * 2, y - 3 + s, "l" if s % 2 else "z", over=False)
    if extra: extra(f, (hx, hy), p1)
    return f.done()


def siphon_corpse():
    f = Fr()
    for x in range(-8, 3):
        if x % 3: f.n.put(x, 0, "β" if x % 2 else "γ")
    ell(f.b, -4.0, -1.8, 4.4, 1.6, BLOOD, bias=0.1,
        shader=lambda nu, nv, d, l, ch, X, Y: pick("123", l) if int((nu + 1) * 3) % 2 else pick(BLOOD, l))
    ell(f.b, 1.6, -2.0, 2.2, 1.8, CHIT_L)
    ell(f.b, 4.6, -1.6, 1.4, 1.3, CHIT)
    line(f.b, 5.8, -1.2, 10.0, -0.2, "5")
    for (x0, x1, y1) in ((0.4, -1.6, -7.0), (1.8, 2.6, -8.0), (3.0, 6.0, -6.0)):
        polyline(f.b, [(x0, -3.4), ((x0 + x1) / 2, y1), (x1, y1 + 1.5)], "i3")
    wing(f.g, (0.0, -3.0), -170, 8.0, 1.3)
    f.g.put(4, -2, "1")
    return f.done()


def build_siphon(outdir):
    S_ = siphon
    idle = [S_(wph=i, dy=[0, -0.6, -1.0, -0.4][i], legs=i * 0.8) for i in range(4)]
    run = [S_(wph=i % 4, dy=-0.5 * math.sin(i * math.pi / 3), tilt=9, legs=i * 1.1 + 0.5, nose=34) for i in range(6)]

    def flecks(n):
        def fn(f, head, tip):
            for j in range(n):
                f.g.put(*P(tip[0] + 1 + (j % 3), tip[1] - 1 + (j // 3) * 2 - (j % 2)), "ε" if j % 2 else "δ")
        return fn
    # STAB: rear back (proboscis up), thrust, HIT (needle buried, blood flecks), pull out dripping, recover
    stab = [S_(wph=0, tilt=-8, nose=10, dx=-0.6, eye="wide"),
            S_(wph=1, tilt=-14, nose=0, dx=-1.8, dy=-0.8, eye="wide"),
            S_(wph=2, tilt=8, nose=22, dx=2.0, reach=1.5, eye="wide"),
            S_(wph=3, tilt=12, nose=24, dx=3.2, reach=2.5, eye="squint", fill=0.15, extra=flecks(5)),
            S_(wph=0, tilt=6, nose=26, dx=1.6, fill=0.2, extra=flecks(2)),
            S_(wph=1, tilt=0, nose=28, dx=0.4, fill=0.1)]
    # DRINK: rise, aim, DIVE (streak; dash + drain hits from here), latched: the abdomen fills red, pull off, recover
    drink = [S_(wph=0, dy=-1.6, tilt=-6, nose=14, eye="wide"),
             S_(wph=2, dy=-2.2, dx=-1.2, tilt=-14, nose=6, eye="wide"),
             S_(fold=True, dx=1.6, dy=0.6, tilt=24, nose=30, reach=1.0, streak=2, eye="wide"),
             S_(wph=1, dx=2.4, dy=1.2, tilt=16, nose=32, reach=2.0, fill=0.3, eye="squint", extra=flecks(3)),
             S_(wph=3, dx=2.4, dy=1.0, tilt=14, nose=32, reach=2.0, fill=0.6, eye="squint", extra=flecks(2)),
             S_(wph=1, dx=2.2, dy=1.0, tilt=14, nose=32, reach=2.0, fill=0.85, eye="squint", extra=flecks(3)),
             S_(wph=2, dx=0.8, dy=-0.4, tilt=2, nose=26, fill=1.0, drip=2),
             S_(wph=0, dy=-0.2, nose=28, fill=0.6, drip=1)]
    death = [S_(wph=1, tilt=-30, nose=-10, eye="wide", dy=-1, fill=0.4),
             S_(fold=True, tilt=-70, nose=40, eye="dead", dy=3.0, fill=0.2),
             grounded(S_(fold=True, tilt=-160, eye="dead", fill=0.1)),
             siphon_corpse()]
    knock = S_(wph=2, tilt=-22, nose=0, dx=-1, eye="squint")
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6),
             ("Stab", stab, [0.12, 0.14, 0.07, 0.06, 0.12, 0.12]),
             ("Drink", drink, [0.12, 0.14, 0.08, 0.12, 0.12, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkSiphon", "Stab", stab, "tip"); note("ZhkSiphon", "Drink", drink, "tip")
    sheet("ZhkSiphon", anims, outdir, scale=6, remap=LIFT)


# ------------------------------------------------------------------ BLOOD GORGER (T3, Blood Siphon line)
# The siphon drank until it could not fly: a vast translucent blood sac slung between six towering pale stilt legs
# (the siphon's banded legs, now long as a man), a small dark thorax with the amber collar, shrivelled wings, and
# the needle grown into a long drill. Tall and spindly; red where its sibling the Botfly is grey fur and pale eggs.
def blood_sac(f, cx, cy, rx, ry, ang=0.0, ph=0, pump=0.0, bands=True):
    """The engorged abdomen: translucent crimson, ring creases between its segments, the old amber/black dorsal bands
    stretched into thin dark plates along the top, a wet highlight; pump (0..1) squeezes it and lights it up."""
    def sh(nu, nv, d, l, ch, X, Y):
        u = (nu + 1.0) * 2.6 + 0.15 * nv
        fr = u - math.floor(u)
        if fr < 0.12 and 0.4 < u < 5.0 and nv > -0.8: return "β" if nv > 0.2 else "γ"      # segment crease
        if bands and nv < -0.62 and 0.3 < fr < 0.8:
            return "3" if l > 0.55 else "2"                                             # stretched dorsal plate
        if nv > 0.66: return pick("βγ", l + 0.3)
        if l > 0.6 and d < 0.4: return "ε"
        return pick(BLOOD_L, l + 0.12 + 0.2 * pump)
    ell(f.b, cx, cy, rx, ry, BLOOD, ang=ang, bias=0.0, shader=sh)


def gorger(dx=0.0, dy=0.0, lean=0.0, legs=0.0, sag=0.0, pump=0.0, nose=38.0, reach=0.0, eye="open", ph=0, wph=0,
           crouch=0.0, extra=None, head=0.0, drip=0, mist=0):
    f = Fr()
    H = 24.0 - crouch * 5.0
    cx, cy = dx, dy - H
    piv = (cx, cy + 4)
    R = lambda x, y: rot((cx + x, cy + y), piv, lean)
    # six stilt legs: knees raised high above the body like a crane fly's, feet spread wide (far set in shadow)
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, kx, ky, fx) in enumerate(((1.6, 7.0, -8.0, 14.0), (0.2, 1.0, -9.0, 3.5), (-1.4, -8.0, -7.0, -13.0))):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(hx - (0 if side else 0.8), 1.2)
            kn = (hp[0] + kx * (1 - 0.15 * crouch) + 0.8 * math.sin(pha) - (0 if side else 1.0), hp[1] + ky * (1 - 0.3 * crouch) - (0 if side else -0.8))
            ft = (dx + fx * (1 - 0.1 * crouch) + 1.8 * math.sin(pha) - (0 if side else 1.4), -max(0.0, 1.6 * math.cos(pha)))
            cols = ("W", "3") if side else ("2", "3")
            for (a, b) in ((hp, kn), (kn, ft)):
                for i, (x, y) in enumerate(line_px(*P(*a), *P(*b))):
                    cv_.put(x, y, cols[(i // 2) % 2])
            cv_.put(*P(*kn), "X" if side else "3")
            cv_.put(*P(ft[0] + 0.5, ft[1]), "3" if side else "2")
    # the sac, slung behind and under the thorax
    sx, sy = R(-9.4, 5.4 + sag)
    rx, ry = 10.0 - pump * 1.6, 6.8 - pump * 1.0 + sag * 0.3
    line(f.b, *R(-2.4, 0.6), *R(-0.6, 0.2), "2")                                 # the thin waist
    blood_sac(f, sx, sy, rx, ry, ang=-14 + lean, ph=ph, pump=pump)
    tail = (sx - rx * 0.95, sy + 1.0)
    if drip:
        for k in range(drip): f.g.put(*P(tail[0] + 1, tail[1] + 2 + k), "γ" if k < drip - 1 else "δ")
    # pores along the top that mist blood when it transfuses
    pores = [R(-11.0 + k * 3.4, -1.2 + sag - abs(k - 1.5) * 0.6) for k in range(4)]
    for q in pores: f.g.put(*P(*q), "δ" if pump > 0.3 else "γ")
    rnd = random.Random(mist * 7 + 1)
    for k in range(mist * 4):
        q = pores[k % 4]
        f.g.put(*P(q[0] + rnd.uniform(-1.5, 1.5), q[1] - 1 - rnd.uniform(0, 2.5 + mist * 1.6)), "δε"[k % 2], over=False)
    # thorax: humped dark shield, the amber collar
    ell(f.b, *R(0.4, -0.6), 3.8, 3.2, CHIT_L, ang=lean, bias=0.15)
    tp = R(0.0, -3.0)
    line(f.b, tp[0] - 1.8, tp[1] + 0.6, tp[0] + 1.8, tp[1] - 0.3, "8")
    f.b.put(*P(*R(-1.4, -1.6)), "5")
    # shrivelled wings, folded and twitching
    wing(f.g, R(-1.0, -2.8), -168 + lean + (wph % 2) * 8, 7.0, 1.3, wph)
    # head + proboscis drill
    hx, hy = R(4.8, -1.0 + head)
    ell(f.b, hx, hy, 2.3, 2.2, CHIT, bias=0.15)
    na = math.radians(nose + lean)
    p0 = (hx + 1.8 * math.cos(na), hy + 1.8 * math.sin(na))
    pl = 11.0 + reach
    p1 = (p0[0] + pl * math.cos(na), p0[1] + pl * math.sin(na))
    tube(f.b, [p0, (p0[0] + 3 * math.cos(na), p0[1] + 3 * math.sin(na))], [1.1, 0.7], "345")
    line(f.b, p0[0], p0[1] + 1, p0[0] + pl * 0.5 * math.cos(na), p0[1] + 1 + pl * 0.5 * math.sin(na), "2")
    line(f.b, p0[0], p0[1], p1[0], p1[1], "W")
    for t in (0.45, 0.7):                                                     # drill barbs
        q = (p0[0] + pl * t * math.cos(na), p0[1] + pl * t * math.sin(na))
        f.b.put(*P(q[0] - math.sin(na), q[1] + math.cos(na)), "4")
    f.g.put(*P(*p1), "δ" if reach > 0.5 or pump > 0 else "X")
    f.pts["tip"] = p1
    polyline(f.b, [(hx + 0.2, hy - 1.8), (hx + 1.6, hy - 4.0), (hx + 3.6, hy - 5.0)], "3")
    if eye != "dead":
        for (a, b, ch) in ((0.7, -0.6, "Q"), (0.7, -1.5, "J" if eye != "squint" else "Q"), (1.6, -0.6, "D"), (1.6, -1.5, "Q")):
            f.g.put(*P(hx + a, hy + b), ch)
        if eye == "wide": f.g.put(*P(hx - 0.2, hy - 1.2), "L")
    else:
        f.g.put(*P(hx + 0.7, hy - 1.0), "1")
    f.pts["sac"] = (sx, sy - ry)
    if extra: extra(f, (hx, hy), p1)
    return f.done()


def gorger_corpse():
    f = Fr()
    for x in range(-16, 6):
        if (x * 3) % 5: f.n.put(x, 0, "β" if x % 2 else "α")
    f.n.put(-6, -1, "γ")
    ell(f.b, -7.0, -2.6, 8.4, 2.6, BLOOD, bias=0.0,
        shader=lambda nu, nv, d, l, ch, X, Y: "1" if nv < -0.4 and int((nu + 1) * 2.4) % 2 else pick("αβγ", l))
    ell(f.b, 3.0, -2.4, 2.8, 2.2, CHIT_L)
    ell(f.b, 6.6, -2.0, 1.8, 1.6, CHIT)
    line(f.b, 8.0, -1.6, 15.0, -0.2, "W")
    for (x0, x1, h) in ((0.0, -6.0, -12.0), (2.0, 4.0, -13.0), (4.0, 11.0, -11.0)):
        banded_leg(f.b, (x0, -4.0), (x1, -4.0), 6.0, 6.5, -1, cols=("W", "3"), joint="X")
    f.g.put(7, -2, "1")
    return f.done()


def build_gorger(outdir):
    G_ = gorger
    idle = [G_(ph=0, wph=0), G_(ph=1, wph=1, dy=0.3, sag=0.3, legs=0.15), G_(ph=2, wph=0, dy=0.5, sag=0.6, legs=0.25, eye="squint"),
            G_(ph=3, wph=1, dy=0.2, sag=0.3, legs=0.1, drip=1)]
    run = [G_(legs=i * math.pi / 3 + math.pi / 6, dy=-0.8 * abs(math.sin(i * math.pi / 3 + math.pi / 6)), lean=3,
              sag=0.6 * math.cos(i * math.pi / 3), ph=i, wph=i % 2, nose=44) for i in range(6)]

    def spray(n):
        def fn(f, head, tip):
            for j in range(n):
                f.g.put(*P(tip[0] + 1 + (j % 3) * 1.2, tip[1] - 2 + (j // 3) * 2 + (j % 2)), "ε" if j % 2 else "δ")
        return fn
    # DRILL: head up, the needle drawn back, PLUNGE (hit, the sac pulses), twist and draw (drip), recover
    drill = [G_(nose=10, head=-1.0, lean=-4, eye="wide", ph=0),
             G_(nose=-6, head=-1.6, lean=-8, dx=-1.0, eye="wide", ph=1, crouch=0.3),
             G_(nose=34, lean=6, dx=1.8, reach=3.0, eye="wide", ph=2),
             G_(nose=40, lean=9, dx=2.6, reach=5.0, eye="squint", ph=3, pump=0.4, extra=spray(6)),
             G_(nose=40, lean=8, dx=2.4, reach=5.0, eye="squint", ph=4, pump=0.7, extra=spray(3)),
             G_(nose=36, lean=4, dx=1.0, reach=1.0, ph=5, pump=0.3, drip=2),
             G_(nose=38, ph=6, drip=1)]
    # TRANSFUSE: crouch and squeeze, the pores MIST blood (heals allies), the sac slackens, rise
    trans = [G_(crouch=0.4, pump=0.2, ph=0, eye="squint"),
             G_(crouch=0.9, pump=0.6, ph=1, eye="squint", nose=50),
             G_(crouch=1.2, pump=1.0, ph=2, eye="squint", nose=56, mist=1),
             G_(crouch=1.0, pump=1.0, ph=3, eye="wide", nose=40, mist=3),
             G_(crouch=0.7, pump=0.7, ph=4, nose=36, mist=3),
             G_(crouch=0.5, pump=0.4, ph=5, mist=2, sag=-0.4),
             G_(crouch=0.2, pump=0.1, ph=6, mist=1, sag=-0.4),
             G_(ph=7)]
    death = [G_(nose=-20, head=-1.6, lean=-8, eye="wide", pump=0.8),
             G_(crouch=2.4, lean=-10, eye="dead", sag=1.4, nose=60, dy=0.5, legs=1.0),
             grounded(G_(crouch=3.4, lean=-6, eye="dead", sag=2.0, nose=70, legs=2.0)),
             gorger_corpse()]
    knock = G_(nose=0, head=-1.2, lean=-10, dx=-1.0, eye="squint", sag=0.6)
    anims = [("Idle", idle, [0.26, 0.2, 0.26, 0.2]), ("Run", run, [0.1] * 6),
             ("Drill", drill, [0.14, 0.14, 0.07, 0.06, 0.12, 0.12, 0.14]),
             ("Transfuse", trans, [0.12, 0.14, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.4], knock)
    note("ZhkGorger", "Drill", drill, "tip"); note("ZhkGorger", "Transfuse", trans, "sac")
    sheet("ZhkGorger", anims, outdir, scale=5)


# ------------------------------------------------------------------ BOTFLY MATRON (T3, Blood Siphon line; flier)
# A fat, hairy fly: ash-grey fur over a round thorax, the siphon's banded abdomen gone furry and hung with clusters of
# pale eggs, the siphon's pale wings broad now, and its needle shortened into a hooked egg-laying sting under the
# tail. Huge acid-green eyes. Round, grey and egg-studded where its sibling the Gorger is a red sac on stilts.
def fur_shader(ramp, seed=0, bands=0, band_ramp=None):
    def sh(nu, nv, d, l, ch, X, Y):
        n = ((X * 7 + Y * 13 + seed) * 2654435761 >> 7) % 7
        l2 = l + (0.18 if n == 0 else (-0.16 if n == 1 else 0.0))
        if d > 0.86 and n in (2, 3): return None                         # ragged hairy edge
        if bands and band_ramp:
            b = int((nu + 1.0) * bands)
            if b % 2 == 1: return pick(band_ramp, l2)
        return pick(ramp, l2)
    return sh


def botfly(dx=0.0, dy=0.0, tilt=0.0, wph=0, curl=0.0, legs=0.0, eye="open", eggs=7, extra=None, streak=0, jaw=0.0, fold=False,
           ovi=0.0):
    f = Fr()
    cx, cy = dx, dy - 17.0
    piv = (cx, cy)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # legs: thick, hairy, banded pale (the siphon's), front pair clasping forward (far set in shadow)
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx, fy) in enumerate(((2.4, 7.0, 9.0), (0.4, 1.0, 11.0), (-1.8, -5.0, 10.5))):
            sw = math.sin(legs + j * 1.9 + side * 1.3) * 0.9
            hp = R(hx - (0 if side else 0.9), 3.6)
            ft = R(fx + sw - (0 if side else 1.2), fy + (0.6 if side else 0))
            if side:
                knee, end = ik(hp[0], hp[1], ft[0], ft[1], 4.6, 5.4, -1 if j == 0 else 1)
                tube(cv_, [hp, knee], [1.0, 0.8], "ΔΘΞ")
                line(cv_, knee[0], knee[1], end[0], end[1], "wwΔ")
            else:
                leg(cv_, hp, ft, 4.6, 5.4, -1 if j == 0 else 1, cols=("Γ", "Δ"), knee_hi=None)
    # abdomen: furry, banded (the siphon's bands, dusty amber under grey fur); curl swings the egg-sting under
    wst = R(-3.0, 0.8)
    aa = 158 - 70 * curl + tilt
    ar = math.radians(aa)
    ac = (wst[0] + 5.2 * math.cos(ar), wst[1] + 5.2 * math.sin(ar))
    ell(f.b, ac[0], ac[1], 6.2, 4.6, FUR, ang=aa + 180, bias=0.1, shader=fur_shader(FUR, 3, bands=3, band_ramp="7889"))
    # egg clusters glued along the underside
    for k in range(eggs):
        t = -0.75 + 1.5 * k / max(1, eggs - 1)
        ex = ac[0] + t * 5.4 * math.cos(ar) - 3.6 * math.sin(ar) * (0.9 + 0.15 * (k % 2))
        ey = ac[1] + t * 5.4 * math.sin(ar) + 3.6 * math.cos(ar) * (0.9 + 0.15 * (k % 2))
        if ey < ac[1] - 1: ey = ac[1] + 3.0
        ell(f.b, ex, ey + 0.4, 1.1, 0.9, "ΞΠΠ", bias=0.4)
    st0 = (wst[0] + 10.6 * math.cos(ar), wst[1] + 10.6 * math.sin(ar))
    st1 = (wst[0] + (12.2 + 2.0 * ovi) * math.cos(ar), wst[1] + (12.2 + 2.0 * ovi) * math.sin(ar))
    line(f.b, st0[0], st0[1], st1[0], st1[1], "W")
    if ovi > 0.5:
        ell(f.g, st1[0], st1[1], 1.2, 1.0, "ΞΠ", bias=0.4)          # an egg on the sting
    else:
        f.g.put(*P(*st1), "Q")
    f.pts["sting"] = st1
    # thorax: a big round furry ball with a dusky amber collar band (the siphon's collar, furred over)
    tx, ty = R(0.6, -0.4)
    ell(f.b, tx, ty, 5.4, 5.0, FUR, ang=tilt, bias=0.15, shader=fur_shader(FUR, 7))
    line(f.b, *R(-2.6, -3.6), *R(2.6, -4.4), "7")
    f.b.put(*P(*R(-2.0, -2.6)), "Π")
    # head: round, two great acid compound eyes, a short hooked proboscis (the siphon's needle, shortened)
    hx, hy = R(6.0, -0.6)
    ell(f.b, hx, hy, 3.2, 3.0, "ΓΔΘ", bias=0.1)
    a = math.radians(tilt)
    M = lambda ox, oy: (hx + ox * math.cos(a) - oy * math.sin(a), hy + ox * math.sin(a) + oy * math.cos(a))
    polyline(f.b, [M(2.2, 1.4), M(3.8, 2.6 + jaw), M(3.6, 4.0 + jaw * 1.4)], "W"); f.b.put(*P(*M(3.6, 4.0 + jaw * 1.4)), "5")
    f.pts["mouth"] = M(3.6, 3.0)
    if eye != "dead":
        ell(f.g, *M(0.8, -0.8), 2.1, 2.2, "DQJ", bias=0.25)
        f.g.put(*P(*M(0.2, -1.8)), "L" if eye == "wide" else "J")
        if eye == "squint": f.g.put(*P(*M(0.8, -2.2)), "Γ"); f.g.put(*P(*M(1.6, -2.0)), "Γ")
        for (ox, oy) in ((1.4, 0.2), (0.0, 0.0), (1.8, -1.0)): f.g.put(*P(*M(ox, oy)), "D")
    else:
        ell(f.b, *M(0.8, -0.8), 1.8, 1.8, "d1", bias=0.2)
    # antennae: two short stubs
    polyline(f.b, [M(1.8, -2.6), M(2.8, -4.0)], "Γ")
    # wings: the siphon's pale wings grown broad, raised in a V
    root = R(-1.0, -4.4)
    if fold:
        wing(f.g, root, 172 + tilt, 11.0, 2.6)
    else:
        angs = [-118, -138, -160, -134][wph % 4]
        wing(f.g, (root[0] - 1.0, root[1] + 0.6), angs - 24 + tilt * 0.3, 9.0, 2.8, wph + 1)
        wing(f.g, root, angs + tilt * 0.3, 11.0, 3.6, wph)
    for s_ in range(streak):
        y = cy + s_ * 3
        line(f.g, cx - 12 - s_ * 2, y - 2, cx - 17 - s_ * 2, y - 3, "l" if s_ % 2 else "z", over=False)
    if extra: extra(f, (hx, hy), st1)
    return f.done()


def botfly_corpse():
    f = Fr()
    ell(f.b, -4.0, -3.0, 6.0, 3.0, FUR, bias=0.1, shader=fur_shader(FUR, 5, bands=3, band_ramp="789"))
    ell(f.b, 3.0, -3.4, 4.2, 3.4, FUR, shader=fur_shader(FUR, 9))
    ell(f.b, 8.4, -2.6, 2.6, 2.4, "ΓΔΘ")
    ell(f.b, 9.0, -3.4, 1.6, 1.6, "d1", bias=0.2)
    for k in range(5):
        ell(f.n, -9 + k * 2.2, -0.6, 1.1, 0.8, "ΞΠ", bias=0.4)
    for (x0, x1) in ((0.0, -3.0), (2.4, 2.0), (4.6, 7.0)):
        polyline(f.b, [(x0, -6.4), ((x0 + x1) / 2, -9.0), (x1, -10.0)], "wΔ")
    wing(f.g, (0.0, -6.0), -170, 10.0, 2.0)
    return f.done()


def build_botfly(outdir):
    B_ = botfly
    idle = [B_(wph=i, dy=[0, -0.6, -1.0, -0.4][i], legs=i * 0.8, curl=0.05 * (i % 2)) for i in range(4)]
    run = [B_(wph=i % 4, dy=-0.5 * math.sin(i * math.pi / 3), tilt=8, legs=i * 1.1, curl=0.1) for i in range(6)]

    def bonk(n):
        def fn(f, head, st):
            for j in range(n):
                a = -0.9 + j * 0.45
                f.g.put(*P(head[0] + 4.6 + 2.4 * math.cos(a), head[1] + 2.4 * math.sin(a)), "Π" if j % 2 else "Ξ")
        return fn
    # RAM: hunch back, wings up, RUSH, HIT (head-first bump), bounce back, recover
    ram = [B_(wph=0, tilt=-10, dx=-0.8, eye="wide", curl=0.2),
           B_(wph=2, tilt=-16, dx=-2.0, dy=-1.0, eye="wide", curl=0.3),
           B_(fold=True, tilt=10, dx=2.6, dy=0.6, streak=2, eye="wide"),
           B_(fold=True, tilt=14, dx=3.6, dy=0.8, streak=1, eye="squint", extra=bonk(5)),
           B_(wph=1, tilt=-4, dx=1.4, eye="squint", extra=bonk(2)),
           B_(wph=3, tilt=0, dx=0.4)]
    # IMPLANT: curl the abdomen under, the egg-sting slides out with an egg on it, FLICK the egg dart, recover
    impl = [B_(wph=0, curl=0.3, tilt=-4, dy=-0.6),
            B_(wph=1, curl=0.7, tilt=-10, dx=-0.8, dy=-1.6, eye="wide", ovi=0.4),
            B_(wph=2, curl=1.0, tilt=-12, dx=-1.2, dy=-2.4, eye="wide", ovi=1.0),
            B_(wph=3, curl=1.15, tilt=-12, dx=-1.4, dy=-2.6, eye="wide", ovi=1.0),
            B_(wph=0, curl=1.2, tilt=4, dx=0.8, dy=-2.4, eye="squint", ovi=0.0, eggs=6),
            B_(wph=1, curl=0.7, dx=0.4, dy=-1.2, eggs=6),
            B_(wph=2, curl=0.2, eggs=6)]
    death = [B_(wph=1, tilt=-30, curl=0.6, eye="wide", dy=-1),
             B_(fold=True, tilt=-70, curl=0.2, eye="dead", dy=3.0, eggs=4),
             grounded(B_(fold=True, tilt=-150, curl=0.0, eye="dead", eggs=3)),
             botfly_corpse()]
    knock = B_(wph=2, tilt=-22, curl=0.5, dx=-1, eye="squint")
    anims = [("Idle", idle, [0.07] * 4), ("Run", run, [0.06] * 6),
             ("Ram", ram, [0.12, 0.14, 0.07, 0.06, 0.12, 0.12]),
             ("Implant", impl, [0.12, 0.14, 0.14, 0.12, 0.06, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkBotfly", "Ram", ram, "mouth"); note("ZhkBotfly", "Implant", impl, "sting")
    sheet("ZhkBotfly", anims, outdir, scale=5)


# ------------------------------------------------------------------ HUNTING WASP (T3, Hive Hornet line; flier)
# A spider wasp: the hornet's upright build, hanging abdomen, horned head and four raised wings, grown long and lean,
# its chitin gone metallic blue-black and its smoky wings burnt orange. Long spiny legs held forward as a cage, curled
# orange antennae, and the sting drawn out into a lance. Slim and cold-blue next to its sibling, the gold Amber Hive.
def hunter(dx=0.0, dy=0.0, tilt=0.0, wph=0, curl=0.0, legs=0.0, eye="open", jaw=0.2, extra=None, streak=0, lance=0.0,
           blur=0, reach=0.0, cage=0.0):
    f = Fr()
    cx, cy = dx, dy - 22.0
    piv = (cx, cy)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # long spiny legs: front two pairs reach forward as a basket, the hind pair trails far down
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, kx, ky, ex, ey) in enumerate(((2.2, 6.0 + cage, 2.0, 9.0 + cage * 2, 6.0 - cage * 2), (0.8, 3.0, 4.6, 5.0 + cage, 10.0 - cage),
                                                  (-0.8, -4.0, 6.0, -5.6, 14.0))):
            sw = math.sin(legs + j * 1.7 + side) * 0.8
            h = R(hx - (0 if side else 0.6), 2.0)
            k = R(kx + sw * 0.5 - (0 if side else 0.6), ky)
            e = R(ex + sw - (0 if side else 0.8), ey + (0.6 if side else 0))
            line(cv_, h[0], h[1], k[0], k[1], "κ" if side else "θ")
            line(cv_, k[0], k[1], e[0], e[1], "ο" if side else "ι")
            if side:
                cv_.put(*P(*k), "π")
                m = ((k[0] + e[0]) / 2, (k[1] + e[1]) / 2)
                cv_.put(*P(m[0] + 0.8, m[1] - 0.6), "ς")                         # orange tibial spur
    # petiole and the long hanging abdomen; curl swings the lance forward
    w0 = R(-1.8, 1.6)
    aa = 100 - 70 * curl + tilt
    ar = math.radians(aa)
    w1 = (w0[0] + 1.8 * math.cos(ar), w0[1] + 1.8 * math.sin(ar))
    line(f.b, w0[0], w0[1], w1[0], w1[1], "ι")
    ac = (w1[0] + 5.2 * math.cos(ar), w1[1] + 5.2 * math.sin(ar))
    def band(nu, nv, d, l, ch, X, Y):
        if l > 0.62 and d < 0.4: return "π"
        b = int((nu + 1.0) * 3.0)
        if b == 4 and nv > -0.3: return pick("ρς", l)                           # one orange warning band
        return pick(INDIGO_L, l)
    ell(f.b, ac[0], ac[1], 5.6, 2.9, INDIGO, ang=aa + 180, bias=0.12, shader=band)
    L = 3.4 + 4.0 * lance
    st0 = (w1[0] + 10.4 * math.cos(ar), w1[1] + 10.4 * math.sin(ar))
    st1 = (st0[0] + L * math.cos(ar), st0[1] + L * math.sin(ar))
    line(f.b, st0[0], st0[1], st1[0], st1[1], "π")
    f.g.put(*P(*st1), "τ")
    f.pts["sting"] = st1
    # thorax: lean, metallic, a bright sheen
    ell(f.b, *R(0.4, -0.2), 3.4, 2.7, INDIGO_L, ang=tilt, bias=0.15)
    f.b.put(*P(*R(-0.6, -1.6)), "π"); f.b.put(*P(*R(0.4, -1.8)), "π")
    # head: the hornet's crest, blue-black; hooked orange mandibles; curled orange antennae
    hx, hy = R(5.0, -1.6)
    ell(f.b, hx, hy, 2.7, 2.5, INDIGO_L, bias=0.15)
    a = math.radians(tilt)
    M = lambda ox, oy: (hx + ox * math.cos(a) - oy * math.sin(a), hy + ox * math.sin(a) + oy * math.cos(a))
    polyline(f.b, [M(2.0, 1.0), M(3.6, 0.6 - jaw), M(4.4, 1.8 - jaw * 0.4)], "τ")
    polyline(f.b, [M(1.8, 1.8), M(3.2, 2.8 + jaw), M(3.8, 2.0 + jaw * 0.5)], "ς")
    f.pts["mouth"] = M(3.4, 1.4)
    polyline(f.b, [M(-1.0, -1.8), M(-0.4, -3.4), M(1.2, -4.4)], "κ")                  # crest
    polyline(f.b, [M(0.8, -2.0), M(2.6, -4.6), M(5.4, -5.6), M(6.8, -4.6), M(6.4, -3.4)], "ς")
    if eye != "dead":
        e = "L" if eye == "wide" else ("J" if eye == "open" else "D")
        for (ox, oy, ch) in ((0.3, -0.8, e), (1.1, -0.6, "Q"), (0.3, 0.2, "D")):
            f.g.put(*P(*M(ox, oy)), ch)
    else:
        f.g.put(*P(*M(0.3, -0.8)), "θ")
    # wings: four burnt-orange wings raised high (the hornet's smoky pairs, grown and coloured)
    root = R(-0.4, -2.4)
    angs = [-96, -118, -142, -114][wph % 4]
    wing(f.g, (root[0] - 0.8, root[1] + 0.3), angs - 24 + tilt * 0.3, 8.6, 2.4, wph + 1, cols=ORANGE_W)
    wing(f.g, root, angs + tilt * 0.3, 11.0, 3.2, wph, cols=ORANGE_W)
    for s_ in range(streak):
        y = cy - 2 + s_ * 3
        line(f.g, cx - 9 - s_ * 2, y - 2 + s_, cx - 14 - s_ * 2, y - 4 + s_, "τ" if s_ % 2 else "ς", over=False)
    if blur:
        rnd = random.Random(blur * 11)
        for k in range(14):
            x = cx + rnd.uniform(-10, 10); y = cy + rnd.uniform(-10, 12)
            line(f.g, x, y, x - 3, y, "ςτ"[k % 2], over=False)
    if extra: extra(f, (hx, hy), st1)
    return f.done()


def hunter_corpse():
    f = Fr()
    ell(f.b, -5.0, -2.0, 5.6, 2.2, INDIGO, shader=lambda nu, nv, d, l, ch, X, Y: pick("ρς", l) if int((nu + 1) * 3) == 4 else pick(INDIGO_L, l))
    line(f.b, 0.6, -2, 1.6, -2, "ι")
    ell(f.b, 3.6, -2.2, 3.0, 2.2, INDIGO_L)
    ell(f.b, 7.6, -2.0, 2.3, 2.0, INDIGO_L)
    line(f.b, -10.6, -1.6, -13.6, -1.0, "π")
    for x in (2.0, 3.4, 4.8):
        polyline(f.b, [(x, -3.8), (x - 0.5, -7), (x + 1, -9)], "κο")
    wing(f.g, (2.6, -3.8), -166, 10.0, 2.2, cols=ORANGE_W)
    f.g.put(8, -2, "θ")
    return f.done()


def build_hunter(outdir):
    H_ = hunter
    idle = [H_(wph=i, dy=[0, -0.8, -1.2, -0.5][i], legs=i * 0.7, curl=0.06 * (i % 2)) for i in range(4)]
    run = [H_(wph=i % 4, dy=-0.5 * math.sin(i * math.pi / 3), tilt=12, legs=i, curl=0.1, cage=0.6) for i in range(6)]

    def jab(n):
        def fn(f, head, st):
            for j in range(n):
                f.g.put(*P(st[0] + 1 + j, st[1] + (j % 2) - 0.5), "τ" if j % 2 else "π")
        return fn
    # LANCE: draw the abdomen back, wings up, CURL and THRUST the lance forward (hit far ahead), hold, recover
    lan = [H_(wph=0, curl=0.0, tilt=-8, dx=-0.6, eye="wide", cage=0.4),
           H_(wph=1, curl=-0.3, tilt=-14, dx=-1.6, dy=-1.0, eye="wide", cage=0.8),
           H_(wph=2, curl=1.0, tilt=6, dx=1.4, dy=-1.0, eye="wide", lance=0.6),
           H_(wph=3, curl=1.25, tilt=10, dx=2.4, dy=-1.2, eye="squint", lance=1.0, extra=jab(4)),
           H_(wph=0, curl=1.1, tilt=6, dx=1.8, dy=-0.8, lance=0.8, extra=jab(2)),
           H_(wph=1, curl=0.5, tilt=0, dx=0.6, lance=0.2),
           H_(wph=2, curl=0.1)]
    # HUNT: wings flare, then a blur of orange (it blinks round the hero three times), the lance out, recover
    hunt = [H_(wph=0, curl=0.3, tilt=-6, eye="wide", cage=0.6),
            H_(wph=2, curl=0.5, tilt=-12, dx=-1.0, dy=-1.6, eye="wide", cage=1.0, streak=1),
            H_(wph=1, curl=1.0, tilt=14, dx=1.6, lance=0.8, blur=1, streak=2, eye="wide"),
            H_(wph=3, curl=1.2, tilt=-10, dx=-1.0, lance=1.0, blur=2, streak=2, eye="wide"),
            H_(wph=1, curl=1.0, tilt=16, dx=1.8, lance=0.8, blur=3, streak=2, eye="wide"),
            H_(wph=3, curl=1.2, tilt=8, dx=1.0, lance=1.0, blur=4, streak=1, eye="squint", extra=jab(3)),
            H_(wph=0, curl=0.6, tilt=2, dx=0.4, lance=0.3),
            H_(wph=1, curl=0.1)]
    death = [H_(wph=1, tilt=-30, curl=0.6, eye="wide", dy=-1),
             H_(wph=3, tilt=-70, curl=0.2, eye="dead", dy=4.0),
             grounded(H_(wph=2, tilt=-150, curl=0.0, eye="dead")),
             hunter_corpse()]
    knock = H_(wph=2, tilt=-22, curl=0.5, dx=-1, eye="squint")
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6),
             ("Lance", lan, [0.12, 0.14, 0.06, 0.06, 0.12, 0.12, 0.12]),
             ("Hunt", hunt, [0.12, 0.16, 0.16, 0.16, 0.16, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkHunter", "Lance", lan, "sting"); note("ZhkHunter", "Hunt", hunt, "sting")
    sheet("ZhkHunter", anims, outdir, scale=5)


# ------------------------------------------------------------------ ACID BLOATER (T3, Acid Spitter line; flier)
# The spitter's acid sac swelled until it lifted the spitter off the floor: a vast floating gas-bladder of stretched
# chitin plates and glowing acid seams, with the spitter's pale grub-flesh body, spout head and limp legs hanging
# under it, and tiny buzzing wings on its flanks. A green balloon where its sibling the Brood Mother drags her bulk.
def bloater(dx=0.0, dy=0.0, tilt=0.0, sac=1.0, ph=0, legs=0.0, spout=20.0, eye="open", glow=1.0, wph=0, extra=None,
            jaw=0.0, bubble=0.0, lift=0.0):
    f = Fr()
    cx, cy = dx, dy - 27.0 - lift
    piv = (cx, cy + 6)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # hanging body: the spitter's grub-flesh thorax under the sac, a short segmented tail
    bx, by = R(3.4, 10.4)
    # limp dangling legs (far set in shadow)
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx) in enumerate(((-1.6, -4.4), (0.6, 0.0), (2.6, 4.6))):
            sw = math.sin(legs + j * 1.9 + side) * 1.0
            hp = (bx + hx - (0 if side else 0.7), by + 1.6)
            kn = (hp[0] + fx * 0.4 + sw * 0.3, hp[1] + 3.0)
            ft = (hp[0] + fx * 0.7 + sw - (0 if side else 0.8), hp[1] + 5.6)
            line(cv_, hp[0], hp[1], kn[0], kn[1], "3" if side else "1")
            line(cv_, kn[0], kn[1], ft[0], ft[1], "4" if side else "2")
            if side: cv_.put(*P(*kn), "5")
    tube2(f.b, [R(-4.6, 8.4), R(-1.6, 10.0), (bx, by)], [1.2, 2.2, 3.0],
          lambda s, ox, oy, r, l: "f" if (s * 2.0) % 1.0 < 0.2 else pick(GRUB, l + 0.1))
    for k in range(3): f.g.put(*P(bx - 3.6 + k * 1.8, by + 0.6), "Q" if glow > 0.5 else "D")      # acid spiracles
    # head with the spout (the spitter's)
    hx, hy = R(8.0, 9.6)
    ell(f.b, hx, hy, 2.6, 2.3, "2345", bias=0.0)
    ta = math.radians(spout + tilt)
    t0 = (hx + 1.8 * math.cos(ta), hy + 1.8 * math.sin(ta) + 0.4)
    t1 = (t0[0] + 3.4 * math.cos(ta), t0[1] + 3.4 * math.sin(ta))
    tube(f.b, [t0, t1], [1.2, 0.9 + jaw * 0.6], "2345")
    f.b.put(*P(*t1), "1")
    f.g.put(*P(t1[0] + 0.5 * math.cos(ta), t1[1] + 0.5 * math.sin(ta)), "Q" if glow > 0.5 else "D")
    f.pts["mouth"] = (t1[0] + 1.0 * math.cos(ta), t1[1] + 1.0 * math.sin(ta))
    if bubble > 0:
        m = f.pts["mouth"]; r = 0.8 + bubble * 2.2
        ell(f.g, m[0] + r * 0.8 * math.cos(ta), m[1] + r * 0.8 * math.sin(ta), r, r, "DQJ", bias=0.3)
        f.g.put(*P(m[0] + r * 0.8 * math.cos(ta) - r * 0.4, m[1] + r * 0.8 * math.sin(ta) - r * 0.5), "L")
    if eye != "dead":
        for (a, b, ch) in ((0.6, -1.2, "J"), (1.6, -0.8, "Q"), (-0.4, -1.4, "Q")):
            f.g.put(*P(hx + a, hy + b), "L" if eye == "wide" and ch == "J" else (ch if eye != "squint" else "D"))
    else:
        f.g.put(*P(hx + 0.6, hy - 1.2), "1")
    # the great floating sac (the spitter's acid sac), veined, a chitin cradle along its belly
    sx, sy = R(0.0, -1.0)
    rx, ry = 11.4 * sac ** 0.5, 9.6 * sac
    seam = 0.2 + 0.12 * max(0.0, sac - 1.0) * 3
    def bl(nu, nv, d, l, ch, X, Y):
        if nv > 0.78: return pick("1123", l + 0.2)                             # chitin cradle along the belly
        # the spitter's sac plates, stretched apart into a net of small plates over the glowing acid
        u = math.asin(max(-1.0, min(1.0, nu))) * 2.2 + 3.0 + 0.4 * (int(math.asin(max(-1.0, min(1.0, nv))) * 2.0 + 3) % 2)
        v = math.asin(max(-1.0, min(1.0, nv))) * 2.0 + 3.0
        fu, fv = u - math.floor(u), v - math.floor(v)
        if fu < seam or fv < seam * 0.8:
            if l > 0.45 and d < 0.7: return "J" if glow > 0.9 else "Q"
            return pick("dDQ", l + 0.3 * glow)
        if l > 0.6 and fu > 0.45 and fv > 0.45: return "5"
        return pick("1234", l + 0.1)
    ell(f.b, sx, sy, rx, ry, ACID, ang=tilt - 6, bias=0.0, shader=bl)
    rnd = random.Random(ph * 5 + 1)
    for _ in range(4):
        q = (sx + rnd.uniform(-0.6, 0.6) * rx, sy + rnd.uniform(-0.5, 0.5) * ry - (ph % 3))
        if f.b.px.get(P(*q)) in ("d", "D", "Q", "J"): f.g.put(*P(*q), "L")
    for k in range(4):                                                                       # tethering veins
        a = math.radians(40 + k * 28)
        line(f.b, sx + rx * 0.55 * math.cos(a), sy + ry * 0.55 * math.sin(a), sx + rx * 0.92 * math.cos(a), sy + ry * 0.92 * math.sin(a), "d", over=False)
    f.pts["sac"] = (sx, sy - ry)
    # tiny buzzing wings on the flanks (the spitter's pale wings)
    for (ox, oy, a0) in ((-8.0, -3.0, -150), (6.0, -6.0, -40)):
        wr = R(ox, oy)
        wing(f.g, wr, a0 + (wph % 2) * 18 + tilt, 5.4, 1.8, wph)
    if extra: extra(f, (hx, hy), f.pts["mouth"])
    return f.done()


def bloater_corpse():
    f = Fr()
    for x in range(-13, 12):
        if (x * 7) % 5: f.n.put(x, 0, "D" if x % 3 else "Q")
    ell(f.b, -2.0, -3.4, 10.0, 3.4, ACID, shader=lambda nu, nv, d, l, ch, X, Y: pick("1234", l) if int((nu + 1) * 3) % 2 and nv < 0 else pick("dDQ", l))
    tube(f.b, [(5.0, -1.6), (9.0, -1.8)], [1.8, 2.2], GRUB, bias=0.1)
    ell(f.b, 11.4, -2.0, 2.2, 1.9, "2345")
    for (x0, x1) in ((-6, -9), (0, 1), (5, 8)):
        polyline(f.b, [(x0, -6), ((x0 + x1) / 2, -8), (x1, -7)], "34")
    f.g.put(-4, -5, "J"); f.g.put(2, -4, "L"); f.g.put(11, -2, "1")
    return f.done()


def build_bloater(outdir):
    B_ = bloater
    idle = [B_(sac=1.0, ph=0, wph=0), B_(sac=1.03, ph=1, wph=1, lift=0.6, legs=0.4), B_(sac=1.06, ph=2, wph=0, lift=1.0, legs=0.8, glow=1.2),
            B_(sac=1.03, ph=3, wph=1, lift=0.5, legs=1.2, eye="squint")]
    run = [B_(sac=1.0 + 0.03 * math.cos(i * math.pi / 3), ph=i, wph=i % 2, tilt=6, lift=0.6 * math.sin(i * math.pi / 3),
              legs=i * 0.9, spout=26) for i in range(6)]
    # BLOW: the sac squeezes, spout up, a bubble swells at the spout, RELEASE, the sac sags, recover
    blow = [B_(sac=1.06, ph=0, spout=0, glow=1.1),
            B_(sac=0.98, ph=1, spout=-10, tilt=-4, glow=1.3, eye="wide", bubble=0.3),
            B_(sac=0.92, ph=2, spout=-14, tilt=-6, glow=1.4, eye="wide", bubble=0.7, jaw=0.6),
            B_(sac=0.88, ph=3, spout=-16, tilt=-6, glow=1.5, eye="wide", bubble=1.0, jaw=1.0),
            B_(sac=0.9, ph=4, spout=-4, tilt=2, glow=0.8, jaw=0.6),
            B_(sac=0.95, ph=5, spout=10, glow=0.9),
            B_(sac=1.0, ph=6, spout=20)]
    # INFLATE: it gulps air, the sac swells huge and its seams blaze (damage reduction), holds, settles
    def blaze(n):
        def fn(f, head, m):
            sx, sy = f.pts["sac"]
            for k in range(n):
                a = k * 2 * math.pi / n
                f.g.put(*P(sx + 13 * math.cos(a), sy + 10 + 11 * math.sin(a)), "J" if k % 2 else "Q", over=False)
        return fn
    infl = [B_(sac=1.0, ph=0, eye="squint", spout=40),
            B_(sac=1.12, ph=1, eye="squint", spout=50, glow=1.3, lift=0.6),
            B_(sac=1.24, ph=2, eye="wide", spout=56, glow=1.6, lift=1.2, extra=blaze(6)),
            B_(sac=1.3, ph=3, eye="wide", spout=58, glow=1.8, lift=1.6, extra=blaze(10)),
            B_(sac=1.3, ph=4, eye="wide", spout=56, glow=1.6, lift=1.6, extra=blaze(8)),
            B_(sac=1.26, ph=5, spout=50, glow=1.4, lift=1.2),
            B_(sac=1.16, ph=6, spout=34, glow=1.2, lift=0.6),
            B_(sac=1.06, ph=7, spout=24)]
    death = [B_(sac=1.3, glow=1.8, eye="wide", spout=-30, tilt=-8),
             B_(sac=0.7, glow=0.5, eye="dead", spout=60, tilt=10, lift=-8.0),
             grounded(B_(sac=0.45, glow=0.3, eye="dead", spout=70, tilt=14)),
             bloater_corpse()]
    knock = B_(sac=1.05, tilt=-10, dx=-1, eye="squint", spout=0)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.1] * 6),
             ("Blow", blow, [0.12, 0.14, 0.14, 0.12, 0.06, 0.12, 0.14]),
             ("Inflate", infl, [0.12, 0.12, 0.12, 0.14, 0.14, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.14, 0.4], knock)
    note("ZhkBloater", "Blow", blow, "mouth"); note("ZhkBloater", "Inflate", infl, "sac")
    sheet("ZhkBloater", anims, outdir, scale=5)


# ------------------------------------------------------------------ PIT ANTLION (T3, Hive Soldier line)
# The soldier gone to ground: its sickle mandibles grown into a pair of huge toothed jaws, its scythe arms shrunk to
# digging rakes, and its pale ringed gaster swollen into a fat, bristly, dust-coloured abdomen (the acid spiracles
# still glowing along it). Low and wide, all jaws, where its sibling the Acid Mantis is tall and thin.
def antlion(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, jaw=0.3, eye="open", sink=0.0, head=0.0, swell=0.0, dirt=0, rake=0.0,
            extra=None, smear=None, mound=0.0):
    f = Fr()
    oy = dy + sink
    cx, cy = dx, oy - 9.0
    piv = (cx, cy + 4)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    if mound > 0:                                                     # a sand rim round it as it sinks
        ell(f.n, dx + 1.0, 0.6, 15.0 + mound * 3, 2.0 + mound * 2.2, "ΣΦΧ", vmax=0.0, bias=0.1)
    # four splayed digging legs (near two outlined, far two shadowed)
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx) in enumerate(((-2.0, -9.0), (1.2, 7.0))):
            pha = legs + j * 2.6 + side * math.pi
            hp = R(hx - (0 if side else 1.0), 2.6)
            ft = (dx + fx + 1.4 * math.sin(pha) - (0 if side else 1.4), oy - max(0.0, 1.2 * math.cos(pha)))
            leg(cv_, hp, ft, 4.4, 4.8, -1 if ft[0] < hp[0] else 1, cols=("3", "4") if side else ("1", "2"), knee_hi="5" if side else None)
            for k in (-1, 1): cv_.put(*P(ft[0] + k, ft[1]), "Φ" if side else "Σ")       # bristly feet
    # the abdomen: the soldier's ringed gaster, swollen, bristly, dust-coloured, acid spiracles along it
    ax, ay = R(-8.6, 0.6)
    arx, ary = 8.6 + swell, 7.0 + swell * 0.8
    def ash(nu, nv, d, l, ch, X, Y):
        b = (nu + 1.0) * 2.8 + 0.4
        if (b - math.floor(b)) < 0.14 and d < 0.92: return "Σ"                             # ring crease
        n = ((X * 5 + Y * 11) * 2654435761 >> 6) % 9
        if n == 0 and nv < 0.4: return "1"                                                  # dark speckle
        if d > 0.84 and n in (2, 5) and nv < 0.3: return None                               # bristly edge
        if nv > 0.6: return pick("ΣΦ", l + 0.3)
        return pick(SAND, l + 0.12)
    ell(f.b, ax, ay, arx, ary, SAND, ang=tilt - 6, bias=0.05, shader=ash)
    for k in range(4):
        f.g.put(*P(ax - 6.0 + k * 3.6, ay + 2.2 - abs(k - 1.5) * 0.4), "Q" if eye != "dead" else "d")
    for k in range(7):                                                                      # bristles
        a = math.radians(-160 + k * 22)
        p0 = (ax + arx * math.cos(a), ay + ary * math.sin(a))
        line(f.b, p0[0], p0[1], p0[0] + 1.6 * math.cos(a), p0[1] + 1.6 * math.sin(a), "Χ")
    # thorax: the soldier's dark chitin, short and broad
    tx, ty = R(0.6, -0.6)
    ell(f.b, tx, ty, 4.4, 3.8, "1234", ang=tilt, bias=0.12)
    f.b.put(*P(tx - 1.6, ty - 2.6), "5")
    # rake arms: the soldier's scythes, shrunk to digging rakes (amber edged)
    for k, (a1, a2) in enumerate(((60 + rake * 40, 120 + rake * 30), (40 + rake * 50, 100 + rake * 40))):
        sh = R(3.0 - k * 1.6, 1.4)
        el = (sh[0] + 3.4 * math.cos(math.radians(a1 - 90)), sh[1] + 3.4 * math.sin(math.radians(a1 - 90)) + 2)
        tp = (el[0] + 3.4 * math.cos(math.radians(a2 - 90)), el[1] + 3.4 * math.sin(math.radians(a2 - 90)))
        cv_ = f.b if k == 0 else f.u
        line(cv_, sh[0], sh[1], el[0], el[1], "3"); line(cv_, el[0], el[1], tp[0], tp[1], "8"); cv_.put(*P(*tp), "9")
    # head: flat and wide, low; the great jaws
    hx, hy = R(7.0, 0.2 + head)
    ell(f.b, hx, hy, 3.6, 2.8, "1234", ang=tilt, bias=0.15)
    f.b.put(*P(hx - 1.4, hy - 2.0), "5")
    a = math.radians(tilt)
    M = lambda ox, oy_: (hx + ox * math.cos(a) - oy_ * math.sin(a), hy + ox * math.sin(a) + oy_ * math.cos(a))
    # each jaw: a long curved sickle (dark spine, amber toothed inner edge) opening by jaw
    def jaw_pts(sgn):
        o = jaw * 1.0
        return [M(2.4, sgn * 0.8), M(6.0, sgn * (1.0 + o * 3.4)), M(10.0, sgn * (0.6 + o * 4.6)), M(12.6, sgn * (0.2 + o * 4.0)),
                M(13.2, sgn * (-0.6 + o * 2.4))]
    for sgn, cv_ in ((-1, f.u), (1, f.b)):
        pts = jaw_pts(sgn)
        tube(cv_, pts[:4], [1.1, 0.9, 0.7, 0.5], "2344")
        polyline(cv_, pts[3:], "4")
        for t in range(1, 4):                                                               # teeth on the inner edge
            q = pts[t]
            cv_.put(*P(q[0], q[1] - sgn * 1.4), "8" if t % 2 else "9")
        cv_.put(*P(*pts[-1]), "9")
    f.pts["mouth"] = M(11.0, 0.2)
    polyline(f.b, [M(0.6, -2.4), M(1.6, -4.4), M(3.6, -5.0)], "2")
    if eye != "dead":
        f.g.put(*P(*M(1.0, -1.2)), "L" if eye == "wide" else ("J" if eye == "open" else "D"))
        f.g.put(*P(*M(0.0, -1.4)), "Q" if eye != "squint" else "D")
    else:
        f.g.put(*P(*M(1.0, -1.2)), "1")
    if smear:
        for k in range(10):
            t = k / 9.0
            ang = math.radians(smear[0] + (smear[1] - smear[0]) * t)
            q = M(4.0 + 8.0 * math.cos(ang), 8.0 * math.sin(ang))
            f.g.put(*P(*q), "E" if k % 2 else "9", over=False)
    if dirt:
        rnd = random.Random(dirt * 17)
        for k in range(6 + dirt * 3):
            x = dx + rnd.uniform(-14, 14); y = -rnd.uniform(1, 3 + dirt * 2.5)
            f.g.put(*P(x, y), "ΦΧΛΣ"[k % 4])
    if extra: extra(f, (hx, hy), M)
    spr = f.done()
    return spr


def antlion_corpse():
    f = Fr()
    ell(f.b, -7.0, -3.4, 8.6, 3.4, SAND, bias=0.05,
        shader=lambda nu, nv, d, l, ch, X, Y: "Σ" if ((nu + 1) * 2.8) % 1.0 < 0.14 else pick(SAND, l + 0.1))
    ell(f.b, 3.0, -2.6, 3.6, 2.6, "1234")
    ell(f.b, 8.0, -2.0, 3.0, 2.0, "1234")
    for sgn in (-1, 1):
        polyline(f.b, [(10, -2), (14, -2 + sgn * 3), (17, -2 + sgn * 2), (18, -2)], "4")
    for (x0, x1) in ((0.0, -3.0), (4.0, 7.0)):
        polyline(f.b, [(x0, -5), ((x0 + x1) / 2, -8), (x1, -9)], "34")
    f.g.put(-5, -3, "d"); f.g.put(8, -3, "1")
    return f.done()


def build_antlion(outdir):
    A_ = antlion
    idle = [A_(jaw=0.62), A_(jaw=0.7, dy=0.3, legs=0.2, swell=0.2), A_(jaw=0.78, dy=0.4, legs=0.3, swell=0.35, eye="squint"),
            A_(jaw=0.68, dy=0.2, legs=0.1, swell=0.15)]
    run = [A_(legs=i * math.pi / 3 + math.pi / 6, dy=-0.5 * abs(math.sin(i * math.pi / 3 + math.pi / 6)), tilt=-2 + 1.5 * math.sin(i),
              jaw=0.6 + 0.1 * (i % 2), rake=0.3 * math.sin(i * math.pi / 3), swell=0.2 * math.cos(i * math.pi / 3)) for i in range(6)]
    # CLAMP: jaws gape, lunge, SNAP (hit), shake, let go, recover
    clamp = [A_(jaw=0.9, tilt=-4, dx=-0.6, eye="wide", head=-0.6),
             A_(jaw=1.3, tilt=-8, dx=-1.4, eye="wide", head=-1.0, swell=0.3),
             A_(jaw=1.4, tilt=4, dx=2.0, eye="wide"),
             A_(jaw=0.0, tilt=6, dx=3.0, eye="squint", smear=(-80, 80)),
             A_(jaw=0.05, tilt=-3, dx=2.6, eye="squint", dirt=1),
             A_(jaw=0.5, tilt=0, dx=1.2),
             A_(jaw=0.35, dx=0.4)]
    # PIT: rake the sand, sink into a funnel (the pit drags the hero in), jaws open in wait, SNAP, climb out
    pit = [A_(jaw=0.5, rake=1.0, dirt=1, tilt=6),
           A_(jaw=0.6, rake=-0.6, dirt=2, sink=2.0, tilt=8, mound=0.3),
           A_(jaw=0.9, rake=1.0, dirt=3, sink=4.0, tilt=6, mound=0.7, eye="wide"),
           A_(jaw=1.3, rake=-0.6, dirt=2, sink=5.0, tilt=2, mound=1.0, eye="wide"),
           A_(jaw=1.4, rake=1.0, dirt=3, sink=5.0, tilt=0, mound=1.0, eye="wide"),
           A_(jaw=1.4, rake=-0.6, dirt=2, sink=5.0, tilt=-2, mound=1.0, eye="wide"),
           A_(jaw=0.0, dirt=4, sink=3.6, tilt=6, mound=0.8, eye="squint", smear=(-80, 80)),
           A_(jaw=0.4, dirt=1, sink=1.0, mound=0.3),
           A_(jaw=0.3)]
    pit = [Spr({k: v for k, v in fr.px.items() if k[1] <= 0}) for fr in pit]
    death = [A_(jaw=1.4, tilt=-12, eye="wide", head=-1.0, swell=0.6),
             A_(jaw=0.8, tilt=-20, eye="dead", dy=0.5, legs=2.0, swell=0.2),
             grounded(A_(jaw=0.5, tilt=-160, eye="dead", legs=2.5)),
             antlion_corpse()]
    knock = A_(jaw=1.0, tilt=-10, eye="squint", dx=-0.8, head=-0.6)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.08] * 6),
             ("Clamp", clamp, [0.14, 0.14, 0.07, 0.06, 0.12, 0.12, 0.12]),
             ("Pit", pit, [0.12, 0.12, 0.14, 0.16, 0.16, 0.16, 0.08, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkAntlion", "Clamp", clamp, "mouth"); note("ZhkAntlion", "Pit", pit, "mouth")
    sheet("ZhkAntlion", anims, outdir, scale=5, remap=LIFT)


# ------------------------------------------------------------------ GLUE MORTAR (T3, Nasute line)
# The nasute's head grown into a siege mortar: a vast dark bulb whose nozzle has become a wide, banded barrel aimed
# at the sky, glue drooling from its lip; the amber glue sacs swollen into a cluster of three hooped tanks; the beetle
# dome on its back now a rack of resin shells. Squat and heavy where its sibling the Colossus is a charging horn.
def mortar(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, aim=-58.0, recoil=0.0, squeeze=0.0, eye="open", glow=0.0, shells=3, drip=1,
           crouch=0.0, smoke=0, extra=None):
    f = Fr()
    cx, cy = dx, dy - 11.0 + crouch * 1.6
    piv = (cx, cy + 4)
    R = lambda x, y: rot((cx + x, cy + y), piv, tilt)
    # six stubby legs, braced wide
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, (hx, fx) in enumerate(((-6.0, -13.0), (-0.6, -1.0), (4.4, 10.0))):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(hx - (0 if side else 1.0), 4.0)
            ft = (dx + fx + 1.2 * math.sin(pha) - (0 if side else 1.2), -max(0.0, 1.2 * math.cos(pha)))
            if side:
                knee, end = ik(hp[0], hp[1], ft[0], ft[1], 4.6, 5.0, -1 if ft[0] < hp[0] else 1)
                tube(cv_, [hp, knee], [1.4, 1.1], "2345"); tube(cv_, [knee, end], [1.1, 0.7], "1234")
            else:
                leg(cv_, hp, ft, 4.6, 5.0, -1 if ft[0] < hp[0] else 1, cols=("1", "2"), knee_hi=None)
    # three hooped amber glue tanks (the nasute's sacs) behind
    for k, (ox, oy, r) in enumerate(((-11.0, 0.6, 4.6), (-7.0, -3.6, 5.0), (-4.0, 1.6, 4.4))):
        q = R(ox, oy)
        rr = r * (1.0 - 0.12 * squeeze)
        def ts(nu, nv, d, l, ch, X, Y, q=q):
            if abs(nu + 0.15 * nv) < 0.1 or abs(nu - 0.55 + 0.1 * nv) < 0.08: return pick("12", l)     # chitin hoops
            if l > 0.7 and d < 0.35: return "E"
            if nv > 0.55: return pick("67", l + 0.3)
            return pick("789", l + 0.15 + 0.2 * glow)
        ell(f.b, q[0], q[1], rr, rr * 0.92, AMB_L, ang=tilt, shader=ts)
    # the body + the beetle's dome, now a rack of resin shells
    resin_shell(f.b, f.g, *R(-1.2, -3.0), 5.0, 3.6, ang=tilt, beads=0)
    for k in range(shells):
        q = R(-4.0 + k * 2.6, -6.4 - (1 if k == 1 else 0))
        ell(f.b, q[0], q[1], 1.2, 1.5, AMB_L, bias=0.35)
        f.g.put(*P(q[0] - 0.4, q[1] - 0.8), "E")
    # the head: the nasute's dark bulb, huge, with its own rim
    hx, hy = R(5.6 - recoil * 1.2, -3.2 + recoil * 0.6)
    stamp_c = Canvas()
    ell(stamp_c, hx, hy, 6.2, 5.8, "1234", ang=tilt, bias=0.3,
        shader=lambda nu, nv, d, l, ch, X, Y: "5" if (l > 0.7 and d < 0.35) else pick("23345", l))
    for k_, v_ in outl(Spr(stamp_c.px), "0").px.items(): f.b.put(k_[0], k_[1], v_)
    polyline(f.b, [(hx - 3.6, hy - 1.8), (hx - 1.0, hy - 4.2), (hx + 2.2, hy - 3.8)], "6")
    # the barrel: wide and banded, a flared muzzle, aimed up by aim (deg)
    na = math.radians(aim + tilt)
    n0 = (hx + 3.6 * math.cos(na), hy + 3.6 * math.sin(na))
    blen = 7.6 - recoil * 1.6
    n1 = (n0[0] + blen * math.cos(na), n0[1] + blen * math.sin(na))
    tube(f.b, [n0, n1], [3.0, 2.4], "1234", bias=0.15)
    nx, ny = -math.sin(na), math.cos(na)
    for t in (0.25, 0.6):                                                      # amber reinforcing bands
        q = (n0[0] + (n1[0] - n0[0]) * t, n0[1] + (n1[1] - n0[1]) * t)
        line(f.b, q[0] - nx * 2.6, q[1] - ny * 2.6, q[0] + nx * 2.6, q[1] + ny * 2.6, "7")
    line(f.b, n1[0] - nx * 3.4, n1[1] - ny * 3.4, n1[0] + nx * 3.4, n1[1] + ny * 3.4, "3")        # muzzle lip
    line(f.b, n1[0] - nx * 3.4 + math.cos(na), n1[1] - ny * 3.4 + math.sin(na), n1[0] + nx * 3.4 + math.cos(na), n1[1] + ny * 3.4 + math.sin(na), "4")
    mz = (n1[0] + 1.4 * math.cos(na), n1[1] + 1.4 * math.sin(na))
    f.g.put(*P(*mz), "E" if glow > 0.5 else "8"); f.g.put(*P(mz[0] + nx, mz[1] + ny), "9")
    f.pts["muzzle"] = mz
    for k in range(drip):                                                      # glue drooling off the lip
        f.g.put(*P(n1[0] + nx * 3.0, n1[1] + ny * 3.0 + 1 + k), "8" if k < drip - 1 else "9")
    rnd = random.Random(smoke * 3 + 2)
    for k in range(smoke * 4):
        t = rnd.uniform(0.5, 2.5 + smoke)
        f.g.put(*P(mz[0] + t * math.cos(na) + rnd.uniform(-1.5, 1.5), mz[1] + t * math.sin(na) + rnd.uniform(-1.5, 1.5)), "9E8"[k % 3], over=False)
    # vestigial eyes: acid pores on the bulb
    if eye != "dead":
        f.g.put(*P(hx + 1.8, hy + 1.4), "Q" if eye != "wide" else "J")
        f.g.put(*P(hx - 2.0, hy + 0.6), "D" if eye == "squint" else "Q")
    if extra: extra(f, (hx, hy), mz)
    return f.done()


def mortar_corpse():
    f = Fr()
    for x in range(-14, 2):
        if (x * 5) % 3: f.n.put(x, 0, "7" if x % 2 else "8")
    for (x, r) in ((-10, 3.6), (-5, 4.0)):
        ell(f.b, x, -r * 0.7, r, r * 0.7, AMB_L, bias=0.2)
    ell(f.b, 2.0, -3.4, 5.6, 3.6, "1234", bias=0.2)
    tube(f.b, [(7.0, -2.0), (13.0, -1.6)], [2.4, 2.0], "1234")
    line(f.b, 13.4, -4.0, 13.4, 0.0, "3")
    for (x0, x1) in ((-3.0, -5.0), (0.0, 1.0), (3.0, 5.0)):
        polyline(f.b, [(x0, -6), ((x0 + x1) / 2, -9), (x1, -9.6)], "34")
    f.g.put(14, -2, "9")
    return f.done()


def build_mortar(outdir):
    M_ = mortar
    idle = [M_(), M_(dy=0.3, legs=0.2, squeeze=0.2, drip=2), M_(dy=0.4, legs=0.3, squeeze=0.35, eye="squint", drip=3),
            M_(dy=0.2, legs=0.1, squeeze=0.15, drip=1)]
    run = [M_(legs=i * math.pi / 3 + math.pi / 6, dy=-0.5 * abs(math.sin(i * math.pi / 3 + math.pi / 6)), tilt=1.5 * math.sin(i * math.pi / 3),
              aim=-48, drip=1 + i % 2) for i in range(6)]
    # LOB: tanks squeeze, the barrel tips up, FIRE (recoil, a glue shell leaves the muzzle), smoke, settle
    def shell_fx(h):
        def fn(f, head, mz):
            ell(f.g, mz[0] + 1.0, mz[1] - h, 1.6, 1.8, "789E", bias=0.4)
        return fn
    lob = [M_(aim=-62, squeeze=0.3, glow=0.3, crouch=0.3),
           M_(aim=-70, squeeze=0.7, glow=0.7, crouch=0.7, eye="wide"),
           M_(aim=-74, squeeze=1.0, glow=1.0, crouch=0.9, eye="wide", drip=0),
           M_(aim=-72, recoil=1.0, squeeze=0.0, glow=1.0, crouch=0.2, eye="wide", drip=0, smoke=2, shells=2, extra=shell_fx(3)),
           M_(aim=-66, recoil=0.5, glow=0.4, smoke=3, shells=2, drip=1),
           M_(aim=-62, recoil=0.2, smoke=1, shells=2, drip=2),
           M_(shells=3)]
    # BARRAGE: three shots, each with a squeeze and a recoil
    bar = [M_(aim=-64, squeeze=0.6, glow=0.5, crouch=0.5),
           M_(aim=-76, squeeze=1.0, glow=1.0, crouch=0.9, eye="wide", drip=0),
           M_(aim=-76, recoil=1.0, glow=1.0, eye="wide", smoke=2, shells=2, drip=0, extra=shell_fx(3)),
           M_(aim=-70, squeeze=0.8, glow=0.8, crouch=0.6, eye="wide", smoke=1, shells=2, drip=0),
           M_(aim=-66, recoil=1.0, glow=1.0, eye="wide", smoke=2, shells=1, drip=0, extra=shell_fx(3)),
           M_(aim=-80, squeeze=0.8, glow=0.8, crouch=0.6, eye="wide", smoke=1, shells=1, drip=0),
           M_(aim=-82, recoil=1.0, glow=1.0, eye="wide", smoke=3, shells=0, drip=0, extra=shell_fx(3)),
           M_(aim=-66, recoil=0.3, smoke=2, shells=0, drip=1),
           M_(shells=1, drip=2)]
    death = [M_(aim=-20, recoil=1.0, eye="wide", squeeze=1.0, glow=1.0),
             M_(aim=10, eye="dead", crouch=2.0, tilt=8, dy=0.5, legs=1.0),
             grounded(M_(aim=20, eye="dead", crouch=3.0, tilt=12, legs=2.0, shells=0)),
             mortar_corpse()]
    knock = M_(aim=-40, tilt=-10, eye="squint", dx=-0.8, squeeze=0.5)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.1] * 6),
             ("Lob", lob, [0.14, 0.14, 0.12, 0.06, 0.12, 0.12, 0.14]),
             ("Barrage", bar, [0.12, 0.12, 0.08, 0.12, 0.08, 0.12, 0.08, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.4], knock)
    note("ZhkMortar", "Lob", lob, "muzzle"); note("ZhkMortar", "Barrage", bar, "muzzle")
    sheet("ZhkMortar", anims, outdir, scale=5)


# ------------------------------------------------------------------ AMBER SCARAB (T2, Resin Beetle line)
# The resin beetle's dome grown jewel-teal and iridescent (the resin seam and amber beads still on it), a flat rake
# head, and the resin it used to spit now rolled into a big glossy amber ball it shoves ahead of itself. A green-blue
# shell and a gold ball, where its sibling the Nasute is pale glue sacs and a dark nozzle.
def amber_ball(c, g, x, y, r, rot_=0.0, glow=0.0, bugs=1):
    """A glossy ball of amber resin, lit from the top-left, a dark speck (a trapped insect) turning with rot_."""
    def sh(nu, nv, d, l, ch, X, Y):
        if l > 0.75 and d < 0.3: return "E"
        return pick("6789", l + 0.1 + 0.25 * glow)
    ell(c, x, y, r, r, AMB_L, bias=0.1, shader=sh)
    for k in range(bugs):
        a = rot_ + k * 2.4
        q = (x + r * 0.45 * math.cos(a), y + r * 0.45 * math.sin(a) * 0.8)
        c.put(*P(*q), "6"); c.put(*P(q[0] + 1, q[1]), "6")
    g.put(*P(x - r * 0.45, y - r * 0.5), "E")


def jewel_shell(c, x, y, rx, ry, ang=0.0, ramp=TEAL_L, seam="7", sheen="ψ", beads=2, g=None):
    """The scarab's elytra dome: iridescent, a bright sheen arc, the beetle's amber resin seam down the middle."""
    def sh(nu, nv, d, l, ch, X, Y):
        if nv > 0.6: return pick(ramp[:2], l)
        if 0.28 < d < 0.5 and -0.75 < nu < 0.1 and nv < -0.2: return sheen
        if abs(nu + nv * 0.35 - 0.15) < 0.1 and nv < 0.35: return seam
        return pick(ramp, l + 0.05)
    ell(c, x, y, rx, ry, ramp, ang=ang, bias=0.0, shader=sh, vmax=0.95)
    a = math.radians(ang)
    for k in range(beads):
        t = -0.4 + 0.8 * k / max(1, beads - 1)
        bx, by = x + t * rx * math.cos(a) - 0.4 * ry * math.sin(a), y + t * rx * math.sin(a) - 0.5 * ry
        ell(c, bx, by, 0.8, 0.7, AMB_L, bias=0.4)
        if g is not None: g.put(*P(bx - 0.3, by - 0.4), "E")


def scarab(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, ball=1.0, bx=0.0, rot_=0.0, jaw=0.2, eye="open", curl=0.0, extra=None,
           streak=0, lift=0.0):
    f = Fr()
    if curl > 0.5:                                                    # ROLL: tucked into a spinning shell
        r = 6.0
        cx, cy = dx, dy - r - 0.4
        def sh(nu, nv, d, l, ch, X, Y):
            ang = math.atan2(nv, nu) + rot_
            if abs(math.sin(ang * 1.0)) < 0.12 and d < 0.85: return "7"                  # the seam, turning
            if 0.3 < d < 0.55 and -0.8 < nu < 0.0 and nv < -0.2: return "ψ"
            return pick(TEAL_L, l + 0.05)
        ell(f.b, cx, cy, r + 0.6, r, TEAL_L, shader=sh)
        for k in range(3):
            a = rot_ + k * 2.1
            q = (cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a))
            ell(f.b, q[0], q[1], 0.8, 0.7, AMB_L, bias=0.4)
        for s_ in range(streak):
            line(f.g, cx - r - 2 - s_ * 2, cy - 2 + s_ * 2, cx - r - 6 - s_ * 2, cy - 2 + s_ * 2, "χ" if s_ % 2 else "φ", over=False)
        f.pts["mouth"] = (cx + r, cy)
        if extra: extra(f, (cx, cy), None)
        return f.done()
    cx, cy = dx - 3.0, dy - 5.6 - lift
    piv = (cx + 2, cy + 3)
    R = lambda x, y: rot((x, y), piv, tilt)
    hips = [(-3.0, 2.4), (0.0, 2.9), (3.0, 2.6)]
    feet = [(-8.0, 0), (-1.6, 0), (6.4, 0)]
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, ((hx, hy), (fx, fy)) in enumerate(zip(hips, feet)):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(cx + hx - (0 if side else 0.8), cy + hy)
            ft = (dx - 3 + fx + 1.0 * math.sin(pha) - (0 if side else 1.0), -max(0.0, 1.0 * math.cos(pha)))
            leg(cv_, hp, ft, 3.0, 3.2, -1 if fx < hx else 1, cols=("υ", "φ") if side else ("σ", "σ"), knee_hi="χ" if side else None)
            cv_.put(*P(ft[0] + 0.5, ft[1]), "φ" if side else "σ")
    ex, ey = R(cx, cy)
    jewel_shell(f.b, ex, ey, 6.2, 4.4, ang=tilt, g=f.g)
    px_, py_ = R(cx + 5.4, cy + 0.4)
    ell(f.b, px_, py_, 2.6, 2.5, TEAL, ang=tilt, bias=0.1)
    f.b.put(*P(px_ - 1, py_ - 1.4), "χ")
    # rake head: flat toothed clypeus
    hx, hy = R(cx + 7.6, cy + 1.6)
    ell(f.b, hx, hy, 2.0, 1.6, TEAL, bias=0.1)
    for k in range(3):
        f.b.put(*P(hx + 1.6 + k * 0.2, hy - 1.4 + k * 1.1), "χ")
    a = math.radians(tilt)
    M = lambda ox, oy: (hx + ox * math.cos(a) - oy * math.sin(a), hy + ox * math.sin(a) + oy * math.cos(a))
    if eye != "dead":
        f.g.put(*P(*M(0.2, -0.8)), "L" if eye == "wide" else ("J" if eye == "open" else "D"))
    else:
        f.g.put(*P(*M(0.2, -0.8)), "σ")
    f.pts["mouth"] = M(2.4, 0.6)
    # forelegs on the ball; the ball itself
    if ball > 0:
        r = 4.6 * ball
        bcx, bcy = dx + 9.6 + bx, dy - r - 0.2
        amber_ball(f.b, f.g, bcx, bcy, r, rot_=rot_)
        line(f.u, *M(0.6, 1.2), bcx - r * 0.7, bcy + r * 0.2, "υ")
        line(f.b, *M(0.8, 0.6), bcx - r * 0.8, bcy - r * 0.4, "φ")
        f.pts["ball"] = (bcx, bcy)
    if extra: extra(f, (hx, hy), M)
    return f.done()


def scarab_corpse():
    f = Fr()
    ell(f.b, -1.5, -2.6, 6.0, 2.6, TEAL_L, bias=0.0)
    ell(f.b, -1.0, -3.6, 4.4, 1.4, "φχ", bias=0.2)
    for j, x in enumerate((-4.0, -1.5, 1.2)):
        polyline(f.b, [(x, -5), (x - 1 + 2 * (j % 2), -7), (x + (1 if j % 2 else -1), -8)], "υφ")
    ell(f.b, 5.4, -1.8, 1.8, 1.5, TEAL)
    amber_ball(f.n, f.g, 10.0, -2.2, 2.2, rot_=1.0, bugs=0)
    f.g.put(5, -2, "σ")
    return f.done()


def build_scarab(outdir):
    S_ = scarab
    idle = [S_(rot_=0.0), S_(rot_=0.0, dy=0.3, legs=0.3, jaw=0.3), S_(rot_=0.0, dy=0.3, legs=0.5, eye="squint", bx=0.3),
            S_(rot_=0.0, legs=0.2, bx=0.1)]
    run = [S_(legs=i * math.pi / 3 + math.pi / 6, dy=-0.5 * abs(math.sin(i * math.pi / 3 + math.pi / 6)),
              tilt=-1.5 - 2 * math.sin(i * math.pi / 3 + math.pi / 6), rot_=i * 1.05, bx=0.3 * math.sin(i)) for i in range(6)]
    # BOWL: rear back, SHOVE (the ball rolls off: it is the projectile), then resin wells up into a new ball
    bowl = [S_(tilt=-6, dx=-1.0, bx=-0.6, eye="wide"),
            S_(tilt=-10, dx=-2.0, bx=-1.2, eye="wide", lift=0.4),
            S_(tilt=6, dx=1.4, bx=2.0, eye="wide"),
            S_(tilt=8, dx=2.0, ball=0.0, eye="squint"),
            S_(tilt=2, dx=1.0, ball=0.35),
            S_(tilt=0, dx=0.4, ball=0.7),
            S_(ball=1.0)]
    # ROLL: tuck the legs, curl into the shell, ROLL (spinning, ricocheting), uncurl
    roll = [S_(tilt=-8, lift=0.6, legs=1.0, eye="wide"),
            S_(tilt=-20, lift=1.6, ball=0.0, eye="wide"),
            S_(curl=1.0, rot_=0.0, ball=0.0, streak=1),
            S_(curl=1.0, rot_=1.0, ball=0.0, streak=2),
            S_(curl=1.0, rot_=2.0, ball=0.0, streak=2),
            S_(curl=1.0, rot_=3.0, ball=0.0, streak=2),
            S_(curl=1.0, rot_=4.0, ball=0.0, streak=1),
            S_(tilt=-10, lift=1.0, ball=0.4),
            S_(ball=0.8)]
    death = [S_(tilt=-14, eye="wide", dx=-0.5, legs=1.0, lift=0.6),
             S_(tilt=-34, eye="dead", dy=0.5, legs=2.0, ball=0.9, bx=2.0),
             grounded(S_(tilt=-150, eye="dead", legs=2.5, ball=0.0)),
             scarab_corpse()]
    knock = S_(tilt=-12, eye="squint", dx=-0.8, legs=0.8, lift=0.5)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.075] * 6),
             ("Bowl", bowl, [0.12, 0.14, 0.07, 0.08, 0.12, 0.12, 0.12]),
             ("Roll", roll, [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkScarab", "Bowl", bowl, "ball")
    sheet("ZhkScarab", anims, outdir, scale=6)


# ------------------------------------------------------------------ STAG TITAN (T3, Amber Scarab line)
# The scarab grown long and tall: the jewel dome gone violet with a teal sheen (the amber seam still down it), a
# broad pronotum, and in place of the rake head two vast branched mandibles, longer than its body, that grab and toss.
def stag(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, jaw=0.3, raise_=0.0, eye="open", head=0.0, extra=None, lift=0.0, smear=None):
    f = Fr()
    cx, cy = dx - 6.0, dy - 10.0 - lift
    piv = (cx + 4, cy + 4)
    R = lambda x, y: rot((x, y), piv, tilt)
    hips = [(-3.5, 3.6), (1.0, 4.2), (5.4, 3.8)]
    feet = [(-13.0, 0), (-4.0, 0), (8.0, 0)]
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, ((hx, hy), (fx, _)) in enumerate(zip(hips, feet)):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(cx + hx - (0 if side else 1.0), cy + hy)
            ft = (dx - 6 + fx + 1.4 * math.sin(pha) - (0 if side else 1.4), -max(0.0, 1.4 * math.cos(pha)))
            bend = -1 if fx < hx else 1
            if side:
                knee, end = ik(hp[0], hp[1], ft[0], ft[1], 5.6, 6.0, bend)
                tube(cv_, [hp, knee], [1.2, 0.9], "ωΩΨ"); line(cv_, knee[0], knee[1], end[0], end[1], "Ω")
                cv_.put(*P(*knee), "χ")
            else:
                leg(cv_, hp, ft, 5.6, 6.0, bend, cols=("ω", "ω"), knee_hi=None)
    ex, ey = R(cx - 1.0, cy)
    jewel_shell(f.b, ex, ey, 9.4, 6.0, ang=tilt, ramp=VIOLET, sheen="ψ", beads=3, g=f.g)
    px_, py_ = R(cx + 9.0, cy + 0.2)
    ell(f.b, px_, py_, 4.0, 3.6, VIOLET, ang=tilt, bias=0.1)
    f.b.put(*P(px_ - 1.6, py_ - 2.2), "ψ"); f.b.put(*P(px_ - 0.6, py_ - 2.6), "χ")
    hx, hy = R(cx + 13.0, cy + 0.6 + head)
    ell(f.b, hx, hy, 3.0, 2.6, VIOLET, bias=0.12)
    ha = math.radians(tilt - raise_)
    M = lambda ox, oy: (hx + ox * math.cos(ha) - oy * math.sin(ha), hy + ox * math.sin(ha) + oy * math.cos(ha))
    # mandibles: long antler-like curves with an inner tine and a forked tip, opening by jaw
    tips = []
    for sgn, cv_ in ((1, f.u), (-1, f.b)):
        o = jaw
        pts = [M(1.8, sgn * 0.8), M(5.4, sgn * (2.2 + o * 2.0) - 1.0), M(9.0, sgn * (2.6 + o * 3.0) - 1.6), M(11.8, sgn * (1.6 + o * 2.4) - 2.0)]
        tube(cv_, pts, [1.4, 1.2, 1.0, 0.7], "ωΩΨχ" if sgn < 0 else "ωωΩΨ", bias=0.1)
        t0 = pts[1]; cv_.put(*P(t0[0] + 0.6, t0[1] - sgn * 1.6), "Ψ"); cv_.put(*P(t0[0] + 1.2, t0[1] - sgn * 2.4), "ψ")   # inner tine
        fk = pts[3]
        cv_.put(*P(fk[0] + 1.0, fk[1] - 0.6), "ψ" if sgn < 0 else "Ψ"); cv_.put(*P(fk[0] + 0.4, fk[1] + 1.0), "Ψ")
        tips.append(fk)
    f.pts["mouth"] = ((tips[0][0] + tips[1][0]) / 2, (tips[0][1] + tips[1][1]) / 2)
    if eye != "dead":
        f.g.put(*P(*M(0.0, -1.4)), "L" if eye == "wide" else ("J" if eye == "open" else "D"))
        f.g.put(*P(*M(-1.0, -1.4)), "Q" if eye != "squint" else "D")
    else:
        f.g.put(*P(*M(0.0, -1.4)), "ω")
    polyline(f.b, [M(-0.6, -2.2), M(0.4, -4.4), M(2.0, -5.0)], "Ω")
    if smear:
        for k in range(12):
            t = k / 11.0
            ang = math.radians(smear[0] + (smear[1] - smear[0]) * t)
            q = (hx + 12.0 * math.cos(ang), hy + 12.0 * math.sin(ang))
            f.g.put(*P(*q), "ψ" if k % 2 else "χ", over=False)
    if extra: extra(f, (hx, hy), M)
    return f.done()


def stag_corpse():
    f = Fr()
    ell(f.b, -4.0, -3.4, 9.0, 3.4, VIOLET, bias=0.05)
    ell(f.b, -3.4, -4.6, 6.4, 1.6, "Ψχ", bias=0.2)
    for j, x in enumerate((-8.0, -4.0, 0.0)):
        polyline(f.b, [(x, -6.6), (x - 1 + 2 * (j % 2), -9), (x + (1 if j % 2 else -1), -10.4)], "ΩΨ")
    ell(f.b, 7.6, -2.4, 2.8, 2.2, VIOLET)
    polyline(f.b, [(9.6, -2.4), (14.0, -4.4), (18.0, -2.6)], "Ψ")
    polyline(f.b, [(9.6, -1.4), (13.6, 0.0), (17.6, -0.6)], "Ω")
    f.g.put(8, -3, "ω")
    return f.done()


def build_stag(outdir):
    S_ = stag
    idle = [S_(jaw=0.3), S_(jaw=0.36, dy=0.3, legs=0.2), S_(jaw=0.42, dy=0.4, legs=0.3, eye="squint", raise_=3),
            S_(jaw=0.34, dy=0.2, legs=0.1, raise_=1)]
    run = [S_(legs=i * math.pi / 3 + math.pi / 6, dy=-0.6 * abs(math.sin(i * math.pi / 3 + math.pi / 6)), tilt=-1.5 * math.sin(i * math.pi / 3),
              jaw=0.3, raise_=4 * math.sin(i * math.pi / 3)) for i in range(6)]
    # PINCH: jaws gape, lunge, SNAP shut (hit), hold, recover
    pinch = [S_(jaw=0.9, tilt=-4, dx=-0.8, raise_=8, eye="wide"),
             S_(jaw=1.3, tilt=-6, dx=-1.6, raise_=12, eye="wide"),
             S_(jaw=1.2, tilt=3, dx=1.6, raise_=-4, eye="wide"),
             S_(jaw=-0.2, tilt=5, dx=2.6, raise_=-6, eye="squint", smear=(-30, 30)),
             S_(jaw=-0.1, tilt=3, dx=2.0, raise_=-2, eye="squint"),
             S_(jaw=0.3, dx=0.6)]
    # TOSS: head down, jaws wide low, CLAMP (grab), heave up overhead, FLING back over its shoulders, settle
    toss = [S_(jaw=0.8, tilt=4, raise_=-14, head=1.0, eye="wide"),
            S_(jaw=1.3, tilt=6, raise_=-20, head=1.4, dx=1.0, eye="wide"),
            S_(jaw=-0.1, tilt=6, raise_=-18, head=1.4, dx=1.6, eye="squint"),
            S_(jaw=-0.1, tilt=-6, raise_=30, dx=0.6, eye="squint", lift=1.0),
            S_(jaw=-0.1, tilt=-12, raise_=70, dx=-0.4, eye="wide", lift=1.6),
            S_(jaw=0.9, tilt=-14, raise_=110, dx=-1.0, eye="wide", lift=1.2, smear=(-150, -60)),
            S_(jaw=0.6, tilt=-6, raise_=60, eye="wide"),
            S_(jaw=0.4, tilt=-2, raise_=20),
            S_(jaw=0.3)]
    death = [S_(jaw=1.2, tilt=-10, eye="wide", raise_=30, dx=-0.6),
             S_(jaw=0.6, tilt=-24, eye="dead", raise_=-10, dy=0.5, legs=2.0),
             grounded(S_(jaw=0.4, tilt=-150, eye="dead", legs=2.5)),
             stag_corpse()]
    knock = S_(jaw=0.9, tilt=-10, eye="squint", dx=-0.8, raise_=20)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.08] * 6),
             ("Pinch", pinch, [0.14, 0.14, 0.07, 0.06, 0.12, 0.14]),
             ("Toss", toss, [0.12, 0.12, 0.08, 0.1, 0.1, 0.08, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkStag", "Pinch", pinch, "mouth"); note("ZhkStag", "Toss", toss, "mouth")
    sheet("ZhkStag", anims, outdir, scale=5)


# ------------------------------------------------------------------ SUN SCARAB (T3, Amber Scarab line)
# The scarab made sacred: a round golden carapace edged in the old jewel teal, its rake head grown into a radiant
# crown of sun-ray spikes, and its amber ball swollen into a blazing sun-ball with a core of light and insects caught
# inside. Round and gold with a ball, where its sibling the Stag Titan is long, violet and all mandible.
GOLD = "oOYy"


def sunscarab(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, ball=1.0, bx=0.0, rot_=0.0, eye="open", glow=0.0, crown=1.0, rear=0.0,
              extra=None, smear=None):
    f = Fr()
    cx, cy = dx - 6.0, dy - 8.0 - rear * 3.0
    piv = (cx + 2, cy + 6)
    R = lambda x, y: rot((x, y), piv, tilt - rear * 18)
    hips = [(-4.0, 3.6), (0.0, 4.4), (4.0, 3.8)]
    feet = [(-11.0, 0), (-3.0, 0), (5.6, 0)]
    for side, cv_ in ((0, f.n), (1, f.u)):
        for j, ((hx, hy), (fx, _)) in enumerate(zip(hips, feet)):
            pha = legs + j * 2.1 + side * math.pi
            hp = R(cx + hx - (0 if side else 1.0), cy + hy)
            ft = (dx - 6 + fx + 1.2 * math.sin(pha) - (0 if side else 1.2), -max(0.0, 1.2 * math.cos(pha)))
            leg(cv_, hp, ft, 4.4, 4.8, -1 if fx < hx else 1, cols=("φ", "χ") if side else ("σ", "υ"), knee_hi="Y" if side else None)
    ex, ey = R(cx, cy)
    def gsh(nu, nv, d, l, ch, X, Y):
        if d > 0.62 or nv > 0.5: return pick("συφχ", l + 0.1)          # the old jewel teal round the rim
        if 0.2 < d < 0.4 and -0.75 < nu < 0.1 and nv < -0.2: return "Y"
        if abs(nu + nv * 0.35 - 0.15) < 0.09 and nv < 0.35: return "6"
        return pick("aoO", l + 0.1)
    ell(f.b, ex, ey, 8.2, 6.4, GOLD, ang=tilt - rear * 18, bias=0.0, shader=gsh, vmax=0.95)
    for k in range(3):                                                   # amber beads along the seam
        q = R(cx - 3.0 + k * 3.0, cy - 3.4 + abs(k - 1) * 0.8)
        ell(f.b, q[0], q[1], 0.8, 0.7, AMB_L, bias=0.4)
    px_, py_ = R(cx + 7.6, cy + 0.6)
    ell(f.b, px_, py_, 3.2, 3.0, TEAL, ang=tilt, bias=0.1)
    hx, hy = R(cx + 10.4, cy + 1.6)
    ell(f.b, hx, hy, 2.4, 2.0, "oOY", bias=0.1)
    # the crown: sun-ray spikes fanning from the rake head
    for k in range(5):
        a = math.radians(-150 + k * 30 - rear * 10)
        L_ = (2.4 + (1.6 if k == 2 else 0.9 if k in (1, 3) else 0.0)) * crown
        b0 = (hx + 1.6 * math.cos(a), hy - 1.0 + 1.6 * math.sin(a))
        b1 = (b0[0] + L_ * math.cos(a), b0[1] + L_ * math.sin(a))
        tube(f.b, [b0, b1], [0.8, 0.35], "oOY")
        f.g.put(*P(*b1), "y" if glow > 0.5 else "Y")
    f.pts["crown"] = (hx, hy - 6)
    if eye != "dead":
        f.g.put(*P(hx + 0.6, hy - 0.4), "L" if eye == "wide" else ("J" if eye == "open" else "D"))
    else:
        f.g.put(*P(hx + 0.6, hy - 0.4), "1")
    f.pts["mouth"] = (hx + 2.4, hy + 0.6)
    # the sun-ball
    if ball > 0:
        r = 8.4 * ball
        bcx, bcy = dx + 10.0 + bx, dy - r - 0.2
        def bs(nu, nv, d, l, ch, X, Y):
            if d < 0.12 + 0.1 * glow: return "y"
            if d < 0.3 + 0.15 * glow: return "E"
            if l > 0.75 and d < 0.45: return "E"
            return pick("6789", l + 0.2 + 0.3 * glow + (0.3 - d) * 0.6)
        ell(f.b, bcx, bcy, r, r, AMB_L, bias=0.1, shader=bs)
        for k in range(3):                                               # insects caught in the amber
            a = rot_ + k * 2.1
            q = (bcx + r * 0.62 * math.cos(a), bcy + r * 0.6 * math.sin(a))
            f.b.put(*P(*q), "6"); f.b.put(*P(q[0] + 1, q[1]), "6"); f.b.put(*P(q[0], q[1] - 1), "7")
        for k in range(6 if glow > 0.3 else 0):                           # rays
            a = rot_ * 0.3 + k * math.pi / 3
            f.g.put(*P(bcx + (r + 1.6) * math.cos(a), bcy + (r + 1.6) * math.sin(a)), "Y" if k % 2 else "y", over=False)
        line(f.u, hx + 1.0, hy + 1.6, bcx - r * 0.75, bcy + r * 0.2, "φ")
        line(f.b, hx + 1.4, hy + 0.8, bcx - r * 0.9, bcy - r * 0.2, "χ")
        f.pts["ball"] = (bcx, bcy)
    if smear:
        for k in range(10):
            t = k / 9.0
            ang = math.radians(smear[0] + (smear[1] - smear[0]) * t)
            f.g.put(*P(dx + 10 + 11.0 * math.cos(ang), dy - 9 + 11.0 * math.sin(ang)), "Y" if k % 2 else "y", over=False)
    if extra: extra(f, (hx, hy), None)
    return f.done()


def sunscarab_corpse():
    f = Fr()
    ell(f.b, -4.0, -3.0, 8.0, 3.0, GOLD, bias=0.05)
    for j, x in enumerate((-7.0, -3.5, 0.0)):
        polyline(f.b, [(x, -5.6), (x - 1 + 2 * (j % 2), -8), (x + (1 if j % 2 else -1), -9.4)], "φχ")
    ell(f.b, 6.0, -2.0, 2.4, 2.0, TEAL)
    for x in range(8, 20):
        if x % 3: f.n.put(x, 0, "7" if x % 2 else "8")
    ell(f.b, 13.0, -2.4, 3.6, 2.4, AMB_L, bias=0.1)
    f.g.put(6, -2, "1")
    return f.done()


def build_sunscarab(outdir):
    S_ = sunscarab
    idle = [S_(glow=0.0, rot_=0.0), S_(glow=0.3, rot_=0.0, dy=0.3, legs=0.2), S_(glow=0.6, rot_=0.0, dy=0.4, legs=0.3, eye="squint"),
            S_(glow=0.3, rot_=0.0, dy=0.2, legs=0.1)]
    run = [S_(legs=i * math.pi / 3 + math.pi / 6, dy=-0.5 * abs(math.sin(i * math.pi / 3 + math.pi / 6)), tilt=-1.0 - 1.5 * math.sin(i),
              rot_=i * 1.05, bx=0.4 * math.sin(i), glow=0.1) for i in range(6)]
    # SHOVE: rear back, the ball pulled in, SHOVE it forward (a heavy hit), roll it back, recover
    shove = [S_(tilt=-4, dx=-1.0, bx=-1.4, eye="wide", glow=0.3),
             S_(tilt=-8, dx=-2.0, bx=-2.4, eye="wide", glow=0.6),
             S_(tilt=6, dx=2.0, bx=3.6, eye="wide", glow=0.8, rot_=0.6),
             S_(tilt=8, dx=2.6, bx=5.4, eye="squint", glow=1.0, rot_=1.2, smear=(-60, 60)),
             S_(tilt=4, dx=1.6, bx=3.0, glow=0.6, rot_=1.6),
             S_(tilt=0, dx=0.6, bx=1.0, glow=0.3, rot_=1.8),
             S_(rot_=2.0)]
    # IDOL: it rears on its hind legs, the crown and ball blaze, SLAM down (an amber idol rises ahead), recover
    idol = [S_(rear=0.3, glow=0.4, crown=1.1, eye="wide"),
            S_(rear=0.7, glow=0.8, crown=1.3, eye="wide"),
            S_(rear=1.0, glow=1.2, crown=1.5, eye="wide"),
            S_(rear=0.0, tilt=6, dx=1.4, glow=1.4, crown=1.3, eye="squint", smear=(-40, 40)),
            S_(rear=0.0, tilt=3, dx=1.0, glow=0.8, crown=1.1),
            S_(glow=0.5, dx=0.4),
            S_(glow=0.3),
            S_(glow=0.1)]
    death = [S_(tilt=-10, eye="wide", rear=0.6, glow=1.0),
             S_(tilt=-22, eye="dead", dy=0.5, legs=2.0, glow=0.2, bx=3.0),
             grounded(S_(tilt=-150, eye="dead", legs=2.5, ball=0.0)),
             sunscarab_corpse()]
    knock = S_(tilt=-10, eye="squint", dx=-0.8, rear=0.3)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.08] * 6),
             ("Shove", shove, [0.14, 0.14, 0.07, 0.06, 0.12, 0.12, 0.14]),
             ("Idol", idol, [0.12, 0.14, 0.16, 0.08, 0.12, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    note("ZhkSunScarab", "Shove", shove, "ball"); note("ZhkSunScarab", "Idol", idol, "ball")
    sheet("ZhkSunScarab", anims, outdir, scale=5)


# ================================================================== v0.10 FX: one sheet per effect of the new monsters
def fx_sip():
    """FxZhkSip: drops of blood spiralling in to the Blood Siphon as it feeds (origin = its feet; played on lifesteal)."""
    out = []
    for i in range(6):
        c = cv()
        for k in range(6):
            a = k * 1.05 + i * 0.55
            r = 11.0 - i * 1.7 - (k % 2)
            if r < 1.0: continue
            x, y = r * math.cos(a), -12 + r * 0.6 * math.sin(a)
            c.put(*P(x, y), "ε" if k % 3 == 0 else "δ"); c.put(*P(x, y + 1), "γ", over=False)
        if i >= 3:
            for k in range(i - 2):
                c.put(*P(-1 + k, -12 - k), "ε")
        out.append(c.spr())
    return out


def fx_transfuse():
    """FxZhkTransfuse: a burst of blood mist rolling out from the Gorger across the floor (origin = its feet)."""
    out = []
    for i in range(6):
        c = cv()
        r = 6 + i * 5.0
        ry = r * 0.36
        n = int(r * 4)
        for k in range(n):
            if i >= 4 and k % 2: continue
            a = 2 * math.pi * k / n
            c.put(*P(r * math.cos(a), ry * math.sin(a) - 2), "δ" if i < 2 else ("γ" if i < 4 else "β"), over=False)
            if k % 3 == 0 and i < 5: c.put(*P(r * 0.85 * math.cos(a), ry * 0.85 * math.sin(a) - 3), "ε" if i < 3 else "δ", over=False)
        rnd = random.Random(i + 40)
        for k in range(8 - i):
            x = rnd.uniform(-r * 0.8, r * 0.8); y = -4 - rnd.uniform(0, 10 + i * 3)
            c.put(*P(x, y), "ε" if k % 2 else "δ"); c.put(*P(x, y + 1), "γ", over=False)
        out.append(c.spr())
    return out


def fx_mend():
    """FxZhkMend: blood motes rising round a monster the Gorger heals, knitting into a red heart-drop (origin = feet)."""
    out = []
    for i in range(7):
        c = cv()
        rnd = random.Random(7)
        for k in range(8):
            x = rnd.uniform(-7, 7); y0 = -rnd.uniform(0, 6)
            y = y0 - i * 2.2
            if y < -18 or (k + i) % 4 == 3: continue
            c.put(*P(x * (1 - i * 0.08), y), "ε" if (k + i) % 2 else "δ")
        if 2 <= i <= 5:
            cy = -14 - (i - 2)
            ell(c, 0, cy, 1.6, 1.8, "γδε", bias=0.4); c.put(0, cy - 3, "δ"); c.put(-1, cy - 1, "ε")
        out.append(outl(c.spr(), "α") if i < 6 else c.spr())
    return out


def fx_egg_dart():
    """FxZhkEggDart: a pale botfly egg on a sticky thread, flying (faces right)."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(5):
            c.put(*P(-3 - k * 1.4, -3 + math.sin(k * 1.3 + i) * 0.8), "Ξ" if k < 2 else "Θ")
        ell(c, 0, -3, 2.4, 1.6, "ΞΠΠ", bias=0.3)
        c.put(-1, -4, "Π"); c.put(1 + (i % 2), -3, "Q")
        out.append(outl(Spr(c.px), "Γ"))
    return out


def fx_implant():
    """FxZhkImplant: an egg-lump squirming under the hero's skin, a red glow pulsing (loop; origin = bottom centre)."""
    out = []
    for i in range(6):
        c = cv()
        w = [0.0, 0.6, 1.0, 0.4, -0.4, -0.8][i]
        ell(c, w * 0.6, -3.2, 2.6, 2.4 + 0.3 * abs(w), "ΘΞΠ", bias=0.25)
        tube(c, [(w * 1.2 - 1.6, -3.6), (w * 0.2, -4.6 + w * 0.6), (1.6 + w * 0.4, -3.0)], [0.6, 0.8, 0.6], "ΔΘ")
        c.put(*P(w * 0.6 - 0.8, -4.4), "Π")
        c.put(*P(w * 0.6 + 1.0, -2.2), "δ" if i % 2 else "γ")
        out.append(outl(c.spr(), "α"))
    return out


def fx_implant_burst():
    """FxZhkImplantBurst: the egg bursts out of the hero in a red splat and a larva wriggles free (origin = ground centre)."""
    out = []
    for i in range(7):
        c = cv()
        if i < 2:
            ell(c, 0, -7 - i, 2.6 + i, 2.4 + i * 1.2, "ΘΞΠ", bias=0.25)
            c.put(0, -9 - i, "δ")
        elif i < 5:
            r = 3 + (i - 2) * 3
            for k in range(10):
                a = -math.pi + k * math.pi / 9
                x, y = r * math.cos(a), -7 + r * 0.8 * math.sin(a) + (i - 2) * 2
                c.put(*P(x, y), "δ" if k % 2 else "ε"); c.put(*P(x * 0.7, y + 1), "γ", over=False)
            for sd in (-1, 1):
                ell(c, sd * (2 + i), -2 - (4 - i), 1.2, 0.9, "ΞΠ", bias=0.3)        # shell halves
        for x in range(-4 - min(i, 4), 5 + min(i, 4)):
            if i >= 2 and (x * 3 + i) % 4: c.put(x, 0, "γ" if x % 2 else "β")
        if i >= 3:                                                                     # the larva, out
            lx = -1 + (i - 3) * 1.2
            tube(c, [(lx - 2.4, -1.2), (lx, -2.0 - (i % 2) * 0.6), (lx + 2.2, -1.4)], [0.9, 1.3, 0.9], "MCH")
            c.put(*P(lx + 2.8, -1.4), "0")
        out.append(c.spr())
    return out


def fx_blink():
    """FxZhkBlink: the Hunting Wasp blinks: a burst of burnt-orange wing blur and blue sparks, then nothing (origin = its feet)."""
    out = []
    for i in range(5):
        c = cv()
        n = [10, 14, 12, 8, 4][i]
        rnd = random.Random(i * 3 + 5)
        for k in range(n):
            a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(2, 6 + i * 3)
            x, y = r * math.cos(a), -18 + r * 0.9 * math.sin(a)
            L = 2 + (k % 3)
            line(c, x, y, x - L * math.cos(a) * 0.8, y - L * 0.8 * math.sin(a), "τ" if k % 2 else "ς")
            if k % 4 == 0: c.put(*P(x + 1, y), "π")
        if i < 2:
            ell(c, 0, -18, 3.0 - i, 4.0 - i, "ικο", bias=0.3)
        out.append(c.spr())
    return out


def fx_bubble():
    """FxZhkBubble: a slow wobbling acid bubble, a glint, a drip trail (faces right)."""
    out = []
    for i in range(6):
        c = cv()
        wob = math.sin(i * math.pi / 3)
        rx, ry = 4.2 + 0.4 * wob, 4.2 - 0.4 * wob
        def sh(nu, nv, d, l, ch, X, Y):
            if d > 0.62: return "Q" if l > 0.2 else "D"
            if l > 0.6 and d < 0.45: return "L"
            return "d" if (X + Y + i) % 3 else "D"
        ell(c, 0, -4.4, rx, ry, ACID, shader=sh)
        c.put(-2, -7, "L"); c.put(-1, -7, "J")
        c.put(*P(-5.6, -3 + (i % 2)), "D"); c.put(*P(-7, -2), "d")
        out.append(outl(c.spr(), "d"))
    return out


def fx_droplet():
    """FxZhkDroplet: a small acid droplet flung out of a popped bubble (faces right)."""
    out = []
    for i in range(4):
        c = cv()
        ell(c, 0, -2, 1.6, 1.2, "DQJ", bias=0.3)
        c.put(1, -2, "L" if i % 2 else "J")
        c.put(-2, -2, "D"); c.put(*P(-3, -2 + (i % 2) * 0.6), "d")
        out.append(c.spr())
    return out


def fx_bubble_pop():
    """FxZhkBubblePop: the bubble skin tears and flies apart in a ring of acid spray (origin = centre)."""
    out = []
    for i in range(5):
        c = cv()
        r = 3 + i * 2.6
        n = 12
        for k in range(n):
            if i >= 3 and k % 2: continue
            a = 2 * math.pi * k / n + i * 0.2
            x, y = r * math.cos(a), -5 + r * 0.8 * math.sin(a)
            c.put(*P(x, y), "J" if i < 2 else ("Q" if i < 4 else "D"))
            if i < 3: c.put(*P(x * 0.8, y * 0.8 - 1), "D", over=False)
        if i == 0: ell(c, 0, -5, 3.0, 3.0, "dDQ", bias=0.2); c.put(-1, -7, "L")
        out.append(c.spr())
    return out


def fx_vent():
    """FxZhkVent: the Bloater vents its swollen sac: a ring of acid gas rolls out across the floor (hits on frames 1-3)."""
    out = []
    for i in range(7):
        c = cv()
        r = 5 + i * 3.4
        ry = r * 0.38
        n = int(r * 4)
        for k in range(n):
            a = 2 * math.pi * k / n
            for rr, ch in ((r, "Q" if i < 4 else "D"), (r - 2.0, "D" if i < 5 else "d")):
                if rr < 2 or (i >= 5 and (k + int(rr)) % 2): continue
                c.put(*P(rr * math.cos(a), rr * 0.38 * math.sin(a) - 2), ch, over=False)
            if k % 4 == 0 and i < 6:
                h = 2 + (k * 3 + i) % 4
                c.put(*P(r * math.cos(a), ry * math.sin(a) - 2 - h), "J" if i < 3 else "Q", over=False)
        out.append(c.spr())
    return out


def fx_inflate():
    """FxZhkInflate: the Bloater's Inflate status (damage taken halved): a swollen green ring with glowing seams pulsing
    over its head (loop; origin = bottom centre)."""
    out = []
    for i in range(6):
        c = cv()
        s = 1.0 + 0.12 * math.sin(i * math.pi / 3)
        def sh(nu, nv, d, l, ch, X, Y):
            if d < 0.45: return None
            if (math.atan2(nv, nu) * 4 / math.pi + i * 0.3) % 1.0 < 0.25: return "J"
            return pick("dDQ", l + 0.2)
        ell(c, 0, -3.6, 4.4 * s, 3.0 * s, ACID, shader=sh)
        c.put(*P(-2 * s, -5.6 * s), "L")
        out.append(outl(c.spr(), "1"))
    return out


def fx_pit():
    """FxZhkPit: the Antlion's sand funnel: it opens, the sand streams round and in for 1.2 s, then caves in
    (origin = the pit's centre on the floor)."""
    out = []
    for i in range(10):
        c = cv()
        grow = min(1.0, (i + 1) / 3.0) * (1.0 if i < 8 else (1.0 - (i - 7) * 0.3))
        R_ = 22.0 * grow
        for ring in range(5):
            rr = R_ * (1.0 - ring * 0.19)
            if rr < 2: continue
            n = int(rr * 3.2)
            for k in range(n):
                a = 2 * math.pi * k / n + i * (0.35 + ring * 0.12)
                if (k + ring + i) % 3 == 0: continue
                ch = "ΣΦΧΛ"[min(3, max(0, 3 - ring + (k % 2)))] if ring < 4 else "Σ"
                c.put(*P(rr * math.cos(a), rr * 0.36 * math.sin(a) - 1), ch, over=False)
        if 0 < grow:
            ell(c, 0, -1, max(1.0, R_ * 0.18), max(0.8, R_ * 0.07), "0Σ", bias=-0.4)
        if i < 8:                                                         # grains sliding down the slope
            for k in range(6):
                a = k * 1.047 + i * 0.6
                rr = R_ * (0.85 - ((i * 0.15 + k * 0.13) % 0.6))
                c.put(*P(rr * math.cos(a), rr * 0.36 * math.sin(a) - 1), "Λ")
        out.append(c.spr())
    return out


def fx_glue_shell():
    """FxZhkGlueShell: a target ring of glue spatter blooms while the mortar's shell drops out of the sky; SPLAT on
    frame 4, sticky strands flung out (origin = floor centre)."""
    out = []
    for i in range(7):
        c = cv()
        rr = [4, 6, 8, 9, 10, 10, 10][i]
        n = int(rr * 5)
        for k in range(n):
            if i < 4 and (k + i) % 3 == 0: continue
            if i >= 5 and k % 2: continue
            a = 2 * math.pi * k / n
            c.put(*P(rr * math.cos(a), rr * 0.38 * math.sin(a) - 1), "7" if i < 3 else "8")
        if i < 4:
            dy = [-34, -25, -16, -7][i]
            for k in range(3): c.put(0, dy - 4 - k * 2, "8" if k == 0 else "7")
            ell(c, 0, dy, 2.2, 2.6, "6789", bias=0.3)
            line(c, -2, dy - 0.5, 2, dy - 1.0, "1")
            c.put(-1, dy - 1, "E")
        elif i == 4:
            ell(c, 0, -2.0, 7.0, 2.8, "6789", bias=0.3)
            for sd in (-1, 1):
                for k in range(3):
                    line(c, sd * (1 + k * 2.0), -2, sd * (3 + k * 3.0), -6 - (2 - k) * 1.8, "89")
            c.put(-1, -3, "E")
        else:
            for x in range(-8, 9):
                if (x + i) % 2: c.put(x, -1, "7")
            for k in range(5):
                c.put(*P(-7 + k * 3.5, -3 - (i - 4) * 2 - (k % 2)), "9" if i == 5 else "8")
        out.append(c.spr())
    return out


def fx_glue_field():
    """FxZhkGlueField: a wide sheet of grey-amber glue, stringy and bubbling, that slows (Life = spread, idle, fade)."""
    E, I = "6Θ8", "7Θ"
    sp = [puddle(E, I, 0.4, 0, w=13, bub="9", glint="Π"), puddle(E, I, 0.75, 1, w=13, bub="9", glint="Π"),
          puddle(E, I, 0.95, 2, w=13, bub="9", glint="Π", strands=True)]
    idle = [puddle(E, I, 1.0, k, seed=k + 3, w=13, bub="9", glint="Π", strands=(k % 2 == 0)) for k in range(3)]
    fd = [puddle(E, I, 0.95, 0, 0.35, w=13, bub="9", glint="Π"), puddle(E, I, 0.85, 1, 0.6, w=13, bub="9", glint="Π"),
          puddle(E, I, 0.7, 2, 0.85, w=13, bub="9", glint="Π")]
    return sp, idle, fd


def fx_roll_ball():
    """FxZhkRollBall: the scarab's amber resin ball rolling (a trapped speck turning, dust behind); faces right."""
    out = []
    for i in range(6):
        c = cv(); g = cv()
        amber_ball(c, g, 0, -4.6, 4.4, rot_=-i * 1.05, bugs=2)
        o = merge(outl(c.spr(), "6"), g.spr())
        dust = cv()
        for k in range(3):
            dust.put(*P(-6 - k * 2 - (i % 2), -1 - (k % 2)), "ΦΧ"[k % 2])
        out.append(merge(dust.spr(), o))
    return out


def fx_toss_land():
    """FxZhkTossLand: where the Stag throws the hero down: a crack of dust and violet chitin chips (origin = floor)."""
    out = []
    for i in range(6):
        c = cv()
        r = 3 + i * 2.6
        for k in range(14):
            a = -math.pi + k * math.pi / 13
            if i >= 4 and k % 2: continue
            c.put(*P(r * math.cos(a), -1 + r * 0.5 * math.sin(a) - (2 if i < 3 else 0) * abs(math.sin(a))), "ΧΛΦ"[k % 3], over=False)
        rnd = random.Random(i + 9)
        for k in range(6 - i):
            x = rnd.uniform(-8, 8); y = -2 - rnd.uniform(0, 4 + i * 1.6)
            c.put(*P(x, y), "Ψ" if k % 2 else "χ")
        for x in range(-3 - i, 4 + i):
            if (x + i) % 3 == 0: c.put(x, 0, "Σ")
        out.append(c.spr())
    return out


def fx_idol():
    """FxZhkIdol: the Sun Scarab's amber idol: it heaves up out of the floor (Rise), glows and spits sparks (Pulse,
    looped by the code while it fires), then cracks and slumps (Crack). Life = the whole run (origin = floor centre)."""
    def idol(h, glow, crack=0.0, ph=0):
        c = cv(); g = cv()
        if h <= 0: return c.spr()
        def sh(nu, nv, d, l, ch, X, Y):
            if crack > 0 and abs(nu * 3 + nv - 0.4 * math.sin(Y)) < 0.3 * crack: return "6"
            if d < 0.2 + 0.1 * glow: return "y" if glow > 0.6 else "E"
            if l > 0.7 and d < 0.45: return "E"
            return pick("6789", l + 0.15 + 0.35 * glow - d * 0.2)
        ell(c, 0, -5 * h - 1, 5.0, 5.6 * h, AMB_L, shader=sh, vmax=1.0)
        for k in range(5):                                            # a crown of sun-ray spikes
            a = math.radians(-150 + k * 30)
            b0 = (4.4 * math.cos(a), -5 * h - 1 + 5.0 * h * math.sin(a))
            b1 = (b0[0] + 2.0 * math.cos(a) * h, b0[1] + 2.0 * math.sin(a) * h)
            line(c, b0[0], b0[1], b1[0], b1[1], "Y")
        ell(c, 0, -0.6, 6.0, 1.4, "συφ", bias=0.2)                    # teal base
        o = outl(c.spr(), "6")
        if glow > 0.5:
            for k in range(6):
                a = k * math.pi / 3 + ph * 0.5
                g.put(*P(7.4 * math.cos(a), -5 * h - 1 + 7.4 * math.sin(a)), "y" if (k + ph) % 2 else "Y")
        return merge(o, g.spr())
    rise = [idol(0.3, 0.0), idol(0.6, 0.1), idol(0.9, 0.3), idol(1.0, 0.5)]
    pulse = [idol(1.0, 0.6, ph=0), idol(1.0, 0.9, ph=1), idol(1.0, 1.0, ph=2), idol(1.0, 0.7, ph=3)]
    crack = [idol(1.0, 0.4, 0.5), idol(0.9, 0.2, 1.0), idol(0.6, 0.0, 1.4), idol(0.3, 0.0, 1.8)]
    return rise, pulse, crack


def fx_idol_spark():
    """FxZhkIdolSpark: a bright amber spark the idol spits at the hero (faces right)."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(4):
            c.put(*P(-2 - k * 1.3, -3 + (k % 2) * (1 if i % 2 else -1) * 0.6), "8" if k < 2 else "7")
        ell(c, 0, -3, 1.8, 1.4, "89Ey", bias=0.4)
        c.put(1, -3, "y")
        out.append(outl(c.spr(), "6"))
    return out


def build_fx10(outdir):
    fx_sheet("FxZhkSip", [("Play", fx_sip(), [0.06] * 6)], outdir)
    fx_sheet("FxZhkTransfuse", [("Play", fx_transfuse(), [0.06, 0.07, 0.08, 0.09, 0.1, 0.12])], outdir, scale=4)
    fx_sheet("FxZhkMend", [("Play", fx_mend(), [0.08] * 7)], outdir)
    fx_sheet("FxZhkEggDart", [("Fly", fx_egg_dart(), [0.07] * 4)], outdir)
    fx_sheet("FxZhkImplant", [("Loop", fx_implant(), [0.09] * 6)], outdir)
    fx_sheet("FxZhkImplantBurst", [("Play", fx_implant_burst(), [0.08, 0.08, 0.05, 0.07, 0.09, 0.1, 0.12])], outdir, scale=6)
    fx_sheet("FxZhkBlink", [("Play", fx_blink(), [0.04, 0.05, 0.05, 0.06, 0.06])], outdir)
    fx_sheet("FxZhkBubble", [("Fly", fx_bubble(), [0.1] * 6)], outdir)
    fx_sheet("FxZhkDroplet", [("Fly", fx_droplet(), [0.06] * 4)], outdir)
    fx_sheet("FxZhkBubblePop", [("Play", fx_bubble_pop(), [0.04, 0.05, 0.06, 0.07, 0.08])], outdir)
    fx_sheet("FxZhkVent", [("Play", fx_vent(), [0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.12])], outdir, scale=4)
    fx_sheet("FxZhkInflate", [("Loop", fx_inflate(), [0.1] * 6)], outdir)
    fx_sheet("FxZhkPit", [("Play", fx_pit(), [0.08, 0.08, 0.1, 0.14, 0.14, 0.14, 0.14, 0.14, 0.1, 0.1])], outdir, scale=4)
    fx_sheet("FxZhkGlueShell", [("Play", fx_glue_shell(), [0.12, 0.12, 0.12, 0.1, 0.06, 0.1, 0.12])], outdir, scale=6)
    sp, idl, fd = fx_glue_field()
    fx_sheet("FxZhkGlueField", [("Life", sp + idl * 4 + fd, [0.1] * 3 + [0.2] * 12 + [0.15] * 3),
                                ("Spread", sp, [0.1] * 3), ("Idle", idl, [0.2] * 3), ("Fade", fd, [0.15] * 3)], outdir)
    fx_sheet("FxZhkRollBall", [("Fly", fx_roll_ball(), [0.06] * 6)], outdir)
    fx_sheet("FxZhkTossLand", [("Play", fx_toss_land(), [0.05, 0.06, 0.07, 0.08, 0.09, 0.1])], outdir)
    rise, pulse, crack = fx_idol()
    fx_sheet("FxZhkIdol", [("Life", rise + pulse * 5 + crack, [0.08] * 4 + [0.2] * 20 + [0.1] * 4),
                           ("Rise", rise, [0.08] * 4), ("Pulse", pulse, [0.2] * 4), ("Crack", crack, [0.1] * 4)], outdir)
    fx_sheet("FxZhkIdolSpark", [("Fly", fx_idol_spark(), [0.06] * 4)], outdir)


# ================================================================== TIMING.md + contact sheet
MONSTERS = ["ZhkGrub", "ZhkDrone", "ZhkBeetle", "ZhkHornet", "ZhkSpitter", "ZhkSoldier", "ZhkNasute", "ZhkHive", "ZhkMother",
            "ZhkMantis", "ZhkColossus", "ZhkLarva", "ZhkSiphon", "ZhkScarab", "ZhkBloater", "ZhkAntlion", "ZhkHunter", "ZhkGorger",
            "ZhkBotfly", "ZhkMortar", "ZhkStag", "ZhkSunScarab"]
# v0.10: one row per tier, children under their parent's order (Grub, Drone, Beetle)
TIERS = [["ZhkGrub", "ZhkDrone", "ZhkBeetle"], ["ZhkSpitter", "ZhkSoldier", "ZhkHornet", "ZhkSiphon", "ZhkNasute", "ZhkScarab"],
         ["ZhkMother", "ZhkBloater", "ZhkMantis", "ZhkAntlion", "ZhkHive", "ZhkHunter", "ZhkGorger", "ZhkBotfly", "ZhkColossus",
          "ZhkMortar", "ZhkStag", "ZhkSunScarab"], ["ZhkLarva"]]
FXN = ["FxZhkAcidSpit", "FxZhkStinger", "FxZhkResinGlob", "FxZhkAcidGlob", "FxZhkResin", "FxZhkAcidPool", "FxZhkSplash",
       "FxZhkEgg", "FxZhkAcidRain", "FxZhkPheromone", "FxZhkSwarm", "FxZhkPlate", "FxZhkResinBurst", "FxZhkDirt",
       "FxZhkGlueJet", "FxZhkSwarmCloud", "FxZhkMarkDart", "FxZhkMark", "FxZhkSeal", "FxZhkHornetStinger", "FxZhkAcidMark",
       "FxZhkFrenzy", "FxZhkSip", "FxZhkTransfuse", "FxZhkMend", "FxZhkEggDart", "FxZhkImplant", "FxZhkImplantBurst", "FxZhkBlink",
       "FxZhkBubble", "FxZhkDroplet", "FxZhkBubblePop", "FxZhkVent", "FxZhkInflate", "FxZhkPit", "FxZhkGlueShell", "FxZhkGlueField",
       "FxZhkRollBall", "FxZhkTossLand", "FxZhkIdol", "FxZhkIdolSpark"]
ICONS = ["IconZhkAcidSpit", "IconZhkAcidSpitBubble", "IconZhkHiveAmber", "IconZhkHiveAmberBubble", "IconZhkHiveAmberHud",
         "DeityZhekra"]

# (anim, moment, frame, spawn-point key or a literal "(x, y)" / "-")
EVENTS = {
    "ZhkGrub": [("Bite", "lunge (jaws wide)", 2, "-"), ("Bite", "HIT: mandibles snap", 3, "mouth"),
                ("Spit", "glands swell (spiracles flare)", 2, "-"), ("Spit", "RELEASE: spawn FxZhkAcidSpit", 3, "mouth")],
    "ZhkDrone": [("Sting", "abdomen curled under, aiming", 2, "-"), ("Sting", "RELEASE: spawn FxZhkStinger", 3, "sting"),
                 ("Dive", "wings fold: dash starts, 14 x 14 body hit on", 2, "(4, -8)"), ("Dive", "pull out: dash ends", 5, "-")],
    "ZhkBeetle": [("Snap", "lunge (mandibles wide)", 2, "-"), ("Snap", "HIT: mandibles snap", 3, "mouth"),
                  ("Resin", "throat full of resin", 2, "-"), ("Resin", "RELEASE: FxZhkResinGlob at the mouth; code launches it on the floor (9, -1), art drawn 4 px up", 3, "mouth")],
    "ZhkSpitter": [("Lob", "sac contracts, spout up", 2, "-"), ("Lob", "RELEASE: FxZhkAcidGlob at the spout; code launches it on the floor (11, -1) with art drawn 14 px up", 3, "mouth"),
                   ("Egg", "egg crowning at the ovipositor", 2, "-"), ("Egg", "EGG LAID: spawn the FxZhkEgg/Life spawner", 4, "rear")],
    "ZhkSoldier": [("Scythe", "HIT 1: near blade sweeps down (smear)", 2, "tip"), ("Scythe", "HIT 2: second sweep (smear)", 5, "tip"),
                   ("Burrow", "digs in: invincible + no collision from here", 1, "-"),
                   ("Burrow", "only the mound is left: TELEPORT under the hero (telegraph 0.52 s)", 3, "-"),
                   ("Burrow", "mound cracks, acid glow", 5, "-"),
                   ("Burrow", "ERUPT: hit + FxZhkDirt, collision back on", 6, "(0, -8)"),
                   ("Burrow", "out of the ground: invincibility off", 7, "-")],
    "ZhkMother": [("Rain", "throat swells, head back", 2, "-"), ("Rain", "RELEASE: acid spewed up; FxZhkAcidRain lands on the hero", 3, "mouth"),
                  ("Brood", "PHEROMONE: spawn FxZhkPheromone (crown)", 2, "crown"),
                  ("Brood", "EGG 1 out of the tail", 4, "tail"), ("Brood", "EGG 2", 5, "tail")],
    "ZhkColossus": [("Gore", "head low, braced", 2, "-"), ("Gore", "HIT: horn heaves up (smear)", 3, "horn"),
                    ("Charge", "HARDEN: shell cracks, resin wells up (gain a plate)", 1, "-"),
                    ("Charge", "CHARGE starts: move + body hit, resin drops behind", 3, "horn"),
                    ("Charge", "skid: charge ends", 7, "-")],
    "ZhkLarva": [("Bite", "HIT: bite", 3, "mouth")],
    "ZhkHornet": [("Volley", "abdomen curled under, aiming", 2, "-"), ("Volley", "RELEASE: 3 FxZhkHornetStinger in a fan", 3, "sting"),
                  ("Mark", "pheromone gland glowing", 2, "-"), ("Mark", "RELEASE: FxZhkMarkDart", 4, "sting")],
    "ZhkNasute": [("Squirt", "head down, gut full", 1, "-"), ("Squirt", "RELEASE: 3 FxZhkGlueJet, 0.05 s apart", 2, "mouth"),
                  ("Seal", "SEAL: allies within 70 px gain a resin plate (FxZhkSeal on each)", 2, "mouth"),
                  ("Seal", "resin rains back down: a resin puddle at its feet", 4, "(0, 0)")],
    "ZhkHive": [("Swarm", "cells glowing, swarm gathering", 2, "-"), ("Swarm", "RELEASE: 2 FxZhkSwarmCloud from the comb", 3, "comb"),
                ("Rebuild", "squats; resin starts oozing", 1, "-"),
                ("Rebuild", "RESIN RING: 4 resin puddles around it, heals 1.5", 3, "(0, 0)")],
    "ZhkMantis": [("Reap", "HIT 1: acid blade sweeps down (smear)", 2, "tip"), ("Reap", "HIT 2: second sweep (smear)", 5, "tip"),
                  ("Pounce", "springs: LEAP to the hero (0.3 s, no collision)", 2, "-"),
                  ("Pounce", "LANDS: impact hit + acid pool", 5, "(9, 0)")],
    # v0.10 new monsters
    "ZhkSiphon": [("Stab", "thrust", 2, "-"), ("Stab", "HIT: the needle goes in (lifesteal)", 3, "tip"),
                  ("Drink", "DIVE: dash starts, drain hits on (lifesteal)", 2, "tip"), ("Drink", "latched: dash stops", 3, "tip")],
    "ZhkGorger": [("Drill", "plunge", 2, "-"), ("Drill", "HIT: the drill goes in (lifesteal)", 3, "tip"),
                  ("Transfuse", "squeezing", 2, "-"), ("Transfuse", "MIST: FxZhkTransfuse; heals itself and every monster near it", 3, "sac")],
    "ZhkBotfly": [("Ram", "rush", 2, "-"), ("Ram", "HIT: head-first bump", 3, "mouth"),
                  ("Implant", "egg on the sting", 2, "-"), ("Implant", "RELEASE: FxZhkEggDart", 4, "sting")],
    "ZhkHunter": [("Lance", "curl", 2, "-"), ("Lance", "HIT: lance thrust (may daze)", 3, "sting"),
                  ("Hunt", "BLINKS start: 3 blinks round the hero, a sting after each", 2, "-"),
                  ("Hunt", "last sting", 5, "sting")],
    "ZhkBloater": [("Blow", "bubble swelling at the spout", 2, "-"), ("Blow", "RELEASE: FxZhkBubble", 4, "mouth"),
                   ("Inflate", "INFLATE: damage taken halved 3 s, then FxZhkVent", 3, "sac")],
    "ZhkAntlion": [("Clamp", "jaws gape", 2, "-"), ("Clamp", "HIT: jaws snap", 3, "mouth"),
                   ("Pit", "PIT opens 18 px ahead (FxZhkPit, code), the hero is dragged in for 0.75 s", 1, "(18, 0)"),
                   ("Pit", "SNAP: jaws close (the Clamp hitbox again)", 6, "(18, -6)")],
    "ZhkMortar": [("Lob", "tanks squeezed", 2, "-"), ("Lob", "FIRE: FxZhkGlueShell lands on the hero", 3, "muzzle"),
                  ("Barrage", "FIRE 1", 2, "muzzle"), ("Barrage", "FIRE 2", 4, "muzzle"), ("Barrage", "FIRE 3", 6, "muzzle")],
    "ZhkScarab": [("Bowl", "ball shoved forward", 2, "ball"), ("Bowl", "RELEASE: FxZhkRollBall at the ball", 3, "-"),
                  ("Roll", "ROLL starts: bouncing roll + body hit", 2, "-"), ("Roll", "uncurl", 7, "-")],
    "ZhkStag": [("Pinch", "lunge", 2, "-"), ("Pinch", "HIT: mandibles snap", 3, "mouth"),
                ("Toss", "GRAB: the hero in front is held in the mandibles", 2, "mouth"),
                ("Toss", "FLING: hero thrown behind it, FxZhkTossLand hit there", 5, "-")],
    "ZhkSunScarab": [("Shove", "ball rolled forward", 2, "-"), ("Shove", "HIT: the ball rams", 3, "ball"),
                     ("Idol", "crown blazing", 2, "-"), ("Idol", "SLAM: FxZhkIdol rises ahead", 3, "(24, 0)")],
}
FX_NOTES = {
    "FxZhkAcidSpit": "Fly loop, faces right (Acid Grub spit, Acid Spit spell).",
    "FxZhkStinger": "Fly loop, faces right (Brood Drone dart).",
    "FxZhkResinGlob": "Fly loop, faces right (Resin Beetle; Colossus trail blobs).",
    "FxZhkAcidGlob": "Fly loop, faces right (Acid Spitter lob).",
    "FxZhkResin": "Life = spread 0-2 (0.1 s), idle 3-18 (2 frames x8, 0.22 s), fade 19-21 (0.15 s); 4.27 s. Sticky root zone.",
    "FxZhkAcidPool": "Life = spread 0-2, idle 3-14 (4 frames x3, 0.2 s), fade 15-17; 3.09 s. Acid zone (damage tick + Corroded).",
    "FxZhkSplash": "Play once; crown peaks on frame 2; vapour on 3-4.",
    "FxZhkEgg": "Hatch 0.56 s (death perk: cracks, splits, larva out at the end); Life 1.26 s (laid egg wobbles, then hatches).",
    "FxZhkAcidRain": "Play once; target ring frames 0-3 while the drop falls from ~32 px up; SPLAT (hit) on frame 4 (t = 0.46 s).",
    "FxZhkPheromone": "Play once; amber rings to r = 36 px (Brood Mother frenzy pulse).",
    "FxZhkSwarm": "Loop; motes circling ~6 px around the anchor (swarm buff marker, attach above the head).",
    "FxZhkPlate": "Loop; two resin plates orbit r = 9 px (Colossus chitin plates).",
    "FxZhkResinBurst": "Play once; resin ring to r = 15 px (Hive Amber artifact).",
    "FxZhkDirt": "Play once; earth + chitin chips (Hive Soldier eruption).",
    "FxZhkGlueJet": "Fly loop, faces right (Nasute glue stream).",
    "FxZhkSwarmCloud": "Loop; a knot of tiny hornets (Amber Hive swarm cloud, drifts slowly).",
    "FxZhkMarkDart": "Fly loop, faces right (Hive Hornet pheromone dart).",
    "FxZhkMark": "Loop; amber chevron over a Marked hero (status effect, attached).",
    "FxZhkSeal": "Play once; resin dome flowing over an ally sealed by the Nasute.",
    "FxZhkHornetStinger": "Fly loop, faces right (Hive Hornet volley; v0.8, was the Drone's FxZhkStinger).",
    "FxZhkAcidMark": "Loop; Corroded status overlay: acid droplet with a corroded hole, hovering over the victim's head (origin = bottom centre).",
    "FxZhkSip": "Play once; blood drops spiral into the Blood Siphon when its lifesteal heals it (origin = its feet).",
    "FxZhkTransfuse": "Play once; blood mist rolling out to r 31 (Blood Gorger Transfuse).",
    "FxZhkMend": "Play once; blood motes rising over a monster the Gorger heals.",
    "FxZhkEggDart": "Fly loop, faces right (Botfly Matron implant dart).",
    "FxZhkImplant": "Loop; the implanted egg squirming over the hero's head (status overlay, 3 s).",
    "FxZhkImplantBurst": "Play once; the egg bursts out of the hero (hit frames 2-3) and a larva crawls free.",
    "FxZhkBlink": "Play once; orange wing blur where the Hunting Wasp blinks out and in.",
    "FxZhkBubble": "Fly loop, faces right (Acid Bloater bubble).",
    "FxZhkDroplet": "Fly loop, faces right (the bubble's 6 droplets).",
    "FxZhkBubblePop": "Play once; the bubble tearing apart.",
    "FxZhkVent": "Play once; acid gas ring to r 25 (Bloater vents after Inflate; hit frames 1-3).",
    "FxZhkInflate": "Loop; Inflate status overlay over the Bloater's head.",
    "FxZhkPit": "Play once (1.16 s); the Antlion's sand funnel, r 22 x 8.",
    "FxZhkGlueShell": "Play once; target ring while the mortar shell falls, SPLAT on frame 4 (t = 0.46 s), leaves FxZhkGlueField.",
    "FxZhkGlueField": "Life = spread 0-2, idle 3-14, fade 15-17 (3.15 s); slowing glue sheet.",
    "FxZhkRollBall": "Fly loop; the Amber Scarab's rolling resin ball (bounces off walls).",
    "FxZhkTossLand": "Play once; dust and chitin where the Stag Titan throws the hero.",
    "FxZhkIdol": "Life = Rise 0-3, Pulse 4-23 (fires sparks), Crack 24-27 (4.72 s); the Sun Scarab's amber idol.",
    "FxZhkIdolSpark": "Fly loop, faces right (the idol's resin sparks).",
    "FxZhkFrenzy": "Loop (r 9 x 3) / LoopBig (r 15 x 5, large monsters); Frenzy status overlay: amber pheromone motes whirling round the feet (origin = feet = row 9 of 13, 3.5 px above the cell bottom edge: overlay offsetY -3.5).",
}


V08_NOTES = [
    "## v0.8 art pass", "",
    "- ZhkHornet redrawn (it read as a big Drone): upright oxblood-and-rust hunter, abdomen hanging below the body with",
    "  acid-green bands and an amber gland, raised smoky-amber wings. Idle 17 x 25. The sting moved: Volley f3 / Mark f4",
    "  release at (8, -9) (kit offsets 8, 9; Strike.Feet node 9; ZhkBrain swarm-mote height 25).",
    "- New FxZhkHornetStinger (was the Drone's FxZhkStinger), FxZhkAcidMark (Corroded overlay, over the head) and FxZhkFrenzy",
    "  (Frenzy overlay at the feet, Loop + LoopBig) wired with ModStatus.RegisterOverlay.",
    "- Readability: ZhkSoldier, ZhkSpitter, ZhkColossus, ZhkBeetle wear a lighter chitin ramp (LIFT), ZhkMantis an olive",
    "  acid-green chitin (LIFT_OLIVE); geometry, sync frames and spawn points unchanged.",
    "- ZhkBeetle and ZhkHive Run: half-step gait offset + lean, so no Run frame repeats an Idle pose.",
    "- ZhkLarva needs no Spawn anim: its base (EnemyFodderMushroom) has no spawn clip.", "",
    "## v0.9 lineage pass",
    "",
    "Every evolution now carries a motif of each parent (strike points, sync frames and hitboxes unchanged):",
    "- ZhkSpitter (Grub + Drone): grub-flesh thorax with acid spiracles, the drone's pale wings, amber-banded ovipositor.",
    "- ZhkSoldier (Grub + Beetle): pale ringed grub gaster with spiracles, the beetle's resin-beaded shell on the mesosoma.",
    "- ZhkNasute (Beetle): the beetle's resin-beaded elytra dome over the thorax. ZhkHornet (Drone): wasp body and wings.",
    "- ZhkMother (Spitter + Hornet): hornet rust torso/head with a black face plate and smoky wings; the spitter's acid sac.",
    "- ZhkMantis (Spitter + Soldier): the spitter's acid sac on the abdomen, the soldier's scythe arms.",
    "- ZhkColossus (Soldier + Nasute): the horn ends in the nasute's glue nozzle, pale termite belly, soldier mandibles.",
    "- ZhkHive (Hornet + Nasute): rust hornet brood and smoky wings, a nasute nozzle on the queen's brow (idle 37 x 38).",
    "- All monster cells now have an even height (a spare top row); feet stay 2 rows above the bottom.",
    "",
    "## v0.10 final art review",
    "",
    "- ZhkLarva: its own creature now (maggot()): a legless, eyeless pale maggot arched like a crescent, ring creases, black",
    "  mouth hooks and an acid drip. Bite hit frame 3 mouth (9, -2), inside the 8 x 8 bite box at (6, 3).",
    "- ZhkNasute: swollen amber glue-sac abdomen and a much bigger dark nozzle head with its own rim (vs the Soldier's pale",
    "  gaster). Squirt release frame 2 nozzle (16, -12): kit GlueJet (15, 11), Strike.Feet 11.",
    "- Lifts: ZhkBeetle shell (no outline-black inside the shell), ZhkHornet midtones (HORNET_LIFT).",
    "- Acid pool / resin Fade frames shrink cleanly instead of stippling.",
    "",
    "## v0.10 unique-evolution tree",
    "",
    "Every evolved monster has ONE parent: Grub -> Spitter (-> Mother, Bloater), Soldier (-> Mantis, Antlion);",
    "Drone -> Hornet (-> Hive, Hunter), Siphon (-> Gorger, Botfly); Beetle -> Nasute (-> Colossus, Mortar), Scarab (-> Stag,",
    "SunScarab). Motifs of lost parents redrawn: Spitter ovipositor is grub flesh (was the drone's banded sting); Soldier",
    "carries grub back plates (was the beetle's beaded shell); Mother has spitter chitin and pale wings (was hornet rust, smoky",
    "wings, face plate); Mantis carries the soldier's ringed gaster (was the spitter's acid sac); Hive has a hornet crest (was",
    "the nasute nozzle); Colossus has the nasute's amber sac belly (was pale grub flesh). Cells, sync frames, spawn points",
    "unchanged. Ten new monsters and nineteen new FX sheets (tables above).",
    ""]


def write_timing(outdir):
    L = ["# Zhekra, the Brood Queen: sprite timing", "",
         "Generated by `tools/sprites/zhekra_rigs.py`. Frame indices are 0-based within the anim; `t` is the time",
         "from the start of the anim to the start of that frame. Monsters face right.",
         "Monster sheets: feet = (cellW//2, cellH-2). FX: origin = effect centre on the ground.",
         "Spawn points are in pixels relative to the feet (x right, y up negative), facing right; mirror x when flipped.",
         "Kit.AddEffect takes offsetX = x, offsetY = -y.", "",
         "## Monster sheets", "", "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        img = b["img"]; fi = b["man"]["anims"][0]["frames"][0]; cols = b["man"]["cols"]
        bb = img.crop(((fi % cols) * cw, (fi // cols) * ch, (fi % cols + 1) * cw, (fi // cols + 1) * ch)).getbbox()
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, cw // 2, ch - 2, bb[2] - bb[0], bb[3] - bb[1],
                 ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Move anims: sync frames", ""]
    for n in MONSTERS:
        if n not in BUILT: continue
        anims = {a: (k, d) for a, k, d in BUILT[n]["anims"]}
        done = set()
        evs = EVENTS[n]
        for idx, (an, ev, fi, sp) in enumerate(evs):
            k, d = anims[an]
            if an not in done:
                L += ["### %s / `%s`: %d frames, %.2f s" % (n, an, k, sum(d)), "Durations: " + ", ".join("%.2f" % x for x in d), "",
                      "| Frame | t (s) | Moment | Spawn point |", "|---|---|---|---|"]
                done.add(an)
            assert fi < k, (n, an, fi)
            if sp not in ("-",) and not sp.startswith("("):
                p = SPAWN.get(n, {}).get((an, fi, sp))
                sp = "%s (%d, %d)" % (sp, p[0], p[1]) if p else sp
            L.append("| %d | %.2f | %s | %s |" % (fi, sum(d[:fi]), ev, sp))
            if idx == len(evs) - 1 or evs[idx + 1][0] != an: L.append("")
    L += ["Every attack has at least two wind-up frames before its first event. Death plays once and ends on the corpse;",
          "Dead is that same corpse frame. Zhekra monsters (not the larva) hatch a larva where they die: FxZhkEgg/Hatch.", "",
          "## FX sheets", "", "| Sheet | Cell (w x h) | Origin | Anims (frames, total s) | Notes |", "|---|---|---|---|---|"]
    for n in FXN:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"]), FX_NOTES[n]))
    L += ["", "## Icons and portrait", "", "| Sheet | Cell | Anims |", "|---|---|---|"]
    for n in ICONS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | %s |" % (n, cw, ch, ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += [""] + V08_NOTES
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(outdir, "TIMING.md"))


def contact_sheet(outdir, extra_path=None):
    """All seven monsters' Idle frame 0 on one floor line, the larva, and the god portrait, at 4x."""
    cells = []
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; img, man = b["img"], b["man"]
        cw, chh = man["cellW"], man["cellH"]
        fi = man["anims"][0]["frames"][0]
        x0, y0 = (fi % man["cols"]) * cw, (fi // man["cols"]) * chh
        c = img.crop((x0, y0, x0 + cw, y0 + chh))
        bb = c.getbbox()
        cells.append(c.crop((bb[0] - 1, 0, bb[2] + 1, chh)))
    if "DeityZhekra" in BUILT:
        cells.append(BUILT["DeityZhekra"]["img"].crop((0, 0, 29, 24)))
    S = 4
    H = max(c.size[1] for c in cells)
    W = sum(c.size[0] for c in cells) + 3 * len(cells) + 3
    bg = Image.new("RGBA", (W * S, (H + 4) * S), (28, 26, 32, 255))
    x = 3
    for i, c in enumerate(cells):
        is_portrait = i == len(cells) - 1 and "DeityZhekra" in BUILT
        y = 1 if is_portrait else H - c.size[1] + 1
        bg.alpha_composite(c.resize((c.size[0] * S, c.size[1] * S), Image.NEAREST), (x * S, y * S))
        x += c.size[0] + 3
    d = ImageDraw.Draw(bg)
    d.line([(0, (H - 1) * S + S // 2), (W * S - 31 * S, (H - 1) * S + S // 2)], fill=(60, 56, 64, 255))
    bg = bg.convert("RGB")
    bg.save(os.path.join(outdir, "contact_idle.png"))
    if extra_path: bg.save(extra_path)
    print("contact sheet", os.path.join(outdir, "contact_idle.png"), extra_path or "")


# ================================================================== main
CONTACT = os.path.join(ROOT, "build", "boards", "zhekra_contact.png")
TREE = os.path.join(ROOT, "build", "boards", "tree_zhekra.png")


def tree_sheet(path):
    """Every monster's Idle frame at 4x, one row per tier (T1 / T2 / T3 / minion), on a shared floor line."""
    if not path: return
    S = 4
    rows = []
    for tier in TIERS:
        cells = []
        for n in tier:
            b = BUILT.get(n)
            if not b: continue
            img, man = b["img"], b["man"]
            cw, chh = man["cellW"], man["cellH"]
            fi = man["anims"][0]["frames"][0]
            c = img.crop(((fi % man["cols"]) * cw, (fi // man["cols"]) * chh, (fi % man["cols"] + 1) * cw, (fi // man["cols"] + 1) * chh))
            bb = c.getbbox()
            cells.append(c.crop((bb[0] - 1, bb[1] - 1, bb[2] + 1, chh)))
        H = max(c.size[1] for c in cells) + 2
        W = sum(c.size[0] + 6 for c in cells) + 6
        row = Image.new("RGBA", (W, H), (28, 26, 32, 255))
        x = 6
        for c in cells:
            row.alpha_composite(c, (x, H - c.size[1]))
            x += c.size[0] + 6
        ImageDraw.Draw(row).line([(0, H - 2), (W, H - 2)], fill=(60, 56, 64, 255))
        rows.append(row)
    W = max(r.size[0] for r in rows); H = sum(r.size[1] + 4 for r in rows)
    bg = Image.new("RGBA", (W, H), (20, 18, 24, 255))
    y = 0
    for r in rows:
        bg.alpha_composite(r, (0, y)); y += r.size[1] + 4
    bg.resize((W * S, H * S), Image.NEAREST).convert("RGB").save(path)
    print("tree sheet", path)


def main():
    args = [a for a in sys.argv[1:]]
    outdir = args[0] if args and not args[0].startswith("-") else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    build_icons(outdir)


if __name__ == "__main__":
    main()
