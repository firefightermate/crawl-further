"""Jinx effect sheets, drawn with the same material renderer as the monsters (jinx_v2_rigs.py). Every sheet that the
code already used keeps its cell, origin, anim names and frame counts, so the templates built on it still line up; the
new ones carry the v2 mechanics (wind notes, the Ace, the lucky six, the roulette bets, the pot, the puppeteer's strings,
the prophecy omens, the burning pawprints, ...). Coordinates below are pixels from each sheet's origin, y up negative."""
import math, os, random
from jinx_v2_rigs import (Rig, Xf, lerp, die3, box3, card, harl, star, arc_smear, dust_puff, pack, preview, BUILT, PIPS, RAMPS,
                          SprRGB, rot3)
from jinx_v2_t2 import spade
from jinx_v2_t3 import club_pip, d20
from jinx_v2_t1 import confetti, spring


def R():
    return Rig()


def done(r):
    return r.resolve(floor=False, cast=False, contour=False)


def fx(name, cell, origin, anims, outdir, scale=8):
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-20s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def motes(r, x, y, k, n=6, mat="glow", spread=6.0, seed=1, z=8.0):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, math.tau); d = spread * (0.3 + 0.7 * rnd.random()) * (0.5 + 0.3 * k)
        r.dot(x + d * math.cos(a), y + d * math.sin(a) - k, mat, max(1, 4 - k), z)


def ring(r, cx, cy, rx, ry, mat, tone, z, n=40, gap=None):
    for i in range(n):
        a = i / n * math.tau
        if gap and gap(a): continue
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), mat, tone, z)


# ------------------------------------------------------------------ projectiles that fly to the right
def spin_card(ang, back="crim", face=False, trail=True, cy=-5.0, w=5.0, h=7.0, mat="card", gold=False):
    r = R()
    edge = abs(math.cos(math.radians(ang))) < 0.25
    ww = max(1.0, w * abs(math.cos(math.radians(ang))))
    if edge:
        r.line(0, cy - h / 2, 0, cy + h / 2, "gold" if gold else mat, 1.0, tone=4)
    else:
        card(r, 0.0, cy, ww, h, mat_face="gold" if gold else mat, back=None if (face or gold) else harl(0, cy, 1.6, back, "card"),
             pip=[(0, 0)] if face and not gold else None, z=1.0, lit=0.15)
        if gold and ww > 2: r.dot(0, cy, "crim", 2, 1.1); r.dot(-0.8, cy - 2, "white", 4, 1.1)
    if trail:
        for i in range(1, 4):
            r.dot(-ww / 2 - 1 - i * 1.5, cy + (i % 2) * 0.5, "gold" if gold else "white", max(1, 4 - i), 0.5)
    return done(r)


def fx_card(out):
    fx("FxCard", (22, 14), (11, 12), [("Fly", [spin_card(a) for a in (0, 45, 90, 135)], [0.05] * 4)], out)


def fx_ace(out):
    """The Card Sharp's gold Ace: Fly (a fast flat gold card with a long gold streak) and Over (2-frame loop: the Ace
    hanging over its head while the next deal is the Ace; origin = the card's bottom)."""
    fly = []
    for k in range(4):
        r = R()
        card(r, 2.0, -5.0, 5.0, 7.0, mat_face="gold", z=1.0, ang=90 + (k % 2) * 6, lit=0.2)
        r.dot(2.0, -5.0, "crim", 2, 1.1)
        for i in range(10):
            r.dot(-2 - i, -5 + (1 if (i + k) % 3 == 0 else 0), "gold", 4 if i < 3 else 3 if i < 6 else 2, 0.5)
        if k % 2: star(r, 6.0, -8.0, 2)
        fly.append(done(r))
    over = []
    for k in range(2):
        r = R()
        card(r, 0.0, -4.0, 5.0, 7.0, mat_face="gold", z=1.0, lit=0.2 + 0.1 * k)
        r.stamp("""
.n.
nCn
.n.
""", 0.0, -4.0, 1.1, {"n": ("crim", 1), "C": ("crim", 3)}, pivot=(1, 1))
        if k: star(r, 2.0, -7.0, 2)
        over.append(done(r))
    fx("FxJinxAce", (24, 14), (12, 11), [("Fly", fly, [0.04] * 4), ("Over", over, [0.4, 0.2])], out)


def fx_coin(out):
    frs = []
    for k in range(4):
        r = R()
        w = [2.4, 1.6, 0.6, 1.6][k]
        r.ell(0, -4, w, 2.4, "gold", 1.0, bias=0.15)
        if w > 1: r.dot(-0.5, -5, "gold", 4, 1.1)
        r.dot(-3 - k % 2, -4, "gold", 2, 0.5)
        frs.append(done(r))
    fx("FxCoin", (16, 11), (8, 9), [("Fly", frs, [0.05] * 4)], out)


def fx_confetti(out):
    frs = []
    for k in range(6):
        r = R()
        if k == 0:
            r.ell(0, -6, 3, 3, "white", 2, flat=4); star(r, 0, -6, 1)
        else:
            for i, (x, y, rr) in enumerate(((-4, -4, 2.6), (3, -5, 3.0), (0, -9, 2.4))):
                if k < 4: r.ell(x * (1 + 0.15 * k), y - k * 0.6, rr * (1.1 - 0.15 * k), rr * (1.0 - 0.12 * k), "smoke", 1 + i * 0.01, bias=0.2)
            confetti(r, 0, -6, k - 1, 16, 2, spread=11)
        frs.append(done(r))
    fx("FxConfetti", (34, 21), (17, 19), [("Play", frs, [0.05, 0.07, 0.08, 0.1, 0.12, 0.14])], out)


def tumble_die(rot, cy=-5.0, size=6.0, mat="ivory", trail=True):
    r = R()
    die3(r, 0.0, cy, size, *rot, z=1.0, pip_faces=2, pip_min=1.5, mat=mat)
    if trail:
        r.dots([(-5, cy + 2), (-7, cy + 2), (-9, cy + 2)], "smoke", 2, 0.5)
    return done(r)


def fx_die(out):
    fx("FxDie", (20, 16), (10, 12), [("Fly", [tumble_die((0, 30 + 45 * k, 30 * k)) for k in range(4)], [0.06] * 4)], out)


def fx_dieface(out):
    frs = []
    for k, (y, sq) in enumerate(((-16, 1.0), (-5.5, 1.0), (-8, 1.0), (-5.5, 1.0), (-5.5, 1.0), (-5.5, 1.0))):
        r = R()
        die3(r, 0.0, y, 9.0, 0, 0 if k > 2 else 40 * k, 0, z=1.0, tilt=10.0, pip_faces=1, pip_min=1.0)
        if k == 1: dust_puff(r, 0, 0, 0, 1.4); star(r, 6, -2, 2)
        if k == 2: dust_puff(r, 0, 0, 1, 1.6)
        if k == 4:
            for (dx, dy) in ((-6, -12), (6, -12), (0, -16)): r.dot(dx, dy, "glow", 4, 3)
        frs.append(done(r))
    fx("FxDieFace", (24, 27), (12, 25), [("Play", frs, [0.06, 0.05, 0.06, 0.1, 0.2, 0.2])], out)


def fx_fatemark(out):
    """Fortune Teller's fate mark: a violet sigil on the floor with an eye in it. Open and tracking the hero (0-4: the
    code moves it for 0.5 s), it seals: the eye shuts (5); a face-down card spins over it (6-8); flash (9)."""
    frs = []
    for k in range(10):
        r = R()
        rx, ry = 9.0, 3.6
        ring(r, 0, -2, rx * min(1.0, 0.4 + 0.3 * k), ry * min(1.0, 0.4 + 0.3 * k), "glow", 3 if k % 2 else 2, 0.5)
        if k >= 2: ring(r, 0, -2, rx - 2.5, ry - 1.2, "glow", 1, 0.4, n=24)
        # the eye
        if k <= 4:
            r.ell(0, -2, 3.2, 1.4, "white", 1.0, flat=3)
            r.ell(0.6 * math.sin(k), -2, 1.0, 1.0, "viol", 1.1, flat=1); r.dot(0.6 * math.sin(k), -2, "blk", 0, 1.2)
        else:
            r.line(-3, -2, 3, -2, "viol", 1.0, tone=1)
            r.dots([(-2, -1), (0, -1), (2, -1)], "viol", 2, 1.0)
        if 6 <= k <= 8:
            ang = [0, 60, 120][k - 6]
            card(r, 0, -14, max(1.0, 6 * abs(math.cos(math.radians(ang)))), 8, back=harl(0, -14, 1.6, "viol", "card"), z=3, lit=0.2)
        if k == 9:
            r.ell(0, -8, 6, 6, "white", 3, flat=3); star(r, 0, -8, 1); ring(r, 0, -2, rx, ry, "white", 4, 3)
        frs.append(done(r))
    fx("FxFateMark", (24, 26), (12, 24), [("Play", frs, [0.06, 0.08, 0.08, 0.12, 0.12, 0.12, 0.12, 0.12, 0.1, 0.1])], out)


def flames_ring(r, rx, ry, k, z=1.0, seed=3, height=3.0, n=22):
    rnd = random.Random(seed + k)
    for i in range(n):
        a = i / n * math.tau
        x, y = rx * math.cos(a), -ry + ry * math.sin(a) - 1
        h = height * (0.5 + rnd.random())
        front = math.sin(a) > 0
        zz = z + (1 if front else -1)
        r.dot(x, y, "ember", 2, zz)
        for j in range(int(h)):
            r.dot(x + (rnd.choice((-1, 0, 0, 1)) if j else 0), y - 1 - j, "fire", max(1, 4 - j), zz)


def fx_firering(out):
    frs = []
    for k in range(8):
        r = R()
        if k < 2:
            for i in range(12):
                a = i / 12 * math.tau
                d = 6 + 6 * k
                r.dot(d * math.cos(a), -5 + 0.4 * d * math.sin(a), "fire", 4, 2); r.dot(d * 0.7 * math.cos(a), -5 + 0.3 * d * math.sin(a), "ember", 3, 2)
        elif k < 7:
            flames_ring(r, 14, 4.5, k, height=3.5 if k < 6 else 2.0)
        else:
            for i in range(10):
                r.dot(14 * math.cos(i * 0.63), -5 + 4.5 * math.sin(i * 0.63) - (i % 3), "ember", 2, 1)
        frs.append(done(r))
    fx("FxFireRing", (36, 17), (18, 15), [("Play", frs, [0.06, 0.08, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])], out)


def hoop_frame(k, encore=False):
    r = R()
    w = [5.0, 3.0, 0.8, 3.0][k]
    cy = -9.0
    for i in range(32):
        a = i / 32 * math.tau
        x, y = w * math.cos(a), cy + 7.0 * math.sin(a)
        r.dot(x, y, "white" if encore else "gold", 3 if (math.cos(a) < 0 and math.sin(a) < 0) else 2, 1 + (0.5 if math.cos(a) > 0 else 0))
    rnd = random.Random(k)
    for i in range(0, 32, 2):
        a = i / 32 * math.tau
        x, y = w * math.cos(a), cy + 7.0 * math.sin(a)
        for j in range(1 + rnd.randint(0, 2)):
            r.dot(x + (1 if a > math.pi else -1) * 0 , y - 1 - j, "white" if encore and j == 0 else "fire", max(2, 4 - j), 2)
    if encore:
        star(r, -w - 2, cy - 6, 2); star(r, w + 2, cy + 5, 2)
    return done(r)


def fx_hoop(out):
    fx("FxHoop", (24, 25), (12, 23), [("Fly", [hoop_frame(k) for k in range(4)], [0.06] * 4),
                                      ("Encore", [hoop_frame(k, True) for k in range(4)], [0.05] * 4)], out)


def fx_blink(out):
    frs = []
    for k in range(5):
        r = R()
        if k < 2:
            r.ell(0, -12, 4 - k, 10 - 2 * k, "glow", 1, flat=2 + k)
        motes(r, 0, -12, k, n=14, spread=8 + 2 * k, seed=4)
        frs.append(done(r))
    fx("FxJinxBlink", (24, 33), (12, 31), [("Play", frs, [0.05, 0.06, 0.07, 0.08, 0.1])], out)


def chip_frame(k, m="crim"):
    r = R()
    w = [2.6, 1.6, 0.6, 1.6][k]
    r.ell(0, 0, w, 2.6, m, 1, bias=0.2)
    if w > 1:
        r.ell(0, 0, w * 0.5, 1.2, "ivory", 1.1, flat=3)
    r.dots([(-4, 0), (-6, 0)], m, 2, 0.5)
    return done(r)


def fx_chip(out):
    fx("FxJinxChip", (20, 10), (10, 5), [("Fly", [chip_frame(k) for k in range(4)], [0.05] * 4)], out)


def fx_clubslam(out):
    frs = []
    for k in range(5):
        r = R()
        if k == 0:
            r.ell(0, -3, 8, 3, "white", 1, flat=4); star(r, 0, -4, 1)
        else:
            club_pip(r, 0, -8 - k, 3.0 + k * 0.6, "smoke", 1 + 0.1 * k)
            for s in (-1, 1):
                r.polyline([(s * 2, -1), (s * (5 + 2 * k), 0), (s * (8 + 2 * k), -1)], "blk", 0.5, tone=1)
            dust_puff(r, 0, 0, min(2, k - 1), 1.6)
        frs.append(done(r))
    fx("FxJinxClubSlam", (30, 23), (15, 19), [("Play", frs, [0.05, 0.07, 0.08, 0.1, 0.12])], out)


def fx_crit(out):
    crit = []
    for k in range(7):
        r = R()
        rad = min(17, 4 + 2.4 * k)
        for i in range(16):
            a = i / 16 * math.tau
            r.line(rad * 0.5 * math.cos(a), -12 + rad * 0.5 * math.sin(a), rad * math.cos(a), -12 + rad * math.sin(a),
                   "glow" if i % 2 else "gold", 1, tone=max(1, 4 - k // 2))
        if k < 5:
            r.stamp("""
GG.GGG
.G.G.G
GG.G.G
G..G.G
GG.GGG
""", 0, -26 - k, 3, {"G": ("gold", 4)}, pivot=(3, 4))
        if k < 2: r.ell(0, -12, 5, 5, "white", 2, flat=4)
        crit.append(done(r))
    fum = []
    for k in range(5):
        r = R()
        for i, (x, y) in enumerate(((-3, -4), (2, -5), (0, -8))):
            r.ell(x, y - k, 2.4 - 0.3 * k, 2.0 - 0.3 * k, "smoke", 1 + i * 0.01, bias=0.1)
        r.stamp("""
.S.
SS.
.S.
.S.
SSS
""", 0, -10 - k * 2, 2, {"S": ("smoke", max(1, 4 - k))}, pivot=(1, 4))
        fum.append(done(r))
    fx("FxJinxCrit", (38, 37), (19, 35), [("Crit", crit, [0.04, 0.05, 0.06, 0.08, 0.1, 0.12, 0.14]),
                                          ("Fumble", fum, [0.08, 0.1, 0.12, 0.14, 0.16])], out)


def fx_crunch(out):
    frs = []
    for k in range(5):
        r = R()
        g = [6, 1, 0, 0, 0][k]
        for s in (-1, 1):
            # wooden jaws closing from above and below, ivory teeth
            y = -8 + s * (3 + g)
            r.poly([(-8, y - s * 2), (8, y - s * 2), (8, y), (-8, y)], "wood", 1, normal=(-0.2, -0.5 * s, 1))
            for i in range(5): r.dot(-6 + 3 * i, y + s * 0.5, "ivory", 4, 1.1)
        if k >= 1:
            rnd = random.Random(k)
            for i in range(6 + 2 * k):
                a = rnd.uniform(0, math.tau); d = 3 + 2.5 * k
                r.dot(d * math.cos(a), -8 + d * 0.6 * math.sin(a), rnd.choice(("wood", "ivory", "mane")), 3, 2)
            if k == 1: star(r, 0, -8, 1)
        frs.append(done(r))
    fx("FxJinxCrunch", (34, 24), (17, 21), [("Play", frs, [0.05, 0.06, 0.07, 0.08, 0.1])], out)


def fx_d20shard(out):
    frs = []
    for k in range(4):
        r = R()
        T = Xf(k * 90, (0, 0))
        r.poly([T(-3, 2), T(3, 2), T(0, -3)], "d20", 1, normal=(-0.3, -0.5, 1))
        r.line(*T(-3, 2), *T(0, -3), "glow", 1.1, tone=3)
        r.dots([(-5, 0), (-6, 1)], "glow", 2, 0.5)
        frs.append(done(r))
    fx("FxJinxD20Shard", (14, 12), (7, 6), [("Fly", frs, [0.05] * 4)], out)


def diamond_card(r, x, y, w, h, z, lit=0.15):
    card(r, x, y, w, h, z=z, lit=lit)
    if w > 2.5:
        r.poly([(x, y - h * 0.3), (x + w * 0.3, y), (x, y + h * 0.3), (x - w * 0.3, y)], "rdie", z + 0.01, normal=(-0.3, -0.3, 1))


def fx_diamond(out):
    orbit = []
    for k in range(8):
        r = R()
        a = k / 8 * math.tau
        x, y = 11 * math.cos(a), 4 * math.sin(a)
        w = max(1.2, 6 * abs(math.cos(a + 0.6)))
        diamond_card(r, x, y - 1, w, 8, 1 + math.sin(a))
        for j in range(1, 4):
            aa = a - j * 0.35
            r.dot(11 * math.cos(aa), 4 * math.sin(aa) - 1, "rdie", max(1, 4 - j), 0.5)
        orbit.append(done(r))
    brk = []
    for k in range(4):
        r = R()
        if k == 0: diamond_card(r, 0, -10, 6, 8, 1); star(r, 0, -10, 1)
        else:
            for i in range(5):
                a = i / 5 * math.tau + 0.3
                d = 2 + 3 * k
                r.poly([(d * math.cos(a), -10 + d * math.sin(a) + k), (d * math.cos(a) + 2, -10 + d * math.sin(a) + k),
                        (d * math.cos(a) + 1, -8 + d * math.sin(a) + k)], "rdie" if i % 2 else "card", 1, flat=max(1, 4 - k))
        brk.append(done(r))
    fx("FxJinxDiamondPlate", (29, 17), (14, 8), [("Orbit", orbit, [0.08] * 8)], out)
    fx("FxJinxDiamondBreak", (28, 20), (14, 17), [("Break", brk, [0.06, 0.08, 0.1, 0.12])], out)


def fx_dieshard(out):
    frs = []
    for k in range(4):
        r = R()
        die3(r, 0, 0, 3.6, 0, 30 + 45 * k, 40 * k, z=1, pips=False)
        r.dots([(-3, 0), (-5, 1)], "ivory", 2, 0.5)
        frs.append(done(r))
    fx("FxJinxDieShard", (14, 9), (7, 4), [("Fly", frs, [0.05] * 4)], out)


def orb(r, x, y, rad, mat="glow", trail=4, tone_core=4):
    r.ell(x, y, rad, rad, mat, 1, bias=0.25)
    r.dot(x - 0.5, y - 0.5, "white", tone_core, 1.1)
    for i in range(1, trail + 1):
        r.dot(x - rad - i * 1.4, y + (i % 2) * 0.5 - 0.25, mat, max(1, 4 - i), 0.5)


def fx_eyeorb(out):
    fly, ghost = [], []
    for k in range(4):
        r = R(); orb(r, 2, 0, 2.6 + 0.4 * (k % 2)); r.ell(2, 0, 1.0, 1.0, "white", 1.2, flat=3); r.dot(2.4, 0, "viol", 1, 1.3)
        fly.append(done(r))
        r = R()
        for (dx, dy) in ((0, -2), (2, 0), (0, 2), (-2, 0), (2, -2), (-2, 2), (0, 0)):
            if (dx + dy + k) % 2 == 0: r.dot(2 + dx, dy, "glow", 3, 1)
        for i in range(1, 5): r.dot(2 - 3 - i * 1.5, (i + k) % 2, "glow", 1, 0.5)
        ghost.append(done(r))
    fx("FxJinxEyeOrb", (24, 12), (12, 6), [("Fly", fly, [0.07] * 4), ("Ghost", ghost, [0.07] * 4)], out)


def fx_orb(out):
    frs = []
    for k in range(4):
        r = R(); orb(r, 2, -4, 2.2 + 0.3 * (k % 2), mat="glass"); r.dot(2 + (1 if k % 2 else -1), -4, "glow", 3, 1.2)
        frs.append(done(r))
    fx("FxOrb", (20, 11), (10, 9), [("Fly", frs, [0.06] * 4)], out)


def fx_gaze(out):
    frs = []
    for k in range(6):
        r = R()
        if k < 2:
            star(r, 0, 0, 2 - k + 1 if k else 2); r.dot(0, 0, "jade", 4, 2)
        elif k < 4:
            for x in range(62):
                r.dot(x, 0, "jade", 4 if (x + k) % 4 else 3, 2)
                r.dot(x, -1, "jade", 3, 1.9); r.dot(x, 1, "jade", 2, 1.9)
                if (x + k) % 6 == 0: r.dot(x, -2, "white", 4, 2.1); r.dot(x, 2, "ivory", 3, 2.1)
            star(r, 0, 0, 1)
        else:
            for x in range(0, 62, 2 if k == 4 else 4):
                r.dot(x, 0, "jade", 3 if k == 4 else 2, 2)
        frs.append(done(r))
    fx("FxJinxGaze", (130, 10), (65, 5), [("Play", frs, [0.05, 0.05, 0.12, 0.12, 0.08, 0.08])], out, scale=4)


def fx_imprint(out):
    frs = []
    for k in range(6):
        r = R()
        sq = 6 + k
        r.poly([(-sq, -2), (sq, -2), (sq + 2, 2), (-sq - 2, 2)], "ivory", 1, flat=max(1, 3 - k // 2))
        for (pu, pv) in PIPS[5]:
            r.dot(pu * 3.5, pv * 1.2, "crim", 2 if k < 4 else 1, 1.1)
        if 1 <= k <= 3:
            for s in (-1, 1):
                r.polyline([(s * sq, 0), (s * (sq + 5 + 2 * k), -1), (s * (sq + 9 + 2 * k), 1)], "blk", 0.5, tone=1)
            dust_puff(r, 0, 2, k - 1, 2.0)
        if k == 0: star(r, 0, -3, 1)
        frs.append(done(r))
    fx("FxJinxImprint", (54, 22), (27, 15), [("Play", frs, [0.04, 0.06, 0.08, 0.1, 0.14, 0.16])], out, scale=5)


def swipe_frames(kind):
    """OrcSwipe-shaped arcs drawn from the origin (9, 14): sweep 0-2 (growing), fade 3."""
    frs = []
    for k in range(4):
        r = R()
        a0, a1 = -120 + 25 * k, -120 + 60 * (k + 1)
        if kind == "lash":
            arc_smear(r, 6, 0, 13, a0, min(a1, 70), "crim", 2, z=1)
            arc_smear(r, 6, 0, 11, a0 + 20, min(a1, 70), "glow", 1, z=1.1)
            a = math.radians(min(a1, 70)); r.ell(6 + 13 * math.cos(a), 13 * math.sin(a), 1.3, 1.3, "porc", 2)
        elif kind == "maul":
            for j in range(4):
                arc_smear(r, 4, -3 + j * 2, 12, a0, min(a1, 60), "gold" if j % 2 else "white", 1, z=1 + j * 0.01)
        else:   # sabre
            arc_smear(r, 6, 0, 14, a0, min(a1, 70), "steel", 2, z=1)
            arc_smear(r, 6, 0, 15, a0 + 30, min(a1, 70), "white", 1, z=1.1)
        if k == 3:
            r2 = R()
            for (x, y), c in []: pass
        frs.append(done(r))
    return frs


def fx_swipes(out):
    fx("FxJinxLash", (36, 29), (9, 14), [("Play", swipe_frames("lash"), [0.117, 0.117, 0.117, 0.067])], out)
    fx("FxJinxMaul", (36, 28), (9, 14), [("Play", swipe_frames("maul"), [0.117, 0.117, 0.117, 0.067])], out)
    fx("FxJinxSabre", (36, 29), (9, 14), [("Play", swipe_frames("sabre"), [0.117, 0.117, 0.117, 0.067])], out)


def die_face_icon(r, n, x, y, mat="ivory", pip="crim", z=1, size=7, glow=0):
    r.poly([(x - size / 2, y - size), (x + size / 2, y - size), (x + size / 2, y), (x - size / 2, y)], mat, z, normal=(-0.3, -0.4, 1))
    r.polyline([(x - size / 2, y), (x + size / 2, y), (x + size / 2, y - size)], mat, z + 0.01, tone=1)
    for (pu, pv) in PIPS[n]:
        r.dot(x + pu * 2, y - size / 2 + pv * 2, pip, 2 + glow, z + 0.02)


def fx_loadedpips(out):
    anims = []
    for n in range(1, 7):
        frs = []
        for k in range(2):
            r = R(); die_face_icon(r, n, 0, 0, glow=k)
            if k: r.dot(2.5, -6.5, "white", 4, 2)
            frs.append(done(r))
        anims.append(("P%d" % n, frs, [0.5, 0.15]))
    fx("FxJinxLoadedPips", (16, 14), (8, 11), anims, out)


def fx_lucky(out):
    """The Dice Imp's banked six: a gold 6 face with a sparkle (Loop 2), over its head."""
    frs = []
    for k in range(2):
        r = R(); die_face_icon(r, 6, 0, 0, mat="gold", pip="crim", glow=k)
        star(r, 3 if k else -3, -7, 2)
        frs.append(done(r))
    fx("FxJinxLucky", (16, 14), (8, 11), [("Loop", frs, [0.3, 0.2])], out)


def fx_wind(out):
    """Jack-in-the-Box Wound Up: gold music notes over the box, One..Three (2-frame loop: the notes bob)."""
    anims = []
    for n, nm in ((1, "One"), (2, "Two"), (3, "Three")):
        frs = []
        for k in range(2):
            r = R()
            for i in range(n):
                x = (i - (n - 1) / 2.0) * 5
                y = -2 - ((i + k) % 2)
                r.ell(x, y, 1.3, 1.0, "gold", 1, bias=0.2)
                r.line(x + 1, y, x + 1, y - 4, "gold", 1, tone=3)
                r.dot(x + 2, y - 4, "gold", 4, 1); r.dot(x + 2, y - 3, "gold", 2, 1)
            frs.append(done(r))
        anims.append((nm, frs, [0.25, 0.25]))
    fx("FxJinxWind", (18, 10), (9, 9), anims, out)


def fx_orbitcard(out):
    fx("FxJinxOrbitCard", (14, 14), (7, 7), [("Fly", [spin_card(a, trail=False, cy=0.0, w=5, h=7) for a in (0, 50, 90, 130)], [0.06] * 4)], out)


def fx_riposte(out):
    frs = []
    for k in range(4):
        r = R()
        ang = [0, 45, 90, 135][k]
        w = max(1.0, 6 * abs(math.cos(math.radians(ang))))
        if w > 1.5: diamond_card(r, 0, 0, w, 8, 1)
        else: r.line(0, -4, 0, 4, "card", 1, tone=4)
        r.dots([(-5, 0), (-7, 0)], "rdie", 2, 0.5)
        frs.append(done(r))
    fx("FxJinxRiposte", (22, 14), (11, 7), [("Fly", frs, [0.05] * 4)], out)


def fx_poppuff(out):
    frs = []
    for k in range(6):
        r = R()
        for i, (x, y, rr) in enumerate(((-5, -4, 3.4), (5, -5, 3.6), (0, -10, 3.2), (-3, -15, 2.4), (4, -14, 2.2))):
            s = (1.0 + 0.2 * k) if k < 4 else (1.6 - 0.2 * (k - 3))
            r.ell(x * (0.8 + 0.12 * k), y - k * 0.8, rr * s * 0.7, rr * s * 0.6, "smoke", 1 + i * 0.01, bias=0.25 - 0.05 * k)
        confetti(r, 0, -9, min(3, k), 12, 9, spread=10)
        frs.append(done(r))
    fx("FxJinxPopPuff", (34, 37), (17, 27), [("Play", frs, [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])], out)


def fx_shuffle(out):
    frs = []
    for k in range(5):
        r = R()
        n = 5
        for i in range(n):
            a = -90 + (i - 2) * (18 + 8 * k)
            x, y = 6 * math.cos(math.radians(a)), -10 + 6 * math.sin(math.radians(a))
            card(r, x, y, 3.0, 4.4, back=harl(x, y, 1.4, "crim", "card") if i % 2 else None, pip=[(0, 0)], z=1 + i * 0.01,
                 ang=a + 90, lit=0.1 - 0.05 * k)
        if k == 0: star(r, 0, -12, 1)
        frs.append(done(r))
    fx("FxJinxShuffle", (35, 30), (17, 27), [("Play", frs, [0.05, 0.06, 0.08, 0.07, 0.1])], out)


def fx_string(out):
    frs = []
    for k in range(4):
        r = R()
        r.line(-14, 0, 12, 0, "glow", 1, tone=2 + (k % 2))
        r.line(12, 0, 14, 0, "steel", 1.1, tone=4)
        r.dot(13, -1, "steel", 3, 1.1)
        r.line(-14, -2, -14, 2, "wood", 1.1, tone=3)
        for i in range(3):
            r.dot(-10 + i * 8 + k * 2, (1 if (i + k) % 2 else -1), "glow", 1, 0.9)
        frs.append(done(r))
    fx("FxJinxString", (34, 10), (17, 5), [("Fly", frs, [0.06] * 4)], out)


def fx_strung(out):
    """Puppeteer strings: Bead (a violet thread bead, laid along each string every frame) and Cross (2-frame loop: a
    little control cross over the head of every ally it holds)."""
    bead = []
    for k in range(2):
        r = R(); r.dot(0, -1, "glow", 3 + k, 1); r.dot(0, 0, "glow", 2, 1)
        bead.append(done(r))
    cross = []
    for k in range(2):
        r = R()
        r.line(-3, -4, 3, -4, "wood", 1, tone=3); r.line(0, -7, 0, -1, "wood", 1, tone=2)
        r.line(-3, -4, -3, 0, "glow", 1.1, tone=3 + k); r.line(3, -4, 3, 0, "glow", 1.1, tone=4 - k)
        cross.append(done(r))
    fx("FxJinxStrung", (10, 10), (5, 8), [("Bead", bead, [0.2, 0.2]), ("Cross", cross, [0.3, 0.3])], out)


def fx_surge(out):
    frs = []
    for k in range(4):
        r = R()
        for i in range(6):
            a = i / 6 * math.tau + k * 0.5
            x = 9 * math.cos(a); y = -8 + 3 * math.sin(a) - (k + i) % 4 * 2
            spade(r, x, y, 0.9, "rdie", 1 + math.sin(a), tone=3 if math.sin(a) > 0 else 2)
        ring(r, 0, -1, 9, 3, "rdie", 2, 0.5, n=24)
        frs.append(done(r))
    fx("FxJinxSurge", (26, 27), (13, 21), [("Loop", frs, [0.09] * 4)], out)


def fx_trap(out):
    land, lie, snap = [], [], []
    for k in range(4):
        r = R()
        y = [-16, -10, -4, -1][k]
        card(r, 0, y, 7 if k > 1 else 5, 3 if k > 1 else 7, back=harl(0, y, 1.6, "crim", "card"), z=1, ang=[60, 30, 10, 0][k], lit=0.1)
        if k == 3: dust_puff(r, 0, 0, 1, 0.8)
        land.append(done(r))
    for k in range(2):
        r = R(); card(r, 0, -1, 7, 3, back=harl(0, -1, 1.6, "crim", "card"), z=1, lit=0.1)
        if k: r.dot(2, -2, "white", 3, 1.2)
        lie.append(done(r))
    for k in range(6):
        r = R()
        card(r, 0, -1, 7, 3, back=None, pip=[(0, 0)], z=1, lit=0.1)
        h = [6, 10, 9, 7, 4, 2][k]
        for dx in (-3, 0, 3):
            r.poly([(dx - 1.4, -1), (dx + 1.4, -1), (dx, -1 - h - (2 if dx == 0 else 0))], "steel", 2, normal=(-0.5, -0.2, 1))
            spade(r, dx, -1 - h - (2 if dx == 0 else 0), 0.8, "blk", 2.1)
        if k == 1: star(r, 0, -12, 1)
        snap.append(done(r))
    fx("FxJinxTrapCard", (26, 27), (13, 23), [("Land", land, [0.06] * 4), ("Lie", lie, [0.5, 0.15]),
                                              ("Snap", snap, [0.05, 0.06, 0.08, 0.08, 0.08, 0.1])], out)


def fx_juggle(out):
    frs = []
    for k in range(4):
        r = R()
        r.ell(0, -3, 2.6, 2.6, ["crim", "gold", "chipb", "crim"][k], 1, bias=0.2)
        r.line(-2, -3 + (k % 2), 2, -3 - (k % 2), "ivory", 1.1, tone=3)
        r.dots([(-4, -2), (-6, -2)], "white", 2, 0.5)
        frs.append(done(r))
    fx("FxJuggleBall", (20, 10), (10, 8), [("Fly", frs, [0.06] * 4)], out)


def knife(r, x, y, ang, z):
    a = math.radians(ang)
    tip = (x + 6 * math.cos(a), y + 6 * math.sin(a))
    r.line(x, y, *tip, "steel", z, tone=4)
    r.line(x + 0.6, y + 0.6, tip[0] + 0.6, tip[1] + 0.6, "steel", z - 0.01, tone=2)
    r.line(x - 1.5 * math.cos(a + 1.57), y - 1.5 * math.sin(a + 1.57), x + 1.5 * math.cos(a + 1.57), y + 1.5 * math.sin(a + 1.57), "gold", z + 0.01, tone=3)
    r.line(x, y, x - 3 * math.cos(a), y - 3 * math.sin(a), "crim", z, tone=2)


def fx_knife(out):
    frs = []
    for k, (y, ang) in enumerate(((-24, -40), (-16, 60), (-7, 90), (-6, 90), (-6, 86), (-6, 90))):
        r = R()
        knife(r, 0, y, ang, 1)
        if k == 3: star(r, 0, 0, 1); dust_puff(r, 0, 0, 0, 0.8)
        if k == 4: r.dots([(-2, -1), (2, -1)], "smoke", 2, 0.5)
        frs.append(done(r))
    fx("FxKnifeRain", (22, 29), (11, 27), [("Play", frs, [0.06, 0.06, 0.05, 0.08, 0.1, 0.3])], out)


def reel_sym(r, sym, x, y, z=1.2):
    if sym == "Cherry":
        r.ell(x - 1.5, y + 1, 1.4, 1.4, "eye", z, bias=0.2); r.ell(x + 1.5, y + 1.4, 1.4, 1.4, "eye", z, bias=0.2)
        r.polyline([(x - 1.5, y - 0.5), (x, y - 3), (x + 1.5, y)], "felt", z, tone=3)
    elif sym == "Bell":
        r.poly([(x - 2.5, y + 2), (x + 2.5, y + 2), (x + 1.2, y - 2), (x - 1.2, y - 2)], "gold", z, bias=0.1); r.dot(x, y + 3, "gold", 2, z)
    elif sym == "Skull":
        r.ell(x, y - 0.5, 2.2, 2.0, "ivory", z, bias=0.15); r.dots([(x - 1, y - 0.6), (x + 1, y - 0.6)], "blk", 0, z + 0.01)
        r.line(x - 1, y + 2, x + 1, y + 2, "ivory", z, tone=3)
    else:
        r.polyline([(x - 2, y - 2.5), (x + 2, y - 2.5), (x - 0.5, y + 2.5)], "crim", z, tone=3)
        r.polyline([(x - 2, y - 2), (x + 2, y - 2)], "crim", z, tone=4)


def fx_reel(out):
    anims = []
    for sym in ("Cherry", "Bell", "Skull", "Seven"):
        frs = []
        for k in range(2):
            r = R()
            r.poly([(-5, -14), (5, -14), (5, -2), (-5, -2)], "glass", 1, normal=(-0.3, -0.3, 1))
            r.polyline([(-5, -14), (5, -14), (5, -2), (-5, -2), (-5, -14)], "gold", 1.1, tone=3)
            reel_sym(r, sym, 0, -8 - (2 if k == 0 else 0))
            if k: star(r, 4, -14, 2)
            frs.append(done(r))
        anims.append((sym, frs, [0.08, 0.5]))
    fx("FxReel", (16, 19), (8, 17), anims, out)


def fx_tarot(out):
    anims = []
    for nm, m in (("Tower", "eye"), ("Fool", "fire"), ("Star", "chipb")):
        frs = []
        for k in range(4):
            r = R()
            w = [1.2, 4.0, 9.0, 9.0][k]
            if k < 2:
                card(r, 0, -12, w, 14, back=harl(0, -12, 1.6, "viol", "card"), z=1, lit=0.2)
            else:
                card(r, 0, -12, w, 14, z=1, lit=0.2 if k == 2 else -0.1)
                if nm == "Tower":
                    r.poly([(-2, -6), (2, -6), (1.5, -15), (-1.5, -15)], "blk", 1.1, normal=(-0.3, 0, 1)); star(r, 0, -16, 2)
                elif nm == "Fool":
                    r.ell(0, -12, 2.2, 2.2, "fire", 1.1); r.dots([(-1, -12.5), (1, -12.5)], "blk", 0, 1.2); r.line(-1, -11, 1, -11, "blk", 1.2, tone=0)
                else:
                    star(r, 0, -12, 1); r.dots([(-3, -16), (3, -8), (3, -16)], "chipb", 4, 1.2)
                if k == 2: ring(r, 0, -12, 7, 9, m, 3, 0.5, n=30)
            frs.append(done(r))
        anims.append((nm, frs, [0.05, 0.05, 0.3, 0.15]))
    fx("FxTarot", (22, 25), (11, 23), anims, out)


def fx_wheel(out):
    frs = []
    for k in range(8):
        r = R()
        cy = -17
        if k == 0:
            ring(r, 0, cy, 12, 12, "gold", 4, 1, n=24)
        else:
            spin = k * 50 if k < 6 else 300
            for i in range(8):
                a0 = math.radians(spin + i * 45); a1 = math.radians(spin + i * 45 + 45)
                m = "crim" if i % 2 else "blk"
                if 2 <= k <= 4: m = "crim" if i % 2 else "coat"
                r.poly([(0, cy), (13 * math.cos(a0), cy + 13 * math.sin(a0)), (13 * math.cos((a0 + a1) / 2) * 1.04, cy + 13 * math.sin((a0 + a1) / 2) * 1.04),
                        (13 * math.cos(a1), cy + 13 * math.sin(a1))], m, 1, normal=(-0.2, -0.3, 1))
            ring(r, 0, cy, 13.5, 13.5, "gold", 3, 1.1, n=48)
            r.ell(0, cy, 2.4, 2.4, "gold", 1.2, bias=0.2)
            r.poly([(-2, cy - 16), (2, cy - 16), (0, cy - 12)], "ivory", 1.3, flat=4)
            if k == 7: star(r, 0, cy - 16, 1)
        frs.append(done(r))
    fx("FxWheel", (36, 37), (18, 35), [("Play", frs, [0.1, 0.07, 0.06, 0.06, 0.07, 0.12, 0.25, 0.2])], out)


def fx_wildcard(out):
    play = []
    for k in range(8):
        r = R()
        if k < 4:
            ang = [80, 50, 20, 0][k]
            w = max(1.0, 9 * abs(math.cos(math.radians(ang))))
            card(r, 0, -12, w, 13, back=harl(0, -12, 2.0, "glow", "viol") if k < 3 else None, z=1, lit=0.2)
            if k == 3: r.stamp("""
.n...n.
nCn.nCn
.n...n.
..www..
.wmwmw.
..wnw..
""", 0, -12, 1.2, {"n": ("crim", 1), "C": ("crim", 3), "w": ("ivory", 4), "m": ("blk", 0)}, pivot=(3, 3))
        elif k < 7:
            card(r, 0, -12 - (k - 4), 9, 13, z=1, lit=0.15)
            r.stamp("""
.n...n.
nCn.nCn
.n...n.
..www..
.wmwmw.
..wnw..
""", 0, -12 - (k - 4), 1.2, {"n": ("crim", 1), "C": ("crim", 3), "w": ("ivory", 4), "m": ("blk", 0)}, pivot=(3, 3))
            star(r, [5, -5, 4][k - 4], [-18, -15, -8][k - 4], 2)
        else:
            for i in range(4):
                a = i * 1.57 + 0.6
                r.poly([(5 * math.cos(a), -12 + 5 * math.sin(a)), (5 * math.cos(a) + 3, -12 + 5 * math.sin(a)), (5 * math.cos(a) + 1, -9 + 5 * math.sin(a))],
                       "card", 1, flat=3)
            motes(r, 0, -12, 1, n=8, mat="gold", spread=9)
        play.append(done(r))
    anims = [("Play", play, [0.06, 0.05, 0.05, 0.06, 0.12, 0.14, 0.14, 0.12])]
    for suit, m in (("Hearts", "crim"), ("Spades", "blk"), ("Diamonds", "rdie"), ("Clubs", "blk")):
        r = R()
        card(r, 0, -12, 9, 13, z=1, lit=0.15)
        if suit == "Hearts":
            r.ell(-1.4, -13, 1.8, 1.6, m, 1.1); r.ell(1.4, -13, 1.8, 1.6, m, 1.1); r.poly([(-3.2, -12.6), (3.2, -12.6), (0, -8.5)], m, 1.1)
        elif suit == "Spades": spade(r, 0, -12.5, 2.0, m, 1.1)
        elif suit == "Diamonds": r.poly([(0, -17), (3, -12), (0, -7), (-3, -12)], m, 1.1, normal=(-0.3, -0.3, 1))
        else: club_pip(r, 0, -13, 2.0, m, 1.1)
        star(r, 4, -18, 2)
        anims.append((suit, [done(r)], [0.5]))
    fx("FxWildCard", (26, 26), (13, 24), anims, out)


# ------------------------------------------------------------------ new mechanics
BET_RX, BET_RY, BET_IN = 34.0, 15.0, 0.25


def bet_wheel(r, called=None, flash=0, sweep=None, fade=1.0, zero_at=None):
    """The Roulette's bets on the floor: an elliptical wheel of 8 wedges (alternating red / black, the inner quarter
    empty) round the origin. called: "Red" / "Black" / "Zero" lights those wedges (Zero: all, green)."""
    for i in range(8):
        a0 = math.radians(i * 45 - 90 - 22.5); a1 = math.radians(i * 45 - 90 + 22.5)
        red = i % 2 == 0
        lit = called == "Zero" or (called == "Red" and red) or (called == "Black" and not red)
        m = "felt" if called == "Zero" else ("rdie" if red else "sblk")
        pts = []
        for t in range(7):
            a = lerp(a0, a1, t / 6.0)
            pts.append((BET_RX * math.cos(a), BET_RY * math.sin(a)))
        for t in range(6, -1, -1):
            a = lerp(a0, a1, t / 6.0)
            pts.append((BET_RX * BET_IN * 1.6 * math.cos(a), BET_RY * BET_IN * 1.6 * math.sin(a)))
        tone = 3 if (lit and flash) else 2 if lit else 1
        if fade < 1.0 and not lit: continue
        r.poly(pts, m, 0.5, flat=tone)
        if sweep is not None and abs(((i * 45) - sweep + 180) % 360 - 180) < 23:
            r.poly(pts, "white", 0.6, flat=2)
    for i in range(8):     # gold frets between the wedges
        a = math.radians(i * 45 - 90 + 22.5)
        r.line(BET_RX * BET_IN * 1.6 * math.cos(a), BET_RY * BET_IN * 1.6 * math.sin(a), BET_RX * math.cos(a), BET_RY * math.sin(a), "gold", 0.7, tone=2)
    ring(r, 0, 0, BET_RX, BET_RY, "gold", 3, 0.8, n=72)


def fx_betwheel(out):
    """FxJinxBetWheel (origin = the centre of the bets): Mark (4-frame loop: the wheel marked round the hero, a
    highlight running round it like the ball), Red / Black / Zero (4: the called wedges flash for 0.3 s, then the
    rest fade; the erupting wedges are FxJinxWedgeBurst)."""
    mark = []
    for k in range(4):
        r = R(); bet_wheel(r, sweep=k * 90 + 45); mark.append(done(r))
    anims = [("Mark", mark, [0.1] * 4)]
    for c in ("Red", "Black", "Zero"):
        frs = []
        for k in range(4):
            r = R(); bet_wheel(r, called=c, flash=k % 2 == 0, fade=1.0 if k < 2 else 0.5); frs.append(done(r))
        anims.append((c, frs, [0.08, 0.08, 0.08, 0.12]))
    fx("FxJinxBetWheel", (74, 34), (37, 17), anims, out, scale=4)


def fx_wedgeburst(out):
    """FxJinxWedgeBurst Red / Black / Zero: a called wedge erupts: a column of chips and sparks (damage frames 1-2),
    falling back (3-5). Origin = the wedge's centre on the floor."""
    anims = []
    for c, m, m2 in (("Red", "rdie", "fire"), ("Black", "sblk", "glow"), ("Zero", "felt", "gold")):
        frs = []
        for k in range(6):
            r = R()
            h = [4, 14, 16, 10, 5, 2][k]
            r.ell(0, 0, 6 - (k > 3) * 2, 2.4, m, 0.5, flat=3 if k < 3 else 2)
            rnd = random.Random(k * 7 + len(c))
            for i in range(10):
                x = rnd.uniform(-4, 4); y = -rnd.uniform(0, h)
                r.dot(x, y, m2 if i % 3 else m, 4 if y < -h * 0.6 else 3, 1)
            if k in (1, 2):
                for i in range(3): r.ell(-3 + 3 * i, -h * 0.5 - i * 2, 1.4, 0.7, ("crim", "chipb", "gold")[i], 1.5, bias=0.2)
                star(r, 0, -h, 1 if k == 1 else 2)
            frs.append(done(r))
        anims.append((c, frs, [0.04, 0.06, 0.08, 0.1, 0.1, 0.12]))
    fx("FxJinxWedgeBurst", (20, 26), (10, 22), anims, out)


def fx_pot(out):
    """High Roller's pot (origin = its floor point): Land (3: chips crash down into a pile), Tick (2-frame loop: the
    pile glows, ticking), Burst (5: chips blast up and out), Bust (5: the pile collapses, dull, into smoke)."""
    def pile(r, n=9, glow=0, dy=0.0, spread=1.0):
        cols = ["crim", "chipb", "gold", "ivory"]
        for i in range(n):
            row = [0, 0, 0, 0, 1, 1, 1, 2, 2][i % 9]
            x = ((i % 4) - 1.5) * 3.2 * spread * (1 - 0.25 * row)
            r.ell(x, -1.0 - row * 1.6 + dy, 1.9, 0.9, cols[i % 4], 1 + 0.01 * i, bias=0.2)
        if glow:
            ring(r, 0, -1, 8, 2.5, "fire", 3 + (glow > 1), 0.5, n=30)
    land = []
    for k in range(3):
        r = R(); pile(r, n=[3, 6, 9][k], dy=[-4, -1, 0][k])
        if k == 2: dust_puff(r, 0, 0, 0, 1.4)
        land.append(done(r))
    tick = []
    for k in range(2):
        r = R(); pile(r, glow=1 + k); r.dot(0, -7 - k, "fire", 4, 2); tick.append(done(r))
    burst = []
    for k in range(5):
        r = R()
        if k < 2: pile(r, glow=2, spread=1 + 0.3 * k)
        for i in range(10):
            a = math.radians(-160 + i * 15)
            d = 3 + 4 * k
            r.ell(d * math.cos(a), -2 + d * 0.8 * math.sin(a), 1.2, 0.8, ["crim", "chipb", "gold"][i % 3], 2, bias=0.2)
        if k == 0: star(r, 0, -4, 1)
        burst.append(done(r))
    bust = []
    for k in range(5):
        r = R(); pile(r, n=max(3, 9 - 2 * k), spread=1 + 0.2 * k, dy=0.5 * k)
        for i, (x, y) in enumerate(((-3, -4), (2, -5), (0, -8))):
            r.ell(x, y - k, 1.8 + 0.3 * k, 1.4, "smoke", 3, bias=0.1 - 0.05 * k)
        bust.append(done(r))
    fx("FxJinxPot", (34, 22), (17, 18), [("Land", land, [0.05, 0.05, 0.1]), ("Tick", tick, [0.25, 0.25]),
                                         ("Burst", burst, [0.04, 0.05, 0.06, 0.08, 0.1]), ("Bust", bust, [0.06, 0.08, 0.1, 0.12, 0.14])], out)


def fx_pawprint(out):
    """Big-Top Chimera's burning pawprint (origin = its centre on the floor): flares (0-1), burns (2-6, damage ticks),
    gutters out (7)."""
    frs = []
    for k in range(8):
        r = R()
        m = "ember" if k < 7 else "smoke"
        r.ell(0, 0, 2.6, 1.6, m, 0.5, flat=2)
        for (x, y) in ((-3, -2), (-1, -3), (1, -3), (3, -2)):
            r.ell(x, y, 0.9, 0.7, m, 0.5, flat=2)
        if 0 < k < 7:
            rnd = random.Random(k)
            for i in range(6):
                x = rnd.uniform(-3, 3)
                for j in range(1 + rnd.randint(0, 2 if k < 6 else 1)):
                    r.dot(x, -1 - j, "fire", max(2, 4 - j), 1)
        frs.append(done(r))
    fx("FxJinxPawprint", (14, 12), (7, 9), [("Play", frs, [0.05, 0.08, 0.3, 0.3, 0.3, 0.3, 0.4, 0.2])], out)


def fx_tierfall(out):
    """House of Cards loses a tier: its cards flutter down off the top (origin = the house's feet)."""
    frs = []
    for k in range(6):
        r = R()
        rnd = random.Random(3)
        for i in range(7):
            x = rnd.uniform(-10, 10) * (0.6 + 0.2 * k); y = -30 + k * 4 + rnd.uniform(-3, 3)
            card(r, x, y, 3.0, 4.0, back=harl(x, y, 1.4, "crim", "card") if i % 2 else None, pip=[(0, 0)], z=1 + 0.01 * i,
                 ang=rnd.uniform(0, 360) + k * 40, lit=0.1)
        frs.append(done(r))
    fx("FxJinxTierFall", (32, 36), (16, 34), [("Play", frs, [0.06, 0.08, 0.1, 0.1, 0.12, 0.14])], out)


def fx_strike(out):
    """Natural Twenty's Advantage: the red slash struck through the lower of its two rolls (origin = the number)."""
    frs = []
    for k in range(4):
        r = R()
        L = [3, 6, 6, 6][k]
        r.line(-L, 2, L, -3, "eye", 1, tone=4 if k < 3 else 2)
        r.line(-L, 3, L, -2, "eye", 0.9, tone=2)
        frs.append(done(r))
    fx("FxJinxStrike", (16, 10), (8, 5), [("Play", frs, [0.04, 0.05, 0.4, 0.2])], out)


def fx_tada(out):
    """Grand Jester's Turn the Mask: a ring of gold bell-sparks bursts round him (damage frames 1-2). Origin = feet."""
    frs = []
    for k in range(6):
        r = R()
        rx, ry = 6 + 4 * k, 3 + 1.8 * k
        for i in range(12):
            a = i / 12 * math.tau + k * 0.1
            x, y = rx * math.cos(a), -2 + ry * math.sin(a)
            if k < 5:
                r.ell(x, y - 1, 1.2, 1.1, "gold", 1 + (1 if math.sin(a) > 0 else -1), bias=0.2)
                r.dot(x, y + 0.6, "gold", 1, 1)
            elif i % 2 == 0:
                r.dot(x, y - 1, "gold", 2, 1)     # the last bells fading
            if k < 3 and i % 3 == 0: star(r, x, y - 3, 2)
        if k == 0: star(r, 0, -10, 1)
        frs.append(done(r))
    fx("FxJinxTaDa", (52, 28), (26, 18), [("Play", frs, [0.04, 0.05, 0.06, 0.08, 0.1, 0.12])], out, scale=5)


# ------------------------------------------------------------------ the god portrait and the gold idol (29 x 24)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
PO = (14, 23)      # portrait origin: bottom centre of the cell


def backdrop(spr, fn, origin=PO, cell=(29, 24)):
    """Lay a resolved sprite over a full-cell background: fn(x, y) -> rgb, x/y in cell pixels. Portraits are opaque."""
    px = {}
    for yy in range(cell[1]):
        for xx in range(cell[0]):
            k = (xx - origin[0], yy - origin[1])
            px[k] = spr.px.get(k) or fn(xx, yy)
    out = SprRGB(px); out.tones = getattr(spr, "tones", {})
    return out


def fx_deity(out):
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    fx("DeityJinx", (29, 24), PO, [("Idle", frames("jinx", PO), [0.35, 0.12, 0.3, 0.2])], out)


def warm_bg(xx, yy):
    """The gold slot's warm backdrop (the one every gold idol sits on)."""
    cols = [(0x14, 0x0c, 0x0c), (0x24, 0x15, 0x14), (0x33, 0x1d, 0x19), (0x45, 0x27, 0x1d)]
    if xx in (0, 28) or yy in (0, 23):
        return cols[0]
    d = ((xx - 14) ** 2 / 196.0 + (yy - 10) ** 2 / 110.0) ** 0.5
    v = max(0.0, 1.0 - d) * 3.0 + (BAYER[yy % 4][xx % 4] / 16.0 - 0.47)
    return cols[max(0, min(3, int(v) + 1))]


def jinx_idol(k):
    """The gold idol: the jester's bust in gold leaf, its cap of three belled points over a grinning mask, on a plain
    plinth with one small die at its foot. Violet luck in its eyes. k 0-7: the glint frames 0-4, then the eyes flare
    (5), the die's pip winks (6), rest (7)."""
    r = R()
    # plinth: a plain slab and a step
    box3(r, -11.0, 0.0, 22.0, 3.0, 1.2, "gold", 0.0)
    r.line(-11.0, -3.0, 10.0, -3.0, "gold", 0.05, tone=4)
    r.line(-11.0, -2.0, 10.0, -2.0, "gold", 0.05, tone=3)
    die3(r, 8.6, -5.4, 4.0, ry=30.0, z=2.0, mat="gold", pip="wood", one="crim", pip_min=1.4)
    # shoulders and a smooth collar, standing on the slab
    r.ell(0.0, -4.8, 6.4, 1.8, "gold", 0.3, bias=0.35)
    r.ell(0.0, -6.4, 4.6, 1.2, "gold", 0.5, bias=0.45)
    # the mask: a big smooth face, features cut as fine lines
    r.ell(0.0, -11.2, 5.6, 4.8, "gold", 1.0, bias=0.45)
    for sx in (-1, 1):
        cx, cy = sx * 2.4, -12.0
        r.dots([(cx - 1, cy), (cx + 1, cy), (cx, cy - 1)], "gold", 1, 1.1)
        r.dot(cx, cy, "glow", 4 if k == 5 else 3, 1.2)
    r.polyline([(-3.4, -9.6), (-2.0, -8.6), (2.0, -8.6), (3.4, -9.6)], "gold", 1.1, tone=0)
    # the cap: a band and three points ending in bells
    r.tube([(-5.4, -15.0), (5.4, -15.0)], [1.0], "gold", 1.6, bias=0.3)
    for base, mid, tip, z in (((-3.6, -16.0), (-8.0, -19.0), (-10.2, -14.6), 1.5),
                               ((3.6, -16.0), (8.0, -19.0), (10.2, -14.6), 1.5),
                               ((0.0, -16.6), (0.6, -20.6), (3.6, -21.0), 1.45)):
        r.tube([base, mid, tip], [2.0, 1.2, 0.6], "gold", z, bias=0.15)
        r.ell(tip[0], tip[1] + 1.2, 1.3, 1.2, "gold", z + 0.05, bias=0.3)
    if k == 6:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): r.dot(8.6 + dx, -6.4 + dy, "fire", 3, 9)
        r.dot(8.6, -6.4, "white", 4, 9)
    if k == 5:
        for sx in (-1, 1): r.dot(sx * 2.4, -13.4, "glow", 2, 1.3)
    s = r.resolve(floor=False, cast=False)
    if k < 5:
        g = -18 + k * 8
        for p, (m, t) in s.tones.items():
            if m == "gold" and t >= 2 and abs((p[0] + p[1] * 0.6) - g) < 1.2:
                s.px[p] = RAMPS["gold"][4]
    return backdrop(s, warm_bg, origin=(14, 22))


def fx_idol(out):
    fx("DeityGoldIdolJinx", (29, 24), (14, 22), [("Idle", [jinx_idol(k) for k in range(8)],
                                                   [0.06, 0.06, 0.06, 0.06, 0.06, 0.22, 0.2, 0.5])], out)


JOBS = [("FxCard", fx_card), ("FxJinxAce", fx_ace), ("FxCoin", fx_coin), ("FxConfetti", fx_confetti), ("FxDie", fx_die),
        ("FxDieFace", fx_dieface), ("FxFateMark", fx_fatemark), ("FxFireRing", fx_firering), ("FxHoop", fx_hoop),
        ("FxJinxBlink", fx_blink), ("FxJinxChip", fx_chip), ("FxJinxClubSlam", fx_clubslam), ("FxJinxCrit", fx_crit),
        ("FxJinxCrunch", fx_crunch), ("FxJinxD20Shard", fx_d20shard), ("FxJinxDiamond", fx_diamond),
        ("FxJinxDieShard", fx_dieshard), ("FxJinxEyeOrb", fx_eyeorb), ("FxOrb", fx_orb), ("FxJinxGaze", fx_gaze),
        ("FxJinxImprint", fx_imprint), ("FxJinxSwipes", fx_swipes),
        ("FxJinxLoadedPips", fx_loadedpips), ("FxJinxLucky", fx_lucky), ("FxJinxWind", fx_wind),
        ("FxJinxOrbitCard", fx_orbitcard), ("FxJinxRiposte", fx_riposte), ("FxJinxPopPuff", fx_poppuff),
        ("FxJinxShuffle", fx_shuffle), ("FxJinxString", fx_string), ("FxJinxStrung", fx_strung), ("FxJinxSurge", fx_surge),
        ("FxJinxTrapCard", fx_trap), ("FxJuggleBall", fx_juggle), ("FxKnifeRain", fx_knife), ("FxReel", fx_reel),
        ("FxTarot", fx_tarot), ("FxWheel", fx_wheel), ("FxWildCard", fx_wildcard), ("FxJinxBetWheel", fx_betwheel),
        ("FxJinxWedgeBurst", fx_wedgeburst), ("FxJinxPot", fx_pot), ("FxJinxPawprint", fx_pawprint),
        ("FxJinxTierFall", fx_tierfall), ("FxJinxStrike", fx_strike), ("FxJinxTaDa", fx_tada),
        ("DeityJinx", fx_deity), ("DeityGoldIdolJinx", fx_idol)]
NOTES = {
    "FxJinxBetWheel": "Roulette Place Your Bets: 74 x 34, origin (37, 17) = the centre of the bets (rx 34, ry 15, the inner "
                      "quarter empty). Wedge i (0..7) is centred at angle i*45-90 deg; even = red, odd = black.",
    "FxJinxWedgeBurst": "One erupting wedge (Red / Black / Zero), origin = the wedge centre on the floor; damage frames 1-2.",
    "FxJinxPot": "High Roller's pot: Land, Tick (loops while it ticks), Burst (pays out), Bust (hit while down).",
    "FxJinxWind": "Jack-in-the-Box Wound Up indicator One..Three (head overlay).",
    "FxJinxAce": "Fly: the Card Sharp's Ace projectile; Over: the head overlay while the next deal is the Ace.",
    "FxJinxLucky": "Dice Imp Lucky Six head overlay.",
    "FxJinxStrung": "Puppeteer: Bead (laid along each string), Cross (head overlay on each strung ally).",
    "FxHoop": "Fly: the Ringmaster's hoop; Encore: the white-gold hoop of an encore.",
    "FxJinxEyeOrb": "Fly: the Oracle's orb; Ghost: the harmless omen orbs her prophecy ghost looses.",
    "DeityGoldIdolJinx": "Jinx's gold idol portrait (SlotGods.PortraitFor, gold tier).",
}
