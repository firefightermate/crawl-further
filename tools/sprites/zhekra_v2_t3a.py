"""Zhekra tier 3, first half: Brood Mother, Acid Bloater, Acid Mantis, Pit Antlion, Amber Hive, Hunting Wasp. Built
through zhekra_v2_rigs.py. Same renderer and rules as the lower tiers. T3 idle limit 42 x 40, and never a smaller
footprint than the v1 sheet it replaces."""
import math, random
from zhekra_v2_rigs import (ZRig, Rig, Xf, chain, ik, lerp, segs, leg, gait6, legs6, antenna, wing, wing_blur, eye, mandible,
                            drip, puddle, dust, smear, splat, ground_shadow, arc_pts, sheet, tail_anims, SYNC, NOTES, line_px)
from zhekra_v2_t1 import banded
from zhekra_v2_t2 import walk_feet, scythe


def bez(p0, p1, p2, n=6):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [k / float(n) for k in range(n + 1)]]


# ================================================================== BROOD MOTHER: the queen over her egg-heavy abdomen
def mother(bob=0.0, lean=0.0, ph=0.0, wave=0.0, crest=1.0, arms=0.0, mouth=0.0, rear=0.0, i=0, n=6, stride=0.0,
           wings=0.0, hurt=False, dead=False, spew=None, eggs=None, extra=None, dust_at=None, glow=0.0):
    r = ZRig(1.14)
    T = Xf(lean, (4.0, -8.0))
    # the abdomen: a long segmented egg sac dragged behind, rising to the waist
    sp = []
    for k in range(7):
        t = k / 6.0
        x = lerp(-19.0, 2.0, t) + math.sin(ph + k) * wave * 0.4
        R = 4.4 + 4.6 * math.sin(math.pi * min(1.0, t * 0.9 + 0.12))
        y = -R + 0.5 - t * t * 3.0 * (1 + rear * 0.3) + math.sin(ph + k * 0.9) * wave * 0.5
        sp.append((x, y, R))
    for k, (x, y, R) in enumerate(sp):
        r.ell(x, y, 2.9 if k < 6 else 3.2, R, "cream", 0.0 + k * 0.004, bias=0.05)
    for k, (x, y, R) in enumerate(sp[1:-1]):
        # amber veins, and the eggs packed under the skin: pale ovals ringed in amber
        r.polyline([(x - 1.6, y - R * 0.7), (x - 0.4, y - R * 0.15), (x + 0.6, y + R * 0.45)], "amber", 0.05, tones=[3, 2])
        for j, (ex, ey) in enumerate(((0.6, 0.15), (-0.8, 0.55))):
            if (k + j) % 2: continue
            r.ell(x + ex * 1.6, y + R * ey, 1.5, 1.2, "amber", 0.055, flat=2)
            r.ell(x + ex * 1.6 - 0.2, y + R * ey - 0.2, 1.0, 0.8, "cream", 0.056, flat=4)
    tail = (sp[0][0] - 2.0, sp[0][1] + 1.0)
    r.ell(tail[0], tail[1], 1.6, 1.8, "cream", -0.01, bias=-0.1)
    # walking legs under the thorax (4) and folded wings over the waist
    hips = [T(4.0, -7.0 + bob - rear), T(6.0, -7.5 + bob - rear), T(4.6, -7.4 + bob - rear), T(6.6, -7.8 + bob - rear)]
    base = [(1.0, 0.0), (9.0, 0.0), (2.5, 0.0), (10.5, 0.0)]
    feet = walk_feet(i, n, base, stride, lift=1.4) if stride else base
    if dead: feet = [(h[0] + [-2, 2, -1, 3][k], h[1] - 1.0) for k, h in enumerate(hips)]
    for k in (2, 3): leg(r, hips[k], feet[k], 4.2, 4.6, -1.0, "dchit", near=False, bend=-1 if k == 2 else 1, rad=0.45)
    root = T(5.0, -15.0 + bob - rear)
    wing(r, root, -165 + wings * 40, 12.0, 4.4, -0.5, near=False)
    wing(r, (root[0] + 0.8, root[1] + 0.6), -158 + wings * 50, 11.0, 4.0, 0.9, near=True)
    if wings > 0.5: wing_blur(r, root, -170, -120, 9.0, -0.6, n=2)
    # the slender upper body
    th = [T(3.5, -9.0 + bob - rear), T(6.0, -15.0 + bob - rear), T(7.5, -21.5 + bob - rear * 1.4)]
    r.tube(th, [3.8, 3.0, 2.3], "chit", 1.0, bias=0.08)
    for k in range(4):
        t = 0.15 + k * 0.22
        px, py = lerp(th[0][0], th[2][0], t), lerp(th[0][1], th[2][1], t)
        r.ell(px + 0.6, py, 2.4 - 0.3 * k, 0.8, "royal", 1.01 + k * 0.001, bias=0.15)
    r.ell(th[2][0] - 0.4, th[2][1] + 1.2, 3.0, 1.4, "cream", 1.02, bias=0.2)   # the pale ruff under her head
    for k in (0, 1): leg(r, hips[k], feet[k], 4.2, 4.6, 1.6, "chit", near=True, bend=-1 if k == 0 else 1, rad=0.55)
    # raptorial arms
    sh = T(7.0, -18.5 + bob - rear * 1.3)
    for k in (1, 0):
        hand = (sh[0] + 4.5 + arms * 2.0 - k, sh[1] + 2.5 - arms * 4.0 + k)
        el = ik(sh[0], sh[1], hand[0], hand[1], 3.0, 3.4, 1)
        r.tube([sh, el, hand], [1.1, 0.9, 0.6], "chit" if k == 0 else "dchit", 1.3 if k == 0 else 0.4)
        r.dot(hand[0] + 0.6, hand[1] + 0.4, "royal", 3, 1.31)
    # head and the crown crest
    hx, hy = th[2][0] + 2.0, th[2][1] - 2.4
    r.ell(hx, hy, 2.6, 2.3, "chit", 1.4, bias=0.1)
    r.ell(hx + 1.6, hy + 1.2, 1.5, 1.0, "cream", 1.41, bias=0.0)
    eye(r, hx + 0.6, hy - 0.4, 1.45, glint=not dead, big=True)
    if hurt and not dead: r.dot(hx + 0.6, hy - 0.4, "white", 2, 1.46)
    # the crown: a gold band round the head with five spires tipped in jelly, and two long antennae sweeping back
    r.ell(hx - 0.4, hy - 1.8, 2.6, 1.1, "royal", 1.43, bias=0.2)
    for k, a in enumerate((-140, -115, -92, -70, -48)):
        L = (2.4 + (1.4 if k == 2 else 0.8 if k in (1, 3) else 0.0)) * crest
        bx, by = hx - 0.4 + 2.2 * math.cos(math.radians(a)), hy - 2.2 + 1.0 * math.sin(math.radians(a))
        tip = (bx + L * math.cos(math.radians(a)), by + L * math.sin(math.radians(a)))
        r.tube([(bx, by), tip], [0.7, 0.35], "royal", 1.44)
        r.dot(tip[0], tip[1], "jelly", 4 if k == 2 else 3, 1.45)
    for k, (a0, curl) in enumerate(((-120, -70), (-100, -60))):
        pts = chain(hx + 0.4 - k, hy - 2.6, [(3.0 * crest, a0), (3.0 * crest, a0 + curl * 0.5), (2.6 * crest, a0 + curl)])
        r.polyline(pts, "royal", 1.38 - k * 0.02, tones=[2 - k, 1, 1])
        for (px, py) in pts[1:]:
            r.dot(px - 1, py, "royal", 1, 1.38 - k * 0.02)   # the feathered barbs
    # mouthparts
    mandible(r, (hx + 2.4, hy + 1.6), 50 + 30 * mouth, 2.4, -50, 1.42, mat="amber", rad=0.5)
    mouth_pt = (hx + 3.2, hy + 1.0)
    if spew:
        for (dx, dy, kk) in spew:
            r.ell(mouth_pt[0] + dx, mouth_pt[1] + dy, 1.3 - kk * 0.2, 1.5, "aglow", 3.0, flat=3)
    if eggs:
        for (ex, ey) in eggs:
            r.ell(tail[0] + ex, tail[1] + ey - 0.6, 2.2, 2.8, "cream", 2.0, bias=0.2)
            r.dot(tail[0] + ex - 0.6, tail[1] + ey - 1.6, "cream", 4, 2.01)
            r.dot(tail[0] + ex + 0.6, tail[1] + ey + 0.2, "aglow", 3, 2.01)
    if glow:
        for k in range(5):
            a = k / 5.0 * math.tau + glow
            r.dot(hx + 7 * math.cos(a), hy + 4 * math.sin(a), "jelly", 3, 4.0)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, (hx, hy), mouth_pt, tail)
    return r.resolve()


def mother_sheet(outdir):
    M = mother
    idle = [M(bob=[0, 0.3, 0.6, 0.3][i], ph=i * 0.6, wave=0.6, arms=[0, 0.1, 0.2, 0.1][i], crest=[1.0, 1.02, 1.05, 1.02][i]) for i in range(4)]
    run = [M(i=i, n=6, stride=2.0, ph=i / 6 * math.tau, wave=1.4, bob=0.4 * abs(math.sin(i / 6 * math.tau)), lean=4, arms=0.2) for i in range(6)]
    # Rain: rear and draw breath (0-2), SPEW three drops up (3), they rise (4, 5), settle (6, 7)
    rain = [M(rear=0.8, lean=-4, mouth=0.3, arms=0.4), M(rear=1.6, lean=-8, mouth=0.6, arms=0.8), M(rear=2.2, lean=-10, mouth=0.9, arms=1.0),
            M(rear=1.8, lean=-6, mouth=1.0, arms=0.6, spew=[(1.5, -2.0, 0)]),
            M(rear=1.4, lean=-4, mouth=0.8, spew=[(2.5, -6.0, 0), (0.5, -4.0, 1)]),
            M(rear=1.0, lean=-2, mouth=0.6, spew=[(3.0, -10.0, 1), (0.0, -8.0, 1), (5.0, -6.0, 1)]),
            M(rear=0.4, mouth=0.3), M()]
    # Call: the crest flares and the wings buzz (0-3, the call at 2), eggs drop from the tail (4, 5), settle (6, 7)
    call = [M(crest=1.1, wings=0.3, rear=0.6, mouth=0.5), M(crest=1.25, wings=0.8, rear=1.2, mouth=1.0, arms=0.8),
            M(crest=1.3, wings=1.0, rear=1.4, mouth=1.0, arms=1.0, glow=0.0), M(crest=1.25, wings=0.8, rear=1.2, mouth=0.8, glow=0.6),
            M(crest=1.1, wings=0.4, ph=1.0, wave=1.0, eggs=[(-1.0, -1.0)]), M(crest=1.05, ph=2.0, wave=1.0, eggs=[(-2.0, 0.0), (1.5, 0.0)]),
            M(ph=2.5, wave=0.6), M()]
    d = [M(hurt=True, rear=1.5, lean=-8, arms=1.0, mouth=1.0), M(hurt=True, rear=0.5, lean=10, bob=2.0, arms=0.4, wings=0.2),
         M(dead=True, lean=35, bob=4.0, crest=0.8, dust_at=(8, 0, 0)), M(dead=True, lean=42, bob=5.0, crest=0.8)]
    knock = M(hurt=True, rear=1.8, lean=-10, arms=1.0, mouth=0.9)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.1] * 6),
             ("Rain", rain, [0.12, 0.1, 0.1, 0.06, 0.08, 0.1, 0.12, 0.12]),
             ("Call", call, [0.1, 0.1, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])]
    anims += tail_anims(idle[0], d, [0.12, 0.14, 0.14, 0.5], knock)
    return sheet("ZhkMother", anims, outdir, scale=5)


SYNC["ZhkMother"] = {"Rain": [("SPEW: three drops go up from the mouth at (13, -22); they fall on and by the hero", 3)],
                     "Call": [("CALL: the frenzy pheromone", 2), ("egg 1 at the tail (-21, -2)", 4), ("egg 2", 5)]}
NOTES["ZhkMother"] = "Royal Jelly is drawn by FxZhkJelly (the thread from her mouth at (13, -22) to the larva) and FxZhkJellyGlow."


# ================================================================== ACID BLOATER: a floating bag of acid
def bloater(size=1.0, bob=0.0, tilt=0.0, ph=0, open_=0.0, legs=0.0, mouth=0.0, limp=0.0, hurt=False, dead=False,
            streak=0, mist=0, bubble=None, extra=None, shadow=True, alt=4.0, squash=0.0):
    r = ZRig(1.0)
    R = 6.0 + 6.6 * size
    cy = -alt - R * (1.0 - squash * 0.3) + bob + limp * 3.0
    if shadow: ground_shadow(r, 0.0, R * 0.7, h=1.2)
    T = Xf(tilt, (0.0, cy))
    c = T(0.0, cy)
    Rx, Ry = R * (1.0 + squash * 0.2), R * (1.0 - squash * 0.3)
    # stubby wings on the back, far too small to lift it (it floats on its own gas)
    wroot = (c[0] - Rx * 0.25, c[1] - Ry * 0.9)
    wing(r, wroot, -150 + (ph % 2) * 20, 6.5 + 2.0 * size, 3.2, -0.5, near=False)
    wing(r, (wroot[0] + 1.5, wroot[1] + 0.5), -132 + (ph % 2) * 25, 6.0 + 2.0 * size, 3.0, 0.4, near=True)
    r.ell(c[0], c[1], Rx, Ry, "bloat", 0.0, ang=tilt, bias=0.1)
    # the acid showing through the stretched skin
    r.ell(c[0] + R * 0.12, c[1] + R * 0.28, R * 0.55, R * 0.42, "aglow", 0.01, flat=1 if size < 0.6 else 2)
    r.ell(c[0] + R * 0.2, c[1] + R * 0.38, R * 0.3, R * 0.2, "aglow", 0.011, flat=2 if size < 0.6 else 3)
    # veins: branching dark lines spreading from the crown of the bag
    rnd = random.Random(12)
    top = (c[0] - Rx * 0.2, c[1] - Ry * 0.55)
    for k in range(7):
        a = math.radians(-170 + k * 50 + rnd.uniform(-10, 10))
        pts = [top]
        x, y = top
        for j in range(3):
            a += math.radians(rnd.uniform(-25, 25))
            x += math.cos(a) * R * 0.32; y += math.sin(a) * R * 0.32
            if ((x - c[0]) / Rx) ** 2 + ((y - c[1]) / Ry) ** 2 > 0.88: break
            pts.append((x, y))
        if len(pts) > 1: r.polyline(pts, "bloat", 0.02, tones=[1] * (len(pts) - 1))
        if len(pts) > 2:
            fx, fy = pts[2]
            r.line(fx, fy, fx + math.cos(a + 0.9) * 2.0, fy + math.sin(a + 0.9) * 2.0, "bloat", 0.02, tone=1)
    # what is left of its carapace: dark plates pulled apart over the skin
    for k, (u, v) in enumerate(((-0.55, -0.15), (-0.2, -0.75), (0.35, -0.6), (-0.65, 0.4), (0.55, 0.15))):
        px, py = c[0] + Rx * u, c[1] + Ry * v
        r.poly([(px - 1.6, py - 0.8), (px + 1.2, py - 1.2), (px + 1.6, py + 0.6), (px - 1.0, py + 1.0)], "ochit", 0.03,
               normal=(-0.3, -0.5, 0.8))
    # stretch-shine on the lit side
    r.ell(c[0] - R * 0.42, c[1] - R * 0.45, R * 0.24, R * 0.14, "bloat", 0.04, flat=4)
    r.dot(c[0] - R * 0.15, c[1] - R * 0.62, "white", 3, 0.045)
    # spiracles along the side, rimmed in chitin (they open to whistle and zip)
    for k in range(5):
        a = math.radians(140 + k * 22)
        sx, sy = c[0] + Rx * 0.9 * math.cos(a), c[1] + Ry * 0.9 * math.sin(a)
        r.ell(sx, sy, 1.1 + open_ * 0.6, 0.9 + open_ * 0.5, "ochit", 0.05, flat=1)
        r.ell(sx, sy, 0.6 + open_ * 0.5, 0.5 + open_ * 0.4, "spir", 0.06, flat=3 if open_ > 0.3 else 2)
        if open_ > 0.6 and mist:
            for j in range(mist): r.dot(sx - 2 - j * 2, sy + (j % 2), "mist", 3 - (j > 1), 0.07)
    # dangling legs under the bag
    for k, dx in enumerate((-3.0, -1.0, 1.0, 3.0)):
        hip = T(dx, cy + R * 0.85)
        foot = (hip[0] - 1.0 + legs * (k - 1.5) * 0.5 + limp, hip[1] + 4.0 + limp)
        leg(r, hip, foot, 2.4, 2.6, 0.5 if k % 2 else -0.5, "ochit" if k % 2 else "dchit", near=bool(k % 2), bend=-1, rad=0.5)
    # the face: a chitin head on the front of the bag, two acid eyes, a spout
    hx, hy = c[0] + Rx * 0.86, c[1] + Ry * 0.12
    r.ell(hx, hy, 3.0, 2.8, "chit", 0.2, bias=0.12)
    r.ell(hx - 0.8, hy - 1.6, 1.4, 0.6, "chit", 0.21, flat=4)
    eye(r, hx + 0.6, hy - 0.8, 0.25, glow="aglow" if not dead else None, glint=False)
    eye(r, hx - 1.2, hy - 0.4, 0.24, glow="aglow" if not dead else None, glint=False)
    if hurt and not dead: r.dot(hx + 0.6, hy - 0.8, "white", 3, 0.26)
    antenna(r, (hx - 0.5, hy - 2.6), -80, 3.4, 50, 0.19)
    spout = (hx + 3.2, hy + 0.8 - mouth)
    r.tube([(hx + 1.8, hy + 0.8), spout], [1.2, 0.9 + mouth * 0.4], "chit", 0.21)
    r.dot(spout[0], spout[1], "aglow", 3, 0.22)
    mandible(r, (hx + 1.6, hy + 2.0), 60, 2.0, -40, 0.215, mat="amber", rad=0.5)
    if bubble:
        bx, by, br = bubble
        r.ell(spout[0] + bx, spout[1] + by, br, br, "acid", 2.0, bias=0.3)
        r.dot(spout[0] + bx - br * 0.4, spout[1] + by - br * 0.4, "white", 3, 2.01)
    if streak:
        for k in range(streak): smear(r, [(c[0] - R - 2 - 3 * k, c[1] - 2 + 2 * k), (c[0] - R + 1 - 3 * k, c[1] - 2 + 2 * k)], "mist", 2, -1.0)
    if extra: extra(r, c, R)
    return r.resolve()


def bloater_sheet(outdir):
    Bl = bloater
    anims = []
    for size, sfx in ((1.0, ""), (0.6, "Mid"), (0.25, "Low")):
        idle = [Bl(size=size, bob=[0, -0.5, -1.0, -0.5][i], ph=i, legs=[0, 0.4, 0.8, 0.4][i], squash=[0, 0.05, 0.1, 0.05][i]) for i in range(4)]
        run = [Bl(size=size, bob=-0.6 * math.sin(i / 6 * math.tau), tilt=6, ph=i, legs=1.0) for i in range(6)]
        # Blow: swell (0, 1), the spout puckers (2, 3), the BUBBLE leaves (4), sag (5, 6)
        blow = [Bl(size=size, squash=-0.1, mouth=0.3), Bl(size=size, squash=-0.2, mouth=0.6, bubble=(1.0, 0.0, 1.0)),
                Bl(size=size, squash=-0.25, mouth=1.0, bubble=(1.6, 0.0, 2.0)), Bl(size=size, squash=-0.15, mouth=1.0, bubble=(2.6, -0.5, 3.0)),
                Bl(size=size, squash=0.1, mouth=0.4, bubble=(5.5, -1.0, 3.0)), Bl(size=size, squash=0.05), Bl(size=size)]
        anims += [("Idle" + sfx, idle, [0.16, 0.14, 0.16, 0.14]), ("Run" + sfx, run, [0.1] * 6),
                  ("Blow" + sfx, blow, [0.12, 0.12, 0.1, 0.1, 0.06, 0.12, 0.12])]
    # Whistle: the spiracles open and whistle before it zips (4 frames)
    whistle = [Bl(open_=0.4, squash=-0.05), Bl(open_=0.8, squash=-0.1, mist=1), Bl(open_=1.0, squash=-0.15, mist=2, bob=-0.5),
               Bl(open_=1.0, squash=-0.2, mist=3, bob=-1.0)]
    # Zip: the venting dash (loops while it darts); it shrinks as it goes (Low, a stretched body)
    zip_ = [Bl(size=0.55 - 0.08 * k, open_=1.0, mist=3, streak=2, tilt=-10 + 6 * k, squash=0.25) for k in range(3)]
    # Limp: deflated, hanging slack (2-frame loop)
    limp = [Bl(size=0.1, limp=1.0, squash=0.4, alt=1.0, open_=0.6, legs=[0, 0.6][k], bob=[0, 0.5][k]) for k in range(2)]
    anims += [("Whistle", whistle, [0.1, 0.1, 0.1, 0.1]), ("Zip", zip_, [0.05, 0.05, 0.05]), ("Limp", limp, [0.3, 0.3])]
    idle0 = anims[0][1][0]
    d = [Bl(hurt=True, squash=0.2, open_=1.0, mist=2), Bl(size=0.6, hurt=True, squash=0.4, open_=1.0, mist=3, alt=2.0, tilt=-20),
         Bl(size=0.2, dead=True, squash=0.6, alt=-1.0, tilt=-30, shadow=False, extra=lambda r, c, R: splat(r, c[0], c[1], 0, 3.0, n=8, spread=8)),
         Bl(size=0.05, dead=True, squash=0.7, alt=-2.0, tilt=-40, shadow=False, extra=lambda r, c, R: puddle(r, 0.0, 7.0, -3.0))]
    knock = Bl(hurt=True, squash=0.25, tilt=-14, open_=0.5)
    anims += tail_anims(idle0, d, [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("ZhkBloater", anims, outdir, scale=5)


SYNC["ZhkBloater"] = {"Blow": [("BUBBLE leaves the spout at (21, -17)", 4)], "Whistle": [("the zip starts after the last frame", 3)]}
NOTES["ZhkBloater"] = ("Refill: Idle/Run/Blow (full), IdleMid/RunMid/BlowMid, IdleLow/RunLow/BlowLow. Deflate: Whistle (4) then Zip "
                       "loops while it darts, then Limp loops while it hangs slack.")


# ================================================================== ACID MANTIS: a tall green mantis with acid blades
def mantis_arm(r, sh, a1, a2, z, mat="leaf", glow=True, open_=0.0):
    """A raptorial foreleg from the shoulder: femur along a1, tibia blade folding back along a2."""
    el = chain(sh[0], sh[1], [(6.0, a1)])[-1]
    tip = chain(el[0], el[1], [(6.5, a2)])[-1]
    r.tube([sh, el], [2.0, 1.6], mat, z, bias=0.05)
    r.tube([el, tip], [1.3, 0.6], mat, z + 0.01, bias=0.05)
    if glow:
        # the acid edge along the inside of the blade
        r.line(el[0], el[1] + 0.8, lerp(el[0], tip[0], 0.85), lerp(el[1], tip[1], 0.85) + 0.6, "aglow", z + 0.02, tone=3)
    for k in (0.3, 0.55, 0.8):
        r.dot(lerp(sh[0], el[0], k), lerp(sh[1], el[1], k) + 1.0, mat, 4, z + 0.02)   # spines
    return el, tip


def mantis(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, near=(-60, 150), far=(-55, 145), head=0.0, crouch=0.0, wings=0.0,
           hurt=False, dead=False, reach=0.0, smears=None, extra=None, dust_at=None, sway=0.0):
    r = ZRig(1.1)
    T = Xf(lean, (0.0, -12.0))
    c = crouch
    # four walking legs, long and thin
    hips = [T(-1.0, -12.0 + bob + c), T(-3.0, -12.0 + bob + c), T(-0.4, -12.4 + bob + c), T(-2.4, -12.4 + bob + c)]
    base = [(4.0, 0.0), (-7.0, 0.0), (6.0, 0.0), (-5.0, 0.0)]
    feet = walk_feet(i, n, base, stride, lift=1.6) if stride else base
    if dead: feet = [(h[0] + [3, -3, 4, -2][k], h[1] - 1.0) for k, h in enumerate(hips)]
    for k in (2, 3): leg(r, hips[k], feet[k], 7.0, 7.6, -2.0, "dchit", near=False, bend=-1 if k == 3 else 1, rad=0.75)
    # abdomen sloping back
    ab = [T(-2.0, -12.5 + bob + c), T(-7.5, -11.0 + bob + c), T(-12.5, -7.5 + bob + c)]
    r.tube(ab, [4.4, 5.8, 3.2], "leaf", 0.0, bias=0.08)
    for k in range(3):
        x, y = lerp(ab[0][0], ab[2][0], 0.2 + k * 0.25), lerp(ab[0][1], ab[2][1], 0.2 + k * 0.25)
        r.line(x, y - 2.2, x + 0.4, y + 2.0, "leaf", 0.001, tone=1)
    # folded wings over the abdomen
    wing(r, T(-1.0, -15.5 + bob + c), 166 - wings * 40, 13.0, 5.6, 0.2, mat="leaf", near=True, veins=1)
    for k in (0, 1): leg(r, hips[k], feet[k], 7.0, 7.6, 1.0, "leaf", near=True, bend=-1 if k == 1 else 1, rad=0.85)
    # the tall prothorax, rising
    neck = [T(-0.5, -12.5 + bob + c), T(1.5 + sway, -19.0 + bob + c * 0.6), T(2.5 + sway, -25.0 + bob + c * 0.4)]
    r.tube(neck, [3.4, 2.8, 2.1], "leaf", 0.6, bias=0.1)
    # triangle head
    hx, hy = neck[2][0] + 1.5 + head, neck[2][1] - 2.5
    r.poly([(hx - 3.6, hy - 2.0), (hx + 3.6, hy - 2.2), (hx + 0.8, hy + 3.8)], "leaf", 1.2, normal=(-0.3, -0.5, 0.8))
    eye(r, hx - 2.0, hy - 1.4, 1.25, glow="aglow" if not dead else None, glint=False)
    eye(r, hx + 2.0, hy - 1.6, 1.25, glow="aglow" if not dead else None, glint=False)
    if hurt and not dead: r.dot(hx + 2.0, hy - 1.6, "white", 3, 1.26)
    antenna(r, (hx - 0.6, hy - 2.0), -120, 6.0, 40, 1.19)
    antenna(r, (hx + 0.6, hy - 2.0), -80, 6.0, -30, 1.18, tone=1)
    sh = T(2.0 + sway, -19.5 + bob + c * 0.6)
    tips = []
    tips.append(mantis_arm(r, (sh[0] - 0.5, sh[1] + 0.3), far[0], far[1], 0.5, mat="dchit", glow=True)[1])
    tips.append(mantis_arm(r, sh, near[0], near[1], 1.5)[1])
    if smears:
        for pts in smears: smear(r, pts, "aglow", 3, 2.0)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, tips)
    return r.resolve()


def mantis_sheet(outdir):
    Mt = mantis
    idle = [Mt(bob=[0, 0.3, 0.5, 0.3][i], sway=[0, 0.3, 0.6, 0.3][i], near=(-28 - i % 2 * 3, 168), far=(-22, 163)) for i in range(4)]
    run = [Mt(i=i, n=6, stride=2.6, bob=0.6 * abs(math.sin(i / 6 * math.tau)), lean=6, near=(-50, 150), far=(-45, 145)) for i in range(6)]
    # Blades: raise (0, 1), SWEEP 1 near (2), recoil (3), SWEEP 2 far (4), follow (5), fold (6)
    bl = [Mt(near=(-100, 120), far=(-80, 140), lean=-4), Mt(near=(-130, 100), far=(-95, 130), lean=-8, crouch=0.6),
          Mt(near=(20, 60), far=(-110, 120), lean=8, smears=[arc_pts(4, -20, 12, 10, -60, 20, 6)]),
          Mt(near=(30, 70), far=(-120, 110), lean=6), Mt(near=(30, 70), far=(15, 55), lean=10, smears=[arc_pts(4, -19, 11, 9, -50, 20, 6)]),
          Mt(near=(10, 80), far=(10, 70), lean=6), Mt(near=(-60, 150), far=(-55, 145))]
    # Scissor: open both blades WIDE (0-2, held 0.5 s), SNAP shut in an X ahead (3), hold (4), fold (5)
    sc = [Mt(near=(-110, -60), far=(40, 100), crouch=0.5), Mt(near=(-125, -70), far=(55, 110), crouch=1.0, lean=-4),
          Mt(near=(-130, -75), far=(60, 115), crouch=1.2, lean=-6),
          Mt(near=(10, 30), far=(-15, -35), lean=10, smears=[[(8, -30), (17, -20)], [(8, -12), (17, -22)]]),
          Mt(near=(12, 32), far=(-12, -32), lean=10), Mt(near=(-60, 150), far=(-55, 145))]
    # Reflex: the instant cut (3 frames: a flick of the near blade)
    rf = [Mt(near=(-20, 30), far=(-58, 148), lean=6, smears=[arc_pts(3, -20, 10, 9, -70, 10, 5)]), Mt(near=(0, 40), far=(-58, 148), lean=4),
          Mt(near=(-60, 150), far=(-55, 145))]
    d = [Mt(hurt=True, lean=-10, near=(-120, 100), far=(-100, 120)), Mt(hurt=True, lean=-25, bob=2.0, near=(-80, 120)),
         Mt(dead=True, lean=20, bob=8.0, near=(40, 160), far=(30, 150), dust_at=(-8, 0, 0)),
         Mt(dead=True, lean=25, bob=9.5, near=(50, 170), far=(40, 160))]
    knock = Mt(hurt=True, lean=-14, near=(-120, 100), far=(-100, 120))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Blades", bl, [0.12, 0.1, 0.05, 0.08, 0.05, 0.08, 0.12]),
             ("Scissor", sc, [0.15, 0.17, 0.18, 0.05, 0.12, 0.12]), ("Reflex", rf, [0.05, 0.1, 0.1])]
    anims += tail_anims(idle[0], d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkMantis", anims, outdir, scale=5)


SYNC["ZhkMantis"] = {"Blades": [("SWEEP 1: blade tip to (16, -14); box 20 x 20 at (13, -13)", 2), ("SWEEP 2", 4)],
                     "Scissor": [("SNAP: the blades cross at (14, -20) (box 18 x 14 at (14, -16))", 3)],
                     "Reflex": [("CUT: reach 28 px", 0)]}
NOTES["ZhkMantis"] = "Lightning Reflex plays Reflex (3 frames) when it cuts a shot or strikes; FxZhkReach is its reach crescent."


# ================================================================== PIT ANTLION: a squat antlion, all jaws
def antlion(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, jaw=0.3, sink=0.0, head=0.0, hurt=False, dead=False, flick=None,
            rake=0.0, extra=None, dust_at=None, swell=0.0):
    r = ZRig(1.25)
    T = Xf(lean, (0.0, -6.0))
    s = sink
    body_y = -6.5 + bob + s
    hips = [T(1.5, body_y + 2.5), T(-1.5, body_y + 2.6), T(-4.5, body_y + 2.6), T(2.5, body_y + 2.0), T(-0.5, body_y + 2.2), T(-3.5, body_y + 2.2)]
    base = [(7.0, 0.0), (0.0, 0.0), (-8.0, 0.0), (8.5, 0.0), (1.5, 0.0), (-6.5, 0.0)]
    feet = gait6(i, n, hips, base, stride=stride, lift=1.4) if stride else list(base)
    if rake:
        feet[0] = (feet[0][0] + rake * 2, feet[0][1] - abs(rake) * 2)
    if dead: feet = [(h[0] + [2, 0, -2, 3, 1, -1][k], h[1] - 3.0) for k, h in enumerate(hips)]
    if s < 4: legs6(r, hips, feet, 4.0, 4.6, 1.5, -2.0, mat="sand", far_mat="dchit", rad=0.6, far_rad=0.5)
    # fat bristly abdomen
    ab = T(-8.0, body_y - 0.5)
    r.ell(ab[0], ab[1], 8.6 + swell, 7.4 + swell * 0.6, "sand", 0.0, bias=0.06)
    rnd = random.Random(4)
    for k in range(14):
        a = rnd.uniform(-3.0, -0.2); d = rnd.uniform(0.75, 1.0)
        px, py = ab[0] + (8.0 + swell) * d * math.cos(a), ab[1] + (6.0 + swell * 0.6) * d * math.sin(a)
        r.line(px, py, px + math.cos(a) * 1.2, py + math.sin(a) * 1.2, "sand", 0.01, tone=1 + k % 2)
    for k in range(3):
        r.line(ab[0] - 5 + k * 3.4, ab[1] - 5.4, ab[0] - 5.6 + k * 3.4, ab[1] + 4.0, "sand", 0.005, tone=1)
    tho = T(0.0, body_y - 1.0)
    r.ell(tho[0], tho[1], 4.0, 3.6, "sand", 0.2, bias=0.1)
    # broad flat head with sickle jaws
    hx, hy = T(5.5 + head, body_y - 1.5)
    r.ell(hx, hy, 3.4, 2.8, "sand", 0.4, bias=0.08)
    r.ell(hx - 0.6, hy - 1.4, 1.8, 0.8, "sand", 0.41, flat=4)
    eye(r, hx + 0.8, hy - 1.2, 0.45, glint=not dead)
    eye(r, hx - 0.8, hy - 1.5, 0.44, glint=False)
    if hurt and not dead: r.dot(hx + 0.8, hy - 1.2, "white", 2, 0.46)
    a = 15 + 55 * jaw
    t1 = mandible(r, (hx + 2.4, hy - 0.6), -a, 9.5, 85, 0.5, mat="blood", rad=1.1)
    t2 = mandible(r, (hx + 2.4, hy + 1.0), a * 0.6, 9.0, -80, 0.3, mat="blood", rad=1.0)
    if s:
        # sand heaped round it: it sits in the pit
        r.ell(0.0, -s * 0.4, 13.0, s * 0.9, "sand", 1.0, flat=2)
        r.ell(-3.0, -s * 0.6, 8.0, s * 0.5, "sand", 1.01, flat=3)
    if flick:
        for (fx, fy, k) in flick:
            for j in range(3): r.dot(fx - j * 1.2, fy + j * (0.6 + k * 0.3), "sand", 4 - j, 3.0)
    if dust_at: dust(r, *dust_at, mat="sand")
    if extra: extra(r, (hx, hy), (t1, t2))
    return r.resolve()


def antlion_sheet(outdir):
    A = antlion
    idle = [A(bob=[0, 0.3, 0.5, 0.3][i], jaw=[0.3, 0.4, 0.5, 0.4][i], swell=[0, 0.2, 0.4, 0.2][i]) for i in range(4)]
    run = [A(i=i, n=6, stride=2.2, bob=0.5 * abs(math.sin(i / 6 * math.tau)), lean=3, jaw=0.35) for i in range(6)]
    # Clamp: jaws wide (0, 1), CLAMP shut (2), grind (3, 4), let go (5, 6)
    cl = [A(jaw=0.8, head=-0.8, lean=-3), A(jaw=1.2, head=-1.2, lean=-6), A(jaw=0.0, head=2.5, lean=6, dust_at=(14, 0, 0)),
          A(jaw=0.05, head=2.2, lean=5), A(jaw=0.1, head=2.0, lean=4), A(jaw=0.4, head=0.8), A(jaw=0.35)]
    # Dig: rake the sand (0-2), sink in (3-5): ends in the pit
    dig = [A(rake=1.0, jaw=0.5, dust_at=(6, 0, 0)), A(rake=-1.0, jaw=0.5, sink=1.0, dust_at=(6, 0, 1)), A(rake=1.0, jaw=0.6, sink=2.0, dust_at=(-6, 0, 0)),
           A(jaw=0.6, sink=3.0, dust_at=(-6, 0, 1)), A(jaw=0.7, sink=4.0), A(jaw=0.7, sink=4.5)]
    # PitIdle: only the head and the open jaws above the sand (loop)
    pit = [A(sink=4.5, jaw=[0.7, 0.9, 1.0, 0.85][k], head=[0, 0.3, 0.5, 0.3][k]) for k in range(4)]
    # Flick: a jerk of the head throws sand up the slope (the puff leaves at 1)
    fl = [A(sink=4.5, jaw=0.4, head=-1.0), A(sink=4.5, jaw=1.1, head=1.5, flick=[(12, -8, 0), (10, -10, 0)]),
          A(sink=4.5, jaw=0.9, head=0.8, flick=[(16, -11, 1), (14, -13, 1)]), A(sink=4.5, jaw=0.8)]
    # Emerge: climbs out when the pit closes
    em = [A(sink=3.5, jaw=0.6, dust_at=(0, 0, 0)), A(sink=2.0, jaw=0.5, dust_at=(0, 0, 1)), A(sink=0.8, jaw=0.4), A(jaw=0.35)]
    d = [A(hurt=True, jaw=1.2, lean=-6, head=-1), A(hurt=True, jaw=1.0, lean=-10, bob=1.0),
         A(dead=True, jaw=0.6, lean=6, bob=3.0, dust_at=(0, 0, 0)), A(dead=True, jaw=0.7, lean=8, bob=3.5)]
    knock = A(hurt=True, jaw=1.1, lean=-10, head=-1.5)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Clamp", cl, [0.12, 0.12, 0.05, 0.1, 0.1, 0.1, 0.12]), ("Dig", dig, [0.08, 0.08, 0.08, 0.08, 0.08, 0.1]),
             ("PitIdle", pit, [0.15, 0.15, 0.15, 0.15]), ("Flick", fl, [0.08, 0.06, 0.08, 0.12]), ("Emerge", em, [0.1, 0.1, 0.1, 0.1])]
    anims += tail_anims(idle[0], d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkAntlion", anims, outdir, scale=5)


SYNC["ZhkAntlion"] = {"Clamp": [("CLAMP: jaws shut at (21, -6); box 16 x 12 at (18, -7)", 2)],
                      "Flick": [("FLICK: the sand puff leaves the jaws at (14, -6)", 1)]}
NOTES["ZhkAntlion"] = "Sand Pit: Dig (0.48 s) sinks it, PitIdle loops in the pit, Flick throws sand, Emerge climbs out."


# ================================================================== AMBER HIVE: a honeycomb mound on stubby legs
def hexagon(cx, cy, rr):
    return [(cx + rr * math.cos(math.radians(30 + 60 * k)), cy + rr * 0.92 * math.sin(math.radians(30 + 60 * k))) for k in range(6)]


def comb_cells(r, c, W, H, z, ph=0, cell=2.5, seed=3, open_every=3, cracked=()):
    """Hex comb over a dome centred c (W x H): wax walls, capped cells in three tones lit from the top-left, open cells
    dark with honey in them. Returns the cell centres (for drips and hornets)."""
    rnd = random.Random(seed)
    out = []
    dx, dy = cell * 1.73, cell * 1.5
    rows = int(H * 2 / dy) + 2
    for j in range(-rows // 2 - 1, rows // 2 + 2):
        for i in range(-int(W / dx) - 2, int(W / dx) + 3):
            x = c[0] + i * dx + (dx / 2 if j % 2 else 0.0)
            y = c[1] + j * dy
            d = ((x - c[0]) / W) ** 2 + ((y - c[1]) / H) ** 2
            if d > 0.86: continue
            l = -((x - c[0]) / W) * 0.55 - ((y - c[1]) / H) * 0.75 + 0.1 * rnd.random()
            t = 3 if l > 0.35 else 2 if l > -0.25 else 1
            hx = hexagon(x, y, cell * 0.98)
            r.polyline(hx + [hx[0]], "amber", z + 0.01, tones=[t - 1] * 6)
            key = (i, j)
            opened = (abs(i * 7 + j * 3 + seed) % open_every == 0) or key in cracked
            if opened:
                r.poly(hexagon(x, y, cell * 0.66), "honey", z + 0.02, flat=max(0, t - 2))
                r.dot(x - 0.4, y + 0.4, "jelly", 1 if (i + j + ph) % 2 else 2, z + 0.03)
            else:
                r.poly(hexagon(x, y, cell * 0.66), "wax", z + 0.02, flat=t)
                if t == 3: r.dot(x - 0.5, y - 0.5, "wax", 4, z + 0.03)
            out.append((x, y, opened, t))
    return out


def hornet_tiny(r, x, y, z, ang=0.0, wing=0):
    """A hornet the size of a fingernail: banded abdomen, dark head, a flick of wing."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    P = lambda u, v: (x + u * ca - v * sa, y + u * sa + v * ca)
    r.ell(*P(-1.4, 0), 1.3, 0.9, "hyel", z, flat=3)
    r.dot(*P(-1.4, 0), "hblk", 1, z + 0.01)
    r.dot(*P(-2.6, 0), "hblk", 1, z + 0.01)
    r.ell(*P(0.4, 0), 0.8, 0.7, "hblk", z + 0.01, flat=2)
    r.dot(*P(1.4, 0), "hblk", 0, z + 0.01)
    r.dot(*P(-0.4, -1.2 - (wing % 2)), "white", 3, z + 0.02)
    r.dot(*P(-1.2, -1.4 - (wing % 2)), "wblur", 3, z + 0.02)


def hive(bob=0.0, lean=0.0, i=0, n=6, stride=0.0, crack=0, ph=0, squash=0.0, hurt=False, dead=False, open_=0.0,
         slam=0.0, extra=None, dust_at=None, wasps=4, flakes=None):
    r = ZRig(1.08)
    T = Xf(lean, (0.0, -10.0))
    # jointed legs: thick, dark, knees out
    hips = [T(-7.0, -8.0 + bob), T(5.0, -8.0 + bob), T(-3.5, -7.5 + bob), T(8.5, -7.5 + bob)]
    base = [(-10.0, 0.0), (7.0, 0.0), (-5.0, 0.0), (11.5, 0.0)]
    feet = walk_feet(i, n, base, stride, lift=1.6) if stride else base
    if dead: feet = [(h[0] + [-2, 2, -1, 3][k], h[1] - 1.0) for k, h in enumerate(hips)]
    for k in (2, 3): leg(r, hips[k], feet[k], 4.4, 4.6, -1.0, "dchit", near=False, bend=1 if k == 3 else -1, rad=1.0)
    # the mound: a lumpy dome of comb over a dark underside
    c = T(0.0, -20.0 + bob + squash * 3.0)
    W, H = 15.0 * (1 + squash * 0.15), 14.6 * (1 - squash * 0.2)
    r.ell(c[0], c[1] + H * 0.62, W * 0.9, H * 0.42, "hblk", -0.3, bias=-0.1)
    r.ell(c[0], c[1], W, H, "wax", 0.0, bias=0.1)
    r.ell(c[0] - 5.0, c[1] - H * 0.75, 6.0, 4.0, "wax", 0.005, bias=0.15)
    cracked = [(-2, 1), (1, -2), (0, 3), (3, 1), (-3, -1)][:crack]
    cells = comb_cells(r, c, W, H, 0.01, ph=ph, cracked=cracked)
    # honey running down from open cells low on the flank
    for k, (x, y, opened, t) in enumerate(cells):
        if opened and y > c[1] + 2 and k % 2 == 0:
            drip(r, x, y + 1.2, 2 + (k + ph) % 3, 0.06, mat="jelly", ph=0)
    for k in range(crack):
        cx, cy = c[0] + [-6, 4, -2, 8, -9][k % 5], c[1] + [2, -4, 7, 4, -3][k % 5]
        r.ell(cx, cy, 1.6, 1.4, "dchit", 0.07, flat=0)
        drip(r, cx, cy + 1.4, 3 + k % 2, 0.08, mat="jelly", ph=(ph + k) % 2)
    # the entrance: a dark hole low at the front, ringed in wax, hornets crawling out
    mx, my = c[0] + 10.0, c[1] + 5.5
    r.ell(mx, my, 4.4 + open_ * 0.8, 3.4 + open_ * 0.6, "amber", 0.1, flat=1)
    r.ell(mx + 0.3, my + 0.3, 3.0 + open_, 2.2 + open_ * 0.7, "dchit", 0.11, flat=0)
    hornet_tiny(r, mx + 1.5 + open_, my + 0.5, 0.12, ang=-15, wing=ph)
    if wasps > 3: hornet_tiny(r, mx + 4.5, my - 3.0, 0.2, ang=-60, wing=ph + 1)
    # a face over the door: two amber eyes and mandibles either side of it
    for k, dx in enumerate((-2.2, 1.6)):
        eye(r, mx + dx, my - 4.6, 0.15, glow="jelly" if not dead else None, glint=False)
        if hurt and not dead: r.dot(mx + dx, my - 4.6, "white", 3, 0.16)
    for k in (0, 1):
        mandible(r, (mx + 3.0, my - 1.8 + k * 3.6), -35 + k * 70 + slam * 12 * (1 - 2 * k), 5.0, 60 * (1 - 2 * k), 0.13,
                 mat="hblk", rad=1.0)
    for k in (0, 1): leg(r, hips[k], feet[k], 4.4, 4.6, 0.5, "hblk", near=True, bend=1 if k == 1 else -1, rad=1.2)
    # hornets crawling over the comb
    rnd = random.Random(7)
    for k in range(max(0, wasps - 2)):
        a = rnd.uniform(-2.7, -0.5) + ph * 0.3 * (1 if k % 2 else -1)
        wx, wy = c[0] + W * 0.8 * math.cos(a), c[1] + H * 0.8 * math.sin(a)
        hornet_tiny(r, wx, wy, 0.3, ang=math.degrees(a) + 90, wing=ph + k)
    if flakes:
        for (fx, fy) in flakes: r.dot(fx, fy, "wax", 4, 3.0)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, c, (mx, my))
    return r.resolve()


def hive_sheet(outdir):
    Hv = hive
    anims = []
    for crack, sfx in ((0, ""), (3, "Crack")):
        idle = [Hv(crack=crack, bob=[0, 0.4, 0.7, 0.4][i], ph=i, squash=[0, 0.03, 0.06, 0.03][i]) for i in range(4)]
        run = [Hv(crack=crack, i=i, n=6, stride=1.8, bob=0.8 * abs(math.sin(i / 6 * math.tau)), lean=3, ph=i) for i in range(6)]
        anims += [("Idle" + sfx, idle, [0.16, 0.14, 0.16, 0.14]), ("Run" + sfx, run, [0.1] * 6)]
    # Slam: rock back (0, 1), DROP forward (2, the weight lands), wax flakes fly (3), settle (4, 5)
    sl = [Hv(lean=-6, squash=-0.05), Hv(lean=-12, squash=-0.12, bob=-1.0), Hv(lean=14, squash=0.18, slam=1.0, dust_at=(14, 0, 0)),
          Hv(lean=12, squash=0.12, slam=1.0, dust_at=(14, 0, 1), flakes=[(16, -12), (20, -9), (13, -16), (22, -14)]),
          Hv(lean=5, squash=0.05), Hv()]
    # Swarm: the mouth gapes (0-2), the SWARMS pour out (3), it rumbles (4-6)
    sw = [Hv(open_=0.5, squash=-0.05), Hv(open_=1.2, squash=-0.1, ph=1), Hv(open_=1.8, squash=-0.12, ph=2, wasps=6),
          Hv(open_=2.0, squash=0.05, ph=3, wasps=2, extra=lambda r, c, m: [r.ell(m[0] + 4 + k * 2, m[1] - 2 - k * 2, 1.0, 0.7, "hyel", 3.0, flat=3) for k in range(4)]),
          Hv(open_=1.2, ph=4, wasps=3), Hv(open_=0.5, ph=5), Hv(ph=6)]
    anims += [("Slam", sl, [0.12, 0.14, 0.06, 0.1, 0.12, 0.14]), ("Swarm", sw, [0.1, 0.1, 0.12, 0.08, 0.1, 0.1, 0.12])]
    idle0 = anims[0][1][0]
    d = [Hv(hurt=True, lean=-8, crack=2, open_=1.0), Hv(hurt=True, lean=-16, crack=4, bob=1.0, wasps=7),
         Hv(dead=True, lean=10, crack=5, squash=0.35, bob=3.0, wasps=0, dust_at=(0, 0, 0)), Hv(dead=True, lean=12, crack=5, squash=0.45, bob=4.0, wasps=0)]
    knock = Hv(hurt=True, lean=-12, crack=1, open_=0.8)
    anims += tail_anims(idle0, d, [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("ZhkHive", anims, outdir, scale=5)


SYNC["ZhkHive"] = {"Slam": [("SLAM: the front lands at (16, -6); box 22 x 18 at (14, -9)", 2)],
                   "Swarm": [("SWARMS leave the mouth at (12, -14)", 3)]}
NOTES["ZhkHive"] = "Honeycomb: IdleCrack/RunCrack once its cells are cracked (three hits); each crack drips amber (FxZhkDrip)."


# ================================================================== HUNTING WASP: a steel-blue spider wasp
def hunter(alt=7.0, tilt=0.0, curl=0.0, wing_a=-110.0, blur=1, lance=0.0, white=False, hurt=False, dead=False, legs=0.0,
           extra=None, shadow=True, x=0.0, streak=0, fold=0.0, grab=0.0):
    r = ZRig(1.17)
    if shadow: ground_shadow(r, x, 4.0)
    wx, wy = x - 1.0, -alt - 10.0
    T = Xf(tilt, (wx, wy)); C = Xf(-curl, (wx, wy))
    # long dangling legs (they grab with `grab`)
    for k, dx in enumerate((-1.2, 0.6, 2.4)):
        hip = T(wx + 3.0 + dx, wy + 2.0)
        for side in (0, 1):
            fx = hip[0] + (-3.0 + k * 2.5 + legs * (k - 1)) * (1.0 if side else 0.8) + grab * 3
            fy = hip[1] + 8.5 - fold * 3 - grab * 3
            leg(r, hip, (fx, fy), 4.6, 5.0, 0.4 if side else -0.4, "sblue" if side else "dchit", near=bool(side),
                bend=-1 if k < 1 else 1, rad=0.5 if side else 0.45)
    ab = [T(*C(wx + dx, wy + dy)) for dx, dy in ((-0.6, 0.4), (-4.4, 2.6), (-8.4, 5.6), (-10.6, 8.4))]
    r.tube(ab, [1.6, 3.0, 2.4, 1.0], "sblue", 0.1, bias=0.08)
    r.line(ab[1][0] - 1, ab[1][1] - 2.2, ab[2][0], ab[2][1] - 1.6, "sblue", 0.11, tone=4)
    sa = math.atan2(ab[3][1] - ab[2][1], ab[3][0] - ab[2][0])
    L = 3.0 + lance * 4.0
    st = (ab[3][0] + L * math.cos(sa), ab[3][1] + L * math.sin(sa))
    r.tube([ab[3], st], [0.8, 0.35], "sblue", 0.13)
    r.dot(st[0], st[1], "white", 3, 0.14)
    root = T(wx + 2.4, wy - 2.6)
    wa = wing_a + fold * 60
    wm = "white" if white else "orwing"
    wing(r, root, wa - 12, 12.0 - fold * 3, 4.0, -0.6, mat=wm, near=False)
    wing(r, (root[0] + 1.0, root[1] + 0.3), wa + 8, 11.5 - fold * 3, 3.6, -0.4, mat=wm, near=True)
    if blur: wing_blur(r, root, wa + 45, wa + 75, 10.0, -0.7, mat="white" if white else "wblur", n=2)
    th = T(wx + 3.2, wy - 0.8)
    r.ell(th[0], th[1], 3.2, 2.6, "sblue", 0.2, bias=0.12)
    hd = T(wx + 7.2, wy - 0.6)
    r.ell(hd[0], hd[1], 2.4, 2.2, "sblue", 0.3, bias=0.05)
    eye(r, hd[0] + 0.3, hd[1] - 0.6, 0.32, glint=not dead, big=True)
    if hurt and not dead: r.dot(hd[0] + 0.3, hd[1] - 0.6, "white", 2, 0.33)
    mandible(r, (hd[0] + 1.8, hd[1] + 1.2), 70, 2.4, -50, 0.34, rad=0.5, mat="orwing")
    antenna(r, (hd[0] + 0.8, hd[1] - 2.0), -60 + tilt * 0.3, 6.0, 70 if not dead else 110, 0.29, tone=1)
    if streak:
        for k in range(streak): smear(r, [(hd[0] - 12 - 3 * k, hd[1] + k), (hd[0] - 8 - 3 * k, hd[1] + k)], "wblur", 2, -1.0)
    if extra: extra(r, hd, st)
    return r.resolve()


def hunter_sheet(outdir):
    Hn = hunter
    idle = [Hn(alt=[5.0, 5.5, 6.0, 5.5][i], wing_a=[-145, -100, -135, -95][i], curl=[0, 4, 8, 4][i], legs=[0, 0.4, 0.8, 0.4][i]) for i in range(4)]
    run = [Hn(alt=5.5 + 0.6 * math.sin(i / 6 * math.tau), tilt=12, wing_a=[-145, -100, -135, -95, -140, -105][i], curl=-6,
              legs=1.0, streak=1 if i % 2 else 0) for i in range(6)]
    # Lance: the abdomen swings under and forward (0-2), the lance THRUSTS out (3), held (4), withdrawn (5, 6)
    ln = [Hn(curl=40, alt=6), Hn(curl=90, alt=6.5, tilt=-8), Hn(curl=120, alt=6.5, tilt=-12),
          Hn(curl=135, alt=6.0, tilt=-4, lance=1.0, x=2.0, extra=lambda r, h, s: smear(r, [(s[0] - 6, s[1]), (s[0] - 1, s[1])], "white", 2)),
          Hn(curl=135, alt=6.0, tilt=-4, lance=1.0, x=2.0), Hn(curl=80, alt=6.5, lance=0.3), Hn(curl=10, alt=6.0)]
    # Rise: climbs (0, 1), circles once (2-5, banking), the MARK (6), hover (7)
    rise = [Hn(alt=8, tilt=-10), Hn(alt=11, tilt=-15, wing_a=-100), Hn(alt=13, tilt=15, curl=10), Hn(alt=13, tilt=25, curl=20, wing_a=-100),
            Hn(alt=12, tilt=10, curl=10), Hn(alt=11, tilt=-5), Hn(alt=10, curl=100, tilt=-10, extra=lambda r, h, s: r.ell(s[0], s[1], 1.3, 1.1, "jelly", 2.0, flat=3)),
            Hn(alt=8, curl=20)]
    # Carry: wings beat white, legs clasped round the prey (loop)
    carry = [Hn(alt=9 + [0, 0.5, 1, 0.5][k], white=True, wing_a=[-150, -100, -140, -95][k], grab=1.0, tilt=-6, curl=-10) for k in range(4)]
    d = [Hn(alt=6, tilt=-30, blur=0, wing_a=-165, hurt=True, curl=30), Hn(alt=3, tilt=-50, blur=0, wing_a=-178, hurt=True, curl=20, fold=0.4),
         Hn(alt=-5.0, tilt=12, blur=0, wing_a=175, dead=True, curl=-10, fold=1.0, shadow=False, extra=lambda r, h, s: dust(r, 0, 0, 0)),
         Hn(alt=-5.5, tilt=14, blur=0, wing_a=178, dead=True, curl=-14, fold=1.0, shadow=False)]
    knock = Hn(alt=7, tilt=-28, blur=0, wing_a=-165, hurt=True, curl=25)
    anims = [("Idle", idle, [0.06] * 4), ("Run", run, [0.06] * 6), ("Lance", ln, [0.12, 0.1, 0.1, 0.05, 0.1, 0.1, 0.12]),
             ("Rise", rise, [0.1, 0.1, 0.08, 0.08, 0.08, 0.08, 0.1, 0.12]), ("Carry", carry, [0.05] * 4)]
    anims += tail_anims(idle[0], d, [0.08, 0.1, 0.12, 0.4], knock)
    return sheet("ZhkHunter", anims, outdir, scale=5)


SYNC["ZhkHunter"] = {"Lance": [("THRUST: the lance tip at (18, -14); box 14 x 10 at (15, -13)", 3)],
                     "Rise": [("MARK: the scent dart from the sting", 6)]}
NOTES["ZhkHunter"] = "Carry Off: Carry loops (white wings) while it holds the hero; FxZhkCarry is the hero's lifted shadow."

JOBS = [("ZhkMother", mother_sheet), ("ZhkBloater", bloater_sheet), ("ZhkMantis", mantis_sheet), ("ZhkAntlion", antlion_sheet),
        ("ZhkHive", hive_sheet), ("ZhkHunter", hunter_sheet)]
