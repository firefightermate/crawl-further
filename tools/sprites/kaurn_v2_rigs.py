"""KAURN v2: every Kaurn monster and effect sheet, drawn with the material renderer of the Jinx v2
rig (jinx_v2_rigs.Rig: lit primitives, 3 tones per material, top-left light, selective outline, stray pixels folded).
This file holds Kaurn's palette, the shared parts (limbs, rods, hammers, lightning) and the build entry point; the
monsters are in kaurn_v2_t1.py, kaurn_v2_t2.py, kaurn_v2_t3a.py and kaurn_v2_t3b.py, the effects in kaurn_v2_fx.py.

    python3 kaurn_v2_rigs.py [outdir] [--only Name,Name]

Writes to art/out_kaurn/ of the checkout this file sits in. Sheets: <id>.png + <id>.json (cellW, cellH, cols,
anims[{name, frames, durations}]) + <id>_preview.png, feet at (cellW // 2, cellH - 2), facing right.

Kaurn's look: forge iron, copper and brass under one top-left light; ember orange for heat; storm blue-white for every
arc, eye and spark (emissive: never shaded, never outlined). Each final adds one accent hue so they stay apart.
"""
import math, os, sys, random
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
from jinx_v2_rigs import (Rig, Xf, chain, ik, lerp, sheet, tail_anims, stone, line_px, poly_px, dust_puff,  # noqa: E402,F401
                          arc_smear, BUILT, _h)
from anim import pack, preview  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = str(ROOT / "art" / "out_kaurn")

# ================================================================== palette (ink, shadow, base, light, hi)
KAURN_RAMPS = {
    "iron":   ["18181f", "33353f", "555865", "7d818e", "aeb2bc"],   # forge iron (cool shadows)
    "dkiron": ["141418", "28292f", "403f48", "5c5b66", "7e7c88"],   # blackened iron (anvils, cages)
    "copper": ["2c1008", "6c2e14", "a8582a", "d6874a", "f6bc84"],
    "brass":  ["2c1c08", "6c4c16", "aa8430", "dab656", "f8e49a"],
    "verd":   ["0e2422", "1e4a40", "2f7462", "50a08a", "8accb2"],   # verdigris
    "soot":   ["1e1618", "45342f", "6c5248", "92705c", "b49076"],   # forge-imp hide (warm soot)
    "apron":  ["1e130c", "40281a", "64432e", "88623e", "aa845a"],   # heavy leather
    "skin":   ["3a1a18", "7a3e30", "b06a4e", "d6966c", "f0c098"],   # smith's ruddy skin
    "ghide":  ["141c16", "2c3c30", "4a5c48", "6e8062", "98a684"],   # gremlin green-grey
    "wyv":    ["0e2018", "1c4430", "2e6a44", "4c9458", "7cbc76"],   # wyvern green
    "bull":   ["16181e", "363a4c", "585e72", "7e8698", "a8b0be"],   # storm-grey hide
    "robe":   ["1a1820", "3a3640", "5c5662", "807a86", "a49ea8"],
    "tabard": ["0c1430", "1a2e66", "2c4e9a", "4a76c6", "80a4e4"],
    "scarab": ["0a1430", "163068", "2454aa", "4082d6", "8ec6f6"],
    "zinc":   ["1e2226", "3e4448", "62686c", "8a9094", "b8bec0"],
    "brine":  ["102014", "24442a", "3a6a3e", "5a8e52", "88b47a"],
    "magred": ["2a0808", "661414", "a82424", "dc4a3a", "ff9a7a"],
    "magblu": ["081430", "142e6a", "2050b0", "4a86e0", "9cc8ff"],
    "pred":   ["2a0a0a", "6a1a14", "b03424", "e0643a", "ffa070"],
    "pgreen": ["0a2210", "1a4a22", "2e7a34", "52aa48", "94d678"],
    "pviol":  ["1a0c2a", "3a1e5e", "6232a0", "8e58cc", "c49cf0"],
    "mwing":  ["241410", "4e2e1e", "7c4c30", "a87648", "d0a874"],   # moth's copper-dust wings
    "fur":    ["1c1a20", "3a3a44", "5e5e6a", "868892", "b0b2ba"],   # warg / hound iron-grey fur
    "glassk": ["14222c", "2a4656", "4a7486", "7eaab8", "c6eaf2"],   # leyden jar glass
    "wood":   ["1e120e", "4a2a1a", "70442a", "96643c", "b88a58"],
    "gold":   ["2e1a10", "6e4618", "a8782a", "dcb04a", "fbe796"],
    # emissive: storm light, heat, steam
    "storm":  ["1a3a6a", "3a6eb4", "6ab0ec", "b8e4ff", "f6fdff"],
    "coal":   ["2a0a08", "5a1410", "8a2a18", "b04a24", "d06a34"],
    "ember":  ["4a0c0a", "a0200e", "e8501a", "ffa040", "fff0a0"],
    "fire":   ["5a1a0a", "b8401a", "f07a24", "ffc04a", "fff0b0"],
    "steam":  ["6a7480", "98a2ac", "c4ccd4", "e4eaee", "ffffff"],
    "spark":  ["4a3a6a", "8a74c8", "c0b0f4", "e8e0ff", "ffffff"],
    "violetg": ["2a1050", "5a2a9a", "9a5ae0", "cc9cf8", "f4e4ff"],
    "glowred": ["5a0c0c", "b01a1a", "ff3a2a", "ff8a6a", "ffd8c8"],
    "lode":   ["16161c", "2e3040", "4c5064", "72788e", "a6aec4"],   # lodestone hide: blued iron
}
J.RAMPS.update({k: [_h(c) for c in v] for k, v in KAURN_RAMPS.items()})
J.EMISSIVE |= {"storm", "coal", "steam", "spark", "violetg", "glowred"}
J.SHINY |= {"copper", "brass", "verd", "magred", "magblu", "scarab", "pred", "pgreen", "pviol", "glassk", "iron", "zinc", "lode"}

FX_SCALE = 6


# ================================================================== lightning
def zig(a, b, n=4, amp=2.0, seed=0):
    """Jagged points from a to b: n legs, each kink pushed up to amp px across the line."""
    rnd = random.Random(seed)
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    pts = [a]
    for i in range(1, n):
        t = i / n
        o = rnd.uniform(-amp, amp)
        pts.append((x0 + (x1 - x0) * t + nx * o, y0 + (y1 - y0) * t + ny * o))
    pts.append(b)
    return pts


def bolt(r, a, b, z=8.0, n=None, amp=2.0, seed=0, core=4, glow=2, mat="storm", fork=0):
    """A lightning bolt: a white-hot core polyline wrapped in a one-pixel glow; fork adds side branches."""
    if n is None: n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 4))
    pts = zig(a, b, n, amp, seed)
    p = r.part(True, z)
    core_px = []
    for i in range(len(pts) - 1):
        core_px += line_px(int(round(pts[i][0])), int(round(pts[i][1])), int(round(pts[i + 1][0])), int(round(pts[i + 1][1])))
    if glow is not None:
        for (x, y) in core_px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                r.put(x + dx, y + dy, z - 0.01, mat, 0.5, p, glow)
    for (x, y) in core_px:
        r.put(x, y, z, mat, 0.5, p, core)
    rnd = random.Random(seed + 77)
    for k in range(fork):
        i = rnd.randrange(1, len(pts) - 1) if len(pts) > 2 else 0
        sx, sy = pts[i]
        ang = math.atan2(b[1] - a[1], b[0] - a[0]) + rnd.choice((-1, 1)) * rnd.uniform(0.6, 1.1)
        ln = rnd.uniform(2.5, 4.5)
        e = (sx + ln * math.cos(ang), sy + ln * math.sin(ang))
        for (x, y) in line_px(int(round(sx)), int(round(sy)), int(round(e[0])), int(round(e[1]))):
            r.put(x, y, z - 0.005, mat, 0.5, p, max(2, core - 1))
    return pts


def crackle(r, x, y, k=0, seed=0, z=9.0, mat="storm", size=2):
    """A tiny static crackle (3-5 px zigzag) at (x, y); k cycles its shape."""
    rnd = random.Random(seed * 13 + k * 7)
    px, py = x, y
    for i in range(size + 1):
        r.dot(px, py, mat, 4 if i == 0 else 3, z)
        px += rnd.choice((-1, 1)); py += rnd.choice((-1, 0, 1))


def spark(r, x, y, k=1, z=9.0, mat="storm"):
    """A struck spark: k=1 a bright 4-point star, 2 a fading cross, 3 a single glint."""
    if k == 1:
        r.dot(x, y, mat, 4, z)
        for d in (1, 2):
            for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                r.dot(x + dx, y + dy, mat, 3 if d == 1 else 2, z)
    elif k == 2:
        r.dot(x, y, mat, 3, z)
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            r.dot(x + dx, y + dy, mat, 2, z)
    else:
        r.dot(x, y, mat, 3, z)


def ember_spark(r, x, y, k=1, z=9.0):
    spark(r, x, y, k, z, mat="ember")


def eye(r, x, y, z, mat="storm", tone=4, wide=False):
    r.dot(x, y, mat, tone, z)
    if wide: r.dot(x + 1, y, mat, tone - 1, z)


# ================================================================== limbs and gear
def leg(r, hip, foot, l1, l2, mat, z, rad=(1.6, 1.3), bend=1, boot=None, boot_len=2.5, bias=0.0, toe=1, thin=False):
    """A two-bone leg from hip to foot (the sole's back point), knee by IK; a boot block forward of the foot."""
    kx, ky = ik(hip[0], hip[1], foot[0], foot[1] - 0.8, l1, l2, bend)
    r.tube([hip, (kx, ky), (foot[0], foot[1] - 0.8)], [rad[0], rad[1], rad[1]], mat, z, bias=bias, thin=thin)
    if boot:
        bl = boot_len * toe
        r.poly([(foot[0] - 1.2 * toe, foot[1] - 2.0), (foot[0] + bl, foot[1] - 1.4), (foot[0] + bl + 0.6 * toe, foot[1]),
                (foot[0] - 1.2 * toe, foot[1])], boot, z + 0.01, bias=bias + 0.1)
    return kx, ky


def arm(r, sh, hand, l1, l2, mat, z, rad=(1.4, 1.1), bend=-1, fist=None, fist_r=1.4, bias=0.0, thin=False):
    ex, ey = ik(sh[0], sh[1], hand[0], hand[1], l1, l2, bend)
    r.tube([sh, (ex, ey), hand], [rad[0], rad[1], rad[1]], mat, z, bias=bias, thin=thin)
    if fist: r.ell(hand[0], hand[1], fist_r, fist_r, fist, z + 0.02, bias=bias + 0.1, thin=thin)
    return ex, ey


def hammer(r, hx, hy, ang, ln, z, head=(4.0, 3.0), haft="wood", head_mat="dkiron", glow=None, back=0.0):
    """A hammer held at (hx, hy): haft of length ln along ang (deg), a head w x h square across its end."""
    a = math.radians(ang)
    tx, ty = hx + ln * math.cos(a), hy + ln * math.sin(a)
    bx, by = hx - back * math.cos(a), hy - back * math.sin(a)
    r.tube([(bx, by), (tx, ty)], [0.7, 0.7], haft, z, thin=True)
    w, h = head
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for su, sv in ((-0.5, -1), (0.5, -1), (0.5, 1), (-0.5, 1)):
        u, v = su * h, sv * w / 2.0
        pts.append((tx + u * ca - v * sa, ty + u * sa + v * ca))
    r.poly(pts, head_mat, z + 0.05, normal=(-0.4, -0.5, 0.8))
    if glow:
        r.dot(tx + ca * h * 0.5, ty + sa * h * 0.5, glow, 3, z + 0.06)
    return tx, ty


def rod(r, x, y, h, z, hot=0, mat="iron", tip="copper", lean=0.0, spark_k=None, glow=None):
    """An iron lightning rod standing at (x, y), h px tall: a copper finial and a little base flange. hot: 0..1 glow."""
    top = (x + lean, y - h)
    r.tube([(x, y - 0.5), top], [0.9, 0.7], mat if not hot else "coal", z, bias=0.1)
    if hot:
        for i in range(int(h * hot)):
            r.dot(x + lean * (i / h), y - 1 - i, "ember" if hot > 0.6 else "coal", 3 if i > h * 0.5 else 2, z + 0.01)
    r.ell(top[0], top[1] - 0.6, 1.2, 1.2, tip, z + 0.02, bias=0.2)
    r.dot(top[0], top[1] - 2, tip, 3, z + 0.03)
    r.ell(x, y - 0.4, 2.0, 0.8, mat, z - 0.02, bias=-0.1)
    if glow: r.dot(top[0], top[1] - 0.6, glow, 4, z + 0.04)
    if spark_k: spark(r, top[0], top[1] - 2, spark_k)
    return top


def shadow(r, x, y, w, z=-5.0, mat="dkiron"):
    """A one-tone floor shadow ellipse under a hovering body (drawn in the ink tone)."""
    p = r.part(True, z)
    # a soft one-row smudge (the game draws its own shadow too): solid in the middle, broken toward the ends
    for i in range(-int(w), int(w) + 1):
        if abs(i) < w * 0.6 or i % 2 == 0: r.put(x + i, y, z, mat, 0.5, p, 1)


def corpse_rod(r, x, y, z=6.0, k=0):
    """The slag rod a dying Kaurn monster leaves (drawn into the last death frames)."""
    rod(r, x, y, 9 + k * 3, z, mat="dkiron", tip="copper", lean=-1.0, spark_k=2 if k else 1)


# ================================================================== FX sheet helper
def fx(name, cell, origin, anims, outdir, scale=FX_SCALE):
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-22s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def done(r):
    return r.resolve(floor=False, cast=False, contour=False)


def msheet(name, anims, outdir, scale=4):
    """A monster sheet (every anim posed): the cell fits every frame."""
    return sheet(name, anims, outdir, scale=scale)


# ================================================================== timing notes
SYNC, NOTES = {}, {}


def write_timing(outdir):
    L = ["# Kaurn, the Storm Forge: sprite timing", "",
         "Generated by `tools/sprites/kaurn_v2_rigs.py` (and the kaurn_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet, x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). FX sheets: points are from the sheet's",
         "origin. Every sheet is at final size (no ArtScale).", "",
         "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in BUILT.items():
        if n.startswith("Fx") or n.startswith("Deity"): continue
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox()
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], bb[2] - bb[0], bb[3] - bb[1],
                                                               ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "| FX sheet | Cell | Origin | Anims |", "|---|---|---|---|"]
    for n, b in BUILT.items():
        if not n.startswith("Fx") and not n.startswith("Deity"): continue
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, b["cell"][0], b["cell"][1], b["feet"][0], b["feet"][1],
                                                     ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Sync frames", "", "| Sheet | Anim | Event | Frame | Time (s) | Length (s) |", "|---|---|---|---|---|---|"]
    for n, anims in SYNC.items():
        if n not in BUILT: continue
        dd = {a: d for a, k, d in BUILT[n]["anims"]}
        for a, evs in anims.items():
            if a not in dd: continue
            d = dd[a]
            for ev, fi in evs:
                L.append("| %s | %s | %s | %d | %.2f | %.2f |" % (n, a, ev, fi, sum(d[:fi]), sum(d)))
    L += ["", "## Durations", ""]
    for n, b in BUILT.items():
        for a, k, d in b["anims"]:
            L.append("- %s %s: %s" % (n, a, ", ".join("%.2f" % x for x in d)))
    L += ["", "## Notes", ""] + ["- **%s**: %s" % kv for kv in NOTES.items()]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


# ================================================================== build
MODULES = ("kaurn_v2_t1", "kaurn_v2_t2", "kaurn_v2_t3a", "kaurn_v2_t3b", "kaurn_v2_fx")


def all_jobs():
    import importlib
    jobs = []
    for mod in MODULES:
        try:
            m = importlib.import_module(mod)
        except ImportError as e:
            if mod not in str(e): raise
            continue
        jobs += m.JOBS
        SYNC.update(getattr(m, "SYNC", {}))
        NOTES.update(getattr(m, "NOTES", {}))
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
    sys.modules["kaurn_v2_rigs"] = sys.modules[__name__]   # the tier modules import this one by name: share its state
    main()
