"""v0.8 art pass: the effect sheets Sylvene, Umbrael and Jinx were borrowing from vanilla or from each other.

    python3 godsb_fx.py [--only FxA,FxB] [--god sylvene|umbrael]

Every effect here is drawn in full RGB (no shared palette letters, so nothing collides with the god rigs' PALETTE
additions) by small deterministic generators, packed with anim.pack and previewed. Each god rig imports this module
and calls build(god, outdir) and timing_section(god) so its own run regenerates these sheets and their TIMING rows.

Melee arcs replace the tinted vanilla OrcSwipe / OrcSwipe2 arcs (AtlasEffectsShared 39-42 / 63-66). They keep the
vanilla frame count and timing (4 frames, 0.117 x 3 + 0.067 = 0.42 s) and the same footprint around the effect origin:
  OrcSwipe  arc: centre (9, 0), about 21 x 21, crescent on the right opening left (swings top -> bottom)
  OrcSwipe2 arc: centre (6, 0), about 18 x 31, tall crescent (swings bottom -> top)
The C# side clones the same vanilla template (collider, attach and rotation kept) and draws the sheet with
Strike.ArtAt(go, sheet, ox, oy), where (ox, oy) is the origin pixel listed in TIMING.md.
"""
import math, os, random, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from anim import SprRGB, pack, preview  # noqa: E402

OUT = {"sylvene": os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_sylvene"), "umbrael": os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_umbrael"),
       "jinx": os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out_jinx")}
SWING = [0.117, 0.117, 0.117, 0.067]          # vanilla 1HandedSwordSwipe2 / Upslash timing


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def R(*hs):
    return [rgb(h) for h in hs]


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ------------------------------------------------------------------ material ramps (dark -> light)
OUTLINE = rgb("1e1a1c")
VINE = R("1f3319", "2f5a26", "4a8a3a", "74b84e", "b4e486")
THORN = R("7a6553", "b8a276", "dcc998", "f4eac6")
POISON = R("5b2f6e", "9a5cbf", "e58fb0")
LEAF = R("2f5a26", "5aa44a", "9fd46a")
BARK = R("2b221c", "4e3a2a", "6b5238", "8f7350", "b09670")
MOSS = R("3f7a3a", "5aa44a", "8fcf6a")
IVORY = R("5a4a42", "9a8468", "dcc998", "f4eac6", "fffbe8")
DIRT = R("3b2f2c", "5a4a42", "7a6553")
VIOL = R("2b1a36", "4a2a5e", "6e3c8c", "9a5cbf", "c6a0ec", "efe2ff")
GLASS = R("8a93a8", "c9d2e6", "e6f2ff", "ffffff")
ICE_B = R("3d6fb0", "8cc8ff", "d8f2ff")
ROSE = R("8a3070", "d064a8", "ffb0dc")
SMOKE = R("1c1424", "2e2038", "45304f", "5e4470")
CRIM = R("3e0e16", "6c141e", "962026", "be3a34", "e8665a")
GOLD = R("6a5a2e", "b49646", "e2cc84", "fff3b8")
CREAM = R("b8a276", "dcc998", "f4eac6", "fffbe8")
PURP = R("5b2f6e", "9a5cbf", "c48ae8", "ecd2ff")
WOODC = R("3b2a1e", "6b5238", "9a7a52", "c8a878")
FLAMEC = R("a8341a", "f28a26", "ffd85e", "fff3b8")
SPADE = R("2a0a10", "5a0e1a", "a81e2a", "ff4a3a")


def hsh(x, y, seed=0):
    h = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def pick(ramp, l):
    l = max(0.0, min(0.999, l))
    return ramp[int(l * len(ramp))]


class Px(dict):
    """(x, y) -> rgb; y down, origin = the effect's spawn point."""
    def put(self, x, y, c, over=True):
        k = (int(round(x)), int(round(y)))
        if over or k not in self:
            self[k] = c

    def line(self, x0, y0, x1, y1, c, over=True):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c, over)

    def disc(self, cx, cy, r, c, over=True):
        for y in range(int(math.floor(cy - r)), int(math.ceil(cy + r)) + 1):
            for x in range(int(math.floor(cx - r)), int(math.ceil(cx + r)) + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.3:
                    self.put(x, y, c, over)

    def outline(self, c=OUTLINE, skip=()):
        add = {}
        for (x, y), v in self.items():
            if v in skip: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in self: add[(x + dx, y + dy)] = c
        for k, v in add.items(): self.setdefault(k, v)
        return self

    def spr(self):
        return SprRGB(dict(self))


def merge(*ps):
    o = Px()
    for p in ps: o.update(p)
    return o


# ------------------------------------------------------------------ crescent field
def crescent(oc, R_, ic, r, rot=0.0, lead_up=False, clip=None, sy=1.0):
    """Pixels inside the outer disc (centre oc, radius R_) and outside the inner disc (centre ic, radius r), after
    rotating the whole shape by `rot` degrees about oc. Returns {(x, y): (depth, t)}: depth 0 = outer edge, 1 = inner
    edge; t 0 = trailing tip, 1 = leading tip (leading = bottom unless lead_up)."""
    a = math.radians(-rot)
    ca, sa = math.cos(a), math.sin(a)
    out = {}
    for y in range(int(oc[1] - R_ * sy - 2), int(oc[1] + R_ * sy + 3)):
        for x in range(int(oc[0] - R_ - 2), int(oc[0] + R_ + 3)):
            qx, qy = x - oc[0], (y - oc[1]) / sy
            ux, uy = qx * ca - qy * sa + oc[0], qx * sa + qy * ca + oc[1]
            do = R_ - math.hypot(ux - oc[0], uy - oc[1])
            di = math.hypot(ux - ic[0], uy - ic[1]) - r
            if do < 0 or di < 0: continue
            if clip and not clip(x, y): continue
            out[(x, y)] = [do / max(0.01, do + di), math.degrees(math.atan2(uy - oc[1], ux - oc[0])), do + di]
    if out:
        angs = [v[1] for v in out.values()]
        a0, a1 = min(angs), max(angs)
        for k, v in out.items():
            t = (v[1] - a0) / max(1e-3, a1 - a0)
            v[1] = 1 - t if lead_up else t
    return {k: tuple(v) for k, v in out.items()}


# The two vanilla footprints (effect origin = (0, 0), y down)
SW_OC = (8.0, 0.0)     # OrcSwipe arc: circle r 11 round (8, 0): x -3..19, y -11..11
UP_OC = (5.5, 0.0)     # OrcSwipe2 arc: circle r 10 round (5.5, 0) stretched x1.55 tall: x -4..15, y -15..15


def swipe_field(rot=0.0, thick=5.0, R_=11.0):
    return crescent(SW_OC, R_, (SW_OC[0] - thick, -1.0), R_ - 0.3, rot=rot)


def upslash_field(rot=0.0, thick=5.0, R_=10.0):
    return crescent(UP_OC, R_, (UP_OC[0] - thick, 1.0), R_ - 0.2, rot=rot, lead_up=True, sy=1.55)


def band(oc, Rr, th, rot=0.0, amax=70.0, sy=1.0, lead_up=False):
    """A concentric arc band (claw furrow / thread) of width th at radius Rr round oc, |angle| <= amax (deg)."""
    def clip(x, y):
        a = math.degrees(math.atan2((y - oc[1]) / sy, x - oc[0])) - rot
        return abs(a) <= amax
    return crescent(oc, Rr, oc, Rr - th, rot=0.0, lead_up=lead_up, clip=clip, sy=sy)


def arc_line(p, oc, Rr, a0, a1, colf, sy=1.0, width=1, keep=None, seed=0):
    """A continuous 1-2 px stroke along an arc from angle a0 to a1 (deg, y down); colf(t) gives the colour at t
    (0 = a0 end). keep(t, i) may drop pixels to break the stroke up."""
    n = int(abs(a1 - a0) / 180.0 * math.pi * Rr * max(1.0, sy) * 2.5) + 2
    seen = set()
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        for w in range(width):
            x = int(round(oc[0] + (Rr - w) * math.cos(a))); y = int(round(oc[1] + (Rr - w) * math.sin(a) * sy))
            if (x, y) in seen: continue
            seen.add((x, y))
            if keep is not None and not keep(t, hsh(x, y, seed)): continue
            c = colf(t) if w == 0 else colf(max(0.0, t - 0.3))
            if c is not None: p.put(x, y, c)
    return p


def thin(field, keep_depth, seed, gap=0.0, tmin=0.0, tmax=1.0):
    return {k: v for k, v in field.items()
            if v[0] <= keep_depth and tmin <= v[1] <= tmax and hsh(k[0], k[1], seed) >= gap}


def tip_pts(field, n=1, end=1.0):
    """Points along the outer edge nearest a given t."""
    edge = sorted(((abs(v[1] - end), k) for k, v in field.items() if v[0] < 0.25))
    return [k for _, k in edge[:n]]


def outer_normal(k, oc=(8.0, 0.0)):
    d = math.hypot(k[0] - oc[0], k[1] - oc[1]) or 1.0
    return (k[0] - oc[0]) / d, (k[1] - oc[1]) / d


# ================================================================== generic arc painter
def paint_arc(field, ramp, lead_hi=None, rim=None, bias=0.0):
    """Shade a crescent: outer rim dark-ish, body in the ramp, brightest band near the outer-middle and leading end."""
    p = Px()
    for k, (d, t, th) in field.items():
        l = 0.25 + 0.55 * (1 - abs(d - 0.35) * 1.6) + 0.35 * t - 0.15 + bias
        if d < 0.12 and rim is not None:
            p[k] = rim
            continue
        p[k] = pick(ramp, l)
        if lead_hi and t > 0.55 and 0.15 < d < 0.5:
            p[k] = lead_hi
    return p


def motes(p, pts, cols, seed):
    rnd = random.Random(seed)
    for (x, y) in pts:
        p.put(x, y, cols[rnd.randrange(len(cols))])
    return p


def scatter_along(field, n, seed, dmax=0.4, push=2.0, oc=(8.0, 0.0), tmin=0.0, tmax=1.0):
    rnd = random.Random(seed)
    cand = [k for k, v in field.items() if v[0] <= dmax and tmin <= v[1] <= tmax]
    cand.sort()
    out = []
    for _ in range(n):
        if not cand: break
        k = cand[rnd.randrange(len(cand))]
        nx, ny = outer_normal(k, oc)
        out.append((k[0] + nx * push * rnd.random(), k[1] + ny * push * rnd.random()))
    return out


# ================================================================== SYLVENE
def thorn_arc(kind, k):
    """Bramble Knight's thorn sweep: a lashing crescent of braided vine with bone thorns along its back."""
    F = swipe_field if kind == "Slash" else upslash_field
    oc = SW_OC if kind == "Slash" else UP_OC
    rot = [0, 14, 26, 34][k] * (1 if kind == "Slash" else -1)
    fld = F(rot=rot, thick=[5.5, 4.0, 2.5, 1.5][k])
    p = Px()
    if k <= 1:
        body = fld if k == 0 else thin(fld, 0.85, 7, gap=0.22, tmin=0.18)
        for key, (d, t, th) in body.items():
            # braided vine: two strands twisting along t
            braid = math.sin(t * 22 + d * 6)
            l = 0.35 + 0.35 * (1 - d) + 0.2 * braid + 0.25 * t - (0.2 if k else 0)
            p[key] = pick(VINE, l)
            if d < 0.14: p[key] = VINE[1] if t > 0.15 else VINE[0]
        # bone thorns on the outer edge, pointing outward along the swing
        rnd = random.Random(11 + k)
        edge = sorted(kk for kk, v in body.items() if v[0] < 0.12)
        for i, kk in enumerate(edge):
            if (kk[0] * 3 + kk[1] * 7) % 5: continue
            nx, ny = outer_normal(kk, oc)
            ln = 2 if rnd.random() < 0.6 else 3
            for s in range(1, ln + 1):
                p.put(kk[0] + nx * s, kk[1] + ny * s, THORN[min(3, s)] if s < ln else THORN[3])
        # a few poison blossoms caught in the vine
        for kk in tip_pts(body, 1, 0.55) + tip_pts(body, 1, 0.85):
            p.put(kk[0], kk[1], POISON[2]); p.put(kk[0] - 1, kk[1], POISON[1])
    if k >= 1:
        # leaves and torn thorns flung off the vine
        n = [0, 7, 9, 5][k]
        for (x, y) in scatter_along(fld, n, 30 + k, dmax=0.6, push=2 + 2 * k, oc=oc, tmin=0.2):
            x, y = x + k * 0.6, y + (k - 1) * 1.5
            p.put(x, y, LEAF[(int(x * 7 + y) % 3)])
            if (int(x) + int(y)) % 3 == 0: p.put(x + 1, y, LEAF[0])
        if k == 2:
            for kk, v in thin(fld, 0.18, 9, gap=0.5, tmin=0.5).items(): p[kk] = VINE[2]
    return p


def tusk_hook(k):
    """Briar Behemoth's gore: an ivory tusk hooking upward, ripping up sod and splinters."""
    fld = crescent((7.0, -1.0), 11.0, (2.5, 2.5), 10.4, rot=[-4, -14, -24, -30][k], lead_up=True, sy=1.3)
    p = Px()
    if k <= 1:
        body = fld if k == 0 else thin(fld, 0.75, 4, gap=0.25, tmin=0.25)
        for key, (d, t, th) in body.items():
            l = 0.3 + 0.5 * (1 - d) + 0.3 * t - (0.25 if k else 0)
            p[key] = pick(IVORY, l)
            if d < 0.1: p[key] = IVORY[1]
            # growth rings on the tusk
            if 0.2 < t < 0.9 and int(t * 30) % 5 == 0 and d > 0.3: p[key] = IVORY[1]
        # the hooked tip curls over at the leading end
        for kk in tip_pts(body, 2, 1.0):
            p.put(kk[0] - 1, kk[1] - 1, IVORY[4]); p.put(kk[0] - 2, kk[1] - 1, IVORY[3])
    # sod and splinters thrown up off the floor
    rnd = random.Random(5 + k)
    n = [6, 9, 8, 4][k]
    for i in range(n):
        x = rnd.uniform(2, 17) + k * 1.5
        y = 9 - rnd.uniform(0, 5 + 4 * k)
        c = DIRT[rnd.randrange(3)] if i % 3 else BARK[3]
        p.put(x, y, c)
        if i % 3 == 0 and k < 3: p.put(x + 1, y - 1, MOSS[1])
    return p


def bark_plate(k):
    """A spinning slab of bark armour with a moss cap and a thorn (orbit loop, centred on the origin)."""
    p = Px()
    w = [3.0, 2.0, 0.7, 2.0][k]          # half-width as it turns edge-on
    back = k == 3
    for y in range(-3, 4):
        hw = w * (1 - (abs(y) / 4.2) ** 2)
        for x in range(-3, 4):
            if abs(x) > hw + 0.25: continue
            l = 0.55 - 0.15 * y / 3 - 0.2 * x / max(1, w) - (0.3 if back else 0)
            c = pick(BARK[1:], l)
            if (x * 2 + y) % 4 == 0 and not back: c = BARK[1]      # furrows
            p[(x, y)] = c
    if k != 2:
        for x in range(-int(w), int(w) + 1):
            p[(x, -3)] = MOSS[1] if (x + k) % 2 else MOSS[2]
    if k == 2: p[(0, -3)] = MOSS[1]
    # a thorn on the face
    if k in (0, 1): p[(int(w) + 1, 0)] = THORN[2]; p[(int(w) + 2, 0)] = THORN[3]
    if k == 3: p[(-int(w) - 1, 0)] = THORN[1]
    p.outline()
    # a leaf trailing behind the spin
    lx = [-5, -4, 5, 4][k]; ly = [1, -2, -1, 2][k]
    p.put(lx, ly, LEAF[1]); p.put(lx + (1 if lx < 0 else -1), ly, LEAF[2])
    return p


def bark_splinter(k):
    """The bark plate cracks off the knight's chest (~11 px up) and splinters fall to the floor (origin = feet)."""
    p = Px()
    rnd = random.Random(3)
    pieces = [(rnd.uniform(-1, 1), rnd.uniform(-1.2, -0.2), rnd.choice((0, 1, 2))) for _ in range(9)]
    cy = -11
    if k == 0:
        for (x, y), c in bark_plate(0).items(): p[(x, y + cy)] = c
        for (x, y) in ((0, -1), (1, 0), (-1, 1), (0, 2)): p[(x, y + cy)] = IVORY[3]   # the crack of light
        p[(1, cy - 2)] = IVORY[4]
        return p
    for i, (vx, vy, kind) in enumerate(pieces):
        t = k / 3.0
        x = vx * (6 + 8 * t) + (i - 4) * 0.8
        y = cy + vy * 6 * t + 18 * t * t + i % 3
        y = min(0, y)
        col = BARK[2 + (i % 3)] if kind < 2 else MOSS[1]
        if k == 3 and i % 2: continue
        p.put(x, y, col)
        if kind == 0 and k < 3: p.put(x + 1, y, BARK[1])
        if kind == 1 and k < 3: p.put(x, y - 1, BARK[3])
    if k == 1:
        for (x, y) in ((0, cy), (-2, cy - 1), (2, cy + 1), (0, cy - 3), (3, cy - 2)): p.put(x, y, THORN[3])
    if k >= 2:
        for x in (-3, -1, 2, 4): p.put(x, 0, DIRT[1])
    return p


# ================================================================== UMBRAEL
def shadow_body(field, ramp=VIOL, hi=None, k=0):
    p = Px()
    for key, (d, t, th) in field.items():
        # dark core, bright moonlit outer edge: a cut in the dark that glows at its rim
        l = 0.85 - 1.0 * d + 0.25 * t - 0.12 * k
        c = pick(ramp, l)
        if d < 0.13: c = ramp[-1] if t > 0.35 else ramp[-2]
        p[key] = c
    if hi:
        for kk in tip_pts(field, 3, 1.0): p[kk] = hi
    return p


def imp_claw(k):
    """Shade Imp rake: three parallel claw furrows tearing a crescent of shadow (swings top -> bottom)."""
    p = Px()
    sweep = [0, 14, 24, 30][k]
    for j, Rr in enumerate((11.0, 11.0, 11.0)):
        a0, a1 = -60 + j * 4 + sweep, 56 - j * 6 + sweep
        if k == 1: a0 += 40
        if k == 2: a0 += 80
        if k == 3: continue
        keep = None if k == 0 else (lambda t, h, k=k: h > 0.15 * k)
        cols = VIOL[2:] if j else [VIOL[3], VIOL[4], VIOL[5], GLASS[3]]
        arc_line(p, (7.0 - 3.2 * j, 0.0), Rr, a0, a1, lambda t, cols=cols, k=k: pick(cols, 0.15 + 0.85 * t - 0.25 * k),
                 width=2 if (k == 0 and j == 0) else 1, keep=keep, seed=j + 3 * k)
    n = [3, 6, 7, 4][k]
    rnd = random.Random(40 + k)
    for i in range(n):
        x = 8 + rnd.uniform(0, 10) + k; y = rnd.uniform(-8, 9) + k * 1.5
        p.put(x, y, SMOKE[2 + (i % 2)] if k > 1 else VIOL[3])
    return p


def imp_strike(k):
    """Shade Imp's reappearing strike: one rending upward stroke that leaves a tear of darkness."""
    fld = upslash_field(rot=[0, -10, -18, -24][k], thick=[6.0, 4.5, 3.0, 2.0][k])
    p = Px()
    if k == 0:
        p = shadow_body(fld, hi=VIOL[5])
    elif k == 1:
        p = shadow_body(thin(fld, 0.9, 4, gap=0.15, tmin=0.1), k=1)
        for kk, v in fld.items():
            if v[0] > 0.55 and hsh(*kk, 9) > 0.4: p[kk] = SMOKE[0]          # the tear: pure dark inside
    elif k == 2:
        for kk, v in thin(fld, 0.3, 6, gap=0.45, tmin=0.4).items(): p[kk] = VIOL[3]
    rnd = random.Random(50 + k)
    for i in range([2, 5, 8, 5][k]):
        x = rnd.uniform(6, 15); y = rnd.uniform(-14, 12) - 2 * k
        p.put(x, y, SMOKE[1 + (i % 3)] if k else VIOL[4])
    return p


def twin_cut(k):
    """The Twinned's cut: two thin blades sweep together, a pale silver cut and its violet reflection."""
    p = Px()
    rot = [0, -12, -20, -26][k]
    pale = upslash_field(rot=rot, thick=2.0, R_=10.5)
    dark = crescent((UP_OC[0] - 3.0, 0.0), 8.5, (UP_OC[0] - 4.6, 1.0), 8.3, rot=rot - 6, lead_up=True, sy=1.55)
    for fld, ramp, sd in ((dark, VIOL[2:], 2), (pale, GLASS, 1)):
        if k == 1: fld = thin(fld, 0.8, sd, gap=0.2, tmin=0.2)
        if k == 2: fld = thin(fld, 0.5, sd + 4, gap=0.6, tmin=0.55)
        if k == 3: fld = {}
        for key, (d, t, _) in fld.items():
            p[key] = pick(ramp, 0.3 + 0.7 * t - 0.2 * k)
    if k <= 1:
        # glints where the two cuts meet the leading end
        for kk in tip_pts(pale, 1, 1.0):
            x, y = kk
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): p.put(x + dx, y + dy, GLASS[3])
    rnd = random.Random(60 + k)
    for i in range([0, 3, 5, 3][k]):
        p.put(rnd.uniform(2, 14), rnd.uniform(-14, 10) - k, GLASS[1] if i % 2 else VIOL[4])
    return p


def king_cleave(k):
    """The Hollow King's Eclipse Cleave: a huge black crescent moon with a pale corona burning along its back."""
    oc = (10.0, 0.0)
    rot = [-20, 0, 14, 24, 30][k]
    fld = crescent(oc, 18.0, (10.0 - [8, 8, 6, 4.5, 3.5][k], -1.0), 17.6, rot=rot, sy=1.12)
    p = Px()
    if k <= 2:
        body = fld if k <= 1 else thin(fld, 0.8, 12, gap=0.25, tmin=0.2)
        if k == 0: body = {kk: v for kk, v in body.items() if v[1] < 0.7}      # the cleave is still coming round
        for key, (d, t, th) in body.items():
            l = 0.15 + 0.45 * d + 0.15 * t
            c = pick(VIOL[:4], l)
            if d < 0.16: c = ICE_B[2] if t > 0.3 else ICE_B[1]           # corona edge
            elif d < 0.28: c = ICE_B[0] if (key[0] + key[1]) % 2 else VIOL[3]
            p[key] = c
        # star motes in the eclipse
        for (x, y) in scatter_along(body, 6, 70 + k, dmax=1.0, push=0, oc=oc):
            if (int(x), int(y)) in p and hsh(int(x), int(y), 3) > 0.3: p[(int(x), int(y))] = VIOL[5]
    if k >= 3:
        for kk, v in thin(fld, 0.2, 13 + k, gap=0.4 + 0.2 * (k - 3), tmin=0.4).items(): p[kk] = ICE_B[1] if k == 3 else VIOL[3]
    if k >= 1:
        rnd = random.Random(80 + k)
        for i in range([0, 6, 10, 12, 8][k]):
            x = rnd.uniform(10, 27) + k; y = rnd.uniform(-18, 18) - k
            p.put(x, y, ICE_B[2] if i % 3 == 0 else VIOL[4] if i % 3 == 1 else SMOKE[3])
    return p


def nail_rake(k):
    """Nailshade's pounce rake: five glass nails scoring bright parallel furrows upward (swings bottom -> top)."""
    p = Px()
    sweep = [0, -12, -20, -26][k]
    for j in range(5):
        if k == 3: break
        Rr = 10.0
        a0, a1 = 66 - j * 3 + sweep, -66 + j * 5 + sweep          # bottom -> top
        if k == 1: a0 -= 50
        if k == 2: a0 -= 95
        keep = None if k == 0 else (lambda t, h, k=k: h > 0.18 * k)
        oc = (UP_OC[0] - 2.2 * j, UP_OC[1])
        arc_line(p, oc, Rr, a0, a1, lambda t, j=j, k=k: (ROSE[1] if (j % 2 and 0.3 < t < 0.5) else pick(GLASS, 0.1 + 0.9 * t - 0.2 * k)),
                 sy=1.55, keep=keep, seed=j + 7 * k)
        if k == 0:
            a = math.radians(a1)
            p.put(oc[0] + Rr * math.cos(a), oc[1] + Rr * math.sin(a) * 1.55, ROSE[2])
    rnd = random.Random(90 + k)
    for i in range([0, 4, 6, 3][k]):
        x, y = rnd.uniform(4, 15), rnd.uniform(-14, 10) - k
        p.put(x, y, ROSE[2] if i % 2 else GLASS[2])
        if k < 3: p.put(x + 1, y + 1, GLASS[0])
    return p


def echo_smear(k):
    """Umbrael echo afterimage: a body-high smear of violet smoke that peels back off the monster in streaks
    (origin = feet)."""
    p = Px()
    hgt = 17
    for y in range(-hgt, 1):
        prof = math.sin(math.pi * (y + hgt) / (hgt + 1))           # widest at the waist
        w = 1.5 + 2.5 * prof
        if (y + k) % 3 == 0 and k: continue                       # scan-line streaks open up as it fades
        for x in range(-6, 7):
            n = hsh(x, y, 4 + k)
            if abs(x) > w: continue
            if n < 0.2 + 0.2 * k: continue
            l = 0.75 - 0.18 * k - 0.35 * n + (0.15 if x < 0 else 0)
            p.put(x - k * 2 - (1 if (y % 2 and k) else 0), y - k, pick(VIOL[1:6], l))
        for s_ in range(1 + k):                                   # trailing streak behind each row
            if hsh(y, s_, 9) < 0.5: p.put(-w - 1 - s_ - k * 2, y - k, VIOL[2] if s_ < 2 else SMOKE[3], over=False)
    return p


def ring_shard(i):
    """Mirror Witch ring shard: a curved sliver broken from a mirror's silver frame, violet glass inside (faces right)."""
    p = Px()
    ang = [0, 20, 0, -20][i]
    for s in range(-5, 6):
        a = math.radians(s * 9 + ang)
        x = 3 - 7 * (1 - math.cos(a)) * 0.6 + s * 0.0
        y = 6 * math.sin(a) * 0.6
        x = 3 - abs(s) * 0.55 + (2 if abs(s) < 2 else 0)
        y = s * 0.55
        p.put(x, y, GLASS[2] if abs(s) < 3 else GLASS[1])
        p.put(x - 1, y, VIOL[3] if abs(s) < 4 else VIOL[2])
    p.put(5, 0, GLASS[3]); p.put(4, 0, GLASS[3])
    gy = [-2, -1, 1, 2][i]                             # a glint slides along the sliver as it spins
    p.put(3 - abs(gy) * 0.55 + (2 if abs(gy) < 2 else 0), gy * 0.55 * 1.8, GLASS[3])
    for t in range(1, 4):                              # violet trail
        p.put(-t * 2, (t + i) % 2 - 0.5, VIOL[3 - min(2, t - 1)], over=False)
    if i % 2 == 0: p.put(5, -1 if i == 0 else 1, VIOL[5])
    return p


def pane_bolt(i):
    """Glass Seraph pane bolt: a leaded-glass splinter (blue / rose / gold panes) streaming prism light (faces right)."""
    p = Px()
    panes = [ICE_B[1], ROSE[1], GOLD[2], ICE_B[2]]
    for x in range(-2, 6):
        hw = 2 if x < 3 else 1 if x < 5 else 0
        for y in range(-hw, hw + 1):
            col = panes[((x + 2) // 2 + (y > 0) + i) % 4]
            if (x + 2) % 2 == 0 and x < 4: col = VIOL[0]           # lead came
            p[(x, y)] = col
    p[(6, 0)] = GLASS[3]; p[(5, 0)] = GLASS[3]
    for t in range(3, 11):                             # prism trail: three thin coloured streams
        if (t + i) % 3 == 0: continue
        p.put(-t, -1, ICE_B[1] if t < 7 else ICE_B[0], over=False)
        p.put(-t, 0, GLASS[2] if t < 6 else GLASS[1], over=False)
        p.put(-t, 1, ROSE[1] if t < 7 else ROSE[0], over=False)
    p.outline(VIOL[0], skip=())
    for x in range(-11, -2):
        for y in (-2, 2):
            p.pop((x, y), None)
    return p


def ink_pool(r, seed, k=0, fade=0.0):
    """Gloamcoil's ink: a flat pool of glossy black-violet ink on the floor (centre = origin)."""
    p = Px()
    for y in range(-6, 6):
        for x in range(-13, 14):
            d = (x / max(1, r)) ** 2 + (y / max(1, r * 0.42)) ** 2 + (hsh(x, y, seed) - 0.5) * 0.25
            if d > 1: continue
            if fade and hsh(x, y, seed + 9) < fade: continue
            c = SMOKE[1] if d > 0.75 else SMOKE[0]
            if d < 0.55 and y < 0 and x < 0: c = SMOKE[2]
            p[(x, y)] = c
    # oily sheen and ripples
    for (x, y), c in list(p.items()):
        if y == -1 and -r * 0.5 < x < r * 0.1 and (x + k) % 3 == 0: p[(x, y)] = VIOL[3]
        if y == 0 and (x - k) % 5 == 0 and abs(x) < r * 0.6: p[(x, y)] = VIOL[2]
    if not fade:
        bx = [-4, 3, -1, 5][k % 4]
        if (bx, -1) in p: p[(bx, -1)] = VIOL[4]; p.put(bx, -2, VIOL[2])
    return p


def gloam_pool_frames():
    fr = [ink_pool(r, 3) for r in (4, 8, 11)]
    idle = [ink_pool(12, 3, k) for k in (0, 1)]
    fr += [idle[i % 2] for i in range(22)]
    fr += [ink_pool(12, 3, 2, fade=f) for f in (0.3, 0.55, 0.8)]
    return fr


def shroud(k, rise=1.0, fade=0.0):
    """Lights Out shroud: a cowl of darkness winding round a monster's feet, smoke rising past it (origin = feet)."""
    p = Px()
    for t in range(0, 360, 6):
        a = math.radians(t + k * 25)
        for rr in (8.5, 9.5):
            x, y = rr * math.cos(a), rr * 0.4 * math.sin(a)
            if fade and hsh(int(x), int(y), t) < fade: continue
            p.put(x, y, SMOKE[0] if math.sin(a) > 0 else SMOKE[1])
    # smoke ribbons rising, behind and around (never a solid block over the body)
    for j, x0 in enumerate((-8, -4, 5, 9)):
        hgt = int((6 + (j * 5 + k * 3) % 8) * rise)
        for s in range(hgt):
            x = x0 + math.sin((s + k * 2 + j) * 0.7) * 1.2
            y = -s - 1
            if fade and hsh(int(x), y, j) < fade: continue
            p.put(x, y, SMOKE[2] if s < hgt - 2 else SMOKE[3], over=False)
    # the shut eye sigil on the floor in front
    if not fade:
        for x in range(-2, 3): p.put(x, 3, VIOL[3] if abs(x) < 2 else VIOL[2])
        p.put(0, 4, VIOL[4] if k % 2 else VIOL[3])
    return p


def shroud_frames():
    fr = [shroud(0, 0.3), shroud(1, 0.6), shroud(2, 0.9)]
    idle = [shroud(k) for k in (0, 1)]
    fr += [idle[i % 2] for i in range(22)]
    fr += [shroud(3, 0.8, fade=f) for f in (0.3, 0.55, 0.8)]
    return fr


# ================================================================== sheet table
# name: (god, [(anim, frames_fn, n, durations)], cell (w, h), origin (ox, oy), note)
def _arc_rows(fn):
    return [(None, fn, 4, SWING)]


SHEETS = {
    # ---- Sylvene
    "FxSylThornSweep": ("sylvene", [("Slash", lambda k: thorn_arc("Slash", k), 4, SWING),
                                    ("Upslash", lambda k: thorn_arc("Upslash", k), 4, SWING)], (36, 42), (9, 21),
                        "Bramble Knight Thorn Sweep: Slash = OrcSwipe footprint, Upslash = OrcSwipe2 footprint. Damage frame 0."),
    "FxSylTuskHook": ("sylvene", [("Play", tusk_hook, 4, SWING)], (36, 34), (9, 19),
                      "Briar Behemoth Gore (OrcSwipe clone): ivory tusk hooking up from (0, 9) to (12, -14). Damage frame 0."),
    "FxSylBarkPlate": ("sylvene", [("Orbit", bark_plate, 4, [0.1] * 4)], (18, 14), (9, 7),
                       "Bramble Knight bark plate, loops while a plate is up; origin = plate centre (code lifts it 11 px)."),
    "FxSylBarkSplinter": ("sylvene", [("Break", bark_splinter, 4, [0.06, 0.08, 0.1, 0.12])], (29, 24), (15, 21),
                          "Bark plate breaking, origin = the knight's feet; plate at (0, -11) on frame 0."),
    # ---- Umbrael
    "FxUmbImpClaw": ("umbrael", [("Play", imp_claw, 4, SWING)], (36, 28), (9, 14),
                     "Shade Imp Rake (OrcSwipe clone): three claw furrows to x 18. Damage frame 0."),
    "FxUmbImpStrike": ("umbrael", [("Play", imp_strike, 4, SWING)], (32, 40), (9, 20),
                       "Shade Imp Shadowstep strike (OrcSwipe2 clone): one upward rend. Damage frame 0."),
    "FxUmbTwinCut": ("umbrael", [("Play", twin_cut, 4, SWING)], (32, 40), (9, 20),
                     "Twinned Twin Cut / Exchange cut (OrcSwipe2 clone): a silver cut and its violet reflection."),
    "FxUmbKingCleave": ("umbrael", [("Play", king_cleave, 5, [0.06, 0.1, 0.1, 0.1, 0.07])], (50, 48), (15, 24),
                        "Hollow King Eclipse Cleave (OrcSwipe2 clone, no transform scale): eclipse crescent x -8..26, "
                        "y -20..20. Damage on frame 1 (the full crescent)."),
    "FxUmbNailRake": ("umbrael", [("Play", nail_rake, 4, SWING)], (32, 40), (9, 20),
                      "Nailshade pounce rake (OrcSwipe2 clone): five glass-nail furrows."),
    "FxUmbEchoSmear": ("umbrael", [("Play", echo_smear, 4, [0.08, 0.1, 0.12, 0.15])], (28, 28), (15, 24),
                       "Twice Struck afterimage smear, origin = the monster's feet (spawned with each echo)."),
    "FxUmbRingShard": ("umbrael", [("Fly", ring_shard, 4, [0.06] * 4)], (20, 12), (10, 6),
                       "Mirror Witch Shatter ring shard and the Glimmer decoys' shard (faces right, centre = origin)."),
    "FxUmbPaneBolt": ("umbrael", [("Fly", pane_bolt, 4, [0.06] * 4)], (24, 11), (13, 5),
                      "Glass Seraph mirror-pane bolt (faces right, centre = origin)."),
    "FxUmbGloamPool": ("umbrael", [("Life", lambda k: gloam_pool_frames()[k], 28,
                                    [0.08] * 3 + [0.2] * 22 + [0.12] * 3)], (32, 16), (16, 8),
                       "Gloamcoil ink pool on the floor, centre = origin. Same 28-frame Life layout as FxDarkness "
                       "(spread 0-2, idle pair 3-24, fade 25-27) so DarkDurations() re-times it."),
    "FxUmbShroud": ("umbrael", [("Life", lambda k: shroud_frames()[k], 28,
                                 [0.08] * 3 + [0.2] * 22 + [0.12] * 3)], (28, 26), (14, 19),
                    "Unblinking Lights Out shroud, origin = the shrouded monster's feet; same Life layout as FxDarkness."),
    # (the Jinx sheets that used to be here are drawn by jinx_v2_fx.py)
}

BUILT = {}


def build_one(name, outdir, scale=8):
    god, rows, (cw, ch), (ox, oy), note = SHEETS[name]
    anims = []
    for an, fn, n, durs in rows:
        frames = [Px(fn(k)).spr() for k in range(n)]
        assert len(durs) == n, name
        anims.append((an, frames, durs))
    # Cells and origins in SHEETS are frozen: the C# packs hard-code the origin (Strike.ArtAt). If a redraw no
    # longer fits, the cell grows here (1 px margin) and the new origin is printed: update the pack to match.
    allp = [k for a in anims for f in a[1] for k in f.px]
    x0 = min(min(p[0] for p in allp) - 1, -ox); x1 = max(max(p[0] for p in allp) + 1, cw - 1 - ox)
    y0 = min(min(p[1] for p in allp) - 1, -oy); y1 = max(max(p[1] for p in allp) + 1, ch - 1 - oy)
    if (-x0, -y0, x1 - x0 + 1, y1 - y0 + 1) != (ox, oy, cw, ch):
        print("NOTE %s: cell/origin changed to %dx%d (%d, %d): update the C# Strike.ArtAt call" % (name, x1 - x0 + 1, y1 - y0 + 1, -x0, -y0))
    ox, oy, cw, ch = -x0, -y0, x1 - x0 + 1, y1 - y0 + 1
    SHEETS[name] = (god, rows, (cw, ch), (ox, oy), note)
    img, man = pack(name, anims, cw, ch, (ox, oy), outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = (cw, ch, ox, oy, [(a, len(f), list(d)) for a, f, d in anims], note)
    print("built %-20s cell %dx%d origin (%d, %d)  %s" % (name, cw, ch, ox, oy,
                                                       ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return img, man


def build(god=None, outdir=None, only=None):
    for name, spec in SHEETS.items():
        if god and spec[0] != god: continue
        if only and name not in only: continue
        build_one(name, outdir or OUT[spec[0]])


def timing_section(god):
    """Markdown rows for the god's TIMING.md (cells, origins, anims, sync notes)."""
    L = ["", "## v0.8 effect sheets (tools/sprites/godsb_fx.py)", "",
         "Origin = the pixel that sits on the effect's spawn point (C#: `Strike.ArtAt(go, sheet, ox, oy)`; y down). "
         "Melee arcs keep the vanilla swipe timing (0.117 x 3 + 0.067 s) and its footprint.", "",
         "| Sheet | Cell (w x h) | Origin | Anims (frames, total s) | Notes |", "|---|---|---|---|---|"]
    for name, spec in SHEETS.items():
        if spec[0] != god: continue
        god_, rows, (cw, ch), (ox, oy), note = spec
        an = ", ".join("%s %d, %.2f s" % (a, n, sum(d)) for a, _, n, d in rows)
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (name, cw, ch, ox, oy, an, note))
    return L


if __name__ == "__main__":
    args = sys.argv[1:]
    only = god = None
    if "--only" in args:
        i = args.index("--only"); only = set(args[i + 1].split(",")); del args[i:i + 2]
    if "--god" in args:
        i = args.index("--god"); god = args[i + 1]; del args[i:i + 2]
    build(god, args[0] if args else None, only)
