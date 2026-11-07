"""v0.8 art pass: the effect sheets that replace vanilla / tinted / shared art in the Vhorrul, Bel'Mora and
Ossivar packs.

    python3 godsa_fx.py [--only Name,Name]

Writes each sheet to its god's art dir (art/out, art/out_belmora, art/out_ossivar):

  Vhorrul   FxVhKnightSlash   Slash 4    Waxen Knight Combo1/2 (was the vanilla OrcSwipe arc)
            FxVhKnightCleave  Upslash 4  Waxen Knight Combo3 (was OrcSwipe2 x1.25)
            FxVhMatronRake    Rake 4     Moth Matron claw (was OrcSwipe)
            FxVhColossusFist  Fist 4     Tallow Colossus Hammer (was OrcSwipe x1.4)
            FxVhSoulBurst     Play 11    Lantern Wraith orb burst + Soul Lantern item (was tinted skydropExplode)
            FxVhLanternBeam   Open 3, Loop 8, End 4   Lantern Wraith beam (was tinted DamageBeholderBeam + vanilla end)
            FxVhMoltenGlob    Fly 4      Chandler's burning glob (was the tinted FxWaxGlob)
            FxVhEmberMoth     Fly 4      Moth Matron's brood (was the Candelabra's FxEmber spark)
  Bel'Mora  FxBelPinch        Pinch 4    Barnacle Crab pinch (was aqua OrcSwipe)
            FxBelTrident      Thrust 4   Tide Matriarch thrust (was pink OrcSwipe)
            FxBelAnchorQuake  Ring 4     Bell Diver anchor quake (was the tinted troll shockwave)
            FxBelBrineGlob    Fly 4      brine glob (was the Siren's FxWaterBolt)
            FxBelBarnacle     Orbit 4, Break 4   Barnacle Crab shell plate (was Ossivar's bone plate + crumble)
  Ossivar   FxOssHowl         Ring 4     Marrow Hound howl (was the red troll shockwave)
            FxOssBonePlateBreak Play 4   plate shatter / halo-skull hit (was FxBonePile Crumble)

Every frame is drawn fresh from shaded primitives (crescent bands, rings, blobs) in the gods' own palettes, then
packed into a fixed cell whose ORIGIN pixel is listed in the TIMING sections (and used by Strike.ArtAt in code).
Coordinates: x right, y DOWN (negative = up), (0, 0) = the effect origin.
"""
import math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from rig import Canvas, line_px  # noqa: E402
from anim import Spr, PALETTE, pack, preview  # noqa: E402
import belmora_rigs  # noqa: E402,F401  (adds the Bel'Mora palette chars Z D d E Q z x f H j ...)

ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "art")
OUT = {"vh": os.path.join(ROOT, "out"), "bel": os.path.join(ROOT, "out_belmora"), "oss": os.path.join(ROOT, "out_ossivar")}
if os.environ.get("FX_TMP"):     # draft renders: everything into one scratch dir
    OUT = {k: os.environ["FX_TMP"] for k in OUT}
    os.makedirs(os.environ["FX_TMP"], exist_ok=True)
SWIPE_D = [0.1167, 0.1167, 0.1167, 0.0667]      # vanilla 1HandedSwordSwipe2 / Upslash: 4 frames, 0.42 s
RING_D = [0.0667] * 4                            # vanilla BigShockwaveFront: 4 frames, 0.27 s
BURST_D = [0.0667, 0.0667, 0.1, 0.1, 0.1333, 0.1333, 0.1333, 0.1667, 0.1, 0.1, 0.1]   # vanilla skydropExplode, 1.2 s
BUILT = {}


def P(x, y):
    return int(round(x)), int(round(y))


def pick(ramp, l):
    n = len(ramp)
    return ramp[max(0, min(n - 1, int((l + 1.0) * 0.5 * n)))]


def ell(c, cx, cy, rx, ry, ramp, bias=0.0, over=True):
    R = int(max(rx, ry)) + 2
    for y in range(int(cy - R), int(cy + R) + 2):
        for x in range(int(cx - R), int(cx + R) + 2):
            nu, nv = (x - cx) / max(rx, 0.5), (y - cy) / max(ry, 0.5)
            d = nu * nu + nv * nv
            if d > 1.0: continue
            l = 0.8 * (-(nu + nv) / 1.414) + 0.35 * (1 - d) - 0.12 + bias
            c.put(x, y, pick(ramp, l), over)


def line(c, x0, y0, x1, y1, ch, over=True):
    pts = line_px(*P(x0, y0), *P(x1, y1))
    for i, (x, y) in enumerate(pts):
        c.put(x, y, ch[min(len(ch) - 1, i * len(ch) // max(1, len(pts)))], over)
    return pts


def outline(c, ch, over=False):
    """1px outline round everything drawn so far."""
    px = dict(c.px)
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in px: c.put(x + dx, y + dy, ch, over)


def crescent(c, cx, cy, rx, ry, a0, a1, thick, cols, gap=0, seed=0, lead=0.5, over=True):
    """A swept band hugging the ellipse (cx, cy, rx, ry) between angles a0..a1 (deg, 0 = right, +90 = down).
    thick: max depth in px (tapers to both ends, fattest at `lead` along the sweep); cols: outer edge -> inner.
    gap > 0 breaks the band into dashes (every other `gap`-degree segment) for fading frames."""
    rnd = random.Random(seed)
    R = int(max(rx, ry) + thick) + 2
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            dx, dy = x - cx, y - cy
            ang = math.degrees(math.atan2(dy / ry, dx / rx))
            if not (a0 <= ang <= a1): continue
            t = (ang - a0) / max(1e-6, (a1 - a0))
            if gap and int((ang - a0) / gap) % 2 == 1 and rnd.random() < 0.85: continue
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            rb = math.hypot(rx * ca, ry * sa)
            depth = rb - math.hypot(dx, dy)
            prof = math.sin(math.pi * (t ** (math.log(0.5) / math.log(max(0.05, min(0.95, lead)))))) ** 0.8
            th = max(0.6, thick * prof)
            if depth < -0.5 or depth > th: continue
            k = int(max(0.0, depth) / max(th, 0.6) * len(cols))
            c.put(x, y, cols[min(len(cols) - 1, k)], over)


def ring(c, rx, ry, cy, front, back, gap=0, seed=0, width=1, chips=None):
    """A floor ring (ellipse) around (0, cy): the front half (y > cy) in `front`, the back half in `back`."""
    rnd = random.Random(seed)
    n = max(12, int((rx + ry) * 4))
    for k in range(n):
        a = 2 * math.pi * k / n
        if gap and (k // gap) % 3 == 0 and rnd.random() < 0.9: continue
        x, y = rx * math.cos(a), cy + ry * math.sin(a)
        f = math.sin(a) > -0.15
        cols = front if f else back
        for w in range(width):
            sh = 1.0 - w * 0.9 / max(1, rx)
            c.put(*P(x * sh, cy + (y - cy) * sh - (w * 0.4 if f else 0)), cols[min(w, len(cols) - 1)], over=(w == 0))


def blob(c, cx, cy, r, cols, noise=0.35, seed=0, ang_n=7, holes=0.0, sy=1.0):
    """A ragged radial blob (fire, smoke): cols from the core outward; angular noise makes tongues."""
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    R = int(r * (1 + noise)) + 2
    for y in range(int(cy - R), int(cy + R) + 1):
        for x in range(int(cx - R), int(cx + R) + 1):
            dx, dy = x - cx, (y - cy) / sy
            a = math.atan2(dy, dx)
            rr = r * (1 + noise * (0.5 * math.sin(ang_n * a + ph[0]) + 0.3 * math.sin((ang_n + 4) * a + ph[1])
                                   + 0.2 * math.sin(3 * a + ph[2])))
            d = math.hypot(dx, dy) / max(0.5, rr)
            if d > 1.0: continue
            if holes and rnd.random() < holes * d: continue
            c.put(x, y, cols[min(len(cols) - 1, int(d * len(cols)))])


def sheet(god, name, anims, cell=None, origin=None, scale=6):
    """Pack with a cell that just fits every frame (1 px margin); the origin pixel is reported for Strike.ArtAt."""
    allf = [f for a in anims for f in a[1] if f.px]
    for an, fr, du in anims:
        assert len(du) == len(fr), (name, an)
    x0 = min(f.bbox()[0] for f in allf) - 1; x1 = max(f.bbox()[2] for f in allf) + 1
    y0 = min(f.bbox()[1] for f in allf) - 1; y1 = max(f.bbox()[3] for f in allf) + 1
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    cw += cw % 2
    origin = (-x0, -y0)
    out = OUT[god]
    img, man = pack(name, anims, cw, ch, origin, out)
    preview(img, man, os.path.join(out, name + "_preview.png"), scale=scale)
    BUILT[name] = {"god": god, "cell": (cw, ch), "origin": origin, "anims": [(a, len(f), list(d)) for a, f, d in anims]}
    print("built %-20s cell %dx%d origin %s  %s" % (name, cw, ch, origin, ", ".join("%s:%d" % (a, len(f)) for a, f, d in anims)))


# =================================================================================== melee arcs
def knight_slash():
    """A guttering wax blade's arc: pale wax edge, ember heat on the inside, molten drips flung off the end."""
    out = []
    # f0: full crescent, the blade's edge (OrcSwipe capsule: x -3..19, y -8..10)
    c = Canvas()
    crescent(c, 1, 0, 16, 10, -75, 78, 4.2, "XXWwo", lead=0.45)
    crescent(c, 1, 0, 13, 7.5, -50, 60, 1.2, "O")
    c.put(13, -7, "y"); c.put(17, -1, "y"); c.put(16, 3, "X")
    for (x, y) in ((6, 10), (9, 9), (12, 8)): c.put(x, y + 1, "w")
    outline(c, "k")
    out.append(c.spr())
    # f1: the band has passed: its trailing half, thinner, drips leaving the bottom
    c = Canvas()
    crescent(c, 1, 0, 16, 10, -20, 85, 2.6, "XWwo", lead=0.75)
    crescent(c, 1, 0, 16, 10, -62, -20, 1.0, "w", gap=10, seed=2)
    for (x, y, ch) in ((4, 12, "W"), (8, 12, "w"), (12, 11, "O"), (15, 7, "o")): c.put(x, y, ch)
    outline(c, "k")
    out.append(c.spr())
    # f2: broken streaks, wax drops falling
    c = Canvas()
    crescent(c, 1, 0, 17, 11, 15, 88, 1.3, "Wh", gap=9, seed=3)
    for (x, y, ch) in ((3, 13, "w"), (7, 14, "W"), (11, 13, "h"), (14, 10, "o"), (16, 6, "h")): c.put(x, y, ch)
    out.append(c.spr())
    # f3: specks
    c = Canvas()
    for (x, y, ch) in ((4, 15, "h"), (8, 15, "w"), (12, 15, "h"), (17, 9, "g"), (15, 12, "g")): c.put(x, y, ch)
    out.append(c.spr())
    return out


def knight_cleave():
    """The overhead cleave: a tall wax crescent ending in a splash of molten wax at the bottom (it spills a puddle)."""
    out = []
    c = Canvas()
    crescent(c, -3, -1, 16, 16, -80, 82, 4.6, "XXWwwo", lead=0.6)
    crescent(c, -3, -1, 13, 13, -40, 70, 1.2, "O")
    c.put(9, -11, "y"); c.put(13, 0, "y")
    outline(c, "k")
    for (x, y, ch) in ((2, 15, "O"), (5, 14, "Y"), (8, 13, "O"), (0, 14, "o")): c.put(x, y, ch)
    out.append(c.spr())
    c = Canvas()
    crescent(c, -3, -1, 16, 16, -10, 88, 3.0, "XWwo", lead=0.8)
    crescent(c, -3, -1, 16, 16, -70, -10, 1.0, "w", gap=12, seed=5)
    outline(c, "k")
    for (x, y, ch) in ((-2, 15, "O"), (2, 13, "Y"), (6, 15, "O"), (9, 12, "o"), (4, 11, "O"), (11, 14, "o")): c.put(x, y, ch)
    out.append(c.spr())
    c = Canvas()
    crescent(c, -3, -1, 17, 17, 30, 88, 1.4, "Wh", gap=10, seed=6)
    for (x, y, ch) in ((-4, 15, "o"), (1, 12, "O"), (5, 14, "o"), (9, 11, "w"), (12, 15, "o"), (7, 9, "o")): c.put(x, y, ch)
    out.append(c.spr())
    c = Canvas()
    for (x, y, ch) in ((-5, 15, "g"), (0, 15, "a"), (5, 15, "o"), (10, 15, "g"), (13, 14, "h")): c.put(x, y, ch)
    out.append(c.spr())
    return out


def matron_rake():
    """Three claw rakes in ember and ash: bright cinder edges over dark ash streaks; ash flakes drift off."""
    out = []
    for i in range(4):
        c = Canvas()
        if i < 3:
            for j, r in enumerate((10.5, 14, 17.5)):
                a0 = [-62, -20, 20][i] + j * 4
                a1 = [55, 70, 80][i] + j * 3
                th = [2.2, 1.6, 1.0][i]
                cols = ["YOoK", "Ook", "ok"][i]
                crescent(c, 0, 0, r, r * 0.7, a0, a1, th, cols, gap=(0 if i == 0 else 8), seed=11 + j + i, lead=0.4)
            if i == 0:
                for (x, y) in ((10, -6), (16, -7), (19, -3)): c.put(x, y, "y")
        rnd = random.Random(40 + i)
        for k in range(4 + 2 * i):     # ash flakes
            x = rnd.uniform(4, 20); y = rnd.uniform(-8, 10) + i * 1.5
            c.put(*P(x, y), "ihgs"[min(3, i + (k % 2))])
        out.append(c.spr())
    return out


def colossus_fist():
    """A huge tallow fist's swing: a fat smear of pale wax with an impact burst at the knuckles, globs flung off."""
    out = []
    # OrcSwipe capsule x1.4, kept unscaled in code: x -4..27, y -12..15 around the spawn
    c = Canvas()
    crescent(c, 1, 1, 23, 13, -65, 62, 7.0, "XXWWwwh", lead=0.7)
    crescent(c, 1, 1, 18, 9, -35, 45, 1.5, "o")
    outline(c, "k")
    # knuckle impact star at the front
    for a in range(0, 360, 45):
        r = 6 if a % 90 == 0 else 4
        line(c, 22, 2, 22 + r * math.cos(math.radians(a)), 2 + r * math.sin(math.radians(a)), "yX")
    c.put(22, 2, "y")
    out.append(c.spr())
    c = Canvas()
    crescent(c, 1, 1, 23, 13, -10, 70, 4.5, "XWwh", lead=0.85)
    outline(c, "k")
    for k in range(10):   # impact ring
        a = 2 * math.pi * k / 10
        c.put(*P(22 + 7 * math.cos(a), 2 + 6 * math.sin(a)), "X" if k % 2 else "W")
    for (x, y) in ((27, -6), (29, 5), (16, 10)): ell(c, x, y, 1.6, 1.4, "wWX")
    out.append(c.spr())
    c = Canvas()
    crescent(c, 1, 1, 24, 14, 20, 75, 1.6, "Wh", gap=10, seed=9)
    for k in range(10):
        a = 2 * math.pi * k / 10
        if k % 3: c.put(*P(22 + 9 * math.cos(a), 2 + 7.5 * math.sin(a)), "w")
    for (x, y) in ((29, -3), (31, 9), (17, 13), (24, 13)): ell(c, x, y, 1.3, 1.1, "hwW")
    out.append(c.spr())
    c = Canvas()
    for (x, y, ch) in ((30, 3, "h"), (32, 12, "w"), (18, 15, "h"), (25, 15, "w"), (12, 14, "g"), (27, -4, "g")): c.put(x, y, ch)
    out.append(c.spr())
    return out


def bel_pinch():
    """A claw snapping shut: two red shell-edged arcs meeting at the tip, a burst of brine where they close."""
    out = []
    for i in range(4):
        c = Canvas()
        if i < 2:
            spread = [1.0, 0.45][i]
            # v0.10: sized for the final-size Barnacle Crab (no ArtScale shrink any more): tip 11 px ahead
            crescent(c, 2, -1.2, 9, 4.6 * spread + 1, -88, -5, 2.6 - i * 0.8, "QPPpj", lead=0.65)
            crescent(c, 2, 1.2, 9, 4.2 * spread + 1, 5, 88, 2.4 - i * 0.8, "QPPpj", lead=0.65)
            outline(c, "Z")
        tip = (11, 0)
        if i >= 1:
            n = [0, 8, 10, 7][i]
            r = [0, 2.5, 4.0, 5.0][i]
            for k in range(n):
                a = 2 * math.pi * k / n + i
                if i == 3 and k % 2: continue
                c.put(*P(tip[0] + r * math.cos(a), tip[1] + r * 0.8 * math.sin(a)), "QEd"[min(2, i - 1)])
        if i == 0:
            c.put(9, -4, "c"); c.put(9, 4, "c")
        if i == 1:
            c.put(*tip, "c"); c.put(tip[0] + 1, tip[1], "Q")
        rnd = random.Random(70 + i)
        for k in range(i * 2):
            c.put(*P(tip[0] + rnd.uniform(-3, 5), tip[1] + rnd.uniform(-4, 4) + i * 0.7), "Ed"[k % 2])
        out.append(c.spr())
    return out


def bel_trident():
    """The three-tined thrust: coral-pink tine streaks driving forward, a ring of spray at the tips."""
    out = []
    for i in range(4):
        c = Canvas()
        x0 = [-2, 6, 12, 0][i]
        x1 = [19, 21, 21, 0][i]
        if i < 3:
            for j, y in enumerate((-3, 0, 3)):
                tip = x1 - (1 if j != 1 else 0)
                cols = ["dEFFQ", "DdEF", "Dd"][i]
                line(c, x0 + (2 if j != 1 else 0), y, tip, y * 0.7, cols)
                if i == 0: c.put(tip + 1, int(round(y * 0.7)), "c")
            if i == 0:
                outline(c, "Z")
                for y in (-3, 0, 3): c.put(x1 + 1, int(round(y * 0.7)), "Q")
        if i >= 1:
            r = [0, 3, 5, 6.5][i]
            for k in range(12):
                a = math.radians(-90 + k * 30)
                if i == 3 and k % 2: continue
                c.put(*P(21 + r * 0.6 * math.cos(a) + (i - 1), r * math.sin(a)), "QEd"[min(2, i - 1)])
        rnd = random.Random(90 + i)
        for k in range(2 * i):
            c.put(*P(14 + rnd.uniform(0, 9), rnd.uniform(-5, 5) + i * 0.7), "Ed"[k % 2])
        out.append(c.spr())
    return out


# =================================================================================== shockwaves
def anchor_quake():
    """The anchor's ground ring: a ripple of brine racing out over the floor, sand and barnacle grit kicked up."""
    out = []
    rxs = [8, 14, 19, 22]
    for i, rx in enumerate(rxs):
        c = Canvas()
        ry = rx * 0.36
        ring(c, rx, ry, 0, ["QE", "EE", "Ed", "d"][i], ["Ed", "dD", "D", "D"][i], gap=(3 if i == 3 else 0), seed=i,
             width=2 if i < 3 else 1)
        if i < 3:
            ring(c, rx * 0.75, ry * 0.75, 0, "d", "D", gap=2, seed=10 + i)
        rnd = random.Random(30 + i)
        for k in range(6 + i):    # grit and spray flung up off the ring
            a = rnd.uniform(0, 2 * math.pi)
            h = [2, 4, 4, 2][i] * rnd.uniform(0.5, 1.0)
            x, y = rx * 0.9 * math.cos(a), ry * 0.9 * math.sin(a) - h
            c.put(*P(x, y), "fHQx"[k % 4] if i < 3 else "x")
        if i == 0:
            ell(c, 0, 0, 4, 1.5, "dEQ", bias=0.3)
        out.append(c.spr())
    return out


def oss_howl():
    """The hound's howl: a blood-red pressure ring on the floor, bone grit jumping, sound arcs rising over it."""
    out = []
    rxs = [9, 16, 21, 24]
    for i, rx in enumerate(rxs):
        c = Canvas()
        ry = rx * 0.44
        ring(c, rx, ry, 0, ["Ry", "Rr", "rp", "p"][i], ["rp", "rp", "p", "p"][i], gap=(3 if i >= 2 else 0), seed=i,
             width=2 if i < 3 else 1)
        rnd = random.Random(50 + i)
        for k in range(8):     # bone grit on the ring
            a = rnd.uniform(0, 2 * math.pi)
            x, y = rx * math.cos(a), ry * math.sin(a) - rnd.uniform(0, 2 + i)
            if i < 3 or k % 2: c.put(*P(x, y), "XWwi"[min(3, i + k % 2)])
        if i < 3:               # howl arcs rising from the centre
            for j in range(2):
                r = 4 + i * 3 + j * 4
                for a in range(-150, -29, 8):
                    ar = math.radians(a)
                    if (a // 8 + j + i) % 4 == 0: continue
                    c.put(*P(r * math.cos(ar) * 1.2, -4 - i * 2 + r * 0.55 * math.sin(ar)), "Rr"[j] if i < 2 else "rp"[j])
        out.append(c.spr())
    return out


# =================================================================================== Lantern Wraith
SOUL = "cBBbn"     # core -> rim


def soul_burst():
    """Soul-fire burst (11 frames, vanilla skydropExplode timing): a white-blue flash, a big ball of pale soul flame
    with licking tongues and violet smoke round it, the flame breaking up into tongues and wisps that rise and cool
    to violet embers."""
    out = []
    for i in range(11):
        c = Canvas()
        rnd = random.Random(120 + i)
        if i == 0:
            blob(c, 0, 0, 3.0, "XcB", noise=0.2, seed=1)
        elif i == 1:
            blob(c, 0, 0, 5.5, "XccBb", noise=0.3, seed=2)
            for a in range(0, 360, 60): line(c, 0, 0, 8 * math.cos(math.radians(a)), 6 * math.sin(math.radians(a)), "cB")
        elif i <= 7:
            t = i - 2                      # 0..5
            r = [10, 13, 14, 14, 13, 11][t]
            cy = -t * 1.2
            # violet smoke puffs round the ball (behind it), growing and drifting up
            for k in range(6):
                a = math.radians(k * 60 + 20 + t * 9)
                rr = r * (0.75 + 0.1 * t)
                blob(c, rr * math.cos(a), cy + rr * 0.7 * math.sin(a) - t * 0.6, 3.2 + t * 0.5, "nnqm"[0:2 + (t > 2)],
                     noise=0.35, seed=60 + k + t * 7, holes=0.1 * t)
            core = ["XccBBbn", "cBBBbbn", "cBBbbnn", "BBbbnn", "Bbbnn", "bbnn"][t]
            blob(c, 0, cy, r * (1.0 - 0.06 * t), core, noise=0.32 + 0.04 * t, seed=i, ang_n=7, sy=0.8, holes=[0, 0.05, 0.15, 0.3, 0.45, 0.6][t])
            if t >= 2:   # the middle burns through first
                blob(c, 0, cy, r * 0.25 * (t - 1), "n", noise=0.4, seed=40 + i, holes=0.5)
            for k in range(6 + 2 * t):   # flung sparks
                a = rnd.uniform(0, 2 * math.pi); rr = r + rnd.uniform(1, 4 + t)
                c.put(*P(rr * math.cos(a), cy + rr * 0.8 * math.sin(a)), "cBb"[min(2, t // 2)])
            if t >= 3:   # tongues of soul flame rising out of the top
                for k in range(5 - (t - 3)):
                    x = rnd.uniform(-8, 8); y = cy - r * 0.6 - rnd.uniform(0, 4)
                    line(c, x, y, x + rnd.uniform(-1, 1), y - 3 - (t - 3), "cBb"[t - 3:] or "b")
        else:
            t = i - 8
            for k in range(14 - 4 * t):   # cooling embers and smoke rags drifting up
                x = rnd.uniform(-14, 14); y = -9 - t * 4 - rnd.uniform(0, 10)
                c.put(*P(x, y), "BbnNq"[min(4, t + k % 3)])
                if k % 3 == 0 and t < 2: c.put(*P(x + 1, y), "n")
        out.append(c.spr())
    return out


def lantern_beam():
    """The lantern's beam, 87 px from the origin (left end) to the right: a white core, blue body with a wavering
    edge, the lantern flare at the root and motes streaming along it."""
    L = 87

    def beam(length, ph, fade=0, broken=False):
        c = Canvas()
        rnd = random.Random(200 + ph * 7 + fade * 31)
        for x in range(0, length + 1):
            if broken and ((x // 5 + ph) % 3 == 0): continue
            t = x / float(L)
            w = 2.6 + 1.0 * math.sin(x * 0.33 + ph * 1.6) + 0.6 * math.sin(x * 0.11 - ph)
            w *= (1.0 - 0.25 * t) * (1.0 - 0.3 * fade)
            if x < 4: w = 1.5 + x * 0.5
            iw = int(round(w))
            for y in range(-iw, iw + 1):
                a = abs(y) / max(1.0, w)
                ch = ("X" if a < 0.2 else "c" if a < 0.45 else "B" if a < 0.8 else "b") if fade == 0 else \
                     ("c" if a < 0.3 else "B" if a < 0.7 else "b") if fade == 1 else ("B" if a < 0.4 else "b")
                c.put(x, y, ch)
            if (x + ph * 3) % 11 == 0 and fade < 2:      # motes streaming along the edge
                c.put(x, -iw - 1 - (x + ph) % 2, "c" if fade == 0 else "B")
            if (x + ph * 5) % 13 == 0:
                c.put(x, iw + 1, "B" if fade == 0 else "b")
        if length >= L - 1 and not broken:          # splash where it ends
            for k in range(5):
                c.put(L + 1 - (k % 2), -3 + k + (ph % 2), "cB"[k % 2])
        # the flare at the root (the lantern)
        if fade < 2:
            for k in range(8):
                a = 2 * math.pi * k / 8 + ph * 0.4
                c.put(*P(1 + 3.2 * math.cos(a), 3.2 * math.sin(a)), "c" if k % 2 else "B", over=False)
            c.put(0, 0, "X"); c.put(1, 0, "X")
        return c.spr()

    opn = [beam(26, 0), beam(56, 1), beam(L, 2)]
    loop = [beam(L, k) for k in range(8)]
    end = [beam(L, 1, fade=1, broken=True), beam(L - 18, 2, fade=2, broken=True), beam(L - 40, 3, fade=2, broken=True)]
    c = Canvas()
    rnd = random.Random(9)
    for k in range(14):
        c.put(rnd.randint(30, L), rnd.randint(-3, 3), "b")
    end.append(c.spr())
    return opn, loop, end


def molten_glob():
    """Chandler's molten glob: a burning blob of tallow, flames streaming back off it (it lands as a burning pool)."""
    out = []
    for i in range(4):
        c = Canvas()
        ell(c, 0, 0, 3.4 + (i % 2) * 0.4, 3.0 - (i % 2) * 0.3, "awWX", bias=0.15)
        outline(c, "k")
        # flames licking up and back off the top
        for k, (fx, h) in enumerate(((-2, 3), (0, 4), (2, 2))):
            hh = h + ((i + k) % 3) - 1
            for t in range(hh):
                c.put(fx - t // 2 - (i % 2), -3 - t, "YOo"[min(2, t * 3 // max(1, hh))])
        c.put(-1, -1, "X"); c.put(1, 1, "o"); c.put(-1 + (i % 2), 1, "O")
        for k in range(3):       # glowing drops trailing behind
            c.put(-5 - k * 2 - (i % 2), 1 + (k + i) % 2, "Oo"[k % 2] if k < 2 else "a")
        out.append(c.spr())
    return out


MOTH = [
"""
OO.....OO
YOO.y.OOY
.oOOgOOo.
..aOkOa..
...a.a...
""", """
.........
.O..y..O.
.YOOgOOY.
..oOkOo..
..a.k.a..
""", """
....y....
...OgO...
.YOOkOOY.
.oOa.aOo.
..a...a..
""", """
.........
.o..y..o.
.OOOgOOO.
..YOkOY..
..a.k.a..
"""]


def ember_moth():
    """A moth made of ember (top-down, wings beating through four positions): ash body, glowing wings."""
    return [Spr.parse(t, feet_x=4).shift(0, 2) for t in MOTH]


# =================================================================================== Bel'Mora plate, brine glob
def brine_glob():
    """A glob of thick brine: a murky green-grey body with a crust of salt, dripping as it flies (not a water bolt)."""
    out = []
    for i in range(4):
        c = Canvas()
        ell(c, 0, -4, 3.3 - (i % 2) * 0.3, 3.0 + (i % 2) * 0.3, "ZDdM", bias=0.1)
        outline(c, "Z")
        for (x, y) in ((-1, -6), (0, -6), (1, -5), (-2, -5)): c.put(x, y, "H" if (x + i) % 2 else "f")   # salt crust
        c.put(1, -3, "E"); c.put(-1, -4, "d")
        for k in range(3):       # drips and spray trailing behind
            c.put(-4 - k * 2 - (i % 2), -4 + ((k + i) % 3) - 1 + k // 2, "dDz"[k])
        c.put(*P(-2 + (i % 2), -1 + (i % 2)), "D"); c.put(*P(-3, 0 - (i % 2)), "d")
        out.append(c.spr())
    return out


def barnacle_plate():
    """Barnacle Crab's shell plate: a crusted shell chip that circles the crab (Orbit), and cracks into shards,
    grit and brine (Break). Orbit centre 7 px above the origin."""
    orbit = []
    for i in range(4):
        c = Canvas()
        a = math.radians(i * 90 + 20)
        x, y = 9 * math.cos(a), -7 + 3 * math.sin(a)
        ell(c, x, y, 2.8 - (i % 2) * 0.9, 2.2, "zxfH", bias=0.2)
        outline(c, "Z")
        c.put(*P(x - 0.5, y - 1), "H"); c.put(*P(x + 0.5, y), "z")      # a barnacle on it
        if i % 2 == 0: c.put(*P(x + 1, y - 1), "Q")
        c.put(*P(x, y + 3), "E")                                         # a drip
        orbit.append(c.spr())
    brk = []
    for i in range(4):
        c = Canvas()
        rnd = random.Random(300)
        if i == 0:
            ell(c, 0, -7, 3.2, 2.6, "zxfH", bias=0.3)
            outline(c, "Z")
            line(c, -2, -9, 1, -6, "Z"); line(c, 1, -6, 2, -4, "Z"); c.put(0, -7, "Q")
        else:
            for k in range(6):
                a = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(3, 5)
                t = i
                x, y = sp * t * math.cos(a), -7 + sp * t * 0.6 * math.sin(a) + 1.2 * t * t
                if y > 0: y = 0
                ch = "fHxz"[k % 4] if i < 3 else "xz"[k % 2]
                c.put(*P(x, y), ch)
                if k < 3 and i < 3: c.put(*P(x + 1, y), "z")
            for k in range(5 - i):
                a = rnd.uniform(0, 2 * math.pi)
                c.put(*P(3 * i * math.cos(a), -7 + 2 * i * math.sin(a) + i), "QEd"[min(2, i - 1)])
        brk.append(c.spr())
    return orbit, brk


# =================================================================================== Ossivar plate break
def bone_plate_break():
    """A bone plate shattering: the plate (drawn where FxBonePlate turns, ~11 px up) cracks, shards and chips fly
    out and rain down to the floor, a puff of marrow-green grave dust."""
    out = []
    rnd0 = random.Random(5)
    shards = [(rnd0.uniform(0, 2 * math.pi), rnd0.uniform(2.5, 4.5), rnd0.choice("XWw")) for _ in range(7)]
    for i in range(4):
        c = Canvas()
        if i == 0:
            ell(c, 0, -11, 3.0, 2.2, "iwWX", bias=0.2)
            outline(c, "k")
            line(c, -1, -13, 0, -11, "k"); line(c, 0, -11, 2, -10, "k"); c.put(-2, -11, "X")
            for k in range(4): c.put(*P(4.5 * math.cos(k * 1.6), -11 + 3 * math.sin(k * 1.6)), "X")
        else:
            for a, sp, ch in shards:
                x = sp * i * math.cos(a) * 1.2
                y = -11 + sp * i * 0.7 * math.sin(a) + 1.6 * i * i
                if y > 0: y = 0
                cc = ch if i < 3 else "hi"[int(a) % 2]
                c.put(*P(x, y), cc)
                if i == 1: c.put(*P(x + (1 if math.cos(a) > 0 else -1), y), "k")
            for k in range(4 - i):   # grave dust
                c.put(*P(rnd0.uniform(-3, 3), -11 - i - rnd0.uniform(0, 3)), "VG"[k % 2] if i < 3 else "v")
        out.append(c.spr())
    return out


# =================================================================================== hit splats (replace the vanilla red blood)
def hit_splat(seed, chunk_cols, drop_cols, flash="X", n=12, grav=1.0, chunky=1):
    """A hit splat (5 frames): a flash, chunks flung out in a fan away from the hit, falling and fading."""
    rnd = random.Random(seed)
    parts = [(rnd.uniform(-2.6, 0.5), rnd.uniform(2.0, 4.2), k) for k in range(n)]   # (angle rad, speed, id)
    out = []
    for i in range(5):
        c = Canvas()
        if i == 0:
            for a in range(0, 360, 90): line(c, 0, 0, 2.5 * math.cos(math.radians(a + 45)), 2.5 * math.sin(math.radians(a + 45)), flash)
            ell(c, 0, 0, 1.6, 1.4, chunk_cols, bias=0.4)
            c.put(0, 0, flash)
        else:
            t = i * 1.0
            if i <= 2:   # the splash itself, a ragged lump breaking up (vanilla blood's chunky f1-f2)
                blob(c, 0.6 * i, 0.4 * i, [3.4, 2.8][i - 1], chunk_cols[1:], noise=0.55, seed=seed + i, ang_n=5,
                     holes=0.15 + 0.25 * i, sy=0.75)
            for a, sp, k in parts:
                x = math.cos(a) * sp * t * (1 if k % 2 else -1) * 0.9
                y = math.sin(a) * sp * t * 0.7 + grav * 0.45 * t * t
                cols = chunk_cols if k % 3 else drop_cols
                ch = cols[min(len(cols) - 1, i - 1 + (k % 2))]
                c.put(*P(x, y), ch)
                if chunky and k % 3 == 0 and i < 3:
                    c.put(*P(x + 1, y), cols[min(len(cols) - 1, i)])
                if i < 3 and k % 4 == 1:     # a short streak behind fast drops
                    c.put(*P(x - math.cos(a) * (1 if k % 2 else -1), y - math.sin(a) * 0.7), cols[-1])
        out.append(c.spr())
    return out


SPLAT_D = [0.05, 0.06, 0.07, 0.08, 0.1]


# =================================================================================== TIMING.md
MARK0, MARK1 = "<!-- godsa_fx begin -->", "<!-- godsa_fx end -->"
FX_NOTES = {
    "FxVhKnightSlash": ("ModKnightSwipe: OrcSwipe clone, capsule x -3..19 / y -10..8 about the spawn; spawned at (0, -10) from the"
                        " feet (Combo1/2). Damage on f0, off at f1 (0.12 s), like the vanilla swipe."),
    "FxVhKnightCleave": ("ModKnightCleave: OrcSwipe2 clone, box 23.5 x 16.9 centred (3.75, 3.5) below the spawn (the old x1.25 baked in);"
                         " spawned at (2, -14) on Combo3 f3. Molten wax splashes at the foot of the arc (the puddle spills there)."),
    "FxVhMatronRake": "ModMatronSlash: OrcSwipe clone; three ember claw rakes over the capsule x -3..19.",
    "FxVhColossusFist": ("ModColossusFist: OrcSwipe clone, capsule now 31 x 26.3 centred (11.55, 1.5) below the spawn (the old x1.4"
                         " baked in, art drawn at full size); knuckle burst at (22, 2), where the fists land."),
    "FxVhSoulBurst": ("ModLanternBlast (= VhorrulFx.SoulBurst; also the Soul Lantern item's burst): skydropExplode clone. Sound f1,"
                      " damage f2-f4 (0.13-0.37 s; vanilla 0.12-0.37). Drawn with the ball's centre 3 px below the orb."),
    "FxVhLanternBeam": ("ModLanternBeam: DamageBeholderBeam clone (87 x 12 box from the origin to the right). Clip = Open + Loop x3"
                        " (1.50 s, vanilla 1.55): damage from frame 3 (0.18 s) to the last frame (1.45 s). On despawn it spawns"
                        " ModLanternBeamEnd (End, 4 x 0.05 s) instead of the vanilla DamageBeholderBeamEnd. Origin = the lantern."),
    "FxVhMoltenGlob": "ModMoltenGlob: webBall clone (hits feet); drawn 16 px above the origin (Strike.ArtAt pixel = origin + (0, 16)).",
    "FxVhEmberMoth": "ModEmberMoth: DFX_PriestessRune clone (no rotation); top-down moth, centred on the origin.",
    "FxBelPinch": "ModCrabPinch: OrcSwipe clone; two shell blades close at (11, 0), brine burst there on f1 (final size, v0.10).",
    "FxBelTrident": ("ModTridentThrust: OrcSwipe clone; three coral tines from x -2 to 21, spray ring at the tips. Drawn 7 px above"
                     " the origin in code (ArtAt pixel (4, 14)) so it rides level with the Matriarch's trident."),
    "FxBelAnchorQuake": ("ModAnchorQuake: troll-shockwave clone via FxKit.TimedHit, damage f0-f3; 42 x 16 floor footprint centred on"
                         " the origin (unscaled; was the tinted x0.6 troll ring)."),
    "FxBelBrineGlob": "ModBrineGlob: webBall clone; the glob rides 4 px above the origin.",
    "FxBelBarnacle": ("Barnacle Crab plate: `Orbit` (loop) = ModBarnaclePlateOrbit, a crusted chip circling an ellipse rx 9 / ry 3"
                      " centred 7 px above the origin; `Break` = ModBarnaclePlateBreak (shards, grit and brine from that point)."
                      " Set as the crab's MonsterTraits plateFx / plateBreakFx."),
    "FxOssHowl": ("ModHoundHowl: troll-shockwave clone via FxKit.TimedHit, damage f0-f3; 48 x 22 floor footprint centred on the"
                  " hound (was the red-tinted x0.8 troll ring); sound arcs rise over it on f0-f2."),
    "FxVhWaxSplat": ("ModVhHitSplat: replaces the vanilla red BloodSplashGenericRandom on every Vhorrul monster's m_spawnOnHit"
                     " (wax chips and molten drops; `Play` and `Play2` variants, one picked per hit). Centred on the origin."),
    "FxBelBrineSplat": "ModBelHitSplat: the Bel'Mora hit splat (brine spray and salt grit), as above.",
    "FxOssBoneChips": "ModOssHitSplat: the Ossivar hit splat (bone chips and grave dust), as above.",
    "FxOssBonePlateBreak": ("ModBonePlateShatter (OssivarFx.PlateShatter): the plate cracks 11 px above the origin (where FxBonePlate"
                            " turns), shards rain to the floor."),
}
SHEET_NOTES = {
    "vh": [
        "### Monster sheets changed in v0.8 (build_rigs.py rigs + vhorrul_t3.py)",
        "Every lengthened attack keeps its old event TIMES (the kit's frame indices moved, VhorrulPack.cs); AnimRun sits on the"
        " last frame, as in every kit (Kit.Melee convention), at the time the old clip ended:",
        "",
        "| Sheet / anim | Frames | Durations | Sync frames (t) |",
        "|---|---|---|---|",
        "| WaxenKnight / Combo1 | 6 | 0.07, 0.05, 0.03, 0.03, 0.1, 0.05 | f2 input off + step + HIT (0.12); f4 step stops (0.18); f5 AnimRun (0.28) |",
        "| WaxenKnight / Combo2 | 6 | 0.03 x 4, 0.1, 0.05 | f2 HIT (0.06); f4 step stops (0.12); f5 AnimRun (0.22) |",
        "| WaxenKnight / Combo3 | 6 | 0.07, 0.07, 0.12, 0.05, 0.16, 0.08 | f2 input off (0.14); f3 CLEAVE + wax spill (0.26); f4 stop (0.31); f5 AnimRun (0.47) |",
        "| WaxenKnight / Death | 4 | 0.08, 0.08, 0.1, 0.3 | - |",
        "| Chandler / Idle | 4 (all distinct) | 0.2 x 4 | - |",
        "| Chandler / Death | 4 | 0.08, 0.08, 0.12, 0.3 | - |",
        "| MothMatron / Brood | 6 | 0.12, 0.08, 0.1, 0.12, 0.14, 0.07 | f3 RELEASE 3 FxVhEmberMoth (0.30); f5 AnimRun (0.56) |",
        "| MothMatron / Death | 4 | 0.1, 0.1, 0.12, 0.3 | - |",
        "| Candelabra / Vigil | 8 | 0.1 x 8 (kit plays it x4 = 32 frames, 3.2 s) | ModLightPuddle f1, 5, 9 ... 29; spark f6, 14, 22, 30 (unchanged) |",
        "| Candelabra / Death | 4 | 0.08, 0.08, 0.12, 0.3 | - |",
        "| TallowColossus / Idle | 4 (all distinct) | 0.22 x 4 | - |",
        "| TallowColossus / Slam | 6 | 0.2, 0.12, 0.06, 0.05, 0.25, 0.1 | f1 input off (0.2); f3 IMPACT: FxWaxShockwave + 4 wax splashes (0.38); f5 AnimRun (0.68) |",
        "| TallowColossus / Curl | 6 | 0.05, 0.05, 0.04, 0.04, 0.04, 0.03 | the roll starts on clip frame 6 (0.25); ModAbsorbWax on clip frames 8, 12 ... 52 |",
        "| TallowColossus / Death | 4 | 0.12, 0.12, 0.14, 0.3 | - |",
        "| AshMoth / Run, Death | 6 / 4 | unchanged | no Idle frames reused any more |",
        "| TallowGrub / Run, Rise, MeltRise | 6 / 5 / 12 | unchanged | no Idle frame reused; the under-floor hold is its own (bubbling) frame |",
        "| Wickling | - | - | (v0.8) design scale 0.65 -> 0.69; superseded in v0.10: redrawn at final size, no ArtScale entry |",
        "| VhChandelier / Death | 4 (all distinct) | 0.1, 0.12, 0.14, 0.3 | - |",
        "| VhAshSeraph / Idle | 4 (all distinct) | 0.18 x 4 | - |",
        "",
        "### v0.10 final-size redraws (godsa_final.py; no ArtScale.cs entry: kit offsets are in these pixels, x fwd / y up)",
        "Frame counts and durations are unchanged, so every event keeps its frame and time.",
        "",
        "| Sheet | Idle | Spawn points (feet-relative, y up) | Node |",
        "|---|---|---|---|",
        "| Wickling | 19 x 15 | Bite f3 jaws (12, 6): WickBite (10, 6), 10 x 11 box; Dash body hit (4, 6), 13 x 11 | 6 |",
        "| AshMoth | 16 x 14 | Puff f3 mouth (9, 8): AshPuff (7, 8); Dive hit (3, 7), 13 x 10; burst (4, 6) | 8 |",
        "| MothMatron | 22 x 25 | Slash f2 claws reach (14, 7): rake at (0, 9); puff (11, 7); Brood f3 moths (6, 16) | 12 |",
        "",
        "- Wickling: a crouched sooty wax rat with a pale tallow candle-skull head (lit wick, red eyes) and a wick tail with an"
        " ember tip; outlined (the 0.69 resample was outline-less).",
        "- AshMoth: a fuzzy moth facing right, pale ash fore-wing with an ember eye-spot, dark hind-wing, feathered antennae.",
        "- MothMatron: one connected moth-woman: ash wings with ember eye-spots, furred body, pale mask with ember eyes,"
        " feathered antennae and two clawed mantis forearms (the claw rake). Death f1-2 is a drawn crumble with an ember burst.",
        "- VhAshSeraph Death f1: drawn crumble (shards pushed out of an ember burst) replaces the checkerboard dissolve.",
        "- FxWaxShockwave: a full floor ellipse (front edge pale wax, back edge duller, drips): centre (35, 15) in its cells.",
        "- FxAshCloud: filled pale-ash puffs (u/U/S) with an ember, readable on dark floors (was dark s/S/m specks).",
        "",
        "### v0.9 lineage pass (every evolution carries a motif of each parent; frames, timing and spawn points unchanged)",
        "- Chandler (Wickling + Tallow Grub): candle head with the Wickling's red eyes and flame, pale segmented tallow body,"
        " leather apron (was grey head + red robe, too close to the Waxen Knight). Idle 24 x 22.",
        "- Candelabra (Tallow Grub + Ash Moth): ash-moth wings with ember eye-spots spread behind the stem. Idle 23 x 24.",
        "- TallowColossus (Waxen Knight + Chandler): the knight's rust great-helm (candle crown, red visor) is its face, a rust"
        " pauldron on the front shoulder, the Chandler's molten bucket stuck in its back.",
        "- LanternWraith (Moth Matron + Candelabra): moth wing-cape with ember eye-spots, feathered antennae, the Candelabra's"
        " candles on the wax mantle and its weeping tear under the mask.",
        "- VhChandelier (Chandler + Candelabra): its heart is the Chandler's rusted bucket of molten wax with two red eyes.",
        "",
        "### LanternWraith (T3, v0.8 redraw in vhorrul_t3.py, v0.9 lineage motifs): cell 46 x 47, feet (23, 45), Idle 30 x 40",
        "Lantern glass (spawn points, feet-relative, y up negative): Idle f0 (9, -15); Swing f2 (15, -18) = the orb;"
        " Beam (16, -22) = the beam origin. Attack node 18.",
        "",
        "| Anim | Frames | Durations | Sync frames (t) |",
        "|---|---|---|---|",
        "| Idle | 4 | 0.16 x 4 | hovering, lantern swaying |",
        "| Run | 6 | 0.09 x 6 | leaning, robe streaming |",
        "| Swing | 6 | 0.12, 0.12, 0.05, 0.08, 0.1, 0.12 | f2 RELEASE FxLanternOrb at (15, -18) (0.24) |",
        "| BlinkOut | 6 | 0.03 x 6 | clip f4 collide off (0.12); dissolves into soul smoke |",
        "| BlinkIn | 6 | 0.03 x 6 | clip f6 = ModBlinkToFlame (0.18); clip f10 vulnerable again (0.30) |",
        "| Beam | 6 (x5 in the kit) | 0.08, 0.06, 0.06, 0.06, 0.05, 0.05 | clip f12 = Beam f0: FxVhLanternBeam at (16, -22) (0.36) |",
        "| Death | 4 | 0.1, 0.12, 0.14, 0.3 | dims, dissolves, the empty robe heap |",
        "",
    ],
    "bel": [
        "### Monster sheets changed in v0.8",
        "- BelUrchin: test ramp lifted (Zqjn -> qjnN) and lit spines (Idle luminance 55 -> 65, p90 90 -> 121).",
        "- BelCaptain: coat navy ramp and hat lifted (Idle luminance 62 -> 76, p90 109 -> 139). Frames and timing unchanged.",
        "",
        "### v0.9 lineage pass (frames, timing and spawn points unchanged)",
        "- BelDiver (Bell Urchin + Barnacle Crab): a violet urchin grown onto the helmet, a red crab claw for the back hand.",
        "- BelSiren (Bell Urchin + Lurefish): urchin spines through her kelp hair, the Lurefish's glowing lure on a brow stalk.",
        "- BelDrownedBell (Bell Diver + Bell Hermit): its head sealed in the Diver's cracked brass helmet, the Hermit's red"
        " crusher claw as its front hand.",
        "- BelCaptain (Bell Diver + Salt Siren): the Diver's anchor chain slung across the coat and a brass diving collar.",
        "- BelMatriarch (Salt Siren + Brine Lamprey): body ramp is now the Lamprey's teal-slate (was indigo/lavender).",
        "- BelKraken (Bell Hermit + Brine Lamprey): wears the Hermit's barnacled bronze bell on its mantle; a lamprey's toothed"
        " sucker under its head.",
        "",
        "### v0.10 final art pass",
        "- Palette midtones lifted a step across the line (Z D d E Q z x f H L l J M C j and the Greek ramps): Idle luminance"
        " now ~75-98 (was 65-81).",
        "- BelCrab and BelDiver redrawn at final size (godsa_final.py) and BelDrownedBell drawn at design scale 1.0: no ArtScale"
        " entries; kit offsets are in these pixels (x fwd, y up).",
        "",
        "| Sheet | Idle | Spawn points | Node |",
        "|---|---|---|---|",
        "| BelCrab | 19 x 15 | Pinch f3 claw (13-15, 6-12): CrabPinch at (5, 8), blades to x 11 of it, collider 12 x 10 | 6 |",
        "| BelDiver | 20 x 26 | Anchor f3-4 crown lands (12, 0): slam box (12, 5) 14 x 12, quake (12, 0); Hook f2 hand (13, 16): hook (12, 16) | 12 |",
        "",
        "- BelCrab: front-on crab: red carapace under a high grey barnacle-crust dome (the shell it hides in), two raised red"
        " pincers (near one bigger), stalk eyes, three legs a side. Shell tucks claws over the face and sinks under the dome.",
        "- BelDiver: carries the anchor over its shoulder (Idle/Run), urchin on the helmet; v0.10: the back hand is a canvas glove studded with urchin spines (was a red crab claw).",
        "- BelDrownedBell: drawn at 1.0 with clean flesh (no speckle), the bell lowered; Idle 40 x 40.",
        "- BelCaptain: the Diver's brass helmet hangs at its hip and a glowing lure dangles from the hat brim (the Siren).",
        "- FxSpine / FxHook: lifted (violet base, pale shaft, white tip / pale iron, bright glints) for dark floors.",
        "- FxBelPinch: resized for the final-size crab (tip 11 px ahead), origin (-1, 9).",
        "",
    ],
    "oss": [
        "### Monster sheets changed in v0.8",
        "- OssRattlebones: design scale 0.75 -> 0.8 (Idle 8 x 16, T1 limit 16 high; ArtScale.cs entry must follow); Idle now moves"
        " (sags, arms swing, skull lolls, jaw chatters).",
        "- OssBoneRat: Bite 6 (0.12, 0.1, 0.05, 0.04, 0.04, 0.05; strike still f2, AnimRun still 0.35 s), Death 4, new Spawn 3"
        " (0.1 x 3, played by the fodder base's spawn clip).",
        "- OssCairnCrow: Peck 6 (0.12, 0.14, 0.05, 0.05, 0.05, 0.1): strike f2 (0.26), stop f3 (0.31), last frame (AnimRun) 0.41 s as before.",
        "- OssOssuary: Run 6 distinct frames (arms on the cosine of the stride).",
        "",
        "### v0.9 lineage pass (frames, timing and spawn points unchanged)",
        "- (v0.10: every evolution now has ONE parent; see the v0.10 section below for the motifs that changed.)",
        "- OssBoneLancer (Rattlebones): the v0.9 hound-skull helm was removed in v0.10 (leather cap and brow again).",
        "- OssOssuaryPriest (Cairn Crow): the mitre is a crow's skull with black crest and beak; crow-feather mantle.",
        "- OssOssuary (Ossuary Priest): a red vestment and bead stole; v0.10 swapped the Lancer's spine-spears for the priest's crow-feather mantle.",
        "- OssMarrowWyrm (Carrion Vulture): a black vulture ruff, black wing membrane (v0.10 dropped the Gravetusk tusk).",
        "",
        "### v0.10 final-size redraws (godsa_final.py; no ArtScale.cs entry: kit offsets are in these pixels, x fwd / y up)",
        "",
        "| Sheet | Idle | Spawn points | Node |",
        "|---|---|---|---|",
        "| OssRattlebones | 15 x 16 | SkullToss f2 hand (9, 11): Skull at (8, 11) | 9 |",
        "| OssMarrowHound | 20 x 10 | Gnaw f2/f4 jaws (12.5, 3): HoundBite (11, 4), 10 x 10 | 6 |",
        "| OssBoneRat | 15 x 7 | Bite f2 jaws (9, 2): RatBite (7, 4), 8 x 8 | 4 |",
        "| OssCairnCrow | 19 x 17 | Peck f2 beak (13, 7): CrowPeck (10, 7), 10 x 10; Caw crows (8, 11) | 9 |",
        "",
        "- OssOssuaryPriest: the crow-skull mitre and feather mantle substitutes enlarged so the long beak reads at 1x.",
        "",
    ],
}


def timing_lines(god):
    """The godsa_fx section of a god's TIMING.md (also used by ossivar_rigs / belmora_rigs write_timing)."""
    import json
    L = ["", MARK0, "## v0.8 art pass (tools/sprites/godsa_fx.py and the monster rigs)", "",
         "Effect sheets: origin = the pixel Strike.ArtAt puts on the effect's spawn point (cell coordinates, y down);"
         " points below are relative to the origin, y down.", "",
         "| Sheet | Cell | Origin | Anims (frames: durations) | Use |", "|---|---|---|---|---|"]
    for name in FX_NOTES:
        god_ = {"FxVh": "vh", "FxBe": "bel", "FxOs": "oss"}[name[:4]]
        if god_ != god: continue
        jp = os.path.join(OUT[god], name + ".json")
        if not os.path.exists(jp): continue
        m = json.load(open(jp))
        org = BUILT.get(name, {}).get("origin") or ORIGINS.get(name, ("?", "?"))
        an = "; ".join("%s %d: %s" % (a["name"], len(a["frames"]), ", ".join("%.3g" % d for d in a["durations"])) for a in m["anims"])
        L.append("| %s | %d x %d | (%s, %s) | %s | %s |" % (name, m["cellW"], m["cellH"], org[0], org[1], an, FX_NOTES[name]))
    L += [""] + SHEET_NOTES[god] + [MARK1, ""]
    return L


# the origins as built (C# Strike.ArtAt calls use these numbers; rebuilt sheets print theirs)
ORIGINS = {"FxVhKnightSlash": (-1, 11), "FxVhKnightCleave": (6, 19), "FxVhMatronRake": (-1, 11), "FxVhColossusFist": (-7, 13),
           "FxVhSoulBurst": (21, 26), "FxVhLanternBeam": (3, 7), "FxVhMoltenGlob": (11, 8), "FxVhEmberMoth": (5, 3),
           "FxBelPinch": (-1, 9), "FxBelTrident": (4, 7), "FxBelAnchorQuake": (23, 9), "FxBelBrineGlob": (10, 9),
           "FxBelBarnacle": (13, 14), "FxOssHowl": (25, 17), "FxOssBonePlateBreak": (14, 18),
           "FxVhWaxSplat": (13, 6), "FxBelBrineSplat": (15, 5), "FxOssBoneChips": (15, 4)}


def write_timing():
    """Replace (or append) the godsa_fx section in each god's TIMING.md."""
    for god in ("vh", "bel", "oss"):
        p = os.path.join(OUT[god], "TIMING.md")
        old = open(p).read() if os.path.exists(p) else ""
        if MARK0 in old:
            old = old[:old.index(MARK0)].rstrip("\n") + "\n" + old[old.index(MARK1) + len(MARK1):].lstrip("\n")
        open(p, "w").write(old.rstrip("\n") + "\n" + "\n".join(timing_lines(god)))
        print("timing ->", p)


# =================================================================================== build
def build(only=None):
    def want(n): return only is None or n in only
    if want("FxVhKnightSlash"): sheet("vh", "FxVhKnightSlash", [("Slash", knight_slash(), SWIPE_D)], (30, 30), (7, 15))
    if want("FxVhKnightCleave"): sheet("vh", "FxVhKnightCleave", [("Upslash", knight_cleave(), SWIPE_D)], (32, 40), (10, 21))
    if want("FxVhMatronRake"): sheet("vh", "FxVhMatronRake", [("Rake", matron_rake(), SWIPE_D)], (28, 30), (6, 15))
    if want("FxVhColossusFist"): sheet("vh", "FxVhColossusFist", [("Fist", colossus_fist(), SWIPE_D)], (42, 36), (8, 18))
    if want("FxVhSoulBurst"): sheet("vh", "FxVhSoulBurst", [("Play", soul_burst(), BURST_D)], (48, 50), (24, 26))
    if want("FxVhLanternBeam"):
        opn, loop, end = lantern_beam()
        sheet("vh", "FxVhLanternBeam", [("Open", opn, [0.06] * 3), ("Loop", loop, [0.055] * 8), ("End", end, [0.05] * 4)],
              (96, 14), (4, 7))
    if want("FxVhMoltenGlob"): sheet("vh", "FxVhMoltenGlob", [("Fly", molten_glob(), [0.07] * 4)], (16, 14), (9, 8))
    if want("FxVhEmberMoth"): sheet("vh", "FxVhEmberMoth", [("Fly", ember_moth(), [0.06] * 4)], (12, 12), (6, 6))
    if want("FxBelPinch"): sheet("bel", "FxBelPinch", [("Pinch", bel_pinch(), SWIPE_D)], (30, 26), (5, 13))
    if want("FxBelTrident"): sheet("bel", "FxBelTrident", [("Thrust", bel_trident(), SWIPE_D)], (32, 18), (5, 9))
    if want("FxBelAnchorQuake"): sheet("bel", "FxBelAnchorQuake", [("Ring", anchor_quake(), RING_D)], (50, 22), (25, 12))
    if want("FxBelBrineGlob"): sheet("bel", "FxBelBrineGlob", [("Fly", brine_glob(), [0.07] * 4)], (18, 12), (10, 10))
    if want("FxBelBarnacle"):
        orbit, brk = barnacle_plate()
        sheet("bel", "FxBelBarnacle", [("Orbit", orbit, [0.12] * 4), ("Break", brk, [0.06, 0.08, 0.1, 0.12])], (30, 18), (15, 15))
    if want("FxVhWaxSplat"):
        sheet("vh", "FxVhWaxSplat", [("Play", hit_splat(3, "XWwh", "OoaK", flash="y"), SPLAT_D),
                                      ("Play2", hit_splat(8, "WXwh", "Ooak", flash="X"), SPLAT_D)])
    if want("FxBelBrineSplat"):
        sheet("bel", "FxBelBrineSplat", [("Play", hit_splat(4, "QEdD", "HfxZ", flash="c"), SPLAT_D),
                                         ("Play2", hit_splat(9, "EQdD", "fHxz", flash="Q"), SPLAT_D)])
    if want("FxOssBoneChips"):
        sheet("oss", "FxOssBoneChips", [("Play", hit_splat(5, "XWwi", "GVvk", flash="X", grav=1.3), SPLAT_D),
                                        ("Play2", hit_splat(11, "WXwi", "VGvk", flash="W", grav=1.3), SPLAT_D)])
    if want("FxOssHowl"): sheet("oss", "FxOssHowl", [("Ring", oss_howl(), RING_D)], (54, 34), (27, 22))
    if want("FxOssBonePlateBreak"):
        sheet("oss", "FxOssBonePlateBreak", [("Play", bone_plate_break(), [0.06, 0.08, 0.1, 0.12])], (30, 22), (15, 20))


if __name__ == "__main__":
    a = sys.argv[1:]
    only = None
    if "--only" in a: only = set(a[a.index("--only") + 1].split(","))
    build(only)
    for n, b in BUILT.items():
        if tuple(b["origin"]) != tuple(ORIGINS[n]):
            print("WARNING %s origin moved %s -> %s: update ORIGINS and the Strike.ArtAt call in its pack" % (n, ORIGINS[n], b["origin"]))
    if not os.environ.get("FX_TMP"): write_timing()
