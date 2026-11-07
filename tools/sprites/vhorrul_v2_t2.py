"""Vhorrul tier 2: Waxen Knight, Chandler, Wickworm, Tallow Sow, Moth Matron, Candelabra. Built through
vhorrul_v2_rigs.py. T2 idle limit 28 x 26. The biped helper here is shared by the tier 3 humanoids."""
import math
from vhorrul_v2_rigs import (Rig, Xf, chain, ik, lerp, flame, candle, smoke_curl, drip, floor_pool, ember_dots, glow_ring,
                             sheet, tail_anims, line_px, scaled)
from vhorrul_v2_t1 import bez, dust, _ash_cloud


# ================================================================== shared: a posed biped
def biped(r, hip=(0.0, -9.0), feet=((-2.0, 0.0), (2.0, 0.0)), lean=0.0, sh=7.0, hands=((5.0, -11.0), (-3.0, -10.0)),
          leg=(4.6, 4.6), arm=(3.6, 3.4), legm="iron", armm="iron", torso=None, tw=3.0, hipw=1.6, legr=(1.2, 1.0),
          armr=(1.0, 0.8), z=0.0, far_arm=True, knee=-1):
    """Legs (far, near), arms (near hands[0], far hands[1]) by IK from a hip point; the torso is the caller's.
    Returns (shoulder_near, shoulder_far, neck)."""
    hx, hy = hip
    nx, ny = hx + lean * sh * 0.12, hy - sh
    shn, shf = (nx + 0.6, ny + 0.8), (nx - 1.4, ny + 0.4)
    for k, (fx, fy) in enumerate(feet):
        near = k == 1
        hp = (hx + (0.7 if near else -0.7), hy)
        kx, ky = ik(hp[0], hp[1], fx, fy - 1.0, leg[0], leg[1], bend=-knee)
        zz = z + (0.6 if near else -1.0)
        r.tube([hp, (kx, ky), (fx, fy - 1.0)], [legr[0], legr[1], legr[1]], legm, zz, bias=0.0 if near else -0.3)
    for k, (tx, ty) in enumerate(hands):
        near = k == 0
        if not near and not far_arm: continue
        s = shn if near else shf
        ex, ey = ik(s[0], s[1], tx, ty, arm[0], arm[1], bend=1)
        zz = z + (2.0 if near else -0.8)
        r.tube([s, (ex, ey), (tx, ty)], [armr[0], armr[1], armr[1]], armm, zz, bias=0.0 if near else -0.3)
    return shn, shf, (nx, ny)


def boots(r, feet, mat="iron", z=0.0, w=2.2):
    for k, (fx, fy) in enumerate(feet):
        near = k == 1
        r.poly([(fx - 1.2, fy - 1.6), (fx + w, fy - 1.0), (fx + w, fy), (fx - 1.2, fy)], mat, z + (0.65 if near else -0.95),
               bias=0.1 if near else -0.3)


def walk_feet(i, n=6, stride=3.0, lift=1.4, base=2.0):
    a = i / float(n) * math.tau
    return ((-base * 0.5 + stride * math.cos(a), -max(0.0, lift * math.sin(a))),
            (base * 0.5 - stride * math.cos(a), -max(0.0, -lift * math.sin(a))))


def swipe_arc(r, cx, cy, R, a0, a1, mat="tallow", z=4.8, width=2, tone=4):
    """A slash smear: an arc of light from angle a0 to a1 (degrees, y down)."""
    p = r.part(True, z)
    cx, cy, R = cx * r.k, cy * r.k, R * r.k
    n = int(abs(a1 - a0) / 6) + 2
    for i in range(n):
        a = math.radians(lerp(a0, a1, i / float(n - 1)))
        for w in range(width):
            rr = R - w
            r.put(cx + rr * math.cos(a), cy + rr * math.sin(a), z, mat, 0.5, p, tone if w == 0 else max(1, tone - 1 - (i < n // 3)))


# ================================================================== WAXEN KNIGHT
def knight(hip=(0.0, -8.5), feet=((-2.5, 0.0), (2.5, 0.0)), lean=0.0, hand=(6.0, -12.0), hand2=(-3.0, -11.0),
           sword=-30.0, ph=0, smear=None, seal=0.0, crack=0, extra=None, slump=0.0, dead=False):
    """A rusted knight sealed in poured wax: square and heavy, three candles on the helm, wax hanging in sheets off
    the arms. sword: blade angle (deg, 0 = ahead, -90 = up); seal: 0..1 wax poured over it; crack: 1-2 the shell
    bursting off."""
    r = Rig()
    hx, hy = hip[0], hip[1] + slump
    shn, shf, (nx, ny) = biped(r, (hx, hy), feet, lean, 6.8, (hand, hand2), (4.4, 4.4), (3.6, 3.4), "iron", "rust",
                               legr=(1.5, 1.2), armr=(1.4, 1.1))
    boots(r, feet, "iron", w=2.6)
    # cuirass: a square iron box under sheets of wax
    T = Xf(lean * 6.0, (hx, hy))
    body = [T(hx - 3.6, hy + 0.8), T(hx + 3.4, hy + 0.8), T(hx + 3.8, hy - 6.8), T(hx - 3.8, hy - 7.0)]
    r.poly(body, "iron", 0.0, curve=0.6)
    r.poly([T(hx - 3.7, hy - 7.6), T(hx + 3.7, hy - 7.4), T(hx + 3.0, hy - 4.2), T(hx - 0.5, hy - 2.8), T(hx - 3.6, hy - 4.6)],
           "tallow", 0.2, curve=0.5)
    for dx, ln in ((-2.6, 3.5), (-0.6, 1.8), (1.6, 2.6)):
        drip(r, T(hx + dx, hy - 4)[0], T(hx + dx, hy - 4)[1], ln, "tallow", 0.25)
    r.line(*T(hx - 3.4, hy - 1.0), *T(hx + 3.2, hy - 1.0), "rust", 0.3, tone=2)   # belt
    # pauldrons: wax-caked lumps
    r.ell(shf[0], shf[1] - 0.4, 2.2, 1.8, "tallow", -0.5, bias=-0.2)
    r.ell(shn[0] + 0.6, shn[1] - 0.6, 2.6, 2.0, "tallow", 2.5)
    drip(r, shn[0] + 1.4, shn[1] + 1.0, 2.4, "tallow", 2.55)
    # helm: a bucket helm with a visor slit and three candles on its crown
    gx, gy = nx + 0.4, ny - 0.2
    r.poly([(gx - 2.6, gy), (gx + 2.8, gy), (gx + 3.0, gy - 4.6), (gx - 2.8, gy - 4.8)], "iron", 1.0, curve=0.7)
    r.line(gx - 0.6, gy - 2.2, gx + 2.6, gy - 2.2, "soot", 1.02, tone=0)
    r.dot(gx + 1.6, gy - 2.2, "ember", 3, 1.03)
    r.poly([(gx - 2.8, gy - 4.8), (gx + 3.0, gy - 4.6), (gx + 2.4, gy - 3.4), (gx - 2.6, gy - 3.6)], "tallow", 1.05)
    for k, dx in enumerate((-1.8, 0.4, 2.4)):
        candle(r, gx + dx, gy - 4.6, [1.4, 2.4, 1.8][k], 1.6, z=1.1 + 0.01 * k, ph=ph + k, flh=2.0, drip=0)
    # the sword in the near hand: a rusted blade with a wax-sealed guard
    a = math.radians(sword)
    tip = (hand[0] + 11.0 * math.cos(a), hand[1] + 11.0 * math.sin(a))
    pom = (hand[0] - 2.0 * math.cos(a), hand[1] - 2.0 * math.sin(a))
    r.line(*pom, *hand, "lthr", 2.9, tone=2)
    gxx, gyy = math.sin(a) * 2.0, -math.cos(a) * 2.0
    r.line(hand[0] - gxx, hand[1] - gyy, hand[0] + gxx, hand[1] + gyy, "tallow", 2.95, tone=3)
    r.tube([(hand[0] + math.cos(a), hand[1] + math.sin(a)), tip], [0.9, 0.5], "iron", 3.0, bias=0.2)
    r.dot(*hand, "rust", 2, 3.05)
    if seal > 0.0:
        # poured wax: a lump that swallows the knight from the helm down
        top = lerp(gy - 3.0, gy - 8.0, min(1.0, seal))
        r.ell(hx, lerp(hy, hy - 5.0, seal), 5.4 + seal, 7.5 * seal + 2.0, "tallow", 4.0,
              clip=lambda x, y: y >= top - 1)
        for k in range(3): drip(r, hx - 4 + 3 * k, hy + 1.0, 1.0, "tallow", 4.1)
        if crack:
            for (x0, y0, x1, y1) in ((hx - 1, top + 2, hx + 1, hy - 4), (hx + 2, hy - 7, hx + 4, hy - 2), (hx - 3, hy - 6, hx - 1, hy)):
                r.line(x0, y0, x1, y1, "ember" if crack == 2 else "soot", 4.2, tone=3 if crack == 2 else 1)
    if smear:
        for args in smear: swipe_arc(r, *args)
    if extra: extra(r)
    return r.resolve()


def _wax_shards(r, k):
    p = r.part(True, 5.0)
    for i in range(10):
        a = i * 0.63
        d = 6 + k * 4
        r.put(math.cos(a) * d, -10 + math.sin(a) * d * 0.7, 5.0, "tallow", 0.5, p, 4 if (i + k) % 2 else 3)


def knight_sheet(outdir):
    K = knight
    idle = [K(hip=(0, -8.0 + [0, 0.3, 0.5, 0.3][i]), hand=(6.0, -11.5 + [0, 0.3, 0.5, 0.3][i]), ph=i) for i in range(4)]
    run = []
    for i in range(6):
        f = walk_feet(i, 6, 3.0, 1.6, 4.0)
        b = abs(math.sin(i / 6.0 * math.tau)) * 0.8
        run.append(K(hip=(0.5, -8.0 - b), feet=f, lean=0.6, hand=(6.5, -11.0 - b), hand2=(-3.5 + f[0][0] * 0.5, -10.5 - b),
                     sword=-25.0, ph=i))
    # Combo1: a rising cut. Combo2: a level backhand. Combo3: the overhead that spills wax (hit on f3)
    c1 = [K(hand=(3.0, -10.0), sword=40.0, lean=-0.4, ph=0), K(hand=(1.5, -9.0), sword=70.0, lean=-0.8, hip=(-0.5, -7.7), ph=1),
          K(hand=(7.5, -14.0), sword=-55.0, lean=0.8, feet=((-2.5, 0), (4.0, 0)), ph=2, smear=[(4.0, -10.0, 13.0, 60, -60)]),
          K(hand=(6.5, -16.0), sword=-80.0, lean=0.6, feet=((-2.5, 0), (4.0, 0)), ph=3),
          K(hand=(6.0, -13.0), sword=-50.0, lean=0.3, ph=4), K(hand=(6.0, -12.0), sword=-30.0, ph=5)]
    c2 = [K(hand=(4.0, -14.0), sword=-120.0, lean=-0.3, ph=0), K(hand=(2.0, -14.5), sword=-160.0, lean=-0.6, ph=1),
          K(hand=(8.0, -12.0), sword=10.0, lean=0.9, feet=((-2.0, 0), (4.5, 0)), ph=2, smear=[(3.0, -12.0, 13.0, -110, 20)]),
          K(hand=(6.0, -11.0), sword=40.0, lean=0.7, feet=((-2.0, 0), (4.5, 0)), ph=3),
          K(hand=(5.0, -11.5), sword=0.0, lean=0.3, ph=4), K(ph=5)]
    c3 = [K(hand=(3.0, -17.0), sword=-110.0, lean=-0.5, ph=0), K(hand=(1.0, -19.0), sword=-150.0, lean=-1.0, hip=(-0.5, -8.5), ph=1),
          K(hand=(0.0, -19.5), sword=-175.0, lean=-1.2, hip=(-0.8, -8.7), ph=2),
          K(hand=(8.0, -8.0), sword=30.0, lean=1.4, hip=(1.0, -7.2), feet=((-2.0, 0), (5.0, 0)), ph=3,
            smear=[(2.0, -12.0, 14.0, -120, 40)]),
          K(hand=(8.0, -6.0), sword=50.0, lean=1.4, hip=(1.0, -6.8), feet=((-2.0, 0), (5.0, 0)), ph=4,
            extra=lambda r: floor_pool(r, 16.0, -0.8, 4.0, 1.0, "tallow", -1.0)),
          K(hand=(7.0, -9.0), sword=10.0, lean=0.8, ph=5), K(ph=0)]
    seal = [K(hand=(2.0, -21.0), hand2=(-1.0, -21.0), sword=-100.0, ph=0),
            K(hand=(2.0, -21.0), hand2=(-1.0, -21.0), sword=-100.0, seal=0.4, ph=1),
            K(hand=(2.0, -19.0), hand2=(-1.0, -19.0), sword=-100.0, seal=0.8, ph=2),
            K(hand=(2.0, -18.0), hand2=(-1.0, -18.0), sword=-100.0, seal=1.0, crack=1, ph=3),
            K(hand=(8.0, -15.0), hand2=(-6.0, -15.0), sword=-40.0, ph=4, extra=lambda r: _wax_shards(r, 0)),
            K(hand=(7.0, -13.0), hand2=(-4.0, -12.0), sword=-35.0, ph=5, extra=lambda r: _wax_shards(r, 1)),
            K(ph=0)]
    knock = K(hip=(-1.0, -7.8), lean=-1.2, hand=(4.0, -9.0), hand2=(-5.0, -13.0), sword=20.0, ph=2)
    d0 = K(hip=(-1.0, -7.8), lean=-1.0, hand=(3.0, -8.0), hand2=(-5.0, -14.0), sword=60.0, ph=1)
    d1 = K(hip=(-1.0, -6.0), feet=((-3.0, 0), (1.0, 0)), lean=0.8, hand=(6.0, -2.0), hand2=(-4.0, -3.0), sword=10.0, ph=3)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("Combo1", c1, [0.08, 0.07, 0.05, 0.08, 0.08, 0.1]), ("Combo2", c2, [0.06, 0.06, 0.05, 0.08, 0.08, 0.1]),
             ("Combo3", c3, [0.1, 0.1, 0.06, 0.05, 0.1, 0.1, 0.1]),
             ("Seal", seal, [0.1, 0.1, 0.1, 0.25, 0.08, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, knight_corpse(0), knight_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("WaxenKnight", anims, outdir, scale=6)


def knight_corpse(stage):
    r = Rig()
    r.poly([(-8, -1), (5, -1), (6, -5), (-7, -5)], "iron", 0.0, curve=0.5)
    r.poly([(-8, -4), (6, -4), (5, -6), (-7, -6.5)], "tallow", 0.2)
    r.poly([(6, -1), (10.5, -1), (11, -5.5), (6.5, -5.5)], "iron", 0.5, curve=0.6)
    r.line(7, -3.4, 10, -3.4, "soot", 0.6, tone=0)
    r.tube([(-9, -1.4), (-13, -1.0)], [1.2, 1.0], "rust", -0.2)
    r.line(-4, -7, 8, -9, "iron", 1.0, tone=3)
    for k, x in enumerate((7.0, 9.0)):
        candle(r, x + 4, -5.0, 1.6, 1.4, z=0.7, out=True, ph=k)
    floor_pool(r, 0.0, -0.4, 11.0, 1.2, "tallow", -1.0, tone=2 if stage else 3)
    return r.resolve()


# ================================================================== CHANDLER
def chandler(hip=(0.0, -9.0), feet=((-2.0, 0.0), (2.2, 0.0)), lean=0.6, hand=(5.0, -12.0), hand2=(-2.5, -11.0),
             taper=55.0, ph=0, pot_tilt=0.0, pour=0, glob=None, extra=None, hunch=1.0):
    """A stooped candle-maker in a waxed leather apron, a dipping pot on one hip, leaning on a long lit taper.
    taper: the taper's angle from the near hand (deg; 90 = straight down). pot_tilt tips the pot (pouring)."""
    r = Rig()
    hx, hy = hip
    shn, shf, (nx, ny) = biped(r, hip, feet, lean + hunch, 6.4, (hand, hand2), (4.4, 4.4), (3.6, 3.4), "lthr", "flesh",
                               legr=(1.0, 0.8), armr=(0.9, 0.7))
    boots(r, feet, "lthr")
    T = Xf(10.0 * (lean + hunch) * 0.6, (hx, hy))
    r.poly([T(hx - 2.6, hy + 0.6), T(hx + 2.6, hy + 0.6), T(hx + 2.8, hy - 6.4), T(hx - 2.2, hy - 6.8)], "soot", 0.0, curve=0.6)
    # the waxed apron down the front, glossy with drips
    r.poly([T(hx - 0.4, hy - 5.8), T(hx + 3.0, hy - 5.6), T(hx + 3.6, hy + 1.6), T(hx - 0.2, hy + 2.0)], "lthr", 0.4, curve=0.4)
    for dy in (-3.0, 0.0):
        r.dot(*T(hx + 2.4, hy + dy), "tallow", 3, 0.45)
    # head: a bald, sallow, wax-spattered head jutting forward on the stoop, a smoking wick of hair
    gx, gy = nx + 1.6, ny + 0.6
    r.ell(gx, gy - 1.8, 2.0, 2.2, "flesh", 1.2)
    r.dot(gx + 1.2, gy - 2.0, "ember", 3, 1.3)
    r.dot(gx + 2.0, gy - 1.2, "flesh", 2, 1.25)
    r.line(gx - 1.0, gy - 0.4, gx + 1.4, gy - 0.2, "flesh", 1.26, tone=1)
    r.dot(gx - 0.8, gy - 3.6, "tallow", 4, 1.3)
    # the dipping pot on the far hip
    px_, py_ = hx - 3.6, hy - 1.2
    TP = Xf(pot_tilt, (px_, py_))
    r.poly([TP(px_ - 2.4, py_ - 2.4), TP(px_ + 2.4, py_ - 2.4), TP(px_ + 2.0, py_ + 1.8), TP(px_ - 2.0, py_ + 1.8)], "iron", -1.2, curve=0.7)
    r.line(*TP(px_ - 2.4, py_ - 2.4), *TP(px_ + 2.4, py_ - 2.4), "tallow", -1.1, tone=4)
    if pour:
        lip = TP(px_ + 2.4, py_ - 2.4)
        for i in range(int(lip[1] < 0) * (4 + pour)):
            r.dot(lip[0] + 0.6 + i * 0.3, lip[1] + i, "tallow", 3 if i % 2 else 4, 3.5)
    # the long taper: a thin wax stick, lit at the far end
    a = math.radians(taper)
    end = (hand[0] + 13.0 * math.cos(a), hand[1] + 13.0 * math.sin(a))
    r.line(*hand, *end, "tallow", 2.8, tone=3)
    r.line(hand[0], hand[1] + 1, end[0], end[1] + 1, "tallow", 2.79, tone=1)
    if end[1] < -1.0:
        flame(r, end[0], end[1] - 0.5, 3.0, ph, "fire", 3.0)
    else:
        flame(r, hand[0] - 13.0 * math.cos(a) * 0.15, hand[1] - 1, 2.0, ph, "fire", 3.0)
    if glob:
        r.ell(glob[0], glob[1], 1.6, 1.4, "bees", 3.2)
        flame(r, glob[0], glob[1] - 1.0, 2.6, ph, "fire", 3.3)
    if extra: extra(r)
    return r.resolve()


@scaled(1.12)
def chandler_sheet(outdir):
    C = chandler
    idle = [C(hip=(0, -9.0 + [0, 0.2, 0.4, 0.2][i]), hand=(5.0, -12.0 + [0, 0.2, 0.4, 0.2][i]), ph=i) for i in range(4)]
    run = []
    for i in range(6):
        f = walk_feet(i, 6, 2.6, 1.2, 4.0)
        run.append(C(feet=f, hand=(5.0 + f[1][0] * 0.4, -12.0), hand2=(-2.5 + f[0][0] * 0.5, -10.5), taper=60.0 + f[1][0] * 4, ph=i,
                     lean=0.9))
    # Toss: the taper dips the glob from the pot and flicks it along the floor (release f3)
    toss = [C(hand=(-1.0, -10.0), hand2=(-4.0, -9.5), taper=150.0, lean=0.2, ph=0),
            C(hand=(-2.0, -12.0), hand2=(-4.0, -9.5), taper=200.0, lean=-0.2, ph=1, glob=(-7.0, -14.5)),
            C(hand=(2.0, -15.0), hand2=(-3.0, -10.0), taper=-60.0, lean=0.1, ph=2, glob=(5.0, -22.0)),
            C(hand=(7.0, -11.0), hand2=(-2.0, -10.0), taper=10.0, lean=1.3, ph=3, feet=((-2.0, 0), (4.0, 0)),
              extra=lambda r: _glob_trail(r)),
            C(hand=(6.5, -10.0), taper=30.0, lean=1.1, ph=4, feet=((-2.0, 0), (4.0, 0))), C(ph=5)]
    # Pour: the pot comes off the hip and pours a line of wax ahead
    pour = [C(hand=(3.0, -12.0), hand2=(-1.0, -12.0), ph=0, pot_tilt=10.0),
            C(hand=(4.0, -12.0), hand2=(1.0, -13.0), ph=1, pot_tilt=50.0),
            C(hand=(5.0, -11.0), hand2=(2.0, -12.0), ph=2, pot_tilt=95.0, pour=1, lean=1.0),
            C(hand=(5.0, -10.0), hand2=(2.0, -11.0), ph=3, pot_tilt=110.0, pour=2, lean=1.2,
              extra=lambda r: floor_pool(r, 10.0, -0.7, 5.0, 0.9, "tallow", -1.0, tone=3)),
            C(hand=(5.0, -10.0), hand2=(2.0, -11.0), ph=4, pot_tilt=110.0, pour=2, lean=1.2,
              extra=lambda r: floor_pool(r, 13.0, -0.7, 8.0, 0.9, "tallow", -1.0, tone=3)),
            C(hand=(4.0, -12.0), hand2=(0.0, -12.0), ph=5, pot_tilt=40.0), C(ph=0)]
    knock = C(hip=(-1.0, -9.0), lean=-0.6, hand=(3.0, -13.0), hand2=(-5.0, -12.0), taper=30.0, ph=2)
    d0 = C(hip=(-1.0, -8.5), lean=-0.8, hand=(4.0, -14.0), hand2=(-5.0, -13.0), taper=-20.0, ph=1)
    d1 = C(hip=(0.0, -5.5), feet=((-2.5, 0), (1.5, 0)), lean=2.0, hand=(7.0, -2.0), hand2=(-2.0, -2.0), taper=0.0, ph=3, pot_tilt=80.0)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.1] * 6),
             ("Toss", toss, [0.1, 0.1, 0.08, 0.06, 0.1, 0.12]),
             ("Pour", pour, [0.1, 0.1, 0.1, 0.1, 0.12, 0.1, 0.1])]
    anims += tail_anims(idle[0], [d0, d1, chandler_corpse(0), chandler_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("Chandler", anims, outdir, scale=6)


def _glob_trail(r):
    r.ell(13.0, -3.0, 1.6, 1.3, "bees", 3.2)
    flame(r, 13.0, -4.0, 2.6, 1, "fire", 3.3)
    for i in range(3): r.dot(10.5 - i * 1.4, -2.0 + i * 0.3, "fire", 2, 3.1)


def chandler_corpse(stage):
    r = Rig()
    r.ell(0.0, -2.0, 6.0, 2.0, "soot", 0.0)
    r.poly([(-2, -3.5), (5, -3.6), (5.5, -0.8), (-2, -0.6)], "lthr", 0.3)
    r.ell(7.6, -2.4, 2.0, 1.8, "flesh", 0.5)
    r.line(-10, -1, 4, -1, "tallow", 0.6, tone=3)
    r.poly([(-12, -3), (-8, -3), (-8.5, 0), (-11.5, 0)], "iron", -0.5)
    floor_pool(r, -6.0, -0.4, 6.0, 1.0, "tallow", -1.0, tone=2 if stage else 3)
    if stage == 0: smoke_curl(r, -10, -2, 2, 2.0)
    return r.resolve()


JOBS = [("WaxenKnight", knight_sheet), ("Chandler", chandler_sheet)]
SYNC = {
    "WaxenKnight": {"Combo1": [("cut 1: swipe at the chest (0, -10)", 2)], "Combo2": [("cut 2", 2)],
                    "Combo3": [("OVERHEAD: cleave box + the wax spill at (18, 0)", 3)],
                    "Seal": [("poured: can't be hit", 1), ("the shell cracks off: the ring on the feet", 4)]},
    "Chandler": {"Toss": [("glob leaves the taper at (13, -3); launch along the floor at (14, -1)", 3)],
                 "Pour": [("the pour starts: the line's first puddle at (14, 0)", 2), ("the line is down (50 px ahead)", 4)]},
}
NOTES = {}


# ================================================================== WICKWORM
def worm_path(n, x0, x1, amp, ph, rear=0.0, rear_n=3, coil=0.0):
    """Points of a body lying along the floor from x0 (tail) to x1 (head), waving amp px; the front rear_n points
    lift `rear` px (rearing)."""
    pts = []
    for i in range(n):
        t = i / float(n - 1)
        x = lerp(x0, x1, t)
        y = -2.4 - amp * math.sin(t * math.tau * 1.2 + ph)
        k = max(0.0, (i - (n - 1 - rear_n)) / float(rear_n))
        y -= rear * k * k
        x -= rear * 0.35 * k * k
        pts.append((x, y))
    return pts


def wickworm(amp=0.6, ph=0.0, rear=0.0, jaw=0.0, fph=0, x0=-10.0, x1=7.5, swim=False, extra=None, flames=True, dead=False, ring=0):
    """A long segmented grub with five candle stubs down its back. swim=True: under the wax, only the five flames show
    (cutting through the wax like fins) over a ripple."""
    r = Rig()
    n = 9
    pts = worm_path(n, x0, x1, amp, ph, rear)
    if swim:
        for k, i in enumerate((1, 2, 4, 5, 7)):
            x, y = pts[i]
            r.dot(x - 1, -1.0, "tallow", 3, -1.0); r.dot(x + 1, -1.0, "tallow", 2, -1.0)
            r.dot(x - 2, -0.6, "tallow", 2, -1.0)
            flame(r, x, -1.4, 3.0 - 0.3 * (k % 2), fph + k, "fire", 2.0)
        for i in range(3):
            r.dot(x0 - 2 - i * 2, -0.8, "tallow", 2, -1.0)
        return r.resolve(floor=False)
    for i, (x, y) in enumerate(pts):
        t = i / float(n - 1)
        rad = 3.0 + 1.9 * math.sin(math.pi * min(1.0, 0.15 + t * 0.95))
        r.ell(x, y - rad * 0.25, rad * 1.15, rad, "bees" if i % 2 else "tallow", 0.1 * i)
        r.dot(x - rad * 0.4, y - rad * 0.9, "tallow", 4, 0.1 * i + 0.02)
    hx, hy = pts[-1]
    # the head: a blunt amber grub head with two hooked mandibles
    r.ell(hx + 1.6, hy - 0.6, 2.6, 2.3, "bees", 1.2)
    r.dot(hx + 2.4, hy - 1.6, "ember", 3, 1.3)
    for s in (-1, 1):
        r.tube([(hx + 3.4, hy + 0.2 + s * 0.4), (hx + 5.0 + jaw, hy + 0.2 + s * (0.6 + jaw * 1.6)), (hx + 5.6 + jaw * 0.6, hy - 0.2 + s * (0.2 + jaw))],
               [0.6, 0.5, 0.3], "chitin", 1.35 if s > 0 else 1.15)
    if flames:
        for k, i in enumerate((1, 2, 4, 5, 7)):
            x, y = pts[i]
            t = i / float(n - 1)
            rad = 2.6 + 1.8 * math.sin(math.pi * min(1.0, 0.15 + t * 0.95))
            candle(r, x, y - rad * 1.1, 2.0 + (k % 2) * 0.6, 1.6, z=1.0 + 0.1 * i, ph=fph + k, flh=2.4, drip=0, out=dead)
    if extra: extra(r)
    return r.resolve()


def worm_sheet(outdir):
    Wm = wickworm
    idle = [Wm(amp=0.5, ph=i * 0.4, fph=i) for i in range(4)]
    run = [Wm(amp=1.0, ph=i * math.tau / 6, fph=i, x0=-10.0 + 0.6 * math.sin(i), x1=7.5 + 0.6 * math.sin(i)) for i in range(6)]
    bite = [Wm(rear=2.0, ph=0.0, fph=0), Wm(rear=5.0, x1=7.0, jaw=0.6, fph=1), Wm(rear=7.0, x1=5.5, jaw=1.0, fph=2),
            Wm(rear=1.0, x1=11.0, jaw=0.2, fph=3, extra=lambda r: ember_dots(r, [(17, -3, 3), (18, -1, 2), (16, -5, 2)])),
            Wm(rear=0.5, x1=10.0, jaw=0.4, fph=4), Wm(fph=5)]
    road = [Wm(amp=1.4, ph=i * math.tau / 6, fph=i, x0=-11, x1=9.5,
               extra=(lambda k: lambda r: floor_pool(r, -14 - k, -0.6, 4.0, 0.8, "tallow", -2.0, tone=3))(i % 2)) for i in range(6)]
    swim = [Wm(swim=True, ph=i * 0.4, fph=i, amp=0.3) for i in range(4)]
    swimrun = [Wm(swim=True, ph=i * 1.0, fph=i, amp=0.6) for i in range(6)]
    knock = Wm(rear=3.0, x1=8.5, jaw=1.0, fph=2, amp=1.2)
    d0 = Wm(rear=6.0, x1=8.0, jaw=1.0, fph=1)
    d1 = Wm(rear=0.0, amp=1.8, fph=3, jaw=0.6, dead=True)
    d2 = Wm(amp=0.3, fph=4, dead=True, extra=lambda r: floor_pool(r, 0, -0.5, 12.0, 1.0, "tallow", -2.0))
    anims = [("Idle", idle, [0.16, 0.14, 0.16, 0.14]), ("Run", run, [0.08] * 6),
             ("Bite", bite, [0.1, 0.1, 0.08, 0.05, 0.1, 0.12]), ("Road", road, [0.07] * 6),
             ("Swim", swim, [0.12] * 4), ("SwimRun", swimrun, [0.07] * 6)]
    anims += tail_anims(idle[0], [d0, d1, d2, d2], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhWickworm", anims, outdir, scale=6)


# ================================================================== TALLOW SOW
def sow(bob=0.0, legs=None, head=(0.0, 0.0), snout=0.0, coat=False, ph=0, squat=0.0, eggs=3, extra=None, eye=True, roll=0.0):
    """A bloated sow of rendered fat: a heavy oval on short trotters dripping wax, a row of wax eggs like teats under
    her belly, small mean eyes. coat: greased (a pale shine over her hide)."""
    r = Rig()
    by = -6.4 + bob + squat
    mat = "grease" if coat else "pink"
    if legs is None:
        legs = ((-5.0, 0.0), (-3.6, 0.0), (4.0, 0.0), (5.4, 0.0))
    for k, (fx, fy) in enumerate(legs):
        near = k % 2 == 1
        hx_ = fx * 0.9
        r.tube([(hx_, by + 2.0), (fx, fy - 0.8)], [1.3, 1.0], "pink", 1.0 if near else -1.0, bias=0.0 if near else -0.3)
        r.dot(fx, fy - 0.3, "soot", 1, 1.01 if near else -0.99)
        drip(r, fx - 0.6, fy - 2.4, 1.0, "tallow", 1.02 if near else -0.98, bulb=False)
    r.ell(0.0, by, 8.0, 4.6, mat, 0.0, ang=roll)
    # rolls of fat and a wax drip line along the back
    r.line(-4.5, by - 1.0, -3.5, by + 2.5, mat, 0.05, tone=1)
    r.line(1.0, by - 2.5, 2.0, by + 2.0, mat, 0.05, tone=1)
    for dx in (-5.0, -1.5, 2.5):
        drip(r, dx, by - 3.6 + abs(dx) * 0.08, 1.6, "tallow", 0.1)
    # the egg-teats
    for k in range(eggs):
        ex = -3.5 + k * 3.2
        r.ell(ex, by + 4.2, 1.1, 1.3, "bees", 0.3)
        r.dot(ex - 0.4, by + 3.6, "bees", 4, 0.31)
    # head: a heavy jowled head, small mean eyes, a wet snout
    hx, hy = 7.4 + head[0], by - 1.0 + head[1]
    r.ell(hx, hy, 3.2, 3.0, mat, 1.0)
    r.ell(hx + 2.8 + snout, hy + 0.8, 1.6, 1.5, "pink", 1.1)
    r.dot(hx + 3.4 + snout, hy + 0.6, "soot", 0, 1.2); r.dot(hx + 3.4 + snout, hy + 1.4, "soot", 0, 1.2)
    if eye:
        r.dot(hx + 0.8, hy - 1.2, "eye", 3, 1.2)
    r.poly([(hx - 1.6, hy - 2.2), (hx - 0.4, hy - 4.6), (hx + 0.6, hy - 2.4)], "pink", 1.15)
    if coat:
        for (x, y) in ((-4, by - 3), (-1, by - 4), (3, by - 3.5), (hx - 0.5, hy - 2.4)):
            r.dot(x, y, "white", 3, 2.0)
    if extra: extra(r)
    return r.resolve()


def sow_sheet(outdir):
    S = sow
    sets = {}
    for coat in (False, True):
        idle = [S(bob=[0, 0.3, 0.5, 0.3][i], coat=coat, ph=i) for i in range(4)]
        run = []
        for i in range(6):
            a = i / 6.0 * math.tau
            lg = ((-5.0 + 1.4 * math.cos(a), -max(0, math.sin(a))), (-3.6 - 1.4 * math.cos(a), -max(0, -math.sin(a))),
                  (4.0 - 1.4 * math.cos(a), -max(0, -math.sin(a))), (5.4 + 1.4 * math.cos(a), -max(0, math.sin(a))))
            run.append(S(bob=-0.5 * abs(math.sin(a)), legs=lg, coat=coat, roll=2 * math.sin(a), ph=i))
        sets[coat] = (idle, run)
    idle, run = sets[False]
    spray = [S(head=(-0.6, 0.4), squat=0.6), S(head=(-1.2, 1.0), squat=1.0, snout=-0.4), S(head=(0.4, -1.2), snout=0.4),
             S(head=(1.4, -0.4), snout=1.0, extra=lambda r: _fat_fan(r)), S(head=(1.0, 0.0), snout=0.6), S()]
    lay = [S(squat=0.4), S(squat=1.0, head=(-0.4, 0.6)), S(squat=1.6, head=(-0.6, 1.0)), S(squat=2.0, head=(-0.6, 1.2)),
           S(squat=1.6, eggs=0, extra=lambda r: _eggs_down(r, 0)), S(squat=0.6, eggs=0, extra=lambda r: _eggs_down(r, 1)),
           S(eggs=1, extra=lambda r: _eggs_down(r, 1)), S(eggs=3)]
    knock = S(head=(-1.0, -1.2), roll=-8.0, snout=-0.4)
    d0 = S(head=(-0.6, -1.6), roll=-10.0)
    d1 = S(squat=2.6, roll=10.0, head=(0.0, 2.0), eye=False, legs=((-5, -2), (-3.6, -2.6), (4, -2), (5.4, -2.6)))
    corpse = sow_corpse()
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("IdleCoat", sets[True][0], [0.18, 0.15, 0.18, 0.15]), ("RunCoat", sets[True][1], [0.09] * 6),
             ("Spray", spray, [0.1, 0.1, 0.08, 0.06, 0.1, 0.12]),
             ("Lay", lay, [0.1, 0.1, 0.1, 0.12, 0.06, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, corpse, corpse], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("VhTallowSow", anims, outdir, scale=6)


def _fat_fan(r):
    for k, a in enumerate((-16.0, 0.0, 16.0)):
        x, y = 15.0 + 3 * math.cos(math.radians(a)), -6.0 + 3 * math.sin(math.radians(a)) * 2
        r.ell(x, y, 1.0, 0.9, "bees", 3.0)
        r.dot(x - 1.4, y, "tallow", 3, 2.9)


def _eggs_down(r, k):
    for i, (x, y) in enumerate(((-9.0, -1.4), (-7.0, -0.8), (-11.0, -1.0))):
        r.ell(x - k, y, 1.4, 1.6, "bees", 0.5 + 0.1 * i)
        r.dot(x - k - 0.5, y - 0.8, "bees", 4, 0.6 + 0.1 * i)


def sow_corpse():
    r = Rig()
    r.ell(0.0, -3.4, 9.0, 3.2, "pink", 0.0)
    for x in (-5.0, -3.0, 4.0, 6.0):
        r.tube([(x, -6.0), (x + 0.6, -8.2)], [1.0, 0.8], "pink", 0.5)
    r.ell(9.0, -3.0, 2.8, 2.4, "pink", 0.6)
    r.dot(9.6, -3.6, "soot", 1, 0.7)
    floor_pool(r, 0.0, -0.5, 12.0, 1.0, "tallow", -2.0)
    return r.resolve()


# ================================================================== MOTH MATRON
def matron(sway=0.0, lean=0.0, hand=(5.0, -10.0), hand2=(-4.0, -10.0), cloak=0.0, ph=0, glowc=False, extra=None,
           head=(0.0, 0.0), sink=0.0):
    """A tall moth-woman shaman: a bell of folded ash wings for a cloak, antennae like a feathered crown, a pale moth
    face, ember claws. cloak: 0 folded .. 1 spread open (the wings fan out behind her)."""
    r = Rig()
    by = -sink
    # the cloak: folded wings, a bell from shoulders to floor; spread, they open into two wings behind her
    top = (lean * 0.8, by - 15.0)
    cloak = max(cloak, 0.5)
    if cloak > 0.05:
        for s, z in ((-1, -2.0), (1, -1.8)):
            sp = cloak
            pts = [(top[0], top[1] + 1), (top[0] + s * (4 + 6 * sp), top[1] - 3 - 4 * sp), (top[0] + s * (6 + 7 * sp), top[1] + 3),
                   (top[0] + s * (5 + 5 * sp), top[1] + 9), (top[0] + s * 1.5, top[1] + 8)]
            r.poly(pts, "moth", z, bias=-0.1 if s > 0 else -0.35, normal=(-0.3, -0.3, 1.0))
            ex, ey = top[0] + s * (4 + 4 * sp), top[1] + 1
            r.dot(ex, ey, "soot", 0, z + 0.01); r.dot(ex, ey - 1, "ember", 3 if glowc else 1, z + 0.02)
    bell = [(top[0] - 2.4, top[1] + 1.0), (top[0] + 2.6, top[1] + 1.0), (5.0 + sway, by - 0.4), (2.0 + sway * 0.6, by),
            (-2.0 + sway * 0.6, by), (-5.4 + sway, by - 0.4)]
    r.poly(bell, "moth", 0.0, curve=0.8)
    for k, x in enumerate((-3.0, -0.6, 2.0)):   # the folds of the wing-cloak, eye-spots along the hem
        r.line(top[0] + x * 0.3, top[1] + 3, x + sway * 0.8, by - 1, "moth", 0.05, tone=1)
        r.dot(x + 1.0 + sway * 0.8, by - 3, "soot", 0, 0.06)
        r.dot(x + 1.0 + sway * 0.8, by - 4, "ember" if glowc else "ash", 2 if glowc else 3, 0.07)
    # arms out of the cloak, ember claws
    sh = (top[0] + 2.0, top[1] + 3.0)
    for k, (tx, ty) in enumerate((hand, hand2)):
        near = k == 0
        s = sh if near else (top[0] - 2.0, top[1] + 3.0)
        ex, ey = ik(s[0], s[1], tx, ty, 3.6, 3.4, bend=1)
        z = 2.0 if near else -0.5
        r.tube([s, (ex, ey), (tx, ty)], [0.9, 0.7, 0.6], "ash", z, bias=0.0 if near else -0.3)
        for d in (-1, 0, 1):
            r.dot(tx + 1.2, ty + d, "ember", 3 if near else 2, z + 0.01)
    # the pale moth face under a ruff of ash fur, feathered antennae
    hx, hy = top[0] + 0.8 + head[0], top[1] - 1.2 + head[1]
    r.ell(hx, hy + 1.6, 3.0, 1.4, "ash", 1.0)
    r.ell(hx + 0.4, hy - 0.6, 2.0, 2.2, "ashw", 1.2)
    r.dot(hx + 1.0, hy - 1.0, "soot", 0, 1.3); r.dot(hx - 0.6, hy - 1.0, "soot", 0, 1.3)
    r.dot(hx + 1.0, hy - 1.2, "ember", 3, 1.31)
    for s in (-1, 1):
        base = (hx + s * 1.0, hy - 2.4)
        pts = bez(base, (base[0] + s * 1.0, base[1] - 3), (base[0] + s * 3.0, base[1] - 4.5), (base[0] + s * 4.5, base[1] - 4.0), 6)
        r.polyline(pts, "ash", 1.25, tone=3)
        for (x, y) in pts[2::2]:
            r.dot(x, y + 1, "ash", 2, 1.24)
    if extra: extra(r)
    return r.resolve()


@scaled(1.08)
def matron_sheet(outdir):
    Mt = matron
    idle = [Mt(sway=[0, 0.4, 0.6, 0.4][i], hand=(4.5, -10.0 + [0, 0.3, 0.5, 0.3][i]), ph=i) for i in range(4)]
    run = [Mt(sway=-1.0 + 0.6 * math.sin(i), lean=0.8, hand=(5.0, -10.5 + math.sin(i)), hand2=(-4.5, -10.0 - math.sin(i)), ph=i)
           for i in range(6)]
    rake = [Mt(hand=(3.0, -16.0), lean=-0.6, sway=0.6), Mt(hand=(2.0, -18.0), lean=-1.0, sway=1.0, cloak=0.2),
            Mt(hand=(9.0, -7.0), lean=1.2, sway=-1.2, extra=lambda r: _claw_rake(r)),
            Mt(hand=(8.0, -5.0), lean=1.0, sway=-1.0, extra=lambda r: _ash_cloud(r, 12.0, -7.0, 2)),
            Mt(hand=(6.0, -8.0), lean=0.4), Mt()]
    lamp = [Mt(hand=(3.0, -12.0), hand2=(-2.0, -12.0), cloak=0.2), Mt(hand=(4.0, -15.0), hand2=(-4.0, -15.0), cloak=0.6, glowc=True),
            Mt(hand=(5.0, -18.0), hand2=(-5.0, -18.0), cloak=1.0, glowc=True),
            Mt(hand=(6.0, -19.0), hand2=(-6.0, -19.0), cloak=1.0, glowc=True, extra=lambda r: _little_moths(r, 0)),
            Mt(hand=(6.0, -18.0), hand2=(-6.0, -18.0), cloak=0.8, glowc=True, extra=lambda r: _little_moths(r, 1)),
            Mt(hand=(5.0, -13.0), hand2=(-4.0, -12.0), cloak=0.3), Mt()]
    knock = Mt(lean=-1.0, sway=1.5, hand=(3.0, -14.0), hand2=(-5.0, -13.0), head=(-0.6, 0.4))
    d0 = Mt(lean=-1.2, sway=2.0, hand=(3.0, -15.0), hand2=(-6.0, -14.0), cloak=0.4)
    d1 = Mt(sink=6.0, sway=1.0, hand=(5.0, -3.0), hand2=(-5.0, -3.0), cloak=0.8)
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.09] * 6),
             ("Rake", rake, [0.1, 0.08, 0.05, 0.08, 0.1, 0.12]),
             ("Lamp", lamp, [0.1, 0.1, 0.1, 0.06, 0.1, 0.1, 0.12])]
    anims += tail_anims(idle[0], [d0, d1, matron_corpse(0), matron_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("MothMatron", anims, outdir, scale=6)


def _claw_rake(r):
    for k in range(3):
        swipe_arc(r, 4.0, -12.0 + k * 1.5, 10.0 + k, -50, 40, "ember", 4.8, 1, 3 - (k == 2))


def _little_moths(r, k):
    for i, (x, y) in enumerate(((8, -22), (12, -18), (10, -25))):
        x += k * 3; y -= k
        r.dot(x, y, "ember", 4, 5.0); r.dot(x - 1, y - 1, "ember", 2, 5.0); r.dot(x + 1, y - 1, "ember", 2, 5.0)


def matron_corpse(stage):
    r = Rig()
    r.poly([(-9, -1), (-3, -5), (4, -4), (8, -1), (0, 0)], "moth", 0.0, bias=-0.1)
    r.ell(8.0, -2.4, 2.0, 1.8, "ashw", 0.5)
    r.dot(8.6, -2.8, "soot", 0, 0.6)
    for s in (-1, 1): r.line(9.5, -3.5, 12.0, -4.5 + s, "ash", 0.6, tone=3)
    if stage == 0: ember_dots(r, [(-2, -3, 3), (1, -2, 2)])
    return r.resolve()


# ================================================================== CANDELABRA
def candelabra(lean=0.0, feet=None, bob=0.0, arms=0.0, flare=0.0, ph=0, extra=None, face="calm", tilt=0.0, out=False):
    """A walking iron candelabrum: a stem on three clawed iron feet, five branching arms each holding a candle, a
    wax-crusted face set in the stem. arms: -1 drooped .. 1 swept up (the fan); flare: the flames leap (Vigil)."""
    r = Rig()
    if feet is None:
        feet = ((-4.0, 0.0), (0.5, 0.0), (4.5, 0.0))
    base = (lean * 0.4, -2.4 + bob)
    for k, (fx, fy) in enumerate(feet):
        z = -0.5 if k == 0 else 0.6 if k == 2 else 0.2
        kx, ky = lerp(base[0], fx, 0.5), base[1] + 0.6 - 1.2
        r.tube([base, (kx, ky), (fx, fy - 0.6)], [1.0, 0.8, 0.6], "iron", z)
        r.dot(fx + 1, fy - 0.2, "iron", 2, z + 0.01)
    T = Xf(tilt, base)
    top = T(base[0] + lean, base[1] - 10.0)
    r.tube([base, T(base[0] + lean * 0.5, base[1] - 5.5), top], [1.6, 2.0, 1.5], "iron", 0.0)
    # the face in the stem, half drowned in wax
    fx_, fy_ = T(base[0] + lean * 0.5, base[1] - 5.8)
    r.ell(fx_, fy_, 2.2, 2.6, "tallow", 0.5)
    r.dot(fx_ - 0.8, fy_ - 0.6, "soot", 0, 0.6); r.dot(fx_ + 0.8, fy_ - 0.6, "soot", 0, 0.6)
    r.dot(fx_ + 0.8, fy_ - 0.6, "ember", 2 if face != "dead" else 1, 0.61)
    r.line(fx_ - 0.6, fy_ + 1.0, fx_ + 0.8, fy_ + (1.4 if face == "shout" else 1.0), "soot", 0.61, tone=1)
    drip(r, fx_ - 1.2, fy_ + 1.8, 2.0, "tallow", 0.62)
    # five arms: two pairs and the crown
    tips = []
    for k, (ang, ln) in enumerate(((-165, 9.0), (-125, 6.5), (-90, 3.0), (-55, 6.5), (-15, 9.0))):
        a = math.radians(ang + arms * (ang + 90) * -0.35 + tilt)
        mid = (top[0] + ln * 0.6 * math.cos(a), top[1] + 1.6 + ln * 0.6 * math.sin(a))
        end = (top[0] + ln * math.cos(a), top[1] + ln * math.sin(a) * 0.6 - 1.5)
        z = 1.0 if 1 <= k <= 3 else 1.4 if k == 4 else -0.6
        r.tube([(top[0], top[1] + 1.5), mid, end], [1.0, 0.8, 0.7], "iron", z)
        r.ell(end[0], end[1], 1.4, 0.6, "iron", z + 0.01)   # the drip pan
        tips.append((end, z))
    for k, (end, z) in enumerate(tips):
        candle(r, end[0], end[1] - 0.4, 2.6 if k != 2 else 3.2, 1.6, z=z + 0.02, ph=ph + k, flh=2.6 + 2.2 * flare, out=out, drip=1)
    if extra: extra(r)
    return r.resolve()


def candelabra_sheet(outdir):
    Cb = candelabra
    idle = [Cb(bob=[0, -0.3, -0.5, -0.3][i], ph=i) for i in range(4)]
    run = []
    for i in range(6):
        a = i / 6.0 * math.tau
        feet = ((-4.0 + 1.6 * math.cos(a), -max(0, math.sin(a))), (0.5 - 1.6 * math.cos(a), -max(0, -math.sin(a))),
                (4.5 + 1.6 * math.cos(a + 2), -max(0, math.sin(a + 2))))
        run.append(Cb(feet=feet, lean=0.8, bob=-0.6 * abs(math.sin(a)), tilt=3 * math.sin(a), ph=i))
    fan = [Cb(arms=-0.4, lean=-0.6, ph=0), Cb(arms=-0.8, lean=-1.2, tilt=-6, ph=1), Cb(arms=-1.0, lean=-1.4, tilt=-8, ph=2, flare=0.4),
           Cb(arms=1.0, lean=1.4, tilt=8, flare=1.0, ph=3, face="shout"), Cb(arms=0.8, lean=1.0, tilt=5, flare=0.4, ph=4),
           Cb(arms=0.2, lean=0.4, ph=5), Cb(ph=0)]
    vigil = [Cb(bob=1.0, feet=((-5.0, 0), (0.5, 0), (5.5, 0)), ph=0), Cb(bob=1.6, feet=((-5.5, 0), (0.5, 0), (6.0, 0)), arms=0.6, flare=0.6, ph=1, face="shout")]
    for i in range(6):
        vigil.append(Cb(bob=1.6, feet=((-5.5, 0), (0.5, 0), (6.0, 0)), arms=0.8 + 0.1 * (i % 2), flare=1.0 - 0.15 * (i % 2), ph=i + 2,
                        face="shout", extra=(lambda k: lambda r: _vigil_ring(r, k))(i)))
    knock = Cb(lean=-1.6, tilt=-12, arms=-0.6, ph=2)
    d0 = Cb(lean=-1.8, tilt=-16, arms=-1.0, ph=1, face="shout")
    d1 = Cb(tilt=-50, arms=-1.0, ph=3, bob=2.0, out=True, face="dead")
    anims = [("Idle", idle, [0.18, 0.15, 0.18, 0.15]), ("Run", run, [0.1] * 6),
             ("Fan", fan, [0.1, 0.1, 0.08, 0.06, 0.1, 0.1, 0.12]),
             ("Vigil", vigil, [0.15, 0.2, 0.19, 0.19, 0.19, 0.19, 0.19, 0.2])]
    anims += tail_anims(idle[0], [d0, d1, candelabra_corpse(0), candelabra_corpse(1)], [0.1, 0.12, 0.14, 0.4], knock)
    return sheet("Candelabra", anims, outdir, scale=6)


def _vigil_ring(r, k):
    glow_ring(r, 0.0, -1.0, 11.0 + (k % 3), "fire", -3.0, tone=2 + (k % 2), ry=3.0)


def candelabra_corpse(stage):
    r = Rig()
    r.tube([(-8, -1.5), (8, -1.5)], [1.2, 1.2], "iron", 0.0)
    for k, x in enumerate((-10.0, -6.0, 9.0)):
        r.tube([(x * 0.8, -1.5), (x, -4.0)], [0.6, 0.6], "iron", 0.3)
        candle(r, x, -4.0, 1.6, 1.4, z=0.4, out=True, ph=k)
    r.ell(0.0, -2.2, 2.0, 2.0, "tallow", 0.5)
    floor_pool(r, 0.0, -0.4, 11.0, 0.9, "tallow", -2.0, tone=2 if stage else 3)
    return r.resolve()


JOBS += [("VhWickworm", worm_sheet), ("VhTallowSow", sow_sheet), ("MothMatron", matron_sheet), ("Candelabra", candelabra_sheet)]
SYNC.update({
    "VhWickworm": {"Bite": [("SNAP: jaws at (17, -3); bite box 14 x 12 at (13, -4)", 3)],
                   "Road": [("loops while it slithers; the road drips behind it", 0)]},
    "VhTallowSow": {"Spray": [("3 drops leave the snout at (13, -7)", 3)], "Lay": [("3 eggs dropped behind her at (-9, 0)", 4)]},
    "MothMatron": {"Rake": [("RAKE: claws through (10, -8)", 2), ("ash puff at (12, -7)", 3)],
                   "Lamp": [("3 ember moths leave the raised hands at (6, -19)", 3)]},
    "Candelabra": {"Fan": [("5 flames leave the candles at (7, -17)", 3)],
                   "Vigil": [("planted; candles flare: all wax within 40 px lights", 1), ("flame 1", 3), ("flame 2", 5), ("flame 3", 7)]},
})
NOTES.update({"VhWickworm": "Swim / SwimRun: under the wax, only the five candle flames show (drawn without the floor cut).",
              "VhTallowSow": "IdleCoat / RunCoat: greased (a pale shine; the hero's shots glance off for half damage)."})
