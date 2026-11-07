"""Sylvene effect sheets and the gold idol, drawn with the same material renderer as the monsters. Sheets the code already
used keep their cell, origin and anim names (so templates built on them still line up); the new ones carry the v2
mechanics (fast seeds, grafted pods, thorn patches, the dragged bush, pollen dust, furrow vines, the drone ring, gas
lanes, ...). Coordinates below are pixels from each sheet's origin, y up negative."""
import math, os, random
from sylvene_v2_rigs import (Rig, Xf, chain, lerp, star, arc_smear, dust_puff, pack, preview, BUILT, RAMPS, EMISSIVE, SprRGB, vine, thorn,
                             leaf, pod, motes, puff, soil, wing, cap)


def done(r):
    return r.resolve(floor=False, cast=False, contour=False)


def fx(name, cell, origin, anims, outdir, scale=8):
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-22s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def blank():
    return SprRGB({})


# ================================================================== seeds and pods
def seed_frame(stage, fast=False, shake=0, pulse=0):
    """stage 0 (a seed just landed, popping) .. 1 (sprouting) .. 2 (a husk swelling) .. 3 (a ripe pod)."""
    r = Rig()
    husk = "gall" if not fast else "pollen"
    if stage < 0.5:
        k = stage * 2
        r.ell(0.0, -1.2, 1.4, 1.2, husk, 0.0, bias=0.2)
        if fast: r.line(-1, -1, 1, -1, "chitin", 0.1, tone=1)
        if stage == 0: soil(r, 0.0, 0.0, 0, 0.6)
        if k > 0.4:
            r.line(0, -2, 0, -2 - int(2 * k), "moss", 0.2, tone=3)
            leaf(r, 0, -2 - 2 * k, -40, 1.5 + k, 0.3)
    elif stage < 2.5:
        k = (stage - 0.5) / 2.0
        s = 3.0 + 3.0 * k
        pod(r, shake * 0.5, 0.0, s, 0.0, ripe=k, husk="rot")
        if fast:
            for y in range(int(-s), 0, 2):
                r.dot(shake * 0.5 - 1 + (y % 4 == 0), y, "pollen", 3, 0.2)
        leaf(r, -1, -1, -160, 2.5, 0.1); leaf(r, 1, -1, -20, 2.5, 0.1)
    else:
        s = 6.4 + 0.5 * pulse
        pod(r, shake, 0.0, s, 0.0, ripe=1.0, husk="rot", split=1.0)
        if fast:
            for y in (-5, -3):
                r.line(shake - 2, y, shake + 2, y, "pollen", 0.2, tone=3)
        leaf(r, -2, -1, -170, 3.0, 0.1); leaf(r, 2, -1, -10, 3.0, 0.1)
        if pulse: r.dot(shake - 1, -5, "podf", 4, 0.3)
    return done(r)


def pod_burst(k, w=1.0, mat="sporec", seed=4):
    r = Rig()
    if k == 0:
        pod(r, 0, 0, 7.0, 0.0, ripe=1.0, split=1.0)
        r.dot(0, -8, "podf", 4, 1)
    else:
        puff(r, 0, -4 - k * 0.6, (4.0 + k * 1.8) * w, 0.0, mat, max(0, k - 2), seed=seed, n=6)
        for i in range(4 + k):
            a = i / (4 + k) * math.tau
            r.dot(math.cos(a) * (5 + k * 2.4) * w, -3 + math.sin(a) * (2 + k * 0.8), "podf" if i % 2 else "gall", max(1, 4 - k // 2), 2)
    return done(r)


def fx_seeds(out):
    life = [seed_frame(s) for s in (0, 0.25, 0.4, 0.6, 0.9, 1.2, 1.5, 1.8, 2.1, 2.4)]
    ripe = [seed_frame(3, pulse=0), seed_frame(3, pulse=1)]
    burst = [pod_burst(k, 0.55) for k in range(5)]
    shake = [seed_frame(3, shake=-1), seed_frame(3, shake=1)]
    fx("FxSeed", (20, 18), (10, 16), [("Life", life, [0.25] * 10), ("Ripe", ripe, [0.25, 0.25]), ("Burst", burst, [0.06, 0.08, 0.09, 0.1, 0.1]),
                                      ("Shake", shake, [0.05, 0.05])], out)
    flife = [seed_frame(s, fast=True) for s in (0, 0.3, 0.7, 1.2, 1.8, 2.4)]
    fx("FxSylSeedFast", (20, 18), (10, 16), [("Life", flife, [0.25] * 6), ("Ripe", [seed_frame(3, True), seed_frame(3, True, pulse=1)], [0.25, 0.25]),
                                             ("Burst", burst, [0.06, 0.08, 0.09, 0.1, 0.1]),
                                             ("Shake", [seed_frame(3, True, shake=-1), seed_frame(3, True, shake=1)], [0.05, 0.05])], out)
    big = [pod_burst(k, 0.74, seed=7) for k in range(7)]
    fx("FxSylPodBurst", (44, 20), (21, 16), [("Play", big, [0.05, 0.08, 0.08, 0.1, 0.1, 0.12, 0.12])], out)


def cloud(k, rad, mat="sporec", seed=2, n=5):
    r = Rig()
    puff(r, 0, 0, rad * (0.7 + 0.12 * k), 0.0, mat, max(0, k - 2), seed=seed, n=n)
    return done(r)


def fx_clouds(out):
    fx("FxSporeCloud", (20, 17), (10, 8), [("Play", [cloud(k, 6.0, seed=k + 1) for k in range(6)], [0.08, 0.1, 0.11, 0.11, 0.12, 0.12])], out)
    fx("FxSylSproutPuff", (16, 13), (8, 6), [("Play", [cloud(k, 4.4, seed=k + 3) for k in range(6)], [0.08, 0.1, 0.11, 0.11, 0.12, 0.12])], out)
    fx("FxSylRotCloud", (22, 18), (11, 9), [("Play", [cloud(k, 6.6, "gas", seed=k + 5) for k in range(6)], [0.08, 0.1, 0.12, 0.14, 0.16, 0.16])], out)


# ================================================================== projectiles
def glob(k, mat="bile", s=2.2, trail=4, tmat="bilef"):
    r = Rig()
    r.ell(2, 0, s, s * 0.85, mat, 1.0, bias=0.25)
    r.dot(1.5, -1, mat, 4, 1.1)
    for i in range(trail):
        r.dot(-1 - i * 1.5, (k + i) % 2 - 0.5, tmat, max(1, 3 - i), 0.5)
    return done(r)


def needle(k, ln=10, mat="thorn", tip="blood", tr="pollen"):
    r = Rig()
    r.line(-ln // 2, 0, ln // 2, 0, mat, 1, tone=3)
    r.dot(ln // 2 + 1, 0, tip, 3, 1.1)
    r.dot(-ln // 2, -1, "gall", 3, 1)
    for i in range(3):
        r.dot(-ln // 2 - 2 - i * 2, (k + i) % 2, tr, max(1, 3 - i), 0.5)
    return done(r)


def lance_fr(k):
    r = Rig()
    for i in range(16):
        r.dot(-8 + i, 0, "pollc", 4 if i > 12 else 3 if i > 6 else 2, 1)
    for i in range(3):
        r.dot(-6 + i * 5 + k, -1 + (i + k) % 3, "pollc", 4, 1.1)
    r.dot(8, 0, "white", 4, 1.2)
    return done(r)


def dart(k):
    r = Rig()
    r.ell(2, 0, 2.2, 1.6, "pollc", 1, flat=3); r.dot(3, 0, "pollc", 4, 1.1)
    for i in range(4):
        r.dot(-1 - i * 1.6, (k + i) % 3 - 1, "pollc", max(1, 3 - i), 0.5)
    return done(r)


def lasso_fr(k):
    r = Rig()
    for i in range(14):
        a = i / 14 * math.tau + k * 0.8
        r.dot(2 + 3.4 * math.cos(a), 2.2 * math.sin(a), "moss", 3 if math.sin(a) < 0 else 2, 1)
    r.polyline([(-9, 0), (-4, -1 + k % 2), (-1, 0)], "moss", 1, tone=3)
    thorn(r, 5, -2, -60, 1.5, 1.1)
    return done(r)


def pod_spin(k):
    r = Rig()
    T = Xf(k * 90, (0, 0))
    r.ell(0, 0, 3.0, 3.2, "podf", 1, bias=0.2)
    for side in (-1, 1):
        r.dot(*T(side * 2.6, 1.6), "rot", 2, 1.1)
    r.dot(*T(0, -3.2), "rot", 3, 1.1)
    for i in range(3):
        r.dot(-4 - i * 1.6, (k + i) % 2, "podf", max(1, 3 - i), 0.5)
    return done(r)


def berry(k, s=2.4):
    r = Rig()
    r.ell(1, 0, s, s, "berry", 1, bias=0.3)
    r.dot(0, -s + 0.5, "berry", 4, 1.1)
    r.dot(1, -s - 0.5, "rot", 3, 1.1)
    for i in range(3):
        r.dot(-s - 1 - i * 1.4, (k + i) % 2, "bell", max(1, 3 - i), 0.5)
    return done(r)


def berry_pop(k):
    r = Rig()
    for i in range(6):
        a = i / 6 * math.tau
        d = 2 + k * 2
        r.dot(math.cos(a) * d, -6 + math.sin(a) * d * 0.7, "bell" if i % 2 else "berry", max(1, 4 - k), 1)
    if k < 2: r.ell(0, -6, 2.4 - k, 2.0 - k, "berry", 1.2, bias=0.3)
    return done(r)


def spine_fr(k):
    r = Rig()
    r.line(-7, 0, 6, 0, "cordy", 1, tone=3)
    r.dot(7, 0, "cordy", 4, 1.1); r.dot(-7, -1, "cordy", 2, 1)
    for i in range(3):
        r.dot(-9 - i * 2, (k + i) % 2, "cordy", max(1, 2 - i // 2), 0.5)
    return done(r)


def thorn_spin(k):
    r = Rig()
    a = k * 45
    thorn(r, -3 * math.cos(math.radians(a)), -3 * math.sin(math.radians(a)), a, 6, 1, mat="thorn", tip="blood")
    return done(r)


def seed_shot(k):
    r = Rig()
    r.ell(2, 0, 1.8, 1.3, "gall", 1, bias=0.2); r.dot(3, -1, "gall", 4, 1.1)
    r.line(-1, 0, -4, 0, "irid", 0.5, tone=3)
    r.dot(-5 - k % 2, 0, "irid", 2, 0.5)
    return done(r)


def fx_projectiles(out):
    fx("FxPoisonGlob", (20, 10), (10, 5), [("Fly", [glob(k) for k in range(4)], [0.07] * 4)], out)
    fx("FxGallNeedle", (30, 10), (15, 5), [("Fly", [needle(k) for k in range(3)], [0.07] * 3)], out)
    fx("FxPollen", (30, 11), (15, 5), [("Fly", [lance_fr(k) for k in range(4)], [0.05] * 4)], out)
    fx("FxPollenDart", (24, 12), (12, 6), [("Fly", [dart(k) for k in range(4)], [0.06] * 4)], out)
    fx("FxSylLasso", (22, 12), (11, 6), [("Fly", [lasso_fr(k) for k in range(4)], [0.05] * 4)], out)
    fx("FxSylPodSling", (14, 14), (7, 7), [("Fly", [pod_spin(k) for k in range(4)], [0.06] * 4)], out)
    fx("FxSylBileDrop", (18, 9), (9, 4), [("Fly", [glob(k, s=1.8, trail=3) for k in range(4)], [0.06] * 4)], out)
    fx("FxSylSpine", (30, 9), (15, 4), [("Fly", [spine_fr(k) for k in range(3)], [0.06] * 3)], out)
    fx("FxSylBerry", (20, 12), (10, 6), [("Fly", [berry(k) for k in range(4)], [0.06] * 4)], out)
    fx("FxSylBerrySmall", (18, 9), (9, 4), [("Fly", [berry(k, 1.6) for k in range(4)], [0.06] * 4)], out)
    fx("FxSylBerryPop", (20, 14), (10, 12), [("Play", [berry_pop(k) for k in range(4)], [0.06, 0.07, 0.08, 0.08])], out)
    fx("FxSylThorn", (14, 14), (7, 7), [("Fly", [thorn_spin(k) for k in range(4)], [0.05] * 4)], out)
    fx("FxSylSeedShot", (14, 8), (7, 4), [("Fly", [seed_shot(k) for k in range(4)], [0.05] * 4)], out)


# ================================================================== roots, thorns, sweeps
def roots(k, n, spread, h=1.0):
    r = Rig()
    for i in range(n):
        x = -spread + i * 2 * spread / max(1, n - 1)
        hh = [0, 4, 7, 6, 3, 1, 0][min(6, k)] * h * (0.7 + 0.3 * ((i * 7) % 3) / 2)
        if hh <= 0:
            r.dot(x, 0, "bark", 1, 0); continue
        r.tube([(x, 0), (x + 0.6 * (1 if i % 2 else -1), -hh * 0.6), (x + 1.2 * (1 if i % 2 else -1), -hh)], [1.2, 0.9, 0.5], "bark", i * 0.01)
        if hh > 3: r.dot(x + 1.2 * (1 if i % 2 else -1), -hh - 1, "moss", 3, 0.5)
    if k < 3: soil(r, 0, 0, k, spread / 6.0)
    return done(r)


def thorn_knot(k, life=True, rise=1.0):
    r = Rig()
    for i in range(5):
        x = -6 + i * 3
        h = (4.0 + (i % 2) * 2.5) * rise
        a = -90 + (i - 2) * 22 + (math.sin(k + i) * 6 if life else 0)
        thorn(r, x, 0, a, h, i * 0.01, mat="thorn", tip="blood")
    vine(r, [(-7, -1), (-2, -2), (3, -1), (7, -2)], [0.9], 0.0, mat="bark", thorns=0)
    return done(r)


def sweep(kind, k):
    """Thorn-vine arcs round the origin: Slash across the front, Upslash up from the floor."""
    r = Rig()
    if kind == "Slash":
        a0, a1, R = -125, -5, 15
    else:
        a0, a1, R = 80, -10, 13
    span = [0.4, 1.0, 1.0, 0.7][k]
    end = lerp(a0, a1, span)
    start = lerp(a0, end, [0.0, 0.2, 0.55, 0.8][k])
    n = 14
    for i in range(n + 1):
        t = i / n
        a = math.radians(lerp(start, end, t))
        # a thick band of vine thinning behind the lead: pale thorn edge, lit moss, shadowed moss
        width = 4 if t > 0.55 else 3 if t > 0.25 else 2
        for w in range(width):
            m, tone = (("thorn", 3 + (t > 0.7)), ("moss", 3), ("moss", 2), ("moss", 1))[w]
            r.dot((R - w) * math.cos(a), (R - w) * math.sin(a), m, tone, 1 + 0.01 * (4 - w))
        if i % 3 == 1: thorn(r, (R + 1) * math.cos(a), (R + 1) * math.sin(a), math.degrees(a) + 15, 2.2, 1.1)
    return done(r)


def tusk_hook(k):
    r = Rig()
    span = [0.4, 1.0, 1.0, 0.6][k]
    for i in range(12):
        t = i / 11 * span
        a = math.radians(lerp(100, -60, t))
        for w in range(3):
            r.dot(10 * math.cos(a) + 6, -2 + (10 - w) * math.sin(a), "tusk" if w < 2 else "bark", 2 + (t > 0.5) - (w > 1), 1)
    if k == 1: star(r, 10, -10, 2)
    return done(r)


def fx_roots(out):
    fx("FxRootLine", (30, 13), (15, 11), [("Play", [roots(k, 5, 9) for k in range(7)], [0.08] * 7 + [])], out)
    fx("FxSylRootErupt", (36, 15), (18, 13), [("Play", [roots(k, 7, 13, 1.3) for k in range(7)], [0.3, 0.25, 0.2, 0.08, 0.1, 0.15, 0.2][:7])], out)
    rise = [thorn_knot(0, rise=0.3), thorn_knot(0, rise=0.7), thorn_knot(1, rise=1.1)]
    lifef = [thorn_knot(k) for k in range(4)]
    wither = [thorn_knot(0, life=False, rise=0.6), thorn_knot(0, life=False, rise=0.3)]
    fx("FxSylThornPatch", (22, 12), (11, 10), [("Rise", rise, [0.05, 0.05, 0.08]), ("Life", lifef, [0.25] * 4), ("Wither", wither, [0.1, 0.1])], out)
    fx("FxSylThornSweep", (36, 42), (9, 21), [("Slash", [sweep("Slash", k) for k in range(4)], [0.06, 0.12, 0.12, 0.12]),
                                              ("Upslash", [sweep("Upslash", k) for k in range(4)], [0.06, 0.12, 0.12, 0.12])], out)
    fx("FxSylTuskHook", (36, 34), (9, 19), [("Play", [tusk_hook(k) for k in range(4)], [0.06, 0.12, 0.12, 0.12])], out)


# ================================================================== rings, grounds and lingering clouds
def ground_ring(k, rx, ry, mat, n=40, thick=1, z=1):
    r = Rig()
    for i in range(n):
        a = i / n * math.tau
        if (i * 7 + k) % 9 == 0: continue
        for w in range(thick):
            r.dot((rx - w) * math.cos(a), (ry - w * 0.4) * math.sin(a), mat, max(1, 4 - k // 2 - w), z)
    return done(r)


def spore_ring(k, R=11, mat="sporec"):
    r = Rig()
    rx = 4 + k * (R - 4) / 5
    for i in range(10):
        a = i / 10 * math.tau
        puff(r, rx * math.cos(a), -2 + rx * 0.35 * math.sin(a), 2.2 - 0.2 * k, i * 0.01, mat, min(3, k // 2), seed=i, n=3)
    return done(r)


def fx_rings(out):
    fx("FxSylPuffRing", (36, 14), (18, 12), [("Play", [spore_ring(k) for k in range(6)], [0.06, 0.08, 0.09, 0.1, 0.1, 0.12])], out)
    fx("FxSylShakeRing", (40, 16), (20, 8), [("Play", [ground_ring(k, 6 + k * 4, 2 + k * 1.4, "glowg") for k in range(4)], [0.06, 0.07, 0.08, 0.1])], out, scale=6)
    # the drone: a ring of sound rolling out to r 50 (rx 50, ry 25: it lies flat on the floor)
    fr = []
    for k in range(6):
        rx = 8 + k * 8.4
        fr.append(ground_ring(k, rx, rx * 0.5, "ring", n=60, thick=2))
    fx("FxSylDroneRing", (108, 56), (54, 28), [("Play", fr, [0.07] * 6)], out, scale=4)
    # bile: splash, puddle (bubbling), and the spoiled marker at the hero's feet
    sp = []
    for k in range(4):
        r = Rig()
        for i in range(8):
            a = i / 8 * math.pi
            d = 2 + k * 2.5
            r.dot(-math.cos(a) * d * 1.4, -math.sin(a) * d * 0.8 - (1 if k < 2 else 0), "bilef", max(1, 4 - k), 1)
        r.ell(0, -0.5, 3 + k, 1.2, "bilef", 0.5, flat=max(1, 3 - k))
        sp.append(done(r))
    fx("FxSylBileSplash", (26, 14), (13, 10), [("Play", sp, [0.05, 0.06, 0.08, 0.1])], out)
    pud = []
    for k in range(6):
        r = Rig()
        w = [3, 6, 8, 8, 8, 8][k]
        r.ell(0, -1, w, 2.4, "bilef", 0, flat=2)
        r.ell(-1, -1.4, w * 0.6, 1.2, "bilef", 0.1, flat=3)
        if k >= 2:
            for i, (x, ph) in enumerate(((-4, 0), (3, 1), (0, 2))):
                if (k + ph) % 3 == 0: r.dot(x, -2.5, "bilef", 4, 0.3)
                elif (k + ph) % 3 == 1: r.ell(x, -2.0, 0.8, 0.8, "bilef", 0.3, flat=3)
        pud.append(done(r))
    fx("FxSylBilePuddle", (24, 10), (12, 7), [("Rise", pud[:2], [0.08, 0.08]), ("Life", pud[2:], [0.15] * 4)], out)
    sv = []
    for k in range(4):
        r = Rig()
        for i, x in enumerate((-5, -2, 2, 5)):
            if (k + i) % 2 == 0: r.dot(x, -1 - (k + i) % 3, "bilef", 4 - (k + i) % 2, 1)
            else: r.dot(x, -2, "glowg", 3, 1)
        sv.append(done(r))
    fx("FxSylSpoiled", (16, 8), (8, 6), [("Loop", sv, [0.12] * 4)], out)
    # pollen storm: a wide cloud rolling forward; the dust overlay on a dusted hero
    st = []
    for k in range(8):
        r = Rig()
        for i in range(7):
            x = -18 + i * 6 + k * 0.6
            puff(r, x, -6 - (i % 2) * 3, 3.6 + 0.3 * (i % 3), i * 0.01, "pollc", min(3, max(0, k - 4)), seed=i + k, n=4)
        st.append(done(r))
    fx("FxSylPollenCloud", (56, 22), (28, 18), [("Play", st, [0.08, 0.1, 0.12, 0.14, 0.16, 0.18, 0.2, 0.2])], out, scale=5)
    du = []
    for k in range(4):
        r = Rig()
        rnd = random.Random(k)
        for i in range(9):
            r.dot(rnd.randint(-5, 5), -rnd.randint(1, 14), "pollc", 3 + (i + k) % 2, 1)
        du.append(done(r))
    fx("FxSylDust", (14, 16), (7, 15), [("Loop", du, [0.1] * 4)], out)
    # gas: puffs that linger, lane tiles, the bladder and its burst (Stale Air: thick and slow-curling)
    gp = [cloud(k, 4.8, "gas", seed=11 + k, n=6) for k in range(6)]
    fx("FxSylGasPuff", (24, 18), (12, 12), [("Play", gp[:2], [0.08, 0.1]), ("Life", gp[2:], [0.3] * 4)], out)
    tl = [cloud(k % 3 + (1 if k > 2 else 0), 5.0, "gas", seed=21 + k, n=5) for k in range(6)]
    fx("FxSylGasTile", (16, 14), (8, 9), [("Rise", tl[:2], [0.06, 0.08]), ("Life", tl[2:], [0.3] * 4)], out)
    bl = []
    for k in range(4):
        r = Rig()
        h = [0, 3, 4, 2][k]
        r.ell(0, -3 - h, 3.0 - (0.4 if k == 0 else 0), 2.6 + (0.4 if k == 0 else 0), "bile", 1, bias=0.2)
        r.dot(-1, -5 - h, "bile", 4, 1.1); r.line(-1, -6 - h, 1, -6 - h, "lthr", 1.2, tone=2)
        r.ell(0, 0, 2.0, 0.6, "chitin", 0, flat=1)
        bl.append(done(r))
    fx("FxSylBladder", (14, 14), (7, 12), [("Hop", bl, [0.08] * 4)], out)
    bb = [pod_burst(k, 0.7, "gas", seed=13) for k in range(1, 7)]
    fx("FxSylBladderBurst", (36, 20), (18, 16), [("Play", bb, [0.06, 0.08, 0.1, 0.1, 0.12, 0.14])], out)


# ================================================================== markers and indicators
def fx_markers(out):
    # Tend: green motes drifting down from the Sporeling's cap to a seed
    tm = []
    for k in range(6):
        r = Rig()
        for i in range(4):
            y = -12 + ((k * 2 + i * 3) % 12)
            r.dot((i - 1.5) * 2 + math.sin(k + i), y, "glowg", 4 if y > -4 else 3, 1)
        tm.append(done(r))
    fx("FxSylTendMote", (10, 14), (5, 13), [("Play", tm, [0.08] * 6)], out)
    # the grafted pod riding on a monster's head (over-head indicator)
    gp = []
    for k in range(4):
        r = Rig()
        pod(r, 0, 0, 6.0 + [0, 0.4, 0.8, 0.4][k], 0, ripe=1.0, split=1.0)
        r.dot(-1, -6 - (k % 2), "podf", 4, 1)
        gp.append(done(r))
    fx("FxSylGraftPod", (12, 11), (6, 10), [("Loop", gp, [0.15] * 4)], out)
    # cordyceps stalks on the infected (over-head indicator)
    sk = []
    for k in range(4):
        r = Rig()
        for i, a in enumerate((-120, -90, -60)):
            pts = chain(-2 + i * 2, 0, [(3.0 + (k + i) % 2, a + 6 * math.sin(k + i))])
            r.tube(pts, [0.7, 0.5], "cordy", i * 0.01)
            r.ell(pts[-1][0], pts[-1][1], 0.9, 1.1, "cordy", 0.1 + i * 0.01, bias=0.4)
        sk.append(done(r))
    fx("FxSylStalk", (12, 8), (6, 7), [("Loop", sk, [0.15] * 4)], out)
    # the orchard's green wisp flying to the Rot Mother
    ws = []
    for k in range(4):
        r = Rig()
        r.ell(0, -4, 1.6, 1.6, "glowg", 1, flat=4)
        for i in range(3):
            r.dot(-2 - i * 1.5, -4 + ((k + i) % 3 - 1), "glowg", 3 - i, 0.5)
        ws.append(done(r))
    fx("FxSylHuskWisp", (12, 9), (6, 8), [("Fly", ws, [0.06] * 4)], out)
    # Nightshade's shimmer over a hidden pod
    sh = []
    for k in range(4):
        r = Rig()
        for i in range(5):
            x = -4 + i * 2
            if (i + k) % 3 == 0: r.dot(x, -2 - (i % 2) * 2, "glowp", 3, 1)
            elif (i + k) % 3 == 1: r.dot(x, -1 - (i % 2), "glowp", 2, 1)
        sh.append(done(r))
    fx("FxSylShimmer", (12, 7), (6, 5), [("Loop", sh, [0.14] * 4)], out)
    # the Sower's furrow: a thin vine segment along +x (rotated to join the row)
    fv = []
    for k in range(3):
        r = Rig()
        n = [3, 8, 12][k]
        for i in range(n):
            r.dot(-6 + i, (1 if i % 5 == 2 else 0), "moss", 3 if i % 2 else 2, 1)
        if k == 2:
            leaf(r, -1, 0, -60, 2.0, 1.1); leaf(r, 4, 0, -120, 2.0, 1.1)
        fv.append(done(r))
    fx("FxSylFurrowVine", (14, 6), (7, 3), [("Grow", fv, [0.06, 0.06, 0.06]), ("Loop", [fv[2]], [0.3])], out)
    # the Champion's lance being trimmed back
    lt = []
    for k in range(4):
        r = Rig()
        for i in range(3):
            r.dot(-2 + i * 2 + (i - 1) * k, -6 + k * 2 + i, "moss" if i % 2 else "thorn", max(1, 4 - k), 1)
        lt.append(done(r))
    fx("FxSylLanceTrim", (14, 14), (7, 11), [("Play", lt, [0.06, 0.08, 0.08, 0.1])], out)
    # the Sprout's soil burst (its spawner) and the Rot Mother's sprouting hit
    sb = []
    for k in range(5):
        r = Rig()
        soil(r, 0, 0, min(2, k), 1.4)
        if k < 3: r.ell(0, -1, 4 - k, 1.6, "bark", 0, flat=1)
        if 1 <= k <= 3: leaf(r, 0, -1, -90 + (k - 2) * 20, 2 + k, 0.5)
        sb.append(done(r))
    fx("FxSylSproutBurst", (22, 14), (11, 12), [("Play", sb, [0.08, 0.08, 0.1, 0.1, 0.1])], out)


# ================================================================== the dragged bush
def bush(k, taut=0, spin=None):
    r = Rig()
    ang = 0 if spin is None else spin
    T = Xf(ang, (0, -6))
    for i, (x, y, s) in enumerate(((-4, -6, 4.6), (2, -7, 4.2), (-1, -10, 4.0), (4, -4, 3.4), (-5, -3, 3.2))):
        px, py = T(x, y + (k % 2) * 0.3)
        r.ell(px, py, s, s * 0.85, "moss" if i % 2 else "rot", i * 0.01, bias=0.1)
    for i in range(8):
        a = i / 8 * math.tau + k * 0.2
        thorn(r, *T(7 * math.cos(a), -6 + 6 * math.sin(a)), math.degrees(a) + ang, 2.0, 0.2)
    # the vine to the Behemoth: along +x, slack or taut
    if spin is None:
        if taut:
            r.line(6, -6, 15, -8, "moss", 0.3, tone=4)
        else:
            r.polyline([(6, -6), (10, -4 + (k % 2)), (15, -7)], "moss", 0.3, tone=3)
    return done(r)


def bush_swing(k):
    """The bush sweeping a wide arc behind the Behemoth (origin = the Behemoth's feet)."""
    r = Rig()
    a = math.radians(lerp(110, 250, k / 4.0))
    cx, cy = 20 * math.cos(a), -6 + 9 * math.sin(a)
    for i in range(5):
        t = math.radians(lerp(110, 250, max(0.0, k / 4.0 - i * 0.07)))
        r.dot(20 * math.cos(t), -6 + 9 * math.sin(t), "moss", max(1, 3 - i // 2), 0.5)
    for i, (x, y, s) in enumerate(((-2, 0, 4.4), (2, -1, 4.0), (0, -4, 3.6))):
        r.ell(cx + x, cy + y, s, s * 0.85, "moss" if i % 2 else "rot", 1 + i * 0.01, bias=0.1)
    for i in range(6):
        b = i / 6 * math.tau
        thorn(r, cx + 6 * math.cos(b), cy - 2 + 5 * math.sin(b), math.degrees(b), 1.8, 1.2)
    return done(r)


def fx_bush(out):
    drag = [bush(k) for k in range(4)]
    taut = [bush(0, taut=1), bush(1, taut=1)]
    fx("FxSylBush", (36, 26), (13, 22), [("Drag", drag, [0.12] * 4), ("Taut", taut, [0.08, 0.08])], out, scale=6)
    fx("FxSylBushSwing", (56, 36), (28, 22), [("Play", [bush_swing(k) for k in range(5)], [0.05, 0.05, 0.05, 0.06, 0.08])], out, scale=5)


# ================================================================== the god's portrait and the gold idol
def idol(stage, glint=0):
    """A gold orchard mother shaped like a gourd: split open on pink seeds, gold vines over the shoulders, a bud head.
    stage 0 the closed pod, 1 splitting, 2 open with the bud in flower and a ring of gold thorns at the base."""
    r = Rig()
    cy = -9.0
    r.ell(0, cy, 7.0, 7.6, "gold", 0.0, bias=0.05)
    r.ell(0, cy - 8.4, 3.0, 2.4, "gold", 0.2, bias=0.1)
    # the split down the front: darkest gold, pink seeds inside
    w = [0.4, 1.6, 3.0][stage]
    if stage:
        r.poly([(0, cy - 6.0), (w, cy - 2.0), (w * 0.9, cy + 3.0), (0, cy + 6.0), (-w * 0.9, cy + 3.0), (-w, cy - 2.0)], "gold", 0.1, flat=0)
        for i, (x, y) in enumerate(((0, -3), (-1, 0), (1, 1), (0, 3), (-1, -2), (1, -1))[:2 + stage * 2]):
            r.ell(x * w * 0.5, cy + y, 0.9, 0.9, "podf", 0.2 + i * 0.01, bias=0.3)
    else:
        r.line(0, cy - 6, 0, cy + 6, "gold", 0.1, tone=0)
    # gold vines winding up from the base over the shoulders
    for side in (-1, 1):
        pts = [(side * 6.0, 0.0), (side * 7.6, cy + 2.0), (side * 5.0, cy - 5.0), (side * 2.6, cy - 7.4)]
        r.tube(pts, [0.9, 0.8, 0.7, 0.6], "gold", 0.4, bias=0.1)
        leaf(r, side * 7.5, cy + 1.0, -90 + side * 60, 2.6, 0.45, mat="gold", w=1.0)
    # the bud head, in flower at stage 2
    if stage == 2:
        for a in (-150, -110, -70, -30):
            leaf(r, 0, cy - 9.4, a, 3.6, 0.5, mat="gold", w=1.4)
        r.dot(0, cy - 11, "podf", 4, 0.6)
        for x in range(-7, 8, 2):
            thorn(r, x, 0, -90 + x * 4, 2.0, 0.6, mat="gold", tip="gold")
    else:
        r.poly([(-1.6, cy - 9.0), (0, cy - 13.0 + stage), (1.6, cy - 9.0)], "gold", 0.3, normal=(-0.4, -0.5, 0.8))
    if glint:
        star(r, -3 + glint, cy - 5, 2)
    return r.resolve()


def fx_idol(out):
    frames = [idol(0), idol(0, glint=1), idol(1), idol(1), idol(2), idol(2, glint=2), idol(1), idol(0)]
    lock = [idol(0)]
    fx("DeityGoldIdolSylvene", (29, 24), (14, 22), [("Idle", frames, [0.5, 0.3, 0.3, 0.2, 0.6, 0.3, 0.2, 0.3]), ("Locked", lock, [0.3])], out, scale=8)


# ------------------------------------------------------------------ the god portrait: the Rot Orchard
RAMPS.setdefault("bloom", [tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for c in ("5a1a3a", "a83a6a", "e86aa0", "ffa8cc", "fff4f8")])
EMISSIVE.add("bloom")     # the portrait's blossom eyes: a pink glow with a white core


def fx_deity(out):
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    fx("DeitySylvene", (29, 24), (14, 23), [("Idle", frames("sylvene", (14, 23)), [0.3, 0.25, 0.3, 0.25])], out)


JOBS = [("FxSeed", fx_seeds), ("FxSporeCloud", fx_clouds), ("FxPoisonGlob", fx_projectiles), ("FxRootLine", fx_roots),
        ("FxSylPuffRing", fx_rings), ("FxSylTendMote", fx_markers), ("FxSylBush", fx_bush), ("DeityGoldIdolSylvene", fx_idol),
        ("DeitySylvene", fx_deity)]

SYNC = {}
NOTES = {
    "FxSeed": "Life lasts 2.5 s (the ripening), then Ripe loops; FxSylSeedFast is the Gall Wasp's striped seed (Life 1.5 s). Shake is "
              "the Spore Husk's tell (pods shake for a beat before they burst).",
    "FxSylDroneRing": "Rolls out to rx 50 / ry 25 in 0.42 s; the code dazes a hero the ring's edge crosses.",
    "FxSylBush": "Drag/Taut: the vine runs along +x to the Behemoth (the code turns the bush to face it); FxSylBushSwing sweeps the arc "
                 "behind the Behemoth (origin at its feet).",
    "DeityGoldIdolSylvene": "The gold idol's portrait: the pod opens and closes once per loop (closed, splitting, open in flower).",
}
