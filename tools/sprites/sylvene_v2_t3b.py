"""Sylvene tier 3, the vine and insect finals: Carrion Lily, Briar Wyrm, Pollen Monarch, The Sower (new), Blight Bellows,
Carrion Queen. Built through sylvene_v2_rigs.py. T3 idle limit 42 x 40 (fliers count their hover)."""
import math
from sylvene_v2_rigs import (Rig, Xf, chain, ik, lerp, sheet, tail_anims, cap, vine, thorn, leaf, wing, pod, motes, puff,
                             smears, sparks, soil, dust_puff)
from sylvene_v2_t2 import arm, legs


# ================================================================== CARRION LILY: a corpse lily on a thick stalk
def lily_head(r, x, y, z, open_=0.0, ang=0.0, size=1.5, bite=0.0):
    """The bloom facing right: five huge rot-red petals blotched white round a pit of a mouth. open_ spreads the petals
    (Corpse Bloom); bite closes them into jaws."""
    T = Xf(ang, (x, y))
    s = size
    spread = 1.0 + 0.5 * open_ - 0.45 * bite
    for k, a in enumerate((-150, -95, -40, 30, 85)):
        aa = math.radians(a * spread + (0 if a > -60 else -10 * open_))
        tip = T(x + 7.5 * s * math.cos(aa), y + 6.5 * s * math.sin(aa))
        base = T(x, y)
        perp = (-math.sin(aa), math.cos(aa))
        mid = T(x + 4.5 * s * math.cos(aa), y + 4.0 * s * math.sin(aa))
        pts = [base, (mid[0] + perp[0] * 2.6 * s, mid[1] + perp[1] * 2.6 * s), tip, (mid[0] - perp[0] * 2.6 * s, mid[1] - perp[1] * 2.6 * s)]
        r.poly(pts, "rotred", z + (0.1 if math.sin(aa) > 0 else 0.0) + k * 0.001, normal=(-0.3 + 0.4 * math.cos(aa), -0.5, 0.8))
        # the white blotches
        r.dot(*T(x + 4.2 * s * math.cos(aa), y + 3.6 * s * math.sin(aa)), "lily", 3, z + 0.2)
        if k % 2 == 0: r.dot(*T(x + 5.6 * s * math.cos(aa) + 1, y + 4.8 * s * math.sin(aa)), "lily", 2, z + 0.2)
    # the pit: a dark throat ringed with pale stamens
    r.ell(*T(x + 1.0, y), 2.6 * s, 2.4 * s, "chitin", z + 0.3, bias=-0.3)
    for k in range(5):
        a = k / 5 * math.tau
        r.dot(*T(x + 1.0 + 2.4 * s * math.cos(a), y + 2.2 * s * math.sin(a)), "bile", 4, z + 0.31)
    r.dot(*T(x + 1.5, y - 0.5), "eye", 3, z + 0.32)


def carrion_lily(sway=0.0, head=(8.0, -26.0), open_=0.0, bite=0.0, planted=True, step=0.0, lean=0.0, mid=None, smear=None,
                 spark=None, extra=None, sink=0.0, droop=0.0, cloud=None, dig=0.0):
    r = Rig()
    # roots: dug in (planted) or dangling and walking
    for k in range(6):
        x = -6.0 + k * 2.4
        if planted:
            r.tube([(x * 0.4, -6.0 + sink), (x * 0.9, -2.0), (x * 1.3 + (1 if k % 2 else -1), 0.0)], [1.4, 1.0, 0.8], "bark", -0.5 + 0.1 * k,
                   bias=-0.1 * (k % 2))
            r.dot(x * 1.3, 0.0, "bark", 0, -0.4 + 0.1 * k)
            if dig: soil(r, x * 1.3, 0.0, 0 if dig > 1 else 1, 0.5)
        else:
            ph = step + k * 1.1
            lift = max(0.0, math.sin(ph)) * 2.0
            r.tube([(x * 0.4, -7.0 + sink), (x * 0.8 + math.cos(ph), -3.0 - lift * 0.5), (x * 1.1 + 1.4 * math.cos(ph), -0.4 - lift)],
                   [1.3, 0.9, 0.6], "bark", -0.5 + 0.1 * k, bias=-0.1 * (k % 2))
    # the bulb the stalk rises from: rotting, with a few leaves
    r.ell(0.0, -7.5 + sink, 7.0, 4.4, "rot", 0.0, bias=0.05)
    for a in (-165, -15, -125, -55):
        leaf(r, 0.0, -8.0 + sink, a, 9.0, 0.1, mat="moss", w=2.4)
    # the thick stalk to the bloom
    hx, hy = head
    mx, my = mid or (lerp(0.0, hx, 0.35) - 3.0 + sway, lerp(-10.0, hy, 0.55))
    vine(r, [(0.0, -9.0 + sink), (mx, my), (hx - 2.0, hy + 2.0)], [3.0, 2.4, 1.8], 0.5, mat="rot", thorns=3, seed=8, tlen=1)
    lily_head(r, hx, hy, 2.0, open_=open_, ang=lean + droop, bite=bite)
    if cloud:
        k, x0, y0 = cloud
        for i in range(5):
            d = 4.0 + i * 3.8
            for side in (-1, 0, 1):
                puff(r, x0 + d, y0 + side * d * 0.55, 1.8 + i * 0.5, 6.0 + i * 0.01, "gas", min(3, max(0, k + (i > 3))), seed=i + side * 7, n=4)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def lily_sheet(outdir):
    L = carrion_lily
    idle = [L(planted=False, sway=[0, 0.5, 1.0, 0.5][i], head=(8.0 + [0, 0.5, 1.0, 0.5][i], -26.0 + [0, 0.3, 0.6, 0.3][i]), step=0.0)
            for i in range(4)]
    run = [L(planted=False, step=i / 6 * math.tau, sway=-1.0, head=(9.0, -25.0 + 0.6 * math.sin(i / 6 * math.tau)), lean=4) for i in range(6)]
    pidle = [L(planted=True, sway=[0, 0.5, 1.0, 0.5][i], head=(8.0 + [0, 0.5, 1.0, 0.5][i], -26.0 + [0, 0.3, 0.6, 0.3][i])) for i in range(4)]
    # Plant (3): the roots bore into the floor
    plant = [L(planted=False, step=1.5, sink=1.0), L(planted=True, dig=2, sink=0.5), L(planted=True, dig=1)]
    # Lunge (7): the bloom draws back (0-1), STRIKES on its stalk (2-3: bite at (24, -11)), holds, recoils (5-6)
    ln = [L(planted=False, head=(4.0, -28.0), bite=0.0, open_=0.5), L(planted=False, head=(1.0, -29.0), open_=0.8, mid=(-2.0, -18.0)),
          L(planted=False, head=(18.0, -16.0), open_=0.6, mid=(6.0, -18.0), smear=[("arc", 6.0, -14.0, 14.0, -100, -30, "rotred", 2)]),
          L(planted=False, head=(22.0, -12.0), bite=1.0, mid=(9.0, -15.0), spark=[(28.0, -12.0, 2)]),
          L(planted=False, head=(20.0, -13.0), bite=0.6, mid=(8.0, -16.0)), L(planted=False, head=(13.0, -20.0)), L(planted=False)]
    # LungeFar (7): planted, the stalk reaches 40 px (bite at (38, -10))
    lf = [L(head=(4.0, -28.0), open_=0.5, dig=1), L(head=(0.0, -30.0), open_=0.8, mid=(-3.0, -19.0)),
          L(head=(26.0, -14.0), open_=0.6, mid=(12.0, -18.0), smear=[("arc", 10.0, -12.0, 18.0, -100, -25, "rotred", 2)]),
          L(head=(35.0, -10.0), bite=1.0, mid=(16.0, -15.0), spark=[(41.0, -10.0, 2)]),
          L(head=(32.0, -11.0), bite=0.6, mid=(15.0, -16.0)), L(head=(18.0, -20.0), mid=(6.0, -20.0)), L()]
    # Bloom (8): the petals swell (0-2), OPEN WIDE (3), BREATHES rot (4-6: a 120 degree cone from the pit at (12, -24)), close (7)
    bl = [L(open_=0.3, head=(7.0, -27.0)), L(open_=0.6, head=(6.0, -28.0)), L(open_=0.9, head=(6.0, -28.5)),
          L(open_=1.2, head=(8.0, -26.0), cloud=(0, 9.0, -26.0)), L(open_=1.2, head=(8.5, -26.0), cloud=(1, 9.0, -26.0)),
          L(open_=1.1, head=(8.5, -26.0), cloud=(2, 9.0, -26.0)), L(open_=0.6, head=(8.0, -26.0)), L()]
    d0 = L(open_=0.8, head=(4.0, -28.0), planted=False)
    d1 = L(planted=False, head=(12.0, -12.0), droop=40, mid=(6.0, -14.0), sink=1.0)
    d2 = _lily_corpse(0)
    corpse = _lily_corpse(1)
    knock = L(planted=False, open_=0.5, head=(4.0, -27.0), lean=-10)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6), ("IdlePlanted", pidle, [0.2, 0.17, 0.2, 0.17]),
             ("Plant", plant, [0.1, 0.12, 0.12]),
             ("Lunge", ln, [0.12, 0.1, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("LungeFar", lf, [0.12, 0.1, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Bloom", bl, [0.12, 0.12, 0.12, 0.08, 0.15, 0.15, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylCarrionLily", anims, outdir, scale=3)


def _lily_corpse(stage):
    r = Rig()
    r.ell(-4.0, -3.0, 6.0, 3.0, "rot", 0.0)
    for k in range(4):
        r.tube([(-6.0 + k * 2, -2.0), (-9.0 + k * 1.5, 0.0)], [1.0, 0.7], "bark", -0.3)
    vine(r, [(-1.0, -3.0), (6.0, -2.4), (12.0, -2.0)], [2.0, 1.6, 1.4], 0.3, mat="rot", thorns=2, seed=3, tlen=1)
    lily_head(r, 16.0, -3.0 + stage, 0.8, open_=0.2, ang=70, size=1.0)
    if stage == 0: dust_puff(r, 2.0, 0, 1, 1.8)
    return r.resolve()


# ================================================================== BRIAR WYRM: a long bramble serpent, a mace of thorns on its tail
WYRM_LEG = {"k": ("moss", 0), "d": ("moss", 1), "g": ("moss", 2), "G": ("moss", 3), "H": ("moss", 4), "m": ("chitin", 0),
            "e": ("eye", 3), "E": ("eye", 4), "t": ("thorn", 3), "T": ("thorn", 4), "b": ("bark", 2)}
WYRM_HEAD = {
    # pivot (0, 4): the neck. A long wedge head of plaited vine, a red eye, thorn teeth
    "calm": """
..gGG....
.gGHGGg..
dgmEgGGg.
dgGGGGGGg
.dgtgtgTk
..ddkkk..
""",
    "roar": """
..gGG....
.gGHGGg..
dgmEgGg..
dgGGGg.T.
dgt...t..
.dgtgtgT.
..ddkkk..
""",
    "dead": """
.........
..gGG....
.gGGGg...
dgmmgGGg.
dgGGGGGGk
.ddkkkk..
""",
}


def mace(r, x, y, z, rad=4.2, spin=0.0):
    r.ell(x, y, rad, rad, "bark", z, bias=0.1)
    for k in range(8):
        a = k / 8 * math.tau + spin
        thorn(r, x + rad * math.cos(a), y + rad * math.sin(a), math.degrees(a), 2.4, z + 0.05, mat="thorn", tip=None)


def briar_wyrm(phase=0.0, head=(14.0, -12.0), tail=(-13.0, -27.0), face="calm", amp=1.0, coil=0.0, spin=0.0, smear=None,
               spark=None, extra=None, mace_spin=0.0, rise=0.0):
    r = Rig()
    hx, hy = head
    tx, ty = tail
    # the body: a long S along the floor from the neck back to where the tail rises to the mace
    pts = []
    n = 16
    for i in range(n + 1):
        t = i / n
        if t < 0.25:
            x = lerp(hx - 2.0, 5.0, t / 0.25); y = lerp(hy + 2.0, -3.5, t / 0.25) - rise * math.sin(t / 0.25 * math.pi)
        elif t < 0.75:
            u = (t - 0.25) / 0.5
            x = lerp(5.0, -9.0, u) + coil * math.cos(u * math.tau) * 3.0
            y = -3.0 - amp * 1.5 * math.sin(phase + u * 6.0) - coil * math.sin(u * math.tau) * 3.0
        else:
            u = (t - 0.75) / 0.25
            x = lerp(-9.0, tx, u); y = lerp(-3.0, ty + 3.0, u * u)
        pts.append((x, y))
    rad = [lerp(4.0, 5.2, min(1.0, i / 5.0)) if i < 10 else lerp(5.2, 2.0, (i - 10) / 6.0) for i in range(n + 1)]
    r.tube(pts, rad, "moss", 0.0, bias=0.05)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r.line(x0, y0 - rad[i] * 0.5, x1, y1 + rad[i + 1] * 0.3, "bark", 0.05, tone=2 if i % 2 else 3)
    vine(r, pts, [0.1], 0.1, mat="moss", thorns=9, seed=2, tlen=2, tmat="thorn", tip=None)
    for i, a in ((3, -120), (6, -60), (9, -140), (12, -100)):
        leaf(r, pts[i][0], pts[i][1] - rad[i] + 0.5, a, 4.0, 0.12, mat="moss", w=1.6)
    # the belly plates in thorn white
    for i in range(2, 12, 2):
        r.dot(pts[i][0], pts[i][1] + rad[i] - 0.5, "thorn", 2, 0.06)
    mace(r, tx, ty, 1.0 if ty > -20 else -1.0, spin=mace_spin)
    r.stamp(WYRM_HEAD[face], hx, hy, 1.2, WYRM_LEG, pivot=(0, 4))
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def wyrm_sheet(outdir):
    W = briar_wyrm
    idle = [W(phase=i * 0.5, head=(14.0, -12.0 + [0, -0.4, -0.8, -0.4][i]), tail=(-13.0, -27.0 + [0, 0.6, 1.2, 0.6][i]), mace_spin=i * 0.2)
            for i in range(4)]
    run = [W(phase=i / 6 * math.tau, amp=1.5, head=(15.0, -11.0 + 0.6 * math.sin(i / 6 * math.tau)), tail=(-13.0, -25.0 - math.sin(i / 6 * math.tau)))
           for i in range(6)]
    # Mace (8): the mace winds up OVER ITS HEAD (0-2, the tell), CRACKS DOWN IN FRONT (3: mace at (20, -4)), drags round (4-5),
    # SWINGS BEHIND (6: mace at (-22, -6)), recover (7)
    mc = [W(tail=(-6.0, -30.0), face="roar"), W(tail=(2.0, -33.0), face="roar", rise=1.0), W(tail=(8.0, -33.0), face="roar", rise=1.5),
          W(tail=(21.0, -6.0), face="roar", head=(13.0, -14.0), smear=[("arc", 8.0, -14.0, 13.0, -100, 40, "thorn", 2)], spark=[(22.0, -3.0, 1)]),
          W(tail=(14.0, -12.0), head=(13.0, -14.0)), W(tail=(-4.0, -20.0)),
          W(tail=(-23.0, -6.0), face="roar", smear=[("arc", -8.0, -12.0, 14.0, -60, -200, "thorn", 2)], spark=[(-24.0, -3.0, 1)]),
          W(tail=(-16.0, -20.0))]
    # Spiral (10): coils (0-1), SPINS (2-8: the thorns fly, two arms turning), uncoils (9)
    sp = [W(coil=0.6, head=(12.0, -14.0), tail=(-8.0, -24.0)), W(coil=1.0, head=(8.0, -16.0), tail=(-4.0, -26.0), face="roar")]
    for k in range(7):
        a = k / 7 * math.tau
        sp.append(W(coil=1.2, head=(8.0 * math.cos(a) + 2.0, -10.0 - 5.0 * math.sin(a)), tail=(-8.0 * math.cos(a), -18.0 + 5.0 * math.sin(a)),
                    face="roar", mace_spin=k * 0.8,
                    smear=[("arc", 0.0, -12.0, 14.0, math.degrees(a) - 80, math.degrees(a), "moss", 2)]))
    sp.append(W(coil=0.4))
    d0 = W(face="roar", rise=2.0, head=(12.0, -16.0))
    d1 = W(face="dead", head=(16.0, -6.0), tail=(-16.0, -8.0), amp=0.5)
    d2 = W(face="dead", head=(16.0, -4.0), tail=(-18.0, -4.0), amp=0.3, extra=lambda r: dust_puff(r, 0.0, 0, 1, 2.0))
    corpse = W(face="dead", head=(16.0, -4.0), tail=(-18.0, -3.5), amp=0.2)
    knock = W(face="roar", head=(11.0, -15.0), rise=2.0, amp=1.8)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.08] * 6),
             ("Mace", mc, [0.12, 0.12, 0.14, 0.05, 0.08, 0.08, 0.05, 0.14]),
             ("Spiral", sp, [0.12, 0.12] + [0.21] * 7 + [0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylBriarWyrm", anims, outdir, scale=3)


# ================================================================== POLLEN MONARCH: a great moth with stained-pollen wings
MOTH_LEG = {"k": ("chitin", 0), "c": ("chitin", 2), "C": ("chitin", 3), "y": ("pollen", 2), "Y": ("pollen", 3), "X": ("pollen", 4),
            "e": ("glowg", 3), "E": ("glowg", 4), "m": ("chitin", 0)}
MOTH_HEAD = {
    # pivot (0, 3): the neck. Feathered antennae, big round eyes, the curled tongue below
    "calm": """
Y...Y.
.y.y..
.cCCc.
cEcCEc
cCCCCk
.kcck.
..Yk..
..yY..
""",
    "dead": """
......
Y...Y.
.cCCc.
cmcCmc
cCCCCk
.kcck.
""",
}


def moth_wing(r, root, ang, span, h, z, upper=True, flap=0.0):
    """One wing: a gold panel with black veins and eye-spots, flapping by squashing its height."""
    x, y = root
    a = math.radians(ang)
    hh = h * max(0.25, math.cos(math.radians(flap)))
    c, s = math.cos(a), math.sin(a)
    tip = (x + c * span, y + s * span - (hh * 0.6 if upper else -hh * 0.3))
    p1 = (x + c * span * 0.4, y - hh if upper else y + hh * 0.8)
    p2 = (x + c * span * 0.9, y - hh * 0.9 if upper else y + hh * 0.5)
    pts = [(x, y), p1, p2, tip, (x + c * span * 0.6, y + (hh * 0.15 if upper else hh * 0.1))]
    r.poly(pts, "pollen", z, normal=(-0.4, -0.5 if upper else 0.2, 0.8))
    # black veins radiating from the root, a black border
    for f in (0.35, 0.65, 0.95):
        q = (lerp(p1[0], tip[0], f), lerp(p1[1], tip[1], f))
        r.line(x, y, *q, "chitin", z + 0.01, tone=1)
    r.polyline([p1, p2, tip], "chitin", z + 0.02, tone=0)
    ex, ey = lerp(x, p2[0], 0.6), lerp(y, p2[1], 0.55)
    r.ell(ex, ey, 1.4, 1.4 * max(0.3, math.cos(math.radians(flap))), "bruise", z + 0.03, bias=0.3)
    r.dot(ex, ey, "chitin", 0, z + 0.04)


def monarch(alt=10.0, flap=0.0, lean=0.0, legs_k=0.0, face="calm", clap=0.0, smear=None, spark=None, extra=None, storm=None, tongue=0.0):
    r = Rig()
    oy = -alt
    T = Xf(lean, (0.0, oy - 10.0))
    bx, by = T(0.0, oy - 10.0)
    # wings: far pair behind, near pair in front; clap folds them up and forward
    fl = flap + clap * 70
    moth_wing(r, (bx - 1.0, by - 1.0), 180 + 15 - clap * 40, 15.0, 12.0, -2.0, True, fl)
    moth_wing(r, (bx - 1.0, by + 1.0), 180 - 25 + clap * 20, 11.0, 8.0, -1.9, False, fl)
    moth_wing(r, (bx + 1.0, by - 1.0), -15 + clap * 40, 15.0, 12.0, 2.0, True, fl)
    moth_wing(r, (bx + 1.0, by + 1.0), 25 - clap * 20, 11.0, 8.0, 2.1, False, fl)
    # furred body: thorax and a long ringed abdomen
    r.ell(bx, by, 2.6, 3.0, "pollen", 0.5, bias=0.2)
    ab = chain(bx, by + 2.0, [(3.0, 95), (3.0, 100), (2.6, 105)])
    r.tube(ab, [2.2, 2.0, 1.6, 0.9], "chitin", 0.4, bias=0.1)
    for p in ab[1:3]: r.line(p[0] - 1.8, p[1], p[0] + 1.8, p[1], "pollen", 0.45, tone=2)
    for k in range(3):
        sx, sy = bx + 0.6 + k * 0.6, by + 2.4
        a = 80 + k * 12 + 12 * math.sin(legs_k + k)
        r.polyline(chain(sx, sy, [(2.4, a), (2.0, a + 20)]), "chitin", 0.6, tone=1 + k % 2)
    hx, hy = bx + 2.6, by - 2.5
    r.stamp(MOTH_HEAD[face], hx, hy, 1.0, MOTH_LEG, pivot=(0, 3))
    if tongue:
        r.polyline([(hx + 2, hy + 4), (hx + 2 + 3 * tongue, hy + 5), (hx + 2 + 5 * tongue, hy + 4)], "pollen", 1.1, tone=3)
    if storm is not None:
        k = storm
        for i in range(6):
            d = 6.0 + i * 3.5
            for side in (-1, 1):
                puff(r, hx + d, hy + side * d * 0.35 + 3.0, 2.0 + i * 0.4, 6.0 + i * 0.01, "pollc", min(3, max(0, k + (i > 4))), seed=i + side, n=4)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def monarch_sheet(outdir):
    M = monarch
    idle = [M(alt=10.0 + [0, 0.6, 1.2, 0.6][i], flap=[0, 35, 60, 35][i], legs_k=i) for i in range(4)]
    run = [M(alt=10.0 + 0.8 * math.sin(i / 6 * math.tau), flap=[0, 35, 60, 35, 0, 20][i], lean=8, legs_k=i) for i in range(6)]
    # Clap (6): wings spread wide (0-1), CLAP shut (2: three darts leave the thorax at (12, -24)), open (3-5)
    cl = [M(flap=-20), M(flap=-30, alt=11.0), M(clap=1.0, alt=9.5, extra=lambda r: motes(r, 12.0, -24.0, 0, n=6, mat="pollc", spread=4.0)),
          M(clap=0.6, flap=10), M(flap=30), M()]
    # Storm (8): beats its wings high (0-2), SHAKES a storm of pollen ahead (3-6: the cloud from (8, -22) forward; 4 seeds fall),
    # settle (7)
    st = [M(flap=-30, alt=12.0), M(flap=60, alt=12.5), M(flap=-40, alt=13.0, tongue=1.0),
          M(flap=50, alt=12.0, tongue=1.0, storm=0), M(flap=-30, alt=12.0, storm=1), M(flap=50, alt=11.5, storm=1), M(flap=0, storm=2), M()]
    d0 = M(flap=70, lean=-20)
    d1 = M(flap=85, lean=-40, alt=4.0)
    d2 = _moth_corpse(0)
    corpse = _moth_corpse(1)
    knock = M(flap=60, lean=-24)
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.08] * 6),
             ("Clap", cl, [0.12, 0.12, 0.06, 0.1, 0.1, 0.12]),
             ("Storm", st, [0.12, 0.1, 0.12, 0.1, 0.12, 0.12, 0.14, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("SylPollenMonarch", anims, outdir, scale=3)


def _moth_corpse(stage):
    r = Rig()
    moth_wing(r, (-1.0, -2.0), 175, 15.0, 4.0, -0.5, True, 60)
    moth_wing(r, (1.0, -2.0), 5, 15.0, 4.0, 0.5, True, 60 + stage * 10)
    r.ell(0.0, -2.0, 2.6, 2.0, "pollen", 0.6)
    r.tube([(0.0, -1.0), (-2.0, -0.8), (-5.0, -0.6)], [1.8, 1.6, 1.0], "chitin", 0.55)
    r.stamp(MOTH_HEAD["dead"], 3.0, -1.0, 0.8, MOTH_LEG, pivot=(0, 3))
    return r.resolve()


# ================================================================== THE SOWER: a long black hornet with a ribbed seed-drill belly
SOWER_LEG = {"k": ("chitin", 0), "c": ("chitin", 2), "C": ("chitin", 3), "e": ("glowg", 3), "E": ("glowg", 4), "m": ("chitin", 0),
             "t": ("gall", 3), "T": ("gall", 4)}
SOWER_HEAD = {
    # pivot (0, 3): the neck. A wedge hornet head, mould-green eyes, a seed in its mandibles
    "calm": """
.cCC...
cCEECc.
cCEECCc
ckcCCck
.kkckTt
..k.kt.
""",
    "dead": """
.......
.cCC...
cCmmCc.
cCCCCCk
.kkckk.
""",
}


def sower(alt=10.0, flap=0.0, lean=0.0, drill=0.0, legs_k=0.0, face="calm", aim=0.0, smear=None, spark=None, extra=None, needle=None,
          stretch=1.0):
    r = Rig()
    oy = -alt
    T = Xf(lean, (0.0, oy - 6.0))
    tx, ty = T(4.0, oy - 6.0)
    # the drill-abdomen: a long level cone of mould-green ribs on black, turning (drill shifts the ribs), seed tan tip
    ln = 20.0 * stretch
    a = math.radians(180 + aim)
    c, s = math.cos(a), math.sin(a)
    base = (tx - 2.0, ty + 0.5)
    tip = (base[0] + c * ln, base[1] + s * ln)
    r.tube([base, (lerp(base[0], tip[0], 0.3), lerp(base[1], tip[1], 0.3)), tip], [4.2, 3.8, 1.0], "chitin", 0.0, bias=0.05)
    nrib = 7
    for k in range(nrib):
        f = ((k + drill) % nrib) / nrib * 0.92 + 0.04
        px, py = lerp(base[0], tip[0], f), lerp(base[1], tip[1], f)
        rr = lerp(4.0, 1.2, f)
        r.line(px - s * rr + c * 0.6, py + c * rr + s * 0.6, px + s * rr - c * 0.6, py - c * rr - s * 0.6, "irid" if k % 2 else "gall",
               0.05, tone=3)
    r.dot(*tip, "gall", 4, 0.1)
    # thorax, wings, legs
    r.ell(tx, ty, 3.6, 3.2, "chitin", 0.4, bias=0.15)
    r.dot(tx - 0.5, ty - 2.0, "irid", 4, 0.45)
    for k, (a0, z) in enumerate(((-150 + flap, -1.0), (-120 + flap * 0.8, 1.4))):
        wing(r, (tx - 0.6, ty - 2.4), a0, 14.0 - k * 1.5, 3.6, z, veins=2, tone=2 if k == 0 else 3)
    for k in range(3):
        sx, sy = tx - 1.0 + k * 1.2, ty + 2.0
        aa = 95 + k * 12 + 12 * math.sin(legs_k + k)
        r.polyline(chain(sx, sy, [(2.6, aa), (2.2, aa + 25)]), "chitin", -0.4 if k % 2 else 0.8, tone=1 if k % 2 else 2)
    hx, hy = tx + 3.6, ty - 0.5
    r.stamp(SOWER_HEAD[face], hx, hy, 1.0, SOWER_LEG, pivot=(0, 3))
    if needle:
        r.line(*needle[0], *needle[1], "thorn", 5.0, tone=4)
        r.dot(*needle[1], "gall", 4, 5.1)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def sower_sheet(outdir):
    S = sower
    idle = [S(alt=8.0 + [0, 0.5, 1.0, 0.5][i], flap=[0, 45, 15, 45][i], drill=i * 0.5, legs_k=i) for i in range(4)]
    run = [S(alt=8.0 + 0.5 * math.sin(i / 6 * math.tau), flap=[0, 45, 15, 45, 0, 45][i], lean=6, drill=i, legs_k=i) for i in range(6)]
    # Shot (6): the drill turns fast and dips (0-1), FIRES a seed forward from its jaws (2: at (14, -14)), recoil, recover
    sh = [S(drill=1.0, aim=8, flap=30), S(drill=2.5, aim=12, flap=0, lean=-4),
          S(drill=4.0, aim=-4, flap=45, needle=((14.0, -14.0), (18.0, -14.0)), smear=[("line", [(11, -14), (14, -14)], "gall", 2)]),
          S(drill=5.0, aim=-2, flap=10, lean=-4), S(drill=5.5, flap=40), S(drill=6.0)]
    # Strafe (8): banks (0), FLIES ACROSS the hero's front (1-6: a needle on each frame from (12, -10) at the hero; the drill
    # spins), levels out (7)
    sf = [S(lean=-8, flap=40, drill=0.0)]
    for k in range(6):
        sf.append(S(lean=-4 + 2 * (k % 2), flap=[45, 0][k % 2], drill=k * 1.5, aim=6, legs_k=k,
                    needle=((12.0, -10.0), (16.0, -7.0)) if k % 2 == 0 else None,
                    smear=[("line", [(-14, -13 + (k % 2)), (-8, -13 + (k % 2))], "irid", 2)]))
    sf.append(S(lean=0, flap=20, drill=9.0))
    d0 = S(face="dead", lean=-20, flap=70)
    d1 = S(face="dead", lean=-50, alt=3.0, flap=95, aim=-20)
    d2 = _sower_corpse(0)
    corpse = _sower_corpse(1)
    knock = S(lean=-24, flap=60, aim=-10)
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6),
             ("Shot", sh, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1]),
             ("Strafe", sf, [0.1] + [0.2] * 6 + [0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("SylSower", anims, outdir, scale=4)


def _sower_corpse(stage):
    r = Rig()
    r.tube([(-18.0, -1.0), (-6.0, -2.4), (0.0, -2.6)], [0.8, 2.8, 3.0], "chitin", 0.0)
    for k in range(6):
        x = -16.0 + k * 2.6
        r.line(x, -3.0 - k * 0.3, x + 0.5, -0.2, "irid" if k % 2 else "gall", 0.05, tone=2)
    r.ell(3.0, -2.6, 2.8, 2.4, "chitin", 0.3)
    r.stamp(SOWER_HEAD["dead"], 6.0, -1.0, 0.5, SOWER_LEG, pivot=(0, 3))
    wing(r, (2.0, -4.0), -170 + stage * 10, 11.0, 2.4, -0.4, veins=2, tone=2)
    for x in (-10.0, -4.0, 9.0): r.ell(x, -0.6, 0.8, 0.8, "gall", 0.6, bias=0.3)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.6)
    return r.resolve()


# ================================================================== BLIGHT BELLOWS: a giant fly whose belly is a leather bellows
BELL_LEG = {"e": ("rot", 2), "E": ("rot", 3), "W": ("mould", 4), "m": ("chitin", 0), "k": ("chitin", 1), "c": ("chitin", 2),
            "g": ("gas", 3), "G": ("gas", 4)}
BELL_HEAD = {
    "calm": """
.EEe...
EWEeee.
eEEeeek
.kccckk
..kgk..
""",
    "pump": """
.EEe...
EWEeee.
eEEeeek
.kcmmkk
..kgGk.
...gG..
""",
    "dead": """
.eee...
emeeek.
eeemeek
.kccckk
""",
}


def bellows(alt=8.0, flap=0.0, lean=0.0, pump=0.0, face="calm", legs_k=0.0, vent=None, smear=None, extra=None, lob=None):
    """pump 0 = full, 1 = squeezed flat (it wheezes the gas out)."""
    r = Rig()
    oy = -alt
    T = Xf(lean, (0.0, oy - 8.0))
    for k in range(3):
        sx, sy = T(2.0 + k * 1.6, oy - 4.0)
        a = 95 + k * 10 + 10 * math.sin(legs_k + k)
        r.tube(chain(sx, sy, [(2.6, a), (2.2, a + 25)]), [0.7, 0.5], "chitin", -0.4 if k % 2 else 0.8, flat=1 if k % 2 else 2)
    # the bellows belly: two leather boards hinged at the front, pleated sides that fold as it pumps
    bx, by = T(-3.0, oy - 8.0)
    h = lerp(8.4, 4.0, pump)
    w = 10.5
    # accordion pleats: alternating lit and shadowed folds of leather, each fold a ridge that juts top and bottom
    n = 7
    for k in range(n):
        f = k / (n - 1)
        x = bx - w + 1.0 + f * (w * 1.65)
        hh = lerp(h, h * 0.62, f)
        ridge = k % 2 == 0
        r.poly([T(x - 1.6, by - hh + (0 if ridge else 1.2)), T(x + 1.6, by - hh + (0 if ridge else 1.2)),
                T(x + 1.6, by + hh - (0 if ridge else 1.2)), T(x - 1.6, by + hh - (0 if ridge else 1.2))], "lthr", 0.01 + k * 0.001,
               normal=(-0.6 if ridge else 0.5, -0.3, 0.75), bias=0.15 if ridge else -0.25)
        if ridge:
            r.line(*T(x - 1.2, by - hh), *T(x - 1.2, by + hh), "lthr", 0.02 + k * 0.001, tone=4)
    r.poly([T(bx - w - 0.5, by - h - 1.4), T(bx + w * 0.75, by - h * 0.6 - 1.4), T(bx + w * 0.75, by - h * 0.6), T(bx - w - 0.5, by - h)], "bark", 0.1)
    r.poly([T(bx - w - 0.5, by + h), T(bx + w * 0.75, by + h * 0.6), T(bx + w * 0.75, by + h * 0.6 + 1.4), T(bx - w - 0.5, by + h + 1.4)], "bark", 0.1)
    for k in range(3):
        r.dot(*T(bx - w + 2 + k * 5, by - h - 0.5), "gold", 3, 0.15)
    # the nozzle at the tail end venting fog
    nx, ny = T(bx - w - 2.0, by)
    r.tube([T(bx - w, by), (nx, ny)], [1.6, 1.0], "gold", 0.2)
    if vent is not None:
        # thick blight fog rolling out of the nozzle and curling up round the body
        puff(r, nx - 4.0, ny + 1.0, 3.6, 3.0, "gas", vent, 7, 5)
        puff(r, nx - 1.0, ny - 5.0 - vent, 2.6, -2.5, "gas", min(3, vent + 1), 9, 4)
        puff(r, bx - 2.0, by + h + 2.0, 2.4, -2.4, "gas", min(3, vent + 1), 11, 4)
    tx, ty = T(7.0, oy - 10.0)
    r.ell(tx, ty, 3.8, 3.4, "chitin", 0.5, bias=0.1)
    for k, (a0, z) in enumerate(((-125 + flap, -1.0), (-100 + flap * 0.8, 1.4))):
        wing(r, (tx - 0.6, ty - 2.4), a0, 12.0 - k, 3.6, z, veins=2, tone=2 if k == 0 else 3)
    hx, hy = T(10.0, oy - 10.0)
    r.stamp(BELL_HEAD[face], hx, hy, 1.5, BELL_LEG, pivot=(1, 3))
    if lob:
        x, y, s = lob
        r.ell(x, y, s, s * 0.9, "bile", 4.0, bias=0.2); r.dot(x - 0.5, y - s * 0.6, "lthr", 2, 4.1)
    smears(r, smear)
    if extra: extra(r)
    return r.resolve()


def bellows_sheet(outdir):
    B = bellows
    idle = [B(alt=8.0 + [0, 0.5, 1.0, 0.5][i], flap=[0, 45, 10, 45][i], pump=[0, 0.15, 0.3, 0.15][i], legs_k=i,
              vent=[1, 2, 1, 3][i]) for i in range(4)]
    run = [B(alt=8.0 + 0.6 * math.sin(i / 6 * math.tau), flap=[0, 45, 10, 45, 0, 45][i], lean=6, pump=0.1, legs_k=i * 0.7) for i in range(6)]
    # Lob (6): inflates a bladder in its mouth (0-1), LOBS it (2: it leaves the mouth at (14, -18)), recoil, recover
    lb = [B(face="pump", pump=0.2, lob=(14.0, -17.0, 1.4)), B(face="pump", pump=0.4, lean=-8, lob=(13.5, -18.5, 2.0)),
          B(face="pump", pump=0.6, lean=10, lob=(17.0, -18.0, 2.0), smear=[("line", [(12, -18), (15, -18)], "bile", 2)]),
          B(pump=0.3, lean=6), B(pump=0.1), B()]
    # Pump (9): three pumps; each squeezes the bellows flat (0, 3, 6: a gas lane leaves from (10, -10) forward), refills
    pm = []
    for k in range(3):
        pm += [B(face="pump", pump=1.0, flap=45, vent=0, extra=lambda r: puff(r, 16.0, -9.0, 3.0, 6.0, "gas", 0, 9, 5)),
               B(face="pump", pump=0.6, flap=10, vent=1), B(face="calm", pump=0.0, flap=40, vent=2)]
    d0 = B(face="pump", lean=-20, flap=60, pump=0.5)
    d1 = B(face="dead", lean=-40, alt=3.0, flap=90, pump=1.0, vent=0)
    d2 = _bellows_corpse(0)
    corpse = _bellows_corpse(1)
    knock = B(face="pump", lean=-24, flap=50, pump=0.4)
    anims = [("Idle", idle, [0.08] * 4), ("Run", run, [0.06] * 6),
             ("Lob", lb, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Pump", pm, [0.08, 0.12, 0.25] * 3)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("SylBlightBellows", anims, outdir, scale=3)


def _bellows_corpse(stage):
    r = Rig()
    r.poly([(-12.0, -6.0), (4.0, -4.0), (4.0, 0.0), (-12.0, 0.0)], "lthr", 0.0, curve=0.3)
    for k in range(4): r.line(-10.0 + k * 3.5, -5.0, -10.0 + k * 3.5, -0.5, "lthr", 0.05, tone=1)
    r.ell(7.0, -2.6, 3.0, 2.6, "chitin", 0.3)
    r.stamp(BELL_HEAD["dead"], 10.0, -1.0, 0.5, BELL_LEG, pivot=(1, 3))
    wing(r, (6.0, -4.0), -160, 9.0, 2.6, -0.5, veins=2, tone=2)
    puff(r, -14.0, -3.0, 2.6, 3.0, "gas", 1 + stage, 4, 4)
    return r.resolve()


# ================================================================== CARRION QUEEN: an upright fly queen, a veil of lesser flies
QUEEN_LEG = {"i": ("irid", 1), "I": ("irid", 2), "J": ("irid", 3), "K": ("irid", 4), "m": ("chitin", 0), "c": ("chitin", 2),
             "C": ("chitin", 3), "e": ("eye", 3), "E": ("eye", 4), "g": ("gold", 3), "G": ("gold", 4)}
QUEEN_HEAD = {
    # pivot (2, 6): the neck. Two huge compound eyes in iridescent green, a gold crown-ridge, the proboscis root
    "calm": """
.g.G.g.
.gGgGg.
IJKcKJI
JKJcJKJ
iJIcIJi
.icCci.
..cmc..
""",
    "dead": """
.......
.g.G.g.
IJIcIJI
JmJcJmJ
iJIcIJi
.icCci.
..cmc..
""",
}


def queen(alt=6.0, flap=0.0, lean=0.0, blur=False, prob=None, face="calm", train=0.0, flies=0, smear=None, spark=None, extra=None,
          hand=(6.0, -18.0)):
    r = Rig()
    oy = -alt
    T = Xf(lean, (0.0, oy - 14.0))
    # the bloated egg-sac train trailing behind and down
    for k in range(4):
        x, y = T(-5.0 - k * 3.0 + train * (k % 2), oy - 6.0 + k * 1.6)
        r.ell(x, y, 3.2 - k * 0.4, 2.8 - k * 0.3, "mould" if k % 2 else "podf", -1.0 - k * 0.1, bias=0.1)
        r.dot(x - 0.5, y - 1.0, "mould", 4, -0.95 - k * 0.1)
    # upright abdomen and thorax (iridescent green)
    ax, ay = T(-1.0, oy - 8.0)
    r.ell(ax, ay, 4.4, 6.0, "irid", 0.0, bias=0.05)
    for y in (-3.0, 0.0, 3.0):
        r.line(ax - 3.8, ay + y, ax + 3.8, ay + y + 0.6, "chitin", 0.05, tone=1)
    tx, ty = T(0.5, oy - 16.0)
    r.ell(tx, ty, 3.6, 3.4, "irid", 0.2, bias=0.15)
    # wings: blurred grey fans when the drone builds
    for k, (a0, z) in enumerate(((-150 + flap, -2.0), (-115 + flap * 0.8, -1.5))):
        if blur:
            for j in range(3):
                wing(r, (tx - 1.0, ty - 1.5), a0 - 25 + j * 25, 13.0 - k, 3.0, z + j * 0.01, veins=0, tone=1 + (j % 2))
        else:
            wing(r, (tx - 1.0, ty - 1.5), a0, 13.0 - k, 3.4, z, veins=3, tone=2 if k == 0 else 3)
    # four thin arms folded like a mantis, one reaching
    arm(r, (tx + 1.0, ty + 1.5), hand, 3.6, 3.4, "chitin", 1.0, rad=(0.6, 0.5, 0.4), bend=-1)
    arm(r, (tx - 1.0, ty + 2.0), (tx - 2.0, ty + 6.0), 2.6, 2.4, "chitin", -0.5, rad=(0.6, 0.5, 0.4), bend=1)
    for k in range(2):
        r.polyline(chain(ax + 1.0 - k * 2.0, ay + 5.0, [(3.0, 95 + k * 20), (2.6, 120 + k * 10)]), "chitin", 0.6 - k, tone=1 + k)
    hx, hy = T(1.5, oy - 20.0)
    r.stamp(QUEEN_HEAD[face], hx, hy, 0.8, QUEEN_LEG, pivot=(2, 6))
    # the proboscis
    pr = prob or [(hx + 1.0, hy + 1.0), (hx + 4.0, hy + 3.0), (hx + 7.0, hy + 3.0)]
    r.polyline(pr, "chitin", 0.9, tone=2)
    r.dot(*pr[-1], "irid", 4, 0.95)
    # the veil of lesser flies circling her head
    for k in range(flies):
        a = k / max(1, flies) * math.tau + flap * 0.03
        r.dot(hx + 7.0 * math.cos(a), hy - 3.0 + 3.0 * math.sin(a), "chitin", 1, 3.0 if math.sin(a) > 0 else -3.0)
        r.dot(hx + 7.0 * math.cos(a) + 1, hy - 3.0 + 3.0 * math.sin(a), "wingm", 3, 3.0 if math.sin(a) > 0 else -3.0)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def queen_sheet(outdir):
    Q = queen
    idle = [Q(alt=6.0 + [0, 0.6, 1.2, 0.6][i], flap=[0, 40, 15, 40][i], train=[0, 0.5, 1.0, 0.5][i], flies=6, hand=(6.0, -18.0 + [0, -0.6, -1.2, -0.6][i]))
            for i in range(4)]
    run = [Q(alt=6.0 + 0.5 * math.sin(i / 6 * math.tau), flap=[0, 40, 15, 40, 0, 40][i], lean=8, train=-1.0, flies=6, hand=(7.0, -17.0))
           for i in range(6)]
    bidle = [Q(alt=6.0 + [0, 0.6, 1.2, 0.6][i], flap=[0, 10, 20, 10][i], blur=True, flies=8, hand=(6.0, -19.0)) for i in range(4)]
    brun = [Q(alt=6.0, flap=i * 6, lean=8, blur=True, flies=8, hand=(7.0, -18.0)) for i in range(6)]
    # Stab (6): draws the proboscis back (0-1), STABS (2: tip at (22, -26)), holds, withdraw (4-5)
    stb = [Q(prob=[(3.0, -26.0), (5.0, -26.0), (6.0, -28.0)], lean=-8), Q(prob=[(3.0, -26.0), (4.0, -27.0), (4.0, -29.0)], lean=-12),
           Q(prob=[(3.0, -26.0), (12.0, -26.0), (22.0, -26.0)], lean=10, smear=[("line", [(8, -24), (18, -24)], "irid", 2)], spark=[(23.0, -26.0, 2)]),
           Q(prob=[(3.0, -26.0), (12.0, -26.0), (20.0, -26.0)], lean=8), Q(lean=4), Q()]
    # Dive (8): rears up (0-1), DIVES steered (2-5: proboscis first, stretched), pulls up (6-7)
    dv = [Q(lean=-14, alt=8.0, flap=40), Q(lean=-18, alt=9.0, flap=0)]
    for k in range(4):
        dv.append(Q(lean=40, alt=4.0, flap=[45, 0][k % 2], prob=[(10.0, -18.0), (17.0, -15.0), (24.0, -12.0)], train=2.0,
                    smear=[("line", [(-12, -20 + k), (-4, -16 + k)], "irid", 2)]))
    dv += [Q(lean=-10, alt=7.0, flap=40), Q(lean=-2, flap=10)]
    d0 = Q(lean=-20, flap=70)
    d1 = Q(face="dead", lean=-40, alt=2.0, flap=95)
    d2 = _queen_corpse(0)
    corpse = _queen_corpse(1)
    knock = Q(lean=-24, flap=60)
    anims = [("Idle", idle, [0.07] * 4), ("Run", run, [0.06] * 6), ("IdleBlur", bidle, [0.04] * 4), ("RunBlur", brun, [0.04] * 6),
             ("Stab", stb, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Dive", dv, [0.12, 0.12, 0.08, 0.08, 0.08, 0.08, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("SylCarrionQueen", anims, outdir, scale=3)


def _queen_corpse(stage):
    r = Rig()
    for k in range(4):
        r.ell(-8.0 - k * 3.0, -1.6, 2.6 - k * 0.3, 1.6, "mould" if k % 2 else "podf", -0.5)
    r.ell(-2.0, -3.0, 6.0, 3.0, "irid", 0.0)
    r.ell(5.0, -2.6, 3.0, 2.6, "irid", 0.2)
    r.stamp(QUEEN_HEAD["dead"], 10.0, -1.0, 0.5, QUEEN_LEG, pivot=(2, 6))
    wing(r, (3.0, -4.0), -170 + stage * 8, 12.0, 3.0, -0.5, veins=3, tone=2)
    if stage == 0: dust_puff(r, 0.0, 0, 1, 1.8)
    return r.resolve()


JOBS = [("SylCarrionLily", lily_sheet), ("SylBriarWyrm", wyrm_sheet), ("SylPollenMonarch", monarch_sheet), ("SylSower", sower_sheet),
        ("SylBlightBellows", bellows_sheet), ("SylCarrionQueen", queen_sheet)]

SYNC = {
    "SylCarrionLily": {"Lunge": [("BITE at (24, -11)", 2)], "LungeFar": [("BITE at (38, -10)", 2)],
                       "Bloom": [("OPEN WIDE", 3), ("BREATH: a 120 degree cone from the pit at (12, -24)", 4)]},
    "SylBriarWyrm": {"Mace": [("wind-up over the head (the tell)", 0), ("FRONT: mace at (21, -6)", 3), ("BEHIND: mace at (-23, -6)", 6)],
                     "Spiral": [("thorns fly (two arms, turning)", 2)]},
    "SylPollenMonarch": {"Clap": [("CLAP: three darts leave the thorax at (12, -24)", 2)],
                         "Storm": [("STORM: the pollen cloud rolls forward from (8, -22); 4 seeds fall", 3)]},
    "SylSower": {"Shot": [("seed leaves the jaws at (14, -14)", 2)], "Strafe": [("needles at frames 1, 3, 5 from (12, -10)", 1)]},
    "SylBlightBellows": {"Lob": [("bladder leaves the mouth at (14, -18)", 2)], "Pump": [("PUMP 1: lane from (10, -10)", 0), ("PUMP 2", 3), ("PUMP 3", 6)]},
    "SylCarrionQueen": {"Stab": [("STAB: tip at (22, -26)", 2)], "Dive": [("DIVE (steered)", 2)]},
}
NOTES = {
    "SylCarrionLily": "Idle/Run: uprooted, walking on its roots; IdlePlanted: roots dug in (Planted); Plant is the 3-frame dig.",
    "SylCarrionQueen": "IdleBlur/RunBlur: the wings blur for the 0.3 s before each drone ring (the tell).",
    "SylSower": "New T3 (replaces SylAmberHornet). The drill ribs turn half a rib per idle frame, one per run frame.",
}
