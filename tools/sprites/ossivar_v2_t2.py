"""Ossivar tier 2: Bone Lancer, Gravedigger, Gravetusk, Barghest, Ossuary Priest, Carrion Vulture. Built through
ossivar_v2_rigs.py (python3 ossivar_v2_rigs.py --only OssBoneLancer,...). Same renderer and rules as the tier 1s:
material ramps, top-left light, selective outline, hand-pixelled heads, every frame posed. T2 idle limit 28 x 26."""
import math
from ossivar_v2_rigs import (Rig, Xf, chain, ik, lerp, line_px, skullp, lbone, skeleton, rib_rows, vertebrae, bone, heap,
                             bone_bits, dust, smear, arc_pts, sheet, tail_anims, SYNC, NOTES, BONE_LEG, dog_body, hound_head,
                             gait, wing, crow, J)

J.RAMPS.update({k: [J._h(c) for c in v] for k, v in {
    "wood": ["1e120e", "4a2a1a", "70442a", "96643c", "b88a58"],
}.items()})


# ------------------------------------------------------------------ shared props
def spine_spear(r, a, b, z, blade=True, pennant=0.0, near=True, pen=True):
    """A spear of straightened vertebrae from butt a to tip b, a jawbone blade at the tip, a marrow-red pennant."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    p = r.part(True, z)
    k = 0
    for (x, y) in line_px(int(round(a[0])), int(round(a[1])), int(round(b[0] - ux * 2)), int(round(b[1] - uy * 2))):
        r.put(x, y, z, "bone", 0.5, p, (3 if near else 2) if (k // 2) % 2 == 0 else 1)
        k += 1
    if blade:
        tx, ty = b
        bx, by = b[0] - ux * 3.5, b[1] - uy * 3.5
        nx, ny = -uy, ux
        r.poly([(bx + nx * 1.4, by + ny * 1.4), (tx, ty), (bx - nx * 0.6, by - ny * 0.6)], "obone", z + 0.01, normal=(-0.4, -0.6, 0.7))
        r.dot(tx, ty, "obone", 4, z + 0.02)
        r.dot(bx + nx * 0.8 + ux, by + ny * 0.8 + uy, "obone", 1, z + 0.02)
    if pen:
        px, py = b[0] - ux * 5.5, b[1] - uy * 5.5
        w = math.sin(pennant)
        r.poly([(px, py), (px - ux * 3.0, py - uy * 3.0), (px - ux * (4.0 + w), py - uy * (4.0 + w) + 2.6),
                (px - ux * 1.0, py - uy * 1.0 + 2.0 + w * 0.5)], "marrow", z - 0.01, normal=(-0.3, -0.4, 0.8))


# ================================================================== BONE LANCER (T2): a tall skeleton spearman
def lancer(lean=6.0, bob=0.0, feet=((3.0, 0.0), (-3.0, 0.0)), hand=(5.0, -12.0), hand2=(-3.0, -12.0), spear=None, jaw=0,
           extra=None, smear_pts=None, crouch=0.0, pen=0.0, bundle=True, bundle_hand=None, dust_at=None, head=True):
    """spear: (butt, tip) or None (the default hold: across the body, tip forward and up)."""
    r = Rig()
    hip = (-0.5, -10.0 + bob + crouch)
    neck, sh = skeleton(r, hip, lean, hands=(hand, hand2), feet=feet, arm=(4.2, 4.0), leg=(5.2, 5.0), ribs=4, rib_w=4,
                        torso=7.5 - crouch * 0.4, elbows=(-1, 1), knees=(1, 1))
    # rusted gorget over the collar
    r.ell(neck[0] + 0.3, neck[1] + 1.4, 2.4, 1.2, "rust", 2.5, bias=0.1)
    r.dot(neck[0] - 1.0, neck[1] + 1.2, "rust", 4, 2.6)
    # bundle of spare spears on the back
    if bundle:
        bx, by = neck[0] - 3.0, neck[1] + 3.0
        for i in range(3):
            r.line(bx - 1 + i, by + 4, bx + 1 + i, by - 6 + i, "bone", -2.0 + i * 0.01, tone=2 if i != 1 else 1)
            r.dot(bx + 1 + i, by - 6 + i, "obone", 3, -1.99)
        r.line(bx - 1, by - 1, bx + 3, by - 2, "rope", -1.9, tone=2)
    if bundle_hand:
        hx, hy = bundle_hand
        for i, a in enumerate((-30, -10, 10)):
            t = (hx + 7 * math.cos(math.radians(a - 60)), hy + 7 * math.sin(math.radians(a - 60)))
            spine_spear(r, (hx - 2 * math.cos(math.radians(a - 60)), hy - 2 * math.sin(math.radians(a - 60))), t, 4.0 + i * 0.01,
                        pen=False)
    if head:
        skullp(r, neck[0] + 1.0, neck[1] + 0.5, "M", 3.0, jaw=jaw)
    if spear is None:
        spear = ((hand2[0] - 3.0, hand2[1] + 2.0), (hand[0] + 9.0, hand[1] - 6.0))
    if spear:
        spine_spear(r, spear[0], spear[1], 2.2, pennant=pen)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def lancer_sheet(outdir):
    Lc = lancer
    idle = [Lc(bob=[0, 0.3, 0.6, 0.3][i], hand=(5.0, -12.0 + [0, 0.3, 0.6, 0.3][i]), hand2=(-3.0, -12.0 + [0, 0.3, 0.6, 0.3][i]),
               pen=i * 1.5, jaw=[0, 0, 1, 0][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (0.5 + 3.4 * math.cos(ph), -max(0.0, 2.0 * math.sin(ph)))
        f2 = (-0.5 - 3.4 * math.cos(ph), -max(0.0, -2.0 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        run.append(Lc(lean=14, bob=b, feet=(f1, f2), hand=(6.0, -12.0 + b), hand2=(-2.0, -12.5 + b), pen=i * 1.1,
                      spear=((-6.0, -10.5 + b), (16.0, -15.0 + b))))
    # Thrust (6): draw back (0), coil (1), THRUST (2: tip at (32, -12)), hold (3), pull back (4), recover (5)
    thrust = [Lc(lean=0, hand=(1.0, -12.0), hand2=(-5.0, -12.0), spear=((-11.0, -11.0), (10.0, -13.0)), crouch=0.6),
              Lc(lean=-8, hand=(-2.0, -12.0), hand2=(-7.0, -12.0), spear=((-14.0, -11.5), (7.0, -12.5)), crouch=1.0,
                 feet=((4.0, 0.0), (-4.0, 0.0))),
              Lc(lean=22, hand=(11.0, -12.0), hand2=(5.0, -12.0), spear=((0.0, -12.0), (32.0, -12.0)), feet=((7.0, 0.0), (-4.0, 0.0)),
                 smear_pts=[(14, -10), (22, -11), (30, -12)], jaw=1, pen=1.0),
              Lc(lean=20, hand=(10.0, -12.0), hand2=(4.0, -12.0), spear=((-1.0, -12.0), (31.0, -12.0)), feet=((7.0, 0.0), (-4.0, 0.0)), pen=2.5),
              Lc(lean=10, hand=(5.0, -12.0), hand2=(-1.0, -12.0), spear=((-6.0, -11.5), (22.0, -13.0)), feet=((5.0, 0.0), (-3.0, 0.0))),
              Lc()]
    # Volley (7): reach back for the bundle (0), three spears in the fist overhead (1), cock (2), THROW (3: they leave the
    # hand at (11, -19)), follow (4), settle (5-6). The lance stays in the far hand.
    vs = ((-7.0, -10.0), (8.0, -16.0))
    volley = [Lc(lean=-4, hand=(-3.0, -18.0), hand2=(-3.0, -12.0), spear=vs, bundle=True),
              Lc(lean=-8, hand=(-1.0, -22.0), hand2=(-3.0, -12.0), spear=vs, bundle=False, bundle_hand=(-1.0, -22.0)),
              Lc(lean=-16, hand=(-5.0, -20.0), hand2=(-3.0, -12.0), spear=vs, bundle=False, bundle_hand=(-5.0, -20.0), crouch=0.6),
              Lc(lean=18, hand=(11.0, -19.0), hand2=(-4.0, -11.0), spear=vs, bundle=False, feet=((5.0, 0.0), (-3.0, 0.0)),
                 smear_pts=[(-4, -24), (3, -24), (9, -21), (12, -19)], jaw=1),
              Lc(lean=16, hand=(9.0, -11.0), hand2=(-4.0, -11.0), spear=vs, bundle=False, feet=((5.0, 0.0), (-3.0, 0.0))),
              Lc(lean=8, bundle=False), Lc(bundle=True)]
    d0 = Lc(lean=-12, jaw=2, hand=(1.0, -15.0), hand2=(-5.0, -14.0), spear=((-8.0, -6.0), (10.0, -20.0)))
    d1 = Lc(lean=-30, bob=4.0, crouch=2.0, jaw=2, hand=(0.0, -6.0), hand2=(-7.0, -8.0), feet=((4.0, 0.0), (-5.0, 0.0)),
            spear=((-12.0, -2.0), (8.0, -8.0)))
    d2 = lancer_corpse(0)
    corpse = lancer_corpse(1)
    knock = Lc(lean=-14, jaw=2, hand=(2.0, -14.0), hand2=(-5.0, -13.0), feet=((4.0, 0.0), (-3.0, 0.0)),
               spear=((-9.0, -8.0), (11.0, -18.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.075] * 6),
             ("Thrust", thrust, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Volley", volley, [0.12, 0.1, 0.12, 0.05, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssBoneLancer", anims, outdir)


def lancer_corpse(stage):
    r = Rig()
    heap(r, -1.0, 0, 16.0 if stage else 12.0, 14, seed=21, h=0.6 if stage else 1.4)
    skullp(r, -6.0, -0.5 if stage else -2.0, "M", 1.0, jaw=1, eye=False, flip=True)
    r.ell(-3.0, -1.0, 2.0, 1.0, "rust", 0.8)
    spine_spear(r, (-10.0, -0.5), (12.0, -1.5), 0.5, pennant=2.0)
    if not stage: dust(r, 0, 0, 1, 1.6)
    return r.resolve()


SYNC["OssBoneLancer"] = {"Thrust": [("THRUST: tip at (32, -12); hit box 26 x 10 at (19, -12)", 2)],
                         "Volley": [("THROW: three spears leave the hand at (11, -19); launch along the floor at (11, -1)", 3)]}


# ================================================================== GRAVEDIGGER (T2): a stooped digger, spade, lantern, sack
DIGGER_HEAD = """
..ccccc..
.cCCCCCc.
ccccccccc
..LHLB...
.LkkLkS..
.SkeBeS..
..STtS...
"""
DIG_LEG = dict(BONE_LEG, c=("umber", 1), C=("umber", 3))


def spade(r, grip, tip, z, near=True, dirt=False):
    """A long spade from the grip (top of the haft) to the blade tip."""
    L = math.hypot(tip[0] - grip[0], tip[1] - grip[1])
    ux, uy = (tip[0] - grip[0]) / L, (tip[1] - grip[1]) / L
    bx, by = tip[0] - ux * 4.0, tip[1] - uy * 4.0
    r.line(grip[0], grip[1], bx, by, "wood", z, tone=3 if near else 2)
    r.line(grip[0] - uy * 1.2, grip[1] + ux * 1.2, grip[0] + uy * 1.2, grip[1] - ux * 1.2, "wood", z + 0.01, tone=2)
    nx, ny = -uy, ux
    r.poly([(bx + nx * 1.8, by + ny * 1.8), (tip[0] + nx * 1.4, tip[1] + ny * 1.4), (tip[0] + ux * 0.6, tip[1] + uy * 0.6),
            (tip[0] - nx * 1.4, tip[1] - ny * 1.4), (bx - nx * 1.8, by - ny * 1.8)], "iron", z + 0.02, normal=(-0.5, -0.5, 0.7), bias=0.2)
    if dirt:
        r.dot(tip[0] - ux, tip[1] - uy, "dirt", 3, z + 0.03); r.dot(tip[0] - ux * 2 + nx, tip[1] - uy * 2 + ny, "dirt", 2, z + 0.03)


def digger(lean=28.0, bob=0.0, feet=((3.0, 0.0), (-2.5, 0.0)), hand=(6.0, -10.0), hand2=(3.0, -14.0), spade_at=None,
           jaw=0, lamp=0, extra=None, smear_pts=None, crouch=0.0, dust_at=None, sack=0.0):
    """spade_at: (grip, tip). The coat is a hunched bell; the sack of bones rides the back."""
    r = Rig()
    hip = (-1.0, -8.5 + bob + crouch)
    T = Xf(lean, hip)
    neck = T(-1.0, -17.0 + bob + crouch * 0.5)
    # legs (in dark trousers) and boots
    for k, (fx_, fy_) in enumerate(feet):
        near = k == 0
        hx, hy = hip[0] + (0.8 if near else -0.6), hip[1]
        kx, ky = ik(hx, hy, fx_, fy_ - 0.8, 4.4, 4.2, bend=-1)
        zz = 0.6 if near else -1.0
        r.tube([(hx, hy), (kx, ky), (fx_, fy_ - 0.8)], [1.3, 1.0, 0.9], "cloth", zz, bias=0.0 if near else -0.4)
        r.poly([(fx_ - 1.2, fy_ - 1.6), (fx_ + 2.2, fy_ - 1.2), (fx_ + 2.2, fy_), (fx_ - 1.2, fy_)], "tar", zz + 0.01, bias=0.2 if near else -0.2)
    # sack of bones on the back
    sx, sy = T(-5.0, -14.5 + bob + crouch * 0.5 + sack)
    r.ell(sx, sy, 3.4, 3.6, "rope", -1.5, bias=-0.05)
    r.line(sx + 1.0, sy - 3.8, sx - 1.5, sy - 6.0, "bone", -1.4, tone=3); r.dot(sx - 1.5, sy - 6.0, "bone", 4, -1.39)
    r.line(sx - 1.0, sy - 3.4, sx - 3.5, sy - 4.8, "bone", -1.45, tone=2)
    skullp(r, sx + 2.0, sy - 2.2, "S", -1.42, eye=False)
    # coat: a hunched bell from the shoulders to the knees
    c0 = T(-3.6, -17.4 + bob + crouch * 0.5); c1 = T(2.8, -16.6 + bob + crouch * 0.5)
    c2 = (hip[0] + 4.6, hip[1] + 3.6); c3 = (hip[0] - 4.8, hip[1] + 4.0)
    r.poly([c0, c1, c2, (hip[0] + 1.0, hip[1] + 4.0), c3], "umber", 0.0, curve=0.7, normal=(-0.2, -0.3, 1.0))
    r.line(c0[0] + 1, c0[1] + 1, c3[0] + 1, c3[1] - 1, "umber", 0.01, tone=3)
    # belt + lantern
    bx, by = T(-1.0, -10.5 + bob + crouch)
    r.line(bx - 3.6, by, bx + 3.6, by - 0.4, "tar", 0.05, tone=2)
    lx, ly = bx + 3.0, by + 1.4
    r.line(lx, ly - 1.4, lx, ly - 0.4, "iron", 0.1, tone=2)
    r.ell(lx, ly + 0.6, 1.0, 1.3, "lant", 0.1, flat=3 if lamp % 2 == 0 else 2)
    r.dot(lx, ly + 0.4, "lant", 4, 0.11)
    r.line(lx - 1, ly - 0.6, lx + 1, ly - 0.6, "iron", 0.12, tone=1)
    # arms in coat sleeves
    for k, (hx_, hy_) in enumerate((hand2, hand)):
        near = k == 1
        s0 = T(1.0 if near else -1.5, -16.0 + bob + crouch * 0.5)
        ex, ey = ik(s0[0], s0[1], hx_, hy_, 4.0, 4.0, bend=-1 if near else 1)
        r.tube([s0, (ex, ey), (hx_, hy_)], [1.3, 1.1, 0.8], "umber", 1.6 if near else -0.8, bias=0.0 if near else -0.4)
        r.dot(hx_, hy_, "ghoul", 3 if near else 2, (1.7 if near else -0.7))
    # head: a skull under a slouch hat
    r.stamp(DIGGER_HEAD, neck[0] + 1.0, neck[1] + 1.0, 2.5, dict(DIG_LEG, **({} if jaw == 0 else {"T": ("bone", 2)})), pivot=(4, 7))
    if spade_at is None:
        spade_at = ((hand2[0] - 1.0, hand2[1] - 3.0), (hand[0] + 4.0, 0.0))
    spade(r, spade_at[0], spade_at[1], 1.2)
    if smear_pts: smear(r, smear_pts, "dirt", 4)
    if dust_at: dust(r, *dust_at, mat="dirt")
    if extra: extra(r)
    return r.resolve()


def dirt_fling(r, x, y, k, n=7, seed=4):
    import random
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(-70, 10); d = 3 + k * 3 + rnd.uniform(0, 3)
        px, py = x + d * math.cos(math.radians(a)), y + d * math.sin(math.radians(a)) + k * k * 0.6
        r.dot(px, py, "dirt", 3 if i % 2 else 2, 7.0)
        if i % 3 == 0: r.dot(px + 1, py, "dirt", 1, 7.0)


def digger_sheet(outdir):
    D = digger
    idle = [D(bob=[0, 0.3, 0.6, 0.3][i], lamp=i, hand=(6.0, -10.0 + [0, 0.3, 0.6, 0.3][i]), hand2=(3.0, -14.0 + [0, 0.3, 0.6, 0.3][i]),
              sack=[0, 0.3, 0.6, 0.3][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (1.0 + 3.0 * math.cos(ph), -max(0.0, 1.8 * math.sin(ph)))
        f2 = (-1.0 - 3.0 * math.cos(ph), -max(0.0, -1.8 * math.sin(ph)))
        b = -0.6 * abs(math.sin(ph))
        run.append(D(lean=34, bob=b, feet=(f1, f2), lamp=i, hand=(7.0, -11.0 + b), hand2=(2.0, -15.0 + b), sack=-b,
                     spade_at=((-3.0, -18.0 + b), (12.0, -6.0 + b))))
    # Spade (6): heave it up over the shoulder (0-1), SWING down (2: blade on the floor at (11, -2), dirt flung), follow,
    # dirt rains (4), lift (5)
    spd = [D(lean=10, hand=(1.0, -16.0), hand2=(-2.0, -18.0), spade_at=((4.0, -20.0), (-8.0, -22.0))),
           D(lean=-6, hand=(-1.0, -19.0), hand2=(-4.0, -20.0), spade_at=((2.0, -22.0), (-9.0, -26.0)), crouch=0.4),
           D(lean=40, hand=(8.0, -9.0), hand2=(5.0, -12.0), spade_at=((2.0, -15.0), (13.0, -1.0)), feet=((5.0, 0.0), (-2.5, 0.0)),
             smear_pts=[(-6, -24), (4, -22), (10, -14), (13, -4)], dust_at=(12.0, 0.0, 0, 1.2, 3, 6.0)),
           D(lean=42, hand=(8.0, -8.0), hand2=(5.0, -11.0), spade_at=((2.0, -14.0), (13.0, 0.0)), feet=((5.0, 0.0), (-2.5, 0.0)),
             extra=lambda r: dirt_fling(r, 13.0, -3.0, 0)),
           D(lean=30, hand=(7.0, -10.0), hand2=(3.0, -13.0), extra=lambda r: dirt_fling(r, 13.0, -3.0, 1)),
           D(extra=lambda r: dirt_fling(r, 13.0, -3.0, 2, n=4))]
    # Unearth (8): raise the spade (0-1), STAB it in (2), lever (3-4), heave (5: two piles fly out), toss (6), settle (7)
    une = [D(lean=10, hand=(4.0, -16.0), hand2=(2.0, -19.0), spade_at=((2.0, -21.0), (6.0, -6.0))),
           D(lean=0, hand=(4.0, -19.0), hand2=(2.0, -22.0), spade_at=((2.0, -24.0), (6.0, -9.0)), crouch=-0.5),
           D(lean=34, hand=(6.0, -11.0), hand2=(4.0, -14.0), spade_at=((4.0, -16.0), (8.0, 2.0)), dust_at=(8.0, 0.0, 0, 1.4, 3, 6.0)),
           D(lean=44, hand=(5.0, -9.0), hand2=(3.0, -12.0), spade_at=((2.0, -13.0), (9.0, 1.0)), crouch=1.0,
             extra=lambda r: dirt_fling(r, 9.0, -1.0, 0, n=5, seed=8)),
           D(lean=46, hand=(4.0, -8.0), hand2=(2.0, -11.0), spade_at=((0.0, -12.0), (9.5, 1.0)), crouch=1.4,
             extra=lambda r: dirt_fling(r, 9.0, -1.0, 1, n=6, seed=8)),
           D(lean=6, hand=(3.0, -17.0), hand2=(1.0, -20.0), spade_at=((0.0, -22.0), (10.0, -14.0)),
             extra=lambda r: [dirt_fling(r, 10.0, -8.0, 1, n=8, seed=9), bone_bits(r, 10.0, -10.0, 1, 5, seed=3, z=7)]),
           D(lean=20, extra=lambda r: [dirt_fling(r, 10.0, -6.0, 2, n=6, seed=9), bone_bits(r, 10.0, -6.0, 2, 4, seed=3, z=7)]),
           D()]
    d0 = D(lean=0, hand=(2.0, -16.0), hand2=(-2.0, -15.0), spade_at=((-3.0, -20.0), (6.0, -2.0)))
    d1 = D(lean=-10, bob=3.0, crouch=2.0, hand=(1.0, -8.0), hand2=(-4.0, -9.0), feet=((4.0, 0.0), (-4.0, 0.0)),
           spade_at=((-8.0, -10.0), (8.0, -1.0)))
    d2 = digger_corpse(0)
    corpse = digger_corpse(1)
    knock = D(lean=0, hand=(2.0, -15.0), hand2=(-3.0, -14.0), feet=((4.0, 0.0), (-3.0, 0.0)), spade_at=((-4.0, -19.0), (6.0, -1.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Spade", spd, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Unearth", une, [0.12, 0.1, 0.06, 0.1, 0.1, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssGravedigger", anims, outdir)


def digger_corpse(stage):
    r = Rig()
    r.poly([(-8, -1), (5, -2.5), (7, 0), (-9, 0)], "umber", 0.0, curve=0.5)
    r.ell(-6.5, -3.0, 3.0, 2.4, "rope", -0.5)
    r.stamp(DIGGER_HEAD, 7.0, 0.0 if stage else -1.0, 0.5, DIG_LEG, pivot=(4, 7))
    heap(r, -6.0, 0, 5.0, 5, seed=4, z=0.6, h=0.6)
    spade(r, (-10.0, -1.5), (9.0, -3.0) if not stage else (12.0, -0.5), 0.3)
    r.ell(2.0, -1.2, 1.0, 1.0, "lant", 0.7, flat=1 if stage else 2)
    if not stage: dust(r, 0, 0, 1, 1.6, mat="dirt")
    return r.resolve()


SYNC["OssGravedigger"] = {"Spade": [("SWING: the blade hits the floor at (12, -2); hit box 14 x 10 at (10, -4); dirt flies", 2)],
                          "Unearth": [("STAB: the spade bites the floor at (8, 0)", 2),
                                      ("HEAVE: two bone piles fly out (spawn them 12-30 px round the feet)", 5)]}


# ================================================================== GRAVETUSK (T2): a skeletal boar, dirt in its ribs, curled tusks
BOAR_HEAD = {
    # pivot (1, 5): the back of the jaw. A long boar skull, a yellowed tusk curling up past the snout.
    "shut": """
.LHL.....
LHHLLHL..
LkeLLLHL.
SBBLLLLHB.
.SBBBBLLLS
..SBTtBS.O
.......OO.
""",
    "open": """
.LHL.....
LHHLLHL..
LkeLLLHL.
SBBLLLLHB.
.SBBBBLLLS
..SBTt...O
...SB..OO.
....SBBS..
""",
}


def boar_body(r, hip, sh, legs, z=0.0, chest=3.6, ribs=5, dirt=True, face=1, mat="bone", leg_len=(3.6, 3.4), fleg_len=(3.4, 3.6),
              seed=3, leg_rad=0.8):
    """A skeletal boar: a heavy ribcage hung from an arched spine, short thick legs; grave dirt packed between the ribs."""
    import random
    rnd = random.Random(seed)
    hx, hy = hip; sx, sy = sh
    for k in (2, 3, 0, 1):
        fore = k in (1, 3); near = k < 2
        ax, ay = (sx - 0.6, sy + 1.2) if fore else (hx + 0.2, hy + 0.4)
        if not near: ax -= 0.8
        fx_, fy_ = legs[k]
        L = fleg_len if fore else leg_len
        kx, ky = ik(ax, ay, fx_, fy_ - 0.5, L[0], L[1], bend=(1 if fore else -1))
        zz = z + (1.0 if near else -1.0)
        bone(r, (ax, ay), (kx, ky), leg_rad, zz, "bone" if near else "dbone")
        if leg_rad > 1.0:
            bone(r, (kx, ky), (fx_, fy_ - 0.5), leg_rad * 0.75, zz + 0.01, "bone" if near else "dbone")
        else:
            lbone(r, (kx, ky), (fx_, fy_ - 0.5), zz + 0.01, near, knob=False)
        r.line(fx_ - 0.5, fy_, fx_ + 1.0, fy_, "bone" if near else "dbone", zz + 0.02, tone=2 if near else 1)
    # pelvis
    r.ell(hx, hy - 0.4, 1.8, 1.4, mat, z + 0.1, bias=0.05)
    # arched spine with tall processes over the shoulders
    mid = ((hx + sx) / 2, min(hy, sy) - 1.4)
    pts = [(hx - 1.0, hy - 1.0), mid, (sx + 0.4, sy - 1.6)]
    vertebrae(r, pts, z + 0.3, mat, tone_a=3, tone_b=1)
    for i in range(4):
        t = 0.55 + 0.12 * i
        px, py = lerp(mid[0], pts[2][0], t - 0.4), lerp(mid[1], pts[2][1], t - 0.4)
        r.line(px, py - 1, px - 0.5, py - 2.5 - (1.0 if i in (1, 2) else 0), mat, z + 0.25, tone=3 if i % 2 == 0 else 2)
    # dirt packed in the belly, then the ribs over it
    if dirt:
        r.ell((hx + sx) / 2 + 1.2, (hy + sy) / 2 + 1.4, abs(sx - hx) * 0.5, chest * 0.65, "dirt", z - 0.2, bias=-0.1)
        for i in range(5):
            r.dot(lerp(hx, sx, rnd.uniform(0.3, 0.9)), lerp(hy, sy, 0.5) + rnd.uniform(0.0, 2.6), "dirt", rnd.choice((1, 2, 3)), z - 0.15)
    for i in range(ribs):
        t = 0.15 + 0.15 * i
        x0, y0 = lerp(sx, mid[0], t * 1.2), lerp(sy, mid[1], t * 1.2) - 1.0
        L = chest * (1.0 - 0.08 * i)
        r.polyline([(x0, y0), (x0 + 0.8, y0 + L * 0.5), (x0 + 0.4, y0 + L)], mat, z + 0.35, tones=[3 if i % 2 == 0 else 2, 2, 1])


def tusk(lean=0.0, bob=0.0, legs=None, head_at=None, face="shut", extra=None, smear_pts=None, dust_at=None, crouch=0.0,
         stretch=0.0, glow=False):
    r = Rig()
    legs = legs or ((-6.0, 0.0), (5.0, 0.0), (-5.0, 0.0), (6.0, 0.0))
    T = Xf(lean, (0.0, -9.0))
    hip = T(-6.0 - stretch * 0.5, -9.0 + bob + crouch)
    sh = T(4.0 + stretch * 0.5, -10.5 + bob + crouch * 0.6)
    boar_body(r, hip, sh, legs, chest=5.6, ribs=6, leg_len=(4.4, 4.4), fleg_len=(4.8, 5.0))
    r.line(hip[0] - 1.5, hip[1] - 1.2, hip[0] - 3.5, hip[1] + 0.5, "bone", -0.2, tone=2)   # stub of a tail
    hx, hy = head_at or (sh[0] + 2.0, sh[1] + 0.5)
    vertebrae(r, [(sh[0] + 0.4, sh[1] - 1.2), (hx - 0.4, hy - 2.4)], 0.6, "bone", tone_a=3, tone_b=2)
    r.stamp(BOAR_HEAD[face], hx, hy, 2.0, BONE_LEG, pivot=(1, 5))
    # the great curled tusk, the beast's name: yellowed ivory sweeping up past the snout
    tk = chain(hx + 3.5, hy - 1.0, [(2.4, 20), (2.4, -25), (2.2, -70), (1.8, -115), (1.4, -150)])
    r.tube(tk, [1.3, 1.2, 1.0, 0.8, 0.6, 0.4], "obone", 2.4, bias=0.15)
    r.tube([(p[0] - 1.0, p[1] + 0.5) for p in tk[:4]], [0.9, 0.8, 0.6, 0.5], "obone", 1.2, bias=-0.4)
    if glow:
        r.dot(hx + 2, hy - 3, "mglow", 4, 2.1)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at, mat="dirt")
    if extra: extra(r)
    return r.resolve()


def tusk_sheet(outdir):
    Tk = tusk
    idle = [Tk(bob=[0, 0.3, 0.6, 0.3][i], face="shut" if i != 2 else "open") for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(Tk(lean=-4 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)), legs=gait(i, 6, 2.8, 1.6, base=((-5.0, 0.0), (4.0, 0.0), (-4.0, 0.0), (5.0, 0.0))),
                      stretch=0.8 * math.cos(ph)))
    # Gore (6): drop the head (0-1), HOOK up (2: tusks at (14, -10), the toss), follow (3), shake (4), settle (5)
    gore = [Tk(crouch=0.8, lean=8, head_at=(6.0, -5.0)),
            Tk(crouch=1.4, lean=12, head_at=(7.0, -3.5), legs=((-4.0, 0.0), (5.0, 0.0), (-3.0, 0.0), (6.0, 0.0))),
            Tk(lean=-14, head_at=(8.0, -10.5), face="open", legs=((-4.0, 0.0), (6.0, 0.0), (-3.0, 0.0), (7.0, 0.0)),
               smear_pts=[(10, -2), (13, -5), (15, -10), (14, -14)]),
            Tk(lean=-18, head_at=(7.0, -12.0), face="open"),
            Tk(lean=-6, head_at=(6.0, -8.5)),
            Tk()]
    # Charge (8): paw (0), lower the tusks (1), CHARGE (2-6: dust, tusks low), skid to a stop (7)
    charge = [Tk(lean=6, head_at=(6.0, -5.5), legs=((-5.0, 0.0), (4.0, -1.5), (-4.0, 0.0), (5.0, 0.0)), dust_at=(4.0, 0.0, 1, 0.8)),
              Tk(lean=10, crouch=1.0, head_at=(7.0, -4.5), glow=True)]
    for i in range(5):
        ph = i / 5 * math.tau
        charge.append(Tk(lean=12, bob=-0.6 * abs(math.sin(ph)), head_at=(8.0, -4.5), stretch=1.6,
                         legs=gait(i, 5, 3.4, 1.8, gallop=True, base=((-5.0, 0.0), (4.0, 0.0), (-4.0, 0.0), (5.0, 0.0))),
                         dust_at=(-7.0, 0.0, i % 2, 1.0), glow=True,
                         smear_pts=[(-12, -9 + i % 2), (-8, -9)] if i % 2 == 0 else None))
    charge.append(Tk(lean=-8, head_at=(6.0, -8.0), legs=((-3.0, 0.0), (6.0, 0.0), (-2.0, 0.0), (7.0, 0.0)), dust_at=(6.0, 0.0, 0, 1.4)))
    d0 = Tk(lean=-16, face="open", head_at=(6.0, -11.0))
    d1 = Tk(lean=-24, bob=2.0, face="open", head_at=(5.0, -5.0), legs=((-6.0, 0.0), (3.0, 0.0), (-5.0, 0.0), (5.0, -1.0)))
    d2 = tusk_corpse(0)
    corpse = tusk_corpse(1)
    knock = Tk(lean=-14, face="open", head_at=(5.0, -10.0), legs=((-6.0, 0.0), (3.0, 0.0), (-5.0, 0.0), (4.0, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.07] * 6),
             ("Gore", gore, [0.1, 0.1, 0.05, 0.08, 0.1, 0.12]),
             ("Charge", charge, [0.12, 0.12, 0.06, 0.06, 0.06, 0.06, 0.06, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssGravetusk", anims, outdir)


def tusk_corpse(stage):
    r = Rig()
    heap(r, -2.0, 0, 13.0 if stage else 10.0, 13, seed=31, h=0.6 if stage else 1.2)
    r.ell(-2.0, -1.0, 4.0, 1.0, "dirt", -0.4)
    r.stamp(BOAR_HEAD["open"], 4.0, 0.0 if stage else -1.0, 1.0, BONE_LEG, pivot=(1, 5))
    if not stage: dust(r, 0, 0, 1, 1.6, mat="dirt")
    return r.resolve()


SYNC["OssGravetusk"] = {"Gore": [("HOOK: tusks at (14, -10); hit box 14 x 14 at (11, -8)", 2)],
                        "Charge": [("tusks lowered: the scent bend starts", 1), ("CHARGE: move from here (box on the snout)", 2),
                                   ("stop", 7)]}


# ================================================================== BARGHEST (T2): a black grave hound with a broken church chain
BARG_HEADS = {
    "shut": """
.dD......
dGgD.....
DgGgD....
.DgEeggd.
..dgggggGg
..DgTTTTTd
...DtStS..
""",
    "open": """
.dD......
dGgD.....
DgGgD....
.DgEeggd.
..dgggggGg
..DgTtTtT.
...D.....
...dTtTt..
...DdddD..
""",
}
BARG_LEG = dict(BONE_LEG, g=("bhide", 2), G=("bhide", 3), d=("bhide", 1), D=("bhide", 0), e=("lant", 3), E=("lant", 4))


def barghest(lean=0.0, bob=0.0, legs=None, head_at=None, face="shut", tail=0.0, extra=None, smear_pts=None, dust_at=None,
             crouch=0.0, stretch=0.0, chain_swing=0.0, flare=False, alt=0.0):
    r = Rig()
    legs = legs or ((-5.0, 0.0), (5.0, 0.0), (-4.0, 0.0), (6.0, 0.0))
    legs = [(x, y - alt) for (x, y) in legs]
    T = Xf(lean, (0.0, -7.0 - alt))
    hip = T(-5.0 - stretch * 0.5, -7.0 + bob + crouch - alt)
    sh = T(4.0 + stretch * 0.5, -7.5 + bob + crouch * 0.6 - alt)
    dog_body(r, hip, sh, legs, mat="bhide", chest=4.2, haunch=3.2, waist=2.4, ribs=0, thick=1.8, leg_len=(3.8, 3.4), fleg_len=(3.4, 3.8),
             tail=[(2.4, 190 + tail), (2.2, 205 + tail), (2.0, 225 + tail), (1.6, 245 + tail)], paw="bhide", rib_mat="bhide")
    hx, hy = head_at or (sh[0] + 2.5, sh[1] - 3.0)
    r.tube([(sh[0] + 0.5, sh[1] - 1.0), (hx - 0.5, hy - 0.5)], [2.0, 1.5], "bhide", 0.6, bias=0.15)
    # broken church chain round the neck: links, one end swinging loose
    cx, cy = lerp(sh[0], hx, 0.55), lerp(sh[1], hy, 0.55) + 0.5
    for i in range(3):
        r.dot(cx - 1 + i, cy - 1 + (i % 2), "iron", 3 if i % 2 == 0 else 2, 0.8)
    pts = chain(cx - 0.5, cy + 1.0, [(1.5, 100 + chain_swing), (1.5, 110 + chain_swing * 1.3), (1.5, 120 + chain_swing * 1.6)])
    r.polyline(pts, "iron", 0.85, tones=[3, 2, 3])
    leg = dict(BARG_LEG)
    if flare: leg["e"] = ("lant", 4); leg["E"] = ("white", 4)
    r.stamp(BARG_HEADS[face], hx, hy, 2.0, leg, pivot=(2, 4))
    if flare:
        r.dot(hx + 1, hy - 2, "lant", 3, 2.1); r.dot(hx + 3, hy - 1, "lant", 2, 2.1)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def barg_sheet(outdir):
    B = barghest
    idle = [B(bob=[0, 0.3, 0.6, 0.3][i], face="shut" if i != 2 else "open", tail=[0, 8, 14, 6][i], chain_swing=[0, 10, 20, 10][i])
            for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(B(lean=-5 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)), legs=gait(i, 6, 3.4, 2.0, gallop=True,
                                                                                         base=((-5.0, 0.0), (5.0, 0.0), (-4.0, 0.0), (6.0, 0.0))),
                     face="open", tail=24 + 10 * math.sin(ph), stretch=1.4 * math.cos(ph), chain_swing=-30 + 20 * math.sin(ph)))
    lunge = ((-4.0, 0.0), (7.0, 0.0), (-3.0, 0.0), (8.0, 0.0))
    # Bite (6): two rending bites (2, 4: jaws at (15, -9))
    bite = [B(crouch=0.8, lean=4, face="open"),
            B(lean=-8, face="open", head_at=(7.0, -12.0)),
            B(lean=8, face="shut", head_at=(10.0, -9.0), legs=lunge, stretch=2.0, smear_pts=[(9, -14), (13, -12), (16, -9)]),
            B(lean=-6, face="open", head_at=(7.5, -11.5)),
            B(lean=10, face="shut", head_at=(10.5, -8.5), legs=lunge, stretch=2.4, smear_pts=[(10, -14), (14, -11), (17, -8)]),
            B(face="shut")]
    # Pounce (8): crouch (0-1), LEAP (2: untouchable from here), arc over (3-5), land (6: jaws, dust), turn (7)
    pounce = [B(crouch=1.5, lean=8, face="open"),
              B(crouch=2.4, lean=12, face="open", legs=((-3.0, 0.0), (4.0, 0.0), (-2.0, 0.0), (5.0, 0.0)), dust_at=(0.0, 0.0, 0, 1.2)),
              B(lean=-20, alt=3.0, stretch=3.0, face="open", legs=((-9.0, 1.0), (8.0, -2.0), (-8.0, 1.0), (9.0, -2.0))),
              B(lean=-6, alt=6.0, stretch=3.4, face="open", legs=((-9.0, 0.0), (9.0, 0.0), (-8.0, 0.0), (10.0, 0.0))),
              B(lean=8, alt=5.0, stretch=3.0, face="open", legs=((-8.0, -1.0), (8.0, 1.0), (-7.0, -1.0), (9.0, 1.0))),
              B(lean=18, alt=2.0, stretch=2.0, face="wide" if False else "open", legs=((-6.0, -1.0), (7.0, 1.0), (-5.0, -1.0), (8.0, 1.0))),
              B(lean=6, crouch=1.6, face="shut", head_at=(9.0, -7.0), dust_at=(2.0, 0.0, 0, 1.6)),
              B(face="shut")]
    d0 = B(lean=-14, face="open", head_at=(6.0, -12.0))
    d1 = B(lean=-28, bob=2.0, face="open", head_at=(4.0, -6.0), legs=((-7.0, 0.0), (4.0, 0.0), (-6.0, 0.0), (6.0, -1.0)))
    d2 = barg_corpse(0)
    corpse = barg_corpse(1)
    knock = B(lean=-14, face="open", head_at=(5.5, -11.0), legs=((-6.5, 0.0), (3.5, 0.0), (-5.5, 0.0), (4.5, 0.0)))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.065] * 6),
             ("Bite", bite, [0.1, 0.06, 0.05, 0.06, 0.05, 0.12]),
             ("Pounce", pounce, [0.12, 0.1, 0.06, 0.06, 0.06, 0.06, 0.12, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssBarghest", anims, outdir)


def barg_corpse(stage):
    r = Rig()
    r.ell(-0.5, -2.4, 6.5, 2.2, "bhide", 0.0)
    for (ax, ay, a) in ((-5.5, -3.0, -130), (-4.5, -3.2, -110), (3.5, -3.4, -70), (4.5, -3.2, -50)):
        pts = chain(ax, ay, [(2.8, a), (2.2, a + (10 if stage else 30))])
        r.tube(pts[:2], [1.1, 0.8], "bhide", 0.5)
        r.line(pts[1][0], pts[1][1], pts[2][0], pts[2][1], "bhide", 0.6, tone=3)
    leg = dict(BARG_LEG, e=("iron", 0), E=("iron", 0))
    r.stamp(BARG_HEADS["open"], 6.5, -0.5, 1.0, leg, pivot=(2, 4))
    r.polyline([(3.0, -2.0), (4.0, -1.0), (6.0, -0.5), (8.0, -0.5)], "iron", 1.1, tones=[3, 2, 3])
    if not stage: dust(r, 0, 0, 1, 1.4)
    return r.resolve()


SYNC["OssBarghest"] = {"Bite": [("BITE 1: jaws at (16, -9); box 14 x 12 at (13, -8)", 2), ("BITE 2", 4)],
                       "Pounce": [("LEAP: untouchable, fly to 20 px past the hero", 2), ("LAND: jaws + dust; vulnerable again", 6)]}


# ================================================================== OSSUARY PRIEST (T2): a robed priest of bones
PRIEST_HEAD = """
.H.L.H.
.L.H.L.
.LLLLL.
..yyy..
.LHHLB.
LkkLLkS
SkeBLeS
.SBnBS.
..TtTt.
"""
PRIEST_LEG = dict(BONE_LEG, y=("gold", 3), Y=("gold", 4))


def reliquary(r, x, y, z, swing=0.0, glow=3):
    """A reliquary lantern on a short chain: gold cage, a skull inside, marrow light."""
    ax, ay = x + swing * 0.3, y + 2.0
    r.line(x, y, ax, ay, "gold", z, tone=2)
    r.poly([(ax - 2.0, ay), (ax + 2.0, ay), (ax + 2.4, ay + 4.0), (ax - 2.4, ay + 4.0)], "gold", z + 0.01, normal=(-0.4, -0.3, 0.8))
    r.ell(ax, ay + 2.0, 1.4, 1.4, "mglow", z + 0.02, flat=glow)
    r.dot(ax, ay + 2.0, "bone", 4, z + 0.03); r.dot(ax + 1, ay + 2.0, "bone", 3, z + 0.03); r.dot(ax, ay + 3.0, "bone", 2, z + 0.03)
    r.line(ax - 2.0, ay, ax - 2.4, ay + 4.0, "gold", z + 0.04, tone=4)
    r.line(ax, ay - 0.5, ax, ay + 4.5, "gold", z + 0.04, tone=3)
    r.line(ax - 2.6, ay + 4.4, ax + 2.6, ay + 4.4, "gold", z + 0.04, tone=1)


def priest(lean=0.0, bob=0.0, hand=(6.0, -12.0), hand2=(-4.0, -11.0), sway=0.0, lamp=None, glow=3, hem=0.0, extra=None,
           raise_k=0.0):
    """The robe is a bell to the floor (it glides). lamp: where the reliquary hangs (default: from the near hand)."""
    r = Rig()
    T = Xf(lean, (0.0, 0.0))
    top = T(0.0, -16.5 + bob)
    # robe bell
    hl, hr = -6.0 + hem * 0.5, 6.0 + hem
    r.poly([(top[0] - 3.2, top[1]), (top[0] + 3.0, top[1]), (hr, -0.2), (hr - 2.0, 0.0), (0.0, -0.6), (hl + 2.0, 0.0), (hl, -0.2)],
           "fviol", 0.0, curve=0.8, normal=(-0.15, -0.2, 1.0))
    # gold orphrey down the front and at the hem
    r.line(top[0] + 0.5, top[1] + 1, 1.0 + hem * 0.3, -1.0, "gold", 0.05, tone=3)
    r.line(top[0] + 1.5, top[1] + 1, 2.0 + hem * 0.3, -1.0, "gold", 0.05, tone=2)
    r.polyline([(hl + 0.5, -0.6), (0.0, -1.0), (hr - 0.5, -0.6)], "gold", 0.05, tones=[2, 3])
    # finger-bone rosary across the chest
    for i in range(5):
        r.dot(top[0] - 2 + i, top[1] + 3 + abs(i - 2) * 0.5, "bone", 3 if i % 2 == 0 else 2, 0.06)
    # arms: wide sleeves
    for k, (hx, hy) in enumerate((hand2, hand)):
        near = k == 1
        s0 = (top[0] + (1.8 if near else -2.2), top[1] + 1.0)
        ex, ey = ik(s0[0], s0[1], hx, hy, 4.2, 4.2, bend=-1 if near else 1)
        r.tube([s0, (ex, ey)], [1.4, 1.8], "fviol", 1.4 if near else -0.8, bias=0.05 if near else -0.4)
        r.poly([(ex - 1.8, ey - 0.6), (ex + 1.8, ey - 0.6), (hx + 1.6, hy + 1.2), (hx - 1.6, hy + 1.2)], "fviol",
               1.41 if near else -0.79, bias=0.0 if near else -0.4)
        lbone(r, (lerp(ex, hx, 0.5), lerp(ey, hy, 0.5)), (hx, hy), 1.5 if near else -0.7, near)
    r.stamp(PRIEST_HEAD, top[0] + 1.0, top[1] + 0.5, 2.5, PRIEST_LEG, pivot=(3, 9))
    lx, ly = lamp or (hand[0], hand[1])
    reliquary(r, lx, ly, 2.0, swing=sway, glow=glow)
    if raise_k:
        for i in range(int(4 * raise_k)):
            a = -150 + i * 40
            r.dot(top[0] + 7 * math.cos(math.radians(a)), top[1] - 2 + 4 * math.sin(math.radians(a)), "spirit", 3, 6.0)
    if extra: extra(r)
    return r.resolve()


def priest_sheet(outdir):
    P = priest
    idle = [P(bob=[0, 0.4, 0.8, 0.4][i], sway=[0, 2, 0, -2][i], glow=[3, 3, 4, 3][i], hand=(6.0, -12.0 + [0, 0.4, 0.8, 0.4][i]),
              hand2=(-4.0, -11.0 + [0, 0.4, 0.8, 0.4][i])) for i in range(4)]
    run = [P(lean=8, bob=[0, -0.5, -0.8, -0.5, 0, 0.3][i], sway=[-4, -3, -1, 1, -1, -3][i], hem=[-1, 0, 1, 0, -1, -1.5][i],
             hand=(6.5, -12.0), hand2=(-4.0, -12.0)) for i in range(6)]
    # Bolt (6): lift the lantern (0-1), swing it forward (2), RELEASE (3: the bolt leaves the lantern at (12, -12)), hold (4), back (5)
    bolt = [P(hand=(4.0, -15.0), sway=-3, glow=3), P(lean=-6, hand=(2.0, -18.0), sway=-5, glow=4),
            P(lean=6, hand=(9.0, -15.0), sway=3, glow=4),
            P(lean=10, hand=(11.0, -13.0), sway=6, glow=2, extra=lambda r: [r.dots([(14, -10), (15, -9), (13, -8)], "mglow", 4, 7)]),
            P(lean=6, hand=(9.0, -12.0), sway=2, glow=2), P()]
    # Raise (8): arms up (0-2), the bones answer (3-5: RAISE on 5), arms sweep down (6-7)
    rs = [P(hand=(5.0, -16.0), hand2=(-5.0, -15.0), glow=3),
          P(lean=-4, hand=(5.0, -21.0), hand2=(-5.0, -20.0), glow=4, raise_k=0.25),
          P(lean=-6, hand=(6.0, -24.0), hand2=(-6.0, -23.0), glow=4, raise_k=0.5),
          P(lean=-6, hand=(6.0, -25.0), hand2=(-6.0, -24.0), glow=4, raise_k=0.75),
          P(lean=-6, hand=(6.0, -25.0), hand2=(-6.0, -24.0), glow=4, raise_k=1.0),
          P(lean=6, hand=(8.0, -12.0), hand2=(-7.0, -11.0), glow=4,
            extra=lambda r: [r.dots(arc_pts(0, -6, 10, 4, 0, 360, 12), "spirit", 3, 7)]),
          P(lean=4, hand=(7.0, -10.0), hand2=(-6.0, -9.0), glow=3), P()]
    d0 = P(lean=-10, hand=(4.0, -18.0), hand2=(-5.0, -17.0), glow=4)
    d1 = priest_fall(0)
    d2 = priest_fall(1)
    corpse = priest_fall(2)
    knock = P(lean=-12, hand=(3.0, -15.0), hand2=(-6.0, -13.0), sway=-6)
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.09] * 6),
             ("Bolt", bolt, [0.12, 0.12, 0.06, 0.06, 0.1, 0.12]),
             ("Raise", rs, [0.1, 0.1, 0.1, 0.1, 0.08, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssOssuaryPriest", anims, outdir)


def priest_fall(stage):
    r = Rig()
    if stage == 0:
        r.poly([(-6, -8), (2, -11), (7, -0.2), (-7, -0.2)], "fviol", 0.0, curve=0.8)
        r.stamp(PRIEST_HEAD, 2.0, -9.0, 1.0, PRIEST_LEG, pivot=(3, 9))
    else:
        r.poly([(-9, -2.5), (6, -3.5), (9, -0.2), (-10, -0.2)], "fviol", 0.0, curve=0.5)
        r.line(-8, -0.8, 8, -1.2, "gold", 0.1, tone=2)
        heap(r, -2.0, 0, 6.0, 5, seed=13, z=0.3, h=0.5)
        skullp(r, 7.0 if stage == 2 else 6.0, 0.0, "M", 0.5, eye=False)
    reliquary(r, -8.0, -5.0 if stage < 2 else -5.0, 0.6, glow=2 if stage < 2 else 1)
    return r.resolve()


SYNC["OssOssuaryPriest"] = {"Bolt": [("RELEASE: the marrow bolt leaves the lantern at (12, -12)", 3)],
                            "Raise": [("RAISE: the piles stand up as Bone Rats", 5)]}


# ================================================================== CARRION VULTURE (T2): a bald vulture, bone ruff, ragged wings
VULT_HEAD = {
    "shut": """
..rR...
.rRRr..
rRkeRo.
.rRRRooO
..rr.QoO
""",
    "open": """
..rR...
.rRRr..
rRkeRo.
.rRRRooO
..rr...O
....QQo.
""",
}
VULT_LEG = dict(BONE_LEG, r=("rawred", 2), R=("rawred", 3))


def vulture(r, x, y, z=0.0, wing_a=20.0, wing_b=None, lean=0.0, face="shut", neck=(3.0, -4.0), talons=0.0, flip=False,
            ruff=True, eye=True):
    f = -1 if flip else 1
    T = Xf(lean * f, (x, y))
    F = lambda dx, dy: T(x + dx * f, y + dy)
    wb = wing_a if wing_b is None else wing_b
    wing(r, F(0.5, -1.6), wb + 6, 11.0, z - 1.0, near=False, n=5, chord=4.0, face=f)
    # tail
    r.poly([F(-2.0, -0.6), F(-7.0, 1.0), F(-6.5, 2.4), F(-2.0, 1.6)], "feath", z - 0.3, normal=(-0.3, -0.5, 0.8))
    # talons
    for k, dx in enumerate((1.2, -0.6)):
        lx, ly = F(dx, 2.4)
        tx, ty = lx + talons * f * 1.5, ly + 2.4 - talons * 0.4
        r.line(lx, ly, tx, ty, "obone", z + (0.4 if k == 0 else -0.4), tone=3 if k == 0 else 2)
        r.line(tx, ty, tx + 1.4 * f, ty + 0.6, "obone", z + (0.41 if k == 0 else -0.39), tone=4 if k == 0 else 2)
    bx, by = F(0.0, 0.0)
    r.ell(bx, by, 5.6, 4.4, "feath", z, ang=-10 * f, bias=0.1)
    # bone-feather ruff round the base of the neck
    if ruff:
        for i in range(5):
            a = math.radians(-140 + i * 32)
            cx, cy = F(2.2, -2.0)
            r.line(cx, cy, cx + 2.4 * math.cos(a) * f, cy + 2.0 * math.sin(a), "bone", z + 0.2, tone=3 if i % 2 == 0 else 2)
    # bare raw neck to the head
    n0 = F(2.4, -2.2); hx, hy = F(neck[0] + 2.4, neck[1] - 2.0)
    r.tube([n0, ((n0[0] + hx) / 2, (n0[1] + hy) / 2 - 0.6), (hx, hy)], [1.2, 0.9, 0.8], "rawred", z + 0.25, bias=0.1)
    leg = dict(VULT_LEG)
    if not eye: leg["e"] = ("iron", 0)
    r.stamp(VULT_HEAD[face], hx, hy, z + 0.3, leg, pivot=(1, 3), flip=flip)
    wing(r, F(0.8, -1.4), wing_a, 12.0, z + 0.6, near=True, n=5, chord=5.5, face=f)


def vult_frame(x=0.0, alt=6.0, **kw):
    r = Rig()
    extra = kw.pop("extra", None); sm = kw.pop("smear_pts", None); shadow = kw.pop("shadow", True)
    vulture(r, x, -alt - 6.0, **kw)
    if shadow:
        r.ell(x, -0.3, 3.6, 0.8, "tar", -5.0, flat=2)
    if sm: smear(r, sm, "bone", 4)
    if extra: extra(r)
    return r.resolve()


def vult_sheet(outdir):
    V = vult_frame
    idle = [V(alt=[3.0, 3.5, 4.0, 3.5][i], wing_a=[60, 100, 50, 20][i], wing_b=[70, 115, 60, 30][i]) for i in range(4)]
    run = [V(alt=6.0 + [0, 0.8, 1.2, 0.8, 0.2, -0.2][i], lean=12, wing_a=[115, 80, 30, 0, 40, 90][i], wing_b=[115, 90, 40, 10, 50, 95][i])
           for i in range(6)]
    # Rake (6): rise (0), fold for the dive (1), RAKE through (2: talons at (8, -4)), sweep up (3-4), level (5)
    rake = [V(alt=7.0, lean=-10, wing_a=100), V(alt=8.0, lean=-6, wing_a=130, wing_b=130, talons=-0.5),
            V(x=3.0, alt=2.0, lean=26, wing_a=10, wing_b=20, talons=2.0, face="open", smear_pts=[(-6, -16), (0, -12), (6, -7), (9, -4)]),
            V(x=5.0, alt=3.0, lean=10, wing_a=60, talons=1.5, extra=lambda r: bone_bits(r, 10, -3, 0, 3, seed=2, z=6, mat="rawred")),
            V(x=3.0, alt=6.0, lean=-10, wing_a=110), V(alt=6.0, wing_a=50)]
    # Plummet (9): beat up (0-1), climb out of sight (2: the shadow appears under the hero), gone (3), drop in high (4: arrives
    # above the mark), falling (5), IMPACT (6: hit at the feet), shake (7), climb back (8)
    plum = [V(alt=7.0, wing_a=120, wing_b=120), V(alt=12.0, lean=-12, wing_a=20, wing_b=30),
            V(alt=22.0, lean=-20, wing_a=120, wing_b=120, shadow=False),
            far_speck(),
            V(alt=26.0, lean=60, wing_a=-20, wing_b=-10, face="open", shadow=False),
            V(alt=12.0, lean=70, wing_a=-30, wing_b=-20, face="open", smear_pts=[(0, -40), (0, -34), (1, -28)]),
            V(alt=1.0, lean=10, wing_a=130, wing_b=125, talons=1.5, face="open", extra=lambda r: dust(r, 0.0, 0.0, 0, 1.6, n=4)),
            V(alt=2.0, lean=-6, wing_a=90, extra=lambda r: dust(r, 0.0, 0.0, 1, 1.8, n=4)),
            V(alt=5.0, wing_a=110)]
    d0 = V(alt=6.0, lean=-30, wing_a=130, wing_b=80, face="open")
    d1 = V(alt=2.0, lean=-80, wing_a=150, wing_b=110, face="open", extra=lambda r: bone_bits(r, 0, -4, 1, 5, seed=5, z=6, mat="feath"))
    d2 = vult_corpse(0)
    corpse = vult_corpse(1)
    knock = V(alt=6.0, lean=-30, wing_a=130, wing_b=120, face="open")
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.075] * 6),
             ("Rake", rake, [0.1, 0.1, 0.05, 0.08, 0.1, 0.12]),
             ("Plummet", plum, [0.1, 0.1, 0.1, 0.35, 0.05, 0.05, 0.08, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssCarrionVulture", anims, outdir)


def far_speck():
    """High over the room: the vulture circling far above, wings spread (the frame between the climb and the drop)."""
    r = Rig()
    r.poly([(-11, -35), (-4, -40), (0, -38), (4, -40), (11, -35), (4, -36.5), (0, -34), (-4, -36.5)], "feath", 0, bias=0.35)
    r.line(-11, -35, -4, -40, "feath", 0.1, tone=4); r.line(4, -40, 11, -35, "feath", 0.1, tone=3)
    r.dot(0, -39, "rawred", 3, 0.2); r.dot(1, -39, "bone", 4, 0.2); r.dot(0, -40, "rawred", 2, 0.2)
    r.ell(0, -0.3, 2.5, 0.6, "tar", -1, flat=1)
    return r.resolve()


def vult_corpse(stage):
    r = Rig()
    vulture(r, 0.0, -2.6, 0.0, wing_a=-30 if stage else 10, wing_b=170, lean=-90 if stage else -60, face="open", eye=False)
    if not stage: bone_bits(r, 0, -2, 2, 5, seed=9, z=6, mat="feath")
    return r.resolve()


SYNC["OssCarrionVulture"] = {"Rake": [("RAKE: talons at (9, -4); box 16 x 12 at (6, -5); fly through", 2)],
                             "Plummet": [("climb: mark the hero's spot (shadow), untouchable", 2), ("arrive over the mark", 4),
                                         ("IMPACT at the feet: hit 18 x 10, vulnerable again", 6)]}
NOTES["OssCarrionVulture"] = "Flies (hover 6 px). Plummet frame 3 is empty on purpose: it is high above the room."

JOBS = [("OssBoneLancer", lancer_sheet), ("OssGravedigger", digger_sheet), ("OssGravetusk", tusk_sheet),
        ("OssBarghest", barg_sheet), ("OssOssuaryPriest", priest_sheet), ("OssCarrionVulture", vult_sheet)]
