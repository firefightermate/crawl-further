"""Zhekra tier 1 (Acid Grub, Brood Drone, Resin Beetle) and the Hive Larva. Built through zhekra_v2_rigs.py
(python3 zhekra_v2_rigs.py --only ZhkGrub,...). Material ramps, top-left light, selective outline, every frame posed.
T1 idle limit 20 x 16 (a flier counts its hover)."""
import math
from zhekra_v2_rigs import (Rig, Xf, chain, ik, lerp, segs, leg, gait6, legs6, antenna, wing, wing_blur, eye, mandible,
                            drip, puddle, dust, smear, splat, ground_shadow, arc_pts, sheet, tail_anims, SYNC, NOTES)


# ================================================================== ACID GRUB: a fat segmented grub, hooked mandibles
def grub_body(r, n=5, fat=0.0, wave=0.0, ph=0.0, head=(0.0, 0.0), jaw=0.3, rear=0.0, drool=0, beads=True, bulge=-1,
              squash=0.0, z=0.0, x0=None, sp=2.25, hsize=1.0, dead=False, mat="cream", head_mat="chit", hurt=False, plates=True):
    """A grub lying along the floor, tail at the left, head reared at the right: one fat tapered tube with segment
    seams. n segments, fat adds girth, wave a peristaltic ripple (phase ph), rear lifts the front, bulge = index of a
    segment swollen with acid (it glows through the skin)."""
    if x0 is None: x0 = -((n - 1) * sp) / 2.0 - 2.0
    pts, rad = [], []
    for i in range(n + 1):
        t = i / float(n)
        w = math.sin(ph + i * 1.2) * wave
        R = (2.0 + 2.1 * math.sin(math.pi * min(1.0, 0.18 + t * 0.9)) + fat) * (1.0 - 0.18 * squash)
        if i == bulge or i == bulge + 1: R += 0.6
        x = x0 + i * sp * (1.0 - squash) + w * 0.5
        lift = rear * max(0.0, t - 0.5) * 3.0
        pts.append((x, -R + 0.4 - lift + abs(w) * 0.3)); rad.append(R)
    # each segment is a lit bulge; the seams pinch in between them
    parts = []
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        R = (rad[i] + rad[i + 1]) / 2.0
        parts.append(r.ell((xa + xb) / 2.0, (ya + yb) / 2.0, sp * 0.62 * (1.0 - 0.2 * squash) + 0.3, R, mat, z + i * 0.003,
                           bias=0.06))
    body = parts[-1]
    for i in range(1, n):
        x, y = pts[i]; R = rad[i]
        r.dot(x, -0.0, "dchit", 1, z - 0.3)   # proleg
    for i in range(n):
        x, y = (pts[i][0] + pts[i + 1][0]) / 2.0, (pts[i][1] + pts[i + 1][1]) / 2.0; R = (rad[i] + rad[i + 1]) / 2.0
        if plates and 0 < i < n - 1 and i % 2 == (n % 2):
            r.ell(x - 0.2, y - R * 0.72, 1.4, 0.7, "chit", z + 0.04, bias=0.2)
        if beads and (i + int(ph * 1.6)) % 2 == 1 and 0 < i < n - 1:
            r.dot(x + 0.3, y - R * 0.15, "aglow", 3, z + 0.06)
        if i == bulge:
            r.ell(x, y, 1.4, R * 0.55, "aglow", z + 0.06, flat=2)
            r.dot(x - 0.4, y - R * 0.3, "aglow", 4, z + 0.07)
    # head capsule
    hs = hsize
    hx, hy = pts[-1][0] + 1.4 * hs + head[0], pts[-1][1] - 1.8 * hs + head[1]
    if dead:
        hy = pts[-1][1] + 0.8
    nk = ((pts[-1][0] + pts[-2][0]) / 2.0 + sp * 0.3, (pts[-1][1] + pts[-2][1]) / 2.0)
    r.tube([nk, (hx - 1.0 * hs, hy + 0.4)], [rad[-1] * 0.8, 1.5 * hs], mat, z + 0.1, bias=0.05)
    r.ell(hx, hy, 2.5 * hs, 2.3 * hs, head_mat, z + 0.2, bias=0.12)
    eye(r, hx + 0.7 * hs, hy - 0.7 * hs, z + 0.25, glint=not dead, big=False)
    if hurt: r.dot(hx + 0.7 * hs, hy - 0.7 * hs, "white", 2, z + 0.26)
    # hooked mandibles: open by jaw (0 shut .. 1 wide)
    a = 20 + 50 * jaw
    mandible(r, (hx + 1.8 * hs, hy + 0.6 * hs), -a * 0.4 + 15, 3.4 * hs, 80, z + 0.3, mat="amber", rad=0.65 * hs)
    mandible(r, (hx + 1.4 * hs, hy + 1.4 * hs), a + 15, 3.0 * hs, -70, z + 0.18, mat="chit", rad=0.55 * hs)
    if drool:
        drip(r, hx + 2.8 * hs, hy + 2.2 * hs, drool, z + 0.4, ph=0)
    return pts, (hx, hy)


def grub(n=5, fat=0.0, extra=None, dust_at=None, splat_at=None, glob=None, rear=0.0, **kw):
    r = Rig()
    pts, hd = grub_body(r, n=n, fat=fat + 0.5, hsize=1.6, sp=2.0, rear=rear + 0.5, **kw)
    if glob:
        gx, gy, k = glob
        r.ell(hd[0] + gx, hd[1] + gy, 1.4 - 0.2 * k, 1.1, "aglow", 2.0, flat=3)
        r.dot(hd[0] + gx - 0.4, hd[1] + gy - 0.4, "aglow", 4, 2.01)
        if k: smear(r, [(hd[0] + gx - 2 - k, hd[1] + gy), (hd[0] + gx - 1.5, hd[1] + gy)], "aglow", 2, 2.0)
    if splat_at: splat(r, *splat_at, z=3.0)
    if dust_at: dust(r, *dust_at)
    if extra: extra(r, pts, hd)
    return r.resolve()


def grub_anims(k, suffix):
    """The four moving anims of a grub that has grown k times (k extra segments, fatter)."""
    n, fat = 5 + k, 0.3 * k
    G = lambda **kw: grub(n=n, fat=fat, **kw)
    idle = [G(ph=i * 0.5, wave=0.25, head=(0, [0, -0.3, -0.5, -0.3][i]), jaw=[0.2, 0.3, 0.45, 0.3][i],
              drool=[1, 2, 2, 0][i]) for i in range(4)]
    run = [G(ph=i / 6.0 * math.tau, wave=0.7, squash=[0.0, 0.08, 0.16, 0.12, 0.05, 0.0][i], head=([0.5, 0.0, -0.4, -0.2, 0.2, 0.5][i], [0, 0.3, 0.5, 0.2, 0, -0.2][i]),
             jaw=0.25, rear=0.2) for i in range(6)]
    # Bite: coil back (0, 1), LUNGE (2, the head 3 px out, jaws wide), SNAP shut (3), hold (4), settle (5)
    bite = [G(squash=0.12, head=(-1.0, -0.5), rear=0.5, jaw=0.4),
            G(squash=0.2, head=(-1.5, -1.5), rear=1.0, jaw=0.9, drool=1),
            G(squash=-0.15, head=(3.0, 0.5), rear=0.2, jaw=1.0, extra=lambda r, p, h: smear(r, [(h[0] - 4, h[1]), (h[0] - 1, h[1])], "cream", 3, 1.0)),
            G(squash=-0.15, head=(3.5, 0.8), rear=0.1, jaw=0.0, splat_at=(p_head(n, 3.5) + 3, -3, 0)),
            G(squash=-0.05, head=(1.5, 0.3), rear=0.2, jaw=0.1),
            G(head=(0.3, 0.0), jaw=0.2)]
    # Spit: rear up (0), the acid swells down the throat (1, 2), SPIT (3, a glob leaves the mouth), recoil (4, 5)
    spit = [G(rear=0.6, head=(-0.5, -0.8), jaw=0.2, bulge=n - 3),
            G(rear=1.2, head=(-1.0, -1.8), jaw=0.3, bulge=n - 2),
            G(rear=1.4, head=(-1.0, -2.0), jaw=0.6, bulge=n - 1, drool=2),
            G(rear=0.6, head=(1.5, 0.0), jaw=1.0, glob=(4.0, 1.0, 1)),
            G(rear=0.3, head=(0.5, 0.3), jaw=0.7, drool=1, glob=(8.0, 1.5, 2)),
            G(rear=0.1, head=(0.0, 0.0), jaw=0.3)]
    return [("Idle" + suffix, idle, [0.14, 0.12, 0.14, 0.12]), ("Run" + suffix, run, [0.08] * 6),
            ("Bite" + suffix, bite, [0.12, 0.12, 0.05, 0.07, 0.1, 0.12]),
            ("Spit" + suffix, spit, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12])]


def p_head(n, dx):
    sp = 2.0
    return -((n - 1) * sp) / 2.0 - 2.0 + n * sp + 2.2 + dx


def grub_sheet(outdir):
    anims = grub_anims(0, "")
    for k in (1, 2, 3):
        anims += grub_anims(k, str(k))
    idle0 = anims[0][1][0]
    d0 = grub(jaw=1.0, head=(-0.5, -1.5), rear=1.0, hurt=True)
    d1 = grub(jaw=0.8, head=(0.5, 0.5), squash=0.1, wave=0.6, ph=1.0, hurt=True)
    d2 = grub(jaw=0.5, head=(0.0, 1.5), squash=0.2, dead=True, splat_at=(0, -2, 1))
    d3 = grub(jaw=0.6, head=(0.0, 1.5), squash=0.25, dead=True, beads=False,
              extra=lambda r, p, h: puddle(r, 0.0, 5.0, -1.0, mat="acid"))
    knock = grub(rear=1.4, head=(-1.5, -2.0), jaw=0.9, squash=0.1, hurt=True)
    anims += tail_anims(idle0, [d0, d1, d2, d3], [0.1, 0.12, 0.12, 0.4], knock)
    return sheet("ZhkGrub", anims, outdir, scale=7)


SYNC["ZhkGrub"] = {"Bite": [("LUNGE: jaws at (10, -3); box 12 x 12 at (12, -4)", 2), ("snap", 3)],
                   "Spit": [("SPIT: the glob leaves the mouth at (10, -7)", 3)]}
NOTES["ZhkGrub"] = ("Gorge: Idle1/Run1/Bite1/Spit1 .. Idle3/Run3/Bite3/Spit3 are the grub after 1-3 feeds (one more segment and "
                    "fatter each time). The mouth moves forward 1 px per feed.")


# ================================================================== HIVE LARVA: a small cream maggot with hooks
def larva(ph=0.0, wave=0.3, head=(0.0, 0.0), jaw=0.3, rear=0.0, squash=0.0, dead=False, hurt=False, drool=0,
          extra=None, splat_at=None):
    r = Rig()
    pts, hd = grub_body(r, n=4, fat=0.2, wave=wave, ph=ph, head=head, jaw=jaw, rear=rear, squash=squash, dead=dead,
                        beads=False, sp=2.1, mat="cream", head_mat="amber", hurt=hurt, drool=drool, plates=False, hsize=0.9)
    if splat_at: splat(r, *splat_at, z=3.0, mat="cream")
    if extra: extra(r, pts, hd)
    return r.resolve()


def larva_sheet(outdir):
    idle = [larva(ph=i * 0.6, head=(0, [0, -0.4, -0.6, -0.2][i]), jaw=[0.2, 0.4, 0.6, 0.3][i]) for i in range(4)]
    run = [larva(ph=i / 6.0 * math.tau, wave=0.8, squash=[0.0, 0.1, 0.2, 0.14, 0.06, 0.0][i], rear=0.2,
                 head=([0.5, 0, -0.4, -0.2, 0.2, 0.5][i], 0)) for i in range(6)]
    bite = [larva(rear=0.6, head=(-1.0, -1.0), jaw=0.5, squash=0.15), larva(rear=1.0, head=(-1.5, -1.5), jaw=1.0, squash=0.2),
            larva(head=(2.5, 0.5), jaw=1.0, squash=-0.15), larva(head=(3.0, 0.8), jaw=0.0, squash=-0.15, splat_at=(9, -2, 0)),
            larva(head=(1.0, 0.3), jaw=0.2), larva(jaw=0.3)]
    d = [larva(hurt=True, rear=1.0, jaw=1.0, head=(-1, -1.5)), larva(hurt=True, squash=0.15, jaw=0.8, wave=0.8, ph=1.0),
         larva(dead=True, squash=0.2, jaw=0.4, splat_at=(0, -2, 1)),
         larva(dead=True, squash=0.3, jaw=0.5, extra=lambda r, p, h: puddle(r, 0.0, 3.5, -1.0, mat="cream", glint=False))]
    knock = larva(hurt=True, rear=1.2, jaw=0.9, head=(-1.5, -1.8))
    anims = [("Idle", idle, [0.12, 0.1, 0.12, 0.1]), ("Run", run, [0.06] * 6),
             ("Bite", bite, [0.1, 0.1, 0.05, 0.07, 0.08, 0.1])] + tail_anims(idle[0], d, [0.08, 0.1, 0.1, 0.3], knock)
    return sheet("ZhkLarva", anims, outdir, scale=9)


SYNC["ZhkLarva"] = {"Bite": [("BITE: jaws at (8, -2)", 2)]}


# ================================================================== BROOD DRONE: a small wasp drone
def banded(p0, p1, period, a, b, phase=0.0):
    """A material callable: stripes of a / b across the axis p0 -> p1, `period` px apart."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L

    def f(x, y):
        t = (x - p0[0]) * ux + (y - p0[1]) * uy + phase
        return a if (t // (period / 2.0)) % 2 == 0 else b
    return f


def drone_body(r, x=0.0, y=-9.0, tilt=0.0, curl=0.0, wing_a=-120.0, blur=0, legs=0.0, glow=False, fold=0.0, z=0.0,
               jaw=0.2, hurt=False, dead=False):
    """(x, y) = the waist. tilt leans the whole body (deg, + = nose down), curl swings the abdomen forward under it."""
    T = Xf(tilt, (x, y))
    C = Xf(-curl, (x, y))
    # abdomen: a banded tapered tube hanging back and down from the waist, the sting at its tip
    ab = [T(*C(x + dx, y + dy)) for dx, dy in ((-0.6, 0.3), (-3.2, 1.4), (-5.8, 3.0), (-7.6, 4.4))]
    yel = "rglow" if glow else "hyel"
    p = r.tube(ab, [1.5, 2.6, 2.1, 0.9], banded(ab[0], ab[3], 3.2, "hblk", yel, phase=0.4), z + 0.1, bias=0.05)
    sa = math.atan2(ab[3][1] - ab[2][1], ab[3][0] - ab[2][0])
    st = (ab[3][0] + 2.2 * math.cos(sa), ab[3][1] + 2.2 * math.sin(sa))
    r.line(ab[3][0], ab[3][1], st[0], st[1], "hblk", z + 0.12, tone=1)
    r.dot(st[0], st[1], "rglow" if glow else "aglow", 3, z + 0.13)
    if glow:
        r.dot(ab[1][0] - 0.5, ab[1][1] - 1.4, "rglow", 4, z + 0.14)
    # wings: two membranes up and back from the shoulder (drawn behind the body)
    root = T(x + 2.2, y - 2.0)
    wa = wing_a + fold * 65
    wing(r, root, wa - 12, 9.5 - fold * 2.5, 3.6, z - 0.6, near=False)
    wing(r, (root[0] + 0.8, root[1] + 0.3), wa + 8, 9.0 - fold * 2.5, 3.2, z - 0.4, near=True)
    if blur:
        wing_blur(r, root, wa + 45, wa + 70, 6.5, z - 0.7, n=2)
    # thorax and head
    th = T(x + 2.8, y - 0.6)
    r.ell(th[0], th[1], 2.7, 2.4, "chit", z + 0.2, bias=0.12)
    r.ell(th[0] - 0.4, th[1] - 1.5, 1.3, 0.6, "hyel", z + 0.21, flat=3)
    hd = T(x + 6.2, y - 0.4)
    r.ell(hd[0], hd[1], 2.1, 2.0, "chit", z + 0.3, bias=0.08)
    r.ell(hd[0] + 1.0, hd[1] + 0.9, 1.0, 0.7, "hyel", z + 0.31, flat=2)
    eye(r, hd[0] + 0.2, hd[1] - 0.5, z + 0.32, glint=not dead, big=True)
    if hurt and not dead: r.dot(hd[0] + 0.2, hd[1] - 0.5, "white", 2, z + 0.33)
    mandible(r, (hd[0] + 1.6, hd[1] + 1.2), 70 + 30 * jaw, 1.8, -50, z + 0.31, rad=0.4, mat="amber")
    antenna(r, (hd[0] + 0.8, hd[1] - 1.7), -75 + tilt * 0.3, 4.6, 60 if not dead else 100, z + 0.29)
    # legs dangling under the thorax
    for k, dx in enumerate((-1.2, 0.4, 2.0)):
        hip = T(x + 2.6 + dx, y + 1.4)
        foot = (hip[0] - 1.5 + legs * (k - 1) * 0.6 - fold * 1.5 + k * 0.6, hip[1] + 3.4 - fold)
        leg(r, hip, foot, 1.9, 2.1, z + (0.4 if k != 1 else 0.05), "chit" if k != 1 else "dchit", near=k != 1, bend=-1)
    return hd, st


def drone(alt=6.0, tilt=0.0, curl=0.0, wing_a=-120.0, blur=1, glow=False, fold=0.0, legs=0.0, jaw=0.2, x=0.0, hurt=False,
          shadow=True, streak=0, extra=None, dead=False):
    r = Rig()
    if shadow: ground_shadow(r, x + 1.0, 3.5 if alt < 8 else 2.6)
    hd, st = drone_body(r, x=x - 1.5, y=-alt - 3.5, tilt=tilt, curl=curl, wing_a=wing_a, blur=blur, glow=glow, fold=fold,
                        legs=legs, jaw=jaw, hurt=hurt, dead=dead)
    if streak:
        for k in range(streak):
            smear(r, [(hd[0] - 6 - 3 * k, hd[1] - 1 + k), (hd[0] - 3 - 3 * k, hd[1] - 1 + k)], "wblur", 2, -1.0)
    if extra: extra(r, hd, st)
    return r.resolve()


def drone_set(glow, sfx):
    idle = [drone(alt=[2.6, 2.8, 3.0, 2.8][i], wing_a=[-150, -138, -148, -136][i], blur=1, curl=[0, 3, 6, 3][i], glow=glow,
                  legs=[0, 0.5, 1, 0.5][i]) for i in range(4)]
    run = [drone(alt=3.5 + 0.6 * math.sin(i / 6 * math.tau), tilt=14, wing_a=[-140, -100, -130, -95, -135, -105][i], blur=1,
                 curl=-5, glow=glow, legs=1.0, streak=1 if i % 2 else 0) for i in range(6)]
    # Dive: rise (0), wings fold and the body tips nose-down (1), DIVE through (2-4, streaks), pull up (5, 6)
    dive = [drone(alt=8.0, tilt=-10, wing_a=-110, blur=1, curl=10, glow=glow),
            drone(alt=9.0, tilt=-20, wing_a=-160, blur=0, fold=0.6, curl=20, glow=glow, jaw=0.8),
            drone(alt=4.0, tilt=25, blur=0, fold=1.0, curl=30, glow=glow, streak=2, x=2.0, jaw=1.0),
            drone(alt=3.0, tilt=30, blur=0, fold=1.0, curl=40, glow=glow, streak=3, x=4.0, jaw=1.0),
            drone(alt=3.5, tilt=20, blur=0, fold=0.9, curl=35, glow=glow, streak=2, x=5.0),
            drone(alt=5.0, tilt=0, wing_a=-110, blur=1, curl=10, glow=glow, x=3.0),
            drone(alt=6.0, tilt=0, wing_a=-125, blur=1, curl=0, glow=glow, x=1.0)]
    out = [("Idle" + sfx, idle, [0.06, 0.06, 0.06, 0.06]), ("Run" + sfx, run, [0.06] * 6),
           ("Dive" + sfx, dive, [0.14, 0.12, 0.05, 0.05, 0.06, 0.08, 0.1])]
    return out, idle


def drone_sheet(outdir):
    anims, idle = drone_set(False, "")
    # Sting: the abdomen swings forward under the body (0-2), FIRE (3), recoil (4), settle (5)
    sting = [drone(alt=6.5, curl=20, wing_a=-120), drone(alt=7.0, curl=50, tilt=-5, wing_a=-100),
             drone(alt=7.0, curl=80, tilt=-8, wing_a=-130),
             drone(alt=7.0, curl=95, tilt=-10, wing_a=-100, extra=lambda r, h, s: r.dot(s[0] + 1, s[1], "white", 3, 2.0)),
             drone(alt=7.5, curl=60, tilt=4, wing_a=-130), drone(alt=6.5, curl=15, wing_a=-110)]
    anims.insert(2, ("Sting", sting, [0.12, 0.1, 0.1, 0.05, 0.1, 0.12]))
    last, _ = drone_set(True, "Last")
    anims += last
    d0 = drone(alt=6.0, tilt=-30, blur=0, wing_a=-160, hurt=True, curl=30)
    d1 = drone(alt=3.0, tilt=-50, blur=0, wing_a=-175, hurt=True, curl=20, fold=0.4)
    d2 = drone(alt=-1.5, tilt=12, blur=0, wing_a=175, dead=True, curl=-10, fold=1.0, shadow=False,
               extra=lambda r, h, s: dust(r, 0, 0, 0))
    d3 = drone(alt=-2.0, tilt=14, blur=0, wing_a=178, dead=True, curl=-14, fold=1.0, shadow=False)
    knock = drone(alt=7.0, tilt=-28, blur=0, wing_a=-165, hurt=True, curl=25)
    anims += tail_anims(idle[0], [d0, d1, d2, d3], [0.08, 0.1, 0.12, 0.4], knock)
    return sheet("ZhkDrone", anims, outdir, scale=7)


SYNC["ZhkDrone"] = {"Sting": [("FIRE: the dart leaves the sting at (3, -4)", 3)],
                    "Dive": [("DIVE: wings folded, body hit from (6, -7)", 2)],
                    "DiveLast": [("LAST STING: dives and dies on the hero", 2)]}
NOTES["ZhkDrone"] = "IdleLast/RunLast/DiveLast: below 1 health the abdomen glows red (Last Sting)."


# ================================================================== RESIN BEETLE: a squat beetle, shovel mandibles
def beetle(lean=0.0, lift=0.0, jaw=0.3, fe=None, i=0, n=6, stride=0.0, glands=1.0, pump=0.0, head=0.0, hurt=False,
           dead=False, flip=False, extra=None, dust_at=None, splat_at=None, push=0.0):
    r = Rig()
    T = Xf(lean, (0.0, -3.0))
    cx, cy = T(-1.5 + push, -5.0 - lift)
    hips = [T(1.5 + push, -3.0 - lift), T(-0.8 + push, -2.8 - lift), T(-3.4 + push, -2.8 - lift),
            T(2.5 + push, -3.2 - lift), T(0.3 + push, -3.0 - lift), T(-2.5 + push, -3.0 - lift)]
    base = [(5.0 + push, 0.0), (1.0 + push, 0.0), (-5.5 + push, 0.0), (6.0 + push, 0.0), (2.0 + push, 0.0), (-4.5 + push, 0.0)]
    feet = fe or (gait6(i, n, hips, base, stride=stride, lift=1.0) if stride else base)
    if dead:
        feet = [(hips[k][0] + [1.5, 0.3, -1.2, 2.0, 0.6, -1.0][k], hips[k][1] - 2.5 - (k % 2)) for k in range(6)]
    legs6(r, hips, feet, 2.6, 2.8, -0.2, -2.0, mat="chit", far_mat="dchit")
    # under-plate and the domed shell: two clean elytra split by one dark seam, a single hard highlight
    r.ell(cx, cy + 1.6, 6.0, 2.0, "dchit", -0.5)
    sh = r.ell(cx, cy - 0.6, 6.6, 5.2, "chit", 0.0, flat=1)
    r.ell(cx - 0.4, cy - 1.0, 5.9, 4.5, "chit", 0.01, flat=2, part=sh)
    r.ell(cx - 1.2, cy - 1.9, 4.4, 3.2, "chit", 0.02, flat=3, part=sh)
    r.line(cx + 2.6, cy - 4.4, cx + 0.8, cy - 0.6, "chit", 0.05, tone=1, part=sh)
    r.ell(cx - 2.2, cy - 3.1, 2.0, 0.8, "chit", 0.04, flat=4, part=sh)
    r.dot(cx - 2.8, cy - 3.4, "white", 3, 0.045, part=sh)
    # resin glands: two tidy amber blisters on the rear wing case that swell with pump
    for k, (gx, gy) in enumerate(((-3.8, -1.0), (-1.6, -2.4))):
        s = (0.8 + 0.35 * glands) * (1.0 + 0.45 * pump * (k == 1))
        r.ell(cx + gx, cy + gy, s, s * 0.85, "amber", 0.1, bias=0.2)
        r.dot(cx + gx - 0.3, cy + gy - 0.4, "amber", 4, 0.11)
    # pronotum and head with shovel mandibles
    pr = T(4.6 + push, -5.0 - lift)
    r.ell(pr[0], pr[1], 2.6, 2.8, "chit", 0.3, bias=0.05)
    hx, hy = T(7.0 + push + head * 0.6, -3.8 - lift + head * 0.3)
    r.ell(hx, hy, 2.0, 1.8, "chit", 0.4, bias=0.0)
    eye(r, hx + 0.4, hy - 0.6, 0.45, glint=not dead, big=True)
    if hurt and not dead: r.dot(hx + 0.3, hy - 0.5, "white", 2, 0.46)
    a = 10 + 45 * jaw
    mandible(r, (hx + 1.4, hy + 0.2), -a * 0.6, 3.2, 55, 0.5, mat="amber", rad=0.85)
    mandible(r, (hx + 1.2, hy + 1.0), a * 0.6, 3.0, -45, 0.35, mat="chit", rad=0.8)
    antenna(r, (hx + 0.4, hy - 1.0), -110, 2.6, 60, 0.38)
    if dust_at: dust(r, *dust_at)
    if splat_at: splat(r, *splat_at, z=3.0, mat="amber")
    if extra: extra(r, (hx, hy))
    s = r.resolve()
    return s


def beetle_sheet(outdir):
    B = beetle
    idle = [B(lift=[0, 0.3, 0.5, 0.3][i], jaw=[0.2, 0.35, 0.5, 0.35][i], glands=[1.0, 1.1, 1.2, 1.1][i]) for i in range(4)]
    run = [B(i=i, n=6, stride=1.6, lift=0.3 * abs(math.sin(i / 6 * math.tau)), lean=4, jaw=0.3) for i in range(6)]
    # Snap: crouch (0), jaws wide (1), SNAP + shove forward (2), the head pushed out (3), recover (4, 5)
    snap = [B(lean=-6, lift=-0.4, jaw=0.6, head=-1.0), B(lean=-10, lift=-0.6, jaw=1.0, head=-1.5),
            B(lean=8, jaw=0.0, head=2.5, push=1.5, dust_at=(-3.0, 0, 0),
              extra=lambda r, h: smear(r, [(h[0] - 2, h[1] - 3), (h[0] + 3, h[1] - 3)], "white", 2, 3.0)),
            B(lean=10, jaw=0.1, head=3.0, push=2.0, dust_at=(-3.0, 0, 1)), B(lean=4, jaw=0.2, head=1.0, push=0.8),
            B(jaw=0.3)]
    # Resin: rear up (0), the middle gland pumps (1, 2), SPIT a glob along the floor (3), drip (4), settle (5)
    resin = [B(lean=-8, lift=0.5, jaw=0.4, pump=0.3), B(lean=-14, lift=1.0, jaw=0.6, pump=0.8),
             B(lean=-16, lift=1.2, jaw=0.9, pump=1.2), B(lean=6, lift=0.0, jaw=1.0, pump=0.0, splat_at=(10, -3, 0)),
             B(lean=3, jaw=0.6, extra=lambda r, h: drip(r, h[0] + 2.5, h[1] + 1.5, 2, 0.6, mat="amber")), B(jaw=0.3)]
    d = [B(lean=-15, lift=1.0, jaw=1.0, hurt=True), B(lean=-40, lift=1.0, jaw=0.8, hurt=True),
         B(lean=-178, lift=-7.0, jaw=0.5, dead=True, dust_at=(0, 0, 0)), B(lean=-180, lift=-7.5, jaw=0.6, dead=True)]
    knock = B(lean=-18, lift=1.2, jaw=0.9, hurt=True)
    anims = [("Idle", idle, [0.14, 0.12, 0.14, 0.12]), ("Run", run, [0.08] * 6),
             ("Snap", snap, [0.12, 0.1, 0.05, 0.08, 0.1, 0.12]), ("Resin", resin, [0.12, 0.1, 0.1, 0.06, 0.1, 0.12])]
    anims += tail_anims(idle[0], d, [0.1, 0.1, 0.12, 0.4], knock)
    return sheet("ZhkBeetle", anims, outdir, scale=7)


SYNC["ZhkBeetle"] = {"Snap": [("SNAP + SHOVE: jaws at (12, -3); box 12 x 12 at (11, -3)", 2)],
                     "Resin": [("SPIT: the resin glob leaves the jaws at (10, -3), runs along the floor", 3)]}

JOBS = [("ZhkGrub", grub_sheet), ("ZhkLarva", larva_sheet), ("ZhkDrone", drone_sheet), ("ZhkBeetle", beetle_sheet)]
