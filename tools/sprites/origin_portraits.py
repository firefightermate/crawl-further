"""Hero-origin portraits (29x24, 4-frame Idle) drawn with the shared material renderer (jinx_v2_rigs.Rig).

    python3 tools/sprites/origin_portraits.py      (hero_portraits.py runs it too)

Writes art/out_heroes/Hero<Origin>.png/.json/_preview.png (the canonical colours) and art/out_heroes/board_origins.png.
hero_slots.py draws the same portraits in each player slot's colours through frames(name, slot).

Every portrait is a bust on a dark vignette: shaded volumes (head, hair, cloth, steel) lit from the top left with three
tones per material, the right and bottom edges in each material's own dark tones, faces hand-placed on top. Each origin
names its team materials (TEAM): those ramps turn to the player's colour family in the slot sets (hero_looks.slot_col,
the same rule as the in-game body and the gear), everything else (skin, steel, leather, gold) never changes.
The four Idle frames are posed redraws: breath, a blink, a glance, a prop catching the light.
"""
import colorsys
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
from jinx_v2_rigs import Rig  # noqa: E402
import hero_looks as HL  # noqa: E402
import weapon_bubbles as WB  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "art", "out_heroes")
W, H = 29, 24
DURS = [0.2, 0.18, 0.2, 0.16]
ORDER = ["Wanderer", "Sellsword", "Huntress", "Hexblade", "Flagellant", "Pilgrim", "Gambler",
         "Reaver", "Cutpurse", "Arbalist", "Scholar"]

BASE = {
    # skin and hair
    "p_skin":   ("3a2018", "7a4a32", "b07a52", "d2a070", "ecc898"),
    "p_hair":   ("1a120c", "3a2818", "5e4228", "86643a", "a68654"),
    "p_ginger": ("2a0e06", "6a2a10", "a64a1c", "d4742c", "f0a04e"),
    "p_white":  ("4a4642", "7e7a74", "b0aca4", "dcd8d0", "f6f4ee"),
    "p_black":  ("0c0a0c", "1c181c", "2c2628", "40383a", "5a5052"),
    # cloth
    "p_rust":   ("260c0c", "662418", "a43e28", "cc5e34", "e48a50"),
    "p_green":  ("0e160c", "223420", "36522c", "52723a", "76944e"),
    "p_violet": ("0e0818", "261640", "40265e", "5c3a84", "8058aa"),
    "p_sack":   ("1a140e", "3a3022", "5a4c38", "7a6a50", "9c8c6c"),
    "p_white_c": ("3a3630", "7a746a", "b4ae9e", "d8d2c2", "f0ecdc"),
    "p_robe":   ("1c100c", "40281c", "66402c", "885a3c", "a8784e"),
    "p_wine":   ("1c0610", "4a1020", "7e1e30", "a8303e", "c8505a"),
    "p_coal":   ("0a0a0c", "1a181c", "2c282e", "403a42", "5a5258"),
    "p_teal":   ("08181a", "123634", "1e5450", "347a72", "54a096"),
    "p_ochre":  ("261808", "5a3e14", "8e6a26", "b88e3c", "d8b45c"),
    "p_oxblood": ("1a0608", "461214", "742420", "983a30", "b85a44"),
    "p_navy":   ("080c1c", "141e3e", "22325e", "344a84", "5068a6"),
    "p_pelt":   ("241c14", "54463a", "867662", "b0a088", "d2c4a8"),
    "p_felt":   ("16161c", "2e2e38", "4a4a58", "6a6a7a", "8c8c9c"),
    "p_red":    ("2a0608", "6a1012", "a81e1a", "d03a2a", "f06a4a"),
    "p_woad":   ("0c1430", "1a2e64", "2a4a96", "4470c0", "6a96dc"),
    "p_plume":  ("2a0606", "6a1010", "aa1e1a", "e03a2a", "ff7a5a"),
    # gear
    "p_steel":  ("161820", "3a3e4c", "666c7c", "a0a6b4", "e0e4ec"),
    "p_iron":   ("121016", "2a2830", "4a4652", "6e6a76", "9c98a4"),
    "p_lthr":   ("140c0a", "30201a", "4e3426", "6c4a34", "8c6646"),
    "p_wood":   ("1e120c", "432818", "6a4228", "8e6038", "b48650"),
    "p_gold":   ("2a1808", "6a4414", "a8762a", "dcb04a", "fbe796"),
    "p_rope":   ("2a2010", "5a4828", "8a7448", "b89e6a", "d8c294"),
    "p_bone":   ("34281e", "75644e", "b2a07e", "dccca6", "f8f0d8"),
    "p_paper":  ("3a3024", "7a6a4c", "b4a07a", "dccaa0", "f6ecd0"),
    # emissive
    "p_eyew":   ("6a5e54", "a49a8e", "e6dccc", "f4ece0", "ffffff"),
    "p_rune":   ("3a1a5a", "8a3ab8", "c070f0", "f0c0ff", "ffffff"),
    "p_flame":  ("5a1a0a", "b8401a", "f07a24", "ffc04a", "fff0b0"),
    "p_blood":  ("3a0608", "6e0e12", "a81e1a", "d0402e", "f07050"),
    "p_shine":  ("8a8a90", "c8ccd4", "e8ecf2", "f6f8fc", "ffffff"),
}
EMIT = {"p_eyew", "p_rune", "p_flame", "p_blood", "p_shine"}
SHINY = {"p_steel", "p_gold", "p_iron", "p_bone"}

# origin -> [(materials that take the player colour, canonical slot)]; -1: tinted in every slot (Wanderer: the
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
# background vignette tones (frame, edge, mid, centre)
BG = {
    "Wanderer":   ("121014", "221c21", "2d252a", "3a3034"),
    "Sellsword":  ("101115", "1d1f25", "282a31", "34363e"),
    "Huntress":   ("0f120f", "1b211b", "252c23", "30382c"),
    "Hexblade":   ("100c16", "1e1628", "291e36", "352745"),
    "Flagellant": ("140c0e", "241518", "311c1f", "402427"),
    "Pilgrim":    ("101116", "1e1f26", "292a33", "363742"),
    "Gambler":    ("13110e", "221e19", "2e2820", "3b3328"),
    "Reaver":     ("140f0c", "251b16", "31241d", "3f2e24"),
    "Cutpurse":   ("0d1112", "181f21", "212a2c", "2b3638"),
    "Arbalist":   ("13100b", "231e15", "2f281c", "3c3324"),
    "Scholar":    ("0c0e18", "171b2c", "20263c", "2a324e"),
}
# the tunic colour of the vanilla hero, read from each player's ramp (hero_looks): the Wanderer wears it
WANDERER_SRC = (203, 76, 43)
BG_TINT_MIN = 0.16


def _h(s):
    return J._h(s)


def hls(c):
    return colorsys.rgb_to_hls(*[v / 255.0 for v in c[:3]])


def rgb(h, l, s):
    return tuple(max(0, min(255, int(round(v * 255)))) for v in colorsys.hls_to_rgb(h, l, s))


# ------------------------------------------------------------------ colours per slot
def ramps_for(name, slot):
    """Material ramps for origin `name` in player slot 0-3 (None = the canonical colours). Every ramp but the
    emissive ones is kept inside Crawl's muted range (weapon_bubbles.tame)."""
    out = {k: [_h(c) if k in EMIT else WB.tame(_h(c), 0.30, 0.62) for c in v] for k, v in BASE.items()}
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
    """The four vignette tones: canonical, or turned to the slot hue so the frame reads in the player colour."""
    base = [_h(c) for c in BG[name]]
    if slot is None:
        return base
    canon = TEAM[name][0][1]
    if slot == canon and hls(base[3])[2] >= 0.12:
        return base
    return [rgb(HL.SLOT_HUE[slot] / 360.0, hls(c)[1], max(hls(c)[2], BG_TINT_MIN)) for c in base]


def install(ramps):
    J.RAMPS.update(ramps)
    J.EMISSIVE.update(EMIT)
    J.SHINY.update(SHINY)


# ------------------------------------------------------------------ background
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def background(tones, cx=14.0, cy=9.0):
    im = Image.new("RGBA", (W, H), tones[0] + (255,))
    p = im.load()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            d = (((x - cx) / 15.0) ** 2 + ((y - cy) / 13.0) ** 2) ** 0.5
            t = d * 2.6 + BAYER[y % 4][x % 4] / 16.0 - 0.5
            p[x, y] = (tones[3] if t < 0.55 else tones[2] if t < 1.55 else tones[1]) + (255,)
    return im


def compose(r, tones):
    """Resolve the bust and lay it over the vignette; the 1 px frame stays on top."""
    s = r.resolve(selout=True, cast=True, contour=True, clean=True, floor=False)
    im = background(tones)
    p = im.load()
    for (x, y), c in s.px.items():
        if 1 <= x < W - 1 and 1 <= y < H - 1:
            p[x, y] = tuple(c[:3]) + (255,)
    return im


# ------------------------------------------------------------------ the bust
class Pose:
    """Per-frame pose: breath lifts the chest, the head bobs less, the eyes glance and blink."""

    def __init__(self, f):
        self.f = f
        self.breath = [0.0, 0.5, 1.0, 0.5][f]
        self.hy = [0, 0, 1, 0][f]
        self.head = float(self.hy)
        self.blink = f == 3
        self.look = [0, 0, 1, 0][f]
        self.sway = [0.0, 0.6, 1.0, 0.4][f]


def torso(r, mat, p, cx=14.5, top=15.5, rx=14.5, ry=10.0, z=0.0, bias=0.0):
    """Shoulders and chest: the top of a wide dome, cut by the frame."""
    cy = top + ry + p.breath * 0.6
    return r.ell(cx, cy, rx, ry, mat, z, bias=bias, clip=lambda x, y: y <= H - 1)


def neck(r, p, cx=14.0, w=2.4, z=0.5, mat="p_skin"):
    return r.tube([(cx, 11.0 + p.hy), (cx + 0.3, 17.0 + p.breath)], [w, w + 0.4], mat, z, bias=0.0)


# The face: hand-placed tones of the skin ramp (4 highlight .. 0 ink), light from the left, 12 x 11 at (FX, FY).
# e = eye white, p = pupil, b = brow, m = mouth line, M = lips.
FACE_M = [
    ".1233332210.",
    ".2343333221.",
    ".2343333221.",
    ".2343333221.",
    ".23bb33bb21.",
    "123ep33ep210",
    "123334332210",
    ".2333321221.",
    ".2233mmm221.",
    "..223332211.",
    "...112211...",
]
FACE_F = [
    "..12333221..",
    ".2343333221.",
    ".2343333221.",
    ".2343333221.",
    ".2b333b3221.",
    "123ep33ep210",
    ".23334332210",
    ".2333321221.",
    "..233MM3221.",
    "...233321...",
    "....1221....",
]
FX, FY = 8, 3


def face(r, p, female=False, brow="p_hair", brow_tone=1, z=2.0, lip="p_blood", scar=False, eyes=True):
    rows = list(FACE_F if female else FACE_M)
    if p.blink or not eyes:
        rows = [row.replace("e", "1").replace("p", "1") for row in rows]
    elif p.look:
        rows = [row.replace("ep", "pe") for row in rows]
    lg = {str(t): ("p_skin", t) for t in range(5)}
    lg.update({"e": ("p_eyew", 2), "p": ("p_black", 0), "b": (brow, brow_tone), "m": ("p_skin", 0), "M": (lip, 2)})
    r.stamp("\n".join(rows), FX, FY + p.hy, z, lg)
    if scar:
        for (x, y) in ((17, 6), (17, 8), (18, 9)):
            r.dot(x, y + p.hy, "p_blood", 1, z + 0.5)


def strap(r, p, a, b, mat="p_lthr", w=1.0, z=3.0, buckle=None):
    dy = p.breath * 0.6
    r.tube([(a[0], a[1] + dy), (b[0], b[1] + dy)], [w, w], mat, z)
    if buckle is not None:
        t = buckle
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + dy
        r.ell(x, y, 1.1, 1.1, "p_gold", z + 0.1)


def sparkle(r, x, y, size=1, mat="p_shine", z=9.0):
    r.dot(x, y, mat, 4, z)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            r.dot(x + dx, y + dy, mat, 3 if k == 1 else 2, z)


# ------------------------------------------------------------------ origins
def hair_mop(r, p, mat="p_hair", z=4.0, fringe=6.0, sides=(10.0, 8.0), sway=0.0):
    """A full head of hair over the skull rows of the face template: crown, side parting, locks over the brow."""
    hy = p.hy
    r.ell(13.8, 3.8 + hy, 6.6, 4.4, mat, z, bias=0.15, clip=lambda x, y: y <= 5 + hy)
    # side locks over the ears
    r.tube([(8.4, 4 + hy), (8.0, sides[0] + hy)], [1.4, 0.8], mat, z + 0.1, thin=True)
    r.tube([(19.4, 4 + hy), (19.8, sides[1] + hy)], [1.3, 0.7], mat, z + 0.1, thin=True)
    # strands: light lines combed from the crown, dark partings between them
    for i, (x0, x1) in enumerate(((10.0, 8.6), (12.0, 11.0), (14.0, 14.4), (16.0, 17.6), (18.0, 19.6))):
        r.line(x0 + 1.0, 0.6 + hy, x1, 4.4 + hy, mat, z + 0.15, 3 if i < 3 else 2)
        r.line(x0 + 2.0, 1.0 + hy, x1 + 1.0, 4.6 + hy, mat, z + 0.15, 1)
    # fringe: tufts falling onto the forehead, swept to the right
    for i, x0 in enumerate((9.5, 11.5, 13.5, 15.5, 17.5)):
        r.tube([(x0, 3.5 + hy), (x0 + 1.0 + sway * (i % 2), fringe - (i % 2) * 0.8 + hy)], [1.2, 0.5], mat, z + 0.2, thin=True)


def wanderer(f):
    """The plain hero: tousled brown hair, the player's own tunic, a baldric and a sword hilt over the shoulder."""
    p, r = Pose(f), Rig()
    r.tube([(23.0, 21), (24.0, 10.5)], [1.0, 0.9], "p_steel", -1)
    r.tube([(20.8, 10.5 + p.breath * 0.4), (27.0, 9.8 + p.breath * 0.4)], [0.9, 0.9], "p_iron", 1.2)
    r.tube([(24.0, 10 + p.breath * 0.4), (24.4, 4.5)], [0.9, 0.8], "p_lthr", 1.1)
    for yy in (8.6, 6.8, 5.0):
        r.line(23.2, yy, 25.2, yy - 0.8, "p_lthr", 1.15, 1)
    r.ell(24.5, 3.4, 1.4, 1.3, "p_iron", 1.3)
    torso(r, "p_rust", p)
    by = p.breath * 0.6
    r.poly([(11.0, 15.0 + by), (17.0, 15.0 + by), (14.0, 18.5 + by)], "p_skin", 0.8, normal=(0, 0.3, 0.9))
    r.tube([(10.0, 16.0 + by), (14.0, 19.0 + by), (18.0, 16.0 + by)], [0.7, 0.7, 0.7], "p_rust", 0.9, bias=-0.35)
    strap(r, p, (20.5, 15.5), (8.5, 23.5), buckle=0.55)
    neck(r, p)
    face(r, p)
    hair_mop(r, p, sway=p.sway)
    if f == 1:
        sparkle(r, 24, 5, 1)
    return r


def sellsword(f):
    """A hired blade: an iron half-helm with a nasal, a mail coif over the shoulders, a rust tunic, a scar."""
    p, r = Pose(f), Rig()
    r.tube([(4.5, 22), (7.0, 1.5)], [1.1, 0.9], "p_steel", -1)        # greatsword over the far shoulder
    r.tube([(2.0, 16.5), (9.0, 15.0)], [0.9, 0.9], "p_iron", -0.8)
    r.tube([(5.3, 16), (5.8, 21)], [0.9, 0.9], "p_lthr", -0.9)
    torso(r, "p_rust", p)
    dy = p.breath * 0.6
    mail = r.ell(14.0, 20.0 + dy, 10.0, 5.6, "p_iron", 1.0, bias=0.15, clip=lambda x, y: y <= 18.0 + dy)
    for (x, y), v in list(r.b.items()):
        if v[3] == mail and (x + y) % 2 == 0:
            v[2] -= 0.35
    neck(r, p, mat="p_iron")
    strap(r, p, (22.0, 17.5), (12.0, 23.5), buckle=0.5)
    face(r, p, scar=True)
    hy = p.hy
    for (x, y) in ((10, 11), (11, 12), (12, 12), (15, 12), (16, 12), (17, 11)):
        r.dot(x, y + hy, "p_skin", 1, 2.5)
    # mail coif down both cheeks, under the helm
    r.poly([(7.4, 5.5 + hy), (9.6, 5.5 + hy), (9.6, 12.5 + hy), (8.0, 15)], "p_iron", 2.6, normal=(-0.3, 0, 0.9))
    r.poly([(18.6, 5.5 + hy), (20.6, 5.5 + hy), (20.2, 15), (18.8, 12.5 + hy)], "p_iron", 2.6, normal=(0.4, 0, 0.9))
    # helm: a rounded iron cap low over the brow, a riveted band, a nasal bar down the nose
    r.ell(14.0, 4.6 + hy, 6.6, 5.0, "p_steel", 5, bias=0.0, clip=lambda x, y: y <= 6 + hy)
    r.tube([(7.6, 6.2 + hy), (20.4, 6.2 + hy)], [0.9, 0.9], "p_iron", 5.2)
    r.tube([(14.0, 6.5 + hy), (14.0, 9.6 + hy)], [0.6, 0.6], "p_iron", 7)
    for x in (9, 11.5, 16.5, 19):
        r.dot(x, 6 + hy, "p_steel", 4, 5.6)
    r.tube([(14.0, -0.2 + hy), (14.0, 5.0 + hy)], [0.6, 0.6], "p_steel", 5.4, bias=0.3)
    if f == 1:
        sparkle(r, 11, 2, 1)
    elif f == 2:
        sparkle(r, 7, 3, 1)
    return r


def hood(r, p, mat, z_back=0.6, z_brim=3.0, peak=None, low=4.6, wide=7.6, arc=6.6, inset=0.0):
    """A hood: the back of it behind the head, a thick brim round the face that hides the skull rows."""
    hy = p.hy
    r.ell(13.8, 7.0 + hy, wide, 8.6, mat, z_back, bias=0.05)
    if peak:
        r.poly([(9.0, 3.0 + hy), (peak[0], peak[1] + hy), (13.0, 1.0 + hy)], mat, z_back + 0.05, normal=(-0.3, -0.5, 0.8))
    # brim: an arch over the brow, down both cheeks
    pts = []
    for i in range(13):
        a = math.radians(180 + i * 15)
        pts.append((13.8 + math.cos(a) * arc, low + 1.0 + hy + math.sin(a) * 4.2))
    r.tube(pts, [1.4] * len(pts), mat, z_brim, bias=0.15)
    i = inset
    r.poly([(7.0 + i, low + hy), (9.6 + i, low + hy), (9.6 + i, 13.0 + hy), (7.6 + i, 15.0)], mat, z_brim - 0.1, normal=(-0.2, 0, 0.9))
    r.poly([(18.4 - i, low + hy), (21.0 - i, low + hy), (20.6 - i, 15.0), (18.6 - i, 13.0 + hy)], mat, z_brim - 0.1,
           normal=(0.5, 0, 0.8))


def huntress(f):
    """A forest hunter: a green hood and cloak over a rust jerkin, a quiver over the shoulder, her bow stave beside her."""
    p, r = Pose(f), Rig()
    # bow stave on the right, string taut
    stave = [(24.5, 1.0), (26.2, 6.0), (26.6, 12.0), (26.0, 18.0), (24.6, 23.0)]
    r.tube(stave, [0.8, 1.0, 1.1, 1.0, 0.8], "p_wood", -1)
    r.line(24.2, 1.6, 24.2, 22.4, "p_bone", -0.9, 2)
    r.tube([(25.6, 10.5), (27.2, 13.5)], [1.2, 1.2], "p_lthr", -0.8)
    # quiver behind the left shoulder: three arrows with red and white fletching
    r.tube([(4.0, 21.0), (6.5, 9.0)], [2.0, 1.8], "p_lthr", -1)
    for i, (x, y) in enumerate(((4.5, 6.0), (6.6, 4.6), (8.4, 6.2))):
        r.tube([(x + 0.8, y + 4.0), (x, y)], [0.5, 0.5], "p_wood", -0.6)
        r.poly([(x - 1.2, y - 2.4 + (0.4 if f == 2 and i == 1 else 0)), (x + 1.2, y - 2.0), (x + 0.6, y + 1.6), (x - 0.8, y + 1.2)],
               "p_plume" if i % 2 == 0 else "p_white_c", -0.5, normal=(-0.3, -0.4, 0.8))
    torso(r, "p_green", p)
    by = p.breath * 0.6
    r.poly([(11.0, 15.0 + by), (17.4, 15.0 + by), (15.6, 23.5), (12.6, 23.5)], "p_rust", 0.8, normal=(0, 0.2, 1.0))
    for y in (18.0, 20.5):
        r.dot(14.2, y + by, "p_gold", 3, 0.9)
    strap(r, p, (8.0, 15.0), (18.0, 23.5), mat="p_lthr", w=0.8, z=1.0)
    neck(r, p)
    hood(r, p, "p_green")
    face(r, p, female=True, brow="p_hair")
    # a braid out of the hood over her shoulder
    hy = p.hy
    r.tube([(19.0, 11.0 + hy), (19.8, 14.5 + hy), (19.6, 18.5 + by)], [1.2, 1.1, 0.8], "p_ginger", 3.4)
    for y in (13.0, 15.0, 17.0):
        r.line(18.4, y + hy * 0.5, 20.6, y + 0.8 + hy * 0.5, "p_ginger", 3.5, 1)
    r.ell(19.6, 19.2 + by, 0.9, 0.7, "p_lthr", 3.6)
    if f == 1:
        sparkle(r, 25, 3, 1)
    return r


def hexblade(f):
    """A cursed swordmage: a deep violet cowl with a trailing peak, eyes glowing in its shadow, a rune-lit staff."""
    p, r = Pose(f), Rig()
    # staff on the right with a violet crystal in an iron claw
    r.tube([(24.5, 23.0), (24.0, 6.0)], [0.9, 0.8], "p_wood", -1)
    r.tube([(22.6, 6.5), (24.0, 5.0), (25.4, 6.5)], [0.6, 0.6, 0.6], "p_iron", -0.6)
    fl = [2.6, 2.9, 3.2, 2.8][f]
    for y in range(int(-1), 6):
        for x in range(21, 28):
            d = math.hypot((x - 24.0) * 1.4, (y - 2.6) / fl * 2.6)
            if d < 2.8:
                r.put(x, y, -0.4, "p_rune", 0.5, r.part(True, -0.4), 4 if d < 0.9 else 3 if d < 1.9 else 2)
    torso(r, "p_violet", p)
    by = p.breath * 0.6
    r.poly([(11.6, 15.0 + by), (16.8, 15.0 + by), (14.2, 23.5)], "p_black", 0.8, normal=(0, 0.2, 1.0))
    r.ell(14.2, 17.0 + by, 1.6, 1.4, "p_steel", 1.0)
    r.dot(14.0, 16.8 + by, "p_rune", 4 if f % 2 == 0 else 3, 1.2)
    for (x, y) in ((6, 19), (8, 21), (21, 19), (23, 21)):
        r.dot(x, y + by, "p_rune", 2 if (x + f) % 3 else 3, 1.1)
    neck(r, p)
    face(r, p, female=True, brow="p_black")
    hood(r, p, "p_violet", peak=(3.0, -3.0), low=5.6, arc=5.6, inset=0.8, wide=7.0)
    hy = p.hy
    # the cowl's shadow on the brow, the eyes lit from inside
    for x in range(10, 18):
        r.dot(x, 6 + hy, "p_skin", 1, 3.5)
    if not p.blink:
        ex = (12, 16) if not p.look else (11, 15)
        for x in ex:
            r.dot(x, 8 + hy, "p_rune", 4, 6)
            r.dot(x + (1 if not p.look else 1), 8 + hy, "p_rune", 2, 6)
    # a hex sigil drawn on the cheek
    for (x, y) in ((17, 10), (18, 11), (17, 12), (16, 11)):
        r.dot(x, y + hy, "p_rune", 2 + (f % 2), 6)
    return r


def flagellant(f):
    """A penitent: wild hair, a bare scarred chest crossed by a rope sash, a spiked club raised over the shoulder."""
    p, r = Pose(f), Rig()
    # spiked club up on the left
    r.tube([(5.0, 23.0), (4.2, 11.0)], [1.0, 1.2], "p_wood", -1)
    r.ell(4.0, 6.5, 3.4, 4.6, "p_bone", -0.9, bias=0.15)
    for (sx, sy, ex, ey) in ((1.2, 4.0, -0.8, 3.0), (2.2, 2.2, 1.0, -0.4), (5.0, 2.0, 5.8, -0.6), (6.8, 4.0, 9.2, 3.0),
                             (7.0, 7.5, 9.4, 7.8), (1.2, 8.0, -0.8, 8.8), (4.0, 6.0, 4.0, 6.0)):
        r.tube([(sx, sy), (ex, ey)], [0.8, 0.4], "p_steel", -0.8)
    r.line(2.6, 9.0, 6.0, 9.6, "p_blood", -0.7, 1)
    r.tube([(3.4, 11.0), (5.6, 10.6)], [0.8, 0.8], "p_lthr", -0.7)
    torso(r, "p_skin", p, bias=0.1)
    by = p.breath * 0.6
    # welts across the chest
    for (x0, y0, x1, y1) in ((6, 18, 10, 20), (9, 17, 12, 19), (17, 18, 21, 17), (19, 21, 23, 19), (11, 21, 14, 22)):
        r.line(x0, y0 + by, x1, y1 + by, "p_blood", 0.9, 1)
    r.dot(13.5, 19.5 + by, "p_skin", 1, 0.9)
    # the penitent's sash: a thick rope from the left shoulder to the right hip, knotted
    sash = [(6.0, 15.5), (10.0, 18.0), (14.0, 20.0), (18.0, 22.0), (21.0, 23.5)]
    r.tube([(x, y + by) for x, y in sash], [1.3] * 5, "p_rope", 1.2)
    for (x, y) in sash[:-1]:
        r.line(x - 0.6, y + by - 1.0, x + 0.6, y + by + 1.0, "p_rope", 1.3, 1)
    r.ell(16.0, 21.0 + by, 1.6, 1.4, "p_rope", 1.4)
    r.tube([(16.0, 22.0 + by), (15.0, 23.8)], [0.7, 0.6], "p_rope", 1.35)
    neck(r, p)
    face(r, p)
    hy = p.hy
    # wild hair: a dark crown with spikes everywhere
    r.ell(13.8, 4.0 + hy, 6.6, 3.6, "p_hair", 4, bias=0.1, clip=lambda x, y: y <= 5 + hy)
    spikes = [(8.0, 4.5, 5.6, 2.6), (9.4, 3.0, 8.4, -0.4), (11.6, 2.0, 11.4, -1.6), (14.0, 2.0, 14.8, -2.0),
              (16.2, 2.4, 17.8, -1.0), (18.4, 3.4, 20.8, 1.2), (19.6, 5.0, 21.6, 5.4), (8.4, 5.4, 7.0, 8.0)]
    for i, (x0, y0, x1, y1) in enumerate(spikes):
        w = 0.6 * (1 if f != 2 or i % 2 else 1.5)
        r.tube([(x0, y0 + hy), (x1 + w * (i % 2), y1 + hy)], [1.4, 0.5], "p_hair", 4.1)
    for x0 in (10.5, 13.0, 15.5, 18.0):
        r.tube([(x0, 4.0 + hy), (x0 + 0.6, 6.0 + hy)], [0.9, 0.4], "p_hair", 4.3, thin=True)
    # a fresh streak of blood down the cheek
    for (x, y, t) in ((17, 8, 2), (17, 9, 2), (18, 10, 1), (18, 11, 1)):
        r.dot(x, y + hy, "p_blood", t, 6)
    if f == 2:
        r.dot(18, 12 + hy, "p_blood", 1, 6)
    return r


def pilgrim(f):
    """A wayfarer of the faith: a wide-brimmed felt hat with a coloured band, a white tabard with a red cross, a staff."""
    p, r = Pose(f), Rig()
    # walking staff on the left with a scallop shell and a gourd hung from it
    r.tube([(4.0, 23.0), (3.2, 1.0)], [0.9, 0.8], "p_wood", -1)
    r.tube([(2.0, 3.0), (3.4, 2.0), (4.8, 3.0)], [0.6, 0.6, 0.6], "p_wood", -0.9)
    r.line(3.6, 5.0, 5.4, 9.0, "p_rope", -0.8, 2)
    r.ell(5.6, 11.0, 1.8, 2.4, "p_ochre", -0.7, bias=0.1)
    r.ell(5.2, 8.6, 1.0, 0.8, "p_ochre", -0.65)
    shell = r.ell(2.0, 13.6, 2.2, 2.0, "p_bone", -0.6, bias=0.2)
    for x in (1.0, 2.0, 3.0):
        r.line(2.0, 15.0, x, 12.4, "p_bone", -0.55, 1)
    torso(r, "p_robe", p)
    by = p.breath * 0.6
    # the tabard: a white panel down the front, a red cross on it
    r.poly([(9.0, 15.4 + by), (19.4, 15.4 + by), (20.6, 23.5), (7.8, 23.5)], "p_white_c", 0.8, normal=(-0.1, 0.1, 1.0))
    r.poly([(13.4, 17.0 + by), (15.2, 17.0 + by), (15.2, 23.5), (13.4, 23.5)], "p_red", 1.0, normal=(0, 0, 1))
    r.poly([(10.6, 19.0 + by), (18.0, 19.0 + by), (18.0, 20.6 + by), (10.6, 20.6 + by)], "p_red", 1.0, normal=(0, 0, 1))
    neck(r, p)
    face(r, p)
    hy = p.hy
    # hair under the hat at the sides
    r.tube([(8.4, 5 + hy), (8.2, 9 + hy)], [1.2, 0.7], "p_hair", 3.0, thin=True)
    r.tube([(19.4, 5 + hy), (19.6, 8 + hy)], [1.1, 0.6], "p_hair", 3.0, thin=True)
    # hat: a low crown, a band, a broad brim that droops at the sides
    r.ell(13.8, 2.8 + hy, 5.0, 3.6, "p_felt", 5, bias=0.1, clip=lambda x, y: y <= 4.6 + hy)
    r.tube([(9.0, 4.2 + hy), (18.6, 4.2 + hy)], [0.9, 0.9], "p_plume", 5.2)
    brim = [(1.5, 7.6), (4.5, 6.0), (9.0, 5.2), (13.8, 5.0), (18.6, 5.2), (23.0, 6.0), (26.0, 7.6)]
    r.tube([(x, y + hy) for x, y in brim], [1.0, 1.3, 1.4, 1.4, 1.4, 1.3, 1.0], "p_felt", 5.4, bias=0.05)
    if f == 1:
        sparkle(r, 14, 18, 1, "p_shine")
    return r


def gambler(f):
    """A card-sharp: a black tricorn trimmed in gold with a red plume, a wine coat, a cravat, a coin flipping."""
    p, r = Pose(f), Rig()
    torso(r, "p_wine", p)
    by = p.breath * 0.6
    r.poly([(10.4, 15.2 + by), (18.2, 15.2 + by), (16.6, 23.5), (12.0, 23.5)], "p_coal", 0.8, normal=(0, 0.2, 1.0))
    for y in (18.5, 21.0):
        r.dot(14.4, y + by, "p_gold", 3, 0.9)
    # coat lapels with gold piping
    r.tube([(10.0, 15.2 + by), (12.0, 23.4)], [0.8, 0.8], "p_gold", 0.95)
    r.tube([(18.6, 15.2 + by), (16.8, 23.4)], [0.8, 0.8], "p_gold", 0.95)
    neck(r, p)
    r.ell(14.4, 15.4 + by, 2.4, 1.6, "p_white_c", 1.6)
    r.ell(14.6, 17.4 + by, 1.2, 1.6, "p_white_c", 1.65)
    face(r, p)
    hy = p.hy
    # moustache and a gold earring
    for (x, y) in ((11, 10), (12, 10), (13, 10), (15, 10), (16, 10)):
        r.dot(x, y + hy, "p_black", 2, 2.5)
    r.dot(17, 11 + hy, "p_skin", 0, 2.5)
    r.ell(19.4, 10.2 + hy, 0.7, 0.9, "p_gold", 3.0)
    r.tube([(8.4, 5 + hy), (8.2, 9 + hy)], [1.2, 0.7], "p_black", 3.0, thin=True)
    # tricorn: crown, three upturned brim points, gold edging, a plume at the back
    r.poly([(5.4 + p.sway, -3.0 + hy), (8.2, 1.0 + hy), (10.6, 3.0 + hy), (8.0, 3.2 + hy), (4.6, -1.0 + hy)], "p_plume", 4.4,
           normal=(-0.4, -0.5, 0.8))
    r.ell(13.8, 2.6 + hy, 5.6, 3.4, "p_coal", 5, bias=0.25, clip=lambda x, y: y <= 4.4 + hy)
    brim = [(5.0, 2.2), (7.0, 4.6), (10.4, 5.4), (13.8, 4.6), (17.2, 5.4), (20.6, 4.6), (22.6, 2.2)]
    r.tube([(x, y + hy) for x, y in brim], [1.0, 1.4, 1.5, 1.2, 1.5, 1.4, 1.0], "p_coal", 5.2, bias=0.2)
    r.polyline([(x, y - 1.2 + hy) for x, y in brim], "p_gold", 5.4, tones=[3, 3, 2, 2, 3, 2])
    # the coin: flipping in the air at his left
    cx, cy = 4.0, [12.0, 9.0, 7.0, 9.5][f]
    w = [2.2, 0.8, 2.2, 1.4][f]
    r.ell(cx, cy, w, 2.2, "p_gold", 7, bias=0.2)
    if f == 2:
        sparkle(r, 5, 5, 1, "p_shine")
    return r


def reaver(f):
    """A northern raider: a ginger mane and braided beard, a woad stripe over the eyes, a wolf pelt, an axe."""
    p, r = Pose(f), Rig()
    # bearded axe over the right shoulder
    r.tube([(19.0, 23.0), (25.0, 2.0)], [1.0, 0.9], "p_wood", -1)
    r.poly([(23.0, 1.0), (28.0, -1.0), (28.0, 9.0), (25.0, 7.0), (24.0, 5.0)], "p_steel", -0.8, normal=(0.2, -0.3, 0.9))
    r.line(28, 0, 28, 8, "p_steel", -0.7, 4 if f == 1 else 3)
    torso(r, "p_lthr", p)
    by = p.breath * 0.6
    # the wolf pelt mantle over both shoulders, the wolf's head on the left shoulder
    r.ell(14.0, 22.0 + by, 15.0, 7.0, "p_pelt", 1.0, bias=0.15, clip=lambda x, y: y <= 19.0 + by)
    for x in range(1, 28, 2):
        r.tube([(x, 17.0 + by + (x % 3) * 0.4), (x + 0.6, 20.5 + by + (x % 4) * 0.3)], [0.6, 0.4], "p_pelt", 1.1, thin=True)
    r.ell(4.6, 15.0 + by, 3.6, 3.0, "p_pelt", 1.4, bias=0.2)
    r.poly([(2.4, 13.4 + by), (3.0, 10.4 + by), (4.6, 12.8 + by)], "p_pelt", 1.5, normal=(-0.3, -0.5, 0.8))
    r.poly([(5.4, 12.8 + by), (6.6, 10.0 + by), (7.2, 13.4 + by)], "p_pelt", 1.5, normal=(-0.3, -0.5, 0.8))
    r.ell(7.8, 16.6 + by, 2.0, 1.2, "p_pelt", 1.6, bias=0.1)
    r.dot(8.8, 16.4 + by, "p_black", 0, 1.7)
    r.dot(5.6, 14.6 + by, "p_flame", 3 if f != 3 else 2, 1.8)
    neck(r, p)
    face(r, p, brow="p_ginger")
    hy = p.hy
    # woad stripe across the eyes
    for x in range(8, 20):
        if x not in (10, 11, 14, 15):
            r.dot(x, 8 + hy, "p_woad", 2 if x < 14 else 1, 2.4)
    for x in (9, 12, 13, 16, 17, 18):
        r.dot(x, 9 + hy, "p_woad", 1, 2.4)
    # beard: a broad red beard from the cheeks, two braids hanging, beads
    r.ell(13.8, 12.6 + hy, 5.6, 4.0, "p_ginger", 3.0, bias=0.2, clip=lambda x, y: y >= 10 + hy)
    for (x, t) in ((12.0, 1), (15.6, 1)):
        r.tube([(x, 14.0 + hy), (x + 0.4, 19.0 + by)], [1.0, 0.8], "p_ginger", 3.2)
        r.ell(x + 0.4, 17.0 + by, 0.9, 0.7, "p_gold", 3.3)
    for x in range(10, 18):
        r.dot(x, 10 + hy, "p_ginger", 2 if x % 2 else 3, 3.4)
    r.dot(13, 11 + hy, "p_blood", 1, 3.5); r.dot(14, 11 + hy, "p_blood", 1, 3.5)
    # mane: a big ginger crown with locks falling past the ears
    r.ell(13.8, 3.6 + hy, 7.0, 4.4, "p_ginger", 4, bias=0.15, clip=lambda x, y: y <= 6 + hy)
    for i, (x0, y0, x1, y1) in enumerate(((7.6, 4.0, 6.4, 12.0), (8.6, 5.0, 8.0, 10.6), (19.6, 4.0, 21.0, 11.6),
                                          (18.6, 5.0, 19.4, 10.0), (9.0, 1.0, 7.4, -1.2), (12.0, 0.0, 11.6, -2.2),
                                          (15.4, 0.0, 16.2, -2.2), (18.4, 1.0, 20.2, -1.0))):
        r.tube([(x0, y0 + hy), (x1 + (p.sway * 0.6 if i < 4 else 0), y1 + hy)], [1.4, 0.6], "p_ginger", 4.1)
    for x0 in (10.0, 12.6, 15.2, 17.6):
        r.tube([(x0, 4.0 + hy), (x0 + 0.8, 6.6 + hy)], [1.0, 0.4], "p_ginger", 4.3, thin=True)
    return r


def cutpurse(f):
    """A thief: a charcoal hood, a teal cloth mask over the nose and mouth, a teal jerkin, a knife held ready."""
    p, r = Pose(f), Rig()
    torso(r, "p_coal", p)
    by = p.breath * 0.6
    r.poly([(10.8, 15.2 + by), (17.6, 15.2 + by), (16.4, 23.5), (12.0, 23.5)], "p_teal", 0.8, normal=(0, 0.2, 1.0))
    for y in (17.5, 19.5, 21.5):
        r.line(12.6, y + by, 15.8, y + by, "p_lthr", 0.9, 1)
    strap(r, p, (19.0, 15.5), (9.0, 23.5), mat="p_lthr", w=0.8, z=1.0, buckle=0.4)
    neck(r, p)
    face(r, p, brow="p_black")
    hy = p.hy
    # mask over nose and mouth, knotted behind
    r.poly([(8.2, 9.0 + hy), (19.8, 9.0 + hy), (19.4, 12.6 + hy), (14.0, 14.2 + hy), (8.6, 12.6 + hy)], "p_teal", 3.0,
           normal=(-0.15, 0.1, 1.0))
    r.line(8.6, 9.0 + hy, 19.6, 9.0 + hy, "p_teal", 3.1, 3)
    r.tube([(14.6, 10.0 + hy), (14.8, 13.2 + hy)], [0.5, 0.5], "p_teal", 3.2, bias=-0.4)
    hood(r, p, "p_coal", low=5.2)
    # knife held up beside the face, point up
    kx, ky = 23.4, [10.0, 9.6, 9.0, 9.6][f]
    r.tube([(kx, ky + 7.0), (kx, ky + 3.0)], [1.0, 1.0], "p_lthr", 6)
    r.tube([(kx - 2.0, ky + 2.6), (kx + 2.0, ky + 2.6)], [0.7, 0.7], "p_iron", 6.2)
    r.poly([(kx - 1.2, ky + 2.2), (kx + 1.2, ky + 2.2), (kx + 0.8, ky - 4.0), (kx, ky - 6.6), (kx - 0.8, ky - 4.0)], "p_steel",
           6.1, normal=(-0.4, -0.2, 0.9))
    r.ell(kx - 0.6, ky + 8.4, 1.8, 1.6, "p_skin", 6.3, bias=0.2)
    if f == 2:
        sparkle(r, int(kx), int(ky - 6), 1)
    return r


def arbalist(f):
    """A crossbowman: a broad-brimmed kettle hat, a quilted oxblood jack, a beard, the crossbow on his shoulder."""
    p, r = Pose(f), Rig()
    # crossbow over the left shoulder: stock rising to the upper left, the steel prod across it
    r.tube([(9.0, 18.0), (2.0, 4.0)], [1.4, 1.1], "p_wood", -1)
    prod = [(-1.0, 9.0), (1.2, 6.6), (3.0, 5.0), (5.0, 3.4), (7.4, 1.6)]
    r.tube(prod, [0.8] * 5, "p_steel", -0.8)
    r.line(-1.0, 9.0, 4.4, 8.2, "p_bone", -0.9, 2)
    r.line(7.4, 1.6, 4.4, 8.2, "p_bone", -0.9, 2)
    r.ell(3.0, 5.0, 1.2, 1.2, "p_iron", -0.7)
    torso(r, "p_oxblood", p)
    by = p.breath * 0.6
    # quilting: diamond stitch lines on the jack
    for k in range(-3, 4):
        r.line(6 + k * 4, 16 + by, 12 + k * 4, 23.5, "p_oxblood", 0.9, 1)
    r.tube([(9.0, 15.5 + by), (19.8, 15.5 + by)], [1.1, 1.1], "p_ochre", 1.0)
    neck(r, p)
    face(r, p)
    hy = p.hy
    # beard: short, brown, along the jaw and chin
    r.ell(13.8, 12.2 + hy, 5.0, 3.2, "p_hair", 2.6, bias=0.2, clip=lambda x, y: y >= 10 + hy)
    for (x, y) in ((11, 10), (12, 10), (15, 10), (16, 10)):
        r.dot(x, y + hy, "p_hair", 2, 2.8)
    r.dot(13, 11 + hy, "p_skin", 1, 2.9); r.dot(14, 11 + hy, "p_skin", 0, 2.9)
    # chapel-de-fer: a low steel dome on a wide drooping brim
    r.ell(13.8, 3.2 + hy, 5.4, 4.0, "p_steel", 5, bias=0.0, clip=lambda x, y: y <= 5.2 + hy)
    r.tube([(13.8, -0.4 + hy), (13.8, 4.6 + hy)], [0.5, 0.5], "p_steel", 5.1, bias=0.4)
    brim = [(2.0, 8.4), (5.0, 7.0), (9.0, 5.8), (13.8, 5.6), (18.6, 5.8), (22.6, 7.0), (25.6, 8.4)]
    r.tube([(x, y + hy) for x, y in brim], [0.9, 1.2, 1.3, 1.3, 1.3, 1.2, 0.9], "p_steel", 5.3, bias=-0.1)
    if f == 1:
        sparkle(r, 10, 2 + hy, 1)
    return r


def scholar(f):
    """A grey sage: white hair in a bun, gold spectacles, a midnight robe with a gold stole, a candle lantern."""
    p, r = Pose(f), Rig()
    torso(r, "p_navy", p)
    by = p.breath * 0.6
    for (a, b) in (((10.4, 15.2), (9.4, 23.5)), ((18.4, 15.2), (19.4, 23.5))):
        r.tube([(a[0], a[1] + by), (b[0], b[1])], [1.4, 1.6], "p_gold", 1.0)
    for y in (18.0, 21.0):
        r.dot(9.6, y + by, "p_navy", 1, 1.1); r.dot(19.2, y + by, "p_navy", 1, 1.1)
    neck(r, p)
    face(r, p, brow="p_white", brow_tone=2)
    hy = p.hy
    # wrinkles and a long white moustache
    r.dot(9, 9 + hy, "p_skin", 1, 2.4); r.dot(18, 9 + hy, "p_skin", 1, 2.4)
    for (x, y) in ((11, 10), (12, 10), (13, 10), (15, 10), (16, 10), (11, 11), (17, 11)):
        r.dot(x, y + hy, "p_white", 3 if x < 14 else 2, 2.5)
    # spectacles: gold rims, glass catching the light
    for cx in (11, 15):
        for (x, y) in ((0, -1), (1, -1), (-1, 0), (2, 0), (0, 1), (1, 1)):
            r.dot(cx + x, 8 + y + hy, "p_gold", 3 if y < 0 else 2, 3.0)
    if f == 2:
        r.dot(11, 8 + hy, "p_shine", 4, 3.1); r.dot(15, 8 + hy, "p_shine", 3, 3.1)
    # white hair: thin on top, a bun, wisps over the ears
    r.ell(13.8, 3.6 + hy, 6.2, 3.4, "p_white", 4, bias=0.1, clip=lambda x, y: y <= 5 + hy)
    r.ell(15.4, 0.4 + hy, 2.8, 2.2, "p_white", 4.2, bias=0.1)
    r.tube([(13.0, 0.4 + hy), (17.6, -0.6 + hy)], [0.5, 0.5], "p_gold", 4.4)
    for (x0, y0, x1, y1) in ((8.0, 4.0, 6.6, 9.0), (8.6, 5.0, 7.8, 10.4), (19.6, 4.0, 21.0, 9.4), (19.0, 5.0, 19.8, 9.6)):
        r.tube([(x0, y0 + hy), (x1 + p.sway * 0.5, y1 + hy)], [1.0, 0.4], "p_white", 4.1, thin=True)
    # candle lantern in the lower left
    lx, ly = 4.4, 18.0
    r.poly([(lx - 2.6, ly - 4.0), (lx + 2.6, ly - 4.0), (lx + 1.6, ly - 6.0), (lx - 1.6, ly - 6.0)], "p_gold", 5,
           normal=(-0.2, -0.6, 0.8))
    r.tube([(lx, ly - 6.0), (lx, ly - 8.0)], [0.5, 0.5], "p_gold", 5)
    for yy in range(int(ly - 4), int(ly + 4)):
        for xx in range(int(lx - 2), int(lx + 3)):
            d = math.hypot((xx - lx) * 1.2, (yy - ly + 0.5) * 0.7)
            r.put(xx, yy, 5.0, "p_flame", 0.5, r.part(True, 5.0), 4 if d < 0.8 + 0.3 * (f % 2) else 3 if d < 1.6 else 1)
    for xx in (lx - 2.6, lx + 2.6):
        r.line(xx, ly - 4, xx, ly + 4, "p_gold", 5.2, 3 if xx < lx else 1)
    r.tube([(lx - 2.8, ly + 4.6), (lx + 2.8, ly + 4.6)], [0.8, 0.8], "p_gold", 5.2)
    for i, (x, y) in enumerate(((lx - 3, ly - 9), (lx + 2, ly - 11))):
        r.dot(x + (f % 2), y - (f % 3), "p_flame", 3 if i == f % 2 else 2, 8)
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


def build():
    rows = []
    for name in ORDER:
        if name not in ORIGINS: continue
        ims = frames(name)
        pack("Hero" + name, ims)
        rows.append(ims)
        print("built Hero" + name)
    board(rows, os.path.join(OUT, "board_origins.png"))
    return rows


if __name__ == "__main__":
    build()
