"""VHORRUL, THE TALLOW SAINT: the two v0.7.2 finals and their effects.

    python3 vhorrul_t3.py [outdir]          (default art/out; writes only the sheets below)

  VhChandelier  T3  Grand Chandelier: a cathedral chandelier fallen from its chain, walking on its scrolled
                    iron arms. Two tiers of candles, wax stalactites, a single ember eye in the glass heart.
                    Moves: Whirl (spins its ring, the candles lash all round it and fling wax) and
                    Candlefall (shakes its candles loose; they drop on the hero from above).
  VhAshSeraph   T3  Ashen Seraph: a wax-plated knight on great ash-moth wings, crowned with three wicks,
                    carrying a candle-lance. Moves: Lance (a wing-borne lunge) and Halo (five cinder moths
                    circle it as a burning ward, then scatter).
  LanternWraith T3  (v0.8 redraw, was big_rigs.build_wraith) a hovering grave-robe in dusk grey with a dripping wax
                    mantle, a bone mask in its hood and a soul lantern: Idle 4, Run 6, Swing 6, BlinkOut 6, BlinkIn 6,
                    Beam 6, Death 4.
  FxCandleFall      a candle falling from above onto a shadow, shattering into flame.
  FxCinderMoth      a small ember-winged moth (the Seraph's halo).

Same hand as the older Vhorrul rigs (big_rigs.py, knight_rig.py, candelabra_rig.py): pack palette only,
wax in w/W/X, flames o/O/Y/y, iron k/m/s, ash g/h/i; drawn with the shaded primitives of the newer packs
(belmora_rigs.py): every frame is a fresh pose lit from the top-left, then a 1px dark outline, then glow
pixels (flames, eyes) on top. Existing Vhorrul sheets are built by build_rigs.py and are not touched here.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, pack, preview  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out")

# material ramps, dark -> light (pack palette)
IRON = "Kmss"
IRON_L = "msS"
BRASS = "kAew"
WAX = "hwWX"
WAX_D = "ghwW"
ASH = "kghi"
ASH_D = "Kkgh"
PLATE = "hwWX"
RUST = "kaa"
CLOTH = "Kms"
FLAMES = set("oOYy")
GLOW = set("oOYyRrBc")


# ------------------------------------------------------------------ primitives
def pick(ramp, l):
    n = len(ramp)
    i = int((l + 1.0) * 0.5 * n)
    return ramp[max(0, min(n - 1, i))]


def P(x, y):
    return int(round(x)), int(round(y))


def ell(c, cx, cy, rx, ry, ramp, ang=0.0, bias=0.0, vmax=None, vmin=None, over=True, shader=None):
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
            l = 0.8 * (-(wx + wy) / 1.414) + 0.35 * (1 - d) - 0.12 + bias
            ch = pick(ramp, l)
            if shader:
                ch = shader(nu, nv, d, l, ch, x, y)
                if ch is None: continue
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
                if math.hypot(ox, oy) > r + 0.15: continue
                l = bias if r < 0.75 else -(ox + oy) / (r * 1.414) * 0.9 + 0.15 + bias
                c.put(x, y, pick(ramp, l), over)


def line(c, x0, y0, x1, y1, ch, over=True):
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    for i, (x, y) in enumerate(pts):
        c.put(x, y, ch[i % len(ch)], over)
    return pts


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


class Fr:
    """A frame: b = outlined body, u = outlined under-layer (behind b), n = far layer (no outline),
    g = glow pixels laid last."""
    def __init__(self):
        self.b, self.g, self.u, self.n = Canvas(), Canvas(), Canvas(), Canvas()

    def done(self, outline=True, clip=True, ink="K"):
        base = dict(self.u.px)
        base.update(self.b.px)
        spr = Spr(base)
        if outline: spr = outl(spr, ink)
        px = dict(self.n.px)
        px.update(spr.px)
        px.update(self.g.px)
        if clip: px = {k: v for k, v in px.items() if k[1] <= 0}
        return Spr(px)


def outl(spr, ch="K"):
    out = dict(spr.px)
    for (x, y) in spr.px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in spr.px: out[k] = ch
    return Spr(out)


def flame(c, x, y, size=1, phase=0, over=True):
    """Candle flame standing on (x, y) (the wick top). size 0 = bud, 1 = normal, 2 = blazing, 3 = roaring."""
    x, y = P(x, y)
    lean = [0, 1, 0, -1][phase % 4]
    if size <= 0:
        c.put(x, y - 1, "o", over); c.put(x, y - 2, "O" if phase % 2 else "o", over)
        return
    if size == 1:
        c.put(x, y - 1, "Y", over); c.put(x, y - 2, "O", over); c.put(x + (lean if phase % 2 else 0), y - 3, "o", over)
        if phase % 2: c.put(x - lean, y - 1, "o", over)
        return
    h = 4 if size == 2 else 6
    for i in range(h):
        k = i / (h - 1)
        w = 1 if k > 0.55 else (2 if size >= 3 and k < 0.35 else 1)
        dx = int(round(lean * k * (1.5 if size >= 3 else 1)))
        core = "y" if (k < 0.3 and size >= 2) else ("Y" if k < 0.55 else ("O" if k < 0.85 else "o"))
        c.put(x + dx, y - 1 - i, core, over)
        if w >= 2 or (k < 0.5):
            c.put(x + dx - 1, y - 1 - i, "O" if k < 0.5 else "o", over)
            c.put(x + dx + 1, y - 1 - i, "o" if (i + phase) % 2 else "O", over)


def candle(fr, x, y, h, phase=0, size=1, lit=True, drip=0, layer="b"):
    """A wax candle standing on (x, y): 2px wide wax column h tall, wick, flame to the glow layer."""
    c = getattr(fr, layer)
    x, y = P(x, y)
    for i in range(h):
        c.put(x, y - i, "W" if i < h - 1 else "X")
        c.put(x + 1, y - i, "w" if i < h - 1 else "W")
    if drip:
        for i in range(drip):
            c.put(x - 1, y - h + 2 + i, "w" if i < drip - 1 else "h")
    top = y - h
    if lit:
        fr.g.put(x, top, "k")
        flame(fr.g, x, top, size=size, phase=phase)
    else:
        fr.g.put(x, top, "k"); fr.g.put(x, top - 1, "s"); fr.g.put(x + (phase % 2), top - 2, "S")


def stone_of(spr):
    return spr.stone()


# ------------------------------------------------------------------ sheet helpers
BUILT = {}


def sheet(name, anims, outdir, scale=5, pad=2):
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
    idle = anims[0][1][0].bbox()
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "idle": (idle[2] - idle[0] + 1, -idle[1] + 1),
                   "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-14s cell %dx%d  idle %dx%d  %s" % (name, cw, ch, BUILT[name]["idle"][0], BUILT[name]["idle"][1],
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
    BUILT[name] = {"cell": (cw, ch), "feet": (hw, h), "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-14s cell %dx%d origin (%d, %d)  %s" % (name, cw, ch, hw, h, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def std_tail(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


# ================================================================== GRAND CHANDELIER (T3)
def bez(p0, p1, p2, p3, n=10):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                    u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]))
    return out


def scroll_leg(fr, hx, hy, fx, fy, side, lift=0.0, layer="b", curl=1.0):
    """A wrought-iron chandelier arm used as a leg: leaves the ring up and outward in an arch, comes down
    to a scrolled foot. (hx, hy) = root on the ring, (fx, fy) = foot."""
    c = getattr(fr, layer)
    fy = fy - lift
    top = min(hy, fy) - 6.0 - lift * 0.5
    pts = bez((hx, hy), (hx + side * 3.5, top), (fx + side * 2.5, top + 2.0), (fx, fy - 1.5), 9)
    tube(c, pts, [0.95, 0.9, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.55, 0.5], IRON_L if layer == "b" else "Kmm")
    # the scrolled foot: the arm curls back under itself
    tx, ty = P(fx, fy)
    for dx, dy, ch in ((0, 0, "m"), (-side, 0, "s"), (-side * 2, -1, "m"), (-side, -1, "K")):
        c.put(tx + dx, ty + dy, ch)
    if curl:
        # a brass collar where the arm leaves the ring
        rx_, ry_ = P(pts[2][0], pts[2][1])
        c.put(rx_, ry_, "e"); c.put(rx_, ry_ + 1, "A")


def chandelier(dy=0.0, rot=0.0, tilt=0.0, legs=None, lit=1, phase=0, eye="open", candles_on=True, stubs=False,
               flame_size=1, trail=0, rise=0.0, chains=True, sway=0.0, drip_len=0, top_lit=True, extra=None):
    """dy: body height offset (negative = up). rot: candle ring rotation (deg). tilt: ring lean (px, + = front up).
    legs: 4 (dx, lift) tuples for the feet, back pair first. trail: whirl flame streak strength (0-2)."""
    f = Fr()
    cx, cy = sway, -13.0 + dy
    rx, ry = 13.0, 3.6
    legs = legs or [(0, 0), (0, 0), (0, 0), (0, 0)]
    # ---- back legs (far layer, darker) ----
    for i, (side, root, foot) in enumerate(((-1, -7, -11), (1, 7, 12))):
        ldx, lift = legs[i]
        scroll_leg(f, cx + root, cy + 1.5, cx * 0.5 + foot + ldx, 0.0, side, lift=lift, layer="n", curl=0)
    # ---- chains and the upper crown ----
    uy = cy - 7.0 - rise
    if chains:
        for sx in (-7, 0, 7):
            pts = line_px(int(round(cx + sx)), int(round(cy - 1)), int(round(cx + sx * 0.45)), int(round(uy)))
            for k, (x, y) in enumerate(pts):
                f.u.put(x, y, "s" if k % 2 else "m")
        for sx in (-5, 5):
            pts = line_px(int(round(cx + sx)), int(round(uy)), int(round(cx)), int(round(uy - 7)))
            for k, (x, y) in enumerate(pts):
                f.u.put(x, y, "S" if k % 2 else "s")
        hx, hy = P(cx, uy - 8)
        for dx, dy_, ch in ((0, 0, "s"), (-1, -1, "s"), (1, -1, "S"), (0, -2, "s"), (0, 1, "m")):
            f.u.put(hx + dx, hy + dy_, ch)
    # upper ring (small brass band) with three candles
    def ring(layer, ccx, ccy, rrx, rry, front):
        c = getattr(f, layer)
        for k in range(72):
            a = math.radians(k * 5)
            x, y = ccx + rrx * math.cos(a), ccy + rry * math.sin(a) - tilt * math.cos(a) * 0.25
            fr_ = math.sin(a) >= 0
            if fr_ != front: continue
            ch = pick(BRASS, -math.cos(a) * 0.5 + (0.6 if front else -0.4) - math.sin(a) * 0.2)
            c.put(*P(x, y), ch)
            c.put(*P(x, y + 1), "A" if front else "k", over=False)
    ring("u", cx, uy, 6.0, 1.6, False)
    for k in range(3):
        a = math.radians(rot * 1.0 + 210 + k * 120)
        if math.sin(a) < 0:
            candle(f, cx + 6.0 * math.cos(a) - 0.5, uy + 1.6 * math.sin(a), 3, phase=phase + k, size=flame_size if top_lit else 0,
                   lit=candles_on and lit, layer="u")
    ring("b", cx, uy, 6.0, 1.6, True)
    for k in range(3):
        a = math.radians(rot * 1.0 + 210 + k * 120)
        if math.sin(a) >= 0:
            candle(f, cx + 6.0 * math.cos(a) - 0.5, uy + 1.6 * math.sin(a), 3, phase=phase + k, size=flame_size if top_lit else 0,
                   lit=candles_on and lit)
    # ---- lower ring: back half, back candles ----
    ring("u", cx, cy, rx, ry, False)
    ncand = 7
    def lower_candles(front):
        for k in range(ncand):
            a = math.radians(rot + 90 + k * 360.0 / ncand)
            if (math.sin(a) >= 0) != front: continue
            x = cx + rx * math.cos(a) - 0.5
            y = cy + ry * math.sin(a) - tilt * math.cos(a) * 0.5
            h = 5 if k % 2 == 0 else 4
            if stubs:
                h = 2
            if candles_on or stubs:
                candle(f, x, y, h, phase=phase + k, size=flame_size, lit=lit, drip=1 if k % 3 == 0 else 0,
                       layer="b" if front else "u")
            else:
                c = f.b if front else f.u
                c.put(*P(x, y), "A"); c.put(*P(x + 1, y), "k")
                f.g.put(*P(x, y - 1), "s")
    lower_candles(False)
    # ---- the heart (v0.10 lineage, one parent: the Candelabra): the Candelabra's weeping skull hangs under the ring in
    #      an iron cage, wax dripping off its jaw (v0.9 had the Chandler's bucket of molten wax here) ----
    bt, bb = cy + 1.0, cy + 8.0
    skx, sky = cx + 0.5, cy + 4.5
    for yy in range(int(round(bt)), int(round(bb)) + 1):              # the cage bars
        for xx in (-4, 4):
            f.b.put(*P(skx + xx * (1.0 - 0.15 * (yy - bt) / (bb - bt)), yy), "k" if yy % 2 else "A")
    for xx in range(-4, 5):
        f.b.put(*P(skx + xx, bt), "A"); f.b.put(*P(skx + xx * 0.6, bb), "k")
    ell(f.b, skx, sky - 0.3, 3.0, 2.6, "SXXX", bias=0.2)                     # the skull: pale bone like the Candelabra's
    f.b.put(*P(skx - 1, sky), "K"); f.b.put(*P(skx + 1, sky), "K")          # sockets
    for xx in (-1, 0, 1): f.b.put(*P(skx + xx, sky + 2), "S" if xx else "K")
    tipx, tipy = P(skx, bb + 1)
    f.b.put(tipx, tipy, "W"); f.b.put(tipx, tipy + 1, "w")
    # ---- front legs ----
    for i, (side, root, foot) in enumerate(((-1, -11, -15), (1, 11, 16))):
        ldx, lift = legs[2 + i]
        scroll_leg(f, cx + root, cy + 1.0, cx * 0.5 + foot + ldx, 0.0, side, lift=lift, layer="b")
    # ---- lower ring front band ----
    ring("b", cx, cy, rx, ry, True)
    # wax stalactites hanging off the ring
    for sx, n in ((-10, 2 + drip_len), (-5, 3 + drip_len), (4, 2 + drip_len), (9, 3 + drip_len)):
        x, y = P(cx + sx, cy + ry * math.sqrt(max(0.0, 1 - (sx / rx) ** 2)) + 1)
        for i in range(n):
            f.b.put(x, y + i, "W" if i < n - 1 else "w")
    lower_candles(True)
    # ---- the skull's eyes (the Candelabra's) and its tear ----
    if eye == "open":
        f.g.put(*P(skx - 1, sky), "R"); f.g.put(*P(skx + 1, sky), "r")
        f.g.put(*P(skx + 1, sky + 1 + phase % 2), "B"); f.g.put(*P(skx + 1, sky + 2 + phase % 2), "b")
    elif eye == "wide":
        f.g.put(*P(skx - 1, sky), "Y"); f.g.put(*P(skx + 1, sky), "Y"); f.g.put(*P(skx, sky - 2), "R")
        f.g.put(*P(skx + 1, sky + 1), "B")
    elif eye == "dim":
        f.g.put(*P(skx - 1, sky), "p"); f.g.put(*P(skx + 1, sky), "p")
    # ---- whirl streaks: flame arcs swept around the ring ----
    if trail:
        for k in range(ncand):
            a0 = rot + 90 + k * 360.0 / ncand
            for j in range(1, 3 + 2 * trail):
                a = math.radians(a0 - j * 9)
                x = cx + (rx + 2 + trail) * math.cos(a)
                y = cy - 4 + (ry + 1.5 + trail * 0.7) * math.sin(a)
                ch = "Y" if j == 1 else ("O" if j < 3 + trail else "o")
                if (j + k) % 4 == 3 and j > 2: continue
                f.g.put(*P(x, y), ch, over=False)
    if extra: extra(f)
    return f.done()


def chand_corpse(stage):
    """Death: the ring drops, candles roll off, the legs splay."""
    f = Fr()
    cy = -4.0
    if stage == 0:
        return chandelier(dy=6, tilt=-3, legs=[(-2, 0), (2, 0), (-3, 0), (3, 0)], eye="dim", lit=0, flame_size=0, drip_len=2)
    rx, ry = 13.0, 3.6
    # splayed legs flat on the floor
    for side in (-1, 1):
        tube(f.u, [(side * 8, cy + 1), (side * 14, -1.5), (side * 19, 0)], [1, 0.9, 0.7], IRON)
        tube(f.b, [(side * 11, cy + 2), (side * 17, -1), (side * 21, 0)], [1, 0.9, 0.7], IRON_L)
    # ring lying tilted
    for k in range(72):
        a = math.radians(k * 5)
        x, y = rx * math.cos(a), cy + ry * math.sin(a) - 1.2 * math.cos(a)
        f.b.put(*P(x, y), pick(BRASS, -math.cos(a) * 0.5 + 0.2))
    ell(f.b, 1, cy + 1, 3.6, 3.0, IRON_L)
    f.g.put(2, int(cy + 1), "p")
    # spilled candles and wax
    rnd = random.Random(4)
    for sx in (-17, -9, 6, 13, 19):
        x = sx; y = 0
        f.b.put(x, y - 1, "W"); f.b.put(x + 1, y - 1, "X"); f.b.put(x + 2, y - 1, "w")
        if stage == 1 and rnd.random() < 0.6:
            f.g.put(x + 3, y - 1, "o"); f.g.put(x + 3, y - 2, "O")
        elif stage == 2:
            f.g.put(x + 3, y - 2, "s"); f.g.put(x + 3 + (sx % 2), y - 3, "S")
        elif stage >= 3:      # v0.8: the last frame is its own: smoke gone, the wax has run out into a pool
            f.n.put(x - 1, 0, "w"); f.n.put(x + 3, 0, "h")
    for x in range(-6 - 2 * max(0, stage - 2), 8 + 2 * max(0, stage - 2)):
        f.n.put(x, 0, "w" if x % 3 else "W")
    return f.done()


def build_chandelier(outdir):
    idle = [chandelier(dy=[0, -0.4, -0.8, -0.4][i], rot=[0, 2, 4, 2][i], phase=i, sway=[0, 0, 0, 0][i],
                       legs=[(0, 0), (0, 0), (0, 0), (0, 0)]) for i in range(4)]
    # run: a scuttle - the legs step in diagonal pairs while the ring bobs and the candles slosh
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        lA, lB = max(0.0, math.sin(t)) * 3.0, max(0.0, -math.sin(t)) * 3.0
        sA, sB = math.cos(t) * 2.0, -math.cos(t) * 2.0
        run.append(chandelier(dy=-1 + abs(math.sin(t)) * -1.0, rot=i * 4, phase=i, sway=1,
                              legs=[(sA, lA), (sB, lB), (sB, lB), (sA, lA)], tilt=1))
    # Whirl (attack): crouch, spin up, two full lashing turns, settle
    whirl = []
    wspec = [  # (dy, rot, trail, legs lift, eye, flame)
        (1.5, 0, 0, 0, "open", 1),
        (2.0, -12, 0, 0, "wide", 2),
        (-2.0, 40, 1, 3, "wide", 2),
        (-2.5, 95, 2, 4, "wide", 3),
        (-2.5, 150, 2, 4, "wide", 3),
        (-2.5, 205, 2, 4, "wide", 3),
        (-1.5, 250, 1, 2, "wide", 2),
        (0.5, 275, 0, 0, "open", 1),
    ]
    for k, (dy, rot, tr, lift, eye, fs) in enumerate(wspec):
        whirl.append(chandelier(dy=dy, rot=rot, trail=tr, phase=k, eye=eye, flame_size=fs,
                                legs=[(1 if lift else 0, lift), (-1 if lift else 0, lift), (2 if lift else 0, lift), (-2 if lift else 0, lift)]))
    # Candlefall (special): shudder, rear up with the candles blazing, fling them skyward, stand bare, relight
    def sparks_up(h):
        def ex(f):
            for k, sx in enumerate((-12, -6, 0, 6, 12)):
                y = -27 - h - (k % 2) * 3
                f.g.put(sx, y, "W"); f.g.put(sx, y + 1, "w"); f.g.put(sx, y - 1, "O"); f.g.put(sx, y - 2, "o")
                f.g.put(sx, y + 3, "o"); f.g.put(sx, y + 5, "s")
        return ex
    fall = [chandelier(dy=1.0, sway=-1, phase=0, eye="open", flame_size=1),
            chandelier(dy=2.0, sway=1, phase=1, eye="wide", flame_size=2, tilt=-1),
            chandelier(dy=-3.0, rise=1, phase=2, eye="wide", flame_size=3, legs=[(0, 0), (0, 0), (-1, 0), (1, 0)]),
            chandelier(dy=-1.0, rise=1, phase=3, eye="wide", candles_on=False, top_lit=False, extra=sparks_up(0)),
            chandelier(dy=0.0, phase=0, eye="open", candles_on=False, top_lit=False, extra=sparks_up(4)),
            chandelier(dy=0.0, phase=1, eye="open", candles_on=False, stubs=True, flame_size=0),
            chandelier(dy=0.0, phase=2, eye="open", flame_size=1)]
    death = [chand_corpse(0), chand_corpse(1), chand_corpse(2), chand_corpse(3)]
    knock = chandelier(dy=-1, tilt=-3, sway=-2, phase=2, eye="wide", flame_size=2, legs=[(-1, 1), (-1, 2), (-2, 2), (-1, 1)])
    anims = [("Idle", idle, [0.16] * 4), ("Run", run, [0.08] * 6),
             ("Whirl", whirl, [0.12, 0.14, 0.05, 0.05, 0.05, 0.05, 0.08, 0.14]),
             ("Candlefall", fall, [0.12, 0.16, 0.12, 0.08, 0.3, 0.14, 0.14])] + \
        std_tail(idle[0], death, [0.1, 0.12, 0.14, 0.3], knock)
    sheet("VhChandelier", anims, outdir, scale=5)


# ================================================================== ASHEN SERAPH (T3)
def moth_wing(fr, layer, root, length, angle, spread, ramp, rim, spots, seed, tatter=0.16):
    """A broad moth wing fanned from root toward angle (deg, -90 = up); ember eye-spots at fractions."""
    c = getattr(fr, layer)
    a = math.radians(angle)
    pts = [root,
           (root[0] + length * 0.75 * math.cos(a - spread * 1.2), root[1] + length * 0.75 * math.sin(a - spread * 1.2)),
           (root[0] + length * math.cos(a - spread * 0.45), root[1] + length * math.sin(a - spread * 0.45)),
           (root[0] + length * 1.05 * math.cos(a + spread * 0.2), root[1] + length * 1.05 * math.sin(a + spread * 0.2)),
           (root[0] + length * 0.7 * math.cos(a + spread), root[1] + length * 0.7 * math.sin(a + spread)),
           (root[0] + length * 0.3 * math.cos(a + spread * 1.3), root[1] + length * 0.3 * math.sin(a + spread * 1.3))]
    sub = Canvas()
    poly(sub, pts, "x")
    rnd = random.Random(seed)
    keys = list(sub.px.keys())
    for (x, y) in keys:
        edge = any((x + dx, y + dy) not in sub.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        d = math.hypot(x - root[0], y - root[1]) / max(1.0, length)
        if edge:
            if rnd.random() < tatter and d > 0.5: continue
            ch = rim
        else:
            # veins radiating from the root, lighter toward the leading edge
            ang = math.degrees(math.atan2(y - root[1], x - root[0])) - angle
            vein = abs(((ang + 360) % 22) - 11) < 1.6 and d > 0.25
            l = -0.5 + d * 0.9 - (ang / 90.0) * 0.4
            ch = ramp[0] if vein else pick(ramp, l)
        c.put(x, y, ch)
    for fpos, aoff, big in spots:
        sx, sy = P(root[0] + length * fpos * math.cos(a + aoff), root[1] + length * fpos * math.sin(a + aoff))
        if (sx, sy) not in sub.px: continue
        fr.g.put(sx, sy, "Y" if big else "O")
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (sx + dx, sy + dy) in sub.px: fr.g.put(sx + dx, sy + dy, "o" if big else "a")
        if big:
            for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                if (sx + dx, sy + dy) in sub.px: c.put(sx + dx, sy + dy, "k")


def lance(fr, hx, hy, ang, back=7.0, fwd=17.0, flare=1, phase=0, layer="b"):
    """The candle-lance: an iron-shod haft through the hand at (hx, hy), a wax blade that burns at the tip."""
    c = getattr(fr, layer)
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    x0, y0 = hx - back * ca, hy - back * sa
    x1, y1 = hx + fwd * ca, hy + fwd * sa
    pts = line_px(*P(x0, y0), *P(x1, y1))
    for k, (x, y) in enumerate(pts):
        c.put(x, y, "a" if k % 4 else "k")
    c.put(*P(x0, y0), "s")
    # crossguard of brass at the blade's foot
    nx, ny = -sa, ca
    gx, gy = x1, y1
    for s_ in (-1.5, -0.5, 0.5, 1.5):
        c.put(*P(gx + nx * s_, gy + ny * s_), "e" if s_ < 0 else "A")
    # wax blade: 2px wide, 5 long, tapering
    for k in range(1, 7):
        bx, by = gx + ca * k, gy + sa * k
        w = 1.0 if k < 5 else 0.0
        c.put(*P(bx - nx * 0.5 * w, by - ny * 0.5 * w), "X" if k < 4 else "W")
        if w: c.put(*P(bx + nx * 0.5, by + ny * 0.5), "W" if k < 4 else "w")
    tx, ty = gx + ca * 7, gy + sa * 7
    # flame at the tip, blown back along the haft
    lean = [0, 1, 0, -1][phase % 4]
    for k in range(2 + flare):
        fx, fy = tx + ca * k * 0.8 - nx * 0.3 * lean, ty + sa * k * 0.8 - ny * 0.3 * lean
        fr.g.put(*P(fx, fy), "y" if k == 0 else ("Y" if k < 2 else ("O" if k < 3 else "o")))
    if flare >= 2:
        fr.g.put(*P(tx + nx, ty + ny), "O"); fr.g.put(*P(tx - nx, ty - ny), "o")
    return P(tx, ty)


def seraph(dx=0.0, dy=0.0, lift=0.0, lean=0.0, wing=-120.0, wing_f=-95.0, spread=0.55, wlen=16.0, legs=((-2.5, 0), (2.5, 0)),
           lance_mode="up", lance_ang=-90.0, hand=None, arm_b=None, phase=0, visor="lit", crown=1, halo=0, halo_rot=0.0,
           flare=1, fade=0, extra=None, smear=0, wing_len=None):
    """Ashen Seraph. lift raises the whole body (hovering on the wings); lean tips the torso forward.
    lance_mode 'up' = held upright at its side; 'aim' = held at lance_ang through hand."""
    f = Fr()
    bx, by = dx, dy - lift
    hip = (bx, by - 11.0)
    sh = (bx + lean * 0.6, by - 19.0)
    # ---- wings: far pair (dark, no spots), near pair (ash with ember eye-spots); fore wing long, hind wing round ----
    root = (sh[0] - 2.0, sh[1] + 0.5)
    hind = wing - 52.0
    moth_wing(f, "u", (root[0] + 2, root[1]), wlen * 0.55, wing_f - 52.0, 0.5, "Kkg", "K", [], 10, tatter=0.1)
    moth_wing(f, "u", (root[0] + 2, root[1] - 1), wlen * 0.95, wing_f, spread * 0.6, "Kkgg", "K", [(0.7, 0.0, False)], 11)
    moth_wing(f, "u", (root[0], root[1] + 1), wlen * 0.62, hind, 0.55, "kgh", "k", [(0.6, 0.0, False)], 13, tatter=0.12)
    moth_wing(f, "u", root, wlen * 1.15, wing, spread * 0.62, ASH, "k", [(0.6, -0.05, True), (0.9, 0.12, False)], 12)
    # ---- legs: wax greaves, dark sabatons ----
    for i, (fx_, lft) in enumerate(legs):
        foot = (bx + fx_, by - lft)
        knee = (hip[0] + fx_ * 0.7 + 1.0, hip[1] + 6.0 - lft * 0.5)
        layer = f.u if i == 0 else f.b
        tube(layer, [(hip[0] + (-1.5 if i == 0 else 1.5), hip[1]), knee, (foot[0], foot[1] - 1)], [1.4, 1.2, 1.1], WAX_D if i == 0 else PLATE)
        layer.put(*P(foot[0], foot[1]), "k"); layer.put(*P(foot[0] + 1, foot[1]), "k"); layer.put(*P(foot[0] - 1, foot[1]), "K")
        layer.put(*P(knee[0] + 1, knee[1]), "a")
    # ---- tabard of ash cloth ----
    def tab(x, y):
        return "g" if (x + y) % 5 == 0 else ("h" if x < hip[0] else "g")
    poly(f.b, [(hip[0] - 4, hip[1] - 1), (hip[0] + 4 + lean * 0.3, hip[1] - 1), (hip[0] + 3 + lean * 0.2, hip[1] + 5),
               (hip[0] + 0.5, hip[1] + 4), (hip[0] - 3.5, hip[1] + 5)], "g", shade=tab)
    # ---- far arm ----
    if arm_b:
        tube(f.u, [(sh[0] - 2.5, sh[1] + 1), arm_b], [1.1, 0.9], WAX_D)
    # ---- torso: ash mail under a wax breastplate with a rust keel, rust belt, rust pauldron ----
    ell(f.b, sh[0] - 0.3, sh[1] + 4.0, 4.2, 5.0, ASH, ang=lean * 3)
    ell(f.b, sh[0] + 0.3, sh[1] + 3.0, 3.6, 3.6, PLATE, ang=lean * 3)
    for k in range(4):
        f.b.put(*P(sh[0] + 1.0 + lean * 0.1, sh[1] + 1.5 + k), "w" if k < 3 else "g")
    for x in range(int(round(hip[0] - 3)), int(round(hip[0] + 4 + lean * 0.3))):
        f.b.put(x, int(round(hip[1] - 1)), "k")
    f.b.put(*P(hip[0] + 1, hip[1] - 1), "o")
    for x0, n in ((-2, 2), (2, 3)):
        for k in range(n): f.b.put(*P(sh[0] + x0, sh[1] + 5 + k), "W" if k < n - 1 else "w")
    # ---- head: gorget, then a wax great-helm with a rust visor band, a burning slit and three wicks ----
    hx, hy = sh[0] + 1.0 + lean * 0.3, sh[1] - 4.5
    for x in range(int(round(hx - 2)), int(round(hx + 3))):
        f.b.put(x, int(round(hy + 3.5)), "k")
    ell(f.b, hx, hy, 2.9, 3.3, PLATE)
    for k in (-1, 0, 1, 2, 3):
        f.b.put(*P(hx + k, hy + 0.5), "g")
    if visor == "lit":
        for k in (1, 2): f.g.put(*P(hx + k, hy + 0.5), "Y")
        f.g.put(*P(hx + 3, hy + 0.5), "O")
    elif visor == "flare":
        for k in (0, 1, 2, 3): f.g.put(*P(hx + k, hy + 0.5), "y" if 1 <= k <= 2 else "Y")
        f.g.put(*P(hx + 4, hy + 0.5), "O")
    else:
        for k in (1, 2, 3): f.b.put(*P(hx + k, hy + 0.5), "K")
    ell(f.b, sh[0] + 2.8, sh[1] + 0.8, 2.3, 1.7, "kghW")
    # v0.10 lineage (one parent, the Moth Matron): her feathered antennae sweep back from the helm (the rust trim the
    # Waxen Knight lent it in v0.9 is ash now)
    for k, (a0, a1) in enumerate(((-150, -185), (-125, -165))):
        q = chain(hx - 2.0 + k * 1.0, hy - 2.0, [(4.0, a0), (4.0, a1)])
        line(f.b, q[0][0], q[0][1], q[1][0], q[1][1], "w")
        line(f.b, q[1][0], q[1][1], q[2][0], q[2][1], "W")
        f.b.put(*P(q[1][0] - 1, q[1][1]), "h")
    for k, cxo in enumerate((-2, 0, 2)):
        x, y = P(hx + cxo, hy - 3.5 + abs(cxo) * 0.5)
        f.b.put(x, y, "W"); f.b.put(x, y - 1, "X")
        if crown:
            flame(f.g, x, y - 1, size=crown if k == 1 else max(0, crown - 1), phase=phase + k)
        else:
            f.g.put(x, y - 2, "s")
    # ---- near arm + lance ----
    if lance_mode == "up":
        hand_ = hand or (sh[0] + 6.0, sh[1] + 6.0)
        tube(f.b, [(sh[0] + 2.5, sh[1] + 1.5), (sh[0] + 4.5, sh[1] + 5.0), hand_], [1.2, 1.1, 1.0], PLATE)
        tip = lance(f, hand_[0] + 1, hand_[1], -90.0 + lean, back=6.0, fwd=13.0, flare=flare, phase=phase)
    else:
        hand_ = hand or (sh[0] + 6.0, sh[1] + 4.0)
        el = ((sh[0] + 2.5 + hand_[0]) / 2.0 - 0.5, (sh[1] + 1.5 + hand_[1]) / 2.0 + 1.5)
        tube(f.b, [(sh[0] + 2.5, sh[1] + 1.5), el, hand_], [1.2, 1.1, 1.0], PLATE)
        tip = lance(f, hand_[0], hand_[1], lance_ang, back=8.0, fwd=13.0, flare=flare, phase=phase)
    f.b.put(*P(hand_[0], hand_[1]), "w")
    # ---- motion smear behind a lunge ----
    if smear:
        for k in range(smear):
            yy = int(round(sh[1] + 2 + k * 3))
            for x in range(int(round(bx - 10 - k * 2)), int(round(bx - 5))):
                if (x + k) % 3: f.n.put(x, yy, "g" if x % 2 else "h")
    # ---- halo: cinder moths wheeling round it ----
    if halo:
        for k in range(5):
            a = math.radians(halo_rot + k * 72)
            mx, my = P(bx + 15 * math.cos(a), by - 14 + 7 * math.sin(a))
            if halo == 1 and k % 2: continue
            for ddx, ddy, ch in ((-1, -1, "o"), (1, -1, "o"), (0, 0, "Y"), (-1, 0, "O"), (1, 0, "O"), (0, 1, "a")):
                f.g.put(mx + ddx, my + ddy, ch)
    if extra: extra(f)
    out = f.done()
    if fade:
        out = Spr({k: v for k, v in out.px.items() if (k[0] * 3 + k[1] * 5) % (fade + 1) == 0 or v in GLOW})
    return out


def crumble(spr, seed=5, cx=0.0, cy=-14.0, cell=3, push=1.6, drop=2.0, burst=7.0):
    """v0.10 drawn break-up (replaces the checkerboard dissolve): the figure splits along cracks into chunky shards
    that are pushed out from (cx, cy) and sag, with an ember burst at the core and ash puffs at the cracks."""
    rnd = random.Random(seed)
    px = {}
    offs = {}
    for (x, y), v in spr.px.items():
        key = (int(math.floor(x / cell)), int(math.floor(y / cell)))
        if key not in offs:
            ccx, ccy = key[0] * cell + cell / 2.0 - cx, key[1] * cell + cell / 2.0 - cy
            d = max(1.0, math.hypot(ccx, ccy))
            k = push * rnd.uniform(0.5, 1.2)
            offs[key] = (int(round(ccx / d * k)), int(round(ccy / d * k + drop * rnd.uniform(0.4, 1.0))))
        ox, oy = offs[key]
        if v == "K" and rnd.random() < 0.25: continue                     # inner outline breaks where it cracked
        q = (x + ox, min(0, y + oy))
        if q not in px or v not in "K": px[q] = v
    for k in range(14):                                                    # ember burst out of the core
        a = 2 * math.pi * k / 14 + rnd.uniform(-0.2, 0.2)
        r = burst * rnd.uniform(0.6, 1.0)
        px[P(cx + r * math.cos(a), cy + r * 0.8 * math.sin(a))] = "Y" if k % 3 == 0 else "O"
        if k % 2 == 0: px[P(cx + r * 0.6 * math.cos(a), cy + r * 0.5 * math.sin(a))] = "y"
    px[P(cx, cy)] = "y"; px[P(cx + 1, cy)] = "Y"; px[P(cx, cy - 1)] = "Y"
    for k in range(6):                                                     # ash puffs at the cracks
        x, y = cx + rnd.uniform(-8, 8), cy + rnd.uniform(-8, 6)
        for (ddx, ddy, ch) in ((0, 0, "S"), (1, 0, "s"), (0, -1, "U")):
            q = P(x + ddx, y + ddy)
            if q[1] <= 0: px.setdefault(q, ch)
    return Spr(px)


def seraph_corpse(stage):
    f = Fr()
    # crumpled wings like dead leaves, the helm rolled off, the lance across them
    moth_wing(f, "u", (-3, -2), 13 - stage, -170, 0.5, ASH_D, "K", [(0.55, 0.0, False)], 21, tatter=0.3)
    moth_wing(f, "u", (2, -2), 12 - stage, -10, 0.5, ASH, "k", [], 22, tatter=0.3)
    ell(f.b, 0, -3, 6, 2.6, PLATE)
    ell(f.b, 9, -2.5, 2.6, 2.4, PLATE)
    for x in range(-12, 13):
        if x % 5: f.b.put(x, -1, "a")
    f.b.put(13, -1, "W"); f.b.put(14, -1, "X")
    if stage == 0:
        f.g.put(10, -3, "O"); f.g.put(15, -2, "O"); f.g.put(15, -3, "o")
    else:
        f.g.put(10, -3, "K"); f.g.put(15, -2, "s")
    f.g.put(9, -6 - stage, "s"); f.g.put(10, -7 - stage, "S")
    return f.done()


def build_seraph(outdir):
    # v0.8: frames 1 and 3 drew the same wingbeat: f3 is now on the way down
    idle = [seraph(wing=-122 + [0, -4, -7, -2][i], wing_f=-96 + [0, -3, -5, -1][i], dy=[0, 0, -0.6, -0.3][i], phase=i)
            for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(seraph(lift=1.5 + math.sin(t) * 1.0, lean=2.0, wing=-150 + math.sin(t) * 22, wing_f=-125 + math.sin(t) * 18,
                          legs=((-3 + math.cos(t) * 2, max(0, math.sin(t)) * 2), (3 - math.cos(t) * 2, max(0, -math.sin(t)) * 2)),
                          lance_mode="aim", lance_ang=-60, hand=(6, -14), phase=i))
    # Lance: rear back, wings cocked; drive forward on a wingbeat; hold the thrust; recover
    lance_f = [seraph(lean=-1.5, wing=-105, wing_f=-85, lance_mode="aim", lance_ang=-25, hand=(1, -14), phase=0, arm_b=(-6, -15)),
               seraph(lean=-2.5, dx=-1, wing=-95, wing_f=-75, spread=0.6, lance_mode="aim", lance_ang=-8, hand=(-2, -14), phase=1,
                      visor="flare", arm_b=(-7, -14), flare=2),
               seraph(lean=3.0, dx=3, lift=1.0, wing=-165, wing_f=-150, spread=0.45, lance_mode="aim", lance_ang=0, hand=(13, -14),
                      phase=2, visor="flare", smear=3, legs=((-5, 1), (1, 2)), arm_b=(-5, -12), flare=3),
               seraph(lean=3.0, dx=3, lift=0.5, wing=-160, wing_f=-145, lance_mode="aim", lance_ang=0, hand=(14, -14), phase=3,
                      visor="flare", smear=2, legs=((-5, 0), (2, 0)), arm_b=(-5, -12), flare=3),
               seraph(lean=2.0, dx=2, wing=-140, wing_f=-120, lance_mode="aim", lance_ang=2, hand=(12, -13), phase=0,
                      legs=((-4, 0), (2, 0)), arm_b=(-5, -13), flare=2),
               seraph(lean=1.0, dx=1, wing=-130, wing_f=-105, lance_mode="aim", lance_ang=-40, hand=(7, -14), phase=1),
               seraph(wing=-122, wing_f=-96, phase=2)]
    # Halo: wings sweep up and wide, chest flares, the moths burst out and wheel round it
    halo_f = [seraph(wing=-110, wing_f=-90, lance_mode="aim", lance_ang=-80, hand=(6, -15), phase=0, arm_b=(-6, -16)),
              seraph(lift=1, wing=-80, wing_f=-65, spread=0.65, wlen=16, lance_mode="aim", lance_ang=-95, hand=(5, -20), phase=1,
                     visor="flare", crown=2, arm_b=(-6, -23)),
              seraph(lift=2, wing=-70, wing_f=-55, spread=0.7, wlen=16, lance_mode="aim", lance_ang=-95, hand=(5, -21), phase=2,
                     visor="flare", crown=3, halo=1, halo_rot=0, arm_b=(-6, -24)),
              seraph(lift=2, wing=-150, wing_f=-130, spread=0.5, lance_mode="aim", lance_ang=-95, hand=(5, -20), phase=3,
                     visor="flare", crown=2, halo=2, halo_rot=25, arm_b=(-7, -22)),
              seraph(lift=1, wing=-130, wing_f=-105, lance_mode="aim", lance_ang=-80, hand=(6, -16), phase=0, crown=2, halo=2,
                     halo_rot=50),
              seraph(wing=-122, wing_f=-96, phase=1)]
    death = [seraph(lean=-3, wing=-60, wing_f=-40, visor="flare", crown=1, lance_mode="aim", lance_ang=-130, hand=(2, -13)),
             crumble(seraph(lean=-4, dy=1, wing=-20, wing_f=-10, visor="dark", crown=0, lance_mode="aim", lance_ang=-160,
                            hand=(0, -12)), seed=7, cx=0.0, cy=-15.0),
             seraph_corpse(0), seraph_corpse(1)]
    knock = seraph(lean=-3, dx=-1, wing=-70, wing_f=-55, visor="flare", lance_mode="aim", lance_ang=-120, hand=(3, -14), phase=2)
    anims = [("Idle", idle, [0.18] * 4), ("Run", run, [0.08] * 6),
             ("Lance", lance_f, [0.14, 0.14, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Halo", halo_f, [0.12, 0.14, 0.1, 0.12, 0.14, 0.12])] + \
        std_tail(idle[0], death, [0.1, 0.12, 0.14, 0.3], knock)
    sheet("VhAshSeraph", anims, outdir, scale=5)



# ================================================================== LANTERN WRAITH (T3, v0.8 redraw)
ROBE = "msSU"        # dusk-grey grave cloth, lit from the top-left (brighter than the old black cloak)
ROBE_D = "Kmss"
SOULC = "bBc"


def wraith_lantern(fr, hx, hy, swing=0.0, glow=2, phase=0):
    """A wax-sealed iron lantern hanging from the hand at (hx, hy) on a short ring; swing tilts it (deg).
    glow: 0 dark, 1 dim, 2 lit, 3 flaring. Returns the lantern's centre (where orbs and the beam come out)."""
    a = math.radians(90 + swing)
    cx, cy = math.floor(hx + 4.0 * math.cos(a) + 0.5), math.floor(hy + 4.0 * math.sin(a) + 0.5)   # whole pixels: the cage stays even
    line(fr.b, hx, hy, hx + 1.6 * math.cos(a), hy + 1.6 * math.sin(a), "k")
    # cap, cage, base
    ell(fr.b, cx, cy - 2.6, 2.0, 0.9, "kAe")
    for yy in range(-2, 3):
        for xx in (-2, 2):
            fr.b.put(*P(cx + xx, cy + yy), "k" if yy % 2 else "A")
    for xx in (-1, 0, 1):
        fr.b.put(*P(cx + xx, cy + 3), "k")
    fr.b.put(*P(cx - 1, cy - 3.6), "W"); fr.b.put(*P(cx, cy - 3.6), "X")     # a stub of wax on the cap
    # glass
    if glow == 0:
        for yy in range(-1, 2):
            for xx in (-1, 0, 1): fr.g.put(*P(cx + xx, cy + yy), "m" if xx else "s")
    else:
        core = "c" if glow >= 2 else "B"
        for yy in range(-1, 3):
            for xx in (-1, 0, 1):
                fr.g.put(*P(cx + xx, cy + yy), core if (xx == 0 and yy in (0, 1)) else ("B" if glow >= 2 else "b"))
        if glow >= 2: fr.g.put(*P(cx, cy), "X")
        # the soul flame flickering inside
        fr.g.put(*P(cx + [0, 1, 0, -1][phase % 4] * 0.5, cy - 1), "c" if glow >= 2 else "B")
        if glow >= 2:      # halo of cold light on the floor of the air
            for k in range(10 if glow == 3 else 6):
                ang = 2 * math.pi * k / (10 if glow == 3 else 6) + phase * 0.5
                r = 4.5 if glow == 3 else 3.8
                fr.n.put(*P(cx + r * math.cos(ang), cy + 0.5 + r * math.sin(ang)), "b")
    return P(cx, cy)


def wraith(lift=3.0, lean=0.0, hem=0, hand=(9.0, -20.0), swing=0.0, glow=2, arm_b=(-6.0, -15.0), hood=(0.0, 0.0),
           eyes="lit", phase=0, trail=0.0, fade=0, mantle=True, extra=None, wing=-150.0, candles=1):
    """Lantern Wraith: a hovering grave-robe with a dripping wax mantle, a pale bone mask deep in its hood and a
    soul lantern held out in a bone hand. lift = hover height of the hem; lean tips it forward; trail streams the
    robe back (run / blink)."""
    f = Fr()
    hemy = -lift
    sh = (0.5 + lean * 0.5, -24.0 - lift * 0.3)
    # v0.9 lineage (Moth Matron parent): a ragged ash-moth wing-cape spread behind the shoulders, ember eye-spots on it
    moth_wing(f, "u", (sh[0] - 3.0, sh[1] + 2.5), 13.0, wing - 12.0, 0.5, ASH, "k", [(0.62, 0.0, True), (0.88, 0.1, False)],
              31 + hem % 2, tatter=0.2)
    moth_wing(f, "u", (sh[0] - 3.0, sh[1] + 5.0), 9.0, wing - 50.0, 0.45, ASH_D, "K", [(0.6, 0.0, False)], 33, tatter=0.2)
    # ---- robe: a long bell, tatters below the hem streaming back with `trail` ----
    top_l, top_r = sh[0] - 4.5, sh[0] + 4.5
    bot_l, bot_r = -8.0 - trail * 1.5, 7.0 - trail * 0.5
    pts = [(top_l, sh[1]), (top_r, sh[1]), (bot_r, hemy), (bot_l, hemy)]

    def shade(x, y):
        t = (y - sh[1]) / max(1.0, hemy - sh[1])
        xl, xr = top_l + (bot_l - top_l) * t, top_r + (bot_r - top_r) * t
        u = (x - xl) / max(1.0, xr - xl)          # 0 = back edge, 1 = front edge
        fold = (int(round(x - t * trail * 1.5 + lean * t)) % 4 == 0) and t > 0.2
        l = 0.95 - u * 1.15 - t * 0.3
        ch = pick(ROBE, l)
        if fold: ch = "s" if ch in "SU" else "m"
        return ch
    poly(f.b, pts, "s", shade=shade)
    # ragged hem: uneven strips, longer at the back, swaying with `hem`
    x = int(math.floor(bot_l)) + 1
    k = 0
    while x <= int(bot_r):
        u = (x - bot_l) / max(1.0, bot_r - bot_l)
        n = int(round(1 + (1 - u) * 2.5 + ((x * 5 + hem * 3) % 3) * 0.7))
        sway = math.sin(hem * 1.3 + x * 0.7) * 0.6 - trail * 0.6
        for d in range(n):
            xx = x + int(round(sway * d * 0.6))
            f.b.put(xx, int(hemy) + 1 + d, "S" if d == 0 else ("s" if d < n - 1 else "m"))
            if d < n - 2: f.b.put(xx + 1, int(hemy) + 1 + d, "s")
        x += 3 if k % 2 else 2
        k += 1
    # ---- far arm: a bony hand hanging (or reaching) ----
    tube(f.u, [(sh[0] - 3.0, sh[1] + 2.0), (arm_b[0] * 0.5 + sh[0] * 0.5 - 1, (arm_b[1] + sh[1]) * 0.5 + 2), arm_b], [1.5, 1.4, 1.2], ROBE_D)
    f.u.put(*P(arm_b[0], arm_b[1] + 1), "U"); f.u.put(*P(arm_b[0] - 1, arm_b[1] + 2), "u")
    # ---- wax mantle over the shoulders, dripping down the robe ----
    if mantle:
        ell(f.b, sh[0] - 0.5, sh[1] + 1.0, 6.0, 2.6, "hwWX", vmin=-0.4)
        for k, (dx, ln) in enumerate(((-5, 3), (-3, 5), (-1, 2), (1, 4), (3, 2), (5, 3))):
            ln2 = ln + ((k + hem) % 2 if trail == 0 else 0)
            for d in range(ln2):
                f.b.put(*P(sh[0] + dx, sh[1] + 3 + d), "W" if d < ln2 - 1 else "w")
    # ---- hood + mask ----
    hx, hy = sh[0] + 1.5 + lean * 0.4 + hood[0], sh[1] - 4.5 + hood[1]
    ell(f.b, hx - 0.5, hy, 4.6, 5.0, ROBE)
    ell(f.b, hx - 2.6, hy + 2.5, 2.6, 3.0, ROBE_D)                    # the cowl falling behind
    ell(f.b, hx + 1.2, hy + 0.6, 2.8, 3.4, "KKm")                     # the dark of the hood
    for (mx, my, ch) in ((1, -1, "U"), (2, -1, "u"), (3, -1, "u"), (1, 0, "u"), (3, 0, "U"), (1, 1, "U"), (2, 1, "u"),
                         (3, 1, "U"), (2, 2, "U"), (3, 2, "s")):
        f.b.put(*P(hx + mx, hy + my), ch)                              # pale bone mask, eye holes at (2, 0) and (4, 0)
    f.b.put(*P(hx + 2, hy + 0), "K"); f.b.put(*P(hx + 4, hy + 0), "K")
    if eyes == "lit":
        f.g.put(*P(hx + 2, hy + 0), "c"); f.g.put(*P(hx + 4, hy + 0), "B")
    elif eyes == "flare":
        f.g.put(*P(hx + 2, hy + 0), "X"); f.g.put(*P(hx + 4, hy + 0), "c"); f.g.put(*P(hx + 3, hy - 2), "B"); f.g.put(*P(hx + 5, hy - 1), "b")
    f.b.put(*P(hx - 2.0, hy - 4.5), "S"); f.b.put(*P(hx - 1.0, hy - 5.0), "U")   # the hood's lit crown
    # the Moth Matron's feathered antennae rising out of the hood
    for k, (a0, a1) in enumerate(((-120, -165), (-75, -30))):
        x0, y0 = hx - 0.5 + k * 1.5, hy - 4.5
        pts = chain(x0, y0, [(3.0, a0), (2.5, a1)])
        line(f.b, pts[0][0], pts[0][1], pts[1][0], pts[1][1], "w")
        line(f.b, pts[1][0], pts[1][1], pts[2][0], pts[2][1], "W")
    # v0.10 lineage (one parent, the Moth Matron): the Candelabra's tear and mantle candles are gone; her ember
    # eye-spots burn on the wing-cape instead
    if mantle and candles and False:
        for k, (dx_, h) in enumerate(((-5.0, 3), (-2.0, 2))):
            candle(f, sh[0] + dx_, sh[1] - 0.5, h, phase=phase + k, size=1 if candles else 0, lit=(eyes != "dark"))
    # ---- near arm: sleeve to a bone hand holding the lantern ----
    el = ((sh[0] + 3.0 + hand[0]) / 2.0, (sh[1] + 2.0 + hand[1]) / 2.0 + 1.5)
    tube(f.b, [(sh[0] + 3.0, sh[1] + 2.0), el, (hand[0] - 0.8, hand[1] + 0.5)], [1.7, 1.5, 1.3], ROBE)
    f.b.put(*P(hand[0], hand[1]), "u"); f.b.put(*P(hand[0] + 1, hand[1]), "U"); f.b.put(*P(hand[0], hand[1] + 1), "U")
    lc = wraith_lantern(f, hand[0] + 0.5, hand[1] + 1.0, swing=swing, glow=glow, phase=phase)
    if extra: extra(f, lc)
    out = f.done()
    if fade:
        # dissolve from the hem upward into soul smoke: the low rows go first, a scatter of pixels everywhere
        line_y = hemy + 2 - fade * 7.0
        px = {}
        for (x, y), v in out.px.items():
            r = random.Random(x * 131 + y * 17 + fade * 7).random()
            if v in "cBX" and fade < 4:
                px[(x, y)] = v; continue
            if y > line_y + r * 4:
                if r < 0.12: px[(x, y - fade)] = "b" if r < 0.06 else "B"
                continue
            if r < fade * 0.09: continue
            px[(x, y)] = v
        out = Spr(px)
    return out, lc


def wisps(pts, cols="cBb"):
    def ex(f, lc):
        for k, (x, y) in enumerate(pts):
            f.g.put(x, y, cols[k % len(cols)]); f.g.put(x, y - 1, cols[min(len(cols) - 1, k % len(cols) + 1)])
    return ex


def wraith_corpse(stage):
    """The robe empties and collapses into a heap of grave cloth under the guttering lantern."""
    f = Fr()
    h = [9, 6, 4][min(2, stage)]
    ell(f.b, -1, -h / 2.0, 9.0, h / 2.0 + 0.5, ROBE, vmin=-1.0)
    for k, dx in enumerate((-7, -4, -1, 2, 5)):
        f.b.put(dx, 0, "s"); f.b.put(dx + 1, 0, "m")
    ell(f.b, -4, -h + 0.5, 3.4, 1.4, "hwWX")                      # the wax mantle, slumped
    for k, dx in enumerate((-6, -3, 0)): f.b.put(dx, -h + 2 + k % 2, "W")
    ell(f.b, 4, -h + 1, 2.4, 2.0, ROBE_D)                          # the empty hood
    f.b.put(5, -h + 1, "K"); f.b.put(4, -h + 2, "u")
    # lantern on its side
    lx = 10
    for xx in range(-2, 3): f.b.put(lx + xx, -3, "k"); f.b.put(lx + xx, 0, "k")
    for yy in (-2, -1): f.b.put(lx - 2, yy, "A"); f.b.put(lx + 2, yy, "A")
    for xx in (-1, 0, 1):
        for yy in (-2, -1): f.g.put(lx + xx, yy, ("B" if stage == 0 else "b") if stage < 2 else "m")
    if stage < 2: f.g.put(lx, -2, "c" if stage == 0 else "B")
    else: f.g.put(lx, -4, "s"); f.g.put(lx + 1, -5, "S")
    return f.done()


def build_wraith(outdir):
    """Lantern Wraith (T3, Vhorrul): Idle 4, Run 6, Swing 6 (orb release on f2), BlinkOut 6 + BlinkIn 6 (blink on the
    seam, 0.18 s each like before), Beam 6 (looped x5 by the kit), Death 4, Dead, Statue, Knockback, Portrait."""
    idle, lcs = [], []
    for i in range(4):
        fr, lc = wraith(lift=[3, 2, 1, 2][i], hem=[0, 1, 2, 4][i], hand=(9.0, -20.0 + [0, 1, 2, 1][i]),
                        swing=[6, 0, -6, -12][i], phase=i, arm_b=(-6.0, -15.0 + [0, 1, 2, 1][i]))
        idle.append(fr); lcs.append(lc)
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        fr, _ = wraith(lift=3.5 + math.sin(t) * 1.0, lean=2.5, trail=2.0 + math.sin(t) * 0.8, hem=i * 2,
                       hand=(10.0, -19.5 + math.sin(t) * 0.8), swing=-18 + math.cos(t) * 8, phase=i, arm_b=(-8.0, -16.0))
        run.append(fr)
    # Swing: draw the lantern back, whirl it over and forward (release on f2), follow through, settle
    sw_spec = [((-2.0, -19.0), 40, 2, -1.0, (-7, -15), "lit"),
               ((-4.0, -25.0), 120, 3, -2.0, (-7, -16), "flare"),
               ((12.0, -22.0), -40, 3, 2.5, (-8, -17), "flare"),
               ((12.0, -19.0), -60, 1, 3.0, (-8, -17), "lit"),
               ((11.0, -19.0), -20, 1, 1.5, (-7, -16), "lit"),
               ((9.0, -20.0), 0, 2, 0.0, (-6, -15), "lit")]
    swing, sw_lc = [], []
    for k, (hand, swg, glow, lean, ab, ey) in enumerate(sw_spec):
        ex = wisps([(16, -22), (18, -23), (19, -21)]) if k == 2 else None
        fr, lc = wraith(lift=3, lean=lean, hand=hand, swing=swg, glow=glow, arm_b=ab, eyes=ey, phase=k, hem=k, extra=ex)
        swing.append(fr); sw_lc.append(lc)
    # Blink: the robe guts into soul-smoke from the hem up and is gone; then pours back in
    blink_out = []
    for k in range(6):
        smoke = wisps([(-3 + k, -6 - k * 3), (2 - k, -10 - k * 3), (0, -16 - k * 2), (5, -12 - k * 2)][: 2 + k // 2])
        fr, _ = wraith(lift=3 + k * 0.5, hem=k, eyes="flare" if k < 3 else "lit", glow=2 if k < 4 else 1, fade=k, extra=smoke,
                       trail=k * 0.3)
        blink_out.append(fr)
    blink_out[-1] = Spr({k: v for k, v in blink_out[-1].px.items() if v in "cBb" and k[1] < -12})   # only the light is left
    blink_in = []
    for k in range(6):
        j = 5 - k
        smoke = wisps([(4 - j, -8 - j * 2), (-3 + j, -12 - j * 2), (1, -18 - j)][: 1 + j // 2])
        fr, _ = wraith(lift=3 + j * 0.4, hem=k + 3, eyes="flare", glow=2, fade=j, extra=smoke, trail=-j * 0.2)
        blink_in.append(fr)
    # Beam: lantern raised and held out level, the light streaming (looped by the kit)
    beam, bm_lc = [], []
    for k in range(6):
        fr, lc = wraith(lift=3 + [0, 0.5, 1, 1, 0.5, 0][k], lean=-0.5, hand=(11.0, -23.0), swing=-90 + [0, 3, 6, 3, 0, -3][k], glow=3,
                        arm_b=(-7.0, -21.0 + k % 2), eyes="flare", phase=k, hem=k, hood=(0, -0.5))
        beam.append(fr); bm_lc.append(lc)
    death = []
    for k in range(2):
        fr, _ = wraith(lift=[2, 0][k], lean=-2 - k * 2, hand=(8.0 + k, -15.0 + k * 4), swing=40 + k * 30, glow=[1, 0][k],
                       arm_b=(-8.0, -12.0 + k * 3), eyes="dark", phase=k, hem=k, fade=k * 2)
        death.append(fr)
    death += [wraith_corpse(0), wraith_corpse(2)]
    knock, _ = wraith(lift=4, lean=-3.5, hand=(4.0, -25.0), swing=60, glow=2, arm_b=(-9.0, -22.0), eyes="flare", hem=3, trail=-1.5)
    anims = [("Idle", idle, [0.16] * 4), ("Run", run, [0.09] * 6),
             ("Swing", swing, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("BlinkOut", blink_out, [0.03] * 6), ("BlinkIn", blink_in, [0.03] * 6),
             ("Beam", beam, [0.08, 0.06, 0.06, 0.06, 0.05, 0.05])] + \
        std_tail(idle[0], death, [0.1, 0.12, 0.14, 0.3], knock)
    sheet("LanternWraith", anims, outdir, scale=5)
    print("  wraith lantern centre: idle %s  swing f2 %s  beam f0 %s" % (lcs[0], sw_lc[2], bm_lc[0]))


# ================================================================== EFFECTS
def candle_fall():
    """Origin = the impact point on the floor. A shadow gathers, the candle drops (flame streaming upward),
    smashes: wax splash + a burst of flame, then soot. Damage frames 4-5 (see TIMING.md)."""
    frames = []
    def shadow(f, rx):
        for x in range(-int(rx), int(rx) + 1):
            k = abs(x) / max(1.0, rx)
            f.n.put(x, -1, "K" if k < 0.7 else "m")
            if k < 0.5: f.n.put(x, -2, "m"); f.n.put(x, 0, "m")
    def falling(f, y, glow=1):
        # a tumbling candle: wax 2 x 6, wick down, flame dragged up behind it
        for k in range(6):
            f.b.put(-1 + (k // 4), y - k, "W" if k > 0 else "w")
            f.b.put(0 + (k // 4), y - k, "X" if k > 1 else "W")
        f.g.put(0, y + 1, "k")
        for k, ch in enumerate("YOOo"[:2 + glow]):
            f.g.put(0, y + 1 - 7 - k, ch, over=False)
            if k < 2: f.g.put(1, y - 7 - k, "o")
        f.g.put(-2, y - 3, "o")
    for i, (rx, cy) in enumerate(((2.5, None), (4.0, -34), (5.5, -22), (6.5, -10))):
        f = Fr()
        shadow(f, rx)
        if cy is not None: falling(f, cy, glow=2 if i > 1 else 1)
        if i == 0: f.g.put(0, -40, "o")
        frames.append(f.done(outline=True))
    # impact
    f = Fr()
    shadow(f, 7)
    for x, y, ch in ((-6, -1, "w"), (-4, -2, "W"), (-2, -1, "X"), (2, -1, "X"), (4, -2, "W"), (6, -1, "w"),
                     (-7, -3, "W"), (7, -4, "W"), (-3, -4, "w"), (3, -5, "w")):
        f.g.put(x, y, ch)
    for x in range(-3, 4):
        for k in range(5 - abs(x)):
            f.g.put(x, -1 - k, "y" if (abs(x) < 2 and k < 2) else ("Y" if k < 3 else "O"))
    frames.append(f.done())
    f = Fr()
    shadow(f, 7)
    for x, y, ch in ((-8, -2, "w"), (-6, -4, "W"), (8, -3, "w"), (6, -6, "W"), (-3, -8, "w"), (4, -9, "W")):
        f.g.put(x, y, ch)
    for x in range(-5, 6):
        h = 8 - abs(x) - (1 if x % 2 else 0)
        for k in range(max(1, h)):
            f.g.put(x, -1 - k, "Y" if k < h * 0.4 else ("O" if k < h * 0.8 else "o"))
    frames.append(f.done())
    f = Fr()
    for x in range(-6, 7):
        f.n.put(x, -1, "k" if x % 3 else "K")
    for x in (-4, -1, 2, 5):
        for k in range(3 - (x % 2)):
            f.g.put(x, -2 - k, "O" if k == 0 else "o")
    f.g.put(0, -6, "s"); f.g.put(1, -8, "S"); f.g.put(-2, -7, "s")
    frames.append(f.done(outline=False))
    return frames


def cinder_moth(n=4):
    """A small ember moth, centred 4 px above the origin (like the other Vhorrul projectiles)."""
    frames = []
    for i in range(n):
        f = Fr()
        up = [2, 1, -1, 1][i]
        # body
        f.b.put(0, -4, "a"); f.b.put(1, -4, "o"); f.b.put(-1, -4, "a")
        # wings: up-stroke / down-stroke
        for side in (-1, 1):
            for k in range(1, 4):
                y = -4 - up * k // 2
                f.g.put(side * k, y - 1, "O" if k < 3 else "o")
                if k < 3: f.g.put(side * k, y, "Y" if k == 1 else "O")
            f.b.put(side * 3, -4 - up * 3 // 2 - 2, "k")
        f.g.put(2, -5, "y")
        f.g.put(-3 - (i % 2), -3, "o")
        frames.append(f.done(outline=False))
    return frames


def build_fx(outdir):
    fx_sheet("FxCandleFall", [("Fall", candle_fall(), [0.18, 0.16, 0.06, 0.05, 0.06, 0.08, 0.12])], outdir)
    fx_sheet("FxCinderMoth", [("Fly", cinder_moth(), [0.06] * 4)], outdir)


# ================================================================== main
def build_all(outdir):
    build_chandelier(outdir)
    build_seraph(outdir)
    build_wraith(outdir)
    build_fx(outdir)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    build_all(out)
    # v0.10: the ten new tree monsters and their effects (vhorrul_v10.py) build in the same step
    import vhorrul_v10
    vhorrul_v10.build_all(out)
