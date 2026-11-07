"""Bel'Mora tier 1: Bell Urchin, Lurefish, Barnacle Crab. Built through belmora_v2_rigs.py
(python3 belmora_v2_rigs.py --only BelUrchin,BelLurefish,BelCrab). T1 idle limit 20 x 16."""
import math
from belmora_v2_rigs import (Rig, Xf, chain, ik, lerp, eye, spines, foam_ring, drips, bubbles, barnacles, leg, crab_legs,
                             claw, fin, dust, splash, star, arc_smear, sheet, tail_anims, legend)

# ================================================================== BELL URCHIN
BELL = legend(k="bronze:0", d="bronze:1", b="bronze:2", B="bronze:3", H="bronze:4", v="verd:2", V="verd:3")
SMALL_BELL = """
.dBd.
dbHBd
dbBbk
vbbbd
kddkk
"""


def urchin(rot=0.0, bob=0.0, sx=1.0, sy=1.0, ln=4.0, feet=0, grip=False, bell=0.0, eyes=True, curl=0.0, x=0.0,
           smear=None, foam=None, hurt=False, extra=None, ball=False):
    """The urchin: a teal-black spined ball on a fringe of pale tube feet, a little bronze bell rattling inside.
    rot turns the spines (deg), curl 0..1 folds them flat (the roll), grip splays the tube feet (the brine tell)."""
    r = Rig()
    cy = -6.5 + bob - (0.0 if not ball else -1.0)
    rx, ry = 5.0 * sx, 4.6 * sy
    L = ln * (1.0 - 0.75 * curl)
    # back spines first (behind the body)
    spines(r, x, cy, rx, ry, 20, L, "urch", -1.0, phase=math.radians(rot), skip_down=not ball, front=False, tips=4)
    # tube feet: a fringe of pale nubs under the body
    if not ball:
        n = 6
        for i in range(n):
            u = (i / (n - 1)) * 2 - 1
            spread = 7.5 if grip else 4.0
            fx = x + u * spread + (0.5 if (i + feet) % 2 else 0)
            lift = 0 if grip else ((i + feet) % 3 == 0)
            top = (x + u * 3.2, cy + ry * 0.75)
            r.line(top[0], top[1], fx, -lift, "hag", 0.5, tone=3 if u < 0.3 else 2)
            r.dot(fx, -lift, "pouch", 3, 0.6)
            if grip: r.dot(fx + (1 if u > 0 else -1), 0, "pouch", 2, 0.6)
    r.ell(x, cy, rx, ry, "teal", 0.0, bias=-0.05)
    # mottled crown: darker dimples where the spines root
    for (dx, dy) in ((-2, -3), (1, -3.5), (3, -1.5), (-3.5, -0.5), (0, -1)):
        r.dot(x + dx * sx, cy + dy * sy, "teal", 1, 0.05)
    # the bell, rattling in a gap of the spines (front, low)
    if not ball and curl < 0.6:
        r.stamp(SMALL_BELL, x + 1 + bell, cy + 0.5, 1.5, BELL, pivot=(2, 2))
    if eyes and curl < 0.6:
        eye(r, x + 2.5, cy - 2.5, 1.6); eye(r, x - 0.5, cy - 3, 1.6)
        if hurt: r.dot(x + 2.5, cy - 2.5, "lure", 1, 1.7)
    # front spines
    spines(r, x, cy, rx, ry, 20, L, "urch", 1.0, phase=math.radians(rot), skip_down=not ball, front=True, tips=2)
    if ball:
        # rolled up: bone tips everywhere, the bell hidden
        for i in range(10):
            a = math.radians(rot * 1.5 + i * 36)
            r.dot(x + math.cos(a) * (rx + 1), cy + math.sin(a) * (ry + 1), "ivory", 3, 1.2)
    if foam is not None: foam_ring(r, x, -0.5, 9, 2.2, foam, z=-2.0, n=20)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def urchin_corpse(stage):
    r = Rig()
    cy = -3.5
    spines(r, 0, cy, 5.6, 3.0, 12, 3.0 - stage, "urch", -1.0, phase=0.3, front=False, skip_down=True)
    r.ell(0, cy, 5.6, 3.0, "teal", 0.0, bias=-0.15)
    r.stamp(SMALL_BELL, 6 + stage, -2, 1.5, BELL, pivot=(2, 4))
    spines(r, 0, cy, 5.6, 3.0, 12, 3.0 - stage, "urch", 1.0, phase=0.6, front=True, skip_down=True, tone=1)
    for i in range(5): r.dot(-4 + i * 2, -0.3, "pouch", 2, 0.5)
    if stage == 0: dust(r, 0, 0, 1)
    return r.resolve()


def urchin_sheet(out):
    U = urchin
    idle = [U(rot=[0, 4, 8, 4][i], bob=[0, -0.3, -0.5, -0.3][i], bell=[0, 0.4, 0, -0.4][i], feet=i) for i in range(4)]
    run = [U(rot=-12 * i, bob=[0, -0.6, -1.0, -0.6, 0, -0.3][i], bell=[0, 0.6, 0.8, 0, -0.6, -0.4][i], feet=i, x=0.4,
             sx=[1.0, 1.02, 0.98, 1.0, 1.02, 0.98][i]) for i in range(6)]
    grip = [U(rot=[0, 2, 4, 2][i], bob=0.3, grip=True, foam=i, bell=[0, 0.3, 0, -0.3][i]) for i in range(4)]
    # Roll (7): crouch and fold the spines (0-1), ROLL (2-5, spinning ball with a sand trail), uncurl (6)
    roll = [U(bob=0.6, sy=0.9, curl=0.4, bell=-0.5),
            U(bob=0.8, sy=0.85, sx=1.06, curl=0.8, eyes=False),
            U(ball=True, rot=0, curl=1, x=1.0, smear=[((-6, -4), (-9, -4), "urch", 2), ((-6, -8), (-8, -9), "urch", 1)],
              extra=lambda r: dust(r, -5, 0, 0)),
            U(ball=True, rot=60, curl=1, x=1.5, smear=[((-6, -5), (-10, -5), "urch", 2), ((-6, -9), (-9, -10), "urch", 1)]),
            U(ball=True, rot=120, curl=1, x=1.5, smear=[((-6, -4), (-10, -4), "urch", 2)], extra=lambda r: dust(r, -6, 0, 1)),
            U(ball=True, rot=180, curl=1, x=1.0),
            U(bob=0.3, curl=0.3, feet=1, bell=0.8)]
    # Bristle (6): draw the spines in (0-1), swell (2), FIRE them out in a ring (3), recoil (4), settle (5)
    ring = lambda r: [r.dot(math.cos(a) * 10, -6 + math.sin(a) * 8, "ivory", 4, 4) for a in [i * math.tau / 8 for i in range(8)]]
    bristle = [U(curl=0.3, sy=0.95, bob=0.3), U(curl=0.6, sx=0.92, sy=0.9, bob=0.5, bell=0.6),
               U(curl=0.0, sx=1.12, sy=1.1, ln=3.0, bob=-0.5, bell=-0.6),
               U(ln=6.5, sx=1.08, sy=1.05, bob=-0.6, extra=ring),
               U(ln=5.0, bob=-0.3, rot=8), U(ln=4.0, rot=4)]
    d0 = U(hurt=True, bob=-0.5, rot=-10, sx=1.05, sy=0.92)
    d1 = U(hurt=True, curl=0.5, bob=0.5, sy=0.8, sx=1.1, eyes=False, bell=1.5)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6), ("IdleGrip", grip, [0.14] * 4),
             ("Roll", roll, [0.14, 0.12, 0.06, 0.06, 0.06, 0.06, 0.16]),
             ("Bristle", bristle, [0.14, 0.14, 0.18, 0.06, 0.12, 0.16])]
    anims += tail_anims(idle[0], [d0, d1, urchin_corpse(0), urchin_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        U(hurt=True, rot=-14, sx=1.06, sy=0.9, bob=-0.6))
    return sheet("BelUrchin", anims, out)


# ================================================================== LUREFISH
LURE_LEG = legend(k="bruise:0", d="bruise:1", b="bruise:2", B="bruise:3", W="ivory:3", w="ivory:2", e="lure:3",
                  m="bruise:0", p="coral:1")


def lurefish(bob=0.0, jaw=0.0, lean=0.0, lit=0, lure=None, stride=0.0, lunge=0.0, tail=0.0, smear=None, hurt=False,
             line_to=None, extra=None, eye_open=True):
    """Anglerfish on stubby fin legs: a big round head with a huge underbite, the lure arcing on its stalk.
    lit 0..3 = how bright the lure is (Bright Bait); lure = (x, y) of the bulb (else at rest over the jaw)."""
    r = Rig()
    x0 = lunge
    T = Xf(lean, (x0, -4.0))
    hx, hy = T(x0 + 2.0, -6.5 + bob)
    # tail and tail fin
    tp = [T(x0 - 2.5, -6.0 + bob), T(x0 - 5.0, -6.5 + bob + tail * 0.4), T(x0 - 6.5, -7.0 + bob + tail)]
    r.tube(tp, [2.6, 1.6, 0.8], "bruise", -0.5, bias=-0.05)
    tx, ty = tp[-1]
    fin(r, [(tx, ty), (tx - 2.5, ty - 3.0 + tail), (tx - 1.5, ty), (tx - 2.5, ty + 2.5 + tail)], "bruise", -0.6, bias=0.1)
    # dorsal ridge
    for i in range(4): r.dot(*T(x0 - 2.0 - i * 1.3, -9.3 + bob + i * 0.4), "bruise", 2, 0.4)
    # fin legs (two stubby pectoral fins as feet)
    for k, (bx, ph) in enumerate(((-0.5, 0.0), (2.5, 0.5))):
        s = math.sin((stride + ph) * math.tau)
        hip = T(x0 + bx, -3.5 + bob)
        foot = (x0 + bx + s * 1.5, 0.0 - max(0.0, math.cos((stride + ph) * math.tau)) * (1.0 if stride else 0.0))
        r.tube([hip, foot], [1.0, 0.8], "bruise", 0.5 if k else -0.3, bias=-0.2 if not k else 0.0)
        r.dot(foot[0] + 1, foot[1], "bruise", 3 if k else 1, 0.6)
    # head: a fat round skull with the lower jaw jutting out under it
    r.ell(hx, hy, 5.4, 4.8, "bruise", 0.0)
    r.ell(hx - 0.5, hy + 2.6, 4.0, 1.6, "hag", 0.05, bias=-0.1)                      # pale belly
    ja = jaw * 30.0
    J = Xf(ja + lean, (hx - 1.0, hy + 1.5))
    jaw_pts = [J(hx - 2.0, hy + 1.0), J(hx + 7.5, hy - 0.5), J(hx + 7.0, hy + 2.0), J(hx + 2.0, hy + 4.2), J(hx - 2.5, hy + 3.5)]
    r.poly(jaw_pts, "bruise", 1.0, normal=(0.0, 0.3, 1.0), bias=0.05)
    # teeth: lower fangs stand up out of the underbite, upper ones hang
    for i in range(4):
        bx, by = J(hx + 2.5 + i * 1.4, hy + 0.2)
        r.dot(bx, by - 1, "ivory", 3, 1.2)
        if i % 2 == 0: r.dot(bx, by - 2, "ivory", 4 if i == 0 else 3, 1.2)
    # the mouth line under the brow, upper fangs hanging from it
    ma, mb = T(hx + 1.0, hy + 0.4 + jaw * 0.5), T(hx + 5.4, hy - 0.3 + jaw * 0.5)
    r.line(*ma, *mb, "bruise", 1.05, tone=0)
    for i in range(3):
        ux, uy = T(hx + 2.5 + i * 1.5, hy + 0.9 + jaw * 2.0)
        r.dot(ux, uy, "ivory", 2 if jaw < 0.25 else 3, 1.1)
    if jaw > 0.25:
        mx, my = T(hx + 3.5, hy + 1.2 + jaw)
        r.ell(mx, my, 2.4, jaw * 1.6, "coral", 0.9, flat=1)
    # eye: a small cyan bead high on the head
    if eye_open: eye(r, *T(hx + 1.5, hy - 2.5), 1.3, big=True)
    else: r.dot(*T(hx + 1.5, hy - 2.5), "bruise", 0, 1.3)
    # the lure: a stalk from the brow arcing forward, the bulb glowing
    sx, sy = T(hx + 0.5, hy - 4.0)
    bx, by = lure if lure else T(hx + 6.5, hy - 6.5 + bob * 0.5)
    mx, my = (sx + bx) / 2 - 1.0, min(sy, by) - 3.0
    pts = [(sx, sy)] + [((1 - t) ** 2 * sx + 2 * (1 - t) * t * mx + t * t * bx, (1 - t) ** 2 * sy + 2 * (1 - t) * t * my + t * t * by)
                        for t in (0.25, 0.5, 0.75, 1.0)]
    r.polyline(pts, "bruise", 2.0, tones=[2, 3, 3, 2])
    if lit >= 2:
        for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)): r.dot(bx + dx, by + dy, "lurey", 2 if lit == 2 else 3, 2.4)
    if lit >= 3:
        for (dx, dy) in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (1, -1), (-1, 1)): r.dot(bx + dx, by + dy, "lurey", 1, 2.3)
    r.dot(bx, by, "lurey", 3 + (1 if lit >= 1 else 0), 2.5)
    if lit >= 1: r.dot(bx + 1, by, "lurey", 2 + (1 if lit >= 2 else 0), 2.45)
    if lit >= 1:
        # the light cone on the floor under the lure grows with each step
        w = 1.0 + lit * 1.2
        for i in range(int(w * 2) + 1):
            if i % 2 and lit < 3: continue
            r.dot(bx - w + i, 0, "lurey", 1 if abs(i - w) > w * 0.5 else 2, -3.0)
    if line_to:
        r.line(bx, by, line_to[0], line_to[1], "lurey", 2.2, tone=2)
    if hurt: r.dot(*T(hx + 1.5, hy - 2.5), "bruise", 4, 1.4)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.0, tone=t)
    if extra: extra(r)
    return r.resolve()


def lure_corpse(stage):
    r = Rig()
    # belly up: the jaw hangs open, the lure flops on the floor
    r.tube([(-7.0, -2.0), (-3.0, -2.5), (1.0, -3.0)], [1.0, 2.0, 2.4], "bruise", -0.5, bias=-0.2)
    r.ell(2.5, -3.2, 4.8, 3.2, "bruise", 0.0, bias=-0.1)
    r.poly([(1, -1), (9, -2), (8, 0), (2, 0)], "bruise", 1.0, bias=-0.1)
    for i in range(3): r.dot(4 + i * 1.5, -2.5, "ivory", 3, 1.2)
    r.dot(3.5, -5.0, "bruise", 0, 1.3); r.dot(4.5, -5.0, "bruise", 0, 1.3)
    r.polyline([(1, -6), (-1, -7), (-4, -6), (-6, -4)], "bruise", 2.0, tone=2)
    r.dot(-6, -3, "lurey", 2 if stage else 3, 2.1)
    fin(r, [(-7, -2), (-10, -5), (-9, -2), (-10, 0)], "bruise", -0.6)
    return r.resolve()


def lure_sheet(out):
    Lf = lurefish
    sets = []
    for lit in range(4):
        idle = [Lf(bob=[0, -0.3, -0.5, -0.3][i], tail=[0, 1, 2, 1][i], lit=lit) for i in range(4)]
        run = [Lf(bob=[0, -0.7, -1.0, -0.4, 0, -0.5][i], stride=i / 6.0, tail=[-1, 0, 2, 1, -1, 0][i], lean=-4, lit=lit)
               for i in range(6)]
        sets.append((idle, run))
    idle, run = sets[0]
    # Chomp (6): rear back, jaws open (0-1), LUNGE (2, smear), SNAP shut (3: the bite), hold (4), recover (5)
    chomp = [Lf(lean=-10, jaw=0.4, bob=-0.5, lunge=-1.0), Lf(lean=-14, jaw=1.0, bob=-0.8, lunge=-1.5),
             Lf(lean=8, jaw=1.1, lunge=3.0, smear=[((-6, -10), (-2, -10), "bruise", 2), ((-6, -4), (-1, -4), "bruise", 1)]),
             Lf(lean=10, jaw=0.0, lunge=4.0, extra=lambda r: star(r, 13.5, -6.0, 1)),
             Lf(lean=6, jaw=0.1, lunge=3.0), Lf(lean=0, jaw=0.2, lunge=1.0)]
    # Lure (8): swing the lure back (0-1), CAST it forward (2), the tug (3-5: a yellow line to the hero, the bulb
    # blazing, the head bowed), jaws open (5), BITE (6), recover (7)
    lure = [Lf(lean=-6, lure=(-3.0, -15.0), lit=2), Lf(lean=-10, lure=(-6.0, -13.0), lit=2, jaw=0.2),
            Lf(lean=6, lure=(14.0, -11.0), lit=3, smear=[((0, -16), (10, -14), "lurey", 1)]),
            Lf(lean=4, lure=(16.0, -7.0), lit=3, line_to=(21.0, -5.0)),
            Lf(lean=2, lure=(13.0, -8.0), lit=3, line_to=(19.0, -5.0), jaw=0.3),
            Lf(lean=0, lure=(10.0, -10.0), lit=2, jaw=1.0),
            Lf(lean=10, lit=1, jaw=0.0, lunge=2.5, extra=lambda r: star(r, 12.5, -6.0, 1)),
            Lf(lean=2, lit=0, jaw=0.2)]
    d0 = Lf(hurt=True, lean=-16, jaw=0.8, bob=-1.0)
    d1 = Lf(hurt=True, lean=-35, jaw=1.0, bob=0.5, eye_open=False)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Chomp", chomp, [0.14, 0.12, 0.06, 0.06, 0.1, 0.14]),
             ("Lure", lure, [0.12, 0.12, 0.08, 0.12, 0.12, 0.1, 0.06, 0.16])]
    for lit in (1, 2, 3):
        anims += [("IdleLit%d" % lit, sets[lit][0], [0.16, 0.14, 0.16, 0.14]), ("RunLit%d" % lit, sets[lit][1], [0.08] * 6)]
    anims += tail_anims(idle[0], [d0, d1, lure_corpse(0), lure_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        Lf(hurt=True, lean=-18, jaw=0.6, bob=-1.0))
    return sheet("BelLurefish", anims, out)


# ================================================================== BARNACLE CRAB
def crab(bob=0.0, phase=0.0, claw_at=None, claw_open=0.3, tilt=-70.0, small_at=None, sideways=False, hunker=0.0, plate=False,
         hurt=False, kick=None, smear=None, extra=None, lean=0.0, eyes=True, glint=False):
    """Squat barnacled crab, one huge claw held high (coral tip). hunker 0..1 sinks it into its shell."""
    r = Rig()
    cy = -5.0 + bob + hunker * 2.2
    hw = 5.4
    crab_legs(r, -2.2, cy + 0.5, hw, 3, phase, "teal", 1.5, -1.5, step=1.4, sideways=sideways, reach=2.2, lift=1.2,
              tuck=hunker, knee=2.6, spread=1.5)
    # small far claw
    sx, sy = small_at or (-6.5, cy - 0.5 + hunker)
    r.line(-4.5, cy + 0.5, sx + 1.0, sy + 0.5, "teal", -1.0, tone=1)
    r.ell(sx, sy, 1.6, 1.1, "barn", -0.9, bias=-0.3)
    r.dot(sx - 1.5, sy - 0.5, "coral", 1, -0.85)
    # carapace: a wide flat dome, crusted with barnacles
    r.ell(-2.5, cy, hw, 3.4 - hunker * 0.4, "barn", 0.0, ang=lean)
    r.ell(-2.5, cy + 1.8, hw - 1.2, 1.0, "teal", 0.1, bias=-0.15)
    barnacles(r, [(-4, cy - 2.2), (-1, cy - 3.0), (2, cy - 2.4), (-6, cy - 0.6)], 0.3)
    if plate:
        r.ell(-1.0, cy - 2.4, 4.4, 1.6, "barn", 0.4, bias=0.3)
        barnacles(r, [(-3, cy - 3.4), (0, cy - 3.9), (2, cy - 3.1)], 0.5)
    if glint: star(r, -2.0, cy - 5.0, 1)
    # eye stalks
    if eyes and hunker < 0.7:
        for ex in (1.5, 3.5):
            r.line(ex, cy - 2.5, ex, cy - 4.0, "barn", 0.6, tone=3)
            eye(r, ex, cy - 4.5, 0.7)
        if hurt: r.dot(3.5, cy - 4.5, "barn", 4, 0.8)
    # big claw on the near side, held high: a fat palm and two coral-tipped fingers
    bx, by = claw_at or (7.0, cy - 3.0 + hunker * 2.5)
    sh = (3.5, cy + 0.8)
    el = ik(sh[0], sh[1], bx - 0.5, by + 1.6, 3.2, 3.2, bend=-1)
    r.tube([sh, el, (bx - 0.5, by + 1.6)], [1.0, 0.9, 1.1], "teal", 1.8)
    r.dot(*el, "teal", 4, 1.85)
    T = Xf(tilt, (bx, by))
    r.ell(bx, by, 3.7, 2.9, "barn", 2.2, ang=tilt, bias=0.3)
    barnacles(r, [T(bx - 1.2, by - 1.2)], 2.25)
    o = claw_open
    up = [T(bx + 2.5, by - 1.2), T(bx + 5.0, by - 2.5 - o * 1.8), T(bx + 6.5, by - 1.8 - o * 2.6)]
    lo = [T(bx + 2.5, by + 1.2), T(bx + 4.8, by + 1.0 + o * 1.4), T(bx + 5.8, by - 0.4 + o * 2.4)]
    r.tube(up, [1.5, 1.1, 0.6], "coral", 2.3, bias=0.15)
    r.tube(lo, [1.2, 0.9, 0.5], "coral", 2.32, bias=-0.1)
    r.dot(*up[-1], "coral", 4, 2.35)
    if kick:
        for (kx, kk) in kick: dust(r, kx, 0, kk, 0.7)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def crab_corpse(stage):
    r = Rig()
    crab_legs(r, 0.0, -2.0, 6.4, 3, 0.2, "teal", -1.0, -1.5, step=0.0, reach=4.0, lift=0.0, knee=1.5)
    r.ell(0, -3.0, 7.0, 3.0, "barn", 0.0, ang=8 if stage else 4, bias=-0.15)
    barnacles(r, [(-4, -5), (-1, -5.5), (3, -5)], 0.3)
    claw(r, 9.0, -2.0, 10, 2.2, "barn", 0.5, open_=0.8, tip="coral", bias=-0.1)
    for ex in (2, 4): r.dot(ex, -6, "barn", 1, 0.6)
    if stage == 0: dust(r, 0, 0, 1)
    return r.resolve()


def crab_sheet(out):
    C = crab
    idle = [C(bob=[0, -0.3, -0.5, -0.3][i], phase=0.0, claw_open=[0.3, 0.5, 0.7, 0.5][i],
              claw_at=(5.0, -6.5 + [0, -0.4, -0.8, -0.4][i])) for i in range(4)]
    run = [C(bob=[0, -0.4, 0, -0.4, 0, -0.4][i], phase=i / 6.0, claw_open=0.3) for i in range(6)]
    # Sidle: the legs blur sideways and kick sand out both sides
    side = [C(bob=[0, -0.5, 0, -0.5, 0, -0.5][i], phase=i / 3.0, sideways=True, claw_open=0.4,
              kick=[(-9, i % 3), (9, (i + 1) % 3)]) for i in range(6)]
    # Pinch (6): raise the claw (0-1), SNAP it down and shut (3), hold (4), lift (5)
    pinch = [C(claw_at=(6.5, -10.0), claw_open=0.8, tilt=-95, lean=-4),
             C(claw_at=(6.0, -11.0), claw_open=1.0, tilt=-110, lean=-8, bob=-0.5),
             C(claw_at=(9.0, -7.0), claw_open=0.9, tilt=-30, lean=6, smear=[((7, -15), (12, -11), "barn", 2)]),
             C(claw_at=(9.5, -4.5), claw_open=0.0, tilt=5, lean=8, extra=lambda r: star(r, 15.0, -5.0, 1)),
             C(claw_at=(9.0, -5.0), claw_open=0.1, tilt=0, lean=6), C(claw_at=(8.0, -7.0), claw_open=0.4, tilt=-50)]
    # Shell (7): tuck down (0-2), hunkered: a barnacle plate crusts over it, glinting (3-5), rise (6)
    shell = [C(hunker=0.4), C(hunker=0.8, claw_open=0.0), C(hunker=1.0, claw_open=0.0, eyes=False),
             C(hunker=1.0, plate=True, eyes=False, glint=True), C(hunker=1.0, plate=True, eyes=False),
             C(hunker=0.9, plate=True, eyes=False), C(hunker=0.3, plate=True, claw_open=0.5)]
    d0 = C(hurt=True, lean=-10, claw_open=1.0, bob=-0.5)
    d1 = C(hurt=True, lean=12, hunker=0.5, claw_open=1.0, claw_at=(8.0, -3.0), tilt=10)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6), ("Sidle", side, [0.06] * 6),
             ("Pinch", pinch, [0.14, 0.12, 0.06, 0.06, 0.12, 0.14]),
             ("Shell", shell, [0.1, 0.1, 0.1, 0.16, 0.16, 0.14, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, crab_corpse(0), crab_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        C(hurt=True, lean=-14, claw_open=0.9, bob=-0.8))
    return sheet("BelCrab", anims, out)


JOBS = [("BelUrchin", urchin_sheet), ("BelLurefish", lure_sheet), ("BelCrab", crab_sheet)]
SYNC = {
    "BelUrchin": {"Roll": [("roll starts: move 150 px/s, contact hitbox on (ball 12 x 12 at (1, -6))", 2), ("roll ends", 6)],
                  "Bristle": [("RELEASE: 8 spines out from (0, -6)", 3)]},
    "BelLurefish": {"Chomp": [("lunge", 2), ("SNAP: jaws at (12, -6); box 12 x 10 at (10, -6)", 3)],
                    "Lure": [("cast: the lure flies out", 2), ("tug: pull the hero in (3-5)", 3), ("BITE at (12, -6)", 6)]},
    "BelCrab": {"Pinch": [("SNAP: claw shuts at (13, -6); box 12 x 10 at (10, -6)", 3)],
                "Shell": [("hunkered: invulnerable from here", 2), ("the plate crusts over", 3), ("rises: invulnerable off", 6)]},
}
NOTES = {
    "BelUrchin": "IdleGrip (4): the tube feet splayed with a foam ring: the idle while it stands in brine (Tube Feet).",
    "BelLurefish": "IdleLit1-3 / RunLit1-3: the lure at each Bright Bait step (the bulb grows, a light cone on the floor).",
    "BelCrab": "Sidle (6): the run played while it moves sideways (mostly up or down the screen relative to its facing).",
}
