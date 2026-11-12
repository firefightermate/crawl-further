"""Floor and wall detail layers for the concept rooms: the dirt, cracks, damp and shade a finished room has.

All of them are floor_fx (fn(x, y, rgb) -> rgb or None) that the Room runs over its floor, so they sit under the
props and shadows. The mod would bake these into its own floor decal layer.
"""
import math
import random

import numpy as np
from scipy import ndimage

from paint import Noise, mix


def _mask(R):
    f = R.floor
    a = np.array(f.im)[..., 3] > 0
    rgb = np.array(f.im)[..., :3].sum(-1) > 60
    return a & rgb, f


def edge_shade(R, width=9, top=16, k=0.42, colour=(0, 0, 0)):
    """The floor darkens toward its edges and most under the back wall, as the game's rooms do in their art."""
    m, f = _mask(R)
    d = ndimage.distance_transform_edt(m)
    H, W = m.shape
    rows = np.arange(H)[:, None].repeat(W, 1).astype(np.float32)
    def fx(x, y, c):
        u, v = int(x - f.left), int(f.bottom + f.im.height - y)
        if not (0 <= u < W and 0 <= v < H) or not m[v, u]:
            return None
        e = max(0.0, 1 - d[v, u] / width)
        t = max(0.0, 1 - (R.fy1 - y) / top)
        s = min(1.0, e * e * k + t * t * k * 1.1)
        return mix(c, colour, s) if s > 0.01 else None
    return fx


def contact_shade(R, reach=5.0, k=0.32):
    """Shade on the floor round everything standing, beyond its own shadow sprite (worked out once the room is
    full)."""
    cache = {}
    def build():
        x0, y0, x1, y1 = int(R.fx0), int(R.fy0), int(R.fx1), int(R.fy1)
        a = np.zeros((y1 - y0 + 1, x1 - x0 + 1), np.float32)
        for (r, lab, dep) in R.solids:
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            hw, hh = (r[2] - r[0]) / 2 + reach, (r[3] - r[1]) / 2 + reach * 0.6
            for yy in range(int(cy - hh), int(cy + hh) + 1):
                for xx in range(int(cx - hw), int(cx + hw) + 1):
                    if y0 <= yy <= y1 and x0 <= xx <= x1:
                        q = ((xx - cx) / hw) ** 2 + ((yy - cy) / hh) ** 2
                        if q < 1:
                            a[yy - y0, xx - x0] = max(a[yy - y0, xx - x0], (1 - q) ** 1.5)
        cache["a"], cache["o"] = a, (x0, y0)
    def fx(x, y, c):
        if "a" not in cache:
            build()
        a, (x0, y0) = cache["a"], cache["o"]
        u, v = int(x) - x0, int(y) - y0
        if 0 <= v < a.shape[0] and 0 <= u < a.shape[1] and a[v, u] > 0.02:
            return mix(c, (0, 0, 0), a[v, u] * k)
        return None
    return fx


def cracks(R, count, seed=0, length=(8, 22), dark=(0, 0, 0), lip=(255, 255, 255), k=0.55, glow=None, width=1):
    """Hairline cracks: a dark line with a light lip on its lower side, branching now and then (the game's cracked
    flagstones). With glow the core is that colour instead."""
    rnd = random.Random(seed)
    pts = {}
    def walk(x, y, a, L, depth):
        for i in range(L):
            a += rnd.uniform(-0.45, 0.45)
            x += math.cos(a); y += math.sin(a) * 0.62
            if not R.on_floor(x, y):
                return
            pts[(int(x), int(y))] = max(pts.get((int(x), int(y)), 0), 1.0 - depth * 0.35)
            if width > 1:
                pts[(int(x), int(y) + 1)] = max(pts.get((int(x), int(y) + 1), 0), 0.7 - depth * 0.3)
            if depth < 2 and rnd.random() < 0.08:
                walk(x, y, a + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.3), int(L * 0.4), depth + 1)
    for _ in range(count):
        for _t in range(20):
            x, y = rnd.uniform(R.fx0, R.fx1), rnd.uniform(R.fy0, R.fy1)
            if R.on_floor(x, y):
                break
        walk(x, y, rnd.uniform(0, math.tau), rnd.randint(*length), 0)
    def fx(x, y, c):
        p = (int(x), int(y))
        if p in pts:
            s = pts[p]
            return mix(c, glow, 0.85 * s) if glow else mix(c, dark, k * s)
        if (p[0], p[1] + 1) in pts and not glow:
            return mix(c, lip, 0.12 * pts[(p[0], p[1] + 1)])
        return None
    return fx


def stains(n, scale=14, k=0.22, colour=(0, 0, 0), thresh=0.55, tint=None):
    """Damp and grime: soft patches of darker (or tinted) floor."""
    def fx(x, y, c):
        v = n.fbm(x, y, scale)
        if v > thresh:
            t = min(1.0, (v - thresh) / (1 - thresh) * 2.2)
            c2 = mix(c, colour, k * t)
            return mix(c2, tint, 0.18 * t) if tint else c2
        return None
    return fx


def grit(R, density=0.02, seed=0, light=(255, 255, 255), dark=(0, 0, 0)):
    """Pebbles and grit: a lit pixel over a shaded one, scattered."""
    rnd = random.Random(seed)
    pts = {}
    area = (R.fx1 - R.fx0) * (R.fy1 - R.fy0)
    for _ in range(int(area * density)):
        x, y = int(rnd.uniform(R.fx0, R.fx1)), int(rnd.uniform(R.fy0, R.fy1))
        pts[(x, y)] = 1
        pts[(x, y - 1)] = 2
        if rnd.random() < 0.25:
            pts[(x + 1, y)] = 1
            pts[(x + 1, y - 1)] = 2
    def fx(x, y, c):
        v = pts.get((int(x), int(y)))
        if v == 1:
            return mix(c, light, 0.22)
        if v == 2:
            return mix(c, dark, 0.35)
        return None
    return fx


def creep(n, colour, scale=10, thresh=0.6, edge_only=None, k=0.6, speck=None):
    """Something growing over the floor (moss, mould, frost): noise patches, thickest where edge_only(x, y) says."""
    def fx(x, y, c):
        v = n.fbm(x, y, scale)
        if edge_only:
            v += edge_only(x, y)
        if v > thresh:
            t = min(1.0, (v - thresh) * 4)
            out = mix(c, colour, k * t)
            if speck and n.v(x * 3.1, y * 3.1, 1.0) > 0.86:
                out = mix(out, speck, 0.6)
            return out
        return None
    return fx


def near_top(R, span=24):
    """0..0.3 bonus near the back wall and floor edges, for creep()."""
    m, f = _mask(R)
    d = ndimage.distance_transform_edt(m)
    H, W = m.shape
    def g(x, y):
        u, v = int(x - f.left), int(f.bottom + f.im.height - y)
        if not (0 <= u < W and 0 <= v < H):
            return 0
        return max(0, 1 - d[v, u] / span) * 0.3
    return g
