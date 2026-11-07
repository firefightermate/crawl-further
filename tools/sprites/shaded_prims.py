"""Shaded char-canvas primitives (ellipsoids, capsule chains, polygons, thorns, sprite helpers) shared by the ghost rigs.
They came out of the old Sylvene rig (sylvene_rigs.py, replaced by sylvene_v2_rigs.py) and draw onto rig.Canvas
with palette chars from anim.PALETTE."""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Part, Canvas, line_px  # noqa: E402,F401
from anim import Spr, SprRGB, PALETTE  # noqa: E402,F401


# ------------------------------------------------------------------ primitives
def pick(ramp, l):
    n = len(ramp)
    i = int((l + 1.0) * 0.5 * n)
    return ramp[max(0, min(n - 1, i))]


def ell(c, cx, cy, rx, ry, ramp, ang=0.0, bias=0.0, vmax=None, vmin=None, spots=(), jit=0.0, seed=0,
        over=True, shader=None):
    """Filled ellipse lit from the top-left. ang rotates it; vmax/vmin clip in local normalised v."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = int(max(rx, ry)) + 2
    rnd = random.Random(seed)
    for y in range(int(math.floor(cy - R)), int(math.ceil(cy + R)) + 1):
        for x in range(int(math.floor(cx - R)), int(math.ceil(cx + R)) + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            nu, nv = u / max(rx, 0.5), v / max(ry, 0.5)
            d = nu * nu + nv * nv
            if jit:
                d += (rnd.random() - 0.5) * jit
            if d > 1.0:
                continue
            if vmax is not None and nv > vmax: continue
            if vmin is not None and nv < vmin: continue
            wx, wy = nu * ca - nv * sa, nu * sa + nv * ca
            l = 0.8 * (-(wx + wy) / 1.414) + 0.35 * (1 - d) - 0.12 + bias
            ch = pick(ramp, l)
            for (su, sv, sr, sc) in spots:
                if (nu - su) ** 2 + (nv - sv) ** 2 <= sr * sr:
                    ch = sc
            if shader:
                r = shader(nu, nv, d, l, ch)
                if r is None: continue
                ch = r
            c.put(x, y, ch, over)


def tube(c, pts, radii, ramp, bias=0.0, over=True):
    """Tapered shaded tube along a polyline. radii: per point."""
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
                dist = math.hypot(ox, oy)
                if dist > r + 0.15:
                    continue
                if r < 0.75:
                    l = bias
                else:
                    l = -(ox + oy) / (r * 1.414) * 0.9 + 0.15 + bias
                c.put(x, y, pick(ramp, l), over)


def line(c, x0, y0, x1, y1, ch, over=True):
    for (x, y) in line_px(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
        c.put(x, y, ch, over)


def chain(x, y, segs):
    """segs: [(len, ang_deg)] -> list of points."""
    pts = [(x, y)]
    for ln, a in segs:
        x += ln * math.cos(math.radians(a)); y += ln * math.sin(math.radians(a))
        pts.append((x, y))
    return pts


def curl(x, y, n, ln, a0, da, dda=0.0):
    """Curling tendril: n segments, start angle a0, turning da per segment (+dda accel)."""
    segs = []
    a = a0
    for i in range(n):
        segs.append((ln, a)); a += da + dda * i
    return chain(x, y, segs)


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
                c.put(x, y, ch, over)


def ik(sx, sy, tx, ty, l1, l2, bend=1):
    """Two-bone IK: shoulder (sx,sy) to target; returns elbow and clamped hand point."""
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = max(1e-3, min(d, l1 + l2 - 1e-3))
    a = math.atan2(dy, dx)
    cosb = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1, min(1, cosb)))
    ea = a - bend * b
    ex, ey = sx + l1 * math.cos(ea), sy + l1 * math.sin(ea)
    hx, hy = sx + d * math.cos(a), sy + d * math.sin(a)
    return (ex, ey), (hx, hy)


def P(x, y):
    return int(round(x)), int(round(y))


def thorns(c, pts, every=3, ch="W", side=-1, phase=0):
    """Small spikes along a polyline, on the outer (side) normal."""
    k = phase
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        ln = max(1, int(math.hypot(x1 - x0, y1 - y0)))
        nx, ny = -(y1 - y0) / ln, (x1 - x0) / ln
        for s in range(ln):
            k += 1
            if k % every == 0:
                t = s / ln
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                sd = side if (k // every) % 2 == 0 else -side
                c.put(*P(x + nx * sd * 1.6, y + ny * sd * 1.6), ch)


def grounded(spr):
    """Shift a sprite so its lowest pixel sits on y=0."""
    b = spr.bbox()
    return Spr({(x, y - b[3]): v for (x, y), v in spr.px.items()})


def floor_cut(spr):
    """Drop anything below the floor (buried tips, roots in the ground)."""
    return Spr({k: v for k, v in spr.px.items() if k[1] <= 0})


def mirror(spr):
    return Spr({(-x, y): v for (x, y), v in spr.px.items()})


def recol(spr, mapping):
    return Spr({k: mapping.get(v, v) for k, v in spr.px.items()})


def dissolve(spr, keep, seed=1):
    r = random.Random(seed)
    return Spr({k: v for k, v in spr.px.items() if r.random() < keep})


def merge(*sprs):
    out = {}
    for s in sprs: out.update(s.px)
    return Spr(out)


# ------------------------------------------------------------------ sheet helper


def outline(spr, ch="K"):
    out = dict(spr.px)
    for (x, y) in spr.px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx, y + dy)
            if k not in spr.px: out[k] = ch
    return Spr(out)
