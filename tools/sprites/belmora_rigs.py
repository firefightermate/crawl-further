"""BEL'MORA, THE DROWNED BELL: "The tide always returns".
Every sprite sheet for the Bel'Mora god pack: 7 monsters, 10 FX sheets, 4 item icons, god portrait.

    python3 belmora_rigs.py [outdir] [--only Name,Name]

Method (same family as sylvene_rigs.py): each monster is a pose function that draws shaded primitives
(ellipses, tapered tubes, polygons lit from the top-left) onto a fresh canvas, so every frame is a real
re-posed drawing. A finished pose gets a 1px deep-sea outline, then glow pixels (eyes, lures, throat)
are laid on top so they stay bright. Everything is wet: barnacle crust, kelp strands, drips, verdigris.
"""
HERE_DIR = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, PALETTE, pack, preview  # noqa: E402
import scalekit as SK  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_belmora")

# ------------------------------------------------------------------ palette (added at runtime, this pack only)
PALETTE.update({
    # v0.9: midtones lifted a step across the whole line (the pack averaged luminance 65-81 against vanilla's ~100)
    'Z': (0x16, 0x2a, 0x2e),   # abyss: outline / deepest shade
    'D': (0x28, 0x62, 0x68),   # drowned teal
    'd': (0x3e, 0x90, 0x8c),   # sea-green
    'E': (0x6c, 0xc2, 0xb6),   # foam teal
    'Q': (0xb0, 0xe8, 0xd8),   # wet highlight / spray
    'z': (0x36, 0x48, 0x4c),   # wet slate (barnacle shadow)
    'x': (0x5e, 0x70, 0x6e),   # wet stone grey
    'f': (0x90, 0x9e, 0x96),   # barnacle grey
    'H': (0xc4, 0xcc, 0xbc),   # barnacle lip
    'L': (0x30, 0x4c, 0x34),   # deep kelp
    'l': (0x6c, 0x86, 0x48),   # kelp highlight (olive)
    'J': (0x4a, 0x3c, 0x1e),   # bronze shadow
    'M': (0x74, 0x90, 0x86),   # drowned flesh mid
    'C': (0xac, 0xc4, 0xb4),   # drowned flesh light
    'j': (0x4e, 0x34, 0x42),   # bruise / gill purple-brown
})
GLOW = set("cBQ")

# material ramps, dark -> light
TEAL = "ZDdE"
TEAL_L = "DdEQ"
BRONZE = "JAew"
IRON = "Zzxf"
STONE = "zxfH"
FLESH = "zxMC"
KELP = "LvlL"
RUST = "tTa"
CRAB = "jpPPa"
URCH = "jnNN"       # v0.8: lifted a step (the urchin read as a black blot on the floor: Idle luminance 55)
FISH = "ZzDd"
SUIT = "Zktg"
RAGS = "ZzxM"

# ------------------------------------------------------------------ primitives
def pick(ramp, l):
    n = len(ramp)
    i = int((l + 1.0) * 0.5 * n)
    return ramp[max(0, min(n - 1, i))]


def P(x, y):
    return int(round(x)), int(round(y))


def ell(c, cx, cy, rx, ry, ramp, ang=0.0, bias=0.0, vmax=None, vmin=None, jit=0.0, seed=0, over=True, shader=None):
    """Filled ellipse lit from the top-left; ang rotates; vmax/vmin clip in local normalised v."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = int(max(rx, ry)) + 2
    rnd = random.Random(seed)
    for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)) + 1):
        for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R)) + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            nu, nv = u / max(rx, 0.5), v / max(ry, 0.5)
            d = nu * nu + nv * nv
            if jit: d += (rnd.random() - 0.5) * jit
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
    """Tapered shaded tube along a polyline. radii: per point."""
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
                dist = math.hypot(ox, oy)
                if dist > r + 0.15: continue
                l = bias if r < 0.75 else -(ox + oy) / (r * 1.414) * 0.9 + 0.15 + bias
                c.put(x, y, pick(ramp, l), over)


def line(c, x0, y0, x1, y1, ch, over=True):
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    for i, (x, y) in enumerate(pts):
        cc = ch[i % len(ch)] if len(ch) > 1 else ch
        c.put(x, y, cc, over)
    return pts


def chain(x, y, segs):
    pts = [(x, y)]
    for ln, a in segs:
        x += ln * math.cos(math.radians(a)); y += ln * math.sin(math.radians(a))
        pts.append((x, y))
    return pts


def curl(x, y, n, ln, a0, da, dda=0.0):
    segs = []; a = a0
    for i in range(n):
        segs.append((ln, a)); a += da + dda * i
    return chain(x, y, segs)


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
    ex, ey = sx + l1 * math.cos(ea), sy + l1 * math.sin(ea)
    return (ex, ey), (sx + d * math.cos(a), sy + d * math.sin(a))


def polyline(c, pts, ch, over=True):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        line(c, x0, y0, x1, y1, ch, over)


def barnacles(c, pts, seed=0, big=False):
    """Barnacle crust: pale lip, dark hole; only drawn onto existing body pixels.
    Small renders (design scale < 0.75) shrink each barnacle to a lip pixel over a hole pixel."""
    r = random.Random(seed)
    sc = getattr(c, "s", 1.0)
    if sc != 1.0:
        c, pts = c.raw, [SK.spt(x, y) for (x, y) in pts]
    for (x, y) in pts:
        x, y = P(x, y)
        if (x, y) not in c.px: continue
        if sc < 0.75:
            c.put(x, y, "H"); c.put(x, y + 1, "z")
            continue
        c.put(x, y, "H"); c.put(x + 1, y, "f"); c.put(x, y + 1, "f")
        c.put(x + 1, y + 1, "z")
        if big and r.random() < 0.6:
            c.put(x - 1, y + 1, "x"); c.put(x + 2, y + 1, "x")


def crust(c, region, n, seed, ramp="fHz"):
    """Speckle n barnacle grains onto the existing pixels in region (x0,y0,x1,y1)."""
    r = random.Random(seed)
    x0, y0, x1, y1 = region
    for _ in range(n * 4):
        if n <= 0: break
        x, y = r.randint(int(x0), int(x1)), r.randint(int(y0), int(y1))
        if (x, y) in c.px and (x + 1, y) in c.px and c.px[(x, y)] not in GLOW:
            c.put(x, y, ramp[1]); c.put(x + 1, y, ramp[2]); n -= 1


def kelp(c, x, y, n, sway, seed=0, cols="Lvl", over=True):
    """A hanging kelp strand from (x,y) downward, n px long, swaying."""
    pts = []
    for i in range(n):
        dx = sway * math.sin(i * 0.7 + seed) * (i / max(1, n))
        pts.append(P(x + dx, y + i))
    for i, (px_, py_) in enumerate(pts):
        c.put(px_, py_, cols[(i + seed) % len(cols)] if i < n - 1 else cols[0], over)


def drips(c, pts, ch="E"):
    for (x, y) in pts:
        c.put(*P(x, y), ch)


# ------------------------------------------------------------------ frame: body canvas + glow canvas
class Fr:
    def __init__(self):
        self.b = Canvas()   # outlined body
        self.g = Canvas()   # glow / fx pixels drawn over the outline
        self.u = Canvas()   # under-layer: drawn behind the body, also outlined (back limbs)
        self.n = Canvas()   # far layer: behind everything, no outline (far-side limbs in shadow)

    def done(self, outline=True, clip=True):
        base = dict(self.u.px)
        base.update(self.b.px)
        spr = Spr(base)
        if outline: spr = outl(spr)
        px = dict(self.n.px)
        px.update(spr.px)
        px.update(self.g.px)
        if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
        return Spr(px)


def outl(spr, ch="Z"):
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
    return recol(spr, {"c": "d", "B": "D", "Q": "E"})


# ------------------------------------------------------------------ sheet helpers
BUILT = {}


def sheet(name, anims, outdir, scale=6, pad=2):
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
    feet = (cw // 2, ch - 2)
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man}
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


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


# ================================================================== BELL URCHIN (T1)
def bell_tiny(c, x, y, glint=False):
    """3x4 brass bell; (x,y) = bottom centre."""
    x, y = P(x, y)
    for (a, b, ch) in ((0, -3, "A"), (-1, -2, "A"), (0, -2, "e"), (1, -2, "w"), (-1, -1, "A"), (0, -1, "e"),
                       (1, -1, "e"), (-1, 0, "J"), (0, 0, "Z"), (1, 0, "A")):
        c.put(x + a, y + b, ch)
    if glint: c.put(x + 1, y - 2, "X")


def urchin(dx=0.0, dy=0.0, rx=5.2, ry=4.6, slen=1.0, rot=0.0, sway=0.0, feet=0, eyes="open", ball=False,
           splay=0.0, bell=(1.0, 0.0), stubs=False, tilt=0.0, extra=None, nspines=18, bellglint=False, wet=0):
    f = Fr()
    cy = -(ry + 1.6) + dy
    cx = dx
    if ball:
        cy = -(rx + 2.6 * slen) - 0.5 + dy
    # spines (under the body). Angle 0 = right, 90 = down.
    for k in range(nspines):
        a = rot + k * 360.0 / nspines
        a_n = a % 360
        if not ball and 48 < a_n < 132:
            continue
        long_ = (k % 2 == 0)
        L = (3.0 if long_ else 1.6) * slen
        up = -math.sin(math.radians(a_n))           # +1 pointing up
        L *= 1.0 + 0.25 * max(0.0, up)
        aa = a_n + sway * (1 if k % 2 else -1) + splay * (1 if 270 > a_n > 90 else -1) * (0.4 + 0.6 * max(0, up))
        ca, sa = math.cos(math.radians(aa)), math.sin(math.radians(aa))
        r0 = 0.6
        x0, y0 = cx + ca * rx * r0, cy + sa * ry * r0
        er = 1.0 + (L / max(rx, 1))
        x1, y1 = cx + ca * (rx + L), cy + sa * (ry + L)
        lit = (ca + sa) < -0.3
        if stubs:
            x1, y1 = cx + ca * (rx + 1.2), cy + sa * (ry + 1.2)
        pts = line(f.u, x0, y0, x1, y1, "z")
        n = len(pts)
        for i, (px_, py_) in enumerate(pts):
            t = i / max(1, n - 1)
            f.u.put(px_, py_, ("f" if lit else "x") if t < 0.75 else ("H" if lit else "f"))
            if t < 0.55 and long_:   # stout base
                f.u.put(px_ + (1 if ca < 0.3 else 0), py_ + (1 if ca >= 0.3 else 0), "z", over=False)
        if not stubs and long_:
            f.u.put(*pts[-1], "Q" if lit else "E")
    # tube feet
    if not ball:
        fy = cy + ry - 0.5
        for i, fx in enumerate((-3.2, -1.2, 1.0, 3.0)):
            ph = ((feet or 0) + i) % 4
            xx = cx + fx + [0, 0.5, 0, -0.5][ph] * (1 if feet else 0)
            if fy + 1 < 0:
                line(f.u, cx + fx * 0.8, fy, xx, -1, "z")
            f.u.put(*P(xx, 0), "M" if i % 2 else "x")
    # body: dark violet test with teal-green tubercle rows
    band_off = (rot / 40.0) % 1.0
    def tex(nu, nv, d, l, ch, x, y):
        if d < 0.9:
            # ambulacral bands: meridians of teal tubercles that follow the curve of the test
            k = math.sqrt(max(0.0, 1 - nv * nv))
            if k > 0.2:
                m = (nu / k) * 1.25 + band_off
                if abs(m - round(m)) < 0.13 and (y % 2 == 0):
                    return "d" if l > 0.15 else "D"
        if l > 0.75 and d < 0.6: return "Q" if (x + y) % 3 == 0 else "n"
        return ch
    ell(f.b, cx, cy, rx, ry, URCH, ang=tilt, bias=0.18, shader=tex)
    # front spines over the body edge (a few short ones to break the outline)
    for k in range(5):
        a = rot + 200 + k * 34 + sway
        if not ball and 48 < (a % 360) < 132: continue
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        line(f.b, cx + ca * rx * 0.75, cy + sa * ry * 0.75, cx + ca * (rx + 0.6), cy + sa * (ry + 0.6), "x")
    # algae crust on top
    # the tiny bell nestled in the spines
    if bell is not None and not ball:
        bell_tiny(f.b, cx + bell[0], cy - ry + 1.5 + bell[1], bellglint)
    # eyes
    if not ball:
        ex, ey = cx + rx * 0.45 + math.cos(math.radians(tilt)) * 0.3, cy + 0.5
        if eyes == "open":
            f.g.put(*P(ex, ey), "c"); f.g.put(*P(ex + 2, ey), "c")
            f.g.put(*P(ex, ey + 1), "D"); f.g.put(*P(ex + 2, ey + 1), "D")
        elif eyes == "squint":
            f.g.put(*P(ex, ey), "E"); f.g.put(*P(ex + 2, ey), "E")
        elif eyes == "wide":
            for (a, b) in ((0, 0), (2, 0)):
                f.g.put(*P(ex + a, ey + b), "c"); f.g.put(*P(ex + a, ey + b - 1), "Q")
        elif eyes == "dead":
            f.g.put(*P(ex, ey), "z"); f.g.put(*P(ex + 2, ey), "z")
    else:
        # the eyes flash past as it rolls
        a = math.radians(rot + 30)
        f.g.put(*P(cx + math.cos(a) * rx * 0.55, cy + math.sin(a) * ry * 0.55), "c")
    for i in range(wet):
        f.g.put(*P(cx - rx + 1 + i * 3, cy + ry + 1 + (i % 2)), "E")
    if extra: extra(f, cx, cy)
    return f.done()


def spine_streaks(n, r0, r1, cy=-7.5, skip=(48, 132)):
    def fn(f, cx, _cy):
        for k in range(n):
            a = k * 360.0 / n + 10
            if skip[0] < a % 360 < skip[1]: continue
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            pts = line(f.g, cx + ca * r0, cy + sa * r0 * 0.85, cx + ca * r1, cy + sa * r1 * 0.85, "x")
            f.g.put(*pts[-1], "Q")
            if len(pts) > 2: f.g.put(*pts[-2], "f")
    return fn


def urchin_corpse(stage=2):
    f = Fr()
    # cracked, flattened test, spines snapped and strewn, bell rolled out
    ell(f.b, -1, -2.2, 6.0, 2.6, URCH, bias=0.0, vmax=1.0)
    for x in range(-6, 5, 2):
        line(f.b, x, -3, x - 1 - (x % 3), -5 + (x % 2), "x")
    f.b.put(-3, -4, "Z"); f.b.put(-2, -3, "Z"); f.b.put(-1, -4, "Z"); f.b.put(1, -3, "Z")  # crack
    crust(f.b, (-6, -4, 4, -1), 3, seed=5, ramp="zfH")
    for (x0, y0, x1, y1) in ((-10, 0, -8, -1), (6, 0, 9, 0), (-8, -1, -9, 0)):
        line(f.b, x0, y0, x1, y1, "x")
    bell_tiny(f.b, 7, 0)
    f.g.put(2, -2, "z"); f.g.put(4, -2, "z")
    return f.done()


def build_urchin(outdir):
    def U(**k):
        k["rx"] = k.get("rx", 5.2) + 0.9; k["ry"] = k.get("ry", 4.6) + 0.5
        return urchin(**k)
    idle = [U(sway=0, feet=0),
            U(sway=4, feet=1, ry=4.3, dy=0.3, rx=5.4),
            U(sway=6, feet=2, ry=4.3, dy=0.3, rx=5.4, eyes="squint", bellglint=True),
            U(sway=2, feet=3, ry=4.8, dy=-0.3)]
    run = [U(feet=i % 4, dx=[0, 0.5, 1, 0.5, 0, -0.3][i], dy=[0, -1, -1.4, -0.6, 0, 0][i], tilt=[-4, -8, -6, -2, 0, -3][i],
             sway=[-6, -10, -6, -2, 2, -2][i], ry=[4.6, 4.9, 5, 4.6, 4.2, 4.5][i], rx=[5.2, 5.0, 5, 5.2, 5.6, 5.3][i])
           for i in range(6)]
    # ROLL: crouch, curl, 4 rolling frames, uncurl
    def trail(n):
        def fn(f, cx, cy):
            for i in range(n):
                f.g.put(*P(cx - 9 - i * 2, cy + 3 - (i % 2) * 2), "d" if i else "E")
                f.g.put(*P(cx - 8 - i * 2, cy + 6.5), "D")
        return fn
    roll = [U(ry=3.8, rx=5.8, dy=0.6, sway=-10, splay=10, feet=2, eyes="squint", tilt=-8),
            U(ry=5.0, rx=5.0, dy=-0.5, sway=-4, splay=-8, slen=0.85, feet=0, tilt=-20, eyes="squint", nspines=17),
            U(ball=True, rot=0, slen=0.9, nspines=16, extra=trail(2)),
            U(ball=True, rot=22.5, slen=0.9, nspines=16, extra=trail(3)),
            U(ball=True, rot=45, slen=0.9, nspines=16, extra=trail(3)),
            U(ball=True, rot=67.5, slen=0.9, nspines=16, extra=trail(2)),
            U(ry=4.2, rx=5.6, dy=0.4, sway=8, splay=6, feet=1, tilt=6, eyes="open")]
    # BRISTLE: shrink, puff, max puff (trembling), FIRE ring, stubs, regrow
    bristle = [U(rx=4.6, ry=4.0, slen=0.6, sway=0, eyes="squint", feet=2),
               U(rx=5.8, ry=5.4, slen=1.25, sway=-3, splay=-6, eyes="wide", feet=0, dy=-0.5),
               U(rx=6.2, ry=5.8, slen=1.45, sway=4, splay=-10, eyes="wide", feet=1, dy=-0.8, bellglint=True),
               U(rx=5.6, ry=5.0, slen=0.4, stubs=True, eyes="wide", feet=0, extra=spine_streaks(12, 9, 13)),
               U(rx=5.2, ry=4.6, slen=0.3, stubs=True, eyes="open", feet=1, extra=spine_streaks(12, 15, 17)),
               U(rx=5.2, ry=4.6, slen=0.7, sway=2, eyes="open", feet=3)]
    death = [U(sway=12, splay=14, eyes="wide", tilt=-14, ry=5, dy=-0.5, feet=0),
             U(sway=-8, splay=20, eyes="squint", tilt=-22, ry=3.6, rx=5.8, dy=0.8, slen=0.8, feet=2),
             grounded(U(sway=-14, splay=26, eyes="dead", tilt=-30, ry=2.8, rx=6.2, dy=1.4, slen=0.6, feet=None, bell=(4, 1))),
             urchin_corpse()]
    knock = U(sway=-12, splay=16, eyes="squint", tilt=-18, dx=-0.5, feet=1)
    anims = [("Idle", idle, [0.2, 0.16, 0.22, 0.16]), ("Run", run, [0.08] * 6),
             ("Roll", roll, [0.14, 0.12, 0.06, 0.06, 0.06, 0.06, 0.16]),
             ("Bristle", bristle, [0.14, 0.14, 0.18, 0.06, 0.12, 0.16])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelUrchin", anims, outdir, scale=7)


# ================================================================== LUREFISH (T1)
def lure_glow(c, x, y, glow):
    """Lure bulb: bright core, cyan ring, halo specks at higher glow levels."""
    x, y = P(x, y)
    if glow <= 0:
        c.put(x, y, "E"); c.put(x + 1, y, "d"); c.put(x, y + 1, "d"); c.put(x + 1, y + 1, "D")
        return
    for (a, b) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        c.put(x + a, y + b, "c")
    for (a, b) in ((-1, 0), (2, 0), (0, -1), (1, -1), (-1, 1), (2, 1), (0, 2), (1, 2)):
        c.put(x + a, y + b, "B" if glow >= 2 else "Q")
    if glow >= 2:
        for (a, b) in ((-2, -2), (3, -2), (-2, 3), (3, 3), (-3, 0), (4, 1), (1, -3), (0, 4)):
            c.put(x + a, y + b, "E" if glow >= 3 else "D", over=False)
    if glow >= 3:
        for (a, b) in ((-3, -3), (4, -3), (-4, 1), (5, 0), (1, -4), (0, 5), (-2, 4), (4, 4)):
            c.put(x + a, y + b, "D", over=False)


def lurefish(dx=0.0, dy=0.0, tilt=0.0, gape=0.0, lure_a=-95.0, lure_c=26.0, glow=1, legs=(0.0, 0.0), lift=(0, 0),
             tail=0.0, eye="open", sq=0.0, extra=None, belly_up=False):
    f = Fr()
    rx, ry = 7.2 - sq * 0.5, 5.4 + sq
    cx, cy = dx - 1.0, -(ry + 3.6) + dy
    t = math.radians(tilt)
    def rot(x, y):  # rotate body-local point around the body centre
        return cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)
    # stubby fin-legs (back leg under, front leg in front)
    for i, (hx, ang, lf) in enumerate(((-3.0, legs[0], lift[0]), (2.4, legs[1], lift[1]))):
        hip = rot(hx, ry - 1.2)
        fx, fy = hip[0] + 2.6 * math.sin(math.radians(ang)), -0.6 - lf
        cv_ = f.u if i == 0 else f.b
        tube(cv_, [hip, (fx, fy - 0.6)], [1.4, 0.9], "ZzD" if i == 0 else FISH)
        line(cv_, fx - 1.5, fy + 0.4, fx + 1.8, fy + 0.4, "Dd" if i else "zD")
        cv_.put(*P(fx + 2.2, fy), "D" if i else "z")
    # tail fin (rays) behind
    tb = rot(-rx + 0.8, -0.5)
    for k, a in enumerate((-150, -170, 170, 150)):
        aa = a + tail * 12
        e = (tb[0] + 5 * math.cos(math.radians(aa)), tb[1] + 5 * math.sin(math.radians(aa)) * 0.9)
        line(f.u, tb[0], tb[1], e[0], e[1], "zDd" if k % 2 else "zD")
    poly(f.u, [tb, (tb[0] - 5 * math.cos(math.radians(30 - tail * 12)), tb[1] - 3.5 + tail),
               (tb[0] - 4.5, tb[1] + 3.5 + tail)], "D", over=False)
    # body (cranium); the lower-front wedge belongs to the jaw and is cut out here
    hl = (-2.2, 1.0)                      # hinge, body-local
    sl = (rx + 0.3, -0.6)                 # snout corner, body-local
    def under_lip(lx, ly):
        if lx < hl[0]: return False
        yl = hl[1] + (sl[1] - hl[1]) * (lx - hl[0]) / (sl[0] - hl[0])
        return ly > yl
    def skin(nu, nv, d, l, ch, x, y):
        lx, ly = (x - cx) * math.cos(t) + (y - cy) * math.sin(t), -(x - cx) * math.sin(t) + (y - cy) * math.cos(t)
        if under_lip(lx, ly): return None
        if nv > 0.35 and nu > -0.6: ch = pick("zxM", l + 0.2)      # paler belly
        r = (x * 7 + y * 13) % 11
        if r == 0 and d < 0.85 and nv < 0.3: return "x"           # mottling
        if l > 0.7 and d < 0.5: return "d"
        return ch
    ell(f.b, cx, cy, rx, ry, FISH, ang=tilt, bias=0.08, shader=skin)
    # dorsal ridge: small spines
    for k in range(4):
        b0 = rot(-4.5 + k * 1.8, -ry + 0.6)
        line(f.b, b0[0], b0[1], b0[0] - 0.8, b0[1] - 1.8 + (k % 2) * 0.6, "zx")
    barnacles(f.b, [rot(-3.5, -ry + 1.6), rot(-1, -ry + 1.2), rot(-5.5, -2.5)], seed=2)
    # lower jaw: a heavy underbite scoop pivoting on the hinge
    g = math.radians(gape)
    def jrot(x, y):  # body-local jaw point rotated by gape about the hinge, then to world
        ox, oy = x - hl[0], y - hl[1]
        return rot(hl[0] + ox * math.cos(g) - oy * math.sin(g), hl[1] + ox * math.sin(g) + oy * math.cos(g))
    jaw_local = [(hl[0], hl[1]), (rx + 2.4, -1.8), (rx + 1.8, 1.0), (rx - 1.5, ry - 1.0), (0.0, ry - 0.2), (-3.2, ry - 1.2)]
    jaw = [jrot(*p_) for p_ in jaw_local]
    hinge, tip = rot(*hl), jaw[1]
    snout = rot(*sl)
    if gape > 4:
        poly(f.b, [rot(hl[0] - 0.5, hl[1]), (snout[0] + 0.5, snout[1] + 0.5), (tip[0], tip[1]), jrot(2.0, 1.2)], "j")
        poly(f.b, [rot(hl[0] + 1, hl[1] + 0.3), (snout[0] - 1, snout[1] + 1.5), jrot(rx - 1, 0.5)], "Z")
    jx0 = min(p_[0] for p_ in jaw); jy0 = min(p_[1] for p_ in jaw); jy1 = max(p_[1] for p_ in jaw)
    def jshade(x, y):
        v = (y - jy0) / max(1.0, jy1 - jy0)
        return pick("CMxz", -1.2 + 2 * v + (0.3 if x < hinge[0] + 2 else 0))
    poly(f.b, jaw, "M", shade=jshade)
    # teeth: lower fangs stand up from the jaw lip, upper fangs hang from the cranium
    for k, (tt, h) in enumerate(((0.45, 1), (0.68, 2), (0.95, 2))):
        bx, by = jaw[0][0] + (jaw[1][0] - jaw[0][0]) * tt, jaw[0][1] + (jaw[1][1] - jaw[0][1]) * tt
        nx, ny = math.sin(g + t), -math.cos(g + t)
        for j in range(1, h + 1):
            f.b.put(*P(bx + nx * j, by + ny * j - 0.3), "H")
    for k, (tt, h) in enumerate(((0.5, 1), (0.8, 2))):
        ux, uy = hinge[0] + (snout[0] - hinge[0]) * tt, hinge[1] + (snout[1] - hinge[1]) * tt
        for j in range(1, h + 1):
            f.b.put(*P(ux - math.sin(t) * j, uy + math.cos(t) * j), "H" if j == h else "f")
    if gape > 4:  # tongue / gullet glint
        f.b.put(*P(*jrot(1.5, 0.4)), "p")
    # eye: small, high, glowing pale cyan
    ex, ey = rot(2.8, -2.2)
    if eye == "open":
        f.g.put(*P(ex, ey), "c"); f.g.put(*P(ex + 1, ey), "Q"); f.g.put(*P(ex, ey - 1), "Z"); f.g.put(*P(ex + 1, ey - 1), "Z")
    elif eye == "wide":
        f.g.put(*P(ex, ey), "c"); f.g.put(*P(ex + 1, ey), "c"); f.g.put(*P(ex, ey - 1), "Q"); f.g.put(*P(ex + 1, ey - 1), "Q")
    elif eye == "squint":
        f.g.put(*P(ex, ey), "E"); f.g.put(*P(ex + 1, ey), "E")
    else:
        f.g.put(*P(ex, ey), "z"); f.g.put(*P(ex + 1, ey), "x")
    # lure stalk from the forehead, arcing forward over the jaws
    base = rot(3.4, -ry + 0.8)
    pts = curl(base[0], base[1], 4, 2.4, lure_a + tilt, lure_c)
    polyline(f.b, pts, "x")
    for (x, y) in pts[1:-1]: f.b.put(*P(x, y), "f")
    lx, ly = pts[-1]
    lure_glow(f.g, lx - 0.5, ly, glow)
    if extra: extra(f, cx, cy, (lx, ly), tip)
    return f.done()


def lurefish_corpse(stage):
    f = Fr()
    if stage == 1:
        # mid-roll: on its side, fins splayed, lure still flickering
        ell(f.b, -1, -5.2, 7.2, 4.6, FISH, ang=-12, bias=0.05)
        ell(f.b, 0, -3.0, 6.0, 2.4, "zxMC", ang=-12, bias=0.1)
        for k, a in enumerate((-150, -175, 165)):
            line(f.b, -8, -6, -8 + 4 * math.cos(math.radians(a)), -6 + 3 * math.sin(math.radians(a)), "zD")
        tube(f.b, [(3, -5), (6.5, -3.5), (8.5, -1.5)], [1.7, 1.5, 1.0], "zxM")
        for x in (5, 7): f.b.put(x, -5 + (x == 7), "H")
        tube(f.b, [(-2, -2), (-4, -0.5)], [1.0, 0.8], FISH)
        tube(f.b, [(1, -9), (2.5, -11.5)], [0.9, 0.8], FISH)
        line(f.b, 1.5, -12, 3.5, -12, "D")
        polyline(f.b, [(3, -9), (6, -10), (9, -8), (10, -6)], "x")
        lure_glow(f.g, 10, -6, 1)
        f.g.put(3, -7, "z"); f.g.put(4, -7, "x")
        barnacles(f.b, [(-4, -8), (-1, -9)], seed=4)
        return f.done()
    # belly-up on the floor, jaw hanging, lure limp across the ground
    ell(f.b, -1, -4.4, 7.4, 4.0, "zxMC", bias=0.0)
    ell(f.b, -1, -2.2, 7.6, 2.3, FISH, bias=-0.1)
    for k, a in enumerate((-160, 180, 160)):
        line(f.b, -8, -3, -8 + 4 * math.cos(math.radians(a)), -3 + 3 * math.sin(math.radians(a)), "zD")
    tube(f.b, [(3, -3), (6, -2.5), (8.5, -1.2)], [1.6, 1.4, 1.0], "zxM")
    for x in (5, 7): f.b.put(x, -4, "H")
    tube(f.b, [(-3, -8), (-3.5, -10)], [0.9, 0.8], FISH)
    tube(f.b, [(1.5, -8), (2.5, -10)], [0.9, 0.8], FISH)
    line(f.b, -4.5, -10.5, -2.5, -10.5, "D"); line(f.b, 1.5, -10.5, 3.5, -10.5, "D")
    pts = [(4, -1), (7, -1), (9, 0), (11, 0)]
    polyline(f.b, pts, "x")
    lure_glow(f.g, 12, -1, 0)
    f.g.put(3, -2, "x"); f.g.put(4, -2, "z")
    barnacles(f.b, [(-4, -2), (0, -1)], seed=4)
    return f.done()


def build_lurefish(outdir):
    L = lurefish
    idle = [L(lure_a=-95, lure_c=26, glow=1, tail=0),
            L(lure_a=-92, lure_c=28, glow=2, tail=0.5, sq=-0.3, dy=0.3, gape=6),
            L(lure_a=-90, lure_c=30, glow=1, tail=1, sq=-0.3, dy=0.3, gape=8),
            L(lure_a=-96, lure_c=24, glow=1, tail=0.4, eye="squint")]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(L(dx=0.5, dy=-abs(math.sin(ph)) * 1.2, tilt=6 + 3 * math.sin(ph), legs=(-35 * math.cos(ph), 35 * math.cos(ph)),
                     lift=(max(0, 1.5 * math.sin(ph)), max(0, -1.5 * math.sin(ph))), tail=math.sin(ph + 1) * 1.2,
                     lure_a=-80 - 8 * math.sin(ph + 0.8), lure_c=20 + 6 * math.cos(ph), glow=1, gape=4))
    # CHOMP
    def bite_fx(n):
        def fn(f, cx, cy, lure, tip):
            for k in range(n):
                f.g.put(*P(tip[0] + 2 + k, tip[1] - 3 + (k % 2) * 2), "Q" if k % 2 else "E")
        return fn
    chomp = [L(dx=-1, tilt=-10, gape=18, legs=(-20, -10), lure_a=-110, lure_c=22, eye="wide"),
             L(dx=-1.5, dy=-0.5, tilt=-16, gape=46, legs=(-30, -25), lure_a=-120, lure_c=18, eye="wide"),
             L(dx=3, dy=-1.5, tilt=4, gape=52, legs=(-40, 30), lift=(1, 0), lure_a=-140, lure_c=14, eye="wide"),
             L(dx=4.5, tilt=10, gape=0, legs=(-45, 35), lure_a=-150, lure_c=12, eye="squint", extra=bite_fx(4)),
             L(dx=3.5, tilt=6, gape=4, legs=(-30, 25), lure_a=-125, lure_c=20, eye="squint", extra=bite_fx(2)),
             L(dx=1, tilt=0, gape=6, legs=(-10, 5), lure_a=-100, lure_c=24)]
    # LURE: lift lure, swing it bright (channel), snap, recover
    def pull(n, ph):
        def fn(f, cx, cy, lure, tip):
            # current streaks drawn toward the jaws
            for k in range(n):
                x = tip[0] + 5 + k * 4 + ph
                y = tip[1] - 2 + ((k + ph) % 3) - 1
                line(f.g, x, y, x + 2, y, "D" if k > 1 else "d", over=False)
                f.g.put(*P(x - 1, y), "E", over=False)
        return fn
    swing = [(-70, 30), (-55, 34), (-75, 28), (-60, 36), (-50, 30)]
    lure = [L(lure_a=-120, lure_c=18, glow=1, gape=4, tilt=-4, eye="squint")]
    for i, (a, cc) in enumerate(swing):
        lure.append(L(lure_a=a, lure_c=cc, glow=3 if i % 2 == 0 else 2, gape=18 + 6 * (i % 2), tilt=-6 + i,
                      tail=0.6 * math.sin(i), legs=(-15, 10), eye="wide", extra=pull(3, i % 3)))
    lure += [L(dx=2.5, tilt=8, gape=0, lure_a=-140, lure_c=14, glow=1, legs=(-40, 30), eye="squint", extra=bite_fx(4)),
             L(dx=0.5, tilt=2, gape=6, lure_a=-100, lure_c=24, glow=1, legs=(-10, 5))]
    death = [L(dx=-1, tilt=-18, gape=30, eye="wide", lure_a=-160, lure_c=10, glow=2, legs=(30, 40), lift=(1, 1)),
             L(dx=-1.5, dy=1, tilt=-40, gape=20, eye="dead", lure_a=-170, lure_c=-10, glow=0, legs=(60, 70), sq=-0.8),
             lurefish_corpse(1),
             lurefish_corpse(2)]
    knock = L(dx=-1, tilt=-14, gape=12, eye="squint", lure_a=-150, lure_c=6, glow=1, legs=(25, 35), lift=(1, 0))
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.08] * 6),
             ("Chomp", chomp, [0.14, 0.12, 0.07, 0.06, 0.1, 0.14]),
             ("Lure", lure, [0.14, 0.16, 0.16, 0.16, 0.16, 0.16, 0.06, 0.16])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelLurefish", anims, outdir, scale=6)


# ================================================================== BARNACLE CRAB (T1)
def crab_claw(c, sx, sy, a1, a2, open_, big=1.0, ramp=CRAB):
    """Big crusher claw: elbowed arm from the shoulder, fat palm, and two long prongs (fixed lower finger,
    hinged upper dactyl) with a dark gap between them. a1: arm angle, a2: claw direction, open_: degrees.
    Returns the point between the finger tips."""
    ex, ey = sx + 2.5 * big * math.cos(math.radians(a1 + 40)), sy + 2.5 * big * math.sin(math.radians(a1 + 40))
    wx, wy = ex + 2.5 * big * math.cos(math.radians(a1 - 25)), ey + 2.5 * big * math.sin(math.radians(a1 - 25))
    tube(c, [(sx, sy), (ex, ey)], [0.9 * big, 0.9 * big], "Zjp")
    tube(c, [(ex, ey), (wx, wy)], [0.9 * big, 1.2 * big], "jpP")
    c.put(*P(ex, ey - 1), "P")
    d = math.radians(a2)
    ux, uy = math.cos(d), math.sin(d)
    nx, ny = -uy, ux                       # "down" side of the claw
    pcx, pcy = wx + 2.2 * big * ux, wy + 2.2 * big * uy
    ell(c, pcx, pcy, 3.0 * big, 2.5 * big, ramp, ang=a2, bias=0.3)
    c.put(*P(pcx - 1.0 * ux - 1.2 * nx, pcy - 1.0 * uy - 1.2 * ny), "a")      # wet glint on the palm
    hx, hy = pcx + 2.4 * big * ux, pcy + 2.4 * big * uy
    tips, roots = [], []
    for k, (ang, off, rr) in enumerate(((a2 + 6, 1.1, "ZjpP"), (a2 - 8 - open_, -1.1, "jpPa"))):
        bx, by = hx + off * big * nx, hy + off * big * ny
        aa = math.radians(ang)
        mx, my = bx + 2.6 * big * math.cos(aa), by + 2.6 * big * math.sin(aa)
        ta = aa + (-0.75 if k == 0 else 0.75)
        tx, ty = mx + 2.0 * big * math.cos(ta), my + 2.0 * big * math.sin(ta)
        tube(c, [(bx, by), (mx, my), (tx, ty)], [1.3 * big, 0.95 * big, 0.45], rr, bias=0.2)
        c.put(*P(tx, ty), "H")
        tips.append((tx, ty)); roots.append((mx, my))
    if open_ > 8:   # dark gap inside the pincer
        poly(c, [(hx + 0.5 * ux, hy + 0.5 * uy), roots[0], tips[0], tips[1], roots[1]], "Z", over=False)
    return ((tips[0][0] + tips[1][0]) / 2, (tips[0][1] + tips[1][1]) / 2)


def crab(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, claw=(-40, -10, 25), small=(60, 120), eyes=1.0, eye="open", hunker=0.0,
         lift=0.0, extra=None, shell_sq=0.0, bubble=None):
    f = Fr()
    rx, ry = 7.8 + shell_sq * 0.5, 4.4 - shell_sq * 0.6
    leg_h = 3.4 * (1 - hunker)
    cx, cy = dx - 1.0, -(ry + leg_h + 0.6) + dy
    # spindly walking legs arching up from the rim: three trail behind, two splay under the claw.
    # near legs are outlined; the far set sits in shadow behind them (no outline).
    for side, layer in ((0, f.n), (1, f.b)):
        specs = [(-1, k, -7.6 - 2.3 * k) for k in range(3)] + [(1, k, 6.0 + 2.6 * k) for k in range(2)]
        for (dr, k, fo) in specs:
            ph = legs + (k + (3 if dr > 0 else 0)) * 2.1 + side * math.pi
            root = (cx + dr * (rx * 0.45 + k * 0.6) - (1 - side) * 1.4 * dr, cy + ry * 0.45)
            up = (1 - hunker) * (2.2 + 0.3 * k) + 1.0 * max(0.0, math.sin(ph))
            knee = (root[0] + dr * (2.6 + 1.0 * k), root[1] - up)
            fx = cx + fo + 1.2 * math.sin(ph) - (1 - side) * 1.6 * dr
            fy = -max(0.0, 1.4 * math.cos(ph)) - lift
            if hunker > 0.6:
                fx = cx + (fx - cx) * 0.75; fy = 0; knee = (root[0] + dr * 2, root[1] - 0.5)
            if side:
                line(layer, root[0], root[1], knee[0], knee[1], "p")
                line(layer, knee[0], knee[1], fx, fy, "p")
                layer.put(*P(*knee), "P"); layer.put(*P(fx, fy), "f")
            else:
                line(layer, root[0], root[1], knee[0], knee[1], "j")
                line(layer, knee[0], knee[1], fx, fy, "j")
                layer.put(*P(fx, fy), "x")
    # small claw tucked on the far side
    if hunker < 0.7:
        crab_claw(f.u, cx + 3, cy + 2, small[0], small[1], 6, big=0.5, ramp="ZkpP")
    # shell: barnacle crusted dome
    def shell(nu, nv, d, l, ch, x, y):
        if nv > 0.55: return pick("Zj", l)
        return ch
    ell(f.b, cx, cy, rx, ry, CRAB, ang=tilt, bias=0.1, shader=shell, vmax=0.95)
    # rim teeth along the front edge
    for k in range(3):
        f.b.put(*P(cx + rx - 1 - k * 1.5, cy - ry * 0.6 + k * 0.4 - 0.6), "P")
    barnacles(f.b, [(cx - 4, cy - 2.8), (cx - 1.5, cy - 3.8), (cx - 5.5, cy - 0.8), (cx + 1.2, cy - 3.0)], seed=3, big=True)
    crust(f.b, (cx - rx, cy - ry, cx, cy), 3, seed=9, ramp="zfH")
    kelp(f.b, int(cx - rx + 1), int(cy + 1), 3, 0.5, seed=1)
    kelp(f.b, int(cx - rx + 3), int(cy + 2), 2, 0.5, seed=2)
    # eye stalks
    if eyes > 0.15:
        for k, ox in enumerate((2.4, 4.6)):
            bx, by = cx + ox, cy - ry + 1
            h = 2.6 * eyes
            line(f.b, bx, by, bx + 0.4, by - h, "jp")
            ex, ey = P(bx + 0.4, by - h - 0.6)
            if eye == "open": f.g.put(ex, ey, "c"); f.g.put(ex, ey - 1, "Q")
            elif eye == "squint": f.g.put(ex, ey, "E")
            elif eye == "wide": f.g.put(ex, ey, "c"); f.g.put(ex, ey - 1, "c"); f.g.put(ex + 1, ey, "Q")
            else: f.g.put(ex, ey, "x")
    else:
        # peeking from under the shell rim
        if eye != "dead":
            f.g.put(*P(cx + rx - 1.5, cy + ry * 0.6), "E"); f.g.put(*P(cx + rx - 3, cy + ry * 0.6), "D")
    # big claw on the near side
    tip = None
    if hunker < 0.7:
        tip = crab_claw(f.b, cx + rx - 0.8, cy + 1.4, claw[0], claw[1], claw[2], big=1.0, ramp="jpPa")
    else:
        # claw folded flat across the front like a door
        ell(f.b, cx + rx - 1.5, cy + 1.5, 3.4, 2.4, CRAB, ang=-10, bias=0.15)
        line(f.b, cx + rx - 4, cy + 2.2, cx + rx + 1.5, cy + 1.6, "K")
        barnacles(f.b, [(cx + rx - 2, cy + 0.5)], seed=11)
    if bubble:
        for (bx, by) in bubble:
            f.g.put(*P(cx + bx, cy + by), "Q"); f.g.put(*P(cx + bx + 1, cy + by), "E", over=False)
    if extra: extra(f, cx, cy, tip)
    return f.done()


def crab_corpse():
    f = Fr()
    # flipped on its back: pale underside up, legs curled in the air, claw splayed on the floor
    ell(f.b, -1, -3.2, 7.4, 3.4, "kpPa", bias=0.0, vmin=-1.0)
    ell(f.b, -1, -4.6, 6.0, 2.0, "pPaT", bias=0.2)
    for k in range(4):
        x = -5 + k * 2.6
        pts = [(x, -6), (x - 1 + (k % 2) * 2, -8.5), (x + (1 if k % 2 else -1), -9.5)]
        polyline(f.b, pts, "kP")
    barnacles(f.b, [(-6, -1.5), (-2, -1), (2, -1.2)], seed=13)
    crab_claw(f.b, 5, -2, 10, 20, 30, big=0.9)
    f.g.put(7, -6, "x")
    return f.done()


def build_crab(outdir):
    C = crab
    idle = [C(claw=(-70, -18, 30), eyes=1.0),
            C(claw=(-66, -12, 38), eyes=1.0, dy=0.4, shell_sq=0.2, legs=0.3),
            C(claw=(-64, -8, 40), eyes=0.85, dy=0.4, shell_sq=0.2, legs=0.5, eye="squint"),
            C(claw=(-73, -22, 22), eyes=1.1, legs=0.2)]
    run = [C(legs=i * math.pi / 3, dy=-0.6 * abs(math.sin(i * math.pi / 3)), tilt=2 * math.sin(i * math.pi / 3),
             claw=(-78 + 8 * math.sin(i * math.pi / 3), -24 + 6 * math.sin(i * math.pi / 3), 26 + 10 * math.cos(i * math.pi / 3)), eyes=1.0 - 0.1 * (i % 2))
           for i in range(6)]
    def snap_fx(n):
        def fn(f, cx, cy, tip):
            if tip is None: return
            for k, (a, b) in enumerate(((2, -2), (3, 0), (2, 2), (4, -3), (4, 2))[:n]):
                f.g.put(*P(tip[0] + a, tip[1] + b), "Q" if k % 2 == 0 else "E")
        return fn
    pinch = [C(claw=(-95, -55, 34), tilt=-4, dx=-0.5, eye="wide", legs=0.4),
             C(claw=(-120, -95, 52), tilt=-8, dx=-1.2, dy=0.4, eye="wide", legs=0.8, shell_sq=0.3),
             C(claw=(-30, -8, 55), tilt=4, dx=1.5, legs=1.6, eye="wide"),
             C(claw=(-10, 8, -6), tilt=6, dx=2.2, legs=2.0, eye="squint", extra=snap_fx(5)),
             C(claw=(-14, 4, -6), tilt=4, dx=1.8, legs=2.0, eye="squint", extra=snap_fx(2)),
             C(claw=(-65, -18, 16), tilt=0, dx=0.4, legs=1.0)]
    shell = [C(hunker=0.45, eyes=0.4, claw=(10, 70, 0), eye="squint", legs=0.4, shell_sq=0.3),
             C(hunker=1.0, eyes=0, dy=0.2, shell_sq=0.4, eye="squint", bubble=[(3, -7)]),
             C(hunker=1.0, eyes=0, dy=0.0, shell_sq=0.2, eye="squint", bubble=[(3.5, -9.5), (1, -6.5)]),
             C(hunker=1.0, eyes=0, dy=0.2, shell_sq=0.4, eye="squint", bubble=[(4, -12), (1.5, -9)]),
             C(hunker=1.0, eyes=0, dy=0.0, shell_sq=0.3, eye="open", bubble=[(2, -11.5)]),
             C(hunker=0.25, eyes=0.8, claw=(-60, -10, 24), dy=-0.5, eye="open", legs=1.0)]
    death = [C(claw=(-120, -80, 40), tilt=-12, eye="wide", dx=-0.5, legs=1.0),
             C(claw=(-150, 160, 30), tilt=-28, dy=0.5, eye="dead", eyes=0.6, legs=2.0, lift=0.5),
             grounded(C(claw=(170, 120, 20), tilt=-150, eyes=0.5, eye="dead", hunker=0.5, legs=2.5)),
             crab_corpse()]
    knock = C(claw=(-130, -70, 35), tilt=-14, dx=-0.6, eye="squint", legs=0.8, lift=0.6)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.07] * 6),
             ("Pinch", pinch, [0.14, 0.14, 0.07, 0.06, 0.12, 0.14]),
             ("Shell", shell, [0.1, 0.3, 0.3, 0.3, 0.3, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelCrab", anims, outdir, scale=6)


# ================================================================== BELL DIVER (T2)
def anchor(c, gx, gy, ang, L=12.5, ring=True, smear=False):
    """Rusty anchor gripped at (gx,gy); ang = direction from the grip to the crown (deg).
    Returns the crown point."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    top = (gx - 2.0 * ux, gy - 2.0 * uy)
    crown = (gx + L * ux, gy + L * uy)
    tube(c, [top, crown], [1.0, 1.1], IRON, bias=0.1)
    # stock (cross bar) near the top
    sx, sy = gx - 0.6 * ux, gy - 0.6 * uy
    line(c, sx - 3 * nx, sy - 3 * ny, sx + 3 * nx, sy + 3 * ny, "x")
    c.put(*P(sx - 3 * nx, sy - 3 * ny), "f"); c.put(*P(sx + 3 * nx, sy + 3 * ny), "z")
    if ring:
        rx_, ry_ = top[0] - 1.2 * ux, top[1] - 1.2 * uy
        for k in range(8):
            t = k * math.pi / 4
            c.put(*P(rx_ + 1.3 * math.cos(t), ry_ + 1.3 * math.sin(t)), "x" if k % 2 else "z")
    # flukes: a heavy "smile" of iron curving up from the crown, pointed palms at both ends
    R = 4.2 * L / 12.0
    Cx, Cy = crown[0] - R * ux, crown[1] - R * uy
    for sd in (-1, 1):
        pts = []
        for k in range(7):
            th = math.radians(sd * 115 * k / 6)
            pts.append((Cx + R * (math.cos(th) * ux - math.sin(th) * nx), Cy + R * (math.cos(th) * uy - math.sin(th) * ny)))
        tube(c, pts, [1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.6], IRON, bias=0.05)
        tx, ty = pts[-1]; px0, py0 = pts[-2]
        # barb: a pixel flaring outward from the tip
        ox, oy = tx - Cx, ty - Cy
        on = math.hypot(ox, oy) or 1
        c.put(*P(tx + ox / on * 1.2, ty + oy / on * 1.2), "x")
        c.put(*P(tx + (tx - px0) * 0.8, ty + (ty - py0) * 0.8), "f")
    # rust specks
    for k, t in enumerate((0.25, 0.55, 0.8)):
        c.put(*P(gx + L * t * ux + 0.5 * nx, gy + L * t * uy + 0.5 * ny), "a" if k % 2 else "T")
    return crown


def chain_line(c, pts, cols="zx", over=True):
    k = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in line_px(*P(x0, y0), *P(x1, y1)):
            c.put(x, y, cols[(k // 1) % len(cols)], over); k += 1


def sag(p0, p1, n=8, droop=3.0):
    return [(p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t + droop * 4 * t * (1 - t)) for t in [i / n for i in range(n + 1)]]


def diver_helmet(c, g, hx, hy, tilt=0.0, glow=1, crack=False):
    ell(c, hx, hy, 4.8, 4.6, BRONZE, ang=tilt, bias=0.12,
        shader=lambda nu, nv, d, l, ch, x, y: ("d" if (x * 3 + y * 7) % 13 == 0 and d > 0.4 else
                                               "E" if (x * 3 + y * 7) % 13 == 6 and d > 0.6 and l < 0 else ch))
    # collar / breastplate rim
    line(c, hx - 4, hy + 4, hx + 4, hy + 4, "A"); line(c, hx - 3, hy + 5, hx + 3, hy + 5, "J")
    # rivets
    for (a, b) in ((-3.5, 3.2), (-1, 4.0), (1.5, 4.0), (3.8, 3.0)):
        c.put(*P(hx + a, hy + b), "w")
    # top valve
    c.put(*P(hx - 0.5, hy - 5), "e"); c.put(*P(hx + 0.5, hy - 5), "A"); c.put(*P(hx, hy - 6), "w")
    # side porthole (dark) + front faceplate with glow
    ell(c, hx - 1.3, hy - 0.2, 1.2, 1.3, "ZDD")
    c.put(*P(hx - 1.8, hy - 0.8), "d")
    fx_, fy_ = hx + 2.6 + math.sin(math.radians(tilt)) * 0.5, hy + 0.2
    ell(c, fx_, fy_, 1.9, 2.0, "JAJ")
    for (a, b) in ((0, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)):
        g.put(*P(fx_ - 0.5 + a, fy_ + b - 0.3), "Z" if glow == 0 else ("c" if (a, b) in ((0, -1), (0, 0)) else "B" if glow >= 2 else "d"))
    if glow >= 2:
        g.put(*P(fx_ + 2.2, fy_ - 0.5), "Q", over=False)
    if crack:
        g.put(*P(fx_, fy_), "Q"); g.put(*P(fx_ + 1, fy_ + 1), "Z")
    # barnacles on the dome
    barnacles(c, [(hx - 3, hy - 2.5), (hx - 2.5, hy + 2)], seed=21)


def diver(dx=0.0, dy=0.0, lean=0.0, feet=((-3, 0), (3, 0)), hands=((5, -12), (6, -11)), anchor_g=None, anchor_a=80,
          anchor_ring=True, smear=None, glow=1, hook=None, chain_to=None, extra=None, knee=0.0, head_tilt=0.0,
          bubbles=(), planted=None, crack=False, anchor_L=12.5):
    f = Fr()
    hip = (dx, -9.5 + dy + knee)
    lt = math.tan(math.radians(lean))
    sh_y = hip[1] - 8.0
    chest = (hip[0] + lt * 4.5, hip[1] - 4.5)
    neck = (hip[0] + lt * 8.5, sh_y)
    head = (neck[0] + lt * 3 + 0.5, sh_y - 4.0)
    # planted anchor (behind, for the Hook move)
    if planted is not None:
        anchor(f.u, planted[0], planted[1], planted[2], L=anchor_L)
    # legs: back leg first (darker), lead boots
    for i, (fx, fy) in enumerate(feet):
        hp = (hip[0] + (-1.2 if i == 0 else 1.2), hip[1])
        foot = (dx + fx, fy - 2.0)
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], foot[0], foot[1], 4.2, 4.0, bend=-1)
        lay = f.u if i == 0 else f.b
        ramp = "ZZkt" if i == 0 else SUIT
        tube(lay, [hp, (kx, ky), (ax, ay)], [1.8, 1.6, 1.5], ramp)
        # lead boot
        bx, by = P(ax, ay)
        for yy in range(by, min(0, by + 2) + 1):
            for xx in range(bx - 2, bx + 3):
                lay.put(xx, yy, "x" if yy == by else "z")
        lay.put(bx - 2, by, "f" if i else "x"); lay.put(bx + 2, min(0, by + 2), "Z")
    # back arm
    sh_b = (neck[0] - 2.5, sh_y + 1.5)
    (ebx, eby), (hbx, hby) = ik(sh_b[0], sh_b[1], dx + hands[0][0], hands[0][1] + dy, 3.6, 3.6, bend=1)
    # v0.9 lineage (Barnacle Crab parent): the back arm ends in a red crab claw
    tube(f.u, [sh_b, (ebx, eby), (hbx, hby)], [1.5, 1.4, 1.3], "ZjpP")
    ell(f.u, hbx, hby, 2.0, 1.6, CRAB, bias=0.2)
    line(f.u, hbx + 1.2, hby - 1.0, hbx + 3.2, hby - 1.8, "P"); line(f.u, hbx + 1.2, hby + 0.6, hbx + 2.8, hby + 0.8, "p")
    # torso: waterlogged canvas suit, lead weight belt, barnacles
    def suit(nu, nv, d, l, ch, x, y):
        if (x * 5 + y * 3) % 17 == 0: return "D"
        return ch
    ell(f.b, chest[0], chest[1], 4.0, 5.2, SUIT, ang=lean, bias=0.1, shader=suit)
    line(f.b, hip[0] - 3.5, hip[1] - 1, hip[0] + 3.8, hip[1] - 1, "z")
    for k in (-2, 0, 2):
        f.b.put(*P(hip[0] + k + 0.5, hip[1] - 1), "f" if k < 2 else "x")
    barnacles(f.b, [(chest[0] - 2.5, chest[1] + 1), (chest[0] + 1.5, chest[1] + 2.5)], seed=31)
    kelp(f.b, int(round(chest[0] - 3)), int(round(chest[1] - 1)), 6, 0.8, seed=2)
    # anchor held in both hands (drawn between the arms)
    crown = None
    if anchor_g is not None:
        crown = anchor(f.b, dx + anchor_g[0], anchor_g[1] + dy, anchor_a, ring=anchor_ring, L=anchor_L)
    # chain from the anchor ring to the belt
    if chain_to is not None:
        p0, p1, dr = chain_to
        chain_line(f.b, sag(p0, p1, 10, dr))
    if smear:
        for (x, y, ch) in smear: f.g.put(x, y, ch, over=False)
    # helmet over the shoulders
    diver_helmet(f.b, f.g, head[0], head[1], tilt=head_tilt, glow=glow, crack=crack)
    # v0.9 lineage (Bell Urchin parent): a spiny violet urchin has grown onto the back of the helmet
    ux_, uy_ = head[0] - 2.6, head[1] - 3.6
    for k in range(9):
        a = math.radians(-200 + k * 25)
        line(f.b, ux_ + 1.5 * math.cos(a), uy_ + 1.3 * math.sin(a), ux_ + 3.4 * math.cos(a), uy_ + 3.0 * math.sin(a), "fH")
    ell(f.b, ux_, uy_, 2.0, 1.7, URCH, bias=0.25)
    # front arm
    sh_f = (neck[0] + 1.5, sh_y + 1.5)
    (efx, efy), (hfx, hfy) = ik(sh_f[0], sh_f[1], dx + hands[1][0], hands[1][1] + dy, 3.6, 3.8, bend=1)
    tube(f.b, [sh_f, (efx, efy), (hfx, hfy)], [1.6, 1.5, 1.3], SUIT)
    ell(f.b, hfx, hfy, 1.5, 1.4, "zxf")
    if hook is not None:
        hook(f, (hfx, hfy))
    for (bx, by) in bubbles:
        f.g.put(*P(head[0] + bx, head[1] + by), "Q"); f.g.put(*P(head[0] + bx + 1, head[1] + by + 1), "E", over=False)
    if extra: extra(f, crown)
    return f.done()


def iron_hook(f, x, y, ang=0.0, chain=None, on=None):
    """Small iron grapnel hook; (x,y) = eye at the chain end; ang = direction it points."""
    c = on if on is not None else f.b
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    shank_end = (x + 3.5 * ux, y + 3.5 * uy)
    line(c, x, y, *shank_end, "x")
    pts = [shank_end, (shank_end[0] + 1.2 * ux + 1.2 * nx, shank_end[1] + 1.2 * uy + 1.2 * ny),
           (shank_end[0] - 0.2 * ux + 2.4 * nx, shank_end[1] - 0.2 * uy + 2.4 * ny),
           (shank_end[0] - 1.6 * ux + 2.0 * nx, shank_end[1] - 1.6 * uy + 2.0 * ny)]
    polyline(c, pts, "x")
    c.put(*P(*pts[-1]), "f")
    c.put(*P(x - ux, y - uy), "z")


def diver_corpse():
    f = Fr()
    # face-down sprawl: helmet rolled forward, anchor across the legs
    tube(f.b, [(-11, -1.5), (-6, -2), (-1, -2.5)], [1.6, 1.8, 2.0], SUIT)
    for (x, y) in ((-13, -1), (-12, -1)): f.b.put(x, y, "z")
    f.b.put(-13, 0, "z"); f.b.put(-12, 0, "z"); f.b.put(-14, 0, "z")
    ell(f.b, 1, -3.0, 4.6, 3.0, SUIT, bias=0.05)
    barnacles(f.b, [(0, -4), (2.5, -3)], seed=33)
    diver_helmet(f.b, f.g, 7.5, -4.4, tilt=30, glow=0, crack=True)
    anchor(f.u, -12, -3.5, 4, L=13)
    tube(f.b, [(3, -1.2), (6, -0.8)], [1.3, 1.2], SUIT)
    return f.done()


def build_diver(outdir):
    D = diver
    # idle: anchor held across the body, crown resting near the ground in front
    idle = []
    for i in range(4):
        b = [0, 0.4, 0.6, 0.3][i]
        idle.append(D(dy=b, hands=((4.5, -11 + b * 0.5), (6.5, -12 + b * 0.5)), anchor_g=(5.5, -12 + b), anchor_a=72 + b * 2,
                      bubbles=[((0.5, -8 - i * 2),), ((1, -7 - i), (-0.5, -10 - i))][i % 2] if i else (),
                      glow=1 if i != 2 else 2, head_tilt=b * 2, chain_to=((5.5 + 0.0, -13.5 + b), (1.5, -10.5 + b), 2.5)))
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        fa, fb = 5.0 * math.sin(ph), -5.0 * math.sin(ph)
        lift_a, lift_b = max(0, 1.5 * math.cos(ph)), max(0, -1.5 * math.cos(ph))
        bob = -abs(math.cos(ph)) * 0.8
        run.append(D(dy=bob + 0.6, lean=8, feet=((fa - 0.5, -lift_a), (fb + 1, -lift_b)),
                     hands=((5 + 0.5 * math.sin(ph), -12.5 + bob), (7 + 0.5 * math.sin(ph), -13 + bob)),
                     anchor_g=(6.5 + 0.5 * math.sin(ph), -13.5 + bob), anchor_a=60 + 4 * math.sin(ph), glow=1, head_tilt=4,
                     chain_to=((6.5, -15 + bob), (2, -10.5 + bob), 2)))
    # ANCHOR slam
    def smear_arc(cx_, cy_, r, a0, a1):
        pts = []
        for k in range(14):
            a = math.radians(a0 + (a1 - a0) * k / 13)
            for rr in (r, r - 1):
                pts.append((*P(cx_ + rr * math.cos(a), cy_ + rr * math.sin(a)), "Q" if rr == r else "E"))
        return pts
    def impact(n):
        def fn(f, crown):
            if crown is None: return
            x0 = crown[0]
            for k in range(n):
                f.g.put(*P(x0 + 3 + k * 1.5, -1 - (k % 2)), "Q" if k % 2 else "E")
                f.g.put(*P(x0 - 3 - k * 1.5, -1 - ((k + 1) % 2)), "E")
            for k in range(-5, 6):
                f.g.put(*P(x0 + k, 0), "d", over=False)
        return fn
    anc = [D(knee=0.6, lean=-6, hands=((2, -14), (3.5, -15)), anchor_g=(3, -15), anchor_a=110, glow=1),
           D(knee=-0.3, lean=-14, feet=((-4, 0), (4, 0)), hands=((-1, -24), (0.5, -25)), anchor_g=(0, -25), anchor_a=-150, glow=2,
             head_tilt=-6),
           D(knee=-0.4, lean=-18, feet=((-4, 0), (4.5, 0)), hands=((-2, -25), (-0.5, -26)), anchor_g=(-1, -26), anchor_a=-170, glow=2,
             head_tilt=-8),
           D(knee=0.6, lean=10, feet=((-4.5, 0), (5, 0)), hands=((6, -22), (7, -22)), anchor_g=(7, -23), anchor_a=-30, glow=2,
             smear=smear_arc(2, -16, 13, -170, -40)),
           D(knee=2.0, lean=22, feet=((-5, 0), (5.5, 0)), hands=((9, -12), (10, -12.5)), anchor_g=(10, -13), anchor_a=72, glow=2,
             anchor_L=12, extra=impact(4)),
           D(knee=1.8, lean=20, feet=((-5, 0), (5.5, 0)), hands=((9, -11.5), (10, -12)), anchor_g=(10, -12.5), anchor_a=74, glow=1,
             anchor_L=12, extra=impact(2)),
           D(knee=0.6, lean=6, hands=((5.5, -12), (7, -12.5)), anchor_g=(6.5, -13), anchor_a=70, glow=1)]
    # HOOK: anchor planted behind as a brace; a grapnel on the chain is whirled, thrown, hauled back
    plant = (-9, -10, 80)
    def hook_at(dx_, dy_, ang, chain_from=None, taut=False, coil=False):
        def fn(f, hand):
            hx, hy = hand
            ex, ey = hx + dx_, hy + dy_
            if chain_from == "hand":
                chain_line(f.b, sag((hx, hy), (ex, ey), 8, 0.0 if taut else 1.5))
            iron_hook(f, ex, ey, ang)
            if coil:
                for k in range(5):
                    a = k * 1.25
                    f.b.put(*P(hx - 1 + 1.5 * math.cos(a), hy + 2 + 1.2 * math.sin(a)), "zx"[k % 2])
        return fn
    def taut_off(n):
        # chain runs straight out of frame to the right (the FxHook carries the hook)
        def fn(f, hand):
            hx, hy = hand
            chain_line(f.b, [(hx, hy), (hx + n, hy - 0.5)])
        return fn
    def pull_lines(f, crown):
        for k in range(3):
            f.g.put(*P(16 + k * 2, -13 + k), "D")
    belt_chain = lambda b=0: ((-9, -21.5), (-1, -10.5 + b), 3)
    hk = [D(lean=-4, planted=plant, hands=((-2, -12), (4, -24)), glow=1, chain_to=belt_chain(),
            hook=hook_at(1, -4, -60, "hand")),
          D(lean=-12, planted=plant, feet=((-4, 0), (4, 0)), hands=((-3, -13), (-3, -23)), glow=2, chain_to=belt_chain(),
            hook=hook_at(-5, -2, 160, "hand")),
          D(lean=12, planted=plant, feet=((-4, 0), (5, 0)), hands=((2, -14), (11, -18)), glow=2, chain_to=belt_chain(),
            hook=hook_at(5, -1, -10, "hand", taut=True)),
          D(lean=10, planted=plant, feet=((-4, 0), (5, 0)), hands=((3, -14), (11, -16)), glow=1, chain_to=belt_chain(),
            hook=taut_off(12)),
          D(lean=-8, planted=plant, feet=((-4.5, 0), (4, 0)), knee=0.8, hands=((5, -15), (9, -16)), glow=1, chain_to=belt_chain(0.8),
            hook=taut_off(12), extra=pull_lines),
          D(lean=-14, planted=plant, feet=((-5, 0), (4, 0)), knee=1.2, hands=((8, -15.5), (3, -14)), glow=2, chain_to=belt_chain(1.2),
            hook=taut_off(14), extra=pull_lines),
          D(lean=-18, planted=plant, feet=((-5.5, 0), (4.5, 0)), knee=1.5, hands=((3, -14), (6, -14.5)), glow=2, chain_to=belt_chain(1.5),
            hook=taut_off(14), extra=pull_lines),
          D(lean=-20, planted=plant, feet=((-6, 0), (5, 0)), knee=2.0, hands=((1, -14), (4, -14)), glow=1, chain_to=belt_chain(2),
            hook=hook_at(4, 0, 0, "hand", coil=True))]
    death = [D(lean=-14, head_tilt=-10, hands=((-1, -14), (2, -12)), anchor_g=(3, -12), anchor_a=120, glow=2, feet=((-4, 0), (2, 0))),
             D(knee=2.5, lean=-6, head_tilt=-4, hands=((2, -8), (5, -8)), anchor_g=(6, -6), anchor_a=10, glow=1, feet=((-4, 0), (3, 0))),
             grounded(D(knee=5, lean=40, head_tilt=30, hands=((8, -6), (9, -5)), anchor_g=(-6, -4), anchor_a=5, glow=0,
                        feet=((-5, 0), (0, 0)))),
             diver_corpse()]
    knock = D(lean=-18, head_tilt=-8, hands=((1, -13), (4, -12.5)), anchor_g=(4, -13), anchor_a=95, glow=2, feet=((-5, 0), (2, -1)))
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.1] * 6),
             ("Anchor", anc, [0.16, 0.14, 0.16, 0.05, 0.07, 0.18, 0.16]),
             ("Hook", hk, [0.12, 0.14, 0.06, 0.1, 0.14, 0.14, 0.14, 0.18])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("BelDiver", anims, outdir, scale=5)


# ================================================================== SALT SIREN (T2)
SKIN = "zMCC"
GOWN = "Zjzx"
SCALE = "ZDdE"


def siren(dx=0.0, dy=0.0, lean=0.0, head=(0.0, 0.0), head_tilt=0.0, mouth=0, hands=((-5, -13), (5, -12)), throat=1,
          hair=0.0, hair_up=0.0, tail=0.0, fin=0.0, coil=0.0, hem=0, eye="open", extra=None, slump=0.0):
    f = Fr()
    waist = (dx + 0.0, -12.0 + dy + slump)
    lt = math.tan(math.radians(lean))
    sh = (waist[0] + lt * 6.5, waist[1] - 6.5)
    hd = (sh[0] + lt * 2.5 + 0.8 + head[0], sh[1] - 3.6 + head[1])
    # tail: coiled scaly loop on the floor, fin flicking behind
    tx0 = dx - 1.0 + coil
    tail_pts = [(tx0 - 1, -2.0), (tx0 + 3.5, -1.6), (tx0 + 5.5, -2.2), (tx0 + 4.5, -3.8), (tx0 + 1.0, -4.2)]
    tube(f.u, [(tx0 + 2, -3.0)] + tail_pts[:3], [2.4, 2.2, 1.8, 1.4], SCALE, bias=0.05)
    back = [(tx0 - 1, -2.2), (tx0 - 4.5, -1.8 - tail * 0.5), (tx0 - 7.0, -3.0 - tail * 1.5)]
    tube(f.u, back, [2.0, 1.4, 0.8], SCALE)
    fx_, fy_ = back[-1]
    for k, a in enumerate((-130 - fin * 20, -160 - fin * 15, 160 - fin * 10)):
        e = (fx_ + 3.6 * math.cos(math.radians(a)), fy_ + 3.6 * math.sin(math.radians(a)))
        line(f.u, fx_, fy_, e[0], e[1], "dE" if k == 1 else "Dd")
    poly(f.u, [(fx_, fy_), (fx_ + 3.6 * math.cos(math.radians(-130 - fin * 20)), fy_ + 3.6 * math.sin(math.radians(-130 - fin * 20))),
               (fx_ + 3.6 * math.cos(math.radians(160 - fin * 10)), fy_ + 3.6 * math.sin(math.radians(160 - fin * 10)))], "D", over=False)
    # scale glints
    for k in range(4):
        f.u.put(*P(tx0 - 3 + k * 2.2, -3 + (k % 2)), "E")
    # kelp hair behind the body: a heavy wet mass falling down the back
    for k in range(8):
        a0 = math.radians(-60 - k * 17)
        rootx = hd[0] - 0.4 + 2.2 * math.cos(a0)
        rooty = hd[1] - 0.2 + 2.6 * math.sin(a0)
        n = 10 + (k % 3) * 2 + (k // 3) - int(hair_up * 3)
        x, y = rootx, rooty
        a_start = 150 + k * 3 + hair_up * 30
        a_end = 92 + k * 2.5 + hair_up * (95 + k * 4)
        for j in range(n):
            sway = hair * math.sin(j * 0.45 + k * 0.9)
            a_ = a_start + (a_end - a_start) * min(1.0, j / 5.0) + sway * 12
            x += math.cos(math.radians(a_)); y += math.sin(math.radians(a_))
            ch = "Lvl"[(j + k) % 3] if j < n - 2 else "L"
            f.u.put(*P(x, y), ch)
            if j < n - 3 and k % 2 == 0: f.u.put(*P(x - 1, y), "L", over=False)
    # back arm
    shb = (sh[0] - 1.2, sh[1] + 0.8)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], dx + hands[0][0], hands[0][1] + dy, 4.0, 4.0, bend=-1)
    tube(f.u, [shb, (ex, ey), (hx, hy)], [0.8, 0.7, 0.6], "zM")
    for a in (-30, 0, 30):
        aa = math.atan2(hy - ey, hx - ex) + math.radians(a)
        line(f.u, hx, hy, hx + 1.6 * math.cos(aa), hy + 1.6 * math.sin(aa), "M")
    # gown: tattered, flaring from the waist to a ragged hem over the tail
    top_w, bot_w = 2.6, 6.0
    hem_y = -3.2
    pts = [(waist[0] - top_w, waist[1]), (waist[0] + top_w, waist[1])]
    rag = []
    for k in range(9):
        x = waist[0] + bot_w - k * (2 * bot_w) / 8.0 + lt * 0
        y = hem_y + (1.4 if (k + hem) % 2 == 0 else -0.4) + (0.6 if k in (3, 6) else 0)
        rag.append((x, y))
    poly(f.b, pts + rag, "z", shade=lambda x, y: pick(GOWN, 0.6 - (x - waist[0] + 2) * 0.22 - (y - waist[1]) * 0.03))
    for k in range(3):   # fold lines
        line(f.b, waist[0] - 1 + k * 1.5, waist[1] + 1, waist[0] - 2.5 + k * 3.0, hem_y - 0.5, "Z" if k == 2 else "z")
    barnacles(f.b, [(waist[0] - 3, hem_y - 1.5)], seed=41)
    # torso: gaunt, ribs showing
    ell(f.b, (waist[0] + sh[0]) / 2, (waist[1] + sh[1]) / 2, 2.6, 4.0, SKIN, ang=lean, bias=0.1)
    for k in range(3):
        y = sh[1] + 2.2 + k * 1.3
        x = sh[0] + lt * (y - sh[1]) * -1
        line(f.b, x - 1, y, x + 1.2, y + 0.3, "x")
    # gown bodice straps of kelp
    line(f.b, sh[0] - 1.5, sh[1] + 0.5, waist[0] - 1.5, waist[1], "L")
    # neck + glowing throat
    nk = ((sh[0] + hd[0]) / 2, (sh[1] + hd[1]) / 2 + 0.5)
    tube(f.b, [sh, (hd[0] - 0.4, hd[1] + 1.5)], [1.1, 1.0], SKIN)
    tg = ["E", "Q", "c"][min(2, throat)]
    f.g.put(*P(nk[0] + 0.6, nk[1]), tg); f.g.put(*P(nk[0] + 0.6, nk[1] + 1), "c" if throat >= 2 else "E")
    if throat >= 2:
        f.g.put(*P(nk[0] + 1.6, nk[1]), "B"); f.g.put(*P(nk[0] - 0.4, nk[1] + 1), "B")
    if throat >= 3:
        for (a, b) in ((2.6, -0.5), (2.4, 1.5), (-1.2, -0.2)):
            f.g.put(*P(nk[0] + a, nk[1] + b), "E", over=False)
    # head: gaunt, sunken cheek, glowing eye, open mouth when singing
    ell(f.b, hd[0], hd[1], 2.4, 2.9, SKIN, ang=head_tilt, bias=0.15)
    f.b.put(*P(hd[0] + 0.2, hd[1] + 1.0), "x")                   # sunken cheek
    f.b.put(*P(hd[0] + 2.4, hd[1] - 0.2), "M")                   # nose tip
    ex_, ey_ = P(hd[0] + 1.2, hd[1] - 0.6)
    if eye == "open":
        f.g.put(ex_, ey_, "c"); f.g.put(ex_ - 1, ey_, "Q"); f.g.put(ex_ - 1, ey_ - 1, "Z"); f.g.put(ex_, ey_ - 1, "Z")
    elif eye == "shut":
        f.g.put(ex_, ey_, "z"); f.g.put(ex_ - 1, ey_, "z")
    elif eye == "wide":
        f.g.put(ex_, ey_, "c"); f.g.put(ex_, ey_ - 1, "Q"); f.g.put(ex_ - 1, ey_, "Z")
    else:
        f.g.put(ex_, ey_, "x")
    mx_, my_ = P(hd[0] + 1.6, hd[1] + 1.4)
    if mouth == 0:
        f.b.put(mx_, my_, "z")
    else:
        for j in range(mouth):
            f.b.put(mx_, my_ + j, "Z"); f.b.put(mx_ + 1, my_ + j, "j" if j else "Z")
    # hair crown over the scalp
    for k in range(5):
        f.b.put(*P(hd[0] - 1.6 + k * 0.8, hd[1] - 2.6 - (k % 2) * 0.4), "Lvl"[k % 3])
    f.b.put(*P(hd[0] - 2.4, hd[1] - 1.6), "v"); f.b.put(*P(hd[0] - 2.4, hd[1] - 0.6), "L")
    # v0.10 lineage (Lurefish parent only): the Lurefish's ragged teal fin crest flares from the back of her hair ...
    for k, a in enumerate((-155, -132, -178, -200)):
        ar = math.radians(a)
        x0, y0 = hd[0] - 1.4 + 2.0 * math.cos(ar), hd[1] - 0.4 + 2.2 * math.sin(ar)
        line(f.b, x0, y0, x0 + (2.6 - 0.6 * (k % 2)) * math.cos(ar), y0 + (2.6 - 0.6 * (k % 2)) * math.sin(ar), "DdE")
    # ... and the Lurefish's lure arcs up from her brow on a stalk, glowing
    sway_ = hair * 0.8
    stalk = [(hd[0] + 0.8, hd[1] - 2.4), (hd[0] + 2.4 + sway_ * 0.3, hd[1] - 3.8), (hd[0] + 4.6 + sway_ * 0.5, hd[1] - 4.0)]
    for (x0, y0), (x1, y1) in zip(stalk, stalk[1:]): line(f.b, x0, y0, x1, y1, "x")
    lx_, ly_ = P(*stalk[-1])
    f.g.put(lx_, ly_ + 1, "c"); f.g.put(lx_ + 1, ly_ + 1, "Q"); f.g.put(lx_, ly_ + 2, "B"); f.g.put(lx_ + 1, ly_ + 2, "c")
    # front arm: long, thin, webbed hand
    shf = (sh[0] + 1.0, sh[1] + 1.0)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], dx + hands[1][0], hands[1][1] + dy, 4.2, 4.2, bend=1)
    tube(f.b, [shf, (ex, ey), (hx, hy)], [0.9, 0.8, 0.7], SKIN)
    hand = (hx, hy)
    for a in (-35, 0, 35):
        aa = math.atan2(hy - ey, hx - ex) + math.radians(a)
        line(f.b, hx, hy, hx + 1.8 * math.cos(aa), hy + 1.8 * math.sin(aa), "C" if a < 0 else "M")
    if extra: extra(f, hand, (mx_, my_), hd)
    return f.done()


def water_orb(c, x, y, r, phase=0):
    ell(c, x, y, r, r, "DdEQ", bias=0.25)
    c.put(*P(x - r * 0.4, y - r * 0.4), "c")
    for k in range(4):
        a = phase * 0.8 + k * math.pi / 2
        c.put(*P(x + (r + 1.2) * math.cos(a), y + (r + 1.0) * math.sin(a)), "E" if k % 2 else "d", over=False)


def song_rings(c, x, y, n, phase):
    for k in range(n):
        r = 1.5 + k * 2.2 + phase * 0.7
        for j in range(-3, 4):
            a = math.radians(j * 16 - 20)
            c.put(*P(x + 1 + r * math.cos(a), y + r * math.sin(a) * 1.2), "Q" if k == 0 else "E" if k == 1 else "D", over=False)


def siren_corpse():
    f = Fr()
    # collapsed on the floor: gown heap, tail fin limp, kelp hair fanned out
    tube(f.u, [(-10, -1.0), (-6, -1.5), (-2, -2.0)], [0.9, 1.6, 2.2], SCALE)
    for a in (-160, 180, 160):
        line(f.u, -10, -1, -10 + 3 * math.cos(math.radians(a)), -1 + 2.5 * math.sin(math.radians(a)), "Dd")
    poly(f.b, [(-4, 0), (-2, -4.5), (3, -5), (6, -2), (6, 0)], "z", shade=lambda x, y: pick(GOWN, 0.3 - (x + 2) * 0.12))
    for x in range(-4, 7, 2): f.b.put(x, 0, "Z")
    ell(f.b, 5.5, -3.5, 2.6, 1.7, SKIN)
    ell(f.b, 9.0, -2.4, 2.2, 2.0, SKIN, bias=0.1)
    for k in range(6):
        pts = curl(9 + k * 0.5, -3.5 - (k % 2), 4, 1.0, -10 + k * 18, 15)
        for j, pt in enumerate(pts): f.b.put(*P(*pt), "Lvl"[(j + k) % 3])
    tube(f.b, [(7, -1.5), (11, -0.6), (13.5, -0.5)], [0.7, 0.6, 0.5], SKIN)
    f.g.put(10, -3, "x"); f.g.put(7, -2, "D")
    return f.done()


def build_siren(outdir):
    S = siren
    idle = [S(hair=0.0, hands=((-4, -11), (5, -11)), throat=1),
            S(hair=0.6, hands=((-4.5, -11.5), (5.5, -11.5)), throat=1, dy=-0.4, fin=0.3, hem=1),
            S(hair=1.0, hands=((-4.5, -12), (5.5, -12)), throat=2, dy=-0.6, fin=0.6, hem=1, head_tilt=-3),
            S(hair=0.4, hands=((-4, -11.5), (5, -11)), throat=1, dy=-0.2, fin=0.2, eye="shut")]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(S(lean=10, dy=-0.6 * abs(math.sin(ph)), coil=1.0 * math.sin(ph), tail=math.sin(ph + 1), fin=math.sin(ph),
                     hair=1.2, hair_up=0.15, hands=((-5 + math.sin(ph), -11), (6 - math.sin(ph), -11.5)), hem=i % 2, throat=1))
    def orb_in_hand(r, ph, spray=0):
        def fn(f, hand, mouth, hd):
            water_orb(f.g, hand[0] + 1, hand[1] - 1, r, ph)
            for k in range(spray):
                f.g.put(*P(hand[0] - 2 - k, hand[1] + (k % 2) * 2 - 1), "d")
        return fn
    def flash(f, hand, mouth, hd):
        for (a, b, ch) in ((2, 0, "c"), (3, -1, "Q"), (3, 1, "Q"), (4, 0, "E"), (1, -2, "E"), (1, 2, "E")):
            f.g.put(*P(hand[0] + a, hand[1] + b), ch)
    bolt = [S(lean=-4, hands=((-5, -12), (2, -14)), throat=2, hair=0.5, extra=orb_in_hand(0.8, 0, 2)),
            S(lean=-10, hands=((-4, -11), (-3, -17)), throat=2, hair=0.8, extra=orb_in_hand(1.4, 1, 3), head_tilt=-4, hem=1),
            S(lean=-14, hands=((-3, -11), (-6, -18)), throat=3, hair=1.0, extra=orb_in_hand(1.9, 2, 3), head_tilt=-6, eye="wide"),
            S(lean=12, hands=((-6, -12), (10, -15)), throat=2, hair=-0.6, extra=flash, mouth=1, eye="wide", hem=1),
            S(lean=10, hands=((-6, -12), (9, -13)), throat=1, hair=-0.4, mouth=1),
            S(lean=2, hands=((-4.5, -11.5), (5.5, -11)), throat=1, hair=0.2)]
    def sing(n, ph):
        def fn(f, hand, mouth, hd):
            song_rings(f.g, mouth[0] + 1, mouth[1], n, ph)
        return fn
    song = [S(lean=-6, head=(-0.3, 0.3), head_tilt=-8, hands=((-6, -14), (6, -14)), throat=2, hair=0.4, hair_up=0.2, eye="shut")]
    for i in range(6):
        song.append(S(lean=-3 + (i % 2), head=(0.2, -0.3), head_tilt=-4 + (i % 3), mouth=2 if i % 2 == 0 else 3,
                      hands=((-7.5, -23 + (i % 2)), (8 + (i % 2) * 0.5, -23 + ((i + 1) % 2))), throat=3 if i % 2 == 0 else 2,
                      hair=1.0 + 0.4 * math.sin(i), hair_up=0.6 + 0.15 * (i % 2), eye="wide" if i % 3 == 0 else "open",
                      fin=math.sin(i * 1.3), hem=i % 2, extra=sing(2 + (i % 2), i % 2)))
    song.append(S(lean=0, hands=((-5, -12), (6, -12)), throat=1, hair=0.4, hair_up=0.1, mouth=0))
    death = [S(lean=-12, head_tilt=-15, hands=((0, -15), (2, -16)), throat=3, eye="wide", mouth=2, hair=1.2, hair_up=0.3),
             S(lean=16, slump=3.5, head=(0.8, 1.2), head_tilt=20, hands=((2, -6), (7, -4)), throat=1, eye="shut", mouth=1, hair=0.6),
             grounded(S(lean=55, slump=6, head=(2, 3), head_tilt=50, hands=((6, -2), (10, -1)), throat=0, eye="dead", hair=0.2)),
             siren_corpse()]
    knock = S(lean=-16, head_tilt=-12, hands=((-7, -14), (3, -17)), throat=2, eye="shut", mouth=1, hair=-1.0, hair_up=0.3)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.09] * 6),
             ("Bolt", bolt, [0.14, 0.14, 0.12, 0.06, 0.12, 0.16]),
             ("Song", song, [0.16, 0.18, 0.18, 0.18, 0.18, 0.18, 0.18, 0.16])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("BelSiren", anims, outdir, scale=5)


# ================================================================== THE DROWNED BELL (T3)
TENT = "Zqjn"


def church_bell(c, g, cx, cy, ang, size=8.0, crack=True, mouth_dark=True, ring=0, seed=0, round_=False):
    """Big cracked bronze bell. (cx,cy) = centre; ang = direction of the axis from crown to mouth (deg).
    Returns (crown, mouth_centre, mouth_dir, mouth_halfwidth)."""
    a = math.radians(ang)
    vx, vy = math.cos(a), math.sin(a)       # along the axis, toward the mouth
    ux, uy = -vy, vx                        # across
    H = size                                # half length
    def halfw(v):                           # v in [-1, 1]: crown -> lip
        t = (v + 1) / 2
        if round_:
            return size * (0.62 + 0.08 * t + 0.32 * t ** 4)
        return size * (0.40 + 0.14 * t + 0.62 * t ** 6)
    R = int(H * 1.8) + 3
    rnd = random.Random(seed)
    pts = {}
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            dx_, dy_ = x - cx, y - cy
            v = (dx_ * vx + dy_ * vy) / H
            u = dx_ * ux + dy_ * uy
            if v > 1.0 or v < -1.12: continue
            w = halfw(max(-1, v))
            if v < -0.75:   # rounded shoulder of the crown
                k = (v + 0.75) / 0.37
                w = w * math.sqrt(max(0.0, 1 - k * k))
            if abs(u) > w: continue
            nu = u / max(w, 0.1)
            # light from the top-left in world space
            wx, wy = nu * ux * 0.9 + (v * 0.25) * vx, nu * uy * 0.9 + (v * 0.25) * vy
            l = 0.95 * (-(wx + wy) / 1.414) + 0.25 * (1 - nu * nu) - 0.05
            ch = pick(BRONZE, l)
            if 0.86 < v: ch = "w" if l > 0.0 else "e"              # thick lip
            elif abs(v - 0.62) < 0.07 or abs(v + 0.42) < 0.06: ch = "J" if l < 0.3 else "A"   # cast rings
            elif rnd.random() < 0.07: ch = "d" if l < 0.2 else "E"  # verdigris
            pts[(x, y)] = ch
    for k_, v_ in pts.items(): c.put(k_[0], k_[1], v_)
    crown = (cx - vx * H * 1.12, cy - vy * H * 1.12)
    # yoke / canons on the crown
    for d in (-1.5, 0, 1.5):
        c.put(*P(crown[0] + ux * d - vx * 0.8, crown[1] + uy * d - vy * 0.8), "A" if d else "e")
    mouth = (cx + vx * H, cy + vy * H)
    mw = halfw(1.0)
    if crack:
        # a jagged crack running up from the lip
        x, y = mouth[0] + ux * mw * 0.3, mouth[1] + uy * mw * 0.3
        for k in range(7):
            x -= vx * 1.2 + ux * (0.6 if k % 2 else -0.5)
            y -= vy * 1.2 + uy * (0.6 if k % 2 else -0.5)
            g.put(*P(x, y), "Z")
            if k < 3: g.put(*P(x + ux, y + uy), "J", over=False)
    if ring:
        # vibration lines around the bell
        for k in range(3):
            for sd in (-1, 1):
                r = mw + 2 + ring + k * 0.0
                px_ = cx + ux * sd * (r + 1) - vx * (k - 1) * 3
                py_ = cy + uy * sd * (r + 1) - vy * (k - 1) * 3
                g.put(*P(px_, py_), "Q" if k == 1 else "E")
                g.put(*P(px_ + vx, py_ + vy), "E", over=False)
    return crown, mouth, (vx, vy), mw


def bell_mouth(c, mouth, vdir, mw, tent_phase=0.0, tents=5, droop=1.0, reach=1.0, wet=True):
    """Dark mouth opening + tentacles spilling out of it."""
    vx, vy = vdir
    ux, uy = -vy, vx
    for k in range(-int(mw), int(mw) + 1):
        c.put(*P(mouth[0] + ux * k * 0.95 + vx * 0.2, mouth[1] + uy * k * 0.95 + vy * 0.2), "Z")
    for t in range(tents):
        off = (t - (tents - 1) / 2) / ((tents - 1) / 2) * (mw - 1.2)
        x0, y0 = mouth[0] + ux * off + vx * 0.6, mouth[1] + uy * off + vy * 0.6
        pts = [(x0, y0)]
        ang = math.atan2(vy, vx)
        L = (5 + (t * 3) % 4) * reach
        for j in range(5):
            ang += (math.sin(tent_phase + t * 1.7 + j * 0.8) * 0.45) + 0.18 * droop * (1 if math.cos(ang) > 0 else -1) * 0
            # gravity pulls tentacles down
            gx, gy = math.cos(ang) * (1 - 0.35 * droop) , math.sin(ang) * (1 - 0.35 * droop) + 0.55 * droop
            n = math.hypot(gx, gy) or 1
            ang = math.atan2(gy / n, gx / n)
            pts.append((pts[-1][0] + math.cos(ang) * L / 5, pts[-1][1] + math.sin(ang) * L / 5))
        tube(c, pts, [1.2, 1.1, 0.9, 0.7, 0.5, 0.4], TENT, bias=0.1, over=False)
        for j in (1, 3):
            c.put(*P(*pts[j]), "C" if j == 1 else "M", over=False)
        tip = pts[-1]
        c.put(*P(*tip), "n", over=False)
    if wet:
        c.put(*P(mouth[0] - ux * mw * 0.6 + vx * 2, mouth[1] - uy * mw * 0.6 + vy * 2), "E", over=False)


def giant(dx=0.0, dy=0.0, lean=0.0, knee=0.0, feet=((-6, 0), (5, 0)), hands=((10, -14), (12, -13)),
          bell=(-5.0, -28.0, 200.0), tent=0.0, tents_reach=1.0, tent_droop=1.0, jaw=1, eye="open", head=(0.0, 0.0),
          ring=0, extra=None, bell_front=False, hand_grip=None, arms_over=False):
    f = Fr()
    hip = (dx - 1.0, -11.0 + dy + knee)
    lr = math.radians(lean)
    def T(x, y):  # torso-local (x right, y up from hip) rotated by lean (forward = clockwise)
        return hip[0] + x * math.cos(lr) + (-y) * -math.sin(lr) * -1 + y * 0 if False else \
               (hip[0] + x * math.cos(lr) + y * math.sin(lr), hip[1] + x * math.sin(lr) - y * math.cos(lr))
    chest = T(1.5, 8.0)
    shoulder = T(3.5, 12.5)
    neck = T(6.5, 12.0)
    hd = (neck[0] + 4.0 + head[0], neck[1] + 2.5 + head[1])
    # legs: short, thick, back leg darker
    for i, (fx, fy) in enumerate(feet):
        hp = (hip[0] + (-2.5 if i == 0 else 2.5), hip[1])
        foot = (dx + fx, fy - 1.6)
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], foot[0], foot[1], 5.5, 5.0, bend=-1)
        lay = f.u if i == 0 else f.b
        ramp = "Zzx" if i == 0 else FLESH
        tube(lay, [hp, (kx, ky), (ax, ay)], [3.2, 2.6, 2.2], ramp)
        ell(lay, ax + 1.2, min(-1.6, ay + 0.4), 3.0, 1.7, "Zzx" if i == 0 else "zxM")
        for t_ in (0, 1.5, 3): lay.put(*P(ax + 2.5 + t_ * 0.3, -0.0), "z")
        if i: barnacles(lay, [(kx - 1, ky - 1)], seed=51)
    # back arm (behind body)
    sb = T(1.0, 11.5)
    (ebx, eby), (hbx, hby) = ik(sb[0], sb[1], dx + hands[0][0], hands[0][1] + dy, 7.8, 7.4, bend=1)
    lay_back_arm = f.b if arms_over else f.u
    tube(lay_back_arm, [sb, (ebx, eby), (hbx, hby)], [2.4, 2.0, 1.8], "Zzx" if not arms_over else "zxM")
    ell(lay_back_arm, hbx, hby, 2.4, 2.1, "Zzx" if not arms_over else "zxM")
    # the bell on its back (behind the torso) unless swung in front
    bres = None
    def draw_bell(layer):
        cr, mo, vd, mw = church_bell(layer, f.g, bell[0] + dx, bell[1] + dy, bell[2], size=9.0, ring=ring, seed=3)
        bell_mouth(layer, mo, vd, mw, tent_phase=tent, reach=tents_reach, droop=tent_droop)
        return cr, mo, vd, mw
    if not bell_front:
        bres = draw_bell(f.u)
    # torso: hunched, bloated, barnacled
    def flesh(nu, nv, d, l, ch, x, y):      # v0.9: no scattered bruise pixels (they read as noise at game scale)
        if l > 0.7 and d < 0.45: return "C"
        return ch
    ell(f.b, chest[0], chest[1], 7.0, 8.4, FLESH, ang=lean, bias=0.05, shader=flesh)
    belly = T(3.0, 4.0)
    ell(f.b, belly[0], belly[1], 5.6, 5.0, FLESH, ang=lean, bias=-0.05, shader=flesh)
    hump = T(-1.5, 12.0)
    ell(f.b, hump[0], hump[1], 5.0, 4.0, FLESH, ang=lean, bias=0.15, shader=flesh)
    barnacles(f.b, [T(-3, 13), T(-5, 8)], seed=53, big=True)
    # (v0.9: the speckled crust is gone; three big barnacle clusters carry the texture)
    # navel / ribs shadow
    line(f.b, *T(4.5, 7.0), *T(6.0, 5.0), "x")
    # rope/chain harness over the shoulder to the bell
    if not bell_front and bres is not None:
        cr = bres[0]
        chain_line(f.b, sag(T(5.5, 10.5), cr, 6, 1.0))
        chain_line(f.b, sag(T(-0.5, 4.0), (cr[0] - 1, cr[1] + 2), 6, -1.0), over=False)
    # kelp drapes
    for k, (x0, y0, n) in enumerate(((-4, 13, 7), (-1, 15, 9), (2, 14, 6), (5, 11, 5))):
        px_, py_ = T(x0, y0)
        kelp(f.b, int(round(px_)), int(round(py_)), n, 1.0, seed=k + int(tent * 2))
    # head: small, sunk forward on a bull neck, glowing eyes, slack jaw
    tube(f.b, [T(4.0, 12.0), hd], [3.0, 2.6], FLESH)
    ell(f.b, hd[0], hd[1], 3.4, 3.2, FLESH, bias=0.1)
    for k in range(9):   # crease where the sunken head meets the chest
        a = math.radians(95 + k * 13)
        f.b.put(*P(hd[0] + 3.6 * math.cos(a), hd[1] + 3.4 * math.sin(a)), "z")
    line(f.b, hd[0] - 1.5, hd[1] - 2.2, hd[0] + 3.0, hd[1] - 1.6, "x")                    # heavy brow
    for k, ex_ in enumerate((hd[0] + 1.0, hd[0] + 3.0)):
        ey_ = hd[1] - 0.8
        if eye == "open":
            f.g.put(*P(ex_, ey_), "c"); f.g.put(*P(ex_, ey_ + 1), "D")
        elif eye == "wide":
            f.g.put(*P(ex_, ey_), "c"); f.g.put(*P(ex_ + 0.0, ey_ - 1), "Q"); f.g.put(*P(ex_ + 1, ey_), "Q")
        elif eye == "squint":
            f.g.put(*P(ex_, ey_), "E")
        else:
            f.g.put(*P(ex_, ey_), "x")
    jx, jy = P(hd[0] + 1.5, hd[1] + 2.0)
    for j in range(jaw + 1):
        f.b.put(jx, jy + j, "Z"); f.b.put(jx + 1, jy + j, "Z" if j < jaw else "j"); f.b.put(jx + 2, jy + j, "x")
    f.b.put(jx + 1, jy + jaw + 1, "M")
    for (a, b) in ((-1, 3), (-2, 2)):
        f.b.put(*P(hd[0] + a, hd[1] + b), "x")
    # v0.9 lineage (Bell Diver parent): its head is sealed in a cracked brass diving helmet
    diver_helmet(f.b, f.g, hd[0] + 0.6, hd[1] - 0.6, tilt=8.0, glow=0 if eye in ("dead", "shut") else (2 if eye == "wide" else 1),
                 crack=True)
    # bell in front (swung down / hoisted forward)
    if bell_front:
        bres = draw_bell(f.b)
    # front arm (over everything)
    sf = T(5.5, 11.0)
    (efx, efy), (hfx, hfy) = ik(sf[0], sf[1], dx + hands[1][0], hands[1][1] + dy, 9.0, 8.6, bend=1)
    tube(f.b, [sf, (efx, efy), (hfx, hfy)], [2.8, 2.3, 2.0], FLESH)
    barnacles(f.b, [((sf[0] + efx) / 2, (sf[1] + efy) / 2 - 1)], seed=55)
    # v0.10 lineage (Bell Diver parent only): the front hand wears the diver's brass-cuffed canvas gauntlet
    ell(f.b, hfx + 0.6, hfy, 3.2, 2.7, "ktgh", bias=0.25)
    for k in range(3):
        tube(f.b, [(hfx + 2.4, hfy - 1.4 + k * 1.3), (hfx + 4.6, hfy - 1.0 + k * 1.5)], [0.8, 0.6], "ktgh", bias=0.2)
    tube(f.b, [(hfx - 2.2, hfy - 2.4), (hfx - 2.2, hfy + 2.4)], [1.1, 1.1], BRONZE, bias=0.3)
    f.b.put(*P(hfx - 2.6, hfy - 1.6), "w")
    barnacles(f.b, [(hfx + 0.5, hfy - 1.2)], seed=57)
    if extra: extra(f, bres)
    return f.done()


def giant_corpse():
    f = Fr()
    # face-down heap; the bell has rolled off and lies on its side, tentacles limp across the floor
    ell(f.b, -7, -4.5, 9.0, 4.5, FLESH, bias=0.05)
    ell(f.b, -12, -3.0, 4.0, 3.0, FLESH, bias=0.0)
    barnacles(f.b, [(-9, -7), (-5, -7.5), (-11, -5)], seed=61, big=True)
    ell(f.b, 1.5, -2.6, 3.2, 2.6, FLESH, bias=0.1)
    f.g.put(3, -2, "x"); f.g.put(4, -2, "x")
    tube(f.b, [(-2, -2), (3, -1.2), (7, -1)], [2.0, 1.8, 1.6], FLESH)
    for k in range(4): kelp(f.b, -12 + k * 3, -8 + (k % 2), 4, 0.8, seed=k)
    cr, mo, vd, mw = church_bell(f.b, f.g, 13, -7.0, 160, size=7.0, ring=0, seed=5)
    bell_mouth(f.b, mo, vd, mw, tent_phase=1.0, reach=1.1, droop=1.6)
    return f.done()


def build_giant(outdir):
    G = giant
    idle = []
    for i in range(4):
        b = [0, 0.6, 1.0, 0.5][i]
        idle.append(G(dy=b, hands=((5, -6 + b * 0.3), (10.5, -3.5 + b * 0.3)), bell=(-7.5, -27.5 + b, 108 - b * 2), tent=i * 0.9,
                      jaw=1 + (i == 2), eye="open" if i != 3 else "squint", head=(0, b * 0.3)))
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        fa, fb = 4.5 * math.sin(ph), -4.5 * math.sin(ph)
        la, lb = max(0, 1.8 * math.cos(ph)), max(0, -1.8 * math.cos(ph))
        bob = abs(math.cos(ph)) * -1.0 + 1.0
        run.append(G(dy=bob, lean=10, feet=((fa - 6, -la), (fb + 5, -lb)), hands=((6 + fa * 0.6, -6 + bob), (11 + fb * 0.6, -4 + bob)),
                     bell=(-8.0, -27.0 + bob, 112 + 4 * math.sin(ph)), tent=i * 1.05, jaw=1))
    # TOLL
    def shock(n, r):
        def fn(f, bres):
            mo = bres[1]
            for k in range(n):
                for sd in (-1, 1):
                    x = mo[0] + sd * (r + k * 2.5)
                    f.g.put(*P(x, -1 - (k % 2)), "Q" if k == 0 else "E")
                    f.g.put(*P(x + sd, 0), "d", over=False)
            for k in range(-r, r + 1):
                f.g.put(*P(mo[0] + k, 0), "D", over=False)
        return fn
    def toll_smear(f, bres):
        for k in range(16):
            a = math.radians(-150 + k * 9)
            for rr in (17, 16):
                f.g.put(*P(4 + rr * math.cos(a), -18 + rr * math.sin(a)), "Q" if rr == 17 else "E", over=False)
    toll = [G(knee=1.5, lean=4, hands=((3, -27), (5, -28)), bell=(-6, -31.5, 125), tent=0.5, eye="wide", jaw=1),
            G(knee=-0.5, lean=-12, hands=((-1, -37), (1, -38)), bell=(-3, -43, 250), bell_front=True, tent=1.3, eye="wide", jaw=2,
              arms_over=True, feet=((-7, 0), (6, 0))),
            G(knee=-0.8, lean=-16, hands=((-3, -38), (-1, -39)), bell=(-8, -42, 230), bell_front=True, tent=2.0, eye="wide", jaw=2,
              arms_over=True, feet=((-7, 0), (6, 0))),
            G(knee=1.0, lean=14, hands=((13, -24), (15, -25)), bell=(16, -24, 330), bell_front=True, tent=2.8, eye="wide", jaw=2,
              arms_over=True, feet=((-8, 0), (7, 0)), extra=toll_smear),
            G(knee=3.0, lean=28, hands=((15, -12), (17, -12)), bell=(19, -10.2, 90), bell_front=True, tent=3.3, tents_reach=0.0,
              eye="wide", jaw=3, arms_over=True, feet=((-8, 0), (7, 0)), ring=1, extra=shock(3, 9)),
            G(knee=2.6, lean=24, hands=((15, -12), (17, -12.5)), bell=(19, -10.2, 90), bell_front=True, tent=3.8, tents_reach=0.0,
              eye="open", jaw=2, arms_over=True, feet=((-8, 0), (7, 0)), ring=2, extra=shock(2, 13)),
            G(knee=1.5, lean=10, hands=((10, -20), (12, -21)), bell=(12, -22, 30), bell_front=True, tent=4.4, eye="open", jaw=1,
              arms_over=True, feet=((-7, 0), (6, 0))),
            G(knee=0.5, lean=4, hands=((6, -7), (10.5, -4.5)), bell=(-6, -31.5, 114), tent=5.0, jaw=1)]
    # RIPTIDE
    def pour(n, big):
        """Water gushing out of the tipped bell: thick falling streams, foam where they land."""
        def fn(f, bres):
            cr, mo, vd, mw = bres
            vx, vy = vd
            ux, uy = -vy, vx
            for j, off in enumerate((-0.6, 0.0, 0.6)):
                x0, y0 = mo[0] + ux * off * mw, mo[1] + uy * off * mw
                spd = 1.6 + 0.5 * j
                pts = []
                for k in range(n + 1):
                    t = k * 0.6
                    x, y = x0 + vx * spd * t * 2.2, y0 + vy * spd * t * 2.2 + 1.1 * t * t * 2.2
                    if y > -0.5: pts.append((x, -0.5)); break
                    pts.append((x, y))
                if len(pts) > 1:
                    rad = [max(0.6, (1.6 if big else 1.1) - 0.1 * k) for k in range(len(pts))]
                    tube(f.g, pts, rad, "DdEQ", bias=0.2, over=False)
                    land = pts[-1]
                    if land[1] >= -0.6:
                        for q in range(-2, 3):
                            f.g.put(*P(land[0] + q * 1.3, -1 - (q % 2)), "Q" if q % 2 else "E", over=False)
            if big:
                for k in range(-12, 13):
                    f.g.put(*P(mo[0] + 9 + k, 0), "d" if k % 3 else "Q", over=False)
                    if abs(k) < 8: f.g.put(*P(mo[0] + 9 + k, -1 - (k % 2)), "E", over=False)
                for k in range(5):
                    f.g.put(*P(mo[0] + 16 + k * 1.5, -3 - k * 1.2 + (k % 2)), "Q", over=False)
        return fn
    def drip(f, bres):
        cr, mo, vd, mw = bres
        for k in range(3):
            f.g.put(*P(mo[0] + k * 2 - 2, mo[1] + 2 + k), "E")
    rip = [G(knee=2.0, lean=6, hands=((4, -25), (6, -26)), bell=(-6, -31.5, 125), tent=0.3, jaw=1, eye="open"),
           G(knee=0.5, lean=-6, hands=((2, -33), (4, -34)), bell=(-2, -36, 235), bell_front=True, arms_over=True, tent=1.0, jaw=1,
             eye="wide", extra=drip),
           G(knee=-0.5, lean=-10, hands=((4, -38), (6, -39)), bell=(2, -42, 290), bell_front=True, arms_over=True, tent=1.6, jaw=2,
             eye="wide", tent_droop=0.4, extra=drip),
           G(knee=-0.2, lean=-4, hands=((7, -37), (9, -38)), bell=(8, -40, 335), bell_front=True, arms_over=True, tent=2.2, jaw=2,
             eye="wide", tent_droop=0.6),
           G(knee=0.5, lean=6, hands=((9, -35), (11, -36)), bell=(12, -36, 15), bell_front=True, arms_over=True, tent=2.8, jaw=3,
             eye="wide", tents_reach=0.5, extra=pour(3, False)),
           G(knee=1.5, lean=12, hands=((10, -34), (12, -35)), bell=(13, -34, 30), bell_front=True, arms_over=True, tent=3.4, jaw=3,
             eye="wide", tents_reach=0.4, extra=pour(6, True)),
           G(knee=1.2, lean=10, hands=((10, -33), (12, -34)), bell=(13, -33, 35), bell_front=True, arms_over=True, tent=4.0, jaw=2,
             eye="open", tents_reach=0.6, extra=pour(4, False)),
           G(knee=1.5, lean=4, hands=((6, -28), (8, -29)), bell=(4, -36, 250), bell_front=True, arms_over=True, tent=4.6, jaw=1,
             extra=drip),
           G(knee=0.6, lean=2, hands=((6, -7), (10.5, -4.5)), bell=(-6, -31.5, 113), tent=5.2, jaw=1)]
    death = [G(lean=-10, knee=0.5, hands=((2, -20), (6, -22)), bell=(-7, -29, 140), tent=1, eye="wide", jaw=3),
             G(lean=16, knee=4, hands=((10, -6), (13, -5)), bell=(-12, -18, 160), tent=2, eye="squint", jaw=2, tent_droop=1.6),
             grounded(G(lean=60, knee=8, hands=((14, -2), (16, -1)), bell=(-14, -9, 180), tent=3, eye="dead", jaw=1, tent_droop=1.8,
                        feet=((-7, 0), (2, 0)))),
             giant_corpse()]
    knock = G(lean=-14, knee=0.5, hands=((4, -20), (8, -22)), bell=(-7, -29, 135), tent=1.5, eye="squint", jaw=2,
              feet=((-7, 0), (4, -1)))
    anims = [("Idle", idle, [0.28, 0.22, 0.28, 0.22]), ("Run", run, [0.11] * 6),
             ("Toll", toll, [0.18, 0.18, 0.16, 0.06, 0.08, 0.22, 0.18, 0.18]),
             ("Riptide", rip, [0.16, 0.16, 0.16, 0.14, 0.1, 0.08, 0.2, 0.16, 0.18])]
    anims += std_tail(idle[0], death, [0.12, 0.14, 0.18, 0.5], knock)
    sheet("BelDrownedBell", anims, outdir, scale=4)


# ================================================================== THE TIDE MATRIARCH (T3, Siren line)
# A coiled sea-serpent queen: she sits upright on a thick coil of tail (no legs), rising in a tall S-curve to a
# finned, long-armed torso, an eel face under a jagged coral crown and a mane of red-weed hair. Deep indigo
# body, pearl belly with cyan photophores, coral pink trident / crown / fins. Deliberately nothing grey-green,
# brass or kelp-green, so she never reads as a recoloured Drowned Bell or Siren.
PALETTE.update({
    'Ω': (0x14, 0x0a, 0x2a),   # indigo-black outline
    # v0.9 lineage: the body ramp is the Brine Lamprey's teal-slate (was indigo -> lavender, which matched neither parent)
    'Α': (0x1c, 0x3e, 0x44),   # body ramp (abyss teal -> pale sea-green)
    'Β': (0x2a, 0x5a, 0x5e),
    'Γ': (0x3c, 0x7c, 0x78),
    'Δ': (0x5a, 0xa0, 0x96),
    'Ε': (0x8c, 0xcc, 0xbc),
    'Φ': (0x5e, 0x26, 0x7e),   # fin membrane (violet)
    'φ': (0x96, 0x4e, 0xb6),
    'Π': (0x7c, 0x5c, 0xa4),   # pearl belly ramp
    'π': (0xb4, 0x9c, 0xd8),
    'σ': (0xe2, 0xd6, 0xf4),
    'Σ': (0xfc, 0xf8, 0xff),   # pearl white (coral tips, pearls)
    'κ': (0x80, 0x1e, 0x4c),   # coral ramp
    'λ': (0xc8, 0x3c, 0x74),
    'μ': (0xf4, 0x76, 0xa2),
    'ν': (0xff, 0xbc, 0xd4),
    'θ': (0x3a, 0x0c, 0x32),   # red-weed hair
    'ι': (0x66, 0x1a, 0x4e),
    'η': (0x96, 0x2e, 0x66),
    'ψ': (0x3e, 0xe4, 0xff),   # cyan glow
    'ω': (0xd8, 0xff, 0xff),   # glow core
})
M_BODY = "ΑΒΓΔ"
M_BODY_L = "ΒΓΔΕ"
M_PEARL = "ΠπσΣ"
M_CORAL = "κλμν"
M_FIN = "ΦφφΦ"
M_HAIR = "θιη"


def m_done(f, clip=True):
    """Fr.done with the Matriarch's own indigo outline."""
    base = dict(f.u.px); base.update(f.b.px)
    spr = outl(Spr(base), "Ω")
    px = dict(f.n.px); px.update(spr.px); px.update(f.g.px)
    if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
    return Spr(px)


def rot_about(p, piv, deg):
    a = math.radians(deg)
    x, y = p[0] - piv[0], p[1] - piv[1]
    return (piv[0] + x * math.cos(a) - y * math.sin(a), piv[1] + x * math.sin(a) + y * math.cos(a))


def catmull(pts, rad, step=1.2):
    """Dense Catmull-Rom resample of a control polyline (with radii) for smooth shaded tubes."""
    out, orad = [], []
    P_ = [pts[0]] + list(pts) + [pts[-1]]
    R_ = [rad[0]] + list(rad) + [rad[-1]]
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        n = max(1, int(math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y)); orad.append(R_[i] + (R_[i + 1] - R_[i]) * t)
    out.append(pts[-1]); orad.append(rad[-1])
    return out, orad


def trident(f, butt, tip, glint=0, smear=False):
    """Coral trident from butt to tip (tip = end of the centre prong). Returns the centre prong tip."""
    bx, by = butt; tx, ty = tip
    L = math.hypot(tx - bx, ty - by) or 1.0
    ux, uy = (tx - bx) / L, (ty - by) / L
    nx, ny = -uy, ux
    head = (tx - ux * 5.0, ty - uy * 5.0)                   # where the prongs branch
    # shaft: lit coral line with a dark underside, knobbly coral nubs
    line(f.b, bx, by, head[0], head[1], "λ")
    line(f.b, bx + nx * 0.9, by + ny * 0.9, head[0] + nx * 0.9, head[1] + ny * 0.9, "κ", over=False)
    for k in range(1, int(L / 4.5)):
        t = k * 4.5
        sd = 1 if k % 2 else -1
        f.b.put(*P(bx + ux * t - nx * 1.0 * sd, by + uy * t - ny * 1.0 * sd), "μ" if sd > 0 else "κ")
    # crossbar + three prongs (side prongs curl in a little), pearl points
    line(f.b, head[0] - nx * 3.0, head[1] - ny * 3.0, head[0] + nx * 3.0, head[1] + ny * 3.0, "λ")
    for sd in (-1, 1):
        s0 = (head[0] + nx * 3.0 * sd, head[1] + ny * 3.0 * sd)
        s1 = (s0[0] + ux * 2.5 + nx * 0.4 * sd, s0[1] + uy * 2.5 + ny * 0.4 * sd)
        s2 = (s1[0] + ux * 1.6 - nx * 0.8 * sd, s1[1] + uy * 1.6 - ny * 0.8 * sd)
        line(f.b, *s0, *s1, "μ" if sd < 0 else "λ"); f.b.put(*P(*s2), "ν")
        f.g.put(*P(s2[0] + ux * 0.8, s2[1] + uy * 0.8), "Σ")
    line(f.b, head[0], head[1], tx - ux * 0.8, ty - uy * 0.8, "μ")
    f.g.put(*P(tx, ty), "Σ")
    f.b.put(*P(head[0] - ux * 0.6, head[1] - uy * 0.6), "ν")   # pearl set in the crossbar
    if glint:
        for (a, b, ch) in ((1, 0, "ω"), (2, 0, "ψ"), (0, -1, "ψ"), (0, 1, "ψ"), (1, -1, "Σ") if glint > 1 else (1, 0, "ω")):
            f.g.put(*P(tx + ux * a + nx * b, ty + uy * a + ny * b), ch)
    if smear:
        for k in range(3):
            line(f.n, bx - ux * (2 + k * 2) + nx * (k - 1) * 2, by - uy * (2 + k * 2) + ny * (k - 1) * 2,
                 bx - ux * (8 + k * 3) + nx * (k - 1) * 2, by - uy * (8 + k * 3) + ny * (k - 1) * 2, "σπ" if k == 1 else "π")
    return (tx, ty)


def coral_crown(f, x, y, tilt=0.0, sway=0.0):
    """Jagged pink-and-white coral crown; (x, y) = middle of the band on top of the head."""
    for k in range(-3, 4):
        f.b.put(*P(x + k, y + abs(k) * 0.25), "κ" if k > 1 else "λ")
    for i, (ox, h, a) in enumerate(((-3.0, 4, -118), (-1.6, 6, -104), (0.2, 8, -90), (2.0, 6, -76), (3.4, 4, -62))):
        a += tilt + sway * (1 if i % 2 else -1)
        px_, py_ = x + ox, y + abs(ox) * 0.25 - 0.5
        n = h
        for j in range(n):
            kink = 18 if (j // 2 + i) % 2 else -18
            aa = math.radians(a + (kink if j > 0 else 0))
            px_ += math.cos(aa); py_ += math.sin(aa)
            t = j / max(1, n - 1)
            f.b.put(*P(px_, py_), "κ" if t < 0.25 else "λ" if t < 0.6 else "μ")
            if h >= 6 and j == n // 2:   # side nub
                f.b.put(*P(px_ + (1 if i >= 2 else -1), py_ - 0.4), "μ")
        f.g.put(*P(px_, py_ - 0.6), "Σ" if h >= 6 else "ν")


def matriarch(dx=0.0, dy=0.0, lean=0.0, curve=1.0, coil=0.0, coil_rx=11.0, tail=0.0, hair=0.0, hair_up=0.0,
              hands=((-6, -21), (12, -21)), tri=None, eye="open", mouth=0, lights=1, fin=0.0, head_tilt=0.0,
              crown_sway=0.0, sink=0.0, extra=None, tri_glint=0, tri_smear=False, back_over=False):
    """tri: (butt, tip) in world coords relative to the feet (None = no trident in hand)."""
    f = Fr()
    # --- coil on the floor: a squat ring of tail seen from the side, with the tail tip curling out behind
    C = (dx - 3.0, -6.4 + sink * 0.2)
    rx, ry, cr = coil_rx, 2.6, 3.5
    def ring(a0, a1, n=28):
        return [(C[0] + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                 C[1] + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
    back_arc = ring(180, 360)
    tube(f.u, back_arc, [cr * 0.95] * len(back_arc), "ΑΑΒΓ", bias=0.05)
    # a second, smaller loop stacked on top of the ring (the coil is wound twice)
    C2 = (C[0] + 1.0 + coil_rx * 0.04, C[1] - 4.6)
    loop2 = [(C2[0] + rx * 0.62 * math.cos(math.radians(a)), C2[1] + 2.0 * math.sin(math.radians(a)))
             for a in range(150, 400, 8)]
    tube(f.u, loop2, [2.9] * len(loop2), M_BODY, bias=0.0)
    for k in range(6):
        a = math.radians(160 + k * 36 + coil * 14)
        x, y = C2[0] + rx * 0.62 * math.cos(a), C2[1] + 2.0 * math.sin(a)
        if math.sin(a) > -0.2: line(f.u, x, y - 2.0, x + 0.5, y + 1.6, "Α")
    # tail: leaves the ring at the back, rises and ends in a coral fan fin
    t0 = (C[0] - rx + 0.5, C[1] - 0.5)
    tail_pts = [t0, (t0[0] - 4.0, t0[1] - 1.5 - tail * 0.6), (t0[0] - 7.0, t0[1] - 4.5 - tail * 1.4),
                (t0[0] - 8.0 + tail * 0.6, t0[1] - 8.0 - tail * 1.8)]
    tp, trd = catmull(tail_pts, [3.2, 2.4, 1.6, 0.9])
    tube(f.u, tp, trd, M_BODY, bias=0.05)
    ex, ey = tp[-1]
    fan = [(-150 - fin * 12, 5.5), (-125 - fin * 10, 6.5), (-100 - fin * 8, 6.0), (-78 - fin * 6, 4.5)]
    fan_pts = [(ex + r * math.cos(math.radians(a)), ey + r * math.sin(math.radians(a))) for a, r in fan]
    poly(f.u, [(ex, ey)] + fan_pts, "Φ", shade=lambda x, y: "φ" if (x + y) % 3 == 0 else "Φ")
    for k, (fx_, fy_) in enumerate(fan_pts):
        line(f.u, ex, ey, fx_, fy_, "λμ" if k % 2 else "κλ")
        f.u.put(*P(fx_, fy_), "ν")
    # --- the S-curve body rising out of the coil
    piv = (dx + 5.0, -19.0 + dy + sink)
    ctrl = [(dx + 3.0, -5.0), (dx + 3.5 + 6.5 * curve, -11.5 + dy * 0.5 + sink * 0.5), piv,
            (dx + 4.5 - 6.5 * curve, -25.5 + dy + sink), (dx + 2.0, -30.5 + dy + sink), (dx + 4.5, -34.0 + dy + sink)]
    ctrl = ctrl[:3] + [rot_about(p, piv, lean) for p in ctrl[3:]]
    rads = [4.2, 4.5, 3.6, 3.0, 4.0, 4.8]
    sp, sr = catmull(ctrl, rads)
    chest = ctrl[-1]
    def L(x, y):    # torso-local offset (x right, y down) rotated with the lean
        return rot_about((chest[0] + x, chest[1] + y), chest, lean)
    # dorsal fin along the back of the S (behind the body)
    for i in range(4, len(sp) - 6, 3):
        (x0, y0), (x1, y1) = sp[i], sp[i + 1]
        tl = math.hypot(x1 - x0, y1 - y0) or 1
        tx_, ty_ = (x1 - x0) / tl, (y1 - y0) / tl
        nx_, ny_ = -ty_, tx_                       # front normal; back = -n
        r = sr[i]
        b0 = (x0 - nx_ * r * 0.8, y0 - ny_ * r * 0.8)
        h = 3.2 + 1.2 * math.sin(i * 0.7 + fin * 2)
        tipf = (b0[0] - nx_ * h + tx_ * 1.8, b0[1] - ny_ * h + ty_ * 1.8)
        b1 = (b0[0] + tx_ * 3.2, b0[1] + ty_ * 3.2)
        poly(f.u, [b0, tipf, b1], "Φ", shade=lambda x, y: "φ" if (x * 3 + y) % 4 == 0 else "Φ")
        line(f.u, *b0, *tipf, "κλ"); f.u.put(*P(*tipf), "μ")
    # back arm (behind the torso unless raised over it)
    shb = L(-3.0, 0.6)
    lay = f.b if back_over else f.u
    (ebx, eby), (hbx, hby) = ik(shb[0], shb[1], dx + hands[0][0], hands[0][1] + dy, 8.6, 9.0, bend=-1)
    tube(lay, [shb, (ebx, eby), (hbx, hby)], [1.7, 1.4, 1.1], "ΑΒΓ" if not back_over else M_BODY)
    def arm_fin(layer, e, h, sd):
        ax, ay = h[0] - e[0], h[1] - e[1]
        al = math.hypot(ax, ay) or 1
        nx_, ny_ = -ay / al * sd, ax / al * sd
        pts = [(e[0] - ax * 0.15, e[1] - ay * 0.15), (e[0] + ax * 0.35 + nx_ * 4.4, e[1] + ay * 0.35 + ny_ * 4.4),
               (e[0] + ax * 0.75 + nx_ * 3.0, e[1] + ay * 0.75 + ny_ * 3.0), h]
        poly(layer, pts, "φ", over=False, shade=lambda x, y: "Φ" if (x + 2 * y) % 4 == 0 else "φ")
        line(layer, e[0], e[1], *pts[1], "λμ", over=False)
        line(layer, e[0] + ax * 0.5, e[1] + ay * 0.5, *pts[2], "κλ", over=False)
        f.g.put(*P(*pts[1]), "ν")
    arm_fin(lay, (ebx, eby), (hbx, hby), 1)
    for a in (-35, 0, 35):
        aa = math.atan2(hby - eby, hbx - ebx) + math.radians(a)
        line(lay, hbx, hby, hbx + 2.0 * math.cos(aa), hby + 2.0 * math.sin(aa), "Γ" if a < 0 else "Β")
    # red-weed hair: a long mane falling down the back
    hd = L(4.2 + head_tilt * 0.02, -7.6)
    for k in range(9):
        a0 = math.radians(-140 - k * 12)
        x, y = hd[0] + 2.6 * math.cos(a0) - 0.6, hd[1] + 2.4 * math.sin(a0)
        n = 12 + (k % 3) * 3 + k - int(hair_up * 4)
        a_start = 165 + k * 4 + hair_up * 25
        a_end = 100 + k * 3 + hair_up * 70
        for j in range(n):
            sw = hair * math.sin(j * 0.5 + k * 1.1)
            a_ = a_start + (a_end - a_start) * min(1.0, j / 6.0) + sw * 14
            x += math.cos(math.radians(a_)); y += math.sin(math.radians(a_))
            f.u.put(*P(x, y), ("ηιη" if k % 3 == 0 else M_HAIR)[(j + k) % 3] if j < n - 1 else ("μ" if k % 2 else "λ"))
            if j < n - 4 and k % 2 == 0: f.u.put(*P(x - 1, y), "θ", over=False)
    # body tube + pearl belly band + front coil arc over the body base
    tube(f.b, sp, sr, M_BODY, bias=0.08)
    belly = []
    for i in range(len(sp) - 1):
        (x0, y0), (x1, y1) = sp[i], sp[i + 1]
        tl = math.hypot(x1 - x0, y1 - y0) or 1
        nx_, ny_ = -(y1 - y0) / tl, (x1 - x0) / tl
        belly.append((x0 + nx_ * sr[i] * 0.55, y0 + ny_ * sr[i] * 0.55))
    belly.append(belly[-1])
    tube(f.b, belly[2:-6], [r * 0.36 for r in sr[2:-6]], "Ππσ", bias=0.1)
    for i in range(3, len(belly) - 8, 3):   # scute seams
        f.b.put(*P(*belly[i]), "Π")
    # chest + shoulders (pearl breastplate scales), pearl necklace
    ell(f.b, *L(0.0, 0.4), 5.0, 4.2, M_BODY, ang=lean, bias=0.1)
    ell(f.b, *L(1.4, 1.2), 2.6, 2.6, M_PEARL, ang=lean, bias=0.2)
    for k in range(3): f.b.put(*P(*L(0.6 + k * 1.2, 2.2 + (k % 2) * 0.6)), "Π")
    front_arc = ring(0, 180)
    tube(f.b, front_arc, [cr] * len(front_arc), M_BODY, bias=0.0)
    # eel bands along the coil, sliding with `coil`
    for k in range(9):
        a = (k * 20 + coil * 20) % 180
        x, y = C[0] + rx * math.cos(math.radians(a)), C[1] + ry * math.sin(math.radians(a))
        line(f.b, x, y - cr * 0.9, x + 0.6, y + cr * 0.6, "Α")
    # neck, gills, head
    nk = L(2.6, -3.6)
    tube(f.b, [L(1.2, -1.5), nk, (hd[0] - 0.6, hd[1] + 1.4)], [2.4, 2.0, 1.8], M_BODY, bias=0.1)
    for k in range(2): line(f.b, *L(2.2 + k * 1.2, -3.0), *L(2.6 + k * 1.2, -1.8), "λ")
    ell(f.b, hd[0], hd[1], 3.3, 3.0, M_BODY_L, ang=head_tilt, bias=0.05)
    sn = rot_about((hd[0] + 2.8, hd[1] + 0.9), hd, head_tilt)
    ell(f.b, sn[0], sn[1], 2.2, 1.5, M_BODY_L, ang=head_tilt, bias=0.1)
    # cheek frill fin
    for k, a in enumerate((-150, -175, 160)):
        aa = math.radians(a + head_tilt + fin * 8)
        line(f.b, hd[0] - 1.0, hd[1] + 0.8, hd[0] - 1.0 + 3.6 * math.cos(aa), hd[1] + 0.8 + 3.6 * math.sin(aa), "λμ" if k == 1 else "κλ")
    # eye
    ex_, ey_ = P(*rot_about((hd[0] + 1.4, hd[1] - 0.6), hd, head_tilt))
    if eye == "open":
        f.g.put(ex_, ey_, "ω"); f.g.put(ex_ + 1, ey_, "ψ"); f.g.put(ex_, ey_ - 1, "Ω"); f.g.put(ex_ + 1, ey_ - 1, "Ω")
    elif eye == "wide":
        f.g.put(ex_, ey_, "ω"); f.g.put(ex_ + 1, ey_, "ω"); f.g.put(ex_, ey_ - 1, "ψ"); f.g.put(ex_ - 1, ey_, "ψ")
    elif eye == "squint":
        f.g.put(ex_, ey_, "ψ"); f.g.put(ex_ + 1, ey_, "Ω")
    elif eye == "shut":
        f.g.put(ex_, ey_, "Ω"); f.g.put(ex_ + 1, ey_, "Β")
    else:
        f.g.put(ex_, ey_, "Β")
    # mouth: a long eel jaw line
    mx0 = rot_about((hd[0] + 1.6, hd[1] + 1.6), hd, head_tilt)
    mx1 = rot_about((hd[0] + 4.6, hd[1] + 1.2), hd, head_tilt)
    line(f.b, *mx0, *mx1, "Ω")
    for j in range(mouth):
        line(f.b, mx0[0] + 0.5, mx0[1] + 1 + j, mx1[0] - 0.5 - j * 0.5, mx1[1] + 1 + j, "κ" if j < mouth - 1 else "Ω")
    # coral crown
    cx_, cy_ = rot_about((hd[0] - 0.2, hd[1] - 2.9), hd, head_tilt)
    coral_crown(f, cx_, cy_, tilt=head_tilt, sway=crown_sway)
    # front arm (over everything) with the trident in hand
    shf = L(2.2, 0.8)
    (efx, efy), (hfx, hfy) = ik(shf[0], shf[1], dx + hands[1][0], hands[1][1] + dy, 8.8, 9.2, bend=1)
    hand = (hfx, hfy)
    tip = None
    if tri is not None:
        tip = trident(f, (dx + tri[0][0], tri[0][1] + dy), (dx + tri[1][0], tri[1][1] + dy), glint=tri_glint, smear=tri_smear)
    tube(f.b, [shf, (efx, efy), (hfx, hfy)], [1.8, 1.5, 1.2], M_BODY_L, bias=0.0)
    arm_fin(f.b, (efx, efy), (hfx, hfy), -1)
    ell(f.b, hfx, hfy, 1.5, 1.4, M_BODY_L, bias=0.2)
    f.b.put(*P(hfx + 1.2, hfy - 1.0), "Ε")
    # belly photophores (cyan glow) + a dotted lateral line on the coil
    for i in range(4, len(belly) - 8, 3):
        bx_, by_ = P(*belly[i])
        if lights >= 2: f.g.put(bx_, by_, "ω"); f.g.put(bx_ + 1, by_, "ψ")
        elif lights == 1: f.g.put(bx_, by_, "ψ" if (i // 3) % 2 else "ω")
        else: f.g.put(bx_, by_, "Γ")
    for k in range(5):
        a = 25 + k * 30 + (coil * 12) % 30
        x, y = C[0] + rx * math.cos(math.radians(a)), C[1] + ry * math.sin(math.radians(a)) - 0.4
        f.g.put(*P(x, y), ("ψ" if k % 2 else "ω") if lights else "Γ")
    if extra: extra(f, hand, tip)
    return m_done(f)


def matriarch_corpse():
    f = Fr()
    # slumped over her own coil: the ring is still a heap on the floor, the body drapes forward across it and
    # the head lies on the floor; the crown has slipped off, the trident lies behind her, the lights are out
    C, rx, ry, cr = (-4.0, -4.6), 11.5, 2.0, 3.2
    ring = lambda a0, a1: [(C[0] + rx * math.cos(math.radians(a0 + (a1 - a0) * k / 28.0)),
                            C[1] + ry * math.sin(math.radians(a0 + (a1 - a0) * k / 28.0))) for k in range(29)]
    f2 = Fr()
    trident(f2, (-24, -1), (-1, -2.5))
    for k, v in f2.b.px.items(): f.n.raw.put(k[0], k[1], v)
    tube(f.u, ring(180, 360), [cr] * 29, "ΑΑΒΓ", bias=0.05)
    tp, trd = catmull([(C[0] - rx + 0.5, C[1]), (C[0] - rx - 4, -2.6), (C[0] - rx - 8, -1.6)], [2.8, 2.0, 1.0])
    tube(f.u, tp, trd, M_BODY)
    ex, ey = tp[-1]
    for a, r in ((-170, 4), (-150, 5), (-130, 4)):
        line(f.u, ex, ey, ex + r * math.cos(math.radians(a)), ey + r * math.sin(math.radians(a)), "κλ")
    for k in range(6):   # hair spread on the floor behind the head
        for j in range(5 + k):
            f.u.put(*P(16.0 - j * 0.9, -6.2 + k * 0.5 + math.sin(j * 0.8 + k) * 0.6), M_HAIR[(j + k) % 3])
    sp, sr = catmull([(1.5, -8.0), (6.0, -8.8), (11.0, -6.2), (15.0, -4.0), (18.0, -3.4)], [4.0, 4.2, 3.6, 3.0, 2.4])
    tube(f.b, sp, sr, M_BODY, bias=0.08)
    tube(f.b, [(x + 0.4, y + sr[i] * 0.55) for i, (x, y) in enumerate(sp[2:-4], 2)], [1.2] * (len(sp) - 6), "Ππσ", bias=0.1)
    tube(f.b, ring(0, 180), [cr] * 29, M_BODY)
    for k in range(9):
        a = k * 20 + 10
        x, y = C[0] + rx * math.cos(math.radians(a)), C[1] + ry * math.sin(math.radians(a))
        line(f.b, x, y - cr * 0.9, x + 0.6, y + cr * 0.6, "Α")
    # limp arm with its fin, hand on the floor
    tube(f.b, [(9.0, -7.5), (13.0, -3.5), (16.5, -1.2)], [1.5, 1.3, 1.0], M_BODY_L)
    poly(f.b, [(10.0, -6.0), (11.5, -1.8), (14.0, -1.2)], "φ", over=False)
    ell(f.b, 21.0, -3.0, 3.2, 2.6, M_BODY_L, bias=0.05)
    ell(f.b, 23.6, -1.9, 2.0, 1.3, M_BODY_L, bias=0.1)
    f.g.put(22, -4, "Β"); line(f.b, 21.0, -1.2, 25.0, -0.8, "Ω")
    for i, h in enumerate((3, 5, 4)):
        for j in range(h): f.b.put(27 + i * 2 + j % 2, -1 - j, "λ" if j < h - 1 else "μ")
        f.g.put(27 + i * 2 + (h - 1) % 2, -1 - h, "Σ")
    for x in range(-12, 8, 4): f.g.put(x, -3, "Γ")      # dead photophores
    return m_done(f)


def m_sheet(name, anims, outdir, cell, scale=4):
    """Like sheet(), but with a fixed cell size (frames are clipped to it, with a warning)."""
    cw, ch = cell
    feet = (cw // 2, ch - 2)
    clipped = 0
    out = []
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
        keep = []
        for f in fr:
            px = {k: v for k, v in f.px.items() if -feet[0] <= k[0] < cw - feet[0] and -feet[1] <= k[1] < ch - feet[1]}
            clipped += len(f.px) - len(px)
            keep.append(type(f)(px))
        out.append((an, keep, du))
    if clipped: print("WARNING %s: %d pixels outside the %dx%d cell" % (name, clipped, cw, ch))
    img, man = pack(name, out, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in out], "img": img, "man": man}
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in out)))


M_TRI_REST = ((13, -1), (13, -33))        # trident planted upright beside her


def build_matriarch(outdir):
    M = matriarch
    idle = []
    for i in range(4):
        b = [0, 0.5, 1.0, 0.5][i]
        idle.append(M(dy=b, hands=((-7, -18 + b), (12.4, -19 + b * 0.5)), tri=((13, -1), (13, -33 + b * 0.3)),
                      hair=[0, 0.6, 1.0, 0.4][i], tail=[0, 0.6, 1.0, 0.5][i], fin=[0, 0.4, 0.8, 0.4][i],
                      lights=[1, 1, 2, 1][i], eye="open" if i != 3 else "squint", crown_sway=[0, 4, 0, -4][i]))
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(M(dx=1.0 * math.sin(ph), dy=-0.6 * abs(math.sin(ph)), lean=8 + 2 * math.sin(ph), curve=1.0 + 0.35 * math.sin(ph),
                     coil=i, coil_rx=11.0 + 1.2 * math.sin(ph), tail=1.4 * math.sin(ph + 1.2), fin=math.sin(ph),
                     hair=1.2, hair_up=0.25, hands=((-8 + 1.5 * math.sin(ph), -20), (12, -22)),
                     tri=((5 + math.sin(ph), -9), (26 + math.sin(ph), -31)), lights=1 + (i % 2)))
    # WHIRL: the trident is spun flat overhead (seen edge-on, so it foreshortens), then slammed into the floor
    def spin(theta, R=15.0, cy=-45.0, cx=4.0):
        a = math.radians(theta)
        return ((cx - R * math.cos(a), cy - R * 0.28 * math.sin(a)), (cx + R * math.cos(a), cy + R * 0.28 * math.sin(a)))
    def ring_smear(a0, a1, cy=-45.0, cx=4.0, R=16.0, drops=0):
        def fn(f, hand, tip):
            n = int(abs(a1 - a0) / 7) + 1
            for k in range(n):
                a = math.radians(a0 + (a1 - a0) * k / max(1, n - 1))
                x, y = cx + R * math.cos(a), cy + R * 0.3 * math.sin(a)
                f.n.put(*P(x, y), "σ" if k > n * 0.6 else "π" if k > n * 0.3 else "Δ")
                f.n.put(*P(x, y + 1), "Δ", over=False)
            for k in range(drops):   # water lifting off the floor in front, already turning
                a = math.radians(k * 360.0 / drops + a0)
                f.g.put(*P(24 + 7 * math.cos(a), -1.5 + 2.0 * math.sin(a) - (k % 3)), "ψ" if k % 2 else "π")
        return fn
    def slam_fx(f, hand, tip):
        for k in range(12):   # vertical smear from overhead to the floor
            a = math.radians(-100 + k * 10)
            for rr in (22, 21):
                f.n.put(*P(4 + rr * math.cos(a), -22 + rr * math.sin(a)), "σ" if rr == 22 else "Δ", over=False)
        for k in range(-7, 8):   # splash crown + the first spiral where the prongs bite the floor
            f.g.put(*P(24 + k, 0), "ψ" if k % 3 else "ω")
            if abs(k) in (5, 6): f.g.put(*P(24 + k * 1.1, -2 - (k % 2)), "σ")
        for k in range(10):
            a = math.radians(k * 50)
            r = 1.5 + k * 0.55
            f.g.put(*P(24 + r * math.cos(a), -1 + r * 0.35 * math.sin(a)), "ω" if k < 4 else "ψ")
    def swirl(n, ph):
        def fn(f, hand, tip):
            for k in range(n):
                a = math.radians(k * 40 + ph * 30)
                r = 2 + k * 0.7
                f.g.put(*P(24 + r * math.cos(a), -1 + r * 0.32 * math.sin(a)), "ψ" if k % 2 else "π")
        return fn
    whirl = [M(lean=-4, curve=1.1, hands=((-2, -40), (8, -41)), tri=spin(0, cy=-43), eye="wide", hair=0.6, hair_up=0.3,
               back_over=True, lights=2, sink=1.0),
             M(lean=-8, curve=1.2, hands=((-1, -45), (5, -46)), tri=spin(55), eye="wide", hair=0.9, hair_up=0.6, back_over=True,
               lights=2, extra=ring_smear(200, 330), fin=0.6),
             M(lean=-6, curve=1.2, hands=((0, -46), (4, -46)), tri=spin(125), eye="wide", hair=1.2, hair_up=0.8, back_over=True,
               lights=2, extra=ring_smear(240, 470, drops=6), fin=1.0, mouth=1),
             M(lean=-2, curve=1.15, hands=((1, -45), (6, -46)), tri=spin(205), eye="wide", hair=1.2, hair_up=0.9, back_over=True,
               lights=2, extra=ring_smear(300, 620, drops=10), fin=0.6, mouth=2),
             M(lean=24, curve=0.6, dx=1.5, hands=((15, -16), (17, -15)), tri=((5.5, -30), (22.5, -1)), eye="wide", hair=-0.8,
               hair_up=0.5, back_over=True, lights=2, extra=slam_fx, mouth=2, tri_glint=2, crown_sway=6),
             M(lean=22, curve=0.65, dx=1.5, hands=((15, -16.5), (17, -15.5)), tri=((5.5, -30), (22.5, -1)), eye="open", hair=-0.4,
               hair_up=0.3, back_over=True, lights=1, extra=swirl(8, 1), mouth=1, crown_sway=3),
             M(lean=10, curve=0.85, dx=0.5, hands=((2, -24), (15, -20)), tri=((10, -6), (25, -28)), eye="open", hair=0.2,
               lights=1, extra=swirl(5, 2)),
             M(lean=2, hands=((-6, -19), (12.4, -19.5)), tri=((13, -1), (13, -33)), hair=0.4, lights=1)]
    # SPEAR: coil tightens, she rears back, then lunges the trident straight out
    def lunge_lines(f, hand, tip):
        for k in range(4):
            y = -24 + (k - 1.5) * 3
            line(f.n, -10 - k * 2, y, -2 - k, y, "π" if k % 2 else "Δ")
    spear = [M(lean=-4, curve=1.1, hands=((-6, -20), (8, -24)), tri=((-6, -21), (20, -27)), eye="open", hair=0.3, lights=1),
             M(lean=-14, curve=1.35, sink=2.0, coil_rx=10.0, hands=((-9, -22), (0, -25)), tri=((-14, -22), (12, -26)),
               eye="squint", hair=0.6, hair_up=0.2, lights=2, fin=0.8),
             M(lean=10, curve=0.8, dx=1.0, coil_rx=11.5, hands=((-10, -24), (13, -24)), tri=((-1, -24), (26, -24.5)), eye="wide",
               hair=-0.6, hair_up=0.3, lights=2, tri_smear=True, extra=lunge_lines),
             M(lean=22, curve=0.5, dx=2.0, coil_rx=12.5, hands=((-12, -26), (19, -23)), tri=((7, -23.5), (34, -23)), eye="wide",
               hair=-1.0, hair_up=0.5, lights=2, mouth=2, tri_glint=2, tri_smear=True),
             M(lean=20, curve=0.55, dx=2.0, coil_rx=12.5, hands=((-11, -25), (18, -23)), tri=((6, -23.5), (33, -23)), eye="open",
               hair=-0.6, hair_up=0.4, lights=1, mouth=1, tri_glint=1),
             M(lean=8, curve=0.85, dx=1.0, hands=((-8, -22), (11, -23)), tri=((-3, -22), (23, -25)), eye="open", hair=0.2, lights=1),
             M(lean=2, hands=((-6, -19), (12.4, -19.5)), tri=((13, -1), (13, -33)), hair=0.4, lights=1)]
    def dropped(f, hand, tip):
        f2 = Fr(); trident(f2, (4, -1), (27, -6))
        for k, v in f2.b.px.items(): f.u.raw.put(k[0], k[1], v)
        for k, v in f2.g.px.items(): f.g.raw.put(k[0], k[1], v)
    death = [M(lean=-18, curve=1.3, hands=((-9, -30), (8, -32)), tri=((19, -4), (5, -34)), eye="wide", mouth=2, lights=2,
               hair=1.2, hair_up=0.6, head_tilt=-14, crown_sway=-8),
             M(lean=30, curve=1.1, sink=4.0, hands=((4, -12), (15, -8)), eye="shut", mouth=1, lights=1, hair=0.6,
               head_tilt=24, extra=dropped),
             M(lean=58, curve=0.3, sink=7.0, coil_rx=12.0, hands=((14, -4), (20, -2)), eye="dead", lights=0, hair=0.2,
               head_tilt=50, extra=dropped),
             matriarch_corpse()]
    knock = M(lean=-20, curve=1.4, hands=((-10, -27), (6, -29)), tri=((-1, -4), (19, -30)), eye="squint", mouth=1, hair=-1.0,
              hair_up=0.4, lights=2, head_tilt=-10, crown_sway=-6)
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.1] * 6),
             ("Whirl", whirl, [0.14, 0.12, 0.1, 0.1, 0.06, 0.2, 0.16, 0.16]),
             ("Spear", spear, [0.16, 0.14, 0.08, 0.06, 0.14, 0.14, 0.16])]
    anims += std_tail(idle[0], death, [0.12, 0.14, 0.18, 0.5], knock)
    m_sheet("BelMatriarch", anims, outdir, (SK.Si(80) + SK.Si(80) % 2, SK.Si(60) + 2), scale=4)


def fx_whirlpool(k=1.5):
    """Ground whirlpool, seen low: indigo disc, three cyan spiral arms (a 120-degree turn per loop), foam rim, spray.
    Drawn at its in-game size (k 1.5: 55 x 30 incl. spray) instead of a 37 x 20 sheet blown up x1.5 in the template."""
    out = []
    RX, RY = 18.0 * k, 5.2 * k
    for i in range(6):
        c = cv()
        rot = -i * (2 * math.pi / 3) / 6
        for y in range(-int(RY) - 1, int(RY) + 2):
            for x in range(-int(RX) - 1, int(RX) + 2):
                d = (x / RX) ** 2 + (y / RY) ** 2
                if d > 1.0: continue
                ch = "Δ" if d > 0.72 else "Γ" if d > 0.4 else "Β" if d > 0.14 else "Α"
                if d < 0.035: ch = "Ω"
                c.put(x, y, ch)
        for arm in range(3):
            n = int(30 * k)
            for kk in range(n):
                t = kk / (n - 1.0)
                a = rot + arm * 2 * math.pi / 3 + t * 4.6
                r = 1.5 * k + t * 15.8 * k
                ch = "ω" if t > 0.82 else "ψ" if t > 0.45 else "Ε" if t > 0.2 else "Δ"
                x, y = r * math.cos(a), r * math.sin(a) * RY / RX
                c.put(*P(x, y), ch)
                if t > 0.35: c.put(*P(x, y + 1), "Δ" if t < 0.7 else "Ε", over=False)
        # rim foam (far edge raised a pixel), turning with the arms
        nr = int(36 * k)
        for kk in range(nr):
            a = 2 * math.pi * kk / nr
            x, y = RX * math.cos(a), RY * math.sin(a)
            if (kk + i) % 3 == 0: continue
            c.put(*P(x, y - (1 if y < 0 else 0)), "σ" if (kk + i) % 3 == 1 else "π")
            if y >= 2.5 * k and (kk + i) % 2: c.put(*P(x, y + 1), "Ω")
        # spray flung up off the rim
        for kk in range(7):
            a = rot * 1.5 + kk * 2 * math.pi / 7
            x = RX * 0.85 * math.cos(a)
            h = 4 + ((i + kk * 2) % 4) * 2.5
            y0 = RY * 0.8 * math.sin(a)
            if y0 < 1:
                c.put(*P(x, y0 - h), "ω" if kk % 2 else "ψ")
                c.put(*P(x - 1 * math.sin(a), y0 - h + 2), "π", over=False)
                if kk % 3 == 0: c.put(*P(x + 1, y0 - h + 1), "ψ", over=False)
        out.append(c.spr())
    return out


SHARD = """
.ν....ν.
.μ...μ..
..λ.λ...
..λλλ..ν
...λμ.μ.
...κλλ..
..κκ....
.κκ.....
"""


def fx_coral_shard():
    """Spinning coral shard (FxCoralShard): the branch chunk turns 90 degrees per frame, cyan wake behind."""
    rows = SHARD.strip("\n").split("\n")
    base = {(x, y): ch for y, r in enumerate(rows) for x, ch in enumerate(r) if ch != "."}
    out = []
    for i in range(4):
        px = {}
        for (x, y), ch in base.items():
            for _ in range(i): x, y = 7 - y, x                 # rotate the 8x8 grid clockwise
            px[(x - 4, y - 9)] = ch
        spr = outl(Spr(px), "Ω")
        px = dict(spr.px)
        px[(1 - 4, 3 - 9)] = "Σ" if i % 2 else "ν"           # pearl glint
        for k, (x, y) in enumerate(((-6, -5), (-6, -6), (-7, -5))):
            if x >= -6: px.setdefault((x, y - (i % 2)), "ψ" if k == 0 else "Δ")
        out.append(Spr(px))
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


# ================================================================== FX
def cv():
    return Canvas()


def fx_spine():
    out = []
    for i in range(4):
        c = cv()
        y = -2
        # tapered urchin spine: violet-dark base, grey shaft, pale needle tip; dark underside
        # v0.10: lifted a step and outlined so it reads on dark floors (it was violet-grey on a dark-teal floor)
        for x in range(-5, 6):
            t = (x + 5) / 10.0
            c.put(x, y, "N" if t < 0.2 else "f" if t < 0.5 else "H" if t < 0.8 else "c")
            if t < 0.7: c.put(x, y + 1, "n" if t < 0.3 else "x")
            if t < 0.35: c.put(x, y - 1, "N" if t < 0.15 else "f")
        c.put(6, y, "c")
        c.put(-3 + (i * 2) % 7, y - (1 if (-3 + (i * 2) % 7) < -1 else 0), "c")    # travelling glint
        for k in range(3):   # wet trail specks
            c.put(-8 - k * 2 - (i % 2), y + ((k + i) % 2) - (1 if k == 2 else 0), "Q" if k == 0 else "E" if k == 1 else "d")
        out.append(c.spr())
    return out


def fx_water_bolt():
    out = []
    for i in range(4):
        c = cv()
        rx, ry = [(3.2, 3.0), (3.5, 2.8), (3.1, 3.2), (3.0, 3.3)][i]
        # spray trail first (behind)
        for k in range(5):
            x = -4 - k * 1.6 - (i % 2) * 0.8
            y = -4 + math.sin(k * 1.3 + i) * 1.6
            c.put(*P(x, y), "E" if k < 2 else "d" if k < 4 else "D")
        line(c, -3, -2, -7 - (i % 2), -1, "D")
        line(c, -3, -6, -6 - ((i + 1) % 2), -7, "D")
        ell(c, 0, -4, rx, ry, "DdEQ", bias=0.25)
        c.put(-1, -5, "c"); c.put(-1, -6 if i % 2 else -5, "c"); c.put(0, -6, "Q")
        c.put(*P(1.5, -2.5), "D")
        c.put(*P(3.5 + (i % 2), -4 + (i % 3) - 1), "Q")
        out.append(c.spr())
    return out


def fx_hook():
    out = []
    for i in range(4):
        f = Fr()
        wob = [0, -8, 0, 8][i]
        a = math.radians(wob)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        x0, y0 = -1.0, -5.0
        # shank
        e = (x0 + 5 * ux, y0 + 5 * uy)
        line(f.b, x0, y0, *e, "H")
        line(f.b, x0 + nx * -0.0, y0 + 1, e[0], e[1] + 1, "f", over=False)
        # bend + point curling back (barbed)
        pts = [e, (e[0] + 1.6 * ux + 1.4 * nx, e[1] + 1.6 * uy + 1.4 * ny),
               (e[0] + 0.6 * ux + 3.0 * nx, e[1] + 0.6 * uy + 3.0 * ny),
               (e[0] - 1.6 * ux + 3.2 * nx, e[1] - 1.6 * uy + 3.2 * ny)]
        polyline(f.b, pts, "H")
        f.b.put(*P(*pts[1]), "c")
        f.b.put(*P(pts[-1][0] - 0.8 * ux - 0.6 * nx, pts[-1][1] - 0.8 * uy - 0.6 * ny), "H")    # barb
        f.b.put(*P(e[0] - 0.2, e[1] - 1), "c")
        # rust
        f.b.put(*P(x0 + 2.5 * ux, y0 + 2.5 * uy), "a")
        # eye + short chain trailing left, links alternating
        f.b.put(*P(x0 - 1, y0), "f"); f.b.put(*P(x0 - 1, y0 - 1), "H"); f.b.put(*P(x0 - 1, y0 + 1), "f")
        for k in range(4):
            lx = x0 - 3 - k * 2
            ly = y0 + [0, 0.5, 1, 0.5][(k + i) % 4]
            if (k + i) % 2: f.b.put(*P(lx, ly), "H"); f.b.put(*P(lx - 1, ly), "f")
            else: f.b.put(*P(lx, ly - 0.5), "f"); f.b.put(*P(lx, ly + 0.5), "f"); f.b.put(*P(lx - 1, ly), "x")
        f.g.put(int(x0 - 12 - (i % 2)), int(y0), "D")
        out.append(f.done(clip=False))
    return out


def brine_puddle(spread=1.0, phase=0, fade=0.0, seed=0):
    """Low, lumpy pool of brine: a few overlapping flat lobes, dark centre, lit rim, sparse foam."""
    c = cv()
    lobes = [(0, 0, 11.5, 3.0), (-6.5, 0.3, 5.5, 2.4), (6.0, -0.2, 6.0, 2.6), (-1.5, -0.6, 7.0, 3.2)]
    inside = {}
    for (lx, ly, rx, ry) in lobes:
        rx, ry = rx * spread, max(1.0, ry * (0.5 + 0.5 * spread))
        for y in range(int(-ry) - 1, int(ry) + 2):
            for x in range(int(lx * spread - rx) - 1, int(lx * spread + rx) + 2):
                d = ((x - lx * spread) / rx) ** 2 + ((y - ly) / ry) ** 2
                if d <= 1.0:
                    inside[(x, y)] = min(inside.get((x, y), 9), d)
    for (x, y), d in inside.items():
        if fade and ((x * 7 + y * 13 + seed * 3) % 10) / 10.0 < fade: continue
        edge = any((x + a, y + b) not in inside for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            ch = "E" if (y < 0 and x < 3) else "d" if y <= 0 else "Z"
        else:
            ch = "D"
            if abs(((x + 2 * y + phase) % 7)) == 0 and d > 0.25: ch = "d"          # ripples
            if (x * 5 + y * 3 + seed) % 11 == 0: ch = "v"
        c.put(x, y - 3, ch)
    if fade < 0.7:
        # foam flecks along the top rim + a bubble
        for k in range(6):
            a = math.pi + (k + 0.5) * math.pi / 6 + phase * 0.12
            x, y = 10.0 * spread * math.cos(a), 2.6 * spread * math.sin(a)
            if (k + phase) % 2 == 0:
                c.put(*P(x, y - 3), "E")
        for (bx, by, ph) in ((-4, 0, 0), (3, 1, 1)):
            if (phase + ph) % 2 == 0:
                c.put(*P(bx * spread, by - 3), "Q")
        c.put(*P(-6 * spread, -3), "E" if phase else "d")
    return c.spr()


def fx_brine():
    spread = [brine_puddle(0.35, 0), brine_puddle(0.65, 1), brine_puddle(0.92, 0)]
    idle = [brine_puddle(1.0, 0, seed=1), brine_puddle(1.0, 1, seed=2)]
    fade = [brine_puddle(0.95, 0, 0.35), brine_puddle(0.85, 1, 0.6), brine_puddle(0.7, 0, 0.85)]
    return spread, idle, fade


def fx_wave():
    out = []
    for i in range(4):
        c = cv()
        cur = [0, 1, 2, 1][i]           # how far the lip has curled over
        H = 20 + [0, 1, 1, 0][i]
        crest = (5 + cur * 0.5, -H)
        lip = (11 + cur, -H + 4 + cur * 1.5)
        body = [(-15, 0), (-11, -2), (-6, -6), (-1, -11), (2, -16), crest, (crest[0] + 3.5, -H + 0.5), lip,
                (lip[0] - 1.5, lip[1] + 1.5), (9, -10), (11, -5), (13, -1), (14, 0)]
        poly(c, body, "d", shade=lambda x, y: "D" if y > -4 else ("d" if y > -12 else "E"))
        # hollow of the barrel under the curling lip
        ell(c, 7.5 + cur * 0.5, -H + 7.5, 2.6, 3.2, "ZZD")
        c.put(*P(8 + cur * 0.5, -H + 9), "D")
        # foam on the lip and crest, streaks on the back
        polyline(c, [(2, -16), crest, (crest[0] + 3.5, -H + 0.5), lip], "Q")
        c.put(*P(lip[0], lip[1] + 1), "E")
        for k in range(5):
            x = -12 + k * 3.2 + (i % 2) * 1.5
            y = -(x + 15) * 0.7
            c.put(*P(x, y + 1), "E"); c.put(*P(x + 1, y + 2), "d")
        # light bands on the face
        for k in range(3):
            y = -6 - k * 4 + (i % 2)
            for (lx, ly) in line_px(-1 - k * 2, y, 2 - k, y - 1):
                if (lx, ly) in c.px: c.put(lx, ly, "E")
        # spray off the lip
        for k in range(5):
            a = math.radians(-70 + k * 25 + i * 9)
            r = 2 + ((i + k) % 3)
            c.put(*P(lip[0] + 1 + r * math.cos(a), lip[1] - 2 + r * math.sin(a)), "Q" if k % 2 else "E", over=False)
        # foam boil along the floor at the front
        for x in range(7, 17):
            if (x + i) % 3: c.put(x, -1 if (x + i) % 2 else 0, "Q" if (x + i) % 4 == 0 else "E", over=False)
        out.append(c.spr())
    return out


def fx_bell_ring():
    out = []
    radii = [5, 11, 17, 22, 27]
    for i, r in enumerate(radii):
        c = cv()
        ry = r * 0.36 + 1
        n = int(r * 6)
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = r * math.cos(a), ry * math.sin(a)
            if i >= 3 and (k // 3) % 3 == 0: continue        # breaking up as it fades
            outer = "Q" if i < 2 else "E" if i < 4 else "d"
            inner = "E" if i < 2 else "d" if i < 4 else "D"
            c.put(*P(x, y), outer)
            c.put(*P(x * 0.9, y * 0.85), inner, over=False)
        # sound arcs rising off the ring
        if i < 4:
            for sd in (-1, 1):
                for k in range(-2, 3):
                    a = math.radians(k * 14)
                    rr = 3 + i * 2
                    c.put(*P(sd * (r * 0.5) + sd * rr * math.cos(a) * 0.3, -ry - 2 - i - rr * 0.4 + abs(k) * 0.6),
                          "Q" if i < 2 else "E", over=False)
        if i == 0:
            ell(c, 0, 0, 3, 1.4, "EQ", bias=0.4)
        out.append(c.spr())
    return out


def fx_song_note():
    out = []
    for i in range(6):
        c = cv()
        for j in range(3):
            t = i - j * 1.5
            if t < 0 or t > 4.5: continue
            y = -3 - t * 4.2
            rx, ry = 2 + t * 1.0, 1 + t * 0.35
            sway = math.sin(t * 1.4 + j) * 2.0
            fade = t / 4.5
            col_o = "c" if fade < 0.3 else "Q" if fade < 0.6 else "E" if fade < 0.85 else "D"
            col_i = "E" if fade < 0.5 else "D"
            n = int(8 + rx * 4)
            for k in range(n):
                a = 2 * math.pi * k / n
                if fade > 0.6 and k % 3 == 0: continue
                c.put(*P(sway + rx * math.cos(a), y + ry * math.sin(a)), col_o if math.sin(a) < 0.3 else col_i, over=False)
        # ghostly motes
        for k in range(3):
            c.put(*P(math.sin(i + k * 2) * 6, -2 - ((i * 3 + k * 7) % 20)), "E" if k % 2 else "D", over=False)
        out.append(c.spr())
    return out


def fx_splash():
    out = []
    for i in range(5):
        c = cv()
        # crown of water rising, droplets flung out, then falling to a foam ring
        h = [3, 9, 12, 8, 2][i]
        w = [4, 6, 8, 10, 11][i]
        if i < 4:
            for sd in (-1, 1):
                for k in range(3):
                    x0 = sd * (2 + k * 1.6) * (w / 8.0)
                    hh = h * (1 - 0.25 * k)
                    lean = sd * (2.0 + i * 1.6 + k * 0.8)
                    line(c, x0, 0, x0 + lean, -hh, "dE" if k else "EQ")
                    c.put(*P(x0 + lean, -hh - 1), "Q")
            line(c, -1, 0, 0, -h * 0.6 if i < 3 else -1, "E")
        rnd = random.Random(3)
        for k in range(10):
            a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
            sp = rnd.uniform(0.6, 1.0)
            t = (i + 0.5) / 4.0
            x = math.cos(a) * w * 1.1 * sp * (0.4 + t)
            y = math.sin(a) * 14 * sp * t * (1.4 - t) + t * t * 3
            if y > 0: y = 0
            if i >= 1:
                c.put(*P(x, y), "Q" if k % 3 == 0 else "E")
        for x in range(-w, w + 1):
            if i >= 1 and (x + i) % 2 == 0: c.put(x, 0, "d")
        if i >= 2:
            for x in (-w, w): c.put(x, -1, "E")
        out.append(c.spr())
    return out


def build_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxSpine"):
        fx_sheet("FxSpine", [("Fly", fx_spine(), [0.05] * 4)], outdir)
    if want("FxWaterBolt"):
        fx_sheet("FxWaterBolt", [("Fly", fx_water_bolt(), [0.07] * 4)], outdir)
    if want("FxHook"):
        fx_sheet("FxHook", [("Fly", fx_hook(), [0.06] * 4)], outdir)
    if want("FxBrine"):
        sp, idl, fd = fx_brine()
        life = sp + idl * 10 + fd
        fx_sheet("FxBrine", [("Life", life, [0.12] * 3 + [0.37] * 20 + [0.2] * 3),
                             ("Spread", sp, [0.12] * 3), ("Idle", idl, [0.37, 0.37]), ("Fade", fd, [0.2] * 3)], outdir)
    if want("FxWave"):
        fx_sheet("FxWave", [("Fly", fx_wave(), [0.08] * 4)], outdir, scale=6)
    if want("FxBellRing"):
        fx_sheet("FxBellRing", [("Play", fx_bell_ring(), [0.05, 0.06, 0.07, 0.08, 0.1])], outdir, scale=5)
    if want("FxSongNote"):
        fx_sheet("FxSongNote", [("Play", fx_song_note(), [0.1] * 6)], outdir)
    if want("FxSplash"):
        fx_sheet("FxSplash", [("Play", fx_splash(), [0.05, 0.06, 0.07, 0.09, 0.12])], outdir)
    if want("FxWhirlpool"):
        fx_sheet_fixed("FxWhirlpool", [("Loop", fx_whirlpool(), [0.08] * 6)], outdir, (60, 30), (30, 19), scale=5)
    if want("FxCoralShard"):
        fx_sheet_fixed("FxCoralShard", [("Fly", fx_coral_shard(), [0.06] * 4)], outdir, (12, 12), (6, 11), scale=10)


# ================================================================== ICONS + GOD PORTRAIT
def icon_frame(c):
    sp = Spr({k: v for k, v in c.px.items() if -7 <= k[0] <= 6 and -14 <= k[1] <= -1})
    return outl(sp, "Z")


def icon_tidecaller(ph):
    c = cv()
    # conch: stepped spire at the upper left, fat body whorl, flared lip and pink aperture at the right
    poly(c, [(-7, -13), (-3, -12), (1, -11.5), (5, -10), (6.5, -6), (5, -2), (1, -1.5), (-3, -4), (-5, -8)], "w",
         shade=lambda x, y: pick("hiwWX", 0.9 - (x + 7) * 0.06 - (y + 13) * 0.11 + (0.4 if (x + y) % 5 == 0 and y < -8 else 0)))
    # spiral sutures following the spire steps
    for (x0, y0, x1, y1) in ((-6, -12, -3, -10), (-3, -11, 1, -8), (0, -10, 4, -6)):
        line(c, x0, y0, x1, y1, "h")
    # shoulder knobs
    for (x, y) in ((-4, -12), (0, -11), (3, -10)):
        c.put(x, y - 1, "W"); c.put(x, y, "X")
    # aperture
    ell(c, 3.6, -4.2, 1.8, 2.6, "pPF", ang=-25, bias=0.35)
    c.put(5, -2, "w"); c.put(6, -3, "W"); c.put(6, -5, "W")
    # barnacle + verdigris
    c.put(-2, -5, "f"); c.put(-1, -5, "z"); c.put(-3, -6, "d")
    c.put(-1, -9, "X" if ph == 0 else "W"); c.put(2, -7 if ph else -8, "X")
    out = icon_frame(c)
    if ph:   # a faint call ringing out of the mouth
        out = merge(out, Spr({(6, -12): "E", (5, -13): "Q", (6, -1): "E"}))
    return out


def icon_brine_flask(ph):
    c = cv()
    # round-bellied bottle of murky green seawater, cork, glass glints
    ell(c, 0, -5.0, 5.0, 4.6, "zxxf", bias=0.0)
    for y in range(-10, -6):
        for x in (-1, 0, 1): c.put(x, y, "f" if x < 0 else "x")
    for x in (-2, -1, 0, 1, 2): c.put(x, -11, "T" if x < 2 else "t")
    for x in (-1, 0, 1): c.put(x, -12, "T" if x < 1 else "t")
    # liquid
    ell(c, 0, -4.2, 4.2, 3.6, "LvdE", bias=0.15, vmin=-0.45)
    line(c, -3, -6, 3, -6, "E")
    c.put(-1, -2, "Q" if ph == 0 else "E"); c.put(1, -4 if ph == 0 else -5, "Q")      # bubbles
    c.put(2, -3, "d"); c.put(-2, -4, "v")
    # glass highlight
    c.put(-3, -7, "c"); c.put(-4, -6, "c" if ph else "Q"); c.put(-4, -5, "Q"); c.put(-1, -9, "H")
    c.put(3, -1, "D")
    return icon_frame(c)


def icon_bell_toll(ph):
    c = cv()
    sw = [0, 8][ph]
    church_bell(c, c, 0, -7.0, 90 + sw, size=5.0, crack=False, seed=9, round_=True)
    # yoke + clapper
    for x in (-1, 0, 1): c.put(x, -13, "A")
    c.put(*P(1 if ph else 0, -1), "J"); c.put(*P(1 if ph else 0, -2), "A")
    # crack
    for (x, y) in ((2, -3), (1, -4), (2, -5), (1, -6)): c.put(x, y, "Z")
    out = icon_frame(c)
    if ph:
        out = merge(out, Spr({(-7, -9): "E", (-7, -10): "Q", (6, -6): "Q", (6, -5): "E"}))
    else:
        out = merge(out, Spr({(-1, -11): "X"}))
    return out


def icon_undertow(ph):
    c = cv()
    ell(c, 0, -7, 6.6, 6.2, "ZDDd", bias=-0.1)
    rot = ph * 0.6
    for arm in range(3):
        for k in range(24):
            t = k / 23.0
            a = rot + arm * 2 * math.pi / 3 + t * 4.2
            r = 0.6 + t * 5.6
            ch = "Q" if t > 0.75 else "E" if t > 0.4 else "d"
            c.put(*P(r * math.cos(a), -7 + r * math.sin(a) * 0.95), ch)
    c.put(0, -7, "Z"); c.put(-1, -7, "Z")
    c.put(*P(3 * math.cos(rot + 1), -7 + 3 * math.sin(rot + 1)), "c")
    return icon_frame(c)


def deity_portrait(ph):
    c = cv()
    sway = [0, 1, 0, -1][ph]
    # teal gloom: lighter near the surface, sinking to black
    for y in range(-23, 1):
        for x in range(-14, 15):
            d = (y + 23) / 23.0 + 0.12 * abs(x) / 14.0
            ch = "D" if d < 0.22 else ("z" if d < 0.62 else "Z")
            if 0.18 < d < 0.3 and (x + y) % 2 == 0: ch = "z"         # dithered band
            if 0.58 < d < 0.68 and (x + y) % 2 == 0: ch = "Z"
            c.put(x, y, ch)
    # two faint god-rays
    for (x0, w) in ((-10, 2), (7, 1)):
        for y in range(-23, -9):
            for k in range(w):
                if (y + ph + k) % 3: c.put(x0 + k + (y + 23) // 5, y, "D")
    # chain from the surface
    for y in range(-23, -19):
        c.put(int(sway * 0.5), y, "x" if (y + ph) % 2 else "f")
    # the bell
    bx = sway * 0.5
    church_bell(c, c, bx, -14.0, 90 - sway * 3, size=6.0, crack=True, seed=4, round_=True)
    # the open mouth seen from slightly below, a drowned face peering out of the dark
    my = -6
    ell(c, bx, my + 0.5, 6.4, 3.0, "ZZZ")
    ell(c, bx, my + 0.8, 3.0, 2.8, "zMCC", bias=0.25)
    eye = "c" if ph != 2 else "Q"
    for ex in (-1.4, 1.4):
        c.put(*P(bx + ex, my + 0.3), eye); c.put(*P(bx + ex, my - 0.7), "Z")
    c.put(*P(bx + 1.4, my + 1.3), "B")
    c.put(*P(bx, my + 2.4), "Z"); c.put(*P(bx, my + 3.4), "j" if ph % 2 else "Z"); c.put(*P(bx - 1, my + 2.4), "z")
    # lip of the bell over the mouth (bright rim)
    for x in range(-6, 7):
        c.put(*P(bx + x, my - 2), "w" if x < 0 else "e")
    # kelp hair / tentacles drifting from the mouth
    for k, x0 in enumerate((-5, -3, 3, 5)):
        for j in range(5):
            c.put(*P(x0 + bx + math.sin(j * 0.9 + ph + k) * 0.9, my + 3 + j), "Lvl"[(j + k) % 3] if k % 2 else ("q" if j % 2 else "j"))
    # bubbles rising
    for k, (bx_, by) in enumerate(((-9, -4), (10, -8), (-7, -15), (8, -17), (-11, -20))):
        yy = by - ph * 2 - (k % 2)
        if yy < -23: yy += 20
        c.put(bx_, yy, "Q" if k % 2 else "E")
        if k % 2 == 0: c.put(bx_ + 1, yy - 1, "d")
    return Spr({k: v for k, v in c.px.items() if -14 <= k[0] <= 14 and -23 <= k[1] <= 0})


def build_icons(outdir):
    for name, fn in (("IconTidecaller", icon_tidecaller), ("IconBrineFlask", icon_brine_flask),
                     ("IconBellToll", icon_bell_toll), ("IconUndertow", icon_undertow)):
        frames = [fn(0), fn(1)]
        # first drafts only: the shipped item icons are art/out_icons_v2 (tools/sprites/items_v2_icons.py). Kept out
        # of art/out* so the flat deploy folder never gets a second, different sheet with the same id.
        idir = os.path.join(os.path.dirname(os.path.dirname(HERE_DIR)), "art", "raw", "icon_drafts")
        img, man = pack(name, [("Idle", frames, [0.5, 0.5])], 16, 16, (8, 15), idir)
        preview(img, man, os.path.join(idir, name + "_preview.png"), scale=10)
        BUILT[name] = {"cell": (16, 16), "feet": (8, 15), "anims": [("Idle", 2, [0.5, 0.5])], "img": img, "man": man}
        print("built", name)
    frames = [deity_portrait(i) for i in range(4)]
    img, man = pack("DeityBelMora", [("Idle", frames, [0.3, 0.25, 0.3, 0.25])], 29, 24, (14, 23), outdir)
    preview(img, man, os.path.join(outdir, "DeityBelMora_preview.png"), scale=10)
    BUILT["DeityBelMora"] = {"cell": (29, 24), "feet": (14, 23), "anims": [("Idle", 4, [0.3, 0.25, 0.3, 0.25])], "img": img, "man": man}
    crop = img.crop((0, 0, 29 * 4, 24)).load()
    assert all(crop[x, y][3] == 255 for x in range(29 * 4) for y in range(24)), "portrait must be opaque"
    print("built DeityBelMora (opaque)")


# ================================================================== v0.7.2 tree: four new monsters (drawn at final size)
# BELL HERMIT (T2, Crab line), BRINE LAMPREY (T2, Lurefish line), DROWNED CAPTAIN (T3, Diver + Siren lines),
# ABYSS KRAKEN (T3, Hermit + Lamprey lines). No design scale: every number below is a final pixel.

# ------------------------------------------------------------------ BELL HERMIT (T2)
# A hermit crab living in a sunken ship's bell: the bell lies on its side on the crab's back, mouth forward, and
# the maroon crab (Barnacle Crab colours) spills out of it: stalk eyes over the lip, one huge crusher claw,
# spindly legs. Shell special: it tips the bell down over itself like a dome and the bell rings.
def hermit_bell(f, cx, cy, ang, size=6.2, ring=0, glint=False, seed=71):
    """The shell: round bronze bell + a few barnacles + kelp, dark mouth. Returns (crown, mouth, vdir, mw)."""
    cr, mo, vd, mw = church_bell(f.b, f.g, cx, cy, ang, size=size, crack=False, ring=ring, seed=seed, round_=True)
    vx, vy = vd
    ux, uy = -vy, vx
    # the dark opening seen a little from the front
    ell(f.b, mo[0] - vx * 0.3, mo[1] - vy * 0.3, 1.4, mw - 0.8, "ZZj", ang=ang)
    barnacles(f.b, [(cx - vx * 3.5 - ux * 1.8, cy - vy * 3.5 - uy * 1.8), (cx + vx * 1.5 - ux * 4.5, cy + vy * 1.5 - uy * 4.5)],
              seed=seed, big=True)
    kelp(f.b, int(round(cx - vx * 1 + ux * 3.0)), int(round(cy - vy * 1 + uy * 3.0)), 4, 0.6, seed=seed % 5)
    if glint: f.g.put(*P(cx - vx * 2 - ux * 2.5, cy - vy * 2 - uy * 2.5), "X")
    return cr, mo, vd, mw


def bell_low(ang, size=6.2):
    """How far below its centre a hermit bell at this angle reaches (its lowest lip point)."""
    a = math.radians(ang)
    mw = size * 1.02
    return math.sin(a) * size + abs(math.cos(a)) * mw


def hermit(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, claw=(-30, -5, 30), small=(60, 110), eyes=1.0, eye="open", tuck=0.0,
           ring=0, lift=0.0, extra=None, glint=False, bell_ang=None, bubble=None, reach=0.0):
    """The bell sits on the crab like a dome, crown up and tipped back; the crab's front, eyes, legs and the
    crusher claw come out from under the forward lip. tuck 1 = the bell is set down flat over the crab."""
    f = Fr()
    ang = (70.0 + tilt) if bell_ang is None else bell_ang
    ang = ang + (90.0 - ang) * tuck
    bx = dx - 2.5 + 1.5 * tuck
    floor_gap = 4.2 * (1 - tuck)
    by = -0.6 - floor_gap - lift + dy - bell_low(ang)
    vx, vy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    mo0 = (bx + vx * 6.2, by + vy * 6.2)                 # mouth centre (before drawing)
    if tuck < 0.7:
        hb = (mo0[0] + 3.2 + reach, mo0[1] + 1.2)
        # far legs in shadow (no outline), the small claw and the crab body under the bell (outlined)
        for k in range(3):
            ph = legs + k * 2.4 + math.pi
            root = (hb[0] - 5.5 + k * 2.0, hb[1] + 0.5)
            knee = (root[0] - 1.5 + k * 0.6, root[1] - 1.2 - 0.6 * max(0.0, math.sin(ph)))
            foot = (root[0] - 2.5 + k * 1.2 + 1.0 * math.sin(ph), -max(0.0, 1.0 * math.cos(ph)) - lift)
            line(f.n, *root, *knee, "j"); line(f.n, *knee, *foot, "j")
        crab_claw(f.u, hb[0] - 0.5, hb[1] - 0.2, small[0], small[1], 6, big=0.5, ramp="ZkpP")
        ell(f.u, hb[0] - 2.5, hb[1] - 0.5, 5.0, 2.6, CRAB, bias=0.2)
        ell(f.u, hb[0], hb[1] - 0.8, 2.6, 2.4, CRAB, bias=0.3)
        line(f.u, hb[0] - 1.0, hb[1] + 1.0, hb[0] + 1.8, hb[1] + 0.6, "j")
    bres = hermit_bell(f, bx, by, ang, ring=ring, glint=glint)
    cr, mo, vd, mw = bres
    tip = None
    if tuck < 0.7:
        if eyes > 0.15:
            for k, ox in enumerate((0.4, 2.2)):
                b0 = (hb[0] + ox - 0.4, hb[1] - 2.2)
                h = 3.6 * eyes
                line(f.b, *b0, b0[0] + 0.4 + k * 0.5, b0[1] - h, "jp")
                ex, ey = P(b0[0] + 0.4 + k * 0.5, b0[1] - h - 0.8)
                if eye == "open": f.g.put(ex, ey, "c"); f.g.put(ex, ey - 1, "Q")
                elif eye == "squint": f.g.put(ex, ey, "E")
                elif eye == "wide": f.g.put(ex, ey, "c"); f.g.put(ex, ey - 1, "c"); f.g.put(ex + 1, ey, "Q")
                else: f.g.put(ex, ey, "x")
        # near walking legs: from under the lip, arching out to the floor
        for k in range(3):
            ph = legs + k * 2.1
            root = (hb[0] - 4.5 + k * 2.2, hb[1] + 1.4)
            up = 1.4 + 0.9 * max(0.0, math.sin(ph))
            knee = (root[0] + 1.4 + k * 0.4, root[1] - up + 0.4)
            foot = (root[0] + 2.4 + k * 0.8 + 1.0 * math.sin(ph), -max(0.0, 1.2 * math.cos(ph)) - lift)
            line(f.b, *root, *knee, "p"); line(f.b, *knee, *foot, "p")
            f.b.put(*P(*knee), "P"); f.b.put(*P(*foot), "f")
        # the crusher claw (the Barnacle Crab's, grown fat and barnacled)
        tip = crab_claw(f.b, hb[0] + 1.6, hb[1] + 0.4, claw[0], claw[1], claw[2], big=0.95, ramp="jpPa")
    else:
        # withdrawn: a glint of eyes under the rim and the claw tip jammed in the opening
        if eye != "dead":
            f.g.put(*P(mo[0] + 1.0, -1.6), "E"); f.g.put(*P(mo[0] + 2.5, -1.6), "D")
        ell(f.b, mo[0] + mw - 1.0, -1.2, 1.8, 1.1, "jpP", bias=0.2)
    if bubble:
        for (bx_, by_) in bubble:
            f.g.put(*P(bx + bx_, by + by_), "Q"); f.g.put(*P(bx + bx_ + 1, by + by_), "E", over=False)
    if extra: extra(f, bres, tip)
    return f.done()


def hermit_corpse():
    f = Fr()
    # the bell rolled onto its back, mouth up; the crab hangs limp out of it over the rim
    cr, mo, vd, mw = hermit_bell(f, -2.0, -6.0, -100, size=5.8)
    tube(f.b, [(mo[0] + 2, mo[1] + 2), (5.5, -3.0), (8.5, -1.0)], [2.0, 1.8, 1.3], CRAB)
    crab_claw(f.b, 6.0, -1.5, 10, 15, 35, big=1.0)
    for k in range(3):
        line(f.b, 2 + k * 1.5, -2.5, 3.5 + k * 1.8, -0.0, "p")
    f.g.put(5, -4, "x"); f.g.put(6, -5, "x")
    return f.done()


def build_hermit(outdir):
    H = hermit
    idle = [H(claw=(-28, -6, 26), legs=0.0),
            H(claw=(-26, -3, 32), legs=0.3, dy=0.3, eyes=0.95),
            H(claw=(-24, -1, 34), legs=0.5, dy=0.4, eyes=0.85, eye="squint", glint=True),
            H(claw=(-30, -8, 22), legs=0.2, dy=0.1)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(H(legs=ph * 1.5, dy=-0.6 * abs(math.sin(ph)), tilt=4 * math.sin(ph), lift=0.5 * abs(math.sin(ph)),
                     claw=(-34 + 6 * math.sin(ph), -10 + 5 * math.sin(ph), 22 + 8 * math.cos(ph)), eyes=1.0 - 0.1 * (i % 2)))
    # CRUSH: claw raised wide, reared back, lunge, SNAP at full reach, grind, recover
    def snap_fx(n):
        def fn(f, bres, tip):
            if tip is None: return
            for k, (a, b) in enumerate(((2, -2), (3, 0), (2, 2), (4, -3), (4, 2), (5, 0))[:n]):
                f.g.put(*P(tip[0] + a, tip[1] + b), "Q" if k % 2 == 0 else "E")
        return fn
    crush = [H(claw=(-80, -50, 40), tilt=-6, dx=-0.5, eye="wide", legs=0.4),
             H(claw=(-110, -90, 58), tilt=-12, dx=-1.2, dy=0.3, eye="wide", legs=0.8),
             H(claw=(-25, -2, 60), tilt=6, dx=1.5, legs=1.6, eye="wide", reach=1.0),
             H(claw=(-4, 8, -6), tilt=8, dx=2.5, legs=2.0, eye="squint", reach=1.5, extra=snap_fx(6)),
             H(claw=(-6, 6, -4), tilt=7, dx=2.2, legs=2.0, eye="squint", reach=1.2, extra=snap_fx(3)),
             H(claw=(-20, -2, 14), tilt=3, dx=1.0, legs=1.4),
             H(claw=(-28, -6, 24), tilt=0, dx=0.2, legs=0.6)]
    # SHELL: tuck in, the bell tips over and slams down ringing, rings on, peeks, comes out
    shell = [H(tuck=0.45, claw=(30, 80, 0), eyes=0.4, eye="squint", legs=0.4),
             H(tuck=1.0, lift=1.5, ring=0, eye="squint", bubble=[(5, -6)]),
             H(tuck=1.0, ring=2, eye="squint"),
             H(tuck=1.0, lift=0.3, ring=1, eye="squint", bubble=[(5, -9)]),
             H(tuck=1.0, ring=2, eye="squint"),
             H(tuck=1.0, lift=0.3, ring=1, eye="squint", bubble=[(4, -11), (6, -8)]),
             H(tuck=1.0, ring=0, eye="open"),
             H(tuck=0.3, claw=(-28, -6, 24), eye="open", legs=1.0)]
    death = [H(claw=(-100, -70, 40), tilt=-12, eye="wide", dx=-0.5, legs=1.0),
             H(claw=(-140, 170, 30), tilt=-30, dy=0.5, eye="dead", eyes=0.6, legs=2.0),
             grounded(H(bell_ang=-40, claw=(170, 120, 20), eyes=0.5, eye="dead", legs=2.5)),
             hermit_corpse()]
    knock = H(claw=(-110, -60, 35), tilt=-14, dx=-0.6, eye="squint", legs=0.8, lift=0.6)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.08] * 6),
             ("Crush", crush, [0.14, 0.14, 0.07, 0.06, 0.12, 0.12, 0.14]),
             ("Shell", shell, [0.12, 0.12, 0.14, 0.36, 0.36, 0.36, 0.36, 0.16])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelHermit", anims, outdir, scale=6)


# ------------------------------------------------------------------ BRINE LAMPREY (T2)
# A long slate-grey lamprey that slithers on the floor and rears its neck; a round sucker mouth ringed with
# hooked teeth, seven glowing gill pores along the neck, ragged dorsal fins near the tail. Drinks blood.
LAMP = "jzxM"
LAMP_B = "xMCC"


def lamp_spine(dx=0.0, dy=0.0, phase=0.0, amp=1.0, neck=1.0, head=(0.0, 0.0), lunge=0.0, tail_up=0.0, length=0.92):
    """Control points tail -> head (a floor S-wave, then the neck rising to the head)."""
    pts = []
    n = 6
    for k in range(n):
        x = dx - 13.0 * length + k * 2.9 * length + lunge * k / n * 0.6
        y = -2.0 - amp * math.sin(k * 1.15 + phase) * (0.4 + 0.6 * k / n) - (tail_up if k == 0 else 0)
        pts.append((x, y))
    nb = pts[-1]
    hx = nb[0] + 4.5 + lunge + head[0]
    hy = -3.0 - 8.0 * neck + dy + head[1]
    pts.append((nb[0] + 1.2 + lunge * 0.5, nb[1] - 2.5 * neck))           # the neck lifts off the floor...
    pts.append((nb[0] + 1.0 + lunge * 0.7 + head[0] * 0.4, hy - 0.5))       # ...curls over like a swan's...
    pts.append((hx, hy))                                                      # ...and the head points forward
    return pts


def lamprey(spine=None, mouth=0, eye="open", gills=1, extra=None, fin=0.0, hdir=None, ripple=None, sink=None, **kw):
    """spine: control points tail -> head (default from lamp_spine(**kw)); hdir: head direction in degrees
    (default: along the last segment); mouth 0 shut .. 3 gaping; gills 0 dark .. 2 bright."""
    f = Fr()
    pts = spine if spine is not None else lamp_spine(**kw)
    rad = [0.5, 1.0, 1.5, 1.9, 2.2, 2.3, 2.3, 2.1, 2.3][-len(pts):] if len(pts) <= 9 else [0.5] + [2.2] * (len(pts) - 1)
    sp, sr = catmull(pts, rad, step=0.8)
    # dorsal fins on the rear third (behind the body)
    for i in range(3, int(len(sp) * 0.45), 2):
        (x0, y0), (x1, y1) = sp[i], sp[i + 1]
        tl = math.hypot(x1 - x0, y1 - y0) or 1
        nx_, ny_ = (y1 - y0) / tl, -(x1 - x0) / tl          # "up" normal
        if ny_ > 0: nx_, ny_ = -nx_, -ny_
        h = 1.6 + 0.8 * math.sin(i * 0.9 + fin * 2)
        f.u.put(*P(x0 + nx_ * (sr[i] + h * 0.5), y0 + ny_ * (sr[i] + h * 0.5)), "D")
        f.u.put(*P(x0 + nx_ * (sr[i] + h), y0 + ny_ * (sr[i] + h)), "d" if i % 4 else "E")
    # tail fin
    tx, ty = sp[0]
    for a in (-160, 180, 160):
        line(f.u, tx, ty, tx + 3.0 * math.cos(math.radians(a)), ty + 2.5 * math.sin(math.radians(a)), "Dd")
    # body
    def skin(x, y):
        return None
    tube(f.b, sp, sr, LAMP, bias=0.0)
    # pale belly band along the underside + dark mottling on the back
    for i in range(1, len(sp) - 1):
        (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
        tl = math.hypot(x1 - x0, y1 - y0) or 1
        nx_, ny_ = -(y1 - y0) / tl, (x1 - x0) / tl
        if ny_ < 0: nx_, ny_ = -nx_, -ny_                    # downward normal
        r = sr[i]
        if r > 1.0:
            f.b.put(*P(sp[i][0] + nx_ * r * 0.6, sp[i][1] + ny_ * r * 0.6), "M" if i % 3 else "C")
        if i % 5 == 2 and r > 1.4:
            f.b.put(*P(sp[i][0] - nx_ * r * 0.3, sp[i][1] - ny_ * r * 0.3), "j")
    barnacles(f.b, [sp[len(sp) // 3], sp[len(sp) // 2 + 2]], seed=81)
    # head: blunt, a little fatter than the neck; the oral disc faces along hdir
    hx, hy = pts[-1]
    if hdir is None:
        px_, py_ = sp[-3]
        hdir = math.degrees(math.atan2(hy - py_, hx - px_))
    a = math.radians(hdir)
    ux, uy = math.cos(a), math.sin(a)
    nx_, ny_ = -uy, ux
    ell(f.b, hx - ux * 0.5, hy - uy * 0.5, 3.4, 2.7, LAMP, ang=hdir, bias=0.25)
    # gill pores: seven glowing dots trailing back down the neck from behind the head
    gp = []
    seen = set()
    for i in range(len(sp) - 5, 0, -1):
        q = P(*sp[i])
        if q in seen or math.hypot(q[0] - hx, q[1] - hy) < 3.5: continue
        if gp and abs(q[0] - gp[-1][0]) + abs(q[1] - gp[-1][1]) < 2: continue
        seen.add(q); gp.append(q)
        if len(gp) == 7: break
    for k, (x, y) in enumerate(gp):
        f.g.put(x, y, ("c" if k % 2 == 0 else "B") if gills >= 2 else ("E" if k % 2 == 0 else "d") if gills else "z")
    # oral disc
    dcx, dcy = hx + ux * 2.6, hy + uy * 2.6
    R = 1.8 + 0.55 * mouth
    # the sucker: a pale toothed rim around a dark (or, gaping, raw red) throat, facing forward
    ell(f.b, dcx, dcy, 1.0 + 0.25 * mouth, R, "xfH", ang=hdir, bias=0.3)
    n = int(R * 2) + 1
    for k in range(n):
        t = (k / max(1, n - 1)) * 2 - 1
        f.b.put(*P(dcx + ux * 0.6 + nx_ * t * (R - 0.2), dcy + uy * 0.6 + ny_ * t * (R - 0.2)), "H" if k % 2 == 0 else "f")
    inner = max(0.6, R - 1.2)
    for k in range(-int(inner), int(inner) + 1):
        f.b.put(*P(dcx + ux * 0.9 + nx_ * k, dcy + uy * 0.9 + ny_ * k), ("p" if abs(k) < inner - 0.5 else "j") if mouth >= 2 else "Z")
    # eye: small, pale, set back on top of the head
    ex, ey = P(hx + ux * 0.6 - nx_ * 1.3, hy + uy * 0.6 - ny_ * 1.3)
    if eye == "open": f.g.put(ex, ey, "c"); f.g.put(ex - 1, ey, "Q")
    elif eye == "wide": f.g.put(ex, ey, "c"); f.g.put(ex - 1, ey, "c"); f.g.put(ex, ey - 1, "Q")
    elif eye == "squint": f.g.put(ex, ey, "E")
    else: f.g.put(ex, ey, "x")
    if ripple is not None:
        rx_, rr = ripple
        for k in range(-int(rr), int(rr) + 1):
            f.g.put(*P(rx_ + k, 0), "E" if abs(k) > rr - 2 else "d", over=False)
            if abs(k) == int(rr) - 1 or abs(k) == int(rr * 0.5): f.g.put(*P(rx_ + k, -1), "Q", over=False)
    if extra: extra(f, (hx, hy), (dcx, dcy), hdir)
    spr = f.done()
    if sink is not None:   # everything left of x = sink[0] ... hidden below the floor line already; cut the
        lo, hi = sink      # part that has slid "into" the floor between x lo and hi
        spr = Spr({k: v for k, v in spr.px.items() if not (lo <= k[0] <= hi and k[1] > -3)})
    return spr


def lamprey_corpse():
    pts = [(-13, -1.5), (-9, -2.0), (-5, -1.4), (-1, -2.2), (3, -1.6), (7, -1.8), (10, -2.0)]
    return lamprey(spine=pts, mouth=1, eye="dead", gills=0, hdir=10)


def ripple_only(x, r, drops=0):
    c = Canvas()
    for k in range(-int(r), int(r) + 1):
        c.put(*P(x + k, 0), "E" if abs(k) > r - 2 else "d")
        if abs(k) in (int(r) - 1, int(r * 0.5)): c.put(*P(x + k, -1), "Q")
    for k in range(drops):
        c.put(*P(x - 3 + k * 2, -2 - (k % 2) * 2), "Q" if k % 2 else "E")
    return c.spr()


def build_lamprey(outdir):
    L = lamprey
    idle = [L(phase=i * 0.5, amp=1.0, neck=1.0, head=(0, [0, -0.4, -0.6, -0.2][i]), mouth=[0, 1, 1, 0][i], gills=[1, 1, 2, 1][i],
              fin=i * 0.3, eye="open" if i != 3 else "squint") for i in range(4)]
    run = [L(phase=i * math.pi / 3 * 2, amp=1.6, neck=0.75, lunge=0.5, head=(0, -0.5 * abs(math.sin(i))), mouth=0, gills=1,
             fin=i * 0.6) for i in range(6)]
    # LEECH: coil back, rear high, lunge (sucker wide), CLAMP at full reach, suck (gills pulse), let go, settle
    def drain(n):
        def fn(f, hd, disc, hdir):
            for k in range(n):
                f.g.put(*P(disc[0] + 2 + (k % 2), disc[1] - 2 + k * 1.5), "r" if k % 2 else "R")
        return fn
    leech = [L(phase=0.6, amp=1.4, neck=1.2, head=(-3.0, -1.0), lunge=-1.0, mouth=1, eye="wide", gills=1, hdir=-20),
             L(phase=0.9, amp=1.8, neck=1.35, head=(-4.5, -1.5), lunge=-1.5, mouth=2, eye="wide", gills=2, hdir=-35),
             L(phase=1.4, amp=0.6, neck=0.75, head=(3.5, 1.0), lunge=4.0, mouth=3, eye="wide", gills=2, hdir=5, length=1.0),
             L(phase=1.6, amp=0.4, neck=0.7, head=(4.5, 1.5), lunge=5.0, mouth=1, eye="squint", gills=2, hdir=10, length=1.02,
               extra=drain(3)),
             L(phase=1.8, amp=0.5, neck=0.72, head=(4.0, 1.5), lunge=4.6, mouth=1, eye="squint", gills=2, hdir=8, length=1.0,
               extra=drain(4)),
             L(phase=2.0, amp=0.9, neck=0.9, head=(1.5, 0.5), lunge=2.0, mouth=2, eye="open", gills=1, hdir=-5),
             L(phase=2.2, amp=1.0, neck=1.0, mouth=0, eye="open", gills=1)]
    # DIVE: rear up, arc over, head into the floor, body slides under, gone (ripples), surface, BITE, settle
    def arc(t):
        # head goes from raised (t=0) to under the floor ahead (t=1)
        return lamp_spine(phase=1.0, amp=1.2, neck=1.2 - 1.6 * t, head=(1.5 + 3.0 * t, 2.0 * t), lunge=1.0)
    dive = [L(phase=0.4, amp=1.5, neck=1.4, head=(-1.0, -1.5), mouth=0, eye="wide", gills=2, hdir=-60),
            L(spine=arc(0.45), mouth=0, eye="wide", gills=2, hdir=45),
            L(spine=arc(1.0), mouth=0, eye="squint", gills=2, hdir=85, ripple=(9, 4)),
            L(spine=[(x + 6, y) for (x, y) in arc(1.0)], mouth=0, eye="squint", gills=1, hdir=85, ripple=(10, 5), sink=(5, 30)),
            ripple_only(4, 6, drops=3),
            ripple_only(0, 3),
            L(spine=[(-4, 6), (-3, 3), (-2, 0), (-1.5, -3), (-0.5, -7), (0.5, -11)], mouth=3, eye="wide", gills=2, hdir=-60,
              ripple=(-1, 5)),
            L(spine=[(-6, 4), (-5, 2), (-3.5, -0.5), (-1.5, -3), (1.5, -6), (5.5, -8)], mouth=1, eye="squint", gills=2, hdir=15,
              ripple=(-3, 4), extra=drain(3)),
            L(phase=0.2, amp=1.0, neck=1.0, mouth=0, eye="open", gills=1)]
    death = [L(phase=1.0, amp=2.0, neck=1.5, head=(-3, -2), mouth=3, eye="wide", gills=2, hdir=-70),
             L(phase=1.6, amp=1.6, neck=0.6, head=(2, 2), mouth=2, eye="squint", gills=1, hdir=40),
             L(phase=2.2, amp=1.0, neck=0.1, head=(3, 1), mouth=1, eye="dead", gills=0, hdir=20),
             lamprey_corpse()]
    knock = L(phase=0.8, amp=1.8, neck=1.3, head=(-3.5, -1.0), lunge=-1.5, mouth=1, eye="squint", gills=1, hdir=-40)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.08] * 6),
             ("Leech", leech, [0.14, 0.12, 0.06, 0.07, 0.16, 0.12, 0.14]),
             ("Dive", dive, [0.12, 0.1, 0.08, 0.08, 0.1, 0.14, 0.08, 0.08, 0.16])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("BelLamprey", anims, outdir, scale=6)


# ------------------------------------------------------------------ DROWNED CAPTAIN (T3, Diver + Siren lines)
# A bloated drowned sea captain: barnacled tricorn, one glowing eye, a kelp beard, a long navy greatcoat with
# brass buttons and a blood-red sash, an iron gaff hook for a right hand and a bell-mouthed brass blunderbuss in
# the left. Upright and tall where the Drowned Bell is a hunched heap and the Matriarch a coiled serpent.
PALETTE.update({
    # v0.8: the navy ramp lifted (the captain averaged luminance 62, a dark smear on the dungeon floor)
    'ρ': (0x26, 0x30, 0x4c),   # coat navy ramp, dark -> light
    'τ': (0x3c, 0x4e, 0x7c),
    'υ': (0x58, 0x70, 0xa8),
    'χ': (0x84, 0x9c, 0xd0),
})
COAT = "ρτυχ"
HAT = "kghg"
GUNWOOD = "Ktia"


def blunderbuss(f, grip, ang, layer=None, flash=0, smoke=0):
    """Brass bell-mouthed blunderbuss held at grip, pointing ang (deg). Returns the muzzle point."""
    c = layer if layer is not None else f.b
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    stock = [(grip[0] - ux * 3.5 + nx * 1.2, grip[1] - uy * 3.5 + ny * 1.2), (grip[0], grip[1])]
    tube(c, stock, [1.3, 1.0], "Ktia", bias=0.1)
    m0 = (grip[0] + ux * 1.0, grip[1] + uy * 1.0)
    m1 = (grip[0] + ux * 9.5, grip[1] + uy * 9.5)
    tube(c, [m0, m1], [0.8, 0.95], BRONZE, bias=0.2)
    # flared bell mouth
    mz = (grip[0] + ux * 11.0, grip[1] + uy * 11.0)
    for k in range(-2, 3):
        c.put(*P(mz[0] + nx * k * 0.9, mz[1] + ny * k * 0.9), "w" if k < 0 else "e" if k == 0 else "A")
    c.put(*P(mz[0] - ux * 0.8 + nx * 1.6, mz[1] - uy * 0.8 + ny * 1.6), "J")
    c.put(*P(mz[0] - ux * 0.8 - nx * 1.6, mz[1] - uy * 0.8 - ny * 1.6), "w")
    c.put(*P(grip[0] + ux * 4 - nx * 0.9, grip[1] + uy * 4 - ny * 0.9), "X")        # brass glint
    tip = (mz[0] + ux * 1.0, mz[1] + uy * 1.0)
    if flash:
        for k in range(10):
            aa = a + math.radians((k - 4.5) * 14)
            r = 2.0 + (3.5 if k % 2 else 5.5) * (1.0 if flash >= 2 else 0.6)
            line(f.g, tip[0], tip[1], tip[0] + r * math.cos(aa), tip[1] + r * math.sin(aa), "cQ" if k % 2 else "QE")
        f.g.put(*P(*tip), "c")
    if smoke:
        for k in range(5 + smoke * 2):
            aa = a + math.radians(-60 + k * 30)
            r = 2.5 + smoke * 1.5 + (k % 3)
            f.g.put(*P(tip[0] - ux * 2 + r * math.cos(aa) * 0.8, tip[1] - 1 - smoke + r * math.sin(aa) * 0.6),
                    "f" if k % 3 == 0 else "x", over=False)
    return tip


def captain(dx=0.0, dy=0.0, lean=0.0, knee=0.0, feet=((-4, 0), (3, 0)), hook=(9, -12), gun=((-2, -10), 100), eye="open",
            mouth=0, flap=0.0, hat_tilt=0.0, beard=0.0, extra=None, flash=0, smoke=0, head=(0.0, 0.0), gun_front=False,
            hook_smear=None):
    """hook: front (near) hand position = the iron gaff hook; gun: (grip, angle) of the blunderbuss in the back hand."""
    f = Fr()
    hip = (dx - 0.5, -11.0 + dy + knee)
    lr = math.radians(lean)
    def T(x, y):   # torso-local (x right, y up from hip), leaning forward by `lean`
        return (hip[0] + x * math.cos(lr) + y * math.sin(lr), hip[1] + x * math.sin(lr) - y * math.cos(lr))
    chest = T(0.5, 7.0)
    neck = T(1.5, 12.5)
    hd = (neck[0] + 1.2 + head[0], neck[1] - 3.0 + head[1])
    # legs: dark breeches into heavy sea boots, back leg in shadow
    for i, (fx, fy) in enumerate(feet):
        hp = (hip[0] + (-1.8 if i == 0 else 1.8), hip[1])
        foot = (dx + fx, fy - 2.2)
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], foot[0], foot[1], 5.0, 4.6, bend=-1)
        lay = f.u if i == 0 else f.b
        tube(lay, [hp, (kx, ky), (ax, ay)], [2.0, 1.7, 1.8], "ZZkt" if i == 0 else "Zktg")
        bx, by = P(ax, ay)
        for yy in range(by - 1, min(0, by + 2) + 1):
            for xx in range(bx - 2, bx + 3 + (1 if yy >= by + 1 else 0)):
                lay.put(xx, yy, ("K" if i == 0 else "k") if yy > by - 1 else ("k" if i == 0 else "g"))
        lay.put(bx + 3, min(0, by + 2), "K")
    # back arm + the blunderbuss (behind the coat unless brought round in front)
    (gx, gy), gang = gun
    grip = (dx + gx, gy + dy)
    shb = T(-1.8, 11.0)
    (ebx, eby), (hbx, hby) = ik(shb[0], shb[1], grip[0], grip[1], 5.2, 5.0, bend=1)
    def draw_gun(glay):
        m = blunderbuss(f, grip, gang, layer=glay, flash=flash, smoke=smoke)
        tube(glay, [shb, (ebx, eby), (hbx, hby)], [1.7, 1.5, 1.3], COAT if gun_front else "ρρτ")
        ell(glay, hbx, hby, 1.3, 1.2, "zxM")
        return m
    muzzle = None if gun_front else draw_gun(f.u)
    # coat tails flaring behind
    tail = [T(-3.5, 6.0), T(-6.0 - flap, 0.5), T(-8.5 - flap * 1.6, -5.5 + flap * 0.8), T(-3.0, -6.0), T(0.0, -4.0)]
    poly(f.u, tail, "τ", shade=lambda x, y: "ρ" if (x * 2 + y) % 5 == 0 else "τ")
    # coat body: from the shoulders, belted at the waist, flared skirt to the knees
    body = [T(-4.2, 12.0), T(4.0, 12.0), T(5.2, 7.0), T(4.4, 2.5), T(6.2, -4.5), T(1.0, -5.5), T(-4.5, -5.0), T(-5.6, 2.0),
            T(-5.4, 8.0)]
    cx_ = chest[0]
    poly(f.b, body, "υ", shade=lambda x, y: pick(COAT, 0.75 - (x - cx_ + 3) * 0.16 - (y - chest[1]) * 0.02))
    ell(f.b, chest[0] + 0.5, chest[1] + 0.5, 4.6, 5.0, COAT, ang=lean, bias=0.1)   # bloated chest under the coat
    # lapel, buttons, sash, barnacles
    line(f.b, *T(2.0, 11.5), *T(3.6, 5.0), "χ")
    for k in range(4):
        f.b.put(*P(*T(3.0, 10.0 - k * 2.2)), "e" if k % 2 == 0 else "w")
        f.b.put(*P(*T(0.6, 9.4 - k * 2.2)), "J")
    for k in range(-5, 6):
        f.b.put(*P(*T(k * 1.0, 2.6)), "P" if k < 2 else "p")
        f.b.put(*P(*T(k * 1.0, 1.8)), "p" if k < 3 else "r")
    tube(f.b, [T(4.0, 2.0), T(4.6, -1.0), T(4.0, -3.5)], [0.8, 0.7, 0.6], "pPr", bias=0.2)   # sash knot end
    barnacles(f.b, [T(-3.5, 9.5), T(-4.0, -2.0)], seed=91)
    kelp(f.b, int(round(T(-5.0, 1.0)[0])), int(round(T(-5.0, 1.0)[1])), 5, 0.7, seed=3)
    # v0.9 lineage (Bell Diver parent): an anchor chain slung across the coat, a brass diving collar at the neck
    chain_line(f.b, sag(T(-4.0, 11.0), T(4.4, 1.5), 9, 0.8), cols="Hf")
    # ... and the Diver's brass helmet, urchin and all, hangs from his belt at the back hip
    hh = T(-4.6, 1.0)
    ell(f.b, hh[0], hh[1], 2.8, 2.6, BRONZE, bias=0.25)
    ell(f.b, hh[0] + 1.0, hh[1] + 0.2, 1.1, 1.2, "ZDd")
    f.b.put(*P(hh[0] - 1.2, hh[1] - 2.6), "N"); f.b.put(*P(hh[0] - 2.2, hh[1] - 2.2), "n"); f.b.put(*P(hh[0] - 1.8, hh[1] - 3.4), "H")
    for k in range(-3, 4):
        f.b.put(*P(*T(k * 1.0 + 1.0, 12.4)), "e" if k < 0 else ("w" if k == 0 else "A"))
        f.b.put(*P(*T(k * 1.0 + 1.0, 11.6)), "J")
    # epaulette
    sh_f = T(2.5, 11.4)
    for k in range(3): f.b.put(*P(sh_f[0] - 1 + k, sh_f[1] - 0.6), "e" if k else "A")
    for k in range(3): f.b.put(*P(sh_f[0] - 1.5 + k * 1.2, sh_f[1] + 0.6), "J")
    # head: bloated, grey-green, sunk on the collar; kelp beard; one glowing eye, the other a dark hole
    ell(f.b, hd[0], hd[1], 3.4, 3.3, FLESH, bias=0.15)
    f.b.put(*P(hd[0] + 3.2, hd[1] + 0.2), "M")                                       # nose
    ex_, ey_ = P(hd[0] + 1.6, hd[1] - 0.6)
    if eye == "open": f.g.put(ex_, ey_, "c"); f.g.put(ex_ + 1, ey_, "B"); f.g.put(ex_, ey_ - 1, "Z")
    elif eye == "wide": f.g.put(ex_, ey_, "c"); f.g.put(ex_ + 1, ey_, "c"); f.g.put(ex_, ey_ - 1, "Q")
    elif eye == "squint": f.g.put(ex_, ey_, "E"); f.g.put(ex_ + 1, ey_, "Z")
    else: f.g.put(ex_, ey_, "x")
    f.b.put(*P(hd[0] - 0.4, hd[1] - 0.4), "Z")                                       # the empty socket
    mx_, my_ = P(hd[0] + 2.0, hd[1] + 1.6)
    for j in range(mouth + 1):
        f.b.put(mx_, my_ + j, "Z"); f.b.put(mx_ + 1, my_ + j, "j" if j else "Z")
    for k in range(6):   # kelp beard over the collar
        bx0 = hd[0] - 1.0 + k * 0.9
        n = 4 + (k % 3) + (2 if k in (2, 3) else 0)
        for j in range(n):
            f.b.put(*P(bx0 + beard * math.sin(j * 0.6 + k) * 0.6 + j * 0.15, hd[1] + 2.2 + j), "Lvl"[(j + k) % 3] if j < n - 1 else "L")
    # tricorn: a dark three-cornered hat, brass-trimmed brim, barnacles and a trailing weed
    ht = math.radians(hat_tilt)
    def H(x, y):
        return (hd[0] + x * math.cos(ht) - y * math.sin(ht), hd[1] - 2.6 + x * math.sin(ht) + y * math.cos(ht))
    crown_ = [H(-3.2, 0), H(-2.4, -3.4), H(0.0, -4.4), H(2.6, -3.4), H(3.4, 0)]
    poly(f.b, crown_, "k", shade=lambda x, y: pick(HAT, 0.6 - (x - hd[0]) * 0.18))
    brim = [H(-5.8, -1.4), H(-3.5, 0.6), H(0.0, 1.0), H(3.8, 0.6), H(6.0, -1.8), H(4.0, -0.4), H(0.0, -0.2), H(-3.5, -0.6)]
    poly(f.b, brim, "K")
    polyline(f.b, [H(-5.8, -1.4), H(-3.5, 0.6), H(0.0, 1.0), H(3.8, 0.6), H(6.0, -1.8)], "e")
    f.b.put(*P(*H(6.0, -1.8)), "w"); f.b.put(*P(*H(-5.8, -1.4)), "A")
    barnacles(f.b, [H(-1.5, -2.5), H(1.4, -3.0)], seed=95)
    # v0.10: the Salt Siren's lure on the brim is gone (his one parent is the Bell Diver); a short chain hangs there
    lp = [H(5.6, -1.2), H(6.6, 0.6), H(6.8, 2.2)]
    line(f.b, lp[0][0], lp[0][1], lp[1][0], lp[1][1], "zx"); line(f.b, lp[1][0], lp[1][1], lp[2][0], lp[2][1], "xz")
    kelp(f.b, int(round(H(-5.5, -1.0)[0])), int(round(H(-5.5, -1.0)[1])), 4, 0.6, seed=5)
    if gun_front: muzzle = draw_gun(f.b)   # brought round in front of the coat to aim
    # front arm ending in the gaff hook
    shf = T(2.6, 11.0)
    hand = (dx + hook[0], hook[1] + dy)
    (efx, efy), (hfx, hfy) = ik(shf[0], shf[1], hand[0], hand[1], 5.4, 5.2, bend=1)
    tube(f.b, [shf, (efx, efy), (hfx, hfy)], [1.9, 1.7, 1.5], COAT, bias=0.1)
    for k in range(-1, 2):   # turned-back cuff
        f.b.put(*P(hfx + k * 0.6, hfy + k * 0.6), "χ")
    ha = math.degrees(math.atan2(hfy - efy, hfx - efx))
    hk = [(hfx, hfy)]
    a0 = math.radians(ha)
    pt = (hfx + math.cos(a0) * 3.2, hfy + math.sin(a0) * 3.2)
    hk.append(pt)
    for k in range(4):   # the curl of the gaff, turning back toward him
        a0 += math.radians(-62)
        pt = (pt[0] + math.cos(a0) * 1.6, pt[1] + math.sin(a0) * 1.6)
        hk.append(pt)
    tube(f.b, hk[:2], [0.9, 0.8], IRON, bias=0.2)
    polyline(f.b, hk[1:], "f")
    f.b.put(*P(*hk[-1]), "H"); f.b.put(*P(*hk[1]), "x")
    gaff = hk[2]
    if hook_smear:
        for (x, y, ch) in hook_smear: f.n.put(x, y, ch, over=False)
    if extra: extra(f, gaff, muzzle)
    return f.done()


def captain_corpse():
    f = Fr()
    # face-down in a spreading coat, hat rolled off, blunderbuss dropped, hook arm flung out
    poly(f.b, [(-12, 0), (-10, -4), (-3, -5.5), (4, -4.5), (6, 0)], "τ", shade=lambda x, y: pick(COAT, 0.5 - (x + 4) * 0.08 - (y + 3) * 0.1))
    for k in range(-10, 5, 3): f.b.put(k, -1, "ρ")
    for k in range(-2, 3): f.b.put(k - 4, -3, "p")
    ell(f.b, 7.5, -2.6, 3.0, 2.6, FLESH, bias=0.1)
    f.g.put(9, -3, "x")
    for k in range(4):
        for j in range(3): f.b.put(6 + k, -1 + 0 * j, "Lvl"[(j + k) % 3])
    tube(f.b, [(2, -4), (6, -6.5), (10, -7)], [1.6, 1.4, 1.2], COAT)
    polyline(f.b, [(10, -7), (12.5, -7), (13.5, -8.5), (12.5, -9.5)], "f")
    f2 = Fr(); blunderbuss(f2, (-14, -1.5), 175)
    for k, v in f2.b.px.items(): f.u.raw.put(k[0], k[1], v)
    poly(f.b, [(13, 0), (15, -3), (19, -3.5), (21, -1), (18, 0)], "K")
    polyline(f.b, [(13, 0), (16, -1), (21, -1)], "e")
    return f.done()


def build_captain(outdir):
    Cp = captain
    idle = []
    for i in range(4):
        b = [0, 0.4, 0.6, 0.3][i]
        idle.append(Cp(dy=b, hook=(8.5, -12 + b * 0.5), gun=((-4.5, -10.5 + b * 0.5), 128 - b * 4), beard=b, flap=b * 0.5,
                       eye="open" if i != 3 else "squint", mouth=1 if i == 2 else 0, hat_tilt=-b * 3))
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        fa, fb = 4.5 * math.sin(ph), -4.5 * math.sin(ph)
        la, lb = max(0, 1.5 * math.cos(ph)), max(0, -1.5 * math.cos(ph))
        bob = -abs(math.cos(ph)) * 0.8 + 0.4
        run.append(Cp(dy=bob, lean=8, feet=((fa - 1, -la), (fb + 1, -lb)), hook=(9 + fb * 0.4, -13 + bob), flap=1.0 + 0.6 * math.sin(ph),
                      gun=((-4.5 + fa * 0.3, -11 + bob), 135), beard=math.sin(ph), hat_tilt=4))
    # GAFF: hook drawn back over the shoulder, sweep, HIT at full reach, haul back toward himself
    def sweep(cx_, cy_, r, a0, a1):
        pts = []
        for k in range(14):
            a = math.radians(a0 + (a1 - a0) * k / 13)
            for rr in (r, r - 1):
                pts.append((*P(cx_ + rr * math.cos(a), cy_ + rr * math.sin(a)), "Q" if rr == r else "E"))
        return pts
    def haul(n):
        def fn(f, gaff, muzzle):
            for k in range(n):
                f.g.put(*P(gaff[0] + 3 + k * 2, gaff[1] - 1 + (k % 2)), "E" if k else "Q")
        return fn
    gaffm = [Cp(lean=-6, hook=(-2, -22), gun=((-4.5, -10), 128), eye="wide", flap=0.4),
             Cp(lean=-12, knee=0.5, feet=((-5, 0), (4, 0)), hook=(-6, -25), gun=((-5, -10), 135), eye="wide", mouth=1, flap=0.8,
                hat_tilt=-4),
             Cp(lean=8, knee=0.8, feet=((-5, 0), (5, 0)), hook=(13, -21), gun=((-4.5, -10), 130), eye="wide", mouth=2, flap=-0.4,
                hook_smear=sweep(1, -14, 12, -150, -30)),
             Cp(lean=16, knee=1.2, feet=((-5, 0), (6, 0)), hook=(17, -13), gun=((-4, -10), 128), eye="wide", mouth=2, flap=-0.8,
                hat_tilt=4, extra=haul(3)),
             Cp(lean=-4, knee=1.0, feet=((-5, 0), (5, 0)), hook=(11, -13), gun=((-4.5, -10), 128), eye="squint", mouth=1, flap=0.2,
                extra=haul(2)),
             Cp(lean=-2, knee=0.5, hook=(9, -12.5), gun=((-4.5, -10.5), 128), eye="open", flap=0.3),
             Cp(hook=(8.5, -12), gun=((-4.5, -10.5), 128))]
    # BROADSIDE: swing the blunderbuss up, level it on the hook, fuse sparks, FIRE (muzzle blast), recoil, smoke
    def fuse(f, gaff, muzzle):
        for (a, b, ch) in ((-6, -2, "Y"), (-7, -3, "O"), (-5, -3, "y")):
            f.g.put(*P(muzzle[0] + a, muzzle[1] + b), ch)
    bs = [Cp(lean=-4, hook=(6, -14), gun=((1, -15), 20), gun_front=True, eye="open", flap=0.2),
          Cp(lean=-2, hook=(10, -16.5), gun=((4, -17.5), -4), gun_front=True, eye="wide", mouth=1, flap=0.3),
          Cp(lean=0, hook=(10, -16.5), gun=((4.5, -17.5), 0), gun_front=True, eye="squint", mouth=1, extra=fuse),
          Cp(lean=-10, knee=0.6, feet=((-5, 0), (3, 0)), hook=(8.5, -17.5), gun=((3, -18.5), -6), gun_front=True, eye="wide",
             mouth=2, flash=2, flap=1.2, hat_tilt=-6),
          Cp(lean=-14, knee=0.8, feet=((-5.5, 0), (3, 0)), hook=(7, -18), gun=((1.5, -19.5), -14), gun_front=True, eye="squint",
             mouth=2, flash=1, smoke=1, flap=1.0, hat_tilt=-8),
          Cp(lean=-8, knee=0.4, hook=(8, -16), gun=((2.5, -17.5), -6), gun_front=True, eye="open", mouth=1, smoke=2, flap=0.6),
          Cp(lean=-3, hook=(8, -13), gun=((1, -14), 40), gun_front=True, eye="open", smoke=3),
          Cp(hook=(8.5, -12), gun=((-4.5, -10.5), 128))]
    death = [Cp(lean=-14, knee=0.5, hook=(4, -22), gun=((-6, -14), 150), eye="wide", mouth=2, hat_tilt=-12, flap=1.0),
             Cp(lean=10, knee=4.0, feet=((-5, 0), (3, 0)), hook=(9, -6), gun=((-5, -5), 170), eye="squint", mouth=2, hat_tilt=14,
                head=(0.5, 1.0)),
             grounded(Cp(lean=55, knee=7.0, feet=((-6, 0), (1, 0)), hook=(14, -2), gun=((-8, -2), 180), eye="dead", mouth=1,
                         hat_tilt=40, head=(1, 2))),
             captain_corpse()]
    knock = Cp(lean=-16, knee=0.4, feet=((-5, 0), (2, -1)), hook=(5, -17), gun=((-5, -12), 130), eye="squint", mouth=1,
               hat_tilt=-10, flap=1.0)
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.1] * 6),
             ("Gaff", gaffm, [0.16, 0.14, 0.06, 0.07, 0.16, 0.14, 0.16]),
             ("Broadside", bs, [0.16, 0.16, 0.18, 0.06, 0.12, 0.14, 0.14, 0.16])]
    anims += std_tail(idle[0], death, [0.12, 0.14, 0.18, 0.5], knock)
    sheet("BelCaptain", anims, outdir, scale=4)


# ------------------------------------------------------------------ ABYSS KRAKEN (T3, Hermit + Lamprey lines)
# A squat crimson octopus: a huge barnacled mantle leaning back, two great cyan eyes with goat-slit pupils, a
# skirt of curling arms spread over the floor (pink sucker rows underneath) and two long lashing arms. Low and
# wide where the Captain is tall and narrow.
KRAK = "jpPPa"
KRAK_D = "jppP"


def tentacle(c, pts, r0=2.0, r1=0.4, ramp=KRAK_D, suckers=True, glow_tip=False):
    """A tapered arm along control points (smoothed); pink suckers along its underside. Returns the dense points."""
    sp, _ = catmull(pts, [1.0] * len(pts), step=0.7)
    n = len(sp)
    rad = [r0 + (r1 - r0) * (i / max(1, n - 1)) ** 0.8 for i in range(n)]
    tube(c, sp, rad, ramp, bias=0.1)
    if suckers:
        for i in range(2, n - 2, 2):
            (x0, y0), (x1, y1) = sp[i - 1], sp[i + 1]
            tl = math.hypot(x1 - x0, y1 - y0) or 1
            nx_, ny_ = -(y1 - y0) / tl, (x1 - x0) / tl
            if ny_ < 0: nx_, ny_ = -nx_, -ny_                # the underside (toward the floor)
            r = rad[i]
            if r < 0.7: continue
            if i % 4 == 2: c.put(*P(sp[i][0] + nx_ * r * 0.7, sp[i][1] + ny_ * r * 0.7), "F")
    if glow_tip: c.put(*P(*sp[-1]), "a")
    return sp


def kraken(dx=0.0, dy=0.0, breathe=0.0, lean=0.0, phase=0.0, eye="open", glow=1, lash=None, plunge=None, ripples=(),
           floor_spread=1.0, extra=None, sink=0.0, siphon=0.0):
    """lash: two (mid, tip) control pairs for the raised arms, or None (resting curled in front).
    plunge: list of floor x where arm tips go into the floor (ripples drawn there)."""
    f = Fr()
    base = (dx - 1.0, -7.0 + dy + sink)
    # --- the floor skirt: arms spread back and forward over the floor, tips curling up
    specs = [(-1, 0.0, 15.0, 0.9), (-1, 1.3, 11.0, 0.7), (1, 0.6, 12.5, 0.85), (1, 2.0, 9.0, 0.6)]
    for k, (sd, ph0, L, cu) in enumerate(specs):
        L *= floor_spread
        x0 = base[0] + sd * 2.0
        pts = [(x0, base[1] + 2.0), (x0 + sd * L * 0.35, -1.6), (x0 + sd * L * 0.7, -1.4 - 0.6 * math.sin(phase + ph0))]
        tipx = x0 + sd * L
        curl_ = cu * (3.0 + 1.2 * math.sin(phase * 1.3 + ph0 * 2))
        pts += [(tipx, -1.8 - curl_ * 0.6), (tipx - sd * curl_ * 0.5, -2.5 - curl_)]
        layer = f.u if k in (1, 3) else f.b
        tentacle(layer, pts, r0=2.4 if k in (0, 2) else 1.9, r1=0.45, ramp=KRAK_D if layer is f.b else "Zjjp")
    # --- mantle: a big bulb leaning back, barnacled, pale spots
    mc = (base[0] - 3.0 - lean * 0.08, base[1] - 11.5 - breathe * 0.6)
    def skin(nu, nv, d, l, ch, x, y):
        if (x * 5 + y * 7) % 23 == 0 and d < 0.8: return "j"
        if l > 0.85 and d < 0.35: return "a"
        return ch
    ell(f.b, mc[0], mc[1], 7.6 + breathe * 0.3, 10.2 + breathe * 0.6, KRAK, ang=-25 + lean, bias=0.12, shader=skin)
    barnacles(f.b, [(mc[0] - 3, mc[1] - 5), (mc[0] - 5.5, mc[1] + 0.5), (mc[0] + 0.5, mc[1] - 8)], seed=101)
    for k in range(5):   # darker mottled bands across the mantle
        a = math.radians(-25 + lean)
        y0 = -6 + k * 3.2
        for j in range(-3, 4):
            x, y = mc[0] + j * 1.6 * math.cos(a) - y0 * math.sin(a) * 0.3, mc[1] + y0 + j * 0.5
            if (j + k) % 2 == 0 and (P(x, y) in f.b.px): f.b.put(*P(x, y), "j")
    kelp(f.b, int(round(mc[0] - 6)), int(round(mc[1] + 1)), 6, 0.8, seed=2)
    kelp(f.b, int(round(mc[0] - 4)), int(round(mc[1] + 4)), 4, 0.6, seed=4)
    # v0.9 lineage (Bell Hermit parent): it wears the hermit's barnacled bronze bell on its mantle like a shell
    hermit_bell(f, mc[0] - 1.5, mc[1] - 7.5, 70.0 + lean * 0.5, size=5.0, glint=True, seed=73)
    # --- head below the mantle: the eye ridge, siphon at the side
    hc = (base[0] + 2.2, base[1] - 3.2)
    ell(f.b, hc[0], hc[1], 6.0, 4.4, KRAK, bias=0.05, shader=skin)
    sx, sy = hc[0] - 4.5, hc[1] + 1.5
    tube(f.b, [(sx, sy), (sx - 2.0 - siphon, sy + 1.0), (sx - 3.0 - siphon * 1.5, sy + 0.5)], [1.2, 1.0, 1.1], "jpP")
    # eyes: a great near eye (pale, glowing, goat-slit pupil) under a heavy lid, the far one over the brow
    if True:
        ex, ey = hc[0] + 3.0, hc[1] - 2.2
        ell(f.b, ex - 0.3, ey - 0.8, 3.0, 2.6, "jpP", bias=0.35)            # lid ridge
        f.b.put(*P(hc[0] - 0.8, hc[1] - 3.6), "j")
        ex_, ey_ = P(ex, ey)
        fx_, fy_ = P(hc[0] - 0.6, hc[1] - 3.0)
        if eye == "dead":
            for a in (-1, 0, 1): f.g.put(ex_ + a, ey_, "x")
            f.g.put(fx_, fy_, "z")
        elif eye == "shut":
            for a in (-2, -1, 0, 1, 2): f.g.put(ex_ + a, ey_, "j")
            f.g.put(fx_, fy_, "j")
        else:
            hi = "c" if glow >= 2 else "Q"
            for (a, b_) in ((-1, -1), (0, -1), (1, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1)):
                f.g.put(ex_ + a, ey_ + b_, hi if b_ < 0 else ("B" if b_ == 0 else "E"))
            if eye == "squint":
                for a in (-1, 0, 1): f.g.put(ex_ + a, ey_ - 1, "j")
            for a in (-1, 0, 1): f.g.put(ex_ + a, ey_, "Z")                          # goat slit
            if eye == "wide": f.g.put(ex_ + 2, ey_ - 1, "c"); f.g.put(ex_ - 2, ey_ - 1, "Q")
            if glow >= 2:
                for (a, b_) in ((-3, 0), (3, 0), (0, -2), (-2, -2), (2, -2)): f.g.put(ex_ + a, ey_ + b_, "E", over=False)
            f.g.put(fx_, fy_, hi); f.g.put(fx_ + 1, fy_, "Z")
    # v0.10 (one parent, the Bell Hermit): the lamprey sucker is gone; a hooked black beak with a pale edge
    if eye != "dead":
        mx_, my_ = hc[0] + 4.6, hc[1] + 2.6
        poly(f.b, [(mx_ - 1.2, my_ - 1.6), (mx_ + 1.6, my_ - 1.0), (mx_ + 2.2, my_ + 0.6), (mx_ + 0.8, my_ + 1.8),
                   (mx_ - 1.0, my_ + 1.2)], "k")
        line(f.b, mx_ + 1.6, my_ - 1.0, mx_ + 2.2, my_ + 0.6, "f"); f.b.put(*P(mx_ + 1.4, my_ + 1.4), "H")
        f.b.put(*P(mx_ - 0.4, my_ + 0.2), "Z")
    # --- lashing arms (near side, over everything)
    tips = []
    if lash is None:
        lash = (((base[0] + 8.0, -6.0 - 1.0 * math.sin(phase)), (base[0] + 9.5, -1.5)),
                ((base[0] + 5.5, -4.0), (base[0] + 12.5 + 0.8 * math.cos(phase), -2.5 - 1.5 * math.sin(phase + 1))))
    for k, (mid, tip) in enumerate(lash):
        root = (base[0] + 3.0 + k * 1.5, base[1] + 0.5)
        sp = tentacle(f.b, [root, mid, tip], r0=2.3 - k * 0.3, r1=0.5, ramp="jpPa")
        tips.append(sp[-1])
    for x in (plunge or ()):
        for k in range(-3, 4):
            f.g.put(*P(x + k, 0), "E" if abs(k) == 3 else "d", over=False)
        f.g.put(*P(x - 2, -1), "Q", over=False); f.g.put(*P(x + 2, -1), "Q", over=False)
    for (x, r) in ripples:
        for k in range(-int(r), int(r) + 1):
            if abs(k) >= r - 1: f.g.put(*P(x + k, 0), "Q" if abs(k) == int(r) else "E", over=False)
            elif (k + int(r)) % 3 == 0: f.g.put(*P(x + k, 0), "d", over=False)
    if extra: extra(f, tips, mc)
    return f.done()


def kraken_corpse():
    f = Fr()
    # collapsed: the mantle slumped forward flat on the floor, arms splayed limp, eyes gone dark
    for k, (sd, L) in enumerate(((-1, 16), (-1, 11), (1, 15), (1, 10))):
        pts = [(sd * 2.0, -1.5), (sd * L * 0.5, -1.0 - (k % 2) * 0.5), (sd * L, -0.8)]
        tentacle(f.u if k % 2 else f.b, pts, r0=2.0, r1=0.4)
    ell(f.b, -3.0, -4.0, 11.0, 4.6, KRAK, bias=0.05)
    barnacles(f.b, [(-8, -6), (-3, -7.5), (2, -6)], seed=103, big=True)
    ell(f.b, 8.0, -3.0, 4.5, 3.0, KRAK, bias=0.1)
    f.g.put(10, -4, "x"); f.g.put(11, -4, "z"); f.g.put(9, -4, "x")
    for k in range(4): kelp(f.b, -10 + k * 4, -7 + (k % 2), 3, 0.6, seed=k)
    return f.done()


def build_kraken(outdir):
    K = kraken
    idle = [K(breathe=[0, 0.5, 1.0, 0.5][i], phase=i * math.pi / 2, eye="open" if i != 3 else "squint", glow=1 + (i == 2),
              siphon=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(K(dx=0.6 * math.sin(ph), dy=-0.8 * abs(math.sin(ph)), breathe=0.4 * math.cos(ph), lean=-4 * math.sin(ph),
                     phase=ph * 2, floor_spread=1.0 + 0.12 * math.sin(ph), siphon=0.8 * (1 + math.sin(ph))))
    # SLAM: two arms coil up over the mantle, come down in a blur, SLAM the floor ahead, drag back
    def smear(f, tips, mc):
        for k in range(14):
            a = math.radians(-120 + k * 9)
            for rr in (19, 18):
                f.n.put(*P(4 + rr * math.cos(a), -2 + rr * math.sin(a)), "Q" if rr == 19 else "E", over=False)
    def splash(n):
        def fn(f, tips, mc):
            for t in tips[:1]:
                for k in range(n):
                    f.g.put(*P(t[0] - 4 + k * 1.6, -1 - (k % 2) - (1 if 1 < k < n - 2 else 0)), "Q" if k % 2 else "E", over=False)
                for k in range(-7, 8):
                    f.g.put(*P(t[0] - 2 + k, 0), "d", over=False)
        return fn
    slam = [K(lean=-6, breathe=0.6, eye="wide", lash=(((9, -14), (8, -21)), ((11, -12), (12, -18)))),
            K(lean=-10, breathe=1.0, eye="wide", glow=2, lash=(((10, -22), (6, -31)), ((12, -19), (10, -28)))),
            K(lean=6, breathe=0.2, eye="wide", glow=2, lash=(((12, -20), (20, -16)), ((10, -18), (18, -12))), extra=smear),
            K(lean=10, breathe=-0.4, eye="squint", glow=2, lash=(((12, -8), (22, -1)), ((9, -6), (19, -1))), extra=splash(8)),
            K(lean=8, breathe=-0.3, eye="squint", lash=(((12, -7), (21, -1)), ((9, -5), (18, -1))), extra=splash(5)),
            K(lean=2, breathe=0.2, eye="open", lash=(((10, -9), (15, -2)), ((7, -6), (14, -2)))),
            K(breathe=0.4, eye="open")]
    # ERUPT: rears, raises both arms, drives them into the floor ahead, holds (the deep answers), pulls free
    erupt = [K(lean=-8, breathe=1.0, eye="wide", lash=(((9, -14), (9, -20)), ((11, -12), (13, -17)))),
             K(lean=-12, breathe=1.4, eye="wide", glow=2, lash=(((10, -22), (12, -30)), ((12, -19), (15, -26)))),
             K(lean=8, breathe=0.0, eye="wide", glow=2, lash=(((11, -12), (15, 3)), ((9, -10), (11, 3))), plunge=(15, 11)),
             K(lean=6, breathe=0.6, eye="wide", glow=2, lash=(((11, -11), (15, 3)), ((9, -9), (11, 3))), plunge=(15, 11),
               ripples=((15, 5),)),
             K(lean=6, breathe=1.0, eye="open", glow=2, lash=(((11, -12), (15, 3)), ((9, -10), (11, 3))), plunge=(15, 11),
               ripples=((15, 7),), siphon=1),
             K(lean=6, breathe=0.6, eye="wide", glow=2, lash=(((11, -11), (15, 3)), ((9, -9), (11, 3))), plunge=(15, 11),
               ripples=((15, 9),)),
             K(lean=6, breathe=0.2, eye="open", glow=1, lash=(((11, -12), (15, 3)), ((9, -10), (11, 3))), plunge=(15, 11)),
             K(lean=0, breathe=0.4, eye="open", lash=(((10, -12), (14, -6)), ((8, -10), (12, -5))))]
    death = [K(lean=-12, breathe=1.4, eye="wide", glow=2, lash=(((9, -16), (6, -23)), ((11, -14), (10, -21)))),
             K(lean=10, breathe=-0.8, sink=2.0, eye="shut", glow=0, floor_spread=1.15, lash=(((10, -4), (16, -1)), ((7, -3), (13, -1)))),
             grounded(K(lean=24, breathe=-1.4, sink=4.0, eye="dead", glow=0, floor_spread=1.25,
                        lash=(((10, -2), (17, 0)), ((7, -2), (14, 0))))),
             kraken_corpse()]
    knock = K(lean=-14, breathe=1.0, eye="squint", lash=(((8, -12), (5, -17)), ((10, -10), (9, -15))))
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.1] * 6),
             ("Slam", slam, [0.16, 0.16, 0.06, 0.07, 0.16, 0.14, 0.16]),
             ("Erupt", erupt, [0.16, 0.16, 0.08, 0.2, 0.2, 0.2, 0.2, 0.18])]
    anims += std_tail(idle[0], death, [0.12, 0.14, 0.18, 0.5], knock)
    sheet("BelKraken", anims, outdir, scale=4)


# ------------------------------------------------------------------ FX for the four new monsters
def fx_peal():
    """FxPeal: the Bell Hermit's shell rings when struck - a small ground ring (r = 4, 8, 12, 15 px) + sound arcs."""
    out = []
    for i, r in enumerate((4, 8, 12, 15)):
        c = cv()
        ry = r * 0.36 + 0.8
        n = int(r * 6)
        for k in range(n):
            a = 2 * math.pi * k / n
            if i >= 2 and (k // 3) % 3 == 0: continue
            x, y = r * math.cos(a), ry * math.sin(a)
            c.put(*P(x, y), "Q" if i < 2 else "E" if i < 3 else "d")
            c.put(*P(x * 0.88, y * 0.8), "E" if i < 2 else "d", over=False)
        for sd in (-1, 1):
            for k in range(-1, 2):
                c.put(*P(sd * (r * 0.45 + 1), -ry - 2 - i * 1.5 + abs(k) * 0.6 + k * 0.2), "Q" if i < 2 else "E", over=False)
        if i == 0: ell(c, 0, 0, 2.5, 1.2, "EQ", bias=0.4)
        out.append(c.spr())
    return out


def fx_cannonball():
    """FxCannonball: the Captain's shot - a barnacled iron ball in a cyan water wake (Fly loop, faces right)."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(6):   # wake trailing left
            x = -4 - k * 1.7 - (i % 2) * 0.8
            y = -4 + math.sin(k * 1.1 + i * 1.5) * 1.3
            c.put(*P(x, y), "Q" if k < 1 else "E" if k < 3 else "d" if k < 5 else "D")
        line(c, -3, -2, -8 - (i % 2), -1.5, "D")
        line(c, -3, -6, -7 - ((i + 1) % 2), -6.5, "D")
        ell(c, 0, -4, 2.6, 2.6, "Zzxf", bias=0.25)
        c.put(*P(-1, -5), "H"); c.put(*P(*[(1, -3), (0, -2), (-1, -3), (0, -5)][i]), "f")
        c.put(*P(1, -4 + (i % 2)), "a")
        out.append(Spr(outl(c.spr()).px))
    return out


def fx_cannon_blast():
    """FxCannonBlast: the shot bursts in a spout of brine: crown + a ground ring (hit radius 6, 12, 17, 19, 20 px)."""
    out = []
    for i, r in enumerate((6, 12, 17, 19, 20, 20)):
        c = cv()
        ry = r * 0.36 + 1
        n = int(r * 5)
        for k in range(n):
            a = 2 * math.pi * k / n
            if i >= 3 and (k // 2) % 3 == 0: continue
            if i >= 5 and k % 2: continue
            x, y = r * math.cos(a), ry * math.sin(a)
            c.put(*P(x, y), "Q" if i < 2 else "E" if i < 4 else "d")
            c.put(*P(x * 0.85, y * 0.8), "d" if i < 3 else "D", over=False)
        h = [8, 16, 18, 12, 5, 0][i]
        if h:
            for sd in (-1, 1):
                for k in range(3):
                    x0 = sd * (1.5 + k * 2.0) * (0.6 + 0.15 * i)
                    hh = h * (1 - 0.22 * k)
                    lean = sd * (1.0 + i * 1.4 + k * 0.9)
                    line(c, x0, 0, x0 + lean, -hh, "dEQ" if k else "EQc")
                    c.put(*P(x0 + lean, -hh - 1), "Q")
            line(c, 0, 0, 0, -h * 0.8, "EQ")
        rnd = random.Random(7)
        for k in range(12):
            a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
            t = (i + 0.6) / 5.0
            x = math.cos(a) * r * 1.1
            y = math.sin(a) * 16 * t * (1.3 - t) + t * t * 2
            if i >= 1 and y <= 0: c.put(*P(x, y), "Q" if k % 3 == 0 else "E")
        if i == 0:
            ell(c, 0, -3, 3.0, 3.0, "EQcc", bias=0.5)
        out.append(c.spr())
    return out


def fx_tentacle():
    """FxTentacle: a kraken arm bursting out of the floor under the hero: ripples (telegraph), the tip breaks the
    surface, rears up ~20 px and lashes, then sinks back. Ground origin = the hole."""
    out = []
    poses = [None, None,
             [(0, 2), (0.5, -2), (1, -5)],
             [(0, 2), (-1, -6), (0.5, -13), (3, -18), (5, -19)],
             [(0, 2), (-1.5, -7), (1, -14), (6, -17), (8, -14)],
             [(0, 2), (-0.5, -7), (4, -12), (9, -11), (11, -7)],
             [(0, 2), (0, -6), (2, -10), (4, -10)],
             [(0, 2), (0.5, -3), (1.5, -4)],
             None]
    ripr = [4, 7, 8, 9, 9, 9, 8, 7, 6]
    for i, pts in enumerate(poses):
        f = Fr()
        r = ripr[i]
        # dark water disc where it comes up + ripple rings
        ry = max(1.0, r * 0.3)
        for y in range(-2, 3):
            for x in range(-r - 1, r + 2):
                d = (x / r) ** 2 + (y / ry) ** 2
                if d > 1.0: continue
                edge = d > 0.6
                f.n.put(x, y, ("E" if y < 0 else "d") if edge else ("Z" if d < 0.25 and 0 < i < 8 else "D"))
        for k in (-r, r): f.g.put(k, 0, "Q" if i < 3 else "E")
        if i <= 1:
            for k in range(3 + i * 2):
                f.g.put(*P(-3 + k * 1.5, -2 - (k + i) % 3), "Q" if k % 2 else "E")
        if pts is not None:
            tentacle(f.b, pts, r0=2.4, r1=0.5, ramp="jpPa")
            if i in (3, 4):
                for k in range(-3, 4):
                    f.g.put(*P(k * 1.6, -1 - (abs(k) % 2) - (2 if abs(k) == 1 else 0)), "Q" if k % 2 else "E", over=False)
        out.append(f.done(clip=False))
    return out


def build_fx_new(outdir):
    fx_sheet("FxPeal", [("Play", fx_peal(), [0.05, 0.06, 0.07, 0.09])], outdir, scale=6)
    fx_sheet("FxCannonball", [("Fly", fx_cannonball(), [0.06] * 4)], outdir, scale=8)
    fx_sheet("FxCannonBlast", [("Play", fx_cannon_blast(), [0.05, 0.06, 0.07, 0.08, 0.1, 0.1])], outdir, scale=6)
    fx_sheet("FxTentacle", [("Rise", fx_tentacle(), [0.2, 0.2, 0.05, 0.08, 0.1, 0.1, 0.1, 0.1, 0.12])], outdir, scale=6)


# ================================================================== TIMING.md + contact sheet
MONSTERS = ["BelUrchin", "BelLurefish", "BelCrab", "BelDiver", "BelSiren", "BelDrownedBell", "BelMatriarch",
            "BelHermit", "BelLamprey", "BelCaptain", "BelKraken"]
FXN = ["FxSpine", "FxWaterBolt", "FxHook", "FxBrine", "FxWave", "FxBellRing", "FxSongNote", "FxSplash", "FxWhirlpool",
       "FxCoralShard", "FxPeal", "FxCannonball", "FxCannonBlast", "FxTentacle"]
FX_NEW = ["FxPeal", "FxCannonball", "FxCannonBlast", "FxTentacle"]
ICONS = ["IconTidecaller", "IconBrineFlask", "IconBellToll", "IconUndertow", "DeityBelMora"]

# (anim, event, frame index, spawn point relative to the feet or "-")
EVENTS = {
    "BelUrchin": [("Roll", "roll starts: begin forward motion + contact damage", 2, "-"),
                  ("Roll", "roll ends: stop motion, damage off", 6, "-"),
                  ("Bristle", "RELEASE: fire FxSpine ring (12 spines, skip straight down)", 3, "(0, -8)")],
    "BelLurefish": [("Chomp", "lunge (jaws wide)", 2, "-"),
                    ("Chomp", "HIT: jaw snap", 3, "(15, -9)"),
                    ("Lure", "channel starts: drag the hero toward the lure", 1, "lure bulb ~ (10, -19)"),
                    ("Lure", "channel ends (last glowing frame)", 5, "-"),
                    ("Lure", "HIT: jaw snap", 6, "(14, -9)")],
    "BelCrab": [("Pinch", "HIT: claw snap", 3, "(19, -7)"),
                ("Shell", "shell closed: invulnerable / damage reduction on", 1, "-"),
                ("Shell", "rises: shell open again", 5, "-")],
    "BelDiver": [("Anchor", "swing (smear)", 3, "-"),
                 ("Anchor", "HIT: anchor slams the floor", 4, "(17, 0)"),
                 ("Hook", "RELEASE: spawn FxHook", 2, "(18, -18)"),
                 ("Hook", "chain taut (hold here while the hook flies)", 3, "-"),
                 ("Hook", "haul starts: pull the hooked hero in", 4, "-"),
                 ("Hook", "brace: pull ends", 7, "-")],
    "BelSiren": [("Bolt", "RELEASE: spawn FxWaterBolt", 3, "(12, -15)"),
                 ("Song", "song starts (loop frames 1-6 while channelling; spawn FxSongNote at the mouth)", 1, "(5, -22)"),
                 ("Song", "song ends", 7, "-")],
    "BelDrownedBell": [("Toll", "swing (smear)", 3, "-"),
                       ("Toll", "IMPACT: spawn FxBellRing shockwave", 4, "(19, 0)"),
                       ("Riptide", "water starts pouring", 4, "-"),
                       ("Riptide", "WAVE RELEASE: spawn FxWave", 5, "(26, 0)")],
    "BelMatriarch": [("Whirl", "spin starts (trident whirling overhead)", 1, "-"),
                     ("Whirl", "RELEASE: trident slams the floor, spawn FxWhirlpool", 4, "(24, 0)"),
                     ("Whirl", "whirlpool open (recovery)", 5, "-"),
                     ("Spear", "lunge (smear)", 2, "-"),
                     ("Spear", "HIT: trident at full reach (or RELEASE: spawn FxCoralShard here, flying right)", 3,
                      "tip (36, -23)")],
    # v0.7.2 additions (final size, no design scale)
    "BelHermit": [("Crush", "lunge (claw wide)", 2, "-"),
                  ("Crush", "HIT: crusher claw snaps shut", 3, "claw tip (25, -3)"),
                  ("Shell", "bell slams down over it: guard on (1/3 damage, struck = FxPeal)", 2, "FxPeal at the feet (0, 0)"),
                  ("Shell", "rings (hold frames 3-6)", 3, "-"),
                  ("Shell", "comes out: guard off", 7, "-")],
    "BelLamprey": [("Leech", "lunge (sucker wide)", 2, "-"),
                   ("Leech", "HIT: sucker clamps on (drain frames 3-4)", 3, "sucker (21, -7)"),
                   ("Dive", "head into the floor: invulnerable on, FxSplash", 2, "(9, 0)"),
                   ("Dive", "gone: teleport to the hero (ripples only)", 5, "-"),
                   ("Dive", "bursts up out of the floor: FxSplash, invulnerable off", 6, "(-1, 0)"),
                   ("Dive", "HIT: surfacing bite", 7, "sucker (8, -7)")],
    "BelCaptain": [("Gaff", "sweep (smear)", 2, "-"),
                   ("Gaff", "HIT: gaff hook at full reach (haul back on frame 4)", 3, "hook (18, -14)"),
                   ("Broadside", "fuse lit", 2, "-"),
                   ("Broadside", "FIRE: spawn FxCannonball at the muzzle, flying right", 3, "muzzle (15, -20)")],
    "BelKraken": [("Slam", "arms come down (smear)", 2, "-"),
                  ("Slam", "HIT: both arms slam the floor ahead", 3, "arm tips (19..29, 0), arms lie along x 6..28"),
                  ("Erupt", "arms plunge into the floor", 2, "(11..15, 0)"),
                  ("Erupt", "THE DEEP ANSWERS: FxTentacle under the hero + out of every brine pool near the hero", 3, "-"),
                  ("Erupt", "pulls free", 7, "-")],
}
FX_NOTES = {
    "FxSpine": "Fly loop, faces right (urchin spine).",
    "FxWaterBolt": "Fly loop, faces right.",
    "FxHook": "Fly loop, faces right; the chain trails left toward the diver.",
    "FxBrine": "Life = spread 0-2 (0.12 s), idle 3-22 (2 frames x10, 0.37 s), fade 23-25 (0.2 s); 8.36 s total. "
               "Spread / Idle / Fade are the same frames split out, so the code can loop Idle for any duration.",
    "FxWave": "Fly loop, faces right; travels along the floor.",
    "FxBellRing": "Play once; the ring is the hit radius growing (r = 5, 11, 17, 22, 27 px on frames 0-4).",
    "FxSongNote": "Play once; rings rise ~20 px and fade.",
    "FxSplash": "Play once; crown peaks on frame 2.",
    "FxWhirlpool": "Loop (6 frames, seamless: the 3 arms turn 120 degrees per loop); ground swirl, rx 18 x ry 5 px. "
                   "Tide Matriarch Whirl.",
    "FxCoralShard": "Fly loop, faces right; spins 90 degrees per frame, cyan wake trails left. Tide Matriarch Spear.",
    "FxPeal": "Play once; a small ground ring (r = 4, 8, 12, 15 px). Bell Hermit Shell: rings out each time it is struck.",
    "FxCannonball": "Fly loop, faces right; iron ball (r 2.6) at (0, -4) with the cyan wake trailing left. Drowned Captain.",
    "FxCannonBlast": "Play once; brine spout + ground ring (r = 6, 12, 17, 19, 20, 20 px); hit while frames 0-3. Drowned Captain.",
    "FxTentacle": "Play once (Rise): frames 0-1 dark pool + bubbles (0.4 s warning), 2 tip breaks the surface, 3-5 rears "
                  "~20 px and lashes (hit), 6-8 sinks. Abyss Kraken Erupt.",
}


def write_timing(outdir):
    L = ["# Bel'Mora, the Drowned Bell: sprite timing", "",
         "Generated by `tools/sprites/belmora_rigs.py`. Frame indices are 0-based within the anim; `t` is the time",
         "from the start of the anim to the start of that frame. Monsters face right.",
         "Monster sheets: feet = (cellW//2, cellH-2). FX: origin = effect centre on the ground (fx.py convention).",
         "Spawn points are in pixels relative to the feet (x right, y up negative), facing right; mirror x when flipped.", "",
         SK.SCALE_NOTE, "",
         "## Monster sheets", "", "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h from feet) | Design scale | Anims (frames) |",
         "|---|---|---|---|---|---|"]
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        ib = SK.idle_bounds(b["img"], b["man"])
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %.2f | %s |" % (n, cw, ch, cw // 2, ch - 2, ib[0], ib[1],
                 DSCALE.get(n, 1.0), ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Move anims: sync frames", ""]
    for n in MONSTERS:
        if n not in BUILT: continue
        anims = {a: (k, d) for a, k, d in BUILT[n]["anims"]}
        done = set()
        for an, ev, fi, sp in EVENTS[n]:
            k, d = anims[an]
            if an not in done:
                L += ["### %s / `%s`: %d frames, %.2f s" % (n, an, k, sum(d)), "Durations: " + ", ".join("%.2f" % x for x in d), "",
                      "| Frame | t (s) | Moment | Spawn point |", "|---|---|---|---|"]
                done.add(an)
            assert fi < k
            L.append("| %d | %.2f | %s | %s |" % (fi, sum(d[:fi]), ev, SK.scale_text_pts(sp, DSCALE.get(n, 1.0))))
            nxt = [e for e in EVENTS[n] if e[0] == an]
            if (an, ev, fi, sp) == nxt[-1]: L.append("")
    L += ["Every attack has at least two wind-up frames before its first event. Death plays once and ends on the corpse;",
          "Dead is that same corpse frame. Bel'Mora monsters spawn FxBrine where they die (on the Dead frame).", "",
          "## FX sheets", "", "| Sheet | Cell (w x h) | Origin | Anims (frames, total s) | Notes |", "|---|---|---|---|---|"]
    for n in FXN:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"]), FX_NOTES[n]))
    L += ["", "## Icons and portrait", "", "| Sheet | Cell | Feet | Anims |", "|---|---|---|---|"]
    for n in ICONS:
        if n not in BUILT:     # not rebuilt this run (icons are badge-stamped afterwards): list them from their manifests
            jp = os.path.join(outdir, n + ".json")
            if not os.path.exists(jp): continue
            import json as _j
            m = _j.load(open(jp))
            L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, m["cellW"], m["cellH"], m["cellW"] // 2, m["cellH"] - 2,
                     ", ".join("%s %d" % (a["name"], len(a["frames"])) for a in m["anims"])))
            continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    try:   # v0.8: the new effect sheets and sheet changes
        import godsa_fx
        L += godsa_fx.timing_lines("bel")
    except Exception as e:
        print("godsa_fx timing skipped: %s" % e)
    try:   # v0.10 tree
        import belmora_tree
        L += belmora_tree.timing_lines()
    except Exception as e:
        print("belmora_tree timing skipped: %s" % e)
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(outdir, "TIMING.md"))


def contact_sheet(outdir):
    from PIL import Image, ImageDraw
    cells = []
    try:
        import belmora_tree as T10
        extra = [m for m, _ in T10.MONSTERS]
    except Exception:
        extra = []
    for n in MONSTERS + extra:
        if n not in BUILT: continue
        b = BUILT[n]; img, man = b["img"], b["man"]
        cw, chh = man["cellW"], man["cellH"]
        fi = man["anims"][0]["frames"][0]
        x0, y0 = (fi % man["cols"]) * cw, (fi // man["cols"]) * chh
        cells.append(img.crop((x0, y0, x0 + cw, y0 + chh)))
    S = 6
    H = max(c.size[1] for c in cells)
    W = sum(c.size[0] for c in cells) + 2 * len(cells)
    bg = Image.new("RGBA", (W * S, (H + 2) * S), (28, 26, 32, 255))
    x = 0
    for c in cells:
        bg.alpha_composite(c.resize((c.size[0] * S, c.size[1] * S), Image.NEAREST), (x * S, (H - c.size[1]) * S))
        x += c.size[0] + 2
    d = ImageDraw.Draw(bg)
    d.line([(0, (H - 2) * S + S // 2), (W * S, (H - 2) * S + S // 2)], fill=(60, 56, 64, 255))
    bg.convert("RGB").save(os.path.join(outdir, "contact_idle.png"))
    print("contact sheet", os.path.join(outdir, "contact_idle.png"))


# ================================================================== design scale (v0.7 size pass)
SK.install(sys.modules[__name__], {
    "ell": (["x", "x", "e", "e"], {"shader": "sh"}),
    "tube": (["P", "R"], {}),
    "line": (["x", "x", "x", "x"], {}),
    "poly": (["P"], {"shade": "m2"}),
    "crust": (["box"], {}),
})
# linear factor each monster sheet is rendered at (1.0 = authored size); see src/CrawlFurther/SheetScales.cs
# v0.9: BelCrab and BelDiver are redrawn at final size in godsa_final.py; BelDrownedBell is drawn at its design size
DSCALE = {"BelUrchin": 0.83, "BelLurefish": 0.62, "BelSiren": 0.88, "BelMatriarch": 0.69}
REDRAWN = {"BelCrab", "BelDiver"}     # built by godsa_final.py (final size)


# ================================================================== main
def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    outdir = args[0] if args else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    jobs = [("BelUrchin", build_urchin), ("BelLurefish", build_lurefish), ("BelCrab", build_crab),
            ("BelDiver", build_diver), ("BelSiren", build_siren), ("BelDrownedBell", build_giant),
            ("BelMatriarch", build_matriarch), ("BelHermit", build_hermit), ("BelLamprey", build_lamprey),
            ("BelCaptain", build_captain), ("BelKraken", build_kraken)]
    for n, fn in jobs:
        if n in REDRAWN: continue
        if only is None or n in only:
            with SK.scaled(DSCALE.get(n, 1.0)):
                fn(outdir)
    if only is None or only & (set(FXN) - set(FX_NEW)):
        build_fx(outdir, None if only is None else only & set(FXN))
    if only is None or only & set(FX_NEW):
        build_fx_new(outdir)
    if only is None or only & set(ICONS):
        build_icons(outdir)
    # v0.10 tree: the ten new monsters and their effects (belmora_tree.py)
    import belmora_tree as T10
    t10 = {n for n, _ in T10.MONSTERS} | set(T10.FX_ORDER)
    if only is None or only & t10:
        T10.main([outdir] + ([] if only is None else ["--only", ",".join(sorted(only & t10))]))
    if only is None:
        contact_sheet(outdir)
        write_timing(outdir)


if __name__ == "__main__":
    main()
