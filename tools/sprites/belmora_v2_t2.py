"""Bel'Mora tier 2: Bell Diver, Spinewalker, Salt Siren, Brine Lamprey, Bell Hermit, Anemone Boxer.
Built through belmora_v2_rigs.py. T2 idle limit 28 x 26."""
import math
from belmora_v2_rigs import (Rig, Xf, chain, ik, lerp, eye, spines, foam_ring, drips, bubbles, barnacles, leg, crab_legs,
                             claw, fin, kelp_strand, bell_shape, dust, splash, star, arc_smear, sheet, tail_anims, legend)


def wave_pts(x0, x1, y, amp, phase, n=10, waves=1.0):
    return [(lerp(x0, x1, i / (n - 1.0)), y + amp * math.sin(phase + waves * math.tau * i / (n - 1.0))) for i in range(n)]


def chain_links(r, a, b, z, mat="iron", sag=0.0, every=1.6):
    """A chain between two points: alternating lit and dark links, sagging by `sag` px at the middle."""
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(2, int(d / every))
    for i in range(n + 1):
        t = i / float(n)
        x = lerp(a[0], b[0], t); y = lerp(a[1], b[1], t) + sag * 4 * t * (1 - t)
        r.dot(x, y, mat, 3 if i % 2 else 1, z)


def anchor(r, x, y, ang, z, size=1.0):
    """An iron anchor whose ring is at (x, y), hanging along ang (deg, 90 = straight down)."""
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    L = 7.0 * size
    sx, sy = x + ca * L, y + sa * L
    r.tube([(x, y), (sx, sy)], [1.0, 1.0], "iron", z)
    r.dot(x, y, "iron", 3, z + 0.01); r.dot(x - ca, y - sa, "iron", 1, z)
    # stock across the shank near the ring, flukes at the crown
    px, py = -sa, ca
    r.line(x + ca * 1.5 - px * 2.5, y + sa * 1.5 - py * 2.5, x + ca * 1.5 + px * 2.5, y + sa * 1.5 + py * 2.5, "iron", z + 0.01, tone=2)
    for sgn in (-1, 1):
        fx, fy = sx + px * sgn * 3.2 * size - ca * 2.0, sy + py * sgn * 3.2 * size - sa * 2.0
        r.tube([(sx, sy), (sx + px * sgn * 2.0, sy + py * sgn * 2.0), (fx, fy)], [0.9, 0.8, 0.5], "iron", z + 0.005)
        r.dot(fx, fy, "rust", 3, z + 0.02)
    r.dot(sx, sy, "rust", 2, z + 0.02)
    return sx, sy


# ================================================================== BELL DIVER
def helmet(r, x, y, z, glow=1, tilt=0.0):
    """The brass diving helmet: a bronze dome, a cyan porthole, bolts round the collar."""
    r.ell(x, y, 5.0, 4.8, "bronze", z, bias=0.05)
    r.ell(x - 0.3, y + 4.2, 5.4, 1.4, "bronze", z + 0.01, bias=-0.2)            # collar
    for i in range(6): r.dot(x - 4.2 + i * 1.7, y + 4.2, "bronze", 4 if i < 2 else 3, z + 0.02)
    r.ell(x - 4.6, y + 0.5, 1.0, 1.4, "bronze", z + 0.02, bias=0.1)            # side window rim
    r.dot(x - 2.5, y - 2.5, "verd", 3, z + 0.02); r.dot(x - 3.2, y - 1.0, "verd", 2, z + 0.02)
    px, py = x + 1.8 + tilt, y + 0.2
    r.ell(px, py, 2.0, 2.0, "bronze", z + 0.03, flat=1)
    r.ell(px, py, 1.3, 1.3, "lure", z + 0.04, flat=2 + min(glow, 2))
    r.dot(px - 0.5, py - 0.6, "lure", 4, z + 0.05)
    if glow >= 2:
        for (dx, dy) in ((2, 0), (0, -2), (2, -1)): r.dot(px + dx + 0.5, py + dy, "lure", 1, z + 0.05)
    r.dot(x - 0.5, y - 4.6, "bronze", 2, z + 0.02); r.dot(x - 0.5, y - 5.4, "bronze", 3, z + 0.02)   # valve


def diver(lean=0.0, bob=0.0, feet=((-2.5, 0.0), (2.5, 0.0)), hand=(6.0, -10.0), hand2=(-5.0, -10.5), anchor_at=None,
          anchor_ang=90.0, glow=1, chain_to=None, smear=None, extra=None, hurt=False, bub=0, haul=False, crouch=0.0):
    r = Rig()
    hipy = -8.0 + bob + crouch
    T = Xf(lean, (0.0, hipy))
    # lead boots and canvas legs
    for k, (fx, fy) in enumerate(feet):
        hip = T(-1.6 + k * 3.0, hipy)
        z = 0.5 if k else -0.5
        kn = ik(hip[0], hip[1], fx, fy - 1.5, 4.0, 3.8, bend=1)
        r.tube([hip, kn, (fx, fy - 1.5)], [2.3, 2.1, 1.9], "canvas", z, bias=-0.25 if not k else 0.0)
        r.ell(fx + 0.8, fy - 1.3, 3.0, 1.7, "steel", z + 0.01, bias=-0.1 if k else -0.35)
        r.dot(fx - 0.5, fy - 2.4, "steel", 4, z + 0.02)
    # torso: a swollen canvas suit, a bronze weight-belt
    tx, ty = T(0.0, hipy - 4.5)
    r.ell(tx, ty, 7.2, 6.0, "canvas", 0.0)
    for (dx, dy) in ((-2.0, -2.0), (1.5, -3.0), (-0.5, 0.5)): r.dot(*T(dx, hipy - 4.5 + dy), "canvas", 1, 0.02)    # wet folds
    bx, by = T(0.0, hipy - 0.6)
    r.ell(bx, by, 6.2, 1.4, "bronze", 0.1, bias=-0.15)
    for i in range(3): r.dot(*T(-3 + i * 3, hipy - 0.8), "iron", 2, 0.15)
    # far arm, then helmet, then near arm
    sh2 = T(-4.4, hipy - 7.0)
    el2 = ik(sh2[0], sh2[1], hand2[0], hand2[1], 3.6, 3.4, bend=1)
    r.tube([sh2, el2, hand2], [1.8, 1.5, 1.4], "canvas", -1.0, bias=-0.35)
    r.ell(hand2[0], hand2[1], 1.4, 1.3, "rope", -0.95, bias=-0.2)
    hx, hy = T(0.5, hipy - 12.0)
    helmet(r, hx, hy, 1.0, glow=glow)
    if bub: bubbles(r, hx - 0.5, hy - 6.0, bub, n=2, rise=1.0)
    sh = T(4.2, hipy - 7.0)
    el = ik(sh[0], sh[1], hand[0], hand[1], 3.6, 3.4, bend=-1)
    r.tube([sh, el, hand], [1.9, 1.6, 1.5], "canvas", 2.5)
    r.ell(hand[0], hand[1], 1.5, 1.4, "rope", 2.55)                              # leather glove
    # the anchor on its chain: over the near shoulder, hanging from the hand
    if anchor_at is None:
        anchor_at = (hand[0] + 0.5, hand[1] + 2.0)
    chain_links(r, T(2.0, hipy - 9.5), hand, 2.6, sag=1.0)
    if chain_to:
        chain_links(r, hand, chain_to, 2.7, sag=0.5 if not haul else 0.0)
    else:
        chain_links(r, hand, anchor_at, 2.7)
        anchor(r, anchor_at[0], anchor_at[1], anchor_ang, 2.4, size=1.45)
    if hurt: r.dot(hx + 1.8, hy + 0.2, "bronze", 1, 1.2)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def diver_corpse(stage):
    r = Rig()
    r.ell(-2.0, -3.0, 6.0, 3.2, "canvas", 0.0, bias=-0.1)
    r.tube([(2.0, -2.0), (6.0, -1.5), (9.0, -1.4)], [1.6, 1.5, 1.4], "canvas", -0.2, bias=-0.2)
    r.ell(10.0, -1.4, 1.6, 1.4, "steel", 0.0, bias=-0.2)
    helmet(r, -8.5, -4.0, 1.0, glow=0 if stage else 1)
    anchor(r, 3.0, -6.0, 10, 1.5)
    if stage == 0: dust(r, -3, 0, 1)
    else: bubbles(r, -9.0, -10.0, 1, n=2)
    return r.resolve()


def diver_sheet(out):
    D = diver
    idle = [D(bob=[0, 0.3, 0.5, 0.3][i], glow=1 + (i == 2), hand=(8.0, -9.0 + [0, 0.3, 0.5, 0.3][i]), hand2=(-6.0, -10.0)) for i in range(4)]
    run = []
    for i in range(6):
        s = math.sin(i / 6 * math.tau)
        run.append(D(lean=6, bob=[0, -0.6, -1.0, 0, -0.6, -1.0][i], feet=((-2.5 + 2.5 * s, -max(0, -s) * 1.5), (2.5 - 2.5 * s, -max(0, s) * 1.5)),
                     hand=(6.5 + s, -10.0), anchor_ang=90 - s * 25, bub=i % 3))
    # Anchor (7): heave the anchor up over the helmet (0-2), SLAM it down in front (3), quake at the crown (4),
    # haul it back (5-6). The crown lands at (13, 0).
    anc = [D(lean=-4, hand=(3.0, -16.0), hand2=(0.0, -15.0), anchor_at=(2.0, -18.0), anchor_ang=-60, crouch=0.5),
           D(lean=-10, hand=(-1.0, -21.0), hand2=(-3.0, -20.0), anchor_at=(-3.0, -22.0), anchor_ang=-150, bob=-0.5, glow=2),
           D(lean=10, hand=(7.0, -18.0), hand2=(5.0, -17.0), anchor_at=(8.0, -20.0), anchor_ang=-20, glow=2,
             smear=[((-4, -24), (6, -24), "iron", 1), ((-6, -21), (4, -26), "iron", 2)]),
           D(lean=18, hand=(10.0, -8.0), hand2=(8.0, -8.5), anchor_at=(10.5, -7.0), anchor_ang=60, crouch=1.5, glow=2,
             smear=[((11, -20), (14, -10), "iron", 2)]),
           D(lean=18, hand=(10.0, -7.0), hand2=(8.0, -7.5), anchor_at=(10.5, -6.0), anchor_ang=70, crouch=1.5,
             extra=lambda r: dust(r, 13, 0, 0, 1.2)),
           D(lean=10, hand=(8.0, -8.0), hand2=(6.0, -9.0), anchor_at=(9.0, -6.0), anchor_ang=80, crouch=1.0,
             extra=lambda r: dust(r, 13, 0, 1, 1.4)),
           D(lean=2, hand=(6.5, -10.0))]
    # Hook (8): whirl the anchor overhead on its chain (0-1), THROW (2: the hook leaves the hand at (10, -16)), the
    # chain runs out (3-5), the arm stays out (6), recover (7)
    hook = [D(lean=-4, hand=(3.0, -19.0), anchor_at=(-2.0, -22.0), anchor_ang=-120, glow=2),
            D(lean=-8, hand=(1.0, -20.0), anchor_at=(6.0, -24.0), anchor_ang=-30, glow=2,
              smear=[((-4, -22), (2, -26), "iron", 1)]),
            D(lean=12, hand=(9.0, -15.0), chain_to=(13.0, -16.0), glow=2, smear=[((0, -24), (8, -20), "iron", 2)]),
            D(lean=10, hand=(9.0, -14.0), chain_to=(14.0, -15.0), glow=1),
            D(lean=8, hand=(9.0, -13.5), chain_to=(14.0, -14.0), glow=1),
            D(lean=6, hand=(8.5, -13.0), chain_to=(14.0, -13.0), glow=1),
            D(lean=4, hand=(8.0, -12.0), chain_to=(13.0, -12.0), glow=1),
            D(lean=0, hand=(6.0, -10.0))]
    # Haul (4, loop): shoulder first along the taut chain, both hands on it, the porthole flaring
    haul = []
    for i in range(4):
        s = math.sin(i / 4 * math.tau)
        haul.append(D(lean=20, bob=-0.5 + 0.3 * s, hand=(9.0 + s * 0.5, -12.0), hand2=(7.0 - s * 0.5, -12.5), chain_to=(14.0, -12.5),
                      haul=True, glow=2, feet=((-4.0 + 2 * s, 0.0), (1.0 - 2 * s, -max(0, s))),
                      extra=(lambda r, i=i: dust(r, -5, 0, i % 3, 0.7))))
    d0 = D(hurt=True, lean=-12, hand=(5.0, -14.0), bob=-0.5)
    d1 = D(hurt=True, lean=-30, hand=(3.0, -6.0), anchor_at=(5.0, -2.0), anchor_ang=10, crouch=2.0, glow=0)
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.09] * 6),
             ("Anchor", anc, [0.14, 0.14, 0.08, 0.05, 0.12, 0.12, 0.14]),
             ("Hook", hook, [0.12, 0.12, 0.05, 0.08, 0.1, 0.1, 0.12, 0.14]), ("Haul", haul, [0.08] * 4)]
    anims += tail_anims(idle[0], [d0, d1, diver_corpse(0), diver_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        D(hurt=True, lean=-14, hand=(5.0, -13.0), bob=-0.6))
    return sheet("BelDiver", anims, out)


# ================================================================== SPINEWALKER
def spinewalker(bob=0.0, lean=0.0, legs=None, stab=None, eggs=3, eggs_drop=0.0, squat=0.0, rot=0.0, hurt=False,
                smear=None, extra=None, glow=True):
    """An urchin up on four tall spine-stilts. legs: four (x, y) foot points (back far, back near, front far, front
    near); stab: (x, y) for the front near stilt's spear point."""
    r = Rig()
    cy = -14.0 + bob + squat
    T = Xf(lean, (0, cy))
    legs = legs or [(-9.0, 0.0), (-4.0, 0.0), (4.0, 0.0), (9.0, 0.0)]
    hips = [T(-3.5, cy + 3.5), T(-1.5, cy + 4.5), T(1.5, cy + 3.5), T(3.5, cy + 4.5)]
    for k in range(4):
        fx, fy = legs[k] if not (k == 3 and stab) else stab
        near = k % 2 == 1
        hx, hy = hips[k]
        kx, ky = (hx + fx) / 2 + (1.5 if fx > hx else -1.5), min(hy, fy) - 0.0 + (fy - hy) * 0.45
        z = 1.5 if near else -1.5
        kx, ky = hx + (fx - hx) * 0.65, hy - 2.5 + (fy - hy) * 0.25
        r.tube([(hx, hy), (kx, ky), (fx, fy)], [1.4, 1.1, 0.6], "spinev", z, bias=0.25 if near else -0.2)
        r.dot(fx, fy, "ivory", 3 if near else 2, z + 0.01)
        r.dot(kx, ky, "spinev", 4 if near else 2, z + 0.01)
    # pink egg clusters tucked under the body
    for i in range(eggs):
        ex, ey = T(-2.5 + i * 2.5, cy + 5.2 + (i % 2) * 0.5 + eggs_drop * (2 + i))
        r.ell(ex, ey, 1.2, 1.0, "pink", 0.6, bias=0.1)
    cx, cyy = T(0, cy)
    spines(r, cx, cyy, 9.4, 7.2, 32, 3.8, "spinev", -1.0, phase=math.radians(rot), front=False, tips=3, skip_down=True)
    r.ell(cx, cyy, 9.4, 7.2, "teal", 0.0)
    for (dx, dy) in ((-2, -3), (1, -3.5), (3, -1.5), (-3.5, -0.5), (0.5, 0)): r.dot(cx + dx, cyy + dy, "teal", 1, 0.05)
    if glow:
        eye(r, cx + 3.0, cyy - 0.5, 1.5, big=True); eye(r, cx + 0.5, cyy - 1.0, 1.5)
    if hurt: r.dot(cx + 3.0, cyy - 0.5, "teal", 4, 1.6)
    spines(r, cx, cyy, 9.4, 7.2, 32, 3.8, "spinev", 1.0, phase=math.radians(rot), front=True, tips=2, skip_down=True)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def spinewalker_corpse(stage):
    r = Rig()
    spines(r, 1.0, -4.0, 5.4, 3.6, 18, 3.0, "spinev", -1.0, front=False, phase=0.3)
    r.ell(1.0, -4.0, 5.4, 3.6, "teal", 0.0, bias=-0.15)
    spines(r, 1.0, -4.0, 5.4, 3.6, 18, 3.0, "spinev", 1.0, front=True, phase=0.3, tone=2)
    for (a, b) in (((-4, -2), (-12, -1)), ((-3, -1), (-9, 0)), ((5, -2), (12, -1)), ((4, -1), (10, 0))):
        r.line(*a, *b, "spinev", 0.5, tone=2)
    for i in range(2): r.ell(-2 + i * 6, -0.8, 1.1, 0.8, "pink", 1.0, bias=-0.2 if stage else 0.1)
    if stage == 0: dust(r, 0, 0, 1)
    return r.resolve()


def spine_sheet(out):
    S = spinewalker
    idle = [S(bob=[0, -0.3, -0.6, -0.3][i], rot=[0, 3, 6, 3][i], lean=[0, -1, -2, -1][i]) for i in range(4)]
    run = []
    for i in range(6):
        ph = i / 6 * math.tau
        lg = []
        for k, (bx, off) in enumerate(((-9.0, 0.0), (-4.0, 0.5), (4.0, 0.5), (9.0, 0.0))):
            p = ph + off * math.tau
            lg.append((bx + 2.5 * math.sin(p), -max(0.0, math.cos(p)) * 3.5))
        run.append(S(legs=lg, bob=-0.8 * abs(math.sin(ph)), rot=-6 * i, lean=4))
    # Stab (6): the front stilt rises (0-1), SPEARS the floor ahead (2: tip at (13, 0)), held (3), pulled free (4-5)
    stab = [S(stab=(6.0, -8.0), lean=-4, bob=-0.5), S(stab=(8.0, -11.0), lean=-8, bob=-1.0),
            S(stab=(13.0, 0.0), lean=10, smear=[((9, -11), (13, -3), "spinev", 2)], extra=lambda r: dust(r, 13, 0, 0, 0.8)),
            S(stab=(13.0, 0.0), lean=10, extra=lambda r: dust(r, 13, 0, 1, 0.9)),
            S(stab=(11.0, -3.0), lean=4), S(lean=0)]
    # Sow (7): squat low on the stilts (0-2), let the eggs go (3-4), rise (5-6)
    sow = [S(squat=1.5), S(squat=3.0, lean=-3), S(squat=4.0, lean=-4, eggs_drop=0.3), S(squat=4.0, eggs_drop=0.8, eggs=3),
           S(squat=3.0, eggs=0, extra=lambda r: [r.ell(x, -1.0, 1.4, 1.1, "pink", 1.0) for x in (-4, 0, 4)]),
           S(squat=1.5, eggs=0), S(eggs=0)]
    d0 = S(hurt=True, lean=-10, bob=-1.0)
    d1 = S(hurt=True, lean=-25, squat=5.0, legs=[(-9, 0), (-4, 0), (5, 0), (10, 0)], glow=False)
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.09] * 6),
             ("Stab", stab, [0.14, 0.12, 0.05, 0.12, 0.12, 0.14]), ("Sow", sow, [0.12, 0.12, 0.12, 0.1, 0.12, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, spinewalker_corpse(0), spinewalker_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        S(hurt=True, lean=-14, bob=-1.0))
    return sheet("BelSpinewalker", anims, out)


# ================================================================== SALT SIREN
SIREN_LEG = legend(k="drown:0", d="drown:1", s="drown:2", S="drown:3", L="drown:4", e="lure:3", E="lure:4", m="drown:0",
                   h="kelp:1", H="kelp:2", K="kelp:3", n="tent:2")
SIREN_FACE = {
    # pivot (3, 6): the chin. A gaunt drowned face, hollow cheeks, white-cyan eyes, kelp hair over the brow.
    "calm": """
.hHKH..
hHsSsH.
HsSLSsH
hseSesh
.sSSSs.
.dsmsd.
..dsd..
""",
    "sing": """
.hHKH..
hHsSsH.
HsSLSsH
hsEsEsh
.sSSSs.
.dsmms.
..dmd..
""",
    "hurt": """
.hHKH..
hHsSsH.
HsSLSsH
hsmsmsh
.sSSSs.
.dmmmd.
..dsd..
""",
}


def siren(bob=0.0, lean=0.0, sway=0.0, hand=(6.0, -14.0), hand2=(-4.0, -13.0), face="calm", tail=0.0, throat=1,
          coil=0.0, smear=None, extra=None, notes=None, hair_k=0):
    r = Rig()
    by = -8.0 + bob
    T = Xf(lean, (0.0, by + 3.0))
    # the fish tail coiled under the gown: a scaled sea-green curl on the floor
    tp = [T(-1.0, by + 2.0), (-3.5 + tail * 0.5, -2.0 - coil), (-6.0 + tail, -1.2), (-8.5 + tail * 1.5, -2.5 + coil * 0.5),
          (-10.0 + tail * 2.0, -4.5 + coil)]
    r.tube(tp, [3.0, 2.6, 2.0, 1.3, 0.8], "sea", -0.5)
    for i in range(1, 4): r.dot(tp[i][0], tp[i][1] - 1.0, "sea", 4, -0.45)
    ex, ey = tp[-1]
    fin(r, [(ex, ey), (ex - 2.5, ey - 3.0), (ex - 1.0, ey - 0.5), (ex - 3.0, ey + 1.0)], "sea", -0.6, bias=0.1)
    # a gown of drowned kelp over a scaled sea-green shift: kelp ribbons hang from the bodice and sway with her, the
    # hem ragged where they end; a violet trim at the bodice
    gx, gy = T(0.0, by)
    hem = [(gx - 7.0 + i * 1.75, 0.0 - (1.5 if i % 2 else 0.0)) for i in range(9)]
    r.poly([T(-3.2, by - 6.5), T(3.2, by - 6.5), (gx + 7.0, -1.0)] + hem[::-1] + [(gx - 7.0, -1.0)], "sea", 0.0, curve=0.7)
    for row in range(5):
        for c in range(-3, 4):
            sx_, sy_ = T(c * 1.8 + (0.9 if row % 2 else 0.0), by - 4.5 + row * 2.0)
            r.dot(sx_, sy_, "sea", 4 if c < 0 else 3, 0.02)
    for i in range(7):
        top = T(-3.0 + i * 1.0, by - 6.0)
        ln = 6 + (i * 3) % 4
        bot_x = gx - 6.5 + i * 2.15
        pts = [top] + [(lerp(top[0], bot_x, j / float(ln)) + math.sin(hair_k * 0.9 + i + j * 0.7) * 0.7 * (j / float(ln)),
                        lerp(top[1], -0.5 - (i % 2), j / float(ln))) for j in range(1, ln + 1)]
        r.polyline(pts, "kelp", 0.05 + i * 0.001, tones=[3 if i < 4 else 2] * len(pts))
        r.dot(pts[-1][0], pts[-1][1] + 1, "kelp", 1, 0.05)
    r.poly([T(-3.2, by - 6.6), T(3.2, by - 6.6), T(1.5, by - 5.2), T(-1.5, by - 5.2)], "tent", 0.07, bias=0.1)   # bodice
    for i in range(0, 9, 2): r.dot(hem[i][0], hem[i][1] - 0.5, "tent", 3, 0.06)
    # far arm
    sh2 = T(-2.5, by - 6.0)
    el2 = ik(sh2[0], sh2[1], hand2[0], hand2[1], 3.2, 3.0, bend=1)
    r.tube([sh2, el2, hand2], [0.9, 0.8, 0.7], "drown", -1.0, bias=-0.35)
    # gaunt chest and neck, the throat glowing
    r.ell(*T(0.0, by - 7.5), 3.4, 2.7, "drown", 0.5)
    for i in range(3): r.dot(*T(-1.0 + i, by - 8.0 + (i % 2)), "drown", 1, 0.55)                 # ribs
    nx, ny = T(0.5, by - 10.5)
    r.tube([T(0.0, by - 9.0), (nx, ny)], [1.2, 1.1], "drown", 0.6)
    r.dot(nx, ny + 0.5, "lure", 2 + min(throat, 2), 0.7)
    if throat >= 2:
        for (dx, dy) in ((-1, 0), (1, 0), (0, 1)): r.dot(nx + dx, ny + 0.5 + dy, "lure", 1 + (throat >= 3), 0.69)
    # streaming kelp hair down her back
    hx, hy = T(0.5 + sway * 0.3, by - 14.0)
    r.poly([(hx - 1.0, hy - 3.5), (hx - 4.0, hy - 2.0), (hx - 6.0 + sway * 0.4, hy + 5.0), (hx - 5.0 + sway * 0.5, hy + 10.0),
            (hx - 2.5, hy + 8.0), (hx - 1.5, hy + 3.0)], "kelp", -0.7, bias=-0.15, curve=0.4)
    for k in range(5):
        kelp_strand(r, hx - 2.0 - k * 0.6, hy - 1.0 + k * 0.4, 7 + k * 1.5, -1.5 - k * 0.3 + sway, -0.8 - k * 0.01, k=hair_k + k)
    r.stamp(SIREN_FACE[face], hx, hy + 3.0, 2.0, SIREN_LEG, pivot=(3, 6))
    # near arm
    sh = T(2.5, by - 6.0)
    el = ik(sh[0], sh[1], hand[0], hand[1], 3.2, 3.0, bend=-1)
    r.tube([sh, el, hand], [1.0, 0.9, 0.8], "drown", 2.5)
    r.dot(hand[0] + 1, hand[1], "drown", 4, 2.55)
    if notes:
        for (x, y, k) in notes:
            r.dot(x, y, "lure", 3, 6.0); r.line(x + 1, y, x + 1, y - 3, "lure", 6.0, tone=2)
            if k: r.dot(x + 2, y - 3, "lure", 2, 6.0)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def siren_corpse(stage):
    r = Rig()
    r.tube([(4, -1.5), (-1, -2.0), (-6, -1.5), (-10, -2.5)], [2.4, 2.0, 1.4, 0.7], "sea", -0.5, bias=-0.15)
    fin(r, [(-10, -2.5), (-12.5, -5), (-11, -2), (-13, -1)], "sea", -0.6)
    r.poly([(0, -1), (6, -4), (9, -1), (8, 0), (0, 0)], "sea", 0.0, bias=-0.1)
    r.stamp(SIREN_FACE["hurt"], 11.0, -1.0, 1.0, SIREN_LEG, pivot=(3, 6))
    for k in range(3): kelp_strand(r, 13 + k, -4 + k, 4, 2.0, 0.9, k=k)
    if stage == 0: r.dot(9.0, -3.0, "lure", 2, 1.2)
    return r.resolve()


def siren_sheet(out):
    Sr = siren
    idle = [Sr(bob=[0, -0.3, -0.5, -0.3][i], sway=[0, 1, 2, 1][i], hair_k=i, tail=[0, 0.5, 1, 0.5][i],
               hand=(5.5, -13.5 + [0, 0.3, 0.5, 0.3][i])) for i in range(4)]
    run = [Sr(bob=[0, -0.5, -1.0, -0.5, 0, -0.5][i], lean=8, sway=-2 + i % 3, hair_k=i, coil=[0, 1, 2, 1, 0, -1][i] * 0.6,
              tail=[0, 1.5, 3, 1.5, 0, -1.5][i], hand=(4.0, -11.0), hand2=(-5.0, -10.0)) for i in range(6)]
    # Bolt (6): draw the water to the palm (0-1), THROW (3: the bolt leaves the hand at (11, -15)), follow (4-5)
    bolt = [Sr(hand=(3.0, -16.0), lean=-4, face="sing", throat=2), Sr(hand=(1.0, -18.0), lean=-8, face="sing", throat=2,
                                                                       extra=lambda r: r.ell(1.0, -19.5, 1.4, 1.4, "water", 6.0)),
            Sr(hand=(7.0, -17.0), lean=4, face="sing", throat=2, smear=[((0, -21), (6, -19), "water", 3)]),
            Sr(hand=(10.0, -15.0), lean=10, face="calm", extra=lambda r: splash(r, 12.0, -15.0, 0, 0.5)),
            Sr(hand=(9.0, -13.0), lean=6), Sr(hand=(6.0, -13.5), lean=0)]
    # Song (8): head back, throat blazing, notes rippling out (2-7)
    song = []
    for i in range(8):
        k = min(3, 1 + i // 2)
        song.append(Sr(lean=-6 - 2 * math.sin(i), face="sing", throat=3 if i >= 2 else 2, hand=(5.0, -18.0 - (i % 2)),
                       hand2=(-5.0, -17.0 + (i % 2)), sway=2 + i % 3, hair_k=i,
                       notes=[(6 + (i % 4) * 2, -20 - (i % 4), i % 2), (-4 - (i % 3) * 2, -21 - (i % 3), 0)] if i >= 2 else None))
    d0 = Sr(face="hurt", lean=-12, throat=0, hand=(5.0, -16.0))
    d1 = Sr(face="hurt", lean=-35, throat=0, bob=2.0, hand=(4.0, -8.0), coil=1.0)
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.09] * 6),
             ("Bolt", bolt, [0.14, 0.12, 0.08, 0.06, 0.12, 0.14]), ("Song", song, [0.12] * 8)]
    anims += tail_anims(idle[0], [d0, d1, siren_corpse(0), siren_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        Sr(face="hurt", lean=-15, hand=(5.0, -15.0)))
    return sheet("BelSiren", anims, out)


# ================================================================== BRINE LAMPREY
def sucker(r, x, y, z, open_=1.0, ang=0.0, size=2.6):
    """The round sucker mouth, seen face-on: a raw pink disc ringed with ivory teeth."""
    rx, ry = size * (0.6 + 0.4 * open_), size
    r.ell(x, y, rx, ry, "slate", z, ang=ang)
    r.ell(x + 0.5, y, rx * 0.75, ry * 0.75, "pink", z + 0.01, flat=1, ang=ang)
    r.ell(x + 0.7, y, rx * 0.35, ry * 0.4, "pink", z + 0.02, flat=0, ang=ang)
    for i in range(8):
        a = i / 8 * math.tau
        r.dot(x + 0.5 + math.cos(a) * rx * 0.62, y + math.sin(a) * ry * 0.62, "ivory", 3 if math.sin(a) < 0 else 2, z + 0.03)


def lamprey(phase=0.0, amp=1.6, head=(10.0, -8.5), lift=0.0, x0=-14.5, mouth=0.5, gill=True, hurt=False, smear=None,
            extra=None, latch=False, tail_up=0.0):
    """A long low slate eel: a travelling wave from the tail to the head, a round sucker for a mouth."""
    r = Rig()
    hx, hy = head
    if not latch: hy -= 5.0      # the head carried a little off the floor
    if latch:
        # hanging off the hero's side, mouth first (the head is at (6, -8)), the tail thrashing below and behind
        pts = [(hx - 1.0, hy)] + [(hx - 3.0 - i * 1.6 + math.sin(phase + i) * (1.0 + i * 0.25), hy + 1.5 + i * 1.4) for i in range(7)]
        pts = pts[::-1]
    else:
        n = 12
        pts = [(lerp(x0, hx - 2.0, i / (n - 1.0)),
                -2.6 - lift * (i / (n - 1.0)) ** 2 + (hy + 6.0) * (i / (n - 1.0)) ** 3
                + amp * math.sin(phase + i * 0.8) * (0.3 + 0.7 * (1 - i / (n - 1.0))) - tail_up * (1 - i / (n - 1.0)) ** 2)
               for i in range(n)]
    radii = [0.9 + 3.5 * (i / (len(pts) - 1.0)) ** 0.6 for i in range(len(pts))]
    r.tube(pts, radii, "slate", 0.0)
    # pale belly line and the dorsal fin ridge along the back half
    for i in range(2, len(pts) - 1):
        r.dot(pts[i][0], pts[i][1] + radii[i] * 0.7, "hag", 2, 0.05)
        if i < len(pts) - 4 and i % 2: r.dot(pts[i][0], pts[i][1] - radii[i] - 0.6, "slate", 3, -0.1)
    if gill:
        for i in range(7):
            j = len(pts) - 2 - i // 4
            t = (i % 4) / 4.0
            gx = lerp(pts[j][0], pts[j - 1][0], t) - 0.5
            gy = lerp(pts[j][1], pts[j - 1][1], t) - 0.2
            r.dot(gx - i * 0.0, gy, "lure", 3 if i % 2 == 0 else 2, 0.2)
    sucker(r, hx, hy, 0.5, open_=mouth, size=3.8)
    eye(r, hx - 2.8, hy - 2.6, 0.6, big=True)
    if hurt: r.dot(hx - 2.2, hy - 2.0, "slate", 4, 0.7)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def lamprey_sheet(out):
    Lm = lamprey
    idle = [Lm(phase=i * math.tau / 4, head=(9.0, -6.0 - [0, 0.3, 0.5, 0.3][i]), mouth=[0.5, 0.6, 0.8, 0.6][i]) for i in range(4)]
    run = [Lm(phase=i * math.tau / 6, amp=2.0, head=(9.5, -5.5 - 0.5 * math.sin(i)), mouth=0.4) for i in range(6)]
    # Rasp (6): rear the head up (0-1), DART down and bite (3: sucker at (13, -5)), grind (4), let go (5)
    rasp = [Lm(head=(7.0, -10.0), lift=2.0, mouth=0.6), Lm(head=(5.0, -12.0), lift=4.0, mouth=1.0),
            Lm(head=(11.0, -7.0), mouth=1.0, smear=[((5, -13), (10, -9), "slate", 2)]),
            Lm(head=(13.0, -5.0), mouth=0.2, extra=lambda r: star(r, 16.0, -5.0, 1)),
            Lm(head=(12.5, -5.0), mouth=0.4, phase=1.0), Lm(head=(10.0, -6.0), mouth=0.6, phase=2.0)]
    # Lunge (8): coil back (0-1), LAUNCH flat along the floor (2-4: the whole body slides 70 px; drawn as a lean
    # streak), land (5), settle (6-7)
    lunge = [Lm(head=(6.0, -5.0), amp=3.0, x0=-11.0, mouth=0.3), Lm(head=(4.0, -4.0), amp=3.5, x0=-10.0, mouth=0.8, phase=1.5),
             Lm(head=(13.0, -4.0), amp=0.4, x0=-9.0, mouth=1.0, smear=[((-14, -3), (-8, -3), "slate", 2), ((-12, -1), (-6, -1), "slate", 1)]),
             Lm(head=(14.0, -4.0), amp=0.3, x0=-8.0, mouth=1.0, smear=[((-12, -3), (-6, -3), "slate", 2)]),
             Lm(head=(14.0, -4.5), amp=0.6, x0=-9.0, mouth=1.0),
             Lm(head=(13.0, -5.0), amp=1.0, x0=-10.0, mouth=0.3, extra=lambda r: dust(r, 12, 0, 1, 0.8)),
             Lm(head=(11.0, -5.5), amp=1.2, mouth=0.4, phase=1.0), Lm(head=(9.0, -6.0), mouth=0.5)]
    latch = [Lm(latch=True, head=(6.0, -9.0), phase=i * math.tau / 4, mouth=0.1) for i in range(4)]
    d0 = Lm(hurt=True, head=(7.0, -9.0), lift=3.0, mouth=1.0, amp=2.5)
    d1 = Lm(hurt=True, head=(10.0, -3.0), mouth=1.0, amp=3.0, phase=2.0, gill=False)
    dead = [Lm(head=(11.0, -2.5), mouth=1.0, amp=1.0 - 0.5 * k, phase=2.5, gill=False, tail_up=-1.0) for k in range(2)]
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Rasp", rasp, [0.14, 0.12, 0.05, 0.08, 0.12, 0.14]),
             ("Lunge", lunge, [0.12, 0.14, 0.05, 0.05, 0.06, 0.1, 0.12, 0.14]), ("Latched", latch, [0.07] * 4)]
    anims += tail_anims(idle[0], [d0, d1] + dead, [0.08, 0.12, 0.14, 0.4], Lm(hurt=True, head=(6.0, -8.0), lift=2.0, mouth=1.0))
    return sheet("BelLamprey", anims, out)


# ================================================================== BELL HERMIT
def hermit(bob=0.0, phase=0.0, claw_at=None, claw_open=0.3, out=1.0, tilt=0.0, full=False, drip=0, hurt=False,
           smear=None, extra=None, ring=0, legs_up=0.0, lift=3.0):
    """A hermit crab living in a small bronze bell: the bell rides on its back like a dome, red legs scuttle under
    the lip, the eye stalks and the big claw poke out in front. out 0..1: how far it is out (0 = the bell is down)."""
    r = Rig()
    base = -lift * out + bob
    if out > 0.2:
        crab_legs(r, 0.0, base - 1.5, 7.0, 3, phase, "coral", 1.4, -0.6, step=1.6, reach=3.0, lift=1.2 + legs_up,
                  knee=2.0, spread=1.6, rad=0.6)
    bell_shape(r, -0.5, base, 19.0, 18.0, 0.0, tilt=tilt)
    if full:
        # a load of brine sloshing at the lip, dripping
        for i in range(5):
            r.dot(-6.0 + i * 3.0 + (drip % 2), base - 1.5, "water", 4 if i % 2 else 3, 0.05)
        drips(r, [(-5.5, base + 0.5), (6.0, base + 0.5)], drip, 0.1)
    if ring:
        for i in range(ring):
            rr = 10 + i * 3
            for a in range(-150, -20, 20):
                aa = math.radians(a)
                r.dot(-0.5 + math.cos(aa) * rr, base - 8 + math.sin(aa) * rr * 0.8, "spark", 3 - i, 6.0)
    if out > 0.2:
        hx, hy = 7.0 + 1.5 * out, base - 1.0
        r.ell(hx - 1.0, hy - 0.5, 2.6, 2.0, "coral", 1.0, bias=0.05)
        for ex in (hx - 0.5, hx + 1.4):
            r.line(ex, hy - 1.5, ex + 0.5, hy - 5.0, "coral", 1.1, tone=3)
            eye(r, ex + 0.5, hy - 5.5, 1.2)
        if hurt: r.dot(hx + 1.9, hy - 5.5, "coral", 4, 1.3)
        cx, cy = claw_at or (hx + 4.5, hy + 0.5)
        r.tube([(hx, hy + 0.5), (cx - 2.0, cy)], [1.2, 1.0], "coral", 1.6)
        claw(r, cx, cy, -10 + (cx - hx - 4) * 3, 2.6 * min(1, out + 0.2), "coral", 1.7, open_=claw_open, tip="ivory")
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def hermit_sheet(out):
    H = hermit
    idle = [H(bob=[0, 0, -0.3, 0][i], phase=0.0, claw_open=[0.3, 0.4, 0.6, 0.4][i], claw_at=(12.5, -2.0 - [0, 0.3, 0.6, 0.3][i]))
            for i in range(4)]
    run = [H(phase=i / 6.0, bob=[0, -0.4, 0, -0.4, 0, -0.4][i], tilt=[0, 2, 0, -2, 0, 2][i]) for i in range(6)]
    full_i = [H(bob=[0, 0, -0.3, 0][i], full=True, drip=i, claw_at=(12.5, -2.0)) for i in range(4)]
    full_r = [H(phase=i / 6.0, bob=[0, -0.4, 0, -0.4, 0, -0.4][i], tilt=[0, 3, 0, -3, 0, 3][i], full=True, drip=i) for i in range(6)]
    # Crush (7): draw the claw back (0-1), LUNGE and crush (3: claw tip at (17, -4)), hold (4), back (5-6)
    crush = [H(claw_at=(10.5, -6.0), claw_open=0.9, tilt=-3), H(claw_at=(9.5, -7.0), claw_open=1.0, tilt=-6),
             H(claw_at=(15.0, -4.0), claw_open=0.9, tilt=4, smear=[((10, -8), (15, -6), "coral", 2)]),
             H(claw_at=(17.0, -2.5), claw_open=0.0, tilt=6, extra=lambda r: star(r, 20.0, -2.5, 1)),
             H(claw_at=(16.0, -3.0), claw_open=0.1, tilt=4), H(claw_at=(13.0, -2.5), claw_open=0.3), H()]
    # Shell (8): pull in (0-1), the bell sets down over it (2), rings with each hit (2-6), come out (7)
    shell = [H(out=0.6), H(out=0.25), H(out=0.0, ring=1), H(out=0.0, ring=2), H(out=0.0), H(out=0.0), H(out=0.0, ring=1), H(out=0.6)]
    d0 = H(hurt=True, tilt=-8, claw_open=1.0)
    d1 = H(hurt=True, tilt=-14, out=0.5, legs_up=1.0)
    corpse = [H(out=0.5, tilt=-75 + 5 * k, bob=-2.0, legs_up=2.0, lift=1.0) for k in range(2)]
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("IdleFull", full_i, [0.16, 0.14, 0.16, 0.14]), ("RunFull", full_r, [0.08] * 6),
             ("Crush", crush, [0.14, 0.12, 0.06, 0.06, 0.12, 0.12, 0.12]),
             ("Shell", shell, [0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.12])]
    anims += tail_anims(idle[0], [d0, d1] + corpse, [0.08, 0.12, 0.14, 0.4], H(hurt=True, tilt=-10, claw_open=0.9))
    return sheet("BelHermit", anims, out)


# ================================================================== ANEMONE BOXER
def glove(r, x, y, z, k=0, size=4.0, near=True):
    """An anemone boxing glove: a pink-violet ball fringed with waving tentacle tips."""
    r.ell(x, y, size, size * 0.9, "pink", z, bias=0.05 if near else -0.25)
    for i in range(8):
        a = i / 8 * math.tau + k * 0.4
        tx, ty = x + math.cos(a) * (size + 1.0), y + math.sin(a) * (size * 0.9 + 0.8)
        r.dot(tx, ty, "tent" if i % 2 else "pink", 3 if math.sin(a) < 0 else 2, z + 0.01)
    r.dot(x - 0.8, y - 0.8, "pink", 4, z + 0.02)


def boxer(bob=0.0, lean=0.0, feet=((-5.0, 0.0), (5.0, 0.0)), g1=(8.5, -14.0), g2=(3.5, -13.0), k=0, hurt=False,
          smear=None, extra=None, puffs=None, crouch=0.0):
    """A crab up on its hind legs, an anemone on each claw like a boxing glove. g1 near glove, g2 far glove."""
    r = Rig()
    hy = -8.0 + bob + crouch
    T = Xf(lean, (0.0, hy))
    # hind legs (thin, jointed) and the tucked walking legs
    for i, (fx, fy) in enumerate(feet):
        hip = T(-1.5 + i * 3.0, hy + 0.5)
        kn = (hip[0] + (fx - hip[0]) * 0.5 + (2.0 if i else -2.0), (hip[1] + fy) * 0.5 - 1.5)
        r.tube([hip, kn, (fx, fy)], [1.7, 1.3, 0.9], "orange", 0.5 if i else -0.5, bias=0.0 if i else -0.3)
        r.dot(fx + (1 if i else -1), fy, "orange", 1, 0.55)
    for i in range(3):
        a, b = T(-5.0, hy - 1.0 - i * 2.0), T(-10.5 - i * 0.5, hy + 0.5 - i * 1.5)
        r.tube([a, b], [0.9, 0.6], "orange", -0.8, bias=-0.3)
        r.dot(*b, "orange", 1, -0.8)
    # the fan of its tail under the shell
    r.poly([T(-2.0, hy + 0.0), T(-9.5, hy + 4.0), T(-8.0, hy + 7.5), T(-3.0, hy + 8.0), T(-1.0, hy + 3.0)], "orange", -0.3, bias=-0.2)
    # far arm and glove
    sh2 = T(-1.5, hy - 8.0)
    r.tube([sh2, ((sh2[0] + g2[0]) / 2, (sh2[1] + g2[1]) / 2 + 1.0), g2], [1.5, 1.3, 1.1], "orange", -1.0, bias=-0.3)
    glove(r, g2[0], g2[1], -0.9, k, near=False)
    # upright carapace: orange shell, teal belly plates
    cx, cy = T(0.0, hy - 5.0)
    r.ell(cx, cy, 6.4, 7.2, "orange", 0.0, ang=lean)
    for i in range(4): r.line(*T(-0.5, hy - 1.5 - i * 2.0), *T(2.5, hy - 1.8 - i * 2.0), "teal", 0.05, tone=2 + (i % 2))
    r.ell(*T(-1.5, hy - 8.5), 2.0, 1.4, "orange", 0.04, bias=0.3)
    # stalked eyes
    for ex in (0.5, 2.5):
        a = T(ex, hy - 10.5); b = T(ex + 0.5, hy - 13.5)
        r.line(*a, *b, "orange", 0.3, tone=3)
        eye(r, b[0], b[1] - 0.5, 0.4, big=False)
    if hurt: r.dot(*T(3.0, hy - 14.0), "orange", 4, 0.5)
    # near arm and glove
    sh = T(2.5, hy - 7.0)
    r.tube([sh, ((sh[0] + g1[0]) / 2, (sh[1] + g1[1]) / 2 + 1.2), g1], [1.6, 1.4, 1.2], "orange", 2.0)
    glove(r, g1[0], g1[1], 2.1, k + 1)
    if puffs:
        for (x, kk) in puffs: dust(r, x, 0, kk, 0.6)
    if smear:
        for (a, b, m, t) in smear: r.line(*a, *b, m, 3.5, tone=t)
    if extra: extra(r)
    return r.resolve()


def boxer_corpse(stage):
    r = Rig()
    crab_legs(r, 0.0, -2.0, 5.0, 3, 0.25, "orange", -0.5, -1.5, step=0.0, reach=3.0, lift=0.0, knee=1.5)
    r.ell(0.0, -3.0, 6.0, 3.2, "orange", 0.0, bias=-0.1)
    for i in range(3): r.line(-3 + i * 2, -1.5, -2 + i * 2, -4.5, "teal", 0.05, tone=2)
    glove(r, 8.0, -2.5, 0.5, 2, size=2.2)
    glove(r, -8.0, -2.0, -0.5, 3, size=2.0, near=False)
    if stage == 0: dust(r, 0, 0, 1)
    return r.resolve()


def boxer_sheet(out):
    B = boxer
    bounce = [0.0, -1.0, -1.5, -1.0]
    idle = [B(bob=bounce[i], k=i, g1=(8.5, -14.0 + bounce[i]), g2=(3.5, -13.0 + bounce[i]),
              puffs=[(-3, 1), (3, 1)] if i == 0 else None) for i in range(4)]
    run = [B(bob=[0, -1.5, -2.0, 0, -1.5, -2.0][i], lean=8, k=i, feet=((-3.0 + 2 * math.sin(i), -max(0, math.sin(i)) * 1.5), (3.0 - 2 * math.sin(i), -max(0, -math.sin(i)) * 1.5)),
              g1=(7.0, -13.0), g2=(4.0, -12.0)) for i in range(6)]
    # Jab (7): the one-two: near glove out (2: hit at (13, -12)), back (3), far glove out (4: hit at (12, -11)), back (5-6)
    jab = [B(lean=-4, g1=(4.5, -14.0), g2=(2.0, -13.0)), B(lean=-6, g1=(3.5, -14.5), g2=(2.0, -13.0), crouch=0.5),
           B(lean=8, g1=(13.0, -12.0), g2=(2.0, -12.5), smear=[((6, -12), (10, -12), "pink", 2)]),
           B(lean=4, g1=(6.0, -13.0), g2=(3.0, -12.5)),
           B(lean=10, g1=(5.0, -13.0), g2=(12.0, -11.0), smear=[((5, -11), (9, -11), "pink", 1)]),
           B(lean=4, g1=(6.0, -13.5), g2=(4.0, -12.5)), B(g1=(6.5, -14.0), g2=(3.0, -13.0))]
    # HopIn (8): crouch (0), hop in (1, airborne), land (2), three stinging jabs (3, 5, 7)
    hop = [B(crouch=1.5, lean=-4), B(bob=-4.0, lean=10, feet=((-3.0, -3.0), (3.0, -3.0)), puffs=[(-2, 0)]),
           B(crouch=1.0, lean=6, puffs=[(0, 0)]),
           B(lean=10, g1=(13.0, -12.0), g2=(3.0, -12.5), smear=[((6, -12), (10, -12), "pink", 2)]),
           B(lean=6, g1=(7.0, -13.0), g2=(5.0, -12.5)),
           B(lean=12, g1=(5.0, -13.0), g2=(12.5, -11.0), smear=[((5, -11), (9, -11), "pink", 1)]),
           B(lean=6, g1=(7.0, -13.0), g2=(5.0, -12.5)),
           B(lean=12, g1=(13.5, -10.0), g2=(4.0, -12.0), smear=[((6, -10), (11, -10), "pink", 2)])]
    # HopBack (4): bounce back out of reach: crouch, airborne leaning back, land with two puffs, bounce
    hopb = [B(crouch=1.2, lean=4), B(bob=-3.5, lean=-12, feet=((-3.0, -3.0), (3.0, -3.0))),
            B(crouch=1.0, lean=-4, puffs=[(-3, 0), (3, 0)]), B(bob=-1.0, puffs=[(-3, 1), (3, 1)])]
    d0 = B(hurt=True, lean=-14, g1=(5.0, -16.0), g2=(1.0, -16.0))
    d1 = B(hurt=True, lean=-40, crouch=3.0, g1=(3.0, -10.0), g2=(-2.0, -12.0))
    anims = [("Idle", idle, [0.12] * 4), ("Run", run, [0.08] * 6),
             ("Jab", jab, [0.1, 0.1, 0.06, 0.1, 0.06, 0.1, 0.12]),
             ("HopIn", hop, [0.1, 0.1, 0.08, 0.06, 0.1, 0.06, 0.1, 0.06]), ("HopBack", hopb, [0.06, 0.1, 0.08, 0.08])]
    anims += tail_anims(idle[0], [d0, d1, boxer_corpse(0), boxer_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        B(hurt=True, lean=-16, g1=(5.0, -15.0), g2=(1.0, -15.0)))
    return sheet("BelBoxer", anims, out)


JOBS = [("BelDiver", diver_sheet), ("BelSpinewalker", spine_sheet), ("BelSiren", siren_sheet), ("BelLamprey", lamprey_sheet),
        ("BelHermit", hermit_sheet), ("BelBoxer", boxer_sheet)]
SYNC = {
    "BelDiver": {"Anchor": [("SLAM: the anchor crown lands at (11, -7) -> box at (11, -5)", 3), ("quake ring at (13, 0)", 4)],
                 "Hook": [("THROW: the hook leaves the hand at (12, -16)", 2)]},
    "BelSpinewalker": {"Stab": [("SPEAR: the stilt tip hits the floor at (13, 0); box at (12, -3)", 2)],
                       "Sow": [("the eggs drop: lay them at (-4, 0), (0, 0), (4, 0)", 4)]},
    "BelSiren": {"Bolt": [("THROW: the bolt leaves the hand at (11, -15)", 3)], "Song": [("the song: notes from the throat (1, -19)", 2)]},
    "BelLamprey": {"Rasp": [("BITE: the sucker at (13, -7); box at (12, -7)", 3)],
                   "Lunge": [("LAUNCH: slide 70 px; the sucker leads at (14, -6)", 2), ("lands", 5)]},
    "BelHermit": {"Crush": [("CRUSH: claw tip at (19, -4); box at (15, -4)", 3)],
                  "Shell": [("the bell is down: a third of the damage from here", 2), ("comes out", 7)]},
    "BelBoxer": {"Jab": [("JAB 1: near glove at (13, -12)", 2), ("JAB 2: far glove at (12, -11)", 4)],
                 "HopIn": [("hop in (30 px)", 1), ("STING 1 at (13, -12)", 3), ("STING 2 at (12, -11)", 5), ("STING 3 at (13, -10)", 7)]},
}
NOTES = {
    "BelDiver": "Haul (4, loop): shoulder first along the taut chain (Dropped Anchor). The chain from the hand runs off to the right.",
    "BelLamprey": "Latched (4, loop): the lamprey hanging off the hero's side (mouth at (6, -9)): the body is moved with the hero.",
    "BelHermit": "IdleFull / RunFull: the bell carries a load of brine (water at its lip, dripping): Bellful of Brine.",
    "BelBoxer": "HopBack (4): the Footwork hop back out of reach after each punch.",
}
