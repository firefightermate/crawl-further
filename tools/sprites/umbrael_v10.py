"""UMBRAEL v0.10 unique-evolution tree: the ten new monsters and their effect sheets.

Tree (every evolved monster has exactly one parent):
  Shade Imp   -> The Twinned, Nailshade
  Glimmer     -> Glassmoth*, Hourglass*
  Gloom Lurker-> Mirror Witch, Gloamcoil
  The Twinned -> The Hollow King, The Sundered*
  Nailshade   -> Glass Seraph, Bristleback*
  Mirror Witch-> The Unblinking, Glass Widow*
  Gloamcoil   -> Eclipse Wyrm, The Undertow*
  Glassmoth*  -> Argus Moth*, Glitterswarm*
  Hourglass*  -> The Pendulum*, Sand Wraith*
(* = drawn here, at final size: no design scale, no ArtScale entry.)

Loaded by umbrael_rigs.py (it registers every builder below in umbrael_rigs.SHEETS), so
`python3 umbrael_rigs.py [outdir] [Sheet ...]` builds these with the rest of the god.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import umbrael_rigs as U                     # noqa: E402  (umbrael_rigs aliases itself when run as __main__)
from rig import Part, line_px                # noqa: E402
from anim import Spr, PALETTE, pack, preview  # noqa: E402

sheet = U.sheet
put_px = U.put_px

# ------------------------------------------------------------------------------------------------
# palette additions (two-letter keys never reach Canvas.limb as plain strings: pass (c, c) tuples)
# ------------------------------------------------------------------------------------------------
PALETTE.update({
    # moth glass: clear ice panes, dark leading
    "wv": (0x2c, 0x34, 0x66), "wb": (0x4c, 0x7c, 0xc4), "wB": (0x9c, 0xd0, 0xff), "wc": (0xe2, 0xf6, 0xff),
    # Argus Moth: dusk wings
    "aq": (0x3a, 0x2a, 0x62), "an": (0x5e, 0x48, 0x9c), "aN": (0x8e, 0x74, 0xd0), "aU": (0xc4, 0xb2, 0xf2),
    # hourglass bronze + shadow sand
    "hA": (0x5c, 0x46, 0x2a), "he": (0x96, 0x78, 0x44), "hw": (0xc8, 0xaa, 0x6a), "hW": (0xf0, 0xdc, 0x9e),
    "hs": (0x9a, 0x6c, 0xd6), "hS": (0xc8, 0xa2, 0xf4), "hg": (0x56, 0x4a, 0x78), "hG": (0x80, 0x76, 0xa6),
    # Undertow ink
    "iK": (0x16, 0x12, 0x2a), "iq": (0x24, 0x1e, 0x44),
    # Undertow: the Gloamcoil's indigo, lifted a step (it lives in a dark pool)
    "Uq": (0x46, 0x3c, 0x88), "Un": (0x70, 0x5e, 0xc4), "UN": (0xa4, 0x90, 0xea),
    # venom
    "vg": (0x7c, 0xd8, 0x6a), "vG": (0xc0, 0xff, 0x9a),
})

# tone maps applied by umbrael_rigs.build_sheet after the silhouette pass
LIFT = {"q": "uq", "m": "um", "n": "un", "N": "uN"}
U.TONE_MAPS.update({
    "UmbGlassmoth": dict(LIFT),
    "UmbHourglass": dict(LIFT),
    "UmbArgusMoth": dict(LIFT),
    "UmbGlitterswarm": dict(LIFT),
    "UmbPendulum": dict(LIFT),
    "UmbSandWraith": dict(LIFT),
    "UmbSundered": dict(LIFT),
    "UmbBristleback": {"q": "pq", "m": "pm", "n": "pn", "N": "pN", "c": "pc"},
    "UmbGlassWidow": {"q": "lq", "m": "lm", "n": "ln", "N": "lN", "U": "lU"},
    "UmbUndertow": {"q": "Uq", "m": "gq", "n": "Un", "N": "UN", "c": "lc"},
})


def C():
    return U.Canvas()


def ell(cx, cy, rx, ry, fill="q"):
    return U.ellipse_px(cx, cy, rx, ry, fill)


def poly(pts, fill="q"):
    return U.poly_px(pts, fill)


def shade(px, lit="n", hi="N", dark="m", base="q"):
    return U.shade_body(px, lit=lit, hi=hi, dark=dark, base=base)


def finish_spr(c, extra=()):
    s = c.spr() if hasattr(c, "spr") else Spr(c)
    for item in extra:
        s = s.over(Spr(item))
    return U.ground(s)


def lpts(a, b):
    return line_px(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1])))


def line(c, a, b, col, over=True):
    for p in lpts(a, b):
        c.put(p[0], p[1], col, over)


def pol(ang, r):
    a = math.radians(ang)
    return (r * math.cos(a), r * math.sin(a))


def add(p, q, k=1.0):
    return (p[0] + q[0] * k, p[1] + q[1] * k)


def flash_px(cx, cy, r, cols=("X", "c", "u")):
    """A small four-point glint star."""
    px = {(cx, cy): cols[0]}
    for i in range(1, r + 1):
        col = cols[min(i, len(cols) - 1)]
        for d in ((i, 0), (-i, 0), (0, i), (0, -i)):
            px[(cx + d[0], cy + d[1])] = col
    return px


def corpse_of(spr, k=0.0, seed=0, smoke="sSN"):
    """Lay a frame on its back on the floor (optionally half dissolved)."""
    s = U.ground(U.rot_ccw(spr))
    return U.dissolve(s, k, seed=seed, rise=1, smoke=smoke) if k > 0 else s


def flatten(spr, sy=0.5):
    """Squash a frame onto the floor (corpses): rows merge toward the feet line."""
    out = {}
    for (x, y), c in sorted(spr.px.items(), key=lambda kv: kv[0][1]):
        out[(x, int(round(y * sy)))] = c
    return U.ground(Spr(out))


def anims_std(name, idle, run, death, dead, knock, moves, idle_d=(0.16, 0.14, 0.16, 0.14), run_d=0.07,
              death_d=(0.1, 0.12, 0.14, 0.3)):
    a = [("Idle", idle, list(idle_d)), ("Run", run, [run_d] * len(run)), ("Death", death, list(death_d)),
         ("Dead", [dead], [0.2]), ("Statue", [U.edge_pass(idle[0]).stone()], [0.2]), ("Knockback", [knock], [0.2]),
         ("Portrait", [idle[0]], [0.2])]
    a += moves
    return a


EVENTS = {}       # sheet -> anim -> [(moment, frame)]  (merged into umbrael_rigs.EVENTS for TIMING.md)
NOTES = []        # TIMING.md lines


# ================================================================================================
# GLIMMER LINE (glass that learned to fly)
# ================================================================================================
# ------------------------------------------------------------------------------------------------
# GLASSMOTH (T2, Glimmer): the Glimmer's black-mirror kite is now a moth's body, eye and all; its two little
# crystal wings have grown into four broad panes of ice glass with dark leading. Feathered antennae.
# Attack Scales: two glass wing-scales flicked in a V. Special Glitter Dust: a fanning beat throws a drifting
# cloud of mirror dust at the hero that slows him.
# ------------------------------------------------------------------------------------------------
def glass_wing(root, ang, length, width, far=False, glint=0, veins=3, spots=False):
    """A moth wing of leaded glass: root -> tip along `ang`, bellied toward ang+90 (deg, y down)."""
    tip = add(root, pol(ang, length))
    belly = add(add(root, pol(ang, length * 0.62)), pol(ang + 90, width))
    back = add(root, pol(ang + 70, width * 0.75))
    px = poly([root, tip, belly, back], "W1")
    fill = ("wb", "wv", "wB") if far else ("wB", "wb", "wc")
    out = {}
    for (x, y) in px:
        d = ((x - root[0]) * math.cos(math.radians(ang)) + (y - root[1]) * math.sin(math.radians(ang))) / max(1.0, length)
        out[(x, y)] = fill[0] if (x + y + glint) % 5 else fill[2]
        if d < 0.25: out[(x, y)] = fill[1]
    # leading: veins radiating from the root
    for v in range(veins):
        t = (v + 1) / (veins + 1)
        end = add(add(root, pol(ang, length * (0.95 - 0.2 * t))), pol(ang + 90, width * t * 0.9))
        for p in lpts(root, end):
            if p in out: out[p] = "wv" if not far else "q"
    # bright leading edge along the top
    for p in lpts(root, tip):
        if p in out: out[p] = fill[2] if not far else "wb"
    tx, ty = int(round(tip[0])), int(round(tip[1]))
    out[(tx, ty)] = "wc" if not far else "wB"
    if spots:
        sp = add(add(root, pol(ang, length * 0.6)), pol(ang + 90, width * 0.35))
        sx, sy = int(round(sp[0])), int(round(sp[1]))
        for (ox, oy, col) in ((0, 0, "K"), (1, 0, "c"), (-1, 0, "u"), (0, -1, "u"), (0, 1, "u")):
            if (sx + ox, sy + oy) in out: out[(sx + ox, sy + oy)] = col
    return out


def antenna(c, x, y, ang, ln=5, col="u"):
    ex, ey = c.limb(x, y, [(ln * 0.6, ang), (ln * 0.4, ang - 25)], [col])
    c.put(ex, ey, "c")
    # feathered barbs
    a = math.radians(ang)
    for k in (2, 3):
        bx, by = int(round(x + k * math.cos(a))), int(round(y + k * math.sin(a)))
        c.put(bx - 1, by, "U", over=False)


MOTH_FLAP = [0.0, -0.5, -1.0, -0.5]     # wingbeat: 1 = wings swept down, -1 = raised high


MOTH_GLASS = {"top": "wc", "top_far": "wB", "edge": "wv", "fill": "wB", "fill_far": "wb", "glint": "wc",
              "glint_far": "wB", "vein": "wv", "vein_far": "q"}
ARGUS = {"top": "aU", "top_far": "aN", "edge": "q", "fill": "an", "fill_far": "aq", "glint": "aN", "glint_far": "an",
         "vein": "aq", "vein_far": "q"}


def pane_wing(pts, glint=0, far=False, veins_from=None, spots=(), pal=None, eyespot=None):
    """A leaded-glass wing: dark leading outline, ice panes, a bright upper edge, veins from the root."""
    P = pal or MOTH_GLASS
    px = poly(pts)
    out = {}
    for (x, y) in px:
        edge = any((x + dx, y + dy) not in px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        top = (x, y - 1) not in px
        if edge:
            out[(x, y)] = (P["top_far"] if far else P["top"]) if top else P["edge"]
        else:
            out[(x, y)] = (P["fill_far"] if far else P["fill"]) if (x * 2 + y * 3 + glint) % 7 else \
                (P["glint_far"] if far else P["glint"])
    if veins_from:
        r = veins_from
        for q in pts[1:-1]:
            for p in lpts(r, q):
                if p in out and out[p] not in (P["top"],): out[p] = P["vein_far"] if far else P["vein"]
    if eyespot:
        (ex, ey), er = eyespot
        for (x, y) in list(out):
            d = math.hypot(x - ex, (y - ey) * 1.1)
            if d <= er + 0.4:
                out[(x, y)] = "wB" if d > er - 0.8 else ("u" if d > er - 1.8 else ("K" if d < er * 0.4 else "n"))
        for k in ((int(round(ex - er * 0.35)), int(round(ey - er * 0.35))),):
            if k in out: out[k] = "X"
    for (sx, sy) in spots:
        sx, sy = int(round(sx)), int(round(sy))
        for (ox, oy, col) in ((0, 0, "K"), (1, 0, "n"), (-1, 0, "n"), (0, -1, "N"), (0, 1, "n")):
            if (sx + ox, sy + oy) in out: out[(sx + ox, sy + oy)] = col
        if (sx, sy) in out: out[(sx, sy)] = "K"
    return out


def moth_wings(c, cx, cy, f, glint=0, span=1.0, spots=False, hind=True):
    """Both pairs, mirrored. f: wingbeat (-1 raised .. 1 down)."""
    for s in (-1, 1):
        far = s < 0 and False
        lift = -7 * (-f if f < 0 else 0) + 5 * max(0.0, f)
        fw = [(cx + s * 1, cy - 4), (cx + s * 6 * span, cy - 9 + lift * 0.5), (cx + s * 13 * span, cy - 10 + lift),
              (cx + s * 12 * span, cy - 4 + lift * 0.7), (cx + s * 7 * span, cy - 1 + lift * 0.3), (cx + s * 1, cy)]
        if hind:
            hl = lift * 0.35
            hw = [(cx + s * 1, cy - 1), (cx + s * 8 * span, cy + 1 + hl), (cx + s * 8 * span, cy + 4 + hl),
                  (cx + s * 4 * span, cy + 7 + hl * 0.6), (cx + s * 1, cy + 4)]
            put_px(c, pane_wing(hw, glint, far=True, veins_from=(cx + s, cy + 1)))
        sp = [((cx + s * 9 * span, cy - 6 + lift * 0.75))] if spots else []
        put_px(c, pane_wing(fw, glint + (s > 0), veins_from=(cx + s, cy - 2), spots=sp))


def antenna(c, x, y, s, ln=5, droop=0):
    pts = [(x, y), (x + s * 2, y - 3), (x + s * 4, y - ln + droop)]
    for a_, b_ in zip(pts, pts[1:]):
        line(c, a_, b_, "U")
    c.put(int(round(pts[-1][0])), int(round(pts[-1][1])), "c")
    c.put(int(round(x + s * 1)), int(round(y - 3)), "u", over=False)
    c.put(int(round(x + s * 3)), int(round(y - 5 + droop * 0.5)), "u", over=False)


def glassmoth(flap=0, bob=0, dx=0, tilt=0, eye="open", glow=False, hover=7, glint=0, extra=(), cracks=0, span=1.0,
              droop=0):
    c = C()
    cx, cy = dx, -hover - 9 + bob
    f = MOTH_FLAP[flap % 4] if isinstance(flap, int) else flap
    antenna(c, cx + 1, cy - 8, 1, 6, droop)
    antenna(c, cx - 1, cy - 8, -1, 6, droop)
    moth_wings(c, cx, cy, f, glint, span)
    # body: the Glimmer's mirror kite, upright, eye and all
    put_px(c, U.mirror_shard(cx, cy, tilt, glint=glint * 1.5 - 3, scale=1.3, cracks=cracks, eye=eye, glow=glow))
    return finish_spr(c, extra)


def scale_px(x, y, ang, far=False):
    """A loose glass wing-scale (projectile art in the frames)."""
    px = {}
    a = math.radians(ang)
    for i in range(3):
        px[(int(round(x + i * math.cos(a))), int(round(y + i * math.sin(a))))] = ("wB", "wc", "X")[i]
    px[(int(round(x - math.sin(a))), int(round(y + math.cos(a))))] = "wb"
    return px


def dust_px(cx, cy, r, seed=0, n=14):
    rnd = random.Random(seed)
    px = {}
    for i in range(n):
        a = rnd.uniform(0, 360); d = rnd.uniform(0, r)
        x, y = int(round(cx + d * math.cos(math.radians(a)))), int(round(cy + d * 0.7 * math.sin(math.radians(a))))
        px[(x, y)] = ("c", "wB", "u", "X")[i % 4]
    return px


@sheet
def build_UmbGlassmoth(outdir):
    idle = [glassmoth(flap=i, bob=[0, -1, -1, 0][i], glint=i) for i in range(4)]
    run = [glassmoth(flap=[0.4, -0.3, -1.0, -0.3, 0.4, 0.8][i], bob=[0, -1, -2, -1, 0, 1][i], tilt=12, dx=1, glint=i)
           for i in range(6)]
    # Scales: wings raised (0-1), the downbeat flicks two scales off the forewings (2), recoil, settle
    scales = [
        glassmoth(flap=-1.0, bob=-1, eye="glare", glint=1, tilt=-6),
        glassmoth(flap=-1.3, bob=-2, dx=-1, eye="glare", glow=True, glint=2, tilt=-10, extra=[U.sparkle(9, -30)]),
        glassmoth(flap=1.0, bob=0, dx=1, tilt=10, eye="glare", glint=3,
                  extra=[scale_px(11, -19, -12), scale_px(11, -14, 12), flash_px(10, -17, 1)]),
        glassmoth(flap=0.8, bob=0, dx=1, tilt=8, glint=0),
        glassmoth(flap=0.2, bob=-1, glint=1),
        glassmoth(flap=0, bob=0, glint=2),
    ]
    # Glitter Dust: rise (0), wings held high shimmering (1-2), the great fanning beat (3: dust released), beat
    # through (4-5), settle (6)
    dust = [
        glassmoth(flap=-0.8, bob=-2, glint=0),
        glassmoth(flap=-1.3, bob=-3, eye="glare", glow=True, glint=2, extra=[dust_px(0, -30, 7, 1, 8)]),
        glassmoth(flap=-1.4, bob=-3, eye="glare", glow=True, glint=4, extra=[dust_px(0, -30, 9, 2, 12)]),
        glassmoth(flap=1.2, bob=0, dx=1, tilt=8, eye="glare", glint=1, extra=[dust_px(14, -15, 6, 3, 16)]),
        glassmoth(flap=1.0, bob=1, dx=1, tilt=6, glint=2, extra=[dust_px(18, -14, 7, 4, 10)]),
        glassmoth(flap=0.4, bob=0, glint=3, extra=[dust_px(22, -13, 7, 5, 5)]),
        glassmoth(flap=0, bob=0, glint=0),
    ]
    dead = flatten(glassmoth(flap=0.9, hover=-3, eye="shut", cracks=4, glint=1, droop=4), 0.45).over(
        Spr({(-13, 0): "wB", (12, 0): "wb", (14, -1): "wc"}))
    death = [
        glassmoth(flap=-1.2, bob=-1, eye="shut", cracks=2, tilt=-10, extra=[U.sparkle(5, -24)]),
        glassmoth(flap=1.3, hover=4, tilt=-25, eye="shut", cracks=3, dx=-1, droop=3),
        U.ground(glassmoth(flap=1.6, hover=-1, tilt=-60, eye="shut", cracks=4, dx=-1, droop=4)),
        dead,
    ]
    knock = glassmoth(flap=-1.2, dx=-2, tilt=-20, bob=-1, eye="shut", cracks=1, droop=2)
    anims = anims_std("UmbGlassmoth", idle, run, death, dead, knock,
                      [("Scales", scales, [0.12, 0.14, 0.05, 0.08, 0.1, 0.12]),
                       ("Dust", dust, [0.12, 0.14, 0.14, 0.06, 0.08, 0.1, 0.14])], idle_d=(0.12,) * 4, run_d=0.07)
    return U.build_sheet("UmbGlassmoth", anims, outdir)


EVENTS["UmbGlassmoth"] = {"Scales": [("release (2 FxUmbMothScale from the forewing, (10, -16))", 2)],
                          "Dust": [("downbeat: FxUmbGlitter cloud thrown from (12, -14)", 3)]}


# ------------------------------------------------------------------------------------------------
# generic helpers for rotated drawings
# ------------------------------------------------------------------------------------------------
def rotate_px(px, ang, center=(0.0, 0.0)):
    """Nearest-neighbour rotation of a pixel dict about `center` (deg, y down: positive turns clockwise)."""
    if not px or abs(ang) < 0.01:
        return dict(px)
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    cx, cy = center
    xs = [p[0] for p in px]; ys = [p[1] for p in px]
    R = int(max(max(abs(x - cx) for x in xs), max(abs(y - cy) for y in ys)) * 1.5) + 2
    out = {}
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            dx, dy = x - cx, y - cy
            sx = cx + dx * ca + dy * sa; sy = cy - dx * sa + dy * ca
            k = (int(round(sx)), int(round(sy)))
            if k in px: out[(x, y)] = px[k]
    return out


def shift_px(px, dx, dy):
    return {(x + dx, y + dy): c for (x, y), c in px.items()}


# ------------------------------------------------------------------------------------------------
# HOURGLASS (T2, Glimmer): the Glimmer's black mirror blown into an hourglass of dark glass in a bronze frame. Its
# eye floats in the upper bulb, violet shadow-sand runs into the lower one, and the Glimmer's crystal wings beat
# at the waist. Attack Sand Shard: spits a shard of fused sand. Special Rewind: it flips itself over and marks
# the spot; 2.5 s later time runs back - it snaps back to the mark and gets back the health it lost since.
# ------------------------------------------------------------------------------------------------
def hourglass_body(sand=0.8, flow=1, eye="open", glow=False, cracks=0, glint=0, rev=False, half=9):
    """Local drawing, centre (0, 0) = the waist, y down. sand: share of the sand in the LOWER bulb."""
    px = {}
    # bulbs of dark glass
    up = poly([(-5, -half + 1), (6, -half + 1), (6, -half + 4), (1.5, 0), (-0.5, 0), (-5, -half + 4)])
    lo = {(x, -y): v for (x, y), v in up.items()}
    for blk, upper in ((up, True), (lo, False)):
        for (x, y) in blk:
            edge_l = (x - 1, y) not in blk; edge_r = (x + 1, y) not in blk
            c = "q"
            if edge_l: c = "u" if upper else "U"
            elif edge_r: c = "n"
            elif (x - y + glint) % 6 == 0: c = "b"
            px[(x, y)] = c
    # sand: lower pile rises with `sand`, upper keeps the rest above the neck
    lo_rows = sorted({y for (x, y) in lo})
    n_lo = int(round(len(lo_rows) * (0.15 + 0.7 * sand)))
    for y in lo_rows[-n_lo:]:
        for x in range(-6, 7):
            if (x, y) in lo and px.get((x, y)) not in ("u", "U"):
                px[(x, y)] = "hS" if y == lo_rows[-n_lo] else ("hs" if (x + y) % 3 else "N")
    up_rows = sorted({y for (x, y) in up})
    n_up = int(round(len(up_rows) * (0.6 * (1 - sand))))
    for y in up_rows[len(up_rows) - n_up:]:
        for x in range(-6, 7):
            if (x, y) in up and px.get((x, y)) not in ("u", "U"):
                px[(x, y)] = "hs" if (x + y) % 3 else "hS"
    if flow:
        for y in range(-1, 3 + flow):
            px[(0, y)] = "hS" if (y + glint) % 2 else "X"
    # the eye in the upper bulb
    ex, ey = 1, -half + 4
    if eye == "open":
        for (ox, oy, col) in ((-1, 0, "U"), (0, 0, "c"), (1, 0, "X" if glow else "c"), (2, 0, "U"), (0, -1, "U"),
                              (1, -1, "u"), (0, 1, "n"), (1, 1, "U")):
            px[(ex + ox, ey + oy)] = col
    elif eye == "glare":
        for (ox, oy, col) in ((-1, 0, "u"), (0, 0, "X"), (1, 0, "X"), (2, 0, "c"), (0, -1, "c"), (1, -1, "c"),
                              (0, 1, "u"), (1, 1, "u")):
            px[(ex + ox, ey + oy)] = col
    else:
        for (ox, oy, col) in ((-1, 0, "n"), (0, 0, "U"), (1, 0, "U"), (2, 0, "n")):
            px[(ex + ox, ey + oy)] = col
    # bronze frame: caps + two posts
    for (cy_, top) in ((-half, True), (half, False)):
        for x in range(-7, 9):
            px[(x, cy_)] = "hw" if top else "he"
            px[(x, cy_ + (-1 if top else 1))] = "hA" if top else "hA"
        px[(-7, cy_)] = "hW" if top else "hw"
        px[(8, cy_)] = "he"
    for x_ in (-7, 8):
        for y in range(-half + 1, half):
            px[(x_, y)] = ("hw" if x_ < 0 else "he") if y % 4 else "hW"
    px[(-7, 0)] = "hW"; px[(8, 0)] = "hw"
    if cracks:
        rnd = random.Random(cracks + 3)
        for _ in range(cracks):
            x, y = rnd.uniform(-3, 3), rnd.uniform(-6, 6)
            d = rnd.uniform(0, 360)
            for st in range(4):
                d += rnd.uniform(-40, 40); x += math.cos(math.radians(d)); y += math.sin(math.radians(d))
                k = (int(round(x)), int(round(y)))
                if k in px and px[k] not in ("hw", "he", "hA", "hW"): px[k] = "c" if st < 2 else "u"
    return px


def hourglass(rot=0, sand=0.8, flow=1, eye="open", glow=False, cracks=0, glint=0, flap=0, bob=0, dx=0, hover=4,
              wings=True, extra=()):
    c = C()
    half = 9
    cy = -hover - half - 2 + bob
    fa = U.FLAP[flap % 4] if isinstance(flap, int) else flap
    if wings:
        # the Glimmer's crystal wings at the waist: far (left) dark, near (right) bright
        put_px(c, U.crystal_wing((dx - 7, cy + 1), fa + 10, 6, back=True))
    put_px(c, shift_px(rotate_px(hourglass_body(sand, flow, eye, glow, cracks, glint, half=half), rot), dx, cy))
    if wings:
        put_px(c, U.crystal_wing((dx + 8, cy + 1), -180 - fa - 10, 6))
    return finish_spr(c, extra)


def sand_shard_px(x, y, ang=0):
    px = {}
    a = math.radians(ang)
    for i in range(4):
        px[(int(round(x + i * math.cos(a))), int(round(y + i * math.sin(a))))] = ("hs", "hS", "hS", "X")[i]
    px[(int(round(x + 1 * math.cos(a) - math.sin(a))), int(round(y + 1 * math.sin(a) + math.cos(a))))] = "N"
    return px


@sheet
def build_UmbHourglass(outdir):
    idle = [hourglass(flap=i, bob=[0, -1, -1, 0][i], glint=i, sand=[0.70, 0.73, 0.76, 0.79][i], rot=[0, 2, 0, -2][i])
            for i in range(4)]
    run = [hourglass(flap=i % 4, bob=[0, -1, -2, -1, 0, 1][i], glint=i, rot=14, dx=1, sand=0.7) for i in range(6)]
    # Shard: rock back (0-1, the sand glows), tip forward and spit a fused shard from the neck (2), settle
    shard = [
        hourglass(rot=-14, flap=0, eye="glare", glint=1, sand=0.7),
        hourglass(rot=-24, flap=1, eye="glare", glow=True, dx=-1, glint=2, sand=0.7, extra=[U.sparkle(4, -18)]),
        hourglass(rot=26, flap=3, eye="glare", glint=3, dx=1, sand=0.65,
                  extra=[sand_shard_px(9, -14, 0), flash_px(8, -14, 1, ("X", "hS"))]),
        hourglass(rot=16, flap=2, glint=4, dx=1, sand=0.66),
        hourglass(rot=6, flap=1, glint=5, sand=0.67),
        hourglass(rot=0, flap=0, glint=0, sand=0.68),
    ]
    # Rewind: wings up (0), mark the spot (1: FxUmbRewind "Mark" at the feet), flip end over end (2-5, the sand now
    # pouring the other way), settle upside-up again with the bulbs swapped (6-7)
    rewind = [
        hourglass(rot=0, flap=0, eye="glare", glow=True, sand=0.8, glint=1),
        hourglass(rot=0, flap=1, eye="glare", glow=True, sand=0.8, glint=2, bob=-1,
                  extra=[{(x, 0): "hS" for x in range(-6, 8, 2)}]),
        hourglass(rot=50, flap=2, eye="glare", sand=0.8, glint=3, bob=-2, flow=0),
        hourglass(rot=100, flap=3, eye="glare", sand=0.8, glint=4, bob=-2, flow=0, extra=[U.sparkle(-8, -20)]),
        hourglass(rot=145, flap=0, eye="glare", sand=0.75, glint=5, bob=-2, flow=0),
        hourglass(rot=180, flap=1, eye="shut", sand=0.8, glint=0, bob=-1, flow=0),
        hourglass(rot=0, flap=2, eye="open", glow=True, sand=0.2, glint=1, extra=[U.sparkle(9, -24, True)]),
        hourglass(rot=0, flap=3, sand=0.25, glint=2),
    ]
    dead = U.ground(Spr(shift_px(rotate_px(hourglass_body(0.9, 0, "shut", False, 4, 0), 90), -1, -8))).over(
        Spr({(x, 0): ("hs" if x % 2 else "hS") for x in range(-12, -6)} | {(-11, -1): "hs", (-9, -1): "N", (10, 0): "c", (12, 0): "u"}))
    death = [
        hourglass(rot=-10, flap=0, eye="shut", cracks=2, sand=0.8, extra=[U.sparkle(5, -22)]),
        hourglass(rot=-40, flap=2, eye="shut", cracks=3, sand=0.8, hover=2, dx=-1),
        U.ground(hourglass(rot=-75, flap=3, eye="shut", cracks=5, sand=0.85, hover=-4, wings=False, flow=0)),
        dead,
    ]
    knock = hourglass(rot=-25, flap=1, dx=-2, eye="shut", cracks=1, sand=0.7)
    anims = anims_std("UmbHourglass", idle, run, death, dead, knock,
                      [("Shard", shard, [0.12, 0.14, 0.05, 0.08, 0.1, 0.12]),
                       ("Rewind", rewind, [0.1, 0.14, 0.07, 0.07, 0.07, 0.08, 0.12, 0.14])], idle_d=(0.16,) * 4)
    return U.build_sheet("UmbHourglass", anims, outdir)


EVENTS["UmbHourglass"] = {"Shard": [("release (FxUmbSandShard from the neck, (9, -14))", 2)],
                          "Rewind": [("mark the spot (FxUmbRewind Mark at the feet; snap back 2.5 s later)", 1)]}


# ------------------------------------------------------------------------------------------------
# ARGUS MOTH (T3, Glassmoth): the glass moth grown vast, its wings gone dusk-violet and set with staring
# eyespots - every one the Glimmer's eye. Attack Scale Volley: a fan of three eye-scales. Special Thousand Eyes:
# it throws its wings wide and every eyespot opens; a hero who is looking at it is dazed.
# ------------------------------------------------------------------------------------------------
def argus_wings(c, cx, cy, f, glint=0, open_=0.0, span=1.0):
    for s in (-1, 1):
        lift = -9 * (-f if f < 0 else 0) + 6 * max(0.0, f)
        sp = span * (1 + 0.12 * open_)
        hw = [(cx + s * 1, cy), (cx + s * 11 * sp, cy + 1 + lift * 0.3), (cx + s * 14 * sp, cy + 6 + lift * 0.3),
              (cx + s * 10 * sp, cy + 12 + lift * 0.2), (cx + s * 4 * sp, cy + 12), (cx + s * 1, cy + 6)]
        e_r = 2.6 + 0.8 * open_
        put_px(c, pane_wing(hw, glint, far=True, veins_from=(cx + s, cy + 2), pal=ARGUS,
                            eyespot=((cx + s * 8 * sp, cy + 6 + lift * 0.25), e_r)))
        fw = [(cx + s * 1, cy - 5), (cx + s * 7 * sp, cy - 12 + lift * 0.5), (cx + s * 19 * sp, cy - 15 + lift),
              (cx + s * 20 * sp, cy - 9 + lift * 0.9), (cx + s * 15 * sp, cy - 2 + lift * 0.5), (cx + s * 6 * sp, cy + 1),
              (cx + s * 1, cy + 1)]
        put_px(c, pane_wing(fw, glint + (s > 0), veins_from=(cx + s, cy - 3), pal=ARGUS,
                            eyespot=((cx + s * 12 * sp, cy - 8 + lift * 0.7), 2.2 + 0.9 * open_)))
        # the glass margin of the old moth along the wingtips
        for t in range(6):
            q = (cx + s * (19 - t) * sp, cy - 15 + lift + t * 0.9 + (t > 3) * 1)
            c.put(int(round(q[0])), int(round(q[1])), "wc" if t < 3 else "wB")


def argus(flap=0, bob=0, dx=0, tilt=0, eye="open", glow=False, hover=6, glint=0, extra=(), cracks=0, open_=0.0,
          droop=0, span=1.0):
    c = C()
    cx, cy = dx, -hover - 15 + bob
    f = MOTH_FLAP[flap % 4] if isinstance(flap, int) else flap
    antenna(c, cx + 1, cy - 10, 1, 8, droop)
    antenna(c, cx - 1, cy - 10, -1, 8, droop)
    argus_wings(c, cx, cy, f, glint, open_, span)
    # furred collar
    for (ox, oy) in ((-3, -6), (-2, -7), (2, -7), (3, -6), (-1, -7), (1, -7), (0, -8)):
        c.put(cx + ox, cy + oy, "N" if oy < -6 else "n")
    put_px(c, U.mirror_shard(cx, cy, tilt, glint=glint * 1.5 - 3, scale=1.75, cracks=cracks, eye=eye, glow=glow))
    return finish_spr(c, extra)


def eye_scale_px(x, y, ang=0):
    px = scale_px(x, y, ang)
    px[(int(round(x + math.cos(math.radians(ang)))), int(round(y + math.sin(math.radians(ang)))))] = "aN"
    return px


@sheet
def build_UmbArgusMoth(outdir):
    idle = [argus(flap=i, bob=[0, -1, -1, 0][i], glint=i, open_=[0, 0.1, 0.2, 0.1][i]) for i in range(4)]
    run = [argus(flap=[0.4, -0.3, -1.0, -0.3, 0.4, 0.8][i], bob=[0, -1, -2, -1, 0, 1][i], tilt=10, dx=1, glint=i)
           for i in range(6)]
    # Volley: raise (0-1), downbeat throws three eye-scales from the forewings (2), recoil (3), settle (4-5)
    volley = [
        argus(flap=-1.0, bob=-1, eye="glare", glint=1, tilt=-6),
        argus(flap=-1.3, bob=-2, dx=-1, eye="glare", glow=True, glint=2, tilt=-8, extra=[U.sparkle(12, -40)]),
        argus(flap=1.0, bob=0, dx=1, tilt=10, eye="glare", glint=3,
              extra=[eye_scale_px(18, -26, -14), eye_scale_px(19, -22, 0), eye_scale_px(18, -18, 14), flash_px(17, -22, 2)]),
        argus(flap=0.8, bob=0, dx=1, tilt=8, glint=0),
        argus(flap=0.2, bob=-1, glint=1),
        argus(flap=0, bob=0, glint=2),
    ]
    # Thousand Eyes: fold (0), unfurl (1-2), wings thrown wide, every eyespot open (3: the gaze lands), hold (4-5),
    # fold back (6-7)
    gaze = [
        argus(flap=0.9, bob=0, eye="shut", glint=0, span=0.8),
        argus(flap=-0.6, bob=-1, eye="open", glint=1, open_=0.4),
        argus(flap=-0.2, bob=-2, eye="glare", glow=True, glint=2, open_=0.8, extra=[U.sparkle(-14, -36), U.sparkle(15, -38)]),
        argus(flap=0.0, bob=-2, eye="glare", glow=True, glint=3, open_=1.3, span=1.08,
              extra=[flash_px(0, -24, 3), flash_px(-12, -29, 1), flash_px(12, -29, 1)]),
        argus(flap=0.0, bob=-2, eye="glare", glow=True, glint=4, open_=1.3, span=1.08),
        argus(flap=0.1, bob=-1, eye="glare", glint=5, open_=1.0, span=1.04),
        argus(flap=0.6, bob=0, glint=0, open_=0.4),
        argus(flap=0, bob=0, glint=1),
    ]
    dead = flatten(argus(flap=0.9, hover=-6, eye="shut", cracks=4, glint=1, droop=5), 0.42)
    death = [
        argus(flap=-1.2, bob=-1, eye="shut", cracks=2, tilt=-10, extra=[U.sparkle(6, -36)]),
        argus(flap=1.3, hover=3, tilt=-20, eye="shut", cracks=3, dx=-1, droop=3),
        U.ground(argus(flap=1.6, hover=-4, tilt=-50, eye="shut", cracks=5, dx=-1, droop=5)),
        dead,
    ]
    knock = argus(flap=-1.2, dx=-2, tilt=-18, bob=-1, eye="shut", cracks=1, droop=2)
    anims = anims_std("UmbArgusMoth", idle, run, death, dead, knock,
                      [("Volley", volley, [0.12, 0.16, 0.05, 0.08, 0.1, 0.12]),
                       ("Gaze", gaze, [0.1, 0.12, 0.16, 0.12, 0.2, 0.14, 0.12, 0.12])], idle_d=(0.14,) * 4, run_d=0.08)
    return U.build_sheet("UmbArgusMoth", anims, outdir)


EVENTS["UmbArgusMoth"] = {"Volley": [("release (3 FxUmbArgusScale from (18, -22))", 2)],
                          "Gaze": [("every eye opens: the gaze check (FxUmbGaze at the hero)", 3)]}


# ------------------------------------------------------------------------------------------------
# GLITTERSWARM (T3, Glassmoth): the glass moth has become a hive of itself - a dark mirror heart with the
# Glimmer's eye, ringed by a whirl of tiny glass moths and glitter. Attack Swarm Bite: the cloud surges ahead
# and bites. Special Loose the Swarm: four moths peel off and chase the hero, bursting on him.
# ------------------------------------------------------------------------------------------------
def tiny_moth(x, y, beat, far=False):
    x, y = int(round(x)), int(round(y))
    w = ("wb", "wB", "wv") if far else ("wB", "wc", "wv")
    px = {(x, y): "n" if not far else "q", (x, y + 1): "q", (x, y - 1): "N" if not far else "n"}
    if beat % 2 == 0:      # wings up
        px.update({(x - 1, y - 1): w[1], (x + 1, y - 1): w[1], (x - 2, y - 2): w[0], (x + 2, y - 2): w[0],
                   (x - 1, y): w[0], (x + 1, y): w[0], (x - 2, y - 1): w[2], (x + 2, y - 1): w[2]})
    else:                  # wings down
        px.update({(x - 1, y): w[1], (x + 1, y): w[1], (x - 2, y): w[0], (x + 2, y): w[0],
                   (x - 2, y + 1): w[2], (x + 2, y + 1): w[2], (x - 1, y + 1): w[0], (x + 1, y + 1): w[0]})
    return px


def swarm(phase=0.0, bob=0, dx=0, eye="open", glow=False, hover=6, glint=0, spread=1.0, surge=0.0, extra=(),
          cracks=0, n=15, drop=0.0, core=True):
    c = C()
    cx, cy = dx, -hover - 16 + bob
    moths = []
    for i in range(n):
        a = phase * 60 + i * 360.0 / n + 14 * math.sin(i * 1.7)
        r = (13 + 3 * math.sin(i * 2.3 + phase)) * spread
        x = cx + r * math.cos(math.radians(a)) + surge * (6 + 5 * math.cos(math.radians(a)))
        y = cy + r * 0.8 * math.sin(math.radians(a)) + drop * (12 + i % 4)
        y = min(y, -2.0)
        moths.append((math.sin(math.radians(a)), x, y, i))
    for sa, x, y, i in sorted(moths):
        if sa < 0: put_px(c, tiny_moth(x, y, i + int(phase * 4), far=True))
    if core:
        put_px(c, dust_px(cx, cy, 12 * spread, int(phase * 10) + 3, 22))
        put_px(c, glass_wing_stub(cx, cy, glint))
        put_px(c, U.mirror_shard(cx, cy, 0, glint=glint * 1.5 - 3, scale=1.8, cracks=cracks, eye=eye, glow=glow))
    for sa, x, y, i in sorted(moths):
        if sa >= 0: put_px(c, tiny_moth(x, y, i + int(phase * 4)))
    return finish_spr(c, extra)


def glass_wing_stub(cx, cy, glint=0):
    out = {}
    for s in (-1, 1):
        w = [(cx + s * 1, cy - 4), (cx + s * 9, cy - 10), (cx + s * 10, cy - 3), (cx + s * 5, cy + 3), (cx + s, cy + 1)]
        out.update(pane_wing(w, glint, far=s < 0, veins_from=(cx + s, cy - 1)))
    return out


@sheet
def build_UmbGlitterswarm(outdir):
    idle = [swarm(phase=i * 0.25, bob=[0, -1, -1, 0][i], glint=i) for i in range(4)]
    run = [swarm(phase=i * 0.33, bob=[0, -1, -2, -1, 0, 1][i], dx=1, glint=i, surge=0.25) for i in range(6)]
    # Bite: the whirl draws in (0-1), surges ahead (2: hit), boils at the front (3), drifts back (4-6)
    bite = [
        swarm(phase=0.0, spread=0.8, eye="glare", glint=1),
        swarm(phase=0.3, spread=0.7, eye="glare", glow=True, dx=-1, glint=2),
        swarm(phase=0.6, spread=0.9, surge=1.6, eye="glare", glint=3, extra=[U.sparkle(26, -22, True)]),
        swarm(phase=0.9, spread=1.0, surge=1.3, eye="glare", glint=4),
        swarm(phase=1.2, spread=1.0, surge=0.7, glint=5),
        swarm(phase=1.5, spread=1.0, surge=0.3, glint=0),
        swarm(phase=1.8, spread=1.0, glint=1),
    ]
    # Loose: the whirl tightens (0-1), flares wide (2), four moths break away forward (3: release), the rest reform
    loose = [
        swarm(phase=0.0, spread=0.75, glint=0, eye="glare"),
        swarm(phase=0.4, spread=0.6, glint=1, eye="glare", glow=True),
        swarm(phase=0.8, spread=1.35, glint=2, eye="glare", glow=True, extra=[flash_px(0, -20, 2)]),
        swarm(phase=1.2, spread=1.1, glint=3, eye="glare", n=11,
              extra=[tiny_moth(19, -28, 0), tiny_moth(23, -22, 1), tiny_moth(19, -15, 0), tiny_moth(24, -33, 1)]),
        swarm(phase=1.6, spread=1.0, glint=4, n=11),
        swarm(phase=2.0, spread=1.0, glint=5, n=13),
        swarm(phase=2.4, spread=1.0, glint=0),
    ]
    dead = U.ground(swarm(phase=0.5, hover=-8, eye="shut", cracks=4, drop=1.0, spread=1.2)).over(
        Spr({(x, 0): ("wb" if x % 3 else "wB") for x in range(-12, 13, 2)}))
    death = [
        swarm(phase=0.2, eye="shut", cracks=2, spread=1.2, extra=[U.sparkle(4, -30)]),
        swarm(phase=0.5, eye="shut", cracks=3, spread=1.3, hover=2, drop=0.4),
        U.ground(swarm(phase=0.8, eye="shut", cracks=4, spread=1.25, hover=-4, drop=0.8)),
        dead,
    ]
    knock = swarm(phase=0.2, dx=-2, eye="shut", spread=1.15, cracks=1, surge=-0.6)
    anims = anims_std("UmbGlitterswarm", idle, run, death, dead, knock,
                      [("Bite", bite, [0.1, 0.12, 0.06, 0.08, 0.1, 0.1, 0.12]),
                       ("Loose", loose, [0.12, 0.14, 0.1, 0.08, 0.1, 0.12, 0.12])], idle_d=(0.1,) * 4, run_d=0.07)
    return U.build_sheet("UmbGlitterswarm", anims, outdir)


EVENTS["UmbGlitterswarm"] = {"Bite": [("surge hits (swarm bite box ahead of the heart)", 2)],
                             "Loose": [("release (4 FxUmbSwarmMoth from (20, -24))", 3)]}


# ================================================================================================
# HOURGLASS LINE (time that will not stay spent)
# ================================================================================================
# ------------------------------------------------------------------------------------------------
# THE PENDULUM (T3, Hourglass): a floating bronze clock whose face is the dark mirror with the Glimmer's eye at
# its centre; the hourglass's crystal wings flank it and the bronze of its frame is now the clock case. Below
# swings a pendulum whose bob is a glass crescent blade with a vial of shadow sand at its heart.
# Attack Swing: the pendulum scythes forward. Special Toll: the clock strikes; a ring of sound bursts out and
# throws the hero back.
# ------------------------------------------------------------------------------------------------
def clock_face(cx, cy, r=7, eye="open", glow=False, glint=0, hands=(-60, 20), cracks=0, shake=0):
    px = {}
    for (x, y) in ell(cx, cy, r, r):
        d = math.hypot(x - cx, y - cy)
        if d > r - 1.6:
            px[(x, y)] = ("hW" if (x - cx) + (y - cy) < -r * 0.6 else "hw") if (x < cx or y < cy) else (
                "hA" if (x - cx) + (y - cy) > r * 0.5 else "he")
        else:
            px[(x, y)] = "q" if (x * 2 + y + glint) % 7 else "b"
            if (x - cx) + (y - cy) < -r * 0.9 and d > r - 3: px[(x, y)] = "n"
    for t in (0, 90, 180, 270):          # hour ticks
        a = math.radians(t)
        px[(int(round(cx + (r - 2.2) * math.cos(a))), int(round(cy + (r - 2.2) * math.sin(a))))] = "hW"
    for ang, ln, col in ((hands[0], r - 3, "u"), (hands[1], r - 2, "U")):
        for p in lpts((cx, cy), add((cx, cy), pol(ang, ln))):
            px[p] = col
    # the Glimmer's eye at the hub
    for (ox, oy, col) in (((-1, 0, "U"), (0, 0, "c"), (1, 0, "X" if glow else "c"), (0, -1, "u"), (0, 1, "U"))
                          if eye != "shut" else ((-1, 0, "n"), (0, 0, "U"), (1, 0, "n"))):
        px[(cx + ox, cy + oy)] = col if eye != "glare" or col == "n" else ("X" if (ox, oy) == (0, 0) else "c")
    if cracks:
        rnd = random.Random(cracks)
        for _ in range(cracks):
            x, y, d = float(cx), float(cy), rnd.uniform(0, 360)
            for st in range(r - 1):
                d += rnd.uniform(-35, 35); x += math.cos(math.radians(d)); y += math.sin(math.radians(d))
                k = (int(round(x)), int(round(y)))
                if k in px and px[k] not in ("hw", "hW", "he", "hA"): px[k] = "c" if st < 2 else "u"
    return px


def crescent_blade(x, y, ang, w=6, sand=True, glint=0):
    """Pendulum bob: a glass crescent (horns up) with a sand vial at its heart. (x, y) = rod end."""
    px = {}
    for i in range(-w, w + 1):
        t = i / float(w)
        for j in range(3):
            yy = 3 + 2.6 * (t * t) * -1 + j - 0.6 * j * abs(t)
            q = rotate_pt((i, yy), ang)
            k = (int(round(x + q[0])), int(round(y + q[1])))
            col = ("c" if j == 0 else "B" if j == 1 else "b") if abs(i) > 1 else "hw"
            if abs(i) == w: col = "X" if (i > 0) == (glint % 2 == 0) else "c"
            px[k] = col
    if sand:
        for (ox, oy, col) in ((0, 2, "hA"), (0, 3, "hS"), (0, 4, "hs"), (0, 5, "hA")):
            q = rotate_pt((ox, oy), ang)
            px[(int(round(x + q[0])), int(round(y + q[1])))] = col
    return px


def rotate_pt(p, ang):
    a = math.radians(ang)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


def pendulum(swing=0, bob=0, dx=0, eye="open", glow=False, glint=0, flap=0, hands=(-60, 20), cracks=0, shake=0,
             hover=0, extra=(), wings=True, rod=12):
    c = C()
    cx, cy = dx + shake, -27 + bob - hover
    fa = U.FLAP[flap % 4] if isinstance(flap, int) else flap
    if wings:
        put_px(c, U.crystal_wing((cx - 8, cy + 1), fa, 9, back=True))
    # pendulum: pivot under the face, rod, crescent blade (swing: deg, + = forward)
    pv = (cx, cy + 8)
    end = add(pv, pol(90 - swing, rod))
    line(c, pv, end, "he")
    line(c, add(pv, (-1, 0)), add(end, (-1, 0)), "hA", over=False)
    put_px(c, crescent_blade(end[0], end[1], -swing, w=8, glint=glint))
    # finial on top + the case
    for (ox, oy, col) in ((0, -11, "hW"), (-1, -10, "hw"), (0, -10, "hw"), (1, -10, "he"), (0, -12, "hS")):
        c.put(cx + ox, cy + oy, col)
    put_px(c, clock_face(cx, cy, 9, eye, glow, glint, hands, cracks))
    if wings:
        put_px(c, U.crystal_wing((cx + 9, cy + 1), -180 - fa, 9))
    return finish_spr(c, extra)


def toll_ring(cx, cy, r, k=0):
    px = {}
    for t in range(0, 360, 8):
        if (t // 8 + k) % 4 == 0: continue
        a = math.radians(t)
        px[(int(round(cx + r * math.cos(a))), int(round(cy + r * 0.8 * math.sin(a))))] = "hW" if t % 24 else "hS"
    return px


@sheet
def build_UmbPendulum(outdir):
    idle = [pendulum(swing=[-14, -6, 14, 6][i], bob=[0, -1, -1, 0][i], glint=i, flap=i, hands=(-60 + 6 * i, 20 + 30 * i))
            for i in range(4)]
    run = [pendulum(swing=[-24, -10, 8, 24, 10, -8][i], bob=[0, -1, -2, -1, 0, 1][i], dx=1, glint=i, flap=i % 4)
           for i in range(6)]
    # Swing: draw the pendulum far back (0-1), scythe through (2), the blade crosses the front (3: hit), overshoot (4),
    # swing back (5), settle (6)
    swing = [
        pendulum(swing=-45, eye="glare", glint=1, flap=0),
        pendulum(swing=-70, eye="glare", glow=True, dx=-1, glint=2, flap=1, extra=[U.sparkle(-12, -12)]),
        pendulum(swing=15, eye="glare", glint=3, flap=2, dx=1),
        pendulum(swing=62, eye="glare", glint=4, flap=3, dx=1,
                 extra=[U.slash(2, -19, 17, 120, 25, thick=2, cols=("c", "u", "B", "b"))]),
        pendulum(swing=78, glint=5, flap=0, dx=1),
        pendulum(swing=30, glint=0, flap=1),
        pendulum(swing=-5, glint=1, flap=2),
    ]
    # Toll: the hands spin to the hour (0-1), the case shudders (2), STRIKE: a ring of sound bursts out (3),
    # rings widen (4-5), fade (6-7)
    toll = [
        pendulum(swing=-10, eye="glare", glint=0, hands=(-90, 120)),
        pendulum(swing=-20, eye="glare", glow=True, glint=1, hands=(-90, -90), extra=[U.sparkle(0, -40)]),
        pendulum(swing=-25, eye="glare", glow=True, glint=2, hands=(-90, -90), shake=1),
        pendulum(swing=25, eye="glare", glow=True, glint=3, hands=(-90, -90), shake=-1,
                 extra=[toll_ring(0, -27, 13, 0), flash_px(0, -40, 2, ("X", "hW", "hw"))]),
        pendulum(swing=35, eye="glare", glint=4, hands=(-90, -90), shake=1, extra=[toll_ring(0, -27, 16, 1)]),
        pendulum(swing=10, glint=5, hands=(-90, -85), extra=[toll_ring(0, -27, 19, 2)]),
        pendulum(swing=-10, glint=0, hands=(-80, -60)),
        pendulum(swing=-6, glint=1, hands=(-60, 20)),
    ]
    dead = U.ground(Spr(shift_px(rotate_px(clock_face(0, 0, 9, "shut", False, 0, (40, 160), 4), 70), 0, -9))).over(
        Spr(crescent_blade(-15, -8, 80, w=8))).over(Spr({(x, 0): "he" for x in range(-9, -2)}))
    death = [
        pendulum(swing=-40, eye="shut", cracks=2, glint=1, hands=(100, 100), extra=[U.sparkle(5, -34)]),
        pendulum(swing=50, eye="shut", cracks=3, glint=2, hover=-8, flap=2, hands=(150, 30)),
        U.ground(Spr(shift_px(rotate_px(pendulum(swing=0, eye="shut", cracks=4, wings=False, hands=(160, 60)).px, 50), 0, 8))),
        dead,
    ]
    knock = pendulum(swing=-35, dx=-2, eye="shut", cracks=1, glint=1, hands=(-60, 20))
    anims = anims_std("UmbPendulum", idle, run, death, dead, knock,
                      [("Swing", swing, [0.14, 0.16, 0.05, 0.06, 0.1, 0.12, 0.12]),
                       ("Toll", toll, [0.12, 0.16, 0.16, 0.06, 0.08, 0.1, 0.12, 0.12])], idle_d=(0.25,) * 4, run_d=0.08)
    return U.build_sheet("UmbPendulum", anims, outdir)


EVENTS["UmbPendulum"] = {"Swing": [("blade crosses the front: hit (FxUmbPendulumArc)", 3)],
                         "Toll": [("strike: FxUmbToll ring bursts from the clock (0, -27)", 3)]}


# ------------------------------------------------------------------------------------------------
# SAND WRAITH (T3, Hourglass): the hourglass has burst. In what is left of its bronze cage stands a hooded
# wraith of shadow sand with the Glimmer's single eye, its body pouring into the dune at its feet, its arms long
# streamers of sand reaching out between the bent posts. Attack Sand Bolt: it hurls a fist of sand. Special
# Sandfall: it lifts its arms and sand pours down on four marked spots around the hero.
# ------------------------------------------------------------------------------------------------
def sand_arm(c, sh, segs, k=0, hand=True):
    """A streamer of sand from the shoulder: a 2-px band that frays into grains at the hand."""
    pts = [sh]
    x, y = sh
    for ln, ang in segs:
        x, y = x + ln * math.cos(math.radians(ang)), y + ln * math.sin(math.radians(ang))
        pts.append((x, y))
    for i, (a_, b_) in enumerate(zip(pts, pts[1:])):
        line(c, a_, b_, "hs")
        line(c, add(a_, (0, 1)), add(b_, (0, 1)), "n", over=False)
    ex, ey = int(round(pts[-1][0])), int(round(pts[-1][1]))
    if hand:
        for (ox, oy, col) in ((1, -1, "hS"), (1, 1, "hS"), (2, 0, "X"), (2, -2, "hs"), (2, 2, "hs")):
            c.put(ex + ox, ey + oy, col)
    for g in range(3):
        c.put(ex - 2 - g * 2 + (k + g) % 2, ey + 2 + g, "hS" if g % 2 else "hs", over=False)
    return ex, ey


def wraith(lean=0, dy=0, dx=0, arms=((150, 110), (30, 70)), eye="open", glow=False, glint=0, k=0, cage=1.0,
           pile=1.0, extra=(), hood=0, sink=0.0, hand_l=True, hand_r=True):
    c = C()
    # cage: the bottom cap, two bent posts, the broken top cap tilted
    for x in range(-9, 10):
        c.put(x, -1, "he" if x > -8 else "hw"); c.put(x, 0, "hA")
    c.put(-9, -1, "hW")
    for y in range(-2, -int(30 * cage), -1):
        bend = 0.5 * math.sin((y + 2) / 6.0)
        c.put(int(round(-9 + bend)), y, "hw" if y % 5 else "hW")
    for y in range(-2, -int(18 * cage), -1):                     # the right post is snapped short
        c.put(9 + (1 if y < -12 else 0), y, "he")
    tx0, ty0 = -10, -int(30 * cage)
    for i in range(12):
        c.put(tx0 + i, ty0 - i // 4, "hw" if i < 9 else "he")
        c.put(tx0 + i, ty0 - i // 4 + 1, "hA", over=False)
    # broken bulb glass: shards clinging to the caps
    for (x, y, ang) in ((-7, -3, -60), (6, -3, -120), (-6, ty0 + 3, 70), (0, ty0 + 2, 100)):
        put_px(c, U.small_shard(x, y, ang, 3, ("u", "B", "b")))
    # the dune at its feet
    for x in range(-8, 9):
        h = int(round(pile * (4 - abs(x) * 0.42)))
        for y in range(1, h + 1):
            c.put(x, -1 - y, "hS" if y == h else ("hs" if (x + y + k) % 3 else "N"))
    # the body: a column of sand narrowing into the dune
    top = (dx + lean, -26 + dy + sink * 10)
    body = poly([(top[0] - 4, top[1] + 3), (top[0] + 4, top[1] + 3), (top[0] + 2 + lean, -6), (top[0] - 2 + lean, -6)])
    for (x, y) in body:
        e_l = (x - 1, y) not in body; e_r = (x + 1, y) not in body
        c.put(x, y, "hS" if e_l else ("n" if e_r else ("hs" if (x * 3 + y + k) % 4 else "N")))
    for y in range(-6, -3):            # pour into the dune
        c.put(top[0] + lean + (y + k) % 2, y, "hS")
    # hood
    hx, hy = top[0] + 1, top[1]
    hd = poly([(hx - 5, hy + 4), (hx - 4, hy - 3), (hx, hy - 6 - hood), (hx + 4, hy - 2), (hx + 5, hy + 4)])
    for (x, y) in hd:
        e = any((x + a, y + b) not in hd for a, b in ((1, 0), (-1, 0), (0, -1)))
        c.put(x, y, ("N" if (x - hx) + (y - hy) < 0 else "n") if e else "K")
    ex, ey = hx + 1, hy
    if eye != "shut":
        for (ox, oy, col) in ((-1, 0, "U"), (0, 0, "X" if glow or eye == "glare" else "c"), (1, 0, "c"), (0, -1, "u"),
                              (0, 1, "U")):
            c.put(ex + ox, ey + oy, col)
    else:
        c.put(ex - 1, ey, "n"); c.put(ex, ey, "U"); c.put(ex + 1, ey, "n")
    # arms of sand: back (left) then front (right)
    sand_arm(c, (top[0] - 3, top[1] + 4), [(6, arms[0][0]), (6, arms[0][1])], k, hand_l)
    sand_arm(c, (top[0] + 3, top[1] + 4), [(6, arms[1][0]), (6, arms[1][1])], k + 1, hand_r)
    return finish_spr(c, extra)


def sand_ball_px(x, y, r=2, k=0):
    px = {}
    for (xx, yy) in ell(x, y, r, r):
        px[(xx, yy)] = "hS" if (xx - x) + (yy - y) < 0 else ("hs" if (xx + yy + k) % 3 else "N")
    px[(int(x) - 1, int(y) - 1)] = "X"
    return px


@sheet
def build_UmbSandWraith(outdir):
    idle = [wraith(arms=((150 + 4 * (i % 2), 115 - 6 * i), (30 - 4 * (i % 2), 65 + 6 * i)), dy=[0, 0, 1, 1][i], k=i,
                   glint=i, pile=1.0 + 0.04 * i) for i in range(4)]
    run = [wraith(lean=1, arms=((170, 150), (10, 30)), dy=[0, -1, 0, 0, -1, 0][i], k=i, glint=i) for i in range(6)]
    # Bolt: draw the front arm back over the hood (0-1), hurl (2: release from (13, -20)), follow through, settle
    bolt = [
        wraith(arms=((150, 120), (-120, -160)), eye="glare", k=0, extra=[sand_ball_px(-1, -36, 2)]),
        wraith(lean=-1, arms=((160, 130), (-150, 170)), eye="glare", glow=True, k=1, extra=[sand_ball_px(-8, -32, 2, 1)]),
        wraith(lean=2, arms=((170, 150), (-10, 0)), eye="glare", k=2, hand_r=False,
               extra=[sand_ball_px(15, -20, 2, 2), flash_px(13, -20, 1, ("X", "hS"))]),
        wraith(lean=2, arms=((165, 140), (20, 40)), k=3),
        wraith(lean=1, arms=((155, 125), (30, 60)), k=0),
        wraith(arms=((150, 115), (30, 65)), k=1),
    ]
    # Sandfall: arms sink (0), rise (1-2), sand spirals up out of the cage (3: the marks fall at the hero), pour
    # (4-5), arms fall (6-7)
    fall = [
        wraith(arms=((120, 90), (60, 90)), k=0, hood=0, eye="open"),
        wraith(arms=((-150, -120), (-30, -60)), k=1, eye="glare", hood=1),
        wraith(arms=((-130, -100), (-50, -80)), k=2, eye="glare", glow=True, hood=1, extra=[dust_spiral(0, -36, 0)]),
        wraith(arms=((-120, -95), (-60, -85)), k=3, eye="glare", glow=True, hood=1, pile=0.8,
               extra=[dust_spiral(0, -38, 1), flash_px(0, -40, 2, ("X", "hS", "hs"))]),
        wraith(arms=((-125, -100), (-55, -80)), k=0, eye="glare", hood=1, pile=0.6, extra=[dust_spiral(0, -38, 2)]),
        wraith(arms=((-140, -110), (-40, -70)), k=1, hood=0, pile=0.6),
        wraith(arms=((150, 110), (30, 70)), k=2, pile=0.8),
        wraith(arms=((150, 115), (30, 65)), k=3),
    ]
    dead = wraith(arms=((175, 180), (5, 0)), sink=1.0, eye="shut", cage=0.45, pile=1.6, hand_l=False, hand_r=False)
    death = [
        wraith(arms=((-150, -120), (-30, -60)), eye="shut", lean=-1, k=0),
        wraith(arms=((170, 160), (10, 20)), eye="shut", sink=0.35, cage=0.8, pile=1.2, k=1),
        U.dissolve(wraith(arms=((175, 175), (5, 5)), eye="shut", sink=0.7, cage=0.6, pile=1.4, k=2), 0.3, seed=4,
                   rise=2, smoke="hsN"),
        dead,
    ]
    knock = wraith(lean=-2, arms=((-160, -130), (-110, -80)), eye="shut", k=1)
    anims = anims_std("UmbSandWraith", idle, run, death, dead, knock,
                      [("Bolt", bolt, [0.12, 0.16, 0.05, 0.08, 0.1, 0.12]),
                       ("Sandfall", fall, [0.1, 0.14, 0.14, 0.08, 0.12, 0.12, 0.12, 0.14])], idle_d=(0.2, 0.16, 0.2, 0.16),
                      run_d=0.08)
    return U.build_sheet("UmbSandWraith", anims, outdir)


def dust_spiral(cx, cy, k):
    px = {}
    for i in range(14):
        a = math.radians(i * 40 + k * 30)
        r = 2 + i * 0.6
        px[(int(round(cx + r * math.cos(a))), int(round(cy + r * 0.5 * math.sin(a) + i * 0.7)))] = "hS" if i % 3 else "X"
    return px


EVENTS["UmbSandWraith"] = {"Bolt": [("release (FxUmbSandBall from the hand, (13, -20))", 2)],
                           "Sandfall": [("the sand rises: 4 FxUmbSandfall marks land round the hero", 3)]}


# ================================================================================================
# THE SUNDERED (T3, The Twinned): the fused twins have torn apart. The dark twin stands tall with a long sabre in
# each hand; a step behind it the pale reflection follows every move a moment late, see-through, still joined to
# it at the waist by a fraying thread of shadow. The imp's white eye and smoky tail. Attack Cross Cut: both
# sabres scissor shut ahead. Special Afterimage: it dashes clean through the hero, and 0.6 s later its pale
# reflection runs the same line again.
# ================================================================================================
SD_HEAD = {
    "calm": Part("""
n....n.
.nnnn..
qnnnnn.
qqqqKc.
qqqqqU.
.qqqq..
""", (2, 5)),
    "glare": Part("""
n....n.
.nnnn..
qnnnnn.
qqqKcX.
qqqqcU.
.qqqq..
""", (2, 5)),
    "hurt": Part("""
n......
.nnnn.n
qnnnnn.
qqqqqU.
qqqqqn.
.qqqq..
""", (2, 5)),
}
SD_BOOT = Part("qnnU", (0, 0))


def duelist(c, hip, lean=10, legs=((110, 80), (70, 100)), arms=((60, 20), (40, 0)), sabres=(10, -20), head="calm",
            glint=(False, False), scarf=0, pale=False):
    """One figure. arms/sabres: (back arm, front arm)."""
    hp = (hip[0], hip[1])
    col = (lambda v: v) if not pale else (lambda v: {"q": "tq", "n": "tn", "N": "tN", "m": "tm", "K": "tK"}.get(v, v))
    c.limb(hp[0] - 1, hp[1], [(6, legs[0][0]), (6, legs[0][1])], [(col("q"), col("q")), col("q")], width=2, end=SD_BOOT)
    tp, top = U.torso_px((hp[0], hp[1] - 1), -90 + lean, 11, 2.6, 4.2)
    tp = U.shade_body(tp, lit="n", hi="N", dark="m")
    sh = (top[0] - 1, top[1] + 2)
    hx, hy = c.limb(sh[0], sh[1], [(5, arms[0][0]), (5, arms[0][1])], [col("q")])
    U.blade(c, hx, hy, sabres[0], length=12, glint=glint[0], col=("U", "s"))
    put_px(c, {k: col(v) for k, v in tp.items()})
    # tattered scarf streaming back from the neck
    for i in range(6):
        x = top[0] - 2 - i; y = top[1] + 1 + int(round(0.5 * i + math.sin(scarf + i * 0.9)))
        c.put(x, y, col("N") if i < 2 else col("n")); c.put(x, y + 1, col("q"), over=False)
    c.part(SD_HEAD[head], top[0] + 1, top[1] - 1)
    c.limb(hp[0] + 1, hp[1], [(6, legs[1][0]), (6, legs[1][1])], [(col("n"), col("q")), col("n")], width=2, end=SD_BOOT)
    hx, hy = c.limb(top[0] + 1, top[1] + 2, [(5, arms[1][0]), (5, arms[1][1])], [(col("n"), col("n"))])
    U.blade(c, hx, hy, sabres[1], length=13, glint=glint[1])
    c.put(hx, hy, "U")
    if pale:
        c.px.update({k: col(v) for k, v in c.px.items()})
    return top


def sundered(pose, lag=None, dx=0, dy=0, gap=(-10, -2), extra=(), thread=True, tail=0, pale_k=0.0, solo=False):
    """pose / lag: dicts of duelist() args for the dark twin and its late reflection (lag defaults to pose)."""
    lag = lag or pose
    c = C()
    hip = (dx, -13 + dy)
    if not solo:
        pc = C()
        duelist(pc, (hip[0] + gap[0], hip[1] + gap[1]), pale=True, **lag)
        ps = U.translucent(pc.spr(), phase=1, keep=0.55)
        if pale_k > 0: ps = U.dissolve(ps, pale_k, seed=5, rise=1, smoke=("tn", "tN", "tq"))
        put_px(c, ps.px)
        if thread:
            for i in range(abs(gap[0]) + 1):
                x = hip[0] + gap[0] + i; y = hip[1] + 1 + (1 if 0 < i < abs(gap[0]) else 0)
                if (i + tail) % 3: c.put(x, y, "N" if i % 2 else "n")
    U.imp_tail(c, hip[0] - 2, hip[1] + 2, tail % 4, curl=-30)
    duelist(c, hip, **pose)
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return U.ground(s)


def P(**k):
    return k


@sheet
def build_UmbSundered(outdir):
    rest = [P(lean=8 + (i % 2), arms=((70 + 4 * (i % 2), 30), (45 - 4 * (i % 2), 10)), sabres=(25, -5 - 4 * (i % 2)),
              scarf=i * 1.2) for i in range(4)]
    idle = [sundered(rest[i], rest[(i - 1) % 4], dy=[0, 0, 1, 1][i], tail=i) for i in range(4)]
    cyc = [((150, 95), (40, 80)), ((125, 70), (70, 120)), ((95, 65), (100, 120)),
           ((40, 80), (150, 95)), ((70, 120), (125, 70)), ((100, 120), (95, 65))]
    rp = [P(lean=22, legs=cyc[i], arms=((140, 120), (20, 30)), sabres=(160, 40), scarf=i * 1.5) for i in range(6)]
    run = [sundered(rp[i], rp[(i - 2) % 6], dy=-1 if i in (0, 3) else 0, gap=(-12, -1), tail=i) for i in range(6)]
    # Cross Cut: sabres raised and crossed (0-1), scissor down and shut ahead (2-3: hit on 3), hold, recover
    cross = [
        P(lean=0, arms=((-110, -80), (-90, -60)), sabres=(-60, -110), head="glare"),
        P(lean=-6, arms=((-130, -95), (-110, -80)), sabres=(-40, -130), head="glare", glint=(True, True)),
        P(lean=18, legs=((130, 90), (50, 90)), arms=((-60, -20), (-40, 0)), sabres=(-10, 30), head="glare"),
        P(lean=26, legs=((140, 100), (40, 85)), arms=((-10, 20), (10, 40)), sabres=(35, -35), head="glare", glint=(True, True)),
        P(lean=22, legs=((135, 95), (45, 90)), arms=((10, 40), (30, 60)), sabres=(50, -15)),
        P(lean=14, arms=((50, 30), (40, 20)), sabres=(30, 0)),
        rest[0],
    ]
    cr = [sundered(cross[i], cross[max(0, i - 1)], tail=i, extra=[U.slash(14, -14, 9, -70, 60, thick=2)] if i == 3 else [])
          for i in range(7)]
    # Afterimage: crouch (0-1), the dash: body stretched flat out ahead, reflection left behind (2-4), skid past
    # (5), turn and set (6-7)
    lunge = P(lean=55, legs=((175, 150), (10, 60)), arms=((170, 170), (0, 10)), sabres=(175, 5), head="glare", scarf=2)
    crouch = P(lean=30, legs=((150, 60), (30, 120)), arms=((130, 120), (60, 80)), sabres=(170, 20), head="glare")
    dash = [
        sundered(crouch, rest[0], dy=2, tail=0),
        sundered(P(lean=40, legs=((160, 70), (25, 130)), arms=((150, 150), (40, 60)), sabres=(175, 15), head="glare",
                   glint=(False, True)), crouch, dy=2, tail=1),
        sundered(lunge, crouch, dx=4, gap=(-16, 0), tail=2, extra=[speed_lines(-6, -16, 9, 0)]),
        sundered(lunge, crouch, dx=6, gap=(-18, 0), tail=3, extra=[speed_lines(-6, -16, 11, 1)]),
        sundered(P(lean=48, legs=((170, 140), (15, 70)), arms=((160, 160), (10, 20)), sabres=(170, 10), head="glare"),
                 lunge, dx=5, gap=(-13, -1), tail=0, extra=[speed_lines(-4, -16, 7, 2)]),
        sundered(P(lean=10, legs=((120, 70), (60, 120)), arms=((90, 60), (30, 0)), sabres=(40, -20)), lunge, dx=2, tail=1),
        sundered(rest[1], rest[0], tail=2),
        sundered(rest[2], rest[1], tail=3),
    ]
    dead = U.ground(Spr(flatten(U.rot_ccw(sundered(P(head="hurt", arms=((120, 100), (60, 90)), sabres=(100, 80)), solo=True)), 0.8).px)).over(
        Spr({(x, 0): "s" for x in range(-14, -6)} | {(-13, -1): "U", (12, 0): "u", (13, 0): "U", (14, 0): "u"}))
    death = [
        sundered(P(lean=-14, head="hurt", arms=((-130, -100), (-110, -80)), sabres=(-150, -100)), rest[0], tail=0),
        sundered(P(lean=-25, legs=((165, 60), (20, 150)), head="hurt", arms=((150, 120), (120, 100)), sabres=(120, 100)),
                 P(lean=-14, head="hurt"), dy=2, tail=1, pale_k=0.5),
        U.dissolve(sundered(P(lean=-40, legs=((170, 70), (15, 160)), head="hurt", arms=((160, 150), (140, 120)),
                              sabres=(130, 110)), solo=True, dy=3, tail=2), 0.2, seed=3, rise=2),
        dead,
    ]
    knock = sundered(P(lean=-16, head="hurt", arms=((-140, -110), (-120, -90)), sabres=(-150, -110)), rest[0], dx=-2, tail=3)
    anims = anims_std("UmbSundered", idle, run, death, dead, knock,
                      [("Cross", cr, [0.12, 0.14, 0.05, 0.06, 0.1, 0.12, 0.12]),
                       ("Dash", dash, [0.1, 0.14, 0.06, 0.06, 0.06, 0.1, 0.12, 0.12])], idle_d=(0.18, 0.16, 0.18, 0.16))
    return U.build_sheet("UmbSundered", anims, outdir)


def speed_lines(x, y, ln, k):
    px = {}
    for j, yy in enumerate((-6, -2, 2, 6)):
        for i in range(int(ln - abs(j - 1.5) * 2)):
            if (i + k + j) % 4: px[(x - i - j, y + yy)] = "tN" if i < 3 else "tn"
    return px


EVENTS["UmbSundered"] = {"Cross": [("sabres shut: hit (FxUmbScissor, x 6..22)", 3)],
                         "Dash": [("dash starts (body hit on, path start recorded)", 2), ("dash ends (afterimage queued)", 5)]}


# ================================================================================================
# BRISTLEBACK (T3, Nailshade): the Nailshade dropped onto four legs and kept growing glass: a plum-rose
# brute of a hound whose whole back is a thicket of long glass nails, with the Nailshade's mirror-shard face and
# the imp's smoky tail. Attack Nail Lob: it shakes a volley of three nails up over itself; they stick in the floor
# as caltrops for 4 s. Special Bristle: it hunkers down and raises every nail; for 3 s anything that strikes it
# is pierced (thorns).
# ================================================================================================
BB_HEAD = {
    "calm": Part("""
..nnn...
.nqqqnU.
nqqqqUuu
qqqqqUcu
qqqqqqUU
.qqUUqq.
..qqq...
""", (2, 6)),
    "snarl": Part("""
..nnn...
.nqqqnU.
nqqqqUcX
qqqqqUXc
qqqqKpKU
.qqUqUq.
..qUqU..
""", (2, 6)),
    "hurt": Part("""
..nnn...
.nqqqns.
nqqqqUus
qqqqqqUu
qqqqqqqU
.qqqqqq.
..qqq...
""", (2, 6)),
}


def bristleback(dx=0, dy=0, legs=(0, 0, 0, 0), head="calm", rear=0.0, crouch=0.0, nails=1.0, glint=0, tail=0,
                extra=(), shake=0, glow=False, n_nails=17):
    """legs: swing (deg) of the 4 legs (back-far, back-near, front-far, front-near); rear: front lifted (0..1);
    crouch: belly to the floor (0..1); nails: nail length factor."""
    c = C()
    by = -12 + dy + 4 * crouch
    bx = dx
    tilt = -12 * rear
    # far legs (darker)
    for (lx, sw) in ((bx - 7, legs[0]), (bx + 7, legs[2])):
        ly = by + 3 + (-(lx - bx) * math.sin(math.radians(tilt)) if lx > bx else 0)
        c.limb(lx, ly, [(5 - 2 * crouch, 100 + sw), (4 - crouch, 80 + sw * 0.5)], [("q", "q"), "q"], width=2,
               end=Part("qn", (0, 0)))
    U.imp_tail(c, bx - 11, by - 1, tail % 4, curl=-10)
    body = U.rot_ellipse(bx, by, 11.5, 6.2, tilt)
    body.update(U.rot_ellipse(bx + 7, by - 1 + 3 * math.sin(math.radians(tilt)), 6, 5.5, tilt))
    body = U.shade_body(body)
    for (x, y), v in list(body.items()):           # bristly fur: lit flank streaks, darker belly
        if v != "q": continue
        if y < by - 1 and (x * 2 + y) % 3 == 0: body[(x, y)] = "n" if (x + y) % 4 else "N"
        elif y < by + 2 and (x + y * 3) % 4 == 0: body[(x, y)] = "n"
        elif y > by + 3: body[(x, y)] = "m"
    for t in range(-8, 8, 3):                      # moonlit spine seam
        k = (int(round(bx + t)), int(round(by - 4 + t * math.sin(math.radians(tilt)))))
        if body.get(k) == "q": body[k] = "n"
    put_px(c, body)
    # the thicket: nails fanned over the back from rump to shoulders
    for i in range(n_nails):
        f = i / (n_nails - 1.0)
        th = math.radians(200 + 150 * f + tilt)
        x0 = bx + 10.5 * math.cos(th) * 0.95; y0 = by + 5.8 * math.sin(th) * 0.95 + (shake if i % 2 else -shake) * 0.5
        ang = math.degrees(th) + 10 * math.sin(i * 2.1) - 20 * crouch * math.cos(th)
        ln = int(round(([4, 6, 5, 7, 5, 8, 6, 5, 7][i % 9]) * nails))
        put_px(c, U.nail_px(x0, y0, ang, ln, glint=(i == glint % n_nails) or (glow and i % 3 == 0)))
    # head: low and forward of the shoulders
    hx = int(round(bx + 13 + 2 * rear)); hy = int(round(by - 1 - 6 * rear + 2 * crouch))
    c.part(BB_HEAD[head], hx, hy)
    for (lx, sw) in ((bx - 5, legs[1]), (bx + 9, legs[3])):
        ly = by + 4 - (4 * rear if lx > bx else 0)
        c.limb(lx, ly, [(5 - 2 * crouch, 100 + sw - (30 * rear if lx > bx else 0)), (4 - crouch, 85 + sw * 0.5)],
               [("n", "q"), "n"], width=2, end=Part("nnU", (0, 0)))
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return U.ground(s)


@sheet
def build_UmbBristleback(outdir):
    idle = [bristleback(dy=[0, 0, 1, 1][i] * 0, legs=(0, 0, 0, 0), glint=i * 4, tail=i, nails=1.0 + 0.04 * (i % 2),
                        head="calm") for i in range(4)]
    g = [(-25, 20, 20, -25), (-10, 5, 5, -10), (10, -10, -10, 10), (25, -20, -20, 25), (10, -5, -5, 10), (-10, 10, 10, -10)]
    run = [bristleback(legs=g[i], dy=-1 if i in (1, 4) else 0, glint=i * 3, tail=i, shake=(i % 2) * 2 - 1) for i in range(6)]
    # Nail Lob: rear up (0-1), slam the forefeet and shake (2), three nails fly up off the back (3: release from
    # (0, -24)), settle (4-6)
    lob = [
        bristleback(rear=0.5, legs=(10, 0, -30, -40), head="snarl", glint=1),
        bristleback(rear=0.9, legs=(15, 5, -50, -60), head="snarl", glint=2, nails=1.1),
        bristleback(rear=-0.2, crouch=0.3, legs=(0, 0, 20, 25), head="snarl", shake=2, glint=3, n_nails=15),
        bristleback(crouch=0.2, legs=(0, 0, 10, 10), head="snarl", shake=-2, glint=4, n_nails=14,
                    extra=[U.nail_px(-3, -26, -110, 5), U.nail_px(2, -29, -80, 5), U.nail_px(7, -26, -55, 5),
                           flash_px(2, -24, 1)]),
        bristleback(legs=(0, 0, 5, 5), head="calm", glint=5, n_nails=15),
        bristleback(legs=(0, 0, 0, 0), glint=6, n_nails=16),
        bristleback(glint=7),
    ]
    # Bristle: hunker (0-1), every nail rises and lengthens (2-4), glinting hold (5-6: the thorns are up)
    bristle = [
        bristleback(crouch=0.4, head="snarl", glint=0),
        bristleback(crouch=0.8, head="snarl", glint=2, nails=1.1),
        bristleback(crouch=1.0, head="snarl", glint=4, nails=1.3, shake=1),
        bristleback(crouch=1.0, head="snarl", glint=6, nails=1.45, shake=-1, glow=True, extra=[U.sparkle(-4, -26, True)]),
        bristleback(crouch=1.0, head="snarl", glint=8, nails=1.5, glow=True),
        bristleback(crouch=0.9, head="calm", glint=10, nails=1.45, glow=True),
        bristleback(crouch=0.8, head="calm", glint=12, nails=1.4),
    ]
    dead = bristleback(crouch=1.0, dy=3, head="hurt", nails=0.75, legs=(80, 70, -80, -70), n_nails=13).over(
        Spr(U.nail_px(-17, -1, 180, 4))).over(Spr(U.nail_px(18, -1, 0, 3)))
    death = [
        bristleback(rear=0.6, head="hurt", legs=(20, 10, -40, -50), glint=1),
        bristleback(crouch=0.6, head="hurt", legs=(40, 30, 40, 30), glint=2, nails=0.9,
                    extra=[U.nail_px(-8, -22, -150, 4), U.nail_px(6, -24, -40, 4)]),
        U.ground(bristleback(crouch=1.0, head="hurt", legs=(70, 60, 60, 70), nails=0.8, dy=2)),
        dead,
    ]
    knock = bristleback(rear=0.4, dx=-2, head="hurt", legs=(20, 20, -30, -30), glint=3)
    anims = anims_std("UmbBristleback", idle, run, death, dead, knock,
                      [("Lob", lob, [0.12, 0.14, 0.08, 0.06, 0.1, 0.1, 0.12]),
                       ("Bristle", bristle, [0.1, 0.1, 0.1, 0.12, 0.12, 0.12, 0.14])], idle_d=(0.2, 0.16, 0.2, 0.16))
    return U.build_sheet("UmbBristleback", anims, outdir)


EVENTS["UmbBristleback"] = {"Lob": [("release (3 FxUmbQuill lobbed from (2, -24); each lands as FxUmbCaltrop)", 3)],
                            "Bristle": [("nails up: thorns on for 3 s (FxUmbBristle overlay)", 3)]}


# ================================================================================================
# GLASS WIDOW (T3, Mirror Witch): the Mirror Witch, grown into the Gloom Lurker's shape she always carried
# under her hem: a slate-blue spider body with eight arched legs, the witch rising from its front - pointed
# hat, veil, teal eyes - with her hand mirror held out. Attack Glass Fang: the front legs stab down. Special
# Reel: she casts a glass thread from the mirror; if it catches the hero she reels him in to her fangs.
# ================================================================================================
def widow(dx=0, dy=0, lean=0, legs=0.0, rear=0.0, arm=(40, -40), mirror="face", back_arm=(110, 80), hat="up",
          veil="calm", stab=0.0, extra=(), sink=0.0, glint=0):
    """legs: walk phase; rear: front legs lifted (0..1); stab: front legs driven down/forward (0..1)."""
    c = C()
    ab = (dx - 8, int(round(-11 + dy + 3 * sink)))      # abdomen centre
    th = (dx + 2, int(round(-10 + dy + 3 * sink)))      # cephalothorax
    # far legs (behind): 4, dark
    def leg(hip, ang_up, ang_dn, ln1, ln2, col_up, col_dn, knee_c):
        kx, ky = hip[0] + ln1 * math.cos(math.radians(ang_up)), hip[1] + ln1 * math.sin(math.radians(ang_up))
        fx, fy = kx + ln2 * math.cos(math.radians(ang_dn)), ky + ln2 * math.sin(math.radians(ang_dn))
        fy = min(fy, 0)
        line(c, hip, (kx, ky), col_up); line(c, (kx, ky), (fx, fy), col_dn)
        c.put(int(round(kx)), int(round(ky)), knee_c)
    spec = [(-3, -150, 110, 7, 9), (-1, -125, 95, 7, 10), (2, -60, 85, 7, 10), (4, -35, 70, 7, 9)]
    for i, (ox, a1, a2, l1, l2) in enumerate(spec):
        sw = 10 * math.sin(legs + i * 1.6)
        lift = (-30 * rear - 25 * stab) if i == 3 else 0
        dn = (40 * stab) if i == 3 else 0
        leg((th[0] + ox - 1, th[1] - 1), a1 + sw + 6 + lift, a2 - sw + dn, l1, l2, "q", "q", "n")
    # abdomen: big slate ovoid with a mirror-glass hourglass-mark on its back (the Witch's mirror)
    abd = shade(ell(ab[0], ab[1], 8, 6.2))
    for (x, y), v in list(abd.items()):
        if v == "q" and (x + y * 2) % 5 == 0: abd[(x, y)] = "n"
    put_px(c, abd)
    for (ox, oy, col) in ((-1, -3, "u"), (0, -3, "c"), (1, -3, "u"), (0, -2, "B"), (-1, -1, "b"), (0, -1, "c"),
                          (1, -1, "b"), (0, 0, "B"), (-1, 1, "u"), (0, 1, "c"), (1, 1, "u")):
        c.put(ab[0] + ox - 1, ab[1] + oy - 1, col)
    put_px(c, shade(ell(th[0], th[1], 4.5, 3.6)))
    # the witch: robe torso rising from the thorax
    top = (th[0] + 2 + lean, int(round(th[1] - 11 - 2 * rear)))
    put_px(c, U.robe_px(top, 0, 0, height=9, w_top=2, w_hem=4))
    hx_, hy_ = c.limb(top[0] - 1, top[1] + 2, [(4, back_arm[0]), (4, back_arm[1])], ["q"])
    c.put(hx_, hy_, "U")
    head = (top[0] + 1, top[1] - 6)
    for k in range(3):
        c.limb(head[0] - 2, head[1] + 1 + k, [(4 + k, 115 + k * 8), (3, 100)], ["m" if k else "n"])
    c.part(U.MW_VEIL[veil], head[0], head[1])
    c.put(head[0] - 1, head[1] + 2, "lc"); c.put(head[0] + 1, head[1] + 2, "lc")
    c.part(U.MW_HAT[hat], head[0], head[1] - 1)
    sx, sy = top[0] + 2, top[1] + 2
    mx, my = c.limb(sx, sy, [(4, arm[0]), (4, arm[1])], ["n", "n"])
    c.part(U.MIRROR[mirror], mx, my)
    c.put(mx, my, "u")
    # near legs (front): 4, lit, the front pair are the fangs
    for i, (ox, a1, a2, l1, l2) in enumerate(spec):
        sw = 10 * math.sin(legs + i * 1.6 + 3.1)
        lift = (-45 * rear - 35 * stab) if i >= 2 else 0
        dn = (55 * stab) if i >= 2 else 0
        leg((th[0] + ox, th[1]), a1 + sw + lift * (1 if i == 3 else 0.6), a2 - sw + dn, l1 + 1, l2 + (1 if i == 3 else 0),
            "n", "N", "U")
    for (x, y) in ((th[0] + 4, th[1] + 2), (th[0] + 5, th[1] + 2)):     # chelicerae
        c.put(x, y, "c" if stab > 0.5 else "U")
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return U.ground(s)


def thread_px(x0, y0, x1, y1, k=0):
    px = {}
    for i, p in enumerate(lpts((x0, y0), (x1, y1))):
        px[p] = "c" if (i + k) % 3 == 0 else "u"
    return px


@sheet
def build_UmbGlassWidow(outdir):
    idle = [widow(legs=0.4 * i, dy=[0, 0, 1, 1][i] * 0, arm=(45 + 4 * (i % 2), -40 - 6 * (i % 2)),
                  mirror="face" if i != 2 else "edge", glint=i) for i in range(4)]
    run = [widow(legs=i * math.pi / 3, lean=1, arm=(30, -20), back_arm=(140, 120), mirror="edge", dy=-1 if i % 3 == 0 else 0)
           for i in range(6)]
    # Fang: rear (0-1), stab down (2-3: hit on 3), hold, recover
    fang = [
        widow(rear=0.6, arm=(100, -150), mirror="edge", veil="glow", hat="bent"),
        widow(rear=1.0, lean=-1, arm=(110, -160), mirror="edge", veil="glow", hat="bent", extra=[U.sparkle(16, -16)]),
        widow(rear=0.2, stab=0.6, lean=2, arm=(30, -30), mirror="face", veil="glow"),
        widow(stab=1.0, lean=3, dy=1, arm=(20, -20), mirror="face", veil="glow",
              extra=[U.slash(17, -6, 6, -70, 70, thick=1), flash_px(19, -3, 1)]),
        widow(stab=0.8, lean=2, dy=1, arm=(30, -30)),
        widow(stab=0.3, lean=1, arm=(40, -40)),
        widow(arm=(45, -40)),
    ]
    # Reel: mirror drawn back (0-1), cast: the thread shoots out (2-3: release on 3), hold taut (4-5), YANK (6:
    # the pull), fangs ready (7), settle (8)
    reel = [
        widow(arm=(120, -170), mirror="glow", veil="glow", lean=-1),
        widow(arm=(130, -175), mirror="glow", veil="glow", lean=-2, extra=[U.sparkle(4, -32)]),
        widow(arm=(0, -10), mirror="glow", veil="glow", lean=2, hat="bent"),
        widow(arm=(-5, -10), mirror="glow", veil="glow", lean=3, hat="bent", extra=[thread_px(15, -24, 26, -22, 0)]),
        widow(arm=(-5, -10), mirror="face", lean=3, hat="bent", extra=[thread_px(15, -24, 26, -22, 1)]),
        widow(arm=(10, -20), mirror="face", lean=2, extra=[thread_px(15, -24, 24, -21, 2)]),
        widow(arm=(140, -150), mirror="edge", lean=-3, rear=0.5, veil="glow", extra=[thread_px(9, -28, 22, -22, 0)]),
        widow(arm=(100, -120), mirror="edge", rear=1.0, veil="glow"),
        widow(arm=(45, -40)),
    ]
    dead = widow(sink=1.0, legs=1.0, arm=(150, 170), mirror="down", back_arm=(170, 175), hat="tip", rear=-0.6, dy=2)
    death = [
        widow(rear=0.8, arm=(-120, -60), mirror="edge", hat="tip", lean=-2),
        widow(sink=0.4, arm=(110, 150), mirror="down", hat="bent", legs=0.6),
        U.dissolve(widow(sink=0.8, arm=(150, 170), mirror="down", hat="tip", legs=0.9, dy=1), 0.15, seed=2, rise=2),
        dead,
    ]
    knock = widow(rear=0.7, dx=-2, arm=(-140, -100), mirror="edge", hat="tip", lean=-2)
    anims = anims_std("UmbGlassWidow", idle, run, death, dead, knock,
                      [("Fang", fang, [0.12, 0.14, 0.05, 0.06, 0.1, 0.1, 0.12]),
                       ("Reel", reel, [0.12, 0.14, 0.06, 0.06, 0.12, 0.12, 0.08, 0.1, 0.14])], idle_d=(0.2, 0.16, 0.2, 0.16),
                      run_d=0.07)
    return U.build_sheet("UmbGlassWidow", anims, outdir)


EVENTS["UmbGlassWidow"] = {"Fang": [("fangs stab: hit (FxUmbWidowFang at (17, -6))", 3)],
                           "Reel": [("release (FxUmbThread from the mirror, (15, -24))", 3), ("yank (pull the caught hero)", 6),
                                    ("fangs (bite if he is close)", 7)]}


# ================================================================================================
# THE UNDERTOW (T3, Gloamcoil): the Gloamcoil's ink pools have deepened into one it never leaves. A great
# indigo serpent arches out of a pool of black ink in three humps, gold scutes and teal eyes, its hood carrying
# the mirror-eye; the Lurker's slate legs paddle at the pool's edge. Attack Venom Bite: a rearing bite that
# poisons. Special Undertow: it sinks into its pool, slides unseen beneath the floor and erupts under the hero.
# ================================================================================================
def ink_pool_px(cx, w=20, h=3.4, k=0, ripple=0):
    px = {}
    for (x, y) in ell(cx, -1.5, w, h):
        d = ((x - cx) / w) ** 2 + ((y + 1.5) / h) ** 2
        px[(x, y)] = "iq" if d < 0.5 else ("n" if d < 0.8 else "N")
        if d < 0.5 and (x * 3 + y + k) % 7 == 0: px[(x, y)] = "gn"
        if 0.5 <= d < 0.8 and (x + k) % 4 == 0: px[(x, y)] = "lc" if (x + k) % 8 == 0 else "N"
    if ripple:
        for t in range(0, 360, 12):
            a = math.radians(t + k * 20)
            rr = 0.55 + 0.15 * ripple
            px[(int(round(cx + w * rr * math.cos(a))), int(round(-1.5 + h * rr * math.sin(a))))] = "N" if t % 36 else "lc"
    return U.ground(Spr(px)).px


def undertow(phase=0.0, rear=1.0, strike=0.0, dx=0, mouth="shut", sink=0.0, hood=1.0, eye="open", glint=0,
             extra=(), venom=False, pool=True, ripple=0, wisp=0):
    """sink: 0 = arched out of the pool, 1 = gone under."""
    c = C()
    if pool:
        put_px(c, ink_pool_px(dx - 2, 18, 3.0, int(phase * 3), ripple))
    if sink < 0.98:
        hump_h = 8 * (1 - sink)
        # three humps of body arching out of the ink (back to front)
        for j, (x0, w, hh) in enumerate(((-17, 6, 0.55), (-8, 7, 0.8))):
            pts = []
            for i in range(13):
                t = i / 12.0
                x = dx + x0 + w * 2 * t
                y = -1 - (hump_h * hh) * math.sin(math.pi * t) - 0.6 * math.sin(phase + t * 3 + j)
                pts.append((x, y))
            U.put_outlined(c, U.serpent_body(pts, [1.6 + 1.5 * math.sin(math.pi * t) for t in [i / 12.0 for i in range(13)]], seed=j + 4))
        # the neck rising from the pool at the front
        base = (dx + 5, -1.0)
        hy = -1 - (20 * rear) * (1 - sink)
        head = (dx + 9 + strike, hy)
        ctrl = (dx + 1 - 2 * strike * 0.2, (base[1] + hy) * 0.6)
        neck = [U.bez(base, ctrl, head, k / 12.0) for k in range(13)]
        nr = [3.8 - 1.4 * (k / 12.0) for k in range(13)]
        if hood > 0 and sink < 0.5:
            hc = neck[8]
            hp = U.rot_ellipse(hc[0] - 3.4 * hood, hc[1] + 1, 6.6 * hood, 4.4 * hood, -70)
            hp = {kk: "n" for kk in hp}
            for (x, y) in list(hp):
                if (x, y - 1) not in hp or (x - 1, y) not in hp: hp[(x, y)] = "N"
                elif (x + 1, y) not in hp or (x, y + 1) not in hp: hp[(x, y)] = "q"
                elif (x + y) % 3 == 0: hp[(x, y)] = "q"
            ex, ey = int(round(hc[0] - 4.2 * hood)), int(round(hc[1] + 0.6))
            for (ox, oy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
                hp[(ex + ox, ey + oy)] = "U" if (ox + oy + glint) % 3 else "u"
            hp[(ex, ey)] = "c" if eye == "open" else "n"
            put_px(c, hp)
        U.put_outlined(c, U.serpent_body(neck, nr, seed=1))
        hx, hy_ = int(round(head[0])), int(round(head[1]))
        c.part(UT_HEAD[mouth], hx, hy_)
        if venom:
            for (ox, oy, col) in ((4, 3, "vG"), (4, 4, "vg"), (5, 5, "vg"), (3, 6, "vG")):
                c.put(hx + ox, hy_ + oy, col)
        # the Lurker's slate legs paddling at the pool's rim
        for j, x0 in enumerate((-19, -13, 12)):
            sw = math.sin(phase * 2 + j * 1.9)
            kx, ky = dx + x0 + sw, -5 - 1.5 * (1 - sink)
            line(c, (dx + x0 - 1, -2), (kx, ky), "ln"); line(c, (kx, ky), (kx + 2 + sw, -1), "ln")
            c.put(int(round(kx)), int(round(ky)), "lN")
    # ink wisps over the pool
    for i in range(5):
        if (i + wisp) % 3 == 0: continue
        c.put(dx - 14 + i * 6 + (wisp % 2), -3 - (i + wisp) % 2, "m", over=False)
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return U.ground(s)


UT_HEAD = {
    "shut": Part("""
..nnn...
.nqqqcU.
nqqqqqqU
qqqqqqU.
.qqUuU..
""", (1, 4)),
    "open": Part("""
..nnn...
.nqqqcU.
nqqqqq.u
qqqp....
qqqp..u.
.qqUuU..
""", (1, 4)),
    "wide": Part("""
..nnnU..
.nqqqXc.
nqqqp..u
qqqpp...
qqqp....
qqqp..u.
.qqUuU..
""", (1, 4)),
    "hurt": Part("""
..nnn...
.nqqqU..
nqqqqqs.
qqqqqU..
.qqqq...
""", (1, 4)),
}


@sheet
def build_UmbUndertow(outdir):
    U.BELLY[0] = "gb"
    try:
        return _build_undertow(outdir)
    finally:
        U.BELLY[0] = "n"


def _build_undertow(outdir):
    idle = [undertow(phase=i * 0.5, rear=[1, 1.02, 1.0, 0.98][i], glint=i, wisp=i, mouth="shut" if i != 2 else "open")
            for i in range(4)]
    # it swims its pool along: humps roll, neck low and forward
    run = [undertow(phase=i * math.pi / 3, rear=0.8, strike=2, glint=i % 3, wisp=i, ripple=1) for i in range(6)]
    # Venom Bite: coil back (0-1), launch (2), BITE (3, venom), hold (4), withdraw (5-6)
    bite = [
        undertow(rear=1.05, strike=-3, mouth="open", phase=0.3, glint=1),
        undertow(rear=1.1, strike=-5, mouth="wide", phase=0.6, glint=2, venom=True, extra=[U.sparkle(0, -24)]),
        undertow(rear=0.8, strike=6, mouth="wide", phase=1.0, venom=True),
        undertow(rear=0.55, strike=12, mouth="wide", phase=1.3, venom=True,
                 extra=[U.slash(22, -10, 6, -70, 60, thick=1, cols=("vG", "vg", "c", "u")), flash_px(25, -10, 1, ("X", "vG"))]),
        undertow(rear=0.6, strike=11, mouth="open", phase=1.5),
        undertow(rear=0.8, strike=4, mouth="shut", phase=1.8),
        undertow(rear=0.95, strike=0, mouth="shut", phase=2.1),
    ]
    # Undertow: rear high (0), plunge (1-2), gone under (3: unseen, the mark lands at the hero), the pool slides
    # (4-5: travel), ERUPT beneath the hero (6: hit), sway (7), settle (8)
    dive = [
        undertow(rear=1.15, strike=-2, mouth="open", glint=1),
        undertow(rear=0.6, strike=4, sink=0.4, mouth="shut", phase=0.6, ripple=1),
        undertow(rear=0.3, strike=6, sink=0.8, mouth="shut", phase=1.2, ripple=2),
        undertow(sink=1.0, phase=1.8, ripple=3),
        undertow(sink=1.0, phase=2.4, ripple=2, pool=True),
        undertow(sink=1.0, phase=3.0, ripple=3),
        undertow(rear=1.25, strike=1, mouth="wide", phase=3.4, extra=[flash_px(9, -26, 2), ink_splash(0)]),
        undertow(rear=1.1, strike=0, mouth="open", phase=3.8, extra=[ink_splash(1)]),
        undertow(rear=1.0, phase=4.2),
    ]
    dead = undertow(rear=0.25, sink=0.75, mouth="hurt", eye="shut", phase=0.8, hood=0)
    death = [
        undertow(rear=1.15, strike=-4, mouth="hurt", eye="shut", hood=1.2),
        undertow(rear=0.6, strike=-1, mouth="hurt", eye="shut", phase=1.0, sink=0.3),
        U.dissolve(undertow(rear=0.35, sink=0.6, mouth="hurt", eye="shut", phase=1.6, hood=0), 0.25, seed=3, rise=2,
                   smoke="mns"),
        dead,
    ]
    knock = undertow(rear=1.0, strike=-5, mouth="hurt", eye="shut", dx=-2)
    anims = anims_std("UmbUndertow", idle, run, death, dead, knock,
                      [("Venom", bite, [0.12, 0.16, 0.05, 0.06, 0.1, 0.1, 0.12]),
                       ("Dive", dive, [0.1, 0.08, 0.08, 0.18, 0.18, 0.18, 0.06, 0.12, 0.14])], idle_d=(0.18, 0.15, 0.18, 0.15),
                      run_d=0.08)
    return U.build_sheet("UmbUndertow", anims, outdir)


def ink_splash(k):
    px = {}
    rnd = random.Random(70 + k)
    for i in range(12 - 4 * k):
        x = rnd.uniform(-6, 14); y = -rnd.uniform(2, 14 - 4 * k)
        px[(int(x), int(y))] = ("iq", "n", "N", "lc")[i % 4]
    return px


EVENTS["UmbUndertow"] = {"Venom": [("bite lands (FxUmbVenomBite at (20, -10))", 3)],
                         "Dive": [("sinks: unseen, FxUmbRipple mark under the hero", 3), ("moves under the hero", 5),
                                  ("erupts: FxUmbErupt hit", 6)]}


# ================================================================================================
# EFFECT SHEETS (palette art; origin = the effect's spawn point, y down). The C# side draws each with
# Strike.ArtAt(go, sheet, ox, oy) using the origin printed here / in TIMING.md; projectiles are centred.
# ================================================================================================
FX10 = {}       # name -> (cellW, cellH, ox, oy, [(anim, n, durations)], note)


def fx_pack(name, anims, outdir, note, centred=False, scale=8):
    allp = [k for a in anims for f in a[1] for k in f.px] + [(0, 0)]
    for an, fr, du in anims:
        assert len(fr) == len(du), (name, an)
    if centred:
        hw = max(max(abs(p[0]) for p in allp) + 1, 2); hh = max(max(abs(p[1]) for p in allp) + 1, 2)
        ox, oy, cw, ch = hw, hh, 2 * hw + 1, 2 * hh + 1
    else:
        x0 = min(p[0] for p in allp) - 1; x1 = max(p[0] for p in allp) + 1
        y0 = min(p[1] for p in allp) - 1; y1 = max(p[1] for p in allp) + 1
        ox, oy, cw, ch = -x0, -y0, x1 - x0 + 1, y1 - y0 + 1
    img, man = pack(name, anims, cw, ch, (ox, oy), outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    U.FX_ANCHORS[name] = (ox, oy)
    FX10[name] = (cw, ch, ox, oy, [(a, len(f), list(d)) for a, f, d in anims], note)
    print("built %-18s cell %dx%d origin (%d, %d)  %s" % (name, cw, ch, ox, oy, ", ".join("%s:%d" % (a[0], len(a[1])) for a in anims)))


def S(px):
    return Spr({(int(round(x)), int(round(y))): c for (x, y), c in px.items()})


def outline_dark(px, col="K"):
    out = dict(px)
    for (x, y) in px:
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + d[0], y + d[1])
            if k not in px: out.setdefault(k, col)
    return out


def ring_px(cx, cy, rx, ry, cols, step=8, gap_k=None, k=0):
    px = {}
    for t in range(0, 360, step):
        if gap_k is not None and (t // step + k) % gap_k == 0: continue
        a = math.radians(t)
        px[(int(round(cx + rx * math.cos(a))), int(round(cy + ry * math.sin(a))))] = cols[(t // step + k) % len(cols)]
    return px


# ---- projectiles (face right, centred) ----
def fx_moth_scale(k):
    px = {(0, 0): "wc", (1, 0): "X" if k % 2 == 0 else "wc", (-1, 0): "wB", (0, -1): "wB", (0, 1): "wb", (2, 0): "wB",
          (-2, 0): "wb", (1, -1): "wc" if k == 1 else "wB", (1, 1): "wb"}
    for t in range(1, 4):
        if (t + k) % 2: px[(-2 - t, ((t + k) % 3) - 1)] = ("wB", "wb", "wv")[t - 1]
    return outline_dark(px, "wv")


def fx_argus_scale(k):
    px = {}
    for (x, y) in ell(0, 0, 3.2, 2.0):
        px[(x, y)] = "aN" if y < 0 else "an"
    px.update({(0, 0): "K", (1, 0): "u", (-1, 0): "u", (0, -1): "u", (0, 1): "aU", (2, 0): "X" if k % 2 else "aU"})
    px[(-1 + (k % 3) - 1, -1)] = "c"
    for t in range(1, 4):
        if (t + k) % 2: px[(-3 - t, ((t + k) % 3) - 1)] = ("aU", "aN", "an")[t - 1]
    return outline_dark(px, "q")


def fx_sand_shard(k):
    px = {(2, 0): "X", (1, 0): "hS", (0, 0): "hS", (-1, 0): "hs", (0, -1): "hS", (0, 1): "hs", (-2, 0): "N"}
    rnd = random.Random(k + 5)
    for t in range(4):
        px.setdefault((-3 - t - (k % 2), rnd.randint(-1, 1)), ("hs", "hS", "N", "n")[t])
    return outline_dark(px, "q")


def fx_sand_ball(k):
    px = {}
    for (x, y) in ell(0, 0, 2.6, 2.6):
        px[(x, y)] = "hS" if x + y < -1 else ("hs" if (x + y + k) % 3 else "N")
    px[(-1, -1)] = "X"; px[(2, -1 + k % 2)] = "hW"
    rnd = random.Random(k + 9)
    for t in range(5):
        px.setdefault((-4 - t, rnd.randint(-2, 2)), ("hS", "hs", "N", "hs", "n")[t])
    return outline_dark(px, "q")


def fx_thread(k):
    px = {}
    for x in range(-9, 4):
        px[(x, 0)] = "c" if (x + k) % 4 == 0 else "u"
    px.update({(4, 0): "X", (3, -1): "c", (3, 1): "c", (5, 0): "c", (-10, 0): "U", (-11, 1 if k % 2 else -1): "U"})
    return px


def fx_quill(k):
    ang = [0, 45, 90, 135][k]
    px = U.nail_px(0, 0, ang, 3, tip="c", mid="U", base="S")
    px.update(U.nail_px(0, 0, ang + 180, 2, tip="pq", mid="pn", base="S"))
    px[(0, 0)] = "pN"
    return outline_dark(px, "K")


def fx_swarm_moth(k):
    px = tiny_moth(0, 0, k)
    px = {kk: v for kk, v in px.items()}
    for t in range(1, 4):
        if (t + k) % 2: px[(-2 - t, (t + k) % 2)] = ("c", "wB", "u")[t - 1]
    return px


def fx_moth_burst(k):
    rnd = random.Random(40 + k)
    px = {}
    r = [2, 4, 6, 7, 8][k]
    for i in range([6, 12, 14, 10, 6][k]):
        a = rnd.uniform(0, 360); d = rnd.uniform(0, r)
        px[(int(round(d * math.cos(math.radians(a)))), int(round(d * 0.8 * math.sin(math.radians(a)))))] = \
            ("X", "c", "wB", "u", "wb")[(i + k) % 5] if k < 4 else ("wb", "wv")[i % 2]
    if k < 2: px.update(flash_px(0, 0, 1 + k))
    return px


# ---- clouds, rings, ground marks (origin = floor point / centre) ----
def fx_glitter(k):
    """Glassmoth Glitter Dust: 12 frames, spread 0-2, shimmer 3-8, fade 9-11 (centre = origin, ~24 x 16)."""
    r = [4, 7, 9][k] if k < 3 else 10
    n = [10, 18, 24][k] if k < 3 else (26 if k < 9 else [16, 9, 4][k - 9])
    rnd = random.Random(300 + (k if k < 3 or k > 8 else 3 + (k - 3) % 2))
    px = {}
    for i in range(n):
        a = rnd.uniform(0, 360); d = r * math.sqrt(rnd.uniform(0, 1))
        x, y = d * math.cos(math.radians(a)), d * 0.7 * math.sin(math.radians(a))
        if 3 <= k <= 8:
            x += math.sin(k * 0.9 + i) * 0.8
        col = ("X", "c", "wB", "u", "wb", "N")[(i + k) % 6]
        if k >= 9: col = ("wB", "wb", "N")[i % 3]
        px[(int(round(x)), int(round(y)))] = col
    return px


def fx_rewind_mark(k):
    """Hourglass Rewind mark: a ring of sand on the floor around a ghost hourglass glyph (loops)."""
    px = ring_px(0, -1, 8, 3, ("hS", "hs", "N", "hs"), step=12, k=k)
    gy = -6 - (k % 2)
    for (x, y, c) in ((-2, 0, "he"), (-1, 0, "he"), (0, 0, "he"), (1, 0, "he"), (2, 0, "he"), (-1, 1, "hs"), (0, 1, "hS"),
                      (1, 1, "hs"), (0, 2, "hS" if k % 2 else "X"), (-1, 3, "hs"), (0, 3, "hs"), (1, 3, "hS"),
                      (-2, 4, "he"), (-1, 4, "he"), (0, 4, "he"), (1, 4, "he"), (2, 4, "he")):
        px[(x, gy + y - 4)] = c
    for i in range(3):
        px[((i * 5 + k * 2) % 13 - 6, -2 - (k + i) % 4)] = "hS"
    return px


def fx_rewind_snap(k):
    px = {}
    h = [18, 22, 14, 8, 4][k]
    for y in range(-h, 0):
        px[(0, y)] = "X" if k < 2 else "hS"
        if k < 3: px[(-1, y)] = "hS"; px[(1, y)] = "hs"
    px.update(ring_px(0, -1, [3, 6, 9, 11, 12][k], [1.5, 2.5, 3.5, 4, 4][k], ("hS", "X", "hs") if k < 3 else ("hs", "N"),
                      step=15, gap_k=None if k < 3 else 3, k=k))
    if k < 2: px.update(flash_px(0, -h // 2, 2))
    return px


def fx_gaze(k):
    """Argus Moth gaze landing on the hero: an eye opens over his head and flares (origin = hero feet)."""
    px = {}
    cy = -24
    lid = [1.0, 0.6, 0.0, 0.0, 0.0, 0.6][k]
    for (x, y) in ell(0, cy, 4.5, 2.6):
        d = math.hypot(x / 4.5, (y - cy) / 2.6)
        if abs(y - cy) > 2.6 * (1 - lid) + 0.3:
            continue
        px[(x, y)] = "aU" if d > 0.8 else ("u" if d > 0.5 else "K")
    px[(-4, cy)] = "aN"; px[(4, cy)] = "aN"; px[(-5, cy)] = "an"; px[(5, cy)] = "an"
    if lid < 0.5: px[(-1, cy - 1)] = "X"
    if k in (3, 4):
        for a in range(0, 360, 45):
            for r in range(6, 6 + (3 if k == 3 else 5)):
                if k == 4 and r < 8: continue
                px[(int(round(r * math.cos(math.radians(a)))), int(round(cy + r * 0.7 * math.sin(math.radians(a)))))] = "aU" if r % 2 else "c"
    if k == 3:
        for y in range(cy + 4, -4, 2): px[(0, y)] = "aN"
    return px


def fx_toll(k):
    """Pendulum Toll: a bronze ring of sound rolling out along the floor (origin = the clock's feet)."""
    r = [6, 11, 16, 20, 23, 25][k]
    px = ring_px(0, -1, r, r * 0.42, ("hW", "hw", "hS") if k < 3 else ("hw", "hs", "he"), step=6, gap_k=None if k < 2 else 4 - (k > 3), k=k)
    if k < 4:
        px.update(ring_px(0, -1, r - 3, (r - 3) * 0.42, ("hs", "N") if k else ("X",), step=10, gap_k=3, k=k))
    if k < 2:
        for x in range(-3, 4): px[(x, -1)] = "hW" if k == 0 else "hw"
    return px


def fx_sandfall(k):
    """Sand Wraith Sandfall mark: 0-5 telegraph (a ring of sand + a trickle from above), 6 the column slams
    down (hit), 7-9 the pile spreads and fades. Origin = the floor point."""
    px = {}
    if k <= 5:
        px.update(ring_px(0, -1, 4 + k * 0.6, 1.8 + k * 0.25, ("hS", "hs", "N"), step=20 - k * 2, k=k))
        for i in range(2 + k * 2):
            y = -34 + ((i * 7 + k * 5) % (8 + k * 5))
            px[((i % 3) - 1, y)] = "hS" if i % 2 else "hs"
    elif k == 6:
        for y in range(-30, 0):
            w = 1 if y < -10 else 2
            for x in range(-w, w + 1): px[(x, y)] = "hS" if x <= 0 else "hs"
        px.update(ring_px(0, -1, 7, 2.5, ("X", "hS"), step=15))
        px.update(flash_px(0, -3, 2, ("X", "hW", "hS")))
    else:
        j = k - 7
        for x in range(-6 - j, 7 + j):
            h = int(round((3 - j) - abs(x) * 0.4))
            for y in range(0, max(0, h)):
                px[(x, -1 - y)] = "hS" if y == h - 1 else ("hs" if (x + y) % 3 else "N")
        rnd = random.Random(k)
        for i in range(6 - 2 * j):
            px[(rnd.randint(-9, 9), -rnd.randint(2, 7))] = "hS"
    return px


def fx_caltrop(k):
    """Bristleback caltrops: three glass nails stuck in the floor. Land 0-2, glint idle 3-10, fade 11-13."""
    px = {}
    nails = ((-4, 0, -110), (1, -1, -75), (5, 1, -95))
    for i, (x, y, a) in enumerate(nails):
        if k < 3 and i > k: continue
        if k >= 11 and i < k - 11: continue
        ln = 3 if k != 0 else 4
        px.update(U.nail_px(x, y - 1, a, ln, tip="c" if (k + i) % 4 else "X", mid="U", base="pN"))
        px[(x - 1, y)] = "pq"; px[(x + 1, y)] = "pm"
    if k in (0, 1):
        px.update(flash_px(nails[k][0], nails[k][1] - 1, 1, ("X", "pc")))
    return outline_dark(px, "K") if k < 11 else px


def fx_bristle(k):
    """Bristle aura on the Bristleback (loops, origin = feet): glints dance along the raised nail tips."""
    px = {}
    for i in range(7):
        a = math.radians(200 + i * 23)
        x = int(round(11 * math.cos(a))); y = int(round(-14 + 9 * math.sin(a)))
        if (i + k) % 3 == 0: px.update(flash_px(x, y, 1, ("X", "pc")))
        elif (i + k) % 3 == 1: px[(x, y)] = "pc"
    return px


def fx_thorn(k):
    """Thorns striking back at the hero: three glass nails stab up out of the floor at his feet."""
    px = {}
    h = [3, 7, 6, 3][k]
    for i, (x, a) in enumerate(((-3, -100), (0, -88), (3, -78))):
        px.update(U.nail_px(x, -1, a, max(1, h - (i % 2)), tip="X" if k == 1 else "c", mid="U", base="pN"))
    if k == 1: px.update(flash_px(0, -h - 1, 2, ("X", "pc", "pN")))
    if k >= 2:
        for x in (-5, 5): px[(x, -2 - k)] = "pc"
    return px


def fx_reeled(k):
    """Glass Widow Reel: the glass thread wound twice round the caught hero (origin = his feet)."""
    px = {}
    for j, yy in enumerate((-10, -6)):
        for t in range(0, 360, 20):
            a = math.radians(t + k * 30 + j * 90)
            x, y = int(round(5.5 * math.cos(a))), int(round(yy + 1.4 * math.sin(a)))
            if math.sin(a) < -0.3 and (t // 20) % 2: continue          # the far side shows through in dashes
            px[(x, y)] = "c" if (t // 20 + k) % 4 == 0 else "u"
    # the taut line back toward the widow
    for i in range(6):
        if (i + k) % 2 == 0: px[(6 + i, -8 - i // 3)] = "u" if i % 3 else "c"
    return px


def fx_ripple(k):
    """Undertow mark under the hero: ink rings welling up with teal glints (telegraph, origin = floor)."""
    px = {}
    for j in range(3):
        r = (k * 1.5 + j * 4) % 12 + 2
        px.update(ring_px(0, -1, r, r * 0.4, ("iq", "n", "lc") if j == 0 else ("n", "iq"), step=14, gap_k=3, k=k + j))
    for (x, y) in ell(0, -1, 2 + k * 0.6, 1 + k * 0.25):
        px[(x, y)] = "iq"
    return px


def fx_erupt(k):
    """Undertow eruption: a geyser of ink bursts from the floor (hit on frames 1-2, origin = floor)."""
    px = {}
    h = [8, 22, 20, 12, 6, 2][k]
    w = [3, 4, 4, 5, 6, 7][k]
    for y in range(-h, 0):
        ww = max(1, int(round(w * (0.5 + 0.5 * (y + h) / max(1, h)))))
        for x in range(-ww, ww + 1):
            px[(x, y)] = "n" if x < 0 else ("iq" if x > 0 else "N")
    rnd = random.Random(k + 21)
    for i in range([3, 10, 12, 10, 6, 3][k]):
        a = rnd.uniform(200, 340); d = rnd.uniform(4, 6 + k * 3)
        px[(int(round(d * math.cos(math.radians(a)))), int(round(-h * 0.6 + d * math.sin(math.radians(a)))))] = ("lc", "N", "n", "iq")[i % 4]
    px.update(ring_px(0, -1, 4 + k * 2, 1.5 + k * 0.6, ("iq", "n"), step=18))
    if k == 1: px.update(flash_px(0, -h, 2, ("X", "lc", "N")))
    return px


def fx_after_dash(k):
    """The Sundered's afterimage running the dash again: its pale twin in the lunge, see-through, peeling into
    streaks (origin = its feet). Hit on frame 0."""
    c = C()
    duelist(c, (0, -13), pale=True, lean=55, legs=((175, 150), (10, 60)), arms=((170, 170), (0, 10)),
            sabres=(175, 5), head="glare", scarf=2)
    spr = U.translucent(c.spr(), phase=k, keep=0.7 - 0.1 * k)
    if k: spr = U.dissolve(spr, 0.18 * k, seed=7 + k, rise=0, smoke=("tn", "tq"))
    px = shift_px(spr.px, -2 * k, 0)
    for j, yy in enumerate((-20, -14, -8, -3)):
        for i in range(3 + 2 * k):
            if (i + j + k) % 3: px.setdefault((-9 - i - 2 * k, yy), "tN" if i < 2 else "tn")
    return px


def hsh2(x, y, s):
    return U.hsh(int(x), int(y), s)


# ---- melee arcs (origin = the vanilla swipe's origin; OrcSwipe arc centre (9, 0), OrcSwipe2 centre (6, 0)) ----
def fx_swarm_bite(k):
    """Glitterswarm surge: a crescent of tiny moths and glitter sweeping top -> bottom (OrcSwipe footprint)."""
    px = {}
    sweep = [0, 20, 35, 45][k]
    for i in range(14):
        t = i / 13.0
        a = math.radians(-70 + 140 * t + sweep * (1 - t))
        r = 10 + (i % 3)
        x, y = 9 + r * math.cos(a), r * math.sin(a)
        if k == 3 and i % 2: continue
        if i % 4 == 0 and k < 3: px.update(tiny_moth(x, y, i + k))
        else: px[(int(round(x)), int(round(y)))] = ("X", "c", "wB", "u")[(i + k) % 4] if k < 3 else "wb"
    if k == 0: px.update(flash_px(19, 0, 1))
    return px


def fx_pendulum_arc(k):
    """Pendulum Swing: the glass crescent sweeping from under-behind to up-front (origin = the pivot)."""
    px = {}
    a0, a1 = 140, [70, 30, 10, 0][k]
    lead = [80, 35, 15, 5][k]
    for i in range(30):
        t = i / 29.0
        a = a0 + (a1 - a0) * t
        if k >= 2 and t < 0.4 + 0.2 * (k - 2): continue
        for j, rr in enumerate((17, 16, 15)):
            x, y = rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))
            col = ("c", "B", "b")[j] if t > 0.7 else (("u", "b", "wv")[j] if t > 0.35 else ("hS", "wv", "")[j])
            if col: px[(int(round(x)), int(round(y)))] = col if k < 3 else ("b", "wv", "wv")[j]
    lx, ly = 16 * math.cos(math.radians(lead)), 16 * math.sin(math.radians(lead))
    if k < 2: px.update(flash_px(int(round(lx)), int(round(ly)), 2 - k))
    return px


def fx_scissor(k):
    """The Sundered's Cross Cut: two sabre cuts scissoring shut, a pale one and a violet one (OrcSwipe2 origin)."""
    px = {}
    close = [10, 5, 1, 0][k]
    for s, ramp in ((1, ("tN", "tn", "tq")), (-1, ("uN", "un", "uq"))):
        for i in range(-9, 10):
            x = 9 + i * 0.9
            y = s * (i * 0.85 + close * 0.6 * (1 if i > 0 else -1) * 0) + s * close * 0.4 - s * i * 0.85 * (k / 3.0) * 0
            y = s * (i * 0.95) * (0.3 + 0.7 * close / 10.0) + (0 if k < 3 else s * i * 0.2)
            if k >= 2 and abs(i) > 9 - 3 * (k - 1): continue
            c = ramp[0] if abs(i) < 4 else ramp[1] if abs(i) < 7 else ramp[2]
            px[(int(round(x)), int(round(y)))] = c
            if k < 2: px.setdefault((int(round(x)), int(round(y)) + s), ramp[2])
    if k <= 1: px.update(flash_px(9, 0, 2 - k, ("X", "c", "u")))
    return px


def fx_widow_fang(k):
    """Glass Widow Glass Fang: the two front legs stab down in bright glass streaks (OrcSwipe2 origin)."""
    px = {}
    for j, x0 in enumerate((5, 10)):
        top = [-12, -8, -4, -2][k]
        bot = [-2, 6, 8, 8][k]
        for y in range(top, bot):
            if k >= 2 and y < bot - 4 - (3 - k): continue
            px[(x0 + (y + 12) // 6, y)] = "c" if y > bot - 3 else ("lU" if k < 2 else "lN")
            px.setdefault((x0 + (y + 12) // 6 + 1, y), "lN" if k < 2 else "ln")
        if k == 1: px.update(flash_px(x0 + 3, bot, 1, ("X", "c")))
    if k == 2:
        for (x, y) in ((4, 9), (8, 10), (13, 9), (16, 8)): px[(x, y)] = "lc"
    return px


def fx_venom_bite(k):
    """Undertow Venom Bite: two fang arcs snapping shut with green venom spray (OrcSwipe footprint)."""
    px = {}
    sweep = [0, 18, 28, 34][k]
    for s in (-1, 1):
        for i in range(12):
            t = i / 11.0
            a = math.radians(s * (70 - 60 * t) + s * -sweep * 0.3)
            r = 9
            x, y = 7 + r * math.cos(a) * 0.8, r * math.sin(a)
            if k == 3 and i < 8: continue
            px[(int(round(x)), int(round(y)))] = ("u", "c", "X")[min(2, i // 4)] if k < 2 else ("vg", "vG")[i % 2]
    rnd = random.Random(k + 70)
    for i in range([2, 8, 10, 6][k]):
        px[(int(rnd.uniform(10, 20)), int(rnd.uniform(-6, 8)))] = ("vG", "vg")[i % 2]
    if k == 1: px.update(flash_px(14, 0, 1, ("X", "vG")))
    return px


@sheet
def build_FX10(outdir):
    rng = range
    fx_pack("FxUmbMothScale", [("Fly", [S(fx_moth_scale(k)) for k in rng(4)], [0.05] * 4)], outdir,
            "Glassmoth Scales projectile (faces right, centred).", centred=True)
    fx_pack("FxUmbGlitter", [("Life", [S(fx_glitter(k)) for k in rng(12)], [0.08] * 3 + [0.3] * 6 + [0.12] * 3)], outdir,
            "Glassmoth Glitter Dust cloud, centre = origin; drifts after release, slows on touch. 2.4 s.")
    fx_pack("FxUmbSandShard", [("Fly", [S(fx_sand_shard(k)) for k in rng(4)], [0.05] * 4)], outdir,
            "Hourglass Sand Shard projectile (centred).", centred=True)
    fx_pack("FxUmbRewind", [("Mark", [S(fx_rewind_mark(k)) for k in rng(4)], [0.12] * 4),
                            ("Snap", [S(fx_rewind_snap(k)) for k in rng(5)], [0.05, 0.06, 0.07, 0.08, 0.1])], outdir,
            "Hourglass Rewind: Mark loops on the floor at the marked spot until the snap; Snap plays where it returns. "
            "Origin = floor point.")
    fx_pack("FxUmbArgusScale", [("Fly", [S(fx_argus_scale(k)) for k in rng(4)], [0.05] * 4)], outdir,
            "Argus Moth Scale Volley projectile (centred).", centred=True)
    fx_pack("FxUmbGaze", [("Play", [S(fx_gaze(k)) for k in rng(6)], [0.06, 0.06, 0.08, 0.06, 0.1, 0.12])], outdir,
            "Argus Moth Thousand Eyes: the eye opening over a hero who looked; origin = his feet. Daze on frame 3.")
    fx_pack("FxUmbSwarmMoth", [("Fly", [S(fx_swarm_moth(k)) for k in rng(4)], [0.06] * 4),
                               ("Burst", [S(fx_moth_burst(k)) for k in rng(5)], [0.04, 0.05, 0.06, 0.08, 0.1])], outdir,
            "Glitterswarm homing moth (Fly, centred) and its burst on contact (Burst).", centred=True)
    fx_pack("FxUmbSwarmBite", [("Play", [S(fx_swarm_bite(k)) for k in rng(4)], [0.117, 0.117, 0.117, 0.067])], outdir,
            "Glitterswarm Swarm Bite (OrcSwipe clone): moth crescent to x 21. Damage frame 0.")
    fx_pack("FxUmbPendulumArc", [("Play", [S(fx_pendulum_arc(k)) for k in rng(4)], [0.06, 0.08, 0.1, 0.1])], outdir,
            "Pendulum Swing: the blade's crescent round the pivot (origin = the pivot, 19 px above the feet). Damage frame 0.")
    fx_pack("FxUmbToll", [("Play", [S(fx_toll(k)) for k in rng(6)], [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])], outdir,
            "Pendulum Toll: ground ring of sound, origin = the clock's feet; damage + big knockback on frames 1-2.")
    fx_pack("FxUmbSandBall", [("Fly", [S(fx_sand_ball(k)) for k in rng(4)], [0.05] * 4)], outdir,
            "Sand Wraith Sand Bolt projectile (centred).", centred=True)
    fx_pack("FxUmbSandfall", [("Play", [S(fx_sandfall(k)) for k in rng(10)],
                               [0.12, 0.12, 0.12, 0.12, 0.12, 0.1, 0.06, 0.1, 0.12, 0.14])], outdir,
            "Sand Wraith Sandfall: telegraph 0-5 (0.70 s), the column lands on 6 (hit, floor 16 x 8), spreads 7-9.")
    fx_pack("FxUmbScissor", [("Play", [S(fx_scissor(k)) for k in rng(4)], [0.117, 0.117, 0.117, 0.067])], outdir,
            "Sundered Cross Cut (OrcSwipe2 clone): two cuts scissoring shut at (9, 0). Damage frame 0.")
    fx_pack("FxUmbAfterDash", [("Play", [S(fx_after_dash(k)) for k in rng(5)], [0.05, 0.06, 0.07, 0.08, 0.1])], outdir,
            "Sundered Afterimage: the pale twin re-running the dash; spawned along the path, origin = feet. Hit frame 0.")
    fx_pack("FxUmbQuill", [("Fly", [S(fx_quill(k)) for k in rng(4)], [0.05] * 4)], outdir,
            "Bristleback Nail Lob quill, spinning (centred).", centred=True)
    fx_pack("FxUmbCaltrop", [("Life", [S(fx_caltrop(k)) for k in rng(14)], [0.05, 0.05, 0.06] + [0.42] * 8 + [0.12] * 3)],
            outdir, "Bristleback caltrops on the floor: land 0-2, live 3-10, fade 11-13 (3.9 s); origin = floor.")
    fx_pack("FxUmbBristle", [("Loop", [S(fx_bristle(k)) for k in rng(4)], [0.09] * 4)], outdir,
            "Bristleback Bristle indicator, loops on the monster while thorns are up; origin = its feet.")
    fx_pack("FxUmbThorn", [("Play", [S(fx_thorn(k)) for k in rng(4)], [0.04, 0.06, 0.08, 0.1])], outdir,
            "Bristleback thorns striking the hero who hit it; origin = the hero's feet.")
    fx_pack("FxUmbWidowFang", [("Play", [S(fx_widow_fang(k)) for k in rng(4)], [0.117, 0.117, 0.117, 0.067])], outdir,
            "Glass Widow Glass Fang (OrcSwipe2 clone): two stabbing leg streaks. Damage frame 0.")
    fx_pack("FxUmbThread", [("Fly", [S(fx_thread(k)) for k in rng(4)], [0.05] * 4)], outdir,
            "Glass Widow Reel thread projectile (centred, needle at the front).", centred=True)
    fx_pack("FxUmbReeled", [("Play", [S(fx_reeled(k)) for k in rng(6)], [0.07] * 6)], outdir,
            "Glass Widow: the thread wrapped round a caught hero while she reels; origin = his feet.")
    fx_pack("FxUmbVenomBite", [("Play", [S(fx_venom_bite(k)) for k in rng(4)], [0.117, 0.117, 0.117, 0.067])], outdir,
            "Undertow Venom Bite (OrcSwipe clone): fangs + venom. Damage frame 0.")
    fx_pack("FxUmbRipple", [("Play", [S(fx_ripple(k)) for k in rng(8)], [0.07] * 8)], outdir,
            "Undertow telegraph under the hero (0.56 s = Dive frames 3-5), origin = floor.")
    fx_pack("FxUmbErupt", [("Play", [S(fx_erupt(k)) for k in rng(6)], [0.05, 0.06, 0.08, 0.1, 0.1, 0.12])], outdir,
            "Undertow eruption: ink geyser, origin = floor; damage frames 1-2.")
    return None


SHEET_ORDER = ["UmbGlassmoth", "UmbHourglass", "UmbArgusMoth", "UmbGlitterswarm", "UmbPendulum", "UmbSandWraith",
               "UmbSundered", "UmbBristleback", "UmbGlassWidow", "UmbUndertow"]

LINEAGE = [
    "Glimmer -> Glassmoth: the Glimmer's black-mirror kite and single eye are the moth's body; its two crystal wings grew "
    "into four leaded-glass panes; feathered antennae.",
    "Glimmer -> Hourglass: the black mirror blown into an hourglass of dark glass in a bronze frame, the eye in the upper "
    "bulb, violet shadow-sand, the Glimmer's crystal wings at the waist.",
    "Glassmoth -> Argus Moth: the same frontal moth, much bigger, wings gone dusk-violet with staring eyespots (each the "
    "Glimmer eye); the glass margin survives at the wingtips.",
    "Glassmoth -> Glitterswarm: the moth's mirror heart with stubby glass wings, ringed by a whirl of 15 tiny glass moths "
    "and glitter (its dust grown into a hive).",
    "Hourglass -> The Pendulum: the bronze frame is now a clock case, the mirror eye its hub, the crystal wings at its "
    "sides, a glass crescent pendulum with a sand vial.",
    "Hourglass -> Sand Wraith: the hourglass burst; a hooded wraith of its violet sand stands in the bent bronze cage "
    "with the single eye, pouring into a dune.",
    "Twinned -> The Sundered: the twins torn apart - the dark one with two sabres, the pale reflection a step behind, see-"
    "through, tied at the waist by a thread of shadow; the imp's white eye and smoky tail.",
    "Nailshade -> Bristleback: the Nailshade on all fours, plum-rose, its back a thicket of long glass nails, the same "
    "mirror-shard face and smoky tail.",
    "Mirror Witch -> Glass Widow: the witch (hat, veil, teal eyes, hand mirror) rising from a slate-blue spider body - "
    "the Lurker legs she hid under her hem - with a mirror-glass mark on its back.",
    "Gloamcoil -> The Undertow: the Gloamcoil's indigo, gold scutes, teal eyes and mirror-eyed hood, arched out of a pool "
    "of ink in three humps; its slate legs paddle at the rim.",
]


def timing_section():
    L = ["", "## v0.10 unique-evolution tree (tools/sprites/umbrael_v10.py)", "",
         "Tree: ShadeImp -> Twinned, Nailshade; Glimmer -> Glassmoth, Hourglass; GloomLurker -> MirrorWitch, Gloamcoil; "
         "Twinned -> HollowKing, Sundered; Nailshade -> GlassSeraph, Bristleback; MirrorWitch -> Unblinking, GlassWidow; "
         "Gloamcoil -> EclipseWyrm, Undertow; Glassmoth -> ArgusMoth, Glitterswarm; Hourglass -> Pendulum, SandWraith.",
         "All ten new sheets are drawn at final size (no ArtScale entry); the points in the move tables are their real "
         "pixels. Single-parent lineage:", ""]
    L += ["- " + t for t in LINEAGE]
    L += ["", "### v0.10 effect sheets", "", "| Sheet | Cell (w x h) | Origin | Anims (frames, total s) | Notes |",
          "|---|---|---|---|---|"]
    for name, (cw, ch, ox, oy, rows, note) in FX10.items():
        an = ", ".join("%s %d, %.2f s" % (a, n, sum(d)) for a, n, d in rows)
        L.append("| %s | %d x %d | (%d, %d) | %s | %s |" % (name, cw, ch, ox, oy, an, note))
    return L
