"""YSVELD, THE FROST WIDOW: "Winter weaves, and nothing leaves".
Every sprite sheet for the Ysveld god pack: 7 monsters (+ the Broodling minion), FX sheets, two item icons
(+ shop bubbles / HUD icons) and the god portrait.

    python3 ysveld_rigs.py [outdir] [--only Name,Name]

Method (same family as belmora_rigs.py): every monster is a pose function that draws shaded primitives
(ellipses, tapered tubes, polygons lit from the top-left) onto a fresh canvas, so each frame is a real re-posed
drawing. A finished pose gets a 1px midnight outline, then glow pixels (eyes, hourglasses, rime) are laid on top.
Palette: black widow silk with a violet sheen, pale ice blue, frost white, deep midnight-blue shadows.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, PALETTE, pack, preview  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_ysveld")

# ------------------------------------------------------------------ palette (this process only)
PALETTE.update({
    '0': (0x0b, 0x0c, 0x1a),   # midnight-black outline
    '1': (0x13, 0x17, 0x33),   # midnight shadow ramp
    '2': (0x1d, 0x27, 0x50),
    '3': (0x2a, 0x3c, 0x70),
    '4': (0x3b, 0x60, 0x98),   # ice ramp
    '5': (0x58, 0x8c, 0xc2),
    '6': (0x8a, 0xbe, 0xe4),
    '7': (0xc2, 0xe4, 0xf7),
    '8': (0xf0, 0xf9, 0xff),   # frost white
    'A': (0x0f, 0x0b, 0x16),   # widow silk: black -> violet sheen
    'B': (0x1b, 0x15, 0x27),
    'C': (0x2b, 0x21, 0x3d),
    'D': (0x45, 0x33, 0x63),
    'E': (0x6c, 0x55, 0x96),
    'F': (0x9a, 0x84, 0xc4),
    'f': (0x7c, 0x8a, 0xa8),   # frost-pale skin
    'g': (0xb4, 0xc2, 0xd6),
    'h': (0xe2, 0xea, 0xf4),
    'G': (0x8e, 0xf2, 0xff),   # ice glow
    'H': (0xff, 0xff, 0xff),   # glow core
    'I': (0x4c, 0xc8, 0xff),   # deep glow
    # v0.8: the Rime Colossus is glacier ice (teal), so the knight line Shardling -> Rime Knight -> Colossus reads as
    # violet crystal -> silver plate and navy -> teal glacier
    '!': (0x0e, 0x1e, 0x2e), '@': (0x16, 0x36, 0x52), '#': (0x22, 0x58, 0x7a), '$': (0x3a, 0x88, 0xaa),
    '%': (0x6a, 0xb8, 0xd4), '^': (0xa8, 0xe0, 0xee),   # v0.9: glacier cyan, closer to the family's ice
    # v0.10: the Rime Knight's gunmetal steel (desaturated, so it never reads as the Veil Witch's cyan ice)
    '&': (0x22, 0x28, 0x36), '*': (0x3a, 0x44, 0x5a), '+': (0x5c, 0x6a, 0x84), '=': (0x8a, 0x98, 0xb2), '~': (0xc4, 0xcc, 0xdc),
})
GLACIER = {"1": "!", "2": "@", "3": "#", "4": "$", "5": "%", "6": "^", "7": "^"}
KNIGHT = {"2": "&", "3": "*", "4": "+", "5": "=", "6": "~", "7": "~", "8": "~"}   # v0.10: gunmetal plate, violet silk kept
SILK_LIFT = {"A": "B", "B": "C", "C": "D", "D": "E", "E": "F"}
BROOD_LIFT = {"A": "C", "B": "D", "C": "D", "D": "E", "E": "F", "1": "2", "2": "3"}   # v0.10: the tiny Broodling two steps up
GLOW = set("GHI")
SILK = "ABCD"
SILK_L = "BCDE"
SILK_S = "BCDEF"       # glossy: reaches the violet sheen
ICE = "4567"
ICE_L = "5678"
ICE_D = "2345"
MID = "0123"
SKIN = "fgh"
LACE = "5678"


# ------------------------------------------------------------------ primitives (copied from belmora_rigs.py)
def pick(ramp, l):
    n = len(ramp)
    i = int((l + 1.0) * 0.5 * n)
    return ramp[max(0, min(n - 1, i))]


def P(x, y):
    return int(round(x)), int(round(y))


def ell(c, cx, cy, rx, ry, ramp, ang=0.0, bias=0.0, vmax=None, vmin=None, over=True, shader=None):
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


def rot_about(p, piv, deg):
    a = math.radians(deg)
    x, y = p[0] - piv[0], p[1] - piv[1]
    return (piv[0] + x * math.cos(a) - y * math.sin(a), piv[1] + x * math.sin(a) + y * math.cos(a))


def catmull(pts, rad, step=1.0):
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


def speckle(c, region, n, seed, chars="78", only_on=None):
    """Rime frost grains on existing pixels inside region (x0,y0,x1,y1)."""
    r = random.Random(seed)
    x0, y0, x1, y1 = region
    tries = 0
    while n > 0 and tries < n * 30:
        tries += 1
        x, y = r.randint(int(x0), int(x1)), r.randint(int(y0), int(y1))
        v = c.px.get((x, y))
        if v is None or v in GLOW or (only_on and v not in only_on): continue
        c.put(x, y, chars[r.randrange(len(chars))]); n -= 1


# ------------------------------------------------------------------ frame: body canvas + glow canvas
class Fr:
    def __init__(self):
        self.b = Canvas()   # outlined body
        self.g = Canvas()   # glow pixels over the outline
        self.u = Canvas()   # under-layer: behind the body, outlined with it
        self.n = Canvas()   # far layer: behind everything, no outline
        self.l = Canvas()   # limbs over the body: outlined only where they stand against empty space

    def done(self, clip=True, outline="0"):
        base = dict(self.u.px); base.update(self.b.px)
        spr = outl(Spr(base), outline) if outline else Spr(base)
        px = dict(self.n.px); px.update(spr.px)
        if self.l.px:
            px.update(self.l.px)
            if outline:
                for (x, y) in self.l.px:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        k = (x + dx, y + dy)
                        if k not in px: px[k] = outline
        px.update(self.g.px)
        if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
        return Spr(px)


def outl(spr, ch="0"):
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
    return recol(spr, {"G": "5", "H": "6", "I": "4"})


# ------------------------------------------------------------------ sheet helpers
BUILT = {}


def lifted(anims, remap):
    """v0.8: recolour every frame with remap; the Statue is re-cut from the recoloured Idle frame 0."""
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
    idle = anims[0][1][0]
    b = idle.bbox()
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man,
                   "idle_wh": (b[2] - b[0] + 1, -b[1] + 1)}
    print("built %-16s cell %dx%d  idle %dx%d  %s" % (name, cw, ch, b[2] - b[0] + 1, -b[1] + 1,
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


def frost_tip(c, x, y, ch="7"):
    c.put(*P(x, y), ch)


# ================================================================== SPIDERS (Rimeling, Broodling, Silk Weaver)
def hourglass(g, x, y, s=1, bright=True):
    """Glowing ice hourglass mark (the widow's sign) centred at (x, y)."""
    x, y = P(x, y)
    hi, lo = ("G", "I") if bright else ("6", "4")
    if s <= 1:
        pts = ((0, -1, lo), (1, -1, lo), (0, 0, "H" if bright else hi), (0, 1, lo), (1, 1, lo))
    else:
        pts = ((-1, -2, lo), (0, -2, hi), (1, -2, hi), (2, -2, lo), (0, -1, hi), (1, -1, "H" if bright else "7"),
               (0, 0, hi), (1, 0, "H" if bright else "7"), (-1, 1, lo), (0, 1, hi), (1, 1, hi), (2, 1, lo))
    for (a, b, ch) in pts:
        g.put(x + a, y + b, ch)


def spider_leg(c, root, foot, l1, l2, cols, width=1, tip="7", knee_hi=None, bend=None, band=None):
    """Two-segment arched leg from root to foot (knee always above the line)."""
    if bend is None: bend = 1 if foot[0] >= root[0] else -1
    (kx, ky), _ = ik(root[0], root[1], foot[0], foot[1], l1, l2, bend=bend)
    if width <= 1:
        line(c, root[0], root[1], kx, ky, cols[0])
        line(c, kx, ky, foot[0], foot[1], cols[1])
    else:
        ramp = cols[2] if len(cols) > 2 else "BCD"
        tube(c, [root, (kx, ky)], [width * 0.55, width * 0.45], ramp, bias=0.25)
        tube(c, [(kx, ky), foot], [width * 0.45, 0.3], ramp, bias=0.1)
    if knee_hi: c.put(*P(kx, ky), knee_hi)
    if band:   # frost band just below the knee
        c.put(*P(kx + (foot[0] - kx) * 0.3, ky + (foot[1] - ky) * 0.3), band)
    if tip: c.put(*P(*foot), tip)
    return (kx, ky)


def spider(S=1.0, dx=0.0, dy=0.0, tilt=0.0, abd_lift=0.0, legs=0.0, amp=0.0, rear=0.0, fang=0.0, eye="open",
           crouch=0.0, breathe=0.0, spin=None, extra=None, splay=0.0, frost=True, weaver=False, lift=0.0, reach=0.0,
           matron=False, style="widow"):
    """Black widow, side view facing right. S scales the whole rig (Broodling 0.62, Rimeling 1, Weaver 1.5).
    rear: front legs raised (0..1); abd_lift: abdomen swung up over the back (0..1, Weaver tether).
    style (v0.8 art pass, so the line Rimeling -> Weaver -> Matron stops reading as one dark spider in three sizes):
      "widow"  black silk with a violet sheen (Broodling)
      "rime"   Rimeling: a pale ice-blue spiderling crusted in frost, two rime crystals on its back
      "stilt"  Silk Weaver: black silk raised high on long stilt legs, abdomen wound in white silk bands, no crystals
      "brood"  Widow Matron: low and massive, ice-plated legs, a crown of icicles over the front of the abdomen and a
               clutch of pearl egg sacs riding on its back"""
    f = Fr()
    w = 2 if S >= 1.4 else 1
    stilt = 2.2 * S if style == "stilt" else 0.0
    if style == "rime":
        ABD, CEP, NEAR, NEAR_K, KNEE, GL = "234566", "23456", ("5", "5", "4567"), ("4", "4", "3456"), "7", ("8", "7")
    elif style == "stilt":
        ABD, CEP, NEAR, NEAR_K, KNEE, GL = "DEEFFg", "DEF", ("E", "E", "DEF"), ("D", "D", "CDE"), "h", ("h", "g")
    else:
        ABD, CEP, NEAR, NEAR_K, KNEE, GL = "ABCCDD", "ABCDE", ("D", "D", "CDEF"), ("C", "C", "BCDE"), "F", ("F", "E")
    if style == "brood":   # v0.10: the Weaver's violet silk, banded with her black thread, legs of violet silk
        ABD, CEP, NEAR, NEAR_K, KNEE = "BCCDDE", "BCDE", ("E", "E", "DEF"), ("D", "D", "CDE"), "7"
    if style == "lurker":  # v0.10 Rime Lurker: navy body under a pale trapdoor lid of frost plates, thick ice legs
        ABD, CEP, NEAR, NEAR_K, KNEE, GL = "122334", "12234", ("5", "5", "3456"), ("4", "4", "2345"), "8", ("5", "4")
        w = 2
    T = (dx + 2.8 * S, -(4.5 * S) + dy + crouch * 1.3 * S - lift - stilt)
    trx, try_ = 2.1 * S, 1.7 * S
    ped = (T[0] - 2.0 * S, T[1] - 0.3 * S)
    abd_ang = (4.0 if style == "lurker" else 12.0) + abd_lift * 82.0 + tilt * 0.4 + (24.0 * (1.0 - max(0.0, min(1.0, abd_lift))) if style == "stilt" else 0.0)  # carried high
    arx, ary = (3.8 + breathe * 0.2) * S, (3.1 - breathe * 0.15) * S
    if weaver: arx, ary = arx * 1.06, ary * 1.1
    if style == "stilt": arx, ary = arx * 1.14, ary * 1.12
    if matron: arx, ary, trx, try_ = arx * 1.18, ary * 1.18, trx * 1.15, try_ * 1.15
    if style == "lurker": arx, ary, trx, try_ = arx * 1.12, ary * 0.82, trx * 1.1, try_ * 1.0
    ca, sa = math.cos(math.radians(abd_ang)), math.sin(math.radians(abd_ang))
    A = (ped[0] - (arx - 0.7) * ca, ped[1] - (arx - 0.7) * sa - 0.8 * S)
    # ---- legs: 4 per side, index 0 = hind ... 3 = front. Far side first (shadow, no outline).
    foot_x = [-7.0, -3.9, 4.6, 7.6]
    leg_specs = []
    for side in (1, 0):
        for i in range(4):
            ph = legs + i * math.pi / 2 + side * math.pi
            root = (T[0] - 1.4 * S + i * 0.8 * S - (0.5 * S if side else 0), T[1] - 0.9 * S)
            fx = dx + (foot_x[i] + (1.2 if side else 0)) * S + amp * 1.5 * S * math.sin(ph) + splay * (i - 1.5) * S
            fy = -(max(0.0, amp * 1.3 * math.cos(ph)) * S) - (0.9 * S if side else 0) - lift
            l1, l2 = (6.2 * S, 5.8 * S) if i >= 2 else (7.0 * S, 6.8 * S)
            if stilt: l1, l2 = l1 + stilt * 0.8, l2 + stilt * 0.6
            if i >= 2 and reach > 0:
                fx += reach * (1.0 if i == 3 else 0.6) * S
            if i == 3 and rear > 0:
                fx = T[0] + (4.6 + 1.2 * rear) * S + (0.8 if side else 0); fy = T[1] - (0.5 + 5.0 * rear) * S
            if i == 2 and rear > 0.5:
                fx = T[0] + 4.6 * S; fy = min(fy, -(rear - 0.5) * 3.0 * S)
            leg_specs.append((side, i, root, (fx, fy), l1, l2))
    for side, i, root, foot, l1, l2 in leg_specs:
        if side:
            spider_leg(f.n, root, foot, l1, l2, ("C", "B", "BCD") if style == "stilt" else ("2", "1", "123"), width=w, tip="3")
    # ---- spinnerets + silk (weaver)
    if spin is not None:
        sx, sy = A[0] - (arx - 0.3) * ca, A[1] - (arx - 0.3) * sa
        f.b.put(*P(sx, sy), "D")
        spin(f, (sx, sy))
    # ---- abdomen: glossy black with a violet sheen, rime on the crown
    def gloss(nu, nv, d, l, ch, x, y):
        if style in ("stilt", "brood") and abs(((nu * 1.8 + 2.0) % 1.0) - 0.5) < 0.14 and d < 0.95:     # black thread bands
            return "A" if l < 0.2 else "B"
        if l > 0.6 and d < 0.45: return GL[0] if l > 0.86 else GL[1]
        if weaver and style != "stilt" and 0.25 < d < 0.8 and ((x * 3 + y * 5) % 9 == 0) and nv < 0.3: return "3"
        return ch
    ell(f.b, A[0], A[1], arx, ary, ABD, ang=abd_ang, bias=0.0 if style != "rime" else 0.15, shader=gloss)
    ell(f.b, T[0], T[1], trx, try_, CEP, ang=tilt, bias=0.05)
    # near legs over the body
    for side, i, root, foot, l1, l2 in leg_specs:
        if not side:
            spider_leg(f.l if i >= 2 else f.u, root, foot, l1, l2, NEAR if i >= 2 else NEAR_K, width=w,
                       tip="7" if frost else "D",
                       knee_hi=KNEE, band=("6" if frost and S >= 1.4 else None))
    # pedipalps + chelicerae with frost fangs
    hx, hy = T[0] + trx * 0.85, T[1] + try_ * 0.5
    op = fang
    f.b.put(*P(hx, hy), "C"); f.b.put(*P(hx + 0.6 * S, hy + 0.6 * S), "B")
    f.b.put(*P(hx + 0.8 * S + op, hy + 1.0 * S - op * 0.8), "8")
    if S >= 1.0: f.b.put(*P(hx + 0.2 * S + op * 0.4, hy + 1.2 * S + op * 0.6), "7")
    if S >= 1.4:
        line(f.b, hx + 0.5, hy - 1.2, hx + 2.6 - op, hy - 1.6 - op, "D")
        f.b.put(*P(hx + 1.2 * S + op, hy + 1.6 * S - op), "8")
    # rime crust on the abdomen crown
    if frost:
        for k in range(int(6 * S)):
            t = -150 + k * (110.0 / max(1, int(6 * S) - 1))
            a_ = math.radians(t)
            lx, ly = arx * 0.92 * math.cos(a_), ary * 0.92 * math.sin(a_)
            f.b.put(*P(A[0] + lx * ca - ly * sa, A[1] + lx * sa + ly * ca),
                    ("8" if k % 2 else "7") if style == "rime" else ("7" if k % 2 else "6"))
        if style == "lurker":   # the trapdoor lid: overlapping frost plates over the back half of the abdomen
            for k in range(6):
                t_ = -172 + k * 24
                a_ = math.radians(t_)
                lx, ly = arx * 0.78 * math.cos(a_), ary * 0.78 * math.sin(a_)
                bx_, by_ = A[0] + lx * ca - ly * sa, A[1] + lx * sa + ly * ca
                ell(f.b, bx_, by_ - 0.3 * S, 1.9 * S, 1.4 * S, "56788", ang=t_ + 90 + abd_ang, bias=0.3)
                f.b.put(*P(bx_ + 0.8 * S, by_ + 0.4 * S), "3")
            hinge_ = (A[0] - arx * 0.2, A[1] - ary * 0.9)
            crystal(f.b, hinge_[0], hinge_[1], -100 + abd_ang, 2.6 * S, 0.8, lit=0.25)
        if style in ("rime", "stilt"):   # rime crystals growing out of its back (the Weaver keeps the Rimeling's, grown)
            for (t_, ln) in (((-112, 2.6 * S), (-82, 3.4 * S)) if style == "rime" else ((-128, 2.4 * S), (-100, 3.4 * S), (-72, 2.6 * S))):
                a_ = math.radians(t_)
                lx, ly = arx * 0.75 * math.cos(a_), ary * 0.75 * math.sin(a_)
                crystal(f.b, A[0] + lx * ca - ly * sa, A[1] + lx * sa + ly * ca, t_ + abd_ang, ln, 0.8, lit=0.25)
        if weaver and style != "stilt":
            spikes = ((-120, 3.2), (-95, 4.2), (-70, 3.0)) if not matron else \
                ((-92, 4.6), (-74, 6.0), (-56, 5.0), (-38, 3.2))
            for k, (t_, ln) in enumerate(spikes):
                a_ = math.radians(t_)
                lx, ly = arx * 0.8 * math.cos(a_), ary * 0.8 * math.sin(a_)
                bx_, by_ = A[0] + lx * ca - ly * sa, A[1] + lx * sa + ly * ca
                crystal(f.b, bx_, by_, t_ + abd_ang, ln, 0.9, lit=0.1)
        for k in range(int(2 * S)):   # tiny icicles under the abdomen
            lx, ly = -arx * 0.3 + k * 2.0, ary * 0.98
            x0, y0 = A[0] + lx * ca - ly * sa, A[1] + lx * sa + ly * ca
            f.b.put(*P(x0, y0 + 1), "6")
    # glow: eyes + hourglass (on the belly, half hidden)
    ex, ey = T[0] + trx * 0.5, T[1] - try_ * 0.45
    if eye == "open":
        f.g.put(*P(ex, ey), "G"); f.g.put(*P(ex + 1, ey + 0.4), "I")
        if S >= 1.4: f.g.put(*P(ex - 1, ey - 0.3), "I"); f.g.put(*P(ex + 0.4, ey - 1), "H")
    elif eye == "wide":
        f.g.put(*P(ex, ey), "H"); f.g.put(*P(ex + 1, ey + 0.4), "G"); f.g.put(*P(ex, ey - 1), "G")
        if S >= 1.4: f.g.put(*P(ex - 1, ey - 0.3), "G")
    elif eye == "squint":
        f.g.put(*P(ex, ey), "I")
    else:
        f.g.put(*P(ex, ey), "2")
    lx, ly = arx * 0.1, ary * 0.62
    hg = (A[0] + lx * ca - ly * sa, A[1] + lx * sa + ly * ca)
    if eye != "dead" and S >= 0.9:
        hourglass(f.g, hg[0], hg[1], s=2 if S >= 1.4 else 1, bright=eye != "squint")
    if extra: extra(f, T, A)
    return f.done()


def spider_corpse(S=1.0, weaver=False):
    """On its back, legs curled up into the air, frost creeping over it."""
    f = Fr()
    ell(f.b, -1.5 * S, -2.6 * S, 4.6 * S, 2.6 * S, "ABCCD", bias=0.0)
    ell(f.b, 3.4 * S, -1.8 * S, 2.4 * S, 1.6 * S, "ABCD", bias=0.0)
    for i in range(4):
        bx = -1.0 * S + i * 1.6 * S
        sd = 1 if i % 2 else -1
        pts = [(bx, -3.5 * S), (bx + sd * 1.2 * S, -6.0 * S), (bx + sd * 0.2 * S, -7.4 * S), (bx - sd * 0.8 * S, -6.8 * S)]
        polyline(f.u, pts, "C")
        f.u.put(*P(*pts[2]), "7")
    hourglass(f.g, -1.5 * S, -4.2 * S, s=2 if S >= 1.4 else 1, bright=False)
    for k in range(int(4 * S)):
        f.b.put(*P(-4.5 * S + k * 2.1, -1.0 * S - (k % 2)), "7" if k % 2 else "6")
    f.g.put(*P(5.0 * S, -2.3 * S), "2")
    return f.done()


def build_rimeling(outdir, name="YsvRimeling", S=1.0):
    st = "rime" if name == "YsvRimeling" else "widow"     # v0.8: the Rimeling is a pale frost spiderling
    def R(**k): return spider(S=S, style=st, **k)
    idle = [R(legs=0.0, amp=0.25, breathe=0),
            R(legs=0.6, amp=0.25, breathe=1, dy=0.3, crouch=0.2),
            R(legs=1.2, amp=0.25, breathe=1, dy=0.3, crouch=0.2, eye="squint"),
            R(legs=1.8, amp=0.25, breathe=0)]
    run = [R(legs=i * math.pi / 3, amp=1.0, dy=-0.5 * abs(math.sin(i * math.pi / 3)), tilt=3 * math.sin(i * math.pi / 3),
             breathe=i % 2) for i in range(6)]
    def bite_fx(n):
        def fn(f, T, A):
            hx, hy = T[0] + 2.7 * S + 2, T[1] + 1.5 * S
            for k, (a, b) in enumerate(((1, -2), (2, 0), (1, 2), (3, -1), (3, 1))[:n]):
                f.g.put(*P(hx + a, hy + b), "8" if k % 2 == 0 else "6")
        return fn
    bite = [R(dx=-0.8, crouch=0.6, rear=0.3, fang=0.3, legs=0.3, amp=0.3, eye="wide"),
            R(dx=-1.6, crouch=1.0, rear=0.6, fang=1.0, legs=0.5, amp=0.3, eye="wide", tilt=-6),
            R(dx=2.0, crouch=0.2, rear=0.2, fang=1.0, legs=1.6, amp=0.8, tilt=8, splay=0.4, eye="wide", lift=0.6),
            R(dx=3.4, crouch=0.6, fang=0.0, legs=2.0, amp=0.6, tilt=12, splay=0.5, eye="squint", extra=bite_fx(5)),
            R(dx=3.0, crouch=0.5, fang=0.0, legs=2.2, amp=0.4, tilt=8, splay=0.4, eye="squint", extra=bite_fx(2)),
            R(dx=1.4, crouch=0.2, fang=0.2, legs=2.6, amp=0.4, tilt=2),
            R(dx=0.3, legs=3.0, amp=0.2)]
    def glob_at(n):
        def fn(f, T, A):
            mx, my = T[0] + 2.9 * S, T[1] + 0.4 * S
            for k in range(n):
                f.g.put(*P(mx + 1 + k, my - 0.5 * k), "8" if k == n - 1 else "7")
            if n >= 2: f.g.put(*P(mx + n, my - 0.5 * n - 1), "6")
        return fn
    spit = [R(rear=0.4, crouch=0.3, breathe=1, tilt=-4, fang=0.3, eye="open"),
            R(rear=0.9, crouch=0.6, breathe=1, tilt=-12, fang=0.8, eye="wide", dx=-0.6),
            R(rear=1.0, crouch=0.7, breathe=0, tilt=-16, fang=1.0, eye="wide", dx=-0.8, extra=glob_at(1)),
            R(rear=0.7, crouch=0.2, breathe=0, tilt=-6, fang=1.0, eye="wide", dx=0.6, extra=glob_at(3)),
            R(rear=0.5, crouch=0.4, tilt=-2, fang=0.4, eye="squint", dx=0.2),
            R(rear=0.2, crouch=0.2, fang=0.1, legs=0.5, amp=0.2),
            R(legs=0.2, amp=0.2)]
    death = [R(dx=-0.6, rear=0.8, splay=0.8, fang=1, eye="wide", tilt=-14, lift=1.0),
             grounded(R(dx=-1, rear=1.0, splay=1.2, fang=1, eye="dead", tilt=-40, crouch=0.8)),
             grounded(recol(R(dx=-1, rear=1.0, splay=1.5, fang=0.5, eye="dead", tilt=-70, crouch=1.0), {"7": "6"})),
             spider_corpse(S)]
    knock = R(dx=-0.8, rear=0.5, splay=0.7, fang=0.6, eye="squint", tilt=-12, lift=0.5)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.07] * 6)]
    if name == "YsvRimeling":
        anims += [("Bite", bite, [0.14, 0.12, 0.06, 0.06, 0.1, 0.1, 0.12]),
                  ("Spit", spit, [0.14, 0.14, 0.12, 0.06, 0.12, 0.12, 0.12])]
    else:   # Broodling: bite only, plus the Spawn the tiny-rat base plays (3 frames, 0.28 s like vanilla)
        anims += [("Bite", bite, [0.12, 0.1, 0.05, 0.05, 0.08, 0.08, 0.1])]
        def shell(n):
            def fn(f, T, A):
                # torn pearl egg-silk falling away round it
                pts = ((-8, 0), (6, 0), (-7, -2), (7, -3), (-9, -1), (8, -1), (-1, -6))[:n]
                for j, (a, b) in enumerate(pts):
                    f.g.put(*P(T[0] - 1 + a, b), "h" if j % 2 == 0 else "g")
                    if j < 2 and n > 4: f.g.put(*P(T[0] - 1 + a + (1 if a > 0 else -1), b), "f")
            return fn
        spawn = [grounded(R(crouch=1.6, splay=-0.9, legs=0.0, amp=0.0, fang=0.0, eye="squint", extra=shell(7))),
                 R(crouch=1.0, splay=-0.4, legs=0.8, amp=0.4, fang=0.6, eye="wide", extra=shell(4)),
                 R(crouch=0.4, rear=0.4, fang=1.0, legs=1.6, amp=0.3, eye="wide", extra=shell(2))]
        anims += [("Spawn", spawn, [0.12, 0.08, 0.08])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet(name, anims, outdir, scale=8 if S < 1.2 else 6, remap=BROOD_LIFT if name == "YsvBroodling" else None)


# ================================================================== HOARMOTH (T1, flying)
def hoarmoth(dy=0.0, dx=0.0, flap=0.0, tilt=0.0, ant=0.0, eye="open", fold=0.0, extra=None, dust=0, lean=0.0,
             ground=False):
    """Frost moth seen from the front-right: furry white body, broad pale wings spread to both sides.
    flap: -1 wings raised, 0 level, +1 driven down. fold: 0 open .. 1 folded together over the back."""
    f = Fr()
    cx, cy = dx + 0.0, -7.2 + dy
    if ground: cy = -3.0 + dy
    def wing(sd, layer, back):
        sx, sy = cx + sd * 0.9 + lean * 0.3, cy - 1.0
        span = 7.6 * (0.62 + 0.38 * math.cos(flap * 1.1)) * (1 - fold * 0.75) * (1.0 if sd > 0 else 0.9)
        tipy = sy - 2.6 + flap * 3.4 - fold * 2.5
        tip = (sx + sd * span, tipy)
        low = (sx + sd * span * 0.9, tipy + 4.2 - flap * 0.6)
        root_lo = (sx, sy + 2.0)
        ramp = "3456" if back else "4567"
        def shade(x, y):
            t = abs(x - sx) / max(1.0, span)
            return pick(ramp, 0.7 - t * 0.9 - (y - tipy) * 0.06)
        poly(layer, [(sx, sy - 0.6), (sx + sd * span * 0.5, tipy - 0.6), tip, low, root_lo], ramp[1], shade=shade)
        # hindwing
        hs = span * 0.68
        hl = [(sx, sy + 1.4), (sx + sd * hs, sy + 2.2 + flap * 1.0), (sx + sd * hs * 0.65, sy + 4.8 + flap * 0.5), (sx, sy + 4.2)]
        poly(layer, hl, ramp[0], shade=lambda x, y: pick("2345" if back else "3456", 0.4 - abs(x - sx) / max(1.0, hs) * 0.8))
        # silk-black outer margin + veins
        line(layer, *tip, *low, "B" if back else "C")
        line(layer, low[0], low[1], low[0] - sd * 1.5, low[1] - 0.2, "B" if back else "C")
        if not back:
            line(layer, sx + sd * 1, sy - 0.6, tip[0] - sd * 1.2, tip[1] + 0.3, "7")
            line(layer, sx + sd * 1, sy + 0.2, low[0] - sd * 1.6, low[1] - 0.6, "6")
        # eye-spot
        ex_, ey_ = sx + sd * span * 0.6, (tipy + low[1]) * 0.5 + 0.3
        if span > 3.5:
            for (a_, b_) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                layer.put(*P(ex_ + a_ * sd - (sd < 0), ey_ + b_), "2")
            return (ex_, ey_)
        return None
    sp_far = wing(-1, f.u, True)
    # body: furry white thorax, banded abdomen hanging below, collar of frost fur
    ell(f.b, cx + lean * 0.4, cy + 2.6, 1.4, 2.2, "2356", bias=0.05,
        shader=lambda nu, nv, d, l, ch, x, y: ("6" if (y % 2 == 0 and l > -0.3) else ch))
    ell(f.b, cx + lean * 0.2, cy - 0.4, 2.0, 2.4, "fgh8", bias=0.2,
        shader=lambda nu, nv, d, l, ch, x, y: ("g" if d > 0.7 and (x + y) % 2 else ch))
    hx, hy = cx + 0.8 + lean * 0.6, cy - 3.4
    ell(f.b, hx, hy, 1.5, 1.3, "fgh", bias=0.1)
    # feathery antennae
    for k, sd in enumerate((-1, 1)):
        x, y = hx + sd * 0.6, hy - 1.0
        pts = [(x, y)]
        for j in range(3):
            x += sd * (0.8 + 0.2 * j) + ant * 0.2
            y -= 0.9 - 0.12 * j
            pts.append((x, y))
        polyline(f.b, pts, "6" if sd > 0 else "5")
        for (px_, py_) in pts[1:-1]:
            f.b.put(*P(px_, py_ - 1), "4" if sd < 0 else "5", over=False)
    sp_near = wing(1, f.b, False)
    for sp in (sp_far, sp_near):
        if sp: f.g.put(*P(sp[0] + (0 if sp is sp_near else -1), sp[1]), "I" if eye != "dead" else "3")
    ex, ey = P(hx + 0.7, hy)
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex - 2, ey, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex - 2, ey, "G"); f.g.put(ex, ey - 1, "G")
    elif eye == "squint": f.g.put(ex, ey, "I")
    else: f.g.put(ex, ey, "1"); f.g.put(ex - 2, ey, "1")
    for k in range(dust):
        f.g.put(*P(cx - 5 + k * 3.1, cy + 5 + (k * 7 % 3)), "7" if k % 2 else "6")
    if extra: extra(f, (cx, cy), (hx, hy))
    return f.done()


def hoarmoth_corpse():
    s = hoarmoth(ground=True, flap=0.2, fold=0.0, eye="dead", dy=0.0)
    return grounded(Spr({k: (("5" if v in "67" else v) if k[1] > -2 else v) for k, v in s.px.items()}))


def build_hoarmoth(outdir):
    M = hoarmoth
    idle = [M(flap=-0.9, dy=0.0), M(flap=-0.1, dy=0.6, ant=0.3), M(flap=0.8, dy=1.0, ant=0.5, dust=1),
            M(flap=0.1, dy=0.5, ant=0.3, eye="squint")]
    run = [M(flap=[-1.0, -0.4, 0.4, 1.0, 0.3, -0.5][i], lean=1.0, dx=0.5, dy=[0, 0.4, 0.8, 1.0, 0.6, 0.2][i], ant=-0.5)
           for i in range(6)]
    def motes(n):
        def fn(f, C, hd):
            for k in range(n):
                a = math.radians(-30 + k * 22)
                r = 3 + k * 0.8
                f.g.put(*P(hd[0] + 3 + r * math.cos(a), hd[1] + 3 + r * math.sin(a)), "8" if k % 2 == 0 else "7")
        return fn
    def smear(n):
        def fn(f, C, hd):
            for sd in (-1, 1):
                for k in range(n):
                    f.n.put(*P(C[0] + sd * (8 - k), C[1] - 4 + k * 2.2), "5" if k % 2 else "4")
        return fn
    dust = [M(flap=-1.0, lean=-0.8, dx=-0.4, ant=0.6, eye="wide"),
            M(flap=-1.25, lean=-1.2, dx=-0.8, dy=-0.4, ant=0.8, eye="wide"),
            M(flap=0.3, lean=0.6, dx=0.3, eye="wide", extra=smear(4)),
            M(flap=1.15, lean=1.4, dx=1.0, dy=0.6, eye="squint", extra=motes(4), dust=2),
            M(flap=0.9, lean=1.0, dx=0.8, dy=0.6, extra=motes(2), dust=1),
            M(flap=0.0, lean=0.4, dx=0.3, dy=0.3),
            M(flap=-0.6, dy=0.0)]
    def gustlines(n):
        def fn(f, C, hd):
            for k in range(n):
                y = C[1] - 1 + k * 2.2 - n * 0.4
                line(f.g, C[0] + 8 + (k % 2), y, C[0] + 12 + k, y + 0.5, "7" if k % 2 else "6")
        return fn
    gust = [M(flap=-0.8, dy=-0.4, lean=-0.4, ant=0.4),
            M(flap=-1.3, dy=-1.0, lean=-1.0, dx=-0.6, ant=0.7, eye="wide"),
            M(flap=-1.45, dy=-1.4, lean=-1.4, dx=-1.0, ant=0.9, eye="wide", fold=0.15),
            M(flap=-0.2, dy=-0.6, lean=0.0, eye="wide", extra=smear(5)),
            M(flap=1.25, dy=0.6, lean=1.6, dx=1.2, eye="squint", extra=gustlines(4), dust=3),
            M(flap=1.0, dy=0.7, lean=1.2, dx=1.0, extra=gustlines(2), dust=2),
            M(flap=0.2, dy=0.4, lean=0.4, dx=0.4),
            M(flap=-0.6, dy=0.0)]
    death = [M(flap=-1.3, lean=-1.5, dy=-0.5, eye="wide", fold=0.3, ant=1.0),
             M(flap=0.8, lean=1.5, dy=3.0, eye="dead", fold=0.5, ant=-1),
             M(flap=1.0, dy=5.0, eye="dead", fold=0.8, ant=-1.5),
             hoarmoth_corpse()]
    knock = M(flap=-1.2, lean=-1.6, dx=-1, dy=-0.5, eye="squint", ant=1.0)
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.06] * 6),
             ("Dust", dust, [0.12, 0.12, 0.06, 0.08, 0.1, 0.1, 0.12]),
             ("Gust", gust, [0.12, 0.14, 0.14, 0.06, 0.08, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.14, 0.4], knock)
    sheet("YsvHoarmoth", anims, outdir, scale=8)


# ================================================================== RIME SHARDLING (T1)
def crystal(c, bx, by, ang, ln, wd, lit=0.0, ramp=None, ridge="8"):
    """A faceted ice crystal (side view of a hexagonal prism with a point) from base (bx,by) toward ang."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    shoulder = 0.68
    pts = [(bx - nx * wd, by - ny * wd), (bx + ux * ln * shoulder - nx * wd, by + uy * ln * shoulder - ny * wd),
           (bx + ux * ln, by + uy * ln),
           (bx + ux * ln * shoulder + nx * wd, by + uy * ln * shoulder + ny * wd), (bx + nx * wd, by + ny * wd)]
    lit_side = -1 if (nx + ny) > 0 else 1        # the face toward the top-left is lit
    def shade(x, y):
        s = (x - bx) * nx + (y - by) * ny
        t = ((x - bx) * ux + (y - by) * uy) / max(1.0, ln)
        if (s * lit_side) > 0.4: return pick(ramp or "5678", 0.55 + lit - t * 0.3)
        if (s * lit_side) < -0.4: return pick(ramp or "3456", -0.1 + lit - t * 0.3)
        return pick(ramp or "4567", 0.2 + lit)
    poly(c, pts, "5", shade=shade)
    line(c, bx + ux * 0.6, by + uy * 0.6, bx + ux * ln * 0.92, by + uy * ln * 0.92, ridge)
    return (bx + ux * ln, by + uy * ln)


def shardling(dx=0.0, dy=0.0, lean=0.0, sq=0.0, legs=0.0, amp=0.0, glow=0, eye="open", hood=0.0, crack=0, extra=None,
              spikes=1.0):
    f = Fr()
    piv = (dx, 0.0)
    def L(x, y): return rot_about((dx + x, y * (1 - sq * 0.12) + dy), piv, lean)
    # stubby crystal legs
    for k, ox in enumerate((-2.2, 1.8)):
        ph = legs + k * math.pi
        fx = dx + ox + amp * 1.3 * math.sin(ph)
        fy = -max(0.0, amp * 1.2 * math.cos(ph))
        hip = L(ox * 0.8, -3.0)
        tube(f.u if k == 0 else f.b, [hip, (fx, fy - 0.8)], [1.2, 1.0], "3456" if k else "2345", bias=0.1)
        f.b.put(*P(fx + 0.5, fy), "6" if k else "4")
        f.b.put(*P(fx - 0.5, fy), "5" if k else "3")
    # back crystal spikes (behind the body)
    for (bx, by, a, ln, wd) in ((-2.5, -7.0, -150, 5.0 * spikes, 1.4), (-1.0, -9.0, -118, 5.5 * spikes, 1.5),
                                (1.6, -9.5, -82, 3.4 * spikes, 1.1)):
        p0 = L(bx, by)
        crystal(f.u, p0[0], p0[1], a + lean, ln, wd, lit=0.05 * glow)
    # core body: one fat crystal lump
    c0 = L(0.0, -5.5)
    ell(f.b, c0[0], c0[1], 4.6, 4.4 - sq, "34567", ang=lean, bias=0.1,
        shader=lambda nu, nv, d, l, ch, x, y: ("8" if (abs(nu + nv * 0.6 + 0.2) < 0.08 and nv < 0.2) else
                                               "7" if (abs(nu - nv * 0.8 - 0.35) < 0.08) else ch))
    # black widow-silk shawl over the head and back
    hp = [L(-4.8, -4.0), L(-4.2, -8.0), L(-1.5, -10.6 - hood * 0.6), L(2.4, -10.4), L(4.9, -7.6), L(5.2, -5.6),
          L(3.6, -5.8), L(2.2, -7.2), L(-0.2, -6.4), L(-2.8, -3.6)]
    poly(f.b, hp, "C", shade=lambda x, y: pick("ABCDE", 0.5 - (x - dx) * 0.06 - (y + 10) * 0.12))
    line(f.b, *L(-1.2, -10.0), *L(3.6, -8.6), "E")          # violet sheen along the fold
    line(f.b, *L(-4.6, -4.2), *L(-3.0, -3.4), "D")
    # lace fringe of frost on the shawl edge
    for k in range(4):
        x, y = L(-4.5 + k * 0.6, -4.0 + k * 0.2)
        f.b.put(*P(x, y + 1), "7" if k % 2 else "6")
    # a crystal horn breaking through the hood
    hn = L(1.0, -10.0)
    crystal(f.b, hn[0], hn[1], -68 + lean, 3.6 * spikes, 1.0, lit=0.1)
    # face in the shadow of the hood
    poly(f.b, [L(2.0, -7.6), L(4.8, -7.4), L(5.0, -5.4), L(3.4, -4.8), L(2.0, -5.6)], "1",
         shade=lambda x, y: "1" if (x + y) % 3 else "2")
    ey = L(3.0, -6.6); ey2 = L(4.3, -6.4)
    if eye == "open":
        f.g.put(*P(*ey), "G"); f.g.put(*P(*ey2), "I")
    elif eye == "wide":
        f.g.put(*P(*ey), "H"); f.g.put(*P(*ey2), "G"); f.g.put(*P(ey[0], ey[1] - 1), "I")
    elif eye == "squint":
        f.g.put(*P(*ey), "I")
    else:
        f.g.put(*P(*ey), "2")
    # inner glow (charging)
    if glow:
        for k in range(glow * 2):
            a = math.radians(k * 67 + glow * 20)
            f.g.put(*P(c0[0] - 1 + 1.8 * math.cos(a), c0[1] + 1 + 1.6 * math.sin(a)), "G" if k % 2 else "H")
    if crack:
        for (x, y) in ((-1, -4), (0, -5), (-1, -6), (0, -7), (1, -3))[:crack + 2]:
            f.b.put(*P(*L(x, y)), "1")
    if extra: extra(f, c0, hn)
    return f.done()


def shardling_corpse():
    f = Fr()
    for (bx, by, a, ln, wd) in ((-5, -1, -160, 4, 1.2), (-2, -1, -120, 3.5, 1.2), (3, -1, -40, 3.5, 1.1), (6, 0, -10, 3, 1.0),
                                (0, -1, -80, 3.0, 1.3)):
        crystal(f.b, bx, by, a, ln, wd)
    poly(f.b, [(-4, -1), (-2, -4), (2, -4.5), (5, -2), (4, -1)], "C", shade=lambda x, y: pick("ABCD", 0.3 - y * 0.05))
    line(f.b, -2, -4, 2, -4.5, "E")
    f.g.put(1, -2, "2")
    for x in (-6, -3, 1, 5, 7): f.g.put(x, 0, "7")
    return f.done()


def build_shardling(outdir):
    Sh = shardling
    # v0.8: four distinct breaths (frame 3 used to round to frame 0)
    idle = [Sh(), Sh(dy=0.4, sq=0.3, glow=0), Sh(dy=0.6, sq=0.5, eye="squint", glow=1), Sh(dy=-0.4, sq=-0.3, hood=1.0, spikes=1.06)]
    run = [Sh(legs=i * math.pi / 3, amp=1.0, lean=4 + 3 * math.sin(i * math.pi / 3), dy=-0.6 * abs(math.sin(i * math.pi / 3)),
              hood=0.5 * math.cos(i * math.pi / 3)) for i in range(6)]
    def ram_fx(n):
        def fn(f, c0, hn):
            for k in range(n):
                f.g.put(*P(c0[0] + 6 + (k % 3), c0[1] - 2 + k * 1.3), "8" if k % 2 == 0 else "7")
        return fn
    def streak(f, c0, hn):
        for k in range(3):
            line(f.n, c0[0] - 7 - k, c0[1] - 2 + k * 2, c0[0] - 4 - k, c0[1] - 2 + k * 2, "4")
    ram = [Sh(lean=-12, dx=-0.8, sq=0.4, eye="wide", amp=0.3, legs=0.5),
           Sh(lean=-20, dx=-1.6, sq=0.6, eye="wide", amp=0.4, legs=1.0, hood=1),
           Sh(lean=18, dx=2.4, eye="wide", amp=1.0, legs=2.0, extra=streak),
           Sh(lean=26, dx=3.6, sq=0.2, eye="squint", amp=0.6, legs=2.4, extra=ram_fx(5)),
           Sh(lean=20, dx=3.0, eye="squint", amp=0.4, legs=2.6, extra=ram_fx(2)),
           Sh(lean=6, dx=1.2, legs=3.0, amp=0.3),
           Sh(lean=0, dx=0.2)]
    def motes(n, h):
        def fn(f, c0, hn):
            for k in range(n):
                f.g.put(*P(hn[0] - 3 + k * 2, hn[1] - h - (k * 3) % 4), "8" if k % 2 else "6")
        return fn
    def call(f, c0, hn):
        for k in range(6):
            f.g.put(*P(hn[0] + (k % 2), hn[1] - 2 - k * 1.5), "H" if k < 2 else "G" if k < 4 else "7")
    icicle = [Sh(sq=0.5, dy=0.3, glow=1, eye="squint"),
              Sh(sq=-0.4, dy=-0.6, glow=1, eye="wide", spikes=1.15, extra=motes(2, 2)),
              Sh(sq=-0.8, dy=-1.2, glow=2, eye="wide", spikes=1.25, hood=1, extra=motes(3, 3)),
              Sh(sq=-0.9, dy=-1.4, glow=3, eye="wide", spikes=1.3, hood=1, extra=motes(4, 4)),
              Sh(sq=0.6, dy=0.4, glow=3, eye="wide", spikes=1.3, extra=call),
              Sh(sq=0.4, dy=0.2, glow=1, eye="squint", spikes=1.15),
              Sh(sq=0.1, glow=0, spikes=1.05),
              Sh()]
    death = [Sh(lean=-14, dx=-0.6, eye="wide", crack=1, hood=1),
             Sh(lean=-24, dx=-1.0, sq=0.8, eye="dead", crack=2, spikes=0.8),
             grounded(Sh(lean=-60, sq=1.0, eye="dead", crack=3, spikes=0.6)),
             shardling_corpse()]
    knock = Sh(lean=-16, dx=-0.8, eye="squint", hood=1, amp=0.4, legs=1.2)
    anims = [("Idle", idle, [0.24, 0.18, 0.24, 0.18]), ("Run", run, [0.08] * 6),
             ("Ram", ram, [0.14, 0.14, 0.06, 0.06, 0.1, 0.12, 0.12]),
             ("Icicle", icicle, [0.12, 0.12, 0.12, 0.14, 0.06, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("YsvShardling", anims, outdir, scale=8)


# ================================================================== SILK WEAVER (T2)
def weaver_lace(f, T, A):
    """Frost-lace web pattern over the Weaver's abdomen: spokes and one ring, only on existing body pixels."""
    pass


def build_weaver(outdir):
    S = 1.24
    def lace(f, T, A, ph=0):
        # spokes + ring of frost lace on the abdomen (drawn only over abdomen pixels)
        cx, cy = A
        for k in range(5):
            a = math.radians(-150 + k * 40 + ph * 6)
            for r in (1.5, 2.6, 3.6):
                p = P(cx + r * math.cos(a), cy + r * math.sin(a) * 0.85)
                if f.b.px.get(p) in ("C", "D", "E"): f.b.put(*p, "5" if r < 3 else "6")
        for k in range(12):
            a = math.radians(k * 30)
            p = P(cx + 2.7 * math.cos(a), cy + 2.3 * math.sin(a))
            if f.b.px.get(p) in ("C", "D", "E") and math.sin(a) < 0.5: f.b.put(*p, "4")
    def dragline(n=6, sway=0.0):
        def fn(f, sp):
            x, y = sp
            for k in range(n):
                f.n.put(*P(x - 0.3 * k + sway * math.sin(k * 0.8), y + k * 1.0), "7" if k % 2 else "6")
        return fn
    def W(extra=None, spin=None, ph=0, **k):
        def ex(f, T, A):
            lace(f, T, A, ph)
            if extra: extra(f, T, A)
        return spider(S=S, weaver=True, extra=ex, spin=spin, style="stilt", **k)
    idle = [W(legs=0.0, amp=0.25, spin=dragline(5)), W(legs=0.6, amp=0.25, breathe=1, dy=0.3, crouch=0.2, spin=dragline(5, 0.6), ph=1),
            W(legs=1.2, amp=0.25, breathe=1, dy=0.3, crouch=0.2, eye="squint", spin=dragline(5, 1.0), ph=2),
            W(legs=1.8, amp=0.25, spin=dragline(5, 0.4), ph=1)]
    run = [W(legs=i * math.pi / 3, amp=1.0, dy=-0.6 * abs(math.sin(i * math.pi / 3)), tilt=3 * math.sin(i * math.pi / 3), breathe=i % 2,
             ph=i) for i in range(6)]
    def bite_fx(n):
        def fn(f, T, A):
            hx, hy = T[0] + 2.7 * S + 2.5, T[1] + 2.5 * S
            for k, (a, b) in enumerate(((1, -2), (2, 0), (1, 2), (3, -1), (3, 1), (4, 0))[:n]):
                f.g.put(*P(hx + a, hy + b), "8" if k % 2 == 0 else "6")
        return fn
    fangs = [W(dx=-0.6, crouch=0.4, rear=0.4, fang=0.4, legs=0.3, amp=0.2, eye="wide"),
             W(dx=-1.4, crouch=0.2, rear=1.0, fang=1.0, legs=0.4, amp=0.2, eye="wide", tilt=-10, lift=0.6),
             W(dx=-1.0, crouch=0.0, rear=1.2, fang=1.0, legs=0.5, amp=0.2, eye="wide", tilt=-14, lift=1.0),
             W(dx=2.6, crouch=0.8, rear=0.0, fang=0.0, legs=1.6, amp=0.7, tilt=12, splay=0.4, eye="squint", extra=bite_fx(6)),
             W(dx=2.4, crouch=0.7, fang=0.0, legs=1.9, amp=0.5, tilt=10, splay=0.3, eye="squint", extra=bite_fx(3)),
             W(dx=1.2, crouch=0.3, fang=0.3, legs=2.4, amp=0.3, tilt=4),
             W(dx=0.2, legs=2.8, amp=0.2)]
    def thread(n, taut=True):
        def fn(f, sp):
            x, y = sp
            for k in range(n):
                f.g.put(*P(x + 1 + k * 1.6, y - 0.4 * k + (0 if taut else (k % 2))), "8" if k % 3 == 0 else "7")
        return fn
    def tug(f, sp):
        x, y = sp
        for k in range(10):
            f.g.put(*P(x + 1 + k * 1.6, y - 0.2 * k), "8" if k % 2 == 0 else "6")
    tether = [W(abd_lift=0.25, crouch=0.4, tilt=-4, eye="open", rear=0.2),
              W(abd_lift=0.6, crouch=0.6, tilt=-8, eye="wide", rear=0.2, dx=-0.4),
              W(abd_lift=0.92, crouch=0.8, tilt=-6, eye="wide", rear=0.1, dx=-0.8, spin=thread(1)),
              W(abd_lift=0.95, crouch=0.7, tilt=-2, eye="wide", dx=-0.4, spin=thread(5)),
              W(abd_lift=0.9, crouch=0.9, tilt=-4, eye="squint", dx=-1.2, legs=0.6, amp=0.4, spin=tug),
              W(abd_lift=0.88, crouch=1.0, tilt=-6, eye="squint", dx=-1.8, legs=1.2, amp=0.4, spin=tug),
              W(abd_lift=0.5, crouch=0.5, tilt=-2, eye="open", dx=-0.8, legs=1.6, amp=0.3),
              W(abd_lift=0.1, legs=2.0, amp=0.2)]
    death = [W(dx=-0.6, rear=0.8, splay=0.8, fang=1, eye="wide", tilt=-14, lift=1.0),
             grounded(W(dx=-1, rear=1.0, splay=1.2, fang=1, eye="dead", tilt=-40, crouch=0.8)),
             grounded(recol(W(dx=-1, rear=1.0, splay=1.5, fang=0.5, eye="dead", tilt=-70, crouch=1.0), {"7": "6"})),
             spider_corpse(S, weaver=True)]
    knock = W(dx=-0.8, rear=0.5, splay=0.7, fang=0.6, eye="squint", tilt=-12, lift=0.5)
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.08] * 6),
             ("Fangs", fangs, [0.14, 0.12, 0.12, 0.06, 0.1, 0.12, 0.12]),
             ("Tether", tether, [0.12, 0.12, 0.12, 0.06, 0.14, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("YsvWeaver", anims, outdir, scale=6)


# ================================================================== WIDOWS (Veil Witch T2, Winter Bride T3)
def back_moth_wings(c, L, k, veil, bride, hem):
    """v0.9 lineage: the Veil Witch (Hoarmoth + Shardling) wears the Hoarmoth's frost wings folded down her back in place
    of a plain veil: a long pale forewing with black margins, veins and a dark eye-spot, the hindwing peeking out below.
    The Winter Bride (Silkmoth + Veil Witch) spreads them wider in the Silkmoth's colours (violet root, frost edge)."""
    root = L(-0.4, -16.8)
    spread = 1.0 + veil * 0.25 + (0.15 if bride else 0.0)
    lead = L(-4.6 * spread, -21.0 + veil * 0.8)
    tip = L(-8.6 * spread - hem * 0.4, -14.6 + veil * 1.2)
    low = L(-6.8 * spread - hem * 0.4, -8.0 + veil)
    inner = L(-1.4, -10.0)
    fw = [root, lead, tip, low, inner]
    ramp_f = "CDE556" if bride else "4567"
    def shade(x, y):
        t = math.hypot(x - root[0], y - root[1]) / max(1.0, 14.0 * k)
        return pick(ramp_f, 0.75 - t * 0.9 - (x - root[0]) * 0.02)
    poly(c, fw, ramp_f[1], shade=shade)
    hw = [L(-0.8, -11.0), L(-6.2 * spread - hem * 0.4, -7.6 + veil), L(-5.0 * spread, -2.0), L(-1.6, -3.0)]
    poly(c, hw, "3" if not bride else "C",
         shade=lambda x, y: pick("3456" if not bride else "BCDE", 0.5 - math.hypot(x - hw[0][0], y - hw[0][1]) / (12.0 * k)))
    line(c, *lead, *tip, "B" if bride else "C"); line(c, *tip, *low, "B" if bride else "C")       # silk-black margins
    line(c, *L(-0.8, -16.0), *L(-7.4 * spread, -14.0 + veil), "7" if not bride else "6")         # veins
    line(c, *L(-0.8, -13.0), *L(-5.0 * spread, -4.0 + veil), "6" if not bride else "E")
    ex, ey = L(-5.4 * spread, -15.2 + veil * 0.8)                                                 # eye-spot
    for (a_, b_) in ((0, 0), (1, 0), (0, 1), (1, 1)) if k > 1.2 else ((0, 0), (0, 1)):
        c.put(*P(ex + a_, ey + b_), "1" if not bride else "A")
    c.put(*P(ex, ey), "5" if not bride else "6")


def widow(k=1.0, bride=False, dx=0.0, dy=0.0, lean=0.0, sway=0.0, hands=((-4, -11), (4, -11)), veil=0.0, eye="open",
          mouth=0, crown=0, wand=None, bouquet=None, legs_up=0.0, legs_ph=0.0, veil_up=0.0, extra=None, hem=0.0, sink=0.0):
    """A widow in black silk mourning dress and a frost-lace veil. k scales (witch 1.0, bride 1.5).
    hands: (back, front) world positions relative to the feet. wand: (butt, tip) crystal shard held by the front hand.
    bouquet: True draws frozen roses at the front hand. veil_up: 0 veil down over the face .. 1 lifted back (breath).
    legs_up: bride's four spider legs spread (0 folded along her back .. 1 raised high)."""
    f = Fr()
    piv = (dx, 0.0)
    def L(x, y): return rot_about((dx + x * k, (y + sink) * k + dy), piv, lean)
    waist = L(0.4, -9.0)
    sho = L(0.8 + lean * 0.0, -14.2)
    head = L(1.4, -16.6)
    # ---- far layer: long veil falling down the back to the floor (lace with holes)
    vtop = L(-0.6, -18.0)
    vw = veil * 1.2
    vpts = [L(-0.2, -18.6), L(-3.2 - vw, -15.0), L(-5.6 - vw * 1.5 - hem, -7.0), L(-7.4 - vw * 2 - hem * 1.4, 0.0) if not bride else L(-9.6 - vw * 2 - hem, 0.0),
            L(-3.0 - hem * 0.5, 0.0), L(-2.0, -10.0), L(0.4, -15.5)]
    # v0.8: the Witch wears a pale frost veil over black; the Bride is her negative (black lace veil over a white gown)
    # v0.9: the veil becomes folded moth wings (see back_moth_wings); a short lace veil still hangs from the crown
    back_moth_wings(f.u, L, k, veil, bride, hem)
    sv = [L(-0.2, -18.6), L(-2.4 - vw * 0.5, -15.6), L(-1.6, -13.8), L(0.4, -15.5)]
    poly(f.u, sv, "C" if bride else "6", shade=lambda x, y: (("E" if bride else "7") if (x + 2 * y) % 5 == 0 else
                                                             ("C" if bride else "6") if (x + y) % 2 else ("B" if bride else "5")))
    # ---- bride: train behind the gown + spider legs from the back
    if bride and False:   # v0.10: the Silkmoth's spider legs are gone (one parent: the Veil Witch)
        for j in range(4):
            ph = legs_ph + j * 0.9
            root = L(-1.4 + j * 0.6, -13.6)
            ang = [-128, -108, -88, -62][j] - legs_up * 8 + 5 * math.sin(ph)
            l1 = [6.4, 7.6, 7.8, 6.2][j] * k
            knee = (root[0] + l1 * math.cos(math.radians(ang)), root[1] + l1 * math.sin(math.radians(ang)) - legs_up * 1.5 * k)
            a2 = [128, 152, 176, 58][j] - legs_up * [25, 25, 25, -15][j] + 4 * math.sin(ph + 1)
            l2 = [6.4, 6.0, 5.4, 4.6][j] * k
            tip = (knee[0] + l2 * math.cos(math.radians(a2)), knee[1] + l2 * math.sin(math.radians(a2)))
            lay = f.u
            cols = "1234" if j in (1, 2) else "BCDE"
            tube(lay, [root, knee], [1.0, 0.8], cols, bias=0.25)
            tube(lay, [knee, tip], [0.8, 0.35], cols, bias=0.1)
            lay.put(*P(*knee), "6" if j in (0, 3) else "4")
            lay.put(*P(*tip), "8" if j in (0, 3) else "6")
            if j in (0, 3): lay.put(*P(knee[0] + (tip[0] - knee[0]) * 0.35, knee[1] + (tip[1] - knee[1]) * 0.35), "6")
    # ---- gown: bell skirt of black silk, violet sheen folds, frost lace hem
    sw = sway
    hw0, hw1 = 2.2, 5.6 + hem * 0.5
    if bride:   # a wide white bell gown with a long train sweeping back along the floor
        skirt = [L(-hw0, -9.4), L(hw0 + 0.6, -9.4), L(hw1 + 1.0 + sw * 0.8 + 0.6, -0.2), L(-hw1 - 5.5 + sw * 0.8 - hem, -0.2),
                 L(-hw1 - 3.0 - hem * 0.5, -2.4), L(-hw0 - 1.4, -6.0)]
    else:
        skirt = [L(-hw0, -9.4), L(hw0 + 0.6, -9.4), L(hw1 + sw * 0.8 + 0.6, -0.2), L(-hw1 + sw * 0.8, -0.2)]
    GOWN = "4fgh8" if bride else "BCDEF"     # v0.8: the witch's black silk lifted a step (readability)
    def gown_shade(x, y):
        u = (x - waist[0]) / max(1.0, k * 5)
        band = math.sin((x - y * 0.25 * sw) * 1.3 / k)
        l = -0.25 - u * 0.45 + (0.35 if band > 0.7 else 0) + (0.15 if y > -2 * k else 0) + (0.2 if bride else 0)
        return pick(GOWN, l)
    poly(f.b, skirt, "C", shade=gown_shade)
    # lace hem (frost on the black gown, black lace on the white one)
    x0_, x1_ = int(min(p_[0] for p_ in skirt)), int(skirt[2][0])
    for x in range(x0_, x1_ + 1):
        if (x, -1) not in f.b.px: continue
        f.b.put(x, -1, ("D" if (x + int(hem * 3)) % 2 == 0 else "B") if bride else ("6" if (x + int(hem * 3)) % 2 == 0 else "4"))
        if (x + int(hem * 3)) % 3 == 0: f.b.put(x, -2, "C" if bride else "5")
    # bodice
    tube(f.b, [waist, sho], [1.6 * k, 1.9 * k], "ABCD", bias=0.2)
    ell(f.b, *L(0.9, -12.0), 1.7 * k, 2.4 * k, "BCDE", ang=lean, bias=0.2)
    # back arm (behind the body)
    shb = L(-0.8, -13.6)
    (ebx, eby), (hbx, hby) = ik(shb[0], shb[1], dx + hands[0][0] * k, hands[0][1] * k + dy, 3.6 * k, 3.6 * k, bend=-1)
    tube(f.u, [shb, (ebx, eby), (hbx, hby)], [0.8 * k, 0.7 * k, 0.6 * k], "ABC", bias=0.1)
    f.u.put(*P(hbx, hby), "g")
    # head: dark hair swept back under the veil, pale face, lace over the face
    ell(f.b, *L(0.2, -17.0), 2.0 * k, 1.9 * k, "ABC", ang=lean, bias=0.1)
    ell(f.b, head[0] + 0.4 * k, head[1] + 0.2 * k, 1.55 * k, 1.9 * k, "fgh", ang=lean, bias=0.3)
    if veil_up < 0.5:
        for yy in range(int(head[1] - 1.6 * k), int(head[1] + 2.2 * k) + 1):
            for xx in range(int(head[0] + 0.2 * k), int(head[0] + 2.2 * k) + 1):
                if f.b.px.get((xx, yy)) in ("f", "g", "h") and (xx + yy) % 2 == 0: f.b.put(xx, yy, "6" if (xx * 3 + yy) % 4 else "7")
        line(f.b, *L(2.8, -18.0), *L(3.4, -14.6), "5")
    else:
        line(f.b, *L(-0.4, -19.0), *L(-1.6, -15.6), "7")
    # mouth (breath)
    mx, my = L(3.0, -15.6)
    if mouth: f.b.put(*P(mx, my), "1"); f.b.put(*P(mx, my + 1), "1" if mouth > 1 else "f")
    # crown of icicles
    cpts = [(-0.6, 4), (0.4, 5), (1.4, 6 if bride else 5), (2.4, 5), (3.2, 4)]
    for i, (ox, h) in enumerate(cpts):
        bx_, by_ = L(ox, -18.4)
        crystal(f.b, bx_, by_, -90 + (ox - 1.3) * 22 + lean, h * (0.62 if not bride else 0.72) * k, 0.55 * k, lit=0.0,
                ramp="3456", ridge="6")
    # v0.9 lineage: the Hoarmoth's feathered antennae rise from the crown as two plumes; the Shardling's crystal grows
    # through the hem of the gown
    for sd, (ox, a0) in enumerate(((0.0, -118.0), (2.6, -64.0))):
        x, y = L(ox, -19.0)
        a = a0 + lean
        pts = [(x, y)]
        for j in range(4 if k < 1.2 else 5):
            a += (-10 if sd == 0 else 10)
            x += math.cos(math.radians(a)) * k; y += math.sin(math.radians(a)) * k
            pts.append((x, y))
        polyline(f.b, pts, "g" if not bride else "h")
        for j in range(1, len(pts)):
            if j % 2: f.b.put(*P(pts[j][0] + (-1 if sd == 0 else 1), pts[j][1] + 0.5), "f", over=False)
    if not bride:   # v0.10: frost-fur trim at the hem (the Hoarmoth's ruff) instead of the Shardling's crystals
        for j in range(9):
            f.b.put(*P(*L(-5.2 + j * 1.3, -1.4 - (j % 2))), "h" if j % 2 else "g")
    # front arm + held thing
    shf = L(1.6, -13.6)
    (efx, efy), (hfx, hfy) = ik(shf[0], shf[1], dx + hands[1][0] * k, hands[1][1] * k + dy, 3.6 * k, 3.6 * k, bend=1)
    tube(f.b, [shf, (efx, efy), (hfx, hfy)], [0.9 * k, 0.8 * k, 0.6 * k], "BCDE", bias=0.15)
    tip = None
    if wand is not None:
        (bx_, by_), (tx_, ty_) = wand
        bx_, by_, tx_, ty_ = dx + bx_ * k, by_ * k + dy, dx + tx_ * k, ty_ * k + dy
        ang = math.degrees(math.atan2(ty_ - by_, tx_ - bx_))
        tip = crystal(f.b, bx_, by_, ang, math.hypot(tx_ - bx_, ty_ - by_), 0.8 * k, lit=0.15)
        f.g.put(*P(*tip), "G")
    f.b.put(*P(hfx, hfy), "h"); f.b.put(*P(hfx + 0.6, hfy + 0.4), "g")
    if bouquet:
        for j, (ox, oy) in enumerate(((0.8, -0.4), (1.8, 0.4), (0.6, 1.2), (1.6, -1.4))):
            ell(f.b, hfx + ox * k * 0.7, hfy + oy * k * 0.7, 0.9 * k, 0.8 * k, "4567", bias=0.2)
            f.b.put(*P(hfx + ox * k * 0.7, hfy + oy * k * 0.7), "8")
        line(f.b, hfx - 0.5, hfy + 1, hfx - 1.2, hfy + 3.2 * k, "C")
    # eyes (glowing through the lace)
    ex, ey = P(*L(2.3, -16.9))
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex + 1 if k > 1.2 else ex + 1, ey, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex + 1, ey, "G"); f.g.put(ex, ey - 1, "I")
    elif eye == "squint": f.g.put(ex, ey, "I")
    elif eye == "shut": f.g.put(ex, ey, "f")
    else: f.g.put(ex, ey, "2")
    if crown:
        for i, (ox, h) in enumerate(cpts):
            bx_, by_ = L(ox, -18.4 - h * 0.7)
            f.g.put(*P(bx_, by_), "H" if crown > 1 else "G")
    if extra: extra(f, (hfx, hfy), tip, head)
    return f.done()


def widow_corpse(k=1.0, bride=False):
    f = Fr()
    # collapsed heap of silk (black for the witch, white for the bride), veil spread over it, crown shattered beside
    ell(f.b, -1 * k, -2.0 * k, 6.0 * k, 2.4 * k, "4fgh8" if bride else "ABCDE", bias=0.05)
    if bride:
        poly(f.u, [(-8 * k, 0), (-5 * k, -3.5 * k), (1 * k, -4.2 * k), (4 * k, -2.5 * k), (2 * k, 0)], "C",
             shade=lambda x, y: ("E" if (x + 2 * y) % 5 == 0 else "C" if (x + y) % 2 else "B"))
    else:
        poly(f.u, [(-8 * k, 0), (-5 * k, -3.5 * k), (1 * k, -4.2 * k), (4 * k, -2.5 * k), (2 * k, 0)], "6",
             shade=lambda x, y: ("7" if (x + 2 * y) % 5 == 0 else "6" if (x + y) % 2 else "5"))
    ell(f.b, 4.0 * k, -1.6 * k, 1.8 * k, 1.5 * k, "fgh", bias=0.2)
    for i in range(3):
        crystal(f.b, 6.5 * k + i * 1.5, -0.5, -40 - i * 50, 2.4 * k, 0.5 * k)
    if bride:
        for j in range(3):
            polyline(f.b, [(-3 * k + j * 2 * k, -3.6 * k), (-4 * k + j * 2 * k, -6.5 * k), (-2.5 * k + j * 2 * k, -7.5 * k)], "C")
    f.g.put(*P(4.6 * k, -1.8 * k), "2")
    return f.done()


def build_witch(outdir):
    Wd = lambda **kw: widow(k=1.0, **kw)
    REST = ((-3.5, -9.5), (4.4, -10.0))
    WAND = ((3.8, -8.4), (5.6, -14.0))
    idle = [Wd(hands=REST, wand=WAND, sway=0.0), Wd(hands=((-3.5, -9.2), (4.4, -9.7)), wand=((3.8, -8.1), (5.6, -13.7)), sway=0.4, veil=0.3, hem=0.3),
            Wd(hands=((-3.5, -9.0), (4.4, -9.5)), wand=((3.8, -7.9), (5.6, -13.5)), sway=0.7, veil=0.6, hem=0.5, eye="squint"),
            Wd(hands=REST, wand=WAND, sway=0.3, veil=0.3, hem=0.2)]
    run = [Wd(lean=6, sway=-1.2 + 0.8 * math.sin(i * math.pi / 3), veil=1.0 + 0.4 * math.sin(i * math.pi / 3), hem=0.6 + 0.4 * math.cos(i * math.pi / 3),
              dy=-0.4 * abs(math.sin(i * math.pi / 3)), hands=((-4.5, -10.0), (4.0, -10.6)), wand=((3.2, -9.0), (7.8, -12.0)))
           for i in range(6)]
    def flick(n):
        def fn(f, hand, tip, head):
            if tip is None: return
            for j in range(n):
                f.g.put(*P(tip[0] + 1 + j, tip[1] - 1 + (j % 2)), "8" if j % 2 == 0 else "6")
        return fn
    shard = [Wd(hands=((-3.8, -10.0), (2.6, -15.2)), wand=((2.4, -14.0), (0.6, -19.6)), eye="open", lean=-3, veil=0.2),
             Wd(hands=((-4.2, -10.4), (1.6, -16.6)), wand=((1.4, -15.6), (-1.6, -20.6)), eye="wide", lean=-7, veil=0.4, hem=0.3, crown=1),
             Wd(hands=((-4.4, -10.6), (5.6, -14.2)), wand=((5.0, -13.4), (10.6, -14.6)), eye="wide", lean=4, veil=0.8, hem=0.5),
             Wd(hands=((-4.4, -10.4), (6.4, -12.4)), wand=((5.8, -11.8), (11.8, -11.0)), eye="squint", lean=7, veil=1.0, hem=0.6, extra=flick(4)),
             Wd(hands=((-4.2, -10.2), (6.0, -12.0)), wand=((5.4, -11.4), (11.2, -10.6)), eye="squint", lean=5, veil=0.8, hem=0.5, extra=flick(2)),
             Wd(hands=((-3.8, -9.8), (5.0, -10.6)), wand=((4.4, -9.6), (8.4, -13.6)), lean=2, veil=0.4),
             Wd(hands=REST, wand=WAND, veil=0.2)]
    def rising(n, up):
        def fn(f, hand, tip, head):
            for j in range(n):
                f.g.put(*P(head[0] - 5 + j * 2.5, head[1] - 4 - up - (j * 5) % 4), "8" if j % 2 else "6")
        return fn
    def slam(f, hand, tip, head):
        for j in range(-4, 5):
            f.g.put(*P(8 + j, 0), "7" if j % 2 else "8")
        for j in range(3):
            line(f.g, 6 + j * 2.5, -1, 6.5 + j * 2.5, -4 - j, "6")
    crystals = [Wd(hands=((-3.6, -11.4), (4.6, -12.4)), wand=((4.0, -11.6), (5.6, -17.0)), eye="open", veil=0.3, crown=1),
                Wd(hands=((-2.6, -16.6), (3.4, -17.6)), wand=((3.0, -16.6), (3.6, -22.4)), eye="wide", lean=-4, veil=0.8, hem=0.4, crown=1, extra=rising(2, 1)),
                Wd(hands=((-2.2, -18.0), (2.8, -19.0)), wand=((2.6, -18.0), (2.8, -24.0)), eye="wide", lean=-6, veil=1.0, hem=0.6, crown=2, extra=rising(4, 2)),
                Wd(hands=((-2.0, -18.4), (2.6, -19.4)), wand=((2.4, -18.4), (2.6, -24.4)), eye="wide", lean=-6, veil=1.2, hem=0.7, crown=2, extra=rising(5, 3)),
                Wd(hands=((-1.0, -8.0), (6.6, -5.0)), wand=((6.0, -5.0), (9.4, -0.4)), eye="wide", lean=10, veil=1.3, hem=0.9, crown=2, extra=slam),
                Wd(hands=((-1.4, -8.6), (6.2, -5.8)), wand=((5.6, -5.6), (9.0, -1.2)), eye="squint", lean=8, veil=1.0, hem=0.8, crown=1),
                Wd(hands=((-3.0, -9.4), (5.0, -8.8)), wand=((4.4, -8.0), (7.4, -12.6)), lean=3, veil=0.5, hem=0.4),
                Wd(hands=REST, wand=WAND, veil=0.2)]
    death = [Wd(hands=((-5.0, -14.0), (4.6, -15.0)), wand=((4.0, -14.2), (7.0, -19.0)), eye="wide", lean=-10, veil=1.2, mouth=2, hem=0.8),
             Wd(hands=((-3.0, -7.0), (5.0, -6.0)), eye="shut", lean=18, sink=2.5, veil=0.8, hem=1.0),
             grounded(Wd(hands=((-2.0, -4.0), (6.0, -3.0)), eye="dead", lean=55, sink=3.5, veil=0.6, hem=1.2)),
             widow_corpse(1.0)]
    knock = Wd(hands=((-5.0, -13.0), (4.2, -13.5)), wand=((3.6, -12.8), (6.6, -17.4)), eye="squint", lean=-9, veil=1.0, hem=0.6)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.09] * 6),
             ("Shard", shard, [0.14, 0.14, 0.06, 0.08, 0.12, 0.12, 0.12]),
             ("Crystals", crystals, [0.12, 0.14, 0.14, 0.12, 0.06, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("YsvVeilWitch", anims, outdir, scale=6)


def build_bride(outdir):
    K = 1.5
    B = lambda **kw: widow(k=K, bride=True, bouquet=True, **kw)
    REST = ((-3.2, -9.6), (3.6, -9.2))
    idle = [B(hands=REST, legs_ph=0.0, sway=0.0), B(hands=((-3.2, -9.4), (3.6, -9.0)), legs_ph=0.8, sway=0.4, veil=0.3, hem=0.3),
            B(hands=((-3.2, -9.2), (3.6, -8.8)), legs_ph=1.6, sway=0.6, veil=0.5, hem=0.5, eye="squint"),
            B(hands=REST, legs_ph=2.4, sway=0.3, veil=0.2, hem=0.2)]
    run = [B(lean=5, sway=-1.0 + 0.7 * math.sin(i * math.pi / 3), veil=1.0 + 0.4 * math.sin(i * math.pi / 3),
             hem=0.7 + 0.4 * math.cos(i * math.pi / 3), legs_ph=i * 1.0, legs_up=0.2, dy=-0.4 * abs(math.sin(i * math.pi / 3)),
             hands=((-4.0, -10.4), (3.4, -10.0))) for i in range(6)]
    def breath(n, r0):
        def fn(f, hand, tip, head):
            mx, my = head[0] + 3.6 * K, head[1] + 1.4 * K
            for j in range(n):
                a = math.radians(-20 + j * 40.0 / max(1, n - 1))
                for rr in range(r0, r0 + 6, 2):
                    f.g.put(*P(mx + rr * math.cos(a), my + rr * math.sin(a) + (j % 2)), "8" if rr == r0 else "7" if rr < r0 + 4 else "6")
        return fn
    breathe = [B(hands=((-3.4, -10.0), (2.8, -16.4)), veil_up=0.3, eye="open", legs_ph=0.4, legs_up=0.2),
               B(hands=((-3.8, -10.6), (1.2, -19.6)), veil_up=1.0, eye="wide", lean=-6, legs_up=0.5, mouth=0, veil=0.4),
               B(hands=((-4.0, -11.0), (1.0, -19.8)), veil_up=1.0, eye="wide", lean=-9, legs_up=0.6, mouth=1, veil=0.6, hem=0.3),
               B(hands=((-4.4, -11.6), (4.6, -11.4)), veil_up=1.0, eye="wide", lean=7, legs_up=0.4, mouth=2, veil=1.0, hem=0.6,
                 extra=breath(3, 2)),
               B(hands=((-4.4, -11.6), (4.6, -11.2)), veil_up=1.0, eye="wide", lean=8, legs_up=0.4, mouth=2, veil=1.1, hem=0.7,
                 extra=breath(4, 3)),
               B(hands=((-4.2, -11.2), (4.4, -11.0)), veil_up=1.0, eye="squint", lean=8, legs_up=0.3, mouth=2, veil=1.0, hem=0.6,
                 extra=breath(3, 4)),
               B(hands=((-3.6, -10.2), (2.6, -15.6)), veil_up=0.8, eye="open", lean=3, legs_up=0.2, mouth=1, veil=0.5),
               B(hands=REST, veil_up=0.0, veil=0.2)]
    def icicles(n, h):
        def fn(f, hand, tip, head):
            for j in range(n):
                x = head[0] - 10 + j * 5
                y = head[1] - 6 - h - (j % 2) * 2
                crystal(f.g, x, y, 90, 4, 0.8, ramp="5678")
        return fn
    def flash(f, hand, tip, head):
        for j in range(10):
            a = math.radians(j * 36)
            f.g.put(*P(head[0] + 6 * math.cos(a), head[1] - 3 + 5 * math.sin(a)), "H" if j % 2 else "G")
    requiem = [B(hands=((-4.0, -11.0), (4.0, -11.4)), legs_up=0.3, crown=1, eye="open", legs_ph=0.3),
               B(hands=((-5.0, -15.0), (5.0, -15.4)), legs_up=0.6, crown=1, eye="wide", lean=-3, veil=0.5, legs_ph=0.6),
               B(hands=((-4.4, -19.6), (4.4, -20.0)), legs_up=0.9, crown=2, eye="wide", lean=-5, veil=0.9, hem=0.4, legs_ph=0.9,
                 extra=icicles(3, 0)),
               B(hands=((-3.8, -21.0), (3.8, -21.4)), legs_up=1.0, crown=2, eye="wide", lean=-6, veil=1.1, hem=0.6, legs_ph=1.2,
                 extra=icicles(5, 1)),
               B(hands=((-3.6, -21.4), (3.6, -21.8)), legs_up=1.0, crown=2, eye="wide", lean=-6, veil=1.2, hem=0.7, legs_ph=1.5,
                 extra=icicles(5, 2)),
               B(hands=((-6.4, -8.0), (6.6, -8.4)), legs_up=0.7, crown=2, eye="wide", lean=4, veil=1.4, hem=1.0, legs_ph=1.8, extra=flash),
               B(hands=((-6.0, -8.6), (6.0, -9.0)), legs_up=0.5, crown=1, eye="squint", lean=3, veil=1.1, hem=0.8, legs_ph=2.1),
               B(hands=((-4.0, -9.4), (4.4, -9.4)), legs_up=0.2, eye="open", lean=1, veil=0.6, hem=0.4, legs_ph=2.4),
               B(hands=REST, veil=0.2)]
    death = [B(hands=((-5.0, -15.0), (4.6, -15.6)), eye="wide", lean=-10, veil=1.2, mouth=2, hem=0.8, legs_up=1.0, veil_up=1.0),
             B(hands=((-3.0, -7.0), (5.0, -6.0)), eye="shut", lean=16, sink=2.5, veil=0.8, hem=1.0, legs_up=0.3),
             grounded(B(hands=((-2.0, -4.0), (6.0, -3.0)), eye="dead", lean=55, sink=4.0, veil=0.6, hem=1.2)),
             widow_corpse(K, bride=True)]
    knock = B(hands=((-5.0, -13.0), (4.2, -13.5)), eye="squint", lean=-8, veil=1.0, hem=0.6, legs_up=0.7)
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.1] * 6),
             ("Breath", breathe, [0.14, 0.14, 0.14, 0.12, 0.12, 0.12, 0.14, 0.14]),
             ("Requiem", requiem, [0.12, 0.12, 0.14, 0.14, 0.12, 0.06, 0.18, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.12, 0.14, 0.18, 0.5], knock)
    sheet("YsvBride", anims, outdir, scale=4)


# ================================================================== WIDOW MATRON (T3, Weaver line)
def build_matron(outdir):
    S = 1.9
    def eggs(f, T, A, n=3, drop=None):
        # v0.8: a clutch of pearl egg sacs riding on the rear of her back (her silhouette; the Weaver carries none),
        # each with a faint glowing broodling curled inside
        arx_, ary_ = 3.8 * S * 1.18, 3.1 * S * 1.18
        spots = ((-150, 0.92, 3.3), (-122, 0.95, 3.5), (-176, 0.86, 2.9), (-100, 0.9, 2.8), (-136, 1.25, 2.6))
        for j, (t_, rr, r) in enumerate(spots[:n + 1]):
            a_ = math.radians(t_)
            ex_, ey_ = A[0] + arx_ * rr * math.cos(a_), A[1] + ary_ * rr * math.sin(a_)
            tmp = Canvas()
            ell(tmp, ex_, ey_, r, r * 0.9, "fgh8", bias=0.25)
            for (x_, y_), v_ in outl(Spr(tmp.px), "D").px.items(): f.b.put(x_, y_, v_)     # each sac its own violet rim
            f.b.put(*P(ex_ - 0.6, ey_ - 0.7), "8")
            f.g.put(*P(ex_ + 0.4, ey_ + 0.4), "I" if (j + n) % 2 else "G")
        if drop is not None:
            dx_, dy_ = drop
            ell(f.b, dx_, dy_, 2.4, 2.1, "fgh8", bias=0.2)
            f.g.put(*P(dx_ - 0.6, dy_ - 0.8), "H")
            line(f.n, A[0] - 3 * S, A[1] + 2.0 * S, dx_, dy_ - 2, "7")
    def mask(f, T, A):
        # v0.10 lineage (Silk Weaver only): the Weaver's frost-lace web spun over the front of the abdomen and a crown of
        # her rime crystals on the cephalothorax (the Rime Knight's helm and plate bands are gone)
        cx, cy = A
        for k_ in range(6):
            a_ = math.radians(-160 + k_ * 30)
            for r in (2.0, 3.6, 5.0):
                p_ = P(cx + r * math.cos(a_), cy + r * math.sin(a_) * 0.85)
                if f.b.px.get(p_) in ("B", "C", "D", "E"): f.b.put(*p_, "6" if r < 4 else "7")
        for k_ in range(14):
            a_ = math.radians(k_ * 26)
            p_ = P(cx + 3.8 * math.cos(a_), cy + 3.2 * math.sin(a_))
            if f.b.px.get(p_) in ("B", "C", "D", "E") and math.sin(a_) < 0.4: f.b.put(*p_, "5")
        for j_, (ox, a_, ln) in enumerate(((-0.6, -110, 2.6), (0.8, -88, 3.4), (2.0, -66, 2.4))):
            crystal(f.b, T[0] + ox * S * 0.6, T[1] - 1.2 * S, a_, ln, 0.7, lit=0.25)
    def M(extra=None, n_eggs=3, drop=None, **k):
        def ex(f, T, A):
            eggs(f, T, A, n_eggs, drop)
            mask(f, T, A)
            if extra: extra(f, T, A)
        return spider(S=S, weaver=True, matron=True, extra=ex, style="brood", **k)
    idle = [M(legs=0.0, amp=0.2), M(legs=0.6, amp=0.2, breathe=1, dy=0.3, crouch=0.15),
            M(legs=1.2, amp=0.2, breathe=1, dy=0.3, crouch=0.15, eye="squint"), M(legs=1.8, amp=0.2)]
    run = [M(legs=i * math.pi / 3, amp=0.9, dy=-0.5 * abs(math.sin(i * math.pi / 3)), tilt=2 * math.sin(i * math.pi / 3), breathe=i % 2)
           for i in range(6)]
    def stab_fx(n):
        def fn(f, T, A):
            x0 = T[0] + 10.5 * S
            for j in range(n):
                f.g.put(*P(x0 + (j % 3) - 1, -1 - j), "8" if j % 2 == 0 else "6")
            for j in range(-3, 4):
                f.g.put(*P(x0 + j * 1.5, 0), "7")
        return fn
    def smear(f, T, A):
        for j in range(6):
            a = math.radians(-80 + j * 18)
            f.n.put(*P(T[0] + 3 + 9 * math.cos(a), T[1] + 9 * math.sin(a)), "5" if j % 2 else "4")
    impale = [M(rear=0.4, crouch=0.3, fang=0.3, eye="open", dx=-0.4),
              M(rear=1.0, crouch=0.0, fang=0.8, eye="wide", dx=-1.2, tilt=-10, lift=0.8),
              M(rear=1.35, crouch=0.0, fang=1.0, eye="wide", dx=-1.8, tilt=-16, lift=1.6),
              M(rear=0.0, reach=3.0, crouch=0.6, fang=1.0, eye="wide", dx=0.6, tilt=6, extra=smear),
              M(rear=0.0, reach=4.2, crouch=1.0, fang=0.0, eye="squint", dx=1.6, tilt=12, extra=stab_fx(5)),
              M(rear=0.0, reach=3.6, crouch=0.9, fang=0.0, eye="squint", dx=1.4, tilt=10, extra=stab_fx(2)),
              M(rear=0.2, reach=1.5, crouch=0.4, legs=0.6, amp=0.3, dx=0.6, tilt=3),
              M(legs=1.0, amp=0.2)]
    brood = [M(crouch=0.3, breathe=1, eye="open"),
             M(crouch=0.6, abd_lift=-0.25, breathe=1, eye="squint", dx=0.4),
             M(crouch=0.8, abd_lift=-0.4, breathe=0, eye="squint", dx=0.6, n_eggs=4),
             M(crouch=0.9, abd_lift=-0.5, breathe=1, eye="wide", dx=0.8, n_eggs=4),
             M(crouch=1.0, abd_lift=-0.55, breathe=1, eye="wide", dx=1.0, n_eggs=4),
             M(crouch=0.7, abd_lift=-0.3, eye="wide", dx=1.2, n_eggs=2, drop=(-11.0, -2.6)),
             M(crouch=0.4, abd_lift=-0.1, eye="open", dx=0.8, n_eggs=2),
             M(crouch=0.1, eye="open", dx=0.2)]
    death = [M(dx=-0.6, rear=0.8, splay=0.8, fang=1, eye="wide", tilt=-14, lift=1.0),
             grounded(M(dx=-1, rear=1.0, splay=1.2, fang=1, eye="dead", tilt=-40, crouch=0.8)),
             grounded(recol(M(dx=-1, rear=1.0, splay=1.5, fang=0.5, eye="dead", tilt=-60, crouch=1.0), {"7": "6", "8": "7"})),
             spider_corpse(S, weaver=True)]
    knock = M(dx=-0.8, rear=0.5, splay=0.6, fang=0.6, eye="squint", tilt=-10, lift=0.6)
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.09] * 6),
             ("Impale", impale, [0.14, 0.14, 0.14, 0.05, 0.08, 0.14, 0.14, 0.14]),
             ("Brood", brood, [0.12, 0.14, 0.14, 0.14, 0.12, 0.08, 0.16, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.5], knock)
    sheet("YsvMatron", anims, outdir, scale=4)


# ================================================================== FX
def cv():
    return Canvas()


def fx_fixed(name, anims, outdir, cell, origin, scale=8):
    cw, ch = cell
    clipped = 0
    out = []
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
        keep = []
        for f in fr:
            f = Spr({(int(round(x)), int(round(y))): v for (x, y), v in f.px.items()})
            px = {k: v for k, v in f.px.items() if -origin[0] <= k[0] < cw - origin[0] and -origin[1] <= k[1] < ch - origin[1]}
            clipped += len(f.px) - len(px)
            keep.append(Spr(px))
        out.append((an, keep, du))
    if clipped: print("WARNING %s: %d px clipped" % (name, clipped))
    img, man = pack(name, out, cw, ch, origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in out], "img": img, "man": man}
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in out)))


def _extent(anims):
    anims = [(a, [Spr({(int(round(x)), int(round(y))): v for (x, y), v in f.px.items()}) for f in fr], d) for a, fr, d in anims]
    xs = [abs(x) for a in anims for f in a[1] for (x, y) in f.px] + [abs(x + 1) for a in anims for f in a[1] for (x, y) in f.px]
    ys_up = [-y for a in anims for f in a[1] for (x, y) in f.px]
    ys_dn = [y for a in anims for f in a[1] for (x, y) in f.px]
    return max(xs), max(ys_up), max(ys_dn)


def centered(name, anims, outdir, cell, scale=8):
    """Origin at the cell centre (the code anchors these MidCenter). The cell grows to fit, staying symmetric."""
    mx, mu, md = _extent(anims)
    cw = max(cell[0], 2 * mx + 2); ch = max(cell[1], 2 * max(mu, md) + 2)
    cw += cw % 2; ch += ch % 2
    fx_fixed(name, anims, outdir, (cw, ch), (cw // 2, ch // 2), scale)


def grounded_fx(name, anims, outdir, cell, scale=8):
    """Origin near the bottom centre: y = 0 is the floor row; `below` rows under it hold spill (outline, shadow).
    The code anchors these BotCenter with a sprite offset of -below px."""
    mx, mu, md = _extent(anims)
    md = max(0, md)
    cw = max(cell[0], 2 * mx + 2); ch = max(cell[1] - 1, mu) + 1 + md
    cw += cw % 2
    fx_fixed(name, anims, outdir, (cw, ch), (cw // 2, ch - 1 - md), scale)
    BUILT[name]["below"] = md


ICE_RX, ICE_RY = 15.0, 5.0


def ice_patch(spread=1.0, phase=0, fade=0.0):
    """Slick of black ice: midnight-blue sheet, pale cracked rim, a glint that slides across. Centred on (0,0)."""
    c = cv()
    rx, ry = ICE_RX * spread, max(1.2, ICE_RY * (0.4 + 0.6 * spread))
    lobes = [(0, 0, rx, ry), (-rx * 0.45, 0.6, rx * 0.5, ry * 0.8), (rx * 0.42, -0.5, rx * 0.55, ry * 0.85)]
    inside = {}
    for (lx, ly, ax, ay) in lobes:
        for y in range(int(ly - ay) - 1, int(ly + ay) + 2):
            for x in range(int(lx - ax) - 1, int(lx + ax) + 2):
                d = ((x - lx) / ax) ** 2 + ((y - ly) / ay) ** 2
                if d <= 1.0: inside[(x, y)] = min(inside.get((x, y), 9), d)
    for (x, y), d in inside.items():
        if fade and d > 1.0 - fade * 0.8: continue            # v0.10: fades by shrinking (no stipple noise)
        edge = any((x + a, y + b) not in inside for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge: ch = "7" if y < 0 else "5"
        else:
            ch = "3" if d > 0.55 else "4" if d > 0.2 else "5"
            if y < -ry * 0.3 and d > 0.3: ch = "5"
        c.put(x, y, ch)
    # cracks
    if fade < 0.6:
        for (x0, y0, x1, y1) in ((-6, -1, -2, 1), (-2, 1, 1, 0), (1, 0, 5, 2), (3, -2, 1, 0), (-9, 1, -6, -1)):
            for (x, y) in line_px(int(x0 * spread), y0, int(x1 * spread), y1):
                if (x, y) in c.px: c.put(x, y, "6" if (x + y) % 2 else "2")
        # sliding glint
        gx = int((-rx + 3) + (phase * 0.37 % 1.0) * (2 * rx - 6))
        for k, (a, b) in enumerate(((0, -1), (1, -1), (-1, 0), (0, 0))):
            if (gx + a, b) in c.px: c.put(gx + a, b, "8" if k < 2 else "7")
        for (x, y) in ((-int(rx * 0.6), -1), (int(rx * 0.5), 1)):
            if (x, y) in c.px and (phase % 2 == 0): c.put(x, y, "8")
    return c.spr()


def fx_ice():
    spread = [ice_patch(0.35), ice_patch(0.7, 1), ice_patch(0.95, 2)]
    idle = [ice_patch(1.0, i) for i in range(2)]
    fade = [ice_patch(0.98, 0, 0.3), ice_patch(0.9, 1, 0.55), ice_patch(0.8, 2, 0.8)]
    return spread, idle, fade


def fx_glob():
    out = []
    for i in range(4):
        c = cv()
        # trailing silk strands
        for k in range(3):
            line(c, -2, -1 + k, -5 - k - (i % 2), -2 + k * 2 + (i % 2), "6" if k != 1 else "7")
        ell(c, 0.5, 0, 2.8, 2.6, "45678", bias=0.35)
        c.put(-0.5 + (i % 2), -1, "8"); c.put(1, 1, "5")
        for k, (a, b) in enumerate(((2, -2), (3, 0), (2, 2))):
            if (k + i) % 2: c.put(a, b, "8")
        out.append(outl(c.spr(), "1"))
    return out


def fx_mote():
    out = []
    for i in range(4):
        c = cv()
        arm = 2 if i % 2 == 0 else 1
        c.put(0, 0, "H")
        for (a, b) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.put(a, b, "G")
        if arm == 2:
            for (a, b) in ((2, 0), (-2, 0), (0, 2), (0, -2)): c.put(a, b, "6")
        else:
            for (a, b) in ((1, 1), (-1, -1), (1, -1), (-1, 1)): c.put(a, b, "7")
        c.put(-3 - (i % 2), 0, "5")
        out.append(c.spr())
    return out


def fx_gust():
    """v0.10: three clean crescents of driven frost (solid arcs, no scattered dots) and two wind streaks behind."""
    out = []
    for i in range(4):
        c = cv()
        for k, (r, half, ch) in enumerate(((7.0, 50, "5"), (8.8, 58, "6"), (10.6, 64, "8"))):
            pts = []
            for j in range(-half, half + 1, 6):
                a = math.radians(j + (i % 2) * 4)
                pts.append((-6 + r * math.cos(a) + (i % 2) * 0.5, r * math.sin(a) * 1.1))
            polyline(c, pts, ch)
            if k == 2: polyline(c, [(x - 1, y) for (x, y) in pts[2:-2]], "7")
        for k in range(2):
            y = -4 + k * 7 + (i % 2)
            line(c, -10 - k * 2 - (i % 2), y, -6 - k * 2, y + 1, "4")
        out.append(c.spr())
    return out


def fx_shard():
    out = []
    for i in range(4):
        c = cv()
        for k in range(4):
            c.put(-4 - k * 1.5 - (i % 2), ((k + i) % 3) - 1, "6" if k < 2 else "4")
        crystal(c, -3, 0, 0, 8, 1.4, lit=0.2)
        c.put(4, 0, "8"); c.put(5, 0, "H" if i % 2 else "G")
        out.append(outl(c.spr(), "1"))
    return out


def icicle_fall(i, n=8):
    """Telegraph: a shadow ring on the floor tightens while the icicle drops out of the dark above."""
    c = cv()
    t = i / (n - 1.0)
    r = 8 - t * 3.5
    for k in range(28):
        a = 2 * math.pi * k / 28
        if (k + i) % 3 == 0: continue
        c.put(*P(r * math.cos(a), -2 + r * 0.38 * math.sin(a)), "3" if t < 0.6 else "5")
    ell(c, 0, -2, 4.5 * (0.5 + t * 0.5), 1.6 * (0.5 + t * 0.5), "011", bias=0.0)
    if i >= 2:
        h = 44 - (i - 2) ** 1.6 * 7.0
        tipy = -2 - max(0, h)
        tip = (0, tipy)
        base = (0, tipy - 11)
        poly(c, [(-2.4, base[1]), (2.4, base[1]), tip], "6",
             shade=lambda x, y: "8" if x < -0.5 else "6" if x < 1 else "4")
        line(c, -1, base[1], -0.4, tipy - 2, "8")
        for k in range(3): c.put(*P(-1 + k, base[1] - 1), "7")
        if i >= 5:
            for k in range(3): c.put(*P(-3 + k * 3, tipy - 6 - k * 3), "7")
    return c.spr()


def icicle_shatter(i):
    c = cv()
    h = [10, 7, 4, 2, 1][i]
    w = [3, 6, 9, 11, 12][i]
    rnd = random.Random(5)
    for k in range(12):
        a = rnd.uniform(-math.pi, 0)
        sp = rnd.uniform(0.5, 1.0)
        t = (i + 1) / 5.0
        x, y = math.cos(a) * w * sp * 1.3, -2 + math.sin(a) * (h + 3) * sp * (1.3 - t)
        crystal(c, x, min(-1, y), math.degrees(a), 2.5 * (1 - t * 0.5), 0.6) if k % 3 == 0 and i < 3 else \
            c.put(*P(x, min(-1, y)), "8" if k % 2 else "7")
    for x in range(-w, w + 1):
        if (x + i) % 2 == 0: c.put(x, 0 if abs(x) > 2 else -1, "6")
    if i < 2:
        ell(c, 0, -3, 3 + i, 3 + i, "678H", bias=0.4)
    return c.spr()


def fx_thread():
    fly = []
    for i in range(4):
        c = cv()
        for k in range(10):
            c.put(-2 - k, (1 if (k + i) % 4 == 0 else 0), "7" if k % 2 else "8")
        ell(c, 1, 0, 2.2, 1.8, "5678", bias=0.4)
        rot = i * 45
        for k in range(4):
            a = math.radians(rot + k * 90)
            c.put(*P(1 + 2.6 * math.cos(a), 2.2 * math.sin(a)), "8")
        fly.append(c.spr())
    bead = [Spr({(0, 0): "8", (-1, 0): "7", (1, 0): "7"}), Spr({(0, 0): "7", (-1, 0): "8", (1, 0): "6"})]
    snap = [Spr({(-2, -1): "8", (2, 1): "8", (0, 0): "7", (-3, 0): "6", (3, 0): "6"}),
            Spr({(-4, -2): "7", (4, 2): "7", (-2, 1): "6", (2, -1): "6"}),
            Spr({(-5, -2): "5", (5, 3): "5"})]
    return fly, bead, snap


def crystal_grow(i):
    c = cv()
    t = min(1.0, (i + 1) / 5.0)
    for x in range(-6, 7):
        if (x + i) % 2 == 0: c.put(x, 0, "4")
    specs = ((0, -90, 14, 2.4), (-3, -112, 9, 1.7), (3, -66, 10, 1.8), (-5, -140, 5, 1.2), (5, -40, 6, 1.3))
    for (bx, a, ln, wd) in specs:
        crystal(c, bx, 0, a, max(1.5, ln * t), wd, lit=0.1 * i)
    if i >= 3:
        for k in range(i - 2):
            c.put(*P(-1 + (k % 2), -4 - k * 2.5), "G" if k % 2 else "H")
    if i >= 5:
        for (x, y) in ((0, -6), (1, -8), (-1, -9), (0, -11)): c.put(x, y, "2")
    spr = outl(c.spr(), "1")
    if i >= 4:
        spr = merge(spr, Spr({(0, -15 - (i % 2)): "H", (-1, -14): "G", (1, -14): "G"}))
    return spr


def crystal_shatter(i):
    c = cv()
    rnd = random.Random(9)
    t = (i + 1) / 5.0
    for k in range(14):
        a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
        r = (4 + 10 * t) * rnd.uniform(0.6, 1.0)
        x, y = r * math.cos(a), -5 + r * math.sin(a) * 0.8 + t * t * 6
        y = min(-1, y)
        if i < 3 and k % 3 == 0: crystal(c, x, y, math.degrees(a), 3.0, 0.7)
        else: c.put(*P(x, y), "8" if k % 2 else "6")
    if i < 2: ell(c, 0, -6, 4 + i * 2, 4 + i * 2, "678H", bias=0.5)
    for x in range(-4 - i * 2, 5 + i * 2):
        if (x + i) % 3: c.put(x, 0, "5")
    return c.spr()


def egg_hatch(i):
    c = cv()
    wob = [0, -1, 1, -1, 0, 0, 0, 0][i]
    if i < 5:
        sq = [0, 0.2, -0.2, 0.3, 0.5][i]
        ell(c, wob * 0.6, -4.5 + sq, 4.2 + sq, 4.4 - sq, "fgh8", bias=0.25)
        for k in range(3):   # silk wrapping, only over the sac
            for (x, y) in line_px(-5 + k * 3 + wob, -8, -2 + k * 3 + wob, -1):
                if (x, y) in c.px: c.put(x, y, "g")
        if i >= 3:
            for (x, y) in ((0, -8), (1, -7), (0, -6), (1, -5), (2, -4))[:i]: c.put(x + wob, y, "1")
            c.put(1 + wob, -6, "G")
        spr = outl(c.spr(), "1")
        return spr
    # burst: silk shreds fly, frost puff
    t = (i - 4) / 3.0
    rnd = random.Random(11)
    for k in range(14):
        a = rnd.uniform(-math.pi, 0)
        r = 3 + 9 * t * rnd.uniform(0.6, 1.0)
        x, y = r * math.cos(a), -4 + r * math.sin(a) * 0.9 + t * t * 4
        c.put(*P(x, min(-1, y)), "8" if k % 3 == 0 else "g" if k % 3 == 1 else "7")
    for x in range(-5 + (i - 5), 6 - (i - 5)):
        c.put(x, 0, "g" if abs(x) > 1 else "h")
    if i == 5: ell(c, 0, -4, 4, 3.5, "678H", bias=0.4)
    return c.spr()


def breath_puff(i):
    c = cv()
    t = i / 5.0
    r = 3 + t * 6
    for (ox, oy, rr) in ((0, 0, 1.0), (-r * 0.5, r * 0.15, 0.7), (r * 0.45, -r * 0.2, 0.75)):
        R = r * rr
        for y in range(int(-R) - 1, int(R) + 2):
            for x in range(int(-R * 1.2) - 1, int(R * 1.2) + 2):
                d = (x / (R * 1.2)) ** 2 + (y / (R * 0.85)) ** 2
                if d > 1: continue
                X, Y = P(ox + x, oy + y)
                if t > 0.5 and d < (t - 0.45) * 1.4: continue          # v0.10: thins from the middle out (no stipple)
                ch = "8" if d < 0.25 and t < 0.6 else "7" if d < 0.6 else "6" if d < 0.85 else "5"
                c.put(X, Y, ch, over=False)
    for k in range(4):
        a = math.radians(k * 90 + i * 25)
        c.put(*P((r + 1.5) * math.cos(a), (r + 1) * 0.7 * math.sin(a)), "H" if t < 0.5 else "6")
    return c.spr()


def fx_pips():
    """Rime pips over the hero's head: 1-3 snowflakes."""
    def flake(c, x, y, ph):
        c.put(x, y, "H")
        for (a, b) in ((1, 0), (-1, 0), (0, 1), (0, -1)): c.put(x + a, y + b, "G" if ph else "7")
        for (a, b) in ((1, 1), (-1, -1), (1, -1), (-1, 1)): c.put(x + a, y + b, "4" if ph else "5")
    anims = []
    for n, name in ((1, "One"), (2, "Two"), (3, "Three")):
        frs = []
        for ph in range(2):
            c = cv()
            xs = {1: [0], 2: [-2, 2], 3: [-4, 0, 4]}[n]
            for j, x in enumerate(xs):
                flake(c, x, -1 - ((j + ph) % 2), (j + ph) % 2)
            frs.append(outl(c.spr(), "1"))
        anims.append((name, frs, [0.25, 0.25]))
    return anims


def bind_frame(i):
    """Rimebound: an ice-and-silk cocoon snaps shut around the hero's legs, holds, then cracks apart."""
    c = cv()
    h = [4, 9, 13, 14, 14, 14, 10][i]
    if i <= 5:
        for x in range(-6, 7):
            top = -h + int(abs(x) * 0.6)
            for y in range(top, 1):
                if abs(x) >= 4 or y < top + 2 or (x + y) % 4 == 0:
                    c.put(x, y, "7" if x < 0 else "5" if x > 2 else "6")
        for k in range(4):      # silk bands
            y = -2 - k * 3
            if -h < y: line(c, -6, y, 6, y - 1, "8")
        if i in (2, 3): ell(c, -2, -h + 3, 1.2, 1.2, "8H", bias=0.5)
        if i == 5:
            for (x, y) in ((-1, -12), (0, -10), (-1, -8), (1, -6), (0, -4)): c.put(x, y, "1")
        return outl(c.spr(), "1")
    rnd = random.Random(3)
    for k in range(16):
        a = rnd.uniform(-math.pi, 0)
        r = rnd.uniform(5, 12)
        c.put(*P(r * math.cos(a), -6 + r * math.sin(a) * 0.8), "8" if k % 2 else "6")
    return c.spr()


def nova_frame(i):
    c = cv()
    r = [5, 10, 15, 19, 22, 24][i]
    ry = r * 0.42
    n = int(r * 6) + 8
    for k in range(n):
        a = 2 * math.pi * k / n
        if i >= 4 and (k // 2) % 3 == 0: continue
        c.put(*P(r * math.cos(a), ry * math.sin(a)), "8" if i < 3 else "6")
        c.put(*P(r * 0.85 * math.cos(a), ry * 0.85 * math.sin(a)), "6" if i < 3 else "4", over=False)
    for k in range(8):          # silk spokes
        a = 2 * math.pi * k / 8 + 0.2
        if i < 5:
            for t in (0.3, 0.55, 0.8):
                c.put(*P(r * t * math.cos(a), ry * t * math.sin(a)), "7")
    if i < 2: ell(c, 0, 0, 3 + i * 2, 2 + i, "678H", bias=0.4)
    return c.spr()


def puff_frame(i):
    c = cv()
    rnd = random.Random(4)
    r = [2, 4, 5.5, 6.5][i]
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        c.put(*P(r * math.cos(a), r * 0.8 * math.sin(a)), "8" if i < 2 else "6")
    if i == 0: ell(c, 0, 0, 2, 2, "78H", bias=0.4)
    return c.spr()


def build_fx(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxYsvIce"):
        sp, idl, fd = fx_ice()
        life = sp + idl * 7 + fd
        centered("FxYsvIce", [("Life", life, [0.1] * 3 + [0.38] * 14 + [0.2] * 3),
                              ("Spread", sp, [0.1] * 3), ("Idle", idl, [0.38, 0.38]), ("Fade", fd, [0.2] * 3)], outdir, (36, 14), scale=6)
    if want("FxYsvGlob"): centered("FxYsvGlob", [("Fly", fx_glob(), [0.07] * 4)], outdir, (16, 10))
    if want("FxYsvMote"): centered("FxYsvMote", [("Fly", fx_mote(), [0.05] * 4)], outdir, (10, 8))
    if want("FxYsvGust"): centered("FxYsvGust", [("Fly", fx_gust(), [0.06] * 4)], outdir, (28, 26), scale=6)
    if want("FxYsvShard"): centered("FxYsvShard", [("Fly", fx_shard(), [0.05] * 4)], outdir, (20, 7))
    if want("FxYsvIcicle"):
        grounded_fx("FxYsvIcicle", [("Fall", [icicle_fall(i) for i in range(8)], [0.12, 0.1, 0.1, 0.1, 0.08, 0.08, 0.06, 0.06]),
                                    ("Shatter", [icicle_shatter(i) for i in range(5)], [0.05, 0.06, 0.07, 0.08, 0.1])],
                    outdir, (28, 60), scale=5)
    if want("FxYsvThread"):
        fly, bead, snap = fx_thread()
        centered("FxYsvThread", [("Fly", fly, [0.05] * 4), ("Bead", bead, [0.12, 0.12]), ("Snap", snap, [0.06, 0.08, 0.1])],
                 outdir, (26, 8))
    if want("FxYsvCrystal"):
        grounded_fx("FxYsvCrystal", [("Grow", [crystal_grow(i) for i in range(7)], [0.12, 0.12, 0.14, 0.14, 0.16, 0.16, 0.16]),
                                     ("Shatter", [crystal_shatter(i) for i in range(5)], [0.05, 0.06, 0.07, 0.08, 0.1])],
                    outdir, (36, 26), scale=6)
    if want("FxYsvEgg"):
        grounded_fx("FxYsvEgg", [("Hatch", [egg_hatch(i) for i in range(8)], [0.16, 0.14, 0.14, 0.14, 0.12, 0.06, 0.1, 0.12])],
                    outdir, (28, 20), scale=6)
    if want("FxYsvBreath"): centered("FxYsvBreath", [("Puff", [breath_puff(i) for i in range(6)], [0.07, 0.08, 0.09, 0.1, 0.12, 0.14])],
                                     outdir, (26, 20), scale=6)
    if want("FxYsvPips"): centered("FxYsvPips", fx_pips(), outdir, (15, 7), scale=10)
    if want("FxYsvBind"): grounded_fx("FxYsvBind", [("Bind", [bind_frame(i) for i in range(7)], [0.05, 0.05, 0.06, 0.2, 0.2, 0.14, 0.12])],
                                      outdir, (28, 24), scale=6)
    if want("FxYsvNova"): centered("FxYsvNova", [("Play", [nova_frame(i) for i in range(6)], [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])],
                                   outdir, (52, 24), scale=5)
    if want("FxYsvPuff"): centered("FxYsvPuff", [("Play", [puff_frame(i) for i in range(4)], [0.04, 0.05, 0.06, 0.08])],
                                   outdir, (16, 14))


# ================================================================== ICONS + GOD PORTRAIT
def icon_frame(c):
    sp = Spr({k: v for k, v in c.px.items() if -7 <= k[0] <= 6 and -14 <= k[1] <= -1})
    return outl(sp, "0")


def icon_requiem(ph):
    """Spell: a ring of icicles stabbing down around a glowing frost sigil."""
    c = cv()
    for k in range(20):
        a = 2 * math.pi * k / 20
        c.put(*P(5.6 * math.cos(a), -3.2 + 2.0 * math.sin(a)), "4" if math.sin(a) < 0 else "5")
    ell(c, 0, -3.2, 2.2, 1.0, "IGH", bias=0.3)
    for j, (x, top, ln) in enumerate(((-5, -13, 8), (-1.5, -14, 9), (2.5, -14, 8), (5, -12, 7))):
        drop = (1 if (j + ph) % 2 else 0)
        poly(c, [(x - 1.2, top + drop), (x + 1.2, top + drop), (x, top + ln + drop)], "6",
             shade=lambda X, Y, x=x: "8" if X < x else "6" if X < x + 1 else "4")
    if ph: c.put(0, -4, "H"); c.put(-6, -2, "8"); c.put(6, -4, "8")
    return icon_frame(c)


def icon_shawl(ph):
    """Artifact: a black widow-silk shawl of frost lace pinned by an ice-crystal brooch."""
    c = cv()
    poly(c, [(-7, -12), (6, -12), (5, -9), (0, -2), (-6, -9)], "C",
         shade=lambda x, y: pick("ABCDE", 0.4 - (x + 7) * 0.05 + (y + 12) * -0.02))
    # lace: web rings
    for r in (2.5, 5.0):
        for k in range(14):
            a = math.pi * k / 13
            x, y = -0.5 + r * math.cos(a), -11.5 + r * math.sin(a) * 1.3
            if (P(x, y)) in c.px: c.put(*P(x, y), "6" if r < 3 else "5")
    for a in (35, 65, 90, 115, 145):
        for t in range(1, 9):
            x, y = -0.5 + t * math.cos(math.radians(a)), -11.5 + t * 1.2 * math.sin(math.radians(a))
            if P(x, y) in c.px and t % 2 == 0: c.put(*P(x, y), "4")
    # fringe
    for k in range(6):
        c.put(-6 + k, -9 + k, "7" if (k + ph) % 2 else "5")
        c.put(5 - k, -9 + k, "7" if (k + ph + 1) % 2 else "5")
    # brooch
    crystal(c, -0.5, -9.5, -90, 4, 1.2, lit=0.2)
    c.put(-1, -11, "H" if ph else "G")
    return icon_frame(c)


def deity_portrait(ph):
    c = cv()
    # midnight gradient with falling snow
    for y in range(-23, 1):
        for x in range(-14, 15):
            d = (y + 23) / 23.0 + 0.1 * abs(x) / 14.0
            ch = "2" if d < 0.3 else ("1" if d < 0.75 else "0")
            if 0.26 < d < 0.36 and (x + y) % 2 == 0: ch = "1"
            if 0.7 < d < 0.8 and (x + y) % 2 == 0: ch = "0"
            c.put(x, y, ch)
    # web strands across the top corners
    for (x0, y0, x1, y1) in ((-14, -18, -6, -23), (-14, -12, -9, -23), (14, -17, 7, -23), (14, -11, 10, -23)):
        for i, (x, y) in enumerate(line_px(x0, y0, x1, y1)):
            if i % 2 == 0: c.put(x, y, "3")
    # veil falling to both sides (black silk with violet sheen)
    for y in range(-19, 1):
        w = 6 + (y + 19) * 0.45
        for x in range(int(-w), int(w) + 1):
            if abs(x) < 4.2 and y < -6: continue
            l = 0.3 - abs(x) / w * 0.6 + (0.3 if (x * 3 + y) % 7 == 0 else 0)
            c.put(x, y, pick("ABCDE", l))
    # face
    ell(c, 0, -11, 4.0, 5.0, "fgh", bias=0.25)
    for (x, y) in ((-2, -15), (2, -15), (-3, -13), (3, -13)): c.put(x, y, "g")
    # lace over the brow
    for x in range(-4, 5):
        if (x + ph) % 2 == 0: c.put(x, -14, "7")
    # eyes + frozen tears
    for sx in (-2, 2):
        c.put(sx, -12, "0"); c.put(sx + (1 if sx < 0 else -1), -12, "0")
        c.put(sx, -12, "H" if ph == 2 else "G")
        c.put(sx, -11, "I")
    c.put(-2, -9 + (ph % 2), "6"); c.put(2, -8, "6")
    c.put(0, -7, "D"); c.put(-1, -7, "C"); c.put(1, -7, "C")     # violet lips
    # crown of icicles
    for i, (x, h) in enumerate(((-5, 3), (-3, 5), (-1, 6), (1, 6), (3, 5), (5, 3))):
        crystal(c, x, -15.5, -90 + x * 6, h, 0.8, ramp="4567")
        c.put(*P(x + x * 0.1, -16 - h), "H" if (i + ph) % 3 == 0 else "8")
    # the hourglass brooch at the throat
    hourglass(c, 0, -3, s=2, bright=True)
    # snow
    for k, (x, y) in enumerate(((-11, -20), (9, -16), (-8, -9), (11, -5), (-12, -2), (7, -21))):
        yy = y + ph * 2 + (k % 2)
        if yy > 0: yy -= 22
        if c.px.get((x, yy)) in ("0", "1", "2", "3"): c.put(x, yy, "8" if k % 2 else "7")
    return Spr({k: v for k, v in c.px.items() if -14 <= k[0] <= 14 and -23 <= k[1] <= 0})


def bubble_and_hud(name, frames16, kind, outdir):
    """Shop bubble (34x41) + HUD icon (11x7), like tools/sprites/item_icons.py: spells on the parchment card."""
    from PIL import Image
    cells = []
    for f in frames16:
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0)); p = img.load()
        for (x, y), rgba in f.to_rgba().items():
            if 0 <= x + 8 < 16 and 0 <= y + 15 < 16: p[x + 8, y + 15] = rgba
        cells.append(img)
    if kind == "spell":
        import item_icons
        card = item_icons.blank_card()
    bubbles = []
    for ic in cells:
        b = card.copy() if kind == "spell" else Image.new("RGBA", (34, 41), (0, 0, 0, 0))
        bb = card.getbbox() if kind == "spell" else (0, 0, 34, 41)
        cx = (bb[0] + bb[2]) // 2 - 8
        cy = (bb[1] + bb[3]) // 2 - 8 if kind == "spell" else 41 - 16 - 6
        b.alpha_composite(ic, (cx, cy))
        bubbles.append(b)
    crop = cells[0].crop(cells[0].getbbox())
    s = min(11 / crop.width, 7 / crop.height)
    small = crop.resize((max(1, round(crop.width * s)), max(1, round(crop.height * s))), Image.NEAREST)
    hud = Image.new("RGBA", (11, 7), (0, 0, 0, 0))
    hud.alpha_composite(small, ((11 - small.width) // 2, (7 - small.height) // 2))
    import json
    def save(n, frames, w, h, anim):
        img = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
        for i, f in enumerate(frames): img.alpha_composite(f, (i * w, 0))
        img.save(os.path.join(outdir, n + ".png"))
        json.dump({"cellW": w, "cellH": h, "cols": len(frames),
                   "anims": [{"name": anim, "frames": list(range(len(frames))), "durations": [0.5] * len(frames)}]},
                  open(os.path.join(outdir, n + ".json"), "w"))
    save(name + "Bubble", bubbles, 34, 41, "Bubble")
    save(name + "Hud", [hud], 11, 7, "Hud")
    BUILT[name + "Bubble"] = {"cell": (34, 41), "feet": (17, 40), "anims": [("Bubble", len(bubbles), [0.5] * len(bubbles))]}
    BUILT[name + "Hud"] = {"cell": (11, 7), "feet": (5, 6), "anims": [("Hud", 1, [0.5])]}


def build_icons(outdir):
    for name, fn, kind in (("IconYsvRequiem", icon_requiem, "spell"), ("IconYsvShawl", icon_shawl, "artifact")):
        frames = [fn(0), fn(1)]
        img, man = pack(name, [("Idle", frames, [0.5, 0.5])], 16, 16, (8, 15), outdir)
        preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=10)
        BUILT[name] = {"cell": (16, 16), "feet": (8, 15), "anims": [("Idle", 2, [0.5, 0.5])], "img": img, "man": man}
        bubble_and_hud(name, frames, kind, outdir)
        print("built", name, "+ Bubble + Hud")
    frames = [deity_portrait(i) for i in range(4)]
    img, man = pack("DeityYsveld", [("Idle", frames, [0.3, 0.25, 0.3, 0.25])], 29, 24, (14, 23), outdir)
    preview(img, man, os.path.join(outdir, "DeityYsveld_preview.png"), scale=10)
    BUILT["DeityYsveld"] = {"cell": (29, 24), "feet": (14, 23), "anims": [("Idle", 4, [0.3, 0.25, 0.3, 0.25])], "img": img, "man": man}
    crop = img.crop((0, 0, 29 * 4, 24)).load()
    assert all(crop[x, y][3] == 255 for x in range(29 * 4) for y in range(24)), "portrait must be opaque"
    print("built DeityYsveld (opaque)")


# ================================================================== SILKMOTH (T2, flying; Rimeling / Hoarmoth line)
# A night moth of the widow's court, seen from the side: black silk wings with frost-lace rings and an ice eyespot,
# frost-white fur collar, banded abdomen, and two long silk streamers trailing from the hindwings.
def silk_wing(c, S, f, R, hind=False, far=False, lace=True, ph=0):
    """Side-view wing rooted at S (broad, swept back). f = 1 raised, 0 edge-on, -1 driven down.
    Returns (eyespot, tail root)."""
    if hind:
        shape = [(0.1, 0.0), (-0.15, -0.6), (-0.65, -0.85), (-1.05, -0.55), (-1.0, -0.1), (-0.55, 0.1)]
    else:
        shape = [(0.2, 0.0), (0.15, -0.55), (-0.15, -1.0), (-0.45, -0.95), (-0.85, -0.45), (-0.95, -0.2), (-0.45, 0.05)]
    pts = [(S[0] + x * R, S[1] + y * R * f) for x, y in shape]
    if abs(f) < 0.18:   # edge-on: a thin dark blade
        line(c, S[0] - R * 0.9, S[1] - 0.6, S[0] + R * 0.15, S[1] - 0.4, "C" if not far else "1")
        return None, None
    def shade(x, y):
        dx_, dy_ = (x - S[0]) / R, (y - S[1]) / (R * abs(f))
        r = math.hypot(dx_, dy_)
        if far: return pick("112", 0.3 - r * 0.6)
        lead = -dx_ - dy_ * 0.2            # near the leading edge -> sheen
        # v0.9: the outer half of the wing is the Hoarmoth's pale frost, the root the widow's violet silk
        ch = pick("CDE556", 0.55 - r * 0.2 + (0.25 if dx_ > -0.25 else 0)) if r > 0.55 else pick("BCCDE", 0.65 - r * 0.9 + (0.35 if dx_ > -0.25 else 0))
        if lace and abs(r - 0.6) < 0.06 and (x + y + ph) % 2 == 0: return "5"
        if lace and abs(r - 0.88) < 0.05 and (x + y + ph) % 2 == 0: return "4"
        return ch
    poly(c, pts, "C", shade=shade)
    if not far:
        n0, n1 = (2, 6) if not hind else (2, 5)
        for i in range(n0, n1):
            line(c, *pts[i], *pts[i + 1], "6" if i % 2 else "7")
        line(c, *pts[0], *pts[2], "E")          # violet sheen on the leading edge
    eye = (S[0] - (0.45 if not hind else 0.6) * R, S[1] - (0.55 if not hind else 0.45) * R * f)
    tail = pts[3] if hind else None
    return eye, tail


def silkmoth(dx=0.0, dy=0.0, f=1.0, tilt=0.0, ant=0.0, eye="open", tails=0.0, legs=0.0, extra=None, hover=10.0, ph=0,
             glow=0, ground=False):
    f_ = Fr()
    cx, cy = dx, -hover + dy
    if ground: cy = -3.0 + dy
    def L(x, y): return rot_about((cx + x, cy + y), (cx, cy), tilt)
    R, RH = 10.5, 6.5
    # far wings (shadow, behind everything)
    silk_wing(f_.n, L(-1.5, -1.6), f * 0.92 + 0.08, R * 0.95, far=True)
    silk_wing(f_.n, L(-2.8, -0.6), f * 0.85 + 0.1, RH * 0.95, hind=True, far=True)
    # silk streamers from the hindwing (behind the body)
    _, troot = silk_wing(Canvas(), L(-2.2, -0.2), f, RH, hind=True)
    if troot is None: troot = L(-6.5, 0.0)
    pts = [troot]
    x, y = troot
    for k in range(9):
        a = math.radians(105 + 18 * math.sin(k * 0.7 + tails) + tilt * 0.5)
        x += math.cos(a) * 1.25 - 0.35; y += math.sin(a) * 1.25
        pts.append((x, y))
    for k, (px_, py_) in enumerate(pts[1:]):
        f_.u.put(*P(px_, py_), "8" if k % 3 == 0 else "6" if k % 3 == 1 else "7")
    f_.u.put(*P(*pts[-1]), "G" if glow else "7")
    # abdomen: black silk, frost bands
    ab = L(-4.4, 1.0)
    ell(f_.b, ab[0], ab[1], 4.2, 2.2, "ABCD", ang=tilt + 14, bias=0.05,
        shader=lambda nu, nv, d, l, ch, x, y: ("5" if abs(nu * 4.2 % 2.0 - 1.0) < 0.22 and d < 0.8 else ch))
    for k in range(4):     # v0.10: the Hoarmoth's frost-fur tufts along the abdomen (was a Rimeling crystal)
        f_.b.put(*P(*L(-7.0 + k * 1.6, -0.8 - (k % 2))), "h")
    # v0.9 lineage (Rimeling): long jointed ice spider legs hanging under the moth, frost-tipped, plus a rime crystal
    # on the abdomen; the Hoarmoth side is the white fur ruff and the pale frost wings
    for k, (rx_, kx_, ky_, fx_, fy_) in enumerate(((-1.0, -2.6, 2.2, -3.4, 4.2), (0.2, -0.4, 2.8, -0.6, 4.6),
                                                   (1.2, 2.2, 2.6, 2.6, 4.4))):   # v0.10: short furred moth legs
        sw = 0.5 * math.sin(legs * 2.0 + k * 1.3)
        r0, kn, ft = L(rx_, 1.6), L(kx_ + sw * 0.4, ky_), L(fx_ + sw, fy_ - abs(sw) * 0.4)
        lay = f_.u if k % 2 else f_.b
        line(lay, r0[0], r0[1], kn[0], kn[1], "g" if k % 2 == 0 else "f")
        line(lay, kn[0], kn[1], ft[0], ft[1], "6" if k % 2 == 0 else "5")
        lay.put(*P(*kn), "7")
        f_.g.put(*P(*ft), "8")
    # thorax: frost-white fur collar
    th = L(0.2, -0.2)
    ell(f_.b, th[0], th[1], 2.8, 2.6, "fgh8", ang=tilt, bias=0.2,
        shader=lambda nu, nv, d, l, ch, x, y: ("g" if d > 0.7 and (x + y) % 2 else ch))
    hd = L(3.2, -0.6)
    ell(f_.b, hd[0], hd[1], 1.7, 1.6, "BCDE", ang=tilt, bias=0.15)
    # feathered antennae, sweeping forward and up
    for k, (a0, ln, col) in enumerate(((-58 + ant * 12, 5, "5"), (-34 + ant * 10, 4, "3"))):
        base = L(3.6, -1.8)
        x, y = base
        a = a0 + tilt
        pts = [(x, y)]
        for j in range(ln):
            a += 7
            x += math.cos(math.radians(a)); y += math.sin(math.radians(a))
            pts.append((x, y))
        lay = f_.b if k == 0 else f_.u
        polyline(lay, pts, col)
        for j in range(1, len(pts) - 1):
            if j % 2: lay.put(*P(pts[j][0] - 1, pts[j][1]), "4" if k == 0 else "2", over=False)
    # near wings over the body
    eye_h, _ = silk_wing(f_.b, L(-2.2, -0.2), f, RH, hind=True, ph=ph)
    eye_f, _ = silk_wing(f_.b, L(-0.8, -1.4), f, R, ph=ph)
    for e_, big in ((eye_f, True), (eye_h, False)):
        if e_ is None: continue
        ex_, ey_ = P(*e_)
        f_.g.put(ex_, ey_, "H" if glow else "G")
        if big:
            for (a_, b_) in ((1, 0), (-1, 0), (0, 1), (0, -1)): f_.g.put(ex_ + a_, ey_ + b_, "I" if glow else "4")
    # eye
    ex, ey = P(*L(4.0, -1.0))
    if eye == "open": f_.g.put(ex, ey, "G")
    elif eye == "wide": f_.g.put(ex, ey, "H"); f_.g.put(ex, ey - 1, "G")
    elif eye == "squint": f_.g.put(ex, ey, "I")
    else: f_.g.put(ex, ey, "2")
    if extra: extra(f_, (cx, cy), hd)
    return f_.done()


def silkmoth_corpse():
    s = silkmoth(ground=True, f=-0.35, eye="dead", tilt=8, tails=2.0)
    return grounded(recol(s, {"G": "4", "H": "5", "I": "3"}))


def build_silkmoth(outdir):
    M = silkmoth
    idle = [M(f=1.0, tails=0.0), M(f=0.75, dy=0.5, tails=0.6, ant=0.3, ph=1), M(f=0.45, dy=1.0, tails=1.2, ant=0.5, legs=1),
            M(f=0.8, dy=0.5, tails=1.8, ant=0.3, eye="squint", ph=1)]
    run = [M(f=[1.0, 0.45, -0.3, -0.85, -0.3, 0.5][i], tilt=10, dx=0.5, dy=[0, 0.5, 1.0, 1.3, 0.7, 0.2][i], tails=i * 0.8,
             ant=-0.6, legs=1, ph=i % 2) for i in range(6)]
    def needles(n):
        def fn(f, C, hd):
            for k in range(n):
                y = hd[1] - 1 + (k - (n - 1) / 2.0) * 2.2
                line(f.g, hd[0] + 3, y, hd[0] + 6 + (k % 2), y - (k - 1) * 0.6, "8" if k % 2 == 0 else "7")
        return fn
    volley = [M(f=1.0, tilt=-6, dx=-0.4, ant=0.5, eye="wide"),
              M(f=1.15, tilt=-12, dx=-1.0, dy=-0.5, ant=0.8, eye="wide", tails=0.6, glow=1),
              M(f=0.1, tilt=-2, dx=0.0, ant=0.2, eye="wide", tails=1.2, glow=1),
              M(f=-0.9, tilt=8, dx=1.2, dy=0.8, ant=-0.6, eye="squint", tails=1.8, extra=needles(3)),
              M(f=-0.6, tilt=6, dx=1.0, dy=0.8, ant=-0.4, tails=2.4, extra=needles(1)),
              M(f=0.3, tilt=2, dx=0.4, dy=0.4, tails=3.0),
              M(f=0.9, tails=3.6)]
    def streak(n):
        def fn(f, C, hd):
            for k in range(n):
                y = C[1] - 3 + k * 2.5
                line(f.n, C[0] - 9 - k * 2, y - 2, C[0] - 4 - k, y, "5" if k % 2 else "4")
        return fn
    def flakes(f, C, hd):
        for k in range(5): f.g.put(*P(C[0] - 6 + k * 3, C[1] + 5 + (k % 2) * 2), "8" if k % 2 else "7")
    dive = [M(f=1.1, tilt=-10, dy=-0.8, ant=0.6, eye="wide"),
            M(f=1.25, tilt=-16, dy=-1.8, dx=-1.2, ant=0.9, eye="wide", tails=0.6),
            M(f=1.2, tilt=-18, dy=-2.2, dx=-1.6, ant=1.0, eye="wide", tails=1.0, glow=1),
            M(f=0.9, tilt=24, dy=4.0, dx=2.0, ant=-1.0, eye="squint", tails=2.0, glow=1, extra=streak(4)),
            M(f=0.8, tilt=26, dy=5.0, dx=3.0, ant=-1.0, eye="squint", tails=2.6, glow=1, extra=lambda f, C, hd: (streak(4)(f, C, hd), flakes(f, C, hd))),
            M(f=0.7, tilt=20, dy=4.0, dx=2.6, ant=-0.8, eye="squint", tails=3.2, extra=flakes),
            M(f=-0.6, tilt=-6, dy=1.0, dx=1.0, ant=0.0, eye="open", tails=3.8),
            M(f=0.6, tilt=0, dy=0.2, tails=4.4)]
    death = [M(f=1.2, tilt=-20, dy=-0.5, eye="wide", ant=1.0, tails=1.0),
             M(f=-0.5, tilt=30, dy=4.0, eye="dead", ant=-1.0, tails=2.0),
             M(f=-0.8, tilt=50, hover=4.0, dy=0.5, eye="dead", ant=-1.4, tails=3.0),
             silkmoth_corpse()]
    knock = M(f=1.2, tilt=-22, dx=-1.0, dy=-0.5, eye="squint", ant=1.0, tails=1.0)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.06] * 6),
             ("Volley", volley, [0.12, 0.12, 0.06, 0.08, 0.1, 0.12, 0.12]),
             ("Dive", dive, [0.12, 0.12, 0.12, 0.06, 0.06, 0.08, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.14, 0.4], knock)
    sheet("YsvSilkmoth", anims, outdir, scale=6, remap=SILK_LIFT)


# ================================================================== RIME KNIGHT (T2; Shardling line)
# A widow's sworn knight in plate of clear ice: crystal-spiked pauldrons, a black silk cape and helm plume, a crystal
# greatsword. Her special freezes ice armour (plates) over her that each soak one hero hit.
def knight(dx=0.0, dy=0.0, lean=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), hands=((-3.0, -10.0), (4.0, -11.0)), sword=None,
           eye="open", plume=0.0, cape=0.0, glow=0, crouch=0.0, extra=None, head_tilt=0.0, shield=True):
    """sword: (hilt, tip) world points relative to the feet (hilt in the front hand)."""
    f = Fr()
    piv = (dx, 0.0)
    def L(x, y): return rot_about((dx + x, y + dy + crouch), piv, lean)
    hip = L(0.0, -8.4)
    chest = L(0.6, -13.6)
    head = L(1.4, -18.6)
    # cape: black silk with violet sheen and a frost-lace hem, flowing behind
    cp = [L(-1.2, -16.4), L(-4.4 - cape * 0.8, -11.0), L(-6.6 - cape * 2.0, -3.0), L(-5.2 - cape * 2.4, -0.6),
          L(-2.6 - cape, -1.6), L(-0.8, -9.0)]
    poly(f.u, cp, "C", shade=lambda x, y: pick("ABCDE", 0.2 + (x - dx) * 0.08 + (0.4 if (x * 2 + y) % 7 == 0 else 0)))
    line(f.u, *cp[2], *cp[3], "6"); line(f.u, *cp[3], *cp[4], "5")
    # legs (back one darker), greaves of ice
    for k, (fx, fy) in enumerate(feet):
        h = L(-1.2 + k * 2.2, -8.2)
        foot = (dx + fx, fy + min(0.0, dy * 0.0))
        (kx, ky), _ = ik(h[0], h[1], foot[0], foot[1] - 1.0, 4.6, 4.4, bend=1)
        lay = f.u if k == 0 else f.b
        ramp = "1234" if k == 0 else "3456"
        tube(lay, [h, (kx, ky)], [1.6, 1.3], ramp, bias=0.2)
        tube(lay, [(kx, ky), (foot[0], foot[1] - 1.0)], [1.4, 1.2], ramp, bias=0.2)
        ell(lay, foot[0] + 0.8, foot[1] - 0.8, 1.9, 1.0, ramp, bias=0.2)
        lay.put(*P(kx + 0.5, ky - 0.5), "7" if k else "4")
    # back arm
    shb = L(-1.8, -14.6)
    (ebx, eby), (hbx, hby) = ik(shb[0], shb[1], dx + hands[0][0], hands[0][1] + dy + crouch, 3.8, 3.8, bend=-1)
    tube(f.u, [shb, (ebx, eby), (hbx, hby)], [1.3, 1.1, 1.0], "1234", bias=0.2)
    # v0.10: a steel kite shield on the back arm, rimmed in frost, a crystal boss (the knight reads armoured at 1x)
    if shield:
        sx_, sy_ = hbx - 1.6, hby - 1.0
        def kite(c):
            pts = [(sx_ - 3.0, sy_ - 4.4), (sx_ + 2.6, sy_ - 4.4), (sx_ + 2.4, sy_ + 1.6), (sx_ - 0.2, sy_ + 5.4), (sx_ - 2.8, sy_ + 1.6)]
            poly(c, pts, "3", shade=lambda x, y: pick("2345", 0.55 - (x - sx_) * 0.12 - (y - sy_) * 0.06))
            line(c, *pts[0], *pts[1], "6"); line(c, *pts[0], *pts[4], "5")
            line(c, sx_ - 0.2, sy_ - 4.0, sx_ - 0.2, sy_ + 4.6, "2")
            c.put(*P(sx_ - 0.2, sy_ - 0.6), "7"); c.put(*P(sx_ + 0.8, sy_ - 0.6), "5")
        tmp = Canvas(); kite(tmp)
        for k_, v_ in outl(Spr(tmp.px), "0").px.items(): f.u.put(k_[0], k_[1], v_)
        f.g.put(*P(sx_ - 0.2, sy_ - 1.6), "G")
    # torso: ice breastplate, silk tabard, belt
    tube(f.b, [hip, chest], [2.8, 3.3], "3456", bias=0.25)
    ell(f.b, chest[0] + 0.4, chest[1] + 0.4, 3.3, 3.0, "34567", ang=lean, bias=0.3,
        shader=lambda nu, nv, d, l, ch, x, y: ("8" if abs(nu + nv - 0.1) < 0.12 and nv < 0 else ch))
    tab = [L(-1.2, -11.6), L(2.4, -11.6), L(2.0, -5.2), L(0.6, -4.4), L(-0.8, -5.2)]
    poly(f.b, tab, "C", shade=lambda x, y: pick("BCDE", 0.4 - (x - dx) * 0.1))
    line(f.b, *L(-1.6, -9.0), *L(2.8, -9.0), "2")
    f.b.put(*P(*L(0.6, -9.0)), "6")
    hourglass(f.g, *L(0.5, -7.2), s=1, bright=glow > 0)
    # helm: great-helm of ice, a dark visor slit, black silk plume streaming back
    ell(f.b, head[0], head[1], 2.6, 2.9, "34567", ang=lean + head_tilt, bias=0.3)
    vis = [rot_about((head[0] + dx_, head[1] + 0.2), head, lean + head_tilt) for dx_ in (0.2, 1.2, 2.2)]
    for v_ in vis: f.b.put(*P(*v_), "1")
    pl0 = rot_about((head[0] - 0.2, head[1] - 2.6), head, lean + head_tilt)
    pts = [pl0]
    x, y = pl0
    for j in range(8):
        a = math.radians(200 - j * 11 + plume * 9 * math.sin(j * 0.8 + plume))
        x += math.cos(a) * 1.2; y += math.sin(a) * 1.2
        pts.append((x, y))
    for j, (px_, py_) in enumerate(pts):      # v0.8: a white plume (was black silk)
        f.b.put(*P(px_, py_), "h" if j < 3 else "g"); f.b.put(*P(px_, py_ + 1), "f", over=False)
    crystal(f.b, *rot_about((head[0] + 0.8, head[1] - 2.4), head, lean + head_tilt), -70 + lean, 1.6, 0.5, lit=0.1)
    # pauldrons with crystal spikes
    for k, (ox, sz) in enumerate(((-1.6, 2.2), (2.6, 2.5))):
        pc = L(ox, -15.4)
        lay = f.u if k == 0 else f.b
        ell(lay, pc[0], pc[1], sz, 1.8, "34567" if k else "2345", ang=lean, bias=0.3)
        crystal(lay, pc[0] - 0.3, pc[1] - 1.0, -110 + k * 30 + lean, 2.6 if k else 2.2, 0.7, lit=0.1 if k else -0.3)
    # sword (crystal greatsword) + front arm
    shf = L(2.6, -14.8)
    (efx, efy), (hfx, hfy) = ik(shf[0], shf[1], dx + hands[1][0], hands[1][1] + dy + crouch, 3.8, 3.8, bend=1)
    tip = None
    if sword is not None:
        (hx_, hy_), (tx_, ty_) = sword
        hx_, hy_, tx_, ty_ = dx + hx_, hy_ + dy + crouch, dx + tx_, ty_ + dy + crouch
        ang = math.degrees(math.atan2(ty_ - hy_, tx_ - hx_))
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        line(f.b, hx_ - ux * 2.0, hy_ - uy * 2.0, hx_ + ux * 0.6, hy_ + uy * 0.6, "C")              # silk-wrapped grip
        line(f.b, hx_ + ux * 1.0 - uy * 2.0, hy_ + uy * 1.0 + ux * 2.0, hx_ + ux * 1.0 + uy * 2.0, hy_ + uy * 1.0 - ux * 2.0, "6")
        tip = crystal(f.b, hx_ + ux * 1.4, hy_ + uy * 1.4, ang, math.hypot(tx_ - hx_, ty_ - hy_) - 1.4, 1.2, lit=0.2)
        f.g.put(*P(*tip), "G" if glow else "8")
    tube(f.b, [shf, (efx, efy), (hfx, hfy)], [1.4, 1.2, 1.1], "3456", bias=0.25)
    ell(f.b, hfx, hfy, 1.3, 1.2, "4567", bias=0.3)
    # eyes behind the visor
    ex, ey = P(*vis[1])
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex + 1, ey, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex + 1, ey, "G")
    elif eye == "squint": f.g.put(ex, ey, "I")
    else: f.g.put(ex, ey, "2")
    if glow:
        for k in range(glow * 3):
            a = math.radians(k * 47 + glow * 30)
            f.g.put(*P(chest[0] + 6.5 * math.cos(a), chest[1] + 2 + 5 * math.sin(a)), "7" if k % 2 else "G")
    if extra: extra(f, (hfx, hfy), tip, head)
    return f.done()


def knight_corpse():
    f = Fr()
    poly(f.u, [(-9, 0), (-6, -3), (2, -3.5), (5, -1), (3, 0)], "C", shade=lambda x, y: pick("ABCD", 0.3 + x * 0.03))
    ell(f.b, -1.0, -2.2, 5.0, 2.0, "34567", bias=0.2)
    ell(f.b, 5.0, -2.0, 2.4, 2.0, "34567", bias=0.3)
    f.b.put(5, -2, "1"); f.b.put(6, -2, "1")
    crystal(f.b, -6, -1, -10, 9, 1.0)
    for x in (-3, 0, 2): crystal(f.b, x, -3.5, -80 - x * 6, 2.0, 0.6)
    return f.done()


def build_knight(outdir):
    K = knight
    REST = dict(hands=((-3.4, -9.6), (4.4, -10.4)), sword=((4.6, -10.6), (6.4, 0.5)))
    idle = [K(**REST), K(hands=((-3.4, -9.3), (4.4, -10.1)), sword=((4.6, -10.3), (6.4, 0.6)), plume=0.6, cape=0.3, crouch=0.3),
            K(hands=((-3.4, -9.2), (4.4, -10.0)), sword=((4.6, -10.2), (6.4, 0.6)), plume=1.2, cape=0.6, crouch=0.4, eye="squint"),
            K(**REST, plume=1.8, cape=0.3)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(K(lean=6, dy=-0.6 * abs(math.sin(ph)), feet=((-3.0 - 3.0 * math.sin(ph), -max(0, 1.5 * math.cos(ph))),
                                                                  (3.0 + 3.0 * math.sin(ph), -max(0, -1.5 * math.cos(ph)))),
                     hands=((-4.0, -10.0), (3.6, -11.4)), sword=((3.6, -11.4), (-5.0, -20.0)), plume=i, cape=1.0 + 0.5 * math.sin(ph)))
    def smear(f, hand, tip, head):
        for k in range(10):
            a = math.radians(-110 + k * 17)
            for rr in (15, 14):
                f.n.put(*P(1 + rr * math.cos(a), -10 + rr * math.sin(a)), "6" if rr == 15 else "4", over=False)
    def impact(n):
        def fn(f, hand, tip, head):
            if tip is None: return
            for k in range(n):
                f.g.put(*P(tip[0] + (k % 3) - 1, tip[1] - 1 - k), "8" if k % 2 == 0 else "6")
        return fn
    cleave = [K(hands=((-3.6, -10.4), (2.6, -15.0)), sword=((2.6, -15.0), (-6.0, -21.0)), lean=-4, plume=0.5),
              K(hands=((-3.0, -15.6), (0.6, -18.4)), sword=((0.6, -18.4), (-10.4, -16.0)), lean=-10, crouch=0.4, plume=1.0, eye="wide"),
              K(hands=((-2.0, -16.0), (1.0, -19.0)), sword=((1.0, -19.0), (-9.6, -22.6)), lean=-12, crouch=0.6, plume=1.4, eye="wide", glow=1),
              K(hands=((2.0, -13.0), (8.6, -11.0)), sword=((8.6, -11.0), (16.6, -2.0)), lean=10, feet=((-4.0, 0), (4.6, 0)), plume=2.2,
                eye="wide", extra=smear),
              K(hands=((2.0, -11.0), (8.0, -8.0)), sword=((8.0, -8.0), (17.0, 0.0)), lean=14, feet=((-4.2, 0), (5.0, 0)), crouch=0.8, plume=2.8,
                eye="squint", extra=impact(4)),
              K(hands=((1.0, -10.6), (7.4, -8.4)), sword=((7.4, -8.4), (16.4, -0.6)), lean=10, feet=((-4.0, 0), (4.8, 0)), crouch=0.6, plume=3.2,
                extra=impact(2)),
              K(hands=((-2.0, -10.0), (5.6, -9.8)), sword=((5.6, -9.8), (9.6, 0.5)), lean=4, plume=3.6),
              K(**REST, plume=4.0)]
    def frosting(n):
        def fn(f, hand, tip, head):
            for k in range(n):
                a = math.radians(k * 60 + n * 15)
                crystal(f.g, head[0] - 1 + 7 * math.cos(a), head[1] + 7 + 5.5 * math.sin(a), math.degrees(a) + 90, 2.0, 0.6, ramp="5678")
        return fn
    plate = [K(hands=((-3.0, -11.4), (2.6, -13.6)), sword=((2.6, -13.6), (2.8, -0.2)), lean=0, plume=0.4),
             K(hands=((-1.0, -12.6), (2.4, -13.0)), sword=((2.4, -13.0), (2.6, 0.5)), crouch=1.0, plume=0.8, eye="squint", glow=1),
             K(hands=((-0.6, -12.4), (2.4, -12.8)), sword=((2.4, -12.8), (2.6, 0.5)), crouch=1.6, plume=1.2, eye="squint", glow=2,
               extra=frosting(2)),
             K(hands=((-0.6, -12.2), (2.4, -12.6)), sword=((2.4, -12.6), (2.6, 0.5)), crouch=1.8, plume=1.6, eye="wide", glow=3,
               extra=frosting(4)),
             K(hands=((-0.6, -12.6), (2.4, -13.0)), sword=((2.4, -13.0), (2.6, 0.5)), crouch=0.6, plume=2.4, eye="wide", glow=3,
               extra=frosting(6)),
             K(hands=((-2.4, -11.0), (3.4, -12.0)), sword=((3.4, -12.0), (4.6, 0.5)), plume=3.0, glow=1),
             K(**REST, plume=3.4)]
    death = [K(hands=((-4.4, -14.0), (4.0, -14.6)), sword=((4.0, -14.6), (12.0, -18.0)), lean=-12, eye="wide", plume=1.5, cape=1.0),
             K(hands=((-3.0, -6.0), (4.0, -5.0)), lean=20, crouch=3.0, eye="squint", plume=2.0, cape=1.5),
             grounded(K(hands=((-2.0, -3.0), (5.0, -2.0)), lean=60, crouch=4.0, eye="dead", plume=2.5, cape=1.8)),
             knight_corpse()]
    knock = K(hands=((-4.4, -12.0), (3.8, -13.0)), sword=((3.8, -13.0), (8.0, -1.0)), lean=-10, eye="squint", plume=1.4, cape=1.0)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Cleave", cleave, [0.14, 0.12, 0.12, 0.05, 0.08, 0.12, 0.12, 0.12]),
             ("Plate", plate, [0.12, 0.14, 0.14, 0.14, 0.1, 0.14, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("YsvRimeKnight", anims, outdir, scale=6, remap=KNIGHT)


# ================================================================== THE PALE EMPRESS (T3, flying; Weaver / Silkmoth line)
# A vast moth seen from the front, wings spread like a cathedral window: black silk shading to aurora violet and ice at
# the edges, frost-lace rings, four glowing eyespots, long silk tails; a crown of feathered antennae and a hanging
# ice-lantern abdomen with a living light inside.
def empress(dy=0.0, dx=0.0, flap=0.0, lean=0.0, ant=0.0, eye="open", lamp=1, tails=0.0, extra=None, hover=7.0, fold=0.0,
            storm=0, ground=False):
    f = Fr()
    cx, cy = dx, -(hover + 14.0) + dy
    if ground: cy = -5.0 + dy
    def wing(sd, upper, layer):
        sx, sy = cx + sd * 1.6 + lean * 0.3, cy - (1.5 if upper else -1.5)
        if upper:
            span = 17.5 * (0.7 + 0.3 * math.cos(flap * 1.2)) * (1 - fold * 0.6)   # 17.5: the full-span idle flap stays inside the T3 width (42)
            tipy = sy - 7.5 + flap * 4.5 - fold * 3
            pts = [(sx, sy - 1.0), (sx + sd * span * 0.4, tipy - 1.5), (sx + sd * span * 0.8, tipy - 1.0), (sx + sd * span, tipy + 1.5),
                   (sx + sd * span * 0.9, tipy + 5.0), (sx + sd * span * 0.6, sy + 2.6 - flap * 1.2), (sx, sy + 2.0)]
        else:
            span = 13.0 * (0.75 + 0.25 * math.cos(flap)) * (1 - fold * 0.5)
            pts = [(sx, sy - 1.0), (sx + sd * span, sy + 1.2 + flap * 1.5), (sx + sd * span * 0.85, sy + 6.5 + flap * 0.8),
                   (sx + sd * span * 0.4, sy + 8.0), (sx, sy + 3.0)]
        S = (sx, sy)
        def shade(x, y):
            r = math.hypot((x - sx) / max(1.0, span), (y - sy) / max(1.0, span * 0.7))
            # v0.10: clean shaded panels (no checker dither): violet silk root, a frost band, a pale frost margin
            lit = -((x - sx) * sd * -0.2 + (y - sy)) / max(1.0, span) * 0.6
            if r > 0.84: return "7" if r > 0.93 else "6"
            if 0.62 < r <= 0.84: return pick("456", 0.1 + lit)
            ch = pick("BCCDDE" if upper else "BCCDE", -0.6 + r * 1.9 + lit)
            if abs(r - 0.42) < 0.035: ch = "E"
            if r > 0.3 and abs(math.sin(math.atan2(y - sy, (x - sx) * sd) * 4)) < 0.09: ch = "A"     # veins
            return ch
        poly(layer, pts, "C", shade=shade)
        for i in range(1, len(pts) - 2):
            line(layer, *pts[i], *pts[i + 1], "7" if i % 2 else "6")
        # eyespot
        if upper: e_ = (sx + sd * span * 0.58, (tipy + sy) * 0.5 + 0.8)
        else: e_ = (sx + sd * span * 0.55, sy + 3.6 + flap * 0.6)
        ex_, ey_ = P(*e_)
        for (a_, b_) in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (2, 0), (0, -1), (1, -1), (0, 2), (1, 2)):
            layer.put(ex_ + a_ - (sd < 0), ey_ + b_, "1")
        f.g.put(ex_ - (sd < 0), ey_, "H" if lamp > 1 else "G"); f.g.put(ex_ + 1 - (sd < 0), ey_ + 1, "I")
        if not upper:   # long silk tails
            t0 = pts[3]
            x, y = t0
            for k in range(10):
                a = math.radians(90 + sd * (14 + 10 * math.sin(k * 0.6 + tails)))
                x += math.cos(a) * 1.1; y += math.sin(a) * 1.0
                f.u.put(*P(x, y), "8" if k % 3 == 0 else "6" if k % 3 == 1 else "7")
            f.u.put(*P(x, y + 1), "G")
    for sd in (-1, 1):
        wing(sd, False, f.u)
    for sd in (-1, 1):
        wing(sd, True, f.u)
    # hanging ice lantern abdomen in a silk cage
    lx, ly = cx + lean * 0.6, cy + 7.0
    ell(f.b, lx, ly, 3.4, 5.0, "34567", bias=0.2,
        shader=lambda nu, nv, d, l, ch, x, y: (("E" if l > 0 else "D") if abs(nu) > 0.5 else ch))     # violet silk walls
    for k in range(3): line(f.b, lx - 2.8, ly - 3 + k * 3, lx + 2.8, ly - 2 + k * 3, "C")
    crystal(f.b, lx, ly + 4.0, 90, 3.0, 0.9)
    glow = ["4", "I", "G", "H"][min(3, lamp)]
    for (a_, b_) in ((0, 0), (0, 1), (-1, 0), (1, 1), (0, -1)):
        f.g.put(*P(lx + a_, ly + b_), glow if (a_, b_) == (0, 0) else ("G" if lamp > 1 else "I"))
    # thorax: frost-white fur, mantle
    ell(f.b, cx + lean * 0.3, cy, 3.6, 3.8, "fgh8", bias=0.25,
        shader=lambda nu, nv, d, l, ch, x, y: ("g" if d > 0.7 and (x + y) % 2 else ch))
    hx, hy = cx + lean * 0.5, cy - 4.6
    ell(f.b, hx, hy, 2.4, 2.0, "BCDE", bias=0.2)
    # crown: feathered antennae arching out + a small ice tiara
    for sd in (-1, 1):
        x, y = hx + sd * 0.8, hy - 1.6
        pts = [(x, y)]
        a = -90 + sd * (30 + ant * 8)
        for j in range(7):
            a += sd * 9
            x += math.cos(math.radians(a)) * 1.1; y += math.sin(math.radians(a)) * 1.1
            pts.append((x, y))
        polyline(f.b, pts, "7")
        for j in range(1, len(pts) - 1, 1):
            f.b.put(*P(pts[j][0] + sd * 0.0, pts[j][1] + 1), "5" if j % 2 else "4", over=False)
            f.b.put(*P(pts[j][0] - sd, pts[j][1]), "4", over=False)
        f.g.put(*P(*pts[-1]), "8")
    for k, ox in enumerate((-1.2, 0.0, 1.2)):
        crystal(f.b, hx + ox, hy - 1.6, -90 + ox * 18, 2.2 + (k == 1) * 1.4, 0.5, lit=0.2)
    # eyes
    for sd in (-1, 1):
        ex, ey = P(hx + sd * 1.0, hy + 0.2)
        if eye == "open": f.g.put(ex, ey, "G")
        elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex, ey - 1, "G")
        elif eye == "squint": f.g.put(ex, ey, "I")
        else: f.g.put(ex, ey, "2")
    # v0.9 lineage (Silk Weaver): three pairs of long violet spider legs arching out from under the thorax, knees high,
    # frost-tipped, the same stilt legs the Weaver walks on; the wings are the Silkmoth's
    for sd in (-1, 1):
        for j, (kx_, ky_, fx_, fy_) in enumerate(((7.6, 5.0, 9.0, 11.6), (5.6, 6.4, 6.4, 12.6), (3.6, 7.6, 3.8, 13.0))):
            sw = 0.6 * math.sin(tails + j * 1.4 + (sd > 0))
            r0 = (cx + sd * 1.6, cy + 1.6 + j * 0.8)
            kn = (cx + sd * kx_, cy + ky_ + sw * 0.4)
            ft = (cx + sd * (fx_ + sw * 0.5), cy + fy_ + sw)
            line(f.b, r0[0], r0[1], kn[0], kn[1], "g" if j != 1 else "f")      # v0.10: the Silkmoth's pale furred legs
            line(f.b, kn[0], kn[1], ft[0], ft[1], "6" if j != 1 else "5")
            f.b.put(*P(*kn), "h"); f.g.put(*P(*ft), "7")
    if storm:
        for k in range(storm * 4):
            a = math.radians(k * 37 + storm * 21)
            r = 5 + (k % 4) * 3
            f.g.put(*P(cx + r * math.cos(a), cy - 18 + r * 0.45 * math.sin(a)), "8" if k % 3 == 0 else "7" if k % 3 == 1 else "6")
    if extra: extra(f, (cx, cy), (hx, hy))
    return f.done()


def empress_corpse():
    f = Fr()
    # fallen face-down, wings spread flat on the floor, lantern cracked and dark
    for sd in (-1, 1):
        poly(f.u, [(sd * 1.5, -2.5), (sd * 17, -6.0), (sd * 18, -2.0), (sd * 12, 0.0), (sd * 1.5, 0.0)], "C",
             shade=lambda x, y: pick("ABCDE56", -0.8 + abs(x) / 9.0))
        for x in range(2, 17, 2): f.u.put(sd * x, -1 - (x % 4 == 0), "5")
        poly(f.u, [(sd * 1, -1), (sd * 11, 0.0), (sd * 8, 0.0)], "B")
    ell(f.b, 0, -2.6, 3.4, 2.6, "fgh8", bias=0.2)
    ell(f.b, 4.0, -1.8, 2.6, 1.8, "3456", bias=0.0)
    for (x, y) in ((3, -2), (4, -1), (5, -2)): f.b.put(x, y, "1")
    ell(f.b, -3.5, -1.5, 1.8, 1.4, "BCD", bias=0.1)
    return f.done()


def build_empress(outdir):
    E = empress
    idle = [E(flap=-0.8, lamp=1, tails=0.0), E(flap=-0.1, dy=0.8, lamp=2, tails=0.7, ant=0.3), E(flap=0.6, dy=1.4, lamp=2, tails=1.4, ant=0.5),
            E(flap=0.0, dy=0.8, lamp=1, tails=2.1, eye="squint")]
    run = [E(flap=[-0.9, -0.3, 0.4, 0.9, 0.3, -0.4][i], lean=1.2, dx=0.5, dy=[0, 0.6, 1.2, 1.4, 0.8, 0.2][i], tails=i * 0.7, lamp=1,
             ant=-0.4) for i in range(6)]
    def fan(n):
        def fn(f, C, hd):
            for k in range(n):
                a = math.radians(-30 + k * 15)
                for r in (8, 10):
                    f.g.put(*P(C[0] + 6 + r * math.cos(a), C[1] - 1 + r * math.sin(a)), "8" if r == 8 else "6")
        return fn
    aurora = [E(flap=-1.0, lean=-0.6, eye="wide", lamp=2, ant=0.6),
              E(flap=-1.3, lean=-1.0, dy=-0.8, eye="wide", lamp=3, ant=0.9, tails=0.6),
              E(flap=-1.4, lean=-1.2, dy=-1.2, eye="wide", lamp=3, ant=1.0, tails=1.2),
              E(flap=1.0, lean=1.2, dy=0.8, eye="squint", lamp=3, tails=1.8, extra=fan(5)),
              E(flap=0.8, lean=1.0, dy=1.0, lamp=2, tails=2.4, extra=fan(3)),
              E(flap=0.2, lean=0.4, dy=0.6, lamp=1, tails=3.0),
              E(flap=-0.6, tails=3.6, lamp=1)]
    whiteout = [E(flap=-0.8, eye="open", lamp=1, ant=0.4),
                E(flap=-1.3, dy=-1.0, eye="wide", lamp=2, ant=0.9, storm=1),
                E(flap=-1.5, dy=-1.6, eye="wide", lamp=3, ant=1.1, storm=2, fold=0.1),
                E(flap=-1.5, dy=-1.8, eye="wide", lamp=3, ant=1.2, storm=3, fold=0.15),
                E(flap=1.1, dy=0.8, lean=0.8, eye="wide", lamp=3, storm=4),
                E(flap=0.9, dy=1.0, lean=0.6, eye="squint", lamp=2, storm=2),
                E(flap=0.1, dy=0.6, lamp=1),
                E(flap=-0.6, lamp=1)]
    death = [E(flap=-1.4, dy=-1.0, eye="wide", lamp=3, ant=1.4, tails=1.0),
             E(flap=0.9, dy=5.0, eye="dead", lamp=1, fold=0.4, ant=-1.0, tails=2.0),
             E(flap=1.2, hover=1.0, dy=2.0, eye="dead", lamp=0, fold=0.7, ant=-1.5, tails=3.0),
             empress_corpse()]
    knock = E(flap=-1.3, lean=-1.6, dx=-1, dy=-0.5, eye="squint", lamp=2, ant=1.0)
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.09] * 6),
             ("Aurora", aurora, [0.12, 0.12, 0.12, 0.06, 0.1, 0.12, 0.12]),
             ("Whiteout", whiteout, [0.12, 0.14, 0.14, 0.14, 0.06, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.5], knock)
    sheet("YsvEmpress", anims, outdir, scale=4)


# ================================================================== RIME COLOSSUS (T3; Witch / Knight line)
# A hunched glacier given a body: boulder shoulders of cracked blue ice, crystal spines down the back, black widow silk
# bound round its chest like a mourning sash, a hooded head sunk low between the shoulders, fists like ice floes and a
# frozen hourglass heart that glows through the cracks.
def colossus(dx=0.0, dy=0.0, lean=0.0, fists=((10.0, -4.0), (-4.0, -5.0)), feet=((-6.0, 0.0), (5.0, 0.0)), eye="open",
             core=1, crack=0, extra=None, crouch=0.0, spines=1.0):
    """fists: (front, back) world positions relative to the feet."""
    f = Fr()
    piv = (dx, 0.0)
    def L(x, y): return rot_about((dx + x, y + dy + crouch), piv, lean)
    hip = L(-1.0, -12.0)
    chest = L(-1.0, -20.0)
    def iceshade(nu, nv, d, l, ch, x, y):
        if (x * 3 + y * 7) % 23 == 0 and d < 0.8: return "2"
        if (x * 5 - y * 3) % 29 == 0 and d < 0.85 and l > 0: return "7"
        return ch
    legs = []
    for k, (fx, fy) in enumerate(feet):
        h = L(-4.0 + k * 5.0, -11.0)
        foot = (dx + fx, fy)
        (kx, ky), _ = ik(h[0], h[1], foot[0], foot[1] - 2.0, 5.4, 5.0, bend=1)
        legs.append((h, (kx, ky), foot))
    # back leg + back arm (behind)
    h, kn, foot = legs[0]
    tube(f.u, [h, kn, (foot[0], foot[1] - 2.0)], [3.2, 2.8, 2.6], "1234", bias=0.2)
    ell(f.u, foot[0] + 1.0, foot[1] - 1.6, 3.8, 1.9, "1234", bias=0.2)
    shb = L(-8.0, -25.0)
    fb = (dx + fists[1][0], fists[1][1] + dy + crouch)
    (ebx, eby), _ = ik(shb[0], shb[1], fb[0], fb[1], 9.0, 9.0, bend=-1)
    tube(f.u, [shb, (ebx, eby), fb], [3.0, 2.6, 2.4], "1234", bias=0.2)
    ell(f.u, fb[0], fb[1], 3.8, 3.4, "1234", bias=0.2)
    # back spines (crystal ridge)
    for k, (ox, oy, a, ln) in enumerate(((-11, -21, -155, 5), (-11, -26, -135, 7), (-8, -30, -115, 7.5))):
        b_ = L(ox, oy)
        crystal(f.u, b_[0], b_[1], a + lean, ln * spines, 1.4, lit=0.0)
    # v0.9 lineage (Rime Knight): the knight's crystal greatsword driven into its back to the hilt, the silk-wrapped grip
    # and crossguard standing out above the shoulders
    g0, g1 = L(-3.0, -26.0), L(1.2, -37.0)
    line(f.u, g0[0], g0[1], g1[0], g1[1], "C"); line(f.u, g0[0] + 1, g0[1], g1[0] + 1, g1[1], "D")
    cg = L(-2.4, -28.0)
    line(f.u, cg[0] - 3.0, cg[1] - 1.0, cg[0] + 3.2, cg[1] + 1.2, "7")
    f.u.put(*P(g1[0], g1[1] - 1), "8")
    # torso: a leaning glacier mass
    tube(f.b, [hip, chest], [5.0, 8.0], "12345", bias=0.2)
    ell(f.b, chest[0], chest[1], 10.0, 8.0, "1234567", ang=lean - 10, bias=0.1, shader=iceshade)
    # silk mourning sash wrapped across the chest
    for k in range(2):
        a0, a1 = L(-10.0, -25.0 + k * 3.4), L(8.0, -16.0 + k * 3.4)
        for (x, y) in line_px(*P(*a0), *P(*a1)):
            if (x, y) in f.b.px: f.b.put(x, y, "C" if k else "D"); f.b.put(x, y + 1, "B")
    # frozen heart: an hourglass of light in a crack
    hc = L(-1.0, -19.0)
    for (a_, b_) in ((-1, -3), (0, -2), (-1, -1), (2, 1), (1, 2), (2, 3)): f.b.put(*P(hc[0] + a_, hc[1] + b_), "1")
    hourglass(f.g, hc[0], hc[1], s=2, bright=core > 0)
    if core > 1:
        for (a_, b_) in ((-3, -1), (4, 0), (1, -4), (1, 4)): f.g.put(*P(hc[0] + a_, hc[1] + b_), "G")
    # front leg over the torso
    h, kn, foot = legs[1]
    tube(f.b, [h, kn, (foot[0], foot[1] - 2.0)], [3.4, 3.0, 2.8], "23456", bias=0.25)
    ell(f.b, foot[0] + 1.0, foot[1] - 1.6, 4.0, 2.0, "23456", bias=0.25)
    # front shoulder boulder
    c = L(4.0, -25.5)
    ell(f.b, c[0], c[1], 5.6, 4.6, "234567", ang=lean, bias=0.25, shader=iceshade)
    crystal(f.b, c[0] - 1.5, c[1] - 3.6, -75 + lean, 3.6 * spines, 1.1, lit=0.15)
    # front arm + fist
    shf = L(5.0, -23.0)
    ff = (dx + fists[0][0], fists[0][1] + dy + crouch)
    (efx, efy), _ = ik(shf[0], shf[1], ff[0], ff[1], 9.0, 9.0, bend=-1)
    tube(f.b, [shf, (efx, efy)], [3.0, 2.6], "23456", bias=0.25)
    tube(f.b, [(efx, efy), ff], [2.6, 2.6], "34567", bias=0.25)
    ell(f.b, ff[0], ff[1], 4.0, 3.6, "345678", bias=0.3, shader=iceshade)
    for k in range(3): f.b.put(*P(ff[0] + 1 + k * 0.8, ff[1] - 2.4 + k * 0.6), "2")
    # v0.10 lineage (Rime Knight only): the knight's gunmetal great-helm sunk into the glacier as its head, visor slit
    # glowing, the knight's white plume streaming back from the crest
    hd = L(9.0, -24.0)
    pl = [(hd[0] - 0.6, hd[1] - 3.4)]
    x, y = pl[0]
    for j in range(8):
        a = math.radians(200 - j * 10)
        x += math.cos(a) * 1.3; y += math.sin(a) * 1.3
        pl.append((x, y))
    for j, (px_, py_) in enumerate(pl):
        f.u.put(*P(px_, py_), "h" if j < 4 else "g"); f.u.put(*P(px_, py_ + 1), "f", over=False)
    hp = [(hd[0] - 3.4, hd[1] - 3.4), (hd[0] + 2.8, hd[1] - 3.6), (hd[0] + 3.8, hd[1] + 2.6), (hd[0] + 1.0, hd[1] + 3.6), (hd[0] - 3.2, hd[1] + 3.0)]
    poly(f.b, hp, "+", shade=lambda x, y: pick("&*+=~", 0.55 - (x - hd[0]) * 0.12 - (y - hd[1]) * 0.1))
    line(f.b, hd[0] - 0.4, hd[1] - 3.4, hd[0] - 0.4, hd[1] + 3.2, "*")
    line(f.b, hd[0] + 0.4, hd[1] + 0.6, hd[0] + 3.4, hd[1] + 0.6, "0")
    ex, ey = P(hd[0] + 1.2, hd[1] + 0.6)
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex + 2, ey, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex + 2, ey, "G"); f.g.put(ex, ey - 1, "G")
    elif eye == "squint": f.g.put(ex, ey, "I")
    else: f.g.put(ex, ey, "2")
    speckle(f.b, (dx - 14, -38, dx + 16, -14), 10, seed=5, chars="78", only_on="456")
    if crack:
        for (a_, b_) in ((-5, -21), (-4, -20), (-3, -22), (-2, -19), (-1, -23), (1, -17))[:crack * 2]:
            f.b.put(*P(*L(a_, b_)), "0")
    if extra: extra(f, ff, hd)
    return f.done()


def colossus_corpse():
    f = Fr()
    # collapsed into a heap of ice blocks, the silk sash slack across it, the heart dark
    for (x, y, rx, ry, rp) in ((-8, -3, 5, 3, "1234"), (-1, -4.5, 7, 4.5, "23456"), (7, -3, 5, 3, "2345"), (12, -2, 3, 2, "3456"),
                               (-13, -2, 3, 2, "2345")):
        ell(f.b, x, y, rx, ry, rp, bias=0.2)
    line(f.b, -10, -6, 9, -3, "C"); line(f.b, -10, -5, 9, -2, "B")
    for (x, a, ln) in ((-6, -110, 5), (-2, -95, 6), (3, -80, 4)): crystal(f.b, x, -8, a, ln, 1.1)
    hourglass(f.g, 0, -4, s=2, bright=False)
    return f.done()


def build_colossus(outdir):
    C = colossus
    REST = dict(fists=((11.0, -5.0), (-6.0, -5.5)))
    idle = [C(**REST), C(fists=((11.0, -4.6), (-6.0, -5.1)), crouch=0.5, core=1), C(fists=((11.0, -4.4), (-6.0, -4.9)), crouch=0.8, core=2),
            C(fists=((11.0, -4.8), (-6.0, -5.3)), crouch=0.4, eye="squint")]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(C(lean=5, dy=-0.8 * abs(math.sin(ph)), feet=((-6.0 - 3.0 * math.sin(ph), -max(0, 1.6 * math.cos(ph))),
                                                                 (5.0 + 3.0 * math.sin(ph), -max(0, -1.6 * math.cos(ph)))),
                     fists=((12.0 + 2 * math.sin(ph), -6.0), (-7.0 - 2 * math.sin(ph), -6.0))))
    def smear(f, ff, hd):
        for k in range(9):
            a = math.radians(-95 + k * 18)
            f.n.put(*P(4 + 15 * math.cos(a), -18 + 15 * math.sin(a)), "6" if k % 2 else "5")
    def quake(n):
        def fn(f, ff, hd):
            for k in range(-n, n + 1):
                f.g.put(*P(ff[0] + k * 1.5, 0), "8" if k % 2 else "7")
            for k in range(n):
                crystal(f.g, ff[0] - 4 + k * 3, -1, -90 + (k - n / 2) * 25, 2 + (k % 2), 0.6, ramp="5678")
        return fn
    slam = [C(fists=((9.0, -12.0), (-4.0, -12.0)), lean=-3, eye="open"),
            C(fists=((6.0, -36.0), (1.0, -37.0)), lean=-9, crouch=-0.5, eye="wide", core=2),
            C(fists=((4.0, -38.0), (0.0, -39.0)), lean=-12, crouch=-0.8, eye="wide", core=2),
            C(fists=((16.0, -18.0), (12.0, -20.0)), lean=8, eye="wide", core=2, extra=smear),
            C(fists=((17.0, -4.0), (13.0, -5.0)), lean=14, crouch=1.5, eye="squint", core=2, extra=quake(4)),
            C(fists=((17.0, -4.0), (13.0, -5.0)), lean=13, crouch=1.4, eye="squint", core=1, extra=quake(2)),
            C(fists=((14.0, -6.0), (2.0, -7.0)), lean=7, crouch=0.6),
            C(**REST)]
    def runner(n):
        def fn(f, ff, hd):
            for k in range(n):
                crystal(f.g, ff[0] + 4 + k * 4, -0.5, -90 + (k % 2) * 14 - 7, 3 + (k % 2) * 2, 0.9, ramp="5678")
        return fn
    glacier = [C(fists=((10.0, -8.0), (-6.0, -7.0)), lean=-2, eye="open", core=1),
               C(fists=((12.0, -30.0), (-7.0, -8.0)), lean=-6, eye="wide", core=2, feet=((-7.0, 0.0), (5.0, 0.0))),
               C(fists=((11.0, -34.0), (-8.0, -9.0)), lean=-9, crouch=-0.6, eye="wide", core=2),
               C(fists=((11.0, -35.0), (-8.0, -9.0)), lean=-10, crouch=-0.8, eye="wide", core=2, spines=1.1),
               C(fists=((15.0, -1.0), (-4.0, -6.0)), lean=16, crouch=2.0, eye="wide", core=2, extra=lambda f, ff, hd: (quake(3)(f, ff, hd), runner(1)(f, ff, hd))),
               C(fists=((15.0, -1.0), (-4.0, -6.0)), lean=15, crouch=2.0, eye="squint", core=2, extra=runner(3)),
               C(fists=((14.0, -2.0), (-4.0, -6.0)), lean=12, crouch=1.6, eye="squint", core=1, extra=runner(4)),
               C(fists=((13.0, -5.0), (-5.0, -6.0)), lean=6, crouch=0.8),
               C(**REST)]
    death = [C(fists=((13.0, -24.0), (-8.0, -24.0)), lean=-14, eye="wide", core=2, crack=1),
             C(fists=((14.0, -3.0), (-4.0, -3.0)), lean=18, crouch=4.0, eye="squint", core=1, crack=2),
             grounded(C(fists=((16.0, -2.0), (0.0, -2.0)), lean=40, crouch=7.0, eye="dead", core=0, crack=3, spines=0.7)),
             colossus_corpse()]
    knock = C(fists=((12.0, -16.0), (-8.0, -14.0)), lean=-10, eye="squint", core=1)
    anims = [("Idle", idle, [0.28, 0.24, 0.28, 0.24]), ("Run", run, [0.11] * 6),
             ("Slam", slam, [0.14, 0.16, 0.16, 0.06, 0.08, 0.16, 0.14, 0.14]),
             ("Glacier", glacier, [0.12, 0.12, 0.14, 0.14, 0.06, 0.1, 0.12, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.12, 0.14, 0.18, 0.5], knock)
    sheet("YsvColossus", anims, outdir, scale=4, remap=GLACIER)


# ================================================================== FX for the v0.7.2 monsters
def fx_needle():
    out = []
    for i in range(4):
        c = cv()
        for k in range(5):   # silk thread trailing, wavering
            c.put(-3 - k, (1 if (k + i) % 4 == 1 else -1 if (k + i) % 4 == 3 else 0), "6" if k % 2 else "C")
        line(c, -2, 0, 3, 0, "7"); c.put(4, 0, "8"); c.put(5, 0, "H" if i % 2 else "G")
        c.put(0, -1, "8"); c.put(1, 1, "5")
        out.append(outl(c.spr(), "1"))
    return out


def plates_frame(i, n=8):
    """Two shards of ice armour circling the knight's waist (floor origin; orbit centre 12 px up)."""
    c = cv()
    for k in range(2):
        a = 2 * math.pi * (i / n + k / 2.0)
        x, y = 10 * math.cos(a), -12 + 3.2 * math.sin(a)
        front = math.sin(a) > 0
        crystal(c, x, y + 2.5, -90 + 15 * math.cos(a), 6.0 if front else 4.6, 1.7 if front else 1.3, lit=0.2 if front else -0.4,
                ramp=None if front else "2345", ridge="8" if front else "5")
    return outl(c.spr(), "1")


def storm_frame(i, n=6):
    """A whirling knot of blizzard: dark midnight core, snow rings turning, flakes flung out."""
    c = cv()
    rot = i * (2 * math.pi / 3) / n
    for y in range(-9, 10):
        for x in range(-14, 15):
            d = (x / 13.0) ** 2 + (y / 8.5) ** 2
            if d > 1.0: continue
            if d > 0.7 and (x * 7 + y * 3 + i) % 3 == 0: continue
            c.put(x, y, "1" if d < 0.3 else "2" if d < 0.65 else "3")
    for arm in range(3):
        for k in range(22):
            t = k / 21.0
            a = rot + arm * 2 * math.pi / 3 + t * 4.0
            r = 1.0 + t * 12.0
            ch = "8" if t > 0.75 else "7" if t > 0.4 else "6"
            c.put(*P(r * math.cos(a), r * 0.65 * math.sin(a)), ch)
    rnd = random.Random(7 + i)
    for k in range(10):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(12, 16)
        c.put(*P(r * math.cos(a), r * 0.62 * math.sin(a)), "8" if k % 2 else "6")
    c.put(0, 0, "G"); c.put(1, 0, "I")
    return c.spr()


def spike_frame(i):
    """An ice spike bursts from the floor (the Colossus' glacier line). Floor origin."""
    c = cv()
    if i == 0:
        for (x, y) in ((-3, 0), (-2, -1), (-1, 0), (0, -1), (1, 0), (2, -1), (3, 0)): c.put(x, y, "5")
        c.put(0, 0, "8")
        return c.spr()
    h = [0, 9, 12, 12, 11, 6][i]
    if i <= 4:
        for (bx, a, ln, wd) in ((0, -90, h, 2.0), (-3, -118, h * 0.6, 1.3), (3, -64, h * 0.65, 1.4)):
            crystal(c, bx, 0, a, ln, wd, lit=0.15)
        for x in range(-6, 7):
            if (x + i) % 2: c.put(x, 0, "4")
        spr = outl(c.spr(), "1")
        if i == 1: spr = merge(spr, Spr({(-5, -3): "8", (5, -4): "8", (-2, -11): "7", (3, -10): "7"}))
        return spr
    rnd = random.Random(3)
    for k in range(10):
        a = rnd.uniform(-math.pi, 0); r = rnd.uniform(2, 8)
        c.put(*P(r * math.cos(a), min(-1, r * math.sin(a) * 0.9)), "8" if k % 2 else "6")
    for x in range(-6, 7):
        if (x + i) % 2: c.put(x, 0, "5")
    return c.spr()


def build_fx2(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxYsvNeedle"): centered("FxYsvNeedle", [("Fly", fx_needle(), [0.05] * 4)], outdir, (16, 6))
    if want("FxYsvPlates"): fx_fixed("FxYsvPlates", [("Orbit", [plates_frame(i) for i in range(8)], [0.08] * 8)], outdir, (28, 22), (14, 21), scale=6)
    if want("FxYsvStorm"): centered("FxYsvStorm", [("Loop", [storm_frame(i) for i in range(6)], [0.08] * 6)], outdir, (34, 22), scale=6)
    if want("FxYsvSpike"): grounded_fx("FxYsvSpike", [("Play", [spike_frame(i) for i in range(6)], [0.05, 0.05, 0.08, 0.12, 0.1, 0.1])],
                                       outdir, (18, 16), scale=8)


# ================================================================== v0.8 art pass: own sheets for borrowed art
def cleave_frame(i):
    """FxYsvCleave: the Rime Knight's two-handed crystal greatsword cleave (replaces the tinted vanilla OrcSwipe).
    A crescent of ice swept from overhead down to the floor in front, a white leading edge, frost shards flung off the
    trailing edge. Origin = the effect's spawn point (8 px above the feet, 3 px ahead); the crescent runs from 11 px
    above it to the floor 8 px below it, out to x 16."""
    c = cv()
    cx, cy, R = 3.0, 0.0, 11.5
    a_lead = [44, 48, 50, 52][i]           # the whole sweep shows on the hit frame, then the tail eats it away
    a_tail = [-108, -70, -10, 25][i]
    th = [3.6, 3.0, 2.2, 1.2][i]           # crescent thickness
    for k in range(60):
        a = a_tail + (a_lead - a_tail) * k / 59.0
        t = k / 59.0                      # 0 at the tail .. 1 at the lead
        w = th * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.1)))
        for j in range(int(w * 3) + 1):
            r = R - j / 3.0
            x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
            d = j / max(1.0, w * 3)
            if i == 3 and (k + j) % 3: continue
            ch = "H" if (d < 0.25 and t > 0.45 and i < 2) else "8" if d < 0.35 else "7" if d < 0.6 else "6" if d < 0.85 else "5"
            if i >= 2: ch = {"H": "8", "8": "7", "7": "6", "6": "5", "5": "4"}[ch]
            c.put(*P(x, y), ch, over=False)
    # flung frost shards off the trailing edge
    rnd = random.Random(31)
    for k in range([0, 3, 6, 5][i]):
        a = math.radians(a_tail + rnd.uniform(10, 70))
        r = R + 1.5 + rnd.uniform(0, 2.5) * i
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        c.put(*P(x, y), "8" if k % 2 else "6")
        if i >= 2 and k % 2 == 0: c.put(*P(x + 1, y), "5")
    if i == 0:   # the crystal blade's glint at the lead
        a = math.radians(a_lead)
        c.put(*P(cx + (R + 1) * math.cos(a), cy + (R + 1) * math.sin(a)), "H")
    return c.spr()      # no outline: vanilla swing arcs are flat unoutlined crescents


def plate_break_frame(i):
    """FxYsvPlateBreak: one of the Rime Knight's ice plates breaking (it used the Veil Witch's crystal shatter):
    a curved plate of rime cracks across, splits in two, and bursts into flat flakes and powder. Origin = the feet;
    the plate hangs 12 px up (where FxYsvPlates orbits)."""
    c = cv()
    y0 = -12.0
    if i == 0:      # the plate, a crack running across it
        for x in range(-4, 5):
            for y in range(-3, 4):
                if (x / 4.6) ** 2 + (y / 3.6) ** 2 <= 1:
                    c.put(x, int(y0) + y, pick("4567", 0.6 - x * 0.08 - y * 0.12))
        for (x, y) in ((-3, -2), (-2, -1), (-1, -1), (0, 0), (0, 1), (1, 1), (2, 2)):     # a diagonal crack
            c.put(x, int(y0) + y, "1")
        c.put(-2, int(y0) - 2, "H"); c.put(2, int(y0) - 1, "8")
        return outl(c.spr(), "2")
    if i == 1:      # split: two halves pushed apart, bright seam
        for sd in (-1, 1):
            for x in range(0, 5):
                for y in range(-3, 4):
                    if (x / 4.6) ** 2 + (y / 3.6) ** 2 <= 1:
                        c.put(sd * (x + 1), int(y0) + y - (1 if sd > 0 else 0), pick("4567", 0.6 - sd * x * 0.08 - y * 0.12))
        for y in range(-2, 3): c.put(0, int(y0) + y, "G")
        return outl(c.spr(), "2")
    rnd = random.Random(17)
    t = (i - 1) / 3.0
    for k in range(12):         # flakes thrown out in a burst, then falling
        a = rnd.uniform(0, 2 * math.pi)
        r = (3 + 9 * t) * rnd.uniform(0.6, 1.0)
        x, y = r * math.cos(a), y0 + r * math.sin(a) * 0.8 + t * t * 7
        y = min(-1, y)
        ch = "8" if k % 3 == 0 else "6" if k % 3 == 1 else "7"
        c.put(*P(x, y), ch)
        if i < 4 and k % 2 == 0: c.put(*P(x + (1 if math.cos(a) > 0 else -1), y), "5")
    if i == 2: ell(c, 0, y0, 2.5, 2.2, "78H", bias=0.4)
    return c.spr()


def fx_splinter():
    """FxYsvSplinter: the little ice splinters a Veil Witch crystal bursts into (they used her wand's shard bolt).
    A short jagged sliver that tumbles end over end, a pinch of frost dust behind. Centred."""
    out = []
    shapes = [((-2, 0), (-1, 0), (0, -1), (1, -1), (2, -1)),
              ((-1, 1), (0, 0), (0, -1), (1, -2)),
              ((0, 1), (0, 0), (0, -1), (1, -2), (-1, 1)),
              ((-2, -1), (-1, -1), (0, 0), (1, 0), (2, 1))]
    for i in range(4):
        c = cv()
        for j, (x, y) in enumerate(shapes[i]):
            c.put(x, y, "8" if j == len(shapes[i]) - 1 else "7" if j % 2 else "6")
        c.put(-3 - (i % 2), (i % 3) - 1, "5"); c.put(-5, 0, "4")
        out.append(outl(c.spr(), "2"))
    return out


def fx_aurora_mote():
    """FxYsvAuroraMote: the Pale Empress's aurora motes (they used the Hoarmoth's frost mote). A bead of cold light
    trailing a ribbon that shimmers teal -> violet like an aurora. Faces right, centred."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(9):
            x = -1 - k
            y = round(1.3 * math.sin(k * 0.8 + i * 1.57))
            ch = "^" if k < 2 else "%" if k < 4 else "F" if k < 6 else "E" if k < 8 else "D"
            c.put(x, y, ch)
            if k in (2, 5) : c.put(x, y + (1 if y <= 0 else -1), "$" if k == 2 else "E")
        c.put(0, 0, "H"); c.put(1, 0, "G"); c.put(0, -1, "G"); c.put(0, 1, "%")
        if i % 2: c.put(2, 0, "^")
        out.append(c.spr())
    return out


def quake_frame(i):
    """FxYsvQuake: the Rime Colossus slam: a ring of glacier ice heaves up out of the floor (teal, its own body ice) and
    breaks back down. Not the silk-spoked nova of the Widow's Shawl. Centred on the hit; r 5 -> 24, ry 0.42 r."""
    c = cv()
    r = [5, 11, 16, 20, 24][i]
    ry = r * 0.42
    n = int(r * 5) + 8
    rnd = random.Random(7 + i)
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = r * math.cos(a), ry * math.sin(a)
        if i >= 4 and k % 3 == 0: continue
        c.put(*P(x, y), "^" if i < 2 else "%" if i < 4 else "$")
        c.put(*P(x * 0.88, y * 0.88), "%" if i < 3 else "#", over=False)
        # jagged ice heaved up along the ring
        if k % 4 == 0 and i in (1, 2, 3):
            h = [0, 3, 4, 2][i] * (0.6 + 0.4 * rnd.random())
            for j in range(1, int(h) + 1):
                c.put(*P(x, y - j), "^" if j == int(h) else "$" if j > 1 else "#")
    if i < 2: ell(c, 0, 0, 3 + i * 2, 1.6 + i, "$%^H", bias=0.4)
    if i >= 3:
        for k in range(6):
            a = rnd.uniform(0, 2 * math.pi)
            c.put(*P(r * 0.6 * math.cos(a), ry * 0.6 * math.sin(a) - rnd.uniform(1, 3)), "^")
    return c.spr()


def build_fx3(outdir, only=None):
    def want(n): return only is None or n in only
    if want("FxYsvCleave"):
        fx_fixed("FxYsvCleave", [("Slash", [cleave_frame(i) for i in range(4)], [0.117, 0.117, 0.117, 0.067])], outdir, (40, 36), (16, 18),
                 scale=8)
    if want("FxYsvPlateBreak"):
        fx_fixed("FxYsvPlateBreak", [("Play", [plate_break_frame(i) for i in range(5)], [0.05, 0.05, 0.06, 0.08, 0.1])], outdir,
                 (30, 24), (15, 23), scale=8)
    if want("FxYsvSplinter"): centered("FxYsvSplinter", [("Fly", fx_splinter(), [0.05] * 4)], outdir, (12, 6))
    if want("FxYsvAuroraMote"): centered("FxYsvAuroraMote", [("Fly", fx_aurora_mote(), [0.05] * 4)], outdir, (22, 8))
    if want("FxYsvQuake"): centered("FxYsvQuake", [("Play", [quake_frame(i) for i in range(5)], [0.04, 0.05, 0.06, 0.07, 0.09])],
                                    outdir, (52, 24), scale=5)


# ================================================================== v0.10 TREE: 2 NEW T2 + 8 NEW T3
# Every evolution now has exactly one parent:
#   Rimeling  -> Silk Weaver | Rime Lurker        Silk Weaver -> Widow Matron | Loom Widow
#   Hoarmoth  -> Silkmoth | Veil Witch            Rime Lurker -> Hoarfrost Tarantula | Hoarclaw
#   Shardling -> Rime Knight | Shard Hermit       Silkmoth    -> Pale Empress | Glasswing
#                                                 Veil Witch  -> Winter Bride | Snow Wraith
#                                                 Rime Knight -> Rime Colossus | Rime Warden
#                                                 Shard Hermit-> The Geode | Prism Oracle

# ------------------------------------------------------------------ RIME LURKER (T2; Rimeling)
# A trapdoor spider: low and broad, a navy body under a hinged lid of pale frost plates, thick ice legs. Its lid
# swings open to flick frost-silk snares.
def lurker_lid(S, lid=0.0, glow=0):
    """Extra for spider(style="lurker"): the trapdoor lid lifts off the back (hinged at the rear) to show silk."""
    def fn(f, T, A):
        if lid <= 0.05: return
        arx = 3.8 * S * 1.12
        hinge = (A[0] - arx * 0.9, A[1] - 0.6 * S)
        ang = -lid * 70.0
        ln = arx * 1.5
        a = math.radians(ang)
        tip = (hinge[0] + ln * math.cos(a), hinge[1] + ln * math.sin(a))
        nx, ny = math.sin(a), -math.cos(a)
        pts = [hinge, tip, (tip[0] + nx * 2.4 * S, tip[1] + ny * 2.4 * S), (hinge[0] + nx * 2.0 * S, hinge[1] + ny * 2.0 * S)]
        tmp = Canvas()
        poly(tmp, pts, "6", shade=lambda x, y: pick("45678", 0.5 - (y - hinge[1]) * 0.05 - (x - hinge[0]) * 0.03))
        line(tmp, *pts[2], *pts[3], "8")
        for k_, v_ in outl(Spr(tmp.px), "0").px.items(): f.u.put(k_[0], k_[1], v_)
        # the silk nest under the lid glows
        for k in range(2 + glow * 2):
            f.g.put(*P(A[0] - arx * 0.4 + k * 1.3, A[1] - 2.2 * S - (k % 2)), "8" if k % 2 else "G")
    return fn


def build_lurker(outdir):
    S = 1.32
    def Lk(lid=0.0, glow=0, extra=None, **k):
        lx = lurker_lid(S, lid, glow)
        def ex(f, T, A):
            lx(f, T, A)
            if extra: extra(f, T, A)
        k["crouch"] = k.get("crouch", 0.0) + 0.9
        return spider(S=S, style="lurker", extra=ex, **k)
    idle = [Lk(legs=0.0, amp=0.2), Lk(legs=0.6, amp=0.2, breathe=1, dy=0.3, crouch=0.2),
            Lk(legs=1.2, amp=0.2, breathe=1, dy=0.4, crouch=0.3, eye="squint", lid=0.12), Lk(legs=1.8, amp=0.2, lid=0.06)]
    run = [Lk(legs=i * math.pi / 3, amp=1.0, dy=-0.5 * abs(math.sin(i * math.pi / 3)), tilt=2 * math.sin(i * math.pi / 3), breathe=i % 2)
           for i in range(6)]
    def snap(n):
        def fn(f, T, A):
            hx, hy = T[0] + 3.0 * S + 2.0, T[1] + 1.5 * S
            for k, (a, b) in enumerate(((1, -2), (2, 0), (1, 2), (3, -1), (3, 1), (4, 0))[:n]):
                f.g.put(*P(hx + a, hy + b), "8" if k % 2 == 0 else "6")
        return fn
    bite = [Lk(dx=-0.8, crouch=0.6, fang=0.4, legs=0.3, amp=0.2, eye="wide"),
            Lk(dx=-1.8, crouch=1.0, fang=1.0, legs=0.4, amp=0.2, eye="wide", tilt=-6, lid=0.15),
            Lk(dx=1.6, crouch=0.2, fang=1.0, legs=1.4, amp=0.8, tilt=6, eye="wide"),
            Lk(dx=3.4, crouch=0.6, fang=0.0, legs=1.9, amp=0.6, tilt=10, splay=0.3, eye="squint", extra=snap(6)),
            Lk(dx=3.0, crouch=0.5, fang=0.0, legs=2.2, amp=0.4, tilt=8, splay=0.2, eye="squint", extra=snap(3)),
            Lk(dx=1.4, crouch=0.3, fang=0.3, legs=2.6, amp=0.3, tilt=3),
            Lk(dx=0.2, legs=3.0, amp=0.2)]
    def flick(n):
        def fn(f, T, A):
            x0, y0 = A[0] - 3.8 * S, A[1] - 3.0 * S
            for k in range(n):
                f.g.put(*P(x0 + 2 + k * 1.8, y0 - 3 - k * 1.2 + (k % 2)), "8" if k % 2 == 0 else "7")
        return fn
    snare = [Lk(crouch=0.4, lid=0.2, eye="open"),
             Lk(crouch=0.8, lid=0.55, eye="wide", glow=1, dx=-0.4, tilt=-3),
             Lk(crouch=1.0, lid=0.9, eye="wide", glow=2, dx=-0.8, tilt=-6, abd_lift=0.15),
             Lk(crouch=0.6, lid=1.0, eye="wide", glow=2, dx=-0.4, tilt=-8, abd_lift=0.35, extra=flick(3)),
             Lk(crouch=0.2, lid=1.0, eye="squint", glow=1, dx=0.4, tilt=-4, abd_lift=0.4, extra=flick(6)),
             Lk(crouch=0.4, lid=0.7, eye="squint", dx=0.2, abd_lift=0.2, legs=0.6, amp=0.3),
             Lk(crouch=0.3, lid=0.3, legs=1.2, amp=0.2),
             Lk(lid=0.05, legs=1.8, amp=0.2)]
    death = [Lk(dx=-0.6, rear=0.7, splay=0.8, fang=1, eye="wide", tilt=-12, lift=0.8, lid=0.4),
             grounded(Lk(dx=-1, rear=1.0, splay=1.2, fang=1, eye="dead", tilt=-36, crouch=0.8, lid=0.8)),
             grounded(recol(Lk(dx=-1, rear=1.0, splay=1.5, fang=0.5, eye="dead", tilt=-60, crouch=1.0, lid=1.0), {"8": "7", "G": "6"})),
             lurker_corpse(S)]
    knock = Lk(dx=-0.8, rear=0.5, splay=0.6, fang=0.6, eye="squint", tilt=-10, lift=0.5, lid=0.3)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Bite", bite, [0.14, 0.12, 0.06, 0.06, 0.1, 0.1, 0.12]),
             ("Snare", snare, [0.12, 0.12, 0.12, 0.08, 0.1, 0.12, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock)
    sheet("YsvLurker", anims, outdir, scale=6)


def lurker_corpse(S):
    f = Fr()
    ell(f.b, -1.5 * S, -2.0 * S, 5.2 * S, 2.2 * S, "12345", bias=0.0)
    for k in range(4):    # the lid plates spilled off beside it
        ell(f.b, -6.0 * S + k * 2.6 * S, -0.8 - (k % 2), 1.6 * S, 1.0 * S, "45678", bias=0.2)
    for i in range(4):
        bx = -1.0 * S + i * 1.6 * S
        sd = 1 if i % 2 else -1
        pts = [(bx, -3.5 * S), (bx + sd * 1.2 * S, -5.6 * S), (bx + sd * 0.2 * S, -6.8 * S)]
        polyline(f.u, pts, "3")
        f.u.put(*P(*pts[2]), "7")
    f.g.put(*P(4.0 * S, -2.0 * S), "2")
    return f.done()


# ------------------------------------------------------------------ SHARD HERMIT (T2; Shardling)
# The Shardling grown up: a hunched imp in the same black-silk hood with its crystal horn, walking on a crystal-headed
# staff, carrying a cracked geode on its back that is full of ice crystals. Plants geode spires that shoot.
def hermit(dx=0.0, dy=0.0, lean=0.0, legs=0.0, amp=0.0, hands=((-1.0, -10.0), (6.0, -10.0)), staff=((6.0, -2.0), (7.0, -18.0)),
           eye="open", glow=0, crouch=0.0, hood=0.0, pack=0.0, extra=None, k=1.0):
    f = Fr()
    piv = (dx, 0.0)
    def L(x, y): return rot_about((dx + x * k, (y + crouch) * k + dy), piv, lean)
    # legs: short, wrapped in black silk, crystal-shod
    for j, ox in enumerate((-1.8, 1.6)):
        ph = legs + j * math.pi
        fx = dx + ox * k + amp * 1.6 * math.sin(ph)
        fy = -max(0.0, amp * 1.4 * math.cos(ph))
        hip = L(ox * 0.6, -6.4)
        (kx, ky), _ = ik(hip[0], hip[1], fx + 0.6, fy - 1.0, 3.4 * k, 3.2 * k, bend=1)
        lay = f.u if j == 0 else f.b
        tube(lay, [hip, (kx, ky), (fx, fy - 1.0)], [1.2, 1.0, 0.9], "ABC" if j == 0 else "BCD", bias=0.15)
        ell(lay, fx + 0.8, fy - 0.6, 1.6, 0.9, "3456" if j else "2345", bias=0.3)
        lay.put(*P(fx + 1.8, fy - 0.6), "7" if j else "5")
    # the geode pack on the back: dark rock shell cracked open at the top, ice crystals growing out of it
    gc = L(-3.6, -13.0 - pack * 0.4)
    ell(f.u, gc[0], gc[1], 5.4 * k, 5.0 * k, "12234", ang=lean, bias=0.15,
        shader=lambda nu, nv, d, l, ch, x, y: ("3" if (x * 2 + y * 3) % 7 == 0 and d < 0.8 else "4" if nv < -0.6 and nu < 0 else ch))
    for (ox, oy, a, ln, wd) in ((-3.0, -3.0, -135, 4.6, 1.3), (-1.0, -4.4, -105, 5.6, 1.5), (1.4, -4.0, -78, 4.4, 1.2),
                                (-4.4, -0.6, -170, 3.2, 1.0)):
        b = L(-3.6 + ox, -13.0 - pack * 0.4 + oy)
        crystal(f.u, b[0], b[1], a + lean, ln * k * (1.0 + pack * 0.12), wd * k, lit=0.15 + 0.1 * glow)
    # crack in the shell, glowing
    for (ox, oy) in ((-0.6, -1.0), (0.2, 0.0), (-0.2, 1.0), (0.6, 2.0)):
        f.u.put(*P(*L(-3.6 + ox, -13.0 + oy)), "G" if glow else "5")
    # robe: black silk, hunched forward, frost-lace hem
    robe = [L(-1.8, -14.6), L(2.8, -15.2), L(4.4, -10.0), L(3.6, -5.0), L(-2.6, -5.2), L(-3.4, -9.6)]
    poly(f.b, robe, "C", shade=lambda x, y: pick("BCDEF", 0.45 - (x - dx) * 0.08 - (y + 14) * 0.05))
    for j in range(7):
        x, y = L(-2.6 + j, -5.1)
        f.b.put(*P(x, y + 1), "6" if j % 2 else "4")
    line(f.b, *L(-1.0, -13.8), *L(2.4, -7.0), "E")
    # hood over the head (forward and low), crystal horn through it
    hc = L(3.2, -15.6)
    hp = [L(0.0, -14.0), L(0.8, -18.4 - hood * 0.5), L(3.4, -19.4 - hood * 0.6), L(5.8, -17.6), L(6.6, -14.6), L(5.6, -12.6),
          L(3.0, -12.4), L(1.0, -12.8)]
    poly(f.b, hp, "C", shade=lambda x, y: pick("ABCDE", 0.55 - (x - hc[0]) * 0.07 - (y - hc[1]) * 0.14))
    line(f.b, *L(1.0, -18.0), *L(4.6, -18.6), "E")
    poly(f.b, [L(3.4, -16.6), L(6.0, -16.4), L(6.2, -14.0), L(4.0, -13.6)], "1", shade=lambda x, y: "1" if (x + y) % 3 else "2")
    hn = L(2.2, -18.8)
    crystal(f.b, hn[0], hn[1], -72 + lean, 3.4 * k, 0.9 * k, lit=0.1)
    # back arm under the robe edge
    shb = L(-0.4, -13.0)
    (ebx, eby), (hbx, hby) = ik(shb[0], shb[1], dx + hands[0][0] * k, hands[0][1] * k + dy, 3.4 * k, 3.4 * k, bend=-1)
    tube(f.u, [shb, (ebx, eby), (hbx, hby)], [0.9, 0.8, 0.7], "ABC", bias=0.1)
    f.u.put(*P(hbx, hby), "4")
    # staff: silk-bound black wood, an ice crystal head
    tip = None
    if staff is not None:
        (bx_, by_), (tx_, ty_) = staff
        bx_, by_, tx_, ty_ = dx + bx_ * k, by_ * k + dy, dx + tx_ * k, ty_ * k + dy
        line(f.b, bx_, by_, tx_, ty_, "E")
        line(f.b, bx_ + 1, by_, tx_ + 1, ty_, "C", over=False)
        for j in range(1, 4):
            q = j / 4.0
            f.b.put(*P(bx_ + (tx_ - bx_) * q, by_ + (ty_ - by_) * q), "6")
        ang = math.degrees(math.atan2(ty_ - by_, tx_ - bx_))
        tip = crystal(f.b, tx_, ty_, ang, 3.4 * k, 1.1 * k, lit=0.2 + 0.1 * glow)
        f.g.put(*P(*tip), "H" if glow > 1 else "G")
    shf = L(2.4, -13.4)
    (efx, efy), (hfx, hfy) = ik(shf[0], shf[1], dx + hands[1][0] * k, hands[1][1] * k + dy, 3.4 * k, 3.4 * k, bend=1)
    tube(f.b, [shf, (efx, efy), (hfx, hfy)], [1.0, 0.9, 0.8], "BCDE", bias=0.15)
    ell(f.b, hfx, hfy, 1.0, 1.0, "4567", bias=0.3)
    ex, ey = P(*L(4.4, -15.4)); ex2, ey2 = P(*L(5.6, -15.2))
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex2, ey2, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex2, ey2, "G"); f.g.put(ex, ey - 1, "I")
    elif eye == "squint": f.g.put(ex, ey, "I")
    else: f.g.put(ex, ey, "2")
    if extra: extra(f, (hfx, hfy), tip, gc)
    return f.done()


def hermit_corpse():
    f = Fr()
    ell(f.u, -4.0, -3.0, 5.0, 3.0, "1223", bias=0.1)
    for (bx, a, ln) in ((-6, -150, 3.6), (-3, -100, 4.6), (0, -60, 3.2)):
        crystal(f.u, bx, -4.0, a, ln, 1.1)
    poly(f.b, [(-1, -1), (1, -4), (6, -4), (8, -1), (6, 0)], "C", shade=lambda x, y: pick("ABCD", 0.3 - y * 0.05))
    line(f.b, 2, -4, 6, -3.5, "E")
    line(f.b, 3, 0, 12, -1, "C")
    crystal(f.b, 12, -1, -10, 3.0, 1.0)
    f.g.put(5, -2, "2")
    return f.done()


def build_hermit(outdir):
    H = hermit
    REST = dict(hands=((-1.0, -9.6), (7.4, -10.2)), staff=((8.6, -0.6), (7.6, -17.6)))
    idle = [H(**REST), H(hands=((-1.0, -9.3), (7.4, -9.9)), staff=((8.6, -0.6), (7.6, -17.4)), crouch=0.3, pack=0.3),
            H(hands=((-1.0, -9.2), (7.4, -9.8)), staff=((8.6, -0.6), (7.6, -17.3)), crouch=0.5, pack=0.5, eye="squint", glow=1),
            H(**REST, hood=0.8, pack=0.2)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(H(lean=7, legs=ph, amp=1.0, dy=-0.5 * abs(math.sin(ph)), hood=0.5 * math.cos(ph), pack=0.4 * math.sin(ph),
                     hands=((-1.6, -10.0), (6.0 + math.sin(ph), -10.4)), staff=((7.0 + 1.6 * math.sin(ph), -1.0), (5.0 + math.sin(ph), -18.0))))
    def jab_fx(n):
        def fn(f, hand, tip, gc):
            if tip is None: return
            for j in range(n):
                f.g.put(*P(tip[0] + 1 + (j % 3), tip[1] - 1 + j * 0.9 - n * 0.4), "8" if j % 2 == 0 else "6")
        return fn
    jab = [H(hands=((-1.4, -10.4), (3.4, -11.4)), staff=((0.2, -8.6), (7.6, -13.6)), lean=-4, eye="open"),
           H(hands=((-1.8, -10.6), (2.0, -11.6)), staff=((-1.4, -9.6), (6.0, -13.4)), lean=-8, crouch=0.4, eye="wide", glow=1),
           H(hands=((0.4, -10.4), (8.6, -10.6)), staff=((4.4, -10.0), (13.6, -10.8)), lean=10, eye="wide", glow=1),
           H(hands=((0.8, -10.0), (9.4, -10.0)), staff=((5.0, -9.6), (14.6, -9.8)), lean=12, crouch=0.4, eye="squint", extra=jab_fx(4)),
           H(hands=((0.6, -10.0), (9.0, -10.2)), staff=((4.8, -9.6), (14.2, -10.0)), lean=10, crouch=0.3, eye="squint", extra=jab_fx(2)),
           H(hands=((-0.4, -9.8), (7.0, -10.4)), staff=((6.8, -2.0), (8.0, -18.0)), lean=4),
           H(**REST)]
    def rising(n):
        def fn(f, hand, tip, gc):
            for j in range(n):
                f.g.put(*P(gc[0] - 3 + j * 1.6, gc[1] - 7 - (j * 3) % 4), "8" if j % 2 else "G")
        return fn
    def slam(f, hand, tip, gc):
        for j in range(-4, 5):
            f.g.put(*P(12 + j, 0), "7" if j % 2 else "8")
        for j in range(3):
            line(f.g, 10 + j * 2.5, -1, 10.5 + j * 2.5, -3 - j, "6")
    spire = [H(hands=((-1.0, -11.4), (5.6, -12.4)), staff=((5.8, -3.0), (5.2, -19.4)), eye="open", glow=1, pack=0.4),
             H(hands=((0.2, -15.6), (4.6, -17.6)), staff=((4.8, -10.0), (4.0, -26.0)), eye="wide", lean=-5, glow=1, pack=0.8, extra=rising(2)),
             H(hands=((0.4, -17.0), (4.4, -19.0)), staff=((4.6, -11.4), (3.8, -27.4)), eye="wide", lean=-7, glow=2, pack=1.0, hood=1, extra=rising(4)),
             H(hands=((0.4, -17.2), (4.4, -19.2)), staff=((4.6, -11.6), (3.8, -27.6)), eye="wide", lean=-7, glow=2, pack=1.0, hood=1, extra=rising(5)),
             H(hands=((2.6, -10.0), (9.0, -8.0)), staff=((11.4, -0.4), (6.4, -15.8)), eye="wide", lean=12, crouch=1.0, glow=2, pack=0.6, extra=slam),
             H(hands=((2.2, -10.0), (8.6, -8.4)), staff=((11.0, -0.4), (6.0, -16.0)), eye="squint", lean=9, crouch=0.8, glow=1, pack=0.3),
             H(hands=((0.4, -9.8), (7.0, -9.8)), staff=((8.0, -0.6), (6.6, -17.4)), lean=4, crouch=0.3),
             H(**REST)]
    death = [H(hands=((-2.0, -14.0), (5.0, -15.0)), staff=((4.0, -6.0), (10.0, -20.0)), lean=-12, eye="wide", hood=1),
             H(hands=((-1.0, -6.0), (6.0, -5.0)), staff=None, lean=22, crouch=2.0, eye="squint"),
             grounded(H(hands=((0.0, -3.0), (7.0, -2.0)), staff=None, lean=60, crouch=3.0, eye="dead")),
             hermit_corpse()]
    knock = H(hands=((-2.0, -12.0), (5.0, -13.0)), staff=((5.4, -4.0), (8.0, -19.0)), lean=-12, eye="squint", hood=1)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Jab", jab, [0.14, 0.12, 0.06, 0.06, 0.1, 0.12, 0.12]),
             ("Spire", spire, [0.12, 0.12, 0.12, 0.12, 0.06, 0.14, 0.12, 0.12])]
    anims += std_tail(idle[0], death, [0.08, 0.12, 0.16, 0.4], knock)
    sheet("YsvHermit", anims, outdir, scale=6)


# ------------------------------------------------------------------ FX for the new T2s
def snare_web(c, spread=1.0, glint=0, ph=0, col=("6", "4")):
    """A frost-silk snare lying on the floor: radial strands + two rings, rx 7 x ry 3 at spread 1."""
    rx, ry = 7.0 * spread, 3.0 * spread
    for k in range(8):
        a = math.radians(k * 45 + 22 * (ph % 2))
        line(c, 0, 0, rx * math.cos(a), ry * math.sin(a), col[0] if k % 2 else col[1])
    for rr, ch in ((0.55, col[1]), (1.0, col[0])):
        n = int(18 * spread) + 6
        for k in range(n):
            a = 2 * math.pi * k / n
            c.put(*P(rr * rx * math.cos(a), rr * ry * math.sin(a)), ch)
    c.put(0, 0, "7")
    if glint:
        a = math.radians(glint * 70)
        c.put(*P(rx * 0.7 * math.cos(a), ry * 0.7 * math.sin(a)), "8")


def fx_snare():
    land, idle, snap, fade = [], [], [], []
    # Land: a silk glob drops in an arc and splats open
    for i, (h, sp) in enumerate(((7, 0.0), (3, 0.0), (0, 0.45), (0, 0.8))):
        c = cv()
        if sp == 0:
            ell(c, 0, -h, 1.6, 1.4, "5678", bias=0.3)
            c.put(0, -h - 1, "8")
            c.put(-1, -h + 2, "6")
        else:
            snare_web(c, sp)
            ell(c, 0, -0.5, 1.6 * (1 - sp * 0.5), 1.0, "678", bias=0.3)
        land.append(outl(c.spr(), "1"))
    for i in range(2):
        c = cv(); snare_web(c, 1.0, glint=1 + i * 2, ph=0)
        idle.append(outl(c.spr(), "1"))
    # Snap: strands whip up and lash shut into a cone of frost silk around the feet, then frost bursts off
    for i in range(6):
        c = cv()
        if i < 4:
            snare_web(c, 1.0 - i * 0.18, ph=i)
            h = [3, 7, 10, 11][i]
            for k in range(6):
                x0 = (-6 + k * 2.4) * (1.0 - i * 0.2)
                x1 = (-1.2 + k * 0.5)
                line(c, x0, 0, x1, -h, "7" if k % 2 else "6")
            if i >= 2:
                for y in range(-h + 1, 0, 2): line(c, -2.6 + y * -0.15, y, 2.6 + y * 0.15, y, "5")
                c.put(0, -h, "8")
        else:
            for k in range(8 if i == 4 else 5):
                a = math.radians(k * 45 + i * 20)
                r = 4 + (i - 4) * 3
                c.put(*P(r * math.cos(a), -5 + r * 0.6 * math.sin(a)), "8" if k % 2 else "6")
            snare_web(c, 0.4, col=("5", "3"))
        snap.append(outl(c.spr(), "1"))
    for i in range(3):
        c = cv(); snare_web(c, 1.0 - i * 0.15, col=(("5", "3"), ("4", "2"), ("3", "2"))[i])
        fade.append(c.spr())
    return land, idle, snap, fade


def spire_shape(c, h, glow=0, crack=0, ph=0):
    """A geode spire: a dark rock base with a tall ice crystal and two side shards. h = main crystal length."""
    ell(c, 0, -1.6, 5.2, 2.4, "1223", bias=0.2)
    for x in (-4, -1, 2, 4):
        c.put(x, -3 - (x % 2), "3")
    if h <= 0: return
    crystal(c, -2.6, -2.2, -118, h * 0.45, 1.3, lit=0.1)
    crystal(c, 2.4, -2.4, -64, h * 0.5, 1.2, lit=0.15)
    tip = crystal(c, 0.0, -2.4, -90, h, 2.4, lit=0.2 + 0.1 * glow)
    for k in range(int(h * 0.6)):
        y = -3.5 - k
        if (k + ph) % 3 == 0: c.put(0, y, "G" if glow else "6")
    if crack:
        for k in range(crack * 2):
            c.put((k % 2) - 1, -4 - k * 2, "1")
    return tip


def fx_spire():
    grow, idle, flash, crumble = [], [], [], []
    for i, h in enumerate((0, 6, 12, 17, 19)):
        c = cv()
        spire_shape(c, h, glow=1 if i == 4 else 0)
        if i < 2:
            for k in range(5):
                c.put(-5 + k * 2.5, -1 - (k % 2), "7")
        grow.append(outl(c.spr(), "0"))
    for i in range(2):
        c = cv(); spire_shape(c, 18 + i * 0.6, glow=1, ph=i)
        s = outl(c.spr(), "0")
        g = Canvas(); g.put(0, -21 - i, "H" if i else "G"); g.put(0, -20 - i, "G")
        idle.append(merge(s, g.spr()))
    # Flash: the tip flares (drawn on its own, the same origin as the spire, at the tip height ~21 px)
    for i in range(3):
        c = cv()
        r = [2, 4, 3][i]
        for k in range(8):
            a = math.radians(k * 45 + i * 22)
            c.put(*P(r * math.cos(a), -21 + r * math.sin(a)), "8" if k % 2 else "G")
        c.put(0, -21, "H")
        if i < 2: c.put(1, -21, "G"); c.put(-1, -21, "G")
        flash.append(c.spr())
    for i in range(4):
        c = cv()
        spire_shape(c, [16, 11, 5, 0][i], crack=2 - min(2, i))
        for k in range(i * 3):
            c.put(-6 + (k * 5) % 13, -1 - (k % 3), "6" if k % 2 else "4")
        crumble.append(outl(c.spr(), "0"))
    return grow, idle, flash, crumble


def fx_spire_bolt():
    """FxYsvSpireBolt: a tumbling hexagonal geode bead with an ice glow, short frost tail. Faces right, centred."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(4):
            c.put(-2 - k, (k % 2) * (1 if i % 2 else -1) * (k > 1), "6" if k < 2 else "4")
        hexa = [(-1, -2), (1, -2), (2, 0), (1, 2), (-1, 2), (-2, 0)]
        rot = i * 30
        pts = [rot_about(p_, (0, 0), rot) for p_ in hexa]
        poly(c, pts, "5", shade=lambda x, y: pick("4567", 0.4 - (x + y) * 0.25))
        c.put(0, 0, "G"); c.put(*P(*pts[0]), "8")
        out.append(outl(c.spr(), "1"))
    return out


# ------------------------------------------------------------------ LOOM WIDOW (T3; Silk Weaver)
# The Weaver become a drider: her violet stilt-legged spider body (banded abdomen, rime crystals) carries a pale
# woman's torso with long black-silk hair, a cat's cradle of frost silk strung between her hands.
def loom(hands=((-1.0, -3.4), (5.4, -4.0)), cradle=0.8, lash=None, eye="open", hair=0.0, tlean=0.0, glow=0, extra=None, **k):
    S = 1.3
    def ex(f, T, A):
        bx, by = T[0] + 1.4, T[1] - 2.0 * S
        def Q(x, y): return rot_about((bx + x * 1.25, by + y * 1.25), (bx, by), tlean)
        waist, chest, head = Q(0.2, -1.0), Q(0.8, -6.4), Q(1.4, -10.6)
        # hair: long black silk falling down her back
        hp = [Q(-0.6, -12.6), Q(1.6, -12.8), Q(0.4, -9.0), Q(-2.0 - hair, -4.0), Q(-3.6 - hair * 1.4, 0.6), Q(-2.6 - hair, 1.0),
              Q(-1.6, -4.0)]
        poly(f.b, hp, "B", shade=lambda x, y: pick("ABCC", 0.3 - (x - bx) * 0.1 + (0.4 if (x + y) % 4 == 0 else 0)))
        # torso: a bodice of violet silk (the Weaver's), white silk bands, pale shoulders
        tube(f.b, [waist, chest], [2.2, 2.6], "CDEF", bias=0.2)
        for j in range(3):
            y_ = -1.6 - j * 1.8
            line(f.b, *Q(-1.4, y_), *Q(2.4, y_ - 0.3), "h" if j % 2 else "A")
        ell(f.b, *Q(0.9, -7.4), 2.4, 1.3, "gh8", bias=0.3)
        f.b.put(*P(*Q(1.0, -3.2)), "h")
        ell(f.b, head[0], head[1], 1.7, 2.0, "fgh", bias=0.3)
        ell(f.b, *Q(0.6, -11.6), 1.8, 1.0, "ABC", bias=0.1)         # hair over the crown
        for j, ox in enumerate((-0.6, 0.6, 1.8)):                    # rime crystal tiara (the Weaver's crystals)
            crystal(f.b, *Q(ox, -12.2), -90 + (ox - 0.6) * 25 + tlean, 2.0 + (j == 1), 0.5, lit=0.2)
        shb, shf = Q(-0.6, -6.2), Q(1.8, -6.4)
        (eb, hb) = ik(shb[0], shb[1], bx + hands[0][0], by + hands[0][1], 3.4, 3.4, bend=-1)
        tube(f.u, [shb, eb, hb], [0.8, 0.7, 0.6], "1234", bias=0.0)
        (ef, hf) = ik(shf[0], shf[1], bx + hands[1][0], by + hands[1][1], 3.4, 3.4, bend=1)
        tube(f.b, [shf, ef, hf], [0.9, 0.8, 0.7], "fgh", bias=0.2)
        # the cat's cradle: silk strung between her hands
        if cradle > 0:
            for j in range(3):
                o = (j - 1) * 1.4 * cradle
                line(f.g, hb[0], hb[1] + o, hf[0], hf[1] - o, "7" if j != 1 else "8")
            line(f.g, hb[0], hb[1] - 1.2 * cradle, hf[0], hf[1] + 1.2 * cradle, "6")
        if lash is not None:
            pts, _ = catmull([hf] + [(bx + x, by + y) for x, y in lash], [1] * (len(lash) + 1), 0.7)
            for j, (x, y) in enumerate(pts):
                f.g.put(*P(x, y), "8" if j % 3 == 0 else "7")
        ex_, ey_ = P(head[0] + 0.9, head[1] - 0.2)
        if eye == "open": f.g.put(ex_, ey_, "G")
        elif eye == "wide": f.g.put(ex_, ey_, "H"); f.g.put(ex_, ey_ - 1, "I")
        elif eye == "squint": f.g.put(ex_, ey_, "I")
        else: f.g.put(ex_, ey_, "2")
        if glow:
            for j in range(glow * 3):
                a = math.radians(j * 53 + glow * 17)
                f.g.put(*P((hb[0] + hf[0]) / 2 + 3.5 * math.cos(a), (hb[1] + hf[1]) / 2 + 2.5 * math.sin(a)), "8" if j % 2 else "G")
        if extra: extra(f, (hb, hf), head)
    return spider(S=S, weaver=True, style="stilt", extra=ex, **k)


def build_loom(outdir):
    Lw = loom
    idle = [Lw(legs=0.0, amp=0.2), Lw(legs=0.6, amp=0.2, breathe=1, dy=0.3, crouch=0.2, hair=0.3, cradle=0.9),
            Lw(legs=1.2, amp=0.2, breathe=1, dy=0.3, crouch=0.2, hair=0.6, cradle=0.8, eye="squint"), Lw(legs=1.8, amp=0.2, hair=0.3)]
    run = [Lw(legs=i * math.pi / 3, amp=1.0, dy=-0.6 * abs(math.sin(i * math.pi / 3)), tilt=3 * math.sin(i * math.pi / 3), hair=0.8 + 0.4 * math.sin(i),
              tlean=6, hands=((-3.6, -5.0), (3.4, -5.4)), cradle=0.6) for i in range(6)]
    lash = [Lw(hands=((-3.0, -7.0), (2.0, -10.0)), cradle=0.0, tlean=-6, eye="open", lash=[(-1.0, -13.0), (-4.0, -14.0)]),
            Lw(hands=((-3.4, -7.4), (0.6, -12.0)), cradle=0.0, tlean=-12, eye="wide", hair=0.6, lash=[(-3.0, -15.0), (-7.0, -15.0), (-10.0, -12.0)]),
            Lw(hands=((-3.0, -7.0), (5.0, -9.0)), cradle=0.0, tlean=4, eye="wide", hair=0.8, lash=[(9.0, -12.0), (12.0, -14.0), (13.0, -16.0)]),
            Lw(hands=((-2.6, -6.6), (7.0, -5.4)), cradle=0.0, tlean=12, eye="squint", hair=1.0, dx=1.0, lash=[(13.0, -5.0), (19.0, -3.0), (23.0, 1.0)]),
            Lw(hands=((-2.6, -6.6), (6.6, -5.0)), cradle=0.0, tlean=10, eye="squint", hair=1.0, dx=1.0, lash=[(12.0, -3.0), (17.0, 0.0), (21.0, 3.0)]),
            Lw(hands=((-3.0, -6.4), (5.0, -5.6)), cradle=0.3, tlean=4, hair=0.6, lash=[(8.0, -2.0), (10.0, 1.0)]),
            Lw(cradle=0.8, hair=0.3)]
    def threads(n):
        def fn(f, hands, head):
            hb, hf = hands
            for j in range(n):
                for q in range(3):
                    f.g.put(*P(hf[0] + 2 + j * 1.8, hf[1] - q * 1.5 + j * 0.3 * (q - 1)), "8" if (j + q) % 2 else "7")
        return fn
    feed = [Lw(hands=((-3.0, -8.0), (4.0, -8.0)), cradle=1.2, eye="open", glow=1),
            Lw(hands=((-3.0, -11.0), (4.0, -11.6)), cradle=1.5, eye="wide", tlean=-5, glow=1, hair=0.4),
            Lw(hands=((-2.6, -13.0), (4.4, -13.6)), cradle=1.8, eye="wide", tlean=-8, glow=2, hair=0.6, abd_lift=0.2),
            Lw(hands=((-2.6, -13.2), (4.4, -13.8)), cradle=1.8, eye="wide", tlean=-8, glow=3, hair=0.7, abd_lift=0.25),
            Lw(hands=((-1.0, -8.0), (7.0, -8.6)), cradle=0.6, eye="wide", tlean=8, glow=2, hair=1.0, extra=threads(5)),
            Lw(hands=((-1.0, -8.0), (6.6, -8.4)), cradle=0.4, eye="squint", tlean=6, glow=1, hair=0.8, extra=threads(3)),
            Lw(hands=((-2.6, -6.6), (4.6, -6.6)), cradle=0.6, tlean=2, hair=0.5),
            Lw(cradle=0.9, hair=0.3)]
    death = [Lw(dx=-0.6, rear=0.8, splay=0.8, fang=1, eye="wide", tilt=-12, lift=1.0, tlean=-20, hands=((-4, -10), (4, -12)), cradle=0),
             grounded(Lw(dx=-1, rear=1.0, splay=1.2, fang=1, eye="dead", tilt=-36, crouch=0.8, tlean=-40, cradle=0)),
             grounded(recol(Lw(dx=-1, rear=1.0, splay=1.5, eye="dead", tilt=-60, crouch=1.0, tlean=-70, cradle=0), {"7": "6", "8": "7"})),
             loom_corpse()]
    knock = Lw(dx=-0.8, rear=0.5, splay=0.6, fang=0.6, eye="squint", tilt=-10, lift=0.6, tlean=-14, cradle=0.3)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.08] * 6),
             ("Lash", lash, [0.14, 0.12, 0.06, 0.06, 0.1, 0.12, 0.14]),
             ("Feed", feed, [0.12, 0.14, 0.14, 0.12, 0.06, 0.12, 0.14, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("YsvLoom", anims, outdir, scale=4)


def loom_corpse():
    f = Fr()
    S = 1.42
    ell(f.b, -2.0 * S, -2.4 * S, 5.0 * S, 2.4 * S, "DEEF", bias=0.0)
    ell(f.b, 4.0 * S, -1.6 * S, 2.6 * S, 1.6 * S, "DEF", bias=0.0)
    for i in range(4):
        bx = -1.0 * S + i * 1.8 * S
        sd = 1 if i % 2 else -1
        pts = [(bx, -3.5 * S), (bx + sd * 1.4 * S, -6.6 * S), (bx + sd * 0.2 * S, -8.2 * S)]
        polyline(f.u, pts, "C"); f.u.put(*P(*pts[2]), "h")
    ell(f.b, 9.0, -1.4, 3.6, 1.3, "fgh", bias=0.2)
    poly(f.b, [(8, -3), (13, -2), (14, 0), (9, 0)], "B")
    ell(f.b, 12.6, -1.6, 1.4, 1.2, "fgh", bias=0.3)
    f.g.put(13, -2, "2")
    return f.done()


# ------------------------------------------------------------------ GLASSWING (T3; Silkmoth)
# A clearwing moth: wings of clear ice glass (pale rims, black veins, a cold sheen across the panes) on a slim black
# silk body banded with frost, the Silkmoth's silk streamers trailing behind. It fades out of sight to ambush.
def glass_wing(c, S_, f, R, hind=False, sheen=0):
    shape = ([(0.1, 0.0), (-0.1, -0.5), (-0.6, -0.8), (-1.0, -0.5), (-0.9, -0.05), (-0.5, 0.15)] if hind else
             [(0.25, 0.0), (0.2, -0.45), (-0.1, -0.95), (-0.5, -1.05), (-1.1, -0.7), (-1.15, -0.3), (-0.5, 0.05)])
    pts = [(S_[0] + x * R, S_[1] + y * R * f) for x, y in shape]
    if abs(f) < 0.18:
        line(c, S_[0] - R, S_[1] - 0.5, S_[0] + R * 0.2, S_[1] - 0.3, "7")
        return
    def shade(x, y):
        u, v = (x - S_[0]) / R, (y - S_[1]) / (R * abs(f))
        s = (u + v * 0.6 + 0.2 * sheen)
        if abs(s + 0.55) < 0.1: return "7"                 # the sheen streak across the clear glass
        if abs(s + 0.8) < 0.06: return "4"
        return "2" if (int(x * 0.5) + int(y * 0.7)) % 3 else "3"
    poly(c, pts, "1", shade=shade)
    for i in range(len(pts) - 1):
        line(c, *pts[i], *pts[i + 1], "8" if i in (1, 2) else "7")
    for t in (0.35, 0.65):                                    # frost veins
        line(c, S_[0], S_[1], *pts[2 + int(t * 3)], "5")
    line(c, *pts[1], *pts[3], "4")


def glasswing(dx=0.0, dy=0.0, f=1.0, tilt=0.0, ant=0.0, eye="open", tails=0.0, legs=0.0, extra=None, hover=10.0, sheen=0,
              ground=False, reach=0.0):
    f_ = Fr()
    cx, cy = dx, -hover + dy
    if ground: cy = -3.0 + dy
    def L(x, y): return rot_about((cx + x, cy + y), (cx, cy), tilt)
    R, RH = 15.0, 9.0
    # far wings: only their rims show
    tmp = Canvas(); glass_wing(tmp, L(-1.0, -1.8), f * 0.9 + 0.1, R * 0.92, sheen=sheen)
    for k_, v_ in tmp.px.items():
        if v_ in "78": f_.n.put(k_[0], k_[1], "4")
    # silk streamers (the Silkmoth's)
    for sd, (ox, sp) in enumerate(((-8.0, 0.0), (-7.0, 1.5))):
        x, y = L(ox, 1.2)
        for kk in range(8):
            a = math.radians(160 + 16 * math.sin(kk * 0.7 + tails + sp) + tilt * 0.5)
            x += math.cos(a) * 1.2; y += math.sin(a) * 1.2 + 0.25
            f_.u.put(*P(x, y), "8" if kk % 3 == 0 else "E" if kk % 3 == 1 else "7")
    # long slim abdomen, frost bands
    ab = L(-4.6, 1.0)
    ell(f_.b, ab[0], ab[1], 5.6, 1.7, "fgh8", ang=tilt + 6, bias=0.1,
        shader=lambda nu, nv, d, l, ch, x, y: ("C" if abs(nu * 5.0 % 2.0 - 1.0) < 0.22 and d < 0.85 else ch))
    # thin legs: the front pair are long hooked scythes (the slash)
    for kk, (rx_, kx_, ky_, fx_, fy_) in enumerate(((-0.8, -2.0, 3.0, -3.2, 5.4), (0.4, 0.8, 3.4, 1.0, 5.8))):
        sw = 0.6 * math.sin(legs * 2 + kk)
        r0, kn, ft = L(rx_, 1.2), L(kx_ + sw * 0.3, ky_), L(fx_ + sw, fy_)
        line(f_.u, r0[0], r0[1], kn[0], kn[1], "C"); line(f_.u, kn[0], kn[1], ft[0], ft[1], "D")
    r0 = L(1.6, 0.8)
    kn = L(4.0 + reach * 2.0, 2.4 - reach * 1.0)
    ft = L(6.6 + reach * 5.0, 0.6 - reach * 1.2)
    line(f_.b, r0[0], r0[1], kn[0], kn[1], "D"); line(f_.b, kn[0], kn[1], ft[0], ft[1], "7")
    f_.b.put(*P(*ft), "8")
    th = L(0.4, -0.2)
    ell(f_.b, th[0], th[1], 2.4, 2.2, "fgh8", ang=tilt, bias=0.2)
    hd = L(3.0, -0.8)
    ell(f_.b, hd[0], hd[1], 1.6, 1.5, "BCDE", ang=tilt, bias=0.15)
    # clubbed antennae
    for kk, (a0, ln, col) in enumerate(((-62 + ant * 12, 7, "6"), (-40 + ant * 10, 6, "4"))):
        x, y = L(3.4, -2.0)
        a = a0 + tilt
        pts = [(x, y)]
        for j in range(ln):
            a -= 4
            x += math.cos(math.radians(a)); y += math.sin(math.radians(a))
            pts.append((x, y))
        polyline(f_.b if kk == 0 else f_.u, pts, col)
        (f_.g if kk == 0 else f_.u).put(*P(*pts[-1]), "8" if kk == 0 else "6")
    # near wings over the body (glass)
    glass_wing(f_.b, L(-2.0, -0.4), f, RH, hind=True, sheen=sheen)
    glass_wing(f_.b, L(-0.6, -1.6), f, R, sheen=sheen)
    ex, ey = P(*L(3.8, -1.0))
    if eye == "open": f_.g.put(ex, ey, "G")
    elif eye == "wide": f_.g.put(ex, ey, "H"); f_.g.put(ex, ey - 1, "G")
    elif eye == "squint": f_.g.put(ex, ey, "I")
    else: f_.g.put(ex, ey, "2")
    if extra: extra(f_, (cx, cy), ft)
    return f_.done()


def build_glasswing(outdir):
    G = glasswing
    idle = [G(f=1.0), G(f=0.7, dy=0.5, tails=0.6, ant=0.3, sheen=1), G(f=0.4, dy=1.0, tails=1.2, ant=0.5, legs=1, sheen=2),
            G(f=0.8, dy=0.5, tails=1.8, ant=0.3, eye="squint", sheen=3)]
    run = [G(f=[1.0, 0.45, -0.3, -0.85, -0.3, 0.5][i], tilt=10, dx=0.5, dy=[0, 0.5, 1.0, 1.3, 0.7, 0.2][i], tails=i * 0.8,
             ant=-0.6, legs=1, sheen=i % 4) for i in range(6)]
    def swish(n):
        def fn(f, C, ft):
            for j in range(n):
                a = math.radians(-70 + j * 22)
                f.g.put(*P(ft[0] - 2 + 6 * math.cos(a), ft[1] + 3 + 6 * math.sin(a)), "8" if j % 2 else "7")
        return fn
    def streak(f, C, ft):
        for j in range(3):
            line(f.n, C[0] - 12 - j, C[1] - 2 + j * 2, C[0] - 7, C[1] - 2 + j * 2, "4")
    slash = [G(f=1.1, tilt=-6, dx=-0.6, ant=0.5, eye="wide"),
             G(f=1.2, tilt=-12, dx=-1.6, dy=-0.6, ant=0.8, eye="wide", tails=0.6, reach=-0.4),
             G(f=0.6, tilt=10, dx=2.6, dy=1.0, ant=-0.6, eye="wide", tails=1.2, reach=0.6, extra=streak),
             G(f=-0.6, tilt=16, dx=4.4, dy=1.6, ant=-0.8, eye="squint", tails=1.8, reach=1.0, extra=swish(6)),
             G(f=-0.4, tilt=12, dx=4.0, dy=1.4, ant=-0.6, eye="squint", tails=2.4, reach=0.8, extra=swish(3)),
             G(f=0.4, tilt=4, dx=2.0, dy=0.6, tails=3.0, reach=0.3),
             G(f=0.9, tails=3.6)]
    def shimmer(n, ph):
        def fn(f, C, ft):
            for j in range(n):
                a = math.radians(j * 41 + ph * 25)
                r = 4 + (j % 4) * 2.5
                f.g.put(*P(C[0] - 2 + r * math.cos(a), C[1] - 3 + r * 0.8 * math.sin(a)), "8" if j % 3 == 0 else "G" if j % 3 == 1 else "7")
        return fn
    fade = [G(f=1.0, ant=0.4, eye="open", sheen=1),
            G(f=1.2, dy=-0.6, ant=0.8, eye="wide", sheen=2, extra=shimmer(4, 0)),
            G(f=0.2, dy=-0.4, ant=0.6, eye="wide", sheen=3, extra=shimmer(8, 1)),
            G(f=-0.7, dy=0.4, ant=0.2, eye="squint", sheen=0, extra=shimmer(12, 2)),
            G(f=0.3, dy=0.2, ant=0.0, eye="squint", sheen=1, extra=shimmer(8, 3)),
            G(f=0.9, ant=0.2, sheen=2, extra=shimmer(3, 4)),
            G(f=1.0, sheen=3)]
    death = [G(f=1.2, tilt=-20, dy=-0.5, eye="wide", ant=1.0, tails=1.0),
             G(f=-0.5, tilt=30, dy=4.0, eye="dead", ant=-1.0, tails=2.0),
             G(f=-0.8, tilt=50, hover=4.0, dy=0.5, eye="dead", ant=-1.4, tails=3.0),
             grounded(recol(G(ground=True, f=-0.3, eye="dead", tilt=6, tails=2.0), {"G": "4", "H": "5", "I": "3"}))]
    knock = G(f=1.2, tilt=-22, dx=-1.0, dy=-0.5, eye="squint", ant=1.0, tails=1.0)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.06] * 6),
             ("Slash", slash, [0.12, 0.12, 0.06, 0.06, 0.1, 0.12, 0.12]),
             ("Fade", fade, [0.1, 0.1, 0.1, 0.12, 0.1, 0.1, 0.1])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.14, 0.4], knock)
    sheet("YsvGlasswing", anims, outdir, scale=4)


# ------------------------------------------------------------------ SNOW WRAITH (T3; Veil Witch)
# What the Veil Witch becomes when the gown is gone: a legless shroud of midnight silk, frost-white tatters streaming
# behind, the witch's moth wings grown ragged and spread, a violet-black hood over a pale mask, long ice claws.
def wraith(dx=0.0, dy=0.0, lean=0.0, sway=0.0, hands=((-5.0, -16.0), (6.0, -16.0)), wing=0.0, eye="open", hover=4.0,
           claw=0.0, swirl=0, extra=None, sink=0.0, ground=False):
    f = Fr()
    piv = (dx, -hover)
    def L(x, y): return rot_about((dx + x, y - hover + dy + sink), piv, lean)
    # ragged frost-moth wings behind (far + near), spread by `wing`
    for sd, lay in ((1, f.u), (0, f.u)):
        sp = (1.15 + wing * 0.35) * (-0.7 if sd else 1.0)
        root = L(-1.0, -22.0)
        pts = [root, L(-5.0 * sp, -31.0 - wing * 2), L(-11.0 * sp, -27.0 - wing), L(-13.0 * sp, -20.0), L(-10.6 * sp, -18.0),
               L(-12.0 * sp, -13.0 + wing), L(-8.4 * sp, -14.0), L(-7.6 * sp, -9.0 + wing), L(-2.4, -15.0)]
        if sd:
            poly(lay, pts, "3", shade=lambda x, y: pick("2345", 0.3 - math.hypot(x - root[0], y - root[1]) / 16.0))
            for i in range(1, len(pts) - 1):
                line(lay, *pts[i], *pts[i + 1], "6")
        else:
            poly(lay, pts, "5", shade=lambda x, y: pick("34567", 0.6 - math.hypot(x - root[0], y - root[1]) / 14.0 + (0.25 if (x * 2 + y) % 7 == 0 else 0)))
            for i in range(1, len(pts) - 1):
                line(lay, *pts[i], *pts[i + 1], "7" if i % 2 else "8")
            line(lay, *root, *pts[3], "1"); line(lay, *root, *pts[5], "1")
            ex_, ey_ = L(-8.0 * sp, -24.0 - wing * 0.8)
            lay.put(*P(ex_, ey_), "1"); lay.put(*P(ex_ + 1, ey_), "1"); lay.put(*P(ex_, ey_ + 1), "A")
    # the shroud: midnight silk tapering to tatters that stream back off the floor
    sw = sway
    body = [L(-3.0, -22.0), L(3.8, -22.4), L(4.8, -15.0), L(2.6, -8.0 + sw * 0.3), L(0.6 - sw, -2.0), L(-1.4 - sw * 1.5, -4.6),
            L(-3.0 - sw * 2.0, -1.6), L(-4.6 - sw * 2.4, -5.0), L(-5.2 - sw, -8.0), L(-7.4 - sw * 1.6, -7.6), L(-4.6, -13.0)]
    poly(f.b, body, "2", shade=lambda x, y: pick("11234", 0.35 - (x - dx) * 0.1 - (y + 20 + hover) * 0.02 + (0.3 if (x + 2 * y) % 6 == 0 else 0)))
    for i in (4, 5, 6, 7, 8, 9):
        f.b.put(*P(*body[i]), "7")
    for i in range(4, 9):
        line(f.b, *body[i], *body[i + 1], "6" if i % 2 else "5")
    # a mantle of frost tatters at the shoulders
    for j in range(6):
        x, y = L(-3.0 + j * 1.3, -20.4)
        f.b.put(*P(x, y), "7" if j % 2 else "8"); f.b.put(*P(x, y + 1 + (j % 2)), "6")
    # hood (the witch's violet-black) over a pale mask
    hd = L(1.6, -25.4)
    hp = [L(-2.4, -22.0), L(-1.6, -27.6), L(1.2, -29.8), L(4.2, -28.0), L(5.2, -24.6), L(4.4, -21.6)]
    poly(f.b, hp, "C", shade=lambda x, y: pick("ABCDE", 0.6 - (x - hd[0]) * 0.1 - (y - hd[1]) * 0.12))
    ell(f.b, *L(2.6, -25.0), 1.5, 2.0, "fgh", ang=lean, bias=0.3)
    for j, ox in enumerate((-0.4, 1.2, 2.8)):        # the witch's icicle crown, cracked
        crystal(f.b, *L(ox, -28.6 - (j == 1) * 0.6), -90 + (ox - 1.2) * 22 + lean, 2.6 + (j == 1), 0.5, lit=0.1, ramp="3456", ridge="6")
    # arms + ice claws
    for sd, (hx, hy) in enumerate(hands):
        sh = L(-1.0 + sd * 3.4, -20.6)
        (e_, h_) = ik(sh[0], sh[1], dx + hx, hy - hover + dy, 4.0, 4.0, bend=1 if sd else -1)
        lay = f.b if sd else f.u
        tube(lay, [sh, e_, h_], [1.2, 1.0, 0.8], "1234" if sd else "0123", bias=0.2)
        for c_ in range(3):
            a = math.radians((-30 + c_ * 30) + (80 if claw > 0.5 else 30) * (1 if sd else 1) + lean)
            ln = 3.2 + claw
            line(f.g if sd else lay, h_[0], h_[1], h_[0] + ln * math.cos(a), h_[1] + ln * math.sin(a), "8" if sd else "6")
    ex, ey = P(*L(3.0, -25.4))
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex - 1, ey, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex - 1, ey, "G"); f.g.put(ex, ey - 1, "I")
    elif eye == "squint": f.g.put(ex, ey, "I")
    else: f.g.put(ex, ey, "2")
    if swirl:
        for j in range(swirl * 4):
            a = math.radians(j * 31 + swirl * 40)
            r = 4 + (j % 5) * 2.2
            f.g.put(*P(dx + 2 + r * math.cos(a), -32 - hover + r * 0.4 * math.sin(a)), "8" if j % 3 == 0 else "7" if j % 3 == 1 else "6")
    if extra: extra(f, hands, hd)
    return f.done()


def build_wraith(outdir):
    W = wraith
    idle = [W(), W(dy=-0.6, sway=0.5, wing=0.2), W(dy=-1.0, sway=1.0, wing=0.4, eye="squint"), W(dy=-0.5, sway=0.5, wing=0.2)]
    run = [W(lean=8, sway=1.6 + 0.6 * math.sin(i * math.pi / 3), wing=0.5 + 0.3 * math.sin(i * math.pi / 3), dy=-0.6 * abs(math.sin(i * math.pi / 3)),
             hands=((-6.0, -14.0), (5.0, -15.0))) for i in range(6)]
    def rake(n):
        def fn(f, hands, hd):
            for j in range(n):
                line(f.g, 9 + j * 2, -20 + j, 6 + j * 2, -9 + j, "8" if j % 2 == 0 else "6")
        return fn
    claw = [W(hands=((-5.0, -18.0), (4.0, -24.0)), lean=-4, eye="open", claw=0.4),
            W(hands=((-5.4, -19.0), (3.0, -29.0)), lean=-9, eye="wide", claw=1.0, wing=0.5),
            W(hands=((-5.0, -18.0), (10.0, -20.0)), lean=6, eye="wide", claw=1.0, wing=0.8, dx=1.0),
            W(hands=((-4.4, -16.0), (12.0, -10.0)), lean=12, eye="squint", claw=1.0, wing=1.0, dx=2.0, extra=rake(4)),
            W(hands=((-4.4, -16.0), (11.0, -8.0)), lean=10, eye="squint", claw=0.8, wing=0.8, dx=1.6, extra=rake(2)),
            W(hands=((-5.0, -16.0), (7.0, -13.0)), lean=4, wing=0.4, dx=0.6),
            W()]
    mael = [W(hands=((-6.0, -20.0), (6.0, -20.0)), eye="open", wing=0.4),
            W(hands=((-7.0, -27.0), (5.0, -29.0)), eye="wide", wing=0.8, lean=-4, swirl=1),
            W(hands=((-6.4, -31.0), (4.0, -33.0)), eye="wide", wing=1.1, lean=-6, swirl=2, dy=-1.0),
            W(hands=((-6.0, -32.0), (3.6, -34.0)), eye="wide", wing=1.2, lean=-6, swirl=3, dy=-1.4),
            W(hands=((-6.0, -32.0), (3.6, -34.0)), eye="wide", wing=1.3, lean=-6, swirl=4, dy=-1.6),
            W(hands=((-3.0, -18.0), (11.0, -16.0)), eye="wide", wing=1.0, lean=10, swirl=2, claw=1.0),
            W(hands=((-4.0, -17.0), (8.0, -15.0)), eye="squint", wing=0.6, lean=4),
            W()]
    death = [W(hands=((-7.0, -26.0), (6.0, -28.0)), lean=-12, eye="wide", wing=1.2, sway=1.0),
             W(hands=((-4.0, -12.0), (5.0, -10.0)), lean=16, eye="squint", wing=0.6, sink=6.0, hover=2.0),
             grounded(W(hands=((-3.0, -6.0), (6.0, -5.0)), lean=50, eye="dead", wing=0.2, sink=10.0, hover=0.0)),
             wraith_corpse()]
    knock = W(hands=((-6.0, -22.0), (5.0, -23.0)), lean=-12, eye="squint", wing=0.9, sway=1.0)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.08] * 6),
             ("Claw", claw, [0.14, 0.12, 0.06, 0.06, 0.1, 0.12, 0.12]),
             ("Maelstrom", mael, [0.12, 0.12, 0.12, 0.12, 0.08, 0.1, 0.14, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("YsvWraith", anims, outdir, scale=4)


def wraith_corpse():
    f = Fr()
    poly(f.u, [(-12, 0), (-8, -4), (-2, -5), (3, -3), (1, 0)], "5", shade=lambda x, y: pick("3456", 0.3 + x * 0.04))
    line(f.u, -12, 0, -8, -4, "7")
    poly(f.b, [(-6, 0), (-4, -3), (4, -3.5), (8, -1), (6, 0)], "2", shade=lambda x, y: pick("1234", 0.3 - y * 0.08))
    for x in range(-6, 7, 2): f.b.put(x, -1, "6")
    ell(f.b, 7.0, -2.0, 1.6, 1.4, "fgh", bias=0.3)
    poly(f.b, [(5, -3), (8, -4.5), (10, -2), (8, -1)], "C")
    for i in range(3): crystal(f.b, 10 + i * 1.2, -0.5, -40 - i * 40, 2.2, 0.5)
    f.g.put(7, -2, "2")
    return f.done()


# ------------------------------------------------------------------ RIME WARDEN (T3; Rime Knight)
# The knight grown into a warden of the Widow's gate: heavier gunmetal plate (KNIGHT remap), a horned great-helm with a
# frost crest, a white fur mantle, a flanged mace, and a great round shield rimmed with ice spikes that he throws.
def warden_shield(c, cx, cy, r, spin=0.0, tilt=1.0):
    """Round steel shield, ice-spiked rim, crystal boss; tilt < 1 squashes it toward edge-on."""
    def shade(nu, nv, d, l, ch, x, y):
        if d > 0.72: return "6" if (nu * 0.7 + nv) < 0 else "4"
        return ch
    ell(c, cx, cy, r * tilt, r, "1234", bias=0.25, shader=shade)
    for k in range(8):
        a = math.radians(k * 45 + spin)
        x0, y0 = cx + r * tilt * math.cos(a), cy + r * math.sin(a)
        c.put(*P(cx + (r + 1.4) * tilt * math.cos(a), cy + (r + 1.4) * math.sin(a)), "h")
        c.put(*P(x0, y0), "g")
    ell(c, cx, cy, 1.4 * tilt, 1.4, "fgh", bias=0.4)
    line(c, cx - r * 0.6 * tilt, cy, cx + r * 0.6 * tilt, cy, "3")


def warden(dx=0.0, dy=0.0, lean=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), hands=((5.0, -15.0), (6.0, -14.0)), mace=None,
           shield=True, sh_pos=None, eye="open", cape=0.0, crouch=0.0, glow=0, extra=None):
    """hands: (shield hand, mace hand). mace: (grip, head) points. sh_pos: shield centre (default at the shield hand)."""
    f = Fr()
    k = 1.42
    piv = (dx, 0.0)
    def L(x, y): return rot_about((dx + x * k, (y + crouch) * k + dy), piv, lean)
    hip, chest, head = L(0.0, -8.4), L(0.6, -13.6), L(1.2, -18.8)
    # cape of violet silk under a white fur mantle
    cp = [L(-1.0, -16.6), L(-4.6 - cape * 0.8, -11.0), L(-6.6 - cape * 2.0, -2.4), L(-5.2 - cape * 2.4, -0.4),
          L(-2.4 - cape, -1.4), L(-0.6, -9.0)]
    poly(f.u, cp, "C", shade=lambda x, y: pick("ABCDE", 0.2 + (x - dx) * 0.06 + (0.4 if (x * 2 + y) % 7 == 0 else 0)))
    line(f.u, *cp[2], *cp[3], "g")
    for j, (fx, fy) in enumerate(feet):
        h_ = L(-1.4 + j * 2.4, -8.0)
        foot = (dx + fx, fy)
        (kx, ky), _ = ik(h_[0], h_[1], foot[0], foot[1] - 1.4, 4.6 * k, 4.4 * k, bend=1)
        lay = f.u if j == 0 else f.b
        ramp = "1223" if j == 0 else "2345"
        tube(lay, [h_, (kx, ky)], [2.2, 1.9], ramp, bias=0.2)
        tube(lay, [(kx, ky), (foot[0], foot[1] - 1.4)], [1.9, 1.7], ramp, bias=0.2)
        ell(lay, foot[0] + 1.0, foot[1] - 1.1, 2.6, 1.3, ramp, bias=0.2)
        lay.put(*P(kx + 0.6, ky - 0.6), "7" if j else "4")
    # mace arm (behind) + mace
    shb = L(-1.8, -14.8)
    (eb, hb) = ik(shb[0], shb[1], dx + hands[1][0], hands[1][1] + dy + crouch * k, 4.0 * k, 3.8 * k, bend=-1)
    tube(f.u, [shb, eb, hb], [1.8, 1.5, 1.4], "2345", bias=0.2)
    if mace is not None:
        (gx, gy), (mx, my) = mace
        gx, gy, mx, my = dx + gx, gy + dy, dx + mx, my + dy
        line(f.u, gx, gy, mx, my, "2"); line(f.u, gx + 1, gy, mx + 1, my, "3", over=False)
        ell(f.u, mx, my, 2.6, 2.6, "34567", bias=0.3)
        for a in range(0, 360, 60):
            crystal(f.u, mx, my, a, 3.6, 0.8, lit=0.2, ramp="hhh8", ridge="8")
        f.g.put(*P(mx, my), "G" if glow else "6")
    # torso: breastplate, belt, silk tabard
    tube(f.b, [hip, chest], [3.4, 4.0], "2345", bias=0.2)
    ell(f.b, chest[0] + 0.4, chest[1] + 0.4, 4.4, 3.8, "23456", ang=lean, bias=0.25)
    line(f.b, *L(-2.4, -11.6), *L(3.4, -11.6), "G")
    tab = [L(-1.0, -11.4), L(2.6, -11.4), L(2.2, -4.6), L(0.8, -3.8), L(-0.6, -4.6)]
    poly(f.b, tab, "C", shade=lambda x, y: pick("BCDE", 0.4 - (x - dx) * 0.1))
    hourglass(f.g, *L(0.8, -7.2), s=2, bright=glow > 0)
    # white fur mantle over the shoulders
    for j in range(9):
        a = math.radians(200 + j * 18)
        x, y = L(0.4 + 4.6 * math.cos(a), -15.0 + 2.0 * math.sin(a))
        ell(f.b, x, y, 1.3, 1.1, "fgh8", bias=0.3)
    # great-helm (flat-topped, a dark visor slit) under a fan crest of frost crystals, two short violet horns
    hpts = [(-2.6, -3.6), (2.8, -3.8), (3.4, 2.6), (1.0, 3.6), (-2.8, 3.0)]
    poly(f.b, [rot_about((head[0] + x, head[1] + y), head, lean) for x, y in hpts], "4",
         shade=lambda x, y: pick("23456", 0.5 - (x - head[0]) * 0.12 - (y - head[1]) * 0.08))
    for v_ in (0.2, 1.2, 2.2, 3.0):
        f.b.put(*P(*rot_about((head[0] + v_, head[1] + 0.3), head, lean)), "1")
    for sd in (-1, 1):
        b = rot_about((head[0] + 0.2 + sd * 2.6, head[1] - 2.6), head, lean)
        crystal(f.b, b[0], b[1], -90 + sd * 50 + lean, 3.2, 0.8, lit=0.1, ramp="DEF", ridge="F")
    for j in range(5):
        crystal(f.b, *rot_about((head[0] - 1.6 + j * 0.9, head[1] - 3.6), head, lean), -128 + j * 18 + lean, 3.0 + (j == 2) * 1.6, 0.5, lit=0.3,
                ramp="fgh8", ridge="8")
    vx, vy = P(*rot_about((head[0] + 1.4, head[1] + 0.3), head, lean))
    if eye == "open": f.g.put(vx, vy, "G"); f.g.put(vx + 1, vy, "G")
    elif eye == "wide": f.g.put(vx, vy, "H"); f.g.put(vx + 1, vy, "G")
    elif eye == "squint": f.g.put(vx, vy, "I")
    else: f.g.put(vx, vy, "2")
    # shield arm (front) + the round shield held before him
    shf = L(2.6, -14.8)
    (ef, hf) = ik(shf[0], shf[1], dx + hands[0][0], hands[0][1] + dy + crouch * k, 4.0 * k, 3.8 * k, bend=1)
    tube(f.b, [shf, ef, hf], [1.9, 1.6, 1.5], "2345", bias=0.25)
    if shield:
        sx, sy = sh_pos if sh_pos is not None else (hf[0] + 1.0, hf[1] + 1.0)
        tmp = Canvas(); warden_shield(tmp, sx, sy, 6.2, tilt=0.55)
        for k_, v_ in outl(Spr(tmp.px), "0").px.items(): f.l.put(k_[0], k_[1], v_)
    if glow:
        for j in range(glow * 3):
            a = math.radians(j * 47 + glow * 30)
            f.g.put(*P(chest[0] + 8 * math.cos(a), chest[1] + 2 + 6 * math.sin(a)), "7" if j % 2 else "G")
    if extra: extra(f, hf, hb, head)
    return f.done()


def warden_corpse():
    f = Fr()
    poly(f.u, [(-12, 0), (-8, -3), (2, -3.5), (5, -1), (3, 0)], "C", shade=lambda x, y: pick("ABCD", 0.3 + x * 0.03))
    ell(f.b, -1.0, -2.6, 7.0, 2.6, "34567", bias=0.2)
    ell(f.b, 7.0, -2.4, 3.0, 2.4, "34567", bias=0.3)
    f.b.put(7, -2, "1"); f.b.put(8, -2, "1")
    tmp = Canvas(); warden_shield(tmp, -9, -2.5, 4.0, tilt=1.0)
    for k_, v_ in outl(Spr(tmp.px), "0").px.items(): f.b.put(k_[0], k_[1], v_)
    for j in range(5): ell(f.b, -3 + j * 2, -4.6, 1.2, 1.0, "fgh8", bias=0.3)
    return f.done()


def build_warden(outdir):
    Wd = warden
    REST = dict(hands=((7.0, -14.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)))
    idle = [Wd(**REST), Wd(hands=((7.0, -13.6), (-4.0, -11.6)), mace=((-4.0, -11.6), (-6.0, -3.6)), cape=0.3, crouch=0.3),
            Wd(hands=((7.0, -13.4), (-4.0, -11.4)), mace=((-4.0, -11.4), (-6.0, -3.4)), cape=0.6, crouch=0.4, eye="squint"),
            Wd(**REST, cape=0.3)]
    run = []
    for i in range(6):
        ph = i * math.pi / 3
        run.append(Wd(lean=5, dy=-0.6 * abs(math.sin(ph)), feet=((-4.0 - 3.6 * math.sin(ph), -max(0, 1.6 * math.cos(ph))),
                                                              (4.0 + 3.6 * math.sin(ph), -max(0, -1.6 * math.cos(ph)))),
                      hands=((7.4, -14.6), (-4.6, -13.0)), mace=((-4.6, -13.0), (-8.0, -6.0)), cape=1.0 + 0.5 * math.sin(ph)))
    def smear(f, hf, hb, head):
        for j in range(9):
            a = math.radians(-120 + j * 18)
            f.n.put(*P(2 + 19 * math.cos(a), -14 + 19 * math.sin(a)), "6", over=False)
    def impact(n):
        def fn(f, hf, hb, head):
            for j in range(n):
                f.g.put(*P(15 + (j % 3) - 1, -1 - j), "8" if j % 2 == 0 else "6")
            for j in range(-3, 4): f.g.put(*P(15 + j * 1.5, 0), "7")
        return fn
    smash = [Wd(hands=((7.0, -14.0), (-2.0, -18.0)), mace=((-2.0, -18.0), (-8.0, -24.0)), lean=-4),
             Wd(hands=((6.4, -14.4), (-2.0, -24.0)), mace=((-2.0, -24.0), (-9.0, -29.0)), lean=-9, crouch=0.4, eye="wide"),
             Wd(hands=((6.0, -14.6), (0.0, -26.0)), mace=((0.0, -26.0), (-5.0, -33.0)), lean=-11, crouch=0.6, eye="wide", glow=1),
             Wd(hands=((6.6, -12.0), (10.0, -17.0)), mace=((10.0, -17.0), (17.0, -12.0)), lean=8, eye="wide", extra=smear),
             Wd(hands=((6.0, -10.0), (11.0, -8.0)), mace=((11.0, -8.0), (15.0, -2.6)), lean=13, crouch=0.8, eye="squint", extra=impact(4)),
             Wd(hands=((6.0, -10.4), (10.6, -8.6)), mace=((10.6, -8.6), (14.6, -3.0)), lean=10, crouch=0.6, extra=impact(2)),
             Wd(hands=((6.6, -12.4), (4.0, -10.0)), mace=((4.0, -10.0), (2.0, -2.0)), lean=4),
             Wd(**REST)]
    def flung(f, hf, hb, head):
        for j in range(4):
            f.g.put(*P(hf[0] + 3 + j * 2, hf[1] - 1 + (j % 2)), "8" if j % 2 else "6")
    hurl = [Wd(hands=((4.0, -15.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=-3, eye="open"),
            Wd(hands=((-2.0, -16.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=-10, crouch=0.4, eye="wide",
               sh_pos=(-4.0, -18.0)),
            Wd(hands=((-5.0, -17.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=-14, crouch=0.6, eye="wide", glow=1,
               sh_pos=(-7.0, -19.0)),
            Wd(hands=((-5.4, -17.4), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=-15, crouch=0.7, eye="wide", glow=2,
               sh_pos=(-7.4, -19.4)),
            Wd(hands=((13.0, -15.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=12, eye="squint", shield=False, extra=flung),
            Wd(hands=((12.0, -14.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=8, eye="squint", shield=False),
            Wd(hands=((9.0, -15.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=2, eye="open", shield=False),
            Wd(hands=((10.0, -16.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=0, eye="wide", shield=False),
            Wd(hands=((9.0, -15.0), (-4.0, -12.0)), mace=((-4.0, -12.0), (-6.0, -4.0)), lean=-4, eye="open", sh_pos=(10.0, -15.0))]
    death = [Wd(hands=((6.0, -18.0), (-4.0, -16.0)), mace=((-4.0, -16.0), (-10.0, -20.0)), lean=-12, eye="wide", cape=1.0),
             Wd(hands=((7.0, -8.0), (-3.0, -6.0)), lean=20, crouch=3.0, eye="squint", cape=1.5),
             grounded(Wd(hands=((8.0, -4.0), (-2.0, -3.0)), lean=58, crouch=4.0, eye="dead", cape=1.8, shield=False)),
             warden_corpse()]
    knock = Wd(hands=((5.0, -16.0), (-5.0, -14.0)), mace=((-5.0, -14.0), (-9.0, -8.0)), lean=-10, eye="squint", cape=1.0)
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.09] * 6),
             ("Smash", smash, [0.14, 0.12, 0.12, 0.05, 0.08, 0.12, 0.12, 0.12]),
             ("Hurl", hurl, [0.1, 0.12, 0.12, 0.08, 0.06, 0.2, 0.2, 0.2, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.4], knock)
    sheet("YsvWarden", anims, outdir, scale=4, remap=KNIGHT)


# ------------------------------------------------------------------ HOARFROST TARANTULA (T3; Rime Lurker)
# The Lurker grown huge and shaggy: a round mass of white frost fur, thick hairy legs banded in ice, the Lurker's
# trapdoor lid now a ridge of frost plates down its back, a cluster of glowing eyes. Burrows and erupts under the hero.
def fur(c, cx, cy, rx, ry, ramp, ang=0.0, seed=0, tuft=1.0):
    ell(c, cx, cy, rx, ry, ramp, ang=ang, bias=0.2,
        shader=lambda nu, nv, d, l, ch, x, y: (ramp[0] if (x * 3 + y * 7 + seed) % 5 == 0 and d > 0.4 else ch))
    r = random.Random(seed)
    n = int((rx + ry) * 2 * tuft)
    for k in range(n):
        a = 2 * math.pi * k / n + r.uniform(-0.1, 0.1)
        if math.sin(a) > 0.6: continue
        x, y = cx + (rx + 0.8) * math.cos(a), cy + (ry + 0.8) * math.sin(a)
        c.put(*P(x, y), ramp[-1] if math.sin(a) < -0.2 else ramp[len(ramp) // 2])


def tarantula(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, amp=0.0, crouch=0.0, rear=0.0, fang=0.0, eye="open", sink=0.0, splay=0.0,
              lift=0.0, extra=None, plates=1.0):
    f = Fr()
    S = 1.9
    oy = dy + crouch * 2.0 + sink - lift
    T = (dx + 5.0, -8.0 + oy)
    A = (dx - 6.0, -10.0 + oy)
    # legs: four per side, thick and hairy, knees high
    foot_x = [-12.0, -6.0, 6.5, 13.0]
    specs = []
    for side in (1, 0):
        for i in range(4):
            ph = legs + i * math.pi / 2 + side * math.pi
            root = (T[0] - 3.0 + i * 1.6 - (1.0 if side else 0), T[1] - 0.5)
            fx = dx + foot_x[i] + (1.4 if side else 0) + amp * 2.6 * math.sin(ph) + splay * (i - 1.5) * 2
            fy = -max(0.0, amp * 2.2 * math.cos(ph)) - (1.2 if side else 0) + sink * 0.0 - lift
            if i == 3 and rear > 0:
                fx = T[0] + 7 + 2 * rear; fy = T[1] - 4 - 7 * rear
            l1, l2 = (9.0, 8.4) if i >= 2 else (10.0, 9.4)
            specs.append((side, i, root, (fx, fy), l1, l2))
    def leg(lay, root, foot, l1, l2, far):
        bend = 1 if foot[0] >= root[0] else -1
        (kx, ky), _ = ik(root[0], root[1], foot[0], foot[1], l1, l2, bend=bend)
        ramp = "1223" if far else "3fgh"
        tube(lay, [root, (kx, ky)], [1.6, 1.4], ramp, bias=0.2)
        tube(lay, [(kx, ky), foot], [1.4, 0.8], ramp, bias=0.1)
        if not far:
            for q in (0.3, 0.6):
                x, y = kx + (foot[0] - kx) * q, ky + (foot[1] - ky) * q
                lay.put(*P(x, y), "5"); lay.put(*P(x + 1, y), "5")
            for q in (0.25, 0.55, 0.8):
                x, y = root[0] + (kx - root[0]) * q, root[1] + (ky - root[1]) * q
                lay.put(*P(x, y - 1.6), "h")
            lay.put(*P(*foot), "7")
    for side, i, root, foot, l1, l2 in specs:
        if side: leg(f.n, root, foot, l1, l2, True)
    # body: big furry abdomen, furry cephalothorax
    fur(f.b, A[0], A[1], 8.6, 6.4, "234fgh", ang=tilt * 0.3, seed=3)
    fur(f.b, T[0], T[1] - 0.6, 5.4, 4.2, "234fgh", ang=tilt, seed=7, tuft=0.8)
    # the Lurker's lid, become a ridge of frost plates along the back
    for j in range(5):
        a = math.radians(-160 + j * 26)
        bx_, by_ = A[0] + 7.0 * math.cos(a), A[1] + 5.4 * math.sin(a)
        ell(f.b, bx_, by_ - 0.8 * plates, 2.2, 1.5, "5678", ang=math.degrees(a) + 90, bias=0.3)
        f.b.put(*P(bx_ + 1, by_ + 0.6), "3")
    for side, i, root, foot, l1, l2 in specs:
        if not side: leg(f.l if i >= 2 else f.u, root, foot, l1, l2, False)
    # chelicerae + fangs
    hx, hy = T[0] + 4.6, T[1] + 1.4
    ell(f.b, hx, hy, 1.6, 2.0, "1223", bias=0.1)
    line(f.b, hx + 0.6, hy + 1.6, hx + 1.6 + fang, hy + 3.2 - fang * 1.4, "8")
    # eye cluster
    ex, ey = P(T[0] + 2.6, T[1] - 3.6)
    pts = [(0, 0), (1, 0), (-1, 1), (2, 1), (0, -1)]
    for j, (a_, b_) in enumerate(pts):
        f.g.put(ex + a_, ey + b_, ("H" if j < 2 else "G") if eye == "wide" else "G" if eye == "open" and j < 2 else "I" if eye in ("open", "squint") else "2")
    if extra: extra(f, T, A)
    return f.done()


def build_tarantula(outdir):
    Tr = tarantula
    idle = [Tr(), Tr(legs=0.4, amp=0.15, crouch=0.2), Tr(legs=0.8, amp=0.15, crouch=0.3, eye="squint"), Tr(legs=1.2, amp=0.15, crouch=0.1)]
    run = [Tr(legs=i * math.pi / 3, amp=1.0, dy=-0.6 * abs(math.sin(i * math.pi / 3)), tilt=2 * math.sin(i * math.pi / 3)) for i in range(6)]
    def bite_fx(n):
        def fn(f, T, A):
            for j, (a, b) in enumerate(((2, -2), (3, 0), (2, 2), (4, -1), (4, 1), (5, 0))[:n]):
                f.g.put(*P(T[0] + 8 + a, T[1] + 2 + b), "8" if j % 2 == 0 else "6")
        return fn
    bite = [Tr(dx=-0.8, crouch=0.5, fang=0.4, eye="wide"),
            Tr(dx=-2.0, crouch=0.2, fang=1.0, eye="wide", rear=0.6, lift=0.8),
            Tr(dx=-2.4, crouch=0.0, fang=1.2, eye="wide", rear=1.0, lift=1.4),
            Tr(dx=2.6, crouch=0.8, fang=0.0, eye="squint", legs=1.0, amp=0.5, extra=bite_fx(6)),
            Tr(dx=2.4, crouch=0.7, fang=0.0, eye="squint", legs=1.2, amp=0.4, extra=bite_fx(3)),
            Tr(dx=1.0, crouch=0.3, legs=1.6, amp=0.3),
            Tr()]
    def spray(n, x0=0.0, h=6):
        def fn(f, T, A):
            r = random.Random(n * 7 + int(x0))
            for j in range(n):
                x = x0 + r.uniform(-12, 12); y = -r.uniform(1, h)
                f.g.put(*P(x, y), "8" if j % 3 == 0 else "7" if j % 3 == 1 else "6")
            for x in range(int(x0) - 12, int(x0) + 13):
                if r.random() < 0.6: f.g.put(x, 0, "6" if x % 2 else "7")
        return fn
    def mound(crack):
        def fn(f, T, A):
            ell(f.b, 0, -1.5, 9.0, 2.6 + crack * 0.6, "4567", bias=0.3, vmax=0.4)
            for j in range(crack * 3):
                f.b.put(*P(-6 + j * 2.2, -2.6 - crack * 0.4 + (j % 2)), "1")
            for j in range(2 + crack):
                f.b.put(*P(-8 + j * 4, -1), "7")
        return fn
    burrow = [Tr(crouch=0.6, eye="wide", fang=0.4),
              Tr(crouch=1.4, eye="wide", tilt=8, extra=spray(8)),
              Tr(sink=6.0, eye="squint", tilt=10, extra=spray(14, 0, 9)),
              Tr(sink=12.0, eye="dead", tilt=12, splay=0.4, extra=spray(10, 0, 6)),
              Tr(sink=40.0, extra=mound(0)),
              Tr(sink=40.0, extra=mound(2)),
              Tr(lift=2.0, splay=0.8, rear=0.6, fang=1.2, eye="wide", tilt=-6, extra=spray(16, 0, 14)),
              Tr(lift=0.6, splay=0.4, fang=0.6, eye="wide", extra=spray(6, 0, 5)),
              Tr(crouch=0.3)]
    death = [Tr(dx=-0.6, rear=0.8, splay=0.6, fang=1, eye="wide", tilt=-10, lift=1.0),
             grounded(Tr(dx=-1, rear=1.0, splay=1.0, fang=1, eye="dead", tilt=-24, crouch=1.0)),
             grounded(recol(Tr(dx=-1, rear=1.0, splay=1.4, eye="dead", tilt=-34, crouch=2.0), {"8": "h", "h": "g"})),
             tarantula_corpse()]
    knock = Tr(dx=-0.8, rear=0.5, splay=0.5, fang=0.6, eye="squint", tilt=-8, lift=0.6)
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.09] * 6),
             ("Bite", bite, [0.14, 0.12, 0.12, 0.06, 0.1, 0.12, 0.12]),
             ("Burrow", burrow, [0.1, 0.12, 0.1, 0.1, 0.25, 0.25, 0.08, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.5], knock)
    sheet("YsvTarantula", anims, outdir, scale=4)


def tarantula_corpse():
    f = Fr()
    fur(f.b, -3.0, -3.6, 9.0, 3.6, "34fgh", seed=5)
    fur(f.b, 7.0, -2.6, 4.4, 2.6, "34fgh", seed=9)
    for i in range(4):
        bx = -4.0 + i * 3.4
        sd = 1 if i % 2 else -1
        pts = [(bx, -6.0), (bx + sd * 2.0, -10.0), (bx + sd * 0.4, -12.6)]
        tube(f.u, pts[:2], [1.2, 1.0], "3fgh", bias=0.2); tube(f.u, pts[1:], [1.0, 0.6], "3fgh", bias=0.1)
    for j in range(4): ell(f.b, -10 + j * 4, -1.0, 1.8, 1.0, "5678", bias=0.3)
    f.g.put(9, -3, "2")
    return f.done()


# ------------------------------------------------------------------ HOARCLAW (T3; Rime Lurker)
# A crab spider armoured in the Lurker's frost plates: a flat, wide navy body under a shell of pale plates, short
# splayed walking legs, and two huge raised forelegs ending in ice-crystal pincers. Seizes the hero and hurls him.
def hoarclaw(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, amp=0.0, crouch=0.0, claws=((10.0, -20.0), (13.0, -18.0)), open_=0.5,
             eye="open", lift=0.0, extra=None, glow=0):
    f = Fr()
    oy = dy + crouch * 1.5 - lift
    C = (dx + 1.0, -7.0 + oy)
    def R(p): return rot_about(p, C, tilt)
    # walking legs: three short splayed pairs
    for side in (1, 0):
        for i in range(3):
            ph = legs + i * 2.1 + side * math.pi
            root = R((C[0] - 3.0 + i * 2.6, C[1] + 1.0))
            fx = dx + [-12.0, -5.0, 3.0][i] + (1.2 if side else 0) + amp * 2.0 * math.sin(ph)
            fy = -max(0.0, amp * 1.8 * math.cos(ph)) - (1.0 if side else 0)
            (kx, ky), _ = ik(root[0], root[1], fx, fy, 6.0, 6.4, bend=1 if fx >= root[0] else -1)
            lay = f.n if side else f.u
            ramp = "1223" if side else "2345"
            tube(lay, [root, (kx, ky)], [1.1, 0.9], ramp, bias=0.2); tube(lay, [(kx, ky), (fx, fy)], [0.9, 0.5], ramp, bias=0.1)
            if not side: lay.put(*P(kx, ky - 0.6), "7"); lay.put(*P(fx, fy), "7")
    # flat body: navy under a shell of pale frost plates (the Lurker's lid, now a full carapace)
    ell(f.b, *R((C[0] - 1.0, C[1] + 0.4)), 10.0, 4.4, "12234", ang=tilt, bias=0.1)
    for j in range(7):
        a = math.radians(-170 + j * 26)
        bx_, by_ = R((C[0] - 1.0 + 8.2 * math.cos(a), C[1] + 0.4 + 3.4 * math.sin(a)))
        ell(f.b, bx_, by_ - 0.6, 2.4, 1.6, "56788", ang=math.degrees(a) + 90 + tilt, bias=0.3)
        f.b.put(*P(bx_ + 1, by_ + 0.4), "3")
    crystal(f.b, *R((C[0] - 2.0, C[1] - 3.4)), -100 + tilt, 3.4, 0.9, lit=0.25)
    crystal(f.b, *R((C[0] + 2.4, C[1] - 3.2)), -76 + tilt, 2.6, 0.8, lit=0.25)
    # raised forelegs with pincers (far one first)
    for sd, (cx_, cy_) in ((1, claws[0]), (0, claws[1])):
        root = R((C[0] + 6.0 - sd * 1.2, C[1] - 1.0))
        tx, ty = dx + cx_, cy_ + oy
        (kx, ky), _ = ik(root[0], root[1], tx, ty, 9.0, 9.0, bend=1)
        lay = f.u if sd else f.l
        ramp = "3456" if sd else "34567"
        tube(lay, [root, (kx, ky)], [1.8, 1.6], ramp, bias=0.25)
        tube(lay, [(kx, ky), (tx, ty)], [1.6, 1.3], ramp, bias=0.25)
        lay.put(*P(kx, ky - 1), "D"); lay.put(*P(kx + 1, ky - 1), "E")
        ang = math.degrees(math.atan2(ty - ky, tx - kx))
        a1 = crystal(lay, tx, ty, ang - 20 - 30 * open_, 6.6, 1.6, lit=0.3 if not sd else 0.0, ramp="5678" if not sd else None)
        a2 = crystal(lay, tx, ty, ang + 25 + 25 * open_, 5.0, 1.2, lit=0.3 if not sd else 0.0, ramp="5678" if not sd else None)
        if not sd:
            f.g.put(*P(*a1), "H" if glow else "8"); f.g.put(*P(*a2), "8")
    # eyes on the front rim
    ex, ey = P(*R((C[0] + 8.0, C[1] - 1.6)))
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex - 2, ey, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex - 2, ey, "G"); f.g.put(ex - 1, ey - 1, "G")
    elif eye == "squint": f.g.put(ex, ey, "I")
    else: f.g.put(ex, ey, "2")
    if extra: extra(f, C, claws)
    return f.done()


def build_hoarclaw(outdir):
    Hc = hoarclaw
    REST = dict(claws=((15.0, -21.0), (19.0, -11.0)), open_=0.9)
    idle = [Hc(**REST), Hc(claws=((15.0, -20.6), (19.0, -10.6)), open_=1.1, crouch=0.2, legs=0.3, amp=0.1),
            Hc(claws=((15.0, -20.2), (19.0, -10.2)), open_=1.2, crouch=0.3, legs=0.6, amp=0.1, eye="squint"),
            Hc(claws=((15.0, -20.8), (19.0, -10.8)), open_=1.0, crouch=0.1, legs=0.9, amp=0.1)]
    run = [Hc(legs=i * math.pi / 3, amp=1.0, dy=-0.5 * abs(math.sin(i * math.pi / 3)), tilt=2 * math.sin(i * math.pi / 3),
              claws=((15.0, -21.0 + math.sin(i)), (19.0, -11.0 - math.sin(i))), open_=0.8) for i in range(6)]
    def snapfx(n):
        def fn(f, C, claws):
            for j in range(n):
                f.g.put(*P(dx_ + 22 + (j % 3), -6 + j), "8" if j % 2 == 0 else "6")
        dx_ = 0
        return fn
    snap = [Hc(claws=((6.0, -20.0), (9.0, -19.0)), open_=1.0, eye="wide", tilt=-3),
            Hc(claws=((4.0, -22.0), (7.0, -22.0)), open_=1.3, eye="wide", tilt=-6, crouch=0.4),
            Hc(claws=((14.0, -14.0), (17.0, -12.0)), open_=1.2, eye="wide", tilt=4, dx=1.0),
            Hc(claws=((18.0, -8.0), (21.0, -6.0)), open_=0.0, eye="squint", tilt=8, dx=2.0, extra=snapfx(4)),
            Hc(claws=((17.0, -8.0), (20.0, -6.0)), open_=0.0, eye="squint", tilt=6, dx=1.6, extra=snapfx(2)),
            Hc(claws=((12.0, -13.0), (15.0, -11.0)), open_=0.4, tilt=2, dx=0.6),
            Hc(**REST)]
    def held(f, C, claws):
        for j in range(5):
            f.g.put(*P(claws[1][0] + 2 + (j % 2) * 2, claws[1][1] + 2 + j), "8" if j % 2 else "7")
    def hurl_fx(f, C, claws):
        for j in range(6):
            line(f.g, 10 + j * 1.5, -24 + j, 16 + j * 1.5, -28 + j * 0.5, "7" if j % 2 else "8")
    seize = [Hc(claws=((5.0, -21.0), (8.0, -21.0)), open_=1.4, eye="wide", tilt=-4, crouch=0.4),
             Hc(claws=((3.0, -24.0), (6.0, -24.0)), open_=1.6, eye="wide", tilt=-8, crouch=0.8, glow=1),
             Hc(claws=((19.0, -10.0), (22.0, -8.0)), open_=1.6, eye="wide", tilt=8, dx=3.0, glow=1),
             Hc(claws=((19.0, -8.0), (21.0, -7.0)), open_=0.0, eye="squint", tilt=8, dx=3.0, glow=1, extra=held),
             Hc(claws=((14.0, -16.0), (16.0, -15.0)), open_=0.0, eye="squint", tilt=-2, dx=2.0, extra=held),
             Hc(claws=((10.0, -24.0), (12.0, -23.0)), open_=0.0, eye="wide", tilt=-8, dx=1.0, extra=held),
             Hc(claws=((15.0, -22.0), (18.0, -20.0)), open_=1.6, eye="wide", tilt=6, dx=1.6, extra=hurl_fx),
             Hc(claws=((10.0, -18.0), (13.0, -16.0)), open_=0.8, dx=0.4)]
    death = [Hc(claws=((4.0, -24.0), (7.0, -23.0)), open_=1.6, eye="wide", tilt=-12, lift=0.8),
             grounded(Hc(claws=((10.0, -10.0), (13.0, -8.0)), open_=1.2, eye="dead", tilt=-26, crouch=1.0)),
             grounded(recol(Hc(claws=((14.0, -4.0), (16.0, -2.0)), open_=1.6, eye="dead", tilt=-34, crouch=1.6), {"8": "7"})),
             hoarclaw_corpse()]
    knock = Hc(claws=((5.0, -22.0), (8.0, -21.0)), open_=1.2, eye="squint", tilt=-10, lift=0.6, dx=-0.8)
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.09] * 6),
             ("Snap", snap, [0.14, 0.12, 0.06, 0.06, 0.1, 0.12, 0.12]),
             ("Seize", seize, [0.12, 0.12, 0.06, 0.16, 0.16, 0.14, 0.08, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.5], knock)
    sheet("YsvHoarclaw", anims, outdir, scale=4)


def hoarclaw_corpse():
    f = Fr()
    ell(f.b, -1.0, -2.4, 10.0, 2.4, "12234", bias=0.1)
    for j in range(6): ell(f.b, -9 + j * 3.6, -3.6, 2.0, 1.2, "56788", bias=0.3)
    for (bx, a) in ((10, -30), (13, -10)):
        crystal(f.b, bx, -1, a, 5.0, 1.3)
    for x in (-8, -3, 2):
        polyline(f.u, [(x, -3), (x - 2, -6), (x - 1, -8)], "3")
    f.g.put(8, -2, "2")
    return f.done()


# ------------------------------------------------------------------ THE GEODE (T3; Shard Hermit)
# The Hermit's geode pack has swallowed him: a great dome of dark rock split by glowing cracks, crystal clusters
# bursting out of it, stubby legs underneath, and the hooded Hermit (crystal horn, two eyes) peering out of a hole at
# the front. When it bristles every crystal grows into a thorn.
def geode(dx=0.0, dy=0.0, tilt=0.0, legs=0.0, amp=0.0, squash=0.0, spikes=1.0, eye="open", glow=0, peek=1.0, extra=None, lift=0.0):
    f = Fr()
    C = (dx - 1.0, -12.0 + dy + squash * 2.0 - lift)
    def R(x, y): return rot_about((C[0] + x, C[1] + y * (1 - squash * 0.12)), (C[0], 0.0), tilt)
    for j, ox in enumerate((-9.0, -3.5, 3.5, 9.0)):
        ph = legs + j * math.pi / 2
        fx = dx + ox + amp * 1.6 * math.sin(ph)
        fy = -max(0.0, amp * 1.4 * math.cos(ph))
        top = R(ox * 0.85, 8.0)
        lay = f.u if j in (0, 2) else f.b
        tube(lay, [top, (fx, fy - 1.0)], [2.0, 1.8], "1223" if j in (0, 2) else "2345", bias=0.2)
        ell(lay, fx + 0.6, fy - 0.8, 2.2, 1.0, "2345", bias=0.3)
    # the dome of dark rock
    ell(f.b, *R(0.0, 0.0), 14.0, 11.0, "12234", ang=tilt, bias=0.2, vmax=0.82,
        shader=lambda nu, nv, d, l, ch, x, y: ("3" if (x * 3 + y * 5) % 11 == 0 and d < 0.9 else "4" if nv < -0.75 and nu < 0.1 else ch))
    # glowing cracks
    for (pts) in (((-10, -2), (-6, -4), (-4, -1), (-1, -3)), ((2, -9), (3, -5), (6, -3)), ((-3, 4), (0, 3), (3, 5))):
        polyline(f.b, [R(*p_) for p_ in pts], "G" if glow else "5")
    # crystal clusters bursting out of it
    for (x, y, a, ln, wd) in ((-6, -8, -120, 6.0, 1.6), (-3, -10, -100, 7.2, 1.8), (1, -10.6, -82, 6.0, 1.6), (5, -9, -62, 5.4, 1.4),
                              (-11, -3, -160, 4.6, 1.3), (9, -6, -40, 4.4, 1.3), (-9, -7, -138, 4.0, 1.1)):
        b = R(x, y)
        crystal(f.b, b[0], b[1], a + tilt, ln * spikes, wd, lit=0.15 + 0.1 * glow)
    if spikes > 1.15:
        for (x, y, a) in ((-12, 3, 170), (12, 2, 10), (-8, 7, 150), (11, -1, -10)):
            b = R(x, y)
            crystal(f.b, b[0], b[1], a + tilt, 3.6 * (spikes - 0.6), 1.0, lit=0.2)
    # the hole at the front with the Hermit peering out (black-silk hood, crystal horn, eyes)
    hc = R(8.6, 1.6)
    ell(f.b, hc[0], hc[1], 3.4, 3.8, "0011", bias=0.0)
    if peek > 0:
        hp = [R(6.4, 3.6), R(6.6, -0.6 - peek), R(8.8, -2.6 - peek), R(11.0, -1.0 - peek * 0.6), R(11.4, 3.0)]
        poly(f.b, hp, "C", shade=lambda x, y: pick("ABCDE", 0.5 - (x - hc[0]) * 0.1 - (y - hc[1]) * 0.15))
        crystal(f.b, *R(8.2, -1.8 - peek), -72 + tilt, 2.6, 0.7, lit=0.1)
        ex, ey = P(*R(9.4, 0.8)); ex2, ey2 = P(*R(10.8, 0.8))
        if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex2, ey2, "I")
        elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex2, ey2, "G")
        elif eye == "squint": f.g.put(ex, ey, "I")
        else: f.g.put(ex, ey, "2")
    if extra: extra(f, C)
    return f.done()


def build_geode(outdir):
    Gd = geode
    idle = [Gd(), Gd(squash=0.3, legs=0.3, amp=0.1), Gd(squash=0.5, legs=0.6, amp=0.1, eye="squint", glow=1), Gd(squash=0.2, peek=1.3)]
    run = [Gd(legs=i * math.pi / 3, amp=1.0, tilt=3 * math.sin(i * math.pi / 3), dy=-0.6 * abs(math.sin(i * math.pi / 3))) for i in range(6)]
    def quake(n):
        def fn(f, C):
            for j in range(-n, n + 1):
                f.g.put(*P(16 + j * 1.4, 0), "7" if j % 2 else "8")
            for j in range(n // 2):
                line(f.g, 14 + j * 3, -1, 14.5 + j * 3, -3 - j, "6")
        return fn
    slam = [Gd(tilt=-4, squash=0.2, eye="wide"),
            Gd(tilt=-12, lift=1.0, eye="wide", glow=1),
            Gd(tilt=-16, lift=2.0, eye="wide", glow=1, peek=0.6),
            Gd(tilt=10, squash=0.4, dx=2.0, eye="wide", glow=1),
            Gd(tilt=16, squash=0.8, dx=3.0, eye="squint", glow=2, extra=quake(4)),
            Gd(tilt=12, squash=0.6, dx=2.6, eye="squint", glow=1, extra=quake(2)),
            Gd(tilt=4, squash=0.3, dx=1.0),
            Gd()]
    bristle = [Gd(squash=0.3, eye="squint", glow=1, peek=0.6),
               Gd(squash=0.6, eye="squint", glow=1, peek=0.0, spikes=1.1),
               Gd(squash=0.8, glow=2, peek=0.0, spikes=1.3),
               Gd(squash=-0.2, lift=0.6, glow=2, peek=0.0, spikes=1.55),
               Gd(squash=0.0, glow=2, peek=0.4, spikes=1.6, eye="wide"),
               Gd(squash=0.1, glow=1, peek=0.8, spikes=1.6, eye="wide"),
               Gd(squash=0.1, glow=1, peek=1.0, spikes=1.5)]
    death = [Gd(tilt=-10, lift=1.0, eye="wide", glow=2),
             Gd(tilt=8, squash=1.0, eye="dead", glow=0, spikes=0.8, peek=0.2),
             grounded(Gd(tilt=14, squash=2.0, eye="dead", spikes=0.6, peek=0.0)),
             geode_corpse()]
    knock = Gd(tilt=-10, lift=0.6, eye="squint", peek=0.6)
    anims = [("Idle", idle, [0.28, 0.24, 0.28, 0.24]), ("Run", run, [0.1] * 6),
             ("Slam", slam, [0.14, 0.14, 0.12, 0.05, 0.08, 0.14, 0.14, 0.14]),
             ("Bristle", bristle, [0.12, 0.12, 0.1, 0.08, 0.12, 0.14, 0.14])]
    anims += std_tail(idle[0], death, [0.1, 0.14, 0.16, 0.5], knock)
    sheet("YsvGeode", anims, outdir, scale=4)


def geode_corpse():
    f = Fr()
    ell(f.b, -4.0, -4.0, 9.0, 4.0, "11223", bias=0.2, vmax=0.8)
    ell(f.b, 7.0, -3.0, 5.0, 3.0, "11223", bias=0.2, vmax=0.8)
    for (x, a, ln) in ((-9, -150, 4.0), (-5, -110, 5.0), (-1, -80, 4.4), (5, -60, 3.6), (10, -30, 3.0)):
        crystal(f.b, x, -3.5, a, ln, 1.3)
    poly(f.b, [(2, 0), (3, -3), (6, -3.5), (7, 0)], "C")
    f.g.put(5, -2, "2")
    return f.done()


# ------------------------------------------------------------------ PRISM ORACLE (T3; Shard Hermit)
# The Hermit gone up instead of in: he sits cross-legged on a great floating prism of clear ice that splits light into
# aurora colours, his black-silk hood and crystal horn on top, two shards circling. Sweeps a refracted beam.
def oracle(dy=0.0, dx=0.0, tilt=0.0, hover=4.0, glow=0, eye="open", orbit=0.0, arms=0.0, hood=0.0, extra=None, ground=False, shine=0):
    f = Fr()
    base = -hover + dy
    if ground: base = 0.0
    PC = (dx, base - 11.0)
    def R(x, y): return rot_about((PC[0] + x, PC[1] + y), PC, tilt)
    top, bot, lf, rt = R(0.0, -10.5), R(0.0, 10.5), R(-7.0, -1.0), R(7.0, -1.0)
    mid = R(1.4, -0.6)
    poly(f.b, [top, lf, bot, mid], "7", shade=lambda x, y: pick("5678", 0.7 - (y - PC[1]) * 0.05 + (0.3 if (x + y + shine) % 5 == 0 else 0)))
    poly(f.b, [top, mid, bot, rt], "5", shade=lambda x, y: pick("3456", 0.2 - (y - PC[1]) * 0.05))
    line(f.b, *top, *mid, "8"); line(f.b, *mid, *bot, "6")
    # aurora glints refracted inside
    for j, ch in enumerate(("%", "F", "^", "E")):
        y = PC[1] - 4 + j * 2.6
        f.b.put(*P(PC[0] - 2 + (j + shine) % 3, y), ch)
    core = R(-0.6, 0.6)
    f.g.put(*P(*core), "H" if glow > 1 else "G")
    if glow:
        for (a_, b_) in ((1, 0), (-1, 0), (0, 1), (0, -1)): f.g.put(*P(core[0] + a_, core[1] + b_), "G" if glow > 1 else "I")
    # the Hermit seated on the top point: robe pooled over the facets, hood, horn, arms
    sx, sy = top[0], top[1] + 2.0
    robe = [(sx - 5.0, sy + 1.0), (sx - 3.0, sy - 3.4), (sx + 3.6, sy - 3.4), (sx + 5.4, sy + 1.2), (sx + 1.0, sy + 2.4)]
    poly(f.b, robe, "C", shade=lambda x, y: pick("ABCDE", 0.5 - (x - sx) * 0.08 - (y - sy) * 0.1))
    for j in range(5): f.b.put(*P(sx - 4 + j * 2, sy + 1.6), "6" if j % 2 else "4")
    hc = (sx + 0.6, sy - 6.0 - hood * 0.4)
    hp = [(hc[0] - 3.0, hc[1] + 3.0), (hc[0] - 2.2, hc[1] - 2.0), (hc[0] + 0.6, hc[1] - 3.6), (hc[0] + 3.2, hc[1] - 1.6),
          (hc[0] + 3.4, hc[1] + 3.0)]
    poly(f.b, hp, "C", shade=lambda x, y: pick("ABCDE", 0.6 - (x - hc[0]) * 0.1 - (y - hc[1]) * 0.15))
    poly(f.b, [(hc[0] + 0.4, hc[1] - 0.6), (hc[0] + 3.0, hc[1] - 0.4), (hc[0] + 3.0, hc[1] + 2.4), (hc[0] + 0.8, hc[1] + 2.4)], "1")
    crystal(f.b, hc[0] - 0.8, hc[1] - 2.8, -74, 3.0, 0.8, lit=0.1)
    for sd in (-1, 1):
        sh = (sx + sd * 2.4, sy - 2.6)
        hand = (sx + sd * (4.6 + arms * 1.4), sy - 2.6 - arms * 5.0)
        line(f.b if sd > 0 else f.u, *sh, *hand, "D" if sd > 0 else "B")
        f.g.put(*P(*hand), "G" if glow else "g")
    ex, ey = P(hc[0] + 1.4, hc[1] + 0.6)
    if eye == "open": f.g.put(ex, ey, "G"); f.g.put(ex + 1, ey, "I")
    elif eye == "wide": f.g.put(ex, ey, "H"); f.g.put(ex + 1, ey, "G")
    elif eye == "squint": f.g.put(ex, ey, "I")
    else: f.g.put(ex, ey, "2")
    # two orbiting shards
    for j in range(2):
        a = orbit + j * math.pi
        ox, oy = PC[0] + 10.5 * math.cos(a), PC[1] + 2.0 + 3.0 * math.sin(a)
        lay = f.b if math.sin(a) > 0 else f.u
        crystal(lay, ox, oy + 1.6, -90, 3.4, 0.9, lit=0.2)
    if extra: extra(f, PC, core)
    return f.done()


def build_oracle(outdir):
    O = oracle
    idle = [O(orbit=0.0), O(orbit=0.8, dy=-0.6, shine=1), O(orbit=1.6, dy=-1.0, shine=2, glow=1), O(orbit=2.4, dy=-0.5, shine=3)]
    run = [O(orbit=i * 0.6, tilt=6, dy=-0.4 * abs(math.sin(i * math.pi / 3)), shine=i) for i in range(6)]
    def flare(n):
        def fn(f, PC, core):
            for j in range(n):
                a = math.radians(j * 45)
                f.g.put(*P(core[0] + 3 * math.cos(a), core[1] + 3 * math.sin(a)), "8" if j % 2 else "%")
        return fn
    bolt = [O(orbit=0.0, glow=1, arms=0.3),
            O(orbit=0.5, glow=1, arms=0.8, eye="wide", tilt=-4, extra=flare(2)),
            O(orbit=1.0, glow=2, arms=1.0, eye="wide", tilt=-6, extra=flare(4)),
            O(orbit=1.5, glow=2, arms=0.4, eye="wide", tilt=8, extra=flare(8)),
            O(orbit=2.0, glow=1, arms=0.2, eye="squint", tilt=6, extra=flare(4)),
            O(orbit=2.5, glow=1, tilt=2),
            O(orbit=3.0)]
    def ray(n):
        def fn(f, PC, core):
            for j in range(n):
                f.g.put(*P(core[0] + 3 + j * 2, core[1] - 0.5 + (j % 2)), "H" if j < 2 else "8" if j % 2 else "%")
        return fn
    beam = [O(orbit=0.0, glow=1, arms=0.4, eye="open"),
            O(orbit=0.6, glow=1, arms=1.0, eye="wide", shine=1, extra=flare(4)),
            O(orbit=1.2, glow=2, arms=1.2, eye="wide", shine=2, extra=flare(8)),
            O(orbit=1.8, glow=2, arms=1.2, eye="wide", tilt=4, shine=3, extra=ray(4)),
            O(orbit=2.4, glow=2, arms=1.2, eye="wide", tilt=4, shine=0, extra=ray(5)),
            O(orbit=3.0, glow=2, arms=1.2, eye="wide", tilt=4, shine=1, extra=ray(5)),
            O(orbit=3.6, glow=2, arms=1.2, eye="squint", tilt=4, shine=2, extra=ray(5)),
            O(orbit=4.2, glow=1, arms=0.6, eye="squint", tilt=2),
            O(orbit=4.8)]
    death = [O(tilt=-14, eye="wide", glow=2, arms=1.2, dy=-1.0),
             O(tilt=20, eye="dead", hover=2.0, dy=1.0),
             grounded(O(tilt=70, eye="dead", ground=True)),
             oracle_corpse()]
    knock = O(tilt=-14, eye="squint", arms=0.8)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.08] * 6),
             ("Bolt", bolt, [0.12, 0.12, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("Beam", beam, [0.12, 0.12, 0.12, 0.2, 0.2, 0.2, 0.2, 0.14, 0.12])]
    anims += std_tail(idle[0], death, [0.1, 0.12, 0.16, 0.4], knock)
    sheet("YsvOracle", anims, outdir, scale=4)


def oracle_corpse():
    f = Fr()
    for (x, a, ln, wd) in ((-6, -160, 6, 2.0), (-1, -120, 7, 2.4), (4, -40, 5, 1.8), (8, -10, 4, 1.4)):
        crystal(f.b, x, -1, a, ln, wd, lit=0.2)
    poly(f.b, [(-3, 0), (-1, -4), (4, -4.4), (6, -1), (4, 0)], "C", shade=lambda x, y: pick("ABCD", 0.3 - y * 0.05))
    f.b.put(2, -2, "%"); f.b.put(-4, -1, "F")
    f.g.put(3, -2, "2")
    return f.done()


# ------------------------------------------------------------------ FX for the new T3s
def fx_drain():
    """FxYsvDrain: the Loom Widow's feeding line. Fly: a barbed silk hook trailing a strand; Bead: one droplet of drawn
    life (pale violet with a white core) that runs along the line; Snap: the line breaking."""
    fly, bead, snap = [], [], []
    for i in range(4):
        c = cv()
        for k in range(7):
            c.put(-2 - k, round(0.8 * math.sin(k * 0.9 + i * 1.5)), "7" if k % 2 else "E")
        c.put(0, 0, "8"); c.put(1, 0, "H"); c.put(0, -1, "F"); c.put(0, 1, "F"); c.put(-1, -1 - (i % 2), "8")
        fly.append(outl(c.spr(), "A"))
    for i in range(2):
        c = cv()
        ell(c, 0, 0, 1.5 + 0.3 * i, 1.3 + 0.3 * i, "EFh", bias=0.3)
        c.put(0, 0, "H")
        bead.append(outl(c.spr(), "B"))
    for i in range(4):
        c = cv()
        for sd in (-1, 1):
            for k in range(4 - i):
                c.put(sd * (2 + i * 2 + k), (k % 2) + i * sd * 0.5, "7" if k % 2 else "F")
        if i < 2: c.put(0, 0, "H")
        snap.append(c.spr())
    return fly, bead, snap


def fx_shimmer():
    """FxYsvShimmer: the Glasswing fading in or out: glass glints scatter in a ring and wink out."""
    out = []
    for i in range(5):
        c = cv()
        r = 3 + i * 2.4
        for k in range(10):
            a = math.radians(k * 36 + i * 13)
            x, y = r * math.cos(a), r * 0.8 * math.sin(a)
            if (k + i) % 5 == 4: continue
            ch = "8" if i < 2 else "7" if i < 4 else "5"
            c.put(*P(x, y), ch)
            if i < 3 and k % 2 == 0: c.put(*P(x + 1, y), "6"); c.put(*P(x, y - 1), "6")
        if i < 2: c.put(0, 0, "H")
        out.append(c.spr())
    return out


def vortex_ring(c, t, rx=18.0, ry=7.0, arms=4, dens=1.0):
    for a_ in range(arms):
        for k in range(int(26 * dens)):
            u = k / (26.0 * dens)
            ang = a_ * 2 * math.pi / arms + u * 4.2 + t
            r = 1.0 - u * 0.85
            x, y = rx * r * math.cos(ang), ry * r * math.sin(ang)
            c.put(*P(x, y), "8" if u > 0.75 else "7" if u > 0.45 else "6" if u > 0.2 else "4")


def fx_vortex():
    """FxYsvVortex: the Snow Wraith's maelstrom on the floor around the hero. Open 3 (the spiral spins up),
    Spin 4 (seamless loop), Burst 5 (it collapses inward and blasts up into a pillar of frost: the hit)."""
    opn, spin, burst = [], [], []
    for i in range(3):
        c = cv(); vortex_ring(c, i * 0.7, rx=8 + i * 5, ry=3 + i * 2, dens=0.5 + i * 0.25)
        opn.append(c.spr())
    for i in range(4):
        c = cv(); vortex_ring(c, i * math.pi / 2 / 2, rx=18, ry=7)
        for k in range(6):
            a = math.radians(k * 60 + i * 15)
            c.put(*P(14 * math.cos(a), -2 - 5 * abs(math.sin(a)) - (k % 2)), "7")
        spin.append(c.spr())
    for i in range(5):
        c = cv()
        if i < 2:
            vortex_ring(c, i * 0.8, rx=10 - i * 4, ry=4 - i * 1.5, dens=0.6)
        h = [4, 14, 18, 14, 6][i]
        w = [2, 4, 6, 7, 8][i]
        for y in range(-h, 1):
            for x in range(-w, w + 1):
                if abs(x) > w * (0.4 + 0.6 * (y + h) / max(1, h)): continue
                if (x * 3 + y * 5 + i) % (2 if i < 3 else 3) == 0:
                    c.put(x, y, "8" if abs(x) < w * 0.3 else "7" if abs(x) < w * 0.6 else "6")
        if i >= 2:
            for k in range(8):
                a = math.radians(k * 45 + i * 10)
                c.put(*P((w + 3) * math.cos(a), (w * 0.4 + 1) * math.sin(a)), "6")
        burst.append(c.spr())
    return opn, spin, burst


def fx_shield_spin():
    """FxYsvShieldSpin: the Rime Warden's thrown shield, spinning (its ice spikes turn), seen face-on. Centred."""
    out = []
    for i in range(4):
        c = cv(); warden_shield(c, 0, 0, 5.0, spin=i * 11.25, tilt=1.0)
        s = outl(c.spr(), "0")
        out.append(recol(s, KNIGHT))
    return out


def fx_burrow():
    """FxYsvBurrow: Dig 4 = snow and ice chips thrown up where the Tarantula sinks; Erupt 6 = the floor bursts in a ring
    of ice shards and snow where it comes up (the hit, frames 0-2)."""
    dig, erupt = [], []
    for i in range(4):
        c = cv(); r = random.Random(11 + i)
        for k in range(14 - i * 3):
            x = r.uniform(-10, 10); y = -r.uniform(0, 4 + i * 3)
            c.put(*P(x, y), "8" if k % 3 == 0 else "7" if k % 3 == 1 else "5")
        ell(c, 0, -0.6, 9 - i, 1.6, "345", bias=0.2, vmax=0.3)
        dig.append(c.spr())
    for i in range(6):
        c = cv(); r = random.Random(31 + i)
        rr = [6, 11, 15, 17, 18, 18][i]
        for k in range(12):
            a = 2 * math.pi * k / 12
            x, y = rr * math.cos(a), rr * 0.4 * math.sin(a)
            h = [3, 7, 8, 6, 3, 0][i] * (0.6 + 0.4 * r.random())
            if h >= 1: crystal(c, x, y, -90 + x * 2, h, 1.0, lit=0.2)
            elif i < 5: c.put(*P(x, y), "6")
        for k in range([16, 20, 14, 8, 4, 2][i]):
            c.put(*P(r.uniform(-rr, rr), -r.uniform(0, 4 + i * 3)), "8" if k % 2 else "7")
        erupt.append(outl(c.spr(), "1") if i < 4 else c.spr())
    return dig, erupt


def fx_grab():
    """FxYsvGrab: Hold 2 = frost shackles crusted round the hero's feet while the Hoarclaw holds him;
    Fling 4 = the crust bursting as he is hurled."""
    hold, fling = [], []
    for i in range(2):
        c = cv()
        ell(c, 0, -1.0, 5.0, 2.2, "4567", bias=0.3, vmax=0.4)
        for k in range(5):
            crystal(c, -4 + k * 2, -1.5, -90 + (k - 2) * 18, 3.0 + ((k + i) % 2), 0.8, lit=0.2)
        c.put(-2 + i * 3, -5, "8")
        hold.append(outl(c.spr(), "1"))
    for i in range(4):
        c = cv()
        for k in range(10):
            a = math.radians(k * 36 + i * 9)
            r = 3 + i * 3
            c.put(*P(r * math.cos(a), -3 + r * 0.6 * math.sin(a)), "8" if k % 2 else "6")
        fling.append(c.spr())
    return hold, fling


def fx_thorns():
    """FxYsvThorns: the Geode bristling: a crown of long crystal thorns around the dome (an overlay at its feet),
    glinting; Loop 2."""
    out = []
    for i in range(2):
        c = cv()
        for k in range(11):
            a = math.radians(-180 + k * 18)
            bx, by = 15.5 * math.cos(a), -12 + 12.5 * math.sin(a)
            if by > -2: continue
            crystal(c, bx, by, math.degrees(a), 3.6 + ((k + i) % 2) * 1.4, 1.0, lit=0.2)
        for k in range(3):
            a = math.radians(-160 + k * 60 + i * 30)
            c.put(*P(18 * math.cos(a), -12 + 15 * math.sin(a)), "H")
        out.append(outl(c.spr(), "1"))
    return out


def fx_thorn():
    """FxYsvThorn: one crystal thorn the Geode throws back at whoever hit it. Faces right, centred."""
    out = []
    for i in range(4):
        c = cv()
        crystal(c, -4, 0, 0, 8, 1.2, lit=0.2)
        c.put(-5 - (i % 2), 0, "6"); c.put(-6, (i % 3) - 1, "4")
        out.append(outl(c.spr(), "1"))
    return out


def fx_prism_bolt():
    """FxYsvPrismBolt: a spinning diamond of clear ice trailing a split aurora ribbon (teal / violet). Centred."""
    out = []
    for i in range(4):
        c = cv()
        for k in range(7):
            c.put(-2 - k, -1 + round(0.6 * math.sin(k + i)), "^" if k < 3 else "%")
            c.put(-2 - k, 1 + round(0.6 * math.sin(k + i + 2)), "F" if k < 3 else "E")
        w = [2, 1, 2, 1][i]
        poly(c, [(0, -2.6), (w, 0), (0, 2.6), (-w, 0)], "7", shade=lambda x, y: "8" if x <= 0 else "6")
        c.put(0, 0, "H")
        out.append(outl(c.spr(), "1"))
    return out


def fx_beam():
    """FxYsvBeam: the Prism Oracle's refracted beam, drawn from the origin to the right (96 px). Charge 3: a thin
    flickering line; Fire 4 (loop): a bright core with teal and violet fringes and travelling sparks; Fade 3."""
    L_ = 96
    charge, fire, fade = [], [], []
    for i in range(3):
        c = cv()
        for x in range(0, L_, 1 if i == 2 else 2):
            if (x + i) % 3 != 0 or i == 2: c.put(x, 0, "6" if i < 2 else "7")
        c.put(0, 0, "H")
        charge.append(c.spr())
    for i in range(4):
        c = cv()
        for x in range(0, L_):
            wob = 1 if (x // 6 + i) % 2 else 0
            c.put(x, 0, "H" if x % 9 != (i * 2) % 9 else "8")
            c.put(x, -1, "8" if x % 4 else "G"); c.put(x, 1, "G")
            c.put(x, -2 - wob * ((x + i) % 3 == 0), "^" if x % 3 else "%")
            c.put(x, 2 + wob * ((x + i) % 3 == 0), "F" if x % 3 else "E")
        for k in range(5):
            x = (k * 21 + i * 6) % L_
            c.put(x, -3, "8"); c.put(x + 1, 3, "8")
        ell(c, 0, 0, 2.6, 3.2, "%^8H", bias=0.4)
        fire.append(c.spr())
    for i in range(3):
        c = cv()
        for x in range(0, L_ - i * 20):
            if (x + i) % (i + 2) == 0: c.put(x, 0, "8" if i == 0 else "6")
            if i == 0: c.put(x, -1, "%"); c.put(x, 1, "E")
        fade.append(c.spr())
    return charge, fire, fade


def build_fx4(outdir, only=None):
    """v0.10 FX for the new monsters."""
    def want(n): return only is None or n in only
    if want("FxYsvSnare"):
        land, idle, snap, fade = fx_snare()
        fx_fixed("FxYsvSnare", [("Land", land, [0.06, 0.06, 0.08, 0.1]), ("Idle", idle, [0.3, 0.3]),
                                ("Snap", snap, [0.04, 0.05, 0.06, 0.2, 0.08, 0.1]), ("Fade", fade, [0.1, 0.1, 0.12])],
                 outdir, (20, 20), (10, 15))
    if want("FxYsvSpire"):
        grow, idle, flash, crumble = fx_spire()
        fx_fixed("FxYsvSpire", [("Grow", grow, [0.06, 0.07, 0.08, 0.09, 0.1]), ("Idle", idle, [0.16, 0.16]),
                                ("Flash", flash, [0.04, 0.05, 0.06]), ("Crumble", crumble, [0.07, 0.08, 0.09, 0.1])],
                 outdir, (22, 30), (11, 27))
    if want("FxYsvSpireBolt"): centered("FxYsvSpireBolt", [("Fly", fx_spire_bolt(), [0.05] * 4)], outdir, (14, 8))
    if want("FxYsvDrain"):
        fly, bead, snap = fx_drain()
        centered("FxYsvDrain", [("Fly", fly, [0.05] * 4), ("Bead", bead, [0.12, 0.12]), ("Snap", snap, [0.05, 0.06, 0.07, 0.08])],
                 outdir, (18, 10))
    if want("FxYsvShimmer"): centered("FxYsvShimmer", [("Play", fx_shimmer(), [0.05, 0.05, 0.06, 0.07, 0.08])], outdir, (28, 24))
    if want("FxYsvVortex"):
        opn, spin, burst = fx_vortex()
        fx_fixed("FxYsvVortex", [("Open", opn, [0.08, 0.08, 0.08]), ("Spin", spin, [0.07] * 4), ("Burst", burst, [0.05, 0.05, 0.06, 0.08, 0.1])],
                 outdir, (42, 32), (21, 24), scale=6)
    if want("FxYsvShieldSpin"): centered("FxYsvShieldSpin", [("Fly", fx_shield_spin(), [0.04] * 4)], outdir, (18, 18))
    if want("FxYsvBurrow"):
        dig, erupt = fx_burrow()
        fx_fixed("FxYsvBurrow", [("Dig", dig, [0.06, 0.07, 0.08, 0.1]), ("Erupt", erupt, [0.05, 0.05, 0.06, 0.08, 0.1, 0.1])],
                 outdir, (44, 30), (22, 22), scale=6)
    if want("FxYsvGrab"):
        hold, fling = fx_grab()
        fx_fixed("FxYsvGrab", [("Hold", hold, [0.12, 0.12]), ("Fling", fling, [0.05, 0.06, 0.07, 0.08])], outdir, (30, 24), (15, 19))
    if want("FxYsvThorns"): fx_fixed("FxYsvThorns", [("Loop", fx_thorns(), [0.14, 0.14])], outdir, (46, 36), (23, 33), scale=6)
    if want("FxYsvThorn"): centered("FxYsvThorn", [("Fly", fx_thorn(), [0.05] * 4)], outdir, (14, 6))
    if want("FxYsvPrismBolt"): centered("FxYsvPrismBolt", [("Fly", fx_prism_bolt(), [0.05] * 4)], outdir, (20, 8))
    if want("FxYsvBeam"):
        charge, fire, fade = fx_beam()
        fx_fixed("FxYsvBeam", [("Charge", charge, [0.08, 0.08, 0.08]), ("Fire", fire, [0.05] * 4), ("Fade", fade, [0.06, 0.07, 0.08])],
                 outdir, (100, 12), (2, 6), scale=5)


# ================================================================== the blizzard perk (floor ice paths + the gust)
# Floor ice is drawn like the dungeon floor itself: a flat, low-contrast slab (no outline, no glow) in a dark slate blue
# close to the floor's own value, wind-combed frost streaks, a hairline crack or two and a ragged frosted edge. The code
# chains 4 shape variants into paths (12 px apart, random flip), so overlapping slabs read as one continuous sheet.
PALETTE.update({
    'j': (0x2f, 0x3b, 0x4d),   # crack / under-shadow (slate)
    'l': (0x45, 0x58, 0x6d),   # floor ice (dark slate blue, lum ~86: a dark dungeon floor's value, cooler)
    'x': (0x58, 0x6e, 0x84),   # frost film
    'z': (0x74, 0x8c, 0xa2),   # combed frost streak / lit rim
    'J': (0xa8, 0xbe, 0xcf),   # glint
})
FLOE_RX, FLOE_RY = 12.5, 6.5


def floe_mask(v):
    """The slab's shape for variant v: three overlapping lobes (deterministic per variant)."""
    r = random.Random(1500 + v)
    lobes = [(0.0, 0.0, FLOE_RX, FLOE_RY)]
    for k in range(2):
        lobes.append((r.uniform(-6, 6), r.uniform(-1.6, 1.6), r.uniform(6.5, 9.5), r.uniform(3.8, 5.2)))
    m = {}
    for (lx, ly, ax, ay) in lobes:
        for y in range(int(ly - ay) - 1, int(ly + ay) + 2):
            for x in range(int(lx - ax) - 1, int(lx + ax) + 2):
                d = ((x - lx) / ax) ** 2 + ((y - ly) / ay) ** 2
                if d <= 1.0: m[(x, y)] = min(m.get((x, y), 9.0), d)
    return m


def floe(v, grow=1.0, melt=0.0, glint=-1, front=False):
    """One ice slab, centred on (0, 0). grow < 1: frost still creeping out from the middle (front=True rims the
    growth front with combed frost); melt > 0: the edge thaws back first, in uneven bites."""
    r = random.Random(2500 + v)
    base = floe_mask(v)
    noise = {k: random.Random(hash(k) * 7 + v).random() for k in base}
    keep = {}
    for k, d in base.items():
        x, y = k
        dd = ((x / max(0.01, grow)) / FLOE_RX) ** 2 + ((y / max(0.01, grow)) / FLOE_RY) ** 2 if grow < 1.0 else d
        if grow < 1.0 and dd > 1.0 + 0.25 * noise[k]: continue
        if grow >= 1.0 and melt > 0.0 and d > 1.15 - melt * 1.1 + 0.35 * noise[k]: continue
        keep[k] = d
    c = cv()
    for (x, y), d in keep.items():
        edge = any((x + a, y + b) not in keep for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            if (x + y) % 2 and d > 0.6: continue                 # ragged, frosted edge (no outline)
            c.put(x, y, "z" if (front and grow < 1.0) or y <= -FLOE_RY + 1 else "x")
        else:
            c.put(x, y, "x" if (y < -FLOE_RY * 0.35 and d > 0.25) else "l")
    # wind-combed frost streaks (left to right, a pixel of drop): only on the slab
    for k in range(3):
        sy = r.randint(-4, 3); sx = r.randint(-9, 2); ln = r.randint(4, 8)
        for (x, y) in line_px(sx, sy, sx + ln, sy + (1 if r.random() < 0.5 else 0)):
            if (x, y) in c.px and c.px[(x, y)] == "l": c.put(x, y, "x")
        if (sx + ln, sy) in c.px and melt < 0.5: c.put(sx + ln, sy, "z")
    # hairline cracks
    if melt < 0.7:
        for k in range(2 if v % 2 == 0 else 1):
            x0 = r.randint(-8, 4); y0 = r.randint(-2, 2)
            pts = [(x0, y0)]
            for s in range(3): pts.append((pts[-1][0] + r.randint(2, 4), pts[-1][1] + r.choice((-1, 0, 1))))
            for a, b in zip(pts, pts[1:]):
                for (x, y) in line_px(a[0], a[1], b[0], b[1]):
                    if (x, y) in c.px and c.px[(x, y)] in "lx": c.put(x, y, "j")
    if glint >= 0:
        gx = -6 + glint * 5 + v
        for (x, y) in ((gx, -2), (gx + 1, -2), (gx + 1, -3)):
            if (x, y) in c.px: c.put(x, y, "J")
    return c.spr()


def fx_floe():
    anims = []
    for v in range(4):
        anims.append(("Form%d" % v, [floe(v, 0.35, front=True), floe(v, 0.65, front=True), floe(v, 0.88, front=True), floe(v)],
                      [0.06, 0.06, 0.07, 0.08]))
        anims.append(("Idle%d" % v, [floe(v), floe(v, glint=v % 3)], [1.6 + 0.3 * v, 0.14]))
        anims.append(("Melt%d" % v, [floe(v, melt=0.25), floe(v, melt=0.5), floe(v, melt=0.75), floe(v, melt=0.95)],
                      [0.18, 0.18, 0.2, 0.22]))
    return anims


def gale(i):
    """The blizzard gust that sweeps the room: a sparse band of wind-driven snow, 72 x 20, moving right (the code
    flips it for a west wind). Long thin streaks with a bright head, a few flakes; scrolls 4 px a frame."""
    c = cv()
    r = random.Random(77)
    streaks = [(r.uniform(-36, 30), r.uniform(-9, 9), r.randint(7, 15)) for _ in range(9)]
    for k, (sx, sy, ln) in enumerate(streaks):
        x = ((sx + 36 + i * 4 + k * 3) % 72) - 36
        y = sy + (i * 0.5 if k % 2 else 0)
        tail = "5" if k % 3 == 0 else "6"
        for (px, py) in line_px(int(x - ln), int(y - 1), int(x), int(y)):
            c.put(px, py, tail)
        c.put(int(x), int(y), "8"); c.put(int(x) - 1, int(y), "7")
    for k in range(12):
        fx = ((r.uniform(-36, 36) + i * 5 + 36) % 72) - 36
        fy = r.uniform(-10, 10) + ((i + k) % 3) * 0.6
        c.put(int(fx), int(fy), "8" if k % 3 == 0 else "7")
    return c.spr()


def build_fx5(outdir, only=None):
    """The blizzard perk."""
    def want(n): return only is None or n in only
    if want("FxYsvFloe"): centered("FxYsvFloe", fx_floe(), outdir, (28, 16), scale=6)
    if want("FxYsvGale"): centered("FxYsvGale", [("Blow", [gale(i) for i in range(6)], [0.05] * 6)], outdir, (76, 24), scale=5)


# ================================================================== TIMING.md + contact sheet
# tier order: T1 x3, T2 x4, T3 x4, then the Matron's minion
# v0.10: T2 ordered by parent, T3 ordered by parent (each T2's two options side by side)
TIERS = [["YsvRimeling", "YsvHoarmoth", "YsvShardling"],
         ["YsvWeaver", "YsvLurker", "YsvSilkmoth", "YsvVeilWitch", "YsvRimeKnight", "YsvHermit"],
         ["YsvMatron", "YsvLoom", "YsvTarantula", "YsvHoarclaw", "YsvEmpress", "YsvGlasswing", "YsvBride", "YsvWraith",
          "YsvColossus", "YsvWarden", "YsvGeode", "YsvOracle"]]
MONSTERS = [n for t in TIERS for n in t] + ["YsvBroodling"]
FXN = ["FxYsvIce", "FxYsvGlob", "FxYsvMote", "FxYsvGust", "FxYsvShard", "FxYsvIcicle", "FxYsvThread", "FxYsvCrystal", "FxYsvEgg",
       "FxYsvBreath", "FxYsvPips", "FxYsvBind", "FxYsvNova", "FxYsvPuff", "FxYsvNeedle", "FxYsvPlates", "FxYsvStorm", "FxYsvSpike",
       "FxYsvCleave", "FxYsvPlateBreak", "FxYsvSplinter", "FxYsvAuroraMote", "FxYsvQuake",
       "FxYsvSnare", "FxYsvSpire", "FxYsvSpireBolt", "FxYsvDrain", "FxYsvShimmer", "FxYsvVortex", "FxYsvShieldSpin", "FxYsvBurrow",
       "FxYsvGrab", "FxYsvThorns", "FxYsvThorn", "FxYsvPrismBolt", "FxYsvBeam", "FxYsvFloe", "FxYsvGale"]
ICONS = ["IconYsvRequiem", "IconYsvShawl", "DeityYsveld"]

# (anim, event, frame index, spawn point relative to the feet or "-")
EVENTS = {
    "YsvSilkmoth": [("Volley", "wings raised, lace glowing", 1, "-"),
                    ("Volley", "RELEASE: 3 FxYsvNeedle in a fan (wing downbeat)", 3, "(7, -10)"),
                    ("Dive", "wings folded (wind-up ends)", 2, "-"),
                    ("Dive", "DIVE: forward rush + contact hit; drop FxYsvIce", 3, "(0, 0) ice at the feet"),
                    ("Dive", "drop a 2nd FxYsvIce", 5, "(0, 0)"),
                    ("Dive", "pull up: stop", 6, "-")],
    "YsvRimeKnight": [("Cleave", "sword overhead", 2, "-"),
                      ("Cleave", "swing (smear)", 3, "-"),
                      ("Cleave", "HIT: blade at full reach; FxYsvCleave spawned at (3, -8)", 4, "tip (17, 0); body (12, -6)"),
                      ("Plate", "sword planted, ice gathering", 1, "-"),
                      ("Plate", "ARMOUR: gain 2 ice plates (FxYsvPlates orbit)", 4, "-")],
    "YsvEmpress": [("Aurora", "wings high", 2, "-"),
                   ("Aurora", "RELEASE: 5 FxYsvAuroraMote in a wide fan (wing downbeat)", 3, "(8, -22)"),
                   ("Whiteout", "storm gathering overhead", 3, "-"),
                   ("Whiteout", "RELEASE: FxYsvStorm homing blizzard", 4, "(10, -14)")],
    "YsvColossus": [("Slam", "fists overhead", 2, "-"),
                    ("Slam", "swing (smear)", 3, "-"),
                    ("Slam", "HIT: fists strike the floor + FxYsvQuake shockwave", 4, "(17, -4) / ring (17, 0)"),
                    ("Glacier", "fist raised", 3, "-"),
                    ("Glacier", "RELEASE: glacier runner along the floor (FxYsvSpike + FxYsvIce trail)", 4, "(15, 0)")],
    "YsvRimeling": [("Bite", "lunge (fangs wide)", 2, "-"),
                    ("Bite", "HIT: fangs snap shut (+1 Rime)", 3, "(10, -3)"),
                    ("Spit", "RELEASE: spit FxYsvGlob from the mouth", 3, "(8, -5)")],
    "YsvBroodling": [("Bite", "HIT: fangs snap shut (+1 Rime)", 3, "(7, -2)")],
    "YsvHoarmoth": [("Dust", "wings snap down (smear)", 2, "-"),
                    ("Dust", "RELEASE: 3 FxYsvMote in a fan", 3, "(6, -8)"),
                    ("Gust", "downbeat (smear)", 3, "-"),
                    ("Gust", "RELEASE: FxYsvGust", 4, "(8, -7)")],
    "YsvShardling": [("Ram", "charge (streaks)", 2, "-"),
                     ("Ram", "HIT: crystal head-butt", 3, "(8, -5)"),
                     ("Icicle", "charging (glow grows)", 1, "-"),
                     ("Icicle", "CALL: FxYsvIcicle Fall at the hero (lands 0.70 s later)", 4, "at hero")],
    "YsvWeaver": [("Fangs", "rear up (wind-up)", 2, "-"),
                  ("Fangs", "HIT: fangs strike down (+1 Rime); fang tip ~ (9, -5) on the v0.8 stilt legs", 3, "(11, -4)"),
                  ("Tether", "abdomen swung over the back, spinnerets aimed", 2, "-"),
                  ("Tether", "RELEASE: FxYsvThread silk line (spinnerets ~ (1, -19) on the v0.8 stilt legs; released at node height)", 3, "(4, -14)"),
                  ("Tether", "haul (thread taut)", 4, "-")],
    "YsvVeilWitch": [("Shard", "wand flick (wind-up ends)", 2, "-"),
                     ("Shard", "RELEASE: FxYsvShard from the wand tip", 3, "(12, -11)"),
                     ("Crystals", "arms raised, crown glowing", 2, "-"),
                     ("Crystals", "CALL: 3 FxYsvCrystal Grow around the hero", 4, "at hero")],
    "YsvMatron": [("Impale", "rear up (wind-up)", 2, "-"),
                  ("Impale", "stab (smear)", 3, "-"),
                  ("Impale", "HIT: front legs impale the floor (+1 Rime)", 4, "(22, -4)"),
                  ("Brood", "abdomen lowered, pulsing", 2, "-"),
                  ("Brood", "RELEASE: lay 2 FxYsvEgg sacs (2nd 0.12 s later at (-16, -7)); each hatches a Broodling", 5, "(-12, 0)")],
    "YsvBride": [("Breath", "veil lifted", 1, "-"),
                 ("Breath", "BREATH 1: FxYsvBreath cone at -12 deg (mouth ~ (10, -22); released at node height 12)", 3, "(11, -14)"),
                 ("Breath", "BREATH 2 (0 deg)", 4, "(11, -14)"),
                 ("Breath", "BREATH 3 (+12 deg)", 5, "(11, -14)"),
                 ("Requiem", "arms and legs raised, icicles gathering", 3, "-"),
                 ("Requiem", "RELEASE: ring of 6 FxYsvIcicle Fall around the hero", 5, "at hero")],
}
EVENTS.update({
    "YsvLurker": [("Bite", "lunge (fangs wide)", 2, "-"), ("Bite", "HIT: fangs snap shut (+1 Rime)", 3, "(11, -4)"),
                  ("Snare", "lid swung open, silk glowing", 2, "-"),
                  ("Snare", "RELEASE: 2 FxYsvSnare flicked down beside the hero (14 px either side)", 4, "at hero")],
    "YsvHermit": [("Jab", "staff drawn back", 1, "-"), ("Jab", "HIT: staff thrust (crystal head)", 3, "(12, -10)"),
                  ("Spire", "staff raised, geode glowing", 2, "-"),
                  ("Spire", "SLAM: staff into the floor; FxYsvSpire Grow in front", 4, "(13, 0)")],
    "YsvLoom": [("Lash", "silk whip drawn back over the head", 1, "-"),
                ("Lash", "HIT: whip cracks along the floor ahead (hit box 24 x 12 centred)", 3, "(20, -6)"),
                ("Feed", "cat's cradle raised, glowing", 3, "-"),
                ("Feed", "RELEASE: FxYsvDrain feeding line from her hands (released at node height 18)", 4, "(12, -18)")],
    "YsvGlasswing": [("Slash", "wings back, darting in", 2, "-"),
                     ("Slash", "HIT: scythe forelegs sweep (+1 Rime)", 3, "(14, -10)"),
                     ("Fade", "glints gathering", 1, "-"),
                     ("Fade", "FADE: goes see-through (code), FxYsvShimmer on the body", 3, "(0, -10)")],
    "YsvWraith": [("Claw", "claws raised", 1, "-"), ("Claw", "HIT: ice claws rake down", 3, "(12, -13)"),
                  ("Maelstrom", "arms up, snow swirling overhead", 3, "-"),
                  ("Maelstrom", "CALL: FxYsvVortex opens on the hero", 5, "at hero")],
    "YsvWarden": [("Smash", "mace overhead", 2, "-"), ("Smash", "swing (smear)", 3, "-"),
                  ("Smash", "HIT: mace strikes the floor ahead", 4, "(15, -5)"),
                  ("Hurl", "shield wound back", 3, "-"),
                  ("Hurl", "RELEASE: FxYsvShieldSpin thrown (flies out 0.4 s, returns to his hand)", 4, "(12, -14)"),
                  ("Hurl", "catch (the shield is back)", 8, "-")],
    "YsvTarantula": [("Bite", "rear up", 2, "-"), ("Bite", "HIT: crushing bite", 3, "(16, -5)"),
                     ("Burrow", "digging (FxYsvBurrow Dig at the feet)", 1, "(0, 0)"),
                     ("Burrow", "UNDER: invulnerable until frame 6", 2, "-"),
                     ("Burrow", "MOVE: surfaces under the hero; the snow mound is the warning (0.5 s)", 4, "at hero"),
                     ("Burrow", "ERUPT: FxYsvBurrow Erupt ring hits (feet, 34 x 14)", 6, "(0, 0)")],
    "YsvHoarclaw": [("Snap", "claws raised wide", 1, "-"), ("Snap", "HIT: pincers snap shut", 3, "(20, -8)"),
                    ("Seize", "claws open", 1, "-"),
                    ("Seize", "GRAB: lunge, pincers close; a caught hero is held at the claws", 2, "(21, -8)"),
                    ("Seize", "HURL: the held hero is thrown away", 6, "-")],
    "YsvGeode": [("Slam", "rocked back", 2, "-"), ("Slam", "HIT: the dome slams down ahead", 4, "(15, -5)"),
                 ("Bristle", "curling in", 1, "-"),
                 ("Bristle", "BRISTLE: thorns out (FxYsvThorns overlay, 3 s, code)", 3, "-")],
    "YsvOracle": [("Bolt", "prism flaring", 2, "-"), ("Bolt", "RELEASE: FxYsvPrismBolt from the prism core", 3, "(2, -14)"),
                  ("Beam", "light gathering in the prism", 2, "-"),
                  ("Beam", "RELEASE: FxYsvBeam from the prism core (lives 1.7 s, turns after the hero)", 3, "(2, -14)")],
})
FX_NOTES = {
    "FxYsvNeedle": "Centred. Fly loop, faces right; silk-wrapped ice needle (Silkmoth Volley).",
    "FxYsvPlates": "Floor point = cell pixel (14, 21). Orbit loop 8 (0.64 s): two ice-armour shards circle 12 px up (Rime Knight plates).",
    "FxYsvStorm": "Centred. Loop 6 (0.48 s), seamless: blizzard knot rx 13 x ry 8.5 (Empress Whiteout; the code loops it 7 times).",
    "FxYsvSpike": "Floor point = cell pixel (9, 15). Play 6 (0.5 s): crack, spike bursts up (1), holds (2-4), crumbles (5) (Colossus Glacier).",
    "FxYsvIce": "Centred on the death point (Strike.ArtAt 18,7). Life = Spread 0-2 (0.1 s), Idle 3-16 (2 frames x7, 0.38 s), "
                "Fade 17-19 (0.2 s) = 6.2 s; the code builds the same sequence from Spread + Idle x7 + Fade. "
                "Ellipse rx 15 x ry 5 px; the slide zone in code is rx 15 x ry 5.5.",
    "FxYsvGlob": "Centred. Fly loop, faces right (silk-frost glob).",
    "FxYsvMote": "Centred. Fly loop (rime dust mote).",
    "FxYsvGust": "Centred. Fly loop, faces right; crescent ~16 px tall.",
    "FxYsvShard": "Centred. Fly loop, faces right; ice shard 9 px long.",
    "FxYsvIcicle": "Floor point = cell pixel (15, 59) (Strike.ArtAt). Fall 8 (0.70 s): shadow ring tightens, the icicle drops from 44 px "
                   "and lands on the last frame. Shatter 5: impact, hit radius ~9 x 5 px.",
    "FxYsvThread": "Centred. Fly = silk line head; Bead = one link of the tether line (loop); Snap = the line breaking.",
    "FxYsvCrystal": "Floor point = cell pixel (18, 25). Grow 7 (0.98 s): crystal cluster rises and cracks; Shatter 5: bursts (the code fires 5 FxYsvShard).",
    "FxYsvEgg": "Floor point = cell pixel (14, 19). Hatch 8 (0.98 s): sac wobbles, cracks, bursts on frame 5.",
    "FxYsvBreath": "Centred. Puff 6: frost cloud grows and thins (0.60 s).",
    "FxYsvPips": "Centred, drawn over the hero's head: One / Two / Three Rime stacks (2-frame loops).",
    "FxYsvBind": "Floor point = cell pixel (14, 23), at the hero's feet. Bind 7 (0.82 s): ice-silk cocoon closes (0-2), holds (3-5), cracks off (6).",
    "FxYsvNova": "Centred. Play 6: frost-silk ring, r = 5..24 px x 0.42 (Widow's Shawl).",
    "FxYsvPuff": "Centred. Play 4: snow puff (hit spark).",
    "FxYsvCleave": "Origin = cell pixel (16, 18) = the effect spawn (Strike.ArtAt 16,18). Slash 4 (0.42 s, vanilla 1HandedSwordSwipe2 "
                   "timing): ice crescent from 11 px above the origin to 8 px below, out to x 15; damage on frame 0 (Rime Knight Cleave).",
    "FxYsvPlateBreak": "Floor point = cell pixel (15, 23). Play 5 (0.34 s): an ice plate 12 px up cracks (0), splits (1), bursts into flakes (2-4).",
    "FxYsvSplinter": "Centred. Fly loop: a tumbling ice sliver (Veil Witch crystal burst, 5 per crystal).",
    "FxYsvAuroraMote": "Centred. Fly loop, faces right: cold-light bead with a teal-to-violet aurora ribbon (Pale Empress Aurora).",
    "FxYsvSnare": "Floor point = cell pixel (10, 15). Land 4 (0.30 s) + Idle 2 (loop) + Fade 3: frost-silk snare rx 7 x ry 3 "
                  "(Rime Lurker). Snap 6 (0.53 s): strands lash shut round the hero's feet.",
    "FxYsvSpire": "Floor point = cell pixel (11, 27). Grow 5 (0.40 s), Idle 2 (loop), Crumble 4 (0.34 s): geode spire ~21 px tall "
                  "(Shard Hermit); Flash 3 = the tip flare, drawn at the tip (21 px up) from the same origin.",
    "FxYsvSpireBolt": "Centred. Fly loop: tumbling geode bead (the spire's shot).",
    "FxYsvDrain": "Centred. Fly = barbed silk hook; Bead = one droplet of drawn life on the feeding line; Snap = the line breaking "
                  "(Loom Widow).",
    "FxYsvShimmer": "Centred. Play 5: glass glints scatter (Glasswing fading in or out).",
    "FxYsvVortex": "Floor point = cell pixel (21, 24). Open 3, Spin 4 (loop, rx 18 x ry 7), Burst 5 (pillar of frost, the hit; "
                   "frames 1-3) (Snow Wraith).",
    "FxYsvShieldSpin": "Centred. Fly loop: the Rime Warden's spiked round shield spinning face-on.",
    "FxYsvBurrow": "Floor point = cell pixel (22, 22). Dig 4 (snow spray), Erupt 6: ring of ice shards r 6..18 (hit frames 0-2) "
                   "(Hoarfrost Tarantula).",
    "FxYsvGrab": "Floor point = cell pixel (15, 19), at the hero's feet. Hold 2 (loop): frost shackles; Fling 4: they burst (Hoarclaw).",
    "FxYsvThorns": "Floor point = cell pixel (23, 33), at the Geode's feet. Loop 2: crown of crystal thorns round the dome.",
    "FxYsvThorn": "Centred. Fly loop, faces right: one crystal thorn thrown back at the hero (Geode Bristle).",
    "FxYsvPrismBolt": "Centred. Fly loop, faces right: ice diamond with a teal / violet ribbon (Prism Oracle).",
    "FxYsvFloe": "Centred. Blizzard floor ice: 4 slab variants (rx 12.5, ry 6.5), FormN 4 (0.27 s), IdleN 2 (loop), MeltN 4 (0.78 s). Chained 12 px apart into paths, drawn at floor depth.",
    "FxYsvGale": "Centred. Blizzard gust: Blow 6 (0.30 s loop), a sparse 72 x 20 band of driven snow; the code slides it across the room.",
    "FxYsvBeam": "Origin = cell pixel (2, 6), the beam runs 96 px to the right. Charge 3, Fire 4 (loop), Fade 3 (Prism Oracle).",
    "FxYsvQuake": "Centred (Strike.Ground 26,12). Play 5 (0.31 s): glacier-ice ring r = 5..24 px x 0.42, ice heaved up on frames 1-3 "
                  "(Rime Colossus slam; damage frames 0-3).",
}


V08_NOTES = [
    "## v0.8 art pass", "",
    "- Spider line: YsvRimeling is a pale ice spiderling with two rime crystals (style rime); YsvWeaver is violet silk on",
    "  stilt legs, abdomen carried high and banded with black thread, no crystals (style stilt, S 1.24; she stands ~3 px",
    "  higher: Fangs hit ~ (9, -5) -> kit (11, 4); Tether spawn (4, 14), Strike.Feet node 12); YsvMatron keeps the black",
    "  widow body but wears ice-plated legs, a crown of icicles over the front and a clutch of pearl egg sacs on her back.",
    "- YsvBride is the Veil Witch's negative: white bell gown with a train, black lace veil (the witch: black gown lifted a",
    "  step, frost veil).",
    "- Knight line: YsvRimeKnight silver plate, navy cape/tabard, white plume; YsvColossus glacier teal (GLACIER remap).",
    "- YsvSilkmoth silk lifted a step (luminance 74 -> 85). YsvShardling Idle has 4 unique frames.",
    "- YsvBroodling Spawn 3 (0.28 s, vanilla tiny-rat timing): hatches out of torn egg silk (its base plays a spawn clip).",
    "- New FX: FxYsvCleave (replaces the tinted vanilla OrcSwipe), FxYsvPlateBreak (was FxYsvCrystal Shatter), FxYsvSplinter",
    "  (was FxYsvShard), FxYsvAuroraMote (was the Hoarmoth FxYsvMote), FxYsvQuake (was FxYsvNova, which stays the Widow's",
    "  Shawl ring).", "",
    "## v0.9 lineage pass",
    "",
    "Strike points, sync frames and hitboxes unchanged.",
    "- YsvWeaver (Rimeling): keeps the Rimeling's rime crystals (three) on her banded violet abdomen.",
    "- YsvSilkmoth (Rimeling + Hoarmoth): the Hoarmoth's white fur ruff and frost-edged wings over four long ice spider legs",
    "  and a rime crystal (Rimeling).",
    "- YsvVeilWitch (Hoarmoth + Shardling): the Hoarmoth's frost wings folded down her back (eye-spot, black margins) and its",
    "  feathered antennae as crown plumes; the Shardling's crystals grow through her hem, plus its crystal crown and wand.",
    "- YsvRimeKnight (Shardling): silver plate with the Shardling's violet silk (cape) and crystal horn/pauldron spikes.",
    "- YsvMatron (Weaver + Rime Knight): the Weaver's banded violet silk; the knight's silver helm (visor, crystal horn),",
    "  plate bands round the abdomen and silver legs; pearl egg clutch on her back.",
    "- YsvEmpress (Weaver + Silkmoth): the Silkmoth's lace wings; three pairs of the Weaver's long violet stilt legs.",
    "- YsvBride (Silkmoth + Veil Witch): the witch's gown, crown and plumes; the Silkmoth's violet-and-frost wings and spider legs.",
    "- YsvColossus (Veil Witch + Rime Knight): glacier-cyan ice, the witch's violet hood, icicle crown and plumes, the",
    "  knight's crystal greatsword driven into its back.",
    "- All monster cells now have an even height (a spare top row); feet stay 2 rows above the bottom.",
    "",
    "## v0.10 final art review",
    "",
    "- YsvRimeKnight: gunmetal steel plate (KNIGHT remap) and a steel kite shield with a crystal boss on the back arm, so it",
    "  reads armoured next to the robed, pale-winged Veil Witch in the Shardling's evolve menu.",
    "- YsvEmpress: wings are clean shaded panels (no checker dither): violet root, frost band, pale margin; single-pixel legs.",
    "- YsvBroodling lifted two steps (BROOD_LIFT).",
    "- FX noise: FxYsvGust redrawn as solid crescents, FxYsvIce Fade and FxYsvBreath thin cleanly, FxYsvPlates shards larger",
    "  (cell pinned at 28 x 22, origin (14, 21)), FxYsvEgg burst floor solid.",
    ""]


V08_NOTES += [
    "## v0.10 unique-evolution tree", "",
    "Every evolution has one parent: Rimeling -> Weaver | Lurker; Hoarmoth -> Silkmoth | Veil Witch; Shardling -> Rime Knight |",
    "Hermit; Weaver -> Matron | Loom; Lurker -> Tarantula | Hoarclaw; Silkmoth -> Empress | Glasswing; Veil Witch -> Bride |",
    "Wraith; Rime Knight -> Colossus | Warden; Hermit -> Geode | Oracle.",
    "- Motifs of parents a monster no longer has were redrawn: Matron (knight helm and plate bands -> the Weaver's frost lace",
    "  and rime crystals, violet silk legs), Empress (the Weaver's stilt legs -> the Silkmoth's short furred legs), Bride (no",
    "  spider legs), Colossus (the witch's hood, crown and plumes -> the knight's gunmetal great-helm and white plume),",
    "  Silkmoth (no spider legs or Rimeling crystal: short furred legs, fur tufts), Veil Witch (no Shardling hem crystals:",
    "  fur trim).",
    "- New sheets: YsvLurker, YsvHermit (T2); YsvLoom, YsvTarantula, YsvHoarclaw, YsvGlasswing, YsvWraith, YsvWarden,",
    "  YsvGeode, YsvOracle (T3); FX FxYsvSnare, Spire, SpireBolt, Drain, Shimmer, Vortex, ShieldSpin, Burrow, Grab, Thorns,",
    "  Thorn, PrismBolt, Beam.", ""]


def write_timing(outdir):
    L = ["# Ysveld, the Frost Widow: sprite timing", "",
         "Generated by `tools/sprites/ysveld_rigs.py`. Frame indices are 0-based within the anim; `t` is the time",
         "from the start of the anim to the start of that frame. Monsters face right.",
         "Monster sheets: feet = (cellW//2, cellH-2). Spawn points are pixels relative to the feet (x right, y up NEGATIVE),",
         "facing right; mirror x when flipped. \"at hero\" = the effect is placed on the hero (ClosestEnemy), not the monster.", "",
         "## Monster sheets", "", "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n in MONSTERS:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, cw // 2, ch - 2, b["idle_wh"][0], b["idle_wh"][1],
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
            assert fi < k
            L.append("| %d | %.2f | %s | %s |" % (fi, sum(d[:fi]), ev, sp))
            if idx == len(evs) - 1 or evs[idx + 1][0] != an: L.append("")
    L += ["Every attack has at least two wind-up frames before its first event. Death plays once and ends on the corpse;",
          "Dead is that same corpse frame. Ysveld monsters leave a 3-slab FxYsvFloe patch where they die (FxYsvIce is unused).", "",
          "## FX sheets", "", "| Sheet | Cell (w x h) | Origin | Anims (frames, total s) | Notes |", "|---|---|---|---|---|"]
    for n in FXN:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1],
                 ", ".join("%s %d, %.2f s" % (a, k, sum(d)) for a, k, d in b["anims"]), FX_NOTES[n]))
    L += ["", "## Icons and portrait", "", "| Sheet | Cell | Anims |", "|---|---|---|"]
    for n in ICONS + ["IconYsvRequiemBubble", "IconYsvRequiemHud", "IconYsvShawlBubble", "IconYsvShawlHud"]:
        if n not in BUILT: continue
        b = BUILT[n]; cw, ch = b["cell"]
        L.append("| %s | %d x %d | %s |" % (n, cw, ch, ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += [""] + V08_NOTES
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")
    print("wrote", os.path.join(outdir, "TIMING.md"))


def contact_sheet(outdir, path=None, S=4):
    """Every roster monster's Idle frame at S x, one row per tier on a shared floor line, + the god portrait."""
    from PIL import Image, ImageDraw
    def idle_cell(n):
        b = BUILT[n]; img, man = b["img"], b["man"]
        cw, chh = man["cellW"], man["cellH"]
        fi = man["anims"][0]["frames"][0]
        x0, y0 = (fi % man["cols"]) * cw, (fi // man["cols"]) * chh
        c = img.crop((x0, y0, x0 + cw, y0 + chh))
        bb = c.getbbox()
        return c.crop((bb[0], 0, bb[2], chh)), chh - 2   # keep the floor row (feet at cellH-2)
    rows = []
    for tier in TIERS:
        rows.append([idle_cell(n) for n in tier if n in BUILT])
    portrait = BUILT["DeityYsveld"]["img"].crop((0, 0, 29, 24)) if "DeityYsveld" in BUILT else None
    gap, lab = 6, 10
    row_h = [max(f for c, f in r) + 4 for r in rows]
    W = max(sum(c.size[0] for c, f in r) + gap * (len(r) + 1) for r in rows) + lab + 34
    H = sum(row_h) + 2
    bg = Image.new("RGBA", (W * S, H * S), (52, 44, 40, 255))
    d = ImageDraw.Draw(bg)
    y = 0
    for t, r in enumerate(rows):
        floor = y + row_h[t] - 2
        d.line([(0, floor * S), (W * S, floor * S)], fill=(72, 64, 60, 255), width=max(1, S // 2))
        for k in range(t + 1):   # tier pips
            d.rectangle([(2 + k * 3) * S, (floor - 4) * S, (3 + k * 3) * S, (floor - 3) * S], fill=(140, 190, 230, 255))
        x = lab + gap
        for c, fy in r:
            bg.alpha_composite(c.resize((c.size[0] * S, c.size[1] * S), Image.NEAREST), (x * S, (floor - fy) * S))
            x += c.size[0] + gap
        y += row_h[t]
    if portrait is not None:
        bg.alpha_composite(portrait.resize((29 * S, 24 * S), Image.NEAREST), ((W - 31) * S, 2 * S))
    bg.convert("RGB").save(path or os.path.join(outdir, "contact_idle.png"))
    print("contact sheet", path or os.path.join(outdir, "contact_idle.png"))


# ================================================================== main
def main():
    args = sys.argv[1:]
    only = None
    contact = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    if "--contact" in args:
        i = args.index("--contact"); contact = args[i + 1]; del args[i:i + 2]
    outdir = args[0] if args else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    jobs = [("YsvRimeling", lambda o: build_rimeling(o)), ("YsvHoarmoth", build_hoarmoth), ("YsvShardling", build_shardling),
            ("YsvWeaver", build_weaver), ("YsvVeilWitch", build_witch), ("YsvMatron", build_matron), ("YsvBride", build_bride),
            ("YsvBroodling", lambda o: build_rimeling(o, "YsvBroodling", 0.68)),
            ("YsvSilkmoth", build_silkmoth), ("YsvRimeKnight", build_knight), ("YsvEmpress", build_empress),
            ("YsvColossus", build_colossus),
            ("YsvLurker", build_lurker), ("YsvHermit", build_hermit), ("YsvLoom", build_loom), ("YsvGlasswing", build_glasswing),
            ("YsvWraith", build_wraith), ("YsvWarden", build_warden), ("YsvTarantula", build_tarantula), ("YsvHoarclaw", build_hoarclaw),
            ("YsvGeode", build_geode), ("YsvOracle", build_oracle)]
    for n, fn in jobs:
        if only is None or n in only:
            fn(outdir)
    if only is None or only & set(FXN):
        build_fx(outdir, None if only is None else only & set(FXN))
        build_fx2(outdir, None if only is None else only & set(FXN))
        build_fx3(outdir, None if only is None else only & set(FXN))
        build_fx4(outdir, None if only is None else only & set(FXN))
        build_fx5(outdir, None if only is None else only & set(FXN))
    if only is None or only & set(ICONS):
        build_icons(outdir)
    if only is None:
        contact_sheet(outdir)
        if contact: contact_sheet(outdir, contact)
        write_timing(outdir)
        for n in MONSTERS:
            w, h = BUILT[n]["idle_wh"]
            print("  idle %-14s %2d x %2d" % (n, w, h))


if __name__ == "__main__":
    main()
