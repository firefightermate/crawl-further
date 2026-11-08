"""The custom silver / gold hero's portrait layers, painted like the origin portraits (origin_portraits.py).

hero_custom.py packs them into HcPortrait; HeroCustom.cs composites them at run time and swaps the marker colours
(254, group, k) for the player's picks. Each layer is painted with bust_painter on its own, using the origin portraits'
head, hair, hood and shoulder shapes, so a custom hero sits in the same picker as the origins without looking apart.

Marker materials and how the painter's tones land on their shades:
    m_main, m_trim, m_slot   L M S D        (light, base, shadow, deep)
    m_skin                   L l j J        (lit, base, shadow, deep); m_lip: lips (5) and blush (6)
    m_hair                   H d D
    m_bg                     frame edge fill fill
Every other material (steel, leather, wood, gold, eyes, glows) is drawn in its own colour.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
import bust_painter as BP  # noqa: E402
import origin_portraits as OP  # noqa: E402
from bust_painter import pillow, rows_mask, ell_mask  # noqa: E402
from anim import SprRGB  # noqa: E402

W, H, CX = OP.W, OP.H, OP.CX
GROUP = {"m_main": 1, "m_trim": 2, "m_skin": 3, "m_lip": 3, "m_hair": 4, "m_slot": 5, "m_bg": 6}
# preview ramps (never shipped: the markers replace them); they only let the painter light the shapes
_PREV = {"m_main": "p_rust", "m_trim": "p_ochre", "m_skin": "p_skin", "m_lip": "p_lip", "m_hair": "p_hair",
         "m_slot": "p_woad", "m_bg": "p_coal"}
BP.GLOSS.add("m_skin")
BP.DEEP.add("m_hair")


def setup():
    OP.install(OP.ramps_for("Wanderer", None))
    for k, v in _PREV.items():
        J.RAMPS[k] = J.RAMPS[v]


def marker(mat, t):
    g = GROUP[mat]
    if mat in ("m_main", "m_trim", "m_slot"):
        k = 1 if t >= 6 else 2 if t >= 4 else 3 if t >= 2 else 4
    elif mat == "m_skin":
        k = 1 if t >= 6 else 2 if t >= 4 else 3 if t >= 2 else 4
    elif mat == "m_lip":
        k = 6 if t >= 5 else 5
    elif mat == "m_hair":
        k = 1 if t >= 6 else 2 if t >= 3 else 3
    else:
        k = 1
    return (254, g, k)


def to_spr(r):
    """Resolve a layer: marker materials to their marker colours, the rest to their real colours."""
    t = r.resolve9(W, H)
    px = {}
    cache = {}
    for (x, y), (m, tone) in t.items():
        if not (0 <= x < W and 0 <= y < H): continue
        if m in GROUP:
            px[(x, y)] = marker(m, tone)
        else:
            if m not in cache: cache[m] = BP.ramp9(J.RAMPS[m])
            px[(x, y)] = cache[m][max(0, min(8, tone))]
    return SprRGB(px)


def layer(fn):
    setup()
    return [to_spr(fn(f)) for f in range(4)]


# ------------------------------------------------------------------------------------------------ background
def L_bg(f):
    px = {}
    for y in range(H):
        for x in range(W):
            if x in (0, W - 1) or y in (0, H - 1):
                px[(x, y)] = (254, 6, 1)
            else:
                d = (((x - 14) / 16.5) ** 2 + ((y - 9) / 14.5) ** 2) ** 0.5
                px[(x, y)] = (254, 6, 3) if d < 0.97 else (254, 6, 2)
    return px


def bg_layer():
    return [SprRGB(L_bg(f)) for f in range(4)]


# ------------------------------------------------------------------------------------------------ outfits
def collar(r, p, female=False):
    """The player's slot colour on the neckline, on every outfit."""
    lo, hi = (11, 17) if not female else (12, 16)
    for x in range(lo, hi + 1):
        y = 19 + p.by + (1 if x in (lo, hi) else 0)
        r.put(x, y, 1.5, "m_slot", 0.6 if x < CX else 0.2, r.part(True, 1.5), None)


def outfit_fn(oid, female=False):
    def fn(f):
        p, r = OP.Pose(f), BP.Bust()
        by = p.by
        rx = 14.5 if female else 15.5
        if oid == "Tunic":
            OP.shoulders(r, p, "m_main", rx=rx)
            # trim colour vest panels either side of the chest, a strap over one shoulder
            pillow(r, [(x, y + by) for y in range(20, 24) for x in range(8, 11)], "m_trim", 0.6, bias=0.2)
            pillow(r, [(x, y + by) for y in range(20, 24) for x in range(18, 21)], "m_trim", 0.6, bias=-0.2)
            r.tube([(21.5, 19.5 + by), (16.0, 25.0)], [0.9, 0.9], "p_lthr", 1.0)
        elif oid == "Robe":
            OP.shoulders(r, p, "m_main", rx=rx)
            # a cowl folded on the shoulders, a trim colour cord tied at the chest
            pillow(r, [(x, y + by) for y in range(19, 22) for x in list(range(3, 10)) + list(range(19, 26))
                       if (x - 14) ** 2 / 140.0 + (y - 21) ** 2 / 6.0 >= 0.6], "m_main", 0.5, bias=0.3)
            line = r.part(True, 1.2)
            for (x, y) in ((11, 20), (12, 21), (13, 21), (14, 21), (15, 21), (16, 20), (13, 22), (14, 23)):
                r.put(x, y + by, 1.2, "m_trim", 0.6 if x < 14 else 0.2, line, None)
        elif oid == "Jerkin":
            OP.shoulders(r, p, "m_main", rx=rx)
            # leather sleeves on the shoulder caps, laces down the front
            pillow(r, [(x, y + by) for y in range(19, 24) for x in range(0, 7)], "p_lthr", 0.6, bias=0.2)
            pillow(r, [(x, y + by) for y in range(19, 24) for x in range(22, 29)], "p_lthr", 0.6, bias=-0.1)
            lp = r.part(True, 1.2); r.hand.add(lp)
            for y in (21, 23):
                r.put(13, y + by, 1.2, "m_trim", 0.5, lp, 3); r.put(15, y + by, 1.2, "m_trim", 0.5, lp, 2)
        elif oid == "Tabard":
            OP.shoulders(r, p, "p_iron", rx=rx)
            mp = None
            for (x, y), v in list(r.b.items()):
                if (y % 2 == 0 or (x + y) % 4 == 1): v[2] -= 0.4
            # the tabard: a main colour panel with a trim colour edge
            pillow(r, [(x, y + by) for y in range(20, 24) for x in range(9, 20)], "m_main", 0.6, bias=0.15)
            tp = r.part(True, 0.7); r.hand.add(tp)
            for y in range(20, 24):
                r.put(9, y + by, 0.7, "m_trim", 0.5, tp, 3); r.put(19, y + by, 0.7, "m_trim", 0.5, tp, 1.5)
        elif oid == "Leathers":
            OP.shoulders(r, p, "p_lthr", rx=rx)
            # a trim colour shirt at the neck, straps and a buckle
            pillow(r, [(x, y + by) for y in range(19, 24) for x in range(11, 18)], "m_trim", 0.6, bias=0.2)
            r.tube([(6.0, 19.0 + by), (12.0, 25.0)], [0.9, 0.9], "p_lthr", 1.0, bias=-0.1)
            r.tube([(22.0, 19.0 + by), (16.0, 25.0)], [0.9, 0.9], "p_lthr", 1.0, bias=-0.2)
            pillow(r, ell_mask(8.5, 21.0 + by, 1.0, 0.9), "p_gold", 1.2, bias=0.3)
        elif oid == "Cloak":
            # dark clothes under a main colour cloak, its clasp at the throat
            OP.shoulders(r, p, "p_coal", rx=rx)
            pillow(r, [(x, y + by) for y in range(18, 24) for x in range(0, 29)
                       if (x - 14) ** 2 / 200.0 + (y - 28) ** 2 / 90.0 <= 1.0 and abs(x - 14) >= 4 + (y - 18) // 2],
                   "m_main", 0.6, bias=0.2)
            pillow(r, ell_mask(10.5, 20.5 + by, 1.3, 1.2), "p_gold", 1.2, bias=0.3)
            pillow(r, ell_mask(18.5, 20.5 + by, 1.2, 1.1), "p_gold", 1.2, bias=0.1)
        elif oid == "Mail":
            OP.shoulders(r, p, "p_iron", rx=rx)
            for (x, y), v in list(r.b.items()):
                if (y % 2 == 0 or (x + y) % 4 == 1): v[2] -= 0.4
            pillow(r, [(x, y + by) for y in range(21, 24) for x in list(range(0, 4)) + list(range(25, 29))],
                   "m_main", 0.6, bias=0.1)
        collar(r, p, female)
        return r
    return fn


# ------------------------------------------------------------------------------------------------ faces
def face_fn(fid):
    female = fid == "Soft"

    def fn(f):
        p, r = OP.Pose(f), BP.Bust()
        OP.head(r, p, skin="m_skin", lip="m_lip", brow="m_hair", female=female,
                mouth=fid != "Mask", nose=fid != "Mask")
        return r
    return fn


def facepiece_fn(fid):
    def fn(f):
        p, r = OP.Pose(f), BP.Bust()
        hy = p.hy
        d = OP.Face(r, p, 3.5)
        if fid == "Beard":
            pillow(r, [(x + CX, y + hy) for y, (a, b) in {14: (-6, -4), 15: (-6, -3), 16: (-6, -3), 17: (-5, 4),
                                                           18: (-4, 4), 19: (-3, 3), 20: (-2, 2)}.items()
                       for x in range(a, b + 1)] + [(x + CX, y + hy) for y in (14, 15, 16) for x in range(3, 6)],
                   "m_hair", 2.6, bias=0.2)
            for x in range(CX - 2, CX + 3):
                d(x, 15, "m_hair", 1)
        elif fid == "Moustache":
            for (x, t) in ((CX - 3, 1), (CX - 2, 0.5), (CX - 1, 0.5), (CX, 0.5), (CX + 1, 0.5), (CX + 2, 1)):
                d(x, 15, "m_hair", t)
            d(CX - 4, 16, "m_hair", 1.5); d(CX + 3, 16, "m_hair", 1)
        elif fid == "Scar":
            for (x, y, t) in ((CX - 4, 9, 1.5), (CX - 4, 10, 1), (CX - 3, 12, 1), (CX - 3, 13, 1.5), (CX - 2, 14, 1.5)):
                d(x, y, "m_skin", t)
            d(CX - 3, 11, "m_lip", 1)
        elif fid == "Eyepatch":
            # a band across the brow, the patch over the lit eye
            for x in range(CX - 7, CX + 7):
                y = 9 if x < CX - 3 else 10 if x < CX + 1 else 9
                d(x, y, "p_coal", 1 if x > CX else 2)
            for (x, y) in ((CX - 4, 10), (CX - 3, 10), (CX - 2, 10), (CX - 4, 11), (CX - 3, 11), (CX - 2, 11),
                           (CX - 3, 12)):
                d(x + 0.5, y, "p_coal", 2 if y == 10 else 1)
        elif fid == "Paint":
            for x in range(CX - 6, CX + 7):
                if x in (CX - 4, CX - 3, CX - 2, CX + 2, CX + 3, CX + 4) and not p.blink:
                    d(x + 0.5, 10, "m_trim", 1.5 if x < CX else 1)
                    continue
                d(x + 0.5, 10, "m_trim", 1.5 if x < CX else 1)
                d(x + 0.5, 11, "m_trim", 2 if x < CX else 1.5)
            for (x, y) in ((CX - 4, 13), (CX - 4, 14), (CX + 3, 13)):
                d(x + 0.5, y, "m_trim", 2)
        elif fid == "Specs":
            for ex in (CX - 3, CX + 3):
                for (x, y) in ((-1, 10), (0, 10), (1, 10), (-2, 11), (2, 11), (-1, 12), (0, 12), (1, 12)):
                    d(ex + x + 0.5, y, "p_gold", 3 if y == 10 else 2)
            d(CX + 0.5, 11, "p_gold", 2.5)
            if f == 2:
                d(CX - 3.5, 11, "p_shine", 3)
        elif fid == "Mask":
            pillow(r, [(x + CX, y + hy) for y, (a, b) in {12: (-6, 6), 13: (-7, 6), 14: (-7, 6), 15: (-6, 6),
                                                           16: (-6, 5), 17: (-5, 4), 18: (-4, 3), 19: (-3, 2)}.items()
                       for x in range(a, b + 1)], "m_trim", 3.6, bias=0.2)
            OP.line(r, [(CX + 1, 13 + hy), (CX + 1, 14 + hy), (CX - 3, 16 + hy), (CX - 2, 17 + hy)], "p_coal", 1, 3.7)
        return r
    return fn


# ------------------------------------------------------------------------------------------------ heads
SHORT = {0: (-4, 3), 1: (-6, 5), 2: (-7, 6), 3: (-8, 7), 4: (-8, 7), 5: (-8, 7), 6: (-8, 7), 7: (-8, -5),
         8: (-8, -6), 9: (-8, -7), 10: (-8, -7)}
SHORT_LOCKS = [(-4, 7, 2, -0.5), (-2, 7, 1, 0), (0, 7, 2, 0.5), (2, 7, 1, 0), (4, 7, 2, 0.6), (6, 7, 3, 0.3),
               (-7, 10, 2, 0)]
SHORT_STRANDS = [(-5, 2, 3), (-4, 3, 3), (-3, 4, 3), (-2, 2, 3), (-1, 3, 3), (1, 1, 3), (2, 2, 2.5), (3, 3, 2),
                 (-6, 5, 2.5), (-3, 1, 3.5), (-4, 5, 1), (-1, 5, 1), (2, 5, 1), (5, 4, 1), (0, 4, 1.5), (-7, 7, 2)]
SIDES = {7: (-8, -6), 8: (-8, -7), 9: (-8, -7), 10: (-8, -7)}


def head_fn(hid):
    def fn(f):
        p, r = OP.Pose(f), BP.Bust()
        hy = p.hy
        if hid == "Bare":
            OP.hair(r, p, SHORT, mat="m_hair", locks=SHORT_LOCKS, strands=SHORT_STRANDS)
        elif hid == "Long":
            # long hair falling behind both shoulders and over the near one
            pillow(r, [(x, y + hy if y < 18 else y + p.by) for y in range(6, 24) for x in list(range(CX - 9, CX - 6))
                       + list(range(CX + 6, CX + 9))], "m_hair", 3.9, bias=0.15)
            OP.hair(r, p, SHORT, mat="m_hair", locks=SHORT_LOCKS[:-1], strands=SHORT_STRANDS)
        elif hid == "Topknot":
            OP.hair(r, p, {1: (-5, 4), 2: (-7, 6), 3: (-7, 6), 4: (-8, 7), 5: (-8, 7), 6: (-8, -5), 7: (-8, -7),
                           8: (-8, -7)}, mat="m_hair", strands=[(-5, 3, 3), (-2, 2, 3), (1, 2, 2.5), (4, 3, 2)])
            pillow(r, ell_mask(CX + 0.5, 0.0 + hy, 2.4, 2.0), "m_hair", 4.4, bias=0.3)
            OP.line(r, [(CX - 1 + x, 2 + hy) for x in range(0, 4)], "m_trim", 2, 4.6)
        elif hid == "Mohawk":
            OP.hair(r, p, {0: (-2, 2), 1: (-2, 2), 2: (-2, 2), 3: (-2, 2), 4: (-2, 2), 5: (-2, 1)}, mat="m_hair",
                    strands=[(-1, 0, 3), (-1, 2, 3), (0, 4, 2.5)])
            sp = r.part(True, 4.2)
            for x in range(-2, 3):
                r.put(CX + x, -1 + hy - (x % 2), 4.2, "m_hair", 0.4, sp, None)
            stub = r.part(True, 3.5); r.hand.add(stub)
            for (x, y) in ((-6, 4), (-5, 6), (4, 5), (5, 3), (-7, 7), (6, 6)):
                r.put(CX + x, y + hy, 3.5, "m_hair", 0.5, stub, 1)
        elif hid == "Shaved":
            # a buzz cut: a thin cap of stubble hugging the scalp, the hairline crisp over the brow
            OP.hair(r, p, {1: (-4, 3), 2: (-6, 5), 3: (-7, 6), 4: (-7, 6), 5: (-7, 6), 6: (-7, -4), 7: (-7, -6)},
                    mat="m_hair", z=2.5, bias=-0.15)
        elif hid == "Hood":
            hood_cut(r, p, "m_main")
        elif hid == "Helm":
            helm(r, p)
        elif hid == "Horned":
            helm(r, p, nasal=False)
            for sx in (-1, 1):
                pts = [(CX + sx * (7 + k * 0.7), 4 - k * 1.3 + hy) for k in range(5)]
                r.tube(pts, [1.3, 1.1, 0.9, 0.7, 0.4], "p_bone", 5.6 if sx < 0 else 4.4)
        elif hid == "WideHat":
            OP.hair(r, p, SIDES, mat="m_hair", z=3.0, bias=0.2)
            pillow(r, [(x + CX, y + hy) for y, (a, b) in {0: (-4, 4), 1: (-5, 5), 2: (-6, 6), 3: (-6, 6), 4: (-6, 6)}.items()
                       for x in range(a, b + 1)], "m_main", 5, bias=0.3)
            pillow(r, [(x + CX, 4 + hy) for x in range(-6, 7)], "m_trim", 5.2, bias=0.2)
            pillow(r, [(x + CX, y + hy) for y, (a, b) in {5: (-10, 10), 6: (-13, 13), 7: (-14, -8), 8: (-14, -11)}.items()
                       for x in range(a, b + 1)] + [(x + CX, y + hy) for y, (a, b) in {7: (8, 14), 8: (11, 14)}.items()
                                                    for x in range(a, b + 1)], "m_main", 5.4, bias=0.15, vk=0.5)
            brim_shadow(r, p)
        elif hid == "Cap":
            OP.hair(r, p, SIDES, mat="m_hair", z=3.0, bias=0.2)
            pillow(r, [(x + CX, y + hy) for y, (a, b) in {2: (-5, 3), 3: (-7, 5), 4: (-8, 6), 5: (-8, 7), 6: (-8, 8)}.items()
                       for x in range(a, b + 1)], "m_main", 5, bias=0.3)
            pillow(r, [(x + CX, 7 + hy) for x in range(-8, 9)], "m_trim", 5.2, bias=0.2)
            # a feather sweeping back off the band
            for i, (x, y) in enumerate(((-7, 6), (-9, 5), (-10, 3), (-11, 1), (-11, 0))):
                pillow(r, [(CX + x, y + hy + (1 if f == 2 and i > 2 else 0)), (CX + x + 1, y + hy)], "m_trim", 5.3 + i * 0.01,
                       bias=0.3 - 0.1 * i)
        elif hid == "Wizard":
            OP.hair(r, p, SIDES, mat="m_hair", z=3.0, bias=0.2)
            tip = [-1, 0, 1, 0][f]
            pts = J.poly_px([(CX - 8, 7.5), (CX + 8, 7.5), (CX + 3 + tip, 1.5), (CX - 2 + tip, -0.5)])
            pillow(r, [(x, y + hy) for (x, y) in pts], "m_main", 5, bias=0.2)
            pillow(r, [(x + CX, y + hy) for y in (5, 6) for x in range(-7, 8)], "m_trim", 5.2, bias=0.2)
            pillow(r, [(x + CX, 7 + hy) for x in range(-11, 11)], "m_main", 5.4, bias=0.1, vk=0.4)
            star = r.part(True, 5.3); r.hand.add(star)
            r.put(CX - 1, 3 + hy, 5.3, "p_gold", 0.5, star, 4 if f == 1 else 3)
            brim_shadow(r, p)
        elif hid == "Bandana":
            OP.hair(r, p, SIDES, mat="m_hair", z=3.0, bias=0.2, locks=[(-8, 10, 3, -0.2)])
            pillow(r, [(x + CX, y + hy) for y, (a, b) in {1: (-5, 4), 2: (-7, 6), 3: (-8, 7), 4: (-8, 7), 5: (-8, 7),
                                                           6: (-8, 7), 7: (-8, 7)}.items() for x in range(a, b + 1)],
                   "m_trim", 5, bias=0.25)
            # the knot and its tails at the back
            pillow(r, ell_mask(CX - 9, 6.5 + hy, 1.4, 1.3), "m_trim", 5.2, bias=0.2)
            for i, (x, y) in enumerate(((-10, 8), (-11, 9), (-11, 10), (-12, 11))):
                pillow(r, [(CX + x - (1 if f == 2 and i > 1 else 0), y + hy)], "m_trim", 5.1, bias=0.1)
            dots = r.part(True, 5.3); r.hand.add(dots)
            for (x, y) in ((-5, 3), (-2, 2), (1, 3), (4, 4), (-4, 6), (2, 6)):
                r.put(CX + x, y + hy, 5.3, "m_main", 0.5, dots, 3)
        elif hid == "Circlet":
            OP.hair(r, p, SHORT, mat="m_hair", locks=SHORT_LOCKS, strands=SHORT_STRANDS)
            band = r.part(True, 5.0); r.hand.add(band)
            for x in range(-8, 8):
                r.put(CX + x, 6 + hy - (1 if abs(x) < 3 else 0), 5.0, "p_gold", 0.5, band, 3 if x < 0 else 2)
            gp = r.part(True, 5.1); r.hand.add(gp)
            r.put(CX, 4 + hy, 5.1, "m_trim", 0.5, gp, 3)
            if f == 1:
                OP.glint(r, CX, 4 + hy)
        return r
    return fn


def brim_shadow(r, p):
    d = OP.Face(r, p, 3.4)
    for x in range(CX - 6, CX + 7):
        d(x, 8, "m_skin", 1)


def helm(r, p, nasal=True):
    hy = p.hy
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {0: (-4, 3), 1: (-6, 5), 2: (-7, 6), 3: (-8, 7), 4: (-8, 7),
                                                   5: (-8, 7), 6: (-9, 8)}.items() for x in range(a, b + 1)],
           "p_steel", 5, bias=0.25, vk=1.1)
    pillow(r, [(x, 7 + hy) for x in range(CX - 9, CX + 9)], "p_iron", 5.2, bias=0.1)
    if nasal:
        n = r.part(False, 6)
        for y in range(7, 13):
            r.put(CX + 0.5, y + hy, 6, "p_iron", 0.6 if y < 10 else 0.3, n, None)
    OP.line(r, [(CX - 7, 7 + hy), (CX - 4, 7 + hy), (CX + 3, 7 + hy), (CX + 6, 7 + hy)], "p_steel", 4, 5.5)
    # cheek guards of mail
    mp = pillow(r, [(x, y + hy) for y in range(8, 17) for x in list(range(CX - 9, CX - 6)) + list(range(CX + 6, CX + 9))],
                "p_iron", 4.5, bias=0.1)
    for (x, y), v in list(r.b.items()):
        if v[3] == mp and (y % 2 == 0): v[2] -= 0.4


def hood_cut(r, p, mat):
    """The hood with its face opening cut out (the head layer sits on top of the face layer, so the hood's back can
    only show outside the head)."""
    hy = p.hy
    keep = []
    for y in range(0, 21):
        for x in range(CX - 10, CX + 10):
            outer = ((x - CX) / 9.6) ** 2 + ((y - 9.5) / 10.5) ** 2
            inner = ((x - CX - 0.5) / 5.6) ** 2 + ((y - 11.5) / 8.5) ** 2
            if outer <= 1.0 and inner > 1.0:
                keep.append((x, y + hy))
    pillow(r, keep, mat, 4.0, bias=0.2)
    d = OP.Face(r, p, 3.4)
    for x in range(CX - 5, CX + 6):
        d(x, 8, "m_skin", 1)


# ------------------------------------------------------------------------------------------------ weapons
def weapon_fn(fam):
    def fn(f):
        p, r = OP.Pose(f), BP.Bust()
        if fam == "Sword":
            r.tube([(23.4, 22), (24.6, 7.0)], [1.0, 0.9], "p_lthr", -1)
            r.tube([(21.2, 8.6), (27.6, 7.6)], [0.8, 0.8], "p_iron", -0.9)
            pillow(r, ell_mask(24.8, 4.6, 1.5, 1.4), "p_iron", -0.8, bias=0.2)
            if f == 1: OP.glint(r, 24, 4)
        elif fam == "Greatsword":
            r.tube([(22.6, 24), (24.6, 4.0)], [1.3, 1.1], "p_lthr", -1)
            r.tube([(19.6, 9.4), (28.6, 8.2)], [1.0, 1.0], "p_steel", -0.9)
            pillow(r, ell_mask(24.8, 2.0, 1.6, 1.5), "p_steel", -0.8, bias=0.2)
            if f == 2: OP.glint(r, 22, 9)
        elif fam == "Axe":
            r.tube([(22.6, 24.0), (25.0, 5.0)], [0.9, 0.9], "p_wood", -1)
            pillow(r, [(x, y) for y in range(2, 11) for x in range(25, 29) if abs(y - 6) <= (x - 23)], "p_steel", -0.9, bias=0.15)
            if f == 1: OP.glint(r, 27, 4)
        elif fam == "Club":
            r.tube([(23.0, 24.0), (24.4, 9.0)], [1.0, 1.3], "p_wood", -1)
            pillow(r, ell_mask(24.6, 5.6, 3.0, 4.2), "p_wood", -0.9, bias=0.15)
            stud = r.part(True, -0.8); r.hand.add(stud)
            for (x, y) in ((23, 3), (26, 4), (24, 6), (22, 7), (26, 8)):
                r.put(x, y, -0.8, "p_iron", 0.5, stud, 3 if x < 25 else 2)
        elif fam == "Dagger":
            r.tube([(22.5, 24.0), (22.5, 19.0)], [1.0, 1.0], "p_lthr", 6)
            r.tube([(20.6, 18.4), (24.4, 18.4)], [0.6, 0.6], "p_iron", 6.1)
            pillow(r, [(22, y) for y in range(10, 18)] + [(23, y) for y in range(11, 18)], "p_steel", 6.2, bias=0.3)
            pillow(r, [(20, 22), (21, 22), (21, 21), (20, 21), (24, 21), (24, 22), (23, 22)], "m_skin", 6.3, bias=0.0)
            if f == 0: OP.glint(r, 22, 12)
        elif fam == "Spear":
            r.tube([(23.0, 24.0), (25.0, 3.0)], [0.8, 0.8], "p_wood", -1)
            pillow(r, J.poly_px([(25.2, -2.0), (26.8, 2.0), (25.6, 5.0), (24.0, 2.6)]), "p_steel", -0.9, bias=0.2)
            if f == 3: OP.glint(r, 25, 0)
        elif fam == "Staff":
            r.tube([(24.8, 24.0), (24.2, 6.0)], [0.9, 0.8], "p_wood", -1)
            r.tube([(22.6, 6.6), (24.2, 4.8), (25.8, 6.6)], [0.6, 0.6, 0.6], "p_iron", -0.6)
            pillow(r, ell_mask(24.2, 2.6, 1.6, 1.8), "p_bone", -0.5, bias=0.2)
        elif fam == "Bow":
            r.tube([(24.0, 0.0), (26.4, 6.0), (26.8, 13.0), (26.0, 20.0), (24.4, 24.0)], [0.8, 1.0, 1.1, 1.0, 0.8], "p_wood", -1)
            OP.line(r, [(24, y) for y in range(1, 24)], "p_bone", 2.5, -0.9)
            r.tube([(25.4, 11.5), (27.4, 14.5)], [1.2, 1.2], "p_lthr", -0.8)
        elif fam == "Crossbow":
            r.tube([(24.0, 24.0), (25.0, 6.0)], [1.1, 1.1], "p_wood", -1)
            r.tube([(20.0, 4.6), (25.0, 3.4), (28.6, 4.6)], [0.7, 0.8, 0.7], "p_steel", -0.9)
            OP.line(r, [(21, 5), (22, 6), (23, 7), (27, 6), (26, 7)], "p_bone", 2, -0.95)
            if f == 2: OP.glint(r, 24, 3)
        elif fam == "Sling":
            sw = [0, 1, 0, -1][f]
            r.tube([(23.0, 4.0), (23.0 + sw * 0.6, 8.0), (23.0 + sw, 11.0)], [0.4, 0.4, 0.4], "p_rope", -0.9, thin=True)
            pillow(r, ell_mask(23.0 + sw, 12.5, 1.8, 1.5), "p_lthr", -0.8, bias=0.2)
            pillow(r, ell_mask(23.0 + sw, 12.2, 0.8, 0.7), "p_iron", -0.7, bias=0.3)
            pillow(r, ell_mask(23.0, 3.0, 1.4, 1.3), "m_skin", -0.6, bias=0.1)
        elif fam == "Knives":
            for i, x in enumerate((21, 24, 27)):
                y0 = 4 + i
                pillow(r, [(x, y) for y in range(y0, y0 + 5)], "p_steel", -0.9 + i * 0.01, bias=0.3)
                pillow(r, [(x, y) for y in range(y0 + 5, y0 + 8)], "p_lthr", -0.85 + i * 0.01, bias=0.1)
            r.tube([(19.0, 12.0), (28.0, 15.0)], [0.8, 0.8], "p_lthr", -0.8)
        return r
    return fn


# ------------------------------------------------------------------------------------------------ overlays
def L_glint(f):
    """Magic weapon: sparkles running over the weapon area."""
    pts = [[(22, 3), (25, 9)], [(24, 6), (21, 12)], [(23, 9), (26, 4)], [(25, 12), (22, 6)]][f]
    px = {}
    for (x, y) in pts:
        for (dx, dy) in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
            px[(x + dx, y + dy)] = (255, 255, 255) if (dx, dy) == (0, 0) else (186, 160, 236)
    return SprRGB(px)


def L_spell(f):
    """A spell mote circling the far shoulder: a rune in the trim colour, with sparks."""
    x, y = [(2, 9), (3, 8), (4, 9), (3, 10)][f]
    rows = [".kbk.", "kacak", "bcacb", "kbcdk", ".kbk."]
    m = {"k": (54, 40, 70), "a": (254, 2, 1), "b": (254, 2, 2), "d": (254, 2, 4), "c": (244, 236, 255)}
    px = {}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in m: px[(x + i, y + j)] = m[ch]
    for (sx, sy) in [[(1, 7), (7, 14)], [(7, 7), (2, 15)], [(8, 12), (1, 8)], [(2, 16), (8, 8)]][f]:
        px[(sx, sy)] = (244, 236, 255)
    return SprRGB(px)


def L_unknown(f):
    """Silver / gold slot portrait: a stranger whose face is still in shadow, a question mark glowing."""
    q = [".ύύύ.", "ύ...ύ", "...ύ.", "..ύ..", "..ύ..", ".....", "..ώ.."]
    m = {"ύ": (254, 7, 3), "ώ": (254, 7, 4)}
    px = {}
    dy = [0, 0, 1, 0][f]
    # shadow over the whole face
    for y in range(2, 21):
        for x in range(CX - 6, CX + 8):
            if ((x - CX - 0.5) / 5.6) ** 2 + ((y - 11.5) / 8.5) ** 2 <= 1.0:
                px[(x, y + dy)] = (24, 20, 26) if (x + y) % 2 else (34, 28, 34)
    for j, row in enumerate(q):
        for i, ch in enumerate(row):
            if ch in m: px[(CX - 2 + i, 8 + j + dy)] = m[ch]
    return SprRGB(px)
