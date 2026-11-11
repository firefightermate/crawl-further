"""Bel'Mora effect sheets and portraits, drawn with the same material renderer as the monsters (belmora_v2_rigs.py).
Sheets the code (or the boss and items) already used keep their cell, origin and anim names, so the templates built
on them still line up; the new ones carry the v2 mechanics (the cast bell, the anchor chain, the grapple, crawling
starfish arms, tide eggs, riptide lanes, trailing tentacles, the slime coat, anemone buds, the ringside bell, the kelp
hand). Coordinates are pixels from each sheet's origin, y up negative; projectiles fly to the right."""
import math, random
from belmora_v2_rigs import (Rig, Xf, lerp, eye, spines, foam_ring, drips, bubbles, barnacles, claw, fin, kelp_strand,
                             bell_shape, dust, splash, star, fx, done, pack, preview, BUILT, legend)
from belmora_v2_t2 import anchor, chain_links, sucker
from belmora_v2_t3 import tentacle, curl
from belmora_v2_t3b import anemone


def R():
    return Rig()


def ring(r, cx, cy, rx, ry, mat, tone, z, n=40, gap=None, step=1):
    for i in range(0, n, step):
        a = i / n * math.tau
        if gap and gap(a): continue
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), mat, tone, z)


def ripples(r, cx, cy, rx, ry, k, z=0.0, mat="foam"):
    """Concentric broken rings on water: k grows them."""
    for j in range(2):
        f = (k + j * 0.5)
        ring(r, cx, cy, rx * (0.4 + f * 0.6), ry * (0.4 + f * 0.6), mat, max(1, 3 - j - int(k)), z + j * 0.01, n=36,
             gap=lambda a, j=j: (int(a * 6 + j) % 3) == 0)


# ------------------------------------------------------------------ brine on the floor
def water_blob(r, cx, cy, rx, ry, k=0, z=0.0, lit=True, edge=True, seed=3):
    """A pool of brine seen from above at a low angle: a shaded ellipse, a foam lip, glints."""
    rnd = random.Random(seed + k)
    p = r.part(False, z); r.hand.add(p)
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            u, v = (x - cx) / rx, (y - cy) / ry
            d = u * u + v * v
            wob = 0.08 * math.sin(x * 0.9 + k) * math.sin(y * 1.3)
            if d > 1.0 + wob: continue
            t = 1 if d > 0.72 else 2 if v > -0.1 else 3
            r.put(x, y, z, "water", 0.5, p, t)
    if edge:
        for i in range(int(rx * 3)):
            a = i / (rx * 3) * math.tau
            if math.sin(a) > -0.2 or (i + k) % 4 == 0: continue
            r.dot(cx + math.cos(a) * rx, cy + math.sin(a) * ry, "foam", 2 if (i + k) % 3 else 3, z + 0.01)
    if lit:
        for i in range(3):
            gx = cx - rx * 0.4 + rnd.uniform(-rx * 0.3, rx * 0.5)
            gy = cy - ry * 0.3 + rnd.uniform(-ry * 0.2, ry * 0.3)
            r.dot(gx, gy, "foam", 3 if i else 4, z + 0.02); r.dot(gx + 1, gy, "foam", 2, z + 0.02)


def fx_brine(out):
    """FxBrine (26 x 8, origin (13, 4)): Life (26 frames, 8.4 s): wells up (0-2), lies there rippling (3-22), drains."""
    frames, durs = [], []
    for i, s in enumerate((0.35, 0.65, 0.9)):
        r = R(); water_blob(r, 0, 0, 11.5 * s, 3.4 * s, k=i); frames.append(done(r)); durs.append(0.12)
    for i in range(20):
        r = R(); water_blob(r, 0, 0, 11.5, 3.4, k=i % 4, seed=i % 4); frames.append(done(r)); durs.append(0.35)
    for i, s in enumerate((0.85, 0.6, 0.3)):
        r = R(); water_blob(r, 0, 0, 11.5 * s, 3.4 * s, k=i, edge=False, lit=False); frames.append(done(r)); durs.append(0.2)
    fx("FxBrine", (26, 8), (13, 4), [("Life", frames, durs)], out)


def fx_tide(out):
    """FxBelTide (66 x 24, origin (33, 12)): Spread 4 (the water washes in), Idle 4 (loop), Fade 4 (drains)."""
    spread, idle, fade = [], [], []
    for i, s in enumerate((0.3, 0.55, 0.8, 1.0)):
        r = R(); water_blob(r, 0, 0, 29 * s, 8.5 * s, k=i, seed=11)
        foam_ring(r, 0, 0, 29 * s + 1, 8.5 * s + 1, k=i, z=0.5, n=40)
        spread.append(done(r))
    for i in range(4):
        r = R(); water_blob(r, 0, 0, 29, 8.5, k=i, seed=20 + i)
        for j in range(3): r.dot(-14 + j * 13 + (i % 2) * 2, -2 + j % 2, "foam", 2, 0.3)
        idle.append(done(r))
    for i, s in enumerate((0.9, 0.7, 0.45, 0.2)):
        r = R(); water_blob(r, 0, 0, 29 * s, 8.5 * s, k=i, lit=i < 2, edge=i < 3, seed=30)
        fade.append(done(r))
    fx("FxBelTide", (66, 24), (33, 12), [("Spread", spread, [0.08] * 4), ("Idle", idle, [0.3] * 4), ("Fade", fade, [0.135] * 4)], out)


def fx_tide_crest(out):
    """FxBelTideCrest (40 x 20, origin (20, 10)): the surge line washing in (6)."""
    frames = []
    for i in range(6):
        r = R()
        x0 = -16 + i * 4
        for j in range(7):
            y = -6 + j * 2
            h = 3 - abs(j - 3) * 0.6
            r.line(x0 - 2 + abs(j - 3), y, x0 + abs(j - 3) * 0.5, y - h, "foam", 1.0, tone=3 if j < 4 else 2)
            r.dot(x0 - 3 + abs(j - 3), y, "water", 3, 0.9)
        if i > 2:
            for j in range(4): r.dot(x0 - 6 - j * 2, -4 + j * 3, "foam", 1, 0.8)
        frames.append(done(r))
    fx("FxBelTideCrest", (40, 20), (20, 10), [("Play", frames, [0.05] * 6)], out)


def fx_splash(out):
    """FxSplash (40 x 20, origin (20, 16)): a brine splash (5)."""
    frames = []
    for i in range(5):
        r = R()
        k = min(2, i)
        for j in range(7):
            a = math.radians(-170 + j * 27)
            d = 3 + i * 2.6
            h = 7 - i * 1.6 + (i * i) * 0.3
            r.dot(math.cos(a) * d, -h * abs(math.sin(a)) - 1 + (0 if i < 3 else i - 2), "foam", 3 if j % 2 else 2, 1.0)
            if i < 3: r.dot(math.cos(a) * d * 0.7, -h * 0.6 * abs(math.sin(a)), "water", 3, 0.9)
        if i < 4: ring(r, 0, 0, 4 + i * 3, 1.2 + i * 0.6, "foam", 2 if i < 2 else 1, 0.5, n=28, step=1 + (i > 1))
        frames.append(done(r))
    fx("FxSplash", (40, 20), (20, 16), [("Play", frames, [0.06, 0.07, 0.08, 0.08, 0.1])], out)


def fx_hitsplat(out):
    """FxBelBrineSplat (34 x 20, origin (17, 7)): brine instead of blood when a Bel'Mora monster is hit (Play, Play2)."""
    anims = []
    for v, sgn in (("Play", 1), ("Play2", -1)):
        frames = []
        for i in range(5):
            r = R()
            for j in range(6):
                a = math.radians(-60 * sgn + (j - 2.5) * 22 * sgn)
                d = 2 + i * 2.5 + (j % 2)
                r.dot(sgn * math.cos(a) * d, -math.sin(a) * d * 0.7 + i * 0.6, "water" if j % 3 else "foam", 3 if i < 3 else 2, 1.0)
            if i < 2: r.ell(0, 0, 2 + i, 1.5 + i * 0.5, "foam", 1.1, flat=3 - i)
            frames.append(done(r))
        anims.append((v, frames, [0.06, 0.06, 0.08, 0.08, 0.08]))
    fx("FxBelBrineSplat", (34, 20), (17, 7), anims, out)


# ------------------------------------------------------------------ projectiles
def fx_projectiles(out):
    # FxHook (30 x 10, origin (15, 5)): an iron hook on its chain
    fl = []
    for i in range(4):
        r = R()
        chain_links(r, (-14, 0), (5, 0), 1.0, sag=0.0)
        r.polyline([(5, 0), (8, -1), (9, 1), (7, 3), (5, 2)], "iron", 1.2, tones=[3, 4, 3, 2, 2])
        r.dot(9, 0, "steel", 4 if i % 2 else 3, 1.3); r.dot(5, 2, "rust", 3, 1.3)
        fl.append(done(r))
    fx("FxHook", (30, 10), (15, 5), [("Fly", fl, [0.06] * 4)], out)
    # FxWaterBolt (24 x 9, origin (12, 4)): a slowing water bolt with a trail
    fl = []
    for i in range(4):
        r = R()
        r.ell(4, 0, 3.0, 2.2, "water", 1.0, bias=0.2)
        r.dot(5, -1, "foam", 4, 1.1); r.dot(3, -1, "foam", 3, 1.1)
        for j in range(6): r.dot(1 - j * 1.5, ((j + i) % 3) - 1, "water" if j < 3 else "foam", 3 if j < 2 else 2, 0.5)
        fl.append(done(r))
    fx("FxWaterBolt", (24, 9), (12, 4), [("Fly", fl, [0.07] * 4)], out)
    # FxBelBrineGlob (16 x 11, origin (8, 5)): a salt-crusted glob
    fl = []
    for i in range(4):
        r = R()
        r.ell(1, 0, 3.0 + (i % 2) * 0.4, 2.6 - (i % 2) * 0.3, "water", 1.0)
        for (dx, dy) in ((0, -2), (2, -1), (-1, 1)): r.dot(1 + dx, dy, "sand", 4, 1.1)
        for j in range(3): r.dot(-3 - j * 1.5, (j + i) % 2, "foam", 2, 0.5)
        fl.append(done(r))
    fx("FxBelBrineGlob", (16, 11), (8, 5), [("Fly", fl, [0.07] * 4)], out)
    # FxSpine (28 x 5, origin (14, 2)): an urchin spine
    fl = []
    for i in range(4):
        r = R()
        r.line(-6, 0, 5, 0, "urch", 1.0, tone=3); r.line(-3, 0, 5, 0, "urch", 1.05, tone=4)
        r.dot(6, 0, "ivory", 4, 1.1)
        if i % 2: r.dot(-8, 0, "urch", 2, 0.9)
        fl.append(done(r))
    fx("FxSpine", (28, 5), (14, 2), [("Fly", fl, [0.05] * 4)], out)
    # FxBelThorn / FxBelBroodSpine (22 x 8, origin (11, 4)): a crown thorn; a brood spine
    for name, mat, tip in (("FxBelThorn", "ivory", "pink"), ("FxBelBroodSpine", "spinev", "lure")):
        fl = []
        for i in range(2):
            r = R()
            r.line(-5, 0, 4, 0, mat, 1.0, tone=3); r.line(-5, 1, 2, 1, mat, 0.9, tone=1)
            r.dot(5, 0, tip, 4, 1.1)
            r.dot(-7 - i, 0, mat, 2, 0.8)
            fl.append(done(r))
        fx(name, (22, 8), (11, 4), [("Fly", fl, [0.06, 0.06])], out)
    # FxBelSlimeGlob (16 x 9, origin (8, 4))
    fl = []
    for i in range(4):
        r = R()
        r.ell(1, 0, 2.8 - (i % 2) * 0.3, 2.2 + (i % 2) * 0.3, "slime", 1.0)
        r.dot(2, -1, "slime", 4, 1.1)
        for j in range(3): r.dot(-2 - j * 1.5, 1 + (j + i) % 2, "slime", 2, 0.5)
        fl.append(done(r))
    fx("FxBelSlimeGlob", (16, 9), (8, 4), [("Fly", fl, [0.07] * 4)], out)
    # FxCoralShard (12 x 12, origin (6, 6))
    fl = []
    for i in range(4):
        r = R()
        T = Xf(i * 90, (0, 0))
        r.poly([T(-2, -3), T(3, 0), T(-2, 3), T(-1, 0)], "coral", 1.0, bias=0.1)
        r.dot(*T(2, 0), "coral", 4, 1.1)
        fl.append(done(r))
    fx("FxCoralShard", (12, 12), (6, 6), [("Fly", fl, [0.06] * 4)], out)
    # FxWave (40 x 23, origin (20, 11)): the boss's and the Undertow item's rolling wave
    fl = []
    for i in range(4):
        r = R()
        for j in range(9):
            y = -9 + j * 2.2
            cx = 4 - abs(j - 4) * 1.2 + (i % 2) * 0.5
            r.ell(cx, y, 3.0, 1.3, "water", 1.0 + j * 0.01, bias=0.1)
            r.dot(cx + 2, y - 0.5, "foam", 3 if j % 2 else 4, 1.2)
            r.dot(cx - 4 - (i + j) % 3, y, "foam", 2, 0.8)
        fl.append(done(r))
    fx("FxWave", (40, 23), (20, 11), [("Fly", fl, [0.08] * 4)], out)


def fx_rings(out):
    """Ground rings: FxBellRing (the toll), FxPeal (the hermit's bell), FxBelMarchRing (a marching peal),
    FxBelAnchorQuake (the anchor slam), FxBelStingAura (the Colossus' sting field), FxBelPoolRing (a peal ringing
    through a pool), FxBelJetRing (the Jelly Siren's sting ring)."""
    def ring_set(name, cell, origin, rx, ry, n, mat, spark=True, durs=None, gaps=3):
        frames = []
        for i in range(n):
            r = R()
            f = (i + 1) / float(n)
            for j in range(2):
                fr = f * (1.0 - j * 0.18)
                ring(r, 0, 0, rx * fr, ry * fr, mat, 3 - j if i < n - 1 else 1, 1.0 - j * 0.1, n=int(rx * 4),
                     gap=lambda a, i=i, j=j: int(a * 8 + i + j * 3) % gaps == 0)
            if spark and i < n - 1:
                for k in range(6):
                    a = k / 6 * math.tau + i * 0.4
                    r.dot(math.cos(a) * rx * f, math.sin(a) * ry * f - 2 - i, "spark", 4 if k % 2 else 3, 2.0)
            frames.append(done(r))
        fx(name, cell, origin, [("Play" if name != "FxBelAnchorQuake" else "Ring", frames, durs or [0.07] * n)], out)
    ring_set("FxBellRing", (58, 31), (29, 19), 26, 11, 5, "bronze")
    ring_set("FxPeal", (34, 21), (17, 14), 15, 6.5, 4, "bronze")
    ring_set("FxBelMarchRing", (28, 19), (14, 12), 12, 5.5, 5, "bronze")
    ring_set("FxBelAnchorQuake", (48, 19), (23, 9), 21, 8, 4, "sand", spark=False, durs=[0.0667] * 4)
    ring_set("FxBelStingAura", (60, 26), (30, 13), 26, 10, 5, "pink", spark=False, gaps=2)
    ring_set("FxBelPoolRing", (66, 24), (33, 12), 29, 9, 5, "foam", spark=False, gaps=4)
    ring_set("FxBelJetRing", (40, 18), (20, 9), 16, 6.5, 5, "jelly", spark=False, gaps=3)


# ------------------------------------------------------------------ melee art
def fx_pinch(out):
    """FxBelPinch (18 x 18, origin (9, 9)): a claw snapping shut (4)."""
    frames = []
    for i, o in enumerate((1.0, 0.6, 0.1, 0.0)):
        r = R()
        r.tube([(-4, 2), (2, -1 - o * 3), (6, -3 - o * 4)], [1.2, 0.9, 0.5], "coral", 1.0)
        r.tube([(-4, 3), (2, 4 + o * 3), (6, 4 + o * 3)], [1.0, 0.8, 0.4], "coral", 1.0, bias=-0.2)
        if i >= 2: star(r, 6, 1, 1)
        frames.append(done(r))
    fx("FxBelPinch", (18, 18), (9, 9), [("Pinch", frames, [0.08, 0.06, 0.12, 0.16])], out)


def fx_trident(out):
    """FxBelTrident (44 x 15, origin (22, 7)): the coral trident driving forward, shaded, with a wake of foam (4)."""
    frames = []
    for i in range(4):
        r = R()
        x = -5 + i * 3.5
        r.tube([(x - 12, 0), (x + 4, 0)], [0.7, 0.7], "pearl", 1.0, bias=0.1)
        r.tube([(x + 4, -4), (x + 4, 4)], [0.8, 0.8], "coral", 1.1, bias=0.1)
        for sgn, ln in ((-1, 5), (0, 7), (1, 5)):
            y = sgn * 3.5
            r.tube([(x + 4, y), (x + 4 + ln, y)], [0.8, 0.5], "coral", 1.2 + sgn * 0.01, bias=0.15 if sgn <= 0 else -0.1)
            r.dot(x + 4 + ln + 1, y, "coral", 4, 1.3)
            r.dot(x + 3 + ln, y - 1, "coral", 1, 1.25)
        for j in range(4): r.dot(x - 13 - j * 1.5, (j % 3) - 1, "foam", 3 - (j > 1), 0.5)
        if i == 2: star(r, x + 13, 0, 1)
        frames.append(done(r))
    fx("FxBelTrident", (44, 15), (22, 7), [("Thrust", frames, [0.08, 0.06, 0.12, 0.16])], out)


def fx_sting(out):
    """FxBelSting (22 x 15, origin (11, 13)): an anemone sting splash (4)."""
    frames = []
    for i in range(4):
        r = R()
        for j in range(7):
            a = math.radians(-170 + j * 27)
            d = 2 + i * 2
            r.dot(math.cos(a) * d, -5 + math.sin(a) * d * 0.8, "pink" if j % 2 else "tent", 4 - min(3, i), 1.0)
        if i < 2: r.ell(0, -5, 1.5 + i, 1.3 + i, "pink", 1.1, flat=3)
        frames.append(done(r))
    fx("FxBelSting", (22, 15), (11, 13), [("Play", frames, [0.05, 0.05, 0.06, 0.07])], out)


def fx_barnacle(out):
    """FxBelBarnacle (30 x 18, origin (15, 15)): the crab's shell plate circling it (Orbit 4) and breaking (Break 4)."""
    orbit, brk = [], []
    for i in range(4):
        r = R()
        a = i / 4 * math.tau
        x, y = math.cos(a) * 10, -6 + math.sin(a) * 3
        r.ell(x, y, 2.6, 1.8, "barn", 1.0 + math.sin(a), bias=0.15)
        barnacles(r, [(x - 1, y - 1), (x + 1, y)], 1.1 + math.sin(a))
        orbit.append(done(r))
    for i in range(4):
        r = R()
        for j in range(5):
            a = j / 5 * math.tau
            d = 2 + i * 2.5
            r.dot(math.cos(a) * d, -6 + math.sin(a) * d * 0.6 + i * 0.8, "barn", 3 if j % 2 else 4, 1.0)
        if i < 2: r.ell(0, -6, 2.5 - i, 1.8 - i * 0.5, "barn", 1.1, flat=4)
        brk.append(done(r))
    fx("FxBelBarnacle", (30, 18), (15, 15), [("Orbit", orbit, [0.12] * 4), ("Break", brk, [0.09] * 4)], out)


def fx_song(out):
    """FxSongNote (16 x 24, origin (8, 22)): sea-glass notes rising and fading (6)."""
    frames = []
    for i in range(6):
        r = R()
        for j, (x0, ph) in enumerate(((-3, 0), (3, 2))):
            y = -4 - i * 2.6 - ph
            x = x0 + math.sin(i * 0.9 + j) * 1.5
            t = 4 if i < 3 else 3 if i < 5 else 2
            r.dot(x, y, "lure", t, 1.0); r.dot(x + 1, y, "lure", t - 1, 1.0)
            r.line(x + 1, y, x + 1, y - 3, "lure", 1.0, tone=t - 1)
            r.dot(x + 2, y - 3, "lure", t - 1, 1.0)
        frames.append(done(r))
    fx("FxSongNote", (16, 24), (8, 22), [("Play", frames, [0.1] * 6)], out)


def fx_spine_egg(out):
    """FxBelSpineEgg (36 x 21, origin (18, 14)): Lay 3, Idle 4, Drift 4 (adrift in brine: bobbing in a ring of foam),
    Burst 6 (a ring of spines)."""
    def egg(r, bob=0, sp=1.0, glow=0):
        spines(r, 0, -3 + bob, 2.6, 2.4, 10, 2.2 * sp, "spinev", -1.0, front=False, tips=3, skip_down=True)
        r.ell(0, -3 + bob, 2.6, 2.4, "pink", 0.0, bias=0.1)
        r.dot(-1, -4 + bob, "pink", 4, 0.1)
        if glow: r.dot(0.5, -3 + bob, "lure", 2 + glow, 0.15)
        spines(r, 0, -3 + bob, 2.6, 2.4, 10, 2.2 * sp, "spinev", 1.0, front=True, tips=2, skip_down=True)
    lay, idle, drift, burst = [], [], [], []
    for i, s in enumerate((0.4, 0.7, 1.0)):
        r = R(); egg(r, bob=-3 + i * 1.5, sp=s); lay.append(done(r))
    for i in range(4):
        r = R(); egg(r, bob=[0, -0.3, -0.5, -0.3][i], glow=i % 2); idle.append(done(r))
    for i in range(4):
        r = R(); egg(r, bob=[0, -1, -1.5, -1][i], glow=1); foam_ring(r, 0, 0, 5.5, 1.8, k=i, z=-2.0, n=18)
        ripples(r, 0, 0, 7, 2.2, (i % 4) / 4.0, z=-2.5); drift.append(done(r))
    for i in range(6):
        r = R()
        f = (i + 1) / 6.0
        for j in range(8):
            a = j / 8 * math.tau
            x0, y0 = math.cos(a) * 3 * f * 4, -3 + math.sin(a) * 1.4 * f * 4
            r.line(x0, y0, x0 + math.cos(a) * 3, y0 + math.sin(a) * 1.4, "spinev", 1.0, tone=3 if i < 4 else 2)
            r.dot(x0 + math.cos(a) * 3, y0 + math.sin(a) * 1.4, "ivory", 4 if i < 4 else 2, 1.1)
        if i < 2: r.ell(0, -3, 3 - i, 2.5 - i, "pink", 1.2, flat=4)
        burst.append(done(r))
    fx("FxBelSpineEgg", (36, 21), (18, 14), [("Lay", lay, [0.08, 0.08, 0.1]), ("Idle", idle, [0.16] * 4),
                                             ("Drift", drift, [0.16] * 4), ("Burst", burst, [0.05] * 4 + [0.07, 0.08])], out)


def fx_thorn_patch(out):
    """FxBelThornPatch (22 x 10, origin (11, 5)): Life 8 (3 s): thorns stuck upright in the floor, then sinking."""
    frames = []
    for i in range(8):
        r = R()
        h = 3 if i < 6 else 2 if i == 6 else 1
        for j, (x, y) in enumerate(((-6, 1), (-2, -1), (2, 1), (6, 0), (0, 2))):
            r.line(x, y, x + (1 if j % 2 else -1), y - h, "ivory", 1.0 + y * 0.01, tone=3)
            r.dot(x + (1 if j % 2 else -1), y - h, "pink", 3 if i < 6 else 2, 1.1 + y * 0.01)
            r.dot(x, y + 1, "crown", 1, 0.9)
        frames.append(done(r))
    fx("FxBelThornPatch", (22, 10), (11, 5), [("Life", frames, [0.1, 0.1] + [0.42] * 4 + [0.5, 0.5])], out)


def fx_tentacle(out):
    """FxTentacle (38 x 34, origin (19, 30)): the kraken's arm out of the floor. Rise 5 (bursts up: the hit), Sway 4
    (loop while it stays), Swat 4 (lashes at a hero passing by), Sink 4."""
    def arm(r, h, bend, k=0, swat=None):
        pts = curl(0, 0, -90, h, bend + 6 * math.sin(k), n=7)
        if swat is not None:
            pts = curl(0, 0, -90, h, 18 * swat, n=7)
        tentacle(r, pts, 2.6, "tent", 1.0, suckers="lure")
    rise, sway, swat, sink = [], [], [], []
    for i, h in enumerate((5, 14, 22, 20, 18)):
        r = R(); arm(r, h, 10 - i * 2); splash(r, 0, 0, min(2, i), 1.2); rise.append(done(r))
    for i in range(4):
        r = R(); arm(r, 18, 6, k=i * 1.5); ripples(r, 0, 0, 7, 2.2, i / 4.0, z=-1.0); sway.append(done(r))
    for i, sw in enumerate((-0.6, 0.6, 1.0, 0.3)):
        r = R(); arm(r, 18, 0, swat=sw); swat.append(done(r))
    for i, h in enumerate((14, 9, 4, 1)):
        r = R(); arm(r, h, 8); ripples(r, 0, 0, 6, 2, 0.5 + i * 0.2, z=-1.0); sink.append(done(r))
    fx("FxTentacle", (38, 34), (19, 30), [("Rise", rise, [0.05, 0.05, 0.08, 0.1, 0.12]), ("Sway", sway, [0.14] * 4),
                                          ("Swat", swat, [0.06, 0.05, 0.06, 0.1]), ("Sink", sink, [0.08] * 4)], out)


# ------------------------------------------------------------------ v2 mechanics
def fx_cast_bell(out):
    """FxBelCastBell (52 x 54, origin (26, 49)): the Drowned Bell's thrown bell. Fly 6 (tumbling, drawn high over its
    landing spot: the code plays it at the target), Land 4 (slams mouth-down), Stand 4 (loop: it stands in its pool,
    the tentacles in its mouth stirring). FxBelBellShadow (36 x 12, origin (18, 6)): Grow 6, the shadow that swells on
    the landing spot."""
    fly, land, stand = [], [], []
    for i in range(6):
        r = R()
        bell_shape(r, 0, -24 + i * 4.4, 22, 21, 1.0, tilt=150 - i * 30, crack=True)
        fly.append(done(r))
    for i in range(4):
        r = R()
        bell_shape(r, 0, 0, 24, 22, 1.0, tilt=[6, -3, 1, 0][i], crack=True)
        if i < 3: dust(r, 0, 0, i, 2.0)
        if i < 2: splash(r, -13, 0, i, 1.0); splash(r, 13, 0, i, 1.0)
        land.append(done(r))
    for i in range(4):
        r = R()
        bell_shape(r, 0, 0, 24, 22, 1.0, crack=True)
        for j in range(3):
            x0 = -7 + j * 7
            pts = curl(x0, -1, -60 - j * 30, 5, 30 * math.sin(i * 1.4 + j), n=4)
            tentacle(r, [(x, min(y, -0.5)) for (x, y) in pts], 0.9, "tent", 1.5)
        stand.append(done(r))
    fx("FxBelCastBell", (52, 54), (26, 49), [("Fly", fly, [0.13] * 6), ("Land", land, [0.06, 0.08, 0.1, 0.12]),
                                             ("Stand", stand, [0.2] * 4)], out)
    sh = []
    for i in range(6):
        r = R()
        s = 0.3 + i * 0.14
        r.ell(0, 0, 14 * s, 4 * s, "tower", 0.0, flat=0)
        r.ell(0, 0, 10 * s, 2.8 * s, "tower", 0.01, flat=1)
        sh.append(done(r))
    fx("FxBelBellShadow", (36, 12), (18, 6), [("Grow", sh, [0.13] * 6)], out)


def fx_chain_rope(out):
    """FxBelChain (6 x 6, origin (3, 3)): one dripping chain link (Link 2). FxBelRope (4 x 4, origin (2, 2)): one
    rope knot (Link 2). The code lays a row of them along the line each frame."""
    links, knots = [], []
    for i in range(2):
        r = R()
        ring(r, 0, 0, 1.6, 1.2, "iron", 3 if i == 0 else 2, 1.0, n=10)
        r.dot(-1, -1, "iron", 4, 1.1)
        if i: r.dot(0, 2, "water", 3, 1.2)
        links.append(done(r))
        r = R(); r.dot(0, 0, "rope", 3 if i == 0 else 2, 1.0); r.dot(1, 0, "rope", 2 if i == 0 else 3, 1.0); knots.append(done(r))
    fx("FxBelChain", (6, 6), (3, 3), [("Link", links, [0.2, 0.2])], out)
    fx("FxBelRope", (4, 4), (2, 2), [("Link", knots, [0.2, 0.2])], out)


def fx_anchor_bite(out):
    """FxBelAnchorBite (22 x 16, origin (11, 12)): the Diver's missed hook bitten into the floor. Bite 3, Hold 2."""
    bite, hold = [], []
    for i in range(3):
        r = R()
        anchor(r, 0, -9 + i * 2, 90, 1.0)
        dust(r, 0, 0, min(2, i), 0.9)
        bite.append(done(r))
    for i in range(2):
        r = R()
        anchor(r, 0, -5, 90, 1.0)
        r.dot(1, -5 + i, "water", 3, 1.2)
        hold.append(done(r))
    fx("FxBelAnchorBite", (22, 16), (11, 12), [("Bite", bite, [0.05, 0.05, 0.08]), ("Hold", hold, [0.25, 0.25])], out)


def fx_grapple(out):
    """FxBelGrapple (16 x 16, origin (8, 8)): the Captain's grapple hook biting in (Bite 3, Hold 2)."""
    anims = []
    for name, n in (("Bite", 3), ("Hold", 2)):
        frames = []
        for i in range(n):
            r = R()
            r.line(-3, 0, 2, 0, "iron", 1.0, tone=3)
            for a in (-60, 0, 60):
                aa = math.radians(a)
                r.polyline([(2, 0), (2 + math.cos(aa) * 3, math.sin(aa) * 3), (1 + math.cos(aa) * 4, math.sin(aa) * 4 + 1)], "iron", 1.1, tones=[3, 4, 2])
            if name == "Bite": star(r, 4, 0, 1 if i < 2 else 0)
            frames.append(done(r))
        anims.append((name, frames, [0.05] * n if name == "Bite" else [0.3] * n))
    fx("FxBelGrapple", (16, 16), (8, 8), anims, out)


def fx_crown_arm(out):
    """FxBelArm (30 x 14, origin (15, 11)): a starfish arm broken off the Crown of Thorns, crawling to brine (Crawl
    4, with its wet trail), Die 3 (stamped out), Grow 3 (it reaches brine and dissolves into it)."""
    def arm(r, k, s=1.0):
        pts = [(-6 + math.sin(k) * 0.5, -1.5), (-2, -2 - math.sin(k + 1) * 0.6), (2, -1.8), (6 * s, -1.2 - math.sin(k) * 0.5)]
        r.tube(pts, [2.0 * s, 1.8 * s, 1.3 * s, 0.6], "crown", 1.0)
        for i, (x, y) in enumerate(pts[:-1]):
            r.dot(x, y - 2.0 * s, "ivory", 3, 1.1); r.dot(x, y - 3.0 * s, "pink", 3, 1.12)
        r.dot(*pts[-1], "pink", 4, 1.1)
        for j in range(4): r.dot(-8 - j * 1.5, -0.5, "water", 3 if j < 2 else 2, 0.5)
    crawl = []
    for i in range(4):
        r = R(); arm(r, i * 1.5); crawl.append(done(r))
    die = []
    for i in range(3):
        r = R()
        for j in range(5): r.dot(-4 + j * 2 + (i - 1) * (j - 2) * 0.6, -1 - (2 - i) * (j % 2), "crown" if j % 2 else "pink", 3 - i, 1.0)
        if i == 0: star(r, 0, -3, 1)
        die.append(done(r))
    grow = []
    for i, s in enumerate((0.8, 0.5, 0.25)):
        r = R(); arm(r, 0, s); ripples(r, 0, 0, 6, 2, i / 3.0, z=0.5); grow.append(done(r))
    fx("FxBelArm", (30, 14), (15, 11), [("Crawl", crawl, [0.12] * 4), ("Die", die, [0.06, 0.08, 0.12]),
                                        ("Grow", grow, [0.1, 0.1, 0.12])], out)


def fx_brood_egg(out):
    """FxBelBroodEgg (16 x 40, origin (8, 37)): the Brood Urchin's tide egg. Fall 5 (drops onto its marked spot),
    Sit 2, PulseSlow 4, PulseFast 4 (the tide is near), Pop 3 (hit: popped harmlessly). FxBelEggMark (16 x 8,
    origin (8, 4)): Mark 4, the spot it will land on."""
    def egg(r, y=0.0, glow=1, sq=1.0):
        r.ell(0, -3 + y, 2.8 / sq, 2.6 * sq, "lure", 1.0, flat=1 + min(glow, 2))
        r.ell(-0.5, -3.5 + y, 1.6, 1.4, "lure", 1.01, flat=2 + min(glow, 2))
        r.dot(-1, -4.5 + y, "lure", 4, 1.02)
        for a in (-150, -100, -40, -10):
            aa = math.radians(a)
            r.dot(math.cos(aa) * 3.6, -3 + y + math.sin(aa) * 3.3, "spinev", 3, 0.9)
        if y == 0: r.ell(0, 0, 3.0, 0.8, "tower", 0.5, flat=0)
    fall = []
    for i, y in enumerate((-30, -22, -13, -5, 0)):
        r = R(); egg(r, y=y, glow=1, sq=1.2 if i == 4 else 1.0)
        if i == 4: dust(r, 0, 0, 0, 0.7)
        fall.append(done(r))
    sit = [done((lambda r: (egg(r, glow=g), r)[1])(R())) for g in (1, 1)]
    slow = [done((lambda r: (egg(r, glow=g, sq=s), r)[1])(R())) for g, s in ((0, 1.0), (1, 1.04), (2, 1.08), (1, 1.04))]
    fast = [done((lambda r: (egg(r, glow=g, sq=s), r)[1])(R())) for g, s in ((1, 1.0), (3, 1.12), (1, 1.0), (3, 1.12))]
    pop = []
    for i in range(3):
        r = R()
        for j in range(6):
            a = j / 6 * math.tau
            d = 1.5 + i * 2.0
            r.dot(math.cos(a) * d, -3 + math.sin(a) * d * 0.8, "lure", 3 - i, 1.0)
        pop.append(done(r))
    fx("FxBelBroodEgg", (16, 40), (8, 37), [("Fall", fall, [0.08] * 5), ("Sit", sit, [0.3, 0.3]), ("PulseSlow", slow, [0.18] * 4),
                                            ("PulseFast", fast, [0.07] * 4), ("Pop", pop, [0.05, 0.06, 0.08])], out)
    mark = []
    for i in range(4):
        r = R(); ring(r, 0, 0, 5 - i * 0.6, 2.0 - i * 0.2, "lure", 2 + (i % 2), 0.0, n=20, gap=lambda a: int(a * 4) % 2 == 0)
        mark.append(done(r))
    fx("FxBelEggMark", (16, 8), (8, 4), [("Mark", mark, [0.1] * 4)], out)


def fx_lane(out):
    """FxBelLane (20 x 10, origin (10, 5)): one segment of a riptide lane: foam arrows flowing right (Flow 4, loop).
    The code rotates it along the lane. Also the streak on a pool the Salt Siren's song drags."""
    frames = []
    for i in range(4):
        r = R()
        for j in range(2):
            x = -6 + ((i * 2 + j * 8) % 16) - 1
            r.line(x - 2, -2, x, 0, "foam", 1.0, tone=3); r.line(x - 2, 2, x, 0, "foam", 1.0, tone=2)
            r.dot(x + 1, 0, "foam", 4, 1.1)
        for j in range(5): r.dot(-7 + j * 3.5 + (i % 2), (j % 2) * 2 - 1, "water", 3, 0.5)
        frames.append(done(r))
    fx("FxBelLane", (20, 10), (10, 5), [("Flow", frames, [0.06] * 4)], out)


def fx_tentacle_trail(out):
    """FxBelTentacleTrail (14 x 8, origin (7, 4)): one glowing length of the Jelly Siren's trailing tentacles (Glow 4,
    loop; Fade 2 for the far end). The code lays and rotates them along her path."""
    glow, fade = [], []
    for i in range(4):
        r = R()
        for s in (-2, 0, 2):
            pts = [(-6 + j * 2, s + math.sin(j * 1.2 + i + s) * 0.8) for j in range(7)]
            r.polyline(pts, "jelly", 1.0 + s * 0.01, tones=[3, 4, 3, 3, 4, 3, 3])
        r.dot(-4 + i * 3, 0, "lure", 3, 1.1)
        glow.append(done(r))
    for i in range(2):
        r = R()
        for s in (-2, 0, 2):
            r.polyline([(-6 + j * 2, s) for j in range(7)], "jelly", 1.0, tones=[2 - i] * 7)
        fade.append(done(r))
    fx("FxBelTentacleTrail", (14, 8), (7, 4), [("Glow", glow, [0.1] * 4), ("Fade", fade, [0.15, 0.15])], out)


def fx_slime_coat(out):
    """FxBelSlimeCoat (24 x 24): the slime coating the hero (an overlay at his feet: Loop 4, LoopBig 4 for big
    bodies): drips running down a body-sized glaze."""
    anims = []
    for name, h, w in (("Loop", 16, 6), ("LoopBig", 22, 9)):
        frames = []
        for i in range(4):
            r = R()
            for j in range(6):
                x = -w + j * (2 * w / 5.0)
                top = -h + (j % 3) * 2
                ln = 3 + (j + i) % 4
                for d in range(ln):
                    yy = top + ((i * 2 + d + j) % h)
                    r.dot(x, min(-1, yy), "slime", 3 if d == 0 else 2, 1.0)
            for j in range(4): r.dot(-w + 1 + j * (2 * w / 3.0), -1, "slime", 3, 1.1)
            r.ell(0, 0, w + 1, 1.0, "slime", 0.5, flat=1)
            frames.append(done(r))
        anims.append((name, frames, [0.12] * 4))
    fx("FxBelSlimeCoat", (24, 26), (12, 24), anims, out)


def fx_hag_knot(out):
    """FxBelHagKnot (36 x 32, origin (18, 28) at the hero's feet): the Slime Hag ties herself round the hero. Wrap 5 (a
    slimed hagfish body coils up round him from the right, two and a half turns), Hold 2 (the knot squeezes, slime
    drips), Tear 5 (the knot snaps taut and bursts outwards in slime). The code plays it on the hero; the back half of
    each turn is drawn darker and thinner, so it reads as passing behind him."""
    def helix(r, turns, rx, ry, squeeze=0.0, burst=0.0, lift=0.0, broken=0):
        n = int(turns * 18)
        pts = []
        for i in range(n + 1):
            t = i / 18.0
            a = t * math.tau
            y = -3.0 - t * 5.2 - lift
            k = 1.0 - squeeze * 0.18 + burst
            pts.append((rx * k * math.cos(a), y + ry * k * math.sin(a), math.sin(a)))
        # back runs first (behind), then front runs
        for front in (False, True):
            run = []
            for i, (x, y, sn) in enumerate(pts):
                on = (sn > -0.15) == front
                if broken and (i // 4) % broken == 1: on = False
                if on: run.append((x, y))
                elif len(run) > 1:
                    seg(r, run, front); run = []
                else: run = []
            if len(run) > 1: seg(r, run, front)

    def seg(r, run, front):
        rad = [1.7 if front else 1.0] * len(run)
        r.tube(run, rad, "hag", 1.0 if front else 0.2, bias=0.3)
        for j, (x, y) in enumerate(run):
            if front and j % 3 == 1: r.dot(x, y - 1, "slime", 4, 1.05)        # wet highlight on top
            if not front and j % 2 == 0: r.dot(x, y, "hag", 1, 0.25)

    wrap, hold, tear = [], [], []
    for i in range(5):
        r = R()
        turns = 0.6 + i * 0.5
        helix(r, turns, 9.0 + (4 - i) * 0.8, 3.6)
        # the head leads the coil, mouth open on the last loop
        a = turns * math.tau
        hx, hy = 9.0 * math.cos(a), -3.0 - turns * 5.2 + 3.6 * math.sin(a)
        r.ell(hx, hy, 2.4, 1.8, "hag", 1.2, bias=0.3)
        r.dot(hx + 1.5, hy, "slime", 3, 1.3)
        # the tail still trailing in from the right on the first frames
        if i < 3:
            r.tube([(9, -3), (13, -2), (17 - i, -1)], [1.6, 1.3, 0.9], "hag", 0.9, bias=0.3)
        if i > 2: drips(r, [(-6, -4), (4, -9)], k=i, z=1.4, mat="slime")
        wrap.append(done(r))
    for i in range(2):
        r = R()
        helix(r, 2.6, 8.4, 3.4, squeeze=1.0 if i else 0.4)
        for j, x in enumerate((-8, -2, 5, 9)):
            yy = -4 - j * 3 + (i * 2 + j) % 3
            r.dot(x, yy, "slime", 3, 1.4); r.dot(x, yy + 1, "slime", 2, 1.4)
        r.ell(0, -1, 10, 1.2, "slime", 0.1, flat=1)
        hold.append(done(r))
    for i in range(5):
        r = R()
        if i < 3:
            helix(r, 2.6, 8.4, 3.4, burst=0.25 * i, broken=0 if i == 0 else 3 - i + 1)
        n = 10
        for j in range(n):
            a = j / n * math.tau + i * 0.3
            d = 6 + i * 3.2
            x, y = d * math.cos(a), -9 + d * 0.55 * math.sin(a)
            if i >= 1: r.dot(x, y, "slime", 4 - min(3, i - 1), 1.5)
            if i >= 2: r.dot(x * 0.8, y * 0.8 + 1, "slime", 2, 1.4)
        if i >= 3: r.ell(0, -1, 7 + i * 2, 1.5, "slime", 0.1, flat=1)
        tear.append(done(r))
    fx("FxBelHagKnot", (36, 32), (18, 28), [("Wrap", wrap, [0.05] * 5), ("Hold", hold, [0.12, 0.12]),
                                              ("Tear", tear, [0.05, 0.05, 0.06, 0.07, 0.08])], out)


def fx_bud(out):
    """FxBelBud (24 x 18, origin (12, 14)): an anemone bud the Colossus flicks: Root 4 (lands and roots), Sting 4
    (loop: open, stinging), Wilt 3."""
    root, sting, wilt = [], [], []
    for i in range(4):
        r = R()
        anemone(r, 0, -1, 1.0, "pink", i >= 2, k=i, size=0.6 + i * 0.15)
        if i == 0: dust(r, 0, 0, 0, 0.6)
        root.append(done(r))
    for i in range(4):
        r = R(); anemone(r, 0, -1, 1.0, "pink", True, k=i * 1.5, size=1.1)
        ring(r, 0, 0, 9 + (i % 2), 3.2, "pink", 1, 0.0, n=24, gap=lambda a, i=i: int(a * 5 + i) % 2 == 0)
        sting.append(done(r))
    for i in range(3):
        r = R(); anemone(r, 0, -1, 1.0, "pink", False, size=0.9 - i * 0.25); wilt.append(done(r))
    fx("FxBelBud", (24, 18), (12, 14), [("Root", root, [0.06, 0.06, 0.08, 0.1]), ("Sting", sting, [0.15] * 4),
                                        ("Wilt", wilt, [0.12] * 3)], out)


def fx_round_bell(out):
    """FxBelRoundBell (14 x 14, origin (7, 13)): the Reef Champion's ringside bell over its head: Ring 6 (chimes),
    Hang 2 (loop while it rests)."""
    ringa, hang = [], []
    for i in range(6):
        r = R()
        bell_shape(r, 0, -2, 7.0, 7.0, 1.0, tilt=[-20, 20, -14, 14, -6, 0][i], verd=False, band=False)
        if i < 4:
            for s in (-1, 1): r.line(s * 5, -7, s * 6.5, -8.5, "spark", 2.0, tone=4 - i // 2)
        ringa.append(done(r))
    for i in range(2):
        r = R(); bell_shape(r, 0, -2, 7.0, 7.0, 1.0, tilt=[-3, 3][i], verd=False, band=False); hang.append(done(r))
    fx("FxBelRoundBell", (14, 14), (7, 13), [("Ring", ringa, [0.06] * 6), ("Hang", hang, [0.3, 0.3])], out)


def fx_kelp_hand(out):
    """FxBelKelpHand (24 x 30, origin (12, 25)): Man Overboard: a drowned hand of kelp rises out of the brine at the
    hero's feet, wrist first, opens its fingers and closes round his ankles, then sinks (Grab 8); bubbles stream up."""
    def hand(r, rise, open_, k):
        wy = -rise                                  # the top of the wrist above the water
        r.tube([(0.5, 1.0), (0.0, wy * 0.5), (0.0, wy)], [2.2, 2.0, 1.9], "kelp", 1.0, bias=0.1)
        for j in range(3): r.dot(-1.0 + j, wy * 0.4 + j, "kelp", 1, 1.01)                 # kelp ridges on the wrist
        if rise > 5:
            px, py = 0.0, wy - 2.0
            r.ell(px, py, 3.0, 2.4, "kelp", 1.1, bias=0.15)                                    # palm
            for i, dx in enumerate((-2.2, -0.7, 0.8, 2.2)):
                spread = (dx * 0.5) * open_
                ln = 4.5 - abs(dx) * 0.4
                curl_ = (1.0 - open_) * 2.5
                f = [(px + dx * 0.8, py - 1.5), (px + dx + spread, py - 1.5 - ln * 0.6), (px + dx + spread * 1.4 + curl_ * (0.5 if dx > 0 else -0.5), py - 1.5 - ln + curl_)]
                r.tube(f, [0.8, 0.7, 0.5], "kelp", 1.2 + i * 0.01, bias=0.2)
                r.dot(*f[-1], "kelp", 4, 1.25)
            th = [(px + 2.6, py + 0.5), (px + 4.0 + open_, py - 0.5), (px + 4.5 + open_ * 1.5, py - 2.0 + (1 - open_))]
            r.tube(th, [0.8, 0.6, 0.5], "kelp", 1.3, bias=0.1)
        r.ell(0, 0.5, 5.5, 1.6, "water", 0.5, flat=2)
        ring(r, 0, 0.5, 6.5, 2.0, "foam", 3, 0.6, n=22, gap=lambda a: int(a * 4 + k) % 3 == 0)
        for j in range(5):
            yy = -((k * 3 + j * 4) % 22) - 2
            r.dot(-4 + (j % 3) * 4, yy, "foam", 3 if j % 2 else 2, 2.0)
    frames = []
    for i, (rise, op) in enumerate(((3, 0.0), (8, 0.3), (13, 0.8), (14, 1.0), (13, 0.2), (12, 0.0), (8, 0.0), (3, 0.0))):
        r = R(); hand(r, rise, op, i); frames.append(done(r))
    fx("FxBelKelpHand", (24, 30), (12, 25), [("Grab", frames, [0.08, 0.08, 0.1, 0.1, 0.12, 0.14, 0.1, 0.1])], out)


# ------------------------------------------------------------------ portraits
def portrait_bel(out):
    """DeityBelMora (29 x 24): the god select portrait, Bel'Mora herself (deity_portraits.belmora), Idle 4."""
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    fx("DeityBelMora", (29, 24), (14, 23), [("Idle", frames("belmora", (14, 23)), [0.3, 0.25, 0.3, 0.25])], out, scale=8)


def portrait_idol(out):
    """DeityGoldIdolBelMora (29 x 24): the gold idol in the Drowned Bell's likeness (design 3): a gold bell hung from a
    kelp-wound yoke, a drowned face in its mouth with shut eyes, raised barnacles, a gold hook through the crown, two
    gold drops falling, verdigris in the hollows and one cyan glint in the face's mouth. Idle 8: a glint sweeps
    across, like the plain gold idol's."""
    frames = []
    for i in range(8):
        r = R()
        # the yoke: a gold beam across the top, wound with kelp
        r.tube([(-12, -19), (12, -19)], [1.4, 1.4], "gold", 0.5)
        for x in range(-11, 12, 3): r.dot(x, -19 + (x % 2), "verd", 2, 0.6)
        r.line(-12, -19, -12, -14, "gold", 0.4, tone=1); r.line(12, -19, 12, -14, "gold", 0.4, tone=1)
        # the hook through the crown
        r.polyline([(0, -20), (2, -19), (1, -17)], "gold", 0.7, tones=[4, 3, 2])
        bell_shape(r, 0, -1, 18, 17, 1.0, mat="gold", verd=False, band=True)
        for (x, y) in ((-5, -12), (-3, -14), (4, -11), (6, -9)): r.dot(x, y, "gold", 4, 1.1); r.dot(x + 1, y + 1, "gold", 1, 1.1)
        for (x, y) in ((-6, -8), (5, -5), (-2, -3), (3, -13)): r.dot(x, y, "verd", 2, 1.1)
        # the drowned face in the bell's mouth, eyes shut, one cyan glint in its mouth
        r.ell(0, -4, 4.0, 2.6, "gold", 1.2, bias=-0.15)
        r.line(-2, -5, -1, -5, "gold", 1.3, tone=0); r.line(1, -5, 2, -5, "gold", 1.3, tone=0)
        r.dot(0, -3, "lure", 4, 1.3)
        # two gold drops falling from the lip
        for j, x in enumerate((-6, 6)):
            r.dot(x, 1 + ((i + j * 3) % 4) // 3, "gold", 3, 1.4)
        # the glint sweep
        gx = -12 + i * 5
        if i < 6:
            for d in range(-1, 2): r.dot(gx + d, -10 - d * 3, "white", 4 if d == 0 else 3, 3.0)
        frames.append(r.resolve(floor=False, cast=False, contour=False))
    fx("DeityGoldIdolBelMora", (29, 24), (14, 21), [("Idle", frames, [0.06, 0.06, 0.06, 0.06, 0.06, 0.22, 0.2, 0.5])], out, scale=8)


JOBS = [("FxBrine", fx_brine), ("FxBelTide", fx_tide), ("FxBelTideCrest", fx_tide_crest), ("FxSplash", fx_splash),
        ("FxBelBrineSplat", fx_hitsplat), ("FxProjectiles", fx_projectiles), ("FxRings", fx_rings), ("FxBelPinch", fx_pinch),
        ("FxBelTrident", fx_trident), ("FxBelSting", fx_sting), ("FxBelBarnacle", fx_barnacle), ("FxSongNote", fx_song),
        ("FxBelSpineEgg", fx_spine_egg), ("FxBelThornPatch", fx_thorn_patch), ("FxTentacle", fx_tentacle),
        ("FxBelCastBell", fx_cast_bell), ("FxBelChain", fx_chain_rope), ("FxBelAnchorBite", fx_anchor_bite),
        ("FxBelGrapple", fx_grapple), ("FxBelArm", fx_crown_arm), ("FxBelBroodEgg", fx_brood_egg), ("FxBelLane", fx_lane),
        ("FxBelTentacleTrail", fx_tentacle_trail), ("FxBelSlimeCoat", fx_slime_coat), ("FxBelHagKnot", fx_hag_knot), ("FxBelBud", fx_bud),
        ("FxBelRoundBell", fx_round_bell), ("FxBelKelpHand", fx_kelp_hand), ("DeityBelMora", portrait_bel),
        ("DeityGoldIdolBelMora", portrait_idol)]
NOTES = {
    "FxBelCastBell": "Fly is drawn above the landing spot (the code plays it at the target while FxBelBellShadow grows "
                     "there); Land then Stand loop until the Drowned Bell lifts it.",
    "FxTentacle": "Rise (the hit, damage on frames 1-3), then the code loops Sway for the 2 s the arm stays, plays Swat at a "
                  "hero within 14 px, and Sink at the end.",
}
