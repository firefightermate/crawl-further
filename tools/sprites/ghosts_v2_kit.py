"""Shared kit for the v2 ghost-line art (ghosts_v2_fodder.py, ghosts_v2_blobs.py, goldsecret_v2.py, statuemon_v2.py).

Everything is drawn with the material renderer of jinx_v2_rigs.py (imported, not copied): every pixel keeps its depth,
material and light, shapes are lit from the top left and quantised to three tones per material, the bottom edge takes
the material's darkest tone instead of a black ring, and stray pixels are folded. This file adds the line's own
material ramps and a sheet writer that can keep a cell size the C# depends on.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import jinx_v2_rigs as J  # noqa: E402
from anim import SprRGB, pack, preview  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(ROOT, "art")

Rig, stone, flip_x, Xf, chain, ik, lerp, line_px, poly_px = J.Rig, J.stone, J.flip_x, J.Xf, J.chain, J.ik, J.lerp, J.line_px, J.poly_px
RAMPS, EMISSIVE, SHINY = J.RAMPS, J.EMISSIVE, J.SHINY


def add_ramps(table, emissive=(), shiny=()):
    """Register materials: name -> five hex tones (ink, shadow, base, light, highlight)."""
    for k, v in table.items():
        RAMPS[k] = [J._h(c) for c in v]
    EMISSIVE.update(emissive)
    SHINY.update(shiny)


add_ramps({
    # the ghost line's shared ectoplasm and spirit glows
    "ecto":   ["1c2a28", "2e4440", "4a6a5e", "6a8f78", "9ab89a"],
    "spirit": ["1e3a40", "2e5e66", "5a9aa4", "9ac8cc", "d4ecec"],   # banshee cyan
    "soul":   ["243a26", "3a5e3a", "6a9448", "a4c86a", "d4e8a0"],   # revenant green
    "hexv":   ["241a2e", "403050", "6a5084", "9a80b0", "c8b4d8"],   # hex violet
    "candle": ["2e2018", "54382a", "7e5a40", "a8845e", "d0b488"],
    # bodies and props
    "pale":   ["1e2232", "4a5468", "77849a", "a8b4c6", "d6e0ec"],   # keener: cold dead skin
    "nhair":  ["1a1428", "2e2444", "483a66", "66548a", "8a78ae"],   # night-violet hair
    "bone":   ["3a2c1e", "7a6650", "b49c78", "dcc8a0", "f4e8c8"],
    "rag":    ["101208", "23251c", "363a2a", "4c5238", "687048"],   # grave rags
    "earth":  ["140c08", "2e1e14", "4a3020", "6a4a30", "8a6a48"],
    "tallow": ["5a4630", "9a8664", "cbb68c", "eadcb6", "fff6e0"],
    "wick":   ["0a0808", "1e1a18", "322c28", "4a423c", "605850"],
    "gran":   ["26262e", "484a54", "6a6c76", "8e909a", "b4b6bc"],   # gargoyle granite
    "moss":   ["0e1a0c", "1e3418", "2e4626", "4a6e34", "74a048"],
    "burlap": ["2a1c10", "4a3420", "76563a", "a07c52", "c8a474"],
    "thread": ["1e1010", "46201e", "6e302a", "8e4a3c", "aa6a58"],   # red stitching / yarn
    "yarn":   ["0c0a10", "1c1822", "2e2836", "463e50", "5e566a"],
    "button": ["0a0a10", "1a1a24", "2e2e3c", "4a4a5c", "6e6e84"],
    "chest":  ["1a120c", "33261a", "4e3c2a", "6a543c", "8a7254"],   # mimic oak
    "iron":   ["0e0e12", "26262e", "40404a", "5e5e6a", "828290"],
    "brass":  ["2e2210", "5e4a24", "8e7238", "b49a5a", "d8c48e"],
    "tongue": ["2a1014", "4e242a", "74383e", "985458", "b47a7a"],
    "mouth":  ["06040a", "0e0a12", "1a1220", "2a1e30", "3a2a40"],
}, emissive={"spirit", "soul", "hexv", "candle"}, shiny={"brass", "bone", "tallow", "pale", "iron"})


def outdir_for(sub):
    return os.path.join(ART, sub)


BUILT = {}


def sheet(name, anims, outdir, cell=None, min_cell=(0, 0), scale=6, pad=2, floor_max=0):
    """Pack frames (feet at (cellW // 2, cellH - 2)). cell=(w, h) keeps a size the code depends on (pixels past it are
    reported and clipped); otherwise the cell grows to fit, never smaller than min_cell."""
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an)
        for i, f in enumerate(fr):
            if f.px and max(p[1] for p in f.px) > floor_max:
                print("WARNING %s/%s[%d] has pixels below the floor" % (name, an, i))
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf)
    if cell:
        cw, ch = cell
    else:
        hw = max(-x0, x1 + 1) + pad
        cw, ch = max(min_cell[0], 2 * hw), max(min_cell[1], -y0 + 1 + pad + 2)
    feet = (cw // 2, ch - 2)
    lost = 0
    for an, fr, du in anims:
        for f in fr:
            for (x, y) in f.px:
                if not (-feet[0] <= x < cw - feet[0] and -feet[1] <= y < ch - feet[1]): lost += 1
    if lost: print("WARNING %s: %d pixels outside the %dx%d cell" % (name, lost, cw, ch))
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims], "img": img, "man": man}
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return img, man


def tail(idle0, death, death_d, knock, spawn=None):
    out = [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [stone(idle0)], [0.2]),
           ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]
    if spawn: out.append(("Spawn", spawn, SPAWN_DURS))
    return out


SPAWN_DURS = [0.067, 0.083, 0.2, 0.2, 0.25]   # vanilla slime Spawn timing (its events stay on the same times)


# ------------------------------------------------------------------ small shared shapes
def spark(r, x, y, k, mat="spirit", z=8.0):
    """A four-point twinkle: k = 0 dot, 1 plus, 2 long plus."""
    r.dot(x, y, mat, 4 if k else 3, z)
    if k >= 1:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r.dot(x + dx, y + dy, mat, 2, z - 0.01)
    if k >= 2:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            r.dot(x + dx, y + dy, mat, 1, z - 0.02)


def puff(r, x, y, k, mat="smoke", w=1.0, z=6.0):
    """Floor dust/earth: k = 0 (burst) .. 2 (thinning)."""
    for side in (-1, 1):
        for i in range(3 - k):
            px = x + side * (2 + i * 2 + k * 1.5) * w
            py = y - (i % 2) - (1 if k else 0)
            r.ell(px, py, 1.3 - 0.3 * k, 0.9, mat, z + i * 0.01, flat=2 if i else 3)


def shadow_blob(r, x, w, mat="mouth", z=-9.0):
    """A dark contact shadow on the floor row (used under hovering things)."""
    for dx in range(-int(w), int(w) + 1):
        r.dot(x + dx, 0, mat, 1 if abs(dx) < w - 1 else 0, z)


# ------------------------------------------------------------------ selective outline for finished frames
class RGBASpr(SprRGB):
    """Frame whose pixels are RGBA tuples."""

    def to_rgba(self):
        return dict(self.px)

    def stone(self):
        px = {}
        for k, c in self.px.items():
            l = _lum(c)
            px[k] = J.STONE[max(0, min(4, int(l / 52)))] + (c[3],)
        return RGBASpr(px)


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _shade(c, k):
    """c darkened by k, the shadow pushed a little cooler (the ramps' hue shift)."""
    return (int(min(c[0], c[0] * k * 0.94)), int(min(c[1], c[1] * k * 0.97)), int(min(c[2], c[2] * k * 1.06 + 4)), c[3])


N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def selout(spr, ink_lum=62, gap=22, floor=True):
    """Turn a drawn black ring into a selective outline, keeping the footprint: an outline pixel whose open side is
    below takes its neighbour's darkest tone (it sits the shape on the floor), one open to the right drops to the
    neighbour's shadow tone, and one on the lit top / left edge takes the neighbour's own colour. Only edge pixels
    clearly darker than the shape inside them count as outline; thin dark features (a 1 px staff) are kept."""
    src = spr.to_rgba()
    out = dict(src)
    for (x, y), c in src.items():
        if c[3] == 0 or _lum(c) >= ink_lum: continue
        open_ = [(dx, dy) for dx, dy in N4 if src.get((x + dx, y + dy), (0, 0, 0, 0))[3] == 0]
        if not open_: continue
        # the shape inside: the neighbour opposite an open side, else any lighter neighbour
        inner = None
        for dx, dy in open_:
            q = src.get((x - dx, y - dy))
            if q and q[3] and _lum(q) - _lum(c) > gap:
                inner = q; break
        if inner is None:
            for dx, dy in N4:
                q = src.get((x + dx, y + dy))
                if q and q[3] and _lum(q) - _lum(c) > gap:
                    inner = q; break
        if inner is None: continue
        inner = inner[:3] + (c[3],)
        if (0, 1) in open_:
            out[(x, y)] = _shade(inner, 0.42)
        elif (1, 0) in open_:
            out[(x, y)] = _shade(inner, 0.66)
        else:
            out[(x, y)] = inner
    return RGBASpr(out)


def selout_anims(anims, **kw):
    return [(a, [selout(f, **kw) if f.px else f for f in fr], d) for a, fr, d in anims]


# ------------------------------------------------------------------ Crawl's palette: muted, grimy, low saturation
def mute_palette(palette, chars, sat=0.65, val=0.95, grime=(0x5a, 0x50, 0x44), grime_k=0.12):
    """Pull palette entries toward Crawl's own palette in place: saturation scaled by `sat`, value by `val`, and a
    little of a grimy umber mixed in. Accent chars are simply left out of `chars`."""
    import colorsys
    for ch in chars:
        c = palette.get(ch)
        if c is None: continue
        h, s, v = colorsys.rgb_to_hsv(*(x / 255.0 for x in c[:3]))
        r, g, b = colorsys.hsv_to_rgb(h, s * sat, v * val)
        rgb = tuple(int(round((x * 255) * (1 - grime_k) + grime[i] * grime_k)) for i, x in enumerate((r, g, b)))
        palette[ch] = rgb + tuple(c[3:])


def mute_rgb(ramp, sat=0.65, val=0.95, grime=(0x5a, 0x50, 0x44), grime_k=0.12):
    """mute_palette for a ramp of RGB / RGBA tuples; returns the muted ramp."""
    tmp = {i: c for i, c in enumerate(ramp)}
    mute_palette(tmp, list(tmp), sat, val, grime, grime_k)
    return [tmp[i] for i in range(len(ramp))]
