"""Ysveld tier 3, part one: Widow Matron, Loom Widow, Hoarfrost Tarantula, Hoarclaw, Pale Empress, Glasswing. Built
through ysveld_v2_rigs.py. T3 idle limit 42 x 40; none is smaller than the sprite it replaces."""
import math
from ysveld_v2_rigs import (Rig, Xf, chain, ik, lerp, lerp_pt, spider, moth, wing, antenna, robe, crystal, sparkle, leg,
                            knee_up, arc_smear, snow_puff, flakes, rime_fringe, shadow, sheet, tail_anims)
from ysveld_v2_t2 import arm


def egg_sac(r, x, y, z, rad=1.6):
    r.ell(x, y, rad, rad * 1.1, "web", z, bias=0.15)
    r.dot(x - 0.4, y - 0.4, "frost", 4, z + 0.01)
    r.dot(x + 0.5, y + 0.6, "ice", 2, z + 0.01)


# ================================================================== WIDOW MATRON: a huge pale widow, red hourglass, egg sacs
def matron(phase=0.0, stride=0.0, lean=0.0, cy=-11.0, fang=0.0, front=None, wrap=False, pulse=0.0, abd_dy=0.0,
           eye="eye", extra=None, sacs=3, lift=None):
    r = Rig(1.05)
    s = 2.0
    (ax, ay), (hx, hy) = spider(
        r, cx=6.0, cy=cy, s=s, phase=phase, stride=stride, lean=lean, abd=(5.0 + pulse * 0.3, 4.4 + pulse * 0.3),
        abd_at=(-5.6, -3.6 + abd_dy), ceph=(2.7, 2.1), legs=(6.0, 6.5), spread=(8.0, 4.0, -3.4, -7.6),
        mats=("chit", "chit", "chit"), eyes=((1.6, -0.9), (0.9, -1.2), (2.2, -0.3)), eye_mat=eye, fang=fang, front=front,
        knee_h=(5.6, 5.0, 4.8, 5.4), leg_rad=(0.65, 0.5, 0.35), near_z=0.5, lift=lift)
    # the red hourglass on the underside of the abdomen (glowing while she can wrap)
    gx, gy = ax + 0.5, ay + 6.0
    m, t = ("rglow", 4) if wrap else ("red", 3)
    for dx, dy in ((-1, -1), (0, -1), (1, -1), (0, 0), (-1, 1), (0, 1), (1, 1)):
        r.dot(gx + dx, gy + dy, m, t if dy != 0 else t - 1, 0.6)
    if wrap:
        for (dx, dy) in ((-3, 0), (3, -1), (0, 3), (-2, -3)):
            r.dot(gx + dx, gy + dy, "rglow", 2, 0.61)
    # hoarfrost on the dark abdomen: a crest of rime along its top and frost in its folds
    for i in range(-7, 8):
        y = ay - 8.6 * math.sqrt(max(0.0, 1 - (i / 9.5) ** 2)) + 0.8
        r.dot(ax + i, y, "frost", 4 if i < 2 else 3, 0.3)
        if i % 2 == 0: r.dot(ax + i, y + 1, "frost", 3, 0.3)
    for k in (-3, 0, 3):
        r.dot(ax - 6.0, ay + k, "ice", 3, 0.3); r.dot(ax - 5.0, ay + k + 1, "ice", 2, 0.3)
    # her egg sacs carried on her back, and one clinging to a leg
    for k, (ex, ey) in enumerate(((ax - 4.0, ay - 9.0), (ax + 2.0, ay - 10.0), (hx - 2.0, hy + 6.0))[:sacs]):
        egg_sac(r, ex, ey, 2.8 + k * 0.01, rad=2.2 if k < 2 else 1.6)
    if extra: extra(r)
    return r.resolve()


def matron_corpse(stage):
    r = Rig(1.0)
    r.ell(-4.0, -6.0, 9.0, 6.0, "web", 0.0, bias=0.1)
    for dx, dy in ((-1, -1), (0, -1), (1, -1), (0, 0), (-1, 1), (0, 1), (1, 1)):
        r.dot(-4.0 + dx, -12.0 + dy, "red", 2, 0.5)
    r.ell(8.0, -4.0, 5.0, 3.6, "chit", 0.3)
    for i in range(4):
        x = 0.0 + i * 3.6
        r.tube([(x, -8.0), (x - 2 + i, -17.0 + stage * 3), (x + 3.0, -12.0 + stage * 2)], [1.2, 1.0, 0.7], "ice", 1.0 + i * 0.01)
    for (ex, ey) in ((-15.0, -2.0), (14.0, -2.0)): egg_sac(r, ex, ey, 1.2)
    return r.resolve()


def matron_sheet(out):
    Mt = matron
    idle = [Mt(cy=-11.0 + [0, 0.3, 0.6, 0.3][i], pulse=[0, 0.5, 1, 0.5][i], fang=[0, 0, 0.5, 0][i]) for i in range(4)]
    run = [Mt(phase=i / 6.0, stride=1.0, lean=3, cy=-11.4 + 0.6 * abs(math.sin(i / 6 * math.tau))) for i in range(6)]
    wrap_idle = [Mt(cy=-11.0 + [0, 0.3, 0.6, 0.3][i], pulse=[0, 0.5, 1, 0.5][i], fang=[0.6, 0.9, 1.2, 0.9][i], wrap=True) for i in range(4)]
    wrap_run = [Mt(phase=i / 6.0, stride=1.0, lean=3, cy=-11.4 + 0.6 * abs(math.sin(i / 6 * math.tau)), wrap=True) for i in range(6)]
    # Impale (8): she rears, front legs high (0-2), DRIVES them into the floor ahead (3-4: hit at 4, tips at (24, 0)), hold, pull
    imp = [Mt(lean=-6, cy=-12.0, front=((4.0, -8.0), (3.5, -7.0))),
           Mt(lean=-14, cy=-13.0, abd_dy=1.0, front=((5.0, -12.0), (4.0, -11.0), (6.0, -6.0), (5.0, -5.0)), fang=1.4),
           Mt(lean=-18, cy=-13.6, abd_dy=1.4, front=((6.0, -14.0), (5.0, -13.0), (7.0, -8.0), (6.0, -7.0)), fang=1.8),
           Mt(lean=10, cy=-10.0, front=((9.0, 2.0), (8.0, 2.0), (9.0, 3.0), (8.5, 3.0)), fang=1.8,
              extra=lambda r: arc_smear(r, 12, -14, 12, -100, 20, "snow", 2)),
           Mt(lean=14, cy=-9.4, front=((9.5, 5.0), (8.5, 5.0), (9.5, 5.5), (9.0, 5.5)), fang=0.0,
              extra=lambda r: [snow_puff(r, 24, 0, 0, 1.4), sparkle(r, 25, -3, 1, "white"), sparkle(r, 21, -2, 2, "white")]),
           Mt(lean=12, cy=-9.6, front=((9.5, 5.0), (8.5, 5.0), (9.5, 5.5), (9.0, 5.5)), extra=lambda r: snow_puff(r, 24, 0, 1, 1.4)),
           Mt(lean=4, cy=-10.6), Mt()]
    # Brood (8): the abdomen swells (0-3), she lowers it and sets two frozen sacs down (4-5: thrown at 5), rises (6-7)
    brood = [Mt(pulse=1.0), Mt(pulse=2.0, abd_dy=0.5), Mt(pulse=3.0, abd_dy=1.0, lean=-4), Mt(pulse=3.5, abd_dy=1.5, lean=-6),
             Mt(pulse=2.0, abd_dy=3.0, lean=-8, cy=-9.6, sacs=1, extra=lambda r: [egg_sac(r, -14, -3, 3), egg_sac(r, -10, -2, 3)]),
             Mt(pulse=0.5, abd_dy=2.0, lean=-4, cy=-10.0, sacs=1, extra=lambda r: [sparkle(r, -14, -7, 2, "white")]),
             Mt(pulse=0.0, abd_dy=0.5, sacs=2), Mt(sacs=2)]
    d0 = Mt(lean=-12, eye="white", fang=1.6, front=((4.0, -9.0), (3.0, -8.0)))
    d1 = Mt(lean=-24, cy=-8.0, eye="white", front=((2.0, -12.0), (1.0, -11.0)), sacs=1)
    knock = Mt(lean=-12, eye="white", fang=1.2)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Impale", imp, [0.12, 0.12, 0.12, 0.05, 0.08, 0.14, 0.1, 0.1]),
             ("Brood", brood, [0.1, 0.1, 0.1, 0.12, 0.1, 0.1, 0.1, 0.12]),
             ("IdleWrap", wrap_idle, [0.12, 0.1, 0.12, 0.1]), ("RunWrap", wrap_run, [0.08] * 6)]
    anims += tail_anims(idle[0], [d0, d1, matron_corpse(0), matron_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvMatron", anims, out, scale=4)


# ================================================================== LOOM WIDOW: a veiled woman over a widow's body, a hand loom
LOOM_LEG = {"v": ("veil", 3), "V": ("veil", 4), "u": ("veil", 2), "w": ("veil", 1), "s": ("skin", 3), "S": ("skin", 4),
            "k": ("skin", 2), "e": ("eye", 3), "E": ("eye", 4), "m": ("silk", 0), "r": ("red", 2)}
LOOM_HEAD = {
    # pivot (3, 8): the neck. A long lace veil over her head and shoulders, a pale face, ice-blue eyes, dark lips
    "calm": """
..vVv..
.vVVVvu
vVsSSku
vVeSeku
vVsSsku
uvsmskw
uvvkvuw
uu...ww
u.....w
""",
    "hurt": """
..vVv..
.vVVVvu
vVsSSku
vVmSmku
vVsmsku
uvsmskw
uvvkvuw
uu...ww
u.....w
""",
}


def loom_frame(r, x, y, ang, z, threads=True):
    """The hand loom: a wooden frame strung with frost silk, a silver spool on its side."""
    T = Xf(ang, (x, y))
    pts = [T(x - 1, y - 4), T(x + 5, y - 4), T(x + 5, y + 3), T(x - 1, y + 3)]
    r.polyline(pts + [pts[0]], "wood", z, tone=2)
    r.line(*T(x - 1, y - 4), *T(x - 1, y + 3), "wood", z, tone=3)
    if threads:
        for i in range(0, 5, 2):
            r.line(*T(x + i, y - 3), *T(x + i, y + 2), "web", z - 0.01, tone=3)
    r.ell(*T(x + 6.2, y - 0.5), 1.0, 1.6, "silver", z + 0.01, bias=0.2)


def loom_widow(phase=0.0, stride=0.0, lean=0.0, cy=-7.0, bob=0.0, hand=(7.0, -19.0), hand2=(5.0, -20.0), loom=True,
               loom_at=None, face="calm", whip=None, line=None, extra=None):
    r = Rig(1.15)
    s = 1.55
    (ax, ay), (hx, hy) = spider(r, cx=2.0, cy=cy, s=s, phase=phase, stride=stride, lean=lean, abd=(5.0, 4.0), abd_at=(-5.0, -1.0),
                                ceph=(3.4, 2.6), legs=(5.6, 6.0), spread=(8.0, 4.0, -3.4, -7.6), mats=("chit", "chit", "silk"),
                                eyes=(), knee_h=(4.0, 3.6, 3.4, 3.8), leg_rad=(0.7, 0.55, 0.4), near_z=0.5)
    for i in range(-3, 4, 2): r.dot(ax + i, ay - 6.0, "frost", 4, 0.3)
    r.dot(ax - 1, ay + 1, "red", 2, 0.3); r.dot(ax, ay + 2, "red", 3, 0.3); r.dot(ax + 1, ay + 1, "red", 2, 0.3)
    # the woman rises from the front of the spider body: a silk bodice, the veil's long fall down her back
    T = Xf(lean, (hx, hy))
    wx, wy = T(hx + 0.5, hy - 2.5 + bob)
    r.poly([(wx - 3.0, wy), (wx + 3.0, wy), (wx + 2.4, wy - 9.0), (wx - 2.6, wy - 9.0)], "silk", 1.8, curve=0.8)
    r.poly([(wx - 2.0, wy - 9.0), (wx - 7.5, wy - 1.0), (wx - 9.5, wy + 3.0), (wx - 3.0, wy - 2.0)], "veil", 1.0, bias=-0.1)
    for k in range(3): r.dot(wx - 4.0 - k * 1.6, wy - 4.0 + k * 2.0, "veil", 4, 1.05)
    sh = (wx, wy - 8.0)
    arm(r, (sh[0] - 1.5, sh[1] + 0.5), hand2, "skin", 1.6, 4.0, 4.0, rad=(0.9, 0.8, 0.7), bias=-0.25)
    if loom:
        lx, ly = loom_at or (hand[0] - 1.0, hand[1] + 1.0)
        loom_frame(r, lx, ly, 0.0, 2.6)
    arm(r, (sh[0] + 1.5, sh[1] + 0.5), hand, "skin", 2.7, 4.0, 4.0, rad=(0.9, 0.8, 0.7))
    r.stamp(LOOM_HEAD[face], sh[0] + 0.5, sh[1] - 0.5, 3.0, LOOM_LEG, pivot=(3, 8))
    if whip:
        r.polyline(whip, "web", 3.5, tone=4)
        r.polyline([(p[0], p[1] + 1) for p in whip[1:]], "silk", 3.4, tone=2)
    if line:
        r.polyline(line, "web", 3.5, tone=3)
    if extra: extra(r)
    return r.resolve()


def loom_corpse(stage):
    r = Rig(1.0)
    r.ell(-4.0, -3.0, 7.0, 3.2, "silk", 0.0)
    r.ell(4.0, -2.8, 4.0, 2.4, "chit", 0.3)
    r.poly([(6.0, -1.0), (16.0, -0.5), (15.0, -3.5), (7.0, -4.5)], "silk", 0.6)
    r.poly([(8.0, -4.0), (20.0, -0.5), (18.0, -0.5)], "veil", 0.7)
    r.stamp(LOOM_HEAD["hurt"], 18.0, -1.0, 1.0, LOOM_LEG, pivot=(3, 8))
    loom_frame(r, -12.0, -2.0, 70 if stage else 40, 1.2)
    for i in range(4):
        x = -6.0 + i * 3.0
        r.tube([(x, -5.0), (x, -10.0 + stage * 2), (x + 2.0, -7.0 + stage)], [0.7, 0.55, 0.4], "chit", 1 + i * 0.01)
    return r.resolve()


def loom_sheet(out):
    L = loom_widow
    idle = [L(bob=[0, 0.3, 0.6, 0.3][i], hand=(7.0, -19.0 + [0, 0.3, 0.6, 0.3][i])) for i in range(4)]
    run = [L(phase=i / 6.0, stride=1.0, lean=4, bob=-0.4 * abs(math.sin(i / 6 * math.tau))) for i in range(6)]
    # Lash (7): the whip arm draws back (0-1), cracks the silk along the floor (2-3: hit at 3, reaching (28, -2)), recoil
    lash = [L(hand2=(-1.0, -24.0), lean=-4, whip=[(-1, -24), (-4, -28), (-7, -27)]),
            L(hand2=(-3.0, -26.0), lean=-8, whip=[(-3, -26), (-6, -30), (-10, -29)]),
            L(hand2=(9.0, -20.0), lean=6, whip=[(9, -20), (15, -16), (20, -10), (23, -7)],
              extra=lambda r: arc_smear(r, 2, -20, 14, -150, -20, "snow", 1)),
            L(hand2=(11.0, -15.0), lean=10, whip=[(11, -15), (17, -8), (23, -3), (29, -2)],
              extra=lambda r: [sparkle(r, 29, -3, 1, "white"), snow_puff(r, 26, 0, 0)]),
            L(hand2=(10.0, -14.0), lean=8, whip=[(10, -14), (16, -6), (22, -1), (27, -1)], extra=lambda r: snow_puff(r, 26, 0, 1)),
            L(hand2=(7.0, -17.0), lean=3), L()]
    # Spool (8): she lifts the loom (0-2), casts the line from the spool (3: the line leaves (12, -20)), reels (4-7)
    spool = [L(hand=(6.0, -22.0)), L(hand=(5.0, -25.0), lean=-4), L(hand=(4.0, -27.0), lean=-8, extra=lambda r: sparkle(r, 9, -27, 2, "white")),
             L(hand=(10.0, -21.0), lean=6, line=[(12, -21), (18, -20), (24, -19)], extra=lambda r: sparkle(r, 24, -19, 1, "white")),
             L(hand=(9.0, -21.0), lean=4, line=[(12, -21), (20, -19), (30, -17)]), L(hand=(8.0, -20.0), lean=2, line=[(12, -20), (26, -18)]),
             L(hand=(7.0, -19.0)), L()]
    d0 = L(lean=-10, face="hurt", hand=(4.0, -22.0), hand2=(-2.0, -22.0))
    d1 = L(lean=-24, face="hurt", cy=-5.5, hand=(2.0, -18.0), hand2=(-4.0, -17.0), loom=False)
    knock = L(lean=-12, face="hurt", hand=(5.0, -21.0), hand2=(-1.0, -21.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Lash", lash, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Spool", spool, [0.1, 0.1, 0.12, 0.06, 0.1, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, loom_corpse(0), loom_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvLoom", anims, out, scale=4)


# ================================================================== HOARFROST TARANTULA: shaggy ice-stiff fur, brood on its back
def shaggy(r, cx, cy, rx, ry, z, seed=1, mat="fur", tips="frost", n=22, ice="ice"):
    """Fur clumps over an ellipsoid: spikes of fur standing off the top and back edge, icicle-blue in the shadows."""
    import random
    rnd = random.Random(seed)
    r.ell(cx, cy, rx, ry, mat, z, bias=0.05)
    for i in range(n):
        a = math.radians(-200 + i * 220.0 / n + rnd.uniform(-4, 4))
        x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        L = 1.2 + rnd.random() * 1.6
        r.line(x, y, x + math.cos(a) * L, y + math.sin(a) * L, tips if math.sin(a) < -0.3 else mat, z + 0.01,
               tone=4 if (math.cos(a) < 0.2 and math.sin(a) < -0.3) else 2)
    for i in range(14):
        a = rnd.uniform(-2.8, 2.6); d = rnd.uniform(0.3, 0.85)
        x, y = cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d
        r.line(x, y, x + 0.4, y + 1.4, ice, z + 0.02, tone=2 + (i % 3 == 0) * 2)       # icicles frozen in the fur


def brood_rider(r, x, y, z, k):
    """A Broodling clinging in the fur: a pale little body, two legs, a red fleck."""
    r.ell(x, y, 1.7, 1.2, "frost", z, bias=0.2)
    r.line(x - 1.5, y + 0.5, x - 2.5, y + 1.5, "chit", z, tone=1)
    r.line(x + 1.5, y + 0.5, x + 2.5, y + 1.5, "chit", z, tone=1)
    r.dot(x + 0.8, y - 0.3, "eye", 3, z + 0.01)
    r.dot(x - 0.3, y - 0.6, "red", 3, z + 0.01)


def tarantula(phase=0.0, stride=0.0, lean=0.0, cy=-7.5, fang=0.0, front=None, brood=3, abd_ang=0.0, eye="eye",
              extra=None, hairs=None):
    r = Rig(1.08)
    s = 1.6
    furry = lambda r_, hip, kn, foot, z, side: [r_.dot(*lerp_pt(kn, foot, t), "frost" if side == 0 else "fur", 3 if side == 0 else 1, z + 0.01)
                                                for t in (0.3, 0.6)]
    (ax, ay), (hx, hy) = spider(r, cx=4.0, cy=cy, s=s, phase=phase, stride=stride, lean=lean, abd=(0.1, 0.1), abd_at=(0, 0),
                                ceph=(3.8, 3.0), legs=(5.4, 5.8), spread=(8.0, 4.2, -3.6, -7.8), mats=("fur", "fur", "fur"),
                                eyes=((2.6, -1.6), (1.6, -1.9), (3.2, -0.9)), eye_mat=eye, fang=fang, front=front,
                                knee_h=(3.4, 3.0, 3.0, 3.2), leg_rad=(1.25, 1.0, 0.7), near_z=0.5, hairs=furry)
    T = Xf(lean, (4.0, cy + 2 * s))
    a = math.radians(abd_ang)
    bx, by = T(4.0 - 9.5 * math.cos(a), cy - 2.0 - 9.5 * math.sin(a) * 0.5)
    shaggy(r, bx, by, 9.0, 7.0, 0.2, seed=4)
    for k, (dx, dy) in enumerate(((-3.0, -5.6), (2.5, -5.0), (-6.0, -2.8))[:brood]):
        brood_rider(r, bx + dx, by + dy, 1.4 + k * 0.01, k)
    if hairs:
        for (x, y, t) in hairs: r.line(x, y, x + 2, y - 0.5, "frost", 6.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def tarantula_corpse(stage):
    r = Rig(1.0)
    shaggy(r, -4.0, -5.5, 9.0, 5.5, 0.0, seed=4)
    r.ell(9.0, -3.5, 4.5, 3.0, "fur", 0.3)
    for i in range(4):
        x = 2.0 + i * 3.0
        r.tube([(x, -7.0), (x - 1, -13.0 + stage * 2), (x + 2.5, -10.0 + stage * 2)], [1.1, 0.9, 0.6], "fur", 1 + i * 0.01)
    return r.resolve()


def tarantula_sheet(out):
    Ta = tarantula
    def idle(b): return [Ta(cy=-7.5 + [0, 0.3, 0.6, 0.3][i], fang=[0, 0, 0.5, 0][i], brood=b, abd_ang=[0, 2, 4, 2][i]) for i in range(4)]
    def run(b): return [Ta(phase=i / 6.0, stride=1.0, lean=3, brood=b, cy=-7.8 + 0.5 * abs(math.sin(i / 6 * math.tau))) for i in range(6)]
    # Bite (7): rear (0-1), lunge (2), BITE (3: fangs at (16, -4)), hold, back
    bite = [Ta(lean=-6, fang=1.0, brood=2), Ta(lean=-12, fang=1.8, cy=-8.4, front=((5.0, -6.0), (4.0, -5.0)), brood=2),
            Ta(lean=10, fang=1.8, front=((7.0, -1.0), (6.0, -1.0)), brood=2, extra=lambda r: r.line(-6, -14, 2, -12, "snow", 5, tone=2)),
            Ta(lean=16, fang=0.0, front=((8.0, 3.0), (7.0, 3.0)), brood=2,
               extra=lambda r: [sparkle(r, 17, -4, 1, "white"), snow_puff(r, 15, 0, 0)]),
            Ta(lean=12, brood=2, extra=lambda r: snow_puff(r, 15, 0, 1)), Ta(lean=4, brood=2), Ta(brood=2)]
    # Flick (8): it braces and swings its abdomen up (0-3), FLICKS a spray of frozen hairs forward (4), settles
    flick = [Ta(abd_ang=-10, brood=2), Ta(abd_ang=-25, lean=4, brood=2), Ta(abd_ang=-40, lean=8, brood=2),
             Ta(abd_ang=-50, lean=10, brood=2, extra=lambda r: sparkle(r, -2, -26, 2, "white")),
             Ta(abd_ang=-20, lean=-2, brood=2, hairs=[(8, -22, 4), (12, -17, 4), (14, -12, 3), (10, -27, 3), (16, -20, 2)]),
             Ta(abd_ang=-5, lean=-4, brood=2, hairs=[(18, -20, 2), (20, -14, 2), (16, -26, 1)]), Ta(abd_ang=0, brood=2), Ta(brood=2)]
    d0 = Ta(lean=-12, eye="white", fang=1.6, brood=0)
    d1 = Ta(lean=-24, cy=-6.0, eye="white", front=((2.0, -8.0), (1.0, -7.0)), brood=0)
    knock = Ta(lean=-12, eye="white", fang=1.2, brood=2)
    anims = [("Idle", idle(3), [0.16, 0.14, 0.16, 0.14]), ("Run", run(3), [0.08] * 6),
             ("Bite", bite, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Flick", flick, [0.1, 0.1, 0.1, 0.12, 0.06, 0.1, 0.1, 0.1]),
             ("Idle2", idle(2), [0.16, 0.14, 0.16, 0.14]), ("Run2", run(2), [0.08] * 6),
             ("Idle1", idle(1), [0.16, 0.14, 0.16, 0.14]), ("Run1", run(1), [0.08] * 6),
             ("Idle0", idle(0), [0.16, 0.14, 0.16, 0.14]), ("Run0", run(0), [0.08] * 6)]
    anims += tail_anims(idle(3)[0], [d0, d1, tarantula_corpse(0), tarantula_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvTarantula", anims, out, scale=4)


# ================================================================== HOARCLAW: a low ice crab, two huge crystal pincers
def pincer(r, base, ang, size, open_, z, mat="glass", bias=0.0):
    """A big crab claw from its wrist: the palm, a fixed finger and a moving finger opened `open_` degrees."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); px, py = -uy, ux
    palm = (base[0] + ux * size * 0.45, base[1] + uy * size * 0.45)
    r.ell(palm[0], palm[1], size * 0.5, size * 0.33, mat, z, ang=ang, bias=bias + 0.1)
    tip1 = (palm[0] + ux * size * 0.75 + px * size * 0.05, palm[1] + uy * size * 0.75 + py * size * 0.05)
    r.tube([(palm[0] + px * size * 0.15, palm[1] + py * size * 0.15), tip1], [size * 0.18, size * 0.06], mat, z + 0.01, bias=bias)
    b = math.radians(ang - open_)
    tip2 = (palm[0] - px * size * 0.15 + math.cos(b) * size * 0.7, palm[1] - py * size * 0.15 + math.sin(b) * size * 0.7)
    r.tube([(palm[0] - px * size * 0.15, palm[1] - py * size * 0.15), tip2], [size * 0.16, size * 0.05], mat, z + 0.02, bias=bias + 0.1)
    r.dot(tip1[0], tip1[1], "white", 4, z + 0.03); r.dot(tip2[0], tip2[1], "white", 4, z + 0.03)
    return tip1, tip2


def hoarclaw(phase=0.0, stride=0.0, lean=0.0, cy=-7.0, claw=(0.0, 0.0), reach=0.0, open_=(20.0, 20.0), eye="eye", extra=None,
             tail=0.0, raise_=2.5):
    r = Rig(1.08)
    # legs: three pairs under a low wide shell
    for side, zz, bias in ((1, -3.0, -0.35), (0, 0.3, 0.0)):
        for i in range(3):
            ph = (phase + 0.33 * i + 0.5 * side) % 1.0
            sw = math.sin(ph * math.tau) * stride * 2.0
            up = max(0.0, math.sin(ph * math.tau)) * stride * 1.4
            hx, hy = -4.0 + i * 3.5, cy + 1.5
            fx = hx + (-5.0 + i * 3.0) + sw + (1.0 if side else 0.0)
            leg(r, (hx, hy), (fx, -up), 4.0, 4.5, "shell", zz + i * 0.01, rad=(1.0, 0.8, 0.5), bias=bias,
                knee=(lerp(hx, fx, 0.4), cy - 2.0))
    # tail: a short segmented scorpion tail curling up behind with an ice barb
    tp = chain(-9.0, cy - 0.5, [(3.6, 210 - tail * 0.3), (4.6, 245 - tail * 0.6), (4.6, 280 - tail), (4.0, 320 - tail), (2.6, 5 - tail)])
    r.tube(tp, [2.0, 1.8, 1.5, 1.3, 1.1, 0.8], "shell", -1.0, bias=-0.1)
    for p_ in tp[1:-1]: r.dot(p_[0], p_[1] - 1.2, "frost", 4, -0.95)
    r.line(tp[-1][0], tp[-1][1], tp[-1][0] + 2.0, tp[-1][1] + 1.5, "glass", -0.9, tone=4)
    # the shell: a low, wide carapace with a crest of rime
    T = Xf(lean, (0.0, cy))
    r.ell(*T(-1.0, cy - 1.6), 9.5, 7.2, "shell", 0.5, bias=0.05)
    r.ell(*T(-2.0, cy - 3.6), 6.5, 1.6, "frost", 0.52, bias=0.1)
    for x in range(-8, 8, 3): r.dot(*T(x, cy - 4.8 + abs(x) * 0.1), "frost", 4, 0.53)
    for x in (-5, -1, 3): r.dot(*T(x, cy + 1.0), "shell", 1, 0.53)
    ex, ey = T(7.6, cy - 2.0)
    r.dot(ex, ey - 1, eye, 3, 0.7); r.dot(ex + 1.6, ey - 0.6, eye, 3, 0.7)
    r.line(ex, ey - 1, ex - 0.5, ey - 3, "shell", 0.6, tone=3); r.line(ex + 1.6, ey - 0.6, ex + 1.8, ey - 2.6, "shell", 0.6, tone=3)
    # arms and the two huge pincers, held out front like a plough
    for k, (zz, b) in enumerate(((-2.0, -0.3), (2.0, 0.0))):
        sx, sy = T(6.0, cy + 0.5 - k * 0.5)
        wx, wy = sx + 3.0 + reach + claw[k], sy - 2.5 - raise_ + k * 1.6
        r.tube([(sx, sy), (sx + 2.5 + reach * 0.4, sy - 2.5 - raise_ * 0.5), (wx, wy)], [1.5, 1.4, 1.2], "shell", zz, bias=b)
        pincer(r, (wx, wy), -8 + k * 6 - raise_ * 2, 9.0 + k * 0.8, open_[k], zz + 0.1, bias=b)
    if extra: extra(r)
    return r.resolve()


def hoarclaw_corpse(stage):
    r = Rig(1.0)
    r.ell(-1.0, -3.6, 9.5, 3.6, "shell", 0.0)
    r.ell(-2.0, -6.0, 6.0, 1.4, "frost", 0.1)
    pincer(r, (8.0, -2.5), 10 if stage else -20, 8.0, 50, 0.5)
    pincer(r, (-12.0, -2.0), 190, 7.0, 40, -0.5, bias=-0.3)
    for i in range(3):
        r.tube([(-4 + i * 3.5, -1.0), (-5 + i * 3.5, -6.0 + stage * 1.5), (-3 + i * 3.5, -4.0 + stage)], [0.9, 0.7, 0.5], "shell", 1 + i * 0.01)
    return r.resolve()


def hoarclaw_sheet(out):
    Hc = hoarclaw
    idle = [Hc(cy=-6.0 + [0, 0.3, 0.5, 0.3][i], open_=([20, 26, 30, 24][i], [24, 18, 14, 20][i]), tail=[0, 4, 8, 4][i]) for i in range(4)]
    run = [Hc(phase=i / 6.0, stride=1.0, cy=-6.3 + 0.4 * abs(math.sin(i / 6 * math.tau)), lean=2, tail=4 * math.sin(i / 6 * math.tau),
              claw=(0.8 * math.sin(i / 6 * math.tau), -0.8 * math.sin(i / 6 * math.tau))) for i in range(6)]
    # Snap (7): both claws open wide and draw back (0-1), lunge and SNAP shut (2-3: hit at 3, at (20, -8)), hold, back
    snap = [Hc(reach=-2.0, open_=(45, 45), lean=-3), Hc(reach=-3.0, open_=(60, 60), lean=-6, raise_=1.0),
            Hc(reach=4.0, open_=(40, 35), lean=4, extra=lambda r: r.line(8, -12, 14, -12, "snow", 5, tone=2)),
            Hc(reach=6.0, open_=(0, 0), lean=6, extra=lambda r: [sparkle(r, 26, -10, 1, "white"), sparkle(r, 27, -6, 2, "white")]),
            Hc(reach=4.0, open_=(5, 5), lean=4), Hc(reach=1.0, open_=(15, 15)), Hc()]
    # Seize (8): rear, claws wide (0-1), lunge (2: the grab), CLAMP and hold (3-5), HURL: the claws fling up and out (6), settle
    seize = [Hc(reach=-2.0, open_=(55, 55), raise_=1.5, lean=-4), Hc(reach=-3.5, open_=(75, 75), raise_=2.5, lean=-8),
             Hc(reach=7.0, open_=(30, 30), lean=6, extra=lambda r: r.line(6, -11, 14, -11, "snow", 5, tone=2)),
             Hc(reach=6.0, open_=(5, 5), lean=4, claw=(1.0, 1.0)), Hc(reach=5.0, open_=(5, 5), lean=2, claw=(1.5, 1.5), cy=-6.4),
             Hc(reach=3.0, open_=(5, 5), lean=-4, raise_=2.0, cy=-6.6),
             Hc(reach=6.0, open_=(60, 60), lean=8, raise_=5.0, extra=lambda r: arc_smear(r, 14, -10, 8, 60, -60, "snow", 2)),
             Hc(reach=1.0, open_=(25, 25))]
    d0 = Hc(lean=-8, eye="white", open_=(60, 60), raise_=3.0)
    d1 = Hc(lean=-16, cy=-4.0, eye="white", open_=(70, 70), raise_=4.0)
    knock = Hc(lean=-10, eye="white", open_=(40, 40), reach=-2.0)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.07] * 6),
             ("Snap", snap, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Seize", seize, [0.12, 0.1, 0.06, 0.12, 0.14, 0.14, 0.08, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, hoarclaw_corpse(0), hoarclaw_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvHoarclaw", anims, out, scale=4)


# ================================================================== PALE EMPRESS: a moth empress, vast aurora wings, a frost crown
def aurora_bands(r, root, ang, length, z, phase=0, mats=("aurg", "aurp")):
    """Light shot through a wing: two thin curved ribbons along it, green and pink."""
    a = math.radians(ang)
    for k, m in enumerate(mats):
        pts = []
        for i in range(7):
            t = 0.2 + i * 0.11
            w = (k - 0.5) * 2.4 + math.sin(t * 6 + phase * 1.2 + k) * 0.8
            pts.append((root[0] + math.cos(a) * length * t - math.sin(a) * w, root[1] + math.sin(a) * length * t + math.cos(a) * w))
        r.polyline(pts, m, z, tone=3 if k == 0 else 2)


def empress(alt=12.0, flap=0.0, lean=0.0, body_dy=0.0, ant=0.0, phase=0, motes=None, storm=0, extra=None, eye="eye",
            fold=1.0, flare=False):
    r = Rig(1.22)
    cx, cy = 0.0, -alt + body_dy
    shadow(r, 0.0, -1.0, 8.0)
    hx, hy = moth(r, cx, cy, span=19.0 * fold, chord=13.5, flap=flap, fore="frost", hind="silk", body="fur", lean=lean,
                  spots=[(0.62, 0.0, "aurg", 3), (0.8, 1.5, "aurp", 3)], hspots=[(0.55, 0.0, "aurp", 3)], eye=eye, ant=ant,
                  far=0.85, abd=8.0, head_r=2.2, scallop=0.8, hind_span=0.62, rise=36, rim="ice")
    # icicles hanging from the hem of her hindwings
    for k, x in enumerate((-9, -6, -3, 4, 7, 10)):
        y = cy + 9.0 - abs(x) * 0.25
        r.tube([(x, y), (x + 0.2, y + 2.0 + (k % 2) * 1.5)], [0.7, 0.2], "ice", 2.0 if x > 0 else -2.5, bias=0.2)
    # aurora light on the near forewing
    aurora_bands(r, (cx + 0.6, cy - 0.6), -54 - flap, 19.0 * fold, 1.2, phase)
    aurora_bands(r, (cx - 0.6, cy - 0.6), -126 + flap, 16.0 * fold, -1.9, phase + 2)
    # the frost crown on her antennae: ice spikes between them
    for k, (dx, h) in enumerate(((-1.6, 3.0), (0.0, 4.2), (1.6, 3.0))):
        crystal(r, hx + dx + 0.5, hy - 2.0, h, 1.6, "ice", 0.8 + k * 0.01)
    if flare:
        for (x, y) in ((hx - 6, hy - 8), (hx + 7, hy - 9), (hx, hy - 12)):
            sparkle(r, x, y, 1, "aurg")
    if motes:
        for (x, y, k) in motes: sparkle(r, x, y, k, "aurp" if (x + y) % 2 else "aurg")
    if storm:
        flakes(r, [(8 + i * 2, -18 + (i * 5) % 9, 3 + (i % 2)) for i in range(storm)])
    if extra: extra(r)
    return r.resolve()


def empress_corpse(stage):
    r = Rig(1.0)
    wing(r, (-1.0, -3.0), -175, 14.0, 9.0, "web", -1.0, bias=-0.3, spots=[(0.6, 0.0, "aurg", 1)])
    wing(r, (1.0, -3.0), -8 - 6 * stage, 15.0, 10.0, "web", 1.0, spots=[(0.6, 0.0, "aurp", 2)])
    r.tube([(3.0, -3.0), (-1.0, -2.0), (-6.0, -1.5)], [2.2, 1.8, 1.0], "fur", 0.5)
    for k in range(3): crystal(r, 5.0 + k * 1.6, -4.0 + k * 0.5, 3.0, 1.4, "ice", 0.8, ang=70)
    return r.resolve()


def empress_sheet(out):
    E = empress
    idle = [E(alt=12.0 + [0, -0.6, -1.2, -0.6][i], flap=[-22, 4, 26, 4][i], ant=[0, 3, 6, 3][i], phase=i) for i in range(4)]
    run = [E(alt=12.5 + [0, -0.6, -1, -0.6, 0, 0.4][i], flap=[-30, -8, 22, 34, 12, -14][i], lean=8, phase=i) for i in range(6)]
    # Aurora (7): wings sweep high (0-1), a beat looses five aurora motes from (10, -18) (3), recover
    aur = [E(flap=-35, lean=-4), E(flap=-50, lean=-8, flare=True), E(flap=15, lean=4, motes=[(10, -20, 2)]),
           E(flap=35, lean=8, motes=[(14, -24, 1), (15, -19, 1), (14, -14, 1), (12, -28, 2), (12, -10, 2)]),
           E(flap=20, lean=4), E(flap=-5), E(flap=-20)]
    # Blizzard (8): she folds her wings round her (0-2), throws them open (3-4: the blizzard leaves at (12, -14) on 4), hangs
    bliz = [E(flap=-50, fold=0.85), E(flap=-70, fold=0.7, alt=13), E(flap=-80, fold=0.6, alt=13.5, flare=True),
            E(flap=10, fold=1.08, alt=12, flare=True, storm=4), E(flap=35, fold=1.1, alt=11.5, storm=7),
            E(flap=20, storm=5), E(flap=0, storm=2), E(flap=-15)]
    d0 = E(flap=-60, lean=-16, eye="white"); d1 = E(alt=7.0, flap=40, lean=-34, eye="white", fold=0.8)
    knock = E(flap=-50, lean=-20, eye="white")
    anims = [("Idle", idle, [0.11] * 4), ("Run", run, [0.07] * 6),
             ("Aurora", aur, [0.1, 0.12, 0.06, 0.08, 0.1, 0.1, 0.1]),
             ("Blizzard", bliz, [0.1, 0.1, 0.12, 0.06, 0.08, 0.12, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, empress_corpse(0), empress_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvEmpress", anims, out, scale=4)


# ================================================================== GLASSWING: a moth of clear ice glass, glass scythes for forelegs
def pane_wing(r, root, ang, length, width, z, bias=0.0, keen=False):
    """A wing like a pane of glass: angular, a bright leading edge, the frame lines inside it."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); px, py = -uy, ux
    P = lambda t, w: (root[0] + ux * length * t + px * w, root[1] + uy * length * t + py * w)
    pts = [P(0, 0), P(0.35, width * 0.55), P(1.0, width * 0.25), P(0.85, -width * 0.35), P(0.3, -width * 0.4)]
    r.poly(pts, "glass", z, bias=bias - 0.25, normal=(-0.3, -0.5, 1.0))
    r.polyline([pts[0], pts[1], pts[2], pts[3], pts[4], pts[0]], "glass", z + 0.005, tone=4)
    if keen: r.polyline([pts[0], pts[1], pts[2]], "cyan", z + 0.01, tone=3)
    r.line(*P(0.1, 0), *P(0.9, 0.0), "glass", z + 0.01, tone=1)
    r.line(*P(0.5, width * 0.4), *P(0.55, -width * 0.35), "glass", z + 0.01, tone=1)


def scythe(r, sh, ang, z, keen=False, length=8.0, bias=0.0):
    """A glass scythe foreleg: a thin upper arm, then a long curved blade."""
    a = math.radians(ang)
    el = (sh[0] + math.cos(a) * 3.5, sh[1] + math.sin(a) * 3.5)
    r.tube([sh, el], [0.8, 0.7], "glass", z, bias=bias)
    pts = []
    for i in range(6):
        t = i / 5.0
        b = math.radians(ang + 110 + t * 60)
        pts.append((el[0] + math.cos(b) * length * t, el[1] + math.sin(b) * length * t))
    r.polyline(pts, "cyan", z + 0.01, tone=4 if keen else 2)
    r.polyline([(p[0] + 0.0, p[1] + 1.0) for p in pts[1:-1]], "ice", z, tone=1)
    return pts[-1]


def glasswing(alt=10.0, flap=0.0, lean=0.0, body_dy=0.0, scy=(30.0, 40.0), keen=False, curl=0.0, eye="eye", extra=None,
              fold=1.0, stun=False):
    r = Rig(1.15)
    cx, cy = 0.0, -alt + body_dy
    shadow(r, 0.0, -1.0, 7.0)
    T = Xf(lean, (cx, cy))
    span = 17.0 * fold * (1 - curl * 0.55)
    # wings: angular panes; curl folds them round the body
    pane_wing(r, T(cx - 0.6, cy - 0.8), -125 + flap + curl * 40, span * 0.85, 10.0, -2.0, bias=-0.3, keen=keen)
    pane_wing(r, T(cx - 0.6, cy + 0.8), 160 - flap * 0.5 + curl * 30, span * 0.55, 7.0, -2.1, bias=-0.35)
    # body: a clear thorax, a long glass abdomen
    r.ell(*T(cx + 0.4, cy - 0.2), 3.0, 2.8, "ice", 0.0, bias=0.05)                       # thorax
    r.tube([T(cx, cy + 2.0), T(cx - 0.8, cy + 5.0), T(cx - 1.6, cy + 8.5)], [2.6, 2.0, 0.9], "ice", -0.1, bias=-0.05)
    for k in range(4):
        x, y = T(cx - 0.3 * k, cy + 2.6 + k * 1.6)
        r.line(x - 1.8 + k * 0.3, y, x + 1.8 - k * 0.3, y, "cyan", 0.01, tone=2)          # glowing seams of the glass abdomen
    hx, hy = T(cx + 2.2, cy - 3.4)
    r.ell(hx, hy, 2.4, 2.1, "ice", 0.3, bias=0.15)
    r.dot(hx + 1.2, hy, eye, 4, 0.5); r.dot(hx + 1.6, hy, eye, 4, 0.5); r.dot(hx - 0.4, hy - 0.4, eye, 3, 0.5)
    antenna(r, hx + 0.6, hy - 1.4, -70, 4.6, "glass", 0.2, feather=False)
    antenna(r, hx - 0.4, hy - 1.4, -100, 4.0, "glass", -0.5, feather=False, tone=2)
    pane_wing(r, T(cx + 0.6, cy + 0.8), 20 - flap * 0.5 - curl * 30, span * 0.6, 7.5, -1.0, bias=-0.05)
    pane_wing(r, T(cx + 0.6, cy - 0.8), -55 - flap - curl * 40, span, 11.0, -0.9, bias=0.05, keen=keen)
    # scythe forelegs, folded like a mantis
    for k, (zz, b) in enumerate(((-0.4, -0.3), (2.0, 0.0))):
        scythe(r, T(cx + 1.4, cy + 0.6 + k * 0.6), scy[k], zz, keen=keen and k == 1, bias=b)
    if stun:
        for (x, y) in ((hx - 3, hy - 5), (hx + 3, hy - 6), (hx, hy - 7)): sparkle(r, x, y, 2, "cyan")
    if extra: extra(r)
    return r.resolve()


def glasswing_corpse(stage):
    r = Rig(1.0)
    pane_wing(r, (-1.0, -2.0), -175, 11.0, 8.0, -1.0, bias=-0.3)
    pane_wing(r, (1.0, -2.0), -10 - 5 * stage, 12.0, 9.0, 1.0)
    r.tube([(3.0, -2.0), (-1.0, -1.6), (-6.0, -1.2)], [1.8, 1.4, 0.8], "glass", 0.5)
    if stage:
        for (x, y) in ((-9, -1), (8, -1), (12, -2)): r.dot(x, y, "glass", 4, 1)
    return r.resolve()


def glasswing_sheet(out):
    G = glasswing
    idle = [G(alt=9.0 + [0, -0.5, -1, -0.5][i], flap=[-20, 4, 24, 4][i], scy=(30 + [0, 4, 8, 4][i], 40 - [0, 4, 8, 4][i])) for i in range(4)]
    run = [G(alt=9.5 + [0, -0.5, -1, -0.5, 0, 0.4][i], flap=[-30, -8, 22, 34, 12, -14][i], lean=10) for i in range(6)]
    keen_idle = [G(alt=9.0 + [0, -0.5, -1, -0.5][i], flap=[-20, 4, 24, 4][i], keen=True) for i in range(4)]
    keen_run = [G(alt=9.5 + [0, -0.5, -1, -0.5, 0, 0.4][i], flap=[-30, -8, 22, 34, 12, -14][i], lean=10, keen=True) for i in range(6)]
    # Slash (7): scythes rise (0-1), dart in (2), SLASH (3: both blades sweep down at (14, -8)), follow, recover
    sl = [G(scy=(-20, -10), lean=-4), G(scy=(-60, -50), lean=-8, flap=-30),
          G(scy=(-30, -20), lean=12, alt=8, flap=10, extra=lambda r: r.line(-10, -10, -2, -10, "snow", 5, tone=2)),
          G(scy=(60, 70), lean=18, alt=7, flap=30, extra=lambda r: [arc_smear(r, 6, -9, 9, -70, 70, "cyan", 2), sparkle(r, 15, -6, 1, "white")]),
          G(scy=(80, 90), lean=12, alt=7.5), G(scy=(40, 50), lean=4), G()]
    # Cocoon (6): she folds her wings round herself (0-3), glass closes over her (4-5); Curled holds inside
    coc = [G(curl=0.2, flap=-20), G(curl=0.45, flap=-40, alt=8), G(curl=0.7, flap=-55, alt=7), G(curl=0.9, flap=-60, alt=6.5),
           G(curl=1.0, flap=-62, alt=6.0, scy=(80, 90)), G(curl=1.0, flap=-62, alt=6.0, scy=(80, 90))]
    curled = [G(curl=1.0, flap=-62, alt=6.0 + [0, 0.3][i], scy=(80, 90)) for i in range(2)]
    stunned = [G(alt=4.0 + [0, 0.5, 0, -0.3][i], flap=[30, 40, 30, 20][i], lean=[-14, -10, -16, -12][i], stun=True, scy=(90, 100)) for i in range(4)]
    d0 = G(flap=-50, lean=-16, eye="white"); d1 = G(alt=5.0, flap=40, lean=-34, eye="white", fold=0.8)
    knock = G(flap=-40, lean=-20, eye="white")
    anims = [("Idle", idle, [0.1] * 4), ("Run", run, [0.07] * 6),
             ("Slash", sl, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Cocoon", coc, [0.06, 0.06, 0.06, 0.06, 0.08, 0.1]), ("Curled", curled, [0.3, 0.3]),
             ("Stunned", stunned, [0.12, 0.12, 0.12, 0.12]),
             ("IdleKeen", keen_idle, [0.1] * 4), ("RunKeen", keen_run, [0.07] * 6)]
    anims += tail_anims(idle[0], [d0, d1, glasswing_corpse(0), glasswing_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvGlasswing", anims, out, scale=4)


JOBS = [("YsvMatron", matron_sheet), ("YsvLoom", loom_sheet), ("YsvTarantula", tarantula_sheet),
        ("YsvHoarclaw", hoarclaw_sheet), ("YsvEmpress", empress_sheet), ("YsvGlasswing", glasswing_sheet)]
SYNC = {
    "YsvMatron": {"Impale": [("IMPALE: the front legs strike the floor at (24, 0); box 22 x 14 at (22, -4)", 4)],
                  "Brood": [("two egg sacs are set down by the hero", 5)]},
    "YsvLoom": {"Lash": [("CRACK: the silk whip lies along the floor to (29, -2); box 24 x 12 at (20, -6)", 3)],
                "Spool": [("the line leaves the spool at (12, -20)", 3)]},
    "YsvTarantula": {"Bite": [("BITE: fangs at (17, -4); box 16 x 12 at (14, -5)", 3)],
                     "Flick": [("the hairs are flicked forward from (10, -20)", 4)]},
    "YsvHoarclaw": {"Snap": [("SNAP: the claws shut at (26, -8); box 16 x 14 at (20, -8)", 3)],
                    "Seize": [("GRAB: the claws close at (24, -8)", 2), ("HURL", 6)]},
    "YsvEmpress": {"Aurora": [("five motes leave at (10, -18)", 3)], "Blizzard": [("the blizzard leaves at (12, -14)", 4)]},
    "YsvGlasswing": {"Slash": [("SLASH: both scythes sweep down at (14, -8); box 16 x 14 at (14, -8)", 3)],
                     "Cocoon": [("the glass cocoon closes (FxYsvCocoon over her)", 4)]},
}
NOTES = {
    "YsvMatron": "IdleWrap / RunWrap: the hourglass glows red while her next Impale is doubled (Wrap).",
    "YsvTarantula": "Idle/Run carry 3 Broodlings in the fur, Idle2/Run2 two, Idle1/Run1 one, Idle0/Run0 none.",
    "YsvGlasswing": "Curled loops inside the cocoon; Stunned loops when it is cracked open; IdleKeen / RunKeen: the "
                    "scythes burn cyan while her next slash is doubled.",
}
