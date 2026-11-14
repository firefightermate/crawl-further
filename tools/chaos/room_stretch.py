"""Preview of Crawl Chaos's big rooms: the game's own rooms widened and deepened the way the mod does it at runtime
(src/CrawlFurther/Chaos/ChaosRooms.cs), drawn from the asset dump so the result can be looked at before playing.

How a room grows (both here and in game):
  - one seam across the floor in x and one in y, each placed where no door, prop or set piece crosses it;
  - everything past a seam moves out by the growth (doors, walls, set pieces, the room's outline and camera frame);
    walls that cross a seam get longer;
  - the gap is filled with strips of the room's own floor (and back wall, in x) taken from elsewhere in the same room.
    Each strip is the one whose edge best continues the column (or row) before it, so the stone and mottling run on;
  - small set dressing inside a copied strip (wall bricks, column bases, stray boards) is copied with it.

Concept and checking tool: nothing it makes ships. Needs the dump (build/dump/all).
    python3 tools/chaos/room_stretch.py [room ...]   -> build/chaos_rooms/<room>.png (before above after)
"""
import os
import random
import re
import sys

import numpy as np
from scipy.ndimage import uniform_filter

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "concepts"))
import ingame as G  # noqa: E402

OUT = os.path.join(G.ROOT, "build", "chaos_rooms")

# limits shared with ChaosRooms.cs
MAX_W, MAX_H = 320, 160          # camera frame, game pixels
GROW_W, GROW_H = 1.6, 1.35       # at most this much wider / deeper
DOOR_CLEAR = 10                  # a seam stays this far from a door's centre
EDGE = 14                        # strips are taken at least this far inside the floor
BLOCK = (22, 40)                 # strip widths
MIN_BLOCK = 6
WINDOW = 56                      # strips come from no further than this from the seam
ALIKE = 14                       # a copied column may differ from the seam's by this much (see likeness)
MIN_ALIKE = 28                   # fewer like columns than this near the seam: that side is not stretched
NEAR = 6                         # score per pixel a strip's source lies from the seam
SRC_X, SRC_Y = (0.25, 0.75), (0.3, 0.7)   # strips come from the middle of the floor, clear of borders and insets
STRIP_NAME = re.compile(r"^(BackWallArt\d*|ColumnArt|ColumnArtShadow|ColumnShadows?)$")
COPY_NAME = re.compile(r"^(BackWallBricks|ColumnCollision|Column|Columns|ColumnShadows?|FloorStrayBoards|Candle|PropWallFlag|Bookshelf|RockDebrisFloor)\d*$")
SKIP_NAME = re.compile(r"^(Walls|WallsTop|RoomBounds|SpawnConstraint ?)$")


def eligible(name, r):
    return not (r["m_corridor"] or r["m_bossRoom"] or r["m_isPortalRoom"] or r["m_isPowerupRoom"] or r["m_nonSquareBounds"]
                or name.startswith("Tute") or re.search(r"HeroBattle|Powerup|Store|Portal|Boss", name))


def growth(r):
    cb = r["m_cameraBounds"]
    w, h = cb["width"], cb["height"]
    dx = int(max(0, min(MAX_W - w, w * (GROW_W - 1))) // 2 * 2)
    dy = int(max(0, min(MAX_H - h, h * (GROW_H - 1))) // 2 * 2)
    return dx, dy


def spans(name, gid):
    """x and y extents (room-local) of a direct child: its sprites and colliders."""
    ds = G.collect(gid, 0, 0, 1, 1, True)
    xs, ys = [], []
    for d in ds:
        xs += [d.left, d.left + d.im.size[0]]
        ys += [d.bottom, d.bottom + d.im.size[1]]
    for f in G.footprints(gid):
        xs += [f[0], f[2]]
        ys += [f[1], f[3]]
    n = G.H[gid]
    px, py = n["p"]
    if not xs:
        return (px, px), (py, py)
    return (px + min(xs), px + max(xs)), (py + min(ys), py + max(ys))


class Plan:
    def __init__(self, name):
        self.name = name
        self.r = G.ROOMS[name]
        self.gid = G.BYNAME[name][0]
        self.children = [(c, G.H[c]["n"]) for c in G.H[self.gid]["c"]]
        floor = [d for d in G.collect(self.gid, kind="room") if d.name.count("/") == 1]
        self.floor = floor[0]
        fx0, fy0 = self.floor.left, self.floor.bottom
        self.fx = (fx0, fx0 + self.floor.im.size[0])
        self.fy = (fy0, fy0 + self.floor.im.size[1])
        self.dx, self.dy = growth(self.r)
        self.ext = {c: spans(n, c) for c, n in self.children if not SKIP_NAME.match(n)}

    def blockers(self, axis, source=False):
        """Ranges a seam on this axis may not cross (source: ranges a copied strip may not take in; set dressing
        that is copied along is allowed there)."""
        out = []
        for d in self.r["m_doors"]:
            p = d["m_position"]["x" if axis == 0 else "y"]
            vertical_wall = d["m_direction"] in (0, 1)
            if (axis == 0) != vertical_wall and not source:
                out.append((p - DOOR_CLEAR, p + DOOR_CLEAR))
        for c, n in self.children:
            if c not in self.ext:
                continue
            (x0, x1), (y0, y1) = self.ext[c]
            lo, hi = (x0, x1) if axis == 0 else (y0, y1)
            if STRIP_NAME.match(n) and axis == 0 or source and COPY_NAME.match(n):
                continue
            out.append((lo + 1, hi - 1))
        return out

    def seam(self, axis, rnd, solid=lambda v: True, score=None):
        lo, hi = (self.fx if axis == 0 else self.fy)
        lo, hi = lo + EDGE + 8, hi - EDGE - 8
        if axis == 1:
            hi = min(hi, (self.fy[0] + self.fy[1]) / 2 + 12)   # keep away from the back wall's shadow
        bl = self.blockers(axis)
        ok = [v for v in range(int(lo), int(hi)) if not any(a <= v <= b for a, b in bl) and solid(v) and solid(v - 1)]
        if not ok:
            return None
        mid = (lo + hi) / 2
        if score is not None:
            best = max(score(v) for v in ok)
            if best < MIN_ALIKE:
                return None
            ok = [v for v in ok if score(v) >= best * 0.85]
        ok.sort(key=lambda v: abs(v - mid) + rnd.random() * 6)
        return ok[0]


def likeness(im):
    """dist[a][b]: how different floor column a is from column b once the mottling is smoothed away (the largest
    difference down the column of a 9 x 5 average, summed over r, g, b). Big shapes painted in the floor (inset panels,
    symbols, water) show up; the speckle doesn't."""
    a = np.asarray(im).astype(float)[:, :, :3]
    sm = uniform_filter(a, size=(9, 5, 1))[4:-4]
    w = sm.shape[1]
    out = np.zeros((w, w))
    for x in range(w):
        out[x] = np.abs(sm - sm[:, x:x + 1, :]).sum(axis=2).max(axis=0)
    return out


def column(im, x):
    return [im.getpixel((x, y)) for y in range(im.size[1])]


def diff(a, b):
    return sum(abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) + abs(p[3] - q[3]) for p, q in zip(a, b))


def opaque_cols(im, margin=3):
    """Columns whose pixels are all solid, top and bottom few rows aside (edges carry door notches)."""
    w, h = im.size
    px = im.load()
    return [all(px[x, y][3] == 255 for y in range(margin, h - margin)) for x in range(w)]


def quilt(base, cut, amount, src_lo, src_hi, rnd, usable):
    """Blocks of source columns [s, s + w) of `base` to fill `amount` columns inserted before column `cut`.
    Each block is the one whose left edge best continues the column before it (and, for the last, whose right edge
    best meets the column at the cut), a little in favour of strips near the cut. `usable(s, w)` rules sources out.
    A block too wide to find a source is tried narrower."""
    blocks, left = [], amount
    prev = column(base, cut - 1)
    nxt = column(base, cut)
    cols = {}

    def col(x):
        if x not in cols:
            cols[x] = column(base, x)
        return cols[x]

    while left > 0:
        want = min(left, rnd.randint(*BLOCK))
        if left - want < MIN_BLOCK:
            want = left
        pick, w = None, want
        while w > 0:
            last = w == left
            cands = []
            for s in range(max(src_lo + 1, cut - WINDOW), min(src_hi - w + 1, cut + WINDOW - w)):
                if not usable(s, w):
                    continue
                score = diff(prev, col(s - 1)) + NEAR * abs(s - cut)
                if last:
                    score += diff(nxt, col(s + w))
                cands.append((score, s))
            if cands:
                cands.sort()
                pick = (cands[min(len(cands) - 1, rnd.randint(0, 1))][1], w)
                break
            if w == left and left > 2 * MIN_BLOCK:
                w = left - MIN_BLOCK
            else:
                w -= 4
            if w < MIN_BLOCK:
                break
        if pick is None:
            return None
        blocks.append(pick)
        prev = col(pick[0] + pick[1] - 1)
        left -= pick[1]
    return blocks


def insert_cols(im, cut, blocks):
    w, h = im.size
    add = sum(b[1] for b in blocks)
    out = Image.new("RGBA", (w + add, h))
    out.paste(im.crop((0, 0, cut, h)), (0, 0))
    x = cut
    for s, bw in blocks:
        out.paste(im.crop((s, 0, s + bw, h)), (x, 0))
        x += bw
    out.paste(im.crop((cut, 0, w, h)), (x, 0))
    return out


def composite(floor, strips):
    """The floor with the back wall strips above it, one image in room space, left edge at the floor's."""
    top = max([floor.bottom + floor.im.size[1]] + [s.bottom + s.im.size[1] for s in strips])
    im = Image.new("RGBA", (floor.im.size[0], int(top - floor.bottom)))
    for d in [floor] + strips:
        im.alpha_composite(d.im, (int(d.left - floor.left), int(top - d.bottom - d.im.size[1])))
    return im


def stretch(name, seed=1):
    rnd = random.Random(seed)
    P = Plan(name)
    draws = G.collect(P.gid, kind="room")
    floor = [d for d in draws if d.name.count("/") == 1][0]
    strips = [d for d in draws if d.name.count("/") == 2 and STRIP_NAME.match(d.name.split("/")[2].split(":")[0])]
    others = [d for d in draws if d is not floor and d not in strips]
    solid = opaque_cols(floor.im)
    top = floor.bottom + floor.im.size[1]
    rows_solid = opaque_cols(floor.im.transpose(Image.TRANSPOSE))
    lx = likeness(floor.im) if P.dx else None
    ly = likeness(floor.im.transpose(Image.TRANSPOSE)) if P.dy else None

    def alike(L, ok, cut):
        n = L.shape[0]
        return sum(1 for x in range(max(0, cut - WINDOW), min(n, cut + WINDOW)) if L[cut][x] <= ALIKE and ok[x])

    sx = P.seam(0, rnd, lambda v: solid[int(v - floor.left)], lambda v: alike(lx, solid, int(v - floor.left))) if P.dx else None
    sy = P.seam(1, rnd, lambda v: rows_solid[int(top - v)], lambda v: alike(ly, rows_solid, int(top - v))) if P.dy else None
    # x
    if sx is not None:
        cut = int(sx - floor.left)
        crossing = [st for st in strips if st.left < sx < st.left + st.im.size[0]]
        blocked = [(a - floor.left, b - floor.left) for a, b in P.blockers(0, True)]
        lo = max([int(len(solid) * SRC_X[0])] + [int(st.left - floor.left) + 2 for st in crossing])
        hi = min([int(len(solid) * SRC_X[1])] + [int(st.left + st.im.size[0] - floor.left) - 2 for st in crossing])

        def usable(s, w):
            return (all(solid[s - 1:s + w + 1]) and all(lx[cut][s - 1:s + w + 1] <= ALIKE)
                    and not any(s - 1 < b and s + w + 1 > a for a, b in blocked))

        xblocks = quilt(composite(floor, crossing), cut, P.dx, lo, hi, rnd, usable)
        if xblocks:
            floor.im = insert_cols(floor.im, cut, xblocks)
            for st in strips:
                if st in crossing:
                    st.im = insert_cols(st.im, int(sx - st.left), [(b + int(floor.left - st.left), w) for b, w in xblocks])
                elif st.left >= sx:
                    st.left += P.dx
            copies = []
            for d in others:
                top_name = d.name.split("/")[2].split(":")[0] if d.name.count("/") >= 2 else ""
                if d.left >= sx:
                    d.left += P.dx
                elif COPY_NAME.match(top_name):
                    x = sx
                    for s0, w in xblocks:
                        s0 += floor.left
                        if s0 <= d.left and d.left + d.im.size[0] <= s0 + w:
                            copies.append(G.Draw(d.im, d.left + (x - s0), d.bottom, d.kind, d.depth, d.name + "#copy"))
                        x += w
            others += copies
        else:
            sx = None
    # y
    if sy is not None:
        im = floor.im.transpose(Image.TRANSPOSE)           # rows become columns (top row -> left column)
        rs = opaque_cols(im)
        cut = int(floor.bottom + floor.im.size[1] - sy)
        fh = im.size[0]
        blocked = [(top - b, top - a) for a, b in P.blockers(1, True)]

        def usable_y(s, w):
            return (all(rs[s - 1:s + w + 1]) and all(ly[cut][s - 1:s + w + 1] <= ALIKE)
                    and not any(s - 1 < b and s + w + 1 > a for a, b in blocked))

        yb = quilt(im, cut, P.dy, int(fh * SRC_Y[0]), int(fh * SRC_Y[1]), rnd, usable_y)
        if yb:
            floor.im = insert_cols(im, cut, yb).transpose(Image.TRANSPOSE)
            for d in others + strips:
                if d.bottom >= sy:
                    d.bottom += P.dy
        else:
            sy = None
    return P, sx, sy, draws, floor, strips, others


def render(draws, w, h, ox, oy, marks=()):
    im = Image.new("RGBA", (w, h), (12, 10, 14, 255))
    order = sorted(draws, key=lambda d: (0 if d.kind == "room" else 1 if d.kind == "shadow" else 2, -d.depth if d.kind == "object" else 0))
    for d in order:
        x = int(d.left - ox)
        y = int(h - (d.bottom - oy) - d.im.size[1])
        im.alpha_composite(d.im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
    dr = ImageDraw.Draw(im)
    for (mx, my, c) in marks:
        x, y = mx - ox, h - (my - oy)
        dr.rectangle((x - 2, y - 2, x + 2, y + 2), outline=c)
    return im


def preview(name, seed=1):
    before = G.collect(G.BYNAME[name][0], kind="room")
    P, sx, sy, draws, floor, strips, others = stretch(name, seed)
    cb = P.r["m_cameraBounds"]
    W, H = int(cb["width"] + P.dx), int(cb["height"] + P.dy)
    ox, oy = cb["x"], cb["y"]
    doors_before = [(d["m_position"]["x"], d["m_position"]["y"], (255, 210, 0)) for d in P.r["m_doors"]]
    doors_after = [(x + (P.dx if sx is not None and x >= sx else 0), y + (P.dy if sy is not None and y >= sy else 0), c) for x, y, c in doors_before]
    a = render(before, int(cb["width"]), int(cb["height"]), ox, oy, doors_before)
    b = render([floor] + strips + others, W, H, ox, oy, doors_after)
    dr = ImageDraw.Draw(b)
    if sx is not None:
        dr.line((sx - ox, 0, sx - ox, 3), fill=(255, 0, 255))
        dr.line((sx + P.dx - ox, 0, sx + P.dx - ox, 3), fill=(255, 0, 255))
    out = Image.new("RGBA", (max(a.size[0], b.size[0]), a.size[1] + b.size[1] + 6), (40, 40, 40, 255))
    out.paste(a, (0, 0))
    out.paste(b, (0, a.size[1] + 6))
    return out.resize((out.size[0] * 3, out.size[1] * 3), Image.NEAREST), (sx, sy, P.dx, P.dy)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or [n for n, r in G.ROOMS.items() if eligible(n, r)]
    for n in names:
        im, info = preview(n)
        if info[0] is None and info[1] is None:
            print(n, "no seam: stays as it is")
            continue
        im.save(os.path.join(OUT, n + ".png"))
        print(n, info)
