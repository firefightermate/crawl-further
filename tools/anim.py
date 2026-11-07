"""Procedural pixel-art animation + sheet packer for Crawl mod monsters.

A monster is authored as one or more hand-made key sprites (char grids with a shared palette).
This module derives the remaining frames with pixel-exact transforms (shifts, shears, leg swaps,
flame flicker, snuff-out on death, stone statue) and packs everything into one PNG grid + JSON
manifest that the C# SpriteSheets loads.
"""
import json, math, os
from PIL import Image

PALETTE = {
    '.': None,
    'K': (0x1e, 0x1a, 0x1c), 'k': (0x3b, 0x2f, 0x2c), 'g': (0x5a, 0x4a, 0x42), 'h': (0x7a, 0x65, 0x53),
    'i': (0x9a, 0x84, 0x68),
    'w': (0xb8, 0xa2, 0x76), 'W': (0xdc, 0xc9, 0x98), 'X': (0xf4, 0xea, 0xc6),
    'o': (0xc8, 0x55, 0x1a), 'O': (0xf2, 0x8a, 0x26), 'Y': (0xff, 0xd8, 0x5e), 'y': (0xff, 0xf3, 0xb8),
    'r': (0xa8, 0x1e, 0x1a), 'R': (0xff, 0x46, 0x2a),
    'b': (0x3d, 0x6f, 0xb0), 'B': (0x8c, 0xc8, 0xff), 'c': (0xd8, 0xf2, 0xff),
    'p': (0x5e, 0x24, 0x26), 'P': (0x8a, 0x34, 0x30),
    's': (0x44, 0x40, 0x48), 'S': (0x6e, 0x6a, 0x74), 'm': (0x2a, 0x26, 0x30),
    'a': (0x8e, 0x3b, 0x1e), 'A': (0x6a, 0x5a, 0x2e), 'e': (0x9c, 0x8a, 0x4a),
    # added for the Ossivar / Sylvene / Umbrael packs
    'G': (0x7f, 0xd3, 0x6a), 'v': (0x3f, 0x7a, 0x3a), 'V': (0x5a, 0xa4, 0x4a),
    'F': (0xe5, 0x8f, 0xb0), 'n': (0x5b, 0x2f, 0x6e), 'N': (0x9a, 0x5c, 0xbf), 'q': (0x2b, 0x1a, 0x36),
    'u': (0xc9, 0xd2, 0xe6), 'U': (0x8a, 0x93, 0xa8), 't': (0x4e, 0x3a, 0x2a), 'T': (0x6b, 0x52, 0x38),
}
FLAME = set('oOYy')
STONE = [(0x3a, 0x3a, 0x40), (0x58, 0x58, 0x60), (0x7a, 0x7a, 0x82), (0x9c, 0x9c, 0xa4), (0xbe, 0xbe, 0xc4)]


class Spr:
    """Sparse pixel sprite: dict (x,y) -> palette char. Origin = feet point (x=0 centre, y=0 ground)."""

    def __init__(self, px=None):
        self.px = dict(px or {})

    @staticmethod
    def parse(text, feet_x=None):
        rows = [r for r in text.strip('\n').split('\n')]
        rows = [r.rstrip() for r in rows]
        h = len(rows)
        w = max(len(r) for r in rows)
        fx = w // 2 if feet_x is None else feet_x
        px = {}
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != '.' and c != ' ':
                    px[(x - fx, y - (h - 1))] = c
        return Spr(px)

    def copy(self):
        return Spr(self.px)

    def bbox(self):
        xs = [p[0] for p in self.px]; ys = [p[1] for p in self.px]
        return min(xs), min(ys), max(xs), max(ys)

    def shift(self, dx, dy, pred=None):
        out = {}
        for (x, y), c in self.px.items():
            if pred is None or pred(x, y, c):
                out[(x + dx, y + dy)] = c
        for (x, y), c in self.px.items():
            if pred is not None and not pred(x, y, c):
                out.setdefault((x, y), c)
        return Spr(out)

    def region_shift(self, pred, dx, dy):
        """Move only pixels matching pred; they draw over the rest."""
        keep = {k: v for k, v in self.px.items() if not pred(k[0], k[1], v)}
        mov = {(k[0] + dx, k[1] + dy): v for k, v in self.px.items() if pred(k[0], k[1], v)}
        keep.update(mov)
        return Spr(keep)

    def shear(self, k, y_pivot=0, pred=None):
        """Horizontal shear: rows above pivot move by round(k * height)."""
        out = {}
        for (x, y), c in self.px.items():
            if pred is None or pred(x, y, c):
                dx = int(round(k * (y_pivot - y)))
                out[(x + dx, y)] = c
            else:
                out.setdefault((x, y), c)
        return Spr(out)

    def squash(self, sy, y_pivot=0):
        """Vertical scale about the ground line (nearest neighbour)."""
        b = self.bbox()
        out = {}
        for y in range(b[1] - 2, 1):
            src_y = int(round(y_pivot + (y - y_pivot) / sy))
            for x in range(b[0] - 1, b[2] + 2):
                c = self.px.get((x, src_y))
                if c: out[(x, y)] = c
        return Spr(out)

    def stretch_x(self, sx, x_pivot=0):
        b = self.bbox()
        out = {}
        for x in range(int(b[0] * sx) - 2, int(b[2] * sx) + 3):
            src_x = int(round(x_pivot + (x - x_pivot) / sx))
            for y in range(b[1], b[3] + 1):
                c = self.px.get((src_x, y))
                if c: out[(x, y)] = c
        return Spr(out)

    def recolor(self, mapping):
        return Spr({k: mapping.get(v, v) for k, v in self.px.items()})

    def over(self, other):
        o = dict(self.px); o.update(other.px); return Spr(o)

    def flame_flicker(self, phase):
        """Shift flame pixels sideways / grow them a little to make candle flames dance."""
        out = dict(self.px)
        fl = {k: v for k, v in self.px.items() if v in FLAME}
        if not fl: return self.copy()
        top = min(k[1] for k in fl)
        for k in fl: out.pop(k, None)
        for (x, y), c in fl.items():
            dx = 0
            if y <= top + 1: dx = [0, 1, 0, -1][phase % 4]
            out[(x + dx, y)] = c
        if phase % 2 == 1:  # brighter core
            out = {k: ('Y' if v == 'O' and (k[0] + k[1] + phase) % 3 == 0 else v) for k, v in out.items()}
        return Spr(out)

    def snuff(self):
        """Death: flames go out to a wisp of smoke."""
        return Spr({k: ('s' if v in 'oO' else 'S' if v in 'Yy' else v) for k, v in self.px.items()})

    def flare(self, amount=1):
        """Special/rage: flames grow upward and brighten."""
        out = dict(self.px)
        for (x, y), c in self.px.items():
            if c in FLAME:
                for i in range(1, amount + 1):
                    out.setdefault((x, y - i), 'O' if i < amount else 'o')
        return Spr({k: ('Y' if v == 'O' else 'y' if v == 'Y' else v) for k, v in out.items()})

    def rotate_down(self):
        """Lie the sprite on its back (rotate 90 degrees CW around the feet), used for death frames."""
        out = {}
        for (x, y), c in self.px.items():
            out[(-y, x // 2)] = c  # flatten a little: corpses read lower and longer
        s = Spr(out)
        b = s.bbox()
        return s.shift(-((b[0] + b[2]) // 2), -b[3])

    def stone(self):
        def lum(c):
            r, g, b = PALETTE[c]
            return 0.3 * r + 0.59 * g + 0.11 * b
        out = {}
        for k, c in self.px.items():
            l = lum(c)
            out[k] = STONE[min(4, int(l / 52))]
        return SprRGB(out)

    def to_rgba(self):
        return {k: PALETTE[c] + (255,) for k, c in self.px.items() if PALETTE.get(c)}


class SprRGB(Spr):
    def to_rgba(self):
        return {k: c + (255,) for k, c in self.px.items()}

    def bbox(self):
        return Spr.bbox(self)


def plant(s, clip_max=3, lift_max=2):
    """Keep a monster frame on the floor (y <= 0, the feet row = cellH-2). A body that bobbed a pixel or two below it
    is lifted back onto it; anything else below the floor (a staff tip, a pour stream that ran out of the cell) is
    trimmed, as the cell edge used to cut it anyway."""
    below = [k for k in s.px if k[1] > 0]
    if not below:
        return s
    dy = max(k[1] for k in below)
    if len(below) > clip_max and dy <= lift_max:
        return type(s)({(x, y - dy): v for (x, y), v in s.px.items()})
    return type(s)({k: v for k, v in s.px.items() if k[1] <= 0})


def pack(name, anims, cell_w, cell_h, feet, outdir, cols=8, floor=False):
    """anims: list of (animName, [Spr...], durations or None). feet: (x,y) of the feet point inside a cell.
    floor=True plants every frame on the feet row (see plant) so nothing reaches the cell's bottom edge."""
    if floor:
        anims = [(an, [plant(s) for s in sprs], durs) for an, sprs, durs in anims]
    frames = []
    manifest = {"cellW": cell_w, "cellH": cell_h, "cols": cols, "anims": []}
    for an, sprs, durs in anims:
        idx = []
        for s in sprs:
            idx.append(len(frames)); frames.append(s)
        manifest["anims"].append({"name": an, "frames": idx, "durations": list(durs) if durs else []})
    rows = (len(frames) + cols - 1) // cols
    W, H = cols * cell_w, rows * cell_h
    # textures as powers of two are friendlier to old GPUs
    pw = 1
    while pw < W: pw *= 2
    ph = 1
    while ph < H: ph *= 2
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    p = img.load()
    clipped = 0
    for i, s in enumerate(frames):
        ox = (i % cols) * cell_w + feet[0]
        oy = (i // cols) * cell_h + feet[1]
        for (x, y), c in s.to_rgba().items():
            X, Y = ox + x, oy + y
            if (i % cols) * cell_w <= X < (i % cols + 1) * cell_w and (i // cols) * cell_h <= Y < (i // cols + 1) * cell_h:
                p[X, Y] = c
            else:
                clipped += 1
    os.makedirs(outdir, exist_ok=True)
    img.save(os.path.join(outdir, name + ".png"))
    json.dump(manifest, open(os.path.join(outdir, name + ".json"), "w"))
    if clipped: print("WARNING %s: %d pixels clipped by cell bounds" % (name, clipped))
    return img, manifest


def preview(img, manifest, path, scale=6):
    cw, ch, cols = manifest["cellW"], manifest["cellH"], manifest["cols"]
    rows_out = []
    for a in manifest["anims"]:
        rows_out.append(a)
    W = max(len(a["frames"]) for a in rows_out) * (cw + 2) * scale
    H = len(rows_out) * (ch + 2) * scale
    bg = Image.new("RGBA", (W, H), (28, 26, 32, 255))
    for r, a in enumerate(rows_out):
        for j, fi in enumerate(a["frames"]):
            x0, y0 = (fi % cols) * cw, (fi // cols) * ch
            cell = img.crop((x0, y0, x0 + cw, y0 + ch)).resize((cw * scale, ch * scale), Image.NEAREST)
            bg.alpha_composite(cell, (j * (cw + 2) * scale, r * (ch + 2) * scale))
    bg.convert("RGB").save(path)


def interp_poses(keys, n):
    """keys: list of pose dicts; returns n poses sampled across them (nearest key, holding on the strike)."""
    if n <= len(keys):
        # pick evenly but always include first and the strike (index 2 by convention) and last
        idx = sorted(set([0, min(2, len(keys) - 1), len(keys) - 1] + [round(i * (len(keys) - 1) / max(1, n - 1)) for i in range(n)]))
        while len(idx) > n: idx.pop(len(idx) // 2 if len(idx) // 2 not in (0, 2) else 1)
        return [keys[i] for i in idx]
    out = []
    for i in range(n):
        out.append(keys[min(len(keys) - 1, int(i * len(keys) / n))])
    return out
