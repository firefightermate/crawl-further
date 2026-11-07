"""KAURN, THE STORM FORGE: "Iron calls the lightning down".
Every sprite sheet for the Kaurn god pack: 7 monsters, FX sheets, 2 item icons (+ shop bubbles / HUD icons),
god portrait.

    python3 kaurn_rigs.py [outdir] [--only Name,Name]

Method (same family as belmora_rigs.py): each monster is a pose function that draws shaded primitives
(ellipses, tapered tubes, polygons lit from the top-left) onto a fresh canvas, so every frame is a real
re-posed drawing. A finished pose gets a 1px soot outline, then glow pixels (lightning, eyes, forge seams)
are laid on top so they stay bright.
Look: soot-black iron, cold blue-white lightning as the main light, small orange forge seams as accents.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, PALETTE, pack, preview  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_kaurn")

# ------------------------------------------------------------------ palette (this pack only, set at import)
PALETTE.update({
    'Z': (0x0c, 0x0c, 0x12),   # soot outline
    '1': (0x17, 0x17, 0x1f), '2': (0x25, 0x26, 0x30), '3': (0x38, 0x3a, 0x46),   # iron, dark -> light
    '4': (0x52, 0x55, 0x62), '5': (0x78, 0x7d, 0x8c), '6': (0xa8, 0xae, 0xbc),
    'k': (0x2c, 0x26, 0x28), 'g': (0x45, 0x3b, 0x3a), 'h': (0x63, 0x56, 0x51),   # soot-stained skin
    't': (0x3a, 0x2a, 0x20), 'T': (0x5a, 0x40, 0x2c),                             # scorched leather
    'q': (0x45, 0x22, 0x16), 'Q': (0x84, 0x44, 0x22), 'e': (0xc2, 0x76, 0x3e), 'E': (0xee, 0xb2, 0x7a),   # copper coils
    'a': (0x7a, 0x2a, 0x12), 'o': (0xc8, 0x55, 0x1a), 'O': (0xf2, 0x8a, 0x26), 'Y': (0xff, 0xd8, 0x5e),   # forge heat
    'y': (0xff, 0xf3, 0xb8),
    '7': (0x23, 0x3c, 0x7a), '8': (0x46, 0x8a, 0xf0), '9': (0x9e, 0xda, 0xff), '0': (0xf4, 0xfc, 0xff),   # lightning
    'n': (0x1b, 0x1f, 0x2c), 'N': (0x2c, 0x34, 0x48), 'v': (0x46, 0x52, 0x6c), 'V': (0x68, 0x78, 0x96),   # storm cloth
    'u': (0x34, 0x3a, 0x4c), 'U': (0x52, 0x5a, 0x72), 'w': (0x7e, 0x88, 0xa2), 'W': (0xa8, 0xb2, 0xc8),   # thundercloud
    # v0.8 art pass: each evolution line gets its own material so the evolutions stop reading as "the same grey brute"
    '!': (0x56, 0x22, 0x1a), '@': (0x86, 0x36, 0x22), '#': (0xb8, 0x58, 0x32),                       # Rivet Imp: brick-red imp hide
    '(': (0x46, 0x20, 0x1a), ')': (0x7a, 0x34, 0x26), '/': (0xae, 0x54, 0x38),                       # Thunder Bull: oxide-red hide (v0.9)
    '<': (0x1c, 0x22, 0x32), '>': (0x2e, 0x3a, 0x54), '[': (0x46, 0x58, 0x7c), ']': (0x66, 0x7e, 0xa6),
    '{': (0x98, 0xae, 0xd0),                                                                          # Forge Colossus: blued steel
    ';': (0x2c, 0x16, 0x12), ':': (0x56, 0x26, 0x18), '+': (0x86, 0x3e, 0x22), '=': (0xb4, 0x66, 0x38),
    '-': (0xd8, 0x98, 0x60),                                                                          # Lodestone Hound: rusted magnetite
    '%': (0x1e, 0x20, 0x36), '^': (0x32, 0x36, 0x5c), '&': (0x4e, 0x52, 0x88), '*': (0x76, 0x7a, 0xb4),
    '~': (0xa8, 0xaa, 0xdc),                                                                          # Thunder Bull: storm-cloud hide
    '|': (0x24, 0x30, 0x62), '?': (0x36, 0x4a, 0x94), '}': (0x58, 0x74, 0xc4), '`': (0x8c, 0xa8, 0xe8),  # Stormcaller: storm-blue cloth
})
GLOW = set("7890oOYyE")

IRON = "1234"
IRON_L = "2345"
IRON_HI = "3456"
SOOT = "1kgh"
LEATHER = "1tT"
COPPER = "qQeE"
CLOTH = "nNvV"
CLOUD = "uUwW"
FORGE = "aoOY"


# v0.8 per-line materials (applied to the whole sheet after drawing; see lifted())
IMP_HIDE = {"k": "!", "g": "@", "h": "#"}
SMITH_SKIN = {"k": "@", "g": "#", "h": "e", "1": "2", "t": "T", "T": "Q"}   # v0.10: the imp's hide and leather, lifted
BLUE_STEEL = {"1": "<", "2": ">", "3": "[", "4": "]", "5": "{"}
FORGE_IRON = {"1": "k", "2": "g", "3": "h", "4": "i", "5": "w", "6": "W"}   # v0.10: warm, soot-stained forge iron (the Smith's palette), glowing with his heat
RUST = {"1": ";", "2": ":", "3": "+", "4": "=", "5": "-"}
STORM_HIDE = {"1": "%", "2": "^", "3": "&", "4": "*", "5": "~"}
BULL_RUST = {"1": "(", "2": ")", "3": "/", "4": "=", "5": "-"}     # v0.10: lifted a step     # v0.9: the Hound's rust deepened to oxide red
HERALD = {"n": "|", "N": "?", "v": "}", "V": "`"}   # v0.10: the caller's storm-blue cloth (no hound rust: one parent)
STORM_CLOTH = {"n": "|", "N": "?", "v": "}", "V": "`"}


# ------------------------------------------------------------------ primitives
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


def rect(c, x0, y0, x1, y1, ramp, over=True):
    """Axis box lit from the top-left: top/left edge light, bottom/right dark."""
    for y in range(int(y0), int(y1) + 1):
        for x in range(int(x0), int(x1) + 1):
            if y == y0 or x == x0: ch = ramp[-1]
            elif y == y1 or x == x1: ch = ramp[0]
            else: ch = ramp[len(ramp) // 2]
            c.put(x, y, ch, over)


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    dx, dy = tx - sx, ty - sy
    d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 1e-3))
    a = math.atan2(dy, dx)
    b = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    ea = a - bend * b
    ex, ey = sx + l1 * math.cos(ea), sy + l1 * math.sin(ea)
    return (ex, ey), (sx + d * math.cos(a), sy + d * math.sin(a))


def polar(x, y, ln, ang):
    return x + ln * math.cos(math.radians(ang)), y + ln * math.sin(math.radians(ang))


def bolt(c, x0, y0, x1, y1, seed=0, jag=1.6, core="0", edge="9", halo="8", over=True, step=3.0, fork=0.0):
    """A jagged lightning bolt from (x0,y0) to (x1,y1): white core, blue edge, dim halo under it."""
    r = random.Random(seed)
    L = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(L / step))
    nx, ny = (-(y1 - y0) / max(L, 1e-3), (x1 - x0) / max(L, 1e-3))
    pts = [(x0, y0)]
    for i in range(1, n):
        t = i / n
        off = (r.random() - 0.5) * 2 * jag
        pts.append((x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off))
    pts.append((x1, y1))
    cells = []
    for (a, b), (cx_, cy_) in zip(pts, pts[1:]):
        cells += line_px(*P(a, b), *P(cx_, cy_))
    if halo:
        for (x, y) in cells:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.put(x + dx, y + dy, halo, over=False)
    for i, (x, y) in enumerate(cells):
        c.put(x, y, core if (i % 3 != 1 or not edge) else edge, over)
    if fork and len(pts) > 2:
        k = r.randint(1, len(pts) - 2)
        fx, fy = pts[k]
        ang = math.atan2(y1 - y0, x1 - x0) + (r.random() - 0.5) * 2.2
        ex, ey = fx + math.cos(ang) * fork, fy + math.sin(ang) * fork
        for (x, y) in line_px(*P(fx, fy), *P(ex, ey)):
            c.put(x, y, edge, over=False)
    return pts


def spark(c, x, y, size=1, ch="0", arm="9"):
    """A small 4-point spark star."""
    x, y = P(x, y)
    c.put(x, y, ch)
    for k in range(1, size + 1):
        cc = arm if k == size else ch
        c.put(x + k, y, cc); c.put(x - k, y, cc); c.put(x, y + k, cc); c.put(x, y - k, cc)


def crackle(c, x, y, ph, r=3, seed=0):
    """Tiny crackling arcs jumping around (x, y), phase-dependent."""
    rnd = random.Random(seed * 31 + ph * 7)
    for k in range(2):
        a = rnd.random() * 6.28
        ln = r * (0.6 + rnd.random() * 0.6)
        x1, y1 = x + math.cos(a) * ln, y + math.sin(a) * ln
        mx, my = (x + x1) / 2 + rnd.choice((-1, 1)), (y + y1) / 2 + rnd.choice((-1, 1))
        for (p0, p1) in (((x, y), (mx, my)), ((mx, my), (x1, y1))):
            for (px_, py_) in line_px(*P(*p0), *P(*p1)):
                c.put(px_, py_, "9" if k else "0")


# ------------------------------------------------------------------ frame: body canvas + glow canvas
class Fr:
    def __init__(self):
        self.b = Canvas()   # outlined body
        self.g = Canvas()   # glow / fx pixels drawn over the outline
        self.u = Canvas()   # under-layer: drawn behind the body, also outlined (back limbs)
        self.n = Canvas()   # far layer: behind everything, no outline

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


def stamp(c, fn, ch="Z", sides=((1, 0), (-1, 0), (0, 1), (0, -1))):
    """Draw fn(tmp) on a scratch canvas, give it its own dark contour, then lay it over c.
    Separates overlapping forms (a front arm over the chest, a head over the shoulders)."""
    tmp = Canvas()
    fn(tmp)
    for (x, y), v in tmp.px.items():
        for dx_, dy_ in sides:
            k = (x + dx_, y + dy_)
            if k not in tmp.px: c.put(k[0], k[1], ch)
    for (x, y), v in tmp.px.items():
        c.put(x, y, v)


def grounded(spr):
    b = spr.bbox()
    return Spr({(x, y - b[3]): v for (x, y), v in spr.px.items()})


def recol(spr, mapping):
    return Spr({k: mapping.get(v, v) for k, v in spr.px.items()})


def dim_glow(spr):
    """Death: the lightning goes out (blue-white -> dead iron, forge -> ash)."""
    return recol(spr, {"0": "4", "9": "3", "8": "2", "7": "2", "Y": "a", "O": "a", "o": "t", "y": "a", "E": "e"})


def cv():
    return Canvas()


# ------------------------------------------------------------------ sheet helpers
BUILT = {}


def lifted(anims, remap):
    """Recolour every frame with remap; the Statue is re-cut from the recoloured Idle frame 0."""
    idle0 = recol(anims[0][1][0], remap)
    out = []
    for an, fr, du in anims:
        if an == "Statue":
            out.append((an, [idle0.stone()], du)); continue
        out.append((an, [recol(f, remap) for f in fr], du))
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
    b = anims[0][1][0].bbox()
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man,
                   "idle": (b[2] - b[0] + 1, -b[1] + 1)}
    print("built %-16s cell %dx%d  idle %dx%d (w x h incl. hover)  %s" % (name, cw, ch, b[2] - b[0] + 1, -b[1] + 1,
          ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def fx_fixed(name, anims, outdir, cell, origin, scale=8, note=""):
    """FX sheet with an explicit cell and origin (origin = the point that sits on the effect's transform)."""
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man,
                   "note": note}
    print("built %-16s cell %dx%d origin %s  %s" % (name, cell[0], cell[1], origin, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def std_tail(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


# ================================================================== v0.9 lineage motifs (shared between parents and children)
def imp_tail(c, g, x0, y0, sway=0.0, scale=1.0, lit=True, col=("!", "@")):
    """The Rivet Imp's whip tail with a spark on the tip (Imp -> Anvil Smith / Lodestone Hound)."""
    tp = [(x0, y0)]
    for k in range(1, 6):
        a = math.radians(196 + k * 14 + sway * 8 * math.sin(k * 0.9))
        tp.append((tp[-1][0] + 1.3 * scale * math.cos(a), tp[-1][1] + 1.3 * scale * math.sin(a)))
    for (xa, ya), (xb, yb) in zip(tp, tp[1:]):
        line(c, xa, ya, xb, yb, col[0])
    c.put(*P(*tp[-1]), col[1])
    if lit: g.put(*P(tp[-1][0] + 0.6, tp[-1][1] - 0.8), "9")
    return tp[-1]


def elytra(c, x, y, rx, ry, ang=0.0, seam=True):
    """The Spark Beetle's copper wing-case: a split copper shell with an iron rivet row (Beetle -> Hound / Stormcaller)."""
    ell(c, x, y, rx, ry, COPPER, ang=ang, bias=0.2)
    if seam:
        a = math.radians(ang)
        for t in range(-int(rx) + 1, int(rx)):
            c.put(*P(x + t * math.cos(a), y + t * math.sin(a) - ry * 0.15), "q")
        for t in (-0.5, 0.0, 0.5):
            c.put(*P(x + t * rx * math.cos(a), y + t * rx * math.sin(a) + ry * 0.45), "5")


def coil_antennae(c, g, x, y, ang=-70.0, L=5.0, spread=22.0, lit=True):
    """The Spark Beetle's two copper coil antennae with charged tips."""
    tips = []
    for k, sd in enumerate((-1, 1)):
        t = polar(x + sd * 0.8, y, L - k * 0.8, ang + sd * spread * 0.5)
        coil_line(c, x + sd * 0.8, y, t[0], t[1], "eQ" if k == 0 else "Qq")
        if lit: g.put(*P(*t), "0" if k == 0 else "9")
        tips.append(t)
    return tips


# ================================================================== shared iron bits
def hammer(f, hx, hy, ang, L=7.0, head=(2.4, 1.4), hot=False, smear=0, layer="b", glow_face=False):
    """Hammer held at (hx,hy); handle runs along ang for L px; head sits across the handle end."""
    c = getattr(f, layer)
    b0 = polar(hx, hy, -1.5, ang)
    e = polar(hx, hy, L, ang)
    line(c, b0[0], b0[1], e[0], e[1], "45")
    pa = ang + 90
    h0 = polar(e[0], e[1], -head[0], pa)
    h1 = polar(e[0], e[1], head[0], pa)
    tube(c, [h0, h1], [head[1], head[1]], IRON_L, bias=0.15)
    # striking face (the side the hammer swings toward) glints; hot = forge-orange seam
    face = polar(e[0], e[1], head[1] * 0.9, ang + 90 if smear >= 0 else ang - 90)
    if hot:
        f.g.put(*P(*h1), "O"); f.g.put(*P(*polar(h1[0], h1[1], -1, pa)), "o")
    if smear:
        for k in range(1, abs(smear) + 1):
            a2 = ang - 22 * k * (1 if smear > 0 else -1)
            s = polar(hx, hy, L + 0.5, a2)
            f.g.put(*P(*s), "9" if k == 1 else "8")
            f.g.put(*P(*polar(hx, hy, L - 1.5, a2)), "8" if k == 1 else "7")
    return e, h0, h1


def rivet_px(c, x, y, hot=True):
    x, y = P(x, y)
    c.put(x, y, "Y" if hot else "5"); c.put(x + 1, y, "O" if hot else "4")
    c.put(x, y + 1, "o" if hot else "3"); c.put(x + 1, y + 1, "a" if hot else "2")


# ================================================================== RIVET IMP (T1)
def imp(dx=0.0, dy=0.0, lean=0.0, feet=((-2, 0), (2, 0)), arm=62.0, ha=78.0, hl=5.4, back=(-3.5, -5.5),
        eyes="open", mouth=1, hot=False, smear=0, hammer_on=True, extra=None, head_dy=0.0, pouch=True, front=False, tail=0.0):
    f = Fr()
    hip = (dx, -3.4 + dy)
    # v0.8: a whip tail with a spark on the end (the imp's own silhouette; the Smith and Colossus have none)
    tp = [(hip[0] - 1.6, hip[1] - 0.4)]
    for k in range(1, 6):
        a = math.radians(196 + k * 14 + tail * 8 * math.sin(k * 0.9))
        tp.append((tp[-1][0] + 1.3 * math.cos(a), tp[-1][1] + 1.3 * math.sin(a)))
    polyline_c = f.u
    for (x0, y0), (x1, y1) in zip(tp, tp[1:]):
        line(polyline_c, x0, y0, x1, y1, "!")
    f.u.put(*P(*tp[-1]), "@")
    if eyes != "dead": f.g.put(*P(tp[-1][0] + 0.6, tp[-1][1] - 0.8), "9")
    # legs (back leg in the under-layer)
    for i, (fx_, fy_) in enumerate(feet):
        c = f.u if i == 0 else f.b
        hx_ = hip[0] + (-1.3 if i == 0 else 1.2)
        tube(c, [(hx_, hip[1]), (fx_ + 0.3, fy_ - 1.2)], [1.2, 1.0], SOOT, bias=-0.1 if i == 0 else 0.1)
        line(c, fx_ - 1, fy_, fx_ + 1.4, fy_, "23")          # iron-shod foot
    # rivet pouch on the back hip
    if pouch:
        ell(f.u, hip[0] - 3.0, hip[1] - 0.6, 1.6, 1.8, LEATHER, bias=0.2)
        f.g.put(*P(hip[0] - 3.4, hip[1] - 2.4), "O"); f.g.put(*P(hip[0] - 2.4, hip[1] - 2.2), "3")
    # back arm (reaching for rivets / balancing)
    sh_b = (dx - 1.2 + lean * 0.05, -8.0 + dy)
    tube(f.u, [sh_b, (sh_b[0] + back[0] * 0.5, sh_b[1] + back[1] * 0.5 + 1), (sh_b[0] + back[0], sh_b[1] + back[1] + 3)], [1.0, 0.9, 0.9], SOOT)
    # torso: pot belly, soot skin
    ell(f.b, dx + 0.2, -6.6 + dy, 3.6, 3.0, SOOT, ang=lean, bias=0.05)
    # scorched leather apron + belt with a forge-hot buckle
    poly(f.b, [(dx + 0.5, -7.8 + dy), (dx + 3.9, -7.0 + dy), (dx + 3.6, -3.9 + dy), (dx - 0.4, -3.7 + dy)], "t")
    line(f.b, dx + 0.6, -7.7 + dy, dx + 3.8, -7.0 + dy, "T")
    line(f.b, dx - 0.8, -5.5 + dy, dx + 3.8, -5.7 + dy, "2")
    f.b.put(*P(dx + 2.0, -5.6 + dy), "5")
    # head
    hx, hy = dx + 1.6 + lean * 0.06, -10.1 + dy + head_dy
    ell(f.b, hx - 0.2, hy, 3.3, 2.8, SOOT, bias=0.1)
    ell(f.b, hx + 2.6, hy + 1.0, 1.7, 1.3, SOOT, bias=0.15)                 # snout / jaw
    line(f.b, hx - 2.2, hy - 0.8, hx - 4.6, hy - 2.4, "gk")                 # pointed ear swept back
    f.b.put(*P(hx - 3.4, hy - 1.2), "k")
    # copper skullcap riveted on (v0.8: copper, not iron), two rivet horns
    ell(f.b, hx - 0.3, hy - 0.4, 3.6, 2.8, COPPER, bias=0.25, vmax=-0.05)
    line(f.b, hx - 3.6, hy - 0.4, hx + 2.6, hy - 0.4, "2")
    f.b.put(*P(hx - 1.5, hy - 1.6), "6")
    for (ox, oy) in ((-1.2, -3.0), (1.4, -3.0)):
        f.b.put(*P(hx + ox, hy + oy), "4"); f.b.put(*P(hx + ox, hy + oy - 1), "5")
    # hammer arm
    sh = (dx + 1.4 + lean * 0.05, -8.0 + dy)
    hand = polar(sh[0], sh[1], 3.2, arm)
    hres = None
    if hammer_on:
        hres = hammer(f, hand[0], hand[1], ha, L=hl, hot=hot, smear=smear)
    tube(f.b, [sh, hand], [1.1, 1.0], SOOT, bias=0.15)
    f.b.put(*P(*hand), "h")
    # face glow: two cold eyes and a forge-seam grin
    ex, ey = hx + 1.6, hy - 0.6
    if eyes == "open":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 2, ey), "9"); f.g.put(*P(ex, ey + 1), "8")
    elif eyes == "wide":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 2, ey), "0"); f.g.put(*P(ex, ey - 1), "9"); f.g.put(*P(ex + 2, ey - 1), "9")
    elif eyes == "squint":
        f.g.put(*P(ex, ey), "8"); f.g.put(*P(ex + 2, ey), "8")
    elif eyes == "dead":
        f.g.put(*P(ex, ey), "3"); f.g.put(*P(ex + 2, ey), "3")
    if mouth:
        for k in range(mouth + 1):
            f.g.put(*P(hx + 2.4 + k, hy + 1.6), "O" if k == 1 else "o")
    if extra: extra(f, hres)
    return f.done()


def imp_corpse():
    f = Fr()
    ell(f.b, 0, -2.0, 4.6, 2.0, SOOT, bias=0.0)
    ell(f.b, 4.2, -2.2, 2.6, 2.1, SOOT, bias=0.1)
    line(f.b, 6, -3.6, 8, -4.6, "gk")
    poly(f.b, [(-2, -3.5), (2, -3.6), (2, -1), (-2, -1)], "T")
    for (ox, oy) in ((3.4, -4.4), (5.4, -4.2)):
        f.b.put(*P(ox, oy), "4")
    # the dropped hammer beside it
    line(f.b, -9, 0, -4, -1, "tT")
    tube(f.b, [(-9.6, -2.4), (-9.6, 0)], [1.2, 1.2], IRON_L)
    # a spilled rivet, cooling
    f.b.put(9, 0, "3"); f.b.put(10, 0, "2")
    f.g.put(5, -3, "3"); f.g.put(6, -3, "3")
    return f.done()


def build_imp(outdir):
    I = imp
    idle = [I(),
            I(dy=0.3, arm=64, ha=80, hl=5.1, back=(-3.5, -5.0)),
            I(dy=0.3, arm=64, ha=80, hl=5.1, back=(-3.4, -4.8), eyes="squint"),
            I(dy=0.0, arm=61, ha=77, back=(-3.6, -5.6), head_dy=-0.3)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        s = math.sin(ph)
        run.append(I(dx=0.4, dy=-0.8 * abs(math.cos(ph)), lean=6,
                     feet=((-2 - 2.2 * s, -0.8 * max(0, -math.cos(ph))), (2 + 2.2 * s, -0.8 * max(0, math.cos(ph)))),
                     arm=118 + 6 * s, ha=160 - 4 * s, hl=6.5, back=(-1.0 + 2.5 * s, -4.8),
                     extra=(lambda f, h, i=i: spark(f.g, h[1][0] - 1, -1, 0, "9") if (h and i % 3 == 0) else None)))
    # BONK: crouch + hammer back, overhead, SMASH (hit on 3), shake, recover
    def bonk_fx(n):
        def fn(f, hres):
            if not hres: return
            e = hres[0]
            for k, (a, b) in enumerate(((3, -1), (-2, -2), (4, -3), (1, -4), (-3, -1))[:n]):
                f.g.put(*P(e[0] + a, -1 + b), "0" if k < 2 else "9")
            line(f.g, e[0] - 3, 0, e[0] + 3, 0, "98")
        return fn
    bonk = [I(dy=0.6, lean=-8, arm=-120, ha=-160, back=(-2.8, -4.0), eyes="squint", head_dy=0.3),
            I(dy=0.4, lean=-12, arm=-130, ha=-178, back=(-2.4, -3.8), eyes="wide", hot=True),
            I(dx=1.0, dy=-0.4, lean=4, arm=-75, ha=-80, back=(-4.4, -5.6), eyes="wide", hot=True, smear=-2),
            I(dx=1.8, dy=0.8, lean=14, arm=30, ha=48, hl=8, back=(-4.6, -6.0), eyes="squint", hot=True, mouth=2, extra=bonk_fx(5)),
            I(dx=1.6, dy=0.7, lean=12, arm=28, ha=46, hl=8, back=(-4.4, -5.8), eyes="squint", mouth=2, extra=bonk_fx(2)),
            I(dx=0.8, dy=0.3, lean=6, arm=-10, ha=-10, back=(-4.0, -5.4)),
            I(dx=0.2, dy=0.0, lean=2, arm=56, ha=66, back=(-3.6, -5.4))]

    # RIVETS: pull 3 hot rivets, toss them up, wind the hammer, BAT them out (release on 3), follow-through
    def tossed(pts):
        def fn(f, hres):
            for (x, y) in pts: rivet_px(f.g, x, y)
        return fn
    def batted(f, hres):
        e = hres[0] if hres else (8, -9)
        for k in range(3):
            line(f.g, e[0] + 1, e[1] - 1 + k * 1.5, e[0] + 5, e[1] - 2 + k * 2.5, "98")
        spark(f.g, e[0] + 1, e[1] - 1, 1)
    rivets = [I(dy=0.5, lean=-4, back=(-1.0, 3.0), arm=-50, ha=-100, eyes="squint", head_dy=0.4),
              I(dy=-0.2, lean=-2, back=(1.2, -6.5), arm=-60, ha=-110, eyes="open", extra=tossed([(3, -17), (5, -16), (1, -16)])),
              I(dy=0.4, lean=-10, back=(-2.0, -5.5), arm=-135, ha=-175, eyes="wide", hot=True,
                extra=tossed([(5, -15), (7, -14), (3, -14)])),
              I(dx=1.0, dy=0.2, lean=8, back=(-4.2, -5.2), arm=-20, ha=-30, eyes="wide", hot=True, smear=-2, mouth=2, extra=batted),
              I(dx=1.4, dy=0.4, lean=12, back=(-4.4, -5.6), arm=20, ha=30, eyes="squint", mouth=2),
              I(dx=0.8, dy=0.2, lean=6, back=(-4.0, -5.4), arm=-20, ha=-40),
              I(dx=0.2, dy=0.0, lean=2, back=(-3.6, -5.4), arm=56, ha=66)]
    death = [I(dx=-0.6, lean=-14, arm=-140, ha=-200, eyes="wide", back=(-4, -7), head_dy=-0.4, mouth=2),
             dim_glow(I(dx=-1.0, dy=1.2, lean=-26, arm=160, ha=150, eyes="squint", back=(-4.5, -2), mouth=0)),
             dim_glow(grounded(I(dx=-1.0, dy=2.6, lean=-40, arm=170, ha=190, eyes="dead", back=(-5, 0), mouth=0, pouch=False))),
             dim_glow(imp_corpse())]
    knock = I(dx=-0.6, lean=-14, arm=-140, ha=-190, eyes="squint", back=(-4, -7), head_dy=-0.3)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.08] * 6),
             ("Bonk", bonk, [0.14, 0.14, 0.06, 0.08, 0.12, 0.12, 0.12]),
             ("Rivets", rivets, [0.12, 0.14, 0.14, 0.06, 0.12, 0.12, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("KrnRivetImp", anims, outdir, scale=8, remap=IMP_HIDE)


# ================================================================== SPARK BEETLE (T1)
def coil_line(c, x0, y0, x1, y1, cols="eq", over=True):
    pts = line_px(*P(x0, y0), *P(x1, y1))
    for i, (x, y) in enumerate(pts):
        c.put(x, y, cols[i % len(cols)], over)
    return pts


def beetle(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, ant=(0.0, 0.0), rear=0.0, eye="open", charge=0, ball=False, rot=0.0,
           crackle_ph=-1, extra=None, gait=1.0, flip=False):
    f = Fr()
    if ball:
        cx, cy = dx, -5.2 + dy
        ell(f.b, cx, cy, 5.0, 5.0, COPPER, bias=0.15)
        # riveted shell seams rolling around
        for k in range(3):
            a = math.radians(rot + k * 120)
            for t in (0.3, 0.6, 0.9):
                f.b.put(*P(cx + math.cos(a) * 5 * t, cy + math.sin(a) * 5 * t), "2")
            f.b.put(*P(cx + math.cos(a) * 3.2, cy + math.sin(a) * 3.2), "6")
        out = f.done()
        g = Fr()
        for k in range(4):
            a = math.radians(rot * 1.7 + k * 90 + 20)
            x0, y0 = cx + math.cos(a) * 4.0, cy + math.sin(a) * 4.0
            x1, y1 = cx + math.cos(a + 0.6) * 8.0, cy + math.sin(a + 0.6) * 7.0
            bolt(g.g, x0, y0, x1, y1, seed=k + int(rot), jag=1.0, step=2.0)
        px = dict(out.px)
        for k, v in g.g.px.items():
            if k not in out.px or v in "09": px[k] = v
        return Spr({k: v for k, v in px.items() if k[1] <= 0})
    ca = math.radians(tilt)
    def R(x, y):  # rotate body points about the hind feet
        x, y = x - (-5), y
        return (-5 + x * math.cos(ca) - y * math.sin(ca) + dx, x * math.sin(ca) + y * math.cos(ca) + dy)
    # far legs (no outline, in shadow)
    for i, (hx, fx_) in enumerate(((-4.0, -6.5), (-0.5, 0.0), (3.0, 6.0))):
        ph = legs + i * 2.1 + math.pi
        lift = max(0.0, math.sin(ph)) * 1.4 * gait
        knee = R(hx + 0.6, -6.0)
        footx = fx_ + math.cos(ph) * 1.6 * gait + dx
        line(f.n, *R(hx, -3.5), knee[0], knee[1] - 0.5, "3")
        line(f.n, knee[0], knee[1] - 0.5, footx + 1, -lift, "2")
    # abdomen + elytra shell
    shell_c = R(-0.9, -5.2 - rear * 0.3)
    ell(f.b, shell_c[0], shell_c[1], 6.0, 3.9, COPPER, ang=tilt - rear * 4, bias=0.18)     # v0.8: a copper shell
    # the elytra seam: a split in the shell that glows with stored charge
    for k in range(9):
        x = -5.6 + k * 1.1
        sp_ = R(x, -6.2 - 0.9 * math.sin((k + 0.5) / 9 * math.pi) - rear * 0.3)
        f.g.put(*P(*sp_), "8" if (k + max(charge, 0)) % 3 else "9")
    # under-belly plates (dark) and the shell rim
    ell(f.b, *R(-1.0, -2.6), 5.6, 1.4, "1223", ang=tilt, bias=-0.3)
    lo = [R(x, -3.4 + 0.02 * x * x) for x in range(-7, 5)]
    for (x, y) in lo: f.b.put(*P(x, y), "2")
    # rivets along the shell and a copper coil band
    for x in (-4.6, -1.8, 1.0):
        f.b.put(*P(*R(x, -4.6 + 0.02 * x * x - rear * 0.3)), "5")
    band = R(-4.0, -5.0)
    for k in range(4):
        f.b.put(*P(band[0] + (k % 2), band[1] - 2 + k), "5" if k % 2 == 0 else "3")       # iron band on the copper
    # head + mandibles
    hc = R(5.4 + rear * 0.3, -4.0 - rear * 0.6)
    ell(f.b, hc[0], hc[1], 2.4, 2.2, IRON_HI, bias=0.05)
    line(f.b, hc[0] + 1.8, hc[1] + 1.0, hc[0] + 3.0, hc[1] + 1.6, "5")
    f.b.put(*P(hc[0] + 3.0, hc[1] + 0.6), "6")
    # near legs
    for i, (hx, fx_) in enumerate(((-4.6, -7.5), (-1.2, -1.0), (2.4, 5.0))):
        ph = legs + i * 2.1
        lift = max(0.0, math.sin(ph)) * 1.6 * gait
        knee = R(hx + 0.5, -5.2)
        footx = fx_ + math.cos(ph) * 1.8 * gait + dx
        line(f.u, *R(hx, -3.2), knee[0], knee[1] - 0.4, "4")
        line(f.b, knee[0], knee[1] - 0.4, footx, -lift, "45")
    # copper coil antennae
    tips = []
    for k, (base_dx, L, a0) in enumerate(((0.4, 6.5, -62.0), (-0.6, 5.8, -78.0))):
        a = a0 + ant[k] + tilt - rear * 18
        b0 = (hc[0] + base_dx + 0.6, hc[1] - 1.8)
        t = polar(b0[0], b0[1], L, a)
        coil_line(f.b if k == 0 else f.u, b0[0], b0[1], t[0], t[1], "eQ" if k == 0 else "Qq")
        tips.append(t)
    # glow: eye + charged antenna tips
    ex, ey = hc[0] + 1.0, hc[1] - 0.6
    if eye == "open":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "9")
    elif eye == "wide":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "0"); f.g.put(*P(ex, ey - 1), "9")
    elif eye == "dead":
        f.g.put(*P(ex, ey), "3")
    for i, t in enumerate(tips):
        if eye == "dead": break
        f.g.put(*P(*t), "0" if charge or i == 0 else "9")
        if charge >= 2: f.g.put(*P(t[0], t[1] - 1), "9"); f.g.put(*P(t[0] + 1, t[1]), "8")
    if crackle_ph >= 0 and eye != "dead":
        bolt(f.g, tips[0][0], tips[0][1], tips[1][0], tips[1][1], seed=crackle_ph, jag=1.0, step=2.0, halo=None)
    if charge >= 3:
        for t in tips: spark(f.g, t[0], t[1], 1)
    if extra: extra(f, tips, hc)
    out = f.done()
    if flip:   # on its back (death)
        out = Spr({(x, -y - 10 if False else y): v for (x, y), v in out.px.items()})
    return out


def beetle_corpse():
    f = Fr()
    # on its back: shell down, dark belly up, legs curled in the air
    ell(f.b, 0, -3.0, 6.4, 3.0, IRON_HI, bias=0.0)
    ell(f.b, 0, -4.6, 5.2, 1.6, "1223", bias=-0.3)
    for k, x in enumerate((-3.5, -0.5, 2.5)):
        line(f.b, x, -5.6, x + (1 if k % 2 else -1), -8.0, "3")
        f.b.put(x + (2 if k % 2 else -2), -8, "2")
    ell(f.b, 6.4, -2.2, 2.0, 1.8, IRON_L)
    coil_line(f.b, 7.5, -3.5, 10.5, -1.0, "eQ")
    f.g.put(6, -2, "3")
    return f.done()


def build_beetle(outdir):
    B = beetle
    idle = [B(ant=(0, 0), crackle_ph=0, legs=0.0, gait=0.0),
            B(ant=(-4, -3), dy=0.3, legs=0.0, gait=0.0),
            B(ant=(-6, -5), dy=0.3, crackle_ph=2, legs=0.0, gait=0.0, eye="open"),
            B(ant=(-2, 2), legs=0.0, gait=0.0)]
    run = [B(legs=i * math.pi / 3, dy=-0.4 * abs(math.sin(i * math.pi / 3)), tilt=-2, ant=(-10 + 3 * (i % 2), -8), crackle_ph=i if i % 2 else -1)
           for i in range(6)]
    # ZAP: rear back, antennae forward, charge, ZAP (release on 3), recoil, settle
    def zap_fx(f, tips, hc):
        for t in tips:
            line(f.g, t[0], t[1], t[0] + 4, t[1] + 0.5, "09")
        spark(f.g, tips[0][0] + 4, tips[0][1] + 0.5, 2)
    zap = [B(rear=0.6, tilt=-6, ant=(-8, -6), charge=1, eye="open"),
           B(rear=1.0, tilt=-10, ant=(-14, -10), charge=2, eye="wide", crackle_ph=1),
           B(rear=0.6, tilt=-4, ant=(22, 20), charge=3, eye="wide", crackle_ph=3),
           B(rear=0.0, tilt=2, dx=0.8, ant=(34, 30), charge=3, eye="wide", extra=zap_fx),
           B(rear=0.2, tilt=0, dx=0.4, ant=(26, 24), charge=1, eye="open"),
           B(rear=0.0, tilt=0, ant=(4, 2), eye="open")]
    # RUSH: crouch, curl, 4 frames of rolling ball lightning, uncurl
    rush = [B(rear=-0.4, tilt=6, dy=0.5, ant=(-24, -20), charge=2, eye="wide", gait=0.3),
            B(ball=True, rot=0, dy=0.0),
            B(ball=True, rot=30, dy=-0.6),
            B(ball=True, rot=60, dy=-1.0),
            B(ball=True, rot=90, dy=-0.6),
            B(ball=True, rot=120, dy=0.0),
            B(rear=0.2, tilt=-4, ant=(10, 8), charge=1, eye="open", crackle_ph=5)]
    death = [B(rear=1.2, tilt=-14, ant=(30, -30), eye="wide", charge=3, crackle_ph=4),
             dim_glow(B(rear=0.6, tilt=-24, ant=(50, -40), eye="dead", dy=-1.0, legs=1.0)),
             dim_glow(grounded(B(rear=0.0, tilt=-40, ant=(70, -50), eye="dead", legs=2.0))),
             dim_glow(beetle_corpse())]
    knock = B(rear=1.0, tilt=-12, ant=(24, -24), eye="wide", legs=0.6, crackle_ph=6)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.07] * 6),
             ("Zap", zap, [0.12, 0.14, 0.1, 0.06, 0.12, 0.14]),
             ("Rush", rush, [0.14, 0.08, 0.06, 0.06, 0.06, 0.06, 0.16])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("KrnSparkBeetle", anims, outdir, scale=8)


# ================================================================== COIL WISP (T1, flying)
def wisp(dx=0.0, dy=0.0, tilt=0.0, fin=0.0, core=1.0, ph=0, tail=0.0, eye="open", cage_open=0.0, extra=None, dead=False, cy0=-8.8):
    f = Fr()
    cx, cy = dx, cy0 + dy
    # copper coil tail hanging below, swaying
    pts = [(cx + math.sin(k * 0.9 + tail) * 0.6 * k * 0.4, cy + 4.2 + k) for k in range(4)]
    for k, (x, y) in enumerate(pts):
        f.u.put(*P(x, y), "e" if k % 2 == 0 else "q")
        f.u.put(*P(x + 1, y), "Q" if k % 2 == 0 else "q")
    # iron fins
    for sd in (-1, 1):
        a = -90 + sd * (55 + fin)
        b0 = (cx + sd * 3.6, cy - 0.5)
        t = polar(b0[0], b0[1], 3.2, a)
        tube(f.u if sd < 0 else f.b, [b0, t], [1.1, 0.4], IRON_L, bias=0.1)
    # cage: an iron ring (side view: vertical ellipse) with two crossing bands, a top knob and a bottom collar
    R = 4.3 + cage_open
    for k in range(48):
        a = 2 * math.pi * k / 48
        x, y = cx + math.cos(a) * R, cy + math.sin(a) * R
        lit = math.cos(a) + math.sin(a) < 0
        f.b.put(*P(x, y), "5" if lit else "3")
    for k in range(20):
        t = -1 + k / 9.5
        x = cx + t * R * 0.35 * math.cos(math.radians(tilt))
        y = cy + t * R
        f.b.put(*P(x - R * 0.35 * math.sqrt(max(0, 1 - t * t)) * 0.0, y), "4" if t < 0 else "2")
    f.b.put(*P(cx, cy - R - 0.8), "6"); f.b.put(*P(cx - 1, cy - R - 0.2), "4"); f.b.put(*P(cx + 1, cy - R - 0.2), "3")
    line(f.b, cx - 1.5, cy + R, cx + 1.5, cy + R, "23")
    # core of ball lightning inside the cage (glow, drawn over the cage interior)
    rr = 2.6 * core
    if not dead:
        for y in range(int(cy - rr) - 1, int(cy + rr) + 2):
            for x in range(int(cx - rr) - 1, int(cx + rr) + 2):
                d = math.hypot(x - cx + 0.3, y - cy + 0.3) / max(rr, 0.1)
                if d <= 1.0:
                    f.g.put(x, y, "0" if d < 0.45 else "9" if d < 0.8 else "8")
        rnd = random.Random(ph)
        for k in range(2):
            a = rnd.random() * 6.28
            bolt(f.g, cx + math.cos(a) * rr * 0.8, cy + math.sin(a) * rr * 0.8, cx + math.cos(a) * (R - 0.6), cy + math.sin(a) * (R - 0.6),
                 seed=ph * 3 + k, jag=0.6, step=1.5, halo=None)
        # an eye-like hot spot looking the way it faces
        if eye == "open": f.g.put(*P(cx + 1.4, cy - 0.6), "0"); f.g.put(*P(cx + 2.2, cy - 0.6), "9")
        elif eye == "wide": f.g.put(*P(cx + 1.6, cy - 1), "0"); f.g.put(*P(cx + 1.6, cy), "0")
        f.g.put(*P(pts[-1][0], pts[-1][1] + 1), "9" if ph % 2 else "8")
    else:
        ell(f.b, cx, cy, 2.2, 2.2, IRON, bias=-0.2)
    if extra: extra(f, cx, cy, R)
    return f.done()


def wisp_corpse():
    f = Fr()
    # the cage cracked open on the floor, the coil unwound, the core dead
    for k in range(28):
        a = math.pi + math.pi * k / 27
        f.b.put(*P(math.cos(a) * 4.5, -1.5 + math.sin(a) * 2.6), "4" if k < 14 else "3")
    line(f.b, -4.5, -1, 4.5, -1, "23")
    ell(f.b, 0, -2, 1.8, 1.4, IRON, bias=-0.2)
    for k in range(5):
        f.b.put(6 + k, 0 if k % 2 else -1, "e" if k % 2 else "q")
    tube(f.b, [(-6, -1), (-8, -3)], [1.0, 0.4], IRON_L)
    return f.done()


def build_wisp(outdir):
    W = wisp
    idle = [W(dy=0.4, fin=0, ph=0, tail=0), W(dy=0.0, fin=8, ph=1, tail=0.8, core=1.05),
            W(dy=-0.2, fin=12, ph=2, tail=1.6), W(dy=0.2, fin=6, ph=3, tail=2.4, core=0.95)]
    run = [W(dx=0.5, dy=[-0.2, -0.8, -1.0, -0.6, 0.0, 0.0][i], fin=[0, 14, 24, 14, 4, 0][i], ph=i + 4, tail=i * 0.9 + 2, tilt=8)
           for i in range(6)]
    def muzzle(n):
        def fn(f, cx, cy, R):
            for k in range(n):
                f.g.put(*P(cx + R + 1 + k, cy - 0.5 + (k % 2) - 0.5), "0" if k < 2 else "9")
            if n > 2: spark(f.g, cx + R + 2, cy - 0.5, 2)
        return fn
    shot = [W(dy=0.4, fin=-10, core=0.8, ph=10, eye="open"),
            W(dy=0.2, dx=-0.6, fin=-20, core=1.25, ph=11, eye="wide"),
            W(dy=0.0, dx=-0.8, fin=-24, core=1.4, ph=12, eye="wide", extra=muzzle(1)),
            W(dy=-0.2, dx=0.6, fin=24, core=0.9, ph=13, eye="wide", extra=muzzle(4)),
            W(dy=-0.4, dx=0.2, fin=14, core=0.8, ph=14),
            W(dy=0.0, fin=4, core=1.0, ph=15)]
    def arcs(n, r1):
        def fn(f, cx, cy, R):
            for k in range(n):
                a = k * 360.0 / n + 15
                x0, y0 = polar(cx, cy, R, a)
                x1, y1 = polar(cx, cy, r1, a + 8)
                bolt(f.g, x0, y0, x1, min(y1, -0.5), seed=k + n, jag=1.0, step=2.0, halo="7")
        return fn
    pulse = [W(dy=0.4, fin=-14, core=0.7, ph=20, eye="squint"),
             W(dy=0.6, fin=-26, core=1.0, ph=21, eye="squint", cage_open=0.3),
             W(dy=0.8, fin=-30, core=1.3, ph=22, eye="wide", cage_open=0.6, extra=arcs(3, 6)),
             W(dy=0.8, fin=-34, core=1.5, ph=23, eye="wide", cage_open=0.8, extra=arcs(5, 7)),
             W(dy=-0.4, fin=34, core=1.6, ph=24, eye="wide", cage_open=1.0, extra=arcs(8, 11)),
             W(dy=-0.6, fin=26, core=1.0, ph=25, eye="wide", cage_open=0.4, extra=arcs(4, 9)),
             W(dy=-0.3, fin=12, core=0.8, ph=26, eye="open"),
             W(dy=0.0, fin=4, core=1.0, ph=27)]
    death = [W(dy=0.5, fin=-30, core=1.6, ph=30, eye="wide", cage_open=0.8, tilt=-20),
             dim_glow(W(dy=3.5, fin=40, core=0.6, ph=31, eye="squint", tilt=-30)),
             W(dy=5.8, dead=True, fin=60, tilt=-40),
             wisp_corpse()]
    knock = W(dx=-0.6, dy=0.3, fin=-30, core=1.2, ph=33, eye="wide", tilt=-14)
    anims = [("Idle", idle, [0.18, 0.18, 0.18, 0.18]), ("Run", run, [0.08] * 6),
             ("Spark", shot, [0.12, 0.12, 0.12, 0.06, 0.12, 0.14]),
             ("Pulse", pulse, [0.12, 0.12, 0.12, 0.1, 0.08, 0.12, 0.12, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("KrnCoilWisp", anims, outdir, scale=8)


# ================================================================== ANVIL SMITH (T2, Rivet Imp / Spark Beetle line)
def iron_rod(c, g, x0, y0, ang, L, lit=True, tip=True):
    """A lightning rod: dark iron shaft, copper collar, bright tip."""
    e = polar(x0, y0, L, ang)
    pts = line(c, x0, y0, e[0], e[1], "3")
    for i, (x, y) in enumerate(pts):
        if i % 4 == 1: c.put(x, y, "5")
    col = polar(x0, y0, L - 2.2, ang)
    c.put(*P(*col), "e"); c.put(*P(*polar(x0, y0, L - 1.4, ang)), "Q")
    if tip: g.put(*P(*e), "0" if lit else "5")
    return e


def anvil_shape(c, x, y, s=1.0):
    """A little anvil (horn to the left): used as the smith's shoulder plate."""
    pts = [(x - 4.6 * s, y - 1.0 * s), (x - 1.8 * s, y - 2.4 * s), (x + 2.8 * s, y - 2.4 * s), (x + 2.8 * s, y - 0.4 * s),
           (x + 1.4 * s, y + 0.2 * s), (x + 1.8 * s, y + 1.6 * s), (x - 1.6 * s, y + 1.6 * s), (x - 1.2 * s, y + 0.2 * s),
           (x - 2.8 * s, y + 0.2 * s)]
    poly(c, pts, "3", shade=lambda X, Y: "5" if Y <= y - 2 else ("2" if Y >= y + 1 else "4" if X < x else "3"))


def smith(dx=0.0, dy=0.0, lean=0.0, feet=((-4, 0), (4, 0)), arm=55.0, ha=62.0, hl=11.0, bhand=(-6.0, -9.0),
          rod=None, quiver=2, eyes="open", armour=0, ph=0, smear=0, hot=False, head_dy=0.0, extra=None, dead=False):
    f = Fr()
    hip = (dx, -8.0 + dy)
    # legs: thick, iron-booted
    for i, (fx_, fy_) in enumerate(feet):
        c = f.u if i == 0 else f.b
        hx_ = hip[0] + (-2.4 if i == 0 else 2.2)
        knee = ((hx_ + fx_) / 2 + 1.0, (hip[1] + fy_) / 2 - 0.5)
        tube(c, [(hx_, hip[1]), knee, (fx_, fy_ - 1.6)], [2.2, 1.8, 1.5], SOOT, bias=-0.15 if i == 0 else 0.05)
        rect(c, fx_ - 1.8, fy_ - 2, fx_ + 2.4, fy_, "2345")
    # v0.9 lineage (Rivet Imp): the imp's whip tail, grown, with its spark tip
    imp_tail(f.u, f.g, hip[0] - 3.4, hip[1] - 1.0, sway=lean * 0.05, scale=1.6, lit=not dead, col=("k", "g"))
    # quiver of spare lightning rods across the back
    for k in range(quiver):
        iron_rod(f.u, f.g, dx - 4.5 + k * 1.6 + lean * 0.05, -11.5 + dy, -100 + k * 9, 12.0 - k * 1.5, lit=False)
    # back arm
    sh_b = (dx - 3.0 + lean * 0.08, -16.5 + dy)
    hb = (dx + bhand[0], -16.5 + dy + bhand[1] + 9.0)
    (eb, _) = ik(sh_b[0], sh_b[1], hb[0], hb[1], 4.6, 4.4, bend=-1)
    tube(f.u, [sh_b, eb, hb], [2.0, 1.7, 1.6], SOOT, bias=-0.1)
    if rod is not None:
        iron_rod(f.u, f.g, rod[0], rod[1], rod[2], rod[3], lit=True)
    # torso: barrel chest
    ell(f.b, dx + 0.4, -13.2 + dy, 6.2, 5.6, SOOT, ang=lean, bias=0.05)
    # leather apron with iron studs, belt
    poly(f.b, [(dx - 1.0, -16.0 + dy), (dx + 6.2, -14.8 + dy), (dx + 5.6, -6.0 + dy), (dx - 2.0, -6.2 + dy)], "T",
         shade=lambda X, Y: "t" if X >= dx + 4.6 or Y >= -7 + dy else "T")
    line(f.b, dx - 0.8, -15.9 + dy, dx + 6.0, -14.8 + dy, "h")
    line(f.b, dx - 4.8, -10.0 + dy, dx + 6.0, -10.4 + dy, "2")
    rect(f.b, dx + 1.5, -11.2 + dy, dx + 3.0, -9.4 + dy, "345")
    for (x, y) in ((1.0, -13.4), (4.0, -12.8), (2.0, -7.8)):
        f.b.put(*P(dx + x, y + dy), "O" if not dead else "4")     # forge-hot studs
    # v0.8: a full anvil strapped across the back, its horn jutting behind the shoulders (his silhouette), with a
    # leather strap over the chest and a hot horseshoe hanging off it
    stamp(f.u, lambda c: anvil_shape(c, dx - 3.6 + lean * 0.1, -18.0 + dy, 1.15), ch="1")
    line(f.b, dx - 3.4, -18.0 + dy, dx + 4.4, -10.8 + dy, "t")
    f.g.put(*P(dx - 4.4 + lean * 0.1, -16.6 + dy), "O"); f.g.put(*P(dx - 3.4 + lean * 0.1, -16.6 + dy), "o")
    # head: low and forward, iron welding mask with a lightning slit
    hx, hy = dx + 4.2 + lean * 0.12, -18.4 + dy + head_dy
    def head(c):
        ell(c, hx - 0.6, hy, 2.6, 2.6, SOOT, bias=0.25)
        poly(c, [(hx + 0.2, hy - 2.8), (hx + 3.8, hy - 2.2), (hx + 3.8, hy + 1.8), (hx + 0.4, hy + 2.6)], "4",
             shade=lambda X, Y: "6" if Y <= hy - 2.4 else ("5" if X <= hx + 1 else "3" if X >= hx + 3.4 else "4"))
        c.put(*P(hx + 2, hy + 1.6), "2")
    stamp(f.b, head, ch="1")
    # v0.9 lineage (Rivet Imp): the imp's pointed ear swept back past the mask, and its copper skullcap with rivet horns
    line(f.b, hx - 2.4, hy - 1.0, hx - 6.0, hy - 3.6, "gk"); f.b.put(*P(hx - 4.4, hy - 2.2), "k")
    ell(f.b, hx - 0.8, hy - 1.6, 2.8, 1.8, COPPER, bias=0.3, vmax=0.0)
    for ox in (-2.0, 0.6):
        f.b.put(*P(hx + ox, hy - 3.6), "e"); f.b.put(*P(hx + ox, hy - 4.6), "E")
    # front arm + hammer
    sh = (dx + 2.6 + lean * 0.1, -16.4 + dy)
    hand = polar(sh[0], sh[1], 6.0, arm)
    elbow = polar(sh[0], sh[1], 3.2, arm - 25)
    hres = hammer(f, hand[0], hand[1], ha, L=hl, head=(3.6, 2.0), hot=hot, smear=smear)
    # copper coil wound round the hammer head, charged
    e, h0, h1 = hres
    for k in range(3):
        t = 0.25 + k * 0.25
        f.g.put(*P(h0[0] + (h1[0] - h0[0]) * t, h0[1] + (h1[1] - h0[1]) * t), "e" if k != 1 else "Q")
    if not dead:
        f.g.put(*P(*h1), "9" if not hot else "O")
    def farm(c):
        tube(c, [sh, elbow, hand], [2.2, 1.9, 1.7], SOOT, bias=0.35)
        # iron bracer on the forearm
        bm = ((elbow[0] + hand[0] * 2) / 3, (elbow[1] + hand[1] * 2) / 3)
        tube(c, [polar(bm[0], bm[1], -1.2, arm), polar(bm[0], bm[1], 1.0, arm)], [2.0, 2.0], IRON_HI, bias=0.2)
        c.put(*P(*hand), "h"); c.put(*P(hand[0] - 1, hand[1]), "g")
    stamp(f.b, farm, ch="1")
    # forge seams on the forearm (accent)
    f.g.put(*P(*polar(elbow[0], elbow[1], 0.6, arm - 90)), "o")
    f.g.put(*P(*polar(sh[0], sh[1], 1.2, arm - 60)), "O")
    # visor slit
    if eyes == "open":
        line(f.g, hx + 1.2, hy - 0.4, hx + 3.2, hy - 0.4, "90")
    elif eyes == "wide":
        line(f.g, hx + 1.0, hy - 0.4, hx + 3.6, hy - 0.4, "0"); f.g.put(*P(hx + 4.4, hy - 0.4), "9")
    elif eyes == "dead":
        line(f.g, hx + 1.2, hy - 0.4, hx + 3.2, hy - 0.4, "2")
    # tempered armour: charge crawling over the body
    if armour:
        rnd = random.Random(ph)
        for k in range(armour + 1):
            a = rnd.uniform(0, 6.28)
            x0, y0 = dx + math.cos(a) * 5.0, -13 + dy + math.sin(a) * 5.5
            bolt(f.g, x0, y0, x0 + rnd.uniform(-4, 4), y0 + rnd.uniform(-4, 3), seed=ph * 5 + k, jag=1.0, step=2.0, halo=None)
    if extra: extra(f, hres)
    return f.done()


def smith_corpse():
    f = Fr()
    ell(f.b, 0, -3.2, 8.4, 3.2, SOOT, bias=0.0)
    poly(f.b, [(-3, -5.6), (5, -5.6), (5, -1.0), (-3, -1.0)], "t")
    ell(f.b, 9.0, -2.6, 2.6, 2.4, SOOT, bias=0.1)
    poly(f.b, [(9.4, -5.0), (12.2, -4.4), (12.2, -0.8), (9.6, -0.6)], "4")
    anvil_shape(f.b, -7.0, -2.8, 1.0)
    # dropped hammer and a snapped rod
    line(f.b, -16, 0, -10, -1, "45")
    tube(f.b, [(-16.5, -3.4), (-16.5, 0)], [1.8, 1.8], IRON_L)
    line(f.b, 13, 0, 18, -2, "3"); f.b.put(18, -2, "e")
    f.g.put(10, -3, "2"); f.g.put(11, -3, "2")
    return f.done()


def build_smith(outdir):
    S = smith
    idle = [S(),
            S(dy=0.4, arm=57, ha=64, bhand=(-6.2, -8.6), head_dy=0.3),
            S(dy=0.5, arm=58, ha=65, bhand=(-6.4, -8.4), head_dy=0.4, eyes="open"),
            S(dy=0.2, arm=56, ha=63, bhand=(-6.1, -8.8))]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        sn = math.sin(ph)
        run.append(S(dx=0.6, dy=-0.9 * abs(math.cos(ph)), lean=8,
                     feet=((-4 - 3.2 * sn, -1.2 * max(0, -math.cos(ph))), (4 + 3.2 * sn, -1.2 * max(0, math.cos(ph)))),
                     arm=100 + 6 * sn, ha=150, hl=11, bhand=(-6.0 + 2.5 * sn, -8.0)))
    # HAMMER: heave back, overhead, smear, IMPACT (3: hit + spark surge from (18, 0)), hold, lift, recover
    def impact(n):
        def fn(f, hres):
            e = hres[0]
            for k, (a, b) in enumerate(((4, -2), (-3, -3), (6, -4), (1, -6), (-5, -1), (8, -1))[:n]):
                f.g.put(*P(e[0] + a, b), "0" if k < 2 else "9")
            line(f.g, e[0] - 5, 0, e[0] + 6, 0, "098")
            if n > 3:
                bolt(f.g, e[0] + 3, -1, e[0] + 10, -2, seed=3, jag=1.0, step=2.0)
        return fn
    ham = [S(dy=0.6, lean=-6, arm=-40, ha=-110, bhand=(-5, -9), eyes="open", head_dy=0.4),
           S(dy=0.4, lean=-12, arm=-120, ha=-175, bhand=(-4, -10), eyes="wide", hot=True),
           S(dx=1.0, dy=-0.4, lean=4, arm=-60, ha=-40, bhand=(-6, -8), eyes="wide", hot=True, smear=-3),
           S(dx=2.0, dy=1.0, lean=16, arm=30, ha=58, hl=12, bhand=(-7, -7), eyes="wide", hot=True, extra=impact(6),
             feet=((-5, 0), (5, 0))),
           S(dx=2.0, dy=1.0, lean=15, arm=30, ha=58, hl=12, bhand=(-7, -7), eyes="open", extra=impact(2), feet=((-5, 0), (5, 0))),
           S(dx=1.0, dy=0.4, lean=8, arm=10, ha=20, bhand=(-6.5, -8)),
           S(dx=0.3, dy=0.0, lean=2, arm=50, ha=58, bhand=(-6.2, -8.8))]
    # TEMPER: pull a rod off the back, plant it, hammer it home (3: rod spawns at (11, 0)),
    # lightning answers and runs into the smith's iron (4: gains a plate), glow, recover
    def drive(f, hres):
        spark(f.g, 11, -9, 2)
        for (a, b) in ((13, -8), (9, -10), (14, -11)):
            f.g.put(a, b, "9")
    def answer(f, hres):
        bolt(f.g, 11, -9, 11, -30, seed=7, jag=1.6, step=2.5)
        bolt(f.g, 11, -9, 4, -14, seed=8, jag=1.2, step=2.0)
    tem = [S(dy=0.4, lean=-4, bhand=(-6, -16), quiver=2, arm=60, ha=75, eyes="open"),
           S(dy=0.2, lean=4, bhand=(8, -10), rod=(11, 0, -90, 9), quiver=1, arm=-30, ha=-100, eyes="open"),
           S(dy=0.4, lean=-8, bhand=(8, -9), rod=(11, 0, -90, 9), quiver=1, arm=-120, ha=-170, eyes="wide", hot=True),
           S(dx=1.0, dy=0.8, lean=12, bhand=(7, -6), rod=(11, 0, -90, 6), quiver=1, arm=10, ha=-10, hl=10, eyes="wide", hot=True,
             smear=-2, extra=drive),
           S(dx=1.0, dy=0.6, lean=6, bhand=(-6, -8), quiver=1, arm=20, ha=30, eyes="wide", armour=3, ph=1, extra=answer),
           S(dx=0.6, dy=0.2, lean=2, bhand=(-6, -8.6), quiver=1, arm=40, ha=50, eyes="wide", armour=2, ph=2),
           S(dx=0.3, dy=0.2, lean=0, bhand=(-6, -8.8), quiver=1, arm=50, ha=58, eyes="open", armour=1, ph=3),
           S(dy=0.0, bhand=(-6.1, -8.8), quiver=1, arm=55, ha=62)]
    death = [S(dx=-0.8, lean=-14, arm=-140, ha=-200, eyes="wide", bhand=(-8, -12), head_dy=-0.4, armour=2, ph=9),
             dim_glow(S(dx=-1.4, dy=2.0, lean=-26, arm=170, ha=160, eyes="dead", bhand=(-9, -4), dead=True)),
             dim_glow(grounded(S(dx=-1.4, dy=5.0, lean=-44, arm=180, ha=190, eyes="dead", bhand=(-10, 0), dead=True, quiver=0))),
             dim_glow(smith_corpse())]
    knock = S(dx=-0.8, lean=-14, arm=-140, ha=-195, eyes="wide", bhand=(-8, -12), head_dy=-0.3)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.09] * 6),
             ("Hammer", ham, [0.16, 0.16, 0.06, 0.08, 0.14, 0.14, 0.14]),
             ("Temper", tem, [0.14, 0.16, 0.16, 0.06, 0.12, 0.14, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("KrnAnvilSmith", anims, outdir, scale=6, remap=SMITH_SKIN)


# ================================================================== STORMCALLER (T2, Spark Beetle / Coil Wisp line)
def staff(f, x0, y0, ang, L=22.0, ph=0, charge=1, top_over=True, cage=False):
    """Lightning-rod staff: iron shaft, copper coil near the top, a crackling tip."""
    e = polar(x0, y0, L, ang)
    def shaft(c):
        pts = line(c, x0, y0, e[0], e[1], "4")
        for i, (x, y) in enumerate(pts):
            if i % 5 == 2: c.put(x, y, "6")
    stamp(f.b, shaft, ch="1", sides=((1, 0), (-1, 0)))
    # coil: alternating copper pixels astride the shaft near the top
    for k in range(5):
        cp = polar(x0, y0, L - 2.5 - k, ang)
        side = polar(cp[0], cp[1], 1.0 if k % 2 == 0 else -1.0, ang + 90)
        f.b.put(*P(*cp), "e" if k % 2 == 0 else "Q")
        f.b.put(*P(*side), "Q" if k % 2 == 0 else "q")
    # fork tines at the very top
    for sd in (-1, 1):
        t0 = polar(e[0], e[1], 0, ang)
        t1 = polar(t0[0], t0[1], 1.6, ang + sd * 35)
        line(f.b, t0[0], t0[1], t1[0], t1[1], "5")
    if cage:   # v0.9 lineage (Coil Wisp): the wisp's copper coil cage caught on the staff head, its spark inside
        cc = polar(e[0], e[1], -0.6, ang)
        for k in range(10):
            a = 2 * math.pi * k / 10
            f.b.put(*P(cc[0] + 2.4 * math.cos(a), cc[1] + 2.4 * math.sin(a)), "e" if k % 2 else "Q")
        f.g.put(*P(*cc), "9")
    if charge:
        tip = polar(e[0], e[1], 1.6, ang)
        f.g.put(*P(*tip), "0")
        if charge >= 2:
            spark(f.g, tip[0], tip[1], 1)
        if charge >= 1:
            crackle(f.g, tip[0], tip[1], ph, r=2 + charge, seed=5)
    return e


def caller(dx=0.0, dy=0.0, lean=0.0, sway=0.0, staff_a=-92.0, staff_x=7.0, staff_h=0.0, shand=None, bhand=(-5.0, -10.0),
           orb=0.0, ph=0, charge=1, eyes="open", hood_dy=0.0, hem=0.0, extra=None, dead=False, staff_on=True):
    f = Fr()
    # robe: a flared bell of storm cloth, hem rippling
    top = -14.6 + dy
    hem_y = 0
    L = [(-2.8 + dx + lean * 0.12, top), (2.8 + dx + lean * 0.12, top + 0.4)]
    hem_pts = []
    for k in range(9):
        x = -6.2 + k * 1.55 + dx + sway * (k / 8.0)
        y = hem_y - (0.0 if k % 2 == 0 else 0.8) * (1 if hem >= 0 else 0) - (abs(math.sin(k + hem)) * 0.8)
        hem_pts.append((x, y))
    def robe_shade(X, Y):
        u = (X - dx) / 6.0
        v = (Y - top) / (hem_y - top + 0.01)
        l = -u * 0.7 - v * 0.2 + 0.3
        if (X - dx + int(v * 3)) % 4 == 0 and v > 0.35: l -= 0.45          # deep folds
        return pick(CLOTH, l)
    poly(f.b, [L[0], L[1], (6.6 + dx + sway, -1.0), *reversed(hem_pts), (-6.4 + dx + sway * 0.5, -1.0)], "N", shade=robe_shade)
    # iron hem trim + belt with a coil buckle
    for (x, y) in hem_pts:
        f.b.put(*P(x, y), "3")
    line(f.b, dx - 4.0, -9.0 + dy, dx + 4.0 + sway * 0.3, -8.6 + dy, "2")
    f.b.put(*P(dx + 0.5, -8.8 + dy), "e"); f.b.put(*P(dx + 1.5, -8.8 + dy), "Q")
    # back arm (open palm gathering charge)
    shb = (dx - 2.0 + lean * 0.12, top + 1.5)
    hb = (dx + bhand[0], dy + bhand[1])
    eb, _ = ik(shb[0], shb[1], hb[0], hb[1], 4.0, 4.0, bend=-1)
    tube(f.u, [shb, eb, hb], [1.5, 1.3, 1.1], CLOTH, bias=0.0)
    f.u.put(*P(*hb), "h")
    # hood
    hx, hy = dx + 0.8 + lean * 0.15, -17.6 + dy + hood_dy
    def hood(c):
        ell(c, hx, hy, 3.4, 3.5, COPPER, bias=-0.1)                                            # v0.9: copper shell hood
        poly(c, [(hx - 2.6, hy - 2.6), (hx - 0.2, hy - 4.6), (hx + 0.8, hy - 2.8)], "Q")       # point of the hood
        line(c, hx - 0.6, hy - 4.2, hx - 2.4, hy + 2.6, "q")                                  # the shell's split seam
        for (a_, b_) in ((-2.6, -0.6), (-2.0, 1.4)): c.put(*P(hx + a_, hy + b_), "5")          # rivets
        ell(c, hx + 1.6, hy + 0.6, 1.8, 2.2, "1112", bias=-0.2)                             # the dark face opening
        line(c, hx - 2.6, hy + 2.6, hx + 2.8, hy + 2.8, "3")                                 # iron circlet at the collar
    stamp(f.b, hood, ch="1")
    # v0.9 lineage (Spark Beetle): the beetle's split copper wing-case worn as a mantle over the shoulders, and its coil
    # antennae rising from the hood (the hood itself is copper shell)
    stamp(f.b, lambda c: elytra(c, dx - 0.6 + lean * 0.12, top + 2.0, 5.4, 2.4), ch="1")
    coil_antennae(f.b, f.g, hx - 1.6, hy - 2.6, ang=-140, L=4.0, spread=26, lit=not dead)
    # staff hand
    shf = (dx + 2.2 + lean * 0.12, top + 1.5)
    sx, sy = dx + staff_x, -1.0 + staff_h + dy * 0.3
    if shand is None:
        shand = polar(sx, sy, 11.0, staff_a)
    e = None
    if staff_on:
        e = staff(f, sx, sy, staff_a, L=19.5, ph=ph, charge=charge, cage=False)
    ef, _ = ik(shf[0], shf[1], shand[0], shand[1], 4.0, 4.0, bend=1)
    def farm(c):
        tube(c, [shf, ef, shand], [1.6, 1.4, 1.2], CLOTH, bias=0.3)
        c.put(*P(*shand), "h")
    stamp(f.b, farm, ch="1")
    # ball lightning in the open hand
    if orb > 0:
        r = orb
        for y in range(int(hb[1] - r) - 1, int(hb[1] + r) + 2):
            for x in range(int(hb[0] - r) - 1, int(hb[0] + r) + 2):
                d = math.hypot(x - hb[0], y - hb[1] + 1) / r
                if d <= 1: f.g.put(x, y, "0" if d < 0.5 else "9" if d < 0.85 else "8")
        crackle(f.g, hb[0], hb[1] - 1, ph, r=r + 2, seed=9)
    # eyes in the hood's shadow
    ex, ey = hx + 1.6, hy + 0.2
    if eyes == "open":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1.6, ey), "9")
    elif eyes == "wide":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1.6, ey), "0"); f.g.put(*P(ex, ey - 1), "9"); f.g.put(*P(ex + 1.6, ey - 1), "9")
    elif eyes == "dead":
        f.g.put(*P(ex, ey), "2"); f.g.put(*P(ex + 1.6, ey), "2")
    if extra: extra(f, e, hb)
    return f.done()


def caller_corpse():
    f = Fr()
    poly(f.b, [(-9, 0), (-6, -3.6), (3, -4.2), (7, -2.4), (8, 0)], "N", shade=lambda X, Y: "v" if Y < -3 else "N" if X < 2 else "n")
    ell(f.b, 7.6, -2.2, 2.6, 2.2, CLOTH, bias=0.1)
    for k in range(6):
        f.b.put(-5 + k * 2, 0, "3")
    line(f.b, -14, -1, 6, -1 if False else 0, "3")
    f.b.put(-14, -1, "e"); f.b.put(-13, -1, "Q")
    return f.done()


def build_caller(outdir):
    C = caller
    idle = [C(ph=0, hem=0.0), C(ph=1, dy=0.3, hem=0.8, sway=0.4, bhand=(-5.2, -9.6)),
            C(ph=2, dy=0.4, hem=1.6, sway=0.6, bhand=(-5.3, -9.4), charge=1), C(ph=3, dy=0.1, hem=2.4, sway=0.2)]
    run = [C(dx=0.5, lean=8, ph=4 + i, hem=i * 1.1, sway=-1.2 - 0.6 * math.sin(i * math.pi / 3), dy=-0.5 * abs(math.sin(i * math.pi / 3)),
             staff_a=-70, staff_x=4.0, staff_h=-2.5, bhand=(-6.0, -9.0)) for i in range(6)]
    # ORB: draw the hand back, gather ball lightning, THRUST (3: release at the palm), follow-through
    orb = [C(ph=10, bhand=(-6.5, -11.0), orb=1.0, eyes="open"),
           C(ph=11, bhand=(-7.5, -12.0), orb=1.8, eyes="wide", lean=-4, charge=2),
           C(ph=12, bhand=(-6.5, -14.0), orb=2.4, eyes="wide", lean=-6, charge=2, hood_dy=0.3),
           C(ph=13, bhand=(9.0, -13.0), orb=0, eyes="wide", lean=8, dx=0.6, sway=-1.0,
             extra=lambda f, e, hb: (spark(f.g, hb[0] + 2, hb[1] - 1, 2), f.g.put(*P(hb[0] - 3, hb[1] - 3), "9"),
                                     f.g.put(*P(hb[0] - 5, hb[1]), "8"), f.g.put(*P(hb[0] + 5, hb[1] - 1), "9"))),
           C(ph=14, bhand=(7.0, -11.5), eyes="open", lean=6, dx=0.4),
           C(ph=15, bhand=(-5.0, -10.0), eyes="open")]
    # CALL DOWN: raise the staff, lightning answers the rod (2: strikes called at the hero), hold, lower
    def answered(n):
        def fn(f, e, hb):
            if e is None: return
            bolt(f.g, e[0], e[1] - 2, e[0] + 2, e[1] - 14, seed=n, jag=1.5, step=2.5, fork=4)
            if n > 1: spark(f.g, e[0], e[1] - 1, 2)
        return fn
    call = [C(ph=20, staff_a=-96, staff_h=-1.5, bhand=(-5, -12), eyes="open", charge=1),
            C(ph=21, staff_a=-100, staff_h=-6.0, shand=(6.5, -19.0), bhand=(-6, -15), eyes="wide", charge=2, hood_dy=-0.3),
            C(ph=22, staff_a=-98, staff_h=-8.0, shand=(6.5, -21.0), bhand=(-7, -16), eyes="wide", charge=3, hood_dy=-0.5, extra=answered(2)),
            C(ph=23, staff_a=-97, staff_h=-8.0, shand=(6.5, -21.0), bhand=(-7, -16), eyes="wide", charge=3, hood_dy=-0.5, extra=answered(3)),
            C(ph=24, staff_a=-98, staff_h=-7.5, shand=(6.5, -20.5), bhand=(-7, -15.5), eyes="wide", charge=3, hood_dy=-0.4, extra=answered(1)),
            C(ph=25, staff_a=-97, staff_h=-7.0, shand=(6.5, -20.0), bhand=(-6.5, -15), eyes="wide", charge=2, hood_dy=-0.3),
            C(ph=26, staff_a=-94, staff_h=-3.0, bhand=(-5.5, -12), eyes="open", charge=1),
            C(ph=27, bhand=(-5, -10), eyes="open", charge=1)]
    death = [C(ph=30, lean=-12, staff_a=-120, bhand=(-7, -15), eyes="wide", charge=3, hood_dy=-0.4),
             dim_glow(C(ph=31, lean=-20, dy=2.0, staff_a=-150, staff_x=2, bhand=(-8, -8), eyes="dead", charge=0)),
             dim_glow(grounded(C(ph=32, lean=-34, dy=5.0, staff_on=False, bhand=(-9, -3), eyes="dead", charge=0))),
             dim_glow(caller_corpse())]
    knock = C(ph=33, lean=-12, staff_a=-112, bhand=(-7, -14), eyes="wide", charge=2, hood_dy=-0.3)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.09] * 6),
             ("Orb", orb, [0.12, 0.14, 0.14, 0.06, 0.14, 0.14]),
             ("Call", call, [0.12, 0.14, 0.08, 0.12, 0.12, 0.12, 0.12, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("KrnStormcaller", anims, outdir, scale=6, remap=STORM_CLOTH)


# ================================================================== FORGE COLOSSUS (T3, Anvil Smith line)
def anvil_fist(c, x, y, s=1.0, ang=0.0):
    """A fist cast as an anvil block: flat striking face at the bottom, rivets."""
    w, h = 3.4 * s, 3.0 * s
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def R(u, v): return (x + u * ca - v * sa, y + u * sa + v * ca)
    pts = [R(-w, -h), R(w, -h), R(w + 0.8, h), R(-w - 0.8, h)]
    poly(c, pts, "3", shade=lambda X, Y: "6" if Y <= y - h + 0.6 else ("2" if Y >= y + h - 0.6 else "5" if X < x - w * 0.3 else "4" if X < x + w * 0.5 else "3"))
    c.put(*P(*R(-w * 0.4, -h * 0.2)), "6"); c.put(*P(*R(w * 0.5, -h * 0.2)), "2")


def colossus(dx=0.0, dy=0.0, lean=0.0, feet=((-6, 0), (3, 0)), fist=(13.0, -3.0), bfist=(-11.0, -3.0), arc=1, ph=0,
             furnace=1, eyes="open", head_dy=0.0, rods=True, extra=None, smear=None, dead=False, fist_ang=0.0):
    f = Fr()
    hip = (dx - 1.0, -11.0 + dy)
    # legs: short pillars
    for i, (fx_, fy_) in enumerate(feet):
        c = f.u if i == 0 else f.b
        hx_ = hip[0] + (-3.5 if i == 0 else 3.0)
        tube(c, [(hx_, hip[1]), ((hx_ + fx_) / 2, (hip[1] + fy_) / 2), (fx_, fy_ - 2.0)], [3.4, 3.0, 2.8], IRON, bias=-0.1 if i == 0 else 0.1)
        rect(c, fx_ - 3.2, fy_ - 2.4, fx_ + 3.6, fy_, "2345")
        c.put(*P(fx_ + 2.6, fy_ - 4.0), "o")                       # forge seam at the knee
    # back arm (in the under layer)
    shb = (dx - 6.5 + lean * 0.1, -24.0 + dy)
    eb = ((shb[0] + bfist[0]) / 2 - 2.0, (shb[1] + bfist[1]) / 2 - 1.0)
    tube(f.u, [shb, eb, (bfist[0], bfist[1] - 2.5)], [4.0, 3.2, 2.8], IRON, bias=-0.1)
    anvil_fist(f.u, bfist[0], bfist[1] - 0.5, 0.9)
    # lightning rods rising from the back (drawn behind the torso)
    tips = []
    if rods:
        for k, (bx, ln, a) in enumerate(((-8.0, 11.0, -106.0), (-1.5, 9.5, -80.0))):
            b0 = (dx + bx + lean * 0.15, -26.0 + dy)
            e = polar(b0[0], b0[1], ln, a + lean * 0.4)
            tube(f.u, [b0, e], [1.4, 0.7], IRON_L, bias=0.2)
            col = polar(b0[0], b0[1], ln - 3, a + lean * 0.4)
            f.u.put(*P(*col), "e"); f.u.put(*P(col[0] + 1, col[1]), "Q")
            tips.append(e)
    # torso: a hunched iron hull, riveted shoulder plates
    tc = (dx - 1.5 + lean * 0.1, -20.5 + dy)
    ell(f.b, tc[0], tc[1], 11.0, 9.0, IRON, ang=lean * 0.5, bias=0.25)
    ell(f.b, tc[0] - 3.0, tc[1] - 4.5, 7.5, 4.6, IRON_L, ang=-10 + lean * 0.5, bias=0.2, vmax=0.3)         # shoulder hump plate
    for k in range(5):
        x = tc[0] - 8.0 + k * 3.2
        f.b.put(*P(x, tc[1] - 6.5 + abs(k - 2) * 0.9), "6")
    line(f.b, tc[0] - 10.0, tc[1] - 1.5, tc[0] + 2.0, tc[1] - 3.5, "2")
    # v0.8: two copper bands hooped round the hull (accent against the blued steel)
    for off in ():
        for t in range(-8, 9):
            x = tc[0] + off + t * 0.3
            y = tc[1] + t
            if (x - tc[0]) ** 2 / 121 + (y - tc[1]) ** 2 / 81 < 0.9:
                f.b.put(*P(x, y), "E" if t < 0 else "e")
                f.b.put(*P(x + 1, y), "e" if t < 2 else "Q")
    # v0.9 lineage (Leyden Golem): a Leyden jar of dark glass set into the chest, copper-banded, lightning coiled inside
    # (furnace = charge level); (Anvil Smith): the smith's leather apron hangs below it and the fists are anvils
    gx, gy = tc[0] - 3.4, tc[1] + 0.5
    def jar_shade(nu, nv, d, l, ch, x, y):
        if d > 0.72: return "V" if (nu + nv) < -0.4 else ("v" if (nu + nv) < 0.5 else "N")
        if d > 0.55 and (nu + nv) < -0.6: return "W"
        return "n"
    # v0.10 (one parent, the Anvil Smith): a forge furnace mouth in the chest instead of the jar: an iron frame, a
    # barred grate, coals glowing behind it (brighter with the furnace level)
    rect(f.b, gx - 4.4, gy - 4.6, gx + 4.4, gy + 4.4, "2345")
    for y in range(int(gy - 3.6), int(gy + 3.6) + 1):
        for x in range(int(gx - 3.4), int(gx + 3.4) + 1):
            f.b.put(x, y, "1")
            if not dead:
                hot = (y - gy) > -1 or (x + y + ph) % 3 == 0
                if hot: f.g.put(x, y, ("Y" if furnace >= 2 else "O") if (y - gy) > 1 else ("O" if (x + ph) % 2 else "o"))
    for x in range(int(gx - 3.4), int(gx + 3.4) + 1, 2):
        for y in range(int(gy - 3.6), int(gy + 3.6) + 1):
            f.g.put(x, y, "2")
    rect(f.b, gx - 2.0, gy - 6.2, gx + 2.0, gy - 4.8, "2345")
    apron = [(tc[0] - 2.0, tc[1] + 6.0), (tc[0] + 8.6, tc[1] + 5.0), (tc[0] + 8.0, tc[1] + 12.0), (tc[0] - 1.0, tc[1] + 12.6)]
    poly(f.b, apron, "T", shade=lambda X, Y: "t" if X > tc[0] + 6.4 or Y > tc[1] + 11.2 else "T")
    line(f.b, tc[0] - 2.0, tc[1] + 6.0, tc[0] + 8.6, tc[1] + 5.0, "h")
    # head sunk between the shoulders: iron helm, visor slit
    hx, hy = tc[0] + 9.0 + lean * 0.12, tc[1] - 7.5 + head_dy
    def head(c):
        ell(c, hx, hy, 3.2, 3.0, COPPER, bias=0.25)          # v0.10: the Smith's copper skullcap, grown into a helm
        line(c, hx - 2.6, hy + 1.6, hx + 3.0, hy + 1.2, "q")
        c.put(*P(hx - 1.0, hy - 2.0), "E")
        for ox in (-1.8, 0.8):
            c.put(*P(hx + ox, hy - 3.2), "e"); c.put(*P(hx + ox, hy - 4.2), "E")
    stamp(f.b, head, ch="1")
    # v0.10 lineage (Anvil Smith): the smith's forge heat: red-hot seams split the hull plates and glow at the joints
    if not dead:
        heat = "Y" if furnace >= 2 else "O"
        for (x0, y0, x1, y1) in ((-9.0, -5.0, -5.0, -1.0), (-6.0, 2.0, -1.0, 5.0), (0.0, -8.0, 3.0, -5.0), (-10.0, 1.0, -8.0, 5.0)):
            pts = line_px(*P(tc[0] + x0, tc[1] + y0), *P(tc[0] + x1, tc[1] + y1))
            for i_, (x_, y_) in enumerate(pts):
                if (x_, y_) in f.b.px: f.g.put(x_, y_, heat if i_ % 3 == 1 else ("O" if heat == "Y" else "o"))
    # front arm + anvil fist
    sh = (tc[0] + 3.0, tc[1] - 3.5)
    fe = ((sh[0] + fist[0]) / 2 + 2.5, (sh[1] + fist[1]) / 2 - 2.0)
    def farm(c):
        tube(c, [sh, fe, (fist[0], fist[1] - 2.8)], [4.4, 3.4, 3.0], IRON_L, bias=0.15)
        anvil_fist(c, fist[0], fist[1] - 0.6, 1.05, fist_ang)
        # riveted cuff
        cm = ((fe[0] + fist[0]) / 2, (fe[1] + fist[1]) / 2 - 1)
        c.put(*P(cm[0] - 1, cm[1]), "6"); c.put(*P(cm[0] + 1, cm[1] + 1), "5")
    stamp(f.b, farm, ch="1")
    f.g.put(*P(fe[0] + 0.5, fe[1] + 0.5), "o"); f.g.put(*P(fe[0] + 1.5, fe[1] + 0.5), "O")       # elbow seam
    if not dead:   # v0.10: the anvil fist's striking face glows hot, like the Smith's hammer
        for k in range(-3, 4):
            f.g.put(*P(fist[0] + k, fist[1] + 1.6), "O" if abs(k) < 2 else "o")
    # visor
    if eyes == "open":
        line(f.g, hx + 0.4, hy - 0.2, hx + 2.8, hy - 0.4, "90")
    elif eyes == "wide":
        line(f.g, hx, hy - 0.4, hx + 3.4, hy - 0.6, "0"); f.g.put(*P(hx + 4.2, hy - 0.6), "9")
    elif eyes == "dead":
        line(f.g, hx + 0.4, hy - 0.2, hx + 2.8, hy - 0.4, "2")
    # the arc between the rods
    if rods and arc and not dead:
        bolt(f.g, tips[0][0], tips[0][1], tips[1][0], tips[1][1], seed=ph, jag=1.6 + arc * 0.5, step=2.5, halo="7" if arc < 2 else "8",
             fork=2.0 * arc)
        for t in tips: f.g.put(*P(*t), "0")
        if arc >= 2:
            for t in tips: spark(f.g, t[0], t[1], 1)
    if smear:
        for (x0, y0, x1, y1) in smear:
            line(f.g, x0, y0, x1, y1, "98")
    if extra: extra(f, tips, tc)
    return f.done()


def colossus_corpse():
    f = Fr()
    ell(f.b, -2, -5.0, 13.0, 5.0, IRON_L, bias=0.0)
    ell(f.b, -5, -8.0, 7.0, 3.0, IRON_HI, bias=0.15, vmax=0.2)
    rect(f.b, 3, -7, 8, -2, "1234")
    for x in (4, 6): f.b.put(x, -5, "a"); f.b.put(x, -4, "t")
    anvil_fist(f.b, 15, -2.4, 1.0)
    anvil_fist(f.b, -17, -2.4, 0.9)
    ell(f.b, 11.0, -4.5, 3.0, 2.6, IRON_HI)
    # snapped rods
    line(f.b, -9, -9, -15, -13, "3"); line(f.b, -2, -9, 1, -14, "3")
    f.b.put(1, -14, "e"); f.b.put(-15, -13, "e")
    f.g.put(12, -5, "2"); f.g.put(13, -5, "2")
    return f.done()


def build_colossus(outdir):
    K = colossus
    idle = [K(ph=0, arc=1), K(ph=1, dy=0.5, arc=1, fist=(13, -3), furnace=2, head_dy=0.4),
            K(ph=2, dy=0.7, arc=2, fist=(13, -3), furnace=2, head_dy=0.5), K(ph=3, dy=0.2, arc=1, furnace=1)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        sn, cs = math.sin(ph), math.cos(ph)
        run.append(K(dx=0.8, dy=-1.0 * abs(cs), lean=6, ph=i + 4, arc=1 + (i % 2),
                     feet=((-6 - 3.4 * sn, -1.4 * max(0, -cs)), (3 + 3.4 * sn, -1.4 * max(0, cs))),
                     fist=(13 - 4 * sn, -3 - 2.0 * max(0, sn)), bfist=(-11 + 4 * sn, -3 - 2.0 * max(0, -sn))))
    # SLAM: rear up, fists high, smear down, IMPACT (4: quake ring at (18, 0)), hold, push up, recover
    def impact(n):
        def fn(f, tips, tc):
            for k, (a, b) in enumerate(((22, -3), (12, -4), (25, -6), (16, -8), (9, -2), (28, -1))[:n]):
                f.g.put(a, b, "0" if k < 3 else "9")
            line(f.g, 8, 0, 28, 0, "0998")
            if n >= 4:
                bolt(f.g, 18, -2, 30, -3, seed=11, jag=1.2, step=2.0)
                bolt(f.g, 16, -2, 6, -4, seed=12, jag=1.2, step=2.0)
        return fn
    slam = [K(ph=10, dy=0.8, lean=-4, fist=(11, -10), bfist=(-12, -8), eyes="open", head_dy=0.4, furnace=2),
            K(ph=11, dy=-0.6, lean=-12, fist=(4, -36), bfist=(-6, -34), eyes="wide", furnace=2, arc=2, fist_ang=-20),
            K(ph=12, dy=-1.0, lean=-14, fist=(6, -38), bfist=(-4, -36), eyes="wide", furnace=2, arc=2, fist_ang=-25),
            K(ph=13, dx=1.0, dy=0.0, lean=6, fist=(16, -16), bfist=(8, -18), eyes="wide", furnace=2, arc=2,
              smear=[(10, -34, 18, -22), (6, -32, 14, -20)]),
            K(ph=14, dx=2.0, dy=1.6, lean=14, fist=(19, -2), bfist=(13, -2), eyes="wide", furnace=2, arc=2, extra=impact(6),
              feet=((-7, 0), (4, 0))),
            K(ph=15, dx=2.0, dy=1.4, lean=13, fist=(19, -2), bfist=(13, -2), eyes="open", furnace=1, arc=1, extra=impact(2),
              feet=((-7, 0), (4, 0))),
            K(ph=16, dx=1.0, dy=0.6, lean=6, fist=(16, -5), bfist=(-2, -6), eyes="open", furnace=1),
            K(ph=17, dy=0.2, fist=(13, -3), bfist=(-11, -3), eyes="open")]
    # ROD CAGE: crouch, rear up arms wide, the rods overload (3), smear, IMPACT both fists (5: rods burst up in a ring), recover
    def overload(f, tips, tc):
        for t in tips:
            bolt(f.g, t[0], t[1], t[0] + random.Random(int(t[0])).uniform(-6, 6), t[1] - 9, seed=int(t[1]), jag=1.4, step=2.5)
    cage = [K(ph=20, dy=1.2, lean=4, fist=(9, -3), bfist=(-9, -3), eyes="open", head_dy=0.6, furnace=2),
            K(ph=21, dy=-0.8, lean=-10, fist=(16, -28), bfist=(-16, -26), eyes="wide", furnace=2, arc=2),
            K(ph=22, dy=-1.4, lean=-12, fist=(17, -32), bfist=(-17, -30), eyes="wide", furnace=2, arc=2, extra=overload),
            K(ph=23, dy=-1.4, lean=-12, fist=(17, -32), bfist=(-17, -30), eyes="wide", furnace=2, arc=2, extra=overload),
            K(ph=24, dy=0.0, lean=2, fist=(12, -14), bfist=(-10, -14), eyes="wide", furnace=2, arc=2,
              smear=[(17, -30, 13, -18), (-17, -28, -11, -17)]),
            K(ph=25, dy=1.8, lean=4, fist=(9, -2), bfist=(-9, -2), eyes="wide", furnace=2, arc=2,
              extra=lambda f, t, tc: (line(f.g, -18, 0, 20, 0, "09"), spark(f.g, 9, -3, 2), spark(f.g, -9, -3, 2))),
            K(ph=26, dy=1.6, lean=4, fist=(9, -2), bfist=(-9, -2), eyes="open", furnace=1, arc=1),
            K(ph=27, dy=0.8, lean=2, fist=(11, -3), bfist=(-10, -3), eyes="open"),
            K(ph=28, dy=0.2, fist=(13, -3), bfist=(-11, -3), eyes="open")]
    death = [K(ph=30, dx=-1, lean=-14, fist=(10, -20), bfist=(-14, -18), eyes="wide", arc=2, furnace=2),
             dim_glow(K(ph=31, dx=-1, dy=3.0, lean=-24, fist=(12, -6), bfist=(-15, -4), eyes="dead", arc=0, furnace=0, dead=True)),
             dim_glow(grounded(K(ph=32, dx=-1, dy=8.0, lean=-34, fist=(14, -2), bfist=(-16, -2), eyes="dead", arc=0, furnace=0,
                                 dead=True, rods=False))),
             dim_glow(colossus_corpse())]
    knock = K(ph=33, dx=-1, lean=-12, fist=(10, -16), bfist=(-14, -14), eyes="wide", arc=2, furnace=2)
    anims = [("Idle", idle, [0.26, 0.2, 0.26, 0.2]), ("Run", run, [0.1] * 6),
             ("Slam", slam, [0.16, 0.16, 0.14, 0.06, 0.08, 0.2, 0.16, 0.16]),
             ("Cage", cage, [0.14, 0.16, 0.14, 0.12, 0.06, 0.1, 0.2, 0.16, 0.16])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.45], knock)
    sheet("KrnForgeColossus", anims, outdir, scale=5, remap=FORGE_IRON)


# ================================================================== STORM HERALD (T3, Stormcaller line, flying)
def cloud_puff(c, x, y, r, seed=0, ramp=CLOUD, bias=0.0):
    rnd = random.Random(seed)
    for k in range(4):
        ell(c, x + rnd.uniform(-r, r) * 0.8, y + rnd.uniform(-r, r) * 0.3, r * rnd.uniform(0.55, 0.8), r * rnd.uniform(0.45, 0.65), ramp,
            bias=bias)


def herald(dx=0.0, dy=0.0, lean=0.0, lance=(-70.0, 6.0, -14.0), bhand=(-6.0, -20.0), wings=0.0, halo=1, ph=0, eyes="open",
           cloak=0.0, extra=None, dead=False, lance_on=True, head_dy=0.0, hover=4.0):
    f = Fr()
    base = -hover + dy
    # storm-cloud skirt: churning puffs trailing behind, a few rain/spark specks under it
    skirt = Canvas()
    for k in range(5):
        cloud_puff(skirt, dx + 1.5 - k * 2.4 + math.sin(cloak + k) * 0.8, base - 1.8 - k * 1.2, 3.4 - k * 0.35, seed=ph * 7 + k,
                   bias=0.1 - k * 0.12)
    if not dead:
        for k in range(3):
            x = dx - 3 + k * 3 + (ph % 2)
            f.g.put(*P(x, base + 1 + (k + ph) % 2), "8" if k % 2 else "7")
    # conductor-rod wings: three thin iron rods fanned behind each shoulder, tips sparking
    shc = (dx - 1.0 + lean * 0.2, -25.0 + dy)
    wtips = []
    for sd, layer in ((-1, f.n), (1, f.u)):
        for k in range(3):
            a = -90 - sd * (22 + k * 24) - wings * sd * 0.6 - (14 if sd < 0 else 0)
            L = 12.5 - k * 1.6
            b0 = (shc[0] - (1 if sd < 0 else 0), shc[1])
            e = polar(b0[0], b0[1], L, a)
            line(layer, b0[0], b0[1], e[0], e[1], "3" if sd < 0 else "4")
            m = polar(b0[0], b0[1], L * 0.6, a)
            layer.put(*P(*m), "e")
            wtips.append(e)
    # robe body: long, narrow, dark storm cloth, falling into the cloud skirt
    def body_shade(X, Y):
        u = (X - dx) / 5.0
        l = -u * 0.8 + 0.2 - (0.4 if (X + int(Y * 0.3)) % 4 == 0 and Y > -16 + dy else 0)
        return pick(CLOTH, l)
    poly(f.b, [(dx - 3.0 + lean * 0.2, -27.0 + dy), (dx + 3.4 + lean * 0.2, -27.0 + dy), (dx + 4.6, base - 3.0),
               (dx + 1.0, base - 0.5), (dx - 5.0, base - 2.0)], "N", shade=body_shade)
    for (x, y), v in skirt.px.items(): f.b.put(x, y, v)
    # iron cuirass with a glowing core seam
    poly(f.b, [(dx - 2.8 + lean * 0.2, -27.0 + dy), (dx + 3.4 + lean * 0.2, -27.0 + dy), (dx + 3.0 + lean * 0.15, -19.0 + dy),
               (dx - 2.0 + lean * 0.15, -18.5 + dy)], "4",
         shade=lambda X, Y: "6" if Y <= -26 + dy else ("5" if X < dx + lean * 0.2 else "3"))
    for k in range(6):
        f.g.put(*P(dx + 0.8 + lean * 0.18, -25.5 + dy + k * 1.2), "9" if (k + ph) % 3 else "0")
    line(f.b, dx - 2.4, -18.8 + dy, dx + 3.2, -19.2 + dy, "2")
    # head: smooth iron mask, tall collar
    hx, hy = dx + 1.4 + lean * 0.25, -30.6 + dy + head_dy
    def head(c):
        ell(c, hx, hy, 2.5, 2.9, IRON_HI, bias=0.45)
        line(c, hx - 0.2, hy - 0.2, hx + 2.6, hy - 0.2, "1")
        poly(c, [(hx - 2.8, hy + 1.2), (hx + 2.6, hy + 1.6), (hx + 2.0, hy + 3.4), (hx - 2.4, hy + 3.4)], "3")   # collar
        c.put(*P(hx - 1.0, hy - 1.6), "6")
    stamp(f.b, head, ch="1")
    # v0.9 lineage (Lodestone Hound): the hound's horseshoe magnet mounted behind the mask, poles up; the lightning halo
    # now arcs between its poles. (Stormcaller: the same storm-blue robe, copper antennae and cloud skirt.)
    # v0.10 (one parent, the Stormcaller): the caller's copper beetle-shell hood grown into a split crest behind the
    # mask, with its coil antennae swept up through the halo
    def crest(c):
        for sd in (-1, 1):
            ell(c, hx - 1.6 + sd * 1.6, hy - 2.0, 2.0, 3.6, COPPER, ang=sd * 22, bias=0.2)
        line(c, hx - 1.6, hy - 5.2, hx - 1.6, hy + 0.6, "q")
    stamp(f.u, crest, ch="1")
    coil_antennae(f.b, f.g, hx - 1.2, hy - 3.0, ang=-110, L=5.0, spread=34, lit=not dead)
    # halo: a jagged ring of lightning crowning the mask
    if halo and not dead:
        rr = 4.2 + (halo - 1) * 1.6
        rnd = random.Random(ph * 13)
        prev = None
        for k in range(17):
            a = 2 * math.pi * k / 16
            r = rr + rnd.uniform(-0.6, 0.6)
            pt = (hx - 0.4 + math.cos(a) * r, hy - 4.6 + math.sin(a) * r * 0.42)
            if prev:
                for (x, y) in line_px(*P(*prev), *P(*pt)):
                    f.g.put(x, y, "0" if (k + ph) % 3 else "9")
            prev = pt
        if halo >= 2:
            for k in range(3):
                a = rnd.uniform(0, 6.28)
                spark(f.g, hx + math.cos(a) * rr, hy - 4.6 + math.sin(a) * rr * 0.42, 1)
    # back arm (thin sleeve) and front arm holding the lance
    shb = (dx - 2.0 + lean * 0.2, -26.0 + dy)
    hb = (dx + bhand[0], dy + bhand[1])
    eb, _ = ik(shb[0], shb[1], hb[0], hb[1], 5.0, 5.0, bend=-1)
    tube(f.u, [shb, eb, hb], [1.3, 1.1, 0.9], CLOTH, bias=0.0)
    f.u.put(*P(*hb), "5")
    la, lx, ly = lance
    shf = (dx + 2.6 + lean * 0.2, -26.0 + dy)
    grip = (dx + lx, dy + ly)
    tip = None
    if lance_on:
        butt = polar(grip[0], grip[1], -12.0, la)
        tip = polar(grip[0], grip[1], 15.0, la)
        def lance_px(c):
            pts = line(c, butt[0], butt[1], tip[0], tip[1], "4")
            for i, (x, y) in enumerate(pts):
                if i % 4 == 0: c.put(x, y, "6")
            # spearhead: a forked rod head
            for sd in (-1, 1):
                q = polar(tip[0], tip[1], -2.5, la)
                q2 = polar(q[0], q[1], 1.6, la + sd * 90)
                line(c, q2[0], q2[1], tip[0], tip[1], "5")
            cp = polar(grip[0], grip[1], 9.0, la)
            c.put(*P(*cp), "e"); c.put(*P(*polar(cp[0], cp[1], 1, la)), "Q")
        stamp(f.b, lance_px, ch="1", sides=((1, 0), (-1, 0), (0, 1)))
        f.g.put(*P(*tip), "0")
    ef, _ = ik(shf[0], shf[1], grip[0], grip[1], 5.0, 5.0, bend=1)
    def farm(c):
        tube(c, [shf, ef, grip], [1.4, 1.2, 1.0], CLOTH, bias=0.35)
        c.put(*P(*grip), "5")
    stamp(f.b, farm, ch="1")
    # eyes: two cold slits in the mask
    ex, ey = hx + 1.0, hy - 0.2
    if eyes == "open":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1.4, ey), "9")
    elif eyes == "wide":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1.4, ey), "0"); f.g.put(*P(ex, ey + 1), "9")
    elif eyes == "dead":
        f.g.put(*P(ex, ey), "2"); f.g.put(*P(ex + 1.4, ey), "2")
    if not dead:
        for t in wtips[3:]: f.g.put(*P(*t), "9")
    if extra: extra(f, tip, (hx, hy), hb)
    return f.done()


def herald_corpse():
    f = Fr()
    cloud_puff(f.n, -6, -2.0, 3.0, seed=4, bias=-0.3)
    poly(f.b, [(-12, 0), (-8, -3.4), (6, -4.0), (9, -2.0), (9, 0)], "N", shade=lambda X, Y: "v" if Y < -3 else "N" if X < 2 else "n")
    poly(f.b, [(-2, -4.0), (5, -4.2), (5, -1.0), (-2, -1.0)], "4", shade=lambda X, Y: "5" if Y < -3 else "3")
    ell(f.b, 10.5, -2.6, 2.6, 2.4, IRON_HI, bias=0.2)
    line(f.b, -18, 0, 2, -1, "4"); f.b.put(-18, 0, "5")
    for k in range(3):
        line(f.b, -6 + k * 2, -4, -9 + k * 3, -9, "3")
    return f.done()


def build_herald(outdir):
    H = herald
    idle = [H(ph=0, dy=0.0, wings=0, cloak=0.0), H(ph=1, dy=-0.7, wings=6, cloak=0.8, lance=(-70, 6.0, -14.5)),
            H(ph=2, dy=-1.0, wings=10, cloak=1.6, lance=(-70, 6.0, -15.0), halo=2), H(ph=3, dy=-0.4, wings=4, cloak=2.4)]
    run = [H(dx=0.6, lean=10, ph=4 + i, dy=[-0.3, -0.9, -1.2, -0.8, -0.2, 0.0][i], wings=[0, 10, 18, 10, 2, 0][i], cloak=i * 1.0,
             lance=(-30, 7.0, -16.0), bhand=(-8.0, -19.0)) for i in range(6)]
    # LANCE: draw the lance back, coil, THRUST (3: a lightning lance flies from the tip), hold, recover
    def thrust_fx(f, tip, head, hb):
        if tip is None: return
        bolt(f.g, tip[0], tip[1], tip[0] + 8, tip[1] - 0.5, seed=5, jag=0.8, step=2.0)
        spark(f.g, tip[0] + 1, tip[1], 2)
    lance = [H(ph=10, lean=-4, lance=(-10, 1.0, -17.0), bhand=(-7, -21), eyes="open", wings=-6),
             H(ph=11, lean=-10, lance=(-6, -3.0, -18.0), bhand=(-8, -22), eyes="wide", wings=-14, halo=2),
             H(ph=12, lean=8, dx=1.0, lance=(-2, 8.0, -18.5), bhand=(-9, -20), eyes="wide", wings=16, halo=2,
               extra=lambda f, tip, h, hb: [line(f.g, tip[0] - 14 - k * 2, tip[1] + 2 * k - 1, tip[0] - 9 - k * 2, tip[1] + 2 * k - 1, "8") for k in range(2)]),
             H(ph=13, lean=12, dx=1.6, lance=(-1, 11.0, -18.5), bhand=(-9, -19), eyes="wide", wings=20, halo=2, extra=thrust_fx),
             H(ph=14, lean=10, dx=1.4, lance=(-2, 10.0, -18.0), bhand=(-8, -19), eyes="open", wings=12),
             H(ph=15, lean=4, dx=0.6, lance=(-40, 7.0, -16.0), bhand=(-7, -20), eyes="open", wings=4),
             H(ph=16, lance=(-70, 6.0, -14.0), eyes="open")]
    # THUNDERHEAD: lance raised to the sky, halo swells, a bolt goes up (4: the storm cloud forms over the hero), recover
    def skyward(n):
        def fn(f, tip, head, hb):
            if tip is None: return
            bolt(f.g, tip[0], tip[1], tip[0] + 1, tip[1] - 14, seed=n, jag=1.6, step=2.5, fork=4)
            if n > 1: spark(f.g, tip[0], tip[1] - 1, 2)
        return fn
    thunder = [H(ph=20, lance=(-80, 5.0, -18.0), bhand=(-7, -24), eyes="open", wings=8),
               H(ph=21, lance=(-86, 4.0, -24.0), bhand=(-8, -30), eyes="wide", wings=18, halo=2, dy=-1.0),
               H(ph=22, lance=(-88, 4.0, -27.0), bhand=(-8, -33), eyes="wide", wings=26, halo=3, dy=-2.0),
               H(ph=23, lance=(-88, 4.0, -27.0), bhand=(-8, -33), eyes="wide", wings=28, halo=3, dy=-2.0, extra=skyward(1)),
               H(ph=24, lance=(-88, 4.0, -27.0), bhand=(-8, -33), eyes="wide", wings=30, halo=3, dy=-2.0, extra=skyward(3)),
               H(ph=25, lance=(-86, 4.0, -25.0), bhand=(-8, -30), eyes="wide", wings=20, halo=2, dy=-1.4, extra=skyward(2)),
               H(ph=26, lance=(-78, 5.0, -18.0), bhand=(-7, -24), eyes="open", wings=10, dy=-0.6),
               H(ph=27, eyes="open")]
    death = [H(ph=30, lean=-12, lance=(-120, 2.0, -18.0), bhand=(-9, -26), eyes="wide", halo=3, wings=30),
             dim_glow(H(ph=31, lean=-20, dy=2.0, lance=(-150, 0.0, -12.0), bhand=(-9, -16), eyes="dead", halo=0, dead=True, wings=40)),
             dim_glow(grounded(H(ph=32, lean=-30, dy=6.0, lance_on=False, bhand=(-10, -8), eyes="dead", halo=0, dead=True, wings=50, hover=0))),
             dim_glow(herald_corpse())]
    knock = H(ph=33, lean=-12, lance=(-110, 2.0, -16.0), bhand=(-9, -24), eyes="wide", halo=2, wings=20)
    anims = [("Idle", idle, [0.2, 0.2, 0.2, 0.2]), ("Run", run, [0.09] * 6),
             ("Lance", lance, [0.14, 0.14, 0.06, 0.08, 0.14, 0.14, 0.14]),
             ("Thunder", thunder, [0.14, 0.14, 0.12, 0.1, 0.12, 0.12, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.45], knock)
    sheet("KrnStormHerald", anims, outdir, scale=5, remap=HERALD)


# ================================================================== FX
FX_NOTES = {}


def fx_center(name, anims, w, h, outdir, note, scale=8):
    """Projectile-style sheet: art drawn around (0,0), which is the exact cell centre (vanilla projectiles are MidCenter)."""
    FX_NOTES[name] = note
    fx_fixed(name, anims, outdir, (w, h), (w // 2, h // 2), scale=scale, note=note)


def fx_ground(name, anims, w, h, below, outdir, note, scale=8):
    """Ground sheet: art drawn around (0,0) = the effect's ground point; `below` rows of the cell lie under it
    (the C# side shifts the BotCenter sprite down by that many pixels)."""
    FX_NOTES[name] = note + (" Origin is %d px above the cell bottom: sprite offset y = -%d." % (below, below) if below else "")
    fx_fixed(name, anims, outdir, (w, h), (w // 2, h - 1 - below), scale=scale, note=note)


def fx_spark():
    out = []
    for i in range(4):
        c = cv()
        bolt(c, -5, 0, 2, 0, seed=i, jag=1.0, step=1.6, halo="8")
        spark(c, 2, 0, 1)
        c.put(3 + (i % 2), -1 + (i % 3) - 0 if i % 2 else 1, "9")
        c.put(-6 - (i % 2), (i % 2) - 1 if i % 3 else 1, "7")
        out.append(c.spr())
    return out


def fx_mote():
    out = []
    for i in range(4):
        c = cv()
        for k in range(4):   # wake
            c.put(-3 - k, round(math.sin(i + k * 1.4) * 0.8), "9" if k < 1 else "8" if k < 3 else "7")
        ell(c, 0, 0, 2.2, 2.2, "8990", bias=0.4)
        c.put(0, 0, "0"); c.put(-1, -1, "0")
        crackle(c, 0, 0, i, r=3, seed=2)
        out.append(c.spr())
    return out


def fx_ball():
    out = []
    for i in range(4):
        c = cv()
        r = [3.6, 3.9, 3.5, 3.8][i]
        for y in range(-6, 7):
            for x in range(-6, 7):
                d = math.hypot(x + 0.4, y + 0.4) / r
                if d <= 1.0:
                    c.put(x, y, "0" if d < 0.4 else "9" if d < 0.75 else "8")
                elif d <= 1.3 and (x + y + i) % 2 == 0:
                    c.put(x, y, "7")
        rnd = random.Random(40 + i)
        for k in range(3):
            a = rnd.uniform(0, 6.28)
            bolt(c, math.cos(a) * r * 0.7, math.sin(a) * r * 0.7, math.cos(a + 0.4) * (r + 3.5), math.sin(a + 0.4) * (r + 3.0),
                 seed=i * 3 + k, jag=0.9, step=1.6, halo=None)
        for k in range(3):
            c.put(-int(r) - 2 - k * 2, (k + i) % 3 - 1, "8" if k < 2 else "7")
        out.append(c.spr())
    return out


def fx_rivet():
    out = []
    for i in range(4):
        c = cv()
        # glowing trail
        for k in range(5):
            c.put(-2 - k, (0 if k < 3 else (i % 2)), "O" if k < 1 else "o" if k < 3 else "a")
        # the rivet, spinning: head + shank orientation changes per frame
        a = i * 90
        hd = [(0, -1), (1, 0), (0, 1), (-1, 0)][i]
        c.put(0, 0, "Y"); c.put(1, 0, "O"); c.put(0, 1, "O"); c.put(1, 1, "o")
        c.put(hd[0] * 2 + (1 if hd[0] > 0 else 0), hd[1] * 2 + (1 if hd[1] > 0 else 0), "5")
        c.put(-1, -1, "y")
        out.append(c.spr())
    return out


def fx_surge():
    out = []
    for i in range(4):
        c = cv()
        # a crawling ridge of sparks and lifted grit, leading edge to the right
        for k in range(5):
            x = 5 - k * 3
            h = [5, 4, 3, 2, 1][k] + (1 if (k + i) % 2 else 0)
            bolt(c, x, 2, x + 1, 2 - h, seed=i * 5 + k, jag=0.7, step=1.5, halo="7" if k < 3 else None)
        line(c, -9, 3, 7, 3, "988")
        c.put(8, 2, "0"); c.put(7, 1 - (i % 2), "9")
        for k in range(3):
            c.put(-6 + k * 4 + (i % 2), 1 - k % 2, "4")      # flying grit
        out.append(c.spr())
    return out


def fx_lance():
    out = []
    for i in range(4):
        c = cv()
        bolt(c, -13, 0, 8, 0, seed=60 + i, jag=1.1, step=2.0, halo="8")
        line(c, -4, 0, 9, 0, "0")
        # forked head
        line(c, 9, 0, 6, -2, "9"); line(c, 9, 0, 6, 2, "9")
        c.put(10, 0, "0")
        for k in range(3):
            c.put(-15 - k * 2 - (i % 2), (k + i) % 3 - 1, "8" if k < 2 else "7")
        out.append(c.spr())
    return out


def stud(ph=0, hot=2, land=0):
    c = cv()
    # a rivet driven into the floor: domed head, a ring of cracked floor
    for x in range(-3, 4):
        c.put(x, 0, "2" if abs(x) > 1 else "1")
    c.put(-1, -1, "4"); c.put(0, -1, "5"); c.put(1, -1, "3")
    c.put(0, -2, "6" if hot < 2 else "Y"); c.put(-1, -2, "4" if hot < 1 else "O")
    if hot >= 1: c.put(1, -2, "o")
    if land:
        for (x, y) in ((-4, -1), (4, -1), (-3, -3), (3, -2)):
            c.put(x, y, "O" if land > 1 else "o")
    base = outl(c.spr(), "Z")
    c = Canvas(); c.px = {k: v for k, v in base.px.items() if k[1] <= 0}
    if ph in (1, 3):
        crackle(c, 0, -3, ph, r=2, seed=4)
    return c.spr()


def rod(rise=1.0, ph=0, lit=True, crack=True):
    c = cv()
    L = int(round(13 * rise))
    if crack:
        for x in range(-3, 4):
            c.put(x, 0, "1" if abs(x) < 2 else "2")
        c.put(-4, 0, "2"); c.put(4, 0, "3")
    if L > 0:
        for y in range(1, L + 1):
            c.put(0, -y, "4" if y % 4 else "6")
            c.put(1, -y, "2")
        if L > 4:
            c.put(-1, -L + 3, "e"); c.put(0, -L + 3, "Q"); c.put(1, -L + 3, "q")   # copper collar
        c.put(-1, -L - 1, "5"); c.put(1, -L - 1, "5"); c.put(0, -L - 1, "4")       # fork
        base = outl(Spr({k: v for k, v in c.px.items() if k[1] < 0}), "Z")
        c.px.update(base.px)
        if lit:
            c.put(0, -L - 2, "0")
            if ph % 2 == 1:
                crackle(c, 0, -L - 2, ph, r=3, seed=7)
    if rise < 1.0 and rise > 0:
        for (x, y) in ((-3, -1), (3, -2), (-2, -3), (2, 0)):
            c.put(x, y, "3")
    return c.spr()


def fx_arc():
    out = []
    for i in range(4):
        c = cv()
        bolt(c, -6, 0, 6, 0, seed=80 + i * 3, jag=1.4, step=2.0, halo="7")
        out.append(c.spr())
    return out


def ring_frames(radii, ry_k, pal, arcs=True, debris=False, seed=0):
    out = []
    for i, r in enumerate(radii):
        c = cv()
        ry = r * ry_k + 1
        n = int(r * 6) + 6
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = r * math.cos(a), ry * math.sin(a)
            if i >= len(radii) - 2 and (k // 3) % 3 == 0: continue
            c.put(*P(x, y), pal[0] if i < len(radii) - 2 else pal[1])
            c.put(*P(x * 0.88, y * 0.82), pal[1] if i < len(radii) - 2 else pal[2], over=False)
        if arcs and i < len(radii) - 1:
            rnd = random.Random(seed + i)
            for k in range(4):
                a = rnd.uniform(0, 6.28)
                x0, y0 = r * math.cos(a), ry * math.sin(a)
                bolt(c, x0, y0, x0 * 1.1, y0 - 3 - rnd.uniform(0, 4), seed=seed + i * 5 + k, jag=0.8, step=1.5, halo=None)
        if debris and 0 < i < len(radii) - 1:
            rnd = random.Random(seed * 3 + i)
            for k in range(6):
                a = rnd.uniform(math.pi, 2 * math.pi)
                d = r * rnd.uniform(0.5, 1.0)
                c.put(*P(d * math.cos(a), ry * math.sin(a) - i * 1.5 - rnd.uniform(0, 3)), "4" if k % 2 else "3")
        if i == 0:
            ell(c, 0, 0, max(2, r * 0.6), max(1, ry * 0.6), "890", bias=0.4)
        out.append(c.spr())
    return out


def strike_frames():
    out = []
    # 0-5 telegraph: a ground mark that tightens and brightens while sparks gather; 6-7 the bolt; 8-9 scorch
    for i in range(6):
        c = cv()
        rx, ry = 8.5 - i * 0.5, 3.2 - i * 0.15
        for y in range(-4, 5):
            for x in range(-10, 11):
                d = (x / rx) ** 2 + (y / ry) ** 2
                if d <= 1.0 and (x + y + i) % 2 == 0 and d > 0.15:
                    c.put(x, y, "7")
        n = 26
        for k in range(n):
            a = 2 * math.pi * k / n
            c.put(*P(rx * math.cos(a), ry * math.sin(a)), "8" if i < 3 else ("9" if (k + i) % 2 else "0"))
        c.put(0, 0, "0" if i % 2 else "9"); c.put(-1, 0, "9"); c.put(1, 0, "9")
        rnd = random.Random(90 + i)
        for k in range(1 + i // 2):
            c.put(*P(rnd.uniform(-5, 5), -rnd.uniform(2, 6 + i * 3)), "9" if i > 3 else "8")
        out.append(c.spr())
    for i in range(2):
        c = cv()
        bolt(c, 1 - i * 2, -56, 0, -1, seed=100 + i, jag=2.4, step=3.0, halo="8", fork=6)
        ell(c, 0, 0, 7 - i, 2.6, "890", bias=0.5)
        for k in range(5):
            a = math.radians(-180 + k * 45)
            c.put(*P(10 * math.cos(a), -1 + 5 * math.sin(a)), "0" if i == 0 else "9")
        out.append(c.spr())
    for i in range(2):
        c = cv()
        ell(c, 0, 0, 6, 2.0, "1223" if i == 0 else "112", bias=0.0)
        c.put(0, -1, "o" if i == 0 else "a"); c.put(1, 0, "a")
        if i == 0:
            for (x, y) in ((-3, -3), (2, -4), (4, -2)): c.put(x, y, "3")
        out.append(c.spr())
    return out


def cloud(ph):
    c = cv()
    cy = -40
    rnd = random.Random(7)
    for k in range(7):
        x = -11 + k * 3.6 + math.sin(ph * 1.57 + k) * 0.8
        y = cy + rnd.uniform(-1.5, 1.5) - (2 if 2 <= k <= 4 else 0)
        ell(c, x, y, 4.2 + rnd.uniform(-0.6, 0.8), 3.0 + rnd.uniform(-0.4, 0.6), CLOUD, bias=-0.05)
    ell(c, 0, cy + 2.6, 12.5, 2.0, "1uuU", bias=-0.4)
    spr = outl(Spr(dict(c.px)), "1")
    c2 = Canvas(); c2.px = dict(spr.px)
    # inner flashes
    if ph % 2 == 0:
        bolt(c2, -6 + ph * 2, cy - 1, -2 + ph * 2, cy + 3, seed=ph, jag=0.8, step=1.5, halo=None)
    else:
        for (x, y) in ((-4 + ph, cy), (3, cy - 2)):
            c2.put(x, y, "W")
    # rain streaks under it
    for k in range(5):
        x = -9 + k * 4 + (ph % 2) * 2
        c2.put(x, cy + 5 + (k + ph) % 3, "7"); c2.put(x - 1, cy + 7 + (k + ph) % 3, "7")
    return c2.spr()


def crackle_fx():
    out = []
    for i in range(4):
        c = cv()
        if i < 3:
            crackle(c, 0, 0, i, r=3 - (i == 2), seed=11)
            c.put(0, 0, "0" if i < 2 else "9")
        else:
            c.put(0, 0, "8"); c.put(1, -1, "7")
        out.append(c.spr())
    return out


def hit_fx():
    out = []
    for i in range(4):
        c = cv()
        if i == 0:
            ell(c, 0, 0, 3, 2.2, "890", bias=0.6)
            spark(c, 0, 0, 3)
        else:
            rnd = random.Random(20)
            for k in range(7):
                a = rnd.uniform(0, 6.28)
                d = 2 + i * 2.4 + rnd.uniform(0, 1.5)
                c.put(*P(math.cos(a) * d, math.sin(a) * d * 0.7), "0" if i == 1 else "9" if i == 2 else "8")
                if i == 1: c.put(*P(math.cos(a) * (d - 1), math.sin(a) * (d - 1) * 0.7), "9")
        out.append(c.spr())
    return out


def plates_fx():
    out = []
    for i in range(6):
        c = cv()
        for k in range(3):
            a = 2 * math.pi * (k / 3.0 + i / 6.0)
            x, y = 12 * math.cos(a), -12 + 4.2 * math.sin(a)
            front = math.sin(a) > 0
            # a small riveted plate, edge-on at the sides
            w = max(1, int(round(2.8 * abs(math.sin(a)))) + 1)
            for dx_ in range(-w, w + 1):
                for dy_ in range(-3, 3):
                    # v0.10: bright riveted iron with a copper rim so the orbit reads on a dark floor
                    ch = "E" if dy_ == -3 else "q" if dy_ == 2 else "e" if dx_ < 0 else "Q"     # v0.10: hot copper plates
                    if abs(dx_) == w and dy_ in (-1, 0, 1): ch = "6"
                    c.put(*P(x + dx_, y + dy_), ch if front else {"E": "e", "e": "Q", "Q": "q", "q": "q", "6": "4"}[ch])
            c.put(*P(x, y), "0" if front else "6")
            c.put(*P(x, y + 3), "9" if front else "8")
        out.append(outl(c.spr(), "Z"))
    return out


def shatter_fx():
    out = []
    for i in range(4):
        c = cv()
        rnd = random.Random(3)
        for k in range(6):
            a = rnd.uniform(0, 6.28)
            d = 2 + i * 3
            x, y = math.cos(a) * d, -12 + math.sin(a) * d * 0.7 + i * i * 0.6
            c.put(*P(x, y), "6" if k % 2 else "5"); c.put(*P(x + 1, y), "4"); c.put(*P(x, y + 1), "2")
            if i < 2: c.put(*P(x - 1, y), "9")
        if i < 2: spark(c, 0, -12, 3 - i)
        out.append(c.spr())
    return out


def fx_pull():
    """Magnet field: broken rings that shrink in toward the hound, with field chevrons pointing inward."""
    out = []
    for i in range(6):
        c = cv()
        for j, r0 in enumerate((30, 18)):
            r = r0 - i * 4.0
            if r < 3: continue
            ry = r * 0.38
            n = int(r * 3) + 8
            for k in range(n):
                a = 2 * math.pi * k / n
                if (k + i + j) % 3 == 0: continue
                c.put(*P(r * math.cos(a), ry * math.sin(a)), "9" if j == 0 else "8")
            for k in range(6):
                a = 2 * math.pi * (k + 0.5 * j) / 6
                px_, py_ = (r + 2) * math.cos(a), (ry + 1) * math.sin(a)
                ix, iy = -math.cos(a), -math.sin(a) * 0.38
                c.put(*P(px_ + ix * 1.5, py_ + iy * 1.5), "0" if j == 0 else "9")
        out.append(c.spr())
    return out


def fx_jolt():
    out = []
    for i in range(4):
        c = cv()
        bolt(c, -7, 0, 5, 0, seed=120 + i, jag=1.2, step=1.8, halo="8", fork=3)
        spark(c, 5, 0, 1)
        c.put(-8 - (i % 2), (i % 3) - 1, "7")
        out.append(c.spr())
    return out


def fx_satellite(raise_=12):
    out = []
    for i in range(4):
        c = cv()
        y = -raise_
        sat_ball(c, 0, y, 2.2)
        # a small copper ring around it, turning
        for k in range(16):
            a = 2 * math.pi * k / 16
            rx = 3.8 * abs(math.cos(math.radians(i * 45))) + 0.6
            x_, y_ = rx * math.cos(a), 3.6 * math.sin(a)
            if (k + i) % 4: c.put(*P(x_, y + y_), "e" if x_ < 0 else "Q", over=False)
        crackle(c, 0, y, i, r=4, seed=17)
        # faint ground shadow so the player sees where it really is
        for x in range(-2, 3): c.put(x, 0, "7" if abs(x) < 2 else "1")
        out.append(c.spr())
    return out


def fx_orb():
    out = []
    for i in range(4):
        c = cv()
        for k in range(4):
            c.put(-5 - k * 2, (k + i) % 3 - 1, "8" if k < 2 else "7")
        sat_ball(c, 0, 0, 3.2)
        for k in range(20):
            a = 2 * math.pi * k / 20
            x_, y_ = 5.2 * math.cos(a), 2.2 * math.sin(a)
            ca_, sa_ = math.cos(math.radians(-25 + i * 15)), math.sin(math.radians(-25 + i * 15))
            c.put(*P(x_ * ca_ - y_ * sa_, x_ * sa_ + y_ * ca_), "e" if k % 2 else "Q", over=False)
        out.append(c.spr())
    return out


def build_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxKrnSpark"):
        fx_center("FxKrnSpark", [("Fly", fx_spark(), [0.05] * 4)], 18, 7, outdir,
                  "Fly loop, faces right; centred on the cell (MidCenter). Spark Beetle Zap, static discharge sparks, Chain Spark.")
    if want("FxKrnMote"):
        fx_center("FxKrnMote", [("Fly", fx_mote(), [0.06] * 4)], 16, 10, outdir, "Fly loop, faces right; centred. Coil Wisp Spark.")
    if want("FxKrnBall"):
        fx_center("FxKrnBall", [("Fly", fx_ball(), [0.07] * 4)], 24, 18, outdir, "Fly loop, faces right; centred. Stormcaller ball lightning (r ~4 px).")
    if want("FxKrnRivet"):
        fx_center("FxKrnRivet", [("Fly", fx_rivet(), [0.05] * 4)], 16, 8, outdir, "Fly loop, faces right; centred; spins 90 deg per frame. Rivet Imp.")
    if want("FxKrnSurge"):
        fx_center("FxKrnSurge", [("Fly", fx_surge(), [0.06] * 4)], 20, 12, outdir,
                  "Fly loop, faces right; centred, the spark ridge stands on the row 3 px below centre. Anvil Smith hammer surge.")
    if want("FxKrnLance"):
        fx_center("FxKrnLance", [("Fly", fx_lance(), [0.05] * 4)], 40, 8, outdir, "Fly loop, faces right; centred. Storm Herald lance bolt.")
    if want("FxKrnStud"):
        fx_ground("FxKrnStud", [("Land", [stud(0, 2, 2), stud(0, 2, 1), stud(0, 1, 0)], [0.06, 0.08, 0.12]),
                                ("Idle", [stud(0, 0), stud(1, 0), stud(2, 0), stud(3, 0)], [0.3, 0.08, 0.3, 0.08])], 12, 8, 0, outdir,
                  "Rivet stuck in the floor (conduction node). Land once, then loop Idle.")
    if want("FxKrnRod"):
        fx_ground("FxKrnRod", [("Rise", [rod(0.3), rod(0.7), rod(1.0, 1)], [0.05, 0.05, 0.08]),
                               ("Idle", [rod(1.0, 0), rod(1.0, 1), rod(1.0, 2), rod(1.0, 3)], [0.2, 0.08, 0.2, 0.08])], 12, 20, 0, outdir,
                  "Lightning rod driven into the floor (conduction node); top of the rod 14 px above the ground. Rise once, loop Idle.")
    if want("FxKrnArc"):
        fx_center("FxKrnArc", [("Crackle", fx_arc(), [0.05] * 4)], 16, 8, outdir,
                  "One 12 px arc segment, centred; tiled and rotated by KaurnConduction between linked nodes.")
    if want("FxKrnRing"):
        fx_ground("FxKrnRing", [("Play", ring_frames([4, 9, 14, 18, 21], 0.4, "098", seed=5), [0.05, 0.05, 0.06, 0.07, 0.09])],
                  48, 22, 10, outdir, "Coil Wisp static ring: hit radius r = 4, 9, 14, 18, 21 px on frames 0-4 (ry = 0.4 r).")
    if want("FxKrnQuake"):
        fx_ground("FxKrnQuake", [("Play", ring_frames([5, 11, 16, 20, 23, 25], 0.36, "954", debris=True, seed=9),
                                  [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])],
                  56, 26, 10, outdir, "Forge Colossus quake: ring r = 5..25 px on frames 0-5, iron grit thrown up.")
    if want("FxKrnStrike"):
        fx_ground("FxKrnStrike", [("Play", strike_frames(), [0.1] * 6 + [0.05, 0.06, 0.14, 0.14])], 28, 64, 4, outdir,
                  "Sky strike: frames 0-5 telegraph (ground mark), 6-7 the bolt (damage), 8-9 scorch.")
    if want("FxKrnCloud"):
        fx_ground("FxKrnCloud", [("Loop", [cloud(i) for i in range(4)], [0.12] * 4)], 34, 50, 0, outdir,
                  "Storm cloud, drawn 34-46 px above its ground point (it hangs over the hero). Loop.")
    if want("FxKrnCrackle"):
        fx_center("FxKrnCrackle", [("Play", crackle_fx(), [0.05, 0.05, 0.06, 0.06])], 10, 10, outdir,
                  "Static pip crackle, centred (Visual: BotCenter, offset -5).")
    if want("FxKrnHit"):
        fx_center("FxKrnHit", [("Play", hit_fx(), [0.04, 0.05, 0.06, 0.07])], 22, 16, outdir, "Spark burst, centred (impacts, arc zaps).")
    if want("FxKrnPlates"):
        fx_ground("FxKrnPlates", [("Loop", plates_fx(), [0.1] * 6)], 34, 24, 0, outdir,
                  "Anvil Smith iron plate: 3 plates orbit at 12 px above the feet, rx 12 ry 4. Loop.")
    if want("FxKrnPull"):
        fx_ground("FxKrnPull", [("Play", fx_pull(), [0.08] * 6)], 66, 26, 12, outdir,
                  "Lodestone Hound Howl: field rings r 30 -> 10 (and 18 -> 0) contracting on the hound. Visual only.")
    if want("FxKrnJolt"):
        fx_center("FxKrnJolt", [("Fly", fx_jolt(), [0.05] * 4)], 18, 10, outdir, "Fly loop, faces right; centred. Leyden Golem Arc.")
    if want("FxKrnSatellite"):
        fx_ground("FxKrnSatellite", [("Fly", fx_satellite(), [0.07] * 4)], 14, 20, 0, outdir,
                  "Storm Orrery satellite: the orb is drawn 12 px above its ground point (it orbits on the floor plane). Loop.")
    if want("FxKrnOrb"):
        fx_center("FxKrnOrb", [("Fly", fx_orb(), [0.06] * 4)], 22, 12, outdir, "Fly loop, faces right; centred. Storm Orrery Fling.")
    if want("FxKrnShatter"):
        fx_ground("FxKrnShatter", [("Play", shatter_fx(), [0.05, 0.06, 0.07, 0.09])], 30, 26, 0, outdir,
                  "Plate breaks: iron shards burst from 12 px above the feet.")


# ---- v0.8: own sheets for the two things that borrowed another monster's art
def fx_static_spark():
    """FxKrnStaticSpark: a stored static pip flung at the hero when a Kaurn special discharges (KrnDischarge).
    Not the Spark Beetle's straight zap: a fat crackling bead with a corkscrew tail of charge (faces right)."""
    out = []
    for i in range(4):
        c = cv()
        # corkscrew tail
        for k in range(7):
            x = -2 - k
            y = round(1.6 * math.sin((k + i * 1.5) * 1.3))
            c.put(x, y, "9" if k < 2 else "8" if k < 5 else "7")
        # the bead: white core, blue rim, one pixel of halo flicker
        for (x, y) in ((0, 0), (1, 0), (0, -1), (1, -1)):
            c.put(x, y, "0")
        for (x, y) in ((-1, 0), (-1, -1), (2, 0), (2, -1), (0, 1), (1, 1), (0, -2), (1, -2)):
            c.put(x, y, "9")
        a = i * math.pi / 2
        c.put(*P(0.5 + 3 * math.cos(a), -0.5 + 2.4 * math.sin(a)), "0")
        c.put(*P(0.5 + 2.4 * math.cos(a + 2.3), -0.5 + 2 * math.sin(a + 2.3)), "8")
        out.append(c.spr())
    return out


def slag_rod(rise=1.0, ph=0, cool=0):
    """A Kaurn's death: its iron runs into a crooked rod of slag that still holds the charge. Lumpy, bent, glowing
    orange seams cooling to a dull red, a puddle of slag round the foot, a forked tip that crackles. 13 px tall
    (the conduction node height), so it reads apart from the clean straight lightning rod of the Smith and Colossus."""
    c = cv()
    L = int(round(13 * rise))
    # slag puddle
    for x in range(-4, 5):
        c.put(x, 0, "2" if abs(x) > 2 else "3")
    c.put(-2, -1, "3"); c.put(2, -1, "2")
    hot = ["Y", "O", "o", "a"][min(3, cool)]
    warm = ["O", "o", "a", "a"][min(3, cool)]
    c.put(-1, 0, hot); c.put(1, 0, warm); c.put(3, 0, "a")
    if L > 0:
        for y in range(1, L + 1):
            x = int(round(0.9 * math.sin(y * 0.55)))        # crooked
            w = 1 if y < L - 2 else 0
            c.put(x, -y, "3" if y % 3 else "4")
            if w: c.put(x + 1, -y, "2")
            if y % 4 == 2: c.put(x - 1, -y, "3")               # lumps
            if y % 3 == 1 and y < L - 1: c.put(x + (y % 2), -y, warm if y > 3 else hot)   # glowing seams
        tx = int(round(0.9 * math.sin(L * 0.55)))
        c.put(tx - 1, -L - 1, "4"); c.put(tx + 1, -L - 1, "5"); c.put(tx, -L - 1, "3")
        base = outl(Spr({k: v for k, v in c.px.items() if k[1] < 0}), "Z")
        for k, v in base.px.items():
            if k not in c.px: c.px[k] = v
        c.put(tx, -L - 2, "0" if ph % 2 == 0 else "9")
        if ph % 2 == 1:
            crackle(c, tx, -L - 2, ph, r=3, seed=11)
    if 0 < rise < 1.0:
        for (x, y) in ((-3, -2), (3, -1), (-2, -4), (2, -3)):
            c.put(x, y, "O" if rise < 0.5 else "o")
    return c.spr()


def build_fx_v08(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxKrnStaticSpark"):
        fx_center("FxKrnStaticSpark", [("Fly", fx_static_spark(), [0.05] * 4)], 16, 8, outdir,
                  "Fly loop, faces right; centred. Static pips discharged at the hero by every Kaurn special (v0.8; was FxKrnSpark).")
    if want("FxKrnSlagRod"):
        fx_ground("FxKrnSlagRod", [("Rise", [slag_rod(0.3), slag_rod(0.7), slag_rod(1.0, 1)], [0.05, 0.05, 0.08]),
                                   ("Idle", [slag_rod(1.0, 0, 1), slag_rod(1.0, 1, 1), slag_rod(1.0, 2, 2), slag_rod(1.0, 3, 2)],
                                    [0.2, 0.08, 0.2, 0.08])], 12, 20, 0, outdir,
                  "Slag rod left where a Kaurn monster dies (conduction node, v0.8; was FxKrnRod). Same cell/origin as FxKrnRod: "
                  "tip 14 px above the ground. Rise once, loop Idle.")


FXN = ["FxKrnSpark", "FxKrnMote", "FxKrnBall", "FxKrnRivet", "FxKrnSurge", "FxKrnLance", "FxKrnStud", "FxKrnRod", "FxKrnArc",
       "FxKrnRing", "FxKrnQuake", "FxKrnStrike", "FxKrnCloud", "FxKrnCrackle", "FxKrnHit", "FxKrnPlates", "FxKrnShatter",
       "FxKrnPull", "FxKrnJolt", "FxKrnSatellite", "FxKrnOrb", "FxKrnStaticSpark", "FxKrnSlagRod"]


# ================================================================== ICONS + GOD PORTRAIT
def icon_chain_spark(ph):
    """Spell: a spark leaping from monster to monster (three struck targets joined by a bolt)."""
    c = cv()
    nodes = [(-5, -4), (0, -11), (5, -5)]
    for (x, y) in nodes:
        ell(c, x, y, 1.8, 1.8, "3456", bias=0.3)
    base = outl(Spr(dict(c.px)), "Z")
    c = Canvas(); c.px = dict(base.px)
    pts = [(-6, -13), (-5, -4), (0, -11), (5, -5), (6, -1)]
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        if ph == 0 and k == 3: break
        bolt(c, x0, y0, x1, y1, seed=k * 3 + ph, jag=1.0, step=2.0, halo=None)
    for (x, y) in nodes[: (2 if ph == 0 else 3)]:
        spark(c, x, y, 1)
    if ph == 1: spark(c, 6, -1, 1)
    return Spr({k: v for k, v in c.px.items() if -8 <= k[0] <= 7 and -15 <= k[1] <= 0})


def icon_lightning_rod(ph):
    """Artifact / floating token: an iron lightning rod with a copper coil, crackling at the tip."""
    c = cv()
    for y in range(-11, 0):
        c.put(0, y, "4" if y % 3 else "6"); c.put(1, y, "2")
    for k, y in enumerate(range(-8, -3)):
        c.put(-1, y, "e" if k % 2 == 0 else "Q"); c.put(2, y, "Q" if k % 2 == 0 else "q")
    c.put(-1, -12, "5"); c.put(2, -12, "5"); c.put(0, -12, "4"); c.put(1, -12, "3")
    c.put(-2, -13, "5"); c.put(3, -13, "4")
    c.put(0, 0, "3"); c.put(1, 0, "2")
    base = outl(Spr(dict(c.px)), "Z")
    c = Canvas(); c.px = dict(base.px)
    c.put(0, -14, "0"); c.put(1, -14, "9")
    if ph == 0:
        c.put(-1, -15, "9"); c.put(2, -15, "8"); c.put(-4, -12, "9"); c.put(5, -10, "8")
    else:
        spark(c, 0, -14, 1)
        c.put(-3, -14, "9"); c.put(4, -13, "9"); c.put(-4, -9, "8"); c.put(5, -15, "8")
    return Spr({k: v for k, v in c.px.items() if -8 <= k[0] <= 7 and -15 <= k[1] <= 0})


def hud_lightning_rod():
    """11x7 HUD icon, drawn at its own size (origin = bottom centre (5, 6))."""
    c = cv()
    for x in range(-4, 4):
        c.put(x, -3, "4" if x % 3 else "6")
    c.put(-1, -4, "e"); c.put(1, -4, "e"); c.put(0, -2, "Q"); c.put(-2, -2, "Q")
    c.put(4, -4, "5"); c.put(4, -2, "5")
    base = outl(Spr(dict(c.px)), "Z")
    c = Canvas(); c.px = dict(base.px)
    c.put(5, -3, "0"); c.put(5, -5, "9"); c.put(4, -6, "9") if False else None
    return Spr({k: v for k, v in c.px.items() if -5 <= k[0] <= 5 and -6 <= k[1] <= 0})


def deity_portrait(ph):
    c = cv()
    # storm sky: dark navy fading to soot black at the bottom
    for y in range(-23, 1):
        for x in range(-14, 15):
            d = (y + 23) / 23.0
            ch = "n" if d < 0.35 else ("1" if d < 0.75 else "Z")
            if 0.3 < d < 0.4 and (x + y) % 2 == 0: ch = "1"
            if 0.7 < d < 0.8 and (x + y) % 2 == 0: ch = "Z"
            c.put(x, y, ch)
    # rolling clouds along the top
    rnd = random.Random(2)
    for k in range(8):
        x = -15 + k * 4.2 + (ph % 2) * 0.5
        ell(c, x, -21.5 + rnd.uniform(-1, 1), 3.4, 2.2, "nuU", bias=-0.2)
    # a distant fork of lightning behind (moves between frames)
    bx = [-9, 9, -7, 10][ph]
    bolt(c, bx, -20, bx + (2 if bx < 0 else -2), -9, seed=ph + 1, jag=1.4, step=2.0, halo="7", fork=3)
    # the anvil the god is forged on
    poly(c, [(-11, -3), (-6, -6), (8, -6), (8, -3), (5, -3), (6, -1), (-4, -1), (-3, -3)], "3",
         shade=lambda X, Y: "5" if Y <= -6 else ("2" if Y >= -2 else "4" if X < 0 else "3"))
    for x in range(-12, 13): c.put(x, 0, "2" if x % 3 else "1")
    # the god's iron mask rising out of the anvil: horned with two lightning rods
    mx, my = 0.0, -12.0
    for sd in (-1, 1):
        line(c, mx + sd * 3.5, my - 4.5, mx + sd * 7.5, my - 10.0, "4")
        c.put(*P(mx + sd * 7.5, my - 10.5), "6")
        c.put(*P(mx + sd * 5.2, my - 7.0), "e")
    ell(c, mx, my, 5.0, 5.6, IRON_HI, bias=0.25)
    poly(c, [(mx - 5, my + 1), (mx + 5, my + 1), (mx + 3.5, my + 6), (mx - 3.5, my + 6)], "3",
         shade=lambda X, Y: "4" if X < mx - 1 else "3" if X < mx + 2 else "2")
    line(c, mx - 4, my - 1.5, mx + 4, my - 1.5, "1")           # brow ridge / visor shadow
    line(c, mx, my - 5, mx, my + 5, "2")                        # forged seam down the middle
    for (x, y) in ((-3, -4), (3, -4), (-3, 3), (3, 3)):
        c.put(*P(mx + x, my + y), "6")                          # rivets
    # eyes: cold lightning
    for sd in (-1, 1):
        c.put(*P(mx + sd * 2, my - 0.5), "0"); c.put(*P(mx + sd * 3, my - 0.5), "9")
    # forge-hot mouth grate (small accent)
    for x in range(-2, 3):
        c.put(*P(mx + x, my + 3.5), "O" if (x + ph) % 2 else "o")
    c.put(*P(mx, my + 3.5), "Y")
    # the arc between the horn rods (flickers)
    bolt(c, mx - 7.5, my - 10.5, mx + 7.5, my - 10.5, seed=10 + ph, jag=1.2, step=2.0, halo=None)
    # sparks off the anvil
    for k, (x, y) in enumerate(((-9, -5), (9, -7), (-12, -6), (11, -4))):
        if (k + ph) % 2 == 0: c.put(x, y - (ph % 2), "9")
    return Spr({k: v for k, v in c.px.items() if -14 <= k[0] <= 14 and -23 <= k[1] <= 0})


ICONS = ["IconKrnChainSpark", "IconKrnLightningRod", "IconKrnChainSparkBubble", "IconKrnLightningRodBubble", "IconKrnLightningRodHud",
         "DeityKaurn"]


def build_icons(outdir):
    from PIL import Image
    import json
    for name, fn in (("IconKrnChainSpark", icon_chain_spark), ("IconKrnLightningRod", icon_lightning_rod)):
        frames = [fn(0), fn(1)]
        img, man = pack(name, [("Idle", frames, [0.5, 0.25])], 16, 16, (8, 15), outdir, cols=2)
        preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=10)
        BUILT[name] = {"cell": (16, 16), "feet": (8, 15), "anims": [("Idle", 2, [0.5, 0.25])], "img": img, "man": man}
        print("built", name)
    # shop bubbles (34x41) the way tools/sprites/item_icons.py makes them: spells on the blank parchment card,
    # artifacts at 1x in the lower middle of an empty bubble
    import item_icons as II
    card = II.blank_card()
    for name, kind in (("IconKrnChainSpark", "spell"), ("IconKrnLightningRod", "artifact")):
        img = Image.open(os.path.join(outdir, name + ".png")).convert("RGBA")
        bubbles = []
        for i in range(2):
            ic = img.crop((i * 16, 0, i * 16 + 16, 16))
            b = card.copy() if kind == "spell" else Image.new("RGBA", (34, 41), (0, 0, 0, 0))
            bb = card.getbbox() if kind == "spell" else (0, 0, 34, 41)
            cx = (bb[0] + bb[2]) // 2 - 8
            cy = (bb[1] + bb[3]) // 2 - 8 if kind == "spell" else 41 - 16 - 6
            b.alpha_composite(ic, (cx, cy))
            bubbles.append(b)
        out = Image.new("RGBA", (68, 41), (0, 0, 0, 0))
        for i, b in enumerate(bubbles): out.alpha_composite(b, (i * 34, 0))
        out.save(os.path.join(outdir, name + "Bubble.png"))
        json.dump({"cellW": 34, "cellH": 41, "cols": 2, "anims": [{"name": "Bubble", "frames": [0, 1], "durations": [0.5, 0.5]}]},
                  open(os.path.join(outdir, name + "Bubble.json"), "w"))
        print("built", name + "Bubble")
    img, man = pack("IconKrnLightningRodHud", [("Hud", [hud_lightning_rod()], [0.5])], 11, 7, (5, 6), outdir, cols=1)
    print("built IconKrnLightningRodHud")
    frames = [deity_portrait(i) for i in range(4)]
    img, man = pack("DeityKaurn", [("Idle", frames, [0.3, 0.12, 0.3, 0.12])], 29, 24, (14, 23), outdir)
    preview(img, man, os.path.join(outdir, "DeityKaurn_preview.png"), scale=10)
    BUILT["DeityKaurn"] = {"cell": (29, 24), "feet": (14, 23), "anims": [("Idle", 4, [0.3, 0.12, 0.3, 0.12])], "img": img, "man": man}
    crop = img.crop((0, 0, 29 * 4, 24)).load()
    assert all(crop[x, y][3] == 255 for x in range(29 * 4) for y in range(24)), "portrait must be opaque"
    print("built DeityKaurn (opaque)")


# ================================================================== LODESTONE HOUND (T2, Rivet Imp / Spark Beetle line)
def magnet(f, x, y, s=1.0, glow=1, ph=0, field=0):
    """A horseshoe magnet bolted on the shoulders, poles up: iron U, red bands, silver pole tips, arc between them."""
    def m(c):
        for sd in (-1, 1):
            tube(c, [(x + sd * 2.6 * s, y), (x + sd * 2.6 * s, y - 3.2 * s)], [1.2 * s, 1.2 * s], IRON_HI, bias=0.15)
        ell(c, x, y, 3.8 * s, 1.8 * s, IRON_HI, bias=0.1, vmin=-0.1)
        for sd in (-1, 1):
            c.put(*P(x + sd * 2.6 * s, y - 2.4 * s), "a")
            c.put(*P(x + sd * 2.6 * s, y - 3.6 * s), "6")
    stamp(f.b, m, ch="Z")
    tl, tr = (x - 2.6 * s, y - 4.6 * s), (x + 2.6 * s, y - 4.6 * s)
    if glow >= 1:
        f.g.put(*P(*tl), "9"); f.g.put(*P(*tr), "9")
    if glow >= 2:
        bolt(f.g, tl[0], tl[1] - 0.5, tr[0], tr[1] - 0.5, seed=ph, jag=1.0, step=1.6, halo=None)
    if field:
        # magnetic field loops arching out of the poles
        for k in range(field):
            r = 3.0 + k * 2.4
            for a in range(200, 341, 12):
                px_ = x + math.cos(math.radians(a)) * r * 1.3
                py_ = y - 4.6 * s + math.sin(math.radians(a)) * r
                if (a // 12 + k + ph) % 3: f.g.put(*P(px_, py_), "8" if k else "9")
    return tl, tr


def hound(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, gait=1.0, head=(0.0, 0.0), jaw=0.0, glow=1, ph=0, field=0, eye="open",
          stretch=0.0, crouch=0.0, tail=0.0, extra=None, dead=False):
    f = Fr()
    ca = math.radians(tilt)
    def R(x, y):  # rotate body points about the hips, then translate
        x, y = x + 6.0, y
        return (-6.0 + x * math.cos(ca) - y * math.sin(ca) + dx, x * math.sin(ca) + y * math.cos(ca) + dy)
    sx = 1.0 + stretch * 0.25
    hip = R(-5.0 * sx, -7.0 + crouch)
    sho = R(4.2 * sx, -7.6 + crouch * 0.5)
    # far legs (shadowed, no outline)
    for i, (j, base) in enumerate(((hip, -5.0), (sho, 4.6))):
        ph_ = legs + i * math.pi + math.pi * 0.5
        lift = max(0.0, math.sin(ph_)) * 2.0 * gait
        fx_ = base + math.cos(ph_) * 3.0 * gait + dx + stretch * (3 if i else -3)
        knee = (j[0] + (1.5 if i == 0 else 0.5), (j[1] - lift) * 0.5 - 1.5)
        line(f.n, j[0] + 1, j[1] + 1, knee[0], knee[1], "3")
        line(f.n, knee[0], knee[1], fx_ + 1, -lift, "2")
        f.n.put(*P(fx_ + 2, -lift), "2")
    # coil-spring tail
    tb = R(-7.6 * sx, -10.4 + crouch)
    for k in range(4):
        a = math.radians(-140 + tail + k * 6)
        x_, y_ = tb[0] + math.cos(a) * k * 1.0, tb[1] + math.sin(a) * k * 1.0 - (k % 2) * 0.7
        f.u.put(*P(x_, y_), "e" if k % 2 == 0 else "Q")
    # body: lean iron barrel, deep chest
    ell(f.b, *R(-0.5 * sx, -9.2 + crouch * 0.8), 6.8 * sx, 3.7, IRON_L, ang=tilt, bias=0.15)
    ell(f.b, *R(4.0 * sx, -9.8 + crouch * 0.5), 4.4, 4.3, IRON_L, ang=tilt, bias=0.2)
    ell(f.b, *R(-5.0 * sx, -9.0 + crouch), 3.6, 3.5, IRON_L, ang=tilt, bias=0.1)
    # belly line + rivet row + forge seam on the ribs
    for k in range(6):
        f.b.put(*P(*R((-6.0 + k * 2.0) * sx, -12.4 + crouch * 0.8 + abs(k - 2.5) * 0.3)), "5" if k % 2 else "4")
    for k in range(3):
        f.b.put(*P(*R((-3.0 + k * 2.2) * sx, -6.6 + crouch * 0.8)), "2")
    if not dead:
        f.g.put(*P(*R(0.5 * sx, -8.6 + crouch * 0.8)), "o")
    # head + jaws
    hx, hy = R(9.2 * sx + head[0], -12.0 + crouch * 0.3 + head[1])
    def headf(c):
        ell(c, hx, hy, 3.2, 2.8, IRON_HI, bias=0.25)
        # upper snout
        tube(c, [(hx + 1.5, hy - 0.2), (hx + 5.0, hy + 0.4 - jaw * 0.6)], [1.7, 1.2], IRON_HI, bias=0.25)
        # lower jaw swings open
        ja = 18 + jaw * 30
        je = polar(hx + 1.0, hy + 1.6, 4.0, ja)
        tube(c, [(hx + 1.0, hy + 1.4), je], [1.0, 0.7], IRON, bias=0.1)
        # swept-back ear plate
        line(c, hx - 1.4, hy - 2.0, hx - 3.4, hy - 3.6, "4")
        c.put(*P(hx - 3.6, hy - 3.8), "5")
    stamp(f.b, headf, ch="Z")
    if jaw > 0.3 and not dead:
        f.g.put(*P(hx + 3.0, hy + 1.6), "O"); f.g.put(*P(hx + 4.0, hy + 1.8), "o")
    # near legs
    for i, (j, base) in enumerate(((hip, -5.5), (sho, 4.2))):
        ph_ = legs + i * math.pi
        lift = max(0.0, math.sin(ph_)) * 2.2 * gait
        fx_ = base + math.cos(ph_) * 3.2 * gait + dx + stretch * (4 if i else -4)
        knee = (j[0] + (1.8 if i == 0 else 0.4), (j[1] - lift) * 0.5 - 1.0)
        def leg(c, j=j, knee=knee, fx_=fx_, lift=lift):
            tube(c, [j, knee, (fx_, -1.0 - lift)], [1.9, 1.3, 1.0], IRON_L, bias=0.15)
            line(c, fx_ - 0.5, -lift, fx_ + 1.5, -lift, "4")
        stamp(f.b, leg, ch="Z")
    # v0.9 lineage (Spark Beetle): a copper wing-case saddle over the haunches and the beetle's coil antennae on the brow
    stamp(f.b, lambda c: elytra(c, *R(-3.6 * sx, -11.6 + crouch * 0.8), 4.4, 2.4, ang=tilt), ch="Z")
    coil_antennae(f.b, f.g, hx - 0.6, hy - 2.2, ang=-110 + tilt, L=4.6, spread=26, lit=not dead)
    # magnet on the shoulders
    tl, tr = magnet(f, *R(1.0 * sx, -12.4 + crouch * 0.7), s=0.8, glow=0 if dead else glow, ph=ph, field=field)
    # eye
    ex, ey = hx + 0.8, hy - 0.6
    if eye == "open": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "9")
    elif eye == "wide": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "0"); f.g.put(*P(ex, ey - 1), "9")
    elif eye == "squint": f.g.put(*P(ex, ey), "8")
    elif eye == "dead": f.g.put(*P(ex, ey), "3")
    if extra: extra(f, (hx, hy), (tl, tr))
    return f.done()


def hound_corpse():
    f = Fr()
    ell(f.b, -1, -3.0, 8.4, 3.0, IRON_L, bias=0.0)
    ell(f.b, 8.5, -2.4, 3.0, 2.2, IRON_HI, bias=0.2)
    tube(f.b, [(10, -2), (14, -1)], [1.2, 0.8], IRON_HI)
    for x in (-6, -2, 3):
        line(f.b, x, -5.6, x + 2, -8.4, "3")
    # the magnet fell off
    for sd in (-1, 1):
        tube(f.b, [(-13 + sd * 2, 0), (-13 + sd * 2, -3)], [1.0, 1.0], IRON_HI)
    ell(f.b, -13, 0, 3.0, 1.2, IRON_HI, vmin=-0.2)
    f.b.put(-15, -2, "a"); f.b.put(-11, -2, "a")
    for k in range(4): f.b.put(-10 + k, -6 - (k % 2), "e" if k % 2 == 0 else "Q")
    f.g.put(9, -3, "3")
    return f.done()


def build_hound(outdir):
    H = hound
    idle = [H(legs=0, gait=0.0, ph=0, glow=1), H(legs=0, gait=0.0, ph=1, dy=0.3, head=(0, 0.3), glow=2, tail=8),
            H(legs=0, gait=0.0, ph=2, dy=0.3, head=(0, 0.4), glow=1, tail=14, eye="squint"), H(legs=0, gait=0.0, ph=3, glow=2, tail=6)]
    run = [H(legs=i * math.pi / 3, gait=1.0, dy=-0.8 * abs(math.sin(i * math.pi / 3)), tilt=-3 * math.cos(i * math.pi / 3),
             stretch=0.25 * math.sin(i * math.pi / 3), head=(0.5, 0.6), ph=i + 4, glow=1 + (i % 2), tail=-10 + 6 * (i % 2))
           for i in range(6)]
    # LUNGE: crouch, coil, SPRING + BITE (hit on 3), land, recover
    def bite(f, h, poles):
        hx, hy = h
        for (a, b) in ((6, -1), (7, 2), (5, 3)):
            f.g.put(*P(hx + a, hy + b), "0" if a == 6 else "9")
        line(f.g, hx - 25, hy + 1, hx - 21, hy + 1, "8")
        line(f.g, hx - 24, hy + 4, hx - 21, hy + 4, "7")
    lunge = [H(crouch=2.0, tilt=4, head=(-1.0, 1.5), jaw=0.2, glow=2, ph=10, eye="wide", tail=20),
             H(crouch=3.0, tilt=6, head=(-1.5, 2.0), jaw=0.5, glow=2, ph=11, eye="wide", tail=26, dx=-0.8),
             H(dy=-2.5, tilt=-8, stretch=1.0, gait=0.0, head=(1.5, 0.5), jaw=1.0, glow=2, ph=12, eye="wide", dx=1.5, legs=1.6),
             H(dy=-1.0, tilt=-2, stretch=0.8, gait=0.0, head=(2.0, 1.5), jaw=0.0, glow=2, ph=13, eye="wide", dx=3.0, legs=1.6, extra=bite),
             H(dy=0.4, tilt=3, crouch=1.0, head=(1.0, 1.2), jaw=0.2, glow=1, ph=14, dx=3.0, legs=0.4),
             H(dx=1.5, head=(0.4, 0.4), glow=1, ph=15, legs=0.2, gait=0.3)]
    # HOWL: lower, raise the head, field loops pour out of the magnet (pull frames 1-6), relax
    def howl_fx(n):
        def fn(f, h, poles):
            hx, hy = h
            for k in range(n):
                r = 3 + k * 2.5
                for a in (-30, -15, 0, 15, 30):
                    f.g.put(*P(hx + 4 + r * math.cos(math.radians(a - 40)), hy - 1 + r * math.sin(math.radians(a - 40))), "9" if k == 0 else "8")
        return fn
    howl = [H(crouch=1.2, head=(-1.0, 1.4), jaw=0.2, glow=1, ph=20, eye="squint"),
            H(head=(-1.6, -2.6), jaw=0.8, glow=2, ph=21, field=1, eye="wide", tilt=-4, extra=howl_fx(1)),
            H(head=(-2.0, -3.4), jaw=1.0, glow=2, ph=22, field=2, eye="wide", tilt=-6, extra=howl_fx(2)),
            H(head=(-2.0, -3.6), jaw=1.0, glow=2, ph=23, field=3, eye="wide", tilt=-6, extra=howl_fx(3)),
            H(head=(-2.0, -3.4), jaw=0.9, glow=2, ph=24, field=2, eye="wide", tilt=-6, extra=howl_fx(2)),
            H(head=(-2.0, -3.6), jaw=1.0, glow=2, ph=25, field=3, eye="wide", tilt=-6, extra=howl_fx(3)),
            H(head=(-1.4, -2.0), jaw=0.6, glow=2, ph=26, field=1, eye="open", tilt=-3),
            H(head=(0.0, 0.0), jaw=0.0, glow=1, ph=27, eye="open")]
    death = [H(crouch=0.5, tilt=-10, head=(-1, -2.5), jaw=1.0, glow=2, ph=30, eye="wide", tail=30),
             dim_glow(H(dy=1.0, tilt=-18, head=(0, 1.5), jaw=0.6, glow=0, eye="dead", legs=1.0, dead=True)),
             dim_glow(grounded(H(dy=2.0, tilt=-30, head=(0, 3), jaw=0.4, glow=0, eye="dead", legs=2.0, dead=True))),
             dim_glow(hound_corpse())]
    knock = H(crouch=0.5, tilt=-10, head=(-1, -1.5), jaw=0.6, glow=2, ph=33, eye="wide", tail=24, dx=-0.6)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.07] * 6),
             ("Lunge", lunge, [0.14, 0.14, 0.06, 0.08, 0.12, 0.14]),
             ("Howl", howl, [0.12, 0.14, 0.14, 0.14, 0.14, 0.14, 0.12, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("KrnLodeHound", anims, outdir, scale=6, remap=RUST)


# ================================================================== LEYDEN GOLEM (T2, Coil Wisp / Stormcaller-side line)
def leyden(dx=0.0, dy=0.0, tilt=0.0, feet=((-3, 0), (3, 0)), arm=(70.0, 95.0), barm=(110.0, 85.0), core=1, ph=0, eye="open",
           extra=None, dead=False, cap_dy=0.0, squash=0.0):
    f = Fr()
    jx, jy = dx + tilt * 0.08, -11.5 + dy + squash * 0.6
    rx, ry = 6.2 + squash * 0.5, 6.6 - squash * 0.6
    # stubby iron legs with clamp feet
    for i, (fx_, fy_) in enumerate(feet):
        c = f.u if i == 0 else f.b
        hx_ = jx + (-2.4 if i == 0 else 2.4)
        tube(c, [(hx_, jy + ry - 1.5), (fx_ + dx * 0.3, fy_ - 1.5)], [1.6, 1.4], IRON, bias=-0.1 if i == 0 else 0.15)
        rect(c, fx_ + dx * 0.3 - 2, fy_ - 1.6, fx_ + dx * 0.3 + 2, fy_, "2345")
    # back arm: copper coil, iron clamp hand
    def coil_arm(c, sx_, sy_, a1, a2, L1=3.6, L2=3.4):
        e = polar(sx_, sy_, L1, a1)
        h = polar(e[0], e[1], L2, a2)
        tube(c, [(sx_, sy_), e, h], [1.1, 1.0, 0.9], COPPER, bias=0.0)
        for k, (x, y) in enumerate(line_px(*P(sx_, sy_), *P(*h))):
            if k % 2: c.put(x, y, "q")
        tube(c, [h, polar(h[0], h[1], 1.4, a2)], [1.3, 1.3], IRON_HI, bias=0.2)
        return polar(h[0], h[1], 1.6, a2)
    bh = coil_arm(f.u, jx - rx + 1.2, jy - 3.0, barm[0], barm[1])
    # the jar: thick dark glass, a lightning coil inside, copper bands, a pale rim light
    def jar_shade(nu, nv, d, l, ch, x, y):
        if d > 0.72: return "V" if (nu + nv) < -0.4 else ("v" if (nu + nv) < 0.5 else "N")
        if d > 0.55 and (nu + nv) < -0.6: return "W"
        return "n"
    ell(f.b, jx, jy, rx, ry, CLOTH, bias=0.0, shader=jar_shade)
    # inner charge
    if not dead and core:
        r = 2.0 + core * 0.9
        bolt(f.g, jx - 0.5, jy + ry - 2.5, jx + 0.5, jy - ry + 2.5, seed=ph, jag=1.3 + core * 0.3, step=1.6, halo="7" if core < 3 else "8")
        for y in range(int(jy - r), int(jy + r) + 1):
            for x in range(int(jx - r), int(jx + r) + 1):
                dd = math.hypot(x - jx, (y - jy) * 0.8) / r
                if dd < 0.5: f.g.put(x, y, "0" if core >= 2 else "9")
                elif dd < 0.85 and (x + y + ph) % 2 == 0: f.g.put(x, y, "9" if core >= 2 else "8")
        if core >= 3:
            for k in range(4):
                a = k * 90 + ph * 20
                f.g.put(*P(jx + math.cos(math.radians(a)) * (rx - 1.5), jy + math.sin(math.radians(a)) * (ry - 1.5)), "0")
    # glass glints: a tall highlight streak on the lit side, a small one opposite
    for k in range(-3, 3):
        f.b.put(*P(jx - rx * 0.55, jy + k), "W" if k < 0 else "V")
    f.b.put(*P(jx + rx * 0.6, jy + 2), "v"); f.b.put(*P(jx + rx * 0.6, jy + 3), "v")
    # copper bands
    for by in (jy - ry * 0.45, jy + ry * 0.55):
        w = rx * math.sqrt(max(0.0, 1 - ((by - jy) / ry) ** 2))
        line(f.b, jx - w + 0.5, by, jx + w - 0.5, by, "eQ")
    # iron lid + two terminal posts
    cy0 = jy - ry - 0.5 + cap_dy
    def lid(c):
        rect(c, jx - 4.0, cy0 - 1.5, jx + 4.0, cy0 + 0.6, "2345")
        for sd in (-1, 1):
            tx = jx + sd * 2.2
            line(c, tx, cy0 - 1.5, tx, cy0 - 4.0, "4")
            c.put(*P(tx, cy0 - 4.6), "6"); c.put(*P(tx - 0.6 * sd, cy0 - 4.4), "5")
    stamp(f.b, lid, ch="Z")
    tips = [(jx - 2.2, cy0 - 5.2), (jx + 2.2, cy0 - 5.2)]
    # front arm
    fh = None
    def farm(c):
        return coil_arm(c, jx + rx - 1.2, jy - 3.0, arm[0], arm[1])
    tmp = Canvas()
    fh = farm(tmp)
    stamp(f.b, farm, ch="Z")
    # eye: a single lamp-lens set in the glass
    ex, ey = jx + 1.2, cy0 - 0.5
    f.b.put(*P(ex - 1, ey), "1"); f.b.put(*P(ex, ey), "1"); f.b.put(*P(ex + 1, ey), "1"); f.b.put(*P(ex + 2, ey), "1")
    if eye != "dead":
        f.g.put(*P(ex, ey), "0" if eye in ("open", "wide") else "8"); f.g.put(*P(ex + 1, ey), "9" if eye != "squint" else "8")
        if eye == "wide": f.g.put(*P(ex + 2, ey), "0")
    if not dead:
        for t in tips: f.g.put(*P(*t), "9" if core < 2 else "0")
    if extra: extra(f, tips, fh, (jx, jy))
    return f.done()


def leyden_corpse():
    f = Fr()
    # the jar lies broken, glass shards, the lid rolled off
    ell(f.b, -1, -3.2, 6.5, 3.2, CLOTH, bias=0.0, shader=lambda nu, nv, d, l, ch, x, y: "V" if d > 0.7 and nu + nv < 0 else ("v" if d > 0.7 else "n"))
    for (x, y) in ((6, -1), (8, 0), (-8, 0), (4, -6)):
        f.b.put(x, y, "W"); f.b.put(x + 1, y, "V")
    rect(f.b, -13, -3, -9, 0, "2345")
    line(f.b, -12, -3, -12, -5, "4"); line(f.b, -10, -3, -10, -5, "4")
    for k in range(5): f.b.put(1 + k, -1 - (k % 2), "e" if k % 2 == 0 else "Q")
    f.g.put(-1, -4, "7"); f.g.put(0, -3, "7")
    return f.done()


def build_leyden(outdir):
    L = leyden
    idle = [L(ph=0, core=1), L(ph=1, core=1, dy=0.3, squash=0.3), L(ph=2, core=2, dy=0.3, squash=0.3, eye="open"), L(ph=3, core=1)]
    run = [L(dx=0.4, tilt=[-6, -2, 4, 6, 2, -4][i], dy=-0.6 * abs(math.sin(i * math.pi / 3)), ph=4 + i, core=1 + (i % 2),
             feet=((-3 - 2 * math.sin(i * math.pi / 3), -0.8 * max(0, -math.cos(i * math.pi / 3))),
                   (3 + 2 * math.sin(i * math.pi / 3), -0.8 * max(0, math.cos(i * math.pi / 3)))),
             arm=(60 + 14 * math.sin(i * 1.05), 80), barm=(120 - 14 * math.sin(i * 1.05), 100)) for i in range(6)]
    # ARC: raise the clamp hand, charge runs up the coil, JOLT (3: release at the clamp), recoil
    def jolt(f, tips, fh, jc):
        bolt(f.g, fh[0], fh[1], fh[0] + 6, fh[1] - 1, seed=3, jag=0.8, step=1.5)
        spark(f.g, fh[0] + 1, fh[1], 2)
    def climb(n):
        def fn(f, tips, fh, jc):
            for k in range(n):
                f.g.put(*P(jc[0] + 5 + k, jc[1] - 2 - k * 0.6), "9")
        return fn
    arc = [L(ph=10, core=2, arm=(40, 60), eye="open"),
           L(ph=11, core=2, arm=(-10, -30), eye="wide", tilt=-4, extra=climb(2)),
           L(ph=12, core=3, arm=(-30, -60), eye="wide", tilt=-6, extra=climb(4)),
           L(ph=13, core=2, arm=(-5, -5), eye="wide", tilt=4, dx=0.6, extra=jolt),
           L(ph=14, core=1, arm=(20, 40), eye="open", tilt=2),
           L(ph=15, core=1, eye="open")]
    # OVERCHARGE: squat, arms up, the jar floods white, DISCHARGE (4: ring + allies charged), settle
    def surge(n):
        def fn(f, tips, fh, jc):
            for i, t in enumerate(tips):
                for k in range(n):
                    a = -90 + (i * 2 - 1) * (30 + k * 30)
                    e = polar(t[0], t[1], 6 + k * 2, a)
                    bolt(f.g, t[0], t[1], e[0], e[1], seed=k * 7 + i + n, jag=0.9, step=1.6, halo=None)
        return fn
    over = [L(ph=20, core=2, squash=0.8, dy=0.6, arm=(60, 110), barm=(120, 70), eye="squint"),
            L(ph=21, core=2, squash=0.4, arm=(-40, -80), barm=(220, 260), eye="wide", extra=surge(1)),
            L(ph=22, core=3, squash=0.0, dy=-0.4, arm=(-50, -90), barm=(230, 270), eye="wide", cap_dy=-0.4, extra=surge(2)),
            L(ph=23, core=3, squash=0.0, dy=-0.6, arm=(-55, -95), barm=(235, 275), eye="wide", cap_dy=-0.6, extra=surge(2)),
            L(ph=24, core=3, squash=-0.4, dy=-0.8, arm=(-60, -100), barm=(240, 280), eye="wide", cap_dy=-1.0, extra=surge(3)),
            L(ph=25, core=2, squash=0.6, dy=0.4, arm=(30, 70), barm=(150, 110), eye="open", extra=surge(1)),
            L(ph=26, core=1, squash=0.3, arm=(60, 90), barm=(120, 90), eye="open"),
            L(ph=27, core=1, eye="open")]
    death = [L(ph=30, core=3, tilt=-10, arm=(-50, -90), barm=(230, 270), eye="wide"),
             dim_glow(L(ph=31, core=1, tilt=-20, dy=1.5, eye="dead", dead=True, arm=(100, 140), barm=(80, 40))),
             dim_glow(grounded(L(ph=32, core=0, tilt=-34, dy=3.5, eye="dead", dead=True, squash=1.0))),
             dim_glow(leyden_corpse())]
    knock = L(ph=33, core=2, tilt=-10, dx=-0.6, arm=(-30, -60), barm=(200, 240), eye="wide")
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.09] * 6),
             ("Arc", arc, [0.12, 0.14, 0.12, 0.06, 0.14, 0.14]),
             ("Overcharge", over, [0.12, 0.12, 0.12, 0.12, 0.08, 0.14, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("KrnLeydenGolem", anims, outdir, scale=6)


# ================================================================== THUNDER BULL (T3, Anvil Smith / Lodestone Hound line)
def bull(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, gait=1.0, head=(0.0, 0.0), toss=0.0, horn_glow=1, ph=0, eye="open", snort=0,
         extra=None, dead=False, crouch=0.0, tail=0.0, dust=0):
    f = Fr()
    ca = math.radians(tilt)
    def R(x, y):  # rotate about the hind feet
        x = x + 12.0
        return (-12.0 + x * math.cos(ca) - y * math.sin(ca) + dx, x * math.sin(ca) + y * math.cos(ca) + dy)
    hipj = R(-9.5, -11.0 + crouch)
    shoj = R(4.5, -12.0 + crouch * 0.5)
    # far legs
    for i, (j, base) in enumerate(((hipj, -9.5), (shoj, 5.0))):
        ph_ = legs + i * math.pi + math.pi * 0.5
        lift = max(0.0, math.sin(ph_)) * 2.4 * gait
        fx_ = base + math.cos(ph_) * 3.6 * gait + dx + 1.5
        knee = (j[0] + (1.5 if i == 0 else -0.5), (j[1] - lift) * 0.5 - 1.0)
        tube(f.n, [j, knee, (fx_, -1.5 - lift)], [2.4, 1.8, 1.6], "1223", bias=-0.2)
        rect(f.n, fx_ - 1.6, -1.8 - lift, fx_ + 1.8, -lift, "1122")
    # chain tail with a sparking weight
    tb = R(-14.5, -17.0 + crouch)
    for k in range(6):
        a = math.radians(120 + tail - k * 5)
        f.u.put(*P(tb[0] + math.cos(a) * k * 1.1, tb[1] + math.sin(a) * k * 1.1), "4" if k % 2 else "3")
    te = (tb[0] + math.cos(math.radians(120 + tail - 25)) * 6.6, tb[1] + math.sin(math.radians(120 + tail - 25)) * 6.6)
    ell(f.u, te[0], te[1], 1.3, 1.3, IRON_HI)
    # body: heavy iron hull, hump over the shoulders
    ell(f.b, *R(-3.5, -15.5 + crouch * 0.7), 12.2, 6.6, IRON, ang=tilt, bias=0.1)
    ell(f.b, *R(-11.0, -15.0 + crouch), 5.0, 5.6, IRON, ang=tilt, bias=0.05)
    ell(f.b, *R(3.5, -18.5 + crouch * 0.5), 7.6, 6.2, IRON_L, ang=tilt - 8, bias=0.2)
    # riveted plate seams + a forge seam along the ribs
    for k in range(7):
        f.b.put(*P(*R(-12.0 + k * 3.0, -20.6 + crouch * 0.6 + abs(k - 4) * 0.7)), "6" if k % 2 else "5")
    line(f.b, *R(-13.0, -13.0 + crouch), *R(4.0, -14.5 + crouch * 0.5), "2")
    if not dead:
        for k in range(3):
            f.g.put(*P(*R(-6.0 + k * 3.0, -11.6 + crouch * 0.8)), "o" if k != 1 else "O")
        # lightning veins crawling through the hull plates
        for k, (x0, y0, x1, y1) in enumerate(((-12, -17, -6, -14), (-4, -19, 1, -15), (-9, -21, -3, -20))):
            q0, q1 = R(x0, y0 + crouch * 0.7), R(x1, y1 + crouch * 0.7)
            bolt(f.g, q0[0], q0[1], q1[0], q1[1], seed=k * 5 + ph % 2, jag=0.9, step=2.0, core="9", edge="8", halo=None)
    # v0.9 lineage (Anvil Smith): the smith's anvil strapped on the hump with a leather girth; (Lodestone Hound): the
    # hound's rusted magnetite hide and its horseshoe magnet, grown into a yoke across the shoulders
    an = R(-5.0, -22.6 + crouch * 0.6)
    # v0.10 (one parent, the Lodestone Hound): a raw lodestone boulder strapped on the hump (no anvil)
    stamp(f.b, lambda c: (ell(c, an[0], an[1] + 0.8, 4.6, 3.0, IRON_L, bias=0.15), c.put(*P(an[0] - 1.6, an[1] - 0.6), "6"),
                          c.put(*P(an[0] + 1.4, an[1] + 0.4), "3"), c.put(*P(an[0] + 2.4, an[1] + 1.6), "2")), ch="Z")
    g0, g1 = R(-6.0, -20.0 + crouch * 0.6), R(-7.4, -10.0 + crouch * 0.8)
    line(f.b, g0[0], g0[1], g1[0], g1[1], "t"); line(f.b, g0[0] + 1, g0[1], g1[0] + 1, g1[1], "T")
    mg = Fr()
    yk = R(5.0, -22.0 + crouch * 0.5)
    magnet(mg, yk[0], yk[1], s=1.15, glow=0 if dead else (2 if horn_glow >= 2 else 1), ph=ph)
    for k_, v_ in mg.b.px.items(): f.b.put(k_[0], k_[1], v_)
    for k_, v_ in mg.g.px.items(): f.g.put(k_[0], k_[1], v_)
    # head: low and blunt, ring through the nose, glowing nostrils, two lightning-rod horns
    hc = R(14.0 + head[0], -15.0 + crouch * 0.4 + head[1])
    hx, hy = hc
    hang = -toss
    def headf(c):
        ell(c, hx, hy, 4.4, 4.0, IRON_L, ang=hang, bias=0.3)
        sn = polar(hx, hy, 4.6, 25 + hang)
        ell(c, sn[0], sn[1], 2.8, 2.4, IRON_L, ang=hang, bias=0.15)
        c.put(*P(sn[0] + 1.6, sn[1] + 2.2), "5"); c.put(*P(sn[0] + 2.4, sn[1] + 2.8), "6"); c.put(*P(sn[0] + 1.0, sn[1] + 2.8), "4")
        line(c, hx - 2.0, hy - 1.0, hx + 2.6, hy - 2.2, "2")
    stamp(f.b, headf, ch="Z")
    sn = polar(hx, hy, 4.6, 25 + hang)
    if not dead:
        f.g.put(*P(sn[0] + 1.4, sn[1] - 0.2), "O"); f.g.put(*P(sn[0] + 2.2, sn[1] + 0.4), "o")
        if snort:
            for k in range(snort):
                f.g.put(*P(sn[0] + 4 + k * 1.5, sn[1] + 1 + (k % 2)), "4" if k > 1 else "5")
    tips = []
    for sd, layer in ((-1, f.u), (1, f.b)):
        b0 = polar(hx, hy, 3.4, -100 + hang + sd * 30)
        pts = [b0, polar(b0[0], b0[1], 4.0, -115 + hang + sd * 12), None]
        pts[2] = polar(pts[1][0], pts[1][1], 5.5, -50 + hang + sd * 10)
        def horn(c, pts=pts):
            tube(c, pts, [1.3, 1.0, 0.5], COPPER, bias=0.3)       # v0.8: copper horns
            cp = pts[1]
            c.put(*P(cp[0], cp[1]), "e"); c.put(*P(cp[0] + 1, cp[1]), "Q")
        if layer is f.b: stamp(f.b, horn, ch="Z")
        else: horn(f.u)
        tips.append(pts[2])
    # near legs
    for i, (j, base) in enumerate(((hipj, -10.5), (shoj, 4.0))):
        ph_ = legs + i * math.pi
        lift = max(0.0, math.sin(ph_)) * 2.6 * gait
        fx_ = base + math.cos(ph_) * 3.8 * gait + dx
        knee = (j[0] + (2.0 if i == 0 else 0.0), (j[1] - lift) * 0.5 - 1.0)
        def leg(c, j=j, knee=knee, fx_=fx_, lift=lift):
            tube(c, [j, knee, (fx_, -1.8 - lift)], [2.8, 2.0, 1.8], IRON, bias=0.35)
            rect(c, fx_ - 2.0, -2.2 - lift, fx_ + 2.2, -lift, "2345")
        stamp(f.b, leg, ch="Z")
    # eye: small, deep-set, under the brow
    ex, ey = hx + 1.6, hy - 1.0
    if eye == "open": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "9")
    elif eye == "wide": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "0"); f.g.put(*P(ex, ey - 1), "9")
    elif eye == "squint": f.g.put(*P(ex, ey), "8"); f.g.put(*P(ex + 1, ey), "8")
    elif eye == "dead": f.g.put(*P(ex, ey), "2")
    if not dead and horn_glow:
        for t in tips: f.g.put(*P(*t), "0")
        if horn_glow >= 2:
            bolt(f.g, tips[0][0], tips[0][1], tips[1][0], tips[1][1], seed=ph, jag=1.0, step=1.6, halo=None)
        if horn_glow >= 3:
            for t in tips: spark(f.g, t[0], t[1], 1)
        f.g.put(*P(*te), "9" if ph % 2 else "8")
    if dust:
        rnd = random.Random(ph)
        for k in range(dust * 3):
            f.g.put(*P(dx - 18 + rnd.uniform(-4, 22), -rnd.uniform(0, 3 + dust)), "4" if k % 3 else "9")
    if extra: extra(f, tips, (hx, hy))
    return f.done()


def bull_corpse():
    f = Fr()
    ell(f.b, -3, -5.0, 14.0, 5.0, IRON, bias=0.2)
    ell(f.b, 2, -8.0, 7.0, 3.4, IRON_L, bias=0.2, vmax=0.3)
    ell(f.b, 13.5, -4.0, 4.4, 3.6, IRON_HI, bias=0.2)
    for sd in (-1, 1):
        line(f.b, 13 + sd * 2, -7, 16 + sd * 3, -12, "5")
    for x in (-12, -6, 0, 5):
        rect(f.b, x - 1, -2, x + 2, 0, "2345")
    for k in range(6): f.b.put(-17 - k, -1 - (k % 2), "4" if k % 2 else "3")
    f.g.put(-6, -4, "a"); f.g.put(-3, -4, "a")
    f.g.put(15, -5, "2")
    return f.done()


def build_bull(outdir):
    B = bull
    idle = [B(gait=0.0, ph=0), B(gait=0.0, ph=1, dy=0.5, head=(0, 0.5), crouch=0.4, tail=8),
            B(gait=0.0, ph=2, dy=0.6, head=(0, 0.6), crouch=0.5, tail=14, horn_glow=2), B(gait=0.0, ph=3, dy=0.2, tail=6)]
    run = [B(legs=i * math.pi / 3, gait=1.0, dy=-1.0 * abs(math.sin(i * math.pi / 3)), tilt=-2 * math.cos(i * math.pi / 3),
             head=(0.6, 1.2), ph=i + 4, tail=-14 + 8 * (i % 2), horn_glow=1 + (i % 2)) for i in range(6)]
    # GORE: lower the head, brace, HOOK UP (3: horns hit, smear), hold, recover
    def gore_fx(f, tips, h):
        for t in tips:
            spark(f.g, t[0], t[1], 2)
        for k in range(3):
            line(f.g, h[0] + 4 + k * 1.2, h[1] + 4 - k * 3, h[0] + 7 + k * 1.2, h[1] + 1 - k * 3, "98")
    gore = [B(head=(-1.0, 3.0), crouch=1.4, toss=-20, ph=10, eye="squint", tail=20, snort=3),
            B(head=(-2.0, 4.0), crouch=2.0, toss=-28, ph=11, eye="wide", tail=26, dx=-1.0, horn_glow=2, snort=4),
            B(head=(1.5, 1.5), crouch=0.5, toss=10, ph=12, eye="wide", dx=1.5, horn_glow=3, legs=1.2, gait=0.4),
            B(head=(3.0, -2.5), crouch=-0.5, toss=40, ph=13, eye="wide", dx=2.5, horn_glow=3, legs=1.6, gait=0.4, extra=gore_fx),
            B(head=(2.6, -2.0), crouch=-0.3, toss=34, ph=14, eye="open", dx=2.5, horn_glow=2, legs=1.6, gait=0.4),
            B(head=(1.0, 0.5), toss=10, ph=15, eye="open", dx=1.5, horn_glow=1),
            B(head=(0.0, 0.0), ph=16, eye="open", dx=0.5, horn_glow=1)]
    # STAMPEDE: paw the floor twice, CHARGE (frames 2-6: forward motion, studs dropped), skid to a stop
    stamp_ = [B(head=(-1.0, 3.0), toss=-24, crouch=1.0, legs=2.2, gait=0.6, ph=20, eye="squint", snort=4, dust=1, tail=24),
              B(head=(-1.2, 3.4), toss=-26, crouch=1.4, legs=3.6, gait=0.6, ph=21, eye="wide", snort=4, dust=2, tail=30, horn_glow=2)]
    for i in range(5):
        stamp_.append(B(head=(1.5, 3.5), toss=-24, crouch=1.0, legs=i * math.pi / 2.5, gait=1.3, tilt=-3,
                        dy=-1.0 * abs(math.sin(i * math.pi / 2.5)), ph=22 + i, eye="wide", horn_glow=3, dust=2, tail=-30))
    stamp_.append(B(head=(0.5, 2.0), toss=-12, crouch=1.6, tilt=4, legs=0.8, gait=0.3, ph=28, eye="open", dust=3, horn_glow=2, tail=10))
    death = [B(head=(-1, -2), toss=30, tilt=-10, ph=30, eye="wide", horn_glow=3, tail=40),
             dim_glow(B(head=(0, 2), toss=-10, tilt=-16, dy=2.0, ph=31, eye="dead", dead=True, legs=1.0)),
             dim_glow(grounded(B(head=(1, 4), toss=-20, tilt=-26, dy=5.0, ph=32, eye="dead", dead=True, legs=2.0, crouch=3))),
             dim_glow(bull_corpse())]
    knock = B(head=(-1, -1.5), toss=24, tilt=-10, ph=33, eye="wide", horn_glow=2, tail=30, dx=-1)
    anims = [("Idle", idle, [0.26, 0.2, 0.26, 0.2]), ("Run", run, [0.08] * 6),
             ("Gore", gore, [0.16, 0.16, 0.06, 0.08, 0.16, 0.14, 0.14]),
             ("Stampede", stamp_, [0.14, 0.14, 0.08, 0.08, 0.08, 0.08, 0.08, 0.2])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.45], knock)
    sheet("KrnThunderBull", anims, outdir, scale=5, remap=BULL_RUST)


# ================================================================== STORM ORRERY (T3, Stormcaller / Leyden Golem line, flying)
def sat_ball(c, x, y, r=1.6, lit=True):
    for yy in range(int(y - r) - 1, int(y + r) + 2):
        for xx in range(int(x - r) - 1, int(x + r) + 2):
            d = math.hypot(xx - x, yy - y) / r
            if d <= 1.0: c.put(xx, yy, ("0" if d < 0.5 else "9") if lit else ("4" if d < 0.5 else "3"))
            elif d <= 1.45 and lit: c.put(xx, yy, "8", over=False)


def ring_pts(cx, cy, rx, ry, ang, n=60):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        u, v = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + u * ca - v * sa, cy + u * sa + v * ca, math.sin(a)))
    return out


def orrery(dx=0.0, dy=0.0, spin=0.0, tilt=-14.0, core=1.0, ph=0, sats=2, sat_r=1.6, eye="open", hover=7.0, extra=None, dead=False,
           ring_open=0.0, pend=0.0):
    f = Fr()
    cx, cy = dx, -hover - 15.0 + dy
    # pendulum weight on a short chain under the sphere (sways)
    pb = (cx + pend * 0.8, cy + 13.5)
    for k in range(4):
        f.u.put(*P(cx + pend * 0.2 * k, cy + 9 + k), "4" if k % 2 else "3")
    poly(f.u, [(pb[0] - 2, pb[1] - 1.5), (pb[0] + 2, pb[1] - 1.5), (pb[0], pb[1] + 2.5)], "4",
         shade=lambda X, Y: "5" if X < pb[0] else "3")
    # back halves of the rings (behind the core)
    R1 = 12.5 + ring_open
    meridian_rx = 9.5 * abs(math.cos(math.radians(spin))) + 1.2
    back, front = Canvas(), Canvas()
    for (x, y, sv) in ring_pts(cx, cy, meridian_rx, 10.5 + ring_open * 0.5, 0, n=70):
        c = back if (math.cos(math.radians(spin)) * (x - cx) > 0) else front
        c.put(*P(x, y), "Q" if (y - cy) < 0 else "q")
    for (x, y, sv) in ring_pts(cx, cy, R1, 4.4 + ring_open * 0.3, tilt, n=80):
        c = back if sv < 0 else front
        c.put(*P(x, y), ("E" if (x - cx) < -4 else "e") if sv >= 0 else "Q")
        c.put(*P(x, y + 1), "q" if sv >= 0 else "1", over=False)
    for (x, y), v in back.px.items(): f.n.put(x, y, v)
    # v0.9 lineage (Leyden Golem): the sphere is a Leyden jar of dark glass inside the iron frame, copper-banded
    def jar_shade(nu, nv, d, l, ch, x, y):
        if d > 0.72: return "V" if (nu + nv) < -0.4 else ("v" if (nu + nv) < 0.5 else "N")
        if d > 0.55 and (nu + nv) < -0.6: return "W"
        return "n"
    ell(f.b, cx, cy, 5.6, 5.6, CLOTH, shader=jar_shade)
    line(f.b, cx - 4.6, cy + 3.0, cx + 4.6, cy + 3.0, "eQ")
    # the sphere's iron frame: an equator band and poles
    ell(f.b, cx, cy, 6.2, 6.2, IRON, bias=0.15, shader=lambda nu, nv, d, l, ch, x, y: None if d < 0.55 else ch)
    # rivets on the frame
    for a in (200, 250, 300, 340, 30):
        f.b.put(*P(cx + math.cos(math.radians(a)) * 5.4, cy + math.sin(math.radians(a)) * 5.4), "5")
    # top spire with a forked tip, bottom collar
    def spire(c):
        line(c, cx, cy - 6.4, cx, cy - 13.0, "4")
        line(c, cx + 1, cy - 6.4, cx + 1, cy - 11.0, "2")
        c.put(*P(cx - 1, cy - 13.6), "5"); c.put(*P(cx + 1, cy - 13.6), "5")
        c.put(*P(cx - 1, cy - 9.0), "e"); c.put(*P(cx + 1, cy - 9.0), "Q")
        rect(c, cx - 2, cy + 5.6, cx + 2, cy + 7.2, "2345")
    stamp(f.b, spire, ch="Z")
    # v0.9 lineage (Stormcaller): the caller's storm-blue hood draped over the top of the jar, its copper coil antennae
    # v0.10 (one parent, the Leyden Golem): the golem's iron jar lid with its two terminal posts capping the sphere
    def lid(c):
        rect(c, cx - 4.0, cy - 6.6, cx + 4.0, cy - 5.0, "2345")
        for sd in (-1, 1):
            line(c, cx + sd * 2.4, cy - 6.6, cx + sd * 3.4, cy - 9.4, "4")
            c.put(*P(cx + sd * 3.6, cy - 10.0), "6")
    stamp(f.b, lid, ch="Z")
    if not dead:
        f.g.put(*P(cx - 3.6, cy - 10.6), "9"); f.g.put(*P(cx + 3.6, cy - 10.6), "9")
    # front halves of the rings over the body
    for (x, y), v in front.px.items(): f.g.put(x, y, v)
    # core of lightning inside the frame
    if not dead:
        r = 4.0 * core
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx + 0.3, y - cy + 0.3) / max(r, 0.1)
                if d <= 1.0: f.g.put(x, y, "0" if d < 0.45 else "9" if d < 0.8 else "8")
        rnd = random.Random(ph * 3 + 1)
        for k in range(2):
            a = rnd.uniform(0, 6.28)
            bolt(f.g, cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6, cx + math.cos(a) * 6.0, cy + math.sin(a) * 6.0,
                 seed=ph * 7 + k, jag=0.7, step=1.5, halo=None)
        f.g.put(*P(cx, cy - 14.4), "0")
        if core >= 1.4: crackle(f.g, cx, cy - 14.4, ph, r=3, seed=3)
        # the "eye": a dark pupil-slit in the core, looking forward
        if eye in ("open", "wide"):
            f.g.put(*P(cx + 1.5, cy - 0.5), "7"); f.g.put(*P(cx + 1.5, cy + 0.5), "7")
            if eye == "wide": f.g.put(*P(cx + 1.5, cy - 1.5), "7")
    else:
        ell(f.b, cx, cy, 3.4, 3.4, IRON, bias=-0.2)
    # satellites riding the outer ring
    for k in range(sats):
        a = math.radians(spin * 1.6 + k * 360.0 / max(1, sats) + 30)
        u, v = R1 * math.cos(a), (4.4 + ring_open * 0.3) * math.sin(a)
        ca_, sa_ = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        x, y = cx + u * ca_ - v * sa_, cy + u * sa_ + v * ca_
        if math.sin(a) < 0 and not dead:
            sat_ball(f.u, x, y, sat_r, lit=True)
        else:
            sat_ball(f.g, x, y, sat_r, lit=not dead)
    if not dead:
        f.g.put(*P(pb[0], pb[1] + 2), "9" if ph % 2 else "8")
    if extra: extra(f, (cx, cy), R1)
    return f.done()


def orrery_corpse():
    f = Fr()
    for (x, y, sv) in ring_pts(0, -2.5, 13, 2.6, 0):
        f.b.put(*P(x, y), "e" if x < 0 else "Q")
    ell(f.b, 1, -5, 5.5, 4.5, IRON, bias=0.1)
    ell(f.b, 1, -5, 2.6, 2.4, IRON, bias=-0.2)
    line(f.b, 6, -7, 12, -11, "4")
    sat_ball(f.b, -9, -1.6, 1.4, lit=False)
    sat_ball(f.b, 15, -1.6, 1.4, lit=False)
    return f.done()


def build_orrery(outdir):
    O = orrery
    idle = [O(spin=0, ph=0, pend=0), O(spin=22, ph=1, dy=-0.6, pend=0.8), O(spin=44, ph=2, dy=-1.0, pend=1.2, core=1.1),
            O(spin=66, ph=3, dy=-0.5, pend=0.6)]
    run = [O(dx=0.4, spin=i * 30, tilt=-8, ph=4 + i, dy=[-0.2, -0.8, -1.2, -0.8, -0.2, 0.0][i], pend=-1.5 - 0.8 * (i % 2)) for i in range(6)]
    # FLING: core swells, a satellite swings to the front, HURL (3: release ahead), recover
    def hurl(f, c, R1):
        sat_ball(f.g, c[0] + R1 + 4, c[1] - 1, 2.4)
        for k in range(3):
            line(f.g, c[0] + R1 - 3 - k * 2, c[1] - 2 + k, c[0] + R1, c[1] - 2 + k, "8")
        spark(f.g, c[0] + R1 + 4, c[1] - 1, 2)
    fling = [O(spin=10, core=1.1, ph=10, tilt=-18, eye="open"),
             O(spin=40, core=1.3, ph=11, tilt=-24, eye="wide", sats=2, sat_r=2.0),
             O(spin=70, core=1.5, ph=12, tilt=-28, eye="wide", sats=2, sat_r=2.2, dx=-0.8),
             O(spin=100, core=1.2, ph=13, tilt=-6, eye="wide", sats=1, dx=0.8, extra=hurl),
             O(spin=120, core=1.0, ph=14, tilt=-10, sats=1, eye="open"),
             O(spin=140, core=1.0, ph=15, tilt=-14, sats=2, eye="open")]
    # ORBIT: rings spin up and open, the core flares, RELEASE (4: three satellites fly out to orbit), settle
    def burst(f, c, R1):
        for k in range(3):
            a = math.radians(k * 120 + 20)
            x, y = c[0] + math.cos(a) * (R1 + 6), c[1] + math.sin(a) * 5 + 4
            sat_ball(f.g, x, y, 2.0)
            line(f.g, c[0] + math.cos(a) * (R1 - 2), c[1] + math.sin(a) * 3, x, y, "8")
    orbit = [O(spin=0, core=1.1, ph=20, eye="open", ring_open=0.0),
             O(spin=45, core=1.3, ph=21, eye="wide", ring_open=0.8, sats=3),
             O(spin=100, core=1.5, ph=22, eye="wide", ring_open=1.6, sats=3, sat_r=1.9),
             O(spin=160, core=1.7, ph=23, eye="wide", ring_open=2.4, sats=3, sat_r=2.1, dy=-1.0),
             O(spin=220, core=1.8, ph=24, eye="wide", ring_open=3.0, sats=0, dy=-1.4, extra=burst),
             O(spin=260, core=1.3, ph=25, eye="wide", ring_open=1.6, sats=0, dy=-0.8),
             O(spin=290, core=1.1, ph=26, eye="open", ring_open=0.6, sats=1),
             O(spin=320, core=1.0, ph=27, eye="open", sats=2)]
    death = [O(spin=20, core=1.8, ph=30, eye="wide", tilt=-30, ring_open=2.0),
             dim_glow(O(spin=40, core=0.8, ph=31, tilt=-40, dy=4.0, eye="dead", sats=1)),
             O(spin=60, dead=True, tilt=-50, hover=1.0, sats=2),
             orrery_corpse()]
    knock = O(spin=10, core=1.4, ph=33, eye="wide", tilt=-30, dx=-0.6)
    anims = [("Idle", idle, [0.2, 0.2, 0.2, 0.2]), ("Run", run, [0.08] * 6),
             ("Fling", fling, [0.12, 0.14, 0.12, 0.06, 0.14, 0.14]),
             ("Orbit", orbit, [0.12, 0.12, 0.12, 0.12, 0.08, 0.14, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.45], knock)
    sheet("KrnStormOrrery", anims, outdir, scale=5)


# ================================================================== TIMING.md + contact sheet
MONSTERS = ["KrnRivetImp", "KrnSparkBeetle", "KrnCoilWisp", "KrnAnvilSmith", "KrnLodeHound", "KrnStormcaller", "KrnLeydenGolem",
            "KrnForgeColossus", "KrnThunderBull", "KrnStormHerald", "KrnStormOrrery"]
TIER = {"KrnRivetImp": "T1", "KrnSparkBeetle": "T1", "KrnCoilWisp": "T1 (flying)", "KrnAnvilSmith": "T2", "KrnStormcaller": "T2",
        "KrnForgeColossus": "T3", "KrnStormHerald": "T3 (flying)", "KrnLodeHound": "T2", "KrnLeydenGolem": "T2",
        "KrnThunderBull": "T3", "KrnStormOrrery": "T3 (flying)"}

# (anim, event, frame index, spawn point relative to the feet or "-")
EVENTS = {
    "KrnRivetImp": [("Bonk", "smear: hammer coming down", 2, "-"),
                    ("Bonk", "HIT: hammer head on the floor (+1 static)", 3, "(12, -1)"),
                    ("Rivets", "rivets tossed up out of the pouch", 1, "-"),
                    ("Rivets", "RELEASE: bat 3 FxKrnRivet in a fan (each lands as a FxKrnStud node)", 3, "(10, -12)")],
    "KrnSparkBeetle": [("Zap", "antennae charged", 2, "-"),
                       ("Zap", "RELEASE: FxKrnSpark from the antenna tips (+1 static)", 3, "(14, -9)"),
                       ("Rush", "curled into ball lightning: start forward motion + contact damage", 1, "body centre (0, -5)"),
                       ("Rush", "uncurls: stop motion, damage off", 6, "-")],
    "KrnCoilWisp": [("Spark", "core swells", 2, "-"),
                    ("Spark", "RELEASE: FxKrnMote from the cage front (+1 static)", 3, "(7, -9)"),
                    ("Pulse", "cage opening, arcs reaching out", 2, "-"),
                    ("Pulse", "DISCHARGE: FxKrnRing static ring on the floor under the wisp", 4, "(0, 0)")],
    "KrnAnvilSmith": [("Hammer", "smear", 2, "-"),
                      ("Hammer", "IMPACT: hammer head on the floor; FxKrnSurge sent along the floor (+1 static)", 3, "head (18, -1), surge (20, 0)"),
                      ("Temper", "rod planted upright in front", 1, "-"),
                      ("Temper", "rod hammered home: spawn FxKrnRod node", 3, "(11, 0)"),
                      ("Temper", "lightning answers: gain an iron plate (FxKrnPlates)", 4, "-")],
    "KrnStormcaller": [("Orb", "ball lightning gathered in the palm", 2, "palm (-6, -14)"),
                       ("Orb", "RELEASE: FxKrnBall from the thrust palm (+1 static)", 3, "(11, -14)"),
                       ("Call", "staff raised, charging", 1, "-"),
                       ("Call", "CALL: 3 FxKrnStrike marks at / around the hero (telegraph 0.6 s, then the bolt)", 2, "hero"),
                       ("Call", "lowers staff", 6, "-")],
    "KrnForgeColossus": [("Slam", "fists at the top", 2, "-"),
                         ("Slam", "smear", 3, "-"),
                         ("Slam", "IMPACT: FxKrnQuake ring in front (+1 static)", 4, "(17, 0)"),
                         ("Cage", "rods overloaded", 2, "-"),
                         ("Cage", "IMPACT: FxKrnQuake under itself + 4 FxKrnRod burst up in a box around it", 5,
                          "quake (0, 0); rods (+-34, +-14) from the feet")],
    "KrnStormHerald": [("Lance", "smear (thrust)", 2, "-"),
                       ("Lance", "RELEASE: FxKrnLance from the lance tip (+1 static)", 3, "(28, -19)"),
                       ("Thunder", "lance raised, halo swelling", 2, "-"),
                       ("Thunder", "CALL: FxKrnCloud forms over the hero (strikes 3 times)", 4, "hero")],
    "KrnLodeHound": [("Lunge", "springs: forward motion starts", 2, "-"),
                     ("Lunge", "BITE: jaws snap shut (+1 static)", 3, "jaws (19, -12)"),
                     ("Howl", "howl starts: FxKrnPull on the hound, pull the hero in (frames 1-6)", 1, "(0, 0)"),
                     ("Howl", "howl ends", 7, "-")],
    "KrnLeydenGolem": [("Arc", "charge climbs the coil arm", 2, "-"),
                       ("Arc", "RELEASE: 2 FxKrnJolt from the clamp hand (+1 static)", 3, "(14, -15)"),
                       ("Overcharge", "terminals arcing", 1, "-"),
                       ("Overcharge", "DISCHARGE: FxKrnRing under it; every Kaurn ally within 100 px fills its static", 4, "(0, 0)")],
    "KrnThunderBull": [("Gore", "head drives up (smear)", 2, "-"),
                       ("Gore", "HIT: horns hook up (+1 static)", 3, "horns (19, -12) .. tips (29, -23)"),
                       ("Stampede", "CHARGE: forward motion + body hit; FxKrnStud dropped on frames 2, 4, 6", 2, "head (14, -10); studs (0, 0)"),
                       ("Stampede", "skids to a stop", 7, "-")],
    "KrnStormOrrery": [("Fling", "a satellite swings to the front", 2, "-"),
                       ("Fling", "RELEASE: FxKrnOrb from the ring front (+1 static)", 3, "(16, -21)"),
                       ("Orbit", "rings spin up", 2, "-"),
                       ("Orbit", "RELEASE: 3 FxKrnSatellite orbit the orrery for 4 s, then fly outward", 4, "orbit r 26 x 10 around the feet")],
}


V08_NOTES = [
    "## v0.8 art pass", "",
    "Each evolution line now has its own material (sheet-wide remaps, see lifted()); strike geometry is unchanged, so every",
    "sync frame / spawn point / hitbox above still holds.",
    "- KrnRivetImp: brick-red imp hide, copper skullcap, a whip tail with a spark tip.",
    "- KrnAnvilSmith: sweat-tanned skin, a full anvil strapped across his back (horn behind the shoulders), forge-hot studs.",
    "- KrnForgeColossus: blued steel with two copper hoops round the hull.",
    "- KrnLodeHound: rusted magnetite. KrnThunderBull: storm-cloud hide, a thunderhead mane on the hump, copper horns.",
    "- KrnSparkBeetle: copper shell. KrnStormcaller: storm-blue cloth and a thundercloud stole (luminance 59 -> 75).",
    "- New FxKrnStaticSpark (discharged static pips; was the Beetle's FxKrnSpark) and FxKrnSlagRod (death rod; was the",
    "  Smith/Colossus FxKrnRod), same cell/origin as the sheets they replace.", "",
    "## v0.9 lineage pass",
    "",
    "Shared motifs: imp_tail (Rivet Imp), elytra + coil_antennae (Spark Beetle), the coil cage (Coil Wisp), the Leyden jar,",
    "magnet() (Lodestone Hound), anvil_shape (Anvil Smith). Strike points, sync frames and hitboxes unchanged.",
    "- KrnAnvilSmith (Imp): the imp's brick-red hide, pointed ear, copper skullcap with rivet horns and spark-tipped tail.",
    "- KrnLodeHound (Imp + Beetle): imp-red hide, a copper wing-case saddle and the beetle's coil antennae.",
    "- KrnStormcaller (Beetle + Wisp): copper beetle-shell hood, wing-case mantle and coil antennae; the wisp's coil cage on",
    "  the staff head. KrnLeydenGolem (Wisp): copper coils round a glass jar of lightning.",
    "- KrnForgeColossus (Smith + Leyden): anvil fists and the smith's apron; a Leyden jar of lightning set in the chest.",
    "- KrnThunderBull (Smith + Hound): oxide-red hide, the hound's magnet as a shoulder yoke, the smith's anvil on the hump.",
    "- KrnStormHerald (Stormcaller + Hound): the caller's storm-blue robe and cloud skirt, hound rust iron, the magnet",
    "  behind its mask with the halo arcing between the poles.",
    "- KrnStormOrrery (Stormcaller + Leyden): the sphere is a glass Leyden jar; the caller's blue hood and antennae on top.",
    "- All monster cells now have an even height (a spare top row); feet stay 2 rows above the bottom.",
    "",
    "## v0.10 final art review",
    "",
    "- KrnForgeColossus: warm soot-stained forge iron (FORGE_IRON), red-hot seams across the hull, a hot glowing anvil-fist",
    "  face and a copper helm with rivet horns (the Smith's colours and heat), the Leyden jar kept in the chest.",
    "- Lifts: KrnAnvilSmith hide and leather (SMITH_SKIN), KrnThunderBull oxide hide (BULL_RUST).",
    "- FxKrnPlates: bigger hot-copper plates with steel rims and lit rivets, readable on a dark floor.",
    ""]


def write_timing(outdir):
    L = ["# Kaurn, the Storm Forge: sprite timing", "",
         "Generated by `tools/sprites/kaurn_rigs.py`. Frame indices are 0-based within the anim; `t` is the time",
         "from the start of the anim to the start of that frame. Monsters face right.",
         "Monster sheets: feet = (cellW//2, cellH-2). Spawn points are in pixels relative to the feet (x right, y up NEGATIVE),",
         "facing right; mirror x when flipped. In code: Kit.AddEffect(offsetX = x, offsetY = -y).", "",
         "## Monster sheets", "", "| Sheet | Tier | Cell (w x h) | Feet | Idle bounds (w x h, incl. hover) | Anims (frames) |",
         "|---|---|---|---|---|---|"]
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, TIER[n], cw, ch, cw // 2, ch - 2, b["idle"][0], b["idle"][1],
                 ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "Size limits (v0.7): T1 16 h x 20 w, T2 26 x 28, T3 40 x 42; all Idle frames are inside them.", "",
          "Evolution tree (v0.10: a binary tree, every evolution has exactly one parent; see the v0.10 notes at the end).", "",
          "## Move anims: sync frames", ""]
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
            L.append("| %d | %.2f | %s | %s |" % (fi, sum(d[:fi]), ev, sp))
            nxt = [e for e in EVENTS[n] if e[0] == an]
            if (an, ev, fi, sp) == nxt[-1]: L.append("")
    L += ["Every attack has at least two wind-up frames before its first event. Death plays once and ends on the corpse;",
          "Dead is that same corpse frame (lightning goes out, forge seams go to ash). Every Kaurn monster leaves a FxKrnRod",
          "(slag rod, a conduction node) where it dies.", "",
          "## FX sheets", "", "| Sheet | Cell (w x h) | Origin | Anims (frames, total s) | Notes |", "|---|---|---|---|---|"]
    for n in FXN:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"]), FX_NOTES[n]))
    L += ["", "## Icons and portrait", "", "| Sheet | Cell | Anims |", "|---|---|---|",
          "| IconKrnChainSpark | 16 x 16, feet (8, 15) | Idle 2 (spell icon) |",
          "| IconKrnLightningRod | 16 x 16, feet (8, 15) | Idle 2 (artifact icon + the floating token) |",
          "| IconKrnChainSparkBubble | 34 x 41 | Bubble 2 (parchment card) |",
          "| IconKrnLightningRodBubble | 34 x 41 | Bubble 2 |",
          "| IconKrnLightningRodHud | 11 x 7 | Hud 1 |",
          "| DeityKaurn | 29 x 24, feet (14, 23) | Idle 4 (opaque) |"]
    L += [""] + V08_NOTES
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(outdir, "TIMING.md"))


def tree_sheet(path, S=4):
    """All monsters' first Idle frame at S x, one row per tier, labelled by tier."""
    from PIL import Image, ImageDraw
    rows = [["KrnRivetImp", "KrnSparkBeetle", "KrnCoilWisp"], ["KrnAnvilSmith", "KrnLodeHound", "KrnStormcaller", "KrnLeydenGolem"],
            ["KrnForgeColossus", "KrnThunderBull", "KrnStormHerald", "KrnStormOrrery"]]
    crops = []
    for r in rows:
        cr = []
        for n in r:
            b = BUILT[n]; img, man = b["img"], b["man"]
            cw, chh = man["cellW"], man["cellH"]
            fi = man["anims"][0]["frames"][0]
            x0, y0 = (fi % man["cols"]) * cw, (fi // man["cols"]) * chh
            c = img.crop((x0, y0, x0 + cw, y0 + chh)); bb = c.getbbox()
            cr.append(c.crop((bb[0] - 2, bb[1] - 2, bb[2] + 2, chh)))
        crops.append(cr)
    W = max(sum(c.size[0] + 6 for c in r) for r in crops) + 14
    H = sum(max(c.size[1] for c in r) + 8 for r in crops)
    bg = Image.new("RGBA", (W * S, H * S), (28, 26, 32, 255)); d = ImageDraw.Draw(bg)
    y = 0
    for t, r in enumerate(crops):
        h = max(c.size[1] for c in r)
        d.text((4, y * S + 4), "T%d" % (t + 1), fill=(200, 200, 210, 255))
        d.line([(14 * S, (y + h + 3) * S), (W * S, (y + h + 3) * S)], fill=(60, 56, 64, 255))
        x = 14
        for c in r:
            bg.alpha_composite(c.resize((c.size[0] * S, c.size[1] * S), Image.NEAREST), (x * S, (y + h - c.size[1] + 3) * S))
            x += c.size[0] + 6
        y += h + 8
    bg.convert("RGB").save(path)
    print("tree sheet", path)


def contact_sheet(outdir, S=6, path=None, portrait=False):
    from PIL import Image
    cells = []
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; img, man = b["img"], b["man"]
        cw, chh = man["cellW"], man["cellH"]
        fi = man["anims"][0]["frames"][0]
        x0, y0 = (fi % man["cols"]) * cw, (fi // man["cols"]) * chh
        c = img.crop((x0, y0, x0 + cw, y0 + chh))
        bb = c.getbbox()
        cells.append(c.crop((bb[0] - 2, 0, bb[2] + 2, chh)))
    if portrait and "DeityKaurn" in BUILT:
        p = BUILT["DeityKaurn"]["img"].crop((0, 0, 29, 24))
        cells.append(p)
    H = max(c.size[1] for c in cells)
    W = sum(c.size[0] for c in cells) + 3 * len(cells) + 3
    bg = Image.new("RGBA", (W * S, (H + 2) * S), (28, 26, 32, 255))
    x = 3
    for i, c in enumerate(cells):
        yoff = H - c.size[1] if not (portrait and i == len(cells) - 1) else (H - 24) // 2
        bg.alpha_composite(c.resize((c.size[0] * S, c.size[1] * S), Image.NEAREST), (x * S, yoff * S))
        x += c.size[0] + 3
    out = path or os.path.join(outdir, "contact_idle.png")
    bg.convert("RGB").save(out)
    print("contact sheet", out)


# ================================================================== main (extended below)
JOBS = [("KrnRivetImp", build_imp), ("KrnSparkBeetle", build_beetle), ("KrnCoilWisp", build_wisp), ("KrnAnvilSmith", build_smith), ("KrnStormcaller", build_caller), ("KrnForgeColossus", build_colossus), ("KrnStormHerald", build_herald), ("KrnLodeHound", build_hound), ("KrnLeydenGolem", build_leyden), ("KrnThunderBull", build_bull), ("KrnStormOrrery", build_orrery)]


# ==== v0.10 tree BEGIN (generated block, kept in one place)
# ================================================================== v0.10: the binary tree (3 -> 6 -> 12, one parent each)
# Tree: RivetImp -> AnvilSmith, WireGremlin; SparkBeetle -> LodeHound, Stormcaller; CoilWisp -> LeydenGolem, ArcLantern
#       AnvilSmith -> ForgeColossus, Forgemaster; WireGremlin -> WireWyvern, FuseSapper; LodeHound -> ThunderBull, PolarityWarg
#       Stormcaller -> StormHerald, ScarabMagus; LeydenGolem -> StormOrrery, VoltaicPile; ArcLantern -> TeslaSpire, StaticMoth
PALETTE.update({
    'b': (0x16, 0x33, 0x31), 'B': (0x25, 0x55, 0x4c), 'c': (0x3c, 0x86, 0x72), 'C': (0x74, 0xc4, 0xa2),    # verdigris (Wire Wyvern)
    'r': (0x3e, 0x30, 0x12), 'R': (0x7a, 0x5e, 0x1e), 'p': (0xb8, 0x92, 0x34), 'P': (0xec, 0xd0, 0x74),    # brass (Arc Lantern line, Sapper)
    'G': (0x26, 0x1a, 0x3a), 'F': (0x42, 0x2c, 0x60), 'X': (0x66, 0x4a, 0x92), 'x': (0x9a, 0x7e, 0xc8),    # storm violet (Scarab Magus)
    'm': (0x30, 0x2c, 0x30), 's': (0x56, 0x4e, 0x52), 'S': (0x84, 0x7a, 0x78), 'A': (0xb4, 0xa8, 0x9c),    # moth-dust ash (Static Moth)
})
BRASS = "rRpP"
VERDI = "bBcC"
VIOLET_CLOTH = {"n": "F", "N": "F", "v": "X", "V": "x"}
MOTH = "msSA"
IMP_RED = {"k": "@", "g": "#", "h": "e", "1": "2"}   # the Rivet Imp's red hide, lifted a step for the bigger bodies
MASTER_SKIN = {"k": "@", "g": "#", "h": "e", "1": "2"}   # Forgemaster: the imp/smith red hide, lifted
WARG_STEEL = {"1": "<", "2": ">", "3": "[", "4": "]", "5": "{"}       # Polarity Warg: blued magnetite steel


def bat_wing(f, layer, sx, sy, ang, span=1.0, flap=0.0, far=False, ribs=None, fill=COPPER):
    """The Wire Gremlin's copper-foil bat wing (Gremlin -> Wire Wyvern / Fuse Sapper): an iron arm bone up-back to the
    wrist, three finger ribs, a scalloped copper membrane between them. ang: arm direction (deg); flap: + = downstroke."""
    c = getattr(f, layer)
    a = ang + flap
    w = polar(sx, sy, 5.0 * span, a)
    R = 7.0 * span
    # a broad fan from the wrist, sweeping from along the arm round towards the body, scalloped between the ribs
    angs = [a - 18 + k * 21 for k in range(5)]
    tips = [polar(w[0], w[1], R * (1.0 if k % 2 == 0 else 0.72), angs[k] + flap * 0.25) for k in range(5)]
    root = polar(sx, sy, 3.6 * span, a + 118)
    pts = [(sx, sy), w] + tips + [root]
    tips = tips[0::2]
    lo = 0.6 if far else 0.0
    def sh(X, Y):
        l = -((X - w[0]) * 0.5 + (Y - w[1]) * 0.8) / (8.0 * span) - 0.05 - lo
        return pick(fill, l)
    poly(c, pts, fill[1], shade=sh)
    rc = ribs or (fill[0] if far else fill[0])
    for t in tips:
        e = (w[0] + (t[0] - w[0]) * 0.8, w[1] + (t[1] - w[1]) * 0.8)
        line(c, w[0], w[1], e[0], e[1], rc)
    line(c, sx, sy, w[0], w[1], "2" if far else "4")
    c.put(*P(*w), "3" if far else "5")
    return w, tips


def lantern_body(f, cx, cy, s=1.0, core=1.0, ph=0, eye="open", dead=False, door=0.0, handle=True, layer="b"):
    """The Arc Lantern's brass carriage lantern (Lantern -> Tesla Spire / Static Moth): pointed roof with a ring handle,
    dark glass panes in a brass frame, the wisp's ball-lightning core inside. Returns the glass centre."""
    c = getattr(f, layer)
    w, h = 4.4 * s, 4.8 * s
    def body(cc):
        # roof
        poly(cc, [(cx - w - 0.6, cy - h), (cx + w + 0.6, cy - h), (cx + 1.0, cy - h - 3.6 * s), (cx - 1.0, cy - h - 3.6 * s)], "R",
             shade=lambda X, Y: "P" if X < cx - 1 and Y < cy - h - 1 else ("p" if X < cx + 1 else "R"))
        line(cc, cx - w - 0.6, cy - h, cx + w + 0.6, cy - h, "r")
        if handle:
            for k in range(10):
                a = 2 * math.pi * k / 10
                cc.put(*P(cx + 1.3 * s * math.cos(a), cy - h - 5.0 * s + 1.2 * s * math.sin(a)), "p" if k < 5 else "R")
        # glass box
        for y in range(int(math.floor(cy - h + 1)), int(math.ceil(cy + h - 1)) + 1):
            for x in range(int(math.floor(cx - w)), int(math.ceil(cx + w)) + 1):
                cc.put(x, y, "n")
        for y in range(int(cy - h + 2), int(cy + 1)):
            cc.put(*P(cx - w + 1, y), "W" if y < cy - 1 else "V")
        cc.put(*P(cx + w - 1, cy + h - 2), "v")
        # frame posts + base
        for xx, col in ((cx - w, "p"), (cx + w, "R"), (cx + w * 0.15, "r")):
            line(cc, xx, cy - h, xx, cy + h, col)
        poly(cc, [(cx - w - 0.4, cy + h), (cx + w + 0.4, cy + h), (cx + w * 0.5, cy + h + 2.2 * s), (cx - w * 0.5, cy + h + 2.2 * s)], "R",
             shade=lambda X, Y: "p" if X < cx else "R")
        line(cc, cx - w - 0.4, cy + h, cx + w + 0.4, cy + h, "P")
        if door > 0:      # the front pane swings open
            line(cc, cx + w, cy - h + 1, cx + w + door * 3, cy - h + 1 + door, "p")
            line(cc, cx + w + door * 3, cy - h + 1 + door, cx + w + door * 3, cy + h - 1 + door, "R")
    stamp(c, body, ch="Z")
    if not dead:
        rr = 2.4 * s * core
        for y in range(int(cy - rr) - 1, int(cy + rr) + 2):
            for x in range(int(cx - rr) - 1, int(cx + rr) + 2):
                d = math.hypot(x - cx + 0.3, y - cy + 0.3) / max(rr, 0.1)
                if d <= 1.0 and abs(x - cx) < w - 0.5 and abs(y - cy) < h - 0.5:
                    f.g.put(x, y, "0" if d < 0.45 else "9" if d < 0.8 else "8")
        bolt(f.g, cx - w + 1, cy - h + 1.5, cx + w - 1, cy + h - 1.5, seed=ph, jag=0.7, step=1.6, halo=None, edge="9", core="9")
        if eye == "open": f.g.put(*P(cx + 1.2, cy - 0.6), "0"); f.g.put(*P(cx + 2.0, cy - 0.6), "9")
        elif eye == "wide": f.g.put(*P(cx + 1.4, cy - 1), "0"); f.g.put(*P(cx + 1.4, cy), "0"); f.g.put(*P(cx + 2.4, cy - 1), "9")
        elif eye == "squint": f.g.put(*P(cx + 1.4, cy - 0.4), "8")
        f.g.put(*P(cx, cy - h - 5.0 * s), "8" if ph % 2 else "9")
    else:
        ell(f.b, cx, cy, 1.8 * s, 1.8 * s, IRON, bias=-0.2)
    return (cx, cy), (w, h)


def coil_tail(c, x, y, n, sway=0.0, ph=0.0):
    """The Coil Wisp's hanging copper coil (wisp -> lantern -> spire)."""
    pts = []
    for k in range(n):
        px_ = x + math.sin(k * 0.9 + sway) * 0.25 * k
        c.put(*P(px_, y + k), "e" if k % 2 == 0 else "q")
        c.put(*P(px_ + 1, y + k), "Q" if k % 2 == 0 else "q")
        pts.append((px_, y + k))
    return pts


def lantern_fins(f, cx, cy, s=1.0, fin=0.0):
    """The Coil Wisp's iron fins, doubled on the lantern's sides."""
    for sd in (-1, 1):
        for k in range(2):
            a = -90 + sd * (60 + k * 32 + fin)
            b0 = (cx + sd * 4.6 * s, cy - 1.5 + k * 3.0)
            t = polar(b0[0], b0[1], (3.4 - k * 0.8) * s, a)
            tube(f.u if sd < 0 else f.b, [b0, t], [1.0, 0.4], IRON_L, bias=0.1)


def build_monster(outdir, name, idle, run, moves, death, knock, idle_d=(0.2, 0.18, 0.2, 0.18), run_d=0.08, death_d=(0.08, 0.12, 0.14, 0.4),
                  remap=None, scale=6):
    anims = [("Idle", idle, list(idle_d)), ("Run", run, [run_d] * len(run))] + moves
    anims += std_tail(idle[0], death, list(death_d), knock)
    sheet(name, anims, outdir, scale=scale, remap=remap)


# ================================================================== WIRE GREMLIN (T2, Rivet Imp line, flying)
def imp_head(f, hx, hy, eyes="open", mouth=1, s=1.0, cap=COPPER, goggles=False, dead=False):
    """The Rivet Imp's head: soot (imp-red after remap) skull, snout, swept ear, copper skullcap with two rivet horns."""
    def head(c):
        ell(c, hx - 0.2, hy, 3.3 * s, 2.8 * s, SOOT, bias=0.1)
        ell(c, hx + 2.6 * s, hy + 1.0 * s, 1.7 * s, 1.3 * s, SOOT, bias=0.15)
        line(c, hx - 2.2 * s, hy - 0.8 * s, hx - 4.8 * s, hy - 2.6 * s, "gk")
        c.put(*P(hx - 3.4 * s, hy - 1.2 * s), "k")
        ell(c, hx - 0.3, hy - 0.4 * s, 3.6 * s, 2.8 * s, cap, bias=0.25, vmax=-0.05)
        line(c, hx - 3.6 * s, hy - 0.4 * s, hx + 2.6 * s, hy - 0.4 * s, "2")
        c.put(*P(hx - 1.5 * s, hy - 1.6 * s), "6")
        for ox in (-1.2, 1.4):
            c.put(*P(hx + ox * s, hy - 3.0 * s), "4"); c.put(*P(hx + ox * s, hy - 3.0 * s - 1), "5")
        if goggles:
            for gx in (1.2, 3.2):
                ell(c, hx + gx * s, hy - 0.4 * s, 1.3 * s, 1.2 * s, BRASS, bias=0.3)
            line(c, hx - 2.6 * s, hy - 0.8 * s, hx + 0.2, hy - 0.6 * s, "r")
    stamp(f.b, head, ch="Z")
    ex, ey = hx + 1.6 * s, hy - 0.6 * s
    if goggles:
        if eyes != "dead":
            for gx in (1.2, 3.2):
                f.g.put(*P(hx + gx * s, hy - 0.4 * s), "0" if eyes in ("open", "wide") else "8")
                f.g.put(*P(hx + gx * s - 1, hy - 0.4 * s - 1), "9")
        else:
            for gx in (1.2, 3.2): f.g.put(*P(hx + gx * s, hy - 0.4 * s), "3")
    elif eyes == "open":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 2, ey), "9"); f.g.put(*P(ex, ey + 1), "8")
    elif eyes == "wide":
        f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 2, ey), "0"); f.g.put(*P(ex, ey - 1), "9"); f.g.put(*P(ex + 2, ey - 1), "9")
    elif eyes == "squint":
        f.g.put(*P(ex, ey), "8"); f.g.put(*P(ex + 2, ey), "8")
    elif eyes == "dead":
        f.g.put(*P(ex, ey), "3"); f.g.put(*P(ex + 2, ey), "3")
    if mouth and not dead:
        for k in range(mouth + 1):
            f.g.put(*P(hx + 2.4 * s + k, hy + 1.6 * s), "O" if k == 1 else "o")


def wire_hook(c, x, y, ang=0.0):
    """A forged iron hook on the end of the copper wire."""
    for (a, b, ch) in ((0, 0, "5"), (1, -1, "6"), (2, -1, "5"), (3, 0, "4"), (3, 1, "4"), (2, 2, "3"), (1, 2, "3")):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        c.put(*P(x + a * ca - b * sa, y + a * sa + b * ca), ch)


def gremlin(dx=0.0, dy=0.0, lean=0.0, flap=0.0, arm=40.0, barm=200.0, hook=True, eyes="open", mouth=1, tail=0.0, legs=0.0,
            hover=4.0, extra=None, dead=False, spin=0, wire_to=None, held=None):
    f = Fr()
    base = -hover + dy
    hip = (dx, base - 3.0)
    imp_tail(f.u, f.g, hip[0] - 1.6, hip[1] - 0.2, sway=tail, scale=1.2, lit=not dead, col=("k", "g"))
    # copper-foil bat wings (far one darker, unoutlined), rooted between the shoulder blades
    sh = (dx - 1.4 + lean * 0.06, base - 8.4)
    bat_wing(f, "n", sh[0] + 1.8, sh[1] - 0.5, -80 + lean * 0.3, span=0.8, flap=flap * 0.8, far=True)
    bat_wing(f, "u", sh[0], sh[1], -128 + lean * 0.3, span=1.1, flap=flap)
    # dangling legs, iron-clawed
    for i, off in enumerate((-1.2, 1.4)):
        c = f.u if i == 0 else f.b
        foot = (hip[0] + off + 0.8 + legs * (1 if i else -1), hip[1] + 4.2 - abs(legs) * 0.5)
        tube(c, [(hip[0] + off, hip[1]), foot], [1.1, 0.8], SOOT, bias=-0.1 if i == 0 else 0.1)
        line(c, foot[0] - 0.5, foot[1] + 0.6, foot[0] + 1.5, foot[1] + 0.6, "34")
    # the wire spool on its back (grown from the imp's rivet pouch)
    sp = (dx - 3.8 + lean * 0.05, base - 5.6)
    def spool(c):
        rect(c, sp[0] - 2.0, sp[1] - 2.6, sp[0] - 1.0, sp[1] + 2.6, "2345")
        rect(c, sp[0] + 1.0, sp[1] - 2.6, sp[0] + 2.0, sp[1] + 2.6, "2345")
        for y in range(int(sp[1] - 2), int(sp[1] + 2) + 1):
            c.put(*P(sp[0], y), "e" if (y + spin) % 2 else "Q")
    stamp(f.u, spool, ch="Z")
    # back arm
    shb = (dx - 0.6 + lean * 0.05, base - 7.6)
    tube(f.u, [shb, polar(shb[0], shb[1], 3.6, barm)], [1.0, 0.8], SOOT)
    # pot belly + strap of the spool + hot buckle
    ell(f.b, dx + 0.2, base - 5.8, 3.4, 3.2, SOOT, ang=lean, bias=0.05)
    line(f.b, dx - 2.6, base - 8.0, dx + 2.0, base - 3.6, "tT")
    f.b.put(*P(dx + 0.6, base - 5.4), "5")
    imp_head(f, dx + 1.6 + lean * 0.06, base - 10.2, eyes=eyes, mouth=mouth, dead=dead)
    # front arm with the hook (or a staple) and the copper wire running back to the spool
    shf = (dx + 1.4 + lean * 0.05, base - 7.6)
    hand = polar(shf[0], shf[1], 4.0, arm)
    tube(f.b, [shf, hand], [1.1, 0.9], SOOT, bias=0.15)
    f.b.put(*P(*hand), "h")
    if hook:
        wire_hook(f.b, hand[0] + 0.5, hand[1], ang=arm * 0.3)
        tgt = wire_to or (hand[0] + 0.5, hand[1])
        for (x, y) in line_px(*P(sp[0] + 1, sp[1] + 2), *P(tgt[0], tgt[1] + 1)):
            f.n.put(x, y + 1, "e")
    if held == "staple":
        rivet_px(f.g, hand[0] + 0.5, hand[1] - 1.5)
        f.g.put(*P(hand[0] + 2.5, hand[1] - 1.5), "5")
    if extra: extra(f, hand, sp)
    return f.done()


def gremlin_corpse():
    f = Fr()
    bat_wing(f, "b", -3, -2, -170, span=0.8, flap=0, far=False)
    ell(f.b, 0, -2.0, 4.6, 2.0, SOOT, bias=0.0)
    ell(f.b, 4.2, -2.2, 2.6, 2.1, COPPER, bias=0.2)
    line(f.b, 6, -3.6, 8, -4.4, "gk")
    rect(f.b, -8, -3, -6, 0, "2345"); f.b.put(-7, -2, "e"); f.b.put(-7, -1, "Q")
    for k in range(6): f.b.put(8 + k, 0 if k % 2 else -1, "e")
    wire_hook(f.b, 14, -2, 0)
    f.g.put(5, -3, "3")
    return f.done()


def build_gremlin(outdir):
    G = gremlin
    idle = [G(flap=0, dy=0.0, arm=60), G(flap=16, dy=0.6, arm=64, tail=0.6, spin=1), G(flap=28, dy=0.9, arm=66, tail=1.2, eyes="squint"),
            G(flap=10, dy=0.3, arm=62, tail=0.6, spin=1)]
    run = [G(dx=0.4, lean=10, flap=[0, 18, 30, 18, 4, -8][i], dy=[-0.3, 0.3, 0.8, 0.4, -0.2, -0.6][i], arm=80, barm=210, tail=i * 0.7,
             legs=0.8 * math.sin(i * 1.05), spin=i) for i in range(6)]
    # STAPLE: pluck a hot staple from the spool, cock the arm, FLICK it (release on 3), follow-through
    def flick(f, hand, sp):
        for k in range(3): f.g.put(*P(hand[0] + 2 + k * 1.5, hand[1] - 1), "9" if k else "0")
    staple = [G(flap=-6, arm=170, barm=150, held=None, hook=False, eyes="squint"),
              G(flap=-14, arm=200, barm=150, held="staple", hook=False, eyes="open", dy=0.4),
              G(flap=-20, lean=-6, arm=230, barm=160, held="staple", hook=False, eyes="wide", dy=0.6),
              G(flap=24, lean=10, dx=1.0, arm=-10, barm=200, hook=False, eyes="wide", mouth=2, extra=flick),
              G(flap=18, lean=8, dx=0.8, arm=10, barm=200, hook=False, mouth=2),
              G(flap=6, lean=4, arm=40, hook=False),
              G(flap=0, arm=60, hook=True)]
    # HOOK: whirl the hook overhead (0-2), CAST it (3: the hook leaves), wire paid out and reeled (4-6), settle
    def whirl(n):
        def fn(f, hand, sp):
            for k in range(n):
                a = -90 - k * 50
                p_ = polar(hand[0], hand[1] - 4, 4.0, a)
                f.g.put(*P(*p_), "e" if k < n - 1 else "E")
        return fn
    def paid(n, taut=True):
        def fn(f, hand, sp):
            for k in range(n):
                x = hand[0] + 1 + k
                y = hand[1] + (0 if taut else round(math.sin(k * 0.6) * 1.0))
                f.n.put(*P(x, y), "e" if k % 3 else "E")
                if k % 4 == 0 and taut: f.g.put(*P(x, y - 1), "9")
        return fn
    hookan = [G(flap=0, arm=-60, barm=200, eyes="squint", extra=whirl(1)),
              G(flap=-12, arm=-120, barm=190, eyes="open", extra=whirl(2), dy=0.4),
              G(flap=-22, arm=-160, barm=180, eyes="wide", extra=whirl(3), dy=0.6, lean=-6),
              G(flap=26, lean=12, dx=1.0, arm=-5, barm=210, hook=False, eyes="wide", mouth=2, extra=paid(6)),
              G(flap=16, lean=10, dx=0.8, arm=0, barm=210, hook=False, eyes="wide", mouth=2, extra=paid(9)),
              G(flap=6, lean=6, arm=10, barm=210, hook=False, eyes="open", extra=paid(9, False), spin=1),
              G(flap=0, lean=2, arm=40, hook=False, spin=2),
              G(flap=4, arm=60, hook=True)]
    death = [G(flap=-30, lean=-14, arm=-150, eyes="wide", mouth=2, dy=0.5),
             dim_glow(G(flap=40, lean=-26, arm=160, eyes="squint", dy=2.5, mouth=0, hook=False)),
             dim_glow(grounded(G(flap=60, lean=-40, arm=170, eyes="dead", mouth=0, hook=False, dead=True, hover=0))),
             dim_glow(gremlin_corpse())]
    knock = G(flap=-26, lean=-14, dx=-0.6, arm=-140, eyes="squint", dy=0.4)
    build_monster(outdir, "KrnWireGremlin", idle, run,
                  [("Staple", staple, [0.12, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12]),
                   ("Hook", hookan, [0.1, 0.1, 0.12, 0.06, 0.12, 0.14, 0.12, 0.12])],
                  death, knock, idle_d=(0.12, 0.12, 0.12, 0.12), run_d=0.07, remap=IMP_HIDE, scale=8)


# ================================================================== ARC LANTERN (T2, Coil Wisp line, flying)
def lantern(dx=0.0, dy=0.0, tilt=0.0, fin=0.0, core=1.0, ph=0, tail=0.0, eye="open", door=0.0, hover=3.0, extra=None, dead=False):
    f = Fr()
    cx, cy = dx + tilt * 0.06, -hover - 10.6 + dy
    coil_tail(f.u, cx - 0.5, cy + 6.0, 4, sway=tail)
    if not dead:
        f.g.put(*P(cx + math.sin(3 * 0.9 + tail) * 0.8, cy + 10.0), "9" if ph % 2 else "8")
    lantern_fins(f, cx, cy, s=0.85, fin=fin)
    (gc, wh) = lantern_body(f, cx, cy, s=0.85, core=core, ph=ph, eye=eye, dead=dead, door=door)
    if extra: extra(f, cx, cy, wh)
    return f.done()


def lantern_corpse():
    f = Fr()
    poly(f.b, [(-6, -1), (4, -1), (5, -6), (-5, -7)], "n", shade=lambda X, Y: "n")
    line(f.b, -6, -1, -5, -7, "p"); line(f.b, 4, -1, 5, -6, "R"); line(f.b, -5, -7, 5, -6, "R")
    poly(f.b, [(5, -6), (9, -4), (8, -1), (5, -1)], "R")
    for (x, y) in ((-8, 0), (7, 0), (-3, -8)): f.b.put(x, y, "W")
    for k in range(5): f.b.put(-12 + k, 0 if k % 2 else -1, "e" if k % 2 else "q")
    tube(f.b, [(10, -1), (13, -3)], [1.0, 0.4], IRON_L)
    return f.done()


def build_lantern(outdir):
    L = lantern
    idle = [L(ph=0, dy=0.4), L(ph=1, dy=0.0, fin=8, tail=0.8, core=1.05), L(ph=2, dy=-0.3, fin=12, tail=1.6), L(ph=3, dy=0.1, fin=6, tail=2.4, core=0.95)]
    run = [L(dx=0.4, tilt=10, dy=[-0.2, -0.7, -1.0, -0.6, 0.0, 0.1][i], fin=[0, 14, 24, 14, 4, 0][i], ph=i + 4, tail=i * 0.9) for i in range(6)]
    # SEEKER: the core swells, the front pane opens, a wisp of lightning SLIPS out (3), pane shuts
    def wisp_out(n):
        def fn(f, cx, cy, wh):
            for k in range(n):
                f.g.put(*P(cx + wh[0] + 1 + k, cy - 0.5 + (k % 2)), "0" if k < 2 else "9")
            if n > 2: spark(f.g, cx + wh[0] + 2, cy - 0.5, 1)
        return fn
    seek = [L(ph=10, core=0.9, eye="open"), L(ph=11, core=1.25, eye="wide", fin=-14, door=0.4),
            L(ph=12, core=1.4, eye="wide", fin=-22, door=1.0, extra=wisp_out(1)), L(ph=13, core=0.9, eye="wide", fin=20, door=1.0, dx=-0.6, extra=wisp_out(4)),
            L(ph=14, core=0.8, door=0.4, fin=10), L(ph=15, core=1.0, fin=4)]
    # FIELD: rises, the core floods, a cone of light pours forward-down (4: the field forms at the hero), dims
    def cone(n):
        def fn(f, cx, cy, wh):
            for k in range(n * 3):
                t = k / max(1, n * 3 - 1)
                for s_ in (-1, 1):
                    x = cx + wh[0] + 1 + t * 9
                    y = cy + wh[1] - 1 + t * (4 + s_ * 3)
                    if (k + s_) % 2: f.g.put(*P(x, y), "9" if t < 0.5 else "8")
        return fn
    field = [L(ph=20, core=0.8, eye="squint", dy=0.6), L(ph=21, core=1.2, eye="wide", dy=-0.6, fin=-20),
             L(ph=22, core=1.5, eye="wide", dy=-1.4, fin=-30, tilt=6), L(ph=23, core=1.6, eye="wide", dy=-1.6, fin=-34, tilt=10, door=1.0, extra=cone(1)),
             L(ph=24, core=1.7, eye="wide", dy=-1.4, fin=30, tilt=10, door=1.0, extra=cone(3)), L(ph=25, core=1.3, eye="wide", dy=-1.0, fin=20, tilt=8, door=1.0, extra=cone(2)),
             L(ph=26, core=1.0, eye="open", dy=-0.4, fin=8, door=0.4), L(ph=27, core=1.0, fin=4)]
    death = [L(ph=30, core=1.6, eye="wide", fin=-30, tilt=-20, door=1.0),
             dim_glow(L(ph=31, core=0.6, eye="squint", fin=40, tilt=-30, dy=3.0)),
             dim_glow(grounded(L(ph=32, dead=True, fin=60, tilt=-40, dy=5.0))),
             lantern_corpse()]
    knock = L(dx=-0.6, ph=33, core=1.2, eye="wide", fin=-30, tilt=-14)
    build_monster(outdir, "KrnArcLantern", idle, run,
                  [("Seek", seek, [0.12, 0.12, 0.12, 0.06, 0.12, 0.14]),
                   ("Field", field, [0.12, 0.12, 0.12, 0.1, 0.1, 0.12, 0.12, 0.14])],
                  death, knock, idle_d=(0.18, 0.18, 0.18, 0.18), run_d=0.08, scale=8)


# ================================================================== FORGEMASTER (T3, Anvil Smith line)
def forgemaster(dx=0.0, dy=0.0, lean=0.0, feet=((-5, 0), (5, 0)), hand=(8.0, -18.0), bhand=(-8.0, -14.0), ham="held", ham_ang=-128.0,
                eyes="open", mouth=1, hot=1, beard=0.0, tail=0.0, extra=None, dead=False, crouch=0.0):
    """Tall red-hided master smith (the Smith's hide, leather and copper skullcap grown into a riveted crown), long soot
    beard with embers, a quiver of lightning rods on the back, a white-hot two-handed sledge."""
    f = Fr()
    hip = (dx, -13.0 + dy + crouch)
    ch = (dx + 0.6 + lean * 0.1, -22.0 + dy + crouch * 0.6)
    imp_tail(f.u, f.g, hip[0] - 3.2, hip[1] - 1.0, sway=tail, scale=2.0, lit=not dead, col=("k", "g"))
    # quiver of rods behind the shoulders (the Smith plants rods; the master carries a sheaf of them)
    for k in range(3):
        r0 = (ch[0] - 5.0 + k * 1.6, ch[1] + 3.0)
        e = polar(r0[0], r0[1], 12.0 - k, -112 + k * 6 + lean * 0.3)
        line(f.u, r0[0], r0[1], e[0], e[1], "34")
        f.u.put(*P(*polar(e[0], e[1], -2.0, -112 + k * 6)), "e")
        if not dead: f.g.put(*P(*e), "9" if k != 1 else "0")
    tube(f.u, [(ch[0] - 5.4, ch[1] + 1.0), (ch[0] - 3.0, ch[1] + 6.0)], [1.6, 1.6], LEATHER, bias=0.1)
    # legs: thick, black leather breeches, iron boots
    for i, (fx_, fy_) in enumerate(feet):
        c = f.u if i == 0 else f.b
        hx_ = hip[0] + (-2.4 if i == 0 else 2.4)
        knee = ((hx_ + fx_ + dx) / 2 + 1.0, (hip[1] + fy_) / 2 - 0.5)
        tube(c, [(hx_, hip[1]), knee, (fx_ + dx, fy_ - 2.2)], [2.4, 2.0, 1.8], LEATHER, bias=-0.1 if i == 0 else 0.1)
        rect(c, fx_ + dx - 2.4, fy_ - 2.6, fx_ + dx + 3.0, fy_, "2345")
    # back arm
    shb = (ch[0] - 3.6, ch[1] - 3.0)
    hb = (dx + bhand[0], dy + bhand[1])
    eb, _ = ik(shb[0], shb[1], hb[0], hb[1], 5.0, 5.0, bend=-1)
    tube(f.u, [shb, eb, hb], [2.2, 1.9, 1.7], SOOT, bias=-0.1)
    # torso: broad chest, narrow waist
    ell(f.b, ch[0], ch[1], 7.0, 5.6, SOOT, ang=lean, bias=0.1)
    ell(f.b, hip[0] + 0.4, hip[1] - 2.6, 5.0, 3.6, SOOT, bias=0.0)
    # blackened leather apron to the knees, copper rivets, glowing forge-burn
    ap = [(ch[0] - 2.0, ch[1] - 1.0), (ch[0] + 6.6, ch[1] - 1.5), (hip[0] + 7.0, hip[1] + 6.5), (hip[0] - 1.0, hip[1] + 7.0)]
    poly(f.b, ap, "T", shade=lambda X, Y: "t" if X > ch[0] + 4.6 else "T")
    for k in range(3): f.b.put(*P(ch[0] - 1.0 + k * 3.4, ch[1] - 0.6), "e")
    line(f.b, hip[0] - 4.4, hip[1] - 1.4, hip[0] + 6.0, hip[1] - 1.8, "2")
    f.b.put(*P(hip[0] + 1.6, hip[1] - 1.6), "E")
    # iron pauldron
    stamp(f.b, lambda c: ell(c, ch[0] + 1.6, ch[1] - 4.4, 3.6, 2.4, IRON_HI, bias=0.2), ch="Z")
    # head with the copper crown (the Smith's skullcap, three rivet horns) and a long ember beard
    hx, hy = ch[0] + 3.2 + lean * 0.12, ch[1] - 8.4
    def head(c):
        ell(c, hx - 0.2, hy, 3.4, 3.0, SOOT, bias=0.1)
        ell(c, hx + 2.6, hy + 1.0, 1.8, 1.4, SOOT, bias=0.15)
        line(c, hx - 2.4, hy - 0.8, hx - 5.2, hy - 2.8, "gk")
        ell(c, hx - 0.4, hy - 0.6, 3.8, 3.0, COPPER, bias=0.25, vmax=-0.1)
        line(c, hx - 3.8, hy - 0.6, hx + 2.8, hy - 0.6, "q")
        for ox in (-2.0, 0.2, 2.2):
            c.put(*P(hx + ox, hy - 3.2), "e"); c.put(*P(hx + ox, hy - 4.2), "E")
        # beard: a wedge of soot hanging over the chest
        bb = [(hx - 1.0, hy + 1.6), (hx + 4.0, hy + 2.0), (hx + 2.6 + beard, hy + 8.0), (hx + 0.6 + beard, hy + 9.0), (hx - 1.0, hy + 4.0)]
        poly(c, bb, "3", shade=lambda X, Y: "4" if X < hx + 1.0 else ("3" if (X + Y) % 3 else "2"))
    stamp(f.b, head, ch="Z")
    if not dead:
        for (a, b) in ((1.2, 4.0), (2.4, 6.5), (0.8 + beard, 8.0)):
            f.g.put(*P(hx + a, hy + b), "o")
    ex, ey = hx + 1.6, hy - 0.4
    if eyes == "open": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 2, ey), "9")
    elif eyes == "wide": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 2, ey), "0"); f.g.put(*P(ex, ey - 1), "9")
    elif eyes == "squint": f.g.put(*P(ex, ey), "8"); f.g.put(*P(ex + 2, ey), "8")
    elif eyes == "dead": f.g.put(*P(ex, ey), "3"); f.g.put(*P(ex + 2, ey), "3")
    # front arm + the sledge
    shf = (ch[0] + 3.6, ch[1] - 3.0)
    hf = (dx + hand[0], dy + hand[1])
    ef, _ = ik(shf[0], shf[1], hf[0], hf[1], 5.0, 5.0, bend=1)
    hres = None
    if ham == "held":
        hres = hammer(f, hf[0], hf[1], ham_ang, L=14.0, head=(4.4, 2.8), hot=hot >= 1 and not dead, smear=0,
                      layer="u" if -170 < ham_ang < -100 else "b")
        line(getattr(f, "u" if -170 < ham_ang < -100 else "b"), *polar(hf[0], hf[1], 1.0, ham_ang + 90), *polar(hres[0][0], hres[0][1], 1.0, ham_ang + 90), "3")
        if hot >= 1 and not dead:
            e = hres[0]
            for k in range(-2, 3):
                f.g.put(*P(*polar(e[0], e[1], k * 1.2, ham_ang + 90)), "Y" if hot >= 2 and abs(k) < 2 else "O")
            if hot >= 2: crackle(f.g, e[0], e[1], int(beard * 10) + 1, r=3, seed=4)
    def farm(c):
        tube(c, [shf, ef, hf], [2.2, 1.9, 1.7], SOOT, bias=0.2)
        ell(c, hf[0], hf[1], 1.6, 1.5, SOOT, bias=0.3)
    stamp(f.b, farm, ch="Z")
    if extra: extra(f, hf, hres)
    return f.done()


def forgemaster_corpse():
    f = Fr()
    ell(f.b, -1, -3.6, 10.0, 3.6, SOOT, bias=0.0)
    poly(f.b, [(-4, -6.4), (6, -6.6), (7, -1.0), (-4, -1.0)], "T")
    ell(f.b, 10.5, -3.0, 3.0, 2.8, COPPER, bias=0.2, vmax=0.2)
    poly(f.b, [(9, -1), (14, -1), (12, 0)], "1")
    for k in range(3): line(f.b, -12 + k * 2, -2, -16 + k * 3, -9, "34")
    line(f.b, 14, 0, 26, -1, "45")
    tube(f.b, [(26, -5), (26, 0)], [2.4, 2.4], IRON_L)
    f.g.put(26, -3, "a")
    return f.done()


def build_forgemaster(outdir):
    M = forgemaster
    idle = [M(), M(dy=0.4, hand=(8.0, -17.6), bhand=(-8.0, -13.6), beard=0.4, tail=0.5, ham_ang=-127),
            M(dy=0.5, hand=(8.0, -17.5), bhand=(-8.0, -13.5), beard=0.6, tail=1.0, eyes="squint", hot=2, ham_ang=-127), M(dy=0.2, beard=0.2, tail=0.5)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3; s_ = math.sin(ph)
        run.append(M(dx=0.6, dy=-0.8 * abs(math.cos(ph)), lean=6, feet=((-5 - 3.2 * s_, -1.0 * max(0, -math.cos(ph))), (5 + 3.2 * s_, -1.0 * max(0, math.cos(ph)))),
                     hand=(8.0, -21.0 + s_ * 0.5), bhand=(-7.0 + 2.5 * s_, -14.0), ham_ang=-140, beard=-0.6, tail=i * 0.6))
    # THROW: lift the sledge, wind it back, SWING and let it fly (release 3), wait open-handed, CATCH it (7), settle
    def fly(f, hf, hres):
        for k in range(4): f.g.put(*P(hf[0] + 3 + k * 2, hf[1] - 1 - k * 0.5), "O" if k < 2 else "o")
        spark(f.g, hf[0] + 2, hf[1] - 1, 1, "Y", "O")
    def catch(f, hf, hres):
        spark(f.g, hf[0] + 1, hf[1] - 2, 2, "0", "9")
    throw = [M(hand=(6.0, -22.0), ham_ang=-120, eyes="squint", dy=0.4),
             M(lean=-10, hand=(-2.0, -27.0), bhand=(-10.0, -20.0), ham_ang=-170, eyes="wide", hot=2, dy=0.6, crouch=0.5),
             M(lean=4, dx=1.0, hand=(10.0, -25.0), bhand=(-9.0, -14.0), ham_ang=-30, eyes="wide", hot=2),
             M(lean=10, dx=2.0, hand=(14.0, -20.0), bhand=(-10.0, -13.0), ham="none", eyes="wide", mouth=2, extra=fly),
             M(lean=8, dx=1.6, hand=(13.0, -19.0), bhand=(-9.0, -14.0), ham="none", eyes="open", mouth=2),
             M(lean=4, dx=1.0, hand=(12.0, -21.0), bhand=(-9.0, -15.0), ham="none", eyes="open"),
             M(lean=2, dx=0.6, hand=(12.0, -22.0), bhand=(-9.0, -15.0), ham="none", eyes="wide"),
             M(lean=-4, hand=(8.0, -22.0), ham_ang=-120, eyes="wide", extra=catch),
             M(hand=(8.0, -18.0), eyes="open")]
    # OVERLOAD: raise the sledge high, it floods white, SLAM it down (3), lightning runs out along the floor (4: every rod
    # near him fires), recover
    def slam_fx(n):
        def fn(f, hf, hres):
            if not hres: return
            e = hres[0]
            for sd in (-1, 1):
                bolt(f.g, e[0], -1, e[0] + sd * (6 + n * 4), -1 - n * 0.4, seed=n * 3 + sd, jag=0.9, step=1.8, halo="7")
            spark(f.g, e[0], -2, 2)
        return fn
    over = [M(hand=(6.0, -24.0), ham_ang=-110, eyes="squint", dy=0.4, crouch=0.4),
            M(lean=-6, hand=(2.0, -31.0), bhand=(0.0, -29.0), ham_ang=-95, eyes="wide", hot=2, dy=-0.4),
            M(lean=-8, hand=(1.0, -32.0), bhand=(-1.0, -30.0), ham_ang=-100, eyes="wide", hot=2, dy=-0.6, beard=-0.6),
            M(lean=14, dx=1.4, hand=(10.0, -12.0), bhand=(8.0, -13.0), ham_ang=40, eyes="wide", hot=2, mouth=2, crouch=2.0, extra=slam_fx(1)),
            M(lean=14, dx=1.4, hand=(10.0, -12.0), bhand=(8.0, -13.0), ham_ang=42, eyes="wide", hot=2, mouth=2, crouch=2.0, extra=slam_fx(2)),
            M(lean=12, dx=1.2, hand=(10.0, -13.0), bhand=(7.0, -14.0), ham_ang=40, eyes="squint", hot=1, crouch=1.6, extra=slam_fx(3)),
            M(lean=6, dx=0.6, hand=(9.0, -17.0), bhand=(-4.0, -15.0), ham_ang=-30, eyes="open", crouch=0.6),
            M(hand=(8.0, -18.0), eyes="open")]
    death = [M(lean=-12, hand=(4.0, -28.0), ham_ang=-200, eyes="wide", mouth=2),
             dim_glow(M(lean=-24, dy=2.0, hand=(-2.0, -12.0), bhand=(-10.0, -8.0), ham="none", eyes="squint", mouth=0, crouch=3.0)),
             dim_glow(grounded(M(lean=-40, dy=5.0, hand=(-6.0, -6.0), bhand=(-12.0, -4.0), ham="none", eyes="dead", mouth=0, crouch=6.0, dead=True))),
             dim_glow(forgemaster_corpse())]
    knock = M(lean=-12, dx=-0.8, hand=(4.0, -26.0), ham_ang=-170, eyes="wide", mouth=2)
    build_monster(outdir, "KrnForgemaster", idle, run,
                  [("Throw", throw, [0.12, 0.14, 0.06, 0.08, 0.12, 0.14, 0.14, 0.1, 0.12]),
                   ("Overload", over, [0.12, 0.14, 0.14, 0.06, 0.1, 0.12, 0.14, 0.14])],
                  death, knock, idle_d=(0.22, 0.18, 0.22, 0.18), run_d=0.09, death_d=(0.1, 0.14, 0.16, 0.45), remap=MASTER_SKIN, scale=5)


# ================================================================== WIRE WYVERN (T3, Wire Gremlin line, flying)
def wyvern(dx=0.0, dy=0.0, tilt=0.0, flap=0.0, neck=(0.0, 0.0), jaw=0.0, legs=0.0, tail=0.0, eye="open", glow=1, ph=0,
           hover=6.0, extra=None, dead=False):
    """Verdigris-scaled wyvern: the gremlin's copper-foil bat wings grown huge, its imp-red underside, copper skullcap and
    rivet horns, spark-tipped whip tail, and the copper wire wound round its neck in coils."""
    f = Fr()
    base = -hover + dy
    ca = math.radians(tilt)
    def R(x, y):
        return (dx + x * math.cos(ca) - y * math.sin(ca), base + x * math.sin(ca) + y * math.cos(ca))
    body = R(-2.0, -11.0)
    # far wing behind everything
    sh = R(1.0, -14.0)
    bat_wing(f, "n", sh[0] + 2.0, sh[1] - 1.0, -82 + tilt, span=1.45, flap=flap * 0.8, far=True)
    # long whip tail with the imp's spark tip
    tp = [R(-8.0, -10.0)]
    for k in range(7):
        a = math.radians(170 + tilt + k * 6 + math.sin(tail + k * 0.8) * 10)
        tp.append((tp[-1][0] + 1.6 * math.cos(a), tp[-1][1] + 1.6 * math.sin(a) + 0.6))
    tube(f.u, tp, [2.0, 1.8, 1.5, 1.3, 1.0, 0.8, 0.6, 0.5], VERDI, bias=0.0)
    f.u.put(*P(*tp[-1]), "c")
    if not dead: f.g.put(*P(tp[-1][0] - 1, tp[-1][1] - 1), "0"); f.g.put(*P(tp[-1][0] - 1, tp[-1][1]), "9")
    # back leg
    for i, lx in enumerate((-4.0, 1.5)):
        c = f.u if i == 0 else None
        if c is None: continue
        j = R(lx, -8.0)
        foot = (j[0] + 1.0 + legs, j[1] + 4.6)
        tube(c, [j, foot], [1.6, 1.0], VERDI, bias=-0.1)
        line(c, foot[0] - 1, foot[1] + 0.6, foot[0] + 2, foot[1] + 0.6, "34")
    # body: verdigris barrel with the imp-red belly
    ell(f.b, body[0], body[1], 8.0, 4.4, VERDI, ang=tilt, bias=0.15)
    ell(f.b, *R(-1.0, -8.6), 6.6, 1.8, SOOT, ang=tilt, bias=0.25)
    for k in range(5):   # back scutes
        f.b.put(*P(*R(-6.0 + k * 2.6, -15.0 + abs(k - 2) * 0.3)), "C" if k % 2 else "c")
    # front leg
    j = R(1.5, -8.0)
    foot = (j[0] + 1.0 - legs, j[1] + 4.6)
    stamp(f.b, lambda c: (tube(c, [j, foot], [1.7, 1.1], VERDI, bias=0.15), line(c, foot[0] - 1, foot[1] + 0.6, foot[0] + 2, foot[1] + 0.6, "45")), ch="Z")
    # neck with copper wire coils, head
    n0 = R(5.0, -13.0)
    hx, hy = R(11.0 + neck[0], -21.0 + neck[1])
    nm = ((n0[0] + hx) / 2 + 1.2, (n0[1] + hy) / 2 + 0.6)
    tube(f.b, [n0, nm, (hx - 1.0, hy + 1.0)], [3.0, 2.2, 1.9], VERDI, bias=0.2)
    for t in (0.25, 0.5, 0.75):
        px_ = n0[0] + (hx - n0[0]) * t + 0.6; py_ = n0[1] + (hy - n0[1]) * t
        for k in (-1, 0, 1): f.b.put(*P(px_ + k, py_ - k * 0.5), "e" if k else "E")
    def head(c):
        ell(c, hx, hy, 3.0, 2.4, VERDI, bias=0.25)
        tube(c, [(hx + 1.6, hy - 0.2), (hx + 5.6, hy + 0.6 - jaw * 0.5)], [1.8, 1.1], VERDI, bias=0.3)
        je = polar(hx + 1.0, hy + 1.6, 4.2, 14 + jaw * 34)
        tube(c, [(hx + 1.0, hy + 1.4), je], [1.0, 0.7], SOOT, bias=0.1)
        ell(c, hx - 0.4, hy - 0.8, 3.0, 2.2, COPPER, bias=0.25, vmax=-0.1)       # the gremlin's copper skullcap
        for ox in (-1.6, 0.6):
            line(c, hx + ox, hy - 2.6, hx + ox - 1.6, hy - 5.0, "e"); c.put(*P(hx + ox - 1.8, hy - 5.4), "E")
    stamp(f.b, head, ch="Z")
    if jaw > 0.3 and not dead:
        for k in range(3): f.g.put(*P(hx + 2.6 + k, hy + 1.4 + k * 0.3), "0" if k == 1 else "9")
    ex, ey = hx + 0.8, hy - 0.4
    if eye == "open": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "9")
    elif eye == "wide": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "0"); f.g.put(*P(ex, ey - 1), "9")
    elif eye == "squint": f.g.put(*P(ex, ey), "8")
    elif eye == "dead": f.g.put(*P(ex, ey), "3")
    # near wing over the body
    w, tips = bat_wing(f, "b", sh[0], sh[1], -122 + tilt, span=1.55, flap=flap)
    if not dead and glow:
        for k, t in enumerate(tips):
            if (k + ph) % 2 == 0: f.g.put(*P(*t), "9")
    if extra: extra(f, (hx, hy), w)
    return f.done()


def wyvern_corpse():
    f = Fr()
    bat_wing(f, "b", 2, -4, -165, span=1.3, flap=0)
    ell(f.b, -2, -3.4, 9.0, 3.4, VERDI, bias=0.1)
    ell(f.b, -1, -1.6, 6.5, 1.2, SOOT, bias=0.2)
    tube(f.b, [(-10, -2), (-16, -1), (-21, 0)], [1.8, 1.2, 0.6], VERDI)
    tube(f.b, [(6, -3), (12, -2)], [2.4, 1.8], VERDI)
    ell(f.b, 14, -2.2, 2.8, 2.2, VERDI, bias=0.2)
    ell(f.b, 13.6, -3.2, 2.6, 1.4, COPPER, bias=0.2)
    for k in range(4): f.b.put(7 + k, -5 + (k % 2), "e")
    f.g.put(15, -3, "3")
    return f.done()


def build_wyvern(outdir):
    W = wyvern
    idle = [W(flap=0, ph=0), W(flap=14, dy=0.6, ph=1, tail=0.8, neck=(0, 0.3)), W(flap=26, dy=1.0, ph=2, tail=1.6, neck=(0, 0.5), eye="squint"),
            W(flap=10, dy=0.4, ph=3, tail=2.4)]
    run = [W(dx=0.4, tilt=-6, flap=[0, 16, 30, 16, 2, -10][i], dy=[-0.4, 0.4, 1.0, 0.4, -0.4, -0.8][i], ph=i, tail=i * 0.8, legs=-1.0,
             neck=(1.0, 1.0)) for i in range(6)]
    # BREATH: rear the head back, the throat lights up, BREATHE a beam (3-5), close
    def throat(n):
        def fn(f, h, w):
            hx, hy = h
            for k in range(n): f.g.put(*P(hx - 2 - k, hy + 3 + k), "9" if k % 2 else "0")
        return fn
    def beam(f, h, w):
        hx, hy = h
        for k in range(4): f.g.put(*P(hx + 5 + k, hy + 1 + (k % 2)), "0" if k < 2 else "9")
    breath = [W(neck=(-1.0, -0.5), jaw=0.2, eye="squint", ph=10, flap=-6),
              W(neck=(-2.6, -1.6), jaw=0.4, eye="wide", ph=11, flap=-16, dy=-0.4, extra=throat(2)),
              W(neck=(-3.0, -2.0), jaw=0.6, eye="wide", ph=12, flap=-22, dy=-0.6, extra=throat(4)),
              W(neck=(2.0, 1.5), jaw=1.0, eye="wide", ph=13, flap=20, dx=-0.6, extra=beam),
              W(neck=(2.2, 1.6), jaw=1.0, eye="wide", ph=14, flap=26, dx=-0.8, extra=beam),
              W(neck=(1.6, 1.2), jaw=0.8, eye="wide", ph=15, flap=14, dx=-0.6, extra=beam),
              W(neck=(0.0, 0.4), jaw=0.2, eye="open", ph=16, flap=4)]
    # RAIN: beat up high (0-2), the wings snap down and shake out a rain of sparks (3), glide down (4-7)
    def shower(n):
        def fn(f, h, w):
            rnd = random.Random(n)
            for k in range(5 + n * 2):
                x = w[0] + rnd.uniform(-2, 12); y = w[1] + rnd.uniform(2, 12)
                if y < -1: f.g.put(*P(x, y), "0" if k % 3 == 0 else "9")
        return fn
    rain = [W(flap=-10, dy=0.6, eye="squint", ph=20), W(flap=-30, dy=-1.0, eye="wide", ph=21, neck=(-0.6, -1.0)),
            W(flap=-40, dy=-2.4, eye="wide", ph=22, neck=(-0.8, -1.4)),
            W(flap=34, dy=-2.0, eye="wide", ph=23, jaw=0.6, extra=shower(2)), W(flap=40, dy=-1.6, eye="wide", ph=24, jaw=0.4, extra=shower(3)),
            W(flap=24, dy=-1.0, eye="open", ph=25, extra=shower(1)), W(flap=8, dy=-0.4, eye="open", ph=26), W(flap=0, dy=0.0, ph=27)]
    death = [W(flap=-36, tilt=10, neck=(-2, -2), jaw=1.0, eye="wide", ph=30),
             dim_glow(W(flap=40, tilt=22, dy=3.0, neck=(1, 3), jaw=0.6, eye="squint", glow=0)),
             dim_glow(grounded(W(flap=60, tilt=30, dy=5.0, neck=(2, 5), jaw=0.4, eye="dead", glow=0, dead=True))),
             dim_glow(wyvern_corpse())]
    knock = W(flap=-30, tilt=10, dx=-0.8, neck=(-2, -1), jaw=0.6, eye="wide", ph=33)
    build_monster(outdir, "KrnWireWyvern", idle, run,
                  [("Breath", breath, [0.12, 0.14, 0.12, 0.08, 0.1, 0.1, 0.14]),
                   ("Rain", rain, [0.1, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12, 0.14])],
                  death, knock, idle_d=(0.14, 0.14, 0.14, 0.14), run_d=0.08, death_d=(0.1, 0.14, 0.16, 0.45), remap=IMP_RED, scale=5)


# ================================================================== FUSE SAPPER (T3, Wire Gremlin line)
def sapper(dx=0.0, dy=0.0, lean=0.0, feet=((-4, 0), (4, 0)), hand=(8.0, -12.0), bhand=(-7.0, -12.0), held=None, buzz=0, eyes="open",
           mouth=1, cans=3, tail=0.0, extra=None, dead=False, squash=0.0):
    """A pot-bellied gremlin grown too heavy to fly: brass goggles, its copper wings now stubby buzzing fans on a rack
    of brass charge canisters (its spool grown into an arsenal), fuse wires to its hands."""
    f = Fr()
    hip = (dx, -8.0 + dy + squash)
    bc = (dx - 0.4 + lean * 0.08, -14.0 + dy + squash * 0.7)
    imp_tail(f.u, f.g, hip[0] - 4.0, hip[1] + 1.0, sway=tail, scale=1.6, lit=not dead, col=("k", "g"))
    # the canister rack on its back
    rk = (bc[0] - 6.0, bc[1] - 2.0)
    for k in range(3):
        if k >= cans: continue
        x0 = rk[0] - 2.6 + k * 3.0; y0 = rk[1] - 7.0 - (k % 2) * 2.0
        def can(c, x0=x0, y0=y0):
            rect(c, x0, y0, x0 + 2.4, y0 + 8.0, "rRpP")
            for y in range(int(y0 + 2), int(y0 + 6)): c.put(*P(x0 + 1.2, y), "n")
            rect(c, x0 + 0.4, y0 - 1.2, x0 + 2.0, y0, "2345")
        stamp(f.u, can, ch="Z")
        if not dead:
            for y in range(int(y0 + 2), int(y0 + 6)):
                if (y + k + buzz) % 2 == 0: f.g.put(*P(x0 + 1.2, y), "9")
    # stubby copper fan wings on the rack (buzzing blur)
    for sd, layer in ((0, "n"), (1, "u")):
        bat_wing(f, layer, rk[0] + 1.0 + sd * 1.0, rk[1] - 5.0, -150 + (buzz % 2) * 26 + sd * 20, span=0.62, flap=0, far=sd == 0)
    # legs
    for i, (fx_, fy_) in enumerate(feet):
        c = f.u if i == 0 else f.b
        hx_ = hip[0] + (-2.2 if i == 0 else 2.2)
        tube(c, [(hx_, hip[1]), (fx_ + dx, fy_ - 1.6)], [1.8, 1.5], SOOT, bias=-0.1 if i == 0 else 0.1)
        rect(c, fx_ + dx - 2.0, fy_ - 1.8, fx_ + dx + 2.4, fy_, "2345")
    # back arm
    shb = (bc[0] - 3.0, bc[1] - 2.0)
    hb = (dx + bhand[0], dy + bhand[1])
    tube(f.u, [shb, ((shb[0] + hb[0]) / 2, (shb[1] + hb[1]) / 2 + 1), hb], [1.6, 1.4, 1.3], SOOT)
    # pot belly + harness straps + buckle
    ell(f.b, bc[0], bc[1], 6.6 - squash * 0.2, 6.2 - squash * 0.4, SOOT, ang=lean, bias=0.08)
    line(f.b, bc[0] - 4.0, bc[1] - 4.6, bc[0] + 3.6, bc[1] + 3.0, "tT")
    line(f.b, bc[0] - 5.4, bc[1] + 1.0, bc[0] + 5.6, bc[1] + 0.6, "t")
    f.b.put(*P(bc[0] + 1.0, bc[1] + 0.8), "P")
    imp_head(f, bc[0] + 2.6 + lean * 0.1, bc[1] - 8.2, eyes=eyes, mouth=mouth, s=1.15, goggles=True, dead=dead)
    # front arm (+ a canister in hand), fuse wire to the rack
    shf = (bc[0] + 3.0, bc[1] - 2.6)
    hf = (dx + hand[0], dy + hand[1])
    def farm(c):
        tube(c, [shf, ((shf[0] + hf[0]) / 2, (shf[1] + hf[1]) / 2 + 1), hf], [1.7, 1.5, 1.4], SOOT, bias=0.2)
    if held == "can":
        rect(f.b, hf[0] - 0.4, hf[1] - 4.8, hf[0] + 2.0, hf[1] + 0.4, "rRpP")
        if not dead: f.g.put(*P(hf[0] + 0.8, hf[1] - 2.4), "0"); f.g.put(*P(hf[0] + 0.8, hf[1] - 5.6), "O")
    if held == "mines":
        for k in range(3):
            ell(f.b, hf[0] - 1 + k * 1.8, hf[1] - 1.6 - (k % 2), 1.3, 1.0, IRON_HI, bias=0.2)
            if not dead: f.g.put(*P(hf[0] - 1 + k * 1.8, hf[1] - 2.8 - (k % 2)), "9")
    stamp(f.b, farm, ch="Z")
    for (x, y) in line_px(*P(rk[0] + 1, rk[1] + 2), *P(hf[0], hf[1] + 1)):
        f.n.put(x, y + 1, "e")
    if extra: extra(f, hf, rk)
    return f.done()


def sapper_corpse():
    f = Fr()
    ell(f.b, 0, -4.0, 7.6, 4.0, SOOT, bias=0.0)
    ell(f.b, 8.6, -3.0, 3.2, 2.6, COPPER, bias=0.2)
    for gx in (9.0, 11.0): ell(f.b, gx, -2.6, 1.2, 1.1, BRASS, bias=0.3)
    for k in range(3):
        rect(f.b, -14 + k * 3, -3 - (k % 2), -12 + k * 3, 0, "rRpP")
    bat_wing(f, "b", -6, -5, -160, span=0.55, flap=0)
    f.g.put(-13, -2, "7"); f.g.put(-10, -2, "7")
    return f.done()


def build_sapper(outdir):
    S = sapper
    idle = [S(buzz=0), S(buzz=1, dy=0.3, squash=0.3, tail=0.6), S(buzz=0, dy=0.4, squash=0.4, tail=1.2, eyes="squint"), S(buzz=1, dy=0.2, tail=0.6)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3; s_ = math.sin(ph)
        run.append(S(dx=0.4, dy=-1.0 * abs(math.cos(ph)), lean=8, buzz=i, feet=((-4 - 2.6 * s_, -1.0 * max(0, -math.cos(ph))), (4 + 2.6 * s_, -1.0 * max(0, math.cos(ph)))),
                     hand=(8.0, -11.0 + s_), bhand=(-6.0, -11.0 - s_), tail=i * 0.7))
    # LOB: reach back to the rack, the canister sparks, LOB it (3) in an arc, follow through
    def lit_can(f, hf, rk):
        spark(f.g, hf[0] + 0.8, hf[1] - 6.0, 1, "Y", "O")
    lob = [S(hand=(2.0, -14.0), bhand=(-8.0, -18.0), eyes="squint", buzz=0),
           S(lean=-8, hand=(-6.0, -22.0), bhand=(-8.0, -14.0), held="can", eyes="open", buzz=1, cans=2, extra=lit_can),
           S(lean=-10, hand=(-4.0, -25.0), bhand=(-9.0, -13.0), held="can", eyes="wide", buzz=0, cans=2, squash=0.6, extra=lit_can),
           S(lean=8, dx=1.0, hand=(11.0, -20.0), bhand=(-8.0, -12.0), eyes="wide", mouth=2, buzz=1, cans=2),
           S(lean=6, dx=0.8, hand=(11.0, -15.0), bhand=(-7.0, -12.0), eyes="open", mouth=2, buzz=0, cans=2),
           S(hand=(8.0, -12.0), buzz=1)]
    # MINES: hunch, scoop three mines from the belly pouch, SCATTER them (4), cackle
    def scatter(f, hf, rk):
        for k, (a, b) in enumerate(((6, -6), (10, -3), (4, -2))):
            f.g.put(*P(hf[0] + a, hf[1] + b), "9"); f.g.put(*P(hf[0] + a - 1, hf[1] + b), "5")
    mines = [S(squash=0.8, dy=0.6, hand=(4.0, -9.0), bhand=(-3.0, -9.0), eyes="squint"),
             S(squash=1.0, dy=0.8, hand=(5.0, -8.0), bhand=(-2.0, -8.0), held="mines", eyes="open", buzz=1),
             S(squash=0.4, dy=0.2, hand=(3.0, -12.0), bhand=(-6.0, -12.0), held="mines", eyes="wide", buzz=0, lean=-6),
             S(squash=0.2, hand=(1.0, -16.0), bhand=(-7.0, -15.0), held="mines", eyes="wide", buzz=1, lean=-8),
             S(lean=10, dx=1.0, hand=(12.0, -16.0), bhand=(-8.0, -12.0), eyes="wide", mouth=2, buzz=0, extra=scatter),
             S(lean=6, dx=0.8, hand=(11.0, -14.0), eyes="squint", mouth=3, buzz=1),
             S(lean=2, hand=(9.0, -13.0), eyes="squint", mouth=3, buzz=0, dy=0.3),
             S(hand=(8.0, -12.0), buzz=1)]
    death = [S(lean=-12, hand=(4.0, -22.0), bhand=(-10.0, -20.0), eyes="wide", mouth=2, buzz=0),
             dim_glow(S(lean=-22, dy=1.6, squash=1.6, hand=(6.0, -8.0), eyes="squint", mouth=0, cans=2)),
             dim_glow(grounded(S(lean=-34, dy=3.0, squash=3.0, hand=(8.0, -4.0), bhand=(-9.0, -4.0), eyes="dead", mouth=0, cans=1, dead=True))),
             dim_glow(sapper_corpse())]
    knock = S(lean=-12, dx=-0.8, hand=(4.0, -20.0), bhand=(-10.0, -18.0), eyes="wide", mouth=2)
    build_monster(outdir, "KrnFuseSapper", idle, run,
                  [("Lob", lob, [0.12, 0.14, 0.14, 0.06, 0.12, 0.14]),
                   ("Mines", mines, [0.12, 0.12, 0.12, 0.12, 0.08, 0.14, 0.14, 0.14])],
                  death, knock, idle_d=(0.2, 0.16, 0.2, 0.16), run_d=0.08, death_d=(0.1, 0.14, 0.16, 0.45), remap=IMP_RED, scale=5)


# ================================================================== POLARITY WARG (T3, Lodestone Hound line)
def warg(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, gait=1.0, head=(0.0, 0.0), jaw=0.0, glow=1, ph=0, field=0, eye="open",
         stretch=0.0, crouch=0.0, tail=0.0, mane=1.0, extra=None, dead=False):
    """The hound grown into a lean blued-magnetite wolf: long legs, a bristling mane of iron filings standing on end, the
    hound's copper wing-case saddle and coil antennae, its horseshoe magnet now a great two-pole yoke (red pole, steel
    pole) with a field crackling between the poles, and the coil-spring tail."""
    f = Fr()
    S = 1.45
    ca = math.radians(tilt)
    def R(x, y):
        x, y = x * S + 8.0, y * S
        return (-8.0 + x * math.cos(ca) - y * math.sin(ca) + dx, x * math.sin(ca) + y * math.cos(ca) + dy)
    sx = 1.0 + stretch * 0.22
    hip = R(-5.0 * sx, -7.4 + crouch)
    sho = R(4.4 * sx, -7.8 + crouch * 0.5)
    for i, (j, base) in enumerate(((hip, -7.0), (sho, 6.6))):
        ph_ = legs + i * math.pi + math.pi * 0.5
        lift = max(0.0, math.sin(ph_)) * 2.8 * gait
        fx_ = base + math.cos(ph_) * 4.2 * gait + dx + stretch * (4 if i else -4)
        knee = (j[0] + (2.0 if i == 0 else 0.6), (j[1] - lift) * 0.5 - 2.0)
        line(f.n, j[0] + 1, j[1] + 1, knee[0], knee[1], "[")
        line(f.n, knee[0], knee[1], fx_ + 1, -lift, ">")
        f.n.put(*P(fx_ + 2, -lift), ">")
    # coil-spring tail, longer
    tb = R(-8.0 * sx, -10.8 + crouch)
    for k in range(7):
        a = math.radians(-150 + tail + k * 7)
        x_, y_ = tb[0] + math.cos(a) * k * 1.2, tb[1] + math.sin(a) * k * 1.2 - (k % 2) * 0.8
        f.u.put(*P(x_, y_), "e" if k % 2 == 0 else "Q"); f.u.put(*P(x_, y_ - 1), "q" if k % 2 == 0 else "e")
    # body
    ell(f.b, *R(-0.5 * sx, -9.4 + crouch * 0.8), 7.0 * sx * S, 3.6 * S, IRON, ang=tilt, bias=0.15)
    ell(f.b, *R(4.2 * sx, -10.2 + crouch * 0.5), 4.4 * S, 4.4 * S, IRON, ang=tilt, bias=0.2)
    ell(f.b, *R(-5.4 * sx, -9.2 + crouch), 3.4 * S, 3.4 * S, IRON, ang=tilt, bias=0.1)
    for k in range(5):
        f.b.put(*P(*R((-6.0 + k * 2.4) * sx, -6.6 + crouch * 0.8)), "2")
    # the hound's copper wing-case saddle
    stamp(f.b, lambda c: elytra(c, *R(-4.0 * sx, -12.4 + crouch * 0.8), 4.4 * S, 2.2 * S, ang=tilt), ch="Z")
    # head: long wolf snout
    hx, hy = R(10.0 * sx + head[0], -12.4 + crouch * 0.3 + head[1])
    nb = R(5.0 * sx, -11.6 + crouch * 0.4)
    tube(f.b, [nb, (hx - 1.2, hy + 0.8)], [3.2, 2.4], IRON, bias=0.2)
    def headf(c):
        ell(c, hx, hy, 3.8, 3.2, IRON_L, bias=0.2)
        tube(c, [(hx + 2.0, hy - 0.2), (hx + 7.6, hy + 0.8 - jaw * 0.8)], [2.0, 1.2], IRON_L, bias=0.2)
        c.put(*P(hx + 7.6, hy + 0.2 - jaw * 0.8), "1")
        je = polar(hx + 1.4, hy + 2.0, 5.8, 16 + jaw * 30)
        tube(c, [(hx + 1.4, hy + 1.8), je], [1.3, 0.8], IRON, bias=0.1)
        for sd in (0, 1):   # two swept ears
            line(c, hx - 1.2 + sd * 1.4, hy - 2.4, hx - 3.6 + sd * 1.4, hy - 5.6, "45")
    stamp(f.b, headf, ch="Z")
    coil_antennae(f.b, f.g, hx - 0.2, hy - 2.6, ang=-100 + tilt, L=5.0, spread=30, lit=not dead)
    if jaw > 0.3 and not dead:
        for k in range(3): f.g.put(*P(hx + 3.0 + k * 1.2, hy + 2.0 + k * 0.3), "0" if k == 1 else "9")
    # near legs
    for i, (j, base) in enumerate(((hip, -7.6), (sho, 6.0))):
        ph_ = legs + i * math.pi
        lift = max(0.0, math.sin(ph_)) * 3.0 * gait
        fx_ = base + math.cos(ph_) * 4.4 * gait + dx + stretch * (5 if i else -5)
        knee = (j[0] + (2.4 if i == 0 else 0.6), (j[1] - lift) * 0.5 - 1.4)
        def leg(c, j=j, knee=knee, fx_=fx_, lift=lift):
            tube(c, [j, knee, (fx_, -1.2 - lift)], [2.6, 1.8, 1.3], IRON, bias=0.2)
            line(c, fx_ - 0.8, -lift, fx_ + 2.0, -lift, "4")
        stamp(f.b, leg, ch="Z")
    # the two-pole yoke magnet across the shoulders: red pole and steel pole
    mx, my = R(-2.6 * sx, -13.6 + crouch * 0.6)
    s_ = 1.0
    def yoke(c):
        for sd in (-1, 1):
            tube(c, [(mx + sd * 3.2 * s_, my), (mx + sd * 3.2 * s_, my - 4.2 * s_)], [1.4 * s_, 1.4 * s_], IRON_HI, bias=0.15)
        ell(c, mx, my, 4.6 * s_, 2.0 * s_, IRON_HI, bias=0.1, vmin=-0.1)
        for y in range(int(my - 4.2 * s_ - 1), int(my - 2.6 * s_) + 1):     # red pole on the front, bright steel on the back
            for dxx in (-1, 0, 1):
                c.put(*P(mx + 3.2 * s_ + dxx, y), "a" if dxx > 0 else "o")
                c.put(*P(mx - 3.2 * s_ + dxx, y), "6" if dxx < 0 else "5")
    stamp(f.b, yoke, ch="Z")
    # bristling mane of iron filings along the neck and shoulders, standing on end toward the poles
    for k in range(9):
        b0 = R(1.6 * sx + k * 0.8, -13.0 + crouch * 0.6 + abs(k - 4) * 0.25)
        L = (2.6 + (k % 3) * 1.0) * mane
        e = polar(b0[0], b0[1], L, -100 + (k - 4) * 9 + tilt)
        line(f.b, b0[0], b0[1], e[0], e[1], "45" if k % 2 else "34")
        f.b.put(*P(*e), "6")
    tl, tr = (mx - 3.2 * s_, my - 4.2 * s_ - 1.4), (mx + 3.2 * s_, my - 4.2 * s_ - 1.4)
    if not dead and glow:
        f.g.put(*P(*tl), "9"); f.g.put(*P(*tr), "O")
        if glow >= 2:
            bolt(f.g, tl[0], tl[1] - 0.5, tr[0], tr[1] - 0.5, seed=ph, jag=1.2, step=1.6, halo=None)
    if field and not dead:
        for k in range(field):
            r = 4.0 + k * 3.0
            for a in range(196, 345, 10):
                px_ = mx + math.cos(math.radians(a)) * r * 1.4
                py_ = my - 5.0 * s_ + math.sin(math.radians(a)) * r
                if (a // 10 + k + ph) % 3: f.g.put(*P(px_, py_), "O" if a > 270 else "9")
    ex, ey = hx + 1.0, hy - 0.8
    if eye == "open": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "9")
    elif eye == "wide": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "0"); f.g.put(*P(ex, ey - 1), "9")
    elif eye == "squint": f.g.put(*P(ex, ey), "8")
    elif eye == "dead": f.g.put(*P(ex, ey), "3")
    if extra: extra(f, (hx, hy), (tl, tr))
    return f.done()


def warg_corpse():
    f = Fr()
    ell(f.b, -1, -4.0, 12.0, 4.0, IRON_L, bias=0.0)
    ell(f.b, 12.0, -3.0, 4.0, 3.0, IRON_HI, bias=0.2)
    tube(f.b, [(14, -3), (20, -1)], [1.8, 1.0], IRON_HI)
    for x in range(-8, 6, 2): line(f.b, x, -7.6, x + 1, -9.6, "34")
    stamp(f.b, lambda c: elytra(c, -5, -7, 5.0, 2.4), ch="Z")
    for sd in (-1, 1):
        tube(f.b, [(-17 + sd * 3, 0), (-17 + sd * 3, -4)], [1.4, 1.4], IRON_HI)
    ell(f.b, -17, 0, 4.4, 1.6, IRON_HI, vmin=-0.2)
    f.b.put(-14, -4, "a"); f.b.put(-20, -4, "6")
    f.g.put(13, -4, "3")
    return f.done()


def build_warg(outdir):
    W = warg
    idle = [W(gait=0.0, ph=0, glow=1), W(gait=0.0, ph=1, dy=0.3, head=(0, 0.3), glow=2, tail=8, mane=1.1),
            W(gait=0.0, ph=2, dy=0.4, head=(0, 0.4), glow=1, tail=14, eye="squint", mane=1.2), W(gait=0.0, ph=3, glow=2, tail=6, mane=1.05)]
    run = [W(legs=i * math.pi / 3, gait=1.0, dy=-1.0 * abs(math.sin(i * math.pi / 3)), tilt=-3 * math.cos(i * math.pi / 3),
             stretch=0.3 * math.sin(i * math.pi / 3), head=(0.6, 0.8), ph=i + 4, glow=1 + (i % 2), tail=-12 + 6 * (i % 2), mane=0.8)
           for i in range(6)]
    # SNAP: two quick bites (hits on 2 and 4), the second lunging further
    def snap(f, h, poles):
        hx, hy = h
        for (a, b) in ((8, -1), (9, 2), (7, 3)):
            f.g.put(*P(hx + a, hy + b), "0" if a == 8 else "9")
    snapan = [W(crouch=1.6, tilt=4, head=(-1.0, 1.4), jaw=0.3, glow=2, ph=10, eye="wide", tail=20),
              W(crouch=1.0, tilt=0, head=(-0.5, 0.8), jaw=1.0, glow=2, ph=11, eye="wide", tail=24, dx=-0.6),
              W(stretch=0.6, tilt=-4, head=(2.0, 1.2), jaw=0.0, glow=2, ph=12, eye="wide", dx=2.0, legs=1.0, gait=0.4, extra=snap),
              W(stretch=0.3, crouch=0.8, head=(0.0, 1.0), jaw=1.0, glow=2, ph=13, eye="wide", dx=1.6),
              W(stretch=1.0, tilt=-6, head=(3.0, 1.6), jaw=0.0, glow=2, ph=14, eye="wide", dx=3.4, legs=1.6, gait=0.5, extra=snap),
              W(stretch=0.4, crouch=0.6, head=(1.0, 1.0), jaw=0.2, glow=1, ph=15, dx=2.6),
              W(dx=1.2, head=(0.4, 0.4), glow=1, ph=16)]
    # POLARIZE: rear up, the poles flare, the field snaps out (3: the hero within reach is magnetized), hold, settle
    polar_ = [W(crouch=1.4, head=(-1.0, 1.6), glow=1, ph=20, eye="squint", mane=1.2),
              W(tilt=-8, head=(-1.4, -1.6), jaw=0.6, glow=2, ph=21, field=1, eye="wide", mane=1.5),
              W(tilt=-12, head=(-1.8, -2.4), jaw=0.9, glow=2, ph=22, field=2, eye="wide", mane=1.8),
              W(tilt=-14, head=(-2.0, -2.8), jaw=1.0, glow=2, ph=23, field=3, eye="wide", mane=2.0),
              W(tilt=-12, head=(-2.0, -2.6), jaw=1.0, glow=2, ph=24, field=2, eye="wide", mane=1.9),
              W(tilt=-8, head=(-1.4, -1.6), jaw=0.6, glow=2, ph=25, field=1, eye="wide", mane=1.5),
              W(tilt=-3, head=(-0.6, -0.4), jaw=0.2, glow=1, ph=26, mane=1.2),
              W(glow=1, ph=27)]
    death = [W(crouch=0.5, tilt=-12, head=(-1, -2.5), jaw=1.0, glow=2, ph=30, eye="wide", tail=30, mane=2.0),
             dim_glow(W(dy=1.0, tilt=-18, head=(0, 1.5), jaw=0.6, glow=0, eye="dead", legs=1.0, dead=True, mane=0.6)),
             dim_glow(grounded(W(dy=2.0, tilt=-28, head=(0, 3), jaw=0.4, glow=0, eye="dead", legs=2.0, dead=True, mane=0.4))),
             dim_glow(warg_corpse())]
    knock = W(crouch=0.5, tilt=-10, head=(-1, -1.5), jaw=0.6, glow=2, ph=33, eye="wide", tail=24, dx=-0.8, mane=1.6)
    build_monster(outdir, "KrnPolarityWarg", idle, run,
                  [("Snap", snapan, [0.12, 0.1, 0.06, 0.08, 0.06, 0.12, 0.14]),
                   ("Polarize", polar_, [0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.14])],
                  death, knock, idle_d=(0.22, 0.16, 0.22, 0.16), run_d=0.07, death_d=(0.1, 0.14, 0.16, 0.45), remap=WARG_STEEL, scale=5)


# ================================================================== SCARAB MAGUS (T3, Stormcaller line)
def magus(dx=0.0, dy=0.0, lean=0.0, sway=0.0, staff_a=-88.0, shand=None, bhand=(-6.0, -17.0), shell=0.0, orb=0.0, ph=0,
          charge=1, eyes="open", hem=0.0, extra=None, dead=False, fade=0.0, staff_on=True):
    """The Stormcaller grown into a scarab priest: the caller's robe (storm violet), its copper beetle-shell hood now a
    great scarab carapace on the back whose two halves lift like wings when it casts, the coil antennae, and a staff
    crowned with a copper sun-disc holding ball lightning."""
    f = Fr()
    top = -24.0 + dy
    # carapace halves behind (lift with shell 0..1)
    for sd, layer in ((-1, f.n), (1, f.u)):
        ang = -60 - shell * 70 if sd > 0 else -100 - shell * 50
        cx_, cy_ = dx - 3.0 + lean * 0.1, top + 3.0
        def half(c, ang=ang, cx_=cx_, cy_=cy_, sd=sd):
            e = polar(cx_, cy_, 7.0, ang + 180 if shell < 0.3 else ang)
            ell(c, (cx_ + e[0]) / 2 - 1.0, (cy_ + e[1]) / 2 + 3.0 - shell * 3.0, 4.6, 9.0 - shell * 2.0, COPPER,
                ang=(ang + 90) * (0.2 + shell * 0.8), bias=0.15 if sd > 0 else -0.35)
        half(layer)
    # robe
    hem_pts = []
    for k in range(11):
        x = -8.0 + k * 1.6 + dx + sway * (k / 10.0)
        y = -(0.0 if k % 2 == 0 else 0.8) - abs(math.sin(k + hem)) * 0.8
        hem_pts.append((x, y))
    def robe_shade(X, Y):
        u = (X - dx) / 7.0; v = (Y - top) / (-top + 0.01)
        l = -u * 0.7 - v * 0.2 + 0.25
        if (X - dx + int(v * 3)) % 4 == 0 and v > 0.3: l -= 0.45
        return pick(CLOTH, l)
    poly(f.b, [(dx - 3.6 + lean * 0.15, top), (dx + 3.6 + lean * 0.15, top + 0.4), (dx + 8.4 + sway, -1.0), *reversed(hem_pts),
               (dx - 8.2 + sway * 0.5, -1.0)], "N", shade=robe_shade)
    for (x, y) in hem_pts: f.b.put(*P(x, y), "e")
    # copper scarab clasp + belt
    line(f.b, dx - 5.0, -13.0 + dy, dx + 5.0 + sway * 0.3, -12.6 + dy, "q")
    ell(f.b, dx + 1.0, -12.8 + dy, 1.6, 1.2, COPPER, bias=0.3)
    # back arm
    shb = (dx - 2.8 + lean * 0.15, top + 2.0)
    hb = (dx + bhand[0], dy + bhand[1])
    eb, _ = ik(shb[0], shb[1], hb[0], hb[1], 5.0, 5.0, bend=-1)
    tube(f.u, [shb, eb, hb], [1.8, 1.5, 1.3], CLOTH, bias=0.0)
    f.u.put(*P(*hb), "Q")
    # elytra mantle (the caller's) and hood (copper shell) with antennae
    stamp(f.b, lambda c: elytra(c, dx - 0.8 + lean * 0.12, top + 2.6, 6.6, 2.8), ch="1")
    hx, hy = dx + 1.0 + lean * 0.18, top - 3.6
    def hood(c):
        ell(c, hx, hy, 4.0, 4.0, COPPER, bias=-0.1)
        poly(c, [(hx - 3.2, hy - 2.8), (hx - 0.4, hy - 5.6), (hx + 1.0, hy - 3.2)], "Q")
        line(c, hx - 0.8, hy - 5.0, hx - 2.8, hy + 2.8, "q")
        ell(c, hx + 1.8, hy + 0.8, 2.0, 2.6, "1112", bias=-0.2)
        line(c, hx - 3.0, hy + 3.0, hx + 3.2, hy + 3.2, "3")
    stamp(f.b, hood, ch="1")
    coil_antennae(f.b, f.g, hx - 1.6, hy - 3.2, ang=-130, L=5.4, spread=30, lit=not dead)
    ex, ey = hx + 1.8, hy + 0.4
    if eyes == "open": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "9")
    elif eyes == "wide": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex + 1, ey), "0"); f.g.put(*P(ex, ey - 1), "9")
    elif eyes == "squint": f.g.put(*P(ex, ey), "8")
    elif eyes == "dead": f.g.put(*P(ex, ey), "3")
    # staff with the copper sun-disc
    shf = (dx + 3.0 + lean * 0.15, top + 2.0)
    sx, sy = dx + 9.0, -1.0 + dy * 0.3
    if shand is None: shand = polar(sx, sy, 14.0, staff_a)
    disc = None
    if staff_on:
        e = polar(sx, sy, 27.0, staff_a)
        def shaft(c):
            pts = line(c, sx, sy, e[0], e[1], "4")
            for i, (x, y) in enumerate(pts):
                if i % 5 == 2: c.put(x, y, "6")
        stamp(f.b, shaft, ch="1", sides=((1, 0), (-1, 0)))
        disc = polar(e[0], e[1], 2.6, staff_a)
        for k in range(16):
            a = 2 * math.pi * k / 16
            f.b.put(*P(disc[0] + 3.0 * math.cos(a), disc[1] + 3.0 * math.sin(a)), "E" if math.cos(a) + math.sin(a) < 0 else "Q")
        if not dead and charge:
            f.g.put(*P(*disc), "0"); f.g.put(*P(disc[0] + 1, disc[1]), "9"); f.g.put(*P(disc[0], disc[1] + 1), "9")
            if charge >= 2: crackle(f.g, disc[0], disc[1], ph, r=5, seed=7)
    ef, _ = ik(shf[0], shf[1], shand[0], shand[1], 5.0, 5.0, bend=1)
    def farm(c):
        tube(c, [shf, ef, shand], [1.9, 1.6, 1.4], CLOTH, bias=0.3)
        c.put(*P(*shand), "Q")
    stamp(f.b, farm, ch="1")
    if orb > 0 and disc and not dead:
        r = orb
        for y in range(int(disc[1] - r) - 1, int(disc[1] + r) + 2):
            for x in range(int(disc[0] - r) - 1, int(disc[0] + r) + 2):
                d = math.hypot(x - disc[0], y - disc[1]) / r
                if d <= 1: f.g.put(x, y, "0" if d < 0.5 else "9")
    if extra: extra(f, disc, (hx, hy))
    out = f.done()
    if fade > 0:   # dissolving into lightning (Bolt Step): body pixels thinned out and turned to arcs
        rnd = random.Random(ph)
        px = {}
        for k, v in out.px.items():
            r = rnd.random()
            if r < fade * 0.8: continue
            px[k] = ("9" if r < fade else v) if v not in "Z" else ("8" if r < fade else v)
        out = Spr(px)
    return out


def magus_corpse():
    f = Fr()
    ell(f.b, 2, -2.6, 8.0, 2.6, COPPER, bias=0.0)
    poly(f.b, [(-12, 0), (-8, -4.0), (6, -4.6), (10, -2.0), (10, 0)], "N", shade=lambda X, Y: "v" if Y < -3 else "N" if X < 2 else "n")
    ell(f.b, 11.0, -2.6, 2.8, 2.6, COPPER, bias=0.1)
    line(f.b, -20, 0, 2, -1, "4")
    for k in range(10):
        a = 2 * math.pi * k / 10
        f.b.put(*P(-22 + 2.4 * math.cos(a), -2 + 2.4 * math.sin(a)), "Q")
    f.g.put(-22, -2, "7")
    return f.done()


def build_magus(outdir):
    M = magus
    idle = [M(ph=0), M(ph=1, dy=0.3, hem=0.6, sway=0.3, shell=0.05), M(ph=2, dy=0.4, hem=1.2, sway=0.5, charge=2, eyes="squint"), M(ph=3, dy=0.2, hem=1.8, sway=0.2)]
    run = [M(dx=0.4, lean=6, ph=4 + i, hem=i * 0.9, sway=[-1.0, -0.4, 0.4, 1.0, 0.4, -0.4][i], dy=-0.5 * abs(math.sin(i * math.pi / 3)),
             staff_a=-80, bhand=(-6.0 + math.sin(i) * 1.5, -16.0)) for i in range(6)]
    # ORB: raise the staff, ball lightning gathers in the sun-disc, THRUST (release 3), settle
    orb = [M(ph=10, staff_a=-80, charge=2, eyes="open"), M(ph=11, staff_a=-70, orb=1.4, charge=2, eyes="wide", lean=-4),
           M(ph=12, staff_a=-62, orb=2.2, charge=2, eyes="wide", lean=-6, shell=0.2),
           M(ph=13, staff_a=-40, shand=(14.0, -18.0), orb=0.0, charge=2, eyes="wide", lean=8, dx=1.0),
           M(ph=14, staff_a=-55, charge=1, eyes="open", lean=4, dx=0.6), M(ph=15, staff_a=-80, charge=1)]
    # BOLT STEP: the carapace splits open (0-2), it dissolves into lightning (3: it is gone, reappears by the hero), re-forms
    def column(n):
        def fn(f, disc, h):
            for k in range(n):
                bolt(f.g, -2 + k * 2, -2, k - 1, -36, seed=k * 7 + n, jag=1.4, step=2.0, halo="7")
        return fn
    step = [M(ph=20, shell=0.3, charge=2, eyes="wide", bhand=(-8.0, -22.0)),
            M(ph=21, shell=0.7, charge=2, eyes="wide", bhand=(-9.0, -26.0), staff_a=-95, dy=-0.4),
            M(ph=22, shell=1.0, charge=2, eyes="wide", bhand=(-9.0, -28.0), staff_a=-100, dy=-0.8, extra=column(1)),
            M(ph=23, shell=1.0, charge=2, eyes="wide", fade=0.9, dy=-0.8, extra=column(3)),
            M(ph=24, shell=1.0, charge=2, eyes="wide", fade=0.6, dy=-0.6, extra=column(2)),
            M(ph=25, shell=0.7, charge=2, eyes="wide", fade=0.25, dy=-0.3, extra=column(1)),
            M(ph=26, shell=0.3, charge=1, eyes="open"),
            M(ph=27, charge=1)]
    death = [M(ph=30, shell=0.8, lean=-10, eyes="wide", staff_a=-120, charge=2),
             dim_glow(M(ph=31, lean=-20, dy=2.0, eyes="squint", staff_on=False, bhand=(-8.0, -10.0), shell=0.4)),
             dim_glow(grounded(M(ph=32, lean=-34, dy=6.0, eyes="dead", staff_on=False, dead=True, bhand=(-8.0, -6.0)))),
             dim_glow(magus_corpse())]
    knock = M(ph=33, lean=-12, dx=-0.6, shell=0.5, staff_a=-110, eyes="wide", charge=2)
    build_monster(outdir, "KrnScarabMagus", idle, run,
                  [("Orb", orb, [0.12, 0.14, 0.12, 0.06, 0.12, 0.14]),
                   ("Step", step, [0.1, 0.12, 0.12, 0.06, 0.1, 0.12, 0.12, 0.14])],
                  death, knock, idle_d=(0.22, 0.18, 0.22, 0.18), run_d=0.09, death_d=(0.1, 0.14, 0.16, 0.45), remap=VIOLET_CLOTH, scale=5)


# ================================================================== VOLTAIC PILE (T3, Leyden Golem line)
def jar_glass(nu, nv, d, l, ch, x, y):
    if d > 0.72: return "V" if (nu + nv) < -0.4 else ("v" if (nu + nv) < 0.5 else "N")
    if d > 0.55 and (nu + nv) < -0.6: return "W"
    return "n"


def pile(dx=0.0, dy=0.0, tilt=0.0, feet=((-4, 0), (4, 0)), arm=(30.0, 60.0), barm=(150.0, 110.0), charge=1, ph=0, eye="open",
         extra=None, dead=False, squash=0.0, lash=None):
    """The Leyden Golem grown into a voltaic pile: a tall column of copper and zinc discs on thick iron legs, the golem's
    glass jar (lightning inside, lid and terminal posts) set on top as its head, its copper coil arms now long lashes."""
    f = Fr()
    bx = dx + tilt * 0.05
    y0 = -7.0 + dy + squash
    n = 6
    hgt = 2.7 - squash * 0.15
    # legs
    for i, (fx_, fy_) in enumerate(feet):
        c = f.u if i == 0 else f.b
        hx_ = bx + (-3.0 if i == 0 else 3.0)
        tube(c, [(hx_, y0), (fx_ + dx * 0.3, fy_ - 2.0)], [2.2, 2.0], IRON, bias=-0.1 if i == 0 else 0.15)
        rect(c, fx_ + dx * 0.3 - 2.8, fy_ - 2.2, fx_ + dx * 0.3 + 2.8, fy_, "2345")
    def coil_arm(c, sx_, sy_, a1, a2, L1=5.4, L2=5.0):
        e = polar(sx_, sy_, L1, a1)
        h = polar(e[0], e[1], L2, a2)
        tube(c, [(sx_, sy_), e, h], [1.5, 1.3, 1.2], COPPER, bias=0.0)
        for k, (x, y) in enumerate(line_px(*P(sx_, sy_), *P(*h))):
            if k % 2: c.put(x, y, "q")
        tube(c, [h, polar(h[0], h[1], 1.8, a2)], [1.7, 1.7], IRON_HI, bias=0.2)
        return polar(h[0], h[1], 2.0, a2)
    top = y0 - n * hgt
    coil_arm(f.u, bx - 5.2, top + 5.0, barm[0], barm[1])
    # the disc stack, bottom up: copper / felt / zinc
    for k in range(n):
        cy = y0 - k * hgt - hgt * 0.5
        rx = 6.0 - abs(k - n * 0.45) * 0.18
        ramp = COPPER if k % 2 == 0 else IRON_HI
        ell(f.b, bx + math.sin(k * 0.7 + ph * 0.3) * 0.15 * squash, cy, rx, hgt * 0.62, ramp, bias=0.2)
        line(f.b, bx - rx + 0.6, cy + hgt * 0.5, bx + rx - 0.6, cy + hgt * 0.5, "1")
    # lightning crawling up the stack
    if not dead and charge:
        for k in range(min(n, 2 + charge * 2)):
            cy = y0 - k * hgt - hgt * 0.5
            x = bx + (3.6 if (k + ph) % 2 else -3.0)
            f.g.put(*P(x, cy), "0" if charge >= 3 else "9")
            if charge >= 2: f.g.put(*P(x + (1 if (k + ph) % 2 else -1), cy - 1), "8")
    # the jar head
    jx, jy = bx + 0.6, top - 4.4
    ell(f.b, jx, jy, 4.2, 4.4, CLOTH, shader=jar_glass)
    if not dead:
        bolt(f.g, jx - 0.4, jy + 3.0, jx + 0.4, jy - 3.0, seed=ph, jag=1.0, step=1.5, halo="7" if charge < 3 else "8")
        f.g.put(*P(jx, jy), "0")
    for k in range(-2, 2): f.b.put(*P(jx - 2.6, jy + k), "W" if k < 0 else "V")
    line(f.b, jx - 3.4, jy + 2.2, jx + 3.4, jy + 2.2, "eQ")
    cy0 = jy - 4.8
    def lid(c):
        rect(c, jx - 3.4, cy0 - 1.2, jx + 3.4, cy0 + 0.6, "2345")
        for sd in (-1, 1):
            tx = jx + sd * 2.0
            line(c, tx, cy0 - 1.2, tx + sd * 0.6, cy0 - 4.0, "4")
            c.put(*P(tx + sd * 0.6, cy0 - 4.6), "6")
    stamp(f.b, lid, ch="Z")
    tips = [(jx - 2.0 - 0.6, cy0 - 5.2), (jx + 2.0 + 0.6, cy0 - 5.2)]
    ex, ey = jx + 1.4, jy - 1.0
    for xx in range(-1, 3): f.b.put(*P(ex + xx, ey), "1")
    if eye != "dead":
        f.g.put(*P(ex, ey), "0" if eye in ("open", "wide") else "8"); f.g.put(*P(ex + 1, ey), "9" if eye != "squint" else "8")
        if eye == "wide": f.g.put(*P(ex + 2, ey), "0")
    if not dead:
        for t in tips: f.g.put(*P(*t), "9" if charge < 2 else "0")
    tmp = Canvas()
    fh = coil_arm(tmp, bx + 5.2, top + 5.0, arm[0], arm[1])
    stamp(f.b, lambda c: coil_arm(c, bx + 5.2, top + 5.0, arm[0], arm[1]), ch="Z")
    if lash and not dead:   # the lightning lash trailing from the clamp hand
        pts = [fh]
        for k in range(lash[0]):
            pts.append(polar(pts[-1][0], pts[-1][1], 3.0, lash[1] + k * lash[2]))
        for a, b in zip(pts, pts[1:]):
            bolt(f.g, a[0], a[1], b[0], b[1], seed=ph + len(pts), jag=0.6, step=1.5, halo="7")
    if extra: extra(f, tips, fh, (jx, jy))
    return f.done()


def pile_corpse():
    f = Fr()
    for k in range(6):
        ell(f.b, -10 + k * 4.0, -2.0 - (k % 2) * 0.6, 2.0, 2.2, COPPER if k % 2 == 0 else IRON_HI, bias=0.2)
    ell(f.b, 14, -3.0, 3.6, 3.0, CLOTH, shader=jar_glass)
    rect(f.b, 17, -5, 19, -1, "2345")
    for (x, y) in ((10, 0), (21, 0)): f.b.put(x, y, "W")
    f.g.put(14, -3, "7")
    return f.done()


def build_pile(outdir):
    V = pile
    idle = [V(ph=0, charge=1), V(ph=1, charge=1, dy=0.3, squash=0.3), V(ph=2, charge=2, dy=0.4, squash=0.4), V(ph=3, charge=1, dy=0.1)]
    run = [V(dx=0.4, tilt=[-6, -2, 4, 6, 2, -4][i], dy=-0.6 * abs(math.sin(i * math.pi / 3)), ph=4 + i, charge=1 + (i % 2),
             feet=((-4 - 2.4 * math.sin(i * math.pi / 3), -0.8 * max(0, -math.cos(i * math.pi / 3))),
                   (4 + 2.4 * math.sin(i * math.pi / 3), -0.8 * max(0, math.cos(i * math.pi / 3)))),
             arm=(40 + 14 * math.sin(i * 1.05), 70), barm=(140 - 14 * math.sin(i * 1.05), 110)) for i in range(6)]
    # WHIP: coil arm cocks back, charge climbs, LASH forward (3: hit), the lash trails, recoil
    whip = [V(ph=10, charge=2, arm=(120, 160), eye="open"),
            V(ph=11, charge=2, arm=(170, 200), eye="wide", tilt=-6, lash=(2, 160, 20)),
            V(ph=12, charge=3, arm=(-130, -100), eye="wide", tilt=-4, lash=(3, -110, 30)),
            V(ph=13, charge=3, arm=(-10, 10), eye="wide", tilt=6, dx=1.0, lash=(7, 0, 2)),
            V(ph=14, charge=2, arm=(10, 30), eye="wide", tilt=5, dx=0.8, lash=(6, 20, 6)),
            V(ph=15, charge=1, arm=(30, 60), eye="open", tilt=2, lash=(3, 50, 10)),
            V(ph=16, charge=1, eye="open")]
    # NOVA: squat, the stack lights disc by disc (1-3), DISCHARGE in every direction (4), settle
    def nova(n):
        def fn(f, tips, fh, jc):
            for k in range(8):
                a = k * 45 + 22
                p0 = polar(jc[0], jc[1] + 8, 6, a)
                p1 = polar(jc[0], jc[1] + 8, 6 + n * 3, a)
                if p1[1] < -1: bolt(f.g, p0[0], p0[1], p1[0], p1[1], seed=k + n * 9, jag=0.8, step=1.6, halo=None)
        return fn
    novaan = [V(ph=20, charge=1, squash=1.0, dy=0.6, arm=(80, 120), barm=(100, 60), eye="squint"),
              V(ph=21, charge=2, squash=0.8, dy=0.4, arm=(60, 100), barm=(120, 80), eye="wide"),
              V(ph=22, charge=3, squash=0.4, arm=(-40, -80), barm=(220, 260), eye="wide"),
              V(ph=23, charge=3, squash=0.0, dy=-0.4, arm=(-50, -90), barm=(230, 270), eye="wide", extra=nova(1)),
              V(ph=24, charge=3, squash=-0.4, dy=-0.8, arm=(-60, -100), barm=(240, 280), eye="wide", extra=nova(3)),
              V(ph=25, charge=2, squash=0.6, dy=0.4, arm=(20, 60), barm=(160, 120), eye="wide", extra=nova(2)),
              V(ph=26, charge=1, squash=0.3, arm=(30, 60), eye="open"),
              V(ph=27, charge=1)]
    death = [V(ph=30, charge=3, tilt=-10, arm=(-50, -90), barm=(230, 270), eye="wide"),
             dim_glow(V(ph=31, charge=1, tilt=-20, dy=1.6, eye="dead", dead=True, arm=(100, 140), barm=(80, 40), squash=1.0)),
             dim_glow(grounded(V(ph=32, charge=0, tilt=-36, dy=4.0, eye="dead", dead=True, squash=2.0))),
             dim_glow(pile_corpse())]
    knock = V(ph=33, charge=2, tilt=-10, dx=-0.6, arm=(-30, -60), barm=(200, 240), eye="wide")
    build_monster(outdir, "KrnVoltaicPile", idle, run,
                  [("Whip", whip, [0.12, 0.14, 0.1, 0.06, 0.1, 0.12, 0.14]),
                   ("Nova", novaan, [0.12, 0.12, 0.12, 0.12, 0.08, 0.14, 0.14, 0.14])],
                  death, knock, idle_d=(0.22, 0.16, 0.22, 0.16), run_d=0.1, death_d=(0.1, 0.14, 0.16, 0.45), scale=5)


# ================================================================== TESLA SPIRE (T3, Arc Lantern line, floating)
def spire(dx=0.0, dy=0.0, tilt=0.0, fin=0.0, core=1.0, ph=0, crown=1, eye="open", hover=3.0, extra=None, dead=False, sway=0.0):
    """The lantern raised on a tesla coil: a long copper secondary coil hanging beneath the brass lantern (the wisp's
    coil tail grown into a tower), the lantern's fins, and an iron toroid crown that throws the arcs."""
    f = Fr()
    base = -hover + dy
    cx = dx + tilt * 0.08
    # secondary coil column, tapering down to a point
    for k in range(9):
        y = base - 3.0 - k
        w = 1.2 + k * 0.24
        x = cx + math.sin(k * 0.5 + sway) * 0.3
        line(f.b, x - w, y, x + w, y, "eQ" if k % 2 == 0 else "Qq")
        f.b.put(*P(x - w, y), "E" if k % 2 == 0 else "e")
    line(f.b, cx, base - 3.0, cx, base - 1.0, "4"); f.b.put(*P(cx, base), "5")
    lc = (cx, base - 17.4)
    lantern_fins(f, lc[0], lc[1], s=1.0, fin=fin)
    lantern_body(f, lc[0], lc[1], s=1.0, core=core, ph=ph, eye=eye, dead=dead, handle=False)
    # iron stem and the toroid crown
    tc = (cx, lc[1] - 11.0)
    line(f.b, cx, lc[1] - 8.6, cx, tc[1] + 1.0, "45")
    def torus(c):
        ell(c, tc[0], tc[1], 7.0, 2.6, IRON_HI, bias=0.25)
        ell(c, tc[0], tc[1] - 0.2, 3.6, 1.0, "1112", bias=-0.3)
    stamp(f.b, torus, ch="Z")
    line(f.b, cx, tc[1] - 1.0, cx, tc[1] - 3.6, "56")
    if not dead:
        f.g.put(*P(cx, tc[1] - 4.2), "0")
        if crown >= 1:
            rnd = random.Random(ph * 5 + crown)
            for k in range(crown + 1):
                a = rnd.uniform(-170, -10)
                p0 = (tc[0] + 7.0 * math.cos(math.radians(a)), tc[1] + 2.6 * math.sin(math.radians(a)))
                p1 = polar(p0[0], p0[1], 3 + crown * 1.6, a + rnd.uniform(-20, 20))
                bolt(f.g, p0[0], p0[1], p1[0], p1[1], seed=k + ph * 3, jag=0.9, step=1.6, halo=None)
    if extra: extra(f, tc, lc)
    return f.done()


def spire_corpse():
    f = Fr()
    for k in range(12):
        x = -14 + k * 1.2
        line(f.b, x, -1 - k * 0.12, x, 0, "e" if k % 2 == 0 else "Q")
    lantern_body(f, 4, -5.0, s=0.8, dead=True, handle=False)
    ell(f.b, 13, -2.2, 3.6, 2.2, IRON_HI, bias=0.2)
    ell(f.b, 13, -2.4, 1.6, 0.8, "1112")
    return f.done()


def build_spire(outdir):
    T = spire
    idle = [T(ph=0, crown=1), T(ph=1, dy=-0.4, fin=8, crown=2, sway=0.6), T(ph=2, dy=-0.6, fin=12, crown=1, sway=1.2), T(ph=3, dy=-0.2, fin=6, crown=2, sway=1.8)]
    run = [T(dx=0.4, tilt=10, dy=[-0.2, -0.7, -1.0, -0.6, 0.0, 0.1][i], fin=[0, 14, 24, 14, 4, 0][i], ph=i + 4, crown=1 + (i % 2), sway=i * 0.8)
           for i in range(6)]
    # RELAY: the crown charges (0-2), the bolt leaves for the nearest rod (3), the lantern flickers (4-5)
    def jump(f, tc, lc):
        bolt(f.g, tc[0] + 7, tc[1], tc[0] + 14, tc[1] + 4, seed=4, jag=1.0, step=1.6, halo="8")
        spark(f.g, tc[0] + 7, tc[1], 2)
    relay = [T(ph=10, crown=2, eye="open"), T(ph=11, crown=3, eye="wide", fin=-14, core=1.2), T(ph=12, crown=4, eye="wide", fin=-22, core=1.4, dy=-0.6),
             T(ph=13, crown=1, eye="wide", fin=20, core=0.9, dy=-0.4, extra=jump), T(ph=14, crown=1, core=0.8, fin=10), T(ph=15, crown=1, fin=4)]
    # PYLON: dips, the crown floods (2-3), a bolt drives a pylon into the floor ahead (4), recovers
    def drive(f, tc, lc):
        bolt(f.g, tc[0] + 6, tc[1] + 1, tc[0] + 13, -1, seed=9, jag=1.4, step=2.0, halo="8")
        spark(f.g, tc[0] + 13, -2, 2)
    pylon = [T(ph=20, crown=1, dy=0.8, eye="squint"), T(ph=21, crown=2, dy=0.4, fin=-12, core=1.2), T(ph=22, crown=4, dy=-0.8, fin=-26, core=1.5, eye="wide"),
             T(ph=23, crown=5, dy=-1.2, fin=-30, core=1.6, eye="wide"), T(ph=24, crown=2, dy=-0.6, fin=26, core=1.2, eye="wide", tilt=6, extra=drive),
             T(ph=25, crown=1, dy=-0.2, fin=14, tilt=4), T(ph=26, crown=1, fin=6), T(ph=27, crown=1)]
    death = [T(ph=30, crown=5, eye="wide", fin=-30, tilt=-14, core=1.6),
             dim_glow(T(ph=31, crown=0, eye="squint", fin=40, tilt=-28, dy=3.0, core=0.6)),
             dim_glow(grounded(T(ph=32, crown=0, eye="dead", fin=60, tilt=-40, dy=5.0, dead=True))),
             dim_glow(spire_corpse())]
    knock = T(dx=-0.6, ph=33, crown=3, eye="wide", fin=-30, tilt=-14)
    build_monster(outdir, "KrnTeslaSpire", idle, run,
                  [("Relay", relay, [0.12, 0.12, 0.12, 0.06, 0.12, 0.14]),
                   ("Pylon", pylon, [0.12, 0.12, 0.12, 0.12, 0.08, 0.12, 0.14, 0.14])],
                  death, knock, idle_d=(0.18, 0.18, 0.18, 0.18), run_d=0.09, death_d=(0.1, 0.14, 0.16, 0.45), scale=5)


# ================================================================== STATIC MOTH (T3, Arc Lantern line, flying)
def moth(dx=0.0, dy=0.0, tilt=0.0, flap=0.0, core=1.0, ph=0, eye="open", ant=0.0, hover=6.0, extra=None, dead=False, glow=1):
    """A great ash moth drawn to the forge light: the brass lantern is now its glowing abdomen (core inside), the lantern's
    fins have grown into wide dusty wings marked with lightning eyespots, and copper comb antennae."""
    f = Fr()
    base = -hover + dy
    th = (dx + 2.0, base - 13.0)
    def wing(layer, root, ang, span, far):
        c = getattr(f, layer)
        a = ang + flap
        t1 = polar(root[0], root[1], 13.0 * span, a)
        t2 = polar(root[0], root[1], 11.0 * span, a - 48)
        t3 = polar(root[0], root[1], 6.0 * span, a + 40)
        pts = [root, t3, t1, t2]
        def sh(X, Y):
            l = -((X - root[0]) * 0.5 + (Y - root[1]) * 0.6) / (10.0 * span) + (-0.55 if far else 0.05)
            return pick(MOTH, l)
        poly(c, pts, "s", shade=sh)
        # copper veins
        for t in (t1, t2):
            for (x, y) in line_px(*P(*root), *P((root[0] + t[0]) / 2 + (t[0] - root[0]) * 0.25, (root[1] + t[1]) / 2 + (t[1] - root[1]) * 0.25)):
                c.put(x, y, "Q" if not far else "q")
        eye_c = ((root[0] + t1[0] + t2[0]) / 3, (root[1] + t1[1] + t2[1]) / 3)
        return eye_c
    # hind wings (far, then near), forewings
    ec_far = wing("n", (th[0] + 0.5, th[1] - 1.5), -78 + tilt, 1.35, True)
    # abdomen: the brass lantern hanging behind, tipped back
    ab = (th[0] - 6.0, th[1] + 3.5)
    lantern_body(f, ab[0], ab[1], s=0.9, core=core, ph=ph, eye="none", dead=dead, handle=False, layer="u")
    # fuzzy thorax + head
    def body(c):
        ell(c, th[0], th[1], 3.6, 3.4, MOTH, bias=0.15)
        for k in range(6):
            a = k * 60 + ph * 10
            c.put(*P(th[0] + 3.8 * math.cos(math.radians(a)), th[1] + 3.6 * math.sin(math.radians(a))), "A" if k < 3 else "S")
        ell(c, th[0] + 4.0, th[1] - 1.0, 2.2, 2.0, MOTH, bias=0.25)
    stamp(f.b, body, ch="Z")
    # legs dangling
    for k in range(3):
        b0 = (th[0] - 1 + k * 1.6, th[1] + 3.0)
        line(f.b, b0[0], b0[1], b0[0] + 0.6 + k * 0.4, b0[1] + 4.0, "3")
    # copper comb antennae
    for sd in (0, 1):
        r0 = (th[0] + 4.6 + sd, th[1] - 2.6)
        tip = polar(r0[0], r0[1], 6.0, -70 - sd * 20 + ant)
        for k, (x, y) in enumerate(line_px(*P(*r0), *P(*tip))):
            f.b.put(x, y, "e")
            if k % 2 == 0 and k > 0: f.b.put(x + 1, y, "Q")
    ec = wing("b", (th[0] - 0.5, th[1] - 1.5), -128 + tilt, 1.6, False)
    if not dead and glow:
        for (x0, y0), big in ((ec, True), (ec_far, False)):
            r = 1.8 if big else 1.2
            for k in range(12):
                a = 2 * math.pi * k / 12
                f.g.put(*P(x0 + r * math.cos(a), y0 + r * math.sin(a)), "8")
            f.g.put(*P(x0, y0), "0" if big else "9")
            if big and ph % 2: f.g.put(*P(x0 + 1, y0), "9")
        ex, ey = th[0] + 5.0, th[1] - 1.4
        if eye == "open": f.g.put(*P(ex, ey), "0")
        elif eye == "wide": f.g.put(*P(ex, ey), "0"); f.g.put(*P(ex, ey + 1), "9")
        elif eye == "squint": f.g.put(*P(ex, ey), "8")
    if extra: extra(f, th, ab, ec)
    return f.done()


def moth_corpse():
    f = Fr()
    poly(f.b, [(-14, 0), (-4, -7), (2, -1)], "s", shade=lambda X, Y: pick(MOTH, -(X + Y) / 12.0))
    poly(f.b, [(2, 0), (10, -5), (14, 0)], "s", shade=lambda X, Y: pick(MOTH, -(X + Y) / 14.0 - 0.3))
    ell(f.b, 0, -2.4, 3.2, 2.4, MOTH, bias=0.1)
    lantern_body(f, -5, -3.4, s=0.6, dead=True, handle=False)
    for k in range(4): f.b.put(4 + k, -4 - k, "e")
    return f.done()


def build_moth(outdir):
    M = moth
    idle = [M(flap=0, ph=0), M(flap=14, dy=0.6, ph=1, ant=4), M(flap=26, dy=1.0, ph=2, ant=8, eye="squint"), M(flap=12, dy=0.4, ph=3, ant=4)]
    run = [M(dx=0.4, tilt=-6, flap=[0, 18, 32, 18, 4, -10][i], dy=[-0.4, 0.4, 1.0, 0.4, -0.4, -0.8][i], ph=i, ant=-6) for i in range(6)]
    # DARTS: wings sweep back (0-2), FLAP forward flinging two scale darts (3), recover
    def flick(f, th, ab, ec):
        for k in range(3): f.g.put(*P(th[0] + 7 + k, th[1] - 1 + (k % 2) * 2), "0" if k == 0 else "9")
    darts = [M(flap=-10, ph=10, eye="open"), M(flap=-26, ph=11, eye="wide", dy=-0.4), M(flap=-36, ph=12, eye="wide", dy=-0.8, core=1.2),
             M(flap=36, ph=13, eye="wide", dx=0.8, extra=flick), M(flap=22, ph=14, eye="open", dx=0.6), M(flap=6, ph=15)]
    # DRINK: spreads its wings wide (0-2), the abdomen lantern floods as it drinks the charge of nearby rods (3-6), folds
    def sip(n):
        def fn(f, th, ab, ec):
            for k in range(n):
                a = k * 70 + 20
                p0 = polar(ab[0], ab[1], 7 + k, a)
                for t in range(3):
                    f.g.put(*P(p0[0] + (ab[0] - p0[0]) * t / 3.0, p0[1] + (ab[1] - p0[1]) * t / 3.0), "9" if t else "8")
        return fn
    drink = [M(flap=-6, ph=20, eye="squint"), M(flap=-24, ph=21, eye="wide", dy=-0.6), M(flap=-34, ph=22, eye="wide", dy=-1.0, core=1.2),
             M(flap=-30, ph=23, eye="wide", dy=-1.2, core=1.5, extra=sip(3)), M(flap=-28, ph=24, eye="wide", dy=-1.2, core=1.7, extra=sip(4)),
             M(flap=-30, ph=25, eye="wide", dy=-1.0, core=1.8, extra=sip(5)), M(flap=-12, ph=26, eye="open", core=1.4, extra=sip(2)), M(flap=0, ph=27, core=1.1)]
    death = [M(flap=-36, tilt=10, eye="wide", ph=30, core=1.6),
             dim_glow(M(flap=30, tilt=24, dy=3.0, eye="squint", glow=0, core=0.6)),
             dim_glow(grounded(M(flap=50, tilt=34, dy=5.0, eye="dead", glow=0, dead=True))),
             dim_glow(moth_corpse())]
    knock = M(flap=-30, tilt=10, dx=-0.8, eye="wide", ph=33)
    build_monster(outdir, "KrnStaticMoth", idle, run,
                  [("Darts", darts, [0.12, 0.12, 0.12, 0.06, 0.12, 0.14]),
                   ("Drink", drink, [0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.14])],
                  death, knock, idle_d=(0.14, 0.14, 0.14, 0.14), run_d=0.08, death_d=(0.1, 0.14, 0.16, 0.45), scale=5)


# ================================================================== v0.10 FX (each new monster's own effects)
def _frames(fn, n):
    return [fn(i) for i in range(n)]


def fx_staple(i):
    c = cv()
    pts = [((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))]
    rot = i % 4
    for k, (a, b) in enumerate([(-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), (2, 0), (2, 1), (-2, 0), (-2, 1)]):
        x, y = [(a, b), (-b, a), (-a, -b), (b, -a)][rot]
        c.put(x, y, "Y" if k < 5 else "O")
    for k in range(4): c.put(-4 - k, (i % 2) * (k % 2), "O" if k < 1 else "o" if k < 3 else "a")
    c.put(3, 0, "y")
    return c.spr()


def fx_hook(i):
    c = cv()
    wire_hook(c, 2, -1, 0)
    for k in range(10):
        c.put(1 - k, round(math.sin(k * 0.9 + i) * 0.6), "e" if k % 3 else "E")
    c.put(-3 - (i % 3) * 2, -1, "9"); c.put(5, 0, "6")
    return c.spr()


def fx_wire(i, snap=False):
    c = cv()
    if not snap:
        for x in range(-6, 7):
            c.put(x, round(math.sin(x * 0.7 + i) * 0.5), "e" if (x + i) % 3 else "E")
        rnd = random.Random(i)
        for k in range(2):
            x = rnd.randint(-5, 5); c.put(x, -1, "9"); c.put(x + 1, -2 if k else 1, "0" if k else "8")
    else:
        g = 1 + i * 2
        for x in range(-6, -g + 1): c.put(x, (x + g) // 3 if i else 0, "e")
        for x in range(g, 7): c.put(x, -(x - g) // 3 if i else 0, "e")
        if i < 3: spark(c, 0, 0, 2 - i // 2, "0", "9")
    return c.spr()


def fx_seeker(i):
    c = cv()
    for k in range(5):
        c.put(-3 - k, round(math.sin(i * 1.3 + k) * 1.0), "9" if k < 2 else "8" if k < 4 else "7")
    ell(c, 0, 0, 2.6, 2.0, "8990", bias=0.4)
    c.put(2, 0, "0"); c.put(1, -1, "0"); c.put(-1, -2 - (i % 2), "9")
    c.put(-2, 2, "P" if i % 2 else "p"); c.put(-4, -2, "p")
    return c.spr()


def field_frame(i, n=14):
    c = cv()
    k = 0.4 if i == 0 else 0.75 if i == 1 else (0.6 if i == n - 2 else 0.35 if i == n - 1 else 1.0)
    rx, ry = 22 * k, 8 * k
    m = 64
    for j in range(m):
        a = 2 * math.pi * j / m
        if (j + i) % 4 == 3 and k == 1.0: continue
        c.put(*P(rx * math.cos(a), ry * math.sin(a)), "9" if (j // 4 + i) % 3 else "0")
        c.put(*P(rx * 0.9 * math.cos(a), ry * 0.85 * math.sin(a)), "7", over=False)
    rnd = random.Random(30 + i)
    for j in range(int(3 * k) + 1):
        x0 = rnd.uniform(-rx * 0.7, rx * 0.7); y0 = rnd.uniform(-ry * 0.5, ry * 0.5)
        bolt(c, x0, y0, x0 + rnd.uniform(-5, 5), y0 + rnd.uniform(-3, 3), seed=i * 7 + j, jag=0.8, step=1.5, halo=None, core="9", edge="8")
    for j in range(6):
        x = rnd.uniform(-rx * 0.8, rx * 0.8); y = rnd.uniform(-ry * 0.6, ry * 0.6) - rnd.uniform(0, 4) * k
        c.put(*P(x, y), "0" if j % 2 else "9")
    return c.spr()


def fx_throw_hammer(i):
    c = cv()
    a = -i * 90 + 45
    e = polar(0, 0, 5.0, a)
    b = polar(0, 0, -6.0, a)
    line(c, b[0], b[1], e[0], e[1], "45")
    h0 = polar(e[0], e[1], -4.2, a + 90); h1 = polar(e[0], e[1], 4.2, a + 90)
    tube(c, [h0, h1], [2.6, 2.6], IRON_L, bias=0.15)
    hot = polar(e[0], e[1], 2.0, a)
    for k in range(-2, 3): c.put(*P(*polar(hot[0], hot[1], k * 1.2, a + 90)), "Y" if abs(k) < 2 else "O")
    out = outl(c.spr())
    px = dict(out.px)
    for k in range(3):   # spin blur
        q = polar(0, 0, 9.0, a + 60 + k * 18)
        px[P(*q)] = "O" if k == 0 else "o"
    return Spr(px)


def fx_over_bolt(i):
    c = cv()
    bolt(c, -8, 0, 6, 0, seed=90 + i, jag=1.2, step=2.0, core="y", edge="Y", halo="o")
    c.put(7, 0, "0"); spark(c, 6, 0, 1, "y", "Y")
    for k in range(3): c.put(-10 - k * 2, (i + k) % 3 - 1, "O" if k < 1 else "o")
    return c.spr()


def fx_over_flash(i):
    c = cv()
    h = [6, 12, 16, 10][i]
    bolt(c, 0, 0, (i % 2) * 2 - 1, -h, seed=i + 40, jag=1.0, step=2.0, core="y", edge="Y", halo="O" if i < 3 else "o")
    if i < 3: spark(c, 0, -h, 2 - i // 2, "0", "Y")
    for k in range(3 - i // 2): c.put(-3 + k * 3, -1 - (k + i) % 2, "O")
    return c.spr()


def fx_polar_ring(i):
    c = cv()
    r = [6, 14, 22, 30, 36, 40][i]
    ry = r * 0.38 + 1
    n = int(r * 6) + 8
    for k in range(n):
        a = 2 * math.pi * k / n
        if i >= 4 and (k // 3) % 3 == 0: continue
        x, y = r * math.cos(a), ry * math.sin(a)
        c.put(*P(x, y), ("O" if x > 0 else "W") if i < 4 else ("o" if x > 0 else "w"))
        c.put(*P(x * 0.9, y * 0.85), ("a" if x > 0 else "5") if i < 5 else "2", over=False)
    for k in range(5 - i // 2):
        a = k * 72 + i * 15
        x, y = r * math.cos(math.radians(a)), ry * math.sin(math.radians(a))
        spark(c, x, y, 1, "0", "9")
    return c.spr()


def fx_lode_arc(i):
    c = cv()
    for x in range(-6, 7):
        y = round(math.sin((x + 6) / 12.0 * math.pi) * -1.6 + math.sin(x + i) * 0.4)
        c.put(x, y, "O" if x < 0 else "6")
        if (x + i) % 3 == 0: c.put(x, y - 1, "9")
    c.put(-6, 0, "a"); c.put(6, 0, "5")
    return c.spr()


def fx_ind_magnet(i):
    c = cv()
    for sd in (-1, 1):
        line(c, sd * 2, 0, sd * 2, -3, "o" if sd > 0 else "5")
        c.put(sd * 2, -4, "O" if sd > 0 else "6")
    line(c, -1, 1, 1, 1, "4"); c.put(-2, 1, "3"); c.put(2, 1, "3")
    if i % 2 == 0: bolt(c, -2, -5, 2, -5, seed=i, jag=0.6, step=1.4, halo=None)
    else: c.put(0, -5, "9")
    for (x, y) in [(-4, -2), (4, -3), (-3, -6), (3, -6)][i:i + 1]: c.put(x, y, "9")
    return c.spr()


def fx_split_orb(i):
    c = cv()
    r = [3.6, 3.9, 3.7, 4.0][i]
    for y in range(-6, 7):
        for x in range(-6, 7):
            d = math.hypot(x, y) / r
            if d <= 1.0: c.put(x, y, "0" if d < 0.4 else "9" if d < 0.75 else "x")
    for k in range(3):     # the three shards showing through
        a = k * 120 + i * 30
        line(c, 0, 0, *polar(0, 0, r, a), "X")
    for k in range(12):
        a = 2 * math.pi * k / 12
        c.put(*P(5.0 * math.cos(a), 2.0 * math.sin(a)), "E" if k % 2 else "Q", over=False)
    for k in range(3): c.put(-6 - k * 2, (k + i) % 3 - 1, "x" if k < 2 else "X")
    return c.spr()


def fx_shard(i):
    c = cv()
    line(c, -3, 0, 3, 0, "x"); c.put(3, 0, "0"); c.put(2, -1, "9"); c.put(2, 1, "9")
    for k in range(3): c.put(-4 - k, (i + k) % 2, "X" if k < 2 else "F")
    return c.spr()


def fx_step(i):
    c = cv()
    w = [2, 4, 3, 1, 0][i]
    for k in range(w + 1):
        bolt(c, -w + k * 2, 0, -w + k * 2 + (k % 2), -36 + i * 3, seed=i * 5 + k, jag=1.4, step=2.0, halo="X" if i < 3 else None)
    if i < 3: spark(c, 0, -1, 2, "0", "9")
    for k in range(4):
        c.put(-4 + k * 3, -2 - ((k + i) % 3) * 4, "x" if i < 3 else "X")
    return c.spr()


def fx_step_burst(i):
    rs = [6, 13, 20, 25, 28, 29]
    c = cv()
    r = rs[i]; ry = r * 0.4 + 1
    n = int(r * 6) + 8
    for k in range(n):
        a = 2 * math.pi * k / n
        if i >= 4 and (k // 3) % 2: continue
        x, y = r * math.cos(a), ry * math.sin(a)
        c.put(*P(x, y), "0" if i < 3 else "x")
        c.put(*P(x * 0.86, y * 0.8), "x" if i < 4 else "X", over=False)
    rnd = random.Random(i + 70)
    for k in range(4 if i < 4 else 1):
        a = rnd.uniform(0, 6.28)
        bolt(c, r * 0.4 * math.cos(a), ry * 0.4 * math.sin(a), r * math.cos(a), ry * math.sin(a), seed=k + i * 9, jag=0.8, step=1.6, halo=None)
    for k in range(5):   # copper scarab sparks
        a = k * 72 + i * 20
        c.put(*P(r * 0.7 * math.cos(math.radians(a)), ry * 0.7 * math.sin(math.radians(a)) - i), "E")
    return c.spr()


def fx_whip(i):
    c = cv()
    L = [10, 26, 40, 40, 30][i]
    pts = [(0, 0)]
    for k in range(1, 12):
        x = L * k / 11.0
        pts.append((x, math.sin(k * 0.9 + i * 1.3) * (1.2 + k * 0.12) * (1 if i < 3 else 1.6)))
    for a, b in zip(pts, pts[1:]):
        for (x, y) in line_px(*P(*a), *P(*b)):
            c.put(x, y, "0" if i < 3 else "9")
            c.put(x, y + 1, "8", over=False); c.put(x, y - 1, "7", over=False)
    if i < 4: spark(c, pts[-1][0], pts[-1][1], 2 if i in (2, 3) else 1)
    for k in range(i):
        c.put(*P(L * 0.3 * k, 3 + k % 2), "e")
    return c.spr()


def fx_nova_bolt(i):
    c = cv()
    ell(c, 0, 0, 2.0, 2.0 if i % 2 == 0 else 1.2, COPPER, bias=0.3)
    c.put(0, 0, "6")
    bolt(c, -7, 0, -2, 0, seed=i + 20, jag=0.8, step=1.5, halo="7")
    c.put(3, 0, "0"); c.put(2, -1 - (i % 2), "9")
    return c.spr()


def fx_breath(i):
    c = cv()
    L = [16, 40, 60, 60, 58, 40][i]
    w = [1, 2, 3, 3, 2, 1][i]
    for x in range(0, L):
        for y in range(-w, w + 1):
            t = abs(y) / (w + 0.01)
            if (x + y * 3 + i) % 7 == 0 and t > 0.5: continue
            c.put(x, y, "0" if t < 0.35 else "9" if t < 0.75 else "8")
    rnd = random.Random(i + 11)
    for k in range(3 + i):
        x0 = rnd.uniform(4, max(5, L - 4))
        bolt(c, x0, -w, x0 + rnd.uniform(2, 6), -w - rnd.uniform(2, 4) * (1 if k % 2 else -1) - (0 if k % 2 else 2 * w),
             seed=k + i * 4, jag=0.6, step=1.5, halo=None, core="9", edge="8")
    for k in range(3): c.put(k, 0, "C")
    return c.spr()


def fx_rain(i):
    c = cv()
    if i < 4:
        y = -44 + i * 12
        bolt(c, 0, y - 6, 0, y, seed=i, jag=0.6, step=1.6, halo="7")
        spark(c, 0, y, 1)
        r = 2 + i * 1.5
        for k in range(10):
            a = 2 * math.pi * k / 10
            if (k + i) % 2: c.put(*P(r * math.cos(a), r * 0.4 * math.sin(a)), "7")
    else:
        j = i - 4
        r = [4, 7, 9, 10][j]
        for k in range(16):
            a = 2 * math.pi * k / 16
            c.put(*P(r * math.cos(a), r * 0.4 * math.sin(a)), "0" if j < 2 else "8" if j < 3 else "7")
        if j < 2:
            for k in range(5):
                a = -90 + (k - 2) * 30
                e = polar(0, 0, 3 + j * 3, a)
                line(c, 0, 0, e[0], e[1] * 0.8, "9")
        if j == 3:
            c.put(-1, 0, "2"); c.put(1, 0, "2"); c.put(0, 0, "1")
    return c.spr()


def fx_canister(i, H=14.0):
    c = cv()
    t = i / 5.0
    h = H * (1 - t) + 18.0 * t * (1 - t) * 2
    a = i * 60
    p0 = polar(0, -h, 2.6, a + 90); p1 = polar(0, -h, -2.6, a + 90)
    tube(c, [p0, p1], [1.6, 1.6], BRASS, bias=0.2)
    c.put(*P(0, -h), "9")
    fz = polar(p0[0], p0[1], 1.4, a + 90)
    c.put(*P(*fz), "Y" if i % 2 else "O")
    c.put(*P(fz[0] - 1, fz[1] - 1), "o")
    out = outl(c.spr())
    if h > 3:   # its shadow on the floor
        px = dict(out.px); px[(0, 0)] = "2"; px[(-1, 0)] = "2"; px[(1, 0)] = "2"
        out = Spr(px)
    return out


def fx_can_burst(i):
    c = cv()
    r = [4, 9, 14, 18, 20, 21][i]
    for k in range(18):
        a = 2 * math.pi * k / 18
        if i >= 4 and k % 2: continue
        c.put(*P(r * math.cos(a), r * 0.42 * math.sin(a)), "0" if i < 2 else "9" if i < 4 else "8")
    if i < 4:
        for k in range(6):
            a = -90 + (k - 2.5) * 34
            e = polar(0, -2, 4 + i * 4, a)
            bolt(c, 0, -2, e[0], min(-1, e[1]), seed=k + i * 6, jag=0.8, step=1.6, halo=None)
    rnd = random.Random(i + 3)
    for k in range(6):   # brass shrapnel
        a = rnd.uniform(-170, -10)
        e = polar(0, -1, r * 0.8, a)
        c.put(*P(e[0], e[1] * 0.7), "p" if k % 2 else "P")
    if i == 5:
        for x in range(-3, 4): c.put(x, 0, "1")
    return c.spr()


def mine_frame(arm=1.0, blink=0, land=0):
    c = cv()
    def body(cc):
        ell(cc, 0, -2.0 - land, 3.6, 2.2, IRON_HI, bias=0.2)
        for sd in (-1, 1): cc.put(sd * 4, -1 - land, "3")
        line(cc, -1, -4 - land, 1, -4 - land, "eE")
    stamp(c, body, ch="Z")
    if arm > 0:
        c.put(0, -5 - land, "0" if blink else "8")
        if blink: c.put(-1, -5 - land, "9"); c.put(1, -5 - land, "9"); c.put(0, -6 - land, "9")
    c.put(-2, -2 - land, "7" if not blink else "9"); c.put(2, -2 - land, "7" if not blink else "9")
    return c.spr()


def fx_mine_blast(i):
    c = cv()
    r = [3, 7, 11, 14, 16, 17][i]
    for k in range(16):
        a = 2 * math.pi * k / 16
        if i >= 4 and k % 2: continue
        c.put(*P(r * math.cos(a), r * 0.42 * math.sin(a)), "Y" if i < 2 else "0" if i < 4 else "8")
    if i < 4:
        h = [6, 12, 16, 12][i]
        bolt(c, 0, 0, 0, -h, seed=i, jag=1.2, step=1.8, halo="8")
        for k in range(4):
            e = polar(0, -2, 3 + i * 3, -150 + k * 40)
            c.put(*P(*e), "4" if k % 2 else "5")
    return c.spr()


def fx_relay(i):
    c = cv()
    for x in range(-8, 8):
        y1 = round(math.sin(x * 0.8 + i * 1.6) * 1.6); y2 = -y1
        c.put(x, y1, "9"); c.put(x, y2, "8" if x % 2 else "0")
    c.put(8, 0, "0"); spark(c, 8, 0, 1)
    return c.spr()


def fx_relay_flash(i):
    c = cv()
    r = [3, 6, 8, 7][i]
    for k in range(8):
        a = k * 45 + i * 10
        e = polar(0, 0, r, a)
        bolt(c, 0, 0, e[0], e[1], seed=k + i * 8, jag=0.5, step=1.5, halo=None, core="9" if i > 1 else "0", edge="8")
    if i < 3: spark(c, 0, 0, 2 - i // 2)
    return c.spr()


def pylon_frame(rise=1.0, ph=0, fire=0):
    c = cv()
    H = 16 * rise
    def body(cc):
        for k in range(int(H)):
            w = 2.0 - k * 0.06
            line(cc, -w, -k, w, -k, "eQ" if k % 2 == 0 else "Qq")
        rect(cc, -3, -2, 3, 0, "2345")
        if rise >= 1.0:
            ell(cc, 0, -H - 2, 2.6, 2.4, IRON_HI, bias=0.3)
    stamp(c, body, ch="Z")
    if rise >= 1.0:
        c.put(0, int(-H - 2), "0" if (ph + fire) % 2 == 0 else "9")
        if fire:
            crackle(c, 0, -H - 2, ph, r=4, seed=3)
        elif ph % 2:
            c.put(-2, int(-H - 4), "8"); c.put(2, int(-H - 1), "8")
    else:
        for (x, y) in ((-3, -2), (3, -1)): c.put(x, y, "9")
    return c.spr()


def fx_pylon_zap(i):
    c = cv()
    bolt(c, -5, 0, 3, 0, seed=i + 60, jag=0.8, step=1.4, halo="7", core="0", edge="E")
    c.put(4, 0, "0"); c.put(-6, (i % 2), "e")
    return c.spr()


def fx_dart(i):
    c = cv()
    pts = [(3, 0), (0, -2), (-3, 0), (0, 2)]
    poly(c, pts, "S", shade=lambda X, Y: "A" if X + Y < 0 else "s")
    c.put(0, 0, "0" if i % 2 else "9"); c.put(1, 0, "9")
    for k in range(3): c.put(-4 - k, round(math.sin(i + k) * 1.0), "S" if k < 1 else "s" if k < 2 else "m")
    return outl(c.spr())


def fx_drain(i):
    c = cv()
    rnd = random.Random(5)
    for k in range(9):
        x = rnd.uniform(-7, 7)
        y0 = rnd.uniform(-2, 4)
        y = y0 - i * 3.0 - k * 0.7
        if -24 < y < 4:
            c.put(*P(x * (1 - i * 0.12), y), "0" if (k + i) % 3 == 0 else "9")
    if i < 3:
        for k in range(8):
            a = 2 * math.pi * k / 8
            c.put(*P((6 - i * 2) * math.cos(a), (6 - i * 2) * 0.5 * math.sin(a)), "8")
    return c.spr()


FX10 = {}


def build_fx_v10(outdir, only=None):
    def want(n): return only is None or n in only
    def C(name, anims, w, h, note):
        FX10[name] = note
        if want(name): fx_center(name, anims, w, h, outdir, note)
    def G(name, anims, w, h, below, note):
        FX10[name] = note
        if want(name): fx_ground(name, anims, w, h, below, outdir, note)
    C("FxKrnStaple", [("Fly", _frames(fx_staple, 4), [0.05] * 4)], 14, 7, "Wire Gremlin Staple: a hot rivet staple, spinning; centred. Roots the hero.")
    C("FxKrnHook", [("Fly", _frames(fx_hook, 4), [0.06] * 4)], 22, 8, "Wire Gremlin Hook: iron hook with the copper wire trailing; centred.")
    C("FxKrnWire", [("Crackle", [fx_wire(i) for i in range(4)], [0.06] * 4), ("Snap", [fx_wire(i, True) for i in range(4)], [0.05, 0.05, 0.07, 0.08])],
      16, 8, "Wire Gremlin tether: one 12 px copper-wire segment (Crackle loop), tiled gremlin -> hero; Snap when it breaks.")
    C("FxKrnSeeker", [("Fly", _frames(fx_seeker, 4), [0.07] * 4)], 16, 10, "Arc Lantern Seek: a homing wisp of lantern light; centred.")
    G("FxKrnField", [("Play", [field_frame(i) for i in range(14)], [0.08, 0.08] + [0.2] * 10 + [0.1, 0.1])], 52, 22, 10,
      "Arc Lantern static field on the floor: rx 22 ry 8; damage frames 2-12 (2.0 s).")
    C("FxKrnThrowHammer", [("Spin", _frames(fx_throw_hammer, 4), [0.05] * 4)], 26, 26, "Forgemaster thrown sledge, spinning; centred.")
    C("FxKrnOverBolt", [("Fly", _frames(fx_over_bolt, 4), [0.05] * 4)], 28, 10, "Forgemaster Overload: forge-hot bolt fired by each rod; centred.")
    C("FxKrnOverFlash", [("Play", _frames(fx_over_flash, 4), [0.05, 0.05, 0.06, 0.08])], 16, 40,
      "Forgemaster Overload flare on a rod: the rod's foot is the cell centre; flare rises 16 px.")
    G("FxKrnPolarRing", [("Play", _frames(fx_polar_ring, 6), [0.05, 0.05, 0.06, 0.06, 0.07, 0.09])], 88, 38, 18,
      "Polarity Warg Polarize: red/steel field ring r 6 -> 40 (visual; the 100 px pulse is code).")
    C("FxKrnLodeArc", [("Crackle", _frames(fx_lode_arc, 4), [0.06] * 4)], 16, 8, "Polarity Warg: 12 px magnetic field-line segment, tiled hero -> Kaurn node while Magnetized.")
    C("FxKrnIndMagnet", [("Loop", _frames(fx_ind_magnet, 4), [0.1] * 4)], 14, 12, "Magnetized indicator over the hero's head (ModInd).")
    C("FxKrnSplitOrb", [("Fly", _frames(fx_split_orb, 4), [0.06] * 4)], 20, 14, "Scarab Magus Orb: splits into 3 shards after 0.4 s; centred.")
    C("FxKrnShard", [("Fly", _frames(fx_shard, 4), [0.05] * 4)], 14, 6, "Scarab Magus orb shard; centred.")
    G("FxKrnStep", [("Play", _frames(fx_step, 5), [0.05, 0.05, 0.06, 0.07, 0.08])], 20, 44, 2, "Scarab Magus Bolt Step: violet lightning column where it leaves / lands.")
    G("FxKrnStepBurst", [("Play", _frames(fx_step_burst, 6), [0.05, 0.05, 0.06, 0.07, 0.08, 0.1])], 68, 32, 14,
      "Scarab Magus landing burst: ring r 6 -> 29 (ry 0.4 r); damage frames 1-4.")
    fx_fixed("FxKrnWhip", [("Play", _frames(fx_whip, 5), [0.04, 0.04, 0.06, 0.06, 0.06])], outdir, (46, 14), (2, 7), scale=8,
             note="Voltaic Pile lash: origin = the clamp hand (cell x 2, y 7); lash runs 40 px to the right.") if want("FxKrnWhip") else None
    FX10["FxKrnWhip"] = "Voltaic Pile lash: origin = the clamp hand (cell x 2, y 7); lash runs 40 px to the right."
    FX_NOTES["FxKrnWhip"] = FX10["FxKrnWhip"]
    C("FxKrnNovaBolt", [("Fly", _frames(fx_nova_bolt, 4), [0.05] * 4)], 18, 8, "Voltaic Pile Nova: copper disc bolt, 8 in a ring; centred.")
    fx_fixed("FxKrnBreath", [("Play", _frames(fx_breath, 6), [0.04, 0.04, 0.08, 0.08, 0.08, 0.06])], outdir, (64, 16), (1, 8), scale=6,
             note="Wire Wyvern breath beam: origin = the mouth (cell x 1, y 8), beam 60 px to the right.") if want("FxKrnBreath") else None
    FX10["FxKrnBreath"] = "Wire Wyvern breath beam: origin = the mouth (cell x 1, y 8), beam 60 px to the right."
    FX_NOTES["FxKrnBreath"] = FX10["FxKrnBreath"]
    G("FxKrnRain", [("Play", _frames(fx_rain, 8), [0.06, 0.06, 0.06, 0.06, 0.05, 0.06, 0.08, 0.12])], 26, 62, 6,
      "Wire Wyvern spark rain: a spark falls (0-3), splashes (4-5: damage, r 9 x 4), scorch.")
    G("FxKrnCanister", [("Fly", _frames(fx_canister, 6), [0.1] * 6)], 16, 40, 3,
      "Fuse Sapper lobbed canister: drawn at its arc height above the floor point (14 -> 0 px over 0.6 s).")
    G("FxKrnCanBurst", [("Play", _frames(fx_can_burst, 6), [0.04, 0.05, 0.06, 0.07, 0.08, 0.12])], 48, 30, 10,
      "Fuse Sapper canister burst on the floor: r 4 -> 21; damage frames 1-3.")
    G("FxKrnMine", [("Land", [mine_frame(0, 0, 3), mine_frame(0, 0, 1), mine_frame(0, 0, 0)], [0.06, 0.06, 0.1]),
                    ("Idle", [mine_frame(1, 0), mine_frame(1, 1), mine_frame(1, 0), mine_frame(1, 0)], [0.12, 0.08, 0.2, 0.2])], 16, 16, 2,
      "Fuse Sapper static mine: Land once, loop Idle (blinks); arms after 0.9 s.")
    G("FxKrnMineBlast", [("Play", _frames(fx_mine_blast, 6), [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])], 42, 30, 11,
      "Fuse Sapper mine blast: r 3 -> 17; damage frames 1-3.")
    C("FxKrnRelay", [("Fly", _frames(fx_relay, 4), [0.05] * 4)], 20, 8, "Tesla Spire relay bolt (fired from the relay rod); centred.")
    C("FxKrnRelayFlash", [("Play", _frames(fx_relay_flash, 4), [0.04, 0.05, 0.06, 0.08])], 20, 20, "Tesla Spire: flash on the rod that relays the bolt; centred.")
    G("FxKrnPylon", [("Rise", [pylon_frame(0.3), pylon_frame(0.6), pylon_frame(1.0, 0, 1), pylon_frame(1.0, 1, 1)], [0.05, 0.05, 0.06, 0.08]),
                     ("Idle", [pylon_frame(1.0, k) for k in range(4)], [0.15, 0.1, 0.15, 0.1])], 20, 30, 2,
      "Tesla Spire pylon turret (conduction node): ball top 18 px above the ground. Rise once, loop Idle.")
    C("FxKrnPylonZap", [("Fly", _frames(fx_pylon_zap, 4), [0.05] * 4)], 14, 6, "Tesla Spire pylon zap; centred.")
    C("FxKrnDart", [("Fly", _frames(fx_dart, 4), [0.06] * 4)], 14, 8, "Static Moth weaving scale dart; centred.")
    G("FxKrnDrain", [("Play", _frames(fx_drain, 6), [0.06, 0.06, 0.07, 0.07, 0.08, 0.1])], 20, 30, 4,
      "Static Moth Drink: charge motes streaming up out of a drained rod.")
    for n, note in FX10.items(): FX_NOTES[n] = note


# ---- v0.10 registration (sheets, timing, tree board)
V10_MONSTERS = [("KrnWireGremlin", build_gremlin, "T2 (flying)"), ("KrnArcLantern", build_lantern, "T2 (flying)"),
               ("KrnForgemaster", build_forgemaster, "T3"), ("KrnWireWyvern", build_wyvern, "T3 (flying)"), ("KrnFuseSapper", build_sapper, "T3"),
               ("KrnPolarityWarg", build_warg, "T3"), ("KrnScarabMagus", build_magus, "T3"),
               ("KrnVoltaicPile", build_pile, "T3"), ("KrnTeslaSpire", build_spire, "T3 (flying)"), ("KrnStaticMoth", build_moth, "T3 (flying)")]
for _n, _fn, _t in V10_MONSTERS:
    JOBS.append((_n, _fn)); MONSTERS.append(_n); TIER[_n] = _t
FXN_V10 = ["FxKrnStaple", "FxKrnHook", "FxKrnWire", "FxKrnSeeker", "FxKrnField", "FxKrnThrowHammer", "FxKrnOverBolt", "FxKrnOverFlash",
           "FxKrnPolarRing", "FxKrnLodeArc", "FxKrnIndMagnet", "FxKrnSplitOrb", "FxKrnShard", "FxKrnStep", "FxKrnStepBurst", "FxKrnWhip",
           "FxKrnNovaBolt", "FxKrnBreath", "FxKrnRain", "FxKrnCanister", "FxKrnCanBurst", "FxKrnMine", "FxKrnMineBlast", "FxKrnRelay",
           "FxKrnRelayFlash", "FxKrnPylon", "FxKrnPylonZap", "FxKrnDart", "FxKrnDrain"]
FXN += FXN_V10
EVENTS.update({
    "KrnWireGremlin": [("Staple", "staple plucked from the spool", 1, "-"),
                       ("Staple", "RELEASE: FxKrnStaple (roots the hero; +1 static)", 3, "(10, -13)"),
                       ("Hook", "hook whirled overhead", 1, "-"),
                       ("Hook", "CAST: FxKrnHook; on the hero it starts the 3 s wire tether (FxKrnWire)", 3, "(9, -14)")],
    "KrnArcLantern": [("Seek", "pane opens", 1, "-"),
                      ("Seek", "RELEASE: FxKrnSeeker homing wisp (+1 static)", 3, "(7, -14)"),
                      ("Field", "core floods, rising", 2, "-"),
                      ("Field", "CAST: FxKrnField forms under the hero (2 s)", 4, "hero")],
    "KrnForgemaster": [("Throw", "sledge wound back", 1, "-"),
                       ("Throw", "RELEASE: FxKrnThrowHammer flies out and comes back (+1 static)", 3, "(16, -20)"),
                       ("Throw", "catches the returning sledge", 7, "-"),
                       ("Overload", "sledge raised, white-hot", 2, "-"),
                       ("Overload", "SLAM: hit box at the head, FxKrnRod planted", 3, "head (24, -1); rod (14, 0)"),
                       ("Overload", "OVERLOAD: every node within 110 px flares (FxKrnOverFlash) and fires FxKrnOverBolt", 4, "node tops")],
    "KrnWireWyvern": [("Breath", "throat lights up", 2, "-"),
                      ("Breath", "BREATH: FxKrnBreath beam from the mouth, 60 px (+1 static)", 3, "(17, -24)"),
                      ("Rain", "beats up high", 2, "-"),
                      ("Rain", "SHAKE: 6 FxKrnRain in a ring r 30 x 11 round it, 0.12 s apart", 3, "ring round the feet")],
    "KrnFuseSapper": [("Lob", "canister lit", 1, "-"),
                      ("Lob", "RELEASE: FxKrnCanister lobbed at the hero (+1 static); FxKrnCanBurst on landing", 3, "(10, 0) floor"),
                      ("Mines", "mines scooped", 1, "-"),
                      ("Mines", "SCATTER: 3 FxKrnMine (arm 0.9 s, blow within 13 px)", 4, "(16, -8) (22, 6) (6, 10) floor")],
    "KrnPolarityWarg": [("Snap", "BITE 1", 2, "jaws (24, -14)"), ("Snap", "BITE 2 (+1 static)", 4, "jaws (28, -14)"),
                        ("Polarize", "mane bristles", 1, "-"),
                        ("Polarize", "POLARIZE: FxKrnPolarRing; a hero within 100 px is Magnetized 3 s", 3, "(0, 0)")],
    "KrnScarabMagus": [("Orb", "ball lightning gathers in the sun-disc", 2, "-"),
                       ("Orb", "RELEASE: FxKrnSplitOrb (splits into 3 FxKrnShard after 0.38 s; +1 static)", 3, "(30, -17)"),
                       ("Step", "carapace open, FxKrnStep column", 2, "(0, 0)"),
                       ("Step", "BOLT STEP: teleports 22 px past the hero, FxKrnStep + FxKrnStepBurst there", 3, "hero")],
    "KrnVoltaicPile": [("Whip", "arm cocked back", 1, "-"),
                       ("Whip", "LASH: hit box x 17..57 + FxKrnWhip from the hand (+1 static)", 3, "hand (17, -16)"),
                       ("Nova", "stack lit", 2, "-"),
                       ("Nova", "NOVA: 8 FxKrnNovaBolt in a ring from 8 px up", 4, "(0, 0)")],
    "KrnTeslaSpire": [("Relay", "crown charges", 1, "-"),
                      ("Relay", "RELAY: FxKrnRelay from the node nearest the hero or the crown (+1 static)", 3, "crown (0, -32)"),
                      ("Pylon", "crown floods", 2, "-"),
                      ("Pylon", "PYLON: FxKrnPylon turret planted", 4, "(28, 0) floor")],
    "KrnStaticMoth": [("Darts", "wings swept back", 2, "-"),
                      ("Darts", "RELEASE: 2 FxKrnDart, weaving (+1 static)", 3, "(12, -20)"),
                      ("Drink", "wings spread", 2, "-"),
                      ("Drink", "DRINK: up to 4 nodes within 90 px eaten (FxKrnDrain); heal 0.6 each", 3, "nodes")],
})
V08_NOTES += [
    "## v0.10 tree (3 -> 6 -> 12, every evolution has one parent)", "",
    "- RivetImp -> AnvilSmith, WireGremlin; SparkBeetle -> LodeHound, Stormcaller; CoilWisp -> LeydenGolem, ArcLantern",
    "- AnvilSmith -> ForgeColossus, Forgemaster; WireGremlin -> WireWyvern, FuseSapper; LodeHound -> ThunderBull, PolarityWarg",
    "- Stormcaller -> StormHerald, ScarabMagus; LeydenGolem -> StormOrrery, VoltaicPile; ArcLantern -> TeslaSpire, StaticMoth", "",
    "Lineage motifs now come from the one parent only: Stormcaller lost the wisp cage on its staff; Storm Herald's magnet became",
    "the caller's copper beetle-shell crest (its iron is no longer hound rust); Storm Orrery's caller hood became the Leyden",
    "golem's iron lid and terminal posts; Forge Colossus's Leyden jar became a forge furnace grate; Thunder Bull's smith anvil",
    "became a lodestone boulder. New: bat_wing (Wire Gremlin), lantern_body / lantern_fins / coil_tail (Arc Lantern), imp_head.",
    "New palettes: brass (rRpP), verdigris (bBcC), storm violet (GFXx), moth ash (msSA).", ""]


# ==== v0.10 tree END


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    outdir = args[0] if args else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    for n, fn in JOBS:
        if only is None or n in only:
            fn(outdir)
    if only is None or only & set(FXN):
        build_fx(outdir, None if only is None else only & set(FXN))
        build_fx_v08(outdir, None if only is None else only & set(FXN))
        build_fx_v10(outdir, None if only is None else only & set(FXN))
    if only is None or only & set(ICONS):
        build_icons(outdir)
    if only is None:
        contact_sheet(outdir)
        contact_sheet(outdir, S=4, portrait=True, path=os.environ.get("KRN_CONTACT"))
        if os.environ.get("KRN_TREE"): tree_sheet(os.environ["KRN_TREE"])
        write_timing(outdir)


if __name__ == "__main__":
    main()
