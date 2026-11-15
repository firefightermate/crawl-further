"""Rot Gardens, the first Crawl Chaos biome: its props, floor dressing and spore effects, drawn at game scale.

The props are painted with the concept painters (tools/concepts/props.py and paint.py: small 3D shapes shaded in
hue-shifted ramps like the game's own props) and baked to sheets, each prop its own sheet with its feet at the bottom
centre of the cell. Glowing parts (gills, spots, ink, egg yolks, root tips) are baked into the colours.

    python3 tools/sprites/biome_rot.py          -> art/out_biomes/BiomeRot*.png + .json, and a board in build/
"""
import json
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "concepts"))
import paint as P  # noqa: E402
import props as Q  # noqa: E402

OUT = os.path.join(ROOT, "art", "out_biomes")

# the concept's colours (tools/concepts/ingame_biomes.py)
MAG, TEALG = (150, 62, 128), (110, 255, 220)
OCH, AMBG = (176, 104, 60), (255, 196, 96)
PALE, BLUEG = (214, 210, 222), (150, 200, 255)
STEM = (160, 146, 144)
SPORE = (150, 214, 160)
SPORE_LIGHT = (196, 255, 214)
SPORE_DARK = (70, 120, 96)


def bake(im, em, k=0.85):
    """Glow baked into the colours: emissive pixels pull the sprite toward their colour."""
    if em is None:
        return im
    im = im.copy()
    a, e = im.load(), em.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            g = e[x, y]
            if g[3] == 0:
                continue
            t = k * g[3] / 255
            p = a[x, y]
            if p[3] == 0:
                a[x, y] = g[:3] + (int(g[3] * 0.8),)
            else:
                a[x, y] = tuple(int(p[i] + (g[i] - p[i]) * t) for i in range(3)) + (p[3],)
    return im


def cell_sheet(name, frames, anims, pad=1, feet=True):
    """Frames of one size class into a sheet: cells as big as the largest frame plus padding, each frame placed with
    its bottom centre on the cell's bottom centre (feet) or centred."""
    cw = max(f.size[0] for f in frames) + pad * 2
    ch = max(f.size[1] for f in frames) + pad * 2
    cw += cw % 2
    cols = min(len(frames), 8)
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGBA", (cw * cols, ch * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        cx, cy = (i % cols) * cw, (i // cols) * ch
        x = cx + (cw - f.size[0]) // 2
        y = cy + (ch - f.size[1] - pad) if feet else cy + (ch - f.size[1]) // 2
        sheet.alpha_composite(f, (x, y))
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, name + ".png"))
    with open(os.path.join(OUT, name + ".json"), "w") as fh:
        json.dump({"cellW": cw, "cellH": ch, "cols": cols, "anims": anims}, fh)
    return sheet, (cw, ch)


def still(name, im, extra=None):
    anims = [{"name": "Idle", "frames": [0], "durations": [1.0]}]
    frames = [im]
    if extra:
        for an, fr, du in extra:
            anims.append({"name": an, "frames": list(range(len(frames), len(frames) + len(fr))), "durations": du})
            frames += fr
    return cell_sheet(name, frames, anims)


def squash(im, k):
    """A hit wobble frame: squashed down and out from the feet."""
    w, h = im.size
    nw, nh = max(1, int(round(w * (1 + k * 0.5)))), max(1, int(round(h * (1 - k))))
    return im.resize((nw, nh), Image.NEAREST)


# ------------------------------------------------------------------ props
def props():
    made = {}
    def cap(name, h, c, g, kind, seed):
        im, em, foot, shadow = Q.giant_cap(h, c, g, stem=STEM, seed=seed, kind=kind)
        im = bake(im, em)
        made[name] = (im, foot)
        still(name, im, [("Hit", [squash(im, 0.08), squash(im, -0.04)], [0.06, 0.06])])
    cap("BiomeRotCapParasol", 34, MAG, TEALG, "parasol", 3)
    cap("BiomeRotCapParasolSmall", 22, MAG, TEALG, "parasol", 11)
    cap("BiomeRotCapBell", 26, OCH, AMBG, "bell", 5)
    cap("BiomeRotCapShelf", 20, OCH, AMBG, "shelf", 8)
    for i, h in enumerate((20, 15)):
        im, em, foot, sh = Q.ink_cap(h, PALE, BLUEG, seed=i + 2)
        im = bake(im, em)
        made["BiomeRotInkCaps%d" % (i + 1)] = (im, foot)
        still("BiomeRotInkCaps%d" % (i + 1), im)
    for i, r in enumerate((6, 4)):
        im, em, foot, sh = Q.puffball(r, seed=i + 4)
        made["BiomeRotPuffball%d" % (i + 1)] = (im, foot)
        still("BiomeRotPuffball%d" % (i + 1), im, [("Hit", [squash(im, 0.12), squash(im, -0.06)], [0.05, 0.06])])
    for i, (L, c, f) in enumerate(((44, (86, 66, 62), MAG), (32, (80, 64, 58), OCH))):
        im, em, foot, sh = Q.rotten_log(L, colour=c, cap=f, glow=1, seed=9 - i * 5)
        im = bake(im, em, 0.6)
        made["BiomeRotLog%d" % (i + 1)] = (im, foot)
        still("BiomeRotLog%d" % (i + 1), im)
    for i in range(2):
        im, em, foot, sh = Q.pod_cluster(seed=i + 3)
        im = bake(im, em, 0.7)
        made["BiomeRotEggSacs%d" % (i + 1)] = (im, foot)
        still("BiomeRotEggSacs%d" % (i + 1), im)
    for i in range(2):
        im, em = Q.wall_roots(18, 26, colour=(96, 74, 86), seed=i + 4, tips=TEALG, moss=(60, 96, 74))
        im = bake(P.trim(im, em)[0], P.trim(im, em)[1])
        made["BiomeRotRoots%d" % (i + 1)] = (im, None)
        still("BiomeRotRoots%d" % (i + 1), im)
    # floor dressing: little caps, mycelium mats, moss
    for i, (c, g) in enumerate(((MAG, TEALG), (OCH, AMBG), (MAG, TEALG))):
        im, em = Q.pins(c, g, seed=i * 3 + 1, count=6 + i, spread=6 + i)
        im = bake(*P.trim(im, em))
        made["BiomeRotPins%d" % (i + 1)] = (im, None)
        still("BiomeRotPins%d" % (i + 1), im)
    for i, (w, h) in enumerate(((40, 16), (28, 12))):
        im, em = Q.mycelium(w, h, seed=i + 7, glow=TEALG)
        im = bake(im, em)
        made["BiomeRotMycelium%d" % (i + 1)] = (im, None)
        still("BiomeRotMycelium%d" % (i + 1), im)
    for i, (w, h) in enumerate(((30, 14), (20, 10))):
        im = moss(w, h, seed=i + 2)
        made["BiomeRotMoss%d" % (i + 1)] = (im, None)
        still("BiomeRotMoss%d" % (i + 1), im)
    return made


def moss(w, h, seed=0):
    """A soft patch of moss for the floor: an uneven blot, darker at the edge, lit specks inside."""
    n = P.Noise(seed)
    rnd = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    tones = P.ramp((62, 94, 74), n=5, dark=0.5, light=1.25)
    for y in range(h):
        for x in range(w):
            d = ((x + 0.5 - w / 2) / (w / 2)) ** 2 + ((y + 0.5 - h / 2) / (h / 2)) ** 2
            v = d + (n.fbm(x, y, 4) - 0.5) * 0.9
            if v < 0.9:
                k = 1 if v > 0.7 else (2 if v > 0.35 else 3)
                if n.v(x * 2.3, y * 2.3, 1) > 0.8:
                    k = 4
                px[x, y] = tones[k] + (200 if v > 0.7 else 235,)
    return im


# ------------------------------------------------------------------ spores
def blob(w, h, parts, rnd, colour, alpha, speck, specks):
    """A soft cloud: overlapping round puffs in two alpha steps, spore specks in it."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            best = 0.0
            for (cx, cy, r) in parts:
                d = math.hypot((x + 0.5 - cx) / r, (y + 0.5 - cy) / (r * 0.75))
                best = max(best, 1 - d)
            if best > 0:
                k = 0 if best < 0.3 else 1
                c = SPORE_DARK if k == 0 else colour
                a = int(alpha * (0.55 if k == 0 else 1.0))
                px[x, y] = c + (a,)
    for _ in range(specks):
        x, y = rnd.randrange(w), rnd.randrange(h)
        if px[x, y][3] > 0:
            px[x, y] = speck + (230,)
    return im


def spores():
    rnd = random.Random(5)
    # the burst: a puff thrown out from the cap, swelling then thinning
    frames = []
    for i, s in enumerate((0.35, 0.6, 0.85, 1.0, 1.08, 1.12, 1.15)):
        w, h = 44, 32
        parts = [(w / 2 + rnd.uniform(-3, 3) * s, h * 0.62 - s * 4 + rnd.uniform(-1, 1), 9 * s + rnd.uniform(-1, 1)) for _ in range(5)]
        parts += [(w / 2 + math.cos(a) * 11 * s, h * 0.62 + math.sin(a) * 6 * s, 6 * s) for a in (0.3, 2.0, 3.6, 5.2)]
        alpha = int(200 * (1.0 if i < 4 else 0.75 - (i - 4) * 0.18))
        frames.append(blob(w, h, parts, rnd, SPORE, alpha, SPORE_LIGHT, 18 + i * 3))
    cell_sheet("BiomeRotBurst", frames, [{"name": "Burst", "frames": list(range(7)),
                                           "durations": [0.04, 0.05, 0.06, 0.08, 0.1, 0.12, 0.14]}], feet=False)
    # the lingering cloud a burst leaves: four slow frames that loop
    frames = []
    base = [(20 + rnd.uniform(-6, 6), 12 + rnd.uniform(-2, 2), rnd.uniform(6, 9)) for _ in range(6)]
    for i in range(4):
        parts = [(x + math.sin(i * 1.57 + k) * 1.2, y + math.cos(i * 1.57 + k) * 0.6, r) for k, (x, y, r) in enumerate(base)]
        frames.append(blob(40, 24, parts, rnd, SPORE, 120, SPORE_LIGHT, 14))
    cell_sheet("BiomeRotCloud", frames, [{"name": "Loop", "frames": [0, 1, 2, 3], "durations": [0.18] * 4}], feet=False)
    # the drift: a long low bank of spores that crosses the room
    frames = []
    base = [(10 + k * 7 + rnd.uniform(-2, 2), 14 + rnd.uniform(-3, 3), rnd.uniform(6, 10)) for k in range(6)]
    for i in range(6):
        parts = [(x + math.sin(i * 1.05 + k * 1.3) * 1.5, y + math.cos(i * 1.05 + k) * 0.8, r) for k, (x, y, r) in enumerate(base)]
        frames.append(blob(58, 28, parts, rnd, SPORE, 105, SPORE_LIGHT, 22))
    cell_sheet("BiomeRotDrift", frames, [{"name": "Loop", "frames": list(range(6)), "durations": [0.16] * 6}], feet=False)


def board(made):
    """Everything on one dark board, for looking at (not shipped)."""
    names = sorted(f for f in os.listdir(OUT) if f.endswith(".png"))
    ims = [Image.open(os.path.join(OUT, f)) for f in names]
    W = 8 + sum(i.size[0] + 8 for i in ims[:10])
    rows, x, y, rowh = [], 8, 8, 0
    out = Image.new("RGBA", (420, 260), (40, 36, 44, 255))
    for im in ims:
        if x + im.size[0] > 412:
            x, y = 8, y + rowh + 8
            rowh = 0
        out.alpha_composite(im, (x, y))
        x += im.size[0] + 8
        rowh = max(rowh, im.size[1])
    out = out.crop((0, 0, 420, min(260, y + rowh + 8)))
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    out.resize((out.size[0] * 3, out.size[1] * 3), Image.NEAREST).save(os.path.join(ROOT, "build", "biome_rot_board.png"))


if __name__ == "__main__":
    made = props()
    spores()
    board(made)
    print("wrote", len([f for f in os.listdir(OUT) if f.endswith(".png")]), "sheets to", OUT)
