"""GroundSkin: ground effects made out of the floor they lie on.

A pool, a frozen patch, a puddle of wax or a scorch is drawn by changing the floor's own pixels under it, so the
stone or dirt shows through and the effect sits in the map instead of on top of it like a sticker. The effect's
art gives only its shape (the alpha of its frames); the look comes from the floor and the material.

This is the reference the C# port follows (Core/Art/GroundSkin.cs): same steps, same numbers.

  shape   the art's alpha, made ragged by the floor: liquids run into the floor's dark cracks first and stop at its
          raised bits, so every pool's edge follows the stones it lies on
  depth   distance from the edge, inside the shape (pixels)
  look    per material, from the floor pixel and the depth:
          wet     floor darkened and tinted, deeper toward the middle, a dark meniscus at the edge, a lit lip on the
                  top-left inside edge, sparse glints where the floor's own texture peaks
          frozen  floor whitened and cooled at low contrast (the stone still shows), lit rim, thin cracks, glints
          thick   wax, resin, glue, tar: mostly the material, shaded like a low dome lit from the top left, with a
                  little of the floor's texture through it and a darker rim
          scorch  floor burnt toward black-brown, strongest at the middle, a few embers
          growth  moss, mould: the floor's raised pixels turn the material's colour, the low ones stay
          carved  cracks and quake rings: the floor darkened along the line with a lit lip on its lower edge

Concept and checking tool: nothing it makes ships.
    python3 tools/chaos/groundskin.py   -> build/groundskin/board.png
"""
import json
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_closing, binary_opening, distance_transform_edt, gaussian_filter, uniform_filter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "concepts"))
import ingame as G  # noqa: E402

OUT = os.path.join(G.ROOT, "build", "groundskin")

# materials: colours in Crawl's muted range, each with its one accent at most
MATERIALS = {
    "water":  dict(kind="wet", tint=(46, 78, 92), deep=0.55, gloss=(150, 190, 196)),
    "brine":  dict(kind="wet", tint=(40, 84, 86), deep=0.6, gloss=(140, 196, 186)),
    "acid":   dict(kind="wet", tint=(92, 112, 40), deep=0.5, gloss=(196, 214, 110)),
    "bile":   dict(kind="wet", tint=(104, 104, 44), deep=0.5, gloss=(190, 190, 96)),
    "blood":  dict(kind="wet", tint=(88, 26, 30), deep=0.6, gloss=(170, 90, 86)),
    "goo":    dict(kind="wet", tint=(64, 92, 58), deep=0.55, gloss=(150, 196, 120)),
    "ice":    dict(kind="frozen", tint=(178, 214, 226), rim=(226, 242, 246), crack=(96, 132, 156)),
    "wax":    dict(kind="thick", base=(196, 176, 140), dark=(120, 96, 70), lite=(232, 218, 186), through=0.25),
    "resin":  dict(kind="thick", base=(150, 98, 40), dark=(84, 52, 24), lite=(214, 160, 80), through=0.35),
    "glue":   dict(kind="thick", base=(176, 168, 140), dark=(104, 98, 80), lite=(220, 214, 190), through=0.4),
    "tar":    dict(kind="thick", base=(34, 30, 34), dark=(16, 14, 18), lite=(96, 92, 100), through=0.15),
    "scorch": dict(kind="scorch", burnt=(30, 22, 20), ember=(226, 120, 52)),
    "moss":   dict(kind="growth", tint=(70, 96, 64), tint2=(96, 124, 80)),
    "crack":  dict(kind="carved", depth=0.45, lip=1.25),
}


def lum(a):
    return a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11


def skin(floor_rgb, mask, material, seed=1, raggedness=1.0):
    """floor_rgb: HxWx3 floats 0..255 (the floor under the effect); mask: HxW 0..1 (the art's alpha, scaled to the
    floor). Returns HxWx4 uint8, alpha 0 outside the effect."""
    m = MATERIALS[material]
    rnd = np.random.RandomState(seed)
    L = lum(floor_rgb)
    hp = L - uniform_filter(L, 5)                      # the floor's own texture: + raised, - crevice
    hpn = hp / (np.abs(hp).max() + 1e-6)
    hps = gaussian_filter(hpn, 1.0)                    # its larger shapes, for edges (single pixels would make spikes)
    hps = hps / (np.abs(hps).max() + 1e-6)
    BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    inside = mask > 0.5
    sd = distance_transform_edt(inside) - distance_transform_edt(~inside)   # signed distance to the art's edge
    k = m["kind"]
    if k in ("wet", "thick", "frozen", "growth"):
        # liquids and growths take the floor's shape: in where the floor dips, out where it rises
        sd = sd - hps * 2.2 * raggedness
    shape = sd > 0
    # clean pixel-art edges: no lone pixels, no one-pixel spikes or bites
    shape = binary_closing(binary_opening(shape, np.ones((2, 2))), np.ones((2, 2))) if k != "carved" else shape
    depth = np.where(shape, distance_transform_edt(shape), 0.0)
    out = np.zeros(floor_rgb.shape[:2] + (4,), float)
    f = floor_rgb.astype(float)
    H, W = mask.shape
    yy, xx = np.mgrid[0:H, 0:W]
    # direction to the shape's edge, for lit lips: the top-left inside edge catches light
    gy, gx = np.gradient(gaussian_filter(depth, 0.8))
    toplight = np.clip(-gx * 0.6 + gy * 0.8, 0, None)      # rises toward the top-left edge (y down)

    if k == "wet":
        t = np.clip(depth / 3.0, 0, 1)[..., None]
        tint = np.array(m["tint"], float)
        lf = np.clip(L / (L.mean() + 1e-6), 0.6, 1.4)[..., None]
        # the floor seen through the liquid: its own light and dark kept, coloured and darkened by depth
        c = tint * lf * (1.0 - m["deep"] * 0.3 * t) * 0.85 + f * 0.15
        c = f * (1 - (0.55 + 0.4 * t)) + c * (0.55 + 0.4 * t)
        below = np.zeros_like(shape)
        below[:-1, :] = shape[:-1, :] & ~shape[1:, :]       # the near (lower) edge: a darker meniscus
        c[below] *= 0.78
        above = np.zeros_like(shape)
        above[1:, :] = shape[1:, :] & ~shape[:-1, :]        # the far (upper) edge catches the light
        c[above] = c[above] * 0.55 + np.array(m["gloss"]) * 0.45
        # a few short horizontal glints on the surface
        for _ in range(max(1, int(shape.sum() / 120))):
            pts = np.argwhere(depth > 2.5)
            if not len(pts):
                break
            y, x = pts[rnd.randint(len(pts))]
            for dx in range(rnd.randint(2, 4)):
                if x + dx < W and depth[y, x + dx] > 1.5:
                    c[y, x + dx] = c[y, x + dx] * 0.35 + np.array(m["gloss"]) * 0.65
        out[..., :3] = c
    elif k == "frozen":
        tint = np.array(m["tint"], float)
        lo = L.mean()
        # frozen over: the floor still shows, paler, cooler and flatter, as if under a sheet of ice
        # the floor under a sheet of ice: still there, lighter and cooler, its contrast kept
        c = f * 0.55 + tint * 0.45 + 14.0
        above = np.zeros_like(shape)
        above[1:, :] = shape[1:, :] & ~shape[:-1, :]
        left = np.zeros_like(shape)
        left[:, 1:] = shape[:, 1:] & ~shape[:, :-1]
        c[above] = np.array(m["rim"], float)                 # the lit far edge
        c[left & ~above] = c[left & ~above] * 0.5 + np.array(m["rim"], float) * 0.5
        below = np.zeros_like(shape)
        below[:-1, :] = shape[:-1, :] & ~shape[1:, :]
        c[below] = c[below] * 0.72                           # the ice's thickness on the near edge
        crack = np.zeros((H, W), bool)
        pts = np.argwhere(depth > 2.5)
        for i in range(max(1, int(shape.sum() / 160))):
            if not len(pts):
                break
            y, x = pts[rnd.randint(len(pts))]
            ang = rnd.choice([0.0, 0.5, -0.5, 2.6, -2.6])
            for seg in range(rnd.randint(2, 3)):
                ln = rnd.randint(3, 7)
                for st in range(ln):
                    y2, x2 = int(round(y + np.sin(ang) * st * 0.5)), int(round(x + np.cos(ang) * st))
                    if 0 <= y2 < H and 0 <= x2 < W and depth[y2, x2] > 1.5:
                        crack[y2, x2] = True
                y, x = y + np.sin(ang) * ln * 0.5, x + np.cos(ang) * ln
                ang += rnd.uniform(-0.8, 0.8)
        c[crack] = np.array(m["crack"], float)
        hl = np.zeros_like(crack)
        hl[1:, :] = crack[:-1, :] & ~crack[1:, :]
        c[hl & shape] = c[hl & shape] * 0.5 + np.array(m["rim"], float) * 0.5   # a crack's lit lower side
        for _ in range(max(1, int(shape.sum() / 200))):     # glints: short bright dashes near the top-left
            if not len(pts):
                break
            y, x = pts[rnd.randint(len(pts))]
            if toplight[y, x] >= 0 or rnd.rand() < 0.5:
                for dx in range(2):
                    if x + dx < W and shape[y, x + dx]:
                        c[y, x + dx] = np.array(m["rim"], float)
        out[..., :3] = c
    elif k == "thick":
        base, dark, lite = (np.array(m[n], float) for n in ("base", "dark", "lite"))
        dome = np.clip(depth / max(2.0, depth.max() * 0.7), 0, 1)
        shade = dome * 0.7 + np.clip(toplight * 3, 0, 0.6)
        c = dark[None, None] * (1 - shade[..., None]) + base[None, None] * shade[..., None]
        hi = shape & (depth > 1.5) & (toplight > 0.1)
        c[hi] = c[hi] * 0.4 + lite * 0.6
        c = c + ((L - L.mean()) * m["through"])[..., None]  # the floor's texture under a thin film
        rim = (depth > 0) & (depth <= 1)
        c[rim] = c[rim] * 0.75
        out[..., :3] = c
    elif k == "scorch":
        n = gaussian_filter(rnd.rand(H, W), 1.5)
        t = np.clip(sd / 5.0 + (n - 0.5) * 1.2, 0, 1)
        # three burn levels, stepped with an ordered dither like the game's own shading
        th = BAYER[yy % 4, xx % 4]
        lvl = np.floor(t * 3 + th * 0.99) / 3.0
        shape = lvl > 0
        burnt = np.array(m["burnt"], float)
        c = f * (1 - 0.8 * lvl[..., None]) + burnt * 0.8 * lvl[..., None]
        ember = shape & (lvl >= 0.99) & (rnd.rand(H, W) < 0.03)
        c[ember] = np.array(m["ember"], float)
        out[..., :3] = c
        depth = lvl * 3
    elif k == "growth":
        raised = hpn > -0.1
        n = gaussian_filter(rnd.rand(H, W), 1.0)
        on = shape & (raised | (depth > 2.5)) & (n > 0.42 - np.clip(depth, 0, 3) * 0.06)
        lf = (L / (L.mean() + 1e-6))[..., None]
        c = f.copy()
        t1, t2 = np.array(m["tint"], float), np.array(m["tint2"], float)
        pick = (hpn > 0.35)[..., None]
        col = np.where(pick, t2, t1) * lf
        c[on] = c[on] * 0.25 + col[on] * 0.75
        out[..., :3] = c
        shape = on
    elif k == "carved":
        line = mask > 0.5
        c = f.copy()
        c[line] = f[line] * m["depth"]
        below = np.zeros_like(line)
        below[1:, :] = line[:-1, :] & ~line[1:, :]          # the lower edge of the cut catches light
        c[below] = np.clip(f[below] * m["lip"], 0, 255)
        out[..., :3] = c
        shape = line | below
    out[..., 3] = np.where(shape, 255, 0)
    out[..., :3] = np.clip(out[..., :3], 0, 255)
    return out.astype(np.uint8)


# ---------------------------------------------------------------------------- board

def art_mask(sheet, scale=1.0):
    """The biggest frame's alpha of one of the mod's own sheets: the effect's shape."""
    for d in sorted(os.listdir(os.path.join(G.ROOT, "art"))):
        p = os.path.join(G.ROOT, "art", d, sheet + ".json")
        if os.path.exists(p):
            meta = json.load(open(p))
            im = Image.open(p[:-5] + ".png").convert("RGBA")
            cw, ch, cols = meta["cellW"], meta["cellH"], meta["cols"]
            best = None
            for i in range(cols * (im.height // ch)):
                cell = im.crop(((i % cols) * cw, (i // cols) * ch, (i % cols) * cw + cw, (i // cols) * ch + ch))
                bb = cell.getbbox()
                if bb and (best is None or (bb[2] - bb[0]) * (bb[3] - bb[1]) > best[0]):
                    best = ((bb[2] - bb[0]) * (bb[3] - bb[1]), cell.crop(bb))
            return best[1] if best else None
    return None


def ellipse(w, h, wobble=0.12, seed=1):
    rnd = random.Random(seed)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    pts = []
    for i in range(28):
        a = i / 28 * 2 * np.pi
        r = 1 + rnd.uniform(-wobble, wobble)
        pts.append((w / 2 + np.cos(a) * (w / 2 - 1) * r, h / 2 + np.sin(a) * (h / 2 - 1) * r))
    d.polygon(pts, fill=255)
    return im


def ring(w, h, seed=1):
    rnd = random.Random(seed)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for i in range(18):
        a0 = i / 18 * 2 * np.pi + rnd.uniform(-0.1, 0.1)
        a1 = a0 + rnd.uniform(0.15, 0.3)
        r = rnd.uniform(0.85, 1.0)
        x0, y0 = w / 2 + np.cos(a0) * (w / 2 - 2) * r, h / 2 + np.sin(a0) * (h / 2 - 2) * r
        x1, y1 = w / 2 + np.cos(a1) * (w / 2 - 2) * r, h / 2 + np.sin(a1) * (h / 2 - 2) * r
        d.line((x0, y0, x1, y1), fill=255)
        if rnd.random() < 0.5:   # a short radial crack off the ring
            d.line((x0, y0, x0 - (x0 - w / 2) * 0.18, y0 - (y0 - h / 2) * 0.18), fill=255)
    return im


def on_floor(floor, cx, cy, shape, material, seed=1):
    w, h = shape.size
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    region = floor.crop((x0 - 3, y0 - 3, x0 + w + 3, y0 + h + 3))
    f = np.asarray(region.convert("RGB"), float)
    mk = np.zeros(f.shape[:2])
    mk[3:3 + h, 3:3 + w] = np.asarray(shape, float) / 255.0
    s = Image.fromarray(skin(f, mk, material, seed), "RGBA")
    out = floor.copy()
    out.alpha_composite(s, (x0 - 3, y0 - 3))
    return out


def room_shot(path):
    """One Caves room with the old art dropped on its floor, and the same spots done with GroundSkin."""
    spots = [(-70, -14, "FxBelTide", "brine", (40, 16)), (40, -26, "FxCommonIndIce", "ice", (40, 16)),
             (-10, 6, "FxEmberPatch", "scorch", (30, 13)), (70, 10, "FxZhkAcidPoolWide", "acid", (34, 14)),
             (-60, 22, "FxWaxPuddle", "wax", (24, 10))]
    shots = []
    for new in (False, True):
        R = G.Room("RoomLarge1", seed=5)
        R.fill("Caves", scale=0.8)
        fl = R.floor.im.convert("RGBA")
        for i, (x, y, sheet, mat, (w, h)) in enumerate(spots):
            cx, cy = int(x - R.floor.left), int(R.floor.bottom + fl.height - y)
            if new:
                fl = on_floor(fl, cx, cy, ellipse(w, h, seed=i + 3), mat, seed=i + 7)
            else:
                old = art_mask(sheet)
                if old is not None:
                    fl.alpha_composite(old, (cx - old.width // 2, cy - old.height // 2))
        R.floor.im = fl
        R._fpx = fl.load()
        shots.append(R.render(scale=3))
    w = max(s.width for s in shots)
    out = Image.new("RGBA", (w, shots[0].height + shots[1].height + 8), (24, 20, 26, 255))
    out.paste(shots[0], (0, 0))
    out.paste(shots[1], (0, shots[0].height + 8))
    out.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    floors = {}
    for env, room in (("Caves", "RoomCavesLarge1"), ("Crypt", "RoomCryptLarge1"), ("Mines", "RoomMinesLarge1")):
        floors[env] = G.Room(room, seed=1).floor.im.convert("RGBA")
    # (label, old sheet, material, shape size)
    rows = [("Tide pool", "FxBelTide", "brine", (40, 16)),
            ("Acid pool", "FxZhkAcidPoolWide", "acid", (40, 16)),
            ("Bile puddle", "FxSylBilePuddle", "bile", (30, 12)),
            ("Goo puddle", "FxGooPuddle", "goo", (30, 12)),
            ("Tar", "FxObjTar", "tar", (32, 13)),
            ("Wax puddle", "FxWaxPuddle", "wax", (26, 10)),
            ("Resin", "FxZhkResin", "resin", (26, 11)),
            ("Glue field", "FxZhkGlueField", "glue", (30, 12)),
            ("Ice", "FxCommonIndIce", "ice", (40, 16)),
            ("Ember patch", "FxEmberPatch", "scorch", (30, 13)),
            ("Moss", "BiomeRotMoss1", "moss", (36, 15)),
            ("Quake ring", "FxBelAnchorQuake", "crack", (46, 18))]
    S = 3
    cw, ch = 64, 30
    board = Image.new("RGBA", (S * (cw * 4) + 40, S * ch * len(rows) + 60), (24, 20, 26, 255))
    dr = ImageDraw.Draw(board)
    for j, h in enumerate(("Old (the art as it is)", "GroundSkin: Caves", "GroundSkin: Crypt", "GroundSkin: Mines")):
        dr.text((10 + j * S * cw, 8), h, fill=(230, 226, 232, 255))
    for i, (label, sheet, mat, (w, h)) in enumerate(rows):
        y = 30 + i * S * ch
        fl = floors["Caves"]
        cx, cy = fl.width // 2, fl.height // 2
        base = fl.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2)).copy()
        old = art_mask(sheet)
        if old is not None:
            base.alpha_composite(old, ((cw - old.width) // 2, (ch - old.height) // 2))
        board.paste(base.resize((cw * S, ch * S), Image.NEAREST), (10, y))
        dr.text((14, y + 2), label, fill=(255, 255, 255, 255))
        shape = ring(w, h, seed=i) if mat == "crack" else ellipse(w, h, seed=i)
        for k, env in enumerate(("Caves", "Crypt", "Mines")):
            fl = floors[env]
            cx, cy = fl.width // 2, fl.height // 2
            done = on_floor(fl, cx, cy, shape, mat, seed=i + 1)
            crop = done.crop((cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2))
            board.paste(crop.resize((cw * S, ch * S), Image.NEAREST), (10 + (k + 1) * S * cw, y))
    board.save(os.path.join(OUT, "board.png"))
    room_shot(os.path.join(OUT, "room.png"))
    print("->", os.path.join(OUT, "board.png"), board.size)


if __name__ == "__main__":
    main()
