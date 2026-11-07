"""UMBRAEL, THE HOLLOW MIRROR: every sprite sheet for the god pack.

Monsters (rigged, every frame its own pose): UmbShadeImp, UmbGlimmer, UmbGloomLurker (T1),
UmbTwinned, UmbMirrorWitch (T2), UmbHollowKing (T3).
FX: FxMirrorShard, FxDarkness, FxShadowPuff, FxReflectBolt, FxSwapFlash, FxDecoyBurst, FxEchoMark.
Items: IconMirrorStep, IconHollowCrown. God portrait: DeityUmbrael.

Usage: python3 umbrael_rigs.py [outdir] [SheetName ...]
"""
import math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from rig import Part, Canvas, line_px
from anim import Spr, pack, preview, PALETTE
import scalekit as SK

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "art/out_umbrael")
PREVIEW_SCALE = 5

# ------------------------------------------------------------------------------------------------
# shared helpers
# ------------------------------------------------------------------------------------------------
DARK = set("qmKn")
# lit-edge ramp: what a body pixel becomes when it sits on the top/left (moonlit) silhouette edge
EDGE_TOP = {'q': 'n', 'm': 's', 'K': 'q', 'n': 'N', 's': 'S', 'N': 'U'}
EDGE_PALE = {'n': 'U', 'N': 'u', 's': 'U', 'S': 'u', 'q': 'N', 'm': 'S'}


def rimlight(spr, pale_every=1, skip=""):
    """Moonlight rim: pixels whose upper neighbour is empty get one step lighter; pixels open both
    above and to the left (top-left corners) get the pale highlight. Keeps shadow bodies readable."""
    px = dict(spr.px)
    out = dict(px)
    for (x, y), c in px.items():
        if c in skip:
            continue
        up = (x, y - 1) not in px
        left = (x - 1, y) not in px
        if up and left and c in EDGE_PALE and ((x + y) % pale_every == 0):
            out[(x, y)] = EDGE_PALE[c]
        elif up and c in EDGE_TOP:
            out[(x, y)] = EDGE_TOP[c]
    return Spr(out)


def hsh(x, y, seed=0):
    h = (x * 73856093) ^ (y * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def dissolve(spr, k, seed=0, rise=2, smoke="sSN", spread=1):
    """Fade into smoke: k=0 full body, k=1 nothing left. Lost pixels drift up as smoke flecks."""
    out = {}
    smk = {}
    for (x, y), c in spr.px.items():
        h = hsh(x, y, seed)
        if h >= k:
            # pixels about to go darken first (body thins out)
            out[(x, y)] = ('q' if c in 'nmK' else 'n' if c in 'NUu' else c) if h < k + 0.15 else c
        elif h > k - 0.35 and (x + 2 * y + seed) % 3 == 0:
            sx = x + int(round((hsh(y, x, seed + 1) - 0.5) * 2 * spread))
            sy = y - rise - int(hsh(x, y, seed + 2) * rise)
            smk[(sx, sy)] = smoke[int(hsh(x, x + y, seed) * len(smoke)) % len(smoke)]
    for kk, v in smk.items():
        if kk[1] <= 0:
            out.setdefault(kk, v)
    return Spr(out)


def recolor_shadow(spr, ramp=("q", "m", "n", "N")):
    """Echo/afterimage tint: map every colour onto a 4-step dark violet ramp by luminance."""
    def lum(c):
        r, g, b = PALETTE[c]
        return 0.3 * r + 0.59 * g + 0.11 * b
    out = {}
    for k, c in spr.px.items():
        l = lum(c)
        i = 0 if l < 45 else 1 if l < 75 else 2 if l < 140 else 3
        out[k] = ramp[i]
    return Spr(out)


def rot_ccw(spr):
    """Lay a figure on its back (head to the left), then sit it on the ground line."""
    s = Spr({(y, -x): c for (x, y), c in spr.px.items()})
    b = s.bbox()
    return s.shift(-((b[0] + b[2]) // 2), -b[3])


def ground(spr):
    """Drop anything that dipped below the ground line (y>0)."""
    return Spr({k: v for k, v in spr.px.items() if k[1] <= 0})


def ellipse_px(cx, cy, rx, ry, fill, rim=None, hi=None, rim_t=0.62, jitter=0.0, seed=0):
    px = {}
    for y in range(int(math.floor(cy - ry - 1)), int(math.ceil(cy + ry + 2))):
        for x in range(int(math.floor(cx - rx - 1)), int(math.ceil(cx + rx + 2))):
            j = (hsh(x, y, seed) - 0.5) * jitter
            d = ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 + j
            if d <= 1.0:
                c = fill
                if rim and d > rim_t: c = rim
                if hi and d < 0.3 and y < cy and x < cx + rx * 0.2: c = hi
                px[(x, y)] = c
    return px


def poly_px(pts, fill, rim=None):
    px = {}
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]; xj, yj = pts[j]
                if ((yi > y + 0.5) != (yj > y + 0.5)) and (x + 0.5 < (xj - xi) * (y + 0.5 - yi) / (yj - yi + 1e-9) + xi):
                    inside = not inside
                j = i
            if inside:
                px[(x, y)] = fill
    if rim:
        for (x, y), c in list(px.items()):
            if any((x + dx, y + dy) not in px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[(x, y)] = rim
    return px


def arc_px(cx, cy, r, a0, a1, cols=("c", "u", "U", "N"), thick=1, squash=1.0):
    """Slash arc from angle a0 to a1 (deg). The leading end (a1) is brightest; the tail fades."""
    px = {}
    n = max(2, int(abs(a1 - a0) / 6))
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        ci = min(len(cols) - 1, int((1 - t) * len(cols)))
        for w in range(thick):
            rr = r - w
            x = int(round(cx + rr * math.cos(a))); y = int(round(cy + rr * math.sin(a) * squash))
            c = cols[min(len(cols) - 1, ci + (1 if w else 0))]
            if (x, y) not in px or w == 0:
                px[(x, y)] = c
    return px


def put_px(c, px, over=True):
    """px is already in pixels (the generators below render at the current design scale)."""
    c = getattr(c, "raw", c)
    for (x, y), v in px.items():
        c.put(x, y, v, over)


def limb_pts(x, y, segs):
    pts = [(x, y)]
    cx, cy = float(x), float(y)
    for ln, ang in segs:
        a = math.radians(ang)
        cx += ln * math.cos(a); cy += ln * math.sin(a)
        pts.append((int(round(cx)), int(round(cy))))
    return pts


def report(name, anims):
    bad = []
    for an, frames, _ in anims:
        for i, f in enumerate(frames):
            if any(k[1] > 0 for k in f.px):
                bad.append("%s[%d]" % (an, i))
            for v in f.px.values() if not hasattr(f, "to_rgba") or type(f).__name__ == "Spr" else []:
                if v not in PALETTE:
                    raise ValueError("%s %s: bad palette char %r" % (name, an, v))
    if bad:
        print("WARNING %s: pixels below ground in %s" % (name, ", ".join(bad)))


def cell_for(frames, pad_x=3, pad_top=3):
    x0 = min(f.bbox()[0] for f in frames); x1 = max(f.bbox()[2] for f in frames)
    y0 = min(f.bbox()[1] for f in frames)
    hw = max(-x0, x1) + pad_x
    w = 2 * hw
    h = -y0 + pad_top + 2
    return w, h


def edge_pass(spr, ramp=None):
    """Silhouette pass: any near-black pixel on the outer edge is lifted one step, so the shadow
    side of a creature never melts into Crawl's dark floor."""
    ramp = ramp or {"q": "n", "m": "s", "K": "q"}
    out = dict(spr.px)
    for (x, y), c in spr.px.items():
        if c in ramp and any((x + dx, y + dy) not in spr.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            out[(x, y)] = ramp[c]
    return Spr(out)


def finish(anims):
    """Apply the silhouette pass to every monster frame (statues are already stone-tinted)."""
    out = []
    for an, frames, durs in anims:
        skip = an == "Echo"      # the echo must stay in the dark violets only
        out.append((an, [f if (skip or type(f).__name__ != "Spr") else edge_pass(f) for f in frames], durs))
    return out


# ------------------------------------------------------------------------------------------------
# v0.8 value + identity pass. The whole line was one dark violet (Idle luminance mean 62-85 against vanilla ~100) and
# the Gloom Lurker, Twinned, Nailshade and Gloamcoil blurred together. Every sheet keeps the dark-violet identity but
# its shadow ramp is lifted, and each of the four gets its own accent: the Lurker is cold slate-blue with teal eyes,
# the Twinned is a dark twin and its pale silver reflection (see twinned()), the Nailshade is plum-rose with
# rose-glowing eyes, the Gloamcoil is deep indigo with amber eyes and gold belly scutes.
# Remaps run after the silhouette pass, on every frame except the stone Statue.
PALETTE.update({
    "uq": (0x4c, 0x34, 0x68), "um": (0x44, 0x3e, 0x56), "un": (0x7c, 0x48, 0xa2), "uN": (0xb0, 0x78, 0xdc),
    # Gloom Lurker
    "lq": (0x26, 0x32, 0x56), "lm": (0x2c, 0x34, 0x4a), "ln": (0x42, 0x6c, 0xa4), "lN": (0x7c, 0xaa, 0xe2),
    "lU": (0xa8, 0xd0, 0xf0), "lc": (0x74, 0xff, 0xe0), "lB": (0x2e, 0xc4, 0xb0),
    # Twinned: the pale reflection
    "tq": (0x86, 0x7c, 0xa8), "tn": (0xb8, 0xb0, 0xda), "tN": (0xe6, 0xe0, 0xfa), "tm": (0x60, 0x5a, 0x84),
    "tK": (0x3a, 0x34, 0x54),
    # Nailshade
    "pq": (0x5a, 0x24, 0x52), "pm": (0x44, 0x2a, 0x3e), "pn": (0x8e, 0x34, 0x78), "pN": (0xd4, 0x66, 0xac),
    "pc": (0xff, 0xb4, 0xde),
    # Gloamcoil
    "gq": (0x34, 0x2e, 0x6a), "gm": (0x38, 0x34, 0x54), "gn": (0x5c, 0x4c, 0xa8), "gN": (0x8e, 0x78, 0xd4),
    "gc": (0xff, 0xb8, 0x40), "gb": (0xc8, 0xa0, 0x44),
})
TONE_BASE = {"q": "uq", "m": "um", "n": "un", "N": "uN"}
TONE_MAPS = {
    # v0.10: the Mirror Witch wears the Gloom Lurker's slate blue (its mirror stays the Glimmer's glass)
    "UmbShadeImp": TONE_BASE, "UmbMirrorWitch": {"q": "lq", "m": "lm", "n": "ln", "N": "lN"},
    "UmbHollowKing": {"q": "uq", "m": "um", "n": "un", "N": "tn"},   # v0.10: the Twinned's pale silver (was Nailshade rose)
    "UmbTwinned": TONE_BASE,
    "UmbGloomLurker": {"q": "lq", "m": "lm", "n": "ln", "N": "lN", "U": "lU", "c": "lc", "B": "lB"},
    "UmbNailshade": {"q": "pq", "m": "pm", "n": "pn", "N": "pN", "c": "pc"},
    "UmbGloamcoil": {"q": "gq", "m": "gm", "n": "gn", "N": "gN", "c": "lc"},   # v0.9: the Gloom Lurker's teal eyes
    # v0.9 lineage: the Eclipse Wyrm's void body is the Gloamcoil's indigo (gold scutes, teal eye); the glass head is the
    # Twinned's pale reflection. The Hollow King and the Glass Seraph take the Nailshade's rose; the Unblinking's
    # tendrils are Gloamcoil serpents (indigo, gold scutes).
    "UmbEclipseWyrm": {"q": "gq", "m": "gm", "n": "gn", "N": "gN", "c": "lc"},
    "UmbGlassSeraph": {"N": "pN", "n": "pn"},
    # v0.10: the Unblinking's only parent is the Mirror Witch: her slate blue with teal-tipped tendrils (was the
    # Gloamcoil's indigo with gold scutes); the Eclipse Wyrm's only parent is the Gloamcoil: its glass head is now the
    # slate-blue of the Gloamcoil's Lurker legs (was the Twinned's pale silver).
    "UmbUnblinking": {"q": "lq", "m": "lm", "n": "ln", "N": "lN"},
}


def tone_frames(name, anims):
    mp = TONE_MAPS.get(name)
    if not mp:
        return anims
    out = []
    for an, frames, durs in anims:
        out.append((an, [f if type(f).__name__ != "Spr" else Spr({k: mp.get(v, v) for k, v in f.px.items()}) for f in frames],
                    durs))
    return out


def build_sheet(name, anims, outdir, cell=None, scale=PREVIEW_SCALE, edge=True):
    if edge:
        anims = finish(anims)
    anims = tone_frames(name, anims)
    report(name, anims)
    allf = [f for a in anims for f in a[1]]
    for an, frames, durs in anims:
        assert durs is not None and len(durs) == len(frames), (name, an)
    w, h = cell or cell_for(allf)
    img, man = pack(name, anims, w, h, (w // 2, h - 2), outdir)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    print("built %-16s cell %dx%d  %s" % (name, w, h, ", ".join("%s:%d" % (a[0], len(a[1])) for a in anims)))
    return img, man, (w, h)


SHEETS = {}   # name -> builder(outdir) ; filled below
CELLS = {}    # name -> (w, h) for TIMING.md


def sheet(fn):
    SHEETS[fn.__name__.replace("build_", "")] = fn
    return fn


# ================================================================================================
# 1. SHADE IMP (T1): wiry black imp, long claws, one white eye, smoky tail
# ================================================================================================
IMP_HEAD = {
    "calm": Part("""
n.......
.q...n..
.qqqnn..
qqqqqqq.
qqqqucq.
qqqqqqqU
.qqUuUu.
""", (2, 6)),
    "snarl": Part("""
n.......
.q...n..
.qqqnn..
qqqqqqq.
qqqqucq.
qqqqqqqq
.qqUqqUu
..qUuUu.
""", (2, 7)),
    "low": Part("""
........
n.......
.q...n..
qqqqnn..
qqqqqqq.
qqqqqucq
.qqUuUuU
""", (2, 6)),
    "hurt": Part("""
...q....
n.q.....
.qqqn...
qqqqqqq.
qqqqUsq.
qqqqqqq.
.qqqqq..
""", (2, 6)),
}
IMP_TORSO = {
    "hunch": Part("""
....nnn
..qqqqq
.qqqqqq
qqqqqq.
qqqqq..
.qqqq..
..qq...
""", (2, 6)),
    "low": Part("""
.....nnn
..nqqqqq
.qqqqqqq
qqqqqqq.
.qqqqq..
..qq....
""", (2, 5)),
    "up": Part("""
...nnn.
...qqqq
..qqqqq
.qqqqq.
.qqqqq.
..qqqq.
..qqq..
...q...
""", (3, 7)),
}
IMP_SHOULDER = {"hunch": (3, -5), "low": (4, -4), "up": (3, -6)}
IMP_NECK = {"hunch": (4, -5), "low": (5, -4), "up": (3, -7)}
IMP_FOOT = Part("nnU", (0, 0))
IMP_FOOT_B = Part("qqn", (0, 0))


def imp_claws(c, x, y, ang, col="u", n=2, ln=2, spread=30):
    for i in range(n):
        a = ang + (i - (n - 1) / 2.0) * spread
        c.limb(x, y, [(ln, a)], [col if i != n - 1 else "U"])


def imp_tail(c, x, y, phase, curl=0):
    """Smoky tail: a whip of dark segments ending in a puff that breathes with the phase."""
    w = math.sin(phase * math.pi / 2)
    ex, ey = c.limb(x, y, [(3, 165 + curl), (3, 205 + 18 * w + curl), (3, 250 + 20 * w + curl)], ["q", "q", "n"])
    puffs = [((0, 0), "S"), ((-1, -1), "s"), ((1, -1), "s"), ((0, -2), "S"), ((-1, -3), "s"), ((1, -4), "m")]
    for i, ((dx, dy), col) in enumerate(puffs):
        if (i + phase) % 4 != 3:
            c.put(ex + dx + (phase % 2 if i > 2 else 0), ey + dy, col, over=False)


def imp(torso="hunch", head="calm", dx=0, dy=0, legs=((120, 60), (60, 110)),
        arms=((80, 60), (70, 40)), claws=(None, None), big=(False, False), tail=0, tail_curl=0,
        extra=None, head_off=(0, 0)):
    """legs/arms: ((upper, lower) back, (upper, lower) front). claws: claw angle override;
    big: draw the long 3-blade rake claws (attacks) instead of the 2 short resting claws."""
    c = Canvas()
    hip = (dx, -7 + dy)
    sh = (hip[0] + IMP_SHOULDER[torso][0], hip[1] + IMP_SHOULDER[torso][1])
    imp_tail(c, hip[0] - 2, hip[1] - 1, tail, tail_curl)
    # back limbs (darker)
    c.limb(hip[0] - 1, hip[1], [(4, legs[0][0]), (3, legs[0][1])], [("q", "q"), "q"], width=2, end=IMP_FOOT_B)
    hx, hy = c.limb(sh[0] - 1, sh[1] + 1, [(3, arms[0][0]), (4, arms[0][1])], ["q", "q"])
    ca = claws[0] if claws[0] is not None else arms[0][1]
    imp_claws(c, hx, hy, ca, col="U", n=3 if big[0] else 2, ln=4 if big[0] else 2, spread=20 if big[0] else 30)
    c.part(IMP_TORSO[torso], hip[0], hip[1])
    nx, ny = hip[0] + IMP_NECK[torso][0] + head_off[0], hip[1] + IMP_NECK[torso][1] + head_off[1]
    c.part(IMP_HEAD[head], nx, ny)
    # front limbs
    c.limb(hip[0] + 1, hip[1], [(4, legs[1][0]), (3, legs[1][1])], [("n", "q"), "n"], width=2, end=IMP_FOOT)
    hx, hy = c.limb(sh[0], sh[1] + 1, [(3, arms[1][0]), (4, arms[1][1])], ["n", "n"])
    ca = claws[1] if claws[1] is not None else arms[1][1]
    imp_claws(c, hx, hy, ca, col="u", n=3 if big[1] else 2, ln=4 if big[1] else 2, spread=20 if big[1] else 30)
    s = rimlight(c.spr(), skip="uUcSs")
    if extra:
        s = s.copy()
        for item in extra:
            if isinstance(item, dict): s.px.update(item)
    return s


def slash(cx, cy, r, a0, a1, squash=1.0, thick=2, cols=("c", "u", "U", "N")):
    return arc_px(cx, cy, r, a0, a1, cols=cols, thick=thick, squash=squash)


@sheet
def build_UmbShadeImp(outdir):
    T = True
    idle = [imp(dy=[0, 0, 1, 1][i], tail=i, head=["calm", "calm", "low", "calm"][i],
                arms=((85 + 5 * (i % 2), 60), (70 - 6 * (i % 2), 40 + 10 * (i % 2))),
                legs=((120, 60 + 6 * (i >= 2)), (60 - 6 * (i >= 2), 110))) for i in range(4)]
    cyc = [((150, 95), (35, 80)), ((125, 70), (70, 120)), ((95, 60), (100, 120)),
           ((35, 80), (150, 95)), ((70, 120), (125, 70)), ((100, 120), (95, 60))]
    run = []
    for i, (lb, lf) in enumerate(cyc):
        sw = 40 if i < 3 else -40
        run.append(imp(torso="low", head="calm", dy=-1 if i in (0, 3) else 0, legs=(lb, lf), tail=i,
                       tail_curl=15, arms=((90 + sw, 60 + sw), (70 - sw, 40 - sw))))
    # Rake: cock both arms (2 frames), hit 1 front claw down, switch, hit 2 back claw up, follow, recover
    rake = [
        imp(torso="up", head="snarl", dx=-1, legs=((130, 70), (60, 120)), arms=((-120, -90), (-110, -70)), big=(T, T), tail=0),
        imp(torso="up", head="snarl", dx=-2, dy=1, legs=((150, 70), (45, 130)), arms=((-150, -120), (-140, -105)), big=(T, T), tail=1),
        imp(torso="low", head="snarl", dx=2, legs=((165, 115), (30, 90)), arms=((-130, -90), (20, 60)), big=(T, T), tail=2,
            extra=[slash(8, -10, 7, -80, 55)]),
        imp(torso="low", head="calm", dx=2, legs=((160, 110), (30, 90)), arms=((-70, -20), (100, 150)), big=(T, False), tail=3),
        imp(torso="low", head="snarl", dx=3, legs=((155, 100), (25, 85)), arms=((0, -30), (110, 160)), big=(T, False), tail=0,
            extra=[slash(8, -8, 7, 70, -65)]),
        imp(torso="low", head="calm", dx=2, legs=((145, 90), (40, 100)), arms=((50, 80), (100, 150)), tail=1),
        imp(torso="hunch", head="calm", dx=1, legs=((125, 65), (55, 110)), arms=((85, 60), (70, 40)), tail=2),
    ]
    # Shadowstep: rise, crouch into smoke, dissolve, vanish (frame 4: teleport), gather, lunge out (frame 7), recover
    crouch = imp(torso="low", head="low", dy=2, legs=((170, 40), (15, 150)), arms=((100, 150), (80, 140)), tail=0)
    lunge = imp(torso="low", head="snarl", dx=3, legs=((175, 140), (20, 70)), arms=((-60, -20), (-20, 10)), big=(T, T), tail=2)
    step = [
        imp(torso="up", head="low", dx=-1, legs=((130, 70), (60, 120)), arms=((140, 110), (120, 100)), tail=3),
        crouch,
        dissolve(crouch, 0.45, seed=3, rise=2),
        dissolve(crouch, 0.8, seed=3, rise=4, smoke="sSm"),
        dissolve(crouch.shift(0, SK.Si(2)), 0.985, seed=5, rise=6, smoke="sm"),
        dissolve(lunge, 0.8, seed=7, rise=-1, smoke="sSN"),
        dissolve(lunge, 0.4, seed=7, rise=-1),
        imp(torso="low", head="snarl", dx=4, legs=((175, 150), (15, 60)), arms=((-40, 0), (10, 40)), big=(T, T), tail=3,
            extra=[slash(10, -9, 7, -70, 60)]),
        imp(torso="low", head="calm", dx=3, legs=((155, 100), (30, 90)), arms=((40, 90), (70, 120)), tail=0),
        imp(torso="hunch", head="calm", dx=1, legs=((125, 65), (55, 110)), arms=((85, 60), (70, 40)), tail=1),
    ]
    corpse = Spr.parse("""
...............n...
.m.........n..qn...
s.q...nnnnnqqqqqn..
.q..nqqqqqqqqqqqqn.
..qqqqqqqqqqqqqsqqU
...nqqUqqqUqqqUqUuU
""", feet_x=9)
    corpse = SK.carve_spr(corpse)
    slumped = Spr.parse("""
........nn.........
......nqqqn..n.....
.s....qqqqqqqn.....
s.q..nqqqqqqqqqn...
.q..nqqqqqqqqqqqn..
..qqqqqqqqqqqqqsqU.
...nqqUqqqUqqqqUuUu
""", feet_x=9)
    slumped = SK.carve_spr(slumped)
    death = [
        imp(torso="up", head="hurt", dx=-2, legs=((115, 80), (75, 110)), arms=((-120, -80), (-140, -100)), tail=0),
        imp(torso="hunch", head="hurt", dx=-2, dy=2, legs=((165, 50), (25, 155)), arms=((150, 120), (120, 100)), tail=1),
        slumped.over(Spr(SK.lit({(-6, -8): "S", (1, -9): "s", (4, -10): "s", (-2, -11): "m"}))),
        corpse,
    ]
    knock = [imp(torso="up", head="hurt", dx=-2, legs=((110, 70), (80, 120)), arms=((-150, -120), (-120, -90)), tail=3, tail_curl=-20)]
    anims = [
        ("Idle", idle, [0.16, 0.14, 0.18, 0.14]),
        ("Run", run, [0.07] * 6),
        ("Death", death, [0.1, 0.12, 0.14, 0.3]),
        ("Dead", [corpse], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Rake", rake, [0.12, 0.12, 0.05, 0.07, 0.05, 0.1, 0.12]),
        ("Step", step, [0.1, 0.12, 0.06, 0.06, 0.12, 0.06, 0.06, 0.05, 0.1, 0.12]),
    ]
    return build_sheet("UmbShadeImp", anims, outdir)


# ================================================================================================
# 2. GLIMMER (T1 flier): floating shard of black mirror, one eye, little crystal wings
# ================================================================================================
def rot_pt(p, ang, about=(0, 0)):
    a = math.radians(ang)
    x, y = p[0] - about[0], p[1] - about[1]
    return (about[0] + x * math.cos(a) - y * math.sin(a), about[1] + x * math.sin(a) + y * math.cos(a))


KITE = [(0.2, -7.5), (4.2, -1.5), (0.5, 6.5), (-3.8, -0.5)]


def mirror_shard(cx, cy, tilt, glint=0.0, scale=1.35, cracks=0, eye="open", glow=False, body="q"):
    """The mirror body: dark glass kite, lit top-left rim, moving glint band, single eye."""
    pts = [rot_pt((cx + p[0] * scale, cy + p[1] * scale), tilt, (cx, cy)) for p in KITE]
    px = poly_px(pts, body)
    for (x, y) in list(px):
        nb = lambda dx, dy: (x + dx, y + dy) in px
        if not nb(0, -1) or not nb(-1, 0):
            px[(x, y)] = "u" if (not nb(0, -1) and not nb(-1, 0)) else "U"
        elif not nb(0, 1) or not nb(1, 0):
            px[(x, y)] = "n"
        else:
            # interior: subtle second shade on the lower half, glint band sweeping across
            d = (x - cx) * 0.9 + (y - cy) * 0.55 - glint
            if abs(d) < 0.6: px[(x, y)] = "c" if glow else "B"
            elif abs(d) < 1.4: px[(x, y)] = "b"
            elif y > cy + 1: px[(x, y)] = "m" if body == "q" else body
    # eye (sits a little above centre, toward the facing side)
    ex, ey = rot_pt((cx + 0.6, cy - 1), tilt, (cx, cy))
    ex, ey = int(round(ex)), int(round(ey))
    if eye == "open":
        for (ox, oy, col) in ((-1, 0, "U"), (0, 0, "c"), (1, 0, "X" if glow else "c"), (2, 0, "U"),
                              (0, -1, "U"), (1, -1, "u"), (0, 1, "n"), (1, 1, "U")):
            px[(ex + ox, ey + oy)] = col
    elif eye == "glare":
        for (ox, oy, col) in ((-1, 0, "u"), (0, 0, "X"), (1, 0, "X"), (2, 0, "c"),
                              (0, -1, "c"), (1, -1, "c"), (0, 1, "u"), (1, 1, "u")):
            px[(ex + ox, ey + oy)] = col
    elif eye == "shut":
        for (ox, oy, col) in ((-1, 0, "n"), (0, 0, "U"), (1, 0, "U"), (2, 0, "n")):
            px[(ex + ox, ey + oy)] = col
    if cracks:
        rnd = random.Random(11)
        dirs = [-70, 20, 130, 200, -20, 95][:cracks + 1]
        for k, d in enumerate(dirs):
            x, y = ex, ey
            for st in range(3 + cracks):
                d += rnd.uniform(-35, 35)
                x += math.cos(math.radians(d)); y += math.sin(math.radians(d))
                kk = (int(round(x)), int(round(y)))
                if kk in px: px[kk] = "c" if st < 2 else "u"
    return px


def crystal_wing(root, ang, length, back=False):
    """Small crystal wing: a thin triangle fanned from the root at angle `ang`."""
    a = math.radians(ang)
    tip = (root[0] + length * math.cos(a), root[1] + length * math.sin(a))
    side = (root[0] + length * 0.55 * math.cos(a + 0.75), root[1] + length * 0.55 * math.sin(a + 0.75))
    px = poly_px([root, tip, side], "b" if back else "B")
    for k in list(px):
        if (k[0] + k[1]) % 3 == 0 and not back: px[k] = "c"
    tx, ty = int(round(tip[0])), int(round(tip[1]))
    px[(tx, ty)] = "U" if back else "c"
    for p in line_px(int(root[0]), int(root[1]), tx, ty):
        px[p] = "b" if back else "u"
    return px


FLAP = [-150, -120, -95, -120]
GLIM_HOVER_DROP = 2


def glimmer(tilt=0, flap=0, bob=0, dx=0, glint=0.0, eye="open", glow=False, cracks=0, extra=(), hover=10, body="q"):
    c = Canvas()
    if SK.small() and hover >= 6:   # small render: hover 2 px lower (flying height counts toward the size limit)
        hover -= GLIM_HOVER_DROP
    cx, cy = dx, -hover + bob
    fa = FLAP[flap % 4] if isinstance(flap, int) else flap
    # both wings grow from the back edge of the shard: far wing darker, near wing bright crystal
    put_px(c, crystal_wing(rot_pt((cx - 1, cy - 4), tilt, (cx, cy)), fa + tilt + 30, 6, back=True))
    put_px(c, crystal_wing(rot_pt((cx - 3, cy - 2), tilt, (cx, cy)), fa + tilt - 5, 7))
    put_px(c, mirror_shard(cx, cy, tilt, glint=glint, cracks=cracks, eye=eye, glow=glow, body=body))
    for item in extra:
        put_px(c, item)
    return c.spr()


def small_shard(x, y, ang, size=3, cols=("c", "B", "b")):
    """A loose glass sliver (projectile / debris)."""
    px = {}
    a = math.radians(ang)
    for i in range(size):
        px[(int(round(x + i * math.cos(a))), int(round(y + i * math.sin(a))))] = cols[min(i, len(cols) - 1)]
    px[(int(round(x - math.sin(a))), int(round(y + math.cos(a))))] = cols[-1]
    return px


def sparkle(x, y, big=False):
    px = {(x, y): "X" if big else "c", (x - 1, y): "u", (x + 1, y): "u", (x, y - 1): "u", (x, y + 1): "u"}
    if big:
        px.update({(x - 2, y): "U", (x + 2, y): "U", (x, y - 2): "U", (x, y + 2): "U"})
    return px


def decoy(spr, k=0.0, seed=0):
    """Mirror-image decoy: violet glass copy, optionally breaking apart."""
    d = recolor_shadow(spr, ramp=("q", "n", "N", "U"))
    return dissolve(d, k, seed=seed, rise=1, smoke="NUu") if k > 0 else d


@sheet
def build_UmbGlimmer(outdir):
    return build_sheet("UmbGlimmer", glimmer_anims(), outdir)


def glimmer_anims():
    idle = [glimmer(flap=i, bob=[0, -1, -1, 0][i], glint=[-5, -2, 2, 5][i], tilt=[0, 2, 0, -2][i]) for i in range(4)]
    run = [glimmer(flap=i, tilt=18, bob=[0, -1, -2, -1, 0, 1][i] // 1, glint=[-3, 0, 3, -3, 0, 3][i], dx=1) for i in range(6)]
    # Shard: rear back + glare (2 frames), release (frame 2: the shard leaves the front tip), recoil, settle
    shard = [
        glimmer(tilt=-15, flap=0, bob=-1, eye="glare", glint=-2),
        glimmer(tilt=-28, flap=1, bob=-2, dx=-1, eye="glare", glint=1, glow=True, extra=[sparkle(4, -15)]),
        glimmer(tilt=22, flap=3, bob=0, dx=1, eye="glare", glint=3, extra=[small_shard(10, -10, 180, 4), SK.lit({(13, -10): "c", (14, -10): "u"})]),
        glimmer(tilt=12, flap=2, bob=0, dx=1, glint=4),
        glimmer(tilt=4, flap=1, bob=-1, glint=-3),
        glimmer(tilt=0, flap=0, bob=0, glint=-1),
    ]
    # Split: shiver, glow, crack-flash, decoys appear (frame 3), decoys drift + settle, recover
    base = glimmer(flap=2, glint=0)
    split = [
        glimmer(tilt=-6, flap=0, dx=-1, eye="glare", glint=-3),
        glimmer(tilt=6, flap=1, dx=1, eye="glare", glow=True, glint=1),
        glimmer(tilt=0, flap=2, eye="glare", glow=True, glint=3, extra=[sparkle(-5, -14, True), sparkle(5, -6)]),
        decoy(base.shift(-SK.Si(9), 0)).over(decoy(base.shift(SK.Si(9), 0))).over(glimmer(flap=2, eye="glare", glow=True)),
        decoy(glimmer(flap=3, tilt=-8).shift(-SK.Si(12), -1)).over(decoy(glimmer(flap=1, tilt=8).shift(SK.Si(12), -1))).over(glimmer(flap=3)),
        decoy(glimmer(flap=0, tilt=-4).shift(-SK.Si(13), 0), 0.3, 4).over(decoy(glimmer(flap=2, tilt=4).shift(SK.Si(13), 0), 0.3, 5)).over(glimmer(flap=0, bob=-1)),
        glimmer(flap=1, bob=0, glint=-2),
    ]
    dead = Spr.parse("""
.......u..........
...Uq..Un...b.....
..UqmnUqqn..Bc....
.Uqqmn.UcUn.Uqn.u.
UqqqmmnUqmqnUqqmnB
""", feet_x=9)
    dead = SK.carve_spr(dead)
    death = [
        glimmer(tilt=-20, flap=0, eye="shut", cracks=2, extra=[sparkle(3, -12)]),
        glimmer(tilt=-50, flap=2, eye="shut", cracks=4, hover=6, dx=-1),
        ground(glimmer(tilt=-80, flap=3, eye="shut", cracks=5, hover=3, dx=-1)).over(Spr(small_shard(6, -2, -20))),
        dead,
    ]
    knock = [glimmer(tilt=-30, flap=1, dx=-2, bob=-1, eye="shut", cracks=1)]
    anims = [
        ("Idle", idle, [0.14] * 4),
        ("Run", run, [0.08] * 6),
        ("Death", death, [0.1, 0.1, 0.12, 0.3]),
        ("Dead", [dead], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Shard", shard, [0.12, 0.14, 0.05, 0.08, 0.1, 0.1]),
        ("Split", split, [0.08, 0.1, 0.12, 0.08, 0.12, 0.12, 0.12]),
    ]
    return anims


# v0.8: the Mirror Image decoys get their own sheet (they wore the Glimmer's). A decoy is the Glimmer's reflection:
# the same body and poses, so it still passes for the real one at a glance, but its glass is a photographic negative
# (dark facets pale, pale edges dark violet, the eye dark) and a sparse lattice of facets is missing, so on a second
# look it is see-through. Anims: everything the real one has but Split, plus Spawn (the tiny-rat base plays it).
DECOY_NEG = {"q": "N", "m": "n", "K": "n", "n": "U", "N": "u", "u": "n", "c": "q", "X": "q", "U": "n"}


def decoy_look(spr, seed=0):
    """Outline and wing glass kept as drawn (it must pass for the Glimmer); the dark core turns into pale lilac
    glass, its pale facets and the eye go dark, and a lattice of core facets is missing (see-through)."""
    if type(spr).__name__ != "Spr":
        return spr
    px = spr.px
    out = {}
    for (x, y), c in px.items():
        inner = all((x + dx, y + dy) in px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if inner and c in "qmKnN" and (x * 2 + y * 3 + seed) % 4 == 0:
            continue                                  # see-through facets
        out[(x, y)] = DECOY_NEG.get(c, c) if (inner and c not in "Bb") else c
    return Spr(out)


@sheet
def build_UmbGlimmerDecoy(outdir):
    src = {an: (fr, du) for an, fr, du in glimmer_anims()}
    anims = []
    for an in ("Idle", "Run", "Death", "Dead", "Knockback", "Portrait", "Shard"):
        fr, du = src[an]
        anims.append((an, [decoy_look(edge_pass(f), i) for i, f in enumerate(fr)], du))
        if an == "Dead":
            anims.append(("Statue", [edge_pass(src["Idle"][0][0]).stone()], [0.2]))
    base = glimmer(flap=2, glint=0)
    # Spawn: it gathers out of drifting shards (tiny-rat spawn timing, 3 frames 0.28 s)
    spawn = [dissolve(decoy_look(edge_pass(base)), 0.7, seed=3, rise=1, smoke="NUu"),
             dissolve(decoy_look(edge_pass(base)), 0.35, seed=4, rise=1, smoke="NUu"),
             decoy_look(edge_pass(glimmer(flap=3, glint=2)))]
    anims.append(("Spawn", spawn, [0.12, 0.08, 0.08]))
    return build_sheet("UmbGlimmerDecoy", anims, outdir, edge=False)


# ================================================================================================
# 3. GLOOM LURKER (T1): many-legged shadow crawler, mouth full of pale teeth, legs like ink
# ================================================================================================
def ink_leg(c, hip, knee, foot, col="q", foot_col="n", knee_col="N", upper=True, lower=True):
    if upper:
        for p in line_px(hip[0], hip[1], knee[0], knee[1]): c.put(p[0], p[1], col)
    if lower:
        for p in line_px(knee[0], knee[1], foot[0], foot[1]): c.put(p[0], p[1], col)
        c.put(foot[0], foot[1], foot_col)
    c.put(knee[0], knee[1], knee_col)


LURK_FEET = [15, 9, -8, -14]          # resting foot x of the 4 legs (front to back), near side
LURK_FEET_FAR = [12, 6, -5, -11]
LURK_KNEE = [(5, 6), (3, 7), (-3, 7), (-5, 6)]   # knee (out, up) from the hip


def lurker(dx=0, dy=0, mouth="shut", feet=None, far=None, lifts=None, puff=0, eyes="open", extra=(),
           tilt=0, front_raise=0):
    """feet / far: per-leg (dx, dy) offsets for near and far feet; lifts: extra knee height per leg.
    tilt>0 raises the head end."""
    c = Canvas()
    feet = feet or [(0, 0)] * 4
    far = far or [(0, 0)] * 4
    lifts = lifts or [0, 0, 0, 0]
    bx, by = dx, -7 + dy
    hips = [(bx + 3, by - 1 - tilt), (bx + 1, by - 1), (bx - 2, by - 1), (bx - 5, by - 1 + tilt // 2)]

    def leg_geo(i, near):
        h = hips[i] if near else (hips[i][0] - 1, hips[i][1] - 1)
        ko = LURK_KNEE[i]
        k = (h[0] + ko[0] - (0 if near else 1), h[1] - ko[1] - lifts[i] + (0 if near else 1))
        fx = (LURK_FEET if near else LURK_FEET_FAR)[i] + dx + (feet if near else far)[i][0]
        fy = (feet if near else far)[i][1] - (front_raise if i == 0 else 0)
        return h, k, (fx, min(0, fy))
    # far legs (dark ink) and the hidden upper half of the near legs go behind the body
    for i in range(4):
        h, k, f = leg_geo(i, False)
        ink_leg(c, h, k, f, col="q", foot_col="m", knee_col="n")
    for i in range(4):
        h, k, f = leg_geo(i, True)
        ink_leg(c, h, k, f, col="n", knee_col="U", lower=False)
    # abdomen + head
    acx, acy, arx, ary = bx - 5, by - 2 + tilt // 2, 6 + puff * 0.7, 4.5 + puff * 0.5
    ab = ellipse_px(acx, acy, arx, ary, "q")
    hd = ellipse_px(bx + 3, by - 2 - tilt, 4.4, 3.4, "q")
    body = {}
    body.update(ab); body.update(hd)
    for (x, y) in list(body):
        up = (x, y - 1) not in body; left = (x - 1, y) not in body; down = (x, y + 1) not in body
        if up and left: body[(x, y)] = "U"
        elif up: body[(x, y)] = "N" if (x + y) % 3 == 0 else "n"
        elif left: body[(x, y)] = "n"
        elif down: body[(x, y)] = "m"
        elif (x, y) in ab and y < acy - ary * 0.25 and (x - 1, y - 1) in body and hsh(x, y, 2) < 0.75:
            body[(x, y)] = "n"   # moonlit back of the abdomen
    # abdomen marking: a pale hourglass-like chevron
    ax, ay = SK.spt(bx - 5, by - 3 + tilt // 2)
    for (ox, oy, col) in ((-2, -1, "n"), (-1, 0, "N"), (0, 1, "n"), (1, 0, "N"), (2, -1, "n")):
        if (ax + ox, ay + oy) in body: body[(ax + ox, ay + oy)] = col
    put_px(c, body)
    # eyes: bright pinpricks on the brow
    hx, hy = bx + 3, by - 2 - tilt
    if eyes == "open":
        for (ox, oy, col) in ((1, -1, "c"), (3, -1, "c"), (2, -2, "B"), (0, -2, "B")):
            c.put(hx + ox, hy + oy, col)
    else:
        for (ox, oy, col) in ((1, -1, "U"), (3, -1, "U")):
            c.put(hx + ox, hy + oy, col)
    # mouth (front of the head, low)
    mx, my = hx + 3, hy + 1
    M = {
        "shut": ((-2, 0, "K"), (-1, 0, "K"), (0, 0, "K"), (1, 0, "K"),
                 (-2, 1, "u"), (-1, 1, "X"), (0, 1, "u"), (1, 1, "X"), (2, 0, "u"), (-1, 2, "U"), (1, 2, "U")),
        "open": ((-1, -1, "q"), (0, -1, "u"), (1, -1, "U"), (2, -1, "u"),
                 (-1, 0, "K"), (0, 0, "K"), (1, 0, "K"), (2, 0, "K"),
                 (-1, 1, "u"), (0, 1, "U"), (1, 1, "u"), (2, 1, "U")),
        "wide": ((0, -2, "u"), (1, -2, "U"), (2, -2, "u"), (3, -3, "U"), (3, -2, "q"),
                 (-1, -1, "K"), (0, -1, "K"), (1, -1, "K"), (2, -1, "K"),
                 (-1, 0, "K"), (0, 0, "p"), (1, 0, "K"), (2, 0, "K"),
                 (-1, 1, "K"), (0, 1, "K"), (1, 1, "K"), (0, 2, "u"), (1, 2, "U"), (2, 2, "u"), (3, 3, "U"), (3, 2, "q")),
        "chomp": ((-1, 0, "u"), (0, 0, "X"), (1, 0, "u"), (2, 0, "X"), (3, 0, "u"),
                  (0, -1, "U"), (2, -1, "U"), (1, 1, "U"), (3, 1, "U")),
    }[mouth]
    for (ox, oy, col) in M:
        c.put(mx + ox, my + oy, col)
    # near legs, lower half (in front)
    for i in range(4):
        h, k, f = leg_geo(i, True)
        ink_leg(c, h, k, f, col="n", knee_col="U", upper=False)
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


def gloom_cloud(cx, cy, r, seed=0, dense=1.0):
    """A breath of solid darkness: q/m core, violet edge wisps, a few pale motes."""
    px = {}
    for (x, y), v in ellipse_px(cx, cy, r, r * 0.7, "q", rim="n", rim_t=0.7, jitter=0.5, seed=seed).items():
        if v == "q" and (x * 2 + y * 3 + seed) % 7 == 0: v = "n"          # slow swirl inside the dark
        if v == "q" and (x - y + seed) % 5 == 0: v = "m"
        if hsh(x, y, seed) < dense or v == "n": px[(x, y)] = v
    for (x, y) in list(px):
        if (x, y - 1) not in px and hsh(x, y, seed + 9) < 0.5: px[(x, y)] = "N"
    for k in range(int(r) + 1):
        a = hsh(k, seed, 3) * 6.28
        px[(int(cx + r * 1.15 * math.cos(a)), int(cy + r * 0.85 * math.sin(a)))] = "U" if k % 3 == 0 else "N"
    return px


@sheet
def build_UmbGloomLurker(outdir):
    idle = [lurker(dy=[0, 0, 1, 1][i], puff=[0, 0.4, 0.8, 0.4][i], mouth="shut" if i != 2 else "open",
                   lifts=[[0, 0, 0, 0], [1, 0, 1, 0], [-1, -1, -1, -1], [0, 1, 0, 1]][i],
                   feet=[(0, 0), (i % 2, 0), (0, 0), (-(i % 2), 0)],
                   eyes="open" if i != 3 else "blink") for i in range(4)]
    # alternating tetrapod gait: legs 0,2 vs 1,3 swap, lifted legs swing forward
    run = []
    for i in range(6):
        ph = i / 6.0 * 2 * math.pi
        a = int(round(3 * math.sin(ph))); bb = -a
        la = 2 if math.cos(ph) > 0.3 else 0
        lb = 2 if math.cos(ph) < -0.3 else 0
        feet = [(a, -la // 2), (bb, -lb // 2), (a, -la // 2), (bb, -lb // 2)]
        far = [(bb, -lb // 2), (a, -la // 2), (bb, -lb // 2), (a, -la // 2)]
        run.append(lurker(dy=[0, -1, 0, 0, -1, 0][i], feet=feet, far=far, lifts=[la, lb, la, lb]))
    # Ambush: sink (2 frames, held), leap with jaws wide, chomp (frame 3), hold, recoil, settle
    ambush = [
        lurker(dy=2, dx=-1, lifts=[2, 2, 2, 2], feet=[(1, 0), (1, 0), (0, 0), (0, 0)], mouth="shut", eyes="blink"),
        lurker(dy=3, dx=-2, lifts=[3, 3, 3, 3], feet=[(2, 0), (2, 0), (1, 0), (1, 0)], mouth="open", tilt=1),
        lurker(dy=-3, dx=4, lifts=[-3, -2, -1, -1], feet=[(3, -5), (2, -2), (-3, 0), (-4, 0)], far=[(3, -4), (2, -2), (-3, 0), (-4, 0)],
               mouth="wide", tilt=2),
        lurker(dy=0, dx=6, lifts=[-1, 0, 0, 0], feet=[(2, 0), (0, 0), (-4, 0), (-5, 0)], far=[(1, 0), (0, 0), (-4, 0), (-5, 0)],
               mouth="chomp", extra=[sparkle(19, -6, True)]),
        lurker(dy=1, dx=6, feet=[(0, 0), (0, 0), (-3, 0), (-3, 0)], mouth="chomp"),
        lurker(dy=0, dx=3, feet=[(0, 0), (0, 0), (-1, 0), (-1, 0)], mouth="open"),
        lurker(dy=0, dx=1, mouth="shut"),
    ]
    # Gloom: rear up and inhale (3 frames), exhale (frame 3) a pouring darkness, spread, settle
    gloom = [
        lurker(tilt=1, puff=0.5, front_raise=2, mouth="shut", lifts=[1, 0, 0, 0]),
        lurker(tilt=2, puff=1.2, dy=-1, front_raise=4, mouth="shut", eyes="blink", lifts=[2, 1, 0, 0]),
        lurker(tilt=3, puff=1.8, dy=-1, front_raise=5, mouth="open", lifts=[3, 1, 0, 0]),
        lurker(tilt=0, puff=0.6, dy=1, mouth="wide", extra=[gloom_cloud(15, -5, 3.5, 1)]),
        lurker(tilt=0, puff=0.2, dy=1, mouth="wide", extra=[gloom_cloud(17, -4, 5, 2)]),
        lurker(tilt=0, puff=0, dy=0, mouth="open", extra=[gloom_cloud(18, -4, 6.5, 3, 0.75)]),
        lurker(mouth="shut", extra=[gloom_cloud(19, -4, 7, 4, 0.35)]),
    ]
    def dead_bug(curl, dy=0, roll=0):
        c = Canvas()
        bx, by = 0, -4 + dy
        body = ellipse_px(bx, by, 7, 3, "q", rim="m")
        for (x, y) in list(body):
            if (x, y - 1) not in body: body[(x, y)] = "n"
        body[(bx + 5, by)] = "U"; body[(bx + 6, by + 1)] = "u"
        for i, lx in enumerate((-5, -2, 2, 5)):
            ang = -90 - 30 + i * 20
            pts = limb_pts(bx + lx, by - 2, [(3, ang), (3, ang + 70 * curl * (1 if lx > 0 else -1))])
            for p0, p1 in zip(pts, pts[1:]):
                for p in line_px(p0[0], p0[1], p1[0], p1[1]): c.put(p[0], p[1], "q" if i % 2 else "n")
            c.put(pts[1][0], pts[1][1], "U")
        put_px(c, body)
        return ground(c.spr().shift(roll, 0))
    corpse = dead_bug(1.0)
    death = [
        lurker(dx=-2, tilt=3, front_raise=4, mouth="wide", eyes="blink", lifts=[2, 1, 0, 0]),
        lurker(dx=-2, dy=4, lifts=[-4, -4, -4, -4], feet=[(-4, 0), (-3, 0), (3, 0), (4, 0)], mouth="open", eyes="blink"),
        dead_bug(0.3, dy=-1),
        corpse,
    ]
    knock = [lurker(dx=-2, tilt=2, front_raise=4, lifts=[2, 1, 0, -1], feet=[(-2, 0), (-1, 0), (0, 0), (1, 0)], mouth="open", eyes="blink")]
    anims = [
        ("Idle", idle, [0.18, 0.14, 0.18, 0.14]),
        ("Run", run, [0.07] * 6),
        ("Death", death, [0.1, 0.12, 0.14, 0.3]),
        ("Dead", [corpse], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Ambush", ambush, [0.16, 0.14, 0.06, 0.05, 0.12, 0.1, 0.12]),
        ("Gloom", gloom, [0.12, 0.14, 0.16, 0.06, 0.1, 0.12, 0.14]),
    ]
    return build_sheet("UmbGloomLurker", anims, outdir)


# ================================================================================================
# 4. THE TWINNED (T2): two thin shadow swordsmen fused back-to-back, one blade each
# ================================================================================================
def mirror_part(part):
    p = Part.__new__(Part); p.px = {(-x, y): c for (x, y), c in part.px.items()}; return p


TW_HEAD = {
    "calm": Part("""
.nnn.
qnnnn
qqqKc
qqqqU
.qqq.
""", (2, 4)),
    "glare": Part("""
.nnn.
qnnnn
qqKcX
qqqcU
.qqq.
""", (2, 4)),
    "down": Part("""
.....
.nnn.
qnnnn
qqqqK
.qqKU
""", (2, 4)),
    "dead": Part("""
.nnn.
qnnnn
qqqqU
qqqqn
.qqq.
""", (2, 4)),
}
TW_BOOT = Part("qnU", (0, 0))
TW_PALE = {"q": "tq", "n": "tn", "N": "tN", "m": "tm", "K": "tK"}


def torso_px(hip, ang, length=8, w0=1.8, w1=3.0):
    """Tapered torso polygon from the hip toward angle `ang` (deg, -90 = straight up)."""
    a = math.radians(ang); n = (-math.sin(a), math.cos(a))
    top = (hip[0] + length * math.cos(a), hip[1] + length * math.sin(a))
    pts = [(hip[0] + n[0] * w0, hip[1] + n[1] * w0), (top[0] + n[0] * w1, top[1] + n[1] * w1),
           (top[0] - n[0] * w1 * 0.8, top[1] - n[1] * w1 * 0.8), (hip[0] - n[0] * w0, hip[1] - n[1] * w0)]
    return poly_px(pts, "q"), (int(round(top[0])), int(round(top[1])))


def blade(c, x, y, ang, length=9, glint=False, col=("u", "S")):
    a = math.radians(ang)
    pts = line_px(x, y, int(round(x + length * math.cos(a))), int(round(y + length * math.sin(a))))
    for i, p in enumerate(pts):
        if i == 0: continue
        c.put(p[0], p[1], col[0] if i < len(pts) - 1 else ("c" if glint else col[0]))
        # dark back edge of the blade, one pixel beside it
        q = (p[0] + int(round(math.sin(a))), p[1] - int(round(math.cos(a))))
        if i < len(pts) - 1: c.put(q[0], q[1], col[1], over=False)
    if glint:
        tx, ty = pts[-1]
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)): c.put(tx + d[0], ty + d[1], "u", over=False)
    # pommel + guard
    c.put(int(round(x - math.cos(a))), int(round(y - math.sin(a))), "q")
    gx, gy = int(round(x + 1.2 * math.cos(a))), int(round(y + 1.2 * math.sin(a)))
    c.put(gx + int(round(math.sin(a))), gy - int(round(math.cos(a))), "U")
    c.put(gx - int(round(math.sin(a))), gy + int(round(math.cos(a))), "U")


def twinned(lean=(20, 20), arms=((60, 30), (60, 30)), swords=(20, 20), heads=("calm", "calm"), dx=0, dy=0,
            legs=((105, 80), (75, 100)), glints=(False, False), extra=(), hip_y=-11, tlen=9, skirt=0):
    """lean/arms/swords/heads: (front twin, back twin). The back twin's angles are given in its own
    facing frame (it faces left), so the same numbers make a mirrored pose."""
    c = Canvas()
    hip = (dx, hip_y + dy)
    # legs: one under each twin
    c.limb(hip[0] - 1, hip[1], [(5, legs[0][0]), (6, legs[0][1])], [("q", "q"), "q"], width=2, end=mirror_part(TW_BOOT))
    sub = Canvas()
    tops = []
    for k, f in ((1, -1), (0, 1)):          # back twin first, front twin on top
        ang = -90 + f * lean[k]
        tp, top = torso_px((hip[0], hip[1] - 1), ang, tlen)
        tops.append((k, f, top, tp))
    # back twin arm + blade behind everything
    for k, f, top, tp in tops:
        if k != 1: continue
        sh = (top[0] - 1, top[1] + 1)
        wa = lambda a: a if f == 1 else 180 - a
        hx, hy = c.limb(sh[0], sh[1], [(4, wa(arms[k][0])), (4, wa(arms[k][1]))], ["q", "q"])
        blade(c, hx, hy, wa(swords[k]), glint=glints[k], col=("U", "s"))
        c.put(hx, hy, "N")
    for k, f, top, tp in tops:
        put_px(sub, tp)
    if skirt is not None:
        # shared ragged tabard hanging from the fused waist (sways with `skirt`)
        sk = poly_px([(hip[0] - 3, hip[1] - 2), (hip[0] + 3, hip[1] - 2), (hip[0] + 5 + skirt, hip[1] + 5),
                      (hip[0] - 5 + skirt, hip[1] + 5)], "q")
        for (x, y) in list(sk):
            if y >= hip[1] + 3 and (x * 3 + y + skirt) % 4 == 0: del sk[(x, y)]
        put_px(sub, sk)
    body = sub.px
    for (x, y) in list(body):
        up = (x, y - 1) not in body; left = (x - 1, y) not in body; right = (x + 1, y) not in body
        if up and left: body[(x, y)] = "U"
        elif up or left: body[(x, y)] = "n"
        elif right: body[(x, y)] = "m"
    # fused spine seam + belt
    hp = SK.spt(*hip)
    for y in range(hp[1] - SK.Si(5), hp[1]):
        if (hp[0], y) in body: body[(hp[0], y)] = "n" if y % 2 else "q"
    for x in range(hp[0] - SK.Si(2), hp[0] + SK.Si(3)):
        if (x, hp[1] - 1) in body: body[(x, hp[1] - 1)] = "U" if x == hp[0] else "s"
    put_px(c, body)
    for k, f, top, tp in tops:
        head = TW_HEAD[heads[k]] if f == 1 else mirror_part(TW_HEAD[heads[k]])
        c.part(head, top[0] + f, top[1])
    c.limb(hip[0] + 1, hip[1], [(5, legs[1][0]), (6, legs[1][1])], [("n", "q"), "n"], width=2, end=TW_BOOT)
    # v0.8: the back twin is the pale reflection (silver-lilac), the front twin stays dark violet
    hpx = SK.spt(*hip)[0]
    for k_, v_ in list(c.px.items()):
        if k_[0] < hpx and v_ in TW_PALE:
            c.px[k_] = TW_PALE[v_]
    # v0.9 lineage: the Shade Imp's smoky tail whips out behind the fused waist
    imp_tail(c, hip[0] - 1, hip[1] + 2, int(round(skirt or 0)) % 4, curl=-38)
    # front twin arm + blade on top
    for k, f, top, tp in tops:
        if k != 0: continue
        sh = (top[0], top[1] + 1)
        hx, hy = c.limb(sh[0], sh[1], [(4, arms[k][0]), (4, arms[k][1])], ["n", "n"])
        blade(c, hx, hy, swords[k], glint=glints[k])
        c.put(hx, hy, "U")
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


def mirror_spr(px):
    return {(-x, y): v for (x, y), v in px.items()}


def flash_ring(cx, cy, r, cols=("c", "B")):
    px = {}
    for t in range(0, 360, 10):
        a = math.radians(t)
        x = int(round(cx + r * math.cos(a))); y = int(round(cy + r * 0.8 * math.sin(a)))
        px[(x, y)] = cols[(t // 30) % len(cols)]
    return px


@sheet
def build_UmbTwinned(outdir):
    idle = [twinned(lean=(20 + (i % 2), 20 + ((i + 1) % 2)), dy=[0, 0, 1, 1][i], skirt=[0, 1, 0, -1][i],
                    arms=((70 + 6 * (i % 2), 40), (70 + 6 * ((i + 1) % 2), 40)), swords=(30 + 4 * (i % 2), 30 - 4 * (i % 2)),
                    legs=((105, 80 + (i >= 2) * 4), (75 - (i >= 2) * 4, 100))) for i in range(4)]
    cyc = [((60, 100), (120, 90)), ((80, 110), (100, 80)), ((100, 85), (80, 95)),
           ((120, 90), (60, 100)), ((100, 80), (80, 110)), ((80, 95), (100, 85))]
    run = [twinned(lean=(30, 12), dy=-1 if i % 3 == 0 else 0, legs=cyc[i], skirt=-1 - (i % 2),
                   arms=((40 + 15 * (i // 3), 20), (100 - 15 * (i // 3), 60)), swords=(10, 60)) for i in range(6)]
    # Twin Cut: both cock (2 frames), front hit (2), twist, back hit (4), follow, recover, settle
    cut = [
        twinned(lean=(14, 14), arms=((-100, -120), (-100, -120)), swords=(-150, -150), heads=("glare", "glare")),
        twinned(lean=(8, 8), arms=((-120, -140), (-120, -140)), swords=(-170, -170), heads=("glare", "glare"), dy=1,
                legs=((120, 70), (60, 110)), glints=(True, True)),
        twinned(lean=(36, 6), arms=((-10, 20), (-110, -130)), swords=(40, -160), heads=("glare", "glare"), dx=1, dy=1,
                legs=((130, 80), (50, 100)), skirt=2, extra=[slash(8, -18, 11, -75, 60, thick=2)]),
        twinned(lean=(22, 16), arms=((60, 90), (-60, -80)), swords=(95, -100), heads=("calm", "glare"), dy=1,
                legs=((120, 80), (60, 100)), skirt=1),
        twinned(lean=(8, 38), arms=((70, 100), (-10, 20)), swords=(100, 40), heads=("calm", "glare"), dx=-1, dy=1,
                legs=((120, 90), (60, 95)), skirt=-2, extra=[mirror_spr(slash(8, -18, 11, -75, 60, thick=2))]),
        twinned(lean=(18, 24), arms=((70, 100), (60, 90)), swords=(100, 95), dy=1, skirt=-1),
        twinned(lean=(20, 20), arms=((70, 50), (70, 50)), swords=(50, 50), dy=0),
        twinned(lean=(20, 20), arms=((70, 40), (70, 40)), swords=(30, 30)),
    ]
    # Exchange: lower, point (front & back), hold + glint, sigil, FLASH (frame 4), after-image, reform, recover
    point = dict(lean=(26, 26), arms=((-20, -15), (-20, -15)), swords=(-15, -15), heads=("glare", "glare"))
    flash_body = recolor_shadow(twinned(**point), ramp=("U", "u", "c", "X"))
    swap = [
        twinned(lean=(14, 14), arms=((90, 110), (90, 110)), swords=(100, 100), heads=("down", "down"), dy=1),
        twinned(lean=(22, 22), arms=((-10, -5), (-10, -5)), swords=(-5, -5), heads=("glare", "glare")),
        twinned(glints=(True, True), **point),
        twinned(glints=(True, True), extra=[flash_ring(0, -17, 10, ("B", "b"))], **point),
        flash_body.over(Spr(flash_ring(0, -17, 13, ("c", "X", "u")))).over(Spr(sparkle(0, -18, True))),
        dissolve(recolor_shadow(twinned(**point), ramp=("q", "n", "N", "U")), 0.3, seed=2, rise=1, smoke="NU"),
        twinned(lean=(22, 22), arms=((20, 40), (20, 40)), swords=(40, 40)),
        twinned(lean=(20, 20), arms=((60, 40), (60, 40)), swords=(35, 35), skirt=1),
        twinned(),
    ]
    corpse = twinned(lean=(84, 84), hip_y=-2, legs=((175, 170), (5, 10)), arms=((100, 170), (100, 170)), swords=(175, 175),
                     heads=("dead", "dead"), tlen=8, skirt=None)
    corpse = ground(corpse)
    death = [
        twinned(lean=(4, 4), arms=((-120, -100), (-120, -100)), swords=(-140, -140), heads=("down", "down")),
        twinned(lean=(40, 40), arms=((100, 120), (100, 120)), swords=(110, 110), heads=("down", "down"), dy=4,
                legs=((150, 100), (30, 80)), skirt=None),
        ground(twinned(lean=(64, 64), arms=((110, 150), (110, 150)), swords=(160, 160), heads=("dead", "dead"), hip_y=-5,
                       legs=((170, 120), (10, 60)), skirt=None)),
        corpse,
    ]
    knock = [twinned(lean=(0, 34), arms=((-150, -120), (60, 90)), swords=(-100, 100), heads=("down", "glare"), dx=-2,
                     legs=((120, 90), (70, 110)), skirt=-2)]
    anims = [
        ("Idle", idle, [0.18] * 4),
        ("Run", run, [0.08] * 6),
        ("Death", death, [0.1, 0.12, 0.14, 0.3]),
        ("Dead", [corpse], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Cut", cut, [0.14, 0.12, 0.05, 0.08, 0.05, 0.1, 0.1, 0.12]),
        ("Swap", swap, [0.1, 0.12, 0.16, 0.12, 0.06, 0.1, 0.1, 0.1, 0.12]),
    ]
    return build_sheet("UmbTwinned", anims, outdir)


# ================================================================================================
# 5. MIRROR WITCH (T2): tall witch, cracked hand-mirror, face hidden by a veil of black glass
# ================================================================================================
MW_HAT = {
    "up": Part("""
.....nU.
....nq..
...nqq..
...qqq..
..nqqqq.
..qqqqq.
UnnnqqqnU
""", (4, 6)),
    "bent": Part("""
........
....qnU.
...nqq..
...qqq..
..nqqqq.
..qqqqq.
UnnnqqqnU
""", (4, 6)),
    "tip": Part("""
.......
.......
U......
.nqn...
..qqqn.
..qqqqq
UnnqqqnU
""", (4, 6)),
}
MW_VEIL = {
    "calm": Part("""
qKKKq
KKbKK
KbKKK
KKKBK
nKKKn
.KKK.
""", (2, 0)),
    "glow": Part("""
qKKKq
KKcKK
KcKKK
KKKcK
nKKKn
.KcK.
""", (2, 0)),
}
MIRROR = {
    "face": Part("""
.SUS.
SBcBS
SbBcS
SBuKS
SBKBS
.SSS.
..s..
..s..
""", (2, 7)),
    "glow": Part("""
.SuS.
SccXS
SXcuS
ScuKS
ScKcS
.SuS.
..s..
..s..
""", (2, 7)),
    "edge": Part("""
.S.
.U.
.S.
.U.
.S.
.S.
.s.
.s.
""", (1, 7)),
    "down": Part("""
..s..
..s..
.SSS.
SBKBS
SBuKS
SbBcS
SBcBS
.SUS.
""", (2, 0)),
}


def robe_px(top, lean, sway, height=15, w_top=3, w_hem=7):
    hem_y = top[1] + height
    pts = [(top[0] - w_top + lean, top[1]), (top[0] + w_top + lean, top[1]),
           (top[0] + w_hem + sway, hem_y), (top[0] - w_hem + sway - 1, hem_y)]
    px = poly_px(pts, "q")
    for (x, y) in list(px):
        up = (x, y - 1) not in px; left = (x - 1, y) not in px; right = (x + 1, y) not in px
        if up and left: px[(x, y)] = "U"
        elif left: px[(x, y)] = "n"
        elif up: px[(x, y)] = "n"
        elif right: px[(x, y)] = "m"
        elif (x - top[0] - sway // 2) % 3 == 0 and y > top[1] + 5: px[(x, y)] = "m"   # long folds
    # silver hem trim, ragged
    for x in range(int(top[0] - w_hem + sway - 1), int(top[0] + w_hem + sway + 1)):
        if (x, hem_y - 1) in px:
            px[(x, hem_y - 1)] = "S" if (x + sway) % 3 else "U"
            if (x * 5 + sway) % 4 == 0: px[(x, hem_y)] = "n"
    return px


def witch(lean=0, sway=0, dy=0, dx=0, hat="up", veil="calm", arm=((60, -60)), mirror="face", back_arm=(100, 70),
          mirror_off=(0, 0), extra=(), hair=0, squash=0):
    c = Canvas()
    top = (dx, -15 + dy + squash)
    head = (top[0] + 1 + lean, top[1] - 6)
    # hair: long dark strands down the back
    for k in range(3):
        c.limb(head[0] - 2, head[1] + 1 + k, [(4 + k, 110 + hair * 6 + k * 8), (3, 95 + hair * 8)], ["m" if k else "n"])
    # back arm
    hx, hy = c.limb(top[0] - 1 + lean, top[1] + 2, [(4, back_arm[0]), (4, back_arm[1])], ["q"])
    c.put(hx, hy, "U")
    put_px(c, robe_px(top, lean, sway, height=14 - squash - dy if dy > 0 else 14 - squash))
    # v0.9/v0.10 lineage: the Gloom Lurker's arched slate-blue spider legs reach out from both sides of the hem
    for k, (x0, a1, a2) in enumerate(((-5, 215, 125), (-4, 245, 110), (4, -65, 70), (5, -35, 55))):
        c.limb(top[0] + x0 + sway * 0.5, -3, [(3.4, a1 + (sway * 5 if k < 2 else -sway * 5)), (3.8, a2)],
               [("lN", "lN"), ("ln", "ln")])
    c.part(MW_VEIL[veil], head[0], head[1])
    c.put(head[0] - 1, head[1] + 2, "lc"); c.put(head[0] + 1, head[1] + 2, "lc")   # the Lurker's teal eyes
    c.part(MW_HAT[hat], head[0], head[1] - 1)
    # mirror arm
    sx, sy = top[0] + 2 + lean, top[1] + 2
    hx, hy = c.limb(sx, sy, [(4, arm[0]), (4, arm[1])], ["n", "n"])
    c.part(MIRROR[mirror], hx + mirror_off[0], hy + mirror_off[1])
    c.put(hx, hy, "u"); c.put(hx + 1, hy, "U")
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


def shard_ring(cx, cy, r, n=8, size=3, cols=("c", "B", "b")):
    px = {}
    for i in range(n):
        a = math.radians(i * 360 / n)
        x = cx + r * math.cos(a); y = cy + r * 0.75 * math.sin(a)
        px.update(small_shard(int(round(x)), int(round(y)), math.degrees(a), size, cols))
    return px


def bolt_px(x, y, length=6):
    px = {}
    for i in range(length):
        px[(x - i, y)] = "c" if i < 2 else "B" if i < 4 else "b"
    px[(x + 1, y)] = "X"; px[(x, y - 1)] = "u"; px[(x, y + 1)] = "u"
    px[(x - 2, y - 1)] = "B"; px[(x - 3, y + 1)] = "b"
    return px


@sheet
def build_UmbMirrorWitch(outdir):
    idle = [witch(sway=[0, 1, 0, -1][i], dy=[0, 0, 1, 1][i] * 0, lean=[0, 0, 1, 0][i], hair=[0, 1, 0, -1][i],
                  arm=(70 + 4 * (i % 2), -50 - 6 * (i % 2)), back_arm=(100 + 5 * (i % 2), 75),
                  mirror="face" if i != 2 else "edge") for i in range(4)]
    run = [witch(lean=2, sway=[-2, -1, 0, -2, -1, 0][i] - 1, hair=-2 - (i % 2), dy=-1 if i % 3 == 0 else 0,
                 arm=(40 + 10 * (i % 3), -30), back_arm=(130 + 10 * (i % 3), 120), mirror="edge") for i in range(6)]
    # Reflection: draw the mirror in (2 frames, glint), thrust, release (3), recoil, recover, settle
    reflect = [
        witch(lean=-1, sway=1, arm=(110, -170), mirror="edge", back_arm=(80, 40), veil="calm"),
        witch(lean=-2, sway=2, arm=(120, -150), mirror="glow", back_arm=(60, 20), veil="glow", extra=[sparkle(4, -17)]),
        witch(lean=2, sway=-1, arm=(-5, -10), mirror="glow", back_arm=(150, 120), veil="glow", hat="bent"),
        witch(lean=3, sway=-2, arm=(-5, -10), mirror="face", back_arm=(150, 120), veil="glow", hat="bent",
              extra=[bolt_px(18, -19, 7), sparkle(12, -19, True)]),
        witch(lean=0, sway=1, arm=(20, -30), mirror="face", back_arm=(120, 90), hat="tip"),
        witch(lean=0, sway=0, arm=(50, -45), mirror="face", back_arm=(105, 75)),
        witch(),
    ]
    # Shatter: gather (0), RAISE (1), hold glowing (2-4, 0.8 s with frame 1), BURST ring (5), lower, settle
    shatter = [
        witch(lean=-1, dy=0, squash=1, arm=(100, 140), mirror="down", back_arm=(80, 100), veil="calm"),
        witch(lean=0, arm=(-55, -80), mirror="glow", back_arm=(-100, -80), veil="glow", hat="up"),
        witch(lean=0, arm=(-57, -82), mirror="glow", back_arm=(-110, -90), veil="glow", extra=[sparkle(6, -33)]),
        witch(lean=0, arm=(-55, -80), mirror="glow", back_arm=(-110, -90), veil="glow", sway=1,
              extra=[sparkle(1, -30), sparkle(10, -32, True)]),
        witch(lean=0, arm=(-53, -78), mirror="glow", back_arm=(-110, -90), veil="glow", sway=-1,
              extra=[flash_ring(6, -25, 5, ("c", "u"))]),
        witch(lean=-1, arm=(-40, -60), mirror="face", back_arm=(-140, -120), veil="glow", hat="bent",
              extra=[shard_ring(2, -14, 13), sparkle(8, -25, True)]),
        witch(lean=0, arm=(40, -20), mirror="face", back_arm=(120, 90), extra=[shard_ring(1, -14, 17, cols=("B", "b", "n"))]),
        witch(),
    ]
    corpse = Spr.parse("""
..........................
.....U....................
..nqqn.......SUS..........
.nqqqqnUnnn.SBKBS.........
KKKbqqqqqqqnSuBcS.n.......
nKbKKqqqqmqqqSSSSUqn......
.nnSSUqSqqSqSqSUs.s.U.....
""", feet_x=13)
    corpse = SK.carve_spr(corpse)
    death = [
        witch(lean=-2, sway=0, arm=(-120, -60), mirror="edge", back_arm=(-140, -100), veil="calm", hat="tip"),
        witch(lean=-1, sway=1, squash=4, arm=(110, 150), mirror="down", back_arm=(130, 160), hat="bent"),
        ground(witch(lean=-3, squash=8, arm=(150, 170), mirror="down", back_arm=(170, 175), hat="tip")),
        corpse,
    ]
    knock = [witch(lean=-2, sway=0, arm=(-140, -100), mirror="edge", back_arm=(-150, -120), hat="tip", hair=3)]
    anims = [
        ("Idle", idle, [0.2, 0.16, 0.2, 0.16]),
        ("Run", run, [0.08] * 6),
        ("Death", death, [0.1, 0.12, 0.14, 0.3]),
        ("Dead", [corpse], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Reflect", reflect, [0.14, 0.14, 0.06, 0.06, 0.1, 0.1, 0.12]),
        ("Shatter", shatter, [0.12, 0.2, 0.2, 0.2, 0.2, 0.08, 0.14, 0.14]),
    ]
    return build_sheet("UmbMirrorWitch", anims, outdir)


# ================================================================================================
# 6. THE HOLLOW KING (T3): gaunt crowned king of void, cape of mirrored shards, a crack of light for a face
# ================================================================================================
HK_HEAD = {
    "calm": Part("""
.qqqq.
qqqcqq
qqquqq
qqqcqq
.qqUq.
..qq..
""", (3, 5)),
    "blaze": Part("""
.qqcq.
qqqXqq
qqcXcq
qqqXqq
.qqcq.
..qq..
""", (3, 5)),
    "dim": Part("""
.qqqq.
qqqqqq
qqqnqq
qqqUqq
.qqnq.
..qq..
""", (3, 5)),
}
HK_CROWN = {
    "whole": Part("""
U..u.S.u
S.uS.SUS
SUSSUBSS
.SSSSSS.
""", (4, 3)),
    "tilt": Part("""
.....u..
U..u.S.u
S.uS.SUS
SUSSUBSS
.SSSSSS.
""", (5, 4)),
}


def shard_fill(px, seed=0, glint=0):
    """Turn a filled region into a mosaic of mirror shards with silver seams and blue glints."""
    out = {}
    for (x, y) in px:
        u = x * 0.8 + y * 0.55 + seed * 0.37
        v = x * 0.6 - y * 0.85
        cu, cv = math.floor(u / 3.2), math.floor(v / 3.2)
        fu, fv = u / 3.2 - cu, v / 3.2 - cv
        tile = hsh(int(cu), int(cv), 5)
        col = "q" if tile < 0.45 else "n" if tile < 0.7 else "m" if tile < 0.85 else "b"
        if fu < 0.2 or fv < 0.2:
            col = "U" if hsh(int(cu) + glint, int(cv), 9) < 0.25 else "s" if tile < 0.6 else "n"
        if (fu > 0.6 and fu < 0.8 and fv > 0.5 and fv < 0.7) and hsh(int(cu), int(cv) + glint, 7) < 0.4:
            col = "B" if (x + y + glint) % 3 else "c"
        out[(x, y)] = col
    for (x, y) in list(out):
        if (x - 1, y) not in out or (x, y - 1) not in out: out[(x, y)] = "U" if (x + y) % 2 else "u"
    return out


def king(lean=0, sway=0, dy=0, dx=0, arm=(60, 30), sword=40, back_arm=(100, 80), head="calm", crown="whole",
         cape=0, cape_lift=0, extra=(), squash=0, glint=0, sword_len=15, blade_glow=False, hem_gap=0):
    c = Canvas()
    top = (dx, -24 + dy + squash)
    # cape of mirror shards behind everything: shoulder -> flowing back to the floor
    cp = poly_px([(top[0] - 3 + lean, top[1] - 1), (top[0] + 2 + lean, top[1]),
                  (top[0] - 2 + sway, -1), (top[0] - 9 - cape + sway, -1 - cape_lift // 2),
                  (top[0] - 13 - cape * 2, -3 - cape_lift), (top[0] - 9 - cape, top[1] + 6 - cape_lift // 2)], "q")
    put_px(c, shard_fill(cp, seed=cape, glint=glint))
    # back arm (thin void limb)
    sx, sy = top[0] - 2 + lean, top[1] + 2
    hx, hy = c.limb(sx, sy, [(6, back_arm[0]), (6, back_arm[1])], [("q", "n"), "q"], width=2)
    c.put(hx, hy, "U"); c.put(hx + 1, hy, "u")
    # robe body
    put_px(c, robe_px(top, lean, sway, height=24 - squash - dy, w_top=4, w_hem=7))
    # gaunt chest: shard pauldrons + a hollow where a heart should be
    for (ox, oy, col) in ((-4, 0, "U"), (-3, 0, "S"), (-3, 1, "s"), (3, 0, "S"), (4, 0, "U"), (3, 1, "s"),
                          (0, 4, "K"), (0, 5, "K"), (1, 4, "n"), (-1, 5, "n")):
        c.put(top[0] + lean + ox, top[1] + oy, col)
    # v0.10: its only parent is the Twinned: the pauldron spikes are the Twinned's pale silver reflection (were the
    # Nailshade's rose-tipped nails)
    for (ox, ang_, ln_) in ((-4, -140, 3), (-5, -165, 2), (4, -40, 3), (5, -15, 2)):
        put_px(c, nail_px(top[0] + lean + ox, top[1], ang_, ln_, tip="tN", mid="tn", base="tq"))
    hd = (top[0] + lean + 1, top[1] - 1)
    c.part(HK_HEAD[head], hd[0], hd[1])
    c.part(HK_CROWN[crown], hd[0], hd[1] - 5)
    # sword arm + void greatsword
    sx, sy = top[0] + 3 + lean, top[1] + 2
    hx, hy = c.limb(sx, sy, [(6, arm[0]), (6, arm[1])], [("n", "q"), "n"], width=2)
    blade(c, hx, hy, sword, length=sword_len, glint=blade_glow, col=("u" if blade_glow else "U", "n"))
    a = math.radians(sword)
    for i in range(2, sword_len - 1):   # dark void core beside the bright edge
        p = (int(round(hx + i * math.cos(a) - math.sin(a))), int(round(hy + i * math.sin(a) + math.cos(a))))
        c.put(p[0], p[1], "q" if i % 4 else "N", over=False)
    c.put(hx, hy, "U"); c.put(hx, hy + 1, "u")
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


def translucent(spr, phase=0, keep=0.6):
    """Afterimage look: interior thinned to a checker so the floor shows through; edges kept."""
    out = {}
    for (x, y), c in spr.px.items():
        edge = any((x + dx, y + dy) not in spr.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge or (x + y + phase) % 2 == 0 and hsh(x, y, phase) < keep + 0.3:
            out[(x, y)] = c
    return Spr(out)


def king_echo(spr, k=0.0, seed=0, phase=0):
    e = translucent(recolor_shadow(spr, ramp=("q", "m", "n", "N")), phase)
    return dissolve(e, k, seed=seed, rise=2, smoke="nN") if k > 0 else e


@sheet
def build_UmbHollowKing(outdir):
    idle = [king(sway=[0, 1, 1, 0][i], dy=[0, 0, 1, 1][i] * 0, cape=[0, 1, 2, 1][i], glint=i,
                 arm=(65 + 3 * (i % 2), 45), sword=62 + 3 * (i % 2), back_arm=(100 + 4 * (i % 2), 80),
                 head="calm" if i != 2 else "blaze") for i in range(4)]
    run = [king(lean=2, sway=[-2, -1, 0, -2, -1, 0][i], cape=3 + (i % 3), cape_lift=2 + (i % 2), glint=i,
                dy=-1 if i % 3 == 0 else 0, arm=(50, 30), sword=20 + 6 * (i % 2), back_arm=(120 + 10 * (i % 3), 100))
           for i in range(6)]
    # Eclipse Cleave: settle back, raise (1-2), hold at the top (3, long), HIT (4), follow-through, hold, recover, settle
    cleave = [
        king(lean=-1, sway=1, arm=(100, 140), sword=150, back_arm=(90, 60), cape=1),
        king(lean=-2, sway=2, arm=(-90, -100), sword=-95, back_arm=(60, 20), cape=0, head="blaze"),
        king(lean=-3, sway=2, arm=(-110, -125), sword=-125, back_arm=(40, 0), cape=0, head="blaze", blade_glow=True),
        king(lean=-3, sway=3, arm=(-115, -135), sword=-140, back_arm=(30, -10), cape=0, head="blaze", blade_glow=True,
             extra=[sparkle(-10, -44)]),
        king(lean=4, sway=-2, dx=1, arm=(-10, 20), sword=35, back_arm=(150, 120), cape=4, cape_lift=2, head="blaze",
             blade_glow=True, extra=[slash(4, -18, 18, -110, 50, thick=3, cols=("X", "c", "u", "U", "N", "n"))]),
        king(lean=4, sway=-2, dx=1, arm=(40, 70), sword=80, back_arm=(150, 130), cape=4, cape_lift=1,
             extra=[slash(4, -18, 18, -40, 60, thick=2, cols=("U", "N", "n"))]),
        king(lean=3, sway=-1, dx=1, arm=(50, 80), sword=95, back_arm=(140, 120), cape=3),
        king(lean=1, sway=0, arm=(60, 60), sword=80, back_arm=(110, 90), cape=2),
        king(),
    ]
    # Umbral Court: lower, arms wide (1), cape flares (2), crack blazes (3), hold, SUMMON (5) echoes burst out,
    # echoes fly off, arms lower, recover, settle
    wide = dict(arm=(-40, -60), sword=-70, back_arm=(-140, -120))
    court = [
        king(lean=-1, squash=1, arm=(100, 120), sword=110, back_arm=(80, 100), head="dim"),
        king(lean=0, cape=2, cape_lift=2, **wide),
        king(lean=0, cape=4, cape_lift=5, glint=1, **wide),
        king(lean=0, cape=5, cape_lift=6, glint=2, head="blaze", blade_glow=True, extra=[sparkle(1, -38, True)], **wide),
        king(lean=0, cape=5, cape_lift=6, glint=3, head="blaze", blade_glow=True,
             extra=[flash_ring(1, -20, 14, ("n", "N"))], **wide),
    ]
    stand = king(arm=(60, 60), sword=80, back_arm=(110, 90))
    court += [
        king_echo(stand.shift(-14, 0)).over(king_echo(stand.shift(14, 0), phase=1)).over(
            king(lean=0, cape=4, cape_lift=4, head="blaze", blade_glow=True, **wide)),
        king_echo(stand.shift(-20, 0), 0.35, 3).over(king_echo(stand.shift(20, 0), 0.35, 4, 1)).over(
            king(lean=0, cape=3, cape_lift=2, head="calm", arm=(-10, 10), sword=0, back_arm=(-170, -150))),
        king(lean=1, cape=2, arm=(40, 60), sword=60, back_arm=(130, 110)),
        king(lean=0, cape=1, arm=(60, 60), sword=75, back_arm=(115, 90)),
        king(),
    ]
    # Echo: the shadow copy of the cleave (raised, hit, follow-through, fading)
    echo = [king_echo(cleave[3]), king_echo(cleave[4], phase=1), king_echo(cleave[5]),
            king_echo(cleave[6], 0.55, 2, 1)]
    corpse_px = {}
    heap = ellipse_px(0, -3, 11, 3.2, "q")
    corpse_px.update(shard_fill(ellipse_px(-5, -2, 9, 2.4, "q"), seed=2))
    for (x, y), v in heap.items():
        if x > -6: corpse_px[(x, y)] = v
    corpse = Spr(corpse_px)
    c2 = Canvas(); c2.px = dict(corpse.px)
    c2.part(HK_CROWN["tilt"], 8, -3)
    for p in line_px(-2, -1, 13, -2): c2.put(p[0], p[1], "U")
    for p in line_px(-2, 0, 13, -1): c2.put(p[0], p[1], "n", over=False)
    c2.put(4, -5, "U"); c2.put(5, -5, "c"); c2.put(4, -4, "n")
    corpse = ground(c2.spr())
    death = [
        king(lean=-3, sway=2, arm=(-120, -80), sword=-60, back_arm=(-150, -110), head="blaze", crown="tilt", cape=2),
        king(lean=-1, squash=7, arm=(110, 140), sword=150, back_arm=(120, 150), head="dim", crown="tilt", cape=3, cape_lift=-2,
             extra=[small_shard(-14, -6, 200), small_shard(-10, -14, 250)]),
        dissolve(king(lean=0, squash=13, arm=(150, 170), sword=175, back_arm=(160, 175), head="dim", crown="tilt", cape=4),
                 0.35, seed=5, rise=3, smoke="nNU").over(corpse.shift(0, 0) if False else Spr({})),
        corpse,
    ]
    knock = [king(lean=-4, sway=3, arm=(-150, -120), sword=-110, back_arm=(-160, -130), head="dim", crown="tilt", cape=0, dx=-1)]
    anims = [
        ("Idle", idle, [0.22, 0.18, 0.22, 0.18]),
        ("Run", run, [0.1] * 6),
        ("Death", death, [0.14, 0.16, 0.18, 0.4]),
        ("Dead", [corpse], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Cleave", cleave, [0.14, 0.12, 0.12, 0.2, 0.05, 0.1, 0.14, 0.12, 0.14]),
        ("Court", court, [0.12, 0.14, 0.14, 0.18, 0.16, 0.08, 0.12, 0.12, 0.12, 0.14]),
        ("Echo", echo, [0.1, 0.05, 0.1, 0.14]),
    ]
    return build_sheet("UmbHollowKing", anims, outdir)


# ================================================================================================
# v0.7.2 tree expansion. Drawn at final size (no design scale): T2 <= 28 x 26, T3 <= 42 x 40.
# ================================================================================================
def shade_body(px, lit="n", hi="U", dark="m", base="q"):
    """Moonlit silhouette shading for a filled region: top-left rim lit, bottom-right rim dark."""
    out = dict(px)
    for (x, y), v in px.items():
        if v != base: continue
        up = (x, y - 1) not in px; left = (x - 1, y) not in px
        down = (x, y + 1) not in px; right = (x + 1, y) not in px
        if up and left: out[(x, y)] = hi
        elif up or left: out[(x, y)] = lit
        elif down or right: out[(x, y)] = dark
    return out


def nail_px(x, y, ang, ln=3, tip="c", mid="U", base="S", glint=False):
    """One glass nail: dark base, silver shaft, bright tip."""
    px = {}
    a = math.radians(ang)
    ex, ey = int(round(x + ln * math.cos(a))), int(round(y + ln * math.sin(a)))
    pts = line_px(int(round(x)), int(round(y)), ex, ey)
    for i, p in enumerate(pts):
        px[p] = base if i == 0 else (tip if i == len(pts) - 1 else mid)
    if glint:
        px[(ex, ey)] = "X"
    return px


# ------------------------------------------------------------------------------------------------
# 7. NAILSHADE (T2): hunched, gibbon-armed shadow; its back bristles with glass nails, its face is a
#    single shard of mirror with one eye behind it; the fingers are three long glass nails.
# ------------------------------------------------------------------------------------------------
NS_HEAD = {
    "calm": Part("""
..nnn..
.nqqqU.
nqqqUuu
qqqqUcu
qqqqUuU
.qqqqU.
..qq...
""", (2, 6)),
    "glare": Part("""
..nnn..
.nqqqU.
nqqqUuc
qqqqUXc
qqqqucU
.qqqqU.
..qq...
""", (2, 6)),
    "low": Part("""
.......
..nnn..
.nqqqU.
nqqqUuu
qqqqUcu
.qqqqUU
..qq...
""", (2, 6)),
    "hurt": Part("""
..nnn..
.nqqqs.
nqqqUus
qqqqqUu
qqqqqqU
.qqqqs.
..qq...
""", (2, 6)),
}


def rot_ellipse(cx, cy, ra, rb, ang, fill="q"):
    """Filled ellipse with semi-axis ra along angle ang (deg) and rb across it."""
    px = {}
    t = math.radians(ang); ca, sa = math.cos(t), math.sin(t)
    R = int(max(ra, rb)) + 2
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            dx, dy = x - cx, y - cy
            u = dx * ca + dy * sa; v = -dx * sa + dy * ca
            if (u / ra) ** 2 + (v / rb) ** 2 <= 1.0: px[(x, y)] = fill
    return px


def nailshade(lean=40, dx=0, dy=0, legs=((105, 75), (65, 110)), arms=((110, 95), (70, 95)), head="calm",
              fingers=(None, None), spread=(22, 22), glint=0, held=None, extra=(), nails=8, hip_y=-8, hunch=1.0):
    """A hunched pincushion of shadow. lean: tilt of the back mass forward from vertical (deg).
    arms: ((upper, fore) back, (upper, fore) front). fingers: finger-fan angle override per hand;
    held: angle of a big pin carried in the front hand."""
    c = Canvas()
    hip = (dx - 1, hip_y + dy)
    ang = -90 + lean
    a = math.radians(ang); ax, ay = math.cos(a), math.sin(a)
    nx, ny = -ay, ax                                   # belly side (forward-down)
    bc = (hip[0] + ax * 5.5, hip[1] + ay * 5.5)        # centre of the hunched back
    sh = (int(round(bc[0] + ax * 2.5 + nx * 3.6)), int(round(bc[1] + ay * 2.5 + ny * 3.6)))
    # back leg
    c.limb(hip[0] - 1, hip[1], [(4, legs[0][0]), (5, legs[0][1])], ["q", "q"], width=1, end=Part("qn", (0, 0)))
    # back arm (behind the body)
    ex_, ey_ = c.limb(sh[0] - 1, sh[1], [(6, arms[0][0]), (6, arms[0][1])], ["q", "q"])
    fa = fingers[0] if fingers[0] is not None else arms[0][1]
    for k in (-1, 0, 1):
        put_px(c, nail_px(ex_, ey_, fa + k * spread[0], 2, tip="U", mid="S", base="q"))
    # body: the hunched back mass + a narrow waist to the hips
    body = rot_ellipse(bc[0], bc[1], 6.2 * hunch, 4.6, ang)
    body.update(poly_px([(hip[0] - 2, hip[1] + 1), (hip[0] + 2, hip[1] + 1),
                         (bc[0] + nx * 3, bc[1] + ny * 3), (bc[0] - nx * 3, bc[1] - ny * 3)], "q"))
    body = shade_body(body)
    # a seam of moonlight down the spine of the back
    for t in (-0.6, -0.2, 0.2):
        k = (int(round(bc[0] + ax * 4 * t - nx * 2.6)), int(round(bc[1] + ay * 4 * t - ny * 2.6)))
        if body.get(k) == "q": body[k] = "n"
    put_px(c, body)
    # glass nails radiate out of the back (the side away from the belly)
    for i in range(nails):
        f = i / max(1, nails - 1)
        th = math.radians(ang + 200 + 145 * f)            # from behind-low, over the top, to the shoulders
        rx_ = 6.2 * hunch * 0.9; ry_ = 4.6 * 0.9
        u, v = math.cos(th - a) * rx_, math.sin(th - a) * ry_
        px0 = bc[0] + u * ax - v * ay; py0 = bc[1] + u * ay + v * ax
        na = math.degrees(math.atan2(py0 - bc[1], px0 - bc[0])) + 14 * math.sin(i * 2.3)
        ln = [2, 3, 4, 3, 5, 3, 4, 2, 3][i % 9]
        put_px(c, nail_px(px0, py0, na, ln, glint=(i == glint % nails)), over=True)
    # v0.10: its only parent is the Shade Imp (smoky tail below); the two back shards that were the Glimmer's blue
    # crystal are now its own rose glass
    for f, sz in ((0.3, 3), (0.75, 2)):
        th = math.radians(ang + 200 + 145 * f)
        u, v = math.cos(th - a) * 6.2 * hunch * 0.8, math.sin(th - a) * 4.6 * 0.8
        put_px(c, small_shard(bc[0] + u * ax - v * ay, bc[1] + u * ay + v * ax,
                              math.degrees(th) + 180, sz, ("c", "N", "n")))
    imp_tail(c, hip[0] - 1, hip[1] - 1, glint % 4, curl=-20)
    # head: hangs low and forward of the back, a mirror shard for a face
    hx, hy = int(round(bc[0] + ax * 5 + nx * 3.2)), int(round(bc[1] + ay * 5 + ny * 3.2)) + 3
    c.part(NS_HEAD[head], hx, hy)
    # front leg
    c.limb(hip[0] + 1, hip[1], [(4, legs[1][0]), (5, legs[1][1])], [("n", "q"), "n"], width=2, end=Part("nnU", (0, 0)))
    # front arm
    ex_, ey_ = c.limb(sh[0] + 1, sh[1], [(6, arms[1][0]), (6, arms[1][1])], [("n", "q"), "n"], width=2)
    c.put(ex_, ey_, "U")
    if held is not None:
        put_px(c, pin_px(ex_, ey_, held))
    else:
        fa = fingers[1] if fingers[1] is not None else arms[1][1]
        for k in (-1, 0, 1):
            put_px(c, nail_px(ex_, ey_, fa + k * spread[1], 3, glint=(k == 0 and glint % 2 == 1)))
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


def pin_px(x, y, ang, ln=10):
    """The big black pin of Shadow Pin: a long jet shaft, a pale mirror head, a bright point."""
    px = {}
    a = math.radians(ang)
    pts = line_px(int(round(x - 3 * math.cos(a))), int(round(y - 3 * math.sin(a))),
                  int(round(x + (ln - 3) * math.cos(a))), int(round(y + (ln - 3) * math.sin(a))))
    for i, p in enumerate(pts):
        px[p] = "u" if i == 0 else "c" if i == len(pts) - 1 else ("K" if i % 3 else "n")
    hx, hy = pts[0]
    px[(hx + int(round(math.sin(a))), hy - int(round(math.cos(a))))] = "U"
    px[(hx - int(round(math.sin(a))), hy + int(round(math.cos(a))))] = "U"
    return px


@sheet
def build_UmbNailshade(outdir):
    idle = [nailshade(dy=[0, 0, 1, 1][i], lean=[40, 41, 43, 41][i], glint=i * 3,
                      arms=((112 + 4 * (i % 2), 105), (40 - 5 * (i % 2), 100 + 4 * (i % 2))), fingers=(None, 60 + 6 * (i % 2)),
                      legs=((120, 80 + 4 * (i >= 2)), (70 - 4 * (i >= 2), 110)), head="calm" if i != 2 else "low")
            for i in range(4)]
    # gibbon lope: the long arms vault the body forward, legs tuck under
    cyc = [((140, 100), (45, 110)), ((120, 80), (65, 125)), ((95, 70), (95, 120)),
           ((45, 110), (140, 100)), ((65, 125), (120, 80)), ((95, 120), (95, 70))]
    arm_c = [((60, 90), (120, 100)), ((80, 100), (100, 95)), ((100, 105), (80, 85)),
             ((120, 100), (60, 90)), ((100, 95), (80, 100)), ((80, 85), (100, 105))]
    run = [nailshade(lean=52, dy=[-1, 0, 0, -1, 0, 0][i], legs=cyc[i], arms=arm_c[i], glint=i, head="calm")
           for i in range(6)]
    # Fling: back the hand up behind the head, whip it over (release 2), follow-through, recover
    fling = [
        nailshade(lean=30, dx=-1, arms=((110, 120), (-150, -120)), fingers=(None, -110), head="glare", glint=1),
        nailshade(lean=22, dx=-2, dy=1, arms=((120, 140), (-170, -150)), fingers=(None, -160), head="glare", glint=2,
                  legs=((130, 70), (55, 115))),
        nailshade(lean=55, dx=2, arms=((150, 160), (-20, 0)), fingers=(None, 0), spread=(22, 12), head="glare", glint=3,
                  legs=((140, 90), (40, 100)),
                  extra=[nail_px(14, -12, 0, 3), nail_px(13, -15, -12, 3), nail_px(13, -9, 12, 3),
                         {(18, -12): "c", (17, -16): "u", (17, -8): "u"}]),
        nailshade(lean=58, dx=2, arms=((140, 150), (30, 60)), head="calm", glint=4, legs=((135, 85), (45, 105))),
        nailshade(lean=50, dx=1, arms=((120, 110), (60, 80)), head="calm", glint=5),
        nailshade(lean=44, dx=0, arms=((105, 100), (75, 85)), glint=0),
        nailshade(lean=40, arms=((100, 95), (78, 88)), glint=1),
    ]
    # Shadow Pin: pluck a pin off the back (0-1), cock (2), hurl (3), melt into smoke (4), gone (5: pounce
    # here), re-form lunging (6), rake (7: hit), recover (8)
    lunge = nailshade(lean=62, dx=3, arms=((-40, -10), (-20, 10)), fingers=(-10, 15), head="glare",
                      legs=((165, 130), (25, 70)), glint=2)
    pin = [
        nailshade(lean=30, arms=((100, 95), (-120, -150)), fingers=(None, -170), head="calm", glint=3),
        nailshade(lean=28, dx=-1, arms=((110, 110), (-140, -170)), held=-160, head="glare", glint=4),
        nailshade(lean=20, dx=-2, dy=1, arms=((120, 130), (-170, 170)), held=-175, head="glare", glint=5,
                  legs=((130, 70), (55, 115)), extra=[sparkle(-10, -15)]),
        nailshade(lean=58, dx=2, arms=((150, 160), (-10, 0)), head="glare", glint=0, legs=((140, 90), (40, 100)),
                  extra=[pin_px(17, -12, 0, 12), {(22, -12): "X", (23, -12): "c"}]),
        dissolve(nailshade(lean=50, dx=1, arms=((130, 140), (40, 70)), head="low"), 0.55, seed=4, rise=3),
        dissolve(nailshade(lean=45, arms=((120, 120), (60, 80)), head="low"), 0.97, seed=6, rise=5, smoke="sm"),
        dissolve(lunge, 0.5, seed=8, rise=-1, smoke="sSN"),
        nailshade(lean=64, dx=4, arms=((-30, 0), (10, 40)), fingers=(0, 30), head="glare", legs=((170, 140), (20, 65)),
                  glint=3, extra=[slash(9, -11, 8, -75, 55, thick=2)]),
        nailshade(lean=48, dx=2, arms=((60, 90), (70, 100)), head="calm", glint=4),
    ]
    corpse = Spr.parse("""
.........U.c...........
..S.....qS.u..U........
.U.qnnnqqnUqqqnc.......
..nqqqqqqqqqqqqqqnUu...
..qqqqqqqmqqqqqqqqqUcu.
..nnqUqqqqnqqnqqUqqqUnU
""", feet_x=11)
    death = [
        nailshade(lean=10, dx=-2, arms=((-130, -100), (-110, -80)), head="hurt", glint=1, legs=((115, 80), (75, 110)),
                  extra=[nail_px(-6, -18, -150, 3), nail_px(-2, -21, -100, 3)]),
        nailshade(lean=60, dx=-1, dy=3, hip_y=-6, arms=((120, 160), (110, 150)), head="hurt", nails=4,
                  legs=((165, 60), (20, 150)), extra=[nail_px(-9, -10, 200, 3), nail_px(-11, -5, 160, 3)]),
        ground(rot_ccw(nailshade(lean=0, arms=((110, 100), (100, 90)), head="hurt", nails=5)).shift(1, 0)).over(
            Spr(nail_px(-12, -1, 180, 3))),
        corpse,
    ]
    knock = [nailshade(lean=8, dx=-2, arms=((-150, -120), (-120, -100)), head="hurt", legs=((110, 70), (80, 120)), glint=2)]
    anims = [
        ("Idle", idle, [0.18, 0.14, 0.18, 0.14]),
        ("Run", run, [0.07] * 6),
        ("Death", death, [0.1, 0.12, 0.14, 0.3]),
        ("Dead", [corpse], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Fling", fling, [0.12, 0.14, 0.05, 0.08, 0.1, 0.1, 0.12]),
        ("Pin", pin, [0.1, 0.12, 0.14, 0.05, 0.1, 0.3, 0.06, 0.06, 0.14]),
    ]
    return build_sheet("UmbNailshade", anims, outdir)


# ------------------------------------------------------------------------------------------------
# 8. GLOAMCOIL (T2): hooded shadow serpent; the hood carries a mirror-eye, the tail dissolves into ink.
# ------------------------------------------------------------------------------------------------
GC_HEAD = {
    "shut": Part("""
.nnn..
nqqqc.
qqqqqU
.qUuU.
""", (1, 3)),
    "open": Part("""
.nnn...
nqqqcU.
qqqqq.u
qqp....
.qqUu..
""", (1, 3)),
    "wide": Part("""
.nnnU..
nqqqXc.
qqqp..u
qqpp...
qqp..u.
.qUuU..
""", (1, 3)),
    "hurt": Part("""
.nnn..
nqqqU.
qqqqqs
.qqqU.
""", (1, 3)),
}


def bez(p0, p1, p2, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])


def put_outlined(c, px, col="K", only_over=True):
    """Paste px with a 1px dark seam wherever it overlaps what is already drawn (separates overlapping parts)."""
    c = getattr(c, "raw", c)
    for (x, y) in px:
        for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = (x + dx_, y + dy_)
            if k not in px and (k in c.px or not only_over):
                c.px[k] = col
    for k, v in px.items():
        c.px[k] = v


def tube(spine, radii, fill="q"):
    px = {}
    for (x, y), r in zip(spine, radii):
        px.update(ellipse_px(x, y, r, r, fill))
    return px


BELLY = ["n"]   # belly scute colour; the Gloamcoil switches it to gold ("gb") while it builds


def serpent_body(spine, radii, belly=True, seed=0):
    """Shade a tube: moonlit top rim, pale belly scutes on the underside, dark lower edge."""
    px = tube(spine, radii)
    out = shade_body(px, hi="N", dark="q")
    if belly:
        for i, ((x, y), r) in enumerate(zip(spine, radii)):
            if r < 1.2: continue
            bx, by = int(round(x)), int(round(y + r * 0.75))
            if out.get((bx, by)) in ("q", "m") and (i + seed) % 2 == 0: out[(bx, by)] = BELLY[0]
    return out


def gloamcoil(rear=1.0, lean=0.0, dx=0, phase=0.0, strike=0.0, hood=1.0, mouth="shut", flat=0.0, extra=(),
              wisp=0, glint=0, eye="open", tail_lift=0):
    """rear: neck height factor; lean: neck bend back(-)/forward(+); strike: head thrust forward (px);
    hood: hood flare factor; flat: 1 = pressed to the floor (dive); phase: body ripple."""
    c = Canvas()
    # ground coil: tail (left) to the neck base, rippling
    spine, radii = [], []
    n = 15
    for i in range(n):
        t = i / (n - 1)
        x = dx - 10.5 + 12.5 * t
        y = -1.6 - 1.2 * t - 0.9 * math.sin(phase + t * 5.5) * (1 - t * 0.5) - (tail_lift * (1 - t) ** 2)
        spine.append((x, y)); radii.append(0.7 + 2.3 * t ** 0.6)
    # neck: rises from the base toward the head
    base = (dx + 2.0, -3.2)
    h_y = -3 - (14 * rear) * (1 - flat) - 1.5 * flat
    head = (dx + 5 + strike + 3 * flat, h_y)
    ctrl = (dx - 2 + lean, (base[1] + h_y) * 0.55 - 2 * (1 - flat))
    neck = [bez(base, ctrl, head, k / 10.0) for k in range(11)]
    nr = [3.0 - 1.0 * (k / 10.0) for k in range(11)]
    # a coil looped behind the neck (the body doubles back on itself)
    if flat < 0.5:
        loop = [(dx - 2.5 + 5.2 * math.cos(math.radians(a_)), -4.2 + 2.4 * math.sin(math.radians(a_)) - 0.6 * math.sin(phase + a_ / 40.0))
                for a_ in range(200, 350, 15)]
        put_px(c, serpent_body(loop, [2.0] * len(loop), seed=2))
    # the ink tail: dissolving puffs behind the tip
    tx, ty = spine[0]
    for k, (ox, oy, col) in enumerate(((-1, 0, "n"), (-2, -1, "m"), (-3, 0, "s"), (-4, -1, "m"), (-3, -2, "s"),
                                      (-5, -2, "m"), (-6, -1, "s"))):
        if (k + wisp) % 4 != 3:
            c.put(int(round(tx)) + ox - (wisp % 2 if k > 3 else 0), int(round(ty)) + oy - (1 if k > 4 and wisp % 3 == 0 else 0), col, over=False)
    body = serpent_body(spine, radii, seed=int(phase * 3))
    put_px(c, body)
    # hood behind the head: a flat flare with a mirror-eye on it
    if hood > 0 and flat < 0.5:
        hc = neck[7]
        hp = rot_ellipse(hc[0] - 3.0 * hood, hc[1] + 0.8, 5.6 * hood, 3.8 * hood, math.degrees(math.atan2(neck[9][1] - neck[5][1], neck[9][0] - neck[5][0])))
        hp = {k: "n" for k in hp}
        for (x, y) in list(hp):
            if (x, y - 1) not in hp or (x - 1, y) not in hp: hp[(x, y)] = "N"
            elif (x + 1, y) not in hp or (x, y + 1) not in hp: hp[(x, y)] = "q"
            elif (x + y) % 3 == 0: hp[(x, y)] = "q"
        ex, ey = int(round(hc[0] - 4.6 * hood)), int(round(hc[1] + 0.2))
        if hood >= 0.8:
            for (ox, oy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
                hp[(ex + ox, ey + oy)] = "U" if (ox + oy + glint) % 3 else "u"
            hp[(ex, ey)] = "c" if eye == "open" else "n"
            hp[(ex - 1, ey - 2)] = "N"
        put_px(c, hp)
    nb = serpent_body(neck, nr, seed=1)
    put_outlined(c, nb)
    hx, hy = int(round(head[0])), int(round(head[1]))
    c.part(GC_HEAD[mouth], hx, hy)
    # v0.10 lineage: the Gloom Lurker's arched slate-blue legs run along the ground coil (a many-legged serpent)
    if flat < 0.9:
        for j, i in enumerate((1, 3, 5, 7, 9)):
            x, y = spine[i]; r = radii[i]
            sw = math.sin(phase * 2 + j * 1.7)
            knee = (x + 0.5 + sw * 0.6, y - r - 2.2)
            foot = (x + 2.2 + sw * 0.8, -0.0)
            for (a_, b_) in (((x, y - r * 0.5), knee), (knee, foot)):
                for p_ in line_px(*SK.spt(*a_), *SK.spt(*b_)):
                    c.raw.put(p_[0], p_[1], "ln")
            c.raw.put(*SK.spt(*knee), "lN")
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


@sheet
def build_UmbGloamcoil(outdir):
    BELLY[0] = "gb"
    try:
        return _build_gloamcoil(outdir)
    finally:
        BELLY[0] = "n"


def _build_gloamcoil(outdir):
    idle = [gloamcoil(phase=i * 0.5, lean=[0, 0.6, 1, 0.4][i], rear=[1, 1.02, 1.0, 0.98][i], hood=[1, 1.06, 1.1, 1.04][i],
                      wisp=i, glint=i, mouth="shut" if i != 2 else "open") for i in range(4)]
    # sidewind: the ripple travels down the body, neck held low and forward
    run = [gloamcoil(phase=i * math.pi / 3, rear=0.8, lean=2, strike=1, hood=0.85, wisp=i, glint=i % 3) for i in range(6)]
    # Strike: coil back (0-1), launch (2), BITE (3), hold (4), withdraw (5-6)
    strike = [
        gloamcoil(rear=1.05, lean=-3, strike=-3, hood=1.15, mouth="open", phase=0.3, glint=1),
        gloamcoil(rear=1.1, lean=-5, strike=-5, hood=1.25, mouth="wide", phase=0.6, glint=2, extra=[sparkle(-3, -16)]),
        gloamcoil(rear=0.85, lean=3, strike=6, hood=1.0, mouth="wide", phase=1.0, glint=0),
        gloamcoil(rear=0.6, lean=5, strike=11, hood=0.9, mouth="wide", phase=1.3,
                  extra=[slash(13, -8, 5, -70, 60, thick=1), sparkle(18, -8, True)]),
        gloamcoil(rear=0.62, lean=5, strike=10, hood=0.9, mouth="open", phase=1.5),
        gloamcoil(rear=0.8, lean=2, strike=4, hood=1.0, mouth="shut", phase=1.8),
        gloamcoil(rear=0.95, lean=0, strike=0, hood=1.0, mouth="shut", phase=2.1),
    ]
    # Slither: rear (0), plunge flat (1), dash pressed to the floor with an ink wake (2-5), rise (6-7)
    def wake(x0, k):
        px = {}
        for i in range(10):
            x = x0 - i
            if (i + k) % 3 == 0: continue
            px[(x, -1)] = "m" if i < 5 else "s"
            if i % 2 == k % 2: px[(x - 1, -2)] = "n" if i < 4 else "m"
        return px
    slither = [
        gloamcoil(rear=1.1, lean=-2, hood=1.2, mouth="open", glint=1),
        gloamcoil(rear=0.4, lean=4, strike=3, hood=0.6, mouth="shut", phase=0.5),
        gloamcoil(flat=1.0, phase=1.0, strike=4, hood=0, extra=[wake(-13, 0)]),
        gloamcoil(flat=1.0, phase=2.0, strike=4, hood=0, extra=[wake(-13, 1)]),
        gloamcoil(flat=1.0, phase=3.0, strike=4, hood=0, extra=[wake(-13, 2)]),
        gloamcoil(flat=1.0, phase=4.0, strike=4, hood=0, extra=[wake(-13, 0)]),
        gloamcoil(rear=0.5, lean=3, strike=3, hood=0.7, phase=4.5, mouth="open"),
        gloamcoil(rear=0.9, lean=0, hood=1.0, phase=5.0),
    ]
    dead = ground(gloamcoil(flat=1.0, phase=0.8, hood=0, mouth="hurt", strike=2))
    death = [
        gloamcoil(rear=1.15, lean=-6, strike=-4, hood=1.3, mouth="hurt", eye="shut"),
        gloamcoil(rear=0.6, lean=-2, strike=-1, hood=0.8, mouth="hurt", eye="shut", phase=1.0),
        dissolve(gloamcoil(flat=1.0, phase=1.6, hood=0, mouth="hurt", strike=1), 0.25, seed=3, rise=2, smoke="mns"),
        dead,
    ]
    knock = [gloamcoil(rear=1.0, lean=-6, strike=-5, hood=1.2, mouth="hurt", eye="shut", dx=-2)]
    anims = [
        ("Idle", idle, [0.18, 0.15, 0.18, 0.15]),
        ("Run", run, [0.07] * 6),
        ("Death", death, [0.1, 0.12, 0.14, 0.3]),
        ("Dead", [dead], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Strike", strike, [0.12, 0.16, 0.05, 0.06, 0.1, 0.1, 0.12]),
        ("Slither", slither, [0.1, 0.08, 0.08, 0.08, 0.08, 0.08, 0.1, 0.12]),
    ]
    return build_sheet("UmbGloamcoil", anims, outdir)


# ------------------------------------------------------------------------------------------------
# 9. ECLIPSE WYRM (T3): a heap of shadow coils with two necks: a void head with a white eye and its
#    mirror-glass twin; an eclipsed sun (black disc, silver corona) hangs between them.
# ------------------------------------------------------------------------------------------------
WY_HEAD = {
    "shut": Part("""
..nnnn...
.nqqqqnU.
nqqqqcXq.
qqqqqqqqU
qqqqqqqqU
.qqqUuUu.
""", (2, 4)),
    "open": Part("""
..nnnn....
.nqqqqnU..
nqqqqcXqU.
qqqqqqq.u.
qqqqpp....
qqqqpp.u..
.qqqUuUu..
""", (2, 4)),
    "wide": Part("""
..nnnnU...
.nqqqcXqu.
nqqqqqq..u
qqqqpp....
qqqpp.....
qqqqpp..u.
.qqqqUuu..
""", (2, 4)),
    "hurt": Part("""
..nnnn...
.nqqqqnU.
nqqqqqUq.
qqqqqqqqs
qqqqqqqqs
.qqqsUsU.
""", (2, 4)),
}
# v0.10: slate-blue glass (the Gloamcoil's Lurker legs) instead of the Twinned's pale silver
GLASS = {"q": "ln", "n": "lN", "N": "lU", "m": "lq", "K": "lq", "c": "K", "X": "lc", "U": "lU", "u": "c", "p": "K", "s": "lq"}


def glass_part(part):
    p = Part.__new__(Part); p.px = {k: GLASS.get(v, v) for k, v in part.px.items()}; return p


def glassify(px, seed=0):
    """Mirror-glass skin for a shaded tube: silver body, blue facets, bright upper rim."""
    out = {}
    for (x, y), v in px.items():
        h = hsh(x, y, seed)
        c = {"q": "ln", "n": "lN", "N": "lU", "m": "lq", "U": "c"}.get(v, v)
        if v == "q" and h < 0.18: c = "lq"
        elif v == "q" and h < 0.26: c = "lU"
        out[(x, y)] = c
    return out


def corona(cx, cy, r, glint=0, flare=0.0):
    """The eclipse: a black disc with a broken silver corona and a single bright bead."""
    px = {}
    for (x, y), v in ellipse_px(cx, cy, r, r, "K").items():
        px[(x, y)] = "K" if (x + y) % 5 else "q"
    rr = r + 1 + flare
    for t in range(0, 360, 6):
        if 200 < (t + glint * 40) % 360 < 240: continue          # the break in the ring
        a = math.radians(t)
        x, y = int(round(cx + rr * math.cos(a))), int(round(cy + rr * math.sin(a)))
        px[(x, y)] = "u" if (t // 12 + glint) % 3 else "U"
        if flare > 0.5 and t % 30 == 0:
            px[(int(round(cx + (rr + 1.5) * math.cos(a))), int(round(cy + (rr + 1.5) * math.sin(a))))] = "c"
    b = math.radians(-60 + glint * 40)
    px[(int(round(cx + rr * math.cos(b))), int(round(cy + rr * math.sin(b))))] = "X"
    return px


def wyrm(dx=0, phase=0.0, rear=1.0, front=(0, 0), back=(0, 0), fm="shut", bm="shut", flare=0.0, glint=0,
         tail_up=0.0, extra=(), sink=0, halo=True):
    """front/back: (x, y) offsets of the two heads; tail_up: 0 = tail on the floor, 1 = raised for the slam."""
    c = Canvas()
    oy = sink
    # tail: from the back of the heap; raised for the Constrict slam
    tail = []
    for k in range(9):
        t = k / 8.0
        x = dx - 9 - 8 * t + 3 * tail_up * t * t
        y = -2 + oy - 1.2 * math.sin(phase + t * 4) * (1 - tail_up) - tail_up * 14 * t * t
        tail.append((x, y))
    put_px(c, serpent_body(tail, [2.4 - 1.9 * k / 8.0 for k in range(9)], seed=3))
    # coil heap: three stacked loops, back to front
    def loop(cx, cy, rx, ry, r, a0, a1, seed, pa=0.0):
        pts = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)) - 0.7 * math.sin(phase + pa + a / 50.0))
               for a in range(a0, a1, 10)]
        return serpent_body(pts, [r] * len(pts), seed=seed)
    put_px(c, loop(dx - 1, -4.5 + oy, 10.5, 3.2, 3.0, 180, 361, 4))
    put_outlined(c, loop(dx - 1, -4.5 + oy, 10.5, 3.2, 3.0, 0, 181, 5))
    put_outlined(c, loop(dx - 1, -10 + oy, 7.5, 2.6, 2.7, 160, 400, 6, 1.0))
    base_f = (dx + 3, -13 + oy); base_b = (dx - 3, -13 + oy)
    hf = (dx + 10 + front[0], -23 * rear + oy + front[1]); hb = (dx - 1 + back[0], -29 * rear + oy + back[1])
    # the eclipse hangs behind the necks
    if halo:
        put_px(c, corona(dx + 5, -31 * rear + oy, 4.2, glint, flare))
    def glass_neck():
        cb = (dx - 8 + max(0, back[0]) * 0.6, (base_b[1] + hb[1]) * 0.5)
        nk = [bez(base_b, cb, hb, k / 10.0) for k in range(11)]
        put_outlined(c, glassify(serpent_body(nk, [3.0 - 1.1 * k / 10.0 for k in range(11)], seed=7), 7))
        c.part(glass_part(WY_HEAD[bm]), int(round(hb[0])), int(round(hb[1])))

    def void_neck():
        cf = (dx + 2, (base_f[1] + hf[1]) * 0.5 + 2)
        nk = [bez(base_f, cf, hf, k / 10.0) for k in range(11)]
        put_outlined(c, serpent_body(nk, [3.3 - 1.1 * k / 10.0 for k in range(11)], seed=8))
        c.part(WY_HEAD[fm], int(round(hf[0])), int(round(hf[1])))
    # the glass head strikes over the void one
    for fn in ((void_neck, glass_neck) if back[0] >= 8 else (glass_neck, void_neck)):
        fn()
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


@sheet
def build_UmbEclipseWyrm(outdir):
    BELLY[0] = "gb"            # v0.9: the Gloamcoil's gold belly scutes
    try:
        return _build_wyrm(outdir)
    finally:
        BELLY[0] = "n"


def _build_wyrm(outdir):
    idle = [wyrm(phase=i * 0.6, rear=[1, 1.01, 1.02, 1.01][i], front=(0, [0, -1, 0, 1][i]), back=([0, 1, 0, -1][i], 0),
                 glint=i, fm="shut" if i != 2 else "open") for i in range(4)]
    run = [wyrm(phase=i * math.pi / 3, rear=0.9, front=(2, 2 + (i % 2)), back=(1, 1 - (i % 2)), glint=i % 4) for i in range(6)]
    # Twin Fangs: both rear (0-1), the void head drives in (2) and BITES (3), the glass head
    # rears (4) and BITES over it (5), both withdraw (6-8)
    fangs = [
        wyrm(rear=1.06, front=(-3, -1), back=(-2, 0), fm="open", bm="open", glint=1),
        wyrm(rear=1.1, front=(-5, -2), back=(-3, -1), fm="wide", bm="open", glint=2, flare=0.6),
        wyrm(rear=1.0, front=(3, 5), back=(-3, -1), fm="wide", bm="open", glint=3),
        wyrm(rear=0.95, front=(9, 12), back=(-2, 0), fm="wide", bm="wide", glint=0,
             extra=[slash(22, -11, 6, -80, 60, thick=2), sparkle(25, -10, True)]),
        wyrm(rear=0.98, front=(5, 9), back=(2, 2), fm="open", bm="wide", glint=1),
        wyrm(rear=0.96, front=(2, 7), back=(12, 12), fm="shut", bm="wide", glint=2,
             extra=[slash(19, -17, 6, -80, 60, thick=2, cols=("c", "B", "b", "U")), sparkle(23, -16, True)]),
        wyrm(rear=1.0, front=(1, 3), back=(6, 6), fm="shut", bm="open", glint=3),
        wyrm(rear=1.0, front=(0, 1), back=(2, 2), glint=0),
        wyrm(rear=1.0, glint=1),
    ]
    # Constrict: rear up (0-1), tail lifts (2), SLAM (3: the coil ring rises at the hero), hiss (4-6),
    # the heads snap together as the ring closes (7), settle (8)
    constrict = [
        wyrm(rear=1.08, front=(-2, -1), back=(-1, -1), fm="open", bm="open", tail_up=0.4, glint=1),
        wyrm(rear=1.12, front=(-3, -2), back=(-2, -2), fm="wide", bm="wide", tail_up=0.8, glint=2, flare=0.7),
        wyrm(rear=1.14, front=(-3, -2), back=(-2, -3), fm="wide", bm="wide", tail_up=1.0, glint=3, flare=1.0,
             extra=[sparkle(-14, -16)]),
        wyrm(rear=0.96, front=(1, 2), back=(0, 1), fm="open", bm="open", tail_up=0.0, glint=0, sink=1,
             extra=[{(-20, -1): "U", (-19, -2): "u", (-21, -2): "u", (-18, 0): "S", (-22, 0): "S", (-20, -3): "c"}]),
        wyrm(rear=1.02, front=(2, 0), back=(-2, 0), fm="wide", bm="open", glint=1, flare=0.6),
        wyrm(rear=1.03, front=(1, -1), back=(-1, 1), fm="open", bm="wide", glint=2, flare=0.9),
        wyrm(rear=1.02, front=(2, 0), back=(-2, 0), fm="wide", bm="open", glint=3, flare=0.6),
        wyrm(rear=1.0, front=(-2, -3), back=(4, 4), fm="wide", bm="wide", glint=0, flare=1.0,
             extra=[sparkle(14, -26, True)]),
        wyrm(rear=1.0, glint=1),
    ]
    dead = wyrm(rear=0.35, front=(6, 7), back=(-4, 6), fm="hurt", bm="hurt", halo=False, sink=1)
    death = [
        wyrm(rear=1.1, front=(-4, -2), back=(-3, -2), fm="hurt", bm="hurt", flare=1.0, glint=2),
        wyrm(rear=0.8, front=(3, 3), back=(-4, 2), fm="hurt", bm="hurt", glint=3),
        dissolve(wyrm(rear=0.5, front=(5, 6), back=(-4, 5), fm="hurt", bm="hurt", halo=False), 0.2, seed=4, rise=3, smoke="nNs")
            .over(Spr(small_shard(-4, -20, 200)).over(Spr(small_shard(6, -18, -30)))),
        dead,
    ]
    knock = [wyrm(rear=1.05, front=(-5, -2), back=(-4, -2), fm="hurt", bm="open", dx=-2, glint=1)]
    anims = [
        ("Idle", idle, [0.22, 0.18, 0.22, 0.18]),
        ("Run", run, [0.1] * 6),
        ("Death", death, [0.14, 0.16, 0.18, 0.4]),
        ("Dead", [dead], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Fangs", fangs, [0.14, 0.14, 0.06, 0.06, 0.08, 0.06, 0.1, 0.12, 0.14]),
        ("Constrict", constrict, [0.12, 0.14, 0.16, 0.06, 0.16, 0.16, 0.16, 0.1, 0.16]),
    ]
    return build_sheet("UmbEclipseWyrm", anims, outdir)


# ------------------------------------------------------------------------------------------------
# 10. GLASS SERAPH (T3): a hovering saint of leaded mirror-glass: blade-feather wings, a cracked halo,
#     a blank mirror for a face. No legs: the body tapers to a hanging shard.
# ------------------------------------------------------------------------------------------------
def leaded(px, seed=0, panes=("S", "U", "b", "S", "n", "B"), lead="q", cell=2.6, glint=0):
    """Stained-glass fill: irregular panes of glass separated by dark lead seams, lit top-left rim."""
    out = {}
    for (x, y) in px:
        u = x * 0.85 + y * 0.5 + seed * 0.31
        v = x * 0.5 - y * 0.9 + seed * 0.17
        cu, cv = math.floor(u / cell), math.floor(v / cell)
        fu, fv = u / cell - cu, v / cell - cv
        col = panes[int(hsh(int(cu), int(cv), 11 + seed) * len(panes)) % len(panes)]
        if fu < 0.24 or fv < 0.24: col = lead
        elif hsh(int(cu) + glint, int(cv), 13) < 0.12 and fu > 0.5 and fv > 0.5: col = "c"
        out[(x, y)] = col
    for (x, y) in list(out):
        if (x, y - 1) not in out or (x - 1, y) not in out: out[(x, y)] = "u" if (x + y) % 3 else "U"
        elif (x + 1, y) not in out or (x, y + 1) not in out: out[(x, y)] = "n"
    return out


def feather(root, ang, length, width=1.6, far=False):
    a = math.radians(ang); nrm = (-math.sin(a), math.cos(a))
    tip = (root[0] + length * math.cos(a), root[1] + length * math.sin(a))
    mid = (root[0] + length * 0.45 * math.cos(a), root[1] + length * 0.45 * math.sin(a))
    pts = [(root[0] + nrm[0] * 0.6, root[1] + nrm[1] * 0.6), (mid[0] + nrm[0] * width, mid[1] + nrm[1] * width), tip,
           (mid[0] - nrm[0] * width * 0.7, mid[1] - nrm[1] * width * 0.7), (root[0] - nrm[0] * 0.6, root[1] - nrm[1] * 0.6)]
    px = poly_px(pts, "b" if far else "B")
    for (x, y) in list(px):
        if (x, y - 1) not in px or (x - 1, y) not in px: px[(x, y)] = ("U" if far else "c")
        elif (x + 1, y) not in px or (x, y + 1) not in px: px[(x, y)] = ("n" if far else "U")
    for p in line_px(int(round(root[0])), int(round(root[1])), int(round(mid[0])), int(round(mid[1]))):
        if p in px: px[p] = "n" if far else "b"            # the lead spine of the feather
    px[(int(round(tip[0])), int(round(tip[1])))] = "U" if far else "c"
    return px


SR_FACE = {
    "calm": Part("""
.UuU.
UuccU
uuKcu
UucuU
.UuU.
""", (2, 4)),
    "glare": Part("""
.UuU.
UcXcU
uKXKu
UccuU
.UuU.
""", (2, 4)),
    "dim": Part("""
.sUs.
sUuUs
UsKUU
sUUUs
.sUs.
""", (2, 4)),
}


def halo(cx, cy, glint=0, flare=0.0, broken=True):
    px = {}
    rx, ry = 4.6 + flare, 4.6 + flare
    for t in range(0, 360, 8):
        if broken and 20 < t < 50: continue
        a = math.radians(t)
        x, y = int(round(cx + rx * math.cos(a))), int(round(cy + ry * math.sin(a)))
        px[(x, y)] = "c" if (t // 24 + glint) % 4 == 0 else ("u" if 150 < t < 330 else "U")
    if flare > 0.5:
        for t in range(0, 360, 45):
            a = math.radians(t)
            px[(int(round(cx + (rx + 2) * math.cos(a))), int(round(cy + (ry + 1.5) * math.sin(a))))] = "B"
    return px


def seraph(dy=0, dx=0, lean=0, wings=1.0, wphase=0.0, arm=(70, 100), back_arm=(110, 90), face="calm", glint=0,
           hflare=0.0, extra=(), hover=4, broken_wings=0, droop=0):
    """wings: spread factor (0.5 folded, 1 rest, 1.6 flung wide); wphase: breathing of the wing fan."""
    c = Canvas()
    by = -hover + dy
    waist = (dx, by - 12); sh = (dx + lean, by - 20 + droop)
    # wings: far fan first (darker), from just behind the shoulders
    root = (sh[0] - 2, sh[1] + 1)
    fan = [(-178, 11), (-152, 14), (-127, 14), (-103, 11)]
    for i, (a0, ln) in enumerate(fan):
        if i < broken_wings: continue
        a = -90 + (a0 + 90) * wings + 4 * math.sin(wphase + i)
        put_px(c, feather((root[0] + 2, root[1] - 2), a + 14, ln * (0.85 if wings < 0.8 else 0.95), width=2.0, far=True))
    # hanging shard body (tapers to a point under the waist)
    body = poly_px([(waist[0] - 4.5, waist[1]), (waist[0] + 4.5, waist[1]), (dx + 4.5 + lean * 0.3, by - 6),
                    (dx + 1.5, by - 2), (dx, by + 0.5), (dx - 1.5, by - 2), (dx - 4.5, by - 6)], "q")
    put_px(c, leaded(body, seed=1, glint=glint))
    # back arm
    hx, hy = c.limb(sh[0] - 1, sh[1] + 1, [(5, back_arm[0]), (5, back_arm[1])], ["q", "n"])
    c.put(hx, hy, "U")
    # torso: narrow leaded bodice
    torso = poly_px([(waist[0] - 2.5, waist[1] + 1), (waist[0] + 2.5, waist[1] + 1), (sh[0] + 3.2, sh[1]), (sh[0] - 3.4, sh[1])], "q")
    put_outlined(c, leaded(torso, seed=4, panes=("n", "S", "b", "n", "U"), glint=glint))
    # near wing fan over the body
    for i, (a0, ln) in enumerate(fan):
        if i + 1 < broken_wings: continue
        a = -90 + (a0 + 90) * wings + 5 * math.sin(wphase + i + 0.5)
        put_px(c, feather(root, a, ln, width=2.2))
    # head + halo
    hd = (sh[0] + 1, sh[1] - 1)
    put_px(c, halo(hd[0] - 0.5, hd[1] - 2.5, glint, hflare, broken=True))
    c.part(SR_FACE[face], hd[0], hd[1])
    # front arm (glass hand)
    hx, hy = c.limb(sh[0] + 1, sh[1] + 1, [(5, arm[0]), (5, arm[1])], [("n", "q"), "n"], width=2)
    c.put(hx, hy, "u"); c.put(hx + 1, hy, "c")

    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


def glass_feather_px(x, y, ang=0, ln=5):
    return feather((x, y), ang, ln, width=1.0)


@sheet
def build_UmbGlassSeraph(outdir):
    idle = [seraph(dy=[0, -1, -1, 0][i], wphase=i * 1.57, glint=i, wings=[1, 1.04, 1.06, 1.02][i],
                   arm=(70 + 4 * (i % 2), 100), back_arm=(110 - 4 * (i % 2), 90)) for i in range(4)]
    run = [seraph(dy=[0, -1, -1, 0, -1, -1][i], lean=2, wings=0.75, wphase=i, glint=i % 4,
                  arm=(40, 70), back_arm=(140, 120)) for i in range(6)]
    # Feathers: wings draw forward-up (0-1), the wing fan whips and the hand flicks (2), RELEASE (3), recover
    feathers = [
        seraph(lean=-1, wings=1.3, wphase=0.0, arm=(-60, -100), back_arm=(140, 120), face="glare", glint=1),
        seraph(lean=-2, dy=-1, wings=1.45, wphase=0.6, arm=(-100, -140), back_arm=(150, 130), face="glare", glint=2,
               extra=[sparkle(4, -32)]),
        seraph(lean=2, wings=0.8, wphase=1.2, arm=(-20, -10), back_arm=(120, 100), face="glare", glint=3),
        seraph(lean=3, wings=0.7, wphase=1.6, arm=(0, 5), back_arm=(120, 100), face="calm", glint=0,
               extra=[glass_feather_px(13, -17, 0, 6), glass_feather_px(12, -21, -14, 5), glass_feather_px(12, -13, 14, 5)]),
        seraph(lean=2, wings=0.85, wphase=2.0, arm=(30, 50), back_arm=(115, 95), glint=1),
        seraph(lean=1, wings=0.95, wphase=2.4, arm=(55, 85), back_arm=(112, 92), glint=2),
        seraph(wings=1.0, wphase=2.8, glint=3),
    ]
    # Prism: arms rise (0-1), wings fling wide (2), the halo blazes (3), CAST (4: the panes rise), hold (5-6), lower
    prism = [
        seraph(lean=0, wings=1.1, arm=(-30, -60), back_arm=(-150, -120), glint=0),
        seraph(lean=0, dy=-1, wings=1.3, arm=(-60, -90), back_arm=(-120, -90), face="glare", glint=1, hflare=0.4),
        seraph(lean=0, dy=-2, wings=1.55, arm=(-75, -100), back_arm=(-105, -80), face="glare", glint=2, hflare=0.8),
        seraph(lean=0, dy=-2, wings=1.6, arm=(-80, -95), back_arm=(-100, -85), face="glare", glint=3, hflare=1.2,
               extra=[sparkle(1, -42, True)]),
        seraph(lean=0, dy=-1, wings=1.5, arm=(-20, 0), back_arm=(-160, 180), face="glare", glint=0, hflare=1.0,
               extra=[sparkle(-12, -22), sparkle(14, -24), sparkle(2, -6, True)]),
        seraph(lean=0, dy=-1, wings=1.4, arm=(-10, 10), back_arm=(-170, 170), face="calm", glint=1, hflare=0.6),
        seraph(lean=0, wings=1.25, arm=(10, 40), back_arm=(170, 150), glint=2, hflare=0.3),
        seraph(lean=0, wings=1.1, arm=(45, 80), back_arm=(130, 110), glint=3),
        seraph(wings=1.0, glint=0),
    ]
    def glass_heap(seed):
        px = {}
        rnd = random.Random(seed)
        heap = ellipse_px(0, -2, 10, 2.4, "q")
        px.update(leaded(heap, seed=seed, panes=("S", "U", "b", "n", "B")))
        for _ in range(7):
            px.update(small_shard(rnd.randint(-12, 12), rnd.randint(-3, -1), rnd.choice((0, 30, 150, 200)), 3, ("c", "B", "U")))
        px.update(halo(6, -1, 1, 0.0))
        return ground(Spr(px))
    dead = glass_heap(3)
    death = [
        seraph(lean=-2, wings=1.5, arm=(-130, -100), back_arm=(-140, -110), face="dim", glint=2, hflare=1.0,
               extra=[small_shard(-14, -28, 200), small_shard(-10, -34, 240)]),
        seraph(lean=-1, dy=2, hover=2, wings=0.7, broken_wings=2, droop=2, arm=(110, 140), back_arm=(120, 150), face="dim",
               extra=[small_shard(-12, -12, 160), small_shard(-6, -8, 120), small_shard(9, -6, 30)]),
        dissolve(seraph(dy=5, hover=0, wings=0.5, broken_wings=4, droop=4, arm=(130, 160), back_arm=(140, 170), face="dim"),
                 0.45, seed=2, rise=2, smoke="UbS").over(glass_heap(5)),
        dead,
    ]
    knock = [seraph(lean=-3, wings=1.3, wphase=1.0, arm=(-150, -120), back_arm=(-160, -130), face="dim", dx=-1)]
    anims = [
        ("Idle", idle, [0.2, 0.18, 0.2, 0.18]),
        ("Run", run, [0.09] * 6),
        ("Death", death, [0.12, 0.14, 0.16, 0.4]),
        ("Dead", [dead], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Feathers", feathers, [0.12, 0.14, 0.06, 0.06, 0.1, 0.1, 0.12]),
        ("Prism", prism, [0.1, 0.12, 0.12, 0.14, 0.08, 0.14, 0.12, 0.12, 0.14]),
    ]
    return build_sheet("UmbGlassSeraph", anims, outdir)


# ------------------------------------------------------------------------------------------------
# 11. THE UNBLINKING (T3): a great void eye set in a broken oval mirror-frame, hanging over the floor
#     on a skirt of shadow tendrils.
# ------------------------------------------------------------------------------------------------
def eye_ball(cx, cy, r, look=(1, 0), lid=0.0, pupil=1.0, glow=False, cracked=0):
    """lid: 0 open .. 1 shut. pupil: pupil radius factor. look: pupil offset (px)."""
    px = {}
    ball = ellipse_px(cx, cy, r, r * 0.92, "q")
    for (x, y) in ball:
        d = math.hypot(x - cx, y - cy) / r
        v = "m" if d > 0.82 else "q"
        if (x * 3 + y * 5) % 11 == 0 and d > 0.5: v = "n"           # violet veins
        px[(x, y)] = v
    ix, iy = cx + look[0], cy + look[1]
    ir = r * 0.55
    for (x, y) in ellipse_px(ix, iy, ir, ir, "U"):
        if (x, y) not in px: continue
        d = math.hypot(x - ix, y - iy) / ir
        px[(x, y)] = ("c" if glow else "B") if d > 0.78 else ("u" if glow else "b") if d > 0.55 else ("B" if glow else "U")
    pr = max(0.6, ir * 0.45 * pupil)
    for (x, y) in ellipse_px(ix, iy, pr * 0.8, pr * 1.2, "K"):
        if (x, y) in px: px[(x, y)] = "K"
    px[(int(round(ix - pr * 0.6)), int(round(iy - pr * 0.9)))] = "X"
    # moonlit top rim of the ball
    for (x, y) in list(px):
        if (x, y - 1) not in px and px[(x, y)] in "qm": px[(x, y)] = "N" if (x + y) % 2 else "n"
    if cracked:
        rnd = random.Random(cracked)
        for _ in range(cracked):
            x, y, d = ix, iy, rnd.uniform(0, 360)
            for st in range(int(r)):
                d += rnd.uniform(-30, 30)
                x += math.cos(math.radians(d)); y += math.sin(math.radians(d))
                k = (int(round(x)), int(round(y)))
                if k in px: px[k] = "c" if st < 3 else "u"
    # lids close from top and bottom
    if lid > 0:
        top = cy - r + 2 * r * lid * 0.55; bot = cy + r - 2 * r * lid * 0.45
        for (x, y) in list(px):
            if y < top: px[(x, y)] = "q" if y < top - 1 else "n"
            elif y > bot: px[(x, y)] = "q" if y > bot + 1 else "m"
            elif lid >= 0.98: px[(x, y)] = "K"
        if lid >= 0.98:
            for (x, y) in list(px):
                if abs(y - (top + bot) / 2) < 0.6: px[(x, y)] = "N"
    return px


def mirror_frame(cx, cy, rx, ry, glint=0, gaps=((40, 75), (200, 222)), spin=0):
    """Broken oval of silver mirror-frame around the eye, with a few loose shards."""
    px = {}
    for t in range(0, 360, 4):
        tt = (t + spin) % 360
        if any(a <= tt < b for a, b in gaps): continue
        a = math.radians(t)
        for w in (0, 1):
            x = int(round(cx + (rx + w) * math.cos(a))); y = int(round(cy + (ry + w) * math.sin(a)))
            if w == 0:
                px[(x, y)] = "u" if 180 < t < 300 else "S"
            else:
                px.setdefault((x, y), "s" if 30 < t < 150 else "U")
    for t in (60 + spin, 212 + spin):
        a = math.radians(t)
        x = int(round(cx + (rx + 2.5) * math.cos(a))); y = int(round(cy + (ry + 2.5) * math.sin(a)))
        px.update(small_shard(x, y, t + 90, 3, ("c", "U", "S")))
    g = math.radians(200 + glint * 25)
    px[(int(round(cx + rx * math.cos(g))), int(round(cy + ry * math.sin(g))))] = "X"
    return px


def tendrils(cx, top, n=5, length=10, phase=0.0, trail=0.0, curl=1.0):
    c = Canvas()
    for i in range(n):
        x0 = cx - 6 + i * 3
        ln = length - abs(i - (n - 1) / 2.0) * 1.5
        x, y = float(x0), float(top)
        for k in range(int(ln)):
            ang = 90 + 25 * curl * math.sin(phase + i * 1.3 + k * 0.6) - trail * 40
            nx_, ny_ = x + math.cos(math.radians(ang)), y + math.sin(math.radians(ang))
            for p in line_px(int(round(x)), int(round(y)), int(round(nx_)), int(round(ny_))):
                c.put(p[0], p[1], "q" if k < ln * 0.5 else ("n" if k < ln - 2 else "N"))
                if k % 3 == 1 and k < ln - 2: c.put(p[0] + 1, p[1], "lc")   # v0.10: the Witch's teal
                if k < 3: c.put(p[0] - 1, p[1], "q", over=False)
            x, y = nx_, ny_
    return c.px


def unblinking(dy=0, dx=0, look=(1, 0), lid=0.0, pupil=1.0, glow=False, glint=0, phase=0.0, trail=0.0,
               spin=0, extra=(), cracked=0, hover=0, frame=True, sink=0):
    c = Canvas()
    cx, cy = dx, -21 + dy + hover + sink
    put_px(c, tendrils(cx, cy + 6, 5, 12, phase, trail))
    if frame:
        put_px(c, mirror_frame(cx, cy, 11, 12, glint, spin=spin))
    put_outlined(c, eye_ball(cx, cy, 8.5, look, lid, pupil, glow, cracked))
    s = c.spr()
    for item in extra:
        s = s.over(Spr(item))
    return ground(s)


def beam_px(x, y, ln, k=0):
    px = {}
    for i in range(ln):
        px[(x + i, y)] = "c" if i < 3 else ("u" if (i + k) % 4 else "N")
        if i % 2 == k % 2: px[(x + i, y - 1)] = "N"
        if i % 3 == k % 3: px[(x + i, y + 1)] = "n"
    return px


@sheet
def build_UmbUnblinking(outdir):
    idle = [unblinking(dy=[0, -1, -1, 0][i], look=[(1, 0), (2, -1), (1, 0), (0, 1)][i], phase=i * 1.57, glint=i,
                       spin=[0, 4, 8, 4][i]) for i in range(4)]
    run = [unblinking(dy=[0, -1, -1, 0, -1, -1][i], look=(2, 0), phase=i * 1.05, trail=0.6, glint=i % 4, spin=i * 3)
           for i in range(6)]
    # Gaze: the pupil pins down (0-1), the iris ignites (2), the beam fires (3) and holds (4-5), fades (6-7)
    gaze = [
        unblinking(look=(2, 0), pupil=0.5, glint=0),
        unblinking(look=(3, 0), pupil=0.3, glow=True, glint=1, extra=[sparkle(4, -21)]),
        unblinking(look=(3, 0), pupil=0.3, glow=True, glint=2, dx=-1, extra=[sparkle(12, -21, True)]),
        unblinking(look=(3, 0), pupil=0.25, glow=True, glint=3, dx=-1, extra=[beam_px(11, -21, 8, 0)]),
        unblinking(look=(3, 0), pupil=0.25, glow=True, glint=0, dx=-1, extra=[beam_px(11, -21, 8, 1)]),
        unblinking(look=(3, 0), pupil=0.3, glow=True, glint=1, extra=[beam_px(11, -21, 6, 2)]),
        unblinking(look=(2, 0), pupil=0.7, glint=2),
        unblinking(look=(1, 0), pupil=1.0, glint=3),
    ]
    # Lights Out: the eye narrows (0-1) and shuts (2), the dark pours out (3), it is gone (4: blink here),
    # reappears shut (5), snaps open glaring (6) and sweeps its gaze (7), settles (8)
    shut = unblinking(lid=1.0, glint=1)
    blackout = [
        unblinking(lid=0.4, look=(0, 1), glint=0),
        unblinking(lid=0.75, look=(0, 1), glint=1, extra=[gloom_cloud(-12, -8, 3, 1)]),
        unblinking(lid=1.0, glint=2, extra=[gloom_cloud(-13, -8, 4, 2), gloom_cloud(13, -10, 3, 3)]),
        ground(dissolve(shut, 0.5, seed=3, rise=3, smoke="qmn").over(Spr(gloom_cloud(0, -6, 9, 4, 0.8)))),
        Spr({k: v for k, v in gloom_cloud(0, -5, 7, 5, 0.25).items() if k[1] <= 0}),
        dissolve(shut, 0.35, seed=5, rise=-1, smoke="qmn"),
        unblinking(lid=0.0, look=(3, 0), pupil=0.3, glow=True, glint=3, extra=[sparkle(13, -22, True)]),
        unblinking(lid=0.0, look=(3, -1), pupil=0.25, glow=True, glint=0, extra=[beam_px(11, -22, 8, 1)]),
        unblinking(look=(1, 0), glint=1),
    ]
    dead = unblinking(sink=13, lid=1.0, frame=False, cracked=3, phase=2.0)
    dead = ground(dead.over(Spr(small_shard(-12, -1, 0, 3, ("u", "U", "S")))).over(Spr(small_shard(11, -2, 160, 4, ("c", "U", "S")))))
    death = [
        unblinking(look=(-1, -2), pupil=1.6, cracked=2, glint=2, spin=20),
        unblinking(dy=4, look=(0, 2), pupil=1.8, lid=0.4, cracked=4, spin=40, frame=False,
                   extra=[small_shard(-13, -14, 200), small_shard(12, -18, -20), small_shard(-9, -27, 250)]),
        dissolve(unblinking(dy=9, lid=0.8, cracked=5, frame=False), 0.3, seed=7, rise=2, smoke="nNq"),
        dead,
    ]
    knock = [unblinking(dx=-1, look=(-2, -1), pupil=1.5, lid=0.3, glint=1, spin=10, trail=-0.4)]
    anims = [
        ("Idle", idle, [0.2, 0.16, 0.2, 0.16]),
        ("Run", run, [0.09] * 6),
        ("Death", death, [0.12, 0.14, 0.16, 0.4]),
        ("Dead", [dead], [0.2]),
        ("Statue", [edge_pass(idle[0]).stone()], [0.2]),
        ("Knockback", knock, [0.2]),
        ("Portrait", [idle[0]], [0.2]),
        ("Gaze", gaze, [0.1, 0.14, 0.12, 0.12, 0.12, 0.12, 0.1, 0.12]),
        ("Blackout", blackout, [0.1, 0.12, 0.14, 0.1, 0.24, 0.08, 0.1, 0.14, 0.14]),
    ]
    return build_sheet("UmbUnblinking", anims, outdir)


# ------------------------------------------------------------------------------------------------
# v0.7.2 FX: nails, pins, the coil noose, the gaze beam, mirror panes, glass feathers
# ------------------------------------------------------------------------------------------------
def fx_nail():
    frames = []
    for i in range(4):
        px = nail_px(-3, 0, 0, 6, tip="c", mid="U", base="S")
        px[(3, 0)] = "X" if i % 2 == 0 else "c"
        px[(-1, -1 if i % 2 else 1)] = "u"
        px[(-5 - (i % 2), 0)] = "n"; px[(-7, 0)] = "q" if i % 2 else "n"
        px[(-1 + i, -1)] = "c"                       # v0.8: a glint runs along the shaft (frames 2-3 were copies of 0-1)
        frames.append(Spr(px))
    return frames


def fx_pin():
    frames = []
    for i in range(4):
        px = {k: ("n" if v == "K" else "N" if v == "n" else v) for k, v in pin_px(-2, 0, 0, 12).items()}
        for x in range(-4, 7): px.setdefault((x, -1), "q"); px.setdefault((x, 1), "m")
        px[(9, 0)] = "X" if i % 2 == 0 else "c"
        for k in range(3):
            px[(-7 - k - (i % 2), (k + i) % 3 - 1)] = "n" if k < 2 else "q"
        frames.append(Spr(px))
    return frames


def fx_pinned():
    """The pin driven into the floor at the hero's feet, shadow shackles crawling out of it."""
    frames = []
    for i in range(6):
        px = {}
        h = [12, 6, 5, 5, 5, 4][i]
        for y in range(-h, 1):
            px[(0, y)] = "K" if y > -h + 2 else "n"
        px[(0, -h)] = "u"; px[(-1, -h + 1)] = "U"; px[(1, -h + 1)] = "U"
        if i == 0:
            px[(0, -h - 1)] = "c"
        r = [0, 4, 7, 8, 7, 6][i]
        for t in range(0, 360, 15):
            if i >= 4 and t % 45 == 0: continue
            a = math.radians(t)
            x, y = int(round(r * math.cos(a))), int(round(-1 + r * 0.38 * math.sin(a)))
            px.setdefault((x, y), ("N", "n", "q")[(t // 30 + i) % 3] if i < 5 else "q")
        for k in range(4):                     # shackle tendrils reaching up the hero's legs
            if i in (2, 3, 4):
                a = math.radians(45 + k * 90)
                x0 = int(round(r * 0.7 * math.cos(a)))
                for t in range(3 - (i == 4)):
                    px[(x0 + (1 if x0 < 0 else -1) * (t // 2), -1 - t - (i == 3))] = "n" if t < 2 else "N"
        if i == 1: px.update(sparkle(0, -8, True))
        frames.append(Spr(px))
    return frames


def coil_ring(r, seed, rise=1.0, col_main="q", bright=False):
    """A ring of serpent coils breaking the floor around a point (ground ellipse, ry = 0.42 r)."""
    px = {}
    n = max(5, int(r * 0.55))
    for k in range(n):
        a = 2 * math.pi * (k + 0.5 * (seed % 2)) / n
        x, y = r * math.cos(a), -1 + r * 0.42 * math.sin(a)
        hump = rise * (2.6 if k % 2 == 0 else 1.6)
        for (hx, hy), v in ellipse_px(x, y - hump * 0.7, 2.4, 1.2 + hump * 0.7, col_main).items():
            px[(hx, hy)] = v
    out = shade_body(px, lit="N" if bright else "n", hi="u" if bright else "U", dark="q")
    return out


def fx_coil():
    frames = []
    # emerging (0-1), the noose waits (2-4), it tightens (5), SNAPS (6), sinks (7-8)
    specs = [(24, 0.3), (24, 0.7), (24, 1.0), (23, 1.0), (24, 1.0), (15, 1.1), (6, 1.3), (6, 0.6), (5, 0.25)]
    for i, (r, rise) in enumerate(specs):
        px = {}
        # a faint telegraph ellipse on the floor while the noose is open
        if i <= 5:
            for t in range(0, 360, 6):
                a = math.radians(t)
                px[(int(round(r * math.cos(a))), int(round(-1 + r * 0.42 * math.sin(a))))] = "n" if (t // 6 + i) % 3 else "N"
        px.update(coil_ring(r, i, rise, bright=(i in (4, 6))))
        if i == 6:
            px.update(sparkle(0, -6, True)); px.update(sparkle(-5, -3)); px.update(sparkle(5, -4))
        if i >= 7:
            px = {k: v for k, v in px.items() if hsh(k[0], k[1], i) < (0.7 if i == 7 else 0.4)}
        frames.append(Spr(px))
    return frames


def fx_beam():
    """Gaze beam, drawn from x 0 (the eye) to the right; centre line y 0. 10 frames (v0.8): it lances out (0-1),
    burns and pulses with motes riding outward (2-7), then thins (8) and gutters out (9)."""
    frames = []
    LN = [30, 64, 86, 86, 86, 86, 86, 86, 86, 86]
    TH = [0, 1, 2, 1, 2, 2, 1, 2, 1, 0]
    for i in range(10):
        px = {}
        ln, th = LN[i], TH[i]
        for x in range(0, ln):
            if i == 9 and (x * 7 + 3) % 5 < 2: continue                     # guttering out
            core = "c" if (x + 2 * i) % 9 else "X"
            px[(x, 0)] = core if i < 9 else "N"
            if th >= 1:
                px[(x, -1)] = "u" if (x // 3 + i) % 2 else "N"
                px[(x, 1)] = "N" if (x // 3 + i) % 2 else "n"
            if th >= 2:
                if (x + i) % 2: px[(x, -2)] = "n"
                if (x + i) % 3 == 0: px[(x, 2)] = "n"
            if i == 8 and x % 6 == 0: px[(x, 0)] = "N"
        for k in range(0, ln - 7, 7):                                     # motes riding the beam outward
            px[(k + (i * 3) % 7, -3 if k % 14 else 3)] = "N"
        if ln < 86:                                                       # the lancing tip
            px[(ln, 0)] = "X"; px[(ln + 1, 0)] = "c"; px[(ln, -1)] = "u"; px[(ln, 1)] = "u"
        px[(0, 0)] = "X"; px[(1, -1)] = "c"; px[(1, 1)] = "c"
        if i in (2, 5):                                                    # flare at the iris on the pulses
            px[(0, -2)] = "c"; px[(0, 2)] = "c"; px[(2, 0)] = "X"
        frames.append(Spr(px))
    return frames


def fx_beam_end():
    """v0.8: the gaze beam's tail when it ends (replaces the vanilla DamageBeholderBeamEnd it spawned): the light snaps
    back toward the iris, leaving a dotted afterglow and motes that sink away. 5 frames like the vanilla end."""
    frames = []
    for i in range(5):
        px = {}
        keep = [70, 44, 22, 8, 0][i]                      # the solid stretch still burning near the eye
        for x in range(0, 86):
            if x < keep:
                px[(x, 0)] = "c" if (x + i) % 7 else "X"
                if i < 2: px[(x, -1 if x % 2 else 1)] = "N"
            elif (x * 3 + i * 5) % [3, 4, 5, 7, 9][i] == 0:
                px[(x, 0)] = "N" if i < 3 else "n"        # dotted afterglow breaking up outward
        for k in range(6 + 2 * i):                        # motes drifting off the old beam line
            x = (k * 13 + i * 7) % 84 + 1
            px[(x, (1 + (k + i) % 3) * (1 if k % 2 else -1))] = "N" if i < 3 else "n"
        if i < 4:
            px[(0, 0)] = "X" if i < 2 else "c"
        frames.append(Spr(px))
    return frames


def pane_px(h=14, glint=0, crack=0, k=1.0):
    px = {}
    hh = max(2, int(h * k))
    for (x, y), v in ellipse_px(0, -3 - hh / 2.0, 4.2, hh / 2.0, "S").items():
        px[(x, y)] = v
    glass = ellipse_px(0, -3 - hh / 2.0, 3.0, hh / 2.0 - 1.2, "b")
    for (x, y) in glass:
        px[(x, y)] = "K" if (x + y) % 4 else "q"
    for (x, y) in list(px):
        if (x, y) in glass: continue
        if (x - 1, y) not in px or (x, y - 1) not in px: px[(x, y)] = "u"
        elif (x + 1, y) not in px or (x, y + 1) not in px: px[(x, y)] = "s"
    for (x, y) in glass:
        d = x + (y + 3 + hh / 2.0) * 0.6 - glint
        if abs(d) < 0.6: px[(x, y)] = "c"
        elif abs(d) < 1.4: px[(x, y)] = "B"
    if crack:
        rnd = random.Random(crack)
        for _ in range(crack + 1):
            x, y, d = 0.0, -3 - hh / 2.0, rnd.uniform(0, 360)
            for st in range(5):
                d += rnd.uniform(-35, 35); x += math.cos(math.radians(d)); y += math.sin(math.radians(d))
                kk = (int(round(x)), int(round(y)))
                if kk in glass: px[kk] = "c"
    for x in (-3, -2, -1, 0, 1, 2, 3):           # a stand of shadow
        px[(x, 0)] = "q" if abs(x) < 3 else "n"
        px.setdefault((x, -1), "q" if abs(x) < 2 else "n")
    px[(0, -2)] = "s"
    return px


def fx_pane():
    rise = [Spr(pane_px(14, 0, 0, 0.3)), Spr(pane_px(14, 1, 0, 0.7)).over(Spr(sparkle(0, -12))), Spr(pane_px(14, 2, 0, 1.0))]
    idle = [Spr(pane_px(14, g)) for g in (-5, -2, 2, 5)]
    shatter = []
    for i in range(5):
        base = pane_px(14, 0, 2 + i)
        if i >= 1:
            base = {k: v for k, v in base.items() if hsh(k[0], k[1], i) > 0.18 * i or k[1] >= -1}
            rnd = random.Random(i)
            for _ in range(4 + i):
                base.update(small_shard(rnd.randint(-6 - i, 6 + i), rnd.randint(-16, -2) + i, rnd.choice((30, 150, 210, 330)), 2, ("c", "B")))
        shatter.append(ground(Spr(base)))
    return rise, idle, shatter


def fx_feather():
    frames = []
    for i in range(4):
        px = feather((-4, 0), 0, 8, width=1.6)
        px[(4, 0)] = "X" if i % 2 == 0 else "c"
        px[(-5 - (i % 2), (i % 3) - 1)] = "b"; px[(-6, 0)] = "n"
        frames.append(Spr(px))
    return frames


def pack_fx(name, anims, outdir, anchor_cell=None, scale=8):
    """build_fx with a fixed anchor: anchor_cell = (cellW, cellH, ax, ay) puts sprite (0,0) at (ax, ay)."""
    if anchor_cell is None:
        return build_fx(name, anims, outdir, scale)[2]
    cw, ch, ax, ay = anchor_cell
    img, man = pack(name, anims, cw, ch, (ax, ay), outdir)
    FX_ANCHORS[name] = (ax, ay)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a[0], len(a[1])) for a in anims)))
    return (cw, ch)


@sheet
def build_FX2(outdir):
    out = {}
    out["FxUmbNail"] = pack_fx("FxUmbNail", [("Fly", fx_nail(), [0.05] * 4)], outdir)
    out["FxUmbPin"] = pack_fx("FxUmbPin", [("Fly", fx_pin(), [0.05] * 4)], outdir)
    out["FxUmbPinned"] = pack_fx("FxUmbPinned", [("Play", fx_pinned(), [0.06, 0.12, 0.16, 0.16, 0.16, 0.14])], outdir)
    out["FxUmbCoil"] = pack_fx("FxUmbCoil", [("Play", fx_coil(), [0.1, 0.12, 0.2, 0.2, 0.2, 0.06, 0.1, 0.12, 0.12])], outdir, scale=6)
    out["FxUmbBeam"] = pack_fx("FxUmbBeam", [("Play", fx_beam(), [0.03, 0.04, 0.05, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06]),
                                             ("End", fx_beam_end(), [0.05] * 5)], outdir,
                               anchor_cell=(88, 9, 0, 4), scale=5)
    rise, idle, shatter = fx_pane()
    out["FxUmbPane"] = pack_fx("FxUmbPane", [("Rise", rise, [0.06, 0.08, 0.1]), ("Idle", idle, [0.16, 0.12, 0.12, 0.16]),
                                             ("Shatter", shatter, [0.05, 0.06, 0.07, 0.08, 0.1])], outdir)
    out["FxUmbFeather"] = pack_fx("FxUmbFeather", [("Fly", fx_feather(), [0.05] * 4)], outdir)
    CELLS.update(out)
    return None


# ================================================================================================
# FX: procedural effects in the pack palette. (0,0) = the effect's ground / centre point.
# ================================================================================================
def build_fx(name, anims, outdir, scale=8):
    allf = [f for a in anims for f in a[1]]
    x0 = min(f.bbox()[0] for f in allf); x1 = max(f.bbox()[2] for f in allf)
    y0 = min(f.bbox()[1] for f in allf); y1 = max(f.bbox()[3] for f in allf)
    hw = max(-x0, x1) + 2
    h = -y0 + 2
    cw, ch = 2 * hw, h + max(0, y1) + 2
    for an, frames, durs in anims:
        assert len(durs) == len(frames), (name, an)
    img, man = pack(name, anims, cw, ch, (hw, h), outdir)
    FX_ANCHORS[name] = (hw, h)
    preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=scale)
    print("built %-16s cell %dx%d  %s" % (name, cw, ch, ", ".join("%s:%d" % (a[0], len(a[1])) for a in anims)))
    return img, man, (cw, ch)


def fx_mirror_shard():
    """Spinning sliver of black mirror (projectile, faces right)."""
    frames = []
    for i in range(4):
        ang = i * 45
        pts = [rot_pt(p, ang) for p in [(4, 0), (0, -2), (-3, 0), (0, 2)]]
        px = poly_px(pts, "q")
        for (x, y) in list(px):
            up = (x, y - 1) not in px; left = (x - 1, y) not in px
            if up and left: px[(x, y)] = "c"
            elif up or left: px[(x, y)] = "u"
            elif (x + 1, y) not in px or (x, y + 1) not in px: px[(x, y)] = "n"
            elif (x - y + i) % 3 == 0: px[(x, y)] = "B"
        tip = rot_pt((4, 0), ang)
        px[(int(round(tip[0])), int(round(tip[1])))] = "c"
        px[(-5, 0)] = "b"; px[(-6 - (i % 2), 0)] = "n"     # motion streak (it flies right)
        frames.append(Spr(px))
    return frames


def darkness_frame(rx, ry, seed, dense=1.0, motes=0):
    px = {}
    for (x, y), v in ellipse_px(0, -3, rx, ry, "q", rim="m", rim_t=0.55, jitter=0.35, seed=seed).items():
        if hsh(x, y, seed) > dense: continue
        if v == "q" and (x * 3 + y * 7 + seed * 5) % 11 == 0: v = "K"
        if v == "q" and (x + 2 * y + seed) % 9 == 0: v = "m"
        px[(x, y)] = v
    # lit rim on the top edge, violet wisps curling off it
    for (x, y) in list(px):
        if (x, y - 1) not in px:
            px[(x, y)] = "N" if hsh(x, y, seed + 3) < 0.35 else "n"
        elif (x, y + 1) not in px or (x - 1, y) not in px or (x + 1, y) not in px:
            px[(x, y)] = "n"
    rnd = random.Random(seed)
    for k in range(int(rx // 3)):
        wx = rnd.randint(int(-rx * 0.7), int(rx * 0.7))
        top = -3 - int(ry) - rnd.randint(0, 2)
        for t in range(rnd.randint(1, 3)):
            px[(wx + (t + seed) % 2, top - t)] = "n" if t else "N"
    for k in range(motes):
        px[(rnd.randint(int(-rx * 0.6), int(rx * 0.6)), -4 - int(ry) - rnd.randint(1, 4))] = "U"
    return Spr(px)


def fx_darkness(k=1.4):
    """Drawn at its in-game size (the cloud covers the r 22 DarknessFx circle: 43 x 15 + wisps) instead of a
    31 x 16 sheet blown up x1.4 by the template."""
    spread = [darkness_frame(5 * k, 2 * k, 1), darkness_frame(10 * k, 3.5 * k, 2), darkness_frame(15 * k, 5 * k, 3, motes=1)]
    idle = [darkness_frame(15 * k, 5 * k, 4, motes=3), darkness_frame(15.5 * k, 5.2 * k, 5, motes=3)]
    fade = [darkness_frame(15 * k, 5 * k, 6, 0.65, 1), darkness_frame(14 * k, 4.5 * k, 7, 0.4), darkness_frame(13 * k, 4 * k, 8, 0.18)]
    return spread, idle, fade


def fx_shadow_puff():
    frames = []
    for i in range(5):
        k = (i + 1) / 5.0
        rnd = random.Random(30 + i)
        px = {}
        for _ in range(int(30 + 40 * k)):
            a = rnd.uniform(0, 2 * math.pi)
            r = rnd.uniform(0, 2 + 6 * k)
            x = int(round(r * math.cos(a))); y = int(round(r * 0.8 * math.sin(a) - 2 * k))
            if i == 4 and rnd.random() < 0.5: continue
            d = r / (2 + 6 * k)
            px[(x, y)] = ("q" if d < 0.4 else "n" if d < 0.75 else "N") if i < 3 else ("m" if d < 0.5 else "n")
        if i < 2:
            px[(0, -1)] = "N"; px[(1, -2)] = "U"
        if i >= 2:
            for t in range(3):
                px[(rnd.randint(-5, 5), -7 - i - t)] = "s" if t else "n"
        frames.append(Spr(px))
    return frames


def fx_reflect_bolt():
    frames = []
    for i in range(4):
        px = {}
        for x in range(-7, 1):
            px[(x, 0)] = "c" if x > -2 else "B" if x > -5 else "b"
        for (x, y, c) in ((1, 0, "X"), (2, 0, "c"), (0, -1, "c"), (0, 1, "c"), (-1, -1, "B"), (-1, 1, "B"),
                          (1, -1, "u"), (1, 1, "u")):
            px[(x, y)] = c
        # mirror glint: a cross that flickers between frames
        if i % 2 == 0:
            px[(0, -2)] = "u"; px[(0, 2)] = "u"; px[(3, 0)] = "u"
        else:
            px[(-1, -2)] = "B"; px[(1, 2)] = "B"
        px[(-8 - (i % 2), (i % 3) - 1)] = "b"
        px[(-4, -1 + (i % 2) * 2)] = "B"
        frames.append(Spr(px))
    return frames


def fx_swap_flash():
    frames = []
    for i in range(5):
        px = {}
        if i == 0:
            px.update(sparkle(0, -8, True))
        if 1 <= i <= 3:
            beam_h = [0, 16, 18, 14][i]
            for y in range(-beam_h, 1):
                px[(0, y)] = "c" if i < 3 else "u"
                if i < 3: px[(-1, y)] = "u" if y > -beam_h + 2 else "B"; px[(1, y)] = "B" if i == 1 else "U"
            r = [0, 5, 9, 12][i]
            for t in range(0, 360, 8):
                a = math.radians(t)
                px.setdefault((int(round(r * math.cos(a))), int(round(-1 + r * 0.38 * math.sin(a)))),
                              ("c", "u", "B")[(t // 24) % 3] if i < 3 else ("U", "N")[(t // 24) % 2])
            if i == 1: px.update(sparkle(0, -8, True))
        if i == 4:
            rnd = random.Random(4)
            for _ in range(10):
                a = rnd.uniform(0, 6.28); r = rnd.uniform(8, 14)
                px[(int(r * math.cos(a)), int(r * 0.6 * math.sin(a)) - 4)] = rnd.choice("UNu")
        frames.append(Spr(px))
    return frames


def fx_decoy_burst():
    frames = []
    for i in range(5):
        px = {}
        if i == 0:
            px.update(ellipse_px(0, -6, 3, 4, "n", rim="N"))
            px.update(sparkle(0, -6, True))
        else:
            r = 2 + i * 2.6
            for k in range(7):
                a = math.radians(k * 360 / 7 + 15 + i * 6)
                x = int(round(r * math.cos(a))); y = int(round(-6 + r * 0.8 * math.sin(a) + (i * i) * 0.3))
                if i < 4 or k % 2 == 0:
                    px.update(small_shard(x, y, math.degrees(a) + i * 40, 3 if i < 3 else 2,
                                          ("c", "N", "n") if i < 3 else ("U", "n")))
            if i < 3:
                for (x, y), v in fx_shadow_puff()[i - 1].shift(0, -4).px.items():
                    px.setdefault((x, y), v)
        frames.append(ground(Spr(px)).over(Spr({})))
    return frames


def fx_echo_mark():
    """Floor telegraph: a flat violet ring with three bright arms swirling around it (seamless 4-loop)."""
    frames = []
    for i in range(4):
        px = {}
        for t in range(0, 360, 8):
            a = math.radians(t)
            px[(int(round(7 * math.cos(a))), int(round(-2 + 2.6 * math.sin(a))))] = "n"
        for arm in range(3):
            for s in range(7):
                a = math.radians(arm * 120 + i * 30 + s * 14)
                r = 7 - s * 0.75
                col = "c" if s == 0 else "u" if s < 2 else "N" if s < 5 else "n"
                px[(int(round(r * math.cos(a))), int(round(-2 + r * 0.37 * math.sin(a))))] = col
        px[(0, -2)] = "N" if i % 2 else "U"
        frames.append(Spr(px))
    return frames


@sheet
def build_FX(outdir):
    out = {}
    out["FxMirrorShard"] = build_fx("FxMirrorShard", [("Fly", fx_mirror_shard(), [0.06] * 4)], outdir)[2]
    sp, idl, fd = fx_darkness()
    reps = 11   # 0.24 s spread + 11 x 2 x 0.2 s idle + 0.36 s fade = 5.0 s
    life = sp + idl * reps + fd
    durs = [0.08] * 3 + [0.2] * (2 * reps) + [0.12] * 3
    out["FxDarkness"] = build_fx("FxDarkness", [("Life", life, durs)], outdir, scale=6)[2]
    out["FxShadowPuff"] = build_fx("FxShadowPuff", [("Play", fx_shadow_puff(), [0.06, 0.07, 0.08, 0.09, 0.1])], outdir)[2]
    out["FxReflectBolt"] = build_fx("FxReflectBolt", [("Fly", fx_reflect_bolt(), [0.06] * 4)], outdir)[2]
    out["FxSwapFlash"] = build_fx("FxSwapFlash", [("Play", fx_swap_flash(), [0.04, 0.05, 0.06, 0.08, 0.1])], outdir)[2]
    out["FxDecoyBurst"] = build_fx("FxDecoyBurst", [("Play", fx_decoy_burst(), [0.04, 0.06, 0.07, 0.08, 0.1])], outdir)[2]
    out["FxEchoMark"] = build_fx("FxEchoMark", [("Play", fx_echo_mark(), [0.1] * 4)], outdir)[2]
    CELLS.update(out)
    return None


# ================================================================================================
# Item icons (16x16, feet (8,15)) and the god portrait (29x24, feet (14,23), fully opaque)
# ================================================================================================
def outline(px, col="K"):
    out = dict(px)
    for (x, y) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px: out[(x + dx, y + dy)] = col
    return out


def icon_mirror_step(glint):
    """Standing oval mirror with a dark footprint pressed into the glass."""
    px = {}
    cy = -8
    for (x, y), v in ellipse_px(0, cy, 5.6, 6.4, "S").items():
        px[(x, y)] = v
    glass = ellipse_px(0, cy, 4.1, 4.9, "b")
    for (x, y) in glass:
        px[(x, y)] = "b" if (x + y) % 5 else "B"
    for (x, y) in list(px):
        if (x, y) in glass: continue
        if (x - 1, y) not in px or (x, y - 1) not in px: px[(x, y)] = "U"
        elif (x + 1, y) not in px or (x, y + 1) not in px: px[(x, y)] = "s"
    foot = [(-2, -11), (-1, -12), (1, -12), (2, -11),
            (-1, -10), (0, -10), (1, -10), (-1, -9), (0, -9), (1, -9),
            (0, -8), (1, -8), (0, -7), (1, -7), (-1, -6), (0, -6), (1, -6), (-1, -5), (0, -5)]
    for (x, y) in foot:
        px[(x, y + 1)] = "K"
    for (x, y) in glass:            # glint band sweeping across the glass
        if px[(x, y)] == "K": continue
        d = x + (y - cy) * 0.8 - glint
        if abs(d) < 0.6: px[(x, y)] = "c"
        elif abs(d) < 1.3: px[(x, y)] = "B"
    for x in (-2, -1, 0, 1, 2):      # little stand
        px[(x, 0)] = "s" if x else "S"
    px[(0, -1)] = "S"
    px = outline(px)
    return Spr({k: v for k, v in px.items() if -8 <= k[0] <= 7 and -15 <= k[1] <= 0})


CROWN_ICON = """
................
................
.......K........
......KuK.......
..K..KUnqK......
.KuK.KUnqK...K..
.KUqK.KnqK..KuK.
.KnqKKUnBqKKUqK.
.KnnqqnnqqqqnqK.
KuUUuUUUuUUUuUUK
KnqqqBbqqqKqqqqK
KnqqqbqqqKqqnqqK
KqqqqqqqqqKqqqqK
KsSSSSSSSSSSSSsK
.KKKKKKKKKKKKKK.
................
"""


def icon_hollow_crown(glint):
    s = Spr.parse(CROWN_ICON, feet_x=8)
    px = dict(s.px)
    spots = [(-6, -6), (-1, -6), (3, -6), (5, -6)]
    g = spots[glint % len(spots)]
    if glint:
        px[g] = "X"; px[(g[0] - 1, g[1])] = "c"; px[(g[0] + 1, g[1])] = "c"
        px[(-3, -5)] = "c"   # gem catches the light
    return Spr(px)


def deity_portrait(glint):
    W, H = 29, 24
    px = {}
    for r in range(H):
        for c in range(W):
            x, y = c - 14, r - 23
            v = "q" if (c + r) % 7 else "m"
            if abs(x) > 11 and (x + y) % 2 == 0: v = "m"
            px[(x, y)] = v
    def hw(r):        # gothic arch half-width (outer)
        return 10.0 if r >= 9 else max(1.0, 10.0 - (9 - r) ** 2 / 8.0)
    frame, glass = set(), set()
    for r in range(1, H):
        for c in range(W):
            x = c - 14
            o = hw(r)
            if abs(x) <= o:
                if abs(x) <= o - 2.2 and r >= 3: glass.add((x, r - 23))
                else: frame.add((x, r - 23))
    for (x, y) in frame:
        left = (x - 1, y) not in frame and (x - 1, y) not in glass
        top = (x, y - 1) not in frame and (x, y - 1) not in glass
        px[(x, y)] = "U" if (left or top) and x <= 0 else "S" if x < 0 else "s"
        if (x, y + 1) in glass or (x - 1, y) in glass or (x + 1, y) in glass: px[(x, y)] = "s" if x > 0 else "S"
    for (x, y) in ((0, -22), (-1, -21), (1, -21)):
        px[(x, y)] = "u"                              # finial
    px[(0, -23)] = "U"
    for (x, y) in glass:
        px[(x, y)] = "K" if (x + y) % 4 else "q"
    # crowned silhouette inside the black mirror
    sil = {}
    sil.update(ellipse_px(0, -10, 3.2, 3.8, "m"))
    sil.update(poly_px([(-7, 1), (-4, -5), (4, -5), (7, 1)], "m"))
    for (x, y) in list(sil):
        if (x, y) not in glass: del sil[(x, y)]
    for (x, y) in sil:
        rim = any((x + dx, y + dy) not in sil for dx, dy in ((1, 0), (-1, 0), (0, -1)))
        px[(x, y)] = "n" if rim else "m"
    for (x, y, c) in ((-3, -14, "S"), (-3, -15, "U"), (-1, -14, "S"), (-1, -15, "S"), (-1, -16, "U"), (1, -14, "S"),
                      (1, -15, "U"), (3, -14, "S"), (3, -15, "s"), (-2, -14, "s"), (0, -14, "S"), (2, -14, "s"),
                      (0, -15, "B")):
        px[(x, y)] = c
    px[(1, -10)] = "c"; px[(2, -10)] = "X"; px[(1, -11)] = "u"           # the single white eye
    # glint band sweeping across the glass
    for (x, y) in glass:
        d = x + (y + 12) * 0.7 - glint
        if abs(d) < 0.6: px[(x, y)] = "B" if px[(x, y)] in "Kq" else "U"
        elif abs(d) < 1.6 and px[(x, y)] in "Kq": px[(x, y)] = "b"
    return Spr(px)


@sheet
def build_Items(outdir):
    for name, fn, durs in (("IconMirrorStep", icon_mirror_step, [1.2, 0.15]),
                           ("IconHollowCrown", icon_hollow_crown, [1.2, 0.15])):
        frames = [fn(-9 if name == "IconMirrorStep" else 0), fn(-2 if name == "IconMirrorStep" else 2)]
        img, man = pack(name, [("Idle", frames, durs)], 16, 16, (8, 15), outdir)
        preview(img, man, os.path.join(outdir, name + "_preview.png"), scale=10)
        CELLS[name] = (16, 16)
        print("built %-16s cell 16x16  Idle:2" % name)
    frames = [deity_portrait(g) for g in (-14, -4, 4, 14)]
    img, man = pack("DeityUmbrael", [("Idle", frames, [1.4, 0.1, 0.1, 0.1])], 29, 24, (14, 23), outdir)
    preview(img, man, os.path.join(outdir, "DeityUmbrael_preview.png"), scale=10)
    CELLS["DeityUmbrael"] = (29, 24)
    print("built DeityUmbrael     cell 29x24  Idle:4")
    return None


# ================================================================================================
# TIMING.md: cell sizes + the frame indices gameplay code must sync to
# ================================================================================================
EVENTS = {   # sheet -> anim -> [(moment, 0-based frame index)]
    "UmbShadeImp": {"Rake": [("hit 1 (front claw)", 2), ("hit 2 (back claw)", 4)],
                    "Step": [("vanish: near-invisible frame, teleport here", 4), ("reappear-strike", 7)]},
    "UmbGlimmer": {"Shard": [("release (spawn FxMirrorShard)", 2)],
                   "Split": [("decoys appear (spawn the 2 decoys)", 3)]},
    "UmbGlimmerDecoy": {"Shard": [("release (spawn FxUmbRingShard)", 2)], "Spawn": [("formed", 2)]},
    "UmbGloomLurker": {"Ambush": [("strike (bite lands)", 3)],
                       "Gloom": [("exhale (spawn FxDarkness)", 3)]},
    "UmbTwinned": {"Cut": [("front-hit", 2), ("back-hit", 4)],
                   "Swap": [("flash (swap positions, spawn FxSwapFlash)", 4)]},
    "UmbMirrorWitch": {"Reflect": [("release (spawn FxReflectBolt)", 3)],
                       "Shatter": [("raise (mirror at the top, start telegraph)", 1), ("burst (ring of 8 FxMirrorShard)", 5)]},
    "UmbHollowKing": {"Cleave": [("hit", 4)], "Court": [("summon (spawn the 3 echoes)", 5)],
                      "Echo": [("hit (echo damage)", 1)]},
    "UmbNailshade": {"Fling": [("release (3 FxUmbNail from the hand, (12, -12))", 2)],
                     "Pin": [("pluck the pin", 1), ("release (FxUmbPin from the hand, (12, -12))", 3),
                             ("gone (0.3 s: the pin is still flying)", 5), ("pounce: re-form beside a pinned hero", 6), ("rake hit (slash to x 17)", 7)]},
    "UmbGloamcoil": {"Strike": [("bite lands (jaws at (19, -10))", 3)],
                     "Slither": [("dash starts, ink pool 1", 2), ("ink pool 2", 4), ("dash ends, ink pool 3", 6)]},
    "UmbEclipseWyrm": {"Fangs": [("void head bites (jaws at (25, -10))", 3), ("glass head bites (jaws at (24, -16))", 5)],
                       "Constrict": [("tail slam: FxUmbCoil rises at the hero", 3), ("heads snap (ring snaps 0.88 s after the slam)", 7)]},
    "UmbGlassSeraph": {"Feathers": [("release (3 FxUmbFeather from the hand, (13, -17))", 3)],
                       "Prism": [("cast: the mirror panes rise", 4)]},
    "UmbUnblinking": {"Gaze": [("beam fires (FxUmbBeam from the iris, (11, -21))", 3)],
                      "Blackout": [("eye shut: darkness pours over the god's monsters", 3), ("gone: blink here", 4),
                                   ("sweep: three beams from (11, -22)", 7)]},
}
ORDER = ["UmbShadeImp", "UmbGlimmer", "UmbGlimmerDecoy", "UmbGloomLurker", "UmbTwinned", "UmbMirrorWitch", "UmbHollowKing",
         "UmbNailshade", "UmbGloamcoil", "UmbEclipseWyrm", "UmbGlassSeraph", "UmbUnblinking",
         "FxMirrorShard", "FxDarkness", "FxShadowPuff", "FxReflectBolt", "FxSwapFlash", "FxDecoyBurst", "FxEchoMark",
         "FxUmbNail", "FxUmbPin", "FxUmbPinned", "FxUmbCoil", "FxUmbBeam", "FxUmbPane", "FxUmbFeather",
         "IconMirrorStep", "IconHollowCrown", "DeityUmbrael"]


def write_timing(outdir):
    import json
    L = ["# Umbrael sprite timing", "",
         "Generated by tools/sprites/umbrael_rigs.py. Frame indices are 0-based within each anim.",
         "Feet/anchor point inside every cell is (cellW/2, cellH-2) for monsters; FX, icon and portrait",
         "anchors are listed per sheet. `t` = seconds from the start of the anim to the start of that frame.", "",
         SK.SCALE_NOTE, "",
         "## Cell sizes", "", "| Sheet | Cell (w x h) | Anchor (x, y) | Anims (frames) |", "|---|---|---|---|"]
    mans = {}
    for nm in ORDER:
        p = os.path.join(outdir, nm + ".json")
        if not os.path.exists(p): continue
        m = json.load(open(p)); mans[nm] = m
        if nm.startswith("Umb"): anchor = (m["cellW"] // 2, m["cellH"] - 2)
        elif nm.startswith("Icon"): anchor = (8, 15)
        elif nm.startswith("Deity"): anchor = (14, 23)
        else: anchor = FX_ANCHORS.get(nm, ("?", "?"))
        an = ", ".join("%s %d" % (a["name"], len(a["frames"])) for a in m["anims"])
        if nm.startswith("Umb"):
            from PIL import Image
            ib = SK.idle_bounds(Image.open(os.path.join(outdir, nm + ".png")).convert("RGBA"), m)
            an += "; idle bounds %d x %d, design scale %.2f" % (ib[0], ib[1], SCALE.get(nm, 1.0))
        L.append("| %s | %d x %d | (%s, %s) | %s |" % (nm, m["cellW"], m["cellH"], anchor[0], anchor[1], an))
    L += ["", "## Move anims and sync frames", ""]
    for nm, moves in EVENTS.items():
        m = mans.get(nm)
        if not m: continue
        A = {a["name"]: a for a in m["anims"]}
        L.append("### %s" % nm)
        L.append("")
        L.append("| Anim | Frames | Total (s) | Moment | Frame | t (s) |")
        L.append("|---|---|---|---|---|---|")
        for an, evs in moves.items():
            d = A[an]["durations"]
            for k, (label, fi) in enumerate(evs):
                L.append("| %s | %s | %s | %s | %d | %.2f |" % (an if k == 0 else "", len(d) if k == 0 else "",
                         ("%.2f" % sum(d)) if k == 0 else "", label, fi, sum(d[:fi])))
        L.append("")
    L += ["### Notes", "",
          "- Step: frames 0-3 fade into smoke, frame 4 is the near-invisible frame (teleport on it), frames 5-6 re-form "
          "from smoke in the lunging pose behind the hero, frame 7 is the claw strike.",
          "- Shatter: raise (frame 1) to burst (frame 5) is 0.80 s, matching the spec's 0.8 s ring delay.",
          "- Echo (Hollow King) is drawn only in q/m/n/N with a checkered interior so it reads as a translucent "
          "afterimage; play it at the spot of the original cleave ~0.6 s later.",
          "- FxDarkness `Life`: spread frames 0-2 (0.08 s each), idle pair repeated 11x (frames 3-24, 0.2 s each), "
          "fade frames 25-27 (0.12 s each) = 5.00 s total.",
          "- FxEchoMark is a seamless 4-frame loop under the anim name `Play`; set it to loop while the telegraph lasts.",
          "- Projectiles (FxMirrorShard, FxReflectBolt) face right and loop `Fly`; the others play `Play` once.",
          "- v0.7.2 sheets (Nailshade, Gloamcoil, Eclipse Wyrm, Glass Seraph, Unblinking and the FxUmb* effects) are drawn "
          "at their final size (design scale 1.00, no ArtScale entry): the points above are their real pixels.",
          "- FxUmbBeam is anchored at its LEFT end (cell (0, 4)): the beam runs 86 px to the right of the spawn point. "
          "Play is 10 frames (v0.8: lance out 0-1, burn and pulse 2-7, thin 8, gutter 9); End (5 frames) is spawned when "
          "the beam despawns, in place of the vanilla DamageBeholderBeamEnd.",
          "- FxUmbCoil: open noose r 24 (frames 0-4, 0.82 s), tightens (5), SNAPS at frame 6 (t 0.88 s, r 6), sinks (7-8).",
          "- FxUmbPane: Rise 3 -> Idle 4 (loop while it stands) -> Shatter 5.", ""]
    L += ["", "## v0.8 value and identity pass", "",
          "- Every Umbrael monster but the already-bright Glimmer, Glass Seraph and Unblinking has its shadow ramp lifted "
          "(Idle luminance means were 62-85, now 83-122).",
          "- UmbGloomLurker: cold slate-blue with teal eyes. UmbTwinned: the back twin is the pale silver reflection, the front "
          "twin dark violet. UmbNailshade: plum-rose with rose eyes. UmbGloamcoil: deep indigo, amber eyes, gold belly scutes.",
          "- UmbGlimmerDecoy: the Glimmer's own poses (same 0.75 scale) with a negative core (pale lilac glass, dark facets and "
          "eye) and missing see-through facets; Spawn 3 frames (tiny-rat spawn timing). DecoyKit uses final px "
          "(shard (9, -8.25), node 8.25) since the sheet has no ArtScale entry.",
          "- Geometry is unchanged on every redrawn sheet: TIMING points and kit offsets stand."]
    L += ["", "## v0.10 (final art review)", "",
          "- UmbMirrorWitch wears the Gloom Lurker's slate blue with its teal eyes, and four arched slate-blue spider legs "
          "reach out from her hem.",
          "- UmbGloamcoil has five arched slate-blue Lurker legs along its tail coil (a many-legged serpent) and teal eyes."]
    L += ["", "## Lineage motifs (v0.10: every evolution has one parent)", ""] + ["- " + t for t in ["UmbTwinned (Shade Imp): the imp's head and white eye + its smoky tail behind the fused waist", 'UmbNailshade (Shade Imp): smoky imp tail; the two back shards are its own rose glass (v0.10)', "UmbMirrorWitch (Gloom Lurker): the Lurker's teal eyes in her veil and slate-blue spider legs under the hem", 'UmbGloamcoil (Gloom Lurker): teal eyes (were amber)', "UmbEclipseWyrm (Gloamcoil): slate-blue glass head (the Gloamcoil's Lurker legs) and dark head + Gloamcoil indigo, gold scutes, teal eye (v0.10)", "UmbHollowKing (Twinned): the twin blade + the Twinned's pale silver spikes on the pauldrons and silver highlights (v0.10)", 'UmbGlassSeraph (Nailshade): nail-like glass feathers + Nailshade rose in the violet', 'UmbUnblinking (Mirror Witch): the mirror frame + her slate blue with teal-tipped tendrils (v0.10)']]
    import godsb_fx
    L += godsb_fx.timing_section("umbrael")
    if "umbrael_v10" in sys.modules:
        L += sys.modules["umbrael_v10"].timing_section()
    open(os.path.join(outdir, "TIMING.md"), "w").write("\n".join(L))
    print("wrote TIMING.md")


FX_ANCHORS = {}


# ------------------------------------------------------------------------------------------------
# ================================================================================================
# design scale (v0.7 size pass): generators render in pixels at the current scale; canvases scale puts
# ================================================================================================
def _install_scale():
    mod = sys.modules[__name__]
    K = {
        "ellipse_px": {"cx": "x", "cy": "y", "rx": "e", "ry": "e"},
        "poly_px": {"pts": "P"},
        "arc_px": {"cx": "x", "cy": "x", "r": "x"},
        "mirror_shard": {"cx": "x", "cy": "x", "glint": "x", "scale": "x"},
        "crystal_wing": {"root": "Pt", "length": "x"},
        "small_shard": {"x": "x", "y": "x"},
        "sparkle": {"x": "xi", "y": "xi"},
        "gloom_cloud": {"cx": "x", "cy": "x", "r": "e"},
        "flash_ring": {"cx": "x", "cy": "x", "r": "x"},
        "shard_ring": {"cx": "x", "cy": "x", "r": "x"},
        "bolt_px": {"x": "xi", "y": "xi"},
        "robe_px": {"top": "Pi", "lean": "x", "sway": "xi", "height": "xi", "w_top": "x", "w_hem": "x"},
    }
    for name, kinds in K.items():
        kinds = {n: ("x" if k == "y" else k) for n, k in kinds.items()}
        setattr(mod, name, SK.kwrap(getattr(mod, name), kinds))
    mod.torso_px = SK.kwrap(torso_px, {"hip": "Pt", "length": "x", "w0": "x", "w1": "x"},
                            ret=lambda r, s: (r[0], (r[1][0] / s, r[1][1] / s)))
    mod.Canvas = SK.SCanvas


_install_scale()
# linear factor each monster sheet is rendered at (1.0 = authored size); see src/CrawlFurther/SheetScales.cs
SCALE = {"UmbShadeImp": 0.78, "UmbGlimmer": 0.75, "UmbGlimmerDecoy": 0.75, "UmbGloomLurker": 0.61, "UmbTwinned": 0.76, "UmbMirrorWitch": 0.85}


def _load_v10():
    """v0.10: the ten new monsters of the unique-evolution tree live in umbrael_v10.py; importing it registers its
    builders in SHEETS (and its TIMING rows in EVENTS / ORDER). It imports this module by name."""
    sys.modules.setdefault("umbrael_rigs", sys.modules[__name__])
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import umbrael_v10
    EVENTS.update(umbrael_v10.EVENTS)
    for nm in umbrael_v10.SHEET_ORDER:
        if nm not in ORDER: ORDER.insert(ORDER.index("FxMirrorShard"), nm)
    return umbrael_v10


if __name__ == "__main__":
    V10 = _load_v10()
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    only = sys.argv[2:]
    os.makedirs(out, exist_ok=True)
    for nm, fn in SHEETS.items():
        if only and nm not in only:
            continue
        with SK.scaled(SCALE.get(nm, 1.0)):
            res = fn(out)
        if res: CELLS[nm] = res[2]
    import godsb_fx   # v0.8 effect sheets (arcs, echo smear, ring shard, pane bolt, gloam pool, shroud)
    gfx = {n for n, v in godsb_fx.SHEETS.items() if v[0] == "umbrael"}
    if not only or set(only) & gfx:
        godsb_fx.build("umbrael", out, set(only) & gfx if only else None)
    if not only:
        write_timing(out)
