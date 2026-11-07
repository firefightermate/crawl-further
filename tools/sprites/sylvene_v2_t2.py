"""Sylvene tier 2: Spore Husk, Bloom Witch, Bramble Knight, Strangler Vine, Gall Wasp, Bloatfly. Built through
sylvene_v2_rigs.py. T2 idle limit 28 x 26; none is smaller than the sheet it replaces."""
import math
from sylvene_v2_rigs import (Rig, Xf, chain, ik, lerp, sheet, tail_anims, cap, vine, thorn, leaf, wing, pod, motes, puff,
                             smears, sparks, soil, dust_puff)


def arm(r, sh, hand, l1, l2, mat, z, rad=(1.2, 1.0, 0.9), bend=1, bias=0.0, mat2=None):
    el = ik(sh[0], sh[1], hand[0], hand[1], l1, l2, bend=bend)
    r.tube([sh, el], [rad[0], rad[1]], mat, z, bias=bias)
    r.tube([el, hand], [rad[1], rad[2]], mat2 or mat, z + 0.01, bias=bias)
    return el


def legs(r, hip, feet, l1, l2, mat, z=(-1.0, 1.0), rad=(1.4, 1.1), knee=1, spread=1.2, foot=None, foot_len=2.4):
    for k, f in enumerate(feet):
        hp = (hip[0] + (-spread if k == 0 else spread), hip[1] + 0.4)
        kn = ik(hp[0], hp[1], f[0], f[1] - 1.0, l1, l2, bend=-knee)
        b = -0.3 if k == 0 else 0.0
        r.tube([hp, kn], [rad[0], rad[1]], mat, z[k], bias=b)
        r.tube([kn, (f[0], f[1] - 1.0)], [rad[1], rad[1] * 0.9], mat, z[k] + 0.01, bias=b + 0.1)
        if foot:
            r.poly([(f[0] - 1.2, f[1] - 1.8), (f[0] + foot_len, f[1] - 1.0), (f[0] + foot_len, f[1]), (f[0] - 1.2, f[1])], foot, z[k] + 0.02,
                   bias=b + 0.2)


def shelf(r, x, y, w, z, mat="fung", ang=0.0):
    """A bracket of shelf fungus: a flat lip, lit on top, with a dark underside."""
    T = Xf(ang, (x, y))
    r.ell(*T(x, y), w, w * 0.42, mat, z, bias=0.15, ang=ang, clip=lambda px, py: py <= T(x, y)[1] + 0.3)
    r.line(*T(x - w + 0.6, y + 0.6), *T(x + w - 0.6, y + 0.6), mat, z + 0.01, tone=1)


# ================================================================== SPORE HUSK: a corpse overgrown with shelf fungus, a fungal club
HUSK_LEG = {"k": ("corpse", 0), "d": ("corpse", 1), "c": ("corpse", 2), "C": ("corpse", 3), "m": ("chitin", 0),
            "g": ("glowg", 3), "G": ("glowg", 4), "f": ("fung", 2), "F": ("fung", 3), "w": ("mould", 3), "t": ("thorn", 2)}
HUSK_HEAD = {
    # pivot (3, 6): the neck. A sunken corpse face, one eye glowing rot-green, a shelf of fungus over the brow
    "calm": """
.fFFFf.
fFFFFFf
.dCCCc.
dcmCgCk
dCCCCCk
.dcttdk
..dddk.
""",
    "roar": """
.fFFFf.
fFFFFFf
.dCCCc.
dcmCGCk
dCmmmCk
.dmmmdk
..dtdk.
""",
    "dead": """
.......
.fFFFf.
fdCCCcf
dcmCmCk
dCCCCCk
.dcmcdk
..dddk.
""",
}


def husk(lean=0.0, bob=0.0, feet=((-4.0, 0.0), (3.5, 0.0)), hand=(8.0, -9.0), hand2=(-6.0, -8.0), club=-60.0, face="calm",
         smear=None, spark=None, extra=None, head_d=(0.0, 0.0), cone=None, knee=1):
    r = Rig()
    hip = (0.0, -7.5 + bob)
    T = Xf(lean, hip)
    legs(r, hip, feet, 3.8, 3.6, "corpse", rad=(1.6, 1.3), foot="bark", knee=knee)
    # rags round the hips
    r.poly([T(-4.2, hip[1] - 2.0), T(4.4, hip[1] - 2.2), T(4.8, hip[1] + 2.0), T(2.0, hip[1] + 1.4), T(-1.0, hip[1] + 2.6),
            T(-4.6, hip[1] + 1.6)], "spore", 0.4, normal=(-0.3, -0.2, 0.9))
    # far arm
    sh_f = T(-4.5, hip[1] - 9.0)
    arm(r, sh_f, hand2, 3.8, 3.6, "corpse", -1.0, rad=(1.5, 1.3, 1.2), bend=1, bias=-0.3)
    r.ell(hand2[0], hand2[1], 1.4, 1.4, "corpse", -0.99, bias=-0.2)
    # hunched torso with big shoulders, shelf fungus up the back and on the shoulders
    r.ell(*T(-0.5, hip[1] - 6.0), 5.6, 5.4, "corpse", 0.0, bias=0.05)
    r.ell(*T(-2.0, hip[1] - 9.0), 4.4, 3.2, "corpse", 0.1, bias=0.1)
    r.ell(*T(1.0, hip[1] - 4.6), 2.6, 2.0, "mould", 0.15, bias=0.0)
    for (x, y, w, a) in ((-5.2, -8.0, 2.6, -20), (-5.6, -4.6, 2.2, -10), (-3.6, -11.4, 2.8, -8), (2.6, -10.4, 2.4, 12)):
        shelf(r, *T(x, hip[1] + y + 7.5 - 7.5), w, 0.4, ang=a + lean * 0.3)
    hx, hy = T(3.6 + head_d[0], hip[1] - 10.0 + head_d[1])
    r.stamp(HUSK_HEAD[face], hx, hy, 0.8, HUSK_LEG, pivot=(3, 6))
    # near arm and the club of fungus-grown wood
    sh_n = T(3.0, hip[1] - 8.6)
    arm(r, sh_n, hand, 3.8, 3.6, "corpse", 2.0, rad=(1.6, 1.4, 1.3), bend=-1)
    a = math.radians(club)
    tip = (hand[0] + 11.0 * math.cos(a), hand[1] + 11.0 * math.sin(a))
    r.tube([(hand[0] - 1.5 * math.cos(a), hand[1] - 1.5 * math.sin(a)), tip], [1.0, 2.2], "bark", 2.5, bias=0.05)
    for k, f in enumerate((0.55, 0.8, 0.98)):
        px, py = hand[0] + 11.0 * f * math.cos(a), hand[1] + 11.0 * f * math.sin(a)
        shelf(r, px - math.sin(a) * 1.6 * (1 if k % 2 else -1), py + math.cos(a) * 1.6 * (1 if k % 2 else -1), 1.8, 2.6 + k * 0.01,
              ang=club + 90)
    r.dot(tip[0], tip[1], "mould", 4, 2.7)
    r.ell(hand[0], hand[1], 1.5, 1.4, "corpse", 2.8, bias=0.1)
    if cone:
        k, x0, y0 = cone
        for i in range(4 + k):
            d = 3.0 + i * 3.2
            puff(r, x0 + d, y0 + d * 0.2, 1.6 + i * 0.7, 6.0 + i * 0.01, "sporec", min(3, max(0, k - 1 + (i > 3))), seed=i + 3, n=4)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def shake_ring(r, x, y, k):
    """The floor ringing round the club (the Shake the Tree tell): an ellipse widening and fading."""
    rx = 6 + k * 6
    for i in range(32):
        a = i / 32 * math.tau
        if (i + k) % 3 == 0: continue
        r.dot(x + rx * math.cos(a), y - 1 + rx * 0.35 * math.sin(a), "glowg", max(1, 4 - k), 7.0)


def husk_sheet(outdir):
    H = husk
    idle = [H(bob=[0, 0.4, 0.8, 0.4][i], hand=(8.0, -9.0 + [0, 0.4, 0.8, 0.4][i]), club=-60 + [0, 2, 4, 2][i],
              head_d=(0.0, [0, 0.4, 0.8, 0.4][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(H(lean=8, bob=-0.8 * abs(math.sin(ph)), club=-50 + 8 * math.sin(ph), hand=(8.5, -8.5 + 0.8 * math.sin(ph)),
                     hand2=(-5.5 - 1.5 * math.sin(ph), -8.0), feet=((-4.0 + 3.0 * math.cos(ph), -max(0, 1.6 * math.sin(ph))),
                                                                  (3.5 - 3.0 * math.cos(ph), -max(0, -1.6 * math.sin(ph))))))
    # Smash (8): hauls the club back over the shoulder (0-1), up high (2), SLAMS it down (3: club head lands at (17, -1);
    # the floor rings), the ring spreads (4-5: ripe pods within 40 px shake and burst), heaves it back up (6-7)
    sm = [H(lean=-6, club=-120, hand=(4.0, -15.0), face="roar"), H(lean=-14, club=-160, hand=(1.0, -18.0), face="roar", bob=-0.6),
          H(lean=-10, club=-185, hand=(0.0, -19.0), face="roar", bob=-0.8),
          H(lean=16, club=10, hand=(9.0, -7.0), face="roar", bob=0.8, head_d=(1.0, 1.0), knee=1,
            smear=[("arc", 4.0, -10.0, 13.0, -150, 10, "fung", 2)], spark=[(17.0, -1.0, 1)], extra=lambda r: shake_ring(r, 17.0, 0.0, 0)),
          H(lean=14, club=12, hand=(9.0, -6.5), face="roar", bob=1.0, head_d=(1.0, 1.0), extra=lambda r: shake_ring(r, 17.0, 0.0, 1)),
          H(lean=10, club=8, hand=(9.0, -7.0), bob=0.6, extra=lambda r: shake_ring(r, 17.0, 0.0, 2)),
          H(lean=4, club=-30, hand=(8.5, -8.5)), H()]
    # Belch (8): inhales, chest swelling (0-2), BELCHES a wide cone of spores (3: cone from the mouth at (8, -15)), (4-5) the
    # cloud rolls out, recovers (6-7)
    bl = [H(lean=-8, face="calm", head_d=(-1.0, -1.0)), H(lean=-14, face="roar", head_d=(-1.5, -1.5), bob=-0.4),
          H(lean=-16, face="roar", head_d=(-1.5, -2.0), bob=-0.6),
          H(lean=12, face="roar", head_d=(1.5, 0.5), cone=(0, 9.0, -14.0)), H(lean=12, face="roar", head_d=(1.5, 0.5), cone=(1, 9.0, -14.0)),
          H(lean=10, face="roar", head_d=(1.0, 0.5), cone=(2, 9.0, -14.0)), H(lean=4), H()]
    d0 = H(face="roar", lean=-16, club=-100, hand=(4.0, -13.0))
    d1 = H(face="dead", lean=20, club=40, hand=(10.0, -4.0), bob=2.0, head_d=(2.0, 3.0), feet=((-4.0, 0.0), (4.0, -1.0)))
    d2 = _husk_corpse(0)
    corpse = _husk_corpse(1)
    knock = H(face="roar", lean=-18, club=-90, hand=(5.0, -12.0), head_d=(-1.0, -1.0))
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("Smash", sm, [0.12, 0.12, 0.1, 0.05, 0.1, 0.12, 0.12, 0.12]),
             ("Belch", bl, [0.12, 0.12, 0.12, 0.08, 0.12, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylSporeHusk", anims, outdir, scale=5)


def _husk_corpse(stage):
    r = Rig()
    r.ell(-1.0, -3.0, 8.0, 3.0, "corpse", 0.0)
    r.ell(-3.0, -4.0, 4.0, 2.0, "corpse", 0.1, bias=0.1)
    for (x, w) in ((-6.0, 2.4), (-2.0, 2.8), (2.0, 2.2)):
        shelf(r, x, -5.2 - (1 if stage else 0), w, 0.3)
    r.stamp(HUSK_HEAD["dead"], 8.0, -1.0, 0.5, HUSK_LEG, pivot=(3, 6))
    r.tube([(9.0, -1.0), (19.0, -1.6)], [1.0, 2.0], "bark", 0.4)
    shelf(r, 16.0, -3.0, 1.8, 0.45)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.6)
    return r.resolve()


# ================================================================== BLOOM WITCH: a thin witch whose head is a lily, roots for a hem
WITCH_LEG = {"l": ("lily", 1), "L": ("lily", 2), "W": ("lily", 3), "X": ("lily", 4), "m": ("chitin", 0), "y": ("pollen", 3),
             "Y": ("pollen", 4), "g": ("glowg", 3), "p": ("pale", 2), "P": ("pale", 3), "d": ("pale", 1)}
WITCH_HEAD = {
    # pivot (5, 10): the neck. Lily petals cup a small pale green face like a hood; pollen-yellow stamens rise between
    "calm": """
..l.YyY.l..
.lW..y..Wl.
.lWl...lWl.
lWWXl.lXWWl
lWLWdPdWLWl
.lLdmPmdLl.
.lLdPPPdLl.
..lLdmdLl..
...lLdLl...
....dPd....
.....d.....
""",
    "cast": """
l..YyYyY..l
lW..yyy..Wl
lWl.....lWl
lWWl...lWWl
lWLWdPdWLWl
.lLdgPgdLl.
.lLdPPPdLl.
..lLdmdLl..
...lLdLl...
....dPd....
.....d.....
""",
    "dead": """
...........
...........
...........
...........
...........
...l...l...
..lWdPdWl..
.lLdmPmdLl.
..lLdPdLl..
....dPd....
.....d.....
""",
}


def witch(lean=0.0, bob=0.0, hem=0.0, hand=(5.0, -14.0), hand2=(-4.0, -12.0), face="calm", lance=None, smear=None, spark=None,
          extra=None, pods=(), head_d=(0.0, 0.0), sway=0.0, sink=0.0):
    r = Rig()
    hip = (0.0, -7.4 + bob + sink)
    T = Xf(lean, (0.0, 0.0))
    # hem of roots fanning onto the floor
    for k in range(9):
        x = -6.0 + k * 1.5
        ph = hem + k * 0.9
        r.tube([T(x * 0.7, hip[1] + 3.0), (x + 0.6 * math.sin(ph), -1.4), (x * 1.25 + 0.8 * math.sin(ph + 1), 0.0)],
               [0.9, 0.7, 0.5], "bark", -0.5 + 0.15 * k, bias=-0.1 * (k % 2))
    # gown: a narrow bell of pale green petals
    gp = [T(-2.4, hip[1] - 7.4), T(2.6, hip[1] - 7.4), T(3.4, hip[1] - 2.0), T(6.0 + sway, hip[1] + 4.2), T(0.0, hip[1] + 5.4),
          T(-6.2 + sway, hip[1] + 4.2), T(-3.4, hip[1] - 2.0)]
    r.poly(gp, "pale", 0.0, normal=(-0.2, -0.2, 0.9), curve=0.8)
    for k in (-1, 1):
        r.line(*T(k * 1.4, hip[1] - 3.0), *T(k * 4.2 + sway, hip[1] + 4.2), "pale", 0.05, tone=1)
    for k in range(5):
        hx_, hy_ = T(-5.0 + k * 2.5 + sway, hip[1] + 4.6)
        r.ell(hx_, hy_, 1.6, 1.2, "lily", 0.1 + 0.01 * k, bias=0.1)
    r.poly([T(-1.2, hip[1] - 2.0), T(1.2, hip[1] - 2.0), T(0.0, hip[1] + 3.0)], "pollen", 0.08, normal=(0, -0.3, 0.9))
    r.poly([T(-1.6, hip[1] - 7.4), T(1.8, hip[1] - 7.4), T(1.2, hip[1] - 4.0), T(-1.2, hip[1] - 4.0)], "lily", 0.1, normal=(-0.3, -0.4, 0.8))
    # far arm (thin, pale)
    el2 = arm(r, T(-2.2, hip[1] - 6.6), hand2, 3.4, 3.2, "pale", -0.6, rad=(1.0, 0.9, 0.7), bend=1, bias=-0.3)
    r.tube([el2, hand2], [1.0, 1.8], "lily", -0.55, bias=-0.3)
    hx, hy = T(0.2 + head_d[0], hip[1] - 6.8 + head_d[1])
    r.stamp(WITCH_HEAD[face], hx, hy, 1.0, WITCH_LEG, pivot=(5, 10))
    # near arm, holding nothing but a pollen glow
    el = arm(r, T(2.2, hip[1] - 6.6), hand, 3.4, 3.2, "pale", 2.0, rad=(1.0, 0.9, 0.8), bend=-1)
    r.tube([el, (lerp(el[0], hand[0], 0.8), lerp(el[1], hand[1], 0.8))], [1.0, 1.9], "lily", 2.05, bias=0.05)
    r.dot(hand[0], hand[1], "pale", 3, 2.2)
    if lance:
        x0, y0, ln, k = lance
        for i in range(int(ln)):
            r.dot(x0 + i, y0, "pollc", 4 if i > ln - 3 else 3 - (i < 2), 6.0)
        if k: motes(r, x0 + ln * 0.5, y0, 0, n=4, mat="pollc", spread=3.0, seed=k)
    for (x, y, s, rp) in pods:
        pod(r, x, y, s, 5.0, ripe=rp)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def witch_sheet(outdir):
    W = witch
    idle = [W(bob=[0, -0.4, -0.8, -0.4][i], hem=i * 0.8, sway=[0, 0.3, 0.6, 0.3][i], hand=(5.0, -14.0 + [0, -0.4, -0.8, -0.4][i]))
            for i in range(4)]
    run = [W(lean=6, bob=-0.5 * abs(math.sin(i / 6 * math.tau)), hem=i * 1.4, sway=-1.0, hand=(4.0, -13.0), hand2=(-5.0, -11.0))
           for i in range(6)]
    # Lance (6): draws pollen to her hand (0-1), THRUSTS it out (2: the lance leaves the palm at (9, -15)), streak (3), recover
    ln = [W(lean=-6, hand=(1.0, -16.0), face="cast", extra=lambda r: motes(r, 1.0, -16.0, 0, n=5, mat="pollc", spread=3.0)),
          W(lean=-10, hand=(-1.0, -17.0), face="cast", extra=lambda r: motes(r, -1.0, -17.0, 1, n=6, mat="pollc", spread=2.0, seed=4)),
          W(lean=10, hand=(8.0, -15.0), face="cast", lance=(9.0, -15.0, 8, 1)),
          W(lean=8, hand=(8.0, -15.0), face="cast", lance=(12.0, -15.0, 6, 2)), W(lean=3, hand=(6.0, -14.0)), W()]
    # Graft (8): raises both hands (0-2), the lily opens (3), a ripe pod swells over her palms (4: GRAFT), sends it off (5),
    # bows (6-7)
    gr = [W(hand=(4.0, -18.0), hand2=(-3.0, -18.0)), W(hand=(4.0, -21.0), hand2=(-3.0, -21.0), face="cast", bob=-0.6),
          W(hand=(3.5, -23.0), hand2=(-2.5, -23.0), face="cast", bob=-1.0, extra=lambda r: motes(r, 0.5, -25.0, 0, n=6, spread=4.0)),
          W(hand=(3.5, -23.0), hand2=(-2.5, -23.0), face="cast", bob=-1.0, pods=[(0.5, -23.5, 3.0, 0.5)]),
          W(hand=(3.5, -23.0), hand2=(-2.5, -23.0), face="cast", bob=-1.0, pods=[(0.5, -23.5, 4.2, 1.0)],
            extra=lambda r: motes(r, 0.5, -27.0, 1, n=8, spread=5.0, seed=6)),
          W(hand=(7.0, -16.0), hand2=(-6.0, -16.0), face="cast", extra=lambda r: motes(r, 0.5, -26.0, 2, n=6, spread=7.0, seed=8)),
          W(lean=6, hand=(5.0, -13.0)), W()]
    d0 = W(face="cast", lean=-14, hand=(2.0, -18.0), hand2=(-5.0, -17.0))
    d1 = W(face="dead", lean=-30, sink=3.0, hand=(3.0, -8.0), hand2=(-6.0, -8.0))
    d2 = _witch_corpse(0)
    corpse = _witch_corpse(1)
    knock = W(face="cast", lean=-16, hand=(3.0, -16.0), hand2=(-6.0, -15.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Lance", ln, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Graft", gr, [0.12, 0.12, 0.12, 0.1, 0.12, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylBloomWitch", anims, outdir, scale=5)


def _witch_corpse(stage):
    r = Rig()
    r.poly([(-6.0, -3.0), (5.0, -3.6), (7.0, 0.0), (-7.0, 0.0)], "pale", 0.0, curve=0.6)
    for k in range(6):
        r.tube([(-6.0 + k * 0.4, -1.0), (-9.0 - k * 0.6, 0.0)], [0.7, 0.5], "bark", -0.3 + 0.1 * k)
    for (x, a) in ((7.0, -40), (8.0, 10), (9.0, -80)):
        leaf(r, 7.0, -2.0, a, 3.6, 0.5, mat="lily", w=1.4)
    r.stamp(WITCH_HEAD["dead"], 11.0, 1.0 + (0 if stage else 1), 0.6, WITCH_LEG, pivot=(5, 10))
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.4)
    return r.resolve()


# ================================================================== BRAMBLE KNIGHT: armour split open by bramble, a thorn sword
KNIGHT_LEG = {"k": ("bark", 1), "d": ("bark", 2), "r": ("bark", 3), "R": ("bark", 4), "H": ("rust", 4), "m": ("chitin", 0),
              "g": ("moss", 2), "G": ("moss", 3), "e": ("glowg", 3), "E": ("glowg", 4), "b": ("blood", 3)}
KNIGHT_HEAD = {
    # pivot (3, 7): the neck. A rusted great helm split down the brow, bramble pushing through the visor, green eyes
    "calm": """
..gGb..
.rRgRd.
rRRgRRd
RRmgmRk
rEmmmEk
rRRRRRk
.dRRRk.
..dkk..
""",
    "roar": """
..gGb..
.rRgRd.
rRRgRRd
RRmgmRk
rEEmEEk
rRmmmRk
.dRRRk.
..dkk..
""",
    "dead": """
.......
.rRgRd.
rRRgRRd
RRmgmRk
rmmmmmk
rRRRRRk
.dRRRk.
..dkk..
""",
}


def thorn_sword(r, hx, hy, ang, z, ln=13.0, sap=False):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    # crossguard of knotted root, a blade that is one long thorn with smaller thorns along its back
    r.tube([(hx - s * 2.6, hy + c * 2.6), (hx + s * 2.6, hy - c * 2.6)], [1.0], "bark", z + 0.02)
    r.poly([(hx + c * 1.0 - s * 2.3, hy + s * 1.0 + c * 2.3), (hx + c * ln * 0.7 - s * 1.9, hy + s * ln * 0.7 + c * 1.9),
            (hx + c * ln, hy + s * ln), (hx + c * 1.0 + s * 2.2, hy + s * 1.0 - c * 2.2)],
           "thorn", z, normal=(-0.4, -0.6, 0.7))
    r.line(hx + c * 2, hy + s * 2, hx + c * (ln - 1), hy + s * (ln - 1), "bark", z + 0.01, tone=2)
    for f in (0.35, 0.55, 0.75):
        thorn(r, hx + c * ln * f + s * 1.8, hy + s * ln * f - c * 1.8, ang - 50, 2.0, z + 0.03)
    r.dot(hx + c * ln, hy + s * ln, "blood", 3, z + 0.04)


def knight(lean=0.0, bob=0.0, feet=((-3.5, 0.0), (3.5, 0.0)), hand=(6.0, -11.0), hand2=(-5.0, -10.0), sword=-50.0, face="calm",
           smear=None, spark=None, extra=None, knee=1, head_d=(0.0, 0.0), sword_ln=13.0, burst=0):
    r = Rig()
    hip = (0.0, -8.0 + bob)
    T = Xf(lean, hip)
    legs(r, hip, feet, 4.0, 3.8, "rust", rad=(1.6, 1.4), foot="rust", knee=knee, spread=1.6)
    for k, f in enumerate(feet):
        vine(r, [(f[0] - 1.0, f[1] - 1.0), (f[0] + 0.5, f[1] - 3.0), (f[0] - 0.5, f[1] - 5.0)], [0.6], 1.2 * (k * 2 - 1) + 0.05,
             mat="moss", thorns=1, seed=k + 11, tlen=1)
    # far arm
    arm(r, T(-4.6, hip[1] - 8.4), hand2, 3.6, 3.4, "rust", -1.0, rad=(1.5, 1.3, 1.3), bend=1, bias=-0.3)
    # square cuirass split open: bramble bursting out of the seams
    r.poly([T(-5.6, hip[1] - 10.4), T(5.4, hip[1] - 10.4), T(4.6, hip[1] + 0.6), T(-4.8, hip[1] + 0.6)], "rust", 0.0,
           normal=(-0.3, -0.3, 0.9), curve=0.6)
    r.poly([T(-0.8, hip[1] - 10.0), T(1.4, hip[1] - 10.0), T(1.8, hip[1] - 1.0), T(-1.2, hip[1] - 0.6)], "rot", 0.05, normal=(0, 0, 1))
    vine(r, [T(0.2, hip[1] - 9.6), T(-0.8, hip[1] - 6.0), T(0.8, hip[1] - 3.0), T(-0.2, hip[1] - 0.4)], [0.9], 0.1, mat="moss",
         thorns=3, seed=3, tlen=1)
    for side in (-1, 1):
        r.ell(*T(side * 4.8, hip[1] - 9.6), 2.6, 2.0, "rust", 0.2, bias=0.15)
        for k in range(2):
            thorn(r, *T(side * (5.0 + k * 1.2), hip[1] - 11.2 + k * 0.8), -90 + side * (30 + k * 25), 2.0, 0.3)
    r.line(*T(-4.6, hip[1] - 1.0), *T(4.4, hip[1] - 1.0), "bark", 0.15, tone=1)
    hx, hy = T(0.6 + head_d[0], hip[1] - 10.2 + head_d[1])
    r.stamp(KNIGHT_HEAD[face], hx, hy, 0.6, KNIGHT_LEG, pivot=(3, 7))
    # near arm and thorn sword
    el = arm(r, T(4.6, hip[1] - 8.4), hand, 3.6, 3.4, "rust", 2.2, rad=(1.6, 1.4, 1.4), bend=-1)
    vine(r, [T(3.6, hip[1] - 9.6), el, (lerp(el[0], hand[0], 0.6), lerp(el[1], hand[1], 0.6) + 0.8)], [0.6], 2.25, mat="moss",
         thorns=2, seed=9, tlen=1)
    thorn_sword(r, hand[0], hand[1], sword, 2.6, ln=sword_ln)
    r.ell(hand[0], hand[1], 1.3, 1.3, "rust", 2.9, bias=0.15)
    if burst:
        for (x, k) in ((-11.0, 0), (-6.0, 1), (6.0, 1), (11.0, 0)):
            for i in range(3):
                thorn(r, x + i - 1, 0.0, -90 + (i - 1) * 25, 2.0 + burst + k, 5.0)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def knight_sheet(outdir):
    K = knight
    idle = [K(bob=[0, 0.3, 0.6, 0.3][i], sword=-50 + [0, 2, 4, 2][i], hand=(6.0, -11.0 + [0, 0.3, 0.6, 0.3][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(K(lean=6, bob=-0.8 * abs(math.sin(ph)), sword=-35 + 6 * math.sin(ph), hand=(6.5, -10.0),
                     hand2=(-4.5 - 1.5 * math.sin(ph), -9.5), feet=((-3.5 + 3.0 * math.cos(ph), -max(0, 1.6 * math.sin(ph))),
                                                                   (3.5 - 3.0 * math.cos(ph), -max(0, -1.6 * math.sin(ph))))))
    # Sweep (8): winds back (0-1), FIRST SWEEP (2: across the front, tip at (21, -9)), turns the blade (3), SECOND SWEEP up
    # from the floor (4: tip lands at (20, -2), the thorn patch plants at (22, 0)), follow-through (5), recover (6-7)
    sw = [K(lean=-6, sword=-150, hand=(-2.0, -14.0), face="roar"), K(lean=-10, sword=-170, hand=(-4.0, -13.0), face="roar"),
          K(lean=10, sword=-10, hand=(8.0, -10.0), face="roar", smear=[("arc", 4.0, -10.0, 16.0, -150, -10, "thorn", 2)]),
          K(lean=6, sword=40, hand=(6.0, -7.0)),
          K(lean=12, sword=30, hand=(9.0, -6.0), face="roar", sword_ln=13.5, smear=[("arc", 6.0, -6.0, 14.0, 80, 20, "thorn", 2)],
            spark=[(21.0, -1.0, 2)]),
          K(lean=8, sword=-20, hand=(8.0, -11.0)), K(lean=2, sword=-40), K()]
    # Overgrow (8): raises the sword two-handed (0-2), DRIVES it in (3), four thorn patches burst up round him (4), hold (5-6),
    # pulls it out (7)
    og = [K(sword=-80, hand=(4.0, -16.0), hand2=(2.0, -15.0)), K(sword=-90, hand=(3.0, -19.0), hand2=(1.0, -18.0), face="roar", bob=-0.6),
          K(sword=-92, hand=(3.0, -20.0), hand2=(1.0, -19.0), face="roar", bob=-0.8),
          K(sword=90, hand=(4.0, -12.0), hand2=(2.0, -11.0), face="roar", bob=1.2, knee=1, extra=lambda r: soil(r, 4.0, 0.0, 0)),
          K(sword=90, hand=(4.0, -12.0), hand2=(2.0, -11.0), face="roar", bob=1.2, burst=1, extra=lambda r: soil(r, 4.0, 0.0, 1)),
          K(sword=90, hand=(4.0, -12.0), hand2=(2.0, -11.0), bob=1.0, burst=1),
          K(sword=90, hand=(4.0, -12.5), hand2=(2.0, -11.5), bob=0.8), K(sword=-60, hand=(5.0, -12.0))]
    d0 = K(face="roar", lean=-14, sword=-120, hand=(1.0, -15.0))
    d1 = K(face="dead", lean=-28, bob=2.0, sword=150, hand=(-6.0, -6.0), feet=((-3.0, 0.0), (4.0, -1.0)))
    d2 = _knight_corpse(0)
    corpse = _knight_corpse(1)
    knock = K(face="roar", lean=-18, sword=-100, hand=(2.0, -14.0))
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.08] * 6),
             ("Sweep", sw, [0.12, 0.1, 0.05, 0.08, 0.05, 0.1, 0.12, 0.12]),
             ("Overgrow", og, [0.12, 0.12, 0.1, 0.06, 0.1, 0.12, 0.14, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylBrambleKnight", anims, outdir, scale=5)


def _knight_corpse(stage):
    r = Rig()
    r.poly([(-6.0, -6.0), (5.0, -6.0), (5.0, 0.0), (-6.0, 0.0)], "rust", 0.0, curve=0.5)
    vine(r, [(-5.0, -4.0), (0.0, -6.5 - (1 if stage else 0)), (4.0, -4.0)], [0.9], 0.1, mat="moss", thorns=3, seed=5, tlen=1)
    r.stamp(KNIGHT_HEAD["dead"], -9.0, -1.0, 0.4, KNIGHT_LEG, pivot=(3, 7))
    thorn_sword(r, 7.0, -1.0, 0.0, 0.5, ln=12.0)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.4)
    return r.resolve()


# ================================================================== STRANGLER VINE: a serpent of braided vine with a flower mouth
STRANGLE_LEG = {"p": ("bruise", 1), "P": ("bruise", 2), "B": ("bruise", 3), "H": ("bruise", 4), "m": ("chitin", 0),
                "t": ("thorn", 3), "T": ("thorn", 4), "g": ("moss", 2), "G": ("moss", 3), "e": ("glowg", 4)}
STRANGLE_HEAD = {
    # pivot (1, 3): the neck. A bruise-purple flower for a mouth: five petals round a pit ringed with thorn teeth
    "shut": """
..BHB..
.BPHPB.
gPBtBPB
gPmemTP
gPBtBPB
.BPPPB.
..BPB..
""",
    "open": """
.BHB...
BPHPB.t
gPmt...
gPme..T
gPmt...
BPPPB.t
.BPB...
""",
    "dead": """
.......
.......
..pPp..
.pPmPp.
gPmPmP.
.pPPPp.
..pPp..
""",
}


def strangler(phase=0.0, head=None, mouth="shut", lean=0.0, amp=1.0, coil=0.0, lasso=None, smear=None, spark=None, extra=None,
              rise=0.0, tail_x=-9.5):
    r = Rig()
    hx, hy = head or (11.0, -13.0)
    # the body: braided vine laid in an S along the floor, rising to the neck
    pts = []
    n = 12
    for i in range(n + 1):
        t = i / n
        x = lerp(tail_x, hx - 1.5, t)
        floor = t < 0.62
        y = (-1.5 - 1.2 * amp * math.sin(phase + t * 7.0)) if floor else lerp(-2.0, hy + 1.0, (t - 0.62) / 0.38) - rise * math.sin((t - 0.62) / 0.38 * math.pi)
        if floor: x += coil * math.sin(t * 9.0)
        pts.append((x, y))
    rad = [lerp(1.4, 3.2, min(1.0, i / 4.0)) for i in range(n + 1)]
    r.tube(pts, rad, "rot", 0.0, bias=0.05)
    # braid: a second strand wound round the first
    for i in range(0, n, 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r.line(x0, y0 - rad[i] * 0.4 * (1 if i % 2 else -1), x1, y1 + rad[i + 1] * 0.4 * (1 if i % 2 else -1), "moss", 0.1,
               tone=3 if i % 2 else 2)
    vine(r, pts[2:], [0.1], 0.12, mat="moss", thorns=5, seed=4, tlen=1)
    leaf(r, pts[8][0], pts[8][1] - 1.5, -140, 3.0, 0.2)
    r.stamp(STRANGLE_HEAD[mouth], hx, hy, 1.0, STRANGLE_LEG, pivot=(1, 3))
    if lasso:
        kind, a, b, k = lasso
        if kind == "throw":
            r.polyline([(hx + 3, hy), a, b], "moss", 3.0, tone=3)
            ring_(r, b[0], b[1], 2.4, "moss")
        elif kind == "whirl":
            cx, cy = a
            ring_(r, cx, cy, 5.0, "moss", gap=k)
            ang = k * 1.6
            px, py = cx + 5.0 * math.cos(ang), cy + 2.0 * math.sin(ang)
            r.line(hx + 2, hy - 1, px, py, "moss", 3.1, tone=3)
            if b: pod(r, px, py + 2.0, 4.0, 3.2, ripe=1.0)
        elif kind == "sling":
            r.polyline([(hx + 3, hy - 1), a], "moss", 3.0, tone=3)
            if b: pod(r, a[0], a[1] + 2.0, 4.0, 3.2, ripe=1.0)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def ring_(r, cx, cy, rx, mat, gap=None, tone=3, z=3.0):
    for i in range(24):
        a = i / 24 * math.tau
        if gap is not None and abs(((a - gap * 1.6) + math.pi) % math.tau - math.pi) < 0.5: continue
        r.dot(cx + rx * math.cos(a), cy + rx * 0.4 * math.sin(a), mat, tone if math.sin(a) > 0 else tone - 1, z + (0.2 if math.sin(a) > 0 else -4.0))


def strangler_sheet(outdir):
    ST = strangler
    idle = [ST(phase=i * 0.5, head=(11.0, -13.0 + [0, -0.5, -1.0, -0.5][i])) for i in range(4)]
    run = [ST(phase=i / 6 * math.tau, head=(13.0, -12.0 + 0.6 * math.sin(i / 6 * math.tau)), amp=1.4) for i in range(6)]
    # Bite (7): rears back (0-1), LUNGES (2-3: jaws shut at (24, -6), hit box 14 x 12 at (20, -5)), holds (4), coils back (5-6)
    bite = [ST(head=(9.0, -14.0), rise=1.5, mouth="open", coil=0.5), ST(head=(6.0, -16.0), rise=3.0, mouth="open", coil=1.0),
            ST(head=(19.0, -8.0), mouth="open", smear=[("line", [(8, -14), (16, -9)], "moss", 2)]),
            ST(head=(23.0, -6.0), mouth="shut", spark=[(26.0, -6.0, 2)]), ST(head=(21.0, -7.0)), ST(head=(16.0, -9.0)), ST()]
    # Lasso (9): rears (0), CASTS the vine loop out (1-2), CATCHES the pod (3), drags it in and whirls it overhead (4-6: the tell),
    # SLINGS it (7: the pod leaves the loop at (16, -18)), recoils (8)
    la = [ST(head=(9.0, -14.0), rise=1.0, mouth="open"),
          ST(head=(14.0, -12.0), mouth="open", lasso=("throw", (20.0, -10.0), (28.0, -6.0), 0)),
          ST(head=(15.0, -11.0), mouth="open", lasso=("throw", (24.0, -8.0), (34.0, -3.0), 0)),
          ST(head=(14.0, -12.0), mouth="shut", lasso=("throw", (22.0, -6.0), (30.0, -2.0), 0),
             extra=lambda r: pod(r, 30.0, 0.0, 4.0, 3.2)),
          ST(head=(10.0, -14.0), rise=2.0, lasso=("whirl", (9.0, -22.0), True, 0)),
          ST(head=(10.0, -14.5), rise=2.0, lasso=("whirl", (9.0, -22.0), True, 1)),
          ST(head=(10.0, -15.0), rise=2.5, lasso=("whirl", (9.0, -22.0), True, 2)),
          ST(head=(15.0, -12.0), mouth="open", lasso=("sling", (17.0, -19.0), True, 0), smear=[("arc", 9.0, -20.0, 7.0, 180, 340, "moss", 2)]),
          ST(head=(13.0, -11.0))]
    # Lash (7): with no pod near, the loop is cast at the hero instead: rears (0-1), CRACK (3: loop at (30, -8)), recover
    lash = [ST(head=(9.0, -14.0), rise=1.0, mouth="open"), ST(head=(7.0, -15.0), rise=2.0, mouth="open"),
            ST(head=(14.0, -12.0), mouth="open", lasso=("throw", (22.0, -10.0), (28.0, -8.0), 0)),
            ST(head=(15.0, -11.0), mouth="open", lasso=("throw", (24.0, -9.0), (32.0, -8.0), 0), spark=[(32.0, -8.0, 1)]),
            ST(head=(14.0, -11.0), lasso=("throw", (20.0, -8.0), (24.0, -4.0), 0)), ST(head=(13.0, -11.0)), ST()]
    d0 = ST(head=(8.0, -15.0), rise=2.0, mouth="open")
    d1 = ST(head=(14.0, -5.0), mouth="dead", amp=0.6)
    d2 = ST(head=(14.0, -2.5), mouth="dead", amp=0.4, extra=lambda r: dust_puff(r, 6.0, 0, 1, 1.4))
    corpse = ST(head=(14.0, -2.0), mouth="dead", amp=0.3)
    knock = ST(head=(8.0, -14.0), rise=1.5, mouth="open", amp=1.6)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Bite", bite, [0.12, 0.1, 0.05, 0.06, 0.1, 0.1, 0.12]),
             ("Lasso", la, [0.1, 0.06, 0.06, 0.1, 0.1, 0.1, 0.1, 0.06, 0.12]),
             ("Lash", lash, [0.1, 0.1, 0.05, 0.08, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylStrangler", anims, outdir, scale=5)


# ================================================================== GALL WASP: a lean wasp with a gall on its back and a needle
WASP_LEG = {"k": ("chitin", 0), "c": ("chitin", 2), "C": ("chitin", 3), "y": ("pollen", 2), "Y": ("pollen", 3), "e": ("eye", 3),
            "E": ("eye", 4), "m": ("chitin", 0)}
WASP_HEAD = {
    # pivot (0, 2): the neck. A narrow head, big dark eyes with a red glint, mandibles
    "calm": """
.cCy.
cCEcy
ckccY
.kck.
..k.k
""",
    "dead": """
.cCy.
cCmcy
ckccY
.kck.
""",
}


def gall_wasp(alt=6.0, flap=0.0, lean=0.0, sting=0.0, face="calm", legs_k=0.0, stretch=1.0, smear=None, spark=None, extra=None,
              gall_s=1.0, needle=None):
    r = Rig()
    oy = -alt
    T = Xf(lean, (0.0, oy - 5.0))
    # abdomen: a long striped segment that curls under to the needle (sting = 0 level .. 1 curled forward)
    ab0 = T(-2.0, oy - 5.0)
    a1 = 180 - sting * 50
    pts = chain(ab0[0], ab0[1], [(3.6 * stretch, a1 - lean), (3.4 * stretch, a1 - lean - 20 - sting * 50), (3.0, a1 - lean - 40 - sting * 80)])
    r.tube(pts, [2.6, 2.9, 2.2, 1.2], "chitin", 0.0, bias=0.05)
    for i in range(1, len(pts) - 1):
        r.ell(pts[i][0], pts[i][1], 0.9, 2.3, "pollen", 0.05, ang=a1 - lean, bias=0.0)
    nx, ny = pts[-1]
    na = math.radians(a1 - lean - 40 - sting * 80)
    tip = (nx + 4.0 * math.cos(na), ny + 4.0 * math.sin(na))
    r.line(nx, ny, *tip, "thorn", 0.1, tone=3)
    # thorax with the lumpy gall on its back, wings, thin legs
    tx, ty = T(1.4, oy - 6.0)
    r.ell(tx, ty, 2.8, 2.4, "chitin", 0.4, bias=0.1)
    gx, gy = T(0.2, oy - 8.6)
    r.ell(gx, gy, 3.0 * gall_s, 2.6 * gall_s, "gall", 0.6, bias=0.15)
    for (dx, dy) in ((-1.0, -1.0), (1.2, -0.6), (0.0, 0.8)):
        r.ell(gx + dx * gall_s, gy + dy * gall_s, 1.0, 0.9, "gall", 0.62, bias=0.3)
    for k, (a0, z) in enumerate(((-150 + flap, -1.0), (-120 + flap * 0.8, 1.4))):
        wing(r, (tx - 0.4, ty - 1.6), a0, 9.5 - k, 2.8, z, veins=2, tone=2 if k == 0 else 3)
    for k in range(3):
        sx, sy = T(0.6 + k * 1.1, oy - 4.6)
        a = 95 + k * 10 + 12 * math.sin(legs_k + k)
        r.polyline(chain(sx, sy, [(2.0, a), (2.0, a + 25)]), "chitin", -0.4 if k % 2 else 0.8, tone=1 if k % 2 else 2)
    hx, hy = T(4.2, oy - 6.6)
    r.stamp(WASP_HEAD[face], hx, hy, 1.0, WASP_LEG, pivot=(0, 2))
    if needle:
        r.line(*needle[0], *needle[1], "thorn", 5.0, tone=4)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve(), tip


def wasp_sheet(outdir):
    def G(**k):
        return gall_wasp(**k)[0]
    idle = [G(alt=5.0 + [0, 0.5, 1.0, 0.5][i], flap=[0, 50, 15, 50][i], legs_k=i) for i in range(4)]
    run = [G(alt=5.0 + 0.5 * math.sin(i / 6 * math.tau), flap=[0, 50, 15, 50, 0, 50][i], lean=10, legs_k=i * 0.8) for i in range(6)]
    # Needle (6): curls its abdomen forward under itself (0-1), FIRES (2: needle leaves the tip at (8, -5)), streak, recover
    nd = [G(sting=0.5, flap=30, lean=-6), G(sting=1.0, flap=0, lean=-10),
          G(sting=1.1, flap=50, lean=-4, needle=((9.0, -5.0), (13.0, -4.0)), smear=[("line", [(5, -4), (9, -4)], "thorn", 2)]),
          G(sting=0.8, flap=10), G(sting=0.3, flap=40), G()]
    # Dart (7): rears (0-1), DARTS forward (2-4: stretched, smeared; seeds drop at 2 and 4), brakes (5-6)
    dt = [G(lean=-14, flap=40, alt=6.0), G(lean=-20, flap=0, alt=6.5, sting=0.3),
          G(lean=18, flap=60, stretch=1.3, smear=[("line", [(-12, -10), (-4, -10)], "pollen", 2), ("line", [(-12, -7), (-5, -7)], "chitin", 2)]),
          G(lean=20, flap=10, stretch=1.35, smear=[("line", [(-14, -10), (-4, -10)], "pollen", 2)]),
          G(lean=16, flap=60, stretch=1.2, smear=[("line", [(-10, -9), (-4, -9)], "pollen", 1)]),
          G(lean=-12, flap=20), G(lean=-4, flap=40)]
    d0 = G(lean=-30, flap=70, face="dead")
    d1 = G(lean=-70, alt=2.0, flap=100, face="dead", sting=0.8)
    d2 = _wasp_corpse(0)
    corpse = _wasp_corpse(1)
    knock = G(lean=-30, flap=60, alt=5.5)
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6),
             ("Needle", nd, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1]),
             ("Dart", dt, [0.12, 0.1, 0.06, 0.06, 0.06, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("SylGallWasp", anims, outdir, scale=5)


def _wasp_corpse(stage):
    r = Rig()
    r.tube([(-10.0, -1.6), (-6.0, -2.0), (-2.0, -2.4)], [1.2, 2.0, 1.8], "chitin", 0.0)
    for x in (-7.0, -4.5): r.ell(x, -2.2, 0.7, 1.6, "pollen", 0.05)
    r.ell(1.0, -2.6, 2.4, 2.0, "chitin", 0.2)
    r.ell(0.0, -5.0 + (1 if stage else 0), 2.6, 2.2, "gall", 0.3, bias=0.1)
    r.stamp(WASP_HEAD["dead"], 4.0, -1.0, 0.4, WASP_LEG, pivot=(0, 2))
    wing(r, (0.0, -3.0), -170, 7.0, 2.0, -0.4, veins=2, tone=2)
    for k in range(3): r.polyline([(0.0 + k, -1.0), (1.0 + k * 1.5, -4.5 - (k % 2))], "chitin", 0.5, tone=1)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.2)
    return r.resolve()


# ================================================================== BLOATFLY: a fat fly whose belly sloshes with bile
BLOAT_LEG = {"e": ("rot", 2), "E": ("rot", 3), "W": ("mould", 4), "m": ("chitin", 0), "k": ("chitin", 1), "c": ("chitin", 2),
             "b": ("bile", 3), "B": ("bile", 4)}
BLOAT_HEAD = {
    # pivot (1, 3): the neck. Big cloudy eyes over a wide, drooling mouth
    "calm": """
.EEe..
EWEeee
eEEeek
.kcckk
.kbbk.
..b...
""",
    "retch": """
.EEe..
EWEeee
eEEeek
.kmmbk
.kbBBk
..bBb.
""",
    "dead": """
.eee..
emeeek
eeemek
.kccck
..kk..
""",
}


def bloatfly(alt=8.0, flap=0.0, lean=0.0, slosh=0.0, face="calm", belly=1.0, head_d=(0.0, 0.0), legs_k=0.0, gobs=(), stream=None,
             smear=None, extra=None):
    r = Rig()
    oy = -alt
    T = Xf(lean, (0.0, oy - 7.0))
    for k in range(3):
        sx, sy = T(1.0 + k * 1.4, oy - 4.0)
        a = 95 + k * 10 + 10 * math.sin(legs_k + k)
        r.tube(chain(sx, sy, [(2.4, a), (2.0, a + 25)]), [0.6, 0.5], "chitin", -0.4 if k % 2 else 0.8, flat=1 if k % 2 else 2)
    # the belly: a huge bile-green sac, a darker slosh line, bruise-purple bands
    bx, by = T(-2.0, oy - 7.0)
    r.ell(bx, by, 7.2 * belly, 6.8 * belly, "bile", 0.0, bias=0.05)
    lvl = by - 0.5 + slosh
    r.ell(bx, by + 1.0, 6.4 * belly, 4.6 * belly, "bile", 0.02, bias=-0.35, clip=lambda x, y: y >= lvl + 0.6 * math.sin(x * 0.7 + slosh))
    for k in (-2.6, 0.6, 3.8):
        r.ell(bx + k * belly, by - 0.2, 0.7, 5.8 * belly, "bruise", 0.05, bias=0.0, clip=lambda x, y: True)
    r.ell(bx - 2.4, by - 3.0, 1.6, 1.0, "bile", 0.1, bias=0.6)
    tx, ty = T(4.4, oy - 9.0)
    r.ell(tx, ty, 3.0, 2.8, "chitin", 0.5, bias=0.1)
    # tiny wings working hard
    for k, (a0, z) in enumerate(((-125 + flap, -1.0), (-100 + flap * 0.8, 1.4))):
        wing(r, (tx - 0.6, ty - 2.0), a0, 6.0 - k, 2.4, z, veins=1, tone=2 if k == 0 else 3)
    hx, hy = T(7.4 + head_d[0], oy - 9.0 + head_d[1])
    r.stamp(BLOAT_HEAD[face], hx, hy, 1.5, BLOAT_LEG, pivot=(1, 3))
    for (gx, gy, s) in gobs:
        r.ell(gx, gy, s, s * 0.9, "bilef", 4.0, flat=3); r.dot(gx - 0.5, gy - 0.5, "bilef", 4, 4.1)
    if stream:
        x, y0, k = stream
        for y in range(int(y0), 1):
            w = 1 + (1 if (y + k) % 4 < 2 else 0)
            for dx in range(-w + 1, w):
                r.dot(x + dx + (1 if (y + k) % 5 == 0 else 0), y, "bilef", 3 if dx == 0 else 2, 4.0)
        for side in (-1, 1):
            r.dot(x + side * (2 + k % 2), -1, "bilef", 4, 4.1); r.dot(x + side * 3, -2 - k % 2, "bilef", 3, 4.1)
    smears(r, smear)
    if extra: extra(r)
    return r.resolve()


def bloat_sheet(outdir):
    B = bloatfly
    idle = [B(alt=8.0 + [0, 0.5, 1.0, 0.5][i], flap=[0, 45, 10, 45][i], slosh=[0, 0.6, 1.0, 0.6][i], legs_k=i,
              belly=[1.0, 1.02, 1.04, 1.02][i]) for i in range(4)]
    run = [B(alt=8.0 + 0.6 * math.sin(i / 6 * math.tau), flap=[0, 45, 10, 45, 0, 45][i], lean=8, slosh=-0.8 + 0.5 * math.sin(i),
             legs_k=i * 0.7) for i in range(6)]
    # Retch (7): heaves (0-1), RETCHES three gobs (2: they leave the mouth at (10, -14)), the gobs fly (3), recover (4-6)
    rt = [B(lean=-8, belly=1.06, slosh=1.0, face="retch"), B(lean=-14, belly=1.1, slosh=1.4, face="retch", head_d=(-0.5, -0.5)),
          B(lean=12, belly=0.94, slosh=-1.0, face="retch", head_d=(1.0, 0.5), gobs=[(11.0, -13.0, 1.2), (12.0, -15.5, 1.0), (12.0, -10.5, 1.0)]),
          B(lean=10, belly=0.95, slosh=-0.6, face="retch", gobs=[(15.0, -13.0, 1.0), (15.0, -17.0, 0.9), (15.0, -9.0, 0.9)]),
          B(lean=6, slosh=0.4), B(lean=2, slosh=0.8), B()]
    # Rain (10): climbs and tips nose-down over the hero (0-1), RETCHES STRAIGHT DOWN for 1.5 s (2-7: the stream falls from the
    # mouth at (8, -13) to the floor at (8, 0)), shakes off (8-9)
    rain = [B(alt=10.0, lean=-10, flap=40, face="retch"), B(alt=11.0, lean=30, flap=0, face="retch", head_d=(0.0, 1.5))]
    for k in range(6):
        rain.append(B(alt=10.5 + 0.4 * (k % 2), lean=38, flap=[45, 10][k % 2], face="retch", belly=1.0 - 0.02 * k, slosh=-1.0 + 0.3 * k,
                      head_d=(0.0, 2.0), stream=(8.0, -11.0, k)))
    rain += [B(alt=9.5, lean=10, flap=40, belly=0.88), B(alt=8.5, lean=0, flap=10, belly=0.94)]
    d0 = B(face="retch", lean=-24, flap=60)
    d1 = B(face="dead", lean=-50, alt=3.0, flap=90, belly=0.95)
    d2 = _bloat_corpse(0)
    corpse = _bloat_corpse(1)
    knock = B(face="retch", lean=-26, flap=50, alt=8.5)
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6),
             ("Retch", rt, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1, 0.1]),
             ("Rain", rain, [0.12, 0.12] + [0.25] * 6 + [0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("SylBloatfly", anims, outdir, scale=5)


def _bloat_corpse(stage):
    r = Rig()
    r.ell(-1.0, -3.6, 6.4, 3.6, "bile", 0.0)
    for k in (-2.0, 1.0, 4.0): r.ell(-1.0 + k, -3.6, 0.6, 3.0, "bruise", 0.05)
    r.ell(6.0, -2.4, 2.4, 2.2, "chitin", 0.3)
    r.stamp(BLOAT_HEAD["dead"], 9.0, -1.0, 0.5, BLOAT_LEG, pivot=(1, 3))
    wing(r, (4.0, -4.0), -160, 6.0, 2.2, -0.5, veins=1, tone=2)
    for x in (-6.0, -3.0, 2.0, 5.0): r.dot(x, 0.0 - (stage == 0), "bilef", 3, 0.6)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.4)
    return r.resolve()


JOBS = [("SylSporeHusk", husk_sheet), ("SylBloomWitch", witch_sheet), ("SylBrambleKnight", knight_sheet),
        ("SylStrangler", strangler_sheet), ("SylGallWasp", wasp_sheet), ("SylBloatfly", bloat_sheet)]

SYNC = {
    "SylSporeHusk": {"Smash": [("SLAM: club head lands at (17, -1); the floor rings (Shake the Tree)", 3)],
                     "Belch": [("BELCH: the spore cone leaves the mouth at (9, -14)", 3)]},
    "SylBloomWitch": {"Lance": [("lance leaves the palm at (9, -15)", 2)], "Graft": [("GRAFT: the pod swells over her palms", 4)]},
    "SylBrambleKnight": {"Sweep": [("FIRST SWEEP across the front: tip (21, -9)", 2),
                                   ("SECOND SWEEP up from the floor: tip (20, -2); thorn patch at (22, 0)", 4)],
                         "Overgrow": [("DRIVES the sword in at (4, 0)", 3), ("four thorn patches burst up", 4)]},
    "SylStrangler": {"Bite": [("JAWS SHUT at (24, -6)", 3)], "Lasso": [("CATCHES the pod", 3), ("whirl (the tell)", 4),
                                                                      ("SLING: the pod leaves the loop at (17, -19)", 7)],
                     "Lash": [("CRACK: loop at (32, -8)", 3)]},
    "SylGallWasp": {"Needle": [("needle leaves the tip at (9, -5)", 2)], "Dart": [("DART starts (seed 1)", 2), ("seed 2", 4)]},
    "SylBloatfly": {"Retch": [("gobs leave the mouth at (10, -14)", 2)], "Rain": [("STREAM starts: falls from (8, -11) to (8, 0)", 2),
                                                                                  ("stream ends", 8)]},
}
NOTES = {"SylStrangler": "Lasso is the special when a seed or pod lies within 50 px; Lash replaces it when none does."}
