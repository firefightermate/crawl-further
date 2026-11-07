"""Design-scale support for the procedural rigs (v0.7 size pass).

Monsters were authored in a "design" pixel space. To make a monster smaller we do NOT resample its
finished pixels: every frame is re-rendered with the rig's geometry (coordinates, radii, lengths) multiplied
by a scale factor before rasterisation, so outlines stay 1px, lines stay 1px and shading is recomputed at the
new size. Hand-drawn char-grid parts (faces, skulls) are shrunk by carving out their least important rows and
columns (whole pixel rows are dropped, never blended), or replaced by hand-made small versions.

    with scaled(0.6):            # every SCanvas created inside draws at 0.6
        frames = build(...)

Rig modules opt in with install(module, {...}) which wraps their primitive functions so that, when they
draw on an SCanvas with s != 1, the geometry arguments are scaled and the original primitive rasterises onto
the canvas' raw (unscaled) view.
"""
import math
from rig import Canvas, Part

_STACK = [(1.0, None)]
RMIN = 0.55          # thin tubes / lines keep at least this radius so they stay continuous 1px strokes
EMIN = 0.6           # tiny ellipses (dots) stay at least one pixel


def cur():
    return _STACK[-1][0]


def cur_part():
    s, ps = _STACK[-1]
    return s if ps is None else ps


class scaled:
    def __init__(self, s, part_s=None):
        self.s, self.ps = float(s), part_s

    def __enter__(self):
        _STACK.append((self.s, self.ps))
        return self

    def __exit__(self, *a):
        _STACK.pop()


def rnd(v):
    return int(math.floor(v + 0.5))


def S(v):
    """Scale a design length (float)."""
    return v * cur()


def Si(v):
    """Scale a design length and round to whole pixels."""
    return rnd(v * cur())


# ------------------------------------------------------------------ part carving
PART_SUBST = {}      # id(original part) -> {scale: replacement Part}  (hand-made small versions)
IMPORTANT = set("cBQGyYRLZXF")   # glow / eye / highlight chars that make a row worth keeping


def _carve_axis(px, axis, n_remove, protect):
    """Remove n_remove whole rows (axis=1) or columns (axis=0) choosing those most similar to a neighbour."""
    px = dict(px)
    for _ in range(n_remove):
        idx = sorted(set(k[axis] for k in px))
        if len(idx) <= 1: break
        lo, hi = idx[0], idx[-1]
        best, bcost = None, None
        for r in range(lo, hi + 1):
            row = {k[1 - axis]: v for k, v in px.items() if k[axis] == r}
            costs = []
            for nb in (r - 1, r + 1):
                if nb < lo or nb > hi: continue
                other = {k[1 - axis]: v for k, v in px.items() if k[axis] == nb}
                diff = 0.0
                for j in set(row) | set(other):
                    a, b = row.get(j), other.get(j)
                    if a != b:
                        diff += 1.0
                        if a in protect: diff += 2.5
                costs.append(diff)
            if not costs: continue
            cost = min(costs) + 0.15 * len(row) / 10.0
            # prefer interior rows over silhouette edges (edges carry the shape)
            if r in (lo, hi): cost += 0.6
            if bcost is None or cost < bcost: best, bcost = r, cost
        if best is None: break
        out = {}
        for k, v in px.items():
            if k[axis] == best: continue
            if k[axis] > best:
                # rows below / right of the removed one move toward the pivot side
                k = (k[0] - 1, k[1]) if axis == 0 else (k[0], k[1] - 1)
            out[k] = v
        px = out
    return px


def carve(part, s, protect=IMPORTANT):
    """Shrink a char-grid part to ~s of its size by dropping whole rows/columns (pivot kept on its pixel)."""
    if s >= 0.999 or not part.px: return part
    sub = PART_SUBST.get(id(part))
    if sub:
        for k in sorted(sub, key=lambda k: abs(k - s)):
            if abs(k - s) < 0.09: return sub[k]
    key = (id(part), round(s, 3))
    if key in _CARVED: return _CARVED[key]
    xs = [k[0] for k in part.px]; ys = [k[1] for k in part.px]
    w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    nw, nh = max(1, rnd(w * s)), max(1, rnd(h * s))
    # re-centre around the pivot: carving shifts pixels toward lower indices; keep the pivot's relative place
    px = _carve_axis(part.px, 1, h - nh, protect)
    px = _carve_axis(px, 0, w - nw, protect)
    # keep the part's bottom / left relation to the pivot proportional
    xs2 = [k[0] for k in px]; ys2 = [k[1] for k in px]
    tx = rnd((min(xs) + max(xs)) * 0.5 * s - (min(xs2) + max(xs2)) * 0.5)
    ty = rnd((min(ys) + max(ys)) * 0.5 * s - (min(ys2) + max(ys2)) * 0.5)
    p = Part.__new__(Part)
    p.px = {(x + tx, y + ty): v for (x, y), v in px.items()}
    _CARVED[key] = p
    return p


_CARVED = {}


# ------------------------------------------------------------------ canvas
class RawView:
    """Unscaled view of an SCanvas (what the original primitives draw on)."""

    def __init__(self, owner):
        self._o = owner
        self.s = 1.0

    @property
    def px(self):
        return self._o.px

    @px.setter
    def px(self, v):
        self._o.px = v

    def put(self, x, y, c, over=True):
        if over or (x, y) not in self._o.px:
            self._o.px[(x, y)] = c

    def part(self, part, x, y, dx=0, dy=0):
        for (px_, py_), c in part.px.items():
            self.put(x + px_ + dx, y + py_ + dy, c)

    def limb(self, *a, **k):
        return Canvas.limb(self, *a, **k)

    def spr(self):
        return self._o.spr()


class SCanvas(Canvas):
    """Canvas whose put/part/limb take design coordinates and draw at the current scale."""

    def __init__(self, s=None):
        self.px = {}
        self.s = cur() if s is None else s
        self.ps = cur_part() if s is None else s
        self.raw = RawView(self)

    def put(self, x, y, c, over=True):
        if self.s != 1.0:
            x, y = rnd(x * self.s), rnd(y * self.s)
        if over or (x, y) not in self.px:
            self.px[(x, y)] = c

    def part(self, part, x, y, dx=0, dy=0):
        if self.s == 1.0:
            return Canvas.part(self, part, x, y, dx, dy)
        p = carve(part, self.ps)
        ax, ay = rnd((x + dx) * self.s), rnd((y + dy) * self.s)
        for (px_, py_), c in p.px.items():
            self.px[(ax + px_, ay + py_)] = c

    def limb(self, x, y, segs, colors, width=1, end=None):
        if self.s == 1.0:
            return Canvas.limb(self, x, y, segs, colors, width, end)
        s = self.s
        ex, ey = Canvas.limb(self.raw, x * s, y * s, [(ln * s, a) for ln, a in segs], colors, width, None)
        if end is not None:
            self.raw.part(carve(end, self.ps), ex, ey)
        return rnd(ex / s), rnd(ey / s)   # Canvas.limb returns whole pixels; callers rely on ints


# ------------------------------------------------------------------ primitive wrapping
def _conv(kind, v, s):
    if v is None: return v
    if kind == "x": return v * s
    if kind == "r": return max(v * s, min(v, RMIN))
    if kind == "e": return max(v * s, min(v, EMIN))
    if kind == "P": return [(p[0] * s, p[1] * s) for p in v]
    if kind == "R": return [max(r * s, min(r, RMIN)) for r in v]
    if kind == "m":
        if callable(v):
            return lambda x, y, l, _f=v: _f(x / s, y / s, l)
        return v
    if kind == "sh":
        if callable(v):
            return lambda nu, nv, d, l, ch, x, y, _f=v: _f(nu, nv, d, l, ch, x / s, y / s)
        return v
    if kind == "m2":   # shade(x, y) callback
        if callable(v):
            return lambda x, y, _f=v: _f(x / s, y / s)
        return v
    if kind == "box":
        return tuple(q * s for q in v)
    if kind == "p":   # part
        return carve(v, s)
    return v


def wrap(fn, spec, kw=None):
    """spec: kinds of the positional args after the canvas; kw: kinds of keyword args."""
    kw = kw or {}

    def w(c, *a, **k):
        s = getattr(c, "s", 1.0)
        if s == 1.0:
            return fn(c, *a, **k)
        a = list(a)
        for i in range(min(len(a), len(spec))):
            a[i] = _conv(spec[i], a[i], s)
        for n in list(k):
            if n in kw: k[n] = _conv(kw[n], k[n], s)
        with scaled(1.0):   # canvases the primitive makes internally are raw too
            return fn(c.raw, *a, **k)
    w.__wrapped__ = fn
    w.__name__ = fn.__name__
    return w


def install(mod, prims):
    """prims: name -> (positional kinds, keyword kinds). Replaces mod.<name> with a scaling wrapper and
    mod.Canvas with SCanvas."""
    for name, (spec, kw) in prims.items():
        fn = getattr(mod, name)
        fn = getattr(fn, "__wrapped__", fn)
        setattr(mod, name, wrap(fn, spec, kw))
    mod.Canvas = SCanvas


# ------------------------------------------------------------------ helpers for rig code that mixes spaces
def spt(x, y):
    """Design point -> pixel point at the current scale."""
    s = cur()
    return rnd(x * s), rnd(y * s)


def paste(c, spr_px, x, y, over=True):
    """Paste already-rendered pixels (dict or Spr) with their origin at design point (x, y)."""
    px = getattr(spr_px, "px", spr_px)
    ox, oy = spt(x, y)
    for (a, b), v in px.items():
        if over or (ox + a, oy + b) not in c.px:
            c.px[(ox + a, oy + b)] = v


def lit(d):
    """Scale a literal {(x, y): ch} dict authored in design pixels (later entries win on collisions)."""
    out = {}
    for (x, y), v in d.items():
        out[spt(x, y)] = v
    return out


def small(threshold=0.85):
    """True when the current build renders noticeably below authored size (use for proportion tweaks)."""
    return cur() < threshold


def subst(part, scale, grid, pivot):
    """Register a hand-drawn small version of `part` used when it is drawn at ~scale."""
    PART_SUBST.setdefault(id(part), {})[scale] = Part(grid, pivot)


def idle_bounds(img, man):
    """(w, h_from_feet) of the visible pixels over all Idle frames of a packed sheet."""
    a = {x["name"]: x for x in man["anims"]}.get("Idle")
    if not a: return None
    cw, ch, cols = man["cellW"], man["cellH"], man["cols"]
    W = H = 0
    for i in a["frames"]:
        cell = img.crop(((i % cols) * cw, (i // cols) * ch, (i % cols + 1) * cw, (i // cols + 1) * ch))
        b = cell.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if not b: continue
        W = max(W, b[2] - b[0]); H = max(H, (ch - 1) - b[1])
    return W, H


SCALE_NOTE = ("Design scale: the v0.7 size pass re-rendered these monsters smaller (geometry scaled before rasterising, "
              "not resampled). Spawn points / reach numbers written in the sync notes below are in the CURRENT pixels "
              "(already multiplied by the scale); src/CrawlFurther/SheetScales.cs holds the same factor per sheet so kit offsets "
              "authored for the old art are scaled at load.")


def scale_text_pts(text, s):
    """Rewrite every '(x, y)' pixel pair in a TIMING note to the scaled pixels (authored value kept alongside)."""
    import re
    if abs(s - 1.0) < 1e-6 or not isinstance(text, str): return text

    def f(m):
        x, y = float(m.group(1)), float(m.group(2))
        return "(%d, %d) [authored (%s, %s) x%.2f]" % (rnd(x * s), rnd(y * s), m.group(1), m.group(2), s)
    return re.sub(r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)", f, text)


def kwrap(fn, kinds, ret=None):
    """Wrap a pure pixel-dict generator: arguments named in `kinds` (name -> kind, defaults included) are
    scaled by the current design scale and the generator runs at scale 1 (so nested generators don't scale
    twice). Kinds: x (float), xi (rounded int), e/r (radius), P (points), Pt (one point), Pi (rounded point).
    ret: optional post-processor ret(result, s)."""
    import inspect
    sig = inspect.signature(fn)

    def w(*a, **k):
        s = cur()
        if s == 1.0:
            return fn(*a, **k)
        b = sig.bind(*a, **k); b.apply_defaults()
        for n, kind in kinds.items():
            v = b.arguments.get(n)
            if v is None: continue
            if kind == "xi": b.arguments[n] = rnd(v * s)
            elif kind == "Pt": b.arguments[n] = (v[0] * s, v[1] * s)
            elif kind == "Pi": b.arguments[n] = (rnd(v[0] * s), rnd(v[1] * s))
            else: b.arguments[n] = _conv(kind, v, s)
        with scaled(1.0):
            r = fn(*b.args, **b.kwargs)
        return ret(r, s) if ret else r
    w.__wrapped__ = fn
    w.__name__ = fn.__name__
    return w


def carve_spr(spr, s=None):
    """Shrink a hand-drawn whole-sprite char grid (e.g. a corpse) by dropping rows/columns; stays on the ground."""
    from anim import Spr
    s = cur_part() if s is None else s
    if s >= 0.999: return spr
    p = Part.__new__(Part); p.px = dict(spr.px)
    q = carve(p, s)
    if not q.px: return spr
    my = max(k[1] for k in q.px)
    return Spr({(x, y - my): v for (x, y), v in q.px.items()})
