"""Items wave 3: icons, shop pictures, HUD icons and shop-pedestal drawings for src/CrawlFurther/Items/ItemPack3.cs.

    python3 tools/sprites/items3_icons.py        -> art/out_items3/Icon*.png|json (+ build/boards/items3_icons.png)

Per item:
  Icon<Name>         16x16, anim Idle (2 frames: base + a small real change), feet (8,15), 1 px dark outline,
                     lit from the top-left (same rules as items_v2_icons.py). The vault's SECRETS page and the free
                     pickups use these.
  Icon<Name>Bubble   34x41 shop pop-up / library picture, anim Bubble (2 frames). Artifacts: the icon at 1x in the
                     lower middle like the v2 items. Potions are drawn straight into the bubble in the vanilla potion
                     style (no dark outline, a pale glass rim, three flat liquid tones split light-left / dark-right,
                     a white glint and a cork), the way PotionLargeGreen & co look in AtlasProps.
  Icon<Name>Hud      11x7 hand-drawn HUD icon (artifacts only; potions are drunk, the HUD never shows them).
PEDESTALS: the tiny counter drawing per item id, read by tools/sprites/pedestal_rigs.py (vanilla potion bottles are
5x7 with a cork, artifacts 4-7 px wide, no outline, 2-4 flat tones).

The small RGB canvas kit here (Cv, ell, line, outline, glow...) is shared with items3_fx.py.
"""
import json, math, os, sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import items_v2_icons as V2  # noqa: E402
import jinx_v2_rigs as J  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "art", "out_items3")
BOARDS = os.path.join(ROOT, "build", "boards")


def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def R(*cols):
    return [hx(c) for c in cols]


K = hx("1e1a1c")        # outline, warm black (vanilla)
K2 = hx("2a2226")
# ramps dark -> light
WOOD = R("3b2416", "5e3a22", "8a5a32", "b4844c", "d8ae72")
IRON = R("2c2a30", "46444c", "6c6a74", "9c9aa4", "cfcdd6")
GOLD = R("5c3a14", "9a6426", "d69e3e", "ffe28c", "fff6d0")
BONE = R("5c5040", "968a6c", "ccc0a0", "efe8d2", "fffbef")
RED = R("4e1016", "8a1e24", "c8342e", "f0644a", "ffb090")
PINK = R("5a1a3e", "9a2e6a", "d04e98", "f48cc4", "ffd0ea")
TEAL = R("123a3e", "1f6466", "33a0a0", "78dcd0", "d0fff6")
YEL = R("6a4a0c", "b88a14", "f2c62a", "ffe66a", "fff8c4")
ORNG = R("6a2a0c", "b0501a", "f08a26", "ffbe4e", "ffe8a8")
LEAF = R("1e381a", "365e28", "5e963c", "96ce60", "d6f4a6")
VIO = R("2a1240", "4e2678", "7e46b8", "b48ae8", "e6d2ff")
CREAM = R("6e5c3c", "a48a5c", "d0b888", "efe0bc", "fff8e8")
CLOTH = R("5a4e46", "8a7e72", "bcb0a0", "e0d6c4", "fffaf0")
SKIN = R("4a2c22", "7a4a34", "a8704c", "d49c70", "f2c8a0")
GLASSC = R("2c3c4e", "4c6a82", "86a8c0", "c4dcec", "f4fbff")
STONE = R("3a3a40", "58585f", "7a7a82", "9c9ca4", "c4c4ca")
FUR = R("3a2618", "6a4426", "9a6a3c", "c89a62", "ecd2a0")


class Cv:
    """Pixel canvas: (x, y) -> (r, g, b). y grows downward."""

    def __init__(self):
        self.px = {}

    def put(self, x, y, c, over=True):
        k = (int(round(x)), int(round(y)))
        if c is None:
            self.px.pop(k, None); return
        if over or k not in self.px:
            self.px[k] = tuple(c[:3])

    def get(self, x, y):
        return self.px.get((int(round(x)), int(round(y))))

    def copy(self):
        c = Cv(); c.px = dict(self.px); return c

    def shift(self, dx, dy):
        c = Cv(); c.px = {(x + dx, y + dy): v for (x, y), v in self.px.items()}; return c

    def flipx(self, w):
        c = Cv(); c.px = {(w - 1 - x, y): v for (x, y), v in self.px.items()}; return c

    def merge(self, o, over=True):
        for k, v in o.px.items():
            if over or k not in self.px: self.px[k] = v
        return self

    def bbox(self):
        if not self.px: return None
        xs = [k[0] for k in self.px]; ys = [k[1] for k in self.px]
        return min(xs), min(ys), max(xs), max(ys)

    def image(self, w, h, ox=0, oy=0, alpha=None):
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        p = im.load()
        for (x, y), c in self.px.items():
            X, Y = x + ox, y + oy
            if 0 <= X < w and 0 <= Y < h:
                a = 255 if alpha is None else alpha.get((x, y), 255)
                p[X, Y] = c + (a,)
        return im


def pick(ramp, l):
    n = len(ramp)
    return ramp[max(0, min(n - 1, int((l + 1.0) * 0.5 * n)))]


def ell(c, cx, cy, rx, ry, ramp, bias=0.0, over=True, spec=None, keep=None, ang=0.0):
    """Filled ellipse lit from the top-left."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    Rm = int(max(rx, ry)) + 2
    for y in range(int(math.floor(cy - Rm)), int(math.ceil(cy + Rm)) + 1):
        for x in range(int(math.floor(cx - Rm)), int(math.ceil(cx + Rm)) + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa; v = -dx * sa + dy * ca
            nu, nv = u / max(rx, 0.5), v / max(ry, 0.5)
            d = nu * nu + nv * nv
            if d > 1.0: continue
            if keep and not keep(x, y): continue
            wx, wy = nu * ca - nv * sa, nu * sa + nv * ca
            l = 0.8 * (-(wx + wy) / 1.414) + 0.35 * (1 - d) - 0.1 + bias
            col = pick(ramp, l)
            if spec is not None and -0.8 < wx < -0.15 and -0.85 < wy < -0.2 and d < 0.45:
                col = spec
            c.put(x, y, col, over)


def rect(c, x0, y0, x1, y1, ramp, bias=0.0, over=True):
    """Box shaded lit from the top-left (inclusive corners)."""
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u, v = (x - x0) / w * 2 - 1, (y - y0) / h * 2 - 1
            l = -(u * 0.5 + v * 0.6) * 0.8 + bias
            c.put(x, y, pick(ramp, l), over)


def line_pts(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return out


def line(c, x0, y0, x1, y1, col, over=True):
    for x, y in line_pts(x0, y0, x1, y1):
        c.put(x, y, col, over)


def poly(c, pts, ramp, bias=0.0, over=True):
    """Filled polygon, lit from the top-left by distance into the shape's bbox."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = int(min(xs)), int(max(xs)), int(min(ys)), int(max(ys))
    n = len(pts)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            inside = False
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]; xj, yj = pts[j]
                if ((yi > y + 0.5) != (yj > y + 0.5)) and (x + 0.5 < (xj - xi) * (y + 0.5 - yi) / (yj - yi + 1e-9) + xi):
                    inside = not inside
                j = i
            if inside:
                u = (x - x0) / max(1, x1 - x0) * 2 - 1; v = (y - y0) / max(1, y1 - y0) * 2 - 1
                c.put(x, y, pick(ramp, -(u * 0.55 + v * 0.55) * 0.85 + bias), over)


def selout(c, k=0.42):
    """A 1 px rim round the shape in each edge pixel's own colour, darkened (no flat black ring)."""
    o = Cv(); o.px = dict(c.px)
    for (x, y), v in c.px.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in c.px and q not in o.px:
                o.px[q] = tuple(int(ch * k + 10) for ch in v)
    return o


def outline(c, col=K, skip=()):
    """Selective outline for the world effects: only the lower and right edges get a 1 px rim (they turn away from
    the top-left light and sit the shape on the floor), in the edge pixel's own colour darkened when col is the
    default black, else in col. The lit upper and left edges read against the dark floor by value."""
    o = Cv(); o.px = dict(c.px)
    for (x, y), v in c.px.items():
        if v in skip: continue
        for dx, dy in ((1, 0), (0, 1)):
            k = (x + dx, y + dy)
            if k not in c.px and k not in o.px:
                o.px[k] = tuple(int(ch * 0.42 + 10) for ch in v) if col == K else col
    return o


def write_sheet(name, frames, w, h, anims, out=OUT, origin=None, cols=None):
    """frames: list of PIL images (w x h); anims: [(name, [frame idx], [durations])]."""
    cols = cols or min(len(frames), 8)
    rows = (len(frames) + cols - 1) // cols
    pw, ph = 1, 1
    while pw < cols * w: pw *= 2
    while ph < rows * h: ph *= 2
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.alpha_composite(f, ((i % cols) * w, (i // cols) * h))
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, name + ".png"))
    man = {"cellW": w, "cellH": h, "cols": cols,
           "anims": [{"name": a, "frames": list(fr), "durations": list(du)} for a, fr, du in anims]}
    if origin is not None: man["origin"] = list(origin)
    json.dump(man, open(os.path.join(out, name + ".json"), "w"))
    # preview: every anim on its own row at 6x on Crawl's dark floor
    S = 6
    W = max(len(fr) for _, fr, _ in anims) * (w + 2) * S
    H = len(anims) * (h + 2) * S
    pv = Image.new("RGBA", (max(W, 8), max(H, 8)), (28, 26, 32, 255))
    for r, (_, fr, _) in enumerate(anims):
        for j, fi in enumerate(fr):
            pv.alpha_composite(frames[fi].resize((w * S, h * S), Image.NEAREST), (j * (w + 2) * S, r * (h + 2) * S))
    pv.convert("RGB").save(os.path.join(out, name + "_preview.png"))
    return img


# ===================================================================================================== artifact icons
# Drawn through items_v2_icons.Pen (the jinx_v2 material renderer) in 16-unit cell coordinates, so each renders as the
# 16 px icon and, at V2.BUBBLE_SCALE, as the 22 px shop and vault picture.
for _k, _ramp in (("satin", RED), ("duck", YEL), ("fur3", FUR), ("whet", STONE), ("gem", VIO), ("linen", CLOTH),
                  ("poster", R("6e5434", "a08058", "c8aa76", "e0c896", "f4e2b8")), ("party", PINK), ("teal3", TEAL),
                  ("beak", ORNG), ("ham", R("5a1a1c", "9a3030", "c85a4a", "e88a6a", "f8b890"))):
    J.RAMPS[_k] = list(_ramp)
J.SHINY |= {"duck", "satin", "gem"}


@V2.accent("duck")
def draw_party_hat(g, ph):
    stripe = lambda x, y: "teal3" if (int(x) + 2 * int(y)) % 6 in (0, 1) else "party"
    g.poly([(2.6, 13.4), (13.4, 13.4), (9.4, 2.2)], stripe, 1.0, curve=0.8, bias=0.15)
    g.ell(8.0, 13.6, 5.8, 1.2, "gold", 1.1, bias=0.1)
    g.ell(9.6, 2.2, 1.8, 1.8, "duck", 1.2)
    for (x, y) in ((8.6, 0.6), (11.2, 1.2), (10.8, 3.6)):
        g.dot(x, y, "duck", 4 if ph else 2, 1.25)
    conf = ((1.4, 5.0, "party"), (13.8, 6.0, "teal3"), (14.6, 10.6, "duck"), (1.0, 9.4, "teal3")) if ph == 0 else \
        ((1.6, 3.2, "teal3"), (13.4, 8.0, "duck"), (14.6, 12.8, "party"), (0.8, 11.0, "duck"))
    for (x, y, m) in conf:
        g.dot(x, y, m, 3, 2.0)


@V2.accent("duck")
def draw_bard_lute(g, ph):
    # neck and the bent-back pegbox, behind the body
    g.tube([(8.0, 8.0), (13.2, 2.8)], [1.0, 0.8], "wood", 0.8, bias=0.2)
    g.tube([(13.2, 2.8), (14.6, 2.6), (15.0, 3.8)], [0.9, 0.7, 0.5], "wood", 0.82, bias=0.1)
    for (x, y) in ((13.8, 1.8), (14.8, 2.4)):
        g.dot(x, y, "ivory", 3, 0.9)
    # pear-shaped body, sound hole with a rosette, bridge
    g.ell(6.0, 10.0, 4.8, 4.2, "wood", 1.0, ang=-35, bias=0.15)
    g.ell(6.6, 9.4, 1.4, 1.4, "lthr", 1.1, flat=0)
    g.dot(6.0, 8.8, "gold", 2, 1.12)
    g.line(3.4, 12.0, 4.6, 13.0, "lthr", 1.1, tone=1)
    # strings from the bridge up the neck
    for k in (-0.5, 0.5):
        g.line(4.4 + k, 12.0 + k, 13.0 + k, 3.2 + k, "ivory", 1.2, tone=3)
    # a note drifts off it
    nx, ny = (2.0, 3.6) if ph else (2.6, 4.4)
    g.ell(nx, ny + 2.0, 0.9, 0.7, "duck", 1.3, flat=3)
    g.line(nx + 0.8, ny + 2.0, nx + 0.8, ny - 0.4, "duck", 1.3, tone=3)
    g.line(nx + 0.8, ny - 0.4, nx + 2.0, ny + 0.4, "duck", 1.3, tone=4 if ph else 2)


def draw_pet_ferret(g, ph):
    # long body curled along the bottom, tail rising at the back, head up-left
    tail = 0.6 if ph else 0.0
    g.tube([(11.6, 12.0), (13.4, 10.0), (13.6, 7.0 - tail), (12.8, 5.2 - tail)], [1.2, 1.0, 0.8, 0.5], "fur3", 0.8, bias=0.1)
    g.ell(8.6, 11.2, 5.0, 2.8, "fur3", 1.0, bias=0.15)
    g.ell(4.8, 7.4, 3.2, 2.7, "fur3", 1.1, bias=0.2)
    g.ell(3.0, 8.4, 1.8, 1.1, "linen", 1.15, bias=0.2)
    g.ell(4.0, 4.6, 0.9, 0.9, "fur3", 1.05, bias=0.2)
    g.ell(6.6, 4.8, 0.9, 0.9, "fur3", 1.05)
    # the dark mask band across the eyes, a bright eye, the nose
    g.line(3.6, 6.8, 6.8, 6.8, "fur3", 1.2, tone=0)
    g.dot(4.6, 6.8, "blk", 0, 1.25)
    g.dot(4.4, 6.4, "white", 4 if not ph else 2, 1.26)
    g.dot(1.4, 8.4, "blk", 0, 1.2)
    g.ell(10.8, 10.4, 2.0, 1.0, "fur3", 1.05, flat=3)
    for x in (6.4, 11.0):
        g.ell(x, 13.8, 1.0, 0.6, "fur3", 1.06, flat=1)


@V2.accent("teal3")
def draw_bubble_pipe(g, ph):
    # the bowl on the right, the stem curving down-left to a bone mouthpiece
    g.tube([(1.8, 12.4), (4.0, 13.2), (7.0, 12.0), (9.6, 11.4)], [0.7, 0.8, 0.8, 0.9], "wood", 0.9, bias=0.15)
    g.ell(1.4, 12.4, 0.8, 0.8, "ivory", 0.95)
    g.poly([(9.0, 8.0), (13.6, 8.0), (13.0, 13.4), (9.6, 13.4)], "wood", 1.0, curve=0.9, bias=0.2)
    g.ell(11.3, 8.0, 2.3, 0.8, "lthr", 1.05, flat=0)
    g.line(9.2, 9.6, 13.4, 9.6, "gold", 1.06, tone=2)
    # soap bubbles: thin teal rings with a shine
    bub = ((11.2, 4.4, 1.9), (6.2, 3.0, 1.4), (13.6, 1.0, 0.9)) if ph == 0 else ((11.0, 3.2, 1.9), (6.4, 1.4, 1.4), (14.2, 5.2, 0.9))
    for (x, y, r_) in bub:
        g.arc(x, y, r_, 0, 360, "teal3", 1.5, tone=3, step=20)
        g.dot(x - r_ * 0.5, y - r_ * 0.5, "white", 4, 1.6)


def draw_rubber_duck(g, ph):
    g.ell(12.6, 8.4, 1.6, 1.4, "duck", 0.9, bias=0.1)
    g.ell(8.2, 10.6, 5.6, 3.4, "duck", 1.0, bias=0.1)
    g.ell(5.2, 5.6, 3.0, 2.8, "duck", 1.1, bias=0.15)
    # beak, eye, wing
    g.poly([(0.4, 6.0), (2.8, 5.2), (3.0, 7.6), (0.8, 7.4)], "beak", 1.2, bias=0.2)
    g.line(0.8, 6.8, 2.6, 6.8, "beak", 1.21, tone=1)
    g.dot(5.0, 4.8, "blk", 0, 1.2)
    g.dot(4.6, 4.4, "white", 4, 1.21)
    g.ell(9.2, 10.2, 2.6, 1.4, "duck", 1.05, ang=-12, bias=-0.35)
    g.line(3.0, 13.8, 12.8, 13.8, "duck", 1.05, tone=1)
    if ph:
        for (x0, y0, x1, y1) in ((0.6, 2.8, 1.6, 1.8), (13.4, 3.2, 14.6, 2.2)):
            g.line(x0, y0, x1, y1, "white", 1.3, tone=3)


@V2.accent("tox")
def draw_firefly_jar(g, ph):
    # dark inside of the jar, glass walls catching the light, a cork lid tied with twine
    g.poly([(3.0, 4.4), (13.0, 4.4), (13.0, 14.6), (3.0, 14.6)], "iron", 0.8, flat=1)
    g.tube([(3.2, 4.6), (3.2, 14.4)], [0.6], "glass", 0.9, flat=3)
    g.tube([(12.8, 4.6), (12.8, 14.4)], [0.6], "glass", 0.9, flat=1)
    g.tube([(3.4, 14.4), (12.6, 14.4)], [0.6], "glass", 0.9, flat=2)
    g.line(4.4, 6.0, 4.4, 9.0, "glass", 0.95, tone=4)
    g.poly([(3.4, 1.2), (12.6, 1.2), (12.6, 4.2), (3.4, 4.2)], "cork", 1.0, curve=0.8, bias=0.15)
    for x in range(4, 13):
        g.dot(x, 3.8, "linen", 3 if x % 2 else 1, 1.05)
    # fireflies glowing inside, each with a soft halo
    flies = ((6.0, 8.2), (9.4, 6.4), (8.2, 11.4)) if ph == 0 else ((7.0, 7.0), (10.2, 9.4), (5.8, 11.6))
    for (x, y) in flies:
        g.ell(x, y, 1.4, 1.4, "leaf", 0.85, flat=2)
        g.dot(x, y, "tox", 4, 0.9)


def shoe(g, ox, oy, mat, z, bow=False):
    """A dancing heel in profile, toe to the right; (ox, oy) = the back of the heel cup at the sole."""
    g.poly([(ox, oy), (ox, oy - 2.4), (ox + 2.2, oy - 2.6), (ox + 4.6, oy - 4.2), (ox + 7.6, oy - 4.0), (ox + 9.4, oy - 2.0),
            (ox + 9.2, oy), (ox + 3.6, oy)], mat, z, curve=0.3, bias=0.15)
    g.ell(ox + 1.6, oy - 2.4, 1.6, 0.6, mat, z + 0.01, flat=0)
    g.line(ox + 2.0, oy, ox + 9.2, oy, "lthr", z + 0.01, tone=0)
    g.tube([(ox + 0.4, oy), (ox + 0.8, oy + 2.8)], [0.5], "lthr", z + 0.01, flat=0)
    g.line(ox + 5.0, oy - 3.6, ox + 7.8, oy - 3.4, mat, z + 0.02, tone=4)
    if bow:
        g.ell(ox + 4.4, oy - 3.4, 1.2, 0.8, "party", z + 0.03, flat=3)
        g.dot(ox + 4.4, oy - 3.4, "party", 4, z + 0.04)


@V2.accent("party")
def draw_dancing_shoes(g, ph):
    shoe(g, 5.0, 6.4, "satin", 0.9)
    shoe(g, 1.0, 12.0, "satin", 1.2, bow=True)
    st = (13.6, 2.0) if ph == 0 else (14.2, 5.0)
    g.glint(st[0], st[1])
    g.dot(2.0 if ph else 4.0, 3.0, "duck", 3, 2.0)


@V2.accent("fire")
def draw_whetstone(g, ph):
    # a grey stone block lying across, its top face lit; a blade drawn along it
    g.poly([(1.0, 11.4), (10.0, 6.4), (14.6, 9.0), (5.6, 14.2)], "whet", 1.0, flat=2)
    g.poly([(1.0, 11.4), (10.0, 6.4), (10.6, 5.2), (1.4, 10.2)], "whet", 1.01, flat=3)
    g.poly([(5.6, 14.2), (14.6, 9.0), (14.6, 10.2), (5.6, 15.2)], "whet", 1.01, flat=1)
    g.line(3.0, 11.6, 11.0, 7.4, "whet", 1.02, tone=4)
    g.tube([(4.2, 6.4), (12.6, 2.2)], [0.9, 0.4], "steel", 1.3, bias=0.2)
    g.tube([(1.6, 7.8), (4.2, 6.4)], [0.9], "wood", 1.31, bias=0.2)
    sp = (12.6, 3.6) if ph == 0 else (11.4, 4.8)
    g.glint(sp[0], sp[1])
    for (x, y) in (((14.4, 1.4), (9.4, 1.2)) if ph == 0 else ((14.6, 6.0), (10.2, 0.6))):
        g.dot(x, y, "fire", 3, 2.0)


@V2.accent("fire")
def draw_phoenix_feather(g, ph):
    # vane: warm orange on the lit side, red on the far side, widening toward the tip; the flame burns at the tip
    ax, ay, bx, by = 1.4, 14.6, 12.6, 3.0
    L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L; nx, ny = -uy, ux
    for side, mat in ((1, "satin"), (-1, "beak")):
        pts = [(ax + ux * 3.0, ay + uy * 3.0)]
        for t in (0.35, 0.6, 0.85):
            w = 1.2 + 1.8 * t
            pts.append((ax + ux * L * t + nx * w * side, ay + uy * L * t + ny * w * side))
        pts.append((bx, by))
        g.poly(pts, mat, 1.0 if side < 0 else 0.98, bias=0.2 if side < 0 else -0.1)
    for t in (0.42, 0.62, 0.8):
        x, y = ax + ux * L * t, ay + uy * L * t
        g.line(x, y, x - nx * 2.2 + ux * 1.2, y - ny * 2.2 + uy * 1.2, "beak", 1.05, tone=4)
    g.line(ax, ay, bx - ux, by - uy, "duck", 1.1, tone=3)
    g.line(ax, ay, ax + ux * 3, ay + uy * 3, "ivory", 1.1, tone=3)
    f = 0.5 if ph else 0.0
    g.ell(bx + 0.4, by - 0.6, 1.4, 1.8 + f, "ember", 1.2, flat=2)
    g.ell(bx + 0.4, by - 0.2, 0.7, 1.0, "fire", 1.21, flat=3)
    g.dot(bx + 0.8 + (0.4 if ph else -0.2), by - 2.6 - f, "fire", 3, 1.2)


@V2.accent("lilac")
def draw_siphon_gem(g, ph):
    # silver claws hold a violet gem cut in facets; wisps are drawn into it from both sides
    for (x0, y0, x1, y1) in ((4.0, 14.0, 5.2, 11.0), (12.0, 14.0, 10.8, 11.0), (8.0, 15.0, 8.0, 12.6)):
        g.tube([(x0, y0), (x1, y1)], [0.6], "steel", 0.8, bias=0.2)
    top, l, r_, bot = (8.0, 2.6), (3.8, 7.6), (12.2, 7.6), (8.0, 13.6)
    g.poly([top, l, (8.0, 8.4)], "gem", 1.0, flat=3)
    g.poly([top, r_, (8.0, 8.4)], "gem", 1.0, flat=2)
    g.poly([l, bot, (8.0, 8.4)], "gem", 1.0, flat=2)
    g.poly([r_, bot, (8.0, 8.4)], "gem", 1.0, flat=1)
    g.line(top[0], top[1] + 0.6, l[0] + 0.8, l[1], "gem", 1.01, tone=4)
    g.dot(6.4, 5.6, "white", 4, 1.02)
    w = ((1.0, 3.4), (2.2, 4.2), (3.2, 4.6), (15.0, 2.4), (13.8, 3.2), (12.8, 4.2)) if ph == 0 else \
        ((1.0, 5.4), (2.0, 5.6), (3.0, 6.0), (15.0, 4.4), (14.0, 4.6), (13.0, 5.4))
    for (x, y) in w:
        g.dot(x, y, "lilac", 3, 2.0)
    if ph:
        g.glint(6.4, 5.6)


def draw_gluttons_fork(g, ph):
    # an iron fork rising to the upper right with a hunk of ham speared on its tines
    g.tube([(1.6, 14.6), (7.6, 8.6)], [0.9, 0.7], "iron", 1.0, bias=0.35)
    g.tube([(7.0, 9.2), (10.0, 9.2)], [0.7], "iron", 1.05, bias=0.35)
    for bx in (7.4, 9.0, 10.6):
        g.tube([(bx, 9.0), (bx + 1.6, 1.6)], [0.45], "steel", 1.1, flat=3 if bx < 10 else 2)
    g.ell(10.6, 5.2, 3.0, 2.2, "ham", 1.2, ang=-15, bias=0.15)
    g.ell(9.4, 4.6, 1.0, 0.8, "ham", 1.25, flat=4)
    g.ell(12.6, 5.6, 0.8, 1.0, "ivory", 1.22)
    for bx in (7.4, 9.0, 10.6):
        g.dot(bx + 1.6, 1.4, "steel", 4, 1.3)
    drip = (12.4, 8.6) if ph == 0 else (12.4, 9.8)
    g.dot(drip[0], drip[1], "duck", 3, 1.3)
    if ph:
        g.glint(9.0, 3.6)


@V2.accent("satin")
def draw_tally_stick(g, ph):
    g.tube([(1.0, 12.8), (14.4, 4.6)], [1.6], "wood", 1.0, bias=0.6)
    for n in (4.0, 6.2, 8.4, 10.6):
        y = 12.8 + (n - 1.0) * (4.6 - 12.8) / 13.4
        g.line(n - 0.4, y - 1.2, n + 0.4, y + 1.2, "lthr", 1.1, tone=0)
    g.line(3.0, 11.8, 11.6, 8.0, "satin", 1.15, tone=2)
    g.dot(1.0, 12.8, "wood", 0, 1.05)
    k = (12.4, 3.0) if ph == 0 else (12.0, 3.6)
    g.tube([k, (k[0] + 2.2, k[1] - 2.2)], [0.5, 0.3], "steel", 1.3, flat=3)
    if ph:
        g.dot(13.6, 0.6, "wood", 4, 1.3); g.dot(14.6, 1.6, "wood", 3, 1.3)


def draw_gamblers_coin(g, ph):
    if ph == 0:
        g.ell(8.0, 8.0, 6.4, 6.4, "gold", 1.0, bias=0.1)
        g.arc(8.0, 8.0, 4.8, 0, 360, "gold", 1.01, tone=1, step=12)
        # a crown struck in relief: lit faces, a shadow under it
        crown = [(4.8, 10.0), (11.2, 10.0), (11.2, 6.0), (9.6, 7.6), (8.0, 5.0), (6.4, 7.6), (4.8, 6.0)]
        g.poly([(x + 0.6, y + 0.6) for (x, y) in crown], "gold", 1.015, flat=0)
        g.poly(crown, "gold", 1.02, flat=3)
        g.line(4.8, 9.2, 11.2, 9.2, "gold", 1.03, tone=2)
        g.dot(8.0, 4.8, "gold", 4, 1.03)
        g.dot(5.0, 4.0, "gold", 4, 1.03); g.dot(4.2, 4.8, "gold", 4, 1.03)
    else:
        g.ell(8.0, 8.0, 2.6, 6.4, "gold", 1.0, bias=0.1)
        g.line(9.4, 2.6, 9.4, 13.4, "gold", 1.01, tone=1)
        g.glint(12.2, 3.0, big=True)
        g.dot(3.2, 12.2, "gold", 3, 1.1)


@V2.accent("satin")
def draw_bandage(g, ph):
    # a roll of linen seen side-on, its loose end trailing across the bottom, a patch with a red cross pinned on
    g.tube([(9.4, 12.4), (12.4, 12.6), (14.6, 11.6)], [0.9, 0.9, 0.8], "linen", 0.9, bias=0.2)
    g.poly([(2.0, 4.0), (9.0, 4.0), (9.0, 11.2), (2.0, 11.2)], "linen", 1.0, curve=-0.9, normal=(0.0, -0.6, 1.0), bias=0.1)
    for y in (6.2, 9.0):
        g.line(2.0, y, 9.0, y, "linen", 1.01, tone=1)
    g.ell(9.0, 7.6, 1.8, 3.6, "linen", 1.02, bias=0.25)
    g.ell(9.0, 7.6, 0.8, 1.6, "linen", 1.03, flat=0)
    g.poly([(3.0, 5.8), (6.8, 5.8), (6.8, 9.6), (3.0, 9.6)], "poster", 1.1, flat=2)
    g.poly([(4.4, 6.4), (5.4, 6.4), (5.4, 9.0), (4.4, 9.0)], "satin", 1.11, flat=2)
    g.poly([(3.6, 7.2), (6.2, 7.2), (6.2, 8.2), (3.6, 8.2)], "satin", 1.11, flat=2)
    for (x, y) in ((3.0, 5.8), (6.8, 5.8), (3.0, 9.6), (6.8, 9.6)):
        g.dot(x, y, "lthr", 1, 1.12)
    g.line(2.4, 4.2, 6.0, 4.2, "linen", 1.02, tone=4)
    if ph:
        g.dot(14.6, 12.8, "linen", 4, 1.0)


@V2.accent("satin")
def draw_wanted_poster(g, ph):
    g.poly([(2.0, 2.0), (14.0, 2.0), (14.0, 12.4 + ph * 0.6), (12.4, 14.6), (2.0, 14.6)], "poster", 1.0,
           normal=(-0.2, -0.3, 1.0), bias=0.1)
    g.poly([(14.0, 12.4 + ph * 0.6), (12.4, 14.6), (12.6, 12.6)], "poster", 1.01, flat=1)
    # a skull with a red cross through it, lines of text below, a nail at the top
    g.ell(8.0, 7.2, 2.8, 2.6, "lthr", 1.05, flat=1)
    g.dot(7.0, 7.2, "poster", 2, 1.06); g.dot(9.0, 7.2, "poster", 2, 1.06)
    g.line(4.4, 4.0, 11.6, 10.6, "satin", 1.1, tone=2)
    g.line(11.6, 4.0, 4.4, 10.6, "satin", 1.1, tone=2)
    for x in range(4, 12, 2):
        g.dot(x, 12.6, "lthr", 2, 1.05)
    g.ell(8.0, 2.0, 0.8, 0.8, "steel", 1.2)


def draw_iron_boots(g, ph):
    g.poly([(4.0, 1.6), (10.0, 1.6), (10.0, 9.2), (4.0, 9.2)], "iron", 1.0, curve=0.8, bias=0.3)
    g.poly([(4.0, 8.6), (11.6, 8.6), (14.6, 10.6), (14.6, 13.6), (4.0, 13.6)], "iron", 1.05, curve=0.2, bias=0.3)
    g.ell(7.0, 1.8, 3.0, 0.8, "iron", 1.06, bias=0.2)
    g.line(4.0, 14.0, 14.6, 14.0, "iron", 1.07, tone=0)
    for y in (4.4, 7.4):
        g.line(4.0, y, 10.0, y, "iron", 1.06, tone=1)
    g.line(11.6, 8.8, 13.6, 10.6, "iron", 1.06, tone=1)
    for (x, y) in ((5.2, 5.6), (8.6, 5.6), (5.2, 8.4), (8.6, 8.4), (12.4, 12.0)):
        g.dot(x, y, "steel", 4, 1.1)
    if ph:
        g.glint(5.6, 3.0)


@V2.accent("ice")
def draw_skeleton_key(g, ph):
    # a skull for the bow, a bone shaft, the bit hanging down at the end
    g.tube([(6.0, 7.4), (14.6, 9.6)], [0.9], "ivory", 0.9, bias=0.2)
    g.poly([(11.0, 9.0), (12.2, 9.4), (12.2, 11.6), (11.0, 11.6)], "ivory", 0.92, flat=2)
    g.poly([(13.0, 9.6), (14.4, 10.0), (14.4, 12.4), (13.0, 12.4)], "ivory", 0.92, flat=2)
    g.ell(4.6, 4.8, 3.4, 3.2, "ivory", 1.0, bias=0.2)
    g.ell(4.8, 7.2, 2.0, 1.2, "ivory", 1.0, bias=0.1)
    g.ell(3.4, 4.8, 0.9, 0.9, "blk", 1.1, flat=0); g.ell(6.0, 4.8, 0.9, 0.9, "blk", 1.1, flat=0)
    g.dot(4.7, 6.4, "blk", 1, 1.1)
    if ph:
        g.glint(1.4, 1.4)
    else:
        g.dot(14.6, 13.4, "ice", 4, 1.2)


@V2.accent("seed")
def draw_gilded_heart(g, ph):
    s = 1.0 if ph == 0 else 1.06
    p = g.ell(5.4, 6.2, 3.6 * s, 3.4 * s, "gold", 1.0, bias=0.1)
    g.ell(10.6, 6.2, 3.6 * s, 3.4 * s, "gold", 1.0, part=p, bias=0.1)
    g.poly([(1.9, 7.0), (14.1, 7.0), (8.0, 14.6 if ph == 0 else 15.0)], "gold", 1.0, curve=0.9, part=p, bias=0.1)
    g.ell(8.0, 8.4, 1.8, 2.0, "seed", 1.1, bias=0.2)
    g.dot(7.4, 7.6, "white", 4, 1.12)
    g.line(3.4, 4.4, 4.4, 3.6, "gold", 1.05, tone=4)
    if ph:
        g.glint(13.2, 2.2)


ARTIFACTS = [
    ("PartyHat", "Party Hat", draw_party_hat), ("BardLute", "Bard's Lute", draw_bard_lute),
    ("PetFerret", "Pet Ferret", draw_pet_ferret), ("BubblePipe", "Bubble Pipe", draw_bubble_pipe),
    ("RubberDuck", "Rubber Duck", draw_rubber_duck), ("FireflyJar", "Firefly Jar", draw_firefly_jar),
    ("DancingShoes", "Dancing Shoes", draw_dancing_shoes), ("Whetstone", "Whetstone", draw_whetstone),
    ("PhoenixFeather", "Phoenix Feather", draw_phoenix_feather), ("SiphonGem", "Siphon Gem", draw_siphon_gem),
    ("GluttonsFork", "Glutton's Fork", draw_gluttons_fork), ("TallyStick", "Tally Stick", draw_tally_stick),
    ("GamblersCoin", "Gambler's Coin", draw_gamblers_coin), ("Bandage", "Patchwork Bandage", draw_bandage),
    ("WantedPoster", "Wanted Poster", draw_wanted_poster), ("IronBoots", "Iron Boots", draw_iron_boots),
    ("SkeletonKey", "Skeleton Key", draw_skeleton_key), ("GildedHeart", "Gilded Heart", draw_gilded_heart),
]
DRAW = {k: fn for k, _, fn in ARTIFACTS}


def icon_cv(key, ph, S=1.0):
    """An artifact icon as a Cv (cell coordinates), for the world effects that carry it (party hat, key, heart)."""
    im, _ = V2.render(DRAW[key], ph, S=S)
    c = Cv()
    p = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if p[x, y][3]: c.put(x, y, p[x, y][:3])
    return c


# ----------------------------------------------------------------------------------------------- potions (16x16 icon)
POTIONS = {
    # id: (name, liquid ramp light->dark (3), shape, extra)
    "TrollMarrow": ("Troll Marrow", ("9aa064", "6e7a3a", "48552a"), "round", "bone"),
    "WyrmBlood": ("Wyrm Blood", ("e0503a", "a82224", "6a1018"), "round", "ember"),
    "HaresDew": ("Hare's Dew", ("b6ecd8", "78c8b4", "4a9688"), "tall", "leaf"),
    "BerserkerGrog": ("Berserker's Grog", ("c87838", "9a4a20", "6a2c14"), "jug", "foam"),
    "Stoneskin": ("Stoneskin Draught", ("aaa8a0", "7c7a74", "56544e"), "square", "chip"),
    "Quicksilver": ("Quicksilver", ("eef2f8", "b8c0cc", "7a8494"), "vial", "glint"),
    "ChaosBrew": ("Chaos Brew", ("c070e0", "7a38b0", "4a1a6e"), "round", "swirl"),
}
GLASS_RIM = hx("8e865e")
GLASS_RIM_L = hx("a8926c")
GLASS_TAN = hx("bea984")
GLASS_TAN_D = hx("a68e66")
CORK = hx("8d5e42")
CORK_D = hx("785442")
GLINT = hx("e7dfd2")
BASE = hx("847557")


def potion_shape(shape, S):
    """(neck rows, body mask) for a vanilla-style bottle at scale S (1 = 16x16 icon, 2 = the bubble)."""
    pass


def potion_big(pid, ph):
    """The shop picture: a vanilla-style potion (cf. PotionLargeGreen 13x22, PotionVialBlue 6x21) in a 34x41 cell."""
    name, liq, shape, extra = POTIONS[pid]
    L, M, D = (hx(x) for x in liq)
    c = Cv()
    cx = 17
    if shape == "vial":
        top, bot = 10, 31
        for y in range(top + 3, bot):
            c.put(cx - 2, y, GLASS_TAN); c.put(cx + 2, y, GLASS_TAN_D)
            for x in (cx - 1, cx, cx + 1):
                if y >= top + 7: c.put(x, y, L if x < cx else (M if x == cx else D))
                else: c.put(x, y, GLASS_TAN if x < cx + 1 else GLASS_TAN_D)
        for x in (cx - 1, cx, cx + 1): c.put(x, bot, BASE)
        body_top = top + 7
    else:
        if shape == "round":
            rx, ry, by = 6.4, 6.0, 25.0
        elif shape == "jug":
            rx, ry, by = 6.8, 5.6, 25.4
        elif shape == "square":
            rx, ry, by = 6.0, 6.0, 25.0
        else:  # tall
            rx, ry, by = 4.6, 7.6, 23.4
        top = int(by - ry) - 9
        # neck (glass), cork
        for y in range(top + 2, int(by - ry) + 1):
            c.put(cx - 1, y, GLASS_TAN); c.put(cx, y, GLASS_TAN); c.put(cx + 1, y, GLASS_TAN_D)
        if shape == "jug":   # a jug handle on the right
            for y in range(int(by - ry) - 1, int(by) - 1): c.put(cx + int(rx) + 1, y, GLASS_RIM)
            c.put(cx + int(rx), int(by - ry) - 1, GLASS_RIM)
        c.put(cx - 2, int(by - ry), GLASS_TAN); c.put(cx + 2, int(by - ry), GLINT)
        fill = by - ry * 0.25
        for y in range(int(by - ry), int(by + ry) + 1):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if shape == "square":
                    inside = abs(x - cx) <= rx - (1 if abs(y - by) > ry - 1 else 0) and abs(y - by) <= ry
                    edge = abs(x - cx) > rx - 1 or abs(y - by) > ry - 1
                else:
                    d = ((x - cx) / rx) ** 2 + ((y - by) / ry) ** 2
                    inside = d <= 1.0
                    dd = ((x - cx) / (rx - 1)) ** 2 + ((y - by) / (ry - 1)) ** 2
                    edge = dd > 1.0
                if not inside: continue
                if edge:
                    c.put(x, y, GLASS_RIM if x <= cx + 2 else hx("5b5d40") if extra != "ember" else hx("5a3a30"))
                elif y < fill - (ry * 0.9 if shape != "tall" else ry * 1.2):
                    c.put(x, y, GLASS_TAN if x < cx + 2 else GLASS_TAN_D)        # empty glass above the liquid
                else:
                    c.put(x, y, L if x < cx - 1 else (M if x < cx + 2 else D))
        for x in range(int(cx - rx) + 2, int(cx + rx) - 1): c.put(x, int(by + ry) + 1, BASE)
        body_top = int(by - ry)
    # cork
    for y in range(top - 1, top + 2):
        c.put(cx - 1, y, CORK); c.put(cx, y, CORK); c.put(cx + 1, y, CORK_D)
    c.put(cx, top - 2, CORK_D) if shape != "vial" else None
    # glints
    gx = cx + (3 if shape != "vial" else 1)
    c.put(gx, body_top + 3, GLINT); c.put(gx, body_top + 4, GLINT)
    # extras
    if extra == "bone":
        for x, y in ((cx - 3, 26), (cx - 2, 25), (cx - 1, 25), (cx, 26), (cx + 1, 25)):
            c.put(x, y + (ph and -1), hx("e8dcb4"))
    elif extra == "ember":
        for x, y in ((cx - 2, 24 - ph), (cx + 2, 27), (cx, 22 + ph)):
            c.put(x, y, hx("ffb070"))
    elif extra == "leaf":
        c.put(cx + 2, top, hx("7fb04a")); c.put(cx + 3, top - 1, hx("96ce60")); c.put(cx + 3, top, hx("5e963c"))
        c.put(cx - 1, 20 + ph, hx("e6fff6"))
    elif extra == "foam":
        for x in range(cx - 4, cx + 4):
            c.put(x, 20 - (x % 2) - ph * (x % 3 == 0), hx("f0e4c8"))
    elif extra == "chip":
        for x, y in ((cx - 3, 24), (cx + 1, 27), (cx - 1, 29 - ph)): c.put(x, y, hx("4a4844"))
    elif extra == "glint":
        c.put(cx - 1, 24 - ph * 3, hx("ffffff")); c.put(cx, 27 + ph, hx("ffffff"))
    elif extra == "swirl":
        sw = [hx("ff9a4a"), hx("7aff8a"), hx("ffe060")]
        for i, (x, y) in enumerate(((cx - 3, 23), (cx - 1, 22), (cx + 1, 24), (cx + 2, 27), (cx, 29), (cx - 3, 27))):
            c.put(x, y, sw[(i + ph) % 3])
    # bubbles rising out of the cork on frame 1 (the shop picture's little life)
    if ph:
        c.put(cx + 1, top - 4, GLINT); c.put(cx - 1, top - 6, hx("d0c8b8"))
    else:
        c.put(cx, top - 4, hx("d0c8b8"))
    return c


def potion_icon(pid, ph):
    """16x16 icon: the same bottle at half size, with a dark rim in its own colours so it reads on the vault grid."""
    name, liq, shape, extra = POTIONS[pid]
    L, M, D = (hx(x) for x in liq)
    c = Cv()
    cx = 8
    if shape == "vial":
        for y in range(4, 14):
            for x in (7, 8, 9):
                c.put(x, y, (L if x == 7 else M if x == 8 else D) if y >= 7 else (GLASS_TAN if x < 9 else GLASS_TAN_D))
        neck = 4
    else:
        rx, ry, by = {"round": (4.2, 4.0, 10.0), "jug": (4.6, 3.8, 10.4), "square": (4.0, 4.0, 10.0), "tall": (3.2, 4.2, 10.2)}[shape]
        for y in range(int(round(by - ry)) - 3, int(round(by - ry)) + 1):
            c.put(7, y, GLASS_TAN); c.put(8, y, GLASS_TAN); c.put(9, y, GLASS_TAN_D)
        for y in range(int(by - ry), int(by + ry) + 1):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if shape == "square":
                    if abs(x - cx) > rx or abs(y - by) > ry: continue
                else:
                    if ((x - cx) / rx) ** 2 + ((y - by) / ry) ** 2 > 1.0: continue
                c.put(x, y, L if x < cx - 1 else (M if x < cx + 1 else D))
        if shape == "jug":
            for y in range(int(by - 2), int(by + 2)): c.put(cx + int(rx) + 1, y, GLASS_RIM)
        neck = int(round(by - ry)) - 3
    for x in (7, 8, 9): c.put(x, neck - 1, CORK if x < 9 else CORK_D)
    c.put(8, neck - 2, CORK)
    c = selout(c)
    c.put(10 if shape != "vial" else 8, 8, GLINT)
    acc = {"bone": hx("e8dcb4"), "ember": hx("ffb070"), "leaf": hx("96ce60"), "foam": hx("f0e4c8"),
           "chip": hx("3a3834"), "glint": hx("ffffff"), "swirl": hx("7aff8a")}[extra]
    if extra == "leaf": c.put(10, neck - 1, acc); c.put(11, neck - 2, acc)
    elif extra == "foam":
        for x in range(5, 11): c.put(x, 7 - (x % 2), acc)
    else: c.put(7, 11 - ph, acc)
    if ph: c.put(9, neck - 3, GLINT)
    return c


# ------------------------------------------------------------------------------------------------------- HUD (11x7)
HUD = {
    # hand-drawn 11 x 7 HUD icons; '.' clear
    "PartyHat": (["....y......",
                  "....P......",
                  "...PTP.....",
                  "..TPPTP....",
                  ".PPTTPPT...",
                  "GGGGGGGGG..",
                  "..........."], {"y": "fff8c4", "P": "d04e98", "T": "33a0a0", "G": "d69e3e"}),
    "BardLute": ([".........ww",
                  "........w..",
                  "..bbb.ww...",
                  ".bBBkw.....",
                  ".bBkBb.....",
                  "..bBbb.....",
                  "...bb......"], {"w": "5e3a22", "b": "8a5a32", "B": "b4844c", "k": "1e1a1c"}),
    "PetFerret": (["...........",
                   ".ff........",
                   "fkFf.....t.",
                   "cfff.....t.",
                   "..ffffffft.",
                   "..fFFFFFf..",
                   "...f...f..."], {"f": "6a4426", "F": "c89a62", "k": "1e1a1c", "c": "ecd2a0", "t": "9a6a3c"}),
    "BubblePipe": ([".o.....o...",
                    "o.o...o.o..",
                    ".o.....o...",
                    "......ww...",
                    "......wWw..",
                    ".wwwwwwWw..",
                    "i..........",], {"o": "78dcd0", "w": "5e3a22", "W": "b4844c", "i": "9c9aa4"}),
    "RubberDuck": (["..yy.......",
                    ".yYyy......",
                    "oyky.......",
                    "..yyyyyy.y.",
                    "..yYYYYyyy.",
                    "...yyyyyy..",
                    "..........."], {"y": "f2c62a", "Y": "ffe66a", "k": "1e1a1c", "o": "f08a26"}),
    "FireflyJar": (["..wwwwww...",
                    "..gddddg...",
                    "..gdydyg...",
                    "..gdddyg...",
                    "..gydddg...",
                    "..gggggg...",
                    "..........."], {"w": "8a5a32", "g": "86a8c0", "d": "2a3640", "y": "fffbb0"}),
    "DancingShoes": ([".p.....s...",
                      "..p...sYs..",
                      ".rr.p..s...",
                      ".rRr.rr....",
                      ".rrRrrRr...",
                      "..kk.rrRr..",
                      "......kkk.."], {"p": "f48cc4", "r": "c8342e", "R": "f0644a", "k": "2a1416", "s": "fff8c4", "Y": "ffffff"}),
    "Whetstone": (["......i..y.",
                   ".....iI.yYy",
                   "....iI...y.",
                   "..sSSs.....",
                   ".sSSSSs....",
                   "..ssSSss...",
                   "....sss...."], {"i": "6c6a74", "I": "cfcdd6", "s": "58585f", "S": "9c9ca4", "y": "ffe28c", "Y": "ffffff"}),
    "PhoenixFeather": ([".........yo",
                        "........ro.",
                        ".......rOr.",
                        ".....rOOr..",
                        "...rOOr....",
                        "..rOr......",
                        ".c........."], {"y": "ffe66a", "o": "f08a26", "O": "ffbe4e", "r": "c8342e", "c": "efe0bc"}),
    "SiphonGem": (["w....v....w",
                   ".w..vVv..w.",
                   "...vVVvv...",
                   "...vVvvn...",
                   "....vvn....",
                   "...i.n.i...",
                   "....iii...."], {"w": "c8a8ff", "v": "7e46b8", "V": "e6d2ff", "n": "4e2678", "i": "9c9aa4"}),
    "GluttonsFork": ([".......rr..",
                      "......rRrr.",
                      "......rrrr.",
                      ".....iiii..",
                      "....iI.....",
                      "..iI.......",
                      "iI........."], {"r": "c8342e", "R": "f0644a", "i": "6c6a74", "I": "cfcdd6"}),
    "TallyStick": (["..........w",
                    "........wWw",
                    "......wkWw.",
                    "....wkWw...",
                    "..wkWw.....",
                    "wWWw.......",
                    "ww........."], {"w": "8a5a32", "W": "d8ae72", "k": "1e1a1c"}),
    "GamblersCoin": (["...ggggg...",
                      "..gGYYYgg..",
                      ".gGYkYkYg..",
                      ".gGYYYYYg..",
                      ".gGYkkkYg..",
                      "..ggYYYg...",
                      "...ggggg..."], {"g": "9a6426", "G": "d69e3e", "Y": "ffe28c", "k": "9a6426"}),
    "Bandage": (["...........",
                 ".ccc...ppp.",
                 "cCCCc..prp.",
                 "cCkCc..ppp.",
                 "cCCCcccc...",
                 ".ccc...ccc.",
                 "..........."], {"c": "8a7e72", "C": "e0d6c4", "k": "6a6056", "p": "c8a476", "r": "c8342e"}),
    "WantedPoster": (["....i......",
                      ".pppppppp..",
                      ".prpkkprp..",
                      ".ppkrrkpp..",
                      ".prpkkprp..",
                      ".pppppp.p..",
                      "..........."], {"i": "9c9aa4", "p": "c8aa76", "r": "c8342e", "k": "4a3628"}),
    "IronBoots": (["..iii......",
                   "..iIi......",
                   "..iIi......",
                   "..iIiiiii..",
                   "..iIIIIIi..",
                   "..kkkkkkk..",
                   "..........."], {"i": "46444c", "I": "9c9aa4", "k": "2c2a30"}),
    "SkeletonKey": ([".bbb.......",
                     "bkbkb......",
                     "bbbbb......",
                     ".bBbbbbbbb.",
                     ".......b.b.",
                     ".......b.b.",
                     "..........."], {"b": "ccc0a0", "B": "fffbef", "k": "1e1a1c"}),
    "GildedHeart": ([".ggg.ggg...",
                     "gGYgggYgg..",
                     "gYgggggg...",
                     ".gggrggg...",
                     "..gggggg...",
                     "...gggg....",
                     "....gg....."], {"g": "d69e3e", "G": "fff6d0", "Y": "ffe28c", "r": "c8342e"}),
}


# ------------------------------------------------------------------------------------------------- pedestal drawings
# id (ItemDef id) -> (grid, palette). Read by pedestal_rigs.py. Bottom row sits on canvas row 31 (potions: row 32 like
# the vanilla 5x7 bottles), no outline, flat tones, the shadow is added by pedestal_rigs.
def _potion_ped(liq, cork="8d5e42", shape="round"):
    L, M, D = liq
    if shape == "vial":
        return ([".c.", ".t.", ".t.", ".L.", ".M.", ".D."],
                {"c": cork, "t": "bea984", "L": L, "M": M, "D": D})
    if shape == "tall":
        return ([".c.", ".t.", "tLt", "LMD", "LMD", "LMD", ".b."], {"c": cork, "t": "bea984", "L": L, "M": M, "D": D, "b": "847557"})
    if shape == "square":
        return ([".c..", ".t..", "LLMD", "LMMD", "LMDD", "bbbb"], {"c": cork, "t": "bea984", "L": L, "M": M, "D": D, "b": "847557"})
    if shape == "jug":
        return (["..c..", "..t..", ".LMDr", "LLMDr", "LMMDr", ".bbb."], {"c": cork, "t": "bea984", "L": L, "M": M, "D": D, "b": "847557", "r": "8e865e"})
    return (["..c..", "..t..", ".tdt.", "LMMDD", "LMMDD", ".bbb."], {"c": cork, "t": "bea984", "d": "dcd8d0", "L": L, "M": M, "D": D, "b": "847557"})


PEDESTALS = {
    "PotionTrollMarrow": _potion_ped(("7f8351", "6e7a3a", "48552a")),
    "PotionWyrmBlood": _potion_ped(("c8423a", "a82224", "6a1018")),
    "PotionHaresDew": _potion_ped(("9ad8c4", "78c8b4", "4a9688"), shape="tall"),
    "PotionBerserkerGrog": _potion_ped(("b86c34", "9a4a20", "6a2c14"), shape="jug"),
    "PotionStoneskin": _potion_ped(("9a9890", "7c7a74", "56544e"), shape="square"),
    "PotionQuicksilver": _potion_ped(("dce2ea", "b8c0cc", "7a8494"), shape="vial"),
    "PotionChaosBrew": _potion_ped(("b064d0", "7a38b0", "4a1a6e")),
    "ArtifactPartyHat": (["..y..", "..P..", ".PTP.", ".TPP.", "PPTPT", "GGGGG"], {"y": "fff0a0", "P": "c04a8c", "T": "3a9a96", "G": "c89a48"}),
    "ArtifactBardLute": ([".....ww", "....w..", ".bbw...", "bBkb...", "bBBb...", ".bb...."], {"w": "5e3a22", "b": "7e5230", "B": "b4844c", "k": "2a2226"}),
    "ArtifactPetFerret": (["ff.....", "kFf..t.", "cffffft", ".fFFFf.", ".f..f.."], {"f": "6a4426", "F": "c89a62", "k": "1e1a1c", "c": "ecd2a0", "t": "9a6a3c"}),
    "ArtifactBubblePipe": (["o...o", "...ww", "..wWw", "wwwW."], {"o": "78c8c0", "w": "5e3a22", "W": "a8783e"}),
    "ArtifactRubberDuck": ([".yy...", "oky...", ".yyyyy", ".yYYy.", "..yy.."], {"y": "e0b628", "Y": "ffe066", "k": "1e1a1c", "o": "e07e24"}),
    "ArtifactFireflyJar": (["wwww", "gdyg", "gydg", "gddg", "gggg"], {"w": "7e5230", "g": "86a0b4", "d": "2a3640", "y": "f4f0a0"}),
    "ArtifactDancingShoes": (["p..p...", "rr.rr..", "rRrrRr.", "kkkkkk."], {"p": "e486b8", "r": "b83030", "R": "e06048", "k": "2a1416"}),
    "ArtifactWhetstone": (["....i", "...I.", ".sSs.", "sSSSs", ".sss."], {"i": "6c6a74", "I": "c8c6d0", "s": "58585f", "S": "9c9ca4"}),
    "ArtifactPhoenixFeather": ([".....y", "....ro", "...rO.", "..rO..", ".rO...", "c....."], {"y": "ffe066", "o": "e88426", "O": "f8b04a", "r": "b83030", "c": "e0d0b0"}),
    "ArtifactSiphonGem": ([".v.", "vVv", "vvn", ".n.", "i.i"], {"v": "7e46b8", "V": "d8c0f8", "n": "4e2678", "i": "9c9aa4"}),
    "ArtifactGluttonsFork": (["....rr", "...rRr", "..ii..", ".iI...", "iI...."], {"r": "b83030", "R": "e06048", "i": "6c6a74", "I": "c8c6d0"}),
    "ArtifactTallyStick": ([".....w", "...wkW", ".wkWw.", "wWw..."], {"w": "7e5230", "W": "c8a066", "k": "2a2226"}),
    "ArtifactGamblersCoin": ([".ggg.", "gYkYg", "gYYYg", ".ggg."], {"g": "9a6426", "Y": "e8c860", "k": "9a6426"}),
    "ArtifactBandage": ([".cc..pp", "cCkc.rp", "cCCcccc", ".cc...."], {"c": "8a7e72", "C": "dcd2c0", "k": "6a6056", "p": "c0a070", "r": "b83030"}),
    "ArtifactWantedPoster": (["..i..", "ppppp", "prkrp", "pkrkp", "ppppp"], {"i": "9c9aa4", "p": "c8aa76", "r": "b83030", "k": "4a3628"}),
    "ArtifactIronBoots": (["ii...", "iI...", "iIiii", "iIIIi", "kkkkk"], {"i": "46444c", "I": "8c8a94", "k": "2c2a30"}),
    "ArtifactSkeletonKey": (["bb.....", "kbbbbbb", "bb...bb"], {"b": "ccc0a0", "k": "3a3028"}),
    "ArtifactGildedHeart": (["gg.gg", "gYggg", ".grg.", "..g.."], {"g": "c8963a", "Y": "fff0b0", "r": "b83030"}),
}


# ============================================================================================================ build
def icon_img(c):
    return c.image(16, 16)


def check_cell(name, c):
    b = c.bbox()
    if b and (b[0] < 0 or b[1] < 0 or b[2] > 15 or b[3] > 15):
        print("WARNING out of cell:", name, b)


def hud_img(grid, pal):
    im = Image.new("RGBA", (11, 7), (0, 0, 0, 0))
    p = im.load()
    for y, row in enumerate(grid):
        assert len(row) <= 11, (row, len(row))
        for x, ch in enumerate(row):
            if ch != ".": p[x, y] = hx(pal[ch]) + (255,)
    return V2.crawl_image(im)


def build():
    os.makedirs(OUT, exist_ok=True)
    tiles = []
    for key, nice, fn in ARTIFACTS:
        ims, bubbles = [], []
        for ph in (0, 1):
            im, lost = V2.render(fn, ph)
            if lost: print("WARNING out of cell:", key, ph, lost)
            ims.append(im)
            pic, _ = V2.render(fn, ph, S=V2.BUBBLE_SCALE)
            b = Image.new("RGBA", (34, 41), (0, 0, 0, 0))
            b.alpha_composite(pic, ((34 - pic.width) // 2, 41 - pic.height - 6))
            bubbles.append(b)
        write_sheet("Icon" + key, ims, 16, 16, [("Idle", [0, 1], [0.9, 0.25])], cols=2)
        write_sheet("Icon" + key + "Bubble", bubbles, 34, 41, [("Bubble", [0, 1], [0.9, 0.25])], cols=2)
        g, pal = HUD[key]
        write_sheet("Icon" + key + "Hud", [hud_img(g, pal)], 11, 7, [("Hud", [0], [0.5])], cols=1)
        tiles.append((key, nice, "artifact", ims, bubbles, hud_img(g, pal)))
    for key, (nice, liq, shape, extra) in POTIONS.items():
        frames = [potion_icon(key, 0), potion_icon(key, 1)]
        for f in frames: check_cell(key, f)
        ims = [V2.crawl_image(icon_img(f)) for f in frames]
        write_sheet("Icon" + key, ims, 16, 16, [("Idle", [0, 1], [0.9, 0.25])], cols=2)
        bubbles = [V2.crawl_image(potion_big(key, ph).image(34, 41)) for ph in (0, 1)]
        write_sheet("Icon" + key + "Bubble", bubbles, 34, 41, [("Bubble", [0, 1], [0.9, 0.25])], cols=2)
        tiles.append((key, nice, "potion", ims, bubbles, None))
    board(tiles)
    print("items3 icons:", len(tiles))


def board(tiles, S=4):
    os.makedirs(BOARDS, exist_ok=True)
    font = ImageFont.load_default(size=12)
    cols = 5
    tw, th = 16 * S * 2 + 34 * 3 + 52, 41 * 3 + 22
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new("RGBA", (cols * tw + 10, rows * th + 10), (28, 26, 32, 255))
    d = ImageDraw.Draw(im)
    for i, (key, nice, kind, icons, bubbles, hud) in enumerate(tiles):
        x0, y0 = 6 + (i % cols) * tw, 6 + (i // cols) * th
        for j, f in enumerate(icons):
            d.rectangle([x0 + j * (16 * S + 3), y0, x0 + j * (16 * S + 3) + 16 * S - 1, y0 + 16 * S - 1], fill=(40, 37, 46))
            im.alpha_composite(f.resize((16 * S, 16 * S), Image.NEAREST), (x0 + j * (16 * S + 3), y0))
        bx = x0 + 2 * (16 * S + 3) + 4
        d.rectangle([bx, y0, bx + 34 * 3 - 1, y0 + 41 * 3 - 1], fill=(52, 44, 40))
        im.alpha_composite(bubbles[0].resize((34 * 3, 41 * 3), Image.NEAREST), (bx, y0))
        im.alpha_composite(bubbles[0], (bx + 34 * 3 + 4, y0))
        if hud is not None:
            im.alpha_composite(hud.resize((44, 28), Image.NEAREST), (bx + 34 * 3 + 4, y0 + 46))
            im.alpha_composite(hud, (bx + 34 * 3 + 4, y0 + 78))
        d.text((x0, y0 + 41 * 3 + 4), nice, fill=(220, 210, 190), font=font)
    im.convert("RGB").save(os.path.join(BOARDS, "items3_icons.png"))


if __name__ == "__main__":
    build()
