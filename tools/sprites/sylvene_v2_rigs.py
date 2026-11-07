"""SYLVENE v2: every Sylvene monster and effect sheet, drawn with the material renderer of
jinx_v2_rigs.py (one top-left light, 3 tones per material plus a highlight on shiny ones, selective outline, cluster
passes, hand-pixelled faces, every frame posed). This file holds the Sylvene materials, the orchard's shared parts
(caps, vines, thorns, leaves, insect wings, pods) and the build entry point; the monsters are in sylvene_v2_t1.py,
sylvene_v2_t2.py, sylvene_v2_t3.py and sylvene_v2_t3b.py, the effects and the gold idol in sylvene_v2_fx.py.

    python3 sylvene_v2_rigs.py [outdir] [--only Name,Name]

Writes to art/out_sylvene/ of the checkout this script sits in. Same manifest format as every other sheet: <id>.png +
<id>.json (cellW, cellH, cols, anims[{name, frames, durations}]) + <id>_preview.png, feet at (cellW // 2, cellH - 2),
facing right. Every sheet is drawn at its final size (no ArtScale entry).
"""
import math, os, sys, random
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402
from jinx_v2_rigs import (Rig, Xf, chain, ik, lerp, star, arc_smear, dust_puff, sheet, tail_anims, stone, poly_px,  # noqa: E402,F401
                          line_px, RAMPS, EMISSIVE, SHINY, BUILT, SprRGB, pack, preview, _h)
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = str(ROOT / "art" / "out_sylvene")

# ================================================================== Sylvene materials (ink, shadow, base, light, hi)
SYL_RAMPS = {
    "rot":    ["0e1a12", "1e3a20", "305a2c", "4c7e38", "7ca84c"],   # rot green: flesh of the orchard
    "moss":   ["0c1c0c", "1a3e1a", "2e682a", "4c923a", "86bc5c"],   # living vine and leaf
    "bark":   ["1e140e", "44301e", "6a4c32", "90704a", "b49468"],   # bark brown
    "bruise": ["1a0c20", "3c1a42", "5e2e62", "82507e", "a6789e"],   # bruise purple
    "pollen": ["3a2a0a", "7a5a14", "b89222", "e4c23c", "fff28e"],   # pollen yellow (shiny)
    "podf":   ["3a1624", "7a3446", "b45c66", "dc8a86", "f6c0aa"],   # pod flesh-pink
    "mould":  ["2c302e", "646c66", "a0a89c", "c8d0c0", "eef4e4"],   # mould white
    "corpse": ["1e1c22", "403e46", "66646c", "8e8c92", "b4b2b6"],   # corpse grey
    "fung":   ["2a160c", "5e3618", "905a28", "bc8440", "e0b46c"],   # shelf fungus
    "cordy":  ["3a120a", "7a2c10", "be5018", "ee822c", "ffbc64"],   # cordyceps orange (Saint's accent)
    "blood":  ["2a0610", "5e0e1e", "982232", "c8423e", "ee7c64"],   # blood-red thorn tips, rose red
    "lily":   ["3a3c34", "7e8472", "bcc6aa", "e2eace", "fcfeea"],   # lily white (shiny)
    "pale":   ["162418", "2e4c34", "4e7854", "78a272", "aace96"],   # pale green skin (witch)
    "bile":   ["1e2a0a", "42601a", "6e9a22", "9cc834", "d0ec6a"],   # bile green
    "chitin": ["14121a", "2a2534", "3e3850", "5a5270", "7e769a"],   # insect black (kept off near-black)
    "gall":   ["2a1e12", "5a442a", "8c6c42", "b69462", "dabe8c"],   # gall tan / seed tan
    "rotred": ["2a0a0e", "66141a", "a22626", "ce4836", "ee7e5a"],   # carrion-lily red
    "berry":  ["0a0812", "1a1628", "2c2642", "463e60", "6a6288"],   # berry black (shiny)
    "bell":   ["1c0c2c", "3e1c5c", "64348c", "8c5ab6", "b48ed8"],   # bell-flower purple
    "thorn":  ["3a3430", "7a7268", "b2a896", "d8d0be", "f6f0e0"],   # thorn white (shiny)
    "lthr":   ["1e120c", "44281a", "6c4628", "906638", "b48a52"],   # bellows leather
    "irid":   ["08181a", "0e3e3a", "186a56", "28a074", "78e0a4"],   # iridescent green (shiny)
    "spore":  ["24180e", "4e3622", "7a5836", "a27e4e", "caa872"],   # spore brown
    "rust":   ["1c0e0a", "40200f", "683818", "8c5226", "ae7040"],   # bark-brown rusted iron
    "wingm":  ["2c343a", "4e5c66", "7c8c96", "a8bcc4", "dceef2"],   # insect wing membrane (shiny)
    "tusk":   ["3a3026", "7c6a52", "b8a280", "dccaa4", "f8ecd0"],   # tusk ivory (shiny)
    "gold":   ["2e1a10", "6e4618", "a8782a", "dcb04a", "fbe796"],
    "bramble": ["10240e", "24481c", "3c742c", "5ea240", "9ad068"],  # living bramble plate (Briar Champion)
    "amber":  ["3a1e06", "7a4210", "b8721c", "e8a434", "ffd67a"],   # cordyceps fruiting caps
    "hair":   ["0e0a14", "1e1630", "302650", "4a3e6e", "6c5e92"],   # nightshade's black hair (violet lights)
    # emissive (not shaded, no sel-out)
    "glowg":  ["1a3a10", "3a7a1a", "6ac22a", "a8f05a", "e8ffb0"],   # orchard magic, wisps, motes
    "glowp":  ["2a0a3a", "5a1a7a", "8a3ab4", "c07ae0", "f0c8ff"],   # nightshade shimmer
    "sporec": ["2a2c22", "5a5e46", "8e9468", "bcc290", "e2e8bc"],   # spore cloud
    "gas":    ["2a3010", "4e5a1c", "7a8a30", "a8b850", "d4e08a"],   # blight gas
    "pollc":  ["5a4210", "9a7a1a", "d2b030", "f0d860", "fff6b0"],   # pollen dust
    "bilef":  ["2a3a0a", "4e6a12", "78a01e", "a8cc3a", "dcf27a"],   # flowing bile
    "ring":   ["2a3a2a", "4e6e4a", "86b070", "c0e0a0", "f0ffe0"],   # drone sound ring
}
for _k, _v in SYL_RAMPS.items():
    RAMPS[_k] = [_h(c) for c in _v]
EMISSIVE.update({"glowg", "glowp", "sporec", "gas", "pollc", "bilef", "ring"})
SHINY.update({"pollen", "lily", "berry", "thorn", "irid", "wingm", "tusk", "gold", "podf", "amber"})


# ================================================================== the orchard's parts
def thorn(r, x, y, ang, ln, z, mat="thorn", tip="blood", w=0):
    """A thorn spike from (x, y) along ang (deg), ln px long: pale shaft, blood-red tip."""
    a = math.radians(ang)
    pts = [(x + i * math.cos(a), y + i * math.sin(a)) for i in range(int(ln) + 1)]
    for i, (px, py) in enumerate(pts):
        t = i / max(1, len(pts) - 1)
        m = tip if (tip and t > 0.6) else mat
        r.dot(px, py, m, 3 if m == tip else 2, z)
        if w and i == 0:
            r.dot(px - math.sin(a), py + math.cos(a), mat, 2, z)


def vine(r, pts, rad, z, mat="moss", thorns=0, tmat="thorn", tip="blood", bias=0.0, seed=1, tlen=2, zs=None):
    """A vine (capsule chain) with `thorns` spikes along it, alternating sides."""
    r.tube(pts, rad if isinstance(rad, (list, tuple)) else [rad], mat, z, bias=bias, zs=zs)
    if thorns:
        rnd = random.Random(seed)
        segs = len(pts) - 1
        for k in range(thorns):
            t = (k + 0.5) / thorns * segs
            i = min(segs - 1, int(t)); f = t - i
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
            base = math.degrees(math.atan2(y1 - y0, x1 - x0))
            side = 1 if k % 2 else -1
            rr = rad[min(i, len(rad) - 1)] if isinstance(rad, (list, tuple)) else rad
            ox, oy = -math.sin(math.radians(base)) * rr * side, math.cos(math.radians(base)) * rr * side
            thorn(r, x + ox, y + oy, base + side * 70 + rnd.uniform(-15, 15), tlen, z + 0.05, tmat, tip)


def leaf(r, x, y, ang, ln, z, mat="moss", w=1.2):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    tip = (x + c * ln, y + s * ln)
    mid = (x + c * ln * 0.45, y + s * ln * 0.45)
    pts = [(x, y), (mid[0] - s * w, mid[1] + c * w), tip, (mid[0] + s * w, mid[1] - c * w)]
    r.poly(pts, mat, z, normal=(-0.3, -0.5, 0.8))


def cap(r, cx, cy, rx, ry, z, mat="mould", spots="bruise", gill="corpse", crack=True, seed=3, nspots=4, tilt=0.0):
    """A mushroom cap: a domed half-ellipsoid over a dark gill line, with spots and a crack."""
    T = Xf(tilt, (cx, cy))

    def clip(x, y):
        return y <= cy + 0.5
    p = r.ell(cx, cy, rx, ry, mat, z, bias=0.1, clip=clip, ang=tilt)
    r.ell(cx, cy + 0.6, rx * 0.92, 1.0, gill, z - 0.1, bias=-0.3, ang=tilt)
    rnd = random.Random(seed)
    for k in range(nspots):
        a = math.radians(200 + (k + 0.5) * 140 / nspots + rnd.uniform(-8, 8))
        sx, sy = T(cx + rx * 0.62 * math.cos(a), cy + ry * 0.62 * math.sin(a))
        r.dot(sx, sy, spots, 2, z + 0.02)
        if k % 2 == 0: r.dot(sx + 1, sy, spots, 3, z + 0.02)
    if crack:
        x0, y0 = T(cx + rx * 0.2, cy - ry * 0.9)
        r.polyline([(x0, y0), (x0 + 1, y0 + 1.5), (x0, y0 + 2.5)], "corpse", z + 0.03, tone=1)
    return p


def wing(r, root, ang, ln, w, z, mat="wingm", vein="chitin", veins=2, tone=None):
    """An insect wing: a thin translucent leaf shape from root along ang, with dark veins."""
    x, y = root
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    tip = (x + c * ln, y + s * ln)
    m1 = (x + c * ln * 0.55 - s * w, y + s * ln * 0.55 + c * w)
    m2 = (x + c * ln * 0.6 + s * w * 0.6, y + s * ln * 0.6 - c * w * 0.6)
    r.poly([(x, y), m1, tip, m2], mat, z, normal=(-0.4, -0.6, 0.7), flat=tone)
    for k in range(veins):
        f = 0.35 + 0.5 * k / max(1, veins)
        r.line(x, y, x + c * ln * f - s * w * 0.4 * (k + 1) / veins, y + s * ln * f + c * w * 0.4 * (k + 1) / veins, vein, z + 0.01, tone=2)


def pod(r, x, y, s, z, ripe=1.0, mat="podf", husk="rot", seeds=True, split=0.0):
    """A seed pod sitting at (x, y) (its bottom), size s px: a pink flesh ball in a green husk that splits as it ripens."""
    cy = y - s * 0.55
    r.ell(x, cy, s * 0.5, s * 0.55, mat if ripe > 0.3 else husk, z, bias=0.1)
    # husk leaves cupping the pod
    for side in (-1, 1):
        r.poly([(x + side * s * 0.15, y), (x + side * s * 0.62, cy + s * 0.05), (x + side * s * 0.3, cy - s * (0.15 + 0.3 * (1 - ripe)))],
               husk, z + 0.05, normal=(side * 0.3 - 0.3, -0.4, 0.8))
    if split > 0 and seeds:
        for k in range(int(1 + split * 2)):
            r.dot(x - 1 + k, cy - s * 0.2, "gall", 4, z + 0.1)
    r.dot(x, cy - s * 0.55, husk, 2, z + 0.06)


def motes(r, x, y, k, n=5, mat="glowg", spread=5.0, seed=1, z=8.0, rise=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.uniform(0, math.tau); d = spread * (0.3 + 0.7 * rnd.random())
        r.dot(x + d * math.cos(a), y + d * math.sin(a) * 0.6 - k * rise, mat, max(1, 4 - (k + i) % 3), z)


def puff(r, x, y, rad, z, mat="sporec", k=0, seed=2, n=5):
    """A cloud of lumps (emissive): k = 0 dense .. 3 thinning. Each lump is shaded (a dark rim down-right, a lit crown
    up-left) and the cloud's edge breaks up into a dither, so it reads as soft volume and not a flat blob."""
    rnd = random.Random(seed)
    for i in range(n):
        a = i / n * math.tau + rnd.uniform(-0.3, 0.3)
        d = rad * (0.45 + 0.15 * k)
        rr = rad * (0.55 - 0.08 * k) * rnd.uniform(0.8, 1.15)
        px, py = x + d * math.cos(a), y + d * math.sin(a) * 0.7
        base = max(1, 3 - k + (i % 2))
        r.ell(px + rr * 0.2, py + rr * 0.2, rr, rr * 0.85, mat, z + i * 0.01, flat=max(0, base - 1))
        r.ell(px - rr * 0.1, py - rr * 0.1, rr * 0.85, rr * 0.7, mat, z + i * 0.01 + 0.002, flat=base)
        if rr > 1.4: r.ell(px - rr * 0.35, py - rr * 0.35, rr * 0.4, rr * 0.35, mat, z + i * 0.01 + 0.004, flat=min(4, base + 1))
        for j in range(int(rr * 3)):
            b = rnd.uniform(0, math.tau)
            if rnd.random() < 0.45:
                r.dot(px + (rr + 1.0) * math.cos(b), py + (rr * 0.85 + 0.8) * math.sin(b), mat, max(0, base - 2), z - 0.01)
    if k < 2:
        r.ell(x, y, rad * 0.55, rad * 0.45, mat, z + 0.1, flat=3 - k)
        r.ell(x - rad * 0.15, y - rad * 0.15, rad * 0.3, rad * 0.25, mat, z + 0.11, flat=4 - k)


def smears(r, sm):
    for s in sm or ():
        if s[0] == "arc": arc_smear(r, *s[1:])
        else: r.polyline(s[1], s[2], 4.8, tone=s[3])


def sparks(r, sp):
    for (x, y, k) in sp or (): star(r, x, y, k)


def soil(r, x, y, k, w=1.0, mat="bark"):
    """Dirt kicked up from the floor: k = 0 (burst) .. 2 (settling)."""
    for side in (-1, 1):
        for i in range(3 - k):
            px = x + side * (2 + i * 2.2 + k * 1.2) * w
            py = y - (2 - i) * (1 if k == 0 else 0.5) - (1 if i == 0 and k == 0 else 0)
            r.dot(px, py, mat, 2 + (i % 2), 6.0)


def stance(make, idle_args, run_args):
    return [make(**a) for a in idle_args], [make(**a) for a in run_args]


# ================================================================== TIMING.md
SYNC = {}
NOTES = {}


def write_timing(outdir):
    L = ["# Sylvene, the Rot Orchard: sprite timing", "",
         "Generated by `tools/sprites/sylvene_v2_rigs.py` (and the sylvene_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet (FX: from the sheet's origin), x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). Every sheet",
         "is at final size (no ArtScale).", "",
         "| Sheet | Cell (w x h) | Feet | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in sorted(BUILT.items()):
        if n.startswith("Fx") or n.startswith("Deity"): continue
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox()
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], bb[2] - bb[0], bb[3] - bb[1],
                                                               ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "| Effect sheet | Cell | Origin | Anims (frames) |", "|---|---|---|---|"]
    for n, b in sorted(BUILT.items()):
        if not (n.startswith("Fx") or n.startswith("Deity")): continue
        L.append("| %s | %d x %d | (%d, %d) | %s |" % (n, b["cell"][0], b["cell"][1], b["feet"][0], b["feet"][1],
                                                      ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Sync frames", "", "| Sheet | Anim | Frames | Event | Frame | Time (s) | Length (s) |", "|---|---|---|---|---|---|---|"]
    for n in sorted(SYNC):
        if n not in BUILT: continue
        dd = {a: d for a, k, d in BUILT[n]["anims"]}
        for a, evs in SYNC[n].items():
            d = dd[a]
            for ev, fi in evs:
                L.append("| %s | %s | %d | %s | %d | %.2f | %.2f |" % (n, a, len(d), ev, fi, sum(d[:fi]), sum(d)))
    L += ["", "## Durations", ""]
    for n, b in sorted(BUILT.items()):
        for a, k, d in b["anims"]:
            L.append("- %s %s: %s" % (n, a, ", ".join("%.2f" % x for x in d)))
    L += ["", "## Notes", ""] + ["- **%s**: %s" % kv for kv in sorted(NOTES.items())]
    L += ["- Death plays once and ends on the corpse; Dead is that corpse frame. Statue = the Idle frame mapped tone-for-tone",
          "  onto the stone ramp. Every attack has at least two wind-up frames before its first event."]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


# ================================================================== build
MODULES = ("sylvene_v2_t1", "sylvene_v2_t2", "sylvene_v2_t3", "sylvene_v2_t3b", "sylvene_v2_fx")


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
    sys.modules["sylvene_v2_rigs"] = sys.modules[__name__]   # the tier modules import this one by name: share its state
    main()
