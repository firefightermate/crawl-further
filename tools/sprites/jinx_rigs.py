"""JINX, THE GRINNING JESTER: "Fortune favours the fool". The first Jinx rig. Its monster and effect sheets are now
drawn by jinx_v2_rigs.py (the DeityJinx portrait too); running this file builds only the first drafts of the item
icons.

    python3 jinx_rigs.py [outdir]

A sinister carnival: crimson/black harlequin diamonds, ivory masks with too-wide grins, tarnished gold bells,
card white, sickly purple magic. Monsters are built from shaded primitives lit from the top-left and posed
by a small per-frame rig, so every frame is a fresh drawing (springs re-coil, strings re-solve, wheels spin).
The harlequin pattern is anchored to each body part, so diamonds travel with the cloth instead of swimming.

Sheets: JinxJackBox JinxCardSharp JinxDiceImp JinxRingmaster JinxMarionette JinxGrandJester,
FX: FxCard FxDie FxDieFace FxHoop FxJuggleBall FxWildCard (+Hearts/Spades/Diamonds/Clubs) FxConfetti FxWheel
FxKnifeRain, icons: IconWildCard IconLoadedDice IconJestersBell IconMarionetteCross.
"""
HERE_DIR = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Part, Canvas, line_px  # noqa: E402
from anim import Spr, SprRGB, PALETTE, pack, preview  # noqa: E402
import scalekit as SK  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_jinx")

# ------------------------------------------------------------------ palette additions (this pack only)
PALETTE.update({
    'd': (0x3e, 0x0e, 0x16),   # crimson shadow
    'D': (0x6c, 0x14, 0x1e),   # crimson
    'E': (0x96, 0x20, 0x26),   # crimson lit
    'f': (0xbe, 0x3a, 0x34),   # crimson highlight
    'z': (0xb4, 0x96, 0x46),   # tarnished gold lit
    'Z': (0xe2, 0xcc, 0x84),   # gold glint
    'L': (0xc4, 0x8a, 0xe8),   # sickly purple glow
    'Q': (0x48, 0x46, 0x32),   # goblin skin dark (sallow olive)
    'I': (0x6c, 0x6a, 0x48),   # goblin skin
    'j': (0x90, 0x8c, 0x60),   # goblin skin lit
    'H': (0x1e, 0x4c, 0x30),   # dealer visor (green celluloid) dark
    'M': (0x46, 0x9a, 0x58),   # dealer visor
})

# ------------------------------------------------------------------ material ramps (dark -> light)
CRIM = "dDEf"
BLK = "Kmms"
GOLD = "AezZ"
IVORY = "hwWX"
WOOD = "ktTh"
CARD = "wWXX"
SMOKE = "mssS"
FLAME = "oOYy"
VIOL = "qnNL"
GOB = "QQIj"
IMP = "pdDE"
WING = "Kmms"


# ------------------------------------------------------------------ primitives
def pick(ramp, l):
    n = len(ramp)
    i = int((l + 1.0) * 0.5 * n)
    return ramp[max(0, min(n - 1, i))]


def P(x, y):
    return int(round(x)), int(round(y))


def harl(ox, oy, size=4, a=CRIM, b=BLK, ang=0.0):
    """Harlequin material: diamonds of `size` px anchored at (ox, oy), optionally rotated with the part."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def f(x, y, l):
        dx, dy = x - ox, y - oy
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        k = (math.floor((u + v) / size) + math.floor((u - v) / size)) % 2
        return pick(a if k == 0 else b, l)
    return f


def stripes(ox, size=2, a=CRIM, b=BLK, ang=0.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def f(x, y, l):
        u = (x - ox) * ca + y * sa
        return pick(a if math.floor(u / size) % 2 == 0 else b, l)
    return f


def mat_ch(mat, x, y, l):
    return mat(x, y, l) if callable(mat) else pick(mat, l)


def ell(c, cx, cy, rx, ry, mat, ang=0.0, bias=0.0, vmax=None, vmin=None, over=True, flat=False):
    """Filled ellipse lit from the top-left."""
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
            l = bias if flat else 0.8 * (-(wx + wy) / 1.414) + 0.35 * (1 - d) - 0.12 + bias
            c.put(x, y, mat_ch(mat, x, y, l), over)


def tube(c, pts, radii, mat, bias=0.0, over=True):
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
                c.put(x, y, mat_ch(mat, x, y, l), over)


def line(c, x0, y0, x1, y1, ch, over=True):
    for (x, y) in line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
        c.put(x, y, ch, over)


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


def poly(c, pts, mat, bias=0.0, over=True, lit="row"):
    """Filled polygon. lit='row': lit by position across each row (left = lit); 'flat': constant bias."""
    px = poly_px(pts)
    rows = {}
    for (x, y) in px: rows.setdefault(y, []).append(x)
    y_top = min(rows) if rows else 0
    for (x, y) in px:
        if lit == "flat":
            l = bias
        else:
            xs = rows[y]; x0, x1 = min(xs), max(xs)
            t = (x - x0) / max(1, x1 - x0)
            l = 0.5 - 1.2 * t + bias + (0.15 if y < y_top + 2 else 0)
        c.put(x, y, mat_ch(mat, x, y, l), over)


def chain(x, y, segs):
    pts = [(x, y)]
    for ln, a in segs:
        x += ln * math.cos(math.radians(a)); y += ln * math.sin(math.radians(a))
        pts.append((x, y))
    return pts


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = max(1e-3, min(d, l1 + l2 - 1e-3))
    a = math.atan2(dy, dx)
    cosb = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1, min(1, cosb)))
    ea = a - bend * b
    ex, ey = sx + l1 * math.cos(ea), sy + l1 * math.sin(ea)
    hx, hy = sx + d * math.cos(a), sy + d * math.sin(a)
    return (ex, ey), (hx, hy)


def rot_spr(spr, ang, pivot=(0, 0)):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    x0, y0, x1, y1 = spr.bbox()
    R = int(math.hypot(max(abs(x0), abs(x1)) + abs(pivot[0]), max(abs(y0), abs(y1)) + abs(pivot[1]))) + 2
    out = {}
    for y in range(pivot[1] - R, pivot[1] + R + 1):
        for x in range(pivot[0] - R, pivot[0] + R + 1):
            dx, dy = x - pivot[0], y - pivot[1]
            sx = pivot[0] + dx * ca + dy * sa
            sy = pivot[1] - dx * sa + dy * ca
            v = spr.px.get((int(round(sx)), int(round(sy))))
            if v: out[(x, y)] = v
    return Spr(out)


def grounded(spr):
    b = spr.bbox()
    return Spr({(x, y - b[3]): v for (x, y), v in spr.px.items()})


def floor_cut(spr):
    return Spr({k: v for k, v in spr.px.items() if k[1] <= 0})


def merge(*sprs):
    out = {}
    for s in sprs: out.update(s.px)
    return Spr(out)


def dissolve(spr, keep, seed=1):
    r = random.Random(seed)
    return Spr({k: v for k, v in spr.px.items() if r.random() < keep})


def recol(spr, mapping):
    return Spr({k: mapping.get(v, v) for k, v in spr.px.items()})


def outline(spr, ch="K", skip=()):
    """1px dark outline around the silhouette (pixels whose colour is in `skip` don't grow one)."""
    out = dict(spr.px)
    for (x, y), v in spr.px.items():
        if v in skip: continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in spr.px: out[k] = ch
    return Spr(out)


def finish(c, overlay=None, cut=True):
    """Outline the body, then add thin overlay details (strings, sparks, whips) that must stay 1px."""
    s = outline(c.spr())
    if overlay is not None:
        o = dict(s.px); o.update(overlay.px); s = Spr(o)
    return floor_cut(s) if cut else s


def sparkle(c, x, y, r=1, ch="Z", core="y"):
    c.put(*P(x, y), core)
    for k in range(1, r + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.put(*P(x + dx, y + dy), ch if k == 1 else "e")


# ------------------------------------------------------------------ shared props
def bell(c, x, y, s=1.0, ring=0):
    """Tarnished cap bell hanging from (x, y)."""
    if s < 0.9:
        c.put(*P(x, y), "z"); c.put(*P(x, y + 1), "A"); c.put(*P(x - 1, y), "e")
        return
    ell(c, x + ring * 0.5, y + 1.3, 1.5 * s, 1.4 * s, GOLD, bias=0.1)
    c.put(*P(x + ring * 0.5, y + 2.6 * s), "K")
    c.put(*P(x - 0.6 + ring * 0.5, y + 0.6), "Z")


def spring(c, x0, y0, x1, y1, coils, amp=1.7, bob=0.0):
    """Coiled gold spring from (x0,y0) to (x1,y1): back strokes dark, front strokes lit, glints at the bends."""
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 0.5:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    n = coils * 2
    pts = []
    for i in range(n + 1):
        t = i / n
        side = 0 if i in (0, n) else (1 if i % 2 else -1)
        pts.append((x0 + ux * L * t + nx * amp * side, y0 + uy * L * t + ny * amp * side))
    for i in range(n):
        back = i % 2 == 1
        line(c, *pts[i], *pts[i + 1], "A" if back else "z", over=not back)
    for i in range(1, n, 2):
        c.put(*P(*pts[i]), "Z")


def card(c, cx, cy, w, h, face=True, ang=0.0, mat=None):
    """Small playing card (centre cx,cy). face: white with a red pip; else crimson back with a diamond."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    hw, hh = w / 2.0, h / 2.0
    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    pts = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in corners]
    poly(c, pts, mat or (CARD if face else harl(cx, cy, 2, CRIM, "dDDE")), bias=0.25)
    if face and w >= 2.5 and h >= 3:
        c.put(*P(cx, cy), "E")


GLOVE = Part("""
.dEEf.
dDEEff
dDEEEf
wdDDE.
""", (0, 2))
GLOVE_L = Part("""
.dEf
dDEf
wdD.
""", (0, 1))


def glove(c, x, y, ang=0.0, big=True):
    """Boxing glove whose cuff sits at (x, y), pointing along ang."""
    part = GLOVE if big else GLOVE_L
    if abs(ang) < 1:
        c.part(part, *P(x, y)); return
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    for (px, py), ch in part.px.items():
        c.put(*P(x + px * ca - py * sa, y + px * sa + py * ca), ch)


# ------------------------------------------------------------------ sheet helpers
BUILT = {}


# v0.8 readability: the Ringmaster and the Puppeteer were the darkest Jinx monsters (Idle luminance mean 56 / 60,
# p90 104 / 108 against vanilla ~100 / 170). Their blacks are lifted a step (the outline ring stays K) and lit edges
# (open above or to the left) a step more.
TONE_LIFT = {"K": "m", "m": "s", "s": "S", "d": "D", "D": "E", "k": "t", "q": "n"}
TONE_RIM = {"m": "S", "s": "S", "d": "E", "D": "E", "E": "f", "k": "T", "t": "T", "q": "n", "n": "N"}
TONE = {"JinxPuppeteer": 3, "JinxRingmaster": 2}   # how deep (px) the lit top-left edge reaches


def tone(spr, n=1):
    if type(spr).__name__ != "Spr": return spr
    px = spr.px
    out = {}
    for (x, y), c in px.items():
        nb = [(x + dx, y + dy) in px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        if not all(nb):
            out[(x, y)] = c                                   # silhouette ring (the outline) stays as drawn
            continue
        open_ul = any((x, y - k) not in px or (x - k, y) not in px for k in range(2, n + 1))
        if open_ul and c in TONE_RIM: out[(x, y)] = TONE_RIM[c]
        elif c == "K" and (x * 3 + y) % 4 == 0: out[(x, y)] = "K"   # keep a few deep folds
        else: out[(x, y)] = TONE_LIFT.get(c, c)
    return Spr(out)


def sheet(name, anims, outdir, scale=6, pad=2, min_w=0, min_h=0):
    if name in TONE:
        anims = [(an, [tone(f, TONE[name]) for f in fr], du) for an, fr, du in anims]
    allf = [f for a in anims for f in a[1]]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
        for i, f in enumerate(fr):
            if f.px and max(p[1] for p in f.px) > 0:
                print("WARNING %s/%s[%d] has pixels below the floor" % (name, an, i))
    x0 = min(f.bbox()[0] for f in allf if f.px); x1 = max(f.bbox()[2] for f in allf if f.px)
    y0 = min(f.bbox()[1] for f in allf if f.px)
    hw = max(-x0, x1 + 1) + pad
    cw = max(min_w, 2 * hw)
    ch = max(min_h, -y0 + 1 + pad + 2)
    feet = (cw // 2, ch - 2)
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims],
                   "img": img, "man": man}
    print("built %-18s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return img, man


def std_tail(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


def fx_sheet(name, anims, outdir, scale=8):
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


# ================================================================== JACK-IN-THE-BOX (T1)
JACK_FACE = {
    "grin": Part("""
.hWXXW.
hwXXXXW
hwKXXKX
hwXXXXX
KKXWXKK
hKKKKKw
.hwwW..
""", (3, 6)),
    "wide": Part("""
.hWXXW.
hwKXXKW
hwKXXKX
KwXXXXK
KKXWXWK
hKKEKKK
.hKKKw.
""", (3, 6)),
    "squint": Part("""
.hWXXW.
hwXXXXW
hwKKXKK
hwXXXXX
KKXWXKK
hKKKKKw
.hwwW..
""", (3, 6)),
    "dead": Part("""
.hWXXW.
hKwXKXW
hwKXXKX
hKwXKXX
hwXXXXX
hwKKKKX
.hwwwW.
""", (3, 6)),
}


def jack_head(c, x, y, face="grin", tilt=0.0, flop=0.0):
    """Jester head whose neck point is (x, y). tilt leans the cap points; flop swings them (lag)."""
    hx, hy = x, y
    # cap: two floppy points with bells, crimson (back) and black (front)
    for side, mat in ((-1, CRIM), (1, BLK)):
        root = (hx + side * 1.2, hy - 7.5)
        a0 = -90 + side * 55 + tilt + flop
        pts = chain(root[0], root[1], [(2.2, a0), (2.0, a0 + side * 45), (1.6, a0 + side * 90)])
        tube(c, pts, [1.4, 1.1, 0.7, 0.4], mat, bias=0.1)
        bell(c, pts[-1][0], pts[-1][1], s=0.8)
    ell(c, hx, hy - 7.3, 3.4, 1.4, harl(hx, hy - 6, 3), bias=0.1)
    c.part(JACK_FACE[face], *P(hx, hy))
    # ruff collar
    for k, xx in enumerate(range(-3, 4)):
        c.put(*P(hx + xx, hy + 1), "W" if k % 2 else "w")
    c.put(*P(hx - 2, hy + 2), "w"); c.put(*P(hx, hy + 2), "W"); c.put(*P(hx + 2, hy + 2), "w")


def jack_box(c, dx=0.0, dy=0.0, sq=0.0, lid=100.0, crank=0, legs=((-3, 0), (2, 0)), lean=0.0, open_=True):
    """Battered crank box. Returns the spring anchor (centre of the opening).
    sq squashes the box (px); lid is the lid angle (0 closed, 90 upright, 150 flung back); crank phase 0..3.
    The lid hinges on the box's back (left) edge so it flaps open behind the jester, clear of the spring."""
    bx0, bx1 = -5 + dx, 2 + dx              # front face x span
    bot = -4 + dy
    top = -11 + dy + sq + (1.5 if SK.small() else 0)
    D = 3                                    # depth (projected up-right)
    sh = lambda x, y: (x + lean * (bot - y) / 8.0, y)
    # legs (striped stockings) with curled jester shoes
    for i, (lx, ly) in enumerate(legs):
        hipx = dx + (-3 if i == 0 else 0)
        fx, fy = hipx + lx, ly
        for k, (x, y) in enumerate(line_px(*P(hipx, bot + 1), *P(fx, fy - 1))):
            c.put(x, y, ("D" if k % 2 else "K") if i == 0 else ("E" if k % 2 else "m"))
        c.put(*P(fx, fy), "K"); c.put(*P(fx + 1, fy), "m" if i == 0 else "s"); c.put(*P(fx + 2, fy), "D" if i == 0 else "E")
        c.put(*P(fx + 3, fy - 1), "e" if i == 0 else "z")
    # lid flung open behind (drawn first, it is behind the box)
    if open_ and lid > 20:
        h0, h1 = sh(bx0, top), sh(bx0 + D, top - D)
        a = math.radians(lid)
        W = 7.0
        vx, vy = W * math.cos(a), -W * math.sin(a) * 0.85
        lp = [h0, h1, (h1[0] + vx, h1[1] + vy), (h0[0] + vx, h0[1] + vy)]
        inner = lid > 80
        poly(c, lp, "ddDD" if inner else harl(h0[0], h0[1], 4, "EEEf", "mmms"), lit="flat", bias=0.0)
        line(c, *lp[2], *lp[3], "e")
        line(c, *lp[3], *lp[0], "A")
        c.put(*P(*lp[3]), "z")
    # side face (darker), top face, front face
    side = [sh(bx1, top), sh(bx1 + D, top - D), sh(bx1 + D, bot - D), sh(bx1, bot)]
    tiny = SK.small()
    poly(c, side, "d" if tiny else harl(bx1, top, 4, "DDDD", "KKKK"), lit="flat")
    front = [sh(bx0, top), sh(bx1, top), sh(bx1, bot), sh(bx0, bot)]
    fcx, fcy = (bx0 + bx1) / 2.0, (top + bot) / 2.0
    poly(c, front, "E" if tiny else harl(fcx - 3.5 + lean * (bot - fcy) / 8.0, fcy, 7, "EEEE", "mmmm", ang=0),
         lit="flat")
    if tiny:   # one black diamond pip in the middle of the front face
        c.put(*P(fcx + 0.5, fcy), "m")
    topf = [sh(bx0, top), sh(bx1, top), sh(bx1 + D, top - D), sh(bx0 + D, top - D)]
    if open_ and lid > 20:
        poly(c, topf, "K", lit="flat")
        line(c, *sh(bx0, top), *sh(bx1, top), "z")
        line(c, *sh(bx1, top), *sh(bx1 + D, top - D), "A")
    else:
        poly(c, topf, harl(bx0, top, 4, "ffff", "ssss"), lit="flat")
        line(c, *sh(bx0, top), *sh(bx1, top), "z")
    # tarnished gold trim on the front edges, a dented corner
    line(c, *sh(bx0, bot), *sh(bx1, bot), "A")
    if not tiny:
        line(c, *sh(bx1, bot), *sh(bx1 + D, bot - D), "A")
        line(c, *sh(bx0, top), *sh(bx0, bot), "e")
        line(c, *sh(bx1, top), *sh(bx1, bot), "A")
    c.put(*P(*sh(bx0, top)), "Z")
    c.put(*P(*sh(bx0 + 1, bot - 1)), "d")
    # crank on the right side face
    cy_ = (top + bot) / 2.0 - 1.5
    cx_, cy_ = sh(bx1 + D - 0.5, cy_)
    line(c, cx_, cy_, cx_ + 2, cy_, "A")
    arm = [(0, -2), (1, -1), (0, 2), (-1, 1)][crank % 4]
    kx, ky = cx_ + 2 + arm[0], cy_ + arm[1]
    line(c, cx_ + 2, cy_, kx, ky, "e")
    c.put(*P(kx, ky), "Z"); c.put(*P(kx + 1, ky), "z")
    ox, oy = sh(dx - 1.5 + D / 2.0 + 1, top - D / 2.0)
    return ox, oy


def jack(dx=0.0, dy=0.0, sq=0.0, lid=105.0, crank=0, legs=((-1, 0), (1, 0)), lean=0.0, head=(1.0, -6.0),
         face="grin", coils=3, flop=0.0, tilt=0.0, glove_at=None, glove_ang=0.0, head_on=True, open_=True,
         extra=None, extra_back=None, over=None):
    """head: (dx, dy) of the neck relative to the spring anchor (the spring stretches to it)."""
    c = Canvas()
    if extra_back: extra_back(c)
    ax, ay = jack_box(c, dx, dy, sq, lid, crank, legs, lean, open_)
    if head_on:
        if SK.small():   # small render: the head rides lower on its spring (keeps T1 height)
            head = (head[0], min(-1.5, head[1] + 2.5))
        nx, ny = ax + head[0], ay + head[1]
        spring(c, ax, ay + 1, nx, ny + 2, coils, amp=1.6)
        if glove_at is not None:
            gx, gy = nx + glove_at[0], ny + glove_at[1]
            line(c, nx + 1, ny + 2, gx, gy, "e")
            glove(c, gx, gy, glove_ang)
        jack_head(c, nx, ny, face, tilt=tilt, flop=flop)
    if extra: extra(c)
    return finish(c, over)


def speed_lines(c, x0, x1, ys, ch="w"):
    for y in ys:
        line(c, x0, y, x1, y, ch, over=False)


def build_jackbox(outdir, name="JinxJackBox"):
    J = jack
    # Idle: the head bobs on its spring while the crank ticks round
    idle = [J(head=(0.5, -6), crank=0, flop=0),
            J(head=(0.5, -5), crank=1, flop=8, face="grin", dy=0),
            J(head=(1.0, -4.5), crank=2, flop=14, sq=0.5, face="squint"),
            J(head=(1.0, -6.5), crank=3, flop=-6)]
    run_legs = [((-3, 0), (2, 0)), ((-2, -1), (1, 0)), ((0, -1), (-1, 0)), ((2, 0), (-3, 0)), ((1, 0), (-2, -1)),
                ((-1, 0), (0, -1))]
    run = [J(legs=run_legs[i], dy=(-1 if i in (1, 4) else 0), lean=[1, 2, 1, 1, 2, 1][i],
             head=(-1.5 - (i % 3) * 0.5, -5.5 + (0.5 if i in (1, 4) else 0)), crank=i % 4,
             flop=[-20, -30, -10, -20, -30, -10][i], tilt=-10, face="grin") for i in range(6)]
    # Punch: duck down (2 wind-up), SPRING OUT with the glove (hit 3), wobble back
    punch = [J(head=(0, -3.5), sq=1, face="squint", coils=3, flop=10, legs=((-2, 0), (2, 0))),
             J(head=(-1, -2), sq=1.5, dy=0, face="squint", coils=3, flop=18, lean=-1, legs=((-3, 0), (2, 0)),
               glove_at=(2, 1), glove_ang=-20),
             J(head=(7, -6), face="wide", coils=3, flop=-30, lean=1, glove_at=(3, 1), glove_ang=-10,
               legs=((-3, 0), (3, 0))),
             J(head=(15, -5), face="wide", coils=4, flop=-60, lean=2, glove_at=(4, 2), glove_ang=0,
               legs=((-3, 0), (3, 0)),
               extra_back=lambda c: speed_lines(c, 0, 12, (-15, -12, -9), "s")),
             J(head=(12, -7), face="grin", coils=4, flop=-20, lean=1, glove_at=(3, 2), glove_ang=15,
               legs=((-3, 0), (3, 0))),
             J(head=(5, -8), face="grin", coils=3, flop=20, glove_at=(2, 2), glove_ang=30, legs=((-2, 0), (2, 0))),
             J(head=(0, -6), face="grin", coils=3, flop=-6)]
    # Pop: duck in (1-3 closing), lid SHUT (4, invulnerable / teleport), burst out somewhere new (5-8)
    def confetti(seed, n, r):
        def f(c):
            rr = random.Random(seed)
            for k in range(n):
                a = rr.uniform(-math.pi, 0); d = rr.uniform(0.5, 1.0) * r
                c.put(*P(1 + d * math.cos(a), -14 + d * math.sin(a) * 0.8), "fZLXE"[k % 5])
        return f
    pop = [J(head=(0, -7.5), face="wide", flop=-10, coils=3, legs=((-2, 0), (2, 0))),
           J(head=(0, -3), face="squint", flop=25, coils=3, lid=95, sq=0.5),
           J(head=(0, -0.5), face="squint", flop=40, coils=2, lid=60, sq=1),
           J(head_on=False, lid=25, sq=1.5, legs=((-2, 0), (2, 0)),
             extra=lambda c: [c.put(1, -13, "z"), c.put(2, -14, "z")]),
           J(head_on=False, open_=False, sq=1, legs=((-2, 0), (2, 0)), crank=2),
           J(head=(0, -11), face="wide", flop=-40, coils=4, lid=130, sq=-1, dy=-1, legs=((-2, -1), (2, -1)),
             extra=confetti(3, 10, 8)),
           J(head=(1, -8.5), face="wide", flop=30, coils=4, lid=115, legs=((-2, 0), (2, 0)), extra=confetti(4, 8, 10)),
           J(head=(0.5, -5), face="grin", flop=-15, coils=3, lid=100, sq=0.5, extra=confetti(5, 4, 11)),
           J(head=(0.5, -6), face="grin", flop=5, coils=3)]
    # Death: head boings out, spring snaps, box tips over
    d0 = J(head=(-3, -9), face="dead", flop=-50, coils=4, lid=130, lean=-1)
    d1 = grounded(rot_spr(J(head=(-6, -4), face="dead", flop=-70, coils=3, lid=140, legs=((-2, -1), (1, -2))),
                          -35, (0, -1)))
    # v0.8: a fourth death frame: the box keeps tipping and the head slaps the floor
    d2 = grounded(rot_spr(J(head=(-6, -2), face="dead", flop=-85, coils=2, lid=150, legs=((-2, -1), (1, -2))),
                          -65, (0, -1)))
    corpse = jack_corpse()
    death = [d0, d1, d2, corpse]
    knock = J(head=(-5, -5), face="squint", flop=-50, coils=3, lean=-2, legs=((-1, -1), (3, 0)), lid=125)
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.08] * 6),
             ("Punch", punch, [0.14, 0.12, 0.05, 0.08, 0.1, 0.12, 0.14]),
             ("PunchUp", punch_up, [0.14, 0.12, 0.05, 0.08, 0.1, 0.12, 0.14]),
             ("PunchDown", punch_down, [0.14, 0.12, 0.05, 0.08, 0.1, 0.12, 0.14]),
             ("Pop", pop, [0.1, 0.08, 0.07, 0.07, 0.3, 0.06, 0.1, 0.1, 0.14])]
    anims += std_tail(idle[0], death, [0.12, 0.12, 0.12, 0.4], knock)
    return sheet(name, anims, outdir, scale=6)


def jack_corpse():
    """Box on its side, lid hanging open, the spring sprawled out with the head face-down on the floor."""
    c = Canvas()
    box = jack_box(Canvas(), lid=140)
    b = Canvas()
    jack_box(b, lid=140, legs=((-1, 0), (1, 0)))
    lying = grounded(rot_spr(b.spr(), -90, SK.spt(0, -1)))
    SK.paste(c, lying, -4, 0)
    spring(c, 0, -5, 7, -2, 3, amp=1.4)
    c2 = Canvas()
    jack_head(c2, 0, 0, "dead", tilt=0, flop=-30)
    head = grounded(rot_spr(c2.spr(), 70, SK.spt(0, -3)))
    SK.paste(c, head, 10, 0)
    return finish(c)


# ================================================================== v0.10: JACK-IN-THE-BOX + LOOSE JACK at final size
# The v0.7 size pass shrank the Jack to 0.55 (and the minion to 0.42) of a 30 px design: the box vanished and the
# jester turned into noise. Both are redrawn here pixel by pixel at their final size (no ArtScale entry), with the
# box, its crank and lid, the gold spring and a 5 px jester face all readable at 1x.
#   JinxJackBox: a crimson crank box on stubby striped legs, gold harlequin diamond on the front, a crank on the
#                right side, the lid flapped back; a jester head on a gold spring pops out of it.
#   JinxJackMinion ("Loose Jack"): what got out: a bare spring with the jester head on top, hopping about on the
#                splintered lid board stuck to its foot. No box.
JF = {   # 5 x 5 jester faces, neck point = bottom centre (2, 4)
    "grin": Part(""".hXX.
hKXKX
hXEXX
KXKXK
.KKK.""", (2, 4)),
    "wide": Part(""".hXX.
KKXKK
hXEXX
KKKKK
.KEK.""", (2, 4)),
    "squint": Part(""".hXX.
hKKKX
hXEXX
KXKXK
.KKK.""", (2, 4)),
    "dead": Part(""".hXX.
hKwKX
hXXXX
hwKKX
.hww.""", (2, 4)),
}


def jface(c, x, y, face="grin", flop=0):
    """5 px jester head, neck point (x, y): two-point cap (crimson / black) with gold bells, a ruff below."""
    x, y = int(round(x)), int(round(y))
    f = int(round(flop))
    c.raw.put(x - 2, y - 5, "D"); c.raw.put(x - 1, y - 5, "E"); c.raw.put(x, y - 5, "m"); c.raw.put(x + 1, y - 5, "K"); c.raw.put(x + 2, y - 5, "m")
    c.raw.put(x - 3, y - 6 + (1 if f > 0 else 0), "E"); c.raw.put(x - 4 + min(0, f), y - 6 + (1 if f > 0 else 0), "z")   # crimson point + bell
    c.raw.put(x + 3, y - 6 + (1 if f < 0 else 0), "m"); c.raw.put(x + 4 + max(0, f), y - 6 + (1 if f < 0 else 0), "z")  # black point + bell
    c.part(JF[face], x, y)
    for k in (-2, -1, 0, 1, 2):
        c.raw.put(x + k, y + 1, "W" if k % 2 else "w")      # ruff


def jbox(c, dx=0, dy=0, sq=0, lid="open", crank=0, legs=((-3, 0), (1, 0)), lean=0):
    """The crank box: front face x -5..2, from y -1 up to `top`; 2 px side face to the right; lid hinged at the back.
    Returns the opening's centre (spring anchor)."""
    bot = -1 + dy
    top = -5 + dy + sq
    for (lx, ly) in legs:                       # stubby striped legs and curled shoes
        c.raw.put(lx + dx, bot + 1 + ly, "m"); c.raw.put(lx + dx + 1, bot + 1 + ly, "D")
    for y in range(top, bot + 1):
        sx = int(round(lean * (bot - y) / 6.0))
        for x in range(-5, 3):
            l = 0.6 - 0.35 * (x + 5) / 7.0 - 0.3 * (y - top) / max(1, bot - top)
            ch = "f" if l > 0.45 else "E" if l > 0.05 else "D"
            c.raw.put(x + dx + sx, y, ch)
        c.raw.put(3 + dx + sx, y - 1, "d"); c.raw.put(4 + dx + sx, y - 1, "d")       # side face
        c.raw.put(-5 + dx + sx, y, "e")                                               # gold edge
    st = int(round(lean * (bot - top) / 6.0))
    for x in range(-5, 3): c.raw.put(x + dx + st, top, "z")                           # top trim
    c.raw.put(3 + dx + st, top - 1, "z"); c.raw.put(4 + dx + st, top - 2, "A")
    for x in range(-5, 3): c.raw.put(x + dx, bot, "A")                                # bottom trim
    my = (top + bot) // 2
    for (ox, oy, ch) in ((-2, -1, "Z"), (-3, 0, "z"), (-1, 0, "z"), (-2, 1, "z"), (-2, 0, "y")):   # harlequin diamond
        c.raw.put(ox + dx + int(round(lean * (bot - my) / 6.0)), my + oy, ch)
    # crank on the side face: hub + turning handle
    hx, hy = 4 + dx + int(round(lean * (bot - my) / 6.0)), my - 1
    c.raw.put(hx + 1, hy, "A")
    ox, oy = [(1, -2), (2, -1), (1, 1), (0, -1)][crank % 4]
    c.raw.put(hx + 1 + ox, hy + oy, "Z"); c.raw.put(hx + 1 + (ox + 1) // 2, hy + oy // 2, "z")
    # lid: open = a plank flapped back behind the box, shut = flat on top
    if lid == "open":
        for k in range(5): c.raw.put(-6 - k // 2 + dx + st, top - 1 - k, "D" if k % 2 else "E")
        c.raw.put(-6 + dx + st, top - 1, "z")
        for x in range(-4, 3): c.raw.put(x + dx + st, top - 1, "K")                    # the dark opening
    elif lid == "half":
        for k in range(6): c.raw.put(-5 + k + dx + st, top - 1 - (5 - k) // 2, "E")
    else:
        for x in range(-5, 3): c.raw.put(x + dx + st, top - 1, "E" if x > -5 else "D")
        c.raw.put(4 + dx + st, top - 3, "D")
    return (-1 + dx + st, top - 1)


def jack_v9(dx=0, dy=0, sq=0, lid="open", crank=0, legs=((-3, 0), (1, 0)), lean=0, spring_len=2, head_dx=0,
            face="grin", flop=0, head=True, coils=2, extra=None, punch=None, aim="side"):
    c = Canvas()
    ax, ay = jbox(c, dx, dy, sq, lid, crank, legs, lean)
    if head and punch is None:
        hx, hy = ax + head_dx, ay - 1 - spring_len
        if spring_len > 0:
            spring(c, ax, ay - 1, hx, hy + 1, coils, amp=1.0)
        jface(c, hx, hy, face, flop)
    if punch is not None and aim in ("up", "down"):
        # v0.10 sweep: aimed punches (AttackData.m_animAngles). The same spring + head + glove as the side punch,
        # drawn pointing right on its own canvas and turned a quarter (exact 90 degree pixel turn) to point up / down
        seg = Canvas()
        spring(seg, 0, 0, punch - 2, 0, max(2, punch // 3), amp=1.0)
        jface(seg, punch - 2, 1, face, flop)
        for (ox, oy, ch) in ((0, -1, "f"), (1, -1, "f"), (0, 0, "E"), (1, 0, "E"), (2, 0, "f"), (0, 1, "D"), (1, 1, "E"), (-1, 0, "w")):
            seg.raw.put(int(punch) + 1 + ox, -2 + oy, ch)
        turned = rot_spr(Spr(dict(seg.spr().px)), -90 if aim == "up" else 90, (0, 0))
        if aim == "up":
            SK.paste(c, turned, ax, ay - 1)
        else:
            # down the screen: the spring arcs over the box's front corner and the head slams the floor beside it
            sx = 6 + dx
            spring(c, ax, ay - 1, sx, ay - 2, 1, amp=1.0)
            SK.paste(c, turned, sx, ay - 2)
    elif punch is not None:
        # the spring shoots out forward with the head in a boxing glove: punch = reach in px from the opening
        tx, ty = ax + punch, ay - 3
        spring(c, ax, ay - 1, tx - 2, ty, max(2, punch // 3), amp=1.0)
        jface(c, tx - 2, ty + 1, face, flop)
        for (ox, oy, ch) in ((0, -1, "f"), (1, -1, "f"), (0, 0, "E"), (1, 0, "E"), (2, 0, "f"), (0, 1, "D"), (1, 1, "E"), (-1, 0, "w")):
            c.raw.put(int(tx) + 1 + ox, int(ty) - 2 + oy, ch)                       # the glove on its nose
    if extra: extra(c)
    return finish(c)


def confetti_px(c, cx, cy, n, r, seed):
    rr = random.Random(seed)
    for k in range(n):
        a = rr.uniform(-math.pi, 0); d = rr.uniform(0.4, 1.0) * r
        c.raw.put(int(round(cx + d * math.cos(a))), int(round(cy + d * math.sin(a) * 0.8)), "fZLXE"[k % 5])


def build_jack_v9(outdir):
    J = jack_v9
    idle = [J(spring_len=1, crank=0, flop=0), J(spring_len=1, crank=1, flop=-1, face="grin", lean=1),
            J(spring_len=1, crank=2, flop=1, face="squint"), J(spring_len=0, crank=3, flop=0, sq=1)]
    hop = [(0, 0), (-1, 0), (-2, -1), (-2, 1), (-1, 0), (0, 0)]
    run = [J(dy=hop[i][0], sq=[1, 0, -1, 0, 0, 1][i], crank=i % 4, spring_len=[1, 2, 3, 2, 2, 1][i], flop=hop[i][1] * 2,
             legs=[((-3, 0), (1, 0)), ((-4, 0), (2, -1)), ((-3, -1), (1, -1)), ((-2, 0), (0, -1)), ((-3, 0), (2, 0)), ((-3, 0), (1, 0))][i],
             lean=[0, 1, 1, 0, -1, 0][i]) for i in range(6)]
    # Punch: duck in (0-1), the spring shoots out (2), GLOVE lands (3, reach 14), hold (4), snap back (5-6)
    punch = [J(spring_len=0, face="squint", sq=1, lean=-1), J(spring_len=0, head=False, sq=1, lean=-1),
             J(punch=8, face="wide", lean=1), J(punch=14, face="wide", lean=1, extra=lambda c: speed_lines(c, -2, 4, (-9, -7), "w")),
             J(punch=13, face="grin", lean=1), J(punch=6, face="grin"), J(spring_len=3, face="grin", flop=2)]
    # v0.10 sweep: PunchUp / PunchDown (same frames, timings and hit frame 3) played when the jack aims up or down
    def vlines(xs, y0, y1):
        return lambda c: [line(c.raw, x, y0, x, y1, "w", over=False) for x in xs]
    punch_up = [J(spring_len=0, face="squint", sq=1), J(spring_len=0, head=False, sq=1),
                J(punch=8, aim="up", face="wide"), J(punch=14, aim="up", face="wide", extra=vlines((-5, 3), -9, -11)),
                J(punch=13, aim="up", face="grin"), J(punch=6, aim="up", face="grin"), J(spring_len=3, face="grin", flop=2)]
    # down: the box rears back (up the screen) and the glove slams the floor in front of it
    punch_down = [J(spring_len=0, face="squint", sq=1), J(spring_len=0, head=False, sq=1, lean=1),
                  J(punch=3, aim="down", face="wide", lean=1), J(punch=5, aim="down", face="wide", lean=1,
                  extra=lambda c: [c.raw.put(x, 0, "w") for x in (5, 13)] + [c.raw.put(x, -1, "w") for x in (4, 14)]),
                  J(punch=5, aim="down", face="grin", lean=1), J(punch=2, aim="down", face="grin"), J(spring_len=3, face="grin", flop=2)]
    # Pop: crank wound (0), ducks (1), head in (2), lid swings (3), SHUT - teleport (4), bursts open at the new spot (5),
    # overshoot (6), settle (7-8)
    pop = [J(crank=1, spring_len=2, face="wide"), J(spring_len=0, face="squint", crank=2),
           J(head=False, lid="open", crank=3), J(head=False, lid="half", sq=1), J(head=False, lid="shut", sq=1, crank=0),
           J(spring_len=5, face="wide", flop=-2, coils=3, sq=-1, extra=lambda c: confetti_px(c, -1, -10, 10, 8, 3)),
           J(spring_len=4, face="wide", flop=2, coils=3, extra=lambda c: confetti_px(c, 0, -9, 8, 10, 4)),
           J(spring_len=2, face="grin", flop=-1, extra=lambda c: confetti_px(c, 0, -8, 4, 11, 5)),
           J(spring_len=2, face="grin")]
    # Death: the head boings off (0), the box tips (1-2), corpse (3)
    d0 = J(spring_len=4, head_dx=-3, face="dead", flop=-2, coils=3, lean=-1)
    d1 = grounded(rot_spr(J(spring_len=3, head_dx=-2, face="dead", flop=-2), -30, (0, -1)))
    d2 = grounded(rot_spr(J(spring_len=1, head=False, lid="open"), -70, (0, -1)))
    corpse = jack_v9_corpse()
    knock = J(spring_len=2, head_dx=-2, face="squint", flop=-2, lean=-1, legs=((-2, 0), (2, -1)))
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.08] * 6),
             ("Punch", punch, [0.14, 0.12, 0.05, 0.08, 0.1, 0.12, 0.14]),
             ("PunchUp", punch_up, [0.14, 0.12, 0.05, 0.08, 0.1, 0.12, 0.14]),
             ("PunchDown", punch_down, [0.14, 0.12, 0.05, 0.08, 0.1, 0.12, 0.14]),
             ("Pop", pop, [0.1, 0.08, 0.07, 0.07, 0.3, 0.06, 0.1, 0.1, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.12, 0.12, 0.12, 0.4], knock)
    return sheet("JinxJackBox", anims, outdir, scale=8)


def jack_v9_corpse():
    c = Canvas()
    b = Canvas()
    jbox(b, lid="open")
    lying = grounded(rot_spr(finish(b), -90, (0, -1)))
    SK.paste(c, lying, -3, 0)
    spring(c, 1, -2, 6, -1, 2, amp=1.0)
    jface(c, 9, -1, "dead", 0)
    return grounded(floor_cut(merge(Spr(c.px), finish(c))))


def loose_jack(dy=0, spring_h=5, lean=0, face="grin", flop=0, board_tilt=0, coils=3, head_dx=0, extra=None, board=True):
    """The Loose Jack: a bare gold spring standing on a splintered lid board, the jester head on top."""
    c = Canvas()
    by = -1 + dy
    if board:
        for x in range(-3, 3):                       # the broken lid board, splinters at the right end
            yy = by + (int(round(board_tilt * x / 3.0)))
            c.raw.put(x, yy, "E" if x > -3 else "D"); c.raw.put(x, yy + 1, "D")
        c.raw.put(3, by - 1 + int(round(board_tilt)), "e"); c.raw.put(3, by + 1 + int(round(board_tilt)), "t")
        c.raw.put(-2, by, "z")                      # a hinge still on it
    top = (lean + head_dx, by - 1 - spring_h)
    spring(c, 0, by - 1, top[0], top[1], coils, amp=1.0)
    jface(c, top[0], top[1] - 1, face, flop)
    if extra: extra(c)
    return finish(c)


def build_loose_jack(outdir):
    L = loose_jack
    idle = [L(spring_h=5), L(spring_h=4, flop=-1, face="squint"), L(spring_h=5, flop=1), L(spring_h=4, flop=0, lean=1)]
    run = [L(dy=[0, -2, -4, -3, -1, 0][i], spring_h=[3, 6, 7, 6, 5, 3][i], lean=[0, 1, 1, 0, 0, 0][i],
             flop=[1, 0, -1, -1, 0, 1][i], board_tilt=[0, 1, 1, 0, -1, 0][i]) for i in range(6)]
    # Punch (headbutt): coil down (0-1), whip forward (2), HEAD lands (3, head at (7, -6)), hold (4), back (5-6)
    punch = [L(spring_h=3, face="squint"), L(spring_h=2, face="squint", lean=-1),
             L(spring_h=5, lean=3, face="wide", coils=2), L(spring_h=4, lean=6, head_dx=1, face="wide", coils=2,
             extra=lambda c: speed_lines(c, -2, 2, (-8, -6), "w")),
             L(spring_h=4, lean=5, face="grin", coils=2), L(spring_h=5, lean=2, face="grin"), L(spring_h=5, flop=1)]
    # v0.10 sweep: aimed headbutts for AttackData.m_animAngles (same frame count, timings and hit frame 3).
    # Up: the spring shoots straight up and the head butts the air above. Down: the jack topples forward and the
    # head bonks the floor in front of its board.
    punch_up = [L(spring_h=3, face="squint"), L(spring_h=2, face="squint"),
                L(spring_h=8, face="wide", coils=3), L(spring_h=11, face="wide", coils=4, flop=-1,
                extra=lambda c: [line(c.raw, x, -9, x, -12, "w", over=False) for x in (-4, 4)]),
                L(spring_h=10, face="grin", coils=4), L(spring_h=7, face="grin", coils=3), L(spring_h=5, flop=1)]
    def tip(a, face, extra=None):
        s_ = grounded(rot_spr(L(spring_h=5, face=face, coils=2, board=False), a, (0, -1)))
        b = Canvas()
        for x in range(-3, 3):
            b.raw.put(x, -1, "E" if x > -3 else "D"); b.raw.put(x, 0, "D")
        b.raw.put(3, -2, "e"); b.raw.put(-2, -1, "z")
        if extra: extra(b)
        return merge(finish(b), s_)
    punch_down = [L(spring_h=3, face="squint"), L(spring_h=2, face="squint", lean=1),
                  tip(45, "wide"), tip(80, "wide", lambda c: [c.raw.put(x, 0, "w") for x in (6, 13)]),
                  tip(75, "grin"), tip(35, "grin"), L(spring_h=5, flop=1)]
    d0 = L(spring_h=7, face="dead", flop=-2, lean=-1)
    d1 = grounded(rot_spr(L(spring_h=5, face="dead", flop=-1), -40, (0, -1)))
    d2 = grounded(rot_spr(L(spring_h=3, face="dead"), -80, (0, -1)))
    cc = Canvas()
    for x in range(-6, 0): cc.raw.put(x, 0, "E" if x > -6 else "D")
    spring(cc, 0, -1, 6, -1, 2, amp=1.0)
    jface(cc, 9, -1, "dead")
    corpse = grounded(floor_cut(finish(cc)))
    knock = L(spring_h=4, lean=-2, face="squint", flop=-2, board_tilt=-1)
    anims = [("Idle", idle, [0.18, 0.14, 0.18, 0.14]), ("Run", run, [0.07] * 6),
             ("Punch", punch, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.12]),
             ("PunchUp", punch_up, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.12]),
             ("PunchDown", punch_down, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.12])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("JinxJackMinion", anims, outdir, scale=8)


# ================================================================== shared: dice cube + transforms
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
# face normal -> value (front 1, back 6, right 3, left 4, top 2, bottom 5)
CUBE_FACES = [((0, 0, -1), 1), ((0, 0, 1), 6), ((1, 0, 0), 3), ((-1, 0, 0), 4), ((0, -1, 0), 2), ((0, 1, 0), 5)]


def rot3(v, rx, ry, rz):
    x, y, z = v
    for ax, a in (("y", ry), ("x", rx), ("z", rz)):
        a = math.radians(a); ca, sa = math.cos(a), math.sin(a)
        if ax == "x": y, z = y * ca - z * sa, y * sa + z * ca
        elif ax == "y": x, z = x * ca + z * sa, -x * sa + z * ca
        else: x, y = x * ca - y * sa, x * sa + y * ca
    return x, y, z


CAM_TILT = 28.0


def die(c, cx, cy, size, rx=0.0, ry=35.0, rz=0.0, ramp=IVORY, pip="K", big_pips=False, glow=None):
    """Ivory die, edge length `size` px, centred at (cx, cy). (rx, ry, rz) is the die's own tumble; a fixed
    camera tilt then shows its top face. Faces are drawn darkest first, each rimmed one shade darker on its
    lower/right edges, so a tumbling cube keeps reading as a cube."""
    h = size / 2.0
    L = (-0.5, -0.58, -0.64)
    xf = lambda v: rot3(rot3(v, rx, ry, rz), CAM_TILT, 0, 0)
    faces = []
    for n, val in CUBE_FACES:
        nn = xf(n)
        if nn[2] >= -0.05: continue
        if n[0]: e1, e2 = (0, 0, 1), (0, 1, 0)
        elif n[1]: e1, e2 = (1, 0, 0), (0, 0, 1)
        else: e1, e2 = (1, 0, 0), (0, 1, 0)
        pts = []
        for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            w = xf(tuple(h * (n[k] + su * e1[k] + sv * e2[k]) for k in range(3)))
            pts.append((cx + w[0], cy + w[1]))
        lam = nn[0] * L[0] + nn[1] * L[1] + nn[2] * L[2]
        faces.append((lam, pts, lam * 2.0 - 0.25, val, n, e1, e2, nn))
    faces.sort(key=lambda f: f[0])
    for lam, pts, l, val, n, e1, e2, nn in faces:
        poly(c, pts, ramp, bias=l, lit="flat")
        if size >= 5:
            ei = max(0, ramp.index(pick(ramp, l)) - 1)
            cxp = sum(p[0] for p in pts) / 4.0; cyp = sum(p[1] for p in pts) / 4.0
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                if (a_[0] + b_[0]) / 2 - cxp + (a_[1] + b_[1]) / 2 - cyp > 0.3:
                    line(c, *a_, *b_, ramp[ei])
    for lam, pts, l, val, n, e1, e2, nn in faces:
        if abs(nn[2]) * size < 2.2: continue
        k = 0.5 if size >= 7 else 0.45
        for (pu, pv) in PIPS[val]:
            w = xf(tuple(h * (n[j] + k * (pu * e1[j] + pv * e2[j])) for j in range(3)))
            ch = glow if (glow and val in (1, 6)) else pip
            c.put(*P(cx + w[0], cy + w[1]), ch)
            if big_pips:
                for ox, oy in ((1, 0), (0, 1), (1, 1)):
                    c.put(*P(cx + w[0] + ox, cy + w[1] + oy), ch)


def Xf(ang, pivot):
    """Rotate points about pivot (deg, + = clockwise on screen, i.e. leaning forward/right)."""
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)

    def f(x, y):
        dx, dy = x - pivot[0], y - pivot[1]
        return pivot[0] + dx * ca - dy * sa, pivot[1] + dx * sa + dy * ca
    return f


def fan(c, x, y, ang, n=4, spread=26, ln=3.0, back=False):
    """Fan of playing cards held at (x, y) pointing along ang: one thin card per ray, red pips on the tips."""
    for i in range(n):
        a = ang + (i - (n - 1) / 2.0) * spread
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        tip = (x + ux * ln, y + uy * ln)
        line(c, x + ux, y + uy, *tip, ("D" if i % 2 else "E") if back else ("X" if i % 2 == 0 else "W"))
        if not back:
            c.put(*P(*tip), "E" if i % 2 == 0 else "K")


def rect_card(c, cx, cy, ang=0.0, w=2.0, h=3.0, face=True):
    card(c, cx, cy, w, h, face=face, ang=ang)


# ================================================================== CARD SHARP (T1)
SHARP_HEAD = {
    "grin": Part("""
....HMMMMM..
Q..HHHHHHHM.
.QIjjjjjjI..
..QjjjKYjjj.
..QIjjjjjjjI
..QKXKXKXKK.
...QKKKKKI..
....QIIIQ...
""", (5, 7)),
    "leer": Part("""
....HMMMMM..
Q..HHHHHHHM.
.QIjjjjjjI..
..QjjKKYjjj.
..QIjjjjjjjI
..KXKXKXKXK.
...KKKKKKI..
....QIIIQ...
""", (5, 7)),
    "bow": Part("""
....HMMMMM..
Q..HHHHHHHHM
.QIjjjjjjI..
..QjjKKKjjj.
..QIjjjjjjjI
..QIKKKKKKK.
...QIIIIII..
....QIIIQ...
""", (5, 7)),
    "dead": Part("""
....HMMMMM..
Q..HHHHHHHM.
.QIjjjjjjI..
..QjjKjKjjj.
..QIjjKjjjjI
..QIjKKKKK..
...QIIIIIi..
....QIIIQ...
""", (5, 7)),
}


def card_sharp(dx=0.0, dy=0.0, lean=20.0, feet=(-2, 2), head="grin", hd=(0, 0), fh=(5, -8), bh=(-3, -7),
               fan_f=(-40, 4), fan_b=(-140, 4), extra=None, extra_back=None, back_cards=True, over=None,
               knee=(1, 1)):
    """Hunched goblin dealer. lean: torso forward lean (deg); fh/bh: front/back hand targets;
    fan_f/fan_b: (angle, n cards) of the fans in each hand (n=0 for empty hand)."""
    c = Canvas()
    if extra_back: extra_back(c)
    hip = (dx, -5 + dy)
    T = Xf(lean, hip)
    # back leg
    for i, fx in enumerate(feet):
        if i == 1: continue
        (kx, ky), (ax, ay) = ik(hip[0] - 1, hip[1], dx + fx, -1, 2.6, 2.8, knee[0])
        tube(c, [(hip[0] - 1, hip[1]), (kx, ky), (ax, ay)], [1.0, 0.9, 0.8], "Kmm")
        c.put(*P(ax, 0), "K"); c.put(*P(ax + 1, 0), "m"); c.put(*P(ax + 2, 0), "k")
    # back arm + fan
    shb = T(hip[0] - 0.5, hip[1] - 6)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 2.8, 2.8, -1)
    tube(c, [shb, (ex, ey)], [0.9, 0.8], "Kmm")
    c.put(*P(ex, ey), "w")
    line(c, ex, ey, hx, hy, "Q")
    if fan_b[1]: fan(c, hx, hy, fan_b[0], fan_b[1], spread=24)
    # torso: striped waistcoat, hunched
    tc = T(hip[0] + 0.3, hip[1] - 3.6)
    ell(c, tc[0], tc[1], 3.3, 4.2, stripes(tc[0], 2, CRIM, BLK, ang=lean), ang=lean, bias=0.1)
    # shirt front + gold watch chain
    for k in range(3):
        c.put(*P(*T(hip[0] + 2.6, hip[1] - 5 + k)), "W" if k else "X")
    a, b = T(hip[0] - 1, hip[1] - 2), T(hip[0] + 2, hip[1] - 1.5)
    line(c, *a, *b, "z", over=True)
    # front leg
    (kx, ky), (ax, ay) = ik(hip[0] + 1, hip[1], dx + feet[1], -1, 2.6, 2.8, knee[1])
    tube(c, [(hip[0] + 1, hip[1]), (kx, ky), (ax, ay)], [1.1, 0.9, 0.8], "Kms")
    c.put(*P(ax, 0), "K"); c.put(*P(ax + 1, 0), "m"); c.put(*P(ax + 2, 0), "s"); c.put(*P(ax + 3, -1), "z")
    # head (forward, at the end of the hunched neck)
    neck = T(hip[0] + 2.2, hip[1] - 7.8)
    c.part(SHARP_HEAD[head], *P(neck[0] + hd[0], neck[1] + hd[1] + 1))
    # front arm + fan
    shf = T(hip[0] + 1.2, hip[1] - 6)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 2.8, 2.8, 1)
    tube(c, [shf, (ex, ey)], [1.0, 0.9], "mms")
    c.put(*P(ex, ey), "W")   # shirt cuff
    line(c, ex, ey, hx, hy, "I")
    if fan_f[1]: fan(c, hx, hy, fan_f[0], fan_f[1], spread=22)
    c.put(*P(hx, hy), "j")
    if extra: extra(c)
    return finish(c, over)


def flying_card(x, y, ang=0.0, face=False):
    def f(c):
        card(c, x, y, 2.4, 3.4, face=face, ang=ang)
    return f


def card_ring(cx, cy, rx, ry, n, phase, front, size=1.0, face_every=2):
    """Cards orbiting on an ellipse; front=True draws only the near half."""
    def f(c):
        for i in range(n):
            a = phase + i * 2 * math.pi / n
            near = math.sin(a) > 0
            if near != front: continue
            x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
            card(c, x, y, 1.6 * size, 2.6 * size, face=(i % face_every == 0), ang=math.degrees(a) * 0.5)
    return f


def build_card_sharp(outdir):
    S = card_sharp
    idle = [S(fh=(5, -8), bh=(-3, -7), fan_f=(-40, 4)),
            S(fh=(5, -7.5), bh=(-3, -6.5), fan_f=(-35, 4), dy=0.3, lean=22),
            S(fh=(5.5, -7.5), bh=(-3, -6.5), fan_f=(-30, 4), dy=0.3, lean=22, head="leer"),
            S(fh=(5, -8), bh=(-3, -7), fan_f=(-45, 4), lean=21)]
    stride = [(-4, 3), (-2, 1), (0, -1), (3, -4), (1, -2), (-1, 0)]
    run = [S(feet=stride[i], lean=32, dy=[0, -0.6, 0, 0, -0.6, 0][i], fh=(6 - (i % 3), -7 + (i % 2)),
             bh=(-4 + (i % 3), -6), fan_f=(-30, 4), fan_b=(-150, 3), head="grin") for i in range(6)]
    # Deal: cock the card hand behind the ear (2 wind-ups), FLICK (release 3), follow through
    deal = [S(lean=12, fh=(-1, -12), fan_f=(-120, 1), bh=(-4, -7), head="leer", feet=(-3, 2)),
            S(lean=4, fh=(-3, -13), fan_f=(-160, 1), bh=(-5, -6), head="leer", feet=(-3, 3)),
            S(lean=28, fh=(5, -11), fan_f=(-30, 1), bh=(-5, -6), feet=(-3, 3),
              extra_back=lambda c: [line(c, -2, -14, 3, -13, "s"), line(c, 0, -15, 5, -12, "S")]),
            S(lean=34, fh=(8, -8), fan_f=(0, 0), bh=(-5, -6), head="grin", feet=(-3, 3),
              extra=lambda c: [card(c, 13, -9, 2.4, 3.4, face=False, ang=60), line(c, 9, -9, 11, -9, "w")]),
            S(lean=32, fh=(7, -5), fan_f=(0, 0), bh=(-4, -6), head="grin", feet=(-3, 3)),
            S(lean=22, fh=(5, -7), fan_f=(-40, 2), bh=(-3, -7), feet=(-2, 2))]
    # Shuffle: bridge the deck, cards whirl round (swap moment 3), gather, a deep bow
    def bridge(c):
        for k in range(5):
            t = k / 4.0
            x = -1 + 6 * t; y = -12 - 3 * math.sin(math.pi * t)
            card(c, x, y, 2.0, 3.0, face=(k % 2 == 0), ang=-50 + 100 * t)
    shuffle = [S(lean=16, fh=(4, -9), bh=(0, -9), fan_f=(-70, 3), fan_b=(-110, 3), head="leer"),
               S(lean=14, fh=(6, -11), bh=(-2, -10), fan_f=(0, 0), fan_b=(0, 0), extra=bridge, head="leer"),
               S(lean=10, fh=(5, -12), bh=(-3, -12), fan_f=(0, 0), fan_b=(0, 0),
                 extra_back=card_ring(1, -9, 8, 3, 6, 0.3, False), extra=card_ring(1, -9, 8, 3, 6, 0.3, True)),
               S(lean=8, fh=(4, -13), bh=(-3, -13), fan_f=(0, 0), fan_b=(0, 0), head="leer",
                 extra_back=card_ring(1, -9, 9, 4, 8, 1.0, False),
                 extra=lambda c: [card_ring(1, -9, 9, 4, 8, 1.0, True)(c), sparkle(c, -7, -16, 1, "N", "L"),
                                  sparkle(c, 9, -3, 1, "N", "L")]),
               S(lean=12, fh=(5, -11), bh=(-2, -11), fan_f=(0, 0), fan_b=(0, 0),
                 extra_back=card_ring(1, -10, 6, 2, 6, 1.8, False), extra=card_ring(1, -10, 6, 2, 6, 1.8, True)),
               S(lean=18, fh=(4, -9), bh=(1, -9), fan_f=(-60, 4), fan_b=(0, 0)),
               S(lean=55, dy=1, fh=(7, -2), bh=(-5, -9), fan_f=(20, 4), fan_b=(0, 0), head="bow", feet=(-3, 2),
                 knee=(1, 1))]
    d0 = S(lean=-10, fh=(2, -14), bh=(-6, -12), fan_f=(-100, 4), head="dead", feet=(-3, 2),
           extra=lambda c: [card(c, -6, -16, 2.2, 3.2, False, 30), card(c, 7, -17, 2.2, 3.2, True, -40)])
    d1 = grounded(rot_spr(S(lean=-5, fh=(3, -9), bh=(-5, -8), fan_f=(0, 0), fan_b=(0, 0), head="dead", feet=(-2, 2)),
                          -60, (0, -1)))
    d1 = merge(d1, Spr(SK.lit({(9, -3): "X", (9, -2): "W", (-8, -6): "E", (-9, -5): "d"})))
    # v0.8: a fourth death frame: he hits the floor and the last cards flutter down
    d2 = grounded(rot_spr(S(lean=-5, fh=(3, -8), bh=(-5, -7), fan_f=(0, 0), fan_b=(0, 0), head="dead", feet=(-2, 2)),
                          -82, (0, -1)))
    d2 = merge(d2, Spr(SK.lit({(7, -6): "X", (7, -5): "W", (8, -5): "W", (-10, -3): "E", (-10, -2): "d", (2, -9): "W"})))
    corpse = sharp_corpse()
    knock = S(lean=-18, dx=-1, fh=(3, -13), bh=(-6, -11), fan_f=(-110, 4), fan_b=(-160, 2), head="leer", feet=(-1, 4))
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.075] * 6),
             ("Deal", deal, [0.14, 0.12, 0.05, 0.07, 0.1, 0.14]),
             ("Shuffle", shuffle, [0.1, 0.1, 0.08, 0.08, 0.08, 0.1, 0.3])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxCardSharp", anims, outdir, scale=6)


def sharp_corpse():
    body = card_sharp(lean=0, fh=(3, -7), bh=(-2, -6), fan_f=(0, 0), fan_b=(0, 0), head="dead", feet=(-1, 1))
    lying = grounded(rot_spr(body, -90, (0, -1)))
    c = Canvas(); c.px = dict(lying.px)
    for k, (x, ang, face) in enumerate(((-9, 20, True), (-6, -30, False), (8, 70, True), (11, 10, False))):
        card(c, x, -1, 2.0, 3.0, face=face, ang=ang)
    return grounded(floor_cut(Spr(c.px)))


# ================================================================== DICE IMP (T1, flying)
IMP_HEAD = {
    "grin": Part("""
w....w.
Wh..hW.
.DEEEf.
DEYEYEf
DEEEEEE
dKXKXKE
.dKKKd.
""", (3, 6)),
    "glee": Part("""
w....w.
Wh..hW.
.DEEEf.
DKYEKYf
DEEEEEE
KXKXKXK
.KKEKK.
""", (3, 6)),
    "dead": Part("""
w....w.
Wh..hW.
.DEEEf.
DKEEKEf
DEEEEEE
dEKKKEE
.dDDDd.
""", (3, 6)),
}


def bat_wing(c, sx, sy, ang, spread, near=True, ln=7.0):
    """Bat wing from shoulder (sx,sy): a bone arm at ang and three finger struts fanning `spread` deg."""
    bone = "S" if near else "s"
    memb = "d" if near else "p"
    ex, ey = sx + 3.0 * math.cos(math.radians(ang)), sy + 3.0 * math.sin(math.radians(ang))
    tips = []
    for k in range(3):
        a = ang + 30 + k * spread / 2.0
        tips.append((ex + ln * (1 - 0.18 * k) * math.cos(math.radians(a)), ey + ln * (1 - 0.18 * k) * math.sin(math.radians(a))))
    # membrane between struts and back to the body, scalloped
    pts = [(sx, sy), (ex, ey)] + tips[::1] + [(sx + 0.5, sy + 2.5)]
    poly(c, [(sx, sy), (ex, ey), tips[0], ((tips[0][0] + tips[1][0]) / 2 + 0.3, (tips[0][1] + tips[1][1]) / 2 - 0.6),
             tips[1], ((tips[1][0] + tips[2][0]) / 2 + 0.3, (tips[1][1] + tips[2][1]) / 2 - 0.6), tips[2],
             (sx + 0.5, sy + 2.0)], memb, lit="flat")
    line(c, sx, sy, ex, ey, bone)
    for t in tips:
        line(c, ex, ey, t[0], t[1], bone)
    c.put(*P(ex, ey), "S" if near else "s")
    c.put(*P(ex + 0.5, ey - 1), "w" if near else "h")   # claw thumb


def dice_imp(alt=6.0, dx=0.0, flap=-40.0, tilt=0.0, die_rot=(0, 35, 0), die_pos=None, head="grin",
             hand=(4, -2), hand2=None, small_die=None, sit=True, tail=0.0, extra=None, extra_back=None, over=None,
             die_size=7, imp_dy=0.0, wing_spread=70):
    """Imp riding a big ivory die. alt: height of the die's bottom above the floor.
    die_pos: (x, y) override of the die centre (relative to the imp's seat) when the imp lets go of it."""
    c = Canvas()
    if extra_back: extra_back(c)
    if SK.small():
        alt = max(1.0, alt - IMP_ALT_DROP)
    dcx, dcy = dx, -alt - die_size * 0.75
    seat = (dx - 0.5, dcy - die_size * 0.75 + imp_dy)
    T = Xf(tilt, seat)
    sh = T(seat[0] - 0.5, seat[1] - 4)
    # back wing
    bat_wing(c, sh[0] - 1, sh[1], -160 + flap * 0.8, wing_spread, near=False)
    # tail with a bell on the tip
    tl = chain(seat[0] - 2, seat[1] - 0.5, [(2, 170 + tail), (2, 140 + tail), (2, 100 + tail)])
    for a, b in zip(tl, tl[1:]): line(c, *a, *b, "D")
    bell(c, tl[-1][0], tl[-1][1], s=0.8)
    # the die
    if die_pos is None:
        die(c, dcx, dcy, die_size, *die_rot)
    # body: little pot-bellied imp hugging the die top
    bc = T(seat[0], seat[1] - 2.2)
    ell(c, bc[0], bc[1], 2.4, 2.6, IMP, ang=tilt, bias=0.1)
    c.put(*P(bc[0] + 1, bc[1] + 0.5), "f")
    # legs dangling over the die front
    if sit:
        for k, lx in enumerate((-1, 1.5)):
            a = T(seat[0] + lx, seat[1] - 0.5)
            line(c, a[0], a[1], a[0] + 1.5, a[1] + 2.5, "D" if k else "d")
            c.put(*P(a[0] + 2, a[1] + 2.5), "K")
    else:
        for k, lx in enumerate((-1, 1)):
            a = T(seat[0] + lx, seat[1] - 0.5)
            line(c, a[0], a[1], a[0] - 0.5 + k, a[1] + 3, "D" if k else "d")
    if die_pos is not None:
        die(c, die_pos[0] + dx, die_pos[1], die_size, *die_rot)
    # head with horns
    hc = T(seat[0] + 0.8, seat[1] - 4.8)
    c.part(IMP_HEAD[head], *P(*hc))
    # arms
    for k, hd in enumerate((hand2 or (-2.5, -1.5), hand)):
        s_ = T(seat[0] + (-1.2 if k == 0 else 1.5), seat[1] - 3.6)
        hx, hy = seat[0] + hd[0], seat[1] + hd[1]
        line(c, s_[0], s_[1], hx, hy, "D" if k else "d")
        c.put(*P(hx, hy), "E" if k else "D")
    if small_die is not None:
        x, y, r = small_die
        die(c, seat[0] + x, seat[1] + y, 3, r, r * 1.3, 0)
    # near wing
    bat_wing(c, sh[0] + 0.5, sh[1] + 0.5, -150 + flap, wing_spread, near=True)
    if extra: extra(c)
    return finish(c, over)


IMP_ALT_DROP = 5.0   # design px the imp's hover is lowered by in small renders


def build_dice_imp(outdir):
    I = dice_imp
    flaps = [-60, -15, 15 if SK.small() else 40, 5]   # small: the up-stroke stays under the hover limit
    alts = [6, 5.5, 5, 5.5]
    idle = [I(flap=flaps[i], alt=alts[i], hand=(3, 0 + (i % 2) * 0.5), tail=[0, 10, 20, 5][i],
              head="glee" if i == 2 else "grin") for i in range(4)]
    run = [I(flap=[-70, -30, 20, 50, 0, -40][i], alt=[6, 5.5, 5, 5, 5.5, 6][i], tilt=14, dx=0,
             die_rot=(0, 45, 8), hand=(3, 0), tail=[-10, 0, 10, 20, 10, 0][i]) for i in range(6)]
    # Toss: fish a little die out, cock the arm (2 wind-ups), LOB (release 3), follow through
    toss = [I(flap=-20, tilt=-8, hand=(-1, -3), small_die=(-1, -4, 10), head="glee"),
            I(flap=10, tilt=-16, hand=(-3, -7), small_die=(-3, -8, 40)),
            I(flap=-50, tilt=10, hand=(3, -8), small_die=(4, -9, 80), head="glee"),
            I(flap=-30, tilt=18, hand=(5, -5), head="glee",
              extra=lambda c: [die(c, 9, -20, 3, 30, 60, 0), line(c, 4, -17, 6, -18, "w")]),
            I(flap=30, tilt=12, hand=(5, -2)),
            I(flap=-10, tilt=0, hand=(3, 0))]
    # Roll: heave the big die up (wind-up), spin it overhead (1-5), SLAM it down face-out (6), recover
    spin = [(0, 35, 0)] + [(40 * k, 35 + 12 * k, 0) for k in range(1, 6)]
    roll = [I(flap=-30, alt=7, imp_dy=0, hand=(3, 2), hand2=(-3, 2), head="glee", die_rot=spin[0])]
    for k in range(1, 6):
        roll.append(I(flap=[-60, 40, -60, 40, -60][k - 1], alt=4, die_rot=spin[k],
                      die_pos=(1, -24 - [0, 2, 3, 2, 1][k - 1]), hand=(3, -8), hand2=(-2, -8), head="glee",
                      sit=False, imp_dy=6, tilt=[-5, 5, -5, 5, -5][k - 1]))

    def dust(c):
        for x, y, ch in ((-5, 0, "S"), (-6, -1, "s"), (8, 0, "S"), (9, -1, "s"), (-4, -1, "S"), (7, -1, "S")):
            c.put(x, y, ch)
    roll.append(I(flap=50, alt=4.5, die_rot=(0, 90, 0), die_pos=(2, -4), hand=(4, 4), hand2=(-1, 4), sit=False,
                  imp_dy=0, head="glee", tilt=20, extra=dust))
    roll.append(I(flap=-30, alt=6.5, die_rot=(0, 90, 0), die_pos=(2, -4), hand=(3, 2), hand2=(-2, 2), sit=False,
                  head="grin", tilt=8))
    d0 = I(flap=60, alt=7, tilt=-25, head="dead", hand=(3, -6), hand2=(-4, -5))
    d1 = I(flap=80, alt=2, tilt=-60, head="dead", die_rot=(35, 60, 30), hand=(-2, -4), wing_spread=40)
    # v0.8: a fourth death frame: it crashes, the die bouncing out of its claws
    d2 = grounded(rot_spr(I(flap=95, alt=0, tilt=-30, head="dead", die_rot=(70, 80, 50), hand=(-3, -2), wing_spread=55),
                          -75, (0, -1)))
    corpse = imp_corpse()
    knock = I(flap=70, alt=7, tilt=-28, head="grin", hand=(2, -6), hand2=(-5, -6), die_rot=(-10, 20, -12))
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.07] * 6),
             ("Toss", toss, [0.14, 0.12, 0.05, 0.08, 0.1, 0.14]),
             ("Roll", roll, [0.14, 0.07, 0.07, 0.07, 0.07, 0.07, 0.06, 0.25])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("JinxDiceImp", anims, outdir, scale=6)


def imp_corpse():
    c = Canvas()
    die(c, 3, -4, 7, 0, 20, 0)
    b = Canvas()
    ell(b, 0, -2, 2.4, 1.6, IMP)
    b.part(IMP_HEAD["dead"], -4, -1)
    bat_wing(b, 1, -3, -30, 50, near=True, ln=5)
    SK.paste(c, b, -6, 1)
    return grounded(finish(c))


# ================================================================== RINGMASTER (T2)
RING_HEAD = {
    "grin": Part("""
...hwWWX..
..hwWWXXX.
..hwKWWKX.
..hwWWWXXW
.KhwWWXXXK
.KKKKKKKKK
..hKXWXWXK
...hKKKKK.
....hww...
""", (5, 8)),
    "shout": Part("""
...hwWWX..
..hwKWWKX.
..hwKWWKX.
..hwWWWXXW
.KhwWWXXXK
.KKKKKKKKK
..hKXWXWXK
...hKEEKK.
....hKK...
""", (5, 8)),
    "dead": Part("""
...hwWWX..
..hwWWXXX.
..hKwWKwX.
..hwKWwKXW
.KhwWWXXX.
..KKKKKKK.
..hwKKKKw.
...hwwww..
....hww...
""", (5, 8)),
}


def top_hat(c, x, y, tilt=0.0, h=6):
    """Top hat whose brim centre sits at (x, y)."""
    T = Xf(tilt, (x, y))
    poly(c, [T(x - 2.6, y - 0.5), T(x + 2.6, y - 0.5), T(x + 2.9, y - h), T(x - 2.4, y - h)], "Kmms", bias=0.1)
    a, b = T(x - 2.6, y - 1.5), T(x + 2.7, y - 1.5)
    line(c, *a, *b, "E")
    a, b = T(x - 2.5, y - 2.2), T(x + 2.7, y - 2.2)
    line(c, *a, *b, "D")
    a, b = T(x - 4.2, y), T(x + 4.4, y)
    line(c, *a, *b, "m")
    c.put(*P(*T(x - 4.2, y - 0.6)), "K"); c.put(*P(*T(x + 4.4, y - 0.6)), "s")
    c.put(*P(*T(x - 1.6, y - h + 0.6)), "S")


def whip_pts(hx, hy, angs, seg=3.0):
    return chain(hx, hy, [(seg, a) for a in angs])


def whip(c, pts, crack=False):
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        line(c, *a, *b, "T" if i < 2 else "t")
    if crack:
        x, y = pts[-1]
        sparkle(c, x + 1, y, 2, "Y", "y")


def ringmaster(dx=0.0, dy=0.0, lean=0.0, feet=(-3, 3), fh=(6, -12), bh=(-5, -10), head="grin", hat_tilt=0.0,
               hat=True, whip_angs=None, coil=True, tails=0.0, crack=False, hoop=None, extra=None, extra_back=None,
               over=None, knees=(1, 1)):
    c = Canvas()
    if extra_back: extra_back(c)
    hip = (dx, -10 + dy)
    T = Xf(lean, hip)
    shf, shb = T(hip[0] + 1.2, hip[1] - 8), T(hip[0] - 1.5, hip[1] - 8)
    # coat tails behind
    w0 = T(hip[0] - 2.5, hip[1] - 1)
    tl = [w0, T(hip[0] + 0.5, hip[1] - 1), (hip[0] - 1 - tails * 0.6, hip[1] + 6.5 - abs(tails) * 0.2),
          (hip[0] - 3.5 - tails, hip[1] + 6 - abs(tails) * 0.3)]
    poly(c, tl, CRIM, bias=-0.05)
    line(c, hip[0] - 1.5 - tails * 0.7, hip[1] + 1, hip[0] - 2 - tails * 0.8, hip[1] + 6, "d")
    # back leg: v0.8 white riding breeches over black boots (was all black)
    (kx, ky), (fx, fy) = ik(hip[0] - 0.8, hip[1], dx + feet[0], -1.2, 5.0, 5.2, knees[0])
    mx2, my2 = kx + (fx - kx) * 0.45, ky + (fy - ky) * 0.45
    tube(c, [(hip[0] - 0.8, hip[1]), (kx, ky), (mx2, my2)], [2.0, 1.5, 1.3], "hwwW")
    tube(c, [(mx2, my2), (fx, fy)], [1.1, 0.9], "Kmms")
    c.put(*P(fx, 0), "K"); c.put(*P(fx + 1, 0), "K"); c.put(*P(fx + 2, 0), "m"); c.put(*P(fx, -1), "K")
    # hoop held behind (drawn before the body when it is behind)
    if hoop and hoop[3] == "back":
        flaming_hoop(c, hoop[0], hoop[1], hoop[2], hoop[4] if len(hoop) > 4 else 1)
    # back arm
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 4.0, 4.0, -1)
    tube(c, [shb, (ex, ey), (hx, hy)], [1.0, 0.9, 0.8], "ddD")
    c.put(*P(hx, hy), "W")
    # torso: v0.8 a stout showman: barrel chest in a scarlet tailcoat, round belly in a gold-buttoned
    # waistcoat (was a thin red-and-black coat that read like the Marionette)
    tor = [T(hip[0] - 4.2, hip[1] - 0.5), T(hip[0] + 3.4, hip[1] - 0.5), T(hip[0] + 4.4, hip[1] - 8.8),
           T(hip[0] - 4.4, hip[1] - 8.8)]
    poly(c, tor, CRIM, bias=0.4)
    bx_, by_ = T(hip[0] + 2.2, hip[1] - 4.0)
    ell(c, bx_, by_, 4.8, 4.4, "AezZ", bias=0.1)                       # the belly / waistcoat
    for k in (-2.5, 0, 2.5):
        c.put(*P(bx_ + 1.2, by_ + k), "d")                              # buttons
    line(c, *T(hip[0] - 3.0, hip[1] - 0.8), *T(hip[0] + 5.6, hip[1] - 0.8), "K")   # belt under the belly
    c.put(*P(*T(hip[0] + 3.2, hip[1] - 0.8)), "Z")
    # shirt front, lapels, bow tie
    for k in range(4, 7):
        c.put(*P(*T(hip[0] + 1.6, hip[1] - 2 - k)), "X")
        c.put(*P(*T(hip[0] + 0.4, hip[1] - 3 - k * 0.7)), "K")
    c.put(*P(*T(hip[0] + 1.5, hip[1] - 8.4)), "K"); c.put(*P(*T(hip[0] + 2.6, hip[1] - 8.4)), "K")
    c.put(*P(*T(hip[0] + 2, hip[1] - 8.4)), "E")
    # front leg
    (kx, ky), (fx, fy) = ik(hip[0] + 0.8, hip[1], dx + feet[1], -1.2, 5.0, 5.2, knees[1])
    mx2, my2 = kx + (fx - kx) * 0.45, ky + (fy - ky) * 0.45
    tube(c, [(hip[0] + 0.8, hip[1]), (kx, ky), (mx2, my2)], [2.1, 1.6, 1.4], "wWWX")
    tube(c, [(mx2, my2), (fx, fy)], [1.2, 1.0], "Kmss")
    c.put(*P(fx, 0), "K"); c.put(*P(fx + 1, 0), "m"); c.put(*P(fx + 2, 0), "s"); c.put(*P(fx + 3, 0), "m")
    c.put(*P(fx + 1, -1), "z")
    # head + hat
    neck = T(hip[0] + 1.0, hip[1] - 9.2)
    c.part(RING_HEAD[head], *P(neck[0], neck[1] + 1))
    # v0.8: a waxed handlebar moustache
    mx_, my_ = P(neck[0] + 1, neck[1] - 1)
    for ox, oy in ((-2, 0), (-3, -1), (2, 0), (3, -1), (4, -2)):
        c.put(mx_ + ox, my_ + oy, "K")
    if hat:
        top_hat(c, neck[0] + 0.3, neck[1] - 8.4, tilt=hat_tilt + lean * 0.5)
    # gold epaulette
    ell(c, shf[0] - 0.2, shf[1] + 0.3, 1.8, 1.0, GOLD, bias=0.2)
    # v0.9 lineage: the Jack-in-the-Box's crimson-and-gold harlequin on the coat tails
    for (tx, ty) in ((-1.0, 2.5), (-2.4, 4.6)):
        c.put(*P(hip[0] + tx - tails * 0.5, hip[1] + ty), "z")
    c.put(*P(shf[0] - 1.5, shf[1] + 1.4), "A"); c.put(*P(shf[0] + 0.5, shf[1] + 1.4), "A")
    # whip
    if whip_angs is not None:
        whip(c, whip_pts(fh[0] + dx, fh[1] + dy, whip_angs), crack)
    elif coil:   # coiled whip hanging from the fist
        cx_, cy_ = fh[0] + dx + 0.5, fh[1] + dy + 3.6
        for k in range(16):
            a = 2 * math.pi * k / 16
            c.put(*P(cx_ + 1.9 * math.cos(a), cy_ + 2.5 * math.sin(a)), "T" if math.cos(a) < 0.3 else "t")
        c.put(*P(cx_ - 0.5, cy_ + 3.5), "t"); c.put(*P(cx_ - 1, cy_ + 4.5), "t")
    # front arm
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 4.0, 4.0, 1)
    tube(c, [shf, (ex, ey), (hx, hy)], [1.1, 1.0, 0.9], "DEf")
    c.put(*P(hx, hy), "X"); c.put(*P(hx + 1, hy), "W")
    if hoop and hoop[3] == "front":
        flaming_hoop(c, hoop[0], hoop[1], hoop[2], hoop[4] if len(hoop) > 4 else 1)
    if extra: extra(c)
    return finish(c, over)


def flaming_hoop(c, x, y, rx, fire=1, ry=5.0, phase=0):
    """Gold hoop seen near edge-on (rx small) with flames licking up its rim. fire 0..2."""
    for k in range(28):
        a = 2 * math.pi * k / 28
        px, py = x + rx * math.cos(a), y + ry * math.sin(a)
        near = math.cos(a) > 0
        c.put(*P(px, py), "z" if near else "A")
    if fire:
        r = random.Random(phase + int(x * 3))
        for k in range(10 if fire > 1 else 5):
            a = 2 * math.pi * (k + 0.5 * (phase % 2)) / (10 if fire > 1 else 5)
            px, py = x + rx * math.cos(a), y + ry * math.sin(a)
            hgt = r.randint(1, 2 + fire)
            for j in range(hgt):
                c.put(*P(px + (0 if j < 2 else r.choice((-1, 1))), py - 1 - j), "oOYy"[min(3, j + (1 if fire > 1 else 0))] if j < hgt - 1 else "o")


def build_ringmaster(outdir):
    R = ringmaster
    idle = [R(fh=(6, -12), bh=(-4, -10), tails=0),
            R(fh=(6, -11.5), bh=(-4, -9.5), dy=0.4, tails=0.5, hat_tilt=-3),
            R(fh=(6.2, -11.5), bh=(-4, -9.5), dy=0.4, tails=1, hat_tilt=-4, head="grin"),
            R(fh=(6, -12), bh=(-4, -10), tails=0.5, hat_tilt=-1)]
    stride = [(-7, 5), (-4, 2), (-1, -1), (5, -7), (2, -4), (-1, -1)]
    run = [R(feet=stride[i], lean=8, dy=[0, -0.8, 0, 0, -0.8, 0][i], tails=[3, 4, 3.5, 3, 4, 3.5][i],
             fh=(6 - [0, 1, 2, 3, 2, 1][i], -12), bh=(-5 + [0, 1, 2, 3, 2, 1][i], -11), hat_tilt=-6) for i in range(6)]
    # Whip: arm back (2 wind-ups), CRACK (hit 3), rebound, lash drops, coil
    whip_a = [R(lean=-6, fh=(-2, -22), bh=(-5, -10), whip_angs=[170, 150, 125, 105, 95, 90], tails=-1, feet=(-4, 3)),
              R(lean=-10, fh=(-4, -25), bh=(-6, -9), whip_angs=[-150, -175, 170, 150, 125, 100], head="shout",
                tails=-1.5, feet=(-4, 3)),
              R(lean=6, fh=(3, -23), bh=(-6, -9), whip_angs=[-160, 170, 150, 165, -170, -150], head="shout",
                tails=1.5, feet=(-5, 4)),
              R(lean=12, fh=(9, -16), bh=(-6, -9), whip_angs=[-4, -2, 0, 2, 4, 6, 6, 8], head="shout", crack=True,
                tails=3, feet=(-6, 5), extra_back=lambda c: speed_lines(c, -2, 6, (-22, -19), "s")),
              R(lean=10, fh=(9, -14), bh=(-6, -9), whip_angs=[5, -15, 20, -15, 25, 0, 30], head="grin", tails=2.5,
                feet=(-6, 5)),
              R(lean=6, fh=(8, -12), bh=(-5, -9), whip_angs=[30, 45, 60, 75, 85, 90], tails=1.5, feet=(-5, 4)),
              R(lean=2, fh=(6, -12), bh=(-4, -10), tails=0.5, feet=(-4, 3))]
    # Hoop: fetch the hoop, it ignites, swing it high behind (2-3), RELEASE (4), flourish, tip the hat
    hoop_a = [R(lean=-4, fh=(6, -12), bh=(-7, -7), hoop=(-8, -8, 1.2, "back", 0)),
              R(lean=-8, fh=(6, -12), bh=(-8, -14), hoop=(-9, -15, 1.6, "back", 1), head="grin"),
              R(lean=-12, fh=(5, -13), bh=(-6, -22), hoop=(-7, -23, 2.0, "back", 2), head="shout"),
              R(lean=4, fh=(5, -13), bh=(3, -21), hoop=(5, -22, 2.4, "front", 2), head="shout", tails=1.5),
              R(lean=10, fh=(5, -12), bh=(9, -16), hoop=(16, -16, 3.0, "front", 2), head="shout", tails=2.5,
                extra_back=lambda c: speed_lines(c, 4, 11, (-18, -14), "o")),
              R(lean=8, fh=(5, -12), bh=(8, -15), tails=2, head="grin"),
              R(lean=2, fh=(4, -23), bh=(-4, -10), head="grin", hat_tilt=12, tails=1),
              R(lean=0, fh=(6, -12), bh=(-4, -10), tails=0.5)]
    d0 = R(lean=-14, dx=-1, fh=(5, -18), bh=(-7, -16), head="dead", hat=False, feet=(-4, 3), tails=-2,
           extra=lambda c: top_hat(c, -6, -29, tilt=-40))
    d1 = R(lean=-8, dy=4, fh=(5, -9), bh=(-6, -8), head="dead", hat=False, feet=(-5, 5), tails=-1,
           extra=lambda c: top_hat(c, -9, -3, tilt=-70))
    d2 = grounded(rot_spr(R(lean=0, fh=(6, -9), bh=(-4, -9), head="dead", hat=False, feet=(-2, 2)), -55, (0, -1)))
    d2 = merge(d2, finish(_hat_canvas(-17, -1, -90), cut=True))
    corpse = ring_corpse()
    knock = R(lean=-18, dx=-1.5, fh=(6, -18), bh=(-8, -17), head="shout", hat_tilt=-25, feet=(-2, 5), tails=-2)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.085] * 6),
             ("Whip", whip_a, [0.16, 0.12, 0.06, 0.06, 0.1, 0.12, 0.16]),
             ("Hoop", hoop_a, [0.14, 0.12, 0.12, 0.06, 0.06, 0.12, 0.2, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.14, 0.14, 0.4], knock)
    return sheet("JinxRingmaster", anims, outdir, scale=5)


def _hat_canvas(x, y, tilt):
    c = Canvas(); top_hat(c, x, y, tilt=tilt); return c


def ring_corpse():
    body = ringmaster(lean=0, fh=(5, -8), bh=(-3, -8), head="dead", hat=False, feet=(-2, 2), coil=False)
    lying = grounded(rot_spr(body, -90, (0, -1)))
    c = Canvas(); c.px = dict(lying.px)
    w = Canvas()
    whip(w, whip_pts(2, -1, [0, 10, -10, 5, 0, -5, 0], 2.5))
    top_hat(w, -17, -1, tilt=-20)
    s = merge(Spr(c.px), finish(w))
    return grounded(floor_cut(s))


# ================================================================== MARIONETTE (T2)
PUPPET_HEAD = {
    "grin": Part("""
.hWXXW.
hwWXXKX
hwKXKXX
hwWXXKW
hKKKKKK
hKXWXWK
hKwXXKw
.hKwwK.
""", (3, 7)),
    "gape": Part("""
.hWXXW.
hwKXXKX
hwKXKKX
hwWXXKW
hKKKKKK
hKXWXWK
.KKKKK.
.hK..K.
""", (3, 7)),
    "dead": Part("""
.hWXXW.
hwWXXKX
hwkXkKX
hwWXXKW
hwKKKKw
hwKXWKw
hKwXXKw
.hKwwK.
""", (3, 7)),
}


# v0.8: the Marionette is a carved wooden doll (it read as a second thin red-and-black jester): its face is
# varnished wood with painted cheeks, its limbs are turned wood on brass ball joints, and its strings run up
# to a wooden control cross.
WOOD_FACE = {"h": "T", "w": "h", "W": "i", "X": "w", "k": "k"}
MWOOD_D = "tThh"      # far limbs (darker wood)
MWOOD_L = "Thiw"      # near limbs (lit wood)


def wood_head(part):
    p = Part.__new__(Part)
    p.px = {k: WOOD_FACE.get(v, v) for k, v in part.px.items()}
    return p


def puppet_limb(c, x, y, a1, a2, l1, l2, mat1, mat2, r1=1.1, r2=0.9, joint="T"):
    ex, ey = x + l1 * math.cos(math.radians(a1)), y + l1 * math.sin(math.radians(a1))
    hx, hy = ex + l2 * math.cos(math.radians(a2)), ey + l2 * math.sin(math.radians(a2))
    tube(c, [(x, y), (ex, ey)], [r1, r1 * 0.9], mat1)
    tube(c, [(ex, ey), (hx, hy)], [r2, r2 * 0.85], mat2)
    c.put(*P(ex, ey), joint)
    return (ex, ey), (hx, hy)


def marionette(dx=0.0, dy=0.0, tilt=0.0, head_tilt=0.0, arms=((100, 95), (80, 95)), legs=((95, 92), (85, 92)),
               head="grin", strings=True, cut=False, extra=None, extra_back=None, extra_over=None, top=-38,
               hand_glow=False, magic=None, cap_flop=0.0):
    """Life-size jester puppet hanging on strings. arms/legs: ((upper, lower) back, (upper, lower) front)
    absolute angles in degrees (90 = straight down)."""
    c = Canvas()
    if extra_back: extra_back(c)
    if SK.small() and top == -38:
        top = MARI_TOP_SMALL
    pel = (dx, -13.5 + dy)          # it hangs: toes clear the floor by a pixel or two
    T = Xf(tilt, pel)
    neck = T(pel[0] + 0.5, pel[1] - 8.5)
    shb, shf = T(pel[0] - 2.0, pel[1] - 7.5), T(pel[0] + 2.0, pel[1] - 7.5)
    hipb, hipf = T(pel[0] - 1.2, pel[1]), T(pel[0] + 1.2, pel[1])
    att = {}
    # back limbs (black)
    kb, fb = puppet_limb(c, *hipb, legs[0][0] + tilt, legs[0][1] + tilt, 5.0, 5.0, MWOOD_D, MWOOD_D, 1.0, 0.8, "A")
    line(c, *fb, fb[0] + 1.5, fb[1] + 0.8, "D")
    eb, hb = puppet_limb(c, *shb, arms[0][0], arms[0][1], 4.0, 4.0, MWOOD_D, MWOOD_D, 0.9, 0.75, "A")
    c.put(*P(*hb), "T")
    # torso: harlequin tunic with a dagged hem
    tor = [T(pel[0] - 3.0, pel[1] - 8), T(pel[0] + 3.2, pel[1] - 8), T(pel[0] + 2.6, pel[1] + 1.0),
           T(pel[0] + 1.3, pel[1] + 2.5), T(pel[0], pel[1] + 1.2), T(pel[0] - 1.3, pel[1] + 2.5), T(pel[0] - 2.8, pel[1] + 1.0)]
    poly(c, tor, harl(pel[0] - 1.5, pel[1] - 4, 3, "tThi", "dDEE", ang=tilt), bias=0.25)   # painted wooden barrel
    # brass pins and the waist hinge
    c.put(*P(*T(pel[0] + 2.4, pel[1] - 3)), "z")
    # v0.10 lineage (one parent, the Jack-in-the-Box): the box's gold harlequin diamond painted on the chest
    for (x, y, ch) in ((0.5, -7, "Z"), (-0.5, -6, "z"), (1.5, -6, "Z"), (0.5, -6, "e"), (-0.5, -5, "e"), (1.5, -5, "z"),
                       (0.5, -5, "A"), (0.5, -4, "e")):
        c.put(*P(*T(pel[0] + x, pel[1] + y)), ch)
    line(c, *T(pel[0] - 2.6, pel[1] - 0.6), *T(pel[0] + 2.4, pel[1] - 0.6), "k")
    # front limbs (crimson)
    kf, ff = puppet_limb(c, *hipf, legs[1][0] + tilt, legs[1][1] + tilt, 5.0, 5.0, MWOOD_L, MWOOD_L, 1.1, 0.9, "z")
    # v0.9 lineage: the Jack-in-the-Box's gold spring for a knee
    spring(c, kf[0] - 0.4, kf[1] - 1.2, kf[0] + 0.4, kf[1] + 1.2, 2, amp=1.0)
    line(c, *ff, ff[0] + 1.6, ff[1] + 0.8, "E"); c.put(*P(ff[0] + 2, ff[1] - 0.2), "f")
    # ruff collar with jester points
    for k in range(5):
        a = math.radians(180 + 45 * k)
        px, py = neck[0] + 3.3 * math.cos(a), neck[1] + 1.5 + 1.2 * math.sin(a) + 1.2
        c.put(*P(px, py + 1), "E" if k % 2 else "m")
    ell(c, neck[0], neck[1] + 1.2, 3.4, 1.3, stripes(neck[0], 1, "wWWX", "hwwW"), bias=0.2)
    bell(c, neck[0] - 3.6, neck[1] + 2.4, s=0.8); bell(c, neck[0] + 3.8, neck[1] + 2.4, s=0.8)
    # head on its peg
    hc = (neck[0] + head_tilt * 0.06, neck[1])
    hp = Canvas()
    # carved wooden hair-cap with a red painted bow (no jester points: that is the Grand Jester's look)
    ell(hp, 0, -7.2, 3.6, 2.1, "tThi", bias=0.25)
    hp.put(*P(2.2 + cap_flop * 0.04, -8.6), "E"); hp.put(*P(3.2 + cap_flop * 0.04, -9.2), "f"); hp.put(*P(3.2 + cap_flop * 0.04, -8.0), "D")
    hp.part(wood_head(PUPPET_HEAD[head]), 0, 0)
    hp.put(2, -3, "E")                                   # painted cheek
    # v0.10 lineage: the Jack's grin is carved into the doll's face (PUPPET_HEAD); the Card Sharp's visor is gone
    hs = rot_spr(hp.spr(), head_tilt, (0, 0)) if head_tilt else hp.spr()
    SK.paste(c, hs, *P(*hc))
    att["head"] = (hc[0] + 6 * math.sin(math.radians(head_tilt)), hc[1] - 8)
    # front arm last
    ef, hf = puppet_limb(c, *shf, arms[1][0], arms[1][1], 4.0, 4.0, MWOOD_L, MWOOD_L, 1.0, 0.8, "z")
    c.put(*P(*hf), "i"); c.put(*P(hf[0] + 0.7, hf[1] + 0.5), "w")
    if hand_glow:
        for hh in (hb, hf):
            sparkle(c, hh[0], hh[1], 1, "N", "L")
    if extra: extra(c)
    att.update({"hb": hb, "hf": hf, "kb": kb, "kf": kf})
    o = Canvas()
    if strings:
        cx = dx
        for key in ("head", "hb", "hf", "kf"):
            ax, ay = att[key]
            tx = cx + (ax - cx) * 0.45 + (2 if key in ("hf", "kf") else -2 if key in ("hb", "kb") else 0)
            if cut:
                line(o, ax, ay - 1, ax + (tx - ax) * 0.2, ay - 4, "S")
                line(o, tx, top, tx + (ax - tx) * 0.1, top + 7, "S")
            else:
                for (x, y) in line_px(*SK.spt(tx, top), *SK.spt(ax, ay - 1)):
                    if (x, y) not in c.px: o.raw.put(x, y, "S")
        if not cut:
            # the wooden control cross the strings hang from
            line(o, cx - 6 + tilt * 0.1, top, cx + 6 + tilt * 0.1, top, "T")
            line(o, cx + tilt * 0.1, top - 1, cx + tilt * 0.1, top + 1, "h")
            o.put(*P(cx - 6 + tilt * 0.1, top), "k"); o.put(*P(cx + 6 + tilt * 0.1, top), "k")
    if magic: magic(o)
    if extra_over: extra_over(o)
    return finish(c, o.spr())


def magic_strings(src, tgts, col="N", bright="L"):
    """Purple strings shooting from the hands (src list) to targets."""
    def f(o):
        for (sx, sy), (tx, ty) in zip(src, tgts):
            pts = line_px(*P(sx, sy), *P(tx, ty))
            for i, (x, y) in enumerate(pts):
                o.put(x, y, bright if i % 4 == 0 else col)
            sparkle(o, tx, ty, 1, col, bright)
    return f


MARI_TOP_SMALL = -36   # strings end lower in small renders (the cell top counts toward the size limit)


def build_marionette(outdir):
    M = marionette
    # Idle: jerky, a different string yanks each beat (uneven holds sell the puppet)
    idle = [M(arms=((100, 95), (80, 92)), legs=((95, 92), (86, 92))),
            M(arms=((100, 95), (-30, 50)), legs=((95, 92), (86, 92)), head_tilt=16, dy=-1, cap_flop=10),
            M(arms=((105, 100), (95, 90)), legs=((40, 110), (88, 92)), head_tilt=-12, dy=-1, tilt=-4, cap_flop=-12),
            M(arms=((95, 110), (85, 100)), legs=((95, 92), (86, 92)), head_tilt=24, tilt=3, head="gape", cap_flop=18)]
    # Run: high stiff knee-lifts, limp arm swings, bobbing on the strings
    run = []
    for i in range(6):
        ph = i % 3
        lift_f = i < 3
        lb = (95, 92) if lift_f else [(20, 100), (-5, 85), (40, 110)][ph]
        lf = [(20, 100), (-5, 85), (40, 110)][ph] if lift_f else (88, 95)
        run.append(M(arms=((60 + 30 * ph, 80), (130 - 30 * ph, 95)), legs=(lb, lf), dy=[-2, -3, -1, -2, -3, -1][i],
                     tilt=6, head_tilt=[8, -6, 12, 8, -6, 12][i], cap_flop=[-10, 10, -20, -10, 10, -20][i]))
    # Lash: arm yanked up (2 wind-ups), string-limb SLASH (hit 3), dangle, jerk back
    def slash(c):
        for k in range(14):
            a = math.radians(-70 + k * 9)
            for rr in (9.5, 10.5):
                if k > 2:
                    c.put(*P(4 + rr * math.cos(a), -19 + rr * math.sin(a)), "L" if rr < 10 and k > 8 else "N")
    lash = [M(arms=((110, 100), (-110, -150)), legs=((95, 92), (80, 90)), tilt=-8, head_tilt=-14, dy=-1),
            M(arms=((120, 110), (-130, -175)), legs=((100, 95), (70, 85)), tilt=-12, head_tilt=-22, dy=-2, head="gape"),
            M(arms=((100, 100), (-40, -20)), legs=((95, 92), (60, 80)), tilt=6, head_tilt=10, dy=-1, head="gape"),
            M(arms=((95, 100), (15, 35)), legs=((100, 95), (60, 80)), tilt=14, head_tilt=20, head="gape",
              extra_over=slash),
            M(arms=((95, 100), (70, 110)), legs=((95, 92), (75, 88)), tilt=10, head_tilt=28),
            M(arms=((100, 95), (60, 70)), legs=((95, 92), (86, 92)), tilt=0, head_tilt=-8, dy=-1)]
    # Strings: hands rise (0-2), purple strings SHOOT out (3), taut (4), PULL (5-6), let go (7)
    reach = [(26, -16), (26, -12)]
    strings = [M(arms=((60, -40), (40, -60)), legs=((95, 92), (86, 92)), head_tilt=-6),
               M(arms=((-60, -100), (-40, -80)), legs=((100, 95), (80, 90)), head_tilt=-20, dy=-2, head="gape"),
               M(arms=((-80, -110), (-60, -95)), legs=((105, 95), (75, 88)), head_tilt=-28, dy=-3, head="gape",
                 hand_glow=True),
               M(arms=((-20, -5), (-10, 5)), legs=((95, 92), (70, 85)), tilt=10, head_tilt=12, dy=-1, head="gape",
                 hand_glow=True, magic=lambda o: magic_strings([(5, -21), (9, -20)], reach)(o)),
               M(arms=((-5, 0), (0, 5)), legs=((95, 92), (70, 85)), tilt=12, head_tilt=14, dy=-1,
                 magic=lambda o: magic_strings([(6, -20), (10, -19)], reach)(o)),
               M(arms=((150, 20), (170, 40)), legs=((60, 110), (110, 100)), tilt=-14, head_tilt=-20, dx=-1,
                 head="gape", magic=lambda o: magic_strings([(1, -13), (3, -12)], [(22, -14), (22, -11)])(o)),
               M(arms=((165, 40), (180, 60)), legs=((50, 120), (120, 110)), tilt=-20, head_tilt=-30, dx=-2,
                 head="gape", magic=lambda o: magic_strings([(-1, -12), (1, -11)], [(17, -12), (17, -10)])(o)),
               M(arms=((100, 95), (80, 92)), legs=((95, 92), (86, 92)), head_tilt=6)]
    # Death: strings snap, it drops in a heap
    d0 = M(arms=((-60, 40), (-80, 30)), legs=((95, 92), (86, 92)), head_tilt=-20, cut=True, head="gape", dy=-2)
    d1 = M(arms=((150, 100), (30, 90)), legs=((150, 60), (20, 120)), head_tilt=35, strings=False, head="dead", dy=5,
           tilt=10)
    d2 = grounded(rot_spr(M(arms=((150, 120), (40, 100)), legs=((120, 60), (60, 120)), head_tilt=40, strings=False,
                            head="dead"), -70, (0, -6)))
    corpse = puppet_corpse()
    knock = M(arms=((-150, -120), (-120, -60)), legs=((60, 100), (40, 80)), tilt=-18, head_tilt=-30, dx=-1, dy=-2,
              head="gape")
    anims = [("Idle", idle, [0.3, 0.09, 0.26, 0.1]), ("Run", run, [0.09, 0.06, 0.09, 0.09, 0.06, 0.09]),
             ("Lash", lash, [0.16, 0.1, 0.05, 0.06, 0.16, 0.12]),
             ("Strings", strings, [0.12, 0.12, 0.1, 0.05, 0.12, 0.06, 0.18, 0.16])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.08, 0.1, 0.12, 0.4], knock)
    return sheet("JinxMarionette", anims, outdir, scale=5)


def puppet_corpse():
    body = marionette(arms=((170, 120), (10, 60)), legs=((130, 90), (20, 70)), head_tilt=0, strings=False,
                      head="dead", tilt=0)
    lying = grounded(rot_spr(body, -90, (0, -6)))
    c = Canvas(); c.px = dict(lying.px)
    o = Canvas()
    for k in range(5):   # cut strings lying slack across it
        line(o, -10 + k * 4, -1 - (k % 2), -7 + k * 4, -3 - (k % 3), "S")
    return grounded(floor_cut(merge(Spr(c.px), o.spr())))


# ================================================================== GRAND JESTER (T3)
GJ_MASK = {
    "grin": Part("""
..DEEmms..
.dDEEmmss.
dDEYYmYYm.
dDKKEmKKs.
dXXXXXXXXK
KXKWKXKWKK
.dKKKKKKK.
..dDDmmK..
""", (5, 7)),
    "laugh": Part("""
..DEEmms..
.dDEEmmss.
dDYYEmYYm.
dDEEEmmms.
dXXXXXXXXK
KKKKKKKKKK
.dXKXKXKX.
..dDDmmK..
""", (5, 7)),
    "glare": Part("""
..DEEmms..
.dDEEmmss.
dDKYYmKYm.
dDEKEmmKs.
dXXXXXXXXK
KXKWKXKWKK
.dKKKKKKK.
..dDDmmK..
""", (5, 7)),
    "dead": Part("""
..DEEmms..
.dDEEmmss.
dDKKEmKKm.
dDEEEmmms.
dXXXXXXXXK
KXKWKXKWKK
.dKKKKKKK.
..dDDmmK..
""", (5, 7)),
}


def juggle_ball(c, x, y, ph=0, r=2.0):
    ell(c, x, y, r + 1.0, r + 1.0, "K", flat=True)
    ell(c, x, y, r, r, stripes(x + ph, 1, "Eff", "ezZ", ang=45), bias=0.15)


def jester_hat(c, x, y, sway=0.0, ring=0):
    """Three-pointed belled hat over a tarnished crown band; (x, y) = band centre."""
    pts_all = []
    for k, (a0, da, mat, ln) in enumerate(((-150 + sway, -40, CRIM, 3.2), (-95 + sway * 0.5, -25, BLK, 3.4),
                                           (-35 + sway, 45, CRIM, 3.2))):
        pts = chain(x + (k - 1) * 2.0, y - 1.5, [(ln, a0), (ln * 0.9, a0 + da * 0.6), (ln * 0.7, a0 + da * 1.4)])
        tube(c, pts, [2.0, 1.5, 1.0, 0.5], mat, bias=0.1)
        pts_all.append(pts[-1])
    ell(c, x, y - 1.8, 4.6, 2.2, harl(x, y, 3), bias=0.1)
    # crown band with points
    line(c, x - 4.5, y, x + 4.5, y, "e")
    line(c, x - 4, y + 1, x + 4, y + 1, "A")
    for k in (-4, -1.5, 1, 3.5):
        c.put(*P(x + k, y - 1), "z")
    c.put(*P(x - 3, y), "Z"); c.put(*P(x + 1, y), "E")
    for k, (tx, ty) in enumerate(pts_all):
        bell(c, tx, ty, ring=(ring if k != 1 else -ring))


# v0.8: the Grand Jester is the king of fools: a huge round motley belly (gold, crimson, violet and ivory
# quarters), a jewelled fool's crown hung with bells, a violet cape and striped hose. It read as the Ringmaster /
# Marionette again (thin red-and-black figure).
def motley(cx, cy):
    """Quartered motley anchored at raw pixel (cx, cy)."""
    quarters = (GOLD, CRIM, "qnNL", IVORY)

    def f(x, y, l):
        k = (1 if x >= cx else 0) + (2 if y >= cy else 0)
        return pick(quarters[k], l + (0.15 if k == 3 else 0))
    return f


def fool_crown(c, x, y, sway=0.0, ring=0):
    """Jewelled gold crown over a violet cap; bells swing from its two outer points. (x, y) = band centre."""
    ell(c, x, y - 1.6, 4.0, 2.4, "qnNL", bias=0.2)                       # the cap inside the crown
    for k, h in ((-4.5, 4.5), (-2.2, 3.0), (0.2, 5.5), (2.6, 3.0), (4.8, 4.5)):
        tip = (x + k + sway * 0.05 * (h / 5), y - h)
        line(c, x + k, y, *tip, "z")
        c.put(*P(*tip), "Z")
    line(c, x - 5, y, x + 5, y, "e"); line(c, x - 5, y + 1, x + 5, y + 1, "A")
    c.put(*P(x - 2.5, y + 0.5), "E"); c.put(*P(x + 0.2, y + 0.5), "L"); c.put(*P(x + 2.8, y + 0.5), "E")
    for k in (-4.5, 4.8):
        bell(c, x + k + sway * 0.1, y - 4.5 + 1, ring=ring)


def wheel_of_fortune(c, cx, cy, R, ang, alpha=1.0, blur=False, seed=0, segs=8):
    """Wheel of fortune: crimson/black wedges with ivory pips, tarnished gold rim and pegs, spokes, hub."""
    rnd = random.Random(seed)
    for y in range(int(cy - R - 2), int(cy + R + 3)):
        for x in range(int(cx - R - 2), int(cx + R + 3)):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > R + 0.5: continue
            if alpha < 1 and rnd.random() > alpha: continue
            a = (math.degrees(math.atan2(dy, dx)) - ang) % 360
            seg = int(a // (360 / segs))
            la = -(dx + dy) / (R * 1.414) * 0.6
            if d > R - 1.2:
                ch = pick(GOLD, la + 0.2)
            elif d < 1.8:
                ch = pick(GOLD, la + 0.4)
            else:
                edge = (a % (360 / segs)) < (360 / segs) * (0.18 if not blur else 0.0)
                if edge and not blur: ch = "A"
                elif blur: ch = pick("DdKm", (seg % 2) * 0.6 - 0.3 + 0.3 * math.sin(d))
                else: ch = pick(CRIM if seg % 2 == 0 else BLK, la + 0.1)
                if not blur and abs(d - R * 0.62) < 0.6 and abs((a % (360 / segs)) - 360 / segs / 2) < 6:
                    ch = "X" if seg % 2 else "Z"
            c.put(x, y, ch)
    if alpha >= 1:
        for k in range(segs):
            a = math.radians(ang + k * 360 / segs)
            c.put(*P(cx + (R + 1) * math.cos(a), cy + (R + 1) * math.sin(a)), "Z")


def grand_jester(dx=0.0, dy=0.0, lean=0.0, feet=(-4, 4), fh=(9, -19), bh=(1, -19), mask="grin", balls=(),
                 sway=0.0, cape=0.0, ring=0, wheel=None, point=False, extra=None, extra_back=None, over=None,
                 hat=True, knees=(1, 1)):
    c = Canvas()
    if wheel is not None: wheel(c)
    if extra_back: extra_back(c)
    hip = (dx, -15 + dy)
    T = Xf(lean, hip)
    shf, shb = T(hip[0] + 2.8, hip[1] - 10.5), T(hip[0] - 2.6, hip[1] - 10.5)
    neck = T(hip[0] + 0.5, hip[1] - 12)
    # cape behind (black outside, crimson lining)
    cp = [T(hip[0] - 3.5, hip[1] - 11), T(hip[0] + 1, hip[1] - 11.5), (hip[0] - 3 - cape * 0.5, hip[1] + 10),
          (hip[0] - 6 - cape, hip[1] + 11), (hip[0] - 8.5 - cape * 1.3, hip[1] + 9.5)]
    poly(c, cp, CRIM, bias=0.1)                      # v0.9: the Ringmaster's scarlet tailcoat tails
    line(c, *T(hip[0] - 3.5, hip[1] - 10), hip[0] - 8.3 - cape * 1.3, hip[1] + 9, "z")
    # back leg (violet hose)
    (kx, ky), (fx, fy) = ik(hip[0] - 1.2, hip[1], dx + feet[0], -1.5, 7.5, 7.5, knees[0])
    tube(c, [(hip[0] - 1.2, hip[1]), (kx, ky), (fx, fy)], [1.8, 1.4, 1.1], "qnNN")
    _curl_shoe(c, fx, "n", "q")
    # back arm (black sleeve, ivory glove)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 5.5, 5.5, -1)
    tube(c, [shb, (ex, ey)], [1.4, 1.1], BLK)
    tube(c, [(ex, ey), (hx, hy)], [1.1, 0.9], "hwW")
    # torso: harlequin doublet + dagged skirt with bells
    tor = [T(hip[0] - 4.5, hip[1] - 11), T(hip[0] + 4.8, hip[1] - 11), T(hip[0] + 3.2, hip[1] - 1),
           T(hip[0] - 3.2, hip[1] - 1)]
    tcx, tcy = T(hip[0] + 0.2, hip[1] - 6)
    poly(c, tor, harl(tcx - 3.5, tcy, 7, "DEEf", "Kmms", ang=lean), bias=0.25)
    skirt = [T(hip[0] - 3.4, hip[1] - 2), T(hip[0] + 3.6, hip[1] - 2), T(hip[0] + 5, hip[1] + 3.5),
             T(hip[0] + 3, hip[1] + 2.2), T(hip[0] + 1.5, hip[1] + 4), T(hip[0], hip[1] + 2.4), T(hip[0] - 1.5, hip[1] + 4),
             T(hip[0] - 3, hip[1] + 2.2), T(hip[0] - 4.8, hip[1] + 3.5)]
    poly(c, skirt, stripes(hip[0], 2, GOLD, CRIM, ang=lean), bias=0.1)
    # the great motley belly
    bcx, bcy = T(hip[0] + 1.8, hip[1] - 5.8)
    ell(c, bcx, bcy, 6.8, 6.2, motley(*SK.spt(bcx, bcy)), bias=0.15)
    a, b = T(hip[0] - 4.2, hip[1] - 0.8), T(hip[0] + 7.0, hip[1] - 0.8)
    line(c, *a, *b, "e")
    for k in (-3.5, 1.5, 6.5):                         # bells round the belt
        bx, by = T(hip[0] + k, hip[1] + 0.2)
        bell(c, bx, by, ring=ring)
    # v0.9 lineage: the Ringmaster's coiled whip on his hip, and the Marionette's wooden control cross on its strings
    wx, wy = T(hip[0] - 4.2, hip[1] + 1.5)
    for k in range(12):
        a = 2 * math.pi * k / 12
        c.put(*P(wx + 1.6 * math.cos(a), wy + 2.0 * math.sin(a)), "T" if math.cos(a) < 0.3 else "t")
    # v0.10: the Marionette's control cross is gone (the Ringmaster is its only parent): a gold ringmaster's
    # medal hangs there instead
    cx_, cy_ = T(hip[0] + 4.5, hip[1] + 2.5)
    c.put(*P(cx_, cy_ - 1), "E"); c.put(*P(cx_, cy_), "Z"); c.put(*P(cx_ + 1, cy_), "z"); c.put(*P(cx_, cy_ + 1), "e")
    if bh[0] > 3:   # far hand reaching forward shows past the chest
        tube(c, [((ex + hx) / 2, (ey + hy) / 2), (hx, hy)], [1.0, 0.9], "hwW")
    # front leg (crimson hose)
    (kx, ky), (fx, fy) = ik(hip[0] + 1.2, hip[1], dx + feet[1], -1.5, 7.5, 7.5, knees[1])
    tube(c, [(hip[0] + 1.2, hip[1]), (kx, ky), (fx, fy)], [1.9, 1.5, 1.2], stripes(fx, 2, GOLD, CRIM, ang=80))
    _curl_shoe(c, fx, "E", "d", front=True)
    # ruff
    ell(c, neck[0], neck[1] + 0.5, 5.2, 1.9, stripes(neck[0], 1, "hwWX", "hhww"), bias=0.25)
    # head: split mask + hat
    hcx, hcy = neck[0] + 0.5, neck[1] - 1
    c.part(GJ_MASK[mask], *P(hcx, hcy))
    if hat:
        fool_crown(c, hcx, hcy - 8, sway=sway, ring=ring)
    # front arm (crimson sleeve)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 5.5, 5.5, 1)
    tube(c, [shf, (ex, ey)], [1.5, 1.2], CRIM)
    tube(c, [(ex, ey), (hx, hy)], [1.2, 1.0], "wWX")
    if point:
        line(c, hx, hy, hx + 2, hy - 0.5, "X")
    for (bx, by, ph) in balls:
        juggle_ball(c, bx + dx, by + dy, ph)
    if extra: extra(c)
    return finish(c, over)


def _curl_shoe(c, fx, col, dark, front=False):
    c.put(*P(fx - 1, 0), dark); c.put(*P(fx, 0), col); c.put(*P(fx + 1, 0), col); c.put(*P(fx + 2, -1), col)
    c.put(*P(fx + 3, -2), col); c.put(*P(fx + 2, -3), "z" if front else "e")
    c.put(*P(fx, -1), dark)


def juggle_positions(t, lo=(7, -20), hi=(13, -21), peak=-36):
    """Three-ball cascade: ball i at phase t + i/3. Returns [(x, y, ph)]."""
    out = []
    for i in range(3):
        p = (t + i / 3.0) % 1.0
        if p < 0.6:
            u = p / 0.6
            x = lo[0] + (hi[0] - lo[0]) * u if i % 2 == 0 else hi[0] + (lo[0] - hi[0]) * u
            y = lo[1] - (lo[1] - peak) * math.sin(math.pi * u)
        else:
            u = (p - 0.6) / 0.4
            x = hi[0] + (lo[0] - hi[0]) * u if i % 2 == 0 else lo[0] + (hi[0] - lo[0]) * u
            y = lo[1] + 1.5 * math.sin(math.pi * u)
        out.append((x, y, i * 2 + int(t * 8)))
    return out


def build_grand_jester(outdir):
    G = grand_jester
    idle = []
    for i in range(4):
        t = i / 4.0
        bs = juggle_positions(t)
        up = i % 2
        idle.append(G(fh=(13, -20 - 2 * up), bh=(7, -21 + 2 * up), balls=bs, sway=[0, 3, 5, 2][i], ring=[0, 1, 0, -1][i],
                      dy=[0, 0.4, 0.4, 0][i], cape=[0, 0.5, 1, 0.5][i]))
    stride = [(-8, 6), (-5, 3), (-1, 0), (6, -8), (3, -5), (0, -1)]
    run = [G(feet=stride[i], lean=7, dy=[0, -1, 0, 0, -1, 0][i], cape=[3, 4, 3.5, 3, 4, 3.5][i], sway=-8,
             fh=(10, -18 + (i % 3)), bh=(-3 + (i % 3), -17), ring=[1, -1, 0, 1, -1, 0][i],
             balls=[(11 + (i % 2), -30 - (i % 3), i)]) for i in range(6)]
    # Juggle: juggle higher (2 wind-ups), hurl one ball per frame (release 3, 4, 5), follow-through, recover
    hi_ = lambda t: juggle_positions(t, peak=-38)
    jug = [G(fh=(12, -21), bh=(5, -19), balls=hi_(0.1), lean=-4, mask="glare"),
           G(fh=(11, -19), bh=(5, -22), balls=hi_(0.35), lean=-7, mask="glare", sway=4),
           G(fh=(12, -25), bh=(4, -20), balls=[(8, -38, 0), (13, -41, 2), (5, -35, 4)], lean=-2, mask="laugh", sway=2),
           G(fh=(14, -24), bh=(3, -21), balls=[(18, -25, 1), (12, -37, 2), (6, -33, 4)], lean=8, mask="laugh", cape=2,
             extra_back=lambda c: speed_lines(c, 8, 14, (-25,), "w")),
           G(fh=(14, -27), bh=(4, -21), balls=[(19, -29, 3), (8, -31, 5)], lean=10, mask="laugh", cape=2.5,
             extra_back=lambda c: speed_lines(c, 9, 15, (-29,), "w")),
           G(fh=(14, -22), bh=(1, -20), balls=[(18, -23, 6)], lean=12, mask="laugh", cape=3,
             extra_back=lambda c: speed_lines(c, 8, 14, (-23,), "w")),
           G(fh=(13, -17), bh=(1, -18), lean=10, mask="grin", cape=2),
           G(fh=(12, -19), bh=(5, -20), lean=2, mask="grin", balls=juggle_positions(0.0)[:1])]
    # Wheel: arms spread (wind-up), the wheel conjures (1), spins behind him (2-7), he POINTS (8), fades (9)
    wc = (-3, -27)
    wheel_a = [G(fh=(10, -26), bh=(-8, -26), lean=-4, mask="glare", sway=-3)]
    wheel_a.append(G(fh=(11, -28), bh=(-9, -28), lean=-6, mask="laugh", sway=-5,
                     wheel=lambda c: wheel_of_fortune(c, *wc, 15, 0, alpha=0.45, seed=1)))
    for k in range(6):
        wheel_a.append(G(fh=(11, -28 + (k % 2)), bh=(-9, -28 + (k % 2)), lean=-5, mask="laugh", sway=[-5, 5][k % 2],
                         ring=[1, -1][k % 2], wheel=(lambda kk: lambda c: wheel_of_fortune(c, *wc, 15, kk * 34 + 10,
                                                                                         blur=(1 <= kk <= 4)))(k)))
    wheel_a.append(G(fh=(14, -22), bh=(-6, -18), lean=8, mask="glare", point=True, sway=2,
                     wheel=lambda c: [wheel_of_fortune(c, *wc, 15, 22.5),
                                      [c.put(wc[0] + dx_, wc[1] - 17 + dy_, ch) for dx_, dy_, ch in
                                       ((0, 0, "Z"), (-1, -1, "z"), (1, -1, "z"), (0, -1, "y"))]]))
    wheel_a.append(G(fh=(10, -19), bh=(0, -19), lean=2, mask="grin",
                     wheel=lambda c: wheel_of_fortune(c, *wc, 15, 22.5, alpha=0.3, seed=4)))
    d0 = G(fh=(6, -27), bh=(-8, -27), lean=-14, mask="glare", feet=(-6, 4), cape=-2, sway=-10, ring=1,
           extra=lambda c: [juggle_ball(c, 13, -6), juggle_ball(c, -10, -3, 3)])
    d1 = G(fh=(9, -12), bh=(-6, -12), lean=-8, dy=6, mask="dead", feet=(-7, 7), sway=12, cape=-2)
    d2 = grounded(rot_spr(G(fh=(8, -16), bh=(-2, -17), mask="dead", sway=8, feet=(-3, 3)), -60, (0, -1)))
    corpse = gj_corpse()
    knock = G(fh=(6, -29), bh=(-9, -27), lean=-16, dx=-1.5, mask="glare", feet=(-3, 6), cape=-3, sway=-14, ring=1)
    anims = [("Idle", idle, [0.15] * 4), ("Run", run, [0.09] * 6),
             ("Juggle", jug, [0.14, 0.14, 0.1, 0.06, 0.06, 0.06, 0.14, 0.16]),
             ("Wheel", wheel_a, [0.14, 0.12, 0.08, 0.08, 0.08, 0.08, 0.1, 0.14, 0.24, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.12, 0.16, 0.16, 0.5], knock)
    return sheet("JinxGrandJester", anims, outdir, scale=4)


def gj_corpse():
    body = grand_jester(fh=(7, -14), bh=(-2, -15), mask="dead", sway=10, feet=(-2, 2), hat=True)
    lying = grounded(rot_spr(body, -90, (0, -1)))
    c = Canvas(); c.px = dict(lying.px)
    o = Canvas()
    juggle_ball(o, 16, -2, 2); juggle_ball(o, -19, -2, 5)
    return grounded(floor_cut(merge(Spr(c.px), finish(o))))


# ================================================================== FX
SUITS = {
    "Hearts": ("""
.XX.XX.
XXXXXXX
XXXXXXX
.XXXXX.
..XXX..
...X...
""", "red"),
    "Diamonds": ("""
...X...
..XXX..
.XXXXX.
XXXXXXX
.XXXXX.
..XXX..
...X...
""", "red"),
    "Spades": ("""
...X...
..XXX..
.XXXXX.
XXXXXXX
XXXXXXX
.X.X.X.
..XXX..
""", "black"),
    "Clubs": ("""
..XXX..
..XXX..
XX.X.XX
XXXXXXX
XX.X.XX
...X...
..XXX..
""", "black"),
}


def glyph(c, text, x, y, kind):
    rows = [r for r in text.strip("\n").split("\n")]
    h, w = len(rows), len(rows[0])
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != "X": continue
            if kind == "red":
                col = "f" if (i + j) < 3 else ("D" if (i > w - 2 or j == h - 1) else "E")
            else:
                col = "s" if (i + j) < 3 else "K" if (i > w - 2 or j == h - 1) else "m"
            c.put(x + i - w // 2, y + j - h // 2, col)


def card_face(c, cx, cy, w, h, kind="back", sx=1.0, ang=0.0, glow=False):
    """Playing card centred at (cx, cy); sx squashes its width (flip), ang rotates it in-plane.
    kind: back | joker | Hearts | Diamonds | Spades | Clubs."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    hw, hh = max(0.5, w * sx / 2.0), h / 2.0
    tf = lambda x, y: (cx + x * ca - y * sa, cy + x * sa + y * ca)
    outer = [tf(-hw, -hh), tf(hw, -hh), tf(hw, hh), tf(-hw, hh)]
    if kind == "back":
        poly(c, outer, "wwWW", lit="flat", bias=0.2)
        if hw > 1.4:
            inner = [tf(-hw + 1, -hh + 1), tf(hw - 1, -hh + 1), tf(hw - 1, hh - 1), tf(-hw + 1, hh - 1)]
            poly(c, inner, harl(cx, cy, 3, "DDEE", "KKmm", ang=ang), lit="flat", bias=0.2)
            c.put(*P(cx, cy), "z")
        return
    poly(c, outer, "WXXX", lit="flat", bias=0.3)
    # shade the right and bottom edge of the face
    line(c, *outer[1], *outer[2], "W"); line(c, *outer[2], *outer[3], "W")
    if sx < 0.7 or ang != 0:
        if hw > 1: c.put(*P(cx, cy), "E")
        return
    ix, iy = int(round(cx)), int(round(cy))
    if kind == "joker":
        # tiny grinning jester head with a two-point cap
        for x, y, ch in ((-2, -3, "E"), (-3, -4, "E"), (2, -3, "m"), (3, -4, "K"), (-1, -2, "E"), (0, -2, "m"),
                         (1, -2, "K"), (-4, -5, "z"), (4, -5, "z")):
            c.put(ix + x, iy + y, ch)
        for x, y, ch in ((-1, -1, "K"), (1, -1, "K"), (-2, 1, "K"), (-1, 2, "K"), (0, 2, "K"), (1, 2, "K"),
                         (2, 1, "K"), (-1, 1, "W"), (0, 1, "W"), (1, 1, "W")):
            c.put(ix + x, iy + y, ch)
        c.put(ix - int(hw) + 1, iy - int(hh) + 1, "E"); c.put(ix + int(hw) - 1, iy + int(hh) - 1, "K")
    else:
        text, col = SUITS[kind]
        glyph(c, text, ix, iy, col)
        pc = "E" if col == "red" else "K"
        c.put(ix - int(hw) + 1, iy - int(hh) + 1, pc); c.put(ix + int(hw) - 1, iy + int(hh) - 1, pc)
    if glow:
        for k in range(4):
            a = math.radians(45 + 90 * k)
            c.put(*P(cx + (hw + 2) * math.cos(a) * 1.2, cy + (hh + 1) * math.sin(a)), "L")


def fx_card_frames():
    out = []
    for i in range(4):
        c = Canvas()
        card_face(c, 0, -5, 6, 8, "back", ang=i * 45 - 10)
        o = Canvas()
        for k, (x, y) in enumerate(((-7, -5 + (i % 2)), (-9, -4), (-6, -2 - (i % 2)))):
            o.put(x, y, "s" if k else "w")
        out.append(merge(outline(c.spr()), o.spr()))
    return out


def fx_die_frames():
    out = []
    for i in range(4):
        c = Canvas()
        die(c, 0, -4, 6, i * 22.5, 30, i * 10)
        o = Canvas()
        o.put(-6, -4 + (i % 2), "w"); o.put(-8, -4, "s"); o.put(-7, -2, "s")
        out.append(merge(outline(c.spr()), o.spr()))
    return out


def fx_die_face_frames():
    out = []
    poses = [(0, -15, (40, 25, 20), False, 0), (0, -6, (8, 10, 4), False, 2), (1, -8, (-6, 175, -4), False, 0),
             (0, -6, (0, 180, 0), False, 1), (0, -6, (0, 180, 0), True, 0), (0, -6, (0, 180, 0), False, 0)]
    for i, (x, y, rot, glow, dust) in enumerate(poses):
        c = Canvas()
        die(c, x, y, 9, *rot, big_pips=False, glow="L" if glow else None)
        sp = outline(c.spr())
        o = Canvas()
        if dust:
            for dx_, dy_ in ((-7, 0), (-8, -1), (7, 0), (8, -1), (-6, -1), (6, -1), (-9, 0), (9, 0)):
                if dust > 1 or abs(dx_) < 8: o.put(dx_, dy_, "S" if dx_ % 2 else "s")
        if glow:
            for k in range(6):
                a = math.radians(k * 60 + 15)
                o.put(*P(x + 9 * math.cos(a), y - 1 + 7 * math.sin(a)), "L" if k % 2 else "N")
        if i == 5:
            o.put(x + 6, y - 9, "N"); o.put(x - 6, y - 8, "n")
        out.append(floor_cut(merge(sp, o.spr())))
    return out


def fx_hoop_frames():
    out = []
    for i, rx in enumerate((8.0, 5.0, 1.5, 5.0)):
        c = Canvas()
        flaming_hoop(c, 0, -9, rx, fire=2, ry=8.0, phase=i)
        out.append(c.spr())
    return out


def fx_ball_frames():
    out = []
    for i in range(4):
        c = Canvas()
        o = Canvas()
        for k in range(3):
            o.put(-4 - k * 2, -3 + (k + i) % 2 - 0, "w" if k == 0 else "s")
        juggle_ball(c, 0, -3, ph=i, r=2.4)
        out.append(merge(o.spr(), c.spr()))
    return out


def fx_wild_card_frames():
    spin = [(1.0, "back", -8), (0.5, "back", -10), (0.12, "back", -11), (0.5, "joker", -12)]
    out = []
    for sx, kind, y in spin:
        c = Canvas()
        card_face(c, 0, y, 10, 14, kind, sx=sx)
        o = Canvas()
        if sx < 0.6:
            for k in (-1, 1):
                o.put(*P(k * 6, y - 3), "N"); o.put(*P(k * 5, y + 4), "n")
        out.append(merge(outline(c.spr()), o.spr()))
    for k in range(4):
        c = Canvas()
        card_face(c, 0, -12, 10, 14, "joker", glow=(k in (0, 2)))
        sp = outline(c.spr())
        o = Canvas()
        r = random.Random(k)
        for j in range(3 + 2 * (k < 2)):
            o.put(r.randint(-7, 7), r.randint(-21, -3), "L" if j % 2 else "Z")
        sp = merge(sp, o.spr())
        if k == 3:
            sp = card_burst(-12, 10, 14, 5, frag=("X", "W", "E"), spark=("Z", "L"))   # v0.10: a drawn burst
        out.append(sp)
    suits = {}
    for name in ("Hearts", "Spades", "Diamonds", "Clubs"):
        c = Canvas()
        card_face(c, 0, -12, 10, 14, name)
        sp = outline(c.spr())
        o = Canvas()
        for x, y in ((-7, -19), (7, -6), (6, -20)):
            o.put(x, y, "Z" if name in ("Hearts", "Diamonds") else "L")
        suits[name] = merge(sp, o.spr())
    return out, suits


def fx_confetti_frames():
    out = []
    r0 = random.Random(11)
    bits = [(r0.uniform(-math.pi, 0.3), r0.uniform(0.5, 1.0), "fEZzXLNy"[k % 8], r0.random()) for k in range(26)]
    radius = [2, 6, 9, 11, 12, 12.5]
    fall = [0, 0, 1, 3, 6, 9]
    smoke_r = [2.5, 5.0, 6.0, 6.5, 6.0, 0]
    smoke_keep = [1, 1, 0.8, 0.5, 0.25, 0]
    for i in range(6):
        c = Canvas()
        if smoke_r[i]:
            sc = Canvas()
            for j, (bx, by) in enumerate(((0, 0), (-0.5, -0.3), (0.5, -0.3), (0, -0.6), (-0.6, 0.2), (0.6, 0.2))):
                R = smoke_r[i] * (1 if j == 0 else 0.6)
                ell(sc, bx * smoke_r[i], -9 + by * smoke_r[i] - i * 0.5, R, R * 0.85, SMOKE, bias=0.1)
            ss = sc.spr()
            if smoke_keep[i] < 1: ss = dissolve(ss, smoke_keep[i], i)
            c.px.update(ss.px)
        if i == 0:
            sparkle(c, 0, -9, 2, "Z", "y")
        else:
            for a, d, col, t in bits:
                rr = radius[i] * d
                x, y = rr * math.cos(a) * 1.1, -9 + rr * math.sin(a) * 0.8 + fall[i] * (0.6 + t * 0.6)
                if y > 0: y = 0
                c.put(*P(x, y), col)
                if (i + int(t * 4)) % 2 == 0: c.put(*P(x + 1, y), col)
        out.append(floor_cut(c.spr()))
    return out


def fx_wheel_frames():
    out = []
    cx, cy, R = 0, -17, 12
    angs = [0, 30, 75, 125, 170, 205, 222.5, 222.5]
    for i in range(8):
        c = Canvas()
        # stand
        line(c, -4, 0, 0, cy + 3, "t"); line(c, 4, 0, 0, cy + 3, "T"); line(c, -5, 0, 5, 0, "k")
        if i == 0:
            # v0.10: the wheel conjures as a ring of gold sparks round its hub (was a random-pixel half wheel)
            for k in range(16):
                a = math.radians(k * 22.5)
                c.put(*P(cx + R * math.cos(a), cy + R * math.sin(a)), "Z" if k % 2 else "z")
                if k % 4 == 0:
                    c.put(*P(cx + (R + 1.5) * math.cos(a), cy + (R + 1.5) * math.sin(a)), "y")
                    c.put(*P(cx + (R - 3) * math.cos(a), cy + (R - 3) * math.sin(a)), "L")
            ell(c, cx, cy, 2.0, 2.0, GOLD, bias=0.3)
        else:
            wheel_of_fortune(c, cx, cy, R, angs[i], alpha=1.0, blur=(2 <= i <= 4), seed=i)
        # pointer at the top
        for x, y, ch in ((0, cy - R - 1, "Z"), (-1, cy - R - 2, "z"), (1, cy - R - 2, "z"), (0, cy - R - 2, "y" if i == 7 else "Z"),
                         (0, cy - R - 3, "e")):
            c.put(x, y, ch)
        sp = outline(c.spr())
        if i == 7:
            o = Canvas()
            for k in range(8):
                a = math.radians(k * 45 + 22)
                o.put(*P(cx + (R + 3) * math.cos(a), cy + (R + 3) * math.sin(a)), "L" if k % 2 else "Z")
            sp = merge(sp, o.spr())
        out.append(floor_cut(sp))
    return out


def knife(c, x, y, ang, sunk=0):
    """Throwing knife; (x, y) = tip; ang = direction the tip points (90 = down). sunk px hide in the floor."""
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    back = lambda d: (x - ux * d, y - uy * d)
    tube(c, [back(0.5), back(6.5)], [0.4, 1.0], "SUuc", bias=0.2)
    line(c, *back(1), *back(6), "c")
    g = back(7)
    c.put(*P(g[0] - uy * 1.5, g[1] + ux * 1.5), "z"); c.put(*P(*g), "e"); c.put(*P(g[0] + uy * 1.5, g[1] - ux * 1.5), "z")
    line(c, *back(8), *back(9.5), "D")
    c.put(*P(*back(10.5)), "Z")


def fx_knife_frames():
    out = []
    specs = [(0, -16, -60, 0), (1, -11, 30, 0), (0, -2, 90, 0), (0, 2, 90, 1), (0, 2, 84, 0), (0, 2, 90, 0)]
    for i, (x, y, ang, spark) in enumerate(specs):
        c = Canvas()
        knife(c, x, y, ang)
        sp = outline(c.spr())
        o = Canvas()
        if i < 2:
            o.put(x - 2, y - 7, "s"); o.put(x + 2, y - 9, "s")
        if spark:
            sparkle(o, 0, -1, 2, "Y", "y")
            for dx_ in (-3, 3, -4, 4): o.put(dx_, 0, "S")
        if i == 4:
            o.put(-2, -9, "w"); o.put(2, -8, "w")
        out.append(floor_cut(merge(sp, o.spr())))
    return out


def build_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxCard"): fx_sheet("FxCard", [("Fly", fx_card_frames(), [0.05] * 4)], outdir)
    if want("FxDie"): fx_sheet("FxDie", [("Fly", fx_die_frames(), [0.06] * 4)], outdir)
    if want("FxDieFace"): fx_sheet("FxDieFace", [("Play", fx_die_face_frames(), [0.06, 0.05, 0.06, 0.1, 0.2, 0.2])], outdir)
    if want("FxHoop"): fx_sheet("FxHoop", [("Fly", fx_hoop_frames(), [0.06] * 4)], outdir)
    if want("FxJuggleBall"): fx_sheet("FxJuggleBall", [("Fly", fx_ball_frames(), [0.06] * 4)], outdir)
    if want("FxWildCard"):
        play, suits = fx_wild_card_frames()
        fx_sheet("FxWildCard", [("Play", play, [0.06, 0.05, 0.05, 0.06, 0.12, 0.14, 0.14, 0.12])] +
                 [(n, [suits[n]], [0.5]) for n in ("Hearts", "Spades", "Diamonds", "Clubs")], outdir)
    if want("FxConfetti"): fx_sheet("FxConfetti", [("Play", fx_confetti_frames(), [0.05, 0.07, 0.08, 0.1, 0.12, 0.14])], outdir)
    if want("FxWheel"): fx_sheet("FxWheel", [("Play", fx_wheel_frames(), [0.1, 0.07, 0.06, 0.06, 0.07, 0.12, 0.25, 0.2])], outdir)
    if want("FxKnifeRain"): fx_sheet("FxKnifeRain", [("Play", fx_knife_frames(), [0.06, 0.06, 0.05, 0.08, 0.1, 0.3])], outdir)


FX_NAMES = ["FxCard", "FxDie", "FxDieFace", "FxHoop", "FxJuggleBall", "FxWildCard", "FxConfetti", "FxWheel", "FxKnifeRain"]


# ================================================================== ICONS + GOD PORTRAIT
def clip16(c):
    return Spr({k: v for k, v in c.px.items() if -7 <= k[0] <= 6 and -14 <= k[1] <= -1})


def icon_wild_card(ph):
    c = Canvas()
    card_face(c, 1, -8, 8, 11, "back", ang=-14)
    card_face(c, -1, -7, 8, 11, "joker", ang=0)
    sp = outline(clip16(c))
    if ph:
        sp = merge(sp, Spr({(3, -12): "y", (4, -12): "Z", (3, -13): "Z", (2, -12): "Z", (3, -11): "Z"}))
    return sp


def icon_loaded_dice(ph):
    c = Canvas()
    die(c, -2, -5, 6, 0, 30, 0)
    die(c, 3, -9, 5, 20, -25, 12, glow="L" if ph else None)
    sp = outline(clip16(c))
    if ph:
        sp = merge(sp, Spr({(-4, -10): "L", (-5, -11): "N", (5, -14): "Z"}))
    return sp


def icon_bell(ph):
    c = Canvas()
    sw = 1 if ph else 0
    # crimson ribbon bow on top
    for x, y, ch in ((-2, -13, "D"), (-3, -14, "E"), (2, -13, "D"), (3, -14, "E"), (0, -13, "f"), (-1, -13, "E"), (1, -13, "E")):
        c.put(x, y, ch)
    ell(c, 0 + sw * 0.5, -6.5, 5.2, 5.0, GOLD, bias=0.15)
    line(c, -4 + sw, -5, 4 + sw, -5, "A")         # rim band
    c.put(-3 + sw, -9, "Z"); c.put(-2 + sw, -10, "Z")
    # slot + clapper ball
    line(c, -2 + sw, -3, 2 + sw, -3, "K"); c.put(-3 + sw, -4, "K"); c.put(3 + sw, -4, "K")
    c.put(0 + sw, -2, "k"); c.put(sw, -1, "A")
    sp = outline(clip16(c))
    if ph:
        sp = merge(sp, Spr({(-6, -9): "z", (6, -10): "z", (-7, -7): "e"}))
    return sp


def icon_cross(ph):
    c = Canvas()
    tube(c, [(-6, -10), (6, -10)], [1.0, 1.0], WOOD, bias=0.2)
    tube(c, [(0, -14), (0, -4)], [1.0, 1.0], WOOD, bias=0.2)
    for x, y in ((-6, -10), (6, -10), (0, -14), (0, -4)):
        c.put(x, y, "z")
    sp = outline(clip16(c))
    o = Canvas()
    for k, (x, y0) in enumerate(((-6, -9), (6, -9), (0, -3))):
        sway = (1 if ph else 0) * (1 if k % 2 else -1)
        for y in range(y0 + 1, 0):
            o.put(x + (sway if y > -3 else 0), y, "S" if (y + k) % 3 else "w")
    o.put(-2, -11, "E"); o.put(2, -11, "E")
    return merge(sp, o.spr())


def build_icons(outdir):
    for name, fn in (("IconWildCard", icon_wild_card), ("IconLoadedDice", icon_loaded_dice),
                     ("IconJestersBell", icon_bell), ("IconMarionetteCross", icon_cross)):
        frames = [fn(0), fn(1)]
        # first drafts only: the shipped item icons are art/out_icons_v2 (tools/sprites/items_v2_icons.py). Kept out
        # of art/out* so the flat deploy folder never gets a second, different sheet with the same id.
        idir = os.path.join(os.path.dirname(os.path.dirname(HERE_DIR)), "art", "raw", "icon_drafts")
        img, man = pack(name, [("Idle", frames, [0.6, 0.25])], 16, 16, (8, 15), idir)
        preview(img, man, os.path.join(idir, name + "_preview.png"), scale=10)
        BUILT[name] = {"cell": (16, 16), "feet": (8, 15), "anims": [("Idle", 2, [0.6, 0.25])], "img": img, "man": man}
        print("built", name)


ICON_NAMES = ["IconWildCard", "IconLoadedDice", "IconJestersBell", "IconMarionetteCross"]


# ================================================================== TIMING.md
EVENTS = {
    "JinxJackBox": {"Punch": [("glove hit (long reach)", 3)],
                    "PunchUp": [("glove hit straight up (glove at (-1, -24))", 3)],
                    "PunchDown": [("head slams the floor beside the box (at (8, 0))", 3)],
                    "Pop": [("starts ducking in", 1), ("lid shut: invulnerable, TELEPORT here", 4), ("springs out at new spot", 5)]},
    "JinxJackMinion": {"Punch": [("headbutt hit (head at (7, -9))", 3)],
                       "PunchUp": [("headbutt straight up (head at (0, -19))", 3)],
                       "PunchDown": [("topples, head bonks the floor at (9, -1)", 3)]},
    "JinxCardSharp": {"Deal": [("card release (spawn FxCard)", 3)],
                      "Shuffle": [("swap moment", 3), ("bow", 6)]},
    "JinxDiceImp": {"Toss": [("die release (spawn FxDie)", 3)],
                    "Roll": [("spin starts", 1), ("slam: die shows a face (spawn FxDieFace)", 6)]},
    "JinxRingmaster": {"Whip": [("crack hit", 3)], "Hoop": [("hoop release (spawn FxHoop)", 4)]},
    "JinxMarionette": {"Lash": [("slash hit", 3)],
                       "Strings": [("strings shoot out (hit/latch)", 3), ("pull starts", 5), ("pull peak", 6)]},
    "JinxGrandJester": {"Juggle": [("ball 1 release (FxJuggleBall)", 3), ("ball 2 release", 4), ("ball 3 release", 5)],
                        "Wheel": [("wheel appears", 1), ("spin starts", 2), ("spin ends", 7), ("points: resolve the wheel", 8)]},
}
FX_NOTES = {
    "FxCard": "Fly loop, faces right (spinning card back, small trail on the left).",
    "FxDie": "Fly loop, faces right (tumbling die).",
    "FxDieFace": "Play once: falls 0, hits the floor 1 (impact frame), bounce 2, settles face-out 3, pips glow 4, hold 5.",
    "FxHoop": "Fly loop: flaming hoop spinning about its vertical axis (edge-on on frame 2). Hoop centre is 9 px above the origin.",
    "FxJuggleBall": "Fly loop, faces right.",
    "FxWildCard": "Play: 0-3 the card flips up above the monster (spin), 4-7 joker face with sparkles, fades on 7. "
                  "Card centre is 12 px above the origin, so place the origin just over the monster's head. To show the "
                  "dealt boon, play frames 0-3 then show the 1-frame anim Hearts / Spades / Diamonds / Clubs "
                  "(heal / damage surge / block plate / speed burst).",
    "FxConfetti": "Play once: pop flash 0, burst 1 (spawn moment), confetti falls and smoke thins 2-5.",
    "FxWheel": "Play once: appears 0, spins 1-5 (blurred 2-4), stops 6 (result frame), pointer flash 7. Wheel centre 17 px up.",
    "FxKnifeRain": "Play once: knife spins down 0-1, plunges 2, sticks in the floor 3 (hit frame, spark), quivers 4, rests 5.",
}


def write_timing(outdir):
    L = ["# Jinx, the Grinning Jester: sprite timing", "",
         "Generated by `tools/sprites/jinx_rigs.py`. Frame indices are 0-based within the anim.",
         "Every monster sheet uses feet = (cellW/2, cellH-2), monsters face right. FX sheets use the fx.py centre point "
         "(origin = effect centre on the ground) listed below. Times are seconds from the start of the anim to the start "
         "of that frame.", "",
         SK.SCALE_NOTE, "",
         "## Monster sheets", "", "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h from feet) | Design scale | Anims (frames) |",
         "|---|---|---|---|---|---|"]
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        ib = SK.idle_bounds(b["img"], b["man"])
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %.2f | %s |" % (n, cw, ch, cw // 2, ch - 2, ib[0], ib[1],
                 SCALE.get(n, 1.0), ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
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
    L += ["", "Every attack has at least two wind-up frames before its first event frame. Strike frames are 0.05-0.08 s.",
          "Wild Card perk: flip FxWildCard above the monster on the special's first event frame (Pop 4, Shuffle 3, Roll 6, "
          "Hoop 4, Strings 3, Wheel 8).",
          "The Marionette hangs on strings that run to the top of its cell; its toes clear the floor by 1-2 px on purpose.",
          "The Dice Imp flies: its die hovers ~1 px above the feet point (lowered from 3.3 px for the size limit).",
          "JinxJackMinion is the fodder-sized jack (same anims/frames/durations as JinxJackBox) for the JackMinion def.",
          "Death plays once and ends on the corpse; Dead is that same corpse frame.", "",
          "## FX sheets", "", "| Sheet | Cell (w x h) | Centre | Anims (frames, total s) | Notes |", "|---|---|---|---|---|"]
    for n in FX_NAMES:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"]), FX_NOTES[n]))
    L += ["", "## Icons", "", "| Sheet | Cell | Feet | Anims |", "|---|---|---|---|"]
    for n in ICON_NAMES:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## v0.8 redraws (art pass)", "",
          "- JinxRingmaster: a stout showman: scarlet tailcoat, gold-buttoned waistcoat over a round belly, white riding "
          "breeches, black boots, handlebar moustache; hands, whip and hoop points unchanged (kit offsets unchanged).",
          "- JinxMarionette: a carved wooden doll on brass ball joints, painted barrel body, wooden face with a painted "
          "cheek, strings running up to a wooden control cross; hand and string points unchanged.",
          "- JinxGrandJester: king of fools: round quartered motley belly (gold / crimson / violet / ivory) with belt bells, "
          "jewelled fool's crown with bells, violet cape, striped hose. Hands unchanged; the crown top is 2 design px "
          "lower than the old hat, so the Wheel spawns at offsetY 44 (was 46).",
          "- JinxRingmaster and JinxPuppeteer: blacks lifted a step with a lit top-left edge (Idle mean 56 -> 85, 60 -> 74).",
          "- Death is 4 frames on JinxJackBox, JinxJackMinion, JinxCardSharp and JinxDiceImp (a new frame 2).",
          "- JinxBandit Jackpot frame 6 is its own frame (the first reel stops on a cherry); FxCoin frame 3 is unique."]
    L += ["", "## v0.10 (final art review)", "",
          "- JinxJackBox redrawn pixel by pixel at final size (no ArtScale entry): crimson crank box with a gold harlequin "
          "diamond, crank on the side, lid flapped back, jester head on a gold spring. Punch frame 3: the glove lands at "
          "(16, -11); JackKit hitbox 14 x 10 at (12, 10), node 7. Pop events unchanged (1 duck, 4 shut/teleport, 5 out).",
          "- JinxJackMinion (Loose Jack) has its own silhouette at final size: a bare spring standing on a splintered lid "
          "board with the jester head on top; Punch is a headbutt landing at (7, -9) on frame 3 (hitbox 12 x 10 at (8, 9), "
          "node 7). Anims: Idle 4, Run 6, Punch 7, Death 4 (no Pop: its kit has no special).",
          "- v0.10 sweep: both jacks have PunchUp / PunchDown (7 frames, same timings, hit frame 3), played through "
          "AttackData.m_animAngles when they aim within 40 degrees of straight up / down (AimedMelee.Angles). Their punch "
          "hitboxes rotate with the aim (AimedMelee.Rotating): Jack 16 x 10 along the aim at (12, 10), down nudge (5, 0); "
          "Loose Jack 13 x 10 at (8, 9), down nudge (5, 0). Cells grew to 42 x 30 / 36 x 26 (feet still cellW/2, cellH-2).",
          "- FxWheel Play 0 (a ring of gold sparks conjuring), FxTarot frame 3 and FxWildCard Play 7 (the card bursts into "
          "four fragments and sparkles) are drawn frames (were random-pixel dissolves)."]
    L += ["", "## v0.9 lineage motifs (each evolution carries its parents' signature features)", ""] + ["- " + t for t in ["JinxRingmaster (Jack-in-the-Box): the Jack's ivory grin + gold harlequin flecks on the coat tails", "JinxMarionette (Jack + Card Sharp): a gold Jack spring for a knee + the Card Sharp's green visor and a painted card on the chest", "JinxFortuneTeller (Card Sharp + Dice Imp): the green dealer visor + the imp's ivory horns and a die earring", "JinxSnakeEyes (Dice Imp): the imp's ivory horns", 'JinxGrandJester (Ringmaster + Marionette): scarlet tailcoat tails and a coiled whip at the hip + a wooden control cross on strings', "JinxChimera (Ringmaster + Snake-Eyes): the serpent tail + the Ringmaster's top hat cocked on the mane", 'JinxPuppeteer (Marionette + Fortune Teller): wooden-doll puppets + a plum robe with stitched stars and a crystal ball at the belt', 'JinxBandit (Fortune Teller + Snake-Eyes): the knob is a crystal ball + the lever is a crimson-and-black serpent']]
    import godsb_fx
    L += ["", "## v0.10 tree (3 -> 6 -> 12, one parent each): lineage motifs", "", "Tree: JackInTheBox -> Ringmaster, "
          "Marionette; CardSharp -> FortuneTeller, CardSoldier; DiceImp -> SnakeEyes, LoadedDie; Ringmaster -> Chimera, "
          "GrandJester; Marionette -> Puppeteer, Nutcracker; FortuneTeller -> Oracle, Bandit; SnakeEyes -> Gorgon, Rattler; "
          "CardSoldier -> CardKing, HouseOfCards; LoadedDie -> HighRoller, Twenty. The v0.9 two-parent notes above are "
          "superseded.", ""] + ["- " + t for t in L10]
    L += godsb_fx.timing_section("jinx")
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(outdir, "TIMING.md"))


# ================================================================== design scale (v0.7 size pass)
SK.install(sys.modules[__name__], {
    "ell": (["x", "x", "e", "e", "m"], {"mat": "m"}),
    "tube": (["P", "R", "m"], {"mat": "m"}),
    "line": (["x", "x", "x", "x"], {}),
    "poly": (["P", "m"], {"mat": "m"}),
})
# linear factor each monster sheet is rendered at (1.0 = authored size); see src/CrawlFurther/SheetScales.cs
# v0.10: JinxJackBox and JinxJackMinion are drawn at final size (no entry; removed from ArtScale.cs too)
# v0.10: JinxDiceImp redrawn at final size too (build_dice_imp10; no entry)
SCALE = {"JinxCardSharp": 0.75, "JinxRingmaster": 0.7,
         "JinxMarionette": 0.65, "JinxGrandJester": 0.78}
PART_SCALE = {}

# hand-drawn small heads (carving a 7 px face down to 4 px loses the eyes)
for _sc in (0.42, 0.55, 0.6):
    SK.subst(JACK_FACE["grin"], _sc, """
.hXX.
hKXKX
hXXXX
KXKXK
.KKK.
""", (2, 4))
    SK.subst(JACK_FACE["wide"], _sc, """
.hXX.
hKXKX
KXXXK
KKEKK
.KKK.
""", (2, 4))
    SK.subst(JACK_FACE["squint"], _sc, """
.hXX.
KKXKK
hXXXX
KXKXK
.KKK.
""", (2, 4))
    SK.subst(JACK_FACE["dead"], _sc, """
.hXX.
hKwKX
hXXXX
hwKKX
.hww.
""", (2, 4))
SK.subst(SHARP_HEAD["grin"], 0.75, """
...HMMMM.
Q.HHHHHHM
.QjjjKYj.
..QIjjjjI
..KXKXKK.
...QIIQ..
""", (4, 5))
SK.subst(SHARP_HEAD["leer"], 0.75, """
...HMMMM.
Q.HHHHHHM
.QjjKKYj.
..QIjjjjI
..KXKXKXK
...KKKQ..
""", (4, 5))
SK.subst(SHARP_HEAD["bow"], 0.75, """
...HMMMM.
Q.HHHHHHH
.QjjKKKj.
..QIjjjjI
..QIKKKKK
...QIIQ..
""", (4, 5))
SK.subst(SHARP_HEAD["dead"], 0.75, """
...HMMMM.
Q.HHHHHHM
.QjKjKjj.
..QIjKjjI
..QIKKKK.
...QIIQ..
""", (4, 5))
for _sc in (0.65, 0.72):
    SK.subst(PUPPET_HEAD["grin"], _sc, """
.hXX.
hKXKX
hXXXX
KKKKK
KXWXK
.KwK.
""", (2, 5))
    SK.subst(PUPPET_HEAD["gape"], _sc, """
.hXX.
hKXKX
hXXXX
KKKKK
KXKXK
.K.K.
""", (2, 5))
    SK.subst(PUPPET_HEAD["dead"], _sc, """
.hXX.
hkXkX
hXXXX
hKKKw
hKXKw
.hww.
""", (2, 5))
SK.subst(IMP_HEAD["grin"], 0.55, """
W...W
.DEf.
DYEYf
dKXKE
.dKd.
""", (2, 4))
SK.subst(IMP_HEAD["glee"], 0.55, """
W...W
.DEf.
DKEKf
KXKXK
.KEK.
""", (2, 4))
SK.subst(IMP_HEAD["dead"], 0.55, """
W...W
.DEf.
DpEpf
dEKKE
.dDd.
""", (2, 4))


# ================================================================== v0.7.2 tree: FORTUNE TELLER (T2, hovers)
# New sheets below are drawn at their final size (scale 1.0, no ArtScale entry).
TELLER_HEAD = {
    "gaze": Part("""
.qnNNn..
qnNNNNn.
nNzZzZe.
nNhwWYw.
nnhwWWWX
qnhKKw..
.qnhww..
""", (3, 6)),
    "glare": Part("""
.qnNNn..
qnNNNNn.
nNzZzZe.
nNhwWyw.
nnhwWWWX
qnhKEK..
.qnhKw..
""", (3, 6)),
    "shut": Part("""
.qnNNn..
qnNNNNn.
nNzZzZe.
nNhwKKw.
nnhwWWWX
qnhKKw..
.qnhww..
""", (3, 6)),
    "dead": Part("""
.qnNNn..
qnNNNNn.
nNzZzZe.
nNhKwKw.
nnhwKWWX
qnhwKK..
.qnhww..
""", (3, 6)),
}
ROBE = "qqnN"
GLASS = "nNLc"


def crystal_ball(c, x, y, r=3.0, ph=0, glow=1):
    """Crystal ball centred (x, y): violet glass, a swirl of light that turns with ph, a white glint."""
    ell(c, x, y, r, r, GLASS, bias=0.05 + 0.15 * glow)
    a = ph * 1.3
    for k in range(2 + glow):
        aa = a + k * 2.1
        c.put(*P(x + (r - 1.4) * math.cos(aa), y + (r - 1.4) * math.sin(aa) * 0.8), "L" if k else "y")
    c.put(*P(x - r * 0.5, y - r * 0.55), "c")
    if glow > 1:
        for k in range(4):
            aa = math.radians(45 + 90 * k + ph * 20)
            c.put(*P(x + (r + 2) * math.cos(aa), y + (r + 2) * math.sin(aa)), "L" if k % 2 else "N")


def teller(dx=0.0, dy=0.0, lean=0.0, hover=3.0, ball=(7, -11), glow=1, ph=0, head="gaze", hem=0, trail=0.0,
           bhand=None, fhand=None, ball_on=True, extra=None, extra_back=None, over=None, hd=(0, 0)):
    """Hunched fortune teller hovering on smoke. ball: crystal ball centre; bhand/fhand: hand targets
    (default: cupping the ball); trail: hem streaming back (run)."""
    c = Canvas()
    if extra_back: extra_back(c)
    yh = -hover + dy            # hem
    ys = yh - 12                # shoulders
    T = Xf(lean, (dx, yh))
    bx, by = ball[0] + dx, ball[1] + dy
    bhand = bhand or (bx - 2.5, by + 1.5)
    fhand = fhand or (bx + 0.5, by + 3)
    # back arm (behind the robe)
    shb = T(dx - 1.5, ys + 1.5)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bhand[0] + (0 if bhand is ball else 0), bhand[1], 4.0, 4.0, 1)
    tube(c, [shb, (ex, ey), (hx, hy)], [1.0, 0.9, 0.7], "qqn")
    c.put(*P(hx, hy), "w")
    # robe: a bell of plum cloth that tapers into smoke
    robe = [T(dx - 3.2, ys), T(dx + 3.4, ys), T(dx + 5.2 - trail * 0.3, yh - 2), T(dx + 5.6 - trail * 0.6, yh),
            T(dx - 6.0 - trail, yh), T(dx - 5.0 - trail * 0.6, yh - 2)]
    poly(c, robe, ROBE, bias=0.1)
    # dagged hem melting into violet smoke
    for k, xx in enumerate(range(-6, 6)):
        x0 = dx + xx - trail * (0.9 if xx < 0 else 0.4)
        drop = (k + hem) % 3
        for j in range(drop):
            c.put(*P(*T(x0, yh + 1 + j)), "n" if j == 0 else ("q" if (k + j) % 2 else "N"))
    if trail:
        for j in range(3):
            c.put(*P(dx - 7 - trail - j * 1.5, yh - 1 - (j + hem) % 2), "n" if j < 2 else "q")
    # stars stitched on the robe
    for sx, sy in ((-2.5, 4), (2, 7), (-3.5, 9)):
        c.put(*P(*T(dx + sx, ys + sy)), "e")
    # crimson shawl with a fringe of gold coins
    sh = [T(dx - 4.2, ys - 0.4), T(dx + 3.8, ys - 0.4), T(dx + 4.3, ys + 2.5), T(dx + 1.0, ys + 6.0),
          T(dx - 4.6, ys + 3.5)]
    poly(c, sh, CRIM, bias=0.15)
    for k, (fx, fy) in enumerate(((-4, 4.5), (-2.5, 5.5), (-1, 6.5), (0.6, 7.2), (2.2, 5.6), (3.6, 3.8))):
        c.put(*P(*T(dx + fx, ys + fy)), "Z" if k % 2 else "z")
    # head on a hunched neck
    neck = T(dx + 1.8, ys - 0.2)
    c.part(TELLER_HEAD[head], *P(neck[0] + hd[0], neck[1] + hd[1]))
    # v0.10 lineage (one parent, the Card Sharp): its green celluloid visor over her hood and a playing-card
    # earring (the Dice Imp's horns and die earring are gone)
    hx0, hy0 = P(neck[0] + hd[0], neck[1] + hd[1])
    for x in range(-2, 5):
        c.raw.put(hx0 + x, hy0 - 4, "M" if x < 3 else "H")
    c.raw.put(hx0 + 5, hy0 - 3, "H")
    for (x, y, ch) in ((-1, -1, "X"), (-1, 0, "E"), (-2, 0, "X"), (-2, -1, "X"), (-1, 1, "X"), (-2, 1, "W")):
        c.raw.put(hx0 + x, hy0 + y, ch)
    if ball_on:
        crystal_ball(c, bx, by, 3.0, ph, glow)
    # front arm: bony hand cupping the ball from below
    shf = T(dx + 1.5, ys + 2.0)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fhand[0], fhand[1], 4.0, 4.0, 1)
    tube(c, [shf, (ex, ey)], [1.1, 0.9], "qnN")
    line(c, ex, ey, hx, hy, "w")
    c.put(*P(ex, ey), "z")   # bangle
    c.put(*P(hx, hy), "W"); c.put(*P(hx + 1, hy - 1), "w")
    if extra: extra(c)
    return finish(c, over)


def tarot_back(c, x, y, ang=0.0, face=False):
    card(c, x, y, 2.6, 3.8, face=face, ang=ang)


def build_teller(outdir):
    F = teller
    idle = [F(dy=0, ph=0, hem=0), F(dy=-0.5, ph=1, hem=1), F(dy=-1, ph=2, hem=2, head="shut"), F(dy=-0.5, ph=3, hem=1)]
    run = [F(lean=12, dy=[0, -0.5, -1, -1, -0.5, 0][i], trail=3 + (i % 3), hem=i, ph=i, ball=(8, -10))
           for i in range(6)]
    # Gaze: draw the ball in (0), lift it to the eye (1), it flares (2), THRUST and loose the bolt (3), hold, settle
    gaze = [F(ball=(4, -12), ph=0, lean=-4),
            F(ball=(5, -17), ph=1, glow=2, lean=-8, head="glare"),
            F(ball=(6, -16), ph=2, glow=2, lean=-6, head="glare"),
            F(ball=(10, -12), ph=3, glow=2, lean=10, head="glare",
              extra=lambda c: [sparkle(c, 14, -12, 2, "N", "L"), line(c, 15, -12, 17, -12, "L")]),
            F(ball=(9, -12), ph=4, glow=1, lean=8),
            F(ball=(7, -11), ph=5, lean=2)]

    def orbit(n, phase, r=8.0, cy=-13.0, front=True):
        def f(c):
            for i in range(n):
                a = phase + i * 2 * math.pi / n
                if (math.sin(a) > 0) != front: continue
                tarot_back(c, r * math.cos(a), cy + 2.5 * math.sin(a), ang=math.degrees(a) * 0.3, face=(i % 2 == 0))
        return f
    # Foretell: the ball rises over her head (0), cards fan out (1), they circle her (2-3),
    # she POINTS and one card flies at the hero (4: spawn the fate mark), cards fold away (5-7)
    fore = [F(ball=(2, -24), bhand=(-2, -22), fhand=(4, -23), ph=0, glow=1, head="shut"),
            F(ball=(2, -25), bhand=(-3, -23), fhand=(5, -24), ph=1, glow=2, head="glare",
              extra_back=orbit(3, 0.4, 6, -17, False), extra=orbit(3, 0.4, 6, -17, True)),
            F(ball=(2, -25), bhand=(-3, -23), fhand=(5, -24), ph=2, glow=2, head="glare",
              extra_back=orbit(4, 1.3, 9, -17, False), extra=orbit(4, 1.3, 9, -17, True)),
            F(ball=(2, -24), bhand=(-3, -22), fhand=(5, -23), ph=3, glow=2, head="glare",
              extra_back=orbit(4, 2.2, 9, -17, False), extra=orbit(4, 2.2, 9, -17, True)),
            F(ball=(1, -22), bhand=(-3, -21), fhand=(11, -15), ph=4, glow=2, head="glare", lean=8,
              extra_back=orbit(3, 3.0, 8, -17, False),
              extra=lambda c: [orbit(3, 3.0, 8, -17, True)(c), tarot_back(c, 15, -15, ang=80, face=True),
                               line(c, 11, -15, 13, -15, "L")]),
            F(ball=(2, -21), bhand=(-3, -20), fhand=(10, -15), ph=5, glow=1, lean=6,
              extra=orbit(2, 3.6, 6, -16, True)),
            F(ball=(5, -15), ph=6, lean=2),
            F(ph=7)]
    d0 = F(lean=-16, ball=(9, -18), bhand=(-5, -18), fhand=(7, -20), head="glare", glow=2, dy=-1)
    d1 = F(lean=-22, hover=1, ball=(10, -3), bhand=(-6, -12), fhand=(4, -9), head="dead", glow=0)
    d2 = grounded(rot_spr(F(hover=0, ball_on=False, head="dead", bhand=(-5, -9), fhand=(4, -8)), -55, (0, -1)))
    d2 = merge(d2, Spr({(11, 0): "N", (12, 0): "L", (11, -1): "c", (13, 0): "n"}))
    corpse = teller_corpse()
    knock = F(lean=-20, dx=-1, ball=(6, -18), bhand=(-6, -16), fhand=(5, -19), head="glare", hem=1, dy=-1)
    anims = [("Idle", idle, [0.2, 0.15, 0.2, 0.15]), ("Run", run, [0.08] * 6),
             ("Gaze", gaze, [0.14, 0.12, 0.08, 0.06, 0.1, 0.14]),
             ("Foretell", fore, [0.12, 0.1, 0.08, 0.08, 0.06, 0.12, 0.12, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxFortuneTeller", anims, outdir, scale=5)


def teller_corpse():
    """An empty heap of plum robe and crimson shawl, the cracked crystal ball rolled clear."""
    c = Canvas()
    poly(c, [(-8, 0), (-6, -3), (-2, -4), (3, -3), (6, -1), (7, 0)], ROBE, bias=0.1)
    poly(c, [(-5, -2), (-2, -4.5), (2, -4), (0, -1)], CRIM, bias=0.15)
    for x in (-4, -2, 0, 2):
        c.put(x, -1 if x % 4 else -2, "z")
    c.part(TELLER_HEAD["dead"], -7, -1)
    crystal_ball(c, 10, -2, 2.0, 0, 0)
    c.put(10, -3, "K"); c.put(11, -2, "K")
    return grounded(finish(c))


# ================================================================== v0.7.2 tree: SNAKE-EYES (T2, ground serpent)
SNAKE_HEAD = {
    "shut": Part("""
.msss...
mmsXXs..
mmmXEms.
mmmmmmms
.dDEEDf.
""", (1, 3)),
    "hiss": Part("""
.msss....
mmsXXss..
mmmXEmmms
mmKKKWKW.
mmKffEK..
.dDDDD...
""", (1, 3)),
    "dead": Part("""
.msss...
mmsKXs..
mmmXKms.
mmmmmmms
.dDKKDf.
""", (1, 3)),
}


def snake_path(pts, radii):
    """Smooth a control polyline (Catmull-Rom) into a dense one with interpolated radii."""
    out, rr = [], []
    n = len(pts)
    for i in range(n - 1):
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(n - 1, i + 2)]
        for k in range(4):
            t = k / 4.0
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y)); rr.append(radii[i] + (radii[i + 1] - radii[i]) * t)
    out.append(pts[-1]); rr.append(radii[-1])
    return out, rr


def serpent(c, pts, radii, belly=0.3, anchor=(0, 0)):
    """Harlequin snake body along pts: crimson/black diamonds on the back, an ivory belly stripe below
    (only on the last `belly` fraction of the body: the raised neck shows its throat)."""
    sp, sr = snake_path(pts, radii)
    tube(c, sp, sr, harl(anchor[0], anchor[1], 3, CRIM, BLK), bias=0.1)
    if belly:
        k0 = int(len(sp) * (1 - belly))
        bp = [(x + r * 0.55, y + r * 0.25) for (x, y), r in zip(sp[k0:], sr[k0:])]
        tube(c, bp, [max(0.4, r * 0.35) for r in sr[k0:]], "hwWW", bias=0.2)
    return sp, sr


def rattle(c, x, y, shake=0):
    """Tail tip rattle: two tiny ivory dice."""
    for k, (ox, oy) in enumerate(((0, 0), (-1.6, 1.2))):
        xx, yy = x + ox + (shake if k == 0 else -shake), y + oy
        for ddx, ddy, ch in ((0, 0, "X"), (1, 0, "W"), (0, 1, "W"), (1, 1, "w")):
            c.put(*P(xx + ddx, yy + ddy), ch)
        c.put(*P(xx + (k % 2), yy), "K")


def cobra_hood(c, x, y, ang=0.0, w=4.0, h=4.6, ring=0):
    ell(c, x, y, w, h, harl(x, y, 3, BLK, CRIM), ang=ang, bias=0.05)
    for s in (-1, 1):
        bx = x + s * w * math.cos(math.radians(ang)) * 0.95
        by = y + s * w * math.sin(math.radians(ang)) * 0.95 + 1.5
        bell(c, bx + (ring if s > 0 else -ring) * 0.5, by, s=0.8)


COIL = [(-7, -1.6), (-9, -3.6), (-7, -5.6), (-3.5, -4.6), (-1, -2.4)]


def snake_eyes(neck=((2, -2), (4, -6), (4, -10)), head=(6, -13), head_ang=0.0, face="shut", tongue=False,
               body=None, tail=(-3.5, -1.2), tail_up=None, shake=0, hood=True, hood_ang=-10.0, ring=0, extra=None,
               extra_back=None, over=None, dx=0.0, dy=0.0):
    """Coiled harlequin serpent. body: ground control points from the tail to the neck base; neck: control points
    of the raised neck; head: neck joint of the head part. tail_up: (x, y) of the raised tail tip (rattling)."""
    c = Canvas()
    if extra_back: extra_back(c)
    body = body or COIL
    tailp = [tail] if tail_up is None else [tail_up, (tail_up[0] + 1.0, tail_up[1] + 3.5), (-8.5, -3)]
    allp = [(x + dx, y + dy) for x, y in tailp + body + list(neck) + [head]]
    n_t = len(tailp)
    radii = []
    for i in range(len(allp)):
        t = i / (len(allp) - 1.0)
        radii.append(0.6 + 1.9 * math.sin(min(1.0, t * 1.25) * math.pi * 0.62) if t < 0.85 else 1.6)
    if hood:
        hx, hy = (allp[-2][0] + allp[-1][0]) / 2.0 - 1.4, (allp[-2][1] + allp[-1][1]) / 2.0 + 0.8
        cobra_hood(c, hx, hy, ang=hood_ang, ring=ring)
    serpent(c, allp[:-1] + [(allp[-1][0] - 0.5, allp[-1][1] + 0.5)], radii, anchor=(dx, dy))
    tip = allp[0]
    rattle(c, tip[0] + (0.5 if tail_up is None else -1), tip[1] - 1, shake)
    hp = Canvas()
    hp.part(SNAKE_HEAD[face], 0, 0)
    if tongue:
        for x, y in ((6, 1), (7, 1), (8, 0), (8, 2)):
            hp.put(x, y, "E" if x < 8 else "f")
    # v0.9 lineage: the Dice Imp's ivory horns
    for (x, y, ch) in ((1, -4, "W"), (0, -5, "W"), (-1, -6, "w"), (-1, -7, "h"), (3, -4, "W"), (3, -5, "w"), (4, -6, "h")):
        hp.raw.put(x, y, ch)
    hs = rot_spr(hp.spr(), head_ang, (0, 0)) if head_ang else hp.spr()
    SK.paste(c, hs, *P(head[0] + dx, head[1] + dy))
    if extra: extra(c)
    return finish(c, over)


def build_snake_eyes(outdir):
    S = snake_eyes
    sway = [(0, 0), (0.5, -0.3), (1, -0.5), (0.5, -0.3)]
    idle = [S(neck=((2, -2), (4, -6), (4 + sway[i][0] * 0.5, -10 + sway[i][1])), head=(6 + sway[i][0], -13 + sway[i][1]),
              tongue=(i == 2), shake=(i % 2), ring=[0, 1, 0, -1][i],
              body=[(-7, -1.6), (-9, -3.6), (-7, -5.6 - 0.3 * (i % 2)), (-3.5, -4.6), (-1, -2.4)]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        body = [(-11 + 3 * k, -1.6 - 1.3 * math.sin(ph + k * 1.3)) for k in range(5)]
        run.append(S(body=body[1:], tail=body[0], neck=((5, -3 - 0.6 * math.sin(ph)), (8, -5)), head=(10, -7),
                     head_ang=10, hood=False, tongue=(i in (1, 4)), shake=i % 2))
    # Strike: draw the neck back (0-1), lunge (2), BITE far forward (3), hold, withdraw (4-6)
    strike = [S(neck=((1, -2), (2, -7), (1, -11)), head=(2, -15), face="shut", hood_ang=-30),
              S(neck=((0, -2), (0, -7), (-1, -11)), head=(0, -15), head_ang=-10, face="hiss", hood_ang=-40),
              S(neck=((3, -2), (7, -6), (10, -9)), head=(12, -10), head_ang=10, face="hiss", hood_ang=10),
              S(neck=((4, -2), (9, -4), (14, -6)), head=(16, -8), head_ang=10, face="hiss", hood=False),
              S(neck=((4, -2), (8, -5), (11, -8)), head=(13, -10), head_ang=5, face="hiss", hood_ang=5),
              S(neck=((3, -2), (5, -6), (6, -10)), head=(8, -13), face="shut", hood_ang=-5),
              S(face="shut", tongue=True)]
    # Craps: the rattle rises over its back (0-1, dice shake), the tail FLICKS the dice forward (2-3, release 3),
    # it watches them roll (4-7)
    craps = [S(tail_up=(-9, -9), shake=0, face="shut", head=(7, -13)),
             S(tail_up=(-7, -12), shake=1, face="hiss", head=(7, -12), ring=1,
               extra=lambda c: [c.put(-9, -14, "w"), c.put(-5, -14, "w")]),
             S(tail_up=(-2, -14), shake=-1, face="hiss", head=(8, -12), ring=-1,
               extra=lambda c: [c.put(-4, -16, "S"), c.put(0, -17, "S")]),
             S(tail_up=(6, -6), shake=0, face="hiss", head=(5, -14), head_ang=-10, hood_ang=-20,
               extra=lambda c: [die(c, 11, -5, 3, 20, 40, 0), die(c, 13, -2, 3, 70, 20, 10),
                                line(c, 7, -6, 9, -6, "w")]),
             S(face="shut", head=(7, -14), head_ang=-12, tongue=True),
             S(face="shut", head=(8, -13), head_ang=-6, ring=1),
             S(face="hiss", head=(7, -13), tongue=True, ring=-1),
             S(face="shut")]
    d0 = S(neck=((1, -2), (1, -8), (-1, -12)), head=(-1, -16), head_ang=-30, face="hiss", hood_ang=-50)
    d1 = S(neck=((2, -2), (5, -4), (6, -7)), head=(8, -8), head_ang=40, face="dead", hood_ang=40)
    d2 = S(neck=((3, -1.5), (6, -1.5), (9, -1.5)), head=(11, -2), head_ang=80, face="dead", hood=False,
           body=[(-9, -1.5), (-6, -2.2), (-3, -1.5), (0, -1.4)], tail=(-12, -1))
    corpse = snake_corpse()
    knock = S(neck=((0, -2), (-1, -6), (-3, -10)), head=(-3, -13), head_ang=-35, face="hiss", hood_ang=-45, shake=1)
    anims = [("Idle", idle, [0.2, 0.15, 0.2, 0.15]), ("Run", run, [0.075] * 6),
             ("Strike", strike, [0.14, 0.12, 0.05, 0.08, 0.1, 0.12, 0.14]),
             ("Craps", craps, [0.12, 0.08, 0.08, 0.06, 0.12, 0.12, 0.12, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxSnakeEyes", anims, outdir, scale=6)


def snake_corpse():
    c = Canvas()
    serpent(c, [(-12, -1), (-8, -2), (-4, -1.2), (0, -2), (4, -1.2), (8, -1.6)], [0.6, 1.4, 2.0, 2.0, 1.8, 1.6])
    rattle(c, -13, -2)
    hp = Canvas(); hp.part(SNAKE_HEAD["dead"], 0, 0)
    SK.paste(c, rot_spr(hp.spr(), 90, (0, 0)), 10, -1)
    die(c, 15, -2, 3, 0, 30, 0)
    return grounded(finish(c))


# ================================================================== v0.7.2 tree: BIG-TOP CHIMERA (T3, quadruped)
LION = "hiiw"
LION_DK = "thhi"
MANE = "tdaa"
LION_FACE = {
    "snarl": Part("""
.wWWw...
wWWYKW..
wWWWWWhK
hwWWXXXK
.hwKKKK.
..hhh...
""", (0, 3)),
    "roar": Part("""
.wWWw...
wWWyKW..
wWWWWWhK
hwWXKXK.
.hwKfK..
.hwXKX..
..hh....
""", (0, 3)),
    "dead": Part("""
.wWWw...
wWKwKW..
wWWKWWhK
hwWWWWWK
.hwKKKK.
..hhh...
""", (0, 3)),
}


def paw(c, x, y, near=True, claws=False):
    ell(c, x + 0.5, y - 0.6, 1.6, 1.0, LION if near else LION_DK, bias=0.1)
    if claws:
        for k in range(3):
            c.put(*P(x + 2 + (k % 2), y - 1 + k), "X")


def chimera(dx=0.0, dy=0.0, pitch=0.0, feet=((-9, 0), (-6, 0), (5, 0), (8, 0)), face="snarl", head=(0, 0),
            mane=0, tail=0.0, tongue=False, hoop=None, flames=None, claws=False, extra=None, extra_back=None,
            over=None, body_y=-10.5, front_lift=0.0, tail_rise=1.0):
    """Circus lion in harlequin barding with a ribboned tail. feet: (far back, near back, far front,
    near front) foot targets; pitch tilts the body (negative = rearing); front_lift raises the shoulders."""
    c = Canvas()
    if extra_back: extra_back(c)
    bc = (dx, body_y + dy)
    T = Xf(pitch, bc)
    hipb, shf = T(bc[0] - 7, bc[1] + 1), T(bc[0] + 6, bc[1] + 1 - front_lift)
    if hoop and hoop[3] == "back":
        flaming_hoop(c, hoop[0], hoop[1], hoop[2], 2, ry=hoop[4], phase=hoop[5])
    # serpent tail rising from the rump
    rump = T(bc[0] - 9.5, bc[1] - 1.5)
    k_ = tail_rise
    tp = [rump, (rump[0] - 3, rump[1] - (2 - tail * 0.3) * k_), (rump[0] - 4.5 + tail * 0.5 - 4 * (1 - k_), rump[1] - 7 * k_),
          (rump[0] - 3 + tail - 8 * (1 - k_), rump[1] - 11 * k_), (rump[0] - 0.5 + tail * 1.2 - 11 * (1 - k_), rump[1] - 12.5 * k_)]
    # v0.10 lineage (one parent, the Ringmaster): a lion's tail wound with the Ringmaster's scarlet-and-black
    # ribbon and a dark tuft (the Snake-Eyes serpent tail went with that parent)
    sp_, sr_ = snake_path(tp, [1.4, 1.2, 1.1, 1.0, 0.9])
    tube(c, sp_, sr_, stripes(0, 2, LION, "dDEf", ang=-45), bias=0.15)
    shx, shy = tp[-1]
    ell(c, shx + 0.5, shy - 0.5, 2.0, 1.8, "kttT", bias=0.1)
    c.put(*P(shx - 0.5, shy - 1.5), "T"); c.put(*P(shx + 2, shy + 1), "k")
    if tongue:
        c.put(*P(shx + 2.5, shy - 2), "t")
    # far legs
    for i, (hp, ft) in enumerate(((hipb, feet[0]), (shf, feet[2]))):
        (kx, ky), (ax, ay) = ik(hp[0] - 1, hp[1], ft[0] + dx, ft[1] - 1, 4.2, 4.8, 1 if i == 0 else -1)
        tube(c, [(hp[0] - 1, hp[1]), (kx, ky), (ax, ay)], [2.0, 1.4, 1.1], LION_DK)
        paw(c, ax, min(0, ay + 1), near=False)
    # body
    ell(c, bc[0], bc[1], 10.5, 5.6, LION, ang=pitch, bias=0.1)
    ell(c, *T(bc[0] + 1, bc[1] + 3), 7.5, 1.6, "iwWW", ang=pitch, bias=0.25)   # pale belly
    # harlequin barding blanket with a gold fringe and bells
    bl = [T(bc[0] - 7, bc[1] - 4.5), T(bc[0] + 4.5, bc[1] - 5.2), T(bc[0] + 5.5, bc[1] + 1.5), T(bc[0] - 7.5, bc[1] + 1.5)]
    poly(c, bl, harl(bc[0] - 1, bc[1] - 2, 4, CRIM, BLK, ang=pitch), bias=0.15)
    a, b = T(bc[0] - 7.5, bc[1] + 1.8), T(bc[0] + 5.5, bc[1] + 1.8)
    line(c, *a, *b, "e")
    for k in range(-7, 6, 3):
        bx, by = T(bc[0] + k, bc[1] + 2.8)
        c.put(*P(bx, by), "z"); c.put(*P(bx, by + 1), "A")
    a, b = T(bc[0] - 6.5, bc[1] - 4.6), T(bc[0] + 4.2, bc[1] - 5.3)
    line(c, *a, *b, "z")
    # near legs
    for i, (hp, ft) in enumerate(((T(bc[0] - 6, bc[1] + 1.5), feet[1]), (T(bc[0] + 7, bc[1] + 1.5 - front_lift), feet[3]))):
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], ft[0] + dx, ft[1] - 1, 4.2, 4.8, 1 if i == 0 else -1)
        tube(c, [hp, (kx, ky), (ax, ay)], [2.4, 1.6, 1.3], LION)
        paw(c, ax, min(0, ay + 1), near=True, claws=(claws and i == 1))
    # mane, ruff and face
    hx, hy = T(bc[0] + 10.5 + head[0], bc[1] - 4 + head[1])
    r = random.Random(mane)
    ell(c, hx - 1, hy, 5.2, 6.0, MANE, bias=0.1)
    for k in range(14):
        aa = math.radians(100 + k * 18 + r.uniform(-6, 6))
        rr = r.uniform(5.5, 7.0)
        c.put(*P(hx - 1 + rr * math.cos(aa), hy + rr * 1.1 * math.sin(aa)), "a" if k % 3 else "t")
    for k in range(5):   # lit locks on the top-left of the mane
        c.put(*P(hx - 4 + k * 1.3, hy - 4.5 + abs(k - 2) * 0.6), "O" if k % 2 else "a")
    ell(c, hx - 1.5, hy + 5, 4.6, 1.5, stripes(hx, 1, "hwWX", CRIM), bias=0.25)
    bell(c, hx - 5.5, hy + 5.5, s=0.8); bell(c, hx + 2.5, hy + 6.5, s=0.8)
    c.part(LION_FACE[face], *P(hx, hy))
    c.put(*P(hx - 1, hy - 4), "w"); c.put(*P(hx - 2, hy - 5), "h")   # ear
    # v0.9 lineage: the Ringmaster's black top hat with its red band, cocked on the mane
    top_hat(c, hx - 2.5, hy - 5.5, tilt=-12 + pitch * 0.3, h=4)
    if hoop and hoop[3] == "front":
        flaming_hoop(c, hoop[0], hoop[1], hoop[2], 2, ry=hoop[4], phase=hoop[5])
    if flames:
        fire_ring(c, *flames)
    if extra: extra(c)
    return finish(c, over)


def fire_ring(c, cx, rx, k, ry=3.0, seed=0, up=0):
    """Flames licking up in a ring on the floor (centre cx, radius rx); k = flame height 1..4."""
    rnd_ = random.Random(seed)
    n = max(10, int(rx * 2.4))
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = cx + rx * math.cos(a), -ry + ry * math.sin(a) - up
        if y > 0: y = 0
        hgt = max(1, k + rnd_.randint(-1, 1))
        for j in range(hgt):
            col = ("y" if k > 2 else "Y") if j == 0 else ("O" if j < hgt - 1 else "o")
            c.put(*P(x + (rnd_.choice((-1, 0, 1)) if j > 1 else 0), y - j), col)


def build_chimera(outdir):
    C = chimera
    FT = ((-9, 0), (-6, 0), (5, 0), (8, 0))
    idle = [C(dy=[0, 0.4, 0.6, 0.3][i], tail=[0, 1, 2, 1][i], mane=i, tongue=(i == 2),
              feet=FT, face="snarl") for i in range(4)]
    run = []
    gait = [((-12, 0), (-4, -1), (8, -1), (2, 0)), ((-10, -1), (-6, 0), (10, 0), (4, -2)),
            ((-7, -1), (-9, 0), (6, 0), (9, -1)), ((-4, 0), (-12, -1), (2, -2), (11, 0)),
            ((-6, 0), (-10, -1), (4, -1), (10, 0)), ((-9, 0), (-7, -1), (7, -1), (6, 0))]
    for i in range(6):
        run.append(C(feet=gait[i], dy=[0, -1, -1.5, -1, 0, 0][i], pitch=[2, 0, -2, 0, 2, 0][i], tail=-3 - (i % 3),
                     mane=i + 10))
    # Maul: rear up (0-1), drop the paw (2), RAKE low and forward (3), hold, settle (4-6)
    maul = [C(pitch=-10, front_lift=2, feet=((-9, 0), (-7, 0), (6, -3), (9, -5)), face="snarl", mane=20),
            C(pitch=-22, front_lift=4, dy=-1, feet=((-10, 0), (-8, 0), (6, -8), (10, -11)), face="roar", mane=21,
              tail=2),
            C(pitch=-6, front_lift=1, feet=((-9, 0), (-7, 0), (10, -6), (14, -6)), face="roar", mane=22, claws=True),
            C(pitch=8, dx=2, feet=((-8, 0), (-5, 0), (11, -1), (17, -2)), face="roar", mane=23, claws=True, tail=-3,
              extra=lambda c: [line(c, 17, -9, 22, -4, "X"), line(c, 16, -7, 21, -2, "W"), line(c, 15, -10, 20, -6, "w")]),
            C(pitch=6, dx=2, feet=((-8, 0), (-5, 0), (10, 0), (15, 0)), face="snarl", mane=24, tail=-2),
            C(pitch=2, dx=1, feet=((-9, 0), (-6, 0), (6, 0), (10, 0)), face="snarl", mane=25),
            C(feet=FT, mane=26)]
    # Leap: crouch (0-1, the burning hoop appears), SPRING (2), through the hoop (3-4), LAND (5: fire ring),
    # absorb, recover (6-8)
    lp = [C(dy=2, pitch=4, feet=((-10, 0), (-7, 0), (6, 0), (9, 0)), face="snarl", mane=30),
          C(dy=3, pitch=8, feet=((-11, 0), (-8, 0), (5, 0), (8, 0)), face="roar", mane=31, tail=-2,
            hoop=(19, -14, 2.0, "front", 9.0, 0)),
          C(dy=-5, pitch=-20, front_lift=2, feet=((-13, -1), (-11, 0), (12, -12), (15, -14)), face="roar", mane=32,
            tail=-4, hoop=(20, -14, 2.5, "back", 9.0, 1)),
          C(dy=-10, pitch=-4, feet=((-15, -8), (-13, -7), (13, -11), (16, -12)), face="roar", mane=33, tail=-5,
            hoop=(4, -22, 2.5, "back", 9.0, 2)),
          C(dy=-6, pitch=10, feet=((-12, -8), (-10, -6), (10, -2), (13, -3)), face="roar", mane=34, tail=-3),
          C(dy=2, pitch=6, feet=((-10, 0), (-7, 0), (8, 0), (12, 0)), face="roar", mane=35, flames=(1, 16, 3, 5.0, 1)),
          C(dy=1, pitch=3, feet=((-10, 0), (-7, 0), (6, 0), (10, 0)), face="snarl", mane=36, flames=(1, 18, 2, 5.5, 2)),
          C(dy=0.5, feet=FT, mane=37, flames=(1, 19, 1, 6.0, 3)),
          C(feet=FT, mane=38)]
    d0 = C(pitch=-18, front_lift=3, feet=((-10, 0), (-8, 0), (5, -6), (9, -8)), face="roar", mane=40, tail=3)
    d1 = C(dy=2, pitch=12, feet=((-10, 0), (-7, 0), (4, 0), (7, 0)), face="dead", mane=41, tail=4)
    d2 = C(dy=4, pitch=6, feet=((-13, 0), (-11, 0), (10, 0), (12, 0)), face="dead", mane=42, tail=2, head=(0, 2),
           tail_rise=0.5)
    corpse = chimera_corpse()
    knock = C(pitch=-14, dx=-2, front_lift=2, feet=((-11, 0), (-8, 0), (3, -4), (6, -5)), face="roar", mane=44, tail=4)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.075] * 6),
             ("Maul", maul, [0.16, 0.12, 0.06, 0.08, 0.1, 0.12, 0.14]),
             ("Leap", lp, [0.12, 0.14, 0.08, 0.1, 0.08, 0.06, 0.14, 0.14, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.12, 0.14, 0.16, 0.5], knock)
    return sheet("JinxChimera", anims, outdir, scale=4)


def chimera_corpse():
    """Sprawled flat: legs splayed fore and aft, head down on the floor, the serpent tail limp."""
    return grounded(chimera(dy=5.5, pitch=4, feet=((-15, 0), (-13, 0), (12, 0), (15, 0)), face="dead", mane=50,
                            tail=0, head=(1, 3), tail_rise=0.15))


# ================================================================== v0.7.2 tree: PUPPETEER (T3, tall caster)
PUPPETEER_HEAD = {
    "calm": Part("""
..dDDE....
.dDEEEf...
dDEhXXW...
dDhwXKXWW.
dDhwXXXXXWX
dDhwWXKK...
.dhwwWW....
..dhh......
""", (4, 7)),
    "laugh": Part("""
..dDDE....
.dDEEEf...
dDEhXXW...
dDhwKXKWW.
dDhwXXXXXWX
dDhwKXKX...
.dhwKKK....
..dhh......
""", (4, 7)),
    "dead": Part("""
..dDDE....
.dDEEEf...
dDEhXXW...
dDhwKXKWW.
dDhwXKXXXWX
dDhwKXKK...
.dhwwWW....
..dhh......
""", (4, 7)),
}


def control_cross(c, x, y, ang=0.0):
    """Wooden marionette control bar held at (x, y): returns the three string anchors (back, front, tip)."""
    T = Xf(ang, (x, y))
    a, b = T(x - 3.5, y), T(x + 3.5, y)
    tube(c, [a, b], [0.7, 0.7], WOOD, bias=0.2)
    v0, v1 = T(x, y - 2.5), T(x, y + 2.5)
    tube(c, [v0, v1], [0.6, 0.6], WOOD, bias=0.25)
    for q in (a, b): c.put(*P(*q), "z")
    return a, b, v1


def mini_puppet(c, x, y, jig=0, col=CRIM, face="X", knife=False, flip=False):
    """Tiny jester puppet hanging from (x, y) (top of its cap). Returns its head and hand points."""
    s = -1 if flip else 1
    c.put(*P(x - 1, y), col[1]); c.put(*P(x + 1, y), col[3]); c.put(*P(x - 2, y - 1), "z"); c.put(*P(x + 2, y - 1), "z")
    for dx_, dy_, ch in ((-1, 1, "X"), (0, 1, "X"), (1, 1, "W"), (-1, 2, "W"), (0, 2, face), (1, 2, "w")):
        c.put(*P(x + dx_ * s, y + dy_), ch)
    ell(c, x, y + 5, 1.5, 2.2, col, bias=0.15)
    c.put(*P(x, y + 3), "W")
    arm = [(-2, 2), (-2, 0), (-2, -2), (-1, 3)][jig % 4]
    arm2 = [(2, -1), (2, 1), (2, 3), (3, 0)][jig % 4]
    leg = [(-1, 3), (-2, 2), (0, 3), (-1, 2)][jig % 4]
    leg2 = [(1, 3), (1, 2), (2, 2), (1, 3)][jig % 4]
    h1 = (x - 1 + arm[0] * s, y + 4 + arm[1]); h2 = (x + 1 + arm2[0] * s, y + 4 + arm2[1])
    line(c, x - 1 * s, y + 4, *h1, col[0]); line(c, x + 1 * s, y + 4, *h2, col[1])
    line(c, x - 0.5, y + 7, x - 0.5 + leg[0], y + 7 + leg[1], col[0])
    line(c, x + 0.5, y + 7, x + 0.5 + leg2[0], y + 7 + leg2[1], col[1])
    if knife:
        line(c, h2[0], h2[1], h2[0] + 2 * s, h2[1] - 1, "U"); c.put(*P(h2[0] + 3 * s, h2[1] - 1), "u")
    return (x, y + 1), h1, h2


PUP_FROCK = "kttT"


def puppeteer(dx=0.0, dy=0.0, lean=0.0, feet=(-3, 3), fh=(9, -23), bh=(-7, -24), fang=0.0, bang=0.0,
              pf=None, pb=None, jig=0, head="calm", tails=0.0, knives=False, magic=None, strings=True,
              extra=None, extra_back=None, over=None, crosses=True):
    """Gaunt puppeteer in a black frock and crimson hood working two control bars. pf/pb: top of the
    front / back puppet (default: hanging under each bar)."""
    c = Canvas()
    o = Canvas()
    if extra_back: extra_back(c)
    hip = (dx, -14 + dy)
    T = Xf(lean, hip)
    shf, shb = T(hip[0] + 1.5, hip[1] - 12), T(hip[0] - 1.8, hip[1] - 12)
    fhx, fhy = fh[0] + dx, fh[1] + dy
    bhx, bhy = bh[0] + dx, bh[1] + dy
    pf = pf or (fhx + 1, -12)
    pb = pb or (bhx - 1, -13)
    # back puppet (behind everything) + its strings
    if pb is not False:
        hd, h1, h2 = mini_puppet(c, pb[0], pb[1], jig + 2, MWOOD_D, "E", knives, flip=False)
    # frock tails behind
    tl = [T(hip[0] - 3, hip[1] - 2), T(hip[0] + 1, hip[1] - 2), (hip[0] - 1.5 - tails * 0.6, hip[1] + 7),
          (hip[0] - 4.5 - tails, hip[1] + 6.5)]
    poly(c, tl, PUP_FROCK, bias=-0.1)     # v0.10: varnished walnut (the teller's plum went with the teller)
    # legs: long, striped hose
    for i, fx in enumerate(feet):
        hx_ = hip[0] + (-0.8 if i == 0 else 0.8)
        (kx, ky), (ax, ay) = ik(hx_, hip[1], dx + fx, -1, 7.0, 7.4, 1)
        tube(c, [(hx_, hip[1]), (kx, ky), (ax, ay)], [1.2, 1.0, 0.9], stripes(0, 2, "Kmm", "dDD", ang=90) if i else "Kmm")
        c.put(*P(ax, 0), "K"); c.put(*P(ax + 1, 0), "m"); c.put(*P(ax + 2, 0), "s" if i else "m"); c.put(*P(ax + 3, -1), "z" if i else "A")
    # back arm
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bhx, bhy + 1, 5.5, 5.5, -1)
    tube(c, [shb, (ex, ey), (hx, hy)], [1.0, 0.9, 0.7], "ktt")
    c.put(*P(hx, hy), "w")
    # frock + harlequin waistcoat
    tor = [T(hip[0] - 3.2, hip[1] - 1), T(hip[0] + 2.8, hip[1] - 1), T(hip[0] + 3.2, hip[1] - 12.5), T(hip[0] - 3.0, hip[1] - 12.5)]
    poly(c, tor, PUP_FROCK, bias=0.2)
    for sx, sy in ((-2.2, 3), (-1.5, 8), (1.2, 10)):          # brass ball-joint pins, like the Marionette's
        c.put(*P(*T(hip[0] + sx, hip[1] - sy)), "z")
    wc = [T(hip[0] + 0.2, hip[1] - 2), T(hip[0] + 2.6, hip[1] - 2), T(hip[0] + 2.9, hip[1] - 11.5), T(hip[0] + 0.4, hip[1] - 11.5)]
    poly(c, wc, harl(hip[0] + 1.5, hip[1] - 6, 3, CRIM, BLK, ang=lean), bias=0.2, lit="flat")
    for k in (3, 6, 9):
        c.put(*P(*T(hip[0] + 0.3, hip[1] - k)), "z")
    # ruff + hooded mask
    neck = T(hip[0] + 0.6, hip[1] - 13)
    ell(c, neck[0], neck[1] + 0.3, 3.8, 1.4, stripes(neck[0], 1, "hwWX", "hhww"), bias=0.2)
    c.part(PUPPETEER_HEAD[head], *P(neck[0], neck[1] - 0.5))
    # front arm
    (ex, ey), (hx2, hy2) = ik(shf[0], shf[1], fhx, fhy + 1, 5.5, 5.5, 1)
    tube(c, [shf, (ex, ey), (hx2, hy2)], [1.1, 1.0, 0.8], "tTh")
    c.put(*P(hx2, hy2), "W")
    # a spare carved doll head (the Marionette's) hung from the belt
    bcx, bcy = T(hip[0] - 1.2, hip[1] + 0.5)
    ell(c, bcx, bcy, 2.0, 2.2, MWOOD_L, bias=0.2)
    c.put(*P(bcx + 0.5, bcy - 0.5), "K"); c.put(*P(bcx + 1.5, bcy - 0.5), "K"); c.put(*P(bcx + 1, bcy + 1), "E")
    # control bars + strings
    if crosses:
        bb = control_cross(c, bhx, bhy, bang)
        fb = control_cross(c, fhx, fhy, fang)
    if pf is not False:
        hdf, f1, f2 = mini_puppet(c, pf[0], pf[1], jig, MWOOD_L, "K", knives, flip=False)
    if strings and crosses:
        def string(a, b):
            for (x, y) in line_px(*P(*a), *P(*b)):
                if (x, y) not in c.px: o.raw.put(x, y, "S")
        if pf is not False:
            string(fb[1], hdf); string(fb[0], f1); string(fb[2], f2)
        if pb is not False:
            string(bb[0], hd); string(bb[1], h2)
    if magic: magic(o)
    if extra: extra(c)
    return finish(c, o.spr())


def build_puppeteer(outdir):
    U = puppeteer
    idle = [U(fh=(9, -23 + [0, -1, 0, 0][i]), bh=(-7, -24 + [0, 0, -1, 0][i]), fang=[0, 10, -6, 4][i],
              bang=[0, -8, 6, -4][i], jig=i,
              pf=(10, -12 + [0, -1, 0, 1][i]), pb=(-8, -13 + [0, 1, 0, -1][i]), dy=[0, 0.4, 0, 0.4][i])
            for i in range(4)]
    stride = [(-6, 4), (-3, 2), (0, -1), (4, -6), (2, -3), (-1, 0)]
    run = [U(feet=stride[i], lean=6, dy=[0, -1, 0, 0, -1, 0][i], tails=2 + (i % 2), fh=(10, -23), bh=(-6, -24),
             pf=(9 - (i % 3), -12), pb=(-9 + (i % 3), -13), jig=i, fang=-10, bang=-10) for i in range(6)]
    # Dance: bars up (0), yanked back (1), thrown forward (2), the puppets LUNGE and stab (3), hang, reel in (4-6)
    dance = [U(fh=(6, -31), bh=(-4, -31), pf=(9, -17), pb=(-5, -18), jig=1, head="laugh"),
             U(lean=-6, fh=(2, -32), bh=(-7, -31), pf=(3, -19), pb=(-9, -18), jig=2, head="laugh", fang=-20, bang=-15),
             U(lean=6, fh=(10, -29), bh=(4, -30), pf=(14, -16), pb=(10, -17), jig=3, fang=25, bang=20),
             U(lean=10, fh=(12, -26), bh=(7, -27), pf=(19, -12), pb=(15, -13), jig=0, knives=True, fang=35, bang=30,
               head="laugh", extra_back=lambda c: speed_lines(c, 8, 13, (-9, -6), "s")),
             U(lean=8, fh=(11, -26), bh=(6, -27), pf=(17, -11), pb=(13, -12), jig=1, knives=True, fang=20, bang=20),
             U(lean=3, fh=(8, -27), bh=(-2, -28), pf=(11, -12), pb=(-2, -13), jig=2, fang=5),
             U(jig=3)]
    # Curtain Call: arms wide (0), bars overhead (1), the hands crackle (2), strings SHOOT out to every side (3),
    # taut (4), YANK (5), a deep bow (6), straighten (7-8)
    def fan_strings(srcs, n, r, ang0, ang1, bright=False):
        def f(o):
            for (sx, sy) in srcs:
                for k in range(n):
                    a = math.radians(ang0 + (ang1 - ang0) * k / max(1, n - 1))
                    tx, ty = sx + r * math.cos(a), sy + r * math.sin(a)
                    for i, (x, y) in enumerate(line_px(*P(sx, sy), *P(tx, ty))):
                        o.put(x, y, "L" if (bright and i % 3 == 0) else "N")
                    sparkle(o, tx, ty, 1, "N", "L")
        return f
    curtain = [U(fh=(10, -27), bh=(-9, -27), pf=(12, -12), pb=(-11, -13), jig=0),
               U(fh=(4, -33), bh=(-4, -33), pf=(6, -16), pb=(-6, -17), jig=2, head="laugh"),
               U(fh=(4, -34), bh=(-4, -34), pf=(6, -17), pb=(-6, -18), jig=3, head="laugh",
                 extra=lambda c: [sparkle(c, 4, -34, 1, "N", "L"), sparkle(c, -4, -34, 1, "N", "L")]),
               U(fh=(5, -34), bh=(-5, -34), pf=(6, -17), pb=(-6, -18), jig=1, head="laugh",
                 magic=fan_strings([(5, -36), (-5, -36)], 3, 14, -150, -30, True)),
               U(fh=(6, -33), bh=(-6, -33), pf=(6, -16), pb=(-6, -17), jig=2, head="laugh",
                 magic=fan_strings([(6, -35), (-6, -35)], 3, 16, -160, -20)),
               U(lean=-8, fh=(1, -32), bh=(-9, -30), pf=(3, -17), pb=(-10, -16), jig=0, head="laugh",
                 magic=fan_strings([(1, -34), (-9, -32)], 2, 9, -170, -110)),
               U(lean=40, dy=1, fh=(10, -14), bh=(-6, -22), pf=(12, -4), pb=(-7, -9), jig=1, fang=60, bang=30,
                 feet=(-4, 3)),
               U(lean=12, fh=(9, -22), bh=(-5, -26), pf=(11, -9), pb=(-6, -12), jig=2),
               U(jig=0)]
    d0 = U(lean=-12, fh=(6, -31), bh=(-8, -30), head="laugh", pf=(8, -10), pb=(-9, -11), jig=3, strings=False, fang=40,
           bang=-40)
    d1 = U(lean=-6, dy=6, fh=(7, -15), bh=(-6, -16), head="dead", pf=(10, -4), pb=(-10, -5), jig=2, strings=False,
           crosses=False, feet=(-6, 6))
    d2 = grounded(rot_spr(U(head="dead", strings=False, crosses=False, pf=False, pb=False, fh=(6, -18), bh=(-5, -19)),
                          -70, (0, -2)))
    corpse = puppeteer_corpse()
    knock = U(lean=-16, dx=-1.5, fh=(5, -32), bh=(-9, -30), pf=(6, -15), pb=(-11, -15), jig=2, head="laugh", fang=-30,
              bang=-25, feet=(-2, 5))
    anims = [("Idle", idle, [0.2, 0.14, 0.2, 0.14]), ("Run", run, [0.085] * 6),
             ("Dance", dance, [0.14, 0.12, 0.06, 0.08, 0.1, 0.12, 0.14]),
             ("Curtain", curtain, [0.12, 0.12, 0.1, 0.06, 0.1, 0.1, 0.24, 0.12, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.14, 0.14, 0.5], knock)
    return sheet("JinxPuppeteer", anims, outdir, scale=4)


def puppeteer_corpse():
    body = puppeteer(head="dead", strings=False, crosses=False, pf=False, pb=False, fh=(5, -17), bh=(-4, -18))
    lying = grounded(rot_spr(body, -90, (0, -2)))
    c = Canvas(); c.px = dict(lying.px)
    control_cross(c, 16, -2, 20)
    mini_puppet(c, -20, -9, 2, CRIM, "K")
    return grounded(floor_cut(finish(c, cut=False)))


# ================================================================== v0.7.2 tree: ONE-ARMED BANDIT (T3, slot machine)
REEL_SYM = {   # 3 x 4 symbols drawn in the reel windows
    "cherry": [".e.", "e.e", "Ef.", ".fE"],
    "bell": [".z.", "zZz", "zZz", "AeA"],
    "seven": ["EEf", "..E", ".E.", ".E."],
    "skull": ["XWX", "KXK", "XWX", "W.W"],
    "blur1": ["sSs", "wsw", "sSs", "wsw"],
    "blur2": ["wsw", "sSs", "wsw", "sSs"],
}


def slot_reels(c, x, y, syms, flash=False):
    """Three reel windows (top-left (x, y)), each 3 x 4 px with a dark frame."""
    for k, sname in enumerate(syms):
        wx = x + k * 4
        for j in range(4):
            for i in range(3):
                ch = REEL_SYM[sname][j][i]
                c.put(wx + i, y + j, ("y" if flash else "X") if ch == "." else ch)
        if k < 2:
            for j in range(4): c.put(wx + 3, y + j, "K")


def bandit(dx=0.0, dy=0.0, lean=0.0, legs=((-4, 0), (3, 0)), knob=(13, -31), reels=("cherry", "bell", "seven"),
           bulbs=0, mouth=0, flash=False, sq=0.0, coins=(), sparks=False, crack=False, eyes=True, extra=None,
           extra_back=None, over=None):
    """Living slot machine on stubby claw feet. knob: lever ball position (the lever pivots on the right side)."""
    c = Canvas()
    if extra_back: extra_back(c)
    bot = -5.0 + dy
    top = -26.0 + dy + sq
    x0, x1 = -8.0 + dx, 7.0 + dx
    D = 3
    sh = lambda x, y: (x + lean * (bot - y) / 20.0, y)
    # stubby gold claw-and-ball legs
    for i, (lx, ly) in enumerate(legs):
        hx_ = dx + (-4.5 if i == 0 else 3.5)
        fx, fy = hx_ + lx * 0.6, ly
        tube(c, [(hx_, bot), (fx, fy - 1.5)], [1.6, 1.3], GOLD if i else "AAee", bias=0.1)
        ell(c, fx + 0.5, fy - 1.0, 2.0, 1.1, "AezZ" if i else "AAez", bias=0.1)
        c.put(*P(fx + 2.5, fy), "K"); c.put(*P(fx - 1.5, fy), "K")
    # lever (behind the side face): pivot hub, rod, red ball
    pv = sh(x1 + D + 0.5, (top + bot) / 2.0 - 2)
    # v0.10 lineage (one parent, the Fortune Teller): a gold rod wound with her crimson shawl, coins on the fringe
    tube(c, [pv, knob], [1.2, 1.0], stripes(0, 2, "dDEf", "AezZ", ang=-60), bias=0.2)
    c.put(*P(pv[0], pv[1]), "z")
    # side face, front face, top
    side = [sh(x1, top), sh(x1 + D, top - D), sh(x1 + D, bot - D), sh(x1, bot)]
    poly(c, side, "dDDD", lit="flat", bias=0.0)
    front = [sh(x0, top), sh(x1, top), sh(x1, bot), sh(x0, bot)]
    poly(c, front, CRIM, bias=0.3)
    topf = [sh(x0, top), sh(x1, top), sh(x1 + D, top - D), sh(x0 + D, top - D)]
    poly(c, topf, "Ddff", lit="flat", bias=0.2)
    # marquee arch with chasing bulbs
    mq = [(sh(x0 + 1, top)[0] + 6.5 + 7 * math.cos(math.radians(a)), top - 0.5 - 4 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
    poly(c, mq, harl(dx, top - 2, 3, "Kmmm", "dDDE"), lit="flat", bias=0.1)
    for k, (bx, by) in enumerate(mq[::2]):
        c.put(*P(bx, by), "Y" if (k + bulbs) % 2 == 0 else ("y" if flash else "e"))
    c.put(*P(sh(x0, top)[0] + 7.5, top - 3), "y" if flash else "Y")
    # gold trim
    line(c, *sh(x0, top), *sh(x1, top), "z")
    line(c, *sh(x0, bot), *sh(x1, bot), "A")
    line(c, *sh(x0, top), *sh(x0, bot), "e")
    line(c, *sh(x1, top), *sh(x1, bot), "A")
    line(c, *sh(x1, bot), *sh(x1 + D, bot - D), "A")
    # reel band (the "eyes")
    rx, ry = sh(x0 + 1.5, top + 3)
    for i in range(-1, 13):
        c.put(*P(rx + i, ry - 1), "K"); c.put(*P(rx + i, ry + 4), "K")
    c.put(*P(rx - 1, ry + 1), "K"); c.put(*P(rx - 1, ry + 2), "K"); c.put(*P(rx + 12, ry + 1), "K"); c.put(*P(rx + 12, ry + 2), "K")
    if eyes:
        slot_reels(c, int(round(rx)), int(round(ry)), reels, flash)
    else:
        for i in range(12):
            for j in range(4):
                if flash: ch = "K" if i in (3, 7) else ("y" if (i + j) % 3 else "Y")
                else: ch = "K" if (i + j) % 3 else "s"
                c.put(*P(rx + i, ry + j), ch)
    # payout tray grin with gold teeth
    mx, my = sh(x0 + 2.5, top + 11)
    poly(c, [(mx, my), (mx + 10, my), (mx + 9, my + 3 + mouth), (mx + 1, my + 3 + mouth)], "K", lit="flat")
    for k in range(5):
        c.put(*P(mx + 1 + k * 2, my), "Z" if k % 2 else "z")
        if mouth: c.put(*P(mx + 2 + k * 2, my + 2 + mouth), "z")
    # harlequin skirt panel
    pn = [sh(x0 + 1, bot - 4), sh(x1 - 1, bot - 4), sh(x1 - 1, bot - 1), sh(x0 + 1, bot - 1)]
    poly(c, pn, harl(dx, bot - 2.5, 3, "Kmms", "ddDE"), lit="flat")
    # coin slot on the side
    a = sh(x1 + 1.5, top + 6); c.put(*P(*a), "K"); c.put(*P(a[0], a[1] + 1), "K")
    if crack:
        for x, y in ((2, 0), (3, 1), (3, 2), (4, 3)):
            c.put(*P(rx + x, ry + y), "W")
    # the knob last: v0.9 the Fortune Teller's crystal ball (was a red ball)
    crystal_ball(c, knob[0], knob[1], 2.6, int(knob[1]) % 5, 1)
    o = Canvas()
    for (cx_, cy_) in coins:
        o.put(*P(cx_, cy_), "Z"); o.put(*P(cx_ + 1, cy_), "z")
    if sparks:
        for sx, sy in sparks if isinstance(sparks, (list, tuple)) else ():
            sparkle(o, sx, sy, 1, "Y", "y")
    if extra: extra(c)
    s_ = finish(c, o.spr())
    if over: s_ = merge(s_, over)
    return s_


def build_bandit(outdir):
    B = bandit
    reel_idle = [("cherry", "bell", "seven"), ("bell", "seven", "skull"), ("seven", "skull", "cherry"),
                 ("skull", "cherry", "bell")]
    idle = [B(bulbs=i, reels=reel_idle[i], knob=(13 + [0, 0.5, 1, 0.5][i], -31 + [0, 0.5, 0, -0.5][i]),
              dy=[0, 0.4, 0.4, 0][i], sq=[0, 0.3, 0.3, 0][i]) for i in range(4)]
    run_legs = [((-6, 0), (5, -1)), ((-4, -1), (3, 0)), ((-1, 0), (1, 0)), ((2, -1), (-3, 0)), ((0, 0), (-1, -1)),
                ((-3, 0), (2, 0))]
    run = [B(legs=run_legs[i], dy=[0, -1, 0, 0, -1, 0][i], lean=[1, 2, 1, 1, 2, 1][i], bulbs=i,
             knob=(12 - (i % 3) * 0.5, -31 + (i % 2)), reels=reel_idle[i % 4]) for i in range(6)]
    # Slam: the lever cranks back (0-1), swings over the top (2), SLAMS the floor ahead (3), rebounds (4-6)
    slam = [B(knob=(8, -35), lean=-1, reels=("seven", "seven", "seven"), bulbs=0),
            B(knob=(1, -36), lean=-2, reels=("skull", "skull", "skull"), bulbs=1, sq=-0.5),
            B(knob=(17, -31), lean=1, reels=("skull", "skull", "skull"), bulbs=0),
            B(knob=(20, -3), lean=3, sq=1, reels=("skull", "skull", "skull"), bulbs=1, mouth=1,
              coins=((16, -6), (23, -8), (25, -4)), sparks=((22, -1), (18, -1))),
            B(knob=(20, -5), lean=2, sq=0.5, reels=("seven", "skull", "seven"), coins=((17, -9), (25, -7))),
            B(knob=(17, -18), lean=1, reels=("cherry", "skull", "bell")),
            B(knob=(13, -30), reels=reel_idle[0])]
    # Jackpot: grab the lever (0), PULL it down (1), the reels start (2), spin (3-6), stop on a flash (7),
    # the tray spews coins (8: resolve the reels), settle (9)
    jp = [B(knob=(14, -28), bulbs=0),
          B(knob=(15, -16), bulbs=1, sq=0.5, reels=("blur1", "blur2", "blur1")),
          B(knob=(14, -22), bulbs=0, reels=("blur2", "blur1", "blur2")),
          B(knob=(13, -27), bulbs=1, reels=("blur1", "blur2", "blur1"), dy=-0.5),
          B(knob=(13, -30), bulbs=0, reels=("blur2", "blur1", "blur2")),
          B(knob=(13, -30), bulbs=1, reels=("blur1", "blur2", "blur1"), dy=-0.5),
          B(knob=(13, -31), bulbs=0, reels=("cherry", "blur1", "blur2")),   # v0.8: the first reel clicks to a stop (was a copy of 4)
          B(knob=(13, -31), bulbs=1, flash=True, eyes=False),
          B(knob=(13, -31), bulbs=0, flash=True, mouth=2, eyes=False,
            coins=((12, -12), (15, -10), (13, -7), (18, -8), (10, -4), (20, -5))),
          B(knob=(13, -31), bulbs=1, mouth=1, coins=((14, -1), (19, -1)), eyes=False)]
    d0 = B(knob=(5, -36), lean=-2, crack=True, reels=("skull", "skull", "skull"), mouth=1, sparks=((-4, -28), (9, -22)))
    d1 = grounded(rot_spr(B(knob=(-3, -30), crack=True, reels=("skull", "blur1", "skull"), mouth=2), -25, (0, -1)))
    d2 = grounded(rot_spr(B(knob=(-8, -24), crack=True, eyes=False, mouth=2), -70, (-6, -1)))
    corpse = bandit_corpse()
    knock = B(knob=(4, -35), lean=-3, sq=-0.5, reels=("blur1", "blur2", "blur1"), mouth=1, legs=((-5, 0), (5, -1)))
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.09] * 6),
             ("Slam", slam, [0.16, 0.14, 0.06, 0.08, 0.1, 0.12, 0.14]),
             ("Jackpot", jp, [0.12, 0.1, 0.06, 0.06, 0.06, 0.06, 0.06, 0.12, 0.2, 0.16])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.14, 0.16, 0.5], knock)
    return sheet("JinxBandit", anims, outdir, scale=4)


def bandit_corpse():
    body = bandit(knob=(-6, -24), crack=True, eyes=False, mouth=2)
    lying = grounded(rot_spr(body, -90, (-6, -1)))
    o = Canvas()
    for x in (-18, -15, 12, 14, 17, 20):
        o.put(x, 0, "Z"); o.put(x + 1, 0, "z")
    return grounded(floor_cut(merge(Spr(lying.px), o.spr())))


# ================================================================== v0.7.2 tree: FX
TAROT = {
    "Tower": """
...S...
..SSS..
.SyS.S.
.SSyS..
.S.SyS.
.SSSSS.
SSSSSSS
""",
    "Fool": """
E.....m
EE...mm
.EE.mm.
..EZm..
.XXXXX.
.XKXKX.
..XKX..
""",
    "Star": """
...Z...
...Z...
ZZZyZZZ
.ZyyyZ.
..ZZZ..
.Z...Z.
Z.....Z
""",
}


def tarot_face(c, cx, cy, kind, sx=1.0, glow=False):
    hw, hh = max(0.5, 5 * sx), 7
    poly(c, [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)], "WXXX", lit="flat", bias=0.3)
    if hw > 2:
        line(c, cx - hw + 1, cy - hh + 1, cx + hw - 1, cy - hh + 1, "E"); line(c, cx - hw + 1, cy + hh - 1, cx + hw - 1, cy + hh - 1, "E")
    if sx < 0.9:
        if hw > 1: c.put(*P(cx, cy), "E")
        return
    rows = TAROT[kind].strip("\n").split("\n")
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != ".": c.put(int(cx) + i - 3, int(cy) + j - 4, ch)
    if glow:
        for k in range(6):
            a = math.radians(30 + 60 * k)
            c.put(*P(cx + (hw + 2) * math.cos(a), cy + (hh + 1) * math.sin(a)), "Z" if kind == "Star" else "L")


def card_burst(cy, w, h, seed, frag=("X", "W", "w"), spark=("Z", "L")):
    """v0.10: a card bursting apart (drawn, replaces the old random-pixel dissolve): four outlined fragments of the card
    tumble outward from its centre (0, cy) inside a ring of four-point sparkles."""
    c = Canvas()
    r = random.Random(seed)
    for k, (fx, fy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        ox, oy = fx * (w * 0.45 + 2), fy * (h * 0.4 + 2) - 1
        fw, fh = 2 + (k % 2), 3 - (k // 2)
        for x in range(fw):
            for y in range(fh):
                c.raw.put(int(ox) + x - fw // 2, int(cy + oy) + y - fh // 2, frag[(x + y + k) % len(frag)])
    sp = outline(Spr(dict(c.px)))
    o = Canvas()
    for k in range(6):
        a = math.radians(k * 60 + 30 + r.uniform(-10, 10))
        d = w * 0.75 + 2
        x, y = int(round(d * math.cos(a))), int(round(cy + d * 0.9 * math.sin(a)))
        ch = spark[k % len(spark)]
        o.raw.put(x, y, "y" if k % 2 == 0 else ch)
        for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            o.raw.put(x + dx_, y + dy_, ch)
    return merge(sp, Spr(dict(o.px)))


def fx_tarot_frames(kind):
    out = []
    for i, (sx, glow) in enumerate(((0.15, False), (0.6, False), (1.0, True), (1.0, False))):
        c = Canvas()
        tarot_face(c, 0, -12, kind, sx=sx, glow=glow)
        sp = outline(c.spr(), skip=("Z", "L"))
        if i == 3: sp = card_burst(-12, 8, 12, 7, frag=("X", "W", "z"), spark=("Z", "L"))   # v0.10: a drawn burst
        out.append(sp)
    return out


def fx_orb_frames():
    out = []
    for i in range(4):
        c = Canvas()
        crystal_ball(c, 0, -4, 2.6, i, 1)
        sp = outline(c.spr())
        o = Canvas()
        for k in range(3):
            o.put(-4 - k * 2, -4 + ((k + i) % 3) - 1, "L" if k == 0 else "N")
        out.append(merge(o.spr(), sp))
    return out


def fx_fate_mark_frames():
    out = []
    arc = [0.0, 0.4, 0.8, 1, 1, 1, 1, 1, 1, 1]
    for i in range(10):
        c = Canvas()
        n = int(36 * arc[i])
        for k in range(n):
            a = 2 * math.pi * k / 36
            c.put(*P(9 * math.cos(a), -3.5 + 3.5 * math.sin(a)), "L" if (k + i) % 4 == 0 else "N")
        if arc[i] >= 1:
            pts = [(9 * math.cos(math.radians(90 + 144 * k)), -3.5 + 3.5 * math.sin(math.radians(90 + 144 * k))) for k in range(6)]
            for a_, b_ in zip(pts, pts[1:]):
                line(c, *a_, *b_, "n" if i < 8 else "N", over=False)
        if i == 0:
            sparkle(c, 0, -3, 1, "N", "L")
        sp = c.spr()
        o = Canvas()
        if 2 <= i <= 8:
            sx = [1.0, 0.8, 0.4, 0.8, 1.0, 0.6, 0.15][i - 2]
            bob = [0, -1, -1, 0, 0, -1, -1][i - 2]
            card_face(o, 0, -15 + bob, 8, 11, "back", sx=sx)
            cs = outline(o.spr())
            sp = merge(sp, cs)
        if i == 9:
            fl = Canvas()
            sparkle(fl, 0, -8, 2, "L", "y")
            for k in range(6):
                a = math.radians(k * 60)
                fl.put(*P(6 * math.cos(a), -8 + 5 * math.sin(a)), "N")
            sp = merge(sp, fl.spr())
        out.append(floor_cut(sp))
    return out


def fx_coin_frames():
    out = []
    for i, sx in enumerate((1.0, 0.6, 0.2, 0.6)):
        c = Canvas()
        ell(c, 0, -4, max(0.6, 2.3 * sx), 2.3, GOLD, bias=0.2)
        if sx > 0.5: c.put(0, -4, "A"); c.put(-1, -5, "Z")
        if i == 3: c.put(1, -5, "Z")                  # v0.8: the coin's back face catches the light (frame 3 was a copy of 1)
        sp = outline(c.spr())
        o = Canvas(); o.put(-4, -4 + (i % 2), "z"); o.put(-6, -4, "e")
        out.append(merge(o.spr(), sp))
    return out


def fx_reel_frames(sym):
    """One reel window (gold frame, ivory face) with the symbol drawn at 2x; frame 0 pops up with a glint."""
    out = []
    for i in range(2):
        c = Canvas()
        up = 2 if i == 0 else 0
        top = -11 - up
        poly(c, [(-4, top - 1), (3, top - 1), (3, top + 9), (-4, top + 9)], "AezZ", lit="flat", bias=0.2)
        poly(c, [(-3, top), (2, top), (2, top + 8), (-3, top + 8)], "X", lit="flat")
        for j, r in enumerate(REEL_SYM[sym]):
            for k, ch in enumerate(r):
                if ch == ".": continue
                for ax in range(2):
                    for ay in range(2):
                        c.put(-3 + k * 2 + ax, top + j * 2 + ay, ch)
        sp = outline(c.spr())
        if i == 0:
            sp = merge(sp, Spr({(-6, top + 1): "Z", (5, top): "y", (5, top + 7): "Z"}))
        out.append(sp)
    return out


def fx_fire_ring_frames():
    out = []
    spec = [(6, 1, 2.0), (12, 2, 4.0), (14, 4, 4.5), (14, 3, 4.5), (14, 4, 4.5), (14, 3, 4.5), (14, 2, 4.5), (14, 1, 4.5)]
    for i, (rx, k, ry) in enumerate(spec):
        c = Canvas()
        fire_ring(c, 0, rx, k, ry=ry, seed=i)
        sp = c.spr()
        if i == 7: sp = dissolve(sp, 0.6, 3)
        if i == 0:
            fl = Canvas(); sparkle(fl, 0, -2, 2, "O", "y"); sp = merge(sp, fl.spr())
        out.append(floor_cut(sp))
    return out


EVENTS.update({
    "JinxFortuneTeller": {"Gaze": [("bolt release (FxOrb) at (13, -12)", 3)],
                          "Foretell": [("card flung: fate mark spawns under the hero", 4)]},
    "JinxSnakeEyes": {"Strike": [("bite hit, jaws (16-22, -6..-9)", 3)],
                      "Craps": [("dice flicked: two dice roll from (12, 1)", 3)]},
    "JinxChimera": {"Maul": [("claw rake hit (15-24, -2..-9), +2 lunge", 3)],
                    "Leap": [("spring: airborne, invulnerable", 2), ("lands: fire ring at (1, 0)", 5)]},
    "JinxPuppeteer": {"Dance": [("puppets stab (15-23, -4..-13)", 3)],
                      "Curtain": [("strings shoot out: allies hauled in", 3), ("bow", 6)]},
    "JinxBandit": {"Slam": [("lever knob hits the floor at (20, -3)", 3)],
                   "Jackpot": [("lever pulled", 1), ("reels spin", 2), ("reels stop", 7), ("payout: resolve the reels", 8)]},
})


NEW_FX = ["FxTarot", "FxOrb", "FxFateMark", "FxCoin", "FxReel", "FxFireRing"]
FX_NAMES += NEW_FX


def build_new_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxTarot"):
        fx_sheet("FxTarot", [(k, fx_tarot_frames(k), [0.05, 0.05, 0.3, 0.15]) for k in ("Tower", "Fool", "Star")], outdir)
    if want("FxOrb"): fx_sheet("FxOrb", [("Fly", fx_orb_frames(), [0.06] * 4)], outdir)
    if want("FxFateMark"):
        fx_sheet("FxFateMark", [("Play", fx_fate_mark_frames(), [0.06, 0.08, 0.08, 0.12, 0.12, 0.12, 0.12, 0.12, 0.1, 0.1])], outdir)
    if want("FxCoin"): fx_sheet("FxCoin", [("Fly", fx_coin_frames(), [0.05] * 4)], outdir)
    if want("FxReel"):
        fx_sheet("FxReel", [(n, fx_reel_frames(k), [0.08, 0.5]) for n, k in
                            (("Cherry", "cherry"), ("Bell", "bell"), ("Skull", "skull"), ("Seven", "seven"))], outdir)
    if want("FxFireRing"):
        fx_sheet("FxFireRing", [("Play", fx_fire_ring_frames(), [0.06, 0.08, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])], outdir)


FX_NOTES.update({
    "FxTarot": "Anims Tower / Fool / Star (4 frames, 0.55 s): the card flips face-up over the fate mark (0-1), face + "
               "glow (2), fades (3). Card centre 12 px above the origin.",
    "FxOrb": "Fly loop, faces right: the Fortune Teller's crystal bolt (orb 4 px above the origin, violet trail).",
    "FxFateMark": "Play once (1.12 s): sigil draws itself on the floor (0-2), a face-down card hovers and spins over it "
                  "(2-8), flash (9). The fate resolves at 1.0 s (frame 9 starts at 1.02 s). Ring 18 x 7 px.",
    "FxCoin": "Fly loop, faces right: spinning gold coin 4 px above the origin.",
    "FxReel": "Anims Cherry / Bell / Skull / Seven (2 frames): one reel result popping up over the Bandit.",
    "FxFireRing": "Play once (1.34 s): flames burst out (0-1), a 28 x 9 ring burns (2-6), embers (7).",
})


NEW_JOBS = [("JinxFortuneTeller", build_teller), ("JinxSnakeEyes", build_snake_eyes), ("JinxChimera", build_chimera),
            ("JinxPuppeteer", build_puppeteer), ("JinxBandit", build_bandit)]


# >>> v0.10 tree
# ================================================================== v0.10 tree (3 -> 6 -> 12, every evolution has ONE parent)
# All sheets in this section are drawn at their final size (no ArtScale entry).
#   CardSharp   -> JinxFortuneTeller, JinxCardSoldier      DiceImp -> JinxSnakeEyes, JinxLoadedDie
#   JinxCardSoldier -> JinxCardKing, JinxHouseOfCards      JinxLoadedDie -> JinxHighRoller, JinxTwenty
#   Marionette  -> JinxPuppeteer, JinxNutcracker           JinxFortuneTeller -> JinxBandit, JinxOracle
#   JinxSnakeEyes -> JinxGorgon, JinxRattler               Ringmaster -> JinxChimera, GrandJester
HOSE = "Kmms"


def glyph_px(c, rows, x, y, cmap):
    """Hand-drawn glyph (list of strings) with its centre at (x, y); cmap maps grid chars to palette chars."""
    h, w = len(rows), len(rows[0])
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in cmap: c.put(*P(x + i - w // 2, y + j - h // 2), cmap[ch])


SPADE_BLADE = ["..s..", ".sKK.", "sKKKK", "mKKKm", ".mKm.", "..K.."]


def spade_blade(c, x, y, ang):
    """Black spade-shaped pike head whose socket is at (x, y), pointing along ang (deg)."""
    a = math.radians(ang + 90); ca, sa = math.cos(a), math.sin(a)
    for j, r in enumerate(SPADE_BLADE):
        for i, ch in enumerate(r):
            if ch == ".": continue
            u, v = i - 2, j - len(SPADE_BLADE)       # v < 0: towards the point
            c.put(*P(x + u * ca - v * sa, y + u * sa + v * ca), ch)


def pike(c, hx, hy, ang, fwd=12.0, back=5.0):
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    a = (hx - ux * back, hy - uy * back); b = (hx + ux * fwd, hy + uy * fwd)
    line(c, *a, *b, "t")
    line(c, a[0] - uy * 0.6, a[1] + ux * 0.6, hx - uy * 0.6, hy + ux * 0.6, "h", over=False)
    c.put(*P(*a), "z")
    for k in (0.55, 0.8):
        c.put(*P(hx + ux * fwd * k, hy + uy * fwd * k), "T")
    spade_blade(c, b[0] + ux * 0.5, b[1] + uy * 0.5, ang)
    # crimson tassel under the blade
    c.put(*P(b[0] - ux * 1.5 + uy * 1.2, b[1] - uy * 1.5 - ux * 0.0 + 1.2), "E")
    c.put(*P(b[0] - ux * 1.5 + uy * 1.2, b[1] - uy * 1.5 + 2.2), "D")
    return b


# ------------------------------------------------------------------ CARD SOLDIER (T2, Card Sharp's): a goblin in a
# Knave-of-Clubs playing card worn as a sandwich board, the Card Sharp's green visor on its head, a spade-bladed pike
def card_soldier(dx=0.0, dy=0.0, lean=0.0, feet=(-2, 2), head="grin", hd=(0, 0), fh=(6, -11), bh=(-5, -9),
                 pa=-48.0, pf=9.0, pb=5.0, pike_on=True, flip=1.0, kind="Clubs", extra=None, extra_back=None, over=None,
                 knee=(1, 1)):
    c = Canvas()
    if extra_back: extra_back(c)
    hip = (dx, -4.5 + dy)
    T = Xf(lean, hip)
    # back arm (behind the board)
    shb = T(hip[0] - 3.5, hip[1] - 9.5)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 3.2, 3.2, -1)
    tube(c, [shb, (ex, ey), (hx, hy)], [0.9, 0.8, 0.7], "QQI")
    c.put(*P(hx, hy), "I")
    # legs: crimson-and-black striped hose, black pointed shoes
    for i, fx in enumerate(feet):
        hp = (hip[0] + (-1.2 if i == 0 else 1.2), hip[1])
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], dx + fx, -1, 2.4, 2.6, knee[i])
        tube(c, [hp, (kx, ky), (ax, ay)], [1.0, 0.9, 0.8], stripes(0, 1, CRIM, BLK, ang=90) if i else "Kmm")
        c.put(*P(ax, 0), "K"); c.put(*P(ax + 1, 0), "m"); c.put(*P(ax + 2, 0), "s" if i else "m")
        c.put(*P(ax + 2, -1), "K")
    # the board: a big playing card with a cardboard edge showing on its right
    bc = T(hip[0], hip[1] - 6.5)
    w = 10 * flip
    card_face(c, bc[0] + 1, bc[1] + 0.5, abs(w), 11.5, "back")
    card_face(c, bc[0], bc[1], abs(w), 11.5, kind if flip > 0.75 else "back", sx=1.0)
    # crimson ruff collar on top of the board
    rc = T(hip[0] + 0.5, hip[1] - 12)
    for k in range(-3, 4):
        c.put(*P(rc[0] + k, rc[1] - (k % 2)), "E" if k % 2 else "f")
        c.put(*P(rc[0] + k, rc[1] + 1 - (k % 2)), "D")
    # goblin head with the green dealer visor
    neck = T(hip[0] + 1.5, hip[1] - 12.5)
    c.part(SHARP_HEAD[head], *P(neck[0] + hd[0], neck[1] + hd[1]))
    # front arm + pike
    shf = T(hip[0] + 4.5, hip[1] - 9.5)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 3.2, 3.2, 1)
    if pike_on:
        pike(c, hx, hy, pa, pf, pb)
    tube(c, [shf, (ex, ey)], [1.0, 0.9], "QIj")
    line(c, ex, ey, hx, hy, "I")
    c.put(*P(hx, hy), "j"); c.put(*P(hx, hy + 1), "I")
    if extra: extra(c)
    return finish(c, over)


def build_card_soldier(outdir):
    S = card_soldier
    idle = [S(), S(dy=0.3, fh=(6, -10.5), pa=-46), S(dy=0.3, fh=(6, -10.5), pa=-45, head="leer"), S(pa=-49, fh=(6, -11))]
    stride = [(-4, 3), (-2, 1), (0, -1), (3, -4), (1, -2), (-1, 0)]
    run = [S(feet=stride[i], lean=8, dy=[0, -0.7, 0, 0, -0.7, 0][i], fh=(7, -10 + (i % 2) * 0.5), pa=-14,
             bh=(-6 + (i % 3), -8), head="grin") for i in range(6)]
    # Thrust: draw the pike back (0-1), step in (2), THRUST at full reach (3: the spade at x 21..27), hold, recover
    thrust = [S(lean=-6, fh=(2, -11), pa=-12, feet=(-3, 2), head="leer"),
              S(lean=-10, fh=(0, -11), pa=-6, feet=(-3, 2), head="leer"),
              S(lean=8, fh=(7, -10), pa=-2, feet=(-3, 4), pf=13),
              S(lean=16, dx=1, fh=(11, -9), pa=0, feet=(-3, 6), pf=13,
                extra_back=lambda c: [line(c, 3, -12, 10, -12, "s"), line(c, 5, -7, 11, -7, "s")]),
              S(lean=14, dx=1, fh=(10, -9), pa=0, feet=(-3, 6), pf=13),
              S(lean=6, fh=(7, -10), pa=-10, feet=(-2, 4)),
              S(fh=(6, -11), pa=-24)]

    def fan3(cx, cy, spread, ang0=-90, face=False):
        def f(c):
            for k in range(3):
                a = ang0 + (k - 1) * spread
                card(c, cx + 2.5 * math.cos(math.radians(a)), cy + 2.5 * math.sin(math.radians(a)), 2.6, 3.6,
                     face=face, ang=a + 90)
        return f
    # Deal (special): tuck the pike, pull three cards from behind the board (0-1), fan them (2), FLICK them at the
    # hero's feet (3: the traps), follow through, take the pike back
    deal = [S(lean=-4, bh=(-3, -17), pa=-70, fh=(5, -12), pf=10, head="leer"),
            S(lean=-8, bh=(-2, -20), pa=-75, fh=(5, -12), pf=10, head="leer", extra=fan3(-2, -22, 25)),
            S(lean=-10, bh=(-4, -19), pa=-75, fh=(5, -12), pf=10, head="grin", extra=fan3(-4, -21, 35, -110)),
            S(lean=12, bh=(9, -12), pa=-60, fh=(5, -12), pf=10, head="grin",
              extra=lambda c: [card(c, 14, -15, 2.6, 3.6, False, 60), card(c, 16, -10, 2.6, 3.6, False, 80),
                               card(c, 13, -6, 2.6, 3.6, False, 110), line(c, 9, -12, 11, -13, "w")]),
            S(lean=10, bh=(8, -9), pa=-50, fh=(5, -12), pf=10),
            S(lean=4, bh=(-3, -9), pa=-35, fh=(6, -11)),
            S(fh=(6, -11), pa=-28)]
    d0 = S(lean=-14, fh=(4, -14), bh=(-7, -14), pa=-80, head="dead", feet=(-3, 2))
    d1 = grounded(rot_spr(S(lean=-6, fh=(3, -10), bh=(-6, -10), pike_on=False, head="dead", feet=(-2, 2)), -50, (0, -1)))
    d2 = grounded(rot_spr(S(lean=-4, fh=(3, -9), bh=(-6, -9), pike_on=False, head="dead", feet=(-2, 2)), -86, (0, -1)))
    corpse = soldier_corpse()
    knock = S(lean=-16, dx=-1, fh=(3, -13), bh=(-7, -12), pa=-60, head="leer", feet=(-1, 3))
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.075] * 6),
             ("Thrust", thrust, [0.14, 0.12, 0.06, 0.1, 0.1, 0.12, 0.12]),
             ("Deal", deal, [0.12, 0.12, 0.1, 0.06, 0.1, 0.12, 0.12])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxCardSoldier", anims, outdir, scale=6)


def soldier_corpse():
    body = card_soldier(lean=0, fh=(3, -9), bh=(-6, -9), pike_on=False, head="dead", feet=(-1, 1))
    lying = grounded(rot_spr(body, -90, (0, -1)))
    c = Canvas(); c.px = dict(lying.px)
    o = Canvas()
    pike(o, 2, -1, 180, 9, 6)
    return grounded(floor_cut(merge(Spr(c.px), outline(o.spr()))))


# ------------------------------------------------------------------ LOADED DIE (T2, Dice Imp's): the imp has become
# its die: an ivory cube with a grinning face on its front, the imp's horns, bat wings, crimson legs and belled tail
def face_die(c, cx, cy, size, rx=0.0, ry=50.0, rz=0.0, ramp=IVORY, face="grin", face_n=(1, 0, 0), pip="K",
             glow_pip=None, edge_gold=False):
    """die() with a face (eyes + grin) on the face whose normal is face_n; the other faces keep their pips.
    Returns the screen centre and (u, v) axes of the face, or None when it is turned away."""
    h = size / 2.0
    Lv = (-0.5, -0.58, -0.64)
    xf = lambda v: rot3(rot3(v, rx, ry, rz), CAM_TILT, 0, 0)
    faces = []
    for n, val in CUBE_FACES:
        nn = xf(n)
        if nn[2] >= -0.05: continue
        if n[0]: e1, e2 = (0, 0, 1), (0, 1, 0)
        elif n[1]: e1, e2 = (1, 0, 0), (0, 0, 1)
        else: e1, e2 = (1, 0, 0), (0, 1, 0)
        pts = []
        for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            w = xf(tuple(h * (n[k] + su * e1[k] + sv * e2[k]) for k in range(3)))
            pts.append((cx + w[0], cy + w[1]))
        lam = nn[0] * Lv[0] + nn[1] * Lv[1] + nn[2] * Lv[2]
        faces.append((lam, pts, lam * 2.0 - 0.25, val, n, e1, e2, nn))
    faces.sort(key=lambda f: f[0])
    info = None
    for lam, pts, l, val, n, e1, e2, nn in faces:
        poly(c, pts, ramp, bias=l, lit="flat")
        ei = max(0, ramp.index(pick(ramp, l)) - 1)
        cxp = sum(p[0] for p in pts) / 4.0; cyp = sum(p[1] for p in pts) / 4.0
        for a_, b_ in zip(pts, pts[1:] + pts[:1]):
            if (a_[0] + b_[0]) / 2 - cxp + (a_[1] + b_[1]) / 2 - cyp > 0.3:
                line(c, *a_, *b_, "z" if edge_gold else ramp[ei])
    for lam, pts, l, val, n, e1, e2, nn in faces:
        if abs(nn[2]) * size < 2.2: continue
        def at(u, v):
            w = xf(tuple(h * (n[j] + u * e1[j] + v * e2[j]) for j in range(3)))
            return cx + w[0], cy + w[1]
        if tuple(n) == tuple(face_n):
            info = (at, nn)
            draw_die_face(c, at, face, nn)
            continue
        for (pu, pv) in PIPS[val]:
            ch = glow_pip if (glow_pip and val in (1, 6)) else pip
            c.put(*P(*at(0.5 * pu, 0.5 * pv)), ch)
    return info


DIE_FACES = {
    # (eyes as (u, v, ch)), (mouth points as (u, v, ch)) in face units (-1..1)
    "grin": ([(-0.45, -0.35, "R"), (0.45, -0.35, "R")],
             [(-0.6, 0.25, "K"), (-0.3, 0.45, "K"), (0.0, 0.5, "K"), (0.3, 0.45, "K"), (0.6, 0.25, "K"),
              (-0.3, 0.25, "X"), (0.0, 0.3, "X"), (0.3, 0.25, "X")]),
    "glee": ([(-0.45, -0.4, "R"), (0.45, -0.4, "R")],
             [(-0.6, 0.15, "K"), (-0.3, 0.45, "K"), (0.0, 0.6, "K"), (0.3, 0.45, "K"), (0.6, 0.15, "K"),
              (-0.3, 0.2, "E"), (0.0, 0.3, "E"), (0.3, 0.2, "E"), (0.0, 0.45, "d")]),
    "shut": ([(-0.45, -0.3, "K"), (0.45, -0.3, "K")],
             [(-0.5, 0.35, "K"), (-0.2, 0.45, "K"), (0.2, 0.45, "K"), (0.5, 0.35, "K")]),
    "dead": ([(-0.45, -0.35, "K"), (0.45, -0.35, "K"), (-0.3, -0.5, "K"), (0.3, -0.5, "K")],
             [(-0.4, 0.4, "K"), (0.0, 0.35, "K"), (0.4, 0.4, "K")]),
}


def draw_die_face(c, at, face, nn):
    eyes, mouth = DIE_FACES[face]
    for u, v, ch in mouth: c.put(*P(*at(u, v)), ch)
    for u, v, ch in eyes:
        x, y = at(u, v)
        c.put(*P(x, y), ch)
        if ch == "R": c.put(*P(x, y - 1), "f")


def loaded_die(dx=0.0, dy=0.0, rz=0.0, ry=50.0, rx=0.0, face="grin", flap=-30.0, feet=(-3, 3), legs=True,
               wings=True, tail=0.0, lift=0.0, squash=0.0, extra=None, extra_back=None, over=None, horns=True):
    """The living die. Body: a 12 px ivory cube standing on two crimson imp legs; its face looks right."""
    c = Canvas()
    if extra_back: extra_back(c)
    size = 12.0
    base = -3.0 - lift + dy
    cx, cy = dx, base - 8.0 + squash
    # back wing and tail behind the cube
    if wings:
        bat_wing(c, cx - 4, cy - 4, -165 + flap * 0.8, 60, near=False, ln=7.5)
    tl = chain(cx - 5, cy + 3, [(2.5, 170 + tail), (2.5, 150 + tail), (2.0, 115 + tail)])
    for a, b in zip(tl, tl[1:]): line(c, *a, *b, "D")
    bell(c, tl[-1][0], tl[-1][1], s=1.0)
    if legs:
        for i, fx in enumerate(feet):
            top = (cx + (-2.5 if i == 0 else 2.5), base - 1.5)
            (kx, ky), (ax, ay) = ik(top[0], top[1], dx + fx, -1 - lift, 2.2, 2.4, 1)
            tube(c, [top, (kx, ky), (ax, ay)], [1.2, 1.0, 0.9], "dDDE" if i else "pddD")
            c.put(*P(ax + 1, -lift), "K"); c.put(*P(ax, -lift), "K"); c.put(*P(ax + 2, -lift), "k")
    face_die(c, cx, cy, size, rx, ry, rz, face=face)
    if horns:
        for (x, y, ch) in ((-3, -8, "W"), (-4, -9, "W"), (-4, -10, "W"), (-5, -11, "h"), (-5, -12, "w"),
                           (2, -9, "W"), (3, -10, "W"), (3, -11, "w"), (4, -12, "h"), (4, -13, "w")):
            c.put(*P(cx + x, cy + y + 1 + squash * 0.5), ch)
    if wings:
        bat_wing(c, cx + 1, cy - 3, -150 + flap, 60, near=True, ln=8.0)
    if extra: extra(c)
    return finish(c, over)


def build_loaded_die(outdir):
    L = loaded_die
    idle = [L(flap=-40), L(flap=-15, dy=-0.4, tail=8), L(flap=0, tail=14, face="glee"), L(flap=-10, tail=5)]
    stride = [(-4, 2), (-2, 4), (0, 2), (2, -2), (0, -4), (-2, -2)]
    run = [L(feet=stride[i], lift=[0, 1, 2, 1, 0, 0][i], flap=[-50, -10, 30, 10, -30, -50][i], ry=46,
             rz=[2, 4, 6, 4, 2, 0][i], tail=[0, 10, 20, 10, 0, -5][i]) for i in range(6)]
    # Slam: crouch (0-1), HOP (2-3), crash down front edge first (4: hit, x 4..16), dust, settle
    def dust(c, x0=-7, x1=12):
        for x, y, ch in ((x0, 0, "S"), (x0 - 1, -1, "s"), (x1, 0, "S"), (x1 + 1, -1, "s"), (x0 + 2, -1, "S"),
                         (x1 - 2, -1, "S"), (x1 + 3, 0, "s")):
            c.put(x, y, ch)
    slam = [L(squash=1.5, flap=-60, face="shut", feet=(-3, 3)),
            L(squash=2.5, flap=-70, face="shut", feet=(-4, 4)),
            L(lift=5, rz=-10, flap=20, face="glee", feet=(-2, 2)),
            L(lift=8, dx=3, rz=-25, flap=40, face="glee", feet=(-1, 3)),
            L(lift=0, dx=6, rz=20, flap=-50, face="grin", feet=(-2, 5), extra=lambda c: dust(c, -1, 17)),
            L(dx=5, rz=8, flap=-30, feet=(-2, 5)),
            L(dx=2, flap=-20)]
    # Roll (special): tuck wings and legs (0), tumble forward over its own edges (1-6), unfold (7)
    roll = [L(squash=2, flap=-80, face="shut", feet=(-2, 2))]
    for k in range(6):
        roll.append(L(legs=False, wings=False, horns=False, rz=15 + k * 60, lift=1.5 + abs(math.sin(k * 1.0)) * 1.5,
                      face="glee" if k % 2 else "grin", tail=40,
                      extra_back=lambda c, k=k: [c.put(-9 - j * 2, -2 - (j + k) % 3, "S" if j else "s") for j in range(3)]))
    roll.append(L(flap=30, face="glee", feet=(-3, 4), extra=lambda c: dust(c)))
    d0 = L(rz=-15, face="dead", flap=60, feet=(-4, 2), dx=-1)
    d1 = L(rz=-40, face="dead", flap=80, legs=False, lift=1, dx=-2)
    d2 = grounded(L(rz=-85, face="dead", flap=95, legs=False, wings=False, horns=False, dx=-3))
    corpse = die_corpse()
    knock = L(rz=-18, face="shut", flap=50, feet=(-1, 4), dx=-1)
    anims = [("Idle", idle, [0.2, 0.14, 0.2, 0.14]), ("Run", run, [0.075] * 6),
             ("Slam", slam, [0.12, 0.1, 0.08, 0.06, 0.1, 0.12, 0.12]),
             ("Roll", roll, [0.14, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.16])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxLoadedDie", anims, outdir, scale=6)


def die_corpse():
    c = Canvas()
    face_die(c, 0, -6, 11, 0, 40, -90, face="dead")
    for x, ch in ((-8, "D"), (-7, "d"), (7, "E"), (8, "D"), (9, "K")):
        c.put(x, -1, ch)
    bell(c, -10, -3, 1.0)
    return grounded(finish(c))


# ------------------------------------------------------------------ CARD KING (T3, Card Soldier's): the soldier
# crowned: a fat goblin king in an ermine collar and a crimson mantle, the King of Clubs card for a tabard, a club-
# headed iron mace, and a Diamonds card for a shield (raised in Hold Court)
def club_mace(c, hx, hy, ang, ln=11.0):
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    end = (hx + ux * ln, hy + uy * ln)
    tube(c, [(hx - ux * 3, hy - uy * 3), end], [0.9, 1.0], WOOD, bias=0.1)
    c.put(*P(hx - ux * 3, hy - uy * 3), "z")
    # iron club head: three lobes and a stem
    hx2, hy2 = end[0] + ux * 3, end[1] + uy * 3
    nx, ny = -uy, ux
    for (a, b, r) in ((2.6, 0, 2.3), (0.4, 2.3, 2.1), (0.4, -2.3, 2.1)):
        ell(c, hx2 + ux * a + nx * b, hy2 + uy * a + ny * b, r, r, "Kmss", bias=0.1)
    for k in (-1, 1):
        c.put(*P(hx2 + ux * 0.3 + nx * k * 3.6, hy2 + uy * 0.3 + ny * k * 3.6), "s")
    c.put(*P(hx2 + ux * 3.5 - 0.8, hy2 + uy * 3.5 - 0.8), "S")
    return hx2, hy2


def crown(c, x, y, tilt=0.0):
    T = Xf(tilt, (x, y))
    poly(c, [T(x - 4, y), T(x + 4, y), T(x + 4.5, y - 3), T(x + 2.5, y - 1.5), T(x, y - 4), T(x - 2.5, y - 1.5),
             T(x - 4.5, y - 3)], GOLD, bias=0.2)
    for k, (px, py) in enumerate(((-4.5, -4), (0, -5), (4.5, -4))):
        c.put(*P(*T(x + px, y + py)), "Z")
    for k, px in enumerate((-2, 1, 3)):
        c.put(*P(*T(x + px, y - 1)), "M" if k != 1 else "E")


def card_king(dx=0.0, dy=0.0, lean=0.0, feet=(-4, 4), head="grin", fh=(9, -16), bh=(-8, -14), ma=-70.0,
              shield=None, extra=None, extra_back=None, over=None, crown_tilt=0.0, mace_on=True):
    """shield: None (slung on the back arm) or (x, y, w) of the raised Diamonds card held in front."""
    c = Canvas()
    if extra_back: extra_back(c)
    hip = (dx, -6 + dy)
    T = Xf(lean, hip)
    # back arm + slung shield card
    shb = T(hip[0] - 6, hip[1] - 15)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 4.5, 4.5, -1)
    if shield is None:
        card_face(c, hx - 2, hy + 1, 9, 12, "back")
    tube(c, [shb, (ex, ey), (hx, hy)], [1.6, 1.3, 1.1], "QQI")
    # crimson mantle behind the body
    poly(c, [T(hip[0] - 7, hip[1] - 18), T(hip[0] + 7, hip[1] - 18), T(hip[0] + 11, hip[1] + 0.5), T(hip[0] + 6, hip[1] + 1.5),
             T(hip[0] - 7, hip[1] + 1.5), T(hip[0] - 12, hip[1] + 0.5)], CRIM, bias=0.05)
    for k in range(-11, 12, 2):     # ermine-white hem of the mantle
        c.put(*P(*T(hip[0] + k, hip[1] + 0.5 + (0 if abs(k) < 7 else -0.5))), "X" if k % 4 else "K")
    # thick legs in striped hose, gold-buckled shoes
    for i, fx in enumerate(feet):
        hp = (hip[0] + (-2.5 if i == 0 else 2.5), hip[1])
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], dx + fx, -1, 3.0, 3.2, 1)
        tube(c, [hp, (kx, ky), (ax, ay)], [1.6, 1.4, 1.2], stripes(0, 2, CRIM, BLK, ang=90) if i else "Kmm")
        for k in range(-1, 3): c.put(*P(ax + k, 0), "K" if k < 2 else "m")
        c.put(*P(ax + 1, -1), "z")
    # pot belly and the King of Clubs tabard
    bc = T(hip[0] + 0.5, hip[1] - 8.5)
    ell(c, bc[0] + 1, bc[1] + 1, 8, 8.5, CRIM, bias=0.1)
    card_face(c, bc[0] + 1.5, bc[1] + 0.5, 13, 17, "back")
    card_face(c, bc[0] + 0.5, bc[1], 13, 17, "Clubs")
    for x, y in ((-4, -6), (4, 6)):       # a little gold K in two corners (face-card mark)
        c.put(*P(bc[0] + 0.5 + x, bc[1] + y), "z")
    # ermine collar
    cc = T(hip[0] + 0.5, hip[1] - 17.5)
    ell(c, cc[0], cc[1], 7.5, 2.4, "wWXX", bias=0.2)
    for k in (-5, -2, 1, 4):
        c.put(*P(cc[0] + k, cc[1] + (k % 2)), "K")
    # head: the goblin face under its green visor, crowned
    neck = T(hip[0] + 2, hip[1] - 18.5)
    c.part(SHARP_HEAD[head], *P(neck[0], neck[1]))
    crown(c, neck[0] + 0.5, neck[1] - 7.5, crown_tilt)
    # front arm + mace
    shf = T(hip[0] + 6, hip[1] - 15)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 4.5, 4.5, 1)
    if mace_on:
        club_mace(c, hx, hy, ma)
    tube(c, [shf, (ex, ey)], [1.7, 1.4], CRIM)
    tube(c, [(ex, ey), (hx, hy)], [1.3, 1.1], "QIj")
    c.put(*P(ex, ey), "X"); c.put(*P(ex + 1, ey), "W")
    if shield is not None:
        sx, sy, sw = shield
        card_face(c, sx + 1, sy + 0.5, sw, 14, "back")
        card_face(c, sx, sy, sw, 14, "Diamonds" if sw > 6 else "back", sx=1.0)
    if extra: extra(c)
    return finish(c, over)


def build_card_king(outdir):
    K = card_king
    idle = [K(), K(dy=0.4, fh=(9, -15.5), ma=-72), K(dy=0.4, fh=(9, -15.5), ma=-74, head="leer"), K(ma=-68)]
    stride = [(-6, 3), (-3, 1), (0, -2), (4, -5), (1, -2), (-2, 0)]
    run = [K(feet=stride[i], lean=6, dy=[0, -0.7, 0, 0, -0.7, 0][i], ma=-50, fh=(10, -15 + (i % 2)),
             bh=(-8 + (i % 3), -13)) for i in range(6)]

    def crack(c):
        for x, y, ch in ((14, 0, "K"), (16, -1, "s"), (19, 0, "s"), (12, -1, "S"), (21, -1, "S"), (17, -3, "S"),
                         (13, -3, "s"), (20, -3, "s")):
            c.put(x, y, ch)
    # Smash: heave the mace overhead (0-2), bring it down in front (3: head at x 13..21, y -1..-8), dust, recover
    smash = [K(lean=-6, fh=(5, -24), ma=-110, head="leer"),
             K(lean=-12, fh=(1, -28), ma=-150, head="leer"),
             K(lean=-8, fh=(4, -27), ma=-80, head="grin", crown_tilt=-8),
             K(lean=14, fh=(12, -12), ma=20, feet=(-4, 6), crown_tilt=6, extra=crack),
             K(lean=12, fh=(12, -11), ma=25, feet=(-4, 6), extra=crack),
             K(lean=4, fh=(10, -14), ma=-30),
             K(ma=-65)]

    def gleam(n):
        def f(c):
            for k in range(n):
                a = math.radians(-60 + k * 40)
                c.put(*P(15 + 9 * math.cos(a), -15 + 9 * math.sin(a)), "Z" if k % 2 else "y")
        return f
    # Hold Court: swing the Diamonds card round (0-2), plant it in front (3: the guard starts), gleam, lower it
    court = [K(bh=(-4, -18), head="leer"),
             K(bh=(2, -20), head="leer", shield=(6, -18, 4)),
             K(bh=(9, -17), shield=(10, -16, 8), ma=-90),
             K(lean=6, bh=(11, -15), shield=(12, -14, 10), ma=-95, head="grin", extra=gleam(3)),
             K(lean=6, bh=(11, -15), shield=(12, -14, 10), ma=-95, extra=gleam(4)),
             K(lean=5, bh=(11, -15), shield=(12, -14, 10), ma=-95, head="leer", extra=gleam(2)),
             K(lean=3, bh=(9, -16), shield=(11, -15, 9), ma=-90),
             K(lean=0, bh=(3, -16), shield=(7, -16, 5), ma=-75)]
    d0 = K(lean=-12, fh=(6, -22), bh=(-10, -20), ma=-130, head="dead", crown_tilt=-15)
    d1 = grounded(rot_spr(K(lean=-6, fh=(5, -14), bh=(-9, -14), mace_on=False, head="dead"), -45, (0, -1)))
    d2 = grounded(rot_spr(K(lean=-4, fh=(5, -13), bh=(-9, -13), mace_on=False, head="dead"), -86, (0, -1)))
    corpse = king_corpse()
    knock = K(lean=-14, dx=-1, fh=(6, -20), bh=(-10, -18), ma=-120, head="leer", feet=(-2, 5), crown_tilt=-10)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.085] * 6),
             ("Smash", smash, [0.16, 0.14, 0.08, 0.08, 0.14, 0.14, 0.14]),
             ("Court", court, [0.1, 0.08, 0.08, 0.14, 0.14, 0.14, 0.1, 0.1])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.12, 0.12, 0.14, 0.4], knock)
    return sheet("JinxCardKing", anims, outdir, scale=5)


def king_corpse():
    body = card_king(lean=0, fh=(5, -13), bh=(-9, -13), mace_on=False, head="dead")
    lying = grounded(rot_spr(body, -90, (0, -1)))
    o = Canvas()
    club_mace(o, -14, -2, 180, 6)
    crown(o, 22, -1, 30)
    return grounded(floor_cut(merge(lying, outline(o.spr()))))


# ------------------------------------------------------------------ HOUSE OF CARDS (T3, Card Soldier's): the
# soldier's board multiplied into a walking tower of leaning cards; the green-visored goblin eye peers out of the top
HOC_KINDS = ["Clubs", "back", "Spades", "back", "Hearts", "back", "Diamonds", "back", "Clubs", "back", "Spades", "back"]


def house_card(c, x, y, ang, idx, h=9.0, w=3.6):
    """One card of the tower: white faces with a big pip, crimson backs; right/bottom edges inked so the cards
    stay separate."""
    kind = HOC_KINDS[idx % len(HOC_KINDS)]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    hw, hh = w / 2.0, h / 2.0
    tf = lambda u, v: (x + u * ca - v * sa, y + u * sa + v * ca)
    pts = [tf(-hw, -hh), tf(hw, -hh), tf(hw, hh), tf(-hw, hh)]
    if kind == "back":
        poly(c, pts, "dDEE", lit="flat", bias=0.1)
        line(c, *tf(-hw + 0.5, -hh + 0.5), *tf(-hw + 0.5, hh - 0.5), "f")
        c.put(*P(*tf(0.3, 0)), "z")
    else:
        poly(c, pts, "WXXX", lit="flat", bias=0.3)
        red = kind in ("Hearts", "Diamonds")
        for v in (-1.5, 0, 1.5):
            c.put(*P(*tf(0.2, v)), ("E" if red else "K") if v == 0 else ("f" if red else "m"))
    line(c, *pts[1], *pts[2], "K" if kind != "back" else "d")


def house_of_cards(dx=0.0, dy=0.0, sway=0.0, top=0.0, mid=0.0, arms=((-140, 3), (-40, 3)), eye="open",
                   missing=(), base=0.0, extra=None, extra_back=None, over=None, feet=(-5, 5)):
    """sway: whole-tower lean; top/mid: extra lean of the upper tiers (deg); arms: (angle, n) card fans."""
    c = Canvas()
    if extra_back: extra_back(c)
    # card feet: two folded cards it shuffles on
    for i, fx in enumerate(feet):
        card_face(c, dx + fx, -1.5, 5, 3, "back" if i == 0 else "Hearts")
    y0 = -3 + dy + base
    T0 = Xf(sway, (dx, y0))
    idx = 0
    tiers = [(3, 0.0), (2, mid), (1, mid + top)]
    yb = y0
    for t, (n, extra_lean) in enumerate(tiers):
        piv = T0(dx, yb)
        T = Xf(sway + extra_lean, piv) if extra_lean else T0
        hgt = 9.0 - t * 0.5
        for k in range(n):
            cx = dx + (k - (n - 1) / 2.0) * 8.0
            for s in (-1, 1):
                if idx not in missing:
                    p = T(cx + s * 2.1, yb - hgt / 2 + 0.3)
                    house_card(c, p[0], p[1], s * 22 + sway + extra_lean, idx, hgt)
                idx += 1
        # a flat card across the top of each tent (the floor of the next tier)
        if t < 2:
            for k in range(n - 1):
                cx = dx + (k - (n - 2) / 2.0) * 8.0
                p = T(cx, yb - hgt - 0.5)
                if idx not in missing:
                    house_card(c, p[0], p[1], sway + extra_lean + 90, idx + 1, 9, 2.0)
                idx += 1
        if t == 2:
            ep = T(dx, yb - hgt * 0.55)
            # the goblin eye in the top tent: olive lid, green visor brim above
            if eye != "gone":
                for x in range(-2, 3): c.put(*P(ep[0] + x, ep[1] - 3), "M" if x < 1 else "H")
                ell(c, ep[0], ep[1], 1.8, 1.4, GOB, bias=0.1)
                if eye == "open":
                    c.put(*P(ep[0], ep[1]), "Y"); c.put(*P(ep[0] + 1, ep[1]), "K")
                elif eye == "glare":
                    c.put(*P(ep[0], ep[1]), "y"); c.put(*P(ep[0] + 1, ep[1]), "R"); c.put(*P(ep[0] - 1, ep[1]), "Y")
                else:
                    c.put(*P(ep[0] - 1, ep[1]), "K"); c.put(*P(ep[0], ep[1]), "K"); c.put(*P(ep[0] + 1, ep[1]), "K")
        yb = yb - hgt - 1.2
    # arms: fans of cards from the middle tier
    for i, (a, n) in enumerate(arms):
        if n <= 0: continue
        sx = dx + (-8.5 if i == 0 else 8.5)
        sp = T0(sx, y0 - 13)
        for k in range(n):
            aa = a + (k - (n - 1) / 2.0) * 22
            ux, uy = math.cos(math.radians(aa)), math.sin(math.radians(aa))
            house_card(c, sp[0] + ux * 4, sp[1] + uy * 4, aa + 90, k + i, 5.5, 2.8)
    if extra: extra(c)
    return finish(c, over)


def build_house_of_cards(outdir):
    H = house_of_cards
    idle = [H(), H(sway=1, top=2, arms=((-135, 3), (-45, 3))), H(sway=1.5, top=3, eye="shut", arms=((-130, 3), (-50, 3))),
            H(sway=0.5, top=1, arms=((-138, 3), (-42, 3)))]
    run = [H(sway=6 + [0, 2, 3, 2, 0, -1][i], top=[2, 4, 5, 3, 1, 0][i], feet=[(-6, 4), (-4, 6), (-2, 7), (-4, 5), (-6, 3), (-7, 4)][i],
             dy=[0, -0.6, -1, -0.6, 0, 0][i], arms=((-160, 3), (-20 + 6 * (i % 3), 3))) for i in range(6)]
    # Topple: the upper tiers rock back (0-1), then pitch forward (2), SLAP down in front (3: cards to x ~22), hold, rebuild
    topple = [H(sway=-4, top=-6, eye="glare"), H(sway=-6, mid=-6, top=-10, eye="glare", arms=((-110, 3), (-70, 3))),
              H(sway=6, mid=14, top=18, eye="glare", arms=((-170, 3), (-10, 3))),
              H(sway=10, mid=34, top=40, eye="glare", arms=((-170, 3), (10, 3)),
                extra_back=lambda c: [line(c, 12, -20, 18, -12, "s"), line(c, 8, -24, 16, -18, "s")]),
              H(sway=8, mid=30, top=34, eye="open", arms=((-170, 3), (5, 3))),
              H(sway=3, mid=10, top=10, eye="open"), H(sway=1, top=2)]

    def storm(n, ph, r, cy):
        return card_ring(0, cy, r, r * 0.35, n, ph, False), card_ring(0, cy, r, r * 0.35, n, ph, True)
    # Card Storm: the arm fans and the top tent lift off (0-2), whirl round it (3-5: 4 = the storm starts), settle back
    st = []
    for i, (miss, rr, n, eye) in enumerate(((set(), 0, 0, "open"), ({13, 14}, 10, 4, "glare"), ({13, 14}, 14, 6, "glare"),
                                             ({13, 14}, 17, 8, "glare"), ({13, 14}, 17, 8, "glare"), ({13, 14}, 17, 8, "glare"),
                                             ({13, 14}, 12, 5, "open"), (set(), 0, 0, "open"))):
        b, f = storm(n, i * 0.7, rr, -18) if n else (None, None)
        st.append(H(missing=miss, eye=eye if not miss else "gone", arms=((-90, 0), (-90, 0)) if n else ((-138, 3), (-42, 3)),
                    extra_back=b, extra=(lambda c, f=f, i=i: [f(c), sparkle(c, 0, -27, 1, "N", "L")]) if f else None))
    d0 = H(sway=-8, mid=-10, top=-14, eye="shut")
    d1 = H(sway=-4, mid=25, top=50, missing={13, 14, 11}, eye="gone", base=0, arms=((-160, 2), (20, 2)))
    d2 = house_pile(0.6)
    corpse = house_pile(1.0)
    knock = H(sway=-10, mid=-6, top=-8, eye="glare", feet=(-4, 6))
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.08] * 6),
             ("Topple", topple, [0.14, 0.12, 0.06, 0.1, 0.12, 0.12, 0.14]),
             ("Storm", st, [0.1, 0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 0.12])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxHouseOfCards", anims, outdir, scale=5)


def house_pile(t):
    c = Canvas()
    rnd = random.Random(7)
    for k in range(13):
        x = rnd.uniform(-13, 13) * t + rnd.uniform(-3, 3) * (1 - t)
        y = -1.5 - rnd.uniform(0, 5) * (1.2 - t)
        house_card(c, x, y, rnd.uniform(60, 120), k, 7)
    ell(c, 2, -2, 1.8, 1.2, GOB)
    c.put(2, -2, "K"); c.put(1, -5, "M"); c.put(2, -5, "M"); c.put(3, -5, "H")
    return grounded(finish(c))


# ------------------------------------------------------------------ HIGH ROLLER (T3, Loaded Die's): the die has
# grown a fat crimson devil around it: its pot belly is still the ivory die (pips and all), the imp horns curl
# big, little bat wings, a gold chain, a cigar, and a tower of poker chips in its fist
ROLLER_HEAD = {
    "grin": Part("""
W.......W.
Wh.....hW.
.WhDEEhW..
.DEEEEEf..
DEYKEEYKf.
DEEEEEEEfz
dKXKXKXKEy
.dKKKKKKd.
..ddDDdd..
""", (4, 8)),
    "glee": Part("""
W.......W.
Wh.....hW.
.WhDEEhW..
.DEEEEEf..
DKKEEEKKf.
DEEEEEEEfz
KXKXKXKXKy
.KEEEEEK..
..KKKKK...
""", (4, 8)),
    "dead": Part("""
W.......W.
Wh.....hW.
.WhDEEhW..
.DEEEEEf..
DKEKEEKEK.
DEKEEEKEf.
dEEKKKKEE.
.dEEEEEd..
..ddDDdd..
""", (4, 8)),
}
CHIP_COLS = [("E", "f"), ("X", "W"), ("m", "s"), ("b", "B"), ("z", "Z")]


def chip_stack(c, x, y, n, ang=0.0, top=0):
    """Stack of poker chips: bottom at (x, y), growing along -90+ang."""
    ux, uy = math.cos(math.radians(-90 + ang)), math.sin(math.radians(-90 + ang))
    for k in range(n):
        a, b = CHIP_COLS[(k + top) % len(CHIP_COLS)]
        cx, cy = x + ux * k * 1.4, y + uy * k * 1.4
        for d in (-1.5, -0.5, 0.5, 1.5):
            c.put(*P(cx + d, cy), b if abs(d) < 1 else a)
        c.put(*P(cx - 1.5, cy), "K" if k % 2 else a)


def high_roller(dx=0.0, dy=0.0, lean=0.0, feet=(-4, 4), head="grin", fh=(10, -14), bh=(-9, -12), stack=6,
                stack_ang=0.0, flap=-20.0, chip=None, extra=None, extra_back=None, over=None, cigar=True):
    c = Canvas()
    if extra_back: extra_back(c)
    hip = (dx, -6 + dy)
    T = Xf(lean, hip)
    sh = T(hip[0] - 1, hip[1] - 15)
    bat_wing(c, sh[0] - 5, sh[1], -160 + flap * 0.8, 70, near=False, ln=8)
    # back arm
    shb = T(hip[0] - 7, hip[1] - 13)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 4.2, 4.0, -1)
    tube(c, [shb, (ex, ey), (hx, hy)], [1.6, 1.3, 1.2], "pddD")
    # tail with the bell
    tl = chain(hip[0] - 7, hip[1] - 1, [(3, 170), (3, 150), (2.5, 110)])
    for a, b in zip(tl, tl[1:]): line(c, *a, *b, "D")
    bell(c, tl[-1][0], tl[-1][1], s=1.2)
    # goat legs with black hooves
    for i, fx in enumerate(feet):
        hp = (hip[0] + (-3 if i == 0 else 3), hip[1] - 1)
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], dx + fx, -1, 3.2, 3.4, -1)
        tube(c, [hp, (kx, ky), (ax, ay)], [2.0, 1.5, 1.0], "pddD" if i == 0 else IMP)
        for k in range(-1, 2): c.put(*P(ax + k, 0), "K")
        c.put(*P(ax + 1, -1), "m")
    # fat body
    bc = T(hip[0] + 0.5, hip[1] - 8)
    ell(c, bc[0], bc[1], 9.0, 9.5, IMP, bias=0.15)
    # the die belly: a flat ivory face with five pips
    bp = T(hip[0] + 2, hip[1] - 7.5)
    poly(c, [(bp[0] - 5, bp[1] - 5), (bp[0] + 5, bp[1] - 5.5), (bp[0] + 5.5, bp[1] + 5), (bp[0] - 4.5, bp[1] + 5.5)],
         IVORY, bias=0.25)
    line(c, bp[0] + 5, bp[1] - 5.5, bp[0] + 5.5, bp[1] + 5, "w"); line(c, bp[0] + 5.5, bp[1] + 5, bp[0] - 4.5, bp[1] + 5.5, "w")
    for u, v in ((-2.5, -2.5), (2.5, -2.5), (0, 0), (-2.5, 2.5), (2.5, 2.5)):
        c.put(*P(bp[0] + u, bp[1] + v), "K"); c.put(*P(bp[0] + u + 1, bp[1] + v), "K")
    # gold chain across the chest
    for k in range(9):
        t = k / 8.0
        c.put(*P(*T(hip[0] - 6 + 12 * t, hip[1] - 15 + 3 * math.sin(math.pi * t))), "Z" if k % 2 else "z")
    # head with curled horns
    neck = T(hip[0] + 2.5, hip[1] - 16)
    c.part(ROLLER_HEAD[head], *P(*neck))
    if cigar:
        cg = (neck[0] + 6, neck[1] - 2)
        line(c, cg[0], cg[1], cg[0] + 3, cg[1] - 1, "t"); c.put(*P(cg[0] + 4, cg[1] - 1), "O")
        c.put(*P(cg[0] + 5, cg[1] - 3), "s"); c.put(*P(cg[0] + 4, cg[1] - 5), "S")
    # front arm + chip tower
    shf = T(hip[0] + 7, hip[1] - 13)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 4.2, 4.0, 1)
    tube(c, [shf, (ex, ey), (hx, hy)], [1.7, 1.4, 1.3], IMP)
    for k in range(-1, 2): c.put(*P(hx + k, hy + 1), "Z" if k == 0 else "z")    # gold ring
    if stack: chip_stack(c, hx, hy - 1, stack, stack_ang)
    if chip: chip_stack(c, chip[0], chip[1], 1, chip[2] if len(chip) > 2 else 70)
    bat_wing(c, sh[0] + 1, sh[1] + 1, -150 + flap, 70, near=True, ln=8)
    if extra: extra(c)
    return finish(c, over)


def build_high_roller(outdir):
    R_ = high_roller
    idle = [R_(), R_(dy=0.4, flap=0, fh=(10, -13.5)), R_(dy=0.4, flap=15, head="glee", fh=(10, -13.5)), R_(flap=-5)]
    stride = [(-6, 3), (-3, 1), (0, -2), (4, -5), (1, -2), (-2, 0)]
    run = [R_(feet=stride[i], lean=6, dy=[0, -0.8, 0, 0, -0.8, 0][i], flap=[-40, -10, 25, 10, -20, -40][i],
              fh=(11, -13 + (i % 2)), stack_ang=-8) for i in range(6)]
    # Flick: cock the thumb (0-1), FLICK a chip (2: it leaves the hand at (13, -19)), watch it go (3-5)
    flick = [R_(fh=(8, -17), head="glee", stack=5), R_(fh=(6, -19), head="glee", stack=5, lean=-4),
             R_(fh=(12, -18), lean=6, stack=5, chip=(16, -20, 60)),
             R_(fh=(12, -17), lean=6, stack=5, chip=(20, -21, 30)), R_(fh=(11, -15), lean=3, stack=5), R_(stack=6)]
    # All In: gather every chip into both arms (0-3), SHOVE them at the hero (4-5: 5 = the spray), arms wide
    allin = [R_(fh=(10, -18), bh=(0, -18), stack=6, head="glee"),
             R_(fh=(6, -22), bh=(-2, -22), stack=8, head="glee", lean=-4),
             R_(fh=(4, -24), bh=(-4, -23), stack=10, head="glee", lean=-8),
             R_(fh=(3, -24), bh=(-5, -23), stack=10, head="grin", lean=-10, flap=30),
             R_(fh=(13, -16), bh=(9, -15), stack=6, stack_ang=60, lean=10, flap=-40),
             R_(fh=(15, -13), bh=(11, -12), stack=0, lean=14, flap=-50, head="glee",
                extra=lambda c: [chip_stack(c, 20 + k * 2, -18 + k * 3 - (k % 2) * 2, 1, 80) for k in range(5)]),
             R_(fh=(14, -13), bh=(10, -12), stack=0, lean=10),
             R_(fh=(12, -14), bh=(-6, -12), stack=2, lean=4),
             R_(stack=6)]
    d0 = R_(lean=-12, fh=(8, -20), bh=(-12, -18), head="dead", flap=60, stack=4, stack_ang=-40)
    d1 = grounded(rot_spr(R_(lean=-6, head="dead", flap=70, stack=0, cigar=False), -45, (0, -1)))
    d2 = grounded(rot_spr(R_(lean=-4, head="dead", flap=80, stack=0, cigar=False), -86, (0, -1)))
    corpse = merge(d2, Spr({(16, -1): "E", (17, -1): "f", (18, -1): "E", (20, -1): "X", (21, -1): "W", (-17, -1): "m"}))
    knock = R_(lean=-14, dx=-1, fh=(7, -19), bh=(-12, -16), head="glee", flap=50, stack=5, stack_ang=-30)
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.085] * 6),
             ("Flick", flick, [0.12, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("AllIn", allin, [0.1, 0.1, 0.1, 0.14, 0.06, 0.08, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.12, 0.12, 0.14, 0.4], knock)
    return sheet("JinxHighRoller", anims, outdir, scale=5)


# ------------------------------------------------------------------ NATURAL TWENTY (T3, Loaded Die's): the cube
# has cut itself into a twenty-sided gem: violet resin with gold edges, still the die's grinning face on its front
# facet, the imp's horns, great bat wings and crimson legs
PHI = (1 + 5 ** 0.5) / 2
ICO_V = [(0, s1, s2 * PHI) for s1 in (-1, 1) for s2 in (-1, 1)] + [(s1, s2 * PHI, 0) for s1 in (-1, 1) for s2 in (-1, 1)] + \
        [(s2 * PHI, 0, s1) for s1 in (-1, 1) for s2 in (-1, 1)]
ICO_F = [(i, j, k) for i in range(12) for j in range(i + 1, 12) for k in range(j + 1, 12)
         if all(abs(sum((ICO_V[a][q] - ICO_V[b][q]) ** 2 for q in range(3)) - 4) < 1e-6 for a, b in ((i, j), (j, k), (i, k)))]
RESIN = "qnNL"


def d20(c, cx, cy, r, rx=0.0, ry=0.0, rz=0.0, face="grin", ramp=RESIN, numbers=True):
    s = r / math.sqrt(1 + PHI * PHI)
    xf = lambda v: rot3(rot3(v, rx, ry, rz), CAM_TILT * 0.5, 0, 0)
    V = [xf(v) for v in ICO_V]
    Lv = (-0.55, -0.6, -0.58)
    fl = []
    for f in ICO_F:
        a, b, d = (V[i] for i in f)
        n = [sum(V[i][q] for i in f) / 3.0 for q in range(3)]
        ln = math.sqrt(sum(x * x for x in n)); n = [x / ln for x in n]
        if n[2] >= -0.02: continue
        fl.append((n, f))
    # the face goes on the front-right facet
    best = min(fl, key=lambda t: -(t[0][0] * 0.55 - t[0][2] * 0.8 + t[0][1] * -0.1))
    fl.sort(key=lambda t: -t[0][2])
    for n, f in fl:
        pts = [(cx + V[i][0] * s, cy + V[i][1] * s) for i in f]
        lam = n[0] * Lv[0] + n[1] * Lv[1] + n[2] * Lv[2]
        poly(c, pts, ramp, bias=lam * 2.2 - 0.6, lit="flat")
    for n, f in fl:
        pts = [(cx + V[i][0] * s, cy + V[i][1] * s) for i in f]
        for a_, b_ in zip(pts, pts[1:] + pts[:1]):
            line(c, *a_, *b_, "z" if (a_[1] + b_[1]) < 2 * cy else "e")
        mx = sum(p[0] for p in pts) / 3.0; my = sum(p[1] for p in pts) / 3.0
        if (n, f) == best:
            # grinning face: two glowing eyes and a jagged mouth in the triangle
            for ex_ in (-1.6, 1.6):
                c.put(*P(mx + ex_, my - 1), "R"); c.put(*P(mx + ex_, my - 2), "f")
            for k, xx in enumerate((-2, -1, 0, 1, 2)):
                c.put(*P(mx + xx, my + 1.5 + (0 if k % 2 else 0.6)), "K")
            for xx in (-1, 1):
                c.put(*P(mx + xx, my + 1), "Z")
            if face == "dead":
                for ex_ in (-1.6, 1.6): c.put(*P(mx + ex_, my - 1), "K"); c.put(*P(mx + ex_, my - 2), "K")
            if face == "shut":
                for ex_ in (-1.6, 1.6): c.put(*P(mx + ex_, my - 1), "K"); c.put(*P(mx + ex_, my - 2), "e")
        elif numbers and -n[2] > 0.45:
            c.put(*P(mx, my), "Z"); c.put(*P(mx + 1, my), "z")
    return best


def natural_twenty(dx=0.0, dy=0.0, rz=0.0, ry=18.0, rx=0.0, face="grin", flap=-30.0, feet=(-5, 5), legs=True,
                   wings=True, lift=0.0, squash=0.0, horns=True, extra=None, extra_back=None, over=None, num=None):
    c = Canvas()
    if extra_back: extra_back(c)
    R0 = 12.0
    base = -5.0 - lift + dy
    cx, cy = dx, base - R0 + 1 + squash
    if wings:
        bat_wing(c, cx - 6, cy - 6, -165 + flap * 0.8, 80, near=False, ln=11)
    tl = chain(cx - 9, cy + 6, [(3, 170), (3, 150), (3, 115)])
    for a, b in zip(tl, tl[1:]): line(c, *a, *b, "D")
    bell(c, tl[-1][0], tl[-1][1], s=1.2)
    if legs:
        for i, fx in enumerate(feet):
            top = (cx + (-4 if i == 0 else 4), base - 2)
            (kx, ky), (ax, ay) = ik(top[0], top[1], dx + fx, -1 - lift, 3.0, 3.2, 1)
            tube(c, [top, (kx, ky), (ax, ay)], [2.0, 1.6, 1.2], "pddD" if i == 0 else IMP)
            for k in range(-1, 3): c.put(*P(ax + k, -lift), "K")
            c.put(*P(ax + 3, -lift - 1), "W")   # ivory claw
    d20(c, cx, cy, R0, rx, ry, rz, face=face)
    if horns:
        for (x, y, ch) in ((-5, -11, "W"), (-6, -12, "W"), (-7, -13, "W"), (-8, -14, "W"), (-8, -15, "h"), (-7, -16, "w"),
                           (4, -11, "W"), (5, -12, "W"), (6, -13, "W"), (7, -14, "W"), (7, -15, "h"), (6, -16, "w")):
            c.put(*P(cx + x, cy + y + squash * 0.5), ch)
    if wings:
        bat_wing(c, cx + 1, cy - 6, -150 + flap, 80, near=True, ln=12)
    if num:
        nx, ny, txt = num
        for k, ch in enumerate(txt):
            glyph_px(c, DIGITS3[ch], nx + k * 4, ny, {"X": "Y", "o": "K"})
    if extra: extra(c)
    return finish(c, over)


DIGITS3 = {"2": ["XXo", "ooX", "oXo", "Xoo", "XXX"], "0": ["XXX", "XoX", "XoX", "XoX", "XXX"],
           "1": ["oXo", "XXo", "oXo", "oXo", "XXX"]}


def build_twenty(outdir):
    N = natural_twenty
    idle = [N(flap=-40), N(flap=-10, dy=-0.4, ry=22), N(flap=20, dy=-0.4, ry=26, face="shut"), N(flap=-5, ry=22)]
    stride = [(-6, 3), (-3, 5), (0, 2), (3, -3), (0, -5), (-3, -2)]
    run = [N(feet=stride[i], lift=[0, 1, 2, 1, 0, 0][i], flap=[-50, -10, 30, 10, -30, -50][i], ry=18 + i * 12,
             rz=[2, 4, 6, 4, 2, 0][i]) for i in range(6)]

    def dust(c, x0=-9, x1=14):
        for x, y, ch in ((x0, 0, "S"), (x0 - 1, -1, "s"), (x1, 0, "S"), (x1 + 1, -1, "s"), (x0 + 2, -1, "S"), (x1 + 3, 0, "s")):
            c.put(x, y, ch)
    # Ram: rear back (0-1), lunge and roll its weight forward (2), CRASH in (3: facets at x 8..20), hold, settle
    ram = [N(dx=-1, rz=-10, flap=-60, squash=1, face="shut"), N(dx=-3, rz=-20, flap=-70, squash=2, face="shut"),
           N(dx=3, rz=20, ry=40, flap=30, lift=2, feet=(-3, 6)),
           N(dx=7, rz=45, ry=60, flap=-50, feet=(-1, 9), extra=lambda c: dust(c, -3, 20)),
           N(dx=6, rz=35, ry=55, flap=-40, feet=(-1, 9)), N(dx=3, rz=10, ry=30, flap=-20), N(flap=-30)]
    # Crit (special): crouch (0), LEAP and spin through every facet in the air (1-5), slam down (6: the roll lands),
    # the number shows over the head (7), settle (8)
    crit = [N(squash=2.5, flap=-80, face="shut")]
    for k in range(5):
        crit.append(N(lift=6 + 3 * math.sin((k + 1) / 6 * math.pi), legs=False, wings=k % 2 == 0, flap=60, horns=False,
                      rx=k * 47, ry=18 + k * 73, rz=k * 31, face="grin"))
    crit.append(N(squash=2, flap=-60, extra=lambda c: dust(c, -11, 16)))
    crit.append(N(flap=40, face="grin"))
    crit.append(N(flap=0))
    d0 = N(rz=-15, face="dead", flap=60, feet=(-6, 3), dx=-1)
    d1 = N(rz=-40, face="dead", flap=80, legs=False, lift=1, dx=-2)
    d2 = grounded(N(rz=-80, face="dead", flap=95, legs=False, wings=False, horns=False, dx=-3))
    corpse = twenty_corpse()
    knock = N(rz=-18, face="shut", flap=50, feet=(-2, 6), dx=-1)
    anims = [("Idle", idle, [0.2, 0.15, 0.2, 0.15]), ("Run", run, [0.08] * 6),
             ("Ram", ram, [0.12, 0.12, 0.06, 0.1, 0.12, 0.12, 0.12]),
             ("Crit", crit, [0.12, 0.07, 0.07, 0.07, 0.07, 0.07, 0.1, 0.3, 0.12])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxTwenty", anims, outdir, scale=5)


def twenty_corpse():
    c = Canvas()
    rnd = random.Random(3)
    for k in range(7):
        x = -11 + k * 3.6 + rnd.uniform(-1, 1)
        h = rnd.uniform(2, 5)
        poly(c, [(x - 2, 0), (x + 2, 0), (x + rnd.uniform(-1, 1), -h)], RESIN, bias=0.1 * (k % 3))
        c.put(*P(x, -1), "z")
    c.put(-1, -3, "R"); c.put(2, -3, "K")
    for x, ch in ((-14, "D"), (-13, "d"), (13, "E"), (14, "D")):
        c.put(x, -1, ch)
    bell(c, 16, -3, 1.2)
    return grounded(finish(c))


# ------------------------------------------------------------------ GORGON (T3, Snake-Eyes'): the serpent risen
# into a gorgon: the harlequin coil below, an ashen torso in a black bodice, a pale mask whose eyes are two red
# pips, the imp's ivory horns, and a crown of little harlequin snakes for hair
GORGON_FACE = {
    "calm": Part("""
.hwWW.
hwWWWX
wKRWKR
hwWWWW
.wKKKw
..hww.
""", (2, 5)),
    "glare": Part("""
.hwWW.
hwWWWX
wRyWRy
hwWWWW
.wKEKw
..hww.
""", (2, 5)),
    "dead": Part("""
.hwWW.
hwWWWX
wKwWKw
hwWWWW
.wwKKw
..hww.
""", (2, 5)),
}
SKIN = "hiiw"
TONE.update({"JinxGorgon": 2, "JinxHighRoller": 1})


def hair_snake(c, root, ang, ln, wig=0.0, head=True, bite=False):
    pts = [root]
    a = ang
    for k in range(3):
        a += wig * (1 if k % 2 else -1)
        pts.append((pts[-1][0] + ln / 3.0 * math.cos(math.radians(a)), pts[-1][1] + ln / 3.0 * math.sin(math.radians(a))))
    tube(c, pts, [1.1, 0.9, 0.8, 0.8], harl(root[0], root[1], 2, CRIM, BLK), bias=0.1)
    if head:
        hx, hy = pts[-1]
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        ell(c, hx + ux * 0.8, hy + uy * 0.8, 1.4, 1.0, "Kmms", ang=a, bias=0.2)
        c.put(*P(hx + ux * 1.0 - uy * 0.6, hy + uy * 1.0 + ux * 0.6 - 1), "R")
        if bite:
            c.put(*P(hx + ux * 2.6, hy + uy * 2.6 - 1), "X"); c.put(*P(hx + ux * 2.6, hy + uy * 2.6 + 1), "X")


def gorgon(dx=0.0, dy=0.0, lean=0.0, face="calm", hair=0.0, lash=0.0, fh=(7, -17), bh=(-6, -16), coil_ph=0.0,
           tail_x=0.0, extra=None, extra_back=None, over=None, eyes_glow=0):
    """lash: 0..1, the hair snakes stretch forward to bite."""
    c = Canvas()
    if extra_back: extra_back(c)
    # the coil on the floor (from the tail tip round to the waist)
    coil = [(-12 + tail_x, -1.2), (-9, -2.2 - 0.4 * math.sin(coil_ph)), (-4, -2.6), (2, -2.6), (6, -2.4 + 0.4 * math.sin(coil_ph)),
            (5, -5.5), (0, -6.5), (-4, -6), (-3, -9), (dx, -12 + dy)]
    radii = [0.6, 1.4, 2.2, 2.6, 2.6, 2.6, 2.6, 2.6, 2.6, 2.4]
    serpent(c, coil, radii, belly=0.0)
    rattle(c, -13 + tail_x, -2, 0)
    waist = (dx, -12 + dy)
    T = Xf(lean, waist)
    # back arm
    shb = T(waist[0] - 3, waist[1] - 8)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 3.6, 3.6, -1)
    tube(c, [shb, (ex, ey), (hx, hy)], [1.0, 0.9, 0.7], "ghh")
    # torso: ashen skin, black bodice laced crimson
    tc = T(waist[0], waist[1] - 4)
    ell(c, tc[0], tc[1], 3.4, 5.0, SKIN, ang=lean, bias=0.15)
    bod = [T(waist[0] - 3.4, waist[1] - 5), T(waist[0] + 3.4, waist[1] - 5), T(waist[0] + 3.0, waist[1] + 0.5),
           T(waist[0] - 3.0, waist[1] + 0.5)]
    poly(c, bod, BLK, bias=0.1)
    for k in range(3):
        c.put(*P(*T(waist[0] + 0.5, waist[1] - 4 + k * 1.5)), "E")
    # head
    neck = T(waist[0] + 1, waist[1] - 9)
    hx0, hy0 = P(*neck)
    # hair snakes behind the face
    angs = [-150, -120, -90, -60, -30]
    for k, a in enumerate(angs[:2]):
        hair_snake(c, (hx0 - 1, hy0 - 4), a + hair * (1 if k % 2 else -1), 6, wig=12 + hair)
    c.part(GORGON_FACE[face], hx0, hy0)
    for (x, y, ch) in ((-1, -6, "W"), (-2, -7, "W"), (-2, -8, "h"), (2, -6, "W"), (3, -7, "W"), (3, -8, "h")):
        c.put(hx0 + x, hy0 + y, ch)
    for k, a in enumerate(angs[2:]):
        la = a + (lash * (60 + k * 25) if a > -100 else 0)
        ln = 6 + lash * (9 + k * 3)
        hair_snake(c, (hx0 + 1, hy0 - 4), la + hair * (1 if k % 2 else -1), ln, wig=(12 + hair) * (1 - lash),
                   bite=lash > 0.6)
    if eyes_glow:
        for ex_ in (2, 5):
            for k in range(1, eyes_glow + 1):
                c.put(hx0 + ex_ + k - 2, hy0 - 3, "y" if k == 1 else "Y")
    # front arm
    shf = T(waist[0] + 3, waist[1] - 8)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 3.6, 3.6, 1)
    tube(c, [shf, (ex, ey), (hx, hy)], [1.1, 0.9, 0.8], SKIN)
    c.put(*P(hx, hy), "w"); c.put(*P(ex, ey), "z")
    if extra: extra(c)
    return finish(c, over)


def build_gorgon(outdir):
    G = gorgon
    idle = [G(hair=0), G(hair=8, coil_ph=1, dy=-0.4), G(hair=14, coil_ph=2, dy=-0.4, fh=(7, -16)), G(hair=6, coil_ph=3)]
    run = [G(lean=8, hair=10 * math.sin(i), coil_ph=i * 1.1, tail_x=[0, -1, -2, -1, 0, 1][i], fh=(8, -15), bh=(-7, -14),
             dy=[0, -0.5, -1, -0.5, 0, 0][i]) for i in range(6)]
    # Lash: the hair rears back (0-1), the snakes STRIKE forward (2-3: heads at x 12..20, y -26..-16), hold, back
    lash = [G(lean=-6, hair=-10, face="glare"), G(lean=-10, hair=-20, face="glare", fh=(4, -20)),
            G(lean=6, lash=0.6, face="glare", fh=(9, -18)), G(lean=10, lash=1.0, face="glare", fh=(10, -17)),
            G(lean=8, lash=0.8, face="glare"), G(lean=3, lash=0.3), G()]
    # Stare (special): hands to the temples (0-1), the eyes kindle (2-3), STARE (4: the gaze), burn, fade (5-7)
    stare = [G(fh=(4, -22), bh=(-2, -22), face="calm"), G(fh=(4, -23), bh=(-2, -23), face="glare", hair=10),
             G(fh=(3, -23), bh=(-2, -23), face="glare", hair=18, eyes_glow=1),
             G(fh=(3, -23), bh=(-2, -23), face="glare", hair=22, eyes_glow=2, lean=-4),
             G(fh=(9, -18), bh=(-4, -20), face="glare", hair=26, eyes_glow=3, lean=6),
             G(fh=(9, -18), bh=(-4, -20), face="glare", hair=20, eyes_glow=3, lean=6),
             G(fh=(8, -17), bh=(-5, -18), face="glare", hair=10, eyes_glow=1, lean=3), G()]
    d0 = G(lean=-14, face="dead", hair=30, fh=(5, -22), bh=(-8, -20))
    d1 = G(lean=-30, face="dead", hair=40, dy=3, fh=(2, -14), bh=(-9, -14))
    d2 = grounded(rot_spr(G(face="dead", hair=10), -70, (0, -1)))
    corpse = grounded(rot_spr(G(face="dead", hair=0, fh=(4, -12), bh=(-4, -12)), -88, (0, -1)))
    knock = G(lean=-16, dx=-1, face="glare", hair=25, fh=(5, -22), bh=(-8, -20))
    anims = [("Idle", idle, [0.2, 0.15, 0.2, 0.15]), ("Run", run, [0.08] * 6),
             ("Lash", lash, [0.12, 0.1, 0.06, 0.1, 0.1, 0.12, 0.12]),
             ("Stare", stare, [0.12, 0.1, 0.1, 0.1, 0.12, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxGorgon", anims, outdir, scale=5)


# ------------------------------------------------------------------ DICE RATTLER (T3, Snake-Eyes'): the serpent
# grown into a fat gold-and-black rattlesnake piled in coils, its broad viper head low and forward, and a rattle
# of four stacked ivory dice raised over the coils
VIPER_HEAD = {
    "shut": Part("""
..WW.......
.mmssss....
mmmsXEss...
mmmmmmmmss.
KmmmmmmmmmK
.dDDEEEEfK.
""", (2, 4)),
    "gape": Part("""
..WW.......
.mmssss....
mmmsXEsss..
mmmmmmmmmsK
KmmKWKKKWK.
.mmEEffEEK.
..dDDDDK...
""", (2, 4)),
    "dead": Part("""
..WW.......
.mmssss....
mmmsKXss...
mmmmmmmmss.
KmmmmmmmmmK
.dDKKKKKfK.
""", (2, 4)),
}


def dice_rattle(c, x, y, n=4, shake=0, ang=-90.0):
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for k in range(n):
        s = shake * (1 if k % 2 else -1) * (k / max(1, n - 1))
        die(c, x + ux * k * 3.6 + s, y + uy * k * 3.6, 4, 0, 30 + k * 25 + shake * 10, 0, glow="E")


def diamond_tube(c, pts, radii, own, ring, base=GOLD, dark="dDEf", belly="hwWX", period=5.0):
    """Rattlesnake body along pts: dark diamonds down the back that follow the body, an ivory belly below, a black
    rim wherever this stretch overlaps a different ring (so stacked coils stay separate)."""
    seglen = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    s0 = [0.0]
    for L in seglen: s0.append(s0[-1] + L)
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r0, r1 = radii[i], radii[i + 1]
        L2 = max(1e-6, seglen[i] ** 2)
        R = max(r0, r1) + 1.5
        for y in range(int(math.floor(min(y0, y1) - R)), int(math.ceil(max(y0, y1) + R)) + 1):
            for x in range(int(math.floor(min(x0, x1) - R)), int(math.ceil(max(x0, x1) + R)) + 1):
                t = max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / L2))
                qx, qy = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                r = r0 + (r1 - r0) * t
                ox, oy = x - qx, y - qy
                dist = math.hypot(ox, oy)
                if dist > r + 0.75: continue
                key = (x, y)
                if dist > r + 0.1:
                    if key not in own or own[key] != ring:
                        if key not in own or own[key] < ring:
                            c.put(x, y, "K"); own[key] = ring
                    continue
                if key in own and own[key] > ring: continue
                # signed distance across the body: + towards the screen-down side
                tx, ty = (x1 - x0), (y1 - y0)
                nx, ny = -ty, tx
                if ny < 0: nx, ny = -nx, -ny
                nl = math.hypot(nx, ny) or 1.0
                d = (ox * nx + oy * ny) / nl
                sa = s0[i] + t * seglen[i]
                l = -d / max(r, 0.5) * 0.7 + 0.15 - (0.25 if dist > r - 0.6 else 0)
                if d > 0.5 * r:
                    ch = pick(belly, l)
                else:
                    u = abs((sa % period) - period / 2.0) + abs(d + 0.25 * r) * 1.3
                    ch = ("K" if u < 0.6 else pick(dark, l)) if u < 1.7 else ("K" if u < 2.1 else pick(base, l))
                c.put(x, y, ch); own[key] = ring


def rattler(neck=((7, -6), (10, -9)), head=(12, -11), head_ang=0.0, face="shut", tail=(-14, -12), shake=0,
            coil_ph=0.0, dx=0.0, dy=0.0, extra=None, extra_back=None, over=None, spit=None):
    c = Canvas()
    if extra_back: extra_back(c)
    own = {}
    # a spiral pile: the tail starts at the top centre and winds outward and down for 2.25 turns
    turns = 2.25
    spiral = []
    N = 60
    for j in range(N + 1):
        t = j / float(N)
        a = -math.pi / 2 + t * turns * 2 * math.pi + coil_ph * 0.25
        rx = 3.5 + 9.5 * t
        spiral.append((dx + rx * math.cos(a), dy - 11.5 + 8.5 * t + rx * 0.3 * math.sin(a), 1.4 + 1.7 * min(1, t * 1.6)))
    # draw stretches back to front (painter's order by screen y), each its own ring id so seams get a rim
    chunks = []
    for j in range(0, N, 3):
        seg = spiral[j:j + 4]
        chunks.append((sum(p[1] for p in seg) / len(seg), j, seg))
    # tail rising from the pile's top to the dice rattle
    tp = [(dx - 1, dy - 12), (dx - 6, dy - 13), tail]
    diamond_tube(c, tp, [1.6, 1.3, 1.0], own, -1)
    dice_rattle(c, tail[0], tail[1] - 1.5, 4, shake)
    for _, j, seg in sorted(chunks):
        diamond_tube(c, [(x, y) for x, y, r in seg], [r for x, y, r in seg], own, j)
    # neck up out of the front of the outer coil
    end = spiral[-1]
    pts = [(end[0], end[1])] + [(x + dx, y + dy) for x, y in neck] + [(head[0] + dx - 1, head[1] + dy + 0.5)]
    sp, sr = snake_path(pts, [3.0, 2.6, 2.2, 2.0][:len(pts)] + [2.0] * max(0, len(pts) - 4))
    diamond_tube(c, sp, sr, own, 1000)
    hp = Canvas(); hp.part(VIPER_HEAD[face], 0, 0)
    for (x, y, ch) in ((0, -4, "W"), (-1, -5, "W"), (-1, -6, "h"), (2, -4, "W"), (2, -5, "w"), (3, -6, "h")):
        hp.put(x, y, ch)
    hs = rot_spr(hp.spr(), head_ang, (0, 0)) if head_ang else hp.spr()
    SK.paste(c, hs, *P(head[0] + dx, head[1] + dy))
    if spit:
        sx, sy, n = spit
        for k in range(n):
            c.put(*P(sx + k * 1.5, sy + (k % 2)), "V" if k else "G")
    if extra: extra(c)
    return finish(c, over)


def build_rattler(outdir):
    Rt = rattler
    idle = [Rt(shake=0), Rt(shake=1, coil_ph=0.5, head=(12, -11.5)), Rt(shake=-1, coil_ph=1.0, head=(12.5, -12)),
            Rt(shake=1, coil_ph=0.5, head=(12, -11.5))]
    run = [Rt(coil_ph=i * 1.4, dx=[0, 0.5, 1, 0.5, 0, -0.5][i], neck=((8, -5), (12, -7)), head=(15, -8), head_ang=10,
              shake=(i % 2) * 2 - 1, tail=(-15, -10)) for i in range(6)]
    # Spit: rear back (0-1), jaws wide (2), SPIT (3: the glob leaves the mouth at (21, -12)), follow, settle
    spit = [Rt(neck=((5, -7), (6, -12)), head=(7, -15), head_ang=-15),
            Rt(neck=((4, -8), (4, -13)), head=(5, -17), head_ang=-25, face="gape"),
            Rt(neck=((7, -7), (11, -11)), head=(14, -13), head_ang=-5, face="gape"),
            Rt(neck=((8, -6), (13, -9)), head=(16, -11), face="gape", spit=(25, -12, 3)),
            Rt(neck=((8, -6), (12, -9)), head=(15, -11), face="gape"),
            Rt(neck=((7, -6), (11, -9)), head=(13, -11)), Rt()]
    # Rattle (special): the dice rise high (0-1), SHAKE (2-5: 4 = the ring goes out), settle
    rat = [Rt(tail=(-13, -16), shake=0, face="shut"), Rt(tail=(-11, -20), shake=1, face="gape", head=(11, -13))]
    for k in range(4):
        rat.append(Rt(tail=(-11 + (k % 2), -22), shake=[2, -2, 2, -2][k], face="gape", head=(11, -14), coil_ph=k * 0.3,
                      extra=lambda c, k=k: [c.put(-16 - (k % 2), -30 + j * 3, "S") for j in range(3)] +
                      [c.put(-5 + (k % 2), -31 + j * 3, "S") for j in range(3)]))
    rat += [Rt(tail=(-13, -16), shake=1), Rt()]
    d0 = Rt(neck=((5, -7), (5, -12)), head=(4, -15), head_ang=-35, face="gape", shake=2)
    d1 = Rt(neck=((8, -5), (12, -6)), head=(15, -6), head_ang=40, face="dead", tail=(-14, -8))
    d2 = Rt(neck=((9, -4), (14, -3)), head=(17, -2), head_ang=80, face="dead", tail=(-16, -4))
    corpse = grounded(d2)
    knock = Rt(neck=((5, -7), (4, -12)), head=(3, -14), head_ang=-30, face="gape", shake=2)
    anims = [("Idle", idle, [0.18, 0.12, 0.18, 0.12]), ("Run", run, [0.08] * 6),
             ("Spit", spit, [0.12, 0.1, 0.08, 0.06, 0.1, 0.12, 0.12]),
             ("Rattle", rat, [0.12, 0.1, 0.06, 0.06, 0.06, 0.06, 0.12, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxRattler", anims, outdir, scale=5)


# ------------------------------------------------------------------ NUTCRACKER (T3, Marionette's): the doll cut free
# of its strings and made a soldier: varnished wood face, a white beard over a great hinged jaw, a tall black shako,
# a royal-blue coat with gold buttons, brass ball joints and the Marionette's gold spring for a knee; frayed string
# ends still hang from its wrists and hat
COAT = "mbbU"


def nut_head(c, x, y, jaw=0.0, eye="open", tilt=0.0):
    """Head whose neck point is (x, y); jaw: how far the bearded jaw drops (px)."""
    T = Xf(tilt, (x, y))
    # skull block
    poly(c, [T(x - 3.5, y - 9), T(x + 4, y - 9), T(x + 4.5, y - 3), T(x - 3.5, y - 3)], MWOOD_L, bias=0.25)
    # shako with a gold band, a gold plume and a red-white cockade
    poly(c, [T(x - 3.5, y - 13.5), T(x + 3.5, y - 14), T(x + 4.2, y - 9), T(x - 3.8, y - 9)], BLK, bias=0.1)
    for k in range(-3, 5): c.put(*P(*T(x + k, y - 10)), "z" if k % 2 else "Z")
    c.put(*P(*T(x + 1, y - 12)), "E"); c.put(*P(*T(x + 1, y - 11)), "X")
    for k, (px, py) in enumerate(((0, -15), (-1, -16), (0, -17))):
        c.put(*P(*T(x + px, y + py)), "Z" if k % 2 else "z")
    # eyes, painted cheek, nose
    ex = "K" if eye == "open" else "k"
    c.put(*P(*T(x + 1, y - 7)), "X"); c.put(*P(*T(x + 2, y - 7)), ex)
    c.put(*P(*T(x + 3.5, y - 6)), "T"); c.put(*P(*T(x + 4.5, y - 6)), "t")
    c.put(*P(*T(x + 2, y - 5)), "f")
    if eye == "dead":
        c.put(*P(*T(x + 1, y - 7)), "K"); c.put(*P(*T(x + 2, y - 8)), "K")
    # white moustache + the hinged jaw with its teeth and beard
    for k in range(0, 6): c.put(*P(*T(x - 1 + k, y - 4)), "X" if k % 2 else "W")
    jy = y - 3 + jaw
    if jaw > 0.5:
        poly(c, [T(x - 1, y - 3.5), T(x + 4.5, y - 3.5), T(x + 4.5, jy), T(x - 1, jy)], "dDDd", lit="flat")
        for k in range(0, 5, 2): c.put(*P(*T(x + k, y - 3)), "X")
    poly(c, [T(x - 1.5, jy), T(x + 4.5, jy), T(x + 4.5, jy + 2.5), T(x + 1, jy + 4.5), T(x - 2, jy + 3)], "wWXX", bias=0.2)
    for k in range(0, 5, 2): c.put(*P(*T(x + k, jy)), "X")
    c.put(*P(*T(x - 3.5, y - 5)), "z")      # jaw hinge pin


def frayed(c, x, y, ln=3, sway=0.0):
    for k in range(ln):
        c.put(*P(x + sway * k / ln, y + k), "S" if k < ln - 1 else "s")


def nutcracker(dx=0.0, dy=0.0, lean=0.0, feet=(-3, 3), jaw=0.0, eye="open", fh=(8, -19), bh=(-6, -17), sa=-60.0,
               sabre=True, sway=0.0, extra=None, extra_back=None, over=None, head_tilt=0.0, knees=(1, 1)):
    c = Canvas()
    if extra_back: extra_back(c)
    fh, bh = (fh[0], fh[1] + 2.5), (bh[0], bh[1] + 2.5)      # hand targets were authored for a 2.5 px taller body
    hip = (dx, -10 + dy)
    T = Xf(lean, hip)
    # back arm
    shb = T(hip[0] - 3.5, hip[1] - 10)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0] + dx, bh[1] + dy, 4.5, 4.5, -1)
    tube(c, [shb, (ex, ey)], [1.4, 1.2], "mbb")
    tube(c, [(ex, ey), (hx, hy)], [1.1, 1.0], MWOOD_D)
    c.put(*P(ex, ey), "z"); c.put(*P(hx, hy), "X")
    frayed(c, hx, hy + 1, 3, -sway)
    # legs: white trousers, brass ball knees (a gold spring on the near knee), black boots
    for i, fx in enumerate(feet):
        hp = (hip[0] + (-1.8 if i == 0 else 1.8), hip[1])
        (kx, ky), (ax, ay) = ik(hp[0], hp[1], dx + fx, -1, 4.6, 4.8, knees[i])
        tube(c, [hp, (kx, ky)], [1.6, 1.4], "hwWW" if i else "hhww")
        tube(c, [(kx, ky), (ax, ay)], [1.5, 1.4], BLK)
        if i:
            spring(c, kx - 0.5, ky - 1.5, kx + 0.5, ky + 1.5, 2, amp=1.3)
        else:
            c.put(*P(kx, ky), "z")
        for k in range(-1, 3): c.put(*P(ax + k, 0), "K")
        c.put(*P(ax + 2, -1), "m"); c.put(*P(ax, -3), "s")
    # coat: royal blue with gold buttons, white cross-belt, gold epaulettes, a skirt flaring over the hips
    poly(c, [T(hip[0] - 4, hip[1] - 11), T(hip[0] + 4, hip[1] - 11), T(hip[0] + 4.5, hip[1] + 1), T(hip[0] - 4.5, hip[1] + 1)],
         COAT, bias=0.1)
    a, b = T(hip[0] - 3.5, hip[1] - 10), T(hip[0] + 3.5, hip[1] - 1)
    line(c, *a, *b, "X")
    for k in range(4): c.put(*P(*T(hip[0] + 2, hip[1] - 9 + k * 2.5)), "Z")
    for k in range(-4, 5): c.put(*P(*T(hip[0] + k, hip[1] - 1)), "K" if k % 2 else "m")      # belt
    c.put(*P(*T(hip[0] + 1, hip[1] - 1)), "z")
    for k in range(-4, -1): c.put(*P(*T(hip[0] + k, hip[1] - 11)), "z")
    # head
    neck = T(hip[0] + 0.5, hip[1] - 11)
    nut_head(c, neck[0], neck[1], jaw, eye, head_tilt)
    hat = Xf(head_tilt, neck)(neck[0] - 3, neck[1] - 13.5)
    frayed(c, hat[0], hat[1] - 3, 3, sway)
    # front arm + sabre
    shf = T(hip[0] + 3.5, hip[1] - 10)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0] + dx, fh[1] + dy, 4.5, 4.5, 1)
    if sabre:
        ux, uy = math.cos(math.radians(sa)), math.sin(math.radians(sa))
        tip = (hx + ux * 11, hy + uy * 11)
        line(c, hx + ux * 1.5, hy + uy * 1.5, *tip, "u")
        line(c, hx + ux * 1.5 + uy * 0.8, hy + uy * 1.5 - ux * 0.8, tip[0] + uy * 0.4, tip[1] - ux * 0.4, "c", over=False)
        c.put(*P(*tip), "c")
        line(c, hx - uy * 1.5, hy + ux * 1.5, hx + uy * 1.5, hy - ux * 1.5, "z")     # guard
    tube(c, [shf, (ex, ey)], [1.5, 1.3], COAT)
    tube(c, [(ex, ey), (hx, hy)], [1.2, 1.0], MWOOD_L)
    c.put(*P(ex, ey), "z"); c.put(*P(hx, hy), "X"); c.put(*P(hx, hy + 1), "W")
    frayed(c, hx - 1, hy + 2, 3, sway)
    if extra: extra(c)
    return finish(c, over)


def build_nutcracker(outdir):
    Nc = nutcracker
    idle = [Nc(), Nc(jaw=1, sway=1, dy=-0.3), Nc(jaw=0, sway=2, dy=-0.3, sa=-62), Nc(jaw=1, sway=1)]
    stride = [(-5, 3), (-2, 1), (1, -2), (4, -5), (1, -2), (-2, 1)]
    run = [Nc(feet=stride[i], lean=5, dy=[0, -1, -1.5, -1, 0, 0][i], sa=-35, fh=(9, -18), bh=(-6 + (i % 3), -15),
              sway=[-1, 0, 1, 2, 1, 0][i], knees=(1, 1)) for i in range(6)]

    def arc(c, pts, ch="c"):
        for a, b in zip(pts, pts[1:]): line(c, *a, *b, ch)
    # Sabre: raise it high (0-1), SLASH down and forward (2-3: blade sweeps x 6..20), follow through, back
    sab = [Nc(fh=(4, -27), sa=-120, jaw=1), Nc(fh=(2, -29), sa=-150, jaw=1, lean=-4),
           Nc(fh=(10, -22), sa=-30, lean=6, extra=lambda c: arc(c, [(4, -31), (12, -29), (19, -22)], "S")),
           Nc(fh=(12, -16), sa=20, lean=10, feet=(-3, 5), extra=lambda c: arc(c, [(18, -24), (22, -15), (20, -7)], "S")),
           Nc(fh=(11, -14), sa=40, lean=8, feet=(-3, 5)), Nc(fh=(9, -17), sa=-20, lean=3), Nc()]
    # Crack (special): the jaw drops wide (0-1), lean back (2), LUNGE (3), CLAMP (4: the grab), crunch-crunch-crunch
    # (5-7), spit it out (8)
    crack = [Nc(jaw=2, eye="open"), Nc(jaw=4, lean=-6, fh=(5, -22), bh=(-8, -20)),
             Nc(jaw=5, lean=-10, fh=(4, -24), bh=(-9, -21), sa=-110),
             Nc(jaw=5, lean=16, dx=3, feet=(-3, 7), fh=(12, -18), sa=-20),
             Nc(jaw=0, lean=18, dx=4, feet=(-3, 8), fh=(12, -17), sa=-10, head_tilt=8,
                extra=lambda c: [sparkle(c, 15, -23, 1, "W", "X")]),
             Nc(jaw=2, lean=16, dx=4, feet=(-3, 8), fh=(12, -17), sa=-10, head_tilt=6),
             Nc(jaw=0, lean=18, dx=4, feet=(-3, 8), fh=(12, -17), sa=-10, head_tilt=8,
                extra=lambda c: [sparkle(c, 14, -22, 1, "W", "X")]),
             Nc(jaw=2, lean=14, dx=3, feet=(-3, 7), fh=(11, -18), sa=-20),
             Nc(jaw=1, lean=4, dx=1)]
    d0 = Nc(lean=-12, jaw=4, eye="dead", fh=(6, -24), bh=(-9, -22), sa=-130, head_tilt=-10)
    d1 = grounded(rot_spr(Nc(lean=-4, jaw=5, eye="dead", sabre=False, fh=(4, -16), bh=(-7, -16)), -45, (0, -1)))
    d2 = grounded(rot_spr(Nc(lean=-2, jaw=6, eye="dead", sabre=False, fh=(4, -15), bh=(-7, -15)), -86, (0, -1)))
    corpse = merge(d2, Spr({(18, -1): "c", (19, -1): "u", (20, -1): "u", (21, -1): "u", (17, -1): "z"}))
    knock = Nc(lean=-14, dx=-1, jaw=3, fh=(6, -24), bh=(-9, -21), sa=-120, head_tilt=-8, feet=(-1, 5))
    anims = [("Idle", idle, [0.22, 0.16, 0.22, 0.16]), ("Run", run, [0.08] * 6),
             ("Sabre", sab, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Crack", crack, [0.1, 0.1, 0.1, 0.06, 0.12, 0.12, 0.12, 0.12, 0.14])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxNutcracker", anims, outdir, scale=5)


# ------------------------------------------------------------------ THE ORACLE (T3, Fortune Teller's): the teller
# sits cross-legged on a crystal ball grown as big as herself, a halo of tarot cards fanned behind her hood, a third
# eye open on her brow under the Card Sharp's green visor
def oracle(dy=0.0, hover=2.0, ph=0, head="gaze", halo_ph=0.0, halo_r=10.0, halo_n=5, fh=(8, -21), bh=(-8, -21),
           eye3=1, glow=1, lean=0.0, extra=None, extra_back=None, over=None, trail=0.0, cards_in_hand=True):
    c = Canvas()
    if extra_back: extra_back(c)
    by = -hover - 6 + dy
    # halo of tarot cards behind (drawn first)
    hc = (0.5, by - 21)
    for k in range(halo_n):
        a = math.radians(-170 + (k + 0.5) * 160.0 / halo_n + halo_ph)
        card_face(c, hc[0] + halo_r * math.cos(a), hc[1] + halo_r * 0.6 * math.sin(a), 3.4, 5, "back",
                  ang=math.degrees(a) + 90)
    # smoke trail when gliding
    if trail:
        for j in range(4):
            c.put(*P(-7 - trail - j * 2, by + 2 - (j + ph) % 2), "n" if j < 2 else "q")
    # the great crystal ball (the seat)
    crystal_ball(c, 0, by, 6.0, ph, glow)
    sy = by - 6.5            # seat on top of the ball
    T = Xf(lean, (0, sy))
    # crossed legs: a wide fold of plum robe
    poly(c, [T(-8, sy + 0.5), T(8, sy + 0.5), T(6.5, sy - 3.5), T(-6.5, sy - 3.5)], ROBE, bias=0.15)
    for k in (-5, 5): c.put(*P(*T(k, sy - 0.5)), "w")         # bare goblin toes
    # back arm holding a card up
    shb = T(-3, sy - 10)
    (ex, ey), (hx, hy) = ik(shb[0], shb[1], bh[0], bh[1] + dy, 4.0, 4.0, -1)
    tube(c, [shb, (ex, ey), (hx, hy)], [1.0, 0.9, 0.7], "qqn")
    if cards_in_hand: card_face(c, hx, hy - 2, 3, 4.5, "back", ang=-15)
    # torso + crimson shawl with gold coins
    poly(c, [T(-3.5, sy - 11.5), T(3.5, sy - 11.5), T(5, sy - 3), T(-5, sy - 3)], ROBE, bias=0.1)
    poly(c, [T(-4.2, sy - 12), T(4, sy - 12), T(4.5, sy - 9), T(0.5, sy - 6.5), T(-4.6, sy - 8.5)], CRIM, bias=0.15)
    for k, (fx_, fy_) in enumerate(((-4, -8), (-2, -7), (0, -6.5), (2, -7.5), (3.6, -9))):
        c.put(*P(*T(fx_, sy + fy_)), "Z" if k % 2 else "z")
    for sx_, sy_ in ((-3, -5), (2, -4.5)): c.put(*P(*T(sx_, sy + sy_)), "e")     # stitched stars
    # head, visor, third eye
    neck = T(1.5, sy - 12)
    c.part(TELLER_HEAD[head], *P(*neck))
    hx0, hy0 = P(*neck)
    for x in range(-2, 5): c.raw.put(hx0 + x, hy0 - 4, "M" if x < 3 else "H")
    c.raw.put(hx0 + 5, hy0 - 3, "H")
    e3 = {0: "K", 1: "L", 2: "y"}[eye3]
    c.raw.put(hx0 + 1, hy0 - 5, e3); c.raw.put(hx0 + 2, hy0 - 5, "N" if eye3 < 2 else "L")
    if eye3 == 2:
        for (x, y) in ((1, -7), (3, -6), (-1, -6), (4, -5)): c.raw.put(hx0 + x, hy0 + y, "L")
    # card earrings (the Card Sharp's deck)
    c.raw.put(hx0 - 2, hy0, "X"); c.raw.put(hx0 - 2, hy0 + 1, "E")
    # front arm holding a card out
    shf = T(3, sy - 10)
    (ex, ey), (hx, hy) = ik(shf[0], shf[1], fh[0], fh[1] + dy, 4.0, 4.0, 1)
    tube(c, [shf, (ex, ey)], [1.1, 0.9], "qnN")
    line(c, ex, ey, hx, hy, "w")
    c.put(*P(ex, ey), "z")
    if cards_in_hand: card_face(c, hx + 1, hy - 1.5, 3, 4.5, "Hearts", ang=10)
    if extra: extra(c)
    return finish(c, over)


def build_oracle(outdir):
    O = oracle
    idle = [O(ph=0), O(dy=-0.5, ph=1, halo_ph=4), O(dy=-1, ph=2, halo_ph=8, head="shut"), O(dy=-0.5, ph=3, halo_ph=4)]
    run = [O(lean=8, dy=[0, -0.5, -1, -1, -0.5, 0][i], ph=i, trail=2 + (i % 3), halo_ph=-6, fh=(9, -19)) for i in range(6)]
    # Gaze: the third eye opens (0-2), cards pressed to the brow, the eye FLARES and looses its orb (3: from (8, -33)),
    # hold, close
    gaze = [O(eye3=1, head="gaze"), O(eye3=2, head="glare", fh=(5, -27), bh=(-4, -27), glow=2),
            O(eye3=2, head="glare", fh=(4, -28), bh=(-4, -28), glow=2, halo_ph=6),
            O(eye3=2, head="glare", fh=(11, -24), bh=(-5, -27), glow=2, lean=6,
              extra=lambda c: [sparkle(c, 9, -33, 2, "N", "L")]),
            O(eye3=2, head="glare", fh=(10, -22), lean=4), O(eye3=1, fh=(9, -21)), O(eye3=1)]
    # Foresight (special): eyes shut (0), the halo spins faster and wider (1-5: 4 = foresight), it settles (6-7)
    fore = [O(head="shut", eye3=0)]
    for k in range(5):
        fore.append(O(head="shut" if k < 2 else "glare", eye3=2, halo_ph=20 + k * 26, halo_r=11 + min(k, 3), halo_n=6,
                      glow=2, ph=k, fh=(7, -26), bh=(-6, -26),
                      extra=lambda c, k=k: [sparkle(c, -12 + 2 * (k % 3), -30 + k, 1, "N", "L"),
                                            sparkle(c, 12 - 2 * (k % 2), -25 - k, 1, "N", "L")]))
    fore += [O(halo_ph=8, glow=1, eye3=1), O(eye3=1)]
    d0 = O(lean=-14, head="glare", eye3=2, halo_r=13, fh=(5, -28), bh=(-9, -27))
    d1 = O(lean=-24, hover=1, head="dead", eye3=0, halo_n=3, halo_r=14, cards_in_hand=False)
    d2 = grounded(rot_spr(O(hover=0, head="dead", eye3=0, halo_n=0, cards_in_hand=False), -60, (0, -1)))
    corpse = oracle_corpse()
    knock = O(lean=-18, head="glare", eye3=2, fh=(5, -26), bh=(-9, -25), dy=-1)
    anims = [("Idle", idle, [0.2, 0.15, 0.2, 0.15]), ("Run", run, [0.08] * 6),
             ("Gaze", gaze, [0.12, 0.1, 0.1, 0.06, 0.12, 0.12, 0.12]),
             ("Foresight", fore, [0.12, 0.08, 0.08, 0.08, 0.1, 0.1, 0.12, 0.12])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("JinxOracle", anims, outdir, scale=5)


def oracle_corpse():
    c = Canvas()
    poly(c, [(-10, 0), (-8, -3), (-3, -4), (3, -3), (6, -1), (7, 0)], ROBE, bias=0.1)
    poly(c, [(-7, -2), (-3, -4.5), (1, -4), (-1, -1)], CRIM, bias=0.15)
    c.part(TELLER_HEAD["dead"], -9, -1)
    crystal_ball(c, 12, -4, 4.0, 0, 0)
    for x, y in ((11, -6), (12, -5), (13, -4), (12, -3)): c.put(x, y, "K")
    for k, (x, ang) in enumerate(((-14, 30), (16, -20), (2, 80))):
        card_face(c, x, -1.5, 3, 4.5, "back", ang=ang)
    return grounded(finish(c))


# ------------------------------------------------------------------ v0.10 effect sheets
def _o(c):
    return outline(c.spr())


def flat_card(c, cx, cy, w=8.0, d=3.0, back=True, glint=False):
    """A card lying on the floor (seen from the game's tilted camera): a flat parallelogram."""
    pts = [(cx - w / 2 + 1, cy - d), (cx + w / 2 + 1, cy - d), (cx + w / 2 - 1, cy), (cx - w / 2 - 1, cy)]
    poly(c, pts, "wWXX", lit="flat", bias=0.3)
    if back:
        inner = [(cx - w / 2 + 2, cy - d + 1), (cx + w / 2, cy - d + 1), (cx + w / 2 - 1.5, cy - 0.6), (cx - w / 2 - 0.5, cy - 0.6)]
        poly(c, inner, harl(cx, cy, 2, "DDEE", "KKmm"), lit="flat", bias=0.2)
    if glint:
        c.put(*P(cx + w / 2 - 1, cy - d), "y")


def fx_trap_land():
    out = []
    for k, (y, ang) in enumerate(((-14, 40), (-9, -30), (-4, 20))):
        c = Canvas(); card_face(c, (k % 2) * 2 - 1, y, 5, 7, "back", ang=ang); out.append(_o(c))
    c = Canvas(); flat_card(c, 0, 0); out.append(_o(c))
    return out


def fx_trap_lie():
    out = []
    for g in (False, True):
        c = Canvas(); flat_card(c, 0, 0, glint=g); out.append(_o(c))
    return out


def fx_trap_snap():
    out = []
    for k in range(6):
        c = Canvas(); o = Canvas()
        if k == 0:
            card_face(c, 0, -4, 6, 8, "Spades")
        elif k in (1, 2, 3):
            n = [3, 3, 2][k - 1]
            ln = [6, 9, 6][k - 1]
            card_face(c, 0, -3, 6, 6, "Spades" if k < 3 else "back")
            for j in range(n):
                a = -90 + (j - (n - 1) / 2.0) * 35
                ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
                line(c, ux * 2, -5 + uy * 2, ux * ln, -5 + uy * ln, "m")
                spade_blade(c, ux * ln, -5 + uy * ln, a)
            if k == 2:
                for (x0, y0, x1, y1) in ((-9, -12, 9, -2), (-8, -3, 8, -13)):
                    line(o, x0, y0, x1, y1, "X")
        else:
            rnd = random.Random(k)
            for j in range(6 if k == 4 else 3):
                x, y = rnd.uniform(-8, 8), rnd.uniform(-10, -1) + (k - 4) * 3
                card_face(c, x, y, 2, 3, "back" if j % 2 else "Spades", ang=rnd.uniform(0, 180))
        out.append(merge(_o(c), o.spr()))
    return out


def fx_crunch():
    out = []
    for k in range(5):
        c = Canvas(); o = Canvas()
        rnd = random.Random(20 + k)
        if k < 2:
            # the jaws close: two white rows of teeth meeting over the victim's chest
            gap = [5, 1][k]
            for x in range(-6, 7):
                c.put(x, -10 - gap, "X" if x % 2 else "W"); c.put(x, -11 - gap, "w")
                c.put(x, -9 + gap * 0 + (0 if k else 0), "X" if x % 2 == 0 else "W"); c.put(x, -8, "w")
        if k >= 1:
            # nut-shell splinters flying out
            for j in range(4 + 2 * k):
                a = rnd.uniform(0, 2 * math.pi); r = 2 + k * 2.5 + rnd.uniform(0, 2)
                x, y = r * math.cos(a), -9 + r * 0.7 * math.sin(a)
                c.put(*P(x, y), "t" if j % 3 else "T"); c.put(*P(x + 1, y), "k")
            if k <= 2:
                for a in range(0, 360, 60):
                    ux, uy = math.cos(math.radians(a + k * 20)), math.sin(math.radians(a + k * 20))
                    line(o, ux * (3 + k), -9 + uy * (3 + k) * 0.7, ux * (6 + k * 2), -9 + uy * (6 + k * 2) * 0.7, "y" if k == 1 else "Z")
        out.append(merge(_o(c), o.spr()))
    return out


def fx_eye_orb():
    out = []
    for k in range(4):
        c = Canvas(); o = Canvas()
        for j in range(4):
            o.put(-4 - j * 2, (k + j) % 3 - 1, "L" if j < 2 else "n")
        ell(c, 0, 0, 3.0, 3.0, "wWXX", bias=0.2)
        ell(c, 1.2, 0, 1.6, 1.8, VIOL, bias=0.2)
        c.put(2, 0, "K"); c.put(2, -1 if k % 2 else 0, "K")
        c.put(-1, -2, "y")
        c.put(-1, 1, "E")      # a red vein
        out.append(merge(_o(c), o.spr()))
    return out


FORE_EYE = [".LLL.", "LcKcL", ".LLL."]


def fx_foresight(n):
    out = []
    for k in range(2):
        c = Canvas()
        for j in range(n):
            x = (j - (n - 1) / 2.0) * 6
            glyph_px(c, FORE_EYE if k == 0 or j != n - 1 else [".....", "LLLLL", "....."], x, -2, {"L": "L", "c": "c", "K": "K"})
        out.append(_o(c))
    return out


def fx_blink():
    out = []
    for k in range(5):
        c = Canvas()
        rnd = random.Random(40 + k)
        keep = [1.0, 0.75, 0.5, 0.3, 0.12][k]
        for y in range(-26, 0):
            for x in range(-5, 6):
                if (x / 5.5) ** 2 + ((y + 13) / 13.5) ** 2 > 1: continue
                if rnd.random() > keep: continue
                c.put(x + k, y - k, "n" if (x + y) % 3 else "L")
        for j in range(3 + k):
            sparkle(c, rnd.uniform(-8, 8), rnd.uniform(-28, -4), 1, "N", "L")
        out.append(c.spr())
    return out


def fx_gaze():
    out = []
    L = 62
    for k in range(6):
        c = Canvas()
        w = [0, 1, 2, 2, 1, 0][k]
        reach = [18, 40, L, L, L, L][k]
        for x in range(0, reach):
            if k == 5 and (x * 7) % 5 > 1: continue
            for dy in range(-w, w + 1):
                ch = "y" if dy == 0 else ("Z" if abs(dy) == 1 else "S")
                if k == 4 and dy == 0: ch = "Z"
                c.put(x, dy, ch)
            if k in (2, 3) and x % 6 == (k * 3) % 6:
                c.put(x, -w - 1, "U"); c.put(x + 1, w + 1, "S")
        if k <= 3:
            sparkle(c, 0, 0, 2 if k else 1, "Z", "y")
        if k in (2, 3):
            sparkle(c, reach - 1, 0, 1, "U", "c")
        out.append(c.spr())
    return out


def fx_venom():
    out = []
    for k in range(4):
        c = Canvas(); o = Canvas()
        ell(c, 0, 0, 2.2, 1.8, "vVVG", bias=0.2)
        c.put(-1, -1, "G")
        for j in range(3):
            o.put(-3 - j * 2, (j + k) % 2, "V" if j < 2 else "v")
        o.put(-1, 2 + k % 2, "v")
        out.append(merge(_o(c), o.spr()))
    return out


def fx_venom_pool():
    out = []
    for k in range(8):
        c = Canvas()
        rnd = random.Random(60 + k)
        if k < 2:
            for j in range(7):
                a = math.radians(-160 + j * 23)
                r = 3 + 3 * k
                c.put(*P(r * math.cos(a), -1 + r * 0.6 * math.sin(a)), "G" if j % 2 else "V")
            ell(c, 0, -1, 3 + 2 * k, 1.5 + k * 0.5, "vVVG", bias=0.1, flat=True)
        else:
            rx = 9 - (2 if k == 7 else 0)
            ell(c, 0, -1.5, rx, 3.0, "vvVV", bias=0.0)
            ell(c, -2, -2, rx * 0.5, 1.2, "VVGG", bias=0.1)
            if k < 7:
                for j in range(2):
                    x = rnd.uniform(-6, 6)
                    c.put(*P(x, -2 - (k % 2)), "G"); c.put(*P(x, -3 - (k % 2)), "y" if j else "G")
        out.append(_o(c) if k < 7 else dissolve(_o(c), 0.55, 9))
    return out


def fx_rattle_ring():
    out = []
    for k in range(6):
        c = Canvas()
        rx = 6 + k * 5.5; ry = rx * 0.42
        for i in range(48):
            a = i * 2 * math.pi / 48
            if (i // 3 + k) % 2: continue
            x, y = rx * math.cos(a), -3 + ry * math.sin(a)
            c.put(*P(x, y), "Z" if k < 3 else ("z" if k < 5 else "e"))
            if k < 4: c.put(*P(x * 0.92, y - 1), "W" if k < 2 else "w")
        if k < 3:
            for j in range(3):
                a = j * 2.1 + k
                die(c, rx * 0.7 * math.cos(a), -3 + ry * 0.7 * math.sin(a) - 2, 3, a * 40, 30, 0)
        out.append(c.spr())
    return out


def fx_club_slam():
    out = []
    for k in range(5):
        c = Canvas(); o = Canvas()
        rnd = random.Random(80 + k)
        # floor cracks
        for a in (-170, -140, -30, -5, 20, 160):
            ln = [4, 9, 12, 12, 10][k]
            line(o, 0, 0, ln * math.cos(math.radians(a)), 0.4 * ln * math.sin(math.radians(a)), "K" if k < 4 else "m")
        if 1 <= k <= 3:
            # a club-shaped puff of dust rising
            s = [0.8, 1.2, 1.4][k - 1]
            for (x, y, r) in ((0, -7, 3), (-3.5, -4.5, 2.8), (3.5, -4.5, 2.8)):
                ell(c, x * s, y * s - k, r * s, r * s * 0.9, "sSSU", bias=0.1 - 0.15 * k)
            for j in range(4 + k * 2):
                c.put(*P(rnd.uniform(-10, 10), rnd.uniform(-12, -1)), "S")
        if k == 0:
            sparkle(c, 0, -2, 2, "W", "X")
        out.append(merge(_o(c) if c.px else Spr({}), o.spr()))
    return out


def fx_guard():
    out = []
    for k in range(4):
        c = Canvas()
        card_face(c, 0, -5 - (1 if k in (1, 2) else 0), 6, 8, "Diamonds")
        if k == 2:
            c.put(3, -9, "y"); c.put(4, -10, "Z")
        out.append(_o(c))
    return out


def fx_riposte():
    out = []
    for k in range(4):
        c = Canvas(); o = Canvas()
        sx = [1.0, 0.55, 0.15, 0.55][k]
        card_face(c, 0, 0, 6, 8, "back" if k == 2 else "Diamonds", sx=sx)
        if k == 0:
            for x, y, ch in ((-2, -3, "z"), (0, -3, "Z"), (2, -3, "z"), (-1, -2, "z"), (1, -2, "z")):
                c.put(x, y, ch)
        for j in range(3):
            o.put(-5 - j * 2, (j + k) % 2, "z" if j < 2 else "e")
        out.append(merge(_o(c), o.spr()))
    return out


def fx_orbit_card():
    out = []
    for k in range(4):
        c = Canvas()
        sx = [1.0, 0.5, 0.15, 0.5][k]
        card_face(c, 0, 0, 5, 7, ["Spades", "back", "back", "Hearts"][k], sx=sx)
        if k == 0: c.put(2, -3, "y")
        out.append(_o(c))
    return out


def chip(c, x, y, sx=1.0, col=("E", "f")):
    a, b = col
    ell(c, x, y, max(0.6, 2.5 * sx), 2.5, a, flat=True)
    ell(c, x, y, max(0.4, 1.4 * sx), 1.4, b, flat=True)
    if sx > 0.6:
        for (dx, dy) in ((0, -2), (0, 2), (-2, 0), (2, 0)):
            c.put(*P(x + dx * sx, y + dy), "X")


def fx_chip():
    out = []
    for k in range(4):
        c = Canvas(); o = Canvas()
        chip(c, 0, 0, [1.0, 0.6, 0.25, 0.6][k])
        for j in range(3):
            o.put(-4 - j * 2, (j + k) % 2, "f" if j < 2 else "D")
        out.append(merge(_o(c), o.spr()))
    return out


def fx_chips(n):
    out = []
    for k in range(2):
        c = Canvas()
        for j in range(n):
            a, b = CHIP_COLS[j % len(CHIP_COLS)]
            for d in (-2, -1, 0, 1, 2):
                c.put(d, -1 - j * 2, b if abs(d) < 2 else a)
                c.put(d, -j * 2, "K" if abs(d) == 2 else a)
        if k == 1:
            c.put(-2, -2 * n, "y")
        out.append(_o(c))
    return out


def fx_d20_shard():
    out = []
    for k in range(4):
        c = Canvas()
        a = math.radians(k * 90)
        pts = [(3.2 * math.cos(a + j * 2.094), 3.2 * math.sin(a + j * 2.094)) for j in range(3)]
        poly(c, pts, RESIN, bias=0.3 - 0.2 * (k % 2))
        for p0, p1 in zip(pts, pts[1:] + pts[:1]): line(c, *p0, *p1, "z")
        out.append(_o(c))
    return out


def fx_crit():
    out = []
    for k in range(7):
        c = Canvas()
        r = [3, 7, 11, 14, 16, 17, 18][k]
        for i in range(16):
            a = math.radians(i * 22.5 + k * 5)
            r0 = r * (0.4 if i % 2 else 0.6)
            ln = r if i % 2 == 0 else r * 0.75
            if k >= 5 and i % 3: continue
            line(c, r0 * math.cos(a), -12 + r0 * 0.75 * math.sin(a), ln * math.cos(a), -12 + ln * 0.75 * math.sin(a),
                 "Y" if i % 2 == 0 else "L")
        if k <= 3:
            sparkle(c, 0, -12, 3 - k // 2, "Z", "y")
        if 2 <= k <= 5:
            glyph_px(c, DIGITS3["2"], -2, -26 - k, {"X": "Y", "o": "K"})
            glyph_px(c, DIGITS3["0"], 2, -26 - k, {"X": "Y", "o": "K"})
        out.append(c.spr())
    return out


def fx_fumble():
    out = []
    for k in range(5):
        c = Canvas()
        rnd = random.Random(90 + k)
        for j in range(5):
            x, y = rnd.uniform(-5, 5) * (1 + k * 0.3), -14 - rnd.uniform(0, 4) - k
            ell(c, x, y, 2, 1.6, "mssS", bias=-0.1 * k)
        if k < 4:
            glyph_px(c, DIGITS3["1"], 0, -24 - k, {"X": "S", "o": "K"})
        out.append(dissolve(_o(c), 1.0 - 0.15 * k, k))
    return out


V10_FX = ["FxJinxTrapCard", "FxJinxCrunch", "FxJinxEyeOrb", "FxJinxForesight", "FxJinxBlink", "FxJinxGaze",
          "FxJinxVenom", "FxJinxVenomPool", "FxJinxRattleRing", "FxJinxClubSlam", "FxJinxGuard", "FxJinxRiposte",
          "FxJinxOrbitCard", "FxJinxChip", "FxJinxChips", "FxJinxD20Shard", "FxJinxCrit"]
FX_NAMES += V10_FX


def build_v10_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxJinxTrapCard"):
        fx_sheet("FxJinxTrapCard", [("Land", fx_trap_land(), [0.06] * 4), ("Lie", fx_trap_lie(), [0.5, 0.15]),
                                    ("Snap", fx_trap_snap(), [0.05, 0.06, 0.08, 0.08, 0.08, 0.1])], outdir)
    if want("FxJinxCrunch"): fx_sheet("FxJinxCrunch", [("Play", fx_crunch(), [0.05, 0.06, 0.07, 0.08, 0.1])], outdir)
    if want("FxJinxEyeOrb"): fx_sheet("FxJinxEyeOrb", [("Fly", fx_eye_orb(), [0.07] * 4)], outdir)
    if want("FxJinxForesight"):
        fx_sheet("FxJinxForesight", [(nm, fx_foresight(n), [0.6, 0.1]) for nm, n in (("One", 1), ("Two", 2), ("Three", 3))], outdir)
    if want("FxJinxBlink"): fx_sheet("FxJinxBlink", [("Play", fx_blink(), [0.05, 0.06, 0.07, 0.08, 0.1])], outdir)
    if want("FxJinxGaze"): fx_sheet("FxJinxGaze", [("Play", fx_gaze(), [0.05, 0.05, 0.12, 0.12, 0.08, 0.08])], outdir)
    if want("FxJinxVenom"): fx_sheet("FxJinxVenom", [("Fly", fx_venom(), [0.07] * 4)], outdir)
    if want("FxJinxVenomPool"):
        fx_sheet("FxJinxVenomPool", [("Play", fx_venom_pool(), [0.05, 0.08, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2])], outdir)
    if want("FxJinxRattleRing"): fx_sheet("FxJinxRattleRing", [("Play", fx_rattle_ring(), [0.05, 0.05, 0.06, 0.06, 0.08, 0.1])], outdir)
    if want("FxJinxClubSlam"): fx_sheet("FxJinxClubSlam", [("Play", fx_club_slam(), [0.05, 0.07, 0.08, 0.1, 0.12])], outdir)
    if want("FxJinxGuard"): fx_sheet("FxJinxGuard", [("Loop", fx_guard(), [0.12] * 4)], outdir)
    if want("FxJinxRiposte"): fx_sheet("FxJinxRiposte", [("Fly", fx_riposte(), [0.05] * 4)], outdir)
    if want("FxJinxOrbitCard"): fx_sheet("FxJinxOrbitCard", [("Fly", fx_orbit_card(), [0.06] * 4)], outdir)
    if want("FxJinxChip"): fx_sheet("FxJinxChip", [("Fly", fx_chip(), [0.05] * 4)], outdir)
    if want("FxJinxChips"):
        fx_sheet("FxJinxChips", [(nm, fx_chips(n), [0.7, 0.1]) for nm, n in
                                 (("One", 1), ("Two", 2), ("Three", 3), ("Four", 4), ("Five", 5))], outdir)
    if want("FxJinxD20Shard"): fx_sheet("FxJinxD20Shard", [("Fly", fx_d20_shard(), [0.05] * 4)], outdir)
    if want("FxJinxCrit"):
        fx_sheet("FxJinxCrit", [("Crit", fx_crit(), [0.04, 0.05, 0.06, 0.08, 0.1, 0.12, 0.14]),
                                ("Fumble", fx_fumble(), [0.08, 0.1, 0.12, 0.14, 0.16])], outdir)


def fx_loaded_pips(n):
    """Loaded Die's stored roll over its head: a small ivory die face showing n, its pips pulsing red."""
    out = []
    pts = {1: [(0, 0)], 2: [(-2, -2), (2, 2)], 3: [(-2, -2), (0, 0), (2, 2)], 4: [(-2, -2), (2, -2), (-2, 2), (2, 2)],
           5: [(-2, -2), (2, -2), (0, 0), (-2, 2), (2, 2)], 6: [(-2, -2), (2, -2), (-2, 0), (2, 0), (-2, 2), (2, 2)]}[n]
    for k in range(2):
        c = Canvas()
        poly(c, [(-3.5, -7.5), (3.5, -7.5), (3.5, -0.5), (-3.5, -0.5)], IVORY, bias=0.3, lit="flat")
        line(c, 3.5, -7.5, 3.5, -0.5, "w"); line(c, -3.5, -0.5, 3.5, -0.5, "w")
        for (u, v) in pts:
            c.put(u, -4 + v, "R" if k else "E")
        out.append(_o(c))
    return out


def fx_imprint():
    """Loaded Die's loaded slam: the die face stamps into the floor, cracks run out, red pips flash in the dent."""
    out = []
    for k in range(6):
        c = Canvas(); o = Canvas()
        w = [5, 8, 9, 9, 9, 9][k]
        if k < 5:
            poly(c, [(-w, -w * 0.42), (w, -w * 0.42), (w - 2, w * 0.15), (-w - 2, w * 0.15)], "kssS" if k else "hwWX",
                 lit="flat", bias=0.1 - 0.1 * k)
            if k >= 1:
                for (u, v) in ((-4, -2), (4, -2), (0, 0), (-4, 2), (4, 2)):
                    c.put(u - 1, -1 + v * 0.6, "R" if k in (1, 2) else ("E" if k < 4 else "D"))
        for a in (-170, -150, -20, 10, 35, 150, 200):
            ln = [0, 6, 12, 15, 15, 14][k]
            if ln:
                line(o, (w - 1) * math.cos(math.radians(a)), (w * 0.4) * math.sin(math.radians(a)) - 1,
                     (w + ln) * math.cos(math.radians(a)), ((w + ln) * 0.4) * math.sin(math.radians(a)) - 1, "K" if k < 5 else "m")
        if 1 <= k <= 3:
            rnd = random.Random(k)
            for j in range(6):
                c.put(*P(rnd.uniform(-12, 12), rnd.uniform(-9, -2) - k), "S" if j % 2 else "W")
        out.append(merge(_o(c) if c.px else Spr({}), o.spr()))
    return out


V10_FX += ["FxJinxLoadedPips", "FxJinxImprint"]
FX_NAMES += ["FxJinxLoadedPips", "FxJinxImprint"]


def build_v10_fx2(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxJinxLoadedPips"):
        fx_sheet("FxJinxLoadedPips", [("P%d" % n, fx_loaded_pips(n), [0.5, 0.15]) for n in range(1, 7)], outdir)
    if want("FxJinxImprint"): fx_sheet("FxJinxImprint", [("Play", fx_imprint(), [0.04, 0.06, 0.08, 0.1, 0.14, 0.16])], outdir)


EVENTS.update({
    "JinxCardSoldier": {"Thrust": [("pike thrust hit: spade at x 27..33, y -12..-6 (box 22 x 10 at (22, -9))", 3)],
                        "Deal": [("cards flicked: 3 trap cards land round the hero (ModJinxDealTraps)", 3)]},
    "JinxLoadedDie": {"Slam": [("slam hit (box 14 x 12 at (11, -7)); loaded face stamps FxJinxImprint at (14, 0)", 4)],
                      "Roll": [("tumble starts: AnimMove 210 + body hit (16 x 14 at (3, -9))", 1),
                               ("lands: roll 1-6 (FloatNumber) and load it (FxJinxLoadedPips over the head, 28 up)", 7)]},
    "JinxCardKing": {"Smash": [("mace lands at x 24..30: FxJinxClubSlam quake at (26, 0)", 3)],
                     "Court": [("Diamonds card raised: 3 s guard (FxJinxGuard at (13, -8), FxJinxRiposte per blocked hit)", 3)]},
    "JinxHouseOfCards": {"Topple": [("tiers slap down to x 19 (box 16 x 16 at (12, -10))", 3)],
                         "Storm": [("6 FxJinxOrbitCard spawn, orbit 20 x 8 round (0, -14), launch after 2.5 s", 4)]},
    "JinxHighRoller": {"Flick": [("chip leaves the thumb at (17, -20) (FxJinxChip)", 2)],
                       "AllIn": [("the stack is shoved: chip fan from (18, -15); stack shown by FxJinxChips 34 up", 5)]},
    "JinxTwenty": {"Ram": [("facets hit to x 19 (box 16 x 16 at (13, -9))", 3)],
                   "Crit": [("leap: AnimMove 170", 1), ("lands: d20 roll (FloatNumber); 20 = FxJinxCrit burst, 1 = Fumble", 6)]},
    "JinxGorgon": {"Lash": [("snake heads strike x 18..24 (box 18 x 16 at (16, -14))", 3)],
                   "Stare": [("eyes kindle", 2), ("stare: FxJinxGaze beam from (6, -22), 62 px long, roots", 4)]},
    "JinxRattler": {"Spit": [("venom glob leaves the mouth (23, -11); launched on the floor at (22, 0)", 3)],
                    "Rattle": [("dice shake", 2), ("FxJinxRattleRing bursts from the feet (56 x 20, daze)", 4)]},
    "JinxNutcracker": {"Sabre": [("blade sweeps x 1..23, y -25..-3 (FxJinxSabre, OrcSwipe clone at (4, -14))", 3)],
                       "Crack": [("lunge", 3), ("jaws clamp: FxJinxCrunch at the hero (grabbed) or at (20, 0)", 4),
                                 ("second bite if the hero is held", 6)]},
    "JinxOracle": {"Gaze": [("third eye flares, FxJinxEyeOrb from (10, -30)", 3)],
                   "Foresight": [("3 foresight charges (FxJinxForesight 41 up); each foreseen hit = FxJinxBlink", 4)]},
})
FX_NOTES.update({
    "FxJinxTrapCard": "Card Soldier trap card. Land (4: tumbles down onto the floor), Lie (2, looped 9x: waits face down), "
                      "Snap (6: spade blades spring up on frame 1, damage frames 1-2). Origin = the card's floor point (13, 23).",
    "FxJinxImprint": "Loaded Die's loaded slam: the die face stamps the floor (0), cracks + red pips (1-3: damage), fades. Origin (27, 15).",
    "FxJinxLoadedPips": "Loaded Die's stored roll, P1..P6 (2-frame loop): a 7 x 7 die face; origin = its bottom.",
    "FxJinxClubSlam": "Card King's quake: flash (0, damage 0-1), club-shaped dust cloud (1-3), cracks fade (4). Origin = floor (15, 19).",
    "FxJinxGuard": "Card King's Hold Court card (4-frame loop, a glint on 2). Origin (8, 13): card centre 5 px up.",
    "FxJinxRiposte": "Card King's thrown-back card: Fly loop, faces right, flips edge-on on frame 2.",
    "FxJinxOrbitCard": "House of Cards storm card (4-frame flip loop), centre = origin.",
    "FxJinxChip": "High Roller's poker chip, Fly loop, faces right, spins edge-on on frame 2.",
    "FxJinxChips": "High Roller's stack over its head, One..Five (2-frame loop); origin = the stack's bottom.",
    "FxJinxD20Shard": "Natural Twenty's d20 shard, Fly loop (tumbling violet triangle).",
    "FxJinxCrit": "Natural Twenty: Crit (7: a starburst with 20 over it; damage frames 1-2) and Fumble (5: smoke and a grey 1 "
                  "that fade; spawned 20 px up). Origin = feet (19, 35).",
    "FxJinxGaze": "Gorgon's stone stare: kindle (0-1), full 62 px beam (2-3: damage, roots), fade (4-5). Origin = beam start (65, 5); "
                  "drawn 22 px up, collider on the floor.",
    "FxJinxVenom": "Dice Rattler venom glob, Fly loop; skims the floor, drawn 11 px up.",
    "FxJinxVenomPool": "Dice Rattler poison pool: splash (0-1), bubbling pool (2-6: damage every 0.5 s, poison), fade (7). Origin (12, 8).",
    "FxJinxRattleRing": "Dice Rattler's rattle ring: dice burst out (0-2), the ring spreads to 70 x 30 (damage frames 1-2, daze). Origin (36, 19).",
    "FxJinxSabre": "Nutcracker sabre (OrcSwipe clone): steel crescent with a royal-blue edge. Damage frame 0.",
    "FxJinxCrunch": "Nutcracker's bite: teeth close over the victim (0-1, damage 0), shell splinters fly (2-4). Origin = victim's feet (17, 21).",
    "FxJinxEyeOrb": "Oracle's third-eye orb, Fly loop, faces right (violet trail).",
    "FxJinxForesight": "Oracle's foresight charges over her head, One..Three (2-frame loop: the last eye blinks).",
    "FxJinxBlink": "Oracle's blink: her shape scatters into violet motes (5 frames). Origin = feet (12, 31).",
})
L10 = ["JinxCardSoldier (Card Sharp): its green dealer visor and goblin face, a playing card for a body",
       "JinxLoadedDie (Dice Imp): the imp's ivory die as its body, the imp's horns, bat wings, crimson legs and belled tail",
       "JinxCardKing (Card Soldier): the card tabard (King of Clubs), the green visor and goblin face, a crown, the Soldier's black spades become a club mace",
       "JinxHouseOfCards (Card Soldier): the Soldier's card multiplied into a tower; the goblin eye under the green visor peers from the top",
       "JinxHighRoller (Loaded Die): the die is its belly, the imp's horns grown, the bat wings and belled tail",
       "JinxTwenty (Loaded Die): the die cut into a d20 with the same grinning face, horns, bat wings, crimson legs, belled tail",
       "JinxGorgon (Snake-Eyes): the harlequin coil and rattle below, the imp-ivory horns, harlequin snakes for hair",
       "JinxRattler (Snake-Eyes): the dice rattle grown into four dice, the ivory horns, crimson-diamond scales",
       "JinxNutcracker (Marionette): the varnished wooden face, brass ball joints, the gold spring knee and cut string ends",
       "JinxOracle (Fortune Teller): her robe, shawl of coins, green visor, card earring and the crystal ball grown into a seat",
       "v0.10 single-parent fixes: Marionette (Jack only) lost the Card Sharp visor/card for a gold harlequin diamond; Fortune "
       "Teller (Card Sharp only) lost the imp horns/die earring for a card earring; Grand Jester (Ringmaster only) lost the "
       "control cross; Chimera (Ringmaster only) has a ribboned lion tail instead of the serpent; Puppeteer (Marionette only) "
       "lost the teller's plum robe and crystal ball (walnut frock, a spare doll head); Bandit (Fortune Teller only) has a "
       "shawl-wound lever instead of the serpent"]
EVENTS["JinxDiceImp"] = {"Toss": [("die release at the hand (8, -14): FxDie launched on the floor at (8, 0), drawn 13 px up", 3)],
                         "Roll": [("spin starts", 1), ("slam: die shows a face (spawn FxDieFace at the feet)", 6)]}
L10.append("v0.10: JinxDiceImp redrawn at final size (build_dice_imp10, no ArtScale entry): a crimson imp on a 6 px pipped "
           "ivory die, ivory horns, yellow eyes, bat wings, a belled tail; attack node 9 px up")


# ------------------------------------------------------------------ v0.10: DICE IMP at final size
# The v0.7 pass shrank a 30 px design to 0.55 and the imp turned to noise. Redrawn pixel by pixel at its final size:
# a crimson imp perched on a 5 px ivory die, ivory horns, yellow eyes and an ivory-toothed grin, bat wings, a tail
# with a gold bell. Its children keep these: Snake-Eyes the ivory horns and the dice, the Loaded Die the cube, the
# horns, the bat wings, the crimson legs and the belled tail.
IMP10_HEAD = {
    "grin": Part("""
W...W
.DEf.
DYEYf
dKXKE
.dKd.
""", (2, 4)),
    "glee": Part("""
W...W
.DEf.
DKEKf
KXKXK
.KEK.
""", (2, 4)),
    "dead": Part("""
W...W
.DEf.
DpEpf
dEKKE
.dDd.
""", (2, 4)),
}
IMP10_WING = {   # bat wings drawn round the shoulder ('*'); E = lit finger bones, D membrane, d shadow
    "up": """
E..E..
DE.DE.
dDDdDD*
""",
    "mid": """
EE.....
dDDE...
.ddDDD*
""",
    "down": """
..ddD*
.dDDE.
dDE.E.
E.....
""",
    "fold": """
.dD
dDD*
""",
}
NEAR_W = {"E": "S", "D": "d", "d": "p", "*": "s"}
FAR_W = {"E": "s", "D": "p", "d": "K", "*": "K"}


def imp10_wing(c, x, y, pose, near=True):
    rows = [r for r in IMP10_WING[pose].strip("\n").split("\n")]
    py = [i for i, r in enumerate(rows) if "*" in r][0]
    px = rows[py].index("*")
    cmap = NEAR_W if near else FAR_W
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == ".": continue
            c.put(x + i - px + (0 if near else 1), y + j - py - (0 if near else 1), cmap[ch], over=near)


def flap_pose(flap):
    if flap is None: return "fold"
    return "up" if flap < -35 else ("mid" if flap <= 10 else "down")


def imp10(alt=2, dx=0, flap=-40, tilt=0, die_rot=(0, 35, 0), die_pos=None, head="grin", hand=(3, -11), hand2=None,
          small_die=None, sit=True, tail=0, extra=None, extra_back=None, over=None, imp_dy=0, die_on=True):
    """Imp on its die. alt: px between the floor and the die's bottom. hand / hand2 / small_die / die_pos are
    absolute (feet-relative) pixel points; tilt shifts the head 1 px per 10 deg."""
    c = Canvas()
    if extra_back: extra_back(c)
    dcx, dcy = dx, -alt - 3.5
    sx, sy = dx - 1, dcy - 4 + imp_dy          # seat on the die's top face
    pose = flap_pose(flap)
    hx = int(round(tilt / 10.0))
    # far wing behind everything
    imp10_wing(c, sx + 1, sy - 3, pose, near=False)
    # tail with the gold bell, curling down behind the die
    tl = [(sx - 2, sy), (sx - 3, sy + 1), (sx - 4, sy + 2 + (tail % 2)), (sx - 4, sy + 3 + (tail % 2))]
    for p in tl[:-1]: c.put(*p, "D")
    c.put(tl[-1][0], tl[-1][1], "z"); c.put(tl[-1][0] - 1, tl[-1][1], "e"); c.put(tl[-1][0], tl[-1][1] + 1, "A")
    if die_on and die_pos is None:
        die(c, dcx, dcy, 6, *die_rot)
    # body: pot belly hugging the die top
    ell(c, sx + 0.5, sy - 1.5, 2.0, 1.8, CRIM, bias=0.2)
    c.put(sx + 1, sy - 2, "f")
    # legs dangling over the die's front (or tucked when it lets go)
    if sit:
        c.put(sx + 1, sy + 1, "D"); c.put(sx + 2, sy + 2, "K")
        c.put(sx, sy + 1, "d"); c.put(sx + 1, sy + 2, "K")
    else:
        c.put(sx, sy + 1, "d"); c.put(sx + 1, sy + 1, "D"); c.put(sx, sy + 2, "K"); c.put(sx + 1, sy + 2, "K")
    if die_on and die_pos is not None:
        die(c, die_pos[0] + dx, die_pos[1], 6, *die_rot)
    # near wing from the back of the shoulder, under the head
    imp10_wing(c, sx, sy - 2, pose, near=True)
    # head (neck on the body top)
    c.part(IMP10_HEAD[head], sx + 1 + hx, sy - 2)
    # arms: thin crimson lines to the hands
    for k, hd in enumerate((hand2 or (sx - 2 - dx, sy - 1), hand)):
        s0 = (sx - 1 if k == 0 else sx + 2, sy - 2)
        tx, ty = hd[0] + dx, hd[1]
        line(c, s0[0], s0[1], tx, ty, "D" if k == 0 else "E")
        c.put(int(round(tx)), int(round(ty)), "E" if k == 0 else "f")
    if small_die is not None:
        x, y = small_die
        for (ox, oy, ch) in ((0, 0, "X"), (1, 0, "W"), (0, 1, "W"), (1, 1, "w")):
            c.put(x + dx + ox, y + oy, ch)
        c.put(x + dx, y, "K")
    if extra: extra(c)
    return finish(c, over)


def build_dice_imp10(outdir):
    I = imp10
    idle = [I(flap=-60, alt=0, hand=(3, -9)), I(flap=-10, alt=0.5, hand=(3, -9), tail=1),
            I(flap=30, alt=0, hand=(3, -8), head="glee"), I(flap=-10, alt=0.5, hand=(3, -9), tail=1)]
    run = [I(flap=[-70, -20, 20, 40, -10, -50][i], alt=[2, 2, 1, 1, 2, 3][i], tilt=10, die_rot=(0, 45, 8 + 6 * i),
             hand=(4, -10), tail=i) for i in range(6)]
    # Toss: fish out a little die (0), cock the arm back (1-2), LOB (3: release at (6, -15)), follow through
    toss = [I(flap=-20, hand=(1, -9), small_die=(1, -10), head="glee"),
            I(flap=10, hand=(-1, -14), small_die=(-1, -15)),
            I(flap=-50, hand=(3, -15), small_die=(3, -16), head="glee"),
            I(flap=-30, hand=(6, -13), head="glee", tilt=10,
              extra=lambda c: [c.put(8, -15, "X"), c.put(9, -15, "W"), c.put(8, -14, "W"), c.put(9, -14, "w"),
                               c.put(8, -15, "K"), c.put(7, -14, "w")]),
            I(flap=30, hand=(5, -10), tilt=10), I(flap=-10, hand=(3, -10))]
    # Roll: heave the big die up (0), spin it overhead (1-5), SLAM it down face-out (6), recover (7)
    roll = [I(flap=-30, alt=3, hand=(3, -8), hand2=(-3, -8), head="glee")]
    for k in range(1, 6):
        roll.append(I(flap=[-60, 40, -60, 40, -60][k - 1], alt=0, imp_dy=2, die_rot=(40 * k, 35 + 12 * k, 0),
                      die_pos=(1, -17 - [0, 1, 2, 1, 0][k - 1]), hand=(3, -15), hand2=(-2, -15), head="glee", sit=False))

    def dust(c):
        for x, y, ch in ((-5, 0, "S"), (-6, -1, "s"), (7, 0, "S"), (8, -1, "s"), (6, -1, "S")):
            c.put(x, y, ch)
    roll.append(I(flap=50, alt=0, die_rot=(0, 90, 0), die_pos=(3, -3), hand=(5, -6), hand2=(0, -6), sit=False,
                  head="glee", imp_dy=-2, extra=dust))
    roll.append(I(flap=-30, alt=2, die_rot=(0, 90, 0), die_pos=(3, -4), hand=(4, -8), sit=False))
    d0 = I(flap=60, alt=3, head="dead", hand=(3, -14), hand2=(-4, -13), tilt=-10)
    d1 = I(flap=None, alt=1, head="dead", die_rot=(35, 60, 30), hand=(-2, -10))
    d2 = grounded(rot_spr(I(flap=None, alt=0, head="dead", die_rot=(70, 80, 50), hand=(-3, -8)), -75, (0, -1)))
    corpse = imp10_corpse()
    knock = I(flap=70, alt=3, head="grin", hand=(2, -13), hand2=(-5, -13), die_rot=(-10, 20, -12), tilt=-10)
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.07] * 6),
             ("Toss", toss, [0.14, 0.12, 0.05, 0.08, 0.1, 0.14]),
             ("Roll", roll, [0.14, 0.07, 0.07, 0.07, 0.07, 0.07, 0.06, 0.25])]
    anims += std_tail(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("JinxDiceImp", anims, outdir, scale=8)


def imp10_corpse():
    c = Canvas()
    die(c, 3, -3.5, 6, 0, 20, 0)
    c.part(IMP10_HEAD["dead"], -5, -1)
    ell(c, -2, -1.5, 2.0, 1.2, IMP)
    imp10_wing(c, -1, -2, "fold")
    c.put(-8, -1, "z"); c.put(-7, -1, "D")
    return grounded(finish(c))


V10_JOBS = [("JinxCardSoldier", build_card_soldier), ("JinxLoadedDie", build_loaded_die), ("JinxCardKing", build_card_king), ("JinxHouseOfCards", build_house_of_cards), ("JinxHighRoller", build_high_roller), ("JinxTwenty", build_twenty), ("JinxGorgon", build_gorgon), ("JinxRattler", build_rattler), ("JinxNutcracker", build_nutcracker), ("JinxOracle", build_oracle)]


# <<< v0.10 tree


# ================================================================== main
def contact_sheet(outdir, names):
    from PIL import Image, ImageDraw
    cells = []
    for n in names:
        if n not in BUILT: continue
        b = BUILT[n]; img, man = b["img"], b["man"]
        cw, chh = man["cellW"], man["cellH"]
        fi = man["anims"][0]["frames"][0]
        x0, y0 = (fi % man["cols"]) * cw, (fi // man["cols"]) * chh
        cells.append((n, img.crop((x0, y0, x0 + cw, y0 + chh))))
    if not cells: return
    S = 6
    H = max(c.size[1] for _, c in cells)
    W = sum(c.size[0] for _, c in cells) + 4 * len(cells)
    bg = Image.new("RGBA", (W * S, (H + 4) * S), (28, 26, 32, 255))
    x = 0
    for n, c in cells:
        bg.alpha_composite(c.resize((c.size[0] * S, c.size[1] * S), Image.NEAREST), (x * S, (H - c.size[1]) * S))
        x += c.size[0] + 4
    d = ImageDraw.Draw(bg)
    d.line([(0, (H - 2) * S + S // 2), (W * S, (H - 2) * S + S // 2)], fill=(60, 56, 64, 255))
    bg.convert("RGB").save(os.path.join(outdir, "contact_idle.png"))
    print("contact sheet", os.path.join(outdir, "contact_idle.png"))


MONSTERS = ["JinxJackBox", "JinxJackMinion", "JinxCardSharp", "JinxDiceImp", "JinxRingmaster", "JinxMarionette", "JinxGrandJester",
            "JinxFortuneTeller", "JinxSnakeEyes", "JinxChimera", "JinxPuppeteer", "JinxBandit"] + [n for n, _ in V10_JOBS]


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    outdir = args[0] if args else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    if only is None or only & set(ICON_NAMES):
        build_icons(outdir)


if __name__ == "__main__":
    main()
