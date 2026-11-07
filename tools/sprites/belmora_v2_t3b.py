"""Bel'Mora tier 3, part two: Gulper Eel (new), Slime Hag, Abyss Kraken, Belltower Hermit, Anemone Colossus, Reef
Champion. Built through belmora_v2_rigs.py. T3 idle limit 42 x 40."""
import math
from belmora_v2_rigs import (Rig, Xf, poly_px, chain, ik, lerp, eye, spines, foam_ring, drips, bubbles, barnacles, leg, crab_legs,
                             claw, fin, kelp_strand, bell_shape, dust, splash, star, arc_smear, sheet, tail_anims, legend)
from belmora_v2_t2 import glove, sucker
from belmora_v2_t3 import tentacle, curl


def smear_lines(r, smear, z=5.0):
    if smear:
        for (p, q, m, t) in smear: r.line(*p, *q, m, z, tone=t)


# ================================================================== GULPER EEL (new: replaces the Storm Eel)
def gulper(gape=0.15, bob=0.0, lean=0.0, k=0, full=0.0, light=3, x=0.0, gag=False, hurt=False, smear=None, extra=None,
           ripple=None, head_dy=0.0):
    """A pelican eel: an enormous hinged jaw with a pale pouch, a thin whip of a body curling up behind it, a pink
    light on the tip of its tail. gape 0..1 opens the jaw (1 = unhinged, the lower jaw on the floor); full 0..1
    swells the pouch (Full Pouch)."""
    r = Rig()
    hx, hy = x + 2.0, -17.0 + bob + head_dy          # the jaw hinge
    T = Xf(lean, (hx, hy))
    # the whip body: from the back of the head down to the floor, then curling up behind into the tail
    body = [T(hx - 2.0, hy + 1.0), (hx - 6.0, -5.0), (hx - 10.0, -2.0), (hx - 15.0, -2.5 + math.sin(k) * 0.8),
            (hx - 18.0, -6.0), (hx - 18.5 + math.sin(k * 0.7) * 1.0, -12.0), (hx - 16.0 + math.sin(k * 0.7) * 1.5, -18.0),
            (hx - 13.0 + math.sin(k * 0.7 + 1) * 1.5, -22.0)]
    radii = [3.2, 2.8, 2.3, 1.9, 1.5, 1.2, 0.9, 0.6]
    r.tube(body, radii, "gulp", -0.5)
    for i in range(1, 6): r.dot(body[i][0] - 0.5, body[i][1] - radii[i] + 0.3, "gulp", 4, -0.45)
    # the tail light: a pink lure on the tip, flickering
    tx, ty = body[-1]
    r.dot(tx, ty, "tlight", 3 + (light >= 3), -0.4)
    if light >= 2:
        for (dx, dy) in ((-1, 0), (1, 0), (0, -1)): r.dot(tx + dx, ty + dy, "tlight", 1 + (light >= 3), -0.41)
    # upper jaw: a long thin beak hinged at the head; lower jaw drops with the gape, the pale pouch slung between
    ua = -10.0 - gape * 25.0
    la = 35.0 + gape * 45.0
    ul = 18.0
    up_tip = T(hx + math.cos(math.radians(ua)) * ul, hy + math.sin(math.radians(ua)) * ul)
    lo_tip = T(hx + math.cos(math.radians(la)) * ul * 0.95, hy + math.sin(math.radians(la)) * ul * 0.95)
    if lo_tip[1] > -0.5:
        lo_tip = (lo_tip[0], -0.5)
    pouch_bulge = 3.5 + full * 5.0 + gape * 2.0
    mid = ((up_tip[0] + lo_tip[0]) / 2 - 2.0 + full * 1.0, (up_tip[1] + lo_tip[1]) / 2 + pouch_bulge * 0.6)
    # the pouch: pale stretch-skin from the hinge to both jaw tips, bulging down into a soft belly. Hand-shaded:
    # a pale throat under the jaw line, mid-tone body, a shadowed underside, pleats that stretch flat when full
    pts = [T(hx, hy), up_tip, (up_tip[0] - 1.0, up_tip[1] + 1.0), mid, (lo_tip[0] - 1.0, lo_tip[1]), lo_tip,
           T(hx - 1.0, hy + 3.0)]
    if gape < 0.6:
        pts = [T(hx, hy), up_tip, lo_tip, (mid[0] - 1.0, min(-0.5, mid[1] + pouch_bulge * 0.5)), T(hx - 2.0, hy + 4.0 + full * 2)]
    bxp, byp = mid[0] - 1.5, min(-3.0 - full * 2.0, mid[1] + 3.0 + full * 2.0)
    brx, bry = 5.0 + full * 2.5 + gape * 1.5, 3.0 + full * 3.0
    cells = set(poly_px(pts))
    for y in range(int(byp - bry) - 1, int(byp + bry) + 2):
        for x in range(int(bxp - brx) - 1, int(bxp + brx) + 2):
            if ((x - bxp) / brx) ** 2 + ((y - byp) / bry) ** 2 <= 1.0: cells.add((x, y))
    cells = {c for c in cells if c[1] <= -1}
    if cells:
        top = min(c[1] for c in cells); bot = max(c[1] for c in cells)
        x0 = min(c[0] for c in cells); x1 = max(c[0] for c in cells)
        pp = r.part(False, 0.0); r.hand.add(pp)
        for (x, y) in cells:
            v = (y - top) / max(1.0, bot - top)
            u = (x - x0) / max(1.0, x1 - x0)
            t = 4 if v < 0.12 else 3 if v < 0.4 - full * 0.1 else 2 if v < 0.8 else 1
            if u > 0.85 and t > 1: t -= 1
            if (x, y + 1) not in cells: t = 0 if v > 0.6 else 1
            # pleats run down and back; a full pouch stretches them smooth
            if full < 0.5 and v > 0.3 and (x + y * 2) % 5 == 0 and t > 1: t -= 1
            # stretch-skin mottling
            if t == 3 and (x * 7 + y * 13) % 11 == 0: t = 2
            r.put(x, y, 0.0, "pouch", 0.5, pp, t)
        if full > 0.2:
            for i in range(3): r.dot(bxp - 3 + i * 2.5, byp - bry * 0.4 + (i % 2), "pouch", 4, 0.02)   # stretched shine
            for i in range(2): r.dot(bxp + 1 + i * 2, byp + bry * 0.4, "pink", 2, 0.02)              # blood under the skin
    if gape >= 0.3:
        # the open maw: a red-pink throat going dark down the gullet, a tongue along the lower jaw, needle teeth
        inner = [T(hx + 1.0, hy), (up_tip[0] - 1.5, up_tip[1] + 1.5), (lo_tip[0] - 1.5, lo_tip[1] - 1.0)]
        ip = r.part(False, 0.05); r.hand.add(ip)
        hx0, hy0 = T(hx + 1.0, hy)
        span = max(1.0, math.hypot(up_tip[0] - hx0, up_tip[1] - hy0))
        for (x, y) in poly_px(inner):
            d = math.hypot(x - hx0, y - hy0) / span
            m, t = ("coral", 0) if d < 0.25 else ("coral", 1) if d < 0.45 else ("pink", 1) if d < 0.7 else ("pink", 2)
            r.put(x, y, 0.05, m, 0.5, ip, t)
        tg = [(lerp(hx0, lo_tip[0], t), lerp(hy0, lo_tip[1], t) - 1.5) for t in (0.35, 0.55, 0.75)]
        r.tube(tg, [1.4, 1.6, 1.1], "pink", 0.07, bias=0.2)
        for k in range(9):
            t = 0.3 + k * 0.08
            ux, uy = lerp(hx0, up_tip[0], t), lerp(hy0, up_tip[1], t)
            lx, ly = lerp(hx0, lo_tip[0], t), lerp(hy0, lo_tip[1], t)
            r.dot(ux, uy + 1, "ivory", 4 if k % 2 else 3, 0.1)
            if k % 2: r.dot(ux, uy + 2, "ivory", 2, 0.1)
            r.dot(lx, ly - 1, "ivory", 3, 0.1)
            if k % 2 == 0: r.dot(lx, ly - 2, "ivory", 2, 0.1)
    else:
        # shut: the lip line between the jaws, a sliver of pink and the tips of the needles
        for k in range(6):
            t = 0.35 + k * 0.1
            x, y = lerp(hx, up_tip[0], t), lerp(hy + 1.5, up_tip[1] + 1.5, t)
            r.dot(x, y, "pink", 2, 0.06)
            if k % 2: r.dot(x, y + 1, "ivory", 3, 0.07)
    # jaw bones over the pouch
    r.line(*T(hx, hy), *up_tip, "gulp", 0.2, tone=3)
    r.line(*T(hx, hy + 0.5), *lo_tip, "gulp", 0.2, tone=2)
    r.dot(*up_tip, "gulp", 4, 0.25)
    # the head: small, a tiny cyan eye right at the hinge
    r.ell(*T(hx - 1.0, hy - 0.5), 2.6, 2.2, "gulp", 0.3)
    eye(r, *T(hx, hy - 1.2), 0.4, big=True)
    if hurt: r.dot(*T(hx, hy - 1.2), "gulp", 4, 0.5)
    if gag:
        for (dx, dy) in ((14, -16), (16, -13), (15, -18)): r.dot(x + dx, dy, "foam", 3, 6.0)
    if ripple is not None:
        for i in range(3):
            rr = 4 + i * 3 + ripple * 2
            for a in range(-70, 71, 20):
                aa = math.radians(a)
                r.dot(x + 16 + math.cos(aa) * rr * 0.4, -0.5 + math.sin(aa) * rr * 0.25, "foam", 3 - i if i < 3 else 1, -3.0)
    smear_lines(r, smear)
    if extra: extra(r)
    return r.resolve()


def gulper_corpse(stage):
    r = Rig()
    r.tube([(-14, -2), (-8, -1.5), (-2, -2), (3, -3)], [0.6, 1.4, 2.0, 2.6], "gulp", -0.5, bias=-0.15)
    r.poly([(3, -4), (16, -2), (14, 0), (4, 0)], "pouch", 0.0, bias=-0.15)
    r.line(3, -4, 16, -3, "gulp", 0.1, tone=2)
    r.dot(-14, -2.5, "tlight", 1 if stage else 2, 0.0)
    if stage == 0: dust(r, 6, 0, 1, 1.2)
    return r.resolve()


def gulper_sheet(out):
    Gp = gulper
    idle = [Gp(gape=[0.12, 0.16, 0.2, 0.16][i], bob=[0, -0.3, -0.6, -0.3][i], k=i, light=[3, 2, 3, 3][i]) for i in range(4)]
    run = [Gp(gape=0.1, bob=[0, -0.6, -1.0, -0.6, 0, -0.3][i], k=i * 1.4, lean=6, light=3) for i in range(6)]
    full_i = [Gp(full=1.0, gape=0.08, bob=[0, 0.3, 0.6, 0.3][i], k=i, light=[3, 1, 2, 1][i]) for i in range(4)]
    full_r = [Gp(full=1.0, gape=0.05, bob=[0, -0.3, -0.5, -0.3, 0, -0.2][i], k=i * 0.7, lean=4, light=[2, 1, 3, 1, 2, 1][i])
              for i in range(6)]
    # Scoop (7): rear the jaw up (0-1), SWEEP it wide across the floor (3: the jaw at (16, -5)), snap shut (4-6)
    scoop = [Gp(gape=0.4, lean=-8, head_dy=-1.0), Gp(gape=0.6, lean=-14, head_dy=-2.0),
             Gp(gape=0.7, lean=10, smear=[((6, -24), (18, -14), "pouch", 2)]),
             Gp(gape=0.5, lean=18, x=2.0, extra=lambda r: dust(r, 18, 0, 0, 1.2)),
             Gp(gape=0.2, lean=10, x=1.0), Gp(gape=0.15, lean=4), Gp()]
    # Unhinge (10): the jaw unhinges, wider and wider (0-3: 0.6 s, the floor ahead rippling), GULP 30 px forward
    # (4: the mouth slams shut on (18, -6)), swallow (5-6: the pouch swells), settle with a full pouch (7-9)
    unh = [Gp(gape=0.5, lean=-6, ripple=0), Gp(gape=0.75, lean=-10, ripple=1), Gp(gape=0.95, lean=-12, ripple=2, light=2),
           Gp(gape=1.0, lean=-12, ripple=3, light=1),
           Gp(gape=0.1, lean=20, x=4.0, smear=[((-6, -20), (2, -18), "gulp", 2), ((-6, -10), (4, -8), "pouch", 2)],
              extra=lambda r: splash(r, 18, 0, 0, 1.2)),
           Gp(gape=0.05, full=0.6, lean=10, x=2.0), Gp(gape=0.05, full=1.0, lean=4, x=1.0),
           Gp(gape=0.05, full=1.0), Gp(gape=0.05, full=1.0, bob=0.5), Gp(gape=0.05, full=1.0)]
    # Gag (6): an empty gulp: it chokes, jaw working, spitting foam
    gag = [Gp(gape=0.4, lean=-6, gag=True, head_dy=1.0), Gp(gape=0.1, lean=8, head_dy=2.0), Gp(gape=0.5, lean=-8, gag=True),
           Gp(gape=0.1, lean=10, head_dy=2.0), Gp(gape=0.4, lean=-4, gag=True), Gp(gape=0.15)]
    d0 = Gp(hurt=True, gape=0.7, lean=-14)
    d1 = Gp(hurt=True, gape=0.9, lean=-30, bob=4.0, light=1)
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.08] * 6),
             ("IdleFull", full_i, [0.2, 0.18, 0.2, 0.18]), ("RunFull", full_r, [0.12] * 6),
             ("Scoop", scoop, [0.12, 0.12, 0.06, 0.06, 0.1, 0.12, 0.14]),
             ("Unhinge", unh, [0.15, 0.15, 0.15, 0.15, 0.06, 0.1, 0.1, 0.12, 0.12, 0.14]),
             ("Gag", gag, [0.16, 0.16, 0.16, 0.16, 0.16, 0.2])]
    anims += tail_anims(idle[0], [d0, d1, gulper_corpse(0), gulper_corpse(1)], [0.08, 0.12, 0.14, 0.4], Gp(hurt=True, gape=0.6, lean=-16))
    return sheet("BelGulperEel", anims, out)


# ================================================================== SLIME HAG
def hag(k=0.0, bob=0.0, head=(15.0, -7.0), mouth=0.3, knot=0.0, rear=0.0, slime_k=0, hurt=False, smear=None, extra=None,
        spew=False):
    """An eyeless hagfish tied in a loose knot, streamers of slime hanging off it. knot 0..1 cinches the loop into a
    figure-eight (Knot and Tear); rear lifts the head."""
    r = Rig()
    hx, hy = head[0], head[1] + bob - rear * 5.0
    # path: the tail along the floor at the left, up into the loop, round, and out to the head at the right
    L = 6.5 - knot * 1.5
    lc = (-3.0, -9.0 + bob)
    pts = [(-18.0, -2.0 + math.sin(k) * 0.6), (-13.0, -2.5), (-8.0, -3.0)]
    for i in range(9):
        a = math.radians(90 + i * 40 + knot * 20)
        pts.append((lc[0] + math.cos(a) * L * (1.0 - knot * 0.3 * math.sin(a * 2)), lc[1] + math.sin(a) * L))
    pts += [(4.0, -6.0 + bob), (9.0, -5.5 + bob - rear * 2), (hx - 2.0, hy + 0.5)]
    radii = [1.0, 1.9, 2.6] + [3.0] * 9 + [3.0, 2.9, 2.8]
    # back half of the loop first (behind), then the rest
    r.tube(pts[:7], radii[:7], "hag", -0.5, bias=-0.15)
    r.tube(pts[6:], radii[6:], "hag", 0.5)
    # pale belly and the row of slime pores
    for i in range(2, len(pts) - 1, 2):
        r.dot(pts[i][0], pts[i][1] + radii[i] * 0.6, "hag", 3, 0.55)
        r.dot(pts[i][0] + 0.5, pts[i][1] - 0.3, "slime", 3, 0.56)
    # the eyeless head: blunt, barbels round a rasping mouth
    r.ell(hx, hy, 3.4, 2.8, "hag", 0.7)
    for (dx, dy) in ((3.2, -1.5), (3.5, 1.0), (2.5, 2.2)): r.line(hx + dx - 1, hy + dy * 0.5, hx + dx + 1.5, hy + dy, "hag", 0.75, tone=3)
    if mouth > 0.2:
        r.ell(hx + 2.5, hy + 0.5, 1.2, 0.6 + mouth, "pink", 0.8, flat=1)
        r.dot(hx + 3.0, hy + 0.5 - mouth, "ivory", 3, 0.85); r.dot(hx + 3.0, hy + 0.5 + mouth, "ivory", 2, 0.85)
    if hurt: r.dot(hx, hy - 1.5, "hag", 4, 0.9)
    # slime streamers hanging from the loop and the head
    for j, i in enumerate((4, 7, 10, len(pts) - 2)):
        x, y = pts[i]
        ln = 3 + (j + slime_k) % 3
        for d in range(ln):
            if y + radii[i] + d > -0.5: break
            r.dot(x + (0.5 if d % 2 else 0), y + radii[i] + d, "slime", 3 if d == 0 else 2, 1.0)
    if spew:
        for (dx, dy, t) in ((5, -2, 4), (7, -3, 3), (8, 0, 3), (10, -1, 2)): r.dot(hx + dx, hy + dy, "slime", t, 6.0)
    smear_lines(r, smear)
    if extra: extra(r)
    return r.resolve()


def hag_corpse(stage):
    r = Rig()
    pts = [(-16, -1.5), (-8, -2.0), (0, -2.5), (6, -2.0), (12, -2.5)]
    r.tube(pts, [0.8, 2.0, 2.4, 2.4, 2.2], "hag", 0.0, bias=-0.15)
    r.ell(13.0, -2.5, 3.0, 2.0, "hag", 0.1, bias=-0.15)
    for i in range(5): r.dot(-12 + i * 5, -0.5, "slime", 2 if stage else 3, 0.2)
    r.ell(0, -0.5, 10.0, 1.0, "slime", -0.5, flat=1)
    return r.resolve()


def hag_sheet(out):
    Hg = hag
    idle = [Hg(k=i, bob=[0, -0.3, -0.5, -0.3][i], slime_k=i, mouth=[0.3, 0.4, 0.5, 0.4][i]) for i in range(4)]
    run = [Hg(k=i * 1.2, bob=[0, -0.6, -1.0, -0.6, 0, -0.3][i], slime_k=i, head=(15.5, -6.5), knot=0.1 * (i % 2)) for i in range(6)]
    # Bite (6): rear (0-1), lunge and RASP (3: mouth at (19, -6)), hold (4), pull back (5)
    bite = [Hg(rear=0.6, mouth=0.6), Hg(rear=1.0, mouth=1.0, head=(13.0, -7.0)),
            Hg(head=(18.0, -6.0), mouth=1.0, smear=[((12, -15), (17, -9), "hag", 2)]),
            Hg(head=(19.0, -6.0), mouth=0.1, extra=lambda r: star(r, 23, -6, 1)),
            Hg(head=(18.0, -6.5), mouth=0.3), Hg(mouth=0.4)]
    # Knot (6): the bite took: she ties herself into a figure-eight (0-2), TWISTS (3: a second bite at (19, -6)), loosens
    knot = [Hg(knot=0.4, head=(18.0, -6.0), mouth=0.2), Hg(knot=0.8, head=(17.0, -6.5), mouth=0.6),
            Hg(knot=1.0, head=(16.0, -8.0), mouth=1.0, rear=0.3),
            Hg(knot=1.0, head=(19.0, -6.0), mouth=0.1, smear=[((14, -12), (18, -8), "hag", 2)], extra=lambda r: star(r, 23, -6, 1)),
            Hg(knot=0.6, head=(18.0, -6.0), mouth=0.3), Hg(knot=0.2)]
    # Spew (7): rear and swell (0-2), SPEW (4: three globs from (19, -9)), drip (5-6)
    spew = [Hg(rear=0.4, mouth=0.3), Hg(rear=0.8, mouth=0.5), Hg(rear=1.0, mouth=0.8, head=(14.0, -8.0)),
            Hg(rear=0.6, mouth=1.0, head=(16.0, -8.0), spew=True), Hg(rear=0.4, mouth=1.0, head=(17.0, -7.0), spew=True,
                                                                       smear=[((19, -9), (25, -9), "slime", 3)]),
            Hg(rear=0.2, mouth=0.6, slime_k=1), Hg(mouth=0.3, slime_k=2)]
    d0 = Hg(hurt=True, rear=1.0, mouth=1.0, knot=0.5)
    d1 = Hg(hurt=True, knot=0.0, head=(16.0, -3.0), mouth=1.0)
    anims = [("Idle", idle, [0.18, 0.16, 0.18, 0.16]), ("Run", run, [0.09] * 6),
             ("Bite", bite, [0.12, 0.12, 0.06, 0.08, 0.12, 0.14]), ("Knot", knot, [0.1, 0.1, 0.12, 0.06, 0.1, 0.12]),
             ("Spew", spew, [0.12, 0.12, 0.1, 0.06, 0.1, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, hag_corpse(0), hag_corpse(1)], [0.08, 0.12, 0.14, 0.4], Hg(hurt=True, rear=0.8, mouth=0.8))
    return sheet("BelSlimeHag", anims, out)


# ================================================================== ABYSS KRAKEN
KRAK_LEG = legend(k="tent:0", d="tent:1", s="tent:2", S="tent:3", e="lure:3", E="lure:4", W="ivory:3", w="ivory:2", m="tent:0")


def kraken(k=0.0, bob=0.0, lean=0.0, pale=False, slam=None, dive=0.0, hurt=False, smear=None, extra=None, eyes=2):
    """A kraken's head and mantle hauled up from the deep, its arms coiling round it on the floor. pale: the mantle
    blanched (Arms Out: three arms up, the head open). slam: (x, y) the two front arms strike to; dive 0..1 drives
    the arms into the floor (Erupt)."""
    r = Rig()
    mat = "tent"
    cx, cy = 0.0, -21.0 + bob
    T = Xf(lean, (0.0, -6.0))
    # back arms coiling on the floor
    for i, (ang, ln, bend) in enumerate(((190, 23, -12), (165, 19, 16), (220, 16, -24))):
        sx, sy = T(-3.0 + i, -8.0 + bob)
        pts = curl(sx, sy, ang - dive * 60, ln * (1 - dive * 0.5), bend + 6 * math.sin(k + i), n=7)
        pts = [(x, min(y, -0.6)) for (x, y) in pts]
        tentacle(r, pts, 2.6, mat, -1.0 - i * 0.01, suckers="lure", bias=-0.25)
    # mantle: a tall bulb tipped back, ridged
    mx, my = T(-2.0, cy - 3.0)
    r.ell(mx, my, 9.5, 11.5, "hag" if pale else mat, 0.0, ang=-12 + lean, bias=0.05)
    for i in range(4):
        a, b = T(-6.0 + i * 3.0, cy - 12.0 + abs(i - 1.5)), T(-5.0 + i * 3.0, cy + 2.0)
        r.line(*a, *b, "hag" if pale else mat, 0.05, tone=1)
    r.dot(*T(-6.0, cy - 9.0), "hag" if pale else mat, 4, 0.06)
    # the head: big eyes at the base of the mantle, a beak below
    hx, hy = T(3.0, cy + 7.0)
    r.ell(hx, hy, 8.0, 5.5, mat, 0.5)
    for ex in ((hx + 3.0, hy - 1.5), (hx - 2.0, hy - 2.0)):
        r.ell(ex[0], ex[1], 1.8, 1.5, "ivory", 0.6, flat=2)
        r.dot(ex[0] + 0.3, ex[1], "lure", 4 if eyes >= 2 else 2, 0.65)
        r.dot(ex[0] + 0.3, ex[1] + 0.8, mat, 0, 0.65)
    if hurt: r.dot(hx + 3.3, hy - 1.5, "ivory", 4, 0.7)
    r.poly([(hx + 5.5, hy + 1.0), (hx + 8.0, hy + 2.5), (hx + 5.5, hy + 3.5)], "ivory", 0.62, bias=-0.1)
    # front arms
    for i, (ang, ln, bend) in enumerate(((10, 20, 16), (55, 15, 26), (125, 16, -22))):
        sx, sy = hx + (-2.0 + i * 2.0), hy + 3.5
        if slam and i < 2:
            tx, ty = slam[0] - i * 3.0, slam[1] + i
            pts = [(sx, sy), ((sx + tx) / 2, min(sy, ty) - 6.0 + i * 2), (tx, ty)]
            pts = [pts[0]] + [(lerp(pts[0][0], pts[1][0], t) if t < 1 else pts[1][0], lerp(pts[0][1], pts[1][1], t)) for t in (0.5, 1.0)] + \
                  [(lerp(pts[1][0], pts[2][0], t), lerp(pts[1][1], pts[2][1], t)) for t in (0.5, 1.0)]
        else:
            pts = curl(sx, sy, ang + dive * 40, ln * (1 - dive * 0.4), bend + 8 * math.sin(k * 1.1 + i), n=7)
        pts = [(x, min(y, -0.6)) for (x, y) in pts]
        tentacle(r, pts, 2.8, mat, 1.0 + i * 0.01, suckers="lure")
    if dive > 0.3:
        for x in (-8, 8, 14): splash(r, x, 0, int(dive * 2.9) % 3)
    smear_lines(r, smear)
    if extra: extra(r)
    return r.resolve()


def kraken_corpse(stage):
    r = Rig()
    r.ell(-4.0, -4.0, 11.0, 4.5, "tent", 0.0, bias=-0.15)
    r.ell(6.0, -3.0, 5.0, 3.0, "tent", 0.1, bias=-0.1)
    r.dot(8.0, -4.0, "ivory", 2, 0.2)
    for i in range(5):
        pts = curl(4.0 + i, -1.5, -10 + i * 40, 10, 15, n=6)
        pts = [(x, min(y, -0.5)) for (x, y) in pts]
        tentacle(r, pts, 1.6, "tent", 0.2 + i * 0.01, bias=-0.2)
    if stage == 0: dust(r, 0, 0, 1, 1.5)
    return r.resolve()


def kraken_sheet(out):
    Kr = kraken
    idle = [Kr(k=i * 0.8, bob=[0, -0.4, -0.8, -0.4][i]) for i in range(4)]
    run = [Kr(k=i * 1.2, bob=[0, -0.8, -1.2, -0.8, 0, -0.4][i], lean=6) for i in range(6)]
    open_i = [Kr(k=i * 0.8, bob=[0, -0.4, -0.8, -0.4][i], pale=True, eyes=1) for i in range(4)]
    open_r = [Kr(k=i * 1.2, bob=[0, -0.8, -1.2, -0.8, 0, -0.4][i], lean=6, pale=True, eyes=1) for i in range(6)]
    # Slam (7): two arms rear up (0-1), SLAM the floor ahead (3: tips at (18, -2)), drag back (4-6)
    slam = [Kr(slam=(10.0, -26.0), lean=-4), Kr(slam=(6.0, -30.0), lean=-8),
            Kr(slam=(16.0, -10.0), lean=6, smear=[((8, -30), (16, -14), "tent", 2)]),
            Kr(slam=(18.0, -2.0), lean=10, extra=lambda r: dust(r, 18, 0, 0, 1.4)),
            Kr(slam=(17.0, -2.0), lean=8, extra=lambda r: dust(r, 18, 0, 1, 1.6)), Kr(slam=(12.0, -8.0), lean=4), Kr()]
    # Erupt (8): the arms rise (0-1), drive down into the floor (2-3: the arms erupt from 3), held under (4-6), back (7)
    erupt = [Kr(dive=0.0, bob=-1.0, lean=-4), Kr(dive=0.2, bob=-1.5, lean=-6), Kr(dive=0.7, bob=1.0, lean=6),
             Kr(dive=1.0, bob=1.5, lean=8), Kr(dive=1.0, bob=1.2, k=1), Kr(dive=1.0, bob=1.0, k=2), Kr(dive=0.6, k=3), Kr(dive=0.1)]
    d0 = Kr(hurt=True, lean=-10, bob=-1.0, eyes=1)
    d1 = Kr(hurt=True, lean=-25, bob=4.0, dive=0.5, pale=True, eyes=0)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.1] * 6),
             ("IdleOpen", open_i, [0.2, 0.18, 0.2, 0.18]), ("RunOpen", open_r, [0.1] * 6),
             ("Slam", slam, [0.14, 0.12, 0.06, 0.06, 0.12, 0.12, 0.14]),
             ("Erupt", erupt, [0.12, 0.12, 0.08, 0.1, 0.12, 0.12, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, kraken_corpse(0), kraken_corpse(1)], [0.08, 0.12, 0.14, 0.4], Kr(hurt=True, lean=-12))
    return sheet("BelKraken", anims, out)


# ================================================================== BELLTOWER HERMIT
def belltower(phase=0.0, bob=0.0, tilt=0.0, swing=0.0, claw_at=None, claw_open=0.3, ring=0, hurt=False, smear=None,
              extra=None, out=1.0):
    """A hermit crab carrying a drowned stone bell tower for a shell, its bronze bell swinging in the belfry. Red
    legs scuttle under the tower; the crusher claw and eye stalks reach out in front."""
    r = Rig()
    base = -4.0 + bob
    T = Xf(tilt, (0.0, base))
    if out > 0.2:
        crab_legs(r, 2.0, base - 1.0, 8.0, 3, phase, "coral", 1.4, -1.4, step=1.8, reach=3.5, lift=1.4, knee=2.5, spread=2.0, rad=0.7)
    # the tower: a stone shaft with a belfry opening and a pointed slate roof, barnacles and kelp clinging
    x0, x1 = -12.0, 7.0
    tw = [T(x0, base), T(x1, base), T(x1 - 0.5, base - 24.0), T(x0 + 0.5, base - 24.0)]
    r.poly(tw, "tower", 0.0, curve=0.9, normal=(-0.1, -0.2, 1.0))
    for row in range(6):
        yy = base - 2.0 - row * 4.0
        for c in range(4):
            xx = x0 + 1.0 + c * 3.5 + (1.5 if row % 2 else 0)
            if xx < x1 - 1: r.dot(*T(xx, yy), "tower", 1, 0.01)
        r.line(*T(x0 + 0.5, yy + 1.5), *T(x1 - 0.5, yy + 1.5), "tower", 0.01, tone=1)
    # belfry arch with the bell inside, swinging
    ax, ay = T(-2.0, base - 17.0)
    r.ell(ax, ay, 4.2, 4.0, "tower", 0.02, flat=0)
    r.poly([T(-6.2, base - 13.0), T(2.2, base - 13.0), T(2.2, base - 17.0), T(-6.2, base - 17.0)], "tower", 0.02, flat=0)
    bell_shape(r, ax + swing * 2.0, ay + 5.0, 6.5, 6.0, 0.1, tilt=tilt + swing * 20, verd=False, band=False, knob=False)
    r.dot(ax + swing * 3.0, ay + 5.5, "iron", 2, 0.12)
    # roof
    r.poly([T(x0 - 1.5, base - 23.5), T(x1 + 1.5, base - 23.5), T((x0 + x1) / 2, base - 33.0)], "slate", 0.03, normal=(-0.3, -0.6, 1.0))
    r.dot(*T((x0 + x1) / 2, base - 33.5), "bronze", 3, 0.04)
    barnacles(r, [T(-8.0, base - 3.0), T(-7.0, base - 8.0), T(3.5, base - 2.0), T(-8.5, base - 20.0)], 0.05)
    for i, (kx, ky) in enumerate(((-9.5, -22.0), (5.5, -21.0), (-9.5, -12.0))):
        kelp_strand(r, *T(kx, base + ky), 4 + i, 0.4, 0.06, k=int(phase * 6) + i)
    if ring:
        for i in range(ring):
            rr = 6 + i * 3
            for a in range(-180, 1, 30):
                aa = math.radians(a)
                r.dot(ax + math.cos(aa) * rr, ay + math.sin(aa) * rr * 0.8, "spark", 3 - i, 6.0)
    if out > 0.2:
        hx, hy = T(6.0 + 1.0 * out, base - 3.0)
        r.ell(hx, hy, 2.8, 2.4, "coral", 1.0)
        for ex in (hx, hx + 1.8):
            r.line(ex, hy - 1.5, ex + 0.5, hy - 5.5, "coral", 1.1, tone=3)
            eye(r, ex + 0.5, hy - 6.0, 1.2)
        if hurt: r.dot(hx + 2.3, hy - 6.0, "coral", 4, 1.3)
        cx, cy = claw_at or (hx + 8.5, hy + 0.5)
        r.tube([(hx + 1.0, hy + 0.5), (cx - 2.5, cy)], [1.7, 1.5], "coral", 1.6)
        claw(r, cx, cy, -10 + (cx - hx - 6) * 3, 3.5, "coral", 1.7, open_=claw_open, tip="ivory")
    smear_lines(r, smear)
    if extra: extra(r)
    return r.resolve()


def belltower_corpse(stage):
    r = Rig()
    r.poly([(-16, -1), (-16, -9), (6, -9), (6, -1)], "tower", 0.0, curve=0.5, bias=-0.1)
    r.poly([(6, -10), (6, 0), (12, -5)], "slate", 0.1, bias=-0.15)
    bell_shape(r, -4.0, -1.0, 6.0, 6.0, 0.2, tilt=-80, verd=False, band=False, knob=False)
    crab_legs(r, 0.0, -9.5, 5.0, 2, 0.3, "coral", 0.5, -0.5, step=0.0, reach=2.0, lift=0.0, knee=-1.5, rad=0.6)
    if stage == 0: dust(r, -4, 0, 1, 1.6)
    return r.resolve()


def belltower_sheet(out):
    Bt = belltower
    idle = [Bt(swing=[0, 0.4, 0.6, 0.2][i], bob=[0, 0, -0.3, 0][i], claw_open=[0.3, 0.4, 0.5, 0.4][i]) for i in range(4)]
    run = [Bt(phase=i / 6.0, bob=[0, -0.4, 0, -0.4, 0, -0.4][i], tilt=[0, 2, 0, -2, 0, 2][i], swing=[0.5, -0.5][i % 2]) for i in range(6)]
    # Crush (7): draw back (0-1), LUNGE and crush (3: claw tip at (22, -4)), hold, back
    crush = [Bt(claw_at=(14.0, -12.0), claw_open=0.9, tilt=-3), Bt(claw_at=(13.0, -14.0), claw_open=1.0, tilt=-6, swing=-0.6),
             Bt(claw_at=(19.0, -9.0), claw_open=0.9, tilt=4, swing=0.6, smear=[((14, -15), (19, -11), "coral", 2)]),
             Bt(claw_at=(21.0, -5.0), claw_open=0.0, tilt=6, swing=1.0, extra=lambda r: star(r, 25.0, -5.0, 1)),
             Bt(claw_at=(20.0, -5.5), claw_open=0.1, tilt=4, swing=0.6), Bt(claw_at=(17.0, -6.0), claw_open=0.3, swing=-0.4), Bt()]
    # Peals (8): raise the claw (0-1), SLAM it down (3: the first peal leaves at (16, 0)), the tower bell swings and
    # rings (3-7)
    peals = [Bt(claw_at=(13.0, -14.0), claw_open=0.6), Bt(claw_at=(12.0, -17.0), claw_open=0.8, tilt=-4),
             Bt(claw_at=(17.0, -6.0), claw_open=0.2, tilt=4, smear=[((13, -18), (17, -9), "coral", 2)]),
             Bt(claw_at=(17.0, -3.0), claw_open=0.0, tilt=6, swing=1.0, ring=1, extra=lambda r: dust(r, 17, 0, 0, 1.2)),
             Bt(claw_at=(17.0, -3.5), swing=-1.0, ring=2), Bt(claw_at=(16.0, -4.0), swing=0.8, ring=1),
             Bt(swing=-0.6, ring=1), Bt(swing=0.3)]
    d0 = Bt(hurt=True, tilt=-6, claw_open=1.0, swing=1.0)
    d1 = Bt(hurt=True, tilt=-16, out=0.6, swing=1.5)
    anims = [("Idle", idle, [0.2, 0.18, 0.2, 0.18]), ("Run", run, [0.09] * 6),
             ("Crush", crush, [0.14, 0.12, 0.06, 0.06, 0.12, 0.12, 0.12]),
             ("Peals", peals, [0.12, 0.12, 0.06, 0.08, 0.1, 0.1, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, belltower_corpse(0), belltower_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        Bt(hurt=True, tilt=-8, claw_open=0.9))
    return sheet("BelBelltower", anims, out)


# ================================================================== ANEMONE COLOSSUS
def anemone(r, x, y, z, mat, opened, k=0, size=1.0):
    """One anemone on the shell: open, a crown of waving tentacles round a pale mouth; shut, a tight round bud."""
    if opened:
        n = 7
        for i in range(n):
            a = math.radians(-170 + i * (160 / (n - 1)))
            ln = (3.0 + (i % 2)) * size
            sway = math.sin(k * 0.9 + i) * 0.6
            ex, ey = x + math.cos(a) * ln + sway, y + math.sin(a) * ln
            r.line(x, y, ex, ey, mat, z, tone=3 if a < -1.5 else 2)
            r.dot(ex, ey, mat, 4, z + 0.01)
        r.ell(x, y, 1.6 * size, 1.0 * size, mat, z + 0.02, flat=1)
        r.dot(x, y - 0.5, "pearl", 3, z + 0.03)
    else:
        # shut: a fat round bud, its tentacles folded in to a dark puckered tip, seams down its sides
        r.ell(x, y - 1.4 * size, 2.0 * size, 2.0 * size, mat, z, bias=-0.05)
        r.dot(x, y - 3.2 * size, mat, 0, z + 0.01)
        r.dot(x - 0.6, y - 3.0 * size, mat, 1, z + 0.01); r.dot(x + 0.6, y - 3.0 * size, mat, 1, z + 0.01)
        r.line(x - 1.0 * size, y - 2.6 * size, x - 1.4 * size, y - 0.6 * size, mat, z + 0.01, tone=1)
        r.line(x + 0.8 * size, y - 2.6 * size, x + 1.2 * size, y - 0.6 * size, mat, z + 0.01, tone=1)
        r.dot(x - 0.8 * size, y - 2.2 * size, mat, 4, z + 0.02)


def colossus(phase=0.0, bob=0.0, opened=False, k=0, lean=0.0, hammer=0.0, hurt=False, smear=None, extra=None, flick=None):
    """A crab so old its shell is a garden of anemones: a wide hump of colour on short heavy legs. hammer 0..1 lifts
    then drives both pincers into the floor."""
    r = Rig()
    cy = -13.0 + bob
    T = Xf(lean, (0.0, cy))
    crab_legs(r, -2.0, cy + 7.0, 12.0, 3, phase, "barn", 1.4, -1.4, step=1.6, reach=2.5, lift=1.2, knee=3.0, spread=3.0, rad=1.4)
    # the shell: a broad, high barnacled hump
    r.ell(*T(-2.0, cy), 15.0, 12.5, "barn", 0.0)
    r.ell(*T(-2.0, cy + 6.5), 12.0, 2.2, "teal", 0.05, bias=-0.2)
    barnacles(r, [T(-12.0, cy), T(-8.0, cy + 2.0), T(10.0, cy + 1.0), T(12.0, cy - 2.0)], 0.1)
    # the garden: anemones all over the top in pink, orange and green
    spots = [(-12.0, -4.0, "pink", 1.0), (-8.5, -8.0, "orange", 1.1), (-3.5, -10.0, "sea", 1.2), (1.5, -9.5, "pink", 1.3),
             (6.0, -7.0, "orange", 1.0), (9.5, -3.5, "sea", 0.9), (-6.0, -4.0, "pink", 0.9), (3.0, -4.0, "sea", 0.9),
             (-11.0, 0.0, "orange", 0.8), (-1.5, -5.0, "orange", 0.8), (-4.0, 1.0, "sea", 0.7), (6.0, 0.0, "pink", 0.7)]
    for i, (sx, sy, m, sz) in enumerate(spots):
        anemone(r, *T(sx, cy + sy * 1.15), 0.5 + i * 0.01 + (0.2 if sy < -5 else 0.0), m, opened, k + i, sz * 1.2)
    # eye stalks and the two great pincers in front
    hx, hy = T(10.5, cy + 4.0)
    for ex in (hx - 1.0, hx + 1.0):
        r.line(ex, hy - 2.0, ex + 0.5, hy - 5.0, "barn", 1.0, tone=3)
        eye(r, ex + 0.5, hy - 5.5, 1.1)
    if hurt: r.dot(hx + 1.5, hy - 5.5, "barn", 4, 1.2)
    for i, dz in enumerate((-0.5, 2.0)):
        px = hx + 4.0 + i * 2.0
        py = hy + 2.0 - hammer * 9.0 + (hammer > 1.0) * 0.0
        if hammer > 1.0:
            py = -2.5
        r.tube([(hx - 1.0 + i, hy + 2.5), (px - 2.0, py + 1.0)], [1.8, 1.6], "barn", dz, bias=-0.3 if i == 0 else 0.0)
        claw(r, px, py, 60 if hammer > 1.0 else -10 - hammer * 30, 3.0, "barn", dz + 0.01, open_=0.2, tip="coral",
             bias=-0.3 if i == 0 else 0.0)
    if flick:
        for (x, y) in flick: anemone(r, x, y, 6.0, "pink", False, 0, 0.7)
    smear_lines(r, smear)
    if extra: extra(r)
    return r.resolve()


def colossus_corpse(stage):
    r = Rig()
    crab_legs(r, 0.0, -3.0, 12.0, 3, 0.2, "barn", -0.5, -1.5, step=0.0, reach=4.0, lift=0.0, knee=1.0, rad=1.0)
    r.ell(0.0, -5.0, 15.0, 5.0, "barn", 0.0, bias=-0.15)
    for i, x in enumerate((-9, -4, 1, 6, 10)):
        anemone(r, x, -9.0 + abs(x) * 0.15, 0.5, ("pink", "orange", "sea")[i % 3], False, 0, 0.8 - stage * 0.2)
    if stage == 0: dust(r, 0, 0, 1, 1.8)
    return r.resolve()


def colossus_sheet(out):
    Co = colossus
    idle = [Co(bob=[0, -0.3, -0.5, -0.3][i], k=i) for i in range(4)]
    run = [Co(phase=i / 6.0, bob=[0, -0.5, -0.8, -0.5, 0, -0.3][i], k=i, lean=2) for i in range(6)]
    open_i = [Co(bob=[0, -0.3, -0.5, -0.3][i], k=i * 1.3, opened=True) for i in range(4)]
    open_r = [Co(phase=i / 6.0, bob=[0, -0.5, -0.8, -0.5, 0, -0.3][i], k=i * 1.3, lean=2, opened=True) for i in range(6)]
    # Hammer (7): rear the pincers up (0-1), HAMMER the floor (3: at (20, -2)), shake (4), lift (5-6)
    ham = [Co(hammer=0.5, lean=-3), Co(hammer=1.0, lean=-6, bob=-1.0),
           Co(hammer=0.4, lean=4, smear=[((18, -20), (21, -8), "barn", 2)]),
           Co(hammer=1.5, lean=6, extra=lambda r: [dust(r, 20, 0, 0, 1.6), star(r, 22, -2, 1)]),
           Co(hammer=1.5, lean=5, extra=lambda r: dust(r, 20, 0, 1, 1.8)), Co(hammer=0.3, lean=2), Co()]
    # Budding (7): the garden heaves (0-2), FLICKS two buds (4: from (0, -18)), settle (5-6)
    bud = [Co(bob=0.5, k=1), Co(bob=1.0, k=2, lean=-3), Co(bob=-1.0, k=3, lean=3, opened=True),
           Co(bob=-1.5, opened=True, k=4, flick=[(2.0, -22.0), (-4.0, -21.0)]),
           Co(bob=-0.5, k=5, flick=[(9.0, -26.0), (-1.0, -27.0)]), Co(k=6, flick=[(16.0, -26.0), (5.0, -29.0)]), Co(k=7)]
    d0 = Co(hurt=True, lean=-6, hammer=0.6)
    d1 = Co(hurt=True, lean=-12, bob=3.0)
    anims = [("Idle", idle, [0.22, 0.2, 0.22, 0.2]), ("Run", run, [0.11] * 6),
             ("IdleOpen", open_i, [0.18, 0.16, 0.18, 0.16]), ("RunOpen", open_r, [0.11] * 6),
             ("Hammer", ham, [0.14, 0.14, 0.06, 0.06, 0.12, 0.12, 0.14]),
             ("Budding", bud, [0.12, 0.12, 0.12, 0.08, 0.1, 0.12, 0.14])]
    anims += tail_anims(idle[0], [d0, d1, colossus_corpse(0), colossus_corpse(1)], [0.08, 0.12, 0.14, 0.4], Co(hurt=True, lean=-8))
    return sheet("BelColossus", anims, out)


# ================================================================== REEF CHAMPION
CHAMP_LEG = legend(k="shrimp:0", d="shrimp:1", s="shrimp:2", S="shrimp:3", L="shrimp:4", v="tent:3", V="tent:4", o="orange:3",
                   e="lure:3")


def champion(lean=0.0, bob=0.0, feet=((-3.0, 0.0), (3.0, 0.0)), c1=(7.0, -19.0), c2=(4.0, -18.0), glow=False, bow=0.0,
             hurt=False, smear=None, extra=None, tail_plant=False, k=0):
    """A peacock mantis shrimp standing upright like a prizefighter: a segmented green body, stalked violet eyes,
    two folded orange club arms (c1 near, c2 far), a fan tail."""
    r = Rig()
    hy = -10.0 + bob
    T = Xf(lean, (0.0, hy))
    # walking legs (thin) and the fan tail
    for i, (fx, fy) in enumerate(feet):
        hip = T(-1.0 + i * 2.5, hy)
        r.tube([hip, ((hip[0] + fx) / 2 + (1.5 if i else -1.5), (hip[1] + fy) / 2 - 1.0), (fx, fy)], [2.4, 2.0, 1.5], "coral",
               0.5 if i else -0.5, bias=-0.3 if i == 0 else 0.0)
        r.ell(fx + (1.0 if i else -0.5), fy - 0.8, 2.0, 1.0, "coral", 0.55 if i else -0.45, bias=-0.2)
    # the little walking legs tucked under its belly
    for j in range(3):
        a = T(1.5 + j * 1.2, hy - 4.0 - j * 2.5)
        b = (a[0] + 4.0, a[1] + 3.5)
        r.tube([a, b], [0.9, 0.6], "coral", 0.6 + j * 0.01, bias=-0.1)
    tx, ty = T(-4.0, hy + 2.0)
    fan = [(tx, ty), (tx - 11.0, ty + (4.0 if tail_plant else -1.0)), (tx - 13.0, ty + (7.0 if tail_plant else 4.0)),
           (tx - 9.0, ty + (9.0 if tail_plant else 9.0)), (tx - 1.0, ty + 6.0)]
    fan = [(x, min(y, 0.0)) for (x, y) in fan]
    r.poly(fan, "shrimp", -1.0, bias=0.1)
    for i in range(3): r.line(tx, ty, tx - 6.0 + i, ty + 3.0 + i * 1.5, "tent", -0.99, tone=3 if i % 2 else 2)
    r.dot(tx - 6.5, ty + 3.0, "lure", 3, -0.98); r.dot(tx - 5.0, ty + 5.5, "lure", 3, -0.98)    # tail eyespots
    # segmented body: an upright curve of plates
    segs = [T(-1.0, hy - 1.0), T(0.0, hy - 5.5), T(0.8, hy - 10.0), T(1.0 + bow * 2.0, hy - 14.5 + bow * 2.0)]
    for i, (sx, sy) in enumerate(segs):
        r.ell(sx, sy, 8.0 - i * 0.4, 3.9, "shrimp", 0.0 + i * 0.01, bias=0.05)
        r.line(sx - 5.0, sy + 2.2, sx + 5.0, sy + 2.2, "orange", 0.02 + i * 0.01, tone=2)
        for d in (-3, 0, 3): r.dot(sx + d, sy - 1.0, "shrimp", 4 if d < 0 else 3, 0.03 + i * 0.01)
    # the armoured carapace over its shoulders, spotted, with a red rim
    cx_, cy_ = T(0.5 + bow, hy - 12.5 + bow)
    r.ell(cx_, cy_, 8.5, 5.5, "shrimp", 0.15, bias=0.15)
    for d in range(-7, 8, 2): r.dot(cx_ + d, cy_ + 4.5 - abs(d) * 0.25, "coral", 3, 0.16)
    for (dx, dy) in ((-4, -2), (-1, -3), (3, -2), (5, 0), (-6, 1)): r.dot(cx_ + dx, cy_ + dy, "orange", 3, 0.17)
    # far club arm
    sh2 = T(-0.5, hy - 11.0)
    r.tube([sh2, ((sh2[0] + c2[0]) / 2 - 1.0, (sh2[1] + c2[1]) / 2 + 2.0), c2], [1.8, 1.6, 1.4], "coral", -0.8, bias=-0.3)
    r.ell(c2[0], c2[1], 3.8, 3.2, "orange", -0.75, bias=-0.25)
    # head: stalked violet eyes, antennae
    hx, hy2 = segs[-1][0] + 1.5, segs[-1][1] - 3.5
    r.ell(hx, hy2, 4.6, 3.4, "shrimp", 0.2)
    r.poly([(hx + 2.0, hy2 - 2.0), (hx + 7.0, hy2 - 0.5), (hx + 2.5, hy2 + 1.0)], "shrimp", 0.21, bias=0.2)   # rostrum
    for (ex, ey) in ((hx + 1.0, hy2 - 3.5 + bow * 2.0), (hx + 3.0, hy2 - 3.0 + bow * 2.0)):
        r.line(hx + 0.5, hy2 - 1.0, ex, ey + 1.0, "shrimp", 0.25, tone=3)
        r.ell(ex, ey, 1.2, 1.0, "tent", 0.3, flat=3)
        r.dot(ex, ey, "lure", 3, 0.31)
    r.polyline([(hx + 2.0, hy2 - 1.0), (hx + 6.0, hy2 - 5.0), (hx + 9.0, hy2 - 6.0)], "orange", 0.22, tones=[3, 2, 2])
    if hurt: r.dot(hx + 3.0, hy2 - 3.0, "tent", 4, 0.35)
    # near club arm: folded, the orange club like a fist
    sh = T(1.5, hy - 11.0)
    r.tube([sh, ((sh[0] + c1[0]) / 2, (sh[1] + c1[1]) / 2 + 2.5), c1], [2.2, 2.0, 1.7], "coral", 2.0)
    r.ell(c1[0], c1[1], 4.4, 3.8, "orange", 2.05)
    r.line(c1[0] - 3.0, c1[1] + 1.0, c1[0] + 3.0, c1[1] + 1.5, "coral", 2.06, tone=1)
    r.dot(c1[0] - 1.2, c1[1] - 1.4, "orange", 4, 2.07); r.dot(c1[0] - 0.2, c1[1] - 1.8, "orange", 4, 2.07)
    if glow:
        for (dx, dy) in ((-2, -2), (2, -2), (3, 0), (-3, 0), (0, -3)): r.dot(c1[0] + dx, c1[1] + dy, "spark", 3, 2.1)
    smear_lines(r, smear)
    if extra: extra(r)
    return r.resolve()


def champion_corpse(stage):
    r = Rig()
    for i in range(4): r.ell(-6.0 + i * 4.0, -2.5, 2.8, 2.2, "shrimp", 0.0 + i * 0.01, bias=-0.15)
    r.poly([(-8, -2), (-14, -5), (-15, -1), (-10, 0)], "shrimp", -0.5, bias=-0.1)
    r.ell(9.0, -2.0, 2.2, 1.8, "orange", 0.2, bias=-0.15)
    r.ell(7.0, -5.0, 1.0, 0.9, "tent", 0.3, flat=2)
    if stage == 0: dust(r, 0, 0, 1, 1.3)
    return r.resolve()


def champion_sheet(out):
    Ch = champion
    bounce = [0.0, -1.0, -1.5, -1.0]
    idle = [Ch(bob=bounce[i], c1=(7.0, -19.0 + bounce[i]), c2=(4.0, -18.0 + bounce[i]), k=i) for i in range(4)]
    run = []
    for i in range(6):
        s = math.sin(i / 6 * math.tau)
        run.append(Ch(lean=8, bob=-abs(s) * 1.5, feet=((-3.0 + 2.5 * s, -max(0, -s) * 2), (3.0 - 2.5 * s, -max(0, s) * 2)),
                      c1=(8.0, -17.0), c2=(5.0, -16.0)))
    # Uppercut (7): dip (0-1), DRIVE UP (3: club at (13, -22)), hang (4), back (5-6)
    upper = [Ch(lean=-4, bob=1.0, c1=(6.0, -12.0)), Ch(lean=-8, bob=1.5, c1=(5.0, -10.0)),
             Ch(lean=8, bob=-1.0, c1=(11.0, -15.0), smear=[((7, -10), (11, -14), "orange", 2)]),
             Ch(lean=12, bob=-2.0, c1=(13.0, -23.0), smear=[((11, -13), (13, -20), "orange", 2)], extra=lambda r: star(r, 15, -25, 1)),
             Ch(lean=8, bob=-1.0, c1=(12.0, -22.0)), Ch(lean=2, c1=(8.0, -18.0)), Ch()]
    # Haymaker (9): plant the tail (0-1), wind up, the clubs glowing (2-4), PUNCH straight out (5: club at (19, -13)),
    # follow-through (6), recover (7-8)
    hay = [Ch(tail_plant=True, lean=-4), Ch(tail_plant=True, lean=-10, c1=(3.0, -17.0), c2=(0.0, -16.0)),
           Ch(tail_plant=True, lean=-14, c1=(0.0, -16.0), c2=(-2.0, -15.0), glow=True),
           Ch(tail_plant=True, lean=-16, c1=(-1.0, -15.0), c2=(-3.0, -14.0), glow=True),
           Ch(tail_plant=True, lean=-16, c1=(-1.5, -15.0), c2=(-3.0, -14.0), glow=True),
           Ch(tail_plant=True, lean=14, c1=(19.0, -13.0), glow=True, smear=[((4, -14), (16, -13), "orange", 3), ((4, -12), (14, -12), "spark", 2)],
              extra=lambda r: star(r, 22, -13, 2)),
           Ch(tail_plant=True, lean=12, c1=(18.0, -13.0)), Ch(lean=4, c1=(11.0, -15.0)), Ch()]
    # Rest (4, loop): head bowed in its corner, the clubs lowered
    rest = [Ch(bow=1.0, c1=(6.0, -10.0 + 0.3 * (i % 2)), c2=(3.0, -9.5), bob=0.5 + 0.3 * (i % 2), lean=-4) for i in range(4)]
    d0 = Ch(hurt=True, lean=-14, c1=(6.0, -22.0))
    d1 = Ch(hurt=True, lean=-40, bob=4.0, c1=(4.0, -8.0))
    anims = [("Idle", idle, [0.12] * 4), ("Run", run, [0.08] * 6),
             ("Uppercut", upper, [0.12, 0.12, 0.06, 0.06, 0.12, 0.12, 0.14]),
             ("Haymaker", hay, [0.1, 0.1, 0.2, 0.2, 0.1, 0.05, 0.12, 0.12, 0.14]), ("Rest", rest, [0.25] * 4)]
    anims += tail_anims(idle[0], [d0, d1, champion_corpse(0), champion_corpse(1)], [0.08, 0.12, 0.14, 0.4],
                        Ch(hurt=True, lean=-16, c1=(6.0, -21.0)))
    return sheet("BelChampion", anims, out)


JOBS = [("BelGulperEel", gulper_sheet), ("BelSlimeHag", hag_sheet), ("BelKraken", kraken_sheet), ("BelBelltower", belltower_sheet),
        ("BelColossus", colossus_sheet), ("BelChampion", champion_sheet)]
SYNC = {
    "BelGulperEel": {"Scoop": [("SWEEP: the jaw at (16, -5); box 22 x 12 at (14, -5)", 3)],
                     "Unhinge": [("the jaw unhinges (0.6 s of tell)", 0), ("GULP: move 30 px; the mouth shuts on (18, -6)", 4)]},
    "BelSlimeHag": {"Bite": [("RASP: mouth at (19, -6); box at (16, -6)", 3)], "Knot": [("TWIST: second bite at (19, -6)", 3)],
                    "Spew": [("SPEW: three globs from (19, -9), released on the floor at (17, 0)", 4)]},
    "BelKraken": {"Slam": [("SLAM: the arm tips at (18, -2); box at (15, -3)", 3)], "Erupt": [("the arms are under: erupt", 3)]},
    "BelBelltower": {"Crush": [("CRUSH: claw tip at (24, -5); box at (19, -5)", 3)], "Peals": [("SLAM: the first peal from (16, 0)", 3)]},
    "BelColossus": {"Hammer": [("HAMMER: both pincers hit at (20, -2); box at (17, -4)", 3)],
                    "Budding": [("FLICK: two buds leave from (0, -22)", 4)]},
    "BelChampion": {"Uppercut": [("UPPERCUT: club at (13, -23); box at (12, -17)", 3)],
                    "Haymaker": [("wind-up: the clubs glow (2-4)", 2), ("PUNCH: club at (19, -13); box at (16, -13)", 5)]},
}
NOTES = {
    "BelGulperEel": "New (replaces BelStormEel). IdleFull / RunFull: the pouch swollen pale, the tail light flickering (Full "
                    "Pouch). Gag (6): an empty gulp.",
    "BelKraken": "IdleOpen / RunOpen: the mantle blanched (Arms Out: three arms up, the head open).",
    "BelColossus": "Idle / Run: the anemones shut into buds (dry floor). IdleOpen / RunOpen: open and waving (in brine).",
    "BelChampion": "Rest (4, loop): head bowed in its corner between rounds.",
}
