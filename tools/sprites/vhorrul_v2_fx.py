"""Vhorrul effects: the floor's three states (wax, lit wax, flames), the god perk's pyre and slick, and every effect the
monsters' moves need. Built through vhorrul_v2_rigs.py. Each sheet's origin (its spawn point, the pixel Strike.ArtAt /
Strike.Ground puts on the spawn) is listed in TIMING.md."""
import math, random
from vhorrul_v2_rigs import (Rig, lerp, flame, candle, smoke_curl, drip, floor_pool, ember_dots, glow_ring, fx_sheet, line_px)
from vhorrul_v2_t2 import swipe_arc
from vhorrul_v2_t3a import doll, body_shadow


def F(fn, *a, **k):
    r = Rig()
    fn(r, *a, **k)
    return r.resolve(floor=False)


def tongues(r, cx, cy, rx, ry, n, ph, h=4.0, mat="fire", z=1.0, seed=1):
    """A field of flame tongues standing on an ellipse of floor (burning pools, pyres, rings)."""
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, math.tau); d = math.sqrt(rnd.random())
        x, y = cx + rx * d * math.cos(a), cy + ry * d * math.sin(a)
        hh = h * (0.6 + 0.6 * rnd.random()) * (1.0 - 0.3 * d)
        flame(r, x, y, hh, ph + i, mat, z + y * 0.01)


# ------------------------------------------------------------------ the floor: wax, burning pools, the pyre and its slick
def fx_wax_puddle(outdir):
    """FxWaxPuddle Life: a puddle of unlit wax (forms, sits 4.8 s with a slow glisten, skins over and fades)."""
    def f(r, k, form=1.0, fade=0.0):
        rx, ry = 10.0 * form, 3.4 * form
        floor_pool(r, 0, 0, rx, ry, "tallow", 0.0, tone=2 if fade < 0.5 else 1)
        if fade < 0.8:
            floor_pool(r, -1.5, -0.6, rx * 0.5, ry * 0.4, "tallow", 0.1, tone=3, rim=False)
            r.dot(-4 + (k % 4) * 2, -1, "tallow", 4, 0.2)
        if fade > 0.3:
            for x in (-6, 0, 5): r.dot(x, 1, "tallow", 1, 0.2)
    frs = [F(f, 0, 0.5), F(f, 0, 0.85)] + [F(f, k) for k in range(8)] + [F(f, 0, 1.0, 0.5), F(f, 0, 0.9, 1.0)]
    fx_sheet("FxWaxPuddle", [("Life", frs, [0.08, 0.1] + [0.6] * 8 + [0.3, 0.3])], outdir, (26, 12), (13, 6))


def fx_burning_pool(outdir):
    """FxEmberPatch Loop: lit wax, a 20 x 7 pool of burning tallow (4 frames; the kit repeats it)."""
    def f(r, k):
        floor_pool(r, 0, 0, 10.0, 3.4, "bees", 0.0, tone=2)
        floor_pool(r, 0, 0, 7.0, 2.2, "ember", 0.05, tone=1, rim=False)
        tongues(r, 0, 0, 8.5, 2.6, 7, k, 4.5, seed=3)
    fx_sheet("FxEmberPatch", [("Loop", [F(f, k) for k in range(4)], [0.1] * 4)], outdir, (24, 16), (12, 12))


def fx_pyre(outdir):
    """FxVhPyre: a dead Vhorrul monster's pyre, 28 x 9: Ignite 2, Burn 3 (the kit repeats it), Gutter 3."""
    def f(r, k, h=1.0, gut=0.0):
        floor_pool(r, 0, 0, 14.0, 4.4, "bees", 0.0, tone=2 if gut < 0.6 else 1)
        floor_pool(r, 0, 0, 10.0, 3.0, "ember", 0.05, tone=1 if gut < 0.6 else 0, rim=False)
        if h > 0.05:
            tongues(r, 0, -0.5, 11.0, 3.4, 11, k, 9.0 * h, seed=5)
            tongues(r, 0, -1.0, 5.0, 1.4, 3, k + 2, 13.0 * h, seed=8)
        for i in range(3 if gut else 2):   # sparks rising
            r.dot(-5 + i * 5 + (k % 2), -12 - (k * 3 + i * 4) % 8, "ember", 3, 3.0)
        if gut: smoke_curl(r, 0, -6 * (1 - gut) - 2, k, 3.0, 1.0)
    ign = [F(f, 0, 0.4), F(f, 1, 0.8)]
    burn = [F(f, k) for k in range(3)]
    gut = [F(f, 0, 0.5, 0.3), F(f, 1, 0.25, 0.6), F(f, 2, 0.0, 1.0)]
    fx_sheet("FxVhPyre", [("Ignite", ign, [0.12, 0.12]), ("Burn", burn, [0.18] * 3), ("Gutter", gut, [0.14, 0.16, 0.16])],
             outdir, (34, 28), (17, 22))


def fx_pyre_wax(outdir):
    """FxVhPyreWax: the tallow slick a pyre cools into, 26 x 8: Set 2, Idle 1 (the kit holds it), Fade 2."""
    def f(r, set_=1.0, fade=0.0):
        floor_pool(r, 0, 0, 13.0 * set_, 4.0 * set_, "tallow", 0.0, tone=2 if fade < 0.5 else 1)
        floor_pool(r, -2, -0.6, 6.0 * set_, 1.6 * set_, "tallow", 0.1, tone=3 if fade < 0.5 else 2, rim=False)
        if set_ >= 1.0 and fade < 0.5:
            for x in (-7, 3, 8): r.dot(x, -1, "tallow", 4, 0.2)
            r.dot(1, 0, "ember", 1, 0.2)   # a last coal in the slick
    fx_sheet("FxVhPyreWax", [("Set", [F(f, 0.7), F(f, 1.0)], [0.06, 0.06]), ("Idle", [F(f)], [0.8]),
                             ("Fade", [F(f, 1.0, 0.5), F(f, 0.9, 1.0)], [0.2, 0.2])], outdir, (30, 12), (15, 6))


def fx_wax_line(outdir):
    """FxVhWaxLine Life: one 10 px segment of the Chandler's poured line, unlit and glistening (a glint runs along it)."""
    def f(r, k, form=1.0, fade=0.0):
        floor_pool(r, 0, 0, 6.0 * form, 2.0 * form, "tallow", 0.0, tone=2 if fade < 0.5 else 1)
        if fade < 0.5:
            r.line(-4, -1, 4, -1, "tallow", 0.1, tone=3)
            r.dot(-4 + (k * 2) % 9, -1, "white", 3, 0.2)
            r.dot(-3 + (k * 2) % 9, -1, "tallow", 4, 0.2)
    frs = [F(f, 0, 0.5)] + [F(f, k) for k in range(8)] + [F(f, 0, 1.0, 1.0)]
    fx_sheet("FxVhWaxLine", [("Life", frs, [0.08] + [0.75] * 8 + [0.3])], outdir, (16, 8), (8, 4))


def fx_line_flare(outdir):
    """FxVhLineFlare Play: the flame racing along the line flares up through one segment (hit live f1-2)."""
    def f(r, k):
        h = (4.0, 11.0, 9.0, 6.0, 3.0)[k]
        floor_pool(r, 0, 0, 6.0, 2.0, "bees", 0.0, tone=2)
        tongues(r, 0, 0, 5.0, 1.4, 5, k, h, seed=11)
        if k in (1, 2): ember_dots(r, [(-3, -h - 1, 3), (2, -h, 3), (0, -h - 3, 2)])
    fx_sheet("FxVhLineFlare", [("Play", [F(f, k) for k in range(5)], [0.05, 0.07, 0.08, 0.08, 0.08])], outdir, (16, 20), (8, 16))


# ------------------------------------------------------------------ globs and bolts
def fx_globs(outdir):
    """FxWaxGlob Fly (a glob of wax drawn 8 px over its floor origin), FxVhMoltenGlob Fly (burning, 12 px up)."""
    def g(r, k, lift, mat, lit):
        y = -lift
        r.ell(0, y, 2.2, 1.8, mat, 0.0, ang=k * 30)
        r.dot(-1, y - 1, mat, 4, 0.1)
        for i in range(2): r.dot(-3 - i - k % 2, y + i * 0.5, mat, 2, -0.1)
        if lit: flame(r, 0, y - 1, 3.0, k, "fire", 0.5)
        floor_pool(r, 0, 0, 2.0, 0.6, "soot", -3.0, rim=False, tone=1)
    fx_sheet("FxWaxGlob", [("Fly", [F(g, k, 8.0, "tallow", False) for k in range(3)], [0.08] * 3)], outdir, (12, 14), (6, 12))
    fx_sheet("FxVhMoltenGlob", [("Fly", [F(g, k, 12.0, "bees", True) for k in range(3)], [0.08] * 3)], outdir, (14, 22), (7, 19))


def fx_bolts(outdir):
    """Bolts flying right: FxCandleBolt (the Candelabra's flame), FxVhVotiveFlame (red votive glass and flame),
    FxVhHexFlame (hex violet), FxLanternOrb (soul teal), FxVhSowDrop (hot fat), FxVhFork (a flame forking)."""
    def bolt(r, k, mat, core=None, tail=5):
        """A flying flame: a teardrop head, a tail of fire streaming back, embers shed behind it."""
        p = r.part(True, 0.0)
        wob = (0.0, 0.5, 0.0, -0.5)[k % 4]
        for x in range(-8, 2):
            t = (x + 8) / 9.0                     # 0 at the tail tip .. 1 at the head
            hw = 0.3 + 1.7 * t ** 1.4
            yc = wob * (1.0 - t)
            for y in range(int(math.floor(yc - hw)), int(math.ceil(yc + hw)) + 1):
                d = abs(y - yc) / max(0.5, hw)
                if d > 1.0: continue
                r.put(x, y, 0.0, mat, 0.5, p, 3 if d < 0.45 and t > 0.3 else 2 if t > 0.15 else 1)
        r.ell(1.5, 0.0, 2.4, 2.0, mat, 0.1, flat=3)
        r.ell(2.0, -0.3, 1.3, 1.1, core or mat, 0.2, flat=4)
        r.dot(2.6, -0.6, "white", 4, 0.3)
        r.dot(-1 + (k % 2), -2, mat, 3, 0.1); r.dot(-3, 1 + (k % 2), mat, 2, 0.1)   # tongues licking off the tail
        for i, (dx, dy) in enumerate(((-10, -1), (-12, 1), (-11, 0))):
            if (i + k) % 2: r.dot(dx - (k % 2), dy, "ember", 3 - i % 2, -0.1)
    fx_sheet("FxCandleBolt", [("Fly", [F(bolt, k, "fire") for k in range(4)], [0.06] * 4)], outdir, (20, 10), (12, 5))
    def votive(r, k):
        bolt(r, k, "fire", "sigil")
        r.poly([(0, 2), (3, 2), (3, 0), (0, 0)], "votive", 0.5)   # the red votive glass it flies in
        r.dot(1, 0, "votive", 4, 0.6)
    fx_sheet("FxVhVotiveFlame", [("Fly", [F(votive, k) for k in range(4)], [0.06] * 4)], outdir, (20, 10), (12, 5))
    fx_sheet("FxVhHexFlame", [("Fly", [F(bolt, k, "fire", "hex") for k in range(4)], [0.06] * 4)], outdir, (20, 10), (12, 5))
    def orb(r, k):
        r.ell(0, 0, 2.6, 2.6, "soul", 0.0, flat=2)
        r.ell(-0.5, -0.5, 1.4, 1.4, "soul", 0.1, flat=3)
        r.dot(-1, -1, "soul", 4, 0.2)
        for i in range(4):
            a = k * 0.8 + i * 1.57
            r.dot(3.4 * math.cos(a), 3.4 * math.sin(a), "soul", 2, 0.3)
    fx_sheet("FxLanternOrb", [("Fly", [F(orb, k) for k in range(4)], [0.07] * 4)], outdir, (12, 12), (6, 6))
    def fat(r, k):
        r.ell(0, 0, 1.6, 1.3, "bees", 0.0)
        r.dot(-0.5, -0.6, "bees", 4, 0.1)
        for i in range(2): r.dot(-2 - i - k % 2, i * 0.5, "tallow", 3 - i, -0.1)
    fx_sheet("FxVhSowDrop", [("Fly", [F(fat, k) for k in range(3)], [0.07] * 3)], outdir, (10, 8), (5, 4))
    def fork(r, k):
        for s in (-1, 1):
            for i in range(3 + k * 2):
                r.dot(i, s * i * 0.47, "fire", 4 if i < 2 else 3 if i < 5 else 2, 0.1)
        r.ell(0, 0, 1.6 - k * 0.3, 1.6 - k * 0.3, "white", 0.2, flat=3)
    fx_sheet("FxVhFork", [("Play", [F(fork, k) for k in range(4)], [0.04, 0.05, 0.06, 0.06])], outdir, (16, 14), (4, 7))


def fx_ash(outdir):
    """FxAshCloud Puff: the Ash Moth's drifting ash puff (5 frames). FxVhAshCloud Drift: the Seraph's smothered fire
    rising as a dazing ash cloud (loops). FxVhSmother Rise: a column of smoke off a fire it beat out."""
    def billow(r, cx, cy, size, k, seed, ember=True, n=6):
        """A cloud of ash: overlapping puffs lit from the top left (the renderer shades them), a coal in the heart."""
        rnd = random.Random(seed)
        for i in range(n):
            a = rnd.uniform(0, math.tau) + k * 0.25; d = rnd.uniform(0.2, 1.0) * size
            rr = size * rnd.uniform(0.45, 0.75)
            r.ell(cx + d * math.cos(a), cy + d * math.sin(a) * 0.65, rr, rr * 0.85, "ash", 0.1 * i)
        r.ell(cx - size * 0.3, cy - size * 0.35, size * 0.5, size * 0.4, "ash", 0.9, bias=0.25)
        if ember:
            r.dot(cx, cy, "ember", 4 if k % 2 else 3, 1.0); r.dot(cx + 1, cy + 1, "ember", 2, 1.0)
        for i in range(2):   # wisps trailing off
            r.dot(cx - size - 1 - i - k % 2, cy + i, "smoke", 3 - i, -0.5)

    def puff(r, k):
        size = (1.6, 2.6, 3.6, 4.2, 4.6)[k]
        billow(r, 0, 0, size, k, 7, ember=k < 3, n=4 + k)
        if k >= 3:   # thinning out: holes in the cloud
            for (dx, dy) in ((-1, 0), (2, 1), (0, -2)): r.put(dx, dy, 5.0, "smoke", 0.5, r.part(True, 5.0), 1)
    fx_sheet("FxAshCloud", [("Puff", [F(puff, k) for k in range(5)], [0.1, 0.14, 0.3, 0.35, 0.3])], outdir, (22, 18), (11, 9))
    def cloud(r, k):
        billow(r, 0, -6, 4.6, k, 13, n=8)
        floor_pool(r, 0, 0, 5.0, 1.2, "soot", -3.0, rim=False, tone=1)
    fx_sheet("FxVhAshCloud", [("Drift", [F(cloud, k) for k in range(4)], [0.12] * 4)], outdir, (22, 18), (11, 14))
    def column(r, k):
        for j in range(3 + k * 2):
            if j < k - 1: continue
            r.ell(math.sin(j + k) * 1.2, -j * 3.0, 2.2, 1.8, "ash", 0.1 * j, bias=0.1 * (j % 2))
        if k < 2: floor_pool(r, 0, 0, 5.0, 1.4, "soot", -2.0, tone=1); ember_dots(r, [(0, -1, 3)])
    fx_sheet("FxVhSmother", [("Rise", [F(column, k) for k in range(6)], [0.08, 0.1, 0.12, 0.14, 0.16, 0.2])], outdir, (20, 42), (10, 38))


# ------------------------------------------------------------------ status and body overlays
def fx_overlays(outdir):
    """Overlays anchored at the bottom-centre of their cell: FxVhKindled Loop (flames running up the Waxen Knight's
    armour), FxVhFever Loop (heat shimmer and a red flush on the hero), FxVhSoulless Loop (over the hero's head: his
    soul flame gone, a guttered wick), FxVhAnoint Loop (over a head: a halo flame of holy fire)."""
    def kindled(r, k):
        for i, (x, h) in enumerate(((-5, 7), (-2, 10), (1, 12), (4, 8), (6, 6), (-6, 4))):
            flame(r, x, -6 - (i % 3) * 5 + (k % 2), h * 0.6, k + i, "fire", 0.1 * i, wide=0.9)
        for i in range(4): r.dot(-4 + i * 3, -1 - (k + i) % 3, "ember", 3, 2.0)
    fx_sheet("FxVhKindled", [("Loop", [F(kindled, k) for k in range(4)], [0.08] * 4)], outdir, (22, 30), (11, 29))
    def fever(r, k):
        for i, x in enumerate((-4, 0, 4)):
            for j in range(5):
                r.dot(x + ((j + k + i) % 3 - 1) * 0.6, -4 - j * 2.4, "heat", 3 if j % 2 else 2, 0.1)
        r.dot(-2, -1, "heat", 3, 0.2); r.dot(2, -1, "heat", 3, 0.2)
    fx_sheet("FxVhFever", [("Loop", [F(fever, k) for k in range(4)], [0.1] * 4)], outdir, (14, 18), (7, 17))
    def soulless(r, k):
        r.line(0, 0, 0, -3, "wick", 0.0, tone=3)
        smoke_curl(r, 0, -4, k, 0.2, 0.8)
        r.dot(0, -3, "soul", 1 + (k % 2), 0.3)
    fx_sheet("FxVhSoulless", [("Loop", [F(soulless, k) for k in range(4)], [0.15] * 4)], outdir, (8, 11), (4, 10))
    def anoint(r, k):
        glow_ring(r, 0, -2, 4.0, "sigil", 0.0, 3, 1.4)
        flame(r, 0, -2.5, 3.6, k, "sigil", 0.2, wide=0.8)
        r.dot(-4 + (k % 2), -3, "sigil", 4, 0.3)
    fx_sheet("FxVhAnoint", [("Loop", [F(anoint, k) for k in range(4)], [0.1] * 4)], outdir, (12, 10), (6, 9))
    def sigil(r, k):
        flame(r, 0, -1, 6.0, k, "sigil", 0.0, wide=1.2)
        for (dx, dy) in ((0, -8), (0, -9), (-1, -9), (1, -9), (0, -10)):
            r.dot(dx, dy - (k % 2), "sigil", 4, 0.2)
    fx_sheet("FxVhSigilFlame", [("Loop", [F(sigil, k) for k in range(4)], [0.1] * 4)], outdir, (10, 14), (5, 13))


# ------------------------------------------------------------------ move effects
def fx_moves(outdir):
    # Wickling: the tail relighting white-hot
    def flare(r, k):
        R = (2, 5, 7, 8, 8)[k]
        for i in range(8):
            a = i / 8.0 * math.tau + k * 0.2
            r.dot(R * math.cos(a), -4 + R * math.sin(a) * 0.8, "spark" if k < 3 else "ember", 4 - min(3, k), 1.0)
        if k < 3: flame(r, 0, 0, 7.0 - k * 1.5, k, "spark", 0.5)
    fx_sheet("FxVhFlare", [("Play", [F(flare, k) for k in range(5)], [0.05, 0.06, 0.07, 0.08, 0.1])], outdir, (20, 20), (10, 14))
    # Tallow Sow: a shot glancing off her greased hide
    def glance(r, k):
        for i in range(4):
            a = math.radians(-60 + i * 40)
            d = 2 + k * 2
            r.dot(d * math.cos(a), d * math.sin(a), "white", 4 - k, 0.0)
        r.dot(0, 0, "grease", 4, 0.1)
    fx_sheet("FxVhGlance", [("Play", [F(glance, k) for k in range(3)], [0.05, 0.06, 0.08])], outdir, (14, 14), (7, 7))
    # Tallow Sow: a wax egg (lands, sits 2 s, cracks and spits)
    def egg(r, k, crack=0, wob=0.0):
        r.ell(wob, -3.0, 2.4, 3.0, "bees", 0.0)
        r.dot(-1 + wob, -5, "bees", 4, 0.1)
        if crack:
            r.polyline([(-1, -6), (0, -4), (-1, -2)], "soot", 0.2, tone=1)
            if crack > 1: ember_dots(r, [(0, -4, 3), (0, -3, 2)], 0.3)
        floor_pool(r, 0, 0, 3.0, 1.0, "tallow", -1.0, rim=False, tone=1)
    frs = [F(egg, 0, wob=0.0)] + [F(egg, 0, wob=w) for w in (0.0, 0.6, 0.0, -0.6)] + [F(egg, 0, 1, 0.8), F(egg, 0, 2, -0.8)]
    fx_sheet("FxVhWaxEgg", [("Life", frs, [0.1, 0.35, 0.35, 0.35, 0.35, 0.25, 0.25])], outdir, (10, 12), (5, 10))
    # Moth Matron: an ember moth (drifting) and the same moth hunting (wings flared white, angled)
    def mothlet(r, k, hunt):
        up = (1, 0, -1, 0)[k]
        for s in (-1, 1):
            r.poly([(0, 0), (s * 3, -2 - up), (s * 3.4, 0), (s * 1.5, 1.5)], "ash" if not hunt else "ashw", 0.0 if s > 0 else -0.2)
            r.dot(s * 3, -1 - up, "ember" if not hunt else "white", 3, 0.1)
        r.ell(0, 0, 0.8, 1.6, "ember", 0.5, flat=3)
        r.dot(0, -1, "ember", 4, 0.6)
    fx_sheet("FxVhEmberMoth", [("Drift", [F(mothlet, k, False) for k in range(4)], [0.08] * 4),
                               ("Hunt", [F(mothlet, k, True) for k in range(4)], [0.05] * 4)], outdir, (10, 8), (5, 4))
    # Tallow Colossus: the body-shaped shadow of its Topple, one length per layer
    def shadow(r, L):
        n = 28 + 10 * L
        body_shadow(r, n, tone=0)
        for x in range(5, 4 + n, 3):   # a rim of embers so the dark shape reads on the dark floor
            t = (x - 4) / float(n)
            hw = 2.5 + 2.0 * math.sin(math.pi * min(1.0, t * 1.2))
            r.dot(x, -1.5 - int(hw * 0.5) - 1, "ember", 1, 1.0); r.dot(x + 1, -1.5 + int(hw * 0.5) + 1, "ember", 1, 1.0)
    fx_sheet("FxVhToppleShadow", [("S%d" % L, [F(shadow, L)], [0.8]) for L in range(4)], outdir, (72, 8), (2, 5))
    # Pyre Warden: Stoke's rings of fire spreading out (radius 12, 24, 36)
    def ring(r, R, k):
        p = r.part(True, 0.0)
        n = int(R * 3)
        for i in range(n):
            a = i / float(n) * math.tau
            x, y = R * math.cos(a), R * 0.4 * math.sin(a)
            if (i + k) % 3 == 0: flame(r, x, y, (5.0, 4.0, 2.4, 1.2)[k], i + k, "fire", y * 0.01)
            else: r.put(x, y, 0.0, "ember", 0.5, p, 3 - (k > 1))
    fx_sheet("FxVhStokeRing", [("R%d" % i, [F(ring, R, k) for k in range(4)], [0.06, 0.08, 0.1, 0.12]) for i, R in ((1, 12), (2, 24), (3, 36))],
             outdir, (80, 36), (40, 20))
    # Tallow Renderer: the wave of boiling tallow (40 px wide across its path; flies right)
    def wave(r, k):
        p = r.part(True, 0.0)
        for yy in range(-20, 21):
            y = yy * 0.95
            bow = 3.0 * (1.0 - (yy / 20.0) ** 2)                 # the middle of the wave runs ahead
            crest = bow + math.sin(yy * 0.6 + k * 1.5) * 0.7
            back = crest - 7.0 + math.sin(yy * 0.3 - k) * 0.8
            for x in range(int(back), int(crest) + 1):
                t = (x - back) / max(1.0, crest - back)
                tone = 4 if x >= int(crest) else 3 if t > 0.7 else 2 if t > 0.3 else 1
                r.put(x, y, 0.0, "bees", 0.5, p, tone)
            if (yy + k) % 3 == 0: r.put(int(crest) + 1, y, 0.1, "white", 0.5, p, 3)        # foam on the lip
            if (yy * 7 + k * 3) % 11 == 0: r.put(int(back) + 2, y, 0.1, "bees", 0.5, p, 1)  # a bubble bursting
            if (yy * 5 + k) % 13 == 0: r.put(int(back) + 3, y - 1, 0.1, "tallow", 0.5, p, 4)
        for i in range(5):
            smoke_curl(r, -4 + (i % 2) * 2, -16 + i * 8, k + i, 1.0, 0.7)
    fx_sheet("FxVhBoilWave", [("Roll", [F(wave, k) for k in range(4)], [0.07] * 4)], outdir, (20, 48), (10, 24))
    # Wick Hag: the wax poppet of the hero (sits lit, flinches when burned, melts at the end), and the red thread
    fx_sheet("FxVhPoppet", [("Sit", [F(lambda r, k: (doll(r, 0, 0, 0.0, ph=k), floor_pool(r, 0, 0, 2.6, 0.8, "soot", -2, rim=False, tone=1)), k) for k in range(4)], [0.12] * 4),
                            ("Flinch", [F(lambda r, k: (doll(r, 0, 0, 0.0, ph=k, flinch=(1, -1, 0)[k]), ember_dots(r, [(-2, -4, 3), (2, -3, 3)])), k) for k in range(3)], [0.06] * 3),
                            ("Melt", [F(lambda r, k: doll(r, 0, 0, 0.0, ph=k, melt=k / 4.0), k) for k in range(5)], [0.1] * 5)],
             outdir, (10, 14), (5, 12))
    def thread(r, k):
        r.dot(0, 0, "votive" if k else "heat", 3, 0.0); r.dot(1, 0, "heat", 2, 0.0)
    fx_sheet("FxVhThread", [("Loop", [F(thread, k) for k in range(2)], [0.1, 0.1])], outdir, (4, 4), (1, 2))
    # Candle Wyrm: one segment of the burning coil, glowing white before it closes in
    def seg(r, k, white=False):
        floor_pool(r, 0, 0, 3.0, 1.2, "bees", 0.0, rim=False)
        flame(r, -1, 0, 5.0 if not white else 6.0, k, "white" if white else "fire", 0.5)
        flame(r, 1.5, 0.5, 3.0, k + 2, "spark" if white else "blue", 0.6, core=False)
    fx_sheet("FxVhCoil", [("Burn", [F(seg, k) for k in range(4)], [0.08] * 4), ("White", [F(seg, k, True) for k in range(2)], [0.06] * 2)],
             outdir, (10, 14), (5, 11))
    # Fuse Scorpion: the fizzing spark and the smoke it leaves on the hero's path
    def spark(r, k):
        for i in range(6):
            a = i / 6.0 * math.tau + k * 0.5
            d = 2 + (i + k) % 3
            r.dot(d * math.cos(a), -2 + d * math.sin(a), "spark", 4 if d < 3 else 3, 0.5)
        r.dot(0, -2, "white", 4, 1.0)
    fx_sheet("FxVhFuseSpark", [("Fizz", [F(spark, k) for k in range(4)], [0.05] * 4)], outdir, (12, 12), (6, 9))
    def smoke(r, k):
        for j in range(2 + k):
            r.dot(math.sin(j + k) * 0.6, -j * 1.6, "smoke", 3 - min(2, k // 2), 0.0)
        if k < 2: r.dot(0, 0, "soot", 1, -0.1)
    fx_sheet("FxVhFuseSmoke", [("Puff", [F(smoke, k) for k in range(4)], [0.15, 0.2, 0.25, 0.3])], outdir, (6, 10), (3, 8))
    # Grub Mother: the grubling (crawling, and lit after crawling through fire)
    def grubling(r, k, lit):
        for i in range(3):
            r.ell(-2 + i * 2 + (0.4 if (i + k) % 2 else 0), -1.6 - (0.4 if (i + k) % 2 else 0), 1.6, 1.4, "tallow", 0.1 * i)
        r.dot(3, -2, "ember", 3, 0.5)
        if lit: flame(r, 0, -3, 3.4, k, "fire", 0.6)
    fx_sheet("FxVhGrubling", [("Crawl", [F(grubling, k, False) for k in range(4)], [0.1] * 4),
                              ("CrawlLit", [F(grubling, k, True) for k in range(4)], [0.1] * 4)], outdir, (12, 10), (6, 7))
    # Lantern Wraith: the cone that takes the hero's soul flame (points right from the lantern)
    def cone(r, k):
        p = r.part(True, 0.0)
        for d in range(2, 50, 2):
            if d > 12 + k * 12: break
            w = d * 0.42
            for j in range(-int(w), int(w) + 1, 2):
                if (d + j + k) % 4 == 0:
                    r.put(d, j, 0.0, "soul", 0.5, p, 3 if d < 20 else 2)
        if k >= 2: flame(r, 48 - k * 6, 0, 3.0, k, "fire", 0.5)   # his flame drawn back into the lantern
    fx_sheet("FxVhSoulCone", [("Play", [F(cone, k) for k in range(5)], [0.05, 0.06, 0.08, 0.1, 0.1])], outdir, (54, 44), (2, 22))
    # Grand Chandelier: a drop of hot wax falling from the ring, and the ring flaring at one point
    def drop(r, k):
        y = (-16, -10, -4, 0)[k]
        if k < 3:
            r.ell(0, y, 1.0, 1.4, "tallow", 0.0); r.dot(0, y - 1, "tallow", 4, 0.1)
        else:
            floor_pool(r, 0, 0, 3.0, 1.0, "tallow", 0.0)
            for s in (-1, 1): r.dot(s * 3, -1, "tallow", 4, 0.1)
    fx_sheet("FxVhDrip", [("Fall", [F(drop, k) for k in range(4)], [0.06, 0.06, 0.08, 0.14])], outdir, (10, 20), (5, 17))
    def ringflare(r, k):
        floor_pool(r, 0, 0, 4.0, 1.4, "bees", 0.0, rim=False)
        flame(r, 0, 0, (5.0, 12.0, 9.0, 4.0)[k], k, "fire", 0.5, wide=1.4)
    fx_sheet("FxVhRingFlare", [("Play", [F(ringflare, k) for k in range(4)], [0.05, 0.08, 0.1, 0.12])], outdir, (12, 20), (6, 16))
    # Waxen Knight: the Seal shell cracking off as a slowing ring (Ring), or thrown out lit (Lit)
    def shock(r, k, lit):
        R = (8, 14, 20, 24)[k]
        p = r.part(True, 0.0)
        n = int(R * 3)
        for i in range(n):
            a = i / float(n) * math.tau
            x, y = R * math.cos(a), R * 0.4 * math.sin(a)
            if lit and (i + k) % 3 == 0: flame(r, x, y, 4.0 - k, i, "fire", y * 0.01)
            r.put(x, y, 0.0, "tallow", 0.5, p, 4 - min(2, k))
            if (i + k) % 4 == 0: r.put(x * 0.85, y * 0.85, 0.0, "tallow", 0.5, p, 3)
    fx_sheet("FxWaxShockwave", [("Ring", [F(shock, k, False) for k in range(4)], [0.07, 0.08, 0.1, 0.14]),
                                ("Lit", [F(shock, k, True) for k in range(4)], [0.07, 0.08, 0.1, 0.14])], outdir, (56, 26), (28, 13))


# ------------------------------------------------------------------ the gold idol: Vhorrul's likeness
def fx_idol(outdir):
    """DeityGoldIdolVhorrul Idle: a hooded saint of gold, kneeling, its face melted wax run down over the chest, cupped
    hands round a real flame, gold drips frozen mid-fall, on a heap of guttered candle stubs; a ring of candles round it
    and a halo of flame. A glint sweeps the gold (8 frames, like the plain gold idol). 29 x 24, feet at (14, 22)."""
    def idol(r, k, glint):
        # the dark niche it stands in, like the plain gold idol's tile
        pb = r.part(False, -9.0)
        for y in range(-22, 2):
            for x in range(-14, 15):
                edge = x in (-14, 14) or y in (-22, 1)
                r.put(x, y, -9.0, "soot", 0.5, pb, 0 if edge else (1 if abs(x) > 11 or y < -19 else 0))
        glow_ring(r, 0, -14.0, 8.5, "fire", -8.0, 2 + (k % 2), 7.5)       # the halo of flame behind the hood
        # shoulders and robe, kneeling
        r.poly([(-12, 0), (12, 0), (8, -9), (-8, -9)], "gold", 0.0, curve=0.7)
        # the hood, the melted wax face in its shadow
        r.ell(0, -13.5, 6.4, 7.2, "gold", 0.5)
        r.ell(0.6, -12.6, 3.8, 4.6, "gold", 0.6, bias=-0.45)
        for x, ln in ((-1.6, 6), (0.0, 9), (1.2, 7), (2.4, 4)):           # wax run down over the chest, set there
            drip(r, x, -12.0, ln, "tallow", 0.7)
        r.dot(-0.6, -13.6, "tallow", 4, 0.72); r.dot(1.8, -13.4, "tallow", 3, 0.72)
        for x, y, ln in ((-6.0, -14, 3), (6.2, -12, 4), (-9.0, -5, 2), (9.4, -4, 3)):   # gold drips frozen mid-fall
            drip(r, x, y, ln, "gold", 0.8)
        # cupped hands round the one real flame; it throws a warm bounce up onto the wax face
        r.ell(0, -3.2, 3.6, 1.8, "gold", 0.9)
        flame(r, 0, -4.4, 6.0, k, "fire", 1.0, wide=1.2)
        r.dot(-1, -8, "fire", 2, 0.75); r.dot(1, -9, "fire", 3, 0.75)
        # guttered stubs at its knees
        for i, x in enumerate((-12.0, -9.5, 9.5, 12.0)):
            candle(r, x, 0.0, 2.0 + (i % 2), 1.6, z=1.2, mat="gold", ph=k + i, flh=2.2, drip=1)
        if glint is not None:
            p = r.part(True, 2.0)
            for (x, y), v in list(r.b.items()):
                if v[1] == "gold" and abs((x - y * 0.6) - glint) < 1.0:
                    r.put(x, y, v[0] + 0.001, "gold", 0.5, p, 4)
    frs = [F(idol, i % 4, -14 + i * 6) for i in range(5)] + [F(idol, i, None) for i in range(3)]
    fx_sheet("DeityGoldIdolVhorrul", [("Idle", frs, [0.06, 0.06, 0.06, 0.06, 0.06, 0.22, 0.2, 0.5])], outdir, (29, 24), (14, 22), scale=8)


# ------------------------------------------------------------------ the god portrait: the Tallow Saint
def fx_deity(outdir):
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    frs = frames("vhorrul", (14, 23))
    fx_sheet("DeityVhorrul", [("Idle", frs, [0.18] * 4)], outdir, (29, 24), (14, 23), scale=8)


JOBS = [("FxWaxPuddle", fx_wax_puddle), ("FxEmberPatch", fx_burning_pool), ("FxVhPyre", fx_pyre), ("FxVhPyreWax", fx_pyre_wax),
        ("FxVhWaxLine", fx_wax_line), ("FxVhLineFlare", fx_line_flare), ("FxWaxGlob", fx_globs), ("FxCandleBolt", fx_bolts),
        ("FxAshCloud", fx_ash), ("FxVhKindled", fx_overlays), ("FxVhFlare", fx_moves), ("DeityGoldIdolVhorrul", fx_idol),
        ("DeityVhorrul", fx_deity)]
SYNC = {}
NOTES = {"FxVhPyre": "Origin = the pyre's centre on the floor. The kit plays Ignite, Burn x9, Gutter.",
         "FxVhStokeRing": "R1 / R2 / R3: rings of radius 12, 24, 36 px (floor ellipse, ry = 0.4 r), each one spawned 0.5 s after the last.",
         "FxVhBoilWave": "Flies right; the crest is 40 px across its path, drawn on the origin's x.",
         "FxVhToppleShadow": "S0-S3: 28 + 10 per layer px long, starting 4 px ahead of the feet (origin at the cell's left).",
         "DeityGoldIdolVhorrul": "Vhorrul's gold idol portrait (SlotGods.PortraitFor, gold tier)."}
