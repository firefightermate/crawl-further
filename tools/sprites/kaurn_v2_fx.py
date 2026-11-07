"""Kaurn effect sheets, drawn with the same material renderer as the monsters (kaurn_v2_rigs.py). Points are pixels from
each sheet's origin (the second tuple passed to fx()), y up negative; the code places every template by that origin
(Strike.ArtAt / Strike.Ground), and arc segments (12 px long, anchored mid-centre) are laid end to end along a link."""
import math, random
from kaurn_v2_rigs import (Rig, lerp, fx, done, bolt, zig, crackle, spark, rod, shadow, line_px, dust_puff, hammer, BUILT)
from kaurn_v2_t3b import PLANETS
from jinx_v2_rigs import stone


def R():
    return Rig()


def ring_dots(r, cx, cy, rx, ry, mat, tone, z=1.0, n=40, skip=None, jitter=0.0, seed=0):
    rnd = random.Random(seed)
    for i in range(n):
        if skip and skip(i): continue
        a = i / n * math.tau
        j = rnd.uniform(-jitter, jitter)
        r.dot(cx + (rx + j) * math.cos(a), cy + (ry + j * 0.5) * math.sin(a), mat, tone, z)


# ------------------------------------------------------------------ the perk: arcs, hits, crackles, sparks
def fx_arc(out):
    """Arc segment, 12 px along x, centred: Crackle (the 0.3 arc), Thin (a Coil Wisp relay arc past 70 px), White (the lit
    route of a Wire Wyvern and a Voltaic Pile's surge), Hot (an arc from a red-hot rod)."""
    def seg(k, mat="storm", core=4, glow=2, amp=1.6):
        r = R()
        bolt(r, (-6, 0), (6, 0), z=1.0, n=3, amp=amp, seed=k * 11 + len(mat), core=core, glow=glow, mat=mat)
        return done(r)
    fx("FxKrnArc", (16, 11), (8, 5), [("Crackle", [seg(k) for k in range(4)], [0.05] * 4),
                                     ("Thin", [seg(k, core=3, glow=None, amp=1.0) for k in range(4)], [0.06] * 4),
                                     ("White", [seg(k, mat="spark", core=4, glow=3, amp=1.2) for k in range(3)], [0.04] * 3),
                                     ("Hot", [seg(k, mat="ember", core=4, glow=2) for k in range(4)], [0.05] * 4)], out)


def fx_hit(out):
    frs = []
    for k in range(5):
        r = R()
        if k == 0:
            r.ell(0, 0, 2.4, 2.4, "storm", 1.0, flat=4)
        n = 6
        for i in range(n):
            a = i / n * math.tau + k * 0.3
            L = 2.0 + k * 1.6
            if k < 4: bolt(r, (math.cos(a) * (L - 2), math.sin(a) * (L - 2) * 0.8), (math.cos(a) * L, math.sin(a) * L * 0.8), z=1.0, n=1, amp=0.5,
                           seed=i + k, core=4 - k // 2, glow=2 if k < 2 else None)
        if k >= 2: spark(r, 0, 0, 2 if k < 4 else 3)
        frs.append(done(r))
    fx("FxKrnHit", (24, 18), (12, 9), [("Play", frs, [0.03, 0.04, 0.05, 0.06, 0.07])], out)


def fx_crackle(out):
    def fr(k, mat):
        r = R()
        crackle(r, -1 + (k % 2), 0, k, seed=4, mat=mat, size=3 - k // 2)
        if k == 0: spark(r, 0, 0, 2, mat=mat)
        return done(r)
    fx("FxKrnCrackle", (12, 12), (6, 6), [("Play", [fr(k, "storm") for k in range(4)], [0.05, 0.05, 0.06, 0.07]),
                                          ("White", [fr(k, "spark") for k in range(4)], [0.05, 0.05, 0.06, 0.07])], out)


def fx_static_spark(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(0, 0, 1.6, 1.6, "storm", 1.0, flat=3); r.dot(0, 0, "storm", 4, 1.1)
        crackle(r, -2, 0, k, seed=2, size=2)
        r.dot(-4 - k % 2, (k % 3) - 1, "storm", 2, 0.5)
        frs.append(done(r))
    fx("FxKrnStaticSpark", (14, 10), (7, 5), [("Fly", frs, [0.05] * 4)], out)


def fx_spark_zap(out):
    frs = []
    for k in range(4):
        r = R()
        bolt(r, (-7, 0), (5, 0), z=1.0, n=3, amp=1.4, seed=k * 3)
        spark(r, 5, 0, 1 if k % 2 == 0 else 2)
        frs.append(done(r))
    fx("FxKrnSpark", (18, 10), (9, 5), [("Fly", frs, [0.04] * 4)], out)


def fx_mote(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(0, 0, 2.6, 2.6, "storm", 1.0, flat=2); r.ell(0, 0, 1.6, 1.6, "storm", 1.1, flat=3); r.dot(-0.5, -0.5, "storm", 4, 1.2)
        for i in range(3):
            a = k * 1.1 + i * 2.1
            r.dot(math.cos(a) * 3.5, math.sin(a) * 3.5, "storm", 3, 1.3)
        r.dot(-4, 0, "storm", 2, 0.5); r.dot(-5.5, 0, "storm", 1, 0.5)
        frs.append(done(r))
    fx("FxKrnMote", (14, 12), (7, 6), [("Fly", frs, [0.05] * 4)], out)


def fx_ball(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(0, 0, 4.0, 4.0, "storm", 1.0, flat=2); r.ell(0, 0, 2.8, 2.8, "storm", 1.1, flat=3); r.ell(-0.6, -0.6, 1.2, 1.2, "storm", 1.2, flat=4)
        for i in range(3):
            a = k * 0.8 + i * 2.1
            bolt(r, (math.cos(a) * 2.5, math.sin(a) * 2.5), (math.cos(a) * 6.0, math.sin(a) * 6.0), z=1.3, n=2, amp=0.8, seed=i + k * 3, glow=None)
        frs.append(done(r))
    fx("FxKrnBall", (16, 16), (8, 8), [("Fly", frs, [0.05] * 4)], out)


def fx_rivet(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(1, 0, 1.6, 1.4, "dkiron", 1.0, bias=0.2)
        r.dot(1, 0, "ember", 4 if k % 2 == 0 else 3, 1.1)
        r.dot(-1.0, 0, "dkiron", 2, 1.0)
        for i in range(3): r.dot(-2 - i * 1.5, (k + i) % 2 - 0.5, "ember", 3 - i, 0.5)
        frs.append(done(r))
    fx("FxKrnRivet", (12, 8), (6, 4), [("Fly", frs, [0.05] * 4)], out)


def fx_stud(out):
    """A rivet stud hammered into the floor: an arc post. Land (3), Idle (2)."""
    def fr(k, glow):
        r = R()
        r.ell(0, -0.8, 2.6, 1.0, "dkiron", 0.5, bias=0.1)
        r.tube([(0, -1.0), (0, -3.0 - (0 if k else 1))], [1.0, 1.0], "iron", 1.0, bias=0.1)
        r.ell(0, -3.4, 1.6, 1.0, "iron", 1.1, bias=0.3)
        r.dot(0, -3.6, "ember" if glow else "storm", 4 if glow > 1 or k % 2 else 3, 1.2)
        if glow > 1: spark(r, 0, -6, 1)
        return done(r)
    fx("FxKrnStud", (12, 10), (6, 8), [("Land", [fr(0, 2), fr(1, 1), fr(1, 0)], [0.05, 0.08, 0.1]),
                                       ("Idle", [fr(1, 0), fr(2, 0)], [0.5, 0.3])], out)


ROD_CELL, ROD_O = (14, 26), (7, 23)


def rod_frame(h=13, hot=0.0, mat="iron", rise=1.0, sp=None, lean=0.0, glow=None, dark=0.0, crumble=0):
    r = R()
    if dark > 0: mat = "dkiron"
    hh = h * rise
    rod(r, 0, 0, hh, 1.0, hot=hot, mat=mat, lean=lean, glow=glow, spark_k=sp)
    if crumble:
        for i in range(crumble * 2): r.dot(-2 + i, -1 - (i % 2), "dkiron", 1, 1.2)
    if rise < 1.0: dust_puff(r, 0, 0, 0, 0.8)
    return done(r)


def fx_rod(out):
    """A lightning rod: Rise (4), Idle (2), Hot (red, cooling to grey over 3 s: 6 frames of 0.5 s)."""
    rise = [rod_frame(rise=t, sp=1 if t > 0.9 else None) for t in (0.3, 0.7, 1.0, 1.0)]
    idle = [rod_frame(), rod_frame(sp=3)]
    hot = [rod_frame(hot=h) for h in (1.0, 0.9, 0.75, 0.55, 0.35, 0.15)]
    fx("FxKrnRod", ROD_CELL, ROD_O, [("Rise", rise, [0.04, 0.05, 0.06, 0.1]), ("Idle", idle, [0.6, 0.15]), ("Hot", hot, [0.5] * 6)], out)


def fx_slag_rod(out):
    rise = [rod_frame(rise=t, mat="dkiron", lean=-1.5, sp=1 if t > 0.9 else None) for t in (0.3, 0.7, 1.0, 1.0)]
    idle = [rod_frame(mat="dkiron", lean=-1.5), rod_frame(mat="dkiron", lean=-1.5, sp=3)]
    fx("FxKrnSlagRod", ROD_CELL, ROD_O, [("Rise", rise, [0.05, 0.06, 0.08, 0.12]), ("Idle", idle, [0.6, 0.15])], out)


def fx_rod_glow(out):
    """Drawn over a rod: its tip glows blue (the Tesla Spire is about to fire from it; a Stormcaller's bolt wants it)."""
    frs = []
    for k in range(4):
        r = R()
        y = -14
        r.ell(0, y, 2.6 + k * 0.4, 2.6 + k * 0.4, "storm", 1.0, flat=2)
        r.ell(0, y, 1.4, 1.4, "storm", 1.1, flat=4 if k % 2 else 3)
        for i in range(2): crackle(r, -2 + i * 4, y + 3 + k, k + i, seed=i)
        frs.append(done(r))
    fx("FxKrnRodGlow", ROD_CELL, ROD_O, [("Play", frs, [0.06, 0.08, 0.08, 0.08])], out)


def fx_rod_dark(out):
    """A rod a Static Moth drank dry: its light drains up, it goes black and slumps."""
    frs = [rod_frame(glow="storm"), rod_frame(sp=2), rod_frame(dark=1.0), rod_frame(dark=1.0, lean=-1.0),
           rod_frame(dark=1.0, lean=-2.5, h=11, crumble=1), rod_frame(dark=1.0, lean=-4.0, h=8, crumble=2)]
    fx("FxKrnRodDark", ROD_CELL, ROD_O, [("Play", frs, [0.08, 0.08, 0.3, 0.3, 0.4, 0.4])], out)


def fx_double_clang(out):
    """The Rivet Imp's Spark Plug: two bolt pips flare at once over its head, with a double clang."""
    frs = []
    for k in range(5):
        r = R()
        for i, x in enumerate((-3, 3)):
            if k < 4: spark(r, x, -4 - (k if k < 2 else 2), 1 if k < 2 else 2)
        if k < 3:
            for side in (-1, 1): r.polyline([(side * 7, -3 - k), (side * (8 + k), -5 - k)], "ember", 2.0, tone=4 - k)
        frs.append(done(r))
    fx("FxKrnDoubleClang", (22, 14), (11, 12), [("Play", frs, [0.05, 0.06, 0.08, 0.1, 0.1])], out)


def fx_ring(out):
    frs = []
    for k in range(6):
        r = R()
        rx = 5 + k * 4.0
        ring_dots(r, 0, 0, rx, rx * 0.4, "storm", 4 if k < 3 else 3, n=36, skip=lambda i: (i + k) % 5 == 0, jitter=0.6, seed=k)
        if k < 4: ring_dots(r, 0, 0, rx - 2, (rx - 2) * 0.4, "storm", 2, n=30, skip=lambda i: i % 3 == 0, seed=k + 9)
        if k == 0: r.ell(0, 0, 3, 1.4, "storm", 1.2, flat=4)
        frs.append(done(r))
    fx("FxKrnRing", (52, 22), (26, 11), [("Play", frs, [0.04, 0.05, 0.06, 0.07, 0.08, 0.1])], out)


def fx_surge(out):
    frs = []
    for k in range(4):
        r = R()
        for i in range(4):
            x = -6 + i * 4
            bolt(r, (x, 0), (x + 2, -3 - (i + k) % 3), z=1.0, n=1, amp=0.6, seed=i + k, glow=None)
        r.polyline([(-8, 0), (7, 0)], "storm", 0.9, tone=3)
        r.dot(7, -1, "storm", 4, 1.1)
        frs.append(done(r))
    fx("FxKrnSurge", (20, 10), (10, 8), [("Fly", frs, [0.05] * 4)], out)


def fx_plates(out):
    """The Anvil Smith's iron plate: it hangs round him (Loop) until a hit breaks it (FxKrnShatter)."""
    frs = []
    for k in range(4):
        r = R()
        for i in range(2):
            a = k / 4.0 * math.pi + i * math.pi
            x, y = 13 * math.cos(a), -12 + 5 * math.sin(a)
            front = math.sin(a) > 0
            r.poly([(x - 2.5, y - 3), (x + 2.5, y - 3), (x + 2.0, y + 3), (x - 2.0, y + 3)], "iron", 1.0 if front else -1.0,
                   normal=(-0.4, -0.4, 0.8), bias=0.1 if front else -0.3)
            r.dot(x, y, "ember", 3, 1.1 if front else -0.9)
        frs.append(done(r))
    fx("FxKrnPlates", (36, 26), (18, 22), [("Loop", frs, [0.1] * 4)], out)


def fx_shatter(out):
    frs = []
    for k in range(5):
        r = R()
        for i in range(6):
            a = i / 6 * math.tau
            d = 4 + k * 3
            x, y = d * math.cos(a), -12 + d * 0.6 * math.sin(a) + k * k * 0.3
            r.poly([(x - 1.2, y - 1), (x + 1.2, y - 1.4), (x + 0.8, y + 1)], "iron", 1.0, bias=0.2)
        if k < 2: spark(r, 0, -12, 1, mat="ember")
        frs.append(done(r))
    fx("FxKrnShatter", (40, 30), (20, 24), [("Play", frs, [0.04, 0.05, 0.06, 0.08, 0.1])], out)


# ------------------------------------------------------------------ Wire Gremlin
def fx_staple(out):
    frs = []
    for k in range(4):
        r = R()
        r.polyline([(-2, -1), (2, -1)], "brass", 1.0, tone=4); r.dot(-2, 0, "brass", 2, 1.0); r.dot(2, 0, "brass", 2, 1.0)
        r.dot(3, -1, "ember", 3 if k % 2 else 4, 1.1)
        for i in range(2): r.dot(-4 - i * 2, -1 + (k + i) % 2, "brass", 2 - i, 0.5)
        frs.append(done(r))
    fx("FxKrnStaple", (12, 6), (6, 3), [("Fly", frs, [0.05] * 4)], out)


def fx_hook(out):
    frs = []
    for k in range(4):
        r = R()
        r.polyline([(-6, 0), (-3, (k % 2) - 0.5), (0, 0)], "copper", 1.0, tones=[2, 3])
        r.polyline([(0, 0), (2, -1), (3, 0), (2, 2)], "brass", 1.1, tone=4)
        if k % 2: spark(r, 3, -2, 3)
        frs.append(done(r))
    fx("FxKrnHook", (14, 8), (7, 4), [("Fly", frs, [0.05] * 4)], out)


def fx_wired(out):
    """On a wired hero (Conductor): copper wire coiled round the body, sparks snapping off it. Cell bottom = feet."""
    frs = []
    for k in range(4):
        r = R()
        for i in range(30):
            t = i / 30.0
            a = t * 3 * math.tau + k * 0.8
            x, y = 5.5 * math.cos(a), -3 - t * 12 + 1.5 * math.sin(a)
            front = math.sin(a) > 0
            r.dot(x, y, "copper", 3 if front else 1, 1.0 if front else -1.0)
        crackle(r, 5 * math.cos(k * 1.7), -8 - k * 2, k, seed=1)
        if k % 2: spark(r, -5, -12 + k, 3)
        frs.append(done(r))
    fx("FxKrnWired", (18, 20), (9, 19), [("Loop", frs, [0.08] * 4)], out)


# ------------------------------------------------------------------ Lodestone Hound / Polarity Warg
def fx_magfield(out):
    """Magnet Howl round the hound: Pull (red lines curling inward), Push (blue lines pushing out)."""
    def fr(k, inward):
        r = R()
        mat = "magred" if inward else "magblu"
        for j in range(3):
            t = (k / 5.0 + j / 3.0) % 1.0
            d = (1.0 - t) if inward else t
            rx = 6 + d * 18
            ring_dots(r, 0, -4, rx, rx * 0.45, mat, 4 if d < 0.5 else 3, n=28, skip=lambda i: i % 3 == (0 if inward else 1), seed=j)
            for i in range(6):
                a = i / 6 * math.tau + (0.3 if inward else -0.3) * d
                x, y = rx * math.cos(a), -4 + rx * 0.45 * math.sin(a)
                ax = -1 if inward else 1
                r.dot(x + ax * math.cos(a) * 1.5, y + ax * math.sin(a) * 0.8, mat, 4, 1.2)
        return done(r)
    fx("FxKrnMagField", (54, 28), (27, 17), [("Pull", [fr(k, True) for k in range(6)], [0.06] * 6),
                                             ("Push", [fr(k, False) for k in range(6)], [0.06] * 6)], out)


def fx_lode_arc(out):
    """Polarity Warg's field line (12 px segment): red and blue beads that drift toward the iron."""
    def seg(k):
        r = R()
        for i in range(4):
            x = -6 + ((i * 3 + k) % 12)
            r.dot(x, math.sin(x * 0.7) * 0.6, "magred" if i % 2 else "magblu", 4 if i % 2 else 3, 1.0)
        return done(r)
    fx("FxKrnLodeArc", (14, 7), (7, 3), [("Crackle", [seg(k) for k in range(4)], [0.06] * 4)], out)


def fx_ind_magnet(out):
    frs = []
    for k in range(2):
        r = R()
        r.tube([(-3, -1), (-3, -5), (0, -7), (3, -5), (3, -1)], [1.0], "magred", 1.0, thin=True)
        r.dot(-3, -1, "iron", 4, 1.1); r.dot(3, -1, "iron", 4, 1.1)
        if k: spark(r, 0, -9, 3)
        frs.append(done(r))
    fx("FxKrnIndMagnet", (12, 11), (6, 10), [("Loop", frs, [0.25, 0.25])], out)


def fx_clamp(out):
    """Iron Grip: the hero clamps to the iron in a burst of red and blue sparks."""
    frs = []
    for k in range(6):
        r = R()
        for i in range(8):
            a = i / 8 * math.tau + k * 0.4
            d = 3 + k * 1.6 if k < 3 else 8 - (k - 3) * 1.5
            r.dot(d * math.cos(a), -8 + d * 0.8 * math.sin(a), "magred" if i % 2 else "magblu", 4 if k < 4 else 3, 1.0)
        if k < 3: spark(r, 0, -8, 1)
        frs.append(done(r))
    fx("FxKrnClamp", (26, 24), (13, 20), [("Play", frs, [0.04, 0.05, 0.06, 0.1, 0.12, 0.14])], out)


def fx_polar_ring(out):
    frs = []
    for k in range(5):
        r = R()
        rx = 6 + k * 6
        ring_dots(r, 0, 0, rx, rx * 0.45, "magred", 4, n=30, skip=lambda i: i % 2 == 0, seed=k)
        ring_dots(r, 0, 0, rx + 1, (rx + 1) * 0.45, "magblu", 4, n=30, skip=lambda i: i % 2 == 1, seed=k)
        frs.append(done(r))
    fx("FxKrnPolarRing", (66, 34), (33, 17), [("Play", frs, [0.05, 0.06, 0.07, 0.08, 0.1])], out)


# ------------------------------------------------------------------ Stormcaller
def fx_hair(out):
    """Static Build, over the hero's head: hair on end, crackling (shown for 1.5 s before the bolt)."""
    frs = []
    for k in range(4):
        r = R()
        for i in range(5):
            x = -4 + i * 2
            h = 3 + (i + k) % 3
            r.polyline([(x, 0), (x + (i - 2) * 0.4, -h)], "spark", 1.0, tone=3 if (i + k) % 2 else 4)
        crackle(r, -5 + k * 3, -6, k, seed=2)
        frs.append(done(r))
    fx("FxKrnHair", (16, 12), (8, 11), [("Loop", frs, [0.06] * 4)], out)


def strike_frames(rad=8, mark_frames=6, bolt_h=56, seed=0):
    frs = []
    for k in range(mark_frames):
        r = R()
        t = (k + 1) / mark_frames
        ring_dots(r, 0, 0, rad * (1.6 - 0.6 * t), rad * 0.45 * (1.6 - 0.6 * t), "storm", 3 if k % 2 else 4, n=24,
                  skip=lambda i: i % 2 == k % 2, seed=k)
        r.ell(0, 0, rad * 0.5 * t, rad * 0.22 * t, "storm", 1.0, flat=2)
        if k >= mark_frames - 2:
            for i in range(3): r.dot((i - 1) * 3, -bolt_h + i * 2, "steam", 2, 0.5)
        frs.append(done(r))
    for k in range(4):
        r = R()
        if k < 3:
            bolt(r, (1, -bolt_h), (0, 0), z=2.0, n=8, amp=2.6 - k * 0.6, seed=seed + k, fork=2 - k, core=4 if k < 2 else 3)
            r.ell(0, 0, rad - k, (rad - k) * 0.45, "storm", 1.0, flat=4 if k == 0 else 3)
            if k == 0: spark(r, 0, -2, 1)
        else:
            ring_dots(r, 0, 0, rad + 2, (rad + 2) * 0.45, "storm", 2, n=20, skip=lambda i: i % 2 == 0)
            dust_puff(r, 0, 0, 1, 1.4)
        frs.append(done(r))
    return frs


def fx_strike(out):
    """A struck bolt: 0.6 s of ground mark (frames 0-5), then the bolt (6-8, damage) and its scorch (9). Static Build."""
    frs = strike_frames(rad=11, mark_frames=6, bolt_h=56, seed=1)
    fx("FxKrnStrike", (40, 70), (20, 61), [("Play", frs, [0.1] * 6 + [0.05, 0.06, 0.06, 0.14])], out)


def fx_storm_bolt(out):
    """Eye of the Storm: one strike (16 px), a short mark (frames 0-2), the bolt (3-5, damage), then scorch."""
    frs = strike_frames(rad=8, mark_frames=3, bolt_h=50, seed=4)
    fx("FxKrnStormBolt", (32, 62), (16, 55), [("Play", frs, [0.08, 0.08, 0.08, 0.05, 0.06, 0.06, 0.12])], out)


def fx_storm_band(out):
    """Eye of the Storm: a ring of storm-cloud shadow on the floor marking the strike band (60-110 px round the Herald,
    the floor drawn at half depth). Loop (crawling)."""
    frs = []
    for k in range(3):
        r = R()
        for rad, n in ((60, 46), (110, 80)):
            for i in range(n):
                if (i + k) % 3 == 0: continue
                a = i / n * math.tau
                # a dark dash with a lit edge above it: it reads on dark and bright floors
                x, y = rad * math.cos(a), rad * 0.5 * math.sin(a)
                r.dot(x, y, "dkiron", 0, 1.0); r.dot(x + 1, y, "dkiron", 0, 1.0)
                r.dot(x, y - 1, "storm", 3 if rad < 100 else 2, 1.0)
        rnd = random.Random(k)
        for i in range(26):
            a = rnd.uniform(0, math.tau); d = rnd.uniform(66, 104)
            r.dot(d * math.cos(a), d * 0.5 * math.sin(a), "dkiron", 1, 0.9)
            if i % 4 == k: r.dot(d * math.cos(a) + 1, d * 0.5 * math.sin(a), "storm", 3, 0.95)
        frs.append(done(r))
    fx("FxKrnStormBand", (226, 116), (113, 58), [("Loop", frs, [0.15] * 3)], out, scale=2)


def fx_lance(out):
    frs = []
    for k in range(4):
        r = R()
        bolt(r, (-12, 0), (10, 0), z=1.0, n=6, amp=1.2, seed=k * 2, fork=1)
        for side in (-1, 1): r.polyline([(10, 0), (13, side * 1.5)], "storm", 1.1, tone=4)
        frs.append(done(r))
    fx("FxKrnLance", (30, 10), (15, 5), [("Fly", frs, [0.04] * 4)], out)


# ------------------------------------------------------------------ Leyden Golem / Arc Lantern
def fx_jolt(out):
    frs = []
    for k in range(4):
        r = R()
        bolt(r, (-5, 0), (4, 0), z=1.0, n=3, amp=1.0, seed=k + 5)
        r.ell(4, 0, 1.4, 1.4, "storm", 1.1, flat=4)
        frs.append(done(r))
    fx("FxKrnJolt", (14, 8), (7, 4), [("Fly", frs, [0.04] * 4)], out)


def fx_seeker(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(1, 0, 2.4, 2.0, "storm", 1.0, flat=2); r.ell(1, 0, 1.4, 1.2, "storm", 1.1, flat=4)
        for i in range(4): r.dot(-2 - i * 1.4, math.sin(k + i) * 1.0, "storm", 3 - i // 2, 0.5)
        frs.append(done(r))
    fx("FxKrnSeeker", (14, 10), (7, 5), [("Fly", frs, [0.05] * 4)], out)


def fx_hanging_wisp(out):
    """Hanging Sparks: a missed wisp that stops in the air and hangs 3 s as an arc post (Hang, loop), then Fade."""
    def fr(k, fade=0):
        r = R()
        s = 1.0 - fade * 0.3
        r.ell(0, 0, 3.0 * s, 3.0 * s, "storm", 1.0, flat=2 if fade < 2 else 1)
        r.ell(0, 0, 1.6 * s, 1.6 * s, "storm", 1.1, flat=4 if (k % 2 == 0 and fade == 0) else 3)
        if fade == 0:
            for i in range(3):
                a = k * 1.4 + i * 2.1
                r.dot(4 * math.cos(a), 4 * math.sin(a), "storm", 3, 1.2)
        for i in range(2): r.dot(-1 + i * 2, 7 + (k % 2), "storm", 1, 0.5)
        return done(r)
    fx("FxKrnHangingWisp", (14, 18), (7, 7), [("Hang", [fr(k) for k in range(4)], [0.08] * 4), ("Fade", [fr(0, f) for f in (1, 2, 3)], [0.08] * 3)], out)


def fx_field(out):
    frs = []
    for k in range(12):
        r = R()
        t = min(1.0, k / 2.0) if k < 10 else (12 - k) / 2.0
        rx = 22 * t
        ring_dots(r, 0, 0, rx, rx * 0.36, "storm", 3, n=36, skip=lambda i: (i + k) % 4 == 0, seed=k)
        rnd = random.Random(k)
        for i in range(int(10 * t)):
            a = rnd.uniform(0, math.tau); d = rnd.uniform(0, rx * 0.9)
            crackle(r, d * math.cos(a), d * 0.36 * math.sin(a) - 1, k + i, seed=i, size=1)
        frs.append(done(r))
    fx("FxKrnField", (52, 22), (26, 11), [("Play", frs, [0.08] * 12)], out)


# ------------------------------------------------------------------ Forge Colossus / Forgemaster
def fx_quake(out):
    frs = []
    for k in range(6):
        r = R()
        rx = 8 + k * 3.4
        ring_dots(r, 0, 0, rx, rx * 0.4, "iron", 3 if k < 3 else 2, n=34, skip=lambda i: (i + k) % 4 == 0, jitter=1.0, seed=k)
        for i in range(5):
            a = i / 5 * math.tau + 0.4
            d0, d1 = 2, rx * 0.8
            r.polyline([(d0 * math.cos(a), d0 * 0.4 * math.sin(a)), (d1 * math.cos(a), d1 * 0.4 * math.sin(a))], "dkiron", 0.5, tone=0)
        if k < 2: spark(r, 0, -3, 1, mat="ember")
        if k < 4: dust_puff(r, 0, 0, min(2, k), 2.0)
        frs.append(done(r))
    fx("FxKrnQuake", (62, 26), (31, 15), [("Play", frs, [0.04, 0.05, 0.06, 0.08, 0.1, 0.12])], out)


def fx_steam(out):
    """The Forge Colossus venting: a blast of steam 30 px round its feet."""
    frs = []
    for k in range(6):
        r = R()
        rx = 8 + k * 5
        rnd = random.Random(k)
        for i in range(22):
            a = i / 22 * math.tau + rnd.uniform(-0.1, 0.1)
            x, y = rx * math.cos(a), rx * 0.42 * math.sin(a) - 2 - k * 0.6
            rr = 2.6 - k * 0.3
            if k < 5: r.ell(x, y, rr, rr * 0.8, "steam", 1.0 + i * 0.001, flat=3 if k < 2 else 2)
        if k < 3:
            for i in range(6): r.ell(rnd.uniform(-6, 6), -4 - rnd.uniform(0, 10), 2.0, 1.6, "steam", 2.0, flat=4 - k)
        frs.append(done(r))
    fx("FxKrnSteam", (76, 40), (38, 26), [("Play", frs, [0.04, 0.05, 0.06, 0.08, 0.1, 0.12])], out)


def fx_thrown_rod(out):
    frs = []
    for k in range(4):
        r = R()
        a = math.radians(k * 45)
        ca, sa = math.cos(a), math.sin(a)
        r.tube([(-6 * ca, -6 * sa), (6 * ca, 6 * sa)], [0.8, 0.7], "iron", 1.0, bias=0.15, thin=True)
        r.ell(6 * ca, 6 * sa, 1.1, 1.1, "copper", 1.1, thin=True)
        r.dot(1.0 * ca, 1.0 * sa, "brass", 4, 1.2)
        frs.append(done(r))
    fx("FxKrnThrownRod", (18, 18), (9, 9), [("Fly", frs, [0.05] * 4)], out)


def fx_rod_land(out):
    frs = []
    for k in range(4):
        r = R()
        ring_dots(r, 0, 0, 4 + k * 3, (4 + k * 3) * 0.4, "iron", 3, n=20, skip=lambda i: (i + k) % 3 == 0)
        if k < 2: spark(r, 0, -3, 1)
        dust_puff(r, 0, 0, min(2, k), 1.4)
        frs.append(done(r))
    fx("FxKrnRodLand", (32, 18), (16, 12), [("Play", frs, [0.04, 0.05, 0.07, 0.1])], out)


# ------------------------------------------------------------------ Wire Wyvern
def fx_breath(out):
    """The Wire Wyvern's lightning breath: a piercing beam 2..60 px out of the mouth."""
    frs = []
    for k in range(4):
        r = R()
        bolt(r, (0, 0), (60, (k % 2) - 0.5), z=1.0, n=12, amp=2.0 - k * 0.3, seed=k * 5, fork=3, core=4 if k < 3 else 3)
        if k < 2: r.ell(1, 0, 2.0, 2.0, "storm", 1.1, flat=4)
        frs.append(done(r))
    fx("FxKrnBreath", (64, 14), (2, 7), [("Play", frs, [0.06, 0.08, 0.1, 0.12])], out)


def fx_ride(out):
    """Ride the Arc: the streak of light racing along the arcs (Fly, loop) and the flash where it dives in or bursts out."""
    streak = []
    for k in range(4):
        r = R()
        r.ell(4, 0, 3.0, 2.2, "spark", 1.0, flat=3); r.ell(4, 0, 1.6, 1.2, "spark", 1.1, flat=4)
        for i in range(6): r.dot(1 - i * 1.6, ((i + k) % 3) - 1, "storm", 4 if i < 2 else 3, 0.8)
        bolt(r, (-8, 0), (4, 0), z=0.7, n=3, amp=1.0, seed=k)
        streak.append(done(r))
    flash = []
    for k in range(5):
        r = R()
        h = 26 - k * 4
        if k < 4:
            bolt(r, (0, 0), (0, -h), z=1.0, n=5, amp=1.6, seed=k, fork=1)
            r.ell(0, 0, 6 - k, 2.4 - k * 0.4, "spark", 1.1, flat=4 - k // 2)
        ring_dots(r, 0, 0, 4 + k * 3, (4 + k * 3) * 0.4, "storm", 3, n=20, skip=lambda i: (i + k) % 3 == 0)
        flash.append(done(r))
    fx("FxKrnRideStreak", (22, 10), (11, 5), [("Fly", streak, [0.04] * 4)], out)
    fx("FxKrnRideFlash", (40, 40), (20, 33), [("Play", flash, [0.04, 0.05, 0.06, 0.08, 0.1])], out)


# ------------------------------------------------------------------ Fuse Sapper
def fx_canister(out):
    frs = []
    for k in range(4):
        r = R()
        a = math.radians(k * 90)
        r.tube([(-2 * math.cos(a), -6 - 2 * math.sin(a)), (2 * math.cos(a), -6 + 2 * math.sin(a))], [1.8, 1.8], "copper", 1.0, bias=0.1)
        r.dot(2 * math.cos(a), -6 + 2 * math.sin(a), "magred", 3, 1.1)
        r.dot(2.5 * math.cos(a), -6 + 3 * math.sin(a), "ember", 4, 1.2)
        frs.append(done(r))
    fx("FxKrnCanister", (12, 12), (6, 10), [("Fly", frs, [0.06] * 4)], out)


def blast(k, rad, mat_core="ember", bolts=True):
    r = R()
    if k == 0:
        r.ell(0, -2, rad * 0.4, rad * 0.3, "fire", 1.0, flat=4)
    if k < 4:
        rr = rad * (0.4 + 0.2 * k)
        if k < 2: r.ell(0, -2 - k, rr * 0.8, rr * 0.5, "ember", 1.0, flat=3)
        else:
            for i in range(7): r.ell(-rr * 0.6 + i * rr * 0.2, -3 - k - (i % 2) * 2, 1.8, 1.4, "smoke", 1.0 + i * 0.01, flat=2)
        ring_dots(r, 0, 0, rr, rr * 0.42, "fire" if k < 2 else "smoke", 3, n=26, skip=lambda i: (i + k) % 3 == 0)
        if bolts and k < 3:
            for i in range(4):
                a = i / 4 * math.tau + k
                bolt(r, (0, -3), (rr * math.cos(a), -3 + rr * 0.5 * math.sin(a)), z=1.5, n=2, amp=1.0, seed=i + k, glow=None)
    else:
        for i in range(5): r.ell(-rad * 0.4 + i * rad * 0.2, -4 - i % 2 * 2, 2.0, 1.6, "smoke", 1.0, flat=1)
    return done(r)


def fx_canburst(out):
    fx("FxKrnCanBurst", (48, 30), (24, 19), [("Play", [blast(k, 18) for k in range(6)], [0.04, 0.05, 0.06, 0.08, 0.1, 0.12])], out)


def fx_charge(out):
    """A Fuse Sapper charge on the floor: Idle (a slow red blink), Blink (fast: a Kaurn node is near), Live (an arc has
    reached it: it blows in 0.4 s), Fizzle (it never was reached: a dud after 8 s)."""
    def fr(on, live=False, dud=0):
        r = R()
        r.ell(0, -0.6, 2.8, 1.0, "dkiron", 0.5)
        r.tube([(0, -1.0), (0, -4.0)], [2.0, 2.0], "copper", 1.0, bias=0.1)
        r.ell(0, -4.6, 2.0, 0.9, "magred" if not dud else "dkiron", 1.1, bias=0.2)
        if on: r.dot(0, -5.6, "ember", 4, 1.2); r.dot(1, -5.6, "ember", 3, 1.2)
        if live:
            spark(r, 0, -7, 1)
            crackle(r, -3, -5, on, seed=3)
        if dud: r.dot(dud - 1, -6 - dud, "smoke", 2, 1.3)
        return done(r)
    fx("FxKrnCharge", (14, 14), (7, 11), [("Idle", [fr(1), fr(0)], [0.2, 0.6]), ("Blink", [fr(1), fr(0)], [0.08, 0.08]),
                                         ("Live", [fr(1, True), fr(2, True), fr(3, True)], [0.05, 0.05, 0.05]),
                                         ("Fizzle", [fr(0, dud=1), fr(0, dud=2), fr(0, dud=3)], [0.15, 0.15, 0.2])], out)


def fx_charge_blast(out):
    fx("FxKrnChargeBlast", (44, 30), (22, 20), [("Play", [blast(k, 20) for k in range(6)], [0.04, 0.05, 0.06, 0.08, 0.1, 0.12])], out)


# ------------------------------------------------------------------ Scarab Magus / Storm Orrery / Voltaic Pile / Tesla Spire / Static Moth
def fx_split_orb(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(0, 0, 3.4, 3.4, "scarab", 1.0, bias=0.2)
        r.ell(0, 0, 2.0, 2.0, "storm", 1.1, flat=3)
        for i in range(3):
            a = k * 0.9 + i * 2.1
            r.dot(4 * math.cos(a), 4 * math.sin(a), "gold", 4, 1.2)
        frs.append(done(r))
    fx("FxKrnSplitOrb", (14, 14), (7, 7), [("Fly", frs, [0.05] * 4)], out)


def fx_shard(out):
    frs = []
    for k in range(4):
        r = R()
        r.poly([(-3, -1), (3, 0), (-3, 1)], "scarab", 1.0, bias=0.3)
        r.dot(2, 0, "storm", 4, 1.1)
        r.dot(-5, (k % 2) - 0.5, "storm", 2, 0.5)
        frs.append(done(r))
    fx("FxKrnShard", (12, 6), (6, 3), [("Fly", frs, [0.05] * 4)], out)


def fx_kindle_orb(out):
    """Kindle: a slow ball of lightning drifting across the floor (an arc end). Loop."""
    frs = []
    for k in range(4):
        r = R()
        shadow(r, 0, 9, 2.5)
        r.ell(0, 0, 4.0, 4.0, "storm", 1.0, flat=2); r.ell(0, 0, 2.6, 2.6, "spark", 1.1, flat=3); r.dot(-0.5, -0.5, "spark", 4, 1.2)
        for i in range(4):
            a = k * 0.7 + i * math.pi / 2
            bolt(r, (2.5 * math.cos(a), 2.5 * math.sin(a)), (6.0 * math.cos(a), 6.0 * math.sin(a)), z=1.3, n=2, amp=0.7, seed=i + k, glow=None)
        frs.append(done(r))
    fx("FxKrnKindleOrb", (16, 22), (8, 9), [("Fly", frs, [0.06] * 4)], out)


def fx_orb(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(0, 0, 2.6, 2.6, "storm", 1.0, flat=3); r.dot(-0.5, -0.5, "storm", 4, 1.1)
        for i in range(20):
            a = i / 20 * math.tau
            x, y = 5.5 * math.cos(a), 2.0 * math.sin(a)
            xx, yy = x * math.cos(0.5 + k * 0.2) - y * math.sin(0.5 + k * 0.2), x * math.sin(0.5 + k * 0.2) + y * math.cos(0.5 + k * 0.2)
            r.dot(xx, yy, "brass", 3 if math.sin(a) > 0 else 1, 1.2 if math.sin(a) > 0 else 0.5)
        frs.append(done(r))
    fx("FxKrnOrb", (16, 16), (8, 8), [("Fly", frs, [0.05] * 4)], out)


def fx_planet_line(out):
    """Alignment: the planet line on the floor (Dots, 12 px segment) and the beam that fires along it (Beam)."""
    def dots(k):
        r = R()
        for x in range(-6, 6, 3): r.dot(x + k, 0, "storm", 4 if (x + k) % 6 == 0 else 2, 1.0)
        return done(r)
    def beam(k):
        r = R()
        bolt(r, (-6, 0), (6, 0), z=1.0, n=3, amp=0.6 + k * 0.3, seed=k, core=4, glow=3 - k)
        if k < 2:
            r.polyline([(-6, -2), (6, -2)], "storm", 0.9, tone=2); r.polyline([(-6, 2), (6, 2)], "storm", 0.9, tone=2)
        return done(r)
    fx("FxKrnPlanetLine", (16, 9), (8, 4), [("Dots", [dots(k) for k in range(3)], [0.08] * 3), ("Beam", [beam(k) for k in range(3)], [0.06, 0.08, 0.1])], out)


def fx_planet(out):
    anims = []
    for name, mat in zip(("Red", "Green", "Violet"), PLANETS):
        frs = []
        for k in range(2):
            r = R()
            r.ell(0, 0, 2.6, 2.6, mat, 1.0, bias=0.2 + 0.25 * k)
            frs.append(done(r))
        anims.append((name, frs, [0.2, 0.1]))
    fx("FxKrnPlanet", (10, 10), (5, 5), anims, out)


def fx_whip(out):
    frs = []
    for k in range(4):
        r = R()
        pts = [(0, 0), (12, -2 + k), (24, -1 + k * 0.5), (38, 1)]
        for i in range(len(pts) - 1):
            bolt(r, pts[i], pts[i + 1], z=1.0, n=3, amp=1.2, seed=i + k * 3, core=4 if k < 2 else 3, glow=2 if k < 3 else None)
        if k < 2: spark(r, 38, 1, 1)
        frs.append(done(r))
    fx("FxKrnWhip", (44, 14), (2, 7), [("Play", frs, [0.04, 0.05, 0.06, 0.08])], out)


def fx_bead(out):
    """Pulse: the bright bead that runs out along a Voltaic Pile's arcs (Loop), and the pile's tick (Tick)."""
    bead = []
    for k in range(2):
        r = R()
        r.ell(0, 0, 2.6, 2.6, "brine" if False else "storm", 1.0, flat=3); r.ell(0, 0, 1.4, 1.4, "spark", 1.1, flat=4)
        r.dot(-3 - k, 0, "storm", 2, 0.5)
        bead.append(done(r))
    tick = []
    for k in range(4):
        r = R()
        if k < 3:
            for side in (-1, 1): r.polyline([(side * (2 + k), -k), (side * (4 + k), -2 - k)], "spark", 1.0, tone=4 - k)
        spark(r, 0, -3, 1 if k < 2 else 2)
        tick.append(done(r))
    fx("FxKrnBead", (10, 10), (5, 5), [("Loop", bead, [0.06, 0.06])], out)
    fx("FxKrnPileTick", (16, 12), (8, 9), [("Play", tick, [0.05, 0.06, 0.08, 0.1])], out)


def fx_relay(out):
    frs = []
    for k in range(4):
        r = R()
        bolt(r, (-6, 0), (5, 0), z=1.0, n=3, amp=1.2, seed=k * 3, mat="violetg")
        r.ell(5, 0, 1.6, 1.6, "storm", 1.1, flat=4)
        frs.append(done(r))
    flash = []
    for k in range(4):
        r = R()
        r.ell(0, 0, 4 - k, 4 - k, "violetg", 1.0, flat=3 if k < 2 else 2)
        for i in range(5):
            a = i / 5 * math.tau + k
            r.dot((5 + k) * math.cos(a), (5 + k) * math.sin(a), "storm", 4 - k // 2, 1.1)
        flash.append(done(r))
    fx("FxKrnRelay", (14, 8), (7, 4), [("Fly", frs, [0.04] * 4)], out)
    fx("FxKrnRelayFlash", (22, 22), (11, 11), [("Play", flash, [0.04, 0.05, 0.06, 0.08])], out)


def fx_dart(out):
    frs = []
    for k in range(4):
        r = R()
        r.poly([(-3, -1.5), (3, 0), (-3, 1.5), (-1.5, 0)], "mwing", 1.0, bias=0.3)
        r.dot(1, 0, "storm", 4, 1.1)
        r.dot(-5, (k % 2) * 2 - 1, "copper", 2, 0.5)
        frs.append(done(r))
    fx("FxKrnDart", (12, 8), (6, 4), [("Fly", frs, [0.05] * 4)], out)


def fx_drain(out):
    """Drink the Rods: the rod's light climbs off it toward the moth in a column of motes."""
    frs = []
    for k in range(6):
        r = R()
        for i in range(6):
            y = -2 - ((i * 4 + k * 3) % 22)
            r.dot((i % 2) * 2 - 1, y, "storm", 4 if i % 2 else 3, 1.0)
        if k < 3: r.ell(0, -13, 2.4, 2.4, "storm", 0.9, flat=2)
        frs.append(done(r))
    fx("FxKrnDrain", (12, 28), (6, 25), [("Play", frs, [0.06] * 6)], out)


def fx_sparkfall(out):
    """Spark Fall: a spark shed from the moth's wings drifts down 0.6 s (its shadow growing on the floor), then pops (hit)."""
    frs = []
    for k in range(7):
        r = R()
        t = min(1.0, k / 5.0)
        y = -30 + 30 * t
        if k < 6:
            spark(r, (k % 2) - 0.5, y, 2 if k < 5 else 1, mat="spark")
            shadow(r, 0, 0, 0.6 + 2.0 * t, mat="dkiron")
        else:
            ring_dots(r, 0, 0, 5, 2.2, "spark", 4, n=14)
            spark(r, 0, -2, 1, mat="spark")
        frs.append(done(r))
    fx("FxKrnSparkFall", (16, 36), (8, 33), [("Play", frs, [0.1] * 6 + [0.08])], out)


# ------------------------------------------------------------------ the god: portrait and the gold idol
def fx_deity(out):
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    frs = frames("kaurn", (0, 24))
    fx("DeityKaurn", (29, 24), (0, 24), [("Idle", frs, [0.3, 0.12, 0.3, 0.12])], out, scale=8)


def idol_frame(k, shine=None, glint=None):
    """The gold idol of the Storm Forge: an anvil on a stepped plinth, a fork of lightning rising off it into a three-point
    crown, two little hammers crossed at its waist. Gold all over, copper-brown in the hollows, one blue-white spark."""
    r = R()
    W, H = 29, 24
    for y in range(-H, 0):
        for x in range(0, W):
            edge = x in (0, W - 1) or y in (-H, -1)
            r.put(x, y, -5.0, "apron", 0.5, 1, 1 if edge else 0)
    # plinth: two steps
    r.poly([(5, -3), (24, -3), (24, -1), (5, -1)], "gold", 1.0, normal=(-0.1, -0.2, 1.0))
    r.polyline([(5, -3), (24, -3)], "gold", 1.01, tone=4)
    r.poly([(7, -5), (22, -5), (22, -3), (7, -3)], "gold", 1.05, normal=(-0.1, -0.2, 1.0))
    r.polyline([(7, -5), (22, -5)], "gold", 1.06, tone=4)
    # the anvil: a lit top face, a shadowed front, a horn to the left, a waist and a flared foot
    r.poly([(9, -6), (20, -6), (21, -5), (8, -5)], "gold", 1.1, normal=(-0.2, -0.4, 0.9))
    r.poly([(11, -10), (18, -10), (18, -6), (11, -6)], "gold", 1.12, normal=(0.1, 0.3, 1.0))
    r.poly([(5, -13), (24, -13), (24, -10), (5, -10)], "gold", 1.15, normal=(0.0, 0.2, 1.0))
    r.polyline([(5, -13), (24, -13)], "gold", 1.16, tone=4)
    r.poly([(5, -13), (1, -12), (5, -11)], "gold", 1.15, normal=(-0.6, -0.5, 0.7))
    r.polyline([(11, -9), (11, -6)], "copper", 1.17, tone=1); r.polyline([(18, -9), (18, -6)], "copper", 1.17, tone=1)
    r.polyline([(5, -10), (24, -10)], "copper", 1.17, tone=1)
    # two hammers crossed behind the fork, their heads either side of it
    for side in (-1, 1):
        hx_, hy_ = 15 + side * 8.5, -15.5
        r.polyline([(15 - side * 4, -11), (hx_, hy_)], "copper", 1.3, tone=2)
        r.polyline([(15 - side * 4, -10), (hx_, hy_ + 1)], "copper", 1.29, tone=1)
        r.poly([(hx_ - 2.5, hy_ - 2.5), (hx_ + 2.5, hy_ - 2.5), (hx_ + 2.5, hy_ + 0.5), (hx_ - 2.5, hy_ + 0.5)], "gold", 1.35,
               normal=(-0.3, -0.6, 0.75))
        r.polyline([(hx_ - 2.5, hy_ + 1.0), (hx_ + 2.5, hy_ + 1.0)], "copper", 1.36, tone=1)
        r.dot(hx_ - 2, hy_ - 2.5, "gold", 4, 1.37)
    # the fork of lightning rising off the anvil into a three-point crown
    pts = [(14, -13), (16, -15), (13, -16), (15, -18)]
    for i in range(len(pts) - 1):
        r.polyline([pts[i], pts[i + 1]], "gold", 1.4, tone=3)
        r.polyline([(pts[i][0] + 1, pts[i][1]), (pts[i + 1][0] + 1, pts[i + 1][1])], "copper", 1.39, tone=2)
    r.poly([(10, -19), (20, -19), (19, -18), (11, -18)], "gold", 1.42, normal=(0.0, -0.4, 0.9))
    for i, (bx, tx, ty) in enumerate(((11, 10, -21), (15, 15, -23), (19, 20, -21))):
        r.polyline([(bx, -19), (tx, ty)], "gold", 1.45, tone=4 if i == 1 else 3)
        r.dot(tx, ty, "gold", 4, 1.46)
    r.dot(15, -23, "storm", 4 if glint is None or glint else 3, 1.6)
    if glint: spark(r, 15, -22, 2)
    res = r.resolve(floor=False, selout=True, cast=False, contour=False)
    if shine is not None:
        for (x, y), c in list(res.px.items()):
            m, t = res.tones[(x, y)]
            if m == "gold" and abs((x + y) - shine) <= 1:
                res.px[(x, y)] = (255, 248, 210)
    return res


def fx_idol(out):
    frs = [idol_frame(0, shine=s) for s in (-22, -16, -10, -4, 2)] + [idol_frame(0, glint=True), idol_frame(1, glint=False), idol_frame(0)]
    fx("DeityGoldIdolKaurn", (29, 24), (0, 24), [("Idle", frs, [0.06, 0.06, 0.06, 0.06, 0.06, 0.22, 0.2, 0.5])], out, scale=8)


JOBS = [("FxKrnArc", fx_arc), ("FxKrnHit", fx_hit), ("FxKrnCrackle", fx_crackle), ("FxKrnStaticSpark", fx_static_spark),
        ("FxKrnSpark", fx_spark_zap), ("FxKrnMote", fx_mote), ("FxKrnBall", fx_ball), ("FxKrnRivet", fx_rivet), ("FxKrnStud", fx_stud),
        ("FxKrnRod", fx_rod), ("FxKrnSlagRod", fx_slag_rod), ("FxKrnRodGlow", fx_rod_glow), ("FxKrnRodDark", fx_rod_dark),
        ("FxKrnDoubleClang", fx_double_clang), ("FxKrnRing", fx_ring), ("FxKrnSurge", fx_surge), ("FxKrnPlates", fx_plates),
        ("FxKrnShatter", fx_shatter), ("FxKrnStaple", fx_staple), ("FxKrnHook", fx_hook), ("FxKrnWired", fx_wired),
        ("FxKrnMagField", fx_magfield), ("FxKrnLodeArc", fx_lode_arc), ("FxKrnIndMagnet", fx_ind_magnet), ("FxKrnClamp", fx_clamp),
        ("FxKrnPolarRing", fx_polar_ring), ("FxKrnHair", fx_hair), ("FxKrnStrike", fx_strike), ("FxKrnStormBolt", fx_storm_bolt),
        ("FxKrnStormBand", fx_storm_band), ("FxKrnLance", fx_lance), ("FxKrnJolt", fx_jolt), ("FxKrnSeeker", fx_seeker),
        ("FxKrnHangingWisp", fx_hanging_wisp), ("FxKrnField", fx_field), ("FxKrnQuake", fx_quake), ("FxKrnSteam", fx_steam),
        ("FxKrnThrownRod", fx_thrown_rod), ("FxKrnRodLand", fx_rod_land), ("FxKrnBreath", fx_breath), ("FxKrnRide", fx_ride),
        ("FxKrnCanister", fx_canister), ("FxKrnCanBurst", fx_canburst), ("FxKrnCharge", fx_charge), ("FxKrnChargeBlast", fx_charge_blast),
        ("FxKrnSplitOrb", fx_split_orb), ("FxKrnShard", fx_shard), ("FxKrnKindleOrb", fx_kindle_orb), ("FxKrnOrb", fx_orb),
        ("FxKrnPlanetLine", fx_planet_line), ("FxKrnPlanet", fx_planet), ("FxKrnWhip", fx_whip), ("FxKrnBead", fx_bead),
        ("FxKrnRelay", fx_relay), ("FxKrnDart", fx_dart), ("FxKrnDrain", fx_drain), ("FxKrnSparkFall", fx_sparkfall),
        ("DeityKaurn", fx_deity), ("DeityGoldIdolKaurn", fx_idol)]
