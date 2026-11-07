"""The six ghost-form fodder creatures (possessable T1s, built on the vanilla slime): Keener, Revenant, Fusebelly,
Gargling, Poppet and Mimic. Drawn with the material renderer (ghosts_v2_kit, from jinx_v2_rigs).

    python3 ghosts_v2_fodder.py [outdir] [--only Name,Name]

Writes to art/out_ghosts. Cells, anims, frame counts, event frames and the spawn points the C# uses (GhostV11.cs) are
the same as before: Keener mouth (5, 8), Gargling maw (7, 11), Mimic coins (5, 8), Fusebelly fuse tip (0, 13).
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ghosts_v2_kit import Rig, stone, chain, ik, lerp, sheet, tail, spark, puff, outdir_for, Xf  # noqa: E402

OUT = outdir_for("out_ghosts")
CELLS = {"FodKeener": (24, 21), "FodRevenant": (30, 23), "FodFusebelly": (26, 21), "FodGargling": (28, 21),
         "FodPoppet": (26, 20), "FodMimic": (26, 23)}


def S(v, k):
    return math.sin((v + k) * math.pi * 2)


# ================================================================== KEENER: a floating wailing head trailing its hair
def keener(cx=2.5, cy=-9.5, tilt=0.0, gape=0.3, eye="glow", flow=0.0, sweep=0.0, hands=None, ring=0, droop=0.0,
           mist=1.0, lie=False):
    """(cx, cy) = the head's centre. flow: hair wave phase; sweep: hair blown back (+) or forward (-) in degrees;
    gape 0..1 opens the jaw; hands: [(x, y)] for the bony hands clutching at the hair (None = hidden in it)."""
    r = Rig()
    T = Xf(tilt, (cx, cy))
    # hair: one swept mane from the crown, three locks trailing off it with a wave running along them
    mane = [T(cx + 0.5, cy - 4.0), T(cx - 2.5, cy - 4.2), T(cx - 5.0 - sweep * 0.03, cy - 2.6 + droop * 2),
            T(cx - 5.5 - sweep * 0.04, cy + 0.8 + droop * 3), T(cx - 3.0, cy + 3.2), T(cx - 0.5, cy + 2.0)]
    r.poly(mane, "nhair", -2.0, normal=(-0.3, -0.5, 1.0), curve=0.5)
    r.ell(*T(cx - 1.0, cy - 3.8), 3.0, 1.6, "nhair", -1.9, ang=tilt - 10, bias=0.1)    # the crown of the mane
    locks = []
    for i, (rx_, ry_, ln, rad0) in enumerate(((-3.6, -3.0, 2.0, 1.5), (-4.6, -0.4, 2.1, 1.7), (-3.4, 2.2, 1.8, 1.3))):
        x, y = T(cx + rx_, cy + ry_)
        a0 = 186 - i * 13 - sweep * 0.5 - droop * 45
        segs = [(ln, a0 - k * (5 - sweep * 0.1 + droop * 6) + 12 * math.sin(flow * 2 * math.pi - k * 1.2 + i * 0.9))
                for k in range(5)]
        pts = chain(x, y, segs)
        if lie: pts = [(px, min(py, -0.5)) for px, py in pts]
        locks.append((pts, rad0))
    # the locks are one sheet of hair (filled between them), only the last segment of each hangs free
    for (pa, _), (pb, _) in zip(locks, locks[1:]):
        r.poly(pa[:5] + pb[:5][::-1], "nhair", -2.2, normal=(-0.4, -0.2, 1.0), bias=-0.1)
    for i, (pts, rad0) in enumerate(locks):
        r.tube(pts, [rad0, rad0 * 0.85, rad0 * 0.7, 0.8, 0.6, 0.45], "nhair", -2.1 + (0.05 if i == 0 else -0.05 * i),
               bias=0.12 if i == 0 else -0.05)
        ex, ey = pts[-1]
        if mist and i == 1:
            r.dot(ex - 1, ey, "spirit", 1, -1.9)
    # spirit wisps where a neck would be: the keener has no body, just a cold glow dripping off it
    if mist and not lie:
        for k, (dx, dy) in enumerate(((-0.5, 4.6), (0.6, 5.8), (-0.2, 7.2))):
            x, y = T(cx + dx + 0.6 * math.sin(flow * 6.28 + k), cy + dy)
            if y < -0.5: r.dot(x, y, "spirit", 2 if k == 0 else 1, -1.5)
    # skull-thin head: pale, hollow cheek, a long jaw that drops when it wails
    hx, hy = T(cx, cy)
    r.ell(hx, hy - 0.6, 3.9, 3.7, "pale", 0.0, ang=tilt)
    jx, jy = T(cx + 1.0, cy + 2.3 + gape * 1.6)
    r.ell(jx, jy, 2.4, 1.7 + gape * 0.5, "pale", 0.2, ang=tilt + 10, bias=-0.1)
    # mouth: a dark open O on the right side of the face
    mx, my = T(cx + 2.4, cy + 1.4 + gape * 0.8)
    if gape > 0.15:
        r.ell(mx, my, 0.9 + gape * 0.5, 0.8 + gape * 1.3, "mouth", 1.0, flat=1)
        if gape > 0.6: r.dot(mx - 0.5, my - 0.8 - gape * 0.6, "mouth", 3, 1.05)
    else:
        r.line(mx - 1, my, mx + 1, my, "mouth", 1.0, tone=1)
    # eyes: hollow sockets with a cold glint (right eye nearer, bigger)
    for k, (ex_, ey_) in enumerate(((0.6, -1.5), (2.8, -1.4))):
        x, y = T(cx + ex_, cy + ey_)
        r.ell(x, y, 0.9 if k == 0 else 1.1, 1.1, "mouth", 1.0, flat=1)
        if eye == "glow": r.dot(x + 0.3, y - 0.2, "spirit", 4 if k else 3, 1.1)
        elif eye == "x": r.dot(x, y, "pale", 1, 1.1)
    # brow ridge and cheekbone catch the light
    bx, by = T(cx + 1.6, cy - 2.7)
    r.line(bx - 1.6, by, bx + 1.2, by + 0.2, "pale", 0.9, tone=4)
    # front fringe: two strands across the brow
    fx, fy = T(cx - 0.4, cy - 3.6)
    r.tube(chain(fx, fy, [(2.0, 15 + sweep * 0.2), (1.6, 70 + sweep * 0.3)]), [0.8, 0.7, 0.5], "nhair", 2.0, bias=0.2)
    if hands:
        for i, (ax, ay) in enumerate(hands):
            z = 2.5 if i else -1.0
            r.tube([(ax - 1.5, ay + 2.0), (ax, ay)], [0.6, 0.5], "pale", z, bias=-0.1 if i == 0 else 0.1)
            for d in (-0.8, 0.0, 0.8):
                r.dot(ax + 0.6, ay + d - 0.6, "pale", 3 if i else 2, z + 0.01)
    if ring:
        # the shriek leaving the mouth: two cyan arcs
        for k in range(ring):
            rr = 2.0 + k * 2.2
            for a in range(-50, 51, 12):
                x = mx + 1.5 + rr * math.cos(math.radians(a)); y = my + rr * 1.1 * math.sin(math.radians(a))
                r.dot(x, y, "spirit", 3 if k == 0 else 2, 6.0)
    return r.resolve()


def keener_sheet(outdir):
    K = keener
    idle = [K(cy=-9.5 - [0, 0.5, 1.0, 0.5][i], flow=i / 4, gape=[0.25, 0.35, 0.45, 0.35][i], tilt=[0, -3, -5, -3][i]) for i in range(4)]
    run = [K(cx=3.0, cy=-9.6 - 0.7 * abs(math.sin(i / 6 * math.pi * 2)), flow=i / 6, sweep=18 + 6 * math.sin(i / 6 * 6.28),
             tilt=10, gape=0.25) for i in range(6)]
    shriek = [K(cx=1.5, cy=-9.2, tilt=-14, gape=0.05, sweep=-8, flow=0.1, hands=[(0.5, -6.0), (4.0, -6.0)]),
              K(cx=0.5, cy=-10.0, tilt=-22, gape=0.2, sweep=-16, flow=0.25, eye="glow", hands=[(0.0, -6.5), (3.5, -7.5)]),
              K(cx=3.5, cy=-9.5, tilt=12, gape=1.0, sweep=30, flow=0.4, ring=1, hands=[(1.0, -5.5), (5.0, -5.0)]),
              K(cx=4.0, cy=-9.5, tilt=14, gape=1.0, sweep=40, flow=0.55, ring=2, hands=[(1.0, -5.0), (5.5, -4.5)]),
              K(cx=3.5, cy=-9.4, tilt=8, gape=0.7, sweep=26, flow=0.7, hands=[(1.0, -5.5), (4.5, -5.5)]),
              K(cx=2.7, cy=-9.5, tilt=2, gape=0.4, sweep=10, flow=0.85)]
    death = [K(cx=1.0, cy=-9.0, tilt=-24, gape=0.9, eye="none", sweep=20, flow=0.2),
             K(cx=1.0, cy=-7.0, tilt=-50, gape=0.6, eye="none", sweep=-10, droop=0.5, flow=0.4, mist=0.5),
             K(cx=1.5, cy=-4.3, tilt=-80, gape=0.4, eye="x", droop=1.0, flow=0.6, mist=0),
             K(cx=2.0, cy=-3.6, tilt=-92, gape=0.3, eye="x", droop=1.2, flow=0.8, mist=0, lie=True)]
    knock = K(cx=0.0, cy=-9.8, tilt=-28, gape=0.8, sweep=-30, flow=0.3, eye="x")
    spawn = [K(cx=1.5, cy=-1.5, tilt=-60, gape=0.0, eye="none", droop=1.4, mist=0.5, lie=True),
             K(cx=1.5, cy=-5.0, tilt=-20, gape=0.2, eye="none", sweep=-40, droop=0.6, flow=0.2),
             K(cx=2.5, cy=-12.0, tilt=8, gape=0.9, sweep=40, flow=0.4, ring=1),
             K(cx=2.5, cy=-8.5, tilt=4, gape=0.5, sweep=10, flow=0.6),
             K(cx=2.5, cy=-9.6, gape=0.3, flow=0.8)]
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.07] * 6),
             ("Shriek", shriek, [0.1, 0.12, 0.08, 0.08, 0.14, 0.12])] + tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock, spawn)
    return sheet("FodKeener", anims, outdir, min_cell=CELLS["FodKeener"])


# ================================================================== REVENANT: a grave-rag ghoul clawing out of the earth
def claw_hand(r, x, y, ang, z, open_=1.0, mat="bone", tone=3):
    """Three long finger bones fanning from (x, y) along ang."""
    for k in (-1, 0, 1):
        a = math.radians(ang + k * 22 * open_)
        r.line(x, y, x + 2.6 * math.cos(a), y + 2.6 * math.sin(a), mat, z, tone=tone if k < 1 else tone - 1)


def revenant(hip=(-0.5, -5.0), lean=24.0, feet=((-3.0, 0.0), (2.5, 0.0)), head_dx=0.0, head_dy=0.0, jaw=0.0,
             hand=(5.0, -6.0), hand2=(-1.0, -5.0), claw=0.0, claw_open=1.0, glow=1, rags=0.0, smear=None, earth=None,
             cut=None, eye="glow"):
    """A hunched ghoul: hip -> spine leaning `lean` degrees forward; skull head, rag hood and cloak, bony arms."""
    r = Rig()
    hx, hy = hip
    a = math.radians(-90 + lean)
    sx, sy = hx + 4.6 * math.cos(a), hy + 4.6 * math.sin(a)            # shoulders
    kx, ky = sx + 2.6 * math.cos(a) + head_dx, sy + 2.6 * math.sin(a) + head_dy + 0.4   # skull centre
    # legs: thin bones, knees forward, rag wraps on the shins
    for k, (fx, fy) in enumerate(feet):
        kn = ik(hx + (0.6 if k else -0.6), hy, fx, fy, 3.2, 3.2, bend=-1)
        z = 0.5 if k else -1.0
        r.tube([(hx, hy), kn, (fx, fy - 0.6)], [1.0, 0.8, 0.7], "bone", z, bias=-0.25 if k == 0 else 0.0)
        r.line(fx - 0.5, fy, fx + 1.5, fy, "bone", z + 0.01, tone=2 if k else 1)
    # far arm (behind the body)
    sa = (sx - 1.0, sy + 0.8)
    el = ik(sa[0], sa[1], hand2[0], hand2[1], 2.8, 2.8, bend=1)
    r.tube([sa, el, hand2], [0.7, 0.6, 0.5], "bone", -2.0, bias=-0.3)
    claw_hand(r, hand2[0], hand2[1], math.degrees(math.atan2(hand2[1] - el[1], hand2[0] - el[0])), -2.0, tone=2)
    # rag cloak: hangs from the shoulders down the back, tattered hem that flaps
    hem = []
    for i in range(6):
        t = i / 5.0
        x = lerp(hx - 4.2 - rags * 0.8, hx + 2.4, t)
        y = hy + 2.6 + (1.4 if i % 2 else 0.0) + math.sin(rags * 3 + i) * 0.6
        hem.append((x, min(-0.5, y)))
    cloak = [(sx + 1.4, sy - 1.2), (sx - 2.0, sy - 1.6), (hx - 3.4 - rags * 0.6, hy - 1.0)] + hem + [(hx + 2.4, hy - 0.6)]
    r.poly(cloak, "rag", 0.0, normal=(-0.3, -0.4, 1.0), curve=0.6)
    for i in (1, 3):
        r.line(hem[i][0], hem[i][1] - 3.0, hem[i][0] + 0.3, hem[i][1] - 0.5, "rag", 0.05, tone=1)
    # hood around the skull
    r.ell(kx - 1.0, ky - 0.6, 3.4, 3.3, "rag", 0.6, bias=0.05)
    # skull: domed, deep sockets glowing green, a hanging jaw
    r.ell(kx + 0.6, ky - 0.3, 2.8, 2.6, "bone", 1.0, ang=lean * 0.3, bias=0.1)
    r.ell(kx + 1.6, ky + 1.6 + jaw, 1.6, 0.9, "bone", 1.05, bias=-0.15)
    r.line(kx + 0.8, ky + 1.0 + jaw * 0.5, kx + 2.6, ky + 1.1 + jaw * 0.5, "mouth", 1.1, tone=1)
    if jaw > 0.6: r.dot(kx + 1.6, ky + 1.0 + jaw * 0.5, "mouth", 1, 1.1)
    ex, ey = kx + 1.3, ky - 0.4
    r.dot(ex, ey, "mouth", 0, 1.2); r.dot(ex + 1.0, ey, "mouth", 0, 1.2)
    if eye == "glow":
        r.dot(ex + 1.0, ey, "soul", 4 if glow else 3, 1.3); r.dot(ex, ey, "soul", 2, 1.3)
    # near arm: long, reaching, the claw
    sn = (sx + 0.6, sy + 1.0)
    el = ik(sn[0], sn[1], hand[0], hand[1], 3.0, 3.0, bend=-1 if hand[1] < sn[1] else 1)
    r.tube([sn, el, hand], [0.8, 0.7, 0.6], "bone", 3.0, bias=0.05)
    r.ell(sn[0] - 0.2, sn[1] - 0.2, 1.2, 1.0, "rag", 3.05, bias=0.1)       # rag over the shoulder
    ang = math.degrees(math.atan2(hand[1] - el[1], hand[0] - el[0]))
    claw_hand(r, hand[0], hand[1], ang, 3.1, open_=claw_open)
    if claw:
        r.dots([(hand[0] + 3.2, hand[1] - 0.5), (hand[0] + 3.0, hand[1] + 1.4)], "soul", 3, 3.2)
    if smear:
        for (p0, p1) in smear: r.line(*p0, *p1, "soul", 3.4, tone=2)
    if earth is not None:
        mound(r, earth)
    rs = r.resolve()
    if cut is not None:      # rising out of the grave: nothing below the soil line
        rs.px = {k: v for k, v in rs.px.items() if k[1] <= cut or k[1] >= -1}
        rs.tones = {k: v for k, v in rs.tones.items() if k in rs.px}
    return rs


def mound(r, k):
    """A grave mound of turned earth (k = 0 flat .. 1 heaped), with clods."""
    r.ell(0.0, -0.3, 6.5, 1.6 + k * 1.2, "earth", 5.0, bias=0.05)
    for (x, y, rr) in ((-4.5, -1.8, 0.9), (3.6, -2.0 - k, 1.0), (-1.0, -2.2 - k, 0.8)):
        r.ell(x, y, rr, rr * 0.8, "earth", 5.1, bias=0.2)


def revenant_corpse(stage):
    r = Rig()
    r.ell(-0.5, -1.0, 4.5, 1.4, "rag", 0.0, bias=-0.05)
    if stage == 0:
        r.ell(4.2, -1.8, 2.2, 1.9, "bone", 1.0)
        r.dot(4.8, -2.2, "mouth", 0, 1.1); r.dot(5.8, -2.2, "mouth", 0, 1.1)
    else:
        r.ell(4.6, -1.4, 2.0, 1.5, "bone", 1.0, bias=-0.05)
        r.dot(5.4, -1.6, "mouth", 0, 1.1)
    for (x0, x1) in ((-5.0, -2.0), (-1.5, 1.6)):
        r.line(x0, -0.5, x1, -0.6, "bone", 0.5, tone=2)
    claw_hand(r, 7.0, -0.6, 0, 1.2, tone=2)
    return r.resolve()


def revenant_sheet(outdir):
    R = revenant
    idle = [R(hip=(-0.5, -5.0 + d), lean=22 + l, hand=(4.8, -5.6 + d), hand2=(-1.2, -4.6 + d), rags=i * 0.5, glow=i % 2)
            for i, (d, l) in enumerate(((0, 0), (0.3, 2), (0.6, 4), (0.3, 2)))]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        f1 = (-1.5 + 3.5 * math.cos(t), -max(0, 1.6 * math.sin(t)))
        f2 = (1.0 - 3.5 * math.cos(t), -max(0, -1.6 * math.sin(t)))
        run.append(R(hip=(0.0, -5.8 + 0.5 * abs(math.sin(t))), lean=34, feet=(f1, f2), hand=(5.5 + 1.5 * math.sin(t), -5.0),
                     hand2=(-2.0 - 1.5 * math.sin(t), -5.5), rags=1.0 + i * 0.7, glow=i % 2))
    claw = [R(lean=10, hand=(1.0, -11.5), hand2=(-2.0, -6.0), head_dy=-0.3, jaw=0.4),
            R(lean=2, hip=(-1.0, -5.6), hand=(-1.5, -13.0), hand2=(-2.5, -6.0), jaw=0.8, claw_open=1.3),
            R(lean=38, hip=(0.5, -5.2), feet=((-3.0, 0.0), (4.0, 0.0)), hand=(8.0, -5.0), jaw=1.0, claw=1,
              smear=[((0.0, -13.0), (6.0, -9.0)), ((6.0, -9.0), (9.0, -5.0))]),
            R(lean=44, hip=(1.0, -5.0), feet=((-3.0, 0.0), (4.0, 0.0)), hand=(8.5, -2.5), jaw=0.8, claw=1, claw_open=0.6),
            R(lean=34, hip=(0.5, -5.3), feet=((-3.0, 0.0), (3.5, 0.0)), hand=(6.5, -3.0), jaw=0.4, claw_open=0.7),
            R(lean=24, hand=(5.0, -5.4), jaw=0.1)]
    death = [R(lean=-8, hip=(-1.0, -5.6), hand=(1.0, -9.0), hand2=(-4.0, -9.0), jaw=1.2, head_dx=-1.0, eye="none"),
             R(lean=50, hip=(0.0, -3.6), feet=((-3.0, 0.0), (3.0, 0.0)), hand=(6.0, -0.8), hand2=(-1.0, -1.0), jaw=1.0, eye="none"),
             revenant_corpse(0), revenant_corpse(1)]
    knock = R(lean=-14, hip=(-1.5, -5.5), hand=(2.0, -8.0), hand2=(-4.5, -7.5), jaw=1.0, head_dx=-1.0, eye="glow")
    spawn = [R(earth=0.2, hip=(0, 2), lean=30, hand=(3.0, -1.5), cut=-1),
             R(earth=0.8, hip=(0, -1.0), lean=40, hand=(4.0, -6.0), hand2=(-2.0, -3.0), jaw=0.5, cut=-1),
             R(earth=1.0, hip=(0, -4.0), lean=20, hand=(4.5, -10.5), hand2=(-3.5, -8.0), jaw=1.0, claw_open=1.3),
             R(earth=0.6, lean=30, hand=(6.0, -5.0), jaw=0.3),
             R(lean=24, hand=(4.8, -5.6))]
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.08] * 6),
             ("Claw", claw, [0.1, 0.12, 0.08, 0.07, 0.12, 0.14])] + tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock, spawn)
    return sheet("FodRevenant", anims, outdir, min_cell=CELLS["FodRevenant"])


# ================================================================== FUSEBELLY: a tallow bomb on stubby legs
def fusebelly(dy=0.0, sq=1.0, lean=0.0, feet=((-2.2, 0.0), (2.2, 0.0)), fuse=1.0, whip=0.0, flick=0, eye="open",
              grin=0.5, swell=0.0, glow=0.0, tongue=0.0):
    """Body centre (0, -6.5 + dy). sq squashes it (taller > 1). whip swings the fuse forward (1 = flame at (8, -9)).
    swell 0..1 grows it before it bursts; glow 0..1 lights cracks from the fire inside."""
    r = Rig()
    ry = 4.6 * sq * (1 + swell * 0.25); rx = 4.6 / math.sqrt(sq) * (1 + swell * 0.3)
    cx, cy = lean * 0.6, -ry - 1.6 + dy
    for k, (fx, fy) in enumerate(feet):
        top = (fx * 0.8 + lean * 0.3, cy + ry - 1.0)
        z = 0.5 if k else -1.0
        r.tube([top, (fx, fy - 0.8)], [1.1, 1.0], "tallow", z, bias=-0.3 if k == 0 else -0.1)
        r.ell(fx + 0.5, fy - 0.5, 1.3, 0.7, "wick", z + 0.01, bias=0.1)
    r.ell(cx, cy, rx, ry, "tallow", 0.0)
    # wax drips running down from the crown
    for (dx, ln) in ((-2.6, 2.4), (0.8, 3.4), (2.9, 1.8)):
        x = cx + dx; y0 = cy - ry * 0.75 + abs(dx) * 0.3
        r.tube([(x, y0), (x, y0 + ln)], [0.7, 0.6], "tallow", 0.3, bias=0.35)
        r.dot(x, y0 + ln + 0.6, "tallow", 3, 0.35)
    # face: ember eyes and a carved grin lit from inside
    ey = cy - 0.6
    for k, ex in enumerate((cx + 0.6, cx + 3.0)):
        if eye == "x":
            r.dot(ex, ey, "wick", 0, 1.0)
        else:
            r.dot(ex, ey, "candle", 4 if eye == "wide" else 3, 1.0)
            if eye == "wide": r.dot(ex, ey - 1, "candle", 2, 1.0)
    gy = cy + 1.8
    w = 1.5 + grin * 1.5
    for x in range(int(round(cx + 1.8 - w)), int(round(cx + 1.8 + w)) + 1):
        r.dot(x, gy + (0 if abs(x - cx - 1.8) < w - 0.6 else -1), "candle", 2 if grin > 0.8 else 1, 1.0)
        if grin > 0.8: r.dot(x, gy + 1, "candle", 1, 1.0)
    if tongue:
        r.tube([(cx + 3.0, gy + 0.6), (cx + 3.0 + 2.5 * tongue, gy + 1.2), (cx + 3.0 + 4.5 * tongue, gy - 0.2)],
               [0.8, 0.7, 0.5], "tongue", 1.5, bias=0.1)
    if glow > 0:
        for (pts) in (((cx - 2.6, cy - 1.5), (cx - 1.6, cy + 0.4), (cx - 2.4, cy + 2.0)),
                      ((cx + 0.2, cy - 3.6), (cx + 1.0, cy - 2.2)),
                      ((cx - 0.4, cy + 3.4), (cx + 0.8, cy + 2.2), (cx + 2.4, cy + 3.0))):
            r.polyline(list(pts), "candle", 1.2, tone=3 if glow > 0.6 else 2)
    # the fuse: a braided wick from the crown; its tip sits at (0, -13) at rest (the spark overlay's point)
    if fuse > 0:
        base = (cx - 0.2, cy - ry + 0.4)
        tip0 = (0.0, -13.0 + dy * 0.5)
        tip1 = (8.0, -9.0)
        tip = (lerp(tip0[0], tip1[0], whip), lerp(tip0[1], tip1[1], whip))
        tip = (lerp(base[0], tip[0], fuse), lerp(base[1], tip[1], fuse))
        mid = ((base[0] + tip[0]) / 2 - 1.0 + whip * 1.5 + (flick % 2) * 0.5, (base[1] + tip[1]) / 2 - whip * 1.5)
        r.tube([base, mid, tip], [0.6, 0.5, 0.5], "wick", 1.5, bias=0.2)
        fx, fy = tip
        r.dot(fx, fy - 0.0, "ember", 4, 2.0)
        r.dot(fx + (1 if flick % 2 else 0), fy - 1, "fire", 3, 2.0)
        if flick in (1, 2): r.dot(fx - 1 + flick, fy - 2, "fire", 2, 2.0)
        if whip > 0.5:
            r.dots([(fx - 2.0, fy - 1.5), (fx - 4.0, fy - 2.0)], "fire", 2, 2.0)
    return r.resolve()


def fuse_scraps(k):
    r = Rig()
    for (x, y, rx, ry_) in ((-3.5, -0.8, 1.8, 0.9), (2.5, -0.7, 2.2, 1.0), (-0.5, -1.0, 1.3, 0.8), (5.5, -0.5, 1.0, 0.6)):
        r.ell(x, y, rx, ry_, "tallow", 0.0, bias=-0.15)
    r.dots([(-1.5, -0.4), (0.5, -0.5), (4.0, -0.3)], "wick", 0, 0.5)
    if k == 0:
        r.dots([(-2.0, -3.0), (1.0, -4.0), (3.5, -2.5)], "smoke", 2, 1.0)
        r.dots([(0.0, -1.8), (3.0, -1.6)], "ember", 3, 1.1)
    return r.resolve()


def fusebelly_sheet(outdir):
    F = fusebelly
    idle = [F(sq=[1.0, 0.96, 0.93, 0.96][i], dy=[0, 0.3, 0.6, 0.3][i], flick=i) for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(F(dy=-abs(math.sin(t)) * 1.3, sq=1.0 + 0.07 * math.cos(2 * t), lean=1.0, flick=i,
                     feet=((-2.2 + 1.6 * math.cos(t), -max(0, 1.2 * math.sin(t))), (2.2 - 1.6 * math.cos(t), -max(0, -1.2 * math.sin(t))))))
    lick = [F(lean=-1.0, sq=0.9, whip=-0.1, grin=0.6, flick=0),
            F(lean=1.2, sq=1.05, whip=0.6, grin=1.0, eye="wide", flick=1, tongue=0.6),
            F(lean=2.2, sq=0.95, whip=1.0, grin=1.0, eye="wide", flick=2, tongue=1.0),
            F(lean=1.2, sq=0.98, whip=0.4, grin=0.8, flick=3, tongue=0.3),
            F(lean=0.0, sq=1.0, whip=0.0, flick=0)]
    blow = [F(sq=0.86, fuse=0.9, flick=0, eye="wide", grin=0.9),
            F(sq=1.05, fuse=0.7, flick=1, swell=0.3, glow=0.3, eye="wide", grin=1.0),
            F(sq=1.0, fuse=0.5, flick=2, swell=0.55, glow=0.6, eye="wide", grin=1.0, dy=-0.5),
            F(sq=1.06, fuse=0.3, flick=3, swell=0.8, glow=1.0, eye="wide", grin=1.0, dy=-0.8),
            F(sq=1.1, fuse=0.12, flick=0, swell=1.0, glow=1.0, eye="wide", grin=1.0, dy=-1.0),
            fuse_scraps(0), fuse_scraps(1)]
    death = [F(sq=0.8, eye="x", grin=0.2, glow=0.4, flick=1, lean=-1.0),
             F(sq=0.62, eye="x", grin=0.0, fuse=0.6, flick=2, dy=0.3), fuse_scraps(0), fuse_scraps(1)]
    knock = F(sq=0.85, lean=-1.5, eye="x", grin=0.9, whip=-0.3)
    spawn = [fuse_scraps(1), F(sq=0.45, fuse=0.3, eye="x", grin=0.0), F(sq=1.3, dy=-1.5, eye="wide", grin=1.0, flick=1),
             F(sq=0.85, flick=2), F(sq=1.0, flick=3)]
    anims = [("Idle", idle, [0.15] * 4), ("Run", run, [0.065] * 6), ("Lick", lick, [0.09, 0.08, 0.1, 0.1, 0.1]),
             ("Blow", blow, [0.12, 0.14, 0.14, 0.12, 0.1, 0.12, 0.2])] + tail(idle[0], death, [0.08, 0.1, 0.12, 0.4], knock, spawn)
    return sheet("FodFusebelly", anims, outdir, min_cell=CELLS["FodFusebelly"])


# ================================================================== GARGLING: a squat stone gargoyle that spits stones
def gargling(sit=0.0, head=(5.0, -11.0), tilt=0.0, jaw=0.0, wings=0.0, feet=((-3.5, 0.0), (3.0, 0.0)), stone_at=None,
             dust=None, eye=1, crack=0, cut=None, lean=0.0):
    """Crouched on its haunches. head = the snout's root; jaw 0..1; wings 0 folded .. 1 flared."""
    r = Rig()
    bx, by = -0.5 + lean, -5.5 + sit
    # folded wings behind: two stone fans
    for k, (ang, z) in enumerate(((-120 - wings * 30, -3.0), (-92 - wings * 22, -2.0))):
        root = (bx - 1.5, by - 3.5)
        ln = 5.2 + wings * 1.8
        tips = [(root[0] + ln * f * math.cos(math.radians(ang + d)), root[1] + ln * f * math.sin(math.radians(ang + d)))
                for d, f in ((0, 1.0), (22, 0.7), (40, 0.85), (60, 0.55))]
        r.poly([root] + tips + [(bx - 4.0, by + 0.5)], "gran", z, normal=(-0.3, -0.5, 1.0), bias=-0.15 if k == 0 else 0.0)
        for t in tips[:2]:
            r.line(root[0], root[1], t[0], t[1], "gran", z + 0.01, tone=1 if k == 0 else 4)
    # haunches and body
    r.ell(bx - 1.0, by + 2.2, 4.0, 3.2, "gran", 0.0)
    r.ell(bx + 1.0, by - 1.2, 3.6, 3.8, "gran", 0.5, ang=20 + lean * 3)
    # moss on the shoulders
    r.ell(bx - 0.5, by - 4.3, 2.2, 0.9, "moss", 0.8, bias=0.2)
    r.dot(bx + 1.6, by - 4.5, "moss", 2, 0.85)
    # forelegs (stubby pillars with claws)
    for k, (fx, fy) in enumerate(feet):
        z = 1.0 if k else -0.5
        top = (bx + (2.4 if k else -2.8), by + (0.5 if k else 2.0))
        r.tube([top, (fx, fy - 0.8)], [1.4, 1.2], "gran", z, bias=-0.25 if k == 0 else 0.0)
        r.dots([(fx + 1, fy), (fx, fy), (fx - 1, fy)], "gran", 4 if k else 3, z + 0.01)
    # head: blocky brow, horns, snout, spitting jaw
    hx, hy = head
    T = Xf(tilt, (hx - 2, hy + 1))
    r.ell(*T(hx - 1.5, hy), 3.0, 2.6, "gran", 2.0, ang=tilt)
    r.poly([T(hx - 1.0, hy - 1.8), T(hx + 2.6, hy - 1.0), T(hx + 2.8, hy + 0.8), T(hx - 0.5, hy + 0.9)], "gran", 2.1,
           normal=(0.2, -0.6, 1.0))
    r.poly([T(hx - 0.8, hy + 0.9 + jaw * 0.4), T(hx + 2.4, hy + 1.0 + jaw * 1.6), T(hx + 1.8, hy + 2.0 + jaw * 2.0),
            T(hx - 1.0, hy + 2.0)], "gran", 2.05, normal=(0.0, 0.6, 1.0), bias=-0.15)
    if jaw > 0.25:
        r.poly([T(hx - 0.2, hy + 1.0), T(hx + 2.4, hy + 1.0), T(hx + 2.0, hy + 1.0 + jaw * 1.4)], "mouth", 2.08, flat=1)
        r.dot(*T(hx + 2.2, hy + 1.1), "bone", 3, 2.09)
    for k, d in enumerate((-1, 1)):    # horns sweeping back
        x0, y0 = T(hx - 2.5 + d * 0.6, hy - 1.0)
        # tall horns, rising and curling back: the gargoyle's silhouette
        r.tube(chain(x0, y0, [(1.4, -92 + tilt), (1.3, -115 + tilt), (1.0, -155 + tilt)]), [1.1, 0.9, 0.6, 0.4], "gran",
               1.8 if k else 2.2, bias=0.35 if k else -0.1)
    ex, ey = T(hx + 0.4, hy - 0.8)
    r.dot(ex, ey, "ember", 4 if eye else 2, 2.3)
    if eye: r.dot(ex - 1, ey, "ember", 2, 2.3)
    if crack:
        r.polyline([(bx - 1.0, by - 3.0), (bx + 0.4, by - 1.0), (bx - 0.3, by + 1.4), (bx + 1.0, by + 3.0)], "mouth", 2.5, tone=1)
    if stone_at:
        x, y, k = stone_at
        r.ell(x, y, 1.3 + k * 0.2, 1.1 + k * 0.2, "gran", 3.0, bias=0.3)
    if dust is not None: puff_stone(r, *dust)
    rs = r.resolve()
    if cut is not None:
        rs.px = {k: v for k, v in rs.px.items() if k[1] >= cut}
        rs.tones = {k: v for k, v in rs.tones.items() if k in rs.px}
    return rs


def puff_stone(r, x, y, k):
    for side in (-1, 1):
        for i in range(3 - k):
            r.ell(x + side * (2 + i * 2 + k * 1.5), y - (i % 2) - (1 if k else 0), 1.2 - 0.3 * k, 0.8, "smoke", 5.0, flat=2 if i else 3)


def rubble(k):
    r = Rig()
    for (x, y, rr) in ((-4.0, -1.2, 1.8), (-1.0, -1.6, 2.4), (2.4, -1.3, 2.0), (5.0, -0.8, 1.2), (-6.0, -0.6, 1.0)):
        r.ell(x, y, rr, rr * 0.75, "gran", 0.0, bias=0.1)
    r.dot(2.6, -2.2, "ember", 2 if k == 0 else 1, 1.0)
    r.ell(-1.5, -1.8, 1.0, 0.5, "moss", 0.5, bias=0.2)
    if k == 0: r.dots([(-3, -4), (1, -5), (4, -3.5)], "smoke", 2, 1.0)
    return r.resolve()


def gargling_sheet(outdir):
    G = gargling
    idle = [G(sit=[0, 0.2, 0.4, 0.2][i], head=(5.0, -11.0 + [0, 0.2, 0.4, 0.2][i]), wings=[0, 0.05, 0.1, 0.05][i], eye=i != 2)
            for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(G(sit=-0.4 * abs(math.sin(t)), lean=0.5, head=(5.5, -11.2 - 0.4 * abs(math.sin(t))), wings=0.1 + 0.1 * math.sin(t),
                     feet=((-3.5 + 1.2 * math.cos(t), -max(0, math.sin(t))), (3.0 - 1.2 * math.cos(t), -max(0, -math.sin(t))))))
    spit = [G(head=(4.0, -11.6), tilt=-14, jaw=0.2, wings=0.2), G(head=(3.6, -12.0), tilt=-24, jaw=0.6, wings=0.35),
            G(head=(6.0, -10.6), tilt=8, jaw=1.0, wings=0.5, stone_at=(8.0, -10.5, 1)),
            G(head=(6.2, -10.5), tilt=10, jaw=1.0, wings=0.4), G(head=(5.4, -10.8), tilt=4, jaw=0.5, wings=0.2), G()]
    fan = [G(head=(4.0, -11.4), tilt=-10, jaw=0.2, wings=0.3), G(head=(3.2, -12.2), tilt=-28, jaw=0.5, wings=0.7),
           G(head=(3.0, -12.4), tilt=-32, jaw=0.9, wings=1.0, sit=0.3),
           G(head=(6.2, -10.4), tilt=12, jaw=1.0, wings=1.0, stone_at=(8.0, -11.5, 0)),
           G(head=(6.5, -10.2), tilt=14, jaw=1.0, wings=0.8, dust=(0.0, -0.5, 0)),
           G(head=(5.6, -10.8), tilt=6, jaw=0.4, wings=0.4, dust=(0.0, -0.5, 1)), G(wings=0.1)]
    death = [G(crack=1, eye=0, jaw=0.7, tilt=-10), G(crack=1, eye=0, sit=1.5, head=(4.5, -9.0), tilt=20, jaw=0.4),
             rubble(0), rubble(1)]
    knock = G(head=(3.5, -11.8), tilt=-22, jaw=0.6, wings=0.6, eye=0)
    spawn = [rubble(1), G(cut=-3, sit=2.0), G(sit=-1.0, wings=1.0, head=(5.0, -12.2), jaw=0.8, dust=(0.0, -0.5, 0)),
             G(sit=0.6, wings=0.3, dust=(0.0, -0.5, 1)), G()]
    anims = [("Idle", idle, [0.25, 0.2, 0.25, 0.2]), ("Run", run, [0.1] * 6), ("Spit", spit, [0.1, 0.12, 0.08, 0.08, 0.12, 0.14]),
             ("Fan", fan, [0.12, 0.12, 0.1, 0.1, 0.08, 0.14, 0.14])] + tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock, spawn)
    return sheet("FodGargling", anims, outdir, min_cell=CELLS["FodGargling"])


# ================================================================== POPPET: a stitched voodoo doll stuck with pins
PIN_HEADS = ("thread", "hexv", "brass")


def poppet(dy=0.0, lean=0.0, sq=1.0, feet=((-2.0, 0.0), (2.0, 0.0)), hand=(5.0, -6.0), hand2=(-4.0, -6.5), pin=0.0,
           eye=1, flop=0.0, hex_=0, droop=0.0, smear=False):
    """Body: a burlap sack (0, -6) with a big round head; the near hand carries a long pin at angle `pin` (deg)."""
    r = Rig()
    cx, cy = lean * 0.5, -4.8 + dy
    hx, hy = cx + 0.6 + lean * 0.4, cy - 5.0 * sq
    # stub legs
    for k, (fx, fy) in enumerate(feet):
        z = 0.5 if k else -1.0
        r.tube([(cx + (1.2 if k else -1.2), cy + 2.0), (fx, fy - 0.7)], [1.1, 1.0], "burlap", z, bias=-0.3 if k == 0 else -0.05)
    # far arm
    r.tube([(cx - 1.8, cy - 1.0), hand2], [1.0, 0.9], "burlap", -1.5, bias=-0.3)
    # body sack, stitched seam down the front
    r.ell(cx, cy, 3.3, 3.4 * sq, "burlap", 0.0)
    for y in range(int(cy - 2), int(cy + 3), 2):
        r.dot(cx + 1.6, y, "thread", 2, 0.1)
    r.dot(cx - 0.6, cy + 0.6, "thread", 3, 0.1)     # a patched-on red heart
    r.dot(cx - 1.2, cy + 0.0, "thread", 2, 0.1)
    # head: a pale burlap face, one big button eye, one stitched X eye, a stitched mouth; dark yarn hair on the crown,
    # two pins through it
    T = Xf(droop * 30, (hx, hy + 3))
    r.ell(*T(hx, hy - 0.2), 3.6, 3.4, "burlap", 1.0, bias=0.45)
    for i, (dx, ang) in enumerate(((-2.0, -120), (-0.2, -95))):
        x0, y0 = T(hx + dx, hy - 3.2)
        r.tube(chain(x0, y0, [(1.0, ang - flop * 30), (0.8, ang - 40 - flop * 30)]), [0.6, 0.5, 0.4], "yarn", 0.8)
    r.ell(*T(hx - 1.2, hy - 3.0), 1.8, 0.8, "yarn", 0.85)
    bx_, by_ = T(hx + 2.0, hy - 0.6)                                   # button eye: dark disc, a pale rim, a glint
    for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        r.dot(bx_ + dx, by_ + dy, "button", 0, 1.1)
    r.dot(bx_, by_, "button", 4 if eye else 1, 1.15)
    xx, xy = T(hx - 1.0, hy - 0.4)                                     # X eye, two dark stitches
    r.dot(xx - 1, xy - 1, "yarn", 0, 1.1); r.dot(xx + 1, xy + 1, "yarn", 0, 1.1)
    r.dot(xx + 1, xy - 1, "yarn", 0, 1.1); r.dot(xx - 1, xy + 1, "yarn", 0, 1.1)
    r.dot(xx, xy, "yarn", 0, 1.1)
    mx, my = T(hx + 0.6, hy + 1.8)                                     # stitched mouth
    r.line(mx - 1.5, my, mx + 1.5, my, "yarn", 1.1, tone=0)
    r.dot(mx - 1, my - 1, "yarn", 1, 1.12); r.dot(mx + 1, my - 1, "yarn", 1, 1.12)
    for k, (dx, dy_, ang) in enumerate(((-3.0, -1.0, -160), (2.4, -2.6, -45))):
        x0, y0 = T(hx + dx, hy + dy_)
        a_ = math.radians(ang + droop * 20)
        x1, y1 = x0 + 2.0 * math.cos(a_), y0 + 2.0 * math.sin(a_)
        r.line(x0, y0, x1, y1, "iron", 1.3, tone=3)
        r.dot(x1, y1, PIN_HEADS[k], 3, 1.35)
    # near arm with the long pin
    r.tube([(cx + 1.8, cy - 1.2), hand], [1.0, 0.9], "burlap", 2.0, bias=0.05)
    a = math.radians(pin)
    px1, py1 = hand[0] + 5.0 * math.cos(a), hand[1] + 5.0 * math.sin(a)
    px0, py0 = hand[0] - 1.6 * math.cos(a), hand[1] - 1.6 * math.sin(a)
    r.line(px0, py0, px1, py1, "iron", 2.2, tone=3)
    r.dot(px0, py0, "hexv", 3, 2.3)
    if smear:
        r.line(px1 - 3.0 * math.cos(a), py1 - 3.0 * math.sin(a) - 1.5, px1, py1 - 1.0, "hexv", 2.1, tone=2)
    if hex_:
        for (x, y) in ((px1 + 1, py1 - 1), (px1 + 1, py1 + 1), (px1 + 2, py1)):
            r.dot(x, y, "hexv", 3 if hex_ > 1 else 2, 2.4)
    return r.resolve()


def poppet_flat(k):
    r = Rig()
    r.ell(0.0, -1.2, 4.0, 1.4, "burlap", 0.0, bias=-0.05)
    r.ell(5.0, -1.5, 2.6, 1.6, "burlap", 0.2)
    r.dot(5.8, -1.8, "button", 1, 0.3)
    r.tube([(-3.5, -0.8), (-6.5, -0.6)], [0.9, 0.8], "burlap", 0.1, bias=-0.2)
    r.line(1.0, -0.5, 1.0 + (5 if k else 4), -2.0 - k, "iron", 0.4, tone=3)
    for (x, y, c) in ((-1.5, -1.6, "thread"), (2.5, -2.6, "hexv"), (-4.0, -2.0, "thread")):
        r.dot(x, y, c, 2 if k else 3, 0.6)
    return r.resolve()


def poppet_sheet(outdir):
    Pp = poppet
    idle = [Pp(dy=[0, -0.3, -0.6, -0.3][i], droop=[0, 0.1, 0.2, 0.1][i], flop=[0, 0.3, 0.6, 0.3][i], pin=-50 + 4 * i,
               hand=(4.6, -6.0 + [0, -0.3, -0.6, -0.3][i])) for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(Pp(dy=-abs(math.sin(t)) * 1.2, lean=1.0, droop=-0.1 + 0.15 * math.sin(t), flop=0.5 + 0.5 * math.sin(t),
                      feet=((-2.0 + 1.5 * math.cos(t), -max(0, math.sin(t))), (2.0 - 1.5 * math.cos(t), -max(0, -math.sin(t)))),
                      pin=-30, hand=(4.6, -5.0)))
    jab = [Pp(pin=-110, hand=(2.0, -9.5), lean=-1.0, droop=-0.2), Pp(pin=-150, hand=(0.5, -11.0), lean=-1.6, droop=-0.3, flop=0.6),
           Pp(pin=10, hand=(5.5, -6.5), lean=1.5, droop=0.1, smear=True), Pp(pin=20, hand=(6.5, -4.6), lean=2.2, droop=0.2, hex_=2),
           Pp(pin=10, hand=(5.5, -5.0), lean=1.2, hex_=1), Pp(pin=-40, hand=(4.6, -6.0))]
    death = [Pp(droop=-0.6, eye=0, lean=-1.5, pin=-150, hand=(1.0, -9.0)), Pp(droop=1.4, eye=0, dy=1.5, sq=0.7, pin=60, hand=(4.0, -2.0)),
             poppet_flat(0), poppet_flat(1)]
    knock = Pp(droop=-0.7, lean=-1.8, eye=0, pin=-130, hand=(1.5, -8.0), flop=1.0)
    spawn = [poppet_flat(1), Pp(sq=0.55, dy=2.0, droop=1.0, eye=0, pin=40, hand=(4.0, -2.5)),
             Pp(dy=-1.5, sq=1.1, droop=-0.3, flop=1.0, pin=-100, hand=(3.0, -10.0)), Pp(dy=0.4, sq=0.9, pin=-60), Pp(pin=-50)]
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.07] * 6),
             ("Jab", jab, [0.1, 0.1, 0.1, 0.07, 0.12, 0.12])] + tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock, spawn)
    return sheet("FodPoppet", anims, outdir, min_cell=CELLS["FodPoppet"])


# ================================================================== MIMIC: a treasure chest with teeth on stubby legs
def mimic(dy=0.0, lid=0.0, lean=0.0, feet=((-4.0, 0.0), (4.0, 0.0)), tongue=0.0, coins=None, eye=1, sq=1.0, spill=0,
          shut=False, broken=0):
    """Chest box 13 wide; lid opens `lid` 0..1 (hinged at the back); tongue 0..1 lolls out."""
    r = Rig()
    w, h = 12.0, 5.6 * sq
    x0, y0 = -6.0 + lean, -1.6 + dy
    for k, (fx, fy) in enumerate(feet):            # stubby clawed legs
        z = -1.0 if k == 0 else 0.5
        r.tube([(fx * 0.8 + lean, y0 - 0.5), (fx, fy - 0.6)], [1.2, 1.0], "chest", z, bias=-0.3)
        r.dots([(fx - 1, fy), (fx, fy), (fx + 1, fy)], "bone", 2, z + 0.01)
    # box: front, top lip, side; iron bands and corner brass
    bl, br, tr, tl = J_box(r, x0, y0, w, h, 2.5, "chest", 0.0)
    for bx_ in (x0 + 2.0, x0 + w - 2.0):
        r.line(bx_, y0 - 0.5, bx_, y0 - h + 0.5, "iron", 0.1, tone=2)
    r.line(x0 + 0.5, y0 - h + 1.0, x0 + w - 0.5, y0 - h + 1.0, "iron", 0.1, tone=3)
    # keyhole plate
    r.ell(x0 + w / 2, y0 - h / 2 + 0.3, 1.3, 1.5, "brass", 0.2)
    r.dot(x0 + w / 2, y0 - h / 2 + 0.5, "mouth", 0, 0.3)
    # inside of the lid / mouth
    a = math.radians(-lid * 75)
    hinge = (x0 + 0.5, y0 - h)
    L = w + 0.5
    lid_end = (hinge[0] + L * math.cos(a), hinge[1] + L * math.sin(a))
    if lid > 0.05:
        r.poly([hinge, (x0 + w - 0.5, y0 - h + 0.5), lid_end], "mouth", -0.5, flat=1)
        if tongue:
            r.tube([(x0 + 4.0, y0 - h - 0.5), (x0 + 8.0, y0 - h - 0.5 - tongue), (x0 + 11.5 + tongue * 2, y0 - h + tongue * 1.5)],
                   [1.0, 0.9, 0.7], "tongue", 0.6, bias=0.2)
        # lower teeth on the box rim
        for x in range(int(x0 + 2), int(x0 + w), 2):
            r.dot(x, y0 - h - 1, "bone", 4, 0.7)
        # the eye in the dark
        if eye: r.dot(x0 + 3.5, y0 - h - 1.5 - lid * 1.5, "candle", 4, -0.4)
    # lid: a curved box top rotating about the back hinge
    pts = []
    for i in range(7):
        t = i / 6.0
        u, v = L * t, -2.8 * math.sin(t * math.pi) ** 0.6 - 1.2
        pts.append((hinge[0] + u * math.cos(a) - v * math.sin(a), hinge[1] + u * math.sin(a) + v * math.cos(a)))
    pts2 = [(hinge[0] + L * math.cos(a), hinge[1] + L * math.sin(a))]
    r.poly(pts + pts2[::-1] + [hinge], "chest", 1.0 if lid < 0.05 else 0.5, normal=(-0.2, -0.8, 1.0), curve=0.3)
    for t in (0.18, 0.82):
        i0 = int(t * 6)
        r.line(*pts[i0], hinge[0] + L * t * math.cos(a), hinge[1] + L * t * math.sin(a), "iron", 1.1, tone=3)
    if lid > 0.05:
        # upper teeth hanging from the lid edge
        for t in (0.3, 0.5, 0.7, 0.9):
            ex, ey = hinge[0] + L * t * math.cos(a), hinge[1] + L * t * math.sin(a)
            r.dot(ex + 0.5 * math.sin(a), ey + 1.0, "bone", 4, 1.2)
    else:
        r.dot(x0 + 3.5, y0 - h - 0.4, "candle", 4 if eye else 1, 1.3)   # shut: the eye peeks through the seam
    if coins:
        for (x, y, k) in coins:
            r.ell(x, y, 1.1, 0.8 if k else 1.1, "brass", 3.0, bias=0.3)
    if spill:
        for (x, y) in ((x0 + w + 1.5, -0.8), (x0 + w + 3.5, -0.6), (x0 - 1.5, -0.7))[:spill]:
            r.ell(x, y, 1.1, 0.7, "brass", 3.0, bias=0.3)
    return r.resolve()


def J_box(r, x0, y0, w, h, d, mat, z):
    import jinx_v2_rigs as J
    return J.box3(r, x0, y0, w, h, d, mat, z)


def mimic_sheet(outdir):
    M = mimic
    idle = [M(lid=[0.0, 0.08, 0.2, 0.08][i], dy=[0, 0, -0.3, 0][i], eye=i != 1) for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(M(dy=-abs(math.sin(t)) * 1.2, lean=0.5, lid=0.12 + 0.12 * abs(math.cos(t)), tongue=0.6,
                     feet=((-4.0 + 1.5 * math.cos(t), -max(0, math.sin(t))), (4.0 - 1.5 * math.cos(t), -max(0, -math.sin(t))))))
    chomp = [M(lid=0.35, lean=-1.0, sq=0.95), M(lid=0.9, lean=-1.5, dy=-0.5, tongue=0.5), M(lid=1.0, lean=1.5, dy=-1.0, tongue=1.0),
             M(lid=0.0, lean=2.5, dy=0.0, sq=0.9), M(lid=0.15, lean=1.0, tongue=0.4), M(lid=0.05)]
    spit = [M(lid=0.3, sq=0.92), M(lid=0.6, sq=0.85, dy=0.3), M(lid=0.95, sq=1.08, dy=-0.8, coins=[(1.0, -10.0, 0)]),
            M(lid=0.9, sq=1.05, dy=-0.6, coins=[(4.5, -9.0, 1), (6.0, -11.0, 0)]), M(lid=0.4, tongue=0.6), M(lid=0.1)]
    death = [M(lid=0.7, lean=-1.5, eye=0, tongue=1.0), M(lid=1.0, sq=0.8, eye=0, tongue=1.2, spill=1),
             M(lid=1.0, sq=0.6, dy=0.5, eye=0, tongue=1.2, spill=3), M(lid=1.0, sq=0.6, dy=0.5, eye=0, tongue=1.4, spill=3)]
    knock = M(lid=0.6, lean=-1.8, tongue=0.8, eye=0)
    spawn = [M(lid=0.0, sq=0.4, eye=0, feet=((-3, 0), (3, 0))), M(lid=0.0, sq=0.75, eye=1), M(lid=0.8, sq=1.15, dy=-1.5, tongue=1.0),
             M(lid=0.0, sq=0.9), M(lid=0.05)]
    anims = [("Idle", idle, [0.3, 0.15, 0.2, 0.15]), ("Run", run, [0.08] * 6), ("Chomp", chomp, [0.1, 0.1, 0.1, 0.06, 0.12, 0.14]),
             ("Spit", spit, [0.1, 0.1, 0.1, 0.08, 0.12, 0.14])] + tail(idle[0], death, [0.08, 0.12, 0.14, 0.4], knock, spawn)
    return sheet("FodMimic", anims, outdir, min_cell=CELLS["FodMimic"])


JOBS = [("FodKeener", keener_sheet), ("FodRevenant", revenant_sheet), ("FodFusebelly", fusebelly_sheet),
        ("FodGargling", gargling_sheet), ("FodPoppet", poppet_sheet), ("FodMimic", mimic_sheet)]


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in a:
        i = a.index("--only"); only = set(a[i + 1].split(",")); del a[i:i + 2]
    outdir = a[0] if a else OUT
    os.makedirs(outdir, exist_ok=True)
    for n, fn in JOBS:
        if only is None or n in only:
            fn(outdir)


if __name__ == "__main__":
    main()
