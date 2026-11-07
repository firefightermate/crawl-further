"""Item icons v2: 15 spells + 15 artifacts, drawn with the material renderer of jinx_v2_rigs.py.

    python3 tools/sprites/items_v2_icons.py [outdir]     -> art/out_icons_v2/Icon*.png|json (+ board.png)

Every icon is a 16x16 cell, anim `Idle` (2 frames: the icon and a small real change, a glint or a flicker), feet (8, 15).
Each icon is one function draw(g, ph) that works in cell units (0..16, y down, centre (8, 8)) through a Pen, so the same
drawing also renders bigger: item_icons.py asks for the artifacts at BUBBLE_SCALE for the shop and vault picture.

Shading follows the gods' rigs: three lit tones per material from one top-left light, no black ring, the bottom and
right edges in the material's own darkest tone, glows and flames emissive (never outlined).
"""
import colorsys, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from anim import SprRGB, pack  # noqa: E402
import jinx_v2_rigs as J  # noqa: E402
from jinx_v2_rigs import Rig, die3, line_px  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_OUT = os.path.join(ROOT, "art", "out_icons_v2")
FEET = (8, 15)
BUBBLE_SCALE = 1.375          # 22 px pictures in the 34 x 41 shop bubble
PARCH = (147, 124, 73)
SEP_DIFF = 70           # value difference below which an edge needs a rim to read on the card

# ------------------------------------------------------------------ extra materials (dark -> light, 5 tones)
_NEW = {
    "wax":    ["4a3628", "8c7458", "d4c098", "f0e6c8", "fffaea"],
    "dirt":   ["1a120e", "34261c", "523c2a", "6e543a", "8a6e4c"],
    "spore":  ["1c0c2a", "3a1a56", "5e2e88", "8650b2", "b07ed8"],
    "pink":   ["4a0e2e", "86205a", "c04a8a", "e884b6", "ffc8e0"],
    "root":   ["160e0a", "33221a", "553a26", "7a5634", "9c7a4c"],
    "leaf":   ["0e1e0e", "1c3a18", "325e28", "52903c", "8cc464"],
    "ice":    ["14243a", "2a4c74", "4a80b2", "8cc0e8", "e4f8ff"],
    "iron":   ["14121a", "2a2832", "45434e", "65636e", "8e8c96"],
    "bronze": ["2a1606", "5e3812", "9a6220", "d0983a", "f8dc8a"],
    "sea":    ["0a1c22", "103a42", "1a6266", "2e9696", "74d6c8"],
    "coal":   ["120a0a", "261412", "40221c", "5a3024", "764030"],
    "flesh2": ["3a1222", "6c283e", "a24a5e", "c87a84", "e8b0ae"],
    "seed":   ["2a0810", "5c1018", "981c22", "d03a30", "f8806a"],
    "shell":  ["201a16", "463a30", "766452", "a48e72", "d0be9a"],
    "conch":  ["3a2228", "784a4a", "b47e6c", "dcb092", "f8e2c6"],
    "ash":    ["1e1c1e", "3a383a", "5e5a5a", "868080", "b0aaa4"],
    "cork":   ["1e140c", "443020", "6e5034", "94724a", "b89668"],
    "shadow": ["0e0a16", "1e1630", "34284c", "4e3e6a", "6e5c8a"],
    # emissive
    "soul":   ["10305a", "1e5aa0", "3a9ae8", "8ad0ff", "e6f8ff"],
    "tox":    ["1e4a10", "3e8a1e", "7ccc2e", "c4f552", "eeffb0"],
    "brine":  ["0e2a1e", "1a5038", "2e8a5a", "5cc27e", "b0f0b8"],
    "foam":   ["5e8a8c", "9cc6c4", "d0ece6", "eefcf6", "ffffff"],
    "lilac":  ["3a1e5a", "6a3ea0", "a476d8", "d4b0f4", "f4e8ff"],
}
for _k, _v in _NEW.items():
    J.RAMPS[_k] = [J._h(c) for c in _v]
J.EMISSIVE |= {"soul", "tox", "brine", "foam", "lilac"}
J.SHINY |= {"ice", "seed", "bronze", "wax", "conch"}


# ------------------------------------------------------------------ Crawl's palette
# Crawl's own item and prop art is muted, dusty and dark, with at most one small bright thing per sprite. Every
# material here is pulled into that range (less saturation, a little darker, a little dust mixed in) except the one
# material an icon names as its accent (its gem, flame or rune). tools/palette_check.py measures the result against
# the vanilla atlases.
MUTE_SAT, MUTE_VAL, MUTE_DUST = 0.55, 0.93, 0.10
DUST = (86, 74, 64)


def mute_rgb(c):
    h, sat, val = colorsys.rgb_to_hsv(*(x / 255.0 for x in c))
    rgb = colorsys.hsv_to_rgb(h, sat * MUTE_SAT, val * MUTE_VAL)
    return tuple(int(round(x * 255 * (1 - MUTE_DUST) + d * MUTE_DUST)) for x, d in zip(rgb, DUST))


ACCENT_TOP = 224          # an accent's lit tones stay under this (its pure highlight may go to white)


def crawl_palette(accent=()):
    """A Pen.image remap: every material muted to Crawl's range except the accent materials."""
    def f(mat, tone):
        c = J.RAMPS[mat][max(0, min(4, tone))]
        if mat not in accent: return mute_rgb(c)
        if tone < 4 and max(c) > ACCENT_TOP:
            k = ACCENT_TOP / float(max(c))
            c = tuple(int(x * k) for x in c)
        return c
    return f


def crawl_image(im, accent_share=0.15):
    """Mute a finished image (a hand-drawn HUD icon, a potion) the same way: every colour through mute_rgb except its
    most saturated colour family, kept as the accent when it covers at most accent_share of the pixels."""
    im = im.convert("RGBA")
    p = im.load()
    cols = [(x, y, p[x, y][:3]) for y in range(im.height) for x in range(im.width) if p[x, y][3]]
    if not cols: return im
    fam = {}
    for x, y, c in cols:
        h, sat, val = colorsys.rgb_to_hsv(*(v / 255.0 for v in c))
        if (max(c) - min(c)) / 255.0 > 0.45: fam.setdefault(int(h * 9), []).append((x, y))
    keep = set()
    if fam:
        best = max(fam.values(), key=len)
        if len(best) <= accent_share * len(cols): keep = set(best)
    out = im.copy()
    q = out.load()
    for x, y, c in cols:
        if (x, y) not in keep:
            q[x, y] = mute_rgb(c) + (p[x, y][3],)
        elif max(c) > ACCENT_TOP:
            q[x, y] = tuple(int(v * ACCENT_TOP / float(max(c))) for v in c) + (p[x, y][3],)
    return out


def accent(*mats):
    """Decorator: the one bright material of an icon (a flame, a gem, a rune); everything else is muted."""
    def deco(fn):
        fn.accent = set(mats)
        return fn
    return deco


# ------------------------------------------------------------------ the pen: cell units -> rig pixels at any scale
class Pen:
    """Draws in 16-unit cell coordinates (centre (8, 8), y down) onto a Rig scaled by S."""

    def __init__(self, S=1.0, rot=0.0):
        self.r = Rig()
        self.S = S
        self.rot = rot                 # degrees: turns the whole drawing about the cell centre (the light stays put)
        self._c, self._s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(self, x, y):
        x, y = x - 8, y - 8
        if self.rot: x, y = x * self._c - y * self._s, x * self._s + y * self._c
        return x * self.S, y * self.S

    def _clip(self, kw):
        c = kw.get("clip")
        if c: kw["clip"] = lambda x, y: c(x / self.S + 8, y / self.S + 8)
        return kw

    def ell(self, cx, cy, rx, ry, mat, z, **kw):
        X, Y = self.P(cx, cy)
        if self.rot: kw["ang"] = kw.get("ang", 0.0) + self.rot
        return self.r.ell(X, Y, rx * self.S, ry * self.S, mat, z, **self._clip(kw))

    def tube(self, pts, radii, mat, z, **kw):
        return self.r.tube([self.P(*p) for p in pts], [q * self.S for q in radii], mat, z, **kw)

    def poly(self, pts, mat, z, **kw):
        return self.r.poly([self.P(*p) for p in pts], mat, z, **kw)

    def line(self, x0, y0, x1, y1, mat, z, tone=2):
        return self.r.line(*self.P(x0, y0), *self.P(x1, y1), mat, z, tone=tone)

    def polyline(self, pts, mat, z, tone=2, tones=None):
        return self.r.polyline([self.P(*p) for p in pts], mat, z, tone=tone, tones=tones)

    def dot(self, x, y, mat, tone, z):
        X, Y = self.P(x, y)
        p = self.r.part(True, z)
        n = 2 if self.S >= 1.9 else 1
        for i in range(n):
            for j in range(n):
                self.r.put(X + i, Y + j, z, mat, 0.5, p, tone)
        return p

    def arc(self, cx, cy, R, a0, a1, mat, z, tone=3, ry=None, step=6):
        """A 1 px arc of radius R (ry for an ellipse) from a0 to a1 degrees (0 = right, 90 = down)."""
        ry = R if ry is None else ry
        n = max(2, int(abs(a1 - a0) / step))
        pts = [(cx + R * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
               for i in range(n + 1)]
        return self.polyline(pts, mat, z, tone=tone)

    def die(self, cx, cy, size, **kw):
        X, Y = self.P(cx, cy)
        if self.rot: kw["rz"] = kw.get("rz", 0.0) + self.rot
        return die3(self.r, X, Y, size * self.S, **kw)

    def glint(self, x, y, z=9.0, big=False):
        """A four-point sparkle: the frame-2 shine."""
        self.dot(x, y, "white", 4, z)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.dot(x + dx, y + dy, "white", 2, z)
        if big:
            for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
                self.dot(x + dx, y + dy, "white", 1, z)

    def image(self, n=None, sep=None, remap=None):
        """Resolve to an n x n RGBA image. sep: the colour the icon sits on (the spell card); edge pixels too close to
        it in value get a 1 px rim in their material's darkest tone, so they separate from it, and only there.
        remap(mat, tone) -> rgb recolours every pixel (a greyed-out copy, say)."""
        n = n or int(round(16 * self.S))
        s = self.r.resolve(floor=False)
        px = dict(s.px) if remap is None else {k: remap(*s.tones[k]) for k in s.px}
        if sep is not None:
            lum = lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
            for (x, y), c in s.px.items():
                m = s.tones[(x, y)][0]
                if m in J.EMISSIVE or abs(lum(c) - lum(sep)) >= SEP_DIFF: continue
                ink = remap(m, 0) if remap else J.RAMPS[m][0]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in s.px: px[q] = ink
        im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        p = im.load()
        lost = 0
        for (x, y), c in px.items():
            X, Y = x + n // 2, y + n // 2
            if 0 <= X < n and 0 <= Y < n: p[X, Y] = tuple(c[:3]) + (255,)
            else: lost += 1
        return im, lost


def ring_pts(cx, cy, rx, ry, a0=0.0, a1=360.0, n=28):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def heart_pts(cx, cy, w, h, n=40):
    """Outline of a heart, w wide and h tall, centred (cx, cy)."""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        out.append((cx + x / 32.0 * w, cy + (y + 2.5) / 30.0 * h))
    return out


# ================================================================== SPELLS (glyphs laid on the parchment card)
@accent("fire")
def ember_volley(g, ph):
    k = 1 if ph else 0
    # three candle-flame bolts fanned to the right, each with a wax-ember trail
    for (hx, hy, tx, ty, s) in ((11.5 + k, 3.6, 2.0, 6.0, 0.9), (13.6 + k, 8.0, 3.0, 8.4, 1.1), (11.5 + k, 12.4, 2.0, 10.6, 0.9)):
        ang = math.atan2(hy - ty, hx - tx)
        ca, sa = math.cos(ang), math.sin(ang)
        g.tube([(tx, ty), (lerp(tx, hx, 0.55), lerp(ty, hy, 0.55)), (hx - 1.2 * ca, hy - 1.2 * sa)], [0.3, 0.9 * s, 1.4 * s],
               "ember", 1.0, flat=2)
        g.tube([(lerp(tx, hx, 0.35), lerp(ty, hy, 0.35)), (hx - 1.0 * ca, hy - 1.0 * sa)], [0.2, 0.7 * s], "ember", 1.2, flat=4)
        # head: a teardrop flame pointing along the flight
        g.ell(hx - 0.4 * ca, hy - 0.4 * sa, 2.1 * s, 1.55 * s, "ember", 1.5, ang=math.degrees(ang), flat=3)
        g.ell(hx - 0.1 * ca, hy - 0.1 * sa, 1.0 * s, 0.7 * s, "fire", 1.6, ang=math.degrees(ang), flat=4)
        g.dot(hx + 1.2 * ca, hy + 1.2 * sa, "ember", 3, 1.4)
    for (x, y) in (((4, 4), (6, 12.5), (2, 9)) if not ph else ((3, 5), (5, 13), (1, 8))):
        g.dot(x, y, "ember", 3, 2.0)
    g.dot(7 + k, 6.2, "ember", 3, 2.0); g.dot(8 - k, 10.4, "ember", 3, 2.0)


def wax_slick(g, ph):
    # a spreading pool of candle wax with runners, a drop falling into it
    for (cx, cy, rx, ry) in ((8, 12.8, 7.0, 2.3), (2.6, 13.8, 2.0, 1.1), (13.6, 13.6, 2.0, 1.1)):
        g.ell(cx, cy, rx, ry, "wax", 0.9, flat=1)
    for (cx, cy, rx, ry) in ((8, 12.2, 6.6, 2.0), (2.6, 13.2, 1.6, 0.9), (13.6, 13.0, 1.6, 0.9)):
        g.ell(cx, cy, rx, ry, "wax", 1.0, flat=2)
    g.ell(6.8, 11.6, 3.8, 0.9, "wax", 1.1, flat=3)
    g.line(4.4, 11.4, 6.2, 11.0, "wax", 1.2, tone=4)
    y = 1.4 if not ph else 3.2
    g.ell(8, y + 3.6, 2.1, 2.1, "wax", 2.0, flat=2)
    g.poly([(6.2, y + 3.2), (9.8, y + 3.2), (8, y)], "wax", 2.0, flat=2)
    g.ell(7.4, y + 3.4, 1.0, 1.3, "wax", 2.1, flat=3)
    g.dot(7.2, y + 2.8, "wax", 4, 2.2)
    if ph:
        g.dot(4.6, 9.6, "wax", 3, 2.0); g.dot(11.4, 9.4, "wax", 3, 2.0)


@accent("crim")
def marrow_spikes(g, ph):
    # cracked earth mound
    g.ell(8, 13.2, 7.4, 1.9, "dirt", 0.5, bias=0.2)
    g.line(2.4, 13.0, 4.2, 14.0, "dirt", 0.6, tone=0)
    g.line(11.4, 12.8, 13.4, 13.8, "dirt", 0.6, tone=0)
    # three bone spikes, the middle one tallest, marrow red at the tips
    for (cx, top, w, z, lean) in ((3.8, 5.4, 2.2, 1.0, -0.8), (12.2, 6.0, 2.1, 1.0, 0.8), (8.0, 0.8, 2.8, 2.0, 0.0)):
        base = 12.8
        p = g.poly([(cx - w, base), (cx + w, base), (cx + lean + 0.5, top + 1.2), (cx + lean, top), (cx + lean - 0.5, top + 1.2)],
                   "ivory", z, curve=0.95)
        g.ell(cx + lean, top + 1.3, 0.75, 1.0, "crim", z + 0.02, flat=3)
        g.dot(cx + lean - 0.3, top + 2.6, "crim", 1, z + 0.03)
    for (x, y) in ((5.8, 12.4), (10.4, 12.6)):
        g.ell(x, y, 1.0, 0.7, "dirt", 2.5, bias=0.2)
    if ph:
        g.glint(8.0, 3.2)


@accent("eye")
def bone_boomerang(g, ph):
    k = 1 if ph else 0
    # motion arcs trailing behind it: it spins on its way out
    g.arc(8.6, 8.2, 7.0, 150 - 12 * k, 205 - 12 * k, "white", 0.2, tone=2)
    g.arc(8.6, 8.2, 7.0, 60 - 12 * k, 105 - 12 * k, "white", 0.2, tone=1)
    g.arc(8.6, 8.2, 7.0, 240 - 12 * k, 290 - 12 * k, "white", 0.2, tone=1)
    # skull: cranium, cheekbones, teeth
    p = g.ell(9.0, 6.8, 4.6, 4.0, "ivory", 1.0, bias=0.1)
    g.ell(9.0, 10.0, 3.2, 2.4, "ivory", 1.0, part=p, bias=0.1)
    for x in (7.8, 9.0, 10.2):
        g.line(x, 11.0, x, 12.0, "ivory", 1.1, tone=1)
    g.ell(7.2, 8.0, 1.5, 1.4, "blk", 1.2, flat=0)
    g.ell(10.8, 8.0, 1.5, 1.4, "blk", 1.2, flat=0)
    g.dot(7.2, 8.0, "eye", 3, 1.3); g.dot(10.8, 8.0, "eye", 3, 1.3)
    g.poly([(8.5, 9.4), (9.5, 9.4), (9.0, 10.4)], "blk", 1.25, flat=1)
    g.line(10.6, 3.4, 11.8, 4.8, "ivory", 1.2, tone=1)
    if ph:
        g.glint(6.6, 4.2)


@accent("pink")
def spore_bomb(g, ph):
    s = 0.3 if ph else 0.0
    g.ell(8, 9.2, 5.8 + s, 5.6 + s, "spore", 1.0)
    for (x, y, r_) in ((5.8, 7.6, 1.1), (10.0, 6.8, 0.9), (9.6, 10.6, 1.2), (6.2, 11.8, 0.8), (12.0, 9.4, 0.7)):
        g.ell(x, y, r_, r_ * 0.85, "pink", 1.1)
    # stem and a curled leaf
    g.tube([(8, 4.0), (8.6, 2.0), (9.8, 1.0)], [0.9, 0.7, 0.5], "leaf", 1.2)
    g.poly([(8.8, 2.6), (12.6, 1.4), (11.2, 3.6)], "leaf", 1.1, normal=(-0.2, -0.6, 1.0))
    # spores drifting out
    pts = ((2.4, 4.4), (13.6, 4.6), (1.6, 10.6), (14.2, 12.4)) if not ph else ((2.0, 3.4), (14.2, 3.8), (1.2, 9.4), (14.6, 11.2))
    for (x, y) in pts:
        g.dot(x, y, "pink", 3, 2.0)
    g.dot(6.2, 6.0, "spore", 4, 1.3)


@accent("leaf")
def root_snare(g, ph):
    g.ell(5.6, 14.2, 5.0, 1.4, "dirt", 0.4, bias=0.2)
    # a root climbs out of the soil, arches over and hooks back on itself: a snare loop with daylight through it
    pts = [(3.2, 14.6), (2.6, 10.6), (3.4, 6.2), (6.2, 3.0), (9.8, 2.4), (12.8, 4.2), (13.6, 7.6), (12.2, 10.4), (9.6, 11.0),
           (8.2, 9.2), (9.0, 7.2), (10.6, 7.2)]
    g.tube(pts, [1.9, 1.8, 1.6, 1.5, 1.4, 1.3, 1.1, 1.0, 0.8, 0.7, 0.55, 0.45], "root", 1.0, bias=0.3)
    g.tube([(6.4, 14.6), (7.2, 12.8), (6.6, 11.6)], [0.8, 0.6, 0.4], "root", 1.6, bias=0.3)
    for (x0, y0, x1, y1) in ((4.2, 4.6, 3.0, 3.2), (12.0, 2.8, 13.2, 1.6), (14.4, 9.4, 15.4, 10.4), (2.0, 9.6, 0.8, 9.2)):
        g.line(x0, y0, x1, y1, "ivory", 1.7, tone=3)
    g.poly([(7.6, 2.6), (5.8, 0.8), (9.0, 0.8)], "leaf", 1.8, normal=(-0.3, -0.6, 1.0), bias=0.2)
    if ph:
        g.glint(11.2, 0.8)


@accent("soul")
def shard_nova(g, ph):
    out = 0.8 if ph else 0.0
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        ca, sa = math.cos(a), math.sin(a)
        long_ = i % 2 == 0
        r0, L, w = 2.0 + out, (7.2 if long_ else 5.8) + out * 0.5, (1.6 if long_ else 1.25)
        m = r0 + (L - r0) * 0.4
        pts = [(8 + r0 * ca, 8 + r0 * sa), (8 + m * ca - w * sa, 8 + m * sa + w * ca), (8 + L * ca, 8 + L * sa),
               (8 + m * ca + w * sa, 8 + m * sa - w * ca)]
        lit = -(ca + sa)
        g.poly(pts[:3] + [(8 + m * ca, 8 + m * sa)], "ice", 1.0 + 0.01 * i, flat=3 if lit > -0.3 else 2)
        g.poly([pts[0], (8 + m * ca, 8 + m * sa), pts[2], pts[3]], "ice", 1.0 + 0.01 * i, flat=2 if lit > -0.3 else 1)
        g.dot(8 + (L - 1.0) * ca, 8 + (L - 1.0) * sa, "ice", 4, 1.1 + 0.01 * i)
    g.ell(8, 8, 2.2 - out * 0.5, 2.2 - out * 0.5, "soul", 2.0, flat=3)
    g.ell(8, 8, 1.0, 1.0, "soul", 2.05, flat=4)
    if ph:
        for (x, y) in ((8, 1.4), (1.4, 8), (14.6, 8), (8, 14.6)):
            g.dot(x, y, "white", 3, 2.0)


def figure(g, x, y, mat, z, flip=False, k=1.0):
    """A hooded silhouette, feet at (x, y), k times the base size."""
    s = -1 if flip else 1
    g.poly([(x - 2.4 * k, y), (x + 2.4 * k, y), (x + 1.5 * k, y - 6.0 * k), (x - 1.5 * k, y - 6.0 * k)], mat, z, curve=0.7, bias=0.2)
    g.ell(x, y - 7.6 * k, 2.0 * k, 2.1 * k, mat, z + 0.01, bias=0.2)
    g.poly([(x - 2.0 * k, y - 8.0 * k), (x + 2.0 * k, y - 8.0 * k), (x + 0.5 * s, y - 11.0 * k)], mat, z + 0.02,
           normal=(-0.3, -0.5, 1.0), bias=0.2)


@accent("lilac")
def shadow_swap(g, ph):
    figure(g, 2.8, 14.8, "viol", 1.0)
    figure(g, 13.2, 14.8, "shadow", 1.0, flip=True)
    g.dot(2.2, 7.2, "glow", 3, 1.2); g.dot(3.6, 7.2, "glow", 3, 1.2)
    g.dot(12.4, 7.2, "lilac", 2, 1.2); g.dot(13.8, 7.2, "lilac", 2, 1.2)
    # the swap: one arrow across to the right, one back to the left
    k = 0.6 if ph else 0.0
    g.tube([(5.0, 5.4), (8.0, 4.6 - k), (10.0, 5.0)], [0.6], "lilac", 2.0, flat=3)
    g.poly([(9.6, 3.0), (12.4, 5.2), (9.6, 7.0)], "lilac", 2.1, flat=4)
    g.tube([(11.0, 10.4), (8.0, 11.2 + k), (6.0, 10.8)], [0.6], "lilac", 2.0, flat=2)
    g.poly([(6.4, 9.0), (3.6, 11.0), (6.4, 12.8)], "lilac", 2.1, flat=2)


@accent("soul")
def soul_lantern(g, ph):
    # hook and ring
    g.line(8, 0, 8, 1.6, "iron", 0.5, tone=2)
    g.arc(8, 2.4, 1.2, 180, 360, "iron", 0.6, tone=3)
    # cap
    g.poly([(4.4, 4.8), (11.6, 4.8), (9.6, 2.8), (6.4, 2.8)], "iron", 1.0, normal=(-0.2, -0.8, 0.6))
    g.poly([(4.0, 4.6), (12.0, 4.6), (12.0, 5.6), (4.0, 5.6)], "iron", 1.1)
    # glass and the soul flame inside
    g.poly([(5.0, 5.6), (11.0, 5.6), (11.0, 12.0), (5.0, 12.0)], "shadow", 0.8, flat=2)
    f = 0.5 if ph else 0.0
    g.ell(8, 9.6, 2.4, 2.4, "glass", 0.9, flat=1)
    g.ell(8, 9.4 - f, 1.4, 2.0 + f, "soul", 0.95, flat=3)
    g.poly([(7.0, 9.0), (9.0, 9.0), (8.0 + (0.4 if ph else -0.3), 5.8 - f)], "soul", 0.95, flat=3)
    g.ell(8, 10.0, 0.7, 1.0, "soul", 0.97, flat=4)
    # frame bars over the glass
    for x in (5.0, 11.0):
        g.tube([(x, 5.6), (x, 12.2)], [0.6], "iron", 1.2)
    g.line(8, 5.8, 8, 7.0, "iron", 1.2, tone=2)
    # base
    g.poly([(4.0, 12.0), (12.0, 12.0), (11.0, 14.4), (5.0, 14.4)], "iron", 1.1, curve=0.6)
    g.dot(6.4, 6.4, "white", 3, 1.0)
    if ph:
        g.dot(2.4, 7.0, "soul", 3, 2.0); g.dot(13.6, 9.6, "soul", 3, 2.0)


@accent("white")
def bell_toll(g, ph):
    t = 0.6 if ph else 0.0
    # short sound rings either side, pushed out on the toll frame
    for R, tone in ((6.2 + t, 4), (7.4 + t, 2)):
        g.arc(8, 8.4, R, 155, 205, "white", 0.2, tone=tone)
        g.arc(8, 8.4, R, -25, 25, "white", 0.2, tone=tone)
    g.tube(ring_pts(8, 2.2, 1.3, 1.1, 180, 360, 10), [0.6], "bronze", 0.8)
    g.poly([(5.4, 4.0), (10.6, 4.0), (11.4, 8.0), (13.2, 11.6), (2.8, 11.6), (4.6, 8.0)], "bronze", 1.0, curve=0.95, bias=0.1)
    g.ell(8, 4.2, 2.6, 1.2, "bronze", 1.02, bias=0.1)
    g.ell(8, 11.7, 5.3, 1.3, "bronze", 1.05, bias=0.0)
    g.ell(8, 11.9, 4.2, 0.7, "bronze", 1.06, flat=0)
    g.ell(8 + (0.8 if ph else 0.0), 13.4, 1.2, 1.1, "bronze", 1.1)
    if ph:
        g.glint(5.0, 5.4)


@accent("foam")
def undertow(g, ph):
    rot = 25 if ph else 0
    g.ell(8, 8.6, 7.4, 6.4, "sea", 0.5, bias=-0.15)
    # spiral arms in lighter water, foam on their crests
    for arm in range(3):
        pts = []
        for i in range(14):
            t = i / 13.0
            a = math.radians(arm * 120 + rot + t * 300)
            rr = 6.6 * (1 - t) + 0.6
            pts.append((8 + rr * math.cos(a), 8.6 + rr * math.sin(a) * 0.86))
        g.tube(pts, [1.2 - 0.06 * i for i in range(14)], "sea", 0.8 + 0.01 * arm, bias=0.35)
        g.polyline(pts[:7], "foam", 0.9 + 0.01 * arm, tone=2 if arm else 3)
    g.ell(8, 8.6, 1.4, 1.2, "sea", 1.0, flat=0)
    for (x, y) in (((2.0, 3.6), (13.4, 13.0)) if not ph else ((1.4, 4.6), (14.2, 12.0))):
        g.dot(x, y, "foam", 3, 1.2)


@accent("foam")
def riptide(g, ph):
    # a curling wave: the trough on the right, the crest rolling over to the left
    g.poly([(1.0, 14.6), (15.0, 14.6), (15.0, 11.4), (12.6, 8.6), (11.4, 5.2), (9.2, 2.4), (6.0, 1.6), (3.0, 2.6),
            (1.4, 5.0), (2.0, 7.6), (4.0, 8.4), (5.4, 6.6), (5.0, 4.8)], "sea", 1.0, normal=(-0.3, -0.2, 1.0), curve=0.5, bias=0.2)
    g.poly([(5.4, 6.6), (6.4, 4.4), (8.6, 4.8), (9.4, 8.0), (7.8, 10.8), (5.6, 9.8)], "sea", 1.05, flat=1)
    g.ell(7.2, 7.6, 1.2, 1.6, "sea", 1.06, flat=0)
    g.polyline([(1.6, 5.2), (2.8, 3.0), (5.8, 2.0), (8.8, 2.8), (10.8, 5.0), (11.8, 8.0)], "foam", 1.2, tone=3)
    g.polyline([(2.2, 7.4), (3.8, 8.0), (5.0, 6.8)], "foam", 1.2, tone=2)
    g.polyline([(9.6, 11.2), (12.4, 9.6), (14.6, 11.8)], "foam", 1.2, tone=2)
    g.line(1.0, 13.2, 6.0, 12.4, "sea", 1.1, tone=3)
    spray = ((12.2, 2.0), (13.8, 3.6), (0.8, 1.2)) if not ph else ((12.8, 1.0), (14.4, 2.6), (1.4, 0.4))
    for (x, y) in spray:
        g.dot(x, y, "foam", 3, 1.3)


@accent("gold")
def wild_card(g, ph):
    # the joker: an upright card with a red border, a three-pointed jester's cap with bells, a pale face
    g.poly([(2.6, 0.8), (13.4, 0.8), (13.4, 15.2), (2.6, 15.2)], "card", 1.0, normal=(-0.2, -0.3, 1.0))
    g.polyline([(3.6, 1.8), (12.4, 1.8), (12.4, 14.2), (3.6, 14.2), (3.6, 1.8)], "crim", 1.1, tone=2)
    g.poly([(4.8, 9.4), (7.0, 9.4), (4.4, 3.6)], "crim", 1.2, flat=2)
    g.poly([(9.0, 9.4), (11.2, 9.4), (11.6, 3.6)], "crim", 1.2, flat=1)
    g.poly([(6.0, 9.4), (10.0, 9.4), (8.0, 2.6)], "viol", 1.25, flat=3)
    g.poly([(4.6, 9.2), (11.4, 9.2), (11.4, 10.4), (4.6, 10.4)], "gold", 1.3, flat=2)
    for (x, y) in ((4.4, 3.4), (8.0, 2.4), (11.6, 3.4)):
        g.dot(x, y, "gold", 3, 1.35)
    g.ell(8.0, 12.2, 2.2, 1.5, "porc", 1.3)
    g.dot(7.0, 12.0, "blk", 0, 1.35); g.dot(9.0, 12.0, "blk", 0, 1.35)
    g.dot(8.0, 13.0, "crim", 2, 1.35)
    if ph:
        g.glint(11.0, 2.8)


def rot_pts(pts, ang, pivot):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    return [(pivot[0] + (x - pivot[0]) * ca - (y - pivot[1]) * sa, pivot[1] + (x - pivot[0]) * sa + (y - pivot[1]) * ca)
            for (x, y) in pts]


@accent("crim")
def loaded_dice(g, ph):
    g.die(5.0, 5.4, 6.4, rx=8.0, ry=-30.0, rz=-10.0, z=0.5, pip_min=2.6, pip_faces=2)
    g.die(10.2, 10.4, 7.6, rx=-4.0, ry=28.0, rz=6.0, z=1.0, pip_min=2.6, pip_faces=2)
    if ph:
        g.glint(7.8, 7.4)


@accent("lilac")
def puppet_strings(g, ph):
    sw = 0.8 if ph else 0.0
    # control cross
    g.tube([(2.6, 2.6), (13.4, 2.6)], [0.85], "wood", 1.0, bias=0.2)
    g.tube([(8.0, 0.6), (8.0, 5.0)], [0.85], "wood", 1.1, bias=0.2)
    g.ell(8, 2.6, 0.9, 0.9, "gold", 1.2)
    # strings to a dangling puppet
    px = 8.0 + sw
    hands = [(px - 3.4, 9.4 - sw * 0.6), (px + 3.4, 9.4 + sw * 0.4)]
    for (a, b) in (((2.8, 3.2), hands[0]), ((13.2, 3.2), hands[1]), ((8.0, 5.2), (px, 6.0))):
        g.line(a[0], a[1], b[0], b[1], "lilac", 0.5, tone=1)
    g.ell(px, 7.2, 1.6, 1.5, "porc", 1.0)
    g.dot(px - 0.6, 7.0, "blk", 0, 1.1); g.dot(px + 0.6, 7.0, "blk", 0, 1.1)
    g.poly([(px - 1.8, 8.8), (px + 1.8, 8.8), (px + 2.2, 12.4), (px - 2.2, 12.4)], "crim", 0.9, curve=0.6, bias=0.2)
    g.tube([(px - 1.6, 9.2), hands[0]], [0.5], "crim", 0.95, bias=0.2)
    g.tube([(px + 1.6, 9.2), hands[1]], [0.5], "crim", 0.95, bias=0.2)
    g.tube([(px - 1.0, 12.4), (px - 1.4 - sw * 0.4, 14.8)], [0.5], "blk", 0.85, bias=0.3)
    g.tube([(px + 1.0, 12.4), (px + 1.4 - sw * 0.2, 14.8)], [0.5], "blk", 0.85, bias=0.3)
    if ph:
        g.dot(2.4, 3.6, "lilac", 3, 2.0); g.dot(13.6, 3.6, "lilac", 3, 2.0)


# ================================================================== ARTIFACTS
@accent("fire")
def ember_heart(g, ph):
    p = g.ell(5.2, 5.8, 3.6, 3.4, "coal", 1.0)
    g.ell(10.8, 5.8, 3.6, 3.4, "coal", 1.0, part=p)
    g.poly([(1.7, 6.4), (14.3, 6.4), (8.0, 14.6)], "coal", 1.0, curve=0.9, part=p)
    # glowing cracks running out from a hot core
    hot = 3 if ph else 2
    for pts in (((8, 8.6), (5.6, 6.6), (3.4, 6.6)), ((8, 8.6), (10.4, 6.4), (12.8, 7.0)), ((8, 8.6), (7.2, 11.4), (8.0, 13.2)),
                ((8, 8.6), (10.2, 10.2)), ((5.6, 6.6), (5.4, 4.0)), ((10.4, 6.4), (11.0, 4.0))):
        g.polyline(pts, "ember", 1.1, tone=hot)
    g.ell(8, 8.6, 1.8, 1.6, "fire", 1.2, flat=3)
    g.dot(8, 8.6, "fire", 4, 1.3)
    g.dot(4.0, 4.2, "coal", 4, 1.05); g.dot(4.6, 3.6, "coal", 4, 1.05)
    sp = ((11.8, 1.6), (13.6, 0.6)) if ph else ((12.6, 1.8),)
    for (x, y) in sp:
        g.dot(x, y, "ember", 3, 2.0)


@accent("tox")
def venom_gland(g, ph):
    # duct out to the right and the dripping tip
    g.tube([(11.0, 8.0), (13.2, 7.4), (14.4, 9.0)], [1.3, 1.0, 0.8], "flesh2", 0.8)
    g.ell(8, 8.2, 5.8, 5.0, "flesh2", 1.0)
    # the venom showing through the thin skin
    g.ell(8.2, 8.6, 3.2, 2.8, "brine", 1.1, flat=1)
    g.ell(7.8, 8.2, 1.6, 1.4, "tox", 1.15, flat=3)
    g.dot(7.4, 7.8, "tox", 4, 1.2)
    # veins
    for pts in (((3.2, 6.4), (4.8, 7.0), (5.2, 8.6)), ((6.4, 3.6), (7.4, 5.0)), ((11.8, 11.0), (10.6, 10.4))):
        g.polyline(pts, "flesh2", 1.2, tone=1)
    g.dot(5.0, 4.6, "flesh2", 4, 1.2)
    d = 1.4 if ph else 0.0
    g.ell(14.4, 10.6 + d, 0.7, 0.9, "brine", 1.3, flat=2)
    g.ell(7.0, 13.6, 0.8, 0.9, "brine", 1.3, flat=2)
    g.dot(7.0, 14.8, "brine", 3, 1.3)


@accent("ice")
def rime_ring(g, ph):
    # the band seen from above-front, the back half behind the stone
    back = ring_pts(8, 10.4, 5.6, 2.8, 180, 360, 18)
    front = ring_pts(8, 10.4, 5.6, 2.8, 0, 180, 18)
    g.tube(back, [1.0], "steel", 0.6, bias=0.1)
    g.tube(front, [1.5], "steel", 1.2, bias=0.15)
    g.ell(8, 10.4, 4.0, 1.4, "shadow", 0.5, flat=0)
    # claw setting and a pale blue stone, frost round it
    g.ell(8, 7.4, 2.8, 1.4, "steel", 1.3, bias=0.1)
    g.ell(8, 5.0, 2.6, 2.6, "ice", 1.4, bias=0.1)
    g.dot(7.0, 4.0, "white", 4, 1.5); g.dot(7.6, 3.6, "ice", 4, 1.5)
    for (x0, y0, x1, y1) in ((5.2, 3.2, 3.8, 1.8), (10.8, 3.2, 12.2, 1.8), (8.0, 2.0, 8.0, 0.6)):
        g.line(x0, y0, x1, y1, "ice", 1.35, tone=3)
    for (x, y) in ((2.4, 9.0), (13.6, 12.0), (5.0, 13.6)):
        g.dot(x, y, "ice", 4, 1.4)
    if ph:
        g.glint(11.6, 12.2)


@accent("leaf")
def leech_seed(g, ph):
    # roots reaching down, hungry
    for pts, rr in ((((7.0, 11.0), (5.0, 12.6), (2.6, 13.0), (1.6, 14.6)), [0.8, 0.6, 0.45, 0.3]),
                    (((8.6, 11.4), (9.0, 13.4), (8.2, 15.0)), [0.8, 0.55, 0.3]),
                    (((10.0, 10.6), (12.4, 12.0), (14.2, 11.6)), [0.7, 0.5, 0.3])):
        g.tube(pts, rr, "root", 0.8)
    g.ell(8.0, 7.6, 4.4, 5.0, "seed", 1.0, ang=-12)
    g.line(9.6, 3.6, 10.0, 10.8, "seed", 1.05, tone=1)
    g.dot(6.0, 5.0, "seed", 4, 1.1); g.dot(6.4, 4.4, "seed", 4, 1.1)
    # sprout
    g.tube([(9.0, 3.0), (9.6, 1.4), (11.0, 0.6)], [0.5, 0.45, 0.35], "leaf", 1.2)
    g.poly([(9.8, 1.4), (13.4, 0.4), (12.2, 2.6)], "leaf", 1.25, normal=(-0.3, -0.5, 1.0))
    g.dot(4.6, 13.8, "seed", 3, 1.3)
    if ph:
        g.glint(5.4, 5.6)


def thorn_mail(g, ph):
    # a mail shirt: chest and sleeves, the links in a checker of two tones, a dark neck hole
    pts = [(4.8, 1.6), (11.2, 1.6), (14.8, 6.6), (12.6, 8.0), (11.6, 6.8), (11.8, 14.2), (4.2, 14.2), (4.4, 6.8), (3.4, 8.0),
           (1.2, 6.6)]
    p = g.poly(pts, "steel", 1.0, curve=0.6, bias=0.3)
    for (k, v) in list(g.r.b.items()):
        if v[3] == p and (k[0] + k[1]) % 2 == 0 and v[4] is None:
            v[2] -= 0.4
    g.ell(8.0, 1.8, 2.2, 1.0, "iron", 1.05, flat=0)
    g.line(4.2, 14.2, 11.8, 14.2, "iron", 1.05, tone=1)
    # a thorned vine across the chest and down one side
    vine = [(1.6, 7.2), (4.4, 8.0), (8.0, 7.0), (11.0, 8.0), (11.2, 11.0), (8.4, 12.4), (5.6, 12.0)]
    g.tube(vine, [0.55], "leaf", 1.2, bias=0.4)
    for (x0, y0, x1, y1) in ((4.4, 8.0, 4.2, 9.6), (8.0, 7.0, 8.2, 5.6), (11.2, 11.0, 12.8, 11.4), (8.4, 12.4, 8.6, 13.8)):
        g.line(x0, y0, x1, y1, "ivory", 1.25, tone=3)
    g.poly([(11.0, 8.0), (13.6, 6.2), (12.8, 8.8)], "leaf", 1.25, normal=(-0.3, -0.5, 1.0), bias=0.3)
    if ph:
        g.glint(6.0, 4.0)


@accent("fire")
def saints_wick(g, ph):
    # halo behind the flame
    g.tube(ring_pts(8, 4.2, 3.8, 3.6, 0, 360, 28), [0.6], "gold", 0.5, bias=0.2)
    # candle: a wax pillar with drips, on a little dish
    g.ell(8, 14.0, 5.0, 1.4, "bronze", 0.8)
    g.poly([(5.6, 7.4), (10.4, 7.4), (10.4, 13.6), (5.6, 13.6)], "wax", 1.0, curve=0.9)
    g.ell(8, 7.4, 2.4, 0.8, "wax", 1.02, bias=0.2)
    for (x, y0, y1) in ((6.2, 7.6, 10.6), (9.6, 7.6, 9.0)):
        g.tube([(x, y0), (x, y1)], [0.55], "wax", 1.05, bias=0.3)
    # flame on the wick
    f = 0.6 if ph else 0.0
    g.line(8, 6.0, 8, 7.2, "blk", 1.1, tone=1)
    g.ell(8, 4.6 - f * 0.4, 1.4, 2.0 + f * 0.4, "fire", 1.2, flat=2)
    g.ell(8, 4.9, 0.8, 1.2, "fire", 1.25, flat=3)
    g.dot(8, 5.2, "fire", 4, 1.3)
    g.poly([(7.1, 4.0), (8.9, 4.0), (8.0 + (0.5 if ph else -0.3), 1.0 - f)], "fire", 1.2, flat=2)
    if ph:
        g.dot(3.2, 2.2, "gold", 4, 1.3); g.dot(12.8, 6.0, "gold", 4, 1.3)


def lucky_die(g, ph):
    # one big ivory die showing six (green pips), seen from the front and a little above
    x0, y0, w, h, d = 2.4, 14.6, 9.8, 9.8, 2.6
    box_die(g, x0, y0, w, h, d, 6, "felt", 1.0, pips=False)
    cx, cy = x0 + w / 2.0, y0 - h / 2.0
    for (u, v) in J.PIPS[6]:
        px, py = cx + u * 2.6, cy + v * 2.8
        g.ell(px, py, 1.0, 1.0, "felt", 1.1, flat=1)
        g.dot(px - 0.4, py - 0.4, "felt", 3, 1.12)
    if ph:
        g.glint(3.2, 4.4)


@accent("ember")
def ash_hourglass(g, ph):
    # glass bulbs
    upper = [(4.4, 3.0), (11.6, 3.0), (11.0, 5.6), (8.6, 7.8), (7.4, 7.8), (5.0, 5.6)]
    lower = [(7.4, 8.2), (8.6, 8.2), (11.0, 10.4), (11.6, 13.0), (4.4, 13.0), (5.0, 10.4)]
    g.poly(upper, "glass", 0.8, flat=1)
    g.poly(lower, "glass", 0.8, flat=1)
    # ash: what's left above, the falling thread, the heap below with a few embers in it
    s = 0.6 if ph else 0.0
    g.poly([(5.6, 5.0 + s), (10.4, 5.0 + s), (8.4, 7.6), (7.6, 7.6)], "ash", 0.9, flat=2)
    g.line(8, 7.6, 8, 11.0, "ash", 0.95, tone=3)
    g.poly([(4.8, 13.0), (11.2, 13.0), (9.4, 10.6 - s), (6.6, 10.6 - s)], "ash", 0.9, curve=0.5)
    for (x, y) in (((6.4, 12.2), (9.2, 12.4)) if not ph else ((7.0, 12.4), (9.6, 11.8))):
        g.dot(x, y, "ember", 3, 1.0)
    # glass shine
    g.line(5.6, 3.6, 6.4, 5.4, "glass", 1.0, tone=4)
    g.line(5.4, 12.2, 5.8, 10.8, "glass", 1.0, tone=3)
    # wooden frame: plates and posts
    for y in (1.4, 13.4):
        g.poly([(2.8, y), (13.2, y), (13.2, y + 1.6), (2.8, y + 1.6)], "wood", 1.2, curve=0.4)
    for x in (3.4, 12.6):
        g.tube([(x, 3.0), (x, 13.4)], [0.7], "wood", 1.1)


def glass_mask(g, ph):
    # a face of thin glass: brow, cheeks, a pinched chin
    pts = [(3.0, 3.4), (6.0, 1.6), (10.0, 1.6), (13.0, 3.4), (13.4, 8.0), (11.4, 12.4), (8.0, 14.6), (4.6, 12.4), (2.6, 8.0)]
    p = g.poly(pts, "ice", 1.0, curve=0.9, bias=0.25)
    g.ell(8, 9.0, 4.0, 3.4, "ice", 1.0, bias=0.2, part=p)
    for x in (5.6, 10.4):
        g.poly([(x - 1.8, 6.6), (x + 1.8, 6.4), (x + 1.0, 8.0), (x - 1.2, 8.0)], "shadow", 1.1, flat=0)
    g.poly([(6.2, 11.4), (9.8, 11.4), (8.6, 12.2), (7.4, 12.2)], "shadow", 1.1, flat=0)
    crack = [(9.6, 1.8), (9.0, 4.0), (10.4, 5.4), (9.4, 9.0), (11.0, 10.6)]
    g.polyline(crack, "shadow", 1.2, tone=2)
    g.polyline([(x - 1, y) for (x, y) in crack[1:3]], "white", 1.21, tone=3)
    g.line(10.4, 5.4, 12.4, 5.0, "shadow", 1.2, tone=2)
    g.line(4.4, 3.2, 3.8, 6.0, "white", 1.15, tone=4 if ph else 3)
    if ph:
        g.glint(4.6, 3.0)


def barnacle_shell(g, ph):
    # a ribbed cockle shell crusted with barnacles at one end, a strand of weed caught on it
    p = g.ell(8, 8.8, 7.0, 5.0, "shell", 1.0, bias=0.2)
    g.poly([(5.0, 13.8), (11.0, 13.8), (10.2, 12.0), (5.8, 12.0)], "shell", 1.0, part=p, bias=0.1)
    hx, hy = 8.0, 13.4
    for i in range(9):
        a = math.radians(200 + i * 17.5)
        ca, sa = math.cos(a), math.sin(a)
        t = 0.0
        while True:
            x, y = hx + ca * (t + 0.2), hy + sa * (t + 0.2)
            if ((x - 8) / 7.0) ** 2 + ((y - 8.8) / 5.0) ** 2 > 0.8: break
            t += 0.2
        g.line(hx + ca * 1.6, hy + sa * 1.6, hx + ca * t, hy + sa * t, "shell", 1.02, tone=1 if i % 2 else 3)
    for (x, y, r_) in ((3.4, 7.4, 1.5), (5.2, 5.2, 1.2), (2.8, 10.2, 0.9)):
        g.ell(x, y, r_, r_ * 0.9, "ivory", 1.2, bias=0.1)
        g.dot(x + 0.2, y - 0.1, "shadow", 0, 1.25)
    g.tube([(12.8, 12.8), (14.6, 10.2), (14.0, 7.6)], [0.6, 0.5, 0.3], "brine", 1.3, flat=2)
    g.dot(2.0, 14.0, "sea", 3, 1.3); g.dot(3.2, 14.6, "sea", 2, 1.3)
    if ph:
        g.glint(9.6, 4.6)


@accent("pink")
def tidecaller(g, ph):
    # water spilling from the mouth of the conch
    sp = 0.8 if ph else 0.0
    g.ell(4.0, 14.0, 3.6, 1.2, "sea", 0.5, bias=0.25)
    for (x, y) in ((1.2, 11.6 - sp), (6.6, 12.8 - sp * 0.5), (0.8, 13.6)):
        g.dot(x, y, "foam", 3, 0.6)
    # a short spire up to the tip (top right)
    g.ell(12.6, 3.6, 2.0, 1.6, "conch", 0.92, ang=-40, bias=0.15)
    g.ell(13.8, 2.2, 1.0, 0.9, "conch", 0.9, ang=-40, bias=0.15)
    # the fat body whorl with knobs along its shoulder
    g.ell(8.6, 7.8, 5.4, 4.8, "conch", 1.0, ang=-35, bias=0.15)
    for (x, y) in ((6.0, 3.6), (8.8, 2.8), (11.4, 5.4), (12.6, 8.6)):
        g.ell(x, y, 1.0, 0.9, "conch", 1.02, bias=0.3)
    # the flared lip and the pink mouth on the lower left
    g.poly([(1.8, 12.8), (2.2, 7.6), (4.8, 5.4), (8.0, 8.4), (7.4, 12.8)], "conch", 1.05, curve=0.4, bias=0.35)
    g.poly([(3.2, 12.0), (3.4, 8.4), (5.0, 7.0), (7.0, 9.4), (6.2, 12.0)], "pink", 1.1, curve=0.5, bias=0.15)
    g.poly([(4.2, 11.4), (4.4, 9.2), (5.4, 8.4), (6.0, 10.4)], "pink", 1.12, flat=1)
    g.polyline([(9.2, 4.6), (11.4, 7.0), (11.0, 10.2)], "conch", 1.03, tone=1)
    if ph:
        g.glint(8.6, 5.0)


def brine_flask(g, ph):
    # bottle: round belly, long neck, cork and a twist of cord
    g.ell(8, 10.6, 4.8, 4.4, "glass", 0.9, flat=1)
    g.ell(8, 11.2, 4.2, 3.6, "brine", 1.0, flat=2)
    g.ell(7.4, 10.6, 2.4, 2.0, "brine", 1.01, flat=3)
    g.line(3.8, 9.4, 12.2, 9.4, "brine", 1.02, tone=3)
    g.poly([(6.6, 3.4), (9.4, 3.4), (9.4, 6.8), (6.6, 6.8)], "glass", 1.05, curve=0.8)
    g.poly([(6.4, 0.8), (9.6, 0.8), (9.2, 3.4), (6.8, 3.4)], "cork", 1.1, curve=0.8)
    g.line(6.4, 4.2, 9.6, 4.2, "root", 1.15, tone=3)
    g.tube([(9.4, 4.4), (11.0, 5.2), (10.6, 6.6)], [0.4], "root", 1.15)
    # glass shine and bubbles
    g.line(4.6, 9.0, 5.0, 12.0, "white", 1.2, tone=3)
    g.dot(5.2, 8.0, "white", 4, 1.2)
    b = ((9.4, 12.0), (10.4, 10.6)) if not ph else ((9.8, 11.0), (8.8, 9.8))
    for (x, y) in b:
        g.dot(x, y, "brine", 4, 1.2)


@accent("white")
def jesters_bell(g, ph):
    # the point of a jester's cap curling up from the bell, a gold ball on its tip
    tail = [(9.0, 6.4), (10.8, 4.2), (10.4, 2.0), (8.2, 0.8), (5.8, 1.6)]
    g.tube(tail, [1.5, 1.3, 1.05, 0.85, 0.6], "crim", 1.0, bias=0.35)
    g.tube([(9.0, 6.4), (9.9, 5.3)], [1.6, 1.45], "blk", 1.01, bias=0.5)
    g.ell(5.2, 2.0, 1.1, 1.1, "gold", 1.1)
    # the bell: a gold sphere with its slot and the ball showing
    g.ell(8, 10.2, 5.4, 4.8, "gold", 1.2)
    g.poly([(3.4, 10.6), (12.6, 10.6), (12.6, 11.4), (3.4, 11.4)], "gold", 1.25, flat=1)
    g.ell(8, 12.8, 1.6, 1.1, "gold", 1.3, flat=0)
    g.dot(8, 12.6, "bronze", 2, 1.31)
    g.ell(8, 5.6, 1.4, 0.8, "gold", 1.22)
    if ph:
        g.glint(5.6, 7.6, big=True)
        for (x0, y0, x1, y1) in ((1.4, 7.6, 0.4, 7.0), (14.6, 7.6, 15.4, 7.0)):
            g.line(x0, y0, x1, y1, "white", 1.0, tone=3)
    else:
        g.dot(5.8, 8.0, "gold", 4, 1.3)


def jokers_wild(g, ph):
    # a fanned hand: two red-backed cards behind, the joker face up in front
    piv = (8, 15.4)
    for i, ang in enumerate((-34, -16)):
        g.poly(rot_pts([(4.6, 2.6), (11.4, 2.6), (11.4, 13.6), (4.6, 13.6)], ang, piv), "card", 0.8 + i * 0.05,
               normal=(-0.2, -0.3, 1.0), bias=-0.1)
        g.poly(rot_pts([(5.6, 3.6), (10.4, 3.6), (10.4, 12.6), (5.6, 12.6)], ang, piv), "crim", 0.81 + i * 0.05, flat=2)
        for (u, v) in ((7.0, 5.6), (9.0, 7.8), (7.0, 10.0)):
            c = rot_pts([(u, v)], ang, piv)[0]
            g.dot(c[0], c[1], "crim", 3, 0.82 + i * 0.05)
    ang = 6
    g.poly(rot_pts([(4.8, 2.2), (11.8, 2.2), (11.8, 13.8), (4.8, 13.8)], ang, piv), "card", 1.0, normal=(-0.2, -0.3, 1.0))
    c = rot_pts([(8.3, 7.8)], ang, piv)[0]
    g.poly([(c[0], c[1] - 3.2), (c[0] + 2.3, c[1]), (c[0], c[1] + 3.2), (c[0] - 2.3, c[1])], "crim", 1.1, flat=2)
    g.poly([(c[0], c[1] - 3.2), (c[0] + 2.3, c[1]), (c[0], c[1])], "crim", 1.11, flat=3)
    g.dot(c[0], c[1], "gold", 3, 1.12)
    a, b = rot_pts([(5.8, 3.4), (10.8, 12.6)], ang, piv)
    g.dot(a[0], a[1], "crim", 2, 1.2); g.dot(b[0], b[1], "crim", 2, 1.2)
    if ph:
        g.glint(c[0] + 2.6, c[1] - 3.8)


@accent("lilac")
def marionette_cross(g, ph):
    # strings first, then the crossed bars over them
    sw = 0.6 if ph else 0.0
    for (x0, y0, x1) in ((2.6, 3.0, 2.4), (13.4, 3.0, 13.6), (3.0, 12.6, 3.4), (13.0, 12.6, 12.6), (8.0, 8.0, 8.0)):
        g.line(x0, y0, x1 + sw, 15.6, "lilac", 0.5, tone=2)
    g.tube([(2.2, 2.2), (13.8, 13.4)], [1.1], "wood", 1.0)
    g.tube([(13.8, 2.2), (2.2, 13.4)], [1.1], "wood", 1.1)
    for (x, y) in ((2.2, 2.2), (13.8, 2.2), (2.2, 13.4), (13.8, 13.4)):
        g.ell(x, y, 0.9, 0.9, "gold", 1.2)
    g.ell(8, 7.8, 1.8, 1.8, "gold", 1.3)
    g.dot(7.4, 7.2, "gold", 4, 1.31)
    if ph:
        g.dot(8.0 + sw, 14.0, "lilac", 4, 0.6)
        g.glint(4.4, 4.2)


def box_die(g, x0, y0, w, h, d, face, pip, z, one="crim", top=None, pips=True):
    """A die seen from the front and a little above: front face w x h with its bottom-left at (x0, y0), the corners
    rounded off by a pixel. top: pips on the top face too. pips=False leaves the front face blank."""
    sk = d * 0.6
    c = 0.9
    g.poly([(x0 + w, y0 - c), (x0 + w + sk, y0 - d * 0.7 - c), (x0 + w + sk, y0 - h - d * 0.7 + c), (x0 + w, y0 - h + c)],
           "ivory", z - 0.02, flat=1)
    g.poly([(x0 + c, y0 - h), (x0 + w - c, y0 - h), (x0 + w + sk - c, y0 - h - d * 0.7), (x0 + sk + c, y0 - h - d * 0.7)],
           "ivory", z - 0.01, flat=3)
    g.poly([(x0, y0 - c), (x0 + c, y0), (x0 + w - c, y0), (x0 + w, y0 - c), (x0 + w, y0 - h + c), (x0 + w - c, y0 - h),
            (x0 + c, y0 - h), (x0, y0 - h + c)], "ivory", z, flat=2)
    g.line(x0 + c, y0 - h, x0 + w - c - 0.4, y0 - h, "ivory", z + 0.01, tone=4)
    cx, cy = x0 + w / 2.0, y0 - h / 2.0
    sx, sy = w * 0.27, h * 0.27
    for (u, v) in (J.PIPS[face] if pips else ()):
        if face == 1:
            g.ell(cx, cy, w * 0.17, h * 0.17, one, z + 0.02, flat=2)
            g.dot(cx - 0.4, cy - 0.4, one, 4, z + 0.03)
        else:
            g.ell(cx + u * sx, cy + v * sy, 0.7, 0.7, pip, z + 0.02, flat=1)
    if top:
        tcx, tcy = x0 + w / 2.0 + sk / 2.0, y0 - h - d * 0.35
        for (u, v) in J.PIPS[top]:
            g.dot(tcx + u * w * 0.24 + v * sk * 0.3, tcy + v * d * 0.25, pip, 1, z)
    return sk


def iso_die(g, cx, cy, s, top, left, right, z, pip="blk", one="crim"):
    """A die drawn as an isometric cube: (cx, cy) the near top corner's centre point, s the edge length.
    top/left/right: the number shown on each face."""
    k = 0.87 * s
    T = [(cx, cy - s * 0.5), (cx + k, cy), (cx, cy + s * 0.5), (cx - k, cy)]
    L = [(cx - k, cy), (cx, cy + s * 0.5), (cx, cy + s * 1.5), (cx - k, cy + s)]
    R = [(cx, cy + s * 0.5), (cx + k, cy), (cx + k, cy + s), (cx, cy + s * 1.5)]
    for pts, tone, n, dz in ((L, 2, left, 0.0), (R, 1, right, 0.01), (T, 3, top, 0.02)):
        g.poly(pts, "ivory", z + dz, flat=tone)
        o = pts[0]; u = ((pts[1][0] - o[0]), (pts[1][1] - o[1])); v = ((pts[3][0] - o[0]), (pts[3][1] - o[1]))
        for (a, b) in J.PIPS[n]:
            fa, fb = 0.5 + a * 0.27, 0.5 + b * 0.27
            px, py = o[0] + u[0] * fa + v[0] * fb, o[1] + u[1] * fa + v[1] * fb
            m = one if n == 1 else pip
            if n == 1:
                g.ell(px, py, 1.0, 0.8, m, z + dz + 0.01, flat=2)
            else:
                g.dot(px, py, m, 1, z + dz + 0.01)
    g.line(cx - k + 0.4, cy - 0.2, cx - 0.2, cy - s * 0.5 + 0.2, "ivory", z + 0.03, tone=4)


def lerp(a, b, t):
    return a + (b - a) * t


ICONS = [
    ("IconEmberVolley", "Ember Volley", ember_volley, "spell"),
    ("IconWaxSlick", "Wax Slick", wax_slick, "spell"),
    ("IconMarrowSpikes", "Marrow Spikes", marrow_spikes, "spell"),
    ("IconBoneBoomerang", "Bone Boomerang", bone_boomerang, "spell"),
    ("IconSporeBomb", "Spore Bomb", spore_bomb, "spell"),
    ("IconRootSnare", "Root Snare", root_snare, "spell"),
    ("IconShardNova", "Shard Nova", shard_nova, "spell"),
    ("IconShadowSwap", "Shadow Swap", shadow_swap, "spell"),
    ("IconSoulLantern", "Soul Lantern", soul_lantern, "spell"),
    ("IconBellToll", "Bell Toll", bell_toll, "spell"),
    ("IconUndertow", "Undertow", undertow, "spell"),
    ("IconRiptide", "Riptide Dash", riptide, "spell"),
    ("IconWildCardSpell", "Wild Card", wild_card, "spell"),
    ("IconLoadedDice", "Loaded Dice", loaded_dice, "spell"),
    ("IconPuppetStrings", "Puppet Strings", puppet_strings, "spell"),
    ("IconEmberHeart", "Ember Heart", ember_heart, "artifact"),
    ("IconVenomGland", "Venom Gland", venom_gland, "artifact"),
    ("IconRimeRing", "Rime Ring", rime_ring, "artifact"),
    ("IconLeechSeed", "Leech Seed", leech_seed, "artifact"),
    ("IconThornMail", "Thorn Mail", thorn_mail, "artifact"),
    ("IconSaintsWick", "Saint's Wick", saints_wick, "artifact"),
    ("IconLuckyDie", "Lucky Die", lucky_die, "artifact"),
    ("IconAshHourglass", "Hourglass of Ash", ash_hourglass, "artifact"),
    ("IconGlassMask", "Glass Mask", glass_mask, "artifact"),
    ("IconBarnacleShell", "Barnacle Shell", barnacle_shell, "artifact"),
    ("IconTidecaller", "Tidecaller Conch", tidecaller, "artifact"),
    ("IconBrineFlask", "Brine Flask", brine_flask, "artifact"),
    ("IconJestersBell", "Jester's Bell", jesters_bell, "artifact"),
    ("IconJokersWild", "Joker's Wild", jokers_wild, "artifact"),
    ("IconMarionetteCross", "Marionette Cross", marionette_cross, "artifact"),
]
DRAW = {sheet: fn for sheet, _, fn, _ in ICONS}


def render(fn, ph, S=1.0, sep=None):
    """One frame of an icon at scale S, in Crawl's palette -> (RGBA image of round(16 * S) px, pixels that fell outside)."""
    g = Pen(S)
    fn(g, ph)
    return g.image(sep=sep, remap=crawl_palette(getattr(fn, "accent", ())))


def to_spr(im):
    px = {}
    p = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if p[x, y][3]: px[(x - FEET[0], y - FEET[1])] = p[x, y][:3]
    return SprRGB(px)


def build(outdir=DEFAULT_OUT):
    os.makedirs(outdir, exist_ok=True)
    tiles = []
    for sheet, nice, fn, kind in ICONS:
        ims = []
        for ph in (0, 1):
            im, lost = render(fn, ph, sep=PARCH if kind == "spell" else None)
            if lost: print("WARNING %s frame %d: %d px outside the cell" % (sheet, ph, lost))
            ims.append(im)
        pack(sheet, [("Idle", [to_spr(i) for i in ims], [0.9, 0.25])], 16, 16, FEET, outdir, cols=2)
        tiles.append((sheet, nice, kind, ims))
        print("wrote", sheet)
    board(tiles, outdir)


def board(tiles, outdir, S=6):
    font = ImageFont.load_default(size=13)
    cols = 5
    tw, th = 16 * S * 2 + 3 * S + 70, 16 * S + 26
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new("RGBA", (cols * tw + 10, rows * th + 10), (28, 26, 32, 255))
    d = ImageDraw.Draw(im)
    for i, (sheet, nice, kind, frames) in enumerate(tiles):
        x0, y0 = 6 + (i % cols) * tw, 6 + (i // cols) * th
        for j, f in enumerate(frames):
            bg = PARCH if kind == "spell" else (40, 37, 46)
            d.rectangle([x0 + j * (16 * S + S), y0, x0 + j * (16 * S + S) + 16 * S - 1, y0 + 16 * S - 1], fill=bg + (255,))
            im.alpha_composite(f.resize((16 * S, 16 * S), Image.NEAREST), (x0 + j * (16 * S + S), y0))
        ax = x0 + 2 * (16 * S + S) + 4
        im.alpha_composite(frames[0], (ax, y0 + 4))
        im.alpha_composite(frames[0].resize((32, 32), Image.NEAREST), (ax + 20, y0 + 4))
        if kind == "spell":
            d.rectangle([ax, y0 + 44, ax + 21, y0 + 67], fill=PARCH + (255,))
            im.alpha_composite(frames[0], (ax + 3, y0 + 48))
        d.text((x0, y0 + 16 * S + 4), "%s  (%s)" % (nice, sheet[4:]), fill=(220, 210, 190, 255), font=font)
    im.convert("RGB").save(os.path.join(outdir, "board.png"))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
