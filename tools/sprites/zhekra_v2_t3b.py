"""Zhekra tier 3, second half: Blood Gorger, Botfly Matron, Chitin Colossus, Glue Mortar, Stag Titan, Sun Scarab. Built
through zhekra_v2_rigs.py. Same renderer and rules as the lower tiers. T3 idle limit 42 x 40, and never a smaller
footprint than the v1 sheet it replaces."""
import math, random
from zhekra_v2_rigs import (ZRig, Rig, Xf, chain, ik, lerp, segs, leg, gait6, legs6, antenna, wing, wing_blur, eye, mandible,
                            drip, puddle, dust, smear, splat, ground_shadow, arc_pts, sheet, tail_anims, SYNC, NOTES)
from zhekra_v2_t1 import banded
from zhekra_v2_t2 import walk_feet, amber_ball


# ================================================================== BLOOD GORGER: a blood sac on stilt legs with a drill
def gorger(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, level=0, pump=0.0, nose=0.0, reach=0.0, spin=0, hurt=False,
           dead=False, extra=None, dust_at=None, sag=0.0):
    r = ZRig(1.32)
    T = Xf(lean, (0.0, -20.0))
    k = 0.25 + 0.75 * level / 3.0
    body_y = -21.0 + bob + sag + k * 1.5
    # six stilt legs, jointed high
    hips = [T(-1.0 + dx, body_y + 3.0) for dx in (2.0, 0.0, -2.0, 2.6, 0.6, -1.4)]
    base = [(9.0, 0.0), (2.0, 0.0), (-9.0, 0.0), (12.0, 0.0), (4.0, 0.0), (-6.0, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=2.0) if stride else list(base)
    if dead: feet = [(h[0] + [6, 1, -6, 7, 2, -5][kk], h[1] + 3.0) for kk, h in enumerate(hips)]
    for kk in range(6):
        near = kk < 3
        leg(r, hips[kk], feet[kk], 12.0, 13.0, 1.0 if near else -2.0, "fuzz" if near else "dchit",
            near=near, bend=1 if kk % 3 == 0 else -1, rad=0.95 if near else 0.75)
    # the sac: blood showing through, its level visible as a line
    sc = T(-4.0, body_y - 1.0)
    R = 6.9 + 1.6 * k + pump * 0.6
    r.ell(sc[0], sc[1], R * 1.15, R, "skin", 0.0, bias=0.1)
    lvl = sc[1] + R * (0.8 - 1.4 * k) - 0.5
    kk_ = r.k
    r.ell(sc[0], sc[1], R * 1.15 - 0.6, R - 0.6, "blood", 0.01, bias=-0.1, clip=lambda x, y: y >= lvl * kk_)
    r.line(sc[0] - R * 0.9, lvl, sc[0] + R * 0.9, lvl, "blood", 0.015, tone=3) if 0 < k < 1 else None
    r.dot(sc[0] - R * 0.5, sc[1] - R * 0.55, "skin", 4, 0.02); r.dot(sc[0] - R * 0.35, sc[1] - R * 0.65, "skin", 4, 0.02)
    for a in (-40, 20, 80):
        aa = math.radians(a)
        r.line(sc[0] + R * 0.4 * math.cos(aa), sc[1] + R * 0.4 * math.sin(aa), sc[0] + R * 1.0 * math.cos(aa + 0.3),
               sc[1] + R * 0.9 * math.sin(aa + 0.3), "blood", 0.03, tone=1)
    # small head with the drill proboscis
    hx, hy = T(5.0, body_y - 0.5)
    r.ell(hx - 1.0, hy, 3.0, 2.6, "fuzz", 0.3, bias=0.1)
    eye(r, hx - 0.2, hy - 0.8, 0.35, glint=not dead, big=True)
    if hurt and not dead: r.dot(hx - 0.2, hy - 0.8, "white", 2, 0.36)
    na = 25 + nose
    L = 8.0 + reach
    tip = chain(hx + 1.6, hy + 1.0, [(L, na)])[-1]
    r.tube([(hx + 1.6, hy + 1.0), tip], [1.4, 0.4], "bronze", 0.34)
    for j in range(3):
        t = (j + 1 + spin * 0.5) / 4.0
        r.dot(lerp(hx + 1.6, tip[0], t), lerp(hy + 1.0, tip[1], t), "bronze", 4 if (j + spin) % 2 else 1, 0.341)
    r.dot(tip[0], tip[1], "white", 3, 0.342)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, (hx, hy), tip, sc)
    return r.resolve()


def gorger_sheet(outdir):
    G = gorger
    anims = []
    for lv, sfx in ((0, ""), (1, "1"), (2, "2"), (3, "3")):
        idle = [G(level=lv, bob=[0, 0.4, 0.8, 0.4][i], pump=[0, 0.3, 0.6, 0.3][i], nose=[0, 2, 4, 2][i]) for i in range(4)]
        run = [G(level=lv, i=i, n=6, stride=3.0, bob=0.8 * abs(math.sin(i / 6 * math.tau)), lean=3, nose=5) for i in range(6)]
        anims += [("Idle" + sfx, idle, [0.16, 0.14, 0.16, 0.14]), ("Run" + sfx, run, [0.08] * 6)]
    # Drill: rear up (0, 1), PLUNGE (2), the drill spins in (3, 4), pull out (5, 6)
    dr = [G(lean=-5, nose=-15, reach=-1), G(lean=-10, nose=-25, reach=-2, bob=-1.0), G(lean=8, nose=30, reach=4, spin=0, bob=1.0),
          G(lean=10, nose=32, reach=5, spin=1, bob=1.2), G(lean=10, nose=32, reach=5, spin=2, bob=1.2), G(lean=4, nose=15, reach=1), G()]
    # Pump: the proboscis plunges into a kin (0, 1), the sac pumps (2-5 loop), withdraw (6)
    pump = [G(level=2, lean=6, nose=40, reach=3), G(level=2, lean=8, nose=50, reach=5, bob=1.0)]
    pump += [G(level=2 - (kk % 2), lean=8, nose=50, reach=5, bob=1.0, pump=[1.0, 0.0][kk % 2], sag=[0.5, 0.0][kk % 2]) for kk in range(4)]
    pump += [G(level=1, nose=10)]
    anims += [("Drill", dr, [0.12, 0.12, 0.05, 0.08, 0.08, 0.1, 0.12]), ("Pump", pump, [0.1, 0.1, 0.12, 0.12, 0.12, 0.12, 0.12])]
    idle0 = anims[0][1][0]
    d = [G(level=2, hurt=True, lean=-8, nose=-20), G(level=2, hurt=True, lean=-14, bob=3.0, nose=-10),
         G(level=0, dead=True, lean=6, bob=13.0, nose=10, dust_at=(0, 0, 0), extra=lambda r, h, t, s: splat(r, s[0], s[1], 0, 3.0, mat="blood", n=8, spread=8)),
         G(level=0, dead=True, lean=8, bob=15.0, nose=12, extra=lambda r, h, t, s: puddle(r, -4.0, 8.0, -3.0, mat="blood"))]
    knock = G(level=1, hurt=True, lean=-10, nose=-25, bob=-1.0)
    anims += tail_anims(idle0, d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkGorger", anims, outdir, scale=5)


SYNC["ZhkGorger"] = {"Drill": [("PLUNGE: drill tip at (20, -11); box 16 x 14 at (17, -11)", 2)],
                     "Pump": [("the pump starts: FxZhkPump beads run to the ally", 2)]}
NOTES["ZhkGorger"] = "Blood Bank: Idle/Run (empty) .. Idle3/Run3 (full sac). Pump loops frames 2-5 while it transfuses."


# ================================================================== BOTFLY MATRON: a fat furry fly with an ovipositor
def botfly(alt=6.0, tilt=0.0, curl=0.0, wing_a=-120.0, blur=1, hurt=False, dead=False, legs=0.0, extra=None, shadow=True,
           x=0.0, streak=0, fold=0.0, ovi=0.0, jaw=0.0, egg=False):
    r = ZRig(1.12)
    if shadow: ground_shadow(r, x, 6.0)
    wx, wy = x - 1.0, -alt - 9.0
    T = Xf(tilt, (wx, wy)); C = Xf(-curl, (wx, wy))
    rnd = random.Random(11)
    fur = lambda xx, yy: "fuzz" if (int(xx * 7 + yy * 13) % 5) else "cream"
    # legs
    for k, dx in enumerate((-2.0, 0.5, 3.0)):
        hip = T(wx + 2.0 + dx, wy + 4.0)
        foot = (hip[0] - 1.5 + legs * (k - 1) - fold * 2 + k, hip[1] + 4.0 - fold)
        leg(r, hip, foot, 2.6, 2.8, 0.4 if k != 1 else -0.2, "fuzz" if k != 1 else "dchit", near=k != 1, bend=-1, rad=0.5)
    # the fat round abdomen (fuzzy) with the ovipositor curling under it
    ab = T(*C(wx - 5.0, wy + 1.5))
    r.ell(ab[0], ab[1], 7.4, 6.3, "fuzz", 0.1, bias=0.1)
    for k in range(18):
        a = rnd.uniform(0, math.tau); d = rnd.uniform(0.3, 0.95)
        r.dot(ab[0] + 7.0 * d * math.cos(a), ab[1] + 6.0 * d * math.sin(a), "fuzz" if k % 3 else "cream", 4 if k % 2 else 1, 0.11)
    for k in range(3):
        r.line(ab[0] - 4 + k * 3, ab[1] - 5.4, ab[0] - 4.8 + k * 3, ab[1] + 5.0, "fuzz", 0.105, tone=1)
    oa = 150 - ovi * 120
    ov = chain(ab[0] - 5.0, ab[1] + 2.0, [(3.0, oa), (3.0, oa - 30 * (1 + ovi)), (2.5, oa - 60 * (1 + ovi))])
    r.tube(ov, [1.0, 0.8, 0.6, 0.4], "chit", 0.12)
    r.dot(ov[-1][0], ov[-1][1], "glue", 4, 0.13)
    if egg: r.ell(ov[-1][0], ov[-1][1], 1.2, 1.5, "glue", 0.14, flat=3)
    # wings: smoky, broad
    root = T(wx + 1.5, wy - 3.6)
    wa = wing_a + fold * 60
    wing(r, root, wa - 12, 12.0 - fold * 3, 5.0, -0.6, near=False)
    wing(r, (root[0] + 1.0, root[1] + 0.3), wa + 8, 11.0 - fold * 3, 4.6, 0.6, near=True)
    if blur: wing_blur(r, root, wa + 45, wa + 75, 10.0, -0.7, n=2)
    th = T(wx + 2.4, wy)
    r.ell(th[0], th[1], 4.4, 4.0, "fuzz", 0.2, bias=0.12)
    for k in range(10):
        a = rnd.uniform(0, math.tau); d = rnd.uniform(0.3, 0.9)
        r.dot(th[0] + 4.4 * d * math.cos(a), th[1] + 4.0 * d * math.sin(a), "fuzz", 4 if k % 2 else 1, 0.21)
    # the pale grub-white face
    hd = T(wx + 7.2, wy + 0.6)
    r.ell(hd[0], hd[1], 3.0, 3.0, "cream", 0.3, bias=0.1)
    eye(r, hd[0] + 0.2, hd[1] - 1.2, 0.32, glow="blood" if False else None, glint=not dead, big=True)
    r.ell(hd[0] - 0.4, hd[1] - 1.4, 1.6, 1.4, "blood", 0.31, bias=0.2)
    r.dot(hd[0] - 0.8, hd[1] - 2.0, "white", 3, 0.315)
    if hurt and not dead: r.dot(hd[0] - 0.6, hd[1] - 1.6, "white", 4, 0.33)
    r.ell(hd[0] + 1.6 + jaw, hd[1] + 1.4, 1.2, 1.0, "cream", 0.34, bias=-0.1)
    antenna(r, (hd[0] + 1.0, hd[1] - 2.6), -50, 3.0, 30, 0.29)
    if streak:
        for k in range(streak): smear(r, [(hd[0] - 16 - 3 * k, hd[1] + k), (hd[0] - 12 - 3 * k, hd[1] + k)], "wblur", 2, -1.0)
    if extra: extra(r, hd, ov[-1])
    return r.resolve()


def botfly_sheet(outdir):
    B = botfly
    idle = [B(alt=[4.0, 4.5, 5.0, 4.5][i], wing_a=[-145, -100, -135, -95][i], legs=[0, 0.5, 1, 0.5][i], ovi=[0, 0.05, 0.1, 0.05][i]) for i in range(4)]
    run = [B(alt=4.5 + 0.6 * math.sin(i / 6 * math.tau), tilt=10, wing_a=[-145, -100, -135, -95, -140, -105][i], legs=1.0,
             streak=1 if i % 2 else 0) for i in range(6)]
    # Ram: pull back (0, 1), CHARGE head first (2), hit (3), bounce off (4, 5)
    ram = [B(alt=5, tilt=-10, x=-1.0), B(alt=5.5, tilt=-16, x=-2.0, jaw=0.5), B(alt=4.5, tilt=18, x=4.0, streak=2, jaw=1.0),
           B(alt=4.5, tilt=20, x=5.0, jaw=1.0, extra=lambda r, h, o: r.dot(h[0] + 4, h[1] - 1, "white", 4, 3.0)),
           B(alt=5.5, tilt=-6, x=2.0), B(alt=5.0)]
    # EggDart: the ovipositor swings forward under (0-3), FIRE the egg dart (4), recoil (5, 6)
    ed = [B(alt=5, ovi=0.3), B(alt=5.5, ovi=0.6, tilt=-6, egg=True), B(alt=6.0, ovi=0.9, tilt=-10, egg=True), B(alt=6.0, ovi=1.0, tilt=-12, egg=True),
          B(alt=6.0, ovi=1.0, tilt=-10, extra=lambda r, h, o: r.dot(o[0] + 2, o[1], "white", 4, 3.0)), B(alt=5.5, ovi=0.5, tilt=4), B(alt=5.0, ovi=0.1)]
    d = [B(alt=5, tilt=-30, blur=0, wing_a=-165, hurt=True), B(alt=3, tilt=-45, blur=0, wing_a=-178, hurt=True, fold=0.4),
         B(alt=-3.0, tilt=10, blur=0, wing_a=175, dead=True, fold=1.0, shadow=False, extra=lambda r, h, o: dust(r, 0, 0, 0)),
         B(alt=-3.5, tilt=12, blur=0, wing_a=178, dead=True, fold=1.0, shadow=False)]
    knock = B(alt=6, tilt=-28, blur=0, wing_a=-165, hurt=True)
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6), ("Ram", ram, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("EggDart", ed, [0.12, 0.1, 0.1, 0.1, 0.06, 0.1, 0.12])]
    anims += tail_anims(idle[0], d, [0.08, 0.1, 0.12, 0.4], knock)
    return sheet("ZhkBotfly", anims, outdir, scale=5)


SYNC["ZhkBotfly"] = {"Ram": [("RAM: head at (14, -12); box 14 x 16 at (12, -11)", 2)],
                     "EggDart": [("FIRE: the egg dart leaves the ovipositor at (2, -7)", 4)]}


# ================================================================== CHITIN COLOSSUS: a rhinoceros termite with a ram plate
def colossus(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, head=0.0, horn=0.0, crouch=0.0, hurt=False, dead=False,
             extra=None, dust_at=None, gleam=False, resin=False):
    r = ZRig(1.16)
    T = Xf(lean, (2.0, -8.0))
    c = crouch
    hips = [T(3.0, -6.0 + bob + c), T(-2.0, -6.0 + bob + c), T(-7.0, -5.5 + bob), T(4.0, -6.5 + bob + c), T(-1.0, -6.5 + bob + c), T(-6.0, -6.0 + bob)]
    base = [(9.0, 0.0), (0.0, 0.0), (-11.0, 0.0), (10.5, 0.0), (1.5, 0.0), (-9.5, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.6) if stride else list(base)
    if dead: feet = [(h[0] + [3, 0, -3, 4, 1, -2][k], h[1] - 2.0) for k, h in enumerate(hips)]
    legs6(r, hips, feet, 4.4, 5.0, 2.0, -2.0, mat="chit", far_mat="dchit", rad=1.35, far_rad=1.15)
    # the soft pale back end, tapering
    ab = [T(-6.0, -10.0 + bob), T(-12.0, -8.5 + bob), T(-16.5, -6.0 + bob)]
    r.tube(ab, [6.6, 5.0, 2.8], "pale", 0.0, bias=0.06)
    for k in range(3):
        x, y = lerp(ab[0][0], ab[2][0], 0.15 + k * 0.28), lerp(ab[0][1], ab[2][1], 0.15 + k * 0.28)
        r.line(x, y - 4.0 + k, x + 0.6, y + 3.6 - k, "pale", 0.001, tone=1)
    # the massive armoured fore-body
    fb = T(1.5, -12.0 + bob + c * 0.5)
    r.ell(fb[0], fb[1], 8.9, 8.6, "chit", 0.2, bias=0.1)
    r.ell(fb[0] - 2.0, fb[1] - 3.6, 4.0, 1.6, "chit", 0.21, flat=4)
    for k in range(3): r.line(fb[0] - 5 + k * 4, fb[1] - 6.5 + k * 0.5, fb[0] - 6 + k * 4, fb[1] + 5.5, "chit", 0.205, tone=1)
    # the head plate (a battering ram) and the gold horn
    hx, hy = T(9.5 + head, -11.0 + bob + c)
    r.poly([(hx - 3.0, hy - 6.5), (hx + 4.0, hy - 3.5), (hx + 5.0, hy + 3.5), (hx - 2.0, hy + 5.0)], "chit", 0.4,
           normal=(-0.1, -0.5, 0.85))
    r.line(hx - 2.6, hy - 6.0, hx + 3.8, hy - 3.2, "chit", 0.401, tone=4)
    ha = -40 - horn * 40
    h1 = chain(hx + 2.0, hy - 3.0, [(4.0, ha), (3.0, ha - 25), (2.0, ha - 45)])
    r.tube(h1, [1.6, 1.2, 0.8, 0.4], "royal", 0.45)
    r.dot(h1[-1][0], h1[-1][1], "royal", 4, 0.46)
    eye(r, hx + 2.0, hy + 1.0, 0.47, glint=not dead)
    if hurt and not dead: r.dot(hx + 2.0, hy + 1.0, "white", 3, 0.48)
    if gleam:
        r.dot(hx + 3.6, hy - 2.6, "white", 4, 0.5); r.dot(hx + 4.4, hy - 3.4, "white", 3, 0.5); r.dot(hx + 2.8, hy - 1.8, "white", 3, 0.5)
    mandible(r, (hx + 4.0, hy + 3.0), 30, 3.0, -40, 0.44, mat="amber", rad=0.7)
    if resin: puddle(r, -12.0, 4.0, -1.0, mat="amber")
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, (hx, hy), h1[-1])
    return r.resolve()


def colossus_sheet(outdir):
    Co = colossus
    idle = [Co(bob=[0, 0.4, 0.7, 0.4][i], horn=[0, 0.05, 0.1, 0.05][i], gleam=i == 2) for i in range(4)]
    run = [Co(i=i, n=6, stride=2.2, bob=0.6 * abs(math.sin(i / 6 * math.tau)), lean=3) for i in range(6)]
    # Gore: head low (0, 1), HEAVE the horn up through (2), follow (3), settle (4, 5)
    gore = [Co(head=-1.0, horn=-0.5, crouch=1.0, lean=4), Co(head=-1.5, horn=-0.8, crouch=1.8, lean=8),
            Co(head=2.0, horn=1.2, crouch=-0.5, lean=-6, dust_at=(14, 0, 0), extra=lambda r, h, t: smear(r, [(t[0] + 2, t[1] + 8), (t[0] + 1, t[1] + 1)], "white", 3)),
            Co(head=1.5, horn=1.4, crouch=-0.6, lean=-8), Co(head=0.5, horn=0.5, lean=-2), Co()]
    # Bulldoze: lower the plate (0, 1), CHARGE (2-5 loop, dust, resin dropped), brace (6)
    bull = [Co(head=-0.5, horn=-0.6, crouch=1.4, lean=8, gleam=True), Co(head=-1.0, horn=-0.8, crouch=2.0, lean=10, gleam=True)]
    bull += [Co(i=kk, n=4, stride=3.0, head=1.0, horn=-0.8, crouch=2.0, lean=10, dust_at=(-10, 0, kk % 2), resin=kk % 2 == 1) for kk in range(4)]
    bull += [Co(head=1.5, horn=0.4, crouch=0.5, lean=-4, dust_at=(14, 0, 0))]
    d = [Co(hurt=True, lean=-8, head=-1, horn=0.5), Co(hurt=True, lean=-12, bob=1.5, horn=0.6),
         Co(dead=True, lean=6, bob=4.0, horn=-0.5, dust_at=(0, 0, 0)), Co(dead=True, lean=8, bob=5.0, horn=-0.6)]
    knock = Co(hurt=True, lean=-12, head=-1.5, horn=0.6)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.1] * 6),
             ("Gore", gore, [0.14, 0.14, 0.05, 0.1, 0.12, 0.14]), ("Bulldoze", bull, [0.12, 0.12, 0.07, 0.07, 0.07, 0.07, 0.14])]
    anims += tail_anims(idle[0], d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkColossus", anims, outdir, scale=5)


SYNC["ZhkColossus"] = {"Gore": [("GORE: the horn heaves up at (18, -14); box 20 x 20 at (17, -13)", 2)],
                       "Bulldoze": [("CHARGE starts (frames 2-5 loop while it shoves)", 2)]}
NOTES["ZhkColossus"] = "Front Plate: the head plate gleams on Idle 2 and Bulldoze 0-1; the soft pale back end is the weak side."


# ================================================================== GLUE MORTAR: a termite whose head is a barrel
def mortar(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, aim=-55.0, recoil=0.0, squeeze=0.0, hurt=False, dead=False,
           extra=None, dust_at=None, puff=0.0, shells=3):
    r = ZRig(1.36)
    T = Xf(lean, (0.0, -8.0))
    hips = [T(1.5, -5.0 + bob), T(-1.5, -5.0 + bob), T(-4.5, -5.0 + bob), T(2.5, -5.4 + bob), T(-0.5, -5.4 + bob), T(-3.5, -5.4 + bob)]
    base = [(6.0, 0.0), (0.0, 0.0), (-7.5, 0.0), (7.5, 0.0), (1.5, 0.0), (-6.0, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.4) if stride else list(base)
    if dead: feet = [(h[0] + [2, 0, -2, 3, 1, -1][k], h[1] - 2.5) for k, h in enumerate(hips)]
    legs6(r, hips, feet, 3.6, 4.0, 1.5, -2.0, mat="pale", far_mat="dchit", rad=0.7, far_rad=0.6)
    # squat cream body with glue shells stored in its back
    ab = T(-6.0, -8.0 + bob)
    r.ell(ab[0], ab[1], 7.5, 6.1, "pale", 0.0, bias=0.06)
    for k in range(3): r.line(ab[0] - 4 + k * 3, ab[1] - 4.8, ab[0] - 4.6 + k * 3, ab[1] + 4.6, "pale", 0.001, tone=1)
    for k in range(shells):
        r.ell(ab[0] - 3 + k * 3, ab[1] - 5.0, 1.4, 1.4, "glue", 0.02, bias=0.2)
    tho = T(0.5, -8.0 + bob)
    r.ell(tho[0], tho[1], 4.0, 3.6, "pale", 0.2, bias=0.08)
    # the barrel head, angled up
    hc = T(4.5 - recoil * 0.8, -11.0 + bob + recoil * 0.6)
    r.ell(hc[0], hc[1], 4.4 * (1 + squeeze * 0.1), 4.0 * (1 - squeeze * 0.05), "chit", 0.4, bias=0.1)
    a = math.radians(aim)
    L = 9.0 - recoil
    mz = (hc[0] + L * math.cos(a), hc[1] + L * math.sin(a))
    r.tube([hc, (hc[0] + L * 0.5 * math.cos(a), hc[1] + L * 0.5 * math.sin(a)), mz], [3.6, 3.2, 2.8], "ochit", 0.45, bias=0.05)
    for f in (0.35, 0.7):
        bx, by = hc[0] + L * f * math.cos(a), hc[1] + L * f * math.sin(a)
        r.ell(bx, by, 1.0, 3.3, "chit", 0.46, ang=aim + 90, bias=0.15)   # the barrel bands
    r.ell(mz[0], mz[1], 2.4, 1.6, "glue", 0.47, ang=aim + 90, flat=3)
    r.ell(mz[0] + 0.3, mz[1] + 0.2, 1.4, 0.9, "dchit", 0.48, ang=aim + 90, flat=0)
    drip(r, mz[0] + 1.0, mz[1] + 1.6, 2, 0.49, mat="glue")
    if puff:
        for kk in range(3):
            r.ell(mz[0] + math.cos(a) * (2 + kk * 2) * puff, mz[1] + math.sin(a) * (2 + kk * 2) * puff, 1.6 - kk * 0.3, 1.4 - kk * 0.3, "glue", 3.0, flat=4 - kk)
    eye(r, hc[0] + 1.5, hc[1] + 1.8, 0.5, glint=not dead)
    if hurt and not dead: r.dot(hc[0] + 1.5, hc[1] + 1.8, "white", 3, 0.51)
    mandible(r, (hc[0] + 2.4, hc[1] + 3.2), 40, 2.4, -40, 0.44, mat="amber", rad=0.6)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, mz, hc)
    return r.resolve()


def mortar_sheet(outdir):
    Mo = mortar
    idle = [Mo(bob=[0, 0.3, 0.6, 0.3][i], aim=[-55, -57, -59, -57][i], squeeze=[0, 0.3, 0.6, 0.3][i]) for i in range(4)]
    run = [Mo(i=i, n=6, stride=2.0, bob=0.5 * abs(math.sin(i / 6 * math.tau)), lean=3, aim=-45) for i in range(6)]
    # Shell: aim (0, 1), squeeze (2), FIRE (3, recoil + puff), settle (4, 5)
    sh = [Mo(aim=-60, squeeze=0.5), Mo(aim=-65, squeeze=1.0, bob=0.5), Mo(aim=-66, squeeze=1.6, bob=1.0, lean=-3),
          Mo(aim=-66, recoil=2.0, puff=1.0, lean=-6, shells=2, dust_at=(0, 0, 0)), Mo(aim=-62, recoil=1.0, lean=-2, shells=2), Mo(shells=2)]
    # Bombard: three shots (3, 5, 7), each a recoil
    bb = [Mo(aim=-62, squeeze=0.8), Mo(aim=-66, squeeze=1.6, bob=1.0, lean=-3)]
    for kk in range(3):
        bb += [Mo(aim=-66 + kk * 4, recoil=2.0, puff=1.0, lean=-6, shells=2 - kk, dust_at=(0, 0, 0)),
               Mo(aim=-64 + kk * 4, recoil=0.8, squeeze=1.2, lean=-2, shells=2 - kk)]
    bb += [Mo(shells=0)]
    d = [Mo(hurt=True, lean=-10, aim=-80, recoil=1.0), Mo(hurt=True, lean=-16, bob=1.5, aim=-30),
         Mo(dead=True, lean=8, bob=3.5, aim=10, shells=0, dust_at=(0, 0, 0)),
         Mo(dead=True, lean=10, bob=4.0, aim=15, shells=0, extra=lambda r, m, h: puddle(r, 8.0, 4.0, -3.0, mat="glue"))]
    knock = Mo(hurt=True, lean=-12, aim=-80, recoil=1.0)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.09] * 6),
             ("Shell", sh, [0.12, 0.12, 0.12, 0.06, 0.12, 0.14]), ("Bombard", bb, [0.12, 0.12, 0.06, 0.14, 0.06, 0.14, 0.06, 0.14, 0.14])]
    anims += tail_anims(idle[0], d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkMortar", anims, outdir, scale=5)


SYNC["ZhkMortar"] = {"Shell": [("FIRE: the shell leaves the muzzle at (10, -21)", 3)],
                     "Bombard": [("FIRE 1", 2), ("FIRE 2", 4), ("FIRE 3", 6)]}
NOTES["ZhkMortar"] = "Spotters: FxZhkSpot crosshairs over each ally it fires through."


# ================================================================== STAG TITAN: a stag beetle with antler jaws
def stag(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, jaw=0.3, lift=0.0, head=0.0, hurt=False, dead=False, extra=None,
         dust_at=None, shadow=True, butt=0.0):
    r = ZRig(1.0)
    T = Xf(lean, (0.0, -6.0))
    bob = bob - 2.0
    hips = [T(1.0, -4.5 + bob), T(-2.0, -4.5 + bob), T(-5.5, -4.5 + bob), T(2.0, -5.0 + bob), T(-1.0, -5.0 + bob), T(-4.5, -5.0 + bob)]
    base = [(5.0, 0.0), (-1.5, 0.0), (-10.0, 0.0), (6.5, 0.0), (0.0, 0.0), (-8.5, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.4) if stride else list(base)
    if dead: feet = [(h[0] + [2, 0, -2, 3, 1, -1][k], h[1] - 2.5) for k, h in enumerate(hips)]
    legs6(r, hips, feet, 4.6, 5.0, 1.5, -2.0, mat="rchit", far_mat="dchit", rad=0.8, far_rad=0.6)
    # long low body: elytra and the pronotum
    ab = T(-6.5, -10.0 + bob)
    r.ell(ab[0], ab[1], 8.2, 9.6, "rchit", 0.0, bias=0.1)
    r.ell(ab[0] + 1.0, ab[1] + 3.0, 7.0, 3.0, "dchit", -0.1)
    r.line(ab[0] - 7.0, ab[1] - 0.4, ab[0] + 6.0, ab[1] - 5.6, "rchit", 0.01, tone=1)
    r.ell(ab[0] - 2.0, ab[1] - 4.8, 4.0, 1.2, "rchit", 0.02, flat=4)
    pr = T(2.0, -9.0 + bob)
    r.ell(pr[0], pr[1], 5.0, 6.6, "rchit", 0.2, bias=0.08)
    hx, hy = T(6.0 + head, -9.0 + bob - lift * 0.5 + butt * 0.6)
    r.ell(hx, hy, 4.2, 4.0, "rchit", 0.3, bias=0.06)
    eye(r, hx + 1.0, hy - 1.0, 0.35, glint=not dead)
    if hurt and not dead: r.dot(hx + 1.0, hy - 1.0, "white", 3, 0.36)
    # the antler jaws: two long forks; `lift` raises them, `jaw` opens them
    tips = []
    for kk, (mat, z, sgn) in enumerate((("bronze", 0.25, 1), ("bronze", 0.5, -1))):
        a0 = -8 - lift * 35 + sgn * (11 + (jaw + 0.5) * 16)
        pts = chain(hx + 2.4, hy + (0.8 if kk else -1.2), [(6.0, a0), (6.0, a0 - sgn * 10), (4.0, a0 - sgn * 32), (2.6, a0 - sgn * 72)])
        r.tube(pts, [2.2, 1.8, 1.3, 0.8, 0.4], mat, z, bias=0.0 if kk else -0.25)
        mid = pts[1]
        tine = chain(mid[0], mid[1], [(2.4, a0 - 70 * sgn)])[-1]
        r.tube([mid, tine], [0.7, 0.35], mat, z + 0.01, bias=0.0 if kk else -0.25)
        r.dot(pts[-1][0], pts[-1][1], mat, 4, z + 0.02)
        tips.append(pts[-1])
    if shadow and not dead:
        # the jaws' shadow on the floor marks the tip zone
        tx = (tips[0][0] + tips[1][0]) / 2.0
        r.ell(tx - 1.0, -0.4, 4.0, 0.8, "dchit", -5.0, flat=1)
    antenna(r, (hx + 0.4, hy - 2.4), -100, 3.4, 60, 0.29, club="rchit")
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, (hx, hy), tips)
    return r.resolve()


def stag_sheet(outdir):
    St = stag
    idle = [St(bob=[0, 0.3, 0.5, 0.3][i], jaw=[0.3, 0.4, 0.5, 0.4][i]) for i in range(4)]
    run = [St(i=i, n=6, stride=2.2, bob=0.5 * abs(math.sin(i / 6 * math.tau)), lean=3, jaw=0.3) for i in range(6)]
    # Pinch: jaws wide (0, 1), PINCH the tips shut (2), squeeze (3), let go (4, 5)
    pinch = [St(jaw=0.9, head=-0.5), St(jaw=1.3, head=-1.0, lean=-3), St(jaw=-0.2, head=1.5, lean=4), St(jaw=-0.3, head=1.2, lean=3),
             St(jaw=0.5, head=0.5), St(jaw=0.3)]
    # Uproot: jaws down low (0, 1), HOOK under (2), LIFT and toss up (3, 4), jaws high (5), down (6, 7)
    up = [St(lift=-0.4, jaw=0.6, head=0.5, lean=3), St(lift=-0.6, jaw=0.8, head=1.5, lean=6, bob=0.5),
          St(lift=-0.5, jaw=0.1, head=2.0, lean=6, bob=0.5, dust_at=(18, 0, 0)), St(lift=0.6, jaw=0.1, head=1.0, lean=-6),
          St(lift=1.2, jaw=0.4, head=0.0, lean=-10, extra=lambda r, h, t: smear(r, [(t[0][0], t[0][1] + 8), (t[0][0] - 1, t[0][1])], "white", 3)),
          St(lift=1.2, jaw=0.5, lean=-10), St(lift=0.5, jaw=0.4, lean=-4), St(jaw=0.3)]
    # Butt: the jaws can't reach close: a short headbutt
    bt = [St(head=-1.0, lean=-4, lift=0.6), St(head=-1.6, lean=-8, lift=0.8), St(head=2.5, butt=1.0, lean=8, lift=0.6, dust_at=(8, 0, 0)),
          St(head=1.5, lean=4, lift=0.4), St()]
    d = [St(hurt=True, jaw=1.0, lean=-8, lift=0.5), St(hurt=True, jaw=0.8, lean=-14, bob=1.0, lift=0.8),
         St(dead=True, jaw=0.6, lean=6, bob=3.0, dust_at=(0, 0, 0)), St(dead=True, jaw=0.7, lean=8, bob=3.5)]
    knock = St(hurt=True, jaw=1.0, lean=-12, lift=0.8)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Pinch", pinch, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]), ("Uproot", up, [0.12, 0.1, 0.06, 0.08, 0.1, 0.12, 0.1, 0.12]),
             ("Butt", bt, [0.1, 0.1, 0.05, 0.1, 0.12])]
    anims += tail_anims(idle[0], d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkStag", anims, outdir, scale=5)


SYNC["ZhkStag"] = {"Pinch": [("PINCH: the tips close 26-34 px out at (30, -6)", 2)],
                   "Uproot": [("HOOK: tips under the hero at (28, -2)", 2), ("TOSS: the hero goes up", 3)],
                   "Butt": [("BUTT: head at (12, -6); box 12 x 10 at (10, -6)", 2)]}
NOTES["ZhkStag"] = "Jaw Gap: the dark ellipse on the floor under the jaws marks the tip zone (26-34 px)."


# ================================================================== SUN SCARAB: a scarab with a glowing ball of amber
def sun_ball(r, x, y, R, z, rot=0.0, larvae=0, crack=0.0):
    cx, cy = x, y - R
    r.ell(cx, cy, R, R, "jelly", z, flat=2)
    r.ell(cx + R * 0.15, cy + R * 0.15, R * 0.8, R * 0.8, "amber", z + 0.001, bias=0.25)
    r.ell(cx - R * 0.1, cy - R * 0.05, R * 0.55, R * 0.55, "jelly", z + 0.002, flat=3)
    for k in range(larvae):
        a = math.radians(rot * 0.6 + k * 120)
        lx, ly = cx + R * 0.45 * math.cos(a), cy + R * 0.45 * math.sin(a)
        r.ell(lx, ly, 1.4, 0.8, "honey", z + 0.003, ang=rot + k * 60, flat=1)
        r.dot(lx + 0.6 * math.cos(a), ly + 0.6 * math.sin(a), "honey", 0, z + 0.004)
    r.dot(cx - R * 0.45, cy - R * 0.55, "white", 3, z + 0.005)
    r.dot(cx - R * 0.3, cy - R * 0.65, "white", 2, z + 0.005)
    if crack:
        r.polyline([(cx + R * 0.2, cy - R), (cx, cy - R * 0.3), (cx + R * 0.3, cy + R * 0.2)], "honey", z + 0.006, tones=[0, 0])
    return (cx, cy)


def sunscarab(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, larvae=0, bx=0.0, rot=0.0, head=0.0, rear=0.0, hurt=False,
              dead=False, extra=None, dust_at=None, ball=True, crack=0.0):
    r = ZRig(1.21)
    T = Xf(lean, (-3.0, -5.0))
    cx, cy = T(-5.0, -6.0 + bob - rear)
    hips = [T(0.0, -3.5 + bob - rear), T(-4.0, -3.5 + bob - rear * 0.6), T(-8.0, -3.6 + bob), T(1.0, -4.0 + bob - rear), T(-3.0, -4.0 + bob - rear * 0.6), T(-7.0, -4.0 + bob)]
    base = [(3.5, 0.0), (-3.0, 0.0), (-11.5, 0.0), (5.0, 0.0), (-1.5, 0.0), (-10.0, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.2) if stride else list(base)
    if dead: feet = [(h[0] + [2, 0, -2, 3, 1, -1][k], h[1] - 3.0) for k, h in enumerate(hips)]
    legs6(r, hips, feet, 3.4, 3.8, 1.4, -2.0, mat="scarb", far_mat="dchit", rad=0.6, far_rad=0.5)
    r.ell(cx, cy + 2.0, 7.0, 2.2, "dchit", -0.5)
    r.ell(cx, cy, 8.0, 6.0, "scarb", 0.0, bias=0.1)
    r.line(cx - 7.0, cy - 0.6, cx + 4.0, cy - 5.0, "scarb", 0.01, tone=1)
    r.ell(cx - 2.6, cy - 3.6, 3.6, 1.0, "teal", 0.02, flat=4)
    r.ell(cx + 1.0, cy - 2.0, 2.0, 1.2, "teal", 0.02, flat=3)
    hx, hy = T(4.5 + head, -5.0 + bob - rear * 0.4)
    r.ell(hx - 1.0, hy - 0.8, 3.2, 2.8, "scarb", 0.3, bias=0.05)
    for k in range(4):
        a = math.radians(-80 + k * 25)
        r.tube([(hx + 0.6, hy - 2.0), (hx + 0.6 + 3.0 * math.cos(a), hy - 2.0 + 3.0 * math.sin(a))], [0.7, 0.35], "royal", 0.32)
    eye(r, hx + 0.4, hy - 1.0, 0.34, glint=not dead)
    if hurt and not dead: r.dot(hx + 0.4, hy - 1.0, "white", 3, 0.35)
    out = None
    if ball:
        out = sun_ball(r, hx + 9.4 + bx, 0.0, 7.4, 0.5, rot=rot, larvae=larvae, crack=crack)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, (hx, hy), out)
    return r.resolve()


def sunscarab_sheet(outdir):
    Ss = sunscarab
    anims = []
    for lv, sfx in ((0, ""), (1, "1"), (2, "2"), (3, "3")):
        idle = [Ss(larvae=lv, bob=[0, 0.3, 0.5, 0.3][i], rot=i * 8) for i in range(4)]
        run = [Ss(larvae=lv, i=i, n=6, stride=1.8, bob=0.4 * abs(math.sin(i / 6 * math.tau)), lean=3, rot=i * 30, head=0.3) for i in range(6)]
        anims += [("Idle" + sfx, idle, [0.16, 0.14, 0.16, 0.14]), ("Run" + sfx, run, [0.09] * 6)]
    # Shove: draw back (0, 1), SHOVE the ball forward (2), it settles back (3-5)
    sv = [Ss(bx=-1.0, lean=-4, rear=0.6, head=-1.0), Ss(bx=-2.0, lean=-8, rear=1.0, head=-1.5),
          Ss(bx=4.0, lean=8, head=2.5, rot=40, dust_at=(8, 0, 0)), Ss(bx=3.0, lean=6, head=2.0, rot=60), Ss(bx=1.0, lean=2, head=0.6), Ss()]
    # Release: rear back (0, 1), PUSH it rolling (2), it rolls off (3), gone (4-6)
    rl = [Ss(larvae=2, bx=-1.0, lean=-5, rear=0.8), Ss(larvae=2, bx=-2.0, lean=-10, rear=1.4, crack=1.0),
          Ss(larvae=2, bx=5.0, lean=10, head=2.5, rot=60, crack=1.0, dust_at=(8, 0, 0)), Ss(larvae=2, bx=14.0, lean=8, head=2.0, rot=180, crack=1.0),
          Ss(ball=False, lean=4, head=1.0, dust_at=(10, 0, 2)), Ss(ball=False, lean=2), Ss(ball=False)]
    anims += [("Shove", sv, [0.12, 0.12, 0.05, 0.1, 0.1, 0.12]), ("Release", rl, [0.12, 0.12, 0.06, 0.08, 0.1, 0.1, 0.12])]
    # IdleEmpty / RunEmpty: while the ball is away it waits for a new one to form (a dull amber nub)
    ie = [Ss(ball=False, bob=[0, 0.3, 0.5, 0.3][kk], extra=lambda r, h, o: sun_ball(r, h[0] + 4.0, 0.0, 2.0, 0.5)) for kk in range(4)]
    re_ = [Ss(ball=False, i=kk, n=6, stride=1.8, lean=3, extra=lambda r, h, o: sun_ball(r, h[0] + 4.0, 0.0, 2.0, 0.5)) for kk in range(6)]
    anims += [("IdleEmpty", ie, [0.16, 0.14, 0.16, 0.14]), ("RunEmpty", re_, [0.09] * 6)]
    idle0 = anims[0][1][0]
    d = [Ss(hurt=True, rear=1.5, lean=-12), Ss(hurt=True, lean=-18, bob=1.0, bx=3),
         Ss(dead=True, lean=6, bob=3.0, bx=6, crack=1.0, dust_at=(0, 0, 0)), Ss(dead=True, lean=8, bob=3.5, bx=7, crack=1.0)]
    knock = Ss(hurt=True, rear=1.8, lean=-14)
    anims += tail_anims(idle0, d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkSunScarab", anims, outdir, scale=5)


SYNC["ZhkSunScarab"] = {"Shove": [("SHOVE: the ball at (18, -9); box 20 x 18 at (17, -9)", 2)],
                        "Release": [("RELEASE: the ball rolls off from (16, -7)", 2)]}
NOTES["ZhkSunScarab"] = ("Fossil Ball: Idle/Run (empty ball), Idle1/Run1 .. Idle3/Run3 (larvae caught inside). IdleEmpty/RunEmpty "
                         "while the ball is away.")

JOBS = [("ZhkGorger", gorger_sheet), ("ZhkBotfly", botfly_sheet), ("ZhkColossus", colossus_sheet), ("ZhkMortar", mortar_sheet),
        ("ZhkStag", stag_sheet), ("ZhkSunScarab", sunscarab_sheet)]
