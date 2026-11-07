"""CORE-FX common effects: the mod's status overlays and the per-god impact puffs.

    python3 common_fx.py [outdir]          (default art/out_common)

Sheets
  FxCommonStatusSlow   Loop 6 / LoopBig 6            sludge pooled round the feet, drips falling into it, bubbles popping
  FxCommonStatusRoot   Grip 3 + Loop 4 (and ...Big)  bark tendrils burst from the floor and lash round the ankles
  FxCommonStatusDaze   Loop 4 / LoopBig 4            two violet birds and two gold stars circling over the head
  FxCommonImpact<God>  Wall 5 + Hit 5                a god's projectile puff on a wall / on a body
                       God = Vh Bel Oss Syl Umb Jinx Zhk Krn Ysv, plus Mod (neutral fallback) and Wpn (hero weapons)
  FxCommonInd*         effect indicators (ModInd): Rime / Charge / Plates counters, Might, Regen, Heal, Haste, Ice
                       (python3 common_fx.py --ind rebuilds only these)

Method: every frame is drawn fresh from a deterministic particle set (seeded per god) with shaded primitives lit from
the top-left; bright cores are laid last so they stay on top. Impact cells are 24x24 with the impact point at the cell
centre (the C# side anchors them MidCenter); overlay cells put their anchor on the cell's bottom-centre (feet overlays
draw the feet line two rows above the bottom, so their code offset is -2).
Timings follow vanilla: ContactGenericSmall (5 frames, 0.05 0.05 0.083 0.083 0.083) for Wall, a slightly longer
5-frame flash for Hit (ArcadeyHitEffect2halfsize runs 4 x 0.1 s).
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from anim import Spr, pack, preview  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else \
    os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_common")
# Core's own sheets (status overlays, generic indicators, the neutral impact puff) live in art/core unless an outdir is given
CORE_OUT = OUT if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else \
    os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "core")

WALL_D = [0.05, 0.05, 0.083, 0.083, 0.083]
HIT_D = [0.05, 0.06, 0.07, 0.08, 0.09]


def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


class SprA(Spr):
    """Sparse RGB(A) sprite: (x, y) -> (r, g, b) or (r, g, b, a). Origin = anchor point."""

    def to_rgba(self):
        return {k: (c if len(c) == 4 else c + (255,)) for k, c in self.px.items()}


class C:
    """A tiny raster: put / line / disc / ring / blob with clipping to a box."""

    def __init__(self, box=(-12, -12, 11, 11)):
        self.px = {}
        self.box = box

    def put(self, x, y, col, over=True):
        x, y = int(round(x)), int(round(y))
        b = self.box
        if not (b[0] <= x <= b[2] and b[1] <= y <= b[3]):
            return
        if col is None:
            self.px.pop((x, y), None); return
        if over or (x, y) not in self.px:
            self.px[(x, y)] = col

    def line(self, x0, y0, x1, y1, col, over=True):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.put(x0, y0, col, over)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

    def blob(self, cx, cy, rx, ry, ramp, over=True, light=(-0.6, -0.8)):
        """Shaded ellipse lit from the top-left: ramp dark -> light."""
        n = len(ramp)
        for y in range(int(math.floor(cy - ry)) - 1, int(math.ceil(cy + ry)) + 2):
            for x in range(int(math.floor(cx - rx)) - 1, int(math.ceil(cx + rx)) + 2):
                u, v = (x - cx) / max(rx, 0.01), (y - cy) / max(ry, 0.01)
                d = u * u + v * v
                if d <= 1.0:
                    l = 0.55 - 0.55 * (u * light[0] + v * light[1]) * -1 - 0.35 * d
                    l = 0.5 + (-(u * light[0] + v * light[1])) * 0.5 - d * 0.25
                    i = max(0, min(n - 1, int(l * n)))
                    self.put(x, y, ramp[i], over)

    def disc(self, cx, cy, r, col, over=True):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.3:
                    self.put(x, y, col, over)

    def ring(self, cx, cy, r, col, gaps=0, seed=0, ry=None, over=True):
        ry = r if ry is None else ry
        steps = max(12, int(2 * math.pi * max(r, ry) * 1.6))
        rnd = random.Random(seed)
        holes = set(rnd.randrange(steps) for _ in range(gaps))
        for i in range(steps):
            if any(abs(i - h) <= 1 for h in holes): continue
            a = 2 * math.pi * i / steps
            self.put(cx + r * math.cos(a), cy + ry * math.sin(a), col, over)

    def spr(self):
        return SprA(dict(self.px))


def star(c, x, y, arm, core, mid, tip=None, diag=0):
    """A 4-point flash: white core, arms fading to the tip colour."""
    tip = tip or mid
    for k in range(1, arm + 1):
        col = mid if k < arm else tip
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.put(x + dx, y + dy, col)
    for k in range(1, diag + 1):
        for dx, dy in ((k, k), (-k, k), (k, -k), (-k, -k)):
            c.put(x + dx, y + dy, tip)
    c.put(x, y, core)


def parts(seed, n, smin, smax, up=0.0, spread=(0, 360)):
    """Deterministic particle set: (dir x, dir y, speed, size, spin, kind seed)."""
    r = random.Random(seed)
    out = []
    for i in range(n):
        a = math.radians(r.uniform(*spread) + (360.0 / n) * i * 0.35)
        s = r.uniform(smin, smax)
        out.append(dict(dx=math.cos(a), dy=math.sin(a) - up, s=s, size=r.choice((1, 1, 2, 2, 3)),
                        spin=r.randrange(4), k=r.random()))
    return out


def pos(p, t, g=0.0, drag=0.0):
    """Position at time t (frames): v*t decelerating by drag, plus gravity g*t^2/2 (y down positive)."""
    d = p["s"] * (t - drag * t * t * 0.5)
    return p["dx"] * d, p["dy"] * d + 0.5 * g * t * t


# ============================================================================== impact puffs ==========================
# Each god: dict of palette ramps and two frame painters (wall, hit) taking (c, f) where f = 0..4.

def flash(c, P, arm, rot=20.0, thick=True, diag=None, core=1):
    """A vanilla-style hit flash: four long streaks (slightly rotated, like ContactGenericSmall's first frame), short
    diagonal sparks between them, a white core. Streaks run white -> hi -> mid toward the tips."""
    diag = arm // 2 if diag is None else diag
    for k in range(4):
        a = math.radians(rot + 90 * k)
        L = arm if k % 2 == 0 else arm - 1
        for i in range(1, L + 1):
            col = P["white"] if i <= L // 3 else (P["hi"] if i <= 2 * L // 3 else P["mid"])
            x, y = i * math.cos(a), i * math.sin(a)
            c.put(x, y, col)
            if thick and i <= L // 2:
                c.put(x - math.sin(a) * 0.9, y + math.cos(a) * 0.9, P["hi"], over=False)
        a2 = a + math.radians(45)
        for i in range(2, diag + 1):
            c.put(i * math.cos(a2), i * math.sin(a2), P["mid"] if i < diag else P["lo"])
    c.disc(0, 0, core, P["white"])


def impact_wall_common(c, f, P, debris, g=0.0, drag=0.18, seed=1, n=9, smin=2.4, smax=4.2, ring=False, flash0=True):
    """Shared Wall timeline: f0 streak flash, f1 a small flash + the first burst, f2-4 the god's debris thinning out.
    debris(c, x, y, p, f) draws one piece."""
    if flash0 and f == 0:
        flash(c, P, 6, rot=20 + seed % 30)
    if flash0 and f == 1:
        flash(c, P, 3, rot=65 + seed % 30, thick=False, core=0)
    if ring and f in (1, 2, 3):
        r = (3, 6, 8)[f - 1]
        c.ring(0, 0, r, (P["hi"], P["mid"], P["lo"])[f - 1], gaps=f + 1, seed=seed + f)
    for p in parts(seed, n, smin, smax):
        if f == 0: continue
        x, y = pos(p, f + 0.6, g, drag)
        debris(c, x, y, p, f)


def impact_hit_common(c, f, P, debris, g=0.0, drag=0.15, seed=7, n=12, smin=2.6, smax=4.6, ring=False):
    """Hit: a bigger flash on the body (f0), its afterglow (f1), then the god's debris flying out (f1-4)."""
    if f == 0:
        flash(c, P, 8, rot=15 + seed % 30, diag=4, core=2)
    if f == 1:
        flash(c, P, 5, rot=60 + seed % 30, thick=False, diag=3, core=1)
    if ring and f in (1, 2):
        c.ring(0, 0, (5, 7)[f - 1], (P["hi"], P["mid"])[f - 1], gaps=3 + 2 * f, seed=seed + f)
    for p in parts(seed, n, smin, smax):
        if f == 0: continue
        x, y = pos(p, f + 0.8, g, drag)
        debris(c, x, y, p, f)


# ------------------------------------------------------------------ Vhorrul: wax splat (cream wax, candle flame)
VH = dict(white=hx("fff3b8"), hi=hx("ffd85e"), mid=hx("f28a26"), lo=hx("c8551a"),
          wax=[hx("7a6553"), hx("b8a276"), hx("dcc998"), hx("f4eac6")], soot=hx("5a4a42"))


def vh_drop(c, x, y, p, f):
    w = VH["wax"]
    if f <= 2:
        c.put(x, y, w[3] if p["k"] > 0.4 else w[2]);
        if p["size"] >= 2: c.put(x + 1, y, w[2]); c.put(x, y + 1, w[1])
        if p["k"] > 0.7: c.put(x, y - 1, VH["mid"])          # a lick of flame on the hot drop
    elif f == 3:
        c.put(x, y, w[2]);
        if p["size"] >= 2: c.put(x, y + 1, w[1])
    else:
        if p["k"] > 0.3: c.put(x, y, w[1])


def vh_splat(c, f, big=False):
    w = VH["wax"]
    if f >= 1:
        rx = (0, 3, 4, 4, 4)[f] + (1 if big else 0)
        ry = (0, 2.4, 3, 3, 3)[f]
        c.blob(0, 0, rx, ry, w if f < 4 else w[:3])
        if f >= 2:   # drips running down the splat
            for dx, ln in ((-2, 2 + f // 2), (1, 1 + f // 2), (3, f - 1)):
                for k in range(ln):
                    c.put(dx, ry + k, w[2] if k < ln - 1 else w[1])
        if f in (1, 2):
            c.put(-1, -1, w[3]); c.put(0, -1, VH["white"])
        if f in (2, 3):   # a wick-flame flicker on top of the cooling splat
            c.put(0, -ry - 1, VH["hi"] if f == 2 else VH["mid"]); c.put(0, -ry - 2, VH["mid"] if f == 2 else VH["lo"])
        if f == 4:
            c.put(-1, -1, VH["soot"]); c.put(1, 0, VH["soot"])


def vh_wall(c, f):
    impact_wall_common(c, f, VH, vh_drop, g=0.9, seed=11, n=8, ring=False)
    vh_splat(c, f)


def vh_hit(c, f):
    impact_hit_common(c, f, VH, vh_drop, g=0.9, seed=12)
    if f >= 2: vh_splat(c, f - 1)


# ------------------------------------------------------------------ Bel'Mora: brine splash (teal, foam)
BEL = dict(white=hx("f0fbff"), hi=hx("a8e0d0"), mid=hx("5fb3a8"), lo=hx("2f7a7a"), deep=hx("1f4f55"), foam=hx("d8f2ff"))


def bel_drop(c, x, y, p, f):
    if f <= 2:
        c.put(x, y, BEL["foam"] if p["k"] > 0.6 else BEL["hi"])
        if p["size"] >= 2: c.put(x, y + 1, BEL["mid"])
        if p["size"] >= 3: c.put(x, y + 2, BEL["lo"])
    elif f == 3:
        c.put(x, y, BEL["mid"]);
        if p["size"] >= 2: c.put(x, y + 1, BEL["lo"])
    elif p["k"] > 0.35:
        c.put(x, y, BEL["lo"])


def bel_crown(c, f, r0=3):
    """A splash crown: a ring of spikes rising then collapsing into a puddle ripple."""
    if f in (1, 2):
        h = (0, 3, 4)[f]
        for i, dx in enumerate((-4, -2, 0, 2, 4)):
            hh = h - abs(dx) // 2
            for k in range(max(1, hh)):
                c.put(dx, -k, BEL["hi"] if k == hh - 1 else BEL["mid"])
            c.put(dx, -hh, BEL["foam"])
        c.line(-5, 1, 5, 1, BEL["lo"]); c.line(-3, 0, 3, 0, BEL["mid"])
    if f >= 3:
        r = 3 + (f - 3) * 2
        c.ring(0, 1, r + 2, BEL["mid"] if f == 3 else BEL["lo"], ry=(r + 2) * 0.45, gaps=f - 2, seed=f)
        c.ring(0, 1, r, BEL["lo"], ry=r * 0.45, gaps=2, seed=f + 9)


def bel_wall(c, f):
    impact_wall_common(c, f, BEL, bel_drop, g=1.0, seed=21, n=10)
    bel_crown(c, f)


def bel_hit(c, f):
    impact_hit_common(c, f, BEL, bel_drop, g=1.0, seed=22, n=12)
    if f >= 2: bel_crown(c, min(4, f))


# ------------------------------------------------------------------ Ossivar: bone chips (ivory, marrow red)
OSS = dict(white=hx("fffaf0"), hi=hx("f4eac6"), mid=hx("dcc998"), lo=hx("b8a276"), dark=hx("7a6553"),
           dust=hx("8a8278"), marrow=hx("a81e1a"))
CHIPS = [[(0, 0), (1, 0), (0, 1)], [(0, 0), (1, 1), (1, 0)], [(0, 0), (0, 1), (1, 1)], [(0, 0), (1, 0), (1, -1)]]


def oss_chip(c, x, y, p, f):
    if f >= 4 and p["k"] < 0.5: return
    shape = CHIPS[(p["spin"] + f) % 4]
    for i, (dx, dy) in enumerate(shape if p["size"] >= 2 else shape[:1]):
        col = OSS["hi"] if i == 0 else OSS["mid"]
        if f >= 3: col = OSS["mid"] if i == 0 else OSS["lo"]
        c.put(x + dx, y + dy, col)
    if p["size"] >= 2: c.put(x + 1, y + 2, OSS["dark"], over=False)
    if p["k"] > 0.88 and f <= 2: c.put(x - 1, y, OSS["marrow"])


def oss_dust(c, f):
    if f >= 2:
        for i in range(10):
            a = i * 0.63 + f
            r = 2 + f * 1.3
            if (i + f) % 3: c.put(r * math.cos(a), r * math.sin(a) * 0.7 + f * 0.4, OSS["dust"], over=False)


def oss_wall(c, f):
    impact_wall_common(c, f, OSS, oss_chip, g=0.8, seed=31, n=9)
    oss_dust(c, f)
    if f == 1:   # the crack the bone left
        c.line(-1, -2, 1, 2, OSS["dark"]); c.put(0, 0, OSS["white"])


def oss_hit(c, f):
    impact_hit_common(c, f, OSS, oss_chip, g=0.8, seed=32, n=12)
    oss_dust(c, f)
    if f in (1, 2):   # the bone cracks: jagged dark fissures across the flash
        for (x0, y0, x1, y1, x2, y2) in ((0, 0, -3, -2, -5, -1), (0, 0, 2, 3, 4, 3), (0, 0, 3, -3, 3, -5)):
            if f == 2 and x2 < 0: continue
            c.line(x0, y0, x1, y1, OSS["dark"]); c.line(x1, y1, x2, y2, OSS["dark"] if f == 1 else OSS["lo"])


# ------------------------------------------------------------------ Sylvene: spores (sickly green puff, pink/violet spores)
SYL = dict(white=hx("f4ffd8"), hi=hx("c8f08a"), mid=hx("7fd36a"), lo=hx("5aa44a"), dark=hx("3f7a3a"),
           pink=hx("e58fb0"), vio=hx("9a5cbf"), pollen=hx("ffd85e"))


def syl_spore(c, x, y, p, f):
    col = (SYL["pollen"], SYL["pink"], SYL["vio"], SYL["hi"])[int(p["k"] * 4) % 4]
    if f >= 4 and p["k"] < 0.4: return
    c.put(x, y, col)
    if p["size"] >= 3 and f <= 2: c.put(x + 1, y, col); c.put(x, y + 1, SYL["dark"], over=False)


def syl_puff(c, f, k=1.0):
    """A spore puff: soft lobes that swell and thin out (dithered edges), never a solid blob."""
    if f == 0:
        c.blob(0, 0, 2.0 * k, 1.8 * k, [SYL["lo"], SYL["mid"], SYL["hi"], SYL["white"]])
        return
    if f <= 3:
        spread = 1 + f * 0.3
        for j, (ox, oy, r) in enumerate(((-2.2, 0.6, 2.0), (2.2, 0.8, 1.9), (0, -1.8, 2.2), (0.4, 1.6, 1.6))):
            rr = (r * 0.8 + f * 0.45) * k
            cx, cy = ox * spread * k, oy * spread * k - f * 0.6
            ramp = [SYL["lo"], SYL["mid"], SYL["hi"], SYL["white"]] if f == 1 else \
                   ([SYL["dark"], SYL["lo"], SYL["mid"], SYL["hi"]] if f == 2 else [SYL["dark"], SYL["dark"], SYL["lo"], SYL["mid"]])
            for y in range(int(cy - rr) - 1, int(cy + rr) + 2):
                for x in range(int(cx - rr) - 1, int(cx + rr) + 2):
                    u, v = (x - cx) / rr, (y - cy) / rr
                    d = u * u + v * v
                    if d > 1: continue
                    if d > (0.75 - 0.2 * f) and (x * 7 + y * 13 + f * 5 + j * 3) % 5 < 2: continue      # thinning edge
                    if f == 3 and (x * 11 + y * 5 + j) % 7 < 2: continue
                    l = 0.5 - (u * -0.6 + v * -0.8) * 0.5 - d * 0.25
                    c.put(x, y, ramp[max(0, min(3, int(l * 4)))], over=False)
    else:
        for i in range(10):
            a = i * 0.63
            c.put(6 * math.cos(a) * k, 4.5 * math.sin(a) * k - 3, SYL["lo"] if i % 2 else SYL["dark"])


def syl_wall(c, f):
    if f == 0: flash(c, SYL, 5, rot=30, thick=False)
    syl_puff(c, f, 0.9)
    for p in parts(41, 12, 2.0, 3.4, up=0.25):
        if f == 0: continue
        x, y = pos(p, f + 0.7, -0.25, 0.12)
        syl_spore(c, x, y, p, f)


def syl_hit(c, f):
    if f == 0: flash(c, SYL, 7, rot=25, diag=3, core=1)
    else: syl_puff(c, f, 1.1)
    for p in parts(42, 16, 2.3, 4.0, up=0.2):
        if f == 0: continue
        x, y = pos(p, f + 0.8, -0.2, 0.12)
        syl_spore(c, x, y, p, f)


# ------------------------------------------------------------------ Umbrael: shadow shards (violet, lilac rim)
UMB = dict(white=hx("f4eaff"), hi=hx("d8b8ff"), mid=hx("9a5cbf"), lo=hx("5b2f6e"), dark=hx("2b1a36"), glint=hx("c9d2e6"))


def umb_shard(c, x, y, p, f):
    if f >= 4 and p["k"] < 0.5: return
    L = 2 + (p["size"] >= 2) + (f <= 1)
    ux, uy = p["dx"], p["dy"]
    for k in range(L):
        col = UMB["hi"] if k == L - 1 else (UMB["mid"] if f < 3 else UMB["lo"])
        c.put(x - ux * k, y - uy * k, col)
    c.put(x + ux, y + uy, UMB["glint"] if f <= 2 else UMB["mid"])
    c.put(x - ux * L - uy, y - uy * L + ux, UMB["dark"], over=False)


def umb_core(c, f):
    """A dark rift that opens at the impact and snaps shut."""
    r = (2, 3.2, 2.4, 1.4, 0)[f]
    if r > 0:
        c.blob(0, 0, r, r * 0.8, [UMB["dark"], UMB["dark"], UMB["lo"], UMB["mid"]])
        c.ring(0, 0, r + 1, UMB["hi"] if f < 2 else UMB["mid"], gaps=1 + f, seed=f)


def umb_wall(c, f):
    impact_wall_common(c, f, UMB, umb_shard, seed=51, n=9, flash0=False)
    if f == 0: flash(c, UMB, 5, rot=45)
    umb_core(c, f)


def umb_hit(c, f):
    impact_hit_common(c, f, UMB, umb_shard, seed=52, n=10)
    if f >= 1: umb_core(c, min(4, f + 1))


# ------------------------------------------------------------------ Jinx: confetti (red, gold, cyan, magenta, green)
JNX = dict(white=hx("fff8e0"), hi=hx("ffe680"), mid=hx("e2b040"), lo=hx("b48a30"),
           conf=[hx("e8403a"), hx("ffd24a"), hx("4ad8e8"), hx("e060c8"), hx("6ae05a"), hx("fff3b8")])


def jinx_conf(c, x, y, p, f):
    col = JNX["conf"][int(p["k"] * 6) % 6]
    if f >= 4 and p["k"] < 0.35: return
    flip = (p["spin"] + f) % 3
    if flip == 0: c.put(x, y, col); c.put(x + 1, y, col)
    elif flip == 1: c.put(x, y, col); c.put(x, y + 1, col)
    else: c.put(x, y, col)
    if p["size"] == 3 and f <= 2: c.put(x + 1, y + 1, tuple(int(v * 0.6) for v in col), over=False)


def jinx_wall(c, f):
    impact_wall_common(c, f, JNX, jinx_conf, g=0.55, drag=0.2, seed=61, n=16, smin=2.6, smax=4.6)
    if f == 1: star(c, 0, 0, 2, JNX["white"], JNX["hi"], diag=1)
    if f == 2: c.put(0, 0, JNX["hi"])


def jinx_hit(c, f):
    impact_hit_common(c, f, JNX, jinx_conf, g=0.55, drag=0.2, seed=62, n=20)
    if f == 2:   # a little twinkle where the luck ran out
        star(c, -4, -4, 1, JNX["white"], JNX["hi"]); star(c, 5, -2, 1, JNX["white"], JNX["hi"])


# ------------------------------------------------------------------ Zhekra: acid fizz (acid green, bubbles)
ZHK = dict(white=hx("f4ffcc"), hi=hx("ccff66"), mid=hx("88d622"), lo=hx("488414"), dark=hx("264410"), fume=hx("b6c2a6"))


def zhk_drop(c, x, y, p, f):
    if f >= 4 and p["k"] < 0.5: return
    c.put(x, y, ZHK["hi"] if f <= 2 else ZHK["mid"])
    if p["size"] >= 2: c.put(x, y + 1, ZHK["lo"])


def zhk_bubbles(c, f):
    """Bubbles swell on the splash and pop into fizz specks that rise."""
    spots = [(-3, 0, 1.5), (2, -1, 1.2), (0, 2, 1.0), (4, 2, 1.0), (-2, -3, 1.0)]
    for i, (bx, by, br) in enumerate(spots):
        st = f - (i % 3)
        if st == 1 or st == 2:
            r = br + 0.5 * (st - 1)
            c.ring(bx, by, r + 0.5, ZHK["hi"] if st == 1 else ZHK["mid"])
            c.put(bx - 1, by - 1, ZHK["white"])
        elif st == 3:
            for dx, dy in ((-1, -1), (1, -1), (0, -2)):
                c.put(bx + dx, by + dy - 1, ZHK["fume"] if dy < -1 else ZHK["hi"])


def zhk_splat(c, f, k=1.0):
    if 1 <= f <= 3:
        rx = (0, 3.0, 4.0, 4.4)[f] * k
        c.blob(0, 0.5, rx, rx * 0.6, [ZHK["dark"], ZHK["lo"], ZHK["mid"], ZHK["hi"]])
    if f == 4:
        c.blob(0, 0.5, 4.4 * k, 2.4 * k, [ZHK["dark"], ZHK["dark"], ZHK["lo"]])


def zhk_wall(c, f):
    impact_wall_common(c, f, ZHK, zhk_drop, g=0.7, seed=71, n=7, ring=False)
    zhk_splat(c, f)
    zhk_bubbles(c, f)


def zhk_hit(c, f):
    impact_hit_common(c, f, ZHK, zhk_drop, g=0.7, seed=72, n=10)
    if f >= 2: zhk_splat(c, f - 1, 0.9); zhk_bubbles(c, f)


# ------------------------------------------------------------------ Kaurn: sparks (electric blue arcs, forge embers)
KRN = dict(white=hx("f4fcff"), hi=hx("9edaff"), mid=hx("468af0"), lo=hx("233c7a"), ember=hx("ffb040"), ember2=hx("e06a1a"))


def krn_bolt(c, ang, L, f, seed):
    r = random.Random(seed)
    x, y = 0.0, 0.0
    pts = [(0, 0)]
    for k in range(3):
        a = ang + r.uniform(-0.7, 0.7)
        x += math.cos(a) * L / 3.0; y += math.sin(a) * L / 3.0
        pts.append((x, y))
    for i in range(len(pts) - 1):
        col = KRN["white"] if (i == 0 and f <= 1) else (KRN["hi"] if f <= 1 else KRN["mid"])
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], col)


def krn_ember(c, x, y, p, f):
    if p["k"] < 0.45: return            # most pieces are arcs, a few are forge embers
    if f >= 4 and p["k"] < 0.75: return
    vx, vy = p["dx"], p["dy"] + 0.25 * f
    c.put(x, y, KRN["ember"] if f <= 2 else KRN["ember2"])
    c.put(x - vx, y - vy, KRN["ember2"] if f <= 2 else KRN["lo"], over=False)


def krn_wall(c, f):
    impact_wall_common(c, f, KRN, krn_ember, g=0.8, seed=81, n=10)
    if f in (0, 1, 2):
        for i in range(4 if f < 2 else 3):
            krn_bolt(c, i * 1.7 + f * 0.6, (5, 8, 9)[f], f, 800 + f * 10 + i)
    if f == 3:
        for i in range(3): c.put(6 * math.cos(i * 2.1), 6 * math.sin(i * 2.1), KRN["mid"])


def krn_hit(c, f):
    impact_hit_common(c, f, KRN, krn_ember, g=0.8, seed=82, n=12)
    if f in (1, 2, 3):
        for i in range(5 if f < 3 else 3):
            krn_bolt(c, i * 1.26 + f, (8, 10, 9)[f - 1], min(f, 3), 900 + f * 10 + i)


# ------------------------------------------------------------------ Ysveld: ice chips (pale cyan, navy, white glints)
YSV = dict(white=hx("ffffff"), hi=hx("f0f9ff"), mid=hx("8abee4"), lo=hx("588cc2"), dark=hx("3b6098"), cyan=hx("8ef2ff"))
ICE_CHIPS = [[(0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)], [(0, -1), (0, 0), (1, 0), (0, 1)], [(0, 0), (1, 0), (0, 1)], [(0, -1), (0, 0), (0, 1)]]


def ysv_chip(c, x, y, p, f):
    if f >= 4 and p["k"] < 0.45: return
    shape = ICE_CHIPS[(p["spin"] + f) % 4] if p["size"] >= 2 else [(0, 0)]
    for i, (dx, dy) in enumerate(shape):
        col = YSV["hi"] if dy < 0 or (dx < 0) else (YSV["mid"] if dx == 0 and dy == 0 else YSV["lo"])
        if f >= 3: col = YSV["mid"] if dy <= 0 else YSV["lo"]
        c.put(x + dx, y + dy, col)
    if p["k"] > 0.8 and f <= 2: c.put(x, y, YSV["white"])


def ysv_frost(c, f):
    if f in (2, 3, 4):
        r = (0, 0, 5, 7, 8)[f]
        for i in range(12):
            if (i + f) % 2: continue
            a = i * math.pi / 6
            c.put(r * math.cos(a), r * math.sin(a), YSV["cyan"] if f == 2 else (YSV["mid"] if f == 3 else YSV["dark"]))
    if f == 1:
        c.ring(0, 0, 3, YSV["cyan"])


def ysv_wall(c, f):
    impact_wall_common(c, f, YSV, ysv_chip, g=0.6, seed=91, n=9, ring=False)
    ysv_frost(c, f)
    if f == 1: c.put(0, 0, YSV["white"])


def ysv_hit(c, f):
    impact_hit_common(c, f, YSV, ysv_chip, g=0.6, seed=92, n=11)
    ysv_frost(c, f)


# ------------------------------------------------------------------ Mod (neutral): pale dust ring with the mod's violet glint
MOD = dict(white=hx("ffffff"), hi=hx("e6e0ee"), mid=hx("aaa2b8"), lo=hx("6e6a74"), vio=hx("9a5cbf"), vio2=hx("c48ae8"))


def mod_dust(c, x, y, p, f):
    if f >= 4 and p["k"] < 0.5: return
    c.put(x, y, MOD["hi"] if f <= 2 else MOD["mid"])
    if p["k"] > 0.75 and f <= 2: c.put(x, y, MOD["vio2"])


def mod_wall(c, f):
    impact_wall_common(c, f, MOD, mod_dust, seed=101, n=8, ring=True)
    if f == 2: star(c, 0, 0, 1, MOD["white"], MOD["vio2"])
    if f == 3: c.put(0, 0, MOD["vio"])


def mod_hit(c, f):
    impact_hit_common(c, f, MOD, mod_dust, seed=102, n=10)
    if f == 2: c.ring(0, 0, 7, MOD["mid"], gaps=3, seed=5)
    if f == 2: star(c, 0, 0, 2, MOD["white"], MOD["vio2"], MOD["vio"])


# ------------------------------------------------------------------ Wpn (hero weapons): neutral metallic sparks
WPN = dict(white=hx("ffffff"), hi=hx("fff2a0"), mid=hx("ffc040"), lo=hx("c86a1a"), steel=hx("d6dae0"), steel2=hx("9a96a0"),
           grey=hx("45414c"))


def wpn_spark(c, x, y, p, f):
    if f >= 4 and p["k"] < 0.5: return
    vx, vy = p["dx"], p["dy"] + 0.3 * f
    n = math.hypot(vx, vy) or 1
    vx, vy = vx / n, vy / n
    if p["k"] < 0.3:      # a metal fleck
        c.put(x, y, WPN["steel"] if f <= 2 else WPN["steel2"])
        return
    L = (3, 3, 2, 2, 1)[f]
    for k in range(L):
        col = (WPN["white"] if k == 0 else WPN["hi"]) if f <= 1 else ((WPN["hi"] if k == 0 else WPN["mid"]) if f <= 2 else (WPN["mid"] if k == 0 else WPN["lo"]))
        c.put(x - vx * k, y - vy * k, col)


def wpn_wall(c, f):
    impact_wall_common(c, f, dict(WPN, hi=WPN["steel"], mid=WPN["hi"], lo=WPN["mid"]), wpn_spark, g=0.9, drag=0.1, seed=111, n=10, smin=2.8, smax=4.6)
    if f == 2: c.put(0, 0, WPN["mid"]); c.put(1, 0, WPN["lo"])


def wpn_hit(c, f):
    impact_hit_common(c, f, dict(WPN, hi=WPN["steel"], mid=WPN["hi"], lo=WPN["mid"]), wpn_spark, g=0.9, drag=0.1, seed=112, n=13)


GODS = [("Vh", vh_wall, vh_hit), ("Bel", bel_wall, bel_hit), ("Oss", oss_wall, oss_hit), ("Syl", syl_wall, syl_hit),
        ("Umb", umb_wall, umb_hit), ("Jinx", jinx_wall, jinx_hit), ("Zhk", zhk_wall, zhk_hit), ("Krn", krn_wall, krn_hit),
        ("Ysv", ysv_wall, ysv_hit), ("Mod", mod_wall, mod_hit), ("Wpn", wpn_wall, wpn_hit)]


def build_impacts(out, core_out):
    built = []
    for god, wall, hit in GODS:
        dest = core_out if god == "Mod" else out   # the neutral puff is Core's (ImpactFx.Neutral)
        anims = []
        for an, fn, du, lim in (("Wall", wall, WALL_D, 10), ("Hit", hit, HIT_D, 11)):
            frames = []
            for f in range(5):
                c = C(box=(-lim, -lim, lim, lim))
                fn(c, f)
                frames.append(c.spr())
            anims.append((an, frames, du))
        name = "FxCommonImpact" + god
        img, man = pack(name, anims, 24, 24, (12, 12), dest, cols=5)
        preview(img, man, os.path.join(dest, name + "_preview.png"), scale=8)
        built.append(name)
        for an, fr, _ in anims:
            bb = [f.bbox() for f in fr if f.px]
            w = max(b[2] for b in bb) - min(b[0] for b in bb) + 1
            h = max(b[3] for b in bb) - min(b[1] for b in bb) + 1
            print("built %-22s %-4s 5f  union %dx%d" % (name, an, w, h))
    return built


# ============================================================================== status overlays =======================
# Slow: sludge. A murky ochre-olive tar pooled round the feet (drawn in front of the feet so they read as sunk),
# drips sliding off the shins into it, bubbles that swell and pop.
SL = [hx("2e2616"), hx("4f4222"), hx("7a6a32"), hx("a8954a"), hx("d2c070"), hx("f0e6a8")]


def slow_frame(f, big=False):
    """Feet at (0, 0); the cell keeps two rows below the feet line."""
    c = C(box=(-16, -13, 15, 2))
    w = 13 if big else 8           # half width of the pool
    h = 3.4 if big else 2.4
    wob = math.sin(f * math.pi / 3)
    # the pool: dark rim, olive body, a bright wet lip on the back edge
    c.blob(0, 0.2, w + 0.3 * wob, h, [SL[1], SL[2], SL[2], SL[3]])
    for x in range(-w + 1, w):
        yb = int(round(0.2 + h * math.sqrt(max(0.0, 1 - (x / (w + 0.3)) ** 2))))
        c.put(x, yb, SL[0])
    for x in range(-w + 2, w - 1, 1):           # specular lip along the back edge, moving slowly
        yt = -int(round(h * math.sqrt(max(0.0, 1 - (x / w) ** 2)))) + 1
        if (x + f) % 4 == 0: c.put(x, yt, SL[4])
        elif (x + f) % 4 == 1: c.put(x, yt, SL[3])
    # tar strands clinging to the shins (the feet read as sunk), stretching and sagging over the loop
    for sx in ((-2, 2) if not big else (-4, -1, 2, 5)):
        hgt = 2 + ((f + sx) % 3 == 0) + (1 if big else 0)
        for k in range(1, hgt + 1):
            c.put(sx, -k + 0.2, SL[3] if k == hgt else SL[2])
        c.put(sx + 1, -1, SL[1], over=False)
    for x in range(-w + 1, w, 3):              # lumpy front lip
        c.put(x + (f % 2), int(round(0.2 + h)) , SL[2])
    # drips sliding down off the shins into the pool (6-frame cycle, two lanes per side)
    lanes = [(-3, 0), (3, 3)] if not big else [(-6, 0), (-2, 2), (3, 4), (7, 1)]
    top = -7 if not big else -10
    for lx, ph in lanes:
        t = (f + ph) % 6
        y = top + t * (-top) / 5.0
        if t < 5:
            c.put(lx, y, SL[4]); c.put(lx, y - 1, SL[3]); c.put(lx, y - 2, SL[2], over=False)
        else:
            c.put(lx - 1, -1, SL[4]); c.put(lx + 1, -1, SL[4]); c.put(lx, -2, SL[5])   # the plop
    # bubbles: swell, pop
    spots = [(-5, 1, 0), (4, 0, 3)] if not big else [(-9, 1, 0), (-3, 1, 2), (5, 0, 4), (10, 1, 1)]
    for bx, by, ph in spots:
        t = (f + ph) % 6
        if t in (0, 1):
            c.put(bx, by - t, SL[5] if t else SL[4]); c.put(bx + 1, by - t, SL[3])
            if t: c.put(bx, by - t - 1, SL[4]); c.put(bx + 1, by - t - 1, SL[4])
        elif t == 2:
            c.put(bx - 1, by - 2, SL[4]); c.put(bx + 2, by - 2, SL[4]); c.put(bx, by - 3, SL[5])
    return c.spr()


# Root: bark tendrils, drawn with the material renderer. Dark bark with pale-green growth tips; Grip bursts them out
# of the floor and coils them round the ankles, Loop keeps them squirming and tightening.


def _mr():
    """The material renderer the god art uses (jinx_v2_rigs.py), with the root overlay's bark and growth ramps."""
    if HERE not in sys.path: sys.path.insert(0, HERE)
    import jinx_v2_rigs as mr
    mr.RAMPS.setdefault("rbark", [hx(c) for c in ("1e1612", "3e2c1e", "6b4e32", "94704a", "c49a64")])
    mr.RAMPS.setdefault("rgrow", [hx(c) for c in ("1c3a14", "3a6a22", "5e9a36", "8fd36a", "d8f0a0")])
    return mr


def bez(p0, p1, p2, n=6):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / float(n - 1) for i in range(n))]


def tendril(r, base, ctrl, tip, z, k=1.0, bud=False):
    """A bark tendril from the floor to a pale green growing tip, thick at the root."""
    pts = bez(base, ctrl, tip)
    r.tube(pts, [1.5 * k, 1.3 * k, 1.1 * k, 0.9 * k, 0.7 * k, 0.5], "rbark", z, bias=0.05)
    r.dot(tip[0], tip[1], "rgrow", 4, z + 0.01)
    r.dot(pts[-2][0], pts[-2][1], "rgrow", 3, z + 0.01)
    if bud:
        r.ell(tip[0] + (1 if tip[0] > 0 else -1), tip[1] - 1, 1.1, 0.8, "rgrow", z + 0.02, bias=0.2)


def root_frame(stage, f, big=False):
    """stage 'grip' (f 0..2) or 'loop' (f 0..3). Feet at (0, 0)."""
    mr = _mr()
    r = mr.Rig()
    k = 1.55 if big else 1.0
    s = 1.0 if stage == "loop" else (0.35, 0.7, 1.0)[f]
    sq = 0.0 if stage == "grip" else (0, 1, 0, -1)[f]           # squirm phase
    # torn floor: a dark crack ring with lifted clods the tendrils come up through
    rw = 7 * k
    r.ell(0, 0.6, rw + 1, 1.4, "rbark", -1.0, flat=0)
    for x in (-rw, -rw * 0.4, rw * 0.5, rw):
        r.ell(x, 0.2, 1.2, 0.8, "rbark", -0.9, bias=0.2)
    # back tendrils (outside the body's width): rise beside the legs, curl over
    for side in (-1, 1):
        tip = (side * (6.5 * k - sq * 0.7), -(5.5 * k + 1.5) * s)
        ctrl = (side * (8.5 * k), -3.0 * k * s)
        tendril(r, (side * 6 * k, 0.5), ctrl, tip, 0.5 if side < 0 else 0.4, k, bud=stage == "loop" and side < 0 and f in (1, 2))
    # the wrap: a tendril coiled round the ankles. Front turns are lit and drawn over the feet; back turns only show
    # outside the legs, darker.
    if s > 0.5:
        hw = 4.5 * k
        turns = 1.25 if s < 1 else 1.75
        y0, y1 = -0.5, -(4.5 * k if s >= 1 else 3.0 * k)
        ph = (0.0 if stage == "grip" else f * math.pi / 2)
        steps = 48
        run = []
        for i in range(steps + 1):
            u = i / float(steps)
            th = ph + u * turns * 2 * math.pi
            x = hw * math.sin(th)
            y = y0 + (y1 - y0) * u + 1.5 * math.cos(th)
            if math.cos(th) > 0:
                run.append((x, y))
                continue
            if len(run) > 1: r.tube(run, [0.9 * k], "rbark", 1.0, bias=0.15)
            run = []
            if abs(x) >= 2.5: r.dot(x, y, "rbark", 1, -0.5)
        if len(run) > 1: r.tube(run, [0.9 * k], "rbark", 1.0, bias=0.15)
        tipx = hw * math.sin(ph + turns * 2 * math.pi)
        r.dot(tipx, y1 - 1, "rgrow", 3, 1.1); r.dot(tipx + 1, y1 - 2, "rgrow", 4, 1.1)
        for kx in (-3, 3):     # thorns standing off the coil
            r.dot(kx * k, y0 + (y1 - y0) * 0.5 - 1.5, "rgrow", 2, 1.05)
    # grip: earth clods thrown up as they burst out
    if stage == "grip":
        for i, (dx, dy) in enumerate(((-8, -2), (8, -3), (-5, -5), (6, -6), (0, -4))):
            if i % 3 == f % 3 or f == 0:
                r.ell(dx * k * (0.6 + 0.3 * f), dy * (0.5 + 0.4 * f), 0.8, 0.7, "rbark", 2.0, bias=0.2)
    return r.resolve(floor=False, cast=False)


# Daze: two violet birds and two gold stars on a tilted orbit over the head. Objects alternate bird/star at 90
# degrees; four frames rotate the orbit 45 degrees each, so frame 4 == frame 0 with the birds and stars swapped... and
# since frame 4 has rotated 180 degrees, bird lands on bird: a seamless 4-frame loop.
DZ = dict(gold=hx("ffd85e"), gold2=hx("f28a26"), white=hx("fffbe8"), vio=hx("c48ae8"), vio2=hx("9a5cbf"), vio3=hx("5e3a7a"),
          dim=hx("b49646"))


def daze_frame(f, big=False):
    c = C(box=(-12, -12, 11, 0))
    rx, ry = (5.0, 1.8) if not big else (8.0, 2.8)
    cy = -2.5 if not big else -3.5
    objs = []
    for i in range(4):
        a = math.radians(i * 90 + f * 45 + 20)
        x, y = rx * math.cos(a), cy + ry * math.sin(a)
        front = math.sin(a) > -0.15
        objs.append((math.sin(a), x, y, "bird" if i % 2 == 0 else "star", front, i))
    objs.sort()   # back first
    for _, x, y, kind, front, i in objs:
        x, y = int(round(x)), int(round(y))
        if kind == "star":
            if big and front:
                star(c, x, y, 2, DZ["white"], DZ["gold"], DZ["gold2"])
            elif front:
                star(c, x, y, 1, DZ["white"], DZ["gold"])
            else:
                c.put(x, y, DZ["dim"])
        else:
            up = (f + i // 2) % 2 == 0          # wing beat
            body = DZ["vio"] if front else DZ["vio3"]
            wing = DZ["vio2"] if front else DZ["vio3"]
            c.put(x, y, body)
            if up:
                c.put(x - 1, y - 1, wing); c.put(x + 1, y - 1, wing)
                if big: c.put(x - 2, y - 2, wing); c.put(x + 2, y - 2, wing)
            else:
                c.put(x - 1, y, wing); c.put(x + 1, y, wing)
                if big: c.put(x - 2, y + 1, wing); c.put(x + 2, y + 1, wing)
            if front: c.put(x, y - 1 if not up else y + 1, DZ["white"] if big else DZ["vio"], over=False)
    return c.spr()


def build_status(out):
    slow = [("Loop", [slow_frame(f) for f in range(6)], [0.1] * 6),
            ("LoopBig", [slow_frame(f, True) for f in range(6)], [0.1] * 6)]
    img, man = pack("FxCommonStatusSlow", slow, 32, 16, (16, 13), out, cols=6)
    preview(img, man, os.path.join(out, "FxCommonStatusSlow_preview.png"), scale=8)
    root = [("Grip", [root_frame("grip", f) for f in range(3)], [0.05, 0.06, 0.07]),
            ("Loop", [root_frame("loop", f) for f in range(4)], [0.12] * 4),
            ("GripBig", [root_frame("grip", f, True) for f in range(3)], [0.05, 0.06, 0.07]),
            ("LoopBig", [root_frame("loop", f, True) for f in range(4)], [0.12] * 4)]
    img, man = pack("FxCommonStatusRoot", root, 32, 20, (16, 17), out, cols=7)
    preview(img, man, os.path.join(out, "FxCommonStatusRoot_preview.png"), scale=8)
    daze = [("Loop", [daze_frame(f) for f in range(4)], [0.11] * 4),
            ("LoopBig", [daze_frame(f, True) for f in range(4)], [0.11] * 4)]
    img, man = pack("FxCommonStatusDaze", daze, 24, 10, (12, 9), out, cols=4)
    preview(img, man, os.path.join(out, "FxCommonStatusDaze_preview.png"), scale=8)
    for name, an in (("Slow", slow), ("Root", root), ("Daze", daze)):
        for a, fr, _ in an:
            bb = [f.bbox() for f in fr if f.px]
            print("built FxCommonStatus%-5s %-8s %df  union %dx%d" % (name, a, len(fr), max(b[2] for b in bb) - min(b[0] for b in bb) + 1,
                                                                  max(b[3] for b in bb) - min(b[1] for b in bb) + 1))


# ============================================================================== effect indicators =====================
# Readable markers for buffs, debuffs, stacks and charges that have no status overlay of their own (src/CrawlFurther.Core/Monsters/ModStatus.cs
# ModInd). Counters are head icons: one icon per stack, with the empty slots of a fixed-size meter drawn as dim outlines
# so "2 of 3" reads at a glance. Body effects (regen, heal, haste, ice) are feet overlays drawn round the legs and up
# the flanks, clear of the face. Every icon has a 1 px dark outline so it holds on the dark dungeon floor.

def icon(c, rows, x, y, pal, over=True):
    """Stamp a char-grid icon with its top-left at (x, y); '.' and ' ' are clear, other chars index pal."""
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch in ". ":
                continue
            col = pal.get(ch)
            if col is not None:
                c.put(x + i, y + j, col, over)


# ---- Rime meter (Ysveld frost stacks on the hero: the third binds). Three ice-crystal slots; filled = bright crystal.
RIME = dict(o=hx("0c1630"), D=hx("2c5a92"), M=hx("5aa6e0"), L=hx("a6e2ff"), W=hx("f4fdff"), e=hx("3e5f8c"), E=hx("8fc8f0"))
CRYSTAL = ["..o..",
           ".oWo.",
           ".oLo.",
           "oLWMo",
           "oLMDo",
           ".oMo.",
           "..o.."]
CRYSTAL_EMPTY = ["..e..",
                 ".e.e.",
                 ".e.e.",
                 "e...e",
                 "e...e",
                 ".e.e.",
                 "..e.."]


def meter_frame(n, slots, f, full, empty, pal, glint, warn=None, spacing=7, h=7):
    """n filled of `slots` slots, centred on x = 0, bottom row on y = 0. glint(c, x, y, f, k) adds per-slot sparkle;
    warn(c, x, y, f) animates the next empty slot when only one is left."""
    c = C(box=(-12, -h - 1, 11, 0))
    w = spacing * (slots - 1) + len(full[0])
    x0 = -(w // 2)
    for k in range(slots):
        x = x0 + k * spacing
        y = -h + 1
        if k < n:
            icon(c, full, x, y, pal)
            glint(c, x, y, f, k)
        else:
            if empty is not None:
                icon(c, empty, x, y, pal)
            if warn is not None and k == n and n == slots - 1:
                warn(c, x, y, f)
    return c.spr()


def rime_glint(c, x, y, f, k):
    # a white glint climbs each crystal in turn, plus a twinkle off the tip
    if (f + k) % 4 == 0:
        c.put(x + 1, y + 3, RIME["W"]); c.put(x + 2, y + 2, RIME["W"])
    if (f + k) % 4 == 2:
        c.put(x + 2, y - 1, RIME["E"])


def rime_warn(c, x, y, f):
    # the slot that binds pulses brighter (frames 0-1) so a second stack reads as "one more and you're frozen"
    if f in (0, 1):
        icon(c, CRYSTAL_EMPTY, x, y, dict(e=RIME["E"]))
        if f == 0: c.put(x + 2, y + 3, RIME["D"])


# ---- Static charge (Kaurn: up to 3 pips, all fly at the hero on the special). Lightning-bolt pips, empty = dark slot.
CHG = dict(o=hx("170f28"), Y=hx("ffd23a"), O=hx("e07a18"), W=hx("fffbe0"), B=hx("6cc6ff"), e=hx("3b4258"))
BOLT = ["..ooo",
        ".oYYo",
        ".oYo.",
        "oYWYo",
        ".oYo.",
        "oYo..",
        "oo..."]
BOLT_EMPTY = ["..eee",
              ".e..e",
              ".e.e.",
              "e...e",
              ".e.e.",
              "e.e..",
              "ee..."]


def charge_glint(c, x, y, f, k):
    # the bolt flickers: core flashes white on alternate frames, an arc spark jumps beside it
    if (f + k) % 2 == 0:
        c.put(x + 2, y + 1, CHG["W"]); c.put(x + 2, y + 3, CHG["W"])
    else:
        c.put(x + 1, y + 5, CHG["O"])
    sx = (x - 1, x + 5)[(f + k) % 2]
    sy = y + 1 + ((f * 3 + k) % 4)
    c.put(sx, sy, CHG["B"])


# ---- Plates (any monster/hero plate that blocks one hit each): small steel heater shields, one per plate.
PLT = dict(o=hx("16161e"), D=hx("4e5366"), M=hx("8e95ac"), L=hx("cfd5e6"), W=hx("ffffff"), G=hx("e6c25a"))
SHIELD = ["ooooooo",
          "oWLLMDo",
          "oLLGMDo",
          "oLGGGDo",
          ".oMGDo.",
          "..oDo..",
          "...o..."]


def plate_glint(c, x, y, f, k):
    # a glint sweeps across the shields left to right
    t = (f - k) % 4
    if t == 0: c.put(x + 2, y + 1, PLT["W"]); c.put(x + 1, y + 2, PLT["W"])
    if t == 1: c.put(x + 4, y + 1, PLT["W"])


# ---- Might (damage up): a red-orange double chevron that pulses upward.
MGT = dict(o=hx("2e0a0a"), R=hx("b0261e"), O=hx("ee5a26"), Y=hx("ffb040"), W=hx("fff0b0"))
CHEV = ["...o...",
        "..oYo..",
        ".oYOYo.",
        "oYOoOYo",
        "oOo.oOo",
        "oo...oo"]


def might_frame(f):
    c = C(box=(-8, -10, 7, 0))
    lift = (0, 1, 1, 0)[f]
    icon(c, CHEV, -3, -9 - lift, dict(o=MGT["o"], Y=MGT["Y"] if f != 1 else MGT["W"], O=MGT["O"]))
    icon(c, CHEV, -3, -5 - lift, dict(o=MGT["o"], Y=MGT["O"], O=MGT["R"]))
    # embers rising off the top
    for i, (ex, ph) in enumerate(((-4, 0), (4, 2))):
        t = (f + ph) % 4
        c.put(ex, -4 - t * 1.5 - lift, (MGT["Y"], MGT["O"], MGT["R"], None)[t] if t < 3 else MGT["R"])
    return c.spr()


# ---- Regen (heals over time: brine / wax / resin regeneration, any regen buff). Green crosses rising up the flanks.
RG = dict(o=hx("12301a"), D=hx("2f7a32"), M=hx("5ccc4e"), L=hx("aef58a"), W=hx("f2ffe0"))


def cross(c, x, y, lvl, big=False):
    """A plus with a dark outline (arms 1 px, or 2 px when big); lvl 3 bright .. 0 faint (outline dropped)."""
    x, y = int(round(x)), int(round(y))
    core = (RG["D"], RG["M"], RG["L"], RG["W"])[lvl]
    arm = (RG["D"], RG["D"], RG["M"], RG["L"])[lvl]
    r = 2 if big else 1
    if lvl >= 2:
        for k in range(-r, r + 1):
            for dx, dy in ((k, -1), (k, 1), (-1, k), (1, k)):
                if abs(dx) <= 1 and abs(dy) <= 1 and (dx == 0 or dy == 0): continue
                c.put(x + dx, y + dy, RG["o"], over=False)
            for dx, dy in ((-r - 1, 0), (r + 1, 0), (0, -r - 1), (0, r + 1)):
                c.put(x + dx, y + dy, RG["o"], over=False)
    for k in range(1, r + 1):
        for dx, dy in ((-k, 0), (k, 0), (0, -k), (0, k)):
            c.put(x + dx, y + dy, arm if k == r else core)
    c.put(x, y, core)


def regen_frame(f, big=False):
    """Loop 6: crosses (big: five) climb the flanks and fade, larger near the feet; motes drift up between them; a
    green glow ring breathes round the feet. Feet at (0, 0)."""
    hgt = 30 if big else 19
    c = C(box=(-17, -hgt - 3, 16, 2))
    # feet glow first (crosses draw over it): dim back half, brighter front half, breathing
    rx, ry = (9, 2.2) if not big else (14, 3.2)
    breathe = (0, 1, 1, 0, 0, 0)[f]
    for i in range(96):
        a = 2 * math.pi * i / 96
        front = math.sin(a) > 0
        col = (RG["L"] if breathe else RG["M"]) if front else RG["D"]
        c.put(rx * math.cos(a), ry * math.sin(a), col, over=front)
    lanes = [(-7, 0), (7, 2), (-4, 4)] if not big else [(-12, 0), (11, 2), (-6, 4), (7, 1), (0, 3)]
    for lx, ph in lanes:
        t = (f + ph) % 6
        y = -3 - t * (hgt - 5) / 5.0
        lvl = (3, 3, 3, 2, 1, 0)[t]
        cross(c, lx + (1 if t in (2, 3) else 0) * (1 if lx > 0 else -1), y, lvl, big=t < 2)
    for i, (mx, ph) in enumerate(((-10, 1), (9, 4), (2, 0), (-2, 3)) if not big else ((-15, 1), (14, 4), (3, 0), (-3, 3), (8, 5), (-9, 2))):
        t = (f + ph) % 6
        y = -1 - t * hgt / 6.0
        c.put(mx, y, (RG["W"], RG["L"], RG["M"], RG["M"], RG["D"], RG["D"])[t])
    return c.spr()


def heal_frame(f, big=False):
    """Play 6 (one-shot): a white-green flash ring at the feet, then crosses burst up and out and fade."""
    hgt = 30 if big else 20
    c = C(box=(-17, -hgt - 3, 16, 2))
    k = 1.55 if big else 1.0
    # the ring: flashes white, then expands and thins
    rx, ry = (5 + 2.2 * f) * k, (1.6 + 0.6 * f) * k
    if f < 5:
        col = (RG["W"], RG["L"], RG["M"], RG["D"], RG["D"])[f]
        for i in range(40):
            a = 2 * math.pi * i / 40
            if f >= 3 and i % 3 == 0: continue
            c.put(rx * math.cos(a), ry * math.sin(a), col)
    # crosses fly up from the body centre on a fan
    n = 5 if not big else 7
    for i in range(n):
        a = math.radians(-90 + (i - (n - 1) / 2.0) * (26 if not big else 20))
        sp = (hgt * 0.55) * (0.75 + 0.25 * ((i * 7) % 3))
        d = sp * (1 - (1 - min(1.0, (f + 1) / 6.0)) ** 2)
        x = math.cos(a) * d * (0.9 if not big else 1.1)
        y = -hgt * 0.35 + math.sin(a) * d
        if f == 0:
            continue
        lvl = (3, 3, 3, 2, 1, 0)[f]
        cross(c, x, y, lvl, big=f < 3)
    # a bright sparkle on the body at the start
    if f in (0, 1):
        star(c, 0, int(-hgt * 0.35), 2 if f == 0 else 1, RG["W"], RG["L"], RG["M"])
    return c.spr()


# ---- Haste (move speed up): a wind ring whipping round the ankles, speed streaks peeling off both sides.
HS = dict(o=hx("2a3346"), D=hx("7f97b0"), M=hx("c6d8ea"), W=hx("ffffff"), G=hx("f0d27a"))


def haste_frame(f, big=False):
    """Loop 4: a wind ring whips round the ankles (a bright arc chases round it) and paired speed lines peel off
    both sides; dust kicks at the heels."""
    c = C(box=(-16, -14, 15, 2))
    rx, ry = (8, 2.4) if not big else (13, 3.4)
    n = 56
    for i in range(n):
        a = 2 * math.pi * i / n
        front = math.sin(a) > 0
        ph = (i - f * (n // 4)) % n
        if ph < n // 5:
            col = HS["W"] if ph < n // 10 else HS["M"]
        else:
            col = HS["M"] if front else HS["D"]
        c.put(rx * math.cos(a), -1 + ry * math.sin(a), col, over=front)
    rows = (-3, -6) if not big else (-3, -7, -11)
    for side in (-1, 1):
        for j, yy in enumerate(rows):
            t = (f + j) % 4
            x0 = side * (rx + 1 + t)
            ln = (5, 4, 3, 2)[t] + (1 if big else 0)
            for q in range(ln):
                col = HS["W"] if q < 2 and t < 2 else (HS["M"] if t < 3 else HS["D"])
                c.put(x0 + side * q, yy, col)
    for side in (-1, 1):
        t = (f + (0 if side < 0 else 2)) % 4
        if t < 3:
            c.put(side * (3 + t), 1 - t, HS["G"] if t == 0 else HS["D"])
            if t == 1: c.put(side * (4 + t), 1 - t, HS["D"])
    return c.spr()


# ---- Ice (on Ysveld ice: the hero slides, Ysveld monsters skate faster): a glassy skid under the feet, glints running
# along it and ice chips flicking off the edges.
ICE = dict(o=hx("12243e"), D=hx("2f6aa0"), M=hx("7cc4ee"), L=hx("c6eeff"), W=hx("ffffff"))


def ice_frame(f, big=False):
    c = C(box=(-16, -9, 15, 2))
    rx, ry = (9, 1.6) if not big else (14, 2.3)
    # the skid: a flat glossy ellipse in front of the feet (dark rim, pale body)
    for x in range(-int(rx), int(rx) + 1):
        hh = ry * math.sqrt(max(0.0, 1 - (x / (rx + 0.4)) ** 2))
        for y in range(-int(round(hh)), int(round(hh)) + 1):
            edge = abs(y) == int(round(hh)) or abs(x) >= int(rx) - 1
            c.put(x, y, (ICE["D"] if y > 0 else ICE["M"]) if edge else (ICE["L"] if y <= 0 else ICE["M"]))
    # skid scratches running out behind both sides
    for side in (-1, 1):
        for q in range(3 + (1 if big else 0)):
            if (q + f) % 2 == 0: c.put(side * (rx + 1 + q), 0, ICE["D"])
    # glints sliding along the top edge
    for g in range(2):
        gx = -rx + 2 + ((f * 4 + g * int(rx)) % int(2 * rx - 3))
        c.put(gx, -int(round(ry)) + 1, ICE["W"]); c.put(gx + 1, -int(round(ry)) + 1, ICE["L"])
    # frost chips flicked up off the edges, and a twinkle star
    for side, ph in ((-1, 0), (1, 2)):
        t = (f + ph) % 4
        if t < 3:
            c.put(side * (rx - 2 + t), -2 - t * 1.5, (ICE["W"], ICE["L"], ICE["M"])[t])
    tx = (-4, 5, 2, -6)[f] * (1.5 if big else 1)
    star(c, int(tx), -int(round(ry)) - 3, 1, ICE["W"], ICE["L"])
    return c.spr()


def build_indicators(out, content_out):
    built = []

    def emit(name, anims, cw, ch, feet, cols=8, dest=None):
        dest = dest or out
        img, man = pack(name, anims, cw, ch, feet, dest, cols=cols)
        preview(img, man, os.path.join(dest, name + "_preview.png"), scale=8)
        for an, fr, _ in anims:
            bb = [s.bbox() for s in fr if s.px]
            print("built %-20s %-8s %df  union %dx%d" % (name, an, len(fr), max(b[2] for b in bb) - min(b[0] for b in bb) + 1,
                                                       max(b[3] for b in bb) - min(b[1] for b in bb) + 1))
        built.append(name)

    D4 = [0.12] * 4
    # head counters: 24 x 9 cells, bottom row = the art's bottom (feet = (12, 8))
    emit("FxCommonIndRime",
         [(nm, [meter_frame(n, 3, f, CRYSTAL, CRYSTAL_EMPTY, RIME, rime_glint, rime_warn) for f in range(4)], D4)
          for nm, n in (("One", 1), ("Two", 2))], 24, 9, (12, 8), dest=content_out)   # Ysveld's (content)
    emit("FxCommonIndCharge",
         [(nm, [meter_frame(n, 3, f, BOLT, BOLT_EMPTY, CHG, charge_glint) for f in range(4)], [0.08] * 4)
          for nm, n in (("One", 1), ("Two", 2), ("Three", 3))], 24, 9, (12, 8))
    emit("FxCommonIndPlates",
         [(nm, [meter_frame(n, n, f, SHIELD, None, PLT, plate_glint, spacing=8) for f in range(4)], [0.14] * 4)
          for nm, n in (("One", 1), ("Two", 2), ("Three", 3))], 24, 9, (12, 8))
    emit("FxCommonIndMight", [("Loop", [might_frame(f) for f in range(4)], [0.1] * 4)], 16, 11, (8, 10))
    # body overlays: feet two rows above the cell bottom (code offset -2)
    emit("FxCommonIndRegen", [("Loop", [regen_frame(f) for f in range(6)], [0.1] * 6),
                              ("LoopBig", [regen_frame(f, True) for f in range(6)], [0.1] * 6)], 36, 38, (18, 35), cols=6)
    emit("FxCommonIndHeal", [("Play", [heal_frame(f) for f in range(6)], [0.05, 0.06, 0.07, 0.08, 0.09, 0.1]),
                             ("PlayBig", [heal_frame(f, True) for f in range(6)], [0.05, 0.06, 0.07, 0.08, 0.09, 0.1])],
         36, 38, (18, 35), cols=6)
    emit("FxCommonIndHaste", [("Loop", [haste_frame(f) for f in range(4)], [0.07] * 4),
                              ("LoopBig", [haste_frame(f, True) for f in range(4)], [0.07] * 4)], 32, 18, (16, 15), cols=4)
    emit("FxCommonIndIce", [("Loop", [ice_frame(f) for f in range(4)], [0.11] * 4),
                            ("LoopBig", [ice_frame(f, True) for f in range(4)], [0.11] * 4)], 32, 14, (16, 11), cols=4,
         dest=content_out)   # Ysveld's (content)
    return built


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(CORE_OUT, exist_ok=True)
    if "--ind" not in sys.argv:
        build_status(CORE_OUT)
        build_impacts(OUT, CORE_OUT)
    build_indicators(CORE_OUT, OUT)
