"""New pixel art for the two mod bosses (deterministic; run: python3 tools/sprites/boss_art.py).

The mod bosses run on vanilla boss machinery (BossHydra -> The Leviathan, BossTentacleBlob -> Pandemonium): every part,
collider, possessable head/tentacle, phase and anim depends on each frame's geometry. So this tool keeps every vanilla
frame's footprint and anchor (same element, same original cell, same pivot, silhouette within a few px) but repaints
the content from scratch into that geometry:

  1. per vanilla element: the alpha mask, the vanilla materials (classified by colour: hide, belly, mouth, teeth, eye,
     horn, glass, brain, ...) and the form shading (vanilla luminance ranked inside each material);
  2. body-fixed coordinates so the new patterns ride the anim instead of swimming: geodesic distance from the root of
     a neck / tentacle (rings, fin rays, barnacles, photophores, stripes, juggling-ball nodules follow the tube as it
     bends), distance from the silhouette (fins, valances, outlines), angle from a tent's apex (canvas stripes);
  3. new materials and features painted into the mask, plus feature layers anchored to keypoints tracked per frame
     (eyes, maws, teeth, lures, hooks, gill frills, harlequin diamonds, noses, flags), outline last, glow last.

THE LEVIATHAN (Bel'Mora): slate-indigo eel hide with a spined dorsal fin, pale drowned-flesh belly ribbed with
barnacles and a row of cyan photophores; anglerfish maws (black-violet gullet, needle teeth); head A carries a glowing
lure, head B a rusted hook through the jaw, head C coral gill frills; the body is a capsized wreck: hull planks, a
keel, a glowing porthole, coral and kelp; ichor instead of blood; brine instead of fire and goo.
PANDEMONIUM (Jinx): the mound is a big-top tent (crimson/ivory canvas stripes from the apex, gold scalloped valance,
bunting, a pennant), tentacles are striped canvas with gold-sequined suckers and juggling-ball nodules, the eye and
mouth wear white greasepaint (harlequin diamonds, violet pinwheel iris, red-lipped grin, gold teeth, a red nose), the
brain-bubble is a fortune-teller's crystal ball, gore becomes confetti and canvas scraps.

Output: art/out_bosses/<Sheet>.png + .json (the redrawn elements packed; json maps vanilla element index -> rect in the
png + new trim inside the vanilla original cell) and contact images (vanilla vs new for every anim of every part) in
build/boards: bosses_new_<boss>_<part>.png. BossFactory composites the sheet over a copy of the vanilla atlas at load.
Needs the game dump (build/dump, or CRAWL_DUMP): atlases, clip db, prefab index.
"""
import colorsys, hashlib, json, math, os, pickle, re, sys
from collections import defaultdict

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DUMP = os.environ.get("CRAWL_DUMP", os.path.join(ROOT, "build", "dump"))
BOARDS = os.path.join(ROOT, "build", "boards")
OUT = os.path.join(ROOT, "art", "out_bosses")

# ===================================================================================================== vanilla data
_ATL = {}
_TEX = {}
# vanilla atlases this tool redraws from: name -> (exAtlas pid, extracted png)
ATLAS_PIDS = {"AtlasBossHydra": (39921, "AtlasBossHydra_127.png"), "AtlasBoss": (39919, "AtlasBoss_124.png"),
              "AtlasEffectsShared": (39923, "AtlasEffectsShared_5.png")}
_PIDKEYS = ['"m_PathID": %d' % v[0] for v in ATLAS_PIDS.values()]
_CLIPS = {}      # clip pid -> clip
_BYNAME = {}     # clip name -> first clip of that name (test helpers)


def load_vanilla():
    if _ATL: return
    for l in open(os.path.join(DUMP, "db", "exAtlas.jsonl")):
        a = json.loads(l)
        if a.get("m_Name") in ATLAS_PIDS:
            _ATL[int(a["_pid"])] = a
    for name, (pid, png) in ATLAS_PIDS.items():
        _TEX[pid] = np.array(Image.open(os.path.join(DUMP, "tex", png)).convert("RGBA"))
    for l in open(os.path.join(DUMP, "db", "exSpriteAnimClip.jsonl")):
        if not any(k in l for k in _PIDKEYS): continue
        c = json.loads(l)
        _CLIPS[c["_pid"]] = c
        _BYNAME.setdefault(c["m_Name"], c)


def elem(apid, i):
    return _ATL[apid]["elements"][i]


def elem_rect(apid, i):
    """(x, y_top, w, h) of an element in the atlas png (png origin top-left)."""
    H, W = _TEX[apid].shape[:2]
    c = elem(apid, i)["coords"]
    x0 = round(c["x"] * W); w = round(c["width"] * W); h = round(c["height"] * H)
    y1 = H - round(c["y"] * H)
    return x0, y1 - h, w, h


MARGIN = 10   # new art may grow a few px past the vanilla cell (a lure over a head at the cell's top edge):
              # trimRect then goes negative / past the cell, which ex2D's anchor maths handles like any other offset


def vframe(apid, i):
    """The vanilla element placed in its original cell padded by MARGIN (RGBA uint8 array, origin top-left)."""
    e = elem(apid, i); t = e["trimRect"]
    x, y, w, h = elem_rect(apid, i)
    M = MARGIN
    cv = np.zeros((e["originalHeight"] + 2 * M, e["originalWidth"] + 2 * M, 4), np.uint8)
    if w and h:
        # ex2D trimRect.y counts from the TOP of the original cell (see exSprite.UpdateMesh anchor maths)
        ty = int(t["y"])
        cv[M + ty:M + ty + h, M + int(t["x"]):M + int(t["x"]) + w] = _TEX[apid][y:y + h, x:x + w]
    return cv


def clip_frames(name):
    c = _CLIPS[name] if isinstance(name, int) else _BYNAME[name]
    return [(f["atlas"]["m_PathID"], f["index"]) for f in c["frameInfos"]]


def reachable_clips(root_name, maxdepth=3):
    """Clip pids reachable from a vanilla prefab (hierarchy + referenced prefabs, as BossFactory clones them)."""
    bygo, bypid, gos = pickle.load(open(os.path.join(DUMP, "q", "idx.pkl"), "rb"))
    go, tr, native = pickle.load(open(os.path.join(DUMP, "q", "hier.pkl"), "rb"))
    trbygo = {v["go"]: k for k, v in tr.items()}
    clip_pid = {}
    for l in open(os.path.join(DUMP, "db", "exSpriteAnimClip.jsonl")):
        if not any(k in l for k in _PIDKEYS): continue
        c = json.loads(l); clip_pid[c["_pid"]] = c["m_Name"]

    def refs(o):
        out = []

        def w(v):
            if isinstance(v, dict):
                if set(v.keys()) == {"m_FileID", "m_PathID"}:
                    if v["m_PathID"]: out.append(v["m_PathID"])
                else:
                    for x in v.values(): w(x)
            elif isinstance(v, list):
                for x in v: w(x)
        for k, v in o.items():
            if k in ("m_GameObject", "m_Script", "_go", "_pid", "m_PrefabParentObject", "m_PrefabInternal"): continue
            w(v)
        return out

    def root_of(g):
        t = tr.get(trbygo.get(g))
        while t and t["father"]: t = tr[t["father"]]
        return t["go"] if t else g

    def hier(g):
        out = [g]; t = tr.get(trbygo.get(g))
        if t:
            for ch in t["children"]: out += hier(tr[ch]["go"])
        return out
    roots = [p for p, g in go.items() if g["name"] == root_name and not (tr.get(trbygo.get(p)) or {}).get("father")]
    seen, names, sprites = set(), set(), set()
    front = [(r, 0) for r in roots]
    while front:
        r, d = front.pop()
        if r in seen: continue
        seen.add(r)
        for g in hier(r):
            for c in go[g]["comps"]:
                o = bypid.get(c)
                if not o or o["_cls"] in ("Room", "SpawnGroup", "SpawnGroupContainer"): continue
                if o["_cls"] == "exSprite" and o.get("atlas_", {}).get("m_PathID") in (39921, 39919, 39923):
                    sprites.add((o["atlas_"]["m_PathID"], o["index_"]))
                for p in refs(o):
                    if p in clip_pid: names.add(p)
                    elif p in go:
                        rr = root_of(p)
                        if rr != r and d < maxdepth: front.append((rr, d + 1))
    return names, sprites


# ===================================================================================================== colour utils
def hsv(rgb):
    r, g, b = [c / 255.0 for c in rgb[:3]]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360.0, s, v


def hx(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def ramp(*hexes):
    return [hx(h) for h in hexes]


def pick(rmp, t):
    """t in [0,1] -> ramp colour (dark -> light)."""
    n = len(rmp)
    return rmp[max(0, min(n - 1, int(t * n)))]


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def hsh(*k):
    """Deterministic hash -> [0,1)."""
    h = hashlib.md5(("|".join(str(x) for x in k)).encode()).digest()
    return int.from_bytes(h[:4], "little") / 2.0 ** 32


def lum(a):
    return (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0


MARKERS = {(0, 0, 254), (0, 0, 255), (0, 254, 254), (0, 255, 255), (0, 254, 0), (0, 255, 0)}
# runtime AnimNodes find these exact colours (+-0.005) in the texture: painted colours must never land on them
_PALCELLS = None


def safe(c):
    """Nudge a colour off the vanilla palette-swap cells (PalettePBossOnly) and off the AnimNodes marker colours."""
    global _PALCELLS
    if _PALCELLS is None:
        _PALCELLS = set()
        for f in ("PalettePBossOnly_117", "PaletteP1_139"):
            p = os.path.join(DUMP, "tex", f + ".png")
            if not os.path.exists(p): continue
            im = np.array(Image.open(p).convert("RGBA"))
            ys, xs = np.nonzero((im[..., 3] > 0) & ~((im[..., 0] == 255) & (im[..., 1] == 0) & (im[..., 2] == 255)))
            for y, x in zip(ys, xs): _PALCELLS.add((int(x), int(y)))
    r, g, b = c[:3]
    for _ in range(6):
        cell = (min(15, r * 16 // 256) + min(15, g * 16 // 256) * 16, min(63, b * 64 // 256))
        # ColorSwapper writes the cell and its 8 neighbours
        near = any((cell[0] + dx, cell[1] + dy) in _PALCELLS for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        if not near and (r, g, b) not in MARKERS: break
        b = max(0, b - 5); g = max(0, g - 3)
    return (r, g, b)


# ===================================================================================================== frame geometry
N4 = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)


class Frame:
    """Analysis of one vanilla frame: mask, classes, shading, distance fields, geodesic coordinate."""

    def __init__(self, rgba, classify):
        self.src = rgba
        self.H, self.W = rgba.shape[:2]
        self.alpha = rgba[..., 3]
        self.mask = self.alpha >= 128
        self.soft = (self.alpha > 0) & ~self.mask
        self.L = lum(rgba.astype(np.float32))
        self.cls = classify(rgba, self.mask)
        self.out = np.zeros_like(rgba)
        self.edge = self.mask & ~ndimage.binary_erosion(self.mask, N4)
        self.dist_in = ndimage.distance_transform_edt(self.mask)
        self.dist_out = ndimage.distance_transform_edt(~self.mask) if self.mask.any() else None
        ys, xs = np.nonzero(self.mask)
        self.bbox = (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None
        self._geo = None

    def of(self, *names):
        m = np.zeros(self.mask.shape, bool)
        for n in names: m |= self.cls == n
        return m

    def rank(self, region, levels=None):
        """Vanilla luminance normalised inside a region -> [0,1] shading term (keeps the form lighting)."""
        t = np.zeros(self.mask.shape, np.float32)
        if not region.any(): return t
        v = self.L[region]
        lo, hi = np.percentile(v, 3), np.percentile(v, 97)
        if hi - lo < 0.06:      # flat colour (a white ring, a one-tone fleck): keep its absolute brightness
            t[region] = np.clip(v, 0, 1)
            return t
        t[region] = np.clip((v - lo) / (hi - lo), 0, 1)
        return t

    def geodesic(self, seeds):
        """BFS distance (8-connected, diagonal = 1.4) through the mask from seed pixels."""
        INF = 1e9
        d = np.full(self.mask.shape, INF, np.float32)
        import heapq
        h = []
        for y, x in zip(*np.nonzero(seeds & self.mask)):
            d[y, x] = 0; h.append((0.0, int(y), int(x)))
        heapq.heapify(h)
        m = self.mask
        H, W = m.shape
        while h:
            dd, y, x = heapq.heappop(h)
            if dd > d[y, x]: continue
            for dy, dx, w in ((0, 1, 1), (1, 0, 1), (0, -1, 1), (-1, 0, 1), (1, 1, 1.4), (1, -1, 1.4), (-1, 1, 1.4), (-1, -1, 1.4)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and dd + w < d[ny, nx]:
                    d[ny, nx] = dd + w; heapq.heappush(h, (dd + w, ny, nx))
        d[d >= INF] = -1
        return d

    def normal(self, y, x):
        """Outward normal at an edge pixel (from the blurred mask gradient)."""
        if not hasattr(self, "_gy"):
            b = ndimage.gaussian_filter(self.mask.astype(np.float32), 1.2)
            self._gy, self._gx = np.gradient(b)
        gx, gy = -self._gx[y, x], -self._gy[y, x]
        n = math.hypot(gx, gy)
        return (gx / n, gy / n) if n > 1e-6 else (0.0, -1.0)

    def put(self, x, y, c, a=255, over=True):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.W and 0 <= y < self.H:
            if over or self.out[y, x, 3] == 0:
                cc = safe(c)
                self.out[y, x] = (cc[0], cc[1], cc[2], a)

    def get(self, x, y):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.W and 0 <= y < self.H: return self.out[y, x]
        return None

    def fill(self, region, col_fn):
        ys, xs = np.nonzero(region)
        for y, x in zip(ys, xs):
            c = col_fn(int(x), int(y))
            if c is not None: self.put(x, y, c, int(self.alpha[y, x]) if self.alpha[y, x] else 255)

    def keep_markers(self):
        s = self.src
        ys, xs = np.nonzero(self.mask)
        for y, x in zip(ys, xs):
            if tuple(int(v) for v in s[y, x, :3]) in MARKERS:
                self.out[y, x] = s[y, x]

    def outline(self, col, only_new=True):
        """1px dark outline on the outer edge of the painted art (pixels in out whose 4-neighbour is empty)."""
        a = self.out[..., 3] >= 128
        ed = a & ~ndimage.binary_erosion(a, N4, border_value=0)
        ys, xs = np.nonzero(ed)
        for y, x in zip(ys, xs):
            cur = self.out[y, x, :3]
            if tuple(int(v) for v in cur) in MARKERS: continue
            self.out[y, x, :3] = mix(tuple(int(v) for v in cur), col, 0.7)


def comps(mask, min_px=1):
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), bool))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(xs) >= min_px: out.append((xs, ys))
    return out


def line(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts


def bezier(p0, p1, p2, n=None):
    if n is None: n = int(max(abs(p2[0] - p0[0]), abs(p2[1] - p0[1])) * 2 + 4)
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        q = (int(round(x)), int(round(y)))
        if not pts or pts[-1] != q: pts.append(q)
    return pts


def hsv_arr(rgba):
    a = rgba[..., :3].astype(np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    rr = m & (mx == r); gg = m & (mx == g) & ~rr; bb = m & ~rr & ~gg
    h[rr] = (60 * ((g - b)[rr] / d[rr])) % 360
    h[gg] = 60 * ((b - r)[gg] / d[gg]) + 120
    h[bb] = 60 * ((r - g)[bb] / d[bb]) + 240
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def is_marker(rgba):
    m = np.zeros(rgba.shape[:2], bool)
    for c in MARKERS:
        m |= (rgba[..., 0] == c[0]) & (rgba[..., 1] == c[1]) & (rgba[..., 2] == c[2])
    return m


# ===================================================================================================== THE LEVIATHAN
def classify_hydra(rgba, mask):
    h, s, v = hsv_arr(rgba)
    cls = np.full(mask.shape, "", "<U6")
    cls[mask] = "hide"
    cls[mask & (h >= 40) & (h < 70) & (v >= 0.45)] = "hidel"
    cls[mask & (h >= 20) & (h < 46) & (s >= 0.6) & (v < 0.6)] = "horn"
    red = mask & ((h >= 315) | (h < 16)) & (s >= 0.28)
    cls[red] = "belly"
    teeth = mask & (v >= 0.78) & (s < 0.62) & (h >= 35) & (h <= 72)
    cls[teeth] = "teeth"
    cls[mask & (h >= 160) & (h <= 215) & (s >= 0.12) & (v >= 0.42)] = "eye"
    if teeth.any():
        near = ndimage.distance_transform_edt(~teeth) <= 3.5
        cls[red & near & ((v >= 0.58) | (h >= 330))] = "mouth"
    cls[mask & is_marker(rgba)] = "mark"
    return cls


LV = dict(
    HIDE=ramp("283a4e", "3c5470", "506e8a", "688aa2", "84a6b4", "a8c6ca"),
    FACE=ramp("40566a", "5e7c88", "7c9ea0", "9cbcb4", "c2d8cc"),
    BELLY=ramp("343c42", "4c5a5e", "6a7c7c", "8ea29c", "b4c6bc"),
    MAW=ramp("0a0610", "170a18", "2a0e26", "4a1434"),
    TEETH=ramp("7e8880", "c4cabe", "eef2e4"),
    CORAL=ramp("5a1a36", "963052", "d0607c", "f4a4b4"),
    BARN=ramp("1e262a", "4a5654", "7a8680", "b4bdae"),
    FIN=ramp("23506a", "4a9aa0", "a6f0dc"),
    IRON=ramp("2a2a32", "5a5a64", "8e8e98", "c4c4cc"),
    RUST=ramp("5e2412", "8e3b1e", "b8642e"),
    KELP=ramp("1c3022", "2f5030", "557038"),
    ICHOR=ramp("0c1420", "163040", "2a5a6a", "5fd0c8"),
    WOOD=ramp("2e2822", "4a4034", "665a48", "84765e", "a49478"),
    BRASS=ramp("3a2c14", "6c5426", "a88a46", "dcc27a"),
    GLOW=hx("3ee4ff"), GLOW2=hx("1f8fa0"), CORE=hx("d8ffff"),
    LINE=hx("080a12"), SHADOW=(14, 16, 24),
)


def head_letter(clip):
    m = re.search(r"Head(?:Cooldown)?_?([ABC])(?:_|$|\d)", clip) or re.search(r"Head([ABC])", clip) or re.search(r"Nub_([ABC])", clip)
    return m.group(1) if m else "A"


def keypoints(F):
    eye = F.of("eye"); mouth = F.of("mouth", "teeth")
    E = M = None
    if eye.any():
        ys, xs = np.nonzero(eye); E = (xs.mean(), ys.mean())
    if mouth.any():
        ys, xs = np.nonzero(mouth); M = (xs.mean(), ys.mean())
    return E, M


def root_seeds(mask):
    """The bottom two rows of the largest piece of the art (the neck's root), ignoring stray specks below it."""
    seeds = np.zeros_like(mask)
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), bool))
    if n == 0: return seeds
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    big = lab == (int(np.argmax(sizes)) + 1)
    ys = np.nonzero(big.any(1))[0]
    yb = ys.max()
    seeds[max(0, yb - 1):yb + 1] = big[max(0, yb - 1):yb + 1]
    return seeds


def tri(F, a, b, c, col_fn, alpha=255, outside=None):
    """Rasterise a filled triangle; col_fn(x, y) -> colour; outside: only where this mask is False."""
    xs = [a[0], b[0], c[0]]; ys = [a[1], b[1], c[1]]
    x0, x1 = int(math.floor(min(xs))), int(math.ceil(max(xs)))
    y0, y1 = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-6: return
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px, py = x + 0.0, y + 0.0
            l1 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
            l2 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den
            l3 = 1 - l1 - l2
            if min(l1, l2, l3) >= -0.08:
                if outside is not None and 0 <= y < F.H and 0 <= x < F.W and outside[y, x]: continue
                cc = col_fn(x, y)
                if cc is not None: F.put(x, y, cc, alpha)


def blob(F, cx, cy, ra, rb, ux, uy, ramp_, light=(-0.6, -0.8)):
    """Shaded ellipse (axis ra along (ux, uy), rb across), lit from the top-left."""
    R = int(max(ra, rb)) + 2
    vx, vy = -uy, ux
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            dx, dy = x - cx, y - cy
            a = (dx * ux + dy * uy) / ra; b = (dx * vx + dy * vy) / rb
            r = a * a + b * b
            if r <= 1.0:
                nx, ny = dx / max(ra, rb), dy / max(ra, rb)
                l = 0.55 - (nx * light[0] + ny * light[1]) * 0.8 - r * 0.25
                F.put(x, y, pick(ramp_, min(0.99, max(0.0, l))))


def head_frame(F):
    """Per-frame head keypoints: eye E, mouth centre M, snout tip T (mouth pixel farthest from the eye), the snout
    direction f (unit) and the 'up' direction u (from the jaw toward the eye side)."""
    E, M = keypoints(F)
    if E is None or M is None: return None
    ys, xs = np.nonzero(F.of("mouth", "teeth"))
    d2 = (xs - E[0]) ** 2 + (ys - E[1]) ** 2
    i = int(np.argmax(d2))
    T = (float(xs[i]), float(ys[i]))
    fx, fy = T[0] - E[0], T[1] - E[1]
    n = math.hypot(fx, fy)
    if n < 1.5: return None
    fx, fy = fx / n, fy / n
    ux, uy = fy, -fx
    if (E[0] - M[0]) * ux + (E[1] - M[1]) * uy < 0: ux, uy = -ux, -uy
    if abs((E[0] - M[0]) * ux + (E[1] - M[1]) * uy) < 0.3 and uy > 0: ux, uy = -ux, -uy
    # jaw: the mouth pixel farthest on the down side
    dn = (xs - E[0]) * -ux + (ys - E[1]) * -uy
    j = int(np.argmax(dn))
    J = (float(xs[j]), float(ys[j]))
    return dict(E=E, M=M, T=T, f=(fx, fy), u=(ux, uy), J=J, size=math.sqrt(n * n + 4))


def paint_lev_head(F, ctx):
    """Eel / anglerfish heads on finned necks. The vanilla head keeps only its footprint: the hydra's ears and tusks
    are cut away and each head grows its own skull, jaw and crest (A: angler dome, lure and underbite; B: hooked
    gulper jaw with a throat pouch and a hook through it; C: long moray snout and a coral gill fan); the neck tube is
    broken by a webbed spine sail and a ventral fin."""
    L = LV
    letter = head_letter(ctx["clip"])
    mask = F.mask
    s = F.geodesic(root_seeds(mask))
    E, M = keypoints(F)
    yy, xx = np.mgrid[0:F.H, 0:F.W]
    near_head = np.zeros_like(mask)
    for P in (E, M):
        if P is not None: near_head |= (xx - P[0]) ** 2 + (yy - P[1]) ** 2 <= 8.5 ** 2
    hf = head_frame(F)
    # --- cut the hydra's ears / horns / back spikes off the head (thin protrusions on the up side)
    erase = np.zeros_like(mask)
    if hf is not None:
        ux, uy = hf["u"]
        up = ((xx - hf["E"][0]) * ux + (yy - hf["E"][1]) * uy) > -0.5
        opened = ndimage.binary_opening(mask, np.ones((3, 3), bool), iterations=2)
        zone = (xx - hf["E"][0]) ** 2 + (yy - hf["E"][1]) ** 2 <= 10.5 ** 2
        erase = mask & ~opened & zone & up & ~F.of("eye", "mouth", "teeth", "mark")
        erase |= F.of("horn") & zone
    hide, hidel, belly = F.of("hide"), F.of("hidel"), F.of("belly")
    t_h = smooth_rank(F, hide | hidel, 0.8) * 0.6 + F.rank(hide | hidel) * 0.4
    t_b = F.rank(belly)
    d = F.dist_in

    def hide_col(x, y):
        t = t_h[y, x]
        if F.cls[y, x] == "hidel" and near_head[y, x]:
            return pick(L["FACE"], t)
        i = min(5, int(t * 5.0) + 1)
        sv = s[y, x]
        # eel spotting: small dark spots on a body-fixed (geodesic, depth) lattice
        if sv >= 0 and d[y, x] >= 1.5:
            u, w = sv / 3.0, d[y, x] / 2.2
            if hsh("spot", letter, int(u), int(w)) < 0.3 and (u % 1 - .5) ** 2 + (w % 1 - .5) ** 2 < 0.07: i -= 2
        return L["HIDE"][max(0, min(5, i))]
    F.fill(hide | hidel | F.of("horn"), hide_col)

    def belly_col(x, y):
        t = t_b[y, x]; sv = s[y, x]
        c = pick(L["BELLY"][1:], t)
        if sv >= 0 and int(sv) % 3 == 0 and d[y, x] >= 1.5: c = mix(c, L["BELLY"][0], 0.55)   # ventral plates
        return c
    F.fill(belly, belly_col)
    F.fill(F.of("mark"), lambda x, y: tuple(int(v) for v in F.src[y, x, :3]))
    # --- the maw: black-violet gullet with needle teeth around the lips
    maw = F.of("mouth")
    teeth = F.of("teeth")
    if maw.any():
        dt = ndimage.distance_transform_edt(~teeth) if teeth.any() else np.full(mask.shape, 9.0)
        F.fill(maw, lambda x, y: L["MAW"][min(3, max(0, 3 - int(dt[y, x])))] if dt[y, x] < 2 else L["MAW"][0 if (x + y) % 3 else 1])
        lip = maw & ndimage.binary_dilation(~maw & ~teeth & mask | ~mask, N4)
        for y, x in zip(*np.nonzero(lip)):
            if (x * 3 + y) % 2 == 0: F.put(x, y, L["TEETH"][2] if (x + y) % 4 == 0 else L["TEETH"][1])
    # the hydra's tusks become slim needles: keep the tooth pixels inside the head, drop the outer tusk tips
    tusk_tip = teeth & ~ndimage.binary_dilation(maw | (mask & ~teeth), N4, iterations=1) if teeth.any() else teeth
    F.fill(teeth & ~tusk_tip, lambda x, y: L["TEETH"][2] if (x + y) % 2 else L["TEETH"][1])
    erase |= tusk_tip
    ys, xs = np.nonzero(F.soft)
    for y, x in zip(ys, xs): F.out[y, x] = L["SHADOW"] + (int(F.alpha[y, x]),)
    ys, xs = np.nonzero(erase)
    F.out[ys, xs] = 0
    F.outline(L["LINE"])
    pre = F.out[..., 3] > 0
    body = (F.out[..., 3] >= 128)
    # --- webbed spine sail along the back of the neck
    if belly.any():
        db, (iy, ix) = ndimage.distance_transform_edt(~belly, return_indices=True)
    else:
        db = np.full(mask.shape, 99.0); iy = ix = None
    smax = float(s.max()) if (s >= 0).any() else 0.0
    spines = []
    taken = set()
    edge = body & ~ndimage.binary_erosion(body, N4)
    ys, xs = np.nonzero(edge & (hide | hidel) & ~near_head)
    for y, x in sorted(zip(ys, xs), key=lambda p: s[p[0], p[1]]):
        sv = s[y, x]
        if sv < 5 or db[y, x] < 2.0: continue
        k = int(sv // 3.5)
        if k in taken or sv % 3.5 > 1.4: continue
        nx, ny = F.normal(y, x)
        if iy is not None:
            # the back edge: its outward normal points away from the belly
            bx_, by_ = x - ix[y, x], y - iy[y, x]
            if nx * bx_ + ny * by_ < 0.35 * math.hypot(bx_, by_): continue
        # the spine must stand clear of the body (no rays into the coil of the neck)
        clear = True
        for j in (2, 3):
            qx, qy = int(round(x + nx * j)), int(round(y + ny * j))
            if not (0 <= qx < F.W and 0 <= qy < F.H) or body[qy, qx]: clear = False
        if not clear: continue
        taken.add(k)
        ln = 3 + (1 if smax and sv > smax * 0.35 else 0) + (1 if smax and sv > smax * 0.65 else 0) + (1 if k % 2 else 0)
        spines.append(((x, y), (x + nx * ln, y + ny * ln), k))
    ks = set(k for _, _, k in spines)
    spines = [sp for sp in spines if (sp[2] - 1 in ks or sp[2] + 1 in ks)]     # a sail, never a lone stick
    outside = body.copy()
    for (b0, t0, k), (b1, t1, k1) in zip(spines, spines[1:]):
        if k1 - k != 1 or math.hypot(b1[0] - b0[0], b1[1] - b0[1]) > 5.5: continue
        tri(F, b0, t0, b1, lambda x, y: L["FIN"][1], 255, outside)
    for b0, t0, k in spines:
        for i, (x, y) in enumerate(line(b0[0], b0[1], t0[0], t0[1])):
            if i == 0: continue
            F.put(x, y, L["FIN"][0] if (x, y) != (int(round(t0[0])), int(round(t0[1]))) else L["FIN"][2])
    # --- a ventral fin on the throat side, halfway up the neck
    if belly.any() and smax > 16:
        cand = np.nonzero(edge & belly & (np.abs(s - smax * 0.5) < 1.2))
        if len(cand[0]):
            i = len(cand[0]) // 2
            by, bx = int(cand[0][i]), int(cand[1][i])
            nx, ny = F.normal(by, bx)
            bx2, by2 = bx - ny * 3, by + nx * 3
            if s[min(F.H - 1, max(0, int(by2))), min(F.W - 1, max(0, int(bx2)))] > s[by, bx]: bx2, by2 = bx + ny * 3, by - nx * 3
            tip = (bx + nx * 4 - (bx2 - bx) * 0.6, by + ny * 4 - (by2 - by) * 0.6)
            tri(F, (bx, by), tip, (bx2, by2), lambda x, y: L["FIN"][1], 255, outside)
            for x, y in line(bx, by, tip[0], tip[1])[1:]: F.put(x, y, L["FIN"][0])
            F.put(tip[0], tip[1], L["FIN"][2])
    glow = []
    # --- photophores along the flank, above the belly line
    if belly.any():
        flank = (hide | hidel) & body & (db <= 1.5) & (s >= 4) & ~near_head
        ys, xs = np.nonzero(flank)
        taken = set()
        for y, x in sorted(zip(ys, xs), key=lambda p: s[p[0], p[1]]):
            k = int(s[y, x] / 5)
            if s[y, x] % 5 < 1.6 and k not in taken:
                taken.add(k); glow.append((x, y, L["GLOW"]))
    for s0 in (11, 23):
        cand = np.nonzero((np.abs(s - s0) < 1.0) & body & ~near_head & (db >= 1) & (d >= 1.5))
        if len(cand[0]):
            i = int(np.argmax(db[cand]))
            barnacle(F, int(cand[1][i]), int(cand[0][i]), 2)
    # --- new skull, jaw and crest per head
    if hf is not None:
        new_head(F, hf, letter, glow, body)
    outer_outline(F, pre, L["LINE"])
    # --- eyes last: dark socket, cold glowing pupil
    for xs, ys in comps(F.of("eye")):
        for x, y in zip(xs, ys): F.put(x, y, (10, 14, 22))
        j = int(np.argmin((xs - M[0]) ** 2 + (ys - M[1]) ** 2)) if M is not None else 0
        glow.append((int(xs[j]), int(ys[j]), L["CORE"]))
        if len(xs) > 1:
            k = (j + 1) % len(xs)
            glow.append((int(xs[k]), int(ys[k]), L["GLOW"]))
    for x, y, c in glow: F.put(x, y, c)
    F.keep_markers()


def outer_outline(F, pre, col):
    """A 1px dark rim around everything painted after the base outline (fins, jaws, crests), drawn on the empty
    side so thin features keep their own colour."""
    new = (F.out[..., 3] > 0) & ~pre
    if not new.any(): return
    ring = ndimage.binary_dilation(new, N4) & (F.out[..., 3] == 0)
    ys, xs = np.nonzero(ring)
    for y, x in zip(ys, xs):
        F.out[y, x] = safe(col) + (255,)


def new_head(F, hf, letter, glow, body):
    L = LV
    E, T, J = hf["E"], hf["T"], hf["J"]
    fx, fy = hf["f"]; ux, uy = hf["u"]
    sc = max(0.7, min(1.25, hf["size"] / 7.0))
    H = L["HIDE"]
    if letter == "A":
        # anglerfish: a bulbous dome brow over the eye, the lure rising from it, a jutting fanged underbite
        cx, cy = E[0] + ux * 2.0 * sc - fx * 1.5, E[1] + uy * 2.0 * sc - fy * 1.5
        blob(F, cx, cy, 4.2 * sc, 3.0 * sc, fx, fy, H[1:])
        top = (cx + ux * 3.0 * sc, cy + uy * 3.0 * sc)
        lure(F, (int(round(top[0])), int(round(top[1]))), 1 if fx >= -0.2 else -1, glow, ux, uy, fx, fy)
        jaw(F, J, T, hf, 3.0 * sc, fangs=3, curl=0.6)
    elif letter == "B":
        # gulper: a long hooked lower jaw, a sagging throat pouch, a row of short crest spines, the hook
        jaw(F, J, T, hf, 2.5 * sc, fangs=2, curl=1.8)
        px, py = J[0] - ux * 2.6 * sc - fx * 1.0, J[1] - uy * 2.6 * sc - fy * 1.0
        blob(F, px, py, 3.6 * sc, 2.6 * sc, fx, fy, L["BELLY"][1:])
        for k in range(3):
            bx, by = E[0] + ux * 2.5 * sc - fx * (1 + k * 2.2), E[1] + uy * 2.5 * sc - fy * (1 + k * 2.2)
            for j in range(1, 3):
                F.put(bx + ux * j, by + uy * j, L["FIN"][0] if j < 2 else L["FIN"][2])
        hook(F, int(round(J[0] + fx * 1.0)), int(round(J[1] + fy * 1.0)), 1 if fx >= -0.2 else -1)
    else:
        # moray: the snout runs on into a long narrow tapering beak with tube nostrils; a coral gill fan
        for k in range(1, int(4 * sc) + 1):
            w = max(0.6, 1.6 - k * 0.3)
            cx, cy = T[0] + fx * k + ux * 1.0, T[1] + fy * k + uy * 1.0
            for j in np.arange(-w, w + 0.01, 0.5):
                F.put(cx + ux * j, cy + uy * j, H[2] if j > 0 else H[1])
        F.put(T[0] + fx * 2 + ux * 2.4, T[1] + fy * 2 + uy * 2.4, H[3])
        jaw(F, J, T, hf, 3.0 * sc, fangs=2, curl=0.0)
        gill_fan(F, E, hf, sc)


def jaw(F, J, T, hf, ext, fangs=3, curl=0.5):
    """A lower jaw jutting past the snout tip, its tip curling up, with fangs standing up from it."""
    L = LV
    fx, fy = hf["f"]; ux, uy = hf["u"]
    p0 = (J[0], J[1])
    tip = (T[0] + fx * ext - ux * 0.5 + ux * curl, T[1] + fy * ext - uy * 0.5 + uy * curl)
    mid = ((p0[0] + tip[0]) / 2 - ux * 1.0, (p0[1] + tip[1]) / 2 - uy * 1.0)
    pts = bezier(p0, mid, tip)
    for i, (x, y) in enumerate(pts):
        F.put(x, y, L["HIDE"][2])
        F.put(x - ux, y - uy, L["HIDE"][1])        # jaw underside
    n = len(pts)
    for k in range(fangs):
        x, y = pts[min(n - 1, int(n * (0.45 + 0.5 * k / max(1, fangs - 1 if fangs > 1 else 1))))]
        for j in range(1, 3):
            F.put(x + ux * j, y + uy * j, L["TEETH"][2] if j == 2 else L["TEETH"][1])


def gill_fan(F, E, hf, sc):
    C = LV["CORAL"]
    fx, fy = hf["f"]; ux, uy = hf["u"]
    bx, by = E[0] - fx * 3.5, E[1] - fy * 3.5 + 0.5
    rays = []
    for ang in (-70, -35, 0, 35, 70):
        a = math.radians(ang)
        # rays fan out backwards (-f), spread across u
        dx = -fx * math.cos(a) + ux * math.sin(a)
        dy = -fy * math.cos(a) + uy * math.sin(a)
        ln = (5.5 - abs(ang) / 35.0) * sc
        rays.append(((bx, by), (bx + dx * ln, by + dy * ln)))
    for (b0, t0), (b1, t1) in zip(rays, rays[1:]):
        tri(F, b0, t0, t1, lambda x, y: C[1], 255)
    for b0, t0 in rays:
        for x, y in line(b0[0], b0[1], t0[0], t0[1]): F.put(x, y, C[2])
        F.put(t0[0], t0[1], C[3])


def barnacle(F, x, y, sz):
    """A barnacle cone: lit rim top-left, shadowed bottom-right, a dark mouth on top."""
    B = LV["BARN"]
    if sz == 1:
        F.put(x, y, B[3]); F.put(x + 1, y, B[1]); return
    for dx, dy, c in ((-1, 0, B[3]), (0, -1, B[3]), (1, -1, B[2]), (-1, 1, B[2]), (1, 0, B[1]), (0, 1, B[1]), (1, 1, B[0]),
                      (-1, -1, B[2])):
        F.put(x + dx, y + dy, c)
    F.put(x, y, B[0])


def lure(F, P, sx, glow, ux=0.0, uy=-1.0, fx=1.0, fy=0.0):
    """A thin stalk rising from the brow and arching forward over the snout to a glowing bulb."""
    L = LV
    x0, y0 = P
    top = (x0 + ux * 6 - fx * 1, y0 + uy * 6 - fy * 1)
    end = (x0 + ux * 4 + fx * 6, y0 + uy * 4 + fy * 6)
    pts = bezier((x0, y0), top, end)
    for i, (x, y) in enumerate(pts):
        F.put(x, y, L["HIDE"][1] if i % 3 else L["HIDE"][3])
    ex, ey = pts[-1]
    bx, by = ex - ux * 1.2, ey - uy * 1.2
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)): glow.append((int(round(bx)) + dx, int(round(by)) + dy, L["GLOW"]))
    glow.append((int(round(bx)), int(round(by)), L["CORE"]))
    for dx, dy in ((-1, 0), (-1, 1), (0, 2), (1, 2), (2, 0), (2, 1), (0, -1), (1, -1)):
        g = F.get(int(round(bx)) + dx, int(round(by)) + dy)
        if g is not None and g[3] == 0:
            F.put(int(round(bx)) + dx, int(round(by)) + dy, L["GLOW2"], 160)


def frill(F, E, M, sx):
    L = LV["CORAL"]
    fx = -sx if M is None else -np.sign(M[0] - E[0]) or -sx
    bx, by = E[0] + fx * 3, E[1] + 1
    for k, (ang, ln) in enumerate(((-120, 4), (-150, 5), (170, 4), (140, 3))):
        a = math.radians(ang if fx < 0 else 180 - ang)
        for j in range(1, ln + 1):
            F.put(bx + math.cos(a) * j, by + math.sin(a) * j, L[3] if j == ln else (L[2] if j > 1 else L[1]))


def hook(F, x, y, sx):
    I, R = LV["IRON"], LV["RUST"]
    pts = [(0, 1), (0, 2), (0, 3), (0, 4), (-sx, 5), (-2 * sx, 5), (-3 * sx, 4), (-3 * sx, 3)]
    for i, (dx, dy) in enumerate(pts):
        F.put(x + dx, y + dy, I[3] if i < 2 else (R[2] if i in (4, 6) else I[2]))
        F.put(x + dx + sx, y + dy, I[0], over=False)
    F.put(x - 2 * sx, y + 3, I[3])   # barb
    F.put(x - 3 * sx, y + 2, I[1])


def paint_lev_body(F, ctx):
    """The body becomes a capsized wreck: hull planks, keel, porthole, coral, kelp and barnacles; eel-hide legs."""
    L = LV
    mask = F.mask
    if F.bbox is None: return
    x0, y0, x1, y1 = F.bbox
    H, W = mask.shape
    top = np.full(W, -1); bot = np.full(W, -1)
    for x in range(x0, x1 + 1):
        ys = np.nonzero(mask[:, x])[0]
        if len(ys): top[x] = ys.min(); bot[x] = ys.max()
    yy, xx = np.mgrid[0:H, 0:W]
    dtop = np.where(top[xx] >= 0, yy - top[xx], -1)
    colh = np.where(top[xx] >= 0, bot[xx] - top[xx] + 1, 1)
    hull_h = max(8, int((y1 - y0) * 0.62))
    shell = mask & (dtop >= 0) & (dtop < np.minimum(colh * 0.68, hull_h)) & (colh >= 9) & ~F.of("horn", "mark")
    shell = ndimage.binary_opening(shell, np.ones((2, 2), bool)) & shell
    # heads tucked into the body (intro / death frames): paint them as eel heads, not as hull
    feat = F.of("eye", "teeth", "mouth")
    heads = np.zeros_like(mask)
    if feat.sum() >= 3:
        heads = mask & (ndimage.distance_transform_edt(~feat) <= 5.5) & ~F.of("mark")
        shell &= ~heads
    # red: small spots are wounds (anemones), big masses are spurting blood (ichor)
    gore = np.zeros_like(mask)
    for xs_, ys_ in comps(F.of("belly"), 1):
        if len(xs_) > 24: gore[ys_, xs_] = True
    shell &= ~gore
    legs = mask & ~shell & ~heads & ~gore
    tl = smooth_rank(F, legs, 1.2) * 0.7 + F.rank(legs) * 0.3
    tws = smooth_rank(F, shell, 2.5)
    d = F.dist_in
    cols = np.nonzero(shell.any(0))[0]
    c0, c1 = (cols.min(), cols.max()) if len(cols) else (x0, x1)
    wdt = max(1, c1 - c0)
    hd = np.zeros(W, int)
    for x in cols: hd[x] = int(shell[:, x].sum())

    def wood(x, y):
        dt = int(dtop[y, x])
        v = dt / max(1.0, hd[x])
        l = 0.92 - 0.6 * v - 0.12 * (x - c0) / wdt + 0.3 * (tws[y, x] - 0.5)
        i = int(round(1 + max(0.0, min(1.0, l)) * 3))           # WOOD[1..4]
        if dt == 0: return L["WOOD"][0]                           # keel rim
        if dt == 1: return L["WOOD"][min(4, i + 1)]              # wet glint along the keel
        r = (dt - 2) % 3
        row = (dt - 2) // 3
        xr = x - c0
        if r == 2: return L["WOOD"][max(0, i - 1)] if i > 1 else L["WOOD"][0]      # plank seam
        if (xr + row * 9) % 22 == 0: return L["WOOD"][max(0, i - 1)]             # butt joint
        if (xr + row * 9) % 22 == 1 and r == 1: return L["BRASS"][1]             # a rusted nail by the joint
        return L["WOOD"][i]
    F.fill(shell, wood)

    def hide(x, y):
        c = F.cls[y, x]
        if c == "horn": return pick(L["BARN"][1:], F.L[y, x] * 1.9)
        if c == "belly": return pick(L["ICHOR"], min(0.99, F.L[y, x] * 1.5))
        return L["HIDE"][max(0, min(5, int(tl[y, x] * 4.5) + 1))]
    F.fill(legs & ~F.of("mark"), hide)
    tg = F.rank(gore)
    F.fill(gore, lambda x, y: L["ICHOR"][3] if (x * 7 + y * 5) % 13 == 0 and tg[y, x] > 0.6 else pick(L["ICHOR"][:3], tg[y, x] * 0.9))
    if heads.any():
        th = F.rank(heads)

        def headcol(x, y):
            c = F.cls[y, x]
            if c == "teeth": return L["TEETH"][2]
            if c == "mouth": return L["MAW"][1]
            if c == "eye": return L["GLOW"]
            if c == "hidel": return pick(L["FACE"], th[y, x])
            if c == "belly": return pick(L["BELLY"][1:], th[y, x])
            if c == "horn": return pick(L["CORAL"], th[y, x])
            return pick(L["HIDE"][1:], th[y, x])
        F.fill(heads, headcol)
    ys, xs = np.nonzero(F.soft)
    for y, x in zip(ys, xs): F.out[y, x] = L["SHADOW"] + (int(F.alpha[y, x]),)
    glow = []
    for xs_, ys_ in comps(F.of("belly") & ~gore & ~heads, 2):
        for x, y in zip(xs_, ys_): F.put(x, y, L["CORAL"][2] if (x + y) % 2 else L["CORAL"][1])
        glow.append((int(np.round(xs_.mean())), int(np.round(ys_.mean())), L["CORAL"][3]))
    upright = len(cols) >= 24 and hd[cols].mean() >= 6
    if upright:
        def at(fr, depth):
            cx = int(round(c0 + wdt * fr))
            if top[cx] < 0 or hd[cx] < 3: return None
            return cx, int(top[cx] + depth * hd[cx])
        # a stove-in strake: the planks are gone and the ribs show against the dark inside
        p = at(0.33, 0.5)
        if p:
            hx_, hy_ = p
            for yy_ in range(hy_ - 2, hy_ + 3):
                for xx_ in range(hx_ - 4, hx_ + 5):
                    if ((xx_ - hx_) / 4.6) ** 2 + ((yy_ - hy_) / 2.6) ** 2 <= 1 and 0 <= yy_ < H and shell[yy_, xx_]:
                        rib = (xx_ - hx_) % 3 == 0
                        F.put(xx_, yy_, L["WOOD"][3 if yy_ < hy_ else 2] if rib else (L["MAW"][0] if yy_ > hy_ - 2 else L["MAW"][1]))
        # porthole: brass ring, drowned light behind the glass
        p = at(0.6, 0.38)
        if p:
            px_, py_ = p
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    r2 = dx * dx + dy * dy
                    if r2 <= 5: F.put(px_ + dx, py_ + dy, (L["BRASS"][3] if dx + dy < 0 else L["BRASS"][1]) if r2 >= 3 else L["FIN"][0])
            glow += [(px_, py_, L["GLOW"]), (px_ - 1, py_ - 1, L["CORE"])]
        # barnacle clusters, clean 3x3 cones lit from the top-left
        for fr, dp, n in ((0.16, 0.62, 2), (0.5, 0.7, 3), (0.78, 0.45, 2)):
            p = at(fr, dp)
            if p:
                for k in range(n):
                    barnacle(F, p[0] + k * 3 - (k % 2), p[1] + (k % 2), 2)
    F.outline(L["LINE"])
    pre = F.out[..., 3] > 0
    if upright:
        # ribs of the broken stern standing up out of the hull
        for k, fr in enumerate((0.1, 0.17, 0.24)):
            cx = int(round(c0 + wdt * fr))
            if top[cx] < 0: continue
            hgt = (4, 6, 5)[k]
            for j in range(1, hgt + 1):
                xx_ = cx - (j * j) // 9
                F.put(xx_, top[cx] - j + 1, L["WOOD"][3] if j < hgt else L["WOOD"][4])
                F.put(xx_ + 1, top[cx] - j + 1, L["WOOD"][1])
        # the broken mainmast with a cracked yard and a rag of sail
        cx = int(round(c0 + wdt * 0.47))
        if top[cx] >= 0:
            mt = top[cx]
            for j in range(0, 11):
                F.put(cx, mt - j, L["WOOD"][3]); F.put(cx + 1, mt - j, L["WOOD"][1])
            F.put(cx, mt - 11, L["WOOD"][4])
            yx, yy0 = cx - 4, mt - 7
            pts = line(yx, yy0 + 1, cx + 5, yy0 - 1)
            for x_, y_ in pts: F.put(x_, y_, L["WOOD"][2])
            sail = ramp("3e4a3c", "5a6a52", "7c8c6c")
            for k, (x_, y_) in enumerate(pts[1:-1]):
                ln = 3 + (k * 5) % 3 - (1 if k in (2, 5) else 0)
                for j in range(1, ln + 1):
                    F.put(x_, y_ + j, sail[2] if j == 1 else (sail[1] if (k + j) % 3 else sail[0]))
        # a coral fan on the bow
        cx = int(round(c0 + wdt * 0.82))
        if top[cx] >= 0: coral(F, cx, top[cx], 1)
        # the tail ends in a fish's forked caudal fin
        upper = mask & (yy <= y0 + (y1 - y0) * 0.6)
        ys_, xs_ = np.nonzero(upper)
        if len(xs_):
            j = int(np.argmin(xs_ * 4 + ys_))
            tx_, ty_ = int(xs_[j]), int(ys_[j])
            rays = [(-5, -5), (-6, -2), (-4, 1), (-6, 4)]
            for (ax_, ay_), (bx_, by_) in zip(rays, rays[1:]):
                if (ax_, ay_) == (-6, -2): continue          # the fork between the two lobes
                tri(F, (tx_, ty_), (tx_ + ax_, ty_ + ay_), (tx_ + bx_, ty_ + by_), lambda x, y: L["FIN"][1], 255, pre)
            for ax_, ay_ in rays:
                for x_, y_ in line(tx_, ty_, tx_ + ax_, ty_ + ay_)[1:]: F.put(x_, y_, L["FIN"][0])
                F.put(tx_ + ax_, ty_ + ay_, L["FIN"][2])
        # kelp hanging off the hull over the legs
        for k, fr in enumerate((0.36, 0.64)):
            cx = int(round(c0 + wdt * fr))
            if top[cx] < 0 or hd[cx] < 3: continue
            ys2 = np.nonzero(shell[:, cx])[0]
            kelp(F, cx, int(ys2.max()) + 1, 5, k)
    outer_outline(F, pre, L["LINE"])
    for x, y, c in glow: F.put(x, y, c)
    F.keep_markers()


def coral(F, x, y, k):
    C = LV["CORAL"]
    # a short branching fan of coral (3 fronds) standing on the keel
    for dx, ln in ((-2, 3), (0, 5), (2, 4)):
        for j in range(ln):
            F.put(x + dx + (j * dx) // 4, y - j, C[1] if j < ln - 1 else C[3])
    F.put(x - 1, y, C[0]); F.put(x + 1, y, C[0])


def kelp(F, x, y, ln, k):
    K = LV["KELP"]
    for j in range(ln + 2):
        wob = int(round(math.sin(j * 0.9 + k) * 1.0))
        F.put(x + wob, y + j - 1, K[2] if j % 3 == 0 else K[1])
    F.put(x + 1, y - 2, K[1]); F.put(x + 2, y - 1, K[2])


def paint_lev_ichor(F, ctx):
    """Gore and severed-head FX: blood becomes black-teal brine ichor; any hide/teeth/eyes in them match the heads."""
    L = LV
    t = F.rank(F.mask | F.soft)

    def col(x, y):
        c = F.cls[y, x]
        if c in ("belly", "mouth"):
            if (x * 7 + y * 5) % 13 == 0 and t[y, x] > 0.55: return L["ICHOR"][3]      # rare cold glints
            return pick(L["ICHOR"][:3], t[y, x] * 0.9)
        if c == "teeth": return L["TEETH"][2]
        if c == "eye": return L["GLOW"]
        if c == "horn": return pick(L["CORAL"], t[y, x])
        return pick(L["HIDE"], t[y, x])
    F.fill(F.mask, col)
    ys, xs = np.nonzero(F.soft)
    for y, x in zip(ys, xs):
        F.out[y, x] = pick(L["ICHOR"], 0.3) + (int(F.alpha[y, x]),)
    F.keep_markers()


LV["WATER"] = ramp("0e2a36", "17505e", "2a8088", "62bcb4", "b8eee0")
LV["FOAM"] = hx("eefffa")


def paint_lev_water(F, ctx):
    """Fire, goo and spit FX become brine: deep sea-green body, bright foam lip on the lit (upper-left) edge, glints."""
    L = LV
    region = F.mask | F.soft
    t = F.rank(region)
    W = L["WATER"]
    lit = np.zeros_like(F.mask)
    if F.mask.any():
        sh = np.roll(np.roll(F.mask, 1, 0), 1, 1)
        lit = F.mask & ~sh
    for y, x in zip(*np.nonzero(region)):
        c = pick(W[1:], t[y, x])
        if lit[y, x]: c = mix(c, L["FOAM"], 0.6)
        elif (x * 5 + y * 3) % 13 == 0 and t[y, x] > 0.5: c = L["FOAM"]
        F.out[y, x] = safe(c) + (int(F.alpha[y, x]),)
    if F.mask.sum() >= 6:
        F.outline(W[0])


# ===================================================================================================== PANDEMONIUM
PD = dict(
    CRIM=ramp("2a080e", "4a0e16", "6c141e", "962026", "be3a34"),
    IVORY=ramp("5e4c3e", "8c7660", "b8a276", "dcc998", "f4eac6"),
    GOLD=ramp("3a2c14", "6a5a2e", "9c8a4a", "b49646", "e2cc84"),
    VIOL=ramp("1a1022", "2b1a36", "5b2f6e", "9a5cbf", "c48ae8"),
    PAINT=ramp("2e2638", "564c66", "8a7e94", "b8aeb6", "dad2cc"),
    BLK=ramp("100c12", "1e1a1c", "2a2630", "443e4c"),
    TEAL=ramp("12343a", "1f6466", "3aa49c"),
    WHITE=hx("fffbf0"), LINE=hx("140a14"),
)
CONFETTI = [hx("be3a34"), hx("e2cc84"), hx("3aa49c"), hx("9a5cbf"), hx("f4eac6"), hx("ff8a3a")]


def classify_blob(rgba, mask):
    h, s, v = hsv_arr(rgba)
    cls = np.full(mask.shape, "", "<U6")
    cls[mask] = "hide"
    cls[mask & (h >= 190) & (h <= 260) & (v < 0.32)] = "void"
    cls[mask & (s < 0.2) & (v >= 0.38) & (v < 0.8)] = "glass"
    cls[mask & (s < 0.2) & (v >= 0.38) & (v < 0.8) & (h >= 170) & (h <= 230)] = "glass"
    cls[mask & ((h >= 345) | (h < 12)) & (s >= 0.3) & (s < 0.6) & (v >= 0.5)] = "pink"
    cls[mask & ((h >= 352) | (h < 12)) & (s >= 0.6)] = "red"
    cls[mask & (h >= 320) & (h < 346) & (s >= 0.3) & (v < 0.7)] = "gum"
    cls[mask & (h >= 330) & (h < 350) & (s >= 0.55) & (v >= 0.85)] = "hot"
    cls[mask & (h >= 30) & (h <= 50) & (v >= 0.85)] = "cream"
    cls[mask & (h >= 15) & (h < 40) & (s >= 0.15) & (s < 0.45) & (v >= 0.6) & (v < 0.98)] = "flesh"
    cls[mask & (h >= 0) & (h < 12) & (s >= 0.25) & (s < 0.4) & (v >= 0.6)] = "flesh"
    cls[mask & (s < 0.06) & (v >= 0.95)] = "white"
    return cls


def smooth_rank(F, region, sigma=1.0):
    t = F.rank(region)
    m = region.astype(np.float32)
    num = ndimage.gaussian_filter(t * m, sigma); den = ndimage.gaussian_filter(m, sigma)
    out = np.where(den > 1e-3, num / np.maximum(den, 1e-3), 0)
    return np.clip(out, 0, 1) * region


def tent_stripes(F, region, ax, ay, n=7, frame_k=0):
    """Big-top canvas: crimson/ivory stripes fanning from the apex, shaded by the vanilla form."""
    P = PD
    t = F.rank(region)
    for y, x in zip(*np.nonzero(region)):
        ang = math.atan2(x - ax, (y - ay) + 10.0)
        k = int(math.floor(ang / (math.pi / (2 * n))))
        tt = t[y, x]
        c = pick(P["CRIM"][1:], tt) if k % 2 == 0 else pick(P["IVORY"][1:], tt * 0.9)
        # stitched seam where two panels meet
        nxt = math.atan2(x + 1 - ax, (y - ay) + 10.0)
        if int(math.floor(nxt / (math.pi / (2 * n)))) != k: c = mix(c, P["CRIM"][0], 0.45)
        F.out[y, x] = safe(c) + (255,)


def apex_of(F, region):
    ys, xs = np.nonzero(region)
    if not len(ys): return None
    y0 = ys.min()
    top = xs[ys <= y0 + 1]
    return float(top.mean()), float(y0)


def valance(F, region, ax):
    """Gold scalloped valance along the bottom hem with crimson tassel points."""
    P = PD
    H, W = region.shape
    for x in range(W):
        ys = np.nonzero(region[:, x])[0]
        if not len(ys): continue
        yb = ys.max()
        ph = (x - ax) % 6
        depth = 2 + (1 if ph in (2, 3) else 0)
        for j in range(depth + 1):
            y = yb - j
            if y < 0 or not region[y, x]: break
            if j == depth: F.put(x, y, P["GOLD"][1])
            else: F.put(x, y, P["GOLD"][4] if j == depth - 1 and ph in (2, 3) else P["GOLD"][3 - (j == 0)])
        if ph == 3 and yb + 1 < H: F.put(x, yb, P["CRIM"][3])


def bunting(F, region, ax, ay, w, h, phase=0):
    """A sagging string of pennants across the canvas (on the art only)."""
    P = PD
    xa, xb = ax - w * 0.36, ax + w * 0.36
    yl = ay + h * 0.42
    pts = bezier((xa, yl), (ax, yl + 5), (xb, yl))
    for i, (x, y) in enumerate(pts):
        if 0 <= y < F.H and 0 <= x < F.W and region[y, x]:
            F.put(x, y, P["BLK"][2])
            if i % 5 == 2:
                c = CONFETTI[(i // 5 + phase) % 4]
                for dx, dy in ((0, 1), (1, 1), (0, 2)):
                    if 0 <= y + dy < F.H and region[y + dy, x + dx if x + dx < F.W else x]: F.put(x + dx, y + dy, c)


def pennant(F, ax, ay, k):
    P = PD
    x, y = int(round(ax)), int(round(ay))
    for j in range(1, 6): F.put(x, y - j, P["BLK"][3] if j < 5 else P["GOLD"][4])
    wave = k % 2
    for dx, dy in ((1, -5), (2, -5), (3, -5 + wave), (1, -4), (2, -4 + wave * 0), (1, -3)):
        F.put(x + dx, y + dy, P["CRIM"][4] if dy == -5 else P["CRIM"][3])


def paint_pan_tent(F, ctx):
    region = F.mask & ~F.of("void")
    a = apex_of(F, F.mask)
    if a is None: return
    ax, ay = a
    tent_stripes(F, region, ax, ay)
    F.fill(F.of("void"), lambda x, y: PD["BLK"][1])
    for c in ("pink", "red", "gum", "hot", "flesh"):
        F.fill(F.of(c), lambda x, y: PD["GOLD"][3])
    x0, y0, x1, y1 = F.bbox
    if x1 - x0 > 30:
        valance(F, F.mask, ax)
        bunting(F, F.mask, ax, ay, x1 - x0, y1 - y0, ctx.get("fi", 0) // 3)
    ys, xs = np.nonzero(F.soft)
    for y, x in zip(ys, xs): F.out[y, x] = (24, 16, 26, int(F.alpha[y, x]))
    F.outline(PD["LINE"])
    if x1 - x0 > 30: pennant(F, ax, ay, ctx.get("fi", 0) // 2)


def paint_pan_face(F, ctx):
    """Eye / mouth / head blobs in white greasepaint with harlequin diamonds, pinwheel iris, red grin, gold teeth."""
    P = PD
    hide = F.of("hide")
    t = smooth_rank(F, hide) * 0.55 + F.rank(hide) * 0.45      # smooth greasepaint, but keep lids and creases
    F.fill(hide, lambda x, y: pick(P["PAINT"], t[y, x] * 0.92 + 0.06))
    glow = []
    # eye: sclera stays ivory, the pupil sits in a violet pinwheel iris
    cream = F.of("cream")
    sclera = [c for c in comps(cream, 6)]
    eyes = []
    for xs, ys in sclera:
        cx, cy = xs.mean(), ys.mean()
        r = max(1.0, math.sqrt(len(xs) / math.pi))
        eyes.append((cx, cy, r, xs, ys))
    voids = F.of("void")
    mouth_void = voids.copy()
    for cx, cy, r, xs, ys in eyes:
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        inner = np.zeros_like(voids); inner[y0:y1 + 1, x0:x1 + 1] = True
        pupil = voids & inner
        mouth_void &= ~pupil
        for x, y in zip(xs, ys):
            d = math.hypot(x - cx, y - cy)
            if d < r * 0.62:
                ang = math.atan2(y - cy, x - cx) + d * 0.9
                F.put(x, y, P["VIOL"][3] if int(math.floor(ang / (math.pi / 3))) % 2 == 0 else P["VIOL"][4])
            else:
                F.put(x, y, P["IVORY"][4] if y - cy < r * 0.4 else P["IVORY"][3])
        F.fill(pupil, lambda x, y: P["BLK"][0])
        glow.append((int(round(cx - r * 0.35)), int(round(cy - r * 0.35)), P["WHITE"]))
        # harlequin diamonds above and below the eye, painted onto the greasepaint
        for sgn in (-1, 1):
            dy0 = (y0 - 3) if sgn < 0 else (y1 + 3)
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if abs(dx) + abs(dy) <= 2:
                        xx, yy = int(round(cx)) + dx, dy0 + dy * (1 if abs(dx) < 2 else 1)
                        if 0 <= yy < F.H and 0 <= xx < F.W and hide[yy, xx]:
                            F.put(xx, yy, P["CRIM"][3] if abs(dx) + abs(dy) < 2 else P["CRIM"][2])
    # small cream bits that are not eyes (teeth, eyelets)
    teeth = cream.copy()
    for cx, cy, r, xs, ys in eyes: teeth[ys, xs] = False
    F.fill(mouth_void, lambda x, y: P["BLK"][1] if (x + y) % 5 else P["VIOL"][1])
    F.fill(F.of("gum", "pink"), lambda x, y: P["CRIM"][4] if F.L[y, x] > 0.45 else P["CRIM"][3])
    F.fill(F.of("red"), lambda x, y: P["CRIM"][2])
    F.fill(teeth, lambda x, y: P["GOLD"][4] if (x // 2) % 3 else P["IVORY"][4])
    F.fill(F.of("white"), lambda x, y: P["WHITE"])
    if F.of("glass").any(): orb(F, F.of("glass"), F.of("flesh", "hot"), ctx)
    else: F.fill(F.of("hot", "flesh"), lambda x, y: P["VIOL"][3])
    ys, xs = np.nonzero(F.soft)
    for y, x in zip(ys, xs): F.out[y, x] = (24, 16, 26, int(F.alpha[y, x]))
    # red nose ball: centred over the mouth (the lips' top edge), below any eye
    lips = F.of("gum", "pink") | mouth_void
    comps_l = comps(lips, 8)
    if comps_l:
        xs, ys = max(comps_l, key=lambda c: len(c[0]))
        nx_, ny_ = int(round(xs.mean())), int(ys.min()) - 2
        if eyes:
            ey = max(e[1] + e[2] for e in eyes)
            ny_ = int(round(max(ny_, ey + 2)))
            if ny_ >= ys.min(): ny_ = int(ys.min()) - 1
        if 0 <= ny_ < F.H and F.mask[min(F.H - 1, max(0, ny_)), nx_]:
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
                F.put(nx_ + dx, ny_ + dy, P["CRIM"][4] if dy < 0 or (dx < 0 and dy == 0) else P["CRIM"][3])
            glow.append((nx_ - 1, ny_ - 1, P["WHITE"]))
    F.outline(P["LINE"])
    for x, y, c in glow: F.put(x, y, c)


def paint_pan_tentacle(F, ctx):
    """Striped canvas tentacles: bands follow the arm (geodesic from the root), sequined gold suckers, ball nodules."""
    P = PD
    mask = F.mask
    if F.bbox is None: return
    s = F.geodesic(root_seeds(mask))
    body = mask & ~F.of("pink", "gum", "red", "hot")
    t = F.rank(body)
    under = mask & ~body
    tu = F.rank(under)
    for y, x in zip(*np.nonzero(body)):
        sv = s[y, x]
        band = int(sv / 4.0) if sv >= 0 else 0
        c = pick(P["CRIM"][1:], t[y, x]) if band % 2 == 0 else pick(P["IVORY"][1:], t[y, x] * 0.9)
        if sv >= 0 and sv % 4.0 < 0.8: c = mix(c, P["GOLD"][3], 0.5)    # gold piping between bands
        F.out[y, x] = safe(c) + (255,)
    for y, x in zip(*np.nonzero(under)):
        c = pick(P["GOLD"][1:], tu[y, x])
        if (x + 2 * y) % 4 == 0: c = P["GOLD"][4]                      # sequin glints
        F.out[y, x] = safe(c) + (255,)
    ys, xs = np.nonzero(F.soft)
    for y, x in zip(ys, xs): F.out[y, x] = (24, 16, 26, int(F.alpha[y, x]))
    F.outline(P["LINE"])
    # juggling-ball nodules on the outer (non-sucker) edge
    du = ndimage.distance_transform_edt(~under) if under.any() else np.full(mask.shape, 9.0)
    smax = s.max()
    for k, s0 in enumerate((7, 14, 21, 28)):
        if s0 > smax - 3: break
        cand = np.nonzero(F.edge & (np.abs(s - s0) < 1.0))
        if not len(cand[0]): continue
        i = int(np.argmax(du[cand]))
        by, bx = int(cand[0][i]), int(cand[1][i])
        ball(F, bx, by, CONFETTI[[1, 2, 3, 0][k % 4]])


def ball(F, x, y, col):
    dark = mix(col, (20, 10, 20), 0.55)
    for dx, dy in ((-1, 0), (0, -1), (1, 0), (0, 1), (0, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        F.put(x + dx, y + dy, dark if (dx + dy > 0) else col)
    F.put(x - 1, y - 1, mix(col, (255, 255, 240), 0.6))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        g = F.get(x + dx, y + dy)
        if g is not None and g[3] == 0: F.put(x + dx, y + dy, PD["LINE"])


def orb(F, glass, mist, ctx):
    P = PD
    t = F.rank(glass)
    F.fill(glass, lambda x, y: pick(P["VIOL"][1:], t[y, x]))
    if mist.any():
        ys, xs = np.nonzero(mist); cx, cy = xs.mean(), ys.mean()
        tm = F.rank(mist)
        k = ctx.get("fi", 0)
        for y, x in zip(ys, xs):
            r = math.hypot(x - cx, y - cy)
            ang = math.atan2(y - cy, x - cx) - r * 0.55 + k * 0.5
            arm = int(math.floor(ang / (math.pi / 2))) % 2
            c = pick(P["VIOL"][2:], tm[y, x]) if arm else mix(pick(P["GOLD"][2:], tm[y, x]), CONFETTI[3], 0.25)
            F.put(x, y, c)
        F.put(cx, cy, P["WHITE"])
    if glass.any():
        ys, xs = np.nonzero(glass)
        gx, gy = int(np.percentile(xs, 25)), int(np.percentile(ys, 20))
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            F.put(gx + dx, gy + dy, P["WHITE"] if dx == dy == 0 else P["VIOL"][4])


def paint_pan_orb(F, ctx):
    """The brain bubble becomes a fortune-teller's crystal ball: violet glass, a swirling mist inside, a star glint."""
    P = PD
    glass = F.of("glass")
    mist = F.of("flesh", "hot", "red", "pink", "gum")
    rest = F.mask & ~glass & ~mist
    F.fill(rest & F.of("white"), lambda x, y: P["WHITE"])
    F.fill(rest & F.of("cream"), lambda x, y: P["GOLD"][4])
    F.fill(rest & F.of("void"), lambda x, y: P["BLK"][1])
    hide = rest & F.of("hide")
    th = F.rank(hide)
    F.fill(hide, lambda x, y: pick(P["PAINT"], th[y, x] * 0.95 + 0.05))
    ys, xs = np.nonzero(F.soft)
    for y, x in zip(ys, xs): F.out[y, x] = (40, 24, 56, int(F.alpha[y, x]))
    F.outline(P["LINE"])
    orb(F, glass, mist, ctx)


def paint_pan_whole(F, ctx):
    """Whole-creature frames (intro / explode): tent canvas for the hide, face features where eye and mouth show."""
    P = PD
    a = apex_of(F, F.mask)
    if a is None: return
    paint_pan_face(F, ctx)
    hide = F.of("hide")
    tent_stripes(F, hide, a[0], a[1])
    # the death geyser and its spatter: a cascade of streamers and confetti instead of blood
    for xs, ys in comps(F.of("red", "gum", "pink"), 1):
        big = len(xs) > 40
        for x, y in zip(xs, ys):
            if big:
                c = CONFETTI[((y // 3) + (1 if x % 4 == 0 else 0)) % 4]
                if F.L[y, x] < 0.22: c = mix(c, (20, 10, 20), 0.35)
            else:
                c = CONFETTI[int(hsh("sp", ctx.get("index"), int(xs.min()), int(ys.min())) * 5)]
            F.put(x, y, c)
    F.outline(P["LINE"])


def paint_pan_bomber(F, ctx):
    """The bomb-fodder blobs become juggling balls: crimson/gold quarters around the centre, a fuse-knot on top."""
    P = PD
    if F.bbox is None: return
    reg = F.mask
    ys, xs = np.nonzero(reg)
    cx, cy = xs.mean(), ys.mean()
    t = F.rank(reg)
    for y, x in zip(ys, xs):
        c = F.cls[y, x]
        if c == "white": F.put(x, y, P["WHITE"]); continue
        q = (int(x >= cx) + int(y >= cy)) % 2
        F.put(x, y, pick(P["CRIM"][1:], t[y, x]) if q else pick(P["GOLD"][1:], t[y, x]))
    ys2, xs2 = np.nonzero(F.soft)
    for y, x in zip(ys2, xs2): F.out[y, x] = (24, 16, 26, int(F.alpha[y, x]))
    F.outline(P["LINE"])
    if len(xs) > 12:
        F.put(cx - 1, ys.min() + 1, P["WHITE"])


def paint_pan_confetti(F, ctx):
    """Gore, gibs and brain splashes become confetti and torn canvas: each fleck one colour, picked by its shape."""
    reg = F.mask | F.soft
    _, sat, _ = hsv_arr(F.src)
    for xs, ys in comps(reg):
        if np.mean(sat[ys, xs]) < 0.22:      # splashed water stays water
            for x, y in zip(xs, ys): F.out[y, x] = F.src[y, x]
            continue
        c = CONFETTI[int(hsh("cf", ctx.get("index"), int(xs.min()), int(ys.min())) * len(CONFETTI))]
        n = len(xs)
        for x, y in zip(xs, ys):
            cc = c
            if n > 12:   # big chunks are striped canvas
                cc = PD["CRIM"][3] if ((x + y) // 3) % 2 else PD["IVORY"][3]
            if F.L[y, x] < 0.25: cc = mix(cc, (20, 10, 20), 0.4)
            F.put(x, y, cc, int(F.alpha[y, x]))


def paint_pan_gold(F, ctx):
    """Indicators: vanilla dots/dashes in gold."""
    for y, x in zip(*np.nonzero(F.alpha > 0)):
        F.put(x, y, pick(PD["GOLD"][2:], F.L[y, x]), int(F.alpha[y, x]))


# ===================================================================================================== the bosses
BOSSES = [
    dict(name="Leviathan", sheet="BossLeviathanArt", root="BossHydra", atlas="AtlasBossHydra", apid=39921,
         classify=classify_hydra, rules=[
             (r"_Blood|HeadSever_Blood|HeadDeathExplode", "fx", paint_lev_ichor),
             (r"^(Hydra_Body_|Hydra_Lose_A_Head_Body|Hydra_Lose_Final_Head_Dea|Hydra_Win_Roar_Body)", "body", paint_lev_body),
             (r"^H_Head", "flying_heads", paint_lev_head),
             (r"^(HeadA|HeadCooldownA|Hydra_HeadA|Hydra_Lose_A_Head_HeadA$|Hydra_Win_Roar_HeadA|Hydra_Lost_Head_Nub_A)", "headA", paint_lev_head),
             (r"^(HeadB|HeadCooldownB|Hydra_HeadB|Hydra_Lose_A_Head_HeadB$|Hydra_Win_Roar_HeadB|Hydra_Lost_Head_Nub_B)", "headB", paint_lev_head),
             (r"^(HeadC|HeadCooldownC|Hydra_HeadC|Hydra_Lose_A_Head_HeadC$|Hydra_Win_Roar_HeadC|Hydra_Lost_Head_Nub_C)", "headC", paint_lev_head),
             (r"DFX_hydra_small|FX_hydra_small|muzzleflare|goo_vom|flamethrower|FlameThrower|flame_smoke|HasAttack_(Flame|Goo|Ice)|FX_hydra_frost|FX_IceFrostCloud", "fx", paint_lev_water),
         ]),
    dict(name="Pandemonium", sheet="BossPandemoniumArt", root="BossTentacleBlob", atlas="AtlasBoss", apid=39919,
         classify=classify_blob, rules=[
             (r"^Boss_TentacleBlob_Body_", "tent", paint_pan_tent),
             (r"^Boss_TentacleBlob_Arm|^BossMeleeTentacleStrike", "tentacles", paint_pan_tentacle),
             (r"^Boss_TentacleBlob_(Eye|Mouth|Head)_|Conjoined_BeamAttack_(Eye|Mouth)", "face", paint_pan_face),
             (r"^Boss_TentacleBlob_Bubble_|Conjoined_BeamAttack_Bubble", "orb", paint_pan_orb),
             (r"^Boss_TentacleBlob_WholeGuy_", "whole", paint_pan_whole),
             (r"^(Spawn_Guy|Idle|Run|HitRoll|HitRoll_Then_SwellAndBurst|SwellAndBurst2|FinalSwell)$", "fx", paint_pan_bomber),
             (r"^FXBossGib(?!Water)|^BrainSplash", "fx", paint_pan_confetti),
             (r"^BossBeamIndicator|^DirectionIndicatorLong", "fx", paint_pan_gold),
         ]),
]


def paint_pan_beam(F, ctx):
    """The eye's beam becomes a golden spotlight shaft (cream core, gold body, amber edges, drifting dust motes);
    its end piece (the beam's dying wiggles) becomes gold streamer curls with sparkles."""
    P = PD
    reg = F.alpha > 0
    if not reg.any(): return
    H, W = reg.shape
    fi = ctx.get("fi", 0)
    tl = F.rank(reg)
    for x in range(W):
        ys = np.nonzero(reg[:, x])[0]
        if not len(ys): continue
        y0, y1 = ys.min(), ys.max()
        cy, hh = (y0 + y1) / 2.0, max(1.0, (y1 - y0) / 2.0)
        for y in ys:
            d = abs(y - cy) / hh
            if hh < 2.5: c = P["GOLD"][4] if tl[y, x] > 0.4 else P["GOLD"][3]          # thin curls
            elif d < 0.28: c = P["IVORY"][4]
            elif d < 0.62: c = mix(P["GOLD"][4], P["IVORY"][4], 0.35 * tl[y, x])
            elif d < 0.9: c = P["GOLD"][3]
            else: c = P["GOLD"][2]
            if hh >= 2.5 and hsh("mote", x // 2, y // 2, fi) < 0.025: c = P["WHITE"]
            F.put(x, y, c, int(F.alpha[y, x]))
        # sequin sparkles riding just outside the shaft
        if hh >= 4 and (x + fi * 5) % 19 == 0:
            sy = y0 - 2 if (x // 19) % 2 else y1 + 2
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                F.put(x + dx, sy + dy, P["WHITE"] if dx == dy == 0 else P["GOLD"][4], 220)


def paint_pan_firework(F, ctx):
    """The death blasts and rings become fireworks: each streak / ring one confetti colour with a hot core."""
    P = PD
    reg = (F.alpha > 0)
    for xs, ys in comps(reg):
        k = int(hsh("fw", ctx.get("index"), int(xs.min()), int(ys.min())) * 4)
        base = [P["GOLD"][4], CONFETTI[0], CONFETTI[2], CONFETTI[3]][k]
        for x, y in zip(xs, ys):
            l = F.L[y, x]
            c = pick(P["VIOL"][:3], l * 3) if l < 0.25 else mix(base, P["WHITE"], max(0.0, l - 0.6))
            F.put(x, y, c, int(F.alpha[y, x]))


def paint_pan_smoke(F, ctx):
    """The bomb going off in the mouth: violet greasepaint smoke shot through with confetti flecks."""
    P = PD
    reg = F.alpha > 0
    t = F.rank(reg)
    for y, x in zip(*np.nonzero(reg)):
        c = mix(pick(P["VIOL"][1:], t[y, x]), pick(P["PAINT"], t[y, x]), 0.35)
        if hsh("fl", ctx.get("index"), x // 2, y // 2) < 0.06: c = CONFETTI[int(hsh("flc", x, y) * 5)]
        F.put(x, y, c, int(F.alpha[y, x]))


# the boss FX that live on the shared vanilla effects atlas (beam, blasts, blood, puddles): their own sheets, applied
# to the boss's cloned effect chains only (the vanilla clips are never touched)
BOSSES += [
    dict(name="LeviathanFx", sheet="BossLeviathanFx", root="BossHydra", atlas="AtlasEffectsShared", apid=39923, depth=6,
         classify=classify_hydra, rules=[
             (r"^(BloodPoolNewA|BloodSmearA|BloodSplashGeneric)", "fx", paint_lev_ichor),
             (r"^(LavaEffectLonger|DFX_GooPuddle|AcidSplash|FrozenIceA)", "fx", paint_lev_water),
         ]),
    dict(name="PandemoniumFx", sheet="BossPandemoniumFx", root="BossTentacleBlob", atlas="AtlasEffectsShared", apid=39923,
         depth=6, classify=classify_blob, rules=[
             (r"^BossBeam(End)?$", "beam", paint_pan_beam),
             (r"^(BeamBlasts|FXBossDeathBlastsCircle)", "fx", paint_pan_firework),
             (r"^Effect_BombExplosion_", "fx", paint_pan_smoke),
             (r"^BloodSplashGeneric", "fx", paint_pan_confetti),
         ]),
]


def plan(boss):
    """element index -> (rule index, part, painter name, clip name, frame index); plus part -> [(clip name, frames)]."""
    pids, _ = reachable_clips(boss["root"], boss.get("depth", 6))
    apid = boss["apid"]
    best = {}
    parts = defaultdict(list)
    for pid in sorted(pids):
        c = _CLIPS.get(pid)
        if not c: continue
        name = c["m_Name"]
        for ri, (rx, part, fn) in enumerate(boss["rules"]):
            if re.search(rx, name): break
        else:
            continue
        frames = [(f["atlas"]["m_PathID"], f["index"]) for f in c["frameInfos"]]
        mine = [i for a, i in frames if a == apid]
        if not mine: continue
        parts[part].append((name, pid, frames))
        for fi, (a, i) in enumerate(frames):
            if a != apid: continue
            e = elem(apid, i)
            if e["trimRect"]["width"] <= 0 or e["trimRect"]["height"] <= 0: continue
            k = (ri, name, fi)
            if i not in best or k < best[i][:3]:
                best[i] = (ri, name, fi, part, fn.__name__)
    return best, parts


def _paint_one(args):
    bi, idx, clip, fi, fname = args
    boss = BOSSES[bi]
    v = vframe(boss["apid"], idx)
    F = Frame(v, boss["classify"])
    globals()[fname](F, {"clip": clip, "index": idx, "fi": fi, "boss": boss["name"]})
    out = F.out
    a = out[..., 3] > 0
    if not a.any(): return idx, None, None
    ys, xs = np.nonzero(a)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    return idx, (int(x0), int(y0)), out[y0:y1, x0:x1].copy()


def pack(items, width=1024, pad=2):
    """Shelf packer: items = {idx: array}; returns {idx: (x, y)}, height."""
    order = sorted(items, key=lambda k: (-items[k].shape[0], -items[k].shape[1], k))
    pos = {}
    x = y = shelf = 0
    for k in order:
        h, w = items[k].shape[:2]
        if x + w > width:
            x = 0; y += shelf + pad; shelf = 0
        pos[k] = (x, y)
        x += w + pad; shelf = max(shelf, h)
    return pos, y + shelf


def build(boss, bi, pool=None):
    best, parts = plan(boss)
    jobs = [(bi, idx, v[1], v[2], v[4]) for idx, v in sorted(best.items())]
    res = pool.map(_paint_one, jobs, chunksize=8) if pool else list(map(_paint_one, jobs))
    art = {}
    for idx, off, a in res:
        if a is not None: art[idx] = (off, a)
    pos, H = pack({k: v[1] for k, v in art.items()})
    H = max(1, H)
    sheet = np.zeros((H, 1024, 4), np.uint8)
    rows = []
    for idx in sorted(art):
        (ox, oy), a = art[idx]
        x, y = pos[idx]
        h, w = a.shape[:2]
        sheet[y:y + h, x:x + w] = a
        e = elem(boss["apid"], idx)
        rows.append([int(idx), int(x), int(y), int(w), int(h), int(ox) - MARGIN, int(oy) - MARGIN])
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(sheet).save(os.path.join(OUT, boss["sheet"] + ".png"), optimize=True)
    man = {
        "boss": boss["name"], "atlas": boss["atlas"], "width": 1024, "height": H,
        "elementCount": len(_ATL[boss["apid"]]["elements"]),
        "format": "elements: [vanilla element index, x, y (top-left in this png), w, h, trimX, trimY (trimRect in the "
                  "vanilla original cell, y from the top as ex2D stores it)]",
        "parts": {p: sorted(set(n for n, _, _ in v)) for p, v in parts.items()},
        "elements": rows,
    }
    with open(os.path.join(OUT, boss["sheet"] + ".json"), "w") as f:
        json.dump(man, f, separators=(",", ":"))
    return art, parts, best


# ===================================================================================================== contact images
def _label(img, x, y, text):
    from PIL import ImageDraw
    ImageDraw.Draw(img).text((x, y), text, fill=(200, 196, 210, 255))


def contact(boss, art, parts, maxf=8, scale=3):
    from PIL import ImageDraw
    apid = boss["apid"]
    outs = []
    for part, clips in sorted(parts.items()):
        rows = []
        seen = set()
        for name, pid, frames in sorted(clips, key=lambda c: c[0]):
            if name in seen: continue
            seen.add(name)
            fr = [(a, i) for a, i in frames if a == apid]
            step = max(1, (len(fr) + maxf - 1) // maxf)
            fr = fr[::step][:maxf]
            van, new = [], []
            for a, i in fr:
                v = vframe(a, i)
                n = np.zeros_like(v)
                if i in art:
                    (ox, oy), arr = art[i]
                    h, w = arr.shape[:2]
                    H0, W0 = n.shape[:2]
                    # new art may extend past the cell (it never should): clip for the preview
                    n[oy:min(H0, oy + h), ox:min(W0, ox + w)] = arr[:min(h, H0 - oy), :min(w, W0 - ox)]
                van.append(v); new.append(n)
            # one crop box for the whole anim so motion reads
            acc = np.zeros(van[0].shape[:2], bool)
            for v, n in zip(van, new): acc |= (v[..., 3] > 0) | (n[..., 3] > 0)
            if not acc.any(): continue
            ys, xs = np.nonzero(acc)
            x0, y0, x1, y1 = max(0, xs.min() - 1), max(0, ys.min() - 1), xs.max() + 2, ys.max() + 2
            rows.append((name, len(frames), [v[y0:y1, x0:x1] for v in van], [n[y0:y1, x0:x1] for n in new]))
        if not rows: continue
        cw = max(r[2][0].shape[1] for r in rows); lab = 150
        W = lab + (cw * 2 + 6) * maxf
        Hs = [max(r[2][0].shape[0], 10) + 4 for r in rows]
        # split very tall parts into several images
        chunks, cur, hh = [], [], 0
        for r, h in zip(rows, Hs):
            if cur and (hh + h) * scale > 3000: chunks.append(cur); cur, hh = [], 0
            cur.append((r, h)); hh += h
        if cur: chunks.append(cur)
        for ci, ch in enumerate(chunks):
            im = Image.new("RGBA", (W, sum(h for _, h in ch)), (46, 42, 52, 255))
            y = 0
            for (name, nf, vs, ns), h in ch:
                _label(im, 2, y + 1, "%s (%d)" % (name[:24], nf))
                x = lab
                for v, n in zip(vs, ns):
                    im.alpha_composite(Image.fromarray(v), (x, y))
                    im.alpha_composite(Image.fromarray(n), (x + v.shape[1] + 2, y))
                    x += cw * 2 + 6
                y += h
            big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            fn = os.path.join(BOARDS, "bosses_new_%s_%s%s.png" % (boss["name"], part, "" if len(chunks) == 1 else "_%d" % (ci + 1)))
            big.save(fn)
            outs.append(fn)
    return outs


def main():
    load_vanilla()
    os.makedirs(BOARDS, exist_ok=True)
    import multiprocessing as mp
    only = sys.argv[1:] or [b["name"] for b in BOSSES]
    with mp.get_context("fork").Pool(max(1, os.cpu_count() or 1)) as pool:
        for bi, boss in enumerate(BOSSES):
            if boss["name"] not in only: continue
            art, parts, best = build(boss, bi, pool)
            for f in glob_old(boss["name"]): os.remove(f)
            outs = contact(boss, art, parts) + ([scene(boss, art)] if boss["name"] in SCENES else [])
            print("%s: %d elements redrawn (%d planned), sheet %s.png, %d contact images" %
                  (boss["name"], len(art), len(best), boss["sheet"], len(outs)))


def glob_old(name):
    import glob
    return glob.glob(os.path.join(BOARDS, "bosses_new_%s_*.png" % name))



# scene previews: every part cell of a boss shares one frame layout (the prefab offsets cancel the part positions),
# so the parts composite by simply stacking their cells. (clip, frame) lists, back to front.
SCENES = {
    "Leviathan": [
        ("idle", [("Hydra_Body_Idle", 0), ("Hydra_HeadC_Idle_Right", 0), ("Hydra_HeadB_Idle_Right", 0), ("Hydra_HeadA_Idle_Right", 0)]),
        ("aim", [("Hydra_Body_Idle", 2), ("HeadC_8", 0), ("HeadB_3", 0), ("HeadA_6", 0)]),
        ("attack", [("Hydra_Body_Run2", 1), ("HeadC_360_AttackLarge2", 1), ("HeadB_360_AttackLarge1", 2), ("HeadA_360_AttackLarge4", 1)]),
        ("hurt", [("Hydra_Lose_A_Head_Body", 2), ("Hydra_HeadC_Idle_LeftCooldown", 0), ("Hydra_Lost_Head_Nub_B", 0), ("Hydra_Lose_A_Head_HeadA", 4)]),
        ("roar", [("Hydra_Win_Roar_Body", 30), ("Hydra_Win_Roar_HeadC", 30), ("Hydra_Win_Roar_HeadB", 30), ("Hydra_Win_Roar_HeadA", 30)]),
    ],
    "Pandemonium": [
        ("idle", [("Boss_TentacleBlob_Body_Idle", 0), ("Boss_TentacleBlob_ArmL_ActiveIdle", 0), ("Boss_TentacleBlob_ArmR_ActiveIdle", 0),
                  ("Boss_TentacleBlob_Eye_ActiveIdle", 0), ("Boss_TentacleBlob_Mouth_ClosedIdle", 0)]),
        ("attack", [("Boss_TentacleBlob_Body_Idle", 4), ("Boss_TentacleBlob_ArmL_AttackThrow", 4), ("Boss_TentacleBlob_ArmR_AttackThrow2", 3),
                    ("Boss_TentacleBlob_Conjoined_BeamAttack_Eye", 12), ("Boss_TentacleBlob_Conjoined_BeamAttack_Mouth", 12),
                    ("Boss_TentacleBlob_Conjoined_BeamAttack_Bubble", 12)]),
        ("roar", [("Boss_TentacleBlob_Body_Idle", 2), ("Boss_TentacleBlob_ArmL_InactiveIdle", 0), ("Boss_TentacleBlob_ArmR_InactiveIdle", 0),
                  ("Boss_TentacleBlob_Head_Roar", 10)]),
        ("vulnerable", [("Boss_TentacleBlob_Body_VulnerableLoop", 0), ("Boss_TentacleBlob_Head_VulnerableLoop", 0),
                        ("Boss_TentacleBlob_Bubble_VulnerableLoop", 0)]),
        ("intro", [("Boss_TentacleBlob_WholeGuy_Intro", 60)]),
    ],
}


def scene(boss, art, scale=3):
    apid = boss["apid"]
    tiles = []
    for label, layers in SCENES.get(boss["name"], []):
        van = new = None
        for name, fi in layers:
            if name not in _BYNAME: continue
            fr = clip_frames(name)
            a, i = fr[min(fi, len(fr) - 1)]
            v = vframe(a, i)
            n = np.zeros_like(v)
            if a == apid and i in art:
                (ox, oy), arr = art[i]
                h, w = arr.shape[:2]
                n[oy:oy + h, ox:ox + w] = arr[:n.shape[0] - oy, :n.shape[1] - ox]
            elif a != apid:
                n = v
            if van is None:
                van = Image.new("RGBA", (v.shape[1], v.shape[0]), (0, 0, 0, 0)); new = van.copy()
            van.alpha_composite(Image.fromarray(v)); new.alpha_composite(Image.fromarray(n))
        bb = van.getbbox(); nb = new.getbbox()
        bb = (min(bb[0], nb[0]) - 2, min(bb[1], nb[1]) - 2, max(bb[2], nb[2]) + 2, max(bb[3], nb[3]) + 2)
        tiles.append((label, van.crop(bb), new.crop(bb)))
    W = max(t[1].width for t in tiles) * 2 + 12
    H = sum(t[1].height + 12 for t in tiles)
    im = Image.new("RGBA", (W, H), (58, 54, 50, 255))   # a dungeon-floor grey-brown so dark art reads like in game
    y = 0
    for label, v, n in tiles:
        _label(im, 1, y, label)
        im.alpha_composite(v, (4, y + 10)); im.alpha_composite(n, (v.width + 8, y + 10))
        y += v.height + 12
    fn = os.path.join(BOARDS, "bosses_new_%s_scene.png" % boss["name"])
    im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(fn)
    im.save(os.path.join(BOARDS, "bosses_new_%s_scene_1x.png" % boss["name"]))   # game scale
    return fn


if __name__ == "__main__":
    main()
