"""Ysveld tier 1 (Rimeling, Hoarmoth, Rime Shardling) and the Broodling. Built through ysveld_v2_rigs.py.
T1 idle limit 20 x 16."""
import math
from ysveld_v2_rigs import (Rig, Xf, chain, lerp, lerp_pt, spider, wing, moth, antenna, crystal, sparkle, arc_smear, snow_puff,
                            flakes, rime_fringe, shadow, sheet, tail_anims)


def frost_hairs(tone=3, mat="frost"):
    """Hoarfrost fringe along the lower leg (knee -> foot): a pixel of rime every 2 px under the shin."""
    def f(r, hip, kn, foot, z, side):
        if side == 1: return
        x, y = lerp_pt(kn, foot, 0.4)
        r.dot(x + (1 if foot[0] > hip[0] else -1), y, mat, tone, z + 0.003)
    return f


# ================================================================== RIMELING: a small frost spider with icicle fangs
def rimeling(phase=0.0, stride=0.0, lean=0.0, cy=-4.2, fang=0.0, snap=False, abd_dy=0.0, front=None, extra=None,
             glob=None, smear=None, dust=None, eye="eye", hurt=False):
    r = Rig()
    s = 0.95
    spider(r, cx=2.0, cy=cy, s=s, phase=phase, stride=stride, lean=lean, abd=(4.8, 3.8), abd_at=(-5.4, -2.0 + abd_dy),
           ceph=(3.4, 2.6), legs=(4.8, 5.4), spread=(9.0, 4.6, -4.0, -9.0), mats=("chit", "chit", "ice"), knee_h=(3.6, 3.0, 3.0, 3.4),
           eyes=((2.2, -1.2), (1.2, -1.5)), eye_mat=eye, fang=fang, fang_mat="white" if snap else "frost", front=front,
           hairs=frost_hairs(), leg_rad=(0.8, 0.6, 0.4))
    T = Xf(lean, (2.0, cy + 2 * s))
    # rime on the abdomen: a frosted crest along its top, and a pale chevron
    ax, ay = T(2.0 - 5.4 * s, cy + (-2.0 + abd_dy) * s)
    for i in range(-2, 3):
        r.dot(ax + i, ay - 3.4 * s, "frost", 4 if i < 0 else 3, 1.3)
    for k in (0, 2):        # two blue chevrons down the abdomen
        r.dot(ax - 1 - k, ay - 0.5 + k * 0.6, "silk", 3, 1.2); r.dot(ax - k, ay + 0.5 + k * 0.6, "silk", 3, 1.2)
    if snap:
        hx, hy = T(2.0 + 3.3 * s, cy + 1.6 * s)
        r.dot(hx + 1.5, hy + 0.5, "white", 4, 3.0)
        r.dot(hx + 2.4, hy - 0.6, "snow", 3, 2.9); r.dot(hx + 0.4, hy + 1.6, "snow", 2, 2.9)
    if glob: r.ell(glob[0], glob[1], glob[2], glob[2] * 0.9, "web", 4.0, bias=0.2)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 4.5, tone=t)
    if dust: snow_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def rimeling_corpse(stage):
    r = Rig()
    # on its back, legs curled up over the belly, fangs to the sky
    r.ell(-1.0, -2.6, 5.4, 2.6, "silk", 0.0, bias=0.1)
    r.ell(4.0, -2.4, 2.8, 2.0, "chit", 0.5)
    for i in range(4):
        x = -3.0 + i * 2.2
        k = (x + 0.8, -6.0 - (i % 2) + stage)
        r.tube([(x, -4.0), k, (x + 2.0 + 0.4 * stage, -4.4 + stage)], [0.8, 0.6, 0.4], "chit", 1.0 + i * 0.01)
    r.line(6.0, -3.0, 7.0, -5.0, "frost", 1.2, tone=4)
    for i in range(-3, 3): r.dot(-1 + i * 1.5, -0.4, "frost", 3, 1.3)
    return r.resolve()


def rimeling_sheet(out):
    Ri = rimeling
    idle = [Ri(abd_dy=[0, 0.3, 0.6, 0.3][i], cy=-4.2 + [0, 0.15, 0.3, 0.15][i], fang=[0, 0, 0.4, 0][i]) for i in range(4)]
    run = [Ri(phase=i / 6.0, stride=1.0, lean=4, cy=-4.4 + 0.4 * abs(math.sin(i / 6 * math.tau)), abd_dy=0.3 * (i % 2)) for i in range(6)]
    snap_idle = [Ri(abd_dy=[0, 0.3, 0.6, 0.3][i], cy=-4.2 + [0, 0.15, 0.3, 0.15][i], fang=[0.6, 0.9, 1.2, 0.9][i], snap=True) for i in range(4)]
    snap_run = [Ri(phase=i / 6.0, stride=1.0, lean=4, cy=-4.4 + 0.4 * abs(math.sin(i / 6 * math.tau)), fang=0.8, snap=True) for i in range(6)]
    # Bite (7): squat back (0-1), spring (2, smear), BITE fangs shut at full reach (3), hold (4), settle (5-6)
    bite = [Ri(lean=-6, cy=-3.6, fang=0.6), Ri(lean=-10, cy=-3.2, fang=1.4, abd_dy=0.4),
            Ri(lean=8, cy=-4.8, fang=1.6, front=((5.5, -2.0), (5.0, -1.5)), smear=[((-2, -6), (4, -6), "snow", 2)]),
            Ri(lean=14, cy=-4.4, fang=0.0, front=((6.5, 1.5), (6.0, 2.0)), dust=(8.0, 0, 0, 0.7),
               extra=lambda r: [r.dot(9.5, -2.0, "white", 4, 6), r.dot(10.5, -3.0, "snow", 3, 6), r.dot(10.0, -1.0, "snow", 2, 6)]),
            Ri(lean=10, cy=-4.2, fang=0.2, dust=(8.0, 0, 1, 0.7)), Ri(lean=3, cy=-4.2, fang=0.4), Ri(lean=0, cy=-4.2)]
    # Spit (7): rear up (0-1), the glob gathers at the fangs (2), SPIT (3) glob leaves at (9, -6), recoil (4), settle
    spit = [Ri(lean=-8, cy=-4.6, fang=0.8), Ri(lean=-16, cy=-5.0, fang=1.6, glob=(7.0, -8.5, 1.0)),
            Ri(lean=-20, cy=-5.2, fang=1.8, glob=(7.4, -9.0, 1.6)),
            Ri(lean=-6, cy=-4.6, fang=1.8, glob=(10.0, -7.0, 1.8), smear=[((5, -8), (8, -7), "web", 2)]),
            Ri(lean=2, cy=-4.0, fang=0.6), Ri(lean=0, cy=-4.2, fang=0.2), Ri()]
    d0 = Ri(lean=-14, cy=-4.6, fang=1.6, eye="white")
    d1 = Ri(lean=-30, cy=-4.0, fang=1.6, eye="white", front=((2.0, -5.0), (1.0, -4.0)))
    knock = Ri(lean=-16, cy=-4.4, fang=1.0, eye="white")
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.07] * 6),
             ("Bite", bite, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Spit", spit, [0.12, 0.12, 0.1, 0.06, 0.1, 0.1, 0.1]),
             ("IdleSnap", snap_idle, [0.12, 0.1, 0.12, 0.1]), ("RunSnap", snap_run, [0.07] * 6)]
    anims += tail_anims(idle[0], [d0, d1, rimeling_corpse(0), rimeling_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvRimeling", anims, out, scale=8)


# ================================================================== HOARMOTH: a wide, flat frost moth
def hoarmoth(alt=6.0, flap=0.0, lean=0.0, body_dy=0.0, ant=0.0, gust=0.0, motes=None, extra=None, eye="eye", fold=1.0):
    """flap: wing angle offset (deg, + = down). gust: 0..1 how far the wings sweep forward for the gust."""
    r = Rig()
    cx, cy = 0.0, -alt + body_dy
    shadow(r, 0.0, -1.0, 4.5)
    # a wide flat flier: silk-grey wings dusted with rime, an aurora-green eye on each forewing
    moth(r, cx, cy, span=9.5 * (1 - 0.15 * gust), chord=6.0, flap=flap - gust * 30, fore="frost", hind="silk", body="fur",
         lean=lean, spots=[(0.62, 0.3, "aurg", 3)], hspots=[(0.6, 0.0, "aurg", 2)], eye=eye, ant=ant, fold=fold, far=0.78,
         rim="ice")
    if motes:
        for (x, y, k) in motes: sparkle(r, x, y, k, "white")
    if extra: extra(r)
    return r.resolve()


def hoarmoth_corpse(stage):
    r = Rig()
    wing(r, (-1.0, -1.5), -160, 7.0, 5.0, "silk", -1.0, bias=-0.3)
    wing(r, (0.0, -1.5), -10 - 10 * stage, 7.5, 5.5, "frost", 1.0, spots=[(0.6, 0.4, "aurg", 2)])
    r.tube([(2.0, -1.5), (-1.0, -1.2), (-4.0, -1.0)], [1.6, 1.4, 0.8], "fur", 0.5)
    r.dot(3.0, -2.0, "white", 3, 0.7)
    flakes(r, [(-5, -3, 3), (5, -4, 2)] if stage == 0 else [], 3)
    return r.resolve()


def hoarmoth_sheet(out):
    H = hoarmoth
    flaps = [-25, 5, 30, 5]
    idle = [H(alt=6.0 + [0, -0.5, -1, -0.5][i], flap=flaps[i], ant=[0, 4, 8, 4][i]) for i in range(4)]
    run = [H(alt=6.5 + [0, -0.6, -1, -0.6, 0, 0.4][i], flap=[-35, -10, 25, 40, 15, -15][i], lean=12) for i in range(6)]
    # Dust (7): wings high (0-1), a downstroke flings the 3 motes forward (3, from (6, -8)), recover
    dust = [H(flap=-40, lean=-6), H(flap=-55, lean=-10, motes=[(4.0, -9.0, 3)]),
            H(flap=20, lean=6, motes=[(6.0, -8.0, 2)]), H(flap=45, lean=12, motes=[(9.0, -9.0, 1), (9.0, -6.0, 2), (8.0, -11.0, 2)]),
            H(flap=20, lean=6), H(flap=-10), H(flap=-20)]
    # Gust (8): rear back, wings wide (0-2), a huge forward clap (3-4: the gust leaves at (8, -7)), hang, recover
    gust = [H(flap=-30, lean=-8), H(flap=-55, lean=-16, fold=1.1), H(flap=-70, lean=-20, fold=1.15),
            H(flap=30, lean=10, gust=0.7, extra=lambda r: arc_smear(r, 0, -8, 9, -120, -10, "snow")),
            H(flap=50, lean=16, gust=1.0, extra=lambda r: flakes(r, [(10, -9, 4), (11, -6, 3), (9, -4, 2), (12, -11, 2)])),
            H(flap=30, lean=8, gust=0.5), H(flap=-5), H(flap=-20)]
    d0 = H(flap=-60, lean=-20, eye="white")
    d1 = H(alt=3.5, flap=40, lean=-40, eye="white", fold=0.8)
    knock = H(flap=-50, lean=-24, eye="white")
    anims = [("Idle", idle, [0.09] * 4), ("Run", run, [0.06] * 6),
             ("Dust", dust, [0.1, 0.12, 0.06, 0.08, 0.1, 0.1, 0.1]),
             ("Gust", gust, [0.1, 0.12, 0.14, 0.05, 0.08, 0.12, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, hoarmoth_corpse(0), hoarmoth_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvHoarmoth", anims, out, scale=8)


# ================================================================== RIME SHARDLING: a stubby rime golem under a crystal spike
def shardling(bob=0.0, lean=0.0, step=0.0, arms=(0.0, 0.0), crown=0.0, glow=False, extra=None, eye="eye", squash=0.0):
    r = Rig()
    T = Xf(lean, (0.0, -1.0))
    by = -4.6 + bob
    # stubby legs (packed rime)
    for k, (fx, side) in enumerate(((-2.2, 0), (2.0, 1))):
        dx = step * (1 if side else -1)
        r.tube([T(fx * 0.7, by + 2.0), (fx + dx, -1.0)], [1.6, 1.5], "frost", -1.0 if side == 0 else 1.0, bias=-0.2 if side == 0 else 0.0)
        r.ell(fx + dx, -0.8, 1.8, 0.9, "frost", -0.9 if side == 0 else 1.1, bias=-0.1)
    # body: a lumpy snowball of packed rime, flattened
    r.ell(*T(0.0, by), 4.8 + squash, 3.8 - squash * 0.6, "frost", 0.0, bias=0.05)
    for (x, y) in ((-2.5, 1.5), (1.0, 2.2), (-3.2, -1.0)):
        r.dot(*T(x, by + y), "ice", 2, 0.05)       # blue ice showing through the packed rime
    # little stub arms
    for k, (ax, ang) in enumerate(((-4.0, arms[0]), (3.8, arms[1]))):
        sx, sy = T(ax, by)
        ex, ey = sx + 2.4 * math.cos(math.radians(90 + ang)) * (1 if k else -1) * 0.3 + (1.2 if k else -1.2), sy + 2.4 * math.sin(math.radians(90 + ang))
        r.tube([(sx, sy), (ex, ey)], [1.3, 1.1], "frost", 0.5 if k else -0.5, bias=-0.15 if k == 0 else 0.0)
    # face: two eye slits in the snow
    fx, fy = T(1.4, by - 0.4)
    for ex in (fx, fx + 2.4):
        r.dot(ex, fy, "crys", 0, 1.0); r.dot(ex, fy - 1, "crys", 1, 1.0); r.dot(ex + 0.5, fy, eye, 3, 1.01)
    r.line(fx, fy + 2, fx + 2, fy + 2, "ice", 1.0, tone=1)
    # the crystal head: a violet spike pointing up and slightly forward
    hx, hy = T(0.4, by - 3.0)
    crystal(r, hx, hy, 7.5 + crown, 4.2, "crys", 1.5, ang=lean * 1.4 + 6)
    crystal(r, hx - 2.4, hy + 0.8, 3.5, 2.2, "crys", 1.4, ang=-20 + lean)
    if glow:
        tip = Xf(lean * 1.4 + 6, (hx, hy))(hx, hy - 7.5 - crown)
        sparkle(r, tip[0], tip[1] - 1, 1, "vglow")
    if extra: extra(r)
    return r.resolve()


def shardling_corpse(stage):
    r = Rig()
    r.ell(-1.0, -2.0, 5.0, 2.2, "frost", 0.0)
    r.ell(3.0, -1.5, 2.2, 1.3, "frost", 0.2)
    crystal(r, 7.5, -0.5, 6.0, 3.0, "crys", 1.0, ang=80)
    if stage:
        for (x, y) in ((-6, -1), (-4, -0.5), (1, -0.5)): r.dot(x, y, "crys", 2, 1.2)
    else:
        sparkle(r, 9, -5, 2, "vglow")
    return r.resolve()


def shardling_sheet(out):
    Sh = shardling
    idle = [Sh(bob=[0, 0.3, 0.6, 0.3][i], arms=([0, 0.3, 0.6, 0.3][i] * 10, [0, 0.3, 0.6, 0.3][i] * -10)) for i in range(4)]
    run = [Sh(bob=-0.5 * abs(math.sin(i / 6 * math.tau)), lean=8, step=1.8 * math.sin(i / 6 * math.tau),
              arms=(25 * math.sin(i / 6 * math.tau), -25 * math.sin(i / 6 * math.tau))) for i in range(6)]
    # Ram (7): rear back (0-1), charge (2, smear), the crystal SPEARS forward (3), hold, recover
    ram = [Sh(lean=-10, bob=0.6, squash=0.4), Sh(lean=-20, bob=0.9, squash=0.6, arms=(-30, 30)),
           Sh(lean=30, bob=-0.6, extra=lambda r: [r.line(-6, -9, -1, -8, "snow", 4.6, tone=2), r.line(-6, -6, -2, -6, "snow", 4.6, tone=1)]),
           Sh(lean=38, bob=-0.2, extra=lambda r: [sparkle(r, 10, -6, 1, "white"), snow_puff(r, 1, 0, 0, 0.8)]),
           Sh(lean=30, bob=0.0, extra=lambda r: snow_puff(r, 1, 0, 1, 0.8)), Sh(lean=15), Sh(lean=4)]
    # Icicle (8): plants its feet (0), the crystal head glows (1-3), it calls the icicle down (4), glow fades (5-7)
    icicle = [Sh(squash=0.3, bob=0.4), Sh(lean=-6, crown=0.5, glow=True, arms=(-60, 60)),
              Sh(lean=-10, crown=1.0, glow=True, arms=(-90, 90)), Sh(lean=-12, crown=1.2, glow=True, arms=(-100, 100), bob=-0.5),
              Sh(lean=-4, crown=0.6, glow=True, arms=(-40, 40), extra=lambda r: [sparkle(r, 2, -18, 1, "vglow"), sparkle(r, -3, -15, 2, "white")]),
              Sh(lean=-2, crown=0.3, arms=(-20, 20)), Sh(), Sh()]
    d0 = Sh(lean=-20, eye="white", squash=0.5)
    d1 = Sh(lean=-50, eye="white", bob=1.0)
    knock = Sh(lean=-24, eye="white")
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Ram", ram, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Icicle", icicle, [0.1, 0.1, 0.1, 0.12, 0.08, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, shardling_corpse(0), shardling_corpse(1)], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("YsvShardling", anims, out, scale=8)


# ================================================================== BROODLING: a hatchling frost spider
def broodling(phase=0.0, stride=0.0, lean=0.0, fang=0.0, cy=-2.6, eye="eye", front=None, extra=None):
    r = Rig()
    s = 0.55
    spider(r, cx=1.0, cy=cy, s=s, phase=phase, stride=stride, lean=lean, abd=(4.4, 3.6), abd_at=(-5.0, -1.2),
           ceph=(3.2, 2.6), legs=(4.6, 5.0), spread=(6.5, 3.0, -3.0, -6.5), mats=("chit", "chit", "frost"),
           eyes=((2.0, -1.2),), eye_mat=eye, fang=fang, front=front, leg_rad=(1.0, 0.8, 0.5))
    r.dot(-1.8, cy - 1.6, "red", 3, 1.4)       # a red fleck: the Widow's mark
    if extra: extra(r)
    return r.resolve()


def broodling_sheet(out):
    B = broodling
    idle = [B(cy=-2.6 + [0, 0.2, 0.4, 0.2][i], fang=[0, 0, 0.5, 0][i]) for i in range(4)]
    run = [B(phase=i / 6.0, stride=1.0, lean=5) for i in range(6)]
    bite = [B(lean=-8, fang=0.8), B(lean=-12, fang=1.4), B(lean=12, fang=1.6, front=((5.0, -1.0), (4.5, -0.5))),
            B(lean=18, fang=0.0, front=((5.5, 2.0), (5.0, 2.2)), extra=lambda r: r.dot(7, -1, "white", 4, 5)),
            B(lean=10), B(lean=3), B()]
    spawn = [B(cy=-1.6, lean=-20), B(cy=-2.2, lean=-8, fang=1.0), B()]
    d0 = B(lean=-20, eye="white"); d1 = B(lean=-40, eye="white", cy=-2.0)
    corpse = Rig(); corpse.ell(0, -1.4, 3.0, 1.4, "frost", 0); corpse.ell(2.6, -1.4, 1.6, 1.2, "chit", 0.3)
    for i in range(3): corpse.tube([(-1.5 + i * 1.5, -2.2), (-1 + i * 1.5, -4.0), (0 + i * 1.5, -2.6)], [0.6, 0.5, 0.4], "chit", 1)
    c = corpse.resolve()
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.06] * 6),
             ("Bite", bite, [0.1, 0.08, 0.05, 0.08, 0.1, 0.1, 0.1]), ("Spawn", spawn, [0.08, 0.08, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, c, c], [0.08, 0.1, 0.1, 0.3], d0)
    return sheet("YsvBroodling", anims, out, scale=8)


JOBS = [("YsvRimeling", rimeling_sheet), ("YsvHoarmoth", hoarmoth_sheet), ("YsvShardling", shardling_sheet),
        ("YsvBroodling", broodling_sheet)]
SYNC = {
    "YsvRimeling": {"Bite": [("BITE: fangs shut at (9, -2); box 12 x 12 at (10, -3)", 3)],
                    "Spit": [("glob leaves the fangs at (9, -6)", 3)]},
    "YsvHoarmoth": {"Dust": [("three motes leave at (6, -8)", 3)], "Gust": [("the gust leaves at (8, -7)", 3)]},
    "YsvShardling": {"Ram": [("RAM: the crystal tip at (10, -6); box 12 x 14 at (8, -5)", 3)],
                     "Icicle": [("the icicle is called down on the hero", 4)]},
    "YsvBroodling": {"Bite": [("BITE: fangs at (7, -1)", 3)]},
}
NOTES = {
    "YsvRimeling": "IdleSnap / RunSnap: the fangs burn white while the hero carries 2 frost pips (Cold Snap).",
    "YsvHoarmoth": "Flies 6 px over its shadow; the T1 limit (20 x 16) includes the hover.",
}
