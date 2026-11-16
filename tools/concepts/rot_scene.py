"""Rot Gardens as one designed scene (third pass, after the owner's notes of 2026-11-16: "it needs to be a newly
designed intentionally thought out and put together scene").

The idea: an old underground kitchen garden the dungeon swallowed. Flagstone paths, raised beds of dark loam edged
with cobbles, roots coming down the walls and across the floor into the beds, fungus grown out of the beds instead of
vegetables, and the only light in the room coming off the small glowing caps.

What keeps it one scene, taken from the base game's rooms (see build/study):
  - one palette for everything: the floor, the wall, every prop and the light are drawn from the same few ramps
    (PAL below), so nothing carries colours of its own from somewhere else;
  - the room's identity is in the floor and wall themselves (the way the Crypt has rugs and the Mines have tracks):
    here the paths, beds and roots are painted into the room's own floor shape;
  - props are small, low contrast, three or four tones, edged in a dark tone of their own colour, standing on a soft
    shadow, and they grow out of the beds in groups that belong together, never one by one across the floor;
  - the middle of the room is path, open to walk and fight on;
  - light comes from things in the room (the glowing caps), with the rest of the room in shade.

Concept tool: nothing it makes ships. Needs the dump (build/dump/all).
    python3 tools/concepts/rot_scene.py  -> build/rot_scene/*.png
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import detail as D  # noqa: E402
import ingame as G  # noqa: E402
import paint as P  # noqa: E402
from paint import Mat, Sculpt  # noqa: E402

OUT = os.path.join(G.ROOT, "build", "rot_scene")

# ------------------------------------------------------------------ the palette: every colour in the room
PAL = {
    "stone": [(76, 76, 64), (91, 90, 75), (105, 103, 86), (118, 115, 96), (131, 127, 106)],
    "loam": [(46, 37, 33), (58, 46, 39), (70, 56, 46), (84, 67, 53)],
    "cobble": [(82, 80, 68), (106, 103, 86), (126, 122, 101), (144, 139, 115)],
    "moss": [(62, 68, 46), (76, 84, 54), (91, 99, 62), (108, 114, 72)],
    "root": [(52, 40, 36), (74, 58, 46), (96, 76, 58)],
    "wall": [(32, 31, 29), (48, 47, 42), (63, 62, 53), (79, 77, 64), (95, 92, 76)],
    "mauve": [(70, 52, 60), (94, 70, 78), (118, 90, 96), (140, 110, 112)],
    "ochre": [(84, 64, 44), (110, 86, 56), (136, 108, 70), (158, 128, 86)],
    "stem": [(84, 76, 70), (110, 102, 90), (136, 128, 112), (158, 150, 130)],
    "puff": [(86, 74, 56), (110, 96, 70), (134, 118, 86), (154, 138, 102)],
    "glow": [(92, 132, 112), (130, 182, 150), (176, 222, 186), (214, 244, 210)],
}
GLOW_LIGHT = (150, 220, 180)


def mat(name, **kw):
    """A sculpt material on one of the palette's ramps, low contrast like the game's props."""
    kw.setdefault("dither", 0.35)
    kw.setdefault("ambient", 0.34)
    kw.setdefault("diffuse", 0.72)
    return Mat(tones=PAL[name], **kw)


def done(sc, foot, sw, sh=None):
    im, em = sc.render()
    im, em = P.trim(im, em)
    return im, em, foot, P.shadow(sw, sh, alpha=90, colour=(14, 12, 12))


# ------------------------------------------------------------------ props, all from PAL
def tufted(made, seed, spread):
    """Moss tufts round a prop's foot, drawn as pixels (one to three tall, darker at the root)."""
    im, em, foot, sh = made
    rnd = random.Random(seed * 13 + 1)
    pad = 3
    W = max(im.width, int(spread * 2) + 4)
    out = Image.new("RGBA", (W, im.height + 1), (0, 0, 0, 0))
    out.alpha_composite(im, ((W - im.width) // 2, 0))
    if em is not None:
        e2 = Image.new("RGBA", out.size, (0, 0, 0, 0))
        e2.alpha_composite(em, ((W - im.width) // 2, 0))
        em = e2
    px = out.load()
    M = PAL["moss"]
    for i in range(int(spread * 1.6)):
        x = int(W / 2 + rnd.uniform(-spread, spread))
        h = rnd.choice([1, 1, 2, 2, 3])
        base = out.height - 1 - rnd.choice([0, 0, 1])
        for k in range(h):
            y = base - k
            if 0 <= x < W and y >= 0:
                px[x, y] = M[min(3, k + 1 + (1 if rnd.random() < 0.3 else 0))] + (255,)
    return out, em, foot, sh


def cap_into(sc, x, base, h, w, colour, kind="dome", lean=0.0, glow=False):
    """One mushroom sculpted into sc: a stem from base up h, a cap w across."""
    nz = P.Noise(int(x * 97 + base * 13 + h * 7))
    stem = mat("stem", ambient=0.2, diffuse=0.95, dither=0.25,
               tex=lambda px, py: (nz.v(px * 3.0, py * 0.5, 1.0) - 0.5) * 2, tex_amp=0.16)
    sr = max(0.8, w * 0.13)
    sc.lathe(lambda y: x + lean * (y - base) / max(1, h), base, base + h, lambda y: sr * (1.15 - 0.25 * (y - base) / max(1, h)), 0, stem)
    cx = x + lean
    top = base + h
    cm = mat(colour, emit=(lambda px, py, t: 0.9) if glow else None, ambient=0.24, diffuse=0.9, dither=0.45,
             tex=lambda px, py: (nz.fbm(px, py, 2.2) - 0.5) * 2, tex_amp=0.22)
    if kind == "dome":
        sc.ellipsoid(cx, top, 1.5, w / 2, w * 0.36, w * 0.4, cm, clip=lambda px, py: py >= top - 0.6)
    elif kind == "bell":
        sc.ellipsoid(cx, top - w * 0.1, 1.5, w / 2.4, w * 0.5, w * 0.4, cm, clip=lambda px, py: py >= top - w * 0.25)
    else:  # flat parasol
        sc.ellipsoid(cx, top, 1.5, w / 2, w * 0.2, w * 0.4, cm, clip=lambda px, py: py >= top - 0.4)
    # the gill line under the cap, one tone down from the stem's shade
    sc.disc(cx, top - 0.3, w / 2 - 0.6, 0.7, 1.0, mat(colour, flat=0.05), nrm=(0, -1, 0.2))


def cap_cluster(seed, colour="mauve", big=14, n=4):
    """A clump of caps that grow together: the tallest at the back, smaller ones round its foot, moss at the base."""
    rnd = random.Random(seed)
    W = big * 2 + 10
    sc = Sculpt(W, big + 10, seed)
    cx = W / 2
    kinds = ["dome", "bell", "flat"]
    # back to front, tallest first
    parts = [(cx + rnd.uniform(-2, 2), 2, big, big * 0.85, rnd.choice(kinds), rnd.uniform(-1.5, 1.5))]
    for i in range(n - 1):
        h = big * rnd.uniform(0.35, 0.65)
        parts.append((cx + rnd.choice([-1, 1]) * rnd.uniform(4, big * 0.7), 1, h, h * rnd.uniform(0.8, 1.05),
                      rnd.choice(kinds), rnd.uniform(-1.5, 1.5)))
    for (x, b, h, w, k, ln) in parts:
        cap_into(sc, x, b, h, w, colour, k, ln)
    return tufted(done(sc, (big * 0.45, 3), int(big * 1.6), 5), seed, big * 0.8)


def glow_caps(seed, n=5):
    """Small pale caps that give off light: the room's lamps."""
    rnd = random.Random(seed)
    sc = Sculpt(18, 10, seed)
    for i in range(n):
        h = rnd.uniform(2.5, 5.5)
        cap_into(sc, 9 + rnd.uniform(-6, 6), 1, h, rnd.uniform(2.6, 4.0), "glow", rnd.choice(["dome", "bell"]),
                 rnd.uniform(-0.8, 0.8), glow=True)
    return done(sc, (4, 2), 14, 4)


def puffball(seed, r=4.2):
    rnd = random.Random(seed)
    n = P.Noise(seed)
    sc = Sculpt(int(r * 2 + 6), int(r * 2 + 3), seed)
    cx = sc.w / 2
    tex = lambda x, y: (n.v(x, y, 1.6) - 0.5) * 2
    sc.ellipsoid(cx, r * 0.85 + 0.5, 0, r, r * 0.85, r, mat("puff", tex=tex, tex_amp=0.22))
    for i in range(int(r * 2)):                             # the warty skin
        a = rnd.uniform(0, math.pi * 2)
        sc.pixel(cx + math.cos(a) * r * 0.55, r * 0.85 + 0.5 + math.sin(a) * r * 0.45, r + 1, mat("puff", flat=0.0))
    sc.ellipsoid(cx, r * 1.7 + 0.5, 0.5, 1.0, 0.8, 0.6, mat("puff"))  # the pore on top
    return tufted(done(sc, (r * 0.8, 2), int(r * 2.2), 4), seed, r * 1.1)


def planter(seed):
    """A broken stone urn from when this was a garden, caps growing out of it."""
    rnd = random.Random(seed)
    sc = Sculpt(20, 24, seed)
    stone = mat("stone", ambient=0.4)
    prof = lambda y: 3.6 + 2.6 * math.sin(min(1.0, y / 8.0) * math.pi * 0.9)
    sc.lathe(lambda y: 10, 0, 8, prof, 0, stone)
    sc.lathe(lambda y: 10, 8, 9.6, lambda y: 5.6, 0, mat("cobble", ambient=0.45))       # the lip
    sc.disc(10, 9.4, 4.4, 1.3, 0.8, mat("loam", flat=0.1), nrm=(0, 1, 0.5))           # dark mouth
    sc.disc(13.6, 6.5, 0.6, 2.2, 6.5, mat("stone", flat=0.0), nrm=(0, 0, 1))            # a crack down its side
    cap_into(sc, 8.5, 9.4, 7, 7, "ochre", "dome", -0.6)
    cap_into(sc, 12.2, 9.4, 4, 5, "ochre", "flat", 0.6)
    return tufted(done(sc, (6, 3), 16, 5), seed, 7)


def wall_shelf(seed, colour="ochre"):
    """Bracket fungus stepping up the wall."""
    rnd = random.Random(seed)
    sc = Sculpt(12, 12, seed)
    y = 2
    for i in range(rnd.randint(2, 3)):
        w = rnd.uniform(6, 9) - i * 1.2
        sc.ellipsoid(6 + rnd.uniform(-1.5, 1.5), y, 2, w / 2, 1.3, 2.4, mat(colour), clip=lambda px, py, y=y: py >= y - 0.5)
        y += rnd.uniform(1.8, 2.6)
    im, em = sc.render()
    return P.trim(im, em)


def hanging_root(seed, length):
    """A root coming down the wall from the ceiling line: two or three strands, thinning, with a few hairs."""
    rnd = random.Random(seed)
    w = 9
    im = Image.new("RGBA", (w, length), (0, 0, 0, 0))
    px = im.load()
    R = PAL["root"]
    for s in range(rnd.randint(1, 3)):
        x = w / 2 + rnd.uniform(-2.5, 2.5)
        L = int(length * rnd.uniform(0.45, 1.0))
        for y in range(L):
            x += rnd.uniform(-0.45, 0.45)
            xi = int(round(x))
            if 0 <= xi < w:
                px[xi, y] = R[1] + (255,)
                if xi - 1 >= 0 and y < L * 0.6:
                    px[xi - 1, y] = R[2] + (255,)          # lit side
                if xi + 1 < w and y < L * 0.35:
                    px[xi + 1, y] = R[0] + (255,)          # shade side
            if rnd.random() < 0.08 and 1 <= xi < w - 1:
                hx = xi + rnd.choice([-1, 1])
                px[hx, min(L - 1, y + 1)] = R[0] + (255,)
    return im


# ------------------------------------------------------------------ the floor, painted into the room's own shape
def ramp_pick(ramp, v):
    k = np.clip(np.round(v * (len(ramp) - 1)), 0, len(ramp) - 1).astype(int)
    return np.array(ramp, float)[k]


def paint_floor(R, seed):
    """Paths of flagstones, raised beds of loam edged with cobbles, moss in the joints near the beds and walls,
    roots coming from the back wall into the beds. Returns the bed list (for planting) in world coordinates."""
    f = R.floor
    A = np.array(f.im)
    m = (A[..., 3] > 0) & (A[..., :3].sum(-1) > 60)
    H, W = m.shape
    rnd = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:H, 0:W]

    # flagstones: jittered rows of stones, wider than deep (the floor is seen at a slant)
    pts = []
    cw, ch = 11.0, 7.0
    for gy in range(-1, int(H / ch) + 2):
        off = (gy % 2) * cw / 2
        for gx in range(-1, int(W / cw) + 2):
            pts.append((gx * cw + off + rnd.uniform(-4, 4), gy * ch + rnd.uniform(-2.4, 2.4)))
    pts = np.array(pts)
    tree = cKDTree(pts * [1.0, 1.5])
    q = np.c_[xx.ravel() + 0.5, (yy.ravel() + 0.5) * 1.5]
    dd, ii = tree.query(q, k=2)
    joint = ((dd[:, 1] - dd[:, 0]) < 1.1).reshape(H, W)
    worn = ndimage.gaussian_filter(rnd.rand(H, W), 3.0)
    joint &= worn > np.percentile(worn, 30)               # joints worn away in places, stones run together
    cell = ii[:, 0].reshape(H, W)
    tone = rnd.normal(0, 1, len(pts))[cell]
    mott = ndimage.gaussian_filter(rnd.rand(H, W), 2.2)
    mott = (mott - mott.mean()) / (mott.std() + 1e-6)
    # inside each stone, a touch lighter toward its top left edge (worn, catching the light)
    lit = ndimage.gaussian_filter((~joint).astype(float), 1.0)
    v = 0.55 + 0.06 * tone + 0.12 * mott
    v = v + np.where(np.roll(joint, 1, 0), 0.07, 0.0)
    col = ramp_pick(PAL["stone"], np.clip(v, 0, 1))
    col[joint] = ramp_pick(PAL["stone"], np.clip(v[joint] - 0.26, 0, 1))

    # the beds: along the back wall and in a front corner, never in the middle third
    beds = []
    bed = np.zeros((H, W), bool)
    # beds are a fixed size (a bed is a bed, the room just holds more of them): a row along the back wall with
    # path between, and one or two in the front corners
    plan = []
    for u in (0.17, 0.83):
        plan.append((u * W + rnd.uniform(-6, 6), 13 + rnd.uniform(-1, 2), rnd.uniform(22, 28), rnd.uniform(9, 11)))
    if W > 260:
        for u in (0.39, 0.61):
            plan.append((u * W + rnd.uniform(-4, 4), 11 + rnd.uniform(-1, 1), rnd.uniform(14, 18), rnd.uniform(7, 8)))
    fronts = [0.13, 0.87] if W > 260 else [0.13 if rnd.rand() < 0.5 else 0.87]
    for u in fronts:
        plan.append((u * W, H - 16 + rnd.uniform(-2, 1), rnd.uniform(18, 24), rnd.uniform(8, 10)))
    if W > 260 and H > 120:
        # big rooms: a round bed in the middle, the path going round it
        plan.append((W * 0.5 + rnd.uniform(-10, 10), H * 0.55, 26, 12, "centre"))
    for pl in plan:
        cx, cy, RX, RY = pl[:4]
        n = ndimage.gaussian_filter(rnd.rand(H, W), 2.0)
        n = (n - n.mean()) / (n.std() + 1e-6)
        e = ((xx + 0.5 - cx) / RX) ** 2 + ((yy + 0.5 - cy) / RY) ** 2 + n * 0.08
        b = (e < 1) & ndimage.binary_erosion(m, iterations=3)
        if b.sum() < 60:
            continue
        bed |= b
        beds.append((f.left + cx, f.bottom + H - cy, RX, RY, "centre" if len(pl) > 4 else cy < H * 0.4))
    bed = ndimage.binary_opening(bed, iterations=1)
    # loam: clods lit on their top left
    clod = ndimage.gaussian_filter(rnd.rand(H, W), 0.8)
    clod = (clod - clod.mean()) / (clod.std() + 1e-6)
    lit_c = clod - np.roll(np.roll(clod, 1, 0), 1, 1)        # lighter on a clod's top left, darker under it
    lv = 0.45 + clod * 0.16 + lit_c * 0.1
    col[bed] = ramp_pick(PAL["loam"], np.clip(lv[bed], 0, 1))
    # the cobble edge round each bed: a band of stones, the front ones showing a darker face below
    ring = ndimage.binary_dilation(bed, iterations=2) & ~bed & m
    seg = (np.floor((xx + yy * 0.6) / 3.2).astype(int) + (yy // 2)) % 2
    lab, nl = ndimage.label(ring)
    cob = np.zeros((H, W))
    for k in range(1, nl + 1):
        pass
    d_in = ndimage.distance_transform_edt(~bed)
    top = ring & (d_in <= 1.5)
    outer = ring & (d_in > 1.5)
    face = np.zeros_like(ring)
    face[1:, :] = ring[:-1, :] & ~ring[1:, :] & ~bed[1:, :] & m[1:, :]
    cv = np.where(top, 0.78, 0.5) + np.where(seg == 1, 0.1, -0.05) + mott * 0.05
    col[ring] = ramp_pick(PAL["cobble"], np.clip(cv[ring], 0, 1))
    # gaps between cobbles
    gap = ring & (((xx + (yy // 2) * 2) % 4) == 0) & (rnd.rand(H, W) < 0.6)
    col[gap] = np.array(PAL["cobble"][0], float)
    col[face] = np.array(PAL["stone"][0], float)

    # moss: in the joints and creeping onto stones, thick near the beds and along the back wall
    near_bed = ndimage.distance_transform_edt(~ring)
    from_top = yy.astype(float)
    grow = np.clip(1 - near_bed / 14.0, 0, 1) * 0.9 + np.clip(1 - from_top / 12.0, 0, 1) * 0.7
    mn = ndimage.gaussian_filter(rnd.rand(H, W), 1.3)
    mn = (mn - mn.mean()) / (mn.std() + 1e-6)
    on = m & ~bed & ~ring & (grow > 0.12) & (((joint & (mn > 0.4 - grow * 1.6)) | (mn > 1.5 - grow * 1.4)))
    on |= ring & top & (mn > 1.3 - grow)            # a little on the cobbles' tops
    mg = ndimage.gaussian_filter(mn, 0.8)
    gy2, gx2 = np.gradient(mg)
    mv = 0.5 + (-(gx2 * 0.6 + gy2 * 0.9)) * 2.5
    col[on] = ramp_pick(PAL["moss"], np.clip(mv[on], 0, 1))

    # roots from the back wall, wandering down into the beds
    for (bx, by, RX, RY, isback) in beds:
        u0 = bx - f.left
        if f.bottom + H - by > H * 0.4:          # only beds by the back wall
            continue
        for r in range(rnd.randint(2, 3)):
            x = u0 + rnd.uniform(-RX, RX) * 0.9
            y = 0.0
            dx = rnd.uniform(-0.5, 0.5)
            L = rnd.randint(10, 22)
            for s in range(L):
                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < W and 0 <= yi < H and m[yi, xi] and not bed[yi, xi]:
                    col[yi, xi] = PAL["root"][1]
                    if yi - 1 >= 0 and not bed[yi - 1, xi]:
                        col[yi - 1, xi] = PAL["root"][2]
                    if yi + 1 < H and not bed[yi + 1, xi]:
                        col[yi + 1, xi] = PAL["root"][0]
                y += 0.7
                x += dx + rnd.uniform(-0.6, 0.6)

    # a faint dust of spores round the beds
    dust = m & ~bed & (near_bed < 8) & (rnd.rand(H, W) < 0.025)
    col[dust] = col[dust] * 0.6 + np.array(PAL["puff"][3]) * 0.4

    out = A.copy()
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(m, 255, 0)
    f.im = Image.fromarray(out, "RGBA")
    R._fpx = f.im.load()
    return beds


def paint_wall(R, seed):
    """The game's back wall carries the room's shape and its stonework; its colours go onto the wall ramp, then
    moss grows along its foot and in patches, and roots and bracket fungus come out of it."""
    W_ = PAL["wall"]
    stops = [(0.0, W_[1]), (0.1, W_[2]), (0.22, W_[3]), (0.36, W_[4]), (0.55, (100, 98, 82)), (0.8, (116, 112, 94))]
    R.recolours.append((lambda d: d.kind == "wall", G.remap(G.gradient_map(stops))))
    n = P.Noise(seed)
    moss = PAL["moss"]

    def wall_moss(x, y, c):
        sp = R.wall_span(x) if False else None
        lum = sum(c) / 3
        v = n.fbm(x, y * 1.6, 5)
        foot = max(0.0, 1 - (y - R.fy1) / 9.0)               # thickest at the wall's foot
        if v + foot * 0.4 > 0.8:
            k = 3 if lum > 60 else 2 if lum > 45 else 1
            return moss[k - (1 if v < 0.82 else 0)]
        return None
    R.wall_fx.append(wall_moss)
    rnd = random.Random(seed)
    # roots and bracket fungus
    x = R.fx0 + 8
    i = 0
    while x < R.fx1 - 6:
        sp = R.wall_span(x)
        if sp:
            L = int((sp[1] - sp[0]) * rnd.uniform(0.35, 0.7))
            im = hanging_root(seed + i, L)
            R.add_image(im, x, sp[1] - im.height, kind="object", depth=R.fy1 + 60, name="WallRoot")
        x += rnd.uniform(26, 48)
        i += 1
    for j in range(3):
        x = rnd.uniform(R.fx0 + 12, R.fx1 - 12)
        sp = R.wall_span(x)
        if sp and abs(sp[0] - R.fy1) < 4:
            im, em = wall_shelf(seed * 3 + j, rnd.choice(["ochre", "mauve"]))
            R.add_image(im, x, sp[0] + rnd.uniform(1, 5), kind="object", depth=R.fy1 + 59,
                        name="WallShelf")


# ------------------------------------------------------------------ planting
def plant(R, beds, seed, big=False):
    """Each bed is planted to one of a few plans, so no two neighbours match: a tall clump with a short one beside
    it, a patch of puffballs under low caps, or several low clumps. Every bed has glowing caps at one end and the
    light they give. The middle bed of a big room gets the tallest clump in the room."""
    rnd = random.Random(seed)
    colours = ["mauve", "ochre"]
    plans = ["tall", "puffs", "low"]
    last = None

    def caps(x, y, colour, size, n):
        made = cap_cluster(rnd.randint(0, 10 ** 6), colour, big=size, n=n)
        R.stand(made[0], x, y, made[2], emit=made[1], shadow=made[3], force=True, name="RotCaps")

    def puff(x, y, r):
        p = puffball(rnd.randint(0, 10 ** 6), r)
        R.stand(p[0], x, y, p[2], shadow=p[3], force=True, name="Puffball")

    for i, (bx, by, RX, RY, isback) in enumerate(beds):
        centre = isback == "centre"
        isback = isback is True
        plan = "centre" if centre else rnd.choice([q for q in plans if q != last])
        last = plan
        colour = colours[i % 2]
        other = colours[(i + 1) % 2]
        side = 1 if rnd.random() < 0.5 else -1
        scale = 1.0 if (isback or centre) else 0.8
        if plan in ("tall", "centre"):
            caps(bx + rnd.uniform(-RX, RX) * 0.2, by + RY * 0.25, colour, int((21 if centre else rnd.randint(14, 18)) * scale), 5)
            caps(bx - side * RX * 0.45, by - RY * 0.1, other, rnd.randint(6, 8), rnd.randint(2, 3))
            puff(bx + side * RX * 0.2, by - RY * 0.45, rnd.uniform(3.4, 4.2))
        elif plan == "puffs":
            caps(bx - side * RX * 0.35, by + RY * 0.3, colour, int(rnd.randint(9, 11) * scale), 3)
            for k in range(3 if isback else 2):
                puff(bx + side * RX * (0.05 + 0.25 * k) + rnd.uniform(-2, 2), by + RY * rnd.uniform(-0.4, 0.2),
                     rnd.uniform(3.0, 4.8))
        else:
            for k in range(3 if isback else 2):
                caps(bx + (k - 1) * RX * 0.5 + rnd.uniform(-3, 3), by + RY * rnd.uniform(-0.2, 0.35),
                     colours[(i + k) % 2], rnd.randint(7, 10), rnd.randint(2, 4))
        sides = (side, -side) if centre else (side,)
        for sd in sides:
            g = glow_caps(rnd.randint(0, 10 ** 6))
            gx, gy = bx + sd * RX * 0.62, by + rnd.uniform(-RY * 0.2, RY * 0.2)
            R.stand(g[0], gx, gy, g[2], emit=g[1], shadow=g[3], force=True, name="GlowCaps")
            R.lamp(gx, gy + 3, GLOW_LIGHT, 38 if not big else 44, 0.4)


def debris(seed):
    """A few bits on the path: a fallen cap, root ends, a pebble. Flat, dark, small."""
    rnd = random.Random(seed)
    im = Image.new("RGBA", (9, 5), (0, 0, 0, 0))
    px = im.load()
    kind = rnd.choice(["cap", "root", "pebbles"])
    if kind == "cap":
        c = PAL[rnd.choice(["mauve", "ochre"])]
        for x in range(2, 7):
            px[x, 2] = c[1] + (255,)
        for x in range(3, 6):
            px[x, 1] = c[2] + (255,)
        px[2, 3], px[6, 3] = c[0] + (255,), c[0] + (255,)
    elif kind == "root":
        R_ = PAL["root"]
        y = 2
        for x in range(1, 8):
            px[x, y] = R_[1] + (255,)
            if rnd.random() < 0.3:
                y = max(1, min(3, y + rnd.choice([-1, 1])))
    else:
        for i in range(rnd.randint(2, 3)):
            x, y = rnd.randint(1, 6), rnd.randint(1, 3)
            px[x, y] = PAL["cobble"][2] + (255,)
            px[x + 1, y] = PAL["cobble"][1] + (255,)
            if y + 1 < 5:
                px[x, y + 1] = PAL["stone"][0] + (255,)
    return im


def build(room, seed, hero_at=(0, -6), big=False):
    R = G.Room(room, seed=seed)
    beds = paint_floor(R, seed)
    paint_wall(R, seed)
    plant(R, beds, seed, big)
    rnd = random.Random(seed + 99)
    for i in range(10 if big else 6):
        for _ in range(30):
            x, y = rnd.uniform(R.fx0 + 8, R.fx1 - 8), rnd.uniform(R.fy0 + 4, R.fy1 - 8)
            if R.on_floor(x, y) and R.free((x - 5, y - 2, x + 5, y + 3), R.rects + R.drects):
                im = debris(seed * 31 + i)
                R.drects.append((x - 5, y - 2, x + 5, y + 3))
                R.add_image(im, x, y - 2, kind="decal", name="Debris")
                break
    R.floor_fx += [D.edge_shade(R, k=0.5, colour=(10, 10, 12)), D.contact_shade(R, k=0.3)]
    R.dark = (0.9, 0.9, 0.92)
    R.auto_lamps = None
    if hero_at:
        R.actor(G.hero(), hero_at[0], hero_at[1], "hero")
        R.lamp(hero_at[0], hero_at[1] + 8, (255, 230, 190), 30, 0.35)
    return R


def build_big(room, seed):
    """The big copy of a room (ChaosRooms' growth, via tools/chaos/room_stretch.py), dressed the same way."""
    sys.path.insert(0, os.path.join(HERE, "..", "chaos"))
    import rot_preview as RP
    R = RP.big_room(room, seed)
    if R is None:
        return None
    R.recolours = [r for r in R.recolours]
    beds = paint_floor(R, seed)
    paint_wall(R, seed)
    plant(R, beds, seed, big=True)
    R.floor_fx += [D.edge_shade(R, k=0.5, colour=(10, 10, 12)), D.contact_shade(R, k=0.3)]
    R.dark = (0.9, 0.9, 0.92)
    R.auto_lamps = None
    R.actor(G.hero(), 0, -6, "hero")
    R.lamp(0, 2, (255, 230, 190), 30, 0.35)
    return R


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, seed in (("RoomLarge1", 41), ("RoomLarge2", 42)):
        R = build_big(name, seed)
        if R:
            R.render(scale=3).save(os.path.join(OUT, name + "_big.png"))
            print(name, "big")
    for name, seed in (("RoomLarge1", 31), ("RoomCavesLarge1", 32), ("RoomMed1", 33)):
        R = build(name, seed)
        R.render(scale=3).save(os.path.join(OUT, name + ".png"))
        print(name)


if __name__ == "__main__":
    main()
