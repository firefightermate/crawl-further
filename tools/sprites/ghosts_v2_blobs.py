"""The six ectoplasm blobs (Mote, Spitter, Gel, Brute, Titan, King), drawn with the material renderer
(ghosts_v2_kit, from jinx_v2_rigs) on a metaball body.

    python3 ghosts_v2_blobs.py [outdir] [--only Name,Name]

One ectoplasm for all six: a lit gel skin, a darker core seen through it, a glowing heart, a backlit rim on the lower
right, wet highlights, bubbles and whatever the blob has swallowed. Gel -> Brute -> Titan read as one family growing:
the same face, and one glowing heart per Gel fused into it (Gel 1, Brute 2, Titan 3).

Cells are locked (the C# kits and their ArtScale factors depend on them, see SheetScales.cs and GhostPack.cs); the
anims, frame counts, durations and event frames are the ones in art/out_ghosts/TIMING.md.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ghosts_v2_kit import Rig, stone, chain, lerp, sheet, tail, spark, outdir_for, Xf, add_ramps, J  # noqa: E402

OUT = outdir_for("out_ghosts")
CELLS = {"BlobMote": (24, 16), "BlobSpitter": (30, 20), "BlobGel": (40, 20), "BlobBrute": (54, 33),
         "BlobTitan": (78, 42), "BlobKing": (86, 54)}
# Crawl's own palette: muted, grimy teal-greens (the vanilla slimes and ghosts); the heart's sickly green is the accent
add_ramps({
    "gel":     ["1c2a28", "2e4440", "4a6a5e", "6a8f78", "9ab89a"],     # the ectoplasm skin
    "gelcore": ["121c1a", "1a2826", "243632", "2e4440", "3c5650"],     # the deep core seen through it
    "glowg":   ["3c5a2e", "6a9448", "a4c86a", "d4e8a0", "eef6d0"],     # the heart / inner glow (accent)
    "eyew":    ["5a6a62", "9aaa9c", "d0dccc", "eef2e6", "f8faf2"],
    "rock":    ["1a181c", "36323a", "524e58", "6e6a70", "948e94"],
    "plate":   ["2a2620", "524c42", "7a7262", "a49a84", "c8bea6"],     # Titan's bone plates
    "kcrown":  ["2e2210", "5e4a24", "8e7238", "b49a5a", "d8c48e"],     # tarnished brass
    "kcape":   ["1a1420", "2a2032", "3e3048", "54445e", "6e5e78"],     # faded velvet
    "ermine":  ["4a4842", "86827a", "b4b0a4", "d4d0c4", "e8e4d8"],
    "ruby":    ["2e1216", "54222a", "7a3440", "9a4e58", "b87078"],
    "emer":    ["16261e", "2a4a38", "4a7a5a", "7aa080", "a8c4a8"],
}, emissive={"glowg", "eyew", "emer"}, shiny={"kcrown", "rock", "ruby"})

TH = 0.3
KR = math.sqrt(1 - math.sqrt(TH))


# ================================================================== metaball gel
def goo(r, balls, mat, z, bias=0.0, clip=None, part=None, zr=None, cut=True):
    """Union of soft balls [(x, y, rx, ry)] lit as one smooth surface, one part. Returns its pixel set."""
    if not balls: return set()
    B = [(x, y, rx / KR, ry / KR, min(rx, ry)) for (x, y, rx, ry) in balls]
    x0 = int(math.floor(min(b[0] - b[2] for b in B))) - 1; x1 = int(math.ceil(max(b[0] + b[2] for b in B))) + 1
    y0 = int(math.floor(min(b[1] - b[3] for b in B))) - 1; y1 = int(math.ceil(max(b[1] + b[3] for b in B))) + 1
    Z = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            F = R = 0.0
            for (cx, cy, fx, fy, rr) in B:
                d2 = ((x - cx) / fx) ** 2 + ((y - cy) / fy) ** 2
                if d2 < 1.0:
                    f = (1.0 - d2) ** 2; F += f; R += f * rr
            if F > TH:
                Z[(x, y)] = (zr or (R / F) * 1.15) * math.sqrt(min(1.0, (F - TH) / (1.0 - TH)))
    p = part or r.part(False, z)
    out = set()
    for (x, y), h in Z.items():
        if cut and y > 0: continue
        if clip and not clip(x, y): continue
        gx = (Z.get((x + 1, y), 0.0) - Z.get((x - 1, y), 0.0)) * 0.5
        gy = (Z.get((x, y + 1), 0.0) - Z.get((x, y - 1), 0.0)) * 0.5
        n = math.sqrt(gx * gx + gy * gy + 1.0)
        r.put(x, y, z, mat, J.lam(-gx / n, -gy / n, 1.0 / n) + bias, p)
        out.add((x, y))
    return out


def inset(mask, k):
    """Pixels of mask at least k px from its edge."""
    cur = set(mask)
    for _ in range(k):
        cur = {q for q in cur if all((q[0] + dx, q[1] + dy) in cur for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    return cur


def rim(r, mask, z):
    """Backlight: the gel one pixel in from its lower-right edge glows a step lighter (it reads translucent)."""
    p = r.part(True, z)
    r.hand.add(p)
    for (x, y) in mask:
        if (x + 1, y + 1) in mask and ((x + 2, y + 2) not in mask) and (x + 1, y + 2) in mask | {(x + 1, y + 2)} \
                and y < -1 and (x, y + 1) in mask and (x + 1, y) in mask:
            r.put(x, y, z, "gel", 0.5, p, 3)


def shine(r, x, y, k, z):
    """Wet highlight: a bright pixel (+ a softer one beside it when big)."""
    r.dot(x, y, "eyew", 3, z)
    if k > 1: r.dot(x + 1, y, "glowg", 2, z); r.dot(x, y + 1, "glowg", 2, z)


def bubbles(r, pts, z, mask):
    for (x, y) in pts:
        x, y = int(round(x)), int(round(y))
        if (x, y) in mask and (x + 1, y + 1) in mask:
            r.dot(x, y, "glowg", 1, z); r.dot(x + 1, y + 1, "gelcore", 1, z)


def heart(r, x, y, k, z, pulse=0):
    """The glowing heart a Gel carries (k = size)."""
    r.ell(x, y, 1.3 * k + 0.3 * pulse, 1.1 * k + 0.3 * pulse, "glowg", z, flat=1 if k > 1 else 2)
    r.ell(x - 0.2, y - 0.2, 0.8 * k, 0.7 * k, "glowg", z + 0.01, flat=2 + pulse)
    r.dot(x - 0.4 * k, y - 0.4 * k, "glowg", 4 if pulse else 3, z + 0.02)


def eyes(r, x, y, kind, state, z, gap=3.0, size=1, look=1):
    """Faces. kind: 'one' (the Mote's big eye), 'two' (the family's pair), 'brow' (a heavy-browed pair)."""
    if state == "none": return
    if kind == "one":
        if state in ("open", "wide"):
            r.ell(x, y, 1.9, 1.9 if state == "open" else 2.2, "eyew", z, flat=2)
            r.dot(x + look, y, "mouth", 0, z + 0.01); r.dot(x + look, y + 1, "mouth", 1, z + 0.01)
            r.dot(x - 1, y - 1, "eyew", 4, z + 0.02)
        elif state == "squint":
            r.line(x - 2, y, x + 2, y - 1, "eyew", z, tone=3); r.dot(x + look, y, "mouth", 0, z + 0.01)
        elif state == "blink":
            r.line(x - 2, y + 1, x + 2, y + 1, "gelcore", z, tone=0)
        elif state == "dead":
            for d in (-1, 0, 1): r.dot(x + d, y + d, "gelcore", 0, z); r.dot(x + d, y - d, "gelcore", 0, z)
        return
    for k, ex in enumerate((x - gap / 2, x + gap / 2)):
        near = k == 1
        if state in ("open", "wide"):
            h = 2 if state == "wide" or size > 1 else 1
            for j in range(h + 1):
                r.dot(ex, y - j + (1 if h else 0), "eyew", 3 if j == h else 2, z)
            if size > 1: r.dot(ex + 1, y, "eyew", 2, z)
            r.dot(ex + (1 if size > 1 else 0) * look, y + 1, "mouth", 0, z + 0.01)
        elif state == "squint":
            r.dot(ex, y, "eyew", 3, z); r.dot(ex + 1, y, "eyew", 2, z)
        elif state == "blink":
            r.dot(ex, y + 1, "gelcore", 0, z); r.dot(ex + 1, y + 1, "gelcore", 0, z)
        elif state == "dead":
            r.dot(ex, y, "gelcore", 0, z); r.dot(ex + 1, y + 1, "gelcore", 0, z)
            r.dot(ex + 1, y, "gelcore", 1, z); r.dot(ex, y + 1, "gelcore", 1, z)
        if kind == "brow" and state != "dead":
            r.line(ex - 1, y - 2 + (0 if near else -0.5), ex + 2, y - 1.5 + (0.6 if near else 0), "gelcore", z + 0.02, tone=0)


def mouth(r, x, y, w, gape, z, teeth=0, smile=0.0):
    """A mouth: a smile line (gape 0) or an open dark maw (gape px) with optional fangs."""
    if gape <= 0.3:
        for i in range(int(round(-w)), int(round(w)) + 1):
            dy = smile * (1 - (i / max(1.0, w)) ** 2)
            r.dot(x + i, y + round(dy), "gelcore", 0, z)
        return
    r.ell(x, y + gape * 0.4, w, max(0.8, gape * 0.6), "mouth", z, flat=1)
    r.dot(x + w * 0.4, y + gape * 0.6, "tongue", 2, z + 0.01)
    for t in range(teeth):
        tx = x - w + 1 + t * (2 * w - 1) / max(1, teeth - 1) if teeth > 1 else x
        r.dot(tx, y, "bone", 4, z + 0.02)
        if gape > 2: r.dot(tx + 0.5, y + gape - 0.2, "bone", 3, z + 0.02)


# ================================================================== the body
class P:
    """A blob pose: squash sy (>1 tall), lean (top shifts forward px), lift (off the floor), dx, ph (wobble phase)."""

    def __init__(self, sy=1.0, lean=0.0, lift=0.0, dx=0.0, ph=0.0, sx=None):
        self.sy, self.lean, self.lift, self.dx, self.ph = sy, lean, lift, dx, ph
        self.sx = sx if sx is not None else 1.0 / math.sqrt(sy)

    def __call__(self, x, y):
        """Body-local point (y up negative, 0 = floor) -> pixel; the upper body leans."""
        yy = y * self.sy - self.lift
        return self.dx + x * self.sx + self.lean * (-y / 10.0), yy


def body_balls(p, R, top=0.55, wob=0.6, base=1.25):
    """Main mass, a spread foot and a wobbling crown, for body radius R."""
    w = math.sin(p.ph) * wob
    bs = [(0.0, -R * 0.82, R * 1.08, R * 0.84),
          (0.0, -R * 0.32, R * base, R * 0.42),
          (-R * 0.15 + w * 0.5, -R * 1.42, R * top, R * top * 0.85)]
    return [(p(x, y)[0], p(x, y)[1], rx * p.sx, ry * p.sy) for (x, y, rx, ry) in bs]


def gel_body(r, p, R, extra=(), core=True, z=0.0, top=0.55, base=1.25, cut=True):
    balls = body_balls(p, R, top=top, base=base) + [(x, y, rx, ry) for (x, y, rx, ry) in extra]
    mask = goo(r, balls, "gel", z, bias=-0.12, cut=cut)
    if core and R >= 3.5:
        k = 2 if R > 6 else 1
        inner = inset(mask, k + 1)
        cx, cy = p(R * 0.18, -R * 0.62)
        goo(r, [(cx, cy, R * 0.7 * p.sx, R * 0.55 * p.sy)], "gelcore", z + 0.05, bias=-0.35,
            clip=lambda x, y: (x, y) in inner, cut=cut)
    rim(r, mask, z + 0.2)
    return mask


def finish(r, glints=(), z=9.0):
    for (x, y, k) in glints: shine(r, x, y, k, z)
    return r.resolve()


# ================================================================== MOTE: small and cute, one big eye
def mote(sy=1.0, lean=0.0, lift=0.0, dx=0.0, ph=0.0, sx=None, eye="open", look=1, bite=0.0, smile=0.6, pool=0.0,
         drops=()):
    r = Rig()
    p = P(sy, lean, lift, dx, ph, sx)
    R = 4.0
    extra = []
    if bite:
        extra.append((p(R * 0.9 + bite, -R * 0.55)[0], p(0, -R * 0.55)[1], 1.6 + bite * 0.3, 1.3))
    if pool:
        extra.append((dx, -0.6, R * 1.6 * pool, 0.9))
    mask = gel_body(r, p, R, extra, top=0.5, base=1.2)
    hx, hy = p(R * 0.25, -R * 1.0)
    r.dot(*p(-R * 0.45, -R * 0.45), "glowg", 1, 0.4)                 # a tiny heart low in the back
    eyes(r, hx, hy, "one", eye, 1.0, look=look)
    mx, my = p(R * 0.75, -R * 0.42)
    if bite:
        mouth(r, mx + bite * 0.6, my, 1.4 + bite * 0.3, 1.0 + bite, 1.1, teeth=2)
    elif eye != "dead":
        mouth(r, mx, my, 1, 0, 1.1, smile=smile)
    for (x, y) in drops: r.dot(x, y, "gel", 3, 2.0); r.dot(x, y + 1, "gel", 1, 1.99)
    gx, gy = p(-R * 0.55, -R * 1.25)
    return finish(r, [(gx, gy, 1)] if eye != "dead" else [])


def mote_sheet(outdir):
    M = mote
    idle = [M(), M(sy=0.9, ph=1.6), M(sy=0.95, ph=3.2, eye="blink"), M(sy=1.1, ph=4.7, look=0)]
    run = [M(sy=0.72, lean=0.5), M(sy=1.3, lean=2.0, lift=1, ph=1.2), M(sy=1.1, lean=1.5, lift=3, ph=2.0),
           M(sy=0.95, lift=3.5, ph=2.8), M(sy=1.18, lean=-1.0, lift=1.5, ph=3.6), M(sy=0.66, lean=1.0, ph=4.4)]
    bite = [M(sy=0.86, lean=-0.8, dx=-0.3, ph=0.6), M(sy=0.8, lean=-1.4, dx=-0.6, ph=1.0, eye="squint"),
            M(sy=0.66, lean=-2.2, dx=-1.3, ph=1.8, eye="squint"),
            M(sy=0.9, sx=1.3, lean=2.2, dx=1.0, ph=2.6, eye="wide", bite=1.6),
            M(sy=1.0, sx=1.18, lean=1.6, dx=1.2, ph=3.1, eye="squint", bite=1.2),
            M(sy=1.08, lean=0.6, dx=0.6, ph=3.6, bite=0.6)]
    death = [M(sy=1.25, lean=-1.5, ph=2.0, eye="dead"), M(sy=0.55, ph=3.0, eye="dead", pool=0.6),
             M(sy=0.35, sx=1.7, ph=4.0, eye="none", pool=1.0, drops=[(-6, -2), (6, -3)]),
             M(sy=0.22, sx=1.9, eye="none", pool=1.2)]
    knock = M(sy=0.88, lean=-2.0, dx=-1, ph=5.0, eye="squint")
    spawn = blob_spawn(M)
    anims = [("Idle", idle, [0.18, 0.14, 0.18, 0.14]), ("Run", run, [0.06] * 6),
             ("Bite", bite, [0.07, 0.07, 0.07, 0.06, 0.08, 0.1])] + tail(idle[0], death, [0.08, 0.1, 0.12, 0.4], knock, spawn)
    return sheet("BlobMote", anims, outdir, cell=CELLS["BlobMote"], scale=10)


def blob_spawn(f, **kw):
    """Spawn 5: a pool gathers (0), heaves into a mound (1), surges up tall (2), lands squashed (3), settles (4)."""
    return [f(sy=0.3, sx=1.7, eye="none", pool=1.0, **kw), f(sy=0.62, sx=1.25, ph=1.0, eye="blink", **kw),
            f(sy=1.36, lean=0.4, lift=1.0, ph=1.7, eye="wide", **kw), f(sy=0.76, sx=1.2, ph=2.5, eye="squint", **kw),
            f(sy=1.06, ph=3.4, **kw)]


# ================================================================== SPITTER: a sac of glowing goo and a nozzle
def spitter(sy=1.0, lean=0.0, lift=0.0, dx=0.0, ph=0.0, sx=None, eye="open", sac=1.0, nozzle=0.0, puff=0.0, glob=None,
            pool=0.0, drops=()):
    """sac 0..1.4: how full the sac on its back is; nozzle: the spout's tilt (+ down toward the floor, deg);
    puff 0..1 the spout's lips flaring at the spit."""
    r = Rig()
    p = P(sy, lean, lift, dx, ph, sx)
    R = 4.6
    extra = [(dx + 0.5, -0.6, R * 1.6 * pool, 0.9)] if pool else []
    mask = gel_body(r, p, R, extra, top=0.35, base=1.3)
    # the sac: a translucent bulb riding the back, glowing goo sloshing inside
    if sac > 0:
        sx_, sy_ = p(-R * 0.55, -R * 1.45)
        rs = 2.2 + sac * 0.9
        r.ell(sx_, sy_ - rs * 0.4, rs, rs * 0.9, "gel", 0.3, bias=0.15)
        r.ell(sx_ + 0.3, sy_ - rs * 0.25, rs * 0.65, rs * 0.55, "glowg", 0.32, flat=1)
        r.dot(sx_ - rs * 0.4, sy_ - rs * 0.9, "eyew", 3, 0.35)
        r.dot(sx_ + rs * 0.3, sy_ - rs * 0.2, "glowg", 3, 0.34)
    # the nozzle: a gel tube from the front of the head, lips at its tip
    if eye != "dead":
        bx, by = p(R * 0.6, -R * 1.05)
        a = math.radians(-10 + nozzle)
        L = 3.6 + puff * 0.8
        tip = (bx + L * math.cos(a), by + L * math.sin(a))
        r.tube([(bx, by), tip], [1.4, 1.1], "gel", 0.6, bias=0.1)
        r.ell(tip[0] + 0.3, tip[1], 0.9 + puff * 0.6, 1.2 + puff * 0.7, "gel", 0.65, bias=0.25)
        r.dot(tip[0] + 0.8, tip[1], "mouth", 0, 0.7)
        if puff: r.dot(tip[0] + 1.6, tip[1] - 1, "glowg", 2, 0.7)
    ex, ey = p(R * 0.05, -R * 1.0)
    eyes(r, ex, ey, "two", eye, 1.0, gap=2.4)
    if glob:
        gx, gy, k = glob
        r.ell(gx, gy, 1.6 + k * 0.4, 1.2 + k * 0.3, "glowg", 2.0, flat=1)
        r.dot(gx - 0.5, gy - 0.5, "glowg", 3, 2.01)
    for (x, y) in drops: r.dot(x, y, "gel", 3, 2.0)
    return finish(r, [(p(-R * 0.75, -R * 0.85)[0], p(0, -R * 0.85)[1], 1)])


def spitter_sheet(outdir):
    S = spitter
    idle = [S(), S(sy=0.94, ph=1.6, sac=1.1), S(sy=0.92, ph=3.2, eye="blink", sac=1.2), S(sy=1.04, ph=4.7, sac=1.05)]
    run = [S(sy=0.72, lean=0.5), S(sy=1.25, lean=2.0, lift=1, ph=1.2, sac=0.9), S(sy=1.08, lean=1.5, lift=3, ph=2.0, sac=0.8),
           S(sy=0.95, lift=3.5, ph=2.8, sac=1.1), S(sy=1.15, lean=-1.0, lift=1.5, ph=3.6, sac=1.2), S(sy=0.7, lean=1.0, ph=4.4)]
    # Spit: the sac swells (0-1), squeezes (2), RELEASE on 3 (the glob drops out of the nozzle to the floor), recover
    spit = [S(sy=0.9, sac=1.2, nozzle=-15, eye="squint"), S(sy=0.82, sac=1.45, nozzle=-25, lean=-1.0, eye="squint"),
            S(sy=1.1, sac=0.6, nozzle=10, lean=1.0, puff=0.6, eye="wide"),
            S(sy=1.05, sac=0.3, nozzle=30, lean=1.5, puff=1.0, eye="wide", glob=(10.0, -1.6, 1)),
            S(sy=0.95, sac=0.5, nozzle=15, lean=0.8, puff=0.3), S(sac=0.8, nozzle=0)]
    death = [S(sy=1.2, lean=-1.5, eye="dead", sac=1.4), S(sy=0.6, eye="dead", sac=0.4, pool=0.6, drops=[(-5, -6)]),
             S(sy=0.35, sx=1.7, eye="none", sac=0.0, pool=1.0, drops=[(-7, -2), (7, -2)]), S(sy=0.22, sx=1.9, eye="none", sac=0, pool=1.2)]
    knock = S(sy=0.88, lean=-2.0, dx=-1, eye="squint", sac=1.3, nozzle=-30)
    spawn = [S(sy=0.3, sx=1.7, eye="none", pool=1.0, sac=0), S(sy=0.6, sx=1.25, eye="blink", sac=0.3),
             S(sy=1.3, lean=0.4, lift=1.0, eye="wide", sac=0.7), S(sy=0.78, sx=1.2, eye="squint", sac=1.2), S(sac=1.0)]
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.07] * 6),
             ("Spit", spit, [0.12, 0.12, 0.08, 0.06, 0.14, 0.14])] + tail(idle[0], death, [0.08, 0.12, 0.12, 0.4], knock, spawn)
    return sheet("BlobSpitter", anims, outdir, cell=CELLS["BlobSpitter"], scale=8)


# ================================================================== the family: Gel (1 heart), Brute (2), Titan (3)
def family_face(r, p, R, eye, mouth_open, z, teeth=0, brow=False, grin=0.5, look=1):
    ex, ey = p(R * 0.32, -R * 1.02)
    eyes(r, ex, ey, "brow" if brow else "two", eye, z, gap=max(2.6, R * 0.45), size=2 if R > 7 else 1, look=look)
    mx, my = p(R * 0.5, -R * 0.55)
    if eye == "dead":
        mouth(r, mx, my, max(1.0, R * 0.2), 0, z, smile=-0.6)
    else:
        mouth(r, mx, my, max(1.2, R * 0.25 + mouth_open * 0.3), mouth_open, z, teeth=teeth, smile=grin)


def gel(sy=1.0, lean=0.0, lift=0.0, dx=0.0, ph=0.0, sx=None, eye="open", gape=0.0, slam=0.0, pool=0.0, drops=(),
        pulse=0):
    """Wobbly: a tall crown lobe that lags the body. slam 0..1 throws a gel pseudopod forward and down."""
    r = Rig()
    p = P(sy, lean, lift, dx, ph, sx)
    R = 4.8
    extra = []
    if slam:
        ax, ay = p(R * 0.9, -R * 0.9)
        tx, ty = ax + 3.5 * slam, -0.8 if slam > 0.7 else ay + 2.0 * slam
        for t in (0.35, 0.7, 1.0):
            extra.append((lerp(ax, tx, t), lerp(ay, ty, t), 1.6 + t * 0.4, 1.4))
    if pool: extra.append((dx, -0.6, R * 1.6 * pool, 0.9))
    mask = gel_body(r, p, R, extra, top=0.62, base=1.22)
    heart(r, *p(-R * 0.3, -R * 0.7), 1.2, 0.5, pulse)
    bubbles(r, [p(-R * 0.7, -R * 0.35), p(R * 0.15, -R * 1.45)], 0.6, mask)
    family_face(r, p, R, eye, gape, 1.0)
    for (x, y) in drops: r.dot(x, y, "gel", 3, 2.0)
    return finish(r, [(p(-R * 0.5, -R * 1.55)[0], p(0, -R * 1.55)[1], 1)])


def gel_sheet(outdir):
    G = gel
    idle = [G(), G(sy=0.92, ph=1.6, pulse=1), G(sy=0.96, ph=3.2, eye="blink"), G(sy=1.08, ph=4.7, pulse=1)]
    run = [G(sy=0.72, lean=0.5, ph=0.5), G(sy=1.3, lean=2.0, lift=1, ph=1.2), G(sy=1.1, lean=1.5, lift=3, ph=2.0),
           G(sy=0.95, lift=3.5, ph=2.8), G(sy=1.18, lean=-1.0, lift=1.5, ph=3.6), G(sy=0.68, lean=1.0, ph=4.4)]
    slam = [G(sy=1.12, lean=-1.0, ph=0.5, gape=1.0), G(sy=1.35, lean=-2.0, ph=1.2, eye="wide", gape=1.5, pulse=1),
            G(sy=1.2, lean=2.0, ph=2.0, eye="squint", slam=0.5), G(sy=0.8, sx=1.3, lean=3.0, ph=2.6, eye="squint", slam=1.0, gape=1.0),
            G(sy=0.86, lean=1.5, ph=3.2, slam=0.6), G(sy=1.0, ph=4.0)]
    death = [G(sy=1.25, lean=-1.5, eye="dead", gape=1.5), G(sy=0.6, eye="dead", pool=0.6),
             G(sy=0.35, sx=1.7, eye="none", pool=1.0, drops=[(-7, -2), (7, -2)]), G(sy=0.22, sx=1.9, eye="none", pool=1.2)]
    knock = G(sy=0.88, lean=-2.0, dx=-1, eye="squint", gape=1.0)
    spawn = blob_spawn(G)
    anims = [("Idle", idle, [0.2, 0.16, 0.2, 0.16]), ("Run", run, [0.07] * 6),
             ("Slam", slam, [0.1, 0.12, 0.1, 0.06, 0.16, 0.14])] + tail(idle[0], death, [0.08, 0.12, 0.12, 0.4], knock, spawn)
    return sheet("BlobGel", anims, outdir, cell=CELLS["BlobGel"], scale=8)


def fists(p, R, hand, back, k=1.0):
    """Pseudopod arms ending in fists (balls), from the body's sides to the hand points."""
    out = []
    for (hx, hy), side in ((hand, 1), (back, -1)):
        sx, sy = p(side * R * 0.85, -R * 0.75)
        for t in (0.35, 0.7):
            out.append((lerp(sx, hx, t), lerp(sy, hy, t), 1.5 * k, 1.3 * k))
        out.append((hx, hy, 2.0 * k, 1.8 * k))
    return out


def brute(sy=1.0, lean=0.0, lift=0.0, dx=0.0, ph=0.0, sx=None, eye="open", gape=0.0, hand=(10.0, -5.0), back=(-10.0, -4.5),
          pool=0.0, drops=(), pulse=0, cut=True, quake=0):
    """Two Gels fused: two hearts, rocks it swallowed half sunk in the gel, a bone stuck through, fists."""
    r = Rig()
    p = P(sy * 1.15, lean, lift, dx, ph, sx)
    R = 7.4
    extra = fists(p, R, hand, back) if pool < 0.5 else []
    if pool: extra.append((dx, -0.8, R * 1.5 * pool, 1.2))
    mask = gel_body(r, p, R, extra, top=0.5, base=1.18, cut=cut)
    inner = inset(mask, 1)
    for (u, v) in ((-0.35, -0.6), (0.2, -0.45)):
        heart(r, *p(R * u, R * v), 1.0, 0.5, pulse)
    # rocks: one breaking the surface on the shoulder, two sunk inside (a tone darker)
    for (u, v, rx, ry, sunk) in ((-0.55, -1.25, 2.2, 1.7, False), (0.55, -0.25, 1.6, 1.2, True), (-0.85, -0.3, 1.4, 1.1, True)):
        x, y = p(R * u, R * v)
        r.ell(x, y, rx, ry, "rock", 0.7 if not sunk else 0.45, bias=-0.35 if sunk else 0.1)
    bx, by = p(-R * 0.1, -R * 1.2)
    r.tube([(bx - 2.5, by + 2.0), (bx + 1.5, by - 1.5)], [0.6, 0.6], "bone", 0.5, bias=-0.2)
    r.dot(bx + 2.0, by - 2.0, "bone", 3, 0.8); r.dot(bx + 1.0, by - 2.2, "bone", 3, 0.8)
    bubbles(r, [p(R * 0.1, -R * 1.5), p(-R * 0.9, -R * 0.8)], 0.6, inner)
    family_face(r, p, R, eye, gape, 1.0, teeth=3, brow=True, grin=-0.3)
    for (x, y) in drops: r.dot(x, y, "gel", 3, 2.0)
    if quake:
        for s in (-1, 1):
            for i in range(3):
                r.dot(s * (R + 2 + i * 2.5), -(i % 2) - 1, "gel", 3 if i == 0 else 2, 3.0)
    return finish(r, [(p(-R * 0.55, -R * 1.5)[0], p(0, -R * 1.5)[1], 2)])


def brute_sheet(outdir):
    B = brute
    idle = [B(), B(sy=0.95, ph=1.6, pulse=1, hand=(10.0, -4.6)), B(sy=0.93, ph=3.2, eye="blink", hand=(10.2, -4.4)),
            B(sy=1.03, ph=4.7, pulse=1)]
    run = [B(sy=0.78, lean=0.5, hand=(10.0, -3.0), back=(-10.0, -3.0)), B(sy=1.22, lean=2.0, lift=1, ph=1.2, hand=(11.0, -8.0)),
           B(sy=1.08, lean=1.5, lift=3, ph=2.0, hand=(11.0, -9.0), back=(-11.0, -8.0)), B(sy=0.98, lift=3.5, ph=2.8, hand=(10.5, -8.0)),
           B(sy=1.12, lean=-1.0, lift=1.5, ph=3.6, hand=(10.0, -6.0)), B(sy=0.74, lean=1.0, ph=4.4, hand=(10.5, -2.5))]
    # Slam 7: both fists up (0-2), down (3), HIT on 4 (fists on the floor in front), recover
    slam = [B(sy=1.05, lean=-1.0, hand=(8.0, -11.0), back=(-8.0, -11.0), gape=1.0),
            B(sy=1.2, lean=-2.0, hand=(6.0, -15.0), back=(-4.0, -15.0), eye="wide", gape=2.0, pulse=1),
            B(sy=1.25, lean=-2.5, hand=(5.0, -16.0), back=(-3.0, -16.0), eye="wide", gape=2.5),
            B(sy=1.0, lean=2.0, hand=(13.0, -8.0), back=(4.0, -10.0), eye="squint", gape=1.5),
            B(sy=0.82, sx=1.25, lean=3.0, hand=(13.0, -1.6), back=(7.0, -1.6), eye="squint", gape=2.0, quake=1),
            B(sy=0.9, lean=1.5, hand=(12.0, -2.5), back=(-8.0, -3.0), gape=1.0), B()]
    # Bounce 7: crouch 0, launch 1, airborne 2-4, land 5 (the quake), settle 6
    bounce = [B(sy=0.7, sx=1.25, hand=(10.0, -2.0), back=(-10.0, -2.0), eye="squint"),
              B(sy=1.35, lift=2.0, hand=(8.0, -14.0), back=(-8.0, -14.0), eye="wide", gape=1.5),
              B(sy=1.15, lift=7.0, hand=(9.0, -18.0), back=(-9.0, -18.0), eye="wide", gape=2.0, cut=False),
              B(sy=1.0, lift=9.0, hand=(10.0, -14.0), back=(-10.0, -14.0), eye="open", cut=False),
              B(sy=1.2, lift=4.0, hand=(10.0, -10.0), back=(-10.0, -10.0), eye="squint", gape=1.0),
              B(sy=0.68, sx=1.3, hand=(12.0, -1.6), back=(-12.0, -1.6), eye="squint", gape=2.0, quake=1),
              B(sy=0.92, hand=(10.5, -4.0))]
    death = [B(sy=1.2, lean=-1.5, eye="dead", gape=2.0, hand=(6.0, -12.0), back=(-8.0, -12.0)),
             B(sy=0.6, eye="dead", pool=0.4, hand=(10.0, -1.5), back=(-10.0, -1.5)),
             B(sy=0.35, sx=1.6, eye="none", pool=1.0, drops=[(-12, -2), (12, -3)]), B(sy=0.22, sx=1.8, eye="none", pool=1.2)]
    knock = B(sy=0.9, lean=-2.0, dx=-1, eye="squint", gape=1.5, hand=(7.0, -10.0), back=(-11.0, -8.0))
    spawn = [B(sy=0.3, sx=1.6, eye="none", pool=1.0), B(sy=0.6, sx=1.25, eye="blink", hand=(9.0, -1.6), back=(-9.0, -1.6)),
             B(sy=1.3, lean=0.4, lift=1.0, eye="wide", gape=1.5, hand=(8.0, -15.0), back=(-8.0, -15.0)),
             B(sy=0.78, sx=1.2, eye="squint", hand=(11.0, -2.0)), B()]
    anims = [("Idle", idle, [0.22, 0.18, 0.22, 0.18]), ("Run", run, [0.08] * 6),
             ("Slam", slam, [0.1, 0.1, 0.12, 0.06, 0.06, 0.16, 0.14]),
             ("Bounce", bounce, [0.1, 0.12, 0.08, 0.1, 0.08, 0.08, 0.16])] + tail(idle[0], death, [0.1, 0.12, 0.14, 0.4], knock, spawn)
    return sheet("BlobBrute", anims, outdir, cell=CELLS["BlobBrute"], scale=6)


def plates(r, p, R, raise_, z):
    """Titan's crust: four bone plates over its crown, the gel glowing up through the seams between them."""
    for k, u in enumerate((-0.75, -0.25, 0.25, 0.7)):
        x, y = p(R * u, -R * (1.38 - abs(u) * 0.35))
        y -= raise_ * (1 if k % 2 else 0.5)
        ang = u * 30
        r.ell(x, y, 2.8, 3.3 - abs(u), "plate", z + k * 0.01, ang=ang, bias=0.05)
        r.line(x - 0.6, y - 2.0, x + 0.8, y + 1.0, "plate", z + k * 0.01 + 0.005, tone=1)
    for u in (-0.5, 0.0, 0.48):
        x, y = p(R * u, -R * (1.32 - abs(u) * 0.35))
        r.dot(x, y - 1, "glowg", 3, z + 0.1); r.dot(x, y, "glowg", 2, z + 0.1)


def titan(sy=1.0, lean=0.0, lift=0.0, dx=0.0, ph=0.0, sx=None, eye="open", gape=0.0, hand=(11.0, -6.0), back=(-11.0, -5.0),
          pool=0.0, drops=(), pulse=0, maw=0.0, crest=0.0, quake=0):
    """Three Gels fused: three hearts, a crust of bone plates, a maw that can swallow a hero (maw 0..1 lunges it)."""
    r = Rig()
    p = P(sy * 1.25, lean, lift, dx, ph, sx)
    R = 9.0
    extra = fists(p, R, hand, back, k=1.2) if pool < 0.5 else []
    if maw:
        mx, my = p(R * 0.9, -R * 0.7)
        extra += [(mx + 3.0 * maw, my + 1.0, 3.2, 3.0), (mx + 6.0 * maw, my + 1.5, 3.0, 3.0)]
    if pool: extra.append((dx, -0.8, R * 1.45 * pool, 1.4))
    mask = gel_body(r, p, R, extra, top=0.45, base=1.12)
    inner = inset(mask, 1)
    for (u, v) in ((-0.45, -0.55), (0.05, -0.35), (-0.1, -0.95)):
        heart(r, *p(R * u, R * v), 1.1, 0.5, pulse)
    if pool < 0.5: plates(r, p, R, crest, 0.7)
    for (u, v) in ((-0.8, -0.25), (0.35, -0.2)):
        x, y = p(R * u, R * v)
        r.tube([(x - 1.5, y + 0.5), (x + 1.5, y - 0.5)], [0.6, 0.6], "bone", 0.45, bias=-0.4)
    bubbles(r, [p(R * 0.2, -R * 1.2), p(-R * 0.95, -R * 0.75), p(R * 0.6, -R * 0.35)], 0.6, inner)
    if maw > 0.2:
        x, y = p(R * 0.75, -R * 0.62)
        mouth(r, x + 3.0 * maw, y, 3.0, 2.0 + 3.0 * maw, 1.0, teeth=4)
        ex, ey = p(R * 0.3, -R * 1.02)
        eyes(r, ex + maw, ey, "brow", "wide", 1.05, gap=4.0, size=2)
    else:
        family_face(r, p, R, eye, gape, 1.0, teeth=4, brow=True, grin=-0.4)
    for (x, y) in drops: r.dot(x, y, "gel", 3, 2.0)
    if quake:
        for s in (-1, 1):
            for i in range(3):
                r.dot(s * (R + 2 + i * 2.5), -(i % 2) - 1, "gel", 3 if i == 0 else 2, 3.0)
    return finish(r, [(p(-R * 0.6, -R * 1.25)[0], p(0, -R * 1.25)[1], 2)])


def titan_sheet(outdir):
    T = titan
    idle = [T(), T(sy=0.96, ph=1.6, pulse=1, crest=0.3), T(sy=0.94, ph=3.2, eye="blink", crest=0.6), T(sy=1.02, ph=4.7, pulse=1, crest=0.3)]
    run = [T(sy=0.8, lean=0.5, hand=(13.0, -3.0), back=(-13.0, -3.0)), T(sy=1.18, lean=2.0, lift=1, ph=1.2, hand=(14.0, -10.0)),
           T(sy=1.06, lean=1.5, lift=2.5, ph=2.0, hand=(14.0, -11.0), back=(-14.0, -10.0), crest=1.0),
           T(sy=0.98, lift=3.0, ph=2.8, hand=(13.5, -9.0)), T(sy=1.1, lean=-1.0, lift=1.2, ph=3.6, hand=(13.0, -7.0)),
           T(sy=0.78, lean=1.0, ph=4.4, hand=(13.5, -3.0), crest=0.5)]
    slam = [T(sy=1.05, lean=-1.0, hand=(10.0, -14.0), back=(-10.0, -14.0), gape=1.5),
            T(sy=1.15, lean=-2.0, hand=(7.0, -19.0), back=(-5.0, -19.0), eye="wide", gape=2.5, pulse=1, crest=1.0),
            T(sy=1.2, lean=-2.5, hand=(6.0, -20.0), back=(-4.0, -20.0), eye="wide", gape=3.0, crest=1.5),
            T(sy=1.0, lean=2.0, hand=(17.0, -10.0), back=(6.0, -12.0), eye="squint", gape=2.0),
            T(sy=0.84, sx=1.2, lean=3.0, hand=(17.0, -2.0), back=(9.0, -2.0), eye="squint", gape=2.5, quake=1),
            T(sy=0.88, lean=2.0, hand=(16.0, -2.5), back=(-10.0, -3.0), gape=1.5),
            T(sy=0.95, lean=1.0, hand=(14.0, -4.0), gape=0.5), T()]
    # Engulf 8: rear (0-1), lunge start 2, the maw wide forward (3-4), shut on 5 (grab), pull back (6-7)
    engulf = [T(sy=1.08, lean=-1.5, gape=2.0, hand=(11.0, -12.0), back=(-12.0, -10.0)),
              T(sy=1.2, lean=-2.5, gape=3.0, eye="wide", hand=(9.0, -15.0), back=(-11.0, -13.0), crest=1.0),
              T(sy=0.95, lean=3.0, maw=0.6, hand=(16.0, -6.0), back=(-12.0, -6.0)),
              T(sy=0.9, sx=1.2, lean=4.0, maw=1.0, hand=(18.0, -4.0), back=(-12.0, -4.0)),
              T(sy=0.9, sx=1.2, lean=4.0, maw=1.0, hand=(18.0, -3.0), back=(-12.0, -3.0)),
              T(sy=0.95, sx=1.15, lean=3.0, gape=0.0, eye="squint", hand=(15.0, -4.0), pulse=1),
              T(sy=1.0, lean=1.0, gape=0.0, hand=(13.0, -5.0)), T()]
    death = [T(sy=1.18, lean=-1.5, eye="dead", gape=3.0, hand=(9.0, -16.0), back=(-10.0, -15.0), crest=1.5),
             T(sy=0.62, eye="dead", pool=0.4, hand=(13.0, -1.8), back=(-13.0, -1.8)),
             T(sy=0.35, sx=1.55, eye="none", pool=1.0, drops=[(-15, -2), (15, -3)]), T(sy=0.22, sx=1.7, eye="none", pool=1.2)]
    knock = T(sy=0.9, lean=-2.0, dx=-1, eye="squint", gape=2.0, hand=(9.0, -13.0), back=(-14.0, -10.0))
    spawn = [T(sy=0.3, sx=1.5, eye="none", pool=1.0), T(sy=0.6, sx=1.2, eye="blink", hand=(12.0, -2.0), back=(-12.0, -2.0)),
             T(sy=1.25, lean=0.4, lift=1.0, eye="wide", gape=2.0, hand=(10.0, -17.0), back=(-10.0, -17.0), crest=1.5),
             T(sy=0.8, sx=1.15, eye="squint", hand=(14.0, -2.5)), T()]
    anims = [("Idle", idle, [0.24, 0.2, 0.24, 0.2]), ("Run", run, [0.09] * 6),
             ("Slam", slam, [0.12, 0.12, 0.14, 0.06, 0.07, 0.18, 0.14, 0.14]),
             ("Engulf", engulf, [0.12, 0.14, 0.06, 0.08, 0.08, 0.06, 0.16, 0.16])] + \
        tail(idle[0], death, [0.1, 0.14, 0.16, 0.4], knock, spawn)
    return sheet("BlobTitan", anims, outdir, cell=CELLS["BlobTitan"], scale=5)


# ================================================================== KING: crown and cape
def crown(r, x, y, tilt, z, lost=False):
    T = Xf(tilt, (x, y))
    base = [T(x - 5.0, y), T(x + 5.0, y), T(x + 5.0, y - 2.0), T(x - 5.0, y - 2.0)]
    r.poly(base, "kcrown", z, normal=(-0.2, -0.3, 1.0), curve=0.6)
    for k, u in enumerate((-4.5, -1.5, 1.5, 4.5)):
        h = 3.0 if k in (1, 2) else 2.4
        r.poly([T(x + u - 1.2, y - 1.8), T(x + u, y - 1.8 - h), T(x + u + 1.2, y - 1.8)], "kcrown", z + 0.01,
               normal=(-0.3, -0.5, 1.0))
        r.dot(*T(x + u, y - 1.8 - h - 0.5), "kcrown", 4, z + 0.02)
    for k, u in enumerate((-3.0, 0.0, 3.0)):
        r.dot(*T(x + u, y - 1.0), "ruby" if k != 1 else "emer", 3, z + 0.03)
    r.line(*T(x - 5.0, y - 0.1), *T(x + 5.0, y - 0.1), "kcrown", z + 0.02, tone=1)


def cape(r, p, R, sway, z, pooled=False):
    """A velvet cape slung over the back: an ermine collar at the nape, the hem dragging on the floor behind."""
    top = p(-R * 0.45, -R * 1.42)
    hem = []
    for i in range(6):
        t = i / 5.0
        hem.append((lerp(p(-R * 0.25, 0)[0], p(-R * 1.2, 0)[0] - sway, t), -0.5 - (1.0 if i % 2 else 0.0) * (1 - t)))
    shape = [top, p(-R * 0.05, -R * 1.25), p(-R * 0.2, -R * 0.5)] + hem + [p(-R * 1.15 - sway * 0.5, -R * 0.85),
                                                                          p(-R * 0.95, -R * 1.25)]
    if pooled:
        shape = [(x, min(-0.5, y * 0.25)) for x, y in shape]
    r.poly(shape, "kcape", z, normal=(-0.5, -0.35, 1.0), curve=0.8)
    for i in (1, 2, 4):                              # folds
        x0, y0 = hem[i]
        r.line(x0 + 2.5, y0 - (R * 0.9 if not pooled else 1), x0, y0, "kcape", z + 0.005, tone=1 if i != 2 else 3)
    if not pooled:
        r.tube([p(-R * 0.95, -R * 1.2), top, p(-R * 0.02, -R * 1.3)], [1.2, 1.4, 1.1], "ermine", z + 0.3, bias=0.1)
        for u in (-0.75, -0.3):
            r.dot(*p(R * u, -R * 1.33), "mouth", 0, z + 0.31)


def king(sy=1.0, lean=0.0, lift=0.0, dx=0.0, ph=0.0, sx=None, eye="open", gape=0.0, hand=(15.0, -7.0), back=(-15.0, -6.0),
         pool=0.0, drops=(), pulse=0, sway=0.0, crown_dy=0.0, crown_tilt=0.0, rain=None, quake=0):
    r = Rig()
    p = P(sy * 1.22, lean, lift, dx, ph, sx)
    R = 11.5
    extra = fists(p, R, hand, back, k=1.3) if pool < 0.5 else []
    if pool: extra.append((dx, -0.8, R * 1.45 * pool, 1.5))
    mask = gel_body(r, p, R, extra, top=0.4, base=1.1)
    cape(r, p, R, sway, 0.8, pooled=pool >= 0.5)
    inner = inset(mask, 1)
    for (u, v) in ((-0.5, -0.5), (0.1, -0.35), (-0.15, -0.95), (0.5, -0.8)):
        heart(r, *p(R * u, R * v), 1.1, 0.5, pulse)
    for (u, v) in ((-0.7, -0.3), (0.3, -0.2)):                       # the skulls of its subjects, adrift inside
        x, y = p(R * u, R * v)
        r.ell(x, y, 1.6, 1.4, "bone", 0.45, bias=-0.3)
        r.dot(x + 0.4, y, "gelcore", 0, 0.46); r.dot(x - 0.6, y, "gelcore", 0, 0.46)
    bubbles(r, [p(R * 0.25, -R * 1.25), p(-R * 0.95, -R * 0.75), p(R * 0.7, -R * 0.4)], 0.6, inner)
    if pool < 0.5:
        ex, ey = p(R * 0.32, -R * 1.0)
        eyes(r, ex, ey, "brow", eye, 1.0, gap=4.6, size=2)
        mx, my = p(R * 0.5, -R * 0.55)
        if eye == "dead": mouth(r, mx, my, 2.5, 0, 1.0, smile=-0.8)
        else: mouth(r, mx, my, 3.0 + gape * 0.3, gape, 1.0, teeth=4, smile=1.0)
        cx, cy = p(-R * 0.05, -R * 1.62)
        crown(r, cx, cy + crown_dy, crown_tilt, 2.0)
    else:
        crown(r, 6.0, -1.0, 70, 2.0)                                  # the crown, rolled off into the puddle
    if rain:
        for (x, y, k) in rain:
            r.ell(x, y, 1.4 + k * 0.3, 1.2 + k * 0.3, "glowg", 3.0, flat=1)
    for (x, y) in drops: r.dot(x, y, "gel", 3, 2.0)
    if quake:
        for s in (-1, 1):
            for i in range(3):
                r.dot(s * (R + 3 + i * 2.5), -(i % 2) - 1, "gel", 3 if i == 0 else 2, 3.0)
    return finish(r, [(p(-R * 0.6, -R * 1.2)[0], p(0, -R * 1.2)[1], 2)])


def king_sheet(outdir):
    K = king
    idle = [K(), K(sy=0.97, ph=1.6, pulse=1, sway=0.5), K(sy=0.95, ph=3.2, eye="blink", sway=1.0, crown_dy=0.5),
            K(sy=1.02, ph=4.7, pulse=1, sway=0.5)]
    run = [K(sy=0.82, lean=0.5, hand=(17.0, -3.0), back=(-17.0, -3.0), sway=0.5, crown_dy=0.5),
           K(sy=1.15, lean=2.0, lift=1, ph=1.2, hand=(18.0, -12.0), sway=1.5, crown_dy=-0.5),
           K(sy=1.05, lean=1.5, lift=2.5, ph=2.0, hand=(18.0, -13.0), back=(-18.0, -12.0), sway=2.5, crown_dy=-1.0, crown_tilt=-6),
           K(sy=0.98, lift=3.0, ph=2.8, hand=(17.5, -11.0), sway=2.0),
           K(sy=1.08, lean=-1.0, lift=1.2, ph=3.6, hand=(17.0, -8.0), sway=1.0, crown_tilt=4),
           K(sy=0.8, lean=1.0, ph=4.4, hand=(17.5, -3.0), sway=0.5, crown_dy=1.0)]
    slam = [K(sy=1.04, lean=-1.0, hand=(13.0, -18.0), back=(-13.0, -18.0), gape=2.0),
            K(sy=1.12, lean=-2.0, hand=(9.0, -24.0), back=(-7.0, -24.0), eye="wide", gape=3.0, pulse=1, crown_dy=-1.0),
            K(sy=1.16, lean=-2.5, hand=(8.0, -25.0), back=(-6.0, -25.0), eye="wide", gape=3.5, crown_dy=-1.5, crown_tilt=-8),
            K(sy=1.0, lean=2.0, hand=(22.0, -12.0), back=(8.0, -15.0), eye="squint", gape=2.5, crown_tilt=6),
            K(sy=0.86, sx=1.15, lean=3.0, hand=(22.0, -2.2), back=(12.0, -2.2), eye="squint", gape=3.0, quake=1, crown_dy=1.0),
            K(sy=0.9, lean=2.0, hand=(21.0, -2.6), back=(-14.0, -3.0), gape=2.0, crown_tilt=4),
            K(sy=0.96, lean=1.0, hand=(18.0, -5.0), gape=1.0), K()]
    # Rain 9: rear up 0, swell 1-3, SPEW on 4 (globs flung up), settle 5, watch them fall 6-8
    rain = [K(sy=1.08, lean=-1.0, eye="squint", gape=1.0, hand=(17.0, -12.0), back=(-17.0, -12.0)),
            K(sy=1.16, lean=-1.5, eye="squint", gape=2.0, pulse=1, hand=(15.0, -16.0), back=(-15.0, -16.0)),
            K(sy=1.22, lean=-2.0, eye="wide", gape=3.0, pulse=1, hand=(13.0, -20.0), back=(-13.0, -20.0), crown_dy=-1.0),
            K(sy=1.26, lean=-2.0, eye="wide", gape=4.0, pulse=1, hand=(12.0, -22.0), back=(-12.0, -22.0), crown_dy=-1.5),
            K(sy=0.88, sx=1.15, lean=1.5, eye="wide", gape=5.0, hand=(19.0, -6.0), back=(-19.0, -6.0),
              rain=[(10.0, -34.0, 1), (16.0, -38.0, 0), (4.0, -38.0, 0)], crown_dy=1.0),
            K(sy=0.92, lean=1.0, gape=3.0, rain=[(12.0, -42.0, 0), (19.0, -45.0, 0), (5.0, -46.0, 0)]),
            K(sy=1.0, gape=1.5),
            K(sy=1.02, gape=1.0, pulse=1), K()]
    death = [K(sy=1.15, lean=-1.5, eye="dead", gape=4.0, hand=(12.0, -20.0), back=(-12.0, -20.0), crown_dy=-3.0, crown_tilt=-20),
             K(sy=0.62, eye="dead", pool=0.4, hand=(17.0, -2.0), back=(-17.0, -2.0), crown_tilt=30),
             K(sy=0.35, sx=1.5, eye="none", pool=1.0, drops=[(-20, -2), (20, -3)]), K(sy=0.22, sx=1.6, eye="none", pool=1.2)]
    knock = K(sy=0.9, lean=-2.0, dx=-1, eye="squint", gape=2.5, hand=(12.0, -16.0), back=(-18.0, -13.0), crown_tilt=-12)
    spawn = [K(sy=0.3, sx=1.45, eye="none", pool=1.0), K(sy=0.6, sx=1.2, eye="blink", hand=(16.0, -2.0), back=(-16.0, -2.0)),
             K(sy=1.22, lean=0.4, lift=1.0, eye="wide", gape=3.0, hand=(13.0, -22.0), back=(-13.0, -22.0), crown_dy=-2.0),
             K(sy=0.82, sx=1.12, eye="squint", hand=(18.0, -3.0), crown_dy=1.0), K()]
    anims = [("Idle", idle, [0.26, 0.22, 0.26, 0.22]), ("Run", run, [0.1] * 6),
             ("Slam", slam, [0.12, 0.14, 0.16, 0.06, 0.08, 0.2, 0.16, 0.14]),
             ("Rain", rain, [0.14, 0.14, 0.14, 0.12, 0.08, 0.14, 0.14, 0.14, 0.16])] + \
        tail(idle[0], death, [0.12, 0.14, 0.16, 0.5], knock, spawn)
    return sheet("BlobKing", anims, outdir, cell=CELLS["BlobKing"], scale=4)


JOBS = [("BlobMote", mote_sheet), ("BlobSpitter", spitter_sheet), ("BlobGel", gel_sheet), ("BlobBrute", brute_sheet),
        ("BlobTitan", titan_sheet), ("BlobKing", king_sheet)]


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    only = None
    if "--only" in a:
        i = a.index("--only"); only = set(a[i + 1].split(",")); del a[i:i + 2]
    outdir = a[0] if a else OUT
    os.makedirs(outdir, exist_ok=True)
    for n, fn in JOBS:
        if only is None or n in only: fn(outdir)


if __name__ == "__main__":
    main()
