"""Sylvene tier 1: Sporeling, Thornbiter, Rotfly, and the Sprout (the Rot Mother's minion). Built through
sylvene_v2_rigs.py (python3 sylvene_v2_rigs.py --only SylSporeling,...). T1 idle limit 20 x 16."""
import math
from sylvene_v2_rigs import (Rig, Xf, chain, ik, lerp, sheet, tail_anims, cap, vine, thorn, leaf, wing, pod, motes, puff,
                             smears, sparks, soil, dust_puff)

# ================================================================== SPORELING: a squat cracked-cap mushroom with a puff-sac belly
SPORE_LEG = {"k": ("mould", 0), "m": ("chitin", 0), "g": ("glowg", 3), "G": ("glowg", 4), "w": ("mould", 3), "d": ("mould", 1),
             "p": ("podf", 1), "P": ("podf", 3)}
SPORE_FACE = {
    # pivot (3, 1): the face sits on the stem just under the gills
    "calm": """
.m...m.
.g...g.
..mmm..
""",
    "puff": """
.m...m.
.G...G.
..mpm..
""",
    "hurt": """
.g...g.
.m...m.
..ppp..
""",
    "dead": """
.m...m.
..m.m..
...p...
""",
}


def sporeling(bob=0.0, squash=0.0, tilt=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), face="calm", lean=0.0, belly=1.0,
              cap_dy=0.0, cap_dx=0.0, extra=None, cloud=None, seeds=(), cap_crack=0, alt=0.0):
    r = Rig()
    T = Xf(lean, (0.0, -1.0))
    # stubby root feet: two short tubes splaying into the floor
    for k, (fx, fy) in enumerate(feet):
        hip = T(-1.6 if k == 0 else 1.6, -3.0 + bob - alt)
        r.tube([hip, (fx, fy - 1.0 - alt), (fx + (1.4 if k else -1.4), fy - alt)], [1.3, 1.0, 0.6], "bark", -0.5 if k == 0 else 0.5,
               bias=-0.2 if k == 0 else 0.0)
    # puff-sac belly (pod flesh under mould skin) and the stem
    by = -5.5 + bob + squash * 0.8 - alt
    r.ell(*T(0.0, by), 4.6 * belly + squash * 0.6, 3.6 * belly - squash * 0.5, "mould", 0.0, bias=0.05)
    r.ell(*T(0.4, by + 0.8), 2.8 * belly, 2.0 * belly, "podf", 0.1, bias=0.0)
    r.ell(*T(0.0, by - 3.4), 2.6, 1.8, "mould", 0.2, bias=0.1)
    # face, then the wide cracked cap
    fx_, fy_ = T(0.8, by - 1.6)
    r.stamp(SPORE_FACE[face], fx_, fy_, 0.6, SPORE_LEG, pivot=(3, 1))
    cx, cy = T(cap_dx, -10.0 + bob + squash * 1.4 + cap_dy - alt)
    cap(r, cx, cy, 8.0 + squash * 0.8, 4.8 - squash * 0.6, 1.0, mat="mould", spots="bruise", gill="corpse", tilt=tilt + lean * 0.5,
        nspots=5, seed=4)
    if cap_crack:
        r.polyline([(cx - 2, cy - 4), (cx - 1, cy - 2), (cx - 2, cy - 1), (cx - 1, cy + 0.5)], "chitin", 1.2, tone=1)
        if cap_crack > 1: r.polyline([(cx + 3, cy - 3), (cx + 2, cy - 1)], "chitin", 1.2, tone=1)
    for (sx, sy, k) in seeds:
        r.ell(sx, sy, 1.1, 1.3, "gall", 3.0, bias=0.2); r.dot(sx, sy - 1.3, "moss", 3, 3.1)
        if k: r.dot(sx - 1, sy - 2.5, "gall", 2, 3.0)
    if cloud: puff(r, *cloud)
    if extra: extra(r)
    return r.resolve()


def sporeling_sheet(outdir):
    S = sporeling
    idle = [S(bob=[0, 0.3, 0.6, 0.3][i], belly=[1.0, 1.04, 1.08, 1.04][i], tilt=[0, -3, 0, 3][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(S(bob=-0.8 * abs(math.sin(ph)), lean=6, tilt=8 * math.sin(ph),
                     feet=((-3.0 + 2.2 * math.cos(ph), -max(0, 1.5 * math.sin(ph))), (3.0 - 2.2 * math.cos(ph), -max(0, -1.5 * math.sin(ph))))))
    # Puff (6): draw breath (0-1, belly swells), SQUEEZE (2: the cap slams down, spores burst out of the gills at (8, -7)), vent, recover
    puff_ = [S(belly=1.12, bob=0.4, face="puff"), S(belly=1.2, bob=0.8, squash=-0.6, face="puff", tilt=-6, lean=-6),
             S(belly=0.8, squash=1.4, face="puff", lean=8, cloud=(9.0, -7.0, 3.2, 5.0, "sporec", 0, 3, 5)),
             S(belly=0.85, squash=0.8, face="puff", lean=6, cloud=(11.0, -7.0, 3.6, 5.0, "sporec", 1, 3, 5)),
             S(belly=0.92, squash=0.3, lean=2), S()]
    # Scatter (6): shakes its cap (0-2), two seeds fall out of the gills (3) and drop (4) beside its feet, settle (5)
    scat = [S(tilt=-12, lean=-4, face="puff"), S(tilt=12, lean=4, face="puff"), S(tilt=-14, lean=-5, face="puff", cap_dy=-0.6),
            S(tilt=10, lean=3, face="puff", seeds=[(-6.0, -6.0, 1), (6.5, -5.0, 1)]),
            S(tilt=-4, seeds=[(-7.0, -1.5, 0), (7.5, -1.5, 0)]), S()]
    d0 = S(face="hurt", lean=-12, tilt=-14, squash=0.4)
    d1 = S(face="hurt", lean=-6, tilt=-20, squash=1.4, cap_crack=1, belly=0.9)
    d2 = S(face="dead", squash=2.6, cap_crack=2, belly=0.7, cap_dy=2.0, feet=((-4.0, 0.0), (4.0, 0.0)),
           cloud=(0.0, -6.0, 3.0, 2.0, "sporec", 2, 7, 4))
    corpse = _sporeling_corpse()
    knock = S(face="hurt", lean=-14, tilt=-10, bob=-0.6)
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.08] * 6),
             ("Puff", puff_, [0.14, 0.12, 0.06, 0.1, 0.12, 0.12]),
             ("Scatter", scat, [0.1, 0.1, 0.1, 0.08, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("SylSporeling", anims, outdir, scale=6)


def _sporeling_corpse():
    r = Rig()
    r.ell(0.0, -1.6, 5.0, 1.6, "mould", 0.0)
    r.ell(0.6, -1.4, 3.0, 1.0, "podf", 0.1, bias=-0.2)
    cap(r, 1.5, -2.2, 7.5, 2.6, 1.0, mat="mould", spots="bruise", gill="corpse", tilt=8, nspots=4, seed=9)
    r.polyline([(0, -4), (1, -3), (0, -2)], "chitin", 1.2, tone=1)
    r.stamp(SPORE_FACE["dead"], -4.0, -1.0, 1.3, SPORE_LEG, pivot=(3, 1))
    return r.resolve()


# ================================================================== THORNBITER: a thorny tangle with a fanged rosebud on a stalk
BUD_LEG = {"r": ("blood", 1), "R": ("blood", 2), "L": ("blood", 3), "H": ("blood", 4), "m": ("chitin", 0), "t": ("thorn", 3),
           "T": ("thorn", 4), "g": ("moss", 2), "G": ("moss", 3), "e": ("eye", 3)}
BUD_HEAD = {
    # pivot (1, 3): where the stalk meets the bud. Blood-red petals close over a row of thorn fangs.
    "shut": """
..LHL.
.RLLLr
gRRLRRr
gGRRRr.
.gRtr..
""",
    "open": """
..LHL..
.RLLLrr
gRmmtmT
gGm....
gGRtmt.
.gRRrr.
""",
    "wide": """
.LHL...
RLLLr..
gRmmtmT
gm.....
gm.....
gRtmt.T
.gRRrr.
""",
    "dead": """
......
.rRRr.
gRmRRr
gGRmRr
.gggg.
""",
}


def thornbiter(sway=0.0, head=None, bud="shut", lean=0.0, bob=0.0, legs=0.0, smear=None, extra=None, coil=0.0, tangle=1.0,
               head_z=3.0, stalk_mid=None):
    r = Rig()
    # the tangle: three loops of thorny vine heaped round a knot, rooted to the floor by tendrils
    b = bob
    for k, (cx, cy, rx, ry, z, a) in enumerate(((-2.0, -4.2, 4.0, 3.0, -0.6, -10), (1.0, -3.6, 4.0, 2.8, 0.4, 15),
                                                 (-1.0, -6.4, 3.4, 2.4, 0.0, 0))):
        pts = []
        for i in range(10):
            t = i / 9 * math.tau * 0.9 + k
            pts.append((cx + rx * tangle * math.cos(t) + lean * 0.05 * (cy - (-3)), cy + b + ry * tangle * math.sin(t)))
        vine(r, pts, [1.2, 1.0], z, mat="moss" if k != 1 else "rot", thorns=2, seed=k + 2, bias=-0.1 * k, tlen=1)
    r.ell(-1.0, -4.4 + b, 3.0, 2.4, "bark", 0.2, bias=-0.15)
    for k, x in enumerate((-5.0, -1.0, 3.0)):
        ph = legs + k * 2.1
        r.tube([(x, -2.0 + b), (x + 1.0 * math.sin(ph), -0.8), (x + 1.6 + 1.2 * math.sin(ph), 0.0)], [0.9, 0.7, 0.5], "bark", 0.6 - k * 0.3)
    # the stalk arching forward to the bud
    hx, hy = head or (6.5 + sway, -11.0 + bob)
    mx, my = stalk_mid or ((hx - 1.0) * 0.45 - 1.0 - coil, -13.5 + bob - coil * 0.5)
    sp = [(0.0, -6.0 + b), (mx * 0.5, (my - 6.0 + b) * 0.55), (mx, my), (hx - 1.2, hy + 0.6)]
    vine(r, sp, [1.3, 1.1, 0.9, 0.8], 2.0, mat="moss", thorns=2, seed=7, tlen=1)
    leaf(r, mx - 1.0, my + 1.0, 200, 3.5, 2.1)
    r.stamp(BUD_HEAD[bud], hx, hy, head_z, BUD_LEG, pivot=(1, 3))
    smears(r, smear)
    if extra: extra(r)
    return r.resolve()


def root_line(r, x0, x1, k, z=4.0):
    """Roots racing along the floor from x0 to x1 (k: 0 just broken out .. 2 thrashing)."""
    for i, x in enumerate(range(int(x0), int(x1) + 1, 2)):
        h = 1 + ((i + k) % 3 == 0) + (1 if i == (x1 - x0) // 2 - k else 0)
        r.tube([(x, 0.0), (x + 0.6, -h)], [0.8, 0.5], "bark", z, bias=0.1)
        if i % 2 == 0: r.dot(x + 1, -h - 0.5, "moss", 3, z + 0.1)


def thornbiter_sheet(outdir):
    TB = thornbiter
    idle = [TB(sway=[0, 0.6, 1.0, 0.6][i], bob=[0, 0.2, 0.4, 0.2][i], head=(6.0 + [0, 0.4, 0.8, 0.4][i], -11.0 + [0, -0.4, -0.6, -0.4][i]),
               bud="shut" if i != 2 else "open") for i in range(4)]
    run = [TB(sway=0.8 * math.sin(i / 6 * math.tau), bob=-0.6 * abs(math.sin(i / 6 * math.tau)), legs=i / 6 * math.tau, lean=6,
              head=(9.0, -11.5 - 0.6 * abs(math.sin(i / 6 * math.tau))), tangle=1.0 + 0.04 * math.sin(i / 6 * math.tau * 2)) for i in range(6)]
    # Whip (7): coils back (0-1), the stalk lashes out (2 smear), FULL REACH (3: bud at (26, -7), hit box 22 x 14 at (14, -8)),
    # follow-through (4), recoil (5-6)
    whip = [TB(head=(4.0, -14.0), coil=2.0, bud="open"), TB(head=(-1.0, -15.0), coil=4.0, bud="wide", stalk_mid=(-3.0, -16.0)),
            TB(head=(14.0, -11.0), bud="wide", stalk_mid=(5.0, -15.0), smear=[("arc", 0.0, -8.0, 14.0, -120, -30, "moss", 2)]),
            TB(head=(25.0, -7.0), bud="wide", stalk_mid=(12.0, -11.0), lean=4, smear=[("line", [(9, -12), (22, -9)], "moss", 2)]),
            TB(head=(20.0, -6.0), bud="shut", stalk_mid=(10.0, -10.0)), TB(head=(12.0, -9.0), bud="shut"), TB()]
    # RootRun (7): rears up (0-1), drives its roots into the floor (2-3: roots break out at (10, 0) and race off), settles (4-6)
    rr = [TB(head=(5.0, -15.0), coil=1.5, bud="open", bob=-0.5), TB(head=(3.0, -17.0), coil=3.0, bud="wide", bob=-1.0, tangle=1.06),
          TB(head=(9.0, -5.0), bud="shut", tangle=0.94, stalk_mid=(6.0, -10.0), extra=lambda r: soil(r, 9.0, 0.0, 0)),
          TB(head=(9.0, -4.0), bud="shut", tangle=0.92, stalk_mid=(6.0, -9.0), extra=lambda r: (soil(r, 9.0, 0.0, 1), root_line(r, 11, 17, 0))),
          TB(head=(9.0, -6.0), bud="shut", extra=lambda r: root_line(r, 11, 17, 1)), TB(head=(8.5, -9.0)), TB()]
    d0 = TB(bud="wide", head=(5.0, -14.0), coil=2.0)
    d1 = TB(bud="dead", head=(10.0, -6.0), stalk_mid=(6.0, -9.0), tangle=0.9)
    d2 = _thorn_corpse(0)
    corpse = _thorn_corpse(1)
    knock = TB(bud="open", head=(4.0, -13.0), coil=2.0, lean=-6)
    anims = [("Idle", idle, [0.16, 0.13, 0.16, 0.13]), ("Run", run, [0.08] * 6),
             ("Whip", whip, [0.12, 0.1, 0.05, 0.08, 0.1, 0.1, 0.12]),
             ("RootRun", rr, [0.12, 0.12, 0.06, 0.1, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylThornbiter", anims, outdir, scale=6)


def _thorn_corpse(stage):
    r = Rig()
    for k, (cx, rx) in enumerate(((-3.0, 5.0), (2.0, 4.6))):
        pts = [(cx + rx * math.cos(i / 9 * math.tau), -2.0 + 1.6 * math.sin(i / 9 * math.tau)) for i in range(10)]
        vine(r, pts, [1.1, 0.9], k * 0.3, mat="rot" if k else "moss", thorns=3, seed=k + 5, bias=-0.2)
    r.tube([(0.0, -3.0), (5.0, -2.0), (9.0, -1.2)], [1.0, 0.9, 0.8], "moss", 0.8)
    r.stamp(BUD_HEAD["dead"], 10.0, -1.0 + (0 if stage else 1), 1.0, BUD_LEG, pivot=(1, 3))
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.2)
    return r.resolve()


# ================================================================== ROTFLY: a bloated fly with a bruise-purple belly
FLY_LEG = {"e": ("rot", 2), "E": ("rot", 3), "W": ("mould", 4), "m": ("chitin", 0), "k": ("chitin", 1), "c": ("chitin", 2),
           "p": ("bruise", 2), "y": ("pollen", 3)}
FLY_HEAD = {
    # pivot (1, 2): the neck. Two big cloudy green eyes over a short proboscis
    "calm": """
.EEe.
EWEee
eEEek
.kcck
..m..
""",
    "spit": """
.EEe.
EWEee
eEEek
.kccy
..my.
""",
    "hurt": """
.eEe.
EmEee
eEEek
.kcck
.m.m.
""",
    "dead": """
.eee.
emeek
eeemk
.kcck
""",
}


def rotfly(alt=4.0, flap=0.0, lean=0.0, legs=0.0, face="calm", belly=1.0, head_d=(0.0, 0.0), extra=None, smear=None, glob=None,
           wings_up=True):
    r = Rig()
    oy = -alt
    T = Xf(lean, (0.0, oy - 5.0))
    # dangling legs from the thorax
    for k in range(3):
        sx, sy = T(1.0 + k * 1.2, oy - 4.0)
        a = 100 + k * 8 + 10 * math.sin(legs + k)
        pts = chain(sx, sy, [(2.0, a), (1.8, a + 20)])
        r.tube(pts, [0.5, 0.4], "chitin", -0.5 if k % 2 else 0.6, flat=1 if k % 2 else 2)
    # abdomen: a bloated bruise-purple sac with rot-green bands; thorax; head
    bx, by = T(-2.4, oy - 5.0)
    r.ell(bx, by, 4.6 * belly, 4.0 * belly, "bruise", 0.0, bias=0.08, ang=lean * 0.5)
    for k in (-1, 1):
        r.ell(bx + k * 1.8, by - 0.2, 0.6, 3.2 * belly, "rot", 0.05, bias=0.0, ang=lean * 0.5)
    r.ell(bx - 1.8, by - 1.4, 1.2, 0.8, "bruise", 0.1, bias=0.5)
    tx, ty = T(2.4, oy - 6.0)
    r.ell(tx, ty, 2.4, 2.2, "chitin", 0.5, bias=0.1)
    # wings: two small blurred wings above the thorax
    for k, (a0, z) in enumerate(((-120 + flap, -1.0), (-100 + flap * 0.7, 1.2))):
        wing(r, (tx - 0.5, ty - 1.5), a0 if wings_up else a0 + 60, 6.5 - k, 2.6, z, veins=1, tone=2 if k == 0 else 3)
    hx, hy = T(5.0 + head_d[0], oy - 7.0 + head_d[1])
    r.stamp(FLY_HEAD[face], hx, hy, 1.5, FLY_LEG, pivot=(1, 2))
    if glob:
        gx, gy, gs = glob
        r.ell(gx, gy, gs, gs * 0.9, "bile", 3.0, bias=0.2)
    smears(r, smear)
    if extra: extra(r)
    return r.resolve()


def rotfly_sheet(outdir):
    F = rotfly
    idle = [F(alt=4.0 + [0, 0.5, 1.0, 0.5][i], flap=[0, 40, 10, 40][i], legs=i, belly=[1, 1.03, 1.05, 1.03][i]) for i in range(4)]
    run = [F(alt=4.0 + 0.6 * math.sin(i / 6 * math.tau), flap=[0, 45, 15, 45, 0, 45][i], lean=12, legs=i * 0.7) for i in range(6)]
    # Spit (6): rears back, belly heaving (0-1), SPIT (2: glob leaves the mouth at (9, -10)), recoil, recover
    spit = [F(lean=-10, belly=1.08, face="spit", flap=20), F(lean=-16, belly=1.12, face="spit", flap=40, head_d=(-0.5, -0.5)),
            F(lean=10, belly=0.92, face="spit", flap=0, head_d=(0.8, 0.5), glob=(9.5, -10.0, 1.4),
              smear=[("line", [(4, -10), (8, -10)], "bile", 2)]),
            F(lean=6, belly=0.95, flap=40), F(lean=2, flap=10), F()]
    # Dive (8): climbs (0-1), DIVES (2-3, steep, smeared), BURSTS a puff on the hero (4: puff at (6, -2)), climbs back (5-7)
    dive = [F(alt=6.0, lean=-14, flap=40, face="spit"), F(alt=7.0, lean=-20, flap=0, face="spit", belly=1.06),
            F(alt=3.5, lean=36, flap=50, face="spit", smear=[("line", [(-6, -14), (-2, -10)], "bruise", 2)]),
            F(alt=1.5, lean=48, flap=10, face="spit", smear=[("line", [(-4, -10), (0, -6)], "bruise", 2), ("line", [(-6, -9), (-2, -5)], "bruise", 1)]),
            F(alt=1.0, lean=40, flap=60, belly=0.9, extra=lambda r: puff(r, 6.0, -3.0, 3.0, 6.0, "sporec", 0, 5, 5)),
            F(alt=3.0, lean=-10, flap=0, extra=lambda r: puff(r, 8.0, -3.0, 3.4, 6.0, "sporec", 2, 5, 4)),
            F(alt=5.0, lean=-14, flap=40), F(alt=4.5, lean=-4, flap=10)]
    d0 = F(face="hurt", lean=-24, flap=60)
    d1 = F(face="dead", lean=-60, alt=2.0, flap=90, belly=0.95)
    d2 = _fly_corpse(0)
    corpse = _fly_corpse(1)
    knock = F(face="hurt", lean=-28, flap=50, alt=4.5)
    anims = [("Idle", idle, [0.07] * 4), ("Run", run, [0.06] * 6),
             ("Spit", spit, [0.12, 0.12, 0.05, 0.1, 0.1, 0.1]),
             ("Dive", dive, [0.1, 0.1, 0.06, 0.06, 0.08, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("SylRotfly", anims, outdir, scale=6)


def _fly_corpse(stage):
    r = Rig()
    r.ell(-1.0, -2.6, 4.4, 2.6, "bruise", 0.0)
    r.ell(-1.6, -3.2, 0.6, 2.0, "rot", 0.05)
    r.ell(3.5, -2.2, 2.0, 1.8, "chitin", 0.3)
    r.stamp(FLY_HEAD["dead"], 6.0, -1.0, 1.0, FLY_LEG, pivot=(1, 2))
    for k in range(3):
        r.polyline([(1.0 + k * 1.2, -4.4), (1.5 + k * 1.2 + (k - 1), -6.6 + (k % 2))], "chitin", 0.6, tone=1)
    wing(r, (2.0, -3.0), -170 if stage else -150, 5.0, 1.4, -0.5, veins=1)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.0)
    return r.resolve()


# ================================================================== SPROUT: a seed pod with a seedling on top (the Rot Mother's)
SPROUT_LEG = {"m": ("chitin", 0), "g": ("glowg", 3), "p": ("podf", 1)}


def sprout(bob=0.0, squash=0.0, lean=0.0, legs=0.0, open_=0.0, sink=0.0, extra=None, face="calm", leaves=1.0):
    r = Rig()
    T = Xf(lean, (0.0, -2.0))
    for k in (-1, 1):
        ph = legs + (0 if k < 0 else math.pi)
        r.tube([T(k * 1.8, -2.4 + bob + sink), (k * 2.6 + 0.8 * math.sin(ph), -max(0.0, 0.8 * math.cos(ph)) + sink * 0.2)],
               [0.9, 0.6], "bark", 0.5 * k)
    cx, cy = T(0.0, -5.5 + bob + squash * 0.6 + sink)
    r.ell(cx, cy, 4.2 + squash * 0.5, 4.0 - squash * 0.6, "rot", 0.0, bias=0.05)
    r.ell(cx + 0.4, cy - 0.4, 2.6, 3.2, "podf", 0.1, bias=0.05, clip=lambda x, y: abs(x - cx - 0.4) < 1.0 + open_ * 1.5)
    r.stamp("""
m.m
g.g
""" if face == "calm" else """
m.m
m.m
""", cx + 1.5, cy - 0.5, 0.5, SPROUT_LEG, pivot=(1, 1))
    # the seedling: a stem and two leaves
    sx, sy = cx, cy - 4.0
    r.tube([(sx, sy + 0.5), (sx + 0.3, sy - 2.6 * leaves)], [0.6, 0.5], "moss", 0.3)
    leaf(r, sx + 0.3, sy - 2.6 * leaves, -150 - 10 * bob, 3.2 * leaves, 0.4)
    leaf(r, sx + 0.3, sy - 2.6 * leaves, -30 + 10 * bob, 3.6 * leaves, 0.45)
    if extra: extra(r)
    return r.resolve()


def sprout_sheet(outdir):
    S = sprout
    idle = [S(bob=[0, 0.3, 0.5, 0.3][i]) for i in range(4)]
    run = [S(bob=-0.6 * abs(math.sin(i / 6 * math.tau)), lean=8, legs=i / 6 * math.tau) for i in range(6)]
    # Puff (6): swell (0-1), the husk splits and spores burst at (6, -5) (2), vent (3), close (4-5)
    puff_ = [S(squash=-0.5), S(squash=-0.8, lean=-6), S(squash=0.8, open_=1.0, lean=6, extra=lambda r: puff(r, 7.0, -5.0, 2.4, 5.0, "sporec", 0, 2, 4)),
             S(squash=0.4, open_=0.6, lean=4, extra=lambda r: puff(r, 8.5, -5.0, 2.8, 5.0, "sporec", 1, 2, 4)), S(open_=0.2), S()]
    # Rise (5): bursts up through the floor (the code spawns it under the dirt burst)
    rise = [S(sink=7.0, leaves=0.5, extra=lambda r: soil(r, 0.0, 0.0, 0)), S(sink=4.0, leaves=0.8, extra=lambda r: soil(r, 0.0, 0.0, 0)),
            S(sink=1.0, squash=-0.6, extra=lambda r: soil(r, 0.0, 0.0, 1)), S(squash=0.5, extra=lambda r: soil(r, 0.0, 0.0, 2)), S()]
    d0 = S(squash=-0.4, lean=-14, face="dead")
    d1 = S(squash=1.6, open_=1.0, face="dead", extra=lambda r: puff(r, 0.0, -6.0, 3.0, 5.0, "sporec", 1, 6, 4))
    d2 = S(squash=2.6, open_=1.0, face="dead", leaves=0.6, sink=1.0)
    corpse = S(squash=3.2, open_=1.0, face="dead", leaves=0.5, sink=1.6)
    knock = S(lean=-16, squash=-0.3, face="dead")
    anims = [("Idle", idle, [0.15, 0.12, 0.15, 0.12]), ("Run", run, [0.08] * 6),
             ("Puff", puff_, [0.12, 0.1, 0.06, 0.1, 0.1, 0.1]), ("Rise", rise, [0.06, 0.06, 0.08, 0.08, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.08, 0.1, 0.12, 0.4], knock)
    return sheet("SylSprout", anims, outdir, scale=6)


JOBS = [("SylSporeling", sporeling_sheet), ("SylThornbiter", thornbiter_sheet), ("SylRotfly", rotfly_sheet), ("SylSprout", sprout_sheet)]

SYNC = {
    "SylSporeling": {"Puff": [("SQUEEZE: spores burst from the gills at (9, -7)", 2)], "Scatter": [("two seeds fall from the cap", 3)]},
    "SylThornbiter": {"Whip": [("FULL REACH: bud at (25, -7); hit box 22 x 14 centred (15, -9)", 3)],
                      "RootRun": [("roots break out at (10, 0) and race at the hero", 2)]},
    "SylRotfly": {"Spit": [("glob leaves the mouth at (9, -10)", 2)], "Dive": [("dive starts", 2), ("BURST: puff on the hero at (6, -3)", 4)]},
    "SylSprout": {"Puff": [("husk splits: spores at (7, -5)", 2)]},
}
NOTES = {"SylRotfly": "Flies: hovers 4 px over the feet point (counted in the 16 px T1 height)."}
