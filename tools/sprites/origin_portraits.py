"""Hero-origin portraits (29x24, 4-frame Idle), painted close up like the game's own god portraits.

    python3 tools/sprites/origin_portraits.py      (hero_portraits.py runs it too)

Writes art/out_heroes/Hero<Origin>.png/.json/_preview.png (the canonical colours) and art/out_heroes/board_origins.png.
hero_slots.py draws the same portraits in each player slot's colours through frames(name, slot).

The game's god portraits fill the frame with a head: a three-quarter face lit from the top left, five clean tones a
material, two dozen colours, a flat dusky backdrop. These do the same with bust_painter: the head is one cushion-lit
shape (so the light follows its outline), hair, hats and hoods are cushions on top, and the face (brows, eyes, nose,
mouth) is pixelled by hand. Each origin names its team materials (TEAM): those ramps turn to the player's colour family
in the slot sets (hero_looks.slot_col, the same rule as the in-game body and the gear); skin, hair, steel, leather and
gold never change. The four Idle frames are posed redraws: breath, a prop catching the light, a glance, a blink.
"""
import colorsys
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
import bust_painter as BP  # noqa: E402
from bust_painter import pillow, rows_mask, ell_mask  # noqa: E402
import hero_looks as HL  # noqa: E402
import weapon_bubbles as WB  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "art", "out_heroes")
W, H = 29, 24
DURS = [0.2, 0.18, 0.2, 0.16]
ORDER = ["Wanderer", "Sellsword", "Huntress", "Hexblade", "Flagellant", "Pilgrim", "Gambler",
         "Reaver", "Cutpurse", "Arbalist", "Scholar"]

# ramps: ink, shadow, base, light, highlight. Skin and hair come from the god portraits' own colours.
BASE = {
    # skin and hair
    "p_skin":   ("4a2a24", "8b573c", "ba8251", "d39b67", "eabb86"),
    "p_pale":   ("4a3030", "8e6a5e", "c09a84", "dcbaa0", "f0d6bc"),     # the hexblade's bloodless skin
    "p_lip":    ("2a1012", "5a2424", "8a3c34", "b05a48", "c87a60"),
    "p_hair":   ("24160e", "4e3220", "74502e", "9a703e", "b88c54"),
    "p_dark":   ("140e0e", "2a1e1c", "3e2c28", "56403a", "6e544a"),     # near-black hair
    "p_ginger": ("2e1208", "6a2c12", "a04a1e", "c86a2c", "e0904a"),
    "p_white":  ("3e3a38", "77706a", "aaa49c", "d2ccc2", "eeeae2"),
    # cloth
    "p_rust":   ("301816", "5e2a22", "8a3e2c", "aa5638", "c8764c"),
    "p_green":  ("101a10", "243a22", "385430", "506e40", "6c8a54"),
    "p_violet": ("140c1e", "2c1a40", "44295e", "5e3c7c", "7a569a"),
    "p_white_c": ("3c3832", "7a7266", "aea492", "cec4b0", "e6dcc8"),
    "p_robe":   ("201410", "44301e", "664a2c", "86643c", "a68252"),
    "p_wine":   ("200a12", "4a1822", "722834", "923a42", "b05a58"),
    "p_coal":   ("100e10", "201c20", "322c30", "463e42", "5c5256"),
    "p_teal":   ("0c1a1a", "183634", "24504c", "386e66", "548c82"),
    "p_ochre":  ("2a1c0c", "5c4018", "8a6428", "ae8638", "cca85a"),
    "p_oxblood": ("1e0a0a", "461816", "6c2820", "8c3c2e", "aa5a44"),
    "p_navy":   ("0c1020", "1a2440", "28385e", "3c507c", "566c9a"),
    "p_pelt":   ("261e16", "52443a", "7e6e5c", "a49480", "c4b6a0"),
    "p_felt":   ("161210", "2e2620", "463a30", "5e5040", "7a6a56"),
    "p_red":    ("2a0a0a", "5e1614", "8c2420", "ae3a2c", "c85a44"),
    "p_woad":   ("0e1630", "1e2e5e", "2e4688", "4664aa", "6a86c4"),
    "p_plume":  ("2a0a0a", "5e1614", "922a22", "b8402e", "d06648"),
    "p_cloth":  ("1c1814", "3a322a", "5a4e40", "7a6c5a", "988a74"),    # undyed cloth, sackcloth, scarves
    # gear
    "p_steel":  ("181a22", "3c404c", "666c7a", "9aa0ae", "d4d8e0"),
    "p_iron":   ("16141a", "34323a", "54505a", "7a7680", "a8a4ac"),
    "p_lthr":   ("1e1210", "3e2a20", "5a3e2c", "765438", "94704a"),
    "p_wood":   ("201410", "46301e", "6a4a2c", "8c663c", "aa8250"),
    "p_gold":   ("2a1808", "6a4414", "a8762a", "d4a646", "f2da8a"),
    "p_rope":   ("2a2010", "5a4828", "8a7448", "b09868", "ccb88a"),
    "p_bone":   ("38302a", "786a58", "aa9a80", "cec0a2", "eae0c8"),
    # emissive
    "p_eyew":   ("6a5e54", "a49a8e", "dcd2c2", "f0e8dc", "ffffff"),
    "p_black":  ("120c0c", "241818", "382626", "4c3434", "604444"),
    "p_rune":   ("3a1a5a", "8a3ab8", "c070f0", "f0c0ff", "ffffff"),
    "p_flame":  ("5a1a0a", "b8401a", "f07a24", "ffc04a", "fff0b0"),
    "p_blood":  ("3a0608", "6e0e12", "a01c1a", "c43a2c", "e06048"),
    "p_shine":  ("8a8a90", "c8ccd4", "e8ecf2", "f6f8fc", "ffffff"),
}
EMIT = {"p_eyew", "p_black", "p_rune", "p_flame", "p_blood", "p_shine"}
SHINY = {"p_steel", "p_gold", "p_iron", "p_bone"}
UNTAMED = {"p_skin", "p_pale", "p_lip", "p_hair", "p_dark", "p_ginger", "p_white"}
BP.GLOSS.update({"p_skin", "p_pale"})
BP.DEEP.update({"p_hair", "p_dark", "p_ginger", "p_coal", "p_felt"})

# origin -> [(materials that take the player colour, canonical slot)]; -2: tinted in every slot (Wanderer: the
# vanilla player ramps' tunic colours)
TEAM = {
    "Wanderer":   [(["p_rust"], -2)],
    "Sellsword":  [(["p_rust"], 1)],
    "Huntress":   [(["p_green"], 2)],
    "Hexblade":   [(["p_violet", "p_rune"], 0)],
    "Flagellant": [(["p_rope"], 3)],
    "Pilgrim":    [(["p_robe"], 3), (["p_plume"], 3)],
    "Gambler":    [(["p_wine", "p_plume"], 1)],
    "Reaver":     [(["p_woad"], 0), (["p_pelt"], 3)],
    "Cutpurse":   [(["p_teal"], 0)],
    "Arbalist":   [(["p_oxblood"], 1)],
    "Scholar":    [(["p_navy"], 0)],
}
# backdrop (frame, edge, fill): the god portraits' dusky plum, nudged toward each origin's colour
BG = {
    "Wanderer":   ("1c1619", "3e3134", "4d3c3f"),
    "Sellsword":  ("191a1e", "373840", "45474f"),
    "Huntress":   ("161a15", "33392f", "414a3c"),
    "Hexblade":   ("191420", "382d44", "463854"),
    "Flagellant": ("1e1416", "432f30", "543a3a"),
    "Pilgrim":    ("1a1a20", "3e3f4a", "50525e"),
    "Gambler":    ("1d1814", "41362c", "514436"),
    "Reaver":     ("1e1714", "43352d", "544237"),
    "Cutpurse":   ("141a1b", "2e3a3b", "3b4a4a"),
    "Arbalist":   ("1d1914", "40372b", "504536"),
    "Scholar":    ("15172a", "30344c", "3e425e"),
}
# the tunic colour of the vanilla hero, read from each player's ramp (hero_looks): the Wanderer wears it
WANDERER_SRC = (203, 76, 43)
BG_TINT_MIN = 0.12


def _h(s):
    return J._h(s)


def hls(c):
    return colorsys.rgb_to_hls(*[v / 255.0 for v in c[:3]])


def rgb(h, l, s):
    return tuple(max(0, min(255, int(round(v * 255)))) for v in colorsys.hls_to_rgb(h, l, s))


# ------------------------------------------------------------------ colours per slot
def ramps_for(name, slot):
    """Material ramps for origin `name` in player slot 0-3 (None = the canonical colours). Cloth and gear stay inside
    Crawl's muted range (weapon_bubbles.tame); skin and hair keep the god portraits' warmth; glows are left alone."""
    out = {}
    for k, v in BASE.items():
        if k in EMIT or k in UNTAMED:
            out[k] = [_h(c) for c in v]
        else:
            out[k] = [WB.tame(_h(c), 0.40, 0.70) for c in v]
    if slot is None:
        return out
    for mats, canon in TEAM.get(name, []):
        for m in mats:
            if canon == -2:
                out[m] = wanderer_ramp(out[m], slot)
            else:
                out[m] = [HL.slot_col(c, slot, canon) for c in out[m]]
    return out


def wanderer_ramp(ramp, slot):
    pr = HL.load_ramp(HL.RAMPS[HL.SLOT_NAMES[slot]])
    t = pr[HL.slot(WANDERER_SRC)]
    if t == HL.PINK: t = WANDERER_SRC
    h, l, s = hls(t)
    return [rgb(h, hls(c)[1], max(s * 0.9, 0.12)) for c in ramp]


def bg_for(name, slot):
    """The backdrop tones: canonical, or turned to the slot hue so the frame reads in the player colour."""
    base = [_h(c) for c in BG[name]]
    if slot is None:
        return base
    canon = TEAM[name][0][1]
    if slot == canon:
        return base
    return [rgb(HL.SLOT_HUE[slot] / 360.0, hls(c)[1], max(hls(c)[2] * 0.8, BG_TINT_MIN)) for c in base]


def install(ramps):
    J.RAMPS.update(ramps)
    J.EMISSIVE.update(EMIT)
    J.SHINY.update(SHINY)


# ------------------------------------------------------------------ backdrop
def background(tones):
    frame, edge, fill = tones[:3]
    im = Image.new("RGBA", (W, H), frame + (255,))
    p = im.load()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            d = (((x - 14) / 16.5) ** 2 + ((y - 9) / 14.5) ** 2) ** 0.5
            p[x, y] = (fill if d < 0.97 else edge) + (255,)
    return im


def compose(r, tones):
    t = r.resolve9(W, H)
    im = background(tones)
    return BP.paint({k: v for k, v in t.items() if 1 <= k[0] < W - 1 and 1 <= k[1] < H - 1}, J.RAMPS, im, W, H)


# ------------------------------------------------------------------ pose and the head
class Pose:
    """Per frame: breath lifts the shoulders, the head dips once, the eyes glance and blink."""

    def __init__(self, f):
        self.f = f
        self.breath = [0.0, 0.5, 1.0, 0.5][f]
        self.by = int(round(self.breath * 0.6))
        self.hy = [0, 0, 1, 0][f]
        self.blink = f == 3
        self.look = [0, 0, 1, 0][f]
        self.sway = [0, 1, 1, 0][f]


CX = 14
# half-width of the head per row (the shadow side is cut to 0.92 of it: a slight three-quarter turn)
HEAD_M = {2: 3.5, 3: 5.2, 4: 6.2, 5: 6.7, 6: 7.0, 7: 7.1, 8: 7.1, 9: 7.0, 10: 6.9, 11: 6.8, 12: 6.6, 13: 6.3,
          14: 6.0, 15: 5.6, 16: 5.0, 17: 4.3, 18: 3.4, 19: 2.2}
HEAD_F = {2: 3.4, 3: 5.0, 4: 6.0, 5: 6.5, 6: 6.7, 7: 6.8, 8: 6.8, 9: 6.7, 10: 6.6, 11: 6.4, 12: 6.2, 13: 5.8,
          14: 5.4, 15: 4.9, 16: 4.3, 17: 3.6, 18: 2.6}


class Face:
    """Hand-placed face pixels on one part in front of the head."""

    def __init__(self, r, p, z=3.0):
        self.r, self.p, self.z = r, p, z
        self.part = r.part(True, z)
        r.hand.add(self.part)

    def __call__(self, x, y, m, t):
        self.r.put(x, y + self.p.hy, self.z, m, 0.5, self.part, t)


def head(r, p, skin="p_skin", lip="p_lip", brow="p_hair", female=False, eyes="plain", beard=None, age=0, neck=True,
         ears=True, mouth=True, nose=True):
    """The head, neck and features. eyes: plain / glow (lit from inside, p_rune) / none (hidden by a hood's shadow).
    beard: a hair material for stubble on the jaw. age: 1 adds lines under the eyes and beside the mouth."""
    hy = p.hy
    if neck:
        pillow(r, rows_mask({y: (CX - 3, CX + 2) for y in range(16, 23)}, hy), skin, 0.5, bias=-0.5)
    tab = HEAD_F if female else HEAD_M
    pts = [(x, y + hy) for y, w in tab.items() for x in range(int(round(CX - w)), int(round(CX + w * 0.92)) + 1)]
    pillow(r, pts, skin, 2.0, bias=0.12, vk=0.75)
    if ears:
        pillow(r, ell_mask(CX - 7.1, 11.0 + hy, 1.3, 1.9), skin, 1.9, bias=0.0)
    ex = CX + 0.5
    d = Face(r, p)
    # brows
    if female:
        for x, t in ((ex - 4, 1), (ex - 3, 1), (ex - 2, 1.5)): d(x, 9, brow, t)
        for x, t in ((ex + 2, 1.5), (ex + 3, 1)): d(x, 9, brow, t)
    else:
        for x, t in ((ex - 5, 1), (ex - 4, 0.5), (ex - 3, 0.5), (ex - 2, 1)): d(x, 9, brow, t)
        for x, t in ((ex + 2, 1), (ex + 3, 0.5), (ex + 4, 0.5)): d(x, 9, brow, t)
    lk = 1 if p.look else 0
    if eyes == "glow":
        for x in (ex - 4, ex - 3, ex - 2, ex + 2, ex + 3, ex + 4): d(x, 10, skin, 0.5)
        if not p.blink:
            d(ex - 3 + lk, 11, "p_rune", 4); d(ex - 4 + lk, 11, "p_rune", 2.5); d(ex - 2 + lk, 11, "p_rune", 2)
            d(ex + 3 + lk, 11, "p_rune", 3.5); d(ex + 2 + lk, 11, "p_rune", 2); d(ex + 4, 11, skin, 0.5)
        else:
            for x in (ex - 4, ex - 3, ex - 2, ex + 2, ex + 3, ex + 4): d(x, 11, skin, 0.5)
    elif eyes == "plain":
        if p.blink:
            for x in (ex - 4, ex - 3, ex - 2): d(x, 11, skin, 1)
            for x in (ex + 2, ex + 3, ex + 4): d(x, 11, skin, 0.5)
        else:
            for x in (ex - 4, ex - 3, ex - 2): d(x, 10, skin, 1.5)
            for x in (ex + 2, ex + 3, ex + 4): d(x, 10, skin, 1)
            d(ex - 4, 11, "p_eyew", 2); d(ex - 3, 11, "p_eyew", 2); d(ex - 2, 11, "p_eyew", 1.5)
            d(ex - 3 + lk, 11, "p_black", 0)
            d(ex + 2, 11, "p_eyew", 1.5); d(ex + 3, 11, "p_eyew", 1.5); d(ex + 4, 11, skin, 1)
            d(ex + 3 + lk, 11, "p_black", 0)
            if female:
                d(ex - 5, 10, "p_black", 1); d(ex + 4, 10, "p_black", 1)
    if eyes != "none":
        d(ex - 5, 11, skin, 2); d(ex - 1, 11, skin, 2.5)
    if nose:
        d(ex, 11, skin, 3.5); d(ex, 12, skin, 3.5); d(ex, 13, skin, 3)
        d(ex + 1, 12, skin, 1.5); d(ex + 1, 13, skin, 1); d(ex + 1, 14, skin, 1)
        d(ex - 1, 14, skin, 1.5); d(ex, 14, skin, 0.5)
        d(ex - 4, 13, skin, 3.5)
    if age:
        d(ex - 4, 12, skin, 1.5); d(ex + 3, 12, skin, 1); d(ex - 2, 15, skin, 1.5); d(ex + 2, 15, skin, 1)
    if beard:
        bp = r.part(True, 2.5)
        # stubble: a scatter along the jaw line and the chin, clear of the mouth
        for y in range(16, 20):
            w = tab.get(y, 0)
            for x in range(int(round(CX - w)), int(round(CX + w * 0.92)) + 1):
                edge = x <= CX - w + 1.5 or x >= CX + w * 0.92 - 1.5 or y >= 18
                if edge and (x * 3 + y) % 4 == 0 and not (ex - 2 <= x <= ex + 1 and y <= 17):
                    r.put(x, y + hy, 2.5, beard, -0.2 if x > CX else 0.3, bp, None)
    if mouth:
        if female:
            d(ex - 2, 16, lip, 1.5); d(ex - 1, 16, lip, 0.5); d(ex, 16, lip, 0.5); d(ex + 1, 16, lip, 1.5)
            d(ex - 1, 17, lip, 3); d(ex, 17, lip, 2.5)
        else:
            # a closed mouth: the line between the lips, the lower lip catching a little light
            for x, t in ((ex - 2, 1), (ex - 1, 1), (ex, 1), (ex + 1, 1.5)): d(x, 16, lip, t)
            d(ex - 1, 17, lip, 3); d(ex, 17, skin, 2)
            d(ex - 1, 18, skin, 2)
    return d


def hair(r, p, spec, mat="p_hair", z=4.0, bias=0.25, locks=(), strands=(), dy=0):
    """A hair mass (row spans relative to CX), locks falling from it ((x, y, length, lean)), hand-placed strands
    ((x, y, tone))."""
    hy = p.hy + dy
    pillow(r, [(x + CX, y + hy) for y, (a, b) in spec.items() for x in range(a, b + 1)], mat, z, bias=bias, vk=0.9)
    for i, (x, y, n, lean) in enumerate(locks):
        lp = r.part(True, z + 0.1)
        for k in range(n):
            r.put(CX + x + int(round(lean * k)), y + k + hy, z + 0.1, mat, 0.3 - 0.35 * k, lp, None)
    if strands:
        sp = r.part(True, z + 0.3); r.hand.add(sp)
        for (x, y, t) in strands:
            r.put(CX + x, y + hy, z + 0.3, mat, 0.5, sp, t)


def shoulders(r, p, mat, z=0.0, rx=15.5, top=19.5, bias=0.1):
    return pillow(r, ell_mask(CX, top + 8.6 + p.by, rx, 8.6), mat, z, bias=bias)


def glint(r, x, y, size=1, z=9.0):
    gp = r.part(True, z)
    r.put(x, y, z, "p_shine", 0.5, gp, 4)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))[:2 * size + 2]:
        r.put(x + dx, y + dy, z, "p_shine", 0.5, gp, 2.5)


def line(r, pts, mat, tone, z):
    lp = r.part(True, z); r.hand.add(lp)
    for (x, y) in pts:
        r.put(x, y, z, mat, 0.5, lp, tone)


# ------------------------------------------------------------------ origins
def wanderer(f):
    """The plain hero: a brown mop of hair, the player's own tunic, a baldric and a sword hilt over the shoulder."""
    p, r = Pose(f), BP.Bust()
    by = p.by
    # sword over the right shoulder: grip, cross-guard, pommel
    r.tube([(23.4, 22), (24.6, 7.0)], [1.0, 0.9], "p_lthr", -1)
    r.tube([(21.2, 8.6), (27.6, 7.6)], [0.8, 0.8], "p_iron", -0.9)
    pillow(r, ell_mask(24.8, 4.6, 1.5, 1.4), "p_iron", -0.8, bias=0.2)
    shoulders(r, p, "p_rust")
    pillow(r, [(x, y + by) for y in range(20, 24) for x in range(11 + (y - 20), 18 - (y - 20))], "p_skin", 0.6, bias=-0.35)
    r.tube([(21.5, 19.5 + by), (6.0, 25.0)], [1.0, 1.0], "p_lthr", 1.0)
    pillow(r, ell_mask(16.5, 21.6 + by, 1.2, 1.0), "p_gold", 1.2, bias=0.3)
    head(r, p)
    hair(r, p, {0: (-4, 3), 1: (-6, 5), 2: (-7, 6), 3: (-8, 7), 4: (-8, 7), 5: (-8, 7), 6: (-8, 7), 7: (-8, -5),
                8: (-8, -6), 9: (-8, -7), 10: (-8, -7)},
         locks=[(-4, 7, 2, -0.5), (-2, 7, 1, 0), (0, 7, 2, 0.5), (2, 7, 1, 0), (4, 7, 2, 0.6), (6, 7, 3, 0.3), (-7, 10, 2, 0)],
         strands=[(-5, 2, 3), (-4, 3, 3), (-3, 4, 3), (-2, 2, 3), (-1, 3, 3), (1, 1, 3), (2, 2, 2.5), (3, 3, 2),
                  (-6, 5, 2.5), (-3, 1, 3.5), (-4, 5, 1), (-1, 5, 1), (2, 5, 1), (5, 4, 1), (0, 4, 1.5), (-7, 7, 2)])
    if f == 1:
        glint(r, 24, 4)
    return r


def sellsword(f):
    """A hired blade: an iron half-helm with a nasal and rivets, a mail coif round the face, a scar, a rust tunic."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    # greatsword hilt over the far shoulder
    r.tube([(4.6, 22), (5.6, 4.0)], [1.0, 0.9], "p_lthr", -1)
    r.tube([(1.6, 9.0), (9.0, 8.2)], [0.8, 0.8], "p_iron", -0.9)
    pillow(r, ell_mask(5.4, 2.4, 1.5, 1.3), "p_iron", -0.8, bias=0.2)
    shoulders(r, p, "p_rust")
    # mail: a mantle on the shoulders and a coif round the face, links as a checker of light
    mail = [(x, y + by) for y in range(18, 24) for x in range(4, 25) if (x - 14) ** 2 / 110.0 + (y - 24) ** 2 / 30.0 <= 1.0]
    mail += [(x, y + hy) for y in range(5, 19) for x in list(range(CX - 9, CX - 5)) + list(range(CX + 5, CX + 9))]
    mp = pillow(r, mail, "p_iron", 1.0, bias=0.15)
    head(r, p, beard="p_hair", ears=False)
    for (x, y), v in list(r.b.items()):
        if v[3] == mp and (y % 2 == 0 or (x + y) % 4 == 1):
            v[2] -= 0.4
    # a scar down the lit cheek
    d = Face(r, p, 3.2)
    for (x, y, t) in ((CX - 4, 12, 1.5), (CX - 3, 13, 1), (CX - 3, 14, 1.5), (CX - 2, 15, 1.5)):
        d(x, y, "p_skin", t)
    # helm: an iron cap low over the brow, a riveted band, the nasal down the nose
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {0: (-4, 3), 1: (-6, 5), 2: (-7, 6), 3: (-8, 7), 4: (-8, 7),
                                                     5: (-8, 7), 6: (-9, 8)}.items() for x in range(a, b + 1)],
           "p_steel", 5, bias=0.25, vk=1.1)
    band = [(x, 7 + hy) for x in range(CX - 9, CX + 9)]
    pillow(r, band, "p_iron", 5.2, bias=0.1)
    nasal = r.part(False, 6)
    for y in range(7, 13):
        r.put(CX + 0.5, y + hy, 6, "p_iron", 0.6 if y < 10 else 0.3, nasal, None)
    line(r, [(CX - 7, 7 + hy), (CX - 4, 7 + hy), (CX + 3, 7 + hy), (CX + 6, 7 + hy)], "p_steel", 4, 5.5)
    if f == 1:
        glint(r, CX - 4, 2 + hy)
    elif f == 2:
        glint(r, 5, 2)
    return r


def hood(r, p, mat, front=True, peak=None, depth=0.0, top=0, open_w=6, low=19, shade=True):
    """A hood: the back of it round the head and down to the shoulders, a thick rim round the face."""
    hy = p.hy
    pts = [(x, y + hy) for y in range(top, low + 1) for x in range(CX - 10, CX + 10)
           if ((x - CX) / 9.6) ** 2 + ((y - 9.5) / 10.5) ** 2 <= 1.0]
    if peak:
        pts += [(x, y + hy) for (x, y) in J.poly_px(peak)]
    pillow(r, pts, mat, 0.8, bias=0.1)
    if front:
        rim = []
        for y in range(top + 2, low + 1):
            for x in range(CX - 10, CX + 10):
                inner = ((x - CX - 0.5) / open_w) ** 2 + ((y - 11.5) / 8.5) ** 2
                outer = ((x - CX) / 9.6) ** 2 + ((y - 9.5) / 10.5) ** 2
                if inner > 1.0 and outer <= 1.0 and y >= top + 2:
                    rim.append((x, y + hy))
        pillow(r, rim, mat, 4.0, bias=0.2)


def huntress(f):
    """A forest hunter: a green hood framing her face, a ginger braid, freckles, a quiver and her bow stave."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    # bow stave on the right, string taut
    r.tube([(24.0, 0.0), (26.4, 6.0), (26.8, 13.0), (26.0, 20.0), (24.4, 24.0)], [0.8, 1.0, 1.1, 1.0, 0.8], "p_wood", -1)
    line(r, [(24, y) for y in range(1, 24)], "p_bone", 2.5, -0.9)
    r.tube([(25.4, 11.5), (27.4, 14.5)], [1.2, 1.2], "p_lthr", -0.8)
    # quiver behind the left shoulder, fletching showing
    r.tube([(3.6, 23.0), (5.6, 8.0)], [2.0, 1.8], "p_lthr", -1)
    for i, (x, y) in enumerate(((3.4, 4.6), (5.6, 3.4), (7.4, 5.0))):
        col = "p_plume" if i % 2 == 0 else "p_white_c"
        pillow(r, [(int(x) + dx, int(y) + dy - (1 if f == 2 and i == 1 else 0)) for dx in (-1, 0, 1) for dy in (0, 1, 2) if abs(dx) + dy < 3],
               col, -0.6, bias=0.2)
    shoulders(r, p, "p_green")
    pillow(r, [(x, y + by) for y in range(19, 24) for x in range(11, 19)], "p_rust", 0.5, bias=0.0)
    r.tube([(7.0, 19.0 + by), (20.0, 25.0)], [0.9, 0.9], "p_lthr", 1.0)
    hood(r, p, "p_green", top=0, open_w=5.6)
    d = head(r, p, female=True, brow="p_ginger", ears=False)
    # hair showing under the hood, swept to one side
    hair(r, p, {4: (-5, 4), 5: (-6, 5), 6: (-6, -1), 7: (-6, -3), 8: (-6, -5)}, mat="p_ginger", z=3.5, bias=0.3,
         locks=[(-3, 7, 1, 0), (5, 6, 3, 0.2)], strands=[(-4, 5, 3), (-2, 5, 3), (0, 5, 2.5), (2, 5, 2), (-5, 7, 1.5)])
    # freckles
    for (x, y) in ((CX - 3, 13), (CX - 5, 13), (CX - 4, 14), (CX + 3, 13), (CX + 2, 14)):
        d(x, y, "p_skin", 1.5)
    # her braid out of the hood, over her shoulder
    for i, y in enumerate(range(15, 23)):
        x = CX + 7 + (1 if y > 18 else 0)
        pillow(r, [(x, y + hy if y < 19 else y + by), (x + 1, y + hy if y < 19 else y + by)], "p_ginger", 4.2, bias=0.3 - 0.4 * (i % 2))
    pillow(r, ell_mask(CX + 8.5, 22.6 + by, 1.1, 0.8), "p_lthr", 4.3)
    if f == 1:
        glint(r, 26, 4)
    return r


def hexblade(f):
    """A cursed swordmage: a deep violet cowl with its peak trailing, eyes lit violet in its shadow, a hex sigil on
    her cheek, the crystal of her staff glowing beside her."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    # staff and crystal on the right
    r.tube([(24.8, 24.0), (24.2, 7.0)], [0.9, 0.8], "p_wood", -1)
    r.tube([(22.6, 7.4), (24.2, 5.6), (25.8, 7.4)], [0.6, 0.6, 0.6], "p_iron", -0.6)
    fl = [2.6, 2.9, 3.2, 2.8][f]
    gp = r.part(True, -0.4)
    for y in range(-1, 7):
        for x in range(20, 29):
            dd = math.hypot((x - 24.2) * 1.4, (y - 3.0) / fl * 2.6)
            if dd < 3.0:
                r.put(x, y, -0.4, "p_rune", 0.5, gp, 4 if dd < 0.9 else 3 if dd < 1.8 else 2)
    shoulders(r, p, "p_violet")
    # a black tunic down the front, a silver clasp with a violet stone
    pillow(r, [(x, y + by) for y in range(19, 24) for x in range(12 - (y - 19) // 2, 17 + (y - 19) // 2)], "p_coal", 0.6)
    pillow(r, ell_mask(14.3, 20.6 + by, 1.4, 1.2), "p_steel", 1.2, bias=0.2)
    line(r, [(14, 20 + by)], "p_rune", 4 if f % 2 == 0 else 3, 1.4)
    hood(r, p, "p_violet", top=0, open_w=5.4,
         peak=[(CX - 6.0, 2.0), (CX - 12.0, -3.0), (CX - 2.0, 0.0)])
    d = head(r, p, skin="p_pale", female=True, brow="p_coal", eyes="glow", ears=False)
    # the cowl's shadow over the brow and down the far cheek
    for x in range(CX - 5, CX + 6):
        d(x, 8, "p_pale", 0.5); d(x, 9, "p_pale", 1 if x < CX + 3 else 0.5)
    for y in range(10, 15):
        d(CX + 5, y, "p_pale", 1); d(CX + 4, y, "p_pale", 1.5) if y > 11 else None
    # a hex sigil on the lit cheek
    for (x, y) in ((CX - 4, 13), (CX - 5, 14), (CX - 3, 14), (CX - 4, 15)):
        d(x, y, "p_rune", 2 + (f % 2))
    # dark hair falling from the cowl
    hair(r, p, {5: (-5, 5), 6: (-6, 5), 7: (-6, -2), 8: (-6, -4), 9: (-6, -5)}, mat="p_dark", z=3.5, bias=0.4,
         locks=[(-6, 10, 4, 0), (5, 7, 5, 0.2)], strands=[(-3, 6, 3), (-1, 6, 2.5), (2, 6, 2)])
    return r


def flagellant(f):
    """A penitent: wild black hair, a gaunt bloodied face, bare scarred shoulders, a rope sash, a spiked club."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    # spiked club raised over the left shoulder
    r.tube([(5.0, 24.0), (4.0, 10.0)], [1.0, 1.2], "p_wood", -1)
    pillow(r, ell_mask(3.8, 5.6, 3.2, 4.4), "p_wood", -0.9, bias=0.15)
    for (sx, sy, ex, ey) in ((1.0, 3.0, -1.0, 2.0), (2.6, 1.6, 2.0, -1.0), (5.4, 1.6, 6.4, -0.8), (6.8, 4.0, 9.0, 3.0),
                             (7.0, 7.2, 9.2, 7.8), (1.0, 7.6, -1.0, 8.6)):
        r.tube([(sx, sy), (ex, ey)], [0.7, 0.4], "p_steel", -0.8)
    line(r, [(3, 8), (4, 9), (5, 9)], "p_blood", 1.5, -0.7)
    shoulders(r, p, "p_skin", bias=0.05)
    # welts across the shoulders
    for (x0, y0, x1, y1) in ((4, 21, 7, 23), (20, 21, 24, 20)):
        line(r, [(x, y0 + by + round((y1 - y0) * (x - x0) / max(1, x1 - x0))) for x in range(x0, x1 + 1)], "p_blood", 1.5, 0.9)
    # the rope sash, knotted at the chest
    sash = [(6.0, 19.0), (10.0, 21.0), (14.0, 22.5), (18.0, 24.0)]
    r.tube([(x, y + by) for x, y in sash], [1.3] * 4, "p_rope", 1.2)
    pillow(r, ell_mask(16.0, 22.4 + by, 1.6, 1.3), "p_rope", 1.4, bias=0.2)
    d = head(r, p, brow="p_dark", age=1)
    # hollow cheeks
    for (x, y) in ((CX - 5, 14), (CX - 5, 15), (CX + 4, 14), (CX + 4, 15)):
        d(x, y, "p_skin", 1.5)
    # wild hair, spikes in every direction
    hair(r, p, {1: (-5, 4), 2: (-7, 6), 3: (-8, 7), 4: (-8, 7), 5: (-8, 7), 6: (-8, -3), 7: (-8, -6), 8: (-8, -7),
                9: (-8, -7)}, mat="p_dark", bias=0.35,
         locks=[(-3, 6, 3, -0.3), (0, 6, 2, 0.2), (3, 6, 3, 0.5), (6, 6, 4, 0.3), (-8, 9, 3, -0.3)],
         strands=[(-5, 2, 3), (-2, 2, 3), (1, 2, 2.5), (-4, 4, 2.5), (0, 4, 2), (4, 3, 2)])
    sp = r.part(True, 4.2)
    for (x, y, n, dx) in ((-8, 1, 3, -1), (-5, 0, 3, -0.6), (-1, 0, 3, 0), (3, 0, 3, 0.6), (6, 1, 3, 1), (8, 4, 3, 1),
                          (-9, 5, 2, -1)):
        for k in range(n):
            r.put(CX + x + int(round(dx * k)), y - k + hy, 4.2, "p_dark", 0.5 - 0.3 * k, sp, None)
    # fresh blood down the brow and cheek
    for (x, y, t) in ((CX + 3, 8, 2), (CX + 3, 9, 2), (CX + 4, 10, 1.5), (CX + 4, 12, 1.5), (CX + 4, 13, 1)):
        d(x, y, "p_blood", t)
    if f == 2:
        d(CX + 4, 14, "p_blood", 1)
    return r


def pilgrim(f):
    """A wayfarer of the faith: a wide felt hat with a coloured band, a robe, a white tabard with a red cross, a staff
    with a scallop shell."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    # staff on the left with a shell
    r.tube([(3.4, 24.0), (2.8, 3.0)], [0.9, 0.8], "p_wood", -1)
    pillow(r, ell_mask(4.2, 16.0, 2.2, 2.0), "p_bone", -0.6, bias=0.25)
    for x in (3, 4, 5):
        line(r, [(x, 15), (x, 16), (4, 17)], "p_bone", 1.5, -0.55)
    shoulders(r, p, "p_robe")
    pillow(r, [(x, y + by) for y in range(19, 24) for x in range(9 - (y - 19) // 2, 20 + (y - 19) // 2)], "p_white_c", 0.8, bias=0.1)
    pillow(r, [(x, y + by) for y in range(20, 24) for x in range(13, 16)], "p_red", 1.0, bias=0.1)
    pillow(r, [(x, y + by) for y in range(21, 23) for x in range(10, 19)], "p_red", 1.0, bias=0.1)
    head(r, p, beard="p_hair", age=1)
    hair(r, p, {7: (-8, -6), 8: (-8, -7), 9: (-8, -7), 10: (-8, -7), 11: (-8, -7)}, z=3.0, bias=0.2,
         strands=[(-7, 9, 3)])
    # the hat: a low crown, the band, a broad brim drooping at both sides
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {0: (-4, 4), 1: (-5, 5), 2: (-6, 6), 3: (-6, 6), 4: (-6, 6)}.items()
               for x in range(a, b + 1)], "p_felt", 5, bias=0.3)
    pillow(r, [(x + CX, 4 + hy) for x in range(-6, 7)], "p_plume", 5.2, bias=0.2)
    brim = {5: (-10, 10), 6: (-13, 13), 7: (-14, -8), 8: (-14, -11)}
    brim_r = {7: (8, 14), 8: (11, 14)}
    pillow(r, [(x + CX, y + hy) for y, (a, b) in list(brim.items()) + list(brim_r.items()) for x in range(a, b + 1)],
           "p_felt", 5.4, bias=0.15, vk=0.5)
    # the brim's shadow over the eyes
    d = Face(r, p, 3.4)
    for x in range(CX - 6, CX + 7):
        d(x, 8, "p_skin", 1)
    if f == 1:
        glint(r, 14, 21 + by)
    return r


def gambler(f):
    """A card-sharp: a black tricorn trimmed in gold with a plume, a waxed moustache, a wine coat, a cravat, a coin."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    shoulders(r, p, "p_wine")
    # lapels and the cravat
    pillow(r, [(x, y + by) for y in range(19, 24) for x in range(11, 18)], "p_white_c", 0.8, bias=0.2)
    pillow(r, [(x, y + by) for y in range(19, 24) for x in range(9 + (y - 19) // 3, 12)], "p_wine", 1.0, bias=0.35)
    pillow(r, [(x, y + by) for y in range(19, 24) for x in range(17, 20 - (y - 19) // 3)], "p_wine", 1.0, bias=-0.2)
    for y in (21, 23):
        line(r, [(10, y + by)], "p_gold", 3, 1.2)
    head(r, p, brow="p_dark")
    hair(r, p, {7: (-8, -6), 8: (-8, -7), 9: (-8, -7), 10: (-8, -7)}, mat="p_dark", z=3.0, bias=0.3)
    d = Face(r, p, 3.4)
    # waxed moustache curling up at the ends
    for (x, t) in ((CX - 3, 1), (CX - 2, 0.5), (CX - 1, 0.5), (CX, 0.5), (CX + 1, 0.5), (CX + 2, 1)):
        d(x, 15, "p_dark", t)
    d(CX - 4, 14, "p_dark", 1.5); d(CX + 3, 14, "p_dark", 1)
    d(CX, 18, "p_dark", 1)
    # tricorn: the crown, the up-turned brim, gold edging, the plume
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {1: (-4, 4), 2: (-5, 5), 3: (-6, 6), 4: (-6, 6)}.items()
               for x in range(a, b + 1)], "p_coal", 5, bias=0.3)
    brim = {3: [(-12, -9), (9, 12)], 4: [(-12, -7), (7, 12)], 5: [(-11, 10)], 6: [(-10, -3), (3, 10)], 7: [(-9, -6), (6, 9)]}
    pillow(r, [(x + CX, y + hy) for y, spans in brim.items() for (a, b) in spans for x in range(a, b + 1)],
           "p_coal", 5.4, bias=0.2, vk=0.5)
    line(r, [(CX + x, 5 + hy) for x in range(-11, 11)] + [(CX - 12, 4 + hy), (CX - 12, 3 + hy), (CX + 12, 4 + hy), (CX + 12, 3 + hy)],
         "p_gold", 3, 5.6)
    for i, (x, y) in enumerate(((CX + 4, 0), (CX + 6, -1), (CX + 8, 0), (CX + 9, 1), (CX + 10, 2))):
        pillow(r, [(x, y + hy + (1 if f == 2 and i > 2 else 0)), (x, y + 1 + hy)], "p_plume", 5.3 + i * 0.01, bias=0.3 - 0.1 * i)
    # a gold coin held up in the lower left, spinning between frames
    cw = [1.6, 0.6, 1.6, 1.1][f]
    pillow(r, ell_mask(5.0, 19.0, cw, 1.6), "p_gold", 6, bias=0.25)
    pillow(r, [(4, 21), (5, 21), (6, 21), (4, 22), (5, 22), (6, 22), (5, 23), (4, 23)], "p_skin", 5.9, bias=0.1)
    if f == 0:
        glint(r, 4, 18)
    return r


def reaver(f):
    """A northern raider: a ginger mane and a braided beard, a woad stripe over the eyes, a wolf pelt, an axe."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    # axe head over the right shoulder
    r.tube([(22.6, 24.0), (25.0, 5.0)], [0.9, 0.9], "p_wood", -1)
    pillow(r, [(x, y) for y in range(2, 11) for x in range(25, 29) if abs(y - 6) <= (x - 23)], "p_steel", -0.9, bias=0.15)
    shoulders(r, p, "p_pelt", bias=0.2, top=20.5)
    # pelt fur: tufts along the top edge
    # the pelt's ragged top edge: tufts standing up along the shoulders
    pillow(r, [(x, 19 + by + int(abs(x - 14) / 5.0) - (1 if x % 4 else 2)) for x in range(1, 28) if x % 4 != 3],
           "p_pelt", 0.05, bias=0.25)
    d = head(r, p, beard=None, brow="p_ginger", mouth=False)
    # woad: a band of blue across the eyes
    for x in range(CX - 6, CX + 7):
        if x in (CX - 3, CX - 4, CX + 3) and not p.blink:
            continue
        d(x, 10, "p_woad", 1.5 if x < CX else 1)
        if x not in (CX - 4, CX - 3, CX - 2, CX + 2, CX + 3, CX + 4) or p.blink:
            d(x, 11, "p_woad", 2 if x < CX else 1.5)
    # the beard: a mass from cheek to chest, two braids with rings
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {13: (-6, 6), 14: (-6, 6), 15: (-6, -2), 16: (-6, 6), 17: (-5, 5),
                                                   18: (-5, 4), 19: (-4, 4), 20: (-4, 3)}.items() for x in range(a, b + 1)
            if not (y == 15 and False)], "p_ginger", 3.6, bias=0.25)
    pillow(r, [(x + CX, 15 + hy) for x in range(2, 7)], "p_ginger", 3.6, bias=0.1)
    line(r, [(CX - 1, 15 + hy), (CX, 15 + hy), (CX + 1, 15 + hy)], "p_lip", 1, 3.7)
    for bx in (CX - 2, CX + 2):
        for y in range(20, 24):
            pillow(r, [(bx, y + hy), (bx + 1, y + hy)], "p_ginger", 3.8, bias=0.3 - 0.4 * (y % 2))
        pillow(r, [(bx, 22 + hy), (bx + 1, 22 + hy)], "p_gold", 3.9, bias=0.3)
    hair(r, p, {0: (-5, 4), 1: (-7, 6), 2: (-8, 7), 3: (-9, 8), 4: (-9, 8), 5: (-9, 8), 6: (-9, -4), 7: (-9, -6),
                8: (-9, -7), 9: (-9, -7), 10: (-10, -7), 11: (-10, -7), 12: (-10, -7)}, mat="p_ginger", bias=0.3,
         locks=[(-2, 6, 2, 0), (1, 6, 1, 0), (4, 6, 2, 0.5), (7, 6, 6, 0.2), (-10, 13, 4, 0.2)],
         strands=[(-6, 2, 3), (-3, 1, 3), (0, 2, 3), (3, 2, 2.5), (-5, 4, 3), (-1, 4, 2.5), (-8, 7, 2.5), (-9, 10, 2)])
    if f == 1:
        glint(r, 27, 4)
    return r


def cutpurse(f):
    """A thief: a charcoal hood pulled low, a cloth mask over nose and mouth, sharp eyes, a knife held up."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    shoulders(r, p, "p_coal")
    pillow(r, [(x, y + by) for y in range(20, 24) for x in range(10, 19)], "p_lthr", 0.6, bias=0.1)
    hood(r, p, "p_coal", top=0, open_w=5.6)
    head(r, p, mouth=False, nose=False, ears=False, brow="p_dark")
    hair(r, p, {5: (-5, 5), 6: (-6, 5), 7: (-6, -3), 8: (-6, -5)}, mat="p_dark", z=3.5, bias=0.4,
         locks=[(-2, 7, 1, 0), (2, 7, 2, 0.3)])
    # the mask: from the bridge of the nose down, knotted at the side
    pillow(r, [(x + CX, y + p.hy) for y, (a, b) in {12: (-6, 6), 13: (-7, 6), 14: (-7, 6), 15: (-6, 6), 16: (-6, 5),
                                                     17: (-5, 4), 18: (-4, 3), 19: (-3, 2)}.items()
               for x in range(a, b + 1)], "p_teal", 3.6, bias=0.2)
    line(r, [(CX + 1, 13 + hy), (CX + 1, 14 + hy), (CX - 3, 16 + hy), (CX - 2, 17 + hy)], "p_teal", 1, 3.7)
    pillow(r, ell_mask(CX + 7.5, 14.5 + hy, 1.2, 1.2), "p_teal", 3.8, bias=0.0)
    # a knife held up by the face, edge catching the light
    r.tube([(22.5, 24.0), (22.5, 19.0)], [1.0, 1.0], "p_lthr", 6)
    r.tube([(20.6, 18.4), (24.4, 18.4)], [0.6, 0.6], "p_iron", 6.1)
    pillow(r, [(22, y) for y in range(9, 18)] + [(23, y) for y in range(10, 18)], "p_steel", 6.2, bias=0.3)
    pillow(r, [(20, 22), (21, 22), (21, 21), (20, 21), (24, 21), (24, 22), (23, 22)], "p_skin", 6.3, bias=0.0)
    if f == 1:
        glint(r, 22, 11)
    return r


def arbalist(f):
    """A crossbowman: a broad steel kettle hat, a brown beard, a quilted oxblood jack, the crossbow on his shoulder."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    # crossbow resting on the left shoulder: stock and prod
    r.tube([(0.0, 21.0), (8.0, 17.0)], [1.2, 1.1], "p_wood", 1.6)
    r.tube([(2.0, 13.0), (3.0, 17.4), (5.4, 23.0)], [0.7, 0.8, 0.7], "p_steel", 1.5)
    shoulders(r, p, "p_oxblood")
    # quilting
    for y in (21, 23):
        line(r, [(x, y + by) for x in range(3, 26) if (x - 14) ** 2 / 120.0 + (y - 28) ** 2 / 70.0 < 1.0], "p_oxblood", 1, 0.2)
    for x in (8, 14, 20):
        line(r, [(x, y + by) for y in range(20, 24)], "p_oxblood", 1, 0.2)
    head(r, p)
    # full beard
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {14: (-6, -4), 15: (-6, -3), 16: (-6, -3), 17: (-5, 4), 18: (-4, 4),
                                                   19: (-3, 3), 20: (-2, 2)}.items() for x in range(a, b + 1)]
           + [(x + CX, y + hy) for y in (14, 15, 16) for x in range(3, 6)], "p_hair", 2.6, bias=0.2)
    line(r, [(CX - 2, 15 + hy), (CX - 1, 15 + hy), (CX, 15 + hy), (CX + 1, 15 + hy), (CX + 2, 15 + hy)], "p_hair", 1, 3.5)
    hair(r, p, {7: (-8, -6), 8: (-8, -7), 9: (-8, -7), 10: (-8, -7)}, z=3.0, bias=0.2)
    # kettle hat: a round crown, a wide flat brim, a riveted band
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {0: (-4, 3), 1: (-6, 5), 2: (-7, 6), 3: (-7, 6), 4: (-7, 6), 5: (-7, 6)}.items()
               for x in range(a, b + 1)], "p_steel", 5, bias=0.25)
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {6: (-12, 11), 7: (-13, 12)}.items() for x in range(a, b + 1)],
           "p_steel", 5.4, bias=0.1, vk=0.4)
    line(r, [(CX + x, 5 + hy) for x in (-6, -3, 0, 3, 6)], "p_iron", 1, 5.5)
    d = Face(r, p, 3.4)
    for x in range(CX - 6, CX + 7):
        d(x, 8, "p_skin", 1)
    if f == 1:
        glint(r, CX - 5, 1 + hy)
    elif f == 2:
        glint(r, CX - 11, 6 + hy)
    return r


def scholar(f):
    """A grey sage: white hair in a bun, a long white beard, gold spectacles, a midnight robe, a candle lantern."""
    p, r = Pose(f), BP.Bust()
    by, hy = p.by, p.hy
    shoulders(r, p, "p_navy")
    # gold stole edges
    for x0 in (10, 18):
        line(r, [(x0 + (y - 19) // 2 * (-1 if x0 < 14 else 1), y + by) for y in range(19, 24)], "p_gold", 2.5, 0.6)
    d = head(r, p, brow="p_white", age=1, mouth=False)
    # beard and moustache
    pillow(r, [(x + CX, y + hy) for y, (a, b) in {14: (-6, -3), 15: (-6, -2), 16: (-6, 5), 17: (-5, 5), 18: (-5, 4),
                                                   19: (-4, 4), 20: (-4, 3), 21: (-3, 3), 22: (-2, 2), 23: (-1, 1)}.items()
               for x in range(a, b + 1)] + [(x + CX, y + hy) for y in (14, 15) for x in range(3, 6)],
           "p_white", 3.6, bias=0.3)
    pillow(r, [(x + CX, 15 + hy) for x in range(-2, 3)], "p_white", 3.7, bias=0.4)
    line(r, [(CX, 16 + hy)], "p_white", 1, 3.8)
    hp = r.part(True, 3.8); r.hand.add(hp)
    for (x, y) in ((-3, 18), (0, 19), (2, 18), (-1, 21), (1, 22)):
        r.put(CX + x, y + hy, 3.8, "p_white", 0.5, hp, 1.5)
    # spectacles: gold rims, the glass catching the light
    for ex in (CX - 3, CX + 3):
        for (x, y) in ((-1, 10), (0, 10), (1, 10), (-2, 11), (2, 11), (-1, 12), (0, 12), (1, 12)):
            d(ex + x + 0.5, y, "p_gold", 3 if y == 10 else 2)
    d(CX + 0.5, 11, "p_gold", 2.5)
    if f == 2:
        d(CX - 3.5, 11, "p_shine", 3)
    # white hair, thin on top, a bun
    hair(r, p, {3: (-6, 5), 4: (-7, 6), 5: (-8, 7), 6: (-8, 7), 7: (-8, -5), 8: (-8, -6), 9: (-8, -7), 10: (-8, -7)},
         mat="p_white", bias=0.3, locks=[(7, 7, 3, 0.3), (-8, 11, 2, -0.3)],
         strands=[(-5, 4, 3), (-2, 3, 3), (1, 3, 2.5), (4, 4, 2), (-6, 6, 2.5)])
    pillow(r, ell_mask(CX + 1.5, 1.4 + hy, 3.0, 2.2), "p_white", 4.4, bias=0.2)
    line(r, [(CX - 1 + x, 2 + hy) for x in range(0, 6)], "p_gold", 2.5, 4.6)
    # candle lantern in the lower left, its flame flickering
    lx, ly = 4, 17
    pillow(r, [(x, y) for y in range(ly - 6, ly - 4) for x in range(lx - 2 + (ly - 5 - y), lx + 3 - (ly - 5 - y))], "p_gold", 6, bias=0.3)
    gp = r.part(True, 6)
    for y in range(ly - 4, ly + 4):
        for x in range(lx - 2, lx + 3):
            dd = math.hypot((x - lx) * 1.2, (y - ly + 0.5) * 0.7)
            r.put(x, y, 6, "p_flame", 0.5, gp, 4 if dd < 0.8 + 0.4 * (f % 2) else 3 if dd < 1.6 else 1)
    line(r, [(lx - 3, y) for y in range(ly - 4, ly + 4)], "p_gold", 3, 6.2)
    line(r, [(lx + 3, y) for y in range(ly - 4, ly + 4)], "p_gold", 1.5, 6.2)
    pillow(r, [(x, ly + 4) for x in range(lx - 3, lx + 4)] + [(x, ly + 5) for x in range(lx - 3, lx + 4)], "p_gold", 6.3, bias=0.2)
    for i, (x, y) in enumerate(((lx - 2, ly - 9), (lx + 2, ly - 11))):
        line(r, [(x + (f % 2), y - (f % 3))], "p_flame", 3 if i == f % 2 else 2, 8)
    return r


ORIGINS = {"Wanderer": wanderer, "Sellsword": sellsword, "Huntress": huntress, "Hexblade": hexblade,
           "Flagellant": flagellant, "Pilgrim": pilgrim, "Gambler": gambler, "Reaver": reaver, "Cutpurse": cutpurse,
           "Arbalist": arbalist, "Scholar": scholar}


# ------------------------------------------------------------------ build
def frames(name, slot=None):
    install(ramps_for(name, slot))
    tones = bg_for(name, slot)
    fn = ORIGINS[name]
    return [compose(fn(f), tones) for f in range(4)]


def pack(sid, ims, outdir=OUT):
    """One Idle anim, 4 frames of 29x24 in a row (same layout and manifest as every portrait sheet)."""
    import json
    cols = 8
    sheet = Image.new("RGBA", (256, 32), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * W, (i // cols) * H))
    os.makedirs(outdir, exist_ok=True)
    sheet.save(os.path.join(outdir, sid + ".png"))
    man = {"cellW": W, "cellH": H, "cols": cols, "anims": [{"name": "Idle", "frames": list(range(len(ims))), "durations": DURS}]}
    json.dump(man, open(os.path.join(outdir, sid + ".json"), "w"))
    pv = Image.new("RGBA", (len(ims) * (W + 2) * 6, (H + 2) * 6), (40, 38, 46, 255))
    for i, im in enumerate(ims):
        pv.alpha_composite(im.resize((W * 6, H * 6), Image.NEAREST), (i * (W + 2) * 6, 6))
    pv.convert("RGB").save(os.path.join(outdir, sid + "_preview.png"))


def board(rows, path, scale=6):
    pad = 3
    img = Image.new("RGBA", ((4 * (W + pad) + pad) * scale, (len(rows) * (H + pad) + pad) * scale), (40, 38, 46, 255))
    for j, ims in enumerate(rows):
        for i, im in enumerate(ims):
            img.alpha_composite(im.resize((W * scale, H * scale), Image.NEAREST), ((pad + i * (W + pad)) * scale, (pad + j * (H + pad)) * scale))
    img.convert("RGB").save(path)


def build(outdir=OUT, only=None):
    rows = []
    for name in ORDER:
        if only and name not in only: continue
        ims = frames(name)
        pack("Hero" + name, ims, outdir)
        rows.append(ims)
        print("built Hero" + name)
    board(rows, os.path.join(outdir, "board_origins.png"))
    return rows


if __name__ == "__main__":
    argv = sys.argv[1:]
    only = None
    if "--only" in argv:
        i = argv.index("--only"); only = argv[i + 1].split(","); del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    build(args[0] if args else OUT, only)
