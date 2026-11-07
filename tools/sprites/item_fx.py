"""ITEM FX: the hero-side world art of all 44 shop items (v0.8 art pass).

    python3 item_fx.py [outdir]          # default art/out_itemfx, writes every FxItem* sheet + TIMING.md

Every effect an item shows in the world is drawn here in the item's own look (matched to its shop icon in
art/out_items / art/out_icons_v2): projectiles, ground patches, runners, bursts, proc sparks, orbit plates and
the three follower tokens. Nothing is borrowed from a monster sheet.

Method (same family as zhekra_rigs.py / belmora_rigs.py): each frame is a fresh drawing from shaded primitives
(ellipses, tubes, polygons lit from the top-left), a 1 px dark outline where the thing is solid, then glow
pixels on top so cores stay bright on Crawl's dark floors.

Every sheet carries an "origin": [x, y] in its json: the cell pixel that sits on the effect's spawn point.
The C# side (ItemArt in src/CrawlFurther/Items/ItemFixes.cs) reads it and calls Strike.ArtAt, so art and hitbox can't
drift apart. Colliders are never sized from the art: each sheet is drawn to the collider its template already
has (listed in TIMING.md).
"""
import json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, SprRGB, PALETTE, pack, preview  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_OUT = os.path.join(ROOT, "art", "out_itemfx")

PALETTE.update({
    '0': (0x16, 0x12, 0x14),   # outline, warm black
    '`': (0x10, 0x12, 0x1c),   # outline, cool black
    # fire
    'a': (0x7a, 0x1c, 0x10), 'b': (0xc4, 0x40, 0x18), 'c': (0xf2, 0x8a, 0x26), 'd': (0xff, 0xd6, 0x5e), 'e': (0xff, 0xf6, 0xc8),
    # wax / tallow
    'f': (0x78, 0x62, 0x46), 'g': (0xb0, 0x98, 0x6c), 'h': (0xdc, 0xc8, 0x98), 'i': (0xf4, 0xea, 0xce),
    # bone
    'j': (0x5c, 0x50, 0x40), 'k': (0x96, 0x88, 0x6c), 'l': (0xcc, 0xc0, 0xa0), 'm': (0xf0, 0xea, 0xd4),
    # leaf green
    'n': (0x1e, 0x38, 0x1a), 'o': (0x36, 0x60, 0x28), 'p': (0x5e, 0x96, 0x3c), 'q': (0x96, 0xce, 0x60),
    # bark / earth
    'r': (0x34, 0x22, 0x18), 's': (0x5a, 0x3e, 0x28), 't': (0x86, 0x62, 0x3e),
    # spore purple
    'u': (0x36, 0x1a, 0x42), 'v': (0x66, 0x32, 0x78), 'w': (0x9c, 0x5a, 0xb0), 'x': (0xd4, 0x96, 0xe0),
    # toxic green
    'y': (0x28, 0x50, 0x14), 'z': (0x5a, 0x96, 0x1e), 'A': (0x96, 0xd6, 0x32), 'B': (0xd6, 0xff, 0x78),
    # glass
    'C': (0x3c, 0x50, 0x6e), 'D': (0x78, 0x96, 0xbe), 'E': (0xbe, 0xd6, 0xf0), 'F': (0xf5, 0xfa, 0xff),
    # shadow violet
    'G': (0x1e, 0x12, 0x2c), 'H': (0x42, 0x26, 0x60), 'I': (0x78, 0x4a, 0xaa), 'J': (0xba, 0x8c, 0xf0),
    # soul blue
    'L': (0x1c, 0x34, 0x6e), 'M': (0x36, 0x6e, 0xc8), 'N': (0x78, 0xbe, 0xff), 'O': (0xd2, 0xf0, 0xff),
    # bronze / gold
    'P': (0x5c, 0x3a, 0x14), 'Q': (0xa0, 0x6c, 0x22), 'R': (0xdc, 0xaa, 0x3c), 'S': (0xff, 0xe6, 0x8c),
    # sea
    'T': (0x10, 0x34, 0x3e), 'U': (0x1e, 0x64, 0x6e), 'V': (0x3c, 0xaa, 0xaa), 'W': (0x96, 0xe6, 0xdc), 'X': (0xe6, 0xff, 0xfa),
    # card cream / red / ink
    'Y': (0xe6, 0xdc, 0xbe), 'Z': (0xa0, 0x1e, 0x28), '1': (0xf0, 0x50, 0x46), '2': (0x28, 0x24, 0x30),
    # ice
    '3': (0x28, 0x46, 0x6e), '4': (0x5a, 0x8c, 0xbe), '5': (0xa0, 0xd2, 0xf0), '6': (0xe6, 0xf8, 0xff),
    # lightning
    '7': (0x3c, 0x3c, 0xa0), '8': (0x6e, 0x8c, 0xff), '9': (0xbe, 0xdc, 0xff), '!': (0xff, 0xff, 0xdc),
    # amber resin
    '@': (0x64, 0x32, 0x0c), '#': (0xa4, 0x58, 0x12), '$': (0xd6, 0x8e, 0x22), '%': (0xf4, 0xc4, 0x52), '^': (0xff, 0xec, 0xa4),
    # rot / blood red
    '&': (0x5a, 0x14, 0x18), '*': (0x96, 0x24, 0x24), '(': (0xd2, 0x46, 0x3c),
    # grey (cooldown, stone, iron)
    ')': (0x46, 0x46, 0x4e), '-': (0x6e, 0x6e, 0x78), '+': (0xa0, 0xa0, 0xaa),
    # silk, maggot flesh
    '=': (0xc8, 0xce, 0xdc), '[': (0x8c, 0x96, 0xaa), ']': (0xc8, 0xba, 0x96), '{': (0x96, 0x82, 0x60),
    # lilac string
    '<': (0x8a, 0x6a, 0xb4), '>': (0xd8, 0xc0, 0xff),
})

FIRE = "abcd"; FIRE_L = "bcde"
WAX = "fghi"; BONE = "jklm"; LEAF = "nopq"; BARK = "rst"; SPORE = "uvwx"; TOX = "yzAB"
GLASS = "CDEF"; SHADE = "GHIJ"; SOUL = "LMNO"; GOLD = "PQRS"; SEA = "TUVWX"; ICE = "3456"; VOLT = "789!"
AMBER = "@#$%^"; ROT = "&*("; GREY = ")-+"


# ------------------------------------------------------------------------------------------------ primitives
def pick(ramp, l):
    n = len(ramp)
    return ramp[max(0, min(n - 1, int((l + 1.0) * 0.5 * n)))]


def P(x, y):
    return int(round(x)), int(round(y))


def ell(c, cx, cy, rx, ry, ramp, ang=0.0, bias=0.0, over=True, shader=None, hollow=None):
    """Filled ellipse lit from the top-left; hollow=(inner fraction) leaves a ring."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = int(max(rx, ry)) + 2
    for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)) + 1):
        for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R)) + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            nu, nv = u / max(rx, 0.5), v / max(ry, 0.5)
            d = nu * nu + nv * nv
            if d > 1.0: continue
            if hollow is not None and d < hollow * hollow: continue
            wx, wy = nu * ca - nv * sa, nu * sa + nv * ca
            l = 0.8 * (-(wx + wy) / 1.414) + 0.35 * (1 - d) - 0.12 + bias
            ch = pick(ramp, l)
            if shader:
                ch = shader(nu, nv, d, l, ch, x, y)
                if ch is None: continue
            c.put(x, y, ch, over)


def ring(c, cx, cy, rx, ry, ch, step=None, over=True, gap=None, a0=0.0, a1=360.0):
    """Ellipse outline (1 px), optionally broken (gap(angle_deg) -> True skips)."""
    n = max(12, int(2 * math.pi * max(rx, ry) * 1.6))
    pts = set()
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        if gap and gap(a % 360): continue
        r = math.radians(a)
        pts.add(P(cx + rx * math.cos(r), cy + ry * math.sin(r)))
    for (x, y) in pts:
        cc = ch(x, y) if callable(ch) else ch
        if cc: c.put(x, y, cc, over)
    return pts


def tube(c, pts, radii, ramp, bias=0.0, over=True):
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        r0, r1 = radii[i], radii[i + 1]
        R = max(r0, r1) + 1
        L2 = (x1 - x0) ** 2 + (y1 - y0) ** 2
        for y in range(int(math.floor(min(y0, y1) - R)), int(math.ceil(max(y0, y1) + R)) + 1):
            for x in range(int(math.floor(min(x0, x1) - R)), int(math.ceil(max(x0, x1) + R)) + 1):
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / L2))
                qx, qy = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                r = r0 + (r1 - r0) * t
                ox, oy = x - qx, y - qy
                if math.hypot(ox, oy) > r + 0.15: continue
                l = bias if r < 0.75 else -(ox + oy) / (r * 1.414) * 0.9 + 0.15 + bias
                c.put(x, y, pick(ramp, l), over)


def line(c, x0, y0, x1, y1, ch, over=True):
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    for i, (x, y) in enumerate(pts):
        c.put(x, y, ch[i % len(ch)], over)
    return pts


def poly(c, pts, ch, over=True):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]; xj, yj = pts[j]
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                    inside = not inside
                j = i
            if inside:
                c.put(x, y, ch(x, y) if callable(ch) else ch, over)


def rot(p, deg, piv=(0.0, 0.0)):
    a = math.radians(deg)
    x, y = p[0] - piv[0], p[1] - piv[1]
    return piv[0] + x * math.cos(a) - y * math.sin(a), piv[1] + x * math.sin(a) + y * math.cos(a)


# each palette char -> the darkest tone of its own ramp: the rim a shape takes on its lower and right edges
DARK = {}
for _ramp in (FIRE_L, "abcde", WAX, BONE, LEAF, BARK, SPORE, TOX, GLASS, SHADE, SOUL, GOLD, SEA, ICE, VOLT, AMBER, ROT, GREY,
              "&*(Z1", "Y]{", "[=", "<>H"):
    for _c in _ramp: DARK.setdefault(_c, _ramp[0])
INKS = {"0", "`", "2"}      # the old black rings: now each pixel's own darkest tone


def outl(px, ch="0"):
    """Selective outline: only the lower and right edges get a 1 px rim (the shape sits on the floor and turns away
    from the top-left light), in each edge pixel's own darkest tone when ch is a black ink, else in ch. The upper and
    left edges stay lit, so the shape reads against the dark floor by value, like the vanilla effects."""
    out = dict(px)
    for (x, y), v in px.items():
        for dx, dy in ((1, 0), (0, 1)):
            k = (x + dx, y + dy)
            if k not in px and k not in out:
                out[k] = DARK.get(v, ch) if ch in INKS else ch
    return out


class Fr:
    """b: solid body (outlined), g: glow (no outline, on top), n: back layer (no outline, under)."""
    def __init__(self):
        self.b, self.g, self.n = Canvas(), Canvas(), Canvas()

    def done(self, o="0"):
        px = dict(self.n.px)
        body = outl(self.b.px, o) if (self.b.px and o) else dict(self.b.px)
        px.update(body)
        px.update(self.g.px)
        return Spr(px)


def fade(s, k=0.55):
    """The last frame of a pop-up: the same solid shape, dimmed toward the floor (reads as fading out; a checkerboard
    dissolve turned to noise at 1x)."""
    floor = (40, 34, 38)
    out = {}
    for p, v in s.px.items():
        c = PALETTE.get(v) if isinstance(v, str) else v
        if c: out[p] = tuple(int(a * k + f * (1 - k)) for a, f in zip(c, floor))
    return SprRGB(out)


def spr(c):
    return Spr(dict(c.px))


# ------------------------------------------------------------------------------------------------ the icons' own pen
# Effects that show an item's object (the skull, the die, the lantern, the followers...) draw it with the same pen and
# geometry as its shop icon (items_v2_icons.py / god_item_icons.py), so the thing in the world is the thing you bought.
sys.path.insert(0, HERE)
import items_v2_icons as V2  # noqa: E402
import god_item_icons as GI  # noqa: E402


def pen_spr(draw, ph=0, S=1.0, turn=0.0, at=(0.0, 0.0), remap=None):
    """An icon drawing at scale S, turned `turn` degrees, its cell centre placed at `at` -> SprRGB in fx coordinates."""
    g = V2.Pen(S, turn)
    draw(g, ph)
    n = int(round(16 * S)) + 10
    im, _ = g.image(n=n, remap=remap or V2.crawl_palette(getattr(draw, "accent", ())))
    p = im.load()
    ox, oy = int(round(at[0])), int(round(at[1]))
    return SprRGB({(x - n // 2 + ox, y - n // 2 + oy): p[x, y][:3] for y in range(n) for x in range(n) if p[x, y][3]})


def layered(*sprs):
    """Stack sprites (palette Spr or SprRGB), later ones on top -> SprRGB."""
    px = {}
    for s_ in sprs:
        for k, v in s_.px.items():
            px[k] = PALETTE[v] if isinstance(v, str) else v
    return SprRGB(px)


def grey(mat, tone):
    """Recolour for a spent follower: every material onto the cooldown grey ramp, its shading kept."""
    return PALETTE[")" if tone <= 1 else "-" if tone == 2 else "+"]


def sparks(c, n, cx, cy, r0, r1, chs, seed, t=1.0, yk=1.0, up=0.0):
    """n sparks flung from (cx,cy) outward between radii r0..r1 at time t (0..1), with a little gravity."""
    rnd = random.Random(seed)
    for k in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(r0, r1) * t
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r * yk - up * t + 6 * t * t * (1 if up else 0)
        ch = chs[k % len(chs)]
        c.put(*P(x, y), ch)
        if r > 2.5:   # a short streak back toward where it came from, so a spark reads as a spark, not a stray pixel
            c.put(*P(x - math.cos(a) * 1.2, y - math.sin(a) * 1.2 * yk), chs[(k + 1) % len(chs)], over=False)


# ------------------------------------------------------------------------------------------------ sheet writer
BUILT = {}       # name -> dict(cell, origin, anims, img, man, note)
ORDER = []


def fx(name, anims, cell, origin, outdir, note="", scale=6):
    """cell/origin are the intended size and anchor pixel; the cell grows (keeping the origin on the same art pixel)
    if a frame reaches past it, so nothing is ever clipped. The final origin is written into the json."""
    cw, ch = cell
    ox, oy = origin
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an, len(fr), len(du))
        for i, f in enumerate(fr):
            assert f.px, "%s/%s[%d] empty" % (name, an, i)
    allp = [p for _, fr, _ in anims for f in fr for p in f.px]
    x0 = min(p[0] for p in allp); x1 = max(p[0] for p in allp)
    y0 = min(p[1] for p in allp); y1 = max(p[1] for p in allp)
    gl, gt = max(0, -(x0 + ox)), max(0, -(y0 + oy))
    ox, oy = ox + gl, oy + gt
    cw, ch = max(cw + gl, x1 + ox + 1), max(ch + gt, y1 + oy + 1)
    if cw % 2: cw += 1
    cell, origin = (cw, ch), (ox, oy)
    img, man = pack(name, anims, cw, ch, (ox, oy), outdir)
    man["origin"] = [ox, oy]
    json.dump(man, open(os.path.join(outdir, name + ".json"), "w"))
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "origin": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img,
                   "man": man, "note": note}
    ORDER.append(name)
    print("built %-24s cell %2dx%-2d origin %2d,%-2d %s" % (name, cw, ch, ox, oy, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


# Per-frame durations each item effect took from the monster effect it stands in for. They are fixed here, as shipped,
# so the item's clip length and the frames the C# side hangs its damage on don't move when that monster's art is redrawn.
INHERITED = {
    ('FxEmberPatch', 'Loop'): [0.09, 0.09, 0.09, 0.09, 0.09, 0.09],
    ('FxWaxPuddle', 'Life'): [0.05, 0.05, 0.05, 0.05] + [0.3] * 18 + [0.12, 0.12, 0.12],
    ('FxBrine', 'Life'): [0.12, 0.12, 0.12] + [0.37] * 20 + [0.2, 0.2, 0.2],
    ('FxZhkAcidPool', 'Life'): [0.1, 0.1, 0.1] + [0.2] * 12 + [0.13, 0.13, 0.13],
    ('FxThornPatch', 'Life'): [0.1, 0.1, 0.1] + [0.4] * 18 + [0.15, 0.15, 0.15],
    ('FxSpikeRing', 'Play'): [0.05, 0.06, 0.07, 0.1],
    ('FxSeed', 'Burst'): [0.06, 0.06, 0.07, 0.1, 0.14],
    ('FxRootLine', 'Play'): [0.06, 0.05, 0.05, 0.12, 0.12, 0.08, 0.1],
    ('FxDecoyBurst', 'Play'): [0.04, 0.06, 0.07, 0.08, 0.1],
    ('FxSwapFlash', 'Play'): [0.04, 0.05, 0.06, 0.08, 0.1],
    ('FxBellRing', 'Play'): [0.05, 0.06, 0.07, 0.08, 0.1],
    ('FxZhkResinBurst', 'Play'): [0.05, 0.06, 0.07, 0.09, 0.12],
    ('FxYsvIcicle', 'Fall'): [0.12, 0.1, 0.1, 0.1, 0.08, 0.08, 0.06, 0.06],
    ('FxYsvIcicle', 'Shatter'): [0.05, 0.06, 0.07, 0.08, 0.1],
    ('FxYsvNova', 'Play'): [0.04, 0.05, 0.06, 0.07, 0.08, 0.1],
}


def god_durations(sheet, anim):
    """The per-frame durations an item effect keeps from the monster effect it replaced (see INHERITED)."""
    return list(INHERITED[(sheet, anim)])


# ================================================================================================ fire family
def flame_tongue(c, x, y, h, w, ph, ramp=FIRE_L, lean=0.0):
    """One upright flame: a teardrop (widest a third of the way up) that flickers; base at (x, y), tip h px up.
    Colour by distance from the axis and height: hot core low in the middle, dark red rim."""
    h = max(1.0, h)
    for k in range(int(h) + 1):
        t = k / h
        prof = math.sin(math.pi * min(1.0, 0.25 + t * 0.9)) if t < 0.83 else (1 - t) * 2.2
        half = w * prof * (0.92 + 0.16 * math.sin(ph * 2.1 + k))
        cx = x + lean * t * t * h * 0.5 + math.sin(ph + k * 0.9) * 0.7 * t
        r = int(math.floor(half + 0.5))
        for dx in range(-r, r + 1):
            e = abs(dx) / max(0.6, half + 0.3)
            l = 1.0 - e * 1.2 - t * 0.9
            c.put(*P(cx + dx, y - k), pick(ramp, l))


def ember_bolt(i, core=FIRE_L, tail="abc", hot="e", length=9, wob=1.0, halo=None):
    f = Fr()
    # streaming tail: three tongues of flame pulled back
    for s, (dy, ln) in enumerate(((0, length), (-1.6, length * 0.7), (1.6, length * 0.6))):
        for k in range(int(ln)):
            x = -1 - k
            y = dy * (k / ln) + math.sin(k * 0.8 + i * 1.7 + s) * 0.7 * wob
            ch = tail[min(len(tail) - 1, int(k / ln * len(tail)))]
            if (k + i + s) % 5 == 4 and k > ln * 0.5: continue
            f.n.put(*P(x, y), tail[::-1][min(len(tail) - 1, int(k / ln * len(tail)))] if k < 2 else ch)
    ell(f.g, 1.5, 0, 3.2, 2.5, core, bias=0.35)
    f.g.put(2, -1, hot); f.g.put(3, 0, hot); f.g.put(2, 0, hot)
    f.g.put(*P(-2 - (i % 2), -2 + (i % 3)), "d")
    if halo:
        for a in range(0, 360, 45):
            if (a // 45 + i) % 2 == 0:
                r = math.radians(a + i * 20)
                f.g.put(*P(1.5 + 4.6 * math.cos(r), 3.6 * math.sin(r)), halo)
    return f.done(None)


def ember_pop(i, n=5, ramp="bcde", smoke=")-"):
    c = Canvas()
    t = (i + 1) / n
    r = 1.5 + 6 * t
    if i < 3:
        ell(c, 0, 0, r * 0.6, r * 0.5, ramp[::-1] if i == 0 else ramp, bias=0.5 - t)
    sparks(c, 9, 0, 0, 3, 8, "dcbe" if i < 3 else "ba", seed=3 + i // 5, t=t)
    if i >= 2:
        for k in range(4):
            a = k * 1.6 + i
            c.put(*P(math.cos(a) * r * 0.5, -t * 4 - k % 2 + math.sin(a)), smoke[k % 2])
    return spr(c)


def build_fire(outdir):
    fly = [ember_bolt(i) for i in range(4)]
    pop = [ember_pop(i) for i in range(5)]
    fx("FxItemEmberVolley", [("Fly", fly, [0.06] * 4), ("Pop", pop, [0.04, 0.05, 0.06, 0.08, 0.1])], (22, 18), (12, 9), outdir,
       "Ember Volley flame bolt (DFX_skelMageNewProjectile box 11x10) + its wall/monster pop")
    fly = [ember_bolt(i, core="RSde", tail="QRd", hot="e", length=7, wob=0.6, halo="S") for i in range(4)]
    pop = []
    for i in range(5):
        c = Canvas()
        t = (i + 1) / 5
        if i < 4: ring(c, 0, 0, 2 + 6 * t, 1.5 + 4.5 * t, "S" if i < 2 else "R", gap=lambda a, i=i: (a // 30 + i) % 3 == 2)
        if i < 2: ell(c, 0, 0, 2.5 - i, 2 - i * 0.5, "dee", bias=0.4)
        sparks(c, 6, 0, 0, 2, 7, "eSd", seed=11, t=t)
        pop.append(spr(c))
    fx("FxItemWickBolt", [("Fly", fly, [0.06] * 4), ("Pop", pop, [0.04, 0.05, 0.06, 0.08, 0.1])], (22, 18), (12, 9), outdir,
       "Saint's Wick holy candle-flame bolt with a gold halo + pop")


def floor_fire(i, kind, spread=1.0, fade=0.0, seed=1):
    """Burning floor patches, each in its item's look:
    wick   - Wickwalk: separate drips of molten wax, each burning on its own little wick, embers between;
    votive - Votive Candle: a pool of spilled tallow with three squat votive candles burning in it;
    slick  - Wax Slick set alight: one wide, low sheet of fire across the wax with smoke rising."""
    c = Canvas(); fl = Canvas(); g = Canvas()
    rnd = random.Random(seed)
    def pool(cx, cy, rx, ry, rim="f", body="gh", hi="i"):
        for y in range(int(-ry) - 1, int(ry) + 2):
            for x in range(int(-rx) - 1, int(rx) + 2):
                d = (x / max(0.8, rx)) ** 2 + (y / max(0.8, ry)) ** 2
                if d > 1: continue
                if fade and ((x * 7 + y * 13 + seed) % 10) / 10.0 < fade: continue
                ch = rim if d > 0.62 and y >= 0 else body[0] if d > 0.62 else body[1]
                if d < 0.3 and (x + y + i) % 4 == 0: ch = hi
                c.put(*P(cx + x, cy + y), ch)
    k_h = (1 - 0.65 * fade) * min(1.0, spread * 1.3)
    if kind == "wick":
        spots = [(-7, 0.5, 3.2), (-1, -0.5, 2.6), (5, 0.5, 3.0), (9, -0.5, 1.6)]
        for n, (sx, sy, r) in enumerate(spots):
            pool(sx * spread, sy, r * spread, 1.7)
            if fade > 0.6 and n % 2: continue
            h = (5.5 + 2 * math.sin(i * 1.05 + n * 2.1)) * k_h * (0.7 if n == 3 else 1.0)
            flame_tongue(fl, sx * spread, sy - 1, h, 1.6, i * 1.05 + n * 1.7, lean=0.6 * math.sin(i * 0.8 + n))
            fl.put(*P(sx * spread, sy - 1), "j")                        # the wick stub at the flame's root
        for n in range(5):                                              # embers on the scorched floor
            ex = -9 + n * 4.5 + (i % 2)
            if (n + i) % 3: g.put(*P(ex * spread, 1 + (n % 2)), "b" if (n + i) % 2 else "c")
    elif kind == "votive":
        pool(0, 0, 10 * spread, 2.4, rim="f", body="gh", hi="i")
        for n, cx in enumerate((-6, 0, 6)):
            if fade > 0.7 and n != 1: continue
            cx *= spread
            for yy in range(0, 4):                                      # the candle: a squat cream cylinder
                c.put(*P(cx - 1, -yy), "i"); c.put(*P(cx, -yy), "h"); c.put(*P(cx + 1, -yy), "g")
            c.put(*P(cx, -4), "j")
            h = (4.5 + 1.8 * math.sin(i * 1.05 + n * 2.3)) * k_h
            flame_tongue(fl, cx, -5, h, 1.6, i * 1.05 + n * 2, lean=0.4 * math.sin(i + n))
        for n in range(3):                                              # little fires on the spilled tallow
            fx_ = (-9 + n * 9 + (i % 3)) * spread
            flame_tongue(fl, fx_, 1, (2 + (i + n) % 3) * k_h, 1.0, i + n * 3)
    else:
        pool(0, 0, 11 * spread, 2.6, rim="f", body="gh", hi="i")
        n_f = 7
        for n in range(n_f):
            fx_ = (-9.5 + n * 19 / (n_f - 1)) * spread
            if fade > 0.5 and n % 2: continue
            h = (3.5 + 2.6 * math.sin(i * 1.05 + n * 1.9) + (1.5 if n in (2, 4) else 0)) * k_h
            flame_tongue(fl, fx_, 1 if n % 2 else 0, h, 1.9, i * 1.05 + n * 1.3, lean=0.8 * math.sin(i * 0.7 + n))
        for n in range(3):                                              # smoke
            sx = -6 + n * 6 + (i % 2)
            g.put(*P(sx, -9 - (i + n) % 4), ")" if n % 2 else "-")
    for n in range(2):                                                  # a spark leaping off
        if (i + n) % 3 == 0:
            g.put(*P((-4 + n * 8) * spread + (i % 2), -9 - (i % 3)), "d")
    px = outl(c.px, "0")
    for k_ in list(px):                                                 # wax rims read as wax, not as a black line
        if k_ not in c.px and (k_[0], k_[1] + 1) in c.px: px[k_] = "f"
    fpx = outl(fl.px, "a") if fl.px else {}
    for k_, v in fpx.items():
        if k_ not in fl.px and k_ in px: continue                       # keep the pool rim under the flame rim
        px[k_] = v
    px.update(g.px)
    return Spr(px)


def build_floor_fires(outdir):
    # 30 frames = a 6-frame loop played 5 times (the burning pool these replace: same clip length and damage events)
    d = god_durations("FxEmberPatch", "Loop")
    for kind, name, seed, note in (("wick", "FxItemWickFire", 2, "Wickwalk burning wax drips (ground 20x7 at the origin)"),
                                   ("votive", "FxItemVotive", 4, "Votive Candle spilled burning tallow + votive candles (ground 20x7)"),
                                   ("slick", "FxItemWaxFire", 6, "Wax Slick set alight (hero wax ignition; ground 20x7)")):
        grow = [floor_fire(k, kind, spread=s, seed=seed) for k, s in enumerate((0.55, 0.8))]
        loop = [floor_fire(k, kind, seed=seed) for k in range(6)]
        fade = [floor_fire(k, kind, seed=seed, fade=f) for k, f in zip(range(4), (0.15, 0.35, 0.55, 0.75))]
        life = grow + [loop[(k + 2) % 6] for k in range(24)] + fade
        fx(name, [("Life", life, d * 5), ("Loop", loop, d)], (26, 18), (13, 13), outdir, note)


# ================================================================================================ runners
def runner(kind, i):
    """Tiny things that scurry out of the hero and lay a trail (HeroSlimeDropper runners), faces right."""
    f = Fr()
    b = abs(math.sin(i * math.pi / 2)) * 1.0
    if kind == "wick":       # a scurrying wax drop with a lit wick
        ell(f.b, 0, -2.5 - b, 2.6, 2.2, WAX, bias=0.2)
        f.b.put(-3, -1, "g"); f.b.put(-4, -1 + (i % 2), "f")
        f.b.put(0, -5 - b, "j")
        flame_tongue(f.g, 0, -6 - b, 3 + (i % 2), 1.0, i * 1.7)
        f.g.put(*P(-5 - (i % 2), -3), "c")
    elif kind == "wax":      # a sliding wax glob with drips
        ell(f.b, 0, -2 - b * 0.5, 3.0, 2.0 + b * 0.4, WAX, bias=0.25)
        for k in range(3):
            f.b.put(-3 - k, -1 + (k + i) % 2 * 0, "g" if k < 2 else "f")
        f.g.put(-1, -3, "i")
    elif kind == "thorn":    # a rolling bramble knot with red buds
        cx, cy = 0, -3
        ell(f.b, cx, cy, 2.8, 2.8, "stk", bias=0.15)
        for k in range(5):
            a = math.radians(k * 72 + i * 30)
            f.b.put(*P(cx + 3.6 * math.cos(a), cy + 3.6 * math.sin(a)), "k")
        f.b.put(*P(cx - 1, cy - 1), "p")
        f.g.put(*P(cx + 2 * math.cos(i), cy - 1), "(")
        f.g.put(*P(cx - 1, cy + 1 - (i % 2)), "p")
    elif kind == "root":     # a burrowing root tip pushing up dirt
        for k in range(5):
            f.n.put(-1 - k * 2, 0, "s" if k % 2 else "r")
        ell(f.b, 0, -1, 3.2, 1.6 + b * 0.6, "stk", bias=0.1)
        line(f.b, 0, -2 - b, 3, -4 - b, "k")
        f.g.put(3, -5 - int(b), "q"); f.g.put(2, -4 - int(b), "p")
        f.n.put(*P(-2 + (i % 2), -3 - b), "s"); f.n.put(*P(1 - (i % 2), -4), "t")
    return f.done()


def build_runners(outdir):
    for kind, name, note in (("wick", "FxItemWickRunner", "Wickwalk runner"), ("wax", "FxItemWaxRunner", "Wax Slick runner"),
                             ("thorn", "FxItemThornRunner", "Thornwall sower"), ("root", "FxItemRootRunner", "Root Snare burrower")):
        fx(name, [("Run", [runner(kind, i) for i in range(4)], [0.06] * 4)], (16, 16), (8, 13), outdir, note)


# ================================================================================================ puddles
def puddle(i, ramp_edge, ramp_in, spread=1.0, fade=0.0, w=11.0, seed=0, bub=None, glint=None, swirl=None, specks=None):
    c = Canvas()
    lobes = [(0, 0, w, 2.8), (-w * 0.55, 0.3, w * 0.5, 2.2), (w * 0.5, -0.2, w * 0.55, 2.4), (-1.5, -0.6, w * 0.62, 3.0)]
    inside = {}
    for (lx, ly, rx, ry) in lobes:
        rx, ry = rx * spread, max(1.0, ry * (0.5 + 0.5 * spread))
        for y in range(int(-ry) - 1, int(ry) + 2):
            for x in range(int(lx * spread - rx) - 1, int(lx * spread + rx) + 2):
                d = ((x - lx * spread) / rx) ** 2 + ((y - ly) / ry) ** 2
                if d <= 1.0: inside[(x, y)] = min(inside.get((x, y), 9), d)
    for (x, y), d in inside.items():
        if fade and ((x * 7 + y * 13 + seed * 3) % 10) / 10.0 < fade: continue
        edge = any((x + a, y + b) not in inside for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            ch = ramp_edge[2] if (y < 0 and x < 3) else ramp_edge[1] if y <= 0 else ramp_edge[0]
        else:
            ch = ramp_in[0]
            if ((x + 2 * y + i) % 6) == 0 and d > 0.2: ch = ramp_in[1]
        c.put(x, y, ch)
    if swirl and fade < 0.6:
        # a turning spiral drawn into the pool
        for k in range(22):
            a = k * 0.5 + i * 0.55
            r = 0.4 * k * spread
            x, y = r * math.cos(a), r * math.sin(a) * 0.32
            if (int(round(x)), int(round(y))) in inside: c.put(*P(x, y), swirl[0] if k < 14 else swirl[1])
    if fade < 0.7:
        rnd = random.Random(seed * 5 + 1)
        for k in range(4):
            bx, by = rnd.uniform(-w * 0.7, w * 0.7) * spread, rnd.uniform(-1.5, 1.0)
            if bub and (i + k) % 3 != 2 and (int(bx), int(by)) in inside:
                c.put(*P(bx, by), bub)
                if glint and (i + k) % 3 == 1: c.put(*P(bx, by - 1), glint)
        if specks:
            for k in range(3):
                bx = rnd.uniform(-w * 0.6, w * 0.6) * spread
                if (int(bx), 0) in inside: c.put(*P(bx, rnd.choice((-1, 0, 1))), specks[(k + i) % len(specks)])
    return spr(c)


def pool_life(fn, d_spread, d_idle, n_idle, d_fade, reps):
    sp = [fn(k, 0.35 + 0.3 * k, 0.0) for k in range(3)]
    idle = [fn(k, 1.0, 0.0) for k in range(n_idle)]
    fd = [fn(k, 0.95 - 0.12 * k, f) for k, f in enumerate((0.35, 0.6, 0.85))]
    return sp, idle, fd


def build_puddles(outdir):
    # Wax Slick: Grow 4 + Idle 2 x 9 + Fade 3 = 25 (the FxWaxPuddle timing its slow zone was built around)
    dl = god_durations("FxWaxPuddle", "Life")
    def wax(k, s, f): return puddle(k, "fgh", "hi", spread=s, fade=f, w=10, seed=3, bub="i", glint="i", specks="g")
    grow = [wax(k, 0.25 + 0.25 * k, 0) for k in range(4)]
    idle = [wax(k, 1.0, 0) for k in range(2)]
    fade = [wax(k, 0.95 - 0.1 * k, f) for k, f in enumerate((0.35, 0.6, 0.85))]
    fx("FxItemWaxSlick", [("Life", grow + idle * 9 + fade, dl), ("Idle", idle, [0.3, 0.3])], (26, 10), (13, 5), outdir,
       "Wax Slick puddle (status zone 22x8)")
    # Undertow brine: Spread 3 + Idle 2 x 10 + Fade 3 = 26 (FxBrine timing)
    db = god_durations("FxBrine", "Life")
    def brine(k, s, f): return puddle(k, "TUV", "UV", spread=s, fade=f, w=11, seed=5, bub="W", glint="X", specks="V")
    sp = [brine(k, 0.35 + 0.3 * k, 0) for k in range(3)]
    idle = [brine(k, 1.0, 0) for k in range(2)]
    fd = [brine(k, 0.95 - 0.12 * k, f) for k, f in enumerate((0.35, 0.6, 0.85))]
    fx("FxItemUndertowBrine", [("Life", sp + idle * 10 + fd, db)], (28, 10), (14, 5), outdir, "Undertow brine left by the wave (zone 23x8)")
    # Riptide: a whirl that keeps turning
    def rip(k, s, f): return puddle(k, "TUV", "TU", spread=s, fade=f, w=11, seed=8, bub="W", glint="X", swirl="WV")
    sp = [rip(k, 0.35 + 0.3 * k, 0) for k in range(3)]
    idle = [rip(k, 1.0, 0) for k in range(4)]
    fd = [rip(k, 0.95 - 0.12 * k, f) for k, f in enumerate((0.35, 0.6, 0.85))]
    # 26 frames, same per-frame times as FxBrine (idle frames step through 4 whirl phases)
    life = sp + [idle[k % 4] for k in range(20)] + fd
    fx("FxItemRiptidePool", [("Life", life, db)], (28, 10), (14, 5), outdir, "Riptide Dash whirlpool left where you started (zone 23x8)")
    # Acid Spit pool: Spread 3 + Idle 4 x 3 + Fade 3 = 18 (FxZhkAcidPool timing)
    da = god_durations("FxZhkAcidPool", "Life")
    def acid(k, s, f): return puddle(k, "yzA", "zA", spread=s, fade=f, w=10, seed=9, bub="B", glint="B", specks="A")
    sp = [acid(k, 0.35 + 0.3 * k, 0) for k in range(3)]
    idle = [acid(k, 1.0, 0) for k in range(4)]
    fd = [acid(k, 0.95 - 0.12 * k, f) for k, f in enumerate((0.35, 0.6, 0.85))]
    # hissing vapour over the idle pool
    def vap(s, k):
        px = dict(s.px)
        for j in range(2):
            px[P(-5 + j * 8 + (k % 2), -3 - (k + j) % 3)] = "B" if (k + j) % 2 else "A"
        return Spr(px)
    idle = [vap(s, k) for k, s in enumerate(idle)]
    fx("FxItemAcidPool", [("Life", sp + idle * 3 + fd, da)], (26, 12), (13, 7), outdir, "Acid Spit pool (ground 22x10)")


# ================================================================================================ thorns
def thorn_patch(i, k_life, style="bramble", seed=1):
    """A low line of thorns. k_life: 0..1 grow, 1 = full, >1 wilt (1..2).
    bramble (Thornwall): curved green-brown briars with hooked barbs and red buds, on a turned-earth mound;
    iron (Thorn Mail): steel spikes like the mail's rings, moss-green vines wound round them."""
    c = Canvas(); g = Canvas()
    rnd = random.Random(seed)
    grow = min(1.0, k_life)
    wilt = max(0.0, k_life - 1.0)
    soil = "rs" if style == "bramble" else ")-"
    for x in range(-9, 10):
        if abs(x) <= 9 * grow + 1:
            c.put(x, 1, soil[0]); c.put(x, 0, soil[1] if (x + seed) % 3 else soil[0])
    n = 6
    for k in range(n):
        x = -7.5 + k * 15 / (n - 1) + rnd.uniform(-0.5, 0.5)
        h = (4.5 + rnd.uniform(0, 3)) * grow * (1 - 0.45 * wilt)
        if h < 1.2: continue
        bend = (1 if k % 2 else -1) * (0.8 + 0.4 * math.sin(i * 0.9 + k)) + (wilt * 2.5 if k % 2 else -wilt * 2.5)
        pts = [(x + bend * (j / 3.0) ** 2 * 1.4, -j * h / 3.0) for j in range(4)]
        if style == "bramble":
            tube(c, pts, [1.3, 1.0, 0.7, 0.35], "nopq", bias=0.1)
            for j in (1, 2):                                   # hooked barbs
                bx, by = pts[j]
                s = -1 if (j + k) % 2 else 1
                c.put(*P(bx + s * 1.6, by - 0.4), "t"); c.put(*P(bx + s * 2.2, by - 1.2), "s")
            tx, ty = pts[-1]
            if wilt < 0.6 and k % 2 == 0:
                g.put(*P(tx, ty - 1), "("); g.put(*P(tx + 1, ty - 1), "*"); g.put(*P(tx, ty - 2), "(")
            else:
                g.put(*P(tx, ty - 1), "q" if wilt < 0.5 else "p")
        else:
            tube(c, pts, [1.6, 1.1, 0.6, 0.2], ")-+=", bias=0.25)
            tx, ty = pts[-1]
            g.put(*P(tx, ty - 1), "=")
            if k % 2 == 0:                                       # vine winding round the spike
                for j in range(3):
                    vx, vy = pts[min(3, j + 1)] if j < 2 else pts[1]
                    g.put(*P(vx + (1 if j % 2 else -1), vy + 0.5), "p" if j % 2 else "o")
    px = outl(c.px, "0")
    px.update(g.px)
    return Spr(px)


def build_thorns(outdir):
    d = god_durations("FxThornPatch", "Life")       # 24 frames: grow 3, idle 18, wilt 3
    def life(style, seed):
        fr = [thorn_patch(i, (i + 1) / 3.5, style, seed) for i in range(3)]
        fr += [thorn_patch(i, 1.0, style, seed) for i in range(18)]
        fr += [thorn_patch(i, 1.25 + 0.25 * i, style, seed) for i in range(3)]
        return fr
    fx("FxItemThornwall", [("Life", life("bramble", 3), d)], (24, 14), (12, 10), outdir, "Thornwall bramble patch (ground 18x7)")
    fx("FxItemThornMail", [("Life", life("iron", 5), d)], (24, 14), (12, 10), outdir, "Thorn Mail iron thorns bursting from the floor (ground 18x7)")


# ================================================================================================ bone
def grave_spear(i):
    f = Fr()
    # shaft: a long femur-like bone with knuckles, faces right
    tube(f.b, [(-10, 0), (5, 0)], [1.0, 1.0], "klm", bias=0.25)
    for x in (-10, -4):
        ell(f.b, x, 0, 1.4, 1.6, BONE, bias=0.2)
    poly(f.b, [(5, -2), (11, 0), (5, 2)], lambda x, y: "m" if y < 0 else "l")
    f.g.put(9, 0, "m")
    # grave dust trailing
    rnd = random.Random(i)
    for k in range(5):
        f.n.put(-12 - k * 2 - (i % 2), rnd.choice((-2, -1, 1, 2)), "t" if k < 2 else "s")
    f.g.put(*P(3 - i * 3, -1), "m")
    return f.done()


def bone_chips(i, n=4, ramp="mlkj", dust="ts"):
    c = Canvas()
    t = (i + 1) / n
    sparks(c, 8, 0, 0, 2, 8, ramp[:3] if i < 2 else ramp[1:], seed=5, t=t, up=3.0)
    if i < 2: ell(c, 0, 0, 2.5 + i, 2 + i * 0.5, "klm", bias=0.3)
    for k in range(3):
        c.put(*P(-3 + k * 3, 1 - t * 3), dust[k % 2])
    return spr(c)


@V2.accent("eye")
def skull_draw(g, ph):
    """The Bone Boomerang skull, as on its icon (without the icon's motion arcs)."""
    p = g.ell(8.0, 6.8, 4.6, 4.0, "ivory", 1.0, bias=0.1)
    g.ell(8.0, 10.0, 3.2, 2.4, "ivory", 1.0, part=p, bias=0.1)
    for x in (6.8, 8.0, 9.2):
        g.line(x, 11.0, x, 12.0, "ivory", 1.1, tone=1)
    g.ell(6.2, 8.0, 1.5, 1.4, "blk", 1.2, flat=0)
    g.ell(9.8, 8.0, 1.5, 1.4, "blk", 1.2, flat=0)
    g.dot(6.2, 8.0, "eye", 3 + ph, 1.3); g.dot(9.8, 8.0, "eye", 3 + ph, 1.3)
    g.poly([(7.5, 9.4), (8.5, 9.4), (8.0, 10.4)], "blk", 1.25, flat=1)


def build_bone(outdir):
    fx("FxItemGraveSpear", [("Fly", [grave_spear(i) for i in range(4)], [0.05] * 4),
                            ("Pop", [bone_chips(i) for i in range(4)], [0.04, 0.05, 0.07, 0.09])], (30, 16), (15, 8), outdir,
       "Grave Call bone spear (box 11x10, pierces) + bone-chip impact")
    fly = []
    for i in range(8):
        f = Fr()
        ang = i * 45
        # motion arc behind the spin
        for k in range(6):
            a = math.radians(ang + 130 + k * 18)
            f.n.put(*P(7 * math.cos(a), 7 * math.sin(a)), "m" if k < 2 else "l" if k < 4 else "k")
        fly.append(layered(f.done(None), pen_spr(skull_draw, i % 2, S=0.85, turn=ang)))
    fx("FxItemBoneBoomerang", [("Fly", fly, [0.04] * 8), ("Pop", [bone_chips(i) for i in range(4)], [0.04, 0.05, 0.07, 0.09])],
       (18, 18), (9, 9), outdir, "Bone Boomerang spinning skull, 8 frames like the vanilla boomerang (capsule 13x8)")
    # Marrow Spikes: a ring of bone spikes (red marrow tips) erupting 52 x 21, back half drawn first
    d = god_durations("FxSpikeRing", "Play")
    frames = []
    for i in range(4):
        c = Canvas(); g = Canvas()
        rise = [0.55, 1.0, 0.85, 0.3][i]
        rx, ry = 24, 9.5
        # cracked earth ring the spikes burst through
        ring(c, 0, 0, rx, ry, lambda x, y: "s" if (x + y) % 3 else "r", gap=lambda a: int(a) % 45 < 10)
        if i < 2: ring(c, 0, 0, rx * 0.8, ry * 0.8, "r", gap=lambda a: int(a) % 30 < 15)
        n = 16
        order = sorted(range(n), key=lambda k: math.sin(math.radians(k * 360 / n + 6)))
        for k in order:
            a = math.radians(k * 360 / n + 6)
            bx, by = rx * 0.92 * math.cos(a), ry * 0.92 * math.sin(a)
            near = 0.75 + 0.25 * (math.sin(a) + 1) / 2          # front spikes a little bigger
            h = (8 + 4 * ((k * 7) % 3) / 2) * rise * near
            w = (2.2 if k % 2 else 1.7) * near
            lean = 1.6 * math.cos(a)
            poly(c, [(bx - w, by + 0.5), (bx + lean, by - h), (bx + w, by + 0.5)],
                 lambda x, y, bx=bx, by=by, h=h: "m" if x < bx and y < by - h * 0.3 else "l" if y < by - h * 0.25 else "k")
            if i < 3 and h > 3:
                g.put(*P(bx + lean, by - h), "(")
                if h > 6: g.put(*P(bx + lean * 0.9, by - h + 1), "*")
        if i == 0: ell(c, 0, 0, 6, 2.2, "jk")
        sparks(g, 10, 0, -2, 8, 24, "lmk", seed=4, t=(i + 1) / 4, yk=0.4)
        px = outl(c.px, "0"); px.update(g.px)
        frames.append(Spr(px))
    fx("FxItemMarrowSpikes", [("Play", frames, d)], (58, 36), (29, 23), outdir, "Marrow Spikes ring (ground 52x21 at the origin)")


def bone_plate(c, g, x, y, scale=1.0, flip=False):
    """A curved bone plate with a red marrow seam (Marrow Flask)."""
    s = -1 if flip else 1
    ell(c, x, y, 3.3 * scale, 4.4 * scale, BONE, bias=0.25)
    for yy in range(-2, 3):                                   # the marrow seam
        g.put(*P(x - s * 0.5, y + yy), "*" if abs(yy) == 2 else "(")
    c.put(*P(x + s * 1.5, y - 2), "m"); c.put(*P(x - s * 2, y + 2), "j")


def card(c, g, x, y, w=2.5, h=3.5, ang=0.0, face="Y", mark=None, edge="0"):
    pts = [rot(p, ang) for p in ((-w, -h), (w, -h), (w, h), (-w, h))]
    poly(c, [(x + px, y + py) for px, py in pts], face)
    if mark: g.put(*P(x, y), mark[0]); g.put(*P(x, y - 1), mark[1] if len(mark) > 1 else mark[0])


def build_plates(outdir):
    # Marrow Flask: one or two bone plates orbiting the hero at chest height
    def orbit(nplates, i, kind):
        f = Fr()
        for p in range(nplates):
            a = math.radians(i * 60 + p * 180)
            x, y = 10 * math.cos(a), -9 + 3.5 * math.sin(a)
            sc = 0.8 + 0.2 * math.sin(a)
            if kind == "bone":
                bone_plate(f.b, f.g, x, y, sc, flip=math.cos(a) < 0)
            else:
                ww = 3.0 * abs(math.cos(a * 1.0 + 0.6)) + 0.6
                card(f.b, f.g, x, y, w=ww, h=4.4 * sc, face="Y")
                if ww > 1.6:                                  # the red diamond
                    for dx, dy in ((0, -2), (-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (0, 1)):
                        f.g.put(*P(x + dx, y + dy + 0.5), "1" if dy < 0 else "Z")
                else:
                    f.g.put(*P(x, y), "Z")
        return f.done()
    def brk(i, kind):
        c = Canvas()
        t = (i + 1) / 4
        if kind == "bone":
            sparks(c, 9, 0, -9, 2, 10, "mlk", seed=7, t=t, up=4)
            if i < 2: ell(c, 0, -9, 3 - i, 3.5 - i, BONE, bias=0.3)
            c.put(*P(0, -9 + t * 6), "*")
        else:
            sparks(c, 8, 0, -9, 2, 10, "Y1Z", seed=8, t=t, up=4)
            for k in range(3):   # diamonds flutter out
                x = (k - 1) * 5 * t; y = -9 - 3 * t + k
                c.put(*P(x, y - 1), "1"); c.put(*P(x - 1, y), "1"); c.put(*P(x + 1, y), "Z"); c.put(*P(x, y + 1), "Z")
        return spr(c)
    for kind, name, note in (("bone", "FxItemMarrowPlate", "Marrow Flask bone plates (hero version)"),
                             ("card", "FxItemJokerShield", "Joker's Wild 'Diamonds' card shield (hero version)")):
        fx(name, [("Orbit1", [orbit(1, i, kind) for i in range(6)], [0.1] * 6),
                  ("Orbit2", [orbit(2, i, kind) for i in range(6)], [0.1] * 6),
                  ("Break", [brk(i, kind) for i in range(4)], [0.05, 0.06, 0.08, 0.1])], (28, 22), (14, 20), outdir, note)


# ================================================================================================ spores / plants
def spore_burst(i):
    c = Canvas(); g = Canvas()
    t = (i + 1) / 5
    if i == 0:
        ell(c, -2, -3, 2.5, 3.2, SPORE, bias=0.2); ell(c, 2, -3, 2.5, 3.2, SPORE, bias=0.1)
    rx, ry = 4 + 9 * t, 2 + 4 * t
    rnd = random.Random(6)
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi)
        x, y = math.cos(a) * rx * 0.7, math.sin(a) * ry * 0.7 - 3 * t
        r = (2.4 + rnd.uniform(0, 1.5)) * (1.0 - 0.35 * max(0, t - 0.6))
        if i < 4 or k % 2: ell(c, x, y - 1, r * 1.2, r, "uvwx" if i < 3 else "uvw", bias=0.2 - 0.3 * t)
    for k in range(6):
        a = k * 1.1 + i * 0.6
        g.put(*P(math.cos(a) * rx * 0.9, math.sin(a) * ry * 0.9 - 4 * t - 1), "A" if k % 2 else "B")
    px = outl(c.px, "u") if i < 4 else dict(c.px)
    px.update(g.px)
    return Spr(px)


def root_spike(i):
    """FxRootLine timing: roots shoot up (0-2), grip (3-4), sink (5-6)."""
    c = Canvas(); g = Canvas()
    h = [3, 7, 10, 9, 8, 5, 2][i]
    curl = [0, 0.3, 0.8, 1.2, 1.4, 1.0, 0.5][i]
    for x in range(-8, 9):
        if (x + i) % 3: c.put(x, 1, "r")
    for k, (x0, side) in enumerate(((-6, -1), (-2, 1), (2, -1), (6, 1))):
        hh = h * (0.7 + 0.3 * ((k * 5) % 3) / 2)
        pts = []
        for j in range(int(hh) + 1):
            t = j / max(1, hh)
            pts.append((x0 + side * curl * 3 * math.sin(t * 2.4), -j))
        if len(pts) >= 2:
            sub = pts[::max(1, len(pts) // 4)] + ([pts[-1]] if len(pts) % max(1, len(pts) // 4) != 1 else [])
            rad = [1.3 - 1.0 * j / max(1, len(sub) - 1) for j in range(len(sub))]
            tube(c, sub, rad, "stk", bias=0.15)
        if pts and i < 6:
            g.put(*P(pts[-1][0], pts[-1][1] - 1), "q" if k % 2 else "p")
    if 2 <= i <= 4:
        ring(c, 0, -2, 7, 2.2, lambda x, y: "t" if y < -2 else None, gap=lambda a: 200 < a < 340)
    px = outl(c.px, "0"); px.update(g.px)
    return Spr(px)


def build_plants(outdir):
    pods = []
    for i in range(4):
        f = Fr()
        for k in range(3):                              # a trail of spores behind it
            f.n.put(*P(-6 - k * 2, math.sin(k + i) * 1.5), "x" if k == 0 else "w")
        pods.append(layered(f.done(None), pen_spr(V2.spore_bomb, i % 2, S=0.7, turn=[0, 12, 0, -12][i], at=(0, -0.6))))
    fx("FxItemSporePod", [("Fly", pods, [0.08] * 4)], (14, 14), (7, 17), outdir,
       "Spore Bomb pod: rides 10 px above the webBall's floor point")
    fx("FxItemSporeBurst", [("Burst", [spore_burst(i) for i in range(5)], god_durations("FxSeed", "Burst"))], (34, 22), (17, 15), outdir,
       "Spore Bomb poison burst (ground 26x12 at the origin)")
    fx("FxItemRootSnare", [("Play", [root_spike(i) for i in range(7)], god_durations("FxRootLine", "Play"))], (22, 16), (11, 12), outdir,
       "Root Snare root grab, laid along the burrower's path (ground 20x8)")
    # Rotting Apple maggot swarm
    fly = []
    for i in range(4):
        f = Fr()
        for k in range(5):
            a = math.radians(k * 72 + i * 18)
            r = 3.6 + (k % 2) * 1.2
            cx, cy = r * math.cos(a), r * math.sin(a) * 0.9
            d = a + math.pi / 2 + math.sin(i * 1.7 + k) * 0.6           # each maggot crawls round the swarm
            for j in range(3):
                x, y = cx - math.cos(d) * j, cy - math.sin(d) * j
                f.b.put(*P(x, y), "m" if j == 0 else "]" if j < 2 else "{")
            f.g.put(*P(cx + math.cos(d), cy + math.sin(d)), "*")       # the head
        ell(f.n, 0, 0, 1.8, 1.6, "*((", bias=0.1)                      # a clot of rot at the heart
        for k in range(3):   # rot flecks + a fly
            a = i * 1.6 + k * 2.1
            f.g.put(*P(6 * math.cos(a), 5 * math.sin(a)), "*" if k else "0")
        f.g.put(*P(-6 + i, -6 + (i % 2)), "-")
        fly.append(f.done("0"))
    pop = []
    for i in range(4):
        c = Canvas(); t = (i + 1) / 4
        sparks(c, 7, 0, 0, 1, 7, "]{*", seed=12, t=t, up=2)
        if i < 2: ell(c, 0, 0, 2, 1.6, "&*(")
        pop.append(spr(c))
    fx("FxItemMaggots", [("Fly", fly, [0.08] * 4), ("Pop", pop, [0.05, 0.06, 0.08, 0.1])], (20, 18), (10, 9), outdir,
       "Rotting Apple seeking maggot swarm (capsule 9x13) + bite pop")


# ================================================================================================ glass / shadow
def glass_shard(c, x, y, ang, L=5, W=1.6, bright="F"):
    pts = [rot(p, ang) for p in ((L, 0), (0, -W), (-L * 0.6, 0), (0, W))]
    poly(c, [(x + px, y + py) for px, py in pts], lambda xx, yy: "E" if (xx - x) + (yy - y) < 0 else "D")
    tx, ty = rot((L * 0.6, -0.3), ang)
    c.put(*P(x + tx, y + ty), bright)


def build_glass(outdir):
    # Shard Nova projectile
    fly = []
    for i in range(4):
        f = Fr()
        glass_shard(f.b, 0, 0, 0, L=6.5, W=2.8)
        f.g.put(*P(2 - i, -1 if i % 2 else 0), "F")
        for k in range(4):
            if (k + i) % 2 == 0: f.n.put(-6 - k * 2, (k % 2) * (1 if i % 2 else -1), "E" if k < 2 else "D")
        fly.append(f.done("C"))
    pop = []
    for i in range(4):
        c = Canvas(); t = (i + 1) / 4
        for k in range(5):
            a = k * 72 + 20 + i * 10
            r = 1 + 6 * t
            glass_shard(c, r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), a, L=2.2 * (1 - 0.3 * t), W=0.8)
        if i == 0: c.put(0, 0, "F")
        pop.append(spr(c))
    fx("FxItemNovaShard", [("Fly", fly, [0.06] * 4), ("Pop", pop, [0.04, 0.05, 0.07, 0.09])], (20, 16), (10, 8), outdir,
       "Shard Nova star-glass shard (box 11x10) + shatter pop")
    # Mirror Step: the pane left behind shatters (22 x 12 at the feet), its dash blur and glints
    d = god_durations("FxDecoyBurst", "Play")
    sh = []
    for i in range(5):
        c = Canvas(); g = Canvas()
        t = i / 4
        if i == 0:
            poly(c, [(-5, -18), (5, -18), (5, 0), (-5, 0)], lambda x, y: "E" if x - y < 10 else "D")
            ring(c, 0, -9, 5.5, 9.5, "C")
            line(g, -3, -16, 2, -3, "F"); line(g, 1, -15, -2, -10, "F")
        else:
            rnd = random.Random(21)
            for k in range(11):
                a = rnd.uniform(-math.pi, 0.2)
                r = rnd.uniform(4, 13) * t + 1
                x, y = math.cos(a) * r, -9 + math.sin(a) * r * 0.8 + 10 * t * t
                if y > 1: y = 1 - (k % 2)
                if i < 4 or k % 2: glass_shard(c, x, y, rnd.uniform(0, 360), L=2.8 - t, W=1.0)
            ring(g, 0, 0, 3 + 8 * t, 1.5 + 4 * t, "E" if i < 3 else "D", gap=lambda a, i=i: (int(a) // 25 + i) % 2 == 0)
        px = outl(c.px, "C"); px.update(g.px)
        sh.append(Spr(px))
    fx("FxItemMirrorShatter", [("Shatter", sh, d)], (32, 26), (16, 20), outdir, "Mirror Step pane shatter (ground 22x12 at the feet)")
    blur = []
    for i in range(4):
        c = Canvas(); t = i / 3
        for k in range(3):
            y = -2 + k * 2
            x0, x1 = -14 + 6 * t + k, 12 - 4 * t - k * 2
            for x in range(int(x0), int(x1)):
                if (x + k * 3 + i) % 7 < 5 - i: c.put(x, y, "F" if x > x1 - 4 else "E" if (x + k) % 3 else "D")
        for k in range(3):
            glass_shard(c, -6 - k * 5 + t * 3, (k - 1) * 2, 0, L=1.6, W=0.6)
        blur.append(spr(c))
    fx("FxItemMirrorBlur", [("Play", blur, [0.067, 0.1, 0.1, 0.1])], (32, 10), (16, 5), outdir, "Mirror Step dash streak (replaces the vanilla DashBlur)")
    gl = []
    for i in range(5):
        c = Canvas()
        s = [1, 2, 2, 1, 0][i]
        c.put(0, 0, "F" if i < 3 else "E")
        for k in range(1, s + 1):
            c.put(k, 0, "E"); c.put(-k, 0, "E"); c.put(0, k, "D"); c.put(0, -k, "D")
        if i == 4: c.put(0, 1, "D")
        gl.append(spr(c))
    fx("FxItemMirrorGlint", [("Play", gl, [0.1, 0.1, 0.2, 0.1, 0.1])], (8, 8), (4, 4), outdir, "Mirror Step glints dropped along the dash")
    # Shadow Swap: a violet vortex with two swapping arrows; and a small cast sigil at the hero
    d = god_durations("FxSwapFlash", "Play")
    fl = []
    for i in range(5):
        c = Canvas(); g = Canvas()
        t = i / 4
        r = 4 + 7 * math.sin(t * math.pi * 0.9)
        cy = -11
        ring(c, 0, cy, r, r * 1.05, lambda x, y: "I", gap=lambda a: int(a + i * 40) % 120 < 30)
        if i < 4:
            ell(c, 0, cy, max(1, r * 0.75), max(1, r * 0.8), "HHIJ", bias=-0.15)
            for arm in (0, 180):                       # a two-armed swirl turning
                for k in range(16):
                    a = math.radians(arm + i * 55 + k * 22)
                    rr = r * 0.9 * k / 16
                    g.put(*P(rr * math.cos(a), cy + rr * math.sin(a)), "J" if k > 7 else "I")
            for s in (1, -1):        # the two swapping arrowheads riding the rim
                a = math.radians(i * 70 + (0 if s > 0 else 180))
                ax, ay = r * math.cos(a), cy + r * math.sin(a)
                tx, ty = -math.sin(a), math.cos(a)
                g.put(*P(ax, ay), "F")
                g.put(*P(ax - tx - math.cos(a), ay - ty - math.sin(a)), "J"); g.put(*P(ax - tx + math.cos(a), ay - ty + math.sin(a)), "J")
                line(g, ax - tx * 4, ay - ty * 4, ax - tx, ay - ty, "J")
        sparks(g, 8, 0, cy, r * 0.8, r * 1.4, "JI", seed=31, t=0.6 + 0.4 * t)
        ring(c, 0, 0, 3 + r * 0.6, 1.3 + r * 0.2, "I")
        px = outl(c.px, "G"); px.update(g.px)
        fl.append(Spr(px))
    cast = []
    for i in range(3):
        c = Canvas()
        ring(c, 0, 0, 3 + i * 2, 1 + i * 0.7, "J" if i < 2 else "I")
        c.put(0, -1 - i, "J")
        cast.append(spr(c))
    fx("FxItemShadowSwap", [("Flash", fl, d), ("Cast", cast, [0.05, 0.06, 0.08])], (30, 28), (15, 25), outdir,
       "Shadow Swap vortex at both ends of the swap + cast sigil")
    # Hollow Crown: the shadow that repeats your blow, wearing a pale crown
    ec = []
    for i in range(4):
        f = Fr()
        dis = i / 3
        # hooded shadow silhouette
        ell(f.b, 0, -6, 4.2 - dis, 5.5, "HHI", bias=0.0)
        ell(f.b, 0, -13, 3.0, 3.0, "HIJ", bias=0.0)
        for yy in range(-17, 0, 2): f.g.put(-4 if yy > -10 else -3, yy, "J")     # moonlit rim on the shadow
        f.g.put(-1, -13, "J"); f.g.put(1, -13, "J")
        for x in (-2, 0, 2):                       # the crown
            f.g.put(x, -17, "S" if x == 0 else "R")
        for x in range(-2, 3): f.g.put(x, -16, "R")
        for k in range(4 + i * 2):                 # wisps tearing off
            a = k * 1.7 + i
            f.g.put(*P(math.cos(a) * (4 + i * 2), -8 + math.sin(a) * (5 + i)), "I" if k % 2 else "H")
        s = f.done("G")
        if i >= 2:
            s = fade(s, 0.72 if i == 2 else 0.48)
        ec.append(s)
    fx("FxItemShadowEcho", [("Echo", ec, [0.08, 0.1, 0.12, 0.14])], (22, 22), (11, 20), outdir,
       "Hollow Crown shadow echo (replaces the violet-tinted hero afterimage)")


# ================================================================================================ soul / bell / sea
def build_soul(outdir):
    fly = []
    for i in range(4):
        # the Soul Lantern itself, swinging, with soul-sparks circling it
        g = Canvas()
        for k in range(4):
            a = i * 1.2 + k * 1.57
            g.put(*P(6.6 * math.cos(a), 6.6 * math.sin(a)), "N" if k % 2 else "M")
        fly.append(layered(pen_spr(V2.soul_lantern, i % 2, S=0.8, turn=[0, 14, 0, -14][i]), spr(g)))
    d = [0.067, 0.067, 0.1, 0.1, 0.133, 0.133, 0.133, 0.167, 0.1, 0.1, 0.1]   # = vanilla skydropExplode (its damage events)
    burst = []
    for i in range(11):
        c = Canvas(); g = Canvas()
        t = i / 10
        cy = 6
        if i <= 1:
            ell(g, 0, cy, 4 + i * 4, 3 + i * 3, "NOO", bias=0.6)
        elif i <= 7:
            r = 8 + 12 * min(1, (i - 1) / 4)
            k = (i - 2) / 5
            for j in range(10):
                a = j * 0.63 + i * 0.3
                x, y = math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.42
                flame_tongue(c, x, y + 2, (7 - 4 * k) * (0.7 + 0.3 * ((j * 3) % 2)), 2.2 - k, i + j, ramp="LMNO")
            ell(c, 0, cy, r * 0.55 * (1 - k * 0.6), r * 0.3 * (1 - k * 0.6), "MNO", bias=0.5 - k)
            ring(g, 0, cy + 2, r, r * 0.45, "N" if i < 5 else "M", gap=lambda a, i=i: (int(a) // 20 + i) % 3 == 0)
        else:
            for j in range(7):
                a = j * 0.9 + i
                x, y = math.cos(a) * 14, cy - (i - 7) * 4 + math.sin(a) * 5
                c.put(*P(x, y), "M" if i < 10 else "L"); c.put(*P(x, y - 1), "L")
        sparks(g, 10, 0, cy, 4, 20, "ONM", seed=41, t=min(1, t * 1.4), yk=0.6)
        px = dict(c.px); px.update(g.px)
        burst.append(Spr(px))
    fx("FxItemSoulLantern", [("Fly", fly, [0.08] * 4)], (16, 16), (8, 8), outdir, "Soul Lantern swinging soul-flame lantern (capsule 15x10)")
    fx("FxItemSoulBurst", [("Burst", burst, d)], (48, 34), (24, 10), outdir,
       "Soul Lantern burst (skydropExplode capsule 41x22, centred 6 px under the origin), 11 frames like the vanilla burst")


def bell_ring(i, n, rx, ry, cols, notes=True, bell=True):
    c = Canvas(); g = Canvas()
    t = (i + 0.5) / n
    for k, f in enumerate((1.0, 0.7, 0.42)):
        rr = (0.3 + 0.7 * t) * f
        if rr < 0.15: continue
        fade = i >= n - 2
        gap = lambda a, k=k: (int(a) // 18 + k + i) % 4 == 0
        # each sound ring is a 2 px band: bright crest over a darker bronze lip
        ring(c, 0, 1, rx * rr, ry * rr, cols[min(2, k + 1 + fade)] if k < 2 else "P", gap=gap)
        ring(c, 0, 0, rx * rr, ry * rr, (("S" if k == 0 else cols[0]) if not fade else cols[1]), gap=gap)
    if bell and i < 2:
        b = Canvas()
        ell(b, 0, -5, 3, 3.4, GOLD, bias=0.3); line(b, -4, -2, 4, -2, "Q"); b.put(0, -9, "P")
        c.px.update(outl(b.px, "P")); g.put(0, -1, "S")
    if notes:
        for k in range(4):
            a = math.radians(k * 90 + 30 + i * 15)
            x, y = rx * 0.8 * t * math.cos(a), ry * 0.8 * t * math.sin(a) - 4 * t
            g.put(*P(x, y), "S"); g.put(*P(x + 1, y - 1), "R"); g.put(*P(x + 1, y - 2), "R")
    sparks(g, 8, 0, 0, rx * 0.5, rx * 1.0, "SR", seed=51, t=t, yk=ry / rx)
    px = dict(c.px)
    px.update(g.px)
    return Spr(px)


def build_bell_sea(outdir):
    d = god_durations("FxBellRing", "Play")
    fx("FxItemBellToll", [("Ring", [bell_ring(i, 5, 26, 10, "RQP") for i in range(5)], d)], (58, 28), (29, 15), outdir,
       "Bell Toll bronze sound ring (ground 50x20)")
    # Tidecaller: a ring of breaking water with a foam crest, 6 frames (ground 56 x 24)
    tide = []
    for i in range(6):
        c = Canvas(); g = Canvas()
        t = (i + 0.6) / 6
        rx, ry = 28 * t, 12 * t
        for a in range(0, 360, 6):
            r = math.radians(a)
            x, y = rx * math.cos(r), ry * math.sin(r)
            h = (3 + 2 * math.sin(r * 5 + i)) * (1 - 0.6 * t)
            if (a // 6 + i) % 9 == 0: continue
            for j in range(int(h) + 1):
                ch = "X" if j == int(h) else "W" if j > h * 0.5 else "V" if j > 0 else "U"
                c.put(*P(x, y - j), ch)
        if i < 3:
            ell(c, 0, 0, rx * 0.6, ry * 0.6, "TUV", bias=-0.2)
        else:
            ring(c, 0, 0, rx * 0.65, ry * 0.65, "U", gap=lambda a: int(a) % 30 < 12)
        sparks(g, 10, 0, -2, rx * 0.6, rx * 1.05, "XW", seed=61, t=1.0, yk=0.45)
        px = outl(c.px, "T") if i < 5 else dict(c.px)
        px.update(g.px)
        tide.append(Spr(px))
    fx("FxItemTideBurst", [("Ring", tide, [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])], (62, 34), (31, 18), outdir,
       "Tidecaller Conch wave burst (ground 56x24)")
    # Undertow wave: a curling teal crest with foam, faces right
    wave = []
    for i in range(4):
        f = Fr()
        for y in range(-9, 10):
            # a crescent wall of water, bulging forward (right) in the middle, darker toward its back
            q = (y / 9.0) ** 2
            front = 4.5 - q * 5.5 + math.sin(y * 0.7 + i * 1.6) * 0.5
            back = front - (3.0 + 3.5 * (1 - q))
            for x in range(int(math.floor(back)), int(math.ceil(front)) + 1):
                l = -0.6 + (x - back) / max(1.0, front - back) * 1.4 + (0.25 if y < -2 else 0)
                f.b.put(x, y, pick("TUVW", l))
            f.g.put(*P(front + 0.6, y), "X" if (y + i) % 3 else "W")      # foam on the leading face
        for k in range(7):          # the crest curling over at the top
            a = math.radians(-160 + k * 30 + i * 6)
            f.g.put(*P(2.5 + 3.2 * math.cos(a), -8 + 2.2 * math.sin(a)), "X" if k > 3 else "W")
        for k in range(5):          # spray
            f.g.put(*P(-8 - k * 2 - (i % 2), (k * 7 % 13) - 6 + i), "W" if k % 2 else "X")
        wave.append(f.done("T"))
    drop = []
    for i in range(4):
        c = Canvas(); t = (i + 1) / 4
        sparks(c, 8, 0, 0, 2, 8, "XWV", seed=63, t=t, up=3)
        if i < 2: ell(c, 0, 0, 2.5, 2, "UVW", bias=0.3)
        drop.append(spr(c))
    fx("FxItemUndertowWave", [("Fly", wave, [0.08] * 4), ("Pop", drop, [0.04, 0.05, 0.07, 0.09])], (28, 22), (14, 11), outdir,
       "Undertow wave (box 18x22, pierces) + splash")
    # Riptide dash: a water streak and droplets along the path
    blur = []
    for i in range(4):
        c = Canvas(); t = i / 3
        for k in range(3):
            y = -2 + k * 2
            x0, x1 = -14 + 6 * t + k * 2, 13 - 4 * t - k
            for x in range(int(x0), int(x1)):
                if (x * 2 + k + i) % 6 < 5 - i: c.put(x, y + (1 if (x // 4 + k) % 2 else 0) * (k == 1), "X" if x > x1 - 3 else "W" if (x + k) % 3 else "V")
        blur.append(spr(c))
    fx("FxItemRiptideBlur", [("Play", blur, [0.067, 0.1, 0.1, 0.1])], (32, 10), (16, 5), outdir, "Riptide Dash water streak (replaces the vanilla DashBlur)")
    dr = []
    for i in range(5):
        c = Canvas()
        y = [0, -1, -1, 0, 1][i]
        if i < 3:
            c.put(0, y - 1, "X"); c.put(0, y, "X"); c.put(0, y + 1, "W"); c.put(-1, y + 1, "V"); c.put(1, y + 1, "V"); c.put(0, y + 2, "V")
        else:
            c.put(-1, 1, "W"); c.put(1, 1, "V"); c.put(0, 1, "W"); c.put(-2, 1, "U"); c.put(2, 1, "U")
        dr.append(spr(c))
    fx("FxItemRiptideDrop", [("Play", dr, [0.1, 0.1, 0.2, 0.1, 0.1])], (8, 8), (4, 4), outdir, "Riptide Dash droplets dropped along the dash")


# ================================================================================================ jinx items (cards, dice, strings)
CURSES = [("Fire", "cd", "b"), ("Poison", "AB", "z"), ("Frost", "56", "4"), ("Daze", "SR", "Q")]


def curse_mark(g, x, y, kind, s=1):
    """The curse emblem: a flame, a venom drop, a snowflake or a star."""
    if kind == "Fire":
        g.put(x, y, "d"); g.put(x, y - 1, "c"); g.put(x - 1, y, "c"); g.put(x + 1, y, "b"); g.put(x, y + 1, "b")
    elif kind == "Poison":
        g.put(x, y - 1, "A"); g.put(x, y, "A"); g.put(x - 1, y + 1, "z"); g.put(x, y + 1, "B"); g.put(x + 1, y + 1, "z")
    elif kind == "Frost":
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): g.put(x + dx, y + dy, "6" if (dx, dy) == (0, 0) else "5")
        if s > 1:
            for dx, dy in ((2, 2), (-2, 2), (2, -2), (-2, -2)): g.put(x + dx, y + dy, "4")
    else:
        g.put(x, y, "S"); g.put(x - 1, y, "R"); g.put(x + 1, y, "R"); g.put(x, y - 1, "R"); g.put(x, y + 1, "R")


def build_jinx(outdir):
    anims = []
    for kind in ["Plain"] + [k for k, _, _ in CURSES]:
        fr = []
        for i in range(4):
            f = Fr()
            w = [3.0, 2.0, 0.7, 2.0][i]
            card(f.b, f.g, 0, 0, w=w, h=4.2, ang=-15, face="Y" if i != 2 else "1")
            if i in (0, 3):
                f.b.put(0, -3, "Z"); f.b.put(-1, -2, "Z"); f.b.put(1, -2, "Z")      # the jester crown motif
                if kind != "Plain": curse_mark(f.g, 0, 1, kind)
                else: f.g.put(0, 1, "1")
            elif i == 1:
                f.b.put(0, 0, "Z" if kind == "Plain" else "1")
            for k in range(3):
                f.n.put(-5 - k * 2, (k + i) % 2, {"Plain": "Y", "Fire": "c", "Poison": "A", "Frost": "5", "Daze": "R"}[kind] if k == 0 else "[")
            fr.append(f.done("2"))
        anims.append(("Fly" if kind == "Plain" else "Fly" + kind, fr, [0.05] * 4))
    fx("FxItemWildCard", anims, (16, 14), (8, 7), outdir, "Wild Card spinning card; FlyFire/Poison/Frost/Daze wear the drawn curse")
    curse = []
    for kind, hi, lo in CURSES:
        fr = []
        for i in range(5):
            c = Canvas(); g = Canvas()
            t = (i + 1) / 5
            y = -8 - 5 * t
            if i < 2:
                card(c, g, 0, y + 2, w=3 - i, h=4, face="Y")
            curse_mark(g, 0, int(y - 1), kind, s=2)
            for k in range(6):
                a = k * 1.05 + i * 0.4
                gx, gy = math.cos(a) * 7 * t, y + math.sin(a) * 4 * t
                g.put(*P(gx, gy), hi[k % 2] if i < 4 else lo)
                if i >= 1: g.put(*P(gx * 0.85, gy - math.sin(a) * 0.6), lo, over=False)   # a short trail, not a lone pixel
            if kind == "Fire" and i >= 1: flame_tongue(g, 0, int(y + 3), 4 - i * 0.6, 1.4, i)
            if kind == "Poison" and i >= 1:
                for k in range(3): g.put(*P(-3 + k * 3, y + 3 + i), "z"); g.put(*P(-3 + k * 3, y + 2 + i), "A")
            if kind == "Frost" and i >= 1: ring(g, 0, int(y), 3 + i, 2 + i * 0.6, "4", gap=lambda a: int(a) % 60 < 25)
            if kind == "Daze" and i >= 1:
                for k in range(3):
                    a = i * 1.2 + k * 2.09
                    g.put(*P(5 * math.cos(a), y + 2 * math.sin(a)), "S")
            px = outl(c.px, "2"); px.update(g.px)
            fr.append(Spr(px))
        curse.append(("Curse" + kind, fr, [0.05, 0.06, 0.08, 0.1, 0.12]))
    fx("FxItemWildCurse", curse, (20, 24), (10, 22), outdir, "Wild Card curse landing on the monster (one per curse)")
    # Loaded Dice: a tumbling die, then the rolled face pops up over the victim
    die = []
    for i in range(4):
        f = Fr()
        for k in range(3): f.n.put(-7 - k * 2, 1 + (k + i) % 2, "]" if k == 0 else "[")
        tumble = lambda g, ph, i=i: g.die(8, 8, 8.4, rx=12 + i * 24, ry=-30 + i * 31, rz=i * 18, z=1.0, pip_min=2.4)
        die.append(layered(f.done(None), pen_spr(tumble, 0, S=1.0)))
    fx("FxItemLoadedDie", [("Fly", die, [0.06] * 4)], (20, 18), (10, 9), outdir, "Loaded Dice tumbling die (box 15x13)")
    PIPS = {1: [(0, 0)], 2: [(-2, -2), (2, 2)], 3: [(-2, -2), (0, 0), (2, 2)], 4: [(-2, -2), (2, -2), (-2, 2), (2, 2)],
            5: [(-2, -2), (2, -2), (0, 0), (-2, 2), (2, 2)], 6: [(-2, -2), (2, -2), (-2, 0), (2, 0), (-2, 2), (2, 2)]}
    rolls = []
    for n in range(1, 7):
        fr = []
        for i in range(4):
            f = Fr()
            y = -12 - [0, 3, 4, 4][i]
            s = [0.6, 1.0, 1.0, 0.9][i]
            poly(f.b, [(-4 * s, y - 4 * s), (4 * s, y - 4 * s), (4 * s, y + 4 * s), (-4 * s, y + 4 * s)], lambda x, yy: "Y" if x + yy < y + 2 else "]")
            if i >= 1:
                for (px_, py_) in PIPS[n]: f.g.put(px_, y + py_, "1" if n >= 5 else "Z")
            if i == 1: sparks(f.g, 6, 0, y, 5, 8, "dS", seed=n)
            if n == 6 and i >= 2: f.g.put(-6, y - 5, "e"); f.g.put(6, y - 3, "d")
            s_ = f.done("2")
            if i == 3: s_ = fade(s_)
            fr.append(s_)
        rolls.append(("Roll%d" % n, fr, [0.05, 0.12, 0.2, 0.1]))
    fx("FxItemDieRoll", rolls, (16, 22), (8, 21), outdir, "Loaded Dice: the rolled face (1-6 pips) pops over the monster it hit")
    # Puppet Strings: a taut lilac thread with a brass needle at its tip
    st = []
    for i in range(4):
        f = Fr()
        for x in range(-13, 6):
            y = math.sin(x * 0.7 + i * 1.6) * (0.9 if x < -2 else 0.3) * (1 + (x + 13) / 20)
            f.g.put(*P(x, y), ">" if (x + i) % 3 else "<")
        line(f.b, 5, 0, 9, 0, "RS")
        f.b.put(9, -1, "Q"); f.b.put(10, 0, "S")
        f.b.put(5, -1, "Q"); f.b.put(5, 1, "Q")          # the needle eye
        f.g.put(*P(-13 + (i * 5) % 18, 0), "=")
        st.append(f.done("2"))
    snap = []
    for i in range(4):
        c = Canvas(); t = (i + 1) / 4
        for s in (-1, 1):
            for k in range(6):
                a = k * 0.9 + t * 2
                c.put(*P(s * (1 + k * 1.2 * t + math.cos(a)), math.sin(a) * 2 * (1 - t) - t * 2 + k * 0.3 * t), ">" if k % 2 else "<")
        if i < 2: c.put(0, 0, "S")
        snap.append(spr(c))
    fx("FxItemPuppetString", [("Fly", st, [0.05] * 4), ("Pop", snap, [0.04, 0.05, 0.07, 0.09])], (28, 10), (14, 5), outdir,
       "Puppet Strings piercing thread (box 11x10) + snap")
    # Lucky Die dodge, Jester's Bell crit, Joker's Wild flip
    dodge = []
    for i in range(5):
        f = Fr()
        y = -22 - [0, 3, 5, 6, 6][i]
        a = [45, 20, 0, 0, 0][i]
        pts = [rot(p, a) for p in ((-4, -4), (4, -4), (4, 4), (-4, 4))]
        poly(f.b, [(x, yy + y) for x, yy in pts], lambda x, yy: "i" if x + yy < y + 2 else "h")
        if i >= 2:
            for (px_, py_) in PIPS[6]: f.g.put(px_, y + py_, "p")
        if i == 2: sparks(f.g, 8, 0, y, 5, 9, "qS", seed=71)
        if i >= 1:   # the dodge whoosh round the hero
            ring(f.g, 0, -9, 7 + i, 10, "E" if i < 4 else "D", a0=110 + i * 20, a1=250 + i * 20)
        s_ = f.done("2")
        if i == 4: s_ = fade(s_)
        dodge.append(s_)
    fx("FxItemLuckyDie", [("Dodge", dodge, [0.05, 0.06, 0.18, 0.12, 0.1])], (20, 34), (10, 33), outdir,
       "Lucky Die: a green-pipped six flips over the hero as the hit misses")
    crit = []
    for i in range(5):
        f = Fr()
        sw = [-25, 20, -15, 10, 0][i]
        cy = -14
        ell(f.b, 0, cy, 3.4, 3.0, GOLD, ang=sw, bias=0.3)
        bx, by = rot((0, 3.2), sw)
        f.b.put(*P(bx, cy + by), "Q")
        line(f.b, 0, cy - 3, -4, cy - 7, "Z1")                       # the red ribbon
        f.g.put(*P(bx, cy + by + 1), "S")
        if 1 <= i <= 3:
            for k in range(8):
                a = math.radians(k * 45 + i * 10)
                r = 5 + i * 2
                f.g.put(*P(r * math.cos(a), cy + r * math.sin(a)), "S" if k % 2 else "1")
        crit.append(f.done("P"))
    fx("FxItemJesterCrit", [("Crit", crit, [0.05, 0.07, 0.08, 0.1, 0.12])], (24, 26), (12, 24), outdir,
       "Jester's Bell: the bell rings on every 6th (double damage) hit")
    flip = []
    for i in range(8):
        f = Fr()
        y = -12 - min(i, 4) * 1.5
        w = abs(math.cos(i * math.pi / 4)) * 4 + 0.4
        card(f.b, f.g, 0, y, w=w, h=5, face="Y" if math.cos(i * math.pi / 4) >= 0 else "Z")
        if w > 2 and math.cos(i * math.pi / 4) >= 0:            # the joker: a red jester cap over a grin
            yy = int(round(y))
            for dx, dy, ch in ((-2, -2, "Z"), (0, -3, "Z"), (2, -2, "Z"), (-1, -2, "1"), (1, -2, "1"), (0, -2, "1"),
                               (0, -1, "]"), (-1, 1, "Z"), (0, 2, "Z"), (1, 1, "Z")):
                f.g.put(dx, yy + dy, ch)
        elif w > 2:
            f.g.put(0, int(round(y)), "Y")
        if i >= 5: sparks(f.g, 6, 0, y, 5, 8, "Y1", seed=80 + i)
        flip.append(f.done("2"))
    suits = []
    SUIT = {"Hearts": ("1", [(-1, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (0, 1)]),
            "Diamonds": ("1", [(0, -2), (-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (0, 1)]),
            "Spades": ("2", [(0, -2), (-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (0, 1), (0, 2)]),
            "Clubs": ("2", [(0, -2), (-1, -1), (1, -1), (0, -1), (0, 0), (0, 1), (-1, 2), (1, 2)])}
    for nm, (col, pts) in SUIT.items():
        f = Fr()
        card(f.b, f.g, 0, -18, w=4.4, h=5, face="Y")
        for (x, y) in pts: f.g.put(x, -18 + y, col)
        f.g.put(-3, -22, col); f.g.put(3, -14, col)
        suits.append((nm, [f.done("2")], [0.9]))
    fx("FxItemJokerFlip", [("Flip", flip, [0.06, 0.05, 0.05, 0.06, 0.12, 0.14, 0.14, 0.12])] + suits, (14, 26), (7, 25), outdir,
       "Joker's Wild flip card and its four suit reveals")
    # Marionette Cross: lilac strings snap taut onto the monster from a wooden cross
    tug = []
    for i in range(4):
        f = Fr()
        cy = -26 + [2, 0, 0, 1][i]
        line(f.b, -6, cy, 6, cy, "t"); line(f.b, 0, cy - 2, 0, cy + 2, "t")
        f.b.put(0, cy, "s")
        for x0, x1 in ((-6, -4), (6, 4), (0, 0)):
            sag = [1.5, 0, 0, 0.8][i]
            for y in range(cy + 1, -3):
                t = (y - cy) / (-3 - cy)
                f.g.put(*P(x0 + (x1 - x0) * t + sag * math.sin(t * math.pi), y), ">" if (y + i) % 3 else "<")
        if i == 1:
            for x in (-4, 0, 4): f.g.put(x, -3, "S")
        tug.append(f.done("0"))
    fx("FxItemMarionetteTug", [("Tug", tug, [0.06, 0.1, 0.12, 0.12])], (16, 30), (8, 29), outdir,
       "Marionette Cross: strings jerk the monster that hit you (shown with its daze)")


# ================================================================================================ zhekra / kaurn / ysveld items
def build_godpack_items(outdir):
    # Acid Spit glob (webBall: hits the floor point, drawn 10 px up)
    gl = []
    for i in range(4):
        f = Fr()
        for k in range(6):
            f.n.put(*P(-4.5 - k * 1.4 - (i % 2), math.sin(k * 1.3 + i) * 1.6), "A" if k < 2 else "z" if k < 4 else "y")
        sq = 0.1 * math.sin(i * math.pi / 2)
        ell(f.b, 0, 0, 3.8 * (1 + sq), 3.2 * (1 - sq), TOX, bias=0.15)
        f.b.put(0, -4, "o"); f.b.put(-1, -5, "p")                # a leaf-sac stem, like the icon
        f.g.put(-1, -1, "B"); f.g.put(*P(1, 1 - (i % 2)), "B")
        gl.append(f.done("y"))
    sp = []
    for i in range(5):
        c = Canvas(); t = (i + 1) / 5
        sparks(c, 9, 0, 0, 2, 8, "BAz", seed=91, t=t, up=3)
        if i < 2: ell(c, 0, 0, 3 - i * 0.5, 2.5, "zAB", bias=0.3)
        sp.append(spr(c))
    fx("FxItemAcidSpit", [("Fly", gl, [0.08] * 4)], (22, 14), (11, 17), outdir,
       "Acid Spit glob (webBall: floor point, drawn 10 px up); it lands as FxItemAcidPool")
    # Hive Amber: amber ring bursting out of the hero (ground 32 x 14) and the resin pop on the hero
    d = god_durations("FxZhkResinBurst", "Play")
    rb = []
    for i in range(5):
        c = Canvas(); g = Canvas()
        r = [4, 8, 12, 14, 15][i]; ry = r * 0.42
        for k in range(12):
            a = 2 * math.pi * k / 12 + 0.2
            x, y = r * math.cos(a), ry * math.sin(a)
            if i < 4:
                # little hexagonal amber cells flung out
                ell(c, x, y - 1, 1.6 - i * 0.2, 1.3, "#$%", bias=0.3)
                if k % 3 == 0 and i < 3: g.put(*P(x, y - 2), "^")
                if k % 2 and i < 3: line(c, x * 0.55, y * 0.55 - 1, x, y - 1, "#")
            elif k % 2:
                c.put(*P(x, y), "#")
        if i < 2: ell(c, 0, -2, 3.5 - i, 2.4 - i * 0.5, "$%^", bias=0.4)
        px = outl(c.px, "@"); px.update(g.px)
        rb.append(Spr(px))
    pop = []
    for i in range(5):
        c = Canvas(); g = Canvas(); t = (i + 1) / 5
        cy = -8
        for k in range(6):          # honeycomb shards
            a = k * 1.05 + 0.4
            x, y = math.cos(a) * 9 * t, cy + math.sin(a) * 6 * t + 5 * t * t
            poly(c, [(x - 1.5, y), (x - 0.7, y - 1.3), (x + 0.7, y - 1.3), (x + 1.5, y), (x + 0.7, y + 1.3), (x - 0.7, y + 1.3)],
                 "$" if k % 2 else "%")
        if i < 2: ell(c, 0, cy, 4 - i, 3.5 - i, "#$%^", bias=0.4)
        for k in range(3): g.put(*P(-3 + k * 3, cy + 2 + i * 1.5), "#")
        px = outl(c.px, "@") if i < 4 else dict(c.px)
        px.update(g.px)
        pop.append(Spr(px))
    fx("FxItemHiveAmber", [("Burst", rb, d), ("Pop", pop, [0.05, 0.06, 0.07, 0.09, 0.12])], (38, 22), (19, 15), outdir,
       "Hive Amber resin ring (ground 32x14) + honeycomb pop at the hero")
    # Chain Spark: an electric spark with forked tendrils, and the jump flash
    cs = []
    for i in range(4):
        f = Fr()
        rnd = random.Random(i * 3 + 1)
        ell(f.g, 1, 0, 2.6, 2.2, "89!", bias=0.6)
        for k in range(3):
            x, y = 1, 0
            ang = math.radians(150 + k * 30 + rnd.uniform(-15, 15))
            for j in range(4):
                nx = x + math.cos(ang) * 2.2 + rnd.uniform(-0.8, 0.8)
                ny = y + math.sin(ang) * 2.2 + rnd.uniform(-1, 1)
                line(f.g, x, y, nx, ny, "9" if j < 2 else "8")
                x, y = nx, ny
        for k in range(2):
            a = rnd.uniform(-0.8, 0.8)
            line(f.g, 3, 0, 3 + 4 * math.cos(a), 4 * math.sin(a), "9")
        f.g.put(2, -1, "!")
        cs.append(f.done(None))
    hit = []
    for i in range(4):
        c = Canvas(); t = (i + 1) / 4
        rnd = random.Random(40 + i)
        for k in range(6):
            a = k * 1.05 + rnd.uniform(-0.3, 0.3)
            x, y = 0, 0
            for j in range(3):
                nx, ny = x + math.cos(a) * 2.4 * t + rnd.uniform(-1, 1), y + math.sin(a) * 2.4 * t + rnd.uniform(-1, 1)
                line(c, x, y, nx, ny, "9" if i < 2 else "8" if i < 3 else "7")
                x, y = nx, ny
        if i < 2: ell(c, 0, 0, 2.5 - i, 2.5 - i, "9!!", bias=0.6)
        hit.append(spr(c))
    fx("FxItemChainSpark", [("Fly", cs, [0.05] * 4), ("Hit", hit, [0.04, 0.05, 0.06, 0.08])], (22, 18), (11, 9), outdir,
       "Chain Spark spark (box 11x10) + jump / hit flash")
    # Lightning Rod ball lightning: a crackling sphere with a copper glint
    bl = []
    for i in range(4):
        f = Fr()
        ell(f.g, 0, 0, 4.6, 4.6, "7899", bias=0.15, hollow=0.55)
        ell(f.g, 0, 0, 2.6, 2.6, "9!!", bias=0.5)
        rnd = random.Random(i * 7 + 2)
        for k in range(4):
            a = rnd.uniform(0, 2 * math.pi)
            x, y = 4.5 * math.cos(a), 4.5 * math.sin(a)
            line(f.g, x, y, x + 2.5 * math.cos(a + 0.6), y + 2.5 * math.sin(a + 0.6), "9")
        f.g.put(*P(-2 + (i % 2), -2), "$")
        f.g.put(*P(1, 1 - (i % 2)), "!")
        bl.append(f.done(None))
    pop = []
    for i in range(5):
        c = Canvas(); t = (i + 1) / 5
        ring(c, 0, 0, 2 + 8 * t, 2 + 8 * t, "9" if i < 3 else "7", gap=lambda a, i=i: (int(a) // 30 + i) % 3 == 0)
        if i < 2: ell(c, 0, 0, 3.5 - i, 3.5 - i, "9!!", bias=0.6)
        sparks(c, 6, 0, 0, 3, 9, "9!$", seed=95, t=t)
        pop.append(spr(c))
    fx("FxItemRodBall", [("Fly", bl, [0.07] * 4), ("Pop", pop, [0.04, 0.05, 0.06, 0.08, 0.1])], (24, 24), (12, 12), outdir,
       "Lightning Rod ball lightning (box 11x10) + burst")
    # Icicle Requiem: shadow grows, an icicle falls (Fall 8, same 0.7 s telegraph), shatters on the floor (Shatter 5)
    dfall = god_durations("FxYsvIcicle", "Fall"); dsh = god_durations("FxYsvIcicle", "Shatter")
    fall = []
    for i in range(8):
        f = Fr()
        t = (i + 1) / 8
        ell(f.n, 0, 0, 3 + 5 * t, 1.2 + 1.8 * t, "``3", bias=-0.6)
        ring(f.n, 0, 0, 3.5 + 5 * t, 1.6 + 1.9 * t, "4" if i % 2 else "5", gap=lambda a: int(a) % 60 < 20)   # frost telegraph
        y = -48 + 46 * (t ** 2.2)
        if i >= 1:
            poly(f.b, [(-3.2, y - 12), (3.2, y - 12), (0, y)], lambda x, yy: "6" if x < 0 else "5" if x < 2 else "4")
            ell(f.b, 0, y - 12, 3.8, 1.6, "456", bias=0.2)               # the crown-like cap
            for x in (-3, 0, 3): f.b.put(x, int(y) - 14, "5")
            f.g.put(0, int(y) - 1, "6")
            for k in range(2): f.g.put(*P(-1 + k * 2, y - 11 - k - (i % 2)), "5")
        fall.append(f.done("3"))
    sh = []
    for i in range(5):
        c = Canvas(); g = Canvas(); t = (i + 1) / 5
        rnd = random.Random(5)
        for k in range(8):
            a = rnd.uniform(-math.pi, 0)
            r = rnd.uniform(3, 10) * t
            x, y = math.cos(a) * r, math.sin(a) * r * 0.7 + 4 * t * t
            if y > 0: y = 0
            poly(c, [(x - 1, y), (x, y - 2.5 + t), (x + 1, y)], "5" if k % 2 else "6")
        ring(g, 0, 0, 3 + 6 * t, 1.5 + 3 * t, "5" if i < 3 else "4", gap=lambda a: int(a) % 50 < 18)
        if i < 2: ell(c, 0, -1, 3.2 - i, 2 - i * 0.6, "456", bias=0.3)
        px = outl(c.px, "3"); px.update(g.px)
        sh.append(Spr(px))
    fx("FxItemIcicle", [("Fall", fall, dfall), ("Shatter", sh, dsh)], (24, 56), (12, 52), outdir,
       "Icicle Requiem: crowned icicle falls on its telegraph (0.7 s), shatters (ground 18x10)")
    # Widow's Shawl: a frost-silk web ring (ground 48 x 20) + a puff at the hero
    d = god_durations("FxYsvNova", "Play")
    nv = []
    for i in range(6):
        c = Canvas(); g = Canvas(); t = (i + 1) / 6
        rx, ry = 25 * t, 10.5 * t
        n = 10
        for k in range(n):        # radial silk threads
            a = 2 * math.pi * k / n
            line(c, rx * 0.15 * math.cos(a), ry * 0.15 * math.sin(a), rx * math.cos(a), ry * math.sin(a), "=[" if i < 4 else "[")
        for f_ in (0.45, 0.75, 1.0):   # the web's spiral rings
            if i >= 4 and f_ < 0.7: continue
            ring(c, 0, 0, rx * f_, ry * f_, "=" if f_ < 1 else "6", gap=lambda a, f_=f_: (int(a) // 36 + int(f_ * 4)) % 5 == 0)
        sparks(g, 8, 0, 0, rx * 0.4, rx * 1.0, "6=5", seed=99, t=1.0, yk=0.42)
        px = dict(c.px)
        px.update(g.px)
        nv.append(Spr(px))
    pf = []
    for i in range(4):
        c = Canvas(); t = (i + 1) / 4
        for k in range(6):
            a = k * 1.05
            x, y = math.cos(a) * 6 * t, -8 + math.sin(a) * 5 * t
            ell(c, x, y, 2.2 - t, 1.8 - t * 0.8, "[=6", bias=0.3)
        if i < 2: ell(c, 0, -8, 3 - i, 3 - i, "=66", bias=0.4)
        pf.append(spr(c))
    fx("FxItemShawl", [("Nova", nv, d), ("Puff", pf, [0.04, 0.05, 0.06, 0.08])], (54, 26), (27, 15), outdir,
       "Widow's Shawl frost-silk web (ground 48x20) + silk puff at the hero")


# ================================================================================================ procs / actives
def build_procs(outdir):
    # Ember Heart / Venom Gland / Rime Ring: a 4-frame flare on the monster as the item applies its status
    eh = []
    for i in range(4):
        c = Canvas(); g = Canvas(); t = (i + 1) / 4
        if i < 3:
            s = [0.6, 1.0, 0.8][i]
            # a little heart of embers
            for (x, y) in ((-2, -1), (-1, -2), (1, -2), (2, -1), (-2, 0), (-1, -1), (0, -1), (1, -1), (2, 0), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (0, 2)):
                c.put(*P(x * s, y * s - i), "c" if y < 0 else "b")
            g.put(0, -i, "d" if i < 2 else "c")
        for k in range(5):
            a = k * 1.25 + 0.3
            g.put(*P(math.cos(a) * 6 * t, math.sin(a) * 4 * t - 3 * t), "d" if k % 2 else "c")
        px = outl(c.px, "a") if i < 3 else dict(c.px)
        px.update(g.px)
        eh.append(Spr(px))
    fx("FxItemEmberHeart", [("Proc", eh, [0.04, 0.06, 0.08, 0.1])], (16, 16), (8, 9), outdir, "Ember Heart ignite flare")
    vg = []
    for i in range(4):
        c = Canvas(); g = Canvas(); t = (i + 1) / 4
        if i < 2: ell(c, 0, 0, 2.5 + i, 2 + i * 0.6, "yzAB", bias=0.3)
        for k in range(6):
            a = -math.pi + k * math.pi / 5
            x, y = math.cos(a) * 6 * t, math.sin(a) * 5 * t + 6 * t * t
            g.put(*P(x, y), "B" if k % 2 else "A"); g.put(*P(x, y + 1), "z")
        if i >= 1: g.put(0, -2 + i, "w")
        px = outl(c.px, "y"); px.update(g.px)
        vg.append(Spr(px))
    fx("FxItemVenomGland", [("Proc", vg, [0.04, 0.06, 0.08, 0.1])], (16, 16), (8, 8), outdir, "Venom Gland poison splash")
    rr = []
    for i in range(4):
        c = Canvas(); g = Canvas(); t = (i + 1) / 4
        ring(c, 0, 0, 2 + 5 * t, 2 + 5 * t, "5" if i < 2 else "4", gap=lambda a, i=i: (int(a) // 45 + i) % 2 == 0)
        curse_mark(g, 0, 0, "Frost", s=2 if i < 3 else 1)
        if i == 3: g.put(0, 0, "4")
        rr.append(Spr(dict(list(c.px.items()) + list(g.px.items()))))
    fx("FxItemRimeRing", [("Proc", rr, [0.04, 0.06, 0.08, 0.1])], (16, 16), (8, 8), outdir, "Rime Ring freeze snap")
    # Leech Seed heal (per kill) and Brine Flask regen
    ls = []
    for i in range(5):
        c = Canvas(); g = Canvas(); t = (i + 1) / 5
        if i < 3:
            ell(c, 0, -2, 1.6, 2, "&*(", bias=0.3)            # the red seed at the feet
            line(c, 0, -4, 0, -4 - i * 3, "o")
            g.put(1, -5 - i * 3, "q")
        for k in range(5):
            x = -6 + k * 3
            y = -4 - t * 14 - (k % 2) * 3
            g.put(*P(x, y), "q" if k % 2 else "(")
            if i < 4: g.put(*P(x, y + 1), "p")
        if i >= 2: g.put(0, -18 - i, "q"); g.put(-1, -17 - i, "q"); g.put(1, -17 - i, "q"); g.put(0, -16 - i, "q")
        px = outl(c.px, "&"); px.update(g.px)
        ls.append(Spr(px))
    fx("FxItemLeechSeed", [("Heal", ls, [0.05, 0.07, 0.09, 0.11, 0.13])], (16, 26), (8, 25), outdir, "Leech Seed: the kill's life drawn into you")
    bf = []
    for i in range(5):
        g = Canvas(); t = (i + 1) / 5
        for k in range(6):
            x = -6 + (k * 5) % 13
            y = -2 - t * 16 - (k * 3) % 5
            if (k + i) % 4 == 3: continue
            g.put(*P(x, y), "X"); g.put(*P(x + 1, y), "W"); g.put(*P(x, y + 1), "V"); g.put(*P(x + 1, y + 1), "U")
        cy = -10 - i * 2
        if 1 <= i <= 3:
            for (x, y) in ((0, -1), (-1, 0), (0, 0), (1, 0), (0, 1)): g.put(x, cy + y, "A" if (x, y) == (0, 0) else "z")
        bf.append(spr(g))
    fx("FxItemBrineFlask", [("Regen", bf, [0.06, 0.08, 0.1, 0.12, 0.14])], (16, 28), (8, 27), outdir, "Brine Flask regen bubbles")
    # Barnacle Shell: shell crust closes round the hero's legs (On 3), then holds (Loop 4)
    def shell(i, close):
        f = Fr()
        for s in (-1, 1):
            cx = s * (6 - 2 * close)
            ell(f.b, cx, -4, 3.4, 4.4, "sttk" if s < 0 else "stkl", ang=s * 20, bias=0.2)
            for k in range(3):                 # ribs of the shell
                y = -6 + k * 2
                f.b.put(*P(cx + s * 0.5, y), "j"); f.b.put(*P(cx + s * 1.5, y), "l")
        for k in range(5):                     # white barnacle cones crusted on
            x = -6 + k * 3
            f.b.put(x, -1, "l"); f.b.put(x, -2, "m"); f.b.put(x + 1, -1, "k")
            if (k + i) % 2: f.b.put(x, -3, "k")
        if close >= 1:
            g = (i % 4)
            f.g.put(-5 + g * 3, -7, "W")       # a glint of wet shell
        return f.done("0")
    on = [shell(0, c) for c in (0.0, 0.5, 1.0)]
    lp = [shell(i, 1.0) for i in range(4)]
    fx("FxItemBarnacle", [("On", on, [0.06, 0.06, 0.08]), ("Loop", lp, [0.2] * 4)], (22, 14), (11, 13), outdir,
       "Barnacle Shell crust while you stand still (35% less damage)")
    # Hourglass of Ash (spell cast) and Glass Mask (hit taken)
    hg = []
    for i in range(5):
        g = Canvas()
        cy = -22
        for k in range(4):                      # ash falling round the hero
            g.put(*P(-6 + k * 4, cy + 8 + i * 2 + (k % 2) * 3), "-" if k % 2 else "+")
        hg.append(layered(pen_spr(V2.ash_hourglass, i % 2, S=0.62, turn=[0, 45, 90, 135, 180][i], at=(0, cy)), spr(g)))
    fx("FxItemHourglass", [("Proc", hg, [0.06, 0.06, 0.06, 0.08, 0.12])], (16, 34), (8, 33), outdir,
       "Hourglass of Ash: the glass turns as you cast (spells recharge faster)")
    gm = []
    for i in range(4):
        cy = -22
        s_ = pen_spr(V2.glass_mask, 1 if i >= 1 else 0, S=0.62, at=(0, cy))
        if i >= 2:
            g = Canvas()
            sparks(g, 6, 0, cy, 4, 8, "FE", seed=101, t=(i - 1) / 2, up=3)
            s_ = layered(s_, spr(g))
        gm.append(fade(s_) if i == 3 else s_)
    fx("FxItemGlassMask", [("Crack", gm, [0.05, 0.08, 0.1, 0.1])], (16, 32), (8, 31), outdir,
       "Glass Mask: the mask cracks when a hit gets through (you take 35% more)")


# ================================================================================================ follower tokens
TOKEN_DRAW = {"apple": GI.rotting_apple, "wick": V2.saints_wick, "rod": GI.lightning_rod}


def token(kind, state, i):
    """The follower: the item's own icon drawing at 0.72 scale (about 12 px; vanilla's Book of Tears token is 7x7),
    bobbing over the origin. state: Idle, Ready, Activate, Wait (greyed out, a cooldown pip circling), WakeUp."""
    bob = round(math.sin(i * 2 * math.pi / 12)) if state == "Idle" else 0
    cy = -8 + bob
    spent = state == "Wait"
    glow = 0.0
    if state == "Activate":
        glow = [0.2, 0.5, 0.9, 1.0, 0.6, 0.3, 0.1, 0.0, 0.0, 0.0][i]
    if state == "Ready": glow = 0.4 + 0.3 * i
    ph = 1 if (glow > 0.5 or (state == "Idle" and i % 6 == 3)) else 0
    sway = 7 * math.sin(i * 2 * math.pi / 12 + 1.2) if (state == "Idle" and kind != "wick") else 0.0
    body = pen_spr(TOKEN_DRAW[kind], ph, S=0.72, turn=sway, at=(0, cy), remap=grey if spent else None)
    g = Canvas()
    if not spent:
        if kind == "apple":
            if glow > 0.3: g.put(4, cy + 1, "]"); g.put(5, cy, "]")               # maggots lean out to fire
            if glow > 0.7: g.put(6, cy - 1, "{"); g.put(4, cy + 2, "{")
        elif kind == "wick":
            if glow > 0.6: ring(g, 0, cy - 5, 4, 3.6, "S", gap=lambda a: int(a) % 60 < 25)
            if glow > 0.2: g.put(0, cy - 8 - int(glow * 2), "e")
            if state == "Idle" and i % 4 == 1: g.put(-1 + (i % 3), cy - 8, "d")
        else:
            if glow > 0.2 or (state == "Idle" and i % 4 == 0):
                for k in range(int(1 + glow * 4)):
                    a = i * 1.7 + k * 1.6
                    g.put(*P(math.cos(a) * 3.4, cy - 6 + math.sin(a) * 2), "9" if k % 2 else "8")
    if state == "WakeUp":
        ring(g, 0, cy, 3 + i * 1.5, 3 + i * 1.5, "F" if i < 2 else "E", gap=lambda a: int(a) % 90 < 40)
    if spent:                       # the cooldown pip circling the dimmed token (like vanilla's grey dot)
        a = i * 2 * math.pi / 6
        g.put(*P(6.0 * math.cos(a), cy + 4 * math.sin(a)), "+")
    return layered(body, spr(g))


def build_tokens(outdir):
    for kind, name, note in (("apple", "FxItemTokenApple", "Rotting Apple follower"), ("wick", "FxItemTokenWick", "Saint's Wick follower"),
                             ("rod", "FxItemTokenRod", "Lightning Rod follower")):
        fx(name, [("Idle", [token(kind, "Idle", i) for i in range(12)], [0.117] * 12),
                  ("Ready", [token(kind, "Ready", i) for i in range(2)], [0.1, 0.1]),
                  ("Activate", [token(kind, "Activate", i) for i in range(10)], [0.1, 0.067, 0.067, 0.067, 0.1, 0.1, 0.1, 0.12, 0.12, 0.12]),
                  ("Wait", [token(kind, "Wait", i) for i in range(6)], [0.167] * 6),
                  ("WakeUp", [token(kind, "WakeUp", i) for i in range(4)], [0.05] * 4)], (16, 18), (8, 17), outdir, note, scale=8)


# ================================================================================================ shop bubbles (Wickwalk, Votive Candle)
def build_bubbles(outdir):
    """Wickwalk and Votive Candle had 1-frame bubbles; every other item's bubble has 2. Frame 2 makes their flames
    dance (flame pixels shift and brighten), drawn from the same art."""
    FL = {(0xc8, 0x55, 0x1a), (0xf2, 0x8a, 0x26), (0xff, 0xd8, 0x5e), (0xff, 0xf3, 0xb8)}
    for src, name in (("out_heroes/IconWickwalk", "IconItemWickwalkBubble"), ("out_heroes/IconVotiveCandle", "IconItemVotiveBubble")):
        im = Image.open(os.path.join(ROOT, "art", src + ".png")).convert("RGBA")
        m = json.load(open(os.path.join(ROOT, "art", src + ".json")))
        cw, ch = m["cellW"], m["cellH"]
        f0 = im.crop((0, 0, cw, ch))
        p0 = f0.load()
        f1 = f0.copy()
        p1 = f1.load()
        flame = [(x, y) for y in range(ch) for x in range(cw) if p0[x, y][3] and (p0[x, y][:3] in FL or (p0[x, y][0] > 200 and p0[x, y][1] > 100 and p0[x, y][2] < 120))]
        if not flame:
            # fall back to the warmest pixels
            flame = [(x, y) for y in range(ch) for x in range(cw) if p0[x, y][3] and p0[x, y][0] > 180 and p0[x, y][2] < 110]
        tops = {}
        for (x, y) in flame: tops[x] = min(tops.get(x, 99), y)
        for (x, y) in flame:
            r, g, b, a = p0[x, y]
            # brighten one step and lick the top rows up a pixel
            p1[x, y] = (min(255, r + 20), min(255, g + 40), min(255, b + 30), a)
            if y == tops[x] and y > 0 and (x % 2 == 0 or len(flame) < 60) and not p0[x, y - 1][3]:
                p1[x, y - 1] = (0xf2, 0x8a, 0x26, 255)
        out = Image.new("RGBA", (128, 64), (0, 0, 0, 0))
        out.paste(f0, (0, 0)); out.paste(f1, (cw, 0))
        out.save(os.path.join(outdir, name + ".png"))
        man = {"cellW": cw, "cellH": ch, "cols": 2, "anims": [{"name": "Bubble", "frames": [0, 1], "durations": [0.5, 0.5]}]}
        json.dump(man, open(os.path.join(outdir, name + ".json"), "w"))
        preview(out, man, os.path.join(outdir, name + "_preview.png"), scale=4)
        print("built %-24s 2-frame shop bubble from %s (%d flame px)" % (name, src, len(flame)))


# ================================================================================================ TIMING.md
def write_timing(outdir):
    L = ["# Item FX timing (tools/sprites/item_fx.py)", "",
         "Every sheet's json has `origin: [x, y]`: the cell pixel placed on the effect's spawn point (ItemArt.Place ->",
         "Strike.ArtAt). Pixel coordinates below are relative to that origin, x right, y up NEGATIVE.",
         "Durations copied from a monster sheet keep the replaced effect's clip length and damage events (listed as 'timing of').", ""]
    for n in ORDER:
        b = BUILT[n]
        L.append("## %s  (cell %dx%d, origin %d,%d)" % (n, b["cell"][0], b["cell"][1], b["origin"][0], b["origin"][1]))
        if b["note"]: L.append(b["note"])
        for a, cnt, d in b["anims"]:
            L.append("- %s: %d frames, %.2f s: %s" % (a, cnt, sum(d), ", ".join("%.3g" % x for x in d)))
        L.append("")
    L += ["## Sync points used by the code", "",
          "- FxItemWickFire / FxItemVotive / FxItemWaxFire Life: damage on frame 0, off 3 frames from the end (the 6-frame loop x5 of the",
          "  burning pool, 2.7 s).",
          "- FxItemWaxSlick Life: slow zone live from frame 2 to 3 frames from the end (FxWaxPuddle timing, 5.96 s).",
          "- FxItemThornwall / FxItemThornMail Life: damage frames 3..21 (FxThornPatch timing, 7.95 s).",
          "- FxItemUndertowBrine / FxItemRiptidePool Life: zone live from frame 1 to 3 from the end (FxBrine timing, 8.36 s).",
          "- FxItemAcidPool Life: damage frames 2..15 (FxZhkAcidPool timing).",
          "- FxItemMarrowSpikes Play: damage frames 0..3; FxItemBellToll Ring 0..3; FxItemTideBurst Ring 0..3; FxItemHiveAmber Burst 1..3;",
          "  FxItemShawl Nova 0..4; FxItemMirrorShatter 1..3; FxItemSporeBurst 1..4; FxItemRootSnare 3..5; FxItemIcicle Shatter 0..2.",
          "- FxItemSoulBurst Burst: the vanilla skydropExplode events (damage on 0.12 s, off 0.37 s): same 11 frame times.",
          "- FxItemIcicle Fall: 0.7 s telegraph, then Shatter spawns on the same spot.",
          "- Tokens: Activate fires the shot (AnimAttack 0 + AnimFlash) at the start of frame 3 (the brightest frame).",
          "- Runner sheets ride the HeroSlimeDropper / WebDropper runner (anchor: feet at the origin).", ""]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L))


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    build_fire(outdir)
    build_floor_fires(outdir)
    build_runners(outdir)
    build_puddles(outdir)
    build_thorns(outdir)
    build_bone(outdir)
    build_plates(outdir)
    build_plants(outdir)
    build_glass(outdir)
    build_soul(outdir)
    build_bell_sea(outdir)
    build_jinx(outdir)
    build_godpack_items(outdir)
    build_procs(outdir)
    build_tokens(outdir)
    build_bubbles(outdir)
    write_timing(outdir)
    print("%d FX sheets" % len(ORDER))


if __name__ == "__main__":
    main()
