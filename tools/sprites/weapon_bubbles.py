"""Shop bubbles (34x41, two frames) for the 25 mod weapons, drawn with the shared material renderer
(jinx_v2_rigs.Rig): three tones per material lit from the top left, bottom and right edges in the material's own
dark tones instead of an outline, stray pixels folded, emissive parts laid last.

    python3 tools/sprites/weapon_bubbles.py [outdir]      (default art/out_weapons; weapon_rigs.py also calls build())

Layout follows the vanilla shop portraits (AtlasProps shop_portraits_weapons_*): the weapon lies on the diagonal from
the grip at the bottom left to the tip at the top right. Frame 1 is the same weapon with its glints and glows moved on
(a travelling sheen on steel, a flicker on flames), not a brightened copy.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
from jinx_v2_rigs import Rig  # noqa: E402
from PIL import Image  # noqa: E402

BW, BH = 34, 41


def _ramps(d):
    return {k: [J._h(c) for c in v] for k, v in d.items()}


# (ink, shadow, base, light, highlight); keys are prefixed so they never clash with another rig's materials
RAMPS = _ramps({
    "w_wood":   ("1e120c", "432818", "6a4228", "8e6038", "b48650"),
    "w_dwood":  ("120c0a", "2a1a14", "44291c", "603c26", "805434"),   # dark stained haft
    "w_lthr":   ("140c0a", "2e1c16", "4c3022", "6a4630", "8c6444"),   # grip wraps
    "w_steel":  ("161820", "3a3e4c", "6a7080", "a2a8b6", "e2e6ee"),
    "w_iron":   ("121016", "2a2830", "4a4652", "6e6a76", "9c98a4"),
    "w_gold":   ("2a1808", "6a4414", "a8762a", "dcb04a", "fbe796"),
    "w_bronze": ("241608", "56361a", "8a5c28", "bc8a3e", "ecc272"),
    "w_bone":   ("34281e", "75644e", "b2a07e", "dccca6", "f8f0d8"),
    "w_moon":   ("1a2640", "34507a", "6890b8", "a6cce6", "eef8ff"),
    "w_void":   ("10061c", "2a1046", "4e2080", "7c3cb4", "b878e6"),
    "w_tide":   ("0a1e24", "14444a", "247070", "4ea89a", "a4e4d2"),
    "w_leaf":   ("101a0c", "203a16", "386222", "5e9030", "9cc85a"),
    "w_bark":   ("16100a", "302014", "4a3420", "664a2e", "866844"),
    "w_ice":    ("162638", "2e5678", "5c94bc", "9ccce8", "eefaff"),
    "w_blood":  ("24040c", "520a16", "8c1620", "c4302e", "f0705c"),
    "w_blue":   ("0e1430", "1c2e60", "30509a", "5280c8", "98c0ee"),
    "w_night":  ("0a0820", "181640", "2a2668", "403c94", "6c66c0"),
    "w_plague": ("14180a", "2c3614", "4c5c1e", "74882c", "aabc4c"),
    "w_obsid":  ("08080e", "16141e", "282434", "403a52", "6c6488"),
    "w_stone":  ("161214", "302628", "4e4244", "706262", "9a8c88"),
    "w_snake":  ("0c140a", "1c3016", "305022", "4c7432", "7aa050"),
    "w_belly":  ("2a2414", "5c5030", "8e7e4c", "b8a86a", "dcd09a"),
    "w_crim":   ("200610", "4e0e1c", "84182a", "b82e36", "e8665a"),
    "w_glass":  ("101a18", "22302c", "3c4c44", "5a6c60", "8a9a8c"),   # smoky lantern glass
    "w_cloth":  ("1a0c0c", "3e1616", "662424", "8c3a30", "b05a44"),   # pennant / tassel red
    # emissive (flat, no sel-out)
    "w_soul":   ("12302a", "1e5c4a", "3aa07a", "7ee8b4", "d8fff0"),
    "w_volt":   ("101c4a", "2a4ab0", "4a8cf0", "a8d8ff", "ffffff"),
    "w_rift":   ("3a1a5a", "8a3ab8", "d070f0", "f4b8ff", "ffffff"),
    "w_frost":  ("2a5a7a", "5aa0cc", "a0dcf4", "dcf6ff", "ffffff"),
    "w_spark":  ("6a4a10", "c08a20", "f6d260", "fff2b0", "ffffff"),
    "w_blight": ("2e3a08", "5e7a12", "a0c628", "d8f060", "f8ffc8"),
    "w_heart":  ("4a0a14", "a01a2a", "f03a48", "ff8a8a", "ffe0e0"),
    "w_fire":   ("5a1a0a", "b8401a", "f07a24", "ffc04a", "fff0b0"),
    "w_star":   ("4a3a6a", "8a7ac8", "c8c0f4", "f0ecff", "ffffff"),
    "w_shine":  ("8a8a90", "c8ccd4", "e8ecf2", "f6f8fc", "ffffff"),
})
EMIT = {"w_soul", "w_volt", "w_rift", "w_frost", "w_spark", "w_blight", "w_heart", "w_fire", "w_star", "w_shine"}


# Crawl's own palette is muted and grimy: worn wood, dull iron, dusty cloth. Every material ramp is pulled towards a
# warm grey of the same brightness until its colourfulness (max - min channel) is at most its cap, so a weapon reads
# in the game's range and only its magic (the emissive ramps, kept small on the sprite) stands out.
DUSTY = (1.04, 1.0, 0.92)                        # the grey every colour is pulled towards: a little warm
CAP = {"metal": 0.07, "earth": 0.20, "brass": 0.30, "cloth": 0.22, "accent": 0.62}
S_CAP = 0.58                                     # and its saturation (max - min) / max, which dark tones push up
KIND = {
    "w_steel": "metal", "w_iron": "metal", "w_obsid": "metal", "w_moon": "metal", "w_ice": "metal", "w_stone": "metal",
    "w_wood": "earth", "w_glass": "metal", "w_dwood": "earth", "w_lthr": "earth", "w_bark": "earth", "w_bone": "earth", "w_belly": "earth",
    "w_gold": "brass", "w_bronze": "brass",
    "w_void": "cloth", "w_tide": "cloth", "w_leaf": "cloth", "w_blood": "cloth", "w_blue": "cloth", "w_night": "cloth",
    "w_plague": "cloth", "w_snake": "cloth", "w_crim": "cloth", "w_cloth": "cloth",
}


def tame(c, cap, s_cap=S_CAP):
    """Pull c towards a warm grey of the same brightness until max - min <= cap * 255 and (max - min) / max <= s_cap."""
    r, g, b = c
    y = 0.3 * r + 0.59 * g + 0.11 * b
    grey = tuple(min(255.0, y * k) for k in DUSTY)
    over = lambda m: (max(m) - min(m)) / 255.0 > cap or (max(m) - min(m)) / max(1.0, max(m)) > s_cap
    if not over(c): return c
    lo, hi = 0.0, 1.0
    for _ in range(20):                          # bisect the blend that brings it inside both caps
        t = (lo + hi) / 2
        m = tuple(grey[i] + (c[i] - grey[i]) * t for i in range(3))
        if over(m): hi = t
        else: lo = t
    return tuple(int(round(grey[i] + (c[i] - grey[i]) * lo)) for i in range(3))


for _k, _r in RAMPS.items():
    _cap = CAP["accent" if _k in EMIT else KIND[_k]]
    RAMPS[_k] = [tame(c, _cap, 0.9 if _k in EMIT else S_CAP) for c in _r]
SHINY = {"w_steel", "w_gold", "w_bronze", "w_moon", "w_void", "w_tide", "w_ice", "w_blood", "w_obsid", "w_bone"}
J.RAMPS.update(RAMPS)
J.EMISSIVE.update(EMIT)
J.SHINY.update(SHINY)


# ------------------------------------------------------------------ the diagonal frame
class Dg:
    """u runs from the grip end (bottom left) to the tip (top right); v is across it, + towards the upper left
    (the lit side)."""

    def __init__(self, x0=6.0, y0=37.0, x1=29.0, y1=4.0):
        self.x0, self.y0 = x0, y0
        L = math.hypot(x1 - x0, y1 - y0)
        self.ax, self.ay = (x1 - x0) / L, (y1 - y0) / L
        self.px, self.py = self.ay, -self.ax
        self.L = L

    def to(self, u, v=0.0):
        return (self.x0 + self.ax * u + self.px * v, self.y0 + self.ay * u + self.py * v)

    def n_up(self, k=0.6):
        """Normal of a face tilted towards the lit side (k = how far it turns)."""
        return (self.px * k, self.py * k, 1.0 - k * 0.4)

    def n_down(self, k=0.6):
        return (-self.px * k, -self.py * k, 1.0 - k * 0.4)


def shaft(r, d, u0, u1, rad, mat, z, bias=0.0):
    return r.tube([d.to(u0), d.to(u1)], [rad, rad], mat, z, bias)


def wraps(r, d, u0, u1, step, rad, mat, z, tone=1):
    """Diagonal bands round a shaft (grip wrapping)."""
    p = r.part(True, z)
    u = u0
    while u <= u1:
        a, b = d.to(u, rad), d.to(u + 1.2, -rad)
        r.line(a[0], a[1], b[0], b[1], mat, z, tone, part=p)
        u += step


def blade(r, d, u0, u1, top, bot, mat, z, spine=None, k=0.65, n=24, bias=0.0):
    """A bevelled blade between u0 and u1: top(t) / bot(t) give the v of each edge at t in [0, 1]; the upper half
    faces the light, the lower half turns away, so the spine reads as a ridge."""
    sp = spine or (lambda t: 0.0)
    ts = [i / float(n) for i in range(n + 1)]
    U = lambda t: u0 + (u1 - u0) * t
    up = [d.to(U(t), top(t)) for t in ts] + [d.to(U(t), sp(t)) for t in reversed(ts)]
    dn = [d.to(U(t), sp(t)) for t in ts] + [d.to(U(t), bot(t)) for t in reversed(ts)]
    p1 = r.poly(up, mat, z, bias, normal=d.n_up(k))
    p2 = r.poly(dn, mat, z + 0.01, bias, normal=d.n_down(k * 0.7))
    return p1, p2


def uvpoly(r, d, pts, mat, z, normal=(0.0, 0.0, 1.0), bias=0.0, thin=False):
    return r.poly([d.to(u, v) for u, v in pts], mat, z, bias, normal=normal, thin=thin)


def gem(r, x, y, rad, mat, z, glow=None):
    r.ell(x, y, rad, rad, mat, z, bias=0.15)
    if glow:
        r.dot(x - 0.6, y - 0.6, glow, 4, z + 0.1)


def sparkle(r, x, y, size, mat="w_shine", z=9.0):
    """A four-point glint: a bright core and arms that fade."""
    r.dot(x, y, mat, 4, z)
    for k in range(1, size + 1):
        t = 3 if k == 1 else 2
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            r.dot(x + dx, y + dy, mat, t, z)


def sheen(r, d, u_at, half, v_lo, v_hi, mats, z=8.0, step=0.5):
    """A travelling highlight band across a blade (frame 1): lifts the matching pixels to the highlight tone."""
    hits = set()
    u = u_at - half
    while u <= u_at + half:
        v = v_lo
        while v <= v_hi:
            x, y = d.to(u, v)
            hits.add((int(math.floor(x + 0.5)), int(math.floor(y + 0.5))))
            v += step
        u += step
    for k in hits:
        c = r.b.get(k)
        if c and c[1] in mats:
            c[4] = 4 if c[2] > 0.25 else 3


def render(r):
    s = r.resolve(selout=True, cast=True, contour=True, clean=True, floor=False)
    im = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    p = im.load()
    for (x, y), c in s.px.items():
        if 0 <= x < BW and 0 <= y < BH:
            p[x, y] = tuple(c[:3]) + (255,)
    return im


# ------------------------------------------------------------------ the 25 weapons
def gravehook(f):
    """Iron-shod harpoon spear: chain wound on a dark haft, a rusted barbed hook head, links hanging off the collar."""
    r, d = Rig(), Dg(5, 38, 29, 3)
    shaft(r, d, 0, 30, 1.2, "w_dwood", 1)
    for i in range(7):
        u = 9 + i * 2.2
        r.ell(*d.to(u, 0), 1.6, 1.0, "w_iron", 2, ang=-55 if i % 2 else 35)
    r.tube([d.to(29, 0), d.to(31.5, 0)], [2.0, 2.0], "w_iron", 3)
    blade(r, d, 31, 43, lambda t: 3.0 * (1 - t) ** 0.7, lambda t: -3.0 * (1 - t) ** 0.7, "w_steel", 4)
    # the hook: a long barb curling back down the lit side, a short one on the shadow side
    hook = [(37, 1.6), (35, 4.4), (32.4, 6.6), (29.6, 7.0), (28.6, 6.2), (30.4, 5.6), (32.4, 4.4), (34.0, 1.6)]
    uvpoly(r, d, hook, "w_steel", 5, d.n_up(0.5))
    uvpoly(r, d, [(36, -1.6), (33.4, -4.6), (32.2, -4.6), (34.0, -1.4)], "w_steel", 5, d.n_down(0.4))
    r.dot(*d.to(29.4, 6.4), "w_blood", 3, 5.5)
    r.dot(*d.to(30.4, 6.4), "w_blood", 2, 5.5)
    # chain links hanging from the collar
    x, y = d.to(29.5, -2.2)
    for k in range(5):
        r.ell(x + 0.3 * k, y + 1.6 * k + 1, 0.9, 1.1, "w_iron", 6, flat=3 if k % 2 == 0 else 2)
    if f == 0:
        sparkle(r, *[int(round(c)) for c in d.to(40, 0.6)], 1)
    else:
        sheen(r, d, 35, 1.2, -3, 3, {"w_steel"})
        sparkle(r, *[int(round(c)) for c in d.to(29.0, 7.6)], 1)
    return r


def moonglaive(f):
    """A four-horned crescent ring of pale moon-steel with a wrapped grip across its eye."""
    r = Rig()
    cx, cy = 17.0, 21.0
    spin = 0.0 if f == 0 else 9.0
    for y in range(BH):
        for x in range(BW):
            dx, dy = x - cx, y - cy
            rr = math.hypot(dx, dy)
            ang = math.degrees(math.atan2(dy, dx)) + spin
            ph = ((ang + 180.0) % 90.0) / 90.0
            outer = 9.6 + 4.6 * ph ** 2.4
            inner = 6.4 + 0.8 * ph
            if inner <= rr <= outer:
                nx, ny = dx / max(rr, 0.1), dy / max(rr, 0.1)
                mid = (inner + outer) / 2
                s = (rr - mid) / max(1.0, (outer - inner) / 2)
                l = J.lam(nx * s * 0.8, ny * s * 0.8, 0.7) + 0.18
                r.put(x, y, 2.0, "w_moon", l, 1)
    # grip across the eye, leather wrapped, with steel ferrules
    a, b = (cx - 6, cy + 3), (cx + 6, cy - 3)
    r.tube([a, b], [1.3, 1.3], "w_lthr", 3)
    for t in (0.3, 0.5, 0.7):
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        r.line(x - 0.6, y - 1.2, x + 0.6, y + 1.2, "w_lthr", 3.5, 1)
    r.ell(a[0] + 0.6, a[1] - 0.3, 1.6, 1.6, "w_steel", 3.6)
    r.ell(b[0] - 0.6, b[1] + 0.3, 1.6, 1.6, "w_steel", 3.6)
    pts = [(cx - 9, cy - 10), (cx + 12, cy - 6), (cx + 3, cy + 12)] if f == 0 else [(cx + 11, cy + 7), (cx - 11, cy + 4), (cx - 2, cy - 12)]
    for i, (x, y) in enumerate(pts):
        sparkle(r, int(x), int(y), 1 if i else 2, "w_frost")
    return r


def riftblade(f):
    """A violet void-steel arming sword split down its length by a glowing rift; runes leak light."""
    r, d = Rig(), Dg(7, 38, 29, 3)
    r.ell(*d.to(0.6), 1.9, 1.9, "w_steel", 2)
    shaft(r, d, 1.5, 7.5, 1.1, "w_lthr", 1)
    wraps(r, d, 2, 7, 1.6, 1.1, "w_lthr", 1.5)
    uvpoly(r, d, [(7.5, 4.6), (9.4, 4.0), (9.4, -4.0), (7.5, -4.6), (7.0, 0)], "w_steel", 3, d.n_up(0.3))
    gem(r, *d.to(8.4, 0), 1.0, "w_rift", 3.5)
    blade(r, d, 9.4, 41, lambda t: 2.7 - 0.5 * t if t < 0.86 else (1 - t) / 0.14 * 2.3,
          lambda t: -2.7 + 0.5 * t if t < 0.86 else -(1 - t) / 0.14 * 2.3, "w_void", 2)
    # the rift: a jagged crack along the spine
    p = r.part(True, 4)
    for i in range(30):
        u = 11 + i
        v = 0.6 * math.sin(i * 1.7) * (1 if i % 3 else -1)
        x, y = d.to(u, v)
        if u < 38:
            r.put(x, y, 4, "w_rift", 0.6, p, 3 if (i + f * 2) % 5 else 4)
            if i % 2 == 0 and u < 35:
                x2, y2 = d.to(u + 0.5, v - 0.9)
                r.put(x2, y2, 4, "w_rift", 0.6, p, 2)
    for i, u in enumerate((14, 21, 28, 34)):
        x, y = d.to(u, 3.6 if i % 2 else -3.6)
        r.dot(x, y, "w_rift", 3 if (i + f) % 2 else 2, 6)
    if f == 1:
        sparkle(r, *[int(round(c)) for c in d.to(41, 0)], 2, "w_rift")
    return r


def snakeeyes(f):
    """A bone-ivory die, iron-strapped onto a club: two red pips stare out of the front face."""
    r, d = Rig(), Dg(6, 39, 22, 16)
    shaft(r, d, 0, 22, 1.4, "w_wood", 1)
    wraps(r, d, 1, 8, 1.8, 1.4, "w_lthr", 1.5)
    r.ell(*d.to(0.4), 2.0, 2.0, "w_iron", 1.6)
    # the die, drawn as a real cube (three lit faces)
    J.die3(r, 22.0, 12.0, 13.0, rx=-8.0, ry=34.0, rz=-6.0, z=4.0, mat="w_bone", pip="w_obsid",
           one="w_crim", tilt=24.0)
    # iron straps where the die sits on the haft
    x, y = d.to(22.5)
    r.tube([(x - 3.5, y + 1.5), (x + 2.0, y - 3.0)], [1.0, 1.0], "w_iron", 5)
    for (sx, sy) in ((x - 3.0, y + 1.0), (x + 1.4, y - 2.6)):
        r.dot(sx, sy, "w_steel", 4, 5.2)
    sparkle(r, 12 if f == 0 else 29, 6 if f == 0 else 16, 1, "w_heart")
    return r


def tidebreaker(f):
    """A greatsword whose blade is a cresting wave of sea-green steel, foam along its edge, bronze guard."""
    r, d = Rig(), Dg(5, 39, 30, 2)
    r.ell(*d.to(0.6), 2.0, 2.0, "w_bronze", 2)
    shaft(r, d, 1.5, 9.5, 1.2, "w_lthr", 1)
    wraps(r, d, 2, 9, 1.6, 1.2, "w_lthr", 1.5)
    uvpoly(r, d, [(9.5, 5.4), (11.2, 4.6), (11.6, 0), (11.2, -4.6), (9.5, -5.4), (10.2, 0)], "w_bronze", 3, d.n_up(0.3))
    gem(r, *d.to(10.6, 0), 1.0, "w_tide", 3.5)
    wav = lambda t: 1.1 * math.sin(t * 9.0)
    top = lambda t: (3.4 - 0.9 * t + wav(t)) * (1 if t < 0.88 else (1 - t) / 0.12)
    bot = lambda t: (-2.8 + 0.6 * t + wav(t) * 0.5) * (1 if t < 0.88 else (1 - t) / 0.12)
    blade(r, d, 11.6, 44, top, bot, "w_tide", 2, spine=lambda t: wav(t) * 0.7)
    p = r.part(True, 5)
    for i in range(80):
        t = i / 79.0
        if t > 0.9: break
        u = 11.6 + 32.4 * t
        x, y = d.to(u, top(t) - 0.2)
        r.put(x, y, 5, "w_frost", 0.6, p, 4 if (i // 6 + f) % 3 == 0 else 3)
    for i, t in enumerate((0.2, 0.45, 0.7)):
        x, y = d.to(11.6 + 32.4 * t, top(t) + 1.3)
        r.dot(x, y, "w_frost", 3 if (i + f) % 2 else 2, 6)
    if f == 1: sheen(r, d, 30, 1.2, -3, 4, {"w_tide"})
    return r


def leechfang(f):
    """A curved blood-red fang of a dagger with a bone guard; a drop of blood runs from the fuller."""
    r, d = Rig(), Dg(9, 37, 26, 8)
    r.ell(*d.to(0.4), 1.9, 1.9, "w_bone", 2)
    shaft(r, d, 1.4, 9, 1.3, "w_crim", 1)
    wraps(r, d, 2, 8.5, 1.5, 1.3, "w_crim", 1.5, 1)
    uvpoly(r, d, [(9, 4.4), (10.6, 3.8), (11.0, 0), (10.6, -3.4), (9, -4.0)], "w_bone", 3, d.n_up(0.3))
    bend = lambda t: (t * 4.0) ** 2 * 0.22
    blade(r, d, 11.0, 35, lambda t: (2.4 - 0.4 * t) * (1 if t < 0.8 else (1 - t) / 0.2) + bend(t),
          lambda t: (-2.6 + 1.2 * t) * (1 if t < 0.85 else (1 - t) / 0.15) + bend(t) * 0.8, "w_steel", 2,
          spine=lambda t: bend(t) * 0.9 - 0.4)
    # blood groove + edge stain
    p = r.part(True, 4)
    for i in range(17):
        t = i / 22.0
        x, y = d.to(12 + 23 * t, bend(t) * 0.9 - 0.6)
        r.put(x, y, 4, "w_blood", 0.5, p, 2 if i % 3 else 3)
    drop = 2 if f == 0 else 4
    x, y = d.to(23, -2.2)
    for k in range(drop):
        r.dot(x + 0.2 * k, y + 1 + k, "w_blood", 3 if k < drop - 1 else 4, 6)
    sparkle(r, *[int(round(c)) for c in d.to(31 if f == 0 else 20, bend(0.8) + 1.4)], 1)
    return r


def briarbow(f):
    """A living longbow of green wood, thorns along the back of the limbs, leaves at the tips, a thorn arrow nocked."""
    r = Rig()
    pts = []
    for i in range(29):
        t = i / 28.0
        x = 28 - 21 * t - math.sin(t * math.pi) * 8.5
        y = 3 + 34 * t - math.sin(t * math.pi) * 2.5
        pts.append((x, y))
    rad = [1.0 + 0.9 * math.sin(i / 28.0 * math.pi) for i in range(29)]
    r.tube(pts, rad, "w_bark", 2)
    for i in range(3, 26, 4):
        x, y = pts[i]
        r.tube([(x - 0.8, y), (x - 2.8, y - 1.6)], [0.8, 0.3], "w_bone", 2.5)
    r.tube([pts[13], pts[15]], [2.4, 2.4], "w_lthr", 3)
    for i, (x, y, a) in enumerate(((pts[1][0] + 1, pts[1][1] - 1, 30), (pts[27][0] - 1.5, pts[27][1] + 0.5, -40),
                                   (pts[8][0] - 2.5, pts[8][1] + 0.5, 70), (pts[20][0] - 2.4, pts[20][1], -60))):
        r.ell(x, y, 2.6, 1.2, "w_leaf", 3, ang=a + (8 if f else 0))
    r.line(pts[0][0] + 0.5, pts[0][1] + 0.5, pts[-1][0] + 1.0, pts[-1][1], "w_bone", 1.5, 3)
    # thorn arrow across the bow
    ax, ay = pts[14][0] + 1, pts[14][1] + 0.5
    r.tube([(ax - 2, ay + 2.5), (31, 11)], [0.6, 0.6], "w_wood", 4)
    r.poly([(31.5, 10.5), (28.5, 10.5), (30.8, 13.2)], "w_leaf", 4.5, normal=(-0.3, -0.4, 0.8))
    r.ell(ax - 2.5, ay + 3, 1.6, 0.9, "w_leaf", 4.2, ang=-30)
    r.dot(32, 9 if f == 0 else 10, "w_blight", 4, 7)
    r.dot(31, 10, "w_blight", 3, 7)
    return r


def dirgemaul(f):
    """A war maul whose head is a cast bronze bell, verdigris ringed, the clapper showing; the bell is ringing."""
    r, d = Rig(), Dg(8, 39, 21, 16)
    shaft(r, d, 0, 24, 1.4, "w_dwood", 1)
    wraps(r, d, 1, 9, 1.8, 1.4, "w_lthr", 1.5)
    r.ell(*d.to(0.5), 2.0, 2.0, "w_iron", 1.6)
    x, y = d.to(24)
    sway = 0.0 if f == 0 else 1.0
    bx, top = x + 1.0, y - 16.0
    # bell profile, crown to lip: a rounded crown, a waisted waist, then the flare to a thick lip
    prof = [2.4, 3.8, 4.4, 4.6, 4.6, 4.6, 4.7, 4.9, 5.2, 5.6, 6.1, 6.8, 7.6, 8.4, 8.8, 8.6]
    n = len(prof)
    left = [(bx - h + sway * k / n, top + k) for k, h in enumerate(prof)]
    right = [(bx + h + sway * k / n, top + k) for k, h in enumerate(prof)]
    r.poly(left + right[::-1], "w_bronze", 3, normal=(0, -0.15, 1), curve=0.95)
    for k in (4, 12):
        r.line(bx - prof[k] + 0.8 + sway * k / n, top + k, bx + prof[k] - 0.8 + sway * k / n, top + k, "w_bronze", 3.5, 1)
    r.line(bx - prof[13] + 0.6 + sway, top + 13, bx + prof[13] - 0.8 + sway, top + 13, "w_bronze", 3.5, 4)
    r.ell(bx, top - 1.0, 1.6, 1.4, "w_bronze", 2.8)
    r.ell(bx + sway * 2.5, top + n + 0.4, 1.6, 1.5, "w_iron", 3.6)
    for (vx, vy) in ((-2, 6), (2, 9), (-4, 11), (3, 3), (5, 11)):
        r.dot(bx + vx + sway * vy / n, top + vy, "w_tide", 3, 3.6)
    for k in range(3):
        o = 1 if f else 0
        r.dot(bx - 11 - k - o, top + 3 + k * 4, "w_spark", 3, 8)
        r.dot(bx + 11 + k + o, top + 2 + k * 4, "w_spark", 2 + (k == 0), 8)
        r.dot(bx - 12 - k - o, top + 4 + k * 4, "w_spark", 2, 8)
    return r


def wickstaff(f):
    """A crook staff with an iron lantern hanging from its hook, soul-green flame inside, wisps rising."""
    r, d = Rig(), Dg(5, 39, 20, 10)
    shaft(r, d, 0, 30, 1.2, "w_wood", 1)
    r.ell(*d.to(0.5), 1.7, 1.7, "w_iron", 1.5)
    tx, ty = d.to(30)
    r.tube([(tx, ty), (tx + 1, ty - 4), (tx + 4, ty - 6.5), (tx + 7.5, ty - 6), (tx + 9, ty - 3.5)], [1.3, 1.2, 1.1, 1.0, 0.9],
           "w_iron", 2)
    lx, ly = tx + 9, ty + 7
    r.line(tx + 9, ty - 3.5, lx, ly - 7, "w_iron", 2.5, 2)
    r.ell(lx, ly - 7.5, 1.2, 1.0, "w_iron", 2.6, flat=3)
    # lantern: a peaked cap, four soul-lit glass panes in an iron cage, a base
    r.poly([(lx - 1.5, ly - 7), (lx + 1.5, ly - 7), (lx + 4.5, ly - 4), (lx - 4.5, ly - 4)], "w_iron", 3, normal=(0, -0.7, 0.7))
    r.poly([(lx - 4.5, ly + 5), (lx + 4.5, ly + 5), (lx + 3.5, ly + 7), (lx - 3.5, ly + 7)], "w_iron", 3, normal=(0, 0.3, 0.9))
    for yy in range(int(ly - 3), int(ly + 5)):
        for xx in range(int(lx - 3), int(lx + 4)):
            dx, dy = xx - lx, yy - (ly + 1.0)
            core = dx * dx * 1.4 + dy * dy * 0.5
            if core < 3.0 + f:
                r.put(xx, yy, 3.0, "w_soul", 0.5, r.part(True, 3.0), 4 if core < 1.2 + f else 3)
            else:
                r.put(xx, yy, 3.0, "w_glass", 0.5, r.part(True, 3.0), 2 if core < 7 else 1)
    for xx, tone in ((lx - 4, 3), (lx + 4, 1), (lx, 2)):
        r.line(xx, ly - 4, xx, ly + 5, "w_iron", 3.3, tone)
    r.line(lx - 4, ly + 1, lx + 4, ly + 1, "w_iron", 3.3, 2)
    for i, (wx, wy) in enumerate(((lx - 6, ly - 10), (lx + 5, ly - 13), (lx, ly - 17))):
        o = -2 if f else 0
        r.dot(wx + (1 if f and i == 1 else 0), wy + o, "w_soul", 3, 8)
        r.dot(wx + (1 if i % 2 else -1), wy + 1 + o, "w_soul", 2, 8)
    return r


def arcbolt(f):
    """A steel-bound crossbow with a storm crystal at the nut; lightning crawls along its string to the bolt."""
    r, d = Rig(), Dg(5, 36, 29, 6)
    uvpoly(r, d, [(0, -3.2), (0, 1.6), (6, 1.6), (9, 1.2), (28, 1.2), (28, -1.6), (9, -1.6), (6, -3.6)], "w_wood", 1,
           d.n_up(0.2))
    for u in (7.5, 15, 24):
        uvpoly(r, d, [(u, 1.6), (u + 1.2, 1.6), (u + 1.2, -1.9), (u, -1.9)], "w_iron", 1.5, d.n_up(0.3))
    gem(r, *d.to(12, 0), 1.5, "w_volt", 2.5)
    # the prod: a steel bow across the front, swept back
    fx, fy = d.to(23)
    prod = []
    for k in range(-12, 13):
        bend = (abs(k) / 12.0) ** 1.6 * 3.6
        prod.append((fx + d.px * k - d.ax * bend, fy + d.py * k - d.ay * bend))
    r.tube(prod, [1.0] * len(prod), "w_steel", 3)
    sx, sy = d.to(12)
    for end in (prod[0], prod[-1]):
        pts = []
        for i in range(9):
            t = i / 8.0
            j = (0.0 if i in (0, 8) else (0.8 if (i + f) % 2 else -0.8))
            pts.append((end[0] + (sx - end[0]) * t + d.ax * j, end[1] + (sy - end[1]) * t + d.ay * j))
        r.polyline(pts, "w_bone", 6, 2)
        for i in ((2, 5) if f == 0 else (3, 6)):
            r.dot(pts[i][0], pts[i][1], "w_volt", 3, 6.1)
    # the bolt, crackling at the head
    r.tube([d.to(12), d.to(31)], [0.6, 0.6], "w_iron", 5)
    uvpoly(r, d, [(31, 1.6), (35, 0), (31, -1.6)], "w_volt", 5.5)
    tx, ty = d.to(35)
    for (x, y) in (((tx + 1, ty - 2), (tx + 2, ty + 1), (tx - 1, ty - 3)) if f == 0 else ((tx + 2, ty - 1), (tx, ty + 2), (tx + 1, ty - 3))):
        r.dot(x, y, "w_spark", 4, 8)
    return r


def frostbrand(f):
    """An arming sword grown over with ice: a frost-steel blade, crystals bristling from its edge, a rime guard."""
    r, d = Rig(), Dg(7, 38, 29, 3)
    r.ell(*d.to(0.6), 2.0, 2.0, "w_ice", 2)
    shaft(r, d, 1.5, 8, 1.1, "w_blue", 1)
    wraps(r, d, 2, 7.5, 1.6, 1.1, "w_blue", 1.5)
    uvpoly(r, d, [(8, 3.2), (8.8, 5.6), (10, 4.0), (10, -4.0), (8.8, -5.6), (8, -3.2)], "w_ice", 3, d.n_up(0.3))
    blade(r, d, 10, 41, lambda t: 2.5 - 0.3 * t if t < 0.85 else (1 - t) / 0.15 * 2.2,
          lambda t: -2.5 + 0.3 * t if t < 0.85 else -(1 - t) / 0.15 * 2.2, "w_ice", 2)
    for i, (u, s, h) in enumerate(((15, 1, 3.2), (19, -1, 2.6), (24, 1, 3.6), (28, -1, 2.4), (33, 1, 2.6))):
        base = 2.4 * s
        uvpoly(r, d, [(u - 1.0, base), (u + 0.6, base + h * s), (u + 1.2, base)], "w_ice", 3.5,
               d.n_up(0.5) if s > 0 else d.n_down(0.5))
    for i, u in enumerate((13, 22, 31)):
        x, y = d.to(u + (2 if f else 0), 0.6)
        r.dot(x, y, "w_frost", 4, 6)
    sparkle(r, *[int(round(c)) for c in (d.to(36, 4) if f == 0 else d.to(18, -5))], 1, "w_frost")
    return r


def mercyblade(f):
    """A broad, square-tipped executioner's sword: pale steel, a black fuller with a gold mercy inscription."""
    r, d = Rig(), Dg(7, 38, 28, 4)
    r.ell(*d.to(0.6), 2.1, 2.1, "w_gold", 2)
    shaft(r, d, 1.6, 8.5, 1.2, "w_lthr", 1)
    wraps(r, d, 2, 8, 1.6, 1.2, "w_lthr", 1.5)
    uvpoly(r, d, [(8.5, 5.0), (10.2, 4.4), (10.2, -4.4), (8.5, -5.0)], "w_gold", 3, d.n_up(0.3))
    blade(r, d, 10.2, 38.5, lambda t: 3.6 if t < 0.94 else 3.6 - (t - 0.94) / 0.06 * 1.4,
          lambda t: -3.6 if t < 0.97 else -3.6 + (t - 0.97) / 0.03 * 3, "w_steel", 2)
    uvpoly(r, d, [(11.5, 0.9), (33, 0.9), (33, -0.9), (11.5, -0.9)], "w_obsid", 3, (0, 0, 1))
    p = r.part(True, 4)
    for i in range(6):
        x, y = d.to(13.5 + i * 3.4, 0)
        r.put(x, y, 4, "w_gold", 0.6, p, 3 if (i + f) % 3 else 4)
    if f == 0: sparkle(r, *[int(round(c)) for c in d.to(37, 3.0)], 2)
    else: sheen(r, d, 26, 1.0, -3.6, 3.6, {"w_steel"})
    return r


def reaper(f):
    """A war scythe: a long black haft, a wide hooked blade with a bone-white edge, a soul flickering on the tang."""
    r, d = Rig(), Dg(10, 39, 25, 6)
    shaft(r, d, 0, 32, 1.2, "w_dwood", 1)
    r.tube([d.to(12, 0), d.to(12.5, 4.0)], [0.9, 0.8], "w_dwood", 1.2)
    r.ell(*d.to(0.5), 1.8, 1.8, "w_iron", 1.5)
    tx, ty = d.to(31)
    r.tube([(tx - 1.2, ty + 1.6), (tx + 1.6, ty - 1.8)], [1.8, 1.8], "w_iron", 2)
    # the blade leaves the head to the left and curves down: the outer (top) edge is the long cutting arc
    outer, inner = [], []
    for i in range(25):
        t = i / 24.0
        ox = tx + 1.0 - 26.0 * t
        oy = ty - 2.5 - 4.0 * math.sin(t * math.pi * 0.85) + 9.0 * t * t
        w = 0.6 + 4.6 * math.sin(min(1.0, (1 - t) * 1.25) * math.pi * 0.5) * (0.35 + 0.65 * t ** 0.3)
        outer.append((ox, oy))
        inner.append((ox + 0.6 * t, oy + w))
    r.poly(outer + inner[::-1], "w_steel", 3, normal=(-0.2, -0.45, 0.87))
    p = r.part(True, 4)
    for i, (x, y) in enumerate(outer[1:-1]):
        r.put(x, y, 4, "w_bone", 0.8, p, 4 if (i + f * 4) % 9 == 0 else 3)
    sx, sy = d.to(29, 2.4)
    for (ox, oy, t) in ((0, 0, 4), (0, -1, 3), (-1, -2, 2), (1, -2, 3), (0, -3, 2)):
        r.dot(sx + ox + (1 if f and oy < -1 else 0), sy + oy, "w_soul", t, 6)
    if f: sparkle(r, int(outer[12][0]), int(outer[12][1]) - 1, 1)
    return r


def starfall(f):
    """A meteor maul: a cratered night-iron head on a heavy haft, stars caught in its face, a gold band."""
    r, d = Rig(), Dg(7, 39, 22, 14)
    shaft(r, d, 0, 25, 1.5, "w_dwood", 1)
    wraps(r, d, 1, 9, 1.8, 1.5, "w_lthr", 1.5)
    r.ell(*d.to(0.5), 2.0, 2.0, "w_gold", 1.6)
    hx, hy = d.to(28)
    r.ell(hx, hy, 9.0, 8.0, "w_night", 2, bias=0.05)
    for (cx, cy, cr) in ((-3, -2, 2.2), (3, 2, 1.8), (-1, 4, 1.4), (4, -4, 1.4)):
        r.ell(hx + cx, hy + cy, cr, cr * 0.8, "w_night", 2.2, bias=-0.5)
    r.tube([(hx - 8, hy + 3), (hx + 3, hy + 8)], [1.2, 1.2], "w_gold", 3)
    stars = [(-5, -4), (2, -5), (5, 0), (-2, 1), (1, 5)]
    for i, (sx, sy) in enumerate(stars):
        r.dot(hx + sx, hy + sy, "w_star", 4 if (i + f) % 2 == 0 else 3, 4)
    sparkle(r, int(hx + (7 if f == 0 else -8)), int(hy - (8 if f == 0 else 6)), 2, "w_star")
    return r


def hydrabow(f):
    """A recurve bow of green scale with three snake heads at the grip; the arrow in it has three fanged tips."""
    r = Rig()
    pts = []
    for i in range(29):
        t = i / 28.0
        x = 27 - 20 * t - math.sin(t * math.pi) * 9
        y = 4 + 32 * t - math.sin(t * math.pi) * 2.0
        if t < 0.1: x += (0.1 - t) * 30
        if t > 0.9: y += (t - 0.9) * 20
        pts.append((x, y))
    r.tube(pts, [0.9 + 1.0 * math.sin(i / 28.0 * math.pi) for i in range(29)], "w_snake", 2)
    for i in range(2, 27, 3):
        r.dot(pts[i][0] - 1, pts[i][1], "w_belly", 3, 2.4)
    r.line(pts[0][0], pts[0][1], pts[-1][0] + 0.5, pts[-1][1], "w_bone", 1.5, 3)
    gx, gy = pts[14]
    r.tube([(gx + 1, gy + 1), (30, 11)], [0.6, 0.6], "w_wood", 4)
    for (ox, oy) in ((0, 0), (-2.6, -2.0), (1.4, 2.6)):
        r.poly([(32.5 + ox, 9 + oy), (29 + ox, 9.2 + oy), (31.0 + ox, 12.4 + oy)], "w_steel", 4.5, normal=(-0.3, -0.4, 0.8))
    # three snake heads on necks fanning out of the grip
    for k, (nx, ny) in enumerate(((-6, -5), (-7, 1), (-4, 6))):
        hx, hy = gx + nx, gy + ny
        r.tube([(gx - 1, gy), (gx + nx * 0.5, gy + ny * 0.5 - 0.5), (hx + 1, hy)], [1.2, 1.0, 0.9], "w_snake", 3.0 + k * 0.1)
        r.ell(hx, hy, 2.2, 1.6, "w_snake", 3.5 + k * 0.1, ang=-15 + k * 25)
        r.dot(hx - 1, hy - 0.6, "w_heart", 4 if (k + f) % 2 == 0 else 3, 3.8 + k * 0.1)
        if (k + f) % 2 == 0:
            r.dot(hx - 3, hy + 0.6, "w_heart", 2, 3.8)
    if f: sparkle(r, 31, 6, 1)
    return r


def bulwark(f):
    """A flanged mace on a steel haft with a round blue shield bound to it: a gold boss and a riveted rim."""
    r, d = Rig(), Dg(11, 39, 25, 8)
    shaft(r, d, 0, 25, 1.2, "w_steel", 1)
    wraps(r, d, 1, 8, 1.6, 1.2, "w_lthr", 1.5)
    hx, hy = d.to(27)
    for a in range(0, 360, 45):
        ax, ay = math.cos(math.radians(a)), math.sin(math.radians(a))
        r.poly([(hx + ax * 3.0 - ay * 1.4, hy + ay * 3.0 + ax * 1.4), (hx + ax * 7.0, hy + ay * 7.0),
                (hx + ax * 3.0 + ay * 1.4, hy + ay * 3.0 - ax * 1.4)], "w_steel", 2.2, normal=(ax * 0.5, ay * 0.5, 0.75))
    r.ell(hx, hy, 4.0, 4.0, "w_steel", 2.4)
    r.dot(hx, hy, "w_gold", 3, 2.6)
    sx, sy = 11.0, 25.0
    r.ell(sx, sy, 9.6, 9.6, "w_blue", 3, bias=0.1)
    rim = r.part(False, 3.2)
    for a in range(360):
        for rr in (9.0, 9.6):
            x, y = sx + math.cos(math.radians(a)) * rr, sy + math.sin(math.radians(a)) * rr
            r.put(x, y, 3.2, "w_steel", J.lam(math.cos(math.radians(a)), math.sin(math.radians(a)), 0.5) + 0.1, rim)
    for a in range(15, 360, 30):
        x, y = sx + math.cos(math.radians(a)) * 7.6, sy + math.sin(math.radians(a)) * 7.6
        r.dot(x, y, "w_steel", 3, 3.4)
    r.ell(sx, sy, 2.8, 2.8, "w_gold", 3.6)
    for (a, b, t) in (((sx - 6, sy), (sx - 3.4, sy), 3), ((sx + 3.4, sy), (sx + 6, sy), 2),
                      ((sx, sy - 6), (sx, sy - 3.4), 3), ((sx, sy + 3.4), (sx, sy + 6), 2)):
        r.line(a[0], a[1], b[0], b[1], "w_gold", 3.5, t)
    if f == 0: sparkle(r, int(sx - 2), int(sy - 2), 1)
    else: sparkle(r, int(hx + 3), int(hy - 4), 2)
    return r


def heartseeker(f):
    """A heavy crimson crossbow with a gold heart at the nut, loaded with a long bolt whose head is a red heart."""
    r, d = Rig(), Dg(5, 37, 27, 9)
    uvpoly(r, d, [(0, -3.4), (0, 1.8), (6, 1.8), (9, 1.3), (27, 1.3), (27, -1.7), (9, -1.7), (6, -3.8)], "w_crim", 1, d.n_up(0.2))
    for u in (7.5, 16, 24):
        uvpoly(r, d, [(u, 1.8), (u + 1.2, 1.8), (u + 1.2, -2.0), (u, -2.0)], "w_gold", 1.5, d.n_up(0.3))
    fx, fy = d.to(22)
    prod = []
    for k in range(-12, 13):
        bend = (abs(k) / 12.0) ** 1.4 * 4.2
        prod.append((fx + d.px * k - d.ax * bend, fy + d.py * k - d.ay * bend))
    r.tube(prod, [1.1] * len(prod), "w_dwood", 3)
    for end in (prod[0], prod[-1]):
        r.ell(end[0], end[1], 1.2, 1.2, "w_gold", 3.2)
    sx, sy = d.to(11)
    r.line(prod[0][0], prod[0][1], sx, sy, "w_bone", 2.5, 3)
    r.line(prod[-1][0], prod[-1][1], sx, sy, "w_bone", 2.5, 2)
    r.tube([d.to(11), d.to(29)], [0.6, 0.6], "w_wood", 5)
    gem(r, *d.to(12, 0), 1.6, "w_heart", 2.5)
    # the heart head, drawn on its own grid (7 x 6), point towards the target
    hx, hy = d.to(31.5)
    heart = ["..11.11", ".14413 1".replace(" ", ""), "1443331", "1333321", ".13321.", "..121..", "...1..."]
    heart = [".11.11.", "1443321", "1433321", "1333221", ".13221.", "..121..", "...1..."]
    lg = {"1": ("w_crim", 1), "2": ("w_crim", 2), "3": ("w_crim", 3), "4": ("w_heart", 3)}
    hs = r.part(False, 6)
    for j, row in enumerate(heart):
        for i, ch in enumerate(row):
            if ch in lg:
                # rotate the grid 45 degrees towards the bolt's heading (down-left grid -> up-right)
                u, v = i - 3, j - 3
                x, y = hx + (u - v) * 0.72 + 0.5, hy + (u + v) * 0.72 - 0.5
                r.put(x, y, 6, lg[ch][0], 0.5, hs, lg[ch][1])
                r.put(x + 0.5, y, 6, lg[ch][0], 0.5, hs, lg[ch][1])
    for (x, y) in (((hx + 4, hy - 4), (hx - 3, hy - 5)) if f == 0 else ((hx + 5, hy - 2), (hx + 1, hy - 6))):
        r.dot(x, y, "w_heart", 3, 8)
    return r


def kris(f):
    """A wavy-bladed kris of black obsidian steel, a violet shadow running off its edge, a crescent pommel."""
    r, d = Rig(), Dg(9, 37, 27, 7)
    r.poly([(d.to(0)[0] - 3, d.to(0)[1] + 1), (d.to(0)[0] - 1, d.to(0)[1] - 3), (d.to(1.4)[0], d.to(1.4)[1]),
            (d.to(0)[0] + 1, d.to(0)[1] + 2.6)], "w_gold", 2, normal=(-0.3, -0.3, 0.9))
    shaft(r, d, 1.4, 9, 1.3, "w_bark", 1)
    wraps(r, d, 2, 8.5, 1.6, 1.3, "w_bark", 1.5)
    uvpoly(r, d, [(9, 3.0), (11, 4.2), (11.4, 0), (11, -2.4), (9, -3.0)], "w_gold", 3, d.n_up(0.3))
    wav = lambda t: 1.4 * math.sin(t * 15.0) * (1 - t * 0.5)
    blade(r, d, 11.4, 36, lambda t: (2.3 - 0.4 * t) * (1 if t < 0.82 else (1 - t) / 0.18) + wav(t),
          lambda t: (-2.3 + 0.4 * t) * (1 if t < 0.82 else (1 - t) / 0.18) + wav(t), "w_obsid", 2,
          spine=lambda t: wav(t))
    p = r.part(True, 6)
    for i in range(14):
        t = 0.1 + i * 0.055
        x, y = d.to(11.4 + 24.6 * t, wav(t) - 3.2 - (i % 3) * 0.5)
        if (i + f) % 3: r.put(x, y, 6, "w_rift", 0.5, p, 1 if i % 2 else 2)
    sparkle(r, *[int(round(c)) for c in d.to(34 if f == 0 else 22, 2.0 + wav(0.9 if f == 0 else 0.4))], 1, "w_rift")
    return r


def blightstaff(f):
    """A gnarled staff of dead wood grown round a glowing plague bulb; spores drift up from it."""
    r, d = Rig(), Dg(7, 39, 24, 8)
    pts = [d.to(u, 0.8 * math.sin(u * 0.5)) for u in range(0, 30, 3)]
    r.tube(pts, [1.3] * len(pts), "w_bark", 1)
    for u in (9, 18):
        a = d.to(u, 0.8 * math.sin(u * 0.5))
        r.tube([a, (a[0] - 2.4, a[1] - 1.0)], [0.8, 0.4], "w_bark", 1.2)
    hx, hy = d.to(31)
    for y in range(int(hy - 6), int(hy + 7)):
        for x in range(int(hx - 6), int(hx + 7)):
            dd = math.hypot(x - hx + 0.8, (y - hy + 0.8) * 1.05)
            if math.hypot(x - hx, y - hy) <= 5.2:
                if dd < 1.8:
                    r.put(x, y, 2.0, "w_blight", 0.5, r.part(True, 2.0), 4 if dd < 1.0 else 3)
                else:
                    t = 3 if dd < 3.0 else 2 if dd < 4.2 else 1
                    if (x * 3 + y * 5) % 7 == 0 and t > 1: t -= 1
                    r.put(x, y, 2.0, "w_plague", 0.5, r.part(True, 2.0), t)
    for k, a in enumerate((205, 245, 290, 335)):
        ax, ay = math.cos(math.radians(a)), math.sin(math.radians(a))
        r.tube([(hx - ax * 1.0, hy + 4.5), (hx + ax * 6.2, hy + ay * 6.2 + 0.5)], [1.0, 0.6], "w_bark", 3)
    r.tube([(hx - 5.5, hy + 1.0), (hx + 5.0, hy + 2.5)], [0.8, 0.7], "w_bark", 3.1)
    sp = [(-6, -8), (2, -10), (7, -5), (-2, -14), (5, -13)]
    for i, (sx, sy) in enumerate(sp):
        o = -1 if f else 0
        r.dot(hx + sx + (f if i % 2 else 0), hy + sy + o, "w_blight", 3 if (i + f) % 2 else 2, 8)
    return r


def orrery(f):
    """A staff crowned with a brass orrery: a violet star-orb, two gold rings and the little worlds riding them."""
    r, d = Rig(), Dg(6, 39, 23, 9)
    shaft(r, d, 0, 30, 1.2, "w_dwood", 1)
    wraps(r, d, 1, 7, 1.5, 1.2, "w_lthr", 1.5)
    r.ell(*d.to(0.4), 1.8, 1.8, "w_gold", 1.4)
    hx, hy = d.to(31)
    r.tube([d.to(27), d.to(29.5)], [2.0, 1.6], "w_gold", 2)
    r.ell(hx, hy, 4.6, 4.6, "w_night", 3, bias=0.2)
    r.dot(hx - 1.6, hy - 1.6, "w_star", 4, 3.5)
    r.dot(hx + 1.0, hy + 1.2, "w_star", 3, 3.5)
    for (rx, ry, ang, ph, mat) in ((8.5, 3.2, -25, 0.0, "w_heart"), (7.0, 2.6, 50, 2.0, "w_ice")):
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        p = r.part(True, 4)
        for i in range(72):
            a = i * 5 * math.pi / 180
            ex, ey = math.cos(a) * rx, math.sin(a) * ry
            x, y = hx + ex * ca - ey * sa, hy + ex * sa + ey * ca
            front = math.sin(a) > 0
            r.put(x, y, 4 if front else 2.5, "w_gold", 0.5, p, 3 if front and math.cos(a) < 0.3 else 2)
        a = ph + (0.9 if f else 0.0)
        ex, ey = math.cos(a) * rx, math.sin(a) * ry
        gem(r, hx + ex * ca - ey * sa, hy + ex * sa + ey * ca, 1.3, mat, 5)
    sparkle(r, int(hx + (6 if f == 0 else -6)), int(hy - 7), 1, "w_star")
    return r


def grudgestone(f):
    """A leather sling hanging open round a heavy cursed stone carved with a red grudge rune."""
    r = Rig()
    hx, hy = 23.0, 6.0
    sx, sy = 13.0, 27.0
    sw = 0 if f == 0 else 1
    r.polyline([(hx, hy), (hx - 2 - sw, hy + 8), (sx + 4, sy - 5)], "w_lthr", 2, 3)
    r.polyline([(hx + 1, hy), (hx + 4, hy + 9), (sx + 8, sy - 2)], "w_lthr", 2, 1)
    r.ell(hx + 0.5, hy - 1.5, 1.8, 1.4, "w_lthr", 2.4)
    r.ell(hx + 0.5, hy - 2.5, 1.0, 1.0, "w_iron", 2.6, flat=3)
    r.poly([(sx - 4, sy - 2), (sx + 10, sy - 6), (sx + 11, sy + 2), (sx + 2, sy + 9), (sx - 5, sy + 6)], "w_lthr", 3,
           normal=(0.1, 0.3, 0.9))
    r.ell(sx + 3, sy + 0.5, 7.0, 6.2, "w_stone", 4, ang=-15)
    for (cx, cy) in ((sx - 1, sy + 2), (sx + 6, sy - 2)):
        r.ell(cx, cy, 1.4, 1.0, "w_stone", 4.2, bias=-0.5)
    rune = [(0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (-1, -2), (-2, -1), (1, 0), (2, 1), (-1, 2), (1, 2)]
    for (x, y) in rune:
        r.dot(sx + 3 + x, sy + 0.5 + y, "w_heart", 3 if (x + y + f) % 3 else 4, 5)
    for i, (x, y) in enumerate(((sx - 6, sy - 6), (sx + 12, sy - 8), (sx + 13, sy + 6))):
        r.dot(x, y + (-1 if f else 0), "w_heart", 2 + (i % 2), 8)
    return r


def midas(f):
    """A gilded sling of red silk cord cradling a stack of gold coins; one coin flips in the air above."""
    r = Rig()
    hx, hy = 23.0, 6.0
    sx, sy = 13.0, 28.0
    r.polyline([(hx, hy), (hx - 3, hy + 9), (sx + 2, sy - 4)], "w_crim", 2, 3)
    r.polyline([(hx + 1, hy), (hx + 4, hy + 9), (sx + 10, sy - 2)], "w_crim", 2, 1)
    r.ell(hx + 0.5, hy - 1.5, 2.0, 1.6, "w_gold", 2.4)
    r.poly([(sx - 3, sy - 3), (sx + 12, sy - 3), (sx + 11, sy + 4), (sx + 4, sy + 8), (sx - 3, sy + 4)], "w_crim", 3,
           normal=(0.1, 0.3, 0.9))
    for k in range(4):
        r.ell(sx + 4 + k * 0.4, sy + 2 - k * 2.0, 5.0, 1.6, "w_gold", 4 + k * 0.1, bias=0.1)
    r.ell(sx + 5.6, sy - 6.0, 5.0, 1.6, "w_gold", 4.5, bias=0.3)
    cx, cy = (26.0, 18.0) if f == 0 else (27.0, 15.0)
    if f == 0:
        r.ell(cx, cy, 3.6, 3.6, "w_gold", 6, bias=0.2)
        r.dot(cx, cy, "w_gold", 1, 6.2)
        r.dot(cx - 1, cy - 1, "w_gold", 4, 6.2)
    else:
        r.ell(cx, cy, 1.4, 3.6, "w_gold", 6, bias=0.3)
    sparkle(r, int(cx - 4), int(cy - 4), 1, "w_spark")
    sparkle(r, int(sx + 9), int(sy - 8) - f, 1, "w_spark")
    return r


def lance(f):
    """A knight's charging lance: a long fluted steel cone, a flared vamplate guard and a red pennant snapping."""
    r, d = Rig(), Dg(4, 39, 30, 2)
    shaft(r, d, 0, 11, 1.3, "w_wood", 1)
    wraps(r, d, 2, 9, 1.6, 1.3, "w_lthr", 1.5)
    r.ell(*d.to(0.5), 1.8, 1.8, "w_iron", 1.4)
    # vamplate: a round steel guard seen at an angle
    vx, vy = d.to(12.0)
    r.ell(vx, vy, 5.6, 2.6, "w_steel", 3, ang=math.degrees(math.atan2(d.py, d.px)), bias=0.05)
    blade(r, d, 12.6, 46, lambda t: 3.6 * (1 - t) ** 0.9 + 0.2, lambda t: -3.6 * (1 - t) ** 0.9 - 0.2, "w_steel", 2, k=0.8)
    for u in (19, 26, 33):
        w = 3.6 * (1 - (u - 12.6) / 33.4) ** 0.9
        a, b = d.to(u, w), d.to(u + 1.6, -w)
        r.line(a[0], a[1], b[0], b[1], "w_steel", 2.5, 1)
    # pennant tied to the haft behind the guard, streaming back and up
    w = 0.0 if f == 0 else 1.0
    uvpoly(r, d, [(8.0, 1.0), (11.0, 1.0), (9.0 - w, 10.5 + w), (7.4, 7.2), (4.4 + w, 11.0 - w), (4.6, 1.0)], "w_crim", 3.5,
           (-0.25, -0.35, 0.9))
    a, b = d.to(9.6, 1.4), d.to(6.4, 8.6 + w * 0.5)
    r.line(a[0], a[1], b[0], b[1], "w_gold", 3.6, 3)
    if f == 0: sparkle(r, *[int(round(c)) for c in d.to(45, 0.4)], 2)
    else: sheen(r, d, 30, 1.0, -3.6, 3.6, {"w_steel"})
    return r


def lash(f):
    """A coiled viper-skin whip: a wrapped handle with a snake-head pommel, the lash looping out to a cracking tip."""
    r = Rig()
    gx0, gy0, gx1, gy1 = 6.0, 37.0, 13.0, 27.0
    r.tube([(gx0, gy0), (gx1, gy1)], [1.6, 1.4], "w_snake", 2)
    for t in (0.2, 0.4, 0.6, 0.8):
        x, y = gx0 + (gx1 - gx0) * t, gy0 + (gy1 - gy0) * t
        r.line(x - 1.4, y - 0.4, x + 1.0, y + 1.2, "w_belly", 2.5, 2)
    r.ell(gx0 - 0.6, gy0 + 0.6, 2.2, 1.6, "w_snake", 2.4, ang=-55)
    r.dot(gx0 - 1.4, gy0 - 0.2, "w_heart", 4, 2.8)
    pts = []
    for i in range(60):
        t = i / 59.0
        a = t * 2.1 * math.pi + 2.4
        R = 9.0 - 2.0 * t
        cx, cy = 20 + 6 * t, 20 - 9 * t
        pts.append((cx + math.cos(a) * R, cy + math.sin(a) * R * 0.75))
    pts = [(gx1, gy1)] + pts
    rad = [1.3 - 1.0 * (i / len(pts)) for i in range(len(pts))]
    r.tube(pts, [max(0.5, x) for x in rad], "w_snake", 3)
    for i in range(2, len(pts) - 6, 5):
        r.dot(pts[i][0], pts[i][1], "w_belly", 3, 3.2)
    tx, ty = pts[-1]
    for k, (x, y) in enumerate(((tx + 1, ty - 1), (tx + 2, ty - 2), (tx + 3, ty - 1)) if f == 0 else ((tx + 1, ty), (tx + 2, ty - 2), (tx + 2, ty + 1))):
        r.dot(x, y, "w_spark", 4 if k == 0 else 3, 8)
    sparkle(r, int(tx + 3), int(ty - 3) + f, 1, "w_spark")
    return r


def kunai(f):
    """Three dark kunai fanned out, ring pommels and red-wrapped grips, one with a red marking ribbon."""
    r = Rig()
    for k, (x0, y0, x1, y1) in enumerate(((5, 33, 19, 6), (10, 38, 29, 16), (4, 25, 27, 7))):
        d = Dg(x0, y0, x1, y1)
        L = d.L
        rp = r.part(False, 1 + k)
        for a in range(0, 360, 20):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            x, y = d.to(0.2)
            r.put(x + ca * 1.7, y + sa * 1.7, 1 + k, "w_steel", J.lam(ca, sa, 0.4), rp)
        shaft(r, d, 1.6, 7.5, 0.9, "w_crim", 1.2 + k)
        wraps(r, d, 2, 7, 1.4, 0.9, "w_crim", 1.3 + k, 1)
        blade(r, d, 7.5, L, lambda t: 2.2 * math.sin(min(1.0, t * 3.0) * math.pi / 2) * (1 - t) + 0.3,
              lambda t: -2.2 * math.sin(min(1.0, t * 3.0) * math.pi / 2) * (1 - t) - 0.3, "w_iron", 1.4 + k, k=0.8)
        e = r.part(True, 1.5 + k)
        for i in range(int(L - 9)):
            t = i / (L - 7.5)
            x, y = d.to(8 + i, 2.2 * math.sin(min(1.0, t * 3.0) * math.pi / 2) * (1 - t) + 0.1)
            r.put(x, y, 1.5 + k, "w_steel", 0.5, e, 3)
        if k == 2:
            a = d.to(1.0)
            sw = 1 if f else 0
            r.poly([(a[0], a[1]), (a[0] - 3, a[1] + 3 + sw), (a[0] - 1, a[1] + 6), (a[0] + 1, a[1] + 1.5)], "w_cloth", 4,
                   normal=(-0.2, -0.3, 0.9))
    sparkle(r, 26 if f == 0 else 29, 7 if f == 0 else 16, 1)
    return r


ICONS = {
    "Gravehook": gravehook, "Moonglaive": moonglaive, "Riftblade": riftblade, "SnakeEyes": snakeeyes,
    "Tidebreaker": tidebreaker, "Leechfang": leechfang, "Briarbow": briarbow, "DirgeMaul": dirgemaul,
    "Wickstaff": wickstaff, "Arcbolt": arcbolt, "Frostbrand": frostbrand, "Mercyblade": mercyblade, "Reaper": reaper,
    "Starfall": starfall, "HydraBow": hydrabow, "Bulwark": bulwark, "Heartseeker": heartseeker, "Kris": kris,
    "Blightstaff": blightstaff, "Orrery": orrery, "Grudgestone": grudgestone, "Midas": midas, "Lance": lance,
    "Lash": lash, "Kunai": kunai,
}


def frames(name):
    return [render(ICONS[name](f)) for f in (0, 1)]


if __name__ == "__main__":
    import weapon_rigs
    weapon_rigs.build_bubbles()
