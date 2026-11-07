"""Jinx tier 2 (besides the Ringmaster, in jinx_v2_rigs.py): Marionette, Fortune Teller, Snake-Eyes, Card Soldier, Loaded Die.
Built through jinx_v2_rigs.py. T2 idle limit 28 x 26."""
import math
from jinx_v2_rigs import (Rig, Xf, chain, ik, lerp, lerp_pt, die3, box3, card, harl, star, arc_smear, dust_puff, sheet,
                          tail_anims, PIPS)


def smears(r, sm):
    for s in sm or ():
        if s[0] == "arc": arc_smear(r, *s[1:])
        else: r.polyline(s[1], s[2], 4.8, tone=s[3])


def sparks(r, sp):
    for (x, y, k) in sp or (): star(r, x, y, k)


# ================================================================== MARIONETTE: a porcelain jester on violet strings
PUP_LEG = {"a": ("porc", 1), "w": ("porc", 2), "W": ("porc", 3), "X": ("porc", 4), "m": ("blk", 0), "n": ("crim", 1),
           "C": ("crim", 3), "c": ("crim", 2), "k": ("blk", 1), "v": ("glow", 2), "V": ("glow", 3), "t": ("tear", 2)}
PUP_HEAD = {
    # pivot (3, 6): the neck. A cracked porcelain face, painted lips, a two-point cap; "tilt" for the mirror stance
    "calm": """
n.....k
cCc.kkk
.aWWWw.
aWmWmWw
wWWWWWa
.wWnWa.
..aww..
""",
    "tilt": """
.n...k.
.cCckk.
aWWWWw.
aWWmWmw
wWWWWWa
.awnWW.
...awa.
""",
    "shout": """
n.....k
cCc.kkk
.aWWWw.
aWmWmWw
wWWnWWa
.wWmWa.
..aww..
""",
    "broken": """
n......
cCc.kk.
.aWW.w.
aWmW.mw
wWW.WWa
.wWnWa.
..a.w..
""",
}


def puppet(hip=(0.0, -9.5), lean=0.0, hand=(5.0, -10.0), hand2=(-5.0, -10.0), feet=((-2.5, -1.5), (2.5, -1.5)),
           face="calm", glow=False, strings=True, cut=None, smear=None, spark=None, extra=None, knee=1, head_dx=0.0,
           string_top=-25.0, threads=()):
    """A hanging marionette: hip/hands/feet are where its strings hold it. glow: the violet mirror glow."""
    r = Rig()
    T = Xf(lean, hip)
    sh_n, sh_f = T(hip[0] + 2.0, hip[1] - 6.0), T(hip[0] - 1.8, hip[1] - 6.0)
    neck = T(hip[0] + 0.2, hip[1] - 7.2)
    # legs: porcelain ball joints, faded crimson / black hose, toes pointed down (it never stands)
    for k, f in enumerate(feet):
        hp = (hip[0] + (-0.9 if k == 0 else 0.9), hip[1] + 0.4)
        kn = ik(hp[0], hp[1], f[0], f[1], 3.6, 3.4, bend=-knee)
        z = -1.0 if k == 0 else 1.2
        m = "blk" if k == 0 else "crim"
        r.tube([hp, kn], [1.1, 1.0], m, z, bias=-0.3 if k == 0 else 0.0)
        r.tube([kn, f], [0.9, 0.7], m, z - 0.01, bias=-0.3 if k == 0 else 0.0)
        r.ell(kn[0], kn[1], 0.9, 0.9, "porc", z + 0.02, bias=-0.1 if k == 0 else 0.1)
        r.poly([(f[0] - 0.6, f[1] - 0.8), (f[0] + 2.2, f[1] + 0.2), (f[0] + 0.2, f[1] + 0.8)], "porc", z + 0.03)
    # far arm
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 3.2, 3.0, bend=1)
    r.tube([sh_f, e2], [1.0, 0.9], "blk", -0.6, bias=-0.35)
    r.tube([e2, hand2], [0.8, 0.7], "porc", -0.6, bias=-0.3)
    r.ell(e2[0], e2[1], 0.8, 0.8, "porc", -0.55, bias=-0.2)
    # body: a short harlequin doublet, porcelain hips, a ruff
    r.ell(*T(hip[0], hip[1] + 0.2), 2.4, 1.4, "porc", 0.0, bias=0.0)
    tor = [T(hip[0] - 2.6, hip[1] - 0.6), T(hip[0] + 2.6, hip[1] - 0.6), T(hip[0] + 2.8, hip[1] - 6.2), T(hip[0] - 2.4, hip[1] - 6.4)]
    r.poly(tor, harl(hip[0], hip[1], 2.4, "crim", "blk", ang=lean), 0.1, curve=0.8)
    for j in range(2):
        r.dot(*T(hip[0] + 0.4, hip[1] - 2.0 - 2.0 * j), "gold", 3, 0.2)
    for i in range(5):
        a = math.radians(-180 + i * 45)
        r.ell(neck[0] + 2.4 * math.cos(a), neck[1] + 0.4 + 0.8 * math.sin(a), 1.1, 0.9, "ivory", 1.8 + 0.01 * i, bias=0.15)
    hx, hy = neck[0] + head_dx, neck[1] - 0.2
    r.stamp(PUP_HEAD[face], hx, hy, 2.5, PUP_LEG, pivot=(3, 6))
    # near arm
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 3.2, 3.0, bend=1)
    r.tube([sh_n, e1], [1.1, 0.9], "crim", 3.0)
    r.tube([e1, hand], [0.8, 0.7], "porc", 3.0, bias=0.05)
    r.ell(e1[0], e1[1], 0.8, 0.8, "porc", 3.05)
    r.ell(hand[0], hand[1], 0.9, 0.9, "porc", 3.1, bias=0.1)
    # strings: from the hands, the head and the knees, straight up off the top of the cell
    if strings:
        st = "glow"
        tone = 4 if glow else 1
        tips = [hand, hand2, (hx + 0.5, hy - 6.0)]
        for i, (x, y) in enumerate(tips):
            if cut and i in cut: continue
            top = string_top + (1 if i == 2 else 0)
            for (px, py) in [(x, yy) for yy in range(int(top), int(y))]:
                pass
            r.line(x, y, x + (i - 1) * 0.6, top, st, 5.0 if i != 1 else -2.0, tone=tone if i != 1 else tone - 1)
        if glow:
            for (x, y) in tips:
                r.dot(x, y - 1, "glow", 4, 5.1)
    for (a, b) in threads:     # Strings: the threads it casts
        r.line(*a, *b, "glow", 5.2, tone=3)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def mario_sheet(outdir):
    P = puppet
    idle = [P(hip=(0.0, -9.5 - [0, 0.5, 1.0, 0.5][i]), lean=[0, 3, 0, -3][i], hand=(4.5, -9.5 - [0, 1, 2, 1][i]),
              hand2=(-4.5, -9.0 - [1, 0, 1, 2][i]), feet=((-2.0, -1.5 - [0, 0.5, 1.0, 0.5][i]), (2.5, -1.0 - [1, 0.5, 0, 0.5][i])))
            for i in range(4)]
    # Run: jerked along by its strings: a foot flicks up, the other drags, the arms swing loose
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(P(hip=(0.5, -10.0 - abs(math.sin(ph))), lean=10, feet=((-2.0 - 2 * math.cos(ph), -1.0 - max(0, 3 * math.sin(ph))),
                                                                   (2.5 + 2 * math.cos(ph), -1.0 - max(0, -3 * math.sin(ph)))),
                     hand=(4.0 + 2 * math.cos(ph), -10.0), hand2=(-4.0 - 2 * math.cos(ph), -10.5)))
    # Lash: the string yanks the arm up (0-1), whips it down and out (2 smear, 3 HIT reaching (14, -10)), dangles (4-5)
    lash = [P(hand=(3.0, -17.0), hand2=(-4.0, -10.0), lean=-4),
            P(hand=(-1.0, -20.0), hand2=(-5.0, -9.0), lean=-8, face="shout"),
            P(hand=(9.0, -16.0), lean=6, face="shout", smear=[("arc", 2.0, -12.0, 9.0, -120, -20, "white", 2)]),
            P(hand=(13.5, -10.0), lean=10, face="shout", feet=((-3.0, -1.5), (3.5, -2.0)), spark=[(15.5, -10.0, 2)]),
            P(hand=(11.0, -7.0), lean=6),
            P(hand=(5.0, -9.5), lean=2)]
    # Strings: arms flung up (0-2) as its own strings flare, then both arms snap forward (3): three threads fly from (12, -14)
    strings = [P(hand=(3.0, -16.0), hand2=(-3.0, -16.0), glow=True),
               P(hand=(2.0, -20.0), hand2=(-2.0, -20.0), glow=True, face="shout", hip=(0.0, -11.0)),
               P(hand=(0.0, -21.0), hand2=(-3.0, -20.0), glow=True, face="shout", hip=(0.0, -11.5), lean=-6),
               P(hand=(11.0, -14.0), hand2=(9.0, -15.0), glow=True, face="shout", lean=10,
                 threads=[((12, -14), (24, -18)), ((12, -14), (25, -14)), ((12, -14), (24, -10))]),
               P(hand=(10.0, -13.0), hand2=(8.0, -14.0), glow=True, lean=8),
               P(hand=(8.0, -12.0), hand2=(5.0, -12.0), lean=4),
               P(hand=(5.0, -10.0), hand2=(-3.0, -10.0), lean=1),
               P()]
    # Mirror: its strings burn violet and its head tilts like a reflection
    midle = [P(hip=(0.0, -9.5 - [0, 0.5, 1.0, 0.5][i]), face="tilt", glow=True, head_dx=-0.5, hand=(4.0, -11.0), hand2=(-4.0, -11.0 - i % 2),
               lean=[-3, -1, -3, -5][i]) for i in range(4)]
    mrun = []
    for i in range(6):
        ph = i / 6 * math.tau
        mrun.append(P(hip=(0.0, -10.0 - abs(math.sin(ph))), lean=-6, face="tilt", glow=True, head_dx=-0.5,
                      feet=((-2.0 + 2 * math.cos(ph), -1.0 - max(0, 3 * math.sin(ph))), (2.5 - 2 * math.cos(ph), -1.0 - max(0, -3 * math.sin(ph)))),
                      hand=(4.0 - 2 * math.cos(ph), -11.0), hand2=(-4.0 + 2 * math.cos(ph), -11.0)))
    d0 = P(face="shout", lean=-10, hand=(2.0, -16.0), hand2=(-7.0, -13.0), cut=(1,))
    d1 = P(face="broken", lean=-25, hip=(-1.0, -6.0), hand=(4.0, -6.0), hand2=(-6.0, -4.0), feet=((-3.0, 0.0), (3.0, -0.5)), cut=(0, 1, 2))
    d2 = _mario_heap(0)
    corpse = _mario_heap(1)
    knock = P(face="shout", lean=-14, hip=(-1.0, -10.0), hand=(1.0, -15.0), hand2=(-7.0, -12.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Lash", lash, [0.12, 0.12, 0.05, 0.08, 0.12, 0.14]),
             ("Strings", strings, [0.12, 0.12, 0.14, 0.06, 0.1, 0.12, 0.12, 0.14]),
             ("MirrorIdle", midle, [0.12] * 4), ("MirrorRun", mrun, [0.08] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxMarionette", anims, outdir, scale=5)


def _mario_heap(stage):
    r = Rig()
    # a heap of limbs, the doublet, the cracked head on top; the cut strings coiled beside it
    r.poly([(-4.0, -1.0), (3.0, -1.5), (3.5, -4.0), (-3.5, -4.5)], harl(0, 0, 2.4), 1.0)
    r.tube([(-7.0, -0.6), (-3.0, -1.4), (-1.0, -0.6)], [0.8, 0.8, 0.7], "blk", 0.5)
    r.tube([(3.0, -1.0), (6.0, -2.5 if not stage else -1.0), (9.0, -0.6)], [0.9, 0.8, 0.7], "crim", 0.6)
    r.tube([(1.0, -4.0), (4.0, -6.0 if not stage else -3.5), (6.5, -4.0 if not stage else -1.5)], [0.8, 0.7, 0.6], "porc", 1.5)
    r.stamp(PUP_HEAD["broken"], -4.5, -2.0 if not stage else -0.5, 2.0, PUP_LEG, pivot=(3, 6))
    r.polyline([(-10, -0.5), (-12, -1.5), (-11, -2.5), (-13, -3.0)], "glow", 0.2, tone=1)
    r.polyline([(10, -0.5), (12, -2.0), (14, -1.0)], "glow", 0.2, tone=1)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.2)
    return r.resolve()


# ================================================================== FORTUNE TELLER: a veiled seer over a draped table
SEER_LEG = {"k": ("viol", 0), "d": ("viol", 1), "v": ("viol", 2), "V": ("viol", 3), "L": ("viol", 4), "g": ("gold", 2),
            "G": ("gold", 4), "z": ("gold", 1), "e": ("glow", 4), "E": ("glow", 3), "s": ("dskin", 1), "S": ("dskin", 2),
            "w": ("ivory", 3), "m": ("blk", 0)}
SEER_HEAD = {
    # pivot (3, 7): the neck. A violet hood and veil with a gold coin circlet; only the eyes show, glowing
    "veil": """
..dVVd..
.dVLVVd.
dVgGgGgd
dvSeSeSd
dvvvvvvk
.dvVVvk.
..dvvd..
...kk...
""",
    "wide": """
..dVVd..
.dVLVVd.
dVgGgGgd
dvEeSEeS
dvvvvvvk
.dvVVvk.
..dvvd..
...kk...
""",
    "shut": """
..dVVd..
.dVLVVd.
dVgGgGgd
dvSmSmSd
dvvvvvvk
.dvVVvk.
..dvvd..
...kk...
""",
}
BALL = {"cloud": "glass", "Tower": "eye", "Fool": "fire", "Star": "chipb"}


def crystal(r, x, y, rad, mood, z, swirl=0):
    m = BALL[mood]
    r.ell(x, y, rad, rad, m, z, bias=0.1)
    r.dot(x - rad * 0.45, y - rad * 0.45, "white", 4, z + 0.02)
    a = math.radians(swirl)
    r.dot(x + rad * 0.5 * math.cos(a), y + rad * 0.5 * math.sin(a), "white", 3 if m != "glass" else 2, z + 0.01)
    if mood != "cloud":   # the coming card's colour leaks out
        for k in range(4):
            aa = math.radians(swirl + 90 * k + 45)
            r.dot(x + (rad + 1.2) * math.cos(aa), y + (rad + 1.2) * math.sin(aa), m, 3, z + 0.03)


def seer(hover=2.0, lean=0.0, ball=(5.5, -13.0), mood="cloud", face="veil", swirl=0, skirt=0.0, hand2=None, raise_=0.0,
         smear=None, spark=None, extra=None, ball_r=2.6):
    r = Rig()
    by = -hover
    T = Xf(lean, (0.0, by - 6.0))
    # the draped table-skirt: a bell of velvet with a gold coin fringe that sways
    skt = [T(-6.0 - skirt, by), T(-4.6, by - 7.0), T(4.0, by - 7.0), T(6.0 + skirt * 0.4, by), T(3.0, by + 0.6), T(-3.0, by + 0.6)]
    r.poly(skt, "viol", 0.0, curve=0.9)
    for i in range(7):
        x = lerp(-5.6 - skirt, 5.6 + skirt * 0.4, i / 6.0)
        r.dot(x, by + 0.4 - (0.6 if i % 2 else 0.0), "gold", 3 if i < 4 else 2, 0.2)
    r.line(*T(-4.6, by - 6.8), *T(4.0, by - 6.8), "gold", 0.15, tone=2)
    # torso, shawl and arms cupping the ball
    r.ell(*T(0.0, by - 9.5), 3.0, 3.0, "viol", 0.5, bias=0.1)
    r.poly([T(-3.2, by - 11.0), T(3.2, by - 11.0), T(1.5, by - 7.5), T(-2.0, by - 7.5)], "crim", 0.6, bias=0.1)
    for i in range(3):
        r.dot(*T(-1.5 + 1.5 * i, by - 7.6), "gold", 3, 0.65)
    hx, hy = T(0.5, by - 11.6)
    r.stamp(SEER_HEAD[face], hx, hy, 2.0, SEER_LEG, pivot=(3, 7))
    sh_n, sh_f = T(2.4, by - 10.6), T(-2.0, by - 10.6)
    bx, by2 = ball
    h2 = hand2 or (bx - 2.0, by2 + 1.5)
    e2 = ik(sh_f[0], sh_f[1], h2[0], h2[1], 2.6, 2.6, bend=1)
    r.tube([sh_f, e2, h2], [1.1, 0.9, 0.8], "viol", -0.5, bias=-0.3)
    crystal(r, bx, by2, ball_r, mood, 3.0, swirl)
    h1 = (bx + 1.0, by2 + ball_r * 0.8)
    e1 = ik(sh_n[0], sh_n[1], h1[0], h1[1], 2.6, 2.6, bend=1)
    r.tube([sh_n, e1, h1], [1.1, 0.9, 0.8], "viol", 3.5, bias=0.1)
    r.dots([(h1[0], h1[1]), (h2[0], h2[1])], "dskin", 2, 3.6)
    r.dot(*e1, "gold", 3, 3.55)    # bangle
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def seer_sheet(outdir):
    S = seer
    out = []

    def idle_of(mood):
        return [S(hover=2.0 + [0, 0.5, 1.0, 0.5][i], mood=mood, swirl=90 * i, skirt=[0, 0.4, 0.8, 0.4][i],
                  ball=(5.5, -13.0 - [0, 0.5, 1.0, 0.5][i])) for i in range(4)]

    def run_of(mood):
        return [S(hover=2.5 + 0.5 * math.sin(i / 6 * math.tau), lean=10, mood=mood, swirl=60 * i, skirt=1.6 + 0.6 * math.sin(i),
                  ball=(6.5, -12.5)) for i in range(6)]

    def foretell_of(mood):
        # lifts the ball overhead (0-2), the card's colour floods it (3), drives it down at the floor: the mark lands (4),
        # settles (5-7)
        return [S(mood=mood, ball=(3.0, -17.0), face="wide", swirl=0),
                S(mood=mood, ball=(1.0, -22.0), hand2=(-1.0, -20.0), face="wide", swirl=90, hover=3.0, lean=-4),
                S(mood=mood, ball=(1.0, -23.0), hand2=(-1.0, -21.0), face="wide", swirl=180, hover=3.5, lean=-6, ball_r=3.0),
                S(mood=mood, ball=(1.0, -23.0), hand2=(-1.0, -21.0), face="wide", swirl=270, hover=3.5, lean=-6, ball_r=3.4,
                  spark=[(1.0, -27.5, 1)]),
                S(mood=mood, ball=(8.0, -9.0), face="wide", lean=10, hover=1.5, ball_r=3.0,
                  smear=[("arc", 2.0, -12.0, 10.0, -100, 10, "glow", 2)], spark=[(12.0, -6.0, 2)]),
                S(mood=mood, ball=(7.0, -10.0), lean=6, hover=1.8),
                S(mood="cloud", ball=(6.0, -12.0), lean=2),
                S(mood="cloud")]
    idle = idle_of("cloud"); run = run_of("cloud")
    # Gaze: the ball flares (0-2), a bolt flies from it (3) at (9, -13), settle
    gaze = [S(ball=(6.0, -14.0), face="wide", swirl=0), S(ball=(6.5, -15.0), face="wide", swirl=120, ball_r=3.0),
            S(ball=(7.5, -14.5), face="wide", swirl=240, ball_r=3.2, spark=[(7.5, -14.5, 2)], lean=4),
            S(ball=(8.0, -13.5), face="wide", lean=6, spark=[(11.0, -13.5, 1)]),
            S(ball=(6.5, -13.0), lean=3), S()]
    d0 = S(face="shut", lean=-12, ball=(3.0, -16.0), mood="cloud")
    d1 = S(face="shut", lean=-28, hover=0.5, ball=(-2.0, -8.0))
    d2 = _seer_corpse(0)
    corpse = _seer_corpse(1)
    knock = S(face="shut", lean=-16, ball=(3.0, -15.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Gaze", gaze, [0.12, 0.1, 0.1, 0.06, 0.12, 0.14]),
             ("Foretell", foretell_of("cloud"), [0.12, 0.12, 0.12, 0.14, 0.06, 0.12, 0.12, 0.14])]
    for mood in ("Tower", "Fool", "Star"):
        anims += [("Idle" + mood, idle_of(mood), [0.16, 0.14, 0.16, 0.14]), ("Run" + mood, run_of(mood), [0.08] * 6),
                  ("Foretell" + mood, foretell_of(mood), [0.12, 0.12, 0.12, 0.14, 0.06, 0.12, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxFortuneTeller", anims, outdir, scale=5)


def _seer_corpse(stage):
    r = Rig()
    r.poly([(-8.0, 0.0), (-4.0, -3.0), (5.0, -3.5), (8.0, 0.0)], "viol", 0.0, curve=0.6)
    for i in range(6):
        r.dot(-7.0 + 2.8 * i, -0.2, "gold", 3, 0.1)
    r.stamp(SEER_HEAD["shut"], -8.0, -1.0, 1.0, SEER_LEG, pivot=(3, 7))
    crystal(r, 11.0 if stage else 9.0, -2.6, 2.4, "cloud", 1.0)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.4)
    return r.resolve()


# ================================================================== SNAKE-EYES: a coiled viper with dice for eyes
def band_mat(period=3.0, phase=0.0):
    def f(x, y):
        k = int(math.floor((x * 0.8 + y * 0.35 + phase) / period))
        return "scale" if k % 2 else "sblk"
    return f


def eye_dice(r, x, y, z, crossed=False, shut=False):
    """Two ivory one-pip dice for eyes, side by side; crossed: the pips look inward."""
    for k, dx in enumerate((-1.6, 1.6)):
        r.poly([(x + dx - 1.0, y - 1.0), (x + dx + 1.0, y - 1.0), (x + dx + 1.0, y + 1.0), (x + dx - 1.0, y + 1.0)], "ivory", z,
               normal=(-0.3, -0.4, 1.0))
        if shut: r.line(x + dx - 1, y, x + dx + 1, y, "blk", z + 0.01, tone=0)
        else:
            px = (0.5 if k == 0 else -0.5) if crossed else 0.0
            r.dot(x + dx + px, y, "eye", 2, z + 0.01)


def viper(spine, head=None, head_ang=0.0, mouth="shut", eyes="open", rattle=0, phase=0.0, dice=(), smear=None, spark=None,
          extra=None, tongue=False):
    """spine: points from the tail tip to the neck; the head sits at `head` (default: the last point)."""
    r = Rig()
    n = len(spine)
    rad = [max(0.6, 2.4 * min(1.0, (i + 1) / (n * 0.45))) for i in range(n)]
    rad[-1] = 1.8
    r.tube(spine, rad, band_mat(3.0, phase), 0.5, bias=0.05)
    # belly highlight along the lower edge
    for i in range(1, n):
        (x0, y0), (x1, y1) = spine[i - 1], spine[i]
        r.dot((x0 + x1) / 2, (y0 + y1) / 2 + rad[i] * 0.7, "belly", 2, 0.6)
    # dice rattle at the tail tip: three little stacked dice
    tx, ty = spine[0]
    for k in range(3):
        die3(r, tx - 0.5 + (0.5 if (k + rattle) % 2 else -0.5) * (1 if rattle else 0), ty - 1.2 - k * 2.0, 2.2, 0, 30 + 40 * k + 30 * rattle, 0,
             z=0.8 + k * 0.01, pips=False)
    hx, hy = head or spine[-1]
    T = Xf(head_ang, (hx, hy))
    # head: a broad viper wedge in black with crimson lips, dice eyes on top
    pts = [T(hx - 2.0, hy - 2.0), T(hx + 3.0, hy - 2.4), T(hx + 6.0, hy - 0.8), T(hx + 6.0, hy + 0.6), T(hx + 1.0, hy + 2.0), T(hx - 2.0, hy + 1.4)]
    if mouth == "open":
        pts = [T(hx - 2.0, hy - 2.0), T(hx + 3.0, hy - 2.6), T(hx + 6.5, hy - 2.0), T(hx + 3.0, hy - 0.2), T(hx + 6.0, hy + 2.6),
               T(hx + 1.0, hy + 2.4), T(hx - 2.0, hy + 1.4)]
        r.poly([T(hx + 2.0, hy - 0.6), T(hx + 6.0, hy - 1.6), T(hx + 5.6, hy + 2.0)], "crim", 1.9)
        r.dots([T(hx + 5.6, hy - 1.0), T(hx + 5.2, hy + 1.6)], "ivory", 4, 2.2)
    r.poly(pts, "sblk", 2.0, normal=(-0.2, -0.5, 1.0))
    r.line(*T(hx + 1.0, hy + 1.2), *T(hx + 5.5, hy + 0.4), "crim", 2.05, tone=2)
    if tongue:
        r.polyline([T(hx + 6.0, hy + 0.4), T(hx + 8.0, hy + 0.2), T(hx + 9.0, hy - 0.6)], "crim", 2.1, tone=3)
        r.dot(*T(hx + 9.0, hy + 0.6), "crim", 3, 2.1)
    ex, ey = T(hx + 1.6, hy - 2.6)
    eye_dice(r, ex, ey, 2.5, crossed=(eyes == "crossed"), shut=(eyes == "shut"))
    for (x, y, a) in dice:
        die3(r, x, y, 3.2, 0, a, a * 0.7, z=4.0, pip_faces=1, pip_min=1.5)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def s_curve(x0, y0, length, amp, phase, n=14, rise=0.0, coil=0.0):
    """Points along a horizontal S-wave from (x0, y0) going right, amp in y, the last ~third rising by `rise`."""
    pts = []
    for i in range(n):
        t = i / (n - 1.0)
        x = x0 + length * t
        y = y0 + amp * math.sin(t * math.tau * 1.0 + phase) * (1 - t * 0.6) - rise * max(0.0, (t - 0.6) / 0.4) ** 1.4
        pts.append((x - coil * math.sin(t * math.pi) , y))
    return pts


def snake_sheet(outdir):
    V = viper

    def base(phase=0.0, rise=7.0, length=16.0, amp=1.6, x0=-9.0, coil=0.0):
        return s_curve(x0, -2.2, length, amp, phase, rise=rise, coil=coil)
    idle = [V(base(phase=0.4 * i, rise=7.0 + [0, 0.5, 1, 0.5][i]), rattle=i % 2, phase=0.0, head_ang=[0, -4, 0, 4][i]) for i in range(4)]
    run = [V(base(phase=i / 6 * math.tau, rise=5.5, amp=2.2), phase=-1.2 * i, head_ang=4, rattle=i % 2) for i in range(6)]
    # Strike: coil back (0-1), lunge (2 smear), HIT jaws at (17, -7) (3), worry (4), recoil (5-6)
    strike = [V(base(rise=8.0, length=13.0, coil=1.0), mouth="open", head_ang=-12, tongue=True),
              V(base(rise=9.0, length=11.0, x0=-10.0, coil=2.0), mouth="open", head_ang=-20),
              V(base(rise=5.0, length=21.0, amp=0.8), mouth="open", head_ang=8, smear=[("line", [(-2, -10), (4, -9), (9, -8)], "white", 2)]),
              V(base(rise=4.0, length=24.0, amp=0.6), mouth="shut", head_ang=10, spark=[(19.0, -7.0, 1)]),
              V(base(rise=4.5, length=22.0, amp=0.8), mouth="open", head_ang=4, tongue=True),
              V(base(rise=6.5, length=18.0), mouth="shut", head_ang=-2),
              V(base(), head_ang=0)]
    # Craps: whips its tail round to its jaws (0-1), shakes the dice out of the rattle (2), FLICKS two dice (3), watches (4-7)
    craps = [V(base(rise=6.0, coil=1.0), rattle=1, head_ang=20, eyes="open"),
             V(base(rise=6.0, coil=2.0), rattle=0, head_ang=24, mouth="open"),
             V(base(rise=7.5), rattle=1, head_ang=10, mouth="open", dice=[(4.0, -10.0, 20), (6.0, -12.0, 70)]),
             V(base(rise=6.5, length=18.0), head_ang=6, mouth="open", dice=[(13.0, -3.0, 120), (12.0, -6.0, 200)],
               smear=[("line", [(5, -10), (9, -7), (12, -4)], "white", 2)]),
             V(base(rise=7.0), head_ang=0, tongue=True),
             V(base(rise=7.5), head_ang=-4, rattle=1),
             V(base(rise=7.0), head_ang=0),
             V(base(), head_ang=0)]
    # Dazed: crapped out: eyes crossed, the head lolls
    dazed = [V(base(rise=4.0 + [0, 1, 0, -1][i], phase=0.2 * i), eyes="crossed", head_ang=[18, 8, -6, 8][i], tongue=i % 2 == 0)
             for i in range(4)]
    d0 = V(base(rise=9.0, coil=1.0), mouth="open", head_ang=-30, eyes="shut")
    d1 = V(base(rise=3.0, amp=2.5), head_ang=40, eyes="shut")
    d2 = V(s_curve(-11.0, -1.4, 22.0, 1.4, 0.4, rise=0.0), head_ang=10, eyes="shut", extra=lambda r: dust_puff(r, 4.0, 0.0, 1, 1.0))
    corpse = V(s_curve(-11.0, -1.2, 22.0, 1.0, 0.8, rise=0.0), head=(12.5, -1.6), head_ang=90, eyes="shut")
    knock = V(base(rise=8.0, coil=1.5), mouth="open", head_ang=-24, eyes="open")
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.07] * 6),
             ("Strike", strike, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Craps", craps, [0.12, 0.12, 0.12, 0.06, 0.12, 0.12, 0.12, 0.14]),
             ("Dazed", dazed, [0.14, 0.12, 0.14, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxSnakeEyes", anims, outdir, scale=5)


# ================================================================== CARD SOLDIER: a spade card on stick legs, with a pike
SOLD_LEG = {"a": ("ivory", 1), "w": ("ivory", 2), "W": ("ivory", 3), "m": ("blk", 0), "n": ("crim", 1), "C": ("crim", 3),
            "c": ("crim", 2), "g": ("gold", 3), "k": ("blk", 1)}
SOLD_HEAD = {
    "front": """
.nCCn.
nCgCCn
.aWWa.
aWmWmw
.wWWa.
..aa..
""",
    "side": """
.nCCn.
.nCCgC
..aWW.
..WWmw
..wWWW
...aa.
""",
    "shout": """
.nCCn.
nCgCCn
.aWWa.
aWmWmw
.wmma.
..aa..
""",
    "dead": """
......
.nCCn.
nCgCCn
amWmWw
.wmma.
..aa..
""",
}


def spade(r, cx, cy, s, mat, z, tone=None):
    """A spade pip of height ~2.2*s centred (cx, cy)."""
    r.ell(cx - 0.55 * s, cy + 0.1 * s, 0.6 * s, 0.55 * s, mat, z, flat=tone)
    r.ell(cx + 0.55 * s, cy + 0.1 * s, 0.6 * s, 0.55 * s, mat, z, flat=tone)
    r.poly([(cx - 1.1 * s, cy), (cx, cy - 1.2 * s), (cx + 1.1 * s, cy)], mat, z, flat=tone)
    r.poly([(cx - 0.3 * s, cy + 0.5 * s), (cx + 0.3 * s, cy + 0.5 * s), (cx + 0.6 * s, cy + 1.1 * s), (cx - 0.6 * s, cy + 1.1 * s)], mat, z,
           flat=tone)


def pike(r, hx, hy, ang, z, ln=16.0):
    a = math.radians(ang)
    tx, ty = hx + ln * math.cos(a), hy + ln * math.sin(a)
    bx, by = hx - 4.0 * math.cos(a), hy - 4.0 * math.sin(a)
    r.tube([(bx, by), (tx, ty)], [0.6, 0.6], "wood", z)
    # the spade blade, pointing along the shaft
    T = Xf(ang + 90, (tx, ty))
    pts = [T(tx - 2.2, ty + 0.5), T(tx, ty - 3.4), T(tx + 2.2, ty + 0.5), T(tx + 1.0, ty + 1.6), T(tx - 1.0, ty + 1.6)]
    r.poly(pts, "steel", z + 0.01, normal=(-0.3, -0.5, 1.0))
    r.dot(tx + 2.0 * math.cos(a), ty + 2.0 * math.sin(a), "white", 4, z + 0.02)
    return tx, ty


def soldier(lean=0.0, bob=0.0, feet=((-2.5, 0.0), (2.5, 0.0)), hand=(5.0, -9.0), hand2=(-5.0, -9.0), pike_ang=-80.0,
            face="front", edge=False, turn=0.0, cards=(), smear=None, spark=None, extra=None, knee=1, pike_ln=14.5):
    """edge=True: turned edge-on (Paper Thin): the card is a 2 px line and the head is in profile."""
    r = Rig()
    hip = (0.0, -4.5 + bob)
    T = Xf(lean, hip)
    for k, f in enumerate(feet):
        hp = T(hip[0] + (-1.6 if k == 0 else 1.6) * (0.3 if edge else 1.0), hip[1])
        kn = ik(hp[0], hp[1], f[0], f[1] - 0.8, 2.4, 2.2, bend=-knee)
        z = -1.0 if k == 0 else 1.0
        r.line(*hp, *kn, "blk", z, tone=1 if k == 0 else 2)
        r.line(*kn, f[0], f[1] - 0.8, "blk", z, tone=1 if k == 0 else 2)
        r.poly([(f[0] - 0.8, f[1] - 1.2), (f[0] + 1.6, f[1] - 0.8), (f[0] + 1.6, f[1]), (f[0] - 0.8, f[1])], "blk", z + 0.01,
               bias=0.15 if k else -0.2)
    sh_n, sh_f = T(hip[0] + (1.0 if edge else 4.2), hip[1] - 9.0), T(hip[0] - (1.0 if edge else 4.2), hip[1] - 9.0)
    # far arm
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 2.6, 2.6, bend=1)
    r.polyline([sh_f, e2, hand2], "blk", -0.5, tone=1)
    # the card body
    w = 2.0 if edge else 9.0 * max(0.25, math.cos(math.radians(turn)))
    cx, cy = T(hip[0], hip[1] - 6.0)
    if edge:
        r.poly([T(hip[0] - 1.0, hip[1] + 0.2), T(hip[0] + 1.0, hip[1] + 0.2), T(hip[0] + 1.0, hip[1] - 12.2), T(hip[0] - 1.0, hip[1] - 12.2)],
               "card", 0.0, normal=(-0.6, -0.2, 0.8))
        r.line(*T(hip[0] + 1.0, hip[1]), *T(hip[0] + 1.0, hip[1] - 12.0), "crim", 0.05, tone=2)
    else:
        card(r, cx, cy, w, 12.4, z=0.0, ang=lean, lit=0.1)
        Tc = Xf(lean, (cx, cy))
        # crimson border inset, a big spade, corner indices
        pts = [Tc(cx - w / 2 + 0.8, cy - 5.4), Tc(cx + w / 2 - 0.8, cy - 5.4), Tc(cx + w / 2 - 0.8, cy + 5.4), Tc(cx - w / 2 + 0.8, cy + 5.4)]
        r.polyline(pts + [pts[0]], "crim", 0.05, tone=2)
        if w > 5:
            spade(r, *Tc(cx, cy - 0.6), 1.8 * w / 9.0, "blk", 0.1)
            r.dot(*Tc(cx - w / 2 + 1.6, cy - 4.4), "blk", 1, 0.1)
            r.dot(*Tc(cx + w / 2 - 1.6, cy + 4.4), "blk", 1, 0.1)
    hx, hy = T(hip[0] + (0.5 if edge else 0.0), hip[1] - 12.2)
    r.stamp(SOLD_HEAD["side" if edge else face], hx, hy, 2.0, SOLD_LEG, pivot=(3, 5))
    # near arm and pike
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 2.6, 2.6, bend=1)
    r.polyline([sh_n, e1, hand], "blk", 3.0, tone=2)
    pike(r, hand[0], hand[1], pike_ang, 3.2, ln=pike_ln)
    r.dot(*hand, "ivory", 3, 3.3)
    for (x, y, a) in cards:
        card(r, x, y, 3.0, 4.0, back="crim", z=4.0, ang=a, lit=0.1)
    smears(r, smear); sparks(r, spark)
    if extra: extra(r)
    return r.resolve()


def soldier_sheet(outdir):
    S = soldier
    idle = [S(bob=[0, -0.3, -0.5, -0.3][i], hand=(5.0, -9.0 - [0, 0.3, 0.5, 0.3][i])) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        run.append(S(lean=4, bob=-0.6 * abs(math.sin(ph)), feet=((-2.5 * math.cos(ph), -max(0, 2 * math.sin(ph))),
                                                                 (2.5 * math.cos(ph), -max(0, -2 * math.sin(ph)))),
                     hand=(5.0, -9.5), pike_ang=-75))
    # Thrust: draw the pike back (0-1), lunge (2 smear), HIT: blade at x 27..33, y -6..-12 (3), hold (4), recover (5-6)
    thrust = [S(hand=(2.0, -9.0), pike_ang=-20, face="front"),
              S(hand=(-1.0, -9.5), pike_ang=-6, lean=-6, face="shout"),
              S(hand=(7.0, -9.0), pike_ang=-4, lean=8, face="shout", smear=[("line", [(10, -11), (18, -10), (24, -9)], "white", 2)]),
              S(hand=(11.0, -9.0), pike_ang=-2, lean=12, face="shout", feet=((-4.0, 0.0), (4.5, 0.0)), spark=[(30.0, -9.5, 2)]),
              S(hand=(10.0, -9.0), pike_ang=-2, lean=10, feet=((-4.0, 0.0), (4.5, 0.0))),
              S(hand=(5.0, -9.0), pike_ang=-40, lean=4), S()]
    # Deal: draws three face-down cards from its own edge (0-2), flicks them out (3), recovers (4-6)
    deal = [S(hand2=(-2.0, -12.0), pike_ang=-85),
            S(hand2=(-1.0, -14.0), pike_ang=-85, cards=[(-1.0, -16.0, -20)]),
            S(hand2=(-6.0, -15.0), pike_ang=-85, face="shout", cards=[(-7.0, -17.0, -40), (-5.0, -18.0, -10), (-3.0, -17.0, 20)]),
            S(hand2=(4.0, -12.0), pike_ang=-85, face="shout", lean=6,
              cards=[(12.0, -16.0, 30), (14.0, -11.0, 80), (11.0, -6.0, 130)], smear=[("arc", 0.0, -10.0, 8.0, -140, -30, "white", 1)]),
            S(hand2=(2.0, -10.0), pike_ang=-85, lean=3), S(hand2=(-3.0, -9.0)), S()]
    eidle = [S(edge=True, bob=[0, -0.3, -0.5, -0.3][i], hand=(2.0, -9.0), hand2=(-1.0, -9.0), pike_ang=-88) for i in range(4)]
    erun = []
    for i in range(6):
        ph = i / 6 * math.tau
        erun.append(S(edge=True, lean=4, bob=-0.6 * abs(math.sin(ph)), hand=(2.0, -9.5), hand2=(-1.0, -9.5), pike_ang=-85,
                      feet=((-2.0 * math.cos(ph), -max(0, 2 * math.sin(ph))), (2.0 * math.cos(ph), -max(0, -2 * math.sin(ph))))))
    d0 = S(face="shout", lean=-12, turn=40, hand=(3.0, -13.0), pike_ang=-120)
    d1 = S(face="dead", lean=-40, turn=70, bob=1.5, hand=(1.0, -10.0), pike_ang=-170, knee=-1)
    d2 = _soldier_corpse(0)
    corpse = _soldier_corpse(1)
    knock = S(face="shout", lean=-16, turn=30, hand=(3.0, -12.0), pike_ang=-110)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Thrust", thrust, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12, 0.12]),
             ("Deal", deal, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12, 0.12]),
             ("EdgeIdle", eidle, [0.16, 0.14, 0.16, 0.14]), ("EdgeRun", erun, [0.08] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxCardSoldier", anims, outdir, scale=5)


def _soldier_corpse(stage):
    r = Rig()
    card(r, 0.0, -1.6, 12.0, 3.4 if stage else 5.0, z=0.0, lit=0.0)
    spade(r, 0.0, -1.8, 1.0, "blk", 0.1)
    r.stamp(SOLD_HEAD["dead"], -8.5, 0.0, 1.0, SOLD_LEG, pivot=(3, 5))
    r.polyline([(5, -1), (8, -2.5 if not stage else -1), (10, -0.5)], "blk", 0.5, tone=1)
    pike(r, -2.0, -0.6, -4, 0.3, ln=14.0)
    if stage == 0: dust_puff(r, 0.0, 0.0, 1, 1.2)
    return r.resolve()


# ================================================================== LOADED DIE: a living die on little legs
def loaded(hop=0.0, rot=(0.0, 22.0, 0.0), feet=((-3.0, 0.0), (3.0, 0.0)), squash=1.0, face="leer", tilt=0.0, size=11.0,
           smear=None, spark=None, dust=None, extra=None, legs=True, dz=0.0):
    r = Rig()
    by = -2.4 - hop
    cy = by - size * 0.55 * squash
    if legs:
        for k, f in enumerate(feet):
            hp = (f[0] * 0.7, by + 0.6)
            kn = (lerp(hp[0], f[0], 0.5) + 1.2, lerp(hp[1], f[1], 0.5))
            z = -1.0 if k == 0 else 1.0
            r.tube([hp, kn, (f[0], f[1] - 0.6)], [0.8, 0.7, 0.6], "blk", z, bias=-0.3 if k == 0 else 0.0)
            r.poly([(f[0] - 1.0, f[1] - 1.2), (f[0] + 1.6, f[1] - 1.0), (f[0] + 1.6, f[1]), (f[0] - 1.0, f[1])], "gold", z + 0.01,
                   bias=0.1 if k else -0.2)
    die3(r, 0.0, cy, size, rot[0], rot[1], rot[2] + tilt, z=0.0, pip_faces=2, pip_min=2.0, one="crim", pip="crim",
         pip_skip=1 if face else 0, tilt=12.0)
    if face and abs(rot[0]) < 1 and abs(rot[2] + tilt) < 25:
        # the leering face on its front: two pip eyes that glint, a pip grin
        fx, fy = -size * 0.5 * math.sin(math.radians(rot[1])) + tilt * 0.12, cy + 1.0
        eyes = [(fx - 1.8, fy - 1.6), (fx + 1.6, fy - 1.8)]
        for (x, y) in eyes:
            r.ell(x, y, 1.1, 1.1, "crim", 0.5, flat=1 if face != "shut" else 2)
            if face != "shut": r.dot(x + 0.4, y - 0.4, "eye", 3, 0.55)
        grin = [(fx - 2.6, fy + 1.6), (fx - 1.2, fy + 2.2), (fx + 0.4, fy + 2.4), (fx + 2.0, fy + 2.0)]
        if face == "shout": grin = [(fx - 1.0, fy + 1.8), (fx + 0.2, fy + 2.6), (fx - 1.0, fy + 3.0), (fx + 0.6, fy + 1.6)]
        for (x, y) in grin: r.dot(x, y, "crim", 1, 0.5)
    smears(r, smear); sparks(r, spark)
    if dust: dust_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def loaded_sheet(outdir):
    L = loaded
    idle = [L(hop=[0, 0.5, 1.0, 0.5][i], feet=((-3.0, 0.0), (3.0, 0.0)), rot=(0.0, 22.0 + [0, 2, 4, 2][i], 0.0)) for i in range(4)]
    run = [L(hop=1.5 * abs(math.sin(i / 6 * math.pi * 2)), tilt=6 * math.sin(i / 6 * math.tau),
             feet=((-3.0 + 2 * math.cos(i / 6 * math.tau), -max(0, math.sin(i / 6 * math.tau))), (3.0 - 2 * math.cos(i / 6 * math.tau), -max(0, -math.sin(i / 6 * math.tau)))))
           for i in range(6)]
    # Slam: crouch (0), spring up (1-2), hang (3), SLAM down in front (4: the hit), shudder (5), stand (6)
    slam = [L(hop=-1.0, face="leer"), L(hop=4.0, tilt=-8, face="shout"), L(hop=8.0, tilt=-14, face="shout", feet=((-2.0, -6.0), (3.0, -6.0))),
            L(hop=9.0, tilt=10, face="shout", feet=((-2.0, -7.0), (4.0, -7.0)), smear=[("line", [(-4, -14), (-4, -20)], "white", 1)]),
            L(hop=-0.5, tilt=18, face="shout", spark=[(10.0, -2.0, 1)], dust=(6.0, 0.0, 0, 1.2),
              smear=[("line", [(6, -10), (6, -16)], "white", 2), ("line", [(9, -8), (9, -13)], "white", 1)]),
            L(hop=0.0, tilt=8, dust=(6.0, 0.0, 1, 1.4)), L()]
    # Roll: tips forward (0), tumbles over (1-6: a quarter turn every 1.5 frames, legs tucked), lands on a face (7)
    roll = [L(tilt=-10, face="shout")]
    for k in range(6):
        roll.append(L(hop=2.0 + 1.5 * math.sin(k / 5 * math.pi), rot=(0.0, 30.0, 60.0 * (k + 1)), face=None, legs=False,
                      dust=(-6.0, 0.0, k % 3, 0.8) if k % 2 == 0 else None))
    roll.append(L(face="leer", dust=(0.0, 0.0, 0, 1.4), spark=[(0.0, -18.0, 2)]))
    d0 = L(tilt=-20, face="shout", hop=1.0)
    d1 = L(tilt=-50, face="shut", hop=0.5, legs=False)
    d2 = L(rot=(0.0, 20.0, -90.0), face=None, legs=False, extra=lambda r: dust_puff(r, 0.0, 0.0, 1, 1.4))
    corpse = _die_corpse()
    knock = L(tilt=-16, face="shout", hop=1.0, feet=((-4.0, 0.0), (2.0, 0.0)))
    anims = [("Idle", idle, [0.16, 0.12, 0.16, 0.12]), ("Run", run, [0.07] * 6),
             ("Slam", slam, [0.1, 0.08, 0.1, 0.1, 0.05, 0.12, 0.14]),
             ("Roll", roll, [0.1] + [0.06] * 6 + [0.18])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxLoadedDie", anims, outdir, scale=5)


def _die_corpse():
    r = Rig()
    die3(r, 0.0, -4.6, 9.0, 0.0, 0.0, 0.0, z=0.0, tilt=10.0, pip_faces=1, pip_min=1.0, one="crim", pip="crim")
    for k, x in enumerate((-6.0, 6.0)):
        r.tube([(x * 0.6, -1.0), (x, -0.6), (x * 1.4, -0.4)], [0.7, 0.6, 0.5], "blk", 0.5 + k)
    for (x, y) in ((-2, -10), (2, -11), (0, -12)):
        r.dot(x, y, "smoke", 2, 2.0)
    return r.resolve()


# ================================================================== registry
JOBS = [("JinxMarionette", mario_sheet), ("JinxFortuneTeller", seer_sheet), ("JinxSnakeEyes", snake_sheet),
        ("JinxCardSoldier", soldier_sheet), ("JinxLoadedDie", loaded_sheet)]
SYNC = {
    "JinxMarionette": {"Lash": [("HIT: the hand at (14, -10); swipe x -6..16", 3)], "Strings": [("three threads leave the hands at (12, -14)", 3)]},
    "JinxFortuneTeller": {"Gaze": [("bolt leaves the ball at (11, -13)", 3)], "Foretell": [("the ball drives down: the mark lands", 4)]},
    "JinxSnakeEyes": {"Strike": [("HIT: jaws at (17, -7)", 3)], "Craps": [("two dice flicked from (12, -4)", 3)]},
    "JinxCardSoldier": {"Thrust": [("HIT: blade at x 27..33, y -12..-6", 3)], "Deal": [("three cards flicked out", 3)]},
    "JinxLoadedDie": {"Slam": [("SLAM: the die lands at (6, -2)", 4)], "Roll": [("tumble starts", 1), ("lands on a face", 7)]},
}
NOTES = {
    "JinxMarionette": "MirrorIdle/MirrorRun: the stance while it mirrors the hero (strings glowing, head tilted).",
    "JinxFortuneTeller": "Idle/Run/Foretell show a clouded ball; the Tower (red), Fool (gold) and Star (blue) sets show the coming fate.",
    "JinxSnakeEyes": "Dazed (4) loops while it has crapped out.",
    "JinxCardSoldier": "EdgeIdle/EdgeRun: turned edge-on (Paper Thin), a 2 px card.",
}
