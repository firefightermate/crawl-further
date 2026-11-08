"""Close-up portrait painter for the hero busts (origin portraits and the custom hero's portrait layers).

The shapes are the shared material renderer's (jinx_v2_rigs.Rig: lit ellipsoids, capsules and polygons, one top-left
light), plus pillow(): a cushion-lit fill whose light follows any outline, which is how faces, hair and hats are shaped.
Lit surfaces resolve to the game's own god-portrait look: big flat clusters in the ramp's shadow, base and light tones,
the highlight on shiny and GLOSS materials (skin), no dithering. Hand-placed pixels (faces, strands, trims) may also use
the half tones between two ramp tones, so the palette is nine colours per material (ramp9). Edges follow the monster
art: no black ring, the bottom silhouette dropped a step, the right one held at the light tone or below, a cast shadow
down-right from every part in front.

Tones in this module are on the 0..4 ramp scale everywhere (stamps, dots, fixed tones); x.5 is the half step. Inside the
resolver they are doubled (0..8).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
from jinx_v2_rigs import Rig  # noqa: E402

# light -> tone: the lit range of a matte surface spans shadow (1) to light (3); shiny ones reach the highlight (4)
T0, T1, T2, T3 = -0.45, 0.05, 0.50, 0.86
# materials that may reach the highlight tone though not shiny (skin catches the light on brow, nose and cheek)
GLOSS = set()
# materials whose deepest shade drops to the half tone below shadow (hair, dark cloth)
DEEP = set()


def mix(a, b, t=0.5):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def ramp9(r):
    """Five ramp tones -> nine (the half steps between them)."""
    out = []
    for i in range(4):
        out.append(tuple(r[i]))
        out.append(mix(r[i], r[i + 1]))
    out.append(tuple(r[4]))
    return out


class Bust(Rig):
    """A Rig that resolves to the nine-colour ramp (ramp9): lit surfaces in its five ramp tones, fixed tones may be half
    steps (2.5 = between base and light)."""

    def resolve9(self, W, H, edge=True, cast=True, contour=True, clean=True):
        tone, mat, part, z = {}, {}, {}, {}
        fixed = set()
        for k, (zz, m, l, p, t) in self.b.items():
            x, y = k
            if not (0 <= x < W and 0 <= y < H):
                continue
            mat[k] = m; part[k] = p; z[k] = zz
            if t is not None:
                tone[k] = int(round(t * 2)); fixed.add(k)
                continue
            if m in J.EMISSIVE:
                tone[k] = 4 if l < 0.5 else 6 if l < 0.85 else 8
                continue
            # five clean tones, like the game's own portraits: big flat clusters, no dithering
            if l < T1: t = 2
            elif l < T2: t = 4
            elif l < T3 or (m not in J.SHINY and m not in GLOSS): t = 6
            else: t = 8
            if l < T0: t = 1 if m in DEEP else 2
            tone[k] = max(1, min(8, t))
        N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
        if clean:
            ch = {}
            for k, t in tone.items():
                if k in fixed or mat[k] in J.EMISSIVE: continue
                same = [tone[(k[0] + dx, k[1] + dy)] for dx, dy in N4
                        if (k[0] + dx, k[1] + dy) in tone and mat.get((k[0] + dx, k[1] + dy)) == mat[k]
                        and part.get((k[0] + dx, k[1] + dy)) == part[k]]
                if len(same) == 4 and t not in same and max(abs(s - t) for s in same) >= 2:
                    ch[k] = sorted(same)[1]
            tone.update(ch)
        out = dict(tone)
        if cast:
            for k in tone:
                if mat[k] in J.EMISSIVE or k in fixed or part[k] in self.hand: continue
                for dx, dy in ((-1, 0), (0, -1), (-1, -1)):
                    q = (k[0] + dx, k[1] + dy)
                    if q in part and part[q] != part[k] and z[q] > z[k] + 0.01 and mat[q] not in J.EMISSIVE \
                            and part[q] not in self.thin:
                        out[k] = max(1, tone[k] - 2); break
        if contour:
            for k in tone:
                if mat[k] in J.EMISSIVE or part[k] in self.hand or k in fixed: continue
                for dx, dy in N4:
                    q = (k[0] + dx, k[1] + dy)
                    if q in part and part[q] != part[k] and z[q] > z[k] + 0.01 and mat[q] == mat[k] \
                            and part[q] not in self.thin:
                        out[k] = max(1, min(out[k], tone[k] - 2)); break
        if edge:
            for k in tone:
                m = mat[k]
                if m in J.EMISSIVE or part[k] in self.thin or part[k] in self.hand or k in fixed:
                    continue
                x, y = k
                # a silhouette edge is where the neighbour is empty or a part well behind this one
                def behind(q):
                    return q not in tone or (z[q] < z[k] - 0.3 and part[q] != part[k])
                r_open, d_open = behind((x + 1, y)), behind((x, y + 1))
                if d_open and (x, y - 1) in tone and part.get((x, y - 1)) == part[k]:
                    out[k] = max(0, min(out[k], 2) - 1)
                elif r_open and (x - 1, y) in tone and part.get((x - 1, y)) == part[k]:
                    out[k] = max(1, min(out[k], 3))
        return {k: (mat[k], t) for k, t in out.items()}


def paint(tones, ramps, im, W, H):
    """Write resolved (mat, tone9) pixels into a PIL image."""
    cache = {}
    p = im.load()
    for (x, y), (m, t) in tones.items():
        if not (0 <= x < W and 0 <= y < H): continue
        if m not in cache: cache[m] = ramp9(ramps[m])
        p[x, y] = cache[m][max(0, min(8, t))] + (255,)
    return im


def _pillow_normal(x, y, rows, cols):
    x0, x1 = rows[y]
    y0, y1 = cols[x]
    hw, hh = max(0.6, (x1 - x0) / 2.0 + 0.5), max(0.6, (y1 - y0) / 2.0 + 0.5)
    u = (x - (x0 + x1) / 2.0) / hw
    v = (y - (y0 + y1) / 2.0) / hh
    return u, v


def pillow(r, pts, mat, z, bias=0.0, vk=0.8, uk=1.0, part=None, flat=None):
    """Fill a pixel set and shade it as a soft cushion: every pixel's normal leans out by how far it sits from the
    middle of its own row and column, so the light follows the silhouette however odd it is (faces, hair masses,
    hats). pts: iterable of (x, y)."""
    pts = set((int(x), int(y)) for x, y in pts)
    if not pts: return None
    p = part or r.part(False, z)
    rows, cols = {}, {}
    for x, y in pts:
        a = rows.get(y); rows[y] = (min(a[0], x), max(a[1], x)) if a else (x, x)
        b = cols.get(x); cols[x] = (min(b[0], y), max(b[1], y)) if b else (y, y)
    for x, y in pts:
        u, v = _pillow_normal(x, y, rows, cols)
        u, v = u * uk, v * vk
        nz = math.sqrt(max(0.08, 1.0 - min(0.92, u * u + v * v)))
        n = math.sqrt(u * u + v * v + nz * nz)
        r.put(x, y, z, mat, J.lam(u / n, v / n, nz / n) + bias, p, flat)
    return p


def rows_mask(spec, dy=0):
    """{y: (x0, x1)} spans -> pixel list."""
    out = []
    for y, (a, b) in spec.items():
        for x in range(int(a), int(b) + 1):
            out.append((x, y + dy))
    return out


def ell_mask(cx, cy, rx, ry, clip=None):
    out = []
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0 and (clip is None or clip(x, y)):
                out.append((x, y))
    return out
