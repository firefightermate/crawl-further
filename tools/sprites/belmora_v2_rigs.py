"""BEL'MORA v2: every Bel'Mora monster, effect and portrait sheet.

    python3 belmora_v2_rigs.py [outdir] [--only Name,Name]

Writes to <repo>/art/out_belmora/ by default (the repo root is found from this file's own path). The monsters are in
belmora_v2_t1.py, belmora_v2_t2.py and belmora_v2_t3.py, the effects and portraits in belmora_v2_fx.py; this file
holds the palette, the shared sea-creature parts and the build entry point.

The renderer is the Jinx v2 material buffer (jinx_v2_rigs.Rig): every pixel keeps its depth, material, light and part;
shapes are lit by a real normal against one top-left light and quantised to 3 tones per material (+ a highlight on
shiny ones: bronze, pearl, bone, jelly); the bottom/right silhouette takes the material's own dark tone, the top/left
stays lit (no black ring); stray pixels are folded, front parts cast a one-tone shadow onto what is behind. Faces are
hand-pixelled stamps; bodies, limbs and props are procedural so every frame is a fresh pose.

Bel'Mora's palette: drowned teal and sea-green, barnacle grey, kelp green, tarnished bell bronze with verdigris, and
lure cyan for every eye and glow. Each final adds one accent hue so the twelve stay apart. Wet things get a cool rim
of water light on their top-left edge (wet()) and drip.
"""
import math, os, sys, json
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jinx_v2_rigs as J  # noqa: E402  (the shared material renderer)
from jinx_v2_rigs import Rig, Xf, chain, ik, lerp, line_px, poly_px, stone, flip_x, star, arc_smear  # noqa: E402,F401
from anim import pack, preview, SprRGB  # noqa: E402,F401
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = str(ROOT / "art" / "out_belmora")


def _ramp(*cs):
    return [J._h(c) for c in cs]


# ------------------------------------------------------------------ Bel'Mora ramps (ink, shadow, base, light, highlight)
BEL_RAMPS = {
    "teal":   ("0c1a20", "17363c", "26585a", "3c7e76", "68a698"),   # drowned teal skin
    "sea":    ("0e1c18", "1c3a2c", "2e5c3e", "4a8452", "7cae6c"),   # sea-green
    "barn":   ("1c1c22", "3c3c42", "605f60", "88857c", "b2ad9e"),   # barnacle grey
    "kelp":   ("121a0a", "263616", "3e5622", "5e7c2e", "8aa242"),
    "bronze": ("261608", "56361a", "885a2a", "b8843c", "e6b866"),   # tarnished bell bronze
    "verd":   ("0e2622", "1e4c42", "347666", "58a28a", "96ceb2"),   # verdigris
    "coral":  ("2c0a12", "661c1e", "a2322c", "d25a3e", "f28c64"),   # coral red accents
    "tent":   ("1e0c28", "3e1a50", "602e74", "86509a", "b07ebe"),   # violet tentacles / gown
    "pink":   ("300c22", "6c1c44", "a83c6c", "d66c96", "f4a4c2"),   # anemone / egg pink
    "orange": ("2e1208", "6c2c10", "a84c1c", "d6782e", "f2aa58"),   # boxer shell, clubs
    "slate":  ("141a22", "2a3440", "46525e", "66747e", "90a0a6"),   # lamprey grey
    "bruise": ("10142c", "222c50", "38467a", "5868a2", "8698c6"),   # lurefish blue
    "navy":   ("0c1422", "1a283a", "2a4054", "405c70", "62849a"),   # captain's coat, rotted to teal
    "drown":  ("1c2226", "3c4a48", "607266", "8a9c88", "b6c6aa"),   # drowned grey-green skin
    "hag":    ("2a1a22", "583c44", "866266", "b08e8a", "d6baa8"),   # hagfish pink-grey
    "slime":  ("34442a", "6e8e52", "a6c888", "d2ecba", "f2ffe8"),   # slime green-white
    "tower":  ("1a1a1e", "38383e", "58585e", "7e7c7a", "a6a29a"),   # drowned stone
    "gulp":   ("0a0c18", "171c30", "28304c", "3e4a6c", "60708e"),   # gulper blue-black
    "pouch":  ("3a3442", "7a7082", "aea4b2", "d6ced6", "f2ecf0"),   # pale throat pouch
    "crown":  ("1c0c22", "3c1a40", "5c2c5c", "804676", "a66a92"),   # crown-of-thorns purple
    "shrimp": ("0c2016", "1a422c", "2c6c3e", "48984c", "7ec262"),   # mantis shrimp green
    "rope":   ("1e140a", "46321c", "6c4e2c", "927242", "bc9c62"),
    "iron":   ("161214", "342a28", "56423a", "7c5e4c", "a2826a"),   # anchor iron
    "rust":   ("2a0e08", "5e2210", "903c1c", "ba5c2c", "dc8c52"),
    "canvas": ("1a1a14", "3a3a2c", "5e5c46", "828064", "a8a488"),   # sodden diving canvas
    "jelly":  ("2a1432", "5c3064", "8c5494", "ba82bc", "e4b8e0"),   # translucent violet-pink bell
    "pearl":  ("34343e", "7c7c88", "b8b8c2", "e0e0e6", "fcfcff"),
    "sand":   ("2a2418", "5a4c32", "8a7650", "b29c70", "d6c49a"),
    "urch":   ("0c1218", "182630", "263c48", "3a5a66", "5e8288"),   # urchin teal-black spines
    "spinev": ("140c1c", "2a1838", "40285a", "5c3e7a", "80609c"),   # black-violet spines
    "water":  ("0e2a36", "1a4a5a", "2a6c7a", "4a92a2", "82c2ce"),   # brine water (shaded surfaces)
    # emissive
    "lure":   ("0a3a4a", "158aa0", "3ad0dc", "8cf0f0", "e2ffff"),   # lure cyan: eyes and glows
    "lurey":  ("4a3a08", "a08a14", "f0d83a", "fff08c", "fffce0"),   # the Lurefish's lure yellow
    "tlight": ("4a0a2a", "a01a5a", "f04a90", "ff92c2", "ffdaee"),   # the Gulper's tail light
    "foam":   ("4c6c78", "8cb0ba", "c2dee2", "e6f6f6", "ffffff"),
    "spark":  ("5a3a10", "b07a1a", "f0c040", "ffe890", "fffbe0"),   # bell-ring sparks
}
for _k, _v in BEL_RAMPS.items():
    J.RAMPS[_k] = _ramp(*_v)
J.EMISSIVE |= {"lure", "lurey", "tlight", "foam", "spark"}
J.SHINY |= {"bronze", "verd", "pearl", "jelly", "pouch", "iron", "slime", "water"}
RAMPS = J.RAMPS

# legend helpers for hand-pixelled stamps: char -> (material, tone)
def legend(**kw):
    """legend(k=("teal", 0), ...) -> dict; also accepts 'x'='mat:tone' strings."""
    out = {}
    for k, v in kw.items():
        if isinstance(v, str):
            m, t = v.split(":"); v = (m, int(t))
        out[k] = v
    return out


# ================================================================== shared sea-creature parts
def eye(r, x, y, z, big=False, mat="lure"):
    """A lure-cyan eye: a 1 px glint, or 2 px with a pale core."""
    r.dot(x, y, mat, 3, z)
    if big:
        r.dot(x + 1, y, mat, 2, z); r.dot(x, y - 1, mat, 4, z + 0.01)


def spines(r, cx, cy, rx, ry, n, ln, mat, z, tip="ivory", phase=0.0, skip_down=True, splay=1.0, jitter=0.0, front=True,
           tone=None, tips=2):
    """Radial spines from the rim of an ellipse: a 2-tone line `ln` long (lit root half, darker outer half) with a
    bone tip on every `tips`-th one. skip_down leaves out the ones pointing at the floor (the body sits on them).
    front=False draws only the back ones (behind the body), front=True only the front ones, None both."""
    for i in range(n):
        a = phase + i * math.tau / n
        s, c = math.sin(a), math.cos(a)
        if skip_down and s > 0.35: continue
        back = (i % 2 == 1)
        if front is False and not back: continue
        if front is True and back: continue
        L = ln * (0.75 if back else 1.0) * splay * (1.0 + jitter * (((i * 37) % 7) / 7.0 - 0.5))
        x0, y0 = cx + c * rx * 0.85, cy + s * ry * 0.85
        x1, y1 = cx + c * (rx + L), cy + s * (ry + L * 0.85)
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        lit = (c < 0.3 and s < 0.3)
        zz = z - 0.5 if back else z + 0.2
        t0 = tone if tone is not None else (4 if lit and not back else 3 if not back else 2)
        r.line(x0, y0, xm, ym, mat, zz, tone=t0)
        r.line(xm, ym, x1, y1, mat, zz, tone=max(1, t0 - 1))
        if tip and i % tips == 0: r.dot(x1, y1, tip, 3 if s < 0 else 2, zz + 0.01)


def foam_ring(r, cx, cy, rx, ry, k=0, z=-1.0, n=18):
    """A broken ring of foam on the floor (k: animation phase)."""
    for i in range(n):
        if (i + k) % 3 == 0: continue
        a = i / n * math.tau
        r.dot(cx + rx * math.cos(a), cy + ry * math.sin(a), "foam", 2 if math.sin(a) < 0 else 3, z)


def drips(r, pts, k=0, z=6.0, mat="water"):
    """Water drops falling from points; k shifts them down the frame."""
    for i, (x, y) in enumerate(pts):
        d = (k + i * 2) % 4
        r.dot(x, y + d, mat, 3 if d < 2 else 2, z)


def bubbles(r, x, y, k, n=3, z=7.0, rise=3.0):
    for i in range(n):
        yy = y - ((k * 2 + i * rise) % (n * rise + 2))
        xx = x + (1 if (i + k) % 2 else -1) * (i % 2)
        r.dot(xx, yy, "foam", 3 if i % 2 else 2, z)


def barnacles(r, pts, z, mat="barn"):
    """Small cone barnacles: a lit dot over a dark one."""
    for (x, y) in pts:
        r.dot(x, y, mat, 3, z); r.dot(x + 1, y, mat, 1, z); r.dot(x, y + 1, mat, 1, z)
        r.dot(x, y - 1, mat, 4, z + 0.01)


def leg(r, hip, foot, l1, l2, mat, z, bend=1, rad=(0.9, 0.7, 0.5), bias=0.0, tip=None):
    """A jointed limb from hip to foot (2-bone IK)."""
    kx, ky = ik(hip[0], hip[1], foot[0], foot[1], l1, l2, bend=bend)
    r.tube([hip, (kx, ky), foot], list(rad), mat, z, bias=bias)
    if tip: r.dot(foot[0], foot[1], tip[0], tip[1], z + 0.01)
    return (kx, ky)


def crab_legs(r, cx, cy, half, n, phase, mat, z_near, z_far, step=2.0, lift=1.5, reach=4.0, sideways=False, rad=0.0,
              ground=0.0, knee=3.0, spread=1.6, tuck=0.0):
    """n pairs of jointed crab legs from a carapace edge (cx +- half, cy): each rises to a knee out to the side and
    comes down to a pointed tip on the floor. phase walks them (0..1); sideways makes them scuttle (short, fast,
    alternating); tuck 0..1 folds them under the shell. rad > 0 draws them as lit tubes (big crabs), else 1 px lines
    in two tones (thigh lit, shin darker)."""
    feet = []
    for side in (-1, 1):
        for i in range(n):
            ph = (phase + i * 0.5 / n + (0.5 if side > 0 else 0)) % 1.0
            sw = math.sin(ph * math.tau)
            up = max(0.0, math.cos(ph * math.tau))
            hx = cx + side * (half - 1.5 - i * spread)
            hy = cy + 0.8
            out = (reach - i * 0.6) * (1.0 - 0.7 * tuck)
            fx = cx + side * (half + out - i * spread * 0.6) + (sw * step if not sideways else sw * 1.2 * side)
            fy = ground - up * lift * (0.6 if sideways else 1.0)
            kx = hx + side * (out * 0.55 + 1.0)
            ky = min(hy, fy) - knee * (1.0 - 0.5 * tuck) + i * 0.4 - up * 0.5
            near = side > 0 if not sideways else (i % 2 == 0)
            z = (z_near if side > 0 else z_far) - i * 0.01
            if rad > 0:
                r.tube([(hx, hy), (kx, ky), (fx, fy)], [rad + 0.3, rad, rad - 0.3], mat, z, bias=0.0 if side > 0 else -0.35)
            else:
                t = 3 if side > 0 else 2
                r.line(hx, hy, kx, ky, mat, z, tone=t)
                r.line(kx, ky, fx, fy, mat, z, tone=t - 1)
                r.dot(kx, ky, mat, t + (1 if side > 0 else 0), z + 0.005)
            feet.append((fx, fy))
    return feet


def claw(r, x, y, ang, size, mat, z, open_=0.3, tip="ivory", bias=0.0):
    """A crab claw: a fat palm ellipse and two fingers that open by open_ (0 shut .. 1 wide)."""
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    r.ell(x, y, size, size * 0.72, mat, z, ang=ang, bias=bias)
    fx, fy = x + ca * size * 0.9, y + sa * size * 0.9
    o = 0.35 + open_ * 0.6
    for sgn, ln, zz in ((-1, size * 1.3, z + 0.02), (1, size * 1.0, z + 0.03)):
        b = a + sgn * o
        ex, ey = fx + math.cos(b) * ln, fy + math.sin(b) * ln
        r.tube([(fx, fy), (ex, ey)], [size * 0.42, 0.45], mat, zz, bias=bias + 0.05)
        if tip: r.dot(ex, ey, tip, 2, zz + 0.01)
    return fx, fy


def fin(r, pts, mat, z, bias=0.0, rays=True):
    """A translucent fin: a polygon with ray lines one tone darker."""
    r.poly(pts, mat, z, bias=bias, normal=(-0.2, -0.4, 1.0))
    if rays and len(pts) >= 3:
        bx, by = pts[0]
        for (x, y) in pts[1:-1]:
            r.line(bx, by, x, y, mat, z + 0.01, tone=1)


def kelp_strand(r, x, y, ln, sway, z, mat="kelp", k=0):
    pts = [(x, y)]
    for i in range(int(ln)):
        pts.append((x + math.sin((i + k) * 0.9) * 0.6 * sway + sway * i * 0.15, y + i + 1))
    r.polyline(pts, mat, z, tones=[2 if i % 2 else 1 for i in range(len(pts))])


def wet(r, part_pts, z):
    """A cool rim of water light along given points (top-left edges of wet bodies)."""
    for (x, y) in part_pts: r.dot(x, y, "water", 4, z)


def dust(r, x, y, k, w=1.0, mat="sand"):
    """Floor puffs (sand): k = 0 (burst) .. 2 (thinning)."""
    for side in (-1, 1):
        for i in range(3 - k):
            px = x + side * (2 + i * 2 + k * 1.5) * w
            py = y - (i % 2) - (1 if k else 0)
            r.ell(px, py, 1.1 - 0.3 * k, 0.8, mat, 6.0 + i * 0.01, flat=2 if i else 3)


def splash(r, x, y, k, w=1.0):
    """Brine splash: k = 0 (crown) .. 2 (falling drops)."""
    for i in range(5):
        a = math.radians(-160 + i * 35)
        d = (2.5 + k * 2.0) * w
        h = (3.0 - k * 1.0)
        r.dot(x + math.cos(a) * d, y + math.sin(a) * d * 0.5 - h + (k * k * 0.5), "foam", 3 if i % 2 else 2, 7.0)
    if k == 0:
        r.ell(x, y, 3 * w, 1.0, "foam", 6.9, flat=2)


def bell_shape(r, cx, base, w, h, z, tilt=0.0, mat="bronze", verd=True, crack=False, band=True, knob=True, mouth=True,
               flare=1.0):
    """An upright church bell: a flared lip at `base` (w wide), a narrow waist, a rounded shoulder and crown h above
    it, lit as a cylinder. tilt rocks it about the lip's centre. Returns the transform used."""
    T = Xf(tilt, (cx, base))
    Ti = Xf(-tilt, (cx, base))
    prof = [(0.0, 0.5 * flare), (0.12, 0.44), (0.35, 0.33), (0.62, 0.30), (0.82, 0.30), (0.93, 0.25), (1.0, 0.14)]
    left = [T(cx - w * hw, base - h * y) for (y, hw) in prof]
    right = [T(cx + w * hw, base - h * y) for (y, hw) in prof]
    p = r.part(False, z)
    r.hand.add(p)
    for (x, y) in poly_px(right[::-1] + left):
        lx, ly = Ti(x, y)
        yy = (base - ly) / h
        hw = prof[-1][1]
        for (y0, h0), (y1, h1) in zip(prof, prof[1:]):
            if y0 <= yy <= y1:
                hw = h0 + (h1 - h0) * (yy - y0) / max(1e-6, y1 - y0); break
        u = (lx - cx) / max(1.0, w * hw)
        t = 3 if u < -0.55 else 4 if u < -0.35 else 3 if u < -0.15 else 2 if u < 0.45 else 1
        if yy > 0.92 and u > -0.2: t = min(t + 1, 4)
        if u > 0.85 or yy < 0.04: t = 0 if u > 0.85 else t
        r.put(x, y, z, mat, 0.5, p, t)
    # the lip: a heavy rolled rim, lit on top, dark under
    for i in range(int(w * flare) + 1):
        x = cx - w * 0.5 * flare + i
        r.dot(*T(x, base - 1.0), mat, 4 if x < cx - w * 0.2 else 3 if x < cx + w * 0.2 else 2, z + 0.01)
        if mouth: r.dot(*T(x, base), mat, 0, z + 0.01)
    if band:
        for yy in (0.42, 0.80):
            hw_ = 0.33 if yy < 0.6 else 0.30
            for i in range(int(w * hw_ * 2) + 1):
                x = cx - w * hw_ + i
                r.dot(*T(x, base - h * yy), mat, 1 if x > cx else 2, z + 0.01)
    if verd:
        # verdigris weeping down from the bands
        for (dx, top, ln) in ((-0.18, 0.78, 4), (-0.05, 0.78, 2), (0.1, 0.78, 3), (0.2, 0.4, 3), (-0.25, 0.4, 2), (0.0, 0.4, 4)):
            for j in range(max(1, int(ln * h / 16.0))):
                r.dot(*T(cx + w * dx, base - h * top + j + 1), "verd", 3 if j == 0 else 2, z + 0.02)
    if crack:
        for (dx, dy) in ((0.1, 0.95), (0.12, 0.85), (0.08, 0.75), (0.13, 0.65), (0.1, 0.55)):
            r.dot(*T(cx + w * dx, base - h * dy), mat, 0, z + 0.03)
    if knob:
        r.ell(*T(cx, base - h - 1.0), w * 0.12 + 0.5, 1.4, mat, z + 0.01)
    return T


# ================================================================== sheet assembly
BUILT = J.BUILT
SYNC, NOTES = {}, {}


def sheet(name, anims, outdir, scale=6, pad=2, min_w=0, min_h=0):
    return J.sheet(name, anims, outdir, scale=scale, pad=pad, min_w=min_w, min_h=min_h)


def tail_anims(idle0, death, death_d, knock):
    return J.tail_anims(idle0, death, death_d, knock)


def fx(name, cell, origin, anims, outdir, scale=8):
    img, man = pack(name, anims, cell[0], cell[1], origin, outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    BUILT[name] = {"cell": cell, "feet": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-22s cell %dx%d  %s" % (name, cell[0], cell[1], ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


def done(r):
    """Resolve an effect frame (no floor clip, no cast shadows or contours)."""
    return r.resolve(floor=False, cast=False, contour=False)


def write_timing(outdir):
    L = ["# Bel'Mora: sprite timing", "",
         "Generated by `tools/sprites/belmora_v2_rigs.py` (and the belmora_v2_*.py modules it loads). Frame indices are",
         "0-based within the anim. Monster sheets: feet = (cellW / 2, cellH - 2), facing right. Points are pixels from the",
         "feet, x right, y up NEGATIVE (Kit.AddEffect offsetX = x, offsetY = -y). Every sheet is at final size (no ArtScale).",
         "FX sheets: origin = the effect's anchor (its centre on the floor unless noted).", "",
         "| Sheet | Cell (w x h) | Feet / origin | Idle bounds (w x h) | Anims (frames) |", "|---|---|---|---|---|"]
    for n, b in BUILT.items():
        img = Image.open(os.path.join(outdir, n + ".png")).convert("RGBA")
        cw, ch = b["cell"]
        bb = img.crop((0, 0, cw, ch)).getbbox() or (0, 0, 0, 0)
        L.append("| %s | %d x %d | (%d, %d) | %d x %d | %s |" % (n, cw, ch, b["feet"][0], b["feet"][1], bb[2] - bb[0], bb[3] - bb[1],
                                                               ", ".join("%s %d" % (a, k) for a, k, d in b["anims"])))
    L += ["", "## Sync frames", "", "| Sheet | Anim | Frames | Event | Frame | Time (s) | Length (s) |", "|---|---|---|---|---|---|---|"]
    for n, anims in SYNC.items():
        if n not in BUILT: continue
        dd = {a: d for a, k, d in BUILT[n]["anims"]}
        for a, evs in anims.items():
            d = dd[a]
            for ev, fi in evs:
                L.append("| %s | %s | %d | %s | %d | %.2f | %.2f |" % (n, a, len(d), ev, fi, sum(d[:fi]), sum(d)))
    L += ["", "## Durations", ""]
    for n, b in BUILT.items():
        for a, k, d in b["anims"]:
            L.append("- %s %s: %s" % (n, a, ", ".join("%.2f" % x for x in d)))
    L += ["", "## Notes", ""] + ["- **%s**: %s" % kv for kv in NOTES.items()]
    L += ["- Death plays once and ends on the corpse; Dead is that corpse frame. Statue = the Idle frame mapped tone-for-tone",
          "  onto the stone ramp. Every attack has at least two wind-up frames before its first event."]
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L) + "\n")


MODULES = ("belmora_v2_t1", "belmora_v2_t2", "belmora_v2_t3", "belmora_v2_t3b", "belmora_v2_fx")


def all_jobs():
    import importlib
    jobs = []
    for mod in MODULES:
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError as e:
            if e.name != mod: raise
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
    jobs = all_jobs()
    for name, fn in jobs:
        if only and name not in only: continue
        fn(outdir)
    if not only:
        write_timing(outdir)


if __name__ == "__main__":
    sys.modules["belmora_v2_rigs"] = sys.modules[__name__]
    main()
