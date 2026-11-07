"""Jinx tier 3 (besides the Roulette Ouroboros, Grand Jester and High Roller in jinx_v2_rigs.py): Gorgon, Card King, House of Cards,
Natural Twenty, Nutcracker, Puppeteer, the Oracle (and her prophecy ghost), One-Armed Bandit, Big-Top Chimera.
Built through jinx_v2_rigs.py. T3 idle limit 42 x 40."""
import math, os
from PIL import Image
from jinx_v2_rigs import (Rig, Xf, chain, ik, lerp, lerp_pt, die3, box3, card, harl, star, arc_smear, dust_puff, sheet,
                          tail_anims, rot3, lam, poly_px, RAMPS, BUILT, SprRGB, pack, preview)
from jinx_v2_t2 import smears, sparks, spade, band_mat
from jinx_v2_t1 import confetti


def legs2(r, hip, feet, l1, l2, mats, z=(-1.0, 1.2), rad=(1.3, 1.1), knee=1, boots=None, spread=0.9):
    for k, f in enumerate(feet):
        hp = (hip[0] + (-spread if k == 0 else spread), hip[1] + 0.4)
        kn = ik(hp[0], hp[1], f[0], f[1] - 1.0, l1, l2, bend=-knee)
        zz = z[k]
        b = -0.3 if k == 0 else 0.0
        r.tube([hp, kn], [rad[0], rad[1]], mats[0], zz, bias=b)
        r.tube([kn, (f[0], f[1] - 1.0)], [rad[1], rad[1] * 0.9], mats[1], zz + 0.01, bias=b + 0.1)
        if boots:
            r.poly([(f[0] - 1.4, f[1] - 2.0), (f[0] + 2.6, f[1] - 1.2), (f[0] + 2.6, f[1]), (f[0] - 1.4, f[1])], boots, zz + 0.02,
                   bias=b + 0.2)


def recolor(s, mat, keep_alpha_every=None):
    """A ghost copy: every pixel mapped tone-for-tone onto one ramp (used for the Oracle's prophecy)."""
    px = {}
    for k, (m, t) in s.tones.items():
        if keep_alpha_every and (k[0] + k[1]) % keep_alpha_every == 0 and t < 3: continue
        px[k] = RAMPS[mat][max(1, min(4, t + 1))]
    out = SprRGB(px); out.tones = {k: (mat, 2) for k in px}
    return out


# ================================================================== GORGON
GORG_LEG = {"a": ("ivory", 1), "w": ("ivory", 2), "W": ("ivory", 3), "X": ("ivory", 4), "m": ("blk", 0), "j": ("jade", 1),
            "J": ("jade", 3), "e": ("eye", 2), "E": ("eye", 4), "n": ("crim", 1), "C": ("crim", 3), "g": ("gold", 3)}
GORG_HEAD = {
    # pivot (3, 7): the neck. Bone-ivory face, jade lids, eyes that are two red one-pip dice
    "calm": """
.jJJJj.
jJJJJJj
aWWWWWa
aWwWwWw
aWeWWeW
.wWWWWa
..wnna.
...aa..
""",
    "kindle": """
.jJJJj.
jJJJJJj
aWWWWWa
aWwWwWw
aWEWWEW
.wWWWWa
..wnna.
...aa..
""",
    "hiss": """
.jJJJj.
jJJJJJj
aWWWWWa
aWwWwWw
aWeWWeW
.wWmmWa
..wmma.
...aa..
""",
    "dead": """
.jJJJj.
jJJJJJj
aWWWWWa
aWmWmWw
aWWmWmW
.wWWWWa
..wnna.
...aa..
""",
}


def hair_snake(r, root, ang, ln, z, strike=0.0, eye="eye"):
    """One hair snake from the scalp: an S-ish tube, jade and crimson bands, a little head with a red pip eye."""
    pts = chain(root[0], root[1], [(ln * 0.4, ang - 25 + strike * 10), (ln * 0.35, ang + 20 - strike * 25), (ln * 0.3, ang - 10 - strike * 10)])
    r.tube(pts, [1.1, 0.9, 0.8, 0.7], band_mat(2.2), z, bias=0.05)
    hx, hy = pts[-1]
    a = math.radians(ang - 10 - strike * 10)
    r.ell(hx + 0.8 * math.cos(a), hy + 0.8 * math.sin(a), 1.4, 1.1, "jade", z + 0.01, ang=math.degrees(a), bias=0.1)
    r.dot(hx + 0.6 * math.cos(a), hy + 0.6 * math.sin(a) - 0.6, eye, 3, z + 0.02)
    return pts[-1]


def gorgon(coil=0.0, lean=0.0, bob=0.0, hand=(7.0, -18.0), hand2=(-6.0, -17.0), face="calm", hair=(), fan=1.0,
           eyes_glow=False, beam=None, smear=None, spark=None, extra=None, tail_flick=0.0):
    r = Rig()
    base = (0.0, -3.0)
    # the serpent tail: a coil on the floor and up into the hips
    pts = [(-12.0 + tail_flick, -4.0 - tail_flick * 0.3), (-9.0, -1.6), (-3.0, -1.4), (3.0, -2.0 + coil * 0.3), (5.0, -5.0),
           (2.0, -8.0 + bob), (0.0, -11.0 + bob)]
    r.tube(pts, [0.6, 1.6, 2.6, 3.0, 3.2, 3.0, 2.8], band_mat(3.0), 0.0, bias=0.05)
    for i in range(1, 5):
        x0, y0 = pts[i]
        r.dot(x0, y0 + 1.6, "belly", 2, 0.05)
    hip = (0.0, -11.5 + bob)
    T = Xf(lean, hip)
    sh_n, sh_f = T(hip[0] + 2.6, hip[1] - 7.0), T(hip[0] - 2.4, hip[1] - 7.0)
    neck = T(hip[0] + 0.4, hip[1] - 8.2)
    # far arm
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 4.0, 3.8, bend=1)
    r.tube([sh_f, e2, hand2], [1.1, 0.9, 0.8], "ivory", -0.6, bias=-0.35)
    r.dot(*e2, "gold", 2, -0.55)
    # torso: jade bodice with a crimson sash and gold clasp
    tor = [T(hip[0] - 3.0, hip[1] + 0.8), T(hip[0] + 3.0, hip[1] + 0.8), T(hip[0] + 3.2, hip[1] - 7.4), T(hip[0] - 2.8, hip[1] - 7.4)]
    r.poly(tor, "jade", 0.2, curve=0.8)
    r.poly([T(hip[0] - 3.0, hip[1] - 1.0), T(hip[0] + 3.0, hip[1] - 2.6), T(hip[0] + 3.0, hip[1] - 1.0), T(hip[0] - 3.0, hip[1] + 0.6)], "crim", 0.3)
    r.dot(*T(hip[0] + 0.5, hip[1] - 1.6), "gold", 4, 0.35)
    r.ell(*T(hip[0] + 0.4, hip[1] - 7.0), 2.4, 1.0, "ivory", 0.25)
    # hair snakes behind the head (fanned), then the head, then those in front
    hx, hy = neck[0], neck[1] - 0.3
    scalp = (hx, hy - 6.0)
    specs = hair or [(-150, 9.0), (-125, 10.0), (-100, 9.5), (-75, 10.0), (-50, 9.0), (-20, 8.0)]
    for i, (a, ln, *rest) in enumerate(specs):
        st = rest[0] if rest else 0.0
        a2 = -90 + (a + 90) * fan
        hair_snake(r, (scalp[0] + (i - 2.5) * 0.8, scalp[1] + 1.0), a2, ln, 1.0 + (0.1 if i % 2 else -1.6), strike=st,
                   eye="fire" if eyes_glow else "eye")
    r.stamp(GORG_HEAD[face], hx, hy, 2.0, GORG_LEG, pivot=(3, 7))
    if eyes_glow:
        r.dots([(hx - 1, hy - 3.5), (hx + 2, hy - 3.5)], "eye", 4, 2.1)
        for (dx, dy) in ((-2, -5), (3, -5), (-2, -2), (3, -2)):
            r.dot(hx + dx + 0.5, hy - 3.5 + dy * 0.5, "fire", 3, 2.1)
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 4.0, 3.8, bend=1)
    r.tube([sh_n, e1, hand], [1.2, 1.0, 0.9], "ivory", 3.0, bias=0.05)
    r.dot(*e1, "gold", 3, 3.05)
    if beam:
        (bx0, by0), ln, k = beam
        for i in range(int(ln)):
            r.dot(bx0 + i, by0, "jade" if k == 1 else "glow", 4 if i % 3 else 3, 6.0)
            r.dot(bx0 + i, by0 - 1, "jade", 3, 5.9)
            r.dot(bx0 + i, by0 + 1, "jade", 2, 5.9)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def gorgon_sheet(outdir):
    G = gorgon
    idle = [G(bob=[0, -0.5, -1, -0.5][i], hair=[(a + 6 * math.sin(i * 1.6 + k), l) for k, (a, l) in
                                               enumerate([(-150, 9.0), (-125, 10.0), (-100, 9.5), (-75, 10.0), (-50, 9.0), (-20, 8.0)])],
              hand=(7.0, -18.0 + [0, -0.5, -1, -0.5][i]), tail_flick=[0, 1, 2, 1][i]) for i in range(4)]
    run = [G(lean=10, bob=-0.6 * abs(math.sin(i / 6 * math.tau)), coil=1.5 * math.sin(i / 6 * math.tau), fan=0.8,
             hair=[(a - 12 + 5 * math.sin(i + k), l) for k, (a, l) in enumerate([(-150, 9.0), (-125, 10.0), (-100, 9.5), (-75, 10.0), (-50, 9.0), (-20, 8.0)])],
             tail_flick=2 * math.sin(i / 6 * math.tau)) for i in range(6)]
    # Lash: the snakes draw back (0-1), lunge forward in a fan (2 smear, 3 HIT heads x 7..25, y -24..-8), recoil (4-6)
    back = [(-170, 8.0), (-150, 9.0), (-130, 9.0), (-110, 9.0), (-90, 8.0), (-70, 7.0)]
    fwd = [(-40, 11.0, 1.0), (-25, 13.0, 1.0), (-10, 13.0, 1.0), (5, 12.0, 1.0), (15, 10.0, 1.0), (25, 9.0, 1.0)]
    lash = [G(hair=back, face="hiss", lean=-4), G(hair=[(a - 10, l) for a, l in back], face="hiss", lean=-8),
            G(hair=[(a * 0.5 - 30, l + 1) for a, l in back], face="hiss", lean=6, smear=[("arc", 2.0, -26.0, 14.0, -120, 10, "jade", 2)]),
            G(hair=fwd, face="hiss", lean=12, spark=[(23.0, -18.0, 2), (21.0, -10.0, 2)]),
            G(hair=[(a - 20, l - 1, 0.5) for a, l, s in fwd], face="hiss", lean=8),
            G(hair=[(a - 50, l - 2) for a, l, s in fwd], lean=3), G()]
    # Stare: the hair fans wide (0-1), her eyes KINDLE (2-3: the warning), the beam fires (4-5), holds (6), fades (7)
    stare = [G(fan=1.3, face="calm"), G(fan=1.5, face="kindle", lean=-3), G(fan=1.6, face="kindle", eyes_glow=True, lean=-4),
             G(fan=1.6, face="kindle", eyes_glow=True, lean=-4, spark=[(1.0, -34.0, 2), (4.0, -34.0, 2)]),
             G(fan=1.6, face="kindle", eyes_glow=True, lean=2, beam=((5.0, -30.0), 18, 1)),
             G(fan=1.5, face="kindle", eyes_glow=True, lean=2, beam=((5.0, -30.0), 14, 2)),
             G(fan=1.3, face="calm", lean=1), G(fan=1.0)]
    d0 = G(face="dead", lean=-12, fan=1.4, hand=(3.0, -24.0), hand2=(-8.0, -22.0))
    d1 = G(face="dead", lean=-35, bob=4.0, fan=0.6, hand=(-1.0, -14.0), hand2=(-10.0, -10.0))
    d2 = _gorgon_corpse(0)
    corpse = _gorgon_corpse(1)
    knock = G(face="hiss", lean=-16, fan=1.3, hand=(3.0, -22.0), hand2=(-8.0, -21.0))
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Lash", lash, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Stare", stare, [0.12, 0.12, 0.2, 0.2, 0.08, 0.12, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxGorgon", anims, outdir, scale=4)


def _gorgon_corpse(stage):
    r = Rig()
    pts = [(14.0, -1.0), (8.0, -2.0), (2.0, -1.6), (-4.0, -2.4)]
    r.tube(pts, [0.8, 2.4, 2.8, 3.0], band_mat(3.0), 0.0)
    r.poly([(-10.0, -0.6), (-3.0, -0.6), (-3.0, -5.0), (-10.0, -4.4)], "jade", 0.5)
    r.stamp(GORG_HEAD["dead"], -13.0, 0.0, 1.5, GORG_LEG, pivot=(3, 7))
    for i, a in enumerate((-170, -150, 160, 140, -190)):
        hair_snake(r, (-15.0, -3.5), a if stage else a + 15, 6.0, 1.0 + i * 0.01, eye="blk")
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.6)
    return r.resolve()


# ================================================================== CARD KING
KING_LEG = {"a": ("flesh", 1), "w": ("flesh", 2), "W": ("flesh", 3), "m": ("blk", 0), "g": ("gold", 2), "G": ("gold", 4),
            "z": ("gold", 1), "r": ("crim", 3), "n": ("crim", 1), "i": ("ivory", 3), "I": ("ivory", 4), "e": ("eye", 3),
            "f": ("fire", 4)}
KING_HEAD = {
    # pivot (4, 8): the neck. A three-point crown, a stern face and a forked ivory beard
    "stern": """
g..G..g..
gzgGgzg..
gGgGgGg..
.awWWWwa.
awmWWmWw.
.wWWWWWa.
.iIiiIi..
..iI.Ii..
..i...i..
""",
    "roar": """
g..G..g..
gzgGgzg..
gGgGgGg..
.awWWWwa.
awmWWmWw.
.wWmmmWa.
.iImnmi..
..iI.Ii..
..i...i..
""",
    "glow": """
f..f..f..
gfgfgfg..
gGgGgGg..
.awWWWwa.
awmWWmWw.
.wWWWWWa.
.iIiiIi..
..iI.Ii..
..i...i..
""",
    "dead": """
.........
.g..G..g.
gzgGgzg..
.awWWWwa.
awmWWmWw.
.wWWmWWa.
.iIiiIi..
..iI.Ii..
..i...i..
""",
}


def club_pip(r, cx, cy, s, mat, z):
    for (dx, dy) in ((0, -0.7), (-0.75, 0.2), (0.75, 0.2)):
        r.ell(cx + dx * s, cy + dy * s, 0.6 * s, 0.6 * s, mat, z)
    r.poly([(cx - 0.3 * s, cy), (cx + 0.3 * s, cy), (cx + 0.6 * s, cy + 1.2 * s), (cx - 0.6 * s, cy + 1.2 * s)], mat, z)


def mace(r, hx, hy, ang, z, ln=11.0):
    a = math.radians(ang)
    tx, ty = hx + ln * math.cos(a), hy + ln * math.sin(a)
    r.tube([(hx - 2 * math.cos(a), hy - 2 * math.sin(a)), (tx, ty)], [0.8, 0.9], "wood", z)
    # a club-shaped iron head with gold studs
    for (dx, dy) in ((0.0, 0.0), (1.6, 1.0), (-1.6, 1.0)):
        q = Xf(ang + 90, (tx, ty))(tx + dx, ty + dy - 1.0)
        r.ell(q[0], q[1], 1.8, 1.8, "blk", z + 0.01, bias=0.15)
    r.dot(tx + 1.2 * math.cos(a), ty + 1.2 * math.sin(a) - 1, "gold", 4, z + 0.02)
    return tx, ty


def king(lean=0.0, bob=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), hand=(10.0, -14.0), hand2=(-9.0, -13.0), mace_ang=-60.0,
         face="stern", court=None, smear=None, spark=None, dust=None, extra=None, squash=0.0):
    """court: (x, y, tilt) of the raised Diamonds card held in front with the far hand."""
    r = Rig()
    hip = (0.0, -6.0 + bob)
    T = Xf(lean, hip)
    legs2(r, hip, feet, 3.0, 3.0, ("crim", "blk"), rad=(1.6, 1.3), boots="blk", spread=2.4)
    cx, cy = T(hip[0], hip[1] - 9.0 + squash)
    # robe: crimson with ermine trim behind the card body
    r.poly([T(hip[0] - 9.0, hip[1] + 1.0), T(hip[0] + 8.0, hip[1] + 1.0), T(hip[0] + 6.6, hip[1] - 17.0), T(hip[0] - 7.6, hip[1] - 17.0)],
           "crim", -0.5, curve=0.7)
    for i in range(9):
        x = lerp(-8.6, 7.6, i / 8.0)
        r.dot(*T(hip[0] + x, hip[1] + 0.6), "ivory", 3 if i % 2 else 2, -0.45)
        if i % 3 == 1: r.dot(*T(hip[0] + x, hip[1] + 0.6), "blk", 0, -0.44)
    # the King of Clubs card: his body
    card(r, cx, cy, 13.0, 18.0, z=0.0, ang=lean, lit=0.1)
    Tc = Xf(lean, (cx, cy))
    club_pip(r, *Tc(cx - 0.4, cy - 1.4), 2.6, "blk", 0.1)
    r.polyline([Tc(cx - 5.4, cy - 7.6), Tc(cx - 5.4, cy - 5.0)], "crim", 0.1, tone=1)   # the K
    r.polyline([Tc(cx - 5.4, cy - 6.2), Tc(cx - 4.0, cy - 7.6)], "crim", 0.1, tone=1)
    r.polyline([Tc(cx - 5.4, cy - 6.2), Tc(cx - 4.0, cy - 5.0)], "crim", 0.1, tone=1)
    club_pip(r, *Tc(cx + 4.6, cy + 6.2), 0.9, "blk", 0.1)
    # head
    hx, hy = T(hip[0] + 0.8, hip[1] - 17.4 + squash)
    r.stamp(KING_HEAD[face], hx, hy, 2.0, KING_LEG, pivot=(4, 8))
    # shoulders: ermine
    for side in (-1, 1):
        r.ell(*T(hip[0] + side * 5.8, hip[1] - 17.0 + squash), 2.4, 1.6, "ivory", 1.0 + (0.3 if side > 0 else -0.8), bias=0.1)
    sh_n, sh_f = T(hip[0] + 6.2, hip[1] - 15.6 + squash), T(hip[0] - 6.0, hip[1] - 15.6 + squash)
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 4.0, 4.0, bend=1)
    r.tube([sh_f, e2, hand2], [1.6, 1.4, 1.2], "crim", -0.8 if court is None else 3.6, bias=-0.3 if court is None else 0.0)
    r.ell(hand2[0], hand2[1], 1.3, 1.3, "flesh", -0.75 if court is None else 3.65)
    if court:
        x, y, a = court
        card(r, x, y, 9.0, 12.0, z=4.0, ang=a, lit=0.15)
        Tq = Xf(a, (x, y))
        r.poly([Tq(x, y - 4.0), Tq(x + 3.0, y), Tq(x, y + 4.0), Tq(x - 3.0, y)], "rdie", 4.05, normal=(-0.3, -0.3, 1.0))
        r.polyline([Tq(x - 3.6, y - 5.2), Tq(x + 3.6, y - 5.2), Tq(x + 3.6, y + 5.2), Tq(x - 3.6, y + 5.2), Tq(x - 3.6, y - 5.2)],
                   "gold", 4.06, tone=3)
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 4.0, 4.0, bend=1)
    r.tube([sh_n, e1, hand], [1.7, 1.5, 1.3], "crim", 3.0, bias=0.05)
    mace(r, hand[0], hand[1], mace_ang, 3.2)
    r.ell(hand[0], hand[1], 1.4, 1.4, "flesh", 3.3, bias=0.1)
    smears(r, smear); sparks(r, spark)
    if dust: dust_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def king_sheet(outdir):
    K = king
    idle = [K(bob=[0, 0.4, 0.8, 0.4][i], hand=(10.0, -14.0 + [0, 0.4, 0.8, 0.4][i]), mace_ang=-60 + [0, 3, 6, 3][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(K(lean=4 * math.sin(ph), bob=-0.8 * abs(math.sin(ph)),
                     feet=((-4.0 + 2.5 * math.cos(ph), -max(0, 1.6 * math.sin(ph))), (4.0 - 2.5 * math.cos(ph), -max(0, -1.6 * math.sin(ph)))),
                     mace_ang=-55))
    # Smash: heave the club overhead (0-2), SMASH: the head lands at x 24..30 on the floor (3), shudder (4), lift (5-6)
    smash = [K(hand=(6.0, -22.0), mace_ang=-110, lean=-4), K(hand=(2.0, -27.0), mace_ang=-150, lean=-10, face="roar"),
             K(hand=(1.0, -28.0), mace_ang=-175, lean=-12, face="roar", squash=-0.5),
             K(hand=(14.0, -10.0), mace_ang=25, lean=14, face="roar", squash=1.0, feet=((-5.0, 0.0), (6.0, 0.0)),
               smear=[("arc", 4.0, -18.0, 18.0, -150, 20, "white", 2)], spark=[(26.0, -2.0, 1)], dust=(26.0, 0.0, 0, 1.6)),
             K(hand=(14.0, -9.0), mace_ang=30, lean=14, face="roar", squash=1.0, feet=((-5.0, 0.0), (6.0, 0.0)), dust=(26.0, 0.0, 1, 1.8)),
             K(hand=(12.0, -12.0), mace_ang=-10, lean=6), K()]
    # Court: lifts the Diamonds card before him (0-3: the guard is up from 3), holds it, crown aglow (4-7)
    court = [K(hand2=(0.0, -16.0), court=(-4.0, -20.0, -30)), K(hand2=(4.0, -20.0), court=(5.0, -24.0, -10), face="roar"),
             K(hand2=(8.0, -18.0), court=(11.0, -20.0, 0), face="glow", lean=-2),
             K(hand2=(9.0, -17.0), court=(12.0, -19.0, 0), face="glow", spark=[(12.0, -27.0, 1)])]
    court += [K(hand2=(9.0, -17.0 + [0, 0.5, 1.0, 0.5][i]), court=(12.0, -19.0 + [0, 0.5, 1.0, 0.5][i], 0), face="glow",
                bob=[0, 0.4, 0.8, 0.4][i]) for i in range(4)]
    cidle = [K(hand2=(9.0, -17.0 + [0, 0.5, 1.0, 0.5][i]), court=(12.0, -19.0 + [0, 0.5, 1.0, 0.5][i], 0), face="glow",
               bob=[0, 0.4, 0.8, 0.4][i], mace_ang=-80) for i in range(4)]
    crun = []
    for i in range(6):
        ph = i / 6 * math.tau
        crun.append(K(lean=3 * math.sin(ph), bob=-0.6 * abs(math.sin(ph)), face="glow", court=(12.0, -19.0, 2 * math.sin(ph)),
                      hand2=(9.0, -17.0), mace_ang=-80,
                      feet=((-4.0 + 2.0 * math.cos(ph), -max(0, 1.2 * math.sin(ph))), (4.0 - 2.0 * math.cos(ph), -max(0, -1.2 * math.sin(ph))))))
    d0 = K(face="roar", lean=-10, hand=(6.0, -24.0), mace_ang=-140)
    d1 = K(face="dead", lean=-30, bob=3.0, hand=(2.0, -18.0), mace_ang=150)
    d2 = _king_corpse(0)
    corpse = _king_corpse(1)
    knock = K(face="roar", lean=-14, hand=(6.0, -22.0), mace_ang=-120)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.09] * 6),
             ("Smash", smash, [0.14, 0.12, 0.12, 0.06, 0.12, 0.12, 0.14]),
             ("Court", court, [0.1, 0.1, 0.1, 0.12, 0.12, 0.12, 0.12, 0.12]),
             ("CourtIdle", cidle, [0.14] * 4), ("CourtRun", crun, [0.1] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxCardKing", anims, outdir, scale=4)


def _king_corpse(stage):
    r = Rig()
    r.poly([(-10.0, 0.0), (10.0, 0.0), (8.0, -4.0), (-8.0, -4.0)], "crim", -0.5)
    card(r, 0.0, -2.6, 16.0, 4.5 if stage else 6.0, z=0.0)
    club_pip(r, 0.0, -3.2, 1.2, "blk", 0.1)
    r.stamp(KING_HEAD["dead"], -13.0, 0.0, 1.0, KING_LEG, pivot=(4, 8))
    mace(r, 9.0, -1.0, -5, 0.5, ln=9.0)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.8)
    return r.resolve()


# ================================================================== HOUSE OF CARDS
HOUSE_MASK = {
    # pivot (4, 6): a court card's face (the Jack) peering out of the top of the house
    "calm": """
..nCCn...
.nCgCCn..
.aWWWWWa.
aWmWWmWWa
aWWWWWWWa
aWWnCnWWa
.aWWWWWa.
""",
    "shout": """
..nCCn...
.nCgCCn..
.aWWWWWa.
aWmWWmWWa
aWWWWWWWa
aWWmmmWWa
.aWWnWWa.
""",
    "dead": """
.........
..nCCn...
.aWWWWWa.
aWmWWmWWa
aWWmmWWWa
aWWWWWWWa
.aWWWWWa.
""",
}
HOUSE_LEG = {"a": ("card", 1), "W": ("card", 3), "m": ("blk", 0), "n": ("crim", 1), "C": ("crim", 3), "g": ("gold", 4)}


def a_frame(r, x, y, h, z, lean=0.0, back="crim", gap=1.2):
    """Two cards propped into an A on the floor line y, apex at (x, y - h)."""
    w = h * 0.5
    for side in (-1, 1):
        cx = x + side * w * 0.5 + lean * 0.5
        a = side * 18 + lean
        card(r, cx, y - h / 2, 3.6, h, z=z + (0.01 if side > 0 else 0), ang=a, back=harl(cx, y, 2.0, back, "card") if side < 0 else None,
             pip=[(0, -1)], pip_mat="crim", lit=0.05 if side > 0 else -0.2)


def house(tiers=3, lean=0.0, bob=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), face="calm", topple=None, orbit=(), whirl=None,
          smear=None, spark=None, extra=None, sway=0.0):
    """tiers 3..1: stacked rows of A-frames with the mask card on top; tiers 0 (whirl=phase): a whirlwind of cards.
    topple: (dx, dy, ang) offset of the top tier as it slaps forward."""
    r = Rig()
    y0 = -4.0 + bob
    if tiers > 0:
        legs2(r, (0.0, y0), feet, 2.2, 2.2, ("blk", "blk"), rad=(0.6, 0.5), boots="blk", spread=5.0)
        r.line(-12.0, y0 + 0.4, 12.0, y0 + 0.4, "gold", 0.0, tone=2)      # the floor card it stands on
        r.poly([(-12.5, y0 + 1.0), (12.5, y0 + 1.0), (12.5, y0 - 0.4), (-12.5, y0 - 0.4)], "card", -0.1, normal=(0, -1, 0.6))
    H = 9.0
    y = y0 - 0.6
    top_y = y
    for t in range(min(tiers, 3)):
        n = (3, 2, 1)[t]
        off = sway * (t + 1)
        is_top = (t == tiers - 1)
        dx, dy, ang = (topple if (topple and is_top and tiers > 1) else (0.0, 0.0, 0.0))
        for j in range(n):
            x = (j - (n - 1) / 2.0) * 7.4 + off + dx
            a_frame(r, x, y + dy, H, 0.5 + t, lean=lean + ang)
        y -= H
        if t < tiers - 1 or True:
            r.poly([(-3.8 * n + off + dx, y + dy + 0.6), (3.8 * n + off + dx, y + dy + 0.6), (3.8 * n + off + dx, y + dy - 0.6),
                    (-3.8 * n + off + dx, y + dy - 0.6)], "card", 0.6 + t, normal=(0, -1, 0.6))
        top_y = y + dy
        top_x = off + dx
    if tiers > 0:
        r.stamp(HOUSE_MASK[face], top_x + 0.5, top_y - 0.6, 5.0, HOUSE_LEG, pivot=(4, 6))
    else:
        ph = whirl or 0.0
        for i in range(22):
            k = i / 22.0
            yy = -2.0 - k * 24.0
            rad = 3.0 + k * 10.0
            a = ph + i * 2.4
            x = rad * math.cos(a)
            z = 2.0 + math.sin(a)
            card(r, x, yy, 3.0, 4.0, z=z, ang=math.degrees(a) * 0.5, back="crim" if i % 3 == 0 else None, pip=[(0, 0)], lit=0.1 * math.sin(a))
        for i in range(3):
            arc_smear(r, 0.0, -6.0 - i * 7.0, 5.0 + i * 3.0, math.degrees(ph) + i * 60, math.degrees(ph) + i * 60 + 150, "white", 1)
        r.stamp(HOUSE_MASK[face], 0.5, -12.0, 5.0, HOUSE_LEG, pivot=(4, 6))
    for (x, y, a) in orbit:
        card(r, x, y, 3.0, 4.0, z=6.0 + 0.01 * x, ang=a, back="crim", lit=0.1)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def house_sheet(outdir):
    Hs = house
    anims = []
    for tiers in (3, 2, 1):
        sfx = "" if tiers == 3 else str(tiers)
        idle = [Hs(tiers, bob=[0, -0.3, -0.6, -0.3][i], sway=[0, 0.3, 0, -0.3][i]) for i in range(4)]
        run = [Hs(tiers, bob=-0.6 * abs(math.sin(i / 6 * math.tau)), sway=0.5 * math.sin(i / 6 * math.tau),
                  feet=((-4.0 + 2.0 * math.cos(i / 6 * math.tau), -max(0, 1.4 * math.sin(i / 6 * math.tau))),
                        (4.0 - 2.0 * math.cos(i / 6 * math.tau), -max(0, -1.4 * math.sin(i / 6 * math.tau))))) for i in range(6)]
        # Topple: the top tier rocks back (0-1), tips over (2), SLAPS down in front (3: x 4..20), springs back up (4-6)
        top = [Hs(tiers, topple=(-1.0, 0.0, -10)), Hs(tiers, topple=(-2.0, 0.0, -18), face="shout"),
               Hs(tiers, topple=(5.0, 3.0, 40), face="shout", smear=[("arc", 0.0, -16.0, 12.0, -120, -30, "white", 1)]),
               Hs(tiers, topple=(10.0, 8.0, 70), face="shout", spark=[(16.0, -8.0, 1)]),
               Hs(tiers, topple=(7.0, 5.0, 45)), Hs(tiers, topple=(2.0, 1.0, 10)), Hs(tiers)]
        if tiers == 1:   # one tier left: the whole house hops forward and slaps instead
            top = [Hs(1, bob=1.0), Hs(1, bob=-2.0, lean=-10, face="shout"), Hs(1, bob=-3.0, lean=20, face="shout"),
                   Hs(1, bob=0.0, lean=35, face="shout", spark=[(14.0, -6.0, 1)]), Hs(1, lean=20), Hs(1, lean=8), Hs(1)]
        anims += [("Idle" + sfx, idle, [0.16, 0.14, 0.16, 0.14]), ("Run" + sfx, run, [0.08] * 6),
                  ("Topple" + sfx, top, [0.12, 0.12, 0.06, 0.08, 0.1, 0.12, 0.12])]
    # Storm (full house): the cards peel off the tiers (0-3) and whirl round it (4-7: the storm is cast on 4)
    def orbit(k, n=6):
        return [(16.0 * math.cos(k * 0.9 + i * math.tau / n), -12.0 + 6.0 * math.sin(k * 0.9 + i * math.tau / n),
                 30 * k + 60 * i) for i in range(n)]
    storm = [Hs(3, face="shout"), Hs(3, face="shout", orbit=orbit(0, 2)), Hs(3, face="shout", orbit=orbit(1, 4)),
             Hs(3, face="shout", orbit=orbit(2, 6)), Hs(3, orbit=orbit(3)), Hs(3, orbit=orbit(4)), Hs(3, orbit=orbit(5)), Hs(3, orbit=orbit(6))]
    # tier 0: a whirlwind of loose cards round the mask
    widle = [Hs(0, whirl=i * 1.2) for i in range(4)]
    wrun = [Hs(0, whirl=i * 1.6, sway=1.0) for i in range(6)]
    wslash = [Hs(0, whirl=i * 2.0, face="shout" if 1 < i < 5 else "calm",
                 smear=[("arc", 0.0, -8.0, 14.0, i * 60, i * 60 + 200, "white", 2)] if 1 < i < 5 else None) for i in range(6)]
    # Storm with fewer tiers: the cards peel off what is left (Storm2, Storm1) or fly out of the whirl (Storm0, cast on 3)
    st2 = [Hs(2, face="shout")] + [Hs(2, face="shout" if k < 3 else "calm", orbit=orbit(k, min(6, 2 * (k + 1)))) for k in range(7)]
    st1 = [Hs(1, face="shout")] + [Hs(1, face="shout" if k < 3 else "calm", orbit=orbit(k, min(6, 2 * (k + 1)))) for k in range(7)]
    st0 = [Hs(0, whirl=k * 1.4, face="shout", orbit=orbit(k, min(6, 2 * (k + 1)))) for k in range(8)]
    anims += [("Storm", storm, [0.1, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12, 0.14]),
              ("Storm2", st2, [0.1, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12, 0.14]), ("Storm1", st1, [0.1, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12, 0.14]),
              ("Storm0", st0, [0.08, 0.08, 0.08, 0.1, 0.12, 0.12, 0.12, 0.14]),
              ("Whirl", widle, [0.07] * 4), ("WhirlRun", wrun, [0.06] * 6), ("WhirlSlash", wslash, [0.08, 0.08, 0.05, 0.06, 0.08, 0.1])]
    d0 = Hs(3, topple=(-3.0, 0.0, -20), face="shout")
    d1 = Hs(2, topple=(-6.0, 4.0, -60), face="dead", extra=lambda r: [card(r, 10.0, -6.0, 3.0, 4.0, z=6, ang=70, back="crim"),
                                                                       card(r, -12.0, -4.0, 3.0, 4.0, z=6, ang=-50)])
    d2 = _house_corpse(0)
    corpse = _house_corpse(1)
    knock = Hs(3, sway=-1.2, face="shout", lean=-6)
    anims += tail_anims(anims[0][1][0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxHouseOfCards", anims, outdir, scale=4)


def _house_corpse(stage):
    r = Rig()
    import random
    rnd = random.Random(5)
    for i in range(12 if stage else 9):
        card(r, rnd.uniform(-14, 14), -1.0 - rnd.uniform(0, 2), 4.0, 2.4, z=i * 0.05, ang=rnd.uniform(-20, 20),
             back="crim" if i % 3 == 0 else None, pip=[(0, 0)])
    r.stamp(HOUSE_MASK["dead"], 2.0, 0.0, 2.0, HOUSE_LEG, pivot=(4, 6))
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.8)
    return r.resolve()


# ================================================================== NATURAL TWENTY: a d20 on brass spider legs
_PHI = (1 + 5 ** 0.5) / 2
_ICO_V = [(-1, _PHI, 0), (1, _PHI, 0), (-1, -_PHI, 0), (1, -_PHI, 0), (0, -1, _PHI), (0, 1, _PHI), (0, -1, -_PHI), (0, 1, -_PHI),
          (_PHI, 0, -1), (_PHI, 0, 1), (-_PHI, 0, -1), (-_PHI, 0, 1)]
_ICO_F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
          (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]


def d20(r, cx, cy, rad, rx, ry, rz, z, mat="d20", glow=True, number=True):
    """An icosahedron of radius rad: flat-lit facets, glowing violet seams, an ivory '20' mark on the front facet."""
    n = math.sqrt(1 + _PHI * _PHI)
    vs = [rot3(tuple(c / n * rad for c in v), rx, ry, rz) for v in _ICO_V]
    vs = [rot3(v, -20.0, 0, 0) for v in vs]
    faces = []
    for f in _ICO_F:
        a, b, c = (vs[i] for i in f)
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2]); w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        nx, ny, nz = u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
        nx, ny, nz = nx / ln, ny / ln, nz / ln
        cz = (a[2] + b[2] + c[2]) / 3
        if (a[0] + b[0] + c[0]) * nx + (a[1] + b[1] + c[1]) * ny + (a[2] + b[2] + c[2]) * nz < 0: nx, ny, nz = -nx, -ny, -nz
        if nz > -0.05: continue
        faces.append((cz, [(cx + p[0], cy + p[1]) for p in (a, b, c)], (nx, ny, -nz)))
    faces.sort(key=lambda f: -f[0])
    best = min(faces, key=lambda f: -f[2][2]) if faces else None
    for i, (cz, pts, nn) in enumerate(faces):
        l = lam(*nn)
        t = 1 if l < 0.0 else 2 if l < 0.45 else 3 if l < 0.8 else 4
        p = r.part(False, z + 0.001 * i)
        for (x, y) in poly_px(pts):
            r.put(x, y, z + 0.001 * i, mat, 0.5, p, t)
        if glow:
            for a_, b_ in zip(pts, pts[1:] + pts[:1]):
                r.line(a_[0], a_[1], b_[0], b_[1], "glow", z + 0.001 * i + 0.0005, tone=2 if nn[1] > 0 else 3)
    if number and best:
        mx = sum(p[0] for p in best[1]) / 3; my = sum(p[1] for p in best[1]) / 3
        r.dots([(mx - 1, my), (mx, my), (mx + 1, my)], "ivory", 4, z + 0.05)
    return r


def twenty(lift=8.0, rot=(0.0, 0.0, 0.0), lean=0.0, legs=None, smear=None, spark=None, extra=None, rad=8.0, dx=0.0, glow=True):
    r = Rig()
    cx, cy = dx, -lift - rad
    # six spider-thin brass legs: from the underside out to the floor
    legs = legs if legs is not None else [(-13.0, 0.0), (-8.0, 0.0), (-3.0, 0.0), (3.0, 0.0), (8.0, 0.0), (13.0, 0.0)]
    for i, (fx, fy) in enumerate(legs):
        sx, sy = cx + (i - 2.5) * 1.8, cy + rad * 0.6
        kx, ky = sx + (fx - sx) * 0.55, min(sy, fy) - 3.0 - abs(fx - sx) * 0.25
        far = i % 2 == 0
        r.polyline([(sx, sy), (kx, ky), (fx, fy)], "gold", -1.0 if far else 2.0, tones=[1 if far else 3, 1 if far else 2])
        r.dot(kx, ky, "gold", 2 if far else 4, -0.9 if far else 2.1)
    d20(r, cx, cy, rad, *rot, z=1.0, glow=glow)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def twenty_sheet(outdir):
    Tw = twenty
    base = [(-13.0, 0.0), (-8.0, 0.0), (-3.0, 0.0), (3.0, 0.0), (8.0, 0.0), (13.0, 0.0)]
    idle = [Tw(lift=8.0 + [0, 0.4, 0.8, 0.4][i], rot=(0, 8 * i, 0)) for i in range(4)]
    run = []
    for i in range(6):
        lg = [(x + (2.0 if (k + i) % 2 else -2.0), -(1.5 if (k + i) % 2 else 0.0)) for k, (x, y) in enumerate(base)]
        run.append(Tw(lift=8.0 + 0.6 * (i % 2), rot=(10 * i, 15 * i, 0), legs=lg))
    # Ram: legs gather (0), rears back (1), lunges (2 smear), HIT: facets at x 19 (3), recoil (4-6)
    ram = [Tw(lift=6.0, legs=[(x * 0.7, 0.0) for x, y in base]), Tw(lift=9.0, dx=-3.0, rot=(0, -20, 10)),
           Tw(lift=8.0, dx=4.0, rot=(0, 20, -10), smear=[("line", [(-8, -18), (-2, -18), (3, -17)], "white", 2)]),
           Tw(lift=8.0, dx=8.0, rot=(0, 35, -20), spark=[(17.0, -15.0, 1)], legs=[(x + 4, 0.0) for x, y in base]),
           Tw(lift=8.0, dx=6.0, rot=(0, 30, -10)), Tw(lift=8.0, dx=2.0, rot=(0, 10, 0)), Tw()]
    # Crit: crouch (0), LEAP (1-5: tumbling in the air, legs tucked), lands on its roll (6), shakes off (7-8)
    crit = [Tw(lift=4.0, legs=[(x * 0.6, 0.0) for x, y in base])]
    for k in range(5):
        h = 8.0 + 14.0 * math.sin((k + 1) / 6 * math.pi)
        crit.append(Tw(lift=h, rot=(60 * (k + 1), 40 * (k + 1), 20 * k), legs=[(x * 0.3, -h + 4.0) for x, y in base],
                       smear=[("arc", 0.0, -h - 8.0, 11.0, 70 * k, 70 * k + 120, "glow", 1)]))
    crit += [Tw(lift=6.0, rot=(0, 0, 0), spark=[(0.0, -24.0, 1)], extra=lambda r: dust_puff(r, 0.0, 0.0, 0, 2.0)),
             Tw(lift=7.0, extra=lambda r: dust_puff(r, 0.0, 0.0, 1, 2.2)), Tw()]
    # Fumble: rolled a 1: flipped on its back, legs flailing
    fumble = [Tw(lift=1.0, rot=(180, 10 * i, 0), legs=[(x * 0.8 + (2 if (i + k) % 2 else -2), -14.0 - (3 if (i + k) % 2 else 0))
                                                        for k, (x, y) in enumerate(base)], glow=False) for i in range(4)]
    d0 = Tw(lift=9.0, rot=(-30, 20, 10), dx=-2.0)
    d1 = Tw(lift=3.0, rot=(-60, 40, 40), legs=[(x * 1.2, -2.0) for x, y in base], glow=False)
    d2 = Tw(lift=0.0, rot=(-90, 50, 60), legs=[(x * 1.3, 0.0) for x, y in base], glow=False, extra=lambda r: dust_puff(r, 0.0, 0.0, 1, 2.0))
    corpse = Tw(lift=0.0, rot=(-90, 50, 60), legs=[(x * 1.4, 0.0) for x, y in base], glow=False)
    knock = Tw(lift=9.0, rot=(-20, -20, 15), dx=-2.0)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.06] * 6),
             ("Ram", ram, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Crit", crit, [0.12, 0.07, 0.07, 0.07, 0.07, 0.07, 0.14, 0.12, 0.12]),
             ("Fumble", fumble, [0.1] * 4)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxTwenty", anims, outdir, scale=4)


# ================================================================== NUTCRACKER
NUT_LEG = {"w": ("wood", 2), "W": ("wood", 3), "L": ("wood", 4), "d": ("wood", 1), "k": ("blk", 0), "b": ("blk", 2), "B": ("blk", 3),
           "g": ("gold", 2), "G": ("gold", 4), "i": ("ivory", 3), "I": ("ivory", 4), "m": ("blk", 0), "r": ("crim", 3), "e": ("eye", 3),
           "f": ("flesh", 3), "F": ("flesh", 2)}
NUT_HEAD = {
    # pivot (4, 11): the neck. Tall black shako with a gold plate and a red plume; painted face, white whiskers, a jaw
    "shut": """
...r.....
..brb....
.bBBBbk..
.bBgGbk..
.bBGgbk..
.kkkkkk..
.FffffF..
.fmfffm..
.ffrrff..
.iIIIIi..
.iWWWWi..
..iiii...
""",
    "open": """
...r.....
..brb....
.bBBBbk..
.bBgGbk..
.bBGgbk..
.kkkkkk..
.FffffF..
.fmfffm..
.ffrrff..
.imkkki..
.i.....i.
.iWWWWi..
""",
    "wide": """
...r.....
..brb....
.bBBBbk..
.bBgGbk..
.bBGgbk..
.kkkkkk..
.FffffF..
.fefffe..
.ffrrff..
.iIiIii..
.m.....m.
.iWWWWWi.
""",
}


def nut_key(r, x, y, ang, z, speed=0):
    """The brass wind-up key in its back: a shaft and a two-lobed bow seen turning (ang)."""
    r.tube([(x, y), (x - 2.4, y)], [0.6, 0.6], "gold", z)
    w = abs(math.cos(math.radians(ang))) * 2.6 + 0.6
    for side in (-1, 1):
        r.ell(x - 3.6, y + side * w * 0.8, 1.2, max(0.6, w * 0.6), "gold", z + (0.01 if side > 0 else -0.01), bias=0.1 if side < 0 else -0.1)
    for k in range(speed):
        arc_smear(r, x - 3.6, y, 3.5 + k, 100 + 40 * k, 250 + 40 * k, "gold", 1)


def nutcracker(lean=0.0, bob=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), hand=(6.0, -15.0), hand2=(-5.0, -14.0), sabre=-60.0,
               face="shut", key=0.0, key_speed=0, slump=0.0, smear=None, spark=None, extra=None, knee=1, jaw_fx=None):
    r = Rig()
    hip = (0.0, -10.0 + bob + slump)
    T = Xf(lean, hip)
    legs2(r, hip, feet, 5.0, 4.8, ("ivory", "blk"), rad=(1.5, 1.3), boots="blk", knee=knee, spread=1.2)
    sh_n, sh_f = T(hip[0] + 3.2, hip[1] - 9.0), T(hip[0] - 3.0, hip[1] - 9.0)
    # key in the back first
    kx, ky = T(hip[0] - 3.4, hip[1] - 5.5)
    nut_key(r, kx, ky, key, -1.5, key_speed)
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 4.2, 4.0, bend=1)
    r.tube([sh_f, e2, hand2], [1.5, 1.3, 1.1], "crim", -0.6, bias=-0.35)
    r.ell(hand2[0], hand2[1], 1.2, 1.2, "ivory", -0.55, bias=-0.1)
    # a square wooden body in a crimson coat with white crossbelts and a gold belt
    tor = [T(hip[0] - 3.6, hip[1] + 1.0), T(hip[0] + 3.6, hip[1] + 1.0), T(hip[0] + 3.8, hip[1] - 9.6), T(hip[0] - 3.6, hip[1] - 9.6)]
    r.poly(tor, "crim", 0.0, curve=0.7)
    r.polyline([T(hip[0] - 3.2, hip[1] - 9.0), T(hip[0] + 3.0, hip[1] - 1.0)], "ivory", 0.1, tone=3)
    r.polyline([T(hip[0] + 3.2, hip[1] - 9.0), T(hip[0] - 3.0, hip[1] - 1.0)], "ivory", 0.1, tone=2)
    r.line(*T(hip[0] - 3.6, hip[1] - 0.4), *T(hip[0] + 3.6, hip[1] - 0.4), "gold", 0.15, tone=3)
    r.dot(*T(hip[0], hip[1] - 5.0), "gold", 4, 0.2)
    for side in (-1, 1):
        r.ell(*T(hip[0] + side * 3.6, hip[1] - 9.4), 1.8, 1.0, "gold", 0.5 if side > 0 else -0.3, bias=0.1)
    hx, hy = T(hip[0] + 0.6, hip[1] - 9.8)
    r.stamp(NUT_HEAD[face], hx, hy, 2.0, NUT_LEG, pivot=(4, 11))
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 4.2, 4.0, bend=1)
    r.tube([sh_n, e1, hand], [1.6, 1.4, 1.2], "crim", 3.0, bias=0.05)
    # sabre: a curved steel blade with a gold guard
    a = math.radians(sabre)
    pts = [(hand[0] + k * math.cos(a + k * 0.02), hand[1] + k * math.sin(a + k * 0.02)) for k in range(0, 13, 3)]
    r.tube(pts, [0.7, 0.8, 0.7, 0.6, 0.4], "steel", 3.2, bias=0.1)
    r.ell(hand[0] + 0.5, hand[1], 1.3, 1.0, "gold", 3.25)
    r.ell(hand[0], hand[1], 1.2, 1.2, "ivory", 3.3, bias=0.1)
    if jaw_fx: sparks(r, jaw_fx)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def nut_sheet(outdir):
    N = nutcracker
    idle = [N(bob=[0, -0.3, -0.5, -0.3][i], key=45 * i, hand=(6.0, -15.0 - [0, 0.3, 0.5, 0.3][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(N(lean=4, bob=-0.6 * abs(math.sin(ph)), key=60 * i, feet=((-3.0 * math.cos(ph), -max(0, 2.5 * math.sin(ph))),
                                                                         (3.0 * math.cos(ph), -max(0, -2.5 * math.sin(ph)))),
                     hand=(6.0, -15.0), hand2=(-4.0 - 2 * math.cos(ph), -13.0), sabre=-70, knee=1))
    # Sabre: draw over the shoulder (0-1), CUT down and across (2 smear, 3 HIT: x 1..23, y -25..-3), follow (4), recover (5-6)
    sab = [N(hand=(3.0, -22.0), sabre=-150, lean=-4), N(hand=(1.0, -25.0), sabre=-175, lean=-8, face="open"),
           N(hand=(9.0, -18.0), sabre=-40, lean=6, face="open", smear=[("arc", 2.0, -16.0, 14.0, -160, -20, "white", 2)]),
           N(hand=(11.0, -12.0), sabre=20, lean=10, face="open", smear=[("arc", 2.0, -16.0, 14.0, -60, 40, "white", 2)],
             spark=[(20.0, -6.0, 2)]),
           N(hand=(10.0, -10.0), sabre=40, lean=8), N(hand=(7.0, -13.0), sabre=-10, lean=3), N()]
    # Crack: the jaw drops open (0-2), LUNGES jaws first (3), CLAMPS (4: the grab), holds (5), CRUNCH (6), lets go (7-8)
    crack = [N(face="open", lean=-4), N(face="wide", lean=-8), N(face="wide", lean=-12, slump=1.0),
             N(face="wide", lean=24, feet=((-6.0, 0.0), (5.0, 0.0)), smear=[("line", [(-4, -24), (2, -24), (8, -23)], "white", 2)]),
             N(face="shut", lean=28, feet=((-6.0, 0.0), (5.0, 0.0)), spark=[(10.0, -21.0, 1)]),
             N(face="shut", lean=26, feet=((-6.0, 0.0), (5.0, 0.0))),
             N(face="open", lean=28, feet=((-6.0, 0.0), (5.0, 0.0)), spark=[(10.0, -21.0, 1), (12.0, -23.0, 2)]),
             N(face="shut", lean=12), N()]
    slow = [N(bob=0.3, key=15 * i, slump=0.6, hand=(5.0, -13.0), sabre=-30) for i in range(4)]
    srun = []
    for i in range(6):
        ph = i / 6 * math.tau
        srun.append(N(lean=2, slump=0.6, key=20 * i, feet=((-2.0 * math.cos(ph), -max(0, 1.5 * math.sin(ph))), (2.0 * math.cos(ph), -max(0, -1.5 * math.sin(ph)))),
                      hand=(5.0, -13.0), sabre=-30))
    # Rewind: frozen, arms limp, the key spinning backwards hard
    rewind = [N(slump=1.6, lean=6, hand=(4.0, -9.0), hand2=(-3.0, -9.0), sabre=60, key=-90 * i, key_speed=2, face="open") for i in range(4)]
    d0 = N(face="wide", lean=-12, hand=(2.0, -22.0), sabre=-150)
    d1 = N(face="open", lean=-40, bob=3.0, hand=(-1.0, -16.0), sabre=170, knee=-1)
    d2 = _nut_corpse(0)
    corpse = _nut_corpse(1)
    knock = N(face="open", lean=-16, hand=(3.0, -20.0), sabre=-130)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Sabre", sab, [0.12, 0.12, 0.05, 0.07, 0.1, 0.12, 0.12]),
             ("Crack", crack, [0.12, 0.12, 0.12, 0.06, 0.12, 0.14, 0.1, 0.12, 0.12]),
             ("IdleSlow", slow, [0.24] * 4), ("RunSlow", srun, [0.12] * 6), ("Rewind", rewind, [0.06] * 4)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxNutcracker", anims, outdir, scale=4)


def _nut_corpse(stage):
    r = Rig()
    r.poly([(-6.0, -0.4), (6.0, -0.4), (6.0, -6.0), (-6.0, -6.0)], "crim", 0.0)
    r.polyline([(-5, -5), (5, -1)], "ivory", 0.1, tone=3)
    r.tube([(6.0, -2.0), (11.0, -2.5 if not stage else -1.5), (15.0, -1.5)], [1.4, 1.3, 1.2], "ivory", 0.2)
    r.stamp(NUT_HEAD["open"], -9.0, -3.0, 1.0, NUT_LEG, pivot=(4, 11)) if False else None
    r.stamp(NUT_HEAD["shut"], -11.0, 0.0, 1.0, NUT_LEG, pivot=(4, 11)) if False else None
    # the head lies on its side: draw the shako and face rotated by laying a simple stamp
    r.stamp("""
.bbbbbk.
rBgGBBbk
.bbbbbk.
""", -12.0, -1.0, 1.0, NUT_LEG, pivot=(4, 2))
    r.stamp("""
FffF
fmff
irri
iWWi
""", -6.5, -0.5, 1.2, NUT_LEG, pivot=(2, 3))
    nut_key(r, 0.0, -7.0, 0.0, 1.5)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.6)
    return r.resolve()


# ================================================================== PUPPETEER: a stilt-walker with two knife puppets
PUPM_LEG = {"a": ("flesh", 1), "w": ("flesh", 2), "W": ("flesh", 3), "m": ("blk", 0), "b": ("blk", 2), "B": ("blk", 3),
            "n": ("crim", 1), "C": ("crim", 3), "g": ("gold", 3), "e": ("glow", 4)}
PUPM_HEAD = {
    "calm": """
..bBBb..
..bBBb..
..bBBb..
.bbBBbbk
..awWw..
..wewe..
..wWWa..
...nC...
""",
    "laugh": """
..bBBb..
..bBBb..
..bBBb..
.bbBBbbk
..awWw..
..wewe..
..wmma..
...nC...
""",
    "dead": """
........
..bBBb..
..bBBb..
.bbBBbbk
..awWw..
..wmwm..
..wWWa..
...nC...
""",
}


def knife_puppet(r, x, y, z, stab=0.0, arm=0.0):
    """A little jester puppet dangling on its strings, a knife in its fist. stab 0..1 lunges it forward."""
    body = [(x, y - 3.0), (x + stab * 2.0, y - 6.0)]
    r.tube(body, [1.4, 1.2], harl(x, y, 1.6, "crim", "blk"), z)
    r.ell(x + stab * 2.4, y - 8.0, 1.4, 1.4, "porc", z + 0.01, bias=0.1)
    r.dot(x + stab * 2.4 + 0.6, y - 8.2, "blk", 0, z + 0.02)
    r.line(x - 1.0, y - 2.6, x - 1.4, y, "blk", z, tone=1)
    r.line(x + 1.0, y - 2.6, x + 1.2, y, "blk", z, tone=1)
    hx, hy = x + 2.0 + stab * 5.0, y - 5.0 + arm
    r.line(x + stab * 1.6, y - 5.0, hx, hy, "porc", z + 0.02, tone=3)
    r.line(hx, hy, hx + 3.0, hy - 0.8, "steel", z + 0.03, tone=4)
    return (x + stab * 2.4, y - 9.4), (hx, hy)


def puppeteer(lean=0.0, bob=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), hand=(10.0, -26.0), hand2=(-9.0, -25.0), face="calm",
              pups=((12.0, 0.0, 0.0), (-11.0, 0.0, 0.0)), glow=False, smear=None, spark=None, extra=None, cut=False):
    r = Rig()
    hip = (0.0, -17.0 + bob)
    T = Xf(lean, hip)
    # stilts: long black poles under trouser legs
    for k, f in enumerate(feet):
        hp = (hip[0] + (-1.2 if k == 0 else 1.2), hip[1] + 0.4)
        r.tube([hp, (f[0], f[1] - 0.5)], [1.2, 0.6], "blk", -1.0 if k == 0 else 1.0, bias=-0.3 if k == 0 else 0.1)
        r.dot(f[0], f[1] - 0.5, "gold", 2, 1.1)
    # long velvet coat flaring to the knees
    r.poly([T(hip[0] - 5.0, hip[1] + 5.0), T(hip[0] + 4.0, hip[1] + 5.0), T(hip[0] + 3.0, hip[1] - 9.0), T(hip[0] - 3.0, hip[1] - 9.0)],
           "blk", 0.0, curve=0.8)
    r.poly([T(hip[0] + 0.0, hip[1] + 4.8), T(hip[0] + 2.0, hip[1] + 4.8), T(hip[0] + 1.6, hip[1] - 8.8), T(hip[0] + 0.4, hip[1] - 8.8)],
           "crim", 0.1, bias=0.1)
    r.ell(*T(hip[0] + 0.5, hip[1] - 9.0), 3.0, 1.2, "crim", 0.3)          # scarf
    hx, hy = T(hip[0] + 0.6, hip[1] - 9.4)
    r.stamp(PUPM_HEAD[face], hx, hy, 2.0, PUPM_LEG, pivot=(4, 7))
    sh_n, sh_f = T(hip[0] + 2.8, hip[1] - 8.0), T(hip[0] - 2.6, hip[1] - 8.0)
    tips = []
    for k, (sh, hd) in enumerate(((sh_f, hand2), (sh_n, hand))):
        e = ik(sh[0], sh[1], hd[0], hd[1], 4.6, 4.4, bend=1)
        z = -0.5 if k == 0 else 3.0
        r.tube([sh, e, hd], [1.2, 1.0, 0.9], "blk", z, bias=-0.3 if k == 0 else 0.1)
        # the control cross
        r.line(hd[0] - 3.0, hd[1] - 1.0, hd[0] + 3.0, hd[1] - 1.0, "wood", z + 0.1, tone=3)
        r.line(hd[0], hd[1] - 3.5, hd[0], hd[1] + 1.5, "wood", z + 0.1, tone=2)
        r.ell(hd[0], hd[1], 1.0, 1.0, "flesh", z + 0.2)
        tips.append(hd)
    # the knife puppets, and their strings up to the crosses
    for k, (px, py, st) in enumerate(pups):
        head, fist = knife_puppet(r, px, py, 4.0 if px > 0 else -1.5, stab=st)
        cross = tips[1] if px > 0 else tips[0]
        if not cut:
            for (sx, sy), (ex, ey) in (((cross[0] - 3.0, cross[1] - 1.0), head), ((cross[0] + 3.0, cross[1] - 1.0), fist)):
                r.line(sx, sy, ex, ey, "glow", 4.5 if px > 0 else -1.4, tone=4 if glow else 1)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def puppeteer_sheet(outdir):
    P = puppeteer
    idle = [P(bob=[0, -0.4, -0.8, -0.4][i], hand=(10.0, -26.0 - [0, 1, 2, 1][i]), hand2=(-9.0, -25.0 - [1, 2, 1, 0][i]),
              pups=((12.0, -[0, 1, 2, 1][i], 0.0), (-11.0, -[1, 2, 1, 0][i], 0.0))) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(P(lean=6, bob=-1.0 * abs(math.sin(ph)), feet=((-5.0 * math.cos(ph), -max(0, 2 * math.sin(ph))),
                                                                (5.0 * math.cos(ph), -max(0, -2 * math.sin(ph)))),
                     hand=(10.0, -25.0), hand2=(-9.0, -25.0), pups=((13.0, -2.0 * abs(math.sin(ph)), 0.0), (-10.0, -2.0 * abs(math.cos(ph)), 0.0))))
    # Dance: crosses jerk up (0-1), both puppets lunge in (2), STAB: knives at (15-23, -4..-13) (3), recover (4-6)
    dance = [P(hand=(10.0, -29.0), hand2=(-7.0, -28.0), pups=((12.0, -3.0, 0.0), (-6.0, -2.0, 0.0))),
             P(hand=(9.0, -31.0), hand2=(-4.0, -30.0), pups=((11.0, -5.0, -0.3), (-2.0, -4.0, 0.0)), face="laugh"),
             P(hand=(13.0, -27.0), hand2=(4.0, -27.0), pups=((14.0, -3.0, 0.6), (8.0, -2.0, 0.6)), face="laugh",
               smear=[("line", [(16, -8), (20, -8), (23, -7)], "white", 2)]),
             P(hand=(15.0, -25.0), hand2=(8.0, -25.0), pups=((16.0, -2.0, 1.0), (10.0, -1.0, 1.0)), face="laugh",
               spark=[(24.0, -7.0, 2), (18.0, -6.0, 2)]),
             P(hand=(13.0, -26.0), hand2=(2.0, -26.0), pups=((14.0, -1.0, 0.5), (4.0, 0.0, 0.3))),
             P(hand=(11.0, -26.0), hand2=(-6.0, -25.0), pups=((12.0, 0.0, 0.0), (-8.0, 0.0, 0.0))), P()]
    # Curtain: both crosses hauled high, the strings blaze (0-2), YANK (3: the allies are hauled), bow (4-8)
    curtain = [P(hand=(8.0, -31.0), hand2=(-7.0, -31.0), glow=True), P(hand=(6.0, -35.0), hand2=(-5.0, -35.0), glow=True, face="laugh"),
               P(hand=(5.0, -36.0), hand2=(-4.0, -36.0), glow=True, face="laugh", spark=[(5.0, -40.0, 2), (-4.0, -40.0, 2)]),
               P(hand=(12.0, -24.0), hand2=(-11.0, -24.0), glow=True, face="laugh", bob=1.0,
                 extra=lambda r: [confetti(r, 0.0, -30.0, 0, 14, 4, spread=14)]),
               P(hand=(12.0, -24.0), hand2=(-11.0, -24.0), glow=True, lean=10, extra=lambda r: confetti(r, 0.0, -30.0, 1, 12, 4, spread=14)),
               P(hand=(11.0, -24.0), hand2=(-10.0, -24.0), lean=14, extra=lambda r: confetti(r, 0.0, -30.0, 2, 10, 4, spread=14)),
               P(lean=8, extra=lambda r: confetti(r, 0.0, -30.0, 3, 8, 4, spread=14)), P(lean=3), P()]
    d0 = P(face="laugh", lean=-10, hand=(6.0, -30.0), hand2=(-12.0, -28.0))
    d1 = P(face="dead", lean=-30, bob=6.0, hand=(3.0, -20.0), hand2=(-12.0, -16.0), cut=True,
           pups=((12.0, 0.0, 0.0), (-13.0, 0.0, 0.0)))
    d2 = _puppeteer_corpse(0)
    corpse = _puppeteer_corpse(1)
    knock = P(face="laugh", lean=-14, hand=(6.0, -28.0), hand2=(-12.0, -26.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.09] * 6),
             ("Dance", dance, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Curtain", curtain, [0.12, 0.12, 0.14, 0.06, 0.12, 0.12, 0.12, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxPuppeteer", anims, outdir, scale=4)


def _puppeteer_corpse(stage):
    r = Rig()
    r.poly([(-10.0, -0.4), (6.0, -0.4), (5.0, -4.6), (-9.0, -4.0)], "blk", 0.0)
    r.tube([(6.0, -1.0), (16.0, -1.5 if stage else -3.5)], [1.0, 0.6], "blk", 0.3)
    r.tube([(5.0, -2.0), (14.0, -0.5)], [1.0, 0.6], "blk", 0.2)
    r.stamp(PUPM_HEAD["dead"], -14.0, -1.0, 1.0, PUPM_LEG, pivot=(4, 7))
    knife_puppet(r, -20.0, 0.0, 0.5)
    knife_puppet(r, 20.0, 0.0, 0.5)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 2.0)
    return r.resolve()


# ================================================================== THE ORACLE (and her prophecy ghost)
ORA_LEG = {"k": ("viol", 0), "d": ("viol", 1), "v": ("viol", 2), "V": ("viol", 3), "L": ("viol", 4), "g": ("gold", 2),
           "G": ("gold", 4), "a": ("ivory", 1), "w": ("ivory", 2), "W": ("ivory", 3), "e": ("glow", 4), "E": ("glow", 3),
           "m": ("blk", 0), "n": ("crim", 1)}
ORA_HEAD = {
    # pivot (4, 12): the neck. A tall hood rising to a point like a candle flame; the veil open on a third eye
    "calm": """
....V....
...dVd...
...vVv...
..dvLvd..
..dvVvd..
.dvVvVvd.
.dvgGgvd.
dvaWeWavd
dvWmWmWvd
dvaWWWavd
.dvanavd.
..dvwvd..
...dkd...
""",
    "open": """
....V....
...dVd...
...vVv...
..dvLvd..
..dvVvd..
.dvVvVvd.
.dgGeGgd.
dvaEeEavd
dvWeWeWvd
dvaWWWavd
.dvamavd.
..dvwvd..
...dkd...
""",
    "shut": """
....V....
...dVd...
...vVv...
..dvLvd..
..dvVvd..
.dvVvVvd.
.dvgGgvd.
dvaWmWavd
dvWmWmWvd
dvaWWWavd
.dvanavd.
..dvwvd..
...dkd...
""",
}


def oracle(hover=4.0, lean=0.0, hand=(6.0, -18.0), hand2=(-5.0, -18.0), face="calm", orb=None, fade=False, spark=None,
           smear=None, extra=None):
    r = Rig()
    cy = -hover
    # the floating cushion: crimson, gold tassels
    r.ell(0.0, cy - 1.6, 7.0, 2.2, "crim", 0.0, bias=0.1)
    for x in (-7.0, 7.0):
        r.dot(x, cy - 0.2, "gold", 3, 0.1); r.dot(x, cy + 0.8, "gold", 2, 0.1)
    T = Xf(lean, (0.0, cy - 3.0))
    # seated in robes: a broad base narrowing to the shoulders
    r.poly([T(-6.0, cy - 2.6), T(6.0, cy - 2.6), T(3.6, cy - 12.0), T(-3.4, cy - 12.0)], "viol", 0.5, curve=0.9)
    r.polyline([T(-5.0, cy - 3.0), T(5.0, cy - 3.0)], "gold", 0.6, tone=3)
    r.dots([T(-1.0, cy - 8.0), T(1.0, cy - 8.0), T(0.0, cy - 6.0)], "gold", 3, 0.6)
    hx, hy = T(0.4, cy - 12.0)
    r.stamp(ORA_HEAD[face], hx, hy, 2.0, ORA_LEG, pivot=(4, 12))
    sh_n, sh_f = T(3.2, cy - 11.0), T(-3.0, cy - 11.0)
    for k, (sh, hd) in enumerate(((sh_f, hand2), (sh_n, hand))):
        e = ik(sh[0], sh[1], hd[0], hd[1], 3.4, 3.2, bend=1)
        z = -0.5 if k == 0 else 3.0
        r.tube([sh, e, hd], [1.2, 1.0, 0.9], "viol", z, bias=-0.3 if k == 0 else 0.1)
        r.ell(hd[0], hd[1], 1.0, 1.0, "flesh", z + 0.05)
        r.dot(e[0], e[1], "gold", 3, z + 0.06)
    if orb:
        x, y, k = orb
        r.ell(x, y, 1.8 + k * 0.5, 1.8 + k * 0.5, "glow", 4.0)
        r.dot(x - 0.5, y - 0.5, "white", 4, 4.1)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    s = r.resolve()
    if fade:
        s = recolor(s, "glow", keep_alpha_every=2)
    return s


PROPHECY_D = [0.12, 0.12, 0.12, 0.36, 0.36, 0.36, 0.16, 0.08, 0.08, 0.06, 0.16]


def oracle_cast(k):
    """Frames of her cast (shared by her Prophecy and the ghost that acts it out first)."""
    O = oracle
    return [O(hand=(4.0, -24.0), hand2=(-3.0, -24.0), face="open", hover=5.0),
            O(hand=(10.0, -18.0), hand2=(8.0, -21.0), face="open", lean=8, orb=(12.0, -20.0, 1), hover=4.5),
            O(hand=(12.0, -17.0), hand2=(10.0, -19.0), face="open", lean=12, spark=[(15.0, -19.0, 1)], hover=4.0,
              smear=[("arc", 4.0, -18.0, 9.0, -120, -10, "glow", 2)]),
            O(hand=(8.0, -18.0), hand2=(-4.0, -19.0), lean=4)][k]


def oracle_sheet(outdir):
    O = oracle
    idle = [O(hover=4.0 + [0, 0.5, 1.0, 0.5][i], hand=(6.0, -18.0 - [0, 0.5, 1.0, 0.5][i]), hand2=(-5.0, -18.0 - [0, 0.5, 1.0, 0.5][i]))
            for i in range(4)]
    run = [O(hover=4.5 + 0.5 * math.sin(i), lean=10, hand=(5.0, -17.0), hand2=(-6.0, -17.0)) for i in range(6)]
    # Gaze: the third eye flares (0-2), an orb looses from it at (9, -32) (3), settle (4-6)
    gaze = [O(face="open"), O(face="open", hand=(4.0, -22.0), spark=[(1.0, -33.0, 2)]), O(face="open", hand=(4.0, -23.0), spark=[(1.0, -33.0, 1)]),
            O(face="open", lean=6, orb=(8.0, -32.0, 1)), O(lean=3), O(), O()]
    # Prophecy: raises her hands, the third eye opens (0-2: the ghost appears on 2), trance (3-5), she fades out (6-7: blinks
    # to the ghost's spot on 7), appears (8), casts the fan exactly as the ghost did (9), settles (10)
    proph = [O(hand=(3.0, -22.0), hand2=(-3.0, -22.0), face="open"), O(hand=(4.0, -26.0), hand2=(-3.0, -26.0), face="open", hover=5.0),
             O(hand=(4.0, -27.0), hand2=(-3.0, -27.0), face="open", hover=5.5, spark=[(1.0, -36.0, 1)])]
    proph += [O(hand=(4.0, -27.0 + [0, 0.5, 0][i]), hand2=(-3.0, -27.0 + [0.5, 0, 0.5][i]), face="open", hover=5.5 + [0, 0.5, 0][i],
                spark=[(1.0, -36.0, 2)]) for i in range(3)]
    proph += [O(hand=(4.0, -24.0), hand2=(-3.0, -24.0), face="open", hover=5.0, fade=True),
              O(hand=(4.0, -24.0), hand2=(-3.0, -24.0), face="open", hover=5.0, fade=True,
                extra=lambda r: [r.dot(x, y, "glow", 3, 9) for (x, y) in ((-6, -10), (6, -14), (-4, -26), (5, -30))]),
              oracle_cast(0), oracle_cast(2), oracle_cast(3)]
    d0 = O(face="shut", lean=-12, hand=(2.0, -24.0), hand2=(-8.0, -22.0))
    d1 = O(face="shut", lean=-30, hover=1.0, hand=(-1.0, -16.0), hand2=(-10.0, -14.0))
    d2 = _oracle_corpse(0)
    corpse = _oracle_corpse(1)
    knock = O(face="shut", lean=-14, hand=(2.0, -22.0), hand2=(-8.0, -21.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Gaze", gaze, [0.12, 0.1, 0.1, 0.06, 0.12, 0.12, 0.14]),
             ("Prophecy", proph, PROPHECY_D)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxOracle", anims, outdir, scale=4)


def oracle_ghost(outdir):
    """FxJinxOracleGhost Act: her violet ghost acting out the cast she will make (appear, wind up, the fan looses on
    frame ACT_RELEASE, fade). Same cell and feet as JinxOracle so it sits exactly where she will stand."""
    b = BUILT["JinxOracle"]
    cw, ch = b["cell"]; feet = b["feet"]
    O = oracle
    fr = [O(hand=(3.0, -22.0), hand2=(-3.0, -22.0), face="open", hover=5.0, fade=True),
          O(hand=(4.0, -24.0), hand2=(-3.0, -24.0), face="open", hover=5.0, fade=True),
          recolor(oracle_cast(0), "glow", 2), recolor(oracle_cast(1), "glow", 2), recolor(oracle_cast(2), "glow", 2),
          recolor(oracle_cast(3), "glow", 3), recolor(oracle_cast(3), "glow", 2)]
    # timing: the ghost's release (frame 4) comes exactly 1.0 s before hers (Prophecy frame 9 starts at sum(PROPHECY_D[:9]))
    d = [0.12, 0.14, 0.14, 0.12, 0.1, 0.16, 0.2]
    anims = [("Act", fr, d)]
    img, man = pack("FxJinxOracleGhost", anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, "FxJinxOracleGhost_preview.png"), scale=4)
    BUILT["FxJinxOracleGhost"] = {"cell": (cw, ch), "feet": feet, "anims": [("Act", len(fr), d)]}
    print("built FxJinxOracleGhost  cell %dx%d" % (cw, ch))


def _oracle_corpse(stage):
    r = Rig()
    r.ell(4.0, -1.6, 7.0, 1.8, "crim", 0.0)
    r.poly([(-10.0, -0.4), (2.0, -0.4), (1.0, -4.6), (-9.0, -3.6)], "viol", 0.5)
    r.stamp("""
..dvvvvvdV
dvaWmWavLv
dvWmWmWvdv
..dvvvvvd.
""", -14.0, -0.6, 1.0, ORA_LEG, pivot=(5, 3))
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.8)
    return r.resolve()


# ================================================================== ONE-ARMED BANDIT
REEL_SYM = {"cherry": ("eye", 3), "bell": ("gold", 4), "skull": ("ivory", 4), "seven": ("crim", 3), "blur": ("glass", 3)}


def bandit(bob=0.0, tilt=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), lever=-70.0, reels=("seven", "seven", "seven"), lamp=False,
           mouth=0, smear=None, spark=None, dust=None, extra=None, coins=(), jam=False):
    r = Rig()
    by = -3.0 + bob
    for k, f in enumerate(feet):
        r.tube([(f[0] * 0.8, by), (f[0], f[1] - 1.0)], [1.0, 0.8], "gold", -1.0 if k == 0 else 1.0, bias=-0.3 if k == 0 else 0.1)
        r.poly([(f[0] - 1.6, f[1] - 1.2), (f[0] + 2.2, f[1] - 1.0), (f[0] + 2.4, f[1]), (f[0] - 1.6, f[1])], "gold", 1.1, bias=0.1)
    W, H = 13.0, 16.0
    bl, br, tr, tl = box3(r, -W / 2, by, W, H, 4.0, "crim", 1.0, side="coat", ang=tilt, pivot=(0.0, by))
    T = Xf(tilt, (0.0, by))
    r.polyline([tl, tr], "gold", 1.1, tone=3); r.polyline([bl, br], "gold", 1.1, tone=1)
    r.polyline([bl, tl], "gold", 1.1, tone=2); r.polyline([br, tr], "gold", 1.1, tone=1)
    # the reel window: glass with three reels
    wx0, wy0 = -5.0, by - 12.0
    r.poly([T(wx0, wy0 - 3.0), T(wx0 + 10.0, wy0 - 3.0), T(wx0 + 10.0, wy0 + 3.0), T(wx0, wy0 + 3.0)], "glass", 1.2, normal=(-0.3, -0.3, 1.0))
    for i, sym in enumerate(reels):
        cx, cy = T(wx0 + 1.8 + i * 3.2, wy0)
        m, t = REEL_SYM[sym]
        if sym == "blur":
            for dy in (-2, -1, 0, 1, 2): r.dot(cx, cy + dy, "glass", 4 if dy % 2 else 2, 1.3)
            r.dot(cx + 1, cy, "glass", 3, 1.3)
        elif sym == "seven":
            r.polyline([(cx - 1, cy - 1.5), (cx + 1, cy - 1.5), (cx - 0.5, cy + 1.5)], m, 1.3, tone=t)
        elif sym == "skull":
            r.ell(cx, cy - 0.4, 1.2, 1.1, m, 1.3, flat=t); r.dots([(cx - 0.5, cy - 0.5), (cx + 0.5, cy - 0.5)], "blk", 0, 1.31)
            r.dot(cx, cy + 1, m, 3, 1.3)
        elif sym == "bell":
            r.poly([(cx - 1.2, cy + 1.2), (cx + 1.2, cy + 1.2), (cx + 0.6, cy - 1.2), (cx - 0.6, cy - 1.2)], m, 1.3, flat=t)
        else:
            r.dots([(cx - 0.7, cy + 0.6), (cx + 0.7, cy + 0.8)], m, t, 1.3); r.line(cx - 0.5, cy - 0.2, cx + 0.8, cy - 1.6, "felt", 1.3, tone=3)
        if i < 2: r.line(*T(wx0 + 3.4 + i * 3.2, wy0 - 3.0), *T(wx0 + 3.4 + i * 3.2, wy0 + 3.0), "gold", 1.31, tone=1)
    r.polyline([T(wx0, wy0 - 3.0), T(wx0 + 10.0, wy0 - 3.0), T(wx0 + 10.0, wy0 + 3.0), T(wx0, wy0 + 3.0), T(wx0, wy0 - 3.0)], "gold", 1.32,
               tone=3)
    # the SPIN lamp on top, and the coin-slot mouth
    lx, ly = T(0.5, by - H - 2.6)
    r.ell(lx, ly, 2.0, 1.6, "fire" if lamp else "rdie", 1.4, bias=0.2, flat=3 if lamp else None)
    if lamp:
        for (dx, dy) in ((-3, 0), (3, 0), (0, -3), (-2, -2), (2, -2)): r.dot(lx + dx, ly + dy, "fire", 4, 1.5)
    mx, my = T(-0.5, by - 5.0)
    r.poly([(mx - 3.0, my - 0.6 - mouth), (mx + 3.0, my - 0.6 - mouth), (mx + 3.0, my + 0.6 + mouth), (mx - 3.0, my + 0.6 + mouth)],
           "blk", 1.4, flat=0)
    r.polyline([(mx - 3.4, my - 1.2 - mouth), (mx + 3.4, my - 1.2 - mouth)], "gold", 1.45, tone=3)
    if mouth: r.dots([(mx - 1.5, my - mouth + 0.4), (mx + 1.0, my - mouth + 0.4)], "gold", 4, 1.5)
    r.dots([T(-4.5, by - 2.0), T(4.5, by - 2.0)], "gold", 3, 1.4)
    # the lever arm: from the side, a long arm with a red ball knob
    px, py = T(W / 2 + 2.6, by - 9.0)
    a = math.radians(lever)
    kx, ky = px + 11.0 * math.cos(a), py + 11.0 * math.sin(a)
    r.ell(px, py, 1.6, 1.6, "gold", 1.6)
    r.tube([(px, py), (kx, ky)], [1.0, 0.8], "steel", 1.7, bias=0.1)
    r.ell(kx, ky, 2.4, 2.4, "rdie", 1.8, bias=0.15)
    for (x, y, k) in coins:
        r.ell(x, y, 1.2 if k else 0.6, 1.2, "gold", 5.0, bias=0.2)
    if jam:
        for (x, y) in ((-3, -22), (3, -23), (6, -19)): r.dot(x, y + by + 3, "smoke", 3, 6)
    smears(r, smear); sparks(r, spark)
    if dust: dust_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def bandit_sheet(outdir):
    B = bandit
    sy = ("cherry", "bell", "skull", "seven")
    idle = [B(bob=[0, -0.3, -0.5, -0.3][i], lever=-70 + [0, 3, 5, 3][i], lamp=i == 2, reels=(sy[i % 4], sy[(i + 1) % 4], sy[(i + 2) % 4]) if False else ("seven", "bell", "cherry"))
            for i in range(4)]
    run = [B(bob=-0.6 * abs(math.sin(i / 6 * math.tau)), tilt=4 * math.sin(i / 6 * math.tau), lever=-65 + 10 * math.sin(i),
             feet=((-4.0 + 2 * math.cos(i / 6 * math.tau), -max(0, 1.5 * math.sin(i / 6 * math.tau))), (4.0 - 2 * math.cos(i / 6 * math.tau), -max(0, -1.5 * math.sin(i / 6 * math.tau)))),
             reels=("seven", "bell", "cherry")) for i in range(6)]
    # Slam: lever cocked high (0-2), SLAMS down: the knob hits the floor at (20, -3) (3), shudder (4), lever back up (5-6)
    slam = [B(lever=-90, tilt=-3), B(lever=-115, tilt=-6, mouth=1), B(lever=-125, tilt=-8, mouth=1),
            B(lever=15, tilt=8, mouth=1, smear=[("arc", 9.0, -12.0, 11.0, -110, 10, "white", 2)], spark=[(20.0, -2.0, 1)], dust=(20.0, 0.0, 0, 1.2)),
            B(lever=20, tilt=6, dust=(20.0, 0.0, 1, 1.4)), B(lever=-30, tilt=2), B()]
    # Jackpot: grabs the lever (0), PULLS (1), reels spin, SPIN lamp lit (2-7: hit it now and it tilts), reels stop (8), pays (9)
    jp = [B(lever=-90, lamp=True), B(lever=20, lamp=True, mouth=1, reels=("blur",) * 3, tilt=4)]
    jp += [B(lever=-60 + 5 * (i % 2), lamp=i % 2 == 0, reels=("blur",) * 3, bob=-0.4 * (i % 2), tilt=[-2, 2][i % 2]) for i in range(6)]
    jp += [B(lever=-70, lamp=True, reels=("seven", "seven", "blur"), mouth=1),
           B(lever=-70, lamp=False, reels=("seven", "seven", "seven"), mouth=2, coins=[(-1.0, -9.0, 1), (2.0, -11.0, 0), (-3.0, -12.0, 1)])]
    jam = [B(lever=-30 + 10 * (i % 2), tilt=[-8, -4, -10, -6][i], reels=("skull", "skull", "skull"), jam=True, lamp=i % 2 == 0,
             spark=[(6.0 - 2 * i, -18.0, 2)]) for i in range(4)]
    d0 = B(tilt=-10, reels=("skull", "blur", "skull"), lever=-120, mouth=1)
    d1 = B(tilt=-35, reels=("skull", "skull", "skull"), lever=170, mouth=2, coins=[(8.0, -6.0, 1), (12.0, -3.0, 0)])
    d2 = _bandit_corpse(0)
    corpse = _bandit_corpse(1)
    knock = B(tilt=-14, lever=-110, reels=("blur", "seven", "blur"), mouth=1)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Slam", slam, [0.12, 0.12, 0.12, 0.05, 0.12, 0.12, 0.14]),
             ("Jackpot", jp, [0.12, 0.08] + [0.07] * 6 + [0.14, 0.16]),
             ("Jam", jam, [0.08] * 4)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxBandit", anims, outdir, scale=4)


def _bandit_corpse(stage):
    r = Rig()
    box3(r, -9.0, 0.0, 16.0, 9.0, 3.0, "crim", 1.0, side="coat")
    r.poly([(-6.0, -5.5), (0.0, -5.5), (0.0, -2.5), (-6.0, -2.5)], "glass", 1.2)
    for i, x in enumerate((-5.0, -3.0, -1.0)):
        r.ell(x, -4.0, 0.8, 0.8, "ivory", 1.3, flat=4)
    r.tube([(8.0, -4.0), (16.0, -1.5)], [0.9, 0.8], "steel", 1.5)
    r.ell(17.0, -1.8, 2.0, 2.0, "rdie", 1.6)
    for k in range(5 if stage else 3):
        r.ell(-14.0 + k * 2.6, -0.8, 1.1, 0.7, "gold", 2.0, bias=0.2)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.8)
    return r.resolve()


# ================================================================== BIG-TOP CHIMERA
CHIM_LEG = {"d": ("mane", 1), "m": ("mane", 2), "M": ("mane", 3), "L": ("mane", 4), "k": ("blk", 0), "e": ("fire", 4),
            "h": ("horn", 2), "H": ("horn", 3), "i": ("ivory", 4), "n": ("crim", 2), "w": ("ivory", 3)}
CHIM_HEAD = {
    # pivot (2, 7): where the neck meets the head. Goat horns curling back, a lion's muzzle, yellow eyes
    "calm": """
.hH......
hH.hH....
h..dMMd..
..dMMMMd.
.dMeMMMLL
.dMMMMMLw
..dMMnMkk
...dMMMd.
""",
    "roar": """
.hH......
hH.hH....
h..dMMd..
..dMMMMd.
.dMeMMMLL
.dMMMMkkw
..dMMkni.
...dMMkiw
""",
    "dead": """
.........
.hH......
hH.dMMd..
h.dMMMMd.
.dMkMMMLL
.dMMMMMLw
..dMMMMkk
...dMMMd.
""",
}


def mane_tufts(r, cx, cy, rad, z, burn=0, phase=0):
    import random
    rnd = random.Random(int(phase * 7) + 3)
    r.ell(cx, cy, rad, rad * 1.1, "wood", z, bias=0.05)
    for i in range(9):
        a = math.radians(100 + i * 25)
        x, y = cx + rad * math.cos(a), cy + rad * 1.1 * math.sin(a)
        r.ell(x, y, 1.7, 1.7, "wood", z + 0.01, bias=0.05 + 0.1 * (i % 2))
        if burn and math.sin(a) < 0.3:
            for k in range(burn + 1 + rnd.randint(0, 1)):
                r.dot(x + rnd.choice((-1, 0, 1)), y - 1.5 - k, "fire", 4 - min(2, k), z + 0.3)
                if k == 0: r.dot(x + rnd.choice((-1, 1)), y - 1.0, "ember", 3, z + 0.29)


def chimera(lean=0.0, bob=0.0, legs=None, head=(9.0, -14.0), face="calm", tail=0.0, burn=0, phase=0, smear=None, spark=None,
            extra=None, body_dy=0.0, claw=None):
    r = Rig()
    by = -9.0 + bob + body_dy
    legs = legs or [(-8.0, 0.0), (-5.0, 0.0), (5.0, 0.0), (8.0, 0.0)]
    T = Xf(lean, (0.0, by))
    hips = [T(-7.0, by + 1.0), T(-6.0, by + 1.0), T(5.0, by + 1.0), T(6.5, by + 1.0)]
    for k, ((fx, fy), hp) in enumerate(zip(legs, hips)):
        far = k in (0, 2)
        kn = ik(hp[0], hp[1], fx, fy - 1.0, 4.4, 4.0, bend=1 if k < 2 else -1)
        z = -1.0 if far else 1.0
        r.tube([hp, kn, (fx, fy - 1.0)], [2.0, 1.4, 1.2], "mane", z, bias=-0.35 if far else 0.0)
        r.ell(fx + 0.8, fy - 0.8, 1.6, 0.9, "mane", z + 0.01, bias=-0.2 if far else 0.15)
    # the snake tail, with its own head
    tp = chain(*T(-9.0, by - 1.0), [(3.0, 200 + tail), (3.0, 240 + tail), (3.0, 280 + tail * 0.5), (2.6, 320 + tail * 0.5)])
    r.tube(tp, [1.4, 1.2, 1.0, 0.9, 0.8], band_mat(2.4), -1.5, bias=0.0)
    ex, ey = tp[-1]
    r.ell(ex + 1.0, ey - 0.4, 1.6, 1.2, "jade", -1.4, bias=0.1); r.dot(ex + 1.4, ey - 0.8, "eye", 3, -1.35)
    # body: a long lion barrel with a tamer's harness
    r.ell(*T(-0.5, by - 2.6), 9.0, 4.4, "mane", 0.0, bias=0.05)
    r.ell(*T(-0.5, by - 0.4), 7.0, 1.8, "mane", 0.05, bias=-0.15)
    for x in (-3.0, 2.5):
        r.polyline([T(x, by - 6.8), T(x + 0.6, by + 1.2)], "crim", 0.2, tone=2)
        r.dot(*T(x + 0.3, by - 3.0), "gold", 4, 0.25)
    r.polyline([T(-8.0, by - 3.0), T(6.0, by - 3.4)], "crim", 0.2, tone=1)
    # mane and head
    hx, hy = head
    mane_tufts(r, hx - 3.0, hy + 1.0, 4.6, 1.5, burn=burn, phase=phase)
    r.stamp(CHIM_HEAD[face], hx, hy, 2.5, CHIM_LEG, pivot=(2, 7))
    if burn:
        for (dx, dy) in ((-6, -6), (-2, -8), (-8, -2)):
            r.dot(hx + dx, hy + dy - phase % 2, "ember", 3, 2.8)
    if claw:
        x, y = claw
        r.ell(x, y, 2.0, 1.6, "mane", 3.0, bias=0.15)
        for k in range(3): r.dot(x + 2 + 0.5 * k, y - 1 + k, "ivory", 4, 3.1)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def chimera_sheet(outdir):
    C = chimera

    def stance(burn):
        idle = [C(bob=[0, 0.4, 0.8, 0.4][i], tail=[0, 10, 20, 10][i], head=(9.0, -14.0 + [0, 0.4, 0.8, 0.4][i]), burn=burn, phase=i)
                for i in range(4)]
        run = []
        for i in range(6):
            ph = i / 6 * math.tau
            s1, s2 = math.cos(ph), math.cos(ph + math.pi)
            run.append(C(lean=-4 * math.sin(ph), bob=-1.2 * abs(math.sin(ph)), tail=-20 + 15 * math.sin(ph), burn=burn, phase=i,
                         legs=[(-8.0 + 3 * s1, -max(0, 2 * math.sin(ph))), (-5.0 + 3 * s2, -max(0, -2 * math.sin(ph))),
                               (5.0 + 3 * s1, -max(0, 2 * math.sin(ph + 1))), (8.0 + 3 * s2, -max(0, -2 * math.sin(ph + 1)))],
                         head=(10.0, -13.5 - abs(math.sin(ph)))))
        return idle, run
    idle, run = stance(0)
    bidle, brun = stance(2)
    # Maul: rears (0-1), the paw rakes down (2 smear, 3 HIT: x 15..24, y -9..-2), follow (4), recover (5-6)
    maul = [C(lean=-8, head=(8.0, -17.0), face="roar"), C(lean=-16, head=(7.0, -20.0), face="roar", legs=[(-8.0, 0.0), (-5.0, 0.0), (6.0, -6.0), (9.0, -8.0)],
                                                       claw=(12.0, -18.0)),
            C(lean=-4, head=(11.0, -15.0), face="roar", claw=(17.0, -11.0), smear=[("arc", 10.0, -10.0, 9.0, -110, 20, "white", 2)]),
            C(lean=6, head=(12.0, -12.0), face="roar", claw=(20.0, -5.0), spark=[(22.0, -4.0, 1)], legs=[(-8.0, 0.0), (-5.0, 0.0), (6.0, 0.0), (11.0, -2.0)]),
            C(lean=4, head=(11.0, -12.5), claw=(18.0, -3.0)), C(head=(10.0, -13.5)), C()]
    # Leap: crouch (0-1), LEAP (2-4: untouchable in the air, body stretched), LAND in the ring (5), recover (6-8)
    leap = [C(body_dy=2.0, head=(9.0, -11.0), face="roar"), C(body_dy=3.0, head=(9.0, -10.0), face="roar", lean=4),
            C(body_dy=-10.0, lean=-14, head=(12.0, -26.0), face="roar", legs=[(-12.0, -6.0), (-10.0, -7.0), (10.0, -14.0), (13.0, -16.0)], tail=-30),
            C(body_dy=-14.0, lean=0, head=(12.0, -27.0), face="roar", legs=[(-12.0, -11.0), (-10.0, -12.0), (12.0, -12.0), (14.0, -13.0)], tail=-40),
            C(body_dy=-8.0, lean=14, head=(12.0, -19.0), face="roar", legs=[(-10.0, -8.0), (-8.0, -9.0), (10.0, -3.0), (12.0, -4.0)], tail=-20),
            C(body_dy=1.5, head=(10.0, -12.0), face="roar", spark=[(0.0, -2.0, 1)], extra=lambda r: dust_puff(r, 0.0, 0.0, 0, 2.0)),
            C(body_dy=1.0, head=(10.0, -12.5), extra=lambda r: dust_puff(r, 0.0, 0.0, 1, 2.2)), C(body_dy=0.5), C()]
    d0 = C(face="roar", lean=-12, head=(7.0, -18.0))
    d1 = C(face="dead", lean=10, body_dy=3.0, head=(10.0, -8.0), legs=[(-9.0, 0.0), (-6.0, -1.0), (5.0, 0.0), (9.0, -1.0)])
    d2 = _chimera_corpse(0)
    corpse = _chimera_corpse(1)
    knock = C(face="roar", lean=-14, head=(7.0, -17.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.07] * 6),
             ("Maul", maul, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Leap", leap, [0.12, 0.1, 0.09, 0.09, 0.08, 0.1, 0.12, 0.12, 0.12]),
             ("IdleBurn", bidle, [0.12] * 4), ("RunBurn", brun, [0.07] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxChimera", anims, outdir, scale=4)


def _chimera_corpse(stage):
    r = Rig()
    r.ell(0.0, -3.0, 10.0, 3.2, "mane", 0.0)
    for (x, up) in ((-6.0, 3.0), (-3.0, 4.0), (4.0, 3.0), (7.0, 4.0)):
        r.tube([(x, -5.0), (x + 1.0, -5.0 - up), (x + 2.0, -5.5 - up)], [1.4, 1.0, 0.9], "mane", 0.5)
    mane_tufts(r, 11.0, -3.0, 3.6, 1.0)
    r.stamp(CHIM_HEAD["dead"], 13.0, 0.0 if stage else -1.0, 1.5, CHIM_LEG, pivot=(2, 7))
    r.tube([(-10.0, -2.0), (-14.0, -1.0), (-17.0, -0.6)], [1.2, 1.0, 0.8], band_mat(2.4), 0.3)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 2.0)
    return r.resolve()


# ================================================================== registry
JOBS = [("JinxGorgon", gorgon_sheet), ("JinxCardKing", king_sheet), ("JinxHouseOfCards", house_sheet), ("JinxTwenty", twenty_sheet),
        ("JinxNutcracker", nut_sheet), ("JinxPuppeteer", puppeteer_sheet), ("JinxOracle", oracle_sheet),
        ("FxJinxOracleGhost", oracle_ghost), ("JinxBandit", bandit_sheet), ("JinxChimera", chimera_sheet)]
SYNC = {
    "JinxGorgon": {"Lash": [("HIT: snake heads x 7..25, y -24..-8", 3)], "Stare": [("eyes kindle (the tell)", 2), ("the beam fires from (5, -30)", 4)]},
    "JinxCardKing": {"Smash": [("SMASH: the club lands at x 24..30 on the floor", 3)], "Court": [("the Diamonds card is up: guard on", 3)]},
    "JinxHouseOfCards": {"Topple": [("SLAP: the top tier lands x 4..20", 3)], "Storm": [("the six cards whirl out: storm cast", 4)],
                         "WhirlSlash": [("the whirl cuts all round", 2)]},
    "JinxTwenty": {"Ram": [("HIT: facets at (13, -9) .. (19, -15)", 3)], "Crit": [("leaps", 1), ("lands: the roll", 6)]},
    "JinxNutcracker": {"Sabre": [("HIT: the cut, x 1..23, y -25..-3", 3)], "Crack": [("lunge", 3), ("CLAMP: the grab", 4), ("CRUNCH", 6)]},
    "JinxPuppeteer": {"Dance": [("STAB: knives at (15-23, -4..-13)", 3)], "Curtain": [("YANK: the allies are hauled", 3)]},
    "JinxOracle": {"Gaze": [("orb leaves the third eye at (9, -32)", 3)],
                   "Prophecy": [("the ghost appears (FxJinxOracleGhost)", 2), ("she blinks to the ghost's spot", 7), ("the fan looses", 9)]},
    "JinxBandit": {"Slam": [("SLAM: the knob lands at (20, -3)", 3)], "Jackpot": [("reels spinning: a hit now tilts it", 2), ("pay out", 8)]},
    "JinxChimera": {"Maul": [("HIT: claws x 15..24, y -9..-2", 3)], "Leap": [("airborne (invulnerable)", 2), ("LAND: ring of fire", 5)]},
}
NOTES = {
    "JinxCardKing": "CourtIdle/CourtRun: the stance while Hold Court is up (card raised, crown glowing).",
    "JinxHouseOfCards": "Idle/Run/Topple/Storm = 3 tiers; Idle2/Run2/Topple2/Storm2 and Idle1/Run1/Topple1/Storm1 after each lost "
                        "tier; Whirl/WhirlRun/WhirlSlash/Storm0 at 0 tiers (Storm0 casts on frame 3).",
    "JinxTwenty": "Fumble (4) loops while a natural 1 has it dazed.",
    "JinxNutcracker": "IdleSlow/RunSlow: the key running down (the tell); Rewind loops while it is frozen rewinding.",
    "JinxOracle": "FxJinxOracleGhost Act: same cell/feet as JinxOracle; its fan looses on frame 4 at 0.52 s, exactly 1.0 s before "
                  "her own (Prophecy frame 9 at 1.52 s after the ghost spawns on frame 2).",
    "JinxBandit": "Jam (4) loops while it has been tilted (three skulls).",
    "JinxChimera": "IdleBurn/RunBurn: the mane alight (Last Act, below half health).",
}
