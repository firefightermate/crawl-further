"""Ysveld tier 3, part two: Winter Bride, Snow Wraith, Rime Colossus, Rime Warden, The Geode (and its half), Prism
Oracle. Built through ysveld_v2_rigs.py. T3 idle limit 42 x 40; none is smaller than the sprite it replaces."""
import math, random
from ysveld_v2_rigs import (Rig, Xf, chain, ik, lerp, lerp_pt, moth, wing, antenna, robe, crystal, sparkle, arc_smear,
                            snow_puff, flakes, rime_fringe, shadow, sheet, tail_anims)
from ysveld_v2_t2 import arm, legs2, walk, KNIGHT_LEG


# ================================================================== WINTER BRIDE: a bride in a frost veil and a train of snow
BRIDE_LEG = {"v": ("veil", 3), "V": ("veil", 4), "u": ("veil", 2), "w": ("veil", 1), "s": ("skin", 3), "S": ("skin", 4),
             "k": ("skin", 2), "K": ("skin", 1), "x": ("black", 0), "e": ("eye", 4), "m": ("red", 2), "M": ("red", 3),
             "c": ("ice", 4), "C": ("ice", 3), "i": ("ice", 2), "h": ("frost", 3), "H": ("frost", 2), "r": ("rglow", 4)}
# pivot (5, 11): the base of the neck. An ice crown, silver hair, a pale face with dark eyes and lips under a lace veil
# that hangs to her shoulders (the face shows through it); widowed, the lace is black and her eyes burn red
BRIDE_FACE = """
...c.c.c...
..cCcCcCc..
..CiCcCiC..
.uvhhhhhvu.
uvhsSSSShvu
vhsSSSSSShv
vhsxeSexshv
vhssSSSSkhv
vvhsSmMSkhw
uvvhsssskvw
uvv.kSSk.vw
uv..kSSk..w
"""
BRIDE_HEAD = {
    "calm": BRIDE_FACE,
    "breath": BRIDE_FACE.replace("vvhsSmMSkhw", "vvhsSxxSkhw"),
    "hurt": BRIDE_FACE.replace("vhsxeSexshv", "vhsxxSxxshv"),
    "widow": BRIDE_FACE.replace("vhsxeSexshv", "vhsxrSrxshv"),
    "widowbreath": BRIDE_FACE.replace("vhsxeSexshv", "vhsxrSrxshv").replace("vvhsSmMSkhw", "vvhsSxxSkhw"),
}
WIDOW_LEG = dict(BRIDE_LEG, v=("black", 3), V=("black", 4), u=("black", 2), w=("black", 1))


def bouquet(r, x, y, z):
    """A frozen bouquet: four ice-blue roses on white stems."""
    for k, (dx, dy) in enumerate(((0.0, 0.0), (-1.8, -0.8), (1.6, -1.0), (0.0, -2.0))):
        r.ell(x + dx, y + dy - 1.2, 1.4, 1.2, "ice", z + k * 0.01, bias=0.2)
        r.dot(x + dx, y + dy - 1.4, "white", 4, z + k * 0.01 + 0.005)
    r.line(x, y, x - 0.5, y + 2.5, "frost", z - 0.01, tone=3)


def bride(bob=0.0, lean=0.0, sway=0.0, train=0.0, face="calm", hand=(4.0, -15.0), hand2=(-3.0, -15.0), widow=False,
          extra=None, turn=0.0, hem=0.0):
    """turn: 0..1 sweeps the train from behind her round in front (the Train Sweep)."""
    r = Rig(1.22)
    T = Xf(lean, (0.0, -1.0))
    veil_mat = "black" if widow else "veil"
    sh = T(0.0, -23.0 + bob)
    # the train of snow-white silk: a long fan on the floor behind her (it swings round with `turn`), folds running along it
    ta = math.radians(180 - turn * 180)
    tl = 19.0 + train
    tip = (math.cos(ta) * tl, -0.5 + math.sin(ta) * -2.0)
    side = 1.0 if math.cos(ta) >= 0 else -1.0
    tz = -3.0 if turn < 0.5 else 3.5
    r.poly([(-3.0, -11.0), (tip[0] * 0.55, -5.0 - math.sin(ta) * 3.0), (tip[0], tip[1] - 3.5), (tip[0] - side * 2.0, tip[1]),
            (3.0, -0.4), (-3.5, -0.4)], "veil", tz, bias=0.0, normal=(-0.2, -0.9, 0.5))
    for k in range(3):
        f = (k + 1) / 4.0
        r.line(-2.0, -3.0 - k * 2.5, tip[0] * (0.6 + 0.12 * k), tip[1] - 0.5 - k * 0.8, "veil", tz + 0.01, tone=1 if k % 2 else 4)
    # the gown: a full bell skirt with deep folds, a silver bodice, bare shoulders
    robe(r, (sh[0], sh[1] + 5.0), -0.4, 22.0 + hem, sway=sway, mat="veil", z=0.0, top_w=3.0, flare=0.8, hem_teeth=11, teeth_mat="frost")
    for k in range(-3, 4):
        x0 = sh[0] + k * 0.6
        x1 = sh[0] + k * 3.1 + sway * 0.8
        r.line(x0, sh[1] + 8.0, x1, -1.0, "veil", 0.05, tone=1 if k % 2 else 4)
    r.line(sh[0] - 3.0, sh[1] + 7.0, sh[0] + 3.0, sh[1] + 6.5, "ice", 0.06, tone=3)            # a pale blue sash
    r.poly([(sh[0] - 3.0, sh[1] + 1.0), (sh[0] + 3.0, sh[1] + 1.0), (sh[0] + 2.4, sh[1] + 7.0), (sh[0] - 2.4, sh[1] + 7.0)],
           "silver", 0.3, curve=0.8, bias=0.05)
    for dy in (2.5, 4.5): r.line(sh[0] - 1.5, sh[1] + dy, sh[0] + 1.5, sh[1] + dy, "silver", 0.31, tone=4)
    for sx in (-3.2, 3.2):
        r.ell(sh[0] + sx, sh[1] + 0.8, 1.8, 1.4, "skin", 0.35 if sx > 0 else 0.25, bias=0.1)
    # the veil's long fall down her back to the floor: lace, so the gown shows through it
    pts = [(sh[0] - 2.0, sh[1] - 6.0), (sh[0] + 1.0, sh[1] - 6.0), (sh[0] - 8.0 + sway, -2.0), (sh[0] - 13.0 + sway, -0.6),
           (sh[0] - 5.0, sh[1] + 2.0)]
    from ysveld_v2_rigs import poly_px
    pz = r.part(False, -1.5)
    for (x, y) in poly_px([(px * r.k, py * r.k) for (px, py) in pts]):
        if widow or (x + y) % 2 == 0 or (x * 3 + y) % 7 == 0:
            r.put(x, y, -1.5, veil_mat, 0.5, pz, (2 if (x + y) % 3 else 3) if widow else (3 if (x % 4) else 4))
    if widow:
        # widowed: the black veil also falls over her shoulders and down her front
        for sx in (-1, 1):
            r.poly([(sh[0] + sx * 2.5, sh[1] - 3.0), (sh[0] + sx * 5.0, sh[1] + 1.0), (sh[0] + sx * 6.0, sh[1] + 9.0),
                    (sh[0] + sx * 3.5, sh[1] + 8.0)], "black", 0.5, bias=0.1)
    # arms, bare from the shoulder, with lace cuffs; the frozen bouquet held before her
    arm(r, (sh[0] - 3.0, sh[1] + 1.2), hand2, "skin", -0.5, 4.4, 4.2, rad=(1.0, 0.9, 0.8), bias=-0.25)
    arm(r, (sh[0] + 3.0, sh[1] + 1.2), hand, "skin", 1.5, 4.4, 4.2, rad=(1.0, 0.9, 0.8))
    for hx, hy in (hand, hand2): r.dot(hx - 1, hy, veil_mat, 4, 1.6)
    bouquet(r, (hand[0] + hand2[0]) / 2 + 0.5, (hand[1] + hand2[1]) / 2 - 0.5, 2.0)
    r.stamp(BRIDE_HEAD[face], sh[0] + 0.5, sh[1] + 0.5, 2.5, WIDOW_LEG if widow else BRIDE_LEG, pivot=(5, 11))
    if extra: extra(r)
    return r.resolve()


def bride_corpse(stage, widow=False):
    r = Rig(1.12)
    r.poly([(-14.0, -0.3), (10.0, -0.3), (8.0, -4.0), (-8.0, -5.0)], "veil", 0.0, normal=(-0.3, -0.8, 0.6))
    r.poly([(-18.0, -0.3), (-8.0, -0.3), (-10.0, -2.5)], "frost", -0.5)
    r.stamp(BRIDE_HEAD["hurt"], 12.0, 2.0, 1.0, BRIDE_LEG, pivot=(5, 11))
    bouquet(r, -4.0 if stage else 2.0, -1.0 if stage else -5.0, 1.5)
    return r.resolve()


def bride_sheet(out):
    def B(**k):
        return bride(**k)
    for_w = [False, True]
    sets = {}
    for w in for_w:
        f = "widow" if w else "calm"
        fb = "widowbreath" if w else "breath"
        idle = [B(bob=[0, 0.3, 0.6, 0.3][i], sway=[0, -0.4, -0.8, -0.4][i], train=[0, 0.5, 1, 0.5][i], face=f, widow=w) for i in range(4)]
        run = [B(bob=-0.4 * abs(math.sin(i / 6 * math.tau)), lean=5, sway=-2.0 - math.sin(i / 6 * math.tau), train=2.0 + math.sin(i / 6 * math.tau),
                 hem=1.0, face=f, widow=w) for i in range(6)]
        # Breath (8): she lifts the veil (0-1), draws breath (2), BREATHES frost forward from (11, -26) (3-5), lowers (6-7)
        pm = "black" if w else "snow"
        breath = [B(hand=(5.0, -20.0), hand2=(0.0, -19.0), face=f, widow=w),
                  B(hand=(6.0, -25.0), hand2=(1.0, -22.0), face=f, widow=w, lean=-4),
                  B(hand=(6.0, -26.0), hand2=(1.0, -22.0), face=fb, widow=w, lean=-8, bob=-0.5),
                  B(hand=(6.0, -26.0), hand2=(1.0, -22.0), face=fb, widow=w, lean=6, extra=lambda r: flakes(r, [(12, -26, 4), (14, -25, 3), (13, -27, 3)])),
                  B(hand=(6.0, -26.0), hand2=(1.0, -22.0), face=fb, widow=w, lean=8, extra=lambda r: flakes(r, [(13, -26, 4), (16, -25, 3), (18, -27, 3), (15, -24, 2)])),
                  B(hand=(6.0, -26.0), hand2=(1.0, -22.0), face=fb, widow=w, lean=8, extra=lambda r: flakes(r, [(17, -25, 3), (20, -27, 2)])),
                  B(hand=(5.0, -20.0), hand2=(0.0, -18.0), face=f, widow=w, lean=3), B(face=f, widow=w)]
        # Sweep (8): she turns (0-1), the train swings up behind (2), SWEEPS round in front (3-5: the sweep runs 3-5), settles
        sweep = [B(face=f, widow=w, lean=-4, turn=0.0, train=1.0), B(face=f, widow=w, lean=-8, turn=0.15, train=2.0),
                 B(face=f, widow=w, lean=-6, turn=0.35, train=3.0, extra=lambda r: arc_smear(r, 0, -6, 15, 200, 250, "snow", 2)),
                 B(face=f, widow=w, lean=4, turn=0.6, train=4.0, extra=lambda r: arc_smear(r, 0, -6, 16, 240, 300, "snow", 2)),
                 B(face=f, widow=w, lean=8, turn=0.85, train=4.0, extra=lambda r: [arc_smear(r, 0, -6, 16, 280, 340, "snow", 2), snow_puff(r, 14, 0, 0, 1.4)]),
                 B(face=f, widow=w, lean=6, turn=1.0, train=3.0, extra=lambda r: snow_puff(r, 14, 0, 1, 1.4)),
                 B(face=f, widow=w, lean=2, turn=0.6, train=1.0), B(face=f, widow=w)]
        sets[w] = (idle, run, breath, sweep)
    idle, run, breath, sweep = sets[False]
    widx = sets[True]
    d0 = B(lean=-12, face="hurt", hand=(3.0, -22.0), hand2=(-5.0, -21.0))
    d1 = B(lean=-28, face="hurt", bob=3.0, hand=(1.0, -18.0), hand2=(-7.0, -16.0))
    knock = B(lean=-12, face="hurt", hand=(3.0, -20.0), hand2=(-5.0, -19.0))
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.09] * 6),
             ("Breath", breath, [0.1, 0.1, 0.12, 0.08, 0.1, 0.1, 0.1, 0.1]),
             ("Sweep", sweep, [0.1, 0.12, 0.06, 0.06, 0.06, 0.1, 0.1, 0.1]),
             ("IdleWidow", widx[0], [0.18, 0.16, 0.18, 0.16]), ("RunWidow", widx[1], [0.09] * 6),
             ("BreathWidow", widx[2], [0.1, 0.1, 0.12, 0.08, 0.1, 0.1, 0.1, 0.1]),
             ("SweepWidow", widx[3], [0.1, 0.12, 0.06, 0.06, 0.06, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, bride_corpse(0), bride_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvBride", anims, out, scale=4)


# ================================================================== SNOW WRAITH: a shroud of snow and moth wings round a glowing heart
def wraith(alt=4.0, flap=0.0, lean=0.0, bob=0.0, heart=1, claw=(9.0, -16.0), claw2=(-7.0, -15.0), spin=0.0, extra=None,
           eye="eye", flare=False):
    r = Rig(1.12)
    T = Xf(lean, (0.0, -alt))
    cy = -alt - 13.0 + bob
    shadow(r, 0.0, -1.0, 7.0)
    # moth wings behind the shroud
    wing(r, T(-1.0, cy + 1.0), -168 + flap, 15.0, 10.0, "silk", -3.0, bias=-0.3, rim="ice", scallop=0.8, spots=[(0.6, 0.0, "eye", 2)])
    wing(r, T(1.0, cy + 1.0), -12 - flap, 15.0, 10.0, "silk", -2.9, bias=-0.15, rim="ice", scallop=0.8, spots=[(0.6, 0.0, "eye", 3)])
    wing(r, T(-1.0, cy + 2.0), 160 - flap * 0.5, 9.0, 6.0, "silk", -3.1, bias=-0.35, rim="ice")
    wing(r, T(1.0, cy + 2.0), 20 + flap * 0.5, 9.0, 6.0, "silk", -3.05, bias=-0.2, rim="ice")
    # the shroud: a tall flapping shape of snow, torn into tatters at the hem
    rnd = random.Random(int(spin * 10) + 3)
    pts = [T(-2.5, cy - 7.0), T(2.5, cy - 7.0), T(6.0 + math.sin(spin) * 1.0, cy + 2.0), T(5.5, -alt + 1.0)]
    for i in range(6):
        x = 5.0 - i * 2.0
        pts.append(T(x + math.sin(spin + i) * 0.6, -alt + (2.5 if i % 2 else -0.5) + rnd.uniform(-0.5, 0.5)))
    pts += [T(-7.0, -alt + 0.5), T(-6.0 - math.sin(spin) * 1.0, cy + 2.0)]
    r.poly(pts, "frost", 0.0, curve=0.9, bias=0.0)
    # snow drifting off the shroud, blue shadow folds
    for k in range(3):
        x = -3.0 + k * 3.0
        r.line(*T(x, cy - 2.0), *T(x - 0.5, -alt - 1.0), "ice", 0.05, tone=2)
    # the hood: a dark opening with two eyes; the heart glowing through the chest
    hx, hy = T(0.5, cy - 6.0)
    r.ell(hx, hy, 3.4, 3.2, "frost", 0.3, bias=0.15)
    r.ell(hx + 0.8, hy + 0.6, 2.0, 2.0, "black", 0.31, flat=0)
    r.dot(hx + 0.2, hy + 0.4, eye, 4, 0.32); r.dot(hx + 1.8, hy + 0.4, eye, 4, 0.32)
    gx, gy = T(0.5, cy + 1.0)
    r.ell(gx, gy, 2.0 + heart * 0.4, 2.0 + heart * 0.4, "eye", 0.4, flat=2)
    r.ell(gx, gy, 1.0 + heart * 0.3, 1.0 + heart * 0.3, "white", 0.41, flat=4)
    # claws of ice from the shroud's sleeves
    for k, (h, zz, b) in enumerate(((claw2, -0.5, -0.3), (claw, 1.0, 0.0))):
        sh = T(-3.0 if k == 0 else 3.5, cy - 3.0)
        el = ik(sh[0], sh[1], h[0], h[1], 5.0, 5.0, bend=1)
        r.tube([sh, el, h], [1.4, 1.2, 1.0], "frost", zz, bias=b)
        for f in (-1, 0, 1):
            r.line(h[0], h[1], h[0] + 2.2, h[1] + f * 1.2 + 1.0, "ice", zz + 0.01, tone=4 if k else 3)
    if flare:
        for (x, y) in ((gx - 5, gy - 3), (gx + 5, gy - 2), (gx, gy + 5)): sparkle(r, x, y, 2, "eye")
    if extra: extra(r)
    return r.resolve()


def wraith_corpse(stage):
    r = Rig(1.15)
    r.poly([(-12.0, -0.3), (12.0, -0.3), (9.0, -3.0), (-9.0, -3.5)], "frost", 0.0, normal=(-0.3, -0.8, 0.6))
    wing(r, (-3.0, -2.0), -170, 10.0, 6.0, "silk", -1.0, bias=-0.3)
    wing(r, (3.0, -2.0), -10, 10.0, 6.0, "silk", -0.9)
    if stage == 0: r.ell(0.0, -2.0, 1.4, 1.2, "eye", 0.5, flat=2)
    else: r.dot(0, -1, "eye", 1, 0.5)
    return r.resolve()


def wraith_sheet(out):
    Wr = wraith
    idle = [Wr(bob=[0, -0.4, -0.8, -0.4][i], flap=[-10, 4, 14, 4][i], spin=i * 1.5, heart=[1, 2, 1, 0][i]) for i in range(4)]
    run = [Wr(bob=[0, -0.5, -1, -0.5, 0, 0.3][i], flap=[-15, 0, 15, 20, 5, -10][i], lean=8, spin=i, heart=1) for i in range(6)]
    # Claw (7): rise (0-1), lunge (2), RAKE (3: claws at (14, -10)), follow, settle
    claw = [Wr(claw=(5.0, -22.0), lean=-4, flap=-20), Wr(claw=(3.0, -25.0), lean=-8, flap=-30, bob=-1.0),
            Wr(claw=(12.0, -20.0), lean=6, flap=10, extra=lambda r: r.line(-6, -18, 0, -18, "snow", 5, tone=2)),
            Wr(claw=(14.0, -11.0), lean=12, flap=20, extra=lambda r: [arc_smear(r, 6, -16, 10, -80, 60, "snow", 2), sparkle(r, 17, -10, 1, "white")]),
            Wr(claw=(12.0, -9.0), lean=8), Wr(lean=3), Wr()]
    # Maelstrom (8): it spins up (0-3, the heart flares), flings its arms wide (4: the vortex opens on the hero), winds down
    mael = [Wr(spin=1.0, heart=2, claw=(8.0, -20.0), claw2=(-8.0, -20.0)), Wr(spin=2.5, heart=2, claw=(6.0, -24.0), claw2=(-6.0, -24.0), bob=-1.0),
            Wr(spin=4.0, heart=3, claw=(4.0, -26.0), claw2=(-4.0, -26.0), bob=-1.5, flare=True),
            Wr(spin=5.5, heart=3, claw=(4.0, -27.0), claw2=(-4.0, -27.0), bob=-1.8, flare=True),
            Wr(spin=7.0, heart=3, claw=(14.0, -16.0), claw2=(-12.0, -16.0), flap=20, flare=True,
               extra=lambda r: flakes(r, [(16, -20, 4), (-14, -20, 4), (18, -12, 3), (-16, -12, 3)])),
            Wr(spin=8.0, heart=2, claw=(11.0, -15.0), claw2=(-9.0, -15.0)), Wr(heart=1), Wr()]
    d0 = Wr(lean=-12, eye="white", heart=0, flap=-30); d1 = Wr(lean=-30, alt=2.0, eye="white", heart=0, flap=30, bob=4.0)
    knock = Wr(lean=-14, eye="white", heart=1, flap=-20)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Claw", claw, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Maelstrom", mael, [0.08, 0.08, 0.08, 0.1, 0.08, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, wraith_corpse(0), wraith_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvWraith", anims, out, scale=4)


# ================================================================== RIME COLOSSUS: a giant of packed ice and old snow, rocks in its fists
def colossus(bob=0.0, lean=0.0, feet=((-5.0, 0.0), (5.0, 0.0)), fists=((12.0, -12.0), (-9.0, -12.0)), face_dx=0.0,
             streams=False, extra=None, eye="eye", belly=0.0):
    """belly: 0..1 throws it down onto its belly (Glacier Run)."""
    r = Rig(1.06)
    lean = lean + belly * 65.0
    T = Xf(lean, (0.0, -3.0))
    hip = T(0.0, -12.0 + bob)
    if belly < 0.6:
        legs2(r, hip, feet, "ice", 0.0, 6.0, 6.0, rad=(3.0, 2.6, 2.4), boot="frost", back_bias=-0.3)
    # torso: a huge hunched mass of packed snow with an ice core showing through cracks
    ch = T(0.0, -21.0 + bob)
    r.ell(ch[0], ch[1], 11.0, 9.4, "ice", 0.5, bias=0.0)
    r.ell(*T(-2.0, -27.5 + bob), 7.5, 3.2, "frost", 0.55, bias=0.2)        # old snow on its shoulders
    for (x, y) in ((-4, -20), (3, -17), (-1, -24), (5, -23)):
        r.line(*T(x, y + bob), *T(x + 2, y + 2 + bob), "frost", 0.6, tone=4)
        r.dot(*T(x + 1, y + 1 + bob), "ice", 1, 0.61)
    rime_fringe(r, [T(x, -13.0 + bob) for x in range(-8, 9)], 0.62, step=2, seed=9, length=2.0)
    # glacier ice breaking through its shoulders and back
    for k, (x, y, h, a) in enumerate(((-7.0, -27.0, 6.0, -35), (-3.5, -30.0, 7.5, -15), (1.0, -30.5, 5.0, 5), (-9.5, -22.0, 4.5, -60))):
        crystal(r, *T(x, y + bob), h, 3.0, "ice", 0.4 + k * 0.01, ang=a + lean)
    # the small head sunk between the shoulders
    hx, hy = T(4.0 + face_dx, -28.0 + bob)
    r.ell(hx, hy, 3.4, 3.0, "frost", 0.8, bias=0.1)
    r.dot(hx + 1.0, hy, eye, 4, 0.9); r.dot(hx + 2.6, hy - 0.2, eye, 3, 0.9)
    r.line(hx + 0.5, hy + 1.6, hx + 2.6, hy + 1.6, "ice", 0.9, tone=0)
    # huge arms ending in rock-studded fists
    for k, (f, zz, b) in enumerate(((fists[1], -1.0, -0.3), (fists[0], 2.0, 0.0))):
        sh = T(-8.5 if k == 0 else 8.0, -25.0 + bob)
        el = ik(sh[0], sh[1], f[0], f[1], 7.0, 6.5, bend=1 if k else -1)
        r.tube([sh, el, f], [3.4, 3.0, 2.8], "ice", zz, bias=b)
        r.ell(f[0], f[1], 4.6, 4.0, "frost", zz + 0.1, bias=b + 0.1)
        for (dx, dy) in ((-1.5, -1.5), (1.5, 0.5), (0.0, 2.0)):
            r.ell(f[0] + dx, f[1] + dy, 1.4, 1.2, "rock", zz + 0.2, bias=b)
    if streams:
        for k in range(4):
            x = -10.0 - k * 2.5
            r.line(*T(x + 6, -18.0 - k * 3.0 + bob), *T(x, -17.0 - k * 3.0 + bob), "snow", 3.0, tone=3 if k % 2 else 2)
    if extra: extra(r)
    return r.resolve()


def colossus_corpse(stage):
    r = Rig(1.0)
    r.ell(-2.0, -6.0, 13.0, 6.0, "frost", 0.0)
    r.ell(13.0, -4.0, 3.4, 3.0, "ice", 0.3)
    for (x, y) in ((-8, -5), (2, -8), (-2, -3)): r.line(x, y, x + 3, y + 2, "ice", 0.4, tone=2)
    for k, x in enumerate((-17.0, 8.0)):
        r.ell(x, -3.0, 4.0, 3.2, "frost", 0.5 + k)
        r.ell(x + 1, -2.0, 1.4, 1.2, "rock", 0.6 + k)
    if stage:
        for (x, y) in ((-20, -1), (20, -1), (-12, -1)): r.ell(x, y, 1.5, 1.0, "frost", 1.5)
    return r.resolve()


def colossus_sheet(out):
    C = colossus
    idle = [C(bob=[0, 0.4, 0.8, 0.4][i], fists=((12.0, -12.0 + [0, 0.4, 0.8, 0.4][i]), (-9.0, -12.0 + [0, 0.4, 0.8, 0.4][i]))) for i in range(4)]
    ice_idle = [C(bob=[0, 0.4, 0.8, 0.4][i], lean=8, streams=True, fists=((14.0, -10.0), (-7.0, -11.0))) for i in range(4)]
    def runf(i, lean, streams):
        (fa, la), (fb, lb) = walk(i, stride=4.0)
        return C(bob=-0.8 * abs(math.sin(i / 6 * math.tau)), lean=lean, feet=((-3.0 + fa, la), (3.0 + fb, lb)), streams=streams,
                 fists=((12.0 + 2 * math.sin(i / 6 * math.tau), -12.0), (-9.0 - 2 * math.sin(i / 6 * math.tau), -12.0)))
    run = [runf(i, 5, False) for i in range(6)]
    ice_run = [runf(i, 12, True) for i in range(6)]
    # Slam (8): both fists rise high (0-2), SLAM (3: hit, fists at (17, -4), the quake runs ahead), hold (4-5), rise (6-7)
    slam = [C(fists=((8.0, -26.0), (-4.0, -27.0)), lean=-4), C(fists=((6.0, -32.0), (-2.0, -33.0)), lean=-8, bob=-1.0),
            C(fists=((5.0, -34.0), (-1.0, -35.0)), lean=-10, bob=-1.4),
            C(fists=((17.0, -4.0), (13.0, -5.0)), lean=14, bob=1.5, extra=lambda r: [snow_puff(r, 17, 0, 0, 1.6), sparkle(r, 21, -6, 1, "white")]),
            C(fists=((17.0, -4.0), (13.0, -5.0)), lean=14, bob=1.5, extra=lambda r: snow_puff(r, 17, 0, 1, 1.6)),
            C(fists=((16.0, -6.0), (12.0, -7.0)), lean=10, bob=1.0), C(fists=((13.0, -10.0), (-6.0, -11.0)), lean=4), C()]
    # Glacier (10): punch the floor (0-2: the spikes start at 2), crouch (3-4), dive onto its belly (5), SLIDE (6-8), rise (9)
    gla = [C(fists=((10.0, -24.0), (-6.0, -14.0)), lean=-6), C(fists=((16.0, -3.0), (-6.0, -12.0)), lean=10, bob=1.0),
           C(fists=((16.0, -2.0), (-6.0, -12.0)), lean=10, bob=1.0, extra=lambda r: snow_puff(r, 17, 0, 0, 1.4)),
           C(fists=((10.0, -14.0), (-4.0, -14.0)), lean=0, bob=1.5), C(fists=((12.0, -16.0), (-2.0, -16.0)), lean=-6, bob=2.0),
           C(belly=0.6, fists=((18.0, -10.0), (12.0, -12.0)), streams=True),
           C(belly=0.9, fists=((22.0, -6.0), (18.0, -8.0)), streams=True, extra=lambda r: snow_puff(r, -6, 0, 0, 2.0)),
           C(belly=0.9, fists=((22.0, -6.0), (18.0, -8.0)), streams=True, extra=lambda r: snow_puff(r, -8, 0, 1, 2.0)),
           C(belly=0.85, fists=((21.0, -7.0), (17.0, -9.0)), streams=True, extra=lambda r: snow_puff(r, -10, 0, 2, 2.0)),
           C(belly=0.3, fists=((14.0, -10.0), (-4.0, -10.0)), lean=10)]
    d0 = C(lean=-10, eye="white", fists=((8.0, -28.0), (-10.0, -24.0)))
    d1 = C(lean=-22, bob=3.0, eye="white", fists=((4.0, -24.0), (-12.0, -20.0)))
    knock = C(lean=-12, eye="white", fists=((9.0, -22.0), (-11.0, -20.0)))
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.1] * 6),
             ("Slam", slam, [0.12, 0.12, 0.12, 0.05, 0.1, 0.12, 0.1, 0.1]),
             ("Glacier", gla, [0.1, 0.08, 0.1, 0.1, 0.1, 0.06, 0.1, 0.1, 0.1, 0.12]),
             ("IdleIce", ice_idle, [0.16, 0.14, 0.16, 0.14]), ("RunIce", ice_run, [0.08] * 6)]
    anims += tail_anims(idle[0], [d0, d1, colossus_corpse(0), colossus_corpse(1)], [0.12, 0.14, 0.16, 0.4], knock)
    return sheet("YsvColossus", anims, out, scale=4)


# ================================================================== RIME WARDEN: tower shield, flanged mace, the Widow's gatekeeper
WARDEN_HEAD = {
    "calm": """
..FFf..
.Fddddb
Fdcccdb
deEEecb
dcEecbb
dccecbb
bbbbbba
.bccba.
""",
    "hurt": """
..FFf..
.Fddddb
Fdcccdb
dcaacbb
dcaacbb
dccacbb
bbbbbba
.bccba.
""",
}


def tower_shield(r, x, y, z, raise_=0.0, crest=1):
    """A tall rectangular tower shield (front at x), the red crest of the Widow on it, rime on its rim."""
    top, bot = y - 16.0 - raise_, y - raise_
    r.poly([(x - 3.0, top), (x + 3.0, top - 0.5), (x + 3.5, bot - 1.0), (x, bot + 1.0), (x - 3.5, bot - 1.0)], "steel", z,
           normal=(-0.4, -0.2, 1.0), bias=0.05)
    r.polyline([(x - 3.0, top), (x + 3.0, top - 0.5), (x + 3.5, bot - 1.0)], "steel", z + 0.01, tone=4)
    for i in range(-2, 3): r.dot(x + i, top - 0.6, "frost", 4, z + 0.02)
    # the crest: a red hourglass in a diamond
    cy = (top + bot) / 2.0
    m = "rglow" if crest > 1 else "red"
    for dx, dy in ((0, -2), (-1, -1), (0, -1), (1, -1), (0, 0), (-1, 1), (0, 1), (1, 1), (0, 2)):
        r.dot(x + dx, cy + dy, m, 3 if dy else 2, z + 0.02)


def mace(r, hx, hy, ang, z, length=9.0):
    a = math.radians(ang)
    tip = (hx + math.cos(a) * length, hy + math.sin(a) * length)
    r.line(hx - math.cos(a) * 1.5, hy - math.sin(a) * 1.5, *tip, "wood", z, tone=2)
    r.ell(tip[0], tip[1], 2.4, 2.4, "steel", z + 0.01, bias=0.2)
    for k in range(4):
        b = a + k * math.pi / 2
        r.dot(tip[0] + math.cos(b) * 2.8, tip[1] + math.sin(b) * 2.8, "steel", 3, z + 0.02)
    r.dot(tip[0] - 0.8, tip[1] - 0.8, "frost", 4, z + 0.03)
    return tip


def warden(bob=0.0, lean=0.0, feet=((-3.5, 0.0), (3.5, 0.0)), mace_hand=(-4.0, -16.0), mace_ang=-120.0, shield_dx=0.0,
           shield_raise=0.0, face="calm", crest=1, extra=None):
    r = Rig(1.16)
    T = Xf(lean, (0.0, -1.0))
    hip = T(0.0, -10.0 + bob)
    legs2(r, hip, feet, "steel", 0.0, 5.0, 5.0, rad=(2.0, 1.7, 1.5), boot="steel")
    ch = T(0.0, -17.0 + bob)
    r.ell(ch[0], ch[1], 6.4, 6.0, "steel", 0.5, bias=0.05)
    r.ell(ch[0] - 1.0, ch[1] - 3.4, 4.4, 1.4, "frost", 0.52, bias=0.1)
    r.poly([T(-5.0, -12.0 + bob), T(5.0, -12.0 + bob), T(4.0, -8.5 + bob), T(-4.5, -8.5 + bob)], "steel", 0.6, normal=(-0.2, -0.3, 1.0))
    for x in range(-5, 6): r.dot(*T(x, -22.6 + abs(x) * 0.3 + bob), "steel", 4, 0.53)        # the breastplate's lit rim
    for yb in (-12.0, -10.2): r.line(*T(-5.0, yb + bob), *T(5.0, yb + bob), "steel", 0.61, tone=4 if yb < -11 else 1)
    for (sx, zz) in ((-6.0, -0.6), (6.0, 1.2)):
        r.ell(*T(sx, -21.0 + bob), 3.4, 2.6, "steel", zz, bias=0.15 if sx > 0 else -0.2)
        r.ell(*T(sx - 0.4, -22.8 + bob), 2.6, 1.0, "frost", zz + 0.01, flat=3 if sx < 0 else 4)
    # the mace (behind, in the far hand) and the tower shield (in front)
    mace(r, mace_hand[0], mace_hand[1], mace_ang, -1.0)
    arm(r, T(-5.0, -20.0 + bob), mace_hand, "steel", -0.8, 4.5, 4.5, rad=(1.5, 1.3, 1.2), bias=-0.25)
    hx, hy = T(1.0, -23.5 + bob)
    r.stamp(WARDEN_HEAD[face], hx, hy, 3.0, KNIGHT_LEG, pivot=(3, 7))
    r.dot(hx + 3.2, hy - 7.5, "red", 3, 3.1); r.dot(hx + 3.2, hy - 8.5, "red", 4, 3.1)    # a red plume tip
    arm(r, T(5.0, -20.0 + bob), T(8.0 + shield_dx, -14.0 + bob - shield_raise), "steel", 3.5, 4.0, 4.0, rad=(1.5, 1.3, 1.2))
    tower_shield(r, *T(9.5 + shield_dx, -2.0 + bob), 4.0, raise_=shield_raise, crest=crest)
    if extra: extra(r)
    return r.resolve()


def warden_corpse(stage):
    r = Rig(1.1)
    r.ell(-2.0, -4.0, 8.0, 3.6, "steel", 0.0)
    r.stamp(WARDEN_HEAD["hurt"], -12.0, -1.0, 1.0, KNIGHT_LEG, pivot=(3, 7))
    r.poly([(2.0, -0.3), (16.0, -0.3), (16.0, -5.0), (2.0, -5.5)], "steel", 1.0, normal=(-0.2, -0.9, 0.5))
    for dx, dy in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)): r.dot(9 + dx, -3 + dy, "red", 2, 1.1)
    mace(r, -4.0, -1.0, 170 if stage else 140, 1.2)
    return r.resolve()


def warden_sheet(out):
    Wd = warden
    idle = [Wd(bob=[0, 0.3, 0.6, 0.3][i]) for i in range(4)]
    run = []
    for i in range(6):
        (fa, la), (fb, lb) = walk(i, stride=3.4)
        run.append(Wd(bob=-0.5 * abs(math.sin(i / 6 * math.tau)), lean=6, feet=((-1.5 + fa, la), (1.5 + fb, lb)),
                      mace_hand=(-5.0, -15.0 + math.sin(i / 6 * math.tau)), shield_dx=1.0))
    # Smash (8): mace up and back (0-2), OVERHEAD smash past the shield (3-4: hit at 4, head at (18, -6)), recover
    smash = [Wd(mace_hand=(-4.0, -24.0), mace_ang=-150, shield_dx=-1.0), Wd(mace_hand=(-2.0, -28.0), mace_ang=-170, lean=-6, shield_dx=-2.0),
             Wd(mace_hand=(-1.0, -30.0), mace_ang=170, lean=-8, shield_dx=-2.0, bob=-0.6),
             Wd(mace_hand=(8.0, -26.0), mace_ang=-30, lean=6, shield_dx=-4.0, shield_raise=-2.0,
                extra=lambda r: arc_smear(r, 4, -20, 14, -170, -30, "snow", 2)),
             Wd(mace_hand=(10.0, -16.0), mace_ang=40, lean=12, shield_dx=-5.0, shield_raise=-3.0,
                extra=lambda r: [snow_puff(r, 19, 0, 0, 1.2), sparkle(r, 19, -6, 1, "white")]),
             Wd(mace_hand=(10.0, -16.0), mace_ang=50, lean=10, shield_dx=-4.0, extra=lambda r: snow_puff(r, 19, 0, 1, 1.2)),
             Wd(mace_hand=(-2.0, -18.0), mace_ang=-90, lean=3), Wd()]
    # Rush (8): raise the shield (0-1), RUSH behind it (2-5: moving, the shield blocks shots), skid to a halt (6-7)
    rush = [Wd(shield_raise=2.0, lean=-4), Wd(shield_raise=4.0, lean=-6, crest=2),
            Wd(shield_raise=4.0, lean=14, shield_dx=2.0, crest=2, feet=((-6.0, -1.0), (5.0, 0.0)), extra=lambda r: snow_puff(r, -6, 0, 0)),
            Wd(shield_raise=4.0, lean=16, shield_dx=2.5, crest=2, feet=((-2.0, 0.0), (7.0, -1.0)), extra=lambda r: r.line(-14, -16, -8, -16, "snow", 5, tone=2)),
            Wd(shield_raise=4.0, lean=16, shield_dx=2.5, crest=2, feet=((-6.0, -1.0), (5.0, 0.0)), extra=lambda r: r.line(-14, -12, -8, -12, "snow", 5, tone=2)),
            Wd(shield_raise=4.0, lean=14, shield_dx=2.0, crest=2, feet=((-2.0, 0.0), (7.0, -1.0))),
            Wd(shield_raise=2.0, lean=-4, extra=lambda r: snow_puff(r, 8, 0, 0, 1.2)), Wd(shield_raise=0.5)]
    # Challenge (8): he bangs the mace on the shield three times (1, 3, 5), the crest flares; the sigil rises over him
    def bang(k): return Wd(mace_hand=(7.0, -19.0), mace_ang=-10, crest=2, extra=lambda r: sparkle(r, 13, -18, 1, "white"))
    def lift(k): return Wd(mace_hand=(0.0, -24.0), mace_ang=-120, crest=2 if k else 1)
    chal = [lift(0), bang(0), lift(1), bang(1), lift(1), bang(2), Wd(crest=2, mace_hand=(-2.0, -19.0), mace_ang=-100), Wd()]
    d0 = Wd(lean=-10, face="hurt", mace_hand=(-6.0, -22.0), mace_ang=-150)
    d1 = Wd(lean=-24, face="hurt", bob=2.0, mace_hand=(-8.0, -16.0), mace_ang=170, shield_raise=-2.0)
    knock = Wd(lean=-12, face="hurt", mace_hand=(-6.0, -20.0), mace_ang=-140)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.09] * 6),
             ("Smash", smash, [0.12, 0.12, 0.12, 0.05, 0.08, 0.12, 0.1, 0.1]),
             ("Rush", rush, [0.1, 0.12, 0.08, 0.08, 0.08, 0.08, 0.12, 0.1]),
             ("Challenge", chal, [0.08, 0.1, 0.08, 0.1, 0.08, 0.12, 0.12, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, warden_corpse(0), warden_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvWarden", anims, out, scale=4)


# ================================================================== THE GEODE: a walking rock dome with a violet crystal heart
def geode_body(r, cx, w, h, z, seam=0, split=0.0, legs_ph=None, eye="eye", open_=0.0, half=0):
    """A walking geode: a rough rock dome on stubby legs, split round its middle by a jagged seam with violet crystal
    teeth in it. seam 1-2 makes the seam glow; open_ lifts the upper shell (Geode Burst)."""
    k = r.k
    base = -2.5
    cy = base - h * 0.42                 # the dome's centre: the seam runs round it
    lift = open_ * 4.0 + split * 2.0
    # stubby legs, two each side, the far ones darker
    for n, (lx, zz, b) in enumerate(((-w * 0.55, z - 1.0, -0.35), (w * 0.15, z - 0.9, -0.3), (-w * 0.25, z + 1.0, 0.0), (w * 0.5, z + 1.1, 0.0))):
        ph = legs_ph[n] if legs_ph else 0.0
        r.tube([(cx + lx, base - 1.5), (cx + lx + ph, -0.6)], [2.0, 1.8], "rock", zz, bias=b)
    seam_at = lambda x: cy + math.sin(x * 0.9) * 0.9
    # lower shell: the bottom half of the dome, cut at the seam
    r.ell(cx, cy, w, h * 0.52, "rock", z, bias=-0.05, clip=lambda x, y: y >= (seam_at(x / k) + 0.5) * k)
    # the crystal heart, showing in the seam (wider as it opens)
    for x in range(int(-w * 0.9), int(w * 0.9) + 1, 2):
        sy = seam_at(cx + x)
        crystal(r, cx + x, sy + 1.0, 1.6 + lift * 0.7 + (x % 3) * 0.5, 2.2, "crys", z + 0.15 + x * 0.001, ang=x * 4)
    if seam:
        for x in range(int(-w), int(w) + 1):
            r.dot(cx + x, seam_at(cx + x) - lift * 0.5, "vglow", 3 if seam == 1 else 4, z + 0.3)
    # upper dome: lifted when it opens; rough rind, a frost cap, and two cracks showing crystal
    up = cy - lift
    r.ell(cx, up, w, h * 0.62, "rock", z + 0.2, bias=0.12, clip=lambda x, y: y <= (seam_at(x / k) - lift + 0.5) * k)
    rnd = random.Random(7 + int(w))
    for n in range(int(w * 1.2)):
        a = rnd.uniform(-2.9, -0.2); d = rnd.uniform(0.35, 0.9)
        r.dot(cx + math.cos(a) * w * d, up + math.sin(a) * h * 0.55 * d, "rock", 1 if n % 3 else 4, z + 0.21)
    for x in range(int(-w * 0.55), int(w * 0.45) + 1):
        y = up - h * 0.6 * math.sqrt(max(0.0, 1 - (x / w) ** 2)) + 0.6
        r.dot(cx + x, y, "frost", 4 if x < 0 else 3, z + 0.22)
        if x % 3 == 0: r.dot(cx + x, y + 1, "frost", 3, z + 0.22)
    # the shell is studded with crystal: violet points breaking out of the rind, glowing cracks running between them
    for n, (fx, fy, a) in enumerate(((-0.75, 0.35, -60), (-0.45, 0.75, -30), (0.0, 0.95, 0), (0.42, 0.78, 28), (0.78, 0.38, 62))):
        ox, oy = cx + w * fx, up - h * 0.6 * fy
        crystal(r, ox, oy + 1.4, (4.6 + (n % 2) * 2.2) * min(1.0, w / 14.0), 3.0, "crys", z + 0.26 + n * 0.01, ang=a, bias=0.3)
    for n, (fx, fy) in enumerate(((-0.3, 0.5), (0.2, 0.45), (-0.6, 0.15))):
        ox, oy = cx + w * fx, up - h * 0.6 * fy
        r.polyline([(ox - 2, oy - 1), (ox, oy + 0.5), (ox + 1.5, oy - 0.5), (ox + 3, oy + 1)], "vglow", z + 0.25, tone=3 if n else 4)
    # two stubby rock claws in front (a half-geode has no room for them)
    for n, (dz, b) in enumerate(((-0.6, -0.3), (1.3, 0.0)) if w > 12 else ()):
        bx = cx + w * 0.75 + n * 1.5
        r.tube([(bx - 1.0, cy + 2.0), (bx + 2.0, cy + 3.5 - lift * 0.3), (bx + 3.5, base - 1.0)], [1.6, 1.4, 1.0], "rock", z + dz, bias=b)
        r.dot(bx + 3.8, base - 0.5, "frost", 4, z + dz + 0.01)
    # eyes glowing in the gap of the seam
    ex = cx + w * 0.55
    gy = seam_at(ex) - lift * 0.5 - 0.6
    r.dot(ex, gy, eye, 4, z + 0.35); r.dot(ex - 2.5, gy - 0.2, eye, 4, z + 0.35); r.dot(ex + 0.6, gy, eye, 3, z + 0.34)


def geode(bob=0.0, seam=0, open_=0.0, legs_ph=None, split=0.0, extra=None, eye="eye", shards=None):
    r = Rig(1.0)
    if split <= 0.0:
        geode_body(r, 0.0, 15.5, 25.0 + bob, 0.0, seam=seam, open_=open_, legs_ph=legs_ph, eye=eye)
    else:
        # cracking in two along the seam: two halves drift apart
        geode_body(r, -split * 4.0, 10.0, 18.0, -0.5, seam=2, legs_ph=legs_ph, eye=eye)
        geode_body(r, split * 5.0, 10.0, 18.0, 0.5, seam=2, legs_ph=legs_ph, eye=eye)
        for k in range(6):
            sparkle(r, split * 0.5 + (k - 3) * 1.5, -14.0 - (k % 3) * 4, 2 if k % 2 else 1, "vglow")
    if shards:
        for (x, y, k) in shards: crystal(r, x, y, 3.0, 1.6, "crys", 5.0, ang=80 + k * 10)
    if extra: extra(r)
    return r.resolve()


def geode_half(bob=0.0, seam=0, open_=0.0, legs_ph=None, extra=None, eye="eye", shards=None):
    r = Rig(1.0)
    geode_body(r, 0.0, 8.4, 9.0 + bob, 0.0, seam=seam, open_=open_, legs_ph=legs_ph, eye=eye)
    if shards:
        for (x, y, k) in shards: crystal(r, x, y, 2.6, 1.4, "crys", 5.0, ang=80 + k * 10)
    if extra: extra(r)
    return r.resolve()


def geode_corpse(stage, small=False):
    r = Rig(1.0)
    w = 10.0 if small else 15.0
    r.poly([(-w, -0.3), (w, -0.3), (w * 0.8, -5.0), (-w * 0.8, -5.5)], "rock", 0.0, curve=0.8)
    for i in range(int(-w * 0.7), int(w * 0.7), 3):
        crystal(r, i, -4.5, 2.0 + (i % 2), 1.8, "crys", 0.5, ang=(i * 7) % 30 - 15)
    if stage: r.ell(w + 3, -2.0, 3.0, 2.0, "rock", 1.0)
    return r.resolve()


def geode_anims(G, small=False):
    legs = lambda i: [math.sin(i / 6 * math.tau + k * 1.6) * 1.5 for k in range(4)]
    idle = [G(bob=[0, 0.3, 0.6, 0.3][i]) for i in range(4)]
    run = [G(bob=-0.5 * abs(math.sin(i / 6 * math.tau)), legs_ph=legs(i)) for i in range(6)]
    k = 0.7 if small else 1.0
    slam = [G(bob=1.0), G(bob=2.5, extra=lambda r: sparkle(r, 0, -30 * k, 2, "white")), G(bob=3.0),
            G(bob=-2.0, extra=lambda r: [snow_puff(r, 14 * k, 0, 0, 1.4), snow_puff(r, -14 * k, 0, 0, 1.4)]),
            G(bob=-1.5, extra=lambda r: snow_puff(r, 14 * k, 0, 1, 1.4)), G(bob=-0.5), G(), G()]
    burst = [G(bob=-1.0, seam=1), G(bob=-2.0, seam=2), G(bob=-2.0, seam=2, open_=0.5), G(bob=-2.0, seam=2, open_=1.0,
            shards=[(14 * k, -12 * k, 0), (15 * k, -18 * k, 1)]),
             G(bob=-1.5, seam=2, open_=0.8, extra=lambda r: sparkle(r, 18 * k, -14 * k, 1, "vglow")), G(seam=1, open_=0.3), G(), G()]
    return idle, run, slam, burst


def geode_sheet(out):
    G = geode
    idle, run, slam, burst = geode_anims(G)
    seam_idle = [G(bob=[0, 0.3, 0.6, 0.3][i], seam=1 + (i % 2)) for i in range(4)]
    seam_run = [G(bob=-0.5 * abs(math.sin(i / 6 * math.tau)), seam=1 + (i % 2),
                  legs_ph=[math.sin(i / 6 * math.tau + k * 1.6) * 1.5 for k in range(4)]) for i in range(6)]
    split = [G(seam=2, bob=-1.0), G(seam=2, bob=-2.0, extra=lambda r: sparkle(r, 0, -26, 1, "vglow")), G(split=0.4), G(split=1.0), G(split=1.6)]
    H = geode_half
    hidle, hrun, hslam, hburst = geode_anims(H, small=True)
    d0 = G(bob=2.0, eye="white", seam=0); d1 = G(bob=4.0, eye="white", open_=0.6)
    knock = G(bob=1.5, eye="white")
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.09] * 6),
             ("Slam", slam, [0.12, 0.12, 0.12, 0.05, 0.1, 0.12, 0.1, 0.1]),
             ("Burst", burst, [0.1, 0.1, 0.1, 0.06, 0.1, 0.12, 0.1, 0.1]),
             ("IdleSeam", seam_idle, [0.12, 0.1, 0.12, 0.1]), ("RunSeam", seam_run, [0.09] * 6),
             ("Split", split, [0.1, 0.1, 0.08, 0.08, 0.12]),
             ("HalfIdle", hidle, [0.16, 0.14, 0.16, 0.14]), ("HalfRun", hrun, [0.075] * 6),
             ("HalfSlam", hslam, [0.1, 0.1, 0.1, 0.05, 0.08, 0.1, 0.08, 0.08]),
             ("HalfBurst", hburst, [0.08, 0.08, 0.08, 0.05, 0.08, 0.1, 0.08, 0.08])]
    anims += tail_anims(idle[0], [d0, d1, geode_corpse(0), geode_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    sheet("YsvGeode", anims, out, scale=4)
    hd0 = H(bob=2.0, eye="white"); hd1 = H(bob=3.0, eye="white", open_=0.6)
    hanims = [("Idle", hidle, [0.16, 0.14, 0.16, 0.14]), ("Run", hrun, [0.075] * 6),
              ("Slam", hslam, [0.1, 0.1, 0.1, 0.05, 0.08, 0.1, 0.08, 0.08]),
              ("Burst", hburst, [0.08, 0.08, 0.08, 0.05, 0.08, 0.1, 0.08, 0.08])]
    hanims += tail_anims(hidle[0], [hd0, hd1, geode_corpse(0, True), geode_corpse(1, True)], [0.1, 0.12, 0.14, 0.4], H(bob=1.5, eye="white"))
    return sheet("YsvGeodeHalf", hanims, out, scale=4)


# ================================================================== PRISM ORACLE: a veiled seer on a floating prism that throws rainbows
SPECTRUM = ["red", "aurp", "eye", "aurg", "vglow"]
ORACLE_HEAD = {
    "calm": """
..vVv..
.vVVVvu
vVVVVVu
vVsSSku
vVeSeku
uvsSskw
uvvsvuw
uu...ww
""",
    "hurt": """
..vVv..
.vVVVvu
vVVVVVu
vVsSSku
vVmSmku
uvsSskw
uvvsvuw
uu...ww
""",
}


def prism(r, cx, cy, size, z, flare=0, spin=0):
    """A floating triangular prism (point down), clear glass with a spectrum caught in it."""
    s = size
    pts = [(cx - s, cy - s * 0.55), (cx + s, cy - s * 0.55), (cx + 0.6 * math.sin(spin), cy + s)]
    r.poly(pts, "glass", z, normal=(-0.4, -0.5, 0.8), bias=0.1)
    r.poly([(cx - s, cy - s * 0.55), (cx + s, cy - s * 0.55), (cx + s * 0.6, cy - s * 0.85), (cx - s * 0.6, cy - s * 0.85)], "glass", z - 0.01,
           normal=(-0.1, -1.0, 0.4), bias=0.15)
    for k, m in enumerate(SPECTRUM):
        t = (k + spin) % 5 / 5.0
        x = lerp(cx - s * 0.6, cx + s * 0.6, t)
        r.line(x, cy - s * 0.4, cx + (x - cx) * 0.3, cy + s * 0.5, m, z + 0.01, tone=3 if flare else 2)
    if flare:
        for k in range(flare * 3):
            a = math.radians(-160 + k * (140 / max(1, flare * 3 - 1)))
            for d in range(2, 4 + flare):
                r.dot(cx + math.cos(a) * (s + d), cy + math.sin(a) * (s + d) * 0.6, SPECTRUM[k % 5], 3, z + 0.5)


def oracle(alt=3.0, bob=0.0, lean=0.0, hand=(6.0, -27.0), hand2=(-5.0, -24.0), flare=0, spin=0, face="calm", extra=None):
    r = Rig(1.0)
    py = -alt - 9.0 + bob
    shadow(r, 0.0, -1.0, 6.0)
    prism(r, 0.0, py, 10.0, 0.0, flare=flare, spin=spin)
    # the seer, sitting cross-legged on the prism's top face, veiled in silk
    sx, sy = 0.0, py - 5.0
    r.poly([(sx - 9.0, sy + 0.5), (sx + 9.0, sy + 0.5), (sx + 6.0, sy - 3.5), (sx - 6.0, sy - 3.5)], "silk", 0.5, curve=0.6)
    robe(r, (sx, sy - 12.0), sy - 1.0, 11.0, sway=0.0, mat="veil", z=0.6, top_w=2.6, flare=1.3)
    r.poly([(sx - 1.5, sy - 15.0), (sx - 8.5, sy - 4.0), (sx - 10.0, sy - 0.5), (sx - 3.0, sy - 8.0)], "veil", 0.3, bias=-0.1)
    arm(r, (sx - 1.6, sy - 11.0), hand2, "veil", 0.4, 4.0, 4.0, rad=(1.0, 0.8, 0.7), bias=-0.25)
    arm(r, (sx + 1.6, sy - 11.0), hand, "veil", 1.5, 4.0, 4.0, rad=(1.0, 0.8, 0.7))
    r.dot(hand[0], hand[1], "skin", 3, 1.55)
    r.stamp(ORACLE_HEAD[face], sx + 0.5, sy - 11.5, 2.0, {"v": ("veil", 3), "V": ("veil", 4), "u": ("veil", 2), "w": ("veil", 1),
            "s": ("skin", 3), "S": ("skin", 4), "k": ("skin", 2), "e": ("vglow", 4), "m": ("silk", 0)}, pivot=(3, 7))
    if extra: extra(r)
    return r.resolve()


def oracle_corpse(stage):
    r = Rig(1.15)
    prism(r, -6.0, -4.0, 4.5, 0.0, spin=1)
    r.poly([(0.0, -0.3), (12.0, -0.3), (10.0, -3.0), (2.0, -3.5)], "veil", 0.5)
    r.stamp(ORACLE_HEAD["hurt"], 13.0, -1.0, 1.0, {"v": ("veil", 3), "V": ("veil", 4), "u": ("veil", 2), "w": ("veil", 1),
            "s": ("skin", 3), "S": ("skin", 4), "k": ("skin", 2), "e": ("vglow", 4), "m": ("silk", 0)}, pivot=(3, 7))
    if stage:
        for (x, y) in ((-12, -1), (-2, -1)): r.dot(x, y, "glass", 4, 1)
    return r.resolve()


def oracle_sheet(out):
    O = oracle
    idle = [O(bob=[0, -0.5, -1.0, -0.5][i], spin=i) for i in range(4)]
    run = [O(bob=[0, -0.4, -0.8, -0.4, 0, 0.3][i], lean=6, spin=i, hand=(7.0, -26.0)) for i in range(6)]
    # Bolt (7): raise the hand (0-1), the prism catches light (2), the bolt leaves her palm at (9, -28) (3), lower
    bolt = [O(hand=(5.0, -30.0)), O(hand=(4.0, -33.0), spin=1, extra=lambda r: sparkle(r, 4, -35, 2, "white")),
            O(hand=(8.0, -30.0), spin=2, flare=1), O(hand=(10.0, -28.0), spin=3, flare=1, extra=lambda r: sparkle(r, 12, -28, 1, "white")),
            O(hand=(8.0, -27.0), spin=4), O(spin=0), O()]
    # Sunburst (9): she lifts both hands (0-2), the prism FLARES for 0.6 s (3-6), the light runs into the ice (7), settle
    sun = [O(hand=(5.0, -31.0), hand2=(-5.0, -30.0)), O(hand=(4.0, -34.0), hand2=(-4.0, -33.0), bob=-0.6),
           O(hand=(4.0, -36.0), hand2=(-4.0, -35.0), bob=-1.0, flare=1),
           O(hand=(4.0, -36.0), hand2=(-4.0, -35.0), bob=-1.2, flare=2, spin=1),
           O(hand=(4.0, -36.0), hand2=(-4.0, -35.0), bob=-1.2, flare=3, spin=2),
           O(hand=(4.0, -36.0), hand2=(-4.0, -35.0), bob=-1.2, flare=3, spin=3),
           O(hand=(4.0, -36.0), hand2=(-4.0, -35.0), bob=-1.2, flare=2, spin=4),
           O(hand=(7.0, -26.0), hand2=(-7.0, -24.0), flare=1), O()]
    d0 = O(lean=-10, face="hurt", hand=(4.0, -30.0), hand2=(-7.0, -27.0))
    d1 = O(alt=3.0, lean=-24, face="hurt", hand=(2.0, -24.0), hand2=(-8.0, -20.0))
    knock = O(lean=-12, face="hurt", hand=(4.0, -29.0), hand2=(-7.0, -26.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Bolt", bolt, [0.12, 0.1, 0.08, 0.06, 0.1, 0.1, 0.1]),
             ("Sunburst", sun, [0.1, 0.1, 0.1, 0.15, 0.15, 0.15, 0.15, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, oracle_corpse(0), oracle_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("YsvOracle", anims, out, scale=4)


JOBS = [("YsvBride", bride_sheet), ("YsvWraith", wraith_sheet), ("YsvColossus", colossus_sheet), ("YsvWarden", warden_sheet),
        ("YsvGeode", geode_sheet), ("YsvOracle", oracle_sheet)]
SYNC = {
    "YsvBride": {"Breath": [("frost breath leaves her lips at (11, -26), puffs on 3, 4, 5", 3)],
                 "Sweep": [("the train starts its sweep round her (r 40)", 3)]},
    "YsvWraith": {"Claw": [("RAKE: claws at (14, -10); box 16 x 16 at (12, -13)", 3)],
                  "Maelstrom": [("the vortex opens under the hero", 4)]},
    "YsvColossus": {"Slam": [("SLAM: fists at (17, -4); the quake ahead at (17, 0)", 3)],
                    "Glacier": [("the ice spikes start running at the hero", 2), ("the belly slide starts (move 230 px/s)", 5),
                                ("the slide ends", 9)]},
    "YsvWarden": {"Smash": [("SMASH: the mace head at (18, -6); box 18 x 14 at (15, -5)", 4)],
                  "Rush": [("RUSH: moving behind the shield, frames 2-5", 2)],
                  "Challenge": [("the third bang: the challenge lands", 5)]},
    "YsvGeode": {"Slam": [("SLAM: the dome lands; box 22 x 14 at (15, -5)", 3)], "Burst": [("four crystals fly from (14, -12)", 3)],
                 "Split": [("the two halves part", 3)]},
    "YsvOracle": {"Bolt": [("the bolt leaves her palm at (9, -28)", 3)],
                  "Sunburst": [("the prism flares (0.6 s)", 3), ("the light runs into the ice", 7)]},
}
NOTES = {
    "YsvBride": "IdleWidow / RunWidow / BreathWidow / SweepWidow: the same moves with the veil turned black (Widowed).",
    "YsvColossus": "IdleIce / RunIce: it leans forward and frost streams off it while it stands on ice (Downhill).",
    "YsvGeode": "IdleSeam / RunSeam: the seam glows from 60 % health. Split: it cracks in two. Half*: the half it is "
                "after the split (YsvGeodeHalf is the other half, a separate monster).",
}
