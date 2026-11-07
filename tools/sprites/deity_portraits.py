"""The god select portraits (29 x 24, Idle 4) of the eight v2 gods, drawn to the standard of DeityZhekra
(zhekra_v2_fx.portrait): the god itself, a face or bust, fills the frame; an ornate headpiece rises to the top edge and
reaches out to the sides; glowing eyes are the focal point; the shoulders or collar fill the bottom edge; and behind it
a full-bleed coloured backdrop (a glow behind the head, the god's own pattern) instead of an empty frame. Each figure is
drawn with the shared material renderer (jinx_v2_rigs.Rig: lit shapes, 3 tones a material, top-left key light), then
laid over its backdrop with a back rim light in the god's glow colour on its top and right edges and a 1 px shadow on
the backdrop under its bottom and right edges, so the silhouette reads at 1x.

Every god's v2 fx rig calls frames(god, origin) for its Deity<God> sheet and keeps its own sheet name, cell, origin,
anim name, frame count and timings:

    from deity_portraits import frames
    fx("DeityJinx", (29, 24), PO, [("Idle", frames("jinx", PO), [0.35, 0.12, 0.3, 0.2])], out)

Drawing coordinates: x -14..14 left to right, y -23 (top row) .. 0 (bottom row), the cell's bottom centre at (0, 0).
The materials are all named dp_* so they never collide with a god's own ramps in the shared J.RAMPS.

    python3 deity_portraits.py [outdir]     writes <outdir>/deity_portraits.png, the eight at 1x and 6x (a quick look)
"""
import math, os, sys, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402  (the renderer: Rig, ramps, resolve)
from jinx_v2_rigs import Rig, harl  # noqa: E402
from anim import SprRGB  # noqa: E402

GODS = ("jinx", "vhorrul", "ossivar", "sylvene", "umbrael", "belmora", "kaurn", "ysveld")


def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


# ================================================================== palette (ink, shadow, base, light, hi)
DP_RAMPS = {
    # Jinx: harlequin crimson and black, greasepaint ivory, tarnished gold, violet luck
    "dp_crim":   ["2a0a1a", "5e1426", "962230", "c4423a", "e87a58"],
    "dp_blk":    ["120e1a", "2a2036", "463a58", "665a7c", "8a7ca4"],
    "dp_paint":  ["3a2a36", "8a7a86", "cec2c4", "eee6e0", "fffaf4"],
    "dp_gold":   ["2e1a10", "6e4618", "a8782a", "dcb04a", "fbe796"],
    "dp_mouth":  ["14060e", "2e0a16", "4e1020", "6e1a2a", "8e2434"],
    # Vhorrul: tallow cream, soot umber, votive red, beeswax amber
    "dp_tallow": ["3a281c", "8a6e52", "c8ac84", "e8d4ac", "fff4da"],
    "dp_votive": ["220608", "521014", "841c1c", "b4342a", "d65e3e"],
    "dp_soot":   ["120c0a", "281c16", "40302a", "5a463a", "76604e"],
    "dp_wax":    ["2a1408", "6a3a10", "a8661c", "dc9a34", "fcd478"],
    # Ossivar: bone ivory, iron black, verdigris bronze, funeral violet
    "dp_bone":   ["2e2420", "6e6052", "b0a084", "d8ccae", "f6eed6"],
    "dp_iron":   ["0e0c10", "201e26", "36323e", "504a58", "6e6876"],
    "dp_verd":   ["0c1a16", "1a3a30", "2e5e4a", "4a8a68", "7cb894"],
    "dp_bronze": ["1e1006", "4a2c10", "7c4e1e", "aa783a", "d4a862"],
    "dp_fun":    ["120818", "2a1236", "442056", "623478", "8a50a0"],
    # Sylvene: bark, rot green, pod pink, bruise purple, mould white
    "dp_bark":   ["160e0a", "362418", "5a3c2a", "7c5a3e", "a07a56"],
    "dp_leaf":   ["0e1a0a", "22401a", "3e6626", "5e8a36", "8cb256"],
    "dp_pink":   ["3a1424", "7e2e4a", "bc5a72", "e48ea0", "fcc8d0"],
    "dp_bruise": ["160a1c", "34163e", "562a62", "7c4886", "a070aa"],
    "dp_mould":  ["3a3a34", "7a7a6c", "b4b4a0", "d8d8c6", "f4f4e6"],
    # Umbrael: void, porcelain mask, mirror silver, glass
    "dp_void":   ["08060e", "18122a", "2a2042", "3e325c", "56487a"],
    "dp_mask":   ["2e2a3a", "6e6880", "b0aac0", "dcd8e8", "fcfaff"],
    "dp_mirror": ["1a1a26", "44465a", "767a90", "aab0c4", "e2e6f0"],
    "dp_glass":  ["0e2030", "1e4a62", "3a7e98", "6ab8cc", "c4f2fa"],
    # Bel'Mora: drowned skin, bell bronze, verdigris, kelp, barnacle grey
    "dp_drown":  ["0e1e1e", "22403e", "3e6a64", "629488", "92bcaa"],
    "dp_bell":   ["1e1006", "4e3010", "845620", "b4823a", "dcb46a"],
    "dp_verdi":  ["0a1e1a", "164036", "24685a", "3a9a80", "72ccb0"],
    "dp_kelp":   ["0a160a", "183218", "2a5024", "3e7034", "5e9448"],
    "dp_barn":   ["1a1c1e", "3a3e42", "5e6468", "868c8e", "b0b4b2"],
    "dp_wood":   ["3a2414", "6e4a2e", "a07450", "c89e70", "ecca98"],   # Sylvene's face bark, lit
    "dp_kskin":  ["1e1a1c", "463a3a", "70605c", "9c8a82", "c8b8aa"],   # Kaurn's forge-lit iron skin
    "dp_wleg":   ["0a0a12", "16182a", "262a42", "3a4262", "5a6a90"],   # the widow's legs, black with a blue sheen
    # Kaurn: forge iron, copper, brass
    "dp_kiron":  ["101216", "262a32", "40464f", "5e6670", "848c96"],
    "dp_copper": ["240c06", "5a220e", "944220", "c46a36", "eca066"],
    "dp_brass":  ["2a1a06", "6a4a12", "a8802a", "d8b44a", "f8e490"],
    # Ysveld: frost skin, ice, silk grey, crystal violet, widow red
    "dp_frost":  ["2a3040", "6a7890", "a8b8cc", "d4e0ec", "f6faff"],
    "dp_ice":    ["0e2440", "1e4a7a", "3a7ab4", "6eaee0", "bce4fc"],
    "dp_silk":   ["1a1c26", "3a3e4c", "626878", "9298a8", "c4c8d4"],
    "dp_crys":   ["1a1236", "3a2a6a", "5e4ea0", "8a7ccc", "bcb0f0"],
    "dp_widow":  ["2a060a", "641018", "a21e22", "d24a3a", "f48a6a"],
    # emissive: eyes, flames, sparks (keep their drawn tones, never outlined)
    "dp_lucky":  ["3a1a5a", "7a3aa8", "b46ae0", "d8a8f4", "f8ecff"],   # Jinx violet
    "dp_flame":  ["5a1a0a", "b8401a", "f07a24", "ffc04a", "fff4c0"],   # Vhorrul flame
    "dp_marrow": ["4a0a08", "9a1a12", "e03a22", "ff7a4a", "ffd0a8"],   # Ossivar marrow red
    "dp_pollen": ["4a3a06", "8a7210", "d4b824", "f4e05a", "fffac0"],   # Sylvene pollen
    "dp_lilac":  ["3a2a5a", "6a50a0", "9a80d8", "c8b4f4", "f4eeff"],   # Umbrael cold lilac
    "dp_cyan":   ["0e3a4a", "1e7090", "3ab0d0", "7ae0f4", "e0feff"],   # Umbrael glass light
    "dp_lure":   ["0a3a4a", "1a7a90", "2ac0dc", "80ecf8", "e8ffff"],   # Bel'Mora lure cyan
    "dp_foam":   ["2a4a50", "5a8a90", "9ac4c8", "cce8e8", "f4ffff"],
    "dp_storm":  ["1a3a6a", "3a6ab0", "7aaaf0", "c4e0ff", "ffffff"],   # Kaurn storm blue-white
    "dp_ember":  ["4a0c0a", "a0200e", "e8501a", "ffa040", "fff0a0"],
    "dp_rime":   ["1a4a7a", "3a8ac8", "7ac8f8", "c8eeff", "ffffff"],   # Ysveld ice light
}
J.RAMPS.update({k: [_h(c) for c in v] for k, v in DP_RAMPS.items()})
J.EMISSIVE.update({"dp_lucky", "dp_flame", "dp_marrow", "dp_pollen", "dp_lilac", "dp_cyan", "dp_lure", "dp_foam",
                   "dp_storm", "dp_ember", "dp_rime"})
J.SHINY.update({"dp_gold", "dp_paint", "dp_tallow", "dp_wax", "dp_bone", "dp_bronze", "dp_verd", "dp_mask",
                "dp_mirror", "dp_glass", "dp_bell", "dp_copper", "dp_brass", "dp_frost", "dp_ice", "dp_crys"})
RAMPS = J.RAMPS
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
X0, X1, Y0, Y1 = -14, 14, -23, 0


def C(m, t):
    return RAMPS[m][t]


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def cells():
    for y in range(Y0, Y1 + 1):
        for x in range(X0, X1 + 1):
            yield x, y


def dith(x, y):
    return BAYER[(y - Y0) % 4][(x - X0) % 4] / 16.0 - 0.47


# ================================================================== the backdrop and the composite
def glow_bg(cols, cx=0.0, cy=-12.0, rx=13.0, ry=11.0, gain=3.0):
    """A full-bleed backdrop: cols[0] at the frame, a dithered glow up to cols[-1] behind the head."""
    px = {}
    n = len(cols) - 1
    for x, y in cells():
        d = math.hypot((x - cx) / rx, (y - cy) / ry)
        v = max(0.0, 1.0 - d) * gain + dith(x, y) + 0.5
        px[(x, y)] = cols[max(0, min(n, int(v)))]
    return px


def compose(fg, bg, rim, rim_a=0.55, shade=None, shade_a=0.55):
    """fg (a resolved SprRGB) over bg (dict). Its top and right edges against the backdrop take the back rim light;
    the backdrop just right of and under it takes a 1 px shadow, so the silhouette separates at 1x."""
    F = {k: c for k, c in fg.px.items() if X0 <= k[0] <= X1 and Y0 <= k[1] <= Y1}
    tones = getattr(fg, "tones", {})
    inside = lambda q: q in F or not (X0 <= q[0] <= X1 and Y0 <= q[1] <= Y1)
    out = dict(bg)
    for k, c in F.items():
        m = tones.get(k, (None, 2))[0]
        x, y = k
        if rim is not None and m not in J.EMISSIVE:
            # only where the shape is at least 3 px thick across that edge: thin limbs and branches keep their colour
            if (not inside((x + 1, y)) and (x - 1, y) in F and (x - 2, y) in F) or \
                    (not inside((x, y - 1)) and (x, y + 1) in F and (x, y + 2) in F):
                c = mix(c, rim, rim_a)
        out[k] = c
    if shade is not None:
        for k in bg:
            if k in F: continue
            x, y = k
            if (x - 1, y) in F or (x, y - 1) in F:
                out[k] = mix(bg[k], shade, shade_a)
    s = SprRGB(out); s.tones = tones
    return s


def eye(r, cx, cy, mat, z, rx=1.4, ry=0.9, ang=0.0, sock=None, srx=None, sry=None, core=4, hot=False):
    """A glowing eye: a dark socket, the lit iris (emissive) and a white-hot core."""
    if sock:
        r.ell(cx, cy, srx or rx + 0.9, sry or ry + 0.8, sock, z - 0.01, flat=0, ang=ang)
    r.ell(cx, cy, rx, ry, mat, z, flat=3, ang=ang)
    r.dot(cx, cy, mat, core, z + 0.01)
    if hot:
        r.dot(cx - 1, cy, mat, 4, z + 0.01)


def spark(r, x, y, mat, z, big=False):
    r.dot(x, y, mat, 4, z)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        r.dot(x + dx, y + dy, mat, 2, z - 0.001)
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            r.dot(x + dx, y + dy, mat, 1, z - 0.002)


def done(r):
    return r.resolve(floor=False, cast=False)


# ================================================================== Jinx, the Grinning Jester
def jinx(k):
    """A harlequin's painted face, sly and narrow, a crimson diamond over one eye and a black one over the other, both
    eyes lit violet with luck, a wide red grin; a three-pointed cap with gold bells reaching to the corners, a gold
    band, and a ruff over a diamond doublet. k: 0 rest, 1 the lucky eye flares, 2 the bells swing, 3 a wink."""
    r = Rig()
    sway = (0.0, 0.0, 1.0, 0.5)[k]
    # the doublet and ruff
    r.poly([(-15, 1), (-14, -3), (-8, -5), (8, -5), (14, -3), (15, 1)], harl(0, -1, 3.0, "dp_crim", "dp_blk"), -1.0,
           normal=(0, -0.4, 0.9), curve=0.5)
    for i in range(8):
        x = -10.5 + i * 3.0
        y0 = -5.4 + abs(x) * 0.12
        m = "dp_crim" if i % 2 else "dp_blk"
        r.poly([(x - 1.7, y0), (x + 1.7, y0), (x, y0 + 3.6)], m, -0.5 + i * 0.001, normal=(0, -0.2, 1.0))
        r.dot(x, y0 + 4.0, "dp_gold", 4 if (i + k) % 3 == 0 else 3, -0.49 + i * 0.001)
    r.tube([(-12.0, -5.2), (0, -5.8), (12.0, -5.2)], [0.8, 0.9, 0.8], "dp_gold", -0.45, bias=0.15)
    # the cap: three points, crimson, black, crimson, a gold bell on each
    caps = [((-3.5, -16.5), (-9.0, -21.5 + sway * 0.3), (-13.0 - sway * 0.5, -19.5), (-13.0 - sway, -14.0), "dp_crim"),
            ((3.5, -16.5), (9.0, -21.5 - sway * 0.3), (13.0 + sway * 0.5, -19.5), (13.0 + sway, -14.0), "dp_blk"),
            ((0.0, -18.0), (-0.5, -21.0), (2.0, -23.0), (6.0 + sway, -22.5), "dp_crim")]
    for i, (a, b, c, d, m) in enumerate(caps):
        r.tube([a, b, c, d], [3.2, 2.4, 1.5, 0.8], m, 0.5 + i * 0.02, bias=0.1)
        bx, by = d[0], d[1] + (1.6 if i < 2 else 0.8)
        r.ell(bx, by, 1.5, 1.4, "dp_gold", 0.6 + i * 0.02, bias=0.4)
        r.dot(bx - 0.5, by - 0.5, "dp_gold", 4, 0.61 + i * 0.02)
        r.dot(bx, by + 1, "dp_gold", 0, 0.61 + i * 0.02)
    r.ell(0, -18.2, 6.8, 2.4, "dp_crim", 0.45, bias=0.1)
    # the face: narrow, high cheekbones, a pointed chin
    r.ell(0, -11.4, 5.4, 5.6, "dp_paint", 1.0, bias=0.12)
    r.poly([(-5.0, -10.0), (5.0, -10.0), (1.8, -4.4), (0.0, -3.6), (-1.8, -4.4)], "dp_paint", 1.0, normal=(0, 0.2, 1.0), curve=0.6)
    # the band over the brow, a gem in the middle
    r.tube([(-6.4, -15.4), (0.0, -16.4), (6.4, -15.4)], [1.1, 1.2, 1.1], "dp_gold", 1.5, bias=0.15)
    r.ell(0, -16.2, 1.2, 1.1, "dp_lucky", 1.6, flat=3); r.dot(0, -16.4, "dp_lucky", 4, 1.61)
    # the diamonds and the eyes
    for sx, m in ((-1, "dp_crim"), (1, "dp_blk")):
        cx, cy = sx * 2.6, -11.0
        r.poly([(cx, cy - 4.2), (cx + 1.8, cy), (cx, cy + 3.4), (cx - 1.8, cy)], m, 1.1, flat=2)
        if sx > 0 and k == 3:
            r.polyline([(cx - 1.4, cy), (cx, cy + 0.7), (cx + 1.4, cy)], "dp_lucky", 1.2, tone=2)
        else:
            eye(r, cx, cy, "dp_lucky", 1.2, rx=1.6, ry=1.1, ang=sx * -12, core=4, hot=(k == 1))
    # the grin: red lips curling up to the cheeks, a dark mouth, two teeth
    r.polyline([(-4.4, -8.4), (-3.4, -7.0), (-1.8, -6.0), (0.0, -5.8), (1.8, -6.0), (3.4, -7.0), (4.4, -8.4)], "dp_mouth", 1.21,
               tones=[1, 1, 1, 1, 1, 1])
    r.polyline([(-3.0, -6.0), (-1.6, -5.0), (0.0, -4.8), (1.6, -5.0), (3.0, -6.0)], "dp_crim", 1.21, tones=[3, 3, 2, 2])
    r.dot(0.4, -8.8, "dp_paint", 1, 1.15)
    s = done(r)
    # the curtain: big dim harlequin diamonds, a violet bloom behind the head, sparks of luck
    base = glow_bg([C("dp_blk", 0), C("dp_blk", 1), C("dp_lucky", 0), C("dp_lucky", 1)], cy=-12, gain=2.8)
    for (x, y) in list(base):
        if (math.floor((x + y * 1.2) / 5.0) + math.floor((x - y * 1.2) / 5.0)) % 2 == 0:
            base[(x, y)] = mix(base[(x, y)], C("dp_crim", 1), 0.45)
    for i, (x, y) in enumerate(((-11, -7), (11, -9), (-9, -1), (12, -2))):
        if (i + k) % 2 == 0:
            base[(x, y)] = C("dp_lucky", 4)
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in base: base[q] = mix(base[q], C("dp_lucky", 2), 0.7)
    return compose(s, base, C("dp_lucky", 3), 0.5, shade=C("dp_blk", 0))


# ================================================================== Vhorrul, the Tallow Saint
def vhorrul(k):
    """The Tallow Saint: a serene face of tallow melting down over itself, the eyes two hollows full of flame, under a
    votive-red cowl; a crown of five candles burns on its head inside a gold halo. k flickers the flames and lets one
    drip creep."""
    r = Rig()
    # the cowl and the shoulders
    r.poly([(-15, 1), (-14, -4), (-11, -10), (-9.5, -15), (-6, -18), (0, -18.8), (6, -18), (9.5, -15), (11, -10), (14, -4), (15, 1)],
           "dp_votive", -1.0, normal=(0, -0.2, 1.0), curve=0.8)
    r.poly([(-7.5, 1), (-8.0, -10), (-6.5, -15.5), (0, -17), (6.5, -15.5), (8.0, -10), (7.5, 1)], "dp_soot", -0.8, flat=0)
    r.polyline([(-11.5, 0), (-11.0, -8), (-9.6, -14), (-6.4, -17.4), (0, -18.2), (6.4, -17.4), (9.6, -14), (11.0, -8), (11.5, 0)],
               "dp_gold", -0.7, tones=[3, 3, 4, 4, 3, 3, 2, 2])
    # the face
    r.ell(0, -10.4, 5.4, 6.0, "dp_tallow", 0.0, bias=0.1)
    r.poly([(-4.6, -8.0), (4.6, -8.0), (2.0, -3.4), (-2.0, -3.4)], "dp_tallow", 0.0, normal=(0, 0.25, 1.0), curve=0.6)
    # the melt: wax runs from the brow down the cheeks and off the chin
    drip_len = (0.0, 0.5, 1.0, 1.5)[k]
    for x, y0, ln in ((-4.4, -14, 6.0), (-1.4, -15, 2.0), (4.0, -14, 7.5 + drip_len), (1.4, -15, 1.5), (0.8, -4, 2.5)):
        r.tube([(x, y0), (x, y0 + ln)], [0.6, 0.8], "dp_tallow", 0.3, bias=0.4)
        r.dot(x, y0 + ln + 0.6, "dp_tallow", 4, 0.31)
    r.ell(0, -15.2, 5.6, 1.3, "dp_tallow", 0.25, bias=0.35)
    # the eyes: deep hollows with flame in them
    for sx in (-1, 1):
        cx = sx * 2.4
        r.ell(cx, -10.6, 1.9, 1.7, "dp_soot", 0.4, flat=0)
        eye(r, cx, -10.4, "dp_flame", 0.5, rx=1.4, ry=1.1, core=4, hot=(k == 2))
        r.dot(cx, -12.0, "dp_flame", 2 if (k + (sx > 0)) % 2 else 1, 0.52)
    r.dot(0.4, -8.2, "dp_tallow", 1, 0.35)
    r.polyline([(-1.0, -5.8), (1.0, -5.8)], "dp_soot", 0.35, tone=1)
    # the crown of candles: tall in the middle, each with its flame
    for i, (x, h) in enumerate(((-7.4, 2.6), (-3.8, 4.2), (0.0, 5.0), (3.8, 4.2), (7.4, 2.6))):
        base_y = -16.0 + abs(x) * 0.2
        top = base_y - h
        r.tube([(x, base_y), (x, top)], [0.9, 0.9], "dp_wax" if i % 2 else "dp_tallow", 0.6 + i * 0.01, bias=0.15)
        r.dot(x - 0.4, top + 0.6, "dp_tallow", 4, 0.62 + i * 0.01)
        r.dot(x + 0.6, top + 1.6, "dp_tallow", 3, 0.62 + i * 0.01)          # a drip down its side
        f = (k + i) % 3
        lean = (0, 1, -1)[f] * 0.5
        r.dot(x, top - 1, "dp_flame", 3, 0.7)
        r.dot(x + 1 if f == 1 else x - 1 if f == 2 else x, top - 1, "dp_flame", 1, 0.69)
        r.dot(x + lean, top - 2, "dp_flame", 3, 0.7)
        r.dot(x + lean * 2, top - 3, "dp_flame", 2, 0.7)
        if i == 2 or f == 0: r.dot(x + lean * 2, top - 4, "dp_flame", 1, 0.7)
        r.dot(x, top - 1, "dp_flame", 4, 0.71)
    r.tube([(-8.2, -15.0), (0, -16.2), (8.2, -15.0)], [0.7, 0.8, 0.7], "dp_gold", 0.8, bias=0.15)
    r.ell(0, -1.2, 1.6, 1.4, "dp_wax", 0.2, bias=0.2)
    r.dot(0, -1.6, "dp_flame", 3, 0.3)
    s = done(r)
    # the chapel: soot dark, the candlelight glowing behind the head, a gold halo, far votives at the sides
    base = glow_bg([C("dp_soot", 0), C("dp_soot", 1), C("dp_votive", 1), C("dp_wax", 1)], cy=-16, rx=14, ry=11, gain=3.0)
    for i in range(72):
        a = i / 72.0 * math.tau
        q = (int(round(11.5 * math.cos(a))), int(round(-15.0 + 7.5 * math.sin(a))))
        if q in base: base[q] = C("dp_gold", 2 if q[0] < 0 else 1)
    for x in (-13, 13):
        for y in (-12, -8, -4):
            f = (k + y) % 2
            base[(x, y)] = C("dp_flame", 3 if f else 2)
            base[(x, y - 1)] = C("dp_flame", 1 + f)
            base[(x, y + 1)] = C("dp_tallow", 1)
    return compose(s, base, C("dp_flame", 3), 0.45, shade=C("dp_soot", 0))


# ================================================================== Ossivar, the Marrow King
def ossivar(k):
    """The Marrow King: a crowned skull, marrow-red fire in its sockets, a bronze crown with bone spikes and garnets, a
    funeral-violet mantle over bone pauldrons, the ribs bare on a dark chest, before a charnel wall of stacked bones."""
    r = Rig()
    # the mantle, the dark chest and its ribs, the bone pauldrons
    r.poly([(-15, 1), (-14, -4), (-9, -6.5), (9, -6.5), (14, -4), (15, 1)], "dp_fun", -1.2, normal=(0, -0.4, 0.9), curve=0.6)
    r.poly([(-6.5, 1), (-5.5, -6), (5.5, -6), (6.5, 1)], "dp_iron", -1.0, flat=0)
    for j in range(3):
        y = -5.0 + j * 2.0
        for sx in (-1, 1):
            r.polyline([(sx * 1.0, y), (sx * 3.0, y - 0.6), (sx * 4.6, y + 0.4), (sx * 5.2, y + 1.4)], "dp_bone", -0.8,
                       tones=[3 if sx < 0 else 2, 2, 1])
    r.tube([(0, -6), (0, 1)], [0.6, 0.6], "dp_bone", -0.75, bias=0.15)
    for sx in (-1, 1):
        r.ell(sx * 11.0, -3.0, 3.6, 2.4, "dp_bone", -0.6, bias=0.1)
        r.polyline([(sx * 8.0, -2.0), (sx * 14.0, -1.6)], "dp_bone", -0.59, tone=1)
        for j, (bx, ln) in enumerate(((9.0, 3.0), (11.4, 4.0), (13.6, 3.0))):
            r.tube([(sx * bx, -4.6), (sx * (bx + 0.8), -4.6 - ln)], [0.9, 0.3], "dp_bone", -0.58 + j * 0.001, bias=0.2)
    # the skull
    r.ell(0, -12.8, 6.2, 5.8, "dp_bone", 0.0, bias=0.12)
    r.poly([(-5.4, -10.4), (5.4, -10.4), (4.4, -7.0), (-4.4, -7.0)], "dp_bone", 0.0, normal=(0, 0.1, 1.0), curve=0.6)
    r.poly([(-3.8, -7.2), (3.8, -7.2), (3.0, -4.4), (-3.0, -4.4)], "dp_bone", 0.05, normal=(0, 0.3, 1.0), curve=0.6)
    r.ell(-5.4, -9.8, 1.2, 1.0, "dp_bone", 0.06, bias=0.25); r.ell(5.4, -9.8, 1.2, 1.0, "dp_bone", 0.06, bias=0.1)
    # the sockets with the marrow fire, the nose, the teeth
    for sx in (-1, 1):
        cx = sx * 2.6
        r.ell(cx, -11.4, 2.2, 2.0, "dp_iron", 0.2, flat=0)
        eye(r, cx, -11.2, "dp_marrow", 0.3, rx=1.5, ry=1.1, core=4, hot=(k == 1))
        r.dot(cx, -13.0, "dp_marrow", 2 if (k + (sx > 0)) % 2 else 1, 0.32)
    r.poly([(-0.9, -9.2), (0.9, -9.2), (0.0, -7.6)], "dp_iron", 0.2, flat=0)
    r.polyline([(-3.2, -6.8), (3.2, -6.8)], "dp_iron", 0.26, tone=1)
    for x in range(-3, 4):
        r.dot(x, -6.0, "dp_bone", 4 if x < 0 else 3, 0.25)
        r.dot(x, -5.0, "dp_bone", 2, 0.25)
    r.polyline([(-3.0, -5.5), (3.0, -5.5)], "dp_iron", 0.26, tone=0)
    for x in (-2, 0, 2):
        r.dot(x, -6.0, "dp_bone", 1, 0.27)
    # the crown: a bronze band green with age, bone spikes, garnets
    r.poly([(-6.8, -15.4), (6.8, -15.4), (6.4, -17.8), (-6.4, -17.8)], "dp_bronze", 0.6, normal=(0, -0.2, 1.0), curve=0.7)
    for x in (-5.0, -1.6, 1.6, 5.0):
        r.dot(x, -15.8, "dp_verd", 3, 0.61); r.dot(x + 0.6, -15.6, "dp_verd", 2, 0.61)
    for i, (x, h) in enumerate(((-6.4, 3.0), (-3.4, 4.4), (0.0, 5.6), (3.4, 4.4), (6.4, 3.0))):
        r.tube([(x, -17.6), (x * 1.2, -17.6 - h)], [1.1, 0.4], "dp_bone", 0.55 + i * 0.01, bias=0.18)
        r.dot(x * 1.2, -17.6 - h, "dp_bone", 4, 0.56 + i * 0.01)
    for x in (-3.4, 0.0, 3.4):
        r.ell(x, -16.6, 0.9, 0.9, "dp_marrow", 0.65, flat=2 if x else 3)
        r.dot(x - 0.3, -16.8, "dp_marrow", 4, 0.66)
    s = done(r)
    # the charnel wall: stacked long bones, a violet gloom behind the crown
    base = glow_bg([C("dp_iron", 0), C("dp_fun", 0), C("dp_fun", 1), C("dp_fun", 2)], cy=-14, gain=2.8)
    for (x, y) in list(base):
        row = (y - Y0) // 3
        if (y - Y0) % 3 == 1:
            xo = (x + row * 3) % 7
            if xo in (0, 6):
                base[(x, y)] = mix(base[(x, y)], C("dp_bone", 1), 0.6)
            elif xo != 3:
                base[(x, y)] = mix(base[(x, y)], C("dp_bone", 1), 0.3)
    for i, (x, y) in enumerate(((-11, -19), (11, -17), (-12, -11), (12, -12))):
        if (i + k) % 3 == 0:
            base[(x, y)] = C("dp_marrow", 3)
    return compose(s, base, C("dp_marrow", 3), 0.4, shade=C("dp_iron", 0))


# ================================================================== Sylvene, the Rot Orchard
def sylvene(k):
    """The Rot Orchard: a face of old bark, pollen-gold light in its eyes, mould creeping over one cheek; a crown of
    branches spreads to the corners with leaves, pink blossom and bruised pods; leaves and pods on the shoulders."""
    r = Rig()
    # the shoulders: a mantle of leaves over bark
    r.poly([(-15, 1), (-13, -4), (-7, -6), (7, -6), (13, -4), (15, 1)], "dp_bark", -1.2, normal=(0, -0.3, 1.0), curve=0.6)
    for i in range(9):
        x = -12.0 + i * 3.0
        y = -3.4 + abs(x) * 0.06 + (i % 2) * 1.6
        r.ell(x, y, 2.0, 1.2, "dp_leaf", -0.9 + (i % 2) * 0.01, ang=-30 if x < 0 else 30, bias=0.15)
    for x in (-8.5, 9.0):
        r.ell(x, -0.8, 1.5, 1.9, "dp_bruise", -0.6, bias=0.25); r.dot(x - 0.5, -1.6, "dp_pink", 4, -0.59)
    # the crown: branches out to the corners
    sw = (0.0, 0.4, 0.0, -0.4)[k]
    branches = [[(-3, -16.5), (-7, -19.5), (-11, -22), (-14, -21.5)], [(-5.5, -15.5), (-9.5, -16.5), (-13.5, -14.5)],
                [(3, -16.5), (7, -19.5), (11, -22), (14, -21.5)], [(5.5, -15.5), (9.5, -16.5), (13.5, -14.5)],
                [(-1, -17), (-2, -20.5), (-3.5, -23)], [(1, -17), (2.5, -20.5), (4.5, -23)]]
    for j, b in enumerate(branches):
        r.tube(b, [1.3, 0.9, 0.6, 0.4], "dp_bark", 0.2 + j * 0.01, bias=0.15)
    leaves = [(-12.5, -20), (-9, -21.5), (-12, -16.5), (12.5, -20), (9, -21.5), (12, -16.5), (-4.5, -22), (5, -22)]
    for i, (x, y) in enumerate(leaves):
        r.ell(x, y, 1.6, 0.9, "dp_leaf", 0.4 + i * 0.002, ang=(-35, 25, -15, 35, -25, 15, 40, -40)[i], bias=0.2)
    blossoms = [(-10.0, -19.0), (10.0, -19.0), (-6.0, -18.6), (6.0, -18.6), (0.0, -21.4)]
    for i, (x, y) in enumerate(blossoms):
        r.ell(x, y, 1.5, 1.4, "dp_pink", 0.6 + i * 0.002, bias=0.25)
        r.dot(x, y, "dp_pollen", 4 if (i + k) % 3 == 0 else 3, 0.61 + i * 0.002)
    for x, y in ((-12.6, -12.4), (12.8, -12.0)):
        r.line(x, y - 2.2, x + sw, y - 0.8, "dp_bark", 0.5, tone=1)
        r.ell(x + sw, y + 0.4, 1.3, 1.7, "dp_bruise", 0.55, bias=0.25)
        r.dot(x + sw - 0.4, y - 0.2, "dp_pink", 3, 0.56)
    # the face of bark
    r.ell(0, -10.8, 5.6, 6.0, "dp_wood", 0.0, bias=0.2)
    r.poly([(-4.8, -8.0), (4.8, -8.0), (1.8, -3.6), (-1.8, -3.6)], "dp_wood", 0.0, normal=(0, 0.25, 1.0), curve=0.6, bias=0.1)
    r.ell(-3.6, -8.6, 1.4, 0.9, "dp_wood", 0.02, bias=0.35)                       # cheekbones
    r.ell(3.6, -8.6, 1.4, 0.9, "dp_wood", 0.02, bias=0.2)
    for x, y0, y1 in ((-4.6, -14, -9), (4.6, -13, -8), (-1.4, -16, -14.5), (2.2, -7, -4.6), (-2.8, -7.4, -5.6)):
        r.line(x, y0, x + 0.4, y1, "dp_wood", 0.05, tone=1)
    r.ell(0, -15.6, 5.2, 1.3, "dp_wood", 0.1, bias=0.3)                       # the brow ridge
    # mould on the right cheek, moss on the left temple
    for (x, y) in ((3.6, -8.0), (4.4, -7.0), (3.0, -6.6), (4.8, -9.0), (3.8, -6.0)):
        r.dot(x, y, "dp_mould", 3, 0.2)
    r.dot(4.0, -7.6, "dp_mould", 4, 0.21)
    for (x, y) in ((-5.0, -12.6), (-5.2, -11.6), (-4.6, -13.4), (-4.2, -12.0)):
        r.dot(x, y, "dp_leaf", 3, 0.2)
    # the eyes
    for sx in (-1, 1):
        eye(r, sx * 2.5, -11.0, "dp_pollen", 0.4, rx=1.6, ry=1.1, ang=sx * 15, sock="dp_bark", srx=2.1, sry=1.6,
            hot=(k == 2))
    r.poly([(-0.6, -12.6), (0.6, -12.6), (1.2, -8.4), (-1.2, -8.4)], "dp_wood", 0.3, normal=(-0.4, 0.0, 1.0))
    r.ell(0, -5.8, 1.6, 1.0, "dp_bark", 0.3, flat=0)                              # the knot-hole mouth
    for sx in (-1, 1):
        r.ell(sx * 5.8, -13.8, 1.5, 1.3, "dp_pink", 0.5, bias=0.25)
        r.dot(sx * 5.8, -13.8, "dp_pollen", 3, 0.51)
        r.ell(sx * 6.6, -11.8, 1.1, 0.9, "dp_leaf", 0.45, bias=0.2)
    r.ell(4.2, -7.0, 1.6, 0.7, "dp_mould", 0.4, bias=0.3); r.ell(4.6, -8.4, 1.1, 0.6, "dp_mould", 0.41, bias=0.3)
    r.dot(0.0, -4.6 + (k % 2), "dp_pollen", 2, 0.31)
    s = done(r)
    # the orchard at dusk: bruise-purple, a sickly green glow behind, falling petals and spores
    base = glow_bg([C("dp_bruise", 0), C("dp_bruise", 1), C("dp_bruise", 2), C("dp_pink", 1)], cy=-13, gain=2.8)
    for i in range(10):
        x = -13 + (i * 7) % 27
        y = -22 + ((i * 5 + k * 2) % 22)
        if (x, y) in base:
            base[(x, y)] = C("dp_pink", 3) if i % 2 else C("dp_mould", 3)
    return compose(s, base, C("dp_pollen", 3), 0.4, shade=C("dp_bruise", 0))


# ================================================================== Umbrael, the Hollow Mirror
def umbrael(k):
    """The Hollow Mirror: a hooded shadow whose face is a cracked porcelain mask, one half of it gone to mirror glass;
    a lilac eye in the mask, a cyan one in the glass; a crown of glass shards above, a silver mirror-frame gorget below,
    and its echoes, two pairs of lilac eyes, standing in the dark at either side. k: 1-3 the echoes step out and back."""
    r = Rig()
    # the cloak and the hood
    r.poly([(-15, 1), (-14, -5), (-10, -9), (-8, -16), (-4, -20), (0, -20.5), (4, -20), (8, -16), (10, -9), (14, -5), (15, 1)],
           "dp_void", -1.0, normal=(0, -0.2, 1.0), curve=0.8)
    r.poly([(-7, 1), (-7.5, -10), (-5.5, -16.5), (0, -18), (5.5, -16.5), (7.5, -10), (7, 1)], "dp_void", -0.9, flat=0)
    # the gorget: a gothic silver frame round a pane of glass
    r.poly([(-10, 1), (-10, -3), (-6, -4.5), (0, -3), (6, -4.5), (10, -3), (10, 1)], "dp_mirror", -0.5, normal=(0, -0.4, 0.9), curve=0.6)
    r.poly([(-7.5, 1), (-7.5, -2), (-3, -2.6), (0, -1.6), (3, -2.6), (7.5, -2), (7.5, 1)], "dp_glass", -0.45, normal=(0, -0.2, 1.0), curve=0.4)
    r.ell(0, -2.2, 1.3, 1.3, "dp_lilac", -0.3, flat=3); r.dot(0, -2.4, "dp_lilac", 4, -0.29)
    for x in (-9, 9):
        r.dot(x, -3.2, "dp_mirror", 4, -0.4)
    # the mask: left half porcelain, right half mirror glass
    r.ell(0, -10.6, 5.2, 6.0, "dp_mask", 0.0, bias=0.12, clip=lambda x, y: x <= 0)
    r.poly([(-4.2, -8.0), (0.0, -8.0), (0.0, -4.0), (-1.6, -4.2)], "dp_mask", 0.0, normal=(0, 0.25, 1.0), curve=0.5)
    r.ell(0, -10.6, 5.2, 6.0, "dp_glass", 0.0, bias=0.1, clip=lambda x, y: x > 0)
    r.poly([(0.0, -8.0), (4.2, -8.0), (1.6, -4.2), (0.0, -4.0)], "dp_glass", 0.0, normal=(0, 0.25, 1.0), curve=0.5)
    r.polyline([(0, -16.6), (0.8, -13.5), (-0.4, -11), (0.6, -8), (-0.2, -5), (0.4, -4)], "dp_void", 0.1, tone=1)
    r.polyline([(2.2, -15.0), (4.0, -12.4)], "dp_glass", 0.1, tone=4)
    r.polyline([(1.8, -8.4), (3.4, -6.4)], "dp_glass", 0.1, tone=4)
    r.polyline([(-3.6, -14.6), (-2.2, -13.6)], "dp_mask", 0.1, tone=1)
    eye(r, -2.5, -10.8, "dp_lilac", 0.3, rx=1.6, ry=1.1, ang=-10, sock="dp_void", srx=2.1, sry=1.5, hot=(k == 1))
    eye(r, 2.5, -10.8, "dp_cyan", 0.3, rx=1.6, ry=1.1, ang=10, sock="dp_void", srx=2.1, sry=1.5, hot=(k == 2))
    r.polyline([(-1.4, -6.0), (1.4, -6.0)], "dp_void", 0.2, tone=1)
    # the crown of glass shards
    shards = [(-6.5, -16.6, -10.5, -22.0), (-3.4, -18.0, -5.0, -23.2), (0.0, -18.6, 0.0, -23.6), (3.4, -18.0, 5.0, -23.2),
              (6.5, -16.6, 10.5, -22.0)]
    for i, (x0, y0, x1, y1) in enumerate(shards):
        r.tube([(x0, y0), (x1, y1)], [1.4, 0.3], "dp_glass", 0.5 + i * 0.01, bias=0.2)
        r.dot(x0 + (x1 - x0) * 0.6, y0 + (y1 - y0) * 0.6, "dp_glass", 4 if (i + k) % 3 == 0 else 3, 0.51 + i * 0.01)
    r.tube([(-7.2, -16.0), (0, -18.0), (7.2, -16.0)], [0.8, 0.9, 0.8], "dp_mirror", 0.6, bias=0.2)
    s = done(r)
    # the void: a lilac gloom, cracked-mirror lines, and the god's echoes either side
    base = glow_bg([C("dp_void", 0), C("dp_void", 1), C("dp_void", 2), C("dp_lilac", 0)], cy=-12, gain=2.8)
    for i, (a, ln) in enumerate(((200, 18), (235, 16), (320, 18), (300, 16), (160, 14), (20, 14))):
        for t in range(7, ln):
            x = int(round(math.cos(math.radians(a)) * t)); y = int(round(-12 + math.sin(math.radians(a)) * t * 0.8))
            if (x, y) in base:
                base[(x, y)] = mix(base[(x, y)], C("dp_mirror", 3), 0.35)
    off = (0, 1, 2, 1)[k]
    for sx in (-1, 1):
        cx = sx * (11 + off)
        for x, y in cells():
            d = math.hypot((x - cx) / 3.0, (y + 13) / 4.4)
            if 0.7 < d <= 1.0 and y < -10:
                base[(x, y)] = mix(base[(x, y)], C("dp_lilac", 1), 0.55)
        for q in ((cx - 1, -13), (cx + 1, -13)):
            if q in base: base[q] = C("dp_lilac", 3 if k else 2)
    return compose(s, base, C("dp_lilac", 3), 0.5, shade=C("dp_void", 0))


# ================================================================== Bel'Mora, the Drowned Bell
def belmora(k):
    """Bel'Mora: the drowned goddess inside the mouth of her sunken bell. The bronze bell, cracked and green with
    verdigris, rises behind her as a hood (its dome to the top edge, its lip flaring out at her shoulders); she has
    sea-green skin, lure-cyan eyes and gills, kelp for hair, a circlet of pearls and a lure on a stalk curling up from
    her brow, and barnacles on her shoulders, in deep teal water with bubbles rising."""
    r = Rig()
    sw = (0.0, 0.6, 1.0, 0.4)[k]
    # the bell behind her: dome, waist, flared lip
    r.poly([(-4.0, -23.6), (4.0, -23.6), (7.0, -22.4), (8.6, -20.0), (9.2, -16.0), (9.6, -11.0), (10.6, -6.5), (13.0, -3.6),
            (15.0, -2.6), (15.0, 1.0), (-15.0, 1.0), (-15.0, -2.6), (-13.0, -3.6), (-10.6, -6.5), (-9.6, -11.0), (-9.2, -16.0),
            (-8.6, -20.0), (-7.0, -22.4)], "dp_bell", -2.0, normal=(-0.1, -0.1, 1.0), curve=0.95)
    r.poly([(-4.0, -16.0), (4.0, -16.0), (6.2, -14.0), (6.6, -9.0), (7.2, -5.0), (-7.2, -5.0), (-6.6, -9.0),
            (-6.2, -14.0)], "dp_verdi", -1.9, flat=0)
    r.ell(0, -23.4, 1.8, 1.2, "dp_bell", -1.95, bias=0.2)                              # the canon loop
    r.dot(0, -23.0, "dp_verdi", 0, -1.94)                       # the dark inside
    for x, y0, y1 in ((-7.4, -20.0, -12.0), (-9.4, -10.0, -5.0), (7.8, -20.4, -14.6), (9.8, -9.6, -4.4), (-4.4, -22.6, -18.6),
                      (3.2, -22.0, -17.6)):
        r.line(x, y0, x + 0.3, y1, "dp_verdi", -1.85, tone=3 if x < 0 else 2)
    r.tube([(-8.8, -17.2), (0, -18.0), (8.8, -17.2)], [0.6, 0.6, 0.6], "dp_bell", -1.86, bias=0.3)   # the sound bow
    r.polyline([(5.8, -22.6), (6.6, -21.0), (6.0, -19.6), (7.0, -18.2)], "dp_bell", -1.84, tone=0)   # the crack
    for x in (-13.0, -10.6, 10.6, 13.0):
        r.dot(x, -3.2 + (0.4 if abs(x) > 12 else -1.0), "dp_bell", 4 if x < 0 else 3, -1.84)
    # the kelp hair, out from under the circlet and down over the bell's mouth
    for sx in (-1, 1):
        for j, (ex, ey) in enumerate(((11.0, -12.0), (11.6, -7.0), (10.6, -2.0))):
            pts = [(sx * 5.0, -14.5 + j * 1.2), (sx * (7.6 + j * 0.4), -13.0 + j * 2.0 + sw * 0.5),
                   (sx * (ex - 1 + sw), ey - 1.6), (sx * (ex + sw * 0.5), ey)]
            r.tube(pts, [1.4, 1.2, 0.9, 0.5], "dp_kelp", -0.6 - j * 0.01, bias=0.15)
    # the shoulders: barnacle grey, a pearl strand, the bell pendant
    r.poly([(-11, 1), (-10, -3), (-6, -5.5), (6, -5.5), (10, -3), (11, 1)], "dp_barn", -0.5, normal=(0, -0.4, 0.9), curve=0.6)
    for (x, y) in ((-8.6, -2.6), (-7.0, -1.0), (-9.6, -0.4), (8.4, -2.6), (9.6, -1.0), (7.0, -0.4)):
        r.ell(x, y, 0.9, 0.8, "dp_barn", -0.45, bias=0.35); r.dot(x, y, "dp_barn", 0, -0.44)
    for i in range(7):
        x = -4.5 + i * 1.5
        r.dot(x, -3.4 - abs(x) * 0.2, "dp_foam", 3 if i % 2 else 2, -0.3)
    r.ell(0, -1.0, 1.4, 1.6, "dp_bell", -0.2, bias=0.25)
    r.dot(0, 0.4, "dp_lure", 3, -0.1)
    # the face
    r.ell(0, -10.4, 5.0, 5.8, "dp_drown", 0.0, bias=0.15)
    r.poly([(-4.2, -8.0), (4.2, -8.0), (1.8, -4.0), (-1.8, -4.0)], "dp_drown", 0.0, normal=(0, 0.25, 1.0), curve=0.6)
    for sx in (-1, 1):
        for j in range(2):
            r.line(sx * 4.0, -8.4 + j * 1.2, sx * 4.6, -8.8 + j * 1.2, "dp_drown", 0.1, tone=1)
        eye(r, sx * 2.3, -10.8, "dp_lure", 0.3, rx=1.6, ry=1.1, ang=sx * 10, sock="dp_kelp", srx=2.0, sry=1.4,
            hot=(k == 2))
    r.dot(0.4, -8.6, "dp_drown", 1, 0.1)
    r.polyline([(-1.4, -6.0), (0.0, -5.6), (1.4, -6.0)], "dp_kelp", 0.15, tone=0)
    # the circlet of pearls and the lure on its stalk
    r.tube([(-5.0, -15.2), (0, -16.4), (5.0, -15.2)], [0.8, 0.9, 0.8], "dp_bell", 0.4, bias=0.2)
    for i, x in enumerate((-4.0, -2.0, 2.0, 4.0)):
        r.dot(x, -15.6 - (0.6 if abs(x) < 3 else 0.0), "dp_foam", 4 if i == 0 else 3, 0.45)
    r.ell(0, -16.6, 1.2, 1.2, "dp_lure", 0.6, flat=3); r.dot(-0.3, -16.9, "dp_lure", 4, 0.61)
    s = done(r)
    # the deep: teal, rays of light slanting down from the surface, bubbles rising, the lure's glow
    base = glow_bg([C("dp_verdi", 0), C("dp_verdi", 1), C("dp_drown", 1), C("dp_verdi", 2)], cy=-13, gain=2.6)
    for (x, y) in list(base):
        if (x - y // 2 + 40) % 7 == 0 and y < -6:
            base[(x, y)] = mix(base[(x, y)], C("dp_foam", 1), 0.3)
    for i, (x, y0) in enumerate(((-13, -6), (-12, -12), (13, -8), (12, -14), (-11, -20), (11, -21))):
        y = y0 - ((k + i) % 4) * 2
        if (x, y) in base:
            base[(x, y)] = C("dp_foam", 3)
            if (x + 1, y - 1) in base and i % 2: base[(x + 1, y - 1)] = C("dp_foam", 1)
    return compose(s, base, C("dp_lure", 3), 0.4, shade=C("dp_verdi", 0))


# ================================================================== Kaurn, the Storm Forge
def kaurn(k):
    """Kaurn: the Storm Forge as a smith-giant, a broad iron face under a heavy brow, eyes blazing storm blue-white, a
    beard of braided copper bound in brass, the forge glowing in his mouth; a crown of copper lightning rods throwing
    arcs; iron pauldrons riveted in copper. Frames 1 and 3 are the lightning flashes."""
    flash = k in (1, 3)
    r = Rig()
    # the pauldrons
    r.poly([(-8, 1), (-8, -5), (8, -5), (8, 1)], "dp_kiron", -1.1, normal=(0, -0.2, 1.0), curve=0.5)
    for sx in (-1, 1):
        r.ell(sx * 11.0, -2.6, 5.0, 4.0, "dp_kiron", -1.0, bias=0.15)
        r.tube([(sx * 7.0, -5.4), (sx * 14.5, -3.4)], [0.7, 0.7], "dp_copper", -0.9, bias=0.15)
        for x in (8.5, 11.0, 13.4):
            r.dot(sx * x, -1.4, "dp_copper", 4 if sx < 0 else 3, -0.85)
    # the head
    r.ell(0, -12.0, 6.0, 6.0, "dp_kskin", 0.0, bias=0.12)
    for sx in (-1, 1):
        r.ell(sx * 6.0, -11.4, 1.0, 1.6, "dp_kskin", 0.05, bias=0.1)            # the ears
    r.ell(0, -14.4, 6.2, 1.6, "dp_kskin", 0.2, bias=0.3)                      # the brow
    for sx in (-1, 1):
        r.ell(sx * 2.8, -11.8, 1.5, 1.2, "dp_kiron", 0.25, flat=0)
        eye(r, sx * 2.8, -11.8, "dp_storm", 0.3, rx=1.0, ry=0.8, core=4)
        if flash:
            r.polyline([(sx * 4.4, -12.2), (sx * 6.2, -13.6), (sx * 7.0, -13.0), (sx * 8.6, -14.6)], "dp_storm", 0.9, tones=[3, 4, 3])
    r.poly([(-1.0, -13.0), (1.0, -13.0), (1.6, -9.4), (-1.6, -9.4)], "dp_kskin", 0.3, normal=(-0.3, 0.1, 1.0))
    # the beard: three braids of copper bound with brass rings
    r.poly([(-6.0, -10.6), (6.0, -10.6), (5.8, -7.0), (3.6, -4.4), (-3.6, -4.4), (-5.8, -7.0)], "dp_copper", 0.4,
           normal=(0, 0.1, 1.0), curve=0.7)
    for i, x in enumerate((-3.0, 0.0, 3.0)):
        y1 = 0.6 if i == 1 else -0.8
        r.tube([(x, -5.6), (x * 1.1, y1)], [1.3, 0.9], "dp_copper", 0.42 + i * 0.01, bias=0.15)
        for y in (-3.4, y1 - 0.4):
            r.tube([(x * 1.05 - 1.1, y), (x * 1.05 + 1.1, y)], [0.5, 0.5], "dp_brass", 0.5 + i * 0.01, bias=0.2)
    r.poly([(-2.4, -8.6), (2.4, -8.6), (1.8, -6.8), (-1.8, -6.8)], "dp_kiron", 0.45, flat=0)   # the mouth
    r.polyline([(-1.4, -7.6), (1.4, -7.6)], "dp_ember", 0.46, tone=4 if flash else 3)
    r.dot(0, -7.0, "dp_ember", 2, 0.46)
    r.tube([(-5.8, -9.8), (-3.4, -9.2), (-1.0, -9.4)], [0.6, 0.7, 0.6], "dp_copper", 0.47, bias=0.25)   # moustache
    r.tube([(5.8, -9.8), (3.4, -9.2), (1.0, -9.4)], [0.6, 0.7, 0.6], "dp_copper", 0.47, bias=0.1)
    # the crown of lightning rods
    rods = [(-5.6, 3.4, -1.0), (-2.8, 5.0, -0.4), (0.0, 6.6, 0.0), (2.8, 5.0, 0.4), (5.6, 3.4, 1.0)]
    tips = []
    for i, (x, h, lean) in enumerate(rods):
        y0 = -16.8 + abs(x) * 0.2
        tip = (x + lean * 2.2, y0 - h)
        r.tube([(x, y0), tip], [0.9, 0.5], "dp_copper", 0.6 + i * 0.01, bias=0.2)
        r.dot(x, y0 - h * 0.45, "dp_brass", 4, 0.61 + i * 0.01)
        r.dot(tip[0], tip[1] - 1, "dp_storm", 4 if (flash or (i + k) % 2) else 3, 0.62 + i * 0.01)
        tips.append(tip)
    r.tube([(-6.6, -16.2), (0, -17.4), (6.6, -16.2)], [1.0, 1.1, 1.0], "dp_brass", 0.65, bias=0.2)
    r.ell(0, -17.2, 1.0, 0.9, "dp_storm", 0.7, flat=3); r.dot(0, -17.4, "dp_storm", 4, 0.71)
    if flash:
        for a, b in ((tips[0], tips[1]), (tips[3], tips[4])) if k == 1 else ((tips[1], tips[2]), (tips[2], tips[3])):
            mx, my = (a[0] + b[0]) / 2.0, min(a[1], b[1]) - 1.5
            r.polyline([(a[0], a[1] - 1), (mx, my), (b[0], b[1] - 1)], "dp_storm", 0.8, tones=[3, 4])
    s = done(r)
    # the storm: blue-black cloud, the forge's ember glow rising from below, a bolt in the flash frames
    base = glow_bg([C("dp_kiron", 0), C("dp_kiron", 1), C("dp_storm", 0), C("dp_storm", 1)], cy=-15,
                   gain=3.0 + (0.6 if flash else 0))
    for (x, y) in list(base):
        cl = math.sin(x * 0.55 + y * 0.2 + k * 0.4) + math.sin(y * 0.9 - x * 0.25)
        if y < -8 and cl + dith(x, y) > 1.2:
            base[(x, y)] = mix(base[(x, y)], C("dp_kskin", 2), 0.35)
        if y > -8:
            t = (y + 8) / 8.0
            if t * 1.6 + dith(x, y) > 0.8:
                base[(x, y)] = mix(base[(x, y)], C("dp_ember", 1), 0.5)
    if flash:
        sx = -1 if k == 1 else 1
        x, y = sx * 12, -23
        for step in range(13):
            if (x, y) in base: base[(x, y)] = C("dp_storm", 4 if step % 3 else 3)
            if (x - sx, y) in base and step % 4 == 0: base[(x - sx, y)] = C("dp_storm", 2)
            y += 1; x += (1 if (step // 2) % 2 else -1) * (1 if step % 2 else 0)
    return compose(s, base, C("dp_storm", 3), 0.45, shade=C("dp_kiron", 0))


# ================================================================== Ysveld, the Frost Widow
def ysveld(k):
    """The Frost Widow: a pale frost queen, ice-blue eyes and a widow-red mouth, a tall crown of ice crystals, a silk
    veil either side of her face, black spider legs arching out behind her shoulders, a frost collar with a red brooch,
    in a blue night with snow falling."""
    r = Rig()
    # the spider legs behind her, up and out to the edges
    for sx in (-1, 1):
        for j, (kx, ky, tx, ty) in enumerate(((9.5, -21.5, 14.0, -13.0), (12.0, -14.0, 14.5, -5.0))):
            root = (sx * 5.0, -12.0 + j * 1.5)
            r.tube([root, (sx * kx, ky), (sx * tx, ty)], [1.2, 1.0, 0.4], "dp_crys", -1.5 - j * 0.01, bias=0.1)
            r.dot(sx * kx, ky, "dp_rime", 3, -1.49 - j * 0.01)
    # the veil
    r.poly([(-6.0, -15.5), (-8.2, -10.0), (-9.0, -5.0), (-6.0, -4.0), (-5.2, -10.0)], "dp_wleg", -0.6, normal=(-0.4, -0.2, 1.0))
    r.poly([(6.0, -15.5), (8.2, -10.0), (9.0, -5.0), (6.0, -4.0), (5.2, -10.0)], "dp_wleg", -0.6, normal=(0.3, -0.2, 1.0))
    # the collar: frost crystals over a silk shawl, the brooch
    r.poly([(-15, 1), (-14, -3), (-7, -5), (7, -5), (14, -3), (15, 1)], "dp_silk", -0.5, normal=(0, -0.4, 0.9), curve=0.6)
    for i, x in enumerate((-10, -6, 6, 10)):
        r.tube([(x * 0.9, -2.8), (x * 1.1, -6.6 + abs(x) * 0.12)], [1.2, 0.3], "dp_ice", -0.4 + i * 0.01, bias=0.2)
    r.ell(0, -2.0, 1.5, 1.4, "dp_widow", -0.2, bias=0.25); r.dot(-0.4, -2.4, "dp_widow", 4, -0.19)
    # the face
    r.ell(0, -10.6, 5.0, 6.0, "dp_frost", 0.0, bias=0.12)
    r.poly([(-4.2, -8.0), (4.2, -8.0), (1.6, -3.8), (-1.6, -3.8)], "dp_frost", 0.0, normal=(0, 0.25, 1.0), curve=0.6)
    for sx in (-1, 1):
        eye(r, sx * 2.3, -11.0, "dp_rime", 0.3, rx=1.6, ry=1.0, ang=sx * 12, sock="dp_crys", srx=2.0, sry=1.3,
            hot=(k == 1))
        r.dot(sx * 3.9, -8.4, "dp_ice", 3, 0.2)                    # frost on the cheekbones
    r.dot(0.4, -8.4, "dp_frost", 1, 0.1)
    r.polyline([(-1.0, -5.8), (1.0, -5.8)], "dp_widow", 0.2, tone=3)
    r.dot(0, -5.2, "dp_widow", 1, 0.2)
    # the crown of ice
    for i, (x, h) in enumerate(((-6.0, 2.6), (-4.0, 4.4), (-2.0, 5.4), (0.0, 7.6), (2.0, 5.4), (4.0, 4.4), (6.0, 2.6))):
        y0 = -16.0 + abs(x) * 0.2
        r.tube([(x, y0), (x * 1.25, y0 - h)], [1.0, 0.3], "dp_ice" if i % 2 == 0 else "dp_crys", 0.5 + i * 0.01, bias=0.2)
        if (i + k) % 3 == 0:
            r.dot(x * 1.25, y0 - h + 1, "dp_rime", 4, 0.55)
    r.tube([(-6.2, -15.6), (0, -16.6), (6.2, -15.6)], [0.9, 1.0, 0.9], "dp_crys", 0.6, bias=0.2)
    r.ell(0, -16.4, 1.0, 1.0, "dp_widow", 0.65, bias=0.3); r.dot(-0.3, -16.7, "dp_widow", 4, 0.66)
    s = done(r)
    # the night: deep blue, frost glow behind her, snow falling
    base = glow_bg([C("dp_wleg", 0), C("dp_ice", 0), C("dp_ice", 1), C("dp_ice", 2)], cy=-13, gain=2.6)
    for i in range(12):
        x = -13 + (i * 9) % 27
        y = -22 + ((i * 7 + k * 2) % 23)
        if (x, y) in base:
            base[(x, y)] = C("dp_rime", 3 if i % 3 else 4)
    return compose(s, base, C("dp_rime", 3), 0.45, shade=C("dp_wleg", 0))


DRAW = {"jinx": jinx, "vhorrul": vhorrul, "ossivar": ossivar, "sylvene": sylvene, "umbrael": umbrael,
        "belmora": belmora, "kaurn": kaurn, "ysveld": ysveld}


def frames(god, origin=(14, 23), n=4):
    """The god's Idle frames for a 29 x 24 cell whose origin (the sheet's feet point) is origin."""
    dx, dy = origin[0] - 14, origin[1] - 23
    out = []
    for k in range(n):
        s = DRAW[god](k)
        px = {(x - dx, y - dy): c for (x, y), c in s.px.items()}
        o = SprRGB(px); o.tones = {(x - dx, y - dy): t for (x, y), t in getattr(s, "tones", {}).items()}
        out.append(o)
    return out


def to_image(s, scale=1):
    from PIL import Image
    im = Image.new("RGBA", (29, 24))
    for (x, y), c in s.px.items():
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            im.putpixel((x + 14, y + 23), tuple(c) + (255,))
    return im.resize((29 * scale, 24 * scale), Image.NEAREST) if scale > 1 else im


def main():
    from PIL import Image
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    sc = 6
    W = Image.new("RGBA", (len(GODS) * (29 * sc + 8) + 8, 24 * sc + 24 + 40), (24, 22, 28, 255))
    for i, g in enumerate(GODS):
        fr = frames(g)
        W.paste(to_image(fr[0], sc), (8 + i * (29 * sc + 8), 8))
        for j, f in enumerate(fr):
            W.paste(to_image(f), (8 + i * (29 * sc + 8) + j * 31, 24 * sc + 16))
    W.save(os.path.join(out, "deity_portraits.png"))
    print("wrote", os.path.join(out, "deity_portraits.png"))


if __name__ == "__main__":
    main()
