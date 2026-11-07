"""Bel'Mora tier 3, part one: The Drowned Bell, Drowned Captain, Crown of Thorns, Brood Urchin, Tide Matriarch, Jelly
Siren. Built through belmora_v2_rigs.py. T3 idle limit 42 x 40."""
import math
from belmora_v2_rigs import (Rig, Xf, chain, ik, lerp, eye, spines, foam_ring, drips, bubbles, barnacles, leg, crab_legs,
                             claw, fin, kelp_strand, bell_shape, dust, splash, star, arc_smear, sheet, tail_anims, legend)
from belmora_v2_t2 import chain_links, wave_pts


def tentacle(r, pts, r0, mat, z, suckers=None, bias=0.0):
    """A tapering tentacle along pts; suckers: a material for a row of sucker dots on its underside."""
    n = len(pts)
    radii = [max(0.4, r0 * (1.0 - i / (n - 1.0) * 0.85)) for i in range(n)]
    r.tube(pts, radii, mat, z, bias=bias)
    if suckers:
        for i in range(1, n - 1, 2):
            r.dot(pts[i][0] + 0.5, pts[i][1] + radii[i] * 0.6, suckers, 2, z + 0.01)


def curl(x, y, ang, ln, bend, n=7):
    """Points of a curling limb: starts at (x, y) heading ang (deg), turning `bend` deg per step."""
    pts = [(x, y)]
    a = ang
    step = ln / float(n)
    for i in range(n):
        x += math.cos(math.radians(a)) * step; y += math.sin(math.radians(a)) * step
        pts.append((x, y)); a += bend
    return pts


# ================================================================== THE DROWNED BELL
GIANT_LEG = legend(k="drown:0", d="drown:1", s="drown:2", S="drown:3", L="drown:4", e="lure:3", E="lure:4", m="drown:0",
                   t="tent:2", T="tent:3", w="ivory:2")
GIANT_FACE = {
    # pivot (4, 3): a bloated, waterlogged face under a heavy brow, glowing cyan eyes, slack mouth
    "slack": """
.dsSSsd.
dsSLLSsd
smeSSems
sSSSSSSd
dsmmmmsd
.dsttsd.
""",
    "roar": """
.dsSSsd.
dsSLLSsd
sEeSSeEs
sSSmmSSd
dsmmmmsd
.dmttmd.
""",
    "hurt": """
.dsSSsd.
dsSLLSsd
smmSSmms
sSSSSSSd
dsmsmmsd
.dsttsd.
""",
}


def drowned_bell(lean=0.0, bob=0.0, feet=((-6.0, 0.0), (5.0, 0.0)), hand=(11.0, -12.0), hand2=(-2.0, -10.0), bell=True,
                 bell_at=None, bell_tilt=-18.0, face="slack", tent_k=0, crouch=0.0, smear=None, extra=None, ring=0,
                 bell_mouth_down=False):
    """A hunched, waterlogged giant under a huge cracked church bell (on his back, its mouth to the rear with violet
    tentacles hanging out of it). bell=False: his raw hunched back and the tentacles hanging from his shoulders.
    bell_at=(x, base, tilt): the bell held elsewhere (lifted, swung, thrown)."""
    r = Rig()
    hipy = -10.0 + bob + crouch
    T = Xf(lean, (0.0, hipy))
    # thick legs, bloated grey skin, bare feet
    for k, (fx, fy) in enumerate(feet):
        hip = T(-3.0 + k * 6.0, hipy)
        z = 1.0 if k else -1.0
        kn = ik(hip[0], hip[1], fx, fy - 1.0, 5.6, 5.0, bend=1)
        r.tube([hip, kn, (fx, fy - 1.0)], [3.4, 2.8, 2.4], "drown", z, bias=-0.3 if not k else 0.0)
        r.ell(fx + 1.0, fy - 1.0, 3.2, 1.4, "drown", z + 0.01, bias=-0.1 if k else -0.4)
        for t in range(3): r.dot(fx + 2.5 + t * 0.0, fy - 0.5 - t * 0.0, "drown", 1, z + 0.02) if t == 0 else None
    # the body: a huge hunched barrel leaning forward
    bx, by = T(1.0, hipy - 8.0)
    r.ell(bx, by, 11.5, 10.0, "drown", 0.0)
    r.ell(*T(4.0, hipy - 3.0), 6.0, 4.5, "drown", 0.05, bias=-0.05)               # belly
    for (dx, dy) in ((-3, -12), (2, -14), (5, -9), (-5, -6), (6, -5)): r.dot(*T(dx, hipy + dy), "drown", 1, 0.06)   # bloat folds
    barnacles(r, [T(-5.0, hipy - 13.0), T(-2.0, hipy - 15.5)], 0.07)
    # far arm
    sh2 = T(-3.0, hipy - 13.0)
    el2 = ik(sh2[0], sh2[1], hand2[0], hand2[1], 5.0, 4.8, bend=1)
    r.tube([sh2, el2, hand2], [2.2, 2.0, 1.9], "drown", -1.5, bias=-0.35)
    r.ell(hand2[0], hand2[1], 2.2, 2.0, "drown", -1.45, bias=-0.3)
    if not bell:
        # bare: tentacles hang loose from his shoulders and raw back
        for i in range(4):
            sx, sy = T(-6.0 + i * 2.5, hipy - 15.0 + abs(i - 1.5))
            pts = curl(sx, sy, 110 + i * 15, 8 + i, 8 * math.sin(tent_k + i), n=6)
            tentacle(r, pts, 1.3, "tent", -0.5 + i * 0.01, bias=0.05)
        for (dx, dy) in ((-4, -16), (-1, -17), (2, -16)): r.dot(*T(dx, hipy + dy), "pink", 2, 0.08)   # raw sores
    # the head: low, forward, under the bell's rim
    hx, hy = T(8.5, hipy - 13.0)
    r.stamp(GIANT_FACE[face], hx, hy, 3.0, GIANT_LEG, pivot=(4, 3))
    # the bell
    if bell or bell_at:
        if bell_at:
            cx, base, tl = bell_at
        else:
            cx, base, tl = T(-6.5, hipy + 1.5)[0], T(-6.5, hipy + 1.5)[1], bell_tilt + lean
        Tb = bell_shape(r, cx, base, 33.0, 30.0, 2.0 if bell_at is None else 3.5, tilt=tl, crack=True)
        # violet tentacles hanging from the bell's mouth
        for i in range(4):
            mx, my = Tb(cx - 9.0 + i * 5.5, base)
            pts = curl(mx, my, 95 + (i - 1.5) * 10, 6 + (i % 2) * 2, 10 * math.sin(tent_k * 0.9 + i), n=5)
            if pts[-1][1] > 0: pts = [(x, min(y, -0.5)) for (x, y) in pts]
            tentacle(r, pts, 1.2, "tent", 1.9 if bell_at is None else 3.4, bias=-0.05)
        if ring:
            for i in range(ring):
                rr = 15 + i * 3
                for a in range(-160, -10, 15):
                    aa = math.radians(a)
                    r.dot(cx + math.cos(aa) * rr, base - 12 + math.sin(aa) * rr * 0.75, "spark", 3 - i, 6.0)
    # near arm (over the body): a great slab of a forearm
    sh = T(5.0, hipy - 12.0)
    el = ik(sh[0], sh[1], hand[0], hand[1], 5.5, 5.0, bend=-1)
    r.tube([sh, el, hand], [2.6, 2.3, 2.2], "drown", 4.0)
    r.ell(hand[0], hand[1], 2.6, 2.3, "drown", 4.05)
    r.dot(hand[0] + 1.0, hand[1] - 1.0, "drown", 4, 4.1)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 5.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def bell_corpse(stage):
    r = Rig()
    r.ell(2.0, -4.5, 11.0, 4.5, "drown", 0.0, bias=-0.1)
    r.tube([(10, -3), (15, -2), (18, -1.5)], [2.4, 2.2, 2.0], "drown", 0.5, bias=-0.2)
    r.stamp(GIANT_FACE["hurt"], 12.0, -6.0, 1.0, GIANT_LEG, pivot=(4, 3))
    bell_shape(r, -9.0, -1.0, 22.0, 20.0, 1.5, tilt=-80 + stage * 4, crack=True)
    for i in range(3):
        tentacle(r, curl(-14.0 + i * 1.5, -6.0 + i * 3, 160 + i * 10, 7, 12, n=5), 1.1, "tent", 1.8)
    if stage == 0: dust(r, 0, 0, 1, 1.5)
    return r.resolve()


def bell_sheet(out):
    G = drowned_bell
    idle = [G(bob=[0, 0.4, 0.8, 0.4][i], tent_k=i, hand=(13.0, -12.0 + [0, 0.4, 0.8, 0.4][i])) for i in range(4)]
    run = []
    for i in range(6):
        s = math.sin(i / 6 * math.tau)
        run.append(G(lean=6, bob=[0, -0.8, -1.2, 0, -0.8, -1.2][i], tent_k=i * 1.5, feet=((-6.0 + 3 * s, -max(0, -s) * 2), (5.0 - 3 * s, -max(0, s) * 2)),
                     hand=(11.5 + s, -12.0), hand2=(-2.0 - s, -10.0), bell_tilt=-18 + 4 * s))
    # Toll (8): rock the bell up off his back (0-2), swing it over his head (3), slam it down in front mouth-first
    # (4: the ring at (19, 0)), the ring spreads (5), heave it back (6-7)
    toll = [G(lean=-8, bell_tilt=-30, hand=(8.0, -20.0), face="roar"),
            G(lean=-14, bell_at=(-6.0, -12.0, -50), hand=(4.0, -26.0), hand2=(-2.0, -24.0), face="roar"),
            G(lean=-6, bell_at=(2.0, -20.0, -10), hand=(8.0, -28.0), hand2=(4.0, -27.0), face="roar",
              smear=[((-14, -28), (-4, -36), "bronze", 2)]),
            G(lean=14, bell_at=(15.0, -10.0, 40), hand=(14.0, -22.0), hand2=(12.0, -21.0), face="roar", crouch=1.0,
              smear=[((4, -40), (16, -34), "bronze", 2), ((10, -38), (22, -26), "bronze", 1)]),
            G(lean=18, bell_at=(17.0, 0.0, 0), hand=(15.0, -14.0), hand2=(13.0, -13.0), face="roar", crouch=2.0, ring=1,
              extra=lambda r: dust(r, 19, 0, 0, 1.6)),
            G(lean=16, bell_at=(17.0, 0.0, 0), hand=(15.0, -14.0), hand2=(13.0, -13.0), crouch=2.0, ring=2,
              extra=lambda r: dust(r, 19, 0, 1, 2.0)),
            G(lean=4, bell_at=(4.0, -16.0, -20), hand=(9.0, -24.0), hand2=(5.0, -23.0), crouch=1.0),
            G(lean=0)]
    # Cast (9): heave the bell up off his back (0-3), HURL it (4: it leaves his hands at (12, -30); FxBelCastBell
    # takes over), follow-through (5), he is bare (6-8)
    cast = [G(lean=-6, bell_tilt=-30, hand=(8.0, -20.0), face="roar", crouch=1.0),
            G(lean=-12, bell_at=(-6.0, -14.0, -45), hand=(3.0, -26.0), hand2=(-3.0, -25.0), face="roar"),
            G(lean=-16, bell_at=(-4.0, -22.0, -20), hand=(1.0, -30.0), hand2=(-3.0, -29.0), face="roar"),
            G(lean=-18, bell_at=(-2.0, -24.0, -10), hand=(1.0, -32.0), hand2=(-2.0, -31.0), face="roar", bob=-1.0),
            G(lean=16, bell=False, hand=(14.0, -26.0), hand2=(11.0, -25.0), face="roar",
              smear=[((-6, -36), (8, -38), "bronze", 2), ((0, -38), (14, -34), "bronze", 1)]),
            G(lean=18, bell=False, hand=(15.0, -14.0), hand2=(12.0, -13.0), crouch=1.0, tent_k=1),
            G(lean=10, bell=False, hand=(12.0, -12.0), tent_k=2), G(lean=4, bell=False, tent_k=3), G(bell=False, tent_k=4)]
    # Bare: light and quick, the tentacles loose; Punch (6): a short jab, hit at (16, -14) on frame 2
    bare_i = [G(bell=False, bob=[0, 0.4, 0.8, 0.4][i], tent_k=i, hand=(11.0, -12.0 + [0, 0.4, 0.8, 0.4][i])) for i in range(4)]
    bare_r = []
    for i in range(6):
        s = math.sin(i / 6 * math.tau)
        bare_r.append(G(bell=False, lean=10, bob=[0, -1.0, -1.5, 0, -1.0, -1.5][i], tent_k=i * 1.5,
                        feet=((-6.0 + 4 * s, -max(0, -s) * 2.5), (5.0 - 4 * s, -max(0, s) * 2.5)), hand=(12.0 + s, -12.0)))
    punch = [G(bell=False, lean=-6, hand=(8.0, -16.0), face="roar"), G(bell=False, lean=12, hand=(17.0, -15.0), face="roar",
                                                                       smear=[((10, -15), (14, -15), "drown", 2)]),
             G(bell=False, lean=14, hand=(18.0, -14.0), face="roar", extra=lambda r: star(r, 21, -14, 1)),
             G(bell=False, lean=8, hand=(14.0, -13.0)), G(bell=False, lean=4, hand=(12.0, -12.0)), G(bell=False)]
    # Lift (8): bare, he stoops to the bell standing mouth-down in front of him (0-1), gets his arms under it (2),
    # heaves it up (3-5), swings it onto his back (6), and it TOLLS round him (7: ring at (0, 0))
    lift = [G(bell=False, lean=20, crouch=2.0, bell_at=(16.0, 0.0, 0), hand=(14.0, -8.0), hand2=(12.0, -9.0)),
            G(bell=False, lean=24, crouch=3.0, bell_at=(16.0, 0.0, 0), hand=(12.0, -4.0), hand2=(10.0, -5.0), face="roar"),
            G(bell=False, lean=20, crouch=3.0, bell_at=(15.0, -1.0, -6), hand=(11.0, -5.0), hand2=(9.0, -6.0), face="roar"),
            G(bell=False, lean=6, crouch=1.5, bell_at=(10.0, -10.0, -15), hand=(10.0, -16.0), hand2=(8.0, -15.0), face="roar"),
            G(bell=False, lean=-8, bell_at=(2.0, -20.0, -20), hand=(4.0, -28.0), hand2=(1.0, -27.0), face="roar"),
            G(bell=False, lean=-14, bell_at=(-4.0, -14.0, -40), hand=(2.0, -24.0), hand2=(-2.0, -23.0), face="roar"),
            G(lean=-4, bell_tilt=-26, face="roar", crouch=1.0),
            G(lean=4, crouch=2.0, face="roar", ring=2, extra=lambda r: [dust(r, -8, 0, 0, 1.4), dust(r, 10, 0, 0, 1.4)])]
    d0 = G(face="hurt", lean=-10, hand=(10.0, -18.0))
    d1 = G(face="hurt", lean=-25, crouch=4.0, bell_tilt=-50, hand=(8.0, -6.0))
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.1] * 6),
             ("Toll", toll, [0.14, 0.12, 0.1, 0.06, 0.06, 0.12, 0.12, 0.14]),
             ("Cast", cast, [0.12, 0.12, 0.12, 0.14, 0.06, 0.1, 0.12, 0.12, 0.14]),
             ("IdleBare", bare_i, [0.16, 0.14, 0.16, 0.14]), ("RunBare", bare_r, [0.07] * 6),
             ("Punch", punch, [0.1, 0.05, 0.06, 0.1, 0.1, 0.12]),
             ("Lift", lift, [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.2])]
    anims += tail_anims(idle[0], [d0, d1, bell_corpse(0), bell_corpse(1)], [0.1, 0.14, 0.16, 0.4],
                        G(face="hurt", lean=-12, hand=(10.0, -16.0), bob=-0.8))
    return sheet("BelDrownedBell", anims, out)


# ================================================================== DROWNED CAPTAIN
CAPT_LEG = legend(k="ivory:0", d="ivory:1", b="ivory:2", B="ivory:3", W="ivory:4", e="lure:3", E="lure:4", m="navy:0",
                  h="navy:1", H="navy:2", N="navy:3", g="bronze:3", G="bronze:4", r="coral:2", R="coral:3", K="kelp:2")
CAPT_HEAD = {
    # pivot (4, 7): the jaw. A bone face under a tricorn hat (navy, brass trim), cyan pinprick eyes, kelp in the brim.
    "grim": """
h..hHH..h
NhHNHHHhN
hHHNNNHHh
gGggggggK
.dbBBbd.
.bmBmeb.
.dbBBbd.
..bmmb..
...dd...
""",
    "shout": """
h..hHH..h
NhHNHHHhN
hHHNNNHHh
gGggggggK
.dbBBbd.
.bEBmEb.
.dbmmbd.
..bmmb..
...dd...
""",
    "hurt": """
h..hHH..h
NhHNHHHhN
hHHNNNHHh
gGggggggK
.dbBBbd.
.bmBmmb.
.dbBBbd.
..bdmb..
...dd...
""",
}


def captain(lean=0.0, bob=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), hand=(8.0, -15.0), hand2=(-5.0, -14.0), gaff_ang=-60.0,
            face="grim", coat_k=0, rope=None, smear=None, extra=None, crouch=0.0, grapple_hand=False, swing=False,
            coil=True, kick=None):
    """A drowned captain: a kelp-hung navy greatcoat with brass buttons and a red sash, a gaff hook in his near hand
    (aimed along gaff_ang), a coiled rope and grapple on his hip. rope=(x, y): a taut line from the far hand."""
    r = Rig()
    hipy = -13.0 + bob + crouch
    T = Xf(lean, (0.0, hipy))
    for k, (fx, fy) in enumerate(feet if not kick else (feet[0], kick)):
        hip = T(-1.8 + k * 3.6, hipy)
        z = 0.5 if k else -0.5
        kn = ik(hip[0], hip[1], fx, fy - 1.5, 6.0, 5.6, bend=1 if not (kick and k) else -1)
        r.tube([hip, kn, (fx, fy - 1.5)], [1.9, 1.6, 1.5], "navy", z, bias=-0.3 if not k else -0.1)
        r.ell(fx + 0.8, fy - 1.2, 2.6, 1.5, "lthr", z + 0.01, bias=-0.1)
    # the greatcoat: broad at the tails, kelp hanging off the hem
    hem = [T(-12.5 + i * 3.0, hipy + 8.0 + (1.0 if i % 2 else 0.0)) for i in range(9)]
    if swing: hem = [T(-12.5 + i * 3.0 - 2.0, hipy + 7.0 + (1.0 if i % 2 else 0.0)) for i in range(9)]
    r.poly([T(-6.0, hipy - 11.0), T(6.0, hipy - 11.0), T(11.5, hipy + 8.0)] + hem[::-1] + [T(-13.0, hipy + 8.0)], "navy", 0.0, curve=0.8)
    r.poly([T(-5.0, hipy - 10.5), T(-6.5, hipy - 8.0), T(-4.0, hipy - 8.5)], "navy", 0.02, bias=0.3)       # epaulette
    r.poly([T(5.0, hipy - 10.5), T(6.5, hipy - 8.0), T(4.0, hipy - 8.5)], "navy", 0.02, bias=0.2)
    for (a, b) in (((-6.5, -8.0), (-6.5, -7.0)), ((6.5, -8.0), (6.5, -7.0))):
        r.line(*T(a[0], hipy + a[1]), *T(b[0], hipy + b[1]), "bronze", 0.03, tone=3)
    for i in range(0, 9, 2):
        kelp_strand(r, hem[i][0], hem[i][1] - 0.5, 2 + (i + coat_k) % 3, 0.6, 0.05, k=coat_k + i)
    # lapels, brass buttons, the red sash
    for i in range(4): r.dot(*T(1.5, hipy - 8.0 + i * 2.0), "bronze", 4 if i % 2 == 0 else 3, 0.1)
    r.line(*T(-3.5, hipy - 9.5), *T(3.5, hipy - 1.5), "coral", 0.12, tone=3)
    r.line(*T(-3.5, hipy - 8.5), *T(3.5, hipy - 0.5), "coral", 0.12, tone=2)
    for (dx, dy) in ((-5, -2), (-3, 3), (4, 1)): r.dot(*T(dx, hipy + dy), "teal", 2, 0.08)        # rot patches
    # the rope coil and grapple on his hip
    if coil:
        cx, cy = T(-5.0, hipy - 1.0)
        for i in range(12):
            a = i / 12 * math.tau
            r.dot(cx + math.cos(a) * 2.2, cy + math.sin(a) * 1.6, "rope", 3 if math.sin(a) < 0 else 2, 0.2)
        r.line(cx - 1.0, cy + 1.5, cx - 2.0, cy + 4.0, "iron", 0.21, tone=3); r.dot(cx - 3.0, cy + 4.0, "iron", 3, 0.22)
        r.dot(cx - 1.0, cy + 4.0, "iron", 2, 0.22)
    # far arm
    sh2 = T(-3.5, hipy - 9.0)
    el2 = ik(sh2[0], sh2[1], hand2[0], hand2[1], 4.0, 3.8, bend=1)
    r.tube([sh2, el2, hand2], [1.4, 1.2, 1.1], "navy", -1.0, bias=-0.3)
    r.dot(hand2[0], hand2[1], "ivory", 2, -0.95)
    if rope:
        r.line(hand2[0], hand2[1], rope[0], rope[1], "rope", 4.5, tone=3)
        if grapple_hand: r.dot(*rope, "iron", 3, 4.6)
    # head
    hx, hy = T(0.5, hipy - 14.5)
    r.stamp(CAPT_HEAD[face], hx, hy, 2.0, CAPT_LEG, pivot=(4, 7))
    # near arm and the gaff
    sh = T(3.5, hipy - 9.0)
    el = ik(sh[0], sh[1], hand[0], hand[1], 4.0, 3.8, bend=-1)
    r.tube([sh, el, hand], [1.5, 1.3, 1.2], "navy", 3.0)
    r.dot(hand[0], hand[1], "ivory", 3, 3.05)
    a = math.radians(gaff_ang)
    gx, gy = hand[0] + math.cos(a) * 8.0, hand[1] + math.sin(a) * 8.0
    r.line(hand[0] - math.cos(a) * 2.0, hand[1] - math.sin(a) * 2.0, gx, gy, "wood", 3.1, tone=3)
    # the hook: a curl of iron at the end of the pole
    hk = [(gx, gy), (gx + math.cos(a + 1.2) * 2.0, gy + math.sin(a + 1.2) * 2.0), (gx + math.cos(a + 2.2) * 3.0, gy + math.sin(a + 2.2) * 3.0)]
    r.polyline(hk, "iron", 3.2, tones=[3, 4, 3])
    r.dot(*hk[-1], "steel", 4, 3.25)
    if smear:
        for (p, q, m, t) in smear: r.line(*p, *q, m, 5.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def captain_corpse(stage):
    r = Rig()
    r.poly([(-10, -1), (-6, -5), (6, -5), (10, -1), (10, 0), (-10, 0)], "navy", 0.0, bias=-0.1)
    r.line(-4, -4, 4, -1, "coral", 0.1, tone=2)
    r.stamp(CAPT_HEAD["hurt"], 12.0, -2.0, 1.0, CAPT_LEG, pivot=(4, 7))
    r.line(-12, -2, -4, -6, "wood", 0.5, tone=2); r.dot(-12, -3, "iron", 3, 0.6)
    for i in range(4): kelp_strand(r, -8 + i * 4, -1.5, 1 + i % 2, 0.5, 0.2, k=i)
    if stage == 0: dust(r, 0, 0, 1, 1.3)
    return r.resolve()


def captain_sheet(out):
    Cp = captain
    idle = [Cp(bob=[0, 0.3, 0.5, 0.3][i], coat_k=i, hand=(10.0, -15.0), gaff_ang=-65 + [0, 2, 4, 2][i]) for i in range(4)]
    run = []
    for i in range(6):
        s = math.sin(i / 6 * math.tau)
        run.append(Cp(lean=8, bob=[0, -0.8, -1.2, 0, -0.8, -1.2][i], coat_k=i, feet=((-3.0 + 3 * s, -max(0, -s) * 2), (3.0 - 3 * s, -max(0, s) * 2)),
                      hand=(8.0, -14.0 + s), gaff_ang=-40, hand2=(-5.0 - s, -13.0)))
    # Gaff (7): raise the gaff behind (0-1), RAKE it down and through (3: the hook at (17, -10)), haul back (4-6)
    gaff = [Cp(lean=-6, hand=(5.0, -24.0), gaff_ang=-120, face="shout"),
            Cp(lean=-10, hand=(3.0, -26.0), gaff_ang=-135, face="shout"),
            Cp(lean=8, hand=(10.0, -20.0), gaff_ang=-40, face="shout", smear=[((0, -32), (14, -30), "steel", 2)]),
            Cp(lean=14, hand=(12.0, -12.0), gaff_ang=10, face="shout", smear=[((16, -28), (20, -14), "steel", 2)],
               extra=lambda r: star(r, 20, -10, 1)),
            Cp(lean=6, hand=(8.0, -11.0), gaff_ang=150, face="grim"),
            Cp(lean=2, hand=(7.0, -13.0), gaff_ang=-10), Cp(gaff_ang=-60)]
    # Grapple (10): the rope whirls (0-1), FIRE (2: the grapple leaves the far hand toward (40, -40)), he swings
    # across hanging off the taut line (3-7), lets go and lands boot-first (8: kick at (12, -6)), recover (9)
    grap = [Cp(hand2=(-6.0, -24.0), rope=(-2.0, -28.0), grapple_hand=True, coil=False, face="shout"),
            Cp(hand2=(-3.0, -26.0), rope=(-8.0, -28.0), grapple_hand=True, coil=False, face="shout", lean=-6),
            Cp(hand2=(4.0, -24.0), rope=(14.0, -30.0), grapple_hand=True, coil=False, face="shout", lean=8,
               smear=[((-10, -28), (2, -30), "rope", 2)])]
    for k in range(5):
        a = -60 + k * 12
        grap.append(Cp(swing=True, coil=False, lean=-20 + k * 10, bob=-4.0 + abs(k - 2) * 1.5, hand2=(4.0, -24.0), hand=(8.0, -17.0),
                       rope=(4.0 + math.cos(math.radians(a)) * 14, -24.0 + math.sin(math.radians(a)) * 12), face="shout",
                       feet=((-4.0, -3.0 + k), (3.0, -2.0 + k)), gaff_ang=-30,
                       smear=[((-12, -12 + k), (-6, -14 + k), "navy", 2)] if k in (1, 2, 3) else None))
    grap += [Cp(lean=14, kick=(12.0, -6.0), feet=((-3.0, 0.0), (12.0, -6.0)), coil=False, face="shout",
                extra=lambda r: [star(r, 15, -6, 1), dust(r, -3, 0, 0, 1.2)]),
             Cp(lean=4, coil=True, extra=lambda r: dust(r, -2, 0, 1, 1.4))]
    d0 = Cp(face="hurt", lean=-12, hand=(6.0, -20.0), gaff_ang=-120)
    d1 = Cp(face="hurt", lean=-30, crouch=3.0, hand=(4.0, -8.0), gaff_ang=150)
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.09] * 6),
             ("Gaff", gaff, [0.12, 0.12, 0.06, 0.06, 0.12, 0.12, 0.14]),
             ("Grapple", grap, [0.12, 0.1, 0.08, 0.1, 0.1, 0.1, 0.1, 0.1, 0.08, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, captain_corpse(0), captain_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        Cp(face="hurt", lean=-14, hand=(6.0, -18.0), gaff_ang=-100))
    return sheet("BelCaptain", anims, out)


# ================================================================== CROWN OF THORNS
def star_arm(r, base, ang, ln, z, k=0.0, w=3.6, thorny=True, bias=0.0, curl_=0.0):
    """One thick starfish arm from the central disc: tapering, studded with bone thorns (crimson-purple tips) along
    its upper edge, its teal underside showing below."""
    pts = curl(base[0], base[1], ang, ln, curl_ + 4 * math.sin(k), n=5)
    radii = [w, w * 0.85, w * 0.68, w * 0.5, w * 0.35, 0.5]
    r.tube(pts, radii, "crown", z, bias=bias)
    for i in range(1, len(pts) - 1):
        r.dot(pts[i][0] + 0.5, pts[i][1] + radii[i] * 0.6, "teal", 2, z + 0.005)
    if thorny:
        for i in range(1, len(pts)):
            x, y = pts[i]
            for sgn in (-1, 1):
                if (i + (sgn > 0)) % 2: continue
                a = math.radians(ang + sgn * 90 + curl_ * i)
                rr = radii[min(i, 5)] + 0.8
                r.dot(x + math.cos(a) * rr, y + math.sin(a) * rr, "ivory", 3, z + 0.01)
                r.dot(x + math.cos(a) * (rr + 1.0), y + math.sin(a) * (rr + 1.0), "pink", 3 if sgn < 0 else 2, z + 0.02)
        r.dot(*pts[-1], "pink", 4, z + 0.02)
    return pts[-1]


def crown(n=5, lean=0.0, bob=0.0, feet=((-7.0, 0.0), (7.0, 0.0)), lash=None, raise_=0.0, k=0.0, hurt=False, smear=None,
          extra=None, fling=0.0):
    """A huge crown-of-thorns starfish walking upright on two of its arms, the rest raised. n = arms it still has
    (5..2): the raised ones are lost first (top right, top left, then the top). lash: (x, y) a raised arm whips to."""
    r = Rig()
    cy = -15.0 + bob
    T = Xf(lean, (0.0, cy + 6))
    cx, cyy = T(0.0, cy)
    # the two walking arms
    for i, (fx, fy) in enumerate(feet):
        base = T(-2.0 + i * 4.0, cy + 3.0)
        pts = [base, ((base[0] + fx) / 2 + (-1.5 if i == 0 else 1.5), (base[1] + fy) / 2), (fx, fy - 0.5)]
        r.tube(pts, [4.0, 3.0, 1.6], "crown", 0.5 if i else -0.5, bias=-0.25 if i == 0 else 0.0)
        for j in range(3):
            tx, ty = lerp(pts[0][0], fx, (j + 0.5) / 3.0) + (-2.6 if i == 0 else 2.6) * (1 - j / 3.0), lerp(pts[0][1], fy, (j + 0.5) / 3.0)
            r.dot(tx, ty, "ivory", 3, 0.6); r.dot(tx + (-1 if i == 0 else 1), ty, "pink", 3, 0.6)
    raised = [(-150.0 - raise_ * 10, "tl"), (-90.0, "top"), (-30.0 + raise_ * 10, "tr")]
    keep = {5: 3, 4: 2, 3: 1, 2: 0}[n]
    order = ["top", "tl", "tr"]
    have = order[:keep]
    # the disc: a thick purple pad studded with thorns, its mouth side teal
    for ang, name in raised:
        if name not in have: continue
        if name == "tl": continue
        if lash and name == "top":
            star_arm(r, (cx + 1.0, cyy - 3.0), math.degrees(math.atan2(lash[1] - cyy, lash[0] - cx)), 12.0, 2.0, k=k, curl_=-5)
            continue
        star_arm(r, (cx + (1.0 if name == "top" else 3.0), cyy - (3.0 if name == "top" else 1.0)), ang - fling * 30, 12.0,
                 1.0 if name == "top" else 1.5, k=k + (1 if name == "tr" else 0), curl_=6 if name == "tr" else 0)
    if "tl" in have:
        star_arm(r, (cx - 3.0, cyy - 1.0), raised[0][0] + fling * 30, 11.5, -1.0, k=k + 2, bias=-0.25, curl_=-6)
    r.ell(cx, cyy, 8.0, 7.5, "crown", 0.0)
    for i in range(8):
        a = i / 8 * math.tau + 0.3
        r.dot(cx + math.cos(a) * 4.0, cyy + math.sin(a) * 3.5, "ivory", 3 if math.sin(a) < 0 else 2, 0.05)
        r.dot(cx + math.cos(a) * 4.0, cyy + math.sin(a) * 3.5 - 1.0, "pink", 3, 0.06)
    # a ring of cyan eyespots at the arm roots
    eye(r, cx + 2.0, cyy - 1.0, 0.1, big=True); eye(r, cx - 1.0, cyy - 1.5, 0.1)
    if hurt: r.dot(cx + 2.0, cyy - 1.0, "crown", 4, 0.2)
    # stumps where arms broke off: raw pink
    for ang, name in raised:
        if name in have: continue
        sx, sy = cx + math.cos(math.radians(ang)) * 6.0, cyy + math.sin(math.radians(ang)) * 5.5
        r.ell(sx, sy, 1.6, 1.4, "pink", 0.1, bias=-0.1)
        r.dot(sx, sy, "pink", 4, 0.11)
    if smear:
        for (p, q, m, t) in smear: r.line(*p, *q, m, 4.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def crown_corpse(stage):
    r = Rig()
    r.ell(0.0, -2.5, 6.0, 2.6, "crown", 0.0, bias=-0.1)
    for ang in (180, 140, 40, 0, -20):
        a = math.radians(ang)
        pts = [(math.cos(a) * 4, -2.5 + math.sin(a) * 1.0), (math.cos(a) * 12, -1.0 + math.sin(a) * 1.5)]
        r.tube(pts, [2.2, 0.8], "crown", -0.1, bias=-0.2)
        r.dot(pts[1][0], pts[1][1], "pink", 2, 0.0)
    if stage == 0: dust(r, 0, 0, 1, 1.3)
    return r.resolve()


def crown_sheet(out):
    anims = []
    for n in (5, 4, 3, 2):
        sfx = "" if n == 5 else str(n)
        C = lambda **kw: crown(n=n, **kw)
        idle = [C(bob=[0, 0.4, 0.8, 0.4][i], k=i * 0.8, raise_=[0, 0.3, 0.6, 0.3][i]) for i in range(4)]
        run = []
        for i in range(6):
            s = math.sin(i / 6 * math.tau)
            run.append(C(lean=6, bob=-abs(s) * 1.2, k=i, feet=((-6.0 + 3 * s, -max(0, -s) * 2.5), (6.0 - 3 * s, -max(0, s) * 2.5))))
        # Lash (6): the top arm rears back (0-1), WHIPS down ahead (2: tip at (16, -4)), drags (3), back (4-5); with
        # two arms left it lashes with a walking arm (a kick)
        if n > 2:
            lash = [C(lash=(-4.0, -34.0), lean=-6), C(lash=(-8.0, -32.0), lean=-10),
                    C(lash=(16.0, -6.0), lean=10, smear=[((2, -34), (14, -18), "crown", 2)]),
                    C(lash=(17.0, -3.0), lean=12, extra=lambda r: dust(r, 17, 0, 0)),
                    C(lash=(10.0, -20.0), lean=4), C(lean=0)]
        else:
            lash = [C(lean=-8, feet=((-6.0, 0.0), (4.0, -4.0))), C(lean=-12, feet=((-6.0, 0.0), (2.0, -6.0))),
                    C(lean=12, feet=((-6.0, 0.0), (15.0, -4.0)), smear=[((6, -8), (13, -5), "crown", 2)]),
                    C(lean=10, feet=((-6.0, 0.0), (16.0, -3.0)), extra=lambda r: star(r, 18, -3, 1)),
                    C(lean=4, feet=((-6.0, 0.0), (9.0, -2.0))), C()]
        # Fling (7): the arms curl in (0-2), FLING open (3: one thorn per arm from (0, -18)), recoil (4-6)
        fling = [C(fling=-0.4, bob=0.5), C(fling=-0.8, bob=1.0, lean=-4), C(fling=-1.0, bob=1.2, lean=-6),
                 C(fling=0.8, bob=-1.0, lean=6, extra=lambda r: [r.dot(math.cos(math.radians(a)) * 18, -18 + math.sin(math.radians(a)) * 14, "ivory", 4, 6)
                                                               for a in (-160, -120, -90, -60, -20)]),
                 C(fling=0.5, lean=4), C(fling=0.2), C()]
        anims += [("Idle" + sfx, idle, [0.18, 0.16, 0.18, 0.16]), ("Run" + sfx, run, [0.09] * 6),
                  ("Lash" + sfx, lash, [0.14, 0.12, 0.06, 0.08, 0.12, 0.14]),
                  ("Fling" + sfx, fling, [0.1, 0.1, 0.12, 0.06, 0.1, 0.12, 0.14])]
    idle0 = anims[0][1][0]
    d0 = crown(hurt=True, lean=-12, n=3)
    d1 = crown(hurt=True, lean=-30, bob=4.0, n=2)
    anims += tail_anims(idle0, [d0, d1, crown_corpse(0), crown_corpse(1)], [0.08, 0.12, 0.14, 0.4], crown(hurt=True, lean=-14))
    return sheet("BelCrownThorns", anims, out)


# ================================================================== BROOD URCHIN
def brood(bob=0.0, sx=1.0, sy=1.0, rot=0.0, pulse=0, legs_k=0, eggs=True, hurt=False, smear=None, extra=None, ln=3.5,
          lean=0.0, lob=None):
    """A bloated urchin queen: a big low dome on short stubby spines, clusters of glowing cyan eggs nested between
    the spines, lit from inside. pulse 0..2 brightens the eggs."""
    r = Rig()
    cx, cy = 0.0, -11.5 + bob
    rx, ry = 14.0 * sx, 10.0 * sy
    # stubby spine legs
    for i in range(6):
        u = (i / 5.0) * 2 - 1
        fx = cx + u * 11.0 + (1.0 if (i + legs_k) % 2 else 0.0) * u
        top = (cx + u * 9.0, cy + ry * 0.6)
        r.tube([top, (fx, -max(0.0, ((i + legs_k) % 3 == 0) * 1.0))], [1.0, 0.6], "spinev", 0.5 if u > 0 else -0.5, bias=0.1)
        r.dot(fx, 0, "ivory", 2, 0.6)
    spines(r, cx, cy, rx, ry, 34, ln, "spinev", -1.0, phase=math.radians(rot), front=False, tips=3)
    r.ell(cx, cy, rx, ry, "spinev", 0.0, ang=lean)
    r.ell(cx - 1.0, cy - 1.5, rx * 0.8, ry * 0.75, "spinev", 0.01, bias=0.15)
    # inner light: a teal glow through the shell
    for i in range(14):
        a = i / 14 * math.tau
        r.dot(cx + math.cos(a) * rx * 0.45, cy + math.sin(a) * ry * 0.4, "teal", 3, 0.02)
    if eggs:
        for j, (ex, ey) in enumerate(((-8, -4), (-3, -6.5), (3, -6), (8, -3.5), (-10, 0), (10, 0.5), (0, -2), (-5, 1), (5, 1.5))):
            t = 2 + ((j + pulse) % 3 == 0) + (pulse >= 2)
            ex2, ey2 = cx + ex * sx * 1.05, cy + ey * sy * 1.1
            r.ell(ex2 + 0.5, ey2, 1.5, 1.2, "lure", 0.28, flat=1 + (t > 2))
            r.dot(ex2, ey2, "lure", min(4, t), 0.3)
            r.dot(ex2 + 1, ey2, "lure", min(4, t - 1), 0.3)
    eye(r, cx + 9.0, cy - 2.0, 0.4, big=True); eye(r, cx + 6.0, cy - 3.0, 0.4)
    if hurt: r.dot(cx + 9.0, cy - 2.0, "spinev", 4, 0.5)
    spines(r, cx, cy, rx, ry, 34, ln, "spinev", 1.0, phase=math.radians(rot), front=True, tips=2)
    if lob:
        for (x, y) in lob:
            r.ell(x, y, 1.6, 1.4, "lure", 6.0, flat=3); r.dot(x - 0.5, y - 0.5, "lure", 4, 6.1)
    if smear:
        for (p, q, m, t) in smear: r.line(*p, *q, m, 4.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def brood_corpse(stage):
    r = Rig()
    spines(r, 0, -4.5, 13.0, 4.5, 26, 2.5, "spinev", -1.0, front=False, phase=0.4)
    r.ell(0, -4.5, 13.0, 4.5, "spinev", 0.0, bias=-0.15)
    spines(r, 0, -4.5, 13.0, 4.5, 26, 2.5, "spinev", 1.0, front=True, phase=0.4, tone=2)
    for (ex, ey) in ((-6, -4), (2, -5), (8, -3)): r.dot(ex, ey, "lure", 1 if stage else 2, 0.3)
    if stage == 0: dust(r, 0, 0, 1, 1.6)
    return r.resolve()


def brood_sheet(out):
    Bd = brood
    idle = [Bd(bob=[0, 0.3, 0.6, 0.3][i], sy=[1.0, 1.02, 1.04, 1.02][i], rot=i * 2, pulse=i % 3) for i in range(4)]
    run = [Bd(bob=[0, -0.6, -1.0, 0, -0.6, -1.0][i], rot=-5 * i, legs_k=i, pulse=i % 3, sx=[1.0, 0.98, 0.97, 1.0, 0.98, 0.97][i])
           for i in range(6)]
    # Spray (6): swell (0-1), SPIT three spines in a fan (3: from (12, -12)), settle (4-5)
    spray = [Bd(sy=1.06, sx=0.96, bob=-0.5), Bd(sy=1.1, sx=0.94, bob=-1.0, ln=2.5, lean=-4),
             Bd(sy=0.95, sx=1.05, ln=4.5, lean=6), Bd(sy=0.92, sx=1.06, ln=5.0, lean=8,
                                                       extra=lambda r: [r.line(13, -12, 18, -12 + d, "ivory", 6, tone=4) for d in (-3, 0, 3)]),
             Bd(ln=4.0, lean=4), Bd()]
    # Clutch (8): heave (0-2), LOB three eggs high (4: they leave from (0, -20)), the eggs arc away (5-6), settle (7)
    clutch = [Bd(sy=0.94, bob=1.0), Bd(sy=0.9, sx=1.04, bob=1.5, pulse=2), Bd(sy=1.08, sx=0.95, bob=-1.5, pulse=2),
              Bd(sy=1.12, sx=0.93, bob=-2.0, pulse=2, lob=[(0, -22)]),
              Bd(sy=1.0, bob=-0.5, lob=[(-4, -26), (2, -27), (8, -25)]),
              Bd(lob=[(-2, -30), (6, -31), (14, -29)]), Bd(lob=[(4, -33), (12, -33), (19, -31)]), Bd()]
    d0 = Bd(hurt=True, sy=0.9, sx=1.06, rot=-6)
    d1 = Bd(hurt=True, sy=0.7, sx=1.1, bob=2.0, eggs=False)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.1] * 6), ("Spray", spray, [0.14, 0.14, 0.06, 0.08, 0.12, 0.14]),
             ("Clutch", clutch, [0.12, 0.12, 0.12, 0.1, 0.08, 0.08, 0.1, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, brood_corpse(0), brood_corpse(1)], [0.08, 0.12, 0.14, 0.4], Bd(hurt=True, sy=0.92, sx=1.05))
    return sheet("BelBrood", anims, out)


# ================================================================== TIDE MATRIARCH
MAT_LEG = legend(k="teal:0", d="teal:1", s="teal:2", S="teal:3", L="teal:4", e="lure:3", E="lure:4", m="teal:0",
                 c="coral:2", C="coral:3", X="coral:4", p="pearl:3", P="pearl:4", h="kelp:1", H="kelp:2")
MAT_FACE = {
    # pivot (3, 8): the chin. A coral crown of spikes, teal face, cyan eyes, pearl at the brow.
    "regal": """
C.X.C.C
cCcCcCc
.cpPpc.
hsSLSsh
hseSesh
hsSSSsh
.dsmsd.
..dsd..
...d...
""",
    "cry": """
C.X.C.C
cCcCcCc
.cpPpc.
hsSLSsh
hsESEsh
hsSSSsh
.dmmmd.
..dmd..
...d...
""",
    "hurt": """
C.X.C.C
cCcCcCc
.cpPpc.
hsSLSsh
hsmSmsh
hsSSSsh
.dmsmd.
..dsd..
...d...
""",
    "glow": """
X.X.X.X
CXCXCXC
.cpPpc.
hsSLSsh
hsESEsh
hsSSSsh
.dsmsd.
..dsd..
...d...
""",
}


def trident(r, hand, ang, z, ln=27.0, glow=False):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    tx, ty = hand[0] + ca * ln * 0.6, hand[1] + sa * ln * 0.6
    bx, by = hand[0] - ca * ln * 0.4, hand[1] - sa * ln * 0.4
    r.line(bx, by, tx, ty, "pearl", z, tone=2)
    r.line(bx + 1, by, tx + 1, ty, "coral", z - 0.01, tone=1)
    px, py = -sa, ca
    r.line(tx - px * 2.5, ty - py * 2.5, tx + px * 2.5, ty + py * 2.5, "coral", z + 0.01, tone=3)
    for s in (-2.5, 0.0, 2.5):
        r.line(tx + px * s, ty + py * s, tx + px * s + ca * (4.0 if s == 0 else 3.0), ty + py * s + sa * (4.0 if s == 0 else 3.0),
               "coral", z + 0.02, tone=4 if s <= 0 else 3)
    if glow:
        for s in (-2.5, 0.0, 2.5): r.dot(tx + px * s + ca * 4.5, ty + py * s + sa * 4.5, "lure", 4, z + 0.03)
    return tx + ca * 4.0, ty + sa * 4.0


def matriarch(lean=0.0, bob=0.0, hand=(8.5, -18.0), hand2=(-5.0, -17.0), tri_ang=-90.0, face="regal", train_k=0,
              tail_k=0.0, crown_glow=False, smear=None, extra=None, slither=0.0, tri_glow=False, plant=False):
    r = Rig()
    by = -14.0 + bob
    T = Xf(lean, (0.0, by + 6))
    # the kelp train: a long ragged trail behind her on the floor
    for i in range(7):
        kelp_strand(r, -4.0 - i * 2.6, -2.5 - i * 0.2, 3 + (i + train_k) % 3, -1.0, -2.0 + i * 0.01, k=train_k + i)
    r.poly([(-3.0, -11.0), (-12.0, -6.0), (-21.0, -2.5 + math.sin(train_k) * 0.5), (-20.0, 0.0), (-2.0, 0.0)], "kelp", -2.1, bias=-0.1)
    # she stands on her coiled tail: a thick teal coil with pearl fins
    tp = [T(0.0, by + 4.0), (3.0 + slither, -5.0), (7.0 + slither, -2.5), (4.0, -1.0), (-3.0, -1.2), (-7.0 - slither, -3.0)]
    r.tube(tp, [5.2, 5.0, 4.2, 3.4, 2.6, 1.4], "teal", -0.5)
    for i in range(1, 5): r.dot(tp[i][0], tp[i][1] - 1.5, "teal", 4, -0.45)
    fin(r, [tp[-1], (tp[-1][0] - 3.5, tp[-1][1] - 3.0 + tail_k), (tp[-1][0] - 2.0, tp[-1][1]), (tp[-1][0] - 3.5, tp[-1][1] + 1.0)],
        "pearl", -0.6, bias=0.1)
    # torso: teal skin, a pearl-strung bodice of shell
    cx, cy = T(0.0, by - 3.0)
    r.ell(cx, cy, 6.4, 7.8, "teal", 0.0)
    for i in range(5): r.dot(*T(-2.0 + i, by - 6.0 + abs(i - 2) * 0.5), "pearl", 3 if i % 2 else 4, 0.05)
    r.ell(*T(0.0, by + 1.0), 4.4, 2.0, "sea", 0.04, bias=-0.1)                             # scaled hips
    # long hair down her back (kelp)
    hx, hy = T(0.5, by - 12.0)
    r.poly([(hx - 1.0, hy - 4.0), (hx - 7.0, hy - 2.0), (hx - 9.5, hy + 8.0), (hx - 8.0, hy + 15.0), (hx - 3.0, hy + 13.0),
            (hx - 1.5, hy + 4.0)], "kelp", -0.8, curve=0.4)
    for k in range(3): kelp_strand(r, hx - 6.5 + k, hy + 12.0, 4 + k, -1.0, -0.79, k=train_k + k)
    # far arm
    sh2 = T(-3.5, by - 8.0)
    el2 = ik(sh2[0], sh2[1], hand2[0], hand2[1], 4.0, 4.0, bend=1)
    r.tube([sh2, el2, hand2], [1.2, 1.0, 0.9], "teal", -1.0, bias=-0.3)
    r.stamp(MAT_FACE["glow" if crown_glow else face], hx, hy + 4.0, 2.0, MAT_LEG, pivot=(3, 8))
    if crown_glow:
        for (dx, dy) in ((-4, -6), (4, -7), (0, -9)): r.dot(hx + dx, hy + dy, "lure", 3, 2.1)
    # near arm and the trident
    sh = T(3.5, by - 8.0)
    el = ik(sh[0], sh[1], hand[0], hand[1], 4.0, 4.0, bend=-1)
    r.tube([sh, el, hand], [1.3, 1.1, 1.0], "teal", 3.0)
    tip = trident(r, hand, tri_ang, 3.1, glow=tri_glow)
    r.dot(hand[0], hand[1], "teal", 4, 3.2)
    if plant:
        for i in range(3): r.dot(tip[0] - 2 + i * 2, 0, "foam", 3, 3.5)
    if smear:
        for (p, q, m, t) in smear: r.line(*p, *q, m, 5.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def matriarch_corpse(stage):
    r = Rig()
    r.tube([(6, -2), (0, -2.5), (-6, -2), (-12, -3)], [3.0, 3.2, 2.4, 1.2], "teal", -0.5, bias=-0.15)
    fin(r, [(-12, -3), (-15, -6), (-14, -2), (-16, -1)], "pearl", -0.6)
    r.stamp(MAT_FACE["hurt"], 11.0, -1.0, 1.0, MAT_LEG, pivot=(3, 8))
    trident(r, (2.0, -1.5), 0.0, 0.5, ln=20)
    for i in range(4): kelp_strand(r, -4 + i * 3, -2.0, 1 + i % 2, 0.5, -0.4, k=i)
    if stage == 0: dust(r, 0, 0, 1, 1.4)
    return r.resolve()


def matriarch_sheet(out):
    M = matriarch
    idle = [M(bob=[0, -0.4, -0.8, -0.4][i], train_k=i, tail_k=[0, 0.5, 1, 0.5][i], hand=(9.5, -18.0 + [0, -0.4, -0.8, -0.4][i]))
            for i in range(4)]
    run = [M(lean=6, bob=[0, -0.8, -1.2, -0.8, 0, -0.4][i], train_k=i, slither=[0, 1, 2, 1, 0, -1][i], tri_ang=-70,
             hand=(7.0, -16.0)) for i in range(6)]
    # Thrust (7): draw the trident back (0-1), THRUST (3: the tines at (24, -14); the coral shard flies from there),
    # hold (4), recover (5-6)
    thrust = [M(lean=-6, hand=(2.0, -16.0), tri_ang=-10, face="cry"), M(lean=-10, hand=(-1.0, -16.0), tri_ang=-5, face="cry"),
              M(lean=8, hand=(9.0, -15.0), tri_ang=0, face="cry", smear=[((0, -16), (10, -16), "pearl", 2)]),
              M(lean=12, hand=(12.0, -14.0), tri_ang=0, face="cry", extra=lambda r: star(r, 27, -14, 2)),
              M(lean=8, hand=(10.0, -14.5), tri_ang=0), M(lean=2, hand=(7.0, -16.0), tri_ang=-50), M()]
    # Plant (6): raise the trident (0-1), PLANT it in the floor before her (3: the currents start), the crown
    # kindles (4-5). PlantLoop (4): held, the crown glowing, while the lanes run.
    plant = [M(hand=(6.0, -22.0), tri_ang=-80, face="cry"), M(hand=(6.0, -25.0), tri_ang=-85, face="cry", lean=-4),
             M(hand=(9.0, -14.0), tri_ang=95, face="cry", lean=6, smear=[((8, -34), (10, -20), "pearl", 2)]),
             M(hand=(10.0, -12.0), tri_ang=95, crown_glow=True, lean=8, plant=True, extra=lambda r: splash(r, 11, 0, 0, 1.2)),
             M(hand=(10.0, -12.0), tri_ang=95, crown_glow=True, lean=8, plant=True, extra=lambda r: splash(r, 11, 0, 1, 1.4)),
             M(hand=(10.0, -12.0), tri_ang=95, crown_glow=True, lean=6, plant=True)]
    loop = [M(hand=(10.0, -12.0 + [0, -0.3, -0.6, -0.3][i]), tri_ang=95, crown_glow=True, lean=6, plant=True, train_k=i,
              bob=[0, -0.3, -0.6, -0.3][i], hand2=(-6.0, -20.0 - i % 2)) for i in range(4)]
    d0 = M(face="hurt", lean=-12, hand=(5.0, -20.0), tri_ang=-120)
    d1 = M(face="hurt", lean=-30, bob=4.0, hand=(6.0, -8.0), tri_ang=160)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.09] * 6),
             ("Thrust", thrust, [0.14, 0.12, 0.06, 0.06, 0.12, 0.12, 0.14]),
             ("Plant", plant, [0.12, 0.12, 0.08, 0.1, 0.12, 0.14]), ("PlantLoop", loop, [0.14] * 4)]
    anims += tail_anims(idle[0], [d0, d1, matriarch_corpse(0), matriarch_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        M(face="hurt", lean=-14, hand=(5.0, -19.0), tri_ang=-110))
    return sheet("BelMatriarch", anims, out)


# ================================================================== JELLY SIREN
def jelly(bob=0.0, lean=0.0, squeeze=0.0, k=0, hand=(4.0, -16.0), lash=None, glow=1, hurt=False, smear=None, extra=None,
          trail=0.0):
    """The siren under a translucent jellyfish bell: a dome over her head and shoulders, her slim body below, a
    curtain of frilled tentacles hanging from the rim. squeeze 0..1 contracts the bell (the jet pulse)."""
    r = Rig()
    hover = 2.0 + bob
    T = Xf(lean, (0.0, -14.0))
    # her slim pale body and skirt-fins beneath the bell
    bx, by = T(0.0, -12.0 - hover)
    r.ell(bx, by, 2.4, 5.5, "drown", -0.2)
    r.tube([T(0.0, -7.0 - hover), T(-0.5 - trail, -2.0 - hover), T(-1.5 - trail * 2, 0.0 - hover * 0.5)], [1.8, 1.2, 0.6], "sea", -0.3)
    sh = T(1.5, -16.0 - hover)
    r.tube([sh, hand], [0.8, 0.6], "drown", 0.4)
    # back tentacles
    rim_y = -21.0 - hover + squeeze * 2.0
    for i in range(9):
        u = i / 8.0 * 2 - 1
        x0, y0 = T(u * (9.0 - squeeze * 3.0), rim_y)
        ln = 16 + (i % 3) * 3 - squeeze * 5
        wav = 1.2 * math.sin(k * 0.9 + i)
        pts = [(x0, y0)] + [(x0 + wav * math.sin(j * 0.8 + k) - trail * j * 0.4, y0 + j * ln / 6.0) for j in range(1, 7)]
        pts = [(x, min(y, -0.5)) for (x, y) in pts]
        if lash and i in (4, 5, 6):
            pts = [(x0, y0), ((x0 + lash[0]) / 2, (y0 + lash[1]) / 2 - 2), lash]
        r.polyline(pts, "jelly", -1.0 + 0.01 * i, tones=[3, 3, 2, 2, 1, 1, 1])
        if i % 2 == 0: r.dot(*pts[-1], "lure", 2, -0.9)
    # the bell: translucent dome (her head inside it), frilled rim
    cx, cy = T(0.0, -27.0 - hover + squeeze * 1.5)
    rx, ry = 10.5 - squeeze * 2.5, 8.0 + squeeze * 1.5
    r.ell(cx, cy, rx, ry, "jelly", 1.0, bias=0.1)
    r.ell(cx - 1.5, cy - 2.0, rx * 0.5, ry * 0.4, "jelly", 1.01, bias=0.4)
    # her face inside the bell: dim
    r.ell(cx + 1.0, cy + 2.5, 2.2, 2.4, "drown", 1.02, bias=-0.1)
    eye(r, cx + 2.0, cy + 2.0, 1.03, mat="lure"); r.dot(cx + 0.2, cy + 2.0, "lure", 2, 1.03)
    if hurt: r.dot(cx + 2.0, cy + 2.0, "drown", 4, 1.04)
    # radial canals glowing
    for i in range(5):
        a = math.radians(-160 + i * 35)
        r.line(cx + math.cos(a) * 2.0, cy + math.sin(a) * 2.0, cx + math.cos(a) * (rx - 1), cy + math.sin(a) * (ry - 1), "lure",
               1.05, tone=1 + (glow >= 2))
    for i in range(int(rx * 2) + 1):
        x = cx - rx + i
        r.dot(x, cy + ry * 0.55 + (1 if i % 2 else 0), "jelly", 4 if i % 2 else 3, 1.06)
    # front tentacles (frilled oral arms)
    for i in range(3):
        x0, y0 = T(-2.0 + i * 2.5, rim_y + 1.0)
        pts = [(x0 + 0.8 * math.sin(k + j + i) - trail * j * 0.3, y0 + j * 2.2) for j in range(7)]
        pts = [(x, min(y, -0.5)) for (x, y) in pts]
        if lash and i == 2:
            pts = [(x0, y0), ((x0 + lash[0]) / 2, (y0 + lash[1]) / 2 + 1), lash]
        r.polyline(pts, "pink", 1.5 + i * 0.01, tones=[3, 4, 3, 3, 2, 2, 2])
    if smear:
        for (p, q, m, t) in smear: r.line(*p, *q, m, 5.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def jelly_corpse(stage):
    r = Rig()
    r.ell(0, -3.5, 10.0 - stage, 3.5, "jelly", 0.0, bias=-0.1)
    r.ell(2.0, -2.5, 2.0, 1.8, "drown", 0.1, bias=-0.2)
    for i in range(6): r.polyline([(-8 + i * 3, -1), (-10 + i * 3, 0), (-12 + i * 3, -0.5)], "jelly", -0.5, tones=[2, 1, 1])
    for i in range(3): r.dot(-4 + i * 4, -4.5, "lure", 1 + (stage == 0), 0.2)
    return r.resolve()


def jelly_sheet(out):
    Jl = jelly
    idle = [Jl(bob=[0, 0.6, 1.0, 0.6][i], k=i, squeeze=[0, 0.1, 0.2, 0.1][i]) for i in range(4)]
    run = [Jl(bob=[0, 0.5, 1.0, 0.5, 0, -0.3][i], k=i * 1.2, lean=8, trail=1.5, squeeze=[0, 0.2, 0.3, 0.2, 0, 0][i]) for i in range(6)]
    # Lash (7): the bell rears (0-1), the tentacles WHIP ahead (3: tips at (15, -6)), drag back (4-6)
    lash = [Jl(lean=-8, squeeze=0.2), Jl(lean=-12, squeeze=0.4, glow=2),
            Jl(lean=8, lash=(12.0, -10.0), glow=2, smear=[((4, -18), (12, -12), "jelly", 3)]),
            Jl(lean=12, lash=(15.0, -6.0), glow=2, extra=lambda r: star(r, 16, -6, 1)),
            Jl(lean=8, lash=(12.0, -5.0)), Jl(lean=4, k=1), Jl(k=2)]
    # Jet (12): three pulses, each: contract (0), JET (1: she moves 30 px; a sting ring where she stops), glide (2),
    # open (3)
    jet = []
    for p in range(3):
        jet += [Jl(squeeze=0.8, glow=2, k=p), Jl(squeeze=1.0, lean=14, trail=3.0, glow=2, k=p + 1,
                                                  smear=[((-10, -24), (-4, -26), "jelly", 2), ((-10, -20), (-4, -20), "jelly", 1)]),
                Jl(squeeze=0.4, lean=6, trail=2.0, k=p + 2), Jl(squeeze=0.0, k=p + 3)]
    d0 = Jl(hurt=True, lean=-10, squeeze=0.6)
    d1 = Jl(hurt=True, lean=-25, squeeze=1.0, bob=-2.0, glow=0)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.1] * 6),
             ("Lash", lash, [0.12, 0.12, 0.06, 0.06, 0.12, 0.12, 0.14]),
             ("Jet", jet, [0.08, 0.06, 0.12, 0.1] * 3)]
    anims += tail_anims(idle[0], [d0, d1, jelly_corpse(0), jelly_corpse(1)], [0.08, 0.12, 0.14, 0.4], Jl(hurt=True, lean=-12, squeeze=0.5))
    return sheet("BelJellySiren", anims, out)


JOBS = [("BelDrownedBell", bell_sheet), ("BelCaptain", captain_sheet), ("BelCrownThorns", crown_sheet), ("BelBrood", brood_sheet),
        ("BelMatriarch", matriarch_sheet), ("BelJellySiren", jelly_sheet)]
SYNC = {
    "BelDrownedBell": {"Toll": [("the bell swings over his head", 3), ("SLAM: the bell lands mouth-down at (17, 0); ring at (19, 0)", 4)],
                       "Cast": [("HURL: the bell leaves his hands at (12, -30) (FxBelCastBell takes over)", 4)],
                       "Punch": [("JAB: fist at (18, -14); box at (15, -13)", 2)],
                       "Lift": [("starts at the bell (in front of him, (16, 0))", 0), ("the bell is on his back", 6), ("TOLL round him (0, 0)", 7)]},
    "BelCaptain": {"Gaff": [("RAKE: the hook at (20, -10); box at (16, -10)", 3)],
                   "Grapple": [("FIRE: the grapple leaves the far hand at (4, -24)", 2), ("swinging (3-7)", 3),
                               ("LAND: the boot at (12, -6); kick box at (12, -6)", 8)]},
    "BelCrownThorns": {"Lash": [("WHIP: the arm tip at (16, -6); box at (13, -6)", 2)],
                       "Fling": [("FLING: one thorn per arm from (0, -18)", 3)]},
    "BelBrood": {"Spray": [("SPIT: three spines from (13, -12)", 3)], "Clutch": [("LOB: the eggs leave from (0, -22)", 4)]},
    "BelMatriarch": {"Thrust": [("THRUST: the tines at (24, -14); box at (19, -14); the shard flies from (24, -14)", 3)],
                     "Plant": [("PLANT: the trident bites the floor at (11, 0); the lanes start", 3)]},
    "BelJellySiren": {"Lash": [("WHIP: tentacle tips at (15, -6); box at (13, -7)", 3)],
                      "Jet": [("pulse 1: jet (move 30 px)", 1), ("pulse 2", 5), ("pulse 3", 9)]},
}
NOTES = {
    "BelDrownedBell": "IdleBare / RunBare / Punch: with the bell off his back (Bare Back). Lift starts with the bell standing in "
                      "front of him (the floor bell FX is removed as it starts) and ends with the toll.",
    "BelCaptain": "Grapple frames 3-7 are drawn hanging off the line; the code moves the body along the arc.",
    "BelCrownThorns": "Idle/Run/Lash/Fling (5 arms), and Idle4/Run4/Lash4/Fling4 ... Idle2/Run2/Lash2/Fling2: the arm count is its "
                      "shape (Regrowth). The raised arms go first: top right, top left, then the top.",
    "BelMatriarch": "PlantLoop (4): held while the Riptide Lanes run (3 s), the crown glowing.",
    "BelJellySiren": "Hovers 2 px. Jet is three pulses in one clip (frames 1, 5, 9 are the jets).",
}
