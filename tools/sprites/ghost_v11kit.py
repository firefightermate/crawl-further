"""Shared drawing kit for the ghost form art (ghost_v11.py, ghost_custom.py).

Pixels are stored as RGB / RGBA tuples (not palette chars) so this art never collides with the packs that patch
anim.PALETTE at import time. The shaded primitives come from vhorrul_t3 (ell, tube, poly, line, Fr): ramps are lists of
RGB tuples, lit from the top-left, then a 1 px dark outline, then glow pixels on top.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, pack, preview  # noqa: E402
import vhorrul_t3 as V  # noqa: E402

ell, tube, poly, P, pick = V.ell, V.tube, V.poly, V.P, V.pick
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(os.path.dirname(os.path.dirname(HERE)), "build", "dump"))
BOARDS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "build", "boards")
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art", "out_ghosts")
OUT_DIR = [OUT]          # main() may point this at another folder


def hx(h, a=None):
    t = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return t if a is None else t + (a,)


def ramp(*hs):
    return [hx(h) for h in hs]


def line(c, x0, y0, x1, y1, col, over=True):
    cols = col if isinstance(col, list) else [col]
    pts = line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    for i, (x, y) in enumerate(pts):
        c.put(x, y, cols[i % len(cols)], over)
    return pts


# ------------------------------------------------------------------ colours
INK = hx("1e1a1c")
INK2 = hx("2b2228")
WHITE = hx("f4f2ea")
BLACK = hx("0e0c10")
STONE = [hx("3a3a40"), hx("58585f"), hx("7a7a82"), hx("9c9ca4"), hx("bebec4")]


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


class RSpr(Spr):
    """Sprite whose pixels are RGB or RGBA tuples."""

    def to_rgba(self):
        return {k: (v if len(v) == 4 else v + (255,)) for k, v in self.px.items()}

    def stone(self):
        return RSpr({k: STONE[min(4, int(lum(v) / 52))] for k, v in self.px.items() if (len(v) < 4 or v[3] > 40)})

    def copy(self):
        return RSpr(dict(self.px))

    def over(self, other):
        o = dict(self.px); o.update(other.px); return RSpr(o)

    def shift(self, dx, dy):
        return RSpr({(x + dx, y + dy): v for (x, y), v in self.px.items()})


def R(spr):
    return RSpr(spr.px if hasattr(spr, "px") else spr)


def done(f, ink=INK, outline=True):
    return R(f.done(outline=outline, ink=ink))


def grounded(s):
    b = s.bbox()
    return RSpr({(x, y - b[3]): v for (x, y), v in s.px.items()})


def floor(s):
    return RSpr({k: v for k, v in s.px.items() if k[1] <= 0})


def dissolve(s, keep, seed=1):
    import random
    r = random.Random(seed)
    return RSpr({k: v for k, v in s.px.items() if r.random() < keep})


def fade(s, a):
    """Lower the alpha of every pixel (spawn / fade frames of FX)."""
    out = {}
    for k, v in s.px.items():
        al = v[3] if len(v) == 4 else 255
        out[k] = v[:3] + (max(0, min(255, int(al * a))),)
    return RSpr(out)


def mirror(s):
    return RSpr({(-x, y): v for (x, y), v in s.px.items()})


def rot(s, deg, pivot=(0, 0)):
    """Nearest-neighbour rotation (reverse mapped, so no holes)."""
    if not s.px: return RSpr({})
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    xs = [k[0] for k in s.px]; ys = [k[1] for k in s.px]
    r = int(max(abs(min(xs) - pivot[0]), abs(max(xs) - pivot[0]), abs(min(ys) - pivot[1]), abs(max(ys) - pivot[1])) * 1.5) + 2
    out = {}
    for y in range(pivot[1] - r, pivot[1] + r + 1):
        for x in range(pivot[0] - r, pivot[0] + r + 1):
            dx, dy = x - pivot[0], y - pivot[1]
            sx = dx * ca + dy * sa + pivot[0]
            sy = -dx * sa + dy * ca + pivot[1]
            k = (int(round(sx)), int(round(sy)))
            if k in s.px: out[(x, y)] = s.px[k]
    return RSpr(out)


# ------------------------------------------------------------------ sheets
BUILT = {}


def mon_sheet(name, anims, outdir=None, scale=8, pad=2):
    outdir = outdir or OUT_DIR[0]
    """Monster sheet: cell sized round every frame, feet at (cw//2, ch-2)."""
    allf = [f for a in anims for f in a[1]]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
        for i, f in enumerate(fr):
            assert f.px, "%s/%s[%d] is empty" % (name, an, i)
            if max(p[1] for p in f.px) > 0:
                print("WARNING %s/%s[%d] has pixels below the floor" % (name, an, i))
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf)
    hw = max(-x0, x1 + 1) + pad
    cw = 2 * hw
    ch = -y0 + 1 + pad + 2
    feet = (cw // 2, ch - 2)
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    idle = anims[0][1][0].bbox()
    BUILT[name] = {"kind": "monster", "cell": (cw, ch), "feet": feet, "idle": (idle[2] - idle[0] + 1, -idle[1] + 1),
                   "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man}
    print("built %-16s cell %dx%d idle %dx%d  %s" % (name, cw, ch, BUILT[name]["idle"][0], BUILT[name]["idle"][1],
                                                    ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return BUILT[name]


def fx_sheet(name, anims, outdir=None, scale=8, origin=None):
    outdir = outdir or OUT_DIR[0]
    """FX sheet: origin = the effect's centre point (x centre of the cell). Returns the build record with the
    origin cell pixel, which the C# Strike.ArtAt / RingPair calls use."""
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf); y1 = max(f.bbox()[3] for f in allf)
    hw = max(-x0, x1 + 1) + 1
    top = -y0 + 1
    cw, ch = 2 * hw, top + max(0, y1) + 1
    org = (hw, top) if origin is None else origin
    img, man = pack(name, anims, cw, ch, org, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"kind": "fx", "cell": (cw, ch), "origin": org, "anims": [(a, len(f), list(d)) for a, f, d in anims],
                   "img": img, "man": man}
    print("built %-16s cell %dx%d origin (%d, %d)  %s" % (name, cw, ch, org[0], org[1],
                                                         ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return BUILT[name]


def fixed_sheet(name, anims, cw, ch, org, outdir=None, scale=8, kind="fx"):
    outdir = outdir or OUT_DIR[0]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
    if kind == "fx":
        from ghosts_v2_kit import selout_anims
        anims = selout_anims(anims)
    img, man = pack(name, anims, cw, ch, org, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"kind": kind, "cell": (cw, ch), "origin": org, "anims": [(a, len(f), list(d)) for a, f, d in anims],
                   "img": img, "man": man}
    print("built %-16s cell %dx%d origin (%d, %d)  %s" % (name, cw, ch, org[0], org[1],
                                                         ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return BUILT[name]


# vanilla slime Spawn timing (the base prefab's Spawn clip events keep their times; AnimAttack 3 = its splash ring)
SPAWN_DURS = [0.067, 0.083, 0.2, 0.2, 0.25]


def std_tail(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


# ------------------------------------------------------------------ ghost-body colour safety (player ramps)
_RAMPS = None


def ramps():
    """The three player ghost ramps (P2 red, P3 green, P4 yellow): slot -> rgb for the slots they remap."""
    global _RAMPS
    if _RAMPS is not None: return _RAMPS
    from PIL import Image
    out = []
    for n in ("PaletteRed_91", "PaletteGreen_90", "PaletteYellow_121"):
        pth = os.path.join(DUMP, "tex", n + ".png")
        if not os.path.exists(pth):
            _RAMPS = []; return _RAMPS
        im = Image.open(pth).convert("RGB"); px = im.load()
        out.append({(x, 63 - y): px[x, y] for x in range(256) for y in range(64) if px[x, y] != (255, 0, 255)})
    _RAMPS = out
    return out


def slot(c):
    r, g, b = c[:3]
    return min(15, r * 16 // 255) + 16 * min(15, g * 16 // 255), min(63, b * 64 // 255)


def ramp_safe(c):
    return all(slot(c) not in m for m in ramps())


def make_safe(c):
    """Nudge a prop colour until no player ramp would recolour it (keeps it as close as possible)."""
    if ramp_safe(c): return c
    best = None
    for d in range(1, 40):
        for dr in (-d, 0, d):
            for dg in (-d, 0, d):
                for db in (-d, 0, d):
                    n = (max(0, min(255, c[0] + dr)), max(0, min(255, c[1] + dg)), max(0, min(255, c[2] + db))) + tuple(c[3:])
                    if ramp_safe(n):
                        e = dr * dr + dg * dg + db * db
                        if best is None or e < best[0]: best = (e, n)
        if best: return best[1]
    raise ValueError("no ramp-safe colour near %r" % (c,))


def safe_ramp(*hs, a=None):
    return [make_safe(hx(h) if a is None else hx(h, a)) for h in hs]
