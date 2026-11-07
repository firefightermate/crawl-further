"""Ossivar tier 3, first half: Charnel Rider (mounted and unhorsed), Spinehook, Tombwright, Coffin Bearer, Bone Mammoth,
Razorback. Built through ossivar_v2_rigs.py. T3 idle limit 42 x 40."""
import math
from ossivar_v2_rigs import (Rig, Xf, chain, ik, lerp, line_px, skullp, lbone, skeleton, vertebrae, bone, heap, bone_bits,
                             dust, smear, arc_pts, sheet, tail_anims, SYNC, NOTES, BONE_LEG, gait, J)
from ossivar_v2_t2 import spine_spear, boar_body, BOAR_HEAD, dirt_fling

J.RAMPS.update({k: [J._h(c) for c in v] for k, v in {
    "coffin": ["1c1216", "3a262c", "5a3c44", "7c5660", "9c7880"],    # black lacquered coffin wood
}.items()})


# ================================================================== CHARNEL RIDER (T3): a skeleton knight on a skeletal horse
HORSE_HEAD = """
..LHL.......
.LHHLLHL....
LHkeLLLLHL..
SBBLLLLLLLHL
.SBBBBBBBBLS
..STtTtTtS..
"""
HELM = """
.iIIi.
iIIIIi
ikkkeI
iIIIIi
.iIiI.
"""
HELM_LEG = dict(BONE_LEG, i=("iron", 2), I=("iron", 3))


def horse(r, x, y, legs, z=0.0, lean=0.0, neck=(8.0, -9.0), cracked=False, barding=True, flap=0.0, head_drop=0.0):
    """A skeletal horse: (x, y) = the middle of its back. legs: near hind, near fore, far hind, far fore."""
    T = Xf(lean, (x, y))
    hip = T(x - 7.5, y + 1.0)
    sh = T(x + 6.5, y + 0.5)
    boar_body(r, hip, sh, legs, z, chest=6.0, ribs=6, dirt=False, leg_len=(6.0, 6.2), fleg_len=(6.2, 6.4), seed=9, leg_rad=1.1)
    # neck and head
    hx, hy = T(x + neck[0] + 4.0, y + neck[1] + head_drop)
    r.tube([(sh[0] + 0.5, sh[1] - 1.0), ((sh[0] + hx) / 2 + 1.0, (sh[1] + hy) / 2 - 0.5), (hx, hy - 1.5)], [2.0, 1.6, 1.3], "bone", z + 0.45,
           bias=-0.05)
    vertebrae(r, [(sh[0] + 0.5, sh[1] - 2.0), ((sh[0] + hx) / 2 + 1.0, (sh[1] + hy) / 2 - 1.5), (hx - 1.0, hy - 2.0)], z + 0.5, "bone",
              proc=1, tone_a=3, tone_b=1)
    r.stamp(HORSE_HEAD, hx, hy, z + 0.6, BONE_LEG, pivot=(2, 4))
    # tail: a few loose vertebrae
    r.polyline(chain(hip[0] - 1.0, hip[1] - 1.0, [(2.0, 170), (2.0, 140), (2.0, 120)]), "dbone", z - 0.3, tones=[2, 1, 2])
    if barding:
        # black barding over the back, tattered fringe that flaps
        bx0, by0 = T(x - 9.5, y - 1.0); bx1, by1 = T(x + 8.0, y - 1.5)
        pts = [(bx0, by0), (bx1, by1), T(x + 8.5, y + 3.0)]
        for i in range(7):
            t = i / 6.0
            pts.append((lerp(bx1 + 0.5, bx0, t), lerp(by1, by0, t) + 6.6 + (1.4 if i % 2 else 0) + math.sin(flap + i) * 0.6))
        r.poly(pts, "tar", z + 0.8, curve=0.4, normal=(-0.2, -0.6, 0.8))
        r.line(bx0, by0, bx1, by1, "marrow", z + 0.81, tone=2)
    if cracked:
        for (dx, dy) in ((2.0, 4.0), (-4.0, 3.0)):
            cx, cy = T(x + dx, y + dy)
            r.polyline([(cx, cy), (cx + 1, cy + 1), (cx, cy + 2), (cx + 1, cy + 3)], "iron", z + 1.0, tone=0)
    return hip, sh


def rider_body(r, seat, lean=0.0, hand=(6.0, -6.0), hand2=(-2.0, -6.0), jaw=0, z=2.0, leg_foot=None):
    """The skeleton knight sitting at `seat` (its hip)."""
    neck, shp = skeleton(r, seat, lean, hands=(hand, hand2), feet=(leg_foot or (seat[0] + 2.0, seat[1] + 7.0), (seat[0] - 1.0, seat[1] + 6.0)),
                         z=z, arm=(4.6, 4.4), leg=(4.2, 4.2), ribs=4, rib_w=5, torso=8.0, elbows=(-1, 1), knees=(-1, -1),
                         skip=())
    r.ell(neck[0] + 0.3, neck[1] + 1.6, 3.0, 1.4, "iron", z + 0.6, bias=0.1)    # pauldron / gorget
    r.stamp(HELM, neck[0] + 1.0, neck[1] + 0.5, z + 0.8, HELM_LEG, pivot=(2, 5))
    return neck


def rider(lean=0.0, bob=0.0, legs=None, lance=None, hand=None, hand2=None, cracked=False, jaw=0, flap=0.0, extra=None,
          smear_pts=None, dust_at=None, horse_lean=0.0, head_drop=0.0, pen=0.0, rider_lean=-4.0):
    r = Rig()
    legs = legs or ((-8.0, 0.0), (6.0, 0.0), (-6.5, 0.0), (7.5, 0.0))
    back = (0.0, -14.0 + bob)
    hip, sh = horse(r, back[0], back[1], legs, z=0.0, lean=horse_lean, cracked=cracked, flap=flap, head_drop=head_drop)
    seat = (back[0] - 1.0, back[1] - 1.5)
    hand = hand or (seat[0] + 6.0, seat[1] - 6.0)
    hand2 = hand2 or (seat[0] - 1.0, seat[1] - 5.0)
    rider_body(r, seat, rider_lean, hand, hand2, jaw)
    if lance is None:
        lance = ((hand[0] - 6.0, hand[1] + 5.0), (hand[0] + 8.0, hand[1] - 16.0))
    spine_spear(r, lance[0], lance[1], 3.5, pennant=pen)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def foot_knight(lean=4.0, bob=0.0, feet=((3.0, 0.0), (-3.0, 0.0)), hand=(6.0, -13.0), hand2=(-3.0, -13.0), lance=None, jaw=0,
                extra=None, smear_pts=None, crouch=0.0, pen=0.0, dust_at=None):
    r = Rig()
    hip = (-0.5, -11.0 + bob + crouch)
    neck, sh = skeleton(r, hip, lean, hands=(hand, hand2), feet=feet, arm=(4.8, 4.6), leg=(5.8, 5.6), ribs=4, rib_w=5, torso=8.5,
                        elbows=(-1, 1), knees=(1, 1))
    r.ell(neck[0] + 0.3, neck[1] + 1.6, 3.0, 1.4, "iron", 2.6, bias=0.1)
    r.stamp(HELM, neck[0] + 1.0, neck[1] + 0.5, 2.8, HELM_LEG, pivot=(2, 5))
    if lance is None:
        lance = ((hand2[0] - 2.0, hand2[1] + 8.0), (hand[0] + 4.0, hand[1] - 16.0))
    if lance:
        spine_spear(r, lance[0], lance[1], 2.2, pennant=pen)
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


HL = ((-8.0, 0.0), (6.0, 0.0), (-6.5, 0.0), (7.5, 0.0))


def rider_sheet(outdir):
    Rd = rider
    idle = [Rd(bob=[0, 0.3, 0.6, 0.3][i], flap=i * 1.2, pen=i * 1.4, head_drop=[0, 0.5, 1.0, 0.5][i]) for i in range(4)]
    cidle = [Rd(bob=[0, 0.3, 0.6, 0.3][i], flap=i * 1.2, pen=i * 1.4, cracked=True, horse_lean=-3,
                legs=((-8.0, 0.0), (5.0, -1.5 + 0.5 * (i % 2)), (-6.5, 0.0), (7.5, 0.0)), head_drop=1.5) for i in range(4)]

    def runf(i, cracked=False, n=6):
        ph = i / n * math.tau
        lg = gait(i, n, 4.0, 2.6, gallop=True, base=HL)
        if cracked and i % 3 == 0: lg[1] = (lg[1][0] - 1.0, lg[1][1] - 1.5)
        return Rd(bob=-1.2 * abs(math.sin(ph)) + (0.8 if cracked and i % 3 == 0 else 0), horse_lean=-4 * math.sin(ph), legs=lg,
                  flap=i * 1.5, pen=i * 1.6, cracked=cracked, rider_lean=4,
                  lance=((-4.0, -16.0), (14.0, -36.0)))
    run = [runf(i) for i in range(6)]
    crun = [runf(i, True) for i in range(6)]
    # Sweep (6): lance back (0-1), SWEEP across (2: tip arc ahead, (24, -14)), through (3), recover (4-5)
    sweep = [Rd(hand=(-1.0, -22.0), lance=((6.0, -18.0), (-12.0, -32.0)), rider_lean=-10),
             Rd(hand=(-3.0, -21.0), lance=((6.0, -16.0), (-14.0, -26.0)), rider_lean=-16, horse_lean=-3),
             Rd(hand=(8.0, -19.0), lance=((-2.0, -20.0), (26.0, -14.0)), rider_lean=14, horse_lean=3,
                smear_pts=[(-8, -34), (8, -34), (20, -26), (27, -15)]),
             Rd(hand=(7.0, -16.0), lance=((-2.0, -22.0), (22.0, -4.0)), rider_lean=16),
             Rd(hand=(6.0, -18.0), rider_lean=4), Rd()]
    # Joust (11): lower the lance (0-2), GALLOP (3-8: lance couched at (30, -16)), wheel round (9-10)
    couch = ((-6.0, -18.0), (30.0, -16.0))
    joust = [Rd(hand=(6.0, -19.0), lance=((-3.0, -16.0), (18.0, -30.0)), rider_lean=0),
             Rd(hand=(6.0, -19.0), lance=((-6.0, -19.0), (24.0, -22.0)), rider_lean=8, legs=((-8.0, 0.0), (6.0, -2.5), (-6.5, 0.0), (7.5, 0.0))),
             Rd(hand=(6.0, -18.0), lance=couch, rider_lean=14, legs=((-8.0, 0.0), (6.0, 0.0), (-6.5, 0.0), (7.5, -2.0)), dust_at=(8.0, 0.0, 0, 1.0))]
    for i in range(6):
        ph = i / 6 * math.tau
        joust.append(Rd(bob=-1.2 * abs(math.sin(ph)), horse_lean=-3 * math.sin(ph), legs=gait(i, 6, 5.0, 3.0, gallop=True, base=HL),
                        hand=(6.0, -18.0 - abs(math.sin(ph))), lance=((couch[0][0], couch[0][1] - abs(math.sin(ph))), (couch[1][0], couch[1][1] - abs(math.sin(ph)))),
                        rider_lean=16, flap=i * 2.0, pen=i * 2.0, dust_at=(-10.0, 0.0, i % 2, 1.0),
                        smear_pts=[(-20, -10 - i % 2), (-14, -10)] if i % 2 == 0 else None))
    joust += [Rd(horse_lean=-12, legs=((-6.0, 0.0), (8.0, -4.0), (-4.5, 0.0), (9.5, -4.0)), rider_lean=-6, head_drop=-2.0,
                 dust_at=(-6.0, 0.0, 0, 1.4)),
              Rd(horse_lean=-6, rider_lean=0, dust_at=(-6.0, 0.0, 1, 1.4))]
    # Unhorse (7): the horse buckles (0-1), falls apart (2-3: three piles), the rider rolls clear (4), stands (5-6)
    un = [Rd(cracked=True, horse_lean=-10, legs=((-8.0, 0.0), (4.0, -1.0), (-6.5, 0.0), (6.0, 0.0)), head_drop=3.0, rider_lean=-14,
             extra=lambda r: bone_bits(r, 0, -10, 0, 6, seed=3, z=5)),
          Rd(cracked=True, bob=4.0, horse_lean=8, legs=((-9.0, 0.0), (3.0, 0.0), (-7.5, 0.0), (5.0, 0.0)), head_drop=6.0, rider_lean=-20,
             extra=lambda r: bone_bits(r, 0, -8, 1, 8, seed=4, z=5)),
          unhorse_fall(0), unhorse_fall(1), unhorse_fall(2),
          foot_knight(lean=20, crouch=2.0, hand=(7.0, -6.0), hand2=(-4.0, -6.0), extra=lambda r: piles3(r)),
          foot_knight(extra=lambda r: piles3(r, 1))]
    fk = foot_knight
    fidle = [fk(bob=[0, 0.3, 0.6, 0.3][i], pen=i * 1.4, hand=(6.0, -13.0 + [0, 0.3, 0.6, 0.3][i])) for i in range(4)]
    frun = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (0.5 + 3.8 * math.cos(ph), -max(0.0, 2.2 * math.sin(ph)))
        f2 = (-0.5 - 3.8 * math.cos(ph), -max(0.0, -2.2 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        frun.append(fk(lean=12, bob=b, feet=(f1, f2), hand=(7.0, -14.0 + b), hand2=(-2.0, -14.0 + b), pen=i * 1.6,
                       lance=((-8.0, -10.0 + b), (16.0, -26.0 + b))))
    # FootThrow (6): lance back over the shoulder (0-1), THROW (2: it leaves the hand at (10, -22)), follow (3), draw a spare (4-5)
    fthrow = [fk(lean=-6, hand=(-2.0, -22.0), lance=((8.0, -22.0), (-14.0, -24.0))),
              fk(lean=-14, hand=(-5.0, -21.0), lance=((5.0, -22.0), (-17.0, -22.0)), crouch=1.0),
              fk(lean=18, hand=(10.0, -20.0), lance=False, feet=((5.0, 0.0), (-3.0, 0.0)), smear_pts=[(-12, -26), (0, -27), (8, -24), (12, -21)]),
              fk(lean=20, hand=(9.0, -12.0), lance=False, feet=((5.0, 0.0), (-3.0, 0.0))),
              fk(lean=6, hand=(-3.0, -18.0), lance=False),
              fk()]
    # FootThrust (8): crouch (0-1), RUN IN (2-5: lance level, tip at (24, -13)), skid (6), up (7)
    lvl = lambda b: ((-6.0, -13.0 + b), (24.0, -13.0 + b))
    fthrust = [fk(crouch=1.0, hand=(4.0, -13.0), lance=((-10.0, -12.0), (18.0, -14.0))),
               fk(crouch=1.6, lean=10, hand=(3.0, -12.0), lance=((-12.0, -12.0), (16.0, -12.0)))]
    for i in range(4):
        ph = i / 4 * math.tau
        f1 = (1.5 + 4.0 * math.cos(ph), -max(0.0, 2.0 * math.sin(ph)))
        f2 = (-0.5 - 4.0 * math.cos(ph), -max(0.0, -2.0 * math.sin(ph)))
        fthrust.append(fk(lean=22, feet=(f1, f2), hand=(10.0, -13.0), hand2=(3.0, -13.0), lance=lvl(0), dust_at=(-6.0, 0.0, i % 2, 1.0),
                          smear_pts=[(-14, -9), (-9, -9)]))
    fthrust += [fk(lean=-6, feet=((5.0, 0.0), (-4.0, 0.0)), hand=(8.0, -13.0), lance=lvl(0), dust_at=(5.0, 0.0, 0, 1.2)), fk()]
    fdeath = [fk(lean=-12, jaw=2, hand=(1.0, -18.0), lance=False), fk(lean=-30, bob=4.0, crouch=3.0, hand=(0.0, -6.0), hand2=(-7.0, -8.0),
                                                                      feet=((4.0, 0.0), (-5.0, 0.0)), lance=False),
              rider_corpse(0, foot=True), rider_corpse(1, foot=True)]
    d0 = Rd(cracked=True, horse_lean=-12, rider_lean=-20, head_drop=-2.0, legs=((-8.0, 0.0), (7.0, -4.0), (-6.5, 0.0), (8.5, -4.0)))
    d1 = unhorse_fall(0)
    d2 = rider_corpse(0)
    corpse = rider_corpse(1)
    knock = Rd(horse_lean=-8, rider_lean=-16, legs=((-9.0, 0.0), (5.0, 0.0), (-7.5, 0.0), (6.5, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.075] * 6),
             ("IdleCracked", cidle, [0.16, 0.12, 0.16, 0.12]), ("RunCracked", crun, [0.08] * 6),
             ("Sweep", sweep, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Joust", joust, [0.18, 0.16, 0.16, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 0.12]),
             ("Unhorse", un, [0.12, 0.1, 0.1, 0.12, 0.12, 0.12, 0.14]),
             ("FootIdle", fidle, [0.16, 0.12, 0.16, 0.12]), ("FootRun", frun, [0.07] * 6),
             ("FootThrow", fthrow, [0.12, 0.12, 0.05, 0.1, 0.12, 0.12]),
             ("FootThrust", fthrust, [0.1, 0.1, 0.07, 0.07, 0.07, 0.07, 0.1, 0.12]),
             ("FootDeath", fdeath, [0.1, 0.1, 0.12, 0.4])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssCharnelRider", anims, outdir)


def piles3(r, k=0):
    for i, x in enumerate((-12.0, -4.0, 9.0)):
        heap(r, x, 0, 5.0, 4, seed=40 + i, z=-1.0 + i * 0.1, h=0.6)


def unhorse_fall(stage):
    r = Rig()
    if stage == 0:
        heap(r, 0.0, 0, 24.0, 22, seed=50, h=2.0)
        r.stamp(HORSE_HEAD, 12.0, -1.0, 1.0, BONE_LEG, pivot=(2, 4))
        r.poly([(-10, -6), (8, -7), (6, -2), (-9, -2)], "tar", 0.5, curve=0.3)
        rider_body(r, (-2.0, -8.0), -40, (5.0, -12.0), (-6.0, -10.0), 2, z=2.0)
    elif stage == 1:
        piles3(r)
        r.poly([(-6, -1.5), (6, -2.2), (7, 0), (-7, 0)], "tar", 0.4, curve=0.3)
        rider_body(r, (2.0, -4.0), -70, (8.0, -4.0), (-3.0, -6.0), 2, z=2.0, leg_foot=(7.0, -1.0))
    else:
        piles3(r)
        r.poly([(-6, -1.5), (6, -2.2), (7, 0), (-7, 0)], "tar", 0.4, curve=0.3)
        rider_body(r, (1.0, -6.0), 30, (8.0, -2.0), (-4.0, -3.0), 1, z=2.0, leg_foot=(5.0, 0.0))
    return r.resolve()


def rider_corpse(stage, foot=False):
    r = Rig()
    if not foot:
        heap(r, 0.0, 0, 26.0 if stage else 22.0, 24, seed=60, h=0.8 if stage else 1.6)
        r.stamp(HORSE_HEAD, 13.0, 0.0, 1.0, BONE_LEG, pivot=(2, 4))
        r.poly([(-10, -2.5), (8, -3.0), (9, 0), (-11, 0)], "tar", 0.5, curve=0.3)
    else:
        heap(r, 0.0, 0, 16.0 if stage else 12.0, 14, seed=61, h=0.6 if stage else 1.2)
    r.stamp(HELM, -8.0, 0.0 if stage else -1.0, 1.2, HELM_LEG, pivot=(2, 5))
    spine_spear(r, (-14.0, -0.5), (12.0, -1.5), 0.8, pennant=1.0)
    if not stage: dust(r, 0, 0, 1, 2.0)
    return r.resolve()


SYNC["OssCharnelRider"] = {
    "Sweep": [("SWEEP: the lance tip arcs through (26, -14); hit box 30 x 20 at (16, -14)", 2)],
    "Joust": [("lance lowering (tell, 0.5 s)", 0), ("GALLOP: move 230 px/s, lance tip box at (28, -16), trample box at (8, -6)", 3),
              ("wheel round: stop", 9)],
    "Unhorse": [("the horse falls apart: three bone piles at x -12, -4, 9", 3), ("on foot: swap to the Foot* anims", 6)],
    "FootThrow": [("THROW: the lance leaves the hand at (10, -21)", 2)],
    "FootThrust": [("RUN IN: move from here, tip box at (22, -13)", 2), ("stop", 6)],
}
NOTES["OssCharnelRider"] = ("Mounted: Idle/Run (IdleCracked/RunCracked from 7 health: the horse limps and cracks). Unhorse plays at 5 "
                            "health; then the Foot* set (FootIdle, FootRun, FootThrow, FootThrust, FootDeath) is the rider alone, "
                            "about 12 x 27 px: shrink the hurtbox to it.")


# ================================================================== SPINEHOOK (T3): a hunched skeleton whaler
SOUWESTER = """
...ttt...
..tTTTt..
.tTTTTTt.
ttttttttt
"""
SOU_LEG = {"t": ("tar", 2), "T": ("tar", 3)}


def harpoon_head(r, tip, d, z):
    ux, uy = d
    nx, ny = -uy, ux
    bx, by = tip[0] - ux * 4, tip[1] - uy * 4
    r.poly([(tip[0], tip[1]), (bx + nx * 1.8, by + ny * 1.8), (bx + ux, by + uy), (bx - nx * 1.8, by - ny * 1.8)], "bone", z,
           normal=(-0.4, -0.6, 0.7))
    r.dot(tip[0], tip[1], "bone", 4, z + 0.01)
    r.dot(bx + nx * 1.8 - ux, by + ny * 1.8 - uy, "bone", 3, z + 0.01); r.dot(bx - nx * 1.8 - ux, by - ny * 1.8 - uy, "bone", 2, z + 0.01)


def spinehook(lean=26.0, bob=0.0, feet=((3.0, 0.0), (-3.0, 0.0)), hook=(8.0, -12.0), hand=(5.0, -16.0), harp=None, rope=None,
              jaw=0, extra=None, smear_pts=None, crouch=0.0, coil=1.0, dust_at=None):
    """hook: where the hook-hand is. harp: (butt, tip) of the harpoon in the other hand (None: held upright; False: thrown)."""
    r = Rig()
    hip = (-1.0, -11.0 + bob + crouch)
    neck, sh = skeleton(r, hip, lean, hands=(hook, hand), feet=feet, arm=(5.0, 5.0), leg=(5.6, 5.4), ribs=5, rib_w=5, torso=9.5,
                        elbows=(-1, 1), knees=(1, 1))
    # tar oilskin coat hanging off the shoulders
    r.poly([(neck[0] - 5.5, neck[1] + 0.5), (neck[0] + 3.0, neck[1] + 1.0), (hip[0] + 5.0, hip[1] + 7.0), (hip[0] + 1.0, hip[1] + 8.0),
            (hip[0] - 3.0, hip[1] + 7.2), (hip[0] - 7.5, hip[1] + 8.0)], "tar", -0.5, curve=0.6, normal=(-0.2, -0.3, 1.0))
    r.line(neck[0] + 2.0, neck[1] + 1.5, hip[0] + 3.5, hip[1] + 6.0, "tar", -0.45, tone=4)
    # rope coiled on the back
    if coil:
        cx, cy = neck[0] - 4.5, neck[1] + 4.0
        for k in range(4):
            r.ell(cx, cy, 5.4 - k * 0.6, 4.4 - k * 0.6, "rope", -1.0 + k * 0.01, flat=3 - (k % 2))
        r.ell(cx, cy, 1.6, 1.2, "tar", -0.95, flat=1)
    # the hook for a hand
    hx, hy = hook
    r.polyline([(hx, hy), (hx + 1.5, hy + 0.5), (hx + 2.0, hy + 2.0), (hx + 1.0, hy + 3.0)], "iron", 2.0, tones=[3, 4, 2])
    skullp(r, neck[0] + 1.2, neck[1] + 0.5, "XL", 3.0, jaw=jaw)
    r.stamp(SOUWESTER, neck[0] + 1.2, neck[1] - 7.5, 3.2, SOU_LEG, pivot=(4, 3))
    if harp is None:
        harp = ((hand[0] - 1.0, hand[1] + 10.0), (hand[0] + 1.0, hand[1] - 9.0))
    if harp:
        (a, b) = harp
        L = math.hypot(b[0] - a[0], b[1] - a[1]); d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        vertebrae(r, [a, b], 2.4, "bone", tone_a=3, tone_b=1)
        harpoon_head(r, b, d, 2.5)
    if rope:
        r.polyline(rope, "bone", 2.3, tones=[3 if i % 2 == 0 else 1 for i in range(len(rope) - 1)])
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def spine_sheet(outdir):
    Sp = spinehook
    idle = [Sp(bob=[0, 0.3, 0.6, 0.3][i], hook=(8.0, -12.0 + [0, 0.3, 0.6, 0.3][i]), jaw=[0, 0, 1, 0][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (0.5 + 3.8 * math.cos(ph), -max(0.0, 2.0 * math.sin(ph)))
        f2 = (-0.5 - 3.8 * math.cos(ph), -max(0.0, -2.0 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        run.append(Sp(lean=32, bob=b, feet=(f1, f2), hook=(8.0 - 2.0 * math.cos(ph), -11.0 + b), hand=(4.0, -16.0 + b)))
    # Rake (6): hook up (0-1), RAKE down through (2: hook at (14, -8)), through (3), back (4-5)
    rake = [Sp(hook=(6.0, -22.0), crouch=0.5), Sp(lean=10, hook=(2.0, -25.0), crouch=0.8),
            Sp(lean=40, hook=(14.0, -9.0), feet=((5.0, 0.0), (-3.0, 0.0)), smear_pts=[(4, -27), (11, -22), (15, -15), (15, -8)], jaw=1),
            Sp(lean=44, hook=(12.0, -3.0), feet=((5.0, 0.0), (-3.0, 0.0))), Sp(lean=30, hook=(9.0, -8.0)), Sp()]
    # Harpoon (8): heft (0), cock back (1-2), THROW (3: the head leaves the hand at (14, -18)), the line pays out (4),
    # haul (5-7: hand over hand, the rope taut)
    harp = [Sp(hand=(2.0, -20.0), harp=((-6.0, -12.0), (10.0, -26.0))),
            Sp(lean=10, hand=(-3.0, -22.0), harp=((-12.0, -16.0), (6.0, -28.0)), crouch=0.6),
            Sp(lean=4, hand=(-6.0, -21.0), harp=((-16.0, -17.0), (3.0, -26.0)), crouch=1.0),
            Sp(lean=40, hand=(12.0, -17.0), harp=False, feet=((6.0, 0.0), (-3.0, 0.0)),
               rope=[(12, -17), (18, -18), (24, -18)], smear_pts=[(-10, -26), (2, -26), (10, -20), (14, -18)]),
            Sp(lean=36, hand=(11.0, -16.0), harp=False, feet=((6.0, 0.0), (-3.0, 0.0)), rope=[(11, -16), (18, -15), (26, -14)])]
    for i in range(3):
        harp.append(Sp(lean=[10, 4, 10][i], hand=(4.0 - 2 * (i % 2), -15.0 - (i % 2)), hook=(9.0 - (i % 2) * 3, -14.0), harp=False,
                       feet=((4.0, 0.0), (-4.0, 0.0)), crouch=0.8,
                       rope=[(9.0 - (i % 2) * 3, -14.0), (16.0, -12.0), (24.0, -10.0)]))
    d0 = Sp(lean=-6, jaw=2, hook=(6.0, -20.0), hand=(-2.0, -18.0))
    d1 = Sp(lean=-20, bob=5.0, crouch=3.0, jaw=2, hook=(6.0, -4.0), hand=(-6.0, -6.0), feet=((4.0, 0.0), (-5.0, 0.0)),
            harp=((-12.0, -2.0), (6.0, -10.0)))
    d2 = spine_corpse(0); corpse = spine_corpse(1)
    knock = Sp(lean=0, jaw=2, hook=(5.0, -18.0), hand=(-3.0, -17.0), feet=((4.0, 0.0), (-3.0, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.075] * 6),
             ("Rake", rake, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Harpoon", harp, [0.12, 0.12, 0.12, 0.05, 0.1, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssSpinehook", anims, outdir)


def spine_corpse(stage):
    r = Rig()
    heap(r, 0.0, 0, 16.0 if stage else 12.0, 14, seed=71, h=0.6 if stage else 1.4)
    r.poly([(-8, -2), (6, -3), (7, 0), (-9, 0)], "tar", -0.5, curve=0.3)
    skullp(r, -7.0, 0.0 if stage else -1.0, "L", 1.0, jaw=1, eye=False, flip=True)
    r.ell(6.0, -1.5, 3.0, 1.5, "rope", 0.6, flat=2)
    if not stage: dust(r, 0, 0, 1, 1.8)
    return r.resolve()


SYNC["OssSpinehook"] = {"Rake": [("RAKE: hook at (15, -8); hit box 18 x 14 at (11, -10)", 2)],
                        "Harpoon": [("THROW: the harpoon leaves the hand at (14, -18); it flies along the floor at (14, -1)", 3),
                                    ("haul hand over hand while a pile is reeled in", 5)]}


# ================================================================== GHOULS: Tombwright and Coffin Bearer share the head
GHOUL_HEAD = {
    "shut": """
..gGGg..
.gGGGGg.
gGGGGGGg
gkkGGkeg
gGGGGGGd
.gGnGGd.
.gTtTtd.
..dddd..
""",
    "open": """
..gGGg..
.gGGGGg.
gGGGGGGg
gkkGGkeg
gGGGGGGd
.gGnGGd.
.gTtTtd.
..d..d..
..dTtd..
""",
}
GHOUL_HEAD_XL = {
    "shut": """
...gGGGg...
..gGGGGGGg.
.gGGGGGGGGd
gGGGGGGGGGd
gkkkGGGkkkd
gkeeGGGkeed
gGGGGnGGGGd
.gGGGnnGGd.
.gTtTtTtTd.
..gddddddd.
...ddddd...
""",
    "open": """
...gGGGg...
..gGGGGGGg.
.gGGGGGGGGd
gGGGGGGGGGd
gkkkGGGkkkd
gkeeGGGkeed
gGGGGnGGGGd
.gGGGnnGGd.
.gTtTtTtTd.
..d.....d..
..dTtTtTd..
...ddddd...
""",
}
GHOUL_LEG = dict(BONE_LEG, g=("ghoul", 2), G=("ghoul", 3), d=("ghoul", 1), e=("lant", 3), k=("iron", 0))


def ghoul_body(r, hip, lean, hands, feet, z=0.0, coat="umber", coat_len=6.0, broad=1.0, arm=(6.0, 6.0), leg=(6.0, 6.0),
               torso=11.0, face="shut", apron=None, fist=1.3, ribbon=None, big=True):
    """A broad ghoul: legs in dark trousers, a coat or apron over a hunched barrel chest, long arms. Returns neck, shoulder."""
    T = Xf(lean, hip)
    neck = T(hip[0] + 1.0, hip[1] - torso)
    for k, (fx_, fy_) in enumerate(feet):
        near = k == 0
        hx, hy = hip[0] + (1.5 if near else -1.0) * broad, hip[1]
        kx, ky = ik(hx, hy, fx_, fy_ - 1.0, leg[0], leg[1], bend=-1)
        zz = z + (0.6 if near else -1.0)
        r.tube([(hx, hy), (kx, ky), (fx_, fy_ - 1.0)], [2.0 * broad, 1.5, 1.4], "cloth", zz, bias=0.0 if near else -0.4)
        r.poly([(fx_ - 2.0, fy_ - 2.0), (fx_ + 3.0, fy_ - 1.6), (fx_ + 3.0, fy_), (fx_ - 2.0, fy_)], "tar", zz + 0.01, bias=0.2 if near else -0.2)
    # barrel chest + coat
    cx, cy = lerp(hip[0], neck[0], 0.55), lerp(hip[1], neck[1], 0.55)
    r.ell(cx, cy, 5.0 * broad, torso * 0.55, "ghoul", z, ang=lean * 0.5, bias=0.05)
    c0 = (neck[0] - 5.0 * broad, neck[1] + 1.5); c1 = (neck[0] + 4.0 * broad, neck[1] + 1.5)
    c2 = (hip[0] + 5.5 * broad, hip[1] + coat_len); c3 = (hip[0] - 6.0 * broad, hip[1] + coat_len)
    r.poly([c0, c1, c2, (hip[0], hip[1] + coat_len + 1.0), c3], coat, z + 0.1, curve=0.7, normal=(-0.2, -0.3, 1.0))
    if apron:
        r.poly([(cx - 2.5, cy - 1.0), (cx + 3.5, cy - 1.0), (hip[0] + 4.0, hip[1] + coat_len - 1), (hip[0] - 2.0, hip[1] + coat_len - 1)],
               apron, z + 0.2, curve=0.5)
    if ribbon:
        r.poly([(neck[0] - 1, neck[1] + 2), (neck[0] + 2, neck[1] + 2), (neck[0] + 1.5, neck[1] + 6), (neck[0] + 0.5, neck[1] + 4.5),
                (neck[0] - 0.5, neck[1] + 6)], ribbon, z + 0.3, normal=(-0.3, -0.4, 0.8))
    sh = neck
    outs = []
    for k, (hx_, hy_) in enumerate(hands):
        near = k == 0
        s0 = (neck[0] + (2.5 if near else -3.5) * broad, neck[1] + 2.0)
        ex, ey = ik(s0[0], s0[1], hx_, hy_, arm[0], arm[1], bend=-1 if near else 1)
        zz = z + (1.5 if near else -0.8)
        r.tube([s0, (ex, ey)], [2.0 * broad, 1.6], coat, zz, bias=0.0 if near else -0.4)
        r.tube([(ex, ey), (hx_, hy_)], [1.4, 1.2], "ghoul", zz + 0.01, bias=0.0 if near else -0.4)
        r.ell(hx_, hy_, fist, fist, "ghoul", zz + 0.02, bias=0.1 if near else -0.3)
        outs.append((ex, ey))
    if big:
        r.stamp(GHOUL_HEAD_XL[face], neck[0] + 1.5, neck[1] + 1.5, z + 2.5, GHOUL_LEG, pivot=(4, 11))
    else:
        r.stamp(GHOUL_HEAD[face], neck[0] + 1.5, neck[1] + 1.0, z + 2.5, GHOUL_LEG, pivot=(3, 8))
    return neck, outs


# ================================================================== TOMBWRIGHT (T3): a stonemason ghoul, mallet, a blank headstone on its back
def mallet(r, grip, head, z, near=True):
    gx, gy = grip; hx, hy = head
    r.line(gx, gy, hx, hy, "wood", z, tone=3 if near else 2)
    L = math.hypot(hx - gx, hy - gy); ux, uy = (hx - gx) / L, (hy - gy) / L
    nx, ny = -uy, ux
    pts = [(hx + nx * 3.0 - ux * 1.5, hy + ny * 3.0 - uy * 1.5), (hx + nx * 3.0 + ux * 2.0, hy + ny * 3.0 + uy * 2.0),
           (hx - nx * 3.0 + ux * 2.0, hy - ny * 3.0 + uy * 2.0), (hx - nx * 3.0 - ux * 1.5, hy - ny * 3.0 - uy * 1.5)]
    r.poly(pts, "stone", z + 0.02, normal=(-0.5, -0.5, 0.7), bias=0.1)
    r.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], "stone", z + 0.03, tone=4)


def headstone_back(r, x, y, z, tilt=0.0):
    T = Xf(tilt, (x, y))
    pts = [T(x - 4.5, y), T(x + 4.5, y), T(x + 4.5, y - 9.0), T(x + 3.0, y - 11.0), T(x, y - 12.0), T(x - 3.0, y - 11.0), T(x - 4.5, y - 9.0)]
    r.poly(pts, "stone", z, curve=0.3, normal=(-0.3, -0.3, 1.0))
    r.dot(*T(x - 3.0, y - 3.0), "lichen", 3, z + 0.01); r.dot(*T(x - 2.0, y - 2.0), "lichen", 2, z + 0.01)
    r.line(*T(x - 4.5, y - 6.0), *T(x + 4.5, y - 6.0), "rope", z + 0.02, tone=2)


def tombwright(lean=14.0, bob=0.0, feet=((4.0, 0.0), (-4.0, 0.0)), hand=(9.0, -12.0), hand2=(-5.0, -13.0), mal=None, face="shut",
               extra=None, smear_pts=None, crouch=0.0, dust_at=None, chisel=True):
    r = Rig()
    hip = (-1.0, -12.0 + bob + crouch)
    headstone_back(r, -6.0, hip[1] + 1.0, -2.0, tilt=-lean * 0.6)
    neck, elb = ghoul_body(r, hip, lean, (hand, hand2), feet, apron="umber", coat="cloth", coat_len=5.0, broad=1.1, torso=12.0, face=face)
    if mal is None:
        mal = ((hand[0], hand[1] + 1.0), (hand[0] + 2.0, hand[1] - 8.0))
    mallet(r, mal[0], mal[1], 2.0)
    if chisel:
        r.line(hand2[0], hand2[1], hand2[0] + 2.0, hand2[1] - 3.0, "iron", -0.7, tone=3)
    if smear_pts: smear(r, smear_pts, "stone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def tomb_sheet(outdir):
    Tw = tombwright
    idle = [Tw(bob=[0, 0.4, 0.8, 0.4][i], hand=(9.0, -12.0 + [0, 0.4, 0.8, 0.4][i]), face="shut" if i != 2 else "open") for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (1.0 + 4.0 * math.cos(ph), -max(0.0, 2.0 * math.sin(ph)))
        f2 = (-1.0 - 4.0 * math.cos(ph), -max(0.0, -2.0 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        run.append(Tw(lean=20, bob=b, feet=(f1, f2), hand=(9.0 - 2.0 * math.cos(ph), -12.0 + b), hand2=(-5.0 + 2.0 * math.cos(ph), -13.0 + b)))
    # Mallet (7): heave overhead (0-2), SMASH on the floor ahead (3: head at (16, -3)), dust (4), lift (5-6)
    mal = [Tw(hand=(6.0, -22.0), mal=((6.0, -22.0), (0.0, -30.0)), face="open"),
           Tw(lean=0, hand=(2.0, -26.0), mal=((2.0, -26.0), (-6.0, -32.0)), face="open", crouch=-0.5),
           Tw(lean=-4, hand=(0.0, -27.0), mal=((0.0, -27.0), (-9.0, -30.0)), face="open"),
           Tw(lean=30, hand=(11.0, -10.0), mal=((11.0, -10.0), (17.0, -3.0)), feet=((6.0, 0.0), (-4.0, 0.0)),
              smear_pts=[(-10, -32), (4, -34), (14, -22), (18, -6)], dust_at=(17.0, 0.0, 0, 1.6, 4)),
           Tw(lean=32, hand=(11.0, -9.0), mal=((11.0, -9.0), (17.0, -2.5)), feet=((6.0, 0.0), (-4.0, 0.0)), dust_at=(17.0, 0.0, 1, 1.8, 4)),
           Tw(lean=20, hand=(9.0, -12.0)), Tw()]
    # Raise (8): lay the chisel to the floor (0-1), strike it (2-3), the stones answer (4: RAISE), hold (5-6), settle (7)
    rs = [Tw(lean=28, hand=(8.0, -16.0), hand2=(8.0, -4.0), mal=((8.0, -16.0), (6.0, -24.0))),
          Tw(lean=34, hand=(7.0, -20.0), hand2=(9.0, -3.0), mal=((7.0, -20.0), (3.0, -28.0)), crouch=1.0),
          Tw(lean=38, hand=(9.0, -8.0), hand2=(9.0, -3.0), mal=((9.0, -8.0), (9.0, -1.0)), crouch=1.4, dust_at=(10.0, 0.0, 0, 1.2)),
          Tw(lean=36, hand=(8.0, -12.0), hand2=(9.0, -3.0), mal=((8.0, -12.0), (6.0, -20.0)), crouch=1.0,
             extra=lambda r: r.polyline([(11, -1), (16, -2), (20, -1), (26, -2)], "iron", 7.0, tone=0)),
          Tw(lean=6, hand=(7.0, -18.0), hand2=(-4.0, -20.0), mal=((7.0, -18.0), (5.0, -26.0)), face="open",
             extra=lambda r: dust(r, 20.0, 0.0, 0, 2.0, 4)),
          Tw(lean=6, hand=(7.0, -18.0), hand2=(-4.0, -20.0), mal=((7.0, -18.0), (5.0, -26.0)), face="open",
             extra=lambda r: dust(r, 20.0, 0.0, 1, 2.2, 4)),
          Tw(lean=10, hand=(8.0, -14.0)), Tw()]
    d0 = Tw(lean=-8, face="open", hand=(5.0, -20.0), hand2=(-6.0, -18.0), mal=((5.0, -20.0), (0.0, -27.0)))
    d1 = Tw(lean=-24, bob=4.0, crouch=3.0, face="open", hand=(6.0, -6.0), hand2=(-8.0, -7.0), feet=((5.0, 0.0), (-5.0, 0.0)),
            mal=((6.0, -6.0), (13.0, -2.0)))
    d2 = tomb_corpse(0); corpse = tomb_corpse(1)
    knock = Tw(lean=-10, face="open", hand=(6.0, -18.0), hand2=(-6.0, -16.0), feet=((5.0, 0.0), (-4.0, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Mallet", mal, [0.12, 0.1, 0.12, 0.05, 0.1, 0.12, 0.12]),
             ("Raise", rs, [0.12, 0.1, 0.06, 0.1, 0.1, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssTombwright", anims, outdir)


def tomb_corpse(stage):
    r = Rig()
    headstone_back(r, -9.0, 0.0, -0.5, tilt=-80 if stage else -60)
    r.ell(1.0, -2.6, 8.0, 2.6, "cloth", 0.0)
    r.ell(-1.0, -3.6, 5.0, 2.0, "umber", 0.1)
    r.stamp(GHOUL_HEAD["open"], 10.0, 0.0 if stage else -1.0, 0.5, GHOUL_LEG, pivot=(3, 8))
    mallet(r, (2.0, -1.0), (8.0, 1.0) if stage else (8.0, -1.0), 0.6)
    if not stage: dust(r, 0, 0, 1, 2.0)
    return r.resolve()


SYNC["OssTombwright"] = {"Mallet": [("SMASH: the mallet head hits the floor at (17, -3); hit box 18 x 12 at (14, -4); topples a stone", 3)],
                         "Raise": [("RAISE: three headstones rise toward the hero, 14 px apart", 4)]}


# ================================================================== COFFIN BEARER (T3): a huge pallbearer ghoul with a chained coffin
def coffin(r, cx, cy, ang, z, w=8.5, h=19.0, lid=0.0):
    """A black coffin centred (cx, cy), its long axis along ang (deg, 90 = upright). A violet ribbon, iron fittings."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    P = lambda s, t: (cx + ux * s * h / 2 + nx * t * w / 2, cy + uy * s * h / 2 + ny * t * w / 2)
    pts = [P(-1.0, -0.6), P(-0.45, -1.0), P(1.0, -0.75), P(1.0, 0.75), P(-0.45, 1.0), P(-1.0, 0.6)]
    r.poly(pts, "coffin", z, normal=(-0.4, -0.5, 0.8), bias=0.1)
    r.polyline([P(-1.0, -0.6), P(-0.45, -1.0), P(1.0, -0.75)], "coffin", z + 0.01, tone=4)
    r.line(*P(-0.2, -0.9), *P(-0.2, 0.9), "fviol", z + 0.02, tone=3)
    r.line(*P(-0.4, 0.0), *P(0.3, 0.0), "fviol", z + 0.02, tone=2)
    for s in (-0.8, 0.8):
        r.dot(*P(s, -0.5), "iron", 3, z + 0.03); r.dot(*P(s, 0.5), "iron", 2, z + 0.03)
    if lid:
        r.line(*P(-1.0, -0.6 - lid * 0.3), *P(1.0, -0.75 - lid * 0.3), "coffin", z + 0.04, tone=3)
    return P


def chainline(r, a, b, z, slack=0.0, tone=3):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(L / 1.5))
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        pts.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t) + slack * math.sin(t * math.pi)))
    r.polyline(pts, "iron", z, tones=[tone if i % 2 == 0 else max(1, tone - 2) for i in range(n)])


def bearer(lean=6.0, bob=0.0, feet=((4.0, 0.0), (-4.0, 0.0)), hand=(5.0, -24.0), hand2=(-4.0, -24.0), cof=None, face="shut",
           extra=None, smear_pts=None, crouch=0.0, dust_at=None, chains=True, slack=0.0, dizzy=False):
    """cof: (cx, cy, ang, lid) of the coffin; chains run from both fists to its ends."""
    r = Rig()
    hip = (-1.0, -13.0 + bob + crouch)
    cof = cof or (0.5, -33.0 + bob + crouch, 0.0, 0.0)
    P = coffin(r, cof[0], cof[1], cof[2], -2.5 if cof[1] < -28 else 3.0, lid=cof[3] if len(cof) > 3 else 0.0)
    neck, elb = ghoul_body(r, hip, lean, (hand, hand2), feet, coat="cloth", coat_len=7.0, broad=1.45, torso=13.0, face=face,
                           arm=(6.5, 6.5), leg=(6.6, 6.4), fist=1.6, ribbon="fviol")
    if chains:
        chainline(r, hand, P(-0.9, 0.0) if True else None, 3.4, slack=slack)
        chainline(r, hand2, P(0.9, 0.0), -0.5, slack=slack, tone=2)
    if dizzy:
        r.dots(arc_pts(neck[0] + 1.5, neck[1] - 10.0, 4, 1.5, 0, 360, 5), "lant", 3, 8.0)
    if smear_pts: smear(r, smear_pts, "coffin", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


def bearer_sheet(outdir):
    Bb = bearer
    idle = [Bb(bob=[0, 0.4, 0.8, 0.4][i], hand=(5.0, -24.0 + [0, 0.4, 0.8, 0.4][i]), hand2=(-4.0, -24.0 + [0, 0.4, 0.8, 0.4][i]),
               cof=(0.5, -33.0 + [0, 0.4, 0.8, 0.4][i], [0, 2, 0, -2][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (1.0 + 4.0 * math.cos(ph), -max(0.0, 2.0 * math.sin(ph)))
        f2 = (-1.0 - 4.0 * math.cos(ph), -max(0.0, -2.0 * math.sin(ph)))
        b = -0.8 * abs(math.sin(ph))
        run.append(Bb(lean=12, bob=b, feet=(f1, f2), hand=(6.0, -24.0 + b), hand2=(-3.0, -24.0 + b), cof=(1.5, -33.0 + b, 4 * math.sin(ph))))
    # Slam (7): heave the coffin back (0-2), SLAM it down ahead (3: lands across (16..30, -2)), dust (4), haul back (5-6)
    slam = [Bb(lean=0, hand=(2.0, -26.0), hand2=(-5.0, -26.0), cof=(-4.0, -34.0, -20.0)),
            Bb(lean=-8, hand=(0.0, -28.0), hand2=(-6.0, -27.0), cof=(-9.0, -32.0, -40.0), face="open"),
            Bb(lean=-10, hand=(0.0, -28.0), hand2=(-6.0, -27.0), cof=(-12.0, -28.0, -60.0), face="open"),
            Bb(lean=22, hand=(12.0, -12.0), hand2=(8.0, -13.0), cof=(22.0, -4.0, 0.0), feet=((6.0, 0.0), (-4.0, 0.0)),
               smear_pts=[(-12, -36), (6, -38), (22, -24), (26, -8)], dust_at=(22.0, 0.0, 0, 2.2, 4)),
            Bb(lean=24, hand=(12.0, -11.0), hand2=(8.0, -12.0), cof=(22.0, -4.0, 0.0, 0.5), feet=((6.0, 0.0), (-4.0, 0.0)),
               dust_at=(22.0, 0.0, 1, 2.4, 4)),
            Bb(lean=12, hand=(8.0, -20.0), hand2=(3.0, -21.0), cof=(10.0, -20.0, 40.0)), Bb()]
    # Whirl (4, loops for 2 s): the coffin swings round on its chains (out to the right, behind, left, in front)
    wh = []
    for i in range(4):
        a = i / 4 * math.tau
        cx, cy = 18.0 * math.cos(a), -14.0 + 7.0 * math.sin(a)
        wh.append(Bb(lean=0, hand=(4.0 * math.cos(a), -18.0 + 2.0 * math.sin(a)), hand2=(3.0 * math.cos(a) - 1.0, -19.0 + 2.0 * math.sin(a)),
                     cof=(cx, cy, math.degrees(a) + 90, 0.0), face="open",
                     smear_pts=[(18.0 * math.cos(a - 0.9), -14.0 + 7.0 * math.sin(a - 0.9)), (18.0 * math.cos(a - 0.5), -14.0 + 7.0 * math.sin(a - 0.5)),
                                (cx, cy)]))
    # Dizzy (4): staggering, stars over the head
    dz = [Bb(lean=[-10, 6, -6, 10][i], hand=(4.0, -12.0), hand2=(-4.0, -12.0), cof=(-6.0 + 2 * (i % 2), -4.0, 0.0), dizzy=True, face="open",
             feet=((3.0 + (i % 2), 0.0), (-4.0 + (i % 2), 0.0))) for i in range(4)]
    # Fling (8): the coffin lets go of the whirl (0), flies out on full chain (1-3: 60 px, (60, -12) at 3), yanked back (4-6), caught (7)
    import ossivar_v2_rigs as RG
    fl = []
    for i, k in enumerate(x / RG.SX for x in (18.0, 34.0, 50.0, 60.0, 44.0, 28.0, 14.0, 4.0)):   # in game px: the hit is at 60
        fl.append(Bb(lean=14 if i < 4 else -6, hand=(7.0, -16.0), hand2=(4.0, -17.0), cof=(k, -12.0, 0.0), feet=((5.0, 0.0), (-5.0, 0.0)),
                     face="open", slack=-1.0 if i in (0, 5) else 0.0,
                     smear_pts=[(k - 14, -12), (k - 8, -12), (k - 5, -12)] if i in (1, 2, 4, 5) else None))
    d0 = Bb(lean=-12, face="open", hand=(2.0, -26.0), hand2=(-6.0, -24.0), cof=(-14.0, -10.0, 70.0))
    d1 = Bb(lean=-26, bob=5.0, crouch=3.0, face="open", hand=(6.0, -6.0), hand2=(-8.0, -7.0), feet=((5.0, 0.0), (-5.0, 0.0)),
            cof=(-14.0, -4.0, 0.0))
    d2 = bearer_corpse(0); corpse = bearer_corpse(1)
    knock = Bb(lean=-12, face="open", hand=(4.0, -22.0), hand2=(-6.0, -21.0), cof=(-4.0, -31.0, -14.0), feet=((5.0, 0.0), (-4.0, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Slam", slam, [0.12, 0.12, 0.1, 0.05, 0.12, 0.12, 0.12]),
             ("Whirl", wh, [0.1] * 4), ("Dizzy", dz, [0.2] * 4),
             ("Fling", fl, [0.05, 0.05, 0.06, 0.1, 0.06, 0.06, 0.06, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssCoffinBearer", anims, outdir)


def bearer_corpse(stage):
    r = Rig()
    coffin(r, -10.0, -3.5, 0.0, -0.5, lid=1.0 if stage else 0.0)
    r.ell(4.0, -3.0, 9.0, 3.0, "cloth", 0.0)
    r.stamp(GHOUL_HEAD["open"], 14.0, 0.0 if stage else -1.0, 0.5, GHOUL_LEG, pivot=(3, 8))
    chainline(r, (6.0, -2.0), (-4.0, -2.0), 0.6, slack=1.0)
    if not stage: dust(r, 0, 0, 1, 2.2)
    return r.resolve()


SYNC["OssCoffinBearer"] = {"Slam": [("SLAM: the coffin lands across (16..30, -2); hit box 20 x 14 at (22, -5)", 3)],
                           "Whirl": [("loops: the coffin circles on its chains (radius grows in code, 14 -> 34 px)", 0)],
                           "Fling": [("LET GO: the coffin flies out on its chain", 0), ("full stretch: coffin at (60, -12); hit 16 x 14 there", 3),
                                     ("yanked back", 4)]}


# ================================================================== BONE MAMMOTH (T3): a mammoth skeleton in tatters of tar-black hide
MAMMOTH_HEAD = """
...LHHL....
..LHHHHLL..
.LHHLLLLBS.
LLkkeLLLBS.
SLkkLLLBBS.
.SBLLLLBS..
..SBBBBS...
"""


def mammoth(lean=0.0, bob=0.0, legs=None, trunk=None, tusk_a=0.0, head_lift=0.0, extra=None, smear_pts=None, dust_at=None,
            crouch=0.0, rear=0.0):
    r = Rig()
    legs = legs or ((-9.0, 0.0), (6.0, 0.0), (-7.5, 0.0), (7.5, 0.0))
    T = Xf(lean - rear, (-8.0, -14.0))
    hip = T(-8.0, -14.0 + bob + crouch)
    sh = T(5.0, -18.0 + bob + crouch * 0.5)
    if rear:
        legs = [legs[0], (legs[1][0] - rear * 0.05, legs[1][1] - rear * 0.25), legs[2], (legs[3][0] - rear * 0.05, legs[3][1] - rear * 0.25)]
    boar_body(r, hip, sh, legs, chest=8.0, ribs=7, dirt=False, leg_len=(7.5, 7.5), fleg_len=(8.0, 8.2), seed=17, leg_rad=1.7)
    # tar-black hide tatters hanging from the spine
    for i, (t, ln) in enumerate(((0.15, 7.0), (0.4, 9.0), (0.65, 8.0), (0.85, 6.0))):
        x0, y0 = lerp(hip[0], sh[0], t), lerp(hip[1], sh[1], t) - 2.5
        r.poly([(x0 - 3.0, y0), (x0 + 3.5, y0 - 0.5), (x0 + 2.5, y0 + ln), (x0 + 0.5, y0 + ln - 1.5), (x0 - 2.5, y0 + ln + 0.5)],
               "tar", 0.5 + i * 0.01, normal=(-0.3, -0.4, 0.8))
    # head, crossing tusks, a trunk of vertebrae
    hx, hy = sh[0] + 4.0, sh[1] + 1.0 - head_lift
    r.tube([(sh[0] - 1.0, sh[1] - 1.0), (hx - 1.0, hy - 3.0)], [2.6, 2.2], "bone", 1.0, bias=0.05)
    vertebrae(r, [(sh[0] - 1.0, sh[1] - 3.0), (hx - 1.0, hy - 5.5)], 1.1, "bone", tone_a=4, tone_b=2)
    r.stamp(MAMMOTH_HEAD, hx, hy, 2.0, BONE_LEG, pivot=(3, 6))
    trunk = trunk or [(2.5, 80), (2.5, 95), (2.5, 105), (2.0, 80)]
    tp = chain(hx + 5.0, hy - 1.0, trunk)
    vertebrae(r, tp, 2.2, "bone", tone_a=3, tone_b=1)
    for k, (dz, m) in enumerate(((2.4, "obone"), (-1.0, "obone"))):
        s0 = (hx + 4.0 - k, hy - 1.0)
        pts = chain(s0[0], s0[1], [(4.0, 50 + tusk_a - k * 6), (4.0, 10 + tusk_a - k * 6), (3.0, -40 + tusk_a - k * 6), (2.0, -110 + tusk_a)])
        r.tube(pts, [1.2, 1.0, 0.8, 0.6, 0.4], m, dz, bias=0.0 if k == 0 else -0.4)
    if smear_pts: smear(r, smear_pts, "obone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


ML = ((-9.0, 0.0), (6.0, 0.0), (-7.5, 0.0), (7.5, 0.0))


def mammoth_sheet(outdir):
    M = mammoth
    idle = [M(bob=[0, 0.3, 0.6, 0.3][i], trunk=[(2.5, 80 + 6 * s), (2.5, 95 + 8 * s), (2.5, 105 + 6 * s), (2.0, 80)] if True else None)
            for i, s in enumerate((0, 1, 2, 1))]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        lg = gait(i, 6, 3.4, 2.0, base=ML)
        run.append(M(lean=-2 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)), legs=lg,
                     trunk=[(2.5, 80 + 10 * math.sin(ph)), (2.5, 95 + 12 * math.sin(ph)), (2.5, 105), (2.0, 70)],
                     dust_at=(lg[1][0], 0.0, 0, 0.8, 2) if i in (0, 3) else None))
    # Tusk (6): head low (0-1), SWEEP up (2: tusks at (24, -14)), through (3), settle (4-5)
    tk = [M(head_lift=-3.0, tusk_a=20, crouch=1.0), M(head_lift=-4.0, tusk_a=30, crouch=1.6),
          M(head_lift=5.0, tusk_a=-30, lean=-4, smear_pts=[(18, -4), (24, -10), (26, -18), (22, -24)]),
          M(head_lift=6.0, tusk_a=-40, lean=-6), M(head_lift=2.0, tusk_a=-10), M()]
    # Quake (8): rear up (0-3, 0.8 s, the tell), STAMP (4: both fores down, the cracks start), shudder (5-7)
    qk = [M(rear=6, head_lift=2.0), M(rear=12, head_lift=4.0, tusk_a=-10), M(rear=16, head_lift=5.0, tusk_a=-16),
          M(rear=18, head_lift=6.0, tusk_a=-20, trunk=[(2.5, -60), (2.5, -90), (2.5, -110), (2.0, -130)]),
          M(crouch=2.0, head_lift=-2.0, tusk_a=10, dust_at=(4.0, 0.0, 0, 2.6, 4)),
          M(crouch=1.6, head_lift=-1.0, dust_at=(4.0, 0.0, 1, 3.0, 4)), M(crouch=0.8, dust_at=(4.0, 0.0, 2, 3.2, 4)), M()]
    d0 = M(rear=10, head_lift=6.0, tusk_a=-20)
    d1 = M(crouch=6.0, lean=10, head_lift=-6.0, legs=((-11.0, 0.0), (8.0, 0.0), (-9.5, 0.0), (9.5, 0.0)))
    d2 = mammoth_corpse(0); corpse = mammoth_corpse(1)
    knock = M(rear=6, head_lift=3.0, legs=((-10.0, 0.0), (5.0, 0.0), (-8.5, 0.0), (6.5, 0.0)))
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.1] * 6),
             ("Tusk", tk, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Quake", qk, [0.2, 0.2, 0.2, 0.2, 0.06, 0.1, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("OssBoneMammoth", anims, outdir)


def mammoth_corpse(stage):
    r = Rig()
    heap(r, -2.0, 0, 30.0 if stage else 24.0, 26, seed=81, h=1.0 if stage else 2.0)
    r.poly([(-14, -3), (8, -4), (10, 0), (-15, 0)], "tar", 0.4, curve=0.3)
    r.stamp(MAMMOTH_HEAD, 12.0, 0.0 if stage else -2.0, 1.0, BONE_LEG, pivot=(3, 6))
    r.tube(chain(16.0, -3.0, [(4.0, 10), (4.0, -30), (3.0, -80)]), [1.2, 1.0, 0.7, 0.4], "obone", 1.2)
    if not stage: dust(r, 0, 0, 1, 3.0, 4)
    return r.resolve()


SYNC["OssBoneMammoth"] = {"Run": [("footfall: fore foot down (jolt + dust ring)", 0), ("footfall", 3)],
                          "Tusk": [("SWEEP: tusks at (24, -14); hit box 20 x 18 at (18, -10), knockback", 2)],
                          "Quake": [("rearing (0.8 s tell)", 0), ("STAMP: the cross of cracks starts at the feet", 4)]}


# ================================================================== RAZORBACK (T3): a skeletal boar with a crest of bone quills
def razorback(quills=0, lean=0.0, bob=0.0, legs=None, head_at=None, face="shut", extra=None, smear_pts=None, dust_at=None,
              crouch=0.0, stretch=0.0, flat=False):
    r = Rig()
    legs = legs or ((-7.0, 0.0), (6.0, 0.0), (-6.0, 0.0), (7.0, 0.0))
    T = Xf(lean, (0.0, -10.0))
    hip = T(-7.0 - stretch * 0.5, -10.0 + bob + crouch)
    sh = T(5.0 + stretch * 0.5, -11.5 + bob + crouch * 0.6)
    boar_body(r, hip, sh, legs, chest=7.5, ribs=6, dirt=True, leg_len=(5.0, 5.0), fleg_len=(5.4, 5.6), seed=23, leg_rad=1.5)
    # the quill crest: five sockets along the spine; raised quills stand tall (marrow-red tips), lowered ones lie flat
    for i in range(5):
        t = 0.1 + 0.2 * i
        x0, y0 = lerp(hip[0], sh[0], t), lerp(hip[1], sh[1], t) - 2.6 - math.sin(t * math.pi) * 1.2
        up = i < quills
        if up and not flat:
            L = 7.0 + (1.5 if i in (2, 3) else 0)
            a = math.radians(-100 + i * 6)
            tip = (x0 + L * math.cos(a), y0 + L * math.sin(a))
            r.tube([(x0, y0), tip], [0.9, 0.5], "bone", 1.2 + i * 0.01)
            r.dot(tip[0], tip[1], "marrow", 3, 1.3); r.dot(lerp(x0, tip[0], 0.85), lerp(y0, tip[1], 0.85), "marrow", 2, 1.3)
        else:
            r.tube([(x0, y0), (x0 - 4.5, y0 + 1.0)], [0.9, 0.5], "dbone", 1.1)
            r.dot(x0 - 4.0, y0 + 1.0, "marrow", 1, 1.11)
    hx, hy = head_at or (sh[0] + 3.0, sh[1] + 1.0)
    vertebrae(r, [(sh[0] + 0.4, sh[1] - 1.6), (hx - 0.4, hy - 2.4)], 0.6, "bone", tone_a=3, tone_b=2)
    r.stamp(BOAR_HEAD[face], hx, hy, 2.0, BONE_LEG, pivot=(1, 5))
    r.stamp("""
.O
OO
""", hx + 7, hy - 3, 2.1, BONE_LEG, pivot=(0, 1))
    if smear_pts: smear(r, smear_pts, "bone", 4)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r)
    return r.resolve()


RL = ((-7.0, 0.0), (6.0, 0.0), (-6.0, 0.0), (7.0, 0.0))


def razor_sheet(outdir):
    Rz = razorback
    anims = []

    def idle_set(q):
        return [Rz(q, bob=[0, 0.3, 0.6, 0.3][i], face="shut" if i != 2 else "open") for i in range(4)]

    def run_set(q):
        out = []
        for i in range(6):
            ph = i / 6 * math.tau
            out.append(Rz(q, lean=-4 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)), legs=gait(i, 6, 3.2, 1.8, base=RL), stretch=0.8 * math.cos(ph)))
        return out
    idle = idle_set(0)
    anims += [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run_set(0), [0.07] * 6)]
    for q in range(1, 6):
        anims += [("Idle%d" % q, idle_set(q), [0.16, 0.12, 0.16, 0.12]), ("Run%d" % q, run_set(q), [0.07] * 6)]
    # Slash (6): head low (0-1), RIP up (2: tusk at (16, -12)), through (3), settle (4-5)
    sl = [Rz(2, crouch=1.0, lean=8, head_at=(8.0, -7.0)), Rz(2, crouch=1.6, lean=12, head_at=(9.0, -5.5)),
          Rz(2, lean=-14, head_at=(10.0, -13.0), face="open", smear_pts=[(12, -3), (15, -7), (17, -13), (16, -17)]),
          Rz(2, lean=-18, head_at=(9.0, -14.5), face="open"), Rz(2, lean=-6, head_at=(8.0, -11.0)), Rz(2)]
    # Skid (7): burst (0-2), SKID (3: dust), the quills flatten and FLY (4: fan from (6, -24)), slide to rest (5-6)
    sk = [Rz(5, lean=8, crouch=0.8, legs=gait(0, 6, 3.6, 2.0, gallop=True, base=RL), stretch=1.4, dust_at=(-8.0, 0.0, 0, 1.0)),
          Rz(5, lean=10, legs=gait(2, 6, 3.6, 2.0, gallop=True, base=RL), stretch=1.6, dust_at=(-8.0, 0.0, 1, 1.0)),
          Rz(5, lean=10, legs=gait(4, 6, 3.6, 2.0, gallop=True, base=RL), stretch=1.6),
          Rz(5, lean=-10, legs=((-4.0, 0.0), (9.0, 0.0), (-3.0, 0.0), (10.0, 0.0)), dust_at=(9.0, 0.0, 0, 2.0, 4)),
          Rz(0, lean=-14, flat=True, legs=((-4.0, 0.0), (9.0, 0.0), (-3.0, 0.0), (10.0, 0.0)), dust_at=(9.0, 0.0, 1, 2.2, 4),
             extra=lambda r: [r.line(-2 + 3 * i, -26 + i, 4 + 3 * i, -28 + 2 * i, "bone", 7.0, tone=4) for i in range(4)]),
          Rz(0, lean=-6, dust_at=(9.0, 0.0, 2, 2.4, 4)), Rz(0)]
    d0 = Rz(3, lean=-16, face="open", head_at=(8.0, -15.0))
    d1 = Rz(1, lean=-24, bob=2.0, face="open", head_at=(7.0, -7.0), legs=((-8.0, 0.0), (4.0, 0.0), (-7.0, 0.0), (6.0, -1.0)))
    d2 = razor_corpse(0); corpse = razor_corpse(1)
    knock = Rz(2, lean=-14, face="open", head_at=(7.0, -14.0), legs=((-8.0, 0.0), (4.0, 0.0), (-7.0, 0.0), (5.0, 0.0)))
    anims += [("Slash", sl, [0.1, 0.1, 0.05, 0.08, 0.1, 0.12]), ("Skid", sk, [0.07, 0.07, 0.07, 0.08, 0.06, 0.12, 0.12])]
    anims += tail_anims(Rz(2), [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("OssRazorback", anims, outdir)


def razor_corpse(stage):
    r = Rig()
    heap(r, -2.0, 0, 18.0 if stage else 14.0, 16, seed=91, h=0.8 if stage else 1.6)
    for i in range(4):
        r.line(-8 + 4 * i, -1, -5 + 4 * i, -4 - (i % 2), "bone", 0.8, tone=3)
        r.dot(-5 + 4 * i, -4 - (i % 2), "marrow", 2, 0.81)
    r.stamp(BOAR_HEAD["open"], 7.0, 0.0 if stage else -1.0, 1.0, BONE_LEG, pivot=(1, 5))
    if not stage: dust(r, 0, 0, 1, 2.0)
    return r.resolve()


SYNC["OssRazorback"] = {"Slash": [("RIP: tusk at (16, -12); hit box 16 x 14 at (12, -9)", 2)],
                        "Skid": [("burst forward (move from 0)", 0), ("SKID: stop", 3), ("FIRE: every raised quill flies from (6, -24)", 4)]}
NOTES["OssRazorback"] = "IdleN/RunN show N raised quills (1..5); Idle/Run show none."

JOBS = [("OssCharnelRider", rider_sheet), ("OssSpinehook", spine_sheet), ("OssTombwright", tomb_sheet),
        ("OssCoffinBearer", bearer_sheet), ("OssBoneMammoth", mammoth_sheet), ("OssRazorback", razor_sheet)]
