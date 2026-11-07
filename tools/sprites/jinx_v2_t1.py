"""Jinx tier 1: Jack-in-the-Box, its loose head (the Loose Jack minion) and the Card Sharp. Built through
jinx_v2_rigs.py (python3 jinx_v2_rigs.py --only JinxJackBox,JinxJackMinion,JinxCardSharp). Same renderer, same rules:
material ramps, top-left light, selective outline, hand-pixelled faces, every frame posed. T1 idle limit 20 x 16."""
import math
from jinx_v2_rigs import (Rig, Xf, chain, ik, lerp, die3, box3, card, harl, star, arc_smear, dust_puff, sheet, tail_anims,
                          line_px)

# ================================================================== JACK-IN-THE-BOX
JACK_LEG = {"k": ("blk", 0), "b": ("blk", 2), "B": ("blk", 3), "n": ("crim", 1), "C": ("crim", 3), "c": ("crim", 2),
            "g": ("gold", 2), "G": ("gold", 4), "z": ("gold", 1), "a": ("ivory", 1), "w": ("ivory", 2), "W": ("ivory", 3),
            "X": ("ivory", 4), "m": ("blk", 0), "r": ("eye", 2)}
JACK_HEAD = {
    # pivot (3, 5): the chin, where the spring meets the head
    "grin": """
G.....G
nCgggbk
.aWXWa.
aWmWmWw
wWnCnWa
.awwwa.
""",
    "shout": """
G.....G
nCgggbk
.aWXWa.
aWmWmWw
wWmmmWa
.awnwa.
""",
    "squash": """
.G...G.
GnCgbkG
aWXWWWw
wWmWmWa
.awnwa.
""",
    "hurt": """
.G...G.
nCgggbk
.aWXWa.
aWWmWmw
wWmnmWa
.awwwa.
""",
    "dead": """
.......
nCgggbk
.aWXWa.
amWmWmw
wWmWmWa
.awmwa.
""",
}


def jack_head(r, x, y, face, z=4.0):
    piv = (3, 4) if face == "squash" else (3, 5)
    r.stamp(JACK_HEAD[face], x, y, z, JACK_LEG, pivot=piv)


def spring(r, x0, y0, x1, y1, z, coils=None, mat="gold"):
    """A coiled spring from (x0, y0) to (x1, y1): zigzag across the axis, 2 px wide, lit coils / dark backs."""
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 0.5: return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    n = coils or max(2, int(L / 1.6))
    pts = []
    for i in range(n * 2 + 1):
        t = i / (n * 2.0)
        s = (1.2 if i % 2 else -1.2) if 0 < i < n * 2 else 0.0
        pts.append((x0 + ux * L * t + nx * s, y0 + uy * L * t + ny * s))
    tones = [3 if i % 2 == 0 else 1 for i in range(len(pts) - 1)]
    r.polyline(pts, mat, z, tones=tones)


def jack(head=(0.5, -10.5), face="grin", crank=0.0, tilt=0.0, feet=((-2.5, 0.0), (2.5, 0.0)), lift=0.0, lid=1.0,
         sink=0.0, smear=None, spark=None, dust=None, extra=None, head_on=True, spring_from=None, coils=None):
    """head: chin position (spring from the box's opening to it). crank: crank-arm angle. tilt: box tilt (deg).
    lid: 1 = flung open behind, 0 = shut on top. sink: px the box has sunk into the floor (Pop)."""
    r = Rig()
    by = -1.6 - lift + sink                       # the box's bottom
    T = Xf(tilt, (0.0, by))
    # stubby legs and shoes (behind the box)
    if sink < 1.0:
        for k, f in enumerate(feet):
            hx, hy = T(f[0] * 0.8, by)
            z = -1.0 if k == 0 else 0.6
            r.tube([(hx, hy), (f[0], f[1] - 0.8)], [0.8, 0.8], "blk", z, bias=-0.25 if k == 0 else 0.0)
            r.poly([(f[0] - 1.0, f[1] - 1.4), (f[0] + 1.8, f[1] - 1.0), (f[0] + 1.8, f[1]), (f[0] - 1.0, f[1])], "blk", z + 0.01,
                   bias=0.2 if k else -0.2)
            r.dot(f[0] + 1.0, f[1] - 1.2, "gold", 3 if k else 2, z + 0.02)
    # the box: harlequin front, gold rim, crimson top, darker side with the crank
    bl, br, tr, tl = box3(r, -5.0, by, 10.0, 6.0, 3.0, "crim", 1.0, side="coat", ang=tilt, pivot=(0.0, by))
    r.polyline([tl, tr], "gold", 1.05, tone=3)
    r.polyline([bl, br], "gold", 1.05, tone=1)
    for (cx_, cy_) in (bl, br, tr, tl):
        r.dot(cx_, cy_, "gold", 2, 1.06)
    # the front's emblem: a black diamond with an ivory pip
    c0 = T(0.0, by - 3.0)
    r.poly([(c0[0], c0[1] - 2.6), (c0[0] + 2.2, c0[1]), (c0[0], c0[1] + 2.6), (c0[0] - 2.2, c0[1])], "gold", 1.07,
           normal=(-0.3, -0.3, 1.0))
    r.dot(c0[0], c0[1], "crim", 1, 1.08)
    # crank on the side face
    ax, ay = T(6.4, by - 3.4)
    a = math.radians(crank)
    kx, ky = ax + 1.8 * math.cos(a), ay + 1.8 * math.sin(a) * 0.8
    r.dot(ax, ay, "gold", 2, 1.2)
    r.line(ax, ay, kx, ky, "gold", 1.25, tone=3)
    r.dot(kx, ky, "ivory", 4, 1.3)
    # lid: hinged at the back edge of the top, flung back
    hx0, hy0 = T(-4.0, by - 7.6)
    if lid > 0.5:
        r.poly([(hx0, hy0), (hx0 + 3.0, hy0 + 0.4), (hx0 - 0.8, hy0 - 4.6), (hx0 - 2.6, hy0 - 3.6)], "crim", -0.5,
               bias=-0.25, normal=(-0.6, -0.3, 0.7))
        r.line(hx0 - 2.6, hy0 - 3.6, hx0 - 0.8, hy0 - 4.6, "gold", -0.45, tone=2)
    else:
        r.poly([T(-5.4, by - 6.0), T(5.4, by - 6.0), T(7.2, by - 8.4), T(-3.4, by - 8.4)], "crim", 1.4, bias=0.2,
               normal=(-0.1, -1.0, 0.6))
        r.line(*T(-5.4, by - 6.0), *T(5.4, by - 6.0), "gold", 1.45, tone=3)
    # spring and head
    if head_on and head is not None:
        sx, sy = spring_from or T(0.8, by - 7.4)
        spring(r, sx, sy, head[0], head[1] + 0.5, 2.0, coils=coils)
        jack_head(r, head[0], head[1], face)
    if smear:
        for pts, m, tn in smear:
            r.polyline(pts, m, 4.6, tone=tn)
    if spark:
        for (x, y, k) in spark: star(r, x, y, k)
    if dust: dust_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def confetti(r, x, y, k, n=10, seed=1, spread=9.0):
    """A burst of confetti flecks around (x, y): k = 0 (tight) .. 3 (scattered, falling)."""
    import random
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, math.tau)
        d = spread * (0.35 + 0.65 * rnd.random()) * (0.4 + 0.25 * k)
        m = rnd.choice(("crim", "gold", "chipb", "glow", "ivory"))
        r.dot(x + d * math.cos(a), y + d * math.sin(a) * 0.8 + k * 1.5, m, 3, 8.0)


def jack_sheet(outdir):
    J = jack
    idle = [J(head=(0.5 + [0, 0.3, 0, -0.3][i], -10.5 + [0, 0.4, 0.8, 0.4][i]), crank=90 * i) for i in range(4)]
    # Wind: crank spinning hard, head squashed into its shoulders, box shivering (shown while it winds up)
    wind = [J(head=(0.5, -10.0 + [0, -0.5, 0, -0.5][i]), face="squash", crank=120 * i + 30, tilt=[-2, 2, -2, 2][i],
              coils=2) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (2.5 * math.cos(ph), -max(0.0, 1.4 * math.sin(ph)))
        f2 = (-2.5 * math.cos(ph), -max(0.0, -1.4 * math.sin(ph)))
        run.append(J(head=(-0.5 - 0.8 * math.sin(ph), -10.5 - 1.0 * abs(math.cos(ph))), tilt=6 * math.sin(ph), feet=(f2, f1),
                     lift=0.6 * abs(math.sin(ph)), crank=60 * i))

    def punch(tip, smear_pts, spark_at=None, dust=None):
        P = [J(head=(0.5, -9.5), face="squash", crank=0, coils=2),                     # duck in
             J(head=(-0.5, -9.0), face="squash", crank=40, tilt=-6, coils=2),          # coil back
             J(head=tip[0], face="shout", crank=80, tilt=4, smear=smear_pts),          # launch
             J(head=tip[1], face="shout", crank=100, tilt=8, spark=[spark_at] if spark_at else None, dust=dust),   # HIT
             J(head=tip[2], face="grin", crank=110, tilt=5),                          # overshoot wobble
             J(head=tip[3], face="grin", crank=130, tilt=2),                          # retract
             J(head=(0.5, -10.5), face="grin", crank=160)]
        return P
    fwd = punch([(8.0, -12.0), (15.5, -10.0), (13.5, -11.0), (6.0, -12.0)],
                [([(2, -14), (6, -14), (9, -13)], "white", 2)], (19.0, -9.0, 1))
    up = punch([(2.0, -17.0), (2.5, -24.0), (2.0, -21.5), (1.0, -15.0)],
               [([(-1, -13), (-1, -17), (0, -20)], "white", 2)], (3.0, -28.0, 1))
    down = punch([(7.0, -8.0), (8.5, -3.5), (8.0, -5.0), (5.0, -9.0)],
                 [([(3, -12), (6, -10), (8, -7)], "white", 2)], (10.0, -1.0, 1), dust=(9.0, 0.0, 0, 0.8))
    # Pop: duck in, lid shut, rattle, sink through the floor in a puff (4 = gone: the teleport), burst up by the hero (5)
    pop = [J(head=(0.5, -8.5), face="squash", coils=1),
           J(head=None, lid=0.0, tilt=-4, head_on=False),
           J(head=None, lid=0.0, tilt=4, head_on=False, sink=3.0, dust=(0.0, 0.0, 0, 1.0)),
           J(head=None, lid=0.0, head_on=False, sink=6.5, dust=(0.0, 0.0, 1, 1.3)),
           _puff(),
           J(head=(0.5, -21.0), face="shout", lift=1.5, extra=lambda r: confetti(r, 0.5, -14.0, 0, 12, 3)),
           J(head=(0.5, -14.5), face="grin", extra=lambda r: confetti(r, 0.5, -14.0, 1, 12, 3)),
           J(head=(0.5, -9.5), face="squash", coils=2, extra=lambda r: confetti(r, 0.5, -14.0, 2, 10, 3)),
           J(head=(0.5, -10.5), face="grin", extra=lambda r: confetti(r, 0.5, -14.0, 3, 8, 3))]
    d0 = J(head=(-1.5, -10.5), face="hurt", tilt=-8, crank=200)
    d1 = J(head=(-6.0, -16.0), face="dead", tilt=-18, crank=240, spring_from=(0.0, -9.0), coils=4)
    d2 = jack_corpse(0)
    corpse = jack_corpse(1)
    knock = J(head=(-3.0, -10.5), face="hurt", tilt=-12, crank=180)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.07] * 6), ("Wind", wind, [0.07] * 4),
             ("Punch", fwd, [0.12, 0.1, 0.05, 0.08, 0.08, 0.1, 0.12]),
             ("PunchUp", up, [0.12, 0.1, 0.05, 0.08, 0.08, 0.1, 0.12]),
             ("PunchDown", down, [0.12, 0.1, 0.05, 0.08, 0.08, 0.1, 0.12]),
             ("Pop", pop, [0.08, 0.08, 0.08, 0.08, 0.1, 0.08, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxJackBox", anims, outdir, scale=6)


def _puff():
    r = Rig()
    for i, (x, y, rr) in enumerate(((-3, -3, 2.4), (2, -4, 2.8), (0, -7, 2.2), (4, -1.5, 1.8), (-4, -1, 1.6))):
        r.ell(x, y, rr, rr * 0.85, "smoke", 1.0 + i * 0.01, bias=0.2)
    confetti(r, 0.0, -5.0, 0, 8, 7, spread=7)
    return r.resolve()


def jack_corpse(stage):
    r = Rig()
    # the box on its side (front face up-left), lid hanging open, the head lying beyond it on a sprung coil
    box3(r, -6.0, -0.0, 8.0, 6.0, 2.5, "crim", 1.0, side="coat",
         ang=-90 if stage else -70, pivot=(-2.0, 0.0))
    spring(r, 0.5, -3.0, 6.5 if stage else 5.5, -2.0 if stage else -4.0, 2.0, coils=3)
    jack_head(r, 9.5 if stage else 8.5, 0.0 if stage else -2.0, "dead", z=3.0)
    if stage == 0:
        dust_puff(r, 2.0, 0.0, 1, 1.0)
    return r.resolve()


# ================================================================== LOOSE JACK (minion): the head alone on its spring
def loose(base=(0.0, 0.0), head=(0.5, -8.5), face="grin", squash=0, smear=None, spark=None, dust=None, coils=3, extra=None):
    r = Rig()
    bx, by = base
    # the spring's foot: a gold cap it hops on
    r.ell(bx, by - 0.6, 2.4, 0.9, "gold", 0.5, bias=0.1)
    spring(r, bx, by - 1.2, head[0], head[1] + 0.5, 1.0, coils=coils)
    jack_head(r, head[0], head[1], face)
    if smear:
        for pts, m, tn in smear: r.polyline(pts, m, 4.6, tone=tn)
    if spark:
        for (x, y, k) in spark: star(r, x, y, k)
    if dust: dust_puff(r, *dust)
    if extra: extra(r)
    return r.resolve()


def minion_sheet(outdir):
    L = loose
    idle = [L(head=(0.5, -8.5 + [0, 1.0, 1.5, 1.0][i]), coils=[3, 2, 2, 2][i], face="squash" if i == 2 else "grin")
            for i in range(4)]
    run = []
    for i in range(6):
        hop = math.sin(i / 6 * math.pi)
        run.append(L(base=(0.0, -3.0 * hop), head=(1.0 + 0.5 * hop, -9.5 - 3.0 * hop), coils=3 if hop > 0.3 else 2,
                     face="grin" if hop > 0.3 else "squash", dust=(0.0, 0.0, 1, 0.6) if i == 0 else None))

    def butt(tip, sm, sp):
        return [L(head=(-0.5, -6.5), face="squash", coils=2), L(head=(-1.5, -6.0), face="squash", coils=2),
                L(head=tip[0], face="shout", smear=sm), L(head=tip[1], face="shout", spark=[sp]),
                L(head=tip[2], face="grin"), L(head=(1.5, -8.0), face="grin"), L(head=(0.5, -8.5), face="grin")]
    fwd = butt([(4.5, -9.0), (7.5, -8.5), (6.0, -9.0)], [([(-1, -11), (2, -11), (4, -10)], "white", 2)], (11.0, -8.0, 1))
    up = butt([(1.0, -13.0), (1.5, -17.5), (1.0, -15.0)], [([(-1, -9), (-1, -12), (0, -14)], "white", 2)], (2.0, -22.0, 1))
    down = butt([(4.0, -6.0), (6.0, -3.0), (5.0, -5.0)], [([(0, -9), (2, -8), (4, -6)], "white", 2)], (8.0, -1.0, 1))
    d0 = L(head=(-1.5, -8.0), face="hurt")
    d1 = L(head=(-4.0, -12.0), face="dead", coils=4)
    d2 = _minion_corpse(0)
    corpse = _minion_corpse(1)
    knock = L(head=(-2.5, -8.0), face="hurt")
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.06] * 6),
             ("Punch", fwd, [0.1, 0.08, 0.05, 0.08, 0.08, 0.1, 0.1]),
             ("PunchUp", up, [0.1, 0.08, 0.05, 0.08, 0.08, 0.1, 0.1]),
             ("PunchDown", down, [0.1, 0.08, 0.05, 0.08, 0.08, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxJackMinion", anims, outdir, scale=6)


def _minion_corpse(stage):
    r = Rig()
    r.ell(-4.0, -0.6, 2.4, 0.9, "gold", 0.5)
    spring(r, -3.0, -1.0, 2.0, -1.5 if stage else -3.0, 1.0, coils=3)
    jack_head(r, 5.0, 0.0 if stage else -1.0, "dead", z=2.0)
    return r.resolve()


# ================================================================== CARD SHARP: a hunched goblin dealer
SHARP_LEG = {"F": ("felt", 3), "f": ("felt", 2), "h": ("felt", 4), "e": ("felt", 1), "g": ("gob", 2), "G": ("gob", 3),
             "L": ("gob", 4), "d": ("gob", 1), "Y": ("fire", 4), "m": ("blk", 0), "w": ("ivory", 3), "n": ("crim", 1),
             "z": ("gold", 4)}
SHARP_HEAD = {
    # pivot (4, 6): under the chin. Green dealer's visor, a pointed ear behind, one sly yellow eye, a long nose.
    "sly": """
..eFFFF...
.eFfhhfFF.
d.gGGGGg..
dgGYmGGgL.
.gGGGGgLLd
..gwnzwg..
...dggd...
""",
    "glee": """
..eFFFF...
.eFfhhfFF.
d.gGGGGg..
dgGmmGGgL.
.gGGGGgLLd
..gnnnng..
...dwwd...
""",
    "hurt": """
..eFFFF...
.eFfhhfFF.
d.gGGGGg..
dgGmYGGgL.
.gGGGGgLLd
..gmnnmg..
...dggd...
""",
    "dead": """
..........
.eFFFFF...
deFfhhfFF.
dgGmGmGgL.
.gGGmGgLLd
..gnmmng..
...dggd...
""",
}


def card_fan(r, hx, hy, ang, n, z, spread=22.0, size=(3.0, 4.0), gold=False):
    """n cards fanned from a hand at (hx, hy), centre card pointing ang (deg)."""
    for i in range(n):
        a = ang + (i - (n - 1) / 2.0) * spread
        cx, cy = hx + 2.2 * math.cos(math.radians(a)), hy + 2.2 * math.sin(math.radians(a))
        card(r, cx, cy, size[0], size[1], z=z + 0.01 * i, ang=a + 90, mat_face="gold" if gold else "card",
             pip=None if gold else [(0, 0)], pip_mat="crim" if i % 2 else "blk")


def sharp(lean=0.0, bob=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), hand=(6.5, -7.0), hand2=(-5.5, -7.0), face="sly",
          fan=3, fan2=3, fan_ang=-60.0, fan2_ang=-120.0, flying=(), smear=None, spark=None, ace=None, head_dx=0.0, extra=None,
          knee=1):
    r = Rig()
    hip = (0.0, -3.4 + bob)
    T = Xf(lean, hip)
    for k, f in enumerate(feet):
        hp = (hip[0] + (-0.8 if k == 0 else 0.8), hip[1])
        kn = ik(hp[0], hp[1], f[0], f[1] - 0.6, 2.0, 1.8, bend=-knee)
        z = -1.0 if k == 0 else 1.0
        r.tube([hp, kn, (f[0], f[1] - 0.6)], [1.0, 0.8, 0.7], "blk", z, bias=-0.3 if k == 0 else 0.0)
        r.poly([(f[0] - 0.8, f[1] - 1.2), (f[0] + 2.6, f[1] - 0.6), (f[0] + 1.4, f[1]), (f[0] - 0.8, f[1])], "lthr", z + 0.01,
               bias=-0.2 if k == 0 else 0.15)
    sh_n, sh_f = T(hip[0] + 2.4, hip[1] - 4.6), T(hip[0] - 1.6, hip[1] - 4.8)
    # far arm + its fan of cards
    e2 = ik(sh_f[0], sh_f[1], hand2[0], hand2[1], 2.6, 2.4, bend=1)
    r.tube([sh_f, e2, hand2], [1.0, 0.9, 0.8], "ivory", -0.6, bias=-0.35)
    if fan2: card_fan(r, hand2[0], hand2[1], fan2_ang, fan2, -0.7)
    r.ell(hand2[0], hand2[1], 0.9, 0.9, "gob", -0.55, bias=-0.1)
    # hunched body: crimson waistcoat over a white shirt, a little hump
    r.ell(*T(hip[0] - 0.2, hip[1] - 2.6), 3.6, 3.2, "crim", 0.0, bias=0.05)
    r.ell(*T(hip[0] - 1.6, hip[1] - 4.2), 2.2, 1.8, "crim", -0.1, bias=0.1)
    r.poly([T(hip[0] + 1.0, hip[1] - 5.4), T(hip[0] + 3.2, hip[1] - 4.6), T(hip[0] + 2.4, hip[1] - 1.6)], "ivory", 0.2, bias=0.1)
    r.dot(*T(hip[0] + 2.0, hip[1] - 3.8), "gold", 4, 0.3)
    r.dot(*T(hip[0] + 1.8, hip[1] - 2.2), "gold", 3, 0.3)
    # head
    hx, hy = T(hip[0] + 1.6 + head_dx, hip[1] - 5.2)
    r.stamp(SHARP_HEAD[face], hx, hy, 2.0, SHARP_LEG, pivot=(4, 6))
    # near arm + fan
    e1 = ik(sh_n[0], sh_n[1], hand[0], hand[1], 2.6, 2.4, bend=1)
    r.tube([sh_n, e1, hand], [1.1, 0.9, 0.8], "ivory", 3.0)
    if fan: card_fan(r, hand[0], hand[1], fan_ang, fan, 3.1)
    if ace: card(r, ace[0], ace[1], 3.0, 4.0, mat_face="gold", z=3.3, ang=ace[2], lit=0.15)
    r.ell(hand[0], hand[1], 1.0, 1.0, "gob", 3.2, bias=0.1)
    for (x, y, a, m) in flying:
        card(r, x, y, 3.0, 4.0, mat_face=m, z=4.0, ang=a, pip=None if m == "gold" else [(0, 0)], lit=0.1)
    if smear:
        for sm in smear:
            arc_smear(r, *sm) if sm[0] != "line" else r.polyline(sm[1], sm[2], 4.5, tone=sm[3])
    if spark:
        for (x, y, k) in spark: star(r, x, y, k)
    if extra: extra(r)
    return r.resolve()


def sharp_sheet(outdir):
    S = sharp
    # idle: a card arcs from the far hand over the head into the near hand
    arc = [(-6.0, -9.0), (-3.0, -12.5), (3.0, -12.5), (6.5, -9.0)]
    idle = [S(bob=[0, 0.3, 0.5, 0.3][i], flying=[(arc[i][0], arc[i][1], 30 * i - 40, "card")], fan=2 if i < 3 else 3,
              fan2=2 if i > 0 else 3) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        f1 = (2.6 * math.cos(ph), -max(0.0, 1.2 * math.sin(ph)))
        f2 = (-2.6 * math.cos(ph), -max(0.0, -1.2 * math.sin(ph)))
        run.append(S(lean=14, bob=-0.4 * abs(math.sin(ph)), feet=(f2, f1), hand=(5.5, -6.0 + 0.6 * math.sin(ph)),
                     hand2=(-4.0, -6.5 - 0.6 * math.sin(ph)), fan_ang=-30, fan2_ang=-150))
    # Deal: draw back (0), cock (1), flick (2, smear), release three cards (3), follow (4), settle (5)
    deal = [S(hand=(1.5, -8.5), fan_ang=-90, face="sly", lean=-4),
            S(hand=(-1.5, -10.0), fan_ang=-130, face="glee", lean=-10, hand2=(-6.0, -6.0)),
            S(hand=(5.0, -9.0), fan_ang=-40, face="glee", lean=4, smear=[(1.0, -6.0, 6.0, -150, -40, "white", 1)]),
            S(hand=(8.5, -7.5), fan=0, face="glee", lean=10,
              flying=[(13.0, -10.5, 70, "card"), (13.5, -8.0, 90, "card"), (13.0, -5.5, 110, "card")]),
            S(hand=(8.0, -6.5), fan=0, face="sly", lean=8),
            S(hand=(6.5, -7.0), fan=1, face="sly")]
    # Ace: into the sleeve (0), the gold Ace comes out with a glint (1), cocked at the ear (2), FLICKED (3), follow (4-5)
    ace = [S(hand=(-2.0, -8.0), fan=0, face="sly", lean=-2),
           S(hand=(1.0, -13.0), fan=0, face="glee", ace=(1.0, -16.0, 10), spark=[(3.0, -18.0, 1)], lean=-4),
           S(hand=(-1.5, -12.0), fan=0, face="glee", ace=(-2.0, -14.5, -30), lean=-10, spark=[(-1.0, -17.0, 2)]),
           S(hand=(8.5, -8.0), fan=0, face="glee", lean=12, flying=[(13.5, -8.0, 90, "gold")],
             smear=[("line", [(-2, -14), (4, -12), (10, -9)], "gold", 3), ("line", [(-1, -13), (5, -11), (10, -8)], "gold", 2)]),
           S(hand=(8.0, -7.0), fan=0, face="sly", lean=8),
           S(hand=(6.5, -7.0), fan=2, face="sly")]
    # Shuffle: riffle a bridge of cards hand to hand (0-2), the deck bursts round it (3: the swap), cards rain back (4-6)
    def cloud(k):
        def f(r):
            for i in range(9):
                a = i / 9 * math.tau + k * 0.4
                d = 6.0 + 2.0 * k
                card(r, d * math.cos(a), -7.0 + d * 0.7 * math.sin(a) + k, 2.0, 3.0, z=6.0 + i * 0.01, ang=a * 57 + 30 * k,
                     back=("crim" if i % 2 else "card"), lit=0.1)
        return f
    shuffle = [S(hand=(3.5, -9.0), hand2=(-3.5, -9.0), fan_ang=-120, fan2_ang=-60,
                 flying=[(0.0, -12.0, 0, "card")]),
               S(hand=(3.5, -10.0), hand2=(-3.5, -10.0), fan_ang=-120, fan2_ang=-60, face="glee",
                 flying=[(-2.0, -13.0, -20, "card"), (0.0, -14.0, 0, "card"), (2.0, -13.0, 20, "card")]),
               S(hand=(2.0, -11.0), hand2=(-2.0, -11.0), fan=0, fan2=0, face="glee",
                 flying=[(-3.0, -13.0, -40, "card"), (-1.0, -15.0, -15, "card"), (1.0, -15.0, 15, "card"), (3.0, -13.0, 40, "card")]),
               S(fan=0, fan2=0, face="glee", extra=cloud(0)),
               S(fan=0, fan2=0, face="sly", extra=cloud(1)),
               S(fan=1, fan2=1, face="sly", extra=cloud(2)),
               S(face="sly")]
    d0 = S(face="hurt", lean=-12, hand=(4.0, -10.0), hand2=(-7.0, -9.0), fan=1, fan2=1,
           flying=[(8.0, -13.0, 40, "card"), (-9.0, -12.0, -50, "card")])
    d1 = S(face="dead", lean=-35, bob=1.0, hand=(2.0, -11.0), hand2=(-8.0, -6.0), fan=0, fan2=0, knee=-1,
           flying=[(9.0, -6.0, 80, "card"), (-10.0, -5.0, -70, "card"), (3.0, -15.0, 10, "card")])
    d2 = _sharp_corpse(0)
    corpse = _sharp_corpse(1)
    knock = S(face="hurt", lean=-14, hand=(4.0, -9.0), hand2=(-7.0, -8.0), fan=2, fan2=1)
    anims = [("Idle", idle, [0.14, 0.12, 0.12, 0.14]), ("Run", run, [0.07] * 6),
             ("Deal", deal, [0.12, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Ace", ace, [0.12, 0.14, 0.12, 0.05, 0.1, 0.12]),
             ("Shuffle", shuffle, [0.1, 0.1, 0.1, 0.08, 0.1, 0.12, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, d2, corpse], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("JinxCardSharp", anims, outdir, scale=6)


def _sharp_corpse(stage):
    r = Rig()
    r.ell(0.0, -1.8, 4.2, 1.8, "crim", 1.0)
    r.tube([(3.5, -1.2), (6.5, -1.0 if stage else -2.5), (8.0, -0.6)], [0.9, 0.8, 0.7], "blk", 0.8)
    r.tube([(-3.0, -2.0), (-1.0, -4.5 if not stage else -3.0)], [0.9, 0.8], "ivory", 1.2)
    r.stamp(SHARP_HEAD["dead"], -6.0, 0.0, 2.0, SHARP_LEG, pivot=(4, 6))
    for i, (x, a) in enumerate(((10.0, 70), (-12.0, -60), (4.0, 20), (13.0, 100))[:4 if stage else 3]):
        card(r, x, -1.2, 3.0, 2.0, z=0.5 + i * 0.01, ang=a * 0.2, pip=[(0, 0)], back="crim" if i % 2 else None)
    return r.resolve()


# ================================================================== registry
JOBS = [("JinxJackBox", jack_sheet), ("JinxJackMinion", minion_sheet), ("JinxCardSharp", sharp_sheet)]
SYNC = {
    "JinxJackBox": {"Punch": [("HIT: the head at (16, -10), spark (19, -9); box 16 x 10 centred (12, -10)", 3)],
                    "PunchUp": [("HIT: the head at (3, -24)", 3)], "PunchDown": [("HIT: the head slams the floor at (9, -3)", 3)],
                    "Pop": [("lid shut (invulnerable from 1)", 1), ("gone: teleport here", 4), ("bursts up beside the hero", 5)]},
    "JinxJackMinion": {"Punch": [("HIT: the head at (8, -9)", 3)]},
    "JinxCardSharp": {"Deal": [("three cards leave the hand at (13, -8)", 3)], "Ace": [("the gold Ace leaves at (13, -8)", 3)],
                      "Shuffle": [("the deck bursts: swap places here", 3)]},
}
NOTES = {
    "JinxJackBox": "Wind (4) is the idle shown while it winds itself up (Wound Up); the music-note count is FxJinxWind.",
    "JinxCardSharp": "Ace is the third Deal: the gold Ace card (FxJinxAce) instead of three cards.",
}
