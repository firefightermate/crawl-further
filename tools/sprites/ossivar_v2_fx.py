"""Ossivar effect sheets, the Bone Rat minion, the god portrait and the gold idol, drawn with the same material renderer as
the monsters (ossivar_v2_rigs.py). Every effect has a fixed cell and origin: the point the code pins to the effect's
position (Strike.ArtAt / Strike.Ground take the same numbers). Coordinates are pixels from the origin, y up negative."""
import math, random
from ossivar_v2_rigs import (Rig, Xf, chain, ik, lerp, skullp, lbone, skeleton, vertebrae, bone, heap, bone_bits, dust, smear,
                             arc_pts, sheet, fx, done, tail_anims, SYNC, NOTES, BONE_LEG, SKULLS, J, stone)
from ossivar_v2_t3a import harpoon_head, headstone_back, coffin  # noqa: F401


def R():
    return Rig()


def ring(r, cx, cy, rx, ry, mat, tone, z, n=40, gap=None, a0=0.0, a1=360.0):
    for i in range(n):
        a = math.radians(lerp(a0, a1, i / float(n)))
        if gap and gap(a): continue
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), mat, tone, z)


def pile(r, k=0, seed=5, z=0.0, h=1.0, w=11.0, sk=True, eye=False):
    heap(r, 0.0, 0, w, 8, seed=seed, z=z, h=h)
    if sk: skullp(r, 2.0 + (k % 2) * 0.0, -0.6 - h, "S", z + 0.5, eye=eye)


# ================================================================== bone pile, plates, chips
def fx_pile(out):
    life = [None] * 54
    rise = []
    for i, h in enumerate((0.2, 0.6, 1.0)):
        r = R(); pile(r, h=h, sk=i > 0); bone_bits(r, 0, -2, 2 - i, 4, seed=i, z=3); rise.append(done(r))
    rest = []
    for k in range(4):
        r = R(); pile(r, seed=5, h=1.0)
        if k == 2: r.dot(-3, -3, "bone", 4, 3)
        rest.append(done(r))
    crum = []
    for i in range(3):
        r = R(); heap(r, 0.0, 0, 11.0 + i * 2, 8 - i * 2, seed=5, h=0.8 - 0.3 * i); bone_bits(r, 0, -2, i, 5, seed=9, z=3)
        crum.append(done(r))
    life = rise + [rest[(i // 3) % 4 if (i // 3) % 7 == 3 else 0] for i in range(48)] + crum
    crawl = []
    for k in range(4):
        r = R(); pile(r, h=0.8 + 0.2 * (k % 2))
        for j in range(3):
            x = -5 + 4 * j + (k % 2)
            r.line(x, 0, x - 1, -1 if (j + k) % 2 else 0, "bone", 2, tone=3)
        crawl.append(done(r))
    idle = rest[:2]
    veins = []
    for k in range(4):
        r = R()
        for (x, y) in ((-3, -2), (-2, -2), (1, -3), (2, -2), (3, -1), (-1, -1)):
            r.dot(x, y, "mglow", 3 if (x + k) % 2 == 0 else 2, 5)
        r.dot(2, -3, "mglow", 4 if k % 2 == 0 else 3, 5.1)
        veins.append(done(r))
    fx("FxBonePile", (20, 14), (10, 12), [("Life", life, [0.08] * 3 + [0.4] * 48 + [0.12] * 3), ("Rise", rise, [0.08] * 3),
                                         ("Idle", idle, [0.4, 0.4]), ("Crumble", crum, [0.12] * 3), ("Crawl", crawl, [0.09] * 4),
                                         ("Veins", veins, [0.12, 0.12, 0.12, 0.12])], out)


def fx_plate(out):
    fr = []
    for k in range(4):
        r = R()
        a = k / 4.0 * math.tau
        w = 3.5 * abs(math.cos(a)) + 1.0
        r.ell(0, -5, w, 4.0, "bone", 0.0, bias=0.15)
        r.line(0, -9, 0, -1, "bone", 0.1, tone=4 if math.cos(a) > 0 else 2)
        if w > 2.5:
            r.dot(-1, -6, "bone", 4, 0.2); r.line(-int(w) + 1, -5, int(w) - 1, -5, "bone", 0.15, tone=1)
        fr.append(done(r))
    fx("FxBonePlate", (12, 14), (6, 12), [("Play", fr, [0.1] * 4)], out)
    br = []
    for i in range(4):
        r = R()
        rnd = random.Random(3)
        for j in range(7):
            a = rnd.uniform(0, math.tau); d = 2 + i * 3 + rnd.uniform(0, 2)
            x, y = d * math.cos(a), -8 + d * math.sin(a) * 0.8 + i * i * 0.4
            r.line(x, y, x + math.cos(a + 1.2) * 1.5, y + math.sin(a + 1.2) * 1.5, "bone", 1, tone=4 - min(3, i))
        if i == 0: r.ell(0, -8, 3, 3, "white", 2, flat=3)
        br.append(done(r))
    fx("FxOssBonePlateBreak", (36, 28), (17, 21), [("Play", br, [0.06, 0.08, 0.1, 0.12])], out)
    chips = {}
    for v in (0, 1):
        fr = []
        for i in range(5):
            r = R(); rnd = random.Random(10 + v)
            for j in range(8):
                a = rnd.uniform(-math.pi, 0.3) if v == 0 else rnd.uniform(-math.pi - 0.3, 0)
                d = 2 + i * 2.2 + rnd.uniform(0, 2)
                x, y = d * math.cos(a), d * math.sin(a) * 0.8 + i * i * 0.3
                if j % 3 == 0: r.line(x, y, x + 1, y, "bone", 1, tone=4 - min(3, i))
                else: r.dot(x, y, "bone" if j % 2 else "dbone", 4 - min(3, i), 1)
            if i < 2: r.ell(0, 0, 2 - i, 2 - i, "white", 2, flat=3)
            fr.append(done(r))
        chips[v] = fr
    fx("FxOssBoneChips", (32, 20), (16, 12), [("Play", chips[0], [0.05, 0.06, 0.07, 0.08, 0.1]),
                                            ("Play2", chips[1], [0.05, 0.06, 0.07, 0.08, 0.1])], out)


# ================================================================== Rattlebones' skull on the floor
def fx_skull(out):
    def sk(x, y, jaw=1, eye=True, extra=None):
        r = R(); skullp(r, x, y, "L", 1.0, jaw=jaw, eye=eye, wire=True)
        if extra: extra(r)
        return done(r)
    fly = []
    for k in range(4):
        r = R()
        # a tumbling skull at hand height (the projectile flies along the floor)
        skullp(r, 0, -6 + (k % 2), "L", 1.0, jaw=[1, 2, 1, 0][k], flip=k in (1, 2), wire=True)
        r.ell(0, 0, 3, 0.7, "tar", -2, flat=1)
        fly.append(done(r))
    land = [sk(0, -3, 2, extra=lambda r: dust(r, 0, 0, 0, 1.0)), sk(0, 0, 0, extra=lambda r: dust(r, 0, 0, 1, 1.2)), sk(0, -1, 1)]
    chat = []
    for k in range(4):
        r = R(); skullp(r, 0, 0 - (1 if k % 2 else 0), "L", 1.0, jaw=[0, 2, 0, 1][k], wire=True)
        ring(r, 0, -3, 6, 2.0, "mglow", 1 if k % 2 else 2, -1, n=14)
        chat.append(done(r))
    roll = []
    for k in range(4):
        r = R(); skullp(r, 0, 0, "L", 1.0, jaw=1, flip=k % 2 == 1, eye=k % 2 == 0)
        dust(r, -5, 0, k % 2, 0.6, n=2)
        roll.append(done(r))
    fx("FxOssSkull", (24, 16), (12, 13), [("Fly", fly, [0.06] * 4), ("Land", land, [0.06, 0.08, 0.1]), ("Chatter", chat, [0.1] * 4),
                                         ("Roll", roll, [0.06] * 4)], out)


# ================================================================== small tells
def fx_scent(out):
    fr = []
    for k in range(4):
        r = R()
        r.dot(0, -2 + k * 0.5, "mglow", 3 - min(2, k // 2), 1)
        if k < 3: r.dot(1, -1 + k * 0.5, "marrow", 3, 1)
        if k == 0: r.dot(0, -3, "mglow", 4, 1.1)
        fr.append(done(r))
    fx("FxOssScent", (8, 8), (4, 6), [("Drop", fr, [0.1, 0.12, 0.14, 0.16])], out)


def fx_splinter(out):
    fr = []
    for i, (x, y, a) in enumerate(((0, -10, -60), (2, -14, -30), (4, -15, 10), (6, -12, 60), (7, -7, 90))):
        r = R()
        p = chain(x, y, [(3.0, a)])
        r.line(p[0][0], p[0][1], p[1][0], p[1][1], "bone", 1, tone=4)
        if i < 2: r.dot(0, -9, "marrow", 3, 0.5); r.dot(-1, -8, "marrow", 2, 0.5)
        if i == 0: r.dot(1, -11, "white", 4, 1.2)
        fr.append(done(r))
    fx("FxOssSplinter", (20, 20), (10, 16), [("Play", fr, [0.05, 0.06, 0.06, 0.07, 0.08])], out)


def fx_caw(out):
    fr = []
    for i in range(5):
        r = R()
        ring(r, 0, 0, 6 + i * 4, 2.5 + i * 1.6, "spirit", max(1, 4 - i), 1, n=24 + i * 6,
             gap=lambda a: (int(math.degrees(a)) // 20) % 3 == 0)
        fr.append(done(r))
    fx("FxOssCaw", (48, 20), (24, 10), [("Ring", fr, [0.05, 0.06, 0.07, 0.08, 0.1])], out)


def fx_eye(out):
    fr = []
    for k in range(2):
        r = R()
        for x in (-2, 2):
            r.dot(x, -2, "lant", 4 if k == 0 else 3, 1); r.dot(x + 1, -2, "lant", 3, 1)
            r.dot(x, -3 - k, "lant", 2, 1)
        fr.append(done(r))
    fx("FxOssEyeFlare", (12, 8), (6, 6), [("Loop", fr, [0.12, 0.12])], out)


def fx_glow(out):
    fr = []
    for k in range(4):
        r = R()
        ring(r, 0, -2, 6 - k * 0.5, 2.5, "mglow", [2, 3, 4, 3][k], 4, n=16)
        r.dot(-2 + k, -4, "mglow", 4, 5)
        fr.append(done(r))
    fx("FxOssPileGlow", (20, 14), (10, 10), [("Play", fr, [0.08] * 4)], out)


def fx_watch(out):
    fr = []
    for k in range(4):
        r = R()
        ring(r, 0, 0, 13, 4.5, "tar", 2, -1, n=40)
        for j in range(3):
            a = math.radians(k * 30 + j * 120)
            x, y = 13 * math.cos(a), 4.5 * math.sin(a)
            r.line(x - 2, y, x + 2, y - 0.5, "tar", 0, tone=3)
        fr.append(done(r))
    fx("FxOssWatchRing", (34, 14), (17, 7), [("Loop", fr, [0.12] * 4)], out)


def fx_dirt_legs(out):
    fr = []
    for k in range(3):
        r = R()
        r.ell(0, -1, 5.5, 2.0 + 0.3 * (k % 2), "dirt", 0, bias=0.1)
        for x in (-4, -1, 2, 4):
            r.dot(x, -3 - ((x + k) % 2), "dirt", 3, 0.1)
        r.dot(-2 + k, -2, "dirt", 4, 0.2)
        fr.append(done(r))
    fx("FxOssDirtLegs", (16, 8), (8, 6), [("Loop", fr, [0.15] * 3)], out)


def fx_dig(out):
    fr = []
    for i in range(5):
        r = R()
        r.ell(0, -1, 4 + i * 1.5, 1.4 + i * 0.3, "tar", 0, flat=1)
        r.ell(0, -1, 2 + i, 0.8 + i * 0.2, "dirt", 0.1, flat=0)
        for j in range(5):
            a = j * 1.3 + i
            r.dot(math.cos(a) * (5 + i * 2), -1 + math.sin(a) * 1.5 - (2 - abs(2 - i)), "dirt", 3 - j % 2, 1)
        fr.append(done(r))
    fx("FxOssDigHole", (28, 10), (14, 6), [("Play", fr, [0.06, 0.08, 0.1, 0.12, 0.3])], out)


def fx_dust(out):
    fr = []
    for i in range(4):
        r = R(); dust(r, 0, 0, min(2, i), 1.6 + i * 0.4, n=4)
        fr.append(done(r))
    fx("FxOssPounceDust", (44, 18), (22, 12), [("Play", fr, [0.05, 0.06, 0.08, 0.1])], out)
    fr = []
    for i in range(4):
        r = R(); ring(r, 0, 0, 5 + i * 3, 1.6 + i * 1.0, "dust", max(1, 4 - i), 0, n=20); dust(r, 0, 0, min(2, i), 1.0, n=2)
        fr.append(done(r))
    fx("FxOssStepDust", (40, 14), (20, 8), [("Ring", fr, [0.05, 0.06, 0.08, 0.1])], out)


def fx_howl(out):
    fr = []
    for i in range(4):
        r = R()
        ring(r, 0, 0, 8 + i * 5, 3 + i * 2, "mglow", max(1, 4 - i), 1, n=30 + 6 * i)
        ring(r, 0, 0, 6 + i * 5, 2 + i * 2, "marrow", 2, 0.5, n=20 + 6 * i, gap=lambda a: int(math.degrees(a)) % 40 < 20)
        fr.append(done(r))
    fx("FxOssHowl", (52, 30), (25, 17), [("Ring", fr, [0.0667] * 4)], out)


# ================================================================== projectiles
def fx_shard(out):
    fr = []
    for k in range(4):
        r = R()
        a = k * 45
        p = chain(0, 0, [(2.0, a), (2.0, a + 180)])
        r.line(p[1][0], p[1][1], p[2][0] + 2 * math.cos(math.radians(a)), p[2][1], "bone", 1, tone=4)
        r.line(-3, 0, -2, 0, "bone", 0.5, tone=2)
        fr.append(done(r))
    fx("FxBoneShard", (10, 9), (5, 5), [("Fly", fr, [0.05] * 4)], out)
    fr = []
    for k in range(2):
        r = R()
        r.line(-4, 0, 3, 0, "bone", 1, tone=3); r.dot(4, 0, "marrow", 3, 1.1); r.dot(3, 0, "marrow", 2, 1.1)
        r.line(-6 - k, 0, -5, 0, "bone", 0.5, tone=1)
        fr.append(done(r))
    fx("FxOssQuill", (16, 6), (8, 3), [("Fly", fr, [0.05, 0.05])], out)


def fx_bolt(out):
    fr = []
    for k in range(4):
        r = R()
        r.ell(1, 0, 2.6, 2.2, "mglow", 1, flat=3)
        r.dot(2, -1, "mglow", 4, 1.1)
        skullp(r, 1, 2, "S", 1.2, eye=True)
        for j in range(3):
            r.dot(-3 - j * 2 - (k % 2), (j % 2) - 0.5, "mglow", 3 - j, 0.5)
        fr.append(done(r))
    fx("FxMarrowBolt", (20, 11), (12, 6), [("Fly", fr, [0.08] * 4)], out)


def fx_spear(out):
    def spear(r, a, b, z=1.0):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        vertebrae(r, [a, (b[0] - d[0] * 2, b[1] - d[1] * 2)], z, "bone", tone_a=3, tone_b=1)
        r.poly([(b[0] - d[0] * 3.5 - d[1] * 1.4, b[1] - d[1] * 3.5 + d[0] * 1.4), b, (b[0] - d[0] * 3.5 + d[1] * 0.6, b[1] - d[1] * 3.5 - d[0] * 0.6)],
               "obone", z + 0.01, normal=(-0.4, -0.6, 0.7))
    fly = []
    for k in range(2):
        r = R(); spear(r, (-9, 0), (8, 0)); r.line(-12 - k, 0, -10, 0, "white", 0.5, tone=2); fly.append(done(r))
    stand = []
    for k in range(4):
        r = R(); w = [0, 1, 0, -1][k]
        spear(r, (0, 0), (6 + w, -14))
        r.ell(0, 0, 2.5, 0.8, "dirt", 0.5, flat=1)
        stand.append(done(r))
    crum = []
    for i in range(4):
        r = R(); heap(r, 1, 0, 6 + i, 5, seed=60, h=0.6); bone_bits(r, 1, -5 + i, i, 4, seed=61, z=2); crum.append(done(r))
    fx("FxOssSpear", (32, 20), (16, 17), [("Fly", fly, [0.05, 0.05]), ("Stand", stand, [0.1, 0.1, 0.1, 0.1]),
                                         ("Crumble", crum, [0.08, 0.1, 0.12, 0.14])], out)


def fx_harpoon(out):
    fr = []
    for k in range(2):
        r = R()
        vertebrae(r, [(-9, 0), (4, 0)], 1, "bone", tone_a=3, tone_b=1)
        harpoon_head(r, (8, 0), (1, 0), 1.1)
        fr.append(done(r))
    fx("FxOssHarpoon", (22, 10), (11, 5), [("Fly", fr, [0.06, 0.06])], out)
    r = R()
    for x in range(-6, 6):
        r.dot(x, 0, "bone", 3 if (x // 2) % 2 == 0 else 1, 1)
    r.dot(-6, -1, "bone", 2, 1); r.dot(0, -1, "bone", 2, 1)
    seg = done(r)
    fx("FxOssRope", (14, 4), (7, 2), [("Seg", [seg], [1.0])], out)
    fr = []
    for k in range(2):
        r = R()
        for x in range(-6, 6):
            r.dot(x, 0 if (x + k) % 4 else -1, "mglow", 3 if (x + k) % 3 else 2, 1)
        fr.append(done(r))
    fx("FxOssMarrowLine", (14, 4), (7, 2), [("Seg", fr, [0.12, 0.12])], out)


def fx_crow(out):
    fr = []
    for k in range(3):
        r = R()
        r.ell(0, -1, 2.4, 1.6, "feath", 0, bias=0.2)
        r.stamp(".LH\nLHH\n", 2, -2, 0.5, BONE_LEG, pivot=(0, 1))
        r.dot(1, -2, "mglow", 3, 0.6)
        wy = [-5, -1, 2][k]
        r.poly([(-1, -2), (-4, wy), (0, wy + 1), (1, -1)], "feath", 0.8, normal=(-0.3, -0.6, 0.8))
        r.line(-1, -2, -4, wy, "feath", 0.81, tone=4)
        r.line(-2, -1, -5, 0, "feath", -0.5, tone=2)
        fr.append(done(r))
    fx("FxOssCrow", (16, 12), (8, 7), [("Fly", fr, [0.06] * 3)], out)


# ================================================================== Vulture / Roc marks
def fx_dive(out):
    fr = []
    for i in range(6):
        r = R(); s = 0.3 + 0.14 * i
        r.ell(0, 0, 9 * s, 3 * s, "tar", 0, flat=2)
        r.ell(0, 0, 6 * s, 2 * s, "tar", 0.1, flat=1)
        if i >= 3: ring(r, 0, 0, 10 * s, 3.4 * s, "marrow", 2, 0.2, n=22)
        fr.append(done(r))
    fx("FxOssDiveShadow", (30, 12), (15, 6), [("Play", fr, [0.08] * 6)], out)
    fr = []
    for i in range(5):
        r = R(); dust(r, 0, 0, min(2, i), 2.0 + i * 0.4, n=4)
        bone_bits(r, 0, -3, i, 6, seed=70, z=4, mat="feath")
        if i < 2: ring(r, 0, 0, 6 + i * 4, 2 + i * 1.5, "white", 3 - i, 5, n=20)
        fr.append(done(r))
    fx("FxOssDiveImpact", (52, 30), (26, 22), [("Play", fr, [0.05, 0.06, 0.07, 0.08, 0.1])], out)
    fr = []
    for k in range(2):
        r = R(); r.ell(0, 0, 7, 2.2, "tar", 0, flat=2 - k); ring(r, 0, 0, 8, 2.8, "marrow", 2 + k, 0.1, n=20)
        fr.append(done(r))
    fx("FxOssDropShadow", (22, 10), (11, 5), [("Loop", fr, [0.15, 0.15])], out)


# ================================================================== Tombwright headstones
def stone_at(r, x, y, ang=0.0, z=0.0, crack=0, h=1.0, scale=1.0):
    """An upright blank headstone standing on (x, y), tipped ang deg (positive falls to the right)."""
    T = Xf(ang, (x, y))
    W, H = 4.5 * scale, 13.0 * scale * h
    pts = [T(x - W, y), T(x + W, y), T(x + W, y - H + 3), T(x + W * 0.6, y - H + 0.8), T(x, y - H), T(x - W * 0.6, y - H + 0.8), T(x - W, y - H + 3)]
    r.poly(pts, "stone", z, curve=0.4, normal=(-0.3, -0.3, 1.0))
    r.dot(*T(x - 2.5, y - 3), "lichen", 3, z + 0.01); r.dot(*T(x - 1.5, y - 2), "lichen", 2, z + 0.01); r.dot(*T(x + 2, y - 8 * h), "lichen", 2, z + 0.01)
    r.line(*T(x - 2, y - H + 4), *T(x + 2, y - H + 4), "stone", z + 0.02, tone=1)
    if crack:
        pts = [T(x + 0.5, y), T(x + 1.5, y - 1.5), T(x + 0.5, y - 3.0), T(x + 1.5, y - 4.5)][:crack + 1]
        r.polyline(pts, "stone", z + 0.03, tone=1)


def fx_headstone(out):
    def S(**kw):
        r = R(); extra = kw.pop("extra", None); stone_at(r, 0, 0, **kw)
        if extra: extra(r)
        return done(r)
    rise = [S(h=0.25, extra=lambda r: dust(r, 0, 0, 0, 1.4, 4)), S(h=0.6, extra=lambda r: dust(r, 0, 0, 0, 1.6, 4)),
            S(h=1.05, extra=lambda r: dust(r, 0, 0, 1, 1.8, 4)), S(h=1.0, extra=lambda r: dust(r, 0, 0, 2, 2.0, 4))]
    stand = [S(), S(ang=1)]
    crack = [S(crack=1, ang=-2), S(crack=2, ang=3), S(crack=3, ang=6)]
    side = [S(ang=a, extra=(lambda r: dust(r, 11, 0, 0, 2.0, 4)) if a > 80 else None) for a in (20, 45, 70, 90)]
    side.append(S(ang=90, extra=lambda r: dust(r, 11, 0, 1, 2.2, 4)))
    # toward the viewer: the face drops over, foreshortening down onto the floor; away: it tips back and shrinks
    def front(k):
        r = R(); stone_at(r, 0, 0, h=[0.8, 0.5, 0.25, 0.2][k]); r.ell(0, 1.0 + k * 0.8, 4.5, 1.0 + k * 0.7, "stone", 0.5, bias=0.2)
        if k >= 2: dust(r, 0, 3, k - 2, 2.0, 4)
        return done(r)

    def back(k):
        r = R(); stone_at(r, 0, -k * 2.5, h=[0.8, 0.55, 0.3, 0.2][k])
        if k >= 2: dust(r, 0, -6, k - 2, 2.0, 4)
        return done(r)
    crum = []
    for i in range(4):
        r = R(); heap(r, 0, 0, 10 + i * 2, 6, seed=81, h=1.2 - 0.3 * i, mat="bone")
        for j in range(4 - i): r.ell(-4 + j * 3, -1 - (j % 2), 1.6, 1.2, "stone", 0.5 + j * 0.01)
        bone_bits(r, 0, -4, i, 5, seed=82, z=3, mat="stone"); crum.append(done(r))
    fx("FxOssHeadstone", (60, 44), (30, 28), [("Rise", rise, [0.06, 0.06, 0.08, 0.12]), ("Stand", stand, [0.5, 0.5]),
                                             ("Crack", crack, [0.08, 0.08, 0.08]), ("FallSide", side, [0.05, 0.05, 0.05, 0.06, 0.1]),
                                             ("FallFront", [front(k) for k in range(4)], [0.05, 0.06, 0.06, 0.1]),
                                             ("FallBack", [back(k) for k in range(4)], [0.05, 0.06, 0.06, 0.1]),
                                             ("Crumble", crum, [0.08, 0.1, 0.12, 0.14])], out)


# ================================================================== Bone Mammoth cracks and spikes
def fx_cross(out):
    fr = []
    for k in range(4):
        r = R()
        pts = [(-6, 0), (-3, -0.5 if k % 2 else 0.5), (0, 0), (3, 0.5), (6, 0)]
        n = min(4, k + 2)
        r.polyline(pts[:n + 1], "tar", 0, tones=[0] * n)
        if k >= 2:
            for x in (-4, 1, 4): r.dot(x, -1 if x % 2 else 1, "mglow", 2 if k == 2 else 3, 0.5)
        fr.append(done(r))
    fx("FxOssCrack", (16, 6), (8, 3), [("Crack", fr, [0.06, 0.06, 0.1, 0.1])], out)
    fr = []
    for i, h in enumerate((3, 9, 12, 8, 3)):
        r = R()
        for j, (dx, hh) in enumerate(((-3, 0.6), (0, 1.0), (3, 0.7))):
            r.poly([(dx - 1.2, 0), (dx + 1.2, 0), (dx + 0.2 * (j - 1), -h * hh)], "bone", j * 0.01, normal=(-0.4, -0.4, 0.8))
        if i <= 1: bone_bits(r, 0, -2, i, 4, seed=90, z=2, mat="dirt")
        if i >= 3: dust(r, 0, 0, i - 3, 1.2, 3)
        fr.append(done(r))
    fx("FxOssCrossSpike", (18, 18), (9, 15), [("Play", fr, [0.04, 0.05, 0.12, 0.1, 0.08])], out)


# ================================================================== Cerberus grave gas cone (origin = the mouth; opens to the right)
def fx_cone(out):
    fr = []
    for k in range(4):
        r = R(); rnd = random.Random(k)
        puffs = []
        for i in range(14):
            t = (i % 7 + 0.5 + 0.35 * ((k + i) % 2)) / 7.0
            x = 4 + t * 34 + k * 1.2; s = t * 10
            puffs.append((x, (1 if i < 7 else -1) * rnd.uniform(0.3, 1.0) * s, 1.4 + t * 2.6))
        for (x, y, rr) in puffs:
            r.ell(x, y, rr, rr * 0.8, "gas", 1.0 + x * 0.001, bias=0.1)        # lit puffs, top-left light
        for (x, y, rr) in puffs:                                                # soft edge: sparse wisps round each puff
            for j in range(6):
                a = rnd.uniform(0, math.tau)
                r.dot(x + (rr + 1) * math.cos(a), y + (rr * 0.8 + 1) * math.sin(a), "gas", 1, 0.5)
        r.ell(2, 0, 1.8, 1.4, "gfire", 1.2, flat=4)
        fr.append(r.resolve(floor=False, cast=False, contour=False, selout=False))
    fx("FxOssGasCone", (56, 30), (2, 15), [("Loop", fr, [0.08] * 4)], out)


# ================================================================== Church Grim's revive ring
def fx_grim_ring(out):
    fr = []
    for k in range(6):
        r = R()
        ring(r, 0, 0, 11, 4.0, "tar", 2, 0, n=36)
        ring(r, 0, 0, 11, 4.0, "lant", 3 if k < 5 else 4, 0.1, n=36, a1=60.0 * (k + 1), a0=0.0)
        fr.append(done(r))
    fx("FxOssGrimRing", (28, 12), (14, 6), [("Fill", fr, [0.5] * 6)], out)


# ================================================================== The Ossuary's rib cage
def fx_rib(out):
    def rib_img(h=1.0, crack=False, broken=0, left=False):
        r = R(); f = -1 if left else 1
        pts = [(0, 0), (0.5 * f, -6 * h), (2.0 * f, -12 * h), (4.5 * f, -16 * h), (7.5 * f, -17.5 * h)]
        if broken: pts = pts[:max(2, 5 - broken)]
        r.tube(pts, [1.6, 1.4, 1.1, 0.9, 0.7], "bone", 0, bias=0.1)
        r.ell(0, -0.5, 2.0, 1.0, "dirt", -0.5, flat=1)
        if crack: r.polyline([(0, -5), (1 * f, -6), (0, -7)], "iron", 0.5, tone=0)
        if broken: bone_bits(r, 0, -8, broken - 1, 5, seed=99, z=2)
        return done(r)
    anims = []
    for side, L in (("", False), ("L", True)):
        anims += [("Rise" + side, [rib_img(0.3, left=L), rib_img(0.7, left=L), rib_img(1.05, left=L)], [0.05, 0.05, 0.08]),
                  ("Stand" + side, [rib_img(1.0, left=L), rib_img(0.98, left=L)], [0.3, 0.3]),
                  ("Break" + side, [rib_img(1.0, True, 1, L), rib_img(0.8, True, 2, L), rib_img(0.5, True, 3, L), rib_img(0.2, True, 4, L)],
                   [0.05, 0.06, 0.08, 0.1])]
    fx("FxOssRib", (22, 22), (11, 19), anims, out)
    fr = []
    for k in range(4):
        r = R()
        for j in range(6):
            a = math.radians(j * 60 + 15)
            x0, y0 = 10 * math.cos(a), 7 * math.sin(a)
            x1, y1 = 22 * math.cos(a), 16 * math.sin(a)
            n = 1 + k
            r.polyline([(lerp(x0, x1, i / 4.0) + (i % 2), lerp(y0, y1, i / 4.0)) for i in range(n + 1)], "tar", 0, tone=0)
        if k >= 2: ring(r, 0, 0, 22, 16, "dust", 2, 0.5, n=24)
        fr.append(done(r))
    fx("FxOssRibCrack", (52, 36), (26, 18), [("Play", fr, [0.1] * 4)], out)


def fx_spike_ring(out):
    fr = []
    for i, h in enumerate((4, 9, 7, 3)):
        r = R()
        for j in range(10):
            a = math.radians(j * 36)
            x, y = 17 * math.cos(a), 6 * math.sin(a)
            hh = h * (1.0 if j % 2 else 0.7)
            r.poly([(x - 1.2, y), (x + 1.2, y), (x, y - hh)], "bone", y * 0.01, normal=(-0.4, -0.4, 0.8))
        if i >= 2: dust(r, 0, 0, i - 2, 3.0, 4)
        fr.append(done(r))
    fx("FxSpikeRing", (52, 24), (26, 13), [("Play", fr, [0.05, 0.06, 0.07, 0.1])], out)


# ================================================================== Bone Rat (the Priest's minion)
def rat(lean=0.0, bob=0.0, legs=None, jaw=0, extra=None):
    r = Rig()
    legs = legs or ((-3.0, 0.0), (2.5, 0.0), (-2.0, 0.0), (3.5, 0.0))
    hip, sh = (-2.5, -3.0 + bob), (2.0, -3.4 + bob)
    for k, (fx_, fy_) in enumerate(legs):
        a = sh if k in (1, 3) else hip
        lbone(r, a, (fx_, fy_), 0.5 if k < 2 else -0.5, k < 2)
    vertebrae(r, [(hip[0] - 1, hip[1]), (0, -4.5 + bob), (sh[0], sh[1] - 0.5)], 0.3, "bone", tone_a=3, tone_b=1)
    for i in range(3):
        r.line(-1.5 + i * 1.3, -4 + bob, -1 + i * 1.3, -2 + bob, "bone", 0.2, tone=3 if i % 2 == 0 else 2)
    r.polyline(chain(hip[0] - 1, hip[1], [(2, 190), (2, 170), (2, 200)]), "dbone", -0.2, tones=[2, 1, 2])
    r.stamp("""
.LH...
LLkeLH
SBBTtL
""" if jaw == 0 else """
.LH...
LLkeLH
SBBT..
..SBL.
""", sh[0] + 0.5, sh[1] + 0.5, 1.0, BONE_LEG, pivot=(1, 2))
    if extra: extra(r)
    return r.resolve()


def rat_sheet(out):
    idle = [rat(bob=[0, 0.3, 0.5, 0.3][i], jaw=1 if i == 2 else 0) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(rat(bob=-0.5 * abs(math.sin(ph)), legs=[(bx + 1.6 * math.cos(ph + (0 if k in (0, 3) else math.pi)),
                                                             -max(0.0, 1.0 * math.sin(ph + (0 if k in (0, 3) else math.pi))))
                                                            for k, bx in enumerate((-3.0, 2.5, -2.0, 3.5))]))
    bite = [rat(bob=0.5, jaw=1), rat(bob=0.2, jaw=1, legs=((-3.5, 0), (2.0, 0), (-2.5, 0), (3.0, 0))),
            rat(bob=-0.5, jaw=0, legs=((-2.0, 0), (4.0, 0), (-1.0, 0), (5.0, 0)), extra=lambda r: smear(r, [(5, -6), (7, -5), (9, -3)], "bone", 4)),
            rat(jaw=1), rat(), rat()]
    spawn = []
    for i in range(3):
        r = R(); heap(r, 0, 0, 8, 6, seed=5, h=1.0 - 0.3 * i); bone_bits(r, 0, -3, i, 5, seed=7, z=3); spawn.append(r.resolve())
    d = []
    for i in range(3):
        r = R(); heap(r, 0, 0, 7 + i, 5, seed=8, h=0.8 - 0.2 * i); bone_bits(r, 0, -3, i, 4, seed=9, z=3); d.append(r.resolve())
    d = [rat(bob=1.0, jaw=1)] + d
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.06] * 6), ("Bite", bite, [0.08, 0.08, 0.05, 0.08, 0.1, 0.1]),
             ("Spawn", spawn, [0.08, 0.08, 0.1])]
    anims += tail_anims(idle[0], d, [0.08, 0.1, 0.1, 0.4], rat(bob=1.0, jaw=1))
    return sheet("OssBoneRat", anims, out)


SYNC["OssBoneRat"] = {"Bite": [("BITE: jaws at (8, -4); box 9 x 9 at (7, -4)", 2)]}


# ================================================================== the god portrait and the gold idol (29 x 24 portrait cells)
DEITY_SKULL = """
....LHHHHL....
..LHHHHHHHLB..
.LHHHLLLLLLBS.
LHHLLLLLLLLLBS
LHkkkLLLLkkkBS
LLkeekLLkeekBS
SLkkkBLLBkkkBS
.SLBBBnnBBBBS.
..SLBBnnBBBS..
...STtTtTtS...
...SBTtTtTBS..
....SSSSSSS...
"""
GOLD = {"H": ("gold", 4), "L": ("gold", 3), "B": ("gold", 2), "S": ("gold", 1), "K": ("gold", 0), "k": ("gold", 0), "n": ("gold", 0),
        "e": ("mglow", 3), "E": ("mglow", 4), "T": ("gold", 4), "t": ("gold", 0)}


def idol(tier, k=0):
    """The gold reliquary idol: T1 the skull on a plinth, T2 on a stack of three, T3 on a ribcage throne with three plates."""
    r = Rig()
    base = 9.0
    if tier == 1:
        r.poly([(-8, base), (8, base), (6, base - 3), (-6, base - 3)], "gold", 0, normal=(-0.2, -0.6, 0.8))
        sy = base - 3
    elif tier == 2:
        for i, x in enumerate((-6.0, 6.0, 0.0)):
            skullp(r, x, base, "S", 0.2 + i * 0.1, legend=dict(GOLD, e=("mglow", 2)))
        sy = base - 3
    else:
        # ribcage throne
        for i in range(3):
            y0 = base - 1 - i * 4
            r.polyline([(-4, y0), (-10, y0 - 1), (-12, y0 - 4), (-11, y0 - 7)], "gold", -0.5 + i * 0.01, tones=[3, 3, 2])
            r.polyline([(4, y0), (10, y0 - 1), (12, y0 - 4), (11, y0 - 7)], "gold", -0.5 + i * 0.01, tones=[2, 2, 1])
        for i, x in enumerate((-6.0, 6.0, 0.0)):
            skullp(r, x, base, "S", 0.2 + i * 0.1, legend=dict(GOLD, e=("mglow", 2)))
        sy = base - 3
    # the reliquary skull, a crown of finger bones, garnet eyes
    r.stamp(DEITY_SKULL, 0, sy, 1.0, dict(GOLD, e=("mglow", 3 if k % 2 == 0 else 4)), pivot=(7, 12))
    top = sy - 12
    for i in range(5):
        x = -5 + i * 2.5
        r.line(x, top + 1, x, top - 1 - (1 if i == 2 else 0), "gold", 1.1, tone=4 if i < 3 else 3)
    # crossed arm bones in front like a seal
    r.line(-7, sy - 1, 7, sy - 6, "gold", 2.0, tone=4); r.line(-7, sy - 6, 7, sy - 1, "gold", 1.9, tone=2)
    for (x, y) in ((-7, sy - 1), (7, sy - 6), (-7, sy - 6), (7, sy - 1)): r.dot(x, y, "gold", 4, 2.1)
    if tier == 3:
        for j in range(3):
            a = math.radians(k * 30 + j * 120)
            x, y = 10 * math.cos(a), top + 2 + 2.5 * math.sin(a)
            r.ell(x, y, 1.4, 1.6, "gold", 3.0 if math.sin(a) > 0 else -1.0, bias=0.2)
        ring(r, 0, top + 2, 10, 2.5, "gold", 1, -1.5, n=28)
    return r.resolve(floor=False)


def fx_idol(out):
    t3 = [idol(3, k) for k in range(4)]
    fx("DeityOssIdol", (29, 24), (14, 13), [("Idle", t3, [0.3, 0.2, 0.3, 0.2]), ("T1", [idol(1, k) for k in range(2)], [0.4, 0.4]),
                                           ("T2", [idol(2, k) for k in range(2)], [0.4, 0.4]), ("T3", t3, [0.3, 0.2, 0.3, 0.2])], out)


def fx_deity(out):
    from deity_portraits import frames  # the god portrait, drawn to DeityZhekra's standard
    fx("DeityOssivar", (29, 24), (14, 12), [("Idle", frames("ossivar", (14, 12)), [0.16, 0.16, 0.16, 0.16])], out)


JOBS = [("FxBonePile", fx_pile), ("FxBonePlate", fx_plate), ("FxOssSkull", fx_skull), ("FxOssScent", fx_scent),
        ("FxOssSplinter", fx_splinter), ("FxOssCaw", fx_caw), ("FxOssEyeFlare", fx_eye), ("FxOssPileGlow", fx_glow),
        ("FxOssWatchRing", fx_watch), ("FxOssDirtLegs", fx_dirt_legs), ("FxOssDigHole", fx_dig), ("FxOssPounceDust", fx_dust),
        ("FxOssHowl", fx_howl), ("FxBoneShard", fx_shard), ("FxMarrowBolt", fx_bolt), ("FxOssSpear", fx_spear),
        ("FxOssHarpoon", fx_harpoon), ("FxOssCrow", fx_crow), ("FxOssDiveShadow", fx_dive), ("FxOssHeadstone", fx_headstone),
        ("FxOssCrack", fx_cross), ("FxOssGasCone", fx_cone), ("FxOssGrimRing", fx_grim_ring), ("FxOssRib", fx_rib),
        ("FxSpikeRing", fx_spike_ring), ("OssBoneRat", rat_sheet), ("DeityOssIdol", fx_idol),
        ("DeityOssivar", fx_deity)]
