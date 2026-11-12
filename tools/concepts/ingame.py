"""Mock-ups of rooms as the game itself would draw them, built from the game's own sprites and spawn rules.

Reads the asset dump (build/dump/all/db + tex, made from the player's own copy of the game) and does what the game
does when it fills a room:
  - the room prefab's floor image and back wall strip, placed from the prefab hierarchy;
  - props from the environment's prop groups (decal, small, large, feature), picked by the groups' weights, as many as
    the room's m_maxDecalProps / m_maxSmallProps / m_maxLargeProps / m_maxFeatureProps allow, each placed inside its
    prefab's SpawnConstraints (distance from each wall, which corners it may spawn from, corner or centre weighting),
    no two overlapping;
  - drawn the way the game layers them: floor, decals, shadows, then everything standing sorted back to front, then
    the light sprites (the game's lightsource_flicker glows, a faint warm wash).

New biomes are mocked up the way they could really be built: the game's sprites recoloured at runtime (the mod may
recolour game art at runtime; it never ships it), plus a few new sprites of ours.

Concept tool only. Nothing it makes ships, and it needs the dump, which is not in the repo.
"""
import colorsys
import json
import os
import random
import struct

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump", "all"))
DB, TEX = os.path.join(DUMP, "db"), os.path.join(DUMP, "tex")
if not os.path.isdir(TEX):
    TEX = os.path.join(os.path.dirname(DUMP), "tex")

H = {int(k): v for k, v in json.load(open(os.path.join(DB, "_hier.json"))).items()}
BYNAME = {}
for k, v in H.items():
    BYNAME.setdefault(v["n"], []).append(k)


def jl(name):
    return [json.loads(l) for l in open(os.path.join(DB, "sharedassets0__%s.jsonl" % name))]


ATLAS = {a["_pid"]: a for a in jl("exAtlas")}
ATLAS_BY_NAME = {a["m_Name"]: a for a in ATLAS.values()}
SPRITE = {s["m_GameObject"]["m_PathID"]: s for s in jl("exSprite")}
ROOMS = {r["_go"]: r for r in jl("Room")}
CONSTRAINT = {c["m_GameObject"]["m_PathID"]: c for c in jl("SpawnConstraints")}
# The game's 3D colliders (read from the asset file into _colliders.json). A prop's movement collider is a capsule
# lying along x at its base (layer 22, 24 for shelves), never the whole sprite: you can walk behind a tall prop.
_cp = os.path.join(DB, "_colliders.json")
COLLIDERS = {int(k): v for k, v in json.load(open(_cp)).items()} if os.path.exists(_cp) else {}
SOLID_LAYERS = (22, 24, 16, 19, 13, 4, 0)
_texfiles = {}
for f in os.listdir(TEX):
    stem = f[:-4]
    if f.endswith(".png") and stem.rsplit("_", 1)[-1].isdigit():
        _texfiles[int(stem.rsplit("_", 1)[1])] = f
_tex = {}


def texture(pid, atlas_name=None):
    """The atlas texture. Files are named <Atlas>_<texture path id>; ids repeat across asset files, so the atlas's
    own name decides when it can."""
    key = (pid, atlas_name)
    if key not in _tex:
        f = None
        if atlas_name:
            want = "%s_%d.png" % (atlas_name, pid)
            if os.path.exists(os.path.join(TEX, want)):
                f = want
            else:
                c = [x for x in os.listdir(TEX) if x.startswith(atlas_name + "_")]
                f = c[0] if len(c) == 1 else None
        f = f or _texfiles[pid]
        _tex[key] = Image.open(os.path.join(TEX, f)).convert("RGBA")
    return _tex[key]


def element(atlas, idx):
    """An atlas element: (trimmed image, element dict)."""
    el = atlas["elements"][idx]
    t = texture(atlas["texture"]["m_PathID"], atlas.get("m_Name"))
    W, Hh = t.size
    c = el["coords"]
    x, y = round(c["x"] * W), round((1 - c["y"] - c["height"]) * Hh)
    w, h = round(c["width"] * W), round(c["height"] * Hh)
    im = t.crop((x, y, x + w, y + h))
    if el.get("rotated"):
        im = im.transpose(Image.ROTATE_90)
    return im, el


def element_named(atlas_name, name):
    a = ATLAS_BY_NAME[atlas_name]
    for i, e in enumerate(a["elements"]):
        if e["name"] == name:
            return element(a, i)
    raise KeyError(name)


def full_element(atlas_name, name):
    im, el = element_named(atlas_name, name)
    full = Image.new("RGBA", (el["originalWidth"], el["originalHeight"]))
    full.paste(im, (int(el["trimRect"]["x"]), int(el["trimRect"]["y"])))
    return full


# ex2D anchors: 0 TL 1 TC 2 TR 3 ML 4 MC 5 MR 6 BL 7 BC 8 BR. fraction of the width left of the pivot, and of the
# height below it (y up)
ANCHOR_X = {0: 0, 1: .5, 2: 1, 3: 0, 4: .5, 5: 1, 6: 0, 7: .5, 8: 1}
ANCHOR_Y = {0: 1, 1: 1, 2: 1, 3: .5, 4: .5, 5: .5, 6: 0, 7: 0, 8: 0}

SKIP = ("Select_Reticule", "FX_reticule", "TextContainer", "SelectionIndicator", "Damaged", "Broken", "Destroyed", "Debris_", "Gibs")


class Draw:
    """One sprite placed in the world (y up). kind: floor | decal | shadow | object | light. depth: the y it sorts by."""

    def __init__(self, im, left, bottom, kind, depth, name):
        self.im, self.left, self.bottom, self.kind, self.depth, self.name = im, left, bottom, kind, depth, name


def sprite_image(s):
    a = ATLAS.get(s["atlas_"]["m_PathID"])
    if a is None or s["index_"] >= len(a["elements"]):
        return None, None
    im, el = element(a, s["index_"])
    if s.get("useTextureOffset_", 1):
        full = Image.new("RGBA", (int(el["originalWidth"]), int(el["originalHeight"])))
        full.paste(im, (int(el["trimRect"]["x"]), int(el["trimRect"]["y"])))
        im = full
    if s.get("customSize_"):
        im = im.resize((max(1, int(abs(s["width_"]))), max(1, int(abs(s["height_"])))), Image.NEAREST)
    col = s["color_"]
    if (col["r"], col["g"], col["b"], col["a"]) != (1, 1, 1, 1):
        r, g, b, al = im.split()
        r = r.point(lambda v: int(v * col["r"]))
        g = g.point(lambda v: int(v * col["g"]))
        b = b.point(lambda v: int(v * col["b"]))
        al = al.point(lambda v: int(v * col["a"]))
        im = Image.merge("RGBA", (r, g, b, al))
    return im, a["elements"][s["index_"]]["name"]


def collect(gid, x=0.0, y=0.0, sx=1.0, sy=1.0, root=True, kind=None, depth=None, out=None, path=""):
    """Every sprite under a prefab, positioned in world space with the prefab's root at (x, y)."""
    out = [] if out is None else out
    n = H.get(gid)
    if not n:
        return out
    if any(k in n["n"] for k in SKIP):
        return out
    px, py = (0.0, 0.0) if root else n["p"]
    wx, wy = x + px * sx, y + py * sy
    nsx, nsy = sx * n["s"][0], sy * n["s"][1]
    if depth is None:
        depth = wy
    s = SPRITE.get(gid)
    if s and s.get("m_Enabled", 1):
        im, ename = sprite_image(s)
        if im is not None:
            if s["scale_"]["x"] * nsx < 0:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            if s["scale_"]["y"] * nsy < 0:
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            w, h = im.size
            cx = wx + s["offset_"]["x"] * abs(nsx)
            bb = im.getbbox()
            cy = wy + s["offset_"]["y"] * abs(nsy)
            left = cx - ANCHOR_X[s["anchor_"]] * w
            bottom = cy - ANCHOR_Y[s["anchor_"]] * h
            nm = n["n"]
            k = kind
            if "Shadow" in nm or "shadow" in (ename or "") and "Lightsource" not in nm:
                k = "shadow"
            elif "Lightsource" in nm or "lightsource" in (ename or "") or "Glow" in (ename or "") or "lampGlow" in (ename or ""):
                k = "light"
            elif k is None:
                k = "object"
            if bb and k != "light":
                left, bottom = left + bb[0], bottom + (h - bb[3])
                im = im.crop(bb)
            out.append(Draw(im, left, bottom, k, depth, path + "/" + nm + ":" + str(ename)))
    for c in n["c"]:
        collect(c, wx, wy, nsx, nsy, False, kind, depth if kind != "room" else None, out, path + "/" + n["n"])
    return out


def footprints(gid, x=0.0, y=0.0, sx=1.0, sy=1.0, root=True, out=None):
    """The prefab's solid (non-trigger) colliders as rectangles in world space, (x0, y0, x1, y1). A capsule along x
    is its full length by twice its radius; along z (seen from above) a circle."""
    out = [] if out is None else out
    n = H.get(gid)
    if not n:
        return out
    px, py = (0.0, 0.0) if root else n["p"]
    wx, wy = x + px * sx, y + py * sy
    nsx, nsy = sx * n["s"][0], sy * n["s"][1]
    for e in COLLIDERS.get(gid, ()):
        if e["trig"] or not e.get("en", 1) or e["layer"] not in SOLID_LAYERS:
            continue
        cx, cy = wx + e["c"][0] * nsx, wy + e["c"][1] * nsy
        if e["t"] == "CapsuleCollider":
            r, h = e["r"], max(e["h"], 2 * e["r"])
            hx, hy = {0: (h / 2, r), 1: (r, h / 2)}.get(e["dir"], (r, r))
        elif e["t"] == "BoxCollider":
            hx, hy = e["size"][0] / 2, e["size"][1] / 2
        else:
            hx = hy = e["r"]
        hx, hy = hx * abs(nsx), hy * abs(nsy)
        out.append((cx - hx, cy - hy, cx + hx, cy + hy))
    for c in n["c"]:
        footprints(c, wx, wy, nsx, nsy, False, out)
    return out


def prefab_size(gid):
    """Bounding box of a prefab's standing sprites relative to its root: (x0, y0, x1, y1)."""
    ds = [d for d in collect(gid) if d.kind in ("object", "decal")]
    if not ds:
        return (-4, 0, 4, 4)
    return (min(d.left for d in ds), min(d.bottom for d in ds),
            max(d.left + d.im.size[0] for d in ds), max(d.bottom + d.im.size[1] for d in ds))


# ------------------------------------------------------------------ prop groups (from the environment assets)
GROUPS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingame_groups.json")))
SEASONAL = ("Pumpkin", "ChristmasPresent", "ChristmasTree", "Group_Painting")


def pick(rnd, group, allow=None, deny=()):
    items = [(n, p, w) for (n, p, w) in GROUPS[group] if w > 0 and not any(s in n for s in SEASONAL)
             and (allow is None or any(a in n for a in allow)) and not any(d in n for d in deny)]
    tot = sum(w for _, _, w in items)
    r = rnd.uniform(0, tot)
    for n, p, w in items:
        r -= w
        if r <= 0:
            return n, p
    return items[-1][:2]


def rng(r):
    return r["m_min"], (r["m_max"] if r.get("m_hasMax", 1) else r["m_min"])


class Room:
    """A room being filled. Floor rect from the prefab's floor sprite (x0..x1, y0..y1, y up).

    Collision works the game's way: every standing thing has a solid footprint at its base (the prefab's own collider,
    or one we give our own sprites), footprints never overlap, and everything is drawn sorted by its feet, so the hero
    can walk behind the tall part of a prop and be hidden by it."""

    def __init__(self, room_name, seed=1):
        self.name = room_name
        self.r = ROOMS[room_name]
        self.gid = self.r["m_GameObject"]["m_PathID"]
        self.rnd = random.Random(seed)
        self.draws = collect(self.gid, kind="room")
        for d in self.draws:
            if d.kind == "room":
                d.kind = "floor" if "floor" in d.name.lower() or d.name.count("/") <= 1 else "wall"
                if "BackWallArt" in d.name or "wall" in d.name.split(":")[-1].lower():
                    d.kind = "wall"
        floor = [d for d in self.draws if d.kind == "floor"]
        f = max(floor, key=lambda d: d.im.size[0] * d.im.size[1])
        self.floor = f
        self._fpx = f.im.load()
        self.fx0, self.fy0 = f.left, f.bottom
        self.fx1, self.fy1 = f.left + f.im.size[0], f.bottom + f.im.size[1]
        self.counts = {}
        self.solids = []     # (rect, label, depth): footprints of everything standing
        self.drects = []     # decals' rects, so decals do not pile up
        self.covers = []     # (sprite rect, depth) of standing things, to keep props from hiding wholly behind others
        cb = self.r["m_cameraBounds"]
        self.cam = (cb["x"], cb["y"], cb["x"] + cb["width"], cb["y"] + cb["height"])
        self.recolours = []  # (predicate on draw, fn)
        self.floor_fx = []   # fn(x, y, rgb) -> rgb or None, on the floor once floor and decals are down
        self.blocked = []    # fn(x, y) -> True where nothing may stand (deep water, slag)
        self.lamps = []      # (x, y, rgb, radius, intensity) for the darkness layer
        self.dark = None     # ambient (r, g, b) multipliers: None = the game's flat light
        self.wall_fx = []    # fn(x, y, rgb) -> rgb or None, over the back wall art (moss, cracks, damp)
        self.floor_glow = [] # fn(x, y) -> (r, g, b, a) or None: floor that glows (lava, the Seam's cracks)
        self.auto_lamps = ((255, 176, 104), 34, 0.85)   # the game's own flames light the dark

    # -------------------------------------------------------------- collision
    @property
    def rects(self):
        return [r for r, _, _ in self.solids]

    def free(self, rect, rects, gap=0.0):
        x0, y0, x1, y1 = rect
        for (a, b, c, d) in rects:
            if x0 < c + gap and a < x1 + gap and y0 < d + gap and b < y1 + gap:
                return False
        return True

    def walkable(self, x, y):
        return self.on_floor(x, y) and not any(b(x, y) for b in self.blocked)

    def fits(self, foot, sprite_rect=None, depth=None, gap=1.0):
        """A footprint fits if it is on open floor, clear of every other footprint, and neither hides wholly behind a
        standing sprite in front of it nor wholly hides one behind it."""
        x0, y0, x1, y1 = foot
        for (px, py) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1), ((x0 + x1) / 2, (y0 + y1) / 2)):
            if not self.walkable(px, py):
                return False
        if not self.free(foot, self.rects, gap):
            return False
        if sprite_rect is not None:
            cx, cy = (x0 + x1) / 2, y0
            for (r, dep) in self.covers:
                if dep < depth and r[0] + 2 < cx < r[2] - 2 and r[1] < cy + 4 < r[3] - 3:
                    return False          # would stand hidden behind something in front
            for (r, lab, dep) in self.solids:
                fx, fy = (r[0] + r[2]) / 2, r[1]
                if dep > depth and sprite_rect[0] + 2 < fx < sprite_rect[2] - 2 and sprite_rect[1] < fy + 4 < sprite_rect[3] - 3:
                    return False          # would hide something behind it
        return True

    def _claim(self, foots, label, depth, draws):
        for f in foots:
            self.solids.append((f, label, depth))
        ds = [d for d in draws if d.kind == "object"]
        if ds:
            self.covers.append(((min(d.left for d in ds), min(d.bottom for d in ds),
                                 max(d.left + d.im.width for d in ds), max(d.bottom + d.im.height for d in ds)), depth))

    def _foot_of(self, gid, x, y):
        fs = footprints(gid, x, y)
        if fs:
            return fs
        ds = [d for d in collect(gid, x, y) if d.kind == "object"]
        if not ds:
            return []
        x0 = min(d.left for d in ds); x1 = max(d.left + d.im.width for d in ds)
        w = (x1 - x0) * 0.35
        return [((x0 + x1) / 2 - w, y - 2, (x0 + x1) / 2 + w, y + 2)]

    def place(self, gid, kind="object", tries=60):
        con = CONSTRAINT.get(gid)
        nm = H[gid]["n"]
        if con and con.get("m_maxDuplicates", 0) and self.counts.get(nm, 0) >= con["m_maxDuplicates"]:
            return None
        flat = kind == "decal" or "Carpet" in nm or "Tracks" in nm
        bx0, by0, bx1, by1 = prefab_size(gid)
        for _ in range(tries):
            if con:
                corners = [(l, t) for (l, t, k) in ((1, 1, "m_spawnFromTopLeft"), (0, 1, "m_spawnFromTopRight"),
                                                      (1, 0, "m_spawnFromBottomLeft"), (0, 0, "m_spawnFromBottomRight")) if con.get(k)]
                if not corners:
                    corners = [(1, 1), (0, 1), (1, 0), (0, 0)]
                left, top = self.rnd.choice(corners)
                dx0, dx1 = rng(con["m_distLeft"] if left else con["m_distRight"])
                dy0, dy1 = rng(con["m_distTop"] if top else con["m_distBottom"])
                W, Hh = self.fx1 - self.fx0, self.fy1 - self.fy0
                dx1, dy1 = min(dx1, W - 4), min(dy1, Hh - 4)
                if dx1 < dx0 or dy1 < dy0:
                    continue
                bias = 1 + con.get("m_cornerWeight", 0) / 5.0
                ddx = dx0 + (dx1 - dx0) * self.rnd.random() ** bias
                ddy = dy0 + (dy1 - dy0) * self.rnd.random() ** bias
                x = self.fx0 + ddx if left else self.fx1 - ddx
                y = self.fy1 - ddy if top else self.fy0 + ddy
                if con.get("m_centerWeight", 0):
                    k = min(0.85, con["m_centerWeight"] / 25.0)
                    x += (0.5 * (self.fx0 + self.fx1) - x) * k * self.rnd.random()
                    if dy1 - dy0 > 20:
                        y += (0.5 * (self.fy0 + self.fy1) - y) * k * self.rnd.random()
                snap = con.get("m_snap", 1) or 1
                x, y = round(x / snap) * snap, round(y / snap) * snap
            else:
                x = self.rnd.uniform(self.fx0 + 8, self.fx1 - 8)
                y = self.rnd.uniform(self.fy0 + 6, self.fy1 - 6)
            if flat:
                rect = (x + bx0, y + by0, x + bx1, y + by1)
                if kind != "decal" and not (self.on_floor(rect[0] + 1, rect[1] + 1) and self.on_floor(rect[2] - 1, rect[3] - 1)
                                            and self.on_floor(rect[0] + 1, rect[3] - 1) and self.on_floor(rect[2] - 1, rect[1] + 1)):
                    continue
                if not self.walkable(x, y) or not self.free(rect, self.drects, -2):
                    continue
                self.drects.append(rect)
                self.counts[nm] = self.counts.get(nm, 0) + 1
                return self.add_prefab(gid, x, y, kind)
            foots = self._foot_of(gid, x, y)
            ds = collect(gid, x, y)
            obj = [d for d in ds if d.kind == "object"]
            srect = (min(d.left for d in obj), min(d.bottom for d in obj), max(d.left + d.im.width for d in obj),
                     max(d.bottom + d.im.height for d in obj)) if obj else None
            if not all(self.fits(f, srect, y) for f in foots):
                continue
            self.counts[nm] = self.counts.get(nm, 0) + 1
            ds = self.add_prefab(gid, x, y, kind)
            self._claim(foots, nm, y, ds)
            return ds
        return None

    def add_prefab(self, gid, x, y, kind="object"):
        ds = collect(gid, x, y, kind=("decal" if kind == "decal" else None))
        nm = H[gid]["n"]
        flat = kind == "decal" and "Candles" not in nm or "Carpet" in nm or "Tracks" in nm or nm.startswith("Floor")
        for d in ds:
            if d.kind in ("object", "decal"):
                d.kind = "decal" if flat else "object"
        self.draws.extend(ds)
        return ds

    def add_named(self, name, x, y, kind="object"):
        return self.add_prefab(BYNAME[name][0], x, y, kind)

    def add_image(self, im, x, y, kind="object", anchor="bottom", name="mod", emit=None, depth=None):
        """One of our own sprites, its feet (bottom centre) at (x, y). emit: same-size image of the parts that glow
        (drawn over the darkness)."""
        w, h = im.size
        left = round(x - w / 2)
        bottom = y if anchor == "bottom" else y - h / 2
        d = Draw(im, left, bottom, kind, y if depth is None else depth, name)
        d.emit = emit
        self.draws.append(d)
        return d

    def stand(self, im, x, y, foot, name="mod", emit=None, shadow=None, force=False):
        """A standing sprite of ours with a solid footprint (half-width, half-height) at its feet. Returns the draw, or
        None if it does not fit (unless force)."""
        fw, fh = foot
        rect = (x - fw, y - fh, x + fw, y + fh)
        srect = (x - im.width / 2, y, x + im.width / 2, y + im.height)
        if force == "wet":          # stands in water: only kept clear of other footprints
            if not self.free(rect, self.rects, 1) or not self.on_floor(x, y):
                return None
        elif not force and not self.fits(rect, srect, y):
            return None
        if shadow is not None:
            self.add_image(shadow, x, y - shadow.height / 2 + 1, kind="shadow")
        d = self.add_image(im, x, y, name=name, emit=emit)
        self.solids.append((rect, name, y))
        self.covers.append((srect, y))
        return d

    def actor(self, im, x, y, name, foot=None, force=True):
        """The hero or a monster, on open floor; its footprint is kept clear of props."""
        fw = foot[0] if foot else max(3, im.width * 0.28)
        fh = foot[1] if foot else 2.5
        rect = (x - fw, y - fh, x + fw, y + fh)
        if not force and not self.fits(rect):
            return None
        d = self.add_image(im, x, y, name=name)
        self.solids.append((rect, name, y))
        self.covers.append(((x - im.width / 2, y, x + im.width / 2, y + im.height), y))
        return d

    def fill(self, env, scale=1.0, skip_small=(), skip_large=(), only=None):
        """Fill with the environment's own prop groups, as many as the room allows."""
        r = self.r
        n = lambda key: int(round(self.rnd.uniform(*rng(r[key])) * scale))
        plan = [("Decals", "decal", n("m_maxDecalProps")), ("Feature", "object", max(1, int(self.rnd.uniform(*rng(r["m_maxFeatureProps"]))))),
                ("Large", "object", n("m_maxLargeProps")), ("Small", "object", n("m_maxSmallProps"))]
        for part, kind, count in plan:
            g = "GroupProps%s%s" % (part, env)
            if g not in GROUPS:
                continue
            for _ in range(count):
                name, gid = pick(self.rnd, g, deny=(skip_small if part == "Small" else skip_large if part == "Large" else ()))
                if only and not any(o in name for o in only):
                    continue
                self.place(gid, kind)

    # -------------------------------------------------------------- drawing
    def render(self, scale=3, pad=6, light=1.0, ambient=None, grade=None, collision=False, glow=1.0):
        """Draw the room. floor_fx run on the floor once floor and decals are down (water, lava: the mod's own floor
        layer). With self.dark set, a darkness layer multiplies everything by ambient plus the lamps' light (the mod
        would draw it as one full-screen multiply sprite); glowing parts (Draw.emit) go on after it."""
        import numpy as np
        x0, y0, x1, y1 = self.cam
        x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        W, Hh = int(x1 - x0), int(y1 - y0)
        cv = Image.new("RGBA", (W, Hh), (0, 0, 0, 255))
        em = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
        cover = Image.new("L", (W, Hh), 0)      # where standing things hide the floor
        fmask = Image.new("L", (W, Hh), 0)      # the floor itself: decals are clipped to it
        fa = self.floor.im.split()[3].point(lambda v: 255 if v > 0 else 0)
        fmask.paste(fa, (int(round(self.floor.left - x0)), int(round(y1 - (self.floor.bottom + self.floor.im.height)))))
        lamps = list(self.lamps)
        order = {"floor": 0, "decal": 1, "shadow": 2, "wall": 3, "object": 3, "light": 5}
        def key(d):
            o = order.get(d.kind, 3)
            dep = -d.depth if o == 3 else 0
            if d.kind == "wall":
                dep = -1e9
            return (o, dep)
        fx_done = False
        lights = []
        for d in sorted(self.draws, key=key):
            if not fx_done and order.get(d.kind, 3) >= 2:
                self._floor_fx(cv, x0, y1)
                fx_done = True
            im = d.im
            for pred, fn in self.recolours:
                if pred(d):
                    im = fn(im, d) if getattr(fn, "wants_draw", False) else fn(im)
            if d.kind == "wall" and self.wall_fx and "BackWall" in d.name:
                im = im.copy()
                wp = im.load()
                for yy in range(im.height):
                    for xx in range(im.width):
                        c = wp[xx, yy]
                        if c[3] == 0:
                            continue
                        wx_, wy_ = d.left + xx + 0.5, d.bottom + im.height - yy - 0.5
                        for fn in self.wall_fx:
                            r_ = fn(wx_, wy_, c[:3])
                            if r_ is not None:
                                c = tuple(int(max(0, min(255, v))) for v in r_) + (c[3],)
                        wp[xx, yy] = c
            px, py = int(round(d.left - x0)), int(round(y1 - (d.bottom + im.size[1])))
            if d.kind == "light":
                lights.append((im, px, py, getattr(d, "strength", 1.0)))
                if self.auto_lamps and "Lightsource" in d.name:
                    c_, r_, i_ = self.auto_lamps
                    lamps.append((d.left + im.width / 2, d.bottom + im.height / 2, c_, r_, i_))
                continue
            if d.kind == "decal":
                im = im.copy()
                a = ImageChops.multiply(im.split()[3], fmask.crop((px, py, px + im.width, py + im.height)))
                im.putalpha(a)
                e_ = getattr(d, "emit", None)
                if e_ is not None:
                    e_ = e_.copy()
                    e_.putalpha(ImageChops.multiply(e_.split()[3], fmask.crop((px, py, px + im.width, py + im.height))))
                    d = Draw(im, d.left, d.bottom, d.kind, d.depth, d.name)
                    d.emit = e_
            cv.alpha_composite(im, (px, py))
            if d.kind in ("object", "wall"):
                cover.paste(255, (px, py), im.split()[3])
            e = getattr(d, "emit", None)
            if e is not None:
                em.alpha_composite(e, (px, py))
            elif em.getbbox() is not None and d.kind == "object":
                # a solid sprite in front hides the glow behind it
                hole = Image.new("RGBA", im.size, (0, 0, 0, 0))
                a = im.split()[3]
                em.paste(hole, (px, py), a)
        if not fx_done:
            self._floor_fx(cv, x0, y1)
        out = cv.convert("RGB")
        if ambient:
            r, g, b = out.split()
            out = Image.merge("RGB", [ch.point(lambda v, k=k: int(v * k)) for ch, k in zip((r, g, b), ambient)])
        if self.dark:
            yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
            wx, wy = xx + x0 + 0.5, y1 - yy - 0.5
            L = np.ones((Hh, W, 3), np.float32) * np.array(self.dark, np.float32)
            for (lx, ly, col, rad, inten) in lamps:
                d2 = ((wx - lx) / rad) ** 2 + ((wy - ly) / (rad * 0.72)) ** 2
                f = np.clip(1 - np.sqrt(d2), 0, 1) ** 1.6 * inten
                L += f[..., None] * (np.array(col, np.float32) / 255.0)[None, None, :]
            a = np.asarray(out).astype(np.float32) * np.clip(L, 0, 1.6)
            out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        out = out.convert("RGBA")
        if self.floor_glow:
            fg = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
            fp = fg.load()
            cp = cover.load()
            for wy in range(int(self.fy0), int(self.fy1) + 1):
                for wx in range(int(self.fx0), int(self.fx1) + 1):
                    cx_, cy_ = int(wx - x0), int(y1 - wy - 1)
                    if not (0 <= cx_ < W and 0 <= cy_ < Hh) or cp[cx_, cy_] > 128 or not self.on_floor(wx + 0.5, wy + 0.5):
                        continue
                    for fn in self.floor_glow:
                        g_ = fn(wx + 0.5, wy + 0.5)
                        if g_:
                            fp[cx_, cy_] = tuple(int(v) for v in g_)
                            break
            fg.alpha_composite(em)
            em = fg
        out.alpha_composite(em)
        if glow and em.getbbox():
            from PIL import ImageFilter
            bl = em.filter(ImageFilter.GaussianBlur(2.2))
            r, g, b, a = bl.split()
            a = a.point(lambda v: int(v * 0.55 * glow))
            add = Image.merge("RGB", (ImageChops.multiply(r, a), ImageChops.multiply(g, a), ImageChops.multiply(b, a)))
            out = ImageChops.add(out.convert("RGB"), add).convert("RGBA")
        out = out.convert("RGB")
        for im, px, py, k in lights:
            layer = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
            layer.paste(im, (px, py))
            r, g, b, a = layer.split()
            a = a.point(lambda v, k=k: int(min(255, v * light * k)))
            add = Image.merge("RGB", (ImageChops.multiply(r, a), ImageChops.multiply(g, a), ImageChops.multiply(b, a)))
            out = ImageChops.add(out, add)
        if grade:
            out = grade(out)
        if collision:
            out = self._collision_overlay(out, x0, y1)
        return out.resize((W * scale, Hh * scale), Image.NEAREST)

    def _collision_overlay(self, out, x0, y1):
        """Footprints over a dimmed picture: red for props, cyan for the hero and monsters, blue where the floor
        itself blocks (water, slag)."""
        from PIL import ImageDraw
        base = out.convert("RGBA")
        dim = Image.new("RGBA", base.size, (0, 0, 0, 120))
        base.alpha_composite(dim)
        ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(ov)
        if self.blocked:
            px = ov.load()
            for yy in range(base.height):
                for xx in range(base.width):
                    wx, wy = xx + x0 + 0.5, y1 - yy - 0.5
                    if self.on_floor(wx, wy) and any(b(wx, wy) for b in self.blocked) and (xx + yy) % 3 == 0:
                        px[xx, yy] = (80, 150, 255, 200)
        for (r, lab, dep) in self.solids:
            a, b, c, d = r[0] - x0, y1 - r[3], r[2] - x0, y1 - r[1]
            actor = lab in ("hero", "monster")
            col = (90, 230, 255) if actor else (255, 80, 70)
            a, b = int(round(a)), int(round(b))
            c, d = max(int(round(c)) - 1, a + 2), max(int(round(d)) - 1, b + 2)
            rad = int(min(c - a, d - b) // 2)
            if rad >= 2:
                dr.rounded_rectangle((a, b, c, d), radius=rad, fill=col + (90,), outline=col + (255,))
            else:
                dr.rectangle((a, b, c, d), fill=col + (90,), outline=col + (255,))
        base.alpha_composite(ov)
        return base.convert("RGB")

    def _floor_fx(self, cv, x0, y1):
        if not self.floor_fx:
            return
        px = cv.load()
        for wy in range(int(self.fy0), int(self.fy1)):
            for wx in range(int(self.fx0), int(self.fx1)):
                cx, cy = int(wx - x0), int(y1 - wy - 1)
                if not (0 <= cx < cv.width and 0 <= cy < cv.height):
                    continue
                c = px[cx, cy]
                if c[:3] == (0, 0, 0):
                    continue
                for fn in self.floor_fx:
                    r = fn(wx + 0.5, wy + 0.5, c[:3])
                    if r is not None:
                        c = tuple(int(max(0, min(255, v))) for v in r) + (255,)
                px[cx, cy] = c

    def on_floor(self, x, y):
        """True where the room's floor image is solid floor (rooms are not all rectangles)."""
        f = self.floor
        u, v = int(x - f.left), int(f.bottom + f.im.height - y)
        if not (0 <= u < f.im.width and 0 <= v < f.im.height):
            return False
        c = self._fpx[u, v]
        return c[3] > 0 and sum(c[:3]) > 60

    def wall_span(self, x):
        """(bottom, top) of the back wall art at x, or None."""
        ys = []
        for d in self.draws:
            if d.kind == "wall" and "BackWall" in d.name and d.left <= x < d.left + d.im.width:
                col = [yy for yy in range(d.im.height) if d.im.getpixel((int(x - d.left), yy))[3] > 0]
                if col:
                    ys.append((d.bottom + d.im.height - max(col) - 1, d.bottom + d.im.height - min(col)))
        if not ys:
            return None
        return (min(a for a, b in ys), max(b for a, b in ys))

    def block(self, fn):
        """Keep props and actors off where fn(x, y) is true (water, lava, pits)."""
        self.blocked.append(fn)

    def light(self, x, y, colour, strength=1.0, size=1.0, radius=None, intensity=None):
        """One of the game's own light sprites (lightsource_flicker), tinted; with radius, also a lamp in the
        darkness layer."""
        im = full_element("AtlasEffectsFullScreen", "lightsource_flicker_01")
        if size != 1.0:
            im = im.resize((max(1, int(im.width * size)), max(1, int(im.height * size))), Image.BILINEAR)
        r, g, b, a = im.split()
        im = Image.merge("RGBA", (r.point(lambda v: colour[0]), g.point(lambda v: colour[1]), b.point(lambda v: colour[2]), a))
        d = Draw(im, x - im.width / 2, y - im.height / 2, "light", y, "light")
        d.strength = strength
        self.draws.append(d)
        if radius:
            self.lamps.append((x, y, colour, radius, 1.0 if intensity is None else intensity))
        return d

    def shaft(self, x, y, w, length, colour, strength=0.5, slant=0.45):
        """A shaft of light falling from a window at (x, y) (its top centre) down across the floor, as an additive
        sprite (the mod would draw it as one)."""
        L = int(length)
        im = Image.new("RGBA", (int(w + L * abs(slant) + 4), L), (0, 0, 0, 0))
        px = im.load()
        for yy in range(L):
            t = yy / L
            off = yy * slant if slant > 0 else (L - yy) * -slant
            ww = w * (1 + 0.5 * t)
            for xx in range(int(ww)):
                edge = min(xx, ww - xx - 1) / max(1, ww / 2)
                a = int(255 * min(1, edge * 2.2) * (1 - t) ** 1.3 * (0.75 + 0.25 * ((xx // 2) % 2)))
                X = int(off + xx - (ww - w) / 2 + 2)
                if 0 <= X < im.width and a > 0:
                    px[X, yy] = tuple(colour) + (a,)
        d = Draw(im, x - w / 2 - 2 - (L * slant if slant < 0 else 0) * 0, y - L, "light", y, "shaft")
        d.strength = strength
        self.draws.append(d)
        return d

    def lamp(self, x, y, colour, radius, intensity=1.0):
        """A light in the darkness layer only."""
        self.lamps.append((x, y, colour, radius, intensity))

    def scatter(self, names, count, kind="object"):
        """Place count props picked by weight from [(prefab name, weight)], within their own spawn rules."""
        tot = sum(w for _, w in names)
        placed = tries = 0
        out = []
        while placed < count and tries < count * 4:
            tries += 1
            r = self.rnd.uniform(0, tot)
            for n, w in names:
                r -= w
                if r <= 0:
                    break
            ds = self.place(BYNAME[n][0], kind)
            if ds:
                placed += 1
                out.append(ds)
        return out

    def put(self, name, x, y, kind="object", force=False):
        """A prop placed by hand (a set piece). Its real footprint is claimed; unless force, it must fit."""
        gid = BYNAME[name][0]
        foots = self._foot_of(gid, x, y)
        if kind == "decal" or "Carpet" in name:
            ds = self.add_prefab(gid, x, y, kind)
            return ds
        if not force and not all(self.fits(f) for f in foots):
            return None
        ds = self.add_prefab(gid, x, y, kind)
        self._claim(foots, name, y, ds)
        return ds


# ------------------------------------------------------------------ recolouring (what the mod could do at runtime)
def remap(fn):
    """Apply fn(r, g, b) -> (r, g, b) to every opaque pixel, through a cache."""
    cache = {}
    def go(im):
        im = im.copy()
        px = im.load()
        w, h = im.size
        for y in range(h):
            for x in range(w):
                p = px[x, y]
                if p[3] == 0:
                    continue
                k = p[:3]
                if k not in cache:
                    cache[k] = fn(*k)
                px[x, y] = cache[k] + (p[3],)
        return im
    return go


def hsv_shift(dh=0.0, ds=1.0, dv=1.0, sat_add=0.0, toward=None, amount=0.0):
    """Hue rotate (in turns), scale saturation and value; optionally pull toward a colour."""
    def f(r, g, b):
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        h = (h + dh) % 1
        s = max(0, min(1, s * ds + sat_add))
        v = max(0, min(1, v * dv))
        rr, gg, bb = [int(round(c * 255)) for c in colorsys.hsv_to_rgb(h, s, v)]
        if toward:
            rr, gg, bb = [int(round(c + (t - c) * amount)) for c, t in zip((rr, gg, bb), toward)]
        return (rr, gg, bb)
    return f


def gradient_map(stops):
    """Map by luminance onto a list of (lum 0..1, colour) stops: keeps the art's shading, replaces its colours."""
    stops = sorted(stops)
    def f(r, g, b):
        l = (0.3 * r + 0.59 * g + 0.11 * b) / 255
        for (a, ca), (b2, cb) in zip(stops, stops[1:]):
            if a <= l <= b2:
                t = (l - a) / max(1e-6, b2 - a)
                return tuple(int(round(ca[i] + (cb[i] - ca[i]) * t)) for i in range(3))
        return stops[0][1] if l < stops[0][0] else stops[-1][1]
    return f


CLIPS = None


def clip_frame(clip, frame=0):
    """A frame of one of the game's animation clips, at its full (untrimmed) size."""
    global CLIPS
    if CLIPS is None:
        CLIPS = {c["m_Name"]: c for c in jl("exSpriteAnimClip")}
    f = CLIPS[clip]["frameInfos"][frame]
    im, el = element(ATLAS[f["atlas"]["m_PathID"]], f["index"])
    full = Image.new("RGBA", (int(el["originalWidth"]), int(el["originalHeight"])))
    full.paste(im, (int(el["trimRect"]["x"]), int(el["trimRect"]["y"])))
    return full


def hero(clip="1HSwordIdle", frame=0, flip=False):
    """The game's own hero, one frame of one of its clips, centred on its feet."""
    im = clip_frame(clip, frame)
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def mod_sprite(sheet, frame=0, flip=False, prefer=("out_heroes",)):
    for d in list(prefer) + sorted(os.listdir(os.path.join(ROOT, "art"))):
        p = os.path.join(ROOT, "art", d, sheet + ".json")
        if os.path.exists(p):
            m = json.load(open(p))
            im = Image.open(p[:-5] + ".png").convert("RGBA")
            c, r = frame % m["cols"], frame // m["cols"]
            cell = im.crop((c * m["cellW"], r * m["cellH"], (c + 1) * m["cellW"], (r + 1) * m["cellH"]))
            bb = cell.getbbox()
            cell = cell.crop(bb) if bb else cell
            if flip:
                cell = cell.transpose(Image.FLIP_LEFT_RIGHT)
            return cell
    raise KeyError(sheet)
