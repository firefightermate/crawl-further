"""ZHEKRA v2: every Zhekra monster and effect sheet, drawn with the material renderer of
jinx_v2_rigs.py (lit shapes, 3 tones per material, top-left light, selective outline, every frame posed). This file
holds the hive palette and the insect toolkit (segmented bodies, jointed legs and their gaits, wings, antennae,
mandibles, compound eyes, acid and resin drips), the sheet writer and the build entry point. The monsters are in
zhekra_v2_t1.py (tier 1 and the Hive Larva), zhekra_v2_t2.py, zhekra_v2_t3a.py and zhekra_v2_t3b.py; the effects, the
god portrait and the gold idol in zhekra_v2_fx.py.

    python3 zhekra_v2_rigs.py [outdir] [--only Name,Name]

Writes to art/out_zhekra/ of the checkout this file sits in. Manifest format as every other sheet: <id>.png + <id>.json
(cellW, cellH, cols, anims[{name, frames, durations}]) + <id>_preview.png, feet at (cellW // 2, cellH - 2), facing right.
Every sheet is drawn at its final size (no ArtScale entry).
"""
import math, os, sys, random
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402  (the renderer: Rig, ramps, resolve)
from jinx_v2_rigs import Rig, Xf, chain, ik, lerp, line_px, poly_px, flip_x  # noqa: E402,F401
from anim import SprRGB, pack, preview  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = str(ROOT / "art" / "out_zhekra")


def _h(s):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


# ================================================================== palette (ink, shadow, base, light, hi)
# The hive: chitin brown, acid green, resin amber, larva cream, wing violet-grey. Mid tones stay readable on the dark
# crypt floor: no chitin base darker than a warm mid-brown.
ZHK_RAMPS = {
    "chit":   ["1c120e", "3e2a1e", "644630", "8c6844", "b8946a"],   # hive chitin, warm brown (shiny)
    "dchit":  ["16100e", "2e2220", "4a3832", "6a544a", "8e786a"],   # far legs, the dark under-plates
    "rchit":  ["220c0c", "4e1c16", "7c3020", "a85232", "d07e52"],   # soldier ant red-brown
    "ochit":  ["141a0a", "2c3816", "4c5c22", "728238", "9caa58"],   # olive chitin (Spitter, Mortar)
    "cream":  ["3a2a22", "7c6a54", "b8a682", "dcd0aa", "f4ecd0"],   # larva flesh
    "pale":   ["2e2a26", "6c645a", "a69c8a", "cec6b0", "eee8d6"],   # termite cream (Nasute, Colossus back)
    "amber":  ["2a1206", "6a3410", "a8601a", "dc9a34", "fcd478"],   # resin (shiny, translucent)
    "wax":    ["2a1e08", "6a5018", "a8862c", "d8b84c", "f8e490"],   # comb wax
    "acid":   ["1c300a", "3a6a12", "6aa820", "a2dc40", "e2ffa0"],   # acid skin and beads (lit)
    "bloat":  ["1e2a0e", "40581c", "6e8a2e", "a2b84a", "d6e286"],   # the Bloater's swollen green-yellow hide
    "wing":   ["3a3646", "625e74", "8a869c", "b4b0c4", "dcd8e8"],   # violet-grey membrane
    "blood":  ["2a060a", "641018", "a21e22", "d24a3a", "f48a6a"],
    "skin":   ["2e1e22", "6a4a4e", "a87c7a", "d0a8a0", "ecd0c4"],   # the Gorger's stretched sac skin
    "glue":   ["3a3830", "7e7a6c", "bcb8a4", "e0dcca", "fcfaee"],
    "sand":   ["2a2014", "5c4830", "907450", "bca072", "dcc898"],
    "leaf":   ["0e1a0a", "22401a", "3e6626", "5e8a36", "8cb256"],   # mantis green
    "sblue":  ["0c1220", "1c2c4a", "2e4a78", "4c70a4", "7c9ccc"],   # spider wasp steel blue
    "orwing": ["3a1406", "7a300c", "b8561a", "e48c30", "fcc46a"],   # orange wasp wings
    "bronze": ["1e1006", "4a2c10", "7c4e1e", "aa783a", "d4a862"],   # stag jaws
    "scarb":  ["0a1a16", "17402e", "22664a", "3a9064", "6cc08a"],   # scarab iridescent green
    "teal":   ["0a1820", "143a46", "1e5e6a", "36888c", "66b6ae"],   # its sheen
    "fuzz":   ["1e140c", "42301c", "6a4e2e", "947048", "b89670"],   # botfly brown fuzz
    "hyel":   ["2a1a04", "6a4a0a", "ac8414", "dcbc30", "f8e888"],   # hornet yellow bands
    "hblk":   ["120e0c", "2a221c", "463a2e", "625242", "806c58"],   # hornet black bands (a lit brown-black)
    "soot":   ["16120e", "2e2620", "4a4038", "6c6054", "928474"],   # soldier ant black (a lit grey-black)
    "bshell": ["1a120a", "3c2c18", "62482a", "8c6a3a", "bc9658"],   # dung beetle bronze-black
    "royal":  ["2e1a08", "6e4612", "aa7a24", "dcb244", "fbe896"],   # queen gold
    "dust":   ["2a2420", "4a423a", "6e6458", "948a7c", "b8b0a2"],
    "gidol":  ["2c1a08", "6e4614", "aa7826", "dcae46", "fff0a8"],   # gold idol metal
    "honey":  ["1e1006", "3e2410", "62401c", "86602c", "a88444"],   # idol hollows, dark honey
    # emissive (keep their drawn tones, never outlined)
    "aglow":  ["2a5a0a", "5aa018", "9ae034", "d4ff70", "f4ffd0"],   # acid glow (sacs, drool, eyes)
    "rglow":  ["4a0a08", "9a1a12", "e03a22", "ff7a4a", "ffc8a0"],   # red eyes, the Drone's glowing abdomen
    "jelly":  ["6a4a08", "b08a14", "f0c830", "ffe880", "fffad8"],   # royal jelly / amber light
    "spir":   ["4a1a06", "9a3a0c", "e06a1a", "ffa048", "ffd890"],   # spiracle orange
    "mist":   ["3a4a2a", "5a7038", "84a050", "b4d07a", "e0f4b0"],   # acid mist (soft)
    "wblur":  ["3e3a4a", "5e5a70", "8a869e", "b6b2c8", "dedaea"],   # wing blur
    "white":  ["8a8a90", "c8c8cc", "e8e8ea", "f6f6f6", "ffffff"],
}
J.RAMPS.update({k: [_h(c) for c in v] for k, v in ZHK_RAMPS.items()})
J.EMISSIVE.update({"aglow", "rglow", "jelly", "spir", "mist", "wblur", "white", "dust"})
J.SHINY.update({"soot", "bshell", "chit", "rchit", "amber", "acid", "scarb", "bronze", "sblue", "royal", "gidol", "bloat", "hblk"})
RAMPS = J.RAMPS
LIGHT_MATS = ("cream", "pale", "glue", "wax", "amber", "sand", "royal", "gidol", "white")
STONE = [_h(c) for c in ("2a2a30", "4c4c54", "6e6e76", "92929a", "b6b6bc")]


def stone(s):
    """Statue: tones map onto the stone ramp (clusters survive); light materials sit one step up."""
    px = {}
    for k, (m, t) in s.tones.items():
        lift = 1 if m in LIGHT_MATS else 0
        if m in J.EMISSIVE: t = 2
        px[k] = STONE[max(0, min(4, t + lift if t > 0 else 0))]
    out = SprRGB(px); out.tones = {k: ("stone", 0) for k in px}
    return out


class ZRig(Rig):
    """A Rig that draws everything k times larger about the feet (0, 0): a pose is written once in body units and
    each monster picks the scale that fits its tier. 1 px lines stay 1 px wide."""

    def __init__(self, k=1.0):
        Rig.__init__(self)
        self.k = k

    def _p(self, x, y):
        return x * self.k, y * self.k

    def ell(self, cx, cy, rx, ry, mat, z, **kw):
        cx, cy = self._p(cx, cy)
        return Rig.ell(self, cx, cy, rx * self.k, ry * self.k, mat, z, **kw)

    def tube(self, pts, radii, mat, z, **kw):
        return Rig.tube(self, [self._p(*q) for q in pts], [v * self.k for v in radii], mat, z, **kw)

    def poly(self, pts, mat, z, **kw):
        return Rig.poly(self, [self._p(*q) for q in pts], mat, z, **kw)

    def line(self, x0, y0, x1, y1, mat, z, **kw):
        a = self._p(x0, y0); b = self._p(x1, y1)
        return Rig.line(self, a[0], a[1], b[0], b[1], mat, z, **kw)

    def polyline(self, pts, mat, z, **kw):
        return Rig.polyline(self, [self._p(*q) for q in pts], mat, z, **kw)

    def dot(self, x, y, mat, tone, z, part=None):
        x, y = self._p(x, y)
        return Rig.dot(self, x, y, mat, tone, z, part=part)

    def dots(self, pts, mat, tone, z):
        return Rig.dots(self, [self._p(*q) for q in pts], mat, tone, z)


# ================================================================== insect toolkit
def segs(r, pts, radii, mat, z, bias=0.0, ry=None, dz=0.002, bands=None, part_each=True):
    """A segmented body: one lit ellipse per point (pts back to front draw back first). ry: per-segment vertical radii
    (default = radii). bands: per-segment material overrides. Each segment is its own part, so the renderer draws a
    contour where a nearer segment overlaps the one behind it."""
    parts = []
    for i, ((x, y), rx) in enumerate(zip(pts, radii)):
        m = bands[i] if bands else mat
        yy = ry[i] if ry else rx
        parts.append(r.ell(x, y, rx, yy, m, z + i * dz, bias=bias))
    return parts


def leg(r, hip, foot, l1, l2, z, mat="chit", near=True, bend=1, rad=0.0, claw=None, tone=None):
    """A jointed leg from hip to foot (2-bone IK, knee raised). rad > 0 draws a lit tube, else a 1 px line."""
    # an insect's knee rides high: of the two bends, take the one that lifts it
    ka = ik(hip[0], hip[1], foot[0], foot[1], l1, l2, bend)
    kb = ik(hip[0], hip[1], foot[0], foot[1], l1, l2, -bend)
    kx, ky = ka if ka[1] <= kb[1] else kb
    if rad > 0:
        r.tube([hip, (kx, ky), foot], [rad, rad * 0.85, max(0.45, rad * 0.55)], mat, z, bias=0.0 if near else -0.4)
        # the knee: a knob a shade wider, lit on top
        r.ell(kx, ky, rad * 1.15 + 0.2, rad * 1.15 + 0.2, mat, z + 0.001, bias=0.15 if near else -0.3)
    else:
        t = tone if tone is not None else (3 if near else 1)
        r.polyline([hip, (kx, ky), foot], mat, z, tones=[t, max(0, t - 1)])
    if claw:
        r.dot(foot[0] + claw, foot[1], mat, 1 if near else 0, z)
    return (kx, ky)


def gait6(i, n, hips, base, stride=2.0, lift=1.2, phase=0.0):
    """Feet for six legs in a tripod gait: hips/base are lists of 6 (near front, near mid, near back, far front, far
    mid, far back). Legs 0, 4, 2 swing together, then 3, 1, 5."""
    out = []
    for k in range(6):
        grp = 0 if k in (0, 4, 2) else 1
        t = (i / float(n) + grp * 0.5 + phase) % 1.0
        if t < 0.5:     # stance: the foot slides back
            u = t / 0.5
            dx, dy = lerp(stride, -stride, u), 0.0
        else:           # swing: lifts and comes forward
            u = (t - 0.5) / 0.5
            dx, dy = lerp(-stride, stride, u), -lift * math.sin(u * math.pi)
        out.append((base[k][0] + dx, base[k][1] + dy))
    return out


def legs6(r, hips, feet, l1, l2, z_near, z_far, mat="chit", far_mat="dchit", rad=0.0, far_rad=None, bends=None):
    """Six legs: far ones behind the body (darker), near ones in front."""
    for k in range(6):
        near = k < 3
        bend = bends[k] if bends else (1 if (k % 3) == 0 else -1)
        leg(r, hips[k], feet[k], l1[k % 3] if isinstance(l1, (list, tuple)) else l1,
            l2[k % 3] if isinstance(l2, (list, tuple)) else l2, z_near if near else z_far,
            mat if near else far_mat, near=near, bend=bend, rad=(rad if near else (far_rad if far_rad is not None else rad * 0.8)))


def antenna(r, base, ang, ln, curl, z, mat="chit", tone=2, club=None):
    """A thin antenna leaving `base` at `ang` degrees, curling by `curl` degrees along its length."""
    pts = chain(base[0], base[1], [(ln * 0.4, ang), (ln * 0.35, ang + curl * 0.5), (ln * 0.25, ang + curl)])
    r.polyline(pts, mat, z, tones=[tone, tone, max(0, tone - 1)])
    if club:
        r.dot(pts[-1][0], pts[-1][1], club, 3, z + 0.01)
    return pts[-1]


def wing(r, root, ang, ln, chord, z, mat="wing", near=True, veins=2, curve=0.25):
    """A membrane wing from root along ang (degrees), ln long and chord wide. Drawn the way pixel art fakes a clear
    wing: a pale flat membrane, a dark vein frame along the leading edge and tip, veins running out from the root, a
    lighter trailing edge, one glint."""
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    tip = (root[0] + ux * ln, root[1] + uy * ln)
    lead = [root,
            (root[0] + ux * ln * 0.35 + nx * chord * 0.5, root[1] + uy * ln * 0.35 + ny * chord * 0.5),
            (root[0] + ux * ln * 0.75 + nx * chord * 0.55, root[1] + uy * ln * 0.75 + ny * chord * 0.55),
            (tip[0] + nx * chord * 0.15, tip[1] + ny * chord * 0.15), tip]
    trail = [tip, (root[0] + ux * ln * 0.6 - nx * chord * curve, root[1] + uy * ln * 0.6 - ny * chord * curve), root]
    p = r.part(True, z)
    r.poly(lead + trail[1:-1], mat, z, flat=3 if near else 2, part=p)
    # the membrane is lighter toward the trailing edge, as if the floor showed through
    r.poly([lead[1], lead[2], tip, trail[1]], mat, z + 0.0005, flat=4 if near else 3, part=p)
    vt = 1 if near else 0
    r.polyline(lead, mat, z + 0.001, tones=[vt] * (len(lead) - 1), part=p)
    for v in range(veins):
        f = 0.3 + 0.35 * v
        ex = (lerp(lead[2][0], trail[1][0], f), lerp(lead[2][1], trail[1][1], f))
        r.line(root[0], root[1], ex[0], ex[1], mat, z + 0.001, tone=vt + 1, part=p)
    r.dot(lead[2][0] - nx * 0.8, lead[2][1] - ny * 0.8, "white", 3 if near else 2, z + 0.002)
    return tip


def wing_blur(r, root, a0, a1, ln, z, mat="wblur", n=3):
    """A beating wing: the arc its tip sweeps, a thin pale line between a0 and a1 (degrees)."""
    p = r.part(True, z)
    steps = max(4, int(abs(a1 - a0) / 6))
    for k in range(steps + 1):
        a = math.radians(lerp(a0, a1, k / float(steps)))
        r.dot(root[0] + math.cos(a) * ln, root[1] + math.sin(a) * ln, mat, 2 if 0 < k < steps else 1, z, part=p)


def eye(r, x, y, z, mat="dchit", glint=True, big=False, glow=None):
    """A compound eye: a dark glossy bead with a glint (or a lit emissive eye)."""
    if glow:
        r.ell(x, y, 1.1 if big else 0.7, 1.0 if big else 0.6, glow, z, flat=3)
        r.dot(x - 0.4, y - 0.4, glow, 4, z + 0.01)
        return
    r.ell(x, y, 1.3 if big else 0.8, 1.2 if big else 0.7, mat, z, bias=-0.2)
    if glint:
        r.dot(x - (0.5 if big else 0.0), y - (0.5 if big else 0.0), "white", 3, z + 0.01)


def mandible(r, base, ang, ln, curve, z, mat="chit", rad=0.7, tip_tone=4):
    """A hooked mandible from base along ang, bending `curve` degrees toward its point."""
    pts = chain(base[0], base[1], [(ln * 0.5, ang), (ln * 0.3, ang + curve * 0.6), (ln * 0.2, ang + curve)])
    r.tube(pts, [rad, rad * 0.8, rad * 0.55, 0.4], mat, z)
    r.dot(pts[-1][0], pts[-1][1], mat, tip_tone, z + 0.01)
    return pts[-1]


def drip(r, x, y, n, z, mat="aglow", ph=0):
    """A bead hanging from (x, y): n px long; ph picks the stage (0 hangs, 1 stretches, 2 falls)."""
    if ph == 2:
        r.dot(x, y + n + 1, mat, 3, z)
        return
    for j in range(n + (1 if ph == 1 else 0)):
        r.dot(x, y + j, mat, 3 if j == n - 1 else 2, z)


def puddle(r, x, w, z, mat="acid", h=1.6, glint=True, bub=None):
    """A puddle on the floor centred at x (y = 0, drawn just over the floor line)."""
    r.ell(x, -0.6, w, h, mat, z, flat=2)
    r.ell(x - w * 0.25, -0.9, w * 0.45, h * 0.5, mat, z + 0.001, flat=3)
    if glint: r.dot(x - w * 0.4, -1, mat, 4, z + 0.002)
    if bub: r.dot(x + bub, -1, mat, 4, z + 0.003)


def dust(r, x, y, k, w=1.0, n=3, z=6.0, mat="dust"):
    """Floor dust: puffs rolling out to both sides; k = 0 (burst) .. 2 (thinning)."""
    for side in (-1, 1):
        for i in range(n - min(k, n - 1)):
            px = x + side * (2.5 + i * 2.6 + k * 1.6) * w
            py = y - 1.0 - (i % 2) * 0.8 - k * 0.6
            rr = max(0.9, 2.4 - 0.4 * k - 0.3 * i)
            r.ell(px + 0.3, py + rr * 0.35, rr, rr * 0.55, mat, z + i * 0.01 - 0.005, flat=1)   # the shaded underside
            r.ell(px, py, rr, rr * 0.75, mat, z + i * 0.01, flat=3 if (i == 0 and k < 2) else 2)
            if k < 2: r.dot(px - rr * 0.4, py - rr * 0.5, mat, 4, z + i * 0.01 + 0.005)


def smear(r, pts, mat="white", tone=3, z=7.0):
    """A motion smear along pts."""
    r.polyline(pts, mat, z, tones=[tone] * (len(pts) - 1))


def arc_pts(cx, cy, rx, ry, a0, a1, n=8):
    return [(cx + rx * math.cos(math.radians(lerp(a0, a1, k / float(n)))), cy + ry * math.sin(math.radians(lerp(a0, a1, k / float(n)))))
            for k in range(n + 1)]


def splat(r, x, y, k, z, mat="aglow", n=6, spread=5.0, seed=1):
    """Droplets flying out of (x, y): k = 0 (burst) .. 2 (falling)."""
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(-math.pi, 0.0); d = spread * (0.4 + 0.6 * rnd.random()) * (0.6 + 0.4 * k)
        r.dot(x + d * math.cos(a), y + d * math.sin(a) + k * k * 0.8, mat, 3 if i % 2 else 2, z)


def ground_shadow(r, x, w, z=-9.0, mat="dchit", h=1.0):
    """A soft shadow on the floor (for hovering bodies and lifted things)."""
    r.ell(x, -0.4, w, h, mat, z, flat=1)


# ================================================================== sheet assembly
BUILT = {}
SYNC = {}
NOTES = {}


def sheet(name, anims, outdir, scale=6, pad=2, min_w=0, min_h=0):
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert du and len(du) == len(fr), (name, an, len(fr), len(du))
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf)
    hw = max(-x0, x1 + 1) + pad
    cw = max(min_w, 2 * hw)
    ch = max(min_h, -y0 + 1 + pad + 2)
    feet = (cw // 2, ch - 2)
    img, man = pack(name, anims, cw, ch, feet, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": (cw, ch), "feet": feet, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-22s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))
    return img, man


def fx(name, cell, origin, anims, outdir, scale=8):
    """An effect sheet with a fixed cell and origin (the point Strike.ArtAt pins to the effect's position)."""
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-22s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def tail_anims(idle0, death, death_d, knock):
    return [("Death", death, death_d), ("Dead", [death[-1]], [0.3]), ("Statue", [stone(idle0)], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


def done(r):
    """Resolve an effect (no floor clip, no cast shadows or contours: effects are small and float)."""
    return r.resolve(floor=False, cast=False, contour=False)


# ================================================================== timing + build
def write_timing(outdir):
    L = ["# Zhekra: sprite timing", "",
         "Generated by `tools/sprites/zhekra_v2_rigs.py` (and the zhekra_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet, x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). Every sheet is at final size (no ArtScale).",
         "The item icons (IconZhk*) still come from tools/sprites/zhekra_rigs.py.", "",
         "| Sheet | Cell (w x h) | Feet / origin | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in sorted(BUILT.items()):
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox() or (0, 0, 0, 0)
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], bb[2] - bb[0], bb[3] - bb[1],
                                                               ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Sync frames", "", "| Sheet | Anim | Frames | Event | Frame | Time (s) | Length (s) |", "|---|---|---|---|---|---|---|"]
    for n in sorted(SYNC):
        if n not in BUILT: continue
        dd = {a: d for a, k, d in BUILT[n]["anims"]}
        for a, evs in SYNC[n].items():
            if a not in dd: continue
            d = dd[a]
            for ev, fi in evs:
                L.append("| %s | %s | %d | %s | %d | %.2f | %.2f |" % (n, a, len(d), ev, fi, sum(d[:fi]), sum(d)))
    L += ["", "## Durations", ""]
    for n, b in sorted(BUILT.items()):
        for a, k, d in b["anims"]:
            L.append("- %s %s: %s" % (n, a, ", ".join("%.3g" % x for x in d)))
    L += ["", "## Notes", ""] + ["- **%s**: %s" % kv for kv in sorted(NOTES.items())]
    L += ["- Death plays once and ends on the corpse; Dead is that corpse frame. Statue = the Idle frame mapped tone-for-tone",
          "  onto the stone ramp. Every attack has at least two wind-up frames before its first event."]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


JOBS = []


def all_jobs():
    import importlib
    jobs = list(JOBS)
    for mod in ("zhekra_v2_t1", "zhekra_v2_t2", "zhekra_v2_t3a", "zhekra_v2_t3b", "zhekra_v2_fx"):
        try:
            m = importlib.import_module(mod)
        except ImportError as e:
            if mod not in str(e): raise
            continue
        jobs += m.JOBS
    return jobs


def main():
    argv = sys.argv[1:]
    only = None
    if "--only" in argv:
        i = argv.index("--only")
        only = set(argv[i + 1].split(","))
        argv = argv[:i] + argv[i + 2:]
    outdir = argv[0] if argv else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    for name, fn in all_jobs():
        if only and name not in only: continue
        fn(outdir)
    if not only:
        write_timing(outdir)


if __name__ == "__main__":
    sys.modules["zhekra_v2_rigs"] = sys.modules[__name__]
    main()
