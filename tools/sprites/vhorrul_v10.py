"""VHORRUL v0.10 unique-evolution tree: the ten new monsters and their effect sheets.

    python3 vhorrul_v10.py [outdir] [--only Name,Name]      (default art/out)

Tree (every evolved monster has exactly one parent; * = drawn here, at final size, no ArtScale entry):
  Wickling     -> Waxen Knight, Chandler
  Tallow Grub  -> Wickworm*, Tallow Sow*
  Ash Moth     -> Moth Matron, Candelabra
  Waxen Knight -> Tallow Colossus, Pyre Warden*
  Chandler     -> Tallow Renderer*, Wick Hag*
  Moth Matron  -> Ashen Seraph, Lantern Wraith
  Candelabra   -> Grand Chandelier, Votive Reliquary*
  Wickworm*    -> Candle Wyrm*, Fuse Scorpion*
  Tallow Sow*  -> Grub Mother*, Pyre Tick*

Same hand as vhorrul_t3.py (its shaded primitives, Fr layers, 1 px dark outline, glow pixels last); the new materials
get their own ramps below so no two monsters share a palette:
  Wickworm line   old beeswax ochre   (vhw0..3)    Candle Wyrm brighter gold on it, Fuse Scorpion ash-grey plates
  Tallow Sow line rendered-fat pink   (vhs0..3)    Grub Mother the same + amber eggs, Pyre Tick scorched red-black
Run after vhorrul_t3.py (it calls build_all at its end), before godsa_fx.py.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, PALETTE, pack, preview  # noqa: E402
import vhorrul_t3 as V  # noqa: E402

ell, tube, poly, P, pick, Fr = V.ell, V.tube, V.poly, V.P, V.pick, V.Fr


def line(c, x0, y0, x1, y1, ch, over=True):
    """V.line, but a multi-char palette key (vhw0...) is one colour, not a cycle of its letters."""
    if isinstance(ch, str) and len(ch) > 1 and ch.startswith("vh"): ch = [ch]
    return V.line(c, x0, y0, x1, y1, ch, over)
flame, candle, moth_wing = V.flame, V.candle, V.moth_wing
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art/out")

PALETTE.update({
    # Wickworm line: old yellowed beeswax
    "vhw0": (0x3e, 0x2c, 0x1a), "vhw1": (0x72, 0x54, 0x2a), "vhw2": (0xa6, 0x80, 0x3c), "vhw3": (0xcc, 0xa8, 0x5c),
    "vhw4": (0xe8, 0xcc, 0x84),
    # Fuse Scorpion: charcoal-to-ash plates
    "vhf0": (0x30, 0x28, 0x26), "vhf1": (0x56, 0x48, 0x3e), "vhf2": (0x80, 0x6a, 0x54), "vhf3": (0xa8, 0x90, 0x70),
    "vhf4": (0xd2, 0xbc, 0x92),
    # Tallow Sow line: rendered fat
    "vhs0": (0x4c, 0x26, 0x2a), "vhs1": (0x86, 0x48, 0x48), "vhs2": (0xbe, 0x7a, 0x6e), "vhs3": (0xe6, 0xb0, 0x98),
    # amber eggs glowing inside the fat
    "vhe0": (0x9a, 0x52, 0x1c), "vhe1": (0xd8, 0x86, 0x2a), "vhe2": (0xf6, 0xbe, 0x52),
    # Pyre Tick: scorched shell
    "vht0": (0x34, 0x18, 0x16), "vht1": (0x6a, 0x2a, 0x1e), "vht2": (0x9c, 0x40, 0x26), "vht3": (0xc6, 0x5e, 0x32),
    "vht4": (0xe6, 0x8c, 0x52),
    # Votive Reliquary: red votive glass
    "vhv0": (0x4a, 0x10, 0x16), "vhv1": (0x8a, 0x1c, 0x22), "vhv2": (0xc8, 0x34, 0x2c),
    # Wick Hag: grey tallow skin, soot rags
    "vhg0": (0x5c, 0x56, 0x52), "vhg1": (0x8a, 0x84, 0x7a), "vhg2": (0xb4, 0xae, 0xa0),
})
WORM = ["vhw0", "vhw1", "vhw2", "vhw3", "vhw4"]
WORM_D = ["vhw0", "vhw0", "vhw1", "vhw2"]
SOOT = ["vhf0", "vhf1", "vhf2", "vhf3", "vhf4"]
FAT = ["vhs0", "vhs1", "vhs2", "vhs3"]
FAT_D = ["vhs0", "vhs0", "vhs1", "vhs2"]
EGG = ["vhe0", "vhe1", "vhe2"]
TICK = ["vht0", "vht1", "vht2", "vht3", "vht4"]
VOTIVE = ["vhv0", "vhv1", "vhv2"]
HAG = ["vhg0", "vhg1", "vhg2"]
IRON = "Kmss"
IRON_L = "msS"
BRASS = "kAew"
WAX = "hwWX"
RUST = "kaaP"
APRON = "ktT"
GLOWC = set("oOYyRrBc")
BUILT = {}


def sheet(name, anims, outdir, scale=5):
    V.sheet(name, anims, outdir, scale=scale)
    BUILT[name] = V.BUILT.get(name)


def tail(idle0, death, death_d, knock, dead_d=0.3):
    return [("Death", death, death_d), ("Dead", [death[-1]], [dead_d]), ("Statue", [idle0.stone()], [0.2]),
            ("Knockback", [knock], [0.2]), ("Portrait", [idle0], [0.2])]


def fade_out(spr, k, seed=3):
    """Drop a growing share of pixels (glows first) - for melting / dissolving death frames."""
    rnd = random.Random(seed)
    return Spr({p: v for p, v in spr.px.items() if not (v in GLOWC and k > 0.3) and rnd.random() > k * 0.55})


def melt(spr, k, pool=FAT, seed=1, w=None):
    """Sag a sprite toward the floor by k (0..1) and spread a pool under it."""
    px = {}
    b = spr.bbox()
    for (x, y), v in spr.px.items():
        if v in GLOWC and k > 0.4: continue
        ny = int(round(y * (1 - k)))
        nx = int(round(x * (1 + k * 0.35)))
        px[(nx, ny)] = v
    w = w or (b[2] - b[0]) * 0.5 + 2
    for x in range(-int(w * (0.6 + k * 0.5)), int(w * (0.6 + k * 0.5)) + 1):
        for y in (0, -1):
            if y == -1 and abs(x) > w * 0.5: continue
            px.setdefault((x, y), pool[1] if y == 0 else pool[2])
    return Spr(px)


def legline(c, x0, y0, x1, y1, knee_up=1.5, ch="k", ch2="K"):
    """A thin jointed leg from (x0, y0) to a foot at (x1, y1) with the knee lifted."""
    kx, ky = (x0 + x1) / 2.0 + (x1 - x0) * 0.15, min(y0, y1) - knee_up
    line(c, x0, y0, kx, ky, ch)
    line(c, kx, ky, x1, y1, ch2)


def segs_along(pts, n):
    """n points spaced evenly along polyline pts."""
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out = []
    for k in range(n):
        t = L[-1] * k / max(1, n - 1)
        for i in range(1, len(pts)):
            if L[i] >= t or i == len(pts) - 1:
                a = 0 if L[i] == L[i - 1] else (t - L[i - 1]) / (L[i] - L[i - 1])
                out.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * a, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * a))
                break
    return out


def mandibles(c, hx, hy, open_=0.0, ramp=("W", "X"), size=1.0):
    """Two curved wax pincers at the head's front (hx, hy), opening by open_ (0..1)."""
    for sgn in (-1, 1):
        a0 = math.radians(sgn * (12 + 30 * open_))
        p0 = (hx, hy + sgn * 0.6)
        p1 = (hx + 2.2 * size * math.cos(a0), hy + sgn * 0.6 + 2.2 * size * math.sin(a0))
        p2 = (p1[0] + 1.6 * size, p1[1] - sgn * (1.2 - open_) * size)
        line(c, p0[0], p0[1], p1[0], p1[1], ramp[0])
        line(c, p1[0], p1[1], p2[0], p2[1], ramp[1])


# ====================================================================================== WICKWORM (T2, Tallow Grub)
def bez_path(ctrl, n=24):
    """A smooth path through control points (Catmull-Rom), sampled densely."""
    if len(ctrl) == 2:
        return [ctrl[0], ctrl[1]]
    pts = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(8):
            t = k / 8.0
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(ctrl[-1])
    return out


def worm_body(f, ctrl, radii, ramp, ramp_d, phase=0, lit=True, legs=0.0, leg_ch=("vhw0", "k"), candles=(0, 2, 4), wave=0.0,
              seam="vhw0", cand_size=1, leg_n=None, legs_on=True, cand_h=2, bias=0.1):
    """Segments along a path (tail -> head): shaded plates, a pair of legs under each grounded segment, stub candles."""
    n = len(radii)
    path = bez_path(ctrl)
    pts = segs_along(path, n)
    pts = [(x, y - math.sin(i * 0.9 + wave) * 0.5 * (1 if i < n - 1 else 0)) for i, (x, y) in enumerate(pts)]
    for i in range(1, n - 1 if legs_on else 1):
        x, y = pts[i]
        if y + radii[i] < -2.5: continue
        ph = math.sin(legs * 2 * math.pi + i * 1.3)
        for s_, layer, ch in ((-1, f.u, leg_ch[0]), (1, f.b, leg_ch[1])):
            fx_ = x + s_ * 0.5 + ph * 1.2 * s_
            legline(layer, x + s_ * 0.4, y + radii[i] - 0.6, fx_ + 1.0, 0.0, knee_up=0.8 + max(0.0, ph) * 0.8, ch=ch, ch2="K")
    for i in range(n):
        x, y = pts[i]
        r = radii[i]
        ell(f.b, x, y, r * 1.05, r, ramp_d if i % 2 else ramp, bias=bias)
        f.b.put(*P(x - r * 0.75, y - r * 0.35), seam)
        if i in candles and i < n - 1:
            # the candle stands on the segment's back: along the path's normal that points up (and back)
            a_, b_ = pts[max(0, i - 1)], pts[i + 1]
            tx, ty = b_[0] - a_[0], b_[1] - a_[1]
            L_ = max(0.01, math.hypot(tx, ty)); tx, ty = tx / L_, ty / L_
            nx, ny = (ty, -tx) if (ty, -tx)[1] < (-ty, tx)[1] or ((ty, -tx)[1] == (-ty, tx)[1] and ty < -ty) else (-ty, tx)
            bx_, by_ = x + nx * (r - 0.3) + 0.2, y + ny * (r - 0.3)
            for d in range(cand_h):
                f.b.put(*P(bx_, by_ - d), "W" if d < cand_h - 1 else "X")
            f.b.put(*P(bx_, by_ + 1), "w")
            cx, cy = P(bx_, by_ - cand_h + 1)
            if lit: flame(f.g, cx, cy, size=cand_size, phase=phase + i)
            else: f.g.put(cx, cy - 1, "s")
    return pts


WORM_HEAD = {}    # last drawn head centre (for the TIMING / kit spawn points)


def wickworm(dx=0.0, wave=0.0, rear=0.0, lunge=0.0, open_=0.0, phase=0, eye="lit", lit=True, legs=0.0, curl=0.0,
             dark=False, rise=None):
    """Wickworm ~24 x 21: the Grub grown long and reared - seven plated beeswax segments on rippling legs, the front
    half lifted like a striking centipede with the Grub's candles burning along its back, a big head with the Grub's
    red eye and mouth, wax mandibles and two wick feelers. rear lifts the head higher, lunge throws it forward and down
    to the floor; rise = (x, h) draws it bursting straight up out of the floor at x (burrow); curl coils it (death)."""
    f = Fr()
    if rise is not None:
        x0, h = rise
        ctrl = [(x0 - 1.0, 6.0), (x0, -h * 0.45), (x0 + 1.5, -h)]
    elif curl:
        ctrl = [(dx - 4.0, -7.0 * curl - 2.5), (dx - 9.0, -3.0), (dx - 2.0, -2.8), (dx + 8.0, -3.4 + curl)]
    else:
        ctrl = [(dx - 10.0, -2.8), (dx - 4.5, -3.4), (dx + 0.5 + lunge * 0.6, -5.0 - rear * 1.5 + lunge * 0.4),
                (dx + 4.0 + lunge * 1.4, -9.0 - rear * 3.0 + lunge * 1.8), (dx + 6.0 + lunge * 2.2, -12.0 - rear * 4.0 + lunge * 2.2)]
    radii = [2.2, 2.8, 3.2, 3.5, 3.6, 3.5, 3.8]
    pts = worm_body(f, ctrl, radii, WORM_D if dark else WORM, WORM_D, phase=phase, lit=lit, legs=legs, wave=wave,
                    candles=(1, 3, 5), cand_h=3)
    hx, hy = pts[-1]
    WORM_HEAD["last"] = (hx + 3.0, hy + 1.0)
    # wick feelers: two dark wicks curving forward-up, embers at the tips
    for k, (a0, a1) in enumerate(((-115, -65), (-85, -35))):
        q = V.chain(hx - 0.5 + k, hy - 2.8, [(2.4, a0 - rear * 15), (2.0, a1 - rear * 20)])
        line(f.b, q[0][0], q[0][1], q[1][0], q[1][1], "k")
        line(f.b, q[1][0], q[1][1], q[2][0], q[2][1], "K")
        if lit: f.g.put(*P(*q[2]), "O" if (phase + k) % 2 else "Y")
    f.b.put(*P(hx + 3.2, hy + 1.0), "K")                                  # the Grub's mouth
    mandibles(f.b, hx + 3.0, hy + 1.0, open_=open_, ramp=("vhw3", "W"), size=1.0)
    if eye == "lit":
        f.g.put(*P(hx + 1.4, hy - 1.0), "R"); f.g.put(*P(hx + 0.4, hy - 1.0), "r")
    elif eye == "hot":
        f.g.put(*P(hx + 1.4, hy - 1.0), "Y"); f.g.put(*P(hx + 0.4, hy - 1.0), "R"); f.g.put(*P(hx + 1.4, hy - 2.0), "R")
    return f.done()


def dirt_mound(f, x, k, phase=0, crack=True):
    """A heaving mound of floor and wax crumbs at x (k 0..1 = size)."""
    w = 3 + 5 * k
    for xx in range(int(-w), int(w) + 1):
        h = int(round((1 - (xx / max(1.0, w)) ** 2) * (1 + 2.5 * k)))
        for yy in range(h):
            f.b.put(int(x + xx), -yy, "g" if yy == h - 1 else ("k" if (xx + yy + phase) % 3 else "t"))
    if crack:
        for xx in (-2, 1, 3):
            if abs(xx) < w: f.g.put(int(x + xx), -int(1 + 2 * k), "o" if (xx + phase) % 2 else "O")
    rnd = random.Random(phase + 11)
    for _ in range(int(3 + 4 * k)):
        f.n.put(int(x + rnd.uniform(-w - 2, w + 2)), -int(rnd.uniform(1, 3 + 4 * k)), rnd.choice(["vhw2", "W", "h"]))


def build_wickworm(out):
    idle = [wickworm(wave=i * 1.57, legs=i * 0.08, phase=i, rear=[0, 0.1, 0.15, 0.05][i]) for i in range(4)]
    run = [wickworm(wave=i * 1.05, legs=i / 6.0, phase=i, dx=[0, 0.5, 1, 0.5, 0, -0.5][i], lunge=[0, 0.3, 0.6, 0.3, 0, -0.3][i])
           for i in range(6)]
    # Bite: rear up, jaws wide, strike forward and down to the floor, snap, recover
    bite = []
    for k, kw in enumerate((dict(rear=0.3, open_=0.3), dict(rear=0.8, open_=0.8, lunge=-1.0, eye="hot"),
                            dict(rear=0.2, open_=1.0, lunge=2.5, eye="hot"), dict(rear=-0.2, open_=0.0, lunge=3.8, eye="hot"),
                            dict(rear=0.0, open_=0.1, lunge=2.0), dict())):
        bite.append(wickworm(phase=k, **kw)); mark("VhWickworm", "Bite", k, WORM_HEAD["last"])
    # Burrow: it strikes nose-first into the floor and the body follows; a mound heaves where it went under. The kit
    # teleports it between f5 and f6; it bursts straight up out of a new mound head-first and drops back to a crawl.
    def under(k, phase, x=13):
        f = Fr(); dirt_mound(f, x, k, phase); return f.done()
    burrow = [wickworm(rear=0.5, phase=0, lunge=-1),
              wickworm(rear=-0.3, phase=1, lunge=2.5, eye="hot"),
              wickworm(rear=-0.5, lunge=4.5, phase=2, eye="hot", dx=1).over(under(0.4, 0)),
              wickworm(rear=-0.8, lunge=6.0, phase=3, eye="hot", dx=3, lit=False).over(under(0.7, 1)),
              under(0.9, 2), under(0.6, 3),
              under(1.0, 0, 1).over(wickworm(rise=(1, 12), open_=1.0, eye="hot", lit=False)),
              under(0.8, 1, 1).over(wickworm(rise=(1, 18), open_=0.7, eye="hot", phase=1)),
              under(0.4, 2, 1).over(wickworm(rear=0.6, open_=0.2, phase=2, dx=-2)),
              wickworm(rear=0.2, phase=3)]
    death = [wickworm(rear=0.8, open_=1.0, eye="hot", phase=0, lunge=-1),
             wickworm(curl=0.5, open_=0.6, phase=1, lit=False, eye="dim"),
             melt(wickworm(curl=1.0, lit=False, eye="dim", dark=True), 0.35, WORM),
             melt(wickworm(curl=1.0, lit=False, eye="dim", dark=True), 0.7, WORM)]
    knock = wickworm(rear=0.9, open_=1.0, lunge=-2, eye="hot")
    anims = [("Idle", idle, [0.16] * 4), ("Run", run, [0.08] * 6),
             ("Bite", bite, [0.1, 0.12, 0.05, 0.08, 0.1, 0.12]),
             ("Burrow", burrow, [0.08, 0.08, 0.08, 0.08, 0.12, 0.33, 0.06, 0.08, 0.1, 0.12])] + \
        tail(idle[0], death, [0.1, 0.12, 0.14, 0.3], knock)
    sheet("VhWickworm", anims, out)


# ====================================================================================== TALLOW SOW (T2, Tallow Grub)
def sow(dx=0.0, dy=0.0, swell=0.0, head=(0.0, 0.0), mouth=0, phase=0, eggs=5, lay=0.0, legs=0.0, eye="lit", lit=True,
        squash=1.0, dark=False):
    """Tallow Sow ~24 x 18: a grub queen - a great translucent belly of rendered fat (bands like the Grub's segments)
    with amber eggs glowing inside, three Grub candles along its back, a small Grub head with its red eye in front,
    six stubby legs. swell = belly pulse, lay = ovipositor push at the back."""
    f = Fr()
    bx, by = dx - 3.0, dy - 7.0 * squash
    rx, ry = 8.5 + swell * 1.2, 6.2 * squash + swell
    # stubby legs
    for i, lx in enumerate((-8, -3, 2)):
        ph = math.sin(legs * 2 * math.pi + i * 2.1) * 1.0
        for s_, layer in ((-1, f.u), (1, f.b)):
            tube(layer, [(dx + lx + s_ * 0.5, by + 3.5), (dx + lx + s_ * 0.8 + ph * s_, -0.6)], [1.0, 0.8], FAT_D)
    # the belly: shaded fat, darker bands
    def band(nu, nv, d, l, ch, x, y):
        if abs(math.sin((x - bx) * 0.75)) < 0.18 and d > 0.15: return FAT[0]
        return ch
    ell(f.b, bx, by, rx, ry, FAT_D if dark else FAT, bias=0.05, shader=band)
    # the eggs glowing through the fat
    rnd = random.Random(5)
    for k in range(eggs):
        ex = bx - rx * 0.5 + k * rx * 0.28 + rnd.uniform(-0.6, 0.6)
        ey = by + ry * 0.15 + (k % 2) * 1.6 - 0.8
        if dark:
            f.b.put(*P(ex, ey), "vhs1")
            continue
        pul = (phase + k) % 3 == 0
        x_, y_ = P(ex, ey)
        f.g.put(x_, y_, "vhe2" if pul else "vhe1"); f.g.put(x_ + 1, y_, "vhe1")
        f.g.put(x_, y_ + 1, "vhe1"); f.g.put(x_ + 1, y_ + 1, "vhe0")
    # ovipositor at the back
    if lay:
        tube(f.b, [(bx - rx + 1.0, by + 2.0), (bx - rx - 1.0 - lay * 1.5, by + 3.0 + lay * 2.0)], [1.4, 1.0], FAT)
    # candles on the back (the Grub's)
    for k, cx in enumerate((-4.0, 0.0, 4.0)):
        top = by - ry * math.sqrt(max(0.0, 1 - (cx / rx) ** 2)) + 0.6
        candle(f, bx + cx, top, 2 if k != 1 else 3, phase=phase + k, size=1, lit=lit, drip=0)
    # neck segments and the head
    hx, hy = dx + 6.5 + head[0], dy - 5.0 * squash + head[1]
    ell(f.b, dx + 4.5, dy - 4.5 * squash, 2.6, 2.8, FAT_D, bias=0.1)
    ell(f.b, hx, hy, 2.6, 2.4, FAT, bias=0.15)
    f.b.put(*P(hx + 2.2, hy + 0.6), "K")
    if mouth:
        f.b.put(*P(hx + 2.4, hy + 0.0), "X"); f.b.put(*P(hx + 2.4, hy + 1.4), "X"); f.b.put(*P(hx + 3.0, hy + 0.6), "K")
        if mouth > 1:
            f.g.put(*P(hx + 3.6, hy + 0.6), "W"); f.g.put(*P(hx + 4.4, hy + 0.2), "w")
    if eye == "lit":
        f.g.put(*P(hx + 0.6, hy - 1.0), "R"); f.g.put(*P(hx - 0.4, hy - 1.0), "r")
    elif eye == "hot":
        f.g.put(*P(hx + 0.6, hy - 1.0), "Y"); f.g.put(*P(hx - 0.4, hy - 1.0), "R")
    return f.done()


def wax_egg_px(f, x, y, k=1.0, glow=1):
    ell(f.b, x, y - 2.0 * k, 2.0 * k, 2.2 * k, FAT, bias=0.25)
    if glow: f.g.put(*P(x, y - 1.6 * k), "vhe2" if glow > 1 else "vhe1")


def build_sow(out):
    idle = [sow(swell=[0, 0.3, 0.5, 0.2][i], phase=i, head=(0, [0, -0.3, -0.5, -0.2][i])) for i in range(4)]
    run = [sow(dx=[0, 0.5, 1, 0.5, 0, -0.5][i], dy=-abs(math.sin(i * math.pi / 3)) * 0.6, legs=i / 6.0, phase=i,
               squash=[1, 0.96, 0.94, 0.97, 1, 0.98][i]) for i in range(6)]
    spray = [sow(head=(-0.5, 0.5), swell=0.2, phase=0),
             sow(head=(-1.0, -1.0), swell=0.6, mouth=1, phase=1),
             sow(head=(-0.5, -1.6), swell=0.9, mouth=1, phase=2, eye="hot"),
             sow(head=(1.2, 0.0), swell=0.3, mouth=2, phase=3, eye="hot"),
             sow(head=(0.8, 0.2), swell=0.1, mouth=1, phase=0),
             sow(phase=1)]
    def egg_at(i):
        def ex(f): wax_egg_px(f, -15, 0, 0.8 + i * 0.1, glow=1)
        return ex
    lay = []
    for i, (sw, ly, sq) in enumerate(((0.3, 0, 1.0), (0.8, 0.3, 0.95), (1.2, 0.8, 0.9), (1.4, 1.2, 0.88), (0.6, 1.4, 0.94),
                                      (0.2, 0.8, 1.0), (0.1, 0.2, 1.0), (0.0, 0, 1.0))):
        s = sow(swell=sw, lay=ly, squash=sq, phase=i, eggs=5 if i < 4 else 3, eye="hot" if 2 <= i <= 4 else "lit")
        if i >= 4:
            ff = Fr(); wax_egg_px(ff, -15 + (i - 4) * -0.5, 0, 1.0, glow=2 if i % 2 else 1); s = ff.done().over(s)
        lay.append(s)
    death = [sow(swell=1.0, mouth=2, eye="hot", phase=0),
             sow(swell=-0.5, squash=0.8, mouth=2, lit=False, eye="dim", phase=1, dark=True),
             melt(sow(squash=0.7, lit=False, eye="dim", dark=True, eggs=0), 0.4),
             melt(sow(squash=0.6, lit=False, eye="dim", dark=True, eggs=0), 0.75)]
    knock = sow(head=(-1.5, -1.0), swell=0.8, mouth=2, eye="hot", squash=1.05)
    anims = [("Idle", idle, [0.2] * 4), ("Run", run, [0.1] * 6),
             ("Spray", spray, [0.1, 0.1, 0.12, 0.06, 0.1, 0.12]),
             ("Lay", lay, [0.1, 0.1, 0.1, 0.12, 0.1, 0.1, 0.1, 0.12])] + \
        tail(idle[0], death, [0.1, 0.12, 0.14, 0.3], knock)
    sheet("VhTallowSow", anims, out)



MOUTH = {}     # sheet -> {(anim, frame): (x, y)} spawn points read by TIMING (feet-relative, y up negative)


def mark(name, anim, k, xy):
    MOUTH.setdefault(name, {})[(anim, k)] = (int(round(xy[0])), int(round(xy[1])))


# ====================================================================================== CANDLE WYRM (T3, Wickworm)
WYRM = ["vhw1", "vhw2", "vhw3", "vhw4"]


def wyrm(rear=0.0, strike=0.0, open_=0.0, throat=0, phase=0, eye="lit", lit=True, legs=0.0, sway=0.0, sag=0.0, dark=False,
         fire=0):
    """Candle Wyrm ~34 x 36: the Wickworm reared up - ten gold-beeswax plates rising in an S from a coiled tail, a big
    head ringed by a mane of five candles, the worm's red eyes and mandibles, its wick feelers grown long.
    rear pulls the head back/up, strike throws it forward and down, throat glows (spit), sag collapses it (death)."""
    f = Fr()
    hx = 7.0 - rear * 3.0 + strike * 8.0 + sway
    hy = -27.0 - rear * 3.0 + strike * 12.0 + sag * 20.0
    ctrl = [(-15.0, -2.8), (-8.0, -3.4), (-1.0, -5.0 - sag * -2), (0.5 + sway * 0.5 + strike * 2, -14.0 + sag * 10 + strike * 4),
            (2.5 + sway + strike * 5 - rear, -21.0 + sag * 15 + strike * 8), (hx - 2.0, hy + 0.5)]
    radii = [2.0, 2.6, 3.2, 3.6, 3.8, 3.9, 3.8, 3.6, 3.4, 3.2, 3.1, 3.0]
    # mane of candles behind the head (under-layer)
    for k, a in enumerate((-170, -140, -110, -80, -50)):
        ax, ay = hx - 1.0 + 5.4 * math.cos(math.radians(a)), hy - 0.5 + 5.0 * math.sin(math.radians(a))
        candle(f, ax - 0.5, ay + 1.5, 3 if k % 2 else 4, phase=phase + k, size=(2 if fire else 1), lit=lit, layer="u", drip=1)
    pts = worm_body(f, ctrl, radii, WORM_D if dark else WORM, WORM_D, phase=phase, lit=lit, legs=legs, candles=(1, 3),
                    seam="vhw0")
    # the head: a broad plated skull
    ell(f.b, hx, hy, 4.6, 4.0, WORM_D if dark else WYRM, bias=0.1)
    for k in range(4): f.b.put(*P(hx - 3.0 + k * 1.6, hy - 2.8 + abs(k - 1.5) * 0.6), "vhw1")   # brow plates
    # a frill of hanging wax behind the jaw
    for k in range(4):
        for d in range(2 + k % 2):
            f.b.put(*P(hx - 3.5 + k, hy + 3.2 + d), "vhw3" if d == 0 else "vhw2")
    for k, (a0, a1) in enumerate(((-100, -40), (-70, -10))):
        q = V.chain(hx + 0.5 + k, hy - 3.0, [(3.0, a0 - rear * 15), (2.6, a1 - rear * 15)])
        line(f.b, q[0][0], q[0][1], q[1][0], q[1][1], "k"); line(f.b, q[1][0], q[1][1], q[2][0], q[2][1], "K")
        if lit: f.g.put(*P(*q[2]), "Y" if (phase + k) % 2 else "O")
    mandibles(f.b, hx + 3.6, hy + 1.6, open_=open_, ramp=("vhw3", "W"), size=1.3)
    mx, my = hx + 4.0, hy + 1.6
    if throat:
        for k in range(throat + 1):
            f.g.put(*P(hx + 1.5 - k * 0.8, hy + 2.0 + k * 1.4), "O" if k % 2 else "Y")
        f.g.put(*P(mx, my), "y" if throat > 1 else "Y")
    if fire:
        for dx_, dy_, ch in ((1, 0, "y"), (2, 0, "Y"), (1, -1, "Y"), (1, 1, "Y"), (3, 0, "O"), (2, -1, "O"), (2, 1, "O"), (4, 0, "o")):
            f.g.put(*P(mx + dx_ * fire * 0.7, my + dy_), ch)
    if eye == "lit":
        for ex in (0.8, 2.2): f.g.put(*P(hx + ex, hy - 0.8), "R")
        f.g.put(*P(hx + 0.8, hy - 0.0), "r")
    elif eye == "hot":
        for ex in (0.8, 2.2): f.g.put(*P(hx + ex, hy - 0.8), "Y")
        f.g.put(*P(hx + 1.5, hy - 1.6), "R")
    return f.done(), (mx, my)


def build_wyrm(out):
    W = lambda **k: wyrm(**k)[0]
    idle = [W(sway=[0, 0.5, 1, 0.5][i], rear=[0, 0.1, 0.2, 0.1][i], phase=i) for i in range(4)]
    run = [W(sway=[0, 1, 1.5, 1, 0, -0.5][i], legs=i / 6.0, phase=i, strike=[0.05, 0.1, 0.12, 0.08, 0.04, 0][i]) for i in range(6)]
    bite = [W(rear=0.6, open_=0.4, phase=0), W(rear=1.2, open_=1.0, phase=1, eye="hot"),
            W(strike=0.7, open_=1.0, phase=2, eye="hot"), W(strike=0.95, open_=0.0, phase=3, eye="hot"),
            W(strike=0.5, open_=0.2, phase=0), W(strike=0.1, phase=1)]
    spit = []
    for k, kw in enumerate((dict(rear=0.6, throat=1), dict(rear=1.3, throat=2, open_=0.4), dict(rear=1.5, throat=3, open_=0.8, eye="hot"),
                            dict(strike=0.35, throat=3, open_=1.0, fire=2, eye="hot"), dict(strike=0.45, open_=1.0, fire=1, eye="hot"),
                            dict(strike=0.25, open_=0.4), dict(rear=0.1))):
        spr, m = wyrm(phase=k, **kw)
        spit.append(spr)
        mark("VhCandleWyrm", "Spit", k, m)
    for k, kw in enumerate((dict(strike=0.7), dict(strike=0.95))):
        mark("VhCandleWyrm", "Bite", 2 + k, wyrm(**kw)[1])
    death = [W(rear=1.4, open_=1.0, eye="hot"), W(sag=0.4, open_=0.8, lit=False, eye="dim"),
             melt(W(sag=0.8, lit=False, eye="dim", dark=True), 0.3, WORM), melt(W(sag=1.0, lit=False, eye="dim", dark=True), 0.65, WORM)]
    knock = W(rear=1.6, open_=1.0, eye="hot", sway=-2)
    anims = [("Idle", idle, [0.18] * 4), ("Run", run, [0.09] * 6),
             ("Bite", bite, [0.12, 0.14, 0.05, 0.1, 0.1, 0.12]),
             ("Spit", spit, [0.1, 0.12, 0.14, 0.06, 0.1, 0.1, 0.12])] + tail(idle[0], death, [0.12, 0.12, 0.16, 0.3], knock)
    sheet("VhCandleWyrm", anims, out)


# ====================================================================================== FUSE SCORPION (T3, Wickworm)
def scorpion(tail_t=0.0, claw=0.0, reach=0.0, phase=0, eye="lit", lit=True, legs=0.0, dy=0.0, dark=False, spark=1, barb=True):
    """Fuse Scorpion ~36 x 28: the Wickworm hardened into soot-black plates on beeswax joints, raised on four pairs of
    legs, two heavy pincers tipped with wax, and its tail curled over the back ending in a lit fuse-wick sting.
    tail_t 0 = cocked over the back, 1 = whipped forward over the head; claw = pincers open; reach thrusts them."""
    f = Fr()
    by = -8.0 + dy
    joint = ["vhf1", "vhw1", "vhw2", "vhw3"]
    # legs: four pairs, long, knees high above the body's flank
    for i, (root, foot) in enumerate(((-7, -15), (-3, -9), (1, 6), (5, 12))):
        ph = math.sin(legs * 2 * math.pi + i * 1.6)
        for s_, layer, ch in ((-1, f.u, "vhf2"), (1, f.b, "vhw2")):
            fx_ = foot + s_ * 1.0 + ph * 1.6 * s_
            kx, ky = root + (fx_ - root) * 0.55, by - 3.5 - max(0.0, ph) * 1.2
            line(layer, root + s_ * 0.4, by + 1.5, kx, ky, ch)
            line(layer, kx, ky, fx_, 0.0, "vhf2" if s_ < 0 else "vhf3")
    pts_ = worm_body(f, [(-11.0, by + 0.5), (-2.0, by - 0.8), (6.0, by)], [2.8, 3.4, 3.8, 3.9, 3.8, 3.5], SOOT, SOOT,
                     phase=phase, lit=False, candles=(), seam="vhw3", legs_on=False, bias=0.12)
    for (x, y) in pts_[:-1]:                                  # beeswax showing at each joint (the Wickworm under the plates)
        for d in (-1, 0, 1):
            f.b.put(*P(x - 2.4, y + d), "vhw2" if d else "vhw3")
    # tail: from the rump up over the back; tail_t swings it forward
    t = tail_t
    ctrl = [(-12.0, by - 1.0), (-17.0 + 3 * t, by - 7 + t), (-15.0 + 9 * t, by - 15 - t * 2), (-7.0 + 16 * t, by - 19 + t * 3),
            (0.0 + 16 * t, by - 16 + t * 8)]
    tp = segs_along(bez_path(ctrl), 13)
    for k, (x, y) in enumerate(tp):
        r = 2.7 - k * 0.12
        ell(f.b, x, y, r, r, SOOT if (k // 2) % 2 == 0 else joint, bias=0.12)
    sx, sy = tp[-1]
    dxs, dys = sx - tp[-3][0], sy - tp[-3][1]
    L = max(0.1, math.hypot(dxs, dys)); dxs, dys = dxs / L, dys / L
    tip = (sx + dxs * 4.0, sy + dys * 4.0)
    if barb:
        line(f.b, sx, sy, sx + dxs * 3.0, sy + dys * 3.0, "W")
        f.b.put(*P(*tip), "X")
        wx, wy = sx - dys * 2.0, sy + dxs * 2.0 - 1.0          # the fuse: a dark wick off the barb, burning at the end
        line(f.b, sx, sy, wx, wy - 1.0, "K")
        if lit:
            f.g.put(*P(wx, wy - 1.5), "y"); f.g.put(*P(wx + (phase % 2), wy - 2.5), "Y")
            for k in range(spark + 1):
                a = phase * 1.7 + k * 2.1
                f.g.put(*P(wx + math.cos(a) * 2.2, wy - 2.0 + math.sin(a) * 1.7), "O" if k % 2 else "Y")
    # head and pincers
    hx, hy = 8.0 + reach * 0.4, by - 0.5
    ell(f.b, hx, hy, 3.4, 3.0, SOOT, bias=0.2)
    for s_, layer in ((-1, f.u), (1, f.b)):
        ex_, ey_ = hx + 3.0 + reach * 0.5, hy + 2.0 + s_ * 0.8
        cx_, cy_ = ex_ + 3.5 + reach, ey_ - 2.0 - s_ * 0.5
        ramp = SOOT if s_ > 0 else ["vhf0", "vhf0", "vhf1", "vhf2"]
        tube(layer, [(hx + 1.0, hy + 1.0), (ex_, ey_), (cx_ - 1.5, cy_ + 0.5)], [1.3, 1.2, 1.5], ramp)
        ell(layer, cx_, cy_, 2.6, 2.0, ramp, bias=0.2)                     # the claw's palm
        a = math.radians(-20 - claw * 35)
        b = math.radians(20 + claw * 30)
        line(layer, cx_ + 1.5, cy_ - 1.0, cx_ + 1.5 + 3.4 * math.cos(a), cy_ - 1.0 + 3.4 * math.sin(a), "vhw3")
        line(layer, cx_ + 1.5, cy_ + 0.8, cx_ + 1.5 + 2.8 * math.cos(b), cy_ + 0.8 + 2.8 * math.sin(b), "vhw2")
    for k in range(2):
        q = V.chain(hx + 0.5 + k, hy - 2.6, [(1.8, -100 + k * 30), (1.4, -50 + k * 25)])
        line(f.b, q[0][0], q[0][1], q[1][0], q[1][1], "k"); line(f.b, q[1][0], q[1][1], q[2][0], q[2][1], "K")
        if lit: f.g.put(*P(*q[2]), "O")
    if eye == "lit":
        f.g.put(*P(hx + 1.2, hy - 1.2), "R"); f.g.put(*P(hx + 2.2, hy - 1.2), "R")
    elif eye == "hot":
        f.g.put(*P(hx + 1.2, hy - 1.2), "Y"); f.g.put(*P(hx + 2.2, hy - 1.2), "Y")
    return f.done(), tip


def build_scorpion(out):
    S = lambda **k: scorpion(**k)[0]
    idle = [S(tail_t=[0, 0.04, 0.08, 0.04][i], claw=[0.1, 0.2, 0.3, 0.2][i], phase=i, spark=i % 3) for i in range(4)]
    run = [S(legs=i / 6.0, phase=i, dy=-abs(math.sin(i * math.pi / 3)) * 0.5, tail_t=0.05 * (i % 2)) for i in range(6)]
    pinch = [S(claw=0.6, reach=-1, phase=0), S(claw=1.0, reach=-2, phase=1, eye="hot"), S(claw=1.0, reach=3, phase=2, eye="hot"),
             S(claw=0.0, reach=4, phase=3, eye="hot"), S(claw=0.3, reach=1.5, phase=0), S(claw=0.2, phase=1)]
    sting = []
    for k, kw in enumerate((dict(tail_t=-0.15, claw=0.3), dict(tail_t=-0.3, claw=0.5, eye="hot", spark=3),
                            dict(tail_t=0.4, eye="hot", spark=3), dict(tail_t=0.85, eye="hot", spark=2),
                            dict(tail_t=1.0, eye="hot", barb=False), dict(tail_t=0.6, barb=False), dict(tail_t=0.15))):
        spr, m = scorpion(phase=k, **kw)
        sting.append(spr); mark("VhFuseScorpion", "Sting", k, m)
    death = [S(claw=1.0, tail_t=-0.3, eye="hot"), S(dy=2, tail_t=0.2, lit=False, eye="dim", claw=0.5),
             melt(S(dy=3, tail_t=0.5, lit=False, eye="dim", dark=True), 0.4, SOOT), melt(S(dy=3, tail_t=0.6, lit=False, eye="dim"), 0.7, SOOT)]
    knock = S(claw=1.0, tail_t=-0.4, eye="hot", dy=-1)
    anims = [("Idle", idle, [0.16] * 4), ("Run", run, [0.08] * 6),
             ("Pinch", pinch, [0.1, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Sting", sting, [0.1, 0.14, 0.06, 0.06, 0.12, 0.1, 0.12])] + tail(idle[0], death, [0.1, 0.12, 0.16, 0.3], knock)
    sheet("VhFuseScorpion", anims, out)


# ====================================================================================== BROOD MOTHER (T3, Tallow Sow)
def brood(rear=0.0, slam=0.0, split=0.0, phase=0, eye="lit", lit=True, legs=0.0, swell=0.0, dark=False, spill=0, squash=1.0,
          mouth=0):
    """Grub Mother ~40 x 28: the Sow grown huge and carrying her clutch - a long rendered-fat belly with the Sow's bands,
    a mound of glowing amber eggs heaped on her back (grublings curled inside), three Sow candles burning among them,
    the front reared on a thick neck with the Grub head, red eyes and mandibles. split opens the clutch; spill pours
    grublings out down her flank."""
    f = Fr()
    bx, by = -5.0, -8.5 * squash
    rx, ry = 13.0 + swell, 7.0 * squash + swell * 0.6
    for i, lx in enumerate((-14, -9, -3, 2)):
        ph = math.sin(legs * 2 * math.pi + i * 1.7)
        for s_, layer in ((-1, f.u), (1, f.b)):
            tube(layer, [(lx + s_ * 0.6, by + 4.0), (lx + s_ * 1.0 + ph * s_ * 1.2, -0.5)], [1.4, 1.0], FAT if s_ > 0 else FAT_D)
    def band(nu, nv, d, l, ch, x, y):
        if abs(math.sin((x - bx) * 0.62)) < 0.1 and d > 0.12 and nv > -0.3: return FAT[1]
        return ch
    ell(f.b, bx, by, rx, ry, FAT_D if dark else FAT, bias=0.05, shader=band)
    # the clutch heaped on the back
    eggs = [(-11, -14.5), (-7, -16.5), (-3, -16.0), (1, -14.5), (-9, -19.5), (-5, -20.5), (-1.5, -19.0), (-7, -23.5), (-3.5, -23.0)]
    for k, (ex, ey) in enumerate(eggs):
        ex += (-split * 2.0 if ex < -5 else split * 2.0) * (1 if k < 7 else 0.5)
        ey = ey * squash - split * (1.0 if k >= 4 else 0.0)
        if spill and k >= 7: continue
        ell(f.b, ex, ey, 2.2, 2.5, ["vhs1", "vhe0", "vhe1", "vhe2"] if not dark else FAT_D, bias=0.1)
        for ang in range(200, 340, 30):                           # a dark rim where each egg meets the next
            f.b.put(*P(ex + 2.3 * math.cos(math.radians(ang + 180)), ey + 2.4 * math.sin(math.radians(ang + 180)) * -1), "vhs0")
        if not dark:
            f.g.put(*P(ex - 0.6, ey - 0.8), "vhe2" if (phase + k) % 3 == 0 else "vhe1")
            f.b.put(*P(ex + 0.5, ey + 0.7), "vhs1")      # the curled grubling inside
            f.b.put(*P(ex + 0.8, ey + 0.0), "vhs1")
    for k, (cx, cy) in enumerate(((-13.5, -14.0), (-5.5, -25.5), (3.0, -13.0))):
        candle(f, cx, (cy - split) * squash + 0.5, 2 if k != 1 else 3, phase=phase + k, size=1 if k != 1 else 2, lit=lit)
    # grublings spilling out
    if spill:
        rnd = random.Random(spill)
        for k in range(spill * 2 + 1):
            gx, gy = -16 + rnd.uniform(-4, 4) - k * 1.2, -2 - rnd.uniform(0, 8) + k * 0.8
            ell(f.b, gx, gy, 1.6, 1.0, FAT, bias=0.2)
            f.g.put(*P(gx + 1.2, gy - 0.4), "R")
    # neck and head, reared
    hx = 10.5 + slam * 4.0 - rear * 1.0
    hy = -13.0 - rear * 5.0 + slam * 9.0
    tube(f.b, [(5.0, by - 1.0), ((5.0 + hx) / 2 + 0.5, (by + hy) / 2 - 1.5), (hx - 1.0, hy + 0.5)], [3.6, 3.2, 2.8], FAT)
    ell(f.b, hx, hy, 3.3, 3.0, FAT, bias=0.2)
    mandibles(f.b, hx + 3.0, hy + 1.2, open_=0.8 if mouth else 0.2, ramp=("vhs3", "X"), size=1.0)
    if eye == "lit":
        for ex in (0.6, 1.8): f.g.put(*P(hx + ex, hy - 1.0), "R")
    elif eye == "hot":
        for ex in (0.6, 1.8): f.g.put(*P(hx + ex, hy - 1.0), "Y")
    if slam > 0.9:
        for x in range(int(hx) - 4, int(hx) + 7):
            if x % 2: f.n.put(x, 0, "h")
        f.n.put(int(hx) - 5, -2, "W"); f.n.put(int(hx) + 7, -3, "W"); f.n.put(int(hx) + 8, -1, "w")
    return f.done()


def build_brood(out):
    idle = [brood(swell=[0, 0.3, 0.5, 0.2][i], rear=[0, 0.1, 0.2, 0.1][i], phase=i) for i in range(4)]
    run = [brood(legs=i / 6.0, phase=i, squash=[1, 0.97, 0.95, 0.97, 1, 0.99][i], rear=0.1 * (i % 2)) for i in range(6)]
    slam = [brood(rear=0.6, phase=0), brood(rear=1.4, mouth=1, phase=1, eye="hot"), brood(rear=1.7, mouth=1, phase=2, eye="hot"),
            brood(slam=1.0, squash=0.92, mouth=1, phase=3, eye="hot"), brood(slam=0.8, squash=0.95, phase=0), brood(slam=0.2, phase=1)]
    clutch = [brood(swell=0.4, phase=0), brood(swell=1.0, squash=0.95, phase=1, eye="hot"), brood(swell=1.4, squash=0.9, split=0.5, phase=2, eye="hot"),
              brood(swell=1.6, squash=0.88, split=1.0, phase=3, eye="hot", mouth=1), brood(swell=0.8, split=1.4, phase=0, spill=1, eye="hot"),
              brood(swell=0.2, split=1.0, phase=1, spill=2), brood(split=0.5, phase=2, spill=1), brood(phase=3)]
    death = [brood(rear=1.5, mouth=1, eye="hot"), brood(squash=0.8, lit=False, eye="dim", dark=True, mouth=1),
             melt(brood(squash=0.7, lit=False, eye="dim", dark=True), 0.4), melt(brood(squash=0.6, lit=False, eye="dim", dark=True), 0.72)]
    knock = brood(rear=1.8, mouth=1, eye="hot", squash=1.04)
    anims = [("Idle", idle, [0.2] * 4), ("Run", run, [0.11] * 6),
             ("Slam", slam, [0.12, 0.14, 0.1, 0.06, 0.14, 0.12]),
             ("Clutch", clutch, [0.1, 0.12, 0.12, 0.1, 0.08, 0.12, 0.12, 0.12])] + tail(idle[0], death, [0.12, 0.12, 0.16, 0.3], knock)
    sheet("VhBroodMother", anims, out)


# ====================================================================================== PYRE TICK (T3, Tallow Sow)
def tick(swell=0.0, lunge=0.0, phase=0, eye="lit", lit=True, legs=0.0, dy=0.0, burst=0, dark=False, squash=1.0, open_=0.0):
    """Pyre Tick ~32 x 26: the Sow's belly gorged on fire - a round scorched shell split by molten cracks, two of the
    Sow's candles drowning in its back, pink fat showing at every joint, a small barbed head with red eyes, eight
    spindly black legs. swell puffs it up (Bloat), burst blazes the cracks and sprays droplets."""
    f = Fr()
    bx, by = -2.0, (-13.0 + dy) * squash
    rx, ry = 10.0 + swell * 2.0, 8.0 * squash + swell * 1.6
    for i, (root, foot) in enumerate(((-6, -14), (-2, -9), (2, 7), (6, 13))):
        ph = math.sin(legs * 2 * math.pi + i * 1.5)
        for s_, layer, ch in ((-1, f.u, "vht3"), (1, f.b, "vht4")):
            fx_ = foot + s_ * 1.0 + ph * 1.5 * s_
            kx, ky = root + (fx_ - root) * 0.8, by - 4.0 - max(0.0, ph) * 1.0 - (2.0 if abs(foot) > 10 else 0.0)
            line(layer, root + s_ * 0.5, by + 2.0, kx, ky, ch)
            line(layer, kx, ky, fx_, 0.0, "vht2" if s_ < 0 else "vht3")
            layer.put(*P(kx, ky), "vhs2")                 # pink fat at the knee
    ell(f.b, bx, by, rx, ry, ["vht0", "vht1", "vht2", "vht3", "vht4"] if not dark else ["vht0", "vht0", "vht1", "vht2"], bias=0.42)
    # molten cracks: jagged seams radiating from the crown of the shell
    rnd = random.Random(7)
    for k in range(6):
        a = math.radians(-160 + k * 30 + rnd.uniform(-8, 8))
        x, y = bx - 1.0, by - ry * 0.35
        for j in range(9):
            a += rnd.uniform(-0.45, 0.45)
            nx_, ny_ = x + math.cos(a) * 1.3, y + math.sin(a) * 1.1 + 0.35
            if ((nx_ - bx) / rx) ** 2 + ((ny_ - by) / ry) ** 2 > 0.82: break
            x, y = nx_, ny_
            f.b.put(*P(x, y), "vht0")
            if not dark:
                f.g.put(*P(x, y), ("y" if burst else "Y") if j < 2 else (("Y" if burst else "O") if j < 5 else "o"))
                if j < 6: f.g.put(*P(x, y + 1), "O" if j < 3 else "o")          # the seam glows two pixels wide
    for k, cx in enumerate((-4.5, 1.5)):
        top = by - ry * math.sqrt(max(0.0, 1 - (cx / rx) ** 2)) + 1.5
        candle(f, bx + cx, top, 2, phase=phase + k, size=2 if burst else 1, lit=lit)
    hx, hy = bx + rx + 1.5 + lunge, by + 2.5 + lunge * 0.4
    ell(f.b, hx, hy, 2.6, 2.2, FAT, bias=0.15)
    for s_ in (-1, 1):
        a = math.radians(s_ * (10 + open_ * 25))
        line(f.b, hx + 2.0, hy + s_ * 0.6, hx + 2.0 + 2.6 * math.cos(a), hy + s_ * 0.6 + 2.6 * math.sin(a), "X")
    if eye == "lit":
        f.g.put(*P(bx + rx - 1.5, by - 1.5), "R"); f.g.put(*P(bx + rx - 0.5, by - 0.2), "R")
    elif eye == "hot":
        f.g.put(*P(bx + rx - 1.5, by - 1.5), "Y"); f.g.put(*P(bx + rx - 0.5, by - 0.2), "Y")
    if burst:
        rnd = random.Random(burst)
        for k in range(12):
            a = k * math.pi * 2 / 12 + rnd.uniform(-0.2, 0.2)
            r = max(rx, ry) + 2 + burst * 2.5 + rnd.uniform(0, 2)
            x, y = bx + r * math.cos(a), by + r * 0.8 * math.sin(a)
            if y > -1: continue
            f.g.put(*P(x, y), "Y"); f.g.put(*P(x - math.cos(a), y - math.sin(a) * 0.8), "O")
    return f.done()


def build_tick(out):
    idle = [tick(swell=[0, 0.15, 0.3, 0.15][i], phase=i) for i in range(4)]
    run = [tick(legs=i / 6.0, phase=i, dy=-abs(math.sin(i * math.pi / 3)) * 0.8) for i in range(6)]
    bite = [tick(lunge=-1, open_=0.6, phase=0, dy=0.5), tick(lunge=-2, open_=1.0, phase=1, eye="hot", dy=1),
            tick(lunge=3, open_=1.0, phase=2, eye="hot", dy=-0.5), tick(lunge=4, open_=0.0, phase=3, eye="hot"),
            tick(lunge=2, open_=0.1, phase=0, swell=0.2), tick(phase=1)]
    bloat = [tick(swell=0.3, phase=0), tick(swell=0.8, phase=1, eye="hot"), tick(swell=1.3, phase=2, eye="hot", squash=0.97),
             tick(swell=1.7, phase=3, eye="hot", squash=0.95), tick(swell=1.9, phase=0, eye="hot", burst=1),
             tick(swell=0.4, phase=1, burst=2), tick(swell=-0.3, phase=2, squash=0.95), tick(phase=3)]
    death = [tick(swell=1.2, eye="hot", burst=1), tick(swell=-0.5, squash=0.8, lit=False, eye="dim", dark=True),
             melt(tick(swell=-0.8, squash=0.7, lit=False, eye="dim", dark=True), 0.45, TICK),
             melt(tick(swell=-1.0, squash=0.6, lit=False, eye="dim", dark=True), 0.75, TICK)]
    knock = tick(swell=0.4, lunge=-2, eye="hot", dy=-1.5, open_=1.0)
    anims = [("Idle", idle, [0.18] * 4), ("Run", run, [0.08] * 6),
             ("Bite", bite, [0.1, 0.12, 0.05, 0.1, 0.1, 0.12]),
             ("Bloat", bloat, [0.1, 0.12, 0.12, 0.12, 0.06, 0.1, 0.1, 0.12])] + tail(idle[0], death, [0.1, 0.12, 0.16, 0.3], knock)
    sheet("VhPyreTick", anims, out)


# ====================================================================================== PYRE WARDEN (T3, Waxen Knight)
def censer(f, x, y, phase=0, blaze=1, layer="b"):
    """A brass censer ball, spiked, fire showing through its pierced shell."""
    c = getattr(f, layer)
    ell(c, x, y, 2.6, 2.6, BRASS, bias=0.15)
    for a in range(0, 360, 60):
        c.put(*P(x + 3.3 * math.cos(math.radians(a + 15)), y + 3.3 * math.sin(math.radians(a + 15))), "k")
    for dx_, dy_ in ((-1, 0), (1, 0), (0, 1)):
        f.g.put(*P(x + dx_, y + dy_), "Y" if blaze > 1 else ("O" if (dx_ + phase) % 2 else "o"))
    f.g.put(*P(x, y - 3.5 - phase % 2), "o" if blaze else "s")


def warden(dy=0.0, lean=0.0, ball=(-12.0, -14.0), hand_b=(-7.0, -16.0), shield=(0.0, 0.0), legs=((-3, 0), (3, 0)),
           phase=0, visor="lit", crown=1, glyph=1, blaze=1, guard=0, crouch=0.0, dark=False, smash=0):
    """Pyre Warden ~30 x 36: the Waxen Knight grown into a rust-and-iron bulwark - great-helm with the Knight's red
    visor slit and its three-candle crown, iron plate edged in rust, a tower shield sealed with a burning wax sigil,
    and a brass censer-flail swung on a chain. shield = (dx, dy) of the shield, guard = shield sigil flare (Bulwark)."""
    f = Fr()
    by = dy + crouch
    hip = (lean * 0.3, by - 13.0)
    sh_ = (lean, by - 23.0)
    # legs: iron greaves
    for i, (fx_, lft) in enumerate(legs):
        layer = f.u if i == 0 else f.b
        knee = (hip[0] + fx_ * 0.6, hip[1] + 6.5 - lft * 0.5 + crouch * 0.5)
        tube(layer, [(hip[0] + (-2.0 if i == 0 else 2.0), hip[1]), knee, (fx_, -1.0 - lft)], [2.0, 1.8, 1.7],
             "msS" if i == 0 else "sSU")
        layer.put(*P(knee[0] + 1, knee[1]), "a")
        for xx in (-2, -1, 0, 1, 2): layer.put(*P(fx_ + xx, -lft), "k")
    # back arm and the flail chain to the censer
    tube(f.u, [(sh_[0] - 3.5, sh_[1] + 2.0), ((sh_[0] - 3.5 + hand_b[0]) / 2 - 1, (sh_[1] + 2 + hand_b[1]) / 2 + 1), hand_b],
         [1.8, 1.6, 1.5], "Kmms")
    pts = line_px(*P(*hand_b), *P(*ball))
    for k, (x, y) in enumerate(pts):
        f.n.put(x, y, "s" if k % 2 else "S")
    censer(f, ball[0], ball[1], phase=phase, blaze=blaze, layer="u")
    # tabard and torso
    poly(f.b, [(hip[0] - 4.5, hip[1] - 1), (hip[0] + 4.5, hip[1] - 1), (hip[0] + 4.0, hip[1] + 5), (hip[0] - 4.0, hip[1] + 5)], "a",
         shade=lambda x, y: "P" if (x + y) % 4 == 0 else ("a" if x < hip[0] + 1 else "P"))
    ell(f.b, sh_[0], sh_[1] + 5.5, 6.0, 6.5, "msSU", bias=0.05)
    ell(f.b, sh_[0] + 0.5, sh_[1] + 4.0, 4.6, 4.0, "sSUu", bias=0.1)
    for k in range(5): f.b.put(*P(sh_[0] + 1.0, sh_[1] + 2 + k), "a")          # rust keel
    for x in range(int(hip[0] - 5), int(hip[0] + 6)): f.b.put(x, int(hip[1] - 1), "a" if x % 3 else "e")
    for sx in (-1, 1):                                                          # pauldrons
        ell(f.b if sx > 0 else f.u, sh_[0] + sx * 5.5, sh_[1] + 1.0, 3.2, 2.4, RUST, bias=0.2)
    # great-helm: iron, rust band, the Knight's red visor slit, three candles
    hx, hy = sh_[0] + 1.0, sh_[1] - 4.0
    ell(f.b, hx, hy, 3.6, 4.0, "sSUu", bias=0.15)
    for k in range(-3, 4): f.b.put(*P(hx + k, hy + 2.5), "a")
    for k in range(0, 4): f.b.put(*P(hx + k, hy), "K")
    if visor == "lit":
        for k in (1, 2, 3): f.g.put(*P(hx + k, hy), "R")
    elif visor == "flare":
        for k in (0, 1, 2, 3): f.g.put(*P(hx + k, hy), "Y" if k in (1, 2) else "R")
        f.g.put(*P(hx + 4, hy), "R")
    for k, cxo in enumerate((-2, 0, 2)):
        x, y = P(hx + cxo, hy - 4.0 + abs(cxo) * 0.5)
        f.b.put(x, y, "W"); f.b.put(x, y - 1, "X")
        if crown: flame(f.g, x, y - 1, size=crown if k == 1 else max(1, crown - 1), phase=phase + k)
        else: f.g.put(x, y - 2, "s")
    # tower shield on the front arm
    sx0, sy0 = sh_[0] + 6.0 + shield[0], sh_[1] + 1.0 + shield[1]
    tube(f.b, [(sh_[0] + 3.5, sh_[1] + 2.0), (sx0 - 1.0, sy0 + 6.0)], [1.8, 1.6], IRON_L)
    W_, H_ = 8.0, 19.0
    def shade(x, y):
        u = (x - sx0) / W_
        if abs(x - sx0) < 0.6 or abs(x - (sx0 + W_)) < 0.9 or abs(y - sy0) < 0.6 or abs(y - (sy0 + H_)) < 0.9: return "a" if (x + y) % 3 else "P"
        return "U" if u < 0.25 else ("S" if u < 0.7 else "s")
    poly(f.b, [(sx0, sy0), (sx0 + W_, sy0 - 1.0), (sx0 + W_, sy0 + H_ - 3.0), (sx0 + W_ / 2, sy0 + H_ + 1.0), (sx0, sy0 + H_ - 3.0)],
         "s", shade=shade)
    # the wax seal sigil: a disc of wax with a burning mark
    gx, gy = sx0 + W_ / 2, sy0 + 7.0
    ell(f.b, gx, gy, 2.4, 2.4, WAX, bias=0.2)
    if glyph:
        f.g.put(*P(gx, gy - 1), "Y" if guard else "O"); f.g.put(*P(gx, gy), "y" if guard else "Y"); f.g.put(*P(gx, gy + 1), "O")
        f.g.put(*P(gx - 1, gy), "o"); f.g.put(*P(gx + 1, gy), "o")
    if guard:
        for k in range(4 + guard * 2):
            a = math.radians(-90 + k * (360 / (4 + guard * 2)) + phase * 20)
            f.g.put(*P(gx + (3.6 + guard) * math.cos(a), gy + (3.6 + guard) * math.sin(a)), "Y" if k % 2 else "O")
    if smash:
        for k in range(7):
            a = math.radians(-180 + k * 30)
            f.g.put(*P(ball[0] + 4.5 * math.cos(a), ball[1] + 2.0 * math.sin(a) - 1), "Y" if k % 2 else "O")
    return f.done()


def build_warden(out):
    idle = [warden(dy=[0, 0.3, 0.5, 0.3][i], ball=(-12.0, -14.0 + [0, 0.5, 1, 0.5][i]), phase=i) for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(warden(dy=-abs(math.sin(t)) * 0.8, lean=1.0, legs=((-3 + 2.5 * math.sin(t), max(0, math.cos(t)) * 1.5),
                                                                       (3 - 2.5 * math.sin(t), max(0, -math.cos(t)) * 1.5)),
                          ball=(-13.0 - math.sin(t), -13.0 + math.cos(t)), phase=i))
    flail = [warden(ball=(-15.0, -10.0), hand_b=(-8.0, -14.0), lean=-1, phase=0),
             warden(ball=(-14.0, -30.0), hand_b=(-5.0, -22.0), lean=-1.5, phase=1, blaze=2),
             warden(ball=(-2.0, -40.0), hand_b=(-1.0, -27.0), lean=-1, phase=2, blaze=2, visor="flare"),
             warden(ball=(14.0, -30.0), hand_b=(4.0, -24.0), lean=1.5, phase=3, blaze=2, visor="flare"),
             warden(ball=(19.0, -3.0), hand_b=(7.0, -17.0), lean=3, phase=0, blaze=2, visor="flare", smash=1, crouch=1),
             warden(ball=(19.0, -3.0), hand_b=(7.0, -16.0), lean=2.5, phase=1, blaze=1, crouch=1),
             warden(ball=(6.0, -4.0), hand_b=(0.0, -15.0), lean=1, phase=2),
             warden(ball=(-10.0, -10.0), hand_b=(-6.0, -15.0), phase=3)]
    bulwark = [warden(shield=(1.0, 0.0), crouch=0.5, phase=0),
               warden(shield=(2.0, 1.0), crouch=1.5, lean=1, phase=1, guard=1, visor="flare"),
               warden(shield=(2.0, 2.0), crouch=2.0, lean=1.5, phase=2, guard=1),
               warden(shield=(2.0, 2.0), crouch=2.0, lean=1.5, phase=3, guard=2),
               warden(shield=(2.0, 2.0), crouch=2.0, lean=1.5, phase=0, guard=1),
               warden(shield=(2.0, 2.0), crouch=2.0, lean=1.5, phase=1, guard=3, visor="flare"),
               warden(shield=(6.0, 0.0), crouch=0.5, lean=3.5, phase=2, guard=3, visor="flare"),
               warden(shield=(1.0, 0.0), phase=3)]
    death = [warden(visor="flare", shield=(1, 2), lean=-2, crown=2),
             warden(crouch=4, visor="off", crown=0, blaze=0, glyph=0, shield=(2, 6), ball=(-13.0, -2.0), hand_b=(-8.0, -9.0)),
             melt(warden(crouch=6, visor="off", crown=0, blaze=0, glyph=0, shield=(3, 8), ball=(-13.0, -2.0), hand_b=(-8.0, -8.0)), 0.35, list("kmsS")),
             melt(warden(crouch=7, visor="off", crown=0, blaze=0, glyph=0, shield=(4, 9), ball=(-13.0, -2.0), hand_b=(-8.0, -6.0)), 0.6, list("kmsS"))]
    knock = warden(lean=-3, shield=(-1, -2), ball=(-16.0, -20.0), hand_b=(-9.0, -20.0), visor="flare", crown=2)
    anims = [("Idle", idle, [0.2] * 4), ("Run", run, [0.1] * 6),
             ("Flail", flail, [0.12, 0.12, 0.1, 0.05, 0.06, 0.12, 0.1, 0.12]),
             ("Bulwark", bulwark, [0.1, 0.1, 0.42, 0.42, 0.42, 0.1, 0.08, 0.14])] + tail(idle[0], death, [0.12, 0.14, 0.16, 0.3], knock)
    sheet("VhPyreWarden", anims, out)


# ====================================================================================== TALLOW RENDERER (T3, Chandler)
def renderer(dy=0.0, lean=0.0, ladle=(14.0, -12.0), ladle_a=30.0, hook_hand=(-2.0, -14.0), hook=True, chain_to=None, phase=0,
             eye="lit", lit=True, boil=1, legs=((-3, 0), (3, 0)), squash=1.0, splash=0, dark=False):
    """Tallow Renderer ~36 x 34: the Chandler grown into a hunched rendering-man - the Chandler's tallow body, leather
    apron and guttering candle head with red eyes, a great black iron cauldron of molten fat strapped to its back (the
    Chandler's bucket grown huge), a long iron ladle in front and a meat hook on a chain at its hip."""
    f = Fr()
    hip = (lean * 0.2, dy - 10.0 * squash)
    sh_ = (lean + 2.0, dy - 19.0 * squash)
    for i, (fx_, lft) in enumerate(legs):
        layer = f.u if i == 0 else f.b
        tube(layer, [(hip[0] + (-2.2 if i == 0 else 2.2), hip[1]), (fx_ + 0.5, -1.0 - lft)], [2.4, 2.0], WAX if i else "ghwW")
        for xx in (-1, 0, 1, 2): layer.put(*P(fx_ + xx, -lft), "k")
    # the cauldron on its back
    cx, cy = sh_[0] - 9.0, sh_[1] + 1.0
    ell(f.u, cx, cy, 8.0, 6.5, IRON, bias=0.1)
    for x in range(int(cx - 8), int(cx + 9)): f.u.put(x, int(cy + 2), "a" if x % 2 else "P")          # rust hoop
    for x in range(int(cx - 7), int(cx + 8)):                                                         # rim + molten fat
        f.u.put(x, int(cy - 6), "S" if x % 3 else "s")
        if lit or boil:
            f.g.put(x, int(cy - 7), "Y" if (x + phase) % 4 == 0 else "O")
            if boil > 1 and (x + phase) % 3 == 0: f.g.put(x, int(cy - 8), "o")
    for k in range(boil + 1):                                                                         # steam
        sx_ = cx - 4 + k * 4 + (phase % 2)
        f.n.put(*P(sx_, cy - 9 - k % 2), "S"); f.n.put(*P(sx_ + 1, cy - 11), "s")
    f.g.put(*P(cx + 7, cy - 5), "O"); f.g.put(*P(cx + 7, cy - 4), "o")                              # a drip over the rim
    line(f.u, sh_[0] - 3, sh_[1] - 1, cx + 2, cy + 4, "t")                                            # strap
    # body: hunched tallow torso, leather apron
    ell(f.b, sh_[0], sh_[1] + 5.0, 6.0, 6.5, WAX if not dark else "ghwW", bias=0.05)
    poly(f.b, [(hip[0] - 1.0, hip[1] - 6), (hip[0] + 6.5, hip[1] - 5), (hip[0] + 6.0, hip[1] + 4), (hip[0] - 0.5, hip[1] + 4)], "t",
         shade=lambda x, y: "T" if x < hip[0] + 2 else "t")
    f.b.put(*P(hip[0] + 2.5, hip[1] - 2), "e")
    # the hook on its chain, at the hip / in the hand
    if hook:
        hx_, hy_ = hook_hand
        tube(f.u, [(sh_[0] - 3.0, sh_[1] + 2.0), (hx_, hy_)], [1.8, 1.6], "ghwW")
        line(f.u, hx_, hy_, hx_ + 1, hy_ + 4, ["s", "S"])
        f.u.put(*P(hx_ + 1, hy_ + 5), "S"); f.u.put(*P(hx_ + 2, hy_ + 5), "S"); f.u.put(*P(hx_ + 3, hy_ + 4), "s")
    elif chain_to:
        hx_, hy_ = hook_hand
        tube(f.b, [(sh_[0] - 1.0, sh_[1] + 2.0), (hx_, hy_)], [1.8, 1.6], WAX)
        for k, (x, y) in enumerate(line_px(*P(hx_, hy_), *P(*chain_to))):
            f.n.put(x, y, "S" if k % 2 else "s")
    # candle head (the Chandler's) with its red eyes
    hx, hy = sh_[0] + 3.5 + lean * 0.3, sh_[1] - 2.5
    ell(f.b, hx, hy, 2.8, 3.0, WAX, bias=0.2)
    for d in range(3): f.b.put(*P(hx - 2.8, hy + 1 + d), "W" if d < 2 else "w")
    f.b.put(*P(hx + 0.5, hy - 3.3), "k")
    if lit: flame(f.g, *P(hx + 0.5, hy - 3.3), size=2 if eye == "hot" else 1, phase=phase)
    else: f.g.put(*P(hx + 0.5, hy - 4.5), "s")
    if eye in ("lit", "hot"):
        f.g.put(*P(hx + 1.0, hy), "R" if eye == "lit" else "Y"); f.g.put(*P(hx + 2.4, hy), "R")
    # front arm + the ladle
    tube(f.b, [(sh_[0] + 3.0, sh_[1] + 3.0), ((sh_[0] + 3 + ladle[0]) / 2, (sh_[1] + 3 + ladle[1]) / 2 + 2), ladle], [1.9, 1.7, 1.5], WAX)
    a = math.radians(ladle_a)
    bx_, by_ = ladle[0] + 7.0 * math.cos(a), ladle[1] + 7.0 * math.sin(a)
    tx_, ty_ = ladle[0] - 3.0 * math.cos(a), ladle[1] - 3.0 * math.sin(a)
    line(f.b, tx_, ty_, bx_, by_, ["m", "s"])
    ell(f.b, bx_ + 1.0 * math.cos(a), by_ + 1.0 * math.sin(a) + 0.5, 2.0, 1.6, IRON, bias=0.2)
    if splash != 1: f.g.put(*P(bx_ + 1.0 * math.cos(a), by_ + 1.0 * math.sin(a)), "O")
    if splash:
        rnd = random.Random(splash)
        for k in range(10):
            x = bx_ + 2 + rnd.uniform(0, 7) * splash
            y = by_ - rnd.uniform(-3, 4) * splash * 0.6
            f.g.put(*P(x, y), rnd.choice(["Y", "O", "O", "o", "W"]))
    return f.done(), (bx_, by_)


def build_renderer(out):
    R_ = lambda **k: renderer(**k)[0]
    idle = [R_(dy=[0, 0.3, 0.5, 0.3][i], phase=i, boil=1 + (i % 2), ladle=(14.0, -12.0 + [0, 0.3, 0.5, 0.3][i])) for i in range(4)]
    run = []
    for i in range(6):
        t = i / 6.0 * 2 * math.pi
        run.append(R_(dy=-abs(math.sin(t)) * 0.8, lean=1.0, phase=i, legs=((-3 + 2.5 * math.sin(t), max(0, math.cos(t)) * 1.5),
                                                                          (3 - 2.5 * math.sin(t), max(0, -math.cos(t)) * 1.5))))
    ladle = []
    for k, kw in enumerate((dict(ladle=(4.0, -20.0), ladle_a=-150.0, lean=-1), dict(ladle=(2.0, -26.0), ladle_a=-120.0, lean=-1.5, boil=2),
                            dict(ladle=(10.0, -24.0), ladle_a=-40.0, lean=1, eye="hot"),
                            dict(ladle=(15.0, -15.0), ladle_a=10.0, lean=3, eye="hot", splash=1),
                            dict(ladle=(15.0, -14.0), ladle_a=20.0, lean=2.5, splash=2), dict(ladle=(14.0, -12.0), ladle_a=30.0))):
        spr, b = renderer(phase=k, **kw); ladle.append(spr); mark("VhRenderer", "Ladle", k, b)
    hookf = []
    for k, kw in enumerate((dict(hook_hand=(-5.0, -16.0), lean=-1), dict(hook_hand=(-8.0, -22.0), lean=-2, eye="hot"),
                            dict(hook_hand=(-4.0, -26.0), lean=-1, eye="hot"),
                            dict(hook=False, hook_hand=(12.0, -18.0), chain_to=(22.0, -17.0), lean=3, eye="hot"),
                            dict(hook=False, hook_hand=(12.0, -17.0), chain_to=(26.0, -16.0), lean=3),
                            dict(hook=False, hook_hand=(10.0, -15.0), chain_to=(20.0, -12.0), lean=2),
                            dict(hook_hand=(-2.0, -14.0)))):
        spr, b = renderer(phase=k, **kw); hookf.append(spr)
        if "chain_to" in kw: mark("VhRenderer", "Hook", k, kw["hook_hand"])
    death = [R_(eye="hot", lean=-2, boil=2), R_(squash=0.8, eye="off", lit=False, boil=0, dark=True),
             melt(R_(squash=0.65, eye="off", lit=False, boil=0, dark=True), 0.4, list("ghwW")),
             melt(R_(squash=0.55, eye="off", lit=False, boil=0, dark=True), 0.72, list("ghwW"))]
    knock = R_(lean=-3, eye="hot", boil=2, ladle=(10.0, -20.0), ladle_a=-60.0)
    anims = [("Idle", idle, [0.2] * 4), ("Run", run, [0.1] * 6),
             ("Ladle", ladle, [0.12, 0.12, 0.06, 0.06, 0.12, 0.14]),
             ("Hook", hookf, [0.1, 0.12, 0.1, 0.05, 0.25, 0.12, 0.14])] + tail(idle[0], death, [0.12, 0.14, 0.16, 0.3], knock)
    sheet("VhRenderer", anims, out)


# ====================================================================================== WICK HAG (T3, Chandler)
def hag(dy=0.0, lean=0.0, hand_f=(6.0, -18.0), hand_b=(-5.0, -16.0), phase=0, eye="lit", lit=True, crown=1, hem=0, bundle=True,
        cast=0, flying=0, squash=1.0, dark=False):
    """Wick Hag ~24 x 38: the Chandler withered into a crone - grey tallow skin, a crown of seven thin candles burning
    in a mane of black wick-hair (the Chandler's candle head multiplied), its red eyes, a long soot-rag gown, bony
    fingers, and a bundle of candles held to her chest."""
    f = Fr()
    top = dy - 25.5 * squash
    sh_ = (lean * 0.8, top + 2.0)
    # gown: a long ragged bell of soot rags
    hl, hr = -7.0 - hem * 0.5, 6.0
    def gshade(x, y):
        t = (y - sh_[1]) / max(1.0, -sh_[1])
        if int(round(x + t * 2)) % 4 == 0 and t > 0.25: return "m"
        return "S" if x < sh_[0] - 2 + t * -2 else ("s" if x < sh_[0] + 2 else "m")
    poly(f.b, [(sh_[0] - 3.5, sh_[1]), (sh_[0] + 3.5, sh_[1]), (hr, -1.0), (hl, -1.0)], "s", shade=gshade)
    for x in range(int(hl), int(hr) + 1):
        n = 1 + ((x * 7 + hem) % 3 == 0)
        for d in range(n): f.b.put(x, d, "m") if d < 1 else None
    # wick-hair: long black strands falling from the crown down the back
    hx, hy = sh_[0] + 2.0 + lean * 0.4, top - 2.5
    for k in range(6):
        x0 = hx - 2.5 + k * 0.8
        ln = 9 + (k * 5 + hem) % 5 + k
        line(f.u, x0, hy - 1, x0 - 2.5 - k * 0.4 - hem * 0.2, hy + ln, "K" if k % 2 else "k")
    # back arm, holding the candle bundle
    tube(f.u, [(sh_[0] - 2.5, sh_[1] + 1.5), ((sh_[0] - 2.5 + hand_b[0]) / 2 - 1, (sh_[1] + hand_b[1]) / 2 + 2), hand_b], [1.2, 1.0, 0.9], HAG)
    if bundle:
        for k in range(4):
            x, y = P(hand_b[0] + 1 + k, hand_b[1] + 1 - (k % 2))
            f.b.put(x, y, "W"); f.b.put(x, y - 1, "X"); f.b.put(x, y - 2, "W")
            if lit and k % 2: f.g.put(x, y - 3, "O")
        f.b.put(*P(hand_b[0] + 2, hand_b[1] + 1), "a")
    # head: a long grey tallow face, hooked nose, red eyes
    ell(f.b, hx, hy, 2.6, 3.0, HAG, bias=0.2)
    f.b.put(*P(hx + 2.8, hy + 0.5), "vhg1"); f.b.put(*P(hx + 3.4, hy + 1.2), "vhg0")                # the nose
    f.b.put(*P(hx + 1.8, hy + 2.0), "K")                                                            # the mouth
    for d in range(3): f.b.put(*P(hx + 0.5 + d % 2, hy + 3 + d), "W" if d < 2 else "w")             # wax tears
    if eye in ("lit", "hot"):
        f.g.put(*P(hx + 1.2, hy - 0.5), "R" if eye == "lit" else "Y"); f.g.put(*P(hx + 2.4, hy - 0.5), "R")
    # the crown of seven thin candles
    for k in range(7):
        a = math.radians(-160 + k * 23)
        x = hx - 0.2 + 3.2 * math.cos(a)
        y = hy - 1.0 + 3.2 * math.sin(a)
        h = 3 + (k % 3)
        for d in range(h): f.b.put(*P(x, y - d), "W" if d < h - 1 else "X")
        if lit and crown: flame(f.g, *P(x, y - h + 1), size=crown if k % 3 == 1 else 0 if crown == 1 else 1, phase=phase + k)
        elif not lit: f.g.put(*P(x, y - h), "s")
    # front arm: long and bony, fingers splayed
    tube(f.b, [(sh_[0] + 2.0, sh_[1] + 1.5), ((sh_[0] + 2.0 + hand_f[0]) / 2 + 0.5, (sh_[1] + hand_f[1]) / 2 + 1.5), hand_f], [1.2, 1.0, 0.9], HAG)
    for k in range(3):
        a = math.radians(-50 + k * 35)
        line(f.b, hand_f[0], hand_f[1], hand_f[0] + 2.2 * math.cos(a), hand_f[1] + 2.2 * math.sin(a), "vhg2")
    if cast:
        for k in range(3 + cast * 2):
            a = math.radians(-60 + k * 30)
            f.g.put(*P(hand_f[0] + (2.5 + cast) * math.cos(a), hand_f[1] + (2.5 + cast) * math.sin(a)), "Y" if k % 2 else "O")
    if flying:
        for k in range(4):
            x, y = P(-6 + k * 4 + flying * (k - 1.5) * 2, top - 6 - flying * 3 - (k % 2) * 3)
            f.g.put(x, y, "W"); f.g.put(x, y + 1, "w"); f.g.put(x, y - 1, "O"); f.g.put(x, y - 2, "o")
    return f.done(), hand_f


def build_hag(out):
    H = lambda **k: hag(**k)[0]
    idle = [H(dy=[0, -0.3, -0.5, -0.3][i], hem=i, phase=i, hand_f=(6.0, -18.0 + [0, -0.3, -0.5, -0.3][i])) for i in range(4)]
    run = [H(dy=[0, -0.5, -1, -0.5, 0, -0.3][i], lean=1.2, hem=i, phase=i) for i in range(6)]
    hexf = []
    for k, kw in enumerate((dict(hand_f=(3.0, -22.0), lean=-0.5), dict(hand_f=(2.0, -27.0), lean=-1, eye="hot", cast=1),
                            dict(hand_f=(8.0, -24.0), lean=0.5, eye="hot", cast=2), dict(hand_f=(11.0, -20.0), lean=1.5, eye="hot", cast=3),
                            dict(hand_f=(10.0, -19.0), lean=1.0, cast=1), dict(hand_f=(6.0, -18.0)))):
        spr, hnd = hag(phase=k, hem=k, **kw); hexf.append(spr); mark("VhWickHag", "Hex", k, hnd)
    scatter = [H(hand_b=(-6.0, -20.0), hand_f=(4.0, -21.0), phase=0), H(hand_b=(-5.0, -26.0), hand_f=(4.0, -27.0), phase=1, eye="hot", crown=2),
               H(hand_b=(-3.0, -31.0), hand_f=(3.0, -31.0), phase=2, eye="hot", crown=2),
               H(hand_b=(-6.0, -30.0), hand_f=(7.0, -30.0), phase=3, eye="hot", crown=2, bundle=False, flying=1),
               H(hand_b=(-7.0, -24.0), hand_f=(8.0, -24.0), phase=0, bundle=False, flying=2),
               H(hand_b=(-5.0, -18.0), hand_f=(6.0, -19.0), phase=1, bundle=False),
               H(phase=2)]
    death = [H(eye="hot", crown=2, lean=-1.5, hand_f=(6.0, -26.0)), H(squash=0.8, eye="off", lit=False, dark=True, hand_f=(6.0, -12.0)),
             melt(H(squash=0.6, eye="off", lit=False, dark=True, hand_f=(5.0, -8.0)), 0.4, list("msSS")),
             melt(H(squash=0.5, eye="off", lit=False, dark=True, hand_f=(5.0, -6.0)), 0.75, list("msSS"))]
    knock = H(lean=-2, eye="hot", hand_f=(4.0, -26.0), hand_b=(-8.0, -22.0), hem=2)
    anims = [("Idle", idle, [0.2] * 4), ("Run", run, [0.1] * 6),
             ("Hex", hexf, [0.1, 0.12, 0.08, 0.06, 0.1, 0.12]),
             ("Scatter", scatter, [0.1, 0.12, 0.12, 0.06, 0.12, 0.12, 0.14])] + tail(idle[0], death, [0.12, 0.14, 0.16, 0.3], knock)
    sheet("VhWickHag", anims, out)


# ====================================================================================== VOTIVE RELIQUARY (T3, Candelabra)
def votive(f, x, y, phase=0, blaze=1):
    """A red glass votive cup with a flame in it."""
    x, y = P(x, y)
    f.b.put(x, y, "vhv1"); f.b.put(x + 1, y, "vhv0"); f.b.put(x, y - 1, "vhv2"); f.b.put(x + 1, y - 1, "vhv1")
    if blaze:
        f.g.put(x + (phase % 2), y - 2, "Y" if blaze > 1 else "O")
        if blaze > 1: f.g.put(x, y - 3, "O")


def reliquary(dy=0.0, sway=0.0, doors=0.0, phase=0, blaze=1, skull="calm", tear=0, roots=0.0, gather=0, burst=0, lit=True,
              squash=1.0, dark=False):
    """Votive Reliquary ~32 x 38: the Candelabra grown into a walking iron shrine - a gothic iron cabinet on the
    Candelabra's root-feet, its weeping skull behind a glass pane, tiers of red votive cups, a candle spire on the roof,
    and two iron doors hinged open like the Ash Moth wings it carried (ember eye-spots). doors 0..1 opens them wide."""
    f = Fr()
    base = dy
    bx = sway
    # root feet
    for k, (a1, ln) in enumerate(((150, 6), (120, 5), (60, 5), (30, 6))):
        a = math.radians(a1 + math.sin(roots * 2 * math.pi + k) * 12)
        line(f.u if k in (1, 2) else f.b, bx + (k - 1.5) * 2.5, base - 4.0, bx + (k - 1.5) * 2.5 + ln * math.cos(a), min(0.0, base - 4 + ln * math.sin(a) + 2), "k")
    # doors: moth-wing iron panels hinged at the sides
    top = base - 30.0 * squash
    for sgn, layer in ((-1, "u"), (1, "u")):
        ang = (-90 - sgn * (35 + doors * 40)) if sgn > 0 else (-90 + 35 + doors * 40) - 180 + 180
        ang = -90 + sgn * (40 + doors * 38)
        moth_wing(f, layer, (bx + sgn * 6.0, base - 18.0 * squash), 13.0 + doors * 2, ang, 0.55, "sSUuu", "k",
                  [(0.6, 0.0, True)], 41 + (sgn > 0), tatter=0.0)
    # the cabinet
    def cab(x, y):
        u = (x - (bx - 7)) / 14.0
        if abs(y - (base - 4)) < 0.6 or abs(y - (base - 12)) < 0.6 or abs(y - (base - 21)) < 0.6: return "A"
        return "u" if u < 0.14 else ("U" if u < 0.42 else ("S" if u < 0.8 else "s"))
    poly(f.b, [(bx - 7, base - 3.0), (bx + 7, base - 3.0), (bx + 7, top + 6.0), (bx, top), (bx - 7, top + 6.0)], "m", shade=cab)
    # brass edge
    for (x0, y0, x1, y1) in ((bx - 7, base - 3, bx - 7, top + 6), (bx - 7, top + 6, bx, top), (bx, top, bx + 7, top + 6)):
        line(f.b, x0, y0, x1, y1, "ewe")
    # the window: pale glass, the weeping skull inside
    wx, wy = bx, base - 16.0 * squash
    ell(f.b, wx, wy, 3.6, 4.2, ["vhv0", "s", "S", "U"] if not dark else "Kmms", bias=0.3)
    sk = [(-1, -2, "S"), (0, -2, "X"), (1, -2, "S"), (-2, -1, "S"), (-1, -1, "X"), (0, -1, "X"), (1, -1, "X"), (2, -1, "S"),
          (-2, 0, "S"), (-1, 0, "K"), (0, 0, "X"), (1, 0, "K"), (2, 0, "S"), (-1, 1, "X"), (0, 1, "W"), (1, 1, "X"),
          (-1, 2, "S"), (0, 2, "K" if skull == "wail" else "X"), (1, 2, "S")]
    for dx_, dy_, ch in sk: f.b.put(*P(wx + dx_, wy + dy_), ch)
    if skull == "blaze":
        f.g.put(*P(wx - 1, wy), "Y"); f.g.put(*P(wx + 1, wy), "Y")
    elif not dark:
        f.g.put(*P(wx - 1, wy), "R"); f.g.put(*P(wx + 1, wy), "r")
    if not dark:
        f.g.put(*P(wx + 1, wy + 1 + tear), "b"); f.g.put(*P(wx + 1, wy + 2 + tear), "B")          # the tear
    # votive tiers
    for row, yy in enumerate((base - 5.0, base - 13.0)):
        for k, xx in enumerate((-6, -3.5, 2.5, 5)):
            votive(f, bx + xx, yy * squash if row else yy, phase + k + row, blaze if lit else 0)
    for k, xx in enumerate((-5.5, 4.5)):
        votive(f, bx + xx, base - 22.0 * squash, phase + k, blaze if lit else 0)
    # the spire candle
    candle(f, bx - 0.5, top + 0.5, 3, phase=phase, size=2 if blaze > 1 else 1, lit=lit)
    if gather:
        rnd = random.Random(gather)
        for k in range(6):
            a = rnd.uniform(0, 2 * math.pi)
            r0 = 16 - gather * 3
            for j in range(3):
                r = r0 - j * 1.5
                f.g.put(*P(wx + r * math.cos(a + j * 0.15), wy + r * 0.7 * math.sin(a + j * 0.15)), "Y" if j == 0 else ("O" if j == 1 else "o"))
    if burst:
        for k in range(10):
            a = math.radians(k * 36 + 10)
            r = 6 + burst * 4
            f.g.put(*P(wx + r * math.cos(a), wy + r * 0.8 * math.sin(a)), "Y"); f.g.put(*P(wx + (r - 1.5) * math.cos(a), wy + (r - 1.5) * 0.8 * math.sin(a)), "O")
    return f.done(), (wx, wy)


def build_reliquary(out):
    Rq = lambda **k: reliquary(**k)[0]
    idle = [Rq(doors=[0, 0.08, 0.15, 0.08][i], phase=i, tear=i % 3 if i < 3 else 0, dy=[0, -0.3, -0.5, -0.3][i]) for i in range(4)]
    run = [Rq(sway=[0, 1, 1, 0, -1, -1][i], roots=i / 6.0, phase=i, dy=-abs(math.sin(i * math.pi / 3)) * 0.8, doors=0.1 * (i % 2)) for i in range(6)]
    volley = []
    for k, kw in enumerate((dict(doors=0.2), dict(doors=0.5, blaze=2, skull="wail"), dict(doors=0.8, blaze=2, skull="blaze"),
                            dict(doors=0.9, blaze=2, skull="blaze", burst=1), dict(doors=0.6, blaze=1), dict(doors=0.2))):
        spr, w = reliquary(phase=k, **kw); volley.append(spr); mark("VhReliquary", "Volley", k, w)
    gather = []
    for k, kw in enumerate((dict(doors=0.4), dict(doors=0.9, gather=1, skull="wail"), dict(doors=1.0, gather=2, skull="wail", blaze=2),
                            dict(doors=1.0, gather=3, skull="blaze", blaze=2), dict(doors=1.0, gather=4, skull="blaze", blaze=2),
                            dict(doors=0.9, skull="blaze", blaze=2, burst=1), dict(doors=0.7, skull="blaze", burst=2), dict(doors=0.2))):
        spr, w = reliquary(phase=k, **kw); gather.append(spr); mark("VhReliquary", "Gather", k, w)
    death = [Rq(doors=1.0, skull="wail", blaze=2), Rq(doors=0.3, squash=0.85, lit=False, skull="wail", dark=True),
             melt(Rq(doors=0.0, squash=0.7, lit=False, dark=True), 0.4, list("kmsS")), melt(Rq(doors=0.0, squash=0.6, lit=False, dark=True), 0.7, list("kmsS"))]
    knock = Rq(doors=0.7, sway=-2, skull="wail", blaze=2)
    anims = [("Idle", idle, [0.2] * 4), ("Run", run, [0.1] * 6),
             ("Volley", volley, [0.1, 0.12, 0.1, 0.06, 0.12, 0.14]),
             ("Gather", gather, [0.1, 0.1, 0.12, 0.12, 0.12, 0.06, 0.12, 0.14])] + tail(idle[0], death, [0.12, 0.14, 0.16, 0.3], knock)
    sheet("VhReliquary", anims, out)


# ====================================================================================== EFFECTS
FXB = {}   # sheet -> origin (x, y) in the cell, filled by fx()


def fx(name, anims, out, scale=8):
    V.fx_sheet(name, anims, out, scale=scale)
    FXB[name] = V.BUILT[name]["feet"]


def spr_of(f, outline=True):
    return f.done(outline=outline, clip=False)


def fx_worm_mound():
    """Telegraph under the hero: the floor heaves and cracks, embers glowing up through it (0.45 s)."""
    out = []
    for i in range(6):
        k = (i + 1) / 6.0
        f = Fr()
        w = 4 + 5 * k
        for xx in range(-int(w), int(w) + 1):
            h = int(round((1 - (xx / w) ** 2) * (0.5 + 2.0 * k)))
            for yy in range(h): f.b.put(xx, -yy, "t" if (xx + yy + i) % 3 else "k")
        rnd = random.Random(3)
        for c in range(5):
            a = rnd.uniform(0, 2 * math.pi)
            for j in range(int(1 + 4 * k)):
                f.g.put(*P(math.cos(a) * j * 1.3, 0.5 + math.sin(a) * j * 0.5), "O" if j < 2 and i > 2 else "o")
        rnd = random.Random(i)
        for _ in range(int(2 + 4 * k)):
            f.g.put(int(rnd.uniform(-w, w)), -int(rnd.uniform(2, 3 + 4 * k)), rnd.choice(["vhw2", "W", "h"]))
        out.append(spr_of(f))
    return out


def fx_worm_erupt():
    """A burst of beeswax spikes and floor shards thrown up where the Wickworm surfaces."""
    out = []
    spec = [(0.4, 0), (1.0, 1), (1.0, 2), (0.8, 3), (0.5, 3), (0.2, 4)]
    for i, (h, st) in enumerate(spec):
        f = Fr()
        for k, (sx, ln) in enumerate(((-8, 6), (-4, 10), (0, 13), (4, 9), (8, 6))):
            L = ln * h
            if L < 1: continue
            lean = sx * 0.15
            for j in range(int(L)):
                w = 1 if j > L * 0.5 else 2
                for dx in range(w):
                    f.b.put(int(round(sx + lean * j * 0.3)) + dx, -j, WORM[min(4, 1 + j * 3 // max(1, int(L)))] if dx == 0 else "vhw1")
            if st < 3: f.g.put(int(round(sx + lean * L * 0.3)), -int(L), "Y" if st == 1 else "O")
        rnd = random.Random(i + 9)
        for _ in range(8 if st < 3 else 4):
            a = rnd.uniform(-math.pi, 0)
            r = rnd.uniform(4, 9 + st * 3)
            f.g.put(*P(r * math.cos(a) * 1.2, r * math.sin(a) * 0.9), rnd.choice(["O", "o", "vhw3", "t"]))
        for xx in range(-9, 10): f.n.put(xx, 0, "k" if xx % 2 else "t")
        out.append(spr_of(f))
    return out


def droplet(k, body, core, size=2.0, tailc="o", flame_=True, n=4):
    out = []
    for i in range(n):
        f = Fr()
        ell(f.b, 0, 0, size + (i % 2) * 0.3, size * 0.85, body, bias=0.2)
        for t in range(3): f.n.put(int(-size - 1 - t), int(round(math.sin(i + t) * 0.6)), tailc if t < 2 else "s")
        f.g.put(0, 0, core[i % len(core)])
        if flame_: f.g.put(1 - i % 2, -int(size) - 1, "O"); f.g.put(0, -int(size) - 2 + i % 2, "o")
        out.append(spr_of(f))
    return out


def fx_wax_egg():
    """Tallow Sow egg: dropped (2), pulses glowing amber (4), splits with a spurt (3)."""
    out = []
    for i in range(9):
        f = Fr()
        if i < 2:
            ell(f.b, 0, -2.0 - (1 - i) * 3, 2.0, 2.4 - 0.4 * i, FAT, bias=0.25)
        elif i < 6:
            sw = [0.0, 0.3, 0.0, 0.4][i - 2]
            ell(f.b, 0, -2.2, 2.1 + sw, 2.4 + sw, FAT, bias=0.25)
            f.g.put(0, -2, "vhe2" if i % 2 else "vhe1"); f.g.put(-1, -3, "vhe1")
            f.b.put(-2, 0, "vhs1"); f.b.put(2, 0, "vhs1")
        else:
            k = i - 6
            for sgn in (-1, 1):
                ell(f.b, sgn * (1.2 + k), -1.6 + k * 0.4, 1.4, 1.8 - k * 0.3, FAT, bias=0.2, vmin=-0.2 if sgn else None)
            for j in range(2 + k * 2):
                f.g.put(int((j - k) * 0.8), -3 - j - k, "Y" if j == 0 else "O")
        out.append(spr_of(f))
    return out


def fx_censer_smash():
    """The censer hits the floor: a flat ring of embers, brass sparks thrown up, a lick of fire."""
    out = []
    for i in range(6):
        f = Fr()
        r = 3 + i * 2.2
        for k in range(18):
            a = k * 2 * math.pi / 18
            if i > 3 and k % 2: continue
            f.g.put(*P(r * math.cos(a), r * 0.35 * math.sin(a) - 1), ["y", "Y", "O", "O", "o", "o"][i] if k % 3 else ["Y", "O", "o", "o", "s", "s"][i])
        if i < 4:
            for j in range(4 - i):
                f.g.put(0, -2 - j * 2 - i, "Y" if j == 0 else "O")
        rnd = random.Random(i + 2)
        for _ in range(6 - i):
            a = rnd.uniform(-math.pi * 0.9, -math.pi * 0.1); d = rnd.uniform(3, 6 + i * 2)
            f.g.put(*P(d * math.cos(a), d * math.sin(a)), rnd.choice(["e", "Y", "O"]))
        out.append(spr_of(f, outline=False))
    return out


def fx_shield_bash():
    """A forward wall of searing light off the tower shield: a tall crescent pushed out to the right, the sigil's
    burning mark at its heart (centred on the spawn point at chest height)."""
    out = []
    for i in range(5):
        f = Fr()
        x0 = i * 3.0
        for y in range(-9, 10):
            t = abs(y) / 9.0
            x = x0 + 4 * (1 - t * t)
            if i == 4 and y % 2: continue
            f.g.put(*P(x, y), ["y", "Y", "Y", "O", "o"][i] if abs(y) < 7 else ["Y", "O", "O", "o", "o"][i])
            if i < 3: f.g.put(*P(x - 1, y), "O" if i < 2 else "o")
            if i < 2 and abs(y) < 5: f.g.put(*P(x - 2, y), "o")
        if i < 3:
            f.g.put(*P(x0 + 4, 0), "y"); f.g.put(*P(x0 + 4, -1), "Y"); f.g.put(*P(x0 + 4, 1), "Y")
        out.append(spr_of(f, outline=False))
    return out


def fx_ladle_splash():
    """A scalding fan of boiling tallow flung forward off the ladle (4 frames, a swipe)."""
    out = []
    rnd = random.Random(5)
    drops = [(rnd.uniform(-0.5, 0.5), rnd.uniform(0.4, 1.0)) for _ in range(16)]
    for i in range(4):
        f = Fr()
        for a, sp in drops:
            d = (3 + i * 4.0) * sp
            x, y = d * math.cos(a), d * math.sin(a) + i * i * 0.4
            ch = ["X", "W", "w", "h"][i] if sp < 0.7 else ["Y", "O", "O", "o"][i]
            f.b.put(*P(x, y), ch)
            if i < 2: f.b.put(*P(x - 1, y), "W" if sp < 0.7 else "O")
        out.append(spr_of(f, outline=i < 2))
    return out


def fx_render_hook():
    out = []
    for i in range(4):
        f = Fr()
        # hook: shank pointing forward, barb curling back underneath
        line(f.b, -2, 0, 2, 0, "S")
        for (x, y, ch) in ((3, 0, "S"), (4, 1, "s"), (4, 2, "s"), (3, 3, "S"), (2, 3, "s"), (1, 2, "u")):
            f.b.put(x, y, ch)
        for k in range(5):
            f.n.put(-3 - k, (k + i) % 2 - (1 if k > 2 else 0), "s" if (k + i) % 2 else "S")
        f.g.put(1, 2, "o" if i % 2 else "O")       # a smear of hot fat on the barb
        out.append(spr_of(f))
    return out


def fx_hex_flame():
    out = []
    for i in range(4):
        f = Fr()
        for k in range(6):
            w = 1 if k > 2 else 2
            for d in range(-w + 1, w):
                f.g.put(-k + (1 if k > 3 and i % 2 else 0), d + (0 if k < 4 else (i % 2) * (1 if k % 2 else -1)),
                        ["y", "Y", "Y", "O", "o", "s"][k] if d == 0 else ["Y", "O", "O", "o", "o", "s"][k])
        f.g.put(1, 0, "Y"); f.g.put(-6 - i % 2, -1, "s"); f.g.put(-7, 0 + i % 2, "S")
        out.append(spr_of(f, outline=False))
    return out


def hag_candle(f, h=5, lean=0, burn=1, phase=0):
    for d in range(h):
        f.b.put(int(round(lean * d / h)), -d, "W" if d < h - 1 else "X")
    tx = int(round(lean))
    f.b.put(tx, -h, "k")
    if burn:
        flame(f.g, tx, -h, size=burn, phase=phase)
    f.b.put(-1, 0, "w"); f.b.put(1, 0, "h")


def fx_hag_candle():
    land = []
    for i, (yy, lean) in enumerate(((-9, 2), (-3, 1), (0, 0))):
        f = Fr(); hag_candle(f, 5, lean, 1, i)
        land.append(Spr({(x, y + yy): v for (x, y), v in spr_of(f).px.items()}))
    burn = []
    for i in range(4):
        f = Fr(); hag_candle(f, 5, 0, 1, i)
        if i % 2: f.n.put(-2, 0, "h"); f.n.put(2, 0, "w")
        burn.append(spr_of(f))
    return land, burn


def fx_candle_flare():
    out = []
    for i in range(6):
        f = Fr()
        h = [6, 12, 15, 12, 7, 3][i]
        for j in range(h):
            w = 2 if j < h * 0.4 else 1
            for d in range(-w, w + 1):
                if abs(d) == w and (j + i) % 2: continue
                f.g.put(d + (1 if j > h * 0.6 and i % 2 else 0), -j, ("y" if j < 3 else "Y") if abs(d) < w else ("O" if j < h * 0.7 else "o"))
        if i >= 3:
            for k in range(i - 1):
                f.n.put(k - 2, -h - 1 - k, "s"); f.n.put(-k + 2, -h - 2 - k, "S")
        for xx in (-3, -2, 2, 3): f.n.put(xx, 0, "w" if i < 3 else "h")
        out.append(spr_of(f, outline=False))
    return out


def fx_votive_flame():
    out = []
    for i in range(4):
        f = Fr()
        ell(f.b, 0, 0, 1.6, 1.4, VOTIVE, bias=0.3)
        f.g.put(0, 0, "R")
        for k in range(1, 5):
            f.g.put(-k, (i + k) % 2 - 1 if k > 1 else 0, ["Y", "O", "o", "r"][k - 1])
        f.g.put(1, -1 - i % 2, "Y")
        out.append(spr_of(f))
    return out


def fx_flame_draw():
    out = []
    for i in range(4):
        f = Fr()
        for k in range(7):
            f.g.put(-k, int(round(math.sin(k * 0.9 + i) * 0.8)), ["y", "Y", "Y", "O", "O", "o", "o"][k])
        f.g.put(0, -1, "O"); f.g.put(0, 1, "O")
        out.append(spr_of(f, outline=False))
    return out


def fx_wyrm_fireball():
    out = []
    for i in range(4):
        f = Fr()
        a0 = i * 0.8
        for y in range(-4, 5):
            for x in range(-4, 5):
                d = math.hypot(x, y)
                if d > 4.2: continue
                sw = math.sin(math.atan2(y, x) * 3 + a0)
                ch = "y" if d < 1.3 else ("Y" if d < 2.4 else ("O" if d < 3.4 + sw * 0.4 else "o"))
                f.g.put(x, y, ch)
        for k in range(4):
            f.g.put(-5 - k, int(round(math.sin(k + i) * 1.5)), "O" if k < 2 else "o")
        f.g.put(-1, -1, "X")                                     # the wax core showing white-hot
        out.append(spr_of(f, outline=False))
    return out


def fx_fuse_barb():
    out = []
    for i in range(4):
        f = Fr()
        line(f.b, -3, 0, 2, 0, "W")
        f.b.put(3, 0, "X"); f.b.put(1, -1, "w"); f.b.put(1, 1, "w")
        line(f.b, -4, 0, -7, (i % 2) * 2 - 1, "K")
        f.g.put(-7 - i % 2, (i % 2) * 2 - 1, "Y"); f.g.put(-8, (i % 2) * 2 - 2, "O")
        out.append(spr_of(f))
    return out


def fx_fuse_mark():
    """A coil of lit fuse hovering over the marked hero: the spark eats along it (loop of 6)."""
    out = []
    pts = [(int(round(4 * math.cos(t * 0.5))), int(round(-2 - t * 0.6 + 1.5 * math.sin(t * 0.5)))) for t in range(12)]
    for i in range(6):
        f = Fr()
        sx, sy = pts[(i * 2) % len(pts)]
        for k, (x, y) in enumerate(pts):
            if k < (i * 2) % len(pts): continue                  # the burnt part is gone
            f.b.put(x, y, "i" if k % 2 else "h")
        f.g.put(sx, sy, "y"); f.g.put(sx, sy - 1, "Y")
        for k in range(3):
            a = i * 1.3 + k * 2.1
            f.g.put(*P(sx + 1.8 * math.cos(a), sy - 1 + 1.4 * math.sin(a)), "O" if k else "Y")
        out.append(spr_of(f, outline=False))
    return out


def fx_fuse_blast():
    out = []
    for i in range(8):
        f = Fr()
        r = [3, 6, 9, 11, 12, 12, 12, 12][i]
        for y in range(-r - 4, 2):
            for x in range(-r - 2, r + 3):
                d = math.hypot(x, (y + r * 0.45) * 1.25)
                if d > r: continue
                if i >= 4 and random.Random(x * 31 + y * 7 + i).random() < (i - 3) * 0.22: continue
                if i < 4:
                    ch = "y" if d < r * 0.35 else ("Y" if d < r * 0.6 else ("O" if d < r * 0.85 else "o"))
                else:
                    ch = "o" if d < r * 0.5 and i < 6 else ("s" if (x + y) % 2 else "S")
                if y > 0: continue
                f.g.put(x, y, ch)
        if 1 <= i <= 4:
            rnd = random.Random(i)
            for _ in range(10):
                a = rnd.uniform(-math.pi, 0); d = r + rnd.uniform(1, 4)
                f.g.put(*P(d * math.cos(a), d * math.sin(a) * 0.8), rnd.choice(["W", "w", "Y", "O"]))
        out.append(spr_of(f, outline=False))
    return out


def fx_grubling():
    out = []
    for i in range(4):
        f = Fr()
        for k in range(3):
            ell(f.b, -2.4 + k * 2.0, -1.4 - (0.5 if (k + i) % 2 else 0), 1.3, 1.1, FAT, bias=0.2)
        f.g.put(2, -2, "R")
        f.b.put(-1, -3 - (i % 2), "W"); f.g.put(-1, -4 - (i % 2), "O")
        out.append(spr_of(f))
    return out


def fx_grub_pop():
    out = []
    for i in range(5):
        f = Fr()
        rnd = random.Random(4)
        for k in range(12):
            a = rnd.uniform(-math.pi, 0); sp = rnd.uniform(0.5, 1.0)
            d = (1 + i * 2.2) * sp
            x, y = d * math.cos(a) * 1.3, d * math.sin(a) + i * i * 0.25
            if y > 0: y = 0
            f.g.put(*P(x, y), (["vhs3", "vhs2", "vhs2", "vhs1", "vhs1"][i]) if k % 3 else ["Y", "O", "O", "o", "s"][i])
        if i < 3:
            for j in range(3 - i): f.g.put(0, -1 - j, "Y" if j == 0 else "O")
        for xx in range(-2 - i, 3 + i): f.n.put(xx, 0, "vhs1" if xx % 2 else "vhs2")
        out.append(spr_of(f, outline=False))
    return out


def build_fx(out):
    fx("FxVhWormMound", [("Crack", fx_worm_mound(), [0.075] * 6)], out)
    fx("FxVhWormErupt", [("Erupt", fx_worm_erupt(), [0.05, 0.06, 0.08, 0.08, 0.1, 0.12])], out)
    fx("FxVhSowDrop", [("Fly", droplet(0, FAT, ["vhe2", "vhe1"], size=1.8, tailc="vhs2"), [0.08] * 4)], out)
    fx("FxVhWaxEgg", [("Life", fx_wax_egg(), [0.06, 0.1, 0.4, 0.4, 0.4, 0.4, 0.08, 0.08, 0.12])], out)
    fx("FxVhCenserSmash", [("Smash", fx_censer_smash(), [0.05, 0.06, 0.07, 0.08, 0.1, 0.12])], out)
    fx("FxVhShieldBash", [("Bash", fx_shield_bash(), [0.05, 0.05, 0.06, 0.08, 0.1])], out)
    fx("FxVhLadleSplash", [("Splash", fx_ladle_splash(), [0.07, 0.1, 0.12, 0.13])], out)
    fx("FxVhRenderHook", [("Fly", fx_render_hook(), [0.07] * 4)], out)
    fx("FxVhHexFlame", [("Fly", fx_hex_flame(), [0.08] * 4)], out)
    land, burn = fx_hag_candle()
    fx("FxVhHagCandle", [("Land", land, [0.06, 0.06, 0.1]), ("Burn", burn, [0.14] * 4)], out)
    fx("FxVhCandleFlare", [("Flare", fx_candle_flare(), [0.05, 0.06, 0.08, 0.08, 0.1, 0.12])], out)
    fx("FxVhVotiveFlame", [("Fly", fx_votive_flame(), [0.08] * 4)], out)
    fx("FxVhFlameDraw", [("Fly", fx_flame_draw(), [0.06] * 4)], out)
    fx("FxVhWyrmFireball", [("Fly", fx_wyrm_fireball(), [0.07] * 4)], out)
    fx("FxVhFuseBarb", [("Fly", fx_fuse_barb(), [0.07] * 4)], out)
    fx("FxVhFuseMark", [("Burn", fx_fuse_mark(), [0.3] * 6)], out)
    fx("FxVhFuseBlast", [("Blast", fx_fuse_blast(), [0.04, 0.05, 0.06, 0.06, 0.08, 0.08, 0.1, 0.12])], out)
    fx("FxVhGrubling", [("Crawl", fx_grubling(), [0.1] * 4)], out)
    fx("FxVhGrubPop", [("Pop", fx_grub_pop(), [0.05, 0.06, 0.08, 0.1, 0.12])], out)
    fx("FxVhTickSpurt", [("Fly", droplet(0, TICK, ["Y", "O"], size=1.6, tailc="O"), [0.07] * 4)], out)


# ====================================================================================== TIMING.md section
MARK0, MARK1 = "<!-- vhorrul_v10 begin -->", "<!-- vhorrul_v10 end -->"
NOTES = {
    "VhWickworm": ["Bite f3 (0.27 s): ModVhWormBite 11 x 9 box at (15, -4); the reared head strikes down to (17, -2), mandibles "
                   "to x 20; lunge 80 px/s f2-f4; Strike.Feet node 8 (the reared chest)",
                   "Burrow: f1 invulnerable, f2 collide off, f3 (0.24 s) VhWormMark: FxVhWormMound on the floor under the hero; "
                   "f6 (0.77 s) VhWormSurface: teleport there + FxVhWormErupt (damage f1-f4 of its clip, 22 x 10 floor box); f8 vulnerable"],
    "VhTallowSow": ["Spray f3 (0.32 s): 3 ModVhSowDrop at -14 / 0 / 14 deg from the mouth (10, -5)",
                    "Lay f4 (0.42 s): 3 ModVhWaxEgg at (-15, 0), (-9, +-9) (floor); each hatches after 2.04 s and spits a drop at the hero from 4 px up"],
    "VhPyreWarden": ["Flail f4 (0.39 s): ModVhCenserSmash on the floor at (19, 0) where the ball lands (26 x 10 box, live f0-f3)",
                     "Bulwark f2 (0.20 s) VhGuardOn (x4 resistance, up to 3 charges for 1.6 s); f6 (1.46 s) VhGuardBash: "
                     "ModVhShieldBash<charges> at (12, -14), attached, 18 x 20 box centred 8 px ahead"],
    "VhRenderer": ["Ladle f3 (0.30 s): ModVhLadleSplash (OrcSwipe clone) attached at (18, -13): the ladle bowl (22, -14) + the fan x 0..19",
                   "Hook f3 (0.32 s): ModVhRenderHook from the chain hand (12, -18) -> (14, -17), 210 px/s x 0.5 s"],
    "VhWickHag": ["Hex f3 (0.30 s): ModVhHexFlame from the fingertips (11, -20) -> (12, -20)",
                  "Scatter f4 (0.40 s): 4 ModVhHagCandle at the hero + (22, 0), (-22, 0), (4, 15), (-4, -15) (ClosestEnemy), staggered 0.06 s"],
    "VhReliquary": ["Volley f3 (0.32 s): 3 ModVhVotiveFlame at -12 / 0 / 12 deg from the window (0, -16) -> (3, -16)",
                    "Gather f1 (0.10 s) VhGather: burning pools within 90 px streak in (ModVhFlameDraw); f5 (0.56 s) VhGatherBurst: "
                    "2 + pools (max 8) votive flames in a ring from (0, -16)"],
    "VhCandleWyrm": ["Bite f3 (0.31 s): ModVhWyrmBite 12 x 12 at (16, -12), attached; head (19, -14)",
                     "Spit f3 (0.36 s): ModVhWyrmFireball from the mouth (14, -21) -> (15, -21); ricochets 3 s"],
    "VhFuseScorpion": ["Pinch f3 (0.27 s): ModVhScorpPinch 12 x 10 at (17, -8), claws reach x 21",
                       "Sting f4 (0.36 s): ModVhFuseBarb from the barb tip of f3 (16, -14) -> (17, -13)"],
    "VhBroodMother": ["Slam f3 (0.36 s): ModVhBroodSlam 18 x 12 at (15, -4), attached; head hits (15, -4)",
                      "Clutch f4 (0.44 s): 4 ModVhGrubling from the egg mound (-12, -3) at 110 / 150 / -150 / -110 deg, staggered 0.07 s"],
    "VhPyreTick": ["Bite f3 (0.27 s): ModVhTickBite 10 x 10 at (15, -10); head at (14, -10)",
                   "Bloat f4 (0.46 s) VhTickBurst: 6 ModVhTickSpurt in a ring from the feet (art drawn 10 px up)"],
}
FX_USE = {
    "FxVhWormMound": "Wickworm telegraph (Visual) on the floor under the hero",
    "FxVhWormErupt": "Wickworm surfacing: TimedHit (Troll shockwave clone) damage f1-f4, Strike.Ground 22 x 10",
    "FxVhSowDrop": "Tallow Sow drop (skelMage projectile clone), centred",
    "FxVhWaxEgg": "Tallow Sow egg (Inert), Life: drop 2, pulse 4, crack 3 = 2.04 s, then ModVhEggHatch",
    "FxVhCenserSmash": "Pyre Warden flail: TimedHit damage f0-f3, Strike.Ground 26 x 10",
    "FxVhShieldBash": "Pyre Warden Bulwark release: TimedHit (OrcSwipe clone) damage f0-f2, box 18 x 20 at (8, 0)",
    "FxVhLadleSplash": "Tallow Renderer ladle: GodArt.Swipe on an OrcSwipe clone (origin = ladle bowl)",
    "FxVhRenderHook": "Tallow Renderer hook (skelMage projectile clone + HookFx)",
    "FxVhHexFlame": "Wick Hag hex (skelMage projectile clone)",
    "FxVhHagCandle": "Wick Hag mine (Inert): Land 3 then Burn x14 (7 s); origin = the candle's foot",
    "FxVhCandleFlare": "Wick Hag mine flare: TimedHit damage f1-f4, Strike.Ground 12 x 10",
    "FxVhVotiveFlame": "Votive Reliquary flame (skelMage projectile clone)",
    "FxVhFlameDraw": "Votive Reliquary: a burning pool streaking in (no damage)",
    "FxVhWyrmFireball": "Candle Wyrm fireball (skelMage projectile clone, bounce 1, 9 x 9 collider)",
    "FxVhFuseBarb": "Fuse Scorpion barb (skelMage projectile clone)",
    "FxVhFuseMark": "Fuse Scorpion fuse over the hero (Visual, follows 17 px up), Burn 6 x 0.3 s",
    "FxVhFuseBlast": "Fuse Scorpion blast: TimedHit damage f1-f4, Strike.Ground 24 x 12",
    "FxVhGrubling": "Grub Mother grubling (PriestessRune clone, homing, 4 s); origin = its belly on the floor",
    "FxVhGrubPop": "grubling burst: TimedHit damage f0-f2, Strike.Ground 16 x 8, then a wax puddle",
    "FxVhTickSpurt": "Pyre Tick drop (webBall clone: hits feet), art at ArtAt (5, 14) = 10 px up; lands as a burning pool",
}


def write_timing(out):
    import json
    L = ["", MARK0, "## v0.10 unique tree (tools/sprites/vhorrul_v10.py)", "",
         "Ten new monsters at final size (no ArtScale). Feet = (cellW//2, cellH-2); points are relative to the feet, x right,",
         "y up NEGATIVE (code: offsetX = x, offsetY = -y). Frame indices 0-based; times are the event's start.", "",
         "| Sheet | Cell | Idle (w x h) | Anims (frames: durations) |", "|---|---|---|---|"]
    for name in BUILDERS:
        if name == "fx": continue
        jp = os.path.join(out, name + ".json")
        if not os.path.exists(jp): continue
        m = json.load(open(jp))
        b = BUILT.get(name) or {}
        idle = b.get("idle", ("?", "?"))
        an = "; ".join("%s %d: %s" % (a["name"], len(a["frames"]), ", ".join("%.3g" % d for d in a["durations"]))
                       for a in m["anims"] if a["name"] not in ("Dead", "Statue", "Knockback", "Portrait"))
        L.append("| %s | %d x %d | %s x %s | %s |" % (name, m["cellW"], m["cellH"], idle[0], idle[1], an))
    L += ["", "### Moves and spawn points", ""]
    for name, notes in NOTES.items():
        for n in notes: L.append("- %s: %s" % (name, n))
    L += ["", "### Effects (origin = the cell pixel Strike.ArtAt / Ground puts on the spawn point, y down)", "",
          "| Sheet | Cell | Origin | Anims | Use |", "|---|---|---|---|---|"]
    for name, use in FX_USE.items():
        jp = os.path.join(out, name + ".json")
        if not os.path.exists(jp): continue
        m = json.load(open(jp))
        org = FXB.get(name, ("?", "?"))
        an = "; ".join("%s %d: %s" % (a["name"], len(a["frames"]), ", ".join("%.3g" % d for d in a["durations"])) for a in m["anims"])
        L.append("| %s | %d x %d | (%s, %s) | %s | %s |" % (name, m["cellW"], m["cellH"], org[0], org[1], an, use))
    L += ["", "Lineage redraws (v0.10, one parent each): Tallow Colossus (Waxen Knight) has two swallowed sword hilts in its back",
          "instead of the Chandler's bucket (big_rigs.py); Grand Chandelier (Candelabra) has the Candelabra's weeping skull in an iron",
          "cage as its heart instead of the bucket; Ashen Seraph (Moth Matron) has her feathered antennae and ash trim instead of the",
          "Knight's rust; Lantern Wraith (Moth Matron) lost the Candelabra's tear and mantle candles (vhorrul_t3.py).", MARK1, ""]
    p = os.path.join(out, "TIMING.md")
    old = open(p).read() if os.path.exists(p) else ""
    if MARK0 in old:
        old = old[:old.index(MARK0)].rstrip("\n") + "\n" + old[old.index(MARK1) + len(MARK1):].lstrip("\n")
    open(p, "w").write(old.rstrip("\n") + "\n" + "\n".join(L))
    print("timing ->", p)

BUILDERS = {"VhWickworm": build_wickworm, "VhTallowSow": build_sow, "VhCandleWyrm": build_wyrm,
            "VhFuseScorpion": build_scorpion, "VhBroodMother": build_brood, "VhPyreTick": build_tick,
            "VhPyreWarden": build_warden, "VhRenderer": build_renderer, "VhWickHag": build_hag, "VhReliquary": build_reliquary,
            "fx": build_fx}


def build_all(out=DEFAULT_OUT, only=None):
    for k, fn in BUILDERS.items():
        if only and k not in only: continue
        fn(out)
    if not only: write_timing(out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        args = [a for a in args if a != sys.argv[sys.argv.index("--only") + 1]]
    build_all(args[0] if args else DEFAULT_OUT, only)
